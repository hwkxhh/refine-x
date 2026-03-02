"""
Organizational & Product Cleaning Rules — Session 9

Implements formulas from the Formula Rulebook for:
- HTYPE-024: Product Name / Item Name (PROD-01 to PROD-05)
- HTYPE-025: Product Code / SKU / Barcode (SKU-01 to SKU-05)
- HTYPE-026: Organization / Company Name (ORG-01 to ORG-05)
- HTYPE-027: Job Title / Designation / Role (JOB-01 to JOB-05)
- HTYPE-028: Department / Division / Unit (DEPT-01 to DEPT-05)
- HTYPE-034: Serial Number / Reference Number (REFNO-01 to REFNO-05)
- HTYPE-047: Version / Revision Number (VER-01 to VER-04)

Logic First. AI Never.
"""

import re
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
# PRODUCT CONSTANTS
# ============================================================================

# Allowed special characters in product names
PRODUCT_ALLOWED_CHARS = set("()-®™&+/.'\":;, ")

# Common product name abbreviations
PRODUCT_ABBREVIATIONS = {
    "tab": "Tablet",
    "tabs": "Tablets",
    "cap": "Capsule",
    "caps": "Capsules",
    "inj": "Injection",
    "sol": "Solution",
    "susp": "Suspension",
    "syr": "Syrup",
    "pkg": "Package",
    "pkt": "Packet",
    "btl": "Bottle",
}


# ============================================================================
# SKU/BARCODE CONSTANTS
# ============================================================================

# Valid characters for SKU codes
SKU_VALID_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-")

# EAN-13 and UPC-A patterns
EAN13_PATTERN = re.compile(r'^\d{13}$')
UPCA_PATTERN = re.compile(r'^\d{12}$')
EAN8_PATTERN = re.compile(r'^\d{8}$')


# ============================================================================
# ORGANIZATION CONSTANTS
# ============================================================================

# Legal suffix standardization
LEGAL_SUFFIX_MAP = {
    # Limited variants
    "ltd": "Ltd.",
    "ltd.": "Ltd.",
    "limited": "Ltd.",
    "ltda": "Ltda.",
    
    # Incorporated variants
    "inc": "Inc.",
    "inc.": "Inc.",
    "incorporated": "Inc.",
    
    # Corporation variants
    "corp": "Corp.",
    "corp.": "Corp.",
    "corporation": "Corp.",
    
    # Private Limited variants
    "pvt": "Pvt.",
    "pvt.": "Pvt.",
    "private": "Private",
    "pvt ltd": "Pvt. Ltd.",
    "pvt. ltd.": "Pvt. Ltd.",
    "private limited": "Pvt. Ltd.",
    
    # Public Limited Company
    "plc": "PLC",
    "p.l.c.": "PLC",
    
    # Limited Liability Company
    "llc": "LLC",
    "l.l.c.": "LLC",
    
    # Other
    "co": "Co.",
    "co.": "Co.",
    "company": "Co.",
    "llp": "LLP",
    "l.l.p.": "LLP",
    "gmbh": "GmbH",
    "ag": "AG",
    "sa": "S.A.",
    "s.a.": "S.A.",
    "nv": "N.V.",
    "n.v.": "N.V.",
    "bv": "B.V.",
    "b.v.": "B.V.",
}

# Known organization abbreviations
ORG_ABBREVIATIONS = {
    "nhs": "National Health Service",
    "who": "World Health Organization",
    "undp": "United Nations Development Programme",
    "unicef": "United Nations Children's Fund",
    "unesco": "United Nations Educational, Scientific and Cultural Organization",
    "nato": "North Atlantic Treaty Organization",
    "nasa": "National Aeronautics and Space Administration",
    "fbi": "Federal Bureau of Investigation",
    "cia": "Central Intelligence Agency",
    "bbc": "British Broadcasting Corporation",
    "cnn": "Cable News Network",
    "ibm": "International Business Machines",
    "hp": "Hewlett-Packard",
    "ge": "General Electric",
    "gm": "General Motors",
}

# Words to preserve as uppercase in org names
ORG_PRESERVE_UPPER = {
    "NGO", "IT", "HR", "AI", "ML", "US", "UK", "EU", "UN", "UAE",
    "CEO", "CFO", "CTO", "COO", "CMO", "CIO", "VP", "SVP", "EVP",
    "LLC", "LLP", "PLC", "INC", "LTD", "SA", "NV", "BV", "AG",
}


# ============================================================================
# JOB TITLE CONSTANTS
# ============================================================================

# Job title abbreviation expansions
JOB_ABBREVIATIONS = {
    "mgr": "Manager",
    "mngr": "Manager",
    "mgmt": "Management",
    "asst": "Assistant",
    "assoc": "Associate",
    "dir": "Director",
    "exec": "Executive",
    "admin": "Administrator",
    "coord": "Coordinator",
    "supv": "Supervisor",
    "sr": "Senior",
    "jr": "Junior",
    "vp": "Vice President",
    "svp": "Senior Vice President",
    "evp": "Executive Vice President",
    "ceo": "Chief Executive Officer",
    "cfo": "Chief Financial Officer",
    "cto": "Chief Technology Officer",
    "coo": "Chief Operating Officer",
    "cmo": "Chief Marketing Officer",
    "cio": "Chief Information Officer",
    "hr": "Human Resources",
    "it": "Information Technology",
    "dev": "Developer",
    "eng": "Engineer",
    "engr": "Engineer",
    "tech": "Technician",
    "acct": "Accountant",
    "rep": "Representative",
    "spec": "Specialist",
    "anal": "Analyst",
    "consult": "Consultant",
}

# Seniority keywords
SENIORITY_KEYWORDS = {
    "chief", "head of", "director", "vice president", "vp",
    "senior", "sr", "lead", "principal", "staff",
    "junior", "jr", "associate", "assistant", "trainee", "intern",
    "deputy", "executive",
}

# Seniority levels (for extraction)
SENIORITY_LEVELS = {
    "chief": 10,
    "head of": 9,
    "director": 8,
    "vice president": 7,
    "vp": 7,
    "senior": 6,
    "sr": 6,
    "lead": 5,
    "principal": 5,
    "staff": 4,
    "associate": 2,
    "junior": 1,
    "jr": 1,
    "assistant": 1,
    "trainee": 0,
    "intern": 0,
}


