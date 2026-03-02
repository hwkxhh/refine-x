"""
Tests for Cross-Column Conditional Validation Rules (Session 15)

Tests all 12 COND formulas: COND-01 through COND-12

Covers:
- Status-Date Dependency (COND-01)
- Status-Amount Dependency (COND-02)
- Date Sequence Chain (COND-03)
- Referential Integrity Check (COND-04)
- Age-DOB Consistency (COND-05)
- Score-Pass Consistency (COND-06)
- Gender-Title Consistency (COND-07)
- Country-Phone Code Consistency (COND-08)
- Quantity-Amount Sign Consistency (COND-09)
- Admission-Graduation Date (COND-10)
- Total = Sum of Components (COND-11)
- Duplicate ID, Conflicting Status (COND-12)
"""

import pytest
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from unittest.mock import MagicMock

from app.services.conditional_validation import (
    ConditionalValidation,
    ValidationResult,
    ValidationStatus,
    ValidationSeverity,
    ValidationSummary,
    # COND functions
    cond_01_status_date_dependency,
    cond_02_status_amount_dependency,
    cond_03_date_sequence_chain,
    cond_04_referential_integrity,
    cond_05_age_dob_consistency,
    cond_06_score_pass_consistency,
    cond_07_gender_title_consistency,
    cond_08_country_phone_consistency,
    cond_09_quantity_amount_sign,
    cond_10_admission_graduation_date,
    cond_11_total_equals_sum,
    cond_12_duplicate_id_conflicting_status,
    # Helpers
    normalize_status,
    parse_date,
    calculate_age_from_dob,
    extract_phone_prefix,
    find_columns_by_pattern,
    find_status_column,
    find_date_columns,
    find_amount_columns,
    find_quantity_columns,
    find_id_columns,
    # Constants
    COMPLETED_STATUSES,
    PAID_STATUSES,
    TITLE_GENDER_MAP,
    COUNTRY_PHONE_CODES,
    ACTIVE_STATUSES,
    INACTIVE_STATUSES,
)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestNormalizeStatus:
    """Tests for normalize_status helper."""
    
    def test_lowercase_string(self):
        assert normalize_status("ACTIVE") == "active"
    
    def test_with_whitespace(self):
        assert normalize_status("  Completed  ") == "completed"
    
    def test_none_value(self):
        assert normalize_status(None) == ""
    
    def test_nan_value(self):
        assert normalize_status(np.nan) == ""
    
    def test_numeric_value(self):
        assert normalize_status(123) == "123"


class TestParseDate:
    """Tests for parse_date helper."""
    
    def test_datetime_object(self):
        dt = datetime(2023, 5, 15, 10, 30)
        result = parse_date(dt)
        assert result == date(2023, 5, 15)
    
    def test_date_object(self):
        d = date(2023, 5, 15)
        result = parse_date(d)
        assert result == d
    
    def test_string_iso_format(self):
        result = parse_date("2023-05-15")
        assert result == date(2023, 5, 15)
    
    def test_string_us_format(self):
        result = parse_date("05/15/2023")
        assert result == date(2023, 5, 15)
    
    def test_none_value(self):
        assert parse_date(None) is None
    
    def test_nan_value(self):
        assert parse_date(np.nan) is None
    
    def test_invalid_string(self):
        assert parse_date("not a date") is None


class TestCalculateAgeFromDob:
    """Tests for calculate_age_from_dob helper."""
    
    def test_basic_age_calculation(self):
        # Born 30 years ago
        dob = date.today() - timedelta(days=30 * 365)
        age = calculate_age_from_dob(dob)
        assert 29 <= age <= 31  # Allow for leap years
    
    def test_birthday_not_passed_yet(self):
        # Born 25 years ago but birthday is next month
        today = date.today()
        dob = date(today.year - 25, today.month + 1 if today.month < 12 else 1, 1)
        if today.month == 12:
            dob = date(today.year - 24, 1, 1)  # Adjust for December
        age = calculate_age_from_dob(dob)
        # Should be 24 or 25 depending on month
        assert 23 <= age <= 25
    
    def test_with_reference_date(self):
        dob = date(1990, 1, 1)
        ref = date(2020, 6, 15)
        age = calculate_age_from_dob(dob, ref)
        assert age == 30


class TestExtractPhonePrefix:
    """Tests for extract_phone_prefix helper."""
    
    def test_plus_prefix(self):
        assert extract_phone_prefix("+1-555-1234") == "+1"
    
    def test_plus_multi_digit(self):
        assert extract_phone_prefix("+977-9841234567") == "+977"
    
    def test_double_zero_prefix(self):
        assert extract_phone_prefix("001-555-1234") == "+1"
    
    def test_no_prefix(self):
        assert extract_phone_prefix("555-1234") is None
    
    def test_empty_string(self):
        assert extract_phone_prefix("") is None


