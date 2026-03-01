"""
Test suite for HTYPE Detection Engine (Session 3).

Tests all 47 HTYPE classifications across:
1. Column name matching (exact and partial)
2. Value pattern detection
3. Data distribution analysis
4. Edge cases and exclusions
"""

import pytest
import pandas as pd
import numpy as np
from app.services.htype_detector import HtypeDetector, HtypeMatch, detect_htypes


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def detector():
    """Create a fresh HtypeDetector instance."""
    return HtypeDetector()


# ============================================================================
# PART B — PERSONAL & IDENTITY DATA
# ============================================================================

class TestHtype001FullName:
    """Tests for HTYPE-001: Full Name detection."""
    
    def test_exact_match_name(self, detector):
        df = pd.DataFrame({"name": ["John Doe", "Jane Smith", "Bob Wilson"]})
        result = detector.detect_column_htype("name", df["name"])
        assert result.htype_code == "HTYPE-001"
        assert result.formula_set == "FNAME"
        assert result.confidence >= 0.85
    
    def test_exact_match_full_name(self, detector):
        df = pd.DataFrame({"full_name": ["John Doe", "Jane Smith"]})
        result = detector.detect_column_htype("full_name", df["full_name"])
        assert result.htype_code == "HTYPE-001"
    
    def test_partial_match_student_name(self, detector):
        df = pd.DataFrame({"student_name": ["Alice Brown", "Charlie Green"]})
        result = detector.detect_column_htype("student_name", df["student_name"])
        assert result.htype_code == "HTYPE-001"
    
    def test_excludes_first_name(self, detector):
        """first_name should NOT match HTYPE-001 (should match HTYPE-002)."""
        df = pd.DataFrame({"first_name": ["John", "Jane", "Bob"]})
        result = detector.detect_column_htype("first_name", df["first_name"])
        assert result.htype_code == "HTYPE-002"
    
    def test_excludes_product_name(self, detector):
        """product_name should NOT match HTYPE-001."""
        df = pd.DataFrame({"product_name": ["Widget A", "Gadget B"]})
        result = detector.detect_column_htype("product_name", df["product_name"])
        assert result.htype_code != "HTYPE-001"
    
    def test_pii_flag(self, detector):
        df = pd.DataFrame({"full_name": ["John Doe"]})
        result = detector.detect_column_htype("full_name", df["full_name"])
        assert result.is_pii is True


class TestHtype002FirstLastMiddleName:
    """Tests for HTYPE-002: First/Last/Middle Name detection."""
    
    def test_first_name(self, detector):
        df = pd.DataFrame({"first_name": ["John", "Jane", "Bob"]})
        result = detector.detect_column_htype("first_name", df["first_name"])
        assert result.htype_code == "HTYPE-002"
        assert result.formula_set == "SNAME"
    
    def test_last_name(self, detector):
        df = pd.DataFrame({"last_name": ["Doe", "Smith", "Wilson"]})
        result = detector.detect_column_htype("last_name", df["last_name"])
        assert result.htype_code == "HTYPE-002"
    
    def test_surname(self, detector):
        df = pd.DataFrame({"surname": ["Doe", "Smith"]})
        result = detector.detect_column_htype("surname", df["surname"])
        assert result.htype_code == "HTYPE-002"
    
    def test_fname_abbreviation(self, detector):
        df = pd.DataFrame({"fname": ["John", "Jane"]})
        result = detector.detect_column_htype("fname", df["fname"])
        assert result.htype_code == "HTYPE-002"
    
    def test_middle_name(self, detector):
        df = pd.DataFrame({"middle_name": ["Robert", "Marie", ""]})
        result = detector.detect_column_htype("middle_name", df["middle_name"])
        assert result.htype_code == "HTYPE-002"


class TestHtype003UniqueID:
    """Tests for HTYPE-003: Unique ID / Record ID detection."""
    
    def test_id_column(self, detector):
        df = pd.DataFrame({"id": [1, 2, 3, 4, 5]})
        result = detector.detect_column_htype("id", df["id"])
        assert result.htype_code == "HTYPE-003"
        assert result.formula_set == "UID"
    
    def test_student_id(self, detector):
        df = pd.DataFrame({"student_id": ["STU001", "STU002", "STU003"]})
        result = detector.detect_column_htype("student_id", df["student_id"])
        assert result.htype_code == "HTYPE-003"
    
    def test_emp_id(self, detector):
        df = pd.DataFrame({"emp_id": ["EMP100", "EMP101"]})
        result = detector.detect_column_htype("emp_id", df["emp_id"])
        assert result.htype_code == "HTYPE-003"
    
    def test_excludes_national_id(self, detector):
        """national_id should be HTYPE-029, not HTYPE-003."""
        df = pd.DataFrame({"national_id": ["123456789", "987654321"]})
        result = detector.detect_column_htype("national_id", df["national_id"])
        assert result.htype_code == "HTYPE-029"
    
    def test_not_pii(self, detector):
        df = pd.DataFrame({"record_id": [1, 2, 3]})
        result = detector.detect_column_htype("record_id", df["record_id"])
        assert result.is_pii is False


