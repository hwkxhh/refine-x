"""
Universal Column Role Classifier — runs before any chart is generated.

Classifies every column into a role that determines whether it can be
used as a chart axis, and in what capacity (X, Y, or never).

This is the single most important guard in the chart system.
No column classified as IDENTIFIER, SEQUENCE, CONSTANT, or DERIVED_ID
should ever appear on any chart axis.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class ColumnRole(Enum):
    # ── Usable as axes ────────────────────────────────────────────────────
    DATE = "date"           # Time axis — aggregate then plot
    METRIC = "metric"       # Numeric measure — sum, avg, count
    CATEGORY = "category"   # Group by this — bar, donut
    BOOLEAN = "boolean"     # Two-value grouping

    # ── Never use as axis ─────────────────────────────────────────────────
    IDENTIFIER = "identifier"           # Row ID, order number, serial
    CODE = "code"                       # NAICS, ZIP, ICD — categorical meaning
    HIGH_CARDINALITY_TEXT = "hct"       # Free text / names — too many unique values
    CONSTANT = "constant"               # Same value every row — useless
    SEQUENCE = "sequence"               # 1,2,3,4… row numbers — meaningless
    DERIVED_ID = "derived_id"           # Computed IDs, hashes


# ── Name-pattern tables ───────────────────────────────────────────────────────

_ID_PATTERNS = [
    r"_id$", r"^id_", r"^id$", r"order_id", r"row_id", r"record_id",
    r"serial", r"no$", r"^no_", r"number$", r"num$", r"^index$",
    r"invoice", r"transaction", r"reference", r"^ref_", r"_ref$",
    r"uuid", r"guid", r"hash",
]

_CODE_PATTERNS = [
    "naics", "sic", "zip", "postal", "pin",
    "icd", "cpt", "npi", "fips", "hs_code", "tariff",
    "sku", "upc", "isbn", "asin", "product_code",
    "dept_code", "class_code", "grade_code", "region_code",
]

# Any column name containing "code" is treated as a classification code
_CODE_SUBSTRING = "code"

_DATE_PATTERNS = [
    "date", "time", "month", "year", "period",
    "week", "day", "quarter", "timestamp", "created",
    "updated", "modified", "admitted", "discharged",
    "enrolled", "joined", "dob", "birth",
]


def classify_column_role(series: pd.Series, col_name: str) -> ColumnRole:
    """
    Classify a single column into a ColumnRole.

    Call order matters — more specific / certain rules fire first.
    """
    col_lower = col_name.lower().replace(" ", "_").replace("-", "_")
    non_null = series.dropna()
    n_total = len(non_null)

    if n_total == 0:
        return ColumnRole.CONSTANT

    n_unique = non_null.nunique()
    unique_ratio = n_unique / n_total

    # ── RULE 1: Constant column ───────────────────────────────────────────
    if n_unique == 1:
        return ColumnRole.CONSTANT

    # ── RULE 2: Boolean ───────────────────────────────────────────────────
    if n_unique == 2:
        return ColumnRole.BOOLEAN

    # ── RULE 3: Sequence detection (1,2,3,4… or perfectly uniform steps) ─
    try:
        numeric = pd.to_numeric(non_null, errors="coerce").dropna()
        if len(numeric) > 10 and numeric.is_monotonic_increasing:
            diffs = numeric.diff().dropna()
            if diffs.std() < 0.01:   # perfectly uniform steps
                return ColumnRole.SEQUENCE
    except Exception:
        pass

    # ── RULE 4: Identifier — name pattern + high uniqueness ───────────────
    for pattern in _ID_PATTERNS:
        if re.search(pattern, col_lower):
            if unique_ratio > 0.7:
                return ColumnRole.IDENTIFIER

    # ── RULE 5: Code column — classification codes, not measures ─────────
    if _CODE_SUBSTRING in col_lower:
        return ColumnRole.CODE
    for pattern in _CODE_PATTERNS:
        if pattern in col_lower:
            return ColumnRole.CODE

    # ── RULE 6: Date column ───────────────────────────────────────────────
    if any(p in col_lower for p in _DATE_PATTERNS):
        # Try parsing as real dates
        try:
            sample = non_null.head(20).astype(str)
            parsed = pd.to_datetime(sample, errors="coerce")
            if parsed.notna().mean() > 0.7:
                return ColumnRole.DATE
        except Exception:
            pass
        # Year-like integer column (1900–2100 range, low cardinality)
        try:
            numeric = pd.to_numeric(non_null, errors="coerce").dropna()
            if not numeric.empty and numeric.between(1900, 2100).all() and n_unique <= 50:
                return ColumnRole.DATE
        except Exception:
            pass

    # ── RULE 7: Numeric metric — the happy path ───────────────────────────
    try:
        numeric = pd.to_numeric(non_null, errors="coerce")
        numeric_ratio = numeric.notna().mean()
        if numeric_ratio > 0.85:
            numeric_clean = numeric.dropna()
            unique_numeric = numeric_clean.nunique()
            all_integers = bool((numeric_clean % 1 == 0).all())

            # Integers with few unique values in a code-like range → CODE
            if all_integers and unique_numeric < 100:
                values = numeric_clean.unique()
                # NAICS/SIC/classification pattern: 2–6 digit integers
                if len(values) > 0 and all(10 <= v <= 999999 for v in values):
                    if any(p in col_lower for p in ["naics", "sic", "code", "class"]):
                        return ColumnRole.CODE

            # Very high cardinality numeric with unique_ratio > 0.9 → likely row ID
            if unique_ratio > 0.9 and n_unique > 100:
                return ColumnRole.IDENTIFIER

            return ColumnRole.METRIC
    except Exception:
        pass

    # ── RULE 8: High-cardinality text → never plot ────────────────────────
    if non_null.dtype == object or str(non_null.dtype) == "string":
        if unique_ratio > 0.5 and n_unique > 50:
            return ColumnRole.HIGH_CARDINALITY_TEXT

    # ── RULE 9: Category by cardinality ───────────────────────────────────
    if n_unique <= 50:
        return ColumnRole.CATEGORY

    return ColumnRole.HIGH_CARDINALITY_TEXT


# ── Axis-usage policy sets ────────────────────────────────────────────────────

# These roles can NEVER be a chart axis under any circumstances
NEVER_USE_AS_AXIS: frozenset[ColumnRole] = frozenset({
    ColumnRole.IDENTIFIER,
    ColumnRole.SEQUENCE,
    ColumnRole.CONSTANT,
    ColumnRole.DERIVED_ID,
})

# These roles can be X axis only (grouping dimension), never Y axis
ONLY_X_AXIS: frozenset[ColumnRole] = frozenset({
    ColumnRole.CATEGORY,
    ColumnRole.BOOLEAN,
    ColumnRole.DATE,
    ColumnRole.CODE,   # CODE only if cardinality is low enough (checked at call site)
})

# Only these roles can be Y axis (quantitative measure)
VALID_Y_AXIS: frozenset[ColumnRole] = frozenset({
    ColumnRole.METRIC,
})

# These roles should never be Y axis but may still appear somewhere on a chart
NEVER_Y_AXIS: frozenset[ColumnRole] = frozenset({
    ColumnRole.IDENTIFIER,
    ColumnRole.SEQUENCE,
    ColumnRole.CONSTANT,
    ColumnRole.DERIVED_ID,
    ColumnRole.HIGH_CARDINALITY_TEXT,
    ColumnRole.CODE,
    ColumnRole.DATE,
    ColumnRole.CATEGORY,
    ColumnRole.BOOLEAN,
})


def get_plottable_columns(df: pd.DataFrame) -> dict:
    """
    Classify every column and return only plottable ones.

    This is the gate that runs before any chart is generated.
    Columns in 'blocked' must never appear on any chart axis.

    Returns:
        {
            "roles":         {col: ColumnRole},
            "blocked":       [{"column": str, "role": str, "reason": str}],
            "date_cols":     [str],
            "category_cols": [str],
            "metric_cols":   [str],
            "code_cols":     [str],
            "plottable_x":   [str],  # safe for X axis
            "plottable_y":   [str],  # safe for Y axis (METRIC only)
        }
    """
    roles: dict[str, ColumnRole] = {}
    blocked: list[dict] = []

    for col in df.columns:
        role = classify_column_role(df[col], col)
        roles[col] = role
        if role in NEVER_USE_AS_AXIS:
            blocked.append({
                "column": col,
                "role": role.value,
                "reason": (
                    f"Column '{col}' classified as {role.value} "
                    f"— excluded from all charts"
                ),
            })

    date_cols = [c for c, r in roles.items() if r == ColumnRole.DATE]
    category_cols = [c for c, r in roles.items() if r == ColumnRole.CATEGORY]
    metric_cols = [c for c, r in roles.items() if r == ColumnRole.METRIC]
    code_cols = [c for c, r in roles.items() if r == ColumnRole.CODE]
    boolean_cols = [c for c, r in roles.items() if r == ColumnRole.BOOLEAN]

    # Low-cardinality CODE columns (≤30 unique values) are safe as X axis
    low_card_code = [c for c in code_cols if df[c].nunique() <= 30]

    plottable_x = list(dict.fromkeys(
        date_cols + category_cols + boolean_cols + low_card_code + metric_cols
    ))
    plottable_y = metric_cols[:]

    return {
        "roles": roles,
        "blocked": blocked,
        "date_cols": date_cols,
        "category_cols": category_cols,
        "metric_cols": metric_cols,
        "code_cols": code_cols,
        "boolean_cols": boolean_cols,
        "plottable_x": plottable_x,
        "plottable_y": plottable_y,
    }
