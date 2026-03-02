"""
Tests for Medical HTYPE Rules (Session 16)

Tests all DIAG formulas (DIAG-01 through DIAG-07) for HTYPE-031 (Medical Diagnosis)
Tests all PHYS formulas (PHYS-01 through PHYS-08) for HTYPE-032 (Physical Measurement)

Covers:
- Medical abbreviation expansion lookup table
- ICD-10/ICD-11 code validation
- High-sensitivity PII tagging for diagnosis columns
- Unit extraction and standardization
- Imperial-metric conversions
- BMI derivation and categorization
- Biological range validation
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock

from app.services.medical_rules import (
    MedicalRules,
    MedicalFlag,
    SensitivityLevel,
    BMICategory,
    PhysicalMeasurement,
    # DIAG functions
    diag_01_title_case_normalization,
    diag_02_icd_code_validation,
    diag_03_abbreviation_expansion,
    diag_04_typo_detection,
    diag_05_sensitivity_flag,
    diag_06_null_handling,
    diag_07_multiple_diagnoses_split,
    # PHYS functions
    phys_01_unit_extraction,
    phys_02_unit_standardization,
    phys_03_imperial_metric_conversion,
    phys_04_range_validation,
    phys_05_bmi_derivation,
    phys_06_bmi_category_tagging,
    phys_07_decimal_standardization,
    phys_08_null_handling,
    # Helpers
    is_null_or_empty,
    to_title_case,
    extract_measurement,
    calculate_bmi,
    get_bmi_category,
    validate_icd_code,
    is_medical_abbreviation,
    expand_medical_abbreviation,
    detect_multiple_diagnoses,
    # Constants
    MEDICAL_ABBREVIATIONS,
    VALID_RANGES,
    BMI_THRESHOLDS,
)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestIsNullOrEmpty:
    """Tests for is_null_or_empty helper."""
    
    def test_none_is_null(self):
        assert is_null_or_empty(None) is True
    
    def test_nan_is_null(self):
        assert is_null_or_empty(np.nan) is True
    
    def test_empty_string_is_null(self):
        assert is_null_or_empty("") is True
    
    def test_whitespace_is_null(self):
        assert is_null_or_empty("   ") is True
    
    def test_valid_string_not_null(self):
        assert is_null_or_empty("diabetes") is False
    
    def test_zero_not_null(self):
        assert is_null_or_empty(0) is False


class TestToTitleCase:
    """Tests for to_title_case helper."""
    
    def test_basic_title_case(self):
        assert to_title_case("type 2 diabetes") == "Type 2 Diabetes"
    
    def test_preserves_roman_numerals(self):
        result = to_title_case("type ii diabetes mellitus")
        assert "II" in result
    
    def test_handles_numbers(self):
        assert to_title_case("stage 4 cancer") == "Stage 4 Cancer"
    
    def test_empty_string(self):
        assert to_title_case("") == ""
    
    def test_lowercase_words(self):
        result = to_title_case("disease of the heart")
        assert result == "Disease of the Heart"


class TestCalculateBMI:
    """Tests for calculate_bmi helper."""
    
    def test_normal_bmi(self):
        # 70kg, 175cm → BMI ≈ 22.86
        bmi = calculate_bmi(70, 175)
        assert 22.8 <= bmi <= 22.9
    
    def test_underweight_bmi(self):
        # 50kg, 180cm → BMI ≈ 15.43
        bmi = calculate_bmi(50, 180)
        assert bmi < 18.5
    
    def test_obese_bmi(self):
        # 100kg, 170cm → BMI ≈ 34.6
        bmi = calculate_bmi(100, 170)
        assert bmi >= 30
    
    def test_zero_height(self):
        assert calculate_bmi(70, 0) == 0


class TestGetBMICategory:
    """Tests for get_bmi_category helper."""
    
    def test_underweight(self):
        assert get_bmi_category(17.0) == BMICategory.UNDERWEIGHT
    
    def test_normal(self):
        assert get_bmi_category(22.0) == BMICategory.NORMAL
    
    def test_overweight(self):
        assert get_bmi_category(27.0) == BMICategory.OVERWEIGHT
    
    def test_obese(self):
        assert get_bmi_category(35.0) == BMICategory.OBESE
    
    def test_boundary_underweight_normal(self):
        assert get_bmi_category(18.5) == BMICategory.NORMAL
    
    def test_boundary_normal_overweight(self):
        assert get_bmi_category(25.0) == BMICategory.OVERWEIGHT


class TestValidateICDCode:
    """Tests for validate_icd_code helper."""
    
    def test_valid_icd10_simple(self):
        is_valid, version = validate_icd_code("A00")
        assert is_valid is True
        assert version == "ICD-10"
    
    def test_valid_icd10_with_decimal(self):
        is_valid, version = validate_icd_code("E11.9")
        assert is_valid is True
        assert version == "ICD-10"
    
    def test_valid_icd10_z_code(self):
        is_valid, version = validate_icd_code("Z99.9")
        assert is_valid is True
    
    def test_invalid_code(self):
        is_valid, version = validate_icd_code("diabetes")
        assert is_valid is False
    
    def test_empty_code(self):
        is_valid, _ = validate_icd_code("")
        assert is_valid is False


class TestMedicalAbbreviations:
    """Tests for medical abbreviation helpers."""
    
    def test_is_abbreviation_htn(self):
        assert is_medical_abbreviation("HTN") is True
    
    def test_is_abbreviation_lowercase(self):
        assert is_medical_abbreviation("dm") is True
    
    def test_not_abbreviation(self):
        assert is_medical_abbreviation("diabetes") is False
    
    def test_expand_htn(self):
        assert expand_medical_abbreviation("HTN") == "Hypertension"
    
    def test_expand_dm(self):
        assert expand_medical_abbreviation("DM") == "Diabetes Mellitus"
    
    def test_expand_mi(self):
        assert expand_medical_abbreviation("MI") == "Myocardial Infarction"
    
    def test_expand_cva(self):
        assert expand_medical_abbreviation("CVA") == "Cerebrovascular Accident"
    
    def test_expand_copd(self):
        assert expand_medical_abbreviation("COPD") == "Chronic Obstructive Pulmonary Disease"
    
    def test_expand_uti(self):
        assert expand_medical_abbreviation("UTI") == "Urinary Tract Infection"
    
    def test_expand_unknown(self):
        assert expand_medical_abbreviation("XYZ") is None
    
    def test_abbreviations_count(self):
        """Verify comprehensive abbreviation table."""
        assert len(MEDICAL_ABBREVIATIONS) >= 100


class TestDetectMultipleDiagnoses:
    """Tests for detect_multiple_diagnoses helper."""
    
    def test_comma_separated(self):
        result = detect_multiple_diagnoses("Diabetes, Hypertension")
        assert len(result) == 2
        assert "Diabetes" in result
        assert "Hypertension" in result
    
    def test_semicolon_separated(self):
        result = detect_multiple_diagnoses("HTN; DM")
        assert len(result) == 2
    
    def test_and_separated(self):
        result = detect_multiple_diagnoses("Asthma and COPD")
        assert len(result) == 2
    
    def test_single_diagnosis(self):
        result = detect_multiple_diagnoses("Diabetes")
        assert result == []
    
    def test_empty_string(self):
        result = detect_multiple_diagnoses("")
        assert result == []


class TestExtractMeasurement:
    """Tests for extract_measurement helper."""
    
    def test_weight_kg(self):
        from app.services.medical_rules import WEIGHT_PATTERNS
        result = extract_measurement("65 kg", WEIGHT_PATTERNS)
        assert result is not None
        assert result.value == 65
        assert result.unit == 'kg'
    
    def test_weight_lbs(self):
        from app.services.medical_rules import WEIGHT_PATTERNS
        result = extract_measurement("150 lbs", WEIGHT_PATTERNS)
        assert result is not None
        assert result.value == 150
        assert result.unit == 'lb'
    
    def test_height_cm(self):
        from app.services.medical_rules import HEIGHT_PATTERNS
        result = extract_measurement("175 cm", HEIGHT_PATTERNS)
        assert result is not None
        assert result.value == 175
        assert result.unit == 'cm'
    
    def test_height_feet_inches(self):
        from app.services.medical_rules import HEIGHT_PATTERNS
        result = extract_measurement("5'9\"", HEIGHT_PATTERNS)
        assert result is not None
        assert result.unit == 'in'
        assert 68 <= result.value <= 70  # 5*12 + 9 = 69 inches


# ============================================================================
# DIAG-01: TITLE CASE NORMALIZATION
# ============================================================================

class TestDiag01TitleCaseNormalization:
    """Tests for DIAG-01: Title Case Normalization."""
    
    def test_lowercase_normalized(self):
        df = pd.DataFrame({"diagnosis": ["type 2 diabetes", "hypertension"]})
        df, changed = diag_01_title_case_normalization(df, "diagnosis")
        assert df.loc[0, "diagnosis"] == "Type 2 Diabetes"
        assert df.loc[1, "diagnosis"] == "Hypertension"
        assert len(changed) == 2
    
    def test_mixed_case_unchanged(self):
        df = pd.DataFrame({"diagnosis": ["Type 2 Diabetes"]})
        df, changed = diag_01_title_case_normalization(df, "diagnosis")
        assert len(changed) == 0
    
    def test_uppercase_unchanged(self):
        df = pd.DataFrame({"diagnosis": ["DIABETES"]})
        df, changed = diag_01_title_case_normalization(df, "diagnosis")
        # All uppercase is not lowercase, so it's not changed
        assert len(changed) == 0
    
    def test_null_values_skipped(self):
        df = pd.DataFrame({"diagnosis": [None, "asthma"]})
        df, changed = diag_01_title_case_normalization(df, "diagnosis")
        assert len(changed) == 1


# ============================================================================
# DIAG-02: ICD CODE VALIDATION
# ============================================================================

class TestDiag02ICDCodeValidation:
    """Tests for DIAG-02: ICD Code Validation."""
    
    def test_valid_icd_codes_no_flags(self):
        df = pd.DataFrame({"diagnosis": ["E11.9", "I10", "J45.20"]})
        flags = diag_02_icd_code_validation(df, "diagnosis")
        assert len(flags) == 0
    
    def test_invalid_icd_format_flagged(self):
        df = pd.DataFrame({"diagnosis": ["E11.9", "A123456", "J45.20"]})
        flags = diag_02_icd_code_validation(df, "diagnosis")
        # A123456 looks like ICD but is invalid format
        assert len(flags) == 1
        assert 1 in flags[0].row_indices
    
    def test_text_diagnosis_not_flagged(self):
        df = pd.DataFrame({"diagnosis": ["Diabetes", "Hypertension"]})
        flags = diag_02_icd_code_validation(df, "diagnosis")
        # Text diagnoses don't look like ICD codes, so no validation
        assert len(flags) == 0


# ============================================================================
# DIAG-03: ABBREVIATION EXPANSION
# ============================================================================

class TestDiag03AbbreviationExpansion:
    """Tests for DIAG-03: Medical Abbreviation Expansion."""
    
    def test_single_abbreviation(self):
        df = pd.DataFrame({"diagnosis": ["HTN", "DM", "Normal text"]})
        df, changed, flags = diag_03_abbreviation_expansion(df, "diagnosis")
        assert df.loc[0, "diagnosis"] == "Hypertension"
        assert df.loc[1, "diagnosis"] == "Diabetes Mellitus"
        assert df.loc[2, "diagnosis"] == "Normal text"
        assert len(changed) == 2
    
    def test_abbreviation_within_text(self):
        df = pd.DataFrame({"diagnosis": ["Patient has HTN"]})
        df, changed, flags = diag_03_abbreviation_expansion(df, "diagnosis")
        assert "Hypertension" in df.loc[0, "diagnosis"]
    
    def test_multiple_abbreviations(self):
        df = pd.DataFrame({"diagnosis": ["HTN and DM"]})
        df, changed, flags = diag_03_abbreviation_expansion(df, "diagnosis")
        result = df.loc[0, "diagnosis"]
        assert "Hypertension" in result
        assert "Diabetes Mellitus" in result
    
    def test_lowercase_abbreviation(self):
        df = pd.DataFrame({"diagnosis": ["copd"]})
        df, changed, flags = diag_03_abbreviation_expansion(df, "diagnosis")
        assert df.loc[0, "diagnosis"] == "Chronic Obstructive Pulmonary Disease"


# ============================================================================
# DIAG-04: TYPO DETECTION
# ============================================================================

class TestDiag04TypoDetection:
    """Tests for DIAG-04: Typo Detection."""
    
    def test_detects_common_typo(self):
        df = pd.DataFrame({"diagnosis": ["diabeties"]})
        flags = diag_04_typo_detection(df, "diagnosis")
        assert len(flags) == 1
        assert flags[0].requires_confirmation is True
    
    def test_no_typos_no_flags(self):
        df = pd.DataFrame({"diagnosis": ["Diabetes", "Hypertension"]})
        flags = diag_04_typo_detection(df, "diagnosis")
        assert len(flags) == 0
    
    def test_multiple_typos_detected(self):
        df = pd.DataFrame({"diagnosis": ["diabeties", "hypertention"]})
        flags = diag_04_typo_detection(df, "diagnosis")
        assert len(flags) == 1
        assert len(flags[0].row_indices) == 2


# ============================================================================
# DIAG-05: SENSITIVITY FLAG
# ============================================================================

class TestDiag05SensitivityFlag:
    """Tests for DIAG-05: Sensitivity Flag."""
    
    def test_always_returns_flag(self):
        df = pd.DataFrame({"diagnosis": ["Diabetes"]})
        flag = diag_05_sensitivity_flag(df, "diagnosis")
        assert flag is not None
        assert "HIGH SENSITIVITY PII" in flag.issue
    
    def test_flag_covers_all_rows(self):
        df = pd.DataFrame({"diagnosis": ["A", "B", "C", "D", "E"]})
        flag = diag_05_sensitivity_flag(df, "diagnosis")
        assert len(flag.row_indices) == 5


# ============================================================================
# DIAG-06: NULL HANDLING
# ============================================================================

class TestDiag06NullHandling:
    """Tests for DIAG-06: Null Handling."""
    
    def test_null_values_flagged(self):
        df = pd.DataFrame({"diagnosis": [None, "Diabetes", None]})
        df, _, flags = diag_06_null_handling(df, "diagnosis")
        assert len(flags) == 1
        assert len(flags[0].row_indices) == 2
        assert flags[0].requires_confirmation is True
    
    def test_no_nulls_no_flags(self):
        df = pd.DataFrame({"diagnosis": ["A", "B", "C"]})
        df, _, flags = diag_06_null_handling(df, "diagnosis")
        assert len(flags) == 0


# ============================================================================
# DIAG-07: MULTIPLE DIAGNOSES SPLIT
# ============================================================================

class TestDiag07MultipleDiagnosesSplit:
    """Tests for DIAG-07: Multiple Diagnoses Split."""
    
    def test_detects_comma_separated(self):
        df = pd.DataFrame({"diagnosis": ["Diabetes, Hypertension"]})
        flags = diag_07_multiple_diagnoses_split(df, "diagnosis")
        assert len(flags) == 1
        assert flags[0].requires_confirmation is True
    
    def test_single_diagnosis_no_flag(self):
        df = pd.DataFrame({"diagnosis": ["Diabetes"]})
        flags = diag_07_multiple_diagnoses_split(df, "diagnosis")
        assert len(flags) == 0


# ============================================================================
# PHYS-01: UNIT EXTRACTION
# ============================================================================

class TestPhys01UnitExtraction:
    """Tests for PHYS-01: Unit Extraction."""
    
    def test_extracts_weight_units(self):
        df = pd.DataFrame({"weight": ["65 kg", "150 lbs", "70"]})
        df, info = phys_01_unit_extraction(df, "weight")
        assert len(info["extracted_units"]) >= 2
        assert 'kg' in info["extracted_units"]
        assert 'lb' in info["extracted_units"]
    
    def test_extracts_height_units(self):
        df = pd.DataFrame({"height": ["175 cm", "68 in"]})
        df, info = phys_01_unit_extraction(df, "height")
        assert len(info["extracted_units"]) == 2


# ============================================================================
# PHYS-02: UNIT STANDARDIZATION
# ============================================================================

class TestPhys02UnitStandardization:
    """Tests for PHYS-02: Unit Standardization."""
    
    def test_lbs_to_kg(self):
        df = pd.DataFrame({"weight": ["150 lbs"]})
        df, changed = phys_02_unit_standardization(df, "weight")
        assert len(changed) == 1
        # 150 lbs ≈ 68.04 kg
        assert 67 <= float(df.loc[0, "weight"]) <= 69


# ============================================================================
# PHYS-03: IMPERIAL-METRIC CONVERSION
# ============================================================================

class TestPhys03ImperialMetricConversion:
    """Tests for PHYS-03: Imperial-Metric Conversion."""
    
    def test_feet_inches_to_cm(self):
        df = pd.DataFrame({"height": ["5'9\""]})
        df, changed = phys_03_imperial_metric_conversion(df, "height")
        assert len(changed) == 1
        # 5'9" = 175.26 cm
        assert 174 <= float(df.loc[0, "height"]) <= 177
    
    def test_lbs_to_kg(self):
        df = pd.DataFrame({"weight": ["150 lbs"]})
        df, changed = phys_03_imperial_metric_conversion(df, "weight")
        assert len(changed) == 1
        # 150 lbs ≈ 68.04 kg
        assert 67 <= float(df.loc[0, "weight"]) <= 69
    
    def test_fahrenheit_to_celsius(self):
        df = pd.DataFrame({"temperature": ["98.6 F"]})
        df, changed = phys_03_imperial_metric_conversion(df, "temperature")
        assert len(changed) == 1
        # 98.6°F = 37°C
        assert 36.5 <= float(df.loc[0, "temperature"]) <= 37.5


# ============================================================================
# PHYS-04: RANGE VALIDATION
# ============================================================================

class TestPhys04RangeValidation:
    """Tests for PHYS-04: Range Validation."""
    
    def test_valid_weight_no_flags(self):
        df = pd.DataFrame({"weight": [70, 85, 60]})
        flags = phys_04_range_validation(df, "weight")
        assert len(flags) == 0
    
    def test_invalid_weight_flagged(self):
        df = pd.DataFrame({"weight": [70, 600, 0.5]})  # 600 and 0.5 out of range
        flags = phys_04_range_validation(df, "weight")
        assert len(flags) == 1
        assert len(flags[0].row_indices) == 2
    
    def test_valid_height_no_flags(self):
        df = pd.DataFrame({"height": [170, 180, 165]})
        flags = phys_04_range_validation(df, "height")
        assert len(flags) == 0
    
    def test_invalid_height_flagged(self):
        df = pd.DataFrame({"height": [175, 300, 20]})  # 300 and 20 out of range
        flags = phys_04_range_validation(df, "height")
        assert len(flags) == 1
    
    def test_valid_temperature_no_flags(self):
        df = pd.DataFrame({"temperature": [36.5, 37.0, 38.5]})
        flags = phys_04_range_validation(df, "temperature")
        assert len(flags) == 0
    
    def test_invalid_temperature_flagged(self):
        df = pd.DataFrame({"temperature": [37, 50, 25]})  # 50 and 25 out of range
        flags = phys_04_range_validation(df, "temperature")
        assert len(flags) == 1


# ============================================================================
# PHYS-05: BMI DERIVATION
# ============================================================================

class TestPhys05BMIDerivation:
    """Tests for PHYS-05: BMI Derivation."""
    
    def test_derives_bmi(self):
        df = pd.DataFrame({
            "weight": [70, 85],
            "height": [175, 180],
        })
        df, changed = phys_05_bmi_derivation(df, "weight", "height")
        assert "bmi_derived" in df.columns
        assert len(changed) == 2
        # Check BMI values are reasonable
        assert 20 <= df.loc[0, "bmi_derived"] <= 25
        assert 25 <= df.loc[1, "bmi_derived"] <= 30
    
    def test_skips_null_values(self):
        df = pd.DataFrame({
            "weight": [70, None],
            "height": [175, 180],
        })
        df, changed = phys_05_bmi_derivation(df, "weight", "height")
        assert len(changed) == 1
    
    def test_uses_existing_bmi_column(self):
        df = pd.DataFrame({
            "weight": [70],
            "height": [175],
            "bmi": [None],
        })
        df, changed = phys_05_bmi_derivation(df, "weight", "height", "bmi")
        assert df.loc[0, "bmi"] is not None


# ============================================================================
# PHYS-06: BMI CATEGORY TAGGING
# ============================================================================

class TestPhys06BMICategoryTagging:
    """Tests for PHYS-06: BMI Category Tagging."""
    
    def test_tags_categories(self):
        df = pd.DataFrame({
            "bmi": [17.0, 22.0, 27.0, 35.0],
        })
        df, changed = phys_06_bmi_category_tagging(df, "bmi")
        assert "bmi_category" in df.columns
        assert df.loc[0, "bmi_category"] == "Underweight"
        assert df.loc[1, "bmi_category"] == "Normal"
        assert df.loc[2, "bmi_category"] == "Overweight"
        assert df.loc[3, "bmi_category"] == "Obese"


# ============================================================================
# PHYS-07: DECIMAL STANDARDIZATION
# ============================================================================

class TestPhys07DecimalStandardization:
    """Tests for PHYS-07: Decimal Standardization."""
    
    def test_rounds_to_one_decimal(self):
        df = pd.DataFrame({"weight": [70.123, 85.456, 60.789]})
        df, changed = phys_07_decimal_standardization(df, "weight")
        assert df.loc[0, "weight"] == 70.1
        assert df.loc[1, "weight"] == 85.5
        assert df.loc[2, "weight"] == 60.8
        assert len(changed) == 3
    
    def test_already_rounded_unchanged(self):
        df = pd.DataFrame({"weight": [70.0, 85.5]})
        df, changed = phys_07_decimal_standardization(df, "weight")
        assert len(changed) == 0


# ============================================================================
# PHYS-08: NULL HANDLING
# ============================================================================

class TestPhys08NullHandling:
    """Tests for PHYS-08: Null Handling."""
    
    def test_null_values_flagged(self):
        df = pd.DataFrame({"weight": [70, None, 85]})
        flags = phys_08_null_handling(df, "weight")
        assert len(flags) == 1
        assert flags[0].requires_confirmation is True
    
    def test_no_nulls_no_flags(self):
        df = pd.DataFrame({"weight": [70, 75, 80]})
        flags = phys_08_null_handling(df, "weight")
        assert len(flags) == 0


# ============================================================================
# MEDICAL RULES CLASS TESTS
# ============================================================================

class TestMedicalRulesClass:
    """Tests for the MedicalRules orchestrator class."""
    
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
        """Create a sample DataFrame with medical data."""
        return pd.DataFrame({
            "patient_id": [1, 2, 3, 4],
            "diagnosis": ["htn", "DM", "Asthma", None],
            "weight": [70, 150, 85, 65],  # Row 1 is in lbs (high for kg)
            "height": ["175 cm", "5'9\"", "180", "165"],
            "temperature": [37.0, 98.6, 38.5, 36.8],  # Row 1 is Fahrenheit
        })
    
    @pytest.fixture
    def sample_htype_map(self):
        """Create a sample HTYPE map with medical columns."""
        return {
            "patient_id": "HTYPE-005",
            "diagnosis": "HTYPE-031",  # Medical Diagnosis
            "weight": "HTYPE-032",     # Physical Measurement
            "height": "HTYPE-032",     # Physical Measurement
            "temperature": "HTYPE-032",  # Physical Measurement
        }
    
    def test_initialization(self, mock_db, sample_df, sample_htype_map):
        """Test class initialization."""
        runner = MedicalRules(
            job_id=1,
            df=sample_df,
            db=mock_db,
            htype_map=sample_htype_map,
        )
        assert runner.job_id == 1
        assert len(runner.diag_cols) == 1
        assert len(runner.phys_cols) == 3
        assert runner.weight_col == "weight"
        assert runner.height_col == "height"
    
    def test_run_all_returns_summary(self, mock_db, sample_df, sample_htype_map):
        """Test run_all returns comprehensive summary."""
        runner = MedicalRules(
            job_id=1,
            df=sample_df,
            db=mock_db,
            htype_map=sample_htype_map,
        )
        summary = runner.run_all()
        
        assert "medical_rules_applied" in summary
        assert "diag_columns_processed" in summary
        assert "phys_columns_processed" in summary
        assert "total_changes" in summary
        assert "pii_tags" in summary
    
    def test_diagnosis_column_tagged_high_sensitivity(self, mock_db, sample_df, sample_htype_map):
        """Test that diagnosis columns are tagged as high-sensitivity PII."""
        runner = MedicalRules(
            job_id=1,
            df=sample_df,
            db=mock_db,
            htype_map=sample_htype_map,
        )
        runner.run_all()
        
        assert "diagnosis" in runner.pii_tags
        assert runner.pii_tags["diagnosis"]["level"] == "high"
        assert runner.pii_tags["diagnosis"]["ai_processing_excluded"] is True
        assert runner.pii_tags["diagnosis"]["restricted_export"] is True
    
    def test_abbreviations_expanded(self, mock_db, sample_df, sample_htype_map):
        """Test that medical abbreviations are expanded."""
        runner = MedicalRules(
            job_id=1,
            df=sample_df,
            db=mock_db,
            htype_map=sample_htype_map,
        )
        runner.run_all()
        
        # HTN should become Hypertension
        assert runner.df.loc[0, "diagnosis"] == "Hypertension"
        # DM should become Diabetes Mellitus
        assert runner.df.loc[1, "diagnosis"] == "Diabetes Mellitus"
    
    def test_imperial_conversion(self, mock_db, sample_htype_map):
        """Test imperial to metric conversion."""
        df = pd.DataFrame({
            "height": ["5'9\""],
        })
        runner = MedicalRules(
            job_id=1,
            df=df,
            db=mock_db,
            htype_map={"height": "HTYPE-032"},
        )
        runner.run_all()
        
        # 5'9" should become ~175 cm
        height_val = runner.df.loc[0, "height"]
        assert 174 <= float(height_val) <= 177
    
    def test_flags_populated(self, mock_db, sample_df, sample_htype_map):
        """Test that flags are populated."""
        runner = MedicalRules(
            job_id=1,
            df=sample_df,
            db=mock_db,
            htype_map=sample_htype_map,
        )
        runner.run_all()
        
        # Should have sensitivity flag at minimum
        assert len(runner.flags) > 0


# ============================================================================
# EDGE CASE TESTS
# ============================================================================

class TestEdgeCases:
    """Edge case tests for medical rules."""
    
    def test_empty_dataframe(self):
        df = pd.DataFrame({"diagnosis": []})
        df, changed = diag_01_title_case_normalization(df, "diagnosis")
        assert len(changed) == 0
    
    def test_all_null_diagnosis(self):
        df = pd.DataFrame({"diagnosis": [None, None, None]})
        df, changed = diag_01_title_case_normalization(df, "diagnosis")
        assert len(changed) == 0
    
    def test_numeric_values_in_diagnosis(self):
        df = pd.DataFrame({"diagnosis": [123, 456]})
        flags = diag_02_icd_code_validation(df, "diagnosis")
        # Numeric values should be handled gracefully
        assert isinstance(flags, list)
    
    def test_very_long_diagnosis_text(self):
        long_text = "Diabetes Mellitus Type 2 with complications " * 100
        df = pd.DataFrame({"diagnosis": [long_text]})
        df, changed = diag_01_title_case_normalization(df, "diagnosis")
        # Should handle without crashing
        assert isinstance(df, pd.DataFrame)
    
    def test_unicode_in_diagnosis(self):
        df = pd.DataFrame({"diagnosis": ["糖尿病", "高血压"]})
        df, changed = diag_01_title_case_normalization(df, "diagnosis")
        # Should handle unicode without crashing
        assert isinstance(df, pd.DataFrame)
    
    def test_measurement_without_unit(self):
        df = pd.DataFrame({"weight": [70, 85]})
        df, info = phys_01_unit_extraction(df, "weight")
        # Should handle numbers without units
        assert isinstance(info, dict)
    
    def test_negative_measurement(self):
        df = pd.DataFrame({"weight": [-70, 85]})
        flags = phys_04_range_validation(df, "weight")
        # Negative weight should be flagged
        assert len(flags) == 1
        assert 0 in flags[0].row_indices


# ============================================================================
# INTEGRATION TEST
# ============================================================================

class TestIntegration:
    """Integration tests for full medical rules workflow."""
    
    def test_full_medical_workflow(self):
        """Test complete medical rules workflow."""
        df = pd.DataFrame({
            "patient_id": [1, 2, 3, 4, 5],
            "diagnosis": ["htn", "DM, HTN", "copd", "diabeties", None],
            "icd_code": ["I10", "E11.9", "J44.9", "INVALID123", None],
            "weight_kg": [70, 85, 150, 60, 55],  # 150 out of range (likely lbs)
            "height_cm": [175, 180, 165, 170, 160],
            "temperature_c": [37.0, 38.5, 36.8, 50.0, 37.2],  # 50.0 out of range
            "bp": ["120/80", "140/90", "130/85", "90/60", "180/120"],
        })
        
        mock_db = MagicMock()
        mock_db.add = MagicMock()
        mock_db.commit = MagicMock()
        mock_db.rollback = MagicMock()
        
        htype_map = {
            "patient_id": "HTYPE-005",
            "diagnosis": "HTYPE-031",
            "icd_code": "HTYPE-031",
            "weight_kg": "HTYPE-032",
            "height_cm": "HTYPE-032",
            "temperature_c": "HTYPE-032",
            "bp": "HTYPE-032",
        }
        
        runner = MedicalRules(
            job_id=1,
            df=df,
            db=mock_db,
            htype_map=htype_map,
        )
        
        summary = runner.run_all()
        
        # Verify summary structure
        assert summary["diag_columns_processed"] == 2
        assert summary["phys_columns_processed"] == 4
        assert len(summary["high_sensitivity_columns"]) == 2
        
        # Verify abbreviation expansion
        assert runner.df.loc[0, "diagnosis"] == "Hypertension"
        assert "Diabetes Mellitus" in runner.df.loc[1, "diagnosis"]
        assert runner.df.loc[2, "diagnosis"] == "Chronic Obstructive Pulmonary Disease"
        
        # Verify PII tags
        assert "diagnosis" in runner.pii_tags
        assert runner.pii_tags["diagnosis"]["level"] == "high"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