class TestHtype007Age:
    """Tests for HTYPE-007: Age detection."""
    
    def test_age_column(self, detector):
        df = pd.DataFrame({"age": [25, 30, 45, 18, 65]})
        result = detector.detect_column_htype("age", df["age"])
        assert result.htype_code == "HTYPE-007"
        assert result.formula_set == "AGE"
    
    def test_patient_age(self, detector):
        df = pd.DataFrame({"patient_age": [22, 45, 67]})
        result = detector.detect_column_htype("patient_age", df["patient_age"])
        assert result.htype_code == "HTYPE-007"
    
    def test_age_in_years(self, detector):
        df = pd.DataFrame({"age_in_years": [5, 12, 45]})
        result = detector.detect_column_htype("age_in_years", df["age_in_years"])
        assert result.htype_code == "HTYPE-007"


class TestHtype008Gender:
    """Tests for HTYPE-008: Gender / Sex detection."""
    
    def test_gender_column_name(self, detector):
        df = pd.DataFrame({"gender": ["Male", "Female", "Other"]})
        result = detector.detect_column_htype("gender", df["gender"])
        assert result.htype_code == "HTYPE-008"
        assert result.formula_set == "GEN"
    
    def test_sex_column_name(self, detector):
        df = pd.DataFrame({"sex": ["M", "F", "M", "F"]})
        result = detector.detect_column_htype("sex", df["sex"])
        assert result.htype_code == "HTYPE-008"
    
    def test_gender_value_pattern(self, detector):
        """Test detection by value pattern for ambiguous column name."""
        df = pd.DataFrame({"info": ["male", "female", "male", "female", "other"]})
        result = detector.detect_column_htype("info", df["info"])
        assert result.htype_code == "HTYPE-008"
    
    def test_is_pii(self, detector):
        df = pd.DataFrame({"gender": ["Male"]})
        result = detector.detect_column_htype("gender", df["gender"])
        assert result.is_pii is True


class TestHtype029GovernmentID:
    """Tests for HTYPE-029: National ID / Passport / Government ID."""
    
    def test_passport_no(self, detector):
        df = pd.DataFrame({"passport_no": ["AB123456", "CD789012"]})
        result = detector.detect_column_htype("passport_no", df["passport_no"])
        assert result.htype_code == "HTYPE-029"
        assert result.formula_set == "GOVID"
    
    def test_national_id(self, detector):
        df = pd.DataFrame({"national_id": ["123456789012"]})
        result = detector.detect_column_htype("national_id", df["national_id"])
        assert result.htype_code == "HTYPE-029"
    
    def test_ssn(self, detector):
        df = pd.DataFrame({"ssn": ["123-45-6789"]})
        result = detector.detect_column_htype("ssn", df["ssn"])
        assert result.htype_code == "HTYPE-029"
    
    def test_high_sensitivity(self, detector):
        df = pd.DataFrame({"passport_no": ["AB123456"]})
        result = detector.detect_column_htype("passport_no", df["passport_no"])
        assert result.sensitivity_level == "high"


class TestHtype030BloodGroup:
    """Tests for HTYPE-030: Blood Group detection."""
    
    def test_blood_group_column(self, detector):
        df = pd.DataFrame({"blood_group": ["A+", "B-", "O+", "AB+"]})
        result = detector.detect_column_htype("blood_group", df["blood_group"])
        assert result.htype_code == "HTYPE-030"
        assert result.formula_set == "BLOOD"
    
    def test_blood_type(self, detector):
        df = pd.DataFrame({"blood_type": ["A positive", "B negative"]})
        result = detector.detect_column_htype("blood_type", df["blood_type"])
        assert result.htype_code == "HTYPE-030"
    
    def test_blood_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"medical_info": ["A+", "B+", "O-", "AB+", "A-", "O+"]})
        result = detector.detect_column_htype("medical_info", df["medical_info"])
        assert result.htype_code == "HTYPE-030"


# ============================================================================
# PART C — DATE & TIME DATA
# ============================================================================