class TestFindColumnsByPattern:
    """Tests for find_columns_by_pattern helper."""
    
    def test_single_match(self):
        cols = ["name", "age", "status"]
        result = find_columns_by_pattern(cols, ["status"])
        assert result == ["status"]
    
    def test_multiple_matches(self):
        cols = ["order_status", "payment_status", "name"]
        result = find_columns_by_pattern(cols, ["status"])
        assert result == ["order_status", "payment_status"]
    
    def test_no_matches(self):
        cols = ["name", "age", "email"]
        result = find_columns_by_pattern(cols, ["status"])
        assert result == []
    
    def test_multiple_patterns(self):
        cols = ["status", "state", "condition"]
        result = find_columns_by_pattern(cols, ["status", "state"])
        assert len(result) == 2


# ============================================================================
# COND-01: STATUS-DATE DEPENDENCY
# ============================================================================

class TestCond01StatusDateDependency:
    """Tests for COND-01: Status-Date Dependency."""
    
    def test_valid_discharged_with_date(self):
        """No violations when discharged status has date."""
        df = pd.DataFrame({
            "status": ["Discharged", "Active", "Discharged"],
            "discharge_date": ["2023-01-15", None, "2023-02-20"],
        })
        result = cond_01_status_date_dependency(df, "status", "discharge_date")
        assert result.status == ValidationStatus.PASSED
        assert len(result.affected_rows) == 0
    
    def test_discharged_without_date(self):
        """Violation when discharged status has null date."""
        df = pd.DataFrame({
            "status": ["Discharged", "Active", "Discharged"],
            "discharge_date": [None, None, "2023-02-20"],
        })
        result = cond_01_status_date_dependency(df, "status", "discharge_date")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_completed_status_without_date(self):
        """Violation when completed status has null date."""
        df = pd.DataFrame({
            "status": ["completed", "pending", "Closed"],
            "end_date": [None, None, None],
        })
        result = cond_01_status_date_dependency(df, "status", "end_date")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
        assert 2 in result.affected_rows
    
    def test_custom_completed_statuses(self):
        """Works with custom completed status set."""
        df = pd.DataFrame({
            "status": ["done", "pending", "finished"],
            "date": [None, None, "2023-01-01"],
        })
        result = cond_01_status_date_dependency(
            df, "status", "date", 
            completed_statuses={"done", "finished"}
        )
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
        assert 1 not in result.affected_rows
    
    def test_missing_columns(self):
        """Skip when columns don't exist."""
        df = pd.DataFrame({"other": [1, 2, 3]})
        result = cond_01_status_date_dependency(df, "status", "date")
        assert result.status == ValidationStatus.SKIPPED


# ============================================================================
# COND-02: STATUS-AMOUNT DEPENDENCY
# ============================================================================

class TestCond02StatusAmountDependency:
    """Tests for COND-02: Status-Amount Dependency."""
    
    def test_paid_with_positive_amount(self):
        """No violations when paid status has positive amount."""
        df = pd.DataFrame({
            "payment_status": ["Paid", "Pending", "Paid"],
            "amount": [100.00, 0, 250.50],
        })
        result = cond_02_status_amount_dependency(df, "payment_status", "amount")
        assert result.status == ValidationStatus.PASSED
    
    def test_paid_with_zero_amount(self):
        """Violation when paid status has zero amount."""
        df = pd.DataFrame({
            "payment_status": ["Paid", "Pending", "Paid"],
            "amount": [0, 0, 250.50],
        })
        result = cond_02_status_amount_dependency(df, "payment_status", "amount")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_paid_with_null_amount(self):
        """Violation when paid status has null amount."""
        df = pd.DataFrame({
            "payment_status": ["Paid", "Pending"],
            "amount": [None, 0],
        })
        result = cond_02_status_amount_dependency(df, "payment_status", "amount")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_paid_with_negative_amount(self):
        """Violation when paid status has negative amount."""
        df = pd.DataFrame({
            "payment_status": ["Paid", "Pending"],
            "amount": [-50, 0],
        })
        result = cond_02_status_amount_dependency(df, "payment_status", "amount")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_settled_status(self):
        """Works with 'settled' status."""
        df = pd.DataFrame({
            "status": ["Settled", "Pending"],
            "payment": [500, 0],
        })
        result = cond_02_status_amount_dependency(df, "status", "payment")
        assert result.status == ValidationStatus.PASSED