# ============================================================================
# DEPARTMENT CONSTANTS
# ============================================================================

# Department abbreviation expansions
DEPT_ABBREVIATIONS = {
    "hr": "Human Resources",
    "it": "Information Technology",
    "r&d": "Research and Development",
    "rnd": "Research and Development",
    "qa": "Quality Assurance",
    "qc": "Quality Control",
    "ops": "Operations",
    "mktg": "Marketing",
    "fin": "Finance",
    "acct": "Accounting",
    "eng": "Engineering",
    "dev": "Development",
    "sales": "Sales",
    "cs": "Customer Service",
    "pr": "Public Relations",
    "admin": "Administration",
    "legal": "Legal",
    "hr dept": "Human Resources Department",
    "it dept": "Information Technology Department",
}

# Hierarchy separators
HIERARCHY_SEPARATORS = [" > ", " >> ", " / ", " - ", " | "]


# ============================================================================
# VERSION CONSTANTS
# ============================================================================

# Version format patterns
VERSION_PATTERNS = [
    (re.compile(r'^v?(\d+)\.(\d+)\.(\d+)$', re.I), 'semantic'),  # 1.2.3 or v1.2.3
    (re.compile(r'^v?(\d+)\.(\d+)$', re.I), 'major_minor'),      # 1.2 or v1.2
    (re.compile(r'^v?(\d+)$', re.I), 'major_only'),              # 1 or v1
    (re.compile(r'^version\s*(\d+)\.?(\d*)\.?(\d*)$', re.I), 'version_prefix'),
    (re.compile(r'^ver\.?\s*(\d+)\.?(\d*)\.?(\d*)$', re.I), 'ver_prefix'),
    (re.compile(r'^release\s*(\d+)\.?(\d*)\.?(\d*)$', re.I), 'release_prefix'),
    (re.compile(r'^r(\d+)$', re.I), 'r_prefix'),  # r1, r2
]


# ============================================================================
# HELPER FUNCTIONS — PRODUCT
# ============================================================================

def to_product_title_case(value: str) -> str:
    """Convert product name to title case, handling special cases.
    
    Args:
        value: Input string
        
    Returns:
        Title-cased product name
    """
    if not value:
        return value
    
    # Split and process each word
    words = value.split()
    result = []
    
    for word in words:
        # Preserve dosage patterns (e.g., "500mg", "10ml")
        if re.match(r'^\d+\s*(mg|ml|g|kg|l|mcg|iu)$', word, re.I):
            result.append(word.lower())
        # Preserve all-caps abbreviations
        elif word.upper() in {'XL', 'XXL', 'SR', 'XR', 'ER', 'CR', 'DR', 'EC'}:
            result.append(word.upper())
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def clean_product_special_chars(value: str) -> str:
    """Remove non-standard characters from product names.
    
    Args:
        value: Input string
        
    Returns:
        Cleaned string
    """
    if not value:
        return value
    
    # Keep only allowed characters and alphanumeric
    result = []
    for char in value:
        if char.isalnum() or char in PRODUCT_ALLOWED_CHARS:
            result.append(char)
    
    return ''.join(result).strip()


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


def find_product_variants(series: pd.Series, threshold: float = 0.8) -> Dict[str, List[str]]:
    """Find variant product names that likely refer to the same product.
    
    Args:
        series: pandas Series of product names
        threshold: Similarity threshold
        
    Returns:
        Dictionary mapping canonical names to variants
    """
    unique_vals = series.dropna().unique()
    if len(unique_vals) < 2:
        return {}
    
    # Group similar values
    groups = defaultdict(list)
    processed = set()
    
    for val in unique_vals:
        if val in processed:
            continue
        
        # Find all similar values
        similar = [val]
        for other in unique_vals:
            if other != val and other not in processed:
                if calculate_similarity(val, other) >= threshold:
                    similar.append(other)
                    processed.add(other)
        
        if len(similar) > 1:
            # Use the longest one as canonical
            canonical = max(similar, key=len)
            groups[canonical] = similar
        
        processed.add(val)
    
    return dict(groups)


# ============================================================================
# HELPER FUNCTIONS — SKU/BARCODE
# ============================================================================

def validate_ean13(code: str) -> bool:
    """Validate EAN-13 barcode check digit.
    
    Args:
        code: 13-digit barcode string
        
    Returns:
        True if valid
    """
    if not EAN13_PATTERN.match(code):
        return False
    
    # Calculate check digit
    digits = [int(d) for d in code]
    total = sum(digits[i] * (1 if i % 2 == 0 else 3) for i in range(12))
    check = (10 - (total % 10)) % 10
    
    return digits[12] == check


def validate_upca(code: str) -> bool:
    """Validate UPC-A barcode check digit.
    
    Args:
        code: 12-digit barcode string
        
    Returns:
        True if valid
    """
    if not UPCA_PATTERN.match(code):
        return False
    
    # Calculate check digit
    digits = [int(d) for d in code]
    total = sum(digits[i] * (3 if i % 2 == 0 else 1) for i in range(11))
    check = (10 - (total % 10)) % 10
    
    return digits[11] == check


def validate_ean8(code: str) -> bool:
    """Validate EAN-8 barcode check digit.
    
    Args:
        code: 8-digit barcode string
        
    Returns:
        True if valid
    """
    if not EAN8_PATTERN.match(code):
        return False
    
    # Calculate check digit
    digits = [int(d) for d in code]
    total = sum(digits[i] * (3 if i % 2 == 0 else 1) for i in range(7))
    check = (10 - (total % 10)) % 10
    
    return digits[7] == check


def clean_sku(value: str) -> str:
    """Clean SKU code - uppercase and remove invalid characters.
    
    Args:
        value: Input SKU
        
    Returns:
        Cleaned SKU
    """
    if not value:
        return value
    
    # Uppercase and filter
    cleaned = ''.join(c for c in value.upper() if c in SKU_VALID_CHARS)
    return cleaned


