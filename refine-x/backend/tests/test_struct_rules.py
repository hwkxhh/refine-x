"""
Tests for StructRules — Session 2  (STRUCT-01 through STRUCT-06)
=================================================================
Every rule is tested in isolation plus an integration run_all() test.
A mock DB session absorbs all ORM calls — no real DB required.

Run with:
    pytest backend/tests/test_struct_rules.py -v
"""

from __future__ import annotations

import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import numpy as np
import pandas as pd
import pytest

from app.services.struct_rules import (
    StructRules,
    _is_temporal_token,
    _split_temporal,
    _classify_date_granularity,
    MONTH_TOKENS,
    QUARTER_TOKENS,
)


# ─────────────────────────────────────────────────────────────────────────────
# Mock DB
# ─────────────────────────────────────────────────────────────────────────────

class MockDB:
    def __init__(self):
        self.added: list = []

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        pass

    def commit(self):
        pass


def make_db() -> MockDB:
    return MockDB()


def make_sr(df: pd.DataFrame, db: MockDB | None = None,
            file_bytes: bytes | None = None,
            file_type: str | None = None) -> StructRules:
    return StructRules(
        job_id=1,
        df=df,
        db=db or make_db(),
        file_bytes=file_bytes,
        file_type=file_type,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Module-level helper function tests
# ═════════════════════════════════════════════════════════════════════════════

class TestTemporalTokenHelpers:
    """Tests for _is_temporal_token and _split_temporal."""

    def test_month_short_name_is_temporal(self):
        for m in ["jan", "feb", "mar", "apr", "may", "jun",
                  "jul", "aug", "sep", "oct", "nov", "dec"]:
            assert _is_temporal_token(m), f"'{m}' should be temporal"

    def test_month_long_name_is_temporal(self):
        assert _is_temporal_token("january")
        assert _is_temporal_token("december")

    def test_quarter_tokens_are_temporal(self):
        for q in ["q1", "q2", "q3", "q4"]:
            assert _is_temporal_token(q), f"'{q}' should be temporal"

    def test_four_digit_year_is_temporal(self):
        assert _is_temporal_token("2024")
        assert _is_temporal_token("1999")
        assert _is_temporal_token("2000")

    def test_non_temporal_tokens_rejected(self):
        for t in ["sales", "revenue", "total", "name", "id", "abc123"]:
            assert not _is_temporal_token(t), f"'{t}' should NOT be temporal"

    def test_fiscal_year_is_temporal(self):
        assert _is_temporal_token("fy2024")
        assert _is_temporal_token("FY24")

    def test_split_suffix_temporal(self):
        root, temporal = _split_temporal("sales_jan")
        assert root == "sales"
        assert temporal == "jan"

    def test_split_prefix_temporal(self):
        root, temporal = _split_temporal("q1_revenue")
        assert root == "revenue"
        assert temporal == "q1"

    def test_split_year_suffix(self):
        root, temporal = _split_temporal("revenue_2022")
        assert root == "revenue"
        assert temporal == "2022"

    def test_split_no_temporal(self):
        root, temporal = _split_temporal("customer_name")
        assert root is None
        assert temporal is None

    def test_split_single_token_no_match(self):
        root, temporal = _split_temporal("sales")
        assert root is None
        assert temporal is None


class TestGranularityClassifier:
    """Tests for _classify_date_granularity."""

    def test_iso_daily(self):
        assert _classify_date_granularity("2024-01-15") == "daily"

    def test_slash_daily(self):
        assert _classify_date_granularity("15/01/2024") == "daily"

    def test_monthly_iso(self):
        assert _classify_date_granularity("2024-01") == "monthly"

    def test_monthly_long_name(self):
        assert _classify_date_granularity("January 2024") == "monthly"

    def test_monthly_short_name(self):
        assert _classify_date_granularity("Jan 2024") == "monthly"

    def test_quarterly(self):
        assert _classify_date_granularity("Q1 2024") == "quarterly"
        assert _classify_date_granularity("2024-Q3") == "quarterly"

    def test_yearly(self):
        assert _classify_date_granularity("2024") == "yearly"
        assert _classify_date_granularity("FY2024") == "yearly"

    def test_non_date_unknown(self):
        assert _classify_date_granularity("hello world") == "unknown"
        assert _classify_date_granularity("abc") == "unknown"

    def test_non_string_unknown(self):
        assert _classify_date_granularity(123) == "unknown"
        assert _classify_date_granularity(None) == "unknown"


# ═════════════════════════════════════════════════════════════════════════════
# STRUCT-01  Wide-to-Long Format Detection
# ═════════════════════════════════════════════════════════════════════════════

class TestSTRUCT_01_WideToLong:

    def test_detects_monthly_suffix_group(self):
        df = pd.DataFrame({
            "region":      ["North", "South"],
            "sales_jan":   [100, 200],
            "sales_feb":   [110, 210],
            "sales_mar":   [120, 220],
        })
        sr = make_sr(df)
        candidates = sr.STRUCT_01_wide_to_long_detection()
        assert len(candidates) == 1
        assert candidates[0]["root"] == "sales"
        col_names = {m["column"] for m in candidates[0]["columns"]}
        assert col_names == {"sales_jan", "sales_feb", "sales_mar"}

    def test_detects_yearly_suffix_group(self):
        df = pd.DataFrame({
            "country":        ["UK", "US"],
            "revenue_2021":   [1, 2],
            "revenue_2022":   [3, 4],
            "revenue_2023":   [5, 6],
        })
        sr = make_sr(df)
        candidates = sr.STRUCT_01_wide_to_long_detection()
        assert len(candidates) == 1
        assert candidates[0]["root"] == "revenue"

    def test_detects_quarterly_prefix_group(self):
        df = pd.DataFrame({
            "dept":     ["HR"],
            "q1_cost":  [10],
            "q2_cost":  [20],
            "q3_cost":  [30],
            "q4_cost":  [40],
        })
        sr = make_sr(df)
        candidates = sr.STRUCT_01_wide_to_long_detection()
        assert len(candidates) == 1
        assert candidates[0]["root"] == "cost"

    def test_two_groups_detected_independently(self):
        df = pd.DataFrame({
            "id":          [1],
            "sales_jan":   [10], "sales_feb": [20], "sales_mar": [30],
            "cost_jan":    [5],  "cost_feb":  [8],  "cost_mar":  [9],
        })
        sr = make_sr(df)
        candidates = sr.STRUCT_01_wide_to_long_detection()
        roots = {c["root"] for c in candidates}
        assert "sales" in roots
        assert "cost" in roots

    def test_only_two_wide_cols_not_flagged(self):
        # Threshold is ≥3 — two columns should NOT trigger
        df = pd.DataFrame({
            "id":        [1, 2],
            "sales_jan": [10, 20],
            "sales_feb": [30, 40],
        })
        sr = make_sr(df)
        candidates = sr.STRUCT_01_wide_to_long_detection()
        assert len(candidates) == 0

    def test_non_wide_df_produces_no_flags(self):
        df = pd.DataFrame({
            "name":  ["Alice", "Bob"],
            "age":   [30, 25],
            "email": ["a@b.com", "c@d.com"],
        })
        sr = make_sr(df)
        candidates = sr.STRUCT_01_wide_to_long_detection()
        assert candidates == []

    def test_flag_contains_reshape_action(self):
        df = pd.DataFrame({
            "id":        [1],
            "rev_2020":  [10], "rev_2021": [20], "rev_2022": [30],
        })
        sr = make_sr(df)
        sr.STRUCT_01_wide_to_long_detection()
        assert any(f["formula_id"] == "STRUCT-01" for f in sr.flags)
        flag = next(f for f in sr.flags if f["formula_id"] == "STRUCT-01")
        assert flag["suggested_action"] == "reshape_wide_to_long"

    def test_does_not_modify_dataframe(self):
        df = pd.DataFrame({
            "id": [1], "s_jan": [1], "s_feb": [2], "s_mar": [3],
        })
        sr = make_sr(df)
        cols_before = list(sr.df.columns)
        sr.STRUCT_01_wide_to_long_detection()
        assert list(sr.df.columns) == cols_before  # STRUCT-01 is ask-first — no shape change


# ═════════════════════════════════════════════════════════════════════════════
# STRUCT-02  Merged Row Forward-Fill
# ═════════════════════════════════════════════════════════════════════════════

class TestSTRUCT_02_MergedRowForwardFill:

    def test_forward_fills_group_label_column(self):
        df = pd.DataFrame({
            "class":   ["A", None, None, "B", None, None],
            "student": ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"],
            "score":   [90, 85, 88, 76, 92, 80],
        })
        sr = make_sr(df)
        filled = sr.STRUCT_02_merged_row_forward_fill()
        assert "class" in filled
        assert sr.df["class"].tolist() == ["A", "A", "A", "B", "B", "B"]

    def test_group_label_column_logged(self):
        db = make_db()
        df = pd.DataFrame({
            "dept": ["HR", None, None, "IT", None, None],
            "emp":  [1, 2, 3, 4, 5, 6],
        })
        sr = make_sr(df, db)
        sr.STRUCT_02_merged_row_forward_fill()
        from app.models.cleaning_log import CleaningLog
        formula_ids = [e.formula_id for e in db.added if isinstance(e, CleaningLog)]
        assert "STRUCT-02" in formula_ids

    def test_column_starting_with_null_skipped(self):
        # Starts with null → not a group-label pattern
        df = pd.DataFrame({
            "group":  [None, "A", None, None, "B", None],
            "val":    [1, 2, 3, 4, 5, 6],
        })
        sr = make_sr(df)
        filled = sr.STRUCT_02_merged_row_forward_fill()
        assert "group" not in filled

    def test_high_cardinality_column_skipped(self):
        # Each non-null is unique → not a group label
        df = pd.DataFrame({
            "label": ["Alpha", None, "Beta", None, "Gamma", None,
                      "Delta", None, "Epsilon", None, "Zeta", None],
            "val":   range(12),
        })
        sr = make_sr(df)
        # 6 unique values in 6 non-null of 12 = 6/6 = 100% cardinality → SKIP
        # Actually threshold = max(10, 20% of 6) = max(10, 1.2) = 10; unique=6 ≤ 10 → might fill
        # Let's use 15 unique values to exceed threshold
        labels = [f"Group_{i}" if i % 2 == 0 else None for i in range(30)]
        vals   = list(range(30))
        df2 = pd.DataFrame({"label": labels, "val": vals})
        sr2 = make_sr(df2)
        filled = sr2.STRUCT_02_merged_row_forward_fill()
        # 15 unique values; threshold = max(10, 15 * 0.2) = max(10, 3) = 10
        # 15 > 10 → should be skipped
        assert "label" not in filled

    def test_numeric_dominant_column_skipped(self):
        # Numeric dominant → not a group label
        df = pd.DataFrame({
            "code": [101, None, None, 202, None, None],
            "val":  [1, 2, 3, 4, 5, 6],
        })
        sr = make_sr(df)
        filled = sr.STRUCT_02_merged_row_forward_fill()
        assert "code" not in filled

    def test_dense_column_not_filled(self):
        # No nulls → nothing to fill
        df = pd.DataFrame({
            "dept": ["HR", "HR", "IT", "IT"],
            "emp":  [1, 2, 3, 4],
        })
        sr = make_sr(df)
        filled = sr.STRUCT_02_merged_row_forward_fill()
        assert "dept" not in filled

    def test_multiple_group_label_columns_filled(self):
        df = pd.DataFrame({
            "region":  ["North", None, None, "South", None, None],
            "dept":    ["HR", None, None, "IT", None, None],
            "emp_id":  [1, 2, 3, 4, 5, 6],
        })
        sr = make_sr(df)
        filled = sr.STRUCT_02_merged_row_forward_fill()
        assert "region" in filled
        assert "dept" in filled


# ═════════════════════════════════════════════════════════════════════════════
# STRUCT-03  Mixed Granularity Detection
# ═════════════════════════════════════════════════════════════════════════════

class TestSTRUCT_03_MixedGranularity:

    def test_flags_daily_and_monthly_mix(self):
        df = pd.DataFrame({
            "date": [
                "2024-01-15", "2024-02-20", "2024-03-05",
                "January 2024", "February 2024", "March 2024",
                "2024-04-10", "April 2024", "2024-05-01",
            ]
        })
        sr = make_sr(df)
        mixed = sr.STRUCT_03_mixed_granularity_detection()
        assert len(mixed) == 1
        assert mixed[0]["column"] == "date"
        cols_in_breakdown = set(mixed[0]["breakdown"].keys())
        assert "daily" in cols_in_breakdown
        assert "monthly" in cols_in_breakdown

    def test_flags_daily_and_yearly_mix(self):
        df = pd.DataFrame({
            "period": ["2024-01-01", "2024-02-01", "2023", "2024-03-15",
                       "2022", "2024-04-01", "2024-05-01", "2024-06-01"]
        })
        sr = make_sr(df)
        mixed = sr.STRUCT_03_mixed_granularity_detection()
        assert any(m["column"] == "period" for m in mixed)

    def test_uniform_daily_column_not_flagged(self):
        df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02", "2024-01-03",
                     "2024-01-04", "2024-01-05", "2024-01-06"]
        })
        sr = make_sr(df)
        mixed = sr.STRUCT_03_mixed_granularity_detection()
        assert len(mixed) == 0

    def test_non_date_column_not_flagged(self):
        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank"]
        })
        sr = make_sr(df)
        mixed = sr.STRUCT_03_mixed_granularity_detection()
        assert len(mixed) == 0

    def test_flag_contains_standardize_action(self):
        df = pd.DataFrame({
            "dt": ["2024-01-01", "January 2024", "2024-02-15",
                   "February 2024", "2024-03-01", "March 2024",
                   "2024-04-10", "April 2024", "2024-05-20"]
        })
        sr = make_sr(df)
        sr.STRUCT_03_mixed_granularity_detection()
        flag = next((f for f in sr.flags if f["formula_id"] == "STRUCT-03"), None)
        assert flag is not None
        assert flag["suggested_action"] == "standardize_date_granularity"

    def test_does_not_modify_data(self):
        df = pd.DataFrame({
            "d": ["2024-01-01", "January 2024", "2024-02-15",
                  "Feb 2024", "2024-03-01", "March 2024"]
        })
        sr = make_sr(df)
        original_vals = sr.df["d"].tolist()
        sr.STRUCT_03_mixed_granularity_detection()
        assert sr.df["d"].tolist() == original_vals  # ask-first — no data change