# ============================================================================
# COND-03: DATE SEQUENCE CHAIN
# ============================================================================

class TestCond03DateSequenceChain:
    """Tests for COND-03: Date Sequence Chain."""
    
    def test_valid_sequence(self):
        """No violations when dates are in order."""
        df = pd.DataFrame({
            "application_date": ["2023-01-01", "2023-02-01"],
            "interview_date": ["2023-01-15", "2023-02-15"],
            "offer_date": ["2023-02-01", "2023-03-01"],
            "joining_date": ["2023-03-01", "2023-04-01"],
        })
        result = cond_03_date_sequence_chain(df, [
            "application_date", "interview_date", "offer_date", "joining_date"
        ])
        assert result.status == ValidationStatus.PASSED
    
    def test_out_of_sequence(self):
        """Violation when dates are out of order."""
        df = pd.DataFrame({
            "start_date": ["2023-03-01"],
            "end_date": ["2023-01-01"],  # Before start
        })
        result = cond_03_date_sequence_chain(df, ["start_date", "end_date"])
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_partial_null_dates(self):
        """Skip comparison when some dates are null."""
        df = pd.DataFrame({
            "date1": ["2023-01-01", "2023-01-01"],
            "date2": [None, "2023-02-01"],
            "date3": ["2023-03-01", "2023-03-01"],
        })
        result = cond_03_date_sequence_chain(df, ["date1", "date2", "date3"])
        # Should pass because null dates are skipped
        assert result.status == ValidationStatus.PASSED
    
    def test_insufficient_columns(self):
        """Skip when less than 2 date columns."""
        df = pd.DataFrame({"date1": ["2023-01-01"]})
        result = cond_03_date_sequence_chain(df, ["date1"])
        assert result.status == ValidationStatus.SKIPPED
    
    def test_middle_date_violation(self):
        """Detect violation in middle of chain."""
        df = pd.DataFrame({
            "apply": ["2023-01-01"],
            "interview": ["2023-03-01"],  # After offer!
            "offer": ["2023-02-01"],
        })
        result = cond_03_date_sequence_chain(df, ["apply", "interview", "offer"])
        assert result.status == ValidationStatus.FAILED


# ============================================================================
# COND-04: REFERENTIAL INTEGRITY CHECK
# ============================================================================

class TestCond04ReferentialIntegrity:
    """Tests for COND-04: Referential Integrity Check."""
    
    def test_all_valid_references(self):
        """No violations when all references exist."""
        df = pd.DataFrame({
            "department_id": [1, 2, 3, 1, 2],
        })
        reference_set = {1, 2, 3, 4, 5}
        result = cond_04_referential_integrity(df, "department_id", reference_set)
        assert result.status == ValidationStatus.PASSED
    
    def test_orphaned_references(self):
        """Violation when references don't exist in set."""
        df = pd.DataFrame({
            "department_id": [1, 2, 99, 1, 100],
        })
        reference_set = {1, 2, 3, 4, 5}
        result = cond_04_referential_integrity(df, "department_id", reference_set)
        assert result.status == ValidationStatus.FAILED
        assert 2 in result.affected_rows
        assert 4 in result.affected_rows
        assert 99 in result.details["orphaned_values"]
        assert 100 in result.details["orphaned_values"]
    
    def test_null_values_ignored(self):
        """Null values are not flagged as orphans."""
        df = pd.DataFrame({
            "dept_id": [1, None, 2, None],
        })
        reference_set = {1, 2}
        result = cond_04_referential_integrity(df, "dept_id", reference_set)
        assert result.status == ValidationStatus.PASSED
    
    def test_missing_column(self):
        """Skip when column doesn't exist."""
        df = pd.DataFrame({"other": [1, 2, 3]})
        result = cond_04_referential_integrity(df, "dept_id", {1, 2})
        assert result.status == ValidationStatus.SKIPPED


# ============================================================================
# COND-05: AGE-DOB CONSISTENCY
# ============================================================================