def detect_sku_pattern(series: pd.Series) -> Optional[Dict[str, Any]]:
    """Detect common pattern in SKU codes.
    
    Args:
        series: pandas Series of SKU codes
        
    Returns:
        Pattern info dict or None
    """
    non_null = series.dropna()
    if len(non_null) < 3:
        return None
    
    # Check for common prefix
    values = [str(v).upper() for v in non_null]
    
    # Find common prefix
    if not values:
        return None
    
    prefix = values[0]
    for val in values[1:]:
        while not val.startswith(prefix) and prefix:
            prefix = prefix[:-1]
    
    # Check for consistent length
    lengths = [len(v) for v in values]
    consistent_length = len(set(lengths)) == 1
    
    return {
        "common_prefix": prefix if len(prefix) >= 2 else None,
        "consistent_length": consistent_length,
        "typical_length": max(set(lengths), key=lengths.count) if lengths else None,
    }


# ============================================================================
# HELPER FUNCTIONS — ORGANIZATION
# ============================================================================

def to_org_title_case(value: str) -> str:
    """Convert organization name to title case, preserving abbreviations.
    
    Args:
        value: Input string
        
    Returns:
        Title-cased organization name
    """
    if not value:
        return value
    
    words = value.split()
    result = []
    
    for word in words:
        upper_word = word.upper()
        # Preserve known abbreviations
        if upper_word in ORG_PRESERVE_UPPER:
            result.append(upper_word)
        # Check for legal suffix
        elif word.lower().rstrip('.') in LEGAL_SUFFIX_MAP:
            result.append(LEGAL_SUFFIX_MAP.get(word.lower().rstrip('.'), word))
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def standardize_legal_suffix(value: str) -> str:
    """Standardize legal suffixes in organization names.
    
    Args:
        value: Organization name
        
    Returns:
        Name with standardized suffix
    """
    if not value:
        return value
    
    words = value.split()
    if not words:
        return value
    
    # Check last 1-3 words for legal suffix
    for num_words in range(3, 0, -1):
        if len(words) >= num_words:
            suffix_candidate = ' '.join(words[-num_words:]).lower()
            if suffix_candidate in LEGAL_SUFFIX_MAP:
                words = words[:-num_words] + [LEGAL_SUFFIX_MAP[suffix_candidate]]
                break
    
    return ' '.join(words)


def expand_org_abbreviation(value: str) -> Tuple[str, bool]:
    """Expand known organization abbreviations.
    
    Args:
        value: Organization name or abbreviation
        
    Returns:
        Tuple of (expanded_name, was_expanded)
    """
    if not value:
        return value, False
    
    val_lower = value.strip().lower()
    
    if val_lower in ORG_ABBREVIATIONS:
        return ORG_ABBREVIATIONS[val_lower], True
    
    return value, False


# ============================================================================
# HELPER FUNCTIONS — JOB TITLE
# ============================================================================

def to_job_title_case(value: str) -> str:
    """Convert job title to title case.
    
    Args:
        value: Input string
        
    Returns:
        Title-cased job title
    """
    if not value:
        return value
    
    words = value.split()
    result = []
    
    for word in words:
        upper_word = word.upper()
        # Preserve certain abbreviations
        if upper_word in {'IT', 'HR', 'AI', 'ML', 'VP', 'SVP', 'EVP', 'CEO', 'CFO', 'CTO', 'COO', 'CIO', 'CMO'}:
            result.append(upper_word)
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def expand_job_abbreviations(value: str) -> Tuple[str, Dict[str, str]]:
    """Expand abbreviations in job titles.
    
    Args:
        value: Job title
        
    Returns:
        Tuple of (expanded_title, expansions_made)
    """
    if not value:
        return value, {}
    
    words = value.split()
    result = []
    expansions = {}
    
    for word in words:
        word_lower = word.lower().rstrip('.')
        if word_lower in JOB_ABBREVIATIONS:
            expansion = JOB_ABBREVIATIONS[word_lower]
            expansions[word] = expansion
            result.append(expansion)
        else:
            result.append(word)
    
    return ' '.join(result), expansions


def extract_seniority(value: str) -> Optional[Tuple[str, int]]:
    """Extract seniority level from job title.
    
    Args:
        value: Job title
        
    Returns:
        Tuple of (seniority_keyword, level) or None
    """
    if not value:
        return None
    
    val_lower = value.lower()
    
    for keyword, level in sorted(SENIORITY_LEVELS.items(), key=lambda x: -len(x[0])):
        if keyword in val_lower:
            return keyword.title(), level
    
    return None


def find_job_variants(series: pd.Series, threshold: float = 0.85) -> Dict[str, List[str]]:
    """Find variant job titles that likely refer to the same role.
    
    Args:
        series: pandas Series of job titles
        threshold: Similarity threshold
        
    Returns:
        Dictionary mapping canonical titles to variants
    """
    unique_vals = [str(v) for v in series.dropna().unique()]
    if len(unique_vals) < 2:
        return {}
    
    # Expand abbreviations first for better matching
    expanded = {}
    for val in unique_vals:
        exp, _ = expand_job_abbreviations(val)
        expanded[val] = exp.lower()
    
    # Group similar values
    groups = defaultdict(list)
    processed = set()
    
    for val in unique_vals:
        if val in processed:
            continue
        
        similar = [val]
        for other in unique_vals:
            if other != val and other not in processed:
                if calculate_similarity(expanded[val], expanded[other]) >= threshold:
                    similar.append(other)
                    processed.add(other)
        
        if len(similar) > 1:
            # Use the longest expanded form as canonical
            canonical = max(similar, key=lambda x: len(expanded[x]))
            groups[canonical] = similar
        
        processed.add(val)
    
    return dict(groups)


# ============================================================================
# HELPER FUNCTIONS — DEPARTMENT
# ============================================================================

def expand_dept_abbreviation(value: str) -> Tuple[str, bool]:
    """Expand department abbreviations.
    
    Args:
        value: Department name
        
    Returns:
        Tuple of (expanded_name, was_expanded)
    """
    if not value:
        return value, False
    
    val_lower = value.strip().lower()
    
    if val_lower in DEPT_ABBREVIATIONS:
        return DEPT_ABBREVIATIONS[val_lower], True
    
    return value, False


def extract_department_hierarchy(value: str) -> Optional[Dict[str, str]]:
    """Extract parent/child hierarchy from department name.
    
    Args:
        value: Department name with potential hierarchy
        
    Returns:
        Dict with 'parent' and 'child' keys, or None
    """
    if not value:
        return None
    
    for sep in HIERARCHY_SEPARATORS:
        if sep in value:
            parts = value.split(sep)
            if len(parts) >= 2:
                return {
                    "parent": parts[0].strip(),
                    "child": parts[-1].strip(),
                    "full_path": [p.strip() for p in parts],
                }
    
    return None


