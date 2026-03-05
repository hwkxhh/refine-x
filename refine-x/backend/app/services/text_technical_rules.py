"""
Text & Technical Data Cleaning Rules — Session 10

Implements formulas from the Formula Rulebook for:
- HTYPE-022: Text / Notes / Description (TEXT-01 to TEXT-09)
- HTYPE-023: URL / Website (URL-01 to URL-05)
- HTYPE-036: IP Address (IP-01 to IP-05)
- HTYPE-037: File Name / File Path (FILE-01 to FILE-04)

Logic First. AI Never.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import Counter
import ipaddress

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
# TEXT CONSTANTS
# ============================================================================

# Placeholder patterns that should be treated as null
TEXT_PLACEHOLDERS = {
    "n/a", "na", "n.a.", "n.a", "none", "nil", "null", "---", "--", "-",
    ".", "..", "...", "not available", "not applicable", "not specified",
    "unknown", "tbd", "tba", "pending", "empty", "blank", "(blank)",
    "[blank]", "(empty)", "[empty]", "no data", "no info", "missing",
}

# Common encoding artifact replacements (byte-based patterns)
ENCODING_REPLACEMENTS = [
    (b"\xe2\x80\x99".decode('utf-8', errors='ignore'), "'"),   # Right single quote
    (b"\xe2\x80\x9c".decode('utf-8', errors='ignore'), '"'),   # Left double quote
    (b"\xe2\x80\x9d".decode('utf-8', errors='ignore'), '"'),   # Right double quote
    (b"\xe2\x80\x93".decode('utf-8', errors='ignore'), '-'),   # En dash
    (b"\xe2\x80\x94".decode('utf-8', errors='ignore'), '-'),   # Em dash
    (b"\xe2\x80\xa6".decode('utf-8', errors='ignore'), '...'), # Ellipsis
    (b"\xc2\xa0".decode('utf-8', errors='ignore'), ' '),       # Non-breaking space
    (b"\xc3\xa2\xe2\x82\xac\xe2\x84\xa2".decode('utf-8', errors='ignore'), "'"),  # Mojibake apostrophe
    (b"\xc3\xa2\xe2\x82\xac\xc5\x93".decode('utf-8', errors='ignore'), '"'),      # Mojibake left quote
    (b"\xc3\xa2\xe2\x82\xac\xef\xbf\xbd".decode('utf-8', errors='ignore'), '"'),  # Mojibake right quote
]

# HTML tag pattern
HTML_TAG_PATTERN = re.compile(r'<[^>]+>')

# Markdown patterns
MARKDOWN_BOLD_PATTERN = re.compile(r'\*\*([^*]+)\*\*')
MARKDOWN_ITALIC_PATTERN = re.compile(r'\*([^*]+)\*')
MARKDOWN_BOLD_UNDERSCORE = re.compile(r'__([^_]+)__')
MARKDOWN_ITALIC_UNDERSCORE = re.compile(r'_([^_]+)_')
MARKDOWN_LINK_PATTERN = re.compile(r'\[([^\]]+)\]\([^)]+\)')
MARKDOWN_CODE_PATTERN = re.compile(r'`([^`]+)`')

# Maximum text length before flagging
MAX_TEXT_LENGTH = 5000


# ============================================================================
# URL CONSTANTS
# ============================================================================

# Generic placeholder URLs
URL_PLACEHOLDERS = {
    "www.example.com", "example.com", "http://example.com", "https://example.com",
    "http://url.com", "https://url.com", "www.url.com", "url.com",
    "http://www.example.com", "https://www.example.com",
    "http://test.com", "https://test.com", "www.test.com",
    "n/a", "na", "none", "null", "-", "--",
}

# URL validation pattern (basic)
URL_PATTERN = re.compile(
    r'^(https?://)?'  # Optional protocol
    r'([a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}'  # Domain
    r'(:\d{1,5})?'  # Optional port
    r'(/[^\s]*)?$',  # Optional path
    re.IGNORECASE
)

# Protocol pattern
PROTOCOL_PATTERN = re.compile(r'^https?://', re.IGNORECASE)


# ============================================================================
# IP ADDRESS CONSTANTS
# ============================================================================

# Private IP ranges
PRIVATE_IP_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
]

# Loopback addresses
LOOPBACK_IPV4 = '127.0.0.1'
LOOPBACK_IPV6 = '::1'


# ============================================================================
# FILE PATH CONSTANTS
# ============================================================================

# Known file extensions (common ones)
KNOWN_EXTENSIONS = {
    # Documents
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'odt', 'ods', 'odp',
    'txt', 'rtf', 'csv', 'tsv', 'md', 'tex', 'epub',
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'bmp', 'svg', 'ico', 'webp', 'tiff', 'tif',
    'raw', 'psd', 'ai', 'eps', 'heic', 'heif',
    # Audio
    'mp3', 'wav', 'ogg', 'flac', 'aac', 'm4a', 'wma', 'aiff',
    # Video
    'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v', 'mpeg', 'mpg',
    # Archives
    'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'iso',
    # Code
    'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'h', 'cs', 'go',
    'rb', 'php', 'swift', 'kt', 'rs', 'scala', 'r', 'sql', 'sh', 'bat',
    'ps1', 'yml', 'yaml', 'json', 'xml', 'html', 'htm', 'css', 'scss', 'less',
    # Data
    'parquet', 'feather', 'arrow', 'avro', 'db', 'sqlite', 'sqlite3',
    # Executables
    'exe', 'msi', 'dmg', 'app', 'deb', 'rpm', 'apk',
    # Other
    'log', 'bak', 'tmp', 'lock', 'cfg', 'ini', 'conf',
}

# Characters that are problematic in file names
UNSAFE_FILENAME_CHARS = set('<>:"|?*')


# ============================================================================
# HELPER FUNCTIONS — TEXT
# ============================================================================

def normalize_whitespace(value: str) -> str:
    """Normalize whitespace in text: trim and collapse multiple spaces.
    
    Args:
        value: Input string
        
    Returns:
        Normalized string
    """
    if not value:
        return value
    
    # Collapse multiple whitespace to single space
    result = ' '.join(value.split())
    return result


def is_placeholder(value: str) -> bool:
    """Check if value is a placeholder that should be treated as null.
    
    Args:
        value: Input string
        
    Returns:
        True if placeholder
    """
    if not value:
        return False
    
    cleaned = value.strip().lower()
    return cleaned in TEXT_PLACEHOLDERS


def fix_encoding_artifacts(value: str) -> str:
    """Fix common encoding artifacts in text.
    
    Args:
        value: Input string
        
    Returns:
        Fixed string
    """
    if not value:
        return value
    
    result = value
    for old, new in ENCODING_REPLACEMENTS:
        if old in result:
            result = result.replace(old, new)
    
    return result


def strip_html_tags(value: str) -> str:
    """Remove HTML tags from text.
    
    Args:
        value: Input string
        
    Returns:
        Text without HTML tags
    """
    if not value:
        return value
    
    return HTML_TAG_PATTERN.sub('', value)


def strip_markdown(value: str) -> str:
    """Remove markdown formatting from text.
    
    Args:
        value: Input string
        
    Returns:
        Text without markdown
    """
    if not value:
        return value
    
    result = value
    
    # Remove bold (**text** or __text__)
    result = MARKDOWN_BOLD_PATTERN.sub(r'\1', result)
    result = MARKDOWN_BOLD_UNDERSCORE.sub(r'\1', result)
    
    # Remove italic (*text* or _text_)
    result = MARKDOWN_ITALIC_PATTERN.sub(r'\1', result)
    result = MARKDOWN_ITALIC_UNDERSCORE.sub(r'\1', result)
    
    # Remove links [text](url) -> text
    result = MARKDOWN_LINK_PATTERN.sub(r'\1', result)
    
    # Remove inline code `code` -> code
    result = MARKDOWN_CODE_PATTERN.sub(r'\1', result)
    
    return result


def has_html_tags(value: str) -> bool:
    """Check if text contains HTML tags.
    
    Args:
        value: Input string
        
    Returns:
        True if HTML tags present
    """
    if not value:
        return False
    
    return bool(HTML_TAG_PATTERN.search(value))


def has_markdown(value: str) -> bool:
    """Check if text contains markdown formatting.
    
    Args:
        value: Input string
        
    Returns:
        True if markdown present
    """
    if not value:
        return False
    
    return bool(
        MARKDOWN_BOLD_PATTERN.search(value) or
        MARKDOWN_BOLD_UNDERSCORE.search(value) or
        MARKDOWN_ITALIC_PATTERN.search(value) or
        MARKDOWN_ITALIC_UNDERSCORE.search(value) or
        MARKDOWN_LINK_PATTERN.search(value) or
        MARKDOWN_CODE_PATTERN.search(value)
    )


def detect_language(value: str) -> Optional[str]:
    """Simple language detection based on character sets.
    
    Args:
        value: Input string
        
    Returns:
        Language code or None
    """
    if not value or len(value) < 10:
        return None
    
    # Count character types
    latin = 0
    cyrillic = 0
    arabic = 0
    cjk = 0
    devanagari = 0
    
    for char in value:
        code = ord(char)
        if 0x0000 <= code <= 0x007F or 0x0080 <= code <= 0x00FF:
            latin += 1
        elif 0x0400 <= code <= 0x04FF:
            cyrillic += 1
        elif 0x0600 <= code <= 0x06FF:
            arabic += 1
        elif 0x4E00 <= code <= 0x9FFF or 0x3040 <= code <= 0x30FF:
            cjk += 1
        elif 0x0900 <= code <= 0x097F:
            devanagari += 1
    
    total = max(1, latin + cyrillic + arabic + cjk + devanagari)
    
    if cyrillic / total > 0.3:
        return "cyrillic"
    elif arabic / total > 0.3:
        return "arabic"
    elif cjk / total > 0.3:
        return "cjk"
    elif devanagari / total > 0.3:
        return "devanagari"
    elif latin / total > 0.5:
        return "latin"
    
    return None


# ============================================================================
# HELPER FUNCTIONS — URL
# ============================================================================

def normalize_url_protocol(value: str) -> str:
    """Add https:// protocol if missing.
    
    Args:
        value: URL string
        
    Returns:
        URL with protocol
    """
    if not value:
        return value
    
    value = value.strip()
    
    if not PROTOCOL_PATTERN.match(value):
        # Check if it looks like a URL
        if '.' in value and not value.startswith('/'):
            return 'https://' + value
    
    return value


def lowercase_domain(url: str) -> str:
    """Lowercase the domain portion of a URL.
    
    Args:
        url: URL string
        
    Returns:
        URL with lowercased domain
    """
    if not url:
        return url
    
    # Split by protocol
    if '://' in url:
        protocol, rest = url.split('://', 1)
        # Split by path
        if '/' in rest:
            domain, path = rest.split('/', 1)
            return f"{protocol}://{domain.lower()}/{path}"
        else:
            return f"{protocol}://{rest.lower()}"
    else:
        # No protocol
        if '/' in url:
            domain, path = url.split('/', 1)
            return f"{domain.lower()}/{path}"
        else:
            return url.lower()


def is_valid_url(url: str) -> bool:
    """Validate URL format.
    
    Args:
        url: URL string
        
    Returns:
        True if valid format
    """
    if not url:
        return False
    
    return bool(URL_PATTERN.match(url.strip()))


def is_placeholder_url(url: str) -> bool:
    """Check if URL is a generic placeholder.
    
    Args:
        url: URL string
        
    Returns:
        True if placeholder
    """
    if not url:
        return False
    
    cleaned = url.strip().lower()
    
    # Remove protocol for comparison
    cleaned = re.sub(r'^https?://', '', cleaned)
    cleaned = cleaned.rstrip('/')
    
    return cleaned in URL_PLACEHOLDERS or url.strip().lower() in URL_PLACEHOLDERS


# ============================================================================
# HELPER FUNCTIONS — IP ADDRESS
# ============================================================================

def parse_ip_address(value: str) -> Optional[ipaddress.ip_address]:
    """Parse IP address string.
    
    Args:
        value: IP address string
        
    Returns:
        ip_address object or None
    """
    if not value:
        return None
    
    try:
        return ipaddress.ip_address(value.strip())
    except ValueError:
        return None


def is_valid_ip(value: str) -> bool:
    """Validate IP address format.
    
    Args:
        value: IP address string
        
    Returns:
        True if valid
    """
    return parse_ip_address(value) is not None


def is_private_ip(ip: ipaddress.ip_address) -> bool:
    """Check if IP is in private range.
    
    Args:
        ip: IP address object
        
    Returns:
        True if private
    """
    if ip.version == 4:
        for network in PRIVATE_IP_RANGES:
            if ip in network:
                return True
    return ip.is_private


def is_loopback_ip(value: str) -> bool:
    """Check if IP is loopback address.
    
    Args:
        value: IP address string
        
    Returns:
        True if loopback
    """
    cleaned = value.strip()
    
    if cleaned == LOOPBACK_IPV4 or cleaned == LOOPBACK_IPV6:
        return True
    
    ip = parse_ip_address(value)
    if ip:
        return ip.is_loopback
    
    return False


# ============================================================================
# HELPER FUNCTIONS — FILE PATH
# ============================================================================

def get_file_extension(value: str) -> Optional[str]:
    """Extract file extension from filename or path.
    
    Args:
        value: Filename or path
        
    Returns:
        Extension (without dot) or None
    """
    if not value:
        return None
    
    # Get the last part after path separator
    filename = value.replace('\\', '/').split('/')[-1]
    
    if '.' in filename:
        ext = filename.rsplit('.', 1)[-1].lower()
        return ext if ext else None
    
    return None


def is_known_extension(ext: str) -> bool:
    """Check if file extension is known.
    
    Args:
        ext: Extension (without dot)
        
    Returns:
        True if known
    """
    if not ext:
        return False
    
    return ext.lower() in KNOWN_EXTENSIONS


def normalize_path_separator(value: str) -> str:
    """Normalize path separators to forward slash.
    
    Args:
        value: File path
        
    Returns:
        Normalized path
    """
    if not value:
        return value
    
    return value.replace('\\', '/')


def has_unsafe_filename_chars(value: str) -> bool:
    """Check if filename contains unsafe characters.
    
    Args:
        value: Filename or path
        
    Returns:
        True if unsafe characters present
    """
    if not value:
        return False
    
    # Get just the filename
    filename = value.replace('\\', '/').split('/')[-1]
    
    # Check for spaces or special characters
    for char in filename:
        if char in UNSAFE_FILENAME_CHARS:
            return True
    
    # Also flag if filename has spaces
    if ' ' in filename:
        return True
    
    return False


# ============================================================================
# MAIN CLASS
# ============================================================================

class TextTechnicalRules:
    """Text & Technical Data cleaning rules."""
    
    APPLICABLE_HTYPES = {
        "HTYPE-022",  # Text / Notes
        "HTYPE-023",  # URL
        "HTYPE-036",  # IP Address
        "HTYPE-037",  # File Path
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
        self.ip_frequency: Dict[str, Dict[str, int]] = {}
        self.language_stats: Dict[str, Dict[str, int]] = {}
    
    def _ensure_object_dtype(self, col: str):
        """Ensure column has object dtype for mixed type assignment."""
        if col in self.df.columns and self.df[col].dtype in ['string', 'object']:
            self.df[col] = self.df[col].astype(object)

    def _vec_str(self, col: str, func, str_only: bool = True):
        """
        Vectorised helper: apply *func* to non-null (optionally str-only) values,
        batch-assign changed cells.  Returns (new_series, changes_made: int).
        """
        if str_only:
            mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        else:
            mask = self.df[col].notna()
        if not mask.any():
            return self.df[col].copy(), 0
        orig = self.df.loc[mask, col]
        new_vals = orig.apply(func)
        changed = new_vals != orig
        out = self.df[col].copy()
        if changed.any():
            out.loc[new_vals[changed].index] = new_vals[changed]
        return out, int(changed.sum())
    
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
    # TEXT FORMULAS (HTYPE-022: Text / Notes / Description)
    # ========================================================================
    
    def TEXT_01_whitespace_normalization(self, col: str) -> CleaningResult:
        """TEXT-01: Normalize whitespace — trim and collapse."""
        result = CleaningResult(column=col, formula_id="TEXT-01")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            orig = self.df.loc[str_mask, col]
            # ' '.join(v.split()) trims + collapses all internal whitespace
            new_vals = orig.str.split().str.join(' ')
            changed = new_vals != orig
            if changed.any():
                update_idx = changed[changed].index
                self.df.loc[update_idx, col] = new_vals.loc[update_idx]
                result.changes_made = int(changed.sum())
                self.log_cleaning(result)
        return result
    
    def TEXT_02_placeholder_detection(self, col: str) -> CleaningResult:
        """TEXT-02: Detect and convert placeholders to null."""
        result = CleaningResult(column=col, formula_id="TEXT-02")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            lower_vals = self.df.loc[str_mask, col].str.strip().str.lower()
            placeholder_mask = lower_vals.isin(TEXT_PLACEHOLDERS)
            if placeholder_mask.any():
                placeholders_found = Counter(lower_vals[placeholder_mask].tolist())
                update_idx = placeholder_mask[placeholder_mask].index
                self.df.loc[update_idx, col] = None
                result.changes_made = int(placeholder_mask.sum())
                result.details["placeholders_converted"] = dict(placeholders_found)
                self.log_cleaning(result)
        return result
    
    def TEXT_03_encoding_fix(self, col: str) -> CleaningResult:
        """TEXT-03: Fix character encoding artifacts."""
        result = CleaningResult(column=col, formula_id="TEXT-03")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            orig = self.df.loc[str_mask, col].copy()
            new_vals = orig.copy()
            for old, new in ENCODING_REPLACEMENTS:
                if old:
                    new_vals = new_vals.str.replace(old, new, regex=False)
            changed = new_vals != orig
            if changed.any():
                update_idx = changed[changed].index
                self.df.loc[update_idx, col] = new_vals.loc[update_idx]
                result.changes_made = int(changed.sum())
                self.log_cleaning(result)
        return result
    
    def TEXT_04_html_markdown_stripping(self, col: str) -> CleaningResult:
        """TEXT-04: Strip HTML tags and Markdown formatting."""
        result = CleaningResult(column=col, formula_id="TEXT-04")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            orig = self.df.loc[str_mask, col]
            html_mask = orig.apply(has_html_tags)
            md_mask = orig.apply(has_markdown)
            needs_change = html_mask | md_mask
            if needs_change.any():
                def _strip(v):
                    if has_html_tags(v):
                        v = strip_html_tags(v)
                    if has_markdown(v):
                        v = strip_markdown(v)
                    return v
                new_vals = orig[needs_change].apply(_strip)
                changed = new_vals != orig[needs_change]
                if changed.any():
                    update_idx = changed[changed].index
                    self.df.loc[update_idx, col] = new_vals.loc[update_idx]
                    result.changes_made = int(changed.sum())
                    result.details["html_stripped"] = int(html_mask.loc[update_idx].sum())
                    result.details["markdown_stripped"] = int(md_mask.loc[update_idx].sum())
                    self.log_cleaning(result)
        return result
    
    def TEXT_05_long_value_alert(self, col: str) -> CleaningResult:
        """TEXT-05: Flag extremely long text values."""
        result = CleaningResult(column=col, formula_id="TEXT-05")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            str_col = self.df.loc[str_mask, col]
            lengths = str_col.str.len()
            long_mask = lengths > MAX_TEXT_LENGTH
            if long_mask.any():
                long_vals = str_col[long_mask]
                long_lengths = lengths[long_mask]
                long_values = []
                for idx in long_vals.index:
                    v = long_vals.at[idx]
                    ln = int(long_lengths.at[idx])
                    long_values.append({"index": idx, "length": ln})
                    self.add_flag(idx, col, "TEXT-05",
                                 f"Extremely long text ({ln} chars) — possible paste error",
                                 f"{v[:100]}...", severity="warning")
                    result.rows_flagged += 1
                result.details["long_values"] = long_values
                result.was_auto_applied = False
                self.log_cleaning(result)
        return result
    
    def TEXT_06_sentiment_tagging(self, col: str) -> CleaningResult:
        """TEXT-06: Sentiment tagging (placeholder — requires AI).
        
        This is a placeholder. Actual sentiment analysis requires LLM.
        """
        result = CleaningResult(column=col, formula_id="TEXT-06")
        result.details["note"] = "Sentiment tagging requires AI/LLM integration"
        result.was_auto_applied = False
        return result
    
    def TEXT_07_keyword_extraction(self, col: str) -> CleaningResult:
        """TEXT-07: Keyword extraction (placeholder — requires AI).
        
        This is a placeholder. Actual keyword extraction requires LLM.
        """
        result = CleaningResult(column=col, formula_id="TEXT-07")
        result.details["note"] = "Keyword extraction requires AI/LLM integration"
        result.was_auto_applied = False
        return result
    
    def TEXT_08_language_detection(self, col: str) -> CleaningResult:
        """TEXT-08: Detect unexpected languages in text."""
        result = CleaningResult(column=col, formula_id="TEXT-08")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if not str_mask.any():
            return result
        str_col = self.df.loc[str_mask, col]
        langs = str_col.apply(detect_language)
        has_lang = langs.notna()
        if not has_lang.any():
            return result
        language_counts = Counter(langs[has_lang].tolist())
        dominant_lang = language_counts.most_common(1)[0][0]
        self.language_stats[col] = dict(language_counts)
        anomaly_mask = has_lang & (langs != dominant_lang)
        anomalies = []
        for idx in anomaly_mask[anomaly_mask].index:
            lang = langs.at[idx]
            val = str_col.at[idx]
            anomalies.append((idx, lang))
            self.add_flag(idx, col, "TEXT-08",
                         f"Unexpected language ({lang}) in predominantly {dominant_lang} column",
                         str(val)[:100], severity="info")
            result.rows_flagged += 1
        result.details["language_distribution"] = dict(language_counts)
        result.details["anomalies_found"] = len(anomalies)
        if anomalies:
            result.was_auto_applied = False
        self.log_cleaning(result)
        return result
    
    def TEXT_09_leading_apostrophe_removal(self, col: str) -> CleaningResult:
        """TEXT-09: Remove leading apostrophe from Excel-exported text."""
        result = CleaningResult(column=col, formula_id="TEXT-09")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            starts_apos = (
                self.df.loc[str_mask, col].str.startswith("'")
                & (self.df.loc[str_mask, col].str.len() > 1)
            )
            if starts_apos.any():
                update_idx = starts_apos[starts_apos].index
                self.df.loc[update_idx, col] = self.df.loc[update_idx, col].str[1:]
                result.changes_made = int(starts_apos.sum())
                self.log_cleaning(result)
        return result
    
    # ========================================================================
    # URL FORMULAS (HTYPE-023: URL / Website)
    # ========================================================================
    
    def URL_01_protocol_normalization(self, col: str) -> CleaningResult:
        """URL-01: Add https:// protocol if missing."""
        result = CleaningResult(column=col, formula_id="URL-01")
        new_series, n = self._vec_str(col, lambda v: normalize_url_protocol(v.strip()))
        if n:
            self.df[col] = new_series
            result.changes_made = n
            self.log_cleaning(result)
        return result
    
    def URL_02_lowercase_domain(self, col: str) -> CleaningResult:
        """URL-02: Lowercase the domain portion."""
        result = CleaningResult(column=col, formula_id="URL-02")
        new_series, n = self._vec_str(col, lowercase_domain)
        if n:
            self.df[col] = new_series
            result.changes_made = n
            self.log_cleaning(result)
        return result
    
    def URL_03_trailing_slash_standardization(self, col: str) -> CleaningResult:
        """URL-03: Standardize trailing slash presence."""
        result = CleaningResult(column=col, formula_id="URL-03")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if not str_mask.any():
            return result
        # Count with/without slash (no-query URLs only)
        stripped = self.df.loc[str_mask, col].str.strip()
        no_query = ~stripped.str.contains('?', regex=False)
        with_slash = int((no_query & stripped.str.endswith('/')).sum())
        without_slash = int((no_query & ~stripped.str.endswith('/')).sum())
        add_slash = with_slash > without_slash
        # Batch-apply to matching rows
        if add_slash:
            needs_change = no_query & ~stripped.str.endswith('/')
            if needs_change.any():
                update_idx = needs_change[needs_change].index
                self.df.loc[update_idx, col] = stripped.loc[update_idx] + '/'
                result.changes_made = int(needs_change.sum())
        else:
            needs_change = no_query & stripped.str.endswith('/')
            if needs_change.any():
                update_idx = needs_change[needs_change].index
                self.df.loc[update_idx, col] = stripped.loc[update_idx].str.rstrip('/')
                result.changes_made = int(needs_change.sum())
        if result.changes_made > 0:
            result.details["standardized_to"] = "with_slash" if add_slash else "without_slash"
            self.log_cleaning(result)
        return result
    
    def URL_04_format_validation(self, col: str) -> CleaningResult:
        """URL-04: Validate URL format."""
        result = CleaningResult(column=col, formula_id="URL-04")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            str_col = self.df.loc[str_mask, col]
            invalid_mask = ~str_col.apply(is_valid_url)
            if invalid_mask.any():
                invalid_urls = str_col[invalid_mask]
                for idx in invalid_urls.index:
                    val = invalid_urls.at[idx]
                    self.add_flag(idx, col, "URL-04",
                                 "Invalid URL format", val, severity="error")
                    result.rows_flagged += 1
                result.details["invalid_count"] = int(invalid_mask.sum())
                result.was_auto_applied = False
                self.log_cleaning(result)
        return result
    
    def URL_05_placeholder_detection(self, col: str) -> CleaningResult:
        """URL-05: Detect placeholder URLs."""
        result = CleaningResult(column=col, formula_id="URL-05")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            placeholder_mask = self.df.loc[str_mask, col].apply(is_placeholder_url)
            if placeholder_mask.any():
                update_idx = placeholder_mask[placeholder_mask].index
                self.df.loc[update_idx, col] = None
                result.changes_made = int(placeholder_mask.sum())
                self.log_cleaning(result)
        return result
    
    # ========================================================================
    # IP ADDRESS FORMULAS (HTYPE-036: IP Address)
    # ========================================================================
    
    def IP_01_format_validation(self, col: str) -> CleaningResult:
        """IP-01: Validate IPv4/IPv6 format."""
        result = CleaningResult(column=col, formula_id="IP-01")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            str_col = self.df.loc[str_mask, col]
            invalid_mask = ~str_col.apply(is_valid_ip)
            if invalid_mask.any():
                invalid_ips = str_col[invalid_mask]
                for idx in invalid_ips.index:
                    val = invalid_ips.at[idx]
                    self.add_flag(idx, col, "IP-01",
                                 "Invalid IP address format", val, severity="error")
                    result.rows_flagged += 1
                result.details["invalid_count"] = int(invalid_mask.sum())
                result.was_auto_applied = False
                self.log_cleaning(result)
        return result
    
    def IP_02_private_ip_flagging(self, col: str) -> CleaningResult:
        """IP-02: Flag private/internal IP addresses."""
        result = CleaningResult(column=col, formula_id="IP-02")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            str_col = self.df.loc[str_mask, col]
            parsed = str_col.apply(parse_ip_address)
            private_mask = parsed.apply(lambda ip: bool(ip and is_private_ip(ip)))
            if private_mask.any():
                private_vals = str_col[private_mask]
                for idx in private_vals.index:
                    val = private_vals.at[idx]
                    self.add_flag(idx, col, "IP-02",
                                 "Private/internal IP address", val, severity="info")
                    result.rows_flagged += 1
                result.details["private_ip_count"] = int(private_mask.sum())
                result.was_auto_applied = False
                self.log_cleaning(result)
        return result
    
    def IP_03_loopback_detection(self, col: str) -> CleaningResult:
        """IP-03: Detect loopback addresses (127.0.0.1, ::1)."""
        result = CleaningResult(column=col, formula_id="IP-03")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            str_col = self.df.loc[str_mask, col]
            loopback_mask = str_col.apply(is_loopback_ip)
            if loopback_mask.any():
                loopback_vals = str_col[loopback_mask]
                for idx in loopback_vals.index:
                    val = loopback_vals.at[idx]
                    self.add_flag(idx, col, "IP-03",
                                 "Loopback address — likely test data", val, severity="warning")
                    result.rows_flagged += 1
                result.details["loopback_count"] = int(loopback_mask.sum())
                result.was_auto_applied = False
                self.log_cleaning(result)
        return result
    
    def IP_04_duplicate_ip_alert(self, col: str) -> CleaningResult:
        """IP-04: Alert on high-frequency duplicate IPs."""
        result = CleaningResult(column=col, formula_id="IP-04")
        
        # Count IP frequencies
        ip_counts = Counter()
        
        for val in self.df[col].dropna():
            if isinstance(val, str):
                ip_counts[val.strip()] += 1
        
        self.ip_frequency[col] = dict(ip_counts)
        
        # Flag IPs appearing more than threshold times
        total_rows = len(self.df)
        threshold = max(5, total_rows * 0.1)  # 10% or at least 5
        
        high_frequency = {ip: count for ip, count in ip_counts.items() 
                         if count >= threshold}
        
        if high_frequency:
            result.details["high_frequency_ips"] = high_frequency
            result.details["recommendation"] = (
                "High-frequency IPs may indicate proxy, shared network, or data error."
            )
            
            for ip, count in high_frequency.items():
                for idx, val in self.df[col].items():
                    if val == ip:
                        self.add_flag(idx, col, "IP-04",
                                     f"IP appears {count} times — possible proxy or error",
                                     ip, severity="info")
                        result.rows_flagged += 1
                        break  # Only flag once per IP
            
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    def IP_05_null_handling(self, col: str) -> CleaningResult:
        """IP-05: Handle null IP addresses."""
        result = CleaningResult(column=col, formula_id="IP-05")
        
        null_count = self.df[col].isna().sum()
        
        if null_count > 0:
            result.details["null_count"] = int(null_count)
            result.details["recommendation"] = "Mark as 'Not Recorded' or leave null"
            result.rows_flagged = int(null_count)
            result.was_auto_applied = False
            self.log_cleaning(result)
        
        return result
    
    # ========================================================================
    # FILE PATH FORMULAS (HTYPE-037: File Name / File Path)
    # ========================================================================
    
    def FILE_01_extension_validation(self, col: str) -> CleaningResult:
        """FILE-01: Validate file extension is known."""
        result = CleaningResult(column=col, formula_id="FILE-01")
        unknown_extensions: Counter = Counter()
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            str_col = self.df.loc[str_mask, col]
            exts = str_col.apply(get_file_extension)
            unknown_mask = exts.apply(lambda e: bool(e and not is_known_extension(e)))
            if unknown_mask.any():
                for idx in unknown_mask[unknown_mask].index:
                    ext = exts.at[idx]
                    val = str_col.at[idx]
                    unknown_extensions[ext] += 1
                    self.add_flag(idx, col, "FILE-01",
                                 f"Unknown file extension: .{ext}", val, severity="info")
                    result.rows_flagged += 1
                result.details["unknown_extensions"] = dict(unknown_extensions)
                result.was_auto_applied = False
                self.log_cleaning(result)
        return result
    
    def FILE_02_path_separator_normalization(self, col: str) -> CleaningResult:
        """FILE-02: Normalize path separators to forward slash."""
        result = CleaningResult(column=col, formula_id="FILE-02")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            has_backslash = self.df.loc[str_mask, col].str.contains('\\\\', regex=False)
            if has_backslash.any():
                update_idx = has_backslash[has_backslash].index
                self.df.loc[update_idx, col] = (
                    self.df.loc[update_idx, col].str.replace('\\\\', '/', regex=False)
                )
                result.changes_made = int(has_backslash.sum())
                self.log_cleaning(result)
        return result
    
    def FILE_03_special_character_alert(self, col: str) -> CleaningResult:
        """FILE-03: Flag filenames with unsafe characters."""
        result = CleaningResult(column=col, formula_id="FILE-03")
        str_mask = self.df[col].notna() & self.df[col].apply(lambda x: isinstance(x, str))
        if str_mask.any():
            str_col = self.df.loc[str_mask, col]
            unsafe_mask = str_col.apply(has_unsafe_filename_chars)
            if unsafe_mask.any():
                unsafe_vals = str_col[unsafe_mask]
                for idx in unsafe_vals.index:
                    val = unsafe_vals.at[idx]
                    self.add_flag(idx, col, "FILE-03",
                                 "Filename contains spaces or special characters", val,
                                 severity="warning")
                    result.rows_flagged += 1
                result.details["unsafe_count"] = int(unsafe_mask.sum())
                result.was_auto_applied = False
                self.log_cleaning(result)
        return result
    
    def FILE_04_null_handling(self, col: str) -> CleaningResult:
        """FILE-04: Handle null file paths."""
        result = CleaningResult(column=col, formula_id="FILE-04")
        
        null_count = self.df[col].isna().sum()
        
        if null_count > 0:
            result.details["null_count"] = int(null_count)
            result.details["recommendation"] = "Mark as 'No File' or leave null"
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
        
        if htype == "HTYPE-022":  # Text / Notes
            results.append(self.TEXT_01_whitespace_normalization(col))
            results.append(self.TEXT_02_placeholder_detection(col))
            results.append(self.TEXT_03_encoding_fix(col))
            results.append(self.TEXT_04_html_markdown_stripping(col))
            results.append(self.TEXT_05_long_value_alert(col))
            results.append(self.TEXT_08_language_detection(col))
            results.append(self.TEXT_09_leading_apostrophe_removal(col))
            # TEXT-06 and TEXT-07 are AI-only, skip by default
        
        elif htype == "HTYPE-023":  # URL
            results.append(self.URL_05_placeholder_detection(col))
            results.append(self.URL_01_protocol_normalization(col))
            results.append(self.URL_02_lowercase_domain(col))
            results.append(self.URL_03_trailing_slash_standardization(col))
            results.append(self.URL_04_format_validation(col))
        
        elif htype == "HTYPE-036":  # IP Address
            results.append(self.IP_01_format_validation(col))
            results.append(self.IP_02_private_ip_flagging(col))
            results.append(self.IP_03_loopback_detection(col))
            results.append(self.IP_04_duplicate_ip_alert(col))
            results.append(self.IP_05_null_handling(col))
        
        elif htype == "HTYPE-037":  # File Path
            results.append(self.FILE_02_path_separator_normalization(col))
            results.append(self.FILE_01_extension_validation(col))
            results.append(self.FILE_03_special_character_alert(col))
            results.append(self.FILE_04_null_handling(col))
        
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
            "ip_frequency": self.ip_frequency,
            "language_stats": self.language_stats,
        }