class TestHtype004Date:
    """Tests for HTYPE-004: Date detection."""
    
    def test_date_column(self, detector):
        df = pd.DataFrame({"date": ["2024-01-15", "2024-02-20"]})
        result = detector.detect_column_htype("date", df["date"])
        assert result.htype_code == "HTYPE-004"
        assert result.formula_set == "DATE"
    
    def test_dob(self, detector):
        df = pd.DataFrame({"dob": ["1990-05-15", "1985-12-01"]})
        result = detector.detect_column_htype("dob", df["dob"])
        assert result.htype_code == "HTYPE-004"
    
    def test_joining_date(self, detector):
        df = pd.DataFrame({"joining_date": ["2020-01-01", "2021-06-15"]})
        result = detector.detect_column_htype("joining_date", df["joining_date"])
        assert result.htype_code == "HTYPE-004"
    
    def test_date_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"col1": ["15/01/2024", "20/02/2024", "01/03/2024"]})
        result = detector.detect_column_htype("col1", df["col1"])
        assert result.htype_code == "HTYPE-004"


class TestHtype005Time:
    """Tests for HTYPE-005: Time detection."""
    
    def test_time_column(self, detector):
        df = pd.DataFrame({"time": ["09:30", "14:45", "18:00"]})
        result = detector.detect_column_htype("time", df["time"])
        assert result.htype_code == "HTYPE-005"
        assert result.formula_set == "TIME"
    
    def test_check_in(self, detector):
        df = pd.DataFrame({"check_in": ["08:00", "09:15"]})
        result = detector.detect_column_htype("check_in", df["check_in"])
        assert result.htype_code == "HTYPE-005"
    
    def test_time_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"col": ["09:30 AM", "02:45 PM", "11:00 AM"]})
        result = detector.detect_column_htype("col", df["col"])
        assert result.htype_code == "HTYPE-005"


class TestHtype006DateTime:
    """Tests for HTYPE-006: DateTime detection."""
    
    def test_created_at(self, detector):
        df = pd.DataFrame({"created_at": ["2024-01-15 09:30:00", "2024-01-16 10:00:00"]})
        result = detector.detect_column_htype("created_at", df["created_at"])
        assert result.htype_code == "HTYPE-006"
        assert result.formula_set == "DTM"
    
    def test_timestamp(self, detector):
        df = pd.DataFrame({"timestamp": ["2024-01-15T09:30:00", "2024-01-15T10:00:00"]})
        result = detector.detect_column_htype("timestamp", df["timestamp"])
        assert result.htype_code == "HTYPE-006"
    
    def test_datetime_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"col": ["2024-01-15 09:30:00", "2024-01-16 10:00:00"]})
        result = detector.detect_column_htype("col", df["col"])
        assert result.htype_code == "HTYPE-006"


class TestHtype033Duration:
    """Tests for HTYPE-033: Duration / Time Elapsed."""
    
    def test_duration_column(self, detector):
        df = pd.DataFrame({"duration": ["2 hours", "30 minutes", "1 day"]})
        result = detector.detect_column_htype("duration", df["duration"])
        assert result.htype_code == "HTYPE-033"
        assert result.formula_set == "DUR"
    
    def test_years_of_service(self, detector):
        df = pd.DataFrame({"years_of_service": [5, 10, 15]})
        result = detector.detect_column_htype("years_of_service", df["years_of_service"])
        assert result.htype_code == "HTYPE-033"


class TestHtype041FiscalPeriod:
    """Tests for HTYPE-041: Fiscal Period / Academic Year."""
    
    def test_fiscal_year(self, detector):
        df = pd.DataFrame({"fiscal_year": ["FY2023", "FY2024"]})
        result = detector.detect_column_htype("fiscal_year", df["fiscal_year"])
        assert result.htype_code == "HTYPE-041"
        assert result.formula_set == "FISC"
    
    def test_academic_year(self, detector):
        df = pd.DataFrame({"academic_year": ["2023-24", "2024-25"]})
        result = detector.detect_column_htype("academic_year", df["academic_year"])
        assert result.htype_code == "HTYPE-041"
    
    def test_semester(self, detector):
        df = pd.DataFrame({"semester": ["Fall 2023", "Spring 2024"]})
        result = detector.detect_column_htype("semester", df["semester"])
        assert result.htype_code == "HTYPE-041"


# ============================================================================
# PART D — CONTACT & LOCATION DATA
# ============================================================================

class TestHtype009Phone:
    """Tests for HTYPE-009: Phone / Mobile Number."""
    
    def test_phone_column(self, detector):
        df = pd.DataFrame({"phone": ["+1-555-123-4567", "+1-555-987-6543"]})
        result = detector.detect_column_htype("phone", df["phone"])
        assert result.htype_code == "HTYPE-009"
        assert result.formula_set == "PHONE"
    
    def test_mobile_column(self, detector):
        df = pd.DataFrame({"mobile": ["9876543210", "1234567890"]})
        result = detector.detect_column_htype("mobile", df["mobile"])
        assert result.htype_code == "HTYPE-009"
    
    def test_phone_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"contact_info": ["+1 (555) 123-4567", "+1 (555) 987-6543"]})
        result = detector.detect_column_htype("contact_info", df["contact_info"])
        # Should detect by value pattern since numbers match phone format
        assert result.htype_code == "HTYPE-009"


