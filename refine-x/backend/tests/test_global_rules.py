"""
Tests for GlobalRules — Session 1  (GLOBAL-01 through GLOBAL-16)
==================================================================
Each test uses a synthetic "maximally messy" DataFrame that deliberately
triggers exactly the rule under test.  A lightweight mock database session
replaces the real SQLAlchemy session so no DB connection is required.

Run with:
    pytest backend/tests/test_global_rules.py -v
"""

from __future__ import annotations

import sys
import os

# ── Make the backend package importable without installing it ──────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import pytest

from app.services.global_rules import (
    GlobalRules,
    GLOBAL_11_fix_encoding,
    GLOBAL_12_remove_bom,
    GLOBAL_14_strip_leading_apostrophe,
    GLOBAL_15_whitespace_to_null,
    PII_REGISTRY,
    COLUMN_WORD_CORRECTIONS,
    SUMMARY_ROW_KEYWORDS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Mock DB session
# ─────────────────────────────────────────────────────────────────────────────

class MockDB:
    """Minimal mock that absorbs add / flush / commit calls."""
    def __init__(self):
        self.added: list = []

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        pass

    def commit(self):
        pass


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def make_db() -> MockDB:
    return MockDB()


def make_gr(df: pd.DataFrame, db: MockDB | None = None) -> GlobalRules:
    return GlobalRules(job_id=999, df=df, db=db or make_db())


# ═════════════════════════════════════════════════════════════════════════════
# Cell-level formula function unit tests  (Rule 3)
# ═════════════════════════════════════════════════════════════════════════════

class TestCellLevelFunctions:
    """
    GLOBAL-11, GLOBAL-12, GLOBAL-14, GLOBAL-15 are implemented as module-level
    functions returning (cleaned_value, log_entry | None).
    """

    # ── GLOBAL-11 ─────────────────────────────────────────────────────
    def test_GLOBAL_11_fixes_mojibake(self):
        bad = "caf\u00e3\u00a9"   # "café" corrupted as mojibake
        # Use a known artifact from ENCODING_FIXES
        bad2 = "\u00e2\u0080\u0099s"  # â€™s → 's
        val, log = GLOBAL_11_fix_encoding(bad2)
        assert val == "\u2019s"
        assert log is not None
        assert log["formula_id"] == "GLOBAL-11"
        assert log["was_auto_applied"] is True

    def test_GLOBAL_11_no_change_clean_string(self):
        val, log = GLOBAL_11_fix_encoding("hello world")
        assert val == "hello world"
        assert log is None

    def test_GLOBAL_11_non_string_passthrough(self):
        val, log = GLOBAL_11_fix_encoding(42)
        assert val == 42
        assert log is None

    # ── GLOBAL-12 ─────────────────────────────────────────────────────
    def test_GLOBAL_12_strips_bom_at_start(self):
        val, log = GLOBAL_12_remove_bom("\ufeffSome text")
        assert val == "Some text"
        assert log is not None
        assert log["formula_id"] == "GLOBAL-12"

    def test_GLOBAL_12_strips_bom_embedded(self):
        val, log = GLOBAL_12_remove_bom("col\ufeffname")
        assert "\ufeff" not in val
        assert log is not None

    def test_GLOBAL_12_no_bom_no_change(self):
        val, log = GLOBAL_12_remove_bom("normal string")
        assert val == "normal string"
        assert log is None

    def test_GLOBAL_12_non_string_passthrough(self):
        val, log = GLOBAL_12_remove_bom(3.14)
        assert val == 3.14
        assert log is None

    # ── GLOBAL-14 ─────────────────────────────────────────────────────
    def test_GLOBAL_14_strips_excel_apostrophe(self):
        val, log = GLOBAL_14_strip_leading_apostrophe("'12345")
        assert val == "12345"
        assert log is not None
        assert log["formula_id"] == "GLOBAL-14"

    def test_GLOBAL_14_strips_date_apostrophe(self):
        val, log = GLOBAL_14_strip_leading_apostrophe("'2024-01-15")
        assert val == "2024-01-15"
        assert log is not None

    def test_GLOBAL_14_does_not_strip_lowercase_start(self):
        # "'twas the night" — real English, should NOT strip
        val, log = GLOBAL_14_strip_leading_apostrophe("'twas the night")
        assert val == "'twas the night"
        assert log is None

    def test_GLOBAL_14_single_char_apostrophe_ignored(self):
        val, log = GLOBAL_14_strip_leading_apostrophe("'")
        assert val == "'"
        assert log is None

    # ── GLOBAL-15 ─────────────────────────────────────────────────────
    def test_GLOBAL_15_spaces_only_becomes_null(self):
        val, log = GLOBAL_15_whitespace_to_null("   ")
        assert val is None
        assert log is not None
        assert log["formula_id"] == "GLOBAL-15"

    def test_GLOBAL_15_tabs_only_becomes_null(self):
        val, log = GLOBAL_15_whitespace_to_null("\t\t")
        assert val is None
        assert log is not None

    def test_GLOBAL_15_empty_string_unchanged(self):
        # Empty string "" is already null-like; only whitespace triggers this rule
        val, log = GLOBAL_15_whitespace_to_null("")
        assert val == ""
        assert log is None

    def test_GLOBAL_15_real_value_unchanged(self):
        val, log = GLOBAL_15_whitespace_to_null("hello")
        assert val == "hello"
        assert log is None

    def test_GLOBAL_15_non_string_passthrough(self):
        val, log = GLOBAL_15_whitespace_to_null(None)
        assert val is None
        assert log is None


# ═════════════════════════════════════════════════════════════════════════════
# GlobalRules class tests
# ═════════════════════════════════════════════════════════════════════════════

class TestGLOBAL_01_EmptyColumnRemoval:
    """GLOBAL-01: >95% null columns are flagged (ask-first)."""

    def test_flags_column_above_threshold(self):
        # 10 rows; only 1 non-null value → 90% null → above 95%? No, 90 < 95. Use 1/20.
        data = {"id": range(20), "ghost": [None] * 19 + ["x"]}  # 95% null exactly; >95 needs strictly >
        # Use 19/20 = 95% exactly — trigger requires >95, so let's use 19/20 null = 95% → not triggered
        # Use all nulls in a 20-row column except 0 values:
        data2 = {"id": range(20), "ghost": [None] * 20}   # 100% null → GLOBAL-01 triggers
        df = pd.DataFrame(data2)
        gr = make_gr(df)
        flagged = gr.GLOBAL_01_empty_column_removal()
        assert "ghost" in flagged
        assert any(f["formula_id"] == "GLOBAL-01" for f in gr.flags)

    def test_column_with_nulls_below_threshold_not_flagged(self):
        data = {"id": range(10), "sparse": [None, None, None, 1, 2, 3, 4, 5, 6, 7]}  # 30% null
        df = pd.DataFrame(data)
        gr = make_gr(df)
        flagged = gr.GLOBAL_01_empty_column_removal()
        assert "sparse" not in flagged

    def test_flag_includes_suggested_action(self):
        data = {"id": range(5), "empty_col": [None] * 5}
        df = pd.DataFrame(data)
        gr = make_gr(df)
        gr.GLOBAL_01_empty_column_removal()
        flag = next(f for f in gr.flags if f["formula_id"] == "GLOBAL-01")
        assert flag["suggested_action"] == "remove_column"


class TestGLOBAL_02_ConstantColumnDetection:
    """GLOBAL-02: zero-variance columns flagged (ask-first)."""

    def test_flags_all_same_value_column(self):
        data = {"id": range(5), "status": ["active"] * 5}
        df = pd.DataFrame(data)
        gr = make_gr(df)
        constant = gr.GLOBAL_02_constant_column_detection()
        assert "status" in constant
        assert any(f["formula_id"] == "GLOBAL-02" for f in gr.flags)

    def test_column_with_variation_not_flagged(self):
        data = {"id": range(5), "score": [1, 2, 3, 4, 5]}
        df = pd.DataFrame(data)
        gr = make_gr(df)
        constant = gr.GLOBAL_02_constant_column_detection()
        assert "score" not in constant

    def test_constant_column_with_some_nulls_still_flagged(self):
        data = {"id": range(6), "src": ["web", "web", None, "web", None, "web"]}
        df = pd.DataFrame(data)
        gr = make_gr(df)
        constant = gr.GLOBAL_02_constant_column_detection()
        assert "src" in constant


class TestGLOBAL_03_ColumnNameNormalization:
    """GLOBAL-03: column names → snake_case with typo correction."""

    def test_spaces_converted_to_underscores(self):
        df = pd.DataFrame({"First Name": ["Alice"], "Last Name": ["Smith"]})
        gr = make_gr(df)
        rename_map = gr.GLOBAL_03_column_name_normalization()
        assert "First Name" in rename_map
        assert rename_map["First Name"] == "first_name"

    def test_mixed_case_lowercased(self):
        df = pd.DataFrame({"CustomerID": [1], "OrderDate": ["2024-01-01"]})
        gr = make_gr(df)
        gr.GLOBAL_03_column_name_normalization()
        assert "customerid" in gr.df.columns or "customer_id" in gr.df.columns

    def test_special_chars_removed(self):
        df = pd.DataFrame({"col!@#name": [1], "price($)": [9.99]})
        gr = make_gr(df)
        gr.GLOBAL_03_column_name_normalization()
        for col in gr.df.columns:
            assert col == col.lower()
            assert all(c.isalnum() or c == "_" for c in col)

    def test_typo_correction_fule_to_fuel(self):
        df = pd.DataFrame({"Fule Cost": [100]})
        gr = make_gr(df)
        gr.GLOBAL_03_column_name_normalization()
        assert "fuel_cost" in gr.df.columns

    def test_typo_correction_emial_to_email(self):
        df = pd.DataFrame({"emial": ["test@test.com"]})
        gr = make_gr(df)
        gr.GLOBAL_03_column_name_normalization()
        assert "email" in gr.df.columns

    def test_already_snake_case_unchanged(self):
        df = pd.DataFrame({"first_name": ["Alice"], "age": [30]})
        gr = make_gr(df)
        rename_map = gr.GLOBAL_03_column_name_normalization()
        assert rename_map == {}  # Nothing changed

    def test_hyphens_replaced(self):
        df = pd.DataFrame({"start-date": ["2024-01-01"]})
        gr = make_gr(df)
        gr.GLOBAL_03_column_name_normalization()
        assert "start_date" in gr.df.columns

    def test_multiple_underscores_collapsed(self):
        df = pd.DataFrame({"col___name": [1]})
        gr = make_gr(df)
        gr.GLOBAL_03_column_name_normalization()
        assert "col_name" in gr.df.columns


class TestGLOBAL_04_HeaderDuplicateCheck:
    """GLOBAL-04: duplicate column names flagged after normalization."""

    def test_detects_post_normalization_duplicates(self):
        # After GLOBAL-03, "Name" and "name" would both become "name"
        # Simulate by providing already-duplicated names
        df = pd.DataFrame([[1, 2, 3]], columns=["name", "age", "name"])
        gr = make_gr(df)
        dups = gr.GLOBAL_04_header_duplicate_check()
        assert len(dups) > 0
        assert any(d["name"] == "name" for d in dups)
        assert any(f["formula_id"] == "GLOBAL-04" for f in gr.flags)

    def test_auto_suffixes_duplicate_columns(self):
        # Second "name" should get a suffix to avoid pandas ambiguity
        df = pd.DataFrame([[1, 2, 3]], columns=["id", "score", "score"])
        gr = make_gr(df)
        gr.GLOBAL_04_header_duplicate_check()
        assert "score_1" in gr.df.columns

    def test_no_duplicates_no_flags(self):
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        gr = make_gr(df)
        dups = gr.GLOBAL_04_header_duplicate_check()
        assert dups == []


class TestGLOBAL_05_AllNullRowRemoval:
    """GLOBAL-05: rows where every cell is null are auto-removed."""

    def test_removes_all_null_rows(self):
        df = pd.DataFrame({
            "a": [1, None, 3],
            "b": [4, None, 6],
            "c": [7, None, 9],
        })
        gr = make_gr(df)
        count = gr.GLOBAL_05_all_null_row_removal()
        assert count == 1
        assert len(gr.df) == 2

    def test_partial_null_row_not_removed(self):
        df = pd.DataFrame({
            "a": [1, None, 3],
            "b": [4, 5, 6],  # row 1 has value in b
        })
        gr = make_gr(df)
        count = gr.GLOBAL_05_all_null_row_removal()
        assert count == 0
        assert len(gr.df) == 3

    def test_multiple_all_null_rows_removed(self):
        df = pd.DataFrame({
            "x": [1, None, None, 4],
            "y": [2, None, None, 5],
        })
        gr = make_gr(df)
        count = gr.GLOBAL_05_all_null_row_removal()
        assert count == 2

    def test_cleans_log_for_each_removed_row(self):
        db = make_db()
        df = pd.DataFrame({"a": [None, None], "b": [None, None]})
        gr = make_gr(df, db)
        gr.GLOBAL_05_all_null_row_removal()
        from app.models.cleaning_log import CleaningLog
        log_entries = [e for e in db.added if isinstance(e, CleaningLog)]
        assert len(log_entries) == 2


class TestGLOBAL_06_RowStructuralIntegrity:
    """GLOBAL-06: rows >80% null with ≤2 non-null values flagged (ask-first)."""

    def test_flags_malformed_row(self):
        # 6-column df; row 1 has only 1 non-null value → >80% null, ≤2 non-null
        data = {
            "a": [1, "stray"],
            "b": [2, None],
            "c": [3, None],
            "d": [4, None],
            "e": [5, None],
            "f": [6, None],
        }
        df = pd.DataFrame(data)
        gr = make_gr(df)
        count = gr.GLOBAL_06_row_structural_integrity()
        assert count == 1
        assert any(f["formula_id"] == "GLOBAL-06" for f in gr.flags)

    def test_narrow_dataset_skipped(self):
        # < 4 columns → skip check
        df = pd.DataFrame({"a": [1, None], "b": [2, None]})
        gr = make_gr(df)
        count = gr.GLOBAL_06_row_structural_integrity()
        assert count == 0


class TestGLOBAL_07_TrailingSummaryRowDetection:
    """GLOBAL-07: rows with Total/Sum/Average keywords auto-removed."""

    def test_removes_total_row(self):
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Total"],
            "amount": [100, 200, 300],
        })
        gr = make_gr(df)
        count = gr.GLOBAL_07_trailing_summary_row_detection()
        assert count == 1
        assert len(gr.df) == 2
        assert "Total" not in gr.df["name"].values

    def test_removes_grand_total_row(self):
        df = pd.DataFrame({
            "label": ["A", "B", "grand total"],
            "value": [10, 20, 30],
        })
        gr = make_gr(df)
        count = gr.GLOBAL_07_trailing_summary_row_detection()
        assert count == 1

    def test_removes_average_row(self):
        df = pd.DataFrame({
            "metric": ["x", "y", "average"],
            "val": [5, 10, 7.5],
        })
        gr = make_gr(df)
        count = gr.GLOBAL_07_trailing_summary_row_detection()
        assert count == 1

    def test_normal_data_unchanged(self):
        df = pd.DataFrame({
            "city": ["London", "Paris", "Berlin"],
            "pop": [9_000_000, 2_100_000, 3_600_000],
        })
        gr = make_gr(df)
        count = gr.GLOBAL_07_trailing_summary_row_detection()
        assert count == 0
        assert len(gr.df) == 3