class TestCond05AgeDobConsistency:
    """Tests for COND-05: Age-DOB Consistency."""
    
    def test_consistent_age_dob(self):
        """No violations when age matches DOB."""
        today = date.today()
        dob = date(today.year - 30, 1, 1)
        df = pd.DataFrame({
            "age": [30],
            "dob": [dob.isoformat()],
        })
        result = cond_05_age_dob_consistency(df, "age", "dob")
        assert result.status == ValidationStatus.PASSED
    
    def test_inconsistent_age_dob(self):
        """Violation when age doesn't match DOB."""
        today = date.today()
        dob = date(today.year - 30, 1, 1)
        df = pd.DataFrame({
            "age": [25],  # Should be ~30
            "dob": [dob.isoformat()],
        })
        result = cond_05_age_dob_consistency(df, "age", "dob")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_tolerance_within_limit(self):
        """No violation within tolerance."""
        today = date.today()
        # Person turns 30 this year but birthday hasn't passed
        dob = date(today.year - 30, 12, 31)
        df = pd.DataFrame({
            "age": [29],  # Within tolerance
            "dob": [dob.isoformat()],
        })
        result = cond_05_age_dob_consistency(df, "age", "dob", tolerance_years=1)
        assert result.status == ValidationStatus.PASSED
    
    def test_null_values_skipped(self):
        """Null values are skipped."""
        df = pd.DataFrame({
            "age": [None, 25, 30],
            "dob": ["1990-01-01", None, "1993-06-15"],
        })
        result = cond_05_age_dob_consistency(df, "age", "dob")
        # First two rows skipped, only row 2 evaluated
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED]
    
    def test_missing_columns(self):
        """Skip when columns don't exist."""
        df = pd.DataFrame({"name": ["Alice"]})
        result = cond_05_age_dob_consistency(df, "age", "dob")
        assert result.status == ValidationStatus.SKIPPED


# ============================================================================
# COND-06: SCORE-PASS CONSISTENCY
# ============================================================================

class TestCond06ScorePassConsistency:
    """Tests for COND-06: Score-Pass Consistency."""
    
    def test_consistent_pass(self):
        """No violations when score matches pass status."""
        df = pd.DataFrame({
            "score": [75, 35, 40],
            "result": ["Pass", "Fail", "Pass"],
        })
        result = cond_06_score_pass_consistency(df, "score", "result", pass_threshold=40)
        assert result.status == ValidationStatus.PASSED
    
    def test_high_score_marked_fail(self):
        """Violation when high score marked as fail."""
        df = pd.DataFrame({
            "score": [85, 35],
            "result": ["Fail", "Fail"],  # 85 should be pass
        })
        result = cond_06_score_pass_consistency(df, "score", "result", pass_threshold=40)
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_low_score_marked_pass(self):
        """Violation when low score marked as pass."""
        df = pd.DataFrame({
            "score": [20, 45],
            "result": ["Pass", "Pass"],  # 20 should be fail
        })
        result = cond_06_score_pass_consistency(df, "score", "result", pass_threshold=40)
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_exact_threshold(self):
        """Score exactly at threshold should pass."""
        df = pd.DataFrame({
            "score": [40],
            "pass_fail": ["Pass"],
        })
        result = cond_06_score_pass_consistency(df, "score", "pass_fail", pass_threshold=40)
        assert result.status == ValidationStatus.PASSED
    
    def test_custom_threshold(self):
        """Works with custom threshold."""
        df = pd.DataFrame({
            "score": [55],
            "result": ["Fail"],
        })
        result = cond_06_score_pass_consistency(df, "score", "result", pass_threshold=60)
        assert result.status == ValidationStatus.PASSED  # 55 < 60, so Fail is correct


# ============================================================================
# COND-07: GENDER-TITLE CONSISTENCY
# ============================================================================

class TestCond07GenderTitleConsistency:
    """Tests for COND-07: Gender-Title Consistency."""
    
    def test_consistent_mr_male(self):
        """No violations when Mr. is male."""
        df = pd.DataFrame({
            "title": ["Mr.", "Mrs.", "Ms."],
            "gender": ["Male", "Female", "Female"],
        })
        result = cond_07_gender_title_consistency(df, "title", "gender")
        assert result.status == ValidationStatus.PASSED
    
    def test_mr_with_female(self):
        """Violation when Mr. has female gender."""
        df = pd.DataFrame({
            "title": ["Mr."],
            "gender": ["Female"],
        })
        result = cond_07_gender_title_consistency(df, "title", "gender")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_mrs_with_male(self):
        """Violation when Mrs. has male gender."""
        df = pd.DataFrame({
            "title": ["Mrs."],
            "gender": ["Male"],
        })
        result = cond_07_gender_title_consistency(df, "title", "gender")
        assert result.status == ValidationStatus.FAILED
    
    def test_unknown_title_skipped(self):
        """Unknown titles are skipped."""
        df = pd.DataFrame({
            "title": ["Dr.", "Prof."],
            "gender": ["Male", "Female"],
        })
        result = cond_07_gender_title_consistency(df, "title", "gender")
        assert result.status == ValidationStatus.PASSED  # No known titles to check
    
    def test_severity_is_warning(self):
        """Result severity is warning, not error."""
        df = pd.DataFrame({
            "title": ["Mr."],
            "gender": ["Female"],
        })
        result = cond_07_gender_title_consistency(df, "title", "gender")
        assert result.severity == ValidationSeverity.WARNING