# ============================================================================
# HELPER FUNCTIONS — REFERENCE NUMBER
# ============================================================================

def detect_refno_pattern(series: pd.Series) -> Optional[Dict[str, Any]]:
    """Detect pattern in reference numbers.
    
    Args:
        series: pandas Series of reference numbers
        
    Returns:
        Pattern info dict
    """
    non_null = [str(v) for v in series.dropna()]
    if len(non_null) < 3:
        return None
    
    # Find common prefix
    prefix = non_null[0]
    for val in non_null[1:]:
        while not val.startswith(prefix) and prefix:
            prefix = prefix[:-1]
    
    # Check for sequential pattern
    numeric_parts = []
    for val in non_null:
        # Extract numeric suffix
        match = re.search(r'(\d+)$', val)
        if match:
            numeric_parts.append(int(match.group(1)))
    
    is_sequential = False
    gaps = []
    if len(numeric_parts) > 1:
        sorted_nums = sorted(set(numeric_parts))
        expected = list(range(sorted_nums[0], sorted_nums[-1] + 1))
        is_sequential = sorted_nums == expected
        if not is_sequential:
            gaps = [n for n in expected if n not in sorted_nums]
    
    return {
        "prefix": prefix if len(prefix) >= 1 else None,
        "is_sequential": is_sequential,
        "gaps": gaps[:10],  # Limit to first 10 gaps
        "min_value": min(numeric_parts) if numeric_parts else None,
        "max_value": max(numeric_parts) if numeric_parts else None,
    }


def check_refno_uniqueness(series: pd.Series) -> List[Any]:
    """Check for duplicate reference numbers.
    
    Args:
        series: pandas Series of reference numbers
        
    Returns:
        List of duplicate values
    """
    non_null = series.dropna()
    duplicates = non_null[non_null.duplicated(keep=False)]
    return list(duplicates.unique())


# ============================================================================
# HELPER FUNCTIONS — VERSION
# ============================================================================

def parse_version(value: str) -> Optional[Dict[str, Any]]:
    """Parse version string into components.
    
    Args:
        value: Version string
        
    Returns:
        Dict with version components or None
    """
    if not value:
        return None
    
    val_clean = str(value).strip()
    
    for pattern, fmt_type in VERSION_PATTERNS:
        match = pattern.match(val_clean)
        if match:
            groups = match.groups()
            return {
                "format": fmt_type,
                "major": int(groups[0]) if groups[0] else 0,
                "minor": int(groups[1]) if len(groups) > 1 and groups[1] else 0,
                "patch": int(groups[2]) if len(groups) > 2 and groups[2] else 0,
                "original": val_clean,
            }
    
    return None


def normalize_version(value: str) -> str:
    """Normalize version to standard format (vX.Y.Z or vX.Y).
    
    Args:
        value: Version string
        
    Returns:
        Normalized version
    """
    parsed = parse_version(value)
    if not parsed:
        return value
    
    major = parsed["major"]
    minor = parsed["minor"]
    patch = parsed["patch"]
    
    if patch > 0:
        return f"v{major}.{minor}.{patch}"
    elif minor > 0:
        return f"v{major}.{minor}"
    else:
        return f"v{major}.0"


def version_sort_key(value: str) -> Tuple[int, int, int]:
    """Generate sort key for version comparison.
    
    Args:
        value: Version string
        
    Returns:
        Tuple for sorting (major, minor, patch)
    """
    parsed = parse_version(value)
    if not parsed:
        return (0, 0, 0)
    
    return (parsed["major"], parsed["minor"], parsed["patch"])


# ============================================================================
# MAIN CLASS
# ============================================================================