# ═════════════════════════════════════════════════════════════════════════════
# STRUCT-04  Header Row Offset Detection
# ═════════════════════════════════════════════════════════════════════════════

class TestSTRUCT_04_HeaderRowOffset:

    def test_promotes_header_when_unnamed_columns(self):
        """Simulate a CSV where pandas found no header (all Unnamed:)."""
        # Build a DF as pandas would with no header detected
        raw_data = [
            ["Company Sales Report Q1 2024", None, None, None],
            ["Generated: 2024-03-01",         None, None, None],
            ["Name",   "Department", "Salary", "Join Date"],
            ["Alice",  "HR",         50000,    "2020-01-15"],
            ["Bob",    "IT",         60000,    "2019-06-01"],
        ]
        df = pd.DataFrame(raw_data, columns=["Unnamed: 0", "Unnamed: 1", "Unnamed: 2", "Unnamed: 3"])
        sr = make_sr(df)
        detected = sr.STRUCT_04_header_row_offset_detection()
        assert detected == 2   # Row 2 is the real header
        assert list(sr.df.columns) == ["Name", "Department", "Salary", "Join Date"]
        assert len(sr.df) == 2  # Only data rows remain

    def test_no_offset_clean_df_untouched(self):
        """A clean DataFrame with proper column names should not be touched."""
        df = pd.DataFrame({
            "name":   ["Alice", "Bob"],
            "age":    [30, 25],
            "salary": [50000, 60000],
        })
        sr = make_sr(df)
        cols_before = list(sr.df.columns)
        nrows_before = len(sr.df)
        detected = sr.STRUCT_04_header_row_offset_detection()
        assert detected is None
        assert list(sr.df.columns) == cols_before
        assert len(sr.df) == nrows_before

    def test_header_at_row_1_with_title_row(self):
        """One title row before the real header."""
        raw_data = [
            ["Employee Report 2024", None, None],
            ["Name",   "Age", "Department"],
            ["Alice",  30,    "HR"],
            ["Bob",    25,    "IT"],
        ]
        df = pd.DataFrame(raw_data, columns=["Unnamed: 0", "Unnamed: 1", "Unnamed: 2"])
        sr = make_sr(df)
        detected = sr.STRUCT_04_header_row_offset_detection()
        assert detected == 1
        assert "Name" in sr.df.columns
        assert "Age" in sr.df.columns

    def test_logs_correction(self):
        db = make_db()
        raw_data = [
            ["Report Title", None, None],
            ["Name", "Score", "Grade"],
            ["Alice", 90, "A"],
        ]
        df = pd.DataFrame(raw_data, columns=["Unnamed: 0", "Unnamed: 1", "Unnamed: 2"])
        sr = make_sr(df, db)
        sr.STRUCT_04_header_row_offset_detection()
        from app.models.cleaning_log import CleaningLog
        formula_ids = [e.formula_id for e in db.added if isinstance(e, CleaningLog)]
        assert "STRUCT-04" in formula_ids

    def test_empty_df_returns_none(self):
        df = pd.DataFrame()
        sr = make_sr(df)
        assert sr.STRUCT_04_header_row_offset_detection() is None