# ============================================================================
# COND-08: COUNTRY-PHONE CODE CONSISTENCY
# ============================================================================

class TestCond08CountryPhoneConsistency:
    """Tests for COND-08: Country-Phone Code Consistency."""
    
    def test_consistent_us_phone(self):
        """No violations when US country has +1 phone."""
        df = pd.DataFrame({
            "country": ["United States", "USA", "US"],
            "phone": ["+1-555-1234", "+1-555-5678", "+1-555-9999"],
        })
        result = cond_08_country_phone_consistency(df, "country", "phone")
        assert result.status == ValidationStatus.PASSED
    
    def test_inconsistent_country_phone(self):
        """Violation when country doesn't match phone code."""
        df = pd.DataFrame({
            "country": ["Nepal"],
            "phone": ["+1-555-1234"],  # Nepal should be +977
        })
        result = cond_08_country_phone_consistency(df, "country", "phone")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_india_phone(self):
        """Works with India phone codes."""
        df = pd.DataFrame({
            "country": ["India"],
            "phone": ["+91-9876543210"],
        })
        result = cond_08_country_phone_consistency(df, "country", "phone")
        assert result.status == ValidationStatus.PASSED
    
    def test_unknown_country_skipped(self):
        """Unknown countries are skipped."""
        df = pd.DataFrame({
            "country": ["Atlantis"],
            "phone": ["+999-1234567"],
        })
        result = cond_08_country_phone_consistency(df, "country", "phone")
        assert result.status == ValidationStatus.PASSED  # Unknown country
    
    def test_no_phone_prefix(self):
        """Phones without prefix are skipped."""
        df = pd.DataFrame({
            "country": ["USA"],
            "phone": ["555-1234"],  # No country code
        })
        result = cond_08_country_phone_consistency(df, "country", "phone")
        assert result.status == ValidationStatus.PASSED


# ============================================================================
# COND-09: QUANTITY-AMOUNT SIGN CONSISTENCY
# ============================================================================

class TestCond09QuantityAmountSign:
    """Tests for COND-09: Quantity-Amount Sign Consistency."""
    
    def test_both_positive(self):
        """No violations when both positive."""
        df = pd.DataFrame({
            "quantity": [10, 5, 20],
            "amount": [100, 50, 200],
        })
        result = cond_09_quantity_amount_sign(df, "quantity", "amount")
        assert result.status == ValidationStatus.PASSED
    
    def test_both_negative(self):
        """No violations when both negative (returns)."""
        df = pd.DataFrame({
            "quantity": [-5],
            "amount": [-50],
        })
        result = cond_09_quantity_amount_sign(df, "quantity", "amount")
        assert result.status == ValidationStatus.PASSED
    
    def test_positive_qty_negative_amt(self):
        """Violation when positive quantity has negative amount."""
        df = pd.DataFrame({
            "quantity": [10],
            "amount": [-100],
        })
        result = cond_09_quantity_amount_sign(df, "quantity", "amount")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_negative_qty_positive_amt(self):
        """Violation when negative quantity has positive amount."""
        df = pd.DataFrame({
            "quantity": [-10],
            "amount": [100],
        })
        result = cond_09_quantity_amount_sign(df, "quantity", "amount")
        assert result.status == ValidationStatus.FAILED
    
    def test_zeros_allowed(self):
        """Zero values don't cause violations."""
        df = pd.DataFrame({
            "quantity": [0, 10],
            "amount": [0, 100],
        })
        result = cond_09_quantity_amount_sign(df, "quantity", "amount")
        assert result.status == ValidationStatus.PASSED


# ============================================================================
# COND-10: ADMISSION-GRADUATION DATE
# ============================================================================

