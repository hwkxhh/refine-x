"""
StructRules — Session 2 Implementation
=======================================
Implements STRUCT-01 through STRUCT-06 from the RefineX Formula Rulebook v2.0.

These rules run AFTER GlobalRules (Session 1) and BEFORE HTYPE-specific cleaning.
They detect and fix macro-level structural problems in the dataset — shape, layout,
and format issues that cannot be addressed at the column/cell level.

Execution order inside run_all():
  STRUCT-04 first — header realignment must happen before anything else so
  subsequent rules operate on properly-labelled columns.
  STRUCT-01 → STRUCT-02 → STRUCT-03 → STRUCT-05 → STRUCT-06 thereafter.

Auto-applied  : STRUCT-02 (group-label forward-fill), STRUCT-04 (header fix)
Ask-first     : STRUCT-01, STRUCT-03, STRUCT-05, STRUCT-06

Design rules followed:
  Rule 2 — Every formula is a named method (STRUCT_XX_<name>).
  Rule 4 — Every formula checks its trigger condition before firing.
  Rule 5 — Auto vs Ask distinction enforced per above.
  Rule 6 — Descriptive before prescriptive; never destroy data unilaterally.
"""

from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd

from app.models.cleaning_log import CleaningLog

# ─────────────────────────────────────────────────────────────────────────────
# STRUCT-01  Wide-to-Long detection helpers
# ─────────────────────────────────────────────────────────────────────────────

# All recognised temporal token values (lower-case)
MONTH_TOKENS: frozenset[str] = frozenset({
    "jan", "feb", "mar", "apr", "may", "jun",
    "jul", "aug", "sep", "oct", "nov", "dec",
    "january", "february", "march", "april",
    "june", "july", "august", "september",
    "october", "november", "december",
})
QUARTER_TOKENS: frozenset[str] = frozenset({"q1", "q2", "q3", "q4"})

_YEAR_RE      = re.compile(r"^(19|20)\d{2}$")
_FISCAL_RE    = re.compile(r"^(fy|cy|ay)\d{2,4}$", re.I)
_MONTH_NUM_RE = re.compile(r"^\d{1,2}$")


def _is_temporal_token(token: str) -> bool:
    """Return True if *token* looks like a time-period or ordinal label."""
    t = token.lower()
    if t in MONTH_TOKENS or t in QUARTER_TOKENS:
        return True
    if _YEAR_RE.match(t) or _FISCAL_RE.match(t):
        return True
    # Pure month number 1–12
    if _MONTH_NUM_RE.match(t) and 1 <= int(t) <= 12:
        return True
    return False


def _split_temporal(col_name: str) -> tuple[Optional[str], Optional[str]]:
    """
    Try to split *col_name* into (root, temporal_token).

    Examples:
      'sales_jan'     → ('sales',   'jan')
      'q1_revenue'    → ('revenue', 'q1')
      'revenue_2022'  → ('revenue', '2022')
      '2021_students' → ('students','2021')

    Returns (None, None) if no temporal token is detected.
    """
    parts = col_name.split("_")
    if len(parts) < 2:
        return None, None
    # Last token temporal?
    if _is_temporal_token(parts[-1]):
        return "_".join(parts[:-1]), parts[-1]
    # First token temporal?
    if _is_temporal_token(parts[0]):
        return "_".join(parts[1:]), parts[0]
    return None, None


# ─────────────────────────────────────────────────────────────────────────────
# STRUCT-03  Date granularity classifier
# ─────────────────────────────────────────────────────────────────────────────

