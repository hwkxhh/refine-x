"""
Contact & Location Cleaning Rules — Session 6

Implements formulas from the Formula Rulebook for:
- HTYPE-009: Phone / Mobile Number (PHONE-01 to PHONE-11)
- HTYPE-010: Email Address (EMAIL-01 to EMAIL-10)
- HTYPE-011: Address / Location Full (ADDR-01 to ADDR-07)
- HTYPE-012: City / District / Region (CITY-01 to CITY-06)
- HTYPE-013: Country (CNTRY-01 to CNTRY-06)
- HTYPE-014: Postal Code / ZIP Code (POST-01 to POST-05)
- HTYPE-035: Coordinates (GEO-01 to GEO-06)

"""

import re
import math
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

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
# PHONE CONSTANTS
# ============================================================================

# Common phone number separators for multi-number detection
PHONE_SEPARATORS = [
    r'\s*/\s*',           # /
    r'\s*,\s*',           # ,
    r'\s*;\s*',           # ;
    r'\s*&\s*',           # &
    r'\s+or\s+',          # " or "
    r'\s*\n\s*',          # newline
    r'\s+/\s+',           # " / "
]
PHONE_SEPARATOR_PATTERN = re.compile('|'.join(PHONE_SEPARATORS), re.IGNORECASE)

# Extension patterns
EXTENSION_PATTERNS = [
    re.compile(r'\s*(?:ext\.?|extension|x|#)\s*(\d+)\s*$', re.IGNORECASE),
]

# Phone placeholder patterns
PHONE_PLACEHOLDERS = {
    "0000000000", "1234567890", "9999999999", "1111111111",
    "0000000", "1111111", "9999999", "1234567",
    "00000000000", "11111111111", "99999999999",
    "n/a", "na", "none", "null", "unknown", "-", "--", ".",
}

# Country code patterns and lengths
COUNTRY_PHONE_SPECS = {
    "US": {"codes": ["+1", "1"], "length": 10, "mobile_prefixes": []},
    "UK": {"codes": ["+44", "44"], "length": [10, 11], "mobile_prefixes": ["7"]},
    "NP": {"codes": ["+977", "977"], "length": 10, "mobile_prefixes": ["98", "97"]},
    "IN": {"codes": ["+91", "91"], "length": 10, "mobile_prefixes": ["9", "8", "7", "6"]},
    "AU": {"codes": ["+61", "61"], "length": 9, "mobile_prefixes": ["4"]},
    "CA": {"codes": ["+1", "1"], "length": 10, "mobile_prefixes": []},
    "DE": {"codes": ["+49", "49"], "length": [10, 11], "mobile_prefixes": ["15", "16", "17"]},
    "FR": {"codes": ["+33", "33"], "length": 9, "mobile_prefixes": ["6", "7"]},
}


# ============================================================================
# EMAIL CONSTANTS
# ============================================================================

# Basic email regex
EMAIL_PATTERN = re.compile(
    r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
)

# Disposable email domains
DISPOSABLE_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "tempmail.com", "throwaway.email",
    "yopmail.com", "10minutemail.com", "fakeinbox.com", "sharklasers.com",
    "guerrillamailblock.com", "pokemail.net", "spam4.me", "trashmail.com",
    "mailnesia.com", "tempr.email", "dispostable.com", "maildrop.cc",
}

# Email placeholder patterns
EMAIL_PLACEHOLDERS = {
    "test@test.com", "admin@admin.com", "na@na.com", "noreply@noreply.com",
    "test@example.com", "user@example.com", "sample@sample.com",
    "email@email.com", "mail@mail.com", "example@example.com",
    "no@email.com", "none@none.com", "null@null.com",
}

# Common domain typos
DOMAIN_TYPOS = {
    "gmial.com": "gmail.com",
    "gmaill.com": "gmail.com",
    "gamil.com": "gmail.com",
    "gnail.com": "gmail.com",
    "gmai.com": "gmail.com",
    "yahooo.com": "yahoo.com",
    "yaho.com": "yahoo.com",
    "yahho.com": "yahoo.com",
    "hotmai.com": "hotmail.com",
    "hotmal.com": "hotmail.com",
    "hotmaill.com": "hotmail.com",
    "outloo.com": "outlook.com",
    "outlok.com": "outlook.com",
    "outlookk.com": "outlook.com",
}


# ============================================================================
# ADDRESS CONSTANTS
# ============================================================================

# Address abbreviations to expand
ADDRESS_ABBREVIATIONS = {
    r'\bst\.?\b': "Street",
    r'\bave\.?\b': "Avenue",
    r'\bapt\.?\b': "Apartment",
    r'\bblvd\.?\b': "Boulevard",
    r'\brd\.?\b': "Road",
    r'\bdr\.?\b': "Drive",
    r'\bln\.?\b': "Lane",
    r'\bct\.?\b': "Court",
    r'\bpl\.?\b': "Place",
    r'\bpkwy\.?\b': "Parkway",
    r'\bhwy\.?\b': "Highway",
    r'\bno\.?\b': "Number",
    r'\bfl\.?\b': "Floor",
    r'\bste\.?\b': "Suite",
    r'\bbldg\.?\b': "Building",
}

# Address placeholders
ADDRESS_PLACEHOLDERS = {
    "n/a", "na", "none", "null", "unknown", "-", "--",
    "address here", "test address", "123 test st", "123 test street",
    "sample address", "address", "no address", "not provided",
}

# PO Box patterns
PO_BOX_PATTERN = re.compile(
    r'\b(?:p\.?\s*o\.?\s*box|post\s*office\s*box|po\s*box|pobox)\s*\d*',
    re.IGNORECASE
)


# ============================================================================
# CITY/COUNTRY CONSTANTS
# ============================================================================

# Common city abbreviations
CITY_ABBREVIATIONS = {
    "ktm": "Kathmandu",
    "nyc": "New York City",
    "la": "Los Angeles",
    "sf": "San Francisco",
    "dc": "Washington D.C.",
    "phx": "Phoenix",
    "chi": "Chicago",
    "bkk": "Bangkok",
    "hk": "Hong Kong",
    "sg": "Singapore",
    "ldn": "London",
    "mum": "Mumbai",
    "del": "Delhi",
    "blr": "Bangalore",
    "hyd": "Hyderabad",
}

# ISO country codes and names
ISO_COUNTRIES = {
    # ISO-2: (ISO-3, Full Name)
    "AF": ("AFG", "Afghanistan"),
    "AL": ("ALB", "Albania"),
    "DZ": ("DZA", "Algeria"),
    "AU": ("AUS", "Australia"),
    "AT": ("AUT", "Austria"),
    "BD": ("BGD", "Bangladesh"),
    "BE": ("BEL", "Belgium"),
    "BR": ("BRA", "Brazil"),
    "CA": ("CAN", "Canada"),
    "CN": ("CHN", "China"),
    "CO": ("COL", "Colombia"),
    "DK": ("DNK", "Denmark"),
    "EG": ("EGY", "Egypt"),
    "FI": ("FIN", "Finland"),
    "FR": ("FRA", "France"),
    "DE": ("DEU", "Germany"),
    "GR": ("GRC", "Greece"),
    "HK": ("HKG", "Hong Kong"),
    "IN": ("IND", "India"),
    "ID": ("IDN", "Indonesia"),
    "IR": ("IRN", "Iran"),
    "IQ": ("IRQ", "Iraq"),
    "IE": ("IRL", "Ireland"),
    "IL": ("ISR", "Israel"),
    "IT": ("ITA", "Italy"),
    "JP": ("JPN", "Japan"),
    "KE": ("KEN", "Kenya"),
    "KR": ("KOR", "South Korea"),
    "MY": ("MYS", "Malaysia"),
    "MX": ("MEX", "Mexico"),
    "NL": ("NLD", "Netherlands"),
    "NZ": ("NZL", "New Zealand"),
    "NG": ("NGA", "Nigeria"),
    "NO": ("NOR", "Norway"),
    "PK": ("PAK", "Pakistan"),
    "PH": ("PHL", "Philippines"),
    "PL": ("POL", "Poland"),
    "PT": ("PRT", "Portugal"),
    "RU": ("RUS", "Russia"),
    "SA": ("SAU", "Saudi Arabia"),
    "SG": ("SGP", "Singapore"),
    "ZA": ("ZAF", "South Africa"),
    "ES": ("ESP", "Spain"),
    "SE": ("SWE", "Sweden"),
    "CH": ("CHE", "Switzerland"),
    "TW": ("TWN", "Taiwan"),
    "TH": ("THA", "Thailand"),
    "TR": ("TUR", "Turkey"),
    "AE": ("ARE", "United Arab Emirates"),
    "GB": ("GBR", "United Kingdom"),
    "US": ("USA", "United States"),
    "VN": ("VNM", "Vietnam"),
    "NP": ("NPL", "Nepal"),
}

