"""
GlobalRules — Session 1 Implementation
=======================================
Implements GLOBAL-01 through GLOBAL-16 from the RefineX Formula Rulebook v2.0.

These rules run on the ENTIRE dataset BEFORE any HTYPE-specific column cleaning.

Design rules followed:
  Rule 2 — Every formula implemented as a named function (GLOBAL_XX_name).
  Rule 3 — Cell-level helpers return (cleaned_value, log_entry_dict).
  Rule 4 — Every formula checks its trigger condition before firing.
  Rule 5 — Auto vs Ask distinction enforced; ask-first writes to self.flags.
  Rule 6 — Descriptive before prescriptive; never reject what is parseable.
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Any, Optional

import numpy as np
import pandas as pd
from rapidfuzz import fuzz

from app.models.cleaning_log import CleaningLog

# ─────────────────────────────────────────────────────────────────────────────
# PII Classification Registry  (Appendix F)
# ─────────────────────────────────────────────────────────────────────────────
PII_REGISTRY: dict[str, dict] = {
    # level: high | medium | low | none
    "high": {
        "keywords": [
            "national_id", "passport", "passport_no", "ssn", "pan_number",
            "citizenship_no", "nid", "tax_id", "government_id", "govid",
            "diagnosis", "condition", "icd_code", "illness", "disease",
            "medical", "bank_account", "account_number", "card_number",
            "credit_card", "debit_card",
        ],
        "label": "High — Restricted",
        "governance": "Export restricted. Encryption recommended.",
    },
    "medium": {
        "keywords": [
            "name", "full_name", "first_name", "last_name", "middle_name",
            "fname", "lname", "surname",
            "email", "email_address", "mail",
            "phone", "mobile", "contact", "tel", "cell",
            "address", "full_address", "residential_address",
            "dob", "date_of_birth", "birth_date", "birthdate",
            "gender", "sex",
            "ethnicity", "race", "nationality",
            "marital_status", "civil_status",
            "blood_group", "blood_type",
        ],
        "label": "Medium — Personal",
        "governance": "PII tag applied. Included in privacy report.",
    },
    "low": {
        "keywords": [
            "city", "district", "region", "province", "state",
            "country", "job_title", "designation", "position", "role",
            "department", "dept", "division",
            "education", "qualification", "degree",
        ],
        "label": "Low — Contextual",
        "governance": "Individually non-sensitive; may be sensitive in combination.",
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Common English word corrections for column names (GLOBAL-03)
# Maps misspelled → correct for words typically found in data column headers.
# ─────────────────────────────────────────────────────────────────────────────
COLUMN_WORD_CORRECTIONS: dict[str, str] = {
    # Transport / logistics
    "fule": "fuel", "fuell": "fuel", "feul": "fuel",
    "distace": "distance", "distanse": "distance", "distnce": "distance",
    "paymnt": "payment", "paymet": "payment", "payement": "payment",
    # People
    "naem": "name", "nane": "name",
    "adress": "address", "addres": "address", "adres": "address",
    "emial": "email", "emaail": "email",
    "phoen": "phone", "phohe": "phone",
    "geder": "gender", "gneder": "gender",
    # Time
    "datte": "date", "dat": "date",
    "mounth": "month", "mnth": "month",
    "yeer": "year", "yaer": "year",
    # Quantity / numeric
    "totla": "total", "toal": "total",
    "ammount": "amount", "amont": "amount",
    "quntity": "quantity", "quantty": "quantity", "qunatity": "quantity",
    "prise": "price", "prce": "price",
    # Status
    "staus": "status", "satatus": "status",
    "cateogry": "category", "catgory": "category",
    "descripion": "description", "desciption": "description",
    # Other common
    "employe": "employee", "emploee": "employee",
    "stuednt": "student", "studnet": "student",
    "recrod": "record", "recoed": "record",
    "numbr": "number", "numbeer": "number",
    "regsitration": "registration", "reigstration": "registration",
}

# Keywords that, when found at the start of a cell value in any column, signal
# a trailing-summary row (GLOBAL-07).
SUMMARY_ROW_KEYWORDS: set[str] = {
    "total", "grand total", "subtotal", "sub total", "sum",
    "average", "avg", "mean", "overall", "summary",
    "net total", "gross total", "count total",
}

# Mojibake replacement map for GLOBAL-11 (common Windows-1252 / Latin-1 artifacts)
ENCODING_FIXES: list[tuple[str, str]] = [
    ("\u00e2\u0080\u0099", "\u2019"),   # â€™ → '
    ("\u00e2\u0080\u009c", "\u201c"),   # â€œ → "
    ("\u00e2\u0080\u009d", "\u201d"),   # â€  → "
    ("\u00e2\u0080\u0098", "\u2018"),   # â€˜ → '
    ("\u00e2\u0080\u0093", "\u2013"),   # â€" → –
    ("\u00e2\u0080\u0094", "\u2014"),   # â€" → —
    ("\u00e2\u0080\u00a6", "\u2026"),   # â€¦ → …
    ("\u00c3\u00a9", "\u00e9"),         # Ã© → é
    ("\u00c3\u00a8", "\u00e8"),         # Ã¨ → è
    ("\u00c3\u00aa", "\u00ea"),         # Ãª → ê
    ("\u00c3\u00ab", "\u00eb"),         # Ã« → ë
    ("\u00c3\u00b3", "\u00f3"),         # Ã³ → ó
    ("\u00c3\u00ba", "\u00fa"),         # Ãº → ú
    ("\u00c3\u00bc", "\u00fc"),         # Ã¼ → ü
    ("\u00c3\u00a4", "\u00e4"),         # Ã¤ → ä
    ("\u00c3\u00b6", "\u00f6"),         # Ã¶ → ö
    ("\u00c3\u009f", "\u00df"),         # Ã → ß
]


# ─────────────────────────────────────────────────────────────────────────────
# Cell-level formula functions  (Rule 3: return (cleaned_value, log_entry|None))
# ─────────────────────────────────────────────────────────────────────────────

def GLOBAL_11_fix_encoding(value: Any) -> tuple[Any, Optional[dict]]:
    """
    GLOBAL-11: Encoding Normalization.
    Trigger: String contains recognisable mojibake sequences.
    Converts common Windows-1252 / Latin-1 encoding artifacts to proper UTF-8.
    Auto-applied.
    """
    if not isinstance(value, str):
        return value, None
    original = value
    for bad, good in ENCODING_FIXES:
        value = value.replace(bad, good)
    # Also try re-decoding if still contains non-ASCII artifacts
    if value != original:
        return value, {
            "formula_id": "GLOBAL-11",
            "original_value": original,
            "cleaned_value": value,
            "action_taken": "encoding_artifact_fixed",
            "was_auto_applied": True,
        }
    return value, None


def GLOBAL_12_remove_bom(value: Any) -> tuple[Any, Optional[dict]]:
    """
    GLOBAL-12: BOM Character Removal.
    Trigger: String starts with or contains the UTF-8 BOM \\ufeff.
    Auto-applied.
    """
    if not isinstance(value, str):
        return value, None
    BOM = "\ufeff"
    if BOM in value:
        cleaned = value.replace(BOM, "")
        return cleaned, {
            "formula_id": "GLOBAL-12",
            "original_value": value,
            "cleaned_value": cleaned,
            "action_taken": "bom_character_removed",
            "was_auto_applied": True,
        }
    return value, None


def GLOBAL_14_strip_leading_apostrophe(value: Any) -> tuple[Any, Optional[dict]]:
    """
    GLOBAL-14: Leading Apostrophe Strip.
    Trigger: String value starts with ' (Excel text-force prefix).
    Only strips when the apostrophe is the very first character and the rest
    is a non-empty value — prevents stripping genuine apostrophe-starting text
    like 'twas (archaic English).
    Auto-applied.
    """
    if not isinstance(value, str) or len(value) < 2:
        return value, None
    # Excel artifact: starts with ' and what follows is NOT a word character
    # (i.e. it was used to force-interpret a number/date as text).
    # We strip it if the remainder looks numeric or date-like.
    if value.startswith("'"):
        remainder = value[1:]
        # Only strip if remainder has no leading lowercase letter (avoids real text)
        if remainder and not remainder[0].islower():
            return remainder, {
                "formula_id": "GLOBAL-14",
                "original_value": value,
                "cleaned_value": remainder,
                "action_taken": "leading_apostrophe_stripped",
                "was_auto_applied": True,
            }
    return value, None


def GLOBAL_15_whitespace_to_null(value: Any) -> tuple[Any, Optional[dict]]:
    """
    GLOBAL-15: Whitespace-Only Cell Treatment.
    Trigger: Cell contains only spaces, tabs, or other whitespace characters.
    Replaces with None (treated as null).
    Auto-applied.
    """
    if isinstance(value, str) and len(value) > 0 and value.strip() == "":
        return None, {
            "formula_id": "GLOBAL-15",
            "original_value": repr(value),
            "cleaned_value": None,
            "action_taken": "whitespace_only_treated_as_null",
            "was_auto_applied": True,
        }
    return value, None


# ─────────────────────────────────────────────────────────────────────────────
# GlobalRules class
# ─────────────────────────────────────────────────────────────────────────────

class GlobalRules:
    """
    Applies all 16 GLOBAL formula rules to a DataFrame before HTYPE-specific cleaning.

    Usage:
        gr = GlobalRules(job_id=1, df=raw_df, db=db_session)
        result = gr.run_all()
        cleaned_df = gr.df
        flags = gr.flags          # pending-review items for the frontend
        report = result           # summary of what changed
    """

    def __init__(self, job_id: int, df: pd.DataFrame, db):
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.flags: list[dict] = []   # ask-first items surfaced to user
        self.summary: dict = {
            "global_rules_applied": [],
            "columns_removed": [],
            "constant_columns": [],
            "columns_renamed": {},
            "duplicate_headers": [],
            "all_null_rows_removed": 0,
            "malformed_rows": 0,
            "summary_rows_removed": 0,
            "repeated_header_rows_removed": 0,
            "type_inference": {},
            "pii_tags": {},
            "encoding_fixes": 0,
            "bom_removals": 0,
            "forward_fill_columns": [],
            "apostrophe_strips": 0,
            "whitespace_nulls": 0,
            "mixed_type_columns": [],
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
        """Persist a CleaningLog entry with full formula traceability."""
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
        These are surfaced to the frontend via the global_flags field
        on CleanedDataset and do NOT auto-modify the data.
        """
        self.flags.append({
            "formula_id": formula_id,
            "flag_type": flag_type,
            "description": description,
            "affected_columns": affected_columns or [],
            "affected_rows": affected_rows or [],
            "suggested_action": suggested_action,
        })
        # Also log for audit trail (was_auto_applied=False = pending review)
        self._log(
            formula_id=formula_id,
            action=f"pending_review_{flag_type}",
            reason=description,
            column_name=affected_columns[0] if affected_columns else None,
            was_auto_applied=False,
        )

    # ─────────────────────────────────────────────────────────────────
    # Cell-level pass  (GLOBAL-11, GLOBAL-12, GLOBAL-14, GLOBAL-15)
    # ─────────────────────────────────────────────────────────────────

    def _apply_cell_level_rules(self) -> None:
        """
        Sweep every string cell and apply four cell-level GLOBAL rules:
          GLOBAL-11 encoding fix
          GLOBAL-12 BOM removal
          GLOBAL-14 leading apostrophe strip
          GLOBAL-15 whitespace → null
        Also strips BOM from column names (GLOBAL-12).
        """
        # Fix column names first (BOM in header is common with Excel exports)
        new_cols = {}
        for col in self.df.columns:
            cleaned_col, _ = GLOBAL_12_remove_bom(col)
            if cleaned_col != col:
                new_cols[col] = cleaned_col
                self.summary["bom_removals"] += 1
        if new_cols:
            self.df.rename(columns=new_cols, inplace=True)

        # Walk every cell
        for col in self.df.columns:
            for idx in self.df.index:
                original = self.df.at[idx, col]

                value = original

                # GLOBAL-11
                value, log11 = GLOBAL_11_fix_encoding(value)
                if log11:
                    self._log(
                        formula_id="GLOBAL-11",
                        action="encoding_artifact_fixed",
                        reason=log11["action_taken"],
                        column_name=col,
                        row_index=int(idx),
                        original_value=log11["original_value"],
                        new_value=log11["cleaned_value"],
                    )
                    self.summary["encoding_fixes"] += 1

                # GLOBAL-12
                value, log12 = GLOBAL_12_remove_bom(value)
                if log12:
                    self._log(
                        formula_id="GLOBAL-12",
                        action="bom_character_removed",
                        reason="BOM character (\\ufeff) removed from cell value",
                        column_name=col,
                        row_index=int(idx),
                        original_value=log12["original_value"],
                        new_value=log12["cleaned_value"],
                    )
                    self.summary["bom_removals"] += 1

                # GLOBAL-14
                value, log14 = GLOBAL_14_strip_leading_apostrophe(value)
                if log14:
                    self._log(
                        formula_id="GLOBAL-14",
                        action="leading_apostrophe_stripped",
                        reason="Excel text-force leading apostrophe removed",
                        column_name=col,
                        row_index=int(idx),
                        original_value=log14["original_value"],
                        new_value=log14["cleaned_value"],
                    )
                    self.summary["apostrophe_strips"] += 1

                # GLOBAL-15
                value, log15 = GLOBAL_15_whitespace_to_null(value)
                if log15:
                    self._log(
                        formula_id="GLOBAL-15",
                        action="whitespace_only_treated_as_null",
                        reason="Cell contained only whitespace — treated as null",
                        column_name=col,
                        row_index=int(idx),
                        original_value=log15["original_value"],
                        new_value=None,
                    )
                    self.summary["whitespace_nulls"] += 1

                if value is not original:
                    self.df.at[idx, col] = value

        self.summary["global_rules_applied"].extend(
            ["GLOBAL-11", "GLOBAL-12", "GLOBAL-14", "GLOBAL-15"]
        )
        self.db.flush()

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-01  Empty Column Removal (>95% null)
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_01_empty_column_removal(self) -> list[str]:
        """
        GLOBAL-01: Flag columns where >95% of values are null.
        Trigger: Column null-rate > 0.95.
        Ask-first: flags the column for user review before removal.
        Returns list of flagged column names.
        """
        flagged = []
        for col in self.df.columns:
            null_rate = self.df[col].isnull().mean()
            if null_rate > 0.95:
                flagged.append(col)
                self._flag(
                    formula_id="GLOBAL-01",
                    flag_type="empty_column",
                    description=(
                        f"Column '{col}' is {null_rate*100:.1f}% null "
                        f"(threshold: 95%). Recommended for removal."
                    ),
                    affected_columns=[col],
                    suggested_action="remove_column",
                )
        if flagged:
            self.summary["columns_removed"] = flagged
            self.summary["global_rules_applied"].append("GLOBAL-01")
        self.db.flush()
        return flagged

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-02  Constant Column Detection
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_02_constant_column_detection(self) -> list[str]:
        """
        GLOBAL-02: Detect columns where every non-null value is identical
        (zero variance). Flag as metadata / potential constant.
        Trigger: All non-null values in column are equal.
        Ask-first: flags for user review.
        Returns list of constant column names.
        """
        constant_cols = []
        for col in self.df.columns:
            non_null = self.df[col].dropna()
            if len(non_null) == 0:
                continue
            if non_null.nunique() == 1:
                constant_val = non_null.iloc[0]
                constant_cols.append(col)
                self._flag(
                    formula_id="GLOBAL-02",
                    flag_type="constant_column",
                    description=(
                        f"Column '{col}' has zero variance — "
                        f"all non-null values are '{constant_val}'. "
                        f"This may be a metadata or template column."
                    ),
                    affected_columns=[col],
                    suggested_action="review_constant_column",
                )
        if constant_cols:
            self.summary["constant_columns"] = constant_cols
            self.summary["global_rules_applied"].append("GLOBAL-02")
        self.db.flush()
        return constant_cols

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-03  Column Name Normalization to snake_case
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_03_column_name_normalization(self) -> dict[str, str]:
        """
        GLOBAL-03: Normalize all column names to snake_case.
        Steps:
          1. Strip leading/trailing whitespace.
          2. Remove BOM characters (already done in cell-level pass).
          3. Convert to lowercase.
          4. Replace spaces and hyphens with underscores.
          5. Remove any character that is not alphanumeric or underscore.
          6. Collapse multiple underscores.
          7. Spell-check individual words against COLUMN_WORD_CORRECTIONS.
        Trigger: Column name does not already match snake_case pattern.
        Auto-applied.
        Returns dict of {old_name: new_name} for changed columns.
        """
        rename_map: dict[str, str] = {}

        for col in self.df.columns:
            original = col

            # Step 1: strip whitespace
            cleaned = col.strip()

            # Step 2: lowercase
            cleaned = cleaned.lower()

            # Step 3: replace spaces and hyphens with underscores
            cleaned = re.sub(r"[\s\-]+", "_", cleaned)

            # Step 4: remove non-alphanumeric/underscore chars
            cleaned = re.sub(r"[^a-z0-9_]", "", cleaned)

            # Step 5: collapse multiple underscores
            cleaned = re.sub(r"_+", "_", cleaned).strip("_")

            # Step 6: spell-check individual word tokens
            tokens = cleaned.split("_")
            corrected_tokens = []
            for token in tokens:
                corrected = COLUMN_WORD_CORRECTIONS.get(token, token)
                corrected_tokens.append(corrected)
            cleaned = "_".join(corrected_tokens)

            # Only record a rename if something actually changed
            if cleaned != original and cleaned:
                rename_map[original] = cleaned

        if rename_map:
            self.df.rename(columns=rename_map, inplace=True)
            for old, new in rename_map.items():
                self._log(
                    formula_id="GLOBAL-03",
                    action="column_name_normalized",
                    reason=f"Column name '{old}' normalized to snake_case '{new}'",
                    column_name=new,
                    original_value=old,
                    new_value=new,
                    was_auto_applied=True,
                )
            self.summary["columns_renamed"] = rename_map
            self.summary["global_rules_applied"].append("GLOBAL-03")
        self.db.flush()
        return rename_map

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-04  Header Duplicate Check
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_04_header_duplicate_check(self) -> list[list[str]]:
        """
        GLOBAL-04: After normalization, detect columns with duplicate names.
        Trigger: Two or more columns have the same name post-normalization.
        Ask-first: flags for user to decide: rename or merge.
        Returns list of duplicate column name groups.
        """
        seen: dict[str, list[int]] = {}
        for i, col in enumerate(self.df.columns):
            seen.setdefault(col, []).append(i)

        duplicate_groups = [
            {"name": col, "positions": positions}
            for col, positions in seen.items()
            if len(positions) > 1
        ]

        for group in duplicate_groups:
            col = group["name"]
            positions = group["positions"]
            self._flag(
                formula_id="GLOBAL-04",
                flag_type="duplicate_header",
                description=(
                    f"Column name '{col}' appears {len(positions)} times "
                    f"at positions {positions}. Rename or merge required."
                ),
                affected_columns=[col],
                suggested_action="rename_or_merge_duplicate_column",
            )
            # Auto-deduplicate by appending positional suffix to avoid pandas issues
            new_cols = list(self.df.columns)
            for i, pos in enumerate(positions[1:], start=1):
                new_cols[pos] = f"{col}_{i}"
            self.df.columns = pd.Index(new_cols)

        if duplicate_groups:
            self.summary["duplicate_headers"] = [g["name"] for g in duplicate_groups]
            self.summary["global_rules_applied"].append("GLOBAL-04")
        self.db.flush()
        return duplicate_groups

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-05  All-Null Row Removal
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_05_all_null_row_removal(self) -> int:
        """
        GLOBAL-05: Remove rows where EVERY cell is null/NaN.
        Trigger: Row where all cells are null.
        Auto-applied: removes silently and logs each removed row.
        Returns count of rows removed.
        """
        all_null_mask = self.df.isnull().all(axis=1)
        null_row_indices = self.df.index[all_null_mask].tolist()

        for idx in null_row_indices:
            self._log(
                formula_id="GLOBAL-05",
                action="all_null_row_removed",
                reason="Row where every cell is null — removed from dataset",
                row_index=int(idx),
                was_auto_applied=True,
            )

        self.df = self.df[~all_null_mask].reset_index(drop=True)
        count = len(null_row_indices)
        if count > 0:
            self.summary["all_null_rows_removed"] = count
            self.summary["global_rules_applied"].append("GLOBAL-05")
        self.db.flush()
        return count

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-06  Row Structural Integrity
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_06_row_structural_integrity(self) -> int:
        """
        GLOBAL-06: Detect rows that appear structurally malformed.
        In a pandas-loaded DataFrame all rows have the same column count,
        but we detect rows that are >80% null AND have non-null values
        only in the first 1–2 columns — a common sign of CSV parsing issues
        (e.g., a stray footer line with a single text value).
        Trigger: Row is >80% null AND only 1–2 non-null values present.
        Ask-first: flags for user.
        """
        if len(self.df.columns) < 4:
            return 0  # Not meaningful to check very narrow datasets

        malformed_indices = []
        threshold_null = 0.80

        for idx in self.df.index:
            row = self.df.loc[idx]
            non_null_count = row.notna().sum()
            total_cols = len(self.df.columns)
            null_rate = 1 - (non_null_count / total_cols)

            if null_rate > threshold_null and non_null_count <= 2:
                malformed_indices.append(int(idx))

        if malformed_indices:
            self._flag(
                formula_id="GLOBAL-06",
                flag_type="malformed_rows",
                description=(
                    f"{len(malformed_indices)} row(s) appear structurally malformed "
                    f"(>80% null with ≤2 non-null values). "
                    f"Rows: {malformed_indices[:20]}"
                ),
                affected_rows=malformed_indices,
                suggested_action="review_or_drop_malformed_rows",
            )
            self.summary["malformed_rows"] = len(malformed_indices)
            self.summary["global_rules_applied"].append("GLOBAL-06")
        self.db.flush()
        return len(malformed_indices)

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-07  Trailing Summary Row Detection
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_07_trailing_summary_row_detection(self) -> int:
        """
        GLOBAL-07: Detect and separate rows containing summary-level labels
        such as 'Total', 'Grand Total', 'Subtotal', 'Sum', 'Average'.
        Checks all rows but focuses on rows towards the bottom.
        Trigger: Any cell contains a SUMMARY_ROW_KEYWORDS value.
        Auto-applied: removes summary rows from data body and logs them.
        Returns count of summary rows removed.
        """
        summary_row_indices = []

        for idx in self.df.index:
            row = self.df.loc[idx]
            for val in row:
                if isinstance(val, str):
                    val_lower = val.strip().lower()
                    if val_lower in SUMMARY_ROW_KEYWORDS:
                        summary_row_indices.append(int(idx))
                        break

        for idx in summary_row_indices:
            # Capture first non-null value for log
            row = self.df.loc[idx]
            trigger_val = next(
                (str(v) for v in row if isinstance(v, str) and v.strip().lower() in SUMMARY_ROW_KEYWORDS),
                "unknown",
            )
            self._log(
                formula_id="GLOBAL-07",
                action="summary_row_separated",
                reason=f"Row contains summary-level label '{trigger_val}' — separated from data body",
                row_index=idx,
                original_value=trigger_val,
                was_auto_applied=True,
            )

        if summary_row_indices:
            self.df = self.df.drop(index=summary_row_indices).reset_index(drop=True)
            self.summary["summary_rows_removed"] = len(summary_row_indices)
            self.summary["global_rules_applied"].append("GLOBAL-07")
        self.db.flush()
        return len(summary_row_indices)

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-08  Repeated Header Row Detection
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_08_repeated_header_row_detection(self) -> int:
        """
        GLOBAL-08: Remove rows inside the data body that are exact copies of the
        column header row (a common artifact when stacking sheets or copy-pasting).
        Trigger: A data row matches the column names of the DataFrame.
        Auto-applied.
        Returns count of repeated header rows removed.
        """
        header_set = set(str(c).strip().lower() for c in self.df.columns)
        repeated_indices = []

        for idx in self.df.index:
            row_values = set(
                str(v).strip().lower() for v in self.df.loc[idx] if pd.notna(v)
            )
            # If ≥80% of the row's non-null values match column headers exactly
            if len(row_values) > 0 and len(row_values & header_set) / len(header_set) >= 0.8:
                repeated_indices.append(int(idx))

        for idx in repeated_indices:
            self._log(
                formula_id="GLOBAL-08",
                action="repeated_header_row_removed",
                reason="Row inside data body matches column header names — removed",
                row_index=idx,
                was_auto_applied=True,
            )

        if repeated_indices:
            self.df = self.df.drop(index=repeated_indices).reset_index(drop=True)
            self.summary["repeated_header_rows_removed"] = len(repeated_indices)
            self.summary["global_rules_applied"].append("GLOBAL-08")
        self.db.flush()
        return len(repeated_indices)

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-09  Data Type Inference Per Column
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_09_data_type_inference(self) -> dict[str, dict]:
        """
        GLOBAL-09: Infer the dominant data type for each column.
        Reports if >10% of values don't match the dominant type.
        Trigger: Always runs.
        Returns dict of {column: {dominant_type, mismatch_pct, sample_mismatches}}.
        """
        type_report: dict[str, dict] = {}

        for col in self.df.columns:
            series = self.df[col].dropna()
            if len(series) == 0:
                type_report[col] = {"dominant_type": "empty", "mismatch_pct": 0.0}
                continue

            # Try to infer types per value
            type_counts: dict[str, int] = {
                "integer": 0, "float": 0, "date": 0, "boolean": 0, "string": 0
            }
            mismatches: list[str] = []

            for val in series:
                val_str = str(val)
                if isinstance(val, bool):
                    type_counts["boolean"] += 1
                elif isinstance(val, int):
                    type_counts["integer"] += 1
                elif isinstance(val, float):
                    type_counts["float"] += 1
                else:
                    # Try numeric
                    try:
                        int(val_str.replace(",", ""))
                        type_counts["integer"] += 1
                        continue
                    except ValueError:
                        pass
                    try:
                        float(val_str.replace(",", ""))
                        type_counts["float"] += 1
                        continue
                    except ValueError:
                        pass
                    # Try boolean string
                    if val_str.lower() in {"true", "false", "yes", "no", "1", "0"}:
                        type_counts["boolean"] += 1
                        continue
                    # Try date
                    try:
                        pd.to_datetime(val_str)
                        type_counts["date"] += 1
                        continue
                    except Exception:
                        pass
                    type_counts["string"] += 1

            total = len(series)
            dominant_type = max(type_counts, key=type_counts.get)
            dominant_count = type_counts[dominant_type]
            mismatch_count = total - dominant_count
            mismatch_pct = round(mismatch_count / total * 100, 2)

            type_report[col] = {
                "dominant_type": dominant_type,
                "mismatch_pct": mismatch_pct,
                "type_counts": type_counts,
            }

            if mismatch_pct > 10:
                self._log(
                    formula_id="GLOBAL-09",
                    action="data_type_mismatch_flagged",
                    reason=(
                        f"Column '{col}': dominant type is '{dominant_type}' but "
                        f"{mismatch_pct:.1f}% of values differ (threshold 10%)"
                    ),
                    column_name=col,
                    was_auto_applied=True,
                )

        self.summary["type_inference"] = type_report
        if type_report:
            self.summary["global_rules_applied"].append("GLOBAL-09")
        self.db.flush()
        return type_report

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-10  PII Column Tagging
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_10_pii_column_tagging(self) -> dict[str, dict]:
        """
        GLOBAL-10: Tag columns containing personal data for data governance.
        Uses keyword matching against the PII Registry (Appendix F).
        Trigger: Always runs.
        Auto-applied: attaches tags, does not modify data.
        Returns dict of {column: {level, label, governance}}.
        """
        pii_tags: dict[str, dict] = {}

        for col in self.df.columns:
            col_lower = col.lower()
            matched_level = None

            # Token-aware matching: split on '_' to avoid substring false-positives
            # (e.g. 'city' must NOT match 'ethnicity' via substring).
            col_tokens = col_lower.split("_")
            for level, info in PII_REGISTRY.items():
                for keyword in info["keywords"]:
                    kw_tokens = keyword.split("_")
                    # Match if: exact equality | keyword is a whole token in col | col is a whole token in keyword
                    if keyword == col_lower or keyword in col_tokens or col_lower in kw_tokens:
                        matched_level = level
                        break
                if matched_level:
                    break

            if matched_level:
                pii_tags[col] = {
                    "level": matched_level,
                    "label": PII_REGISTRY[matched_level]["label"],
                    "governance": PII_REGISTRY[matched_level]["governance"],
                }
                self._log(
                    formula_id="GLOBAL-10",
                    action="pii_column_tagged",
                    reason=(
                        f"Column '{col}' tagged as "
                        f"PII level '{matched_level}' — "
                        f"{PII_REGISTRY[matched_level]['label']}"
                    ),
                    column_name=col,
                    new_value=matched_level,
                    was_auto_applied=True,
                )

        self.summary["pii_tags"] = pii_tags
        if pii_tags:
            self.summary["global_rules_applied"].append("GLOBAL-10")
        self.db.flush()
        return pii_tags

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-13  Merged Cell Forward-Fill
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_13_merged_cell_forward_fill(self) -> list[str]:
        """
        GLOBAL-13: Detect columns where values look like they originated from
        merged Excel cells (a non-null value followed by multiple nulls that then
        repeat the pattern). Fills nulls forward from the last non-null value.
        Trigger: Column has a pattern of single values followed by blocks of nulls
                 that accounts for >30% of rows.
        Auto-applied.
        Returns list of columns where forward-fill was applied.
        """
        filled_columns: list[str] = []

        for col in self.df.columns:
            series = self.df[col]
            total = len(series)
            if total < 4:
                continue

            null_count = series.isnull().sum()
            null_rate = null_count / total

            # Only candidate columns: between 20% and 90% null
            if null_rate < 0.20 or null_rate > 0.90:
                continue

            # Check for merge pattern: non-null, then 1+ nulls, repeating
            # We detect this by checking if runs of nulls always follow non-null values
            non_null_positions = series.dropna().index.tolist()
            if len(non_null_positions) < 2:
                continue

            # Heuristic: if average gap between non-null values > 1, it looks merged
            gaps = [
                non_null_positions[i + 1] - non_null_positions[i]
                for i in range(len(non_null_positions) - 1)
            ]
            if not gaps:
                continue
            avg_gap = sum(gaps) / len(gaps)

            if avg_gap >= 2.0:  # Average ≥2 rows between non-null values
                before = series.isnull().sum()
                self.df[col] = series.ffill()
                after = self.df[col].isnull().sum()
                filled = int(before - after)
                if filled > 0:
                    filled_columns.append(col)
                    self._log(
                        formula_id="GLOBAL-13",
                        action="merged_cell_forward_fill",
                        reason=(
                            f"Column '{col}' pattern suggests merged Excel cells "
                            f"(avg gap {avg_gap:.1f} rows). Forward-filled {filled} nulls."
                        ),
                        column_name=col,
                        new_value=f"forward_filled_{filled}_nulls",
                        was_auto_applied=True,
                    )

        if filled_columns:
            self.summary["forward_fill_columns"] = filled_columns
            self.summary["global_rules_applied"].append("GLOBAL-13")
        self.db.flush()
        return filled_columns

    # ─────────────────────────────────────────────────────────────────
    # GLOBAL-16  Mixed Data Type Column Alert
    # ─────────────────────────────────────────────────────────────────

    def GLOBAL_16_mixed_data_type_column_alert(self) -> list[str]:
        """
        GLOBAL-16: Flag columns where >20% of values have a different type
        from the dominant type in that column.
        Trigger: >20% type mismatch in a column.
        Ask-first: records flag for user review; does not modify data.
        Returns list of mixed-type column names.
        """
        mixed_columns: list[str] = []
        type_report = self.summary.get("type_inference", {})

        for col, info in type_report.items():
            mismatch_pct = info.get("mismatch_pct", 0)
            if mismatch_pct > 20:
                mixed_columns.append(col)
                self._flag(
                    formula_id="GLOBAL-16",
                    flag_type="mixed_data_type",
                    description=(
                        f"Column '{col}' has {mismatch_pct:.1f}% type mismatch. "
                        f"Dominant type: '{info.get('dominant_type', 'unknown')}'. "
                        f"Type breakdown: {info.get('type_counts', {})}"
                    ),
                    affected_columns=[col],
                    suggested_action="review_mixed_type_column",
                )

        if mixed_columns:
            self.summary["mixed_type_columns"] = mixed_columns
            self.summary["global_rules_applied"].append("GLOBAL-16")
        self.db.flush()
        return mixed_columns

    # ─────────────────────────────────────────────────────────────────
    # run_all  — Orchestrator
    # ─────────────────────────────────────────────────────────────────

    def run_all(self) -> dict:
        """
        Execute all 16 GLOBAL rules in the correct sequence:

          Cell-level first (GLOBAL-11, GLOBAL-12, GLOBAL-14, GLOBAL-15)
          Then dataset-level rules in order.

        Returns the summary dict. The cleaned DataFrame is in self.df.
        Pending-review flags are in self.flags.
        """
        # ── Pass 1: Cell-level rules ──────────────────────────────────
        # GLOBAL-11 (encoding), GLOBAL-12 (BOM), GLOBAL-14 (apostrophe),
        # GLOBAL-15 (whitespace→null) applied to every cell
        self._apply_cell_level_rules()

        # ── Pass 2: Dataset-level rules ───────────────────────────────

        # GLOBAL-05 must run early so null rows don't skew stats below
        self.GLOBAL_05_all_null_row_removal()

        # GLOBAL-07 and GLOBAL-08 remove structural noise rows
        self.GLOBAL_07_trailing_summary_row_detection()
        self.GLOBAL_08_repeated_header_row_detection()

        # GLOBAL-03 normalises column names (must run before GLOBAL-04)
        self.GLOBAL_03_column_name_normalization()

        # GLOBAL-04 checks for duplicate headers post-normalization
        self.GLOBAL_04_header_duplicate_check()

        # GLOBAL-13 forward-fill merged cells (before type inference)
        self.GLOBAL_13_merged_cell_forward_fill()

        # GLOBAL-01 and GLOBAL-02 flag problem columns
        self.GLOBAL_01_empty_column_removal()
        self.GLOBAL_02_constant_column_detection()

        # GLOBAL-06 structural row integrity check
        self.GLOBAL_06_row_structural_integrity()

        # GLOBAL-09 must run before GLOBAL-16 (provides type_inference data)
        self.GLOBAL_09_data_type_inference()

        # GLOBAL-10 PII tagging
        self.GLOBAL_10_pii_column_tagging()

        # GLOBAL-16 uses type_inference output from GLOBAL-09
        self.GLOBAL_16_mixed_data_type_column_alert()

        # Deduplicate applied rule list
        self.summary["global_rules_applied"] = sorted(
            set(self.summary["global_rules_applied"])
        )

        self.db.commit()
        return self.summary
