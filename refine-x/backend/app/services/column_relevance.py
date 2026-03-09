"""
Column Relevance Gate — GPT-4o gives a genuine per-column analysis.

Each column receives:
  - decision: "keep" or "drop"
  - what_it_measures: plain English explanation of what the column actually contains
  - why: specific reason for the decision
  - analytical_use: how this column can be used (keep columns only)
  - warning: any data quality concern (optional)

Runs AFTER GlobalRules + StructRules (Steps 1–4), BEFORE AI Classification (Step 5).
The pipeline pauses here to await user confirmation of which columns to keep.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional

from openai import OpenAI

from app.config import settings

_client = OpenAI(api_key=settings.OPENAI_API_KEY)
logger = logging.getLogger(__name__)

_REMOVE_PATTERNS = [
    "unnamed", "index", "row_num", "rownum", "row_number", "__index",
    "serial", "auto_id", "_id_internal", "hash", "checksum", "uuid_internal",
]

# ── Prompt builder ────────────────────────────────────────────────────────────

def build_header_analysis_prompt(
    columns_info: list,
    filename: str,
    total_rows: int,
) -> str:
    """
    columns_info is a list of dicts:
    [
      {
        "name": "value_of_sales_shipments_receipts_revenue_or_business_done_1000",
        "sample_values": ["529,239,818", "413,524,731", "310,960,365"],
        "unique_count": 847,
        "null_pct": 0.02
      },
      ...
    ]
    """
    columns_json = json.dumps(columns_info, indent=2)

    return f"""
You are a senior data analyst reviewing the columns of a newly uploaded dataset.
File: {filename}
Total rows: {total_rows}

Your job is to evaluate each column and decide:
1. Should it be KEPT for analysis?
2. Should it be DROPPED (not useful, redundant, or problematic)?
3. What is it actually measuring? Explain in plain English what this column represents.
4. Why does keeping or dropping it make sense for data analysis?

COLUMNS TO EVALUATE:
{columns_json}

RULES FOR YOUR EVALUATION:
- ID columns (near-unique values, no analytical value) → suggest drop with reason
- Columns that are clearly duplicates of another column → suggest drop with reason
- Columns with >80% null values → suggest drop with reason
- Columns with only 1 unique value → suggest drop with reason
- Columns with actual analytical value → suggest keep with a specific explanation of WHAT it measures and WHY it is useful

CRITICAL — your descriptions must be SPECIFIC to this dataset, not generic:

BAD description (do not write this):
"Contains meaningful data (e.g. '529,239,818', '413,524,731') — useful for analysis."

GOOD description (write like this):
"Annual revenue or sales volume in thousands of dollars for each industry sector. This is the primary financial metric in the dataset — essential for comparing industry sizes, identifying dominant sectors, and tracking economic changes over time. The values in the billions suggest large industrial sectors like mining and oil extraction."

BAD description:
"Contains meaningful data (e.g. '21', '21', '211') — useful for analysis."

GOOD description:
"NAICS industry classification code from the 2007 North American Industry Classification System. The value '21' represents Mining, Quarrying, and Oil/Gas Extraction at the sector level, while '211' is the subsector for Oil and Gas Extraction specifically. This column enables hierarchical industry grouping — keep it for sector-level analysis."

Return your response as a JSON array:
[
  {{
    "column": "column_name",
    "decision": "keep" or "drop",
    "what_it_measures": "Plain English explanation of what this column actually contains",
    "why": "Specific reason for keeping or dropping based on this dataset",
    "analytical_use": "If keeping — what analysis does this column enable? Set to null if dropping.",
    "warning": "Any data quality concern to flag (optional, set to null if none)"
  }}
]

Be specific. Every description must be unique to its column. No two columns should have similar descriptions.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_columns_info(
    columns: List[str],
    sample_rows: List[Dict[str, Any]],
    df=None,
) -> list:
    """
    Build the rich columns_info list passed into the GPT prompt.
    Includes sample values, unique count, null pct when a DataFrame is available.
    """
    columns_info = []
    for col in columns:
        sample_vals = [
            str(r.get(col, "")).strip()
            for r in sample_rows
            if str(r.get(col, "")).strip() not in ("", "None", "nan", "NaT", "null")
        ][:5]

        info: Dict[str, Any] = {
            "name": col,
            "sample_values": sample_vals,
        }

        if df is not None:
            try:
                series = df[col]
                info["unique_count"] = int(series.nunique())
                null_count = int(series.isna().sum()) + int((series.astype(str).str.strip() == "").sum())
                info["null_pct"] = round(null_count / max(len(series), 1), 3)
            except Exception:
                pass

        columns_info.append(info)

    return columns_info