# Common country name variants
COUNTRY_VARIANTS = {
    "usa": "US", "u.s.a.": "US", "u.s.": "US", "america": "US",
    "united states": "US", "united states of america": "US",
    "uk": "GB", "u.k.": "GB", "britain": "GB", "great britain": "GB",
    "england": "GB", "united kingdom": "GB",
    "uae": "AE", "u.a.e.": "AE", "emirates": "AE",
    "korea": "KR", "south korea": "KR", "rok": "KR",
    "russia": "RU", "russian federation": "RU",
    "china": "CN", "prc": "CN", "peoples republic of china": "CN",
    "holland": "NL", "the netherlands": "NL",
    "deutschland": "DE",
}

# Postal code patterns by country
POSTAL_PATTERNS = {
    "US": re.compile(r'^\d{5}(-\d{4})?$'),  # 12345 or 12345-6789
    "CA": re.compile(r'^[A-Z]\d[A-Z]\s?\d[A-Z]\d$', re.IGNORECASE),  # A1A 1A1
    "GB": re.compile(r'^[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}$', re.IGNORECASE),  # SW1A 1AA
    "NP": re.compile(r'^\d{5}$'),  # 44600
    "IN": re.compile(r'^\d{6}$'),  # 110001
    "DE": re.compile(r'^\d{5}$'),  # 10115
    "AU": re.compile(r'^\d{4}$'),  # 2000
    "FR": re.compile(r'^\d{5}$'),  # 75001
}


# ============================================================================
# COORDINATE CONSTANTS
# ============================================================================

# DMS pattern: 27°42'15"N or 27° 42' 15" N
DMS_PATTERN = re.compile(
    r'''
    (?P<degrees>[-+]?\d+(?:\.\d+)?)\s*[°]\s*
    (?:(?P<minutes>\d+(?:\.\d+)?)\s*[′']\s*)?
    (?:(?P<seconds>\d+(?:\.\d+)?)\s*[″"]\s*)?
    (?P<direction>[NSEW])?
    ''',
    re.VERBOSE | re.IGNORECASE
)


# ============================================================================
# HELPER FUNCTIONS — PHONE
# ============================================================================

def extract_digits(value: str) -> str:
    """Extract only digits from a string, keeping leading + for country code."""
    if not value:
        return ""
    has_plus = value.strip().startswith('+')
    digits = re.sub(r'\D', '', value)
    return ('+' + digits) if has_plus else digits


def detect_multi_phone(value: str) -> List[str]:
    """Split a cell containing multiple phone numbers."""
    if pd.isna(value):
        return []
    val_str = str(value).strip()
    if not val_str:
        return []
    
    parts = PHONE_SEPARATOR_PATTERN.split(val_str)
    phones = []
    for part in parts:
        part = part.strip()
        if part and len(extract_digits(part)) >= 7:
            phones.append(part)
    return phones


def is_phone_placeholder(value: str) -> bool:
    """Check if a phone value is a placeholder."""
    if pd.isna(value):
        return True
    
    normalized = str(value).lower().strip()
    if normalized in PHONE_PLACEHOLDERS:
        return True
    
    digits = extract_digits(normalized)
    if digits in PHONE_PLACEHOLDERS:
        return True
    
    # Check for repeated digits
    if digits and len(set(digits)) == 1 and len(digits) >= 7:
        return True
    
    return False


def extract_extension(value: str) -> Tuple[str, Optional[str]]:
    """Extract extension from phone number if present."""
    for pattern in EXTENSION_PATTERNS:
        match = pattern.search(value)
        if match:
            ext = match.group(1)
            phone = pattern.sub('', value).strip()
            return phone, ext
    return value, None


def detect_country_from_phone(phone: str) -> Optional[str]:
    """Detect country from phone number prefix."""
    digits = extract_digits(phone)
    
    for country, spec in COUNTRY_PHONE_SPECS.items():
        for code in spec["codes"]:
            code_digits = code.replace('+', '')
            if digits.startswith(code_digits) or phone.startswith(code):
                return country
    return None


def format_e164(phone: str, country: str = "US") -> str:
    """Format phone number to E.164 standard."""
    digits = extract_digits(phone).lstrip('+')
    
    if country in COUNTRY_PHONE_SPECS:
        spec = COUNTRY_PHONE_SPECS[country]
        code = spec["codes"][0].replace('+', '')
        
        # Remove country code if present
        if digits.startswith(code):
            digits = digits[len(code):]
        
        return f"+{code}{digits}"
    
    return f"+{digits}" if not phone.startswith('+') else phone


def validate_phone_length(phone: str, country: Optional[str] = None) -> bool:
    """Validate phone number length for a country."""
    digits = extract_digits(phone).lstrip('+')
    
    if country and country in COUNTRY_PHONE_SPECS:
        spec = COUNTRY_PHONE_SPECS[country]
        code = spec["codes"][0].replace('+', '')
        
        # Remove country code for length check
        if digits.startswith(code):
            digits = digits[len(code):]
        
        expected = spec["length"]
        if isinstance(expected, list):
            return len(digits) in expected
        return len(digits) == expected
    
    # Default: valid if 7-15 digits
    return 7 <= len(digits) <= 15


def is_mobile_number(phone: str, country: Optional[str] = None) -> Optional[bool]:
    """Detect if phone is mobile based on prefix rules."""
    if not country or country not in COUNTRY_PHONE_SPECS:
        return None
    
    spec = COUNTRY_PHONE_SPECS[country]
    if not spec.get("mobile_prefixes"):
        return None
    
    digits = extract_digits(phone).lstrip('+')
    code = spec["codes"][0].replace('+', '')
    
    if digits.startswith(code):
        digits = digits[len(code):]
    
    for prefix in spec["mobile_prefixes"]:
        if digits.startswith(prefix):
            return True
    
    return False


# ============================================================================
# HELPER FUNCTIONS — EMAIL
# ============================================================================

def validate_email_format(email: str) -> bool:
    """Validate email format."""
    if not email or pd.isna(email):
        return False
    return bool(EMAIL_PATTERN.match(str(email).strip()))


def is_disposable_email(email: str) -> bool:
    """Check if email uses a disposable domain."""
    if '@' not in email:
        return False
    domain = email.split('@')[-1].lower()
    return domain in DISPOSABLE_DOMAINS


def is_email_placeholder(email: str) -> bool:
    """Check if email is a placeholder."""
    if pd.isna(email):
        return True
    return str(email).lower().strip() in EMAIL_PLACEHOLDERS