# ═════════════════════════════════════════════════════════════════════════════
# STRUCT-05  Multi-Sheet Aggregation
# ═════════════════════════════════════════════════════════════════════════════

class TestSTRUCT_05_MultiSheet:

    def _make_excel_bytes(self, sheets: dict[str, pd.DataFrame]) -> bytes:
        """Create an in-memory Excel workbook with the given sheets."""
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            for sheet_name, df in sheets.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        return buf.getvalue()

    def test_detects_compatible_sheets(self):
        df1 = pd.DataFrame({"name": ["Alice"], "score": [90], "grade": ["A"]})
        df2 = pd.DataFrame({"name": ["Bob"],   "score": [75], "grade": ["B"]})
        df3 = pd.DataFrame({"name": ["Carol"], "score": [85], "grade": ["A"]})
        excel_bytes = self._make_excel_bytes({"Jan": df1, "Feb": df2, "Mar": df3})
        sr = make_sr(pd.DataFrame(), file_bytes=excel_bytes, file_type="xlsx")
        compatible = sr.STRUCT_05_multi_sheet_aggregation()
        assert len(compatible) >= 2

    def test_flags_compatible_sheets(self):
        df1 = pd.DataFrame({"id": [1], "value": [10]})
        df2 = pd.DataFrame({"id": [2], "value": [20]})
        excel_bytes = self._make_excel_bytes({"Sheet1": df1, "Sheet2": df2})
        sr = make_sr(pd.DataFrame(), file_bytes=excel_bytes, file_type="xlsx")
        sr.STRUCT_05_multi_sheet_aggregation()
        assert any(f["formula_id"] == "STRUCT-05" for f in sr.flags)
        flag = next(f for f in sr.flags if f["formula_id"] == "STRUCT-05")
        assert flag["suggested_action"] == "stack_compatible_sheets"

    def test_incompatible_sheets_not_flagged(self):
        df1 = pd.DataFrame({"name": ["Alice"], "score": [90]})
        df2 = pd.DataFrame({"product": ["Widget"], "price": [9.99], "qty": [5], "category": ["A"]})
        excel_bytes = self._make_excel_bytes({"Students": df1, "Inventory": df2})
        sr = make_sr(pd.DataFrame(), file_bytes=excel_bytes, file_type="xlsx")
        compatible = sr.STRUCT_05_multi_sheet_aggregation()
        # Jaccard < 0.80 for these very different schemas
        assert len(compatible) < 2

    def test_csv_file_skipped(self):
        df = pd.DataFrame({"a": [1], "b": [2]})
        sr = make_sr(df, file_bytes=b"a,b\n1,2\n", file_type="csv")
        compatible = sr.STRUCT_05_multi_sheet_aggregation()
        assert compatible == []

    def test_no_file_bytes_skipped(self):
        df = pd.DataFrame({"a": [1]})
        sr = make_sr(df, file_bytes=None, file_type="xlsx")
        assert sr.STRUCT_05_multi_sheet_aggregation() == []

    def test_single_sheet_file_skipped(self):
        df1 = pd.DataFrame({"name": ["Alice"], "score": [90]})
        excel_bytes = self._make_excel_bytes({"OnlySheet": df1})
        sr = make_sr(pd.DataFrame(), file_bytes=excel_bytes, file_type="xlsx")
        compatible = sr.STRUCT_05_multi_sheet_aggregation()
        assert compatible == []