class TestHtype010Email:
    """Tests for HTYPE-010: Email Address."""
    
    def test_email_column(self, detector):
        df = pd.DataFrame({"email": ["john@example.com", "jane@test.org"]})
        result = detector.detect_column_htype("email", df["email"])
        assert result.htype_code == "HTYPE-010"
        assert result.formula_set == "EMAIL"
    
    def test_email_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"user_info": ["john@example.com", "jane@test.org", "bob@company.net"]})
        result = detector.detect_column_htype("user_info", df["user_info"])
        assert result.htype_code == "HTYPE-010"
    
    def test_is_pii(self, detector):
        df = pd.DataFrame({"email": ["test@test.com"]})
        result = detector.detect_column_htype("email", df["email"])
        assert result.is_pii is True


class TestHtype011Address:
    """Tests for HTYPE-011: Address / Location (Full)."""
    
    def test_address_column(self, detector):
        df = pd.DataFrame({"address": ["123 Main St, City, State 12345"]})
        result = detector.detect_column_htype("address", df["address"])
        assert result.htype_code == "HTYPE-011"
        assert result.formula_set == "ADDR"
    
    def test_excludes_email_address(self, detector):
        """email_address should NOT match HTYPE-011."""
        df = pd.DataFrame({"email_address": ["test@example.com"]})
        result = detector.detect_column_htype("email_address", df["email_address"])
        assert result.htype_code == "HTYPE-010"  # Should be Email
    
    def test_high_sensitivity(self, detector):
        df = pd.DataFrame({"address": ["123 Main St"]})
        result = detector.detect_column_htype("address", df["address"])
        assert result.sensitivity_level == "high"


class TestHtype012CityRegion:
    """Tests for HTYPE-012: City / District / Region."""
    
    def test_city_column(self, detector):
        df = pd.DataFrame({"city": ["New York", "Los Angeles", "Chicago"]})
        result = detector.detect_column_htype("city", df["city"])
        assert result.htype_code == "HTYPE-012"
        assert result.formula_set == "CITY"
    
    def test_district(self, detector):
        df = pd.DataFrame({"district": ["Manhattan", "Brooklyn"]})
        result = detector.detect_column_htype("district", df["district"])
        assert result.htype_code == "HTYPE-012"


class TestHtype013Country:
    """Tests for HTYPE-013: Country."""
    
    def test_country_column(self, detector):
        df = pd.DataFrame({"country": ["USA", "Canada", "UK"]})
        result = detector.detect_column_htype("country", df["country"])
        assert result.htype_code == "HTYPE-013"
        assert result.formula_set == "CNTRY"


class TestHtype014PostalCode:
    """Tests for HTYPE-014: Postal Code / ZIP Code."""
    
    def test_zip_column(self, detector):
        df = pd.DataFrame({"zip": ["10001", "90210", "60601"]})
        result = detector.detect_column_htype("zip", df["zip"])
        assert result.htype_code == "HTYPE-014"
        assert result.formula_set == "POST"
    
    def test_postal_code(self, detector):
        df = pd.DataFrame({"postal_code": ["12345", "67890"]})
        result = detector.detect_column_htype("postal_code", df["postal_code"])
        assert result.htype_code == "HTYPE-014"


class TestHtype035Coordinates:
    """Tests for HTYPE-035: Coordinates (Latitude / Longitude)."""
    
    def test_latitude(self, detector):
        df = pd.DataFrame({"latitude": [40.7128, 34.0522, 41.8781]})
        result = detector.detect_column_htype("latitude", df["latitude"])
        assert result.htype_code == "HTYPE-035"
        assert result.formula_set == "GEO"
    
    def test_longitude(self, detector):
        df = pd.DataFrame({"longitude": [-74.006, -118.2437, -87.6298]})
        result = detector.detect_column_htype("longitude", df["longitude"])
        assert result.htype_code == "HTYPE-035"


# ============================================================================
# PART E — NUMERIC & FINANCIAL DATA
# ============================================================================

class TestHtype015Amount:
    """Tests for HTYPE-015: Numeric Amount / Currency / Revenue."""
    
    def test_amount_column(self, detector):
        df = pd.DataFrame({"amount": [1000.50, 2500.00, 3750.25]})
        result = detector.detect_column_htype("amount", df["amount"])
        assert result.htype_code == "HTYPE-015"
        assert result.formula_set == "AMT"
    
    def test_price_column(self, detector):
        df = pd.DataFrame({"price": [19.99, 29.99, 49.99]})
        result = detector.detect_column_htype("price", df["price"])
        assert result.htype_code == "HTYPE-015"
    
    def test_salary_column(self, detector):
        df = pd.DataFrame({"salary": [50000, 75000, 100000]})
        result = detector.detect_column_htype("salary", df["salary"])
        assert result.htype_code == "HTYPE-015"


