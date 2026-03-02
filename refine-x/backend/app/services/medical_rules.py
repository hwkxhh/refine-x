"""
Medical HTYPE Rules — Session 16

Implements the DIAG and PHYS formula sets from the Formula Rulebook.

HTYPE-031: Diagnosis / Medical Condition (DIAG-01 through DIAG-07)
HTYPE-032: Weight / Height / Physical Measurement (PHYS-01 through PHYS-08)

CRITICAL: Medical diagnosis columns (HTYPE-031) are HIGH-SENSITIVITY PII.
They must be:
- Tagged for governance with restricted export
- Excluded from AI processing outside this session
- Logged with access audit trail

Logic First. AI Never.
"""

import re
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import pandas as pd
import numpy as np

from app.models.cleaning_log import CleaningLog


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class SensitivityLevel(Enum):
    """PII Sensitivity levels per Appendix F."""
    HIGH = "high"       # Restricted - Medical Diagnosis
    MEDIUM = "medium"   # Personal - Physical Measurements
    LOW = "low"         # Contextual
    NONE = "none"       # Non-PII


class BMICategory(Enum):
    """BMI classification categories."""
    UNDERWEIGHT = "Underweight"
    NORMAL = "Normal"
    OVERWEIGHT = "Overweight"
    OBESE = "Obese"


@dataclass
class MedicalFlag:
    """Flag for user review of medical data issues."""
    formula_id: str
    column: str
    row_indices: List[int]
    issue: str
    suggestion: str
    severity: str = "info"  # info, warning, error
    requires_confirmation: bool = False


@dataclass
class PhysicalMeasurement:
    """Parsed physical measurement with value and unit."""
    value: float
    unit: str
    original: str
    standardized_value: Optional[float] = None
    standardized_unit: Optional[str] = None


# ============================================================================
# MEDICAL ABBREVIATION LOOKUP TABLE (DIAG-03)
# ============================================================================

MEDICAL_ABBREVIATIONS = {
    # Cardiovascular
    "HTN": "Hypertension",
    "HBP": "High Blood Pressure",
    "MI": "Myocardial Infarction",
    "AMI": "Acute Myocardial Infarction",
    "CHF": "Congestive Heart Failure",
    "CAD": "Coronary Artery Disease",
    "CVD": "Cardiovascular Disease",
    "AF": "Atrial Fibrillation",
    "AFIB": "Atrial Fibrillation",
    "DVT": "Deep Vein Thrombosis",
    "PE": "Pulmonary Embolism",
    "PVD": "Peripheral Vascular Disease",
    "AAA": "Abdominal Aortic Aneurysm",
    
    # Neurological
    "CVA": "Cerebrovascular Accident",
    "TIA": "Transient Ischemic Attack",
    "MS": "Multiple Sclerosis",
    "ALS": "Amyotrophic Lateral Sclerosis",
    "PD": "Parkinson's Disease",
    "AD": "Alzheimer's Disease",
    "CP": "Cerebral Palsy",
    "SCI": "Spinal Cord Injury",
    "TBI": "Traumatic Brain Injury",
    
    # Respiratory
    "COPD": "Chronic Obstructive Pulmonary Disease",
    "ARDS": "Acute Respiratory Distress Syndrome",
    "TB": "Tuberculosis",
    "CF": "Cystic Fibrosis",
    "PE": "Pulmonary Embolism",
    "IPF": "Idiopathic Pulmonary Fibrosis",
    "OSA": "Obstructive Sleep Apnea",
    "URTI": "Upper Respiratory Tract Infection",
    "LRTI": "Lower Respiratory Tract Infection",
    "SOB": "Shortness of Breath",
    
    # Diabetes / Metabolic
    "DM": "Diabetes Mellitus",
    "DM1": "Diabetes Mellitus Type 1",
    "DM2": "Diabetes Mellitus Type 2",
    "T1DM": "Type 1 Diabetes Mellitus",
    "T2DM": "Type 2 Diabetes Mellitus",
    "IDDM": "Insulin-Dependent Diabetes Mellitus",
    "NIDDM": "Non-Insulin-Dependent Diabetes Mellitus",
    "DKA": "Diabetic Ketoacidosis",
    "HHS": "Hyperosmolar Hyperglycemic State",
    "PCOS": "Polycystic Ovary Syndrome",
    
    # Gastrointestinal
    "GERD": "Gastroesophageal Reflux Disease",
    "IBD": "Inflammatory Bowel Disease",
    "IBS": "Irritable Bowel Syndrome",
    "UC": "Ulcerative Colitis",
    "CD": "Crohn's Disease",
    "PUD": "Peptic Ulcer Disease",
    "GI": "Gastrointestinal",
    "NAFLD": "Non-Alcoholic Fatty Liver Disease",
    "HBV": "Hepatitis B Virus",
    "HCV": "Hepatitis C Virus",
    
    # Renal / Urological
    "UTI": "Urinary Tract Infection",
    "CKD": "Chronic Kidney Disease",
    "AKI": "Acute Kidney Injury",
    "ESRD": "End-Stage Renal Disease",
    "ARF": "Acute Renal Failure",
    "CRF": "Chronic Renal Failure",
    "BPH": "Benign Prostatic Hyperplasia",
    "PKD": "Polycystic Kidney Disease",
    
    # Musculoskeletal
    "OA": "Osteoarthritis",
    "RA": "Rheumatoid Arthritis",
    "SLE": "Systemic Lupus Erythematosus",
    "AS": "Ankylosing Spondylitis",
    "FM": "Fibromyalgia",
    "JIA": "Juvenile Idiopathic Arthritis",
    "DJD": "Degenerative Joint Disease",
    "LBP": "Low Back Pain",
    
    # Oncology
    "CA": "Cancer",
    "CRC": "Colorectal Cancer",
    "NHL": "Non-Hodgkin Lymphoma",
    "HL": "Hodgkin Lymphoma",
    "AML": "Acute Myeloid Leukemia",
    "ALL": "Acute Lymphoblastic Leukemia",
    "CML": "Chronic Myeloid Leukemia",
    "CLL": "Chronic Lymphocytic Leukemia",
    "MM": "Multiple Myeloma",
    "HCC": "Hepatocellular Carcinoma",
    "RCC": "Renal Cell Carcinoma",
    "NSCLC": "Non-Small Cell Lung Cancer",
    "SCLC": "Small Cell Lung Cancer",
    
    # Infectious Disease
    "HIV": "Human Immunodeficiency Virus",
    "AIDS": "Acquired Immunodeficiency Syndrome",
    "MRSA": "Methicillin-Resistant Staphylococcus Aureus",
    "VRE": "Vancomycin-Resistant Enterococcus",
    "STI": "Sexually Transmitted Infection",
    "STD": "Sexually Transmitted Disease",
    "RSV": "Respiratory Syncytial Virus",
    "EBV": "Epstein-Barr Virus",
    "CMV": "Cytomegalovirus",
    "HSV": "Herpes Simplex Virus",
    "HPV": "Human Papillomavirus",
    
    # Mental Health
    "MDD": "Major Depressive Disorder",
    "GAD": "Generalized Anxiety Disorder",
    "PTSD": "Post-Traumatic Stress Disorder",
    "OCD": "Obsessive-Compulsive Disorder",
    "ADHD": "Attention Deficit Hyperactivity Disorder",
    "ADD": "Attention Deficit Disorder",
    "BPD": "Borderline Personality Disorder",
    "BD": "Bipolar Disorder",
    "SAD": "Seasonal Affective Disorder",
    "ASD": "Autism Spectrum Disorder",
    
    # Endocrine
    "DI": "Diabetes Insipidus",
    "TSH": "Thyroid Stimulating Hormone",
    "GH": "Growth Hormone",
    "AI": "Adrenal Insufficiency",
    
    # Hematologic
    "IDA": "Iron Deficiency Anemia",
    "ITP": "Immune Thrombocytopenic Purpura",
    "TTP": "Thrombotic Thrombocytopenic Purpura",
    "DIC": "Disseminated Intravascular Coagulation",
    "HIT": "Heparin-Induced Thrombocytopenia",
    "VWD": "Von Willebrand Disease",
    
    # Allergic / Immune
    "SJS": "Stevens-Johnson Syndrome",
    "TEN": "Toxic Epidermal Necrolysis",
    
    # Other Common
    "SOB": "Shortness of Breath",
    "DOE": "Dyspnea on Exertion",
    "CP": "Chest Pain",
    "HA": "Headache",
    "NV": "Nausea and Vomiting",
    "LOC": "Loss of Consciousness",
    "AMS": "Altered Mental Status",
    "FTT": "Failure to Thrive",
    "FUO": "Fever of Unknown Origin",
}