class OrgProductRules:
    """Organizational & Product cleaning rules."""
    
    APPLICABLE_HTYPES = {
        "HTYPE-024",  # Product Name
        "HTYPE-025",  # Product Code / SKU
        "HTYPE-026",  # Organization Name
        "HTYPE-027",  # Job Title
        "HTYPE-028",  # Department
        "HTYPE-034",  # Serial/Reference Number
        "HTYPE-047",  # Version Number
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
        self.product_variants: Dict[str, Dict[str, List[str]]] = {}
        self.sku_patterns: Dict[str, Dict[str, Any]] = {}
        self.job_variants: Dict[str, Dict[str, List[str]]] = {}
        self.refno_patterns: Dict[str, Dict[str, Any]] = {}
        self.seniority_data: Dict[str, Dict[int, Tuple[str, int]]] = {}
    
    def _ensure_object_dtype(self, col: str):
        """Ensure column has object dtype for mixed type assignment."""
        if col in self.df.columns and self.df[col].dtype in ['string', 'object']:
            self.df[col] = self.df[col].astype(object)
    
    def add_flag(self, row_idx: int, col: str, formula_id: str,
                 message: str, value: Any, severity: str = "warning"):
        """Add a flag for manual review."""
        self.flags.append({
            "row": row_idx,
            "column": col,
            "formula": formula_id,
            "message": message,
            "value": value,
            "severity": severity,
        })
    
    def log_cleaning(self, result: CleaningResult):
        """Log cleaning action to database."""
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
    # PROD FORMULAS (HTYPE-024: Product Name)
    # ========================================================================
    
    def PROD_01_title_case_normalization(self, col: str) -> CleaningResult:
        """PROD-01: Apply title case to product names."""
        result = CleaningResult(column=col, formula_id="PROD-01")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            title_cased = to_product_title_case(val.strip())
            if title_cased != val:
                self.df.at[idx, col] = title_cased
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def PROD_02_variant_consolidation(self, col: str) -> CleaningResult:
        """PROD-02: Find and flag product name variants."""
        result = CleaningResult(column=col, formula_id="PROD-02")
        
        variants = find_product_variants(self.df[col], threshold=0.8)
        self.product_variants[col] = variants
        
        if variants:
            result.details["variant_groups"] = {
                k: v for k, v in variants.items()
            }
            result.details["recommendation"] = (
                "Review variant groups and confirm canonical names."
            )
            result.was_auto_applied = False
            
            # Flag rows with variants
            for canonical, variant_list in variants.items():
                for idx, val in self.df[col].items():
                    if val in variant_list and val != canonical:
                        self.add_flag(idx, col, "PROD-02",
                                     f"Possible variant of '{canonical}'", val,
                                     severity="info")
                        result.rows_flagged += 1
            
            self.log_cleaning(result)
        
        return result
    
    def PROD_03_special_character_cleaning(self, col: str) -> CleaningResult:
        """PROD-03: Remove non-standard characters from product names."""
        result = CleaningResult(column=col, formula_id="PROD-03")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            cleaned = clean_product_special_chars(val)
            if cleaned != val:
                self.df.at[idx, col] = cleaned
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def PROD_04_duplicate_name_code_conflict(self, col: str) -> CleaningResult:
        """PROD-04: Flag same code with different names."""
        result = CleaningResult(column=col, formula_id="PROD-04")
        
        # Find potential code column
        code_cols = [c for c, h in self.htype_map.items() 
                    if h == "HTYPE-025" and c in self.df.columns]
        
        if not code_cols:
            return result
        
        code_col = code_cols[0]
        
        # Group by code and check for name conflicts
        conflicts = []
        for code, group in self.df.groupby(code_col):
            if pd.isna(code):
                continue
            
            unique_names = group[col].dropna().unique()
            if len(unique_names) > 1:
                conflicts.append({
                    "code": code,
                    "names": list(unique_names),
                    "indices": list(group.index),
                })
        
        if conflicts:
            result.details["conflicts"] = conflicts
            result.was_auto_applied = False
            
            for conflict in conflicts:
                for idx in conflict["indices"]:
                    self.add_flag(idx, col, "PROD-04",
                                 f"Code '{conflict['code']}' has multiple names: {conflict['names']}",
                                 self.df.at[idx, col], severity="error")
                    result.rows_flagged += 1
            
            self.log_cleaning(result)
        
        return result
    
    def PROD_05_missing_name_recovery(self, col: str) -> CleaningResult:
        """PROD-05: Flag missing product names where code exists."""
        result = CleaningResult(column=col, formula_id="PROD-05")
        
        # Find potential code column
        code_cols = [c for c, h in self.htype_map.items() 
                    if h == "HTYPE-025" and c in self.df.columns]
        
        if not code_cols:
            # Just flag null names
            for idx, val in self.df[col].items():
                if pd.isna(val):
                    self.add_flag(idx, col, "PROD-05",
                                 "Missing product name", None)
                    result.rows_flagged += 1
        else:
            code_col = code_cols[0]
            
            # Build code-to-name lookup from existing data
            code_name_map = {}
            for idx, row in self.df.iterrows():
                code = row[code_col]
                name = row[col]
                if not pd.isna(code) and not pd.isna(name):
                    code_name_map[code] = name
            
            # Try to fill missing names
            for idx, row in self.df.iterrows():
                code = row[code_col]
                name = row[col]
                
                if pd.isna(name) and not pd.isna(code):
                    if code in code_name_map:
                        self.df.at[idx, col] = code_name_map[code]
                        result.changes_made += 1
                    else:
                        self.add_flag(idx, col, "PROD-05",
                                     f"Missing name for code '{code}'", None)
                        result.rows_flagged += 1
        
        if result.changes_made > 0 or result.rows_flagged > 0:
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # SKU FORMULAS (HTYPE-025: Product Code / SKU / Barcode)
    # ========================================================================
    
    def SKU_01_format_consistency(self, col: str) -> CleaningResult:
        """SKU-01: Enforce uppercase and consistent format."""
        result = CleaningResult(column=col, formula_id="SKU-01")
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            cleaned = clean_sku(str(val))
            if cleaned != str(val):
                self.df.at[idx, col] = cleaned
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def SKU_02_duplicate_alert(self, col: str) -> CleaningResult:
        """SKU-02: Alert on duplicate SKUs with different product names."""
        result = CleaningResult(column=col, formula_id="SKU-02")
        
        # Find product name column
        name_cols = [c for c, h in self.htype_map.items() 
                   if h == "HTYPE-024" and c in self.df.columns]
        
        if not name_cols:
            # Just check for duplicates
            duplicates = check_refno_uniqueness(self.df[col])
            for dup in duplicates:
                for idx, val in self.df[col].items():
                    if val == dup:
                        self.add_flag(idx, col, "SKU-02",
                                     f"Duplicate SKU: {dup}", val)
                        result.rows_flagged += 1
        else:
            name_col = name_cols[0]
            
            # Check for same SKU with different names
            for sku, group in self.df.groupby(col):
                if pd.isna(sku):
                    continue
                
                unique_names = group[name_col].dropna().unique()
                if len(unique_names) > 1:
                    for idx in group.index:
                        self.add_flag(idx, col, "SKU-02",
                                     f"SKU '{sku}' has multiple products: {list(unique_names)}",
                                     sku, severity="error")
                        result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def SKU_03_leading_zero_preservation(self, col: str) -> CleaningResult:
        """SKU-03: Ensure SKUs are stored as strings to preserve leading zeros."""
        result = CleaningResult(column=col, formula_id="SKU-03")
        
        # Convert numeric values to string
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, (int, float)):
                str_val = str(int(val)) if val == int(val) else str(val)
                self.df.at[idx, col] = str_val
                result.changes_made += 1
        
        # Detect pattern for context
        pattern = detect_sku_pattern(self.df[col])
        if pattern:
            self.sku_patterns[col] = pattern
            result.details["pattern"] = pattern
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def SKU_04_barcode_validation(self, col: str) -> CleaningResult:
        """SKU-04: Validate EAN-13, UPC-A, EAN-8 check digits."""
        result = CleaningResult(column=col, formula_id="SKU-04")
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            
            # Check different barcode formats
            is_valid = None
            barcode_type = None
            
            if EAN13_PATTERN.match(val_str):
                barcode_type = "EAN-13"
                is_valid = validate_ean13(val_str)
            elif UPCA_PATTERN.match(val_str):
                barcode_type = "UPC-A"
                is_valid = validate_upca(val_str)
            elif EAN8_PATTERN.match(val_str):
                barcode_type = "EAN-8"
                is_valid = validate_ean8(val_str)
            
            if barcode_type and not is_valid:
                self.add_flag(idx, col, "SKU-04",
                             f"Invalid {barcode_type} check digit", val_str,
                             severity="error")
                result.rows_flagged += 1
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def SKU_05_non_alphanumeric_removal(self, col: str) -> CleaningResult:
        """SKU-05: Remove characters outside [A-Z0-9-]."""
        result = CleaningResult(column=col, formula_id="SKU-05")
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            cleaned = ''.join(c for c in val_str.upper() if c in SKU_VALID_CHARS)
            
            if cleaned != val_str:
                self.df.at[idx, col] = cleaned
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # ORG FORMULAS (HTYPE-026: Organization / Company Name)
    # ========================================================================
    
    def ORG_01_title_case_normalization(self, col: str) -> CleaningResult:
        """ORG-01: Apply title case preserving abbreviations."""
        result = CleaningResult(column=col, formula_id="ORG-01")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            title_cased = to_org_title_case(val.strip())
            if title_cased != val:
                self.df.at[idx, col] = title_cased
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def ORG_02_legal_suffix_standardization(self, col: str) -> CleaningResult:
        """ORG-02: Standardize legal suffixes (Ltd., Inc., Corp., etc.)."""
        result = CleaningResult(column=col, formula_id="ORG-02")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            standardized = standardize_legal_suffix(val)
            if standardized != val:
                self.df.at[idx, col] = standardized
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def ORG_03_abbreviation_expansion(self, col: str) -> CleaningResult:
        """ORG-03: Expand known organization abbreviations."""
        result = CleaningResult(column=col, formula_id="ORG-03")
        
        expansions = {}
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            expanded, was_expanded = expand_org_abbreviation(val)
            if was_expanded:
                expansions[val] = expanded
                self.df.at[idx, col] = expanded
                result.changes_made += 1
        
        if expansions:
            result.details["expansions"] = expansions
            self.log_cleaning(result)
        
        return result
    
    def ORG_04_variant_consolidation(self, col: str) -> CleaningResult:
        """ORG-04: Find and flag organization name variants."""
        result = CleaningResult(column=col, formula_id="ORG-04")
        
        variants = find_product_variants(self.df[col], threshold=0.85)
        
        if variants:
            result.details["variant_groups"] = variants
            result.was_auto_applied = False
            
            for canonical, variant_list in variants.items():
                for idx, val in self.df[col].items():
                    if val in variant_list and val != canonical:
                        self.add_flag(idx, col, "ORG-04",
                                     f"Possible variant of '{canonical}'", val,
                                     severity="info")
                        result.rows_flagged += 1
            
            self.log_cleaning(result)
        
        return result
    
    def ORG_05_null_handling(self, col: str) -> CleaningResult:
        """ORG-05: Handle null organization names."""
        result = CleaningResult(column=col, formula_id="ORG-05")
        
        null_count = self.df[col].isna().sum()
        
        if null_count > 0:
            result.details["null_count"] = int(null_count)
            result.details["recommendation"] = (
                "Organization names cannot be predicted. "
                "Please provide or mark as 'Unknown'."
            )
            result.rows_flagged = int(null_count)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # JOB FORMULAS (HTYPE-027: Job Title / Designation)
    # ========================================================================
    
    def JOB_01_title_case_normalization(self, col: str) -> CleaningResult:
        """JOB-01: Apply title case to job titles."""
        result = CleaningResult(column=col, formula_id="JOB-01")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            title_cased = to_job_title_case(val.strip())
            if title_cased != val:
                self.df.at[idx, col] = title_cased
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def JOB_02_abbreviation_expansion(self, col: str) -> CleaningResult:
        """JOB-02: Expand job title abbreviations."""
        result = CleaningResult(column=col, formula_id="JOB-02")
        
        all_expansions = {}
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            expanded, expansions = expand_job_abbreviations(val)
            if expansions:
                all_expansions.update(expansions)
                self.df.at[idx, col] = expanded
                result.changes_made += 1
        
        if all_expansions:
            result.details["expansions"] = all_expansions
            self.log_cleaning(result)
        
        return result
    
    def JOB_03_variant_consolidation(self, col: str) -> CleaningResult:
        """JOB-03: Find and flag job title variants."""
        result = CleaningResult(column=col, formula_id="JOB-03")
        
        variants = find_job_variants(self.df[col], threshold=0.85)
        self.job_variants[col] = variants
        
        if variants:
            result.details["variant_groups"] = variants
            result.was_auto_applied = False
            
            for canonical, variant_list in variants.items():
                for idx, val in self.df[col].items():
                    if str(val) in variant_list and str(val) != canonical:
                        self.add_flag(idx, col, "JOB-03",
                                     f"Possible variant of '{canonical}'", val,
                                     severity="info")
                        result.rows_flagged += 1
            
            self.log_cleaning(result)
        
        return result
    
    def JOB_04_seniority_extraction(self, col: str) -> CleaningResult:
        """JOB-04: Extract seniority level from job titles."""
        result = CleaningResult(column=col, formula_id="JOB-04")
        
        seniority_data = {}
        levels_found = Counter()
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            seniority = extract_seniority(val)
            if seniority:
                seniority_data[idx] = seniority
                levels_found[seniority[0]] += 1
        
        if seniority_data:
            self.seniority_data[col] = seniority_data
            result.details["levels_found"] = dict(levels_found)
            result.details["rows_with_seniority"] = len(seniority_data)
            self.log_cleaning(result)
        
        return result
    
    def JOB_05_department_cross_reference(self, col: str) -> CleaningResult:
        """JOB-05: Flag job title / department mismatches."""
        result = CleaningResult(column=col, formula_id="JOB-05")
        
        # Find department column
        dept_cols = [c for c, h in self.htype_map.items() 
                    if h == "HTYPE-028" and c in self.df.columns]
        
        if not dept_cols:
            return result
        
        dept_col = dept_cols[0]
        
        # Define obvious mismatches
        title_dept_conflicts = {
            "doctor": {"finance", "accounting", "sales", "marketing", "it", "engineering"},
            "nurse": {"finance", "accounting", "sales", "marketing", "it", "engineering"},
            "accountant": {"medical", "healthcare", "engineering", "it"},
            "engineer": {"medical", "healthcare", "finance", "accounting"},
            "developer": {"medical", "healthcare", "finance", "accounting"},
        }
        
        for idx, row in self.df.iterrows():
            title = row[col]
            dept = row[dept_col]
            
            if pd.isna(title) or pd.isna(dept):
                continue
            
            title_lower = str(title).lower()
            dept_lower = str(dept).lower()
            
            for title_key, conflict_depts in title_dept_conflicts.items():
                if title_key in title_lower:
                    for conflict_dept in conflict_depts:
                        if conflict_dept in dept_lower:
                            self.add_flag(idx, col, "JOB-05",
                                         f"Title '{title}' unusual for dept '{dept}'",
                                         title, severity="info")
                            result.rows_flagged += 1
                            break
        
        if result.rows_flagged > 0:
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # DEPT FORMULAS (HTYPE-028: Department / Division)
    # ========================================================================
    
    def DEPT_01_title_case(self, col: str) -> CleaningResult:
        """DEPT-01: Apply title case to department names."""
        result = CleaningResult(column=col, formula_id="DEPT-01")
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            title_cased = to_org_title_case(val.strip())
            if title_cased != val:
                self.df.at[idx, col] = title_cased
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def DEPT_02_abbreviation_expansion(self, col: str) -> CleaningResult:
        """DEPT-02: Expand department abbreviations."""
        result = CleaningResult(column=col, formula_id="DEPT-02")
        
        expansions = {}
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            expanded, was_expanded = expand_dept_abbreviation(val)
            if was_expanded:
                expansions[val] = expanded
                self.df.at[idx, col] = expanded
                result.changes_made += 1
        
        if expansions:
            result.details["expansions"] = expansions
            self.log_cleaning(result)
        
        return result
    
    def DEPT_03_variant_consolidation(self, col: str) -> CleaningResult:
        """DEPT-03: Find and consolidate department variants."""
        result = CleaningResult(column=col, formula_id="DEPT-03")
        
        variants = find_product_variants(self.df[col], threshold=0.8)
        
        if variants:
            result.details["variant_groups"] = variants
            result.was_auto_applied = False
            
            for canonical, variant_list in variants.items():
                for idx, val in self.df[col].items():
                    if val in variant_list and val != canonical:
                        self.add_flag(idx, col, "DEPT-03",
                                     f"Possible variant of '{canonical}'", val,
                                     severity="info")
                        result.rows_flagged += 1
            
            self.log_cleaning(result)
        
        return result
    
    def DEPT_04_hierarchy_extraction(self, col: str) -> CleaningResult:
        """DEPT-04: Extract parent/child hierarchy from department names."""
        result = CleaningResult(column=col, formula_id="DEPT-04")
        
        hierarchies_found = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            hierarchy = extract_department_hierarchy(val)
            if hierarchy:
                hierarchies_found.append({
                    "index": idx,
                    "value": val,
                    **hierarchy
                })
        
        if hierarchies_found:
            result.details["hierarchies_detected"] = len(hierarchies_found)
            result.details["sample"] = hierarchies_found[:5]
            result.details["recommendation"] = (
                "Consider splitting into parent_department and child_department columns."
            )
            self.log_cleaning(result)
        
        return result
    
    def DEPT_05_null_handling(self, col: str) -> CleaningResult:
        """DEPT-05: Handle null department values."""
        result = CleaningResult(column=col, formula_id="DEPT-05")
        
        null_count = self.df[col].isna().sum()
        
        if null_count > 0:
            result.details["null_count"] = int(null_count)
            result.rows_flagged = int(null_count)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # REFNO FORMULAS (HTYPE-034: Serial / Reference Number)
    # ========================================================================
    
    def REFNO_01_uniqueness_check(self, col: str) -> CleaningResult:
        """REFNO-01: Check for duplicate reference numbers."""
        result = CleaningResult(column=col, formula_id="REFNO-01")
        
        duplicates = check_refno_uniqueness(self.df[col])
        
        if duplicates:
            result.details["duplicate_values"] = duplicates
            result.was_auto_applied = False
            
            for dup in duplicates:
                for idx, val in self.df[col].items():
                    if val == dup:
                        self.add_flag(idx, col, "REFNO-01",
                                     f"Duplicate reference: {dup}", dup,
                                     severity="error")
                        result.rows_flagged += 1
            
            self.log_cleaning(result)
        
        return result
    
    def REFNO_02_format_consistency(self, col: str) -> CleaningResult:
        """REFNO-02: Check for consistent format/pattern."""
        result = CleaningResult(column=col, formula_id="REFNO-02")
        
        pattern = detect_refno_pattern(self.df[col])
        
        if pattern:
            self.refno_patterns[col] = pattern
            result.details["pattern"] = pattern
            
            # Flag values that deviate from pattern
            if pattern.get("prefix"):
                prefix = pattern["prefix"]
                for idx, val in self.df[col].items():
                    if pd.isna(val):
                        continue
                    if not str(val).startswith(prefix):
                        self.add_flag(idx, col, "REFNO-02",
                                     f"Does not match expected prefix '{prefix}'",
                                     val, severity="warning")
                        result.rows_flagged += 1
            
            if result.rows_flagged > 0:
                result.was_auto_applied = False
            
            self.log_cleaning(result)
        
        return result
    
    def REFNO_03_leading_zero_preservation(self, col: str) -> CleaningResult:
        """REFNO-03: Ensure stored as string to preserve leading zeros."""
        result = CleaningResult(column=col, formula_id="REFNO-03")
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, (int, float)):
                str_val = str(int(val)) if val == int(val) else str(val)
                self.df.at[idx, col] = str_val
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def REFNO_04_sequence_gap_detection(self, col: str) -> CleaningResult:
        """REFNO-04: Detect gaps in sequential reference numbers."""
        result = CleaningResult(column=col, formula_id="REFNO-04")
        
        pattern = self.refno_patterns.get(col) or detect_refno_pattern(self.df[col])
        
        if pattern and pattern.get("gaps"):
            result.details["gaps"] = pattern["gaps"]
            result.details["recommendation"] = (
                f"Missing reference numbers detected: {pattern['gaps'][:5]}..."
                if len(pattern['gaps']) > 5 else
                f"Missing reference numbers: {pattern['gaps']}"
            )
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def REFNO_05_null_handling(self, col: str) -> CleaningResult:
        """REFNO-05: Handle null reference numbers."""
        result = CleaningResult(column=col, formula_id="REFNO-05")
        
        null_count = self.df[col].isna().sum()
        
        if null_count > 0:
            result.details["null_count"] = int(null_count)
            
            # If we have a pattern, suggest next values
            pattern = self.refno_patterns.get(col)
            if pattern and pattern.get("max_value") is not None:
                next_val = pattern["max_value"] + 1
                prefix = pattern.get("prefix", "")
                result.details["suggested_next"] = f"{prefix}{next_val}"
            
            result.rows_flagged = int(null_count)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # VER FORMULAS (HTYPE-047: Version / Revision Number)
    # ========================================================================
    
    def VER_01_format_standardization(self, col: str) -> CleaningResult:
        """VER-01: Standardize version format to vX.Y or vX.Y.Z."""
        result = CleaningResult(column=col, formula_id="VER-01")
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            normalized = normalize_version(str(val))
            if normalized != str(val):
                self.df.at[idx, col] = normalized
                result.changes_made += 1
        
        if result.changes_made > 0:
            self.log_cleaning(result)
        
        return result
    
    def VER_02_semantic_version_parsing(self, col: str) -> CleaningResult:
        """VER-02: Parse and validate semantic versions."""
        result = CleaningResult(column=col, formula_id="VER-02")
        
        parsed_versions = {}
        invalid_versions = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            parsed = parse_version(str(val))
            if parsed:
                parsed_versions[idx] = parsed
            else:
                invalid_versions.append((idx, val))
        
        result.details["parsed_count"] = len(parsed_versions)
        result.details["formats_detected"] = list(set(
            v["format"] for v in parsed_versions.values()
        ))
        
        if invalid_versions:
            result.details["invalid_count"] = len(invalid_versions)
            for idx, val in invalid_versions:
                self.add_flag(idx, col, "VER-02",
                             "Could not parse version format", val,
                             severity="warning")
                result.rows_flagged += 1
            result.was_auto_applied = False
        
        self.log_cleaning(result)
        return result
    
    def VER_03_chronological_sort_key(self, col: str) -> CleaningResult:
        """VER-03: Create sort key column for proper version ordering."""
        result = CleaningResult(column=col, formula_id="VER-03")
        
        # Create sort key column
        sort_col = f"{col}_sort_key"
        
        sort_keys = []
        for val in self.df[col]:
            if pd.isna(val):
                sort_keys.append((0, 0, 0))
            else:
                sort_keys.append(version_sort_key(str(val)))
        
        # Store as tuple string for JSON serialization
        self.df[sort_col] = [f"{k[0]}.{k[1]}.{k[2]}" for k in sort_keys]
        
        result.details["sort_column_created"] = sort_col
        result.details["recommendation"] = (
            f"Use '{sort_col}' for correct version ordering"
        )
        self.log_cleaning(result)
        
        return result
    
    def VER_04_null_handling(self, col: str) -> CleaningResult:
        """VER-04: Handle null version values."""
        result = CleaningResult(column=col, formula_id="VER-04")
        
        null_count = self.df[col].isna().sum()
        
        if null_count > 0:
            result.details["null_count"] = int(null_count)
            result.details["options"] = [
                "Keep as null",
                "Mark as 'Unknown Version'",
                "Mark as 'v0.0' (baseline)"
            ]
            result.rows_flagged = int(null_count)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_for_column(self, col: str, htype: str) -> List[CleaningResult]:
        """Run all applicable formulas for a column based on its HTYPE."""
        results = []
        
        if htype == "HTYPE-024":  # Product Name
            results.append(self.PROD_03_special_character_cleaning(col))
            results.append(self.PROD_01_title_case_normalization(col))
            results.append(self.PROD_02_variant_consolidation(col))
            results.append(self.PROD_04_duplicate_name_code_conflict(col))
            results.append(self.PROD_05_missing_name_recovery(col))
        
        elif htype == "HTYPE-025":  # Product Code / SKU
            results.append(self.SKU_03_leading_zero_preservation(col))
            results.append(self.SKU_01_format_consistency(col))
            results.append(self.SKU_05_non_alphanumeric_removal(col))
            results.append(self.SKU_04_barcode_validation(col))
            results.append(self.SKU_02_duplicate_alert(col))
        
        elif htype == "HTYPE-026":  # Organization Name
            results.append(self.ORG_01_title_case_normalization(col))
            results.append(self.ORG_02_legal_suffix_standardization(col))
            results.append(self.ORG_03_abbreviation_expansion(col))
            results.append(self.ORG_04_variant_consolidation(col))
            results.append(self.ORG_05_null_handling(col))
        
        elif htype == "HTYPE-027":  # Job Title
            results.append(self.JOB_01_title_case_normalization(col))
            results.append(self.JOB_02_abbreviation_expansion(col))
            results.append(self.JOB_03_variant_consolidation(col))
            results.append(self.JOB_04_seniority_extraction(col))
            results.append(self.JOB_05_department_cross_reference(col))
        
        elif htype == "HTYPE-028":  # Department
            results.append(self.DEPT_01_title_case(col))
            results.append(self.DEPT_02_abbreviation_expansion(col))
            results.append(self.DEPT_03_variant_consolidation(col))
            results.append(self.DEPT_04_hierarchy_extraction(col))
            results.append(self.DEPT_05_null_handling(col))
        
        elif htype == "HTYPE-034":  # Reference Number
            results.append(self.REFNO_03_leading_zero_preservation(col))
            results.append(self.REFNO_02_format_consistency(col))
            results.append(self.REFNO_01_uniqueness_check(col))
            results.append(self.REFNO_04_sequence_gap_detection(col))
            results.append(self.REFNO_05_null_handling(col))
        
        elif htype == "HTYPE-047":  # Version Number
            results.append(self.VER_01_format_standardization(col))
            results.append(self.VER_02_semantic_version_parsing(col))
            results.append(self.VER_03_chronological_sort_key(col))
            results.append(self.VER_04_null_handling(col))
        
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
            "product_variants": {k: len(v) for k, v in self.product_variants.items()},
            "sku_patterns": self.sku_patterns,
            "job_variants": {k: len(v) for k, v in self.job_variants.items()},
            "refno_patterns": self.refno_patterns,
        }
