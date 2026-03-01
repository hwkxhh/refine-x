"""
Numeric & Financial Cleaning Rules — Session 7

Implements formulas from the Formula Rulebook for:
- HTYPE-015: Numeric Amount / Currency / Revenue (AMT-01 to AMT-13)
- HTYPE-016: Quantity / Count / Integer Metric (QTY-01 to QTY-09)
- HTYPE-017: Percentage / Rate / Ratio (PCT-01 to PCT-06)
- HTYPE-021: Score / Rating / Grade / GPA (SCORE-01 to SCORE-13)
- HTYPE-042: Currency Code (CUR-01 to CUR-05)
- HTYPE-043: Rank / Ordinal (RANK-01 to RANK-05)
- HTYPE-044: Calculated / Derived Column (CALC-01 to CALC-05)

Logic First. AI Never.
"""

import re
import math
import statistics
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd
import numpy as np

from app.models.cleaning_log import CleaningLog


# ============================================================================
# DATA CLASSES
# ============================================================================

@dataclass
class CleaningResult:
    """Result of applying a cleaning formula."""
    column: str
    formula_id: str
    changes_made: int = 0
    rows_flagged: int = 0
    was_auto_applied: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# CURRENCY CONSTANTS
# ============================================================================

# Currency symbols and their ISO codes
CURRENCY_SYMBOLS = {
    "$": "USD",
    "€": "EUR",
    "£": "GBP",
    "¥": "JPY",
    "₹": "INR",
    "रु": "NPR",
    "₨": "PKR",
    "฿": "THB",
    "₩": "KRW",
    "₱": "PHP",
    "₽": "RUB",
    "Fr": "CHF",
    "kr": "SEK",  # Also NOK, DKK
    "R$": "BRL",
    "A$": "AUD",
    "C$": "CAD",
    "NZ$": "NZD",
    "S$": "SGD",
    "HK$": "HKD",
}

# Currency prefixes (text-based)
CURRENCY_PREFIXES = {
    "USD", "EUR", "GBP", "JPY", "INR", "NPR", "AUD", "CAD", "NZD",
    "CHF", "SEK", "NOK", "DKK", "SGD", "HKD", "CNY", "KRW", "BRL",
    "MXN", "ZAR", "RUB", "TRY", "THB", "PHP", "PKR", "MYR", "IDR",
    "VND", "AED", "SAR", "QAR", "KWD", "BHD", "OMR", "EGP", "NGN",
}

# ISO 4217 currency codes
ISO_4217_CODES = {
    "USD", "EUR", "GBP", "JPY", "CNY", "INR", "NPR", "AUD", "CAD",
    "NZD", "CHF", "SEK", "NOK", "DKK", "SGD", "HKD", "KRW", "BRL",
    "MXN", "ZAR", "RUB", "TRY", "THB", "PHP", "PKR", "MYR", "IDR",
    "VND", "AED", "SAR", "QAR", "KWD", "BHD", "OMR", "EGP", "NGN",
    "TWD", "ILS", "PLN", "CZK", "HUF", "RON", "BGN", "HRK", "CLP",
    "COP", "PEN", "ARS", "UYU", "VEF", "BOB", "PYG", "GTQ", "HNL",
    "NIO", "CRC", "PAB", "DOP", "JMD", "TTD", "BSD", "BBD", "BZD",
    "XCD", "KYD", "AWG", "ANG", "SRD", "GYD", "FJD", "PGK", "SBD",
    "VUV", "WST", "TOP", "XPF", "LKR", "BDT", "MMK", "KHR", "LAK",
    "MNT", "BND", "MVR", "BTN", "AFN", "IRR", "IQD", "JOD", "LBP",
    "SYP", "YER", "TND", "MAD", "DZD", "LYD", "SDG", "SSP", "ETB",
    "KES", "UGX", "TZS", "RWF", "BIF", "ZMW", "MWK", "MZN", "ZWL",
    "BWP", "LSL", "SZL", "NAD", "SCR", "MUR", "MGA", "KMF", "DJF",
    "SOS", "ERN", "CDF", "AOA", "XAF", "XOF", "GHS", "SLL", "GMD",
    "GNF", "LRD", "CVE", "STN", "XDR",
}


# ============================================================================
# NUMBER WORD CONSTANTS
# ============================================================================

# Word-to-number mappings
WORD_TO_NUMBER = {
    # Basic numbers
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19,
    # Tens
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    # Larger units
    "hundred": 100, "thousand": 1000, "million": 1000000,
    "billion": 1000000000, "trillion": 1000000000000,
    # Ordinals (for rank conversion)
    "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
    "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    "eleventh": 11, "twelfth": 12, "thirteenth": 13, "fourteenth": 14,
    "fifteenth": 15, "sixteenth": 16, "seventeenth": 17,
    "eighteenth": 18, "nineteenth": 19, "twentieth": 20,
}

# Common typos for number words
WORD_NUMBER_TYPOS = {
    "elven": "eleven", "tweleve": "twelve", "twleve": "twelve",
    "thirten": "thirteen", "forteen": "fourteen", "fourten": "fourteen",
    "fiveteen": "fifteen", "fiften": "fifteen", "sixteem": "sixteen",
    "seventen": "seventeen", "eigteen": "eighteen", "ninteen": "nineteen",
    "twnety": "twenty", "thrirty": "thirty", "fourty": "forty",
    "fivety": "fifty", "hundered": "hundred", "thousnd": "thousand",
    "milion": "million", "billoin": "billion",
    "frist": "first", "secnd": "second", "thrid": "third",
}


# ============================================================================
# GRADE/GPA CONSTANTS
# ============================================================================

# GPA 4.0 scale mapping (US standard)
GPA_4_SCALE = {
    "A+": 4.0, "A": 4.0, "A-": 3.7,
    "B+": 3.3, "B": 3.0, "B-": 2.7,
    "C+": 2.3, "C": 2.0, "C-": 1.7,
    "D+": 1.3, "D": 1.0, "D-": 0.7,
    "F": 0.0, "E": 0.0,
}

# GPA 5.0 scale (weighted)
GPA_5_SCALE = {
    "A+": 5.0, "A": 5.0, "A-": 4.7,
    "B+": 4.3, "B": 4.0, "B-": 3.7,
    "C+": 3.3, "C": 3.0, "C-": 2.7,
    "D+": 2.3, "D": 2.0, "D-": 1.7,
    "F": 0.0, "E": 0.0,
}

# Letter grade to numeric range (percentage)
LETTER_TO_PERCENT = {
    "A+": (97, 100), "A": (93, 96), "A-": (90, 92),
    "B+": (87, 89), "B": (83, 86), "B-": (80, 82),
    "C+": (77, 79), "C": (73, 76), "C-": (70, 72),
    "D+": (67, 69), "D": (63, 66), "D-": (60, 62),
    "F": (0, 59),
}