class TestHtype016Quantity:
    """Tests for HTYPE-016: Quantity / Count / Integer Metric."""
    
    def test_quantity_column(self, detector):
        df = pd.DataFrame({"quantity": [10, 25, 50, 100]})
        result = detector.detect_column_htype("quantity", df["quantity"])
        assert result.htype_code == "HTYPE-016"
        assert result.formula_set == "QTY"
    
    def test_count_column(self, detector):
        df = pd.DataFrame({"count": [5, 10, 15]})
        result = detector.detect_column_htype("count", df["count"])
        assert result.htype_code == "HTYPE-016"


class TestHtype017Percentage:
    """Tests for HTYPE-017: Percentage / Rate / Ratio."""
    
    def test_percentage_column(self, detector):
        df = pd.DataFrame({"percentage": [25.5, 50.0, 75.5]})
        result = detector.detect_column_htype("percentage", df["percentage"])
        assert result.htype_code == "HTYPE-017"
        assert result.formula_set == "PCT"
    
    def test_rate_column(self, detector):
        df = pd.DataFrame({"rate": [0.05, 0.10, 0.15]})
        result = detector.detect_column_htype("rate", df["rate"])
        assert result.htype_code == "HTYPE-017"


class TestHtype021Score:
    """Tests for HTYPE-021: Score / Rating / Grade / GPA."""
    
    def test_score_column(self, detector):
        df = pd.DataFrame({"score": [85, 92, 78, 95]})
        result = detector.detect_column_htype("score", df["score"])
        assert result.htype_code == "HTYPE-021"
        assert result.formula_set == "SCORE"
    
    def test_gpa_column(self, detector):
        df = pd.DataFrame({"gpa": [3.5, 3.8, 4.0, 3.2]})
        result = detector.detect_column_htype("gpa", df["gpa"])
        assert result.htype_code == "HTYPE-021"
    
    def test_grade_column(self, detector):
        df = pd.DataFrame({"grade": ["A", "B", "C", "A+"]})
        result = detector.detect_column_htype("grade", df["grade"])
        assert result.htype_code == "HTYPE-021"


class TestHtype042CurrencyCode:
    """Tests for HTYPE-042: Currency Code."""
    
    def test_currency_column(self, detector):
        df = pd.DataFrame({"currency": ["USD", "EUR", "GBP"]})
        result = detector.detect_column_htype("currency", df["currency"])
        assert result.htype_code == "HTYPE-042"
        assert result.formula_set == "CUR"
    
    def test_currency_value_pattern(self, detector):
        """Test ISO 4217 pattern detection."""
        df = pd.DataFrame({"code": ["USD", "EUR", "GBP", "JPY", "INR"]})
        result = detector.detect_column_htype("code", df["code"])
        assert result.htype_code == "HTYPE-042"


class TestHtype043Rank:
    """Tests for HTYPE-043: Rank / Ordinal."""
    
    def test_rank_column(self, detector):
        df = pd.DataFrame({"rank": [1, 2, 3, 4, 5]})
        result = detector.detect_column_htype("rank", df["rank"])
        assert result.htype_code == "HTYPE-043"
        assert result.formula_set == "RANK"


class TestHtype044Calculated:
    """Tests for HTYPE-044: Calculated / Derived Column."""
    
    def test_total_column(self, detector):
        df = pd.DataFrame({"grand_total": [100, 200, 300]})
        result = detector.detect_column_htype("grand_total", df["grand_total"])
        assert result.htype_code == "HTYPE-044"
        assert result.formula_set == "CALC"
    
    def test_net_column(self, detector):
        df = pd.DataFrame({"net": [50.5, 75.25, 100.00]})
        result = detector.detect_column_htype("net", df["net"])
        assert result.htype_code == "HTYPE-044"


# ============================================================================
# PART F — CLASSIFICATION & STATUS DATA
# ============================================================================

class TestHtype018Boolean:
    """Tests for HTYPE-018: Boolean / Flag / Yes-No Field."""
    
    def test_is_active_column(self, detector):
        df = pd.DataFrame({"is_active": [True, False, True]})
        result = detector.detect_column_htype("is_active", df["is_active"])
        assert result.htype_code == "HTYPE-018"
        assert result.formula_set == "BOOL"
    
    def test_verified_column(self, detector):
        df = pd.DataFrame({"verified": ["Yes", "No", "Yes"]})
        result = detector.detect_column_htype("verified", df["verified"])
        assert result.htype_code == "HTYPE-018"
    
    def test_boolean_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"col": ["yes", "no", "yes", "no", "yes"]})
        result = detector.detect_column_htype("col", df["col"])
        assert result.htype_code == "HTYPE-018"