def fix_email_domain_typo(email: str) -> Tuple[str, Optional[str]]:
    """Fix common domain typos. Returns (fixed_email, original_domain)."""
    if '@' not in email:
        return email, None
    
    local, domain = email.rsplit('@', 1)
    domain_lower = domain.lower()
    
    if domain_lower in DOMAIN_TYPOS:
        fixed_domain = DOMAIN_TYPOS[domain_lower]
        return f"{local}@{fixed_domain}", domain
    
    return email, None


def split_multiple_emails(value: str) -> List[str]:
    """Split cell containing multiple emails."""
    if pd.isna(value):
        return []
    
    # Split by common separators
    emails = re.split(r'[,;\s]+', str(value).strip())
    return [e.strip() for e in emails if '@' in e]


# ============================================================================
# HELPER FUNCTIONS — ADDRESS
# ============================================================================

def normalize_address_whitespace(addr: str) -> str:
    """Normalize whitespace and remove line breaks."""
    if pd.isna(addr):
        return addr
    
    # Replace newlines with spaces
    addr = re.sub(r'[\r\n]+', ' ', str(addr))
    # Collapse multiple spaces
    addr = re.sub(r'\s+', ' ', addr)
    return addr.strip()


def expand_address_abbreviations(addr: str) -> str:
    """Expand common address abbreviations."""
    if pd.isna(addr):
        return addr
    
    result = str(addr)
    for abbr_pattern, expansion in ADDRESS_ABBREVIATIONS.items():
        result = re.sub(abbr_pattern, expansion, result, flags=re.IGNORECASE)
    return result


def is_address_placeholder(addr: str) -> bool:
    """Check if address is a placeholder."""
    if pd.isna(addr):
        return True
    return str(addr).lower().strip() in ADDRESS_PLACEHOLDERS


def has_po_box(addr: str) -> bool:
    """Check if address contains a PO Box."""
    if pd.isna(addr):
        return False
    return bool(PO_BOX_PATTERN.search(str(addr)))


def title_case_address(addr: str) -> str:
    """Apply title case to address, respecting abbreviations."""
    if pd.isna(addr):
        return addr
    
    # Title case each word
    words = str(addr).split()
    result = []
    for word in words:
        # Keep all-caps abbreviations (PO, NW, SE, etc.)
        if len(word) <= 3 and word.isupper():
            result.append(word)
        else:
            result.append(word.title())
    return ' '.join(result)


# ============================================================================
# HELPER FUNCTIONS — CITY/COUNTRY
# ============================================================================

def normalize_city(city: str) -> str:
    """Normalize city name to canonical form."""
    if pd.isna(city):
        return city
    
    city_lower = str(city).lower().strip()
    
    # Check abbreviations
    if city_lower in CITY_ABBREVIATIONS:
        return CITY_ABBREVIATIONS[city_lower]
    
    # Title case
    return str(city).strip().title()


def normalize_country(country: str) -> Optional[str]:
    """Normalize country to ISO-2 code."""
    if pd.isna(country):
        return None
    
    country_str = str(country).strip()
    country_lower = country_str.lower()
    
    # Check variants
    if country_lower in COUNTRY_VARIANTS:
        return COUNTRY_VARIANTS[country_lower]
    
    # Check if already ISO-2
    country_upper = country_str.upper()
    if country_upper in ISO_COUNTRIES:
        return country_upper
    
    # Check if ISO-3
    for iso2, (iso3, name) in ISO_COUNTRIES.items():
        if country_upper == iso3:
            return iso2
        if country_lower == name.lower():
            return iso2
    
    return None


def get_country_name(iso2: str) -> Optional[str]:
    """Get full country name from ISO-2 code."""
    if iso2 and iso2.upper() in ISO_COUNTRIES:
        return ISO_COUNTRIES[iso2.upper()][1]
    return None


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def fuzzy_match_country(country: str, threshold: int = 2) -> Optional[str]:
    """Fuzzy match country name with edit distance threshold."""
    if pd.isna(country):
        return None
    
    country_lower = str(country).lower().strip()
    
    for iso2, (iso3, name) in ISO_COUNTRIES.items():
        if levenshtein_distance(country_lower, name.lower()) <= threshold:
            return iso2
    
    return None


# ============================================================================
# HELPER FUNCTIONS — POSTAL CODE
# ============================================================================

def validate_postal_code(code: str, country: Optional[str] = None) -> bool:
    """Validate postal code format for a country."""
    if pd.isna(code):
        return False
    
    code_str = str(code).strip()
    
    if country and country.upper() in POSTAL_PATTERNS:
        pattern = POSTAL_PATTERNS[country.upper()]
        return bool(pattern.match(code_str))
    
    # Default: alphanumeric, 3-10 characters
    return bool(re.match(r'^[\dA-Za-z\s-]{3,10}$', code_str))


def format_us_zip(code: str) -> str:
    """Format US ZIP code with proper hyphenation."""
    digits = re.sub(r'\D', '', str(code))
    if len(digits) == 9:
        return f"{digits[:5]}-{digits[5:]}"
    return digits


def preserve_leading_zeros(code: Any) -> str:
    """Ensure postal code preserves leading zeros."""
    if pd.isna(code):
        return code
    
    # If numeric, convert to string with leading zeros
    if isinstance(code, (int, float)):
        return str(int(code)).zfill(5)
    
    return str(code)


# ============================================================================
# HELPER FUNCTIONS — COORDINATES
# ============================================================================

def parse_dms_to_decimal(value: str) -> Optional[float]:
    """Convert DMS (degrees minutes seconds) to decimal degrees."""
    if pd.isna(value):
        return None
    
    match = DMS_PATTERN.match(str(value).strip())
    if not match:
        return None
    
    degrees = float(match.group('degrees'))
    minutes = float(match.group('minutes') or 0)
    seconds = float(match.group('seconds') or 0)
    direction = match.group('direction')
    
    decimal = degrees + minutes / 60 + seconds / 3600
    
    if direction and direction.upper() in ('S', 'W'):
        decimal = -decimal
    
    return round(decimal, 6)


def validate_latitude(lat: float) -> bool:
    """Validate latitude is in valid range."""
    try:
        return -90 <= float(lat) <= 90
    except (ValueError, TypeError):
        return False


def validate_longitude(lng: float) -> bool:
    """Validate longitude is in valid range."""
    try:
        return -180 <= float(lng) <= 180
    except (ValueError, TypeError):
        return False


def normalize_coordinate_precision(coord: float, decimals: int = 6) -> float:
    """Normalize coordinate to standard precision."""
    try:
        return round(float(coord), decimals)
    except (ValueError, TypeError):
        return coord


def detect_lat_lng_swap(lat: Any, lng: Any) -> bool:
    """Detect if latitude and longitude might be swapped."""
    try:
        lat_val = float(lat)
        lng_val = float(lng)
        
        # If lat is out of range but lng is valid for lat
        if abs(lat_val) > 90 and abs(lng_val) <= 90:
            return True
        
        return False
    except (ValueError, TypeError):
        return False


# ============================================================================
# MAIN RULES CLASS
# ============================================================================