_DAILY_RE = re.compile(
    r"^\d{4}[-/]\d{2}[-/]\d{2}$"          # 2024-01-15  /  2024/01/15
    r"|^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$",  # 15/01/2024  /  1-15-24
)
_MONTHLY_RE = re.compile(
    r"^\d{4}[-/]\d{2}$"                    # 2024-01
    r"|^(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+\d{4}$"
    r"|^\d{4}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*$",
    re.I,
)
_QUARTERLY_RE = re.compile(
    r"^[Qq][1-4][-\s]\d{4}$"              # Q1 2024  /  Q1-2024
    r"|^\d{4}[-\s][Qq][1-4]$",            # 2024-Q1  /  2024 Q1
)
_YEARLY_RE = re.compile(
    r"^\d{4}$"                             # 2024
    r"|^[Ff][Yy]\d{2,4}$",               # FY2024  /  FY24
)


def _classify_date_granularity(val: Any) -> str:
    """
    Classify the temporal granularity of *val*.
    Returns: 'daily' | 'monthly' | 'quarterly' | 'yearly' | 'unknown'
    """
    if not isinstance(val, str):
        return "unknown"
    s = val.strip()
    if _DAILY_RE.match(s):
        return "daily"
    if _QUARTERLY_RE.match(s):
        return "quarterly"
    if _MONTHLY_RE.match(s):
        return "monthly"
    if _YEARLY_RE.match(s):
        return "yearly"
    # Last resort: try pandas parsing — if it resolves cleanly, treat as daily
    try:
        pd.to_datetime(s)
        return "daily"
    except Exception:
        pass
    return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# StructRules class
# ─────────────────────────────────────────────────────────────────────────────

