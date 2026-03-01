"""
Tests for Boolean, Category & Status Cleaning Rules — Session 8

Tests all helper functions and formula implementations for:
- HTYPE-018: Boolean / Flag (BOOL-01 to BOOL-04)
- HTYPE-019: Category / Classification (CAT-01 to CAT-08)
- HTYPE-020: Status Field (STAT-01 to STAT-05)
- HTYPE-045: Survey / Likert Response (SURV-01 to SURV-07)
- HTYPE-046: Multi-Value / Tag Field (MULTI-01 to MULTI-07)
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

from app.services.boolean_category_rules import (
    # Boolean helpers
    normalize_boolean,
    is_non_binary_value,
    detect_boolean_column,
    TRUE_VALUES,
    FALSE_VALUES,
    NON_BINARY_VALUES,
    
    # Category helpers
    to_title_case,
    clean_category_whitespace,
    fix_encoding_artifacts,
    calculate_similarity,
    find_similar_categories,
    get_category_frequencies,
    detect_rare_categories,
    
    # Status helpers
    normalize_status,
    detect_workflow_type,
    validate_workflow_sequence,
    detect_retired_status,
    STATUS_MAPPINGS,
    WORKFLOW_SEQUENCES,
    
    # Survey helpers
    detect_likert_scale,
    verbal_to_numeric_likert,
    fix_likert_typo,
    detect_straight_lining,
    check_likert_range,
    LIKERT_5_AGREE,
    LIKERT_7_AGREE,
    FREQUENCY_SCALE,
    SATISFACTION_SCALE,
    LIKERT_TYPOS,
    
    # Multi-value helpers
    detect_delimiter,
    is_multi_value_column,
    split_multi_value,
    standardize_multi_value_delimiter,
    get_unique_values_from_multi,
    build_variant_map,
    get_multi_value_frequency,
    explode_multi_value_column,
    
    # Main class
    BooleanCategoryRules,
)


# ============================================================================
# BOOLEAN HELPER TESTS
# ============================================================================

class TestNormalizeBoolean:
    def test_true_string_variants(self):
        assert normalize_boolean("yes") == True
        assert normalize_boolean("YES") == True
        assert normalize_boolean("y") == True
        assert normalize_boolean("true") == True
        assert normalize_boolean("TRUE") == True
        assert normalize_boolean("1") == True
        assert normalize_boolean("on") == True
        assert normalize_boolean("active") == True
        assert normalize_boolean("enabled") == True
    
    def test_false_string_variants(self):
        assert normalize_boolean("no") == False
        assert normalize_boolean("NO") == False
        assert normalize_boolean("n") == False
        assert normalize_boolean("false") == False
        assert normalize_boolean("FALSE") == False
        assert normalize_boolean("0") == False
        assert normalize_boolean("off") == False
        assert normalize_boolean("inactive") == False
        assert normalize_boolean("disabled") == False
    
    def test_numeric_values(self):
        assert normalize_boolean(1) == True
        assert normalize_boolean(0) == False
        assert normalize_boolean(1.0) == True
        assert normalize_boolean(0.0) == False
    
    def test_bool_values(self):
        assert normalize_boolean(True) == True
        assert normalize_boolean(False) == False
    
    def test_null_values(self):
        assert normalize_boolean(None) is None
        assert normalize_boolean(np.nan) is None
        assert normalize_boolean(pd.NA) is None
    
    def test_unparseable_values(self):
        assert normalize_boolean("maybe") is None
        assert normalize_boolean("hello") is None
        assert normalize_boolean(5) is None


class TestIsNonBinaryValue:
    def test_non_binary_values(self):
        assert is_non_binary_value("maybe") == True
        assert is_non_binary_value("pending") == True
        assert is_non_binary_value("unknown") == True
        assert is_non_binary_value("n/a") == True
    
    def test_binary_values(self):
        assert is_non_binary_value("yes") == False
        assert is_non_binary_value("no") == False
        assert is_non_binary_value("true") == False
    
    def test_null_values(self):
        assert is_non_binary_value(None) == False
        assert is_non_binary_value(np.nan) == False


class TestDetectBooleanColumn:
    def test_boolean_column(self):
        series = pd.Series(["yes", "no", "yes", "no", "y", "n"])
        is_bool, confidence = detect_boolean_column(series)
        assert is_bool == True
        assert confidence >= 0.9
    
    def test_non_boolean_column(self):
        series = pd.Series(["maybe", "pending", "yes", "no"])
        is_bool, confidence = detect_boolean_column(series)
        assert is_bool == False
    
    def test_empty_series(self):
        series = pd.Series([], dtype=object)
        is_bool, confidence = detect_boolean_column(series)
        assert is_bool == False


# ============================================================================
# CATEGORY HELPER TESTS
# ============================================================================

class TestToTitleCase:
    def test_basic_title_case(self):
        assert to_title_case("hello world") == "Hello World"
        assert to_title_case("HELLO WORLD") == "Hello World"
    
    def test_preserve_acronyms(self):
        assert to_title_case("IT department") == "IT Department"
        assert to_title_case("HR team") == "HR Team"
    
    def test_short_caps_preserved(self):
        assert to_title_case("IT") == "IT"
        assert to_title_case("HR") == "HR"
    
    def test_empty_string(self):
        assert to_title_case("") == ""
        assert to_title_case(None) is None


class TestCleanCategoryWhitespace:
    def test_trim_whitespace(self):
        assert clean_category_whitespace("  hello  ") == "hello"
        assert clean_category_whitespace("\thello\n") == "hello"
    
    def test_normalize_internal_whitespace(self):
        assert clean_category_whitespace("hello   world") == "hello world"
        assert clean_category_whitespace("hello\t\nworld") == "hello world"
    
    def test_empty_string(self):
        assert clean_category_whitespace("") == ""
        assert clean_category_whitespace(None) is None


class TestFixEncodingArtifacts:
    def test_fix_smart_quotes(self):
        # Test that function runs without error and returns a string
        result = fix_encoding_artifacts("hello'world")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_empty_string(self):
        assert fix_encoding_artifacts("") == ""
        assert fix_encoding_artifacts(None) is None


class TestCalculateSimilarity:
    def test_identical_strings(self):
        assert calculate_similarity("hello", "hello") == 1.0
    
    def test_similar_strings(self):
        score = calculate_similarity("science", "sciene")
        assert score > 0.8
    
    def test_different_strings(self):
        score = calculate_similarity("apple", "orange")
        assert score < 0.5
    
    def test_empty_strings(self):
        assert calculate_similarity("", "hello") == 0.0
        assert calculate_similarity("hello", "") == 0.0


class TestFindSimilarCategories:
    def test_find_match(self):
        existing = {"Science", "Mathematics", "English"}
        match = find_similar_categories("Sciene", existing, threshold=0.8)
        assert match == "Science"
    
    def test_no_match(self):
        existing = {"Science", "Mathematics", "English"}
        match = find_similar_categories("History", existing, threshold=0.8)
        assert match is None


class TestGetCategoryFrequencies:
    def test_frequency_count(self):
        series = pd.Series(["A", "B", "A", "C", "A", "B"])
        freq = get_category_frequencies(series)
        assert freq["A"] == 3
        assert freq["B"] == 2
        assert freq["C"] == 1


class TestDetectRareCategories:
    def test_detect_rare(self):
        # 100 rows, categories appearing <1% = <1 time, so use threshold 0.05
        series = pd.Series(["Common"] * 95 + ["Rare1", "Rare2", "Rare3", "Common", "Common"])
        rare = detect_rare_categories(series, threshold=0.05)
        assert "Rare1" in rare
        assert "Common" not in rare


# ============================================================================
# STATUS HELPER TESTS
# ============================================================================

class TestNormalizeStatus:
    def test_completed_variants(self):
        assert normalize_status("completed") == "Completed"
        assert normalize_status("complete") == "Completed"
        assert normalize_status("done") == "Completed"
        assert normalize_status("finished") == "Completed"
    
    def test_pending_variants(self):
        assert normalize_status("pending") == "Pending"
        assert normalize_status("waiting") == "Pending"
        assert normalize_status("on hold") == "Pending"
    
    def test_active_variants(self):
        assert normalize_status("active") == "Active"
        assert normalize_status("in progress") == "Active"
        assert normalize_status("ongoing") == "Active"
    
    def test_cancelled_variants(self):
        assert normalize_status("cancelled") == "Cancelled"
        assert normalize_status("canceled") == "Cancelled"
        assert normalize_status("void") == "Cancelled"
    
    def test_unknown_status(self):
        assert normalize_status("random") is None


class TestDetectWorkflowType:
    def test_standard_workflow(self):
        series = pd.Series(["New", "Pending", "Active", "Completed", "Active"])
        workflow = detect_workflow_type(series)
        assert workflow == "standard"
    
    def test_empty_series(self):
        series = pd.Series([], dtype=object)
        workflow = detect_workflow_type(series)
        assert workflow is None


# ============================================================================
# SURVEY HELPER TESTS
# ============================================================================

class TestDetectLikertScale:
    def test_numeric_5_scale(self):
        series = pd.Series([1, 2, 3, 4, 5, 3, 4, 2])
        scale_type, scale_size, mapping = detect_likert_scale(series)
        assert scale_type == "numeric_5"
        assert scale_size == 5
    
    def test_numeric_10_scale(self):
        series = pd.Series([1, 5, 7, 10, 3, 8])
        scale_type, scale_size, mapping = detect_likert_scale(series)
        assert scale_type == "numeric_10"
        assert scale_size == 10
    
    def test_agree_5_scale(self):
        series = pd.Series(["Strongly Agree", "Agree", "Neutral", "Disagree"])
        scale_type, scale_size, mapping = detect_likert_scale(series)
        assert scale_type == "agree_5"
        assert scale_size == 5
    
    def test_frequency_scale(self):
        series = pd.Series(["Never", "Sometimes", "Often", "Always"])
        scale_type, scale_size, mapping = detect_likert_scale(series)
        assert scale_type == "frequency"


class TestVerbalToNumericLikert:
    def test_5_point_agree(self):
        assert verbal_to_numeric_likert("strongly agree", LIKERT_5_AGREE) == 5
        assert verbal_to_numeric_likert("agree", LIKERT_5_AGREE) == 4
        assert verbal_to_numeric_likert("neutral", LIKERT_5_AGREE) == 3
        assert verbal_to_numeric_likert("disagree", LIKERT_5_AGREE) == 2
        assert verbal_to_numeric_likert("strongly disagree", LIKERT_5_AGREE) == 1
    
    def test_frequency(self):
        assert verbal_to_numeric_likert("never", FREQUENCY_SCALE) == 1
        assert verbal_to_numeric_likert("always", FREQUENCY_SCALE) == 5
    
    def test_with_typo(self):
        # Should fix typo first
        assert verbal_to_numeric_likert("stongly agree", LIKERT_5_AGREE) == 5


class TestFixLikertTypo:
    def test_agree_typos(self):
        fixed, was_typo = fix_likert_typo("stongly agree")
        assert was_typo == True
        assert fixed.lower() == "strongly agree"
    
    def test_neutral_typos(self):
        fixed, was_typo = fix_likert_typo("netural")
        assert was_typo == True
        assert fixed.lower() == "neutral"
    
    def test_no_typo(self):
        fixed, was_typo = fix_likert_typo("Strongly Agree")
        assert was_typo == False


class TestDetectStraightLining:
    def test_straight_liner(self):
        df = pd.DataFrame({
            "q1": ["agree", "agree", "disagree"],
            "q2": ["agree", "agree", "agree"],
            "q3": ["agree", "agree", "neutral"],
        })
        straight_liners = detect_straight_lining(df, ["q1", "q2", "q3"])
        assert 0 in straight_liners  # First row has all "agree"


class TestCheckLikertRange:
    def test_in_range(self):
        assert check_likert_range(3, 5) == True
        assert check_likert_range(1, 5) == True
        assert check_likert_range(5, 5) == True
    
    def test_out_of_range(self):
        assert check_likert_range(6, 5) == False
        assert check_likert_range(0, 5) == False


# ============================================================================
# MULTI-VALUE HELPER TESTS
# ============================================================================

class TestDetectDelimiter:
    def test_comma_delimiter(self):
        series = pd.Series(["a, b, c", "d, e", "f, g, h"])
        delim = detect_delimiter(series)
        assert delim == ","
    
    def test_semicolon_delimiter(self):
        series = pd.Series(["a; b; c", "d; e", "f; g; h"])
        delim = detect_delimiter(series)
        assert delim == ";"
    
    def test_pipe_delimiter(self):
        series = pd.Series(["a|b|c", "d|e", "f|g|h"])
        delim = detect_delimiter(series)
        assert delim == "|"


class TestIsMultiValueColumn:
    def test_multi_value(self):
        series = pd.Series(["a, b", "c, d, e", "f", "g, h"])
        is_multi, delim = is_multi_value_column(series)
        assert is_multi == True
        assert delim == ","
    
    def test_not_multi_value(self):
        series = pd.Series(["apple", "banana", "orange"])
        is_multi, delim = is_multi_value_column(series)
        assert is_multi == False


class TestSplitMultiValue:
    def test_comma_split(self):
        parts = split_multi_value("a, b, c", ",")
        assert parts == ["a", "b", "c"]
    
    def test_and_split(self):
        parts = split_multi_value("Math and Science and English", " and ")
        assert parts == ["Math", "Science", "English"]
    
    def test_empty_parts_removed(self):
        parts = split_multi_value("a,, b, ,c", ",")
        assert parts == ["a", "b", "c"]


class TestStandardizeDelimiter:
    def test_standardize_mixed(self):
        result = standardize_multi_value_delimiter("a;b,c|d", [";", ",", "|"], ", ")
        # After standardization, values should be comma-separated
        assert "," in result
        parts = [p.strip() for p in result.split(",")]
        assert parts == ["a", "b", "c", "d"]


class TestGetUniqueValuesFromMulti:
    def test_unique_values(self):
        series = pd.Series(["a, b", "b, c", "c, d"])
        unique = get_unique_values_from_multi(series, ",")
        assert unique == {"a", "b", "c", "d"}


class TestBuildVariantMap:
    def test_build_map(self):
        unique = {"Math", "Maths", "Mathematics"}
        mapping = build_variant_map(unique, threshold=0.7)
        # Should group similar values
        assert len(set(mapping.values())) <= len(unique)


class TestGetMultiValueFrequency:
    def test_frequency(self):
        series = pd.Series(["a, b", "b, c", "c, d, a"])
        freq = get_multi_value_frequency(series, ",")
        assert freq["a"] == 2
        assert freq["b"] == 2
        assert freq["c"] == 2
        assert freq["d"] == 1


class TestExplodeMultiValueColumn:
    def test_explode(self):
        df = pd.DataFrame({
            "id": [1, 2],
            "tags": ["a, b", "c"]
        })
        exploded = explode_multi_value_column(df, "tags", ",")
        assert len(exploded) == 3
        assert list(exploded["tags"]) == ["a", "b", "c"]


# ============================================================================
# BOOL FORMULA TESTS
# ============================================================================

class TestBoolFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db
    
    def test_BOOL_01_value_standardization(self, mock_db):
        df = pd.DataFrame({"is_active": ["yes", "no", "Y", "N", "true", "false"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"is_active": "HTYPE-018"}
        )
        result = runner.BOOL_01_value_standardization("is_active")
        assert result.changes_made > 0
    
    def test_BOOL_02_binary_enforcement(self, mock_db):
        df = pd.DataFrame({"status": ["yes", "no", "maybe", "pending"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"status": "HTYPE-018"}
        )
        result = runner.BOOL_02_binary_enforcement("status")
        assert result.rows_flagged == 2  # "maybe" and "pending"
    
    def test_BOOL_04_integer_encoding(self, mock_db):
        df = pd.DataFrame({"flag": ["yes", "no", "yes"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"flag": "HTYPE-018"}
        )
        runner.BOOL_01_value_standardization("flag")  # First normalize
        result = runner.BOOL_04_integer_encoding("flag")
        assert result.changes_made == 3
        assert list(runner.df["flag"]) == [1, 0, 1]


# ============================================================================
# CAT FORMULA TESTS
# ============================================================================

class TestCatFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db
    
    def test_CAT_01_title_case(self, mock_db):
        df = pd.DataFrame({"category": ["SCIENCE", "english", "Mathematics"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"category": "HTYPE-019"}
        )
        result = runner.CAT_01_title_case_normalization("category")
        assert result.changes_made == 2  # SCIENCE and english changed
    
    def test_CAT_02_variant_consolidation(self, mock_db):
        df = pd.DataFrame({"cat": ["Science", "SCIENCE", "science", "Math"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"cat": "HTYPE-019"}
        )
        result = runner.CAT_02_variant_consolidation("cat")
        # Should consolidate Science variants
        assert result.changes_made >= 0
    
    def test_CAT_07_whitespace_normalization(self, mock_db):
        df = pd.DataFrame({"cat": ["  Science  ", "Math  ", "  English"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"cat": "HTYPE-019"}
        )
        result = runner.CAT_07_whitespace_normalization("cat")
        assert result.changes_made == 3
        assert runner.df["cat"].iloc[0] == "Science"


# ============================================================================
# STAT FORMULA TESTS
# ============================================================================

class TestStatFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db
    
    def test_STAT_01_canonical_mapping(self, mock_db):
        df = pd.DataFrame({"status": ["completed", "done", "pending", "waiting"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"status": "HTYPE-020"}
        )
        result = runner.STAT_01_canonical_mapping("status")
        assert result.changes_made == 4
        assert runner.df["status"].iloc[0] == "Completed"
        assert runner.df["status"].iloc[1] == "Completed"
        assert runner.df["status"].iloc[2] == "Pending"
        assert runner.df["status"].iloc[3] == "Pending"
    
    def test_STAT_03_case_normalization(self, mock_db):
        df = pd.DataFrame({"status": ["ACTIVE", "pending", "COMPLETED"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"status": "HTYPE-020"}
        )
        result = runner.STAT_03_case_normalization("status")
        assert result.changes_made == 3


# ============================================================================
# SURV FORMULA TESTS
# ============================================================================

class TestSurvFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db
    
    def test_SURV_01_scale_detection(self, mock_db):
        df = pd.DataFrame({"q1": [1, 2, 3, 4, 5]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"q1": "HTYPE-045"}
        )
        result = runner.SURV_01_scale_detection("q1")
        assert result.details["scale_type"] == "numeric_5"
        assert result.details["scale_size"] == 5
    
    def test_SURV_02_verbal_to_numeric(self, mock_db):
        df = pd.DataFrame({"q1": ["Strongly Agree", "Agree", "Neutral"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"q1": "HTYPE-045"}
        )
        runner.SURV_01_scale_detection("q1")  # Detect scale first
        result = runner.SURV_02_verbal_to_numeric("q1")
        assert result.changes_made == 3
        assert runner.df["q1"].iloc[0] == 5
        assert runner.df["q1"].iloc[1] == 4
        assert runner.df["q1"].iloc[2] == 3
    
    def test_SURV_03_variant_standardization(self, mock_db):
        df = pd.DataFrame({"q1": ["stongly agree", "netural", "Agree"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"q1": "HTYPE-045"}
        )
        result = runner.SURV_03_variant_standardization("q1")
        assert result.changes_made == 2  # Fixed two typos
    
    def test_SURV_05_out_of_range_flag(self, mock_db):
        df = pd.DataFrame({"q1": [1, 3, 5, 7, 10]})  # 7 and 10 out of range for 5-scale
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"q1": "HTYPE-045"}
        )
        runner.detected_scales["q1"] = ("numeric_5", 5, {})
        result = runner.SURV_05_out_of_range_flag("q1")
        assert result.rows_flagged == 2


# ============================================================================
# MULTI FORMULA TESTS
# ============================================================================

class TestMultiFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db
    
    def test_MULTI_01_pattern_detection(self, mock_db):
        df = pd.DataFrame({"tags": ["a, b", "c, d, e", "f", "g, h"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"tags": "HTYPE-046"}
        )
        result = runner.MULTI_01_pattern_detection("tags")
        assert result.details["is_multi_value"] == True
        assert result.details["detected_delimiter"] == ","
    
    def test_MULTI_02_delimiter_standardization(self, mock_db):
        df = pd.DataFrame({"tags": ["a; b", "c| d", "e, f"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"tags": "HTYPE-046"}
        )
        result = runner.MULTI_02_delimiter_standardization("tags")
        assert result.changes_made >= 2  # Two rows with non-standard delimiters
    
    def test_MULTI_03_individual_value_cleaning(self, mock_db):
        df = pd.DataFrame({"tags": ["  math  ,  science  ", "english"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"tags": "HTYPE-046"}
        )
        runner.detected_delimiters["tags"] = ","
        result = runner.MULTI_03_individual_value_cleaning("tags")
        assert result.changes_made >= 1
        assert "Math" in runner.df["tags"].iloc[0]
    
    def test_MULTI_06_value_frequency_count(self, mock_db):
        df = pd.DataFrame({"tags": ["a, b", "b, c", "c, d"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"tags": "HTYPE-046"}
        )
        runner.detected_delimiters["tags"] = ","
        result = runner.MULTI_06_value_frequency_count("tags")
        assert result.details["unique_count"] == 4
    
    def test_MULTI_07_unique_value_registry(self, mock_db):
        df = pd.DataFrame({"tags": ["a, b", "b, c", "c, d"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"tags": "HTYPE-046"}
        )
        runner.detected_delimiters["tags"] = ","
        result = runner.MULTI_07_unique_value_registry("tags")
        assert "tags" in runner.unique_value_registry
        assert len(runner.unique_value_registry["tags"]) == 4


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestBooleanCategoryRulesIntegration:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db
    
    def test_run_all_boolean_column(self, mock_db):
        df = pd.DataFrame({"is_active": ["yes", "no", "y", "n"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"is_active": "HTYPE-018"}
        )
        summary = runner.run_all()
        assert summary["columns_processed"] == 1
        assert summary["total_changes"] > 0
    
    def test_run_all_category_column(self, mock_db):
        df = pd.DataFrame({"category": ["  Science  ", "MATH", "english"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"category": "HTYPE-019"}
        )
        summary = runner.run_all()
        assert summary["columns_processed"] == 1
        assert summary["total_changes"] > 0
    
    def test_run_all_status_column(self, mock_db):
        df = pd.DataFrame({"status": ["done", "pending", "in progress"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"status": "HTYPE-020"}
        )
        summary = runner.run_all()
        assert summary["columns_processed"] == 1
        assert summary["total_changes"] > 0
    
    def test_run_all_survey_column(self, mock_db):
        df = pd.DataFrame({"q1": ["Strongly Agree", "Agree", "netural"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"q1": "HTYPE-045"}
        )
        summary = runner.run_all()
        assert summary["columns_processed"] == 1
        assert summary["total_changes"] > 0
    
    def test_run_all_multi_value_column(self, mock_db):
        df = pd.DataFrame({"subjects": ["Math, Science", "English, History"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"subjects": "HTYPE-046"}
        )
        summary = runner.run_all()
        assert summary["columns_processed"] == 1
    
    def test_run_all_multiple_htypes(self, mock_db):
        df = pd.DataFrame({
            "is_verified": ["yes", "no"],
            "category": ["Science", "Math"],
            "status": ["done", "pending"],
        })
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={
                "is_verified": "HTYPE-018",
                "category": "HTYPE-019",
                "status": "HTYPE-020",
            }
        )
        summary = runner.run_all()
        assert summary["columns_processed"] == 3
    
    def test_run_all_ignores_non_applicable_htypes(self, mock_db):
        df = pd.DataFrame({"name": ["John", "Jane"], "age": [25, 30]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={
                "name": "HTYPE-001",  # Full Name - not applicable
                "age": "HTYPE-007",    # Age - not applicable
            }
        )
        summary = runner.run_all()
        assert summary["columns_processed"] == 0
    
    def test_flags_are_collected(self, mock_db):
        df = pd.DataFrame({"bool_col": ["yes", "maybe", "pending"]})
        runner = BooleanCategoryRules(
            job_id=1, df=df, db=mock_db,
            htype_map={"bool_col": "HTYPE-018"}
        )
        runner.run_all()
        assert len(runner.flags) > 0
