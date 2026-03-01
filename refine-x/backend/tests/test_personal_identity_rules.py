"""
Tests for Session 4 — Personal & Identity Rules

Covers:
- FNAME formulas (14 formulas for HTYPE-001 Full Name)
- SNAME formulas (9 formulas for HTYPE-002 First/Last/Middle Name)  
- UID formulas (11 formulas for HTYPE-003 Unique ID)
- AGE formulas (11 formulas for HTYPE-007 Age)
- GEN formulas (8 formulas for HTYPE-008 Gender)
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch

# Import the module under test
import sys
sys.path.insert(0, ".")

from app.services.personal_identity_rules import (
    PersonalIdentityRules,
    word_to_number,
    is_placeholder,
    strip_salutation,
    extract_suffix,
    normalize_name_case,
    clean_whitespace,
    levenshtein_distance,
    detect_name_swap,
    calculate_numeric_ratio,
    is_initials_only,
    WORD_TO_NUMBER,
    WORD_TYPOS,
)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestWordToNumber:
    """Tests for word-to-number conversion (AGE-01 foundation)."""
    
    def test_basic_numbers(self):
        assert word_to_number("zero") == 0
        assert word_to_number("one") == 1
        assert word_to_number("ten") == 10
        assert word_to_number("fifteen") == 15
        assert word_to_number("twenty") == 20
        assert word_to_number("ninety") == 90
    
    def test_compound_numbers_space(self):
        assert word_to_number("twenty one") == 21
        assert word_to_number("thirty five") == 35
        assert word_to_number("forty two") == 42
        assert word_to_number("ninety nine") == 99
    
    def test_compound_numbers_hyphen(self):
        assert word_to_number("twenty-one") == 21
        assert word_to_number("thirty-five") == 35
        assert word_to_number("forty-two") == 42
    
    def test_with_hundred(self):
        assert word_to_number("hundred") == 100
        assert word_to_number("one hundred") == 100
        assert word_to_number("one hundred and twenty") == 120
        assert word_to_number("two hundred") == 200
    
    def test_typo_correction(self):
        assert word_to_number("elven") == 11  # elven -> eleven
        assert word_to_number("twleve") == 12  # twleve -> twelve
        assert word_to_number("forteen") == 14  # forteen -> fourteen
        assert word_to_number("fourty") == 40  # fourty -> forty
        assert word_to_number("ninty") == 90  # ninty -> ninety
    
    def test_case_insensitive(self):
        assert word_to_number("TWENTY") == 20
        assert word_to_number("Twenty One") == 21
        assert word_to_number("FIFTY FIVE") == 55
    
    def test_invalid_returns_none(self):
        assert word_to_number("hello") is None
        assert word_to_number("") is None
        assert word_to_number(None) is None
        assert word_to_number("123") is None  # Already numeric


class TestIsPlaceholder:
    """Tests for placeholder detection."""
    
    def test_common_placeholders(self):
        assert is_placeholder("n/a") is True
        assert is_placeholder("N/A") is True
        assert is_placeholder("null") is True
        assert is_placeholder("NULL") is True
        assert is_placeholder("none") is True
        assert is_placeholder("unknown") is True
        assert is_placeholder("test") is True
        assert is_placeholder("xxx") is True
        assert is_placeholder("---") is True
        assert is_placeholder("tbd") is True
    
    def test_valid_values(self):
        assert is_placeholder("John") is False
        assert is_placeholder("123") is False
        assert is_placeholder("Active") is False
    
    def test_nan_is_placeholder(self):
        assert is_placeholder(np.nan) is True
        assert is_placeholder(None) is True


class TestStripSalutation:
    """Tests for salutation stripping (FNAME-03)."""
    
    def test_mr(self):
        name, sal = strip_salutation("Mr. John Smith")
        assert name == "John Smith"
        assert sal == "Mr."
    
    def test_mrs(self):
        name, sal = strip_salutation("Mrs. Jane Doe")
        assert name == "Jane Doe"
        assert sal == "Mrs."
    
    def test_dr(self):
        name, sal = strip_salutation("Dr. Emily Chen")
        assert name == "Emily Chen"
        assert sal == "Dr."
    
    def test_no_salutation(self):
        name, sal = strip_salutation("John Smith")
        assert name == "John Smith"
        assert sal is None
    
    def test_multiple_words(self):
        name, sal = strip_salutation("Prof. Albert Einstein III")
        assert name == "Albert Einstein III"


class TestExtractSuffix:
    """Tests for suffix extraction (FNAME-14)."""
    
    def test_jr(self):
        name, suffix = extract_suffix("John Smith Jr.")
        assert name == "John Smith"
        assert suffix == "Jr."
    
    def test_sr(self):
        name, suffix = extract_suffix("Robert Brown Sr.")
        assert name == "Robert Brown"
        assert suffix == "Sr."
    
    def test_iii(self):
        name, suffix = extract_suffix("Henry Ford III")
        assert name == "Henry Ford"
        assert suffix == "III"
    
    def test_no_suffix(self):
        name, suffix = extract_suffix("Jane Doe")
        assert name == "Jane Doe"
        assert suffix is None


class TestNormalizeNameCase:
    """Tests for name title case normalization (FNAME-01)."""
    
    def test_basic_title_case(self):
        assert normalize_name_case("john smith") == "John Smith"
        assert normalize_name_case("JANE DOE") == "Jane Doe"
    
    def test_apostrophe_names(self):
        assert normalize_name_case("o'brien") == "O'Brien"
        assert normalize_name_case("d'arcy") == "D'Arcy"
    
    def test_hyphenated_names(self):
        assert normalize_name_case("al-hassan") == "Al-Hassan"
        assert normalize_name_case("marie-claire") == "Marie-Claire"
    
    def test_mc_prefix(self):
        assert normalize_name_case("mcdonald") == "McDonald"
        assert normalize_name_case("mccarthy") == "McCarthy"
    
    def test_mac_prefix(self):
        assert normalize_name_case("macdonald") == "MacDonald"


class TestLevenshteinDistance:
    """Tests for Levenshtein distance (FNAME-11 foundation)."""
    
    def test_identical(self):
        assert levenshtein_distance("hello", "hello") == 0
    
    def test_one_char_diff(self):
        assert levenshtein_distance("hello", "hallo") == 1
    
    def test_two_char_diff(self):
        assert levenshtein_distance("John", "Jon") == 1
        assert levenshtein_distance("Smith", "Smyth") == 1
    
    def test_similar_names(self):
        # Names with distance <= 2 should be flagged
        assert levenshtein_distance("Michael", "Micheal") == 2
        assert levenshtein_distance("Kathrine", "Katherine") == 1


class TestDetectNameSwap:
    """Tests for name swap detection (FNAME-10)."""
    
    def test_swap_detected(self):
        swapped, corrected = detect_name_swap("Doe, John")
        assert swapped is True
        assert corrected == "John Doe"
    
    def test_swap_with_spaces(self):
        swapped, corrected = detect_name_swap("Smith,   Jane")
        assert swapped is True
        assert corrected == "Jane Smith"
    
    def test_no_swap(self):
        swapped, corrected = detect_name_swap("John Doe")
        assert swapped is False
        assert corrected == "John Doe"


class TestCalculateNumericRatio:
    """Tests for numeric ratio calculation (FNAME-05)."""
    
    def test_all_letters(self):
        assert calculate_numeric_ratio("John") == 0.0
    
    def test_all_digits(self):
        assert calculate_numeric_ratio("12345") == 1.0
    
    def test_mixed(self):
        ratio = calculate_numeric_ratio("John123")
        assert 0.4 < ratio < 0.5  # 3/7 = 0.428


class TestIsInitialsOnly:
    """Tests for initials detection (FNAME-09)."""
    
    def test_initials(self):
        assert is_initials_only("J.D.") is True
        assert is_initials_only("A.B.C.") is True
    
    def test_not_initials(self):
        assert is_initials_only("John") is False
        assert is_initials_only("J. Smith") is False


# ============================================================================
# FNAME FORMULA TESTS
# ============================================================================

@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    return db


class TestFNAMEFormulas:
    """Tests for Full Name cleaning formulas (HTYPE-001)."""
    
    def test_fname_01_title_case(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["john smith", "JANE DOE", "o'brien", "mcdonald"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_01_title_case("full_name")
        
        assert rules.df["full_name"].iloc[0] == "John Smith"
        assert rules.df["full_name"].iloc[1] == "Jane Doe"
        assert rules.df["full_name"].iloc[2] == "O'Brien"
        assert rules.df["full_name"].iloc[3] == "McDonald"
        assert result.changes_made == 4
    
    def test_fname_02_whitespace_removal(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["  John Smith  ", "Jane    Doe", "  Test  Name  "]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_02_whitespace_removal("full_name")
        
        assert rules.df["full_name"].iloc[0] == "John Smith"
        assert rules.df["full_name"].iloc[1] == "Jane Doe"
        assert rules.df["full_name"].iloc[2] == "Test Name"
        assert result.changes_made == 3
    
    def test_fname_03_salutation_stripping(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["Mr. John Smith", "Dr. Emily Chen", "Jane Doe"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_03_salutation_stripping("full_name")
        
        assert rules.df["full_name"].iloc[0] == "John Smith"
        assert rules.df["full_name"].iloc[1] == "Emily Chen"
        assert rules.df["full_name"].iloc[2] == "Jane Doe"  # No change
        assert result.changes_made == 2
    
    def test_fname_04_special_char_filter(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John@Smith", "Jane#Doe!", "O'Brien-Smith"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_04_special_char_filter("full_name")
        
        assert rules.df["full_name"].iloc[0] == "JohnSmith"
        assert rules.df["full_name"].iloc[1] == "JaneDoe"
        # O'Brien-Smith should keep apostrophe and hyphen
        assert "'" in rules.df["full_name"].iloc[2]
        assert "-" in rules.df["full_name"].iloc[2]
    
    def test_fname_05_numeric_rejection_flags(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John Smith", "User12345", "J0hn123Sm1th"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_05_numeric_rejection("full_name")
        
        # Should flag rows where >30% is numeric
        assert result.rows_flagged >= 1  # User12345 has >30% digits
        assert result.was_auto_applied is False
        assert len(rules.flags) >= 1
    
    def test_fname_06_placeholder_detection(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John Smith", "N/A", "unknown", "test"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_06_placeholder_detection("full_name")
        
        assert rules.df["full_name"].iloc[0] == "John Smith"
        assert pd.isna(rules.df["full_name"].iloc[1])
        assert pd.isna(rules.df["full_name"].iloc[2])
        assert pd.isna(rules.df["full_name"].iloc[3])
        assert result.changes_made == 3
    
    def test_fname_07_duplicate_detection_flags(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John Smith", "Jane Doe", "John Smith", "Alice Brown"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_07_duplicate_detection("full_name")
        
        assert result.rows_flagged == 2  # Two rows with "John Smith"
        assert result.was_auto_applied is False
    
    def test_fname_08_single_word_alert(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John Smith", "Madonna", "Prince", "Jane Doe"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_08_single_word_alert("full_name")
        
        assert result.rows_flagged == 2  # Madonna, Prince
        assert result.was_auto_applied is False
    
    def test_fname_09_initials_prompt(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John Smith", "J.D.", "A.B.C.", "Jane Doe"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_09_initials_prompt("full_name")
        
        assert result.rows_flagged == 2  # J.D., A.B.C.
    
    def test_fname_10_name_swap(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["Doe, John", "Smith, Jane", "Alice Brown"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_10_name_swap("full_name")
        
        assert rules.df["full_name"].iloc[0] == "John Doe"
        assert rules.df["full_name"].iloc[1] == "Jane Smith"
        assert rules.df["full_name"].iloc[2] == "Alice Brown"  # No change
        assert result.changes_made == 2
    
    def test_fname_11_fuzzy_duplicate(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John Smith", "Jon Smith", "Jane Doe", "Johnn Smith"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_11_fuzzy_duplicate("full_name")
        
        # Should detect John/Jon/Johnn as similar
        assert result.rows_flagged >= 2
    
    def test_fname_14_suffix_separation(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John Smith Jr.", "Robert Brown Sr.", "Jane Doe"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.FNAME_14_suffix_separation("full_name")
        
        assert rules.df["full_name"].iloc[0] == "John Smith"
        assert rules.df["full_name"].iloc[1] == "Robert Brown"
        assert "full_name_suffix" in rules.df.columns
        assert rules.df["full_name_suffix"].iloc[0] == "Jr."
        assert rules.df["full_name_suffix"].iloc[1] == "Sr."


# ============================================================================
# UID FORMULA TESTS
# ============================================================================

class TestUIDFormulas:
    """Tests for Unique ID cleaning formulas (HTYPE-003)."""
    
    def test_uid_01_uniqueness_check_flags(self, mock_db):
        df = pd.DataFrame({
            "user_id": ["001", "002", "001", "003"]
        })
        htype_map = {"user_id": "HTYPE-003"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.UID_01_uniqueness_check("user_id")
        
        assert result.rows_flagged == 2  # Both rows with "001"
        assert result.was_auto_applied is False
        assert len(rules.flags) >= 1
        assert "CRITICAL" in rules.flags[0]["issue"]
    
    def test_uid_02_format_standardization(self, mock_db):
        df = pd.DataFrame({
            "user_id": ["1", "22", "333", "4444"]
        })
        htype_map = {"user_id": "HTYPE-003"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.UID_02_format_standardization("user_id")
        
        # Should zero-pad to max length (4)
        assert rules.df["user_id"].iloc[0] == "0001"
        assert rules.df["user_id"].iloc[1] == "0022"
        assert rules.df["user_id"].iloc[2] == "0333"
        assert rules.df["user_id"].iloc[3] == "4444"
    
    def test_uid_02_format_with_prefix(self, mock_db):
        df = pd.DataFrame({
            "user_id": ["EMP1", "EMP22", "EMP333"]
        })
        htype_map = {"user_id": "HTYPE-003"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.UID_02_format_standardization("user_id")
        
        # Should zero-pad numeric portion
        assert rules.df["user_id"].iloc[0] == "EMP001"
        assert rules.df["user_id"].iloc[1] == "EMP022"
        assert rules.df["user_id"].iloc[2] == "EMP333"
    
    def test_uid_03_prefix_consistency_flags(self, mock_db):
        df = pd.DataFrame({
            "user_id": ["EMP001", "USR002", "EMP003"]
        })
        htype_map = {"user_id": "HTYPE-003"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.UID_03_prefix_consistency("user_id")
        
        # Should flag mixed prefixes
        assert result.rows_flagged > 0
        assert result.was_auto_applied is False
    
    def test_uid_04_leading_zero_preservation(self, mock_db):
        df = pd.DataFrame({
            "user_id": [1, 22, 333]  # Integer type
        })
        htype_map = {"user_id": "HTYPE-003"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.UID_04_leading_zero_preservation("user_id")
        
        # Should convert to string type (object or StringDtype in pandas 3.0)
        assert rules.df["user_id"].dtype in (object, "str", "string")
    
    def test_uid_05_null_id_detection_flags(self, mock_db):
        df = pd.DataFrame({
            "user_id": ["001", None, "003", np.nan]
        })
        htype_map = {"user_id": "HTYPE-003"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.UID_05_null_id_detection("user_id")
        
        assert result.rows_flagged == 2  # Two null IDs
        assert "CRITICAL" in rules.flags[0]["issue"]
    
    def test_uid_08_special_char_cleaning(self, mock_db):
        df = pd.DataFrame({
            "user_id": ["001 ", "0-0-2", "00_3"]
        })
        htype_map = {"user_id": "HTYPE-003"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.UID_08_special_char_cleaning("user_id")
        
        assert rules.df["user_id"].iloc[0] == "001"
        assert rules.df["user_id"].iloc[1] == "002"
        assert rules.df["user_id"].iloc[2] == "003"


# ============================================================================
# AGE FORMULA TESTS
# ============================================================================

class TestAGEFormulas:
    """Tests for Age cleaning formulas (HTYPE-007)."""
    
    def test_age_01_word_to_number(self, mock_db):
        df = pd.DataFrame({
            "age": ["twenty five", "thirty", "forty-two", "15"]
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.AGE_01_word_to_number("age")
        
        assert rules.df["age"].iloc[0] == 25
        assert rules.df["age"].iloc[1] == 30
        assert rules.df["age"].iloc[2] == 42
        assert rules.df["age"].iloc[3] == "15"  # Already numeric, no change
    
    def test_age_01_typo_correction(self, mock_db):
        df = pd.DataFrame({
            "age": ["elven", "twleve", "forteen", "fourty"]
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.AGE_01_word_to_number("age")
        
        assert rules.df["age"].iloc[0] == 11  # elven -> eleven
        assert rules.df["age"].iloc[1] == 12  # twleve -> twelve
        assert rules.df["age"].iloc[2] == 14  # forteen -> fourteen
        assert rules.df["age"].iloc[3] == 40  # fourty -> forty
    
    def test_age_03_numeric_validation_flags(self, mock_db):
        df = pd.DataFrame({
            "age": [25, "thirty", "hello", 40]
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        # First convert words, then validate
        rules.AGE_01_word_to_number("age")
        result = rules.AGE_03_numeric_validation("age")
        
        # "hello" should be flagged
        assert result.rows_flagged >= 1
    
    def test_age_04_range_check_flags(self, mock_db):
        df = pd.DataFrame({
            "age": [25, 150, -5, 200, 85]
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.AGE_04_range_check("age")
        
        # 150, -5, 200 are out of range
        assert result.rows_flagged == 3
    
    def test_age_05_decimal_rounding(self, mock_db):
        df = pd.DataFrame({
            "age": [25.7, 30.3, 1.5, 0.8]
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.AGE_05_decimal_rounding("age")
        
        assert rules.df["age"].iloc[0] == 26  # Rounded up
        assert rules.df["age"].iloc[1] == 30  # Rounded down
        # Infants (<=2) keep 1 decimal
        assert rules.df["age"].iloc[2] == 1.5
        assert rules.df["age"].iloc[3] == 0.8
    
    def test_age_09_negative_rejection_flags(self, mock_db):
        df = pd.DataFrame({
            "age": [25, -5, 30, -10]
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.AGE_09_negative_rejection("age")
        
        assert result.rows_flagged == 2
        assert "CRITICAL" in rules.flags[0]["issue"]
    
    def test_age_10_string_to_int(self, mock_db):
        df = pd.DataFrame({
            "age": ["25", "30", "45"]
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.AGE_10_string_to_int("age")
        
        assert rules.df["age"].iloc[0] == 25
        assert rules.df["age"].iloc[1] == 30
        assert rules.df["age"].iloc[2] == 45
        # Check it's a numeric type (int, np.integer)
        assert isinstance(rules.df["age"].iloc[0], (int, np.integer))


# ============================================================================
# GEN FORMULA TESTS
# ============================================================================

class TestGENFormulas:
    """Tests for Gender cleaning formulas (HTYPE-008)."""
    
    def test_gen_01_binary_standardization(self, mock_db):
        df = pd.DataFrame({
            "gender": ["m", "f", "M", "F", "male", "female", "MALE", "FEMALE"]
        })
        htype_map = {"gender": "HTYPE-008"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.GEN_01_binary_standardization("gender")
        
        assert rules.df["gender"].iloc[0] == "Male"
        assert rules.df["gender"].iloc[1] == "Female"
        assert rules.df["gender"].iloc[2] == "Male"
        assert rules.df["gender"].iloc[3] == "Female"
    
    def test_gen_02_nonbinary_standardization(self, mock_db):
        df = pd.DataFrame({
            "gender": ["non-binary", "nonbinary", "nb", "genderqueer", "other"]
        })
        htype_map = {"gender": "HTYPE-008"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.GEN_02_nonbinary_standardization("gender")
        
        assert rules.df["gender"].iloc[0] == "Non-Binary"
        assert rules.df["gender"].iloc[1] == "Non-Binary"
        assert rules.df["gender"].iloc[2] == "Non-Binary"
        assert rules.df["gender"].iloc[3] == "Non-Binary"
        assert rules.df["gender"].iloc[4] == "Other"
    
    def test_gen_03_refusal_mapping(self, mock_db):
        """V2.0 Critical: Refusal is valid data, not missing."""
        df = pd.DataFrame({
            "gender": [
                "prefer not to say",
                "decline to state",
                "rather not say",
                "private",
                "Male"
            ]
        })
        htype_map = {"gender": "HTYPE-008"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.GEN_03_refusal_mapping("gender")
        
        # All refusal variants should become "Prefer Not to Say"
        assert rules.df["gender"].iloc[0] == "Prefer Not to Say"
        assert rules.df["gender"].iloc[1] == "Prefer Not to Say"
        assert rules.df["gender"].iloc[2] == "Prefer Not to Say"
        assert rules.df["gender"].iloc[3] == "Prefer Not to Say"
        # Should NOT be NaN - it's valid data!
        assert not pd.isna(rules.df["gender"].iloc[0])
    
    def test_gen_04_numeric_code_mapping(self, mock_db):
        df = pd.DataFrame({
            "gender": [1, 2, 3, 4, 0]
        })
        htype_map = {"gender": "HTYPE-008"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = rules.GEN_04_numeric_code_mapping("gender")
        
        assert rules.df["gender"].iloc[0] == "Male"
        assert rules.df["gender"].iloc[1] == "Female"
        assert rules.df["gender"].iloc[2] == "Non-Binary"
        assert rules.df["gender"].iloc[3] == "Prefer Not to Say"
        assert rules.df["gender"].iloc[4] == "Other"
    
    def test_gen_05_invalid_flagging(self, mock_db):
        df = pd.DataFrame({
            "gender": ["Male", "Female", "xyz", "unknown123"]
        })
        htype_map = {"gender": "HTYPE-008"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        # Apply standardization first
        rules.GEN_01_binary_standardization("gender")
        result = rules.GEN_05_invalid_flagging("gender")
        
        # "xyz" and "unknown123" should be flagged
        assert result.rows_flagged == 2


# ============================================================================
# ORCHESTRATION TESTS
# ============================================================================

class TestOrchestration:
    """Tests for running all formulas on appropriate columns."""
    
    def test_run_for_column_htype_001(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["Mr. john  smith", "N/A", "Doe, Jane"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        results = rules.run_for_column("full_name", "HTYPE-001")
        
        # After all FNAME formulas:
        # Row 0: "Mr. john smith" -> "John Smith" (salutation stripped, title case)
        # Row 1: "N/A" -> NaN (placeholder)
        # Row 2: "Doe, Jane" -> "Jane Doe" (name swap)
        assert rules.df["full_name"].iloc[0] == "John Smith"
        assert pd.isna(rules.df["full_name"].iloc[1])
        assert rules.df["full_name"].iloc[2] == "Jane Doe"
    
    def test_run_for_column_htype_007(self, mock_db):
        df = pd.DataFrame({
            "age": ["twenty five", "30.9", "-5"]  # Use 30.9 which rounds to 31 unambiguously
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        results = rules.run_for_column("age", "HTYPE-007")
        
        # Word converted, rounded, negative flagged
        assert rules.df["age"].iloc[0] == 25
        assert rules.df["age"].iloc[1] == 31  # Rounded from 30.9
        # Negative should be flagged
        assert len(rules.flags) >= 1
    
    def test_run_for_column_htype_008(self, mock_db):
        df = pd.DataFrame({
            "gender": ["m", "prefer not to say", 2]
        })
        htype_map = {"gender": "HTYPE-008"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        results = rules.run_for_column("gender", "HTYPE-008")
        
        assert rules.df["gender"].iloc[0] == "Male"
        assert rules.df["gender"].iloc[1] == "Prefer Not to Say"
        assert rules.df["gender"].iloc[2] == "Female"
    
    def test_run_all(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["john smith", "Dr. Jane Doe"],
            "user_id": ["001", "002"],
            "age": ["twenty", "30"],
            "gender": ["m", "f"],
            "other_column": ["foo", "bar"]
        })
        htype_map = {
            "full_name": "HTYPE-001",
            "user_id": "HTYPE-003",
            "age": "HTYPE-007",
            "gender": "HTYPE-008",
            "other_column": "HTYPE-999"  # Not a personal identity type
        }
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        summary = rules.run_all()
        
        # Should have processed 4 columns
        assert summary["columns_processed"] == 4
        assert "personal_identity_rules_applied" in summary
        assert summary["total_changes"] > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_dataframe(self, mock_db):
        df = pd.DataFrame({"full_name": []})
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        summary = rules.run_all()
        
        assert summary["total_changes"] == 0
    
    def test_all_null_column(self, mock_db):
        df = pd.DataFrame({"full_name": [None, np.nan, None]})
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        summary = rules.run_all()
        
        # Should handle gracefully
        assert summary["total_changes"] == 0
    
    def test_mixed_types_age(self, mock_db):
        df = pd.DataFrame({
            "age": [25, "thirty", None, 40.5, "invalid"]
        })
        htype_map = {"age": "HTYPE-007"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        summary = rules.run_all()
        
        # Should convert valid words and flag invalid
        assert rules.df["age"].iloc[1] == 30  # "thirty" converted
        assert len(rules.flags) >= 1  # "invalid" flagged
    
    def test_very_long_name(self, mock_db):
        long_name = "A" * 1000
        df = pd.DataFrame({"full_name": [long_name]})
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        summary = rules.run_all()
        
        # Should handle without crashing
        assert len(rules.df["full_name"].iloc[0]) > 0
    
    def test_unicode_names(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["José García", "François Müller", "北京王"]
        })
        htype_map = {"full_name": "HTYPE-001"}
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        # Should not crash on unicode
        summary = rules.run_all()
        
        # First two should be largely unchanged (already proper case)
        # Just verifying no crash
        assert len(rules.df) == 3
    
    def test_column_not_in_htype_map(self, mock_db):
        df = pd.DataFrame({
            "full_name": ["John Smith"],
            "unknown_col": ["some data"]
        })
        htype_map = {"full_name": "HTYPE-001"}  # unknown_col not mapped
        
        rules = PersonalIdentityRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        summary = rules.run_all()
        
        # Should only process mapped columns
        assert summary["columns_processed"] == 1


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