# Grade descriptor typos
GRADE_DESCRIPTOR_TYPOS = {
    "excelent": "Excellent", "excellant": "Excellent",
    "satisfacory": "Satisfactory", "satifactory": "Satisfactory",
    "distintion": "Distinction", "distiction": "Distinction",
    "outstandng": "Outstanding", "oustanding": "Outstanding",
    "unsatisfacory": "Unsatisfactory", "unsatifactory": "Unsatisfactory",
    "avrage": "Average", "averge": "Average",
    "pass": "Pass", "passs": "Pass", "faill": "Fail",
}


# ============================================================================
# SURVEY / LIKERT CONSTANTS
# ============================================================================

# 5-point Likert scale
LIKERT_5_SCALE = {
    "strongly disagree": 1, "disagree": 2, "neutral": 3,
    "agree": 4, "strongly agree": 5,
    # Variants
    "sd": 1, "d": 2, "n": 3, "a": 4, "sa": 5,
}

# 7-point Likert scale
LIKERT_7_SCALE = {
    "strongly disagree": 1, "disagree": 2, "somewhat disagree": 3,
    "neutral": 4, "somewhat agree": 5, "agree": 6, "strongly agree": 7,
}

# Frequency scale
FREQUENCY_SCALE = {
    "never": 1, "rarely": 2, "sometimes": 3, "often": 4, "always": 5,
    "very rarely": 1.5, "very often": 4.5,
}


# ============================================================================
# HELPER FUNCTIONS — CURRENCY
# ============================================================================

def extract_currency_symbol(value: str) -> Tuple[Optional[str], str]:
    """Extract currency symbol from a value and return (currency_code, cleaned_value)."""
    if not isinstance(value, str):
        return None, str(value) if value is not None else ""
    
    value = value.strip()
    
    # Check for multi-char symbols first
    for symbol, code in sorted(CURRENCY_SYMBOLS.items(), key=lambda x: -len(x[0])):
        if value.startswith(symbol):
            return code, value[len(symbol):].strip()
        if value.endswith(symbol):
            return code, value[:-len(symbol)].strip()
    
    # Check for currency code prefixes/suffixes
    upper_val = value.upper()
    for code in CURRENCY_PREFIXES:
        if upper_val.startswith(code + " ") or upper_val.startswith(code):
            return code, value[len(code):].strip()
        if upper_val.endswith(" " + code) or upper_val.endswith(code):
            return code, value[:-len(code)].strip()
    
    return None, value


def remove_thousand_separators(value: str) -> str:
    """Remove thousand separators (commas) from numeric string."""
    # Pattern: digits followed by comma followed by exactly 3 digits
    # This ensures we don't remove decimal commas in European notation
    pattern = r'(\d),(\d{3})'
    result = value
    while re.search(pattern, result):
        result = re.sub(pattern, r'\1\2', result)
    return result


def detect_european_notation(value: str) -> bool:
    """Detect if value uses European number notation (period as thousand sep, comma as decimal)."""
    # European: 1.234,56 (1234.56)
    # US: 1,234.56
    
    # Has both period and comma
    if '.' in value and ',' in value:
        last_period = value.rfind('.')
        last_comma = value.rfind(',')
        # European: comma comes after period (comma is decimal)
        if last_comma > last_period:
            return True
    
    # Single comma followed by 1-2 digits at end (likely decimal)
    if re.match(r'^[\d.]+,\d{1,2}$', value):
        return True
    
    return False


def convert_european_notation(value: str) -> str:
    """Convert European notation (1.234,56) to standard (1234.56)."""
    # Remove periods (thousand separators)
    value = value.replace('.', '')
    # Convert comma to decimal point
    value = value.replace(',', '.')
    return value


def parse_numeric_value(value: Any) -> Optional[float]:
    """Parse a value to float, handling various formats."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if not isinstance(value, str):
        value = str(value)
    
    value = value.strip()
    if not value:
        return None
    
    # Check for European notation
    if detect_european_notation(value):
        value = convert_european_notation(value)
    else:
        # Remove thousand separators
        value = remove_thousand_separators(value)
    
    # Extract currency symbol if present
    _, value = extract_currency_symbol(value)
    
    # Remove any remaining non-numeric characters except . - +
    value = re.sub(r'[^\d.\-+eE]', '', value)
    
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def standardize_decimals(value: float, places: int = 2) -> float:
    """Round to specified decimal places."""
    return round(value, places)


def detect_outliers_iqr(series: pd.Series) -> pd.Series:
    """Detect outliers using IQR method. Returns boolean Series."""
    numeric = pd.to_numeric(series, errors='coerce')
    q1 = numeric.quantile(0.25)
    q3 = numeric.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    return (numeric < lower) | (numeric > upper)


def detect_outliers_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Detect outliers using Z-score method. Returns boolean Series."""
    numeric = pd.to_numeric(series, errors='coerce')
    mean = numeric.mean()
    std = numeric.std()
    if std == 0:
        return pd.Series([False] * len(series))
    z_scores = abs((numeric - mean) / std)
    return z_scores > threshold


# ============================================================================
# HELPER FUNCTIONS — WORD TO NUMBER
# ============================================================================

def word_to_number(text: str) -> Optional[float]:
    """Convert word representation of number to numeric value."""
    if not isinstance(text, str):
        return None
    
    text = text.lower().strip()
    if not text:
        return None
    
    # Fix common typos first
    for typo, correct in WORD_NUMBER_TYPOS.items():
        text = re.sub(r'\b' + typo + r'\b', correct, text)
    
    # Direct lookup
    if text in WORD_TO_NUMBER:
        return float(WORD_TO_NUMBER[text])
    
    # Handle compound numbers like "twenty one", "one hundred twenty three"
    words = text.replace('-', ' ').replace(',', '').split()
    
    # Try to parse compound number
    result = 0
    current = 0
    
    for word in words:
        if word in ['and']:
            continue
        
        if word not in WORD_TO_NUMBER:
            # Check for ordinal suffix (1st, 2nd, etc.)
            ordinal_match = re.match(r'^(\d+)(?:st|nd|rd|th)$', word)
            if ordinal_match:
                return float(ordinal_match.group(1))
            return None
        
        value = WORD_TO_NUMBER[word]
        
        if value == 100:
            if current == 0:
                current = 1
            current *= 100
        elif value >= 1000:
            if current == 0:
                current = 1
            result += current * value
            current = 0
        else:
            current += value
    
    return float(result + current) if result + current > 0 else None


def extract_number_with_approximation(text: str) -> Tuple[Optional[float], bool]:
    """Extract number from text, detecting approximation markers."""
    if not isinstance(text, str):
        return None, False
    
    text = text.strip()
    is_approximate = False
    
    # Check for approximation markers
    approx_patterns = [
        r'^(?:approx\.?|approximately|about|around|~|roughly|circa|nearly|almost)\s*',
        r'\s*(?:approx\.?|approximately|or so|ish)$',
    ]
    
    for pattern in approx_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            is_approximate = True
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
    
    # Try to parse remaining as number
    num = parse_numeric_value(text.strip())
    
    return num, is_approximate