# ═════════════════════════════════════════════════════════════════════════════
# STRUCT-06  Transposed Table Detection
# ═════════════════════════════════════════════════════════════════════════════

class TestSTRUCT_06_TransposedTable:

    def test_detects_extreme_shape_ratio(self):
        # 30 columns, 3 rows → ratio 10:1 — triggers Signal 1
        # First column looks like column names → triggers Signal 2
        cols = ["metric"] + [f"obs_{i}" for i in range(29)]
        data = {
            "metric":  ["age", "salary", "score"],
        }
        for i in range(29):
            data[f"obs_{i}"] = [i * 10, i * 20, i * 30]
        df = pd.DataFrame(data)
        sr = make_sr(df)
        result = sr.STRUCT_06_transposed_table_detection()
        assert result is True
        assert sr.summary["transposed_likely"] is True

    def test_flags_with_transpose_action(self):
        data = {"metric": ["age", "salary", "score"]}
        for i in range(25):
            data[f"row_{i}"] = [i, i * 2, i * 3]
        df = pd.DataFrame(data)
        sr = make_sr(df)
        sr.STRUCT_06_transposed_table_detection()
        assert any(f["formula_id"] == "STRUCT-06" for f in sr.flags)
        flag = next(f for f in sr.flags if f["formula_id"] == "STRUCT-06")
        assert flag["suggested_action"] == "transpose_dataset"

    def test_normal_dataframe_not_flagged(self):
        df = pd.DataFrame({
            "name":  ["Alice", "Bob", "Carol", "Dave", "Eve"],
            "age":   [30, 25, 35, 28, 32],
            "dept":  ["HR", "IT", "Finance", "IT", "HR"],
        })
        sr = make_sr(df)
        result = sr.STRUCT_06_transposed_table_detection()
        assert result is False

    def test_numeric_column_names_signal(self):
        # Column names are year numbers (data values) → Signal 3
        data = {
            "metric": ["sales", "cost", "profit"],
            "2021": [100, 50, 50],
            "2022": [120, 55, 65],
            "2023": [140, 60, 80],
            "2024": [160, 65, 95],
            "2025": [180, 70, 110],
        }
        df = pd.DataFrame(data)
        sr = make_sr(df)
        result = sr.STRUCT_06_transposed_table_detection()
        # Signals: Signal 3 (5/6 cols are year numbers) + possible Signal 1 or 2
        assert result is True

    def test_does_not_modify_dataframe(self):
        data = {"metric": ["age", "salary"]}
        for i in range(20):
            data[f"obs_{i}"] = [i, i * 2]
        df = pd.DataFrame(data)
        sr = make_sr(df)
        original_shape = sr.df.shape
        sr.STRUCT_06_transposed_table_detection()
        assert sr.df.shape == original_shape  # ask-first — no transpose applied

    def test_too_few_columns_not_flagged(self):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        sr = make_sr(df)
        assert sr.STRUCT_06_transposed_table_detection() is False