class TestGLOBAL_08_RepeatedHeaderRowDetection:
    """GLOBAL-08: rows that mirror the column headers are auto-removed."""

    def test_removes_repeated_header_row(self):
        df = pd.DataFrame({
            "id": [1, "id", 2],
            "name": ["Alice", "name", "Bob"],
            "age": [30, "age", 25],
        })
        gr = make_gr(df)
        count = gr.GLOBAL_08_repeated_header_row_detection()
        assert count == 1
        assert len(gr.df) == 2

    def test_data_only_unchanged(self):
        df = pd.DataFrame({
            "product": ["A", "B", "C"],
            "price": [10, 20, 30],
        })
        gr = make_gr(df)
        count = gr.GLOBAL_08_repeated_header_row_detection()
        assert count == 0


class TestGLOBAL_09_DataTypeInference:
    """GLOBAL-09: infers dominant type and flags >10% mismatch."""

    def test_integer_column_inferred(self):
        df = pd.DataFrame({"age": [25, 30, 35, 40, 22]})
        gr = make_gr(df)
        report = gr.GLOBAL_09_data_type_inference()
        assert report["age"]["dominant_type"] in ("integer", "float")

    def test_mismatch_flagged_in_summary(self):
        # 80% integers, 20% strings → >10% mismatch
        df = pd.DataFrame({"score": [10, 20, 30, 40, "N/A"]})
        gr = make_gr(df)
        report = gr.GLOBAL_09_data_type_inference()
        assert report["score"]["mismatch_pct"] > 0

    def test_empty_column_handled(self):
        df = pd.DataFrame({"blank": [None, None, None]})
        gr = make_gr(df)
        report = gr.GLOBAL_09_data_type_inference()
        assert "blank" in report
        assert report["blank"]["dominant_type"] == "empty"

    def test_date_column_inferred(self):
        df = pd.DataFrame({"created_at": ["2024-01-01", "2024-02-15", "2024-03-20"]})
        gr = make_gr(df)
        report = gr.GLOBAL_09_data_type_inference()
        assert report["created_at"]["dominant_type"] == "date"