def extract_number_with_unit(text: str) -> Tuple[Optional[float], Optional[str]]:
    """Extract number and unit from text like '50 kg', '200 units'."""
    if not isinstance(text, str):
        return None, None
    
    text = text.strip()
    
    # Pattern: number followed by unit
    match = re.match(r'^([\d,.\-+]+)\s*([a-zA-Z%]+)$', text)
    if match:
        num = parse_numeric_value(match.group(1))
        unit = match.group(2)
        return num, unit
    
    # Pattern: unit followed by number
    match = re.match(r'^([a-zA-Z$€£¥₹]+)\s*([\d,.\-+]+)$', text)
    if match:
        unit = match.group(1)
        num = parse_numeric_value(match.group(2))
        return num, unit
    
    return None, None


# ============================================================================
# HELPER FUNCTIONS — PERCENTAGE
# ============================================================================

def parse_percentage(value: Any) -> Optional[float]:
    """Parse percentage value, removing % symbol."""
    if value is None:
        return None
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, str):
        value = value.strip().rstrip('%').strip()
        # Handle word percentages
        word_match = re.match(r'^(\w+)\s*(?:percent|pct)?$', value, re.IGNORECASE)
        if word_match:
            word_num = word_to_number(word_match.group(1))
            if word_num is not None:
                return word_num
        
        return parse_numeric_value(value)
    
    return None


def detect_percentage_format(series: pd.Series) -> str:
    """Detect if percentages are in 0-1 (decimal) or 0-100 (whole) format."""
    numeric = pd.to_numeric(series, errors='coerce').dropna()
    
    if len(numeric) == 0:
        return "unknown"
    
    # If all values between 0 and 1, likely decimal format
    if (numeric >= 0).all() and (numeric <= 1).all():
        return "decimal"
    
    # If values between 0 and 100, likely percentage format
    if (numeric >= 0).all() and (numeric <= 100).all():
        return "whole"
    
    # Mixed or out of range
    return "mixed"


# ============================================================================
# HELPER FUNCTIONS — SCORE/GRADE
# ============================================================================

def detect_score_scale(series: pd.Series) -> Tuple[str, float, float]:
    """Detect the scale of scores (out of 10, 100, 4.0 GPA, etc.)."""
    numeric = pd.to_numeric(series, errors='coerce').dropna()
    
    if len(numeric) == 0:
        return "unknown", 0, 100
    
    max_val = numeric.max()
    min_val = numeric.min()
    
    # GPA 4.0 scale
    if max_val <= 4.0 and min_val >= 0:
        return "gpa_4", 0, 4.0
    
    # GPA 5.0 scale (weighted)
    if max_val <= 5.0 and min_val >= 0:
        return "gpa_5", 0, 5.0
    
    # Out of 10
    if max_val <= 10 and min_val >= 0:
        return "scale_10", 0, 10
    
    # Out of 100
    if max_val <= 100 and min_val >= 0:
        return "scale_100", 0, 100
    
    # Custom scale
    return "custom", min_val, max_val


def letter_to_gpa(letter: str, scale: str = "4.0") -> Optional[float]:
    """Convert letter grade to GPA value."""
    letter = letter.upper().strip()
    
    if scale == "5.0" or scale == "gpa_5":
        return GPA_5_SCALE.get(letter)
    return GPA_4_SCALE.get(letter)


def gpa_to_letter(gpa: float) -> str:
    """Convert GPA to letter grade."""
    if gpa >= 4.0:
        return "A"
    elif gpa >= 3.7:
        return "A-"
    elif gpa >= 3.3:
        return "B+"
    elif gpa >= 3.0:
        return "B"
    elif gpa >= 2.7:
        return "B-"
    elif gpa >= 2.3:
        return "C+"
    elif gpa >= 2.0:
        return "C"
    elif gpa >= 1.7:
        return "C-"
    elif gpa >= 1.3:
        return "D+"
    elif gpa >= 1.0:
        return "D"
    else:
        return "F"


def parse_rating_ratio(text: str) -> Optional[float]:
    """Parse rating like '4/5', '8/10', '4 out of 5' to percentage."""
    if not isinstance(text, str):
        return None
    
    text = text.strip()
    
    # Pattern: X/Y or X of Y
    match = re.match(r'^([\d.]+)\s*(?:/|out of|of)\s*([\d.]+)$', text, re.IGNORECASE)
    if match:
        try:
            numerator = float(match.group(1))
            denominator = float(match.group(2))
            if denominator > 0:
                return (numerator / denominator) * 100
        except ValueError:
            pass
    
    return None


def fix_grade_descriptor_typo(text: str) -> Tuple[str, bool]:
    """Fix common typos in grade descriptors. Returns (fixed, was_typo)."""
    if not isinstance(text, str):
        return text, False
    
    lower = text.lower().strip()
    if lower in GRADE_DESCRIPTOR_TYPOS:
        return GRADE_DESCRIPTOR_TYPOS[lower], True
    
    return text, False


# ============================================================================
# HELPER FUNCTIONS — RANK
# ============================================================================

def parse_ordinal(text: str) -> Optional[int]:
    """Parse ordinal like '1st', '2nd', 'first' to integer."""
    if not isinstance(text, str):
        return None
    
    text = text.strip().lower()
    
    # Word ordinals
    if text in WORD_TO_NUMBER:
        return int(WORD_TO_NUMBER[text])
    
    # Numeric ordinals
    match = re.match(r'^(\d+)(?:st|nd|rd|th)?$', text)
    if match:
        return int(match.group(1))
    
    return None


def check_rank_uniqueness(series: pd.Series, group_col: Optional[pd.Series] = None) -> List[int]:
    """Check for duplicate ranks, returns list of row indices with duplicates."""
    duplicates = []
    
    if group_col is not None:
        # Check uniqueness within each group
        for group_val in group_col.unique():
            mask = group_col == group_val
            group_ranks = series[mask]
            dup_mask = group_ranks.duplicated(keep=False)
            duplicates.extend(group_ranks[dup_mask].index.tolist())
    else:
        # Check overall uniqueness
        dup_mask = series.duplicated(keep=False)
        duplicates = series[dup_mask].index.tolist()
    
    return duplicates


def check_rank_sequence(series: pd.Series) -> List[int]:
    """Check for gaps in rank sequence, returns list of missing ranks."""
    numeric = pd.to_numeric(series, errors='coerce').dropna().astype(int)
    if len(numeric) == 0:
        return []
    
    expected = set(range(1, int(numeric.max()) + 1))
    actual = set(numeric.tolist())
    missing = sorted(expected - actual)
    
    return missing


# ============================================================================
# HELPER FUNCTIONS — CALCULATED COLUMNS
# ============================================================================