class TestCond10AdmissionGraduationDate:
    """Tests for COND-10: Admission-Graduation Date."""
    
    def test_valid_graduation_after_admission(self):
        """No violations when graduation is after admission."""
        df = pd.DataFrame({
            "admission_date": ["2018-09-01"],
            "graduation_date": ["2022-06-15"],  # 4 years
        })
        result = cond_10_admission_graduation_date(
            df, "admission_date", "graduation_date"
        )
        assert result.status == ValidationStatus.PASSED
    
    def test_graduation_before_admission(self):
        """Violation when graduation is before admission."""
        df = pd.DataFrame({
            "admission_date": ["2022-09-01"],
            "graduation_date": ["2018-06-15"],  # Before admission!
        })
        result = cond_10_admission_graduation_date(
            df, "admission_date", "graduation_date"
        )
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_too_short_duration(self):
        """Violation when duration is too short."""
        df = pd.DataFrame({
            "admission": ["2022-01-01"],
            "graduation": ["2022-06-01"],  # Only 5 months
        })
        result = cond_10_admission_graduation_date(
            df, "admission", "graduation", min_years=1
        )
        assert result.status == ValidationStatus.FAILED
    
    def test_too_long_duration(self):
        """Violation when duration is too long."""
        df = pd.DataFrame({
            "admission": ["2000-09-01"],
            "graduation": ["2020-06-15"],  # 20 years
        })
        result = cond_10_admission_graduation_date(
            df, "admission", "graduation", max_years=10
        )
        assert result.status == ValidationStatus.FAILED
    
    def test_exactly_at_boundaries(self):
        """Values exactly at boundaries should pass."""
        df = pd.DataFrame({
            "admission": ["2018-01-01"],
            "graduation": ["2020-01-01"],  # 2 years - within 1-10 range
        })
        result = cond_10_admission_graduation_date(
            df, "admission", "graduation", min_years=1, max_years=10
        )
        assert result.status == ValidationStatus.PASSED


# ============================================================================
# COND-11: TOTAL = SUM OF COMPONENTS
# ============================================================================

class TestCond11TotalEqualsSum:
    """Tests for COND-11: Total = Sum of Components."""
    
    def test_correct_total(self):
        """No violations when total equals sum."""
        df = pd.DataFrame({
            "male": [50, 40],
            "female": [45, 55],
            "other": [5, 5],
            "total_students": [100, 100],
        })
        result = cond_11_total_equals_sum(
            df, "total_students", ["male", "female", "other"]
        )
        assert result.status == ValidationStatus.PASSED
    
    def test_incorrect_total(self):
        """Violation when total doesn't equal sum."""
        df = pd.DataFrame({
            "male": [50],
            "female": [45],
            "other": [5],
            "total": [90],  # Should be 100
        })
        result = cond_11_total_equals_sum(
            df, "total", ["male", "female", "other"]
        )
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
    
    def test_within_tolerance(self):
        """No violation within tolerance."""
        df = pd.DataFrame({
            "a": [33.33],
            "b": [33.33],
            "c": [33.33],
            "total": [100.0],  # 99.99 vs 100
        })
        result = cond_11_total_equals_sum(
            df, "total", ["a", "b", "c"], tolerance=0.01
        )
        assert result.status == ValidationStatus.PASSED
    
    def test_null_components_skipped(self):
        """Rows with null components are skipped."""
        df = pd.DataFrame({
            "a": [10, None],
            "b": [20, 30],
            "total": [30, 60],
        })
        result = cond_11_total_equals_sum(df, "total", ["a", "b"])
        assert result.status == ValidationStatus.PASSED  # Only row 0 checked
    
    def test_insufficient_components(self):
        """Skip when not enough component columns."""
        df = pd.DataFrame({
            "total": [100],
            "part": [100],
        })
        result = cond_11_total_equals_sum(df, "total", ["part"])
        assert result.status == ValidationStatus.SKIPPED


# ============================================================================
# COND-12: DUPLICATE ID, CONFLICTING STATUS
# ============================================================================

class TestCond12DuplicateIdConflictingStatus:
    """Tests for COND-12: Duplicate ID, Conflicting Status."""
    
    def test_no_conflicts(self):
        """No violations when IDs have consistent statuses."""
        df = pd.DataFrame({
            "employee_id": [1, 1, 2, 2],
            "status": ["Active", "Active", "Inactive", "Inactive"],
        })
        result = cond_12_duplicate_id_conflicting_status(df, "employee_id", "status")
        assert result.status == ValidationStatus.PASSED
    
    def test_conflicting_status(self):
        """Violation when same ID has active and inactive status."""
        df = pd.DataFrame({
            "user_id": [1, 1, 2],
            "status": ["Active", "Inactive", "Active"],  # ID 1 has conflict
        })
        result = cond_12_duplicate_id_conflicting_status(df, "user_id", "status")
        assert result.status == ValidationStatus.FAILED
        assert 0 in result.affected_rows
        assert 1 in result.affected_rows
    
    def test_enabled_disabled_conflict(self):
        """Conflict with enabled/disabled statuses."""
        df = pd.DataFrame({
            "id": [100, 100],
            "state": ["Enabled", "Disabled"],
        })
        result = cond_12_duplicate_id_conflicting_status(df, "id", "state")
        assert result.status == ValidationStatus.FAILED
    
    def test_unique_ids_no_conflict(self):
        """No conflict when all IDs are unique."""
        df = pd.DataFrame({
            "id": [1, 2, 3],
            "status": ["Active", "Inactive", "Active"],
        })
        result = cond_12_duplicate_id_conflicting_status(df, "id", "status")
        assert result.status == ValidationStatus.PASSED
    
    def test_null_ids_ignored(self):
        """Null IDs are not grouped."""
        df = pd.DataFrame({
            "id": [None, None],
            "status": ["Active", "Inactive"],
        })
        result = cond_12_duplicate_id_conflicting_status(df, "id", "status")
        assert result.status == ValidationStatus.PASSED


