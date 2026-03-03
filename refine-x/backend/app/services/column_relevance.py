"""
Column Relevance Gate — GPT-4o evaluates each column for analytical usefulness.

Runs AFTER GlobalRules + StructRules (Steps 1–4), BEFORE AI Classification (Step 5).
The pipeline pauses here to await user confirmation of which columns to keep.

"""

import json
import re
from typing import Any, Dict, List

from openai import OpenAI, RateLimitError, AuthenticationError, APIStatusError

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Column name patterns that strongly suggest the column is useless for analysis
_REMOVE_PATTERNS = [
    "unnamed", "index", "row_num", "rownum", "row_number", "__index",
    "serial", "auto_id", "_id_internal", "hash", "checksum", "uuid_internal",
]

# Patterns that suggest a column is an ID/key — keep but flag
_ID_PATTERNS = ["_id", "id_", " id", "code", "ref", "key", "num", "no."]


def _deterministic_column_relevance(
    columns: List[str],
    sample_rows: List[Dict[str, Any]],
    filename: str,
) -> Dict[str, Any]:
    """
    Fallback when GPT is unavailable. Uses column name heuristics and
    sample data to decide keep vs. remove — never returns 'AI call failed'.
    """
    col_results = []

    for col in columns:
        lower = str(col).lower().strip()

        # Check if every sample value is identical (useless column)
        sample_vals = [str(row.get(col, "")).strip() for row in sample_rows if col in row]
        all_same = len(set(sample_vals)) <= 1 and len(sample_vals) > 0

        # Check if all sample values are empty/null
        all_empty = all(v in ("", "None", "nan", "NaT", "null") for v in sample_vals)

        # Check remove patterns
        is_noise = any(p in lower for p in _REMOVE_PATTERNS)

        # Auto-increment check: all numeric, sequential integers
        try:
            nums = [float(v) for v in sample_vals if v not in ("", "None", "nan")]
            is_sequential = (
                len(nums) >= 3
                and all(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1))
                and lower in ("id", "index", "row", "rowid", "#", "no", "sr", "sno", "s.no", "sl.no")
            )
        except ValueError:
            is_sequential = False

        if all_empty:
            rec, reason = "remove", "Column appears to be entirely empty in the sample."
        elif is_sequential:
            rec, reason = "remove", "Sequential row-number index — no analytical value."
        elif all_same and is_noise:
            rec, reason = "remove", "Constant value with noise-like column name — likely internal/system column."
        elif is_noise and all_same:
            rec, reason = "remove", "Identical values across all rows — not useful for analysis."
        else:
            # Default: keep — build a useful reason from sample values
            sample_preview = ", ".join(f'"{v}"' for v in sample_vals[:3] if v not in ("", "None", "nan"))
            if sample_preview:
                reason = f"Contains meaningful data (e.g. {sample_preview}) — useful for analysis."
            else:
                reason = "Retained for analysis — review if values appear meaningful."
            rec = "keep"

        col_results.append({"name": col, "recommendation": rec, "reason": reason})

    remove_count = sum(1 for c in col_results if c["recommendation"] == "remove")
    overall = "useful" if len(columns) - remove_count > 0 else "not_useful"
    summary = (
        f"Heuristic evaluation of '{filename}': "
        f"{len(columns) - remove_count} columns recommended to keep, "
        f"{remove_count} flagged for removal."
        + (" (AI unavailable — review recommendations carefully.)" if remove_count == 0 else "")
    )

    return {"overall_verdict": overall, "reason": summary, "columns": col_results}


def evaluate_column_relevance(
    columns: List[str],
    sample_rows: List[Dict[str, Any]],
    filename: str,
) -> Dict[str, Any]:
    """
    Single GPT-4o call that evaluates every column for analytical relevance.
    Falls back to deterministic heuristics if OpenAI is unavailable.

    Returns:
        {
            "overall_verdict": "useful" | "not_useful",
            "reason": "short explanation",
            "columns": [
                {"name": "col_name", "recommendation": "keep" | "remove", "reason": "why"},
                ...
            ]
        }
    """
    system_prompt = (
        "You are a data quality analyst. You will receive a table's column names, "
        "a sample of its first 5 rows, and the original filename.\n\n"
        "Your task:\n"
        "1. Evaluate EACH column and decide whether it should be KEPT for "
        "analysis/visualization or REMOVED because it is irrelevant, redundant, "
        "or useless (e.g. internal auto-increment IDs with no analytical meaning, "
        "entirely empty columns, meaningless hash codes, row-number indices, "
        "columns that are exact duplicates of another column).\n"
        "2. Provide an overall verdict on whether this table is useful for "
        "visualization/analysis.\n\n"
        "IMPORTANT RULES:\n"
        "- Err on the side of KEEPING columns. Only recommend 'remove' when "
        "a column is clearly useless for any analytical or visualization purpose.\n"
        "- Unique IDs that could serve as record identifiers should be KEPT.\n"
        "- Columns with real data (names, dates, amounts, categories, etc.) "
        "should always be KEPT.\n"
        "- Only flag columns as 'remove' if they are truly meaningless "
        "(e.g. auto-generated row numbers, internal system hashes, "
        "columns where every value is identical, fully empty columns).\n\n"
        "Return ONLY valid JSON in this exact format:\n"
        "{\n"
        '  "overall_verdict": "useful" | "not_useful",\n'
        '  "reason": "short explanation of the table\'s analytical value",\n'
        '  "columns": [\n'
        '    {"name": "column_name", "recommendation": "keep" | "remove", '
        '"reason": "brief reason"}\n'
        "  ]\n"
        "}\n\n"
        "Every column from the input MUST appear in the output. "
        "Do NOT add columns that don't exist. Return ONLY the JSON object, "
        "no markdown fences, no extra text."
    )

    user_prompt = (
        f"Filename: {filename}\n\n"
        f"Columns ({len(columns)}): {json.dumps(columns)}\n\n"
        f"Sample rows (first 5):\n{json.dumps(sample_rows, indent=2, default=str)}"
    )

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,
            max_tokens=4096,
        )

        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if the model wraps the JSON
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)

        # ── Validate structure ────────────────────────────────────────────
        if "overall_verdict" not in result:
            result["overall_verdict"] = "useful"
        if "reason" not in result:
            result["reason"] = ""
        if "columns" not in result or not isinstance(result["columns"], list):
            result["columns"] = [
                {"name": col, "recommendation": "keep", "reason": "default — AI response malformed"}
                for col in columns
            ]

        # Normalise verdict to the two allowed values
        if result["overall_verdict"] not in ("useful", "not_useful"):
            result["overall_verdict"] = "useful"

        # Ensure every input column is represented
        returned_names = {c["name"] for c in result["columns"]}
        for col in columns:
            if col not in returned_names:
                result["columns"].append({
                    "name": col,
                    "recommendation": "keep",
                    "reason": "not evaluated by AI — kept by default",
                })

        return result

    except (RateLimitError, AuthenticationError, APIStatusError, Exception):
        # GPT unavailable — run deterministic fallback
        return _deterministic_column_relevance(columns, sample_rows, filename)