def discover_formula(df: pd.DataFrame, target_col: str) -> Optional[Tuple[str, List[str], float]]:
    """
    Attempt to discover the formula for a calculated column.
    Returns (formula_type, source_columns, confidence) or None.
    """
    target = pd.to_numeric(df[target_col], errors='coerce')
    target_valid = target.notna()
    
    if target_valid.sum() < 5:  # Need at least 5 rows
        return None
    
    numeric_cols = [c for c in df.columns if c != target_col]
    numeric_data = {}
    for col in numeric_cols:
        numeric_data[col] = pd.to_numeric(df[col], errors='coerce')
    
    best_formula = None
    best_confidence = 0.0
    
    # Test two-column formulas
    for col1 in numeric_data:
        for col2 in numeric_data:
            if col1 >= col2:
                continue
            
            a = numeric_data[col1]
            b = numeric_data[col2]
            
            # Test: A * B
            result = a * b
            match_rate = ((result - target).abs() < 0.01).sum() / target_valid.sum()
            if match_rate > best_confidence:
                best_confidence = match_rate
                best_formula = ("multiply", [col1, col2], match_rate)
            
            # Test: A + B
            result = a + b
            match_rate = ((result - target).abs() < 0.01).sum() / target_valid.sum()
            if match_rate > best_confidence:
                best_confidence = match_rate
                best_formula = ("add", [col1, col2], match_rate)
            
            # Test: A - B
            result = a - b
            match_rate = ((result - target).abs() < 0.01).sum() / target_valid.sum()
            if match_rate > best_confidence:
                best_confidence = match_rate
                best_formula = ("subtract", [col1, col2], match_rate)
            
            # Test: A / B (where B != 0)
            with np.errstate(divide='ignore', invalid='ignore'):
                result = a / b
                valid_div = b != 0
                if valid_div.any():
                    match_rate = ((result - target).abs() < 0.01)[valid_div].sum() / valid_div.sum()
                    if match_rate > best_confidence:
                        best_confidence = match_rate
                        best_formula = ("divide", [col1, col2], match_rate)
    
    if best_formula and best_confidence >= 0.9:  # 90% confidence threshold
        return best_formula
    
    return None


def verify_calculated_value(row: pd.Series, formula_type: str, source_cols: List[str], 
                           target_col: str, tolerance: float = 0.01) -> bool:
    """Verify a single row's calculated value matches the formula."""
    try:
        values = [float(row[col]) for col in source_cols]
        expected = float(row[target_col])
        
        if formula_type == "multiply":
            result = values[0] * values[1]
        elif formula_type == "add":
            result = sum(values)
        elif formula_type == "subtract":
            result = values[0] - values[1]
        elif formula_type == "divide":
            if values[1] == 0:
                return False
            result = values[0] / values[1]
        else:
            return True  # Unknown formula, don't flag
        
        return abs(result - expected) <= tolerance
    except (ValueError, TypeError, KeyError):
        return True  # Can't verify, don't flag


# ============================================================================
# HELPER FUNCTIONS — SCIENTIFIC NOTATION
# ============================================================================

def is_scientific_notation(value: str) -> bool:
    """Check if value is in scientific notation."""
    if not isinstance(value, str):
        return False
    return bool(re.match(r'^[+-]?\d+\.?\d*[eE][+-]?\d+$', value.strip()))


def convert_scientific_notation(value: str) -> str:
    """Convert scientific notation to standard decimal string."""
    try:
        num = float(value)
        # Format with enough precision
        return f"{num:.10f}".rstrip('0').rstrip('.')
    except ValueError:
        return value


# ============================================================================
# MAIN CLASS
# ============================================================================