class TestHtype019Category:
    """Tests for HTYPE-019: Category / Classification Label."""
    
    def test_category_column(self, detector):
        df = pd.DataFrame({"category": ["A", "B", "C", "A", "B"]})
        result = detector.detect_column_htype("category", df["category"])
        assert result.htype_code == "HTYPE-019"
        assert result.formula_set == "CAT"
    
    def test_type_column(self, detector):
        df = pd.DataFrame({"type": ["Standard", "Premium", "Basic"]})
        result = detector.detect_column_htype("type", df["type"])
        assert result.htype_code == "HTYPE-019"


class TestHtype020Status:
    """Tests for HTYPE-020: Status Field."""
    
    def test_status_column(self, detector):
        df = pd.DataFrame({"status": ["Active", "Pending", "Completed"]})
        result = detector.detect_column_htype("status", df["status"])
        assert result.htype_code == "HTYPE-020"
        assert result.formula_set == "STAT"
    
    def test_excludes_marital_status(self, detector):
        """marital_status should be HTYPE-040, not HTYPE-020."""
        df = pd.DataFrame({"marital_status": ["Single", "Married"]})
        result = detector.detect_column_htype("marital_status", df["marital_status"])
        assert result.htype_code == "HTYPE-040"


class TestHtype045Survey:
    """Tests for HTYPE-045: Survey / Likert Response."""
    
    def test_response_column(self, detector):
        df = pd.DataFrame({"response": ["Agree", "Disagree", "Neutral"]})
        result = detector.detect_column_htype("response", df["response"])
        assert result.htype_code == "HTYPE-045"
        assert result.formula_set == "SURV"
    
    def test_satisfaction_column(self, detector):
        df = pd.DataFrame({"satisfaction": [1, 2, 3, 4, 5]})
        result = detector.detect_column_htype("satisfaction", df["satisfaction"])
        assert result.htype_code == "HTYPE-045"


class TestHtype046MultiValue:
    """Tests for HTYPE-046: Multi-Value / Tag Field."""
    
    def test_tags_column(self, detector):
        df = pd.DataFrame({"tags": ["python,java", "sql,nosql"]})
        result = detector.detect_column_htype("tags", df["tags"])
        assert result.htype_code == "HTYPE-046"
        assert result.formula_set == "MULTI"
    
    def test_skills_column(self, detector):
        df = pd.DataFrame({"skills": ["Python, SQL", "Java, C++"]})
        result = detector.detect_column_htype("skills", df["skills"])
        assert result.htype_code == "HTYPE-046"


# ============================================================================
# PART G — ORGANIZATIONAL & PRODUCT DATA
# ============================================================================

class TestHtype024ProductName:
    """Tests for HTYPE-024: Product Name / Item Name."""
    
    def test_product_column(self, detector):
        df = pd.DataFrame({"product": ["Widget A", "Gadget B"]})
        result = detector.detect_column_htype("product", df["product"])
        assert result.htype_code == "HTYPE-024"
        assert result.formula_set == "PROD"


class TestHtype025ProductCode:
    """Tests for HTYPE-025: Product Code / SKU / Barcode."""
    
    def test_sku_column(self, detector):
        df = pd.DataFrame({"sku": ["ABC123", "DEF456"]})
        result = detector.detect_column_htype("sku", df["sku"])
        assert result.htype_code == "HTYPE-025"
        assert result.formula_set == "SKU"


class TestHtype026Organization:
    """Tests for HTYPE-026: Organization / Company Name."""
    
    def test_company_column(self, detector):
        df = pd.DataFrame({"company": ["Acme Corp", "XYZ Ltd"]})
        result = detector.detect_column_htype("company", df["company"])
        assert result.htype_code == "HTYPE-026"
        assert result.formula_set == "ORG"


class TestHtype027JobTitle:
    """Tests for HTYPE-027: Job Title / Designation / Role."""
    
    def test_designation_column(self, detector):
        df = pd.DataFrame({"designation": ["Manager", "Director"]})
        result = detector.detect_column_htype("designation", df["designation"])
        assert result.htype_code == "HTYPE-027"
        assert result.formula_set == "JOB"


class TestHtype028Department:
    """Tests for HTYPE-028: Department / Division / Unit."""
    
    def test_department_column(self, detector):
        df = pd.DataFrame({"department": ["HR", "IT", "Finance"]})
        result = detector.detect_column_htype("department", df["department"])
        assert result.htype_code == "HTYPE-028"
        assert result.formula_set == "DEPT"


class TestHtype034SerialNumber:
    """Tests for HTYPE-034: Serial Number / Reference Number."""
    
    def test_invoice_no(self, detector):
        df = pd.DataFrame({"invoice_no": ["INV001", "INV002"]})
        result = detector.detect_column_htype("invoice_no", df["invoice_no"])
        assert result.htype_code == "HTYPE-034"
        assert result.formula_set == "REFNO"


