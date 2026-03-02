"""
Tests for Missing Value Decision Matrix (Session 12)

Covers all scenarios from the Formula Rulebook Section 52.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from app.services.missing_value_matrix import (
    MissingValueMatrix,
    Confidence,
    Action,
    MissingValueResult,
    MissingValueSummary,
    # Helper functions
    calculate_age_from_dob,
    concatenate_name_parts,
    calculate_amount,
    calculate_percentage,
    calculate_duration_days,
    interpolate_date,
    linear_interpolate,
    get_country_from_city,
    extract_city_from_address,
    get_fiscal_year,
    suggest_next_in_sequence,
    is_gender_refusal,
    calculate_gpa,
    # Constants
    GENDER_REFUSAL_PHRASES,
    UNIQUE_CITY_COUNTRY_MAP,
    FISCAL_YEAR_STARTS,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


def create_runner(df: pd.DataFrame, htype_map: dict, mock_db):
    """Helper to create MissingValueMatrix instance."""
    return MissingValueMatrix(
        job_id=1,
        df=df,
        db=mock_db,
        htype_map=htype_map,
    )


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestCalculateAgeFromDob:
    """Tests for calculate_age_from_dob helper."""
    
    def test_calculates_age_from_date_object(self):
        dob = date(1990, 5, 15)
        ref = date(2026, 3, 2)
        age = calculate_age_from_dob(dob, ref)
        assert age == 35
    
    def test_calculates_age_from_datetime(self):
        dob = datetime(1985, 12, 25)
        ref = date(2026, 3, 2)
        age = calculate_age_from_dob(dob, ref)
        assert age == 40
    
    def test_calculates_age_from_string_ymd(self):
        dob = "2000-01-01"
        ref = date(2026, 3, 2)
        age = calculate_age_from_dob(dob, ref)
        assert age == 26
    
    def test_calculates_age_from_string_dmy(self):
        dob = "15/06/1995"
        ref = date(2026, 3, 2)
        age = calculate_age_from_dob(dob, ref)
        assert age == 30
    
    def test_birthday_not_yet_occurred(self):
        dob = date(2000, 12, 25)
        ref = date(2026, 3, 2)
        age = calculate_age_from_dob(dob, ref)
        assert age == 25  # Birthday hasn't happened yet
    
    def test_null_dob_returns_none(self):
        assert calculate_age_from_dob(None) is None
        assert calculate_age_from_dob(np.nan) is None
    
    def test_invalid_age_range_returns_none(self):
        dob = date(1800, 1, 1)  # Would be 226 years old
        ref = date(2026, 3, 2)
        assert calculate_age_from_dob(dob, ref) is None


class TestConcatenateNameParts:
    """Tests for concatenate_name_parts helper."""
    
    def test_first_and_last(self):
        assert concatenate_name_parts("John", None, "Doe") == "John Doe"
    
    def test_first_middle_last(self):
        assert concatenate_name_parts("John", "Michael", "Doe") == "John Michael Doe"
    
    def test_only_first(self):
        assert concatenate_name_parts("John", None, None) == "John"
    
    def test_all_null_returns_none(self):
        assert concatenate_name_parts(None, None, None) is None
    
    def test_empty_strings_ignored(self):
        assert concatenate_name_parts("John", "", "Doe") == "John Doe"
    
    def test_trims_whitespace(self):
        assert concatenate_name_parts("  John  ", None, "  Doe  ") == "John Doe"


class TestCalculateAmount:
    """Tests for calculate_amount helper."""
    
    def test_integer_multiplication(self):
        assert calculate_amount(5, 10) == 50.00
    
    def test_float_multiplication(self):
        assert calculate_amount(2.5, 4.0) == 10.00
    
    def test_rounds_to_two_decimals(self):
        assert calculate_amount(3, 7.333) == 22.00
    
    def test_null_qty_returns_none(self):
        assert calculate_amount(None, 10) is None
    
    def test_null_price_returns_none(self):
        assert calculate_amount(5, None) is None
    
    def test_string_numbers_work(self):
        assert calculate_amount("3", "5.5") == 16.5


class TestCalculatePercentage:
    """Tests for calculate_percentage helper."""
    
    def test_basic_percentage(self):
        assert calculate_percentage(25, 100) == 25.0
    
    def test_rounds_to_two_decimals(self):
        assert calculate_percentage(1, 3) == 33.33
    
    def test_zero_denominator_returns_none(self):
        assert calculate_percentage(10, 0) is None
    
    def test_null_values_return_none(self):
        assert calculate_percentage(None, 100) is None
        assert calculate_percentage(50, None) is None
    
    def test_over_100_percent(self):
        assert calculate_percentage(150, 100) == 150.0


class TestCalculateDurationDays:
    """Tests for calculate_duration_days helper."""
    
    def test_date_objects(self):
        start = date(2026, 1, 1)
        end = date(2026, 1, 31)
        assert calculate_duration_days(start, end) == 30
    
    def test_datetime_objects(self):
        start = datetime(2026, 1, 1, 10, 0)
        end = datetime(2026, 1, 15, 15, 30)
        assert calculate_duration_days(start, end) == 14
    
    def test_string_dates(self):
        assert calculate_duration_days("2026-01-01", "2026-01-11") == 10
    
    def test_negative_duration(self):
        # End before start
        assert calculate_duration_days("2026-01-31", "2026-01-01") == -30
    
    def test_null_returns_none(self):
        assert calculate_duration_days(None, "2026-01-31") is None
        assert calculate_duration_days("2026-01-01", None) is None


class TestInterpolateDate:
    """Tests for interpolate_date helper."""
    
    def test_midpoint_calculation(self):
        before = date(2026, 1, 1)
        after = date(2026, 1, 11)
        result = interpolate_date(before, after)
        assert result == date(2026, 1, 6)
    
    def test_string_dates(self):
        result = interpolate_date("2026-01-01", "2026-01-21")
        assert result == date(2026, 1, 11)
    
    def test_null_returns_none(self):
        assert interpolate_date(None, "2026-01-31") is None
    
    def test_inverted_dates_returns_none(self):
        assert interpolate_date("2026-01-31", "2026-01-01") is None


class TestLinearInterpolate:
    """Tests for linear_interpolate helper."""
    
    def test_basic_average(self):
        assert linear_interpolate(10, 20) == 15.0
    
    def test_rounds_to_two_decimals(self):
        assert linear_interpolate(10, 15) == 12.5
    
    def test_null_returns_none(self):
        assert linear_interpolate(None, 20) is None
        assert linear_interpolate(10, None) is None
    
    def test_string_numbers_work(self):
        assert linear_interpolate("10", "20") == 15.0


class TestGetCountryFromCity:
    """Tests for get_country_from_city helper."""
    
    def test_tokyo_to_japan(self):
        assert get_country_from_city("Tokyo") == "Japan"
    
    def test_case_insensitive(self):
        assert get_country_from_city("PARIS") == "France"
        assert get_country_from_city("london") == "United Kingdom"
    
    def test_unknown_city_returns_none(self):
        assert get_country_from_city("Unknown City") is None
    
    def test_null_returns_none(self):
        assert get_country_from_city(None) is None


class TestExtractCityFromAddress:
    """Tests for extract_city_from_address helper."""
    
    def test_us_style_address(self):
        address = "123 Main St, Springfield, IL 62701"
        city = extract_city_from_address(address)
        assert city == "Springfield"
    
    def test_simple_address(self):
        address = "456 Oak Ave, Boston"
        city = extract_city_from_address(address)
        assert city == "Boston"
    
    def test_null_returns_none(self):
        assert extract_city_from_address(None) is None


class TestGetFiscalYear:
    """Tests for get_fiscal_year helper."""
    
    def test_calendar_year(self):
        # January start = calendar year
        assert get_fiscal_year("2026-03-15", fiscal_start_month=1) == 2026
    
    def test_april_fiscal_year_after_april(self):
        # April-March fiscal year, date in June
        assert get_fiscal_year("2026-06-15", fiscal_start_month=4) == 2026
    
    def test_april_fiscal_year_before_april(self):
        # April-March fiscal year, date in February
        assert get_fiscal_year("2026-02-15", fiscal_start_month=4) == 2025
    
    def test_null_returns_none(self):
        assert get_fiscal_year(None) is None


class TestSuggestNextInSequence:
    """Tests for suggest_next_in_sequence helper."""
    
    def test_numeric_arithmetic_sequence(self):
        values = [10, 20, 30, 40]
        assert suggest_next_in_sequence(values) == 50
    
    def test_string_id_sequence(self):
        values = ["ID001", "ID002", "ID003"]
        assert suggest_next_in_sequence(values) == "ID004"
    
    def test_string_with_leading_zeros(self):
        values = ["STU0001", "STU0002", "STU0003"]
        assert suggest_next_in_sequence(values) == "STU0004"
    
    def test_insufficient_values_returns_none(self):
        assert suggest_next_in_sequence([10]) is None
        assert suggest_next_in_sequence([]) is None
    
    def test_non_arithmetic_returns_none(self):
        values = [1, 3, 6, 10]  # Not constant step
        assert suggest_next_in_sequence(values) is None


class TestIsGenderRefusal:
    """Tests for is_gender_refusal helper."""
    
    def test_prefer_not_to_say(self):
        assert is_gender_refusal("Prefer not to say") is True
        assert is_gender_refusal("PREFER NOT TO ANSWER") is True
    
    def test_decline_variations(self):
        assert is_gender_refusal("decline to state") is True
        assert is_gender_refusal("Decline to Answer") is True
    
    def test_other_refusals(self):
        assert is_gender_refusal("Other") is True
        assert is_gender_refusal("Non-binary") is True
        assert is_gender_refusal("Private") is True
    
    def test_actual_genders_not_refusal(self):
        assert is_gender_refusal("Male") is False
        assert is_gender_refusal("Female") is False
    
    def test_null_returns_false(self):
        assert is_gender_refusal(None) is False


class TestCalculateGpa:
    """Tests for calculate_gpa helper."""
    
    def test_simple_average(self):
        scores = [80, 90, 85]
        assert calculate_gpa(scores) == 85.0
    
    def test_with_weights(self):
        scores = [80, 100]
        weights = [1.0, 3.0]
        result = calculate_gpa(scores, weights)
        assert result == 95.0  # (80*1 + 100*3) / 4
    
    def test_ignores_null_scores(self):
        scores = [80, None, 90]
        assert calculate_gpa(scores) == 85.0
    
    def test_all_null_returns_none(self):
        assert calculate_gpa([None, None]) is None


# ============================================================================
# SCENARIO HANDLER TESTS
# ============================================================================

class TestAgeFromDob:
    """Tests for handle_age_null_dob_present."""
    
    def test_auto_fills_age(self, mock_db):
        df = pd.DataFrame({
            "age": [25, None, 30],
            "dob": ["2001-01-01", "1990-05-15", "1996-01-01"],
        })
        htype_map = {"age": "HTYPE-004", "dob": "HTYPE-013"}
        runner = create_runner(df, htype_map, mock_db)
        
        result = runner.handle_age_null_dob_present(1, "age", "dob")
        
        assert result is not None
        assert result.can_predict is True
        assert result.confidence == Confidence.HIGH
        assert result.action == Action.AUTO_FILL
        assert result.was_applied is True
        assert runner.df.at[1, "age"] == 35  # Born 1990, ref 2026


class TestFullNameFromParts:
    """Tests for handle_fullname_null_parts_present."""
    
    def test_concatenates_name_parts(self, mock_db):
        df = pd.DataFrame({
            "full_name": [None, "Jane Doe"],
            "first_name": ["John", "Jane"],
            "last_name": ["Smith", "Doe"],
        })
        htype_map = {
            "full_name": "HTYPE-001",
            "first_name": "HTYPE-002",
            "last_name": "HTYPE-003",
        }
        runner = create_runner(df, htype_map, mock_db)
        
        result = runner.handle_fullname_null_parts_present(0, "full_name")
        
        assert result is not None
        assert result.predicted_value == "John Smith"
        assert runner.df.at[0, "full_name"] == "John Smith"


class TestAmountFromQtyPrice:
    """Tests for handle_amount_null_qty_price_present."""
    
    def test_calculates_amount(self, mock_db):
        df = pd.DataFrame({
            "amount": [100, None, 150],
            "qty": [10, 5, 15],
            "price": [10, 20, 10],
        })
        runner = create_runner(df, {}, mock_db)
        
        result = runner.handle_amount_null_qty_price_present(1, "amount", "qty", "price")
        
        assert result is not None
        assert result.predicted_value == 100.0  # 5 * 20
        assert runner.df.at[1, "amount"] == 100.0


class TestDurationCalculation:
    """Tests for handle_duration_null."""
    
    def test_calculates_duration(self, mock_db):
        df = pd.DataFrame({
            "duration_days": [None],
            "start_date": ["2026-01-01"],
            "end_date": ["2026-01-31"],
        })
        runner = create_runner(df, {}, mock_db)
        
        result = runner.handle_duration_null(0, "duration_days", "start_date", "end_date")
        
        assert result is not None
        assert result.predicted_value == 30
        assert runner.df.at[0, "duration_days"] == 30


class TestCountryFromCity:
    """Tests for handle_country_null_city_present."""
    
    def test_infers_country_from_unique_city(self, mock_db):
        df = pd.DataFrame({
            "country": [None],
            "city": ["Tokyo"],
        })
        htype_map = {"country": "HTYPE-009", "city": "HTYPE-008"}
        runner = create_runner(df, htype_map, mock_db)
        
        result = runner.handle_country_null_city_present(0, "country", "city")
        
        assert result is not None
        assert result.predicted_value == "Japan"
        assert runner.df.at[0, "country"] == "Japan"


class TestDateInterpolation:
    """Tests for handle_date_interpolation."""
    
    def test_suggests_interpolated_date(self, mock_db):
        df = pd.DataFrame({
            "date": ["2026-01-01", None, "2026-01-21"],
        })
        runner = create_runner(df, {"date": "HTYPE-013"}, mock_db)
        
        result = runner.handle_date_interpolation(1, "date")
        
        assert result is not None
        assert result.confidence == Confidence.MEDIUM
        assert result.action == Action.SUGGEST
        assert result.was_applied is False  # Needs user confirmation
        assert len(runner.flags) == 1


class TestQuantityInterpolation:
    """Tests for handle_quantity_interpolation."""
    
    def test_suggests_interpolated_quantity(self, mock_db):
        df = pd.DataFrame({
            "quantity": [100, None, 200],
        })
        runner = create_runner(df, {"quantity": "HTYPE-024"}, mock_db)
        
        result = runner.handle_quantity_interpolation(1, "quantity")
        
        assert result is not None
        assert result.predicted_value == 150.0
        assert result.action == Action.SUGGEST


class TestFiscalYearDerivation:
    """Tests for handle_fiscal_year_null."""
    
    def test_derives_fiscal_year(self, mock_db):
        df = pd.DataFrame({
            "fiscal_year": [None],
            "transaction_date": ["2026-06-15"],
        })
        runner = create_runner(df, {"transaction_date": "HTYPE-013"}, mock_db)
        runner.date_columns = ["transaction_date"]
        
        result = runner.handle_fiscal_year_null(0, "fiscal_year", "transaction_date", fiscal_start=4)
        
        assert result is not None
        assert result.predicted_value == 2026  # After April, so FY2026


class TestSequentialIdSuggestion:
    """Tests for handle_sequential_id_null."""
    
    def test_suggests_next_id(self, mock_db):
        df = pd.DataFrame({
            "student_id": ["STU001", "STU002", "STU003", None],
        })
        runner = create_runner(df, {"student_id": "HTYPE-005"}, mock_db)
        
        result = runner.handle_sequential_id_null(3, "student_id")
        
        assert result is not None
        assert result.predicted_value == "STU004"
        assert result.action == Action.SUGGEST


class TestGenderRefusalHandling:
    """Tests for handle_gender_refusal."""
    
    def test_maps_refusal_to_standard(self, mock_db):
        df = pd.DataFrame({
            "gender": ["Male", "prefer not to say", "Female"],
        })
        runner = create_runner(df, {"gender": "HTYPE-012"}, mock_db)
        
        result = runner.handle_gender_refusal(1, "gender")
        
        assert result is not None
        assert result.predicted_value == "Prefer Not to Say"
        assert runner.df.at[1, "gender"] == "Prefer Not to Say"


class TestPromptRequired:
    """Tests for handle_prompt_required."""
    
    def test_creates_prompt_flag(self, mock_db):
        df = pd.DataFrame({"email": [None]})
        runner = create_runner(df, {}, mock_db)
        
        result = runner.handle_prompt_required(0, "email", "EMAIL_NULL")
        
        assert result.can_predict is False
        assert result.confidence == Confidence.NONE
        assert result.action == Action.PROMPT
        assert len(runner.flags) == 1


# ============================================================================
# ORCHESTRATION TESTS
# ============================================================================

class TestAnalyzeColumn:
    """Tests for analyze_column method."""
    
    def test_returns_summary_for_column_with_missing(self, mock_db):
        df = pd.DataFrame({
            "age": [25, None, None, 30],
            "dob": ["2001-01-01", "1990-05-15", "1985-12-25", "1996-01-01"],
        })
        htype_map = {"age": "HTYPE-004", "dob": "HTYPE-013"}
        runner = create_runner(df, htype_map, mock_db)
        
        summary = runner.analyze_column("age")
        
        assert summary.total_missing == 2
        assert summary.auto_filled == 2  # Both derived from DOB
    
    def test_empty_column_returns_zero_summary(self, mock_db):
        df = pd.DataFrame({"name": ["John", "Jane", "Bob"]})
        runner = create_runner(df, {}, mock_db)
        
        summary = runner.analyze_column("name")
        
        assert summary.total_missing == 0


class TestAnalyzeGenderRefusals:
    """Tests for analyze_gender_refusals method."""
    
    def test_normalizes_all_refusals(self, mock_db):
        df = pd.DataFrame({
            "gender": ["Male", "prefer not to say", "decline to answer", "Female"],
        })
        htype_map = {"gender": "HTYPE-012"}
        runner = create_runner(df, htype_map, mock_db)
        
        runner.analyze_gender_refusals("gender")
        
        assert runner.df.at[1, "gender"] == "Prefer Not to Say"
        assert runner.df.at[2, "gender"] == "Prefer Not to Say"


class TestRunAll:
    """Tests for run_all orchestration."""
    
    def test_returns_comprehensive_summary(self, mock_db):
        df = pd.DataFrame({
            "age": [25, None],
            "dob": ["2001-01-01", "1990-05-15"],
            "email": ["a@b.com", None],
        })
        htype_map = {"age": "HTYPE-004", "dob": "HTYPE-013"}
        runner = create_runner(df, htype_map, mock_db)
        
        summary = runner.run_all()
        
        assert "total_missing_values" in summary
        assert "auto_filled" in summary
        assert "suggested_for_review" in summary
        assert "prompts_required" in summary
        assert "column_summaries" in summary
    
    def test_processes_all_columns(self, mock_db):
        df = pd.DataFrame({
            "col1": [None, "value"],
            "col2": ["value", None],
            "col3": [None, None],
        })
        runner = create_runner(df, {}, mock_db)
        
        summary = runner.run_all()
        
        assert summary["total_missing_values"] == 4


class TestFlagsGeneration:
    """Tests for flags generation."""
    
    def test_flags_contain_required_fields(self, mock_db):
        df = pd.DataFrame({"email": [None]})
        runner = create_runner(df, {}, mock_db)
        
        runner.run_all()
        
        assert len(runner.flags) >= 1
        flag = runner.flags[0]
        assert "row" in flag
        assert "column" in flag
        assert "scenario" in flag
        assert "message" in flag
        assert "confidence" in flag
        assert "requires_confirmation" in flag


class TestResultsTracking:
    """Tests for results tracking."""
    
    def test_tracks_all_results(self, mock_db):
        df = pd.DataFrame({
            "age": [None, None],
            "dob": ["1990-01-01", "1985-06-15"],
        })
        htype_map = {"age": "HTYPE-004", "dob": "HTYPE-013"}
        runner = create_runner(df, htype_map, mock_db)
        
        runner.run_all()
        
        # Should have results for each missing value
        age_results = [r for r in runner.results if r.column == "age"]
        assert len(age_results) == 2


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_dataframe(self, mock_db):
        df = pd.DataFrame({"col": []})
        runner = create_runner(df, {}, mock_db)
        
        summary = runner.run_all()
        
        assert summary["total_missing_values"] == 0
    
    def test_all_null_column(self, mock_db):
        df = pd.DataFrame({"col": [None, None, None]})
        runner = create_runner(df, {}, mock_db)
        
        summary = runner.run_all()
        
        assert summary["total_missing_values"] == 3
        assert summary["prompts_required"] == 3
    
    def test_no_missing_values(self, mock_db):
        df = pd.DataFrame({
            "name": ["John", "Jane"],
            "age": [25, 30],
        })
        runner = create_runner(df, {}, mock_db)
        
        summary = runner.run_all()
        
        assert summary["total_missing_values"] == 0
        assert summary["auto_filled"] == 0
    
    def test_mixed_scenarios_same_column(self, mock_db):
        # Age with some derivable, some not
        df = pd.DataFrame({
            "age": [None, None, None],
            "dob": ["1990-01-01", None, "1985-06-15"],
        })
        htype_map = {"age": "HTYPE-004", "dob": "HTYPE-013"}
        runner = create_runner(df, htype_map, mock_db)
        
        summary = runner.run_all()
        
        # First and third have DOB, second doesn't
        # auto_filled should be 2 (from DOB)
        # prompted should be 1 (no DOB available)
        age_summary = summary["column_summaries"].get("age", {})
        assert age_summary.get("auto_filled", 0) + age_summary.get("prompted", 0) == 3