class TestGLOBAL_10_PIIColumnTagging:
    """GLOBAL-10: PII columns tagged by keyword matching."""

    def test_email_tagged_medium(self):
        df = pd.DataFrame({"email": ["a@b.com"], "amount": [100]})
        gr = make_gr(df)
        tags = gr.GLOBAL_10_pii_column_tagging()
        assert "email" in tags
        assert tags["email"]["level"] == "medium"

    def test_diagnosis_tagged_high(self):
        df = pd.DataFrame({"diagnosis": ["flu"], "id": [1]})
        gr = make_gr(df)
        tags = gr.GLOBAL_10_pii_column_tagging()
        assert "diagnosis" in tags
        assert tags["diagnosis"]["level"] == "high"

    def test_city_tagged_low(self):
        df = pd.DataFrame({"city": ["London"], "zip": ["EC1"]})
        gr = make_gr(df)
        tags = gr.GLOBAL_10_pii_column_tagging()
        assert "city" in tags
        assert tags["city"]["level"] == "low"

    def test_non_pii_column_not_tagged(self):
        df = pd.DataFrame({"product_code": ["SKU-001"], "quantity": [5]})
        gr = make_gr(df)
        tags = gr.GLOBAL_10_pii_column_tagging()
        assert "product_code" not in tags
        assert "quantity" not in tags

    def test_phone_tagged_medium(self):
        df = pd.DataFrame({"phone": ["+44123456789"]})
        gr = make_gr(df)
        tags = gr.GLOBAL_10_pii_column_tagging()
        assert "phone" in tags
        assert tags["phone"]["level"] == "medium"