# ICD-10 code pattern (A00.0 through Z99.9)
ICD10_PATTERN = re.compile(r'^[A-Z]\d{2}(?:\.\d{1,2})?$', re.IGNORECASE)

# ICD-11 code pattern (alphanumeric, more flexible)
ICD11_PATTERN = re.compile(r'^[A-Z0-9]{2,6}(?:\.\d{1,3})?$', re.IGNORECASE)


# ============================================================================
# PHYSICAL MEASUREMENT CONSTANTS
# ============================================================================

# Unit patterns for extraction (PHYS-01)
WEIGHT_PATTERNS = [
    (re.compile(r'(\d+(?:\.\d+)?)\s*(kg|kgs|kilogram|kilograms)', re.I), 'kg'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*(lb|lbs|pound|pounds)', re.I), 'lb'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*(g|gram|grams)', re.I), 'g'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*(oz|ounce|ounces)', re.I), 'oz'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*(st|stone|stones)', re.I), 'st'),
]

HEIGHT_PATTERNS = [
    (re.compile(r'(\d+(?:\.\d+)?)\s*(cm|centimeter|centimeters|cms)', re.I), 'cm'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*(m|meter|meters|metre|metres)', re.I), 'm'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*(in|inch|inches)', re.I), 'in'),
    (re.compile(r"(\d+)\s*['\u2032]\s*(\d+(?:\.\d+)?)\s*[\"″]?", re.I), 'ft_in'),  # 5'9" format
    (re.compile(r'(\d+(?:\.\d+)?)\s*(ft|foot|feet)', re.I), 'ft'),
]

