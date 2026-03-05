"""
AI Recommendation Engine — Stage 4: Strict JSON chart specifications.
Uses GPT-4o to suggest chart column pairings based on user's analytical goal.
Includes dataset structure detection (flat / longitudinal / cross_sectional)
so the AI can recommend appropriate multi-series charts for longitudinal data.
"""

import json
import re

import pandas as pd
from openai import OpenAI

from app.config import settings
from app.services.chart_type_rules import determine_chart_type as _rulebook_determine

_client = OpenAI(api_key=settings.OPENAI_API_KEY)

# Fixed allowed chart types - ChartEngine must support all of these
ALLOWED_CHART_TYPES = [
    "bar",
    "horizontal_bar",
    "line",
    "scatter",
    "pie",
    "donut",
    "stacked_bar",
    "area",
    "heatmap",
]


def _parse_json(text: str):
    clean = re.sub(r"```[a-z]*\n?", "", text).strip()
    # Strip trailing commas before closing brackets (common GPT mistake)
    clean = re.sub(r",\s*([\]}])", r"\1", clean)
    return json.loads(clean)


def _is_year_col(series: pd.Series) -> bool:
    """True if the column looks like 4-digit years (1800–2100)."""
    nums = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    if nums.empty:
        return False
    return bool((nums >= 1800).all() and (nums <= 2100).all())


def _is_time_col(col_name: str, series: pd.Series) -> bool:
    """True if column name or values suggest it's a date/time/year column."""
    name_lower = str(col_name).lower()
    time_keywords = ["year", "date", "time", "month", "quarter", "period",
                     "fiscal", "semester", "week", "day"]
    if any(k in name_lower for k in time_keywords):
        return True
    return _is_year_col(series)


def _is_categorical_col(col_name: str, series: pd.Series) -> bool:
    """True if column is low-cardinality string — a likely entity identifier."""
    if series.dtype not in (object, "category"):
        return False
    n_unique = series.nunique()
    n_total = len(series)
    # Between 2 and 100 unique values, not too sparse
    return 2 <= n_unique <= min(100, n_total * 0.5)


def detect_dataset_type(df: pd.DataFrame) -> dict:
    """
    Classify the dataset structure as one of:
      flat          — one row = one entity
      longitudinal  — one row = one entity at one point in time
      cross_sectional — one row = one observation at one moment

    Also returns:
      time_col   — name of the detected time/year column (or None)
      entity_col — name of the detected categorical entity column (or None)
    """
    time_cols = [c for c in df.columns if _is_time_col(c, df[c])]
    cat_cols = [c for c in df.columns if _is_categorical_col(c, df[c])]

    # Longitudinal: has both a time column AND a categorical column where
    # the same categorical value repeats across multiple time values
    if time_cols and cat_cols:
        for cat_col in cat_cols:
            for time_col in time_cols:
                # Check: same entity appears more than once (different time values)
                counts = df.groupby(cat_col)[time_col].nunique()
                if counts.max() >= 2:
                    return {
                        "dataset_type": "longitudinal",
                        "time_col": time_col,
                        "entity_col": cat_col,
                    }

    if time_cols:
        return {"dataset_type": "cross_sectional", "time_col": time_cols[0], "entity_col": None}

    return {"dataset_type": "flat", "time_col": None, "entity_col": None}


def _deterministic_recommendations(
    column_names: list[str],
    df: pd.DataFrame,
    structure: dict,
) -> list[dict]:
    """
    Fallback when GPT is unavailable: build sensible recommendations from
    column types and detected dataset structure, using the chart-type rulebook.
    """
    recs = []
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    cat_cols = [c for c in column_names if _is_categorical_col(c, df[c])]
    time_col = structure.get("time_col")
    entity_col = structure.get("entity_col")
    dataset_type = structure.get("dataset_type", "flat")

    def _add(x, y, gb=None, score=0.85, title=None):
        r = _rulebook_determine(x, y, df, group_by=gb)
        recs.append({
            "chart_title": title or f"{(y or 'Count').replace('_', ' ').title()} by {x.replace('_', ' ').title()}",
            "chart_type": r["chart_type"],
            "x_col": x,
            "y_col": y,
            "group_by": r.get("group_by") or gb,
            "relevance_score": score,
            "reasoning": r["reason"],
        })

    if dataset_type == "longitudinal" and time_col and entity_col and numeric_cols:
        y = numeric_cols[0]
        _add(time_col, y, gb=entity_col, score=0.95,
             title=f"{y.replace('_', ' ').title()} Over Time by {entity_col.replace('_', ' ').title()}")
        if len(numeric_cols) >= 2:
            _add(time_col, numeric_cols[1], gb=entity_col, score=0.88,
                 title=f"{numeric_cols[1].replace('_', ' ').title()} Over Time by {entity_col.replace('_', ' ').title()}")

    if cat_cols and numeric_cols:
        _add(cat_cols[0], numeric_cols[0], score=0.85,
             title=f"{numeric_cols[0].replace('_', ' ').title()} by {cat_cols[0].replace('_', ' ').title()}")

    if numeric_cols and len(numeric_cols) >= 2:
        _add(numeric_cols[0], numeric_cols[1], score=0.80,
             title=f"{numeric_cols[1].replace('_', ' ').title()} vs {numeric_cols[0].replace('_', ' ').title()}")

    if time_col and numeric_cols:
        _add(time_col, numeric_cols[0], score=0.90,
             title=f"{numeric_cols[0].replace('_', ' ').title()} Over {time_col.replace('_', ' ').title()}")

    return recs[:5]


