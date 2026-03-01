"""
Boolean, Category & Status Cleaning Rules — Session 8

Implements formulas from the Formula Rulebook for:
- HTYPE-018: Boolean / Flag / Yes-No Field (BOOL-01 to BOOL-04)
- HTYPE-019: Category / Classification Label (CAT-01 to CAT-08)
- HTYPE-020: Status Field (STAT-01 to STAT-05)
- HTYPE-045: Survey / Likert Response (SURV-01 to SURV-07)
- HTYPE-046: Multi-Value / Tag Field (MULTI-01 to MULTI-07)

Logic First. AI Never.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter, defaultdict
from difflib import SequenceMatcher

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
# BOOLEAN CONSTANTS
# ============================================================================

# True equivalents (case-insensitive)
TRUE_VALUES = {
    "yes", "y", "1", "true", "t", "on", "active", "enabled",
    "checked", "positive", "affirmative", "yep", "yeah",
    "si", "oui", "ja", "da", "sim", "tak",  # International
}

# False equivalents (case-insensitive)
FALSE_VALUES = {
    "no", "n", "0", "false", "f", "off", "inactive", "disabled",
    "unchecked", "negative", "nope", "nah",
    "non", "nein", "nie", "nao",  # International
}

# Non-binary values that suggest this should be Status instead
NON_BINARY_VALUES = {
    "maybe", "perhaps", "pending", "unknown", "partial", "n/a",
    "not applicable", "tbd", "to be determined", "in progress",
}


# ============================================================================
# STATUS CONSTANTS
# ============================================================================

# Canonical status mappings
STATUS_MAPPINGS = {
    # Completed variants
    "completed": "Completed",
    "complete": "Completed",
    "done": "Completed",
    "finished": "Completed",
    "closed": "Completed",
    "resolved": "Completed",
    "fulfilled": "Completed",
    "delivered": "Completed",
    "shipped": "Completed",
    
    # Pending variants
    "pending": "Pending",
    "waiting": "Pending",
    "on hold": "Pending",
    "hold": "Pending",
    "paused": "Pending",
    "queued": "Pending",
    "scheduled": "Pending",
    "awaiting": "Pending",
    
    # Active variants
    "active": "Active",
    "ongoing": "Active",
    "in progress": "Active",
    "in-progress": "Active",
    "processing": "Active",
    "running": "Active",
    "started": "Active",
    "working": "Active",
    "open": "Active",
    
    # Cancelled variants
    "cancelled": "Cancelled",
    "canceled": "Cancelled",
    "void": "Cancelled",
    "voided": "Cancelled",
    "terminated": "Cancelled",
    "aborted": "Cancelled",
    "abandoned": "Cancelled",
    
    # New/Draft variants
    "new": "New",
    "draft": "Draft",
    "created": "New",
    "initialized": "New",
    
    # Failed variants
    "failed": "Failed",
    "error": "Failed",
    "rejected": "Failed",
    "declined": "Failed",
    
    # Approved variants
    "approved": "Approved",
    "accepted": "Approved",
    "confirmed": "Approved",
    "verified": "Approved",
}

# Workflow sequences (for validation)
WORKFLOW_SEQUENCES = {
    "standard": ["New", "Pending", "Active", "Completed"],
    "approval": ["Draft", "Pending", "Approved", "Completed"],
    "order": ["New", "Processing", "Shipped", "Delivered"],
}


# ============================================================================
# SURVEY / LIKERT CONSTANTS
# ============================================================================

# 5-point Likert scale
LIKERT_5_AGREE = {
    "strongly disagree": 1,
    "disagree": 2,
    "neutral": 3,
    "neither agree nor disagree": 3,
    "agree": 4,
    "strongly agree": 5,
}

# 7-point Likert scale
LIKERT_7_AGREE = {
    "strongly disagree": 1,
    "disagree": 2,
    "somewhat disagree": 3,
    "neutral": 4,
    "neither agree nor disagree": 4,
    "somewhat agree": 5,
    "agree": 6,
    "strongly agree": 7,
}

# Frequency scale
FREQUENCY_SCALE = {
    "never": 1,
    "rarely": 2,
    "seldom": 2,
    "sometimes": 3,
    "occasionally": 3,
    "often": 4,
    "frequently": 4,
    "always": 5,
    "constantly": 5,
}

# Satisfaction scale
SATISFACTION_SCALE = {
    "very dissatisfied": 1,
    "dissatisfied": 2,
    "neutral": 3,
    "satisfied": 4,
    "very satisfied": 5,
}

# Common Likert typos
LIKERT_TYPOS = {
    # Agree scale
    "stongly agree": "strongly agree",
    "stonrly agree": "strongly agree",
    "storngly agree": "strongly agree",
    "strongy agree": "strongly agree",
    "stronly agree": "strongly agree",
    "strongly agre": "strongly agree",
    "stongly disagree": "strongly disagree",
    "stonrly disagree": "strongly disagree",
    "disagre": "disagree",
    "agre": "agree",
    "nutral": "neutral",
    "netural": "neutral",
    "nuetral": "neutral",
    "neutra": "neutral",
    "nuetreal": "neutral",
    "neautral": "neutral",
    
    # Frequency scale
    "soemtimes": "sometimes",
    "somtimes": "sometimes",
    "sometmes": "sometimes",
    "allways": "always",
    "alwyas": "always",
    "nevr": "never",
    "raerly": "rarely",
    "rarley": "rarely",
    "oftem": "often",
    "freqeuntly": "frequently",
    "frequenly": "frequently",
    
    # Satisfaction scale
    "satisified": "satisfied",
    "satisfed": "satisfied",
    "satified": "satisfied",
    "dissatisified": "dissatisfied",
    "disatisfied": "dissatisfied",
}


# ============================================================================
# MULTI-VALUE CONSTANTS
# ============================================================================

# Common delimiters in multi-value fields
MULTI_VALUE_DELIMITERS = [",", ";", "|", "/", "&", " and ", "\n", "\\n"]


# ============================================================================
# HELPER FUNCTIONS — BOOLEAN
# ============================================================================

def normalize_boolean(value: Any) -> Optional[bool]:
    """Convert various boolean representations to Python bool.
    
    Args:
        value: Input value (string, int, bool, etc.)
        
    Returns:
        True, False, or None if not parseable as boolean
    """
    if value is None or pd.isna(value):
        return None
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        elif value == 0:
            return False
        return None
    
    if isinstance(value, str):
        val_lower = value.strip().lower()
        
        if val_lower in TRUE_VALUES:
            return True
        elif val_lower in FALSE_VALUES:
            return False
    
    return None


def is_non_binary_value(value: Any) -> bool:
    """Check if value is non-binary (should be Status instead of Boolean).
    
    Args:
        value: Input value
        
    Returns:
        True if value represents a non-binary state
    """
    if value is None or pd.isna(value):
        return False
    
    if isinstance(value, str):
        return value.strip().lower() in NON_BINARY_VALUES
    
    return False


def detect_boolean_column(series: pd.Series) -> Tuple[bool, float]:
    """Detect if a column is boolean-like.
    
    Args:
        series: pandas Series to analyze
        
    Returns:
        Tuple of (is_boolean, confidence)
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return False, 0.0
    
    boolean_count = 0
    non_binary_count = 0
    
    for val in non_null:
        if normalize_boolean(val) is not None:
            boolean_count += 1
        elif is_non_binary_value(val):
            non_binary_count += 1
    
    if non_binary_count > 0:
        # Has non-binary values, likely Status field
        return False, 0.0
    
    ratio = boolean_count / len(non_null)
    return ratio >= 0.9, ratio