class TestGLOBAL_13_MergedCellForwardFill:
    """GLOBAL-13: merged-cell pattern detected and forward-filled."""

    def test_forward_fills_typical_merged_pattern(self):
        # Region column: value → null → null → value → null → null → value
        df = pd.DataFrame({
            "region": ["North", None, None, "South", None, None, "East"],
            "sales": [100, 200, 300, 400, 500, 600, 700],
        })
        gr = make_gr(df)
        filled = gr.GLOBAL_13_merged_cell_forward_fill()
        assert "region" in filled
        # No nulls should remain in the region column
        assert gr.df["region"].isnull().sum() == 0
        assert gr.df["region"].tolist() == [
            "North", "North", "North", "South", "South", "South", "East"
        ]

    def test_dense_column_not_forward_filled(self):
        # Column with no gaps — avg_gap = 1 → not a merged cell pattern
        df = pd.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50],
        })
        gr = make_gr(df)
        filled = gr.GLOBAL_13_merged_cell_forward_fill()
        assert "value" not in filled

    def test_logs_forward_fill_action(self):
        db = make_db()
        df = pd.DataFrame({
            "dept": ["HR", None, None, "IT", None, None],
            "emp_id": [1, 2, 3, 4, 5, 6],
        })
        gr = make_gr(df, db)
        gr.GLOBAL_13_merged_cell_forward_fill()
        from app.models.cleaning_log import CleaningLog
        formula_ids = [
            e.formula_id for e in db.added if isinstance(e, CleaningLog)
        ]
        assert "GLOBAL-13" in formula_ids


