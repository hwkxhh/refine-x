"""
Date & Time Rules — Session 5

Implements formula sets for:
- DATE (15 formulas) — HTYPE-004 Date
- TIME (6 formulas) — HTYPE-005 Time
- DTM (6 formulas) — HTYPE-006 DateTime Combined
- DUR (7 formulas) — HTYPE-033 Duration / Time Elapsed
- FISC (7 formulas) — HTYPE-041 Fiscal Period / Academic Year

These formulas apply to columns classified under the respective HTYPEs
by the HTYPE Detection Engine (Session 3).

V2.0 Core Principle: PERMISSIVE parsing. If a human can read it as a date/time,
the system must parse it — not reject it.
"""

import re
from datetime import datetime, date, time, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set, Union
from dataclasses import dataclass, field
import calendar

import pandas as pd
import numpy as np
from dateutil import parser as dateutil_parser
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session

from app.models.cleaning_log import CleaningLog


# ============================================================================
# DATE FORMAT PATTERNS (Appendix C)
# ============================================================================

# Common date placeholder values that should be treated as missing
DATE_PLACEHOLDERS = {
    "01/01/1900", "1900-01-01", "1/1/1900",
    "00/00/0000", "0000-00-00",
    "01/01/1970", "1970-01-01", "1/1/1970",  # Unix epoch
    "01-01-1900", "01.01.1900",
    "n/a", "na", "n.a.", "none", "null", "unknown", "tbd", "pending",
    "not available", "not applicable", "empty", "---", "--", "-",
}

# Ordinal suffixes for date parsing
ORDINAL_PATTERN = re.compile(r'(\d{1,2})(st|nd|rd|th)', re.IGNORECASE)

# Relative date phrases
RELATIVE_DATE_PATTERNS = {
    "today": 0,
    "yesterday": -1,
    "tomorrow": 1,
}

# Week-based relative patterns
WEEK_PATTERN = re.compile(
    r'(?:last|next|this)\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
    re.IGNORECASE
)
DAYS_AGO_PATTERN = re.compile(r'(\d+)\s+days?\s+ago', re.IGNORECASE)
WEEKS_AGO_PATTERN = re.compile(r'(\d+)\s+weeks?\s+ago', re.IGNORECASE)
MONTHS_AGO_PATTERN = re.compile(r'(\d+)\s+months?\s+ago', re.IGNORECASE)

# Excel serial date epoch (December 30, 1899)
EXCEL_EPOCH = datetime(1899, 12, 30)
EXCEL_SERIAL_MIN = 1  # Jan 1, 1900
EXCEL_SERIAL_MAX = 2958465  # Dec 31, 9999

# Month name mappings
MONTH_NAMES = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6,
    "jul": 7, "july": 7, "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11, "dec": 12, "december": 12,
}

# Day of week names
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ============================================================================
# TIME CONSTANTS
# ============================================================================

# AM/PM patterns for flexible matching
AM_PATTERNS = {"am", "a.m.", "a.m", "a"}
PM_PATTERNS = {"pm", "p.m.", "p.m", "p"}

# Time buckets
TIME_BUCKETS = {
    "Morning": (6, 12),      # 06:00 - 11:59
    "Afternoon": (12, 17),   # 12:00 - 16:59
    "Evening": (17, 21),     # 17:00 - 20:59
    "Night": (21, 6),        # 21:00 - 05:59 (wraps around)
}

# Timezone pattern
TIMEZONE_PATTERN = re.compile(
    r'(UTC|GMT)?([+-])(\d{1,2}):?(\d{2})?',
    re.IGNORECASE
)


# ============================================================================
# DURATION CONSTANTS
# ============================================================================

# Duration word-to-number (extends the base word-to-number from Session 4)
DURATION_UNITS = {
    "second": 1, "seconds": 1, "sec": 1, "secs": 1, "s": 1,
    "minute": 60, "minutes": 60, "min": 60, "mins": 60, "m": 60,
    "hour": 3600, "hours": 3600, "hr": 3600, "hrs": 3600, "h": 3600,
    "day": 86400, "days": 86400, "d": 86400,
    "week": 604800, "weeks": 604800, "wk": 604800, "wks": 604800, "w": 604800,
    "month": 2629746, "months": 2629746, "mo": 2629746,  # ~30.44 days
    "year": 31556952, "years": 31556952, "yr": 31556952, "yrs": 31556952, "y": 31556952,
}

# Basic word-to-number for duration parsing
WORD_TO_NUMBER: Dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100,
}


# ============================================================================
# FISCAL PERIOD CONSTANTS
# ============================================================================

FISCAL_YEAR_PATTERNS = [
    re.compile(r'^FY\s*(\d{4})$', re.IGNORECASE),                    # FY2024, FY 2024
    re.compile(r'^FY\s*(\d{2})$', re.IGNORECASE),                    # FY24
    re.compile(r'^(\d{4})\s*FY$', re.IGNORECASE),                    # 2024 FY
    re.compile(r'^Financial\s+Year\s+(\d{4})$', re.IGNORECASE),      # Financial Year 2024
    re.compile(r'^Fiscal\s+Year\s+(\d{4})$', re.IGNORECASE),         # Fiscal Year 2024
]

FISCAL_QUARTER_PATTERNS = [
    re.compile(r'^Q([1-4])\s*(?:FY)?\s*(\d{4})?$', re.IGNORECASE),   # Q1, Q1 FY2024, Q1 2024
    re.compile(r'^Q([1-4])\s*[-/]?\s*FY\s*(\d{2,4})$', re.IGNORECASE),  # Q1-FY24
    re.compile(r'^([1-4])(?:st|nd|rd|th)?\s+Quarter\s+(\d{4})?$', re.IGNORECASE),  # 1st Quarter 2024
]