# ═════════════════════════════════════════════════════════════════════════════
# Integration: run_all()
# ═════════════════════════════════════════════════════════════════════════════

class TestRunAllOrchestration:
    """run_all() on a dataset that triggers STRUCT-01, STRUCT-02, STRUCT-03,
    STRUCT-04, and STRUCT-06 simultaneously."""

    @pytest.fixture
    def messy_df(self):
        """
        DataFrame designed to trigger STRUCT-01 (wide cols), STRUCT-02
        (group label), and STRUCT-03 (mixed granularity) in a single run.
        """
        return pd.DataFrame({
            # Group label column with block nulls → STRUCT-02
            "region":    ["North", None, None, "South", None, None],
            # Mixed granularity → STRUCT-03
            "date":      ["2024-01-15", "Jan 2024", "2024-02-10",
                          "February 2024", "2024-03-05", "March 2024"],
            # Wide format (3 month columns) → STRUCT-01
            "sales_jan": [100, 200, 300, 400, 500, 600],
            "sales_feb": [110, 210, 310, 410, 510, 610],
            "sales_mar": [120, 220, 320, 420, 520, 620],
            # Normal column
            "rep":       ["A", "B", "C", "D", "E", "F"],
        })

    def test_run_all_returns_dict(self, messy_df):
        sr = make_sr(messy_df)
        result = sr.run_all()
        assert isinstance(result, dict)
        assert "struct_rules_applied" in result

    def test_run_all_applies_struct_01(self, messy_df):
        sr = make_sr(messy_df)
        result = sr.run_all()
        assert "STRUCT-01" in result["struct_rules_applied"]

    def test_run_all_applies_struct_02(self, messy_df):
        sr = make_sr(messy_df)
        result = sr.run_all()
        assert "STRUCT-02" in result["struct_rules_applied"]
        # Region column should be fully filled
        assert sr.df["region"].isnull().sum() == 0

    def test_run_all_applies_struct_03(self, messy_df):
        sr = make_sr(messy_df)
        result = sr.run_all()
        assert "STRUCT-03" in result["struct_rules_applied"]

    def test_run_all_does_not_modify_wide_cols(self, messy_df):
        """STRUCT-01 is ask-first — should not remove or rename the wide columns."""
        sr = make_sr(messy_df)
        sr.run_all()
        assert "sales_jan" in sr.df.columns
        assert "sales_feb" in sr.df.columns
        assert "sales_mar" in sr.df.columns

    def test_run_all_struct_04_clean_df_untouched(self):
        """A properly-labelled DataFrame should not be affected by STRUCT-04."""
        df = pd.DataFrame({
            "id":    [1, 2, 3],
            "score": [80, 90, 70],
        })
        sr = make_sr(df)
        sr.run_all()
        assert list(sr.df.columns) == ["id", "score"]
        assert len(sr.df) == 3

    def test_run_all_flags_list_is_populated(self, messy_df):
        sr = make_sr(messy_df)
        sr.run_all()
        flag_formula_ids = {f["formula_id"] for f in sr.flags}
        # At minimum STRUCT-01 and STRUCT-03 should produce flags
        assert "STRUCT-01" in flag_formula_ids
        assert "STRUCT-03" in flag_formula_ids

    def test_run_all_deduplicates_applied_rules(self, messy_df):
        sr = make_sr(messy_df)
        result = sr.run_all()
        applied = result["struct_rules_applied"]
        assert len(applied) == len(set(applied)), "Duplicate rule IDs in struct_rules_applied"

    def test_run_all_struct_04_runs_first(self):
        """STRUCT-04 must correct the header before other rules run.
        Verify by building a df where STRUCT-04 would rename a column and
        STRUCT-02 would then successfully detect the group label under the new name."""
        raw_data = [
            ["Report Title", None, None],         # title row
            ["category",    "item",   "price"],   # real header at row 1
            ["Electronics", "Phone",  999],
            [None,          "Laptop", 1299],
            [None,          "Tablet", 499],
            ["Clothing",    "Shirt",  49],
            [None,          "Pants",  59],
        ]
        df = pd.DataFrame(raw_data, columns=["Unnamed: 0", "Unnamed: 1", "Unnamed: 2"])
        sr = make_sr(df)
        sr.run_all()
        # After STRUCT-04, 'category' should be the column name
        assert "category" in sr.df.columns
        # After STRUCT-02, category should be forward-filled
        assert sr.df["category"].isnull().sum() == 0