class TestGLOBAL_16_MixedDataTypeColumnAlert:
    """GLOBAL-16: >20% type mismatch triggers an ask-first flag."""

    def test_flags_column_with_high_mismatch(self):
        # Force a type_inference result with >20% mismatch
        df = pd.DataFrame({"val": [1, 2, 3, 4, 5]})
        gr = make_gr(df)
        # Manually inject a type_inference summary entry with >20% mismatch
        gr.summary["type_inference"] = {
            "messy_col": {
                "dominant_type": "integer",
                "mismatch_pct": 35.0,
                "type_counts": {"integer": 65, "string": 35},
            }
        }
        mixed = gr.GLOBAL_16_mixed_data_type_column_alert()
        assert "messy_col" in mixed
        assert any(f["formula_id"] == "GLOBAL-16" for f in gr.flags)

    def test_column_below_threshold_not_flagged(self):
        df = pd.DataFrame({"val": [1, 2, 3, 4, 5]})
        gr = make_gr(df)
        gr.summary["type_inference"] = {
            "clean_col": {
                "dominant_type": "integer",
                "mismatch_pct": 5.0,
                "type_counts": {"integer": 95, "string": 5},
            }
        }
        mixed = gr.GLOBAL_16_mixed_data_type_column_alert()
        assert "clean_col" not in mixed