# ============================================================================
# HELPER FUNCTIONS — CATEGORY
# ============================================================================

def to_title_case(value: str) -> str:
    """Convert string to title case, preserving certain patterns.
    
    Args:
        value: Input string
        
    Returns:
        Title-cased string
    """
    if not value:
        return value
    
    # Handle all-caps (likely acronym)
    if value.isupper() and len(value) <= 5:
        return value
    
    # Handle common patterns that should stay uppercase
    preserve_upper = ["IT", "HR", "US", "UK", "EU", "UN", "AI", "ML", "DB"]
    
    words = value.split()
    result = []
    
    for word in words:
        upper_word = word.upper()
        if upper_word in preserve_upper:
            result.append(upper_word)
        else:
            result.append(word.capitalize())
    
    return " ".join(result)


def clean_category_whitespace(value: str) -> str:
    """Clean whitespace in category values.
    
    Args:
        value: Input string
        
    Returns:
        Cleaned string with normalized whitespace
    """
    if not value:
        return value
    
    # Remove leading/trailing whitespace
    cleaned = value.strip()
    
    # Normalize internal whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    return cleaned


def fix_encoding_artifacts(value: str) -> str:
    """Fix common encoding artifacts in text.
    
    Args:
        value: Input string with potential encoding issues
        
    Returns:
        Fixed string
    """
    if not value:
        return value
    
    # Common encoding artifact replacements (using raw patterns)
    replacements = [
        (b"\xe2\x80\x99".decode('utf-8', errors='ignore'), "'"),  # Right single quote
        (b"\xe2\x80\x9c".decode('utf-8', errors='ignore'), '"'),  # Left double quote
        (b"\xe2\x80\x9d".decode('utf-8', errors='ignore'), '"'),  # Right double quote
        (b"\xe2\x80\x94".decode('utf-8', errors='ignore'), "-"),  # Em dash
        (b"\xe2\x80\x93".decode('utf-8', errors='ignore'), "-"),  # En dash
        (b"\xc2\xa0".decode('utf-8', errors='ignore'), " "),      # Non-breaking space
    ]
    
    result = value
    for pattern, replacement in replacements:
        if pattern:
            result = result.replace(pattern, replacement)
    
    # Try to normalize unicode
    try:
        result = unicodedata.normalize('NFKC', result)
    except:
        pass
    
    return result


def calculate_similarity(s1: str, s2: str) -> float:
    """Calculate string similarity using SequenceMatcher.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity ratio (0.0 to 1.0)
    """
    if not s1 or not s2:
        return 0.0
    
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def find_similar_categories(value: str, existing_values: Set[str], 
                           threshold: float = 0.85) -> Optional[str]:
    """Find similar category from existing values.
    
    Args:
        value: Value to match
        existing_values: Set of existing category values
        threshold: Minimum similarity threshold
        
    Returns:
        Best matching existing value or None
    """
    if not value or not existing_values:
        return None
    
    best_match = None
    best_score = threshold
    
    for existing in existing_values:
        score = calculate_similarity(value, existing)
        if score > best_score:
            best_score = score
            best_match = existing
    
    return best_match


def get_category_frequencies(series: pd.Series) -> Dict[str, int]:
    """Get frequency counts for each category.
    
    Args:
        series: pandas Series
        
    Returns:
        Dictionary of value -> count
    """
    non_null = series.dropna()
    return dict(Counter(non_null))


def detect_rare_categories(series: pd.Series, threshold: float = 0.01) -> List[str]:
    """Detect categories appearing in less than threshold of rows.
    
    Args:
        series: pandas Series
        threshold: Minimum frequency threshold (default 1%)
        
    Returns:
        List of rare category values
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return []
    
    frequencies = get_category_frequencies(non_null)
    total = len(non_null)
    min_count = total * threshold
    
    return [val for val, count in frequencies.items() if count < min_count]


# ============================================================================
# HELPER FUNCTIONS — STATUS
# ============================================================================

def normalize_status(value: str) -> Optional[str]:
    """Normalize status value to canonical form.
    
    Args:
        value: Input status string
        
    Returns:
        Canonical status or None
    """
    if not value:
        return None
    
    val_lower = value.strip().lower()
    return STATUS_MAPPINGS.get(val_lower)


def detect_workflow_type(series: pd.Series) -> Optional[str]:
    """Detect which workflow sequence the status values follow.
    
    Args:
        series: pandas Series of status values
        
    Returns:
        Workflow type name or None
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return None
    
    # Get unique normalized values
    normalized = set()
    for val in non_null.unique():
        norm = normalize_status(str(val))
        if norm:
            normalized.add(norm)
    
    # Match against known workflows
    best_match = None
    best_overlap = 0
    
    for workflow_name, sequence in WORKFLOW_SEQUENCES.items():
        workflow_set = set(sequence)
        overlap = len(normalized & workflow_set)
        if overlap > best_overlap:
            best_overlap = overlap
            best_match = workflow_name
    
    return best_match