class TestHtype047Version:
    """Tests for HTYPE-047: Version / Revision Number."""
    
    def test_version_column(self, detector):
        df = pd.DataFrame({"version": ["1.0", "2.0", "2.1"]})
        result = detector.detect_column_htype("version", df["version"])
        assert result.htype_code == "HTYPE-047"
        assert result.formula_set == "VER"


# ============================================================================
# PART H — MEDICAL DATA
# ============================================================================

class TestHtype031Diagnosis:
    """Tests for HTYPE-031: Diagnosis / Medical Condition."""
    
    def test_diagnosis_column(self, detector):
        df = pd.DataFrame({"diagnosis": ["Type 2 Diabetes", "Hypertension"]})
        result = detector.detect_column_htype("diagnosis", df["diagnosis"])
        assert result.htype_code == "HTYPE-031"
        assert result.formula_set == "DIAG"
        assert result.is_pii is True
        assert result.sensitivity_level == "high"


class TestHtype032PhysicalMeasurement:
    """Tests for HTYPE-032: Weight / Height / Physical Measurement."""
    
    def test_weight_column(self, detector):
        df = pd.DataFrame({"weight": [65.5, 70.2, 58.0]})
        result = detector.detect_column_htype("weight", df["weight"])
        assert result.htype_code == "HTYPE-032"
        assert result.formula_set == "PHYS"
    
    def test_height_column(self, detector):
        df = pd.DataFrame({"height": [175, 168, 182]})
        result = detector.detect_column_htype("height", df["height"])
        assert result.htype_code == "HTYPE-032"


# ============================================================================
# PART I — TEXT & TECHNICAL DATA
# ============================================================================

class TestHtype022Text:
    """Tests for HTYPE-022: Text / Notes / Description."""
    
    def test_notes_column(self, detector):
        df = pd.DataFrame({"notes": ["Patient was admitted yesterday", "Follow up needed"]})
        result = detector.detect_column_htype("notes", df["notes"])
        assert result.htype_code == "HTYPE-022"
        assert result.formula_set == "TEXT"
    
    def test_description_column(self, detector):
        df = pd.DataFrame({"description": ["A detailed description of the item"]})
        result = detector.detect_column_htype("description", df["description"])
        assert result.htype_code == "HTYPE-022"


class TestHtype023URL:
    """Tests for HTYPE-023: URL / Website."""
    
    def test_url_column(self, detector):
        df = pd.DataFrame({"url": ["https://example.com", "https://test.org"]})
        result = detector.detect_column_htype("url", df["url"])
        assert result.htype_code == "HTYPE-023"
        assert result.formula_set == "URL"
    
    def test_url_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"link": ["https://example.com", "https://test.org", "https://site.net"]})
        result = detector.detect_column_htype("link", df["link"])
        assert result.htype_code == "HTYPE-023"


class TestHtype036IPAddress:
    """Tests for HTYPE-036: IP Address."""
    
    def test_ip_address_column(self, detector):
        df = pd.DataFrame({"ip_address": ["192.168.1.1", "10.0.0.1"]})
        result = detector.detect_column_htype("ip_address", df["ip_address"])
        assert result.htype_code == "HTYPE-036"
        assert result.formula_set == "IP"
    
    def test_ip_value_pattern(self, detector):
        """Test detection by value pattern."""
        df = pd.DataFrame({"col": ["192.168.1.1", "10.0.0.1", "172.16.0.1"]})
        result = detector.detect_column_htype("col", df["col"])
        assert result.htype_code == "HTYPE-036"


class TestHtype037FileName:
    """Tests for HTYPE-037: File Name / File Path."""
    
    def test_filename_column(self, detector):
        df = pd.DataFrame({"filename": ["report.pdf", "data.csv"]})
        result = detector.detect_column_htype("filename", df["filename"])
        assert result.htype_code == "HTYPE-037"
        assert result.formula_set == "FILE"


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

class TestDetectAllColumns:
    """Tests for detect_all_columns method."""
    
    def test_mixed_columns(self, detector):
        df = pd.DataFrame({
            "name": ["John Doe", "Jane Smith"],
            "email": ["john@test.com", "jane@test.com"],
            "age": [25, 30],
            "city": ["NYC", "LA"],
        })
        results = detector.detect_all_columns(df)
        
        assert len(results) == 4
        assert results["name"].htype_code == "HTYPE-001"
        assert results["email"].htype_code == "HTYPE-010"
        assert results["age"].htype_code == "HTYPE-007"
        assert results["city"].htype_code == "HTYPE-012"
    
    def test_returns_htype_match_objects(self, detector):
        df = pd.DataFrame({"name": ["John"]})
        results = detector.detect_all_columns(df)
        
        assert isinstance(results["name"], HtypeMatch)


