"""
Universal Derived Metrics Engine — domain-agnostic computed columns.

After cleaning and before chart generation, this module scans the cleaned
DataFrame for recognisable column-name patterns and computes all applicable
derived metrics.  The engine is entirely pattern-based: it does NOT hard-code
domain knowledge (no "this is a sales file").  It only knows column-name
substrings and HTYPE codes.

Usage in the pipeline (process_csv.py):
    from app.services.derived_metrics import compute_all_derived_metrics

    cleaned_df, derived_info = compute_all_derived_metrics(cleaned_df)
    # cleaned_df now has extra columns; derived_info is metadata for storage.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd


# ── Pattern-matching helper ───────────────────────────────────────────────────

def _find_col(columns: list[str], patterns: list[str]) -> Optional[str]:
    """Return the first column whose lowercased name contains any pattern."""
    lookup = {
        c.lower().replace(" ", "_").replace("-", "_"): c for c in columns
    }
    for pat in patterns:
        for key, original in lookup.items():
            if pat in key:
                return original
    return None


# ── The universal derived-metric registry ─────────────────────────────────────
#
# Each entry declares:
#   name             – new column name added to the DataFrame
#   label            – human-readable label for chart axes / tooltips
#   requires_patterns – list of pattern-groups; one column must match per group
#   formula          – callable(df, matched_cols) → Series, OR "yoy" / "mom"
#   htype            – HTYPE code for the derived column
#   domain_hint      – informational only (never used for logic)

UNIVERSAL_DERIVED_METRICS: list[dict] = [

    # ── Financial / Sales ─────────────────────────────────────────────────
    {
        "name": "profit_margin_pct",
        "label": "Profit Margin %",
        "requires_patterns": [
            ["profit"],
            ["amount", "revenue", "sales", "income"],
        ],
        "formula": lambda df, cols: (
            pd.to_numeric(df[cols[0]], errors="coerce")
            / pd.to_numeric(df[cols[1]], errors="coerce").replace(0, float("nan"))
            * 100
        ).round(2),
        "htype": "HTYPE-017",
        "domain_hint": "sales",
    },
    {
        "name": "revenue_per_unit",
        "label": "Revenue per Unit",
        "requires_patterns": [
            ["amount", "revenue", "sales"],
            ["quantity", "qty", "units"],
        ],
        "formula": lambda df, cols: (
            pd.to_numeric(df[cols[0]], errors="coerce")
            / pd.to_numeric(df[cols[1]], errors="coerce").replace(0, float("nan"))
        ).round(2),
        "htype": "HTYPE-015",
        "domain_hint": "sales",
    },
    {
        "name": "profit_per_unit",
        "label": "Profit per Unit",
        "requires_patterns": [
            ["profit"],
            ["quantity", "qty", "units"],
        ],
        "formula": lambda df, cols: (
            pd.to_numeric(df[cols[0]], errors="coerce")
            / pd.to_numeric(df[cols[1]], errors="coerce").replace(0, float("nan"))
        ).round(2),
        "htype": "HTYPE-015",
        "domain_hint": "sales",
    },

    # ── HR / Payroll ──────────────────────────────────────────────────────
    {
        "name": "salary_per_experience_year",
        "label": "Salary per Year of Experience",
        "requires_patterns": [
            ["salary", "ctc", "pay", "wage"],
            ["experience", "years", "tenure"],
        ],
        "formula": lambda df, cols: (
            pd.to_numeric(df[cols[0]], errors="coerce")
            / pd.to_numeric(df[cols[1]], errors="coerce").replace(0, float("nan"))
        ).round(2),
        "htype": "HTYPE-015",
        "domain_hint": "hr",
    },

    # ── Education ─────────────────────────────────────────────────────────
    {
        "name": "pass_rate_pct",
        "label": "Pass Rate %",
        "requires_patterns": [
            ["pass", "passed"],
            ["total", "count", "students", "enrolled"],
        ],
        "formula": lambda df, cols: (
            pd.to_numeric(df[cols[0]], errors="coerce")
            / pd.to_numeric(df[cols[1]], errors="coerce").replace(0, float("nan"))
            * 100
        ).round(2),
        "htype": "HTYPE-017",
        "domain_hint": "education",
    },
    {
        "name": "attendance_rate_pct",
        "label": "Attendance Rate %",
        "requires_patterns": [
            ["present", "attended", "attendance"],
            ["total", "enrolled", "count"],
        ],
        "formula": lambda df, cols: (
            pd.to_numeric(df[cols[0]], errors="coerce")
            / pd.to_numeric(df[cols[1]], errors="coerce").replace(0, float("nan"))
            * 100
        ).round(2),
        "htype": "HTYPE-017",
        "domain_hint": "education",
    },

    # ── Healthcare ────────────────────────────────────────────────────────
    {
        "name": "length_of_stay_days",
        "label": "Length of Stay (Days)",
        "requires_patterns": [
            ["discharge", "discharge_date", "exit"],
            ["admission", "admit", "entry"],
        ],
        "formula": lambda df, cols: (
            pd.to_datetime(df[cols[0]], errors="coerce")
            - pd.to_datetime(df[cols[1]], errors="coerce")
        ).dt.days,
        "htype": "HTYPE-033",
        "domain_hint": "healthcare",
    },

    # ── Logistics / Delivery ──────────────────────────────────────────────
    {
        "name": "revenue_per_km",
        "label": "Revenue per KM",
        "requires_patterns": [
            ["amount", "revenue", "earnings", "payment"],
            ["distance", "km", "miles"],
        ],
        "formula": lambda df, cols: (
            pd.to_numeric(df[cols[0]], errors="coerce")
            / pd.to_numeric(df[cols[1]], errors="coerce").replace(0, float("nan"))
        ).round(2),
        "htype": "HTYPE-015",
        "domain_hint": "logistics",
    },
    {
        "name": "orders_per_rider",
        "label": "Orders per Rider",
        "requires_patterns": [
            ["orders", "order_count", "deliveries"],
            ["riders", "agents", "drivers"],
        ],
        "formula": lambda df, cols: (
            pd.to_numeric(df[cols[0]], errors="coerce")
            / pd.to_numeric(df[cols[1]], errors="coerce").replace(0, float("nan"))
        ).round(2),
        "htype": "HTYPE-016",
        "domain_hint": "logistics",
    },

    # ── Universal (any domain) ────────────────────────────────────────────
    {
        "name": "yoy_change_pct",
        "label": "Year-over-Year Change %",
        "requires_patterns": [
            ["year", "yr"],
            ["amount", "revenue", "count", "total", "value"],
        ],
        "formula": "yoy",
        "htype": "HTYPE-017",
        "domain_hint": "any",
    },
    {
        "name": "growth_rate_pct",
        "label": "Month-over-Month Growth %",
        "requires_patterns": [
            ["month", "year_month", "period"],
            ["amount", "revenue", "count"],
        ],
        "formula": "mom",
        "htype": "HTYPE-017",
        "domain_hint": "any",
    },
]


# ── Special handlers for YoY / MoM ───────────────────────────────────────────

def _compute_yoy(df: pd.DataFrame, time_col: str, value_col: str) -> pd.Series:
    """Compute year-over-year % change on already-aggregated yearly data."""
    tmp = df[[time_col, value_col]].copy()
    tmp["_yr"] = pd.to_numeric(tmp[time_col], errors="coerce")
    tmp["_val"] = pd.to_numeric(tmp[value_col], errors="coerce")
    tmp = tmp.sort_values("_yr")
    tmp["_prev"] = tmp["_val"].shift(1)
    result = ((tmp["_val"] - tmp["_prev"]) / tmp["_prev"].replace(0, float("nan")) * 100).round(2)
    return result


def _compute_mom(df: pd.DataFrame, time_col: str, value_col: str) -> pd.Series:
    """Compute month-over-month % change on period-sorted data."""
    tmp = df[[time_col, value_col]].copy()
    tmp["_val"] = pd.to_numeric(tmp[value_col], errors="coerce")
    tmp = tmp.sort_values(time_col)
    tmp["_prev"] = tmp["_val"].shift(1)
    result = ((tmp["_val"] - tmp["_prev"]) / tmp["_prev"].replace(0, float("nan")) * 100).round(2)
    return result


# ── Public API ────────────────────────────────────────────────────────────────

def compute_all_derived_metrics(
    df: pd.DataFrame,
    htype_map: dict | None = None,
) -> tuple[pd.DataFrame, list[dict]]:
    """
    Compute all applicable derived metrics for any dataset.

    Scans UNIVERSAL_DERIVED_METRICS for pattern matches against the
    DataFrame's column names.  Each successfully computed metric adds a
    new column to *df* and an entry to the returned metadata list.

    Never crashes — each metric is independently try/excepted.

    Args:
        df:         The cleaned DataFrame (will be copied internally).
        htype_map:  Optional {col: htype} map (reserved for future filtering).

    Returns:
        (enriched_df, derived_info)
        enriched_df   – DataFrame with new derived columns appended
        derived_info  – list of metadata dicts describing each added column
    """
    df = df.copy()
    columns = df.columns.tolist()
    derived_info: list[dict] = []

    for metric in UNIVERSAL_DERIVED_METRICS:
        try:
            # ── Resolve required columns ──────────────────────────────
            matched_cols: list[str] = []
            for pattern_group in metric["requires_patterns"]:
                col = _find_col(columns, pattern_group)
                if col is not None:
                    matched_cols.append(col)

            if len(matched_cols) < len(metric["requires_patterns"]):
                continue  # prerequisite columns not present

            # Avoid creating a derived column that already exists
            if metric["name"] in df.columns:
                continue

            # ── Compute ───────────────────────────────────────────────
            formula = metric["formula"]

            if callable(formula):
                df[metric["name"]] = formula(df, matched_cols)

            elif formula == "yoy":
                df[metric["name"]] = _compute_yoy(df, matched_cols[0], matched_cols[1])

            elif formula == "mom":
                df[metric["name"]] = _compute_mom(df, matched_cols[0], matched_cols[1])

            else:
                continue  # unknown formula type

            # ── Validate: only keep if non-trivial ────────────────────
            if metric["name"] not in df.columns:
                continue
            valid_count = df[metric["name"]].notna().sum()
            if valid_count == 0:
                df.drop(columns=[metric["name"]], inplace=True)
                continue

            derived_info.append({
                "name": metric["name"],
                "label": metric["label"],
                "htype": metric["htype"],
                "is_derived": True,
                "source_columns": matched_cols,
                "valid_values": int(valid_count),
                "domain_hint": metric["domain_hint"],
            })

        except Exception as exc:
            # Never crash the pipeline — silently skip this metric
            print(f"[DERIVED METRIC SKIP] {metric['name']}: {exc}")
            if metric["name"] in df.columns:
                df.drop(columns=[metric["name"]], inplace=True, errors="ignore")
            continue

    if derived_info:
        print(
            f"[DERIVED METRICS] Computed {len(derived_info)} derived columns: "
            f"{[d['name'] for d in derived_info]}"
        )
    else:
        print("[DERIVED METRICS] No applicable derived metrics for this dataset.")

    return df, derived_info