def validate_workflow_sequence(df: pd.DataFrame, status_col: str, 
                               date_col: Optional[str] = None) -> List[int]:
    """Validate that status progression follows logical sequence.
    
    Args:
        df: DataFrame
        status_col: Status column name
        date_col: Optional date column for temporal ordering
        
    Returns:
        List of row indices with sequence violations
    """
    violations = []
    
    workflow_type = detect_workflow_type(df[status_col])
    if not workflow_type or workflow_type not in WORKFLOW_SEQUENCES:
        return violations
    
    sequence = WORKFLOW_SEQUENCES[workflow_type]
    sequence_order = {status: idx for idx, status in enumerate(sequence)}
    
    # If we have a date column, check temporal sequence
    if date_col and date_col in df.columns:
        # Group by some identifier if available, otherwise check global sequence
        pass
    
    # For now, just flag obviously invalid statuses
    for idx, val in df[status_col].items():
        if pd.isna(val):
            continue
        
        norm = normalize_status(str(val))
        if norm and norm not in sequence:
            # Status exists but not in expected workflow
            violations.append(idx)
    
    return violations


def detect_retired_status(series: pd.Series, 
                          recent_threshold: float = 0.2) -> List[str]:
    """Detect status values that appear only in older records.
    
    This is a simplified version that just checks for very rare values.
    In a full implementation, this would look at date columns.
    
    Args:
        series: pandas Series of status values
        recent_threshold: Threshold for considering a value "retired"
        
    Returns:
        List of potentially retired status values
    """
    frequencies = get_category_frequencies(series.dropna())
    total = sum(frequencies.values())
    
    if total == 0:
        return []
    
    # Values appearing in < 1% of records might be retired
    return [val for val, count in frequencies.items() 
            if count / total < 0.01]


# ============================================================================
# HELPER FUNCTIONS — SURVEY / LIKERT
# ============================================================================

def detect_likert_scale(series: pd.Series) -> Tuple[str, int, Dict[str, int]]:
    """Detect the type and size of Likert scale.
    
    Args:
        series: pandas Series of survey responses
        
    Returns:
        Tuple of (scale_type, scale_size, mapping_dict)
    """
    non_null = series.dropna()
    if len(non_null) == 0:
        return "unknown", 0, {}
    
    # Check for numeric values
    numeric_vals = pd.to_numeric(non_null, errors='coerce').dropna()
    if len(numeric_vals) > 0:
        min_val = numeric_vals.min()
        max_val = numeric_vals.max()
        
        if min_val >= 1 and max_val <= 5:
            return "numeric_5", 5, {}
        elif min_val >= 1 and max_val <= 7:
            return "numeric_7", 7, {}
        elif min_val >= 1 and max_val <= 10:
            return "numeric_10", 10, {}
    
    # Check for verbal scales
    verbal_vals = set()
    for val in non_null:
        if isinstance(val, str):
            verbal_vals.add(val.lower().strip())
    
    # Check against known scales
    if verbal_vals & set(LIKERT_5_AGREE.keys()):
        # Check if more 7-point indicators
        if "somewhat agree" in verbal_vals or "somewhat disagree" in verbal_vals:
            return "agree_7", 7, LIKERT_7_AGREE
        return "agree_5", 5, LIKERT_5_AGREE
    
    if verbal_vals & set(FREQUENCY_SCALE.keys()):
        return "frequency", 5, FREQUENCY_SCALE
    
    if verbal_vals & set(SATISFACTION_SCALE.keys()):
        return "satisfaction", 5, SATISFACTION_SCALE
    
    return "unknown", 0, {}


def verbal_to_numeric_likert(value: str, scale_mapping: Dict[str, int]) -> Optional[int]:
    """Convert verbal Likert response to numeric.
    
    Args:
        value: Verbal response
        scale_mapping: Dictionary mapping verbal to numeric
        
    Returns:
        Numeric value or None
    """
    if not value or not scale_mapping:
        return None
    
    val_lower = value.strip().lower()
    
    # First check for typos
    if val_lower in LIKERT_TYPOS:
        val_lower = LIKERT_TYPOS[val_lower]
    
    return scale_mapping.get(val_lower)


def fix_likert_typo(value: str) -> Tuple[str, bool]:
    """Fix common Likert scale typos.
    
    Args:
        value: Input value
        
    Returns:
        Tuple of (fixed_value, was_typo)
    """
    if not value:
        return value, False
    
    val_lower = value.strip().lower()
    
    if val_lower in LIKERT_TYPOS:
        fixed = LIKERT_TYPOS[val_lower]
        # Return in title case
        return fixed.title(), True
    
    return value, False


def detect_straight_lining(df: pd.DataFrame, 
                           survey_cols: List[str],
                           respondent_col: Optional[str] = None) -> List[int]:
    """Detect respondents who gave identical answers to all questions.
    
    Args:
        df: DataFrame
        survey_cols: List of survey question columns
        respondent_col: Optional column identifying respondent
        
    Returns:
        List of row indices with straight-lining
    """
    if len(survey_cols) < 3:
        return []
    
    straight_liners = []
    
    for idx in df.index:
        row_vals = []
        for col in survey_cols:
            if col in df.columns:
                val = df.at[idx, col]
                if not pd.isna(val):
                    row_vals.append(str(val).lower().strip())
        
        # If all values are the same and we have at least 3
        if len(row_vals) >= 3 and len(set(row_vals)) == 1:
            straight_liners.append(idx)
    
    return straight_liners


def check_likert_range(value: Any, scale_size: int) -> bool:
    """Check if value is within Likert scale range.
    
    Args:
        value: Value to check
        scale_size: Size of scale (5, 7, 10)
        
    Returns:
        True if in range
    """
    if pd.isna(value):
        return True
    
    try:
        num_val = float(value)
        return 1 <= num_val <= scale_size
    except (ValueError, TypeError):
        return True  # Non-numeric, let verbal check handle it


# ============================================================================
# HELPER FUNCTIONS — MULTI-VALUE
# ============================================================================

def detect_delimiter(series: pd.Series) -> Optional[str]:
    """Detect the most common delimiter in multi-value cells.
    
    Args:
        series: pandas Series
        
    Returns:
        Detected delimiter or None
    """
    delimiter_counts = Counter()
    
    for val in series.dropna():
        if not isinstance(val, str):
            continue
        
        for delim in MULTI_VALUE_DELIMITERS:
            if delim in val:
                delimiter_counts[delim] += val.count(delim)
    
    if not delimiter_counts:
        return None
    
    return delimiter_counts.most_common(1)[0][0]


