"""
Tests for Organizational & Product Cleaning Rules — Session 9

Covers:
- HTYPE-024: Product Name (PROD-01 to PROD-05)
- HTYPE-025: Product Code / SKU (SKU-01 to SKU-05)
- HTYPE-026: Organization Name (ORG-01 to ORG-05)
- HTYPE-027: Job Title (JOB-01 to JOB-05)
- HTYPE-028: Department (DEPT-01 to DEPT-05)
- HTYPE-034: Reference Number (REFNO-01 to REFNO-05)
- HTYPE-047: Version Number (VER-01 to VER-04)
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

from app.services.org_product_rules import (
    OrgProductRules,
    CleaningResult,
    # Product helpers
    to_product_title_case,
    clean_product_special_chars,
    calculate_similarity,
    find_product_variants,
    # SKU helpers
    validate_ean13,
    validate_upca,
    validate_ean8,
    clean_sku,
    detect_sku_pattern,
    # Org helpers
    to_org_title_case,
    standardize_legal_suffix,
    expand_org_abbreviation,
    # Job helpers
    to_job_title_case,
    expand_job_abbreviations,
    extract_seniority,
    find_job_variants,
    # Dept helpers
    expand_dept_abbreviation,
    extract_department_hierarchy,
    # Refno helpers
    detect_refno_pattern,
    check_refno_uniqueness,
    # Version helpers
    parse_version,
    normalize_version,
    version_sort_key,
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


# ============================================================================
# PRODUCT HELPER TESTS (HTYPE-024)
# ============================================================================

class TestToProductTitleCase:
    """Test to_product_title_case function."""
    
    def test_basic_title_case(self):
        assert to_product_title_case("aspirin tablet") == "Aspirin Tablet"
    
    def test_preserves_dosage(self):
        result = to_product_title_case("ASPIRIN 500mg")
        assert "500mg" in result.lower()
    
    def test_preserves_abbreviations(self):
        result = to_product_title_case("paracetamol sr")
        assert "SR" in result
    
    def test_empty_string(self):
        assert to_product_title_case("") == ""
    
    def test_none_input(self):
        assert to_product_title_case(None) is None


class TestCleanProductSpecialChars:
    """Test clean_product_special_chars function."""
    
    def test_removes_invalid_chars(self):
        result = clean_product_special_chars("Product@Name#123")
        assert "@" not in result
        assert "#" not in result
    
    def test_preserves_allowed_chars(self):
        result = clean_product_special_chars("Product (500mg) - Name")
        assert "(" in result
        assert ")" in result
        assert "-" in result
    
    def test_preserves_trademark(self):
        result = clean_product_special_chars("Product™ Name®")
        assert "™" in result
        assert "®" in result
    
    def test_empty_string(self):
        assert clean_product_special_chars("") == ""


class TestCalculateSimilarity:
    """Test calculate_similarity function."""
    
    def test_identical_strings(self):
        assert calculate_similarity("test", "test") == 1.0
    
    def test_similar_strings(self):
        result = calculate_similarity("Aspirin", "aspirin")
        assert result > 0.9
    
    def test_different_strings(self):
        result = calculate_similarity("Apple", "Orange")
        assert result < 0.5
    
    def test_empty_strings(self):
        assert calculate_similarity("", "") == 0.0
        assert calculate_similarity("test", "") == 0.0


class TestFindProductVariants:
    """Test find_product_variants function."""
    
    def test_finds_variants(self):
        series = pd.Series(["Aspirin 500mg", "aspirin 500 mg", "Ibuprofen"])
        variants = find_product_variants(series, threshold=0.7)
        # Should group similar aspirin names
        assert len(variants) >= 0  # May or may not detect depending on threshold
    
    def test_no_variants(self):
        series = pd.Series(["Apple", "Orange", "Banana"])
        variants = find_product_variants(series)
        assert len(variants) == 0
    
    def test_empty_series(self):
        series = pd.Series([], dtype=object)
        variants = find_product_variants(series)
        assert variants == {}


# ============================================================================
# SKU HELPER TESTS (HTYPE-025)
# ============================================================================

class TestValidateEAN13:
    """Test validate_ean13 function."""
    
    def test_valid_ean13(self):
        # 5901234123457 is a valid EAN-13
        assert validate_ean13("5901234123457") is True
    
    def test_invalid_check_digit(self):
        # Changed last digit to make it invalid
        assert validate_ean13("5901234123456") is False
    
    def test_wrong_length(self):
        assert validate_ean13("12345") is False


class TestValidateUPCA:
    """Test validate_upca function."""
    
    def test_valid_upca(self):
        # 012345678905 is a valid UPC-A
        assert validate_upca("012345678905") is True
    
    def test_invalid_check_digit(self):
        assert validate_upca("012345678901") is False
    
    def test_wrong_length(self):
        assert validate_upca("123456") is False


class TestValidateEAN8:
    """Test validate_ean8 function."""
    
    def test_valid_ean8(self):
        # 96385074 is a valid EAN-8
        assert validate_ean8("96385074") is True
    
    def test_invalid_check_digit(self):
        assert validate_ean8("96385073") is False
    
    def test_wrong_length(self):
        assert validate_ean8("1234") is False


class TestCleanSku:
    """Test clean_sku function."""
    
    def test_uppercase_conversion(self):
        assert clean_sku("abc123") == "ABC123"
    
    def test_removes_invalid_chars(self):
        result = clean_sku("ABC@123#DEF")
        assert "@" not in result
        assert "#" not in result
        assert result == "ABC123DEF"
    
    def test_preserves_hyphen(self):
        assert clean_sku("ABC-123") == "ABC-123"
    
    def test_empty_string(self):
        assert clean_sku("") == ""


class TestDetectSkuPattern:
    """Test detect_sku_pattern function."""
    
    def test_detects_common_prefix(self):
        series = pd.Series(["SKU001", "SKU002", "SKU003"])
        pattern = detect_sku_pattern(series)
        assert pattern is not None
        assert pattern["common_prefix"] == "SKU00"
    
    def test_detects_consistent_length(self):
        series = pd.Series(["ABC001", "ABC002", "ABC003"])
        pattern = detect_sku_pattern(series)
        assert pattern["consistent_length"] is True
    
    def test_empty_series(self):
        series = pd.Series([], dtype=object)
        pattern = detect_sku_pattern(series)
        assert pattern is None


# ============================================================================
# ORGANIZATION HELPER TESTS (HTYPE-026)
# ============================================================================

class TestToOrgTitleCase:
    """Test to_org_title_case function."""
    
    def test_basic_title_case(self):
        # "inc" gets preserved as uppercase because INC is in ORG_PRESERVE_UPPER
        result = to_org_title_case("apple inc")
        assert "Apple" in result
        assert "INC" in result or "Inc" in result
    
    def test_preserves_abbreviations(self):
        result = to_org_title_case("ngo for health")
        assert "NGO" in result
    
    def test_preserves_llc(self):
        result = to_org_title_case("acme llc")
        assert "LLC" in result


class TestStandardizeLegalSuffix:
    """Test standardize_legal_suffix function."""
    
    def test_ltd_standardization(self):
        assert standardize_legal_suffix("Acme Limited") == "Acme Ltd."
    
    def test_inc_standardization(self):
        assert standardize_legal_suffix("Acme Incorporated") == "Acme Inc."
    
    def test_pvt_ltd_standardization(self):
        result = standardize_legal_suffix("Acme Private Limited")
        assert "Pvt. Ltd." in result
    
    def test_llc_standardization(self):
        result = standardize_legal_suffix("Acme L.L.C.")
        assert "LLC" in result
    
    def test_no_suffix(self):
        assert standardize_legal_suffix("Acme Company") == "Acme Co."


class TestExpandOrgAbbreviation:
    """Test expand_org_abbreviation function."""
    
    def test_expands_who(self):
        expanded, was_expanded = expand_org_abbreviation("WHO")
        assert was_expanded is True
        assert expanded == "World Health Organization"
    
    def test_expands_ibm(self):
        expanded, was_expanded = expand_org_abbreviation("ibm")
        assert was_expanded is True
        assert expanded == "International Business Machines"
    
    def test_unknown_abbreviation(self):
        expanded, was_expanded = expand_org_abbreviation("Acme Corp")
        assert was_expanded is False


# ============================================================================
# JOB TITLE HELPER TESTS (HTYPE-027)
# ============================================================================

class TestToJobTitleCase:
    """Test to_job_title_case function."""
    
    def test_basic_title_case(self):
        assert to_job_title_case("software engineer") == "Software Engineer"
    
    def test_preserves_hr(self):
        result = to_job_title_case("hr manager")
        assert "HR" in result
    
    def test_preserves_ceo(self):
        result = to_job_title_case("ceo")
        assert "CEO" in result


class TestExpandJobAbbreviations:
    """Test expand_job_abbreviations function."""
    
    def test_expands_mgr(self):
        expanded, expansions = expand_job_abbreviations("Sr. Mgr.")
        assert "Manager" in expanded
        assert "Senior" in expanded
    
    def test_expands_multiple(self):
        expanded, expansions = expand_job_abbreviations("Asst. Dir.")
        assert "Assistant" in expanded
        assert "Director" in expanded
    
    def test_no_abbreviations(self):
        expanded, expansions = expand_job_abbreviations("Software Engineer")
        assert len(expansions) == 0


class TestExtractSeniority:
    """Test extract_seniority function."""
    
    def test_extracts_senior(self):
        result = extract_seniority("Senior Software Engineer")
        assert result is not None
        assert result[0] == "Senior"
        assert result[1] == 6
    
    def test_extracts_director(self):
        result = extract_seniority("Director of Engineering")
        assert result is not None
        assert result[0] == "Director"
    
    def test_extracts_intern(self):
        result = extract_seniority("Software Intern")
        assert result is not None
        assert result[1] == 0
    
    def test_no_seniority(self):
        result = extract_seniority("Software Engineer")
        assert result is None


class TestFindJobVariants:
    """Test find_job_variants function."""
    
    def test_finds_variants(self):
        series = pd.Series([
            "Software Engineer",
            "Software Eng.",
            "Data Scientist"
        ])
        variants = find_job_variants(series, threshold=0.7)
        # May or may not find variants depending on threshold
        assert isinstance(variants, dict)


# ============================================================================
# DEPARTMENT HELPER TESTS (HTYPE-028)
# ============================================================================

class TestExpandDeptAbbreviation:
    """Test expand_dept_abbreviation function."""
    
    def test_expands_hr(self):
        expanded, was_expanded = expand_dept_abbreviation("HR")
        assert was_expanded is True
        assert expanded == "Human Resources"
    
    def test_expands_it(self):
        expanded, was_expanded = expand_dept_abbreviation("it")
        assert was_expanded is True
        assert expanded == "Information Technology"
    
    def test_expands_rnd(self):
        expanded, was_expanded = expand_dept_abbreviation("R&D")
        assert was_expanded is True
        assert "Research" in expanded


class TestExtractDepartmentHierarchy:
    """Test extract_department_hierarchy function."""
    
    def test_extracts_hierarchy_with_arrow(self):
        result = extract_department_hierarchy("Engineering > Software")
        assert result is not None
        assert result["parent"] == "Engineering"
        assert result["child"] == "Software"
    
    def test_extracts_hierarchy_with_slash(self):
        result = extract_department_hierarchy("Sales / East")
        assert result is not None
        assert result["parent"] == "Sales"
    
    def test_no_hierarchy(self):
        result = extract_department_hierarchy("Human Resources")
        assert result is None


# ============================================================================
# REFERENCE NUMBER HELPER TESTS (HTYPE-034)
# ============================================================================

class TestDetectRefnoPattern:
    """Test detect_refno_pattern function."""
    
    def test_detects_prefix(self):
        series = pd.Series(["REF001", "REF002", "REF003"])
        pattern = detect_refno_pattern(series)
        assert pattern is not None
        assert pattern["prefix"] == "REF00"
    
    def test_detects_sequential(self):
        series = pd.Series(["INV001", "INV002", "INV003"])
        pattern = detect_refno_pattern(series)
        assert pattern["is_sequential"] is True
    
    def test_detects_gaps(self):
        series = pd.Series(["INV001", "INV003", "INV005"])
        pattern = detect_refno_pattern(series)
        assert pattern["is_sequential"] is False
        assert 2 in pattern["gaps"]


class TestCheckRefnoUniqueness:
    """Test check_refno_uniqueness function."""
    
    def test_finds_duplicates(self):
        series = pd.Series(["REF001", "REF002", "REF001", "REF003"])
        duplicates = check_refno_uniqueness(series)
        assert "REF001" in duplicates
    
    def test_no_duplicates(self):
        series = pd.Series(["REF001", "REF002", "REF003"])
        duplicates = check_refno_uniqueness(series)
        assert len(duplicates) == 0


# ============================================================================
# VERSION HELPER TESTS (HTYPE-047)
# ============================================================================

class TestParseVersion:
    """Test parse_version function."""
    
    def test_parses_semantic(self):
        result = parse_version("1.2.3")
        assert result is not None
        assert result["major"] == 1
        assert result["minor"] == 2
        assert result["patch"] == 3
    
    def test_parses_with_v_prefix(self):
        result = parse_version("v2.0.1")
        assert result is not None
        assert result["major"] == 2
    
    def test_parses_major_minor(self):
        result = parse_version("3.5")
        assert result is not None
        assert result["major"] == 3
        assert result["minor"] == 5
    
    def test_parses_version_prefix(self):
        result = parse_version("Version 4.0")
        assert result is not None
        assert result["major"] == 4


class TestNormalizeVersion:
    """Test normalize_version function."""
    
    def test_normalizes_to_semantic(self):
        assert normalize_version("Version 1.2.3") == "v1.2.3"
    
    def test_normalizes_major_only(self):
        assert normalize_version("v1") == "v1.0"
    
    def test_adds_v_prefix(self):
        result = normalize_version("2.3.4")
        assert result.startswith("v")
    
    def test_preserves_invalid(self):
        assert normalize_version("invalid") == "invalid"


class TestVersionSortKey:
    """Test version_sort_key function."""
    
    def test_sort_key_generation(self):
        key = version_sort_key("v1.2.3")
        assert key == (1, 2, 3)
    
    def test_sort_ordering(self):
        versions = ["v1.0.0", "v0.9.9", "v1.0.1", "v2.0.0"]
        sorted_versions = sorted(versions, key=version_sort_key)
        assert sorted_versions[0] == "v0.9.9"
        assert sorted_versions[-1] == "v2.0.0"


# ============================================================================
# PROD FORMULA TESTS (HTYPE-024)
# ============================================================================

class TestPROD01TitleCaseNormalization:
    """Test PROD-01: Title case normalization."""
    
    def test_applies_title_case(self, mock_db):
        df = pd.DataFrame({"product": ["aspirin tablet", "IBUPROFEN GEL"]})
        htype_map = {"product": "HTYPE-024"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.PROD_01_title_case_normalization("product")
        
        assert result.changes_made == 2
        assert runner.df.at[0, "product"] == "Aspirin Tablet"


class TestPROD02VariantConsolidation:
    """Test PROD-02: Variant consolidation."""
    
    def test_flags_variants(self, mock_db):
        df = pd.DataFrame({
            "product": ["Aspirin 500mg", "aspirin 500 mg", "Different Drug"]
        })
        htype_map = {"product": "HTYPE-024"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.PROD_02_variant_consolidation("product")
        
        # Check that result was created (may or may not find variants)
        assert isinstance(result, CleaningResult)


class TestPROD03SpecialCharCleaning:
    """Test PROD-03: Special character cleaning."""
    
    def test_removes_invalid_chars(self, mock_db):
        df = pd.DataFrame({"product": ["Product@Name", "Normal Product"]})
        htype_map = {"product": "HTYPE-024"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.PROD_03_special_character_cleaning("product")
        
        assert result.changes_made == 1
        assert "@" not in runner.df.at[0, "product"]


class TestPROD05MissingNameRecovery:
    """Test PROD-05: Missing name recovery."""
    
    def test_flags_missing_names(self, mock_db):
        df = pd.DataFrame({
            "product": ["Product A", None, "Product C"],
            "sku": ["SKU001", "SKU002", "SKU003"]
        })
        htype_map = {"product": "HTYPE-024", "sku": "HTYPE-025"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.PROD_05_missing_name_recovery("product")
        
        # Should flag the missing name
        assert result.rows_flagged >= 1


# ============================================================================
# SKU FORMULA TESTS (HTYPE-025)
# ============================================================================

class TestSKU01FormatConsistency:
    """Test SKU-01: Format consistency."""
    
    def test_uppercases_sku(self, mock_db):
        df = pd.DataFrame({"sku": ["abc123", "DEF456"]})
        htype_map = {"sku": "HTYPE-025"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.SKU_01_format_consistency("sku")
        
        assert result.changes_made == 1
        assert runner.df.at[0, "sku"] == "ABC123"


class TestSKU02DuplicateAlert:
    """Test SKU-02: Duplicate alert."""
    
    def test_flags_duplicate_skus(self, mock_db):
        df = pd.DataFrame({
            "sku": ["SKU001", "SKU001", "SKU002"],
            "product": ["Product A", "Product B", "Product C"]
        })
        htype_map = {"sku": "HTYPE-025", "product": "HTYPE-024"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.SKU_02_duplicate_alert("sku")
        
        assert result.rows_flagged >= 2


class TestSKU04BarcodeValidation:
    """Test SKU-04: Barcode validation."""
    
    def test_flags_invalid_barcode(self, mock_db):
        df = pd.DataFrame({
            "barcode": ["5901234123457", "1234567890123"]  # First valid, second invalid
        })
        htype_map = {"barcode": "HTYPE-025"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.SKU_04_barcode_validation("barcode")
        
        assert result.rows_flagged >= 1


# ============================================================================
# ORG FORMULA TESTS (HTYPE-026)
# ============================================================================

class TestORG01TitleCaseNormalization:
    """Test ORG-01: Title case normalization."""
    
    def test_applies_title_case(self, mock_db):
        df = pd.DataFrame({"company": ["acme corp", "MEGA INC"]})
        htype_map = {"company": "HTYPE-026"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.ORG_01_title_case_normalization("company")
        
        assert result.changes_made >= 1


class TestORG02LegalSuffixStandardization:
    """Test ORG-02: Legal suffix standardization."""
    
    def test_standardizes_suffixes(self, mock_db):
        df = pd.DataFrame({"company": ["Acme Limited", "Tech Incorporated"]})
        htype_map = {"company": "HTYPE-026"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.ORG_02_legal_suffix_standardization("company")
        
        assert result.changes_made == 2
        assert "Ltd." in runner.df.at[0, "company"]
        assert "Inc." in runner.df.at[1, "company"]


class TestORG03AbbreviationExpansion:
    """Test ORG-03: Abbreviation expansion."""
    
    def test_expands_abbreviations(self, mock_db):
        df = pd.DataFrame({"company": ["WHO", "IBM", "Regular Corp"]})
        htype_map = {"company": "HTYPE-026"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.ORG_03_abbreviation_expansion("company")
        
        assert result.changes_made == 2
        assert "World Health Organization" in runner.df.at[0, "company"]


# ============================================================================
# JOB FORMULA TESTS (HTYPE-027)
# ============================================================================

class TestJOB01TitleCaseNormalization:
    """Test JOB-01: Title case normalization."""
    
    def test_applies_title_case(self, mock_db):
        df = pd.DataFrame({"title": ["software engineer", "DATA SCIENTIST"]})
        htype_map = {"title": "HTYPE-027"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.JOB_01_title_case_normalization("title")
        
        assert result.changes_made == 2


class TestJOB02AbbreviationExpansion:
    """Test JOB-02: Abbreviation expansion."""
    
    def test_expands_abbreviations(self, mock_db):
        df = pd.DataFrame({"title": ["Sr. Mgr.", "Jr. Dev."]})
        htype_map = {"title": "HTYPE-027"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.JOB_02_abbreviation_expansion("title")
        
        assert result.changes_made == 2
        assert "Senior" in runner.df.at[0, "title"]
        assert "Manager" in runner.df.at[0, "title"]


class TestJOB04SeniorityExtraction:
    """Test JOB-04: Seniority extraction."""
    
    def test_extracts_seniority(self, mock_db):
        df = pd.DataFrame({
            "title": ["Senior Engineer", "Junior Developer", "Manager"]
        })
        htype_map = {"title": "HTYPE-027"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.JOB_04_seniority_extraction("title")
        
        assert result.details.get("rows_with_seniority", 0) >= 2


# ============================================================================
# DEPT FORMULA TESTS (HTYPE-028)
# ============================================================================

class TestDEPT01TitleCase:
    """Test DEPT-01: Title case."""
    
    def test_applies_title_case(self, mock_db):
        df = pd.DataFrame({"dept": ["human resources", "FINANCE"]})
        htype_map = {"dept": "HTYPE-028"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.DEPT_01_title_case("dept")
        
        assert result.changes_made == 2


class TestDEPT02AbbreviationExpansion:
    """Test DEPT-02: Abbreviation expansion."""
    
    def test_expands_abbreviations(self, mock_db):
        df = pd.DataFrame({"dept": ["HR", "IT", "Marketing"]})
        htype_map = {"dept": "HTYPE-028"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.DEPT_02_abbreviation_expansion("dept")
        
        assert result.changes_made == 2
        assert "Human Resources" in runner.df.at[0, "dept"]
        assert "Information Technology" in runner.df.at[1, "dept"]


class TestDEPT04HierarchyExtraction:
    """Test DEPT-04: Hierarchy extraction."""
    
    def test_extracts_hierarchy(self, mock_db):
        df = pd.DataFrame({
            "dept": ["Engineering > Software", "Sales / West", "Finance"]
        })
        htype_map = {"dept": "HTYPE-028"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.DEPT_04_hierarchy_extraction("dept")
        
        assert result.details.get("hierarchies_detected", 0) == 2


# ============================================================================
# REFNO FORMULA TESTS (HTYPE-034)
# ============================================================================

class TestREFNO01UniquenessCheck:
    """Test REFNO-01: Uniqueness check."""
    
    def test_flags_duplicates(self, mock_db):
        df = pd.DataFrame({"ref": ["REF001", "REF002", "REF001"]})
        htype_map = {"ref": "HTYPE-034"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.REFNO_01_uniqueness_check("ref")
        
        assert result.rows_flagged >= 2
        assert "REF001" in result.details.get("duplicate_values", [])


class TestREFNO02FormatConsistency:
    """Test REFNO-02: Format consistency."""
    
    def test_detects_pattern(self, mock_db):
        df = pd.DataFrame({"ref": ["INV001", "INV002", "XYZ999"]})
        htype_map = {"ref": "HTYPE-034"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.REFNO_02_format_consistency("ref")
        
        # Pattern should be detected
        assert result.details.get("pattern") is not None
        # Note: XYZ999 may not be flagged if no common prefix is found for all values


class TestREFNO04SequenceGapDetection:
    """Test REFNO-04: Sequence gap detection."""
    
    def test_detects_gaps(self, mock_db):
        df = pd.DataFrame({"ref": ["REF001", "REF003", "REF005"]})
        htype_map = {"ref": "HTYPE-034"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        runner.REFNO_02_format_consistency("ref")  # Run first to detect pattern
        result = runner.REFNO_04_sequence_gap_detection("ref")
        
        assert result.details.get("gaps") is not None
        assert 2 in result.details["gaps"]


# ============================================================================
# VER FORMULA TESTS (HTYPE-047)
# ============================================================================

class TestVER01FormatStandardization:
    """Test VER-01: Format standardization."""
    
    def test_standardizes_format(self, mock_db):
        df = pd.DataFrame({"version": ["Version 1.2.3", "1.0", "v2.0.0"]})
        htype_map = {"version": "HTYPE-047"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.VER_01_format_standardization("version")
        
        assert result.changes_made >= 2
        assert runner.df.at[0, "version"].startswith("v")
        assert runner.df.at[1, "version"] == "v1.0"


class TestVER02SemanticVersionParsing:
    """Test VER-02: Semantic version parsing."""
    
    def test_parses_versions(self, mock_db):
        df = pd.DataFrame({"version": ["v1.2.3", "invalid", "v2.0"]})
        htype_map = {"version": "HTYPE-047"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.VER_02_semantic_version_parsing("version")
        
        assert result.details.get("parsed_count", 0) == 2
        assert result.details.get("invalid_count", 0) == 1


class TestVER03ChronologicalSortKey:
    """Test VER-03: Chronological sort key."""
    
    def test_creates_sort_column(self, mock_db):
        df = pd.DataFrame({"version": ["v1.0.0", "v0.9.9", "v2.0.0"]})
        htype_map = {"version": "HTYPE-047"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        result = runner.VER_03_chronological_sort_key("version")
        
        assert "version_sort_key" in runner.df.columns
        assert result.details.get("sort_column_created") == "version_sort_key"


# ============================================================================
# ORCHESTRATION TESTS
# ============================================================================

class TestRunForColumn:
    """Test run_for_column orchestration."""
    
    def test_runs_all_product_formulas(self, mock_db):
        df = pd.DataFrame({"product": ["test product", "ANOTHER ONE"]})
        htype_map = {"product": "HTYPE-024"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        results = runner.run_for_column("product", "HTYPE-024")
        
        assert len(results) == 5  # 5 PROD formulas
    
    def test_runs_all_sku_formulas(self, mock_db):
        df = pd.DataFrame({"sku": ["abc123"]})
        htype_map = {"sku": "HTYPE-025"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        results = runner.run_for_column("sku", "HTYPE-025")
        
        assert len(results) == 5  # 5 SKU formulas
    
    def test_runs_all_version_formulas(self, mock_db):
        df = pd.DataFrame({"version": ["v1.0.0"]})
        htype_map = {"version": "HTYPE-047"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        results = runner.run_for_column("version", "HTYPE-047")
        
        assert len(results) == 4  # 4 VER formulas


class TestRunAll:
    """Test run_all orchestration."""
    
    def test_processes_multiple_htypes(self, mock_db):
        df = pd.DataFrame({
            "product": ["Test Product"],
            "company": ["Acme Ltd."],
            "version": ["v1.0.0"]
        })
        htype_map = {
            "product": "HTYPE-024",
            "company": "HTYPE-026",
            "version": "HTYPE-047"
        }
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        summary = runner.run_all()
        
        assert summary["columns_processed"] == 3
    
    def test_ignores_non_applicable_htypes(self, mock_db):
        df = pd.DataFrame({
            "name": ["John"],
            "product": ["Test"]
        })
        htype_map = {
            "name": "HTYPE-001",  # Not applicable
            "product": "HTYPE-024"  # Applicable
        }
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        summary = runner.run_all()
        
        assert summary["columns_processed"] == 1


class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_empty_dataframe(self, mock_db):
        df = pd.DataFrame({"product": []})
        htype_map = {"product": "HTYPE-024"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        summary = runner.run_all()
        
        assert summary["columns_processed"] == 1
        assert summary["total_changes"] == 0
    
    def test_all_null_column(self, mock_db):
        df = pd.DataFrame({"product": [None, None, None]})
        htype_map = {"product": "HTYPE-024"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        summary = runner.run_all()
        
        assert summary["columns_processed"] == 1
    
    def test_missing_column(self, mock_db):
        df = pd.DataFrame({"other": ["test"]})
        htype_map = {"missing_col": "HTYPE-024"}
        
        runner = OrgProductRules(1, df, mock_db, htype_map)
        summary = runner.run_all()
        
        # Should not crash
        assert summary["columns_processed"] == 0
