"""
Universal Chart Suite Generator — domain-agnostic automatic chart production.

Given a DataFrame, its htype map, and optional derived-column metadata, this
module produces the complete set of charts a professional analyst would create.

It works ONLY with column types and cardinality (via ColKind and the chart
type matrix).  It does NOT know about sales, hospitals, schools, or logistics.
"""

from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from app.services.chart_type_rules import (
    ColKind,
    classify_column,
    decide_chart,
)


# ── Formatting helper ─────────────────────────────────────────────────────────

def _label(col_name: str) -> str:
    """Convert 'order_date' → 'Order Date'."""
    return col_name.replace("_", " ").title()


# ── Signature helper ──────────────────────────────────────────────────────────

def _chart_sig(x: str | None, y: str | None, chart_type: str) -> str:
    return f"{(x or '').lower()}|{(y or '').lower()}|{chart_type.lower()}"


# ── The universal engine (core) ───────────────────────────────────────────────

def _generate_universal_chart_suite(
    df: pd.DataFrame,
    htypes: dict,
    goal: str = "",
    derived_columns: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Core engine: build chart specs from column types and cardinality alone.
    Does not know about sales, hospitals, schools, or logistics.
    Only knows about column types, cardinality, and data patterns.
    """
    charts: list[dict] = []
    columns = df.columns.tolist()

    # ── Classify every column ─────────────────────────────────────────────
    col_kinds: dict[str, ColKind] = {}
    for col in columns:
        col_kinds[col] = classify_column(df[col], col)

    # ── Bucket columns by kind ────────────────────────────────────────────
    date_cols = [c for c, k in col_kinds.items() if k == ColKind.DATE]
    numeric_cols = [c for c, k in col_kinds.items() if k == ColKind.NUMERIC]
    category_cols = [c for c, k in col_kinds.items()
                     if k in (ColKind.CATEGORY_TINY, ColKind.CATEGORY_SMALL,
                              ColKind.CATEGORY_MEDIUM, ColKind.CATEGORY_LARGE)]
    bool_cols = [c for c, k in col_kinds.items() if k == ColKind.BOOLEAN]
    id_cols = [c for c, k in col_kinds.items() if k == ColKind.ID]

    # Limit to avoid chart overload
    primary_numerics = numeric_cols[:3]

    # ── RULE SET 1: Date × Numeric → trend lines ─────────────────────────
    for date_col in date_cols[:2]:
        for num_col in primary_numerics:
            charts.append({
                "title": f"{_label(num_col)} Over Time",
                "chart_type": "line",
                "x_col": date_col,
                "y_col": num_col,
                "group_by": None,
                "reason": (
                    f"Line chart tracking {num_col} over time. Aggregated to "
                    f"appropriate granularity based on date span. Lines show "
                    f"continuity and trend direction."
                ),
            })
        # Count over time → bar
        charts.append({
            "title": "Volume Over Time",
            "chart_type": "bar",
            "x_col": date_col,
            "y_col": None,
            "group_by": None,
            "reason": (
                "Bar chart counting events per time period. Each bar is a "
                "discrete count — bars communicate discrete counting better "
                "than a continuous line."
            ),
        })

    # ── RULE SET 2: Category × Numeric → bar / horiz / donut ─────────────
    for cat_col in category_cols:
        for num_col in primary_numerics:
            decision = decide_chart(df, cat_col, num_col)
            if decision["type"]:
                charts.append({
                    "title": f"{_label(num_col)} by {_label(cat_col)}",
                    "chart_type": decision["type"],
                    "x_col": cat_col,
                    "y_col": num_col,
                    "group_by": None,
                    "reason": decision["reason"],
                })

        # Count per category
        count_decision = decide_chart(df, cat_col, "count", is_count=True)
        if count_decision["type"]:
            charts.append({
                "title": f"Count by {_label(cat_col)}",
                "chart_type": count_decision["type"],
                "x_col": cat_col,
                "y_col": None,
                "group_by": None,
                "reason": count_decision["reason"],
            })

    # ── RULE SET 3: Numeric × Numeric → scatter (top pairs) ──────────────
    if len(numeric_cols) >= 2:
        for i in range(min(len(numeric_cols), 3)):
            for j in range(i + 1, min(len(numeric_cols), 4)):
                x_col, y_col = numeric_cols[i], numeric_cols[j]
                charts.append({
                    "title": f"{_label(y_col)} vs {_label(x_col)}",
                    "chart_type": "scatter",
                    "x_col": x_col,
                    "y_col": y_col,
                    "group_by": None,
                    "reason": (
                        f"Scatter plot to reveal the relationship between "
                        f"{x_col} and {y_col}. Shows correlation direction, "
                        f"strength, and any outliers."
                    ),
                })

    # ── RULE SET 4: Boolean × Numeric → comparison bars ───────────────────
    for bool_col in bool_cols:
        for num_col in primary_numerics[:2]:
            charts.append({
                "title": f"{_label(num_col)} by {_label(bool_col)}",
                "chart_type": "bar",
                "x_col": bool_col,
                "y_col": num_col,
                "group_by": None,
                "reason": (
                    f"Bar chart comparing {num_col} between the two "
                    f"{bool_col} groups. Shows whether the boolean flag has "
                    f"a meaningful impact on {num_col}."
                ),
            })

    # ── RULE SET 5: High-cardinality category → top-N horizontal bar ─────
    for cat_col in category_cols:
        if df[cat_col].nunique() > 15:
            for num_col in primary_numerics[:2]:
                charts.append({
                    "title": f"Top 10 {_label(cat_col)} by {_label(num_col)}",
                    "chart_type": "horizontal_bar",
                    "x_col": cat_col,
                    "y_col": num_col,
                    "group_by": None,
                    "reason": (
                        f"Top 10 {cat_col} values by {num_col}. Horizontal "
                        f"bar because names are long. Limited to 10 — showing "
                        f"all {df[cat_col].nunique()} values would be "
                        f"unreadable."
                    ),
                })

    # ── RULE SET 6: Derived metrics → same rules as numeric ──────────────
    for derived in (derived_columns or []):
        d_name = derived.get("name", "")
        d_label = derived.get("label", _label(d_name))
        source = derived.get("source_columns", [])

        if d_name not in df.columns:
            continue

        # Time trend for derived metric
        for date_col in date_cols[:1]:
            charts.append({
                "title": f"{d_label} Over Time",
                "chart_type": "line",
                "x_col": date_col,
                "y_col": d_name,
                "group_by": None,
                "reason": (
                    f"Derived metric '{d_label}' plotted over time. Shows "
                    f"whether the computed ratio/rate is improving, declining, "
                    f"or stable."
                ),
            })

        # By category
        for cat_col in category_cols:
            if df[cat_col].nunique() <= 15:
                ct = "bar" if df[cat_col].nunique() <= 7 else "horizontal_bar"
                charts.append({
                    "title": f"{d_label} by {_label(cat_col)}",
                    "chart_type": ct,
                    "x_col": cat_col,
                    "y_col": d_name,
                    "group_by": None,
                    "reason": (
                        f"{d_label} grouped by {cat_col}. Derived metric "
                        f"computed from source columns: "
                        f"{', '.join(source)}."
                    ),
                })

    # ── DEDUP (internal) ──────────────────────────────────────────────────
    seen: set[tuple] = set()
    unique: list[dict] = []
    for c in charts:
        key = (c["x_col"], c.get("y_col"), c["chart_type"])
        if key not in seen:
            seen.add(key)
            unique.append(c)

    # ── CAP at 15 charts — priority by rule-set order ─────────────────────
    return unique[:15]


# ── Public API ────────────────────────────────────────────────────────────────

def generate_full_chart_suite(
    df: pd.DataFrame,
    htypes: Optional[dict] = None,
    goal: str = "",
    existing_charts: Optional[list[dict]] = None,
    derived_columns: Optional[list[dict]] = None,
) -> list[dict]:
    """
    Produce the full analyst-grade chart suite for any dataset.

    Args:
        df:               The cleaned DataFrame.
        htypes:           Optional {column_name: htype_code} map (reserved).
        goal:             User's analytical goal text (reserved).
        existing_charts:  Already-generated chart dicts for dedup.
        derived_columns:  Metadata list from compute_all_derived_metrics().

    Returns:
        List of chart spec dicts ready to be passed to ChartEngine:
        [
            {
                "title": str,
                "chart_type": str,
                "x_col": str,
                "y_col": str | None,
                "group_by": str | None,
                "reason": str,
            },
            ...
        ]
    """
    charts = _generate_universal_chart_suite(
        df=df,
        htypes=htypes or {},
        goal=goal,
        derived_columns=derived_columns,
    )

    # ── Deduplicate against existing charts ───────────────────────────────
    existing_sigs: set[str] = set()
    if existing_charts:
        for ec in existing_charts:
            sig = _chart_sig(
                ec.get("x_col", ec.get("x_header", "")),
                ec.get("y_col", ec.get("y_header", "")),
                ec.get("chart_type", ""),
            )
            existing_sigs.add(sig)

    suite: list[dict] = []
    seen: set[str] = set()

    for spec in charts:
        sig = _chart_sig(spec["x_col"], spec.get("y_col"), spec["chart_type"])
        if sig in existing_sigs or sig in seen:
            continue

        # Validate columns still exist
        if spec["x_col"] not in df.columns:
            continue
        y = spec.get("y_col")
        if y and y != "count" and y not in df.columns:
            continue

        seen.add(sig)
        suite.append(spec)

    return suite