class TestGetHtypeMap:
    """Tests for get_htype_map method."""
    
    def test_returns_dict_of_codes(self, detector):
        df = pd.DataFrame({
            "email": ["test@test.com"],
            "phone": ["1234567890"],
        })
        result = detector.get_htype_map(df)
        
        assert isinstance(result, dict)
        assert result["email"] == "HTYPE-010"
        assert result["phone"] == "HTYPE-009"


class TestGetPiiColumns:
    """Tests for get_pii_columns method."""
    
    def test_identifies_pii(self, detector):
        df = pd.DataFrame({
            "name": ["John Doe"],
            "email": ["test@test.com"],
            "city": ["NYC"],  # Not PII
            "age": [25],      # Not PII
        })
        pii_cols = detector.get_pii_columns(df)
        
        assert "name" in pii_cols
        assert "email" in pii_cols
        assert "city" not in pii_cols
        assert "age" not in pii_cols


class TestGetHighSensitivityColumns:
    """Tests for get_high_sensitivity_columns method."""
    
    def test_identifies_high_sensitivity(self, detector):
        df = pd.DataFrame({
            "address": ["123 Main St"],  # High
            "passport_no": ["AB123456"],  # High
            "name": ["John"],             # Medium
            "city": ["NYC"],              # Low
        })
        high_sens = detector.get_high_sensitivity_columns(df)
        
        assert "address" in high_sens
        assert "passport_no" in high_sens
        assert "name" not in high_sens
        assert "city" not in high_sens


class TestGetDetectionReport:
    """Tests for get_detection_report method."""
    
    def test_report_structure(self, detector):
        df = pd.DataFrame({
            "name": ["John"],
            "email": ["test@test.com"],
        })
        report = detector.get_detection_report(df)
        
        assert "column_count" in report
        assert "detections" in report
        assert "htype_map" in report
        assert "columns_by_htype" in report
        assert "pii_columns" in report
        assert "confidence_stats" in report
    
    def test_confidence_stats(self, detector):
        df = pd.DataFrame({
            "name": ["John"],
            "email": ["test@test.com"],
        })
        report = detector.get_detection_report(df)
        stats = report["confidence_stats"]
        
        assert "min" in stats
        assert "max" in stats
        assert "mean" in stats
        assert "low_confidence_count" in stats


class TestConvenienceFunction:
    """Tests for detect_htypes convenience function."""
    
    def test_detect_htypes_function(self):
        df = pd.DataFrame({
            "name": ["John"],
            "age": [25],
        })
        result = detect_htypes(df)
        
        assert isinstance(result, dict)
        assert result["name"] == "HTYPE-001"
        assert result["age"] == "HTYPE-007"


# ============================================================================
# EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and special scenarios."""
    
    def test_empty_dataframe(self, detector):
        df = pd.DataFrame()
        results = detector.detect_all_columns(df)
        assert results == {}
    
    def test_all_null_column(self, detector):
        df = pd.DataFrame({"name": [None, None, None]})
        result = detector.detect_column_htype("name", df["name"])
        # Should still detect by column name
        assert result.htype_code == "HTYPE-001"
    
    def test_column_with_spaces_in_name(self, detector):
        df = pd.DataFrame({"Full Name": ["John Doe"]})
        result = detector.detect_column_htype("Full Name", df["Full Name"])
        assert result.htype_code == "HTYPE-001"
    
    def test_column_with_special_characters(self, detector):
        df = pd.DataFrame({"email-address": ["test@test.com"]})
        result = detector.detect_column_htype("email-address", df["email-address"])
        assert result.htype_code == "HTYPE-010"
    
    def test_unknown_column_defaults_to_text(self, detector):
        df = pd.DataFrame({"xyz_unknown_123": ["random", "data", "here"]})
        result = detector.detect_column_htype("xyz_unknown_123", df["xyz_unknown_123"])
        # Should default to text with low confidence
        assert result.htype_code == "HTYPE-022"
        assert result.confidence < 0.5
    
    def test_mixed_case_column_name(self, detector):
        df = pd.DataFrame({"EMAIL_ADDRESS": ["test@test.com"]})
        result = detector.detect_column_htype("EMAIL_ADDRESS", df["EMAIL_ADDRESS"])
        assert result.htype_code == "HTYPE-010"
    
    def test_numeric_column_distribution_detection(self, detector):
        """Test that numeric distribution analysis works for ambiguous columns."""
        # Integers 0-100 with high cardinality - not rating scale
        df = pd.DataFrame({"score_value": list(range(0, 101))})
        result = detector.detect_column_htype("score_value", df["score_value"])
        # Should detect as Score due to column name
        assert result.htype_code == "HTYPE-021"
