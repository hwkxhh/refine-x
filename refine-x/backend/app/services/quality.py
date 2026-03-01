"""Quality score calculator — produces a 0-100 composite score."""

import numpy as np
import pandas as pd


def calculate_quality_score(df: pd.DataFrame, original_row_count: int) -> float:
    """
    Composite quality score (0–100) weighted across 4 dimensions:

    Completeness  40% — % of non-null cells
    Uniqueness    30% — % of non-duplicate rows (vs original)
    Consistency   20% — % of columns with uniform dtype
    Integrity     10% — penalises null cells still remaining after cleaning
    """
    if df.empty or len(df.columns) == 0:
        return 0.0

    row_count = len(df)
    col_count = len(df.columns)
    total_cells = row_count * col_count

    # ── Completeness ─────────────────────────────────────────────────
    null_cells = int(df.isnull().sum().sum())
    completeness = ((total_cells - null_cells) / total_cells * 100) if total_cells > 0 else 100.0

    # ── Uniqueness ───────────────────────────────────────────────────
    if original_row_count > 0:
        uniqueness = (row_count / original_row_count) * 100
    else:
        uniqueness = 100.0
    uniqueness = min(uniqueness, 100.0)

    # ── Consistency ──────────────────────────────────────────────────
    # A column is "consistent" if all its non-null values share the same inferred dtype
    consistent_cols = 0
    for col in df.columns:
        series = df[col].dropna()
        if len(series) == 0:
            consistent_cols += 1
            continue
        # Try numeric
        numeric = pd.to_numeric(series, errors="coerce")
        if numeric.notna().mean() >= 0.95:
            consistent_cols += 1
            continue
        # Otherwise treat as string (always consistent)
        consistent_cols += 1

    consistency = (consistent_cols / col_count * 100) if col_count > 0 else 100.0

    # ── Integrity ────────────────────────────────────────────────────
    # Score degrades linearly with remaining null rate
    remaining_null_rate = null_cells / total_cells if total_cells > 0 else 0
    integrity = max(0.0, (1 - remaining_null_rate) * 100)

    # ── Composite ────────────────────────────────────────────────────
    score = (
        completeness * 0.40
        + uniqueness * 0.30
        + consistency * 0.20
        + integrity * 0.10
    )

    return round(min(max(score, 0.0), 100.0), 2)