TEMPERATURE_PATTERNS = [
    (re.compile(r'(\d+(?:\.\d+)?)\s*°?\s*(C|celsius)', re.I), 'C'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*°?\s*(F|fahrenheit)', re.I), 'F'),
    (re.compile(r'(\d+(?:\.\d+)?)\s*°', re.I), 'unknown'),  # Just degree sign
]

BP_PATTERNS = [
    (re.compile(r'(\d{2,3})\s*/\s*(\d{2,3})', re.I), 'mmHg'),  # 120/80 format
]

PULSE_PATTERNS = [
    (re.compile(r'(\d{2,3})\s*(bpm|beats?\s*per\s*min)', re.I), 'bpm'),
]

# Valid ranges for physical measurements (PHYS-04)
VALID_RANGES = {
    'weight_kg': (1, 500),       # 1-500 kg
    'height_cm': (30, 250),      # 30-250 cm
    'temperature_c': (30, 45),   # 30-45°C (human body)
    'bp_systolic': (60, 250),    # 60-250 mmHg
    'bp_diastolic': (30, 150),   # 30-150 mmHg
    'pulse_bpm': (30, 250),      # 30-250 bpm
    'bmi': (10, 80),             # 10-80 BMI range
}

# Unit conversion factors (PHYS-03)
CONVERSION_FACTORS = {
    # Weight to kg
    'lb_to_kg': 0.453592,
    'oz_to_kg': 0.0283495,
    'g_to_kg': 0.001,
    'st_to_kg': 6.35029,
    
    # Height to cm
    'm_to_cm': 100,
    'in_to_cm': 2.54,
    'ft_to_cm': 30.48,
    
    # Temperature to Celsius
    'f_to_c': lambda f: (f - 32) * 5 / 9,
}

# BMI thresholds (PHYS-06)
BMI_THRESHOLDS = {
    'underweight': 18.5,
    'normal': 25.0,
    'overweight': 30.0,
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def is_null_or_empty(value: Any) -> bool:
    """Check if value is null or empty."""
    if pd.isna(value):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def to_title_case(text: str) -> str:
    """Convert text to title case, handling special cases."""
    if not text:
        return text
    
    # Split on spaces and handle each word
    words = text.split()
    result = []
    
    # Words to keep lowercase unless first word
    lowercase_words = {'and', 'or', 'the', 'a', 'an', 'of', 'with', 'in', 'on', 'to', 'for'}
    
    for i, word in enumerate(words):
        # Keep Roman numerals uppercase
        if re.match(r'^(I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII)+$', word.upper()):
            result.append(word.upper())
        # Keep type numbers (Type 1, Type 2)
        elif re.match(r'^\d+$', word):
            result.append(word)
        # Lowercase words (except first word)
        elif word.lower() in lowercase_words and i > 0:
            result.append(word.lower())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def extract_measurement(value: str, patterns: List[Tuple]) -> Optional[PhysicalMeasurement]:
    """Extract numeric value and unit from a measurement string."""
    if not value or not isinstance(value, str):
        return None
    
    value = value.strip()
    
    for pattern, unit in patterns:
        match = pattern.search(value)
        if match:
            groups = match.groups()
            
            # Handle feet and inches format
            if unit == 'ft_in':
                feet = float(groups[0])
                inches = float(groups[1]) if len(groups) > 1 and groups[1] else 0
                total_inches = feet * 12 + inches
                return PhysicalMeasurement(
                    value=total_inches,
                    unit='in',
                    original=value,
                )
            
            return PhysicalMeasurement(
                value=float(groups[0]),
                unit=unit,
                original=value,
            )
    
    # Try to extract just a number (no unit)
    match = re.search(r'(\d+(?:\.\d+)?)', value)
    if match:
        return PhysicalMeasurement(
            value=float(match.group(1)),
            unit='unknown',
            original=value,
        )
    
    return None


def calculate_bmi(weight_kg: float, height_cm: float) -> float:
    """Calculate BMI from weight (kg) and height (cm)."""
    if height_cm <= 0:
        return 0
    height_m = height_cm / 100
    return weight_kg / (height_m ** 2)


def get_bmi_category(bmi: float) -> BMICategory:
    """Get BMI category from BMI value."""
    if bmi < BMI_THRESHOLDS['underweight']:
        return BMICategory.UNDERWEIGHT
    elif bmi < BMI_THRESHOLDS['normal']:
        return BMICategory.NORMAL
    elif bmi < BMI_THRESHOLDS['overweight']:
        return BMICategory.OVERWEIGHT
    else:
        return BMICategory.OBESE


def validate_icd_code(code: str) -> Tuple[bool, str]:
    """Validate ICD code format. Returns (is_valid, icd_version)."""
    if not code or not isinstance(code, str):
        return False, "unknown"
    
    code = code.strip().upper()
    
    if ICD10_PATTERN.match(code):
        return True, "ICD-10"
    elif ICD11_PATTERN.match(code):
        return True, "ICD-11"
    
    return False, "invalid"


def is_medical_abbreviation(text: str) -> bool:
    """Check if text is a known medical abbreviation."""
    if not text or not isinstance(text, str):
        return False
    return text.strip().upper() in MEDICAL_ABBREVIATIONS


def expand_medical_abbreviation(text: str) -> Optional[str]:
    """Expand a medical abbreviation if known."""
    if not text or not isinstance(text, str):
        return None
    return MEDICAL_ABBREVIATIONS.get(text.strip().upper())


def detect_multiple_diagnoses(text: str) -> List[str]:
    """Detect if multiple diagnoses are present in one cell."""
    if not text or not isinstance(text, str):
        return []
    
    # Common separators for multiple diagnoses
    separators = [',', ';', '/', '&', ' and ', '\n']
    
    # Split by separators
    parts = [text]
    for sep in separators:
        new_parts = []
        for part in parts:
            new_parts.extend(part.split(sep))
        parts = new_parts
    
    # Clean and filter
    diagnoses = []
    for part in parts:
        clean = part.strip()
        if clean and len(clean) > 1:  # Ignore single characters
            diagnoses.append(clean)
    
    return diagnoses if len(diagnoses) > 1 else []


# ============================================================================
# DIAG FORMULA IMPLEMENTATIONS (HTYPE-031)
# ============================================================================

def diag_01_title_case_normalization(df: pd.DataFrame, col: str) -> Tuple[pd.DataFrame, List[int]]:
    """DIAG-01: Title Case Normalization.
    
    Converts lowercase diagnoses to title case.
    "type 2 diabetes" → "Type 2 Diabetes"
    """
    changed_indices = []
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        original = str(value).strip()
        
        # Skip if already mixed case or all uppercase (may be intentional)
        if original != original.lower():
            continue
        
        # Apply title case
        normalized = to_title_case(original)
        
        if normalized != original:
            df.loc[idx, col] = normalized
            changed_indices.append(idx)
    
    return df, changed_indices


def diag_02_icd_code_validation(df: pd.DataFrame, col: str) -> List[MedicalFlag]:
    """DIAG-02: ICD Code Validation.
    
    Validates ICD-10 (A00.0-Z99.9) and ICD-11 formats.
    """
    flags = []
    invalid_rows = []
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        text = str(value).strip()
        
        # Check if it looks like an ICD code (starts with letter, has numbers)
        if re.match(r'^[A-Z]\d', text, re.I):
            is_valid, version = validate_icd_code(text)
            if not is_valid:
                invalid_rows.append(idx)
    
    if invalid_rows:
        flags.append(MedicalFlag(
            formula_id="DIAG-02",
            column=col,
            row_indices=invalid_rows,
            issue=f"Invalid ICD code format in {len(invalid_rows)} rows",
            suggestion="Check ICD-10 (A00.0-Z99.9) or ICD-11 format",
            severity="warning",
        ))
    
    return flags


def diag_03_abbreviation_expansion(df: pd.DataFrame, col: str) -> Tuple[pd.DataFrame, List[int], List[MedicalFlag]]:
    """DIAG-03: Medical Abbreviation Expansion.
    
    Expands known medical abbreviations like HTN, DM, MI, etc.
    Returns expanded df, changed indices, and flags for user confirmation.
    """
    changed_indices = []
    flags = []
    expansion_suggestions = []
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        text = str(value).strip()
        
        # Check if the entire value is an abbreviation
        expansion = expand_medical_abbreviation(text)
        if expansion:
            df.loc[idx, col] = expansion
            changed_indices.append(idx)
            continue
        
        # Check for abbreviations within the text
        words = text.split()
        expanded_words = []
        has_expansion = False
        
        for word in words:
            clean_word = re.sub(r'[^\w]', '', word).upper()
            exp = MEDICAL_ABBREVIATIONS.get(clean_word)
            if exp:
                expanded_words.append(exp)
                has_expansion = True
            else:
                expanded_words.append(word)
        
        if has_expansion:
            df.loc[idx, col] = ' '.join(expanded_words)
            changed_indices.append(idx)
    
    return df, changed_indices, flags


def diag_04_typo_detection(df: pd.DataFrame, col: str) -> List[MedicalFlag]:
    """DIAG-04: Typo Detection (flags for AI-assisted correction).
    
    Detects common medical spelling errors. Does NOT auto-correct.
    Flags for user confirmation with AI suggestion.
    """
    # Common medical typos
    COMMON_TYPOS = {
        "diabeties": "diabetes",
        "diabetis": "diabetes",
        "hypertention": "hypertension",
        "hypertenshun": "hypertension",
        "astma": "asthma",
        "asthama": "asthma",
        "pnuemonia": "pneumonia",
        "pnemonia": "pneumonia",
        "arthritis": None,  # Correct
        "artheritis": "arthritis",
        "seizure": None,
        "seisure": "seizure",
        "seizeure": "seizure",
        "alzhimers": "alzheimer's",
        "alzheimers": "alzheimer's",
        "parkinson": None,
        "parkinsons": "parkinson's",
        "epilepsey": "epilepsy",
        "epilepcy": "epilepsy",
        "schizophrenia": None,
        "schizophernia": "schizophrenia",
        "anemia": None,
        "anaemia": "anemia",  # British to American
        "leukemia": None,
        "leukaemia": "leukemia",
        "tumor": None,
        "tumour": "tumor",
        "colesterol": "cholesterol",
        "cholestorol": "cholesterol",
    }
    
    flags = []
    typo_rows = []
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        text = str(value).strip().lower()
        
        for typo, correction in COMMON_TYPOS.items():
            if correction and typo in text:
                typo_rows.append({
                    "row": idx,
                    "original": value,
                    "typo": typo,
                    "suggestion": correction,
                })
                break
    
    if typo_rows:
        flags.append(MedicalFlag(
            formula_id="DIAG-04",
            column=col,
            row_indices=[r["row"] for r in typo_rows],
            issue=f"Possible spelling errors in {len(typo_rows)} rows",
            suggestion="Review suggested corrections (AI-assisted)",
            severity="warning",
            requires_confirmation=True,
        ))
    
    return flags


def diag_05_sensitivity_flag(df: pd.DataFrame, col: str) -> MedicalFlag:
    """DIAG-05: Sensitivity Flag.
    
    Medical diagnoses are HIGH-SENSITIVITY PII. Always flags for governance.
    """
    return MedicalFlag(
        formula_id="DIAG-05",
        column=col,
        row_indices=list(df.index),
        issue="Medical diagnosis column detected - HIGH SENSITIVITY PII",
        suggestion="Column flagged for restricted export, encryption recommended, access logging enabled",
        severity="info",
    )


def diag_06_null_handling(df: pd.DataFrame, col: str) -> Tuple[pd.DataFrame, List[int], List[MedicalFlag]]:
    """DIAG-06: Null Handling.
    
    Prompts for null values or marks as "Not Diagnosed".
    Does NOT auto-fill — flags for user decision.
    """
    null_indices = []
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            null_indices.append(idx)
    
    flags = []
    if null_indices:
        flags.append(MedicalFlag(
            formula_id="DIAG-06",
            column=col,
            row_indices=null_indices,
            issue=f"Null/empty diagnosis in {len(null_indices)} rows",
            suggestion="Mark as 'Not Diagnosed', 'No Known Diagnosis', or provide value",
            severity="warning",
            requires_confirmation=True,
        ))
    
    return df, [], flags


def diag_07_multiple_diagnoses_split(df: pd.DataFrame, col: str) -> List[MedicalFlag]:
    """DIAG-07: Multiple Diagnoses Split.
    
    Detects multiple diagnoses in one cell and flags for splitting.
    Does NOT auto-split — flags for user confirmation.
    """
    multi_diag_rows = []
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        diagnoses = detect_multiple_diagnoses(str(value))
        if diagnoses:
            multi_diag_rows.append({
                "row": idx,
                "original": value,
                "detected": diagnoses,
            })
    
    flags = []
    if multi_diag_rows:
        flags.append(MedicalFlag(
            formula_id="DIAG-07",
            column=col,
            row_indices=[r["row"] for r in multi_diag_rows],
            issue=f"Multiple diagnoses in single cell detected in {len(multi_diag_rows)} rows",
            suggestion="Consider splitting into primary and secondary diagnosis columns",
            severity="info",
            requires_confirmation=True,
        ))
    
    return flags


# ============================================================================
# PHYS FORMULA IMPLEMENTATIONS (HTYPE-032)
# ============================================================================

def phys_01_unit_extraction(df: pd.DataFrame, col: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """PHYS-01: Unit Extraction.
    
    Extracts numeric value and unit from measurement strings.
    "65 kg" → value: 65, unit: "kg"
    """
    col_lower = col.lower()
    extraction_info = {
        "extracted_values": [],
        "extracted_units": [],
        "rows_with_units": [],
    }
    
    # Determine which patterns to use based on column name
    if any(kw in col_lower for kw in ['weight', 'mass', 'wt']):
        patterns = WEIGHT_PATTERNS
    elif any(kw in col_lower for kw in ['height', 'ht', 'tall', 'length']):
        patterns = HEIGHT_PATTERNS
    elif any(kw in col_lower for kw in ['temp', 'temperature']):
        patterns = TEMPERATURE_PATTERNS
    elif any(kw in col_lower for kw in ['bp', 'blood_pressure', 'pressure']):
        patterns = BP_PATTERNS
    elif any(kw in col_lower for kw in ['pulse', 'heart_rate', 'hr', 'bpm']):
        patterns = PULSE_PATTERNS
    else:
        # Try all patterns
        patterns = WEIGHT_PATTERNS + HEIGHT_PATTERNS + TEMPERATURE_PATTERNS
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        measurement = extract_measurement(str(value), patterns)
        if measurement and measurement.unit != 'unknown':
            extraction_info["extracted_values"].append(measurement.value)
            extraction_info["extracted_units"].append(measurement.unit)
            extraction_info["rows_with_units"].append(idx)
    
    return df, extraction_info


def phys_02_unit_standardization(df: pd.DataFrame, col: str, 
                                   target_unit: Optional[str] = None) -> Tuple[pd.DataFrame, List[int]]:
    """PHYS-02: Unit Standardization.
    
    Standardizes to: Weight: kg, Height: cm, Temperature: °C, BP: mmHg.
    """
    changed_indices = []
    col_lower = col.lower()
    
    # Determine target unit and patterns
    if any(kw in col_lower for kw in ['weight', 'mass', 'wt']):
        patterns = WEIGHT_PATTERNS
        standard_unit = target_unit or 'kg'
    elif any(kw in col_lower for kw in ['height', 'ht', 'tall']):
        patterns = HEIGHT_PATTERNS
        standard_unit = target_unit or 'cm'
    elif any(kw in col_lower for kw in ['temp', 'temperature']):
        patterns = TEMPERATURE_PATTERNS
        standard_unit = target_unit or 'C'
    else:
        return df, changed_indices
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        measurement = extract_measurement(str(value), patterns)
        if not measurement:
            continue
        
        # Convert to standard unit
        converted_value = measurement.value
        needs_conversion = False
        
        if standard_unit == 'kg':
            if measurement.unit == 'lb':
                converted_value = measurement.value * CONVERSION_FACTORS['lb_to_kg']
                needs_conversion = True
            elif measurement.unit == 'oz':
                converted_value = measurement.value * CONVERSION_FACTORS['oz_to_kg']
                needs_conversion = True
            elif measurement.unit == 'g':
                converted_value = measurement.value * CONVERSION_FACTORS['g_to_kg']
                needs_conversion = True
            elif measurement.unit == 'st':
                converted_value = measurement.value * CONVERSION_FACTORS['st_to_kg']
                needs_conversion = True
        
        elif standard_unit == 'cm':
            if measurement.unit == 'm':
                converted_value = measurement.value * CONVERSION_FACTORS['m_to_cm']
                needs_conversion = True
            elif measurement.unit == 'in':
                converted_value = measurement.value * CONVERSION_FACTORS['in_to_cm']
                needs_conversion = True
            elif measurement.unit == 'ft':
                converted_value = measurement.value * CONVERSION_FACTORS['ft_to_cm']
                needs_conversion = True
        
        elif standard_unit == 'C':
            if measurement.unit == 'F':
                converted_value = CONVERSION_FACTORS['f_to_c'](measurement.value)
                needs_conversion = True
        
        if needs_conversion:
            # Convert to object type to allow mixed types
            if df[col].dtype.name in ('string', 'str'):
                df[col] = df[col].astype(object)
            df.loc[idx, col] = round(converted_value, 1)
            changed_indices.append(idx)
    
    return df, changed_indices


def phys_03_imperial_metric_conversion(df: pd.DataFrame, col: str) -> Tuple[pd.DataFrame, List[int]]:
    """PHYS-03: Imperial-Metric Conversion.
    
    "5'9\"" → 175.26 cm
    "150 lbs" → 68.04 kg
    "98.6°F" → 37°C
    """
    changed_indices = []
    col_lower = col.lower()
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        text = str(value).strip()
        converted = None
        
        # Height: feet and inches format
        ft_in_match = re.match(r"(\d+)\s*['\u2032]\s*(\d+(?:\.\d+)?)\s*[\"″]?", text)
        if ft_in_match:
            feet = float(ft_in_match.group(1))
            inches = float(ft_in_match.group(2)) if ft_in_match.group(2) else 0
            total_cm = (feet * 30.48) + (inches * 2.54)
            converted = round(total_cm, 1)
        
        # Weight: pounds
        lb_match = re.match(r'(\d+(?:\.\d+)?)\s*(lb|lbs|pound|pounds)', text, re.I)
        if lb_match and converted is None:
            pounds = float(lb_match.group(1))
            converted = round(pounds * 0.453592, 2)
        
        # Temperature: Fahrenheit
        f_match = re.match(r'(\d+(?:\.\d+)?)\s*°?\s*F', text, re.I)
        if f_match and converted is None:
            fahrenheit = float(f_match.group(1))
            celsius = (fahrenheit - 32) * 5 / 9
            converted = round(celsius, 1)
        
        if converted is not None:
            # Convert to object type to allow mixed types
            if df[col].dtype.name in ('string', 'str'):
                df[col] = df[col].astype(object)
            df.loc[idx, col] = converted
            changed_indices.append(idx)
    
    return df, changed_indices


def phys_04_range_validation(df: pd.DataFrame, col: str) -> List[MedicalFlag]:
    """PHYS-04: Range Validation.
    
    Validates biological ranges:
    - Weight: 1-500 kg
    - Height: 30-250 cm
    - Temperature: 30-45°C
    - BP systolic: 60-250 mmHg
    """
    flags = []
    out_of_range_rows = []
    col_lower = col.lower()
    
    # Determine range based on column type
    if any(kw in col_lower for kw in ['weight', 'mass', 'wt']):
        min_val, max_val = VALID_RANGES['weight_kg']
        measurement_type = 'weight'
    elif any(kw in col_lower for kw in ['height', 'ht', 'tall']):
        min_val, max_val = VALID_RANGES['height_cm']
        measurement_type = 'height'
    elif any(kw in col_lower for kw in ['temp', 'temperature']):
        min_val, max_val = VALID_RANGES['temperature_c']
        measurement_type = 'temperature'
    elif any(kw in col_lower for kw in ['pulse', 'heart_rate', 'hr', 'bpm']):
        min_val, max_val = VALID_RANGES['pulse_bpm']
        measurement_type = 'pulse'
    elif any(kw in col_lower for kw in ['bmi']):
        min_val, max_val = VALID_RANGES['bmi']
        measurement_type = 'bmi'
    else:
        return flags
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        try:
            num_val = float(value) if not isinstance(value, (int, float)) else value
            
            if num_val < min_val or num_val > max_val:
                out_of_range_rows.append({
                    "row": idx,
                    "value": num_val,
                    "range": f"{min_val}-{max_val}",
                })
        except (ValueError, TypeError):
            continue
    
    if out_of_range_rows:
        flags.append(MedicalFlag(
            formula_id="PHYS-04",
            column=col,
            row_indices=[r["row"] for r in out_of_range_rows],
            issue=f"{len(out_of_range_rows)} {measurement_type} values outside biological range",
            suggestion=f"Valid range: {min_val}-{max_val}. Review for data entry errors.",
            severity="warning",
        ))
    
    return flags


def phys_05_bmi_derivation(df: pd.DataFrame, weight_col: str, height_col: str,
                            bmi_col: Optional[str] = None) -> Tuple[pd.DataFrame, List[int]]:
    """PHYS-05: BMI Derivation.
    
    Calculates BMI = weight(kg) / height(m)²
    Creates or fills BMI column if both weight and height are present.
    """
    changed_indices = []
    
    if weight_col not in df.columns or height_col not in df.columns:
        return df, changed_indices
    
    # Create BMI column if not exists
    if bmi_col is None:
        bmi_col = 'bmi_derived'
    
    if bmi_col not in df.columns:
        df[bmi_col] = np.nan
    
    for idx in df.index:
        weight = df.loc[idx, weight_col]
        height = df.loc[idx, height_col]
        
        if is_null_or_empty(weight) or is_null_or_empty(height):
            continue
        
        try:
            weight_kg = float(weight)
            height_cm = float(height)
            
            if weight_kg > 0 and height_cm > 0:
                bmi = calculate_bmi(weight_kg, height_cm)
                
                # Only update if BMI is in valid range
                if VALID_RANGES['bmi'][0] <= bmi <= VALID_RANGES['bmi'][1]:
                    df.loc[idx, bmi_col] = round(bmi, 1)
                    changed_indices.append(idx)
        except (ValueError, TypeError):
            continue
    
    return df, changed_indices


def phys_06_bmi_category_tagging(df: pd.DataFrame, bmi_col: str,
                                   category_col: Optional[str] = None) -> Tuple[pd.DataFrame, List[int]]:
    """PHYS-06: BMI Category Tagging.
    
    Tags BMI values with categories:
    <18.5 = Underweight
    18.5-24.9 = Normal
    25-29.9 = Overweight
    ≥30 = Obese
    """
    changed_indices = []
    
    if bmi_col not in df.columns:
        return df, changed_indices
    
    if category_col is None:
        category_col = f'{bmi_col}_category'
    
    if category_col not in df.columns:
        df[category_col] = None
    
    for idx in df.index:
        bmi = df.loc[idx, bmi_col]
        
        if is_null_or_empty(bmi):
            continue
        
        try:
            bmi_val = float(bmi)
            category = get_bmi_category(bmi_val)
            df.loc[idx, category_col] = category.value
            changed_indices.append(idx)
        except (ValueError, TypeError):
            continue
    
    return df, changed_indices


def phys_07_decimal_standardization(df: pd.DataFrame, col: str, 
                                      decimals: int = 1) -> Tuple[pd.DataFrame, List[int]]:
    """PHYS-07: Decimal Standardization.
    
    Standardizes to 1 decimal place for physical measurements.
    """
    changed_indices = []
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            continue
        
        try:
            num_val = float(value)
            rounded = round(num_val, decimals)
            
            if rounded != num_val:
                df.loc[idx, col] = rounded
                changed_indices.append(idx)
        except (ValueError, TypeError):
            continue
    
    return df, changed_indices


def phys_08_null_handling(df: pd.DataFrame, col: str) -> List[MedicalFlag]:
    """PHYS-08: Null Handling.
    
    Physical measurements cannot be predicted. Prompts user.
    """
    null_indices = []
    
    for idx in df.index:
        value = df.loc[idx, col]
        if is_null_or_empty(value):
            null_indices.append(idx)
    
    flags = []
    if null_indices:
        flags.append(MedicalFlag(
            formula_id="PHYS-08",
            column=col,
            row_indices=null_indices,
            issue=f"Null/empty measurement in {len(null_indices)} rows",
            suggestion="Physical measurements cannot be predicted. User input required.",
            severity="warning",
            requires_confirmation=True,
        ))
    
    return flags


# ============================================================================
# MAIN CLASS
# ============================================================================

class MedicalRules:
    """Medical HTYPE Rules engine for DIAG and PHYS formula sets."""
    
    def __init__(self, job_id: int, df: pd.DataFrame, db, htype_map: Dict[str, str]):
        """Initialize the medical rules engine.
        
        Args:
            job_id: Upload job ID for logging
            df: DataFrame to process
            db: Database session
            htype_map: Mapping of column names to their HTYPEs
        """
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.htype_map = htype_map
        
        self.flags: List[Dict[str, Any]] = []
        self.changes: Dict[str, List[int]] = {}
        self.pii_tags: Dict[str, Dict[str, Any]] = {}
        
        # Identify DIAG and PHYS columns
        self.diag_cols = [col for col, htype in htype_map.items() 
                         if htype == "HTYPE-031" and col in df.columns]
        self.phys_cols = [col for col, htype in htype_map.items() 
                         if htype == "HTYPE-032" and col in df.columns]
        
        # Find weight and height columns for BMI derivation
        self.weight_col = None
        self.height_col = None
        self.bmi_col = None
        
        for col in self.phys_cols:
            col_lower = col.lower()
            if any(kw in col_lower for kw in ['weight', 'mass', 'wt']):
                self.weight_col = col
            if any(kw in col_lower for kw in ['height', 'ht', 'tall']):
                self.height_col = col
            if 'bmi' in col_lower:
                self.bmi_col = col
    
    def add_flag(self, flag: MedicalFlag):
        """Add a flag for user review."""
        self.flags.append({
            "formula_id": flag.formula_id,
            "column": flag.column,
            "row_indices": flag.row_indices[:20],  # Limit for storage
            "row_count": len(flag.row_indices),
            "issue": flag.issue,
            "suggestion": flag.suggestion,
            "severity": flag.severity,
            "requires_confirmation": flag.requires_confirmation,
        })
    
    def log_action(self, formula_id: str, action: str, column: str, 
                    affected_count: int):
        """Log action to database."""
        try:
            log = CleaningLog(
                job_id=self.job_id,
                action=f"{formula_id}: {action} on column '{column}' - {affected_count} rows",
                timestamp=datetime.utcnow(),
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            self.db.rollback()
    
    def track_changes(self, formula_id: str, indices: List[int]):
        """Track which rows were changed by which formula."""
        if formula_id not in self.changes:
            self.changes[formula_id] = []
        self.changes[formula_id].extend(indices)
    
    # ========================================================================
    # DIAG RULES (HTYPE-031)
    # ========================================================================
    
    def run_diag_rules(self):
        """Run all DIAG formulas for medical diagnosis columns."""
        rules_applied = []
        
        for col in self.diag_cols:
            # DIAG-05: Always flag as high-sensitivity PII first
            sensitivity_flag = diag_05_sensitivity_flag(self.df, col)
            self.add_flag(sensitivity_flag)
            
            # Tag for PII governance
            self.pii_tags[col] = {
                "level": SensitivityLevel.HIGH.value,
                "label": "Medical Diagnosis",
                "restricted_export": True,
                "encryption_recommended": True,
                "access_logging": True,
                "ai_processing_excluded": True,  # CRITICAL: No AI outside session
            }
            
            # DIAG-01: Title Case Normalization
            self.df, changed = diag_01_title_case_normalization(self.df, col)
            if changed:
                self.track_changes("DIAG-01", changed)
                self.log_action("DIAG-01", "Title case normalization", col, len(changed))
                rules_applied.append("DIAG-01")
            
            # DIAG-02: ICD Code Validation
            icd_flags = diag_02_icd_code_validation(self.df, col)
            for flag in icd_flags:
                self.add_flag(flag)
            if icd_flags:
                rules_applied.append("DIAG-02")
            
            # DIAG-03: Abbreviation Expansion
            self.df, changed, abbr_flags = diag_03_abbreviation_expansion(self.df, col)
            if changed:
                self.track_changes("DIAG-03", changed)
                self.log_action("DIAG-03", "Medical abbreviation expansion", col, len(changed))
                rules_applied.append("DIAG-03")
            for flag in abbr_flags:
                self.add_flag(flag)
            
            # DIAG-04: Typo Detection
            typo_flags = diag_04_typo_detection(self.df, col)
            for flag in typo_flags:
                self.add_flag(flag)
            if typo_flags:
                rules_applied.append("DIAG-04")
            
            # DIAG-06: Null Handling
            self.df, _, null_flags = diag_06_null_handling(self.df, col)
            for flag in null_flags:
                self.add_flag(flag)
            if null_flags:
                rules_applied.append("DIAG-06")
            
            # DIAG-07: Multiple Diagnoses Detection
            multi_flags = diag_07_multiple_diagnoses_split(self.df, col)
            for flag in multi_flags:
                self.add_flag(flag)
            if multi_flags:
                rules_applied.append("DIAG-07")
        
        return list(set(rules_applied))
    
    # ========================================================================
    # PHYS RULES (HTYPE-032)
    # ========================================================================
    
    def run_phys_rules(self):
        """Run all PHYS formulas for physical measurement columns."""
        rules_applied = []
        
        for col in self.phys_cols:
            # Tag as medium-sensitivity PII
            self.pii_tags[col] = {
                "level": SensitivityLevel.MEDIUM.value,
                "label": "Physical Measurement",
                "restricted_export": False,
                "encryption_recommended": False,
                "access_logging": False,
            }
            
            # PHYS-01: Unit Extraction (informational)
            _, extraction_info = phys_01_unit_extraction(self.df, col)
            if extraction_info["rows_with_units"]:
                rules_applied.append("PHYS-01")
            
            # PHYS-03: Imperial-Metric Conversion (before standardization)
            self.df, changed = phys_03_imperial_metric_conversion(self.df, col)
            if changed:
                self.track_changes("PHYS-03", changed)
                self.log_action("PHYS-03", "Imperial to metric conversion", col, len(changed))
                rules_applied.append("PHYS-03")
            
            # PHYS-02: Unit Standardization
            self.df, changed = phys_02_unit_standardization(self.df, col)
            if changed:
                self.track_changes("PHYS-02", changed)
                self.log_action("PHYS-02", "Unit standardization", col, len(changed))
                rules_applied.append("PHYS-02")
            
            # PHYS-04: Range Validation
            range_flags = phys_04_range_validation(self.df, col)
            for flag in range_flags:
                self.add_flag(flag)
            if range_flags:
                rules_applied.append("PHYS-04")
            
            # PHYS-07: Decimal Standardization
            self.df, changed = phys_07_decimal_standardization(self.df, col)
            if changed:
                self.track_changes("PHYS-07", changed)
                self.log_action("PHYS-07", "Decimal standardization", col, len(changed))
                rules_applied.append("PHYS-07")
            
            # PHYS-08: Null Handling
            null_flags = phys_08_null_handling(self.df, col)
            for flag in null_flags:
                self.add_flag(flag)
            if null_flags:
                rules_applied.append("PHYS-08")
        
        # PHYS-05: BMI Derivation (if weight and height columns exist)
        if self.weight_col and self.height_col:
            self.df, changed = phys_05_bmi_derivation(
                self.df, self.weight_col, self.height_col, self.bmi_col
            )
            if changed:
                bmi_col_name = self.bmi_col or 'bmi_derived'
                self.track_changes("PHYS-05", changed)
                self.log_action("PHYS-05", "BMI derivation", bmi_col_name, len(changed))
                rules_applied.append("PHYS-05")
                
                # PHYS-06: BMI Category Tagging
                self.df, cat_changed = phys_06_bmi_category_tagging(
                    self.df, bmi_col_name
                )
                if cat_changed:
                    self.track_changes("PHYS-06", cat_changed)
                    self.log_action("PHYS-06", "BMI category tagging", 
                                   f"{bmi_col_name}_category", len(cat_changed))
                    rules_applied.append("PHYS-06")
        
        return list(set(rules_applied))
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_all(self) -> Dict[str, Any]:
        """Run all medical rules (DIAG + PHYS).
        
        Returns:
            Comprehensive summary of rules applied and changes made
        """
        diag_rules = self.run_diag_rules()
        phys_rules = self.run_phys_rules()
        
        all_rules = diag_rules + phys_rules
        total_changes = sum(len(indices) for indices in self.changes.values())
        
        return {
            "medical_rules_applied": all_rules,
            "diag_columns_processed": len(self.diag_cols),
            "phys_columns_processed": len(self.phys_cols),
            "total_changes": total_changes,
            "changes_by_formula": {k: len(v) for k, v in self.changes.items()},
            "flags_count": len(self.flags),
            "pii_tags": self.pii_tags,
            "high_sensitivity_columns": [
                col for col, tag in self.pii_tags.items() 
                if tag.get("level") == "high"
            ],
        }