def _deterministic_column_analysis(
    columns: List[str],
    sample_rows: List[Dict[str, Any]],
    filename: str,
    df=None,
) -> List[Dict[str, Any]]:
    """
    Fallback when GPT is unavailable.
    Produces per-column decisions using ColumnRole classification — no template strings,
    no "AI was unavailable" text in user-facing output.
    """
    from app.services.column_role_classifier import classify_column_role, ColumnRole

    results = []

    for col in columns:
        lower = str(col).lower().strip()
        sample_vals = [
            str(r.get(col, "")).strip()
            for r in sample_rows
            if str(r.get(col, "")).strip() not in ("", "None", "nan", "NaT", "null")
        ][:5]

        all_same = len(set(sample_vals)) <= 1 and len(sample_vals) > 0
        all_empty = len(sample_vals) == 0
        is_noise = any(p in lower for p in _REMOVE_PATTERNS)

        try:
            nums = [float(v.replace(",", "")) for v in sample_vals]
            is_sequential = (
                len(nums) >= 3
                and all(nums[i + 1] - nums[i] == 1 for i in range(len(nums) - 1))
                and lower in ("id", "index", "row", "rowid", "#", "no", "sr", "sno", "s.no", "sl.no")
            )
        except (ValueError, AttributeError):
            is_sequential = False

        col_readable = col.replace("_", " ").replace("-", " ").strip()

        # --- gather DataFrame-level stats and classify role when possible ---
        role = None
        null_pct = 0.0
        unique_count = len(set(sample_vals))
        if df is not None:
            try:
                series = df[col]
                role = classify_column_role(series, col)
                null_count = int(series.isna().sum()) + int(
                    (series.astype(str).str.strip() == "").sum()
                )
                null_pct = null_count / max(len(series), 1)
                unique_count = int(series.nunique())
            except Exception:
                pass

        # --- early-exit cases (drop) ---
        if all_empty:
            results.append({
                "column": col,
                "decision": "drop",
                "what_it_measures": (
                    f"'{col_readable}' appears entirely empty — no values found in the sample rows."
                ),
                "why": (
                    "Columns with no data provide no analytical value and add unnecessary "
                    "noise to the dataset."
                ),
                "analytical_use": None,
                "warning": "Verify this column is not populated outside the first 5 rows.",
            })
            continue

        if is_sequential:
            results.append({
                "column": col,
                "decision": "drop",
                "what_it_measures": (
                    f"'{col_readable}' is a sequential row-number index — integers "
                    f"incrementing by 1 per row."
                ),
                "why": (
                    "Auto-generated counters carry no analytical meaning. Removing it will "
                    "not affect any calculation or visualisation."
                ),
                "analytical_use": None,
                "warning": None,
            })
            continue

        if all_same and is_noise:
            first_val = sample_vals[0] if sample_vals else "unknown"
            results.append({
                "column": col,
                "decision": "drop",
                "what_it_measures": (
                    f"'{col_readable}' holds a single constant value ('{first_val}') "
                    f"across all rows — likely a system-generated internal field."
                ),
                "why": (
                    "Constant-value columns contain no information variance and cannot be "
                    "used for grouping, filtering, or measurement."
                ),
                "analytical_use": None,
                "warning": None,
            })
            continue

        # --- role-classified drop cases ---
        if role in (ColumnRole.IDENTIFIER, ColumnRole.DERIVED_ID):
            sample_preview = ", ".join(f'"{v}"' for v in sample_vals[:3])
            results.append({
                "column": col,
                "decision": "drop",
                "what_it_measures": (
                    f"'{col_readable}' appears to be a unique identifier or surrogate key. "
                    f"Sample values: {sample_preview}."
                ),
                "why": (
                    f"Identifier columns typically have one unique value per row "
                    f"({unique_count} unique values detected) and cannot be meaningfully "
                    f"grouped, aggregated, or used on a chart axis."
                ),
                "analytical_use": None,
                "warning": None,
            })
            continue

        if role == ColumnRole.CONSTANT:
            first_val = sample_vals[0] if sample_vals else "unknown"
            results.append({
                "column": col,
                "decision": "drop",
                "what_it_measures": (
                    f"'{col_readable}' holds a single constant value ('{first_val}') — "
                    f"every row is identical."
                ),
                "why": (
                    "Constant-value columns have no variance and cannot contribute to "
                    "any comparison, grouping, or visualisation."
                ),
                "analytical_use": None,
                "warning": None,
            })
            continue

        if role == ColumnRole.SEQUENCE:
            results.append({
                "column": col,
                "decision": "drop",
                "what_it_measures": (
                    f"'{col_readable}' is a monotonically increasing numeric sequence — "
                    f"likely an auto-increment row counter."
                ),
                "why": (
                    "Sequence columns represent row order rather than a measured quantity "
                    "and should not be used in any analysis."
                ),
                "analytical_use": None,
                "warning": None,
            })
            continue

        # --- keep cases — build data-quality warning only when warranted ---
        sample_preview = ", ".join(f'"{v}"' for v in sample_vals[:3])

        warning: str | None = None
        if null_pct > 0.30:
            warning = (
                f"{null_pct:.0%} of values are missing — "
                f"consider imputation or exclusion before analysis."
            )
        elif unique_count == 1:
            warning = "Only 1 unique value — no analytical variance in this column."

        # --- role-specific descriptions ---
        if role == ColumnRole.DATE:
            what_it_measures = (
                f"'{col_readable}' contains date or time values. "
                f"Sample values: {sample_preview}."
            )
            why = (
                "Contains parseable date/time values — essential for trend and "
                "time-series analysis as a time axis."
            )
            analytical_use = (
                "Use as the time axis for line charts, trend plots, and "
                "time-bucketed bar charts."
            )

        elif role == ColumnRole.METRIC:
            what_it_measures = (
                f"'{col_readable}' is a numeric measure with {unique_count} distinct values. "
                f"Sample values: {sample_preview}."
            )
            why = (
                "Holds continuous or discrete numeric data suitable for aggregation "
                "(sum, average, min/max) and Y-axis measures."
            )
            analytical_use = (
                "Use as a Y-axis metric for bar charts, line charts, and scatter plots."
            )

        elif role == ColumnRole.BOOLEAN:
            what_it_measures = (
                f"'{col_readable}' is a binary (yes/no) column. "
                f"Sample values: {sample_preview}."
            )
            why = (
                "Two-value columns are useful for binary comparisons, conditional "
                "filtering, and splitting data into two groups."
            )
            analytical_use = (
                "Use for binary split analysis, boolean filtering, or as a grouping variable."
            )

        elif role == ColumnRole.CATEGORY:
            what_it_measures = (
                f"'{col_readable}' is a categorical column with {unique_count} distinct values. "
                f"Sample values: {sample_preview}."
            )
            why = (
                f"Has {unique_count} distinct categories — sufficient variation for "
                f"grouping, segmentation, and breakdown analysis."
            )
            analytical_use = (
                "Use as a categorical X-axis for bar charts, donut charts, and "
                "grouped aggregations."
            )

        elif role == ColumnRole.CODE:
            what_it_measures = (
                f"'{col_readable}' contains classification codes or structured identifiers "
                f"with {unique_count} distinct values. Sample values: {sample_preview}."
            )
            why = (
                f"Code columns with {unique_count} distinct values can be used for "
                f"category-level grouping and hierarchical breakdowns."
            )
            analytical_use = (
                "Use as a grouping category for sector, classification, or "
                "code-level breakdowns."
            )

        elif role == ColumnRole.HIGH_CARDINALITY_TEXT:
            what_it_measures = (
                f"'{col_readable}' contains free-form text with high cardinality "
                f"({unique_count} distinct values). Sample values: {sample_preview}."
            )
            why = (
                f"High-cardinality text columns ({unique_count} unique values) are best "
                f"used for search and filtering rather than direct charting."
            )
            analytical_use = (
                "Use as a label or search filter; avoid as a direct chart axis."
            )

        else:
            # Unknown role — use numeric vs text heuristic
            has_numbers = any(
                v.replace(",", "").replace(".", "").replace("-", "").isnumeric()
                for v in sample_vals
            )
            if has_numbers:
                what_it_measures = (
                    f"'{col_readable}' contains numeric data with {unique_count} distinct "
                    f"values. Sample values: {sample_preview}."
                )
                why = (
                    "Holds numeric values that support aggregation and comparison."
                )
                analytical_use = "Use as a metric axis or aggregation target."
            else:
                what_it_measures = (
                    f"'{col_readable}' contains text values with {unique_count} distinct "
                    f"entries. Sample values: {sample_preview}."
                )
                why = (
                    f"Contains {unique_count} distinct text values — suitable for "
                    f"categorical grouping or filtering."
                )
                analytical_use = (
                    "Use for grouping, segmentation, or as a categorical axis."
                )

        results.append({
            "column": col,
            "decision": "keep",
            "what_it_measures": what_it_measures,
            "why": why,
            "analytical_use": analytical_use,
            "warning": warning,
        })

    return results