class ContactLocationRules:
    """
    Contact & Location cleaning rules implementation.
    
    Handles: Phone, Email, Address, City, Country, Postal Code, Coordinates
    """
    
    def __init__(
        self,
        job_id: int,
        df: pd.DataFrame,
        db,
        htype_map: Dict[str, str],
    ):
        self.job_id = job_id
        self.df = df
        self.db = db
        self.htype_map = htype_map
        self.flags: List[Dict[str, Any]] = []
    
    def _log(
        self,
        formula_id: str,
        column: str,
        action: str,
        affected_indices: List[int],
        before_values: List[Any],
        after_values: List[Any],
        was_auto_applied: bool = True,
    ):
        """Log cleaning actions to database."""
        for idx, before, after in zip(affected_indices, before_values, after_values):
            log_entry = CleaningLog(
                job_id=self.job_id,
                row_index=int(idx),
                column_name=column,
                action=action,
                original_value=before,
                new_value=after,
                reason=f"{formula_id}: {action}",
                formula_id=formula_id,
                was_auto_applied=was_auto_applied,
                timestamp=datetime.utcnow(),
            )
            self.db.add(log_entry)
    
    def _flag(
        self,
        formula_id: str,
        column: str,
        issue: str,
        affected_rows: List[int],
        suggested_action: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        """Add a flag for user review."""
        self.flags.append({
            "formula_id": formula_id,
            "column": column,
            "issue": issue,
            "affected_rows": affected_rows[:50],
            "affected_count": len(affected_rows),
            "suggested_action": suggested_action,
            "details": details or {},
        })
    
    # ========================================================================
    # PHONE FORMULAS — HTYPE-009
    # ========================================================================
    
    def PHONE_01_dataset_level_scan(self, col: str) -> CleaningResult:
        """V2.0 — Scan to detect if multi-number is the dataset schema."""
        result = CleaningResult(column=col, formula_id="PHONE-01", was_auto_applied=False)
        
        single_count = 0
        multi_count = 0
        
        for val in self.df[col].dropna():
            phones = detect_multi_phone(str(val))
            if len(phones) >= 2:
                multi_count += 1
            elif len(phones) == 1:
                single_count += 1
        
        total = single_count + multi_count
        if total == 0:
            return result
        
        multi_pct = multi_count / total * 100
        
        result.details["single_number_count"] = single_count
        result.details["multi_number_count"] = multi_count
        result.details["multi_number_percentage"] = round(multi_pct, 1)
        
        if multi_pct >= 50:
            self._flag(
                "PHONE-01", col,
                f"≥50% of rows ({multi_pct:.1f}%) contain multiple phone numbers",
                [],
                "Consider splitting into phone_primary and phone_secondary columns",
                {"multi_percentage": multi_pct},
            )
            result.rows_flagged = multi_count
        
        return result
    
    def PHONE_02_multi_number_split(self, col: str) -> CleaningResult:
        """Split multiple phone numbers into separate columns."""
        result = CleaningResult(column=col, formula_id="PHONE-02")
        
        # Create secondary phone column if doesn't exist
        primary_col = f"{col}_primary"
        secondary_col = f"{col}_secondary"
        
        if primary_col not in self.df.columns:
            self.df[primary_col] = pd.Series([None] * len(self.df), dtype=object)
        if secondary_col not in self.df.columns:
            self.df[secondary_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            phones = detect_multi_phone(str(val))
            if len(phones) >= 2:
                self.df.at[idx, primary_col] = phones[0]
                self.df.at[idx, secondary_col] = phones[1]
                changed_indices.append(idx)
            elif len(phones) == 1:
                self.df.at[idx, primary_col] = phones[0]
        
        if changed_indices:
            result.changes_made = len(changed_indices)
            result.details["primary_column"] = primary_col
            result.details["secondary_column"] = secondary_col
        
        return result
    
    def PHONE_03_non_numeric_strip(self, col: str) -> CleaningResult:
        """Remove formatting characters, keep + for country code."""
        result = CleaningResult(column=col, formula_id="PHONE-03")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            cleaned = extract_digits(val_str)
            
            if cleaned != val_str and cleaned:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(cleaned)
                self.df.at[idx, col] = cleaned
        
        if changed_indices:
            self._log("PHONE-03", col, "Formatting characters removed",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def PHONE_04_country_code_handling(self, col: str, default_country: str = "US") -> CleaningResult:
        """Detect and standardize country codes."""
        result = CleaningResult(column=col, formula_id="PHONE-04")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            detected = detect_country_from_phone(val_str)
            
            if not detected:
                # Add default country code if missing
                formatted = format_e164(val_str, default_country)
                if formatted != val_str:
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(formatted)
                    self.df.at[idx, col] = formatted
        
        if changed_indices:
            self._log("PHONE-04", col, "Country code standardized",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def PHONE_05_length_validation(self, col: str) -> CleaningResult:
        """Validate phone number length per country."""
        result = CleaningResult(column=col, formula_id="PHONE-05", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            country = detect_country_from_phone(val_str)
            
            if not validate_phone_length(val_str, country):
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "PHONE-05", col,
                "Phone numbers with invalid length detected",
                flagged_indices,
                "Verify phone number digits",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def PHONE_06_duplicate_alert(self, col: str) -> CleaningResult:
        """Flag same phone number on different entity records."""
        result = CleaningResult(column=col, formula_id="PHONE-06", was_auto_applied=False)
        
        # Find ID column if exists
        id_cols = [c for c, h in self.htype_map.items() if h == "HTYPE-003"]
        
        if not id_cols:
            # Without ID column, just find duplicate phones
            phone_counts = self.df[col].dropna().value_counts()
            dups = phone_counts[phone_counts > 1].index.tolist()
            
            flagged_indices = self.df[self.df[col].isin(dups)].index.tolist()
        else:
            # Find same phone across different entities
            id_col = id_cols[0]
            flagged_indices = []
            
            phone_to_ids = {}
            for idx, row in self.df.iterrows():
                phone = row.get(col)
                entity_id = row.get(id_col)
                
                if pd.isna(phone) or pd.isna(entity_id):
                    continue
                
                phone_str = str(phone)
                if phone_str not in phone_to_ids:
                    phone_to_ids[phone_str] = set()
                phone_to_ids[phone_str].add(entity_id)
            
            for phone, ids in phone_to_ids.items():
                if len(ids) > 1:
                    mask = self.df[col].astype(str) == phone
                    flagged_indices.extend(self.df[mask].index.tolist())
        
        if flagged_indices:
            self._flag(
                "PHONE-06", col,
                "Duplicate phone numbers detected across different records",
                flagged_indices,
                "Review for data errors",
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def PHONE_07_placeholder_rejection(self, col: str) -> CleaningResult:
        """Convert placeholder phone numbers to null."""
        result = CleaningResult(column=col, formula_id="PHONE-07")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if is_phone_placeholder(val):
                changed_indices.append(idx)
                before_vals.append(val)
                self.df.at[idx, col] = None
        
        if changed_indices:
            self._log("PHONE-07", col, "Placeholder phone removed",
                     changed_indices, before_vals, [None] * len(changed_indices))
            result.changes_made = len(changed_indices)
        
        return result
    
    def PHONE_08_extension_separation(self, col: str) -> CleaningResult:
        """Separate phone extensions into new column."""
        result = CleaningResult(column=col, formula_id="PHONE-08")
        
        ext_col = f"{col}_extension"
        if ext_col not in self.df.columns:
            self.df[ext_col] = pd.Series([None] * len(self.df), dtype=object)
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            phone, ext = extract_extension(str(val))
            if ext:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(phone)
                self.df.at[idx, col] = phone
                self.df.at[idx, ext_col] = ext
        
        if changed_indices:
            self._log("PHONE-08", col, "Extension separated",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
            result.details["extension_column"] = ext_col
        
        return result
    
    def PHONE_09_format_standardization(self, col: str, format_type: str = "e164") -> CleaningResult:
        """Standardize phone format (E.164 or other)."""
        result = CleaningResult(column=col, formula_id="PHONE-09")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            country = detect_country_from_phone(val_str) or "US"
            
            if format_type == "e164":
                formatted = format_e164(val_str, country)
            else:
                formatted = extract_digits(val_str)
            
            if formatted != val_str:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(formatted)
                self.df.at[idx, col] = formatted
        
        if changed_indices:
            self._log("PHONE-09", col, f"Format standardized ({format_type})",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def PHONE_10_missing_handling(self, col: str) -> CleaningResult:
        """Flag missing phone numbers."""
        result = CleaningResult(column=col, formula_id="PHONE-10", was_auto_applied=False)
        
        null_mask = self.df[col].isna() | (self.df[col].astype(str).str.strip() == '')
        null_indices = self.df[null_mask].index.tolist()
        
        if null_indices:
            self._flag(
                "PHONE-10", col,
                "Missing phone numbers detected",
                null_indices,
                "Cannot predict phone numbers — requires user input",
            )
            result.rows_flagged = len(null_indices)
        
        return result
    
    def PHONE_11_landline_mobile_tag(self, col: str) -> CleaningResult:
        """Tag numbers as Landline or Mobile where detectable."""
        result = CleaningResult(column=col, formula_id="PHONE-11")
        
        tag_col = f"{col}_type"
        if tag_col not in self.df.columns:
            self.df[tag_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_count = 0
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            country = detect_country_from_phone(val_str)
            is_mobile = is_mobile_number(val_str, country)
            
            if is_mobile is True:
                self.df.at[idx, tag_col] = "Mobile"
                changed_count += 1
            elif is_mobile is False:
                self.df.at[idx, tag_col] = "Landline"
                changed_count += 1
        
        if changed_count > 0:
            result.changes_made = changed_count
            result.details["type_column"] = tag_col
        
        return result
    
    # ========================================================================
    # EMAIL FORMULAS — HTYPE-010
    # ========================================================================
    
    def EMAIL_01_lowercase_normalization(self, col: str) -> CleaningResult:
        """Convert emails to lowercase."""
        result = CleaningResult(column=col, formula_id="EMAIL-01")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            lowered = val_str.lower()
            
            if lowered != val_str:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(lowered)
                self.df.at[idx, col] = lowered
        
        if changed_indices:
            self._log("EMAIL-01", col, "Lowercase normalization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def EMAIL_02_format_validation(self, col: str) -> CleaningResult:
        """Validate email format and flag invalid."""
        result = CleaningResult(column=col, formula_id="EMAIL-02", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if not validate_email_format(val):
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "EMAIL-02", col,
                "Invalid email format detected",
                flagged_indices,
                "Correct email addresses",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def EMAIL_03_domain_validation(self, col: str) -> CleaningResult:
        """Validate domain has proper TLD."""
        result = CleaningResult(column=col, formula_id="EMAIL-03", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            if '@' in val_str:
                domain = val_str.split('@')[-1]
                if '.' in domain:
                    tld = domain.split('.')[-1]
                    if len(tld) < 2:
                        flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "EMAIL-03", col,
                "Email domains with invalid TLD detected",
                flagged_indices,
                "Fix domain/TLD",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def EMAIL_04_duplicate_detection(self, col: str) -> CleaningResult:
        """Flag duplicate email addresses."""
        result = CleaningResult(column=col, formula_id="EMAIL-04", was_auto_applied=False)
        
        email_counts = self.df[col].dropna().str.lower().value_counts()
        dups = email_counts[email_counts > 1].index.tolist()
        
        flagged_indices = self.df[self.df[col].str.lower().isin(dups)].index.tolist()
        
        if flagged_indices:
            self._flag(
                "EMAIL-04", col,
                "Duplicate email addresses detected",
                flagged_indices,
                "Review for data errors",
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def EMAIL_05_disposable_detection(self, col: str) -> CleaningResult:
        """Flag disposable email domains."""
        result = CleaningResult(column=col, formula_id="EMAIL-05", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if is_disposable_email(str(val)):
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "EMAIL-05", col,
                "Disposable/temporary email domains detected",
                flagged_indices,
                "Consider requesting permanent email",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def EMAIL_06_whitespace_removal(self, col: str) -> CleaningResult:
        """Remove whitespace from within emails."""
        result = CleaningResult(column=col, formula_id="EMAIL-06")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            cleaned = re.sub(r'\s+', '', val_str)
            
            if cleaned != val_str:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(cleaned)
                self.df.at[idx, col] = cleaned
        
        if changed_indices:
            self._log("EMAIL-06", col, "Whitespace removed",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def EMAIL_07_placeholder_rejection(self, col: str) -> CleaningResult:
        """Convert placeholder emails to null."""
        result = CleaningResult(column=col, formula_id="EMAIL-07")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if is_email_placeholder(val):
                changed_indices.append(idx)
                before_vals.append(val)
                self.df.at[idx, col] = None
        
        if changed_indices:
            self._log("EMAIL-07", col, "Placeholder email removed",
                     changed_indices, before_vals, [None] * len(changed_indices))
            result.changes_made = len(changed_indices)
        
        return result
    
    def EMAIL_08_missing_handling(self, col: str) -> CleaningResult:
        """Flag missing emails."""
        result = CleaningResult(column=col, formula_id="EMAIL-08", was_auto_applied=False)
        
        null_mask = self.df[col].isna() | (self.df[col].astype(str).str.strip() == '')
        null_indices = self.df[null_mask].index.tolist()
        
        if null_indices:
            self._flag(
                "EMAIL-08", col,
                "Missing email addresses",
                null_indices,
                "Cannot predict email — requires user input",
            )
            result.rows_flagged = len(null_indices)
        
        return result
    
    def EMAIL_09_multiple_split(self, col: str) -> CleaningResult:
        """Split multiple emails into separate rows/columns."""
        result = CleaningResult(column=col, formula_id="EMAIL-09")
        
        secondary_col = f"{col}_secondary"
        if secondary_col not in self.df.columns:
            self.df[secondary_col] = pd.Series([None] * len(self.df), dtype=object)
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            emails = split_multiple_emails(str(val))
            if len(emails) >= 2:
                self.df.at[idx, col] = emails[0]
                self.df.at[idx, secondary_col] = emails[1]
                changed_indices.append(idx)
        
        if changed_indices:
            result.changes_made = len(changed_indices)
            result.details["secondary_column"] = secondary_col
        
        return result
    
    def EMAIL_10_typo_domain_fix(self, col: str) -> CleaningResult:
        """Fix common domain typos (with flagging)."""
        result = CleaningResult(column=col, formula_id="EMAIL-10", was_auto_applied=False)
        
        self.df[col] = self.df[col].astype(object)
        
        flagged_indices = []
        suggestions = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            fixed, original_domain = fix_email_domain_typo(str(val))
            if original_domain:
                flagged_indices.append(idx)
                suggestions.append({"original": val, "suggested": fixed})
        
        if flagged_indices:
            self._flag(
                "EMAIL-10", col,
                "Common domain typos detected",
                flagged_indices,
                "Confirm domain corrections",
                {"suggestions": suggestions[:10]}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    # ========================================================================
    # ADDRESS FORMULAS — HTYPE-011
    # ========================================================================
    
    def ADDR_01_whitespace_cleanup(self, col: str) -> CleaningResult:
        """Normalize whitespace and remove line breaks."""
        result = CleaningResult(column=col, formula_id="ADDR-01")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            cleaned = normalize_address_whitespace(val)
            if cleaned != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(cleaned)
                self.df.at[idx, col] = cleaned
        
        if changed_indices:
            self._log("ADDR-01", col, "Whitespace normalized",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def ADDR_02_abbreviation_standardization(self, col: str) -> CleaningResult:
        """Expand common address abbreviations."""
        result = CleaningResult(column=col, formula_id="ADDR-02")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            expanded = expand_address_abbreviations(str(val))
            if expanded != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(expanded)
                self.df.at[idx, col] = expanded
        
        if changed_indices:
            self._log("ADDR-02", col, "Abbreviations expanded",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def ADDR_03_component_separation(self, col: str) -> CleaningResult:
        """Attempt to separate address components."""
        result = CleaningResult(column=col, formula_id="ADDR-03", was_auto_applied=False)
        
        # This is a complex operation that often requires AI/geocoding
        # For now, flag columns where this might be beneficial
        
        has_complex_addresses = False
        sample_addresses = []
        
        for val in self.df[col].dropna().head(10):
            val_str = str(val)
            # Complex if contains commas or multiple parts
            if ',' in val_str or len(val_str.split()) > 5:
                has_complex_addresses = True
                sample_addresses.append(val_str[:100])
        
        if has_complex_addresses:
            self._flag(
                "ADDR-03", col,
                "Complex addresses may benefit from component separation",
                [],
                "Consider splitting into house_number, street, city, postal_code",
                {"sample_addresses": sample_addresses}
            )
            result.rows_flagged = 1  # Dataset-level flag
        
        return result
    
    def ADDR_04_placeholder_rejection(self, col: str) -> CleaningResult:
        """Convert placeholder addresses to null."""
        result = CleaningResult(column=col, formula_id="ADDR-04")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if is_address_placeholder(val):
                changed_indices.append(idx)
                before_vals.append(val)
                self.df.at[idx, col] = None
        
        if changed_indices:
            self._log("ADDR-04", col, "Placeholder address removed",
                     changed_indices, before_vals, [None] * len(changed_indices))
            result.changes_made = len(changed_indices)
        
        return result
    
    def ADDR_05_case_normalization(self, col: str) -> CleaningResult:
        """Apply title case to addresses."""
        result = CleaningResult(column=col, formula_id="ADDR-05")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            titled = title_case_address(val)
            if titled != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(titled)
                self.df.at[idx, col] = titled
        
        if changed_indices:
            self._log("ADDR-05", col, "Case normalized",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def ADDR_06_null_handling(self, col: str) -> CleaningResult:
        """Flag null addresses."""
        result = CleaningResult(column=col, formula_id="ADDR-06", was_auto_applied=False)
        
        null_mask = self.df[col].isna() | (self.df[col].astype(str).str.strip() == '')
        null_indices = self.df[null_mask].index.tolist()
        
        if null_indices:
            self._flag(
                "ADDR-06", col,
                "Missing addresses",
                null_indices,
                "Cannot predict address — requires user input",
            )
            result.rows_flagged = len(null_indices)
        
        return result
    
    def ADDR_07_po_box_detection(self, col: str) -> CleaningResult:
        """Detect and flag PO Box addresses."""
        result = CleaningResult(column=col, formula_id="ADDR-07", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if has_po_box(str(val)):
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "ADDR-07", col,
                "PO Box addresses detected",
                flagged_indices,
                "Consider handling separately from physical addresses",
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    # ========================================================================
    # CITY FORMULAS — HTYPE-012
    # ========================================================================
    
    def CITY_01_title_case(self, col: str) -> CleaningResult:
        """Apply title case to city names."""
        result = CleaningResult(column=col, formula_id="CITY-01")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            titled = str(val).strip().title()
            if titled != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(titled)
                self.df.at[idx, col] = titled
        
        if changed_indices:
            self._log("CITY-01", col, "Title case applied",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def CITY_02_spelling_correction(self, col: str) -> CleaningResult:
        """Fuzzy match city names for spelling correction."""
        result = CleaningResult(column=col, formula_id="CITY-02", was_auto_applied=False)
        
        # This would need a reference list of cities
        # For now, flag potential typos based on uniqueness
        
        city_counts = self.df[col].dropna().str.lower().value_counts()
        rare_cities = city_counts[city_counts == 1].index.tolist()
        
        flagged_indices = []
        for rare in rare_cities:
            # Check if similar to a common city
            for common in city_counts[city_counts > 1].index:
                if levenshtein_distance(rare, common) <= 2 and rare != common:
                    mask = self.df[col].str.lower() == rare
                    flagged_indices.extend(self.df[mask].index.tolist())
                    break
        
        if flagged_indices:
            self._flag(
                "CITY-02", col,
                "Possible city name spelling errors",
                flagged_indices,
                "Verify city names",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def CITY_03_abbreviation_expansion(self, col: str) -> CleaningResult:
        """Expand city abbreviations."""
        result = CleaningResult(column=col, formula_id="CITY-03")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            expanded = normalize_city(val)
            if expanded != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(expanded)
                self.df.at[idx, col] = expanded
        
        if changed_indices:
            self._log("CITY-03", col, "City abbreviation expanded",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def CITY_04_country_consistency(self, col: str) -> CleaningResult:
        """Check city-country consistency."""
        result = CleaningResult(column=col, formula_id="CITY-04", was_auto_applied=False)
        
        # Find country column
        country_cols = [c for c, h in self.htype_map.items() if h == "HTYPE-013"]
        
        if not country_cols:
            return result
        
        # This would need a city-country reference database
        # For now, just note that validation is available
        result.details["country_column_found"] = country_cols[0]
        result.details["validation_available"] = False
        
        return result
    
    def CITY_05_variant_normalization(self, col: str) -> CleaningResult:
        """Normalize city name variants to canonical form."""
        result = CleaningResult(column=col, formula_id="CITY-05")
        
        self.df[col] = self.df[col].astype(object)
        
        # Build variant map
        city_values = self.df[col].dropna().str.lower().unique()
        variant_map = {}
        
        for city in city_values:
            normalized = normalize_city(city)
            if normalized.lower() != city:
                variant_map[city] = normalized
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_lower = str(val).lower()
            if val_lower in variant_map:
                new_val = variant_map[val_lower]
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(new_val)
                self.df.at[idx, col] = new_val
        
        if changed_indices:
            self._log("CITY-05", col, "City variant normalized",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def CITY_06_extraction_from_address(self, col: str) -> CleaningResult:
        """Extract city from address column if city is null."""
        result = CleaningResult(column=col, formula_id="CITY-06", was_auto_applied=False)
        
        # Find address column
        addr_cols = [c for c, h in self.htype_map.items() if h == "HTYPE-011"]
        
        if not addr_cols:
            return result
        
        # Count rows where city is null but address exists
        null_city_mask = self.df[col].isna() | (self.df[col].astype(str).str.strip() == '')
        has_address_mask = self.df[addr_cols[0]].notna()
        
        extractable = self.df[null_city_mask & has_address_mask].index.tolist()
        
        if extractable:
            self._flag(
                "CITY-06", col,
                "City could potentially be extracted from address",
                extractable,
                "Consider extracting city from address column",
                {"address_column": addr_cols[0]}
            )
            result.rows_flagged = len(extractable)
        
        return result
    
    # ========================================================================
    # COUNTRY FORMULAS — HTYPE-013
    # ========================================================================
    
    def CNTRY_01_iso_normalization(self, col: str, output_format: str = "name") -> CleaningResult:
        """Convert between ISO-2, ISO-3, and full name."""
        result = CleaningResult(column=col, formula_id="CNTRY-01")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            iso2 = normalize_country(val)
            if iso2:
                if output_format == "name":
                    new_val = get_country_name(iso2)
                elif output_format == "iso2":
                    new_val = iso2
                elif output_format == "iso3":
                    new_val = ISO_COUNTRIES.get(iso2, (None, None))[0]
                else:
                    new_val = get_country_name(iso2)
                
                if new_val and str(new_val) != str(val):
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(new_val)
                    self.df.at[idx, col] = new_val
        
        if changed_indices:
            self._log("CNTRY-01", col, f"Country normalized ({output_format})",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def CNTRY_02_spelling_correction(self, col: str) -> CleaningResult:
        """Fuzzy match country names."""
        result = CleaningResult(column=col, formula_id="CNTRY-02", was_auto_applied=False)
        
        flagged_indices = []
        suggestions = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            # Check if exact match fails but fuzzy succeeds
            exact = normalize_country(val)
            if not exact:
                fuzzy = fuzzy_match_country(val, threshold=2)
                if fuzzy:
                    flagged_indices.append(idx)
                    suggestions.append({
                        "original": str(val),
                        "suggested": get_country_name(fuzzy)
                    })
        
        if flagged_indices:
            self._flag(
                "CNTRY-02", col,
                "Possible country spelling errors",
                flagged_indices,
                "Confirm country corrections",
                {"suggestions": suggestions[:10]}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def CNTRY_03_abbreviation_mapping(self, col: str) -> CleaningResult:
        """Map country abbreviations to canonical form."""
        result = CleaningResult(column=col, formula_id="CNTRY-03")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_lower = str(val).lower().strip()
            if val_lower in COUNTRY_VARIANTS:
                iso2 = COUNTRY_VARIANTS[val_lower]
                full_name = get_country_name(iso2)
                if full_name:
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(full_name)
                    self.df.at[idx, col] = full_name
        
        if changed_indices:
            self._log("CNTRY-03", col, "Country abbreviation mapped",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def CNTRY_04_title_case(self, col: str) -> CleaningResult:
        """Apply title case to country names."""
        result = CleaningResult(column=col, formula_id="CNTRY-04")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            titled = str(val).strip().title()
            if titled != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(titled)
                self.df.at[idx, col] = titled
        
        if changed_indices:
            self._log("CNTRY-04", col, "Title case applied",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def CNTRY_05_invalid_rejection(self, col: str) -> CleaningResult:
        """Flag invalid country values."""
        result = CleaningResult(column=col, formula_id="CNTRY-05", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if not normalize_country(val) and not fuzzy_match_country(val, 2):
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "CNTRY-05", col,
                "Invalid/unrecognized country values",
                flagged_indices,
                "Correct or remove invalid countries",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def CNTRY_06_default_inference(self, col: str) -> CleaningResult:
        """Suggest filling missing with dominant country."""
        result = CleaningResult(column=col, formula_id="CNTRY-06", was_auto_applied=False)
        
        # Count country occurrences
        country_counts = self.df[col].dropna().value_counts()
        if len(country_counts) == 0:
            return result
        
        total = country_counts.sum()
        top_country = country_counts.index[0]
        top_pct = country_counts.iloc[0] / total * 100
        
        null_count = self.df[col].isna().sum()
        
        if top_pct >= 80 and null_count > 0:
            self._flag(
                "CNTRY-06", col,
                f"≥80% of records are '{top_country}' — consider filling missing",
                self.df[self.df[col].isna()].index.tolist(),
                f"Suggest filling {null_count} missing values with '{top_country}'",
                {"dominant_country": top_country, "percentage": round(top_pct, 1)}
            )
            result.rows_flagged = null_count
        
        return result
    
    # ========================================================================
    # POSTAL CODE FORMULAS — HTYPE-014
    # ========================================================================
    
    def POST_01_leading_zero_preservation(self, col: str) -> CleaningResult:
        """Ensure postal codes preserve leading zeros."""
        result = CleaningResult(column=col, formula_id="POST-01")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            preserved = preserve_leading_zeros(val)
            if preserved != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(preserved)
                self.df.at[idx, col] = preserved
        
        if changed_indices:
            self._log("POST-01", col, "Leading zeros preserved",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def POST_02_format_validation(self, col: str, country: Optional[str] = None) -> CleaningResult:
        """Validate postal code format per country."""
        result = CleaningResult(column=col, formula_id="POST-02", was_auto_applied=False)
        
        # Try to detect country from country column
        country_cols = [c for c, h in self.htype_map.items() if h == "HTYPE-013"]
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            row_country = country
            if not row_country and country_cols:
                row_country = normalize_country(self.df.at[idx, country_cols[0]])
            
            if not validate_postal_code(val, row_country):
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "POST-02", col,
                "Invalid postal code format detected",
                flagged_indices,
                "Verify postal code format",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def POST_03_hyphen_insertion(self, col: str) -> CleaningResult:
        """Insert hyphen in US ZIP+4 codes."""
        result = CleaningResult(column=col, formula_id="POST-03")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            formatted = format_us_zip(val)
            if formatted != str(val) and '-' in formatted:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(formatted)
                self.df.at[idx, col] = formatted
        
        if changed_indices:
            self._log("POST-03", col, "US ZIP+4 hyphen added",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def POST_04_non_numeric_alert(self, col: str) -> CleaningResult:
        """Flag unexpected non-numeric characters."""
        result = CleaningResult(column=col, formula_id="POST-04", was_auto_applied=False)
        
        flagged_indices = []
        
        # Countries that allow alphanumeric
        alpha_countries = {"GB", "CA", "NL", "IE"}
        country_cols = [c for c, h in self.htype_map.items() if h == "HTYPE-013"]
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            has_alpha = bool(re.search(r'[A-Za-z]', val_str))
            
            if has_alpha:
                # Check if country allows alpha
                row_country = None
                if country_cols:
                    row_country = normalize_country(self.df.at[idx, country_cols[0]])
                
                if row_country not in alpha_countries:
                    flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "POST-04", col,
                "Unexpected alphabetic characters in postal code",
                flagged_indices,
                "Verify postal code format",
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def POST_05_country_city_consistency(self, col: str) -> CleaningResult:
        """Validate postal code against city/country."""
        result = CleaningResult(column=col, formula_id="POST-05", was_auto_applied=False)
        
        # This would need a postal code reference database
        # For now, note the validation is available but not implemented
        result.details["validation_available"] = False
        
        return result
    
    # ========================================================================
    # COORDINATE FORMULAS — HTYPE-035
    # ========================================================================
    
    def GEO_01_range_validation(self, col: str) -> CleaningResult:
        """Validate coordinate range (-90 to 90 for lat, -180 to 180 for lng)."""
        result = CleaningResult(column=col, formula_id="GEO-01", was_auto_applied=False)
        
        # Determine if lat or lng from column name
        col_lower = col.lower()
        is_lat = any(x in col_lower for x in ['lat', 'latitude'])
        is_lng = any(x in col_lower for x in ['lng', 'lon', 'longitude'])
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                coord = float(val)
                if is_lat and not validate_latitude(coord):
                    flagged_indices.append(idx)
                elif is_lng and not validate_longitude(coord):
                    flagged_indices.append(idx)
                elif not is_lat and not is_lng:
                    # Unknown type — flag if out of both ranges
                    if not validate_latitude(coord) and not validate_longitude(coord):
                        flagged_indices.append(idx)
            except (ValueError, TypeError):
                flagged_indices.append(idx)
        
        if flagged_indices:
            coord_type = "Latitude" if is_lat else ("Longitude" if is_lng else "Coordinate")
            self._flag(
                "GEO-01", col,
                f"Out-of-range {coord_type} values",
                flagged_indices,
                "Verify coordinate values",
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def GEO_02_dms_to_decimal(self, col: str) -> CleaningResult:
        """Convert DMS format to decimal degrees."""
        result = CleaningResult(column=col, formula_id="GEO-02")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            # Check if contains DMS indicators
            if any(c in val_str for c in ['°', '′', '″', "'"]):
                decimal = parse_dms_to_decimal(val_str)
                if decimal is not None:
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(decimal)
                    self.df.at[idx, col] = decimal
        
        if changed_indices:
            self._log("GEO-02", col, "DMS converted to decimal",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def GEO_03_coordinate_pair_validation(self, col: str) -> CleaningResult:
        """Flag implausible locations (e.g., ocean for land-based data)."""
        result = CleaningResult(column=col, formula_id="GEO-03", was_auto_applied=False)
        
        # This would need a geographic reference (land/water boundaries)
        # For now, note validation is available
        result.details["validation_available"] = False
        
        return result
    
    def GEO_04_precision_normalization(self, col: str, decimals: int = 6) -> CleaningResult:
        """Standardize coordinate precision."""
        result = CleaningResult(column=col, formula_id="GEO-04")
        
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                original = float(val)
                normalized = normalize_coordinate_precision(original, decimals)
                
                if str(normalized) != str(val):
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(normalized)
                    self.df.at[idx, col] = normalized
            except (ValueError, TypeError):
                pass
        
        if changed_indices:
            self._log("GEO-04", col, f"Precision normalized to {decimals} decimals",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def GEO_05_null_handling(self, col: str) -> CleaningResult:
        """Flag null coordinates."""
        result = CleaningResult(column=col, formula_id="GEO-05", was_auto_applied=False)
        
        null_mask = self.df[col].isna()
        null_indices = self.df[null_mask].index.tolist()
        
        if null_indices:
            self._flag(
                "GEO-05", col,
                "Missing coordinate values",
                null_indices,
                "Cannot predict coordinates — requires geocoding or user input",
            )
            result.rows_flagged = len(null_indices)
        
        return result
    
    def GEO_06_lat_lng_swap_detection(self, col: str) -> CleaningResult:
        """Detect possible lat/lng column swap."""
        result = CleaningResult(column=col, formula_id="GEO-06", was_auto_applied=False)
        
        col_lower = col.lower()
        is_lat = any(x in col_lower for x in ['lat', 'latitude'])
        is_lng = any(x in col_lower for x in ['lng', 'lon', 'longitude'])
        
        if not (is_lat or is_lng):
            return result
        
        # Find the complementary column
        other_type = "lng" if is_lat else "lat"
        other_cols = [c for c in self.df.columns if any(
            x in c.lower() for x in (['lng', 'lon', 'longitude'] if is_lat else ['lat', 'latitude'])
        )]
        
        if not other_cols:
            return result
        
        other_col = other_cols[0]
        swap_detected_indices = []
        
        for idx in self.df.index:
            lat_val = self.df.at[idx, col if is_lat else other_col]
            lng_val = self.df.at[idx, other_col if is_lat else col]
            
            if pd.notna(lat_val) and pd.notna(lng_val):
                if detect_lat_lng_swap(lat_val, lng_val):
                    swap_detected_indices.append(idx)
        
        if swap_detected_indices:
            self._flag(
                "GEO-06", col,
                "Possible latitude/longitude column swap detected",
                swap_detected_indices,
                f"Verify that '{col}' and '{other_col}' are not swapped",
            )
            result.rows_flagged = len(swap_detected_indices)
        
        return result
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_for_column(self, col: str, htype: str) -> List[CleaningResult]:
        """Run all applicable formulas for a column based on its HTYPE."""
        results = []
        
        if htype == "HTYPE-009":  # Phone
            results.append(self.PHONE_07_placeholder_rejection(col))
            results.append(self.PHONE_08_extension_separation(col))
            results.append(self.PHONE_03_non_numeric_strip(col))
            results.append(self.PHONE_09_format_standardization(col))
            results.append(self.PHONE_11_landline_mobile_tag(col))
            # Ask-first
            results.append(self.PHONE_01_dataset_level_scan(col))
            results.append(self.PHONE_05_length_validation(col))
            results.append(self.PHONE_06_duplicate_alert(col))
            results.append(self.PHONE_10_missing_handling(col))
        
        elif htype == "HTYPE-010":  # Email
            results.append(self.EMAIL_06_whitespace_removal(col))
            results.append(self.EMAIL_07_placeholder_rejection(col))
            results.append(self.EMAIL_01_lowercase_normalization(col))
            results.append(self.EMAIL_09_multiple_split(col))
            # Ask-first
            results.append(self.EMAIL_02_format_validation(col))
            results.append(self.EMAIL_03_domain_validation(col))
            results.append(self.EMAIL_04_duplicate_detection(col))
            results.append(self.EMAIL_05_disposable_detection(col))
            results.append(self.EMAIL_08_missing_handling(col))
            results.append(self.EMAIL_10_typo_domain_fix(col))
        
        elif htype == "HTYPE-011":  # Address
            results.append(self.ADDR_04_placeholder_rejection(col))
            results.append(self.ADDR_01_whitespace_cleanup(col))
            results.append(self.ADDR_02_abbreviation_standardization(col))
            results.append(self.ADDR_05_case_normalization(col))
            # Ask-first
            results.append(self.ADDR_03_component_separation(col))
            results.append(self.ADDR_06_null_handling(col))
            results.append(self.ADDR_07_po_box_detection(col))
        
        elif htype == "HTYPE-012":  # City
            results.append(self.CITY_03_abbreviation_expansion(col))
            results.append(self.CITY_01_title_case(col))
            results.append(self.CITY_05_variant_normalization(col))
            # Ask-first
            results.append(self.CITY_02_spelling_correction(col))
            results.append(self.CITY_04_country_consistency(col))
            results.append(self.CITY_06_extraction_from_address(col))
        
        elif htype == "HTYPE-013":  # Country
            results.append(self.CNTRY_03_abbreviation_mapping(col))
            results.append(self.CNTRY_01_iso_normalization(col))
            results.append(self.CNTRY_04_title_case(col))
            # Ask-first
            results.append(self.CNTRY_02_spelling_correction(col))
            results.append(self.CNTRY_05_invalid_rejection(col))
            results.append(self.CNTRY_06_default_inference(col))
        
        elif htype == "HTYPE-014":  # Postal Code
            results.append(self.POST_01_leading_zero_preservation(col))
            results.append(self.POST_03_hyphen_insertion(col))
            # Ask-first
            results.append(self.POST_02_format_validation(col))
            results.append(self.POST_04_non_numeric_alert(col))
            results.append(self.POST_05_country_city_consistency(col))
        
        elif htype == "HTYPE-035":  # Coordinates
            results.append(self.GEO_02_dms_to_decimal(col))
            results.append(self.GEO_04_precision_normalization(col))
            # Ask-first
            results.append(self.GEO_01_range_validation(col))
            results.append(self.GEO_03_coordinate_pair_validation(col))
            results.append(self.GEO_05_null_handling(col))
            results.append(self.GEO_06_lat_lng_swap_detection(col))
        
        return results
    
    def run_all(self) -> Dict[str, Any]:
        """Run all contact/location rules for applicable columns."""
        all_results = []
        columns_processed = 0
        
        applicable_htypes = {
            "HTYPE-009", "HTYPE-010", "HTYPE-011", "HTYPE-012",
            "HTYPE-013", "HTYPE-014", "HTYPE-035"
        }
        
        for col, htype in self.htype_map.items():
            if htype in applicable_htypes and col in self.df.columns:
                col_results = self.run_for_column(col, htype)
                all_results.extend(col_results)
                columns_processed += 1
        
        # Commit logs
        try:
            self.db.flush()
        except Exception:
            pass
        
        total_changes = sum(r.changes_made for r in all_results)
        total_flagged = sum(r.rows_flagged for r in all_results)
        
        return {
            "columns_processed": columns_processed,
            "total_changes": total_changes,
            "total_flagged": total_flagged,
            "total_flags": len(self.flags),
            "formulas_applied": [r.formula_id for r in all_results if r.changes_made > 0 or r.rows_flagged > 0],
            "flags": self.flags,
        }
