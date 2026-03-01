"""
DatasetComparison — fuzzy header matching, dataset alignment, delta calculation.
"""

import numpy as np
import pandas as pd
from rapidfuzz import fuzz


class DatasetComparison:
    def __init__(self, df1: pd.DataFrame, df2: pd.DataFrame):
        self.df1 = df1.copy()
        self.df2 = df2.copy()

    def fuzzy_match_headers(self, threshold: int = 75) -> dict:
        """
        Match df1 columns to df2 columns by fuzzy string similarity.

        Returns: {df1_col: {"df2_col": str, "similarity": int}} for matches above threshold.
        """
        mapping = {}
        used_df2 = set()

        for col1 in self.df1.columns:
            best_col = None
            best_score = 0
            for col2 in self.df2.columns:
                if col2 in used_df2:
                    continue
                score = fuzz.ratio(col1.lower(), col2.lower())
                if score > best_score:
                    best_score = score
                    best_col = col2

            if best_score >= threshold and best_col:
                mapping[col1] = {"df2_col": best_col, "similarity": best_score}
                used_df2.add(best_col)

        return mapping

    def align_datasets(self, mapping: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Align df2 column names to match df1 based on the confirmed mapping.
        Returns (aligned_df1, aligned_df2) — only columns present in both.
        """
        # mapping: {df1_col: df2_col}
        rename = {v: k for k, v in mapping.items()}
        df2_renamed = self.df2.rename(columns=rename)

        common_cols = [c for c in mapping.keys() if c in df2_renamed.columns and c in self.df1.columns]
        return self.df1[common_cols].copy(), df2_renamed[common_cols].copy()

    def calculate_deltas(
        self, aligned_df1: pd.DataFrame, aligned_df2: pd.DataFrame
    ) -> list[dict]:
        """
        Calculate per-column percentage change between period 1 and period 2 totals.
        Returns list of {column, period1_value, period2_value, change_pct}.
        """
        results = []
        for col in aligned_df1.columns:
            s1 = pd.to_numeric(aligned_df1[col], errors="coerce").dropna()
            s2 = pd.to_numeric(aligned_df2[col], errors="coerce").dropna()
            if len(s1) == 0 or len(s2) == 0:
                continue
            p1 = float(s1.sum())
            p2 = float(s2.sum())
            if p1 == 0:
                change_pct = None
            else:
                change_pct = round((p2 - p1) / abs(p1) * 100, 2)

            results.append(
                {
                    "column": col,
                    "period1_value": round(p1, 4),
                    "period2_value": round(p2, 4),
                    "change_pct": change_pct,
                }
            )
        return results

    def flag_significant_changes(
        self, deltas: list[dict], threshold: float = 20.0
    ) -> list[dict]:
        """Return only changes above the threshold percentage."""
        return [
            d for d in deltas
            if d["change_pct"] is not None and abs(d["change_pct"]) >= threshold
        ]