ACADEMIC_YEAR_PATTERNS = [
    re.compile(r'^(\d{4})\s*[/-]\s*(\d{2,4})$'),                     # 2023/24, 2023-2024
    re.compile(r'^AY\s*(\d{4})\s*[-/]?\s*(\d{2,4})$', re.IGNORECASE),  # AY 2023-24
    re.compile(r'^Academic\s+Year\s+(\d{4})\s*[/-]?\s*(\d{2,4})$', re.IGNORECASE),
]

SEMESTER_PATTERNS = {
    re.compile(r'^Sem(?:ester)?\s*1$', re.IGNORECASE): "Semester 1",
    re.compile(r'^Sem(?:ester)?\s*2$', re.IGNORECASE): "Semester 2",
    re.compile(r'^First\s+Semester$', re.IGNORECASE): "Semester 1",
    re.compile(r'^Second\s+Semester$', re.IGNORECASE): "Semester 2",
    re.compile(r'^Term\s*([1-4])$', re.IGNORECASE): "Term {0}",
    re.compile(r'^Spring\s+(\d{4})$', re.IGNORECASE): "Spring {0}",
    re.compile(r'^Fall\s+(\d{4})$', re.IGNORECASE): "Fall {0}",
    re.compile(r'^Summer\s+(\d{4})$', re.IGNORECASE): "Summer {0}",
    re.compile(r'^Winter\s+(\d{4})$', re.IGNORECASE): "Winter {0}",
    re.compile(r'^Autumn\s+(\d{4})$', re.IGNORECASE): "Fall {0}",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def remove_ordinal_suffix(text: str) -> str:
    """Remove ordinal suffixes (st, nd, rd, th) from date strings."""
    return ORDINAL_PATTERN.sub(r'\1', text)


def is_date_placeholder(value: Any) -> bool:
    """Check if a value is a date placeholder."""
    if pd.isna(value):
        return True
    
    normalized = str(value).lower().strip()
    return normalized in DATE_PLACEHOLDERS


def parse_excel_serial(value: float) -> Optional[datetime]:
    """
    Convert Excel serial number to datetime.
    Excel stores dates as number of days since Dec 30, 1899.
    """
    try:
        serial = float(value)
        if EXCEL_SERIAL_MIN <= serial <= EXCEL_SERIAL_MAX:
            # Excel serial 1 = Jan 1, 1900
            # But Excel incorrectly treats 1900 as a leap year, so Feb 29, 1900 is serial 60
            # Dates on or after Mar 1, 1900 (serial > 60) need adjustment
            # However, for most modern dates, we simply calculate from the epoch
            return EXCEL_EPOCH + timedelta(days=serial)
    except (ValueError, TypeError, OverflowError):
        pass
    return None


def is_likely_excel_serial(value: Any) -> bool:
    """Check if a numeric value is likely an Excel serial date."""
    try:
        num = float(value)
        # Excel serial dates are typically 5-digit integers for modern dates
        # (e.g., 44927 = 2023-01-01, range ~40000-50000 for 2009-2036)
        if isinstance(value, (int, float)) and 30000 <= num <= 60000:
            return True
    except (ValueError, TypeError):
        pass
    return False


def detect_date_format_majority(series: pd.Series) -> str:
    """
    Detect whether dates are primarily DD/MM/YYYY or MM/DD/YYYY.
    Returns 'dmy' or 'mdy' based on majority pattern.
    """
    dmy_count = 0
    mdy_count = 0
    
    for val in series.dropna().head(100):
        val_str = str(val)
        # Look for patterns like 15/03/2024 where first number > 12
        match = re.match(r'^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$', val_str)
        if match:
            first, second = int(match.group(1)), int(match.group(2))
            if first > 12 and second <= 12:
                dmy_count += 1
            elif second > 12 and first <= 12:
                mdy_count += 1
    
    return 'dmy' if dmy_count >= mdy_count else 'mdy'


def parse_date_permissive(
    value: Any,
    dayfirst: bool = True,
    reference_date: Optional[datetime] = None
) -> Optional[datetime]:
    """
    Permissive date parser following V2.0 rules.
    If a human can read it as a date, parse it.
    """
    if pd.isna(value):
        return None
    
    if isinstance(value, (datetime, date)):
        if isinstance(value, date) and not isinstance(value, datetime):
            return datetime.combine(value, time())
        return value
    
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    
    # Check for Excel serial number
    if is_likely_excel_serial(value):
        result = parse_excel_serial(value)
        if result:
            return result
    
    val_str = str(value).strip()
    
    if not val_str or is_date_placeholder(val_str):
        return None
    
    # Remove ordinal suffixes (23rd → 23)
    val_str = remove_ordinal_suffix(val_str)
    
    # Handle relative dates
    val_lower = val_str.lower()
    ref = reference_date or datetime.now()
    
    if val_lower in RELATIVE_DATE_PATTERNS:
        return ref + timedelta(days=RELATIVE_DATE_PATTERNS[val_lower])
    
    # Days ago pattern
    days_match = DAYS_AGO_PATTERN.match(val_lower)
    if days_match:
        return ref - timedelta(days=int(days_match.group(1)))
    
    # Weeks ago pattern
    weeks_match = WEEKS_AGO_PATTERN.match(val_lower)
    if weeks_match:
        return ref - timedelta(weeks=int(weeks_match.group(1)))
    
    # Months ago pattern
    months_match = MONTHS_AGO_PATTERN.match(val_lower)
    if months_match:
        return ref - relativedelta(months=int(months_match.group(1)))
    
    # Try dateutil parser (very permissive)
    try:
        parsed = dateutil_parser.parse(val_str, dayfirst=dayfirst, fuzzy=True)
        return parsed
    except (ValueError, TypeError, OverflowError):
        pass
    
    return None


def is_date_valid(dt: datetime) -> bool:
    """Check if a parsed date is logically valid."""
    # Year range check
    if dt.year < 1900 or dt.year > 2100:
        return False
    return True


def parse_time_permissive(value: Any) -> Optional[time]:
    """
    Permissive time parser.
    Handles: "3:00 PM", "3:00pm", "15:00", "9:5", etc.
    """
    if pd.isna(value):
        return None
    
    if isinstance(value, time):
        return value
    
    if isinstance(value, datetime):
        return value.time()
    
    val_str = str(value).strip().lower()
    
    if not val_str:
        return None
    
    # Extract AM/PM indicator
    is_pm = None
    for pm_indicator in PM_PATTERNS:
        if val_str.endswith(pm_indicator):
            is_pm = True
            val_str = val_str[:-len(pm_indicator)].strip()
            break
    
    if is_pm is None:
        for am_indicator in AM_PATTERNS:
            if val_str.endswith(am_indicator):
                is_pm = False
                val_str = val_str[:-len(am_indicator)].strip()
                break
    
    # Parse time components
    time_match = re.match(r'^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?$', val_str)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        second = int(time_match.group(3)) if time_match.group(3) else 0
        
        # Convert 12-hour to 24-hour
        if is_pm is not None:
            if is_pm and hour < 12:
                hour += 12
            elif not is_pm and hour == 12:
                hour = 0
        
        # Validate
        if 0 <= hour <= 23 and 0 <= minute <= 59 and 0 <= second <= 59:
            return time(hour, minute, second)
    
    # Try just hour (e.g., "3PM")
    hour_only_match = re.match(r'^(\d{1,2})$', val_str)
    if hour_only_match and is_pm is not None:
        hour = int(hour_only_match.group(1))
        if is_pm and hour < 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0
        if 0 <= hour <= 23:
            return time(hour, 0, 0)
    
    return None


def extract_timezone(value: str) -> Tuple[str, Optional[str]]:
    """
    Extract timezone from a time/datetime string.
    Returns: (time_without_tz, timezone_string)
    """
    tz_match = TIMEZONE_PATTERN.search(value)
    if tz_match:
        tz_str = tz_match.group(0)
        time_str = value[:tz_match.start()].strip()
        return time_str, tz_str
    return value, None


def get_time_bucket(t: time) -> str:
    """Get time bucket (Morning, Afternoon, Evening, Night)."""
    hour = t.hour
    
    if 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"


def parse_duration(value: Any) -> Optional[Tuple[float, str]]:
    """
    Parse duration string into (value, unit).
    Returns duration in days by default.
    """
    if pd.isna(value):
        return None
    
    val_str = str(value).strip().lower()
    
    if not val_str:
        return None
    
    # Pattern: "2h 30m", "2:30", "150 min", "2.5 hours", "two years"
    total_seconds = 0
    
    # Handle HH:MM or HH:MM:SS format
    time_format = re.match(r'^(\d{1,2}):(\d{2})(?::(\d{2}))?$', val_str)
    if time_format:
        hours = int(time_format.group(1))
        minutes = int(time_format.group(2))
        seconds = int(time_format.group(3)) if time_format.group(3) else 0
        total_seconds = hours * 3600 + minutes * 60 + seconds
        return (total_seconds / 86400, "days")
    
    # Handle "X unit" patterns
    pattern = re.compile(r'(\d+(?:\.\d+)?|\w+)\s*(second|seconds|sec|secs|s|minute|minutes|min|mins|m|hour|hours|hr|hrs|h|day|days|d|week|weeks|wk|wks|w|month|months|mo|year|years|yr|yrs|y)\b', re.IGNORECASE)
    
    matches = pattern.findall(val_str)
    if matches:
        for num_str, unit in matches:
            # Convert word to number if needed
            try:
                num = float(num_str)
            except ValueError:
                num = WORD_TO_NUMBER.get(num_str.lower())
                if num is None:
                    continue
            
            unit_seconds = DURATION_UNITS.get(unit.lower(), 0)
            total_seconds += num * unit_seconds
        
        if total_seconds > 0:
            return (total_seconds / 86400, "days")
    
    # Handle plain number (ambiguous - return as is)
    try:
        num = float(val_str)
        return (num, "unknown")
    except ValueError:
        pass
    
    return None


def parse_fiscal_year(value: str) -> Optional[int]:
    """Parse fiscal year string and return the year."""
    val_str = str(value).strip()
    
    for pattern in FISCAL_YEAR_PATTERNS:
        match = pattern.match(val_str)
        if match:
            year_str = match.group(1)
            year = int(year_str)
            if year < 100:
                year = 2000 + year if year < 50 else 1900 + year
            return year
    
    return None


def parse_academic_year(value: str) -> Optional[Tuple[int, int]]:
    """Parse academic year string and return (start_year, end_year)."""
    val_str = str(value).strip()
    
    for pattern in ACADEMIC_YEAR_PATTERNS:
        match = pattern.match(val_str)
        if match:
            start = int(match.group(1))
            end_str = match.group(2)
            end = int(end_str)
            if end < 100:
                # Handle 2-digit year
                end = (start // 100) * 100 + end
                if end < start:
                    end += 100
            return (start, end)
    
    return None


# ============================================================================
# FORMULA RESULT CLASS
# ============================================================================

@dataclass
class CleaningResult:
    """Result of a cleaning operation on a column."""
    column: str
    formula_id: str
    changes_made: int = 0
    rows_flagged: int = 0
    was_auto_applied: bool = True
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# DATE & TIME RULES CLASS
# ============================================================================

class DateTimeRules:
    """
    Applies date and time cleaning rules based on HTYPE classification.
    """
    
    def __init__(
        self,
        job_id: int,
        df: pd.DataFrame,
        db: Session,
        htype_map: Dict[str, str],
        reference_date: Optional[datetime] = None,
        fiscal_year_start_month: int = 1,
    ):
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.htype_map = htype_map
        self.reference_date = reference_date or datetime.now()
        self.fiscal_year_start_month = fiscal_year_start_month
        self.flags: List[Dict[str, Any]] = []
        self.results: List[CleaningResult] = []
    
    def _log(
        self,
        formula_id: str,
        column: str,
        action: str,
        row_indices: List[int],
        before_values: List[Any],
        after_values: List[Any],
        was_auto_applied: bool = True,
    ):
        """Log cleaning action to database."""
        if not row_indices:
            return
        
        for i, idx in enumerate(row_indices[:100]):
            before = str(before_values[i])[:200] if i < len(before_values) else None
            after = str(after_values[i])[:200] if i < len(after_values) else None
            
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
    # DATE FORMULAS — HTYPE-004
    # ========================================================================
    
    def DATE_01_permissive_parsing(self, col: str) -> CleaningResult:
        """Parse all date variants permissively (V2.0 core rule)."""
        result = CleaningResult(column=col, formula_id="DATE-01")
        
        # Detect majority format for ambiguous dates
        dayfirst = detect_date_format_majority(self.df[col]) == 'dmy'
        
        # Convert column to object dtype to allow datetime values
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            # Skip if already datetime
            if isinstance(val, (datetime, date, pd.Timestamp)):
                continue
            
            parsed = parse_date_permissive(val, dayfirst=dayfirst, reference_date=self.reference_date)
            if parsed and is_date_valid(parsed):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(parsed)
                self.df.at[idx, col] = parsed
        
        if changed_indices:
            self._log("DATE-01", col, "Permissive date parsing",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def DATE_02_ambiguous_resolution(self, col: str) -> CleaningResult:
        """Flag truly ambiguous dates for user review."""
        result = CleaningResult(column=col, formula_id="DATE-02", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            # Check for DD/MM or MM/DD ambiguity (both parts ≤ 12)
            match = re.match(r'^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$', str(val))
            if match:
                first, second = int(match.group(1)), int(match.group(2))
                if first <= 12 and second <= 12 and first != second:
                    flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "DATE-02", col,
                "Ambiguous date format (day/month could be swapped)",
                flagged_indices,
                "Confirm date format: DD/MM/YYYY or MM/DD/YYYY",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def DATE_03_invalid_rejection(self, col: str) -> CleaningResult:
        """Flag logically impossible dates (Feb 31, month 13, etc.)."""
        result = CleaningResult(column=col, formula_id="DATE-03", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str):
                # Check for impossible dates before parsing
                match = re.match(r'^(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{2,4})$', val)
                if match:
                    d1, d2 = int(match.group(1)), int(match.group(2))
                    # Month > 12 is invalid
                    if d1 > 12 and d2 > 12:
                        flagged_indices.append(idx)
                        continue
                    # Day > 31 is invalid
                    if d1 > 31 or d2 > 31:
                        flagged_indices.append(idx)
                        continue
                
                # Try to parse and catch invalid dates
                try:
                    parsed = parse_date_permissive(val)
                    if parsed is None:
                        flagged_indices.append(idx)
                except (ValueError, OverflowError):
                    flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "DATE-03", col,
                "Logically impossible dates detected",
                flagged_indices,
                "Correct or remove invalid dates",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def DATE_04_future_date_check(self, col: str, is_historical: bool = True) -> CleaningResult:
        """Flag future dates in historical columns."""
        result = CleaningResult(column=col, formula_id="DATE-04", was_auto_applied=False)
        
        if not is_historical:
            return result  # Skip for forward-looking columns
        
        today = self.reference_date.date() if isinstance(self.reference_date, datetime) else self.reference_date
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            dt = None
            if isinstance(val, datetime):
                dt = val.date()
            elif isinstance(val, date):
                dt = val
            elif isinstance(val, pd.Timestamp):
                dt = val.date()
            
            if dt and dt > today:
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "DATE-04", col,
                "Future dates detected in historical column",
                flagged_indices,
                "Verify or correct future dates",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def DATE_05_dob_sanity(self, col: str) -> CleaningResult:
        """Check DOB produces valid age (0-120)."""
        result = CleaningResult(column=col, formula_id="DATE-05", was_auto_applied=False)
        
        # Only apply to DOB-like columns
        col_lower = col.lower()
        if not any(kw in col_lower for kw in ["dob", "birth", "born"]):
            return result
        
        today = self.reference_date.date() if isinstance(self.reference_date, datetime) else self.reference_date
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            dt = None
            if isinstance(val, datetime):
                dt = val.date()
            elif isinstance(val, date):
                dt = val
            elif isinstance(val, pd.Timestamp):
                dt = val.date()
            
            if dt:
                age = (today - dt).days / 365.25
                if age < 0 or age > 120:
                    flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "DATE-05", col,
                "DOB produces invalid age (< 0 or > 120)",
                flagged_indices,
                "Verify date of birth values",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def DATE_07_type_enforcement(self, col: str) -> CleaningResult:
        """Ensure date column is stored as datetime type."""
        result = CleaningResult(column=col, formula_id="DATE-07")
        
        # Check current dtype
        if pd.api.types.is_datetime64_any_dtype(self.df[col]):
            return result
        
        # Try to convert
        try:
            original = self.df[col].copy()
            self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
            
            # Count successful conversions
            changed = (~original.isna() & ~self.df[col].isna()).sum()
            result.changes_made = int(changed)
            result.details["dtype_changed"] = True
        except Exception:
            pass
        
        return result
    
    def DATE_08_partial_date_handling(self, col: str) -> CleaningResult:
        """Handle partial dates (year only, year-month only)."""
        result = CleaningResult(column=col, formula_id="DATE-08")
        
        # Convert column to object dtype to allow datetime values
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            
            # Year only (4 digits)
            if re.match(r'^(\d{4})$', val_str):
                year = int(val_str)
                if 1900 <= year <= 2100:
                    new_val = datetime(year, 1, 1)
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(new_val)
                    self.df.at[idx, col] = new_val
                continue
            
            # Year-Month (YYYY-MM or MM/YYYY)
            match = re.match(r'^(\d{4})[/-](\d{1,2})$', val_str)
            if match:
                year, month = int(match.group(1)), int(match.group(2))
                if 1900 <= year <= 2100 and 1 <= month <= 12:
                    new_val = datetime(year, month, 1)
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(new_val)
                    self.df.at[idx, col] = new_val
                continue
        
        if changed_indices:
            self._log("DATE-08", col, "Partial date handling",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def DATE_09_excel_serial_conversion(self, col: str) -> CleaningResult:
        """Convert Excel serial numbers to dates."""
        result = CleaningResult(column=col, formula_id="DATE-09")
        
        # Convert column to object dtype to allow datetime values
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if is_likely_excel_serial(val):
                parsed = parse_excel_serial(val)
                if parsed:
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(parsed)
                    self.df.at[idx, col] = parsed
        
        if changed_indices:
            self._log("DATE-09", col, "Excel serial number conversion",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def DATE_10_placeholder_rejection(self, col: str) -> CleaningResult:
        """Treat date placeholders as missing."""
        result = CleaningResult(column=col, formula_id="DATE-10")
        
        changed_indices = []
        before_vals = []
        
        for idx, val in self.df[col].items():
            if is_date_placeholder(val):
                if not pd.isna(val):
                    changed_indices.append(idx)
                    before_vals.append(val)
                    self.df.at[idx, col] = pd.NaT
        
        if changed_indices:
            self._log("DATE-10", col, "Placeholder to null conversion",
                     changed_indices, before_vals, [None] * len(before_vals))
            result.changes_made = len(changed_indices)
        
        return result
    
    def DATE_12_weekday_annotation(self, col: str) -> CleaningResult:
        """Derive day of week from date column."""
        result = CleaningResult(column=col, formula_id="DATE-12")
        
        weekday_col = f"{col}_weekday"
        if weekday_col not in self.df.columns:
            self.df[weekday_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_count = 0
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            dt = None
            if isinstance(val, (datetime, date, pd.Timestamp)):
                dt = val
            
            if dt:
                weekday = DAY_NAMES[dt.weekday()]
                self.df.at[idx, weekday_col] = weekday
                changed_count += 1
        
        if changed_count > 0:
            result.changes_made = changed_count
            result.details["weekday_column_created"] = weekday_col
        
        return result
    
    def DATE_14_relative_date_parsing(self, col: str) -> CleaningResult:
        """Convert relative date phrases to absolute dates."""
        result = CleaningResult(column=col, formula_id="DATE-14")
        
        # Convert column to object dtype to allow datetime values
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            val_lower = val.lower().strip()
            ref = self.reference_date
            parsed = None
            
            # Check simple relative words
            if val_lower in RELATIVE_DATE_PATTERNS:
                days_offset = RELATIVE_DATE_PATTERNS[val_lower]
                parsed = ref + timedelta(days=days_offset)
            
            # Days ago
            if parsed is None:
                match = DAYS_AGO_PATTERN.match(val_lower)
                if match:
                    parsed = ref - timedelta(days=int(match.group(1)))
            
            # Weeks ago
            if parsed is None:
                match = WEEKS_AGO_PATTERN.match(val_lower)
                if match:
                    parsed = ref - timedelta(weeks=int(match.group(1)))
            
            # Months ago
            if parsed is None:
                match = MONTHS_AGO_PATTERN.match(val_lower)
                if match:
                    parsed = ref - relativedelta(months=int(match.group(1)))
            
            if parsed:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(parsed)
                self.df.at[idx, col] = parsed
        
        if changed_indices:
            self._log("DATE-14", col, "Relative date conversion",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def DATE_15_excel_serial_conversion(self, col: str) -> CleaningResult:
        """Same as DATE-09 - Excel serial number conversion."""
        return self.DATE_09_excel_serial_conversion(col)
    
    # ========================================================================
    # TIME FORMULAS — HTYPE-005
    # ========================================================================
    
    def TIME_01_12h_24h_normalization(self, col: str) -> CleaningResult:
        """Normalize 12h format to 24h format."""
        result = CleaningResult(column=col, formula_id="TIME-01")
        
        # Convert column to object dtype to allow string values
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            # Skip if already time object
            if isinstance(val, time):
                continue
            
            parsed = parse_time_permissive(val)
            if parsed:
                # Format as HH:MM or HH:MM:SS
                if parsed.second > 0:
                    formatted = parsed.strftime("%H:%M:%S")
                else:
                    formatted = parsed.strftime("%H:%M")
                
                if str(val) != formatted:
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(formatted)
                    self.df.at[idx, col] = formatted
        
        if changed_indices:
            self._log("TIME-01", col, "12h to 24h normalization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def TIME_02_format_standardization(self, col: str) -> CleaningResult:
        """Standardize time format to HH:MM or HH:MM:SS."""
        result = CleaningResult(column=col, formula_id="TIME-02")
        
        # Convert column to object dtype to allow string values
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            parsed = parse_time_permissive(val)
            if parsed:
                # If original had seconds (e.g., "7:30:00"), preserve seconds in output
                val_str = str(val)
                has_seconds = len(val_str.replace(" ", "").split(":")) >= 3 or parsed.second > 0
                
                if has_seconds:
                    formatted = parsed.strftime("%H:%M:%S")
                else:
                    formatted = parsed.strftime("%H:%M")
                
                if val_str != formatted:
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(formatted)
                    self.df.at[idx, col] = formatted
        
        if changed_indices:
            self._log("TIME-02", col, "Time format standardization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def TIME_03_invalid_rejection(self, col: str) -> CleaningResult:
        """Flag invalid times (hours > 23, minutes > 59, seconds > 59)."""
        result = CleaningResult(column=col, formula_id="TIME-03", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str):
                # Check for invalid time values
                match = re.match(r'^(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?', val)
                if match:
                    hour = int(match.group(1))
                    minute = int(match.group(2))
                    second = int(match.group(3)) if match.group(3) else 0
                    
                    if hour > 23 or minute > 59 or second > 59:
                        flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "TIME-03", col,
                "Invalid time values detected",
                flagged_indices,
                "Correct invalid times",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def TIME_04_timezone_extraction(self, col: str) -> CleaningResult:
        """Extract timezone to separate column."""
        result = CleaningResult(column=col, formula_id="TIME-04")
        
        tz_col = f"{col}_timezone"
        if tz_col not in self.df.columns:
            self.df[tz_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            time_part, tz_part = extract_timezone(val)
            if tz_part:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(time_part)
                self.df.at[idx, col] = time_part
                self.df.at[idx, tz_col] = tz_part
        
        if changed_indices:
            self._log("TIME-04", col, "Timezone extraction",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
            result.details["timezone_column_created"] = tz_col
        
        return result
    
    def TIME_05_bucketing(self, col: str) -> CleaningResult:
        """Create time bucket column (Morning, Afternoon, Evening, Night)."""
        result = CleaningResult(column=col, formula_id="TIME-05")
        
        bucket_col = f"{col}_bucket"
        if bucket_col not in self.df.columns:
            self.df[bucket_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_count = 0
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            t = None
            if isinstance(val, time):
                t = val
            elif isinstance(val, datetime):
                t = val.time()
            elif isinstance(val, str):
                t = parse_time_permissive(val)
            
            if t:
                bucket = get_time_bucket(t)
                self.df.at[idx, bucket_col] = bucket
                changed_count += 1
        
        if changed_count > 0:
            result.changes_made = changed_count
            result.details["bucket_column_created"] = bucket_col
        
        return result
    
    # ========================================================================
    # DATETIME FORMULAS — HTYPE-006
    # ========================================================================
    
    def DTM_01_permissive_parsing(self, col: str) -> CleaningResult:
        """Parse all combined date-time formats permissively (V2.0 core)."""
        result = CleaningResult(column=col, formula_id="DTM-01")
        
        # Convert column to object dtype to allow datetime values
        self.df[col] = self.df[col].astype(object)
        
        dayfirst = detect_date_format_majority(self.df[col]) == 'dmy'
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, datetime):
                continue
            
            parsed = parse_date_permissive(val, dayfirst=dayfirst)
            if parsed:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(parsed)
                self.df.at[idx, col] = parsed
        
        if changed_indices:
            self._log("DTM-01", col, "Permissive datetime parsing",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def DTM_02_date_time_splitting(self, col: str) -> CleaningResult:
        """Split datetime into separate date and time columns."""
        result = CleaningResult(column=col, formula_id="DTM-02")
        
        date_col = f"{col}_date"
        time_col = f"{col}_time"
        
        if date_col not in self.df.columns:
            self.df[date_col] = pd.Series([None] * len(self.df), dtype=object)
        if time_col not in self.df.columns:
            self.df[time_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_count = 0
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            dt = None
            if isinstance(val, datetime):
                dt = val
            elif isinstance(val, pd.Timestamp):
                dt = val.to_pydatetime()
            
            if dt:
                self.df.at[idx, date_col] = dt.date()
                self.df.at[idx, time_col] = dt.strftime("%H:%M:%S")
                changed_count += 1
        
        if changed_count > 0:
            result.changes_made = changed_count
            result.details["date_column_created"] = date_col
            result.details["time_column_created"] = time_col
        
        return result
    
    def DTM_03_iso_normalization(self, col: str) -> CleaningResult:
        """Normalize datetime to ISO 8601 format."""
        result = CleaningResult(column=col, formula_id="DTM-03")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            dt = None
            if isinstance(val, datetime):
                dt = val
            elif isinstance(val, pd.Timestamp):
                dt = val.to_pydatetime()
            
            if dt:
                iso_format = dt.strftime("%Y-%m-%d %H:%M:%S")
                if str(val) != iso_format:
                    changed_indices.append(idx)
                    before_vals.append(str(val))
                    after_vals.append(iso_format)
                    # Keep as datetime object, not string
        
        if changed_indices:
            self._log("DTM-03", col, "ISO 8601 normalization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def DTM_05_sort_key_generation(self, col: str) -> CleaningResult:
        """Ensure datetime is stored as proper type for sorting."""
        result = CleaningResult(column=col, formula_id="DTM-05")
        
        if pd.api.types.is_datetime64_any_dtype(self.df[col]):
            return result
        
        try:
            original = self.df[col].copy()
            self.df[col] = pd.to_datetime(self.df[col], errors='coerce')
            changed = (~original.isna() & ~self.df[col].isna()).sum()
            result.changes_made = int(changed)
            result.details["converted_to_datetime"] = True
        except Exception:
            pass
        
        return result
    
    def DTM_06_duplicate_timestamp_alert(self, col: str) -> CleaningResult:
        """Flag duplicate timestamps for same entity."""
        result = CleaningResult(column=col, formula_id="DTM-06", was_auto_applied=False)
        
        # Find ID column if exists
        id_cols = [c for c, h in self.htype_map.items() if h == "HTYPE-003"]
        
        if not id_cols:
            # No ID column - just find duplicate timestamps
            dups = self.df[col].duplicated(keep=False)
            flagged_indices = self.df[dups].index.tolist()
        else:
            # Find same entity with same timestamp
            id_col = id_cols[0]
            flagged_indices = []
            
            grouped = self.df.groupby([id_col, col])
            for (entity_id, ts), group in grouped:
                if len(group) > 1:
                    flagged_indices.extend(group.index.tolist())
        
        if flagged_indices:
            self._flag(
                "DTM-06", col,
                "Duplicate timestamps detected (possible double submission)",
                flagged_indices,
                "Review for duplicate records",
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    # ========================================================================
    # DURATION FORMULAS — HTYPE-033
    # ========================================================================
    
    def DUR_01_word_to_unit_parsing(self, col: str) -> CleaningResult:
        """Convert word-based durations to numeric."""
        result = CleaningResult(column=col, formula_id="DUR-01")
        
        # Convert column to object dtype to allow mixed types
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if isinstance(val, str) and not val.replace(".", "").isdigit():
                parsed = parse_duration(val)
                if parsed and parsed[1] != "unknown":
                    days, unit = parsed
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(days)
                    self.df.at[idx, col] = days
        
        if changed_indices:
            self._log("DUR-01", col, "Word-to-unit duration parsing",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def DUR_02_unit_standardization(self, col: str) -> CleaningResult:
        """Convert all durations to standard unit (days)."""
        result = CleaningResult(column=col, formula_id="DUR-02")
        
        # Convert column to object dtype to allow mixed types
        self.df[col] = self.df[col].astype(object)
        
        # Create unit column to track original units
        unit_col = f"{col}_original_unit"
        if unit_col not in self.df.columns:
            self.df[unit_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            parsed = parse_duration(val)
            if parsed:
                days, original_unit = parsed
                if original_unit != "days" and original_unit != "unknown":
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(days)
                    self.df.at[idx, col] = days
                    self.df.at[idx, unit_col] = original_unit
        
        if changed_indices:
            self._log("DUR-02", col, "Duration unit standardization (to days)",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def DUR_03_format_normalization(self, col: str) -> CleaningResult:
        """Normalize duration format variants."""
        result = CleaningResult(column=col, formula_id="DUR-03")
        
        # This is largely handled by DUR-01 and DUR-02
        # Additional normalization can be added here
        
        return result
    
    def DUR_04_negative_rejection(self, col: str) -> CleaningResult:
        """Flag negative durations."""
        result = CleaningResult(column=col, formula_id="DUR-04", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                if float(val) < 0:
                    flagged_indices.append(idx)
            except (ValueError, TypeError):
                pass
        
        if flagged_indices:
            self._flag(
                "DUR-04", col,
                "Negative duration values detected",
                flagged_indices,
                "Correct or remove negative durations",
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def DUR_06_outlier_detection(self, col: str) -> CleaningResult:
        """Flag statistical outliers in duration."""
        result = CleaningResult(column=col, formula_id="DUR-06", was_auto_applied=False)
        
        # Convert to numeric for analysis
        numeric_vals = pd.to_numeric(self.df[col], errors='coerce')
        valid_vals = numeric_vals.dropna()
        
        if len(valid_vals) < 10:
            return result
        
        # Calculate IQR
        q1 = valid_vals.quantile(0.25)
        q3 = valid_vals.quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - 3 * iqr
        upper_bound = q3 + 3 * iqr
        
        outlier_mask = (numeric_vals < lower_bound) | (numeric_vals > upper_bound)
        flagged_indices = self.df[outlier_mask].index.tolist()
        
        if flagged_indices:
            self._flag(
                "DUR-06", col,
                f"Duration outliers detected (outside {lower_bound:.1f} - {upper_bound:.1f})",
                flagged_indices,
                "Review extreme duration values",
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def DUR_07_ambiguous_unit_detection(self, col: str) -> CleaningResult:
        """Flag numeric-only durations with ambiguous units."""
        result = CleaningResult(column=col, formula_id="DUR-07", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            
            # Check if it's just a number without any unit
            try:
                float(val_str)
                # Pure number - unit is ambiguous
                flagged_indices.append(idx)
            except ValueError:
                pass
        
        if flagged_indices:
            self._flag(
                "DUR-07", col,
                "Numeric durations without units detected",
                flagged_indices,
                "Specify the unit (days, months, years, etc.)",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    # ========================================================================
    # FISCAL PERIOD FORMULAS — HTYPE-041
    # ========================================================================
    
    def FISC_01_fiscal_year_standardization(self, col: str) -> CleaningResult:
        """Standardize fiscal year formats to FY####."""
        result = CleaningResult(column=col, formula_id="FISC-01")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            year = parse_fiscal_year(val_str)
            
            if year:
                standard = f"FY{year}"
                if val_str != standard:
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(standard)
                    self.df.at[idx, col] = standard
        
        if changed_indices:
            self._log("FISC-01", col, "Fiscal year standardization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FISC_02_fiscal_quarter_parsing(self, col: str) -> CleaningResult:
        """Parse and standardize fiscal quarter formats."""
        result = CleaningResult(column=col, formula_id="FISC-02")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            
            for pattern in FISCAL_QUARTER_PATTERNS:
                match = pattern.match(val_str)
                if match:
                    quarter = match.group(1)
                    year = match.group(2) if len(match.groups()) > 1 and match.group(2) else None
                    
                    if year:
                        year_int = int(year)
                        if year_int < 100:
                            year_int = 2000 + year_int if year_int < 50 else 1900 + year_int
                        standard = f"Q{quarter} FY{year_int}"
                    else:
                        standard = f"Q{quarter}"
                    
                    if val_str != standard:
                        changed_indices.append(idx)
                        before_vals.append(val)
                        after_vals.append(standard)
                        self.df.at[idx, col] = standard
                    break
        
        if changed_indices:
            self._log("FISC-02", col, "Fiscal quarter standardization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FISC_03_academic_year_standardization(self, col: str) -> CleaningResult:
        """Standardize academic year formats to AY ####-##."""
        result = CleaningResult(column=col, formula_id="FISC-03")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            parsed = parse_academic_year(val_str)
            
            if parsed:
                start, end = parsed
                end_short = end % 100
                standard = f"AY {start}-{end_short:02d}"
                
                if val_str != standard:
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(standard)
                    self.df.at[idx, col] = standard
        
        if changed_indices:
            self._log("FISC-03", col, "Academic year standardization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FISC_04_semester_parsing(self, col: str) -> CleaningResult:
        """Parse and standardize semester/term formats."""
        result = CleaningResult(column=col, formula_id="FISC-04")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            
            for pattern, replacement in SEMESTER_PATTERNS.items():
                match = pattern.match(val_str)
                if match:
                    if "{0}" in replacement:
                        standard = replacement.format(match.group(1))
                    else:
                        standard = replacement
                    
                    if val_str != standard:
                        changed_indices.append(idx)
                        before_vals.append(val)
                        after_vals.append(standard)
                        self.df.at[idx, col] = standard
                    break
        
        if changed_indices:
            self._log("FISC-04", col, "Semester/term standardization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FISC_05_sort_order_derivation(self, col: str) -> CleaningResult:
        """Create numeric sort key for chronological ordering."""
        result = CleaningResult(column=col, formula_id="FISC-05")
        
        sort_col = f"{col}_sort_key"
        if sort_col not in self.df.columns:
            self.df[sort_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_count = 0
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            sort_key = None
            
            # FY#### format
            fy_match = re.match(r'^FY\s*(\d{4})$', val_str, re.IGNORECASE)
            if fy_match:
                sort_key = int(fy_match.group(1)) * 10
            
            # Q# FY#### format
            qfy_match = re.match(r'^Q([1-4])\s*FY\s*(\d{4})$', val_str, re.IGNORECASE)
            if qfy_match:
                sort_key = int(qfy_match.group(2)) * 10 + int(qfy_match.group(1))
            
            # AY ####-## format
            ay_match = re.match(r'^AY\s*(\d{4})-(\d{2})$', val_str, re.IGNORECASE)
            if ay_match:
                sort_key = int(ay_match.group(1)) * 10
            
            if sort_key:
                self.df.at[idx, sort_col] = sort_key
                changed_count += 1
        
        if changed_count > 0:
            result.changes_made = changed_count
            result.details["sort_key_column_created"] = sort_col
        
        return result
    
    def FISC_06_calendar_to_fiscal_mapping(self, col: str) -> CleaningResult:
        """Map calendar dates to fiscal periods."""
        result = CleaningResult(column=col, formula_id="FISC-06")
        
        # Check if there's a date column to map from
        date_cols = [c for c, h in self.htype_map.items() if h == "HTYPE-004"]
        
        if not date_cols:
            return result
        
        # This would create fiscal period from calendar date
        # Implementation depends on user's fiscal year start month
        # Left as flag for user to configure
        
        return result
    
    def FISC_07_null_handling(self, col: str) -> CleaningResult:
        """Flag null fiscal period values."""
        result = CleaningResult(column=col, formula_id="FISC-07", was_auto_applied=False)
        
        null_indices = self.df[self.df[col].isna()].index.tolist()
        
        if null_indices:
            self._flag(
                "FISC-07", col,
                "Missing fiscal period values",
                null_indices,
                "Provide fiscal period values or derive from dates",
            )
            result.rows_flagged = len(null_indices)
        
        return result
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_for_column(self, col: str, htype: str) -> List[CleaningResult]:
        """Run all applicable formulas for a column based on its HTYPE."""
        results = []
        
        if htype == "HTYPE-004":  # Date
            # Flag invalid dates FIRST (before any parsing changes the values)
            results.append(self.DATE_03_invalid_rejection(col))
            # Auto formulas
            results.append(self.DATE_10_placeholder_rejection(col))
            results.append(self.DATE_09_excel_serial_conversion(col))
            results.append(self.DATE_14_relative_date_parsing(col))
            results.append(self.DATE_08_partial_date_handling(col))
            results.append(self.DATE_01_permissive_parsing(col))
            results.append(self.DATE_07_type_enforcement(col))
            results.append(self.DATE_12_weekday_annotation(col))
            # Other ask-first formulas (run after parsing)
            results.append(self.DATE_02_ambiguous_resolution(col))
            results.append(self.DATE_04_future_date_check(col))
            results.append(self.DATE_05_dob_sanity(col))
        
        elif htype == "HTYPE-005":  # Time
            results.append(self.TIME_04_timezone_extraction(col))
            results.append(self.TIME_01_12h_24h_normalization(col))
            results.append(self.TIME_02_format_standardization(col))
            results.append(self.TIME_05_bucketing(col))
            # Ask-first
            results.append(self.TIME_03_invalid_rejection(col))
        
        elif htype == "HTYPE-006":  # DateTime
            results.append(self.DTM_01_permissive_parsing(col))
            results.append(self.DTM_05_sort_key_generation(col))
            results.append(self.DTM_02_date_time_splitting(col))
            results.append(self.DTM_03_iso_normalization(col))
            # Ask-first
            results.append(self.DTM_06_duplicate_timestamp_alert(col))
        
        elif htype == "HTYPE-033":  # Duration
            results.append(self.DUR_01_word_to_unit_parsing(col))
            results.append(self.DUR_02_unit_standardization(col))
            results.append(self.DUR_03_format_normalization(col))
            # Ask-first
            results.append(self.DUR_04_negative_rejection(col))
            results.append(self.DUR_06_outlier_detection(col))
            results.append(self.DUR_07_ambiguous_unit_detection(col))
        
        elif htype == "HTYPE-041":  # Fiscal Period
            results.append(self.FISC_01_fiscal_year_standardization(col))
            results.append(self.FISC_02_fiscal_quarter_parsing(col))
            results.append(self.FISC_03_academic_year_standardization(col))
            results.append(self.FISC_04_semester_parsing(col))
            results.append(self.FISC_05_sort_order_derivation(col))
            # Ask-first
            results.append(self.FISC_07_null_handling(col))
        
        return results
    
    def run_all(self) -> Dict[str, Any]:
        """
        Run date/time rules for all columns based on HTYPE classification.
        """
        all_results = []
        formulas_applied = set()
        
        target_htypes = {"HTYPE-004", "HTYPE-005", "HTYPE-006", "HTYPE-033", "HTYPE-041"}
        
        for col, htype in self.htype_map.items():
            if col not in self.df.columns:
                continue
            
            if htype in target_htypes:
                col_results = self.run_for_column(col, htype)
                all_results.extend(col_results)
                
                for r in col_results:
                    if r.changes_made > 0 or r.rows_flagged > 0:
                        formulas_applied.add(r.formula_id)
        
        # Commit all logs
        self.db.flush()
        
        return {
            "date_time_rules_applied": list(formulas_applied),
            "total_changes": sum(r.changes_made for r in all_results),
            "total_flags": len(self.flags),
            "columns_processed": len([c for c, h in self.htype_map.items() if h in target_htypes]),
        }