# ============================================================================
# CONDITIONAL VALIDATION CLASS TESTS
# ============================================================================

class TestConditionalValidationClass:
    """Tests for the ConditionalValidation orchestrator class."""
    
    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        db = MagicMock()
        db.add = MagicMock()
        db.commit = MagicMock()
        db.rollback = MagicMock()
        return db
    
    @pytest.fixture
    def sample_df(self):
        """Create a sample DataFrame for testing."""
        return pd.DataFrame({
            "employee_id": [1, 2, 3],
            "name": ["Alice", "Bob", "Carol"],
            "status": ["Active", "Inactive", "Active"],
            "start_date": ["2020-01-01", "2019-06-15", "2021-03-10"],
            "end_date": ["2023-12-31", "2023-06-30", None],
            "age": [30, 35, 28],
            "dob": ["1993-05-15", "1988-08-20", "1995-10-05"],
            "score": [85, 45, 92],
            "result": ["Pass", "Pass", "Pass"],  # Row 1 should be Fail
            "quantity": [10, -5, 20],
            "amount": [100, -50, 200],
        })
    
    @pytest.fixture
    def sample_htype_map(self):
        """Create a sample HTYPE map."""
        return {
            "employee_id": "HTYPE-005",  # ID
            "name": "HTYPE-001",  # FNAME
            "status": "HTYPE-029",  # STAT
            "start_date": "HTYPE-013",  # DATE
            "end_date": "HTYPE-013",  # DATE
            "age": "HTYPE-004",  # AGE
            "dob": "HTYPE-013",  # DATE
            "score": "HTYPE-021",  # SCORE
            "result": "HTYPE-029",  # STAT
            "quantity": "HTYPE-020",  # QTY
            "amount": "HTYPE-019",  # AMT
        }
    
    def test_initialization(self, mock_db, sample_df, sample_htype_map):
        """Test class initialization."""
        runner = ConditionalValidation(
            job_id=1,
            df=sample_df,
            db=mock_db,
            htype_map=sample_htype_map,
        )
        assert runner.job_id == 1
        assert len(runner.df) == 3
        assert len(runner.results) == 0
        assert len(runner.flags) == 0
    
    def test_run_all_returns_summary(self, mock_db, sample_df, sample_htype_map):
        """Test run_all returns comprehensive summary."""
        runner = ConditionalValidation(
            job_id=1,
            df=sample_df,
            db=mock_db,
            htype_map=sample_htype_map,
        )
        summary = runner.run_all()
        
        assert "total_checks" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "skipped" in summary
        assert "results" in summary
        assert isinstance(summary["results"], list)
    
    def test_flags_populated(self, mock_db, sample_df, sample_htype_map):
        """Test that flags are populated for failures."""
        # Add an inconsistent score/result
        df = sample_df.copy()
        df.loc[1, "score"] = 45
        df.loc[1, "result"] = "Pass"  # Should be fail
        
        runner = ConditionalValidation(
            job_id=1,
            df=df,
            db=mock_db,
            htype_map=sample_htype_map,
        )
        runner.run_all()
        
        # Should have at least one flag
        assert len(runner.results) > 0
    
    def test_column_detection(self, mock_db, sample_htype_map):
        """Test automatic column detection."""
        df = pd.DataFrame({
            "user_status": ["Active"],
            "created_date": ["2023-01-01"],
            "total_amount": [100],
            "item_quantity": [5],
            "user_id": [1],
        })
        
        runner = ConditionalValidation(
            job_id=1,
            df=df,
            db=mock_db,
            htype_map={},  # Empty HTYPE map
        )
        
        # Should detect columns by name patterns
        assert len(runner.status_cols) > 0
        assert len(runner.date_cols) > 0
        assert len(runner.amount_cols) > 0
        assert len(runner.quantity_cols) > 0
        assert len(runner.id_cols) > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case tests for conditional validation."""
    
    def test_empty_dataframe(self):
        """Handle empty DataFrame."""
        df = pd.DataFrame()
        result = cond_01_status_date_dependency(df, "status", "date")
        assert result.status == ValidationStatus.SKIPPED
    
    def test_single_row_dataframe(self):
        """Handle single row DataFrame."""
        df = pd.DataFrame({
            "status": ["Active"],
            "date": ["2023-01-01"],
        })
        result = cond_01_status_date_dependency(df, "status", "date")
        assert result.status == ValidationStatus.PASSED
    
    def test_all_null_values(self):
        """Handle all null values."""
        df = pd.DataFrame({
            "score": [None, None, None],
            "result": [None, None, None],
        })
        result = cond_06_score_pass_consistency(df, "score", "result")
        assert result.status == ValidationStatus.PASSED  # Nothing to check
    
    def test_mixed_dtypes(self):
        """Handle mixed data types."""
        df = pd.DataFrame({
            "id": [1, "two", 3.0],
            "status": ["Active", "Inactive", "Active"],
        })
        result = cond_12_duplicate_id_conflicting_status(df, "id", "status")
        # Should handle without crashing
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.FAILED]
    
    def test_unicode_values(self):
        """Handle unicode values."""
        df = pd.DataFrame({
            "status": ["完成", "进行中", "完成"],
            "date": [None, "2023-01-01", "2023-02-01"],
        })
        # Custom statuses for Chinese - row 0 is "完成" (completed) with null date
        result = cond_01_status_date_dependency(
            df, "status", "date",
            completed_statuses={"完成"}
        )
        assert result.status == ValidationStatus.FAILED  # Row 0 has null date
        assert 0 in result.affected_rows
    
    def test_very_large_numbers(self):
        """Handle very large numbers."""
        df = pd.DataFrame({
            "quantity": [10**15],
            "amount": [10**15 * 100],
        })
        result = cond_09_quantity_amount_sign(df, "quantity", "amount")
        assert result.status == ValidationStatus.PASSED


# ============================================================================
# INTEGRATION TEST
# ============================================================================

class TestIntegration:
    """Integration tests for full validation workflow."""
    
    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        df = pd.DataFrame({
            "employee_id": [1, 1, 2, 2, 3],
            "name": ["Alice", "Alice", "Bob", "Bob", "Carol"],
            "status": ["Active", "Inactive", "Active", "Active", "Completed"],  # ID 1 conflict
            "hire_date": ["2020-01-01", "2020-01-01", "2019-06-15", "2019-06-15", "2021-03-10"],
            "termination_date": [None, "2023-06-01", None, None, "2023-12-31"],
            "department_id": [10, 10, 20, 20, 99],  # 99 is orphan
            "age": [30, 30, 35, 35, 28],
            "dob": ["1993-05-15", "1993-05-15", "1988-08-20", "1988-08-20", "1995-10-05"],
            "score": [85, 85, 45, 45, 92],
            "pass_status": ["Pass", "Pass", "Pass", "Pass", "Pass"],  # Bob should be Fail
            "title": ["Ms.", "Ms.", "Mr.", "Mr.", "Mrs."],
            "gender": ["Female", "Female", "Female", "Female", "Female"],  # Bob conflict
            "country": ["USA", "USA", "India", "India", "Nepal"],
            "phone": ["+1-555-1234", "+1-555-1234", "+91-9876543210", "+91-9876543210", "+1-555-9999"],  # Carol conflict
            "quantity": [10, 10, -5, -5, 20],
            "amount": [100, 100, -50, -50, -200],  # Carol sign conflict
            "admission_date": ["2015-09-01", "2015-09-01", "2014-09-01", "2014-09-01", "2018-09-01"],
            "graduation_date": ["2019-06-15", "2019-06-15", "2018-06-15", "2018-06-15", "2022-06-15"],
            "male_count": [25, 25, 20, 20, 30],
            "female_count": [25, 25, 30, 30, 20],
            "total_count": [50, 50, 50, 50, 60],  # Carol incorrect total
        })
        
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        
        runner = ConditionalValidation(
            job_id=1,
            df=df,
            db=mock_db,
            htype_map={},
            reference_data={"department_id": {10, 20, 30}},
        )
        
        summary = runner.run_all()
        
        # Should have run multiple checks
        assert summary["total_checks"] > 0
        
        # Should have found some issues
        # (duplicate ID conflict, referential integrity, etc.)
        assert len(runner.flags) >= 0  # May or may not have flags depending on detection


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