def is_multi_value_column(series: pd.Series) -> Tuple[bool, Optional[str]]:
    """Detect if column contains multi-value cells.
    
    Args:
        series: pandas Series
        
    Returns:
        Tuple of (is_multi_value, detected_delimiter)
    """
    delimiter = detect_delimiter(series)
    
    if not delimiter:
        return False, None
    
    # Count how many cells have the delimiter
    non_null = series.dropna()
    if len(non_null) == 0:
        return False, None
    
    has_delimiter = sum(1 for val in non_null 
                       if isinstance(val, str) and delimiter in val)
    
    ratio = has_delimiter / len(non_null)
    
    # If more than 20% of cells have delimiter, likely multi-value
    return ratio >= 0.2, delimiter


def split_multi_value(value: str, delimiter: str) -> List[str]:
    """Split multi-value cell into individual values.
    
    Args:
        value: Multi-value string
        delimiter: Delimiter to split on
        
    Returns:
        List of individual values, cleaned
    """
    if not value or not isinstance(value, str):
        return []
    
    # Handle " and " specially
    if delimiter == " and ":
        parts = value.split(" and ")
    else:
        parts = value.split(delimiter)
    
    # Clean each part
    return [p.strip() for p in parts if p.strip()]


def standardize_multi_value_delimiter(value: str, 
                                       from_delimiters: List[str],
                                       to_delimiter: str = ", ") -> str:
    """Standardize delimiters in multi-value cell.
    
    Args:
        value: Input string
        from_delimiters: List of delimiters to replace
        to_delimiter: Target delimiter
        
    Returns:
        String with standardized delimiters
    """
    if not value or not isinstance(value, str):
        return value
    
    result = value
    for delim in from_delimiters:
        if delim != to_delimiter:
            result = result.replace(delim, to_delimiter)
    
    # Clean up any double delimiters
    while to_delimiter + to_delimiter in result:
        result = result.replace(to_delimiter + to_delimiter, to_delimiter)
    
    return result.strip().strip(to_delimiter.strip())


def get_unique_values_from_multi(series: pd.Series, 
                                  delimiter: str) -> Set[str]:
    """Get all unique values across all multi-value cells.
    
    Args:
        series: pandas Series
        delimiter: Delimiter used
        
    Returns:
        Set of unique individual values
    """
    unique_vals = set()
    
    for val in series.dropna():
        if isinstance(val, str):
            parts = split_multi_value(val, delimiter)
            unique_vals.update(parts)
    
    return unique_vals


def normalize_multi_value_variants(series: pd.Series,
                                    delimiter: str,
                                    canonical_map: Dict[str, str]) -> pd.Series:
    """Normalize variant values within multi-value cells.
    
    Args:
        series: pandas Series
        delimiter: Delimiter used
        canonical_map: Mapping of variants to canonical form
        
    Returns:
        Series with normalized values
    """
    result = series.copy()
    
    for idx, val in series.items():
        if pd.isna(val) or not isinstance(val, str):
            continue
        
        parts = split_multi_value(val, delimiter)
        normalized_parts = []
        
        for part in parts:
            canonical = canonical_map.get(part.lower(), part)
            normalized_parts.append(canonical)
        
        result.at[idx] = delimiter.join(normalized_parts)
    
    return result


def build_variant_map(unique_values: Set[str], 
                      threshold: float = 0.85) -> Dict[str, str]:
    """Build mapping of variant spellings to canonical form.
    
    Args:
        unique_values: Set of unique values
        threshold: Similarity threshold for matching
        
    Returns:
        Dictionary mapping variants to canonical form
    """
    if not unique_values:
        return {}
    
    sorted_vals = sorted(unique_values, key=lambda x: x.lower())
    canonical_map = {}
    processed = set()
    
    for val in sorted_vals:
        if val.lower() in processed:
            continue
        
        # This becomes canonical
        canonical = to_title_case(val)
        canonical_map[val.lower()] = canonical
        processed.add(val.lower())
        
        # Find variants
        for other in sorted_vals:
            if other.lower() in processed:
                continue
            
            if calculate_similarity(val, other) >= threshold:
                canonical_map[other.lower()] = canonical
                processed.add(other.lower())
    
    return canonical_map


def get_multi_value_frequency(series: pd.Series, 
                              delimiter: str) -> Dict[str, int]:
    """Count frequency of each individual value in multi-value column.
    
    Args:
        series: pandas Series
        delimiter: Delimiter used
        
    Returns:
        Dictionary of value -> count
    """
    value_counts = Counter()
    
    for val in series.dropna():
        if isinstance(val, str):
            parts = split_multi_value(val, delimiter)
            value_counts.update(parts)
    
    return dict(value_counts)


def explode_multi_value_column(df: pd.DataFrame, 
                                col: str,
                                delimiter: str) -> pd.DataFrame:
    """Explode multi-value column into multiple rows.
    
    Args:
        df: DataFrame
        col: Column to explode
        delimiter: Delimiter used
        
    Returns:
        New DataFrame with exploded rows
    """
    result_rows = []
    
    for idx, row in df.iterrows():
        val = row[col]
        if pd.isna(val) or not isinstance(val, str):
            result_rows.append(row)
            continue
        
        parts = split_multi_value(val, delimiter)
        if not parts:
            result_rows.append(row)
            continue
        
        for part in parts:
            new_row = row.copy()
            new_row[col] = part
            result_rows.append(new_row)
    
    return pd.DataFrame(result_rows)


# ============================================================================
# MAIN CLASS
# ============================================================================

