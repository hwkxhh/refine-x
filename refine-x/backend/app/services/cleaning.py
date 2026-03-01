"""
DataCleaningPipeline — 4-phase data cleaning service.

IMPORTANT: GlobalRules (GLOBAL-01 to GLOBAL-16) runs BEFORE this pipeline
via the process_csv Celery task.  The pipeline below handles HTYPE-specific
column-level cleaning after the global pass is complete.

Phase 1: Structural cleanup  (remove_duplicates, normalize_column_names, remove_empty_columns)
Phase 2: Value standardisation  (detect_and_convert_dates, detect_and_bucket_ages)
Phase 3: Missing-data handling  (identify_missing_values, auto_fill_numeric, auto_fill_categorical)
Phase 4: Outlier detection  (detect_outliers_iqr)
"""

import re
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from app.models.cleaning_log import CleaningLog


class DataCleaningPipeline:
    def __init__(self, job_id: int, df: pd.DataFrame, db):
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.summary = {
            "duplicates_removed": 0,
            "columns_renamed": 0,
            "columns_dropped": 0,
            "dates_converted": 0,
            "ages_bucketed": 0,
            "missing_filled": 0,
            "outliers_flagged": 0,
        }

    # ─────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────

    def _log(
        self,
        action: str,
        reason: str,
        column_name: Optional[str] = None,
        row_index: Optional[int] = None,
        original_value: Optional[str] = None,
        new_value: Optional[str] = None,
        formula_id: Optional[str] = None,
        was_auto_applied: bool = True,
    ):
        entry = CleaningLog(
            job_id=self.job_id,
            action=action,
            reason=reason,
            column_name=column_name,
            row_index=row_index,
            original_value=str(original_value) if original_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            formula_id=formula_id,
            was_auto_applied=was_auto_applied,
            timestamp=datetime.utcnow(),
        )
        self.db.add(entry)

    # ─────────────────────────────────────────────────────────────────
    # PHASE 1: Structural cleanup
    # ─────────────────────────────────────────────────────────────────

    def remove_duplicates(self) -> int:
        """Remove fully duplicate rows and log each one."""
        dupe_mask = self.df.duplicated(keep="first")
        dupe_indices = self.df.index[dupe_mask].tolist()

        for idx in dupe_indices:
            self._log(
                action="remove_duplicate",
                reason="Row is an exact duplicate of a previous row",
                row_index=int(idx),
            )

        self.df = self.df[~dupe_mask].reset_index(drop=True)
        count = len(dupe_indices)
        self.summary["duplicates_removed"] = count
        self.db.flush()
        return count

    def normalize_column_names(self) -> int:
        """Strip, lowercase and underscore-ify column names."""
        renamed = 0
        new_columns = {}
        for col in self.df.columns:
            clean = re.sub(r"\s+", "_", col.strip().lower())
            clean = re.sub(r"[^a-z0-9_]", "", clean)
            if clean != col:
                new_columns[col] = clean
                self._log(
                    action="normalize_column_name",
                    reason="Column name normalised to lowercase with underscores",
                    column_name=col,
                    original_value=col,
                    new_value=clean,
                )
                renamed += 1

        self.df.rename(columns=new_columns, inplace=True)
        self.summary["columns_renamed"] = renamed
        self.db.flush()
        return renamed

    def remove_empty_columns(self, threshold: float = 0.8) -> int:
        """Drop columns that are more than `threshold` null."""
        dropped = 0
        cols_to_drop = []
        for col in self.df.columns:
            null_pct = self.df[col].isnull().mean()
            if null_pct > threshold:
                cols_to_drop.append(col)
                self._log(
                    action="remove_empty_column",
                    reason=f"Column is {null_pct*100:.1f}% null (threshold {threshold*100:.0f}%)",
                    column_name=col,
                )
                dropped += 1

        self.df.drop(columns=cols_to_drop, inplace=True)
        self.summary["columns_dropped"] = dropped
        self.db.flush()
        return dropped

    # ─────────────────────────────────────────────────────────────────
    # PHASE 2: Value standardisation
    # ─────────────────────────────────────────────────────────────────

    def detect_and_convert_dates(self) -> int:
        """Convert columns that look like dates to YYYY-MM format."""
        converted = 0
        for col in self.df.columns:
            if self.df[col].dtype == object:
                sample = self.df[col].dropna().head(20)
                if len(sample) == 0:
                    continue
                try:
                    parsed = pd.to_datetime(sample, infer_datetime_format=True, errors="coerce")
                    hit_rate = parsed.notna().mean()
                    if hit_rate >= 0.8:
                        full_parsed = pd.to_datetime(
                            self.df[col], infer_datetime_format=True, errors="coerce"
                        )
                        formatted = full_parsed.dt.strftime("%Y-%m")
                        self._log(
                            action="convert_date",
                            reason=f"Column detected as date ({hit_rate*100:.0f}% match), converted to YYYY-MM",
                            column_name=col,
                        )
                        self.df[col] = formatted
                        converted += 1
                except Exception:
                    continue

        self.summary["dates_converted"] = converted
        self.db.flush()
        return converted

    def detect_and_bucket_ages(self) -> int:
        """Replace numeric age-like columns (0-120) with age buckets."""
        bucketed = 0

        def _bucket(val):
            try:
                v = float(val)
            except (TypeError, ValueError):
                return val
            if v < 0 or v > 120:
                return val
            if v <= 18:
                return "0-18"
            if v <= 35:
                return "19-35"
            if v <= 60:
                return "36-60"
            return "60+"

        for col in self.df.select_dtypes(include=[np.number]).columns:
            series = self.df[col].dropna()
            if len(series) == 0:
                continue
            if series.between(0, 120).mean() >= 0.9 and series.max() <= 120:
                self._log(
                    action="bucket_age",
                    reason="Numeric column detected as age (values 0-120), converted to age buckets",
                    column_name=col,
                )
                self.df[col] = self.df[col].apply(_bucket)
                bucketed += 1

        self.summary["ages_bucketed"] = bucketed
        self.db.flush()
        return bucketed

    # ─────────────────────────────────────────────────────────────────
    # PHASE 3: Missing-data handling
    # ─────────────────────────────────────────────────────────────────

    def identify_missing_values(self) -> dict:
        """Return per-column null stats."""
        result = {}
        for col in self.df.columns:
            count = int(self.df[col].isnull().sum())
            if count > 0:
                pct = round(count / len(self.df) * 100, 2)
                result[col] = {"count": count, "percentage": pct}
        return result

    def auto_fill_numeric(self, column: str, method: str = "mean") -> int:
        """Fill nulls in a numeric column with mean or median."""
        if column not in self.df.columns:
            return 0
        null_mask = self.df[column].isnull()
        count = int(null_mask.sum())
        if count == 0:
            return 0

        if method == "median":
            fill_value = self.df[column].median()
        else:
            fill_value = self.df[column].mean()

        for idx in self.df.index[null_mask]:
            self._log(
                action="fill_missing",
                reason=f"Null filled with {method} ({fill_value:.4g})",
                column_name=column,
                row_index=int(idx),
                new_value=str(round(fill_value, 4)),
            )

        self.df[column].fillna(fill_value, inplace=True)
        self.summary["missing_filled"] += count
        self.db.flush()
        return count

    def auto_fill_categorical(self, column: str, method: str = "mode") -> int:
        """Fill nulls in a categorical column with mode."""
        if column not in self.df.columns:
            return 0
        null_mask = self.df[column].isnull()
        count = int(null_mask.sum())
        if count == 0:
            return 0

        mode_vals = self.df[column].mode()
        if len(mode_vals) == 0:
            return 0
        fill_value = mode_vals[0]

        for idx in self.df.index[null_mask]:
            self._log(
                action="fill_missing",
                reason=f"Null filled with mode value '{fill_value}'",
                column_name=column,
                row_index=int(idx),
                new_value=str(fill_value),
            )

        self.df[column].fillna(fill_value, inplace=True)
        self.summary["missing_filled"] += count
        self.db.flush()
        return count

    # ─────────────────────────────────────────────────────────────────
    # PHASE 4: Outlier detection (IQR method — flag only, don't remove)
    # ─────────────────────────────────────────────────────────────────

    def detect_outliers_iqr(self, column: str) -> list:
        """Flag outliers in a numeric column using IQR; returns list of outlier records."""
        if column not in self.df.columns:
            return []

        series = pd.to_numeric(self.df[column], errors="coerce").dropna()
        if len(series) < 4:
            return []

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr

        outliers = []
        numeric_col = pd.to_numeric(self.df[column], errors="coerce")
        mask = (numeric_col < lower) | (numeric_col > upper)

        for idx in self.df.index[mask]:
            val = self.df.at[idx, column]
            self._log(
                action="flag_outlier",
                reason=f"Value {val} is outside IQR range [{lower:.4g}, {upper:.4g}]",
                column_name=column,
                row_index=int(idx),
                original_value=str(val),
            )
            outliers.append(
                {
                    "row_index": int(idx),
                    "column": column,
                    "value": val,
                    "expected_range": f"{lower:.4g} – {upper:.4g}",
                }
            )

        self.summary["outliers_flagged"] += len(outliers)
        self.db.flush()
        return outliers

    # ─────────────────────────────────────────────────────────────────
    # Run full pipeline
    # ─────────────────────────────────────────────────────────────────

    def run_all(self) -> dict:
        """Execute all 4 phases in sequence. Returns summary dict."""
        original_rows = len(self.df)

        # Phase 1
        self.remove_duplicates()
        self.normalize_column_names()
        self.remove_empty_columns()

        # Phase 2
        self.detect_and_convert_dates()
        self.detect_and_bucket_ages()

        # Phase 3 — fill numeric nulls, then categorical nulls
        missing = self.identify_missing_values()
        for col in list(missing.keys()):
            if col not in self.df.columns:
                continue
            if pd.api.types.is_numeric_dtype(self.df[col]):
                self.auto_fill_numeric(col)
            else:
                self.auto_fill_categorical(col)

        # Phase 4 — flag outliers in all remaining numeric columns
        for col in self.df.select_dtypes(include=[np.number]).columns:
            self.detect_outliers_iqr(col)

        self.summary["row_count_original"] = original_rows
        self.summary["row_count_cleaned"] = len(self.df)

        self.db.commit()
        return self.summary
