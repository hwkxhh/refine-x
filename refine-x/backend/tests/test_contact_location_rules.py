"""
Tests for Contact & Location Cleaning Rules — Session 6

Tests all formulas for:
- HTYPE-009: Phone (PHONE-01 to PHONE-11)
- HTYPE-010: Email (EMAIL-01 to EMAIL-10)
- HTYPE-011: Address (ADDR-01 to ADDR-07)
- HTYPE-012: City (CITY-01 to CITY-06)
- HTYPE-013: Country (CNTRY-01 to CNTRY-06)
- HTYPE-014: Postal Code (POST-01 to POST-05)
- HTYPE-035: Coordinates (GEO-01 to GEO-06)
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock

from app.services.contact_location_rules import (
    # Phone helpers
    extract_digits,
    detect_multi_phone,
    is_phone_placeholder,
    extract_extension,
    detect_country_from_phone,
    format_e164,
    validate_phone_length,
    is_mobile_number,
    # Email helpers
    validate_email_format,
    is_disposable_email,
    is_email_placeholder,
    fix_email_domain_typo,
    split_multiple_emails,
    # Address helpers
    normalize_address_whitespace,
    expand_address_abbreviations,
    is_address_placeholder,
    has_po_box,
    title_case_address,
    # City/Country helpers
    normalize_city,
    normalize_country,
    get_country_name,
    levenshtein_distance,
    fuzzy_match_country,
    # Postal helpers
    validate_postal_code,
    format_us_zip,
    preserve_leading_zeros,
    # Coordinate helpers
    parse_dms_to_decimal,
    validate_latitude,
    validate_longitude,
    normalize_coordinate_precision,
    detect_lat_lng_swap,
    # Main class
    ContactLocationRules,
)


# ============================================================================
# PHONE HELPER TESTS
# ============================================================================

class TestExtractDigits:
    def test_extracts_digits_only(self):
        assert extract_digits("+1 (555) 123-4567") == "+15551234567"
    
    def test_preserves_plus(self):
        assert extract_digits("+977-9812345678").startswith("+")
    
    def test_without_plus(self):
        assert extract_digits("555-123-4567") == "5551234567"
    
    def test_empty_string(self):
        assert extract_digits("") == ""


class TestDetectMultiPhone:
    def test_single_number(self):
        assert len(detect_multi_phone("555-1234567")) == 1
    
    def test_slash_separator(self):
        phones = detect_multi_phone("555-1234567 / 555-7654321")
        assert len(phones) == 2
    
    def test_comma_separator(self):
        phones = detect_multi_phone("555-1234567, 555-7654321")
        assert len(phones) == 2
    
    def test_or_separator(self):
        phones = detect_multi_phone("555-1234567 or 555-7654321")
        assert len(phones) == 2
    
    def test_empty_value(self):
        assert detect_multi_phone("") == []


class TestIsPhonePlaceholder:
    def test_zeros_placeholder(self):
        assert is_phone_placeholder("0000000000") is True
    
    def test_sequence_placeholder(self):
        assert is_phone_placeholder("1234567890") is True
    
    def test_repeated_digits(self):
        assert is_phone_placeholder("9999999999") is True
    
    def test_na_placeholder(self):
        assert is_phone_placeholder("N/A") is True
    
    def test_valid_phone(self):
        assert is_phone_placeholder("555-123-4567") is False


class TestExtractExtension:
    def test_ext_format(self):
        phone, ext = extract_extension("555-1234 ext 42")
        assert ext == "42"
    
    def test_x_format(self):
        phone, ext = extract_extension("555-1234 x123")
        assert ext == "123"
    
    def test_no_extension(self):
        phone, ext = extract_extension("555-1234")
        assert ext is None


class TestDetectCountryFromPhone:
    def test_us_number(self):
        assert detect_country_from_phone("+15551234567") == "US"
    
    def test_nepal_number(self):
        assert detect_country_from_phone("+9779812345678") == "NP"
    
    def test_india_number(self):
        assert detect_country_from_phone("+919876543210") == "IN"
    
    def test_short_number_defaults_us(self):
        # Short numbers without country code default to US
        assert detect_country_from_phone("1234567") == "US"
    
    def test_truly_unknown_country(self):
        # Empty or very short input returns None
        assert detect_country_from_phone("") is None


class TestFormatE164:
    def test_us_format(self):
        assert format_e164("5551234567", "US") == "+15551234567"
    
    def test_already_formatted(self):
        result = format_e164("+15551234567", "US")
        assert result.startswith("+1")


class TestValidatePhoneLength:
    def test_us_valid(self):
        assert validate_phone_length("+15551234567", "US") is True
    
    def test_nepal_valid(self):
        assert validate_phone_length("+9779812345678", "NP") is True
    
    def test_too_short(self):
        assert validate_phone_length("123", "US") is False


class TestIsMobileNumber:
    def test_nepal_mobile(self):
        assert is_mobile_number("+9779812345678", "NP") is True
    
    def test_india_mobile(self):
        assert is_mobile_number("+919876543210", "IN") is True
    
    def test_unknown_country(self):
        assert is_mobile_number("5551234567", None) is None


# ============================================================================
# EMAIL HELPER TESTS
# ============================================================================

class TestValidateEmailFormat:
    def test_valid_email(self):
        assert validate_email_format("john.doe@gmail.com") is True
    
    def test_invalid_no_at(self):
        assert validate_email_format("johndoegmail.com") is False
    
    def test_invalid_no_domain(self):
        assert validate_email_format("john@") is False
    
    def test_null_value(self):
        assert validate_email_format(None) is False


class TestIsDisposableEmail:
    def test_disposable_mailinator(self):
        assert is_disposable_email("test@mailinator.com") is True
    
    def test_disposable_tempmail(self):
        assert is_disposable_email("test@tempmail.com") is True
    
    def test_valid_gmail(self):
        assert is_disposable_email("test@gmail.com") is False


class TestIsEmailPlaceholder:
    def test_test_placeholder(self):
        assert is_email_placeholder("test@test.com") is True
    
    def test_admin_placeholder(self):
        assert is_email_placeholder("admin@admin.com") is True
    
    def test_valid_email(self):
        assert is_email_placeholder("john.doe@company.com") is False


class TestFixEmailDomainTypo:
    def test_gmial_typo(self):
        fixed, original = fix_email_domain_typo("john@gmial.com")
        assert fixed == "john@gmail.com"
        assert original == "gmial.com"
    
    def test_yahooo_typo(self):
        fixed, original = fix_email_domain_typo("john@yahooo.com")
        assert fixed == "john@yahoo.com"
    
    def test_no_typo(self):
        fixed, original = fix_email_domain_typo("john@gmail.com")
        assert original is None


class TestSplitMultipleEmails:
    def test_comma_separated(self):
        emails = split_multiple_emails("a@test.com, b@test.com")
        assert len(emails) == 2
    
    def test_semicolon_separated(self):
        emails = split_multiple_emails("a@test.com; b@test.com")
        assert len(emails) == 2
    
    def test_single_email(self):
        emails = split_multiple_emails("a@test.com")
        assert len(emails) == 1


# ============================================================================
# ADDRESS HELPER TESTS
# ============================================================================

class TestNormalizeAddressWhitespace:
    def test_removes_newlines(self):
        result = normalize_address_whitespace("123 Main St\nApt 4")
        assert "\n" not in result
    
    def test_collapses_spaces(self):
        result = normalize_address_whitespace("123    Main   St")
        assert "    " not in result


class TestExpandAddressAbbreviations:
    def test_st_to_street(self):
        result = expand_address_abbreviations("123 Main St")
        assert "Street" in result
    
    def test_ave_to_avenue(self):
        result = expand_address_abbreviations("456 Park Ave")
        assert "Avenue" in result
    
    def test_apt_to_apartment(self):
        result = expand_address_abbreviations("Apt 5")
        assert "Apartment" in result


class TestIsAddressPlaceholder:
    def test_na_placeholder(self):
        assert is_address_placeholder("N/A") is True
    
    def test_test_address(self):
        assert is_address_placeholder("123 Test St") is True
    
    def test_valid_address(self):
        assert is_address_placeholder("123 Oak Street, Austin") is False


class TestHasPoBox:
    def test_po_box(self):
        assert has_po_box("P.O. Box 123") is True
    
    def test_pobox(self):
        assert has_po_box("PO Box 456") is True
    
    def test_no_po_box(self):
        assert has_po_box("123 Main Street") is False


class TestTitleCaseAddress:
    def test_title_case(self):
        result = title_case_address("123 main street")
        assert result == "123 Main Street"
    
    def test_preserves_abbreviations(self):
        result = title_case_address("123 main st NW")
        assert "NW" in result


# ============================================================================
# CITY/COUNTRY HELPER TESTS
# ============================================================================

class TestNormalizeCity:
    def test_abbreviation_expansion(self):
        assert normalize_city("ktm") == "Kathmandu"
    
    def test_nyc_expansion(self):
        assert normalize_city("NYC") == "New York City"
    
    def test_title_case(self):
        assert normalize_city("kathmandu") == "Kathmandu"


class TestNormalizeCountry:
    def test_usa_variant(self):
        assert normalize_country("USA") == "US"
    
    def test_united_states(self):
        assert normalize_country("United States") == "US"
    
    def test_uk_variant(self):
        assert normalize_country("UK") == "GB"
    
    def test_iso2_passthrough(self):
        assert normalize_country("NP") == "NP"
    
    def test_iso3_conversion(self):
        assert normalize_country("NPL") == "NP"


class TestGetCountryName:
    def test_us_to_name(self):
        assert get_country_name("US") == "United States"
    
    def test_np_to_name(self):
        assert get_country_name("NP") == "Nepal"


class TestLevenshteinDistance:
    def test_identical(self):
        assert levenshtein_distance("test", "test") == 0
    
    def test_one_diff(self):
        assert levenshtein_distance("test", "tset") == 2
    
    def test_typo(self):
        assert levenshtein_distance("Nepal", "Neipal") <= 2


class TestFuzzyMatchCountry:
    def test_typo_match(self):
        assert fuzzy_match_country("Neipal") == "NP"
    
    def test_no_match(self):
        assert fuzzy_match_country("Xyz123") is None


# ============================================================================
# POSTAL CODE HELPER TESTS
# ============================================================================

class TestValidatePostalCode:
    def test_us_5_digit(self):
        assert validate_postal_code("12345", "US") is True
    
    def test_us_zip4(self):
        assert validate_postal_code("12345-6789", "US") is True
    
    def test_uk_format(self):
        assert validate_postal_code("SW1A 1AA", "GB") is True
    
    def test_nepal_format(self):
        assert validate_postal_code("44600", "NP") is True
    
    def test_india_format(self):
        assert validate_postal_code("110001", "IN") is True


class TestFormatUsZip:
    def test_9_digit(self):
        assert format_us_zip("123456789") == "12345-6789"
    
    def test_5_digit(self):
        assert format_us_zip("12345") == "12345"


class TestPreserveLeadingZeros:
    def test_numeric_conversion(self):
        assert preserve_leading_zeros(1234) == "01234"
    
    def test_string_passthrough(self):
        assert preserve_leading_zeros("01234") == "01234"


# ============================================================================
# COORDINATE HELPER TESTS
# ============================================================================

class TestParseDmsToDecimal:
    def test_dms_format(self):
        result = parse_dms_to_decimal("27°42'15\"N")
        assert result is not None
        assert 27.70 <= result <= 27.71
    
    def test_degrees_only(self):
        result = parse_dms_to_decimal("27°N")
        assert result == 27.0
    
    def test_south_negative(self):
        result = parse_dms_to_decimal("27°S")
        assert result == -27.0


class TestValidateLatitude:
    def test_valid_range(self):
        assert validate_latitude(45.5) is True
    
    def test_invalid_too_high(self):
        assert validate_latitude(100) is False
    
    def test_invalid_too_low(self):
        assert validate_latitude(-100) is False


class TestValidateLongitude:
    def test_valid_range(self):
        assert validate_longitude(122.5) is True
    
    def test_invalid_too_high(self):
        assert validate_longitude(200) is False


class TestNormalizeCoordinatePrecision:
    def test_rounds_to_6(self):
        result = normalize_coordinate_precision(27.704166666667, 6)
        assert result == 27.704167


class TestDetectLatLngSwap:
    def test_detects_swap(self):
        assert detect_lat_lng_swap(122.5, 45.5) is True
    
    def test_no_swap(self):
        assert detect_lat_lng_swap(45.5, 122.5) is False


# ============================================================================
# PHONE FORMULA TESTS
# ============================================================================

class TestPhoneFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_PHONE_03_non_numeric_strip(self, mock_db):
        """PHONE-03: Remove formatting characters."""
        df = pd.DataFrame({
            "phone": ["+1 (555) 123-4567", "555.123.4567", "5551234567"]
        })
        htype_map = {"phone": "HTYPE-009"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.PHONE_03_non_numeric_strip("phone")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "phone"] == "+15551234567"
    
    def test_PHONE_07_placeholder_rejection(self, mock_db):
        """PHONE-07: Remove placeholder phones."""
        df = pd.DataFrame({
            "phone": ["5551234567", "0000000000", "1234567890", "N/A"]
        })
        htype_map = {"phone": "HTYPE-009"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.PHONE_07_placeholder_rejection("phone")
        
        assert result.changes_made >= 3
        assert pd.isna(runner.df.loc[1, "phone"])
    
    def test_PHONE_08_extension_separation(self, mock_db):
        """PHONE-08: Separate extension."""
        df = pd.DataFrame({
            "phone": ["555-1234 ext 42", "555-4567"]
        })
        htype_map = {"phone": "HTYPE-009"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.PHONE_08_extension_separation("phone")
        
        assert result.changes_made == 1
        assert "phone_extension" in runner.df.columns
        assert runner.df.loc[0, "phone_extension"] == "42"
    
    def test_PHONE_05_length_validation(self, mock_db):
        """PHONE-05: Flag invalid length."""
        df = pd.DataFrame({
            "phone": ["+15551234567", "123", "55512"]
        })
        htype_map = {"phone": "HTYPE-009"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.PHONE_05_length_validation("phone")
        
        assert result.rows_flagged >= 2


# ============================================================================
# EMAIL FORMULA TESTS
# ============================================================================

class TestEmailFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_EMAIL_01_lowercase(self, mock_db):
        """EMAIL-01: Lowercase normalization."""
        df = pd.DataFrame({
            "email": ["John.Doe@Gmail.COM", "test@test.com"]
        })
        htype_map = {"email": "HTYPE-010"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.EMAIL_01_lowercase_normalization("email")
        
        assert result.changes_made >= 1
        assert runner.df.loc[0, "email"] == "john.doe@gmail.com"
    
    def test_EMAIL_02_format_validation(self, mock_db):
        """EMAIL-02: Flag invalid format."""
        df = pd.DataFrame({
            "email": ["valid@test.com", "invalid-email", "missing@"]
        })
        htype_map = {"email": "HTYPE-010"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.EMAIL_02_format_validation("email")
        
        assert result.rows_flagged >= 2
    
    def test_EMAIL_05_disposable_detection(self, mock_db):
        """EMAIL-05: Flag disposable domains."""
        df = pd.DataFrame({
            "email": ["test@mailinator.com", "valid@gmail.com"]
        })
        htype_map = {"email": "HTYPE-010"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.EMAIL_05_disposable_detection("email")
        
        assert result.rows_flagged >= 1
    
    def test_EMAIL_06_whitespace_removal(self, mock_db):
        """EMAIL-06: Remove internal whitespace."""
        df = pd.DataFrame({
            "email": ["john .doe@gmail.com", "test @ test.com"]
        })
        htype_map = {"email": "HTYPE-010"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.EMAIL_06_whitespace_removal("email")
        
        assert result.changes_made >= 2
        assert " " not in runner.df.loc[0, "email"]
    
    def test_EMAIL_07_placeholder_rejection(self, mock_db):
        """EMAIL-07: Remove placeholder emails."""
        df = pd.DataFrame({
            "email": ["test@test.com", "admin@admin.com", "real@company.com"]
        })
        htype_map = {"email": "HTYPE-010"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.EMAIL_07_placeholder_rejection("email")
        
        assert result.changes_made >= 2
        assert pd.isna(runner.df.loc[0, "email"])


# ============================================================================
# ADDRESS FORMULA TESTS
# ============================================================================

class TestAddressFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_ADDR_01_whitespace_cleanup(self, mock_db):
        """ADDR-01: Normalize whitespace."""
        df = pd.DataFrame({
            "address": ["123 Main St\nApt 4", "456    Oak   Ave"]
        })
        htype_map = {"address": "HTYPE-011"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.ADDR_01_whitespace_cleanup("address")
        
        assert result.changes_made >= 2
        assert "\n" not in runner.df.loc[0, "address"]
    
    def test_ADDR_02_abbreviation_standardization(self, mock_db):
        """ADDR-02: Expand abbreviations."""
        df = pd.DataFrame({
            "address": ["123 Main St", "456 Park Ave"]
        })
        htype_map = {"address": "HTYPE-011"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.ADDR_02_abbreviation_standardization("address")
        
        assert result.changes_made >= 2
        assert "Street" in runner.df.loc[0, "address"]
    
    def test_ADDR_04_placeholder_rejection(self, mock_db):
        """ADDR-04: Remove placeholder addresses."""
        df = pd.DataFrame({
            "address": ["N/A", "123 Test St", "456 Real Street"]
        })
        htype_map = {"address": "HTYPE-011"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.ADDR_04_placeholder_rejection("address")
        
        assert result.changes_made >= 2
        assert pd.isna(runner.df.loc[0, "address"])
    
    def test_ADDR_07_po_box_detection(self, mock_db):
        """ADDR-07: Flag PO Box addresses."""
        df = pd.DataFrame({
            "address": ["P.O. Box 123", "123 Main Street"]
        })
        htype_map = {"address": "HTYPE-011"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.ADDR_07_po_box_detection("address")
        
        assert result.rows_flagged >= 1


# ============================================================================
# CITY FORMULA TESTS
# ============================================================================

class TestCityFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_CITY_01_title_case(self, mock_db):
        """CITY-01: Apply title case."""
        df = pd.DataFrame({
            "city": ["kathmandu", "NEW YORK", "Austin"]
        })
        htype_map = {"city": "HTYPE-012"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.CITY_01_title_case("city")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "city"] == "Kathmandu"
    
    def test_CITY_03_abbreviation_expansion(self, mock_db):
        """CITY-03: Expand city abbreviations."""
        df = pd.DataFrame({
            "city": ["KTM", "NYC", "Austin"]
        })
        htype_map = {"city": "HTYPE-012"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.CITY_03_abbreviation_expansion("city")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "city"] == "Kathmandu"
        assert runner.df.loc[1, "city"] == "New York City"


# ============================================================================
# COUNTRY FORMULA TESTS
# ============================================================================

class TestCountryFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_CNTRY_01_iso_normalization(self, mock_db):
        """CNTRY-01: Normalize to full name."""
        df = pd.DataFrame({
            "country": ["US", "NP", "GB"]
        })
        htype_map = {"country": "HTYPE-013"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.CNTRY_01_iso_normalization("country")
        
        assert result.changes_made >= 3
        assert runner.df.loc[0, "country"] == "United States"
        assert runner.df.loc[1, "country"] == "Nepal"
    
    def test_CNTRY_03_abbreviation_mapping(self, mock_db):
        """CNTRY-03: Map abbreviations."""
        df = pd.DataFrame({
            "country": ["USA", "UK", "Nepal"]
        })
        htype_map = {"country": "HTYPE-013"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.CNTRY_03_abbreviation_mapping("country")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "country"] == "United States"
        assert runner.df.loc[1, "country"] == "United Kingdom"
    
    def test_CNTRY_05_invalid_rejection(self, mock_db):
        """CNTRY-05: Flag invalid countries."""
        df = pd.DataFrame({
            "country": ["Nepal", "InvalidCountry", "XYZ123"]
        })
        htype_map = {"country": "HTYPE-013"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.CNTRY_05_invalid_rejection("country")
        
        assert result.rows_flagged >= 2


# ============================================================================
# POSTAL CODE FORMULA TESTS
# ============================================================================

class TestPostalCodeFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_POST_01_leading_zero_preservation(self, mock_db):
        """POST-01: Preserve leading zeros."""
        df = pd.DataFrame({
            "zip": [1234, 12345, "01234"]
        })
        htype_map = {"zip": "HTYPE-014"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.POST_01_leading_zero_preservation("zip")
        
        assert result.changes_made >= 1
        assert runner.df.loc[0, "zip"] == "01234"
    
    def test_POST_03_hyphen_insertion(self, mock_db):
        """POST-03: Add hyphen to ZIP+4."""
        df = pd.DataFrame({
            "zip": ["123456789", "12345"]
        })
        htype_map = {"zip": "HTYPE-014"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.POST_03_hyphen_insertion("zip")
        
        assert result.changes_made >= 1
        assert runner.df.loc[0, "zip"] == "12345-6789"


# ============================================================================
# COORDINATE FORMULA TESTS
# ============================================================================

class TestCoordinateFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_GEO_01_range_validation(self, mock_db):
        """GEO-01: Flag out-of-range coordinates."""
        df = pd.DataFrame({
            "latitude": [27.7, 100.0, -95.0]
        })
        htype_map = {"latitude": "HTYPE-035"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.GEO_01_range_validation("latitude")
        
        assert result.rows_flagged >= 2
    
    def test_GEO_02_dms_to_decimal(self, mock_db):
        """GEO-02: Convert DMS to decimal."""
        df = pd.DataFrame({
            "latitude": ["27°42'15\"N", "27.7"]
        })
        htype_map = {"latitude": "HTYPE-035"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.GEO_02_dms_to_decimal("latitude")
        
        assert result.changes_made >= 1
        assert isinstance(runner.df.loc[0, "latitude"], float)
    
    def test_GEO_04_precision_normalization(self, mock_db):
        """GEO-04: Normalize precision."""
        df = pd.DataFrame({
            "latitude": [27.70416666666667, 27.7]
        })
        htype_map = {"latitude": "HTYPE-035"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.GEO_04_precision_normalization("latitude")
        
        assert result.changes_made >= 1
        # Check precision is 6 decimal places
        assert len(str(runner.df.loc[0, "latitude"]).split('.')[-1]) <= 6


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestContactLocationRulesIntegration:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_run_all_phone_column(self, mock_db):
        """Test run_all processes phone columns."""
        df = pd.DataFrame({
            "phone": ["+1 (555) 123-4567", "555-987-6543"]
        })
        htype_map = {"phone": "HTYPE-009"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 1
        assert "PHONE-03" in result["formulas_applied"]
    
    def test_run_all_email_column(self, mock_db):
        """Test run_all processes email columns."""
        df = pd.DataFrame({
            "email": ["John.Doe@Gmail.COM", "test@test.com"]
        })
        htype_map = {"email": "HTYPE-010"}
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 1
        assert "EMAIL-01" in result["formulas_applied"]
    
    def test_run_all_multiple_htypes(self, mock_db):
        """Test run_all with multiple contact/location columns."""
        df = pd.DataFrame({
            "phone": ["+1-555-123-4567"],
            "email": ["John@Gmail.COM"],
            "city": ["ktm"],
            "country": ["USA"],
        })
        htype_map = {
            "phone": "HTYPE-009",
            "email": "HTYPE-010",
            "city": "HTYPE-012",
            "country": "HTYPE-013",
        }
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 4
        assert result["total_changes"] > 0
    
    def test_run_all_ignores_non_contact_htypes(self, mock_db):
        """Test run_all ignores non-contact HTYPEs."""
        df = pd.DataFrame({
            "name": ["John Doe"],
            "age": [25],
        })
        htype_map = {
            "name": "HTYPE-001",
            "age": "HTYPE-007",
        }
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 0
    
    def test_flags_are_collected(self, mock_db):
        """Test that flags are properly collected."""
        df = pd.DataFrame({
            "phone": ["123", "555-1234567"],  # First is too short
            "email": ["invalid-email", "valid@test.com"],  # First is invalid
        })
        htype_map = {
            "phone": "HTYPE-009",
            "email": "HTYPE-010",
        }
        
        runner = ContactLocationRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert "total_flags" in result
        assert len(runner.flags) > 0