class StructRules:
    """
    Applies all 6 STRUCT formula rules to a DataFrame after GlobalRules.

    Usage:
        sr = StructRules(
            job_id=1, df=globally_cleaned_df, db=db_session,
            file_bytes=raw_bytes, file_type='xlsx'   # optional — needed for STRUCT-05
        )
        result = sr.run_all()
        cleaned_df = sr.df
        flags = sr.flags        # ask-first items for the frontend
        report = result         # summary dict
    """

    def __init__(
        self,
        job_id: int,
        df: pd.DataFrame,
        db,
        file_bytes: Optional[bytes] = None,
        file_type: Optional[str] = None,
    ) -> None:
        self.job_id   = job_id
        self.df       = df.copy()
        self.db       = db
        self.file_bytes = file_bytes   # required only for STRUCT-05
        self.file_type  = file_type    # 'xlsx', 'xls', 'csv', 'txt'
        self.flags: list[dict] = []
        self.summary: dict = {
            "struct_rules_applied":       [],
            "wide_to_long_candidates":    [],
            "group_label_cols_filled":    [],
            "mixed_granularity_columns":  [],
            "header_offset_corrected":    None,
            "compatible_sheets":          [],
            "transposed_likely":          False,
        }

    # ─────────────────────────────────────────────────────────────────
    # Internal helpers
    # ─────────────────────────────────────────────────────────────────

    def _log(
        self,
        formula_id: str,
        action: str,
        reason: str,
        column_name: Optional[str] = None,
        row_index: Optional[int] = None,
        original_value: Optional[str] = None,
        new_value: Optional[str] = None,
        was_auto_applied: bool = True,
    ) -> None:
        """Persist a CleaningLog entry with formula traceability."""
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

    def _flag(
        self,
        formula_id: str,
        flag_type: str,
        description: str,
        affected_columns: Optional[list] = None,
        affected_rows: Optional[list] = None,
        suggested_action: Optional[str] = None,
    ) -> None:
        """
        Record a pending-review item (ask-first formula).
        Surfaced to the frontend via CleanedDataset.struct_flags.
        """
        self.flags.append({
            "formula_id":       formula_id,
            "flag_type":        flag_type,
            "description":      description,
            "affected_columns": affected_columns or [],
            "affected_rows":    affected_rows or [],
            "suggested_action": suggested_action,
        })
        self._log(
            formula_id=formula_id,
            action=f"pending_review_{flag_type}",
            reason=description,
            column_name=affected_columns[0] if affected_columns else None,
            was_auto_applied=False,
        )

    # ─────────────────────────────────────────────────────────────────
    # STRUCT-01  Wide-to-Long Format Detection
    # ─────────────────────────────────────────────────────────────────

    def STRUCT_01_wide_to_long_detection(self) -> list[dict]:
        """
        STRUCT-01: Detect when the dataset is stored in wide (pivot) format —
        multiple columns sharing a common root with temporal or categorical
        suffixes, where each column represents one time period / category.

        Examples detected:
          jan_sales, feb_sales, mar_sales
            → root='sales', temporal tokens: jan|feb|mar
          2021_revenue, 2022_revenue, 2023_revenue
            → root='revenue', temporal tokens: 2021|2022|2023
          sales_q1, sales_q2, sales_q3, sales_q4
            → root='sales', temporal tokens: q1|q2|q3|q4

        Trigger: ≥3 columns share the same root with different temporal tokens.
        Ask-first: flags each group; does NOT reshape the data.
        Returns list of candidate group dicts.
        """
        from collections import defaultdict

        root_groups: dict[str, list[dict]] = defaultdict(list)
        for col in self.df.columns:
            root, temporal = _split_temporal(col)
            if root and temporal:
                root_groups[root].append({"column": col, "temporal": temporal})

        candidates = [
            {"root": root, "columns": members}
            for root, members in root_groups.items()
            if len(members) >= 3
        ]

        for group in candidates:
            wide_cols = [m["column"] for m in group["columns"]]
            temporals = [m["temporal"] for m in group["columns"]]
            self._flag(
                formula_id="STRUCT-01",
                flag_type="wide_format_detected",
                description=(
                    f"Detected {len(wide_cols)} columns sharing root "
                    f"'{group['root']}' with temporal suffixes {temporals}. "
                    f"Dataset is in wide (pivot) format. Reshaping to long "
                    f"(one row per period) enables proper time-series analysis."
                ),
                affected_columns=wide_cols,
                suggested_action="reshape_wide_to_long",
            )

        if candidates:
            self.summary["wide_to_long_candidates"] = [
                {
                    "root": c["root"],
                    "columns": [m["column"] for m in c["columns"]],
                    "temporal_tokens": [m["temporal"] for m in c["columns"]],
                }
                for c in candidates
            ]
            self.summary["struct_rules_applied"].append("STRUCT-01")

        self.db.flush()
        return candidates

    # ─────────────────────────────────────────────────────────────────
    # STRUCT-02  Merged Row Forward-Fill (Group Label Columns)
    # ─────────────────────────────────────────────────────────────────

    def STRUCT_02_merged_row_forward_fill(self) -> list[str]:
        """
        STRUCT-02: Detect columns carrying hierarchical group labels where
        an Excel merged-cell export leaves blank cells beneath each label.

        Detection requires ALL THREE criteria:
          1. String-dominant  — ≥80% of non-null values are strings.
          2. Low cardinality  — unique non-null values ≤ max(10, 20% of
                                non-null count). Excludes constant columns.
          3. Block-null pattern — column starts with a non-null value, and
                                  nulls only appear in continuous blocks that
                                  immediately follow a non-null value
                                  (not isolated, not at the top).

        Trigger: All criteria met and at least one null exists.
        Auto-applied: forward-fills the column and logs the change.
        Returns list of column names that were forward-filled.
        """
        filled: list[str] = []

        for col in self.df.columns:
            series = self.df[col]
            non_null = series.dropna()

            if len(non_null) == 0:
                continue
            if series.isnull().sum() == 0:
                continue  # Nothing to fill

            # Criterion 1: String-dominant
            string_count = sum(isinstance(v, str) for v in non_null)
            if string_count / len(non_null) < 0.80:
                continue

            # Criterion 2: Low cardinality, at least 2 unique values
            unique_count = non_null.nunique()
            if unique_count < 2:
                continue  # Constant column — GLOBAL-02 handles this
            cardinality_limit = max(10, len(non_null) * 0.20)
            if unique_count > cardinality_limit:
                continue

            # Criterion 3: Block-null pattern
            # Column must NOT start with null.
            # Every null must be preceded (directly or via a block) by a non-null.
            values = series.tolist()
            if pd.isna(values[0]):
                continue  # Starts with null → not a group-label pattern

            preceding_non_null = False
            valid = True
            for v in values:
                if pd.notna(v):
                    preceding_non_null = True
                else:
                    if not preceding_non_null:
                        valid = False
                        break
            if not valid:
                continue

            # ── Apply forward fill ────────────────────────────────────
            before = series.isnull().sum()
            self.df[col] = series.ffill()
            filled_count = int(before - self.df[col].isnull().sum())

            if filled_count > 0:
                filled.append(col)
                self._log(
                    formula_id="STRUCT-02",
                    action="group_label_forward_filled",
                    reason=(
                        f"Column '{col}' identified as hierarchical group label "
                        f"({unique_count} unique values, block-null pattern). "
                        f"Forward-filled {filled_count} null cells."
                    ),
                    column_name=col,
                    new_value=f"forward_filled_{filled_count}_nulls",
                    was_auto_applied=True,
                )

        if filled:
            self.summary["group_label_cols_filled"] = filled
            self.summary["struct_rules_applied"].append("STRUCT-02")

        self.db.flush()
        return filled

    # ─────────────────────────────────────────────────────────────────
    # STRUCT-03  Mixed Granularity Detection
    # ─────────────────────────────────────────────────────────────────

    def STRUCT_03_mixed_granularity_detection(self) -> list[dict]:
        """
        STRUCT-03: Detect columns where date-like values are stored at mixed
        temporal granularities — e.g., some cells have '2024-01-15' (daily)
        while others contain 'January 2024' (monthly) or '2024' (yearly).

        Trigger: ≥2 distinct granularity classes each covering >10% of values,
                 AND at least 30% of sampled values are recognisable as dates.
        Ask-first: flags the column and reports a full granularity breakdown.
        Returns list of {column, breakdown} dicts.
        """
        mixed: list[dict] = []

        for col in self.df.columns:
            series = self.df[col].dropna()
            if len(series) < 4:
                continue

            # Quick sample check — only process date-ish columns
            sample = series.head(20).astype(str)
            date_like = sum(
                1 for v in sample if _classify_date_granularity(v) != "unknown"
            )
            if date_like / len(sample) < 0.30:
                continue

            # Full-column granularity classification
            counts: dict[str, int] = {
                "daily": 0, "monthly": 0, "quarterly": 0, "yearly": 0, "unknown": 0
            }
            for v in series.astype(str):
                counts[_classify_date_granularity(v)] += 1

            total = len(series)
            significant = {
                g: cnt
                for g, cnt in counts.items()
                if g != "unknown" and cnt / total > 0.10
            }

            if len(significant) >= 2:
                breakdown = {g: round(cnt / total * 100, 1) for g, cnt in significant.items()}
                mixed.append({"column": col, "breakdown": breakdown})
                self._flag(
                    formula_id="STRUCT-03",
                    flag_type="mixed_date_granularity",
                    description=(
                        f"Column '{col}' contains date values at mixed granularities: "
                        f"{breakdown}. "
                        f"Standardise to a single granularity for reliable analysis."
                    ),
                    affected_columns=[col],
                    suggested_action="standardize_date_granularity",
                )

        if mixed:
            self.summary["mixed_granularity_columns"] = mixed
            self.summary["struct_rules_applied"].append("STRUCT-03")

        self.db.flush()
        return mixed

    # ─────────────────────────────────────────────────────────────────
    # STRUCT-04  Header Row Offset Detection
    # ─────────────────────────────────────────────────────────────────

    def STRUCT_04_header_row_offset_detection(self) -> Optional[int]:
        """
        STRUCT-04: Detect when the real column headers are not in row 0.
        Common in Excel files where rows 1–2 carry report titles / generation
        metadata and the true header appears at row 3 or later.

        Two detection signals (either is sufficient to trigger):
          A. >40% of current column names match the 'Unnamed: N' pattern
             (pandas default when no usable header row is detected).
          B. One of the first 10 rows contains values that are better header
             candidates than the current column names:
               • ≥60% cell fill rate
               • ≥75% of values are short, non-numeric strings
               • Current column names are ≥30% Unnamed/numeric.

        Trigger: Either signal fires.
        Auto-applied: promotes detected row to header, drops rows above it.
        Returns 0-based row index of the promoted header, or None if not found.
        """
        if len(self.df) == 0:
            return None

        n_cols = len(self.df.columns)

        # ── Signal A: Unnamed fraction ────────────────────────────────
        unnamed_count = sum(
            1 for c in self.df.columns if str(c).startswith("Unnamed:")
        )
        unnamed_frac = unnamed_count / n_cols if n_cols else 0

        # ── Signal B: scan first 10 rows for a better header ─────────
        header_candidate: Optional[int] = None
        search_limit = min(10, len(self.df))

        for row_idx in range(search_limit):
            row = self.df.iloc[row_idx]
            non_null_vals = [(i, str(v).strip()) for i, v in enumerate(row) if pd.notna(v)]
            fill_rate = len(non_null_vals) / n_cols if n_cols else 0
            if fill_rate < 0.60:
                continue

            # Quality score for a header: short, non-numeric, alphabetic
            good = sum(
                1 for _, v in non_null_vals
                if v
                and not v.replace(" ", "").replace("_", "").replace("-", "").replace(".", "").isnumeric()
                and not v[0].isdigit()
                and len(v) <= 60
            )
            header_quality = good / len(non_null_vals) if non_null_vals else 0

            if header_quality >= 0.75:
                ugly = sum(
                    1 for c in self.df.columns
                    if str(c).startswith("Unnamed:")
                    or str(c).replace(".", "").replace("-", "").isnumeric()
                )
                ugly_frac = ugly / n_cols if n_cols else 0
                if unnamed_frac > 0.40 or ugly_frac > 0.30:
                    header_candidate = row_idx
                    break

        # Fallback: Signal A alone — look for any sufficiently string-filled row
        if header_candidate is None and unnamed_frac > 0.50:
            for row_idx in range(search_limit):
                row = self.df.iloc[row_idx]
                str_vals = [str(v) for v in row if isinstance(v, str) and str(v).strip()]
                if len(str_vals) >= n_cols * 0.60:
                    header_candidate = row_idx
                    break

        if header_candidate is None:
            return None

        # ── Auto-correct: promote detected row to header ──────────────
        new_headers = [
            str(v).strip() if pd.notna(v) else f"col_{i}"
            for i, v in enumerate(self.df.iloc[header_candidate])
        ]
        self.df = self.df.iloc[header_candidate + 1:].copy()
        self.df.columns = pd.Index(new_headers)
        self.df = self.df.reset_index(drop=True)

        self._log(
            formula_id="STRUCT-04",
            action="header_row_offset_corrected",
            reason=(
                f"True header detected at original row index {header_candidate}. "
                f"Rows 0–{header_candidate} were title/metadata and have been removed. "
                f"New columns: {new_headers[:6]}"
                f"{'…' if len(new_headers) > 6 else ''}"
            ),
            new_value=str(new_headers[:6]),
            was_auto_applied=True,
        )
        self.summary["header_offset_corrected"] = header_candidate
        self.summary["struct_rules_applied"].append("STRUCT-04")
        self.db.flush()
        return header_candidate

    # ─────────────────────────────────────────────────────────────────
    # STRUCT-05  Multi-Sheet Aggregation
    # ─────────────────────────────────────────────────────────────────

    def STRUCT_05_multi_sheet_aggregation(self) -> list[str]:
        """
        STRUCT-05: For Excel files, detect multiple sheets that share the
        same (or very similar) column structure and offer to stack them into
        one unified dataset with a 'source_sheet' traceability column.

        Compatibility is measured by Jaccard similarity on normalised column
        name sets (threshold ≥ 0.80).

        Trigger: Excel file (xlsx/xls) with ≥2 sheets having Jaccard ≥ 0.80.
        Ask-first: flags compatible sheet groups; never auto-stacks.
        Returns list of compatible sheet names.
        """
        if not self.file_bytes:
            return []
        if self.file_type not in ("xlsx", "xls"):
            return []

        try:
            xls = pd.ExcelFile(io.BytesIO(self.file_bytes))
        except Exception:
            return []

        sheet_names = xls.sheet_names
        if len(sheet_names) <= 1:
            return []

        # Sample first 3 rows per sheet to get column names
        sheet_schemas: dict[str, set[str]] = {}
        for sheet in sheet_names:
            try:
                df_s = pd.read_excel(
                    io.BytesIO(self.file_bytes),
                    sheet_name=sheet,
                    nrows=3,
                )
                sheet_schemas[sheet] = {
                    str(c).strip().lower() for c in df_s.columns
                }
            except Exception:
                continue

        if len(sheet_schemas) < 2:
            return []

        # Use the first successfully-loaded sheet as the reference
        sheets_list = list(sheet_schemas.keys())
        ref_sheet = sheets_list[0]
        ref_cols = sheet_schemas[ref_sheet]

        compatible: list[str] = [ref_sheet]
        for sheet in sheets_list[1:]:
            other = sheet_schemas[sheet]
            union = ref_cols | other
            if not union:
                continue
            if len(ref_cols & other) / len(union) >= 0.80:
                compatible.append(sheet)

        if len(compatible) >= 2:
            self._flag(
                formula_id="STRUCT-05",
                flag_type="multi_sheet_aggregation",
                description=(
                    f"Excel file has {len(compatible)} sheets with compatible "
                    f"column structure: {compatible}. "
                    f"Stacking them would create one unified dataset "
                    f"(with a 'source_sheet' column for row traceability)."
                ),
                affected_columns=[],
                suggested_action="stack_compatible_sheets",
            )
            self.summary["compatible_sheets"] = compatible
            self.summary["struct_rules_applied"].append("STRUCT-05")

        self.db.flush()
        return compatible

    # ─────────────────────────────────────────────────────────────────
    # STRUCT-06  Transposed Table Detection
    # ─────────────────────────────────────────────────────────────────

    def STRUCT_06_transposed_table_detection(self) -> bool:
        """
        STRUCT-06: Detect when a dataset has been stored in transposed
        orientation — what should be rows appears as columns and vice versa.

        Three independent signals (≥2 must fire):
          1. Extreme shape ratio: ncols > 5 × nrows AND nrows < 20.
          2. First column values look like column names:
             all strings, all unique, all short, ≥50% snake_case / identifier-like.
          3. Column names look like data values:
             >50% are numeric, date-like (YYYY-MM[-DD]), or ordinal (row_N).

        Trigger: ≥2 of the 3 signals fire simultaneously.
        Ask-first: flags for user confirmation; never auto-transposes.
        Returns True if transposition is likely, False otherwise.
        """
        nrows, ncols = self.df.shape
        if nrows == 0 or ncols < 3:
            return False

        signals: list[str] = []

        # ── Signal 1: extreme column/row ratio ───────────────────────
        if ncols > 5 * nrows and nrows < 20:
            signals.append(
                f"Extreme shape {ncols} cols × {nrows} rows "
                f"(ratio {ncols / max(nrows, 1):.1f}×)"
            )

        # ── Signal 2: first column values look like column names ──────
        first_col = self.df.iloc[:, 0].dropna()
        if len(first_col) >= 2:
            str_vals = [v for v in first_col if isinstance(v, str)]
            if len(str_vals) >= len(first_col) * 0.80:
                all_short  = all(len(v) <= 60 for v in str_vals)
                all_unique = len(set(str_vals)) == len(str_vals)
                # identifier-like: snake_case or single-word, no leading digit
                id_like = sum(
                    1 for v in str_vals
                    if re.match(r"^[a-zA-Z][a-zA-Z0-9_]*$", v)
                )
                if all_short and all_unique and id_like >= len(str_vals) * 0.50:
                    signals.append(
                        f"First column '{self.df.columns[0]}' values "
                        f"look like column names (unique, short, identifier-like)"
                    )

        # ── Signal 3: column names look like data values ──────────────
        numeric_names  = sum(
            1 for c in self.df.columns
            if str(c).replace(".", "").replace("-", "").replace(",", "").isnumeric()
        )
        date_names = sum(
            1 for c in self.df.columns
            if re.match(r"^\d{4}[-/]\d{2}([-/]\d{2})?$", str(c))
        )
        ordinal_names = sum(
            1 for c in self.df.columns
            if re.match(r"^(row|item|record|entry)[\s_]?\d+$", str(c), re.I)
        )
        data_name_count = numeric_names + date_names + ordinal_names
        if data_name_count > ncols * 0.50:
            signals.append(
                f"{data_name_count}/{ncols} column names appear to be data values "
                f"({numeric_names} numeric, {date_names} date-like, "
                f"{ordinal_names} ordinal)"
            )

        if len(signals) >= 2:
            self._flag(
                formula_id="STRUCT-06",
                flag_type="transposed_table",
                description=(
                    f"Dataset may be transposed (rows/columns swapped). "
                    f"Current shape: {nrows} rows × {ncols} columns. "
                    f"After transpose: {ncols} rows × {nrows} columns. "
                    f"Signals: {'; '.join(signals)}"
                ),
                suggested_action="transpose_dataset",
            )
            self.summary["transposed_likely"] = True
            self.summary["struct_rules_applied"].append("STRUCT-06")
            self.db.flush()
            return True

        self.db.flush()
        return False

    # ─────────────────────────────────────────────────────────────────
    # run_all  — Orchestrator
    # ─────────────────────────────────────────────────────────────────

    def run_all(self) -> dict:
        """
        Execute all 6 STRUCT rules in the correct sequence:

          STRUCT-04  Header row realignment  (auto — must run first so all
                     subsequent rules see properly-labelled columns)
          STRUCT-01  Wide-to-long detection  (ask-first)
          STRUCT-02  Group-label forward-fill (auto)
          STRUCT-03  Mixed date granularity   (ask-first)
          STRUCT-05  Multi-sheet aggregation  (ask-first; xlsx only)
          STRUCT-06  Transposed table         (ask-first)

        Returns the summary dict.
        Cleaned / realigned DataFrame is in self.df.
        Pending-review flags are in self.flags.
        """
        # Header fix first — everything else depends on correct column labels
        self.STRUCT_04_header_row_offset_detection()

        # Wide/pivot layout detection (flag only — shape change is irreversible)
        self.STRUCT_01_wide_to_long_detection()

        # Group-label forward-fill (safe auto-correction)
        self.STRUCT_02_merged_row_forward_fill()

        # Mixed date granularity (flag only — user chooses target granularity)
        self.STRUCT_03_mixed_granularity_detection()

        # Multi-sheet stacking (flag only — requires user confirmation)
        self.STRUCT_05_multi_sheet_aggregation()

        # Transposed table (flag only — structural inversion is irreversible)
        self.STRUCT_06_transposed_table_detection()

        # Deduplicate rule list
        self.summary["struct_rules_applied"] = sorted(
            set(self.summary["struct_rules_applied"])
        )

        self.db.commit()
        return self.summary