# ═════════════════════════════════════════════════════════════════════════════
# Integration: run_all() orchestration test
# ═════════════════════════════════════════════════════════════════════════════

class TestRunAllOrchestration:
    """
    run_all() on a single "maximally messy" DataFrame must:
    - apply cell-level rules (GLOBAL-11/12/14/15)
    - remove all-null rows (GLOBAL-05)
    - remove summary / repeated-header rows (GLOBAL-07/08)
    - normalise column names (GLOBAL-03)
    - flag empty / constant / duplicate columns (GLOBAL-01/02/04)
    - detect and forward-fill merged cells (GLOBAL-13)
    - run type inference (GLOBAL-09)
    - tag PII columns (GLOBAL-10)
    - check structural integrity (GLOBAL-06)
    - flag mixed-type columns (GLOBAL-16)
    """

    @pytest.fixture
    def messy_df(self):
        """
        A 12-row DataFrame designed to trigger every single GLOBAL rule.
        """
        return pd.DataFrame({
            # ── Repeated header row (GLOBAL-08) ──────────
            # ── Normal data ──────────────────────────────
            # ── Columns:
            #   "First Name" → needs GLOBAL-03 normalization
            #   "emial"      → typo, GLOBAL-03 corrects to "email"  + GLOBAL-10 PII
            #   "  phone  "  → needs GLOBAL-03 normalization + GLOBAL-10 PII
            #   "diagnosis"  → GLOBAL-10 PII (high)
            #   "empty_col"  → 100% null → GLOBAL-01
            #   "const_col"  → all "active" → GLOBAL-02
            #   "score"      → mixed types (int + string) → GLOBAL-09 / GLOBAL-16
            #   "region"     → merged-cell pattern → GLOBAL-13
            "First Name": [
                "First Name",        # row 0: repeated header — GLOBAL-08
                "\ufeffAlice",       # row 1: BOM character — GLOBAL-12
                "Bob",
                "Carol",
                None, None, None, None, None, None, None,
                "Total",             # row 11: summary row — GLOBAL-07
            ],
            "emial": [
                "emial",             # repeated header
                "alice@example.com",
                "bob@example.com",
                "carol@example.com",
                None, None, None, None, None, None, None,
                None,
            ],
            "  phone  ": [
                "  phone  ",
                "+44 7700 900001",
                "+44 7700 900002",
                "+44 7700 900003",
                None, None, None, None, None, None, None,
                None,
            ],
            "diagnosis": [
                "diagnosis",
                "Hypertension",
                "Diabetes\u00e2\u0080\u0099s",  # mojibake apostrophe — GLOBAL-11
                "'Flu",                           # leading apostrophe — GLOBAL-14
                None, None, None, None, None, None, None,
                None,
            ],
            "empty_col": [None] * 12,   # 100% null → GLOBAL-01

            "const_col": ["active"] * 12,   # zero variance → GLOBAL-02

            "score": [
                "score",
                100, 200, 300,
                "  ",               # whitespace only → GLOBAL-15
                None, None, None, None, None, None,
                None,
            ],

            "region": [
                "region",
                "North", None, None,  # merged-cell pattern → GLOBAL-13
                "South", None, None,
                "East", None, None,
                None,
                None,
            ],
        })

    def test_run_all_completes_without_error(self, messy_df):
        gr = make_gr(messy_df)
        result = gr.run_all()
        assert isinstance(result, dict)
        assert "global_rules_applied" in result

    def test_run_all_applies_at_least_12_rules(self, messy_df):
        gr = make_gr(messy_df)
        result = gr.run_all()
        rules_applied = result["global_rules_applied"]
        # All 16 rule IDs should appear; at minimum 12 should fire on this data
        assert len(rules_applied) >= 12

    def test_summary_rows_removed(self, messy_df):
        gr = make_gr(messy_df)
        gr.run_all()
        # "Total" row should be gone
        for col in gr.df.columns:
            assert "Total" not in [str(v).strip() for v in gr.df[col] if pd.notna(v)], \
                f"'Total' summary row still present in column '{col}'"

    def test_pii_tags_populated(self, messy_df):
        gr = make_gr(messy_df)
        gr.run_all()
        pii = gr.summary["pii_tags"]
        # email (GLOBAL-10 medium), phone (medium), diagnosis (high) should be tagged
        # Column names will have been normalised by GLOBAL-03 by the time GLOBAL-10 runs
        pii_keys_lower = {k.lower() for k in pii.keys()}
        assert any("email" in k or "emial" in k for k in pii_keys_lower), \
            f"email/emial column not in PII tags: {pii_keys_lower}"

    def test_empty_col_flagged(self, messy_df):
        gr = make_gr(messy_df)
        gr.run_all()
        global_01_flags = [f for f in gr.flags if f["formula_id"] == "GLOBAL-01"]
        assert len(global_01_flags) >= 1, "empty_col should have been flagged by GLOBAL-01"

    def test_const_col_flagged(self, messy_df):
        gr = make_gr(messy_df)
        gr.run_all()
        global_02_flags = [f for f in gr.flags if f["formula_id"] == "GLOBAL-02"]
        assert len(global_02_flags) >= 1, "const_col should have been flagged by GLOBAL-02"

    def test_column_names_normalised(self, messy_df):
        gr = make_gr(messy_df)
        gr.run_all()
        # All column names should be snake_case
        for col in gr.df.columns:
            assert col == col.lower(), f"Column '{col}' is not lowercase"
            assert " " not in col, f"Column '{col}' contains spaces"

    def test_all_null_rows_removed(self, messy_df):
        gr = make_gr(messy_df)
        gr.run_all()
        # No row should be fully null
        assert not gr.df.isnull().all(axis=1).any(), "All-null row not removed"

    def test_bom_stripped(self):
        df = pd.DataFrame({
            "\ufeffcolumn_a": ["\ufeffvalue1", "value2"],
            "column_b": ["x", "y"],
        })
        gr = make_gr(df)
        gr.run_all()
        for col in gr.df.columns:
            assert "\ufeff" not in col
        for val in gr.df.iloc[:, 0]:
            if isinstance(val, str):
                assert "\ufeff" not in val


# ═════════════════════════════════════════════════════════════════════════════
# Constants & registry sanity checks
# ═════════════════════════════════════════════════════════════════════════════

class TestConstants:
    def test_pii_registry_has_three_levels(self):
        assert set(PII_REGISTRY.keys()) == {"high", "medium", "low"}

    def test_pii_registry_has_required_fields(self):
        for level, data in PII_REGISTRY.items():
            assert "keywords" in data, f"Missing 'keywords' in level '{level}'"
            assert "label" in data
            assert "governance" in data
            assert len(data["keywords"]) > 0

    def test_summary_row_keywords_contains_common(self):
        required = {"total", "grand total", "subtotal", "sum", "average"}
        assert required.issubset(SUMMARY_ROW_KEYWORDS)

    def test_column_word_corrections_has_fule(self):
        assert "fule" in COLUMN_WORD_CORRECTIONS
        assert COLUMN_WORD_CORRECTIONS["fule"] == "fuel"

    def test_column_word_corrections_has_emial(self):
        assert "emial" in COLUMN_WORD_CORRECTIONS
        assert COLUMN_WORD_CORRECTIONS["emial"] == "email"