def recommend_headers(
    column_names: list[str],
    data_sample: list[dict],
    user_goal: str,
    df: pd.DataFrame | None = None,
) -> list[dict]:
    """
    Stage 4: Returns strict JSON chart specifications.

    Each item:
    {
        "chart_title": str,
        "chart_type": str,
        "x_col": str,
        "y_col": str | null,
        "group_by": str | null,   ← NEW: for longitudinal multi-series charts
        "relevance_score": float,
        "reasoning": str,
    }
    """
    # ── Detect dataset structure ──────────────────────────────────────────
    if df is not None:
        structure = detect_dataset_type(df)
    else:
        # Build a minimal df from the sample for detection
        try:
            structure = detect_dataset_type(pd.DataFrame(data_sample))
        except Exception:
            structure = {"dataset_type": "flat", "time_col": None, "entity_col": None}

    dataset_type = structure["dataset_type"]
    time_col = structure.get("time_col")
    entity_col = structure.get("entity_col")

    columns_text = ", ".join(f'"{c}"' for c in column_names)
    sample_text = json.dumps(data_sample[:5], default=str, indent=2)
    chart_types_text = ", ".join(ALLOWED_CHART_TYPES)

    longitudinal_note = ""
    group_by_note = ""
    if dataset_type == "longitudinal":
        longitudinal_note = f"""
IMPORTANT — This dataset is LONGITUDINAL (one row = one entity at one point in time).
Time column: "{time_col}"   Entity column: "{entity_col}"
- Always group line/area charts by "{entity_col}" so each entity gets its own series.
- Never recommend scatter or bar charts where both axes are raw values without a groupBy.
- The "group_by" field MUST be set to "{entity_col}" for all line/area recommendations."""
        group_by_note = f', "group_by": "{entity_col}" (required for line/area charts)'

    prompt = f"""You are a data analyst helping a user visualize their data.

Dataset type: {dataset_type}{longitudinal_note}
Dataset columns: [{columns_text}]
Sample data (first 5 rows):
{sample_text}

User's analytical goal: "{user_goal}"

Recommend exactly 5 chart specifications. ALLOWED chart types: {chart_types_text}

Rules:
- x_col and y_col MUST be DIFFERENT columns — never the same column for both
- Only use column names that exist exactly in the columns list above
- For pie/donut charts, set y_col to null
- chart_title must be descriptive (e.g. "Electricity Access Over Time by Country")
- For longitudinal data: line charts must include group_by

Return ONLY valid JSON (no markdown fences):
[
  {{
    "chart_title": "Electricity Access Over Time by Country",
    "chart_type": "line",
    "x_col": "year",
    "y_col": "electricity_access_percent",
    "group_by": "country"{group_by_note.split(",")[0] if group_by_note else ""},
    "relevance_score": 0.95,
    "reasoning": "Shows how electricity access changed per country over time"
  }}
]"""

    try:
        response = _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1800,
        )
        result = _parse_json(response.choices[0].message.content)
        if isinstance(result, dict):
            result = list(result.values())[0] if result else []
    except Exception:
        if df is not None:
            return _deterministic_recommendations(column_names, df, structure)
        return []

    # ── Validate and normalise ────────────────────────────────────────────
    validated = []
    for item in result[:5]:
        chart_type = str(item.get("chart_type", "bar")).lower()
        if chart_type not in ALLOWED_CHART_TYPES:
            chart_type = "bar"

        x_col = item.get("x_col") or item.get("x_column")
        y_col = item.get("y_col") or item.get("y_column")
        group_by = item.get("group_by") or None

        if not x_col or x_col not in column_names:
            continue
        if y_col and y_col not in column_names:
            y_col = None
        if group_by and group_by not in column_names:
            group_by = None

        # Fix 2: block same-column charts
        if y_col == x_col:
            y_col = None
            chart_type = "pie"

        # For longitudinal line/area charts without group_by, inject it
        if dataset_type == "longitudinal" and chart_type in ("line", "area") and not group_by and entity_col:
            group_by = entity_col

        # Apply chart-type rulebook: override GPT choice with analyst logic
        if df is not None:
            rule_result = _rulebook_determine(x_col, y_col, df, group_by=group_by)
            chart_type = rule_result["chart_type"]
            group_by = rule_result.get("group_by") or group_by
            rulebook_reasoning = rule_result["reason"]
        else:
            rulebook_reasoning = ""

        validated.append({
            "chart_title": item.get("chart_title", f"{y_col or 'Count'} by {x_col}"),
            "chart_type": chart_type,
            "x_col": x_col,
            "y_col": y_col,
            "group_by": group_by,
            "relevance_score": float(item.get("relevance_score", 0.8)),
            "reasoning": item.get("reasoning", item.get("reason", "")) or rulebook_reasoning,
        })

    return validated