# ── Main entry point ──────────────────────────────────────────────────────────

def analyze_columns_for_header_gate(
    columns: List[str],
    sample_rows: List[Dict[str, Any]],
    filename: str,
    total_rows: int = 0,
    df=None,
) -> List[Dict[str, Any]]:
    """
    Main entry point — calls GPT with the detailed per-column analysis prompt.

    Returns a list of dicts, one per input column, each containing:
      {
        "column": str,
        "decision": "keep" | "drop",
        "what_it_measures": str,
        "why": str,
        "analytical_use": str | None,
        "warning": str | None,
      }

    Falls back to _deterministic_column_analysis if GPT is unavailable.
    """
    logger.info(
        f"[GPT CALL START] analyze_columns_for_header_gate — "
        f"file={filename!r}  columns={len(columns)}"
    )

    columns_info = _build_columns_info(columns, sample_rows, df)
    prompt = build_header_analysis_prompt(columns_info, filename, total_rows)

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=4096,
        )
        logger.info(
            f"[GPT CALL SUCCESS] analyze_columns_for_header_gate — "
            f"tokens used: {response.usage.total_tokens}"
        )

        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw)

        if not isinstance(result, list):
            raise ValueError(f"GPT returned {type(result).__name__}, expected list")

        # Normalise and ensure every input column is represented
        returned = {
            item["column"]: item
            for item in result
            if isinstance(item, dict) and "column" in item
        }
        final = []
        for col in columns:
            if col in returned:
                item = returned[col]
                final.append({
                    "column": col,
                    "decision": str(item.get("decision", "keep")).lower().strip(),
                    "what_it_measures": item.get("what_it_measures") or f"Column '{col}'",
                    "why": item.get("why") or "",
                    "analytical_use": item.get("analytical_use") or None,
                    "warning": item.get("warning") or None,
                })
            else:
                final.append({
                    "column": col,
                    "decision": "keep",
                    "what_it_measures": f"Column '{col}' — not evaluated by AI, retained by default.",
                    "why": "Not returned by AI analysis — kept to avoid unintentional data loss.",
                    "analytical_use": None,
                    "warning": "AI did not evaluate this column — review manually.",
                })

        return final

    except Exception as e:
        logger.error(
            f"[GPT CALL FAILED] analyze_columns_for_header_gate — "
            f"{type(e).__name__}: {e}. Falling back to heuristics."
        )
        return _deterministic_column_analysis(columns, sample_rows, filename, df)


# ── Legacy compatibility wrapper ──────────────────────────────────────────────

def evaluate_column_relevance(
    columns: List[str],
    sample_rows: List[Dict[str, Any]],
    filename: str,
) -> Dict[str, Any]:
    """
    Legacy wrapper kept for callers that still use the old signature.
    Delegates to analyze_columns_for_header_gate and re-shapes to old format.
    """
    results = analyze_columns_for_header_gate(columns, sample_rows, filename)

    keep_count = sum(1 for r in results if r["decision"] == "keep")
    overall = "useful" if keep_count > 0 else "not_useful"
    reason = (
        f"Analysis of '{filename}': "
        f"{keep_count} column(s) recommended to keep, "
        f"{len(results) - keep_count} flagged for removal."
    )

    legacy_cols = [
        {
            "name": r["column"],
            "recommendation": "keep" if r["decision"] == "keep" else "remove",
            "reason": r["why"],
        }
        for r in results
    ]

    return {"overall_verdict": overall, "reason": reason, "columns": legacy_cols}
