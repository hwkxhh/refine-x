"""
Universal Chart Type Decision Engine — domain-agnostic.

Decides chart type based ONLY on column data types and cardinality.
No domain-specific rules (no "sales", "hospital", "logistics" knowledge).
Works for any file from any domain.
"""

from __future__ import annotations

from enum import Enum

import numpy as np
import pandas as pd


# ── Column kind classification ────────────────────────────────────────────────

class ColKind(Enum):
    DATE = "date"
    NUMERIC = "numeric"
    CATEGORY_TINY = "category_tiny"       # 2-6 unique values
    CATEGORY_SMALL = "category_small"     # 7-15 unique values
    CATEGORY_MEDIUM = "category_medium"   # 16-50 unique values
    CATEGORY_LARGE = "category_large"     # 51+ unique values
    ID = "id"                             # near-unique (>80% unique)
    BOOLEAN = "boolean"                   # exactly 2 unique values


def classify_column(series: pd.Series, col_name: str) -> ColKind:
    """Universal column classifier. Domain-agnostic.

    Order of checks matters:
    1. Already-datetime dtype → DATE
    2. Date keyword + parseable → DATE
    3. Numeric (including year-like) → NUMERIC or DATE
    4. Boolean (exactly 2 unique) → BOOLEAN
    5. ID (>80% unique, >50 unique, non-numeric text) → ID
    6. Category by cardinality
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return ColKind.CATEGORY_SMALL

    n_unique = non_null.nunique()
    n_total = len(non_null)
    unique_ratio = n_unique / n_total if n_total > 0 else 0

    name_lower = str(col_name).lower().replace("_", " ").replace("-", " ")

    # ── 1. Already datetime dtype → DATE ──────────────────────────────────
    if pd.api.types.is_datetime64_any_dtype(series):
        return ColKind.DATE

    # ── 2. Date keyword + parseable → DATE ────────────────────────────────
    date_keywords = [
        "date", "time", "month", "year", "period", "week", "day",
        "quarter", "created", "updated", "ordered", "timestamp",
    ]
    if any(kw in name_lower for kw in date_keywords):
        try:
            pd.to_datetime(non_null.head(10), errors="raise")
            return ColKind.DATE
        except Exception:
            pass

    # ── 3. Numeric check ─────────────────────────────────────────────────
    numeric = pd.to_numeric(non_null, errors="coerce")
    if numeric.notna().mean() > 0.85:
        # Year-like integers → treat as DATE
        if (
            name_lower.strip() == "year"
            or (numeric.between(1900, 2100).all() and n_unique < 50)
        ):
            return ColKind.DATE
        return ColKind.NUMERIC

    # ── 4. Boolean — exactly 2 unique values ──────────────────────────────
    if n_unique == 2:
        return ColKind.BOOLEAN

    # ── 5. ID — high cardinality non-numeric text ─────────────────────────
    if unique_ratio > 0.8 and n_unique > 50:
        return ColKind.ID

    # ── 6. Category by cardinality ────────────────────────────────────────
    if n_unique <= 6:
        return ColKind.CATEGORY_TINY
    elif n_unique <= 15:
        return ColKind.CATEGORY_SMALL
    elif n_unique <= 50:
        return ColKind.CATEGORY_MEDIUM
    else:
        return ColKind.CATEGORY_LARGE


# ── The universal chart type lookup table ─────────────────────────────────────
# (x_kind, y_kind) → chart decision
# y_kind can be a ColKind or the string "count" when no y column is provided.

CHART_TYPE_MATRIX: dict[tuple, dict] = {
    # ── Date x-axis ───────────────────────────────────────────────────────
    (ColKind.DATE, ColKind.NUMERIC): {
        "type": "line",
        "reason": (
            "Time series of a numeric metric. Line chart shows continuity "
            "and trend direction. Aggregated to appropriate time granularity "
            "based on date span."
        ),
    },
    (ColKind.DATE, ColKind.BOOLEAN): {
        "type": "bar",
        "reason": (
            "Count of boolean states over time. Bar chart shows how the "
            "yes/no split changes across periods."
        ),
    },
    (ColKind.DATE, "count"): {
        "type": "bar",
        "reason": (
            "Count of events per time period. Bar chart because each period "
            "is a discrete bucket — counting events, not tracking a "
            "continuous flow."
        ),
    },

    # ── Tiny category (2-6 unique) ────────────────────────────────────────
    (ColKind.CATEGORY_TINY, ColKind.NUMERIC): {
        "type": "bar",
        "reason": (
            "Few categories — vertical bar for clean side-by-side comparison. "
            "Sorted descending for immediate ranking visibility."
        ),
    },
    (ColKind.CATEGORY_TINY, "count"): {
        "type": "donut",
        "reason": (
            "Few categories with count — donut chart shows proportion of "
            "whole. Maximum 6 slices for readability."
        ),
    },

    # ── Small category (7-15 unique) ──────────────────────────────────────
    (ColKind.CATEGORY_SMALL, ColKind.NUMERIC): {
        "type": "bar",
        "reason": (
            "Moderate number of categories — vertical bar sorted descending "
            "for ranking comparison."
        ),
    },
    (ColKind.CATEGORY_SMALL, "count"): {
        "type": "bar",
        "reason": (
            "More than 6 categories with count — bar chart more readable "
            "than donut at this cardinality."
        ),
    },

    # ── Medium category (16-50 unique) ────────────────────────────────────
    (ColKind.CATEGORY_MEDIUM, ColKind.NUMERIC): {
        "type": "horizontal_bar",
        "reason": (
            "Many category values — horizontal bar for readability. Long "
            "names read better horizontally. Top 15 shown."
        ),
    },
    (ColKind.CATEGORY_MEDIUM, "count"): {
        "type": "horizontal_bar",
        "reason": (
            "Many categories with count — horizontal bar sorted descending. "
            "Shows ranking clearly."
        ),
    },

    # ── Large category (51+ unique) ───────────────────────────────────────
    (ColKind.CATEGORY_LARGE, ColKind.NUMERIC): {
        "type": "horizontal_bar",
        "reason": (
            "High cardinality column — showing top 10 only. Full list would "
            "be unreadable."
        ),
    },
    (ColKind.CATEGORY_LARGE, "count"): {
        "type": "horizontal_bar",
        "reason": (
            "High cardinality column — top 10 by count. Full list would be "
            "unreadable."
        ),
    },

    # ── Numeric vs numeric ────────────────────────────────────────────────
    (ColKind.NUMERIC, ColKind.NUMERIC): {
        "type": "scatter",
        "reason": (
            "Two numeric columns — scatter plot reveals correlation strength, "
            "direction, and outliers that aggregated charts hide."
        ),
    },

    # ── Boolean x-axis ────────────────────────────────────────────────────
    (ColKind.BOOLEAN, ColKind.NUMERIC): {
        "type": "bar",
        "reason": (
            "Boolean grouping with numeric metric — bar chart comparing the "
            "two groups."
        ),
    },
    (ColKind.BOOLEAN, "count"): {
        "type": "donut",
        "reason": (
            "Two-state boolean with count — donut shows the proportion split."
        ),
    },

    # ── ID column (should not plot, but provide sensible fallback) ────────
    (ColKind.ID, ColKind.NUMERIC): {
        "type": "horizontal_bar",
        "reason": (
            "ID-like column with many unique values — horizontal bar showing "
            "top 10 only."
        ),
    },
    (ColKind.ID, "count"): {
        "type": "horizontal_bar",
        "reason": (
            "ID-like column with count — horizontal bar showing top 10 only."
        ),
    },
}


# ── Public API (backwards-compatible) ─────────────────────────────────────────

def decide_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str | None,
    is_count: bool = False,
) -> dict:
    """
    Universal chart type decision.
    Works for any domain, any file, any column combination.
    Returns dict with 'type', 'reason', 'x_kind', 'y_kind'.
    """
    if x_col not in df.columns:
        return {
            "type": "bar",
            "reason": f"Column '{x_col}' not found — defaulting to bar.",
            "x_kind": "unknown",
            "y_kind": "count" if is_count else "unknown",
        }

    x_kind = classify_column(df[x_col], x_col)
    y_kind: ColKind | str = "count"

    if not is_count and y_col and y_col in df.columns:
        y_kind = classify_column(df[y_col], y_col)

    # Look up in matrix
    decision = CHART_TYPE_MATRIX.get((x_kind, y_kind))

    if not decision:
        # Fallback
        decision = {
            "type": "bar",
            "reason": (
                f"Default bar chart for {x_kind.value} × "
                f"{y_kind if isinstance(y_kind, str) else y_kind.value}."
            ),
        }

    return {
        **decision,
        "x_kind": x_kind.value,
        "y_kind": y_kind if isinstance(y_kind, str) else y_kind.value,
    }


def determine_chart_type(
    x_col: str,
    y_col: str | None,
    df: pd.DataFrame,
    group_by: str | None = None,
) -> dict:
    """
    Drop-in replacement for the old rulebook.

    Signature & return shape are identical:
        {
            "chart_type": str,
            "reason": str,
            "group_by": str | None,
        }
    """
    is_count = not y_col or y_col not in df.columns

    result = decide_chart(df, x_col, y_col, is_count=is_count)
    chart_type = result["type"]

    # When the chart is a line/area with date x and there's a group_by,
    # keep the group_by so ChartEngine renders multi-series.
    resolved_group_by = group_by
    if chart_type == "line" and group_by and group_by in df.columns:
        resolved_group_by = group_by

    return {
        "chart_type": chart_type,
        "reason": result["reason"],
        "group_by": resolved_group_by,
    }


def precompute_chart_types(
    vizzes: list[dict],
    df: pd.DataFrame,
) -> list[dict]:
    """
    Run the engine on every RecommendedViz entry, replacing/enriching the
    chart_type with the universal decision + reason.

    Each viz dict must have x_column, y_column, and optionally group_by.
    Returns the same list with chart_type, chart_type_reason, and group_by updated.
    """
    enriched = []
    for v in vizzes:
        x = v.get("x_column", "")
        y = v.get("y_column") or None
        gb = v.get("group_by") or None
        result = determine_chart_type(x, y, df, group_by=gb)
        enriched.append({
            **v,
            "chart_type": result["chart_type"],
            "chart_type_reason": result["reason"],
            "group_by": result.get("group_by"),
        })
    return enriched