class NumericFinancialRules:
    """
    Applies Numeric & Financial cleaning rules.
    
    Covers HTYPEs:
    - HTYPE-015: Amount/Currency/Revenue (AMT formulas)
    - HTYPE-016: Quantity/Count (QTY formulas)
    - HTYPE-017: Percentage/Rate/Ratio (PCT formulas)
    - HTYPE-021: Score/Rating/Grade/GPA (SCORE formulas)
    - HTYPE-042: Currency Code (CUR formulas)
    - HTYPE-043: Rank/Ordinal (RANK formulas)
    - HTYPE-044: Calculated/Derived Column (CALC formulas)
    """
    
    APPLICABLE_HTYPES = {
        "HTYPE-015",  # Amount/Currency
        "HTYPE-016",  # Quantity
        "HTYPE-017",  # Percentage
        "HTYPE-021",  # Score/Grade
        "HTYPE-042",  # Currency Code
        "HTYPE-043",  # Rank
        "HTYPE-044",  # Calculated
    }
    
    def __init__(self, job_id: int, df: pd.DataFrame, db, htype_map: Dict[str, str]):
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.htype_map = htype_map
        self.flags: List[Dict[str, Any]] = []
        self.results: List[CleaningResult] = []
        
        # Store detected info
        self.detected_currencies: Dict[str, str] = {}  # col -> currency
        self.detected_scales: Dict[str, Tuple[str, float, float]] = {}  # col -> (scale_type, min, max)
        self.detected_formulas: Dict[str, Tuple[str, List[str]]] = {}  # col -> (formula, source_cols)
    
    def log_cleaning(self, result: CleaningResult):
        """Log a cleaning operation to the database."""
        log = CleaningLog(
            job_id=self.job_id,
            column_name=result.column,
            action=result.formula_id,
            reason=f"Applied {result.formula_id}: {result.changes_made} changes, {result.rows_flagged} flagged",
            formula_id=result.formula_id,
            was_auto_applied=result.was_auto_applied,
            timestamp=datetime.utcnow(),
        )
        self.db.add(log)
        self.db.flush()
    
    def add_flag(self, row_idx: int, column: str, formula_id: str, 
                 reason: str, value: Any, severity: str = "warning"):
        """Add a flag for manual review."""
        self.flags.append({
            "row": row_idx,
            "column": column,
            "formula": formula_id,
            "reason": reason,
            "value": value,
            "severity": severity,
        })
    
    def _ensure_object_dtype(self, col: str):
        """Ensure column has object dtype for mixed type assignment (pandas 3.0 compatibility)."""
        if col in self.df.columns and self.df[col].dtype in ['string', 'object']:
            self.df[col] = self.df[col].astype(object)
    
    # ========================================================================
    # AMT FORMULAS (HTYPE-015: Amount/Currency/Revenue)
    # ========================================================================
    
    def AMT_01_currency_symbol_removal(self, col: str) -> CleaningResult:
        """AMT-01: Strip currency symbols, store as pure numeric."""
        result = CleaningResult(column=col, formula_id="AMT-01")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            currency, cleaned = extract_currency_symbol(str(val))
            
            if currency:
                # Store detected currency
                if col not in self.detected_currencies:
                    self.detected_currencies[col] = currency
                
                # Parse to numeric
                num_val = parse_numeric_value(cleaned)
                if num_val is not None:
                    self.df.at[idx, col] = num_val
                    result.changes_made += 1
        
        if result.changes_made > 0:
            result.details["detected_currency"] = self.detected_currencies.get(col)
            self.log_cleaning(result)
        
        return result
    
    def AMT_02_thousand_separator_removal(self, col: str) -> CleaningResult:
        """AMT-02: Remove thousand separators (commas)."""
        result = CleaningResult(column=col, formula_id="AMT-02")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            if ',' in val:
                cleaned = remove_thousand_separators(val)
                if cleaned != val:
                    num_val = parse_numeric_value(cleaned)
                    if num_val is not None:
                        self.df.at[idx, col] = num_val
                        result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def AMT_03_european_notation_conversion(self, col: str) -> CleaningResult:
        """AMT-03: Convert European notation (1.234,56 -> 1234.56)."""
        result = CleaningResult(column=col, formula_id="AMT-03")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            if detect_european_notation(val):
                converted = convert_european_notation(val)
                num_val = parse_numeric_value(converted)
                if num_val is not None:
                    self.df.at[idx, col] = num_val
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def AMT_04_decimal_standardization(self, col: str) -> CleaningResult:
        """AMT-04: Standardize to 2 decimal places."""
        result = CleaningResult(column=col, formula_id="AMT-04")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            num_val = parse_numeric_value(val)
            if num_val is not None:
                standardized = standardize_decimals(num_val, 2)
                if standardized != num_val:
                    self.df.at[idx, col] = standardized
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def AMT_05_negative_value_validation(self, col: str) -> CleaningResult:
        """AMT-05: Flag negative values in revenue/sales contexts."""
        result = CleaningResult(column=col, formula_id="AMT-05")
        
        # Detect if column name suggests non-negative context
        col_lower = col.lower()
        non_negative_keywords = ['revenue', 'sales', 'price', 'cost', 'fee', 'amount', 'total']
        is_non_negative_context = any(kw in col_lower for kw in non_negative_keywords)
        
        # Allow negatives in profit/loss, adjustment columns
        allow_negative_keywords = ['profit', 'loss', 'adjustment', 'change', 'difference', 'net']
        allow_negatives = any(kw in col_lower for kw in allow_negative_keywords)
        
        if is_non_negative_context and not allow_negatives:
            for idx, val in self.df[col].items():
                num_val = parse_numeric_value(val)
                if num_val is not None and num_val < 0:
                    self.add_flag(idx, col, "AMT-05", 
                                 "Negative value in non-negative context", val)
                    result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def AMT_06_outlier_detection(self, col: str) -> CleaningResult:
        """AMT-06: Flag statistical outliers (> 3 std dev from median)."""
        result = CleaningResult(column=col, formula_id="AMT-06")
        
        numeric_series = pd.to_numeric(self.df[col], errors='coerce')
        outlier_mask = detect_outliers_zscore(numeric_series, threshold=3.0)
        
        for idx in self.df.index[outlier_mask]:
            self.add_flag(idx, col, "AMT-06",
                         "Statistical outlier (>3 std dev)", self.df.at[idx, col])
            result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def AMT_07_zero_value_alert(self, col: str) -> CleaningResult:
        """AMT-07: Flag zero values that may indicate missing data."""
        result = CleaningResult(column=col, formula_id="AMT-07")
        
        # Count zeros vs non-zeros
        numeric_series = pd.to_numeric(self.df[col], errors='coerce')
        zero_mask = numeric_series == 0
        zero_count = zero_mask.sum()
        total_count = numeric_series.notna().sum()
        
        # Flag if zeros are rare (< 5% of data)
        if total_count > 0 and zero_count > 0:
            zero_pct = zero_count / total_count
            if zero_pct < 0.05:  # Zeros are unusual
                for idx in self.df.index[zero_mask]:
                    self.add_flag(idx, col, "AMT-07",
                                 "Zero value - possibly missing data", 0, severity="info")
                    result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            result.details["zero_percentage"] = f"{zero_pct*100:.1f}%" if total_count > 0 else "N/A"
            self.log_cleaning(result)
        
        return result
    
    def AMT_08_type_coercion(self, col: str) -> CleaningResult:
        """AMT-08: Convert string numbers to float."""
        result = CleaningResult(column=col, formula_id="AMT-08")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str):
                num_val = parse_numeric_value(val)
                if num_val is not None:
                    self.df.at[idx, col] = num_val
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def AMT_09_currency_unification(self, col: str) -> CleaningResult:
        """AMT-09: Detect mixed currencies and flag for conversion."""
        result = CleaningResult(column=col, formula_id="AMT-09")
        
        detected_currencies = set()
        rows_with_currency = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            currency, _ = extract_currency_symbol(str(val))
            if currency:
                detected_currencies.add(currency)
                rows_with_currency.append((idx, currency))
        
        if len(detected_currencies) > 1:
            result.details["currencies_detected"] = list(detected_currencies)
            for idx, currency in rows_with_currency:
                self.add_flag(idx, col, "AMT-09",
                             f"Mixed currency detected: {currency}", 
                             self.df.at[idx, col])
                result.rows_flagged += 1
            
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def AMT_12_scientific_notation_conversion(self, col: str) -> CleaningResult:
        """AMT-12: Convert scientific notation to standard decimal."""
        result = CleaningResult(column=col, formula_id="AMT-12")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str) and is_scientific_notation(val):
                converted = convert_scientific_notation(val)
                num_val = parse_numeric_value(converted)
                if num_val is not None:
                    self.df.at[idx, col] = num_val
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def AMT_13_word_to_number_conversion(self, col: str) -> CleaningResult:
        """AMT-13: Convert word amounts to numeric."""
        result = CleaningResult(column=col, formula_id="AMT-13")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str):
                # Skip if already numeric-looking
                if re.match(r'^[\d,.\-+]+$', val.strip()):
                    continue
                
                num_val = word_to_number(val)
                if num_val is not None:
                    self.df.at[idx, col] = num_val
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # QTY FORMULAS (HTYPE-016: Quantity/Count)
    # ========================================================================
    
    def QTY_01_word_to_number(self, col: str) -> CleaningResult:
        """QTY-01: Convert word numbers to numeric."""
        result = CleaningResult(column=col, formula_id="QTY-01")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str):
                if re.match(r'^[\d,.\-+]+$', val.strip()):
                    continue
                
                num_val = word_to_number(val)
                if num_val is not None:
                    self.df.at[idx, col] = int(num_val)
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def QTY_02_spelled_number_typo(self, col: str) -> CleaningResult:
        """QTY-02: Fix typos in spelled-out numbers."""
        result = CleaningResult(column=col, formula_id="QTY-02")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            lower_val = val.lower().strip()
            
            # Check for typos
            for typo, correct in WORD_NUMBER_TYPOS.items():
                if typo in lower_val:
                    corrected = re.sub(r'\b' + typo + r'\b', correct, lower_val)
                    num_val = word_to_number(corrected)
                    if num_val is not None:
                        self.df.at[idx, col] = int(num_val)
                        result.changes_made += 1
                        break
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def QTY_03_mixed_text_numeric_extraction(self, col: str) -> CleaningResult:
        """QTY-03: Extract numeric from text like 'approx 50', 'about 100'."""
        result = CleaningResult(column=col, formula_id="QTY-03")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            num, is_approx = extract_number_with_approximation(val)
            if num is not None and is_approx:
                self.df.at[idx, col] = int(num)
                self.add_flag(idx, col, "QTY-03",
                             "Approximate value extracted", val, severity="info")
                result.changes_made += 1
                result.rows_flagged += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def QTY_04_integer_enforcement(self, col: str) -> CleaningResult:
        """QTY-04: Flag decimals in integer-expected fields."""
        result = CleaningResult(column=col, formula_id="QTY-04")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            num_val = parse_numeric_value(val)
            if num_val is not None:
                if num_val != int(num_val):
                    # Check if minor rounding error
                    if abs(num_val - round(num_val)) < 0.001:
                        self.df.at[idx, col] = int(round(num_val))
                        result.changes_made += 1
                    else:
                        self.add_flag(idx, col, "QTY-04",
                                     "Decimal in integer-expected field", val)
                        result.rows_flagged += 1
                else:
                    # Ensure stored as int
                    self.df.at[idx, col] = int(num_val)
        
        if result.changes_made > 0 or result.rows_flagged > 0:
            self.log_cleaning(result)
        
        return result
    
    def QTY_05_negative_rejection(self, col: str) -> CleaningResult:
        """QTY-05: Flag negative quantities."""
        result = CleaningResult(column=col, formula_id="QTY-05")
        
        for idx, val in self.df[col].items():
            num_val = parse_numeric_value(val)
            if num_val is not None and num_val < 0:
                self.add_flag(idx, col, "QTY-05",
                             "Negative quantity", val)
                result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def QTY_06_outlier_detection(self, col: str) -> CleaningResult:
        """QTY-06: Flag statistical outliers."""
        result = CleaningResult(column=col, formula_id="QTY-06")
        
        numeric_series = pd.to_numeric(self.df[col], errors='coerce')
        outlier_mask = detect_outliers_zscore(numeric_series, threshold=3.0)
        
        for idx in self.df.index[outlier_mask]:
            self.add_flag(idx, col, "QTY-06",
                         "Statistical outlier", self.df.at[idx, col])
            result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def QTY_07_zero_value_handling(self, col: str) -> CleaningResult:
        """QTY-07: Flag unexpected zero values."""
        result = CleaningResult(column=col, formula_id="QTY-07")
        
        numeric_series = pd.to_numeric(self.df[col], errors='coerce')
        zero_mask = numeric_series == 0
        zero_count = zero_mask.sum()
        total_count = numeric_series.notna().sum()
        
        # Flag if zeros are rare
        if total_count > 0 and zero_count > 0:
            zero_pct = zero_count / total_count
            if zero_pct < 0.05:
                for idx in self.df.index[zero_mask]:
                    self.add_flag(idx, col, "QTY-07",
                                 "Unexpected zero quantity", 0, severity="info")
                    result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def QTY_09_unit_separation(self, col: str) -> CleaningResult:
        """QTY-09: Separate number from unit like '50 kg'."""
        result = CleaningResult(column=col, formula_id="QTY-09")
        
        units_detected = set()
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            num, unit = extract_number_with_unit(val)
            if num is not None and unit:
                self.df.at[idx, col] = num
                units_detected.add(unit)
                result.changes_made += 1
        
        # Add unit column if units were found
        if units_detected and result.changes_made > 0:
            unit_col = f"{col}_unit"
            if unit_col not in self.df.columns:
                self.df[unit_col] = None
            
            for idx, val in self.df[col].items():
                if pd.isna(val) or not isinstance(val, str):
                    continue
                num, unit = extract_number_with_unit(str(val))
                if unit:
                    self.df.at[idx, unit_col] = unit
            
            result.details["units_detected"] = list(units_detected)
            result.details["unit_column_created"] = unit_col
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # PCT FORMULAS (HTYPE-017: Percentage/Rate/Ratio)
    # ========================================================================
    
    def PCT_01_percentage_symbol_removal(self, col: str) -> CleaningResult:
        """PCT-01: Remove % symbol."""
        result = CleaningResult(column=col, formula_id="PCT-01")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str) and '%' in val:
                num_val = parse_percentage(val)
                if num_val is not None:
                    self.df.at[idx, col] = num_val
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def PCT_02_range_validation(self, col: str) -> CleaningResult:
        """PCT-02: Validate percentage range (0-100 typical)."""
        result = CleaningResult(column=col, formula_id="PCT-02")
        
        # Check if growth rate context (allows > 100)
        col_lower = col.lower()
        growth_keywords = ['growth', 'change', 'increase', 'decrease', 'yoy', 'mom']
        is_growth_context = any(kw in col_lower for kw in growth_keywords)
        
        for idx, val in self.df[col].items():
            num_val = parse_numeric_value(val)
            if num_val is not None:
                if not is_growth_context:
                    if num_val < 0 or num_val > 100:
                        self.add_flag(idx, col, "PCT-02",
                                     f"Percentage out of 0-100 range: {num_val}", val)
                        result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def PCT_03_decimal_vs_whole_detection(self, col: str) -> CleaningResult:
        """PCT-03: Detect and standardize decimal (0.85) vs whole (85) format."""
        result = CleaningResult(column=col, formula_id="PCT-03")
        self._ensure_object_dtype(col)
        
        format_type = detect_percentage_format(self.df[col])
        result.details["detected_format"] = format_type
        
        # If all values 0-1, likely decimal format - convert to whole
        if format_type == "decimal":
            for idx, val in self.df[col].items():
                num_val = parse_numeric_value(val)
                if num_val is not None and 0 <= num_val <= 1:
                    self.df.at[idx, col] = num_val * 100
                    result.changes_made += 1
            
            if result.changes_made > 0:
                result.details["conversion"] = "decimal to whole (x100)"
                self.log_cleaning(result)
        
        return result
    
    def PCT_04_outlier_alert(self, col: str) -> CleaningResult:
        """PCT-04: Flag extreme percentage spikes."""
        result = CleaningResult(column=col, formula_id="PCT-04")
        
        numeric_series = pd.to_numeric(self.df[col], errors='coerce')
        outlier_mask = detect_outliers_iqr(numeric_series)
        
        for idx in self.df.index[outlier_mask]:
            self.add_flag(idx, col, "PCT-04",
                         "Extreme percentage value", self.df.at[idx, col])
            result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def PCT_06_word_to_number(self, col: str) -> CleaningResult:
        """PCT-06: Convert word percentages to numeric."""
        result = CleaningResult(column=col, formula_id="PCT-06")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            # Pattern: "eighty five percent"
            match = re.match(r'^(.+?)\s*(?:percent|pct|%)$', val.strip(), re.IGNORECASE)
            if match:
                word_part = match.group(1).strip()
                num_val = word_to_number(word_part)
                if num_val is not None:
                    self.df.at[idx, col] = num_val
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # SCORE FORMULAS (HTYPE-021: Score/Rating/Grade/GPA)
    # ========================================================================
    
    def SCORE_01_scale_detection(self, col: str) -> CleaningResult:
        """SCORE-01: Detect score scale (10, 100, 4.0 GPA, etc.)."""
        result = CleaningResult(column=col, formula_id="SCORE-01")
        
        scale_type, min_val, max_val = detect_score_scale(self.df[col])
        self.detected_scales[col] = (scale_type, min_val, max_val)
        
        result.details["scale_type"] = scale_type
        result.details["min_value"] = min_val
        result.details["max_value"] = max_val
        self.log_cleaning(result)
        
        return result
    
    def SCORE_02_range_enforcement(self, col: str) -> CleaningResult:
        """SCORE-02: Flag values outside detected scale."""
        result = CleaningResult(column=col, formula_id="SCORE-02")
        
        # Use detected scale or default
        if col in self.detected_scales:
            scale_type, min_val, max_val = self.detected_scales[col]
        else:
            scale_type, min_val, max_val = detect_score_scale(self.df[col])
        
        for idx, val in self.df[col].items():
            num_val = parse_numeric_value(val)
            if num_val is not None:
                if num_val < min_val or num_val > max_val:
                    self.add_flag(idx, col, "SCORE-02",
                                 f"Score outside range [{min_val}, {max_val}]", val)
                    result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def SCORE_03_gpa_4_scale(self, col: str) -> CleaningResult:
        """SCORE-03: Map letter grades to 4.0 GPA scale."""
        result = CleaningResult(column=col, formula_id="SCORE-03")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str):
                gpa = letter_to_gpa(val, "4.0")
                if gpa is not None:
                    self.df.at[idx, col] = gpa
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def SCORE_04_gpa_5_scale(self, col: str) -> CleaningResult:
        """SCORE-04: Handle weighted GPA (5.0 scale)."""
        result = CleaningResult(column=col, formula_id="SCORE-04")
        
        # Check if any values exceed 4.0
        numeric_series = pd.to_numeric(self.df[col], errors='coerce')
        if numeric_series.max() > 4.0:
            result.details["weighted_gpa_detected"] = True
            self.detected_scales[col] = ("gpa_5", 0, 5.0)
            self.log_cleaning(result)
        
        return result
    
    def SCORE_05_letter_to_numeric(self, col: str) -> CleaningResult:
        """SCORE-05: Map letter grades to percentage ranges."""
        result = CleaningResult(column=col, formula_id="SCORE-05")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str):
                letter = val.upper().strip()
                if letter in LETTER_TO_PERCENT:
                    # Use midpoint of range
                    range_vals = LETTER_TO_PERCENT[letter]
                    midpoint = (range_vals[0] + range_vals[1]) / 2
                    self.df.at[idx, col] = midpoint
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def SCORE_10_decimal_rounding(self, col: str) -> CleaningResult:
        """SCORE-10: Round to 2 decimal places."""
        result = CleaningResult(column=col, formula_id="SCORE-10")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            num_val = parse_numeric_value(val)
            if num_val is not None:
                rounded = round(num_val, 2)
                if rounded != num_val:
                    self.df.at[idx, col] = rounded
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def SCORE_12_rating_scale_normalization(self, col: str) -> CleaningResult:
        """SCORE-12: Normalize '4/5', '8/10' ratings to percentage."""
        result = CleaningResult(column=col, formula_id="SCORE-12")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str):
                pct = parse_rating_ratio(val)
                if pct is not None:
                    self.df.at[idx, col] = round(pct, 2)
                    result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def SCORE_13_grade_descriptor_typo(self, col: str) -> CleaningResult:
        """SCORE-13: Fix typos in grade descriptors."""
        result = CleaningResult(column=col, formula_id="SCORE-13")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            fixed, was_typo = fix_grade_descriptor_typo(val)
            if was_typo:
                self.df.at[idx, col] = fixed
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # CUR FORMULAS (HTYPE-042: Currency Code)
    # ========================================================================
    
    def CUR_01_iso_validation(self, col: str) -> CleaningResult:
        """CUR-01: Validate against ISO 4217 currency codes."""
        result = CleaningResult(column=col, formula_id="CUR-01")
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            code = str(val).strip().upper()
            if code and code not in ISO_4217_CODES:
                self.add_flag(idx, col, "CUR-01",
                             f"Invalid currency code: {code}", val)
                result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def CUR_02_uppercase_standardization(self, col: str) -> CleaningResult:
        """CUR-02: Uppercase currency codes."""
        result = CleaningResult(column=col, formula_id="CUR-02")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            upper = val.upper()
            if upper != val:
                self.df.at[idx, col] = upper
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def CUR_03_symbol_to_code(self, col: str) -> CleaningResult:
        """CUR-03: Convert currency symbols to ISO codes."""
        result = CleaningResult(column=col, formula_id="CUR-03")
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            if val_str in CURRENCY_SYMBOLS:
                self.df.at[idx, col] = CURRENCY_SYMBOLS[val_str]
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # RANK FORMULAS (HTYPE-043: Rank/Ordinal)
    # ========================================================================
    
    def RANK_01_ordinal_to_numeric(self, col: str) -> CleaningResult:
        """RANK-01: Convert ordinals (1st, 2nd, first, second) to integers."""
        result = CleaningResult(column=col, formula_id="RANK-01")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            rank = parse_ordinal(str(val))
            if rank is not None and str(val).lower().strip() != str(rank):
                self.df.at[idx, col] = rank
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def RANK_02_uniqueness_check(self, col: str) -> CleaningResult:
        """RANK-02: Check for duplicate ranks."""
        result = CleaningResult(column=col, formula_id="RANK-02")
        
        numeric_series = pd.to_numeric(self.df[col], errors='coerce')
        duplicates = check_rank_uniqueness(numeric_series)
        
        for idx in duplicates:
            self.add_flag(idx, col, "RANK-02",
                         "Duplicate rank detected", self.df.at[idx, col])
            result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def RANK_03_sequence_completeness(self, col: str) -> CleaningResult:
        """RANK-03: Check for gaps in rank sequence."""
        result = CleaningResult(column=col, formula_id="RANK-03")
        
        numeric_series = pd.to_numeric(self.df[col], errors='coerce')
        missing_ranks = check_rank_sequence(numeric_series)
        
        if missing_ranks:
            result.details["missing_ranks"] = missing_ranks
            result.rows_flagged = len(missing_ranks)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def RANK_04_negative_rejection(self, col: str) -> CleaningResult:
        """RANK-04: Flag non-positive ranks."""
        result = CleaningResult(column=col, formula_id="RANK-04")
        
        for idx, val in self.df[col].items():
            num_val = parse_numeric_value(val)
            if num_val is not None and num_val <= 0:
                self.add_flag(idx, col, "RANK-04",
                             "Rank must be positive", val)
                result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # CALC FORMULAS (HTYPE-044: Calculated/Derived Column)
    # ========================================================================
    
    def CALC_01_formula_discovery(self, col: str) -> CleaningResult:
        """CALC-01: Discover if column is derived from formula."""
        result = CleaningResult(column=col, formula_id="CALC-01")
        
        formula_info = discover_formula(self.df, col)
        
        if formula_info:
            formula_type, source_cols, confidence = formula_info
            self.detected_formulas[col] = (formula_type, source_cols)
            result.details["formula_type"] = formula_type
            result.details["source_columns"] = source_cols
            result.details["confidence"] = f"{confidence*100:.1f}%"
            self.log_cleaning(result)
        
        return result
    
    def CALC_02_row_verification(self, col: str) -> CleaningResult:
        """CALC-02: Verify formula holds for each row."""
        result = CleaningResult(column=col, formula_id="CALC-02")
        
        if col not in self.detected_formulas:
            return result
        
        formula_type, source_cols = self.detected_formulas[col]
        
        for idx in self.df.index:
            if not verify_calculated_value(self.df.loc[idx], formula_type, source_cols, col):
                self.add_flag(idx, col, "CALC-02",
                             f"Formula mismatch: expected {formula_type}({', '.join(source_cols)})",
                             self.df.at[idx, col])
                result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def CALC_03_missing_value_fill(self, col: str) -> CleaningResult:
        """CALC-03: Fill null calculated values from formula."""
        result = CleaningResult(column=col, formula_id="CALC-03")
        self._ensure_object_dtype(col)
        
        if col not in self.detected_formulas:
            return result
        
        formula_type, source_cols = self.detected_formulas[col]
        
        for idx in self.df.index:
            if pd.isna(self.df.at[idx, col]):
                # Check if source values are present
                try:
                    values = [float(self.df.at[idx, c]) for c in source_cols]
                    
                    if formula_type == "multiply":
                        calculated = values[0] * values[1]
                    elif formula_type == "add":
                        calculated = sum(values)
                    elif formula_type == "subtract":
                        calculated = values[0] - values[1]
                    elif formula_type == "divide" and values[1] != 0:
                        calculated = values[0] / values[1]
                    else:
                        continue
                    
                    self.df.at[idx, col] = round(calculated, 2)
                    result.changes_made += 1
                    self.add_flag(idx, col, "CALC-03",
                                 f"Value derived from formula", calculated, severity="info")
                    result.rows_flagged += 1
                except (ValueError, TypeError, KeyError):
                    continue
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_for_column(self, col: str, htype: str) -> List[CleaningResult]:
        """Run all applicable formulas for a column based on its HTYPE."""
        results = []
        
        if htype == "HTYPE-015":  # Amount/Currency/Revenue
            results.append(self.AMT_01_currency_symbol_removal(col))
            results.append(self.AMT_02_thousand_separator_removal(col))
            results.append(self.AMT_03_european_notation_conversion(col))
            results.append(self.AMT_13_word_to_number_conversion(col))
            results.append(self.AMT_12_scientific_notation_conversion(col))
            results.append(self.AMT_08_type_coercion(col))
            results.append(self.AMT_04_decimal_standardization(col))
            results.append(self.AMT_09_currency_unification(col))
            results.append(self.AMT_05_negative_value_validation(col))
            results.append(self.AMT_06_outlier_detection(col))
            results.append(self.AMT_07_zero_value_alert(col))
        
        elif htype == "HTYPE-016":  # Quantity/Count
            results.append(self.QTY_01_word_to_number(col))
            results.append(self.QTY_02_spelled_number_typo(col))
            results.append(self.QTY_03_mixed_text_numeric_extraction(col))
            results.append(self.QTY_09_unit_separation(col))
            results.append(self.QTY_04_integer_enforcement(col))
            results.append(self.QTY_05_negative_rejection(col))
            results.append(self.QTY_06_outlier_detection(col))
            results.append(self.QTY_07_zero_value_handling(col))
        
        elif htype == "HTYPE-017":  # Percentage/Rate/Ratio
            results.append(self.PCT_01_percentage_symbol_removal(col))
            results.append(self.PCT_06_word_to_number(col))
            results.append(self.PCT_03_decimal_vs_whole_detection(col))
            results.append(self.PCT_02_range_validation(col))
            results.append(self.PCT_04_outlier_alert(col))
        
        elif htype == "HTYPE-021":  # Score/Rating/Grade/GPA
            results.append(self.SCORE_01_scale_detection(col))
            results.append(self.SCORE_13_grade_descriptor_typo(col))
            results.append(self.SCORE_12_rating_scale_normalization(col))
            results.append(self.SCORE_03_gpa_4_scale(col))
            results.append(self.SCORE_04_gpa_5_scale(col))
            results.append(self.SCORE_05_letter_to_numeric(col))
            results.append(self.SCORE_10_decimal_rounding(col))
            results.append(self.SCORE_02_range_enforcement(col))
        
        elif htype == "HTYPE-042":  # Currency Code
            results.append(self.CUR_03_symbol_to_code(col))
            results.append(self.CUR_02_uppercase_standardization(col))
            results.append(self.CUR_01_iso_validation(col))
        
        elif htype == "HTYPE-043":  # Rank/Ordinal
            results.append(self.RANK_01_ordinal_to_numeric(col))
            results.append(self.RANK_04_negative_rejection(col))
            results.append(self.RANK_02_uniqueness_check(col))
            results.append(self.RANK_03_sequence_completeness(col))
        
        elif htype == "HTYPE-044":  # Calculated/Derived
            results.append(self.CALC_01_formula_discovery(col))
            results.append(self.CALC_02_row_verification(col))
            results.append(self.CALC_03_missing_value_fill(col))
        
        return results
    
    def run_all(self) -> Dict[str, Any]:
        """Run all applicable formulas for all columns."""
        columns_processed = 0
        total_changes = 0
        total_flags = 0
        formulas_applied = set()
        
        for col, htype in self.htype_map.items():
            if htype not in self.APPLICABLE_HTYPES:
                continue
            
            if col not in self.df.columns:
                continue
            
            columns_processed += 1
            results = self.run_for_column(col, htype)
            self.results.extend(results)
            
            for r in results:
                total_changes += r.changes_made
                total_flags += r.rows_flagged
                if r.changes_made > 0 or r.rows_flagged > 0:
                    formulas_applied.add(r.formula_id)
        
        return {
            "columns_processed": columns_processed,
            "total_changes": total_changes,
            "total_flags": total_flags,
            "formulas_applied": list(formulas_applied),
            "detected_currencies": self.detected_currencies,
            "detected_scales": {k: v[0] for k, v in self.detected_scales.items()},
            "detected_formulas": {k: v[0] for k, v in self.detected_formulas.items()},
        }