class BooleanCategoryRules:
    """Boolean, Category, Status, Survey & Multi-Value cleaning rules."""
    
    APPLICABLE_HTYPES = {
        "HTYPE-018",  # Boolean / Flag
        "HTYPE-019",  # Category / Classification
        "HTYPE-020",  # Status
        "HTYPE-045",  # Survey / Likert
        "HTYPE-046",  # Multi-Value / Tag
    }
    
    def __init__(self, job_id: int, df: pd.DataFrame, db, 
                 htype_map: Dict[str, str]):
        """Initialize the rules engine.
        
        Args:
            job_id: Upload job ID for logging
            df: DataFrame to clean
            db: Database session
            htype_map: Mapping of column names to their HTYPEs
        """
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.htype_map = htype_map
        self.results: List[CleaningResult] = []
        self.flags: List[Dict[str, Any]] = []
        
        # Track detected patterns
        self.detected_scales: Dict[str, Tuple[str, int, Dict]] = {}
        self.detected_delimiters: Dict[str, str] = {}
        self.category_canonical: Dict[str, Dict[str, str]] = {}
        self.unique_value_registry: Dict[str, Set[str]] = {}
        self.category_frequencies: Dict[str, Dict[str, int]] = {}
    
    def _ensure_object_dtype(self, col: str):
        """Ensure column has object dtype for mixed type assignment (pandas 3.0 compatibility)."""
        if col in self.df.columns and self.df[col].dtype in ['string', 'object']:
            self.df[col] = self.df[col].astype(object)
    
    def add_flag(self, row_idx: int, col: str, formula_id: str,
                 message: str, value: Any, severity: str = "warning"):
        """Add a flag for manual review.
        
        Args:
            row_idx: Row index
            col: Column name
            formula_id: Formula that triggered the flag
            message: Description of the issue
            value: The problematic value
            severity: Flag severity (info, warning, error)
        """
        self.flags.append({
            "row": row_idx,
            "column": col,
            "formula": formula_id,
            "message": message,
            "value": value,
            "severity": severity,
        })
    
    def log_cleaning(self, result: CleaningResult):
        """Log cleaning action to database.
        
        Args:
            result: CleaningResult object
        """
        try:
            log = CleaningLog(
                job_id=self.job_id,
                action=f"{result.formula_id}: {result.column}",
                timestamp=datetime.utcnow(),
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            self.db.rollback()
    
    # ========================================================================
    # BOOL FORMULAS (HTYPE-018: Boolean / Flag / Yes-No)
    # ========================================================================
    
    def BOOL_01_value_standardization(self, col: str) -> CleaningResult:
        """BOOL-01: Standardize boolean values to True/False."""
        result = CleaningResult(column=col, formula_id="BOOL-01")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            normalized = normalize_boolean(val)
            if normalized is not None:
                # Only count as change if different
                if str(val).lower().strip() not in ("true", "false"):
                    self.df.at[idx, col] = normalized
                    result.changes_made += 1
            elif is_non_binary_value(val):
                # Non-binary value - flag for review
                self.add_flag(idx, col, "BOOL-01",
                             f"Non-binary value in boolean field: {val}", val)
                result.rows_flagged += 1
        
        if result.changes_made > 0 or result.rows_flagged > 0:
            self.log_cleaning(result)
        
        return result
    
    def BOOL_02_binary_enforcement(self, col: str) -> CleaningResult:
        """BOOL-02: Flag non-binary values (suggest reroute to Status)."""
        result = CleaningResult(column=col, formula_id="BOOL-02")
        
        non_binary_found = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if is_non_binary_value(val):
                non_binary_found.append(val)
                self.add_flag(idx, col, "BOOL-02",
                             f"Non-binary value suggests Status field: {val}", val)
                result.rows_flagged += 1
        
        if non_binary_found:
            result.details["non_binary_values"] = list(set(str(v) for v in non_binary_found))
            result.details["suggestion"] = "Consider reclassifying as HTYPE-020 (Status)"
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def BOOL_03_null_distinction(self, col: str) -> CleaningResult:
        """BOOL-03: Distinguish null (unknown) from intentional False."""
        result = CleaningResult(column=col, formula_id="BOOL-03")
        
        null_count = self.df[col].isna().sum()
        false_count = sum(1 for val in self.df[col] 
                         if normalize_boolean(val) is False)
        
        if null_count > 0:
            result.details["null_count"] = int(null_count)
            result.details["false_count"] = int(false_count)
            result.details["recommendation"] = (
                "Null values represent 'unknown' state, not 'False'. "
                "Consider: 1) Keep as null, 2) Mark as 'Unknown', or "
                "3) Impute based on context."
            )
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def BOOL_04_integer_encoding(self, col: str) -> CleaningResult:
        """BOOL-04: Convert to 0/1 integer encoding for analysis."""
        result = CleaningResult(column=col, formula_id="BOOL-04")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            normalized = normalize_boolean(val)
            
            if normalized is True:
                self.df.at[idx, col] = 1
                result.changes_made += 1
            elif normalized is False:
                self.df.at[idx, col] = 0
                result.changes_made += 1
        
        if result.changes_made > 0:
            result.details["encoding"] = "True→1, False→0"
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # CAT FORMULAS (HTYPE-019: Category / Classification Label)
    # ========================================================================
    
    def CAT_01_title_case_normalization(self, col: str) -> CleaningResult:
        """CAT-01: Apply title case to categories."""
        result = CleaningResult(column=col, formula_id="CAT-01")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            title_cased = to_title_case(val.strip())
            if title_cased != val:
                self.df.at[idx, col] = title_cased
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def CAT_02_variant_consolidation(self, col: str) -> CleaningResult:
        """CAT-02: Consolidate case/punctuation variants."""
        result = CleaningResult(column=col, formula_id="CAT-02")
        
        # Build variant map
        unique_vals = set()
        for val in self.df[col].dropna():
            if isinstance(val, str):
                unique_vals.add(val)
        
        # Group by lowercase
        groups = defaultdict(list)
        for val in unique_vals:
            groups[val.lower().strip()].append(val)
        
        # Find groups with variants
        variant_groups = {k: v for k, v in groups.items() if len(v) > 1}
        
        if variant_groups:
            # Build canonical map - use most frequent variant
            canonical_map = {}
            for key, variants in variant_groups.items():
                # Count occurrences of each variant
                counts = {}
                for v in variants:
                    counts[v] = sum(1 for x in self.df[col] 
                                   if not pd.isna(x) and x == v)
                
                # Use most frequent as canonical
                canonical = max(counts, key=counts.get)
                canonical_map[key] = canonical
            
            self.category_canonical[col] = canonical_map
            
            # Apply consolidation
            for idx, val in self.df[col].items():
                if pd.isna(val) or not isinstance(val, str):
                    continue
                
                key = val.lower().strip()
                if key in canonical_map and val != canonical_map[key]:
                    self.df.at[idx, col] = canonical_map[key]
                    result.changes_made += 1
            
            result.details["variant_groups"] = {
                k: v for k, v in variant_groups.items()
            }
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def CAT_03_typo_correction(self, col: str) -> CleaningResult:
        """CAT-03: Fix typos using edit distance matching."""
        result = CleaningResult(column=col, formula_id="CAT-03")
        
        # Get category frequencies
        freq = get_category_frequencies(self.df[col])
        
        if not freq:
            return result
        
        # High-frequency values are likely correct
        total = sum(freq.values())
        canonical_vals = {v for v, c in freq.items() 
                        if c / total >= 0.02 or c >= 5}  # At least 2% or 5 occurrences
        
        if not canonical_vals:
            canonical_vals = set(freq.keys())
        
        corrections = {}
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            if val in canonical_vals:
                continue
            
            # Find best match
            match = find_similar_categories(val, canonical_vals, threshold=0.85)
            if match and match != val:
                corrections[val] = match
                self.df.at[idx, col] = match
                result.changes_made += 1
        
        if corrections:
            result.details["corrections"] = corrections
            self.log_cleaning(result)
        
        return result
    
    def CAT_04_rare_category_flagging(self, col: str) -> CleaningResult:
        """CAT-04: Flag categories appearing in <1% of rows."""
        result = CleaningResult(column=col, formula_id="CAT-04")
        
        rare_cats = detect_rare_categories(self.df[col], threshold=0.01)
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if val in rare_cats:
                self.add_flag(idx, col, "CAT-04",
                             f"Rare category (<1%): {val}", val, severity="info")
                result.rows_flagged += 1
        
        if rare_cats:
            result.details["rare_categories"] = rare_cats
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def CAT_05_frequency_report(self, col: str) -> CleaningResult:
        """CAT-05: Generate category frequency report."""
        result = CleaningResult(column=col, formula_id="CAT-05")
        
        freq = get_category_frequencies(self.df[col])
        self.category_frequencies[col] = freq
        
        result.details["distinct_count"] = len(freq)
        result.details["frequencies"] = freq
        result.details["total_non_null"] = sum(freq.values())
        
        self.log_cleaning(result)
        return result
    
    def CAT_06_null_handling(self, col: str) -> CleaningResult:
        """CAT-06: Handle null category values."""
        result = CleaningResult(column=col, formula_id="CAT-06")
        
        null_count = self.df[col].isna().sum()
        
        if null_count > 0:
            result.details["null_count"] = int(null_count)
            result.details["options"] = [
                "Keep as null/missing",
                "Mark as 'Uncategorized'",
                "Mark as 'Unknown'",
                "Impute from most frequent category"
            ]
            result.rows_flagged = int(null_count)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def CAT_07_whitespace_normalization(self, col: str) -> CleaningResult:
        """CAT-07: Clean whitespace in category values."""
        result = CleaningResult(column=col, formula_id="CAT-07")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            cleaned = clean_category_whitespace(val)
            if cleaned != val:
                self.df.at[idx, col] = cleaned
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def CAT_08_encoding_artifact_fix(self, col: str) -> CleaningResult:
        """CAT-08: Fix encoding artifacts in text."""
        result = CleaningResult(column=col, formula_id="CAT-08")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            fixed = fix_encoding_artifacts(val)
            if fixed != val:
                self.df.at[idx, col] = fixed
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # STAT FORMULAS (HTYPE-020: Status Field)
    # ========================================================================
    
    def STAT_01_canonical_mapping(self, col: str) -> CleaningResult:
        """STAT-01: Map status variants to canonical form."""
        result = CleaningResult(column=col, formula_id="STAT-01")
        
        mappings_applied = {}
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            canonical = normalize_status(val)
            if canonical and canonical != val:
                mappings_applied[val] = canonical
                self.df.at[idx, col] = canonical
                result.changes_made += 1
        
        if mappings_applied:
            result.details["mappings_applied"] = mappings_applied
            self.log_cleaning(result)
        
        return result
    
    def STAT_02_workflow_validation(self, col: str) -> CleaningResult:
        """STAT-02: Validate logical workflow sequence."""
        result = CleaningResult(column=col, formula_id="STAT-02")
        
        workflow = detect_workflow_type(self.df[col])
        
        if workflow:
            result.details["detected_workflow"] = workflow
            result.details["expected_sequence"] = WORKFLOW_SEQUENCES.get(workflow, [])
            
            # Check for violations
            violations = validate_workflow_sequence(self.df, col)
            
            for idx in violations:
                self.add_flag(idx, col, "STAT-02",
                             "Status may not fit expected workflow", 
                             self.df.at[idx, col])
                result.rows_flagged += 1
            
            if violations:
                result.was_auto_applied = False
        
        if result.rows_flagged > 0 or workflow:
            self.log_cleaning(result)
        
        return result
    
    def STAT_03_case_normalization(self, col: str) -> CleaningResult:
        """STAT-03: Normalize status to title case."""
        result = CleaningResult(column=col, formula_id="STAT-03")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            # Title case but preserve known patterns
            title_cased = val.strip().title()
            if title_cased != val:
                self.df.at[idx, col] = title_cased
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def STAT_04_null_handling(self, col: str) -> CleaningResult:
        """STAT-04: Handle null status values."""
        result = CleaningResult(column=col, formula_id="STAT-04")
        
        null_indices = []
        for idx, val in self.df[col].items():
            if pd.isna(val):
                null_indices.append(idx)
                self.add_flag(idx, col, "STAT-04",
                             "Missing status value", None, severity="info")
        
        if null_indices:
            result.rows_flagged = len(null_indices)
            result.details["null_count"] = len(null_indices)
            result.details["options"] = [
                "Keep as null",
                "Mark as 'Unknown'",
                "Mark as 'New' (initial state)"
            ]
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def STAT_05_retired_status_detection(self, col: str) -> CleaningResult:
        """STAT-05: Detect potentially retired status values."""
        result = CleaningResult(column=col, formula_id="STAT-05")
        
        retired = detect_retired_status(self.df[col])
        
        if retired:
            result.details["potentially_retired"] = retired
            result.details["recommendation"] = (
                "These status values appear very rarely (<1%). "
                "They may be deprecated labels."
            )
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # SURV FORMULAS (HTYPE-045: Survey / Likert Response)
    # ========================================================================
    
    def SURV_01_scale_detection(self, col: str) -> CleaningResult:
        """SURV-01: Detect Likert scale type and size."""
        result = CleaningResult(column=col, formula_id="SURV-01")
        
        scale_type, scale_size, mapping = detect_likert_scale(self.df[col])
        self.detected_scales[col] = (scale_type, scale_size, mapping)
        
        result.details["scale_type"] = scale_type
        result.details["scale_size"] = scale_size
        
        if mapping:
            result.details["verbal_scale"] = list(mapping.keys())
        
        self.log_cleaning(result)
        return result
    
    def SURV_02_verbal_to_numeric(self, col: str) -> CleaningResult:
        """SURV-02: Convert verbal responses to numeric."""
        result = CleaningResult(column=col, formula_id="SURV-02")
        self._ensure_object_dtype(col)
        
        if col not in self.detected_scales:
            scale_type, scale_size, mapping = detect_likert_scale(self.df[col])
            self.detected_scales[col] = (scale_type, scale_size, mapping)
        else:
            scale_type, scale_size, mapping = self.detected_scales[col]
        
        if not mapping:
            return result
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            numeric = verbal_to_numeric_likert(val, mapping)
            if numeric is not None:
                self.df.at[idx, col] = numeric
                result.changes_made += 1
        
        if result.changes_made > 0:
            result.details["scale_used"] = scale_type
            self.log_cleaning(result)
        
        return result
    
    def SURV_03_variant_standardization(self, col: str) -> CleaningResult:
        """SURV-03: Fix typos in Likert scale values."""
        result = CleaningResult(column=col, formula_id="SURV-03")
        
        corrections = {}
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            fixed, was_typo = fix_likert_typo(val)
            if was_typo:
                corrections[val] = fixed
                self.df.at[idx, col] = fixed
                result.changes_made += 1
        
        if corrections:
            result.details["corrections"] = corrections
            self.log_cleaning(result)
        
        return result
    
    def SURV_04_frequency_scale_mapping(self, col: str) -> CleaningResult:
        """SURV-04: Map frequency responses (Never/Rarely/.../Always) to numeric."""
        result = CleaningResult(column=col, formula_id="SURV-04")
        self._ensure_object_dtype(col)
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            val_lower = val.strip().lower()
            
            # Check for typos first
            if val_lower in LIKERT_TYPOS:
                val_lower = LIKERT_TYPOS[val_lower]
            
            if val_lower in FREQUENCY_SCALE:
                self.df.at[idx, col] = FREQUENCY_SCALE[val_lower]
                result.changes_made += 1
        
        if result.changes_made > 0:
            result.details["scale"] = "frequency (1-5)"
            self.log_cleaning(result)
        
        return result
    
    def SURV_05_out_of_range_flag(self, col: str) -> CleaningResult:
        """SURV-05: Flag responses outside defined scale."""
        result = CleaningResult(column=col, formula_id="SURV-05")
        
        if col not in self.detected_scales:
            scale_type, scale_size, mapping = detect_likert_scale(self.df[col])
            self.detected_scales[col] = (scale_type, scale_size, mapping)
        else:
            scale_type, scale_size, mapping = self.detected_scales[col]
        
        if scale_size == 0:
            return result
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                num_val = float(val)
                if num_val < 1 or num_val > scale_size:
                    self.add_flag(idx, col, "SURV-05",
                                 f"Value {num_val} outside scale 1-{scale_size}", val)
                    result.rows_flagged += 1
            except (ValueError, TypeError):
                # Non-numeric, check if it's in valid verbal responses
                if isinstance(val, str) and mapping:
                    if val.lower().strip() not in mapping:
                        self.add_flag(idx, col, "SURV-05",
                                     f"Unrecognized response: {val}", val)
                        result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def SURV_06_straight_lining_detection(self, col: str) -> CleaningResult:
        """SURV-06: Detect straight-lining (identical answers across questions)."""
        result = CleaningResult(column=col, formula_id="SURV-06")
        
        # Find other survey columns
        survey_cols = [c for c, h in self.htype_map.items() 
                      if h == "HTYPE-045" and c in self.df.columns]
        
        if len(survey_cols) < 3:
            return result
        
        straight_liners = detect_straight_lining(self.df, survey_cols)
        
        for idx in straight_liners:
            self.add_flag(idx, col, "SURV-06",
                         "Possible straight-lining: identical answers across all survey questions",
                         self.df.at[idx, col], severity="info")
            result.rows_flagged += 1
        
        if straight_liners:
            result.details["straight_line_rows"] = len(straight_liners)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def SURV_07_missing_response_handling(self, col: str) -> CleaningResult:
        """SURV-07: Handle missing survey responses."""
        result = CleaningResult(column=col, formula_id="SURV-07")
        
        null_count = self.df[col].isna().sum()
        
        if null_count > 0:
            result.details["missing_count"] = int(null_count)
            result.details["recommendation"] = (
                "Survey opinions cannot be predicted. "
                "Mark as 'No Response' or exclude from analysis."
            )
            result.rows_flagged = int(null_count)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # MULTI FORMULAS (HTYPE-046: Multi-Value / Tag Field)
    # ========================================================================
    
    def MULTI_01_pattern_detection(self, col: str) -> CleaningResult:
        """MULTI-01: Detect multi-value fields by delimiter presence."""
        result = CleaningResult(column=col, formula_id="MULTI-01")
        
        is_multi, delimiter = is_multi_value_column(self.df[col])
        
        if is_multi and delimiter:
            self.detected_delimiters[col] = delimiter
            result.details["is_multi_value"] = True
            result.details["detected_delimiter"] = delimiter
            
            # Count cells with delimiter
            cells_with_delimiter = sum(
                1 for val in self.df[col].dropna() 
                if isinstance(val, str) and delimiter in val
            )
            result.details["cells_with_delimiter"] = cells_with_delimiter
        else:
            result.details["is_multi_value"] = False
        
        self.log_cleaning(result)
        return result
    
    def MULTI_02_delimiter_standardization(self, col: str) -> CleaningResult:
        """MULTI-02: Standardize to single delimiter type."""
        result = CleaningResult(column=col, formula_id="MULTI-02")
        
        target_delimiter = ", "
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            # Find which delimiters are present
            found_delimiters = [d for d in MULTI_VALUE_DELIMITERS if d in val]
            
            if len(found_delimiters) > 1 or (
                found_delimiters and found_delimiters[0] != target_delimiter.strip()
            ):
                standardized = standardize_multi_value_delimiter(
                    val, found_delimiters, target_delimiter
                )
                if standardized != val:
                    self.df.at[idx, col] = standardized
                    result.changes_made += 1
        
        if result.changes_made > 0:
            result.details["standardized_to"] = target_delimiter
            self.detected_delimiters[col] = target_delimiter.strip()
            self.log_cleaning(result)
        
        return result
    
    def MULTI_03_individual_value_cleaning(self, col: str) -> CleaningResult:
        """MULTI-03: Clean each value within multi-value cells."""
        result = CleaningResult(column=col, formula_id="MULTI-03")
        
        delimiter = self.detected_delimiters.get(col) or detect_delimiter(self.df[col])
        
        if not delimiter:
            return result
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            parts = split_multi_value(val, delimiter)
            cleaned_parts = []
            changed = False
            
            for part in parts:
                # Trim, title case
                cleaned = to_title_case(clean_category_whitespace(part))
                if cleaned != part:
                    changed = True
                cleaned_parts.append(cleaned)
            
            if changed:
                self.df.at[idx, col] = ", ".join(cleaned_parts)
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def MULTI_04_variant_normalization(self, col: str) -> CleaningResult:
        """MULTI-04: Normalize variant spellings across multi-value cells."""
        result = CleaningResult(column=col, formula_id="MULTI-04")
        
        delimiter = self.detected_delimiters.get(col) or detect_delimiter(self.df[col])
        
        if not delimiter:
            return result
        
        # Get all unique values
        unique_vals = get_unique_values_from_multi(self.df[col], delimiter)
        
        # Build variant map
        canonical_map = build_variant_map(unique_vals, threshold=0.85)
        
        # Apply normalization
        variants_found = {}
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            parts = split_multi_value(val, delimiter)
            normalized_parts = []
            changed = False
            
            for part in parts:
                canonical = canonical_map.get(part.lower(), part)
                if canonical != part:
                    variants_found[part] = canonical
                    changed = True
                normalized_parts.append(canonical)
            
            if changed:
                self.df.at[idx, col] = ", ".join(normalized_parts)
                result.changes_made += 1
        
        if variants_found:
            result.details["variants_normalized"] = variants_found
            self.log_cleaning(result)
        
        return result
    
    def MULTI_05_explosion_option(self, col: str) -> CleaningResult:
        """MULTI-05: Offer to explode column into one row per value."""
        result = CleaningResult(column=col, formula_id="MULTI-05")
        
        delimiter = self.detected_delimiters.get(col) or detect_delimiter(self.df[col])
        
        if not delimiter:
            return result
        
        # Count how many rows would be created
        total_values = 0
        for val in self.df[col].dropna():
            if isinstance(val, str):
                parts = split_multi_value(val, delimiter)
                total_values += len(parts)
        
        result.details["current_rows"] = len(self.df)
        result.details["exploded_rows"] = total_values
        result.details["option"] = (
            "Column can be 'exploded' into one row per value. "
            "This is useful for analysis of individual tags/values."
        )
        result.was_auto_applied = False
        
        self.log_cleaning(result)
        return result
    
    def MULTI_06_value_frequency_count(self, col: str) -> CleaningResult:
        """MULTI-06: Count frequency of each individual value."""
        result = CleaningResult(column=col, formula_id="MULTI-06")
        
        delimiter = self.detected_delimiters.get(col) or detect_delimiter(self.df[col])
        
        if not delimiter:
            # Not multi-value, use regular frequency
            freq = get_category_frequencies(self.df[col])
        else:
            freq = get_multi_value_frequency(self.df[col], delimiter)
        
        result.details["value_frequencies"] = freq
        result.details["unique_count"] = len(freq)
        result.details["total_occurrences"] = sum(freq.values())
        
        self.log_cleaning(result)
        return result
    
    def MULTI_07_unique_value_registry(self, col: str) -> CleaningResult:
        """MULTI-07: Maintain master list of all unique values."""
        result = CleaningResult(column=col, formula_id="MULTI-07")
        
        delimiter = self.detected_delimiters.get(col) or detect_delimiter(self.df[col])
        
        if delimiter:
            unique_vals = get_unique_values_from_multi(self.df[col], delimiter)
        else:
            unique_vals = set(self.df[col].dropna().unique())
        
        self.unique_value_registry[col] = unique_vals
        
        result.details["unique_values"] = sorted(list(unique_vals))
        result.details["count"] = len(unique_vals)
        
        self.log_cleaning(result)
        return result
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_for_column(self, col: str, htype: str) -> List[CleaningResult]:
        """Run all applicable formulas for a column based on its HTYPE."""
        results = []
        
        if htype == "HTYPE-018":  # Boolean / Flag
            results.append(self.BOOL_01_value_standardization(col))
            results.append(self.BOOL_02_binary_enforcement(col))
            results.append(self.BOOL_03_null_distinction(col))
            # BOOL_04 is optional - user must request integer encoding
        
        elif htype == "HTYPE-019":  # Category / Classification
            results.append(self.CAT_07_whitespace_normalization(col))
            results.append(self.CAT_08_encoding_artifact_fix(col))
            results.append(self.CAT_01_title_case_normalization(col))
            results.append(self.CAT_02_variant_consolidation(col))
            results.append(self.CAT_03_typo_correction(col))
            results.append(self.CAT_04_rare_category_flagging(col))
            results.append(self.CAT_05_frequency_report(col))
            results.append(self.CAT_06_null_handling(col))
        
        elif htype == "HTYPE-020":  # Status Field
            results.append(self.STAT_03_case_normalization(col))
            results.append(self.STAT_01_canonical_mapping(col))
            results.append(self.STAT_02_workflow_validation(col))
            results.append(self.STAT_04_null_handling(col))
            results.append(self.STAT_05_retired_status_detection(col))
        
        elif htype == "HTYPE-045":  # Survey / Likert
            results.append(self.SURV_01_scale_detection(col))
            results.append(self.SURV_03_variant_standardization(col))
            results.append(self.SURV_02_verbal_to_numeric(col))
            results.append(self.SURV_04_frequency_scale_mapping(col))
            results.append(self.SURV_05_out_of_range_flag(col))
            results.append(self.SURV_06_straight_lining_detection(col))
            results.append(self.SURV_07_missing_response_handling(col))
        
        elif htype == "HTYPE-046":  # Multi-Value / Tag
            results.append(self.MULTI_01_pattern_detection(col))
            results.append(self.MULTI_02_delimiter_standardization(col))
            results.append(self.MULTI_03_individual_value_cleaning(col))
            results.append(self.MULTI_04_variant_normalization(col))
            results.append(self.MULTI_06_value_frequency_count(col))
            results.append(self.MULTI_07_unique_value_registry(col))
            results.append(self.MULTI_05_explosion_option(col))
        
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
            "detected_scales": {
                k: v[0] for k, v in self.detected_scales.items()
            },
            "detected_delimiters": self.detected_delimiters,
            "category_frequencies": self.category_frequencies,
            "unique_value_registry": {
                k: len(v) for k, v in self.unique_value_registry.items()
            },
        }
