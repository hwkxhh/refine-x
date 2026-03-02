"""
Missing Value Decision Matrix — Session 12

Implements the Missing Value Decision Matrix from the Formula Rulebook (Section 52).
For every null encountered, the system follows this matrix to determine:
- Can the system predict/derive the value?
- What confidence level?
- Auto-apply, suggest for confirmation, or prompt user?

Logic First. AI Never (except for suggestions that require user confirmation).
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from collections import Counter
from enum import Enum
import math

import pandas as pd
import numpy as np

from app.models.cleaning_log import CleaningLog


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class Confidence(Enum):
    """Confidence levels for missing value predictions."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class Action(Enum):
    """Actions to take for missing values."""
    AUTO_FILL = "auto_fill"           # High confidence, auto-apply
    SUGGEST = "suggest"               # Medium confidence, user confirms
    PROMPT = "prompt"                 # Cannot predict, ask user
    AI_SUGGEST = "ai_suggest"         # Low confidence, AI suggests, user must confirm


@dataclass
class MissingValueResult:
    """Result of analyzing a missing value."""
    row_idx: int
    column: str
    scenario: str
    can_predict: bool
    confidence: Confidence
    action: Action
    predicted_value: Any = None
    derivation_method: str = ""
    source_columns: List[str] = field(default_factory=list)
    was_applied: bool = False


@dataclass 
class MissingValueSummary:
    """Summary of missing value handling for a column."""
    column: str
    total_missing: int
    auto_filled: int = 0
    suggested: int = 0
    prompted: int = 0
    scenarios: Dict[str, int] = field(default_factory=dict)


# ============================================================================
# CONSTANTS
# ============================================================================

# Gender refusal phrases that are valid data, not missing
GENDER_REFUSAL_PHRASES = {
    "prefer not to say", "prefer not to answer", "decline to state",
    "decline to answer", "rather not say", "not specified", "unspecified",
    "other", "non-binary", "none of your business", "private", "confidential",
}

# Country lookup by unique city (cities that uniquely identify a country)
UNIQUE_CITY_COUNTRY_MAP = {
    "tokyo": "Japan",
    "paris": "France", 
    "london": "United Kingdom",
    "berlin": "Germany",
    "rome": "Italy",
    "madrid": "Spain",
    "moscow": "Russia",
    "beijing": "China",
    "seoul": "South Korea",
    "mumbai": "India",
    "delhi": "India",
    "cairo": "Egypt",
    "sydney": "Australia",
    "melbourne": "Australia",
    "toronto": "Canada",
    "vancouver": "Canada",
    "mexico city": "Mexico",
    "sao paulo": "Brazil",
    "rio de janeiro": "Brazil",
    "buenos aires": "Argentina",
    "amsterdam": "Netherlands",
    "brussels": "Belgium",
    "vienna": "Austria",
    "zurich": "Switzerland",
    "stockholm": "Sweden",
    "oslo": "Norway",
    "copenhagen": "Denmark",
    "helsinki": "Finland",
    "dublin": "Ireland",
    "lisbon": "Portugal",
    "athens": "Greece",
    "warsaw": "Poland",
    "prague": "Czech Republic",
    "budapest": "Hungary",
    "bangkok": "Thailand",
    "singapore": "Singapore",
    "kuala lumpur": "Malaysia",
    "jakarta": "Indonesia",
    "manila": "Philippines",
    "hanoi": "Vietnam",
    "ho chi minh city": "Vietnam",
    "dubai": "United Arab Emirates",
    "tel aviv": "Israel",
    "istanbul": "Turkey",
    "nairobi": "Kenya",
    "lagos": "Nigeria",
    "johannesburg": "South Africa",
    "cape town": "South Africa",
}

# Common fiscal year start months by country/region
FISCAL_YEAR_STARTS = {
    "US": 10,      # October (federal)
    "UK": 4,       # April
    "India": 4,    # April
    "Australia": 7, # July
    "Japan": 4,    # April
    "default": 1,  # January (calendar year)
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_age_from_dob(dob: Any, reference_date: Optional[date] = None) -> Optional[int]:
    """Calculate age from date of birth.
    
    Args:
        dob: Date of birth (datetime, date, or string)
        reference_date: Reference date for age calculation (default: today)
        
    Returns:
        Age in years or None if invalid
    """
    if pd.isna(dob):
        return None
    
    if reference_date is None:
        reference_date = date.today()
    
    try:
        if isinstance(dob, str):
            # Try common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                try:
                    dob = datetime.strptime(dob, fmt).date()
                    break
                except ValueError:
                    continue
            else:
                return None
        elif isinstance(dob, datetime):
            dob = dob.date()
        elif not isinstance(dob, date):
            return None
        
        age = reference_date.year - dob.year
        # Adjust if birthday hasn't occurred yet this year
        if (reference_date.month, reference_date.day) < (dob.month, dob.day):
            age -= 1
        
        return age if 0 <= age <= 150 else None
    except Exception:
        return None


def concatenate_name_parts(first: Any, middle: Any, last: Any) -> Optional[str]:
    """Concatenate name parts into full name.
    
    Args:
        first: First name
        middle: Middle name (optional)
        last: Last name
        
    Returns:
        Full name or None
    """
    parts = []
    
    if not pd.isna(first) and str(first).strip():
        parts.append(str(first).strip())
    
    if not pd.isna(middle) and str(middle).strip():
        parts.append(str(middle).strip())
    
    if not pd.isna(last) and str(last).strip():
        parts.append(str(last).strip())
    
    return " ".join(parts) if parts else None


def calculate_amount(qty: Any, price: Any) -> Optional[float]:
    """Calculate amount from quantity and price.
    
    Args:
        qty: Quantity
        price: Unit price
        
    Returns:
        Amount (qty × price) or None
    """
    try:
        if pd.isna(qty) or pd.isna(price):
            return None
        
        qty_val = float(qty)
        price_val = float(price)
        
        return round(qty_val * price_val, 2)
    except (ValueError, TypeError):
        return None


def calculate_percentage(numerator: Any, denominator: Any) -> Optional[float]:
    """Calculate percentage from numerator and denominator.
    
    Args:
        numerator: Numerator value
        denominator: Denominator value
        
    Returns:
        Percentage or None
    """
    try:
        if pd.isna(numerator) or pd.isna(denominator):
            return None
        
        num = float(numerator)
        denom = float(denominator)
        
        if denom == 0:
            return None
        
        return round((num / denom) * 100, 2)
    except (ValueError, TypeError):
        return None


def calculate_duration_days(start_date: Any, end_date: Any) -> Optional[int]:
    """Calculate duration in days between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of days or None
    """
    try:
        if pd.isna(start_date) or pd.isna(end_date):
            return None
        
        # Parse dates
        def parse_date(d):
            if isinstance(d, date):
                return d
            if isinstance(d, datetime):
                return d.date()
            if isinstance(d, str):
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d-%m-%Y"]:
                    try:
                        return datetime.strptime(d, fmt).date()
                    except ValueError:
                        continue
            return None
        
        start = parse_date(start_date)
        end = parse_date(end_date)
        
        if start is None or end is None:
            return None
        
        return (end - start).days
    except Exception:
        return None


def interpolate_date(before_date: Any, after_date: Any) -> Optional[date]:
    """Interpolate a date between two surrounding dates.
    
    Args:
        before_date: Date before the missing value
        after_date: Date after the missing value
        
    Returns:
        Midpoint date or None
    """
    try:
        def parse_date(d):
            if isinstance(d, date):
                return d
            if isinstance(d, datetime):
                return d.date()
            if isinstance(d, str):
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(d, fmt).date()
                    except ValueError:
                        continue
            return None
        
        before = parse_date(before_date)
        after = parse_date(after_date)
        
        if before is None or after is None:
            return None
        
        if after < before:
            return None
        
        # Return midpoint
        days_diff = (after - before).days
        midpoint = before + timedelta(days=days_diff // 2)
        return midpoint
    except Exception:
        return None


def linear_interpolate(before_val: Any, after_val: Any) -> Optional[float]:
    """Linear interpolation between two numeric values.
    
    Args:
        before_val: Value before missing
        after_val: Value after missing
        
    Returns:
        Interpolated value or None
    """
    try:
        if pd.isna(before_val) or pd.isna(after_val):
            return None
        
        before = float(before_val)
        after = float(after_val)
        
        return round((before + after) / 2, 2)
    except (ValueError, TypeError):
        return None


def get_country_from_city(city: str) -> Optional[str]:
    """Get country from a uniquely identifying city name.
    
    Args:
        city: City name
        
    Returns:
        Country name or None
    """
    if not city or pd.isna(city):
        return None
    
    city_lower = str(city).strip().lower()
    return UNIQUE_CITY_COUNTRY_MAP.get(city_lower)


def extract_city_from_address(address: str) -> Optional[str]:
    """Extract city from a full address string.
    
    Args:
        address: Full address string
        
    Returns:
        Extracted city or None
    """
    if not address or pd.isna(address):
        return None
    
    address = str(address).strip()
    
    # Common patterns: "Street, City, State ZIP" or "Street, City, Country"
    parts = [p.strip() for p in address.split(',')]
    
    if len(parts) >= 2:
        # City is often the second-to-last part
        potential_city = parts[-2] if len(parts) > 2 else parts[-1]
        # Remove any numbers (ZIP codes)
        potential_city = re.sub(r'\d+', '', potential_city).strip()
        if potential_city and len(potential_city) > 2:
            return potential_city
    
    return None


def get_fiscal_year(date_val: Any, fiscal_start_month: int = 1) -> Optional[int]:
    """Derive fiscal year from a date.
    
    Args:
        date_val: Date value
        fiscal_start_month: Month fiscal year starts (1-12)
        
    Returns:
        Fiscal year or None
    """
    try:
        def parse_date(d):
            if isinstance(d, date):
                return d
            if isinstance(d, datetime):
                return d.date()
            if isinstance(d, str):
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
                    try:
                        return datetime.strptime(d, fmt).date()
                    except ValueError:
                        continue
            return None
        
        dt = parse_date(date_val)
        if dt is None:
            return None
        
        if fiscal_start_month == 1:
            return dt.year
        elif dt.month >= fiscal_start_month:
            return dt.year
        else:
            return dt.year - 1
    except Exception:
        return None


def suggest_next_in_sequence(values: List[Any]) -> Optional[Any]:
    """Suggest next value in a sequential pattern.
    
    Args:
        values: List of existing values
        
    Returns:
        Suggested next value or None
    """
    # Filter non-null values
    valid = [v for v in values if not pd.isna(v)]
    
    if len(valid) < 2:
        return None
    
    # Try numeric sequence
    try:
        nums = [float(v) for v in valid]
        # Check if it's an arithmetic sequence
        diffs = [nums[i+1] - nums[i] for i in range(len(nums)-1)]
        if len(set(round(d, 2) for d in diffs)) == 1:
            # Consistent step
            return nums[-1] + diffs[0]
    except (ValueError, TypeError):
        pass
    
    # Try string sequence (e.g., ID001, ID002, ...)
    try:
        strs = [str(v) for v in valid]
        # Extract numeric suffix
        pattern = re.compile(r'^(.*)(\d+)$')
        matches = [pattern.match(s) for s in strs]
        if all(matches):
            prefixes = [m.group(1) for m in matches]
            numbers = [int(m.group(2)) for m in matches]
            if len(set(prefixes)) == 1:
                # Same prefix, check sequence
                diffs = [numbers[i+1] - numbers[i] for i in range(len(numbers)-1)]
                if len(set(diffs)) == 1 and diffs[0] > 0:
                    next_num = numbers[-1] + diffs[0]
                    # Preserve leading zeros
                    num_width = len(matches[-1].group(2))
                    return f"{prefixes[0]}{str(next_num).zfill(num_width)}"
    except Exception:
        pass
    
    return None


def is_gender_refusal(value: Any) -> bool:
    """Check if value is a valid gender refusal phrase.
    
    Args:
        value: Value to check
        
    Returns:
        True if refusal phrase
    """
    if pd.isna(value):
        return False
    
    cleaned = str(value).strip().lower()
    return cleaned in GENDER_REFUSAL_PHRASES


def calculate_gpa(scores: List[Any], weights: Optional[List[float]] = None) -> Optional[float]:
    """Calculate GPA from component scores.
    
    Args:
        scores: List of individual scores
        weights: Optional weights for each score
        
    Returns:
        Weighted average or None
    """
    try:
        valid_scores = []
        valid_weights = []
        
        for i, score in enumerate(scores):
            if not pd.isna(score):
                valid_scores.append(float(score))
                if weights and i < len(weights):
                    valid_weights.append(weights[i])
                else:
                    valid_weights.append(1.0)
        
        if not valid_scores:
            return None
        
        total_weight = sum(valid_weights)
        weighted_sum = sum(s * w for s, w in zip(valid_scores, valid_weights))
        
        return round(weighted_sum / total_weight, 2)
    except (ValueError, TypeError):
        return None


# ============================================================================
# MAIN CLASS
# ============================================================================

class MissingValueMatrix:
    """Missing Value Decision Matrix engine."""
    
    def __init__(self, job_id: int, df: pd.DataFrame, db,
                 htype_map: Dict[str, str]):
        """Initialize the matrix engine.
        
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
        self.results: List[MissingValueResult] = []
        self.flags: List[Dict[str, Any]] = []
        self.column_summaries: Dict[str, MissingValueSummary] = {}
        
        # Build column type mappings
        self._build_column_maps()
    
    def _build_column_maps(self):
        """Build mappings of columns by type for cross-column operations."""
        self.date_columns: List[str] = []
        self.numeric_columns: List[str] = []
        self.name_columns: Dict[str, str] = {}  # type -> column name
        
        for col, htype in self.htype_map.items():
            if htype in ["HTYPE-013", "HTYPE-014", "HTYPE-015", "HTYPE-016"]:
                self.date_columns.append(col)
            elif htype in ["HTYPE-024", "HTYPE-025", "HTYPE-026", "HTYPE-027", 
                          "HTYPE-028", "HTYPE-029", "HTYPE-030", "HTYPE-031"]:
                self.numeric_columns.append(col)
            
            # Name column detection by HTYPE or column name
            col_lower = col.lower()
            if htype == "HTYPE-001":  # Full Name
                self.name_columns["full_name"] = col
            elif htype == "HTYPE-002" or "first" in col_lower:
                self.name_columns["first_name"] = col
            elif htype == "HTYPE-003" or "last" in col_lower:
                self.name_columns["last_name"] = col
            elif "middle" in col_lower:
                self.name_columns["middle_name"] = col
    
    def add_flag(self, row_idx: int, col: str, scenario: str,
                 message: str, suggested_value: Any = None, 
                 confidence: str = "medium"):
        """Add a flag for user review."""
        self.flags.append({
            "row": row_idx,
            "column": col,
            "scenario": scenario,
            "message": message,
            "suggested_value": suggested_value,
            "confidence": confidence,
            "requires_confirmation": True,
        })
    
    def log_action(self, result: MissingValueResult):
        """Log missing value action to database."""
        try:
            log = CleaningLog(
                job_id=self.job_id,
                action=f"MV-{result.scenario}: {result.column} row {result.row_idx}",
                timestamp=datetime.utcnow(),
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            self.db.rollback()
    
    # ========================================================================
    # SCENARIO HANDLERS
    # ========================================================================
    
    def handle_age_null_dob_present(self, row_idx: int, age_col: str, 
                                     dob_col: str) -> Optional[MissingValueResult]:
        """Handle: Age null, DOB present → Auto-calculate."""
        dob_val = self.df.at[row_idx, dob_col]
        
        if pd.isna(dob_val):
            return None
        
        age = calculate_age_from_dob(dob_val)
        
        if age is not None:
            result = MissingValueResult(
                row_idx=row_idx,
                column=age_col,
                scenario="AGE_FROM_DOB",
                can_predict=True,
                confidence=Confidence.HIGH,
                action=Action.AUTO_FILL,
                predicted_value=age,
                derivation_method="Calculated from date of birth",
                source_columns=[dob_col],
                was_applied=True,
            )
            self.df.at[row_idx, age_col] = age
            return result
        
        return None
    
    def handle_fullname_null_parts_present(self, row_idx: int, 
                                            fullname_col: str) -> Optional[MissingValueResult]:
        """Handle: Full name null, first + last present → Concatenate."""
        first_col = self.name_columns.get("first_name")
        last_col = self.name_columns.get("last_name")
        middle_col = self.name_columns.get("middle_name")
        
        if not first_col and not last_col:
            return None
        
        first = self.df.at[row_idx, first_col] if first_col else None
        last = self.df.at[row_idx, last_col] if last_col else None
        middle = self.df.at[row_idx, middle_col] if middle_col else None
        
        full_name = concatenate_name_parts(first, middle, last)
        
        if full_name:
            source_cols = [c for c in [first_col, middle_col, last_col] if c]
            result = MissingValueResult(
                row_idx=row_idx,
                column=fullname_col,
                scenario="FULLNAME_FROM_PARTS",
                can_predict=True,
                confidence=Confidence.HIGH,
                action=Action.AUTO_FILL,
                predicted_value=full_name,
                derivation_method="Concatenated from name parts",
                source_columns=source_cols,
                was_applied=True,
            )
            self.df.at[row_idx, fullname_col] = full_name
            return result
        
        return None
    
    def handle_amount_null_qty_price_present(self, row_idx: int, amount_col: str,
                                              qty_col: str, price_col: str) -> Optional[MissingValueResult]:
        """Handle: Amount null, qty + price present → Calculate."""
        qty = self.df.at[row_idx, qty_col]
        price = self.df.at[row_idx, price_col]
        
        amount = calculate_amount(qty, price)
        
        if amount is not None:
            result = MissingValueResult(
                row_idx=row_idx,
                column=amount_col,
                scenario="AMOUNT_FROM_QTY_PRICE",
                can_predict=True,
                confidence=Confidence.HIGH,
                action=Action.AUTO_FILL,
                predicted_value=amount,
                derivation_method="qty × price",
                source_columns=[qty_col, price_col],
                was_applied=True,
            )
            self.df.at[row_idx, amount_col] = amount
            return result
        
        return None
    
    def handle_percentage_null(self, row_idx: int, pct_col: str,
                                num_col: str, denom_col: str) -> Optional[MissingValueResult]:
        """Handle: Percentage null, numerator + denominator present → Calculate."""
        num = self.df.at[row_idx, num_col]
        denom = self.df.at[row_idx, denom_col]
        
        pct = calculate_percentage(num, denom)
        
        if pct is not None:
            result = MissingValueResult(
                row_idx=row_idx,
                column=pct_col,
                scenario="PERCENTAGE_CALCULATED",
                can_predict=True,
                confidence=Confidence.HIGH,
                action=Action.AUTO_FILL,
                predicted_value=pct,
                derivation_method="(numerator / denominator) × 100",
                source_columns=[num_col, denom_col],
                was_applied=True,
            )
            self.df.at[row_idx, pct_col] = pct
            return result
        
        return None
    
    def handle_duration_null(self, row_idx: int, duration_col: str,
                              start_col: str, end_col: str) -> Optional[MissingValueResult]:
        """Handle: Duration null, start + end date present → Calculate."""
        start = self.df.at[row_idx, start_col]
        end = self.df.at[row_idx, end_col]
        
        duration = calculate_duration_days(start, end)
        
        if duration is not None:
            result = MissingValueResult(
                row_idx=row_idx,
                column=duration_col,
                scenario="DURATION_CALCULATED",
                can_predict=True,
                confidence=Confidence.HIGH,
                action=Action.AUTO_FILL,
                predicted_value=duration,
                derivation_method="end_date - start_date (days)",
                source_columns=[start_col, end_col],
                was_applied=True,
            )
            self.df.at[row_idx, duration_col] = duration
            return result
        
        return None
    
    def handle_country_null_city_present(self, row_idx: int, country_col: str,
                                          city_col: str) -> Optional[MissingValueResult]:
        """Handle: Country null, city uniquely identifies country → Auto-fill."""
        city = self.df.at[row_idx, city_col]
        country = get_country_from_city(city)
        
        if country:
            result = MissingValueResult(
                row_idx=row_idx,
                column=country_col,
                scenario="COUNTRY_FROM_CITY",
                can_predict=True,
                confidence=Confidence.MEDIUM,
                action=Action.AUTO_FILL,
                predicted_value=country,
                derivation_method="Inferred from unique city name",
                source_columns=[city_col],
                was_applied=True,
            )
            self.df.at[row_idx, country_col] = country
            return result
        
        return None
    
    def handle_city_null_address_present(self, row_idx: int, city_col: str,
                                          address_col: str) -> Optional[MissingValueResult]:
        """Handle: City null, full address present → Extract."""
        address = self.df.at[row_idx, address_col]
        city = extract_city_from_address(address)
        
        if city:
            result = MissingValueResult(
                row_idx=row_idx,
                column=city_col,
                scenario="CITY_FROM_ADDRESS",
                can_predict=True,
                confidence=Confidence.MEDIUM,
                action=Action.SUGGEST,
                predicted_value=city,
                derivation_method="Extracted from full address",
                source_columns=[address_col],
                was_applied=False,
            )
            # Don't auto-apply, just suggest
            self.add_flag(row_idx, city_col, "CITY_FROM_ADDRESS",
                         f"City extracted from address: {city}",
                         city, confidence="medium")
            return result
        
        return None
    
    def handle_date_interpolation(self, row_idx: int, date_col: str) -> Optional[MissingValueResult]:
        """Handle: Date null, sequential dates surround → Suggest interpolated."""
        # Find surrounding non-null dates
        before_val = None
        after_val = None
        
        for i in range(row_idx - 1, -1, -1):
            val = self.df.at[i, date_col]
            if not pd.isna(val):
                before_val = val
                break
        
        for i in range(row_idx + 1, len(self.df)):
            val = self.df.at[i, date_col]
            if not pd.isna(val):
                after_val = val
                break
        
        if before_val is not None and after_val is not None:
            interpolated = interpolate_date(before_val, after_val)
            if interpolated:
                result = MissingValueResult(
                    row_idx=row_idx,
                    column=date_col,
                    scenario="DATE_INTERPOLATED",
                    can_predict=True,
                    confidence=Confidence.MEDIUM,
                    action=Action.SUGGEST,
                    predicted_value=str(interpolated),
                    derivation_method="Interpolated from surrounding dates",
                    source_columns=[date_col],
                    was_applied=False,
                )
                self.add_flag(row_idx, date_col, "DATE_INTERPOLATED",
                             f"Suggested interpolated date: {interpolated}",
                             str(interpolated), confidence="medium")
                return result
        
        return None
    
    def handle_quantity_interpolation(self, row_idx: int, qty_col: str) -> Optional[MissingValueResult]:
        """Handle: Quantity null, sequential trend exists → Linear interpolation."""
        before_val = None
        after_val = None
        
        for i in range(row_idx - 1, -1, -1):
            val = self.df.at[i, qty_col]
            if not pd.isna(val):
                before_val = val
                break
        
        for i in range(row_idx + 1, len(self.df)):
            val = self.df.at[i, qty_col]
            if not pd.isna(val):
                after_val = val
                break
        
        if before_val is not None and after_val is not None:
            interpolated = linear_interpolate(before_val, after_val)
            if interpolated is not None:
                result = MissingValueResult(
                    row_idx=row_idx,
                    column=qty_col,
                    scenario="QUANTITY_INTERPOLATED",
                    can_predict=True,
                    confidence=Confidence.MEDIUM,
                    action=Action.SUGGEST,
                    predicted_value=interpolated,
                    derivation_method="Linear interpolation from trend",
                    source_columns=[qty_col],
                    was_applied=False,
                )
                self.add_flag(row_idx, qty_col, "QUANTITY_INTERPOLATED",
                             f"Suggested interpolated value: {interpolated}",
                             interpolated, confidence="medium")
                return result
        
        return None
    
    def handle_fiscal_year_null(self, row_idx: int, fy_col: str,
                                 date_col: str, fiscal_start: int = 1) -> Optional[MissingValueResult]:
        """Handle: Fiscal year null, date present → Derive."""
        date_val = self.df.at[row_idx, date_col]
        fy = get_fiscal_year(date_val, fiscal_start)
        
        if fy is not None:
            result = MissingValueResult(
                row_idx=row_idx,
                column=fy_col,
                scenario="FISCAL_YEAR_DERIVED",
                can_predict=True,
                confidence=Confidence.HIGH,
                action=Action.AUTO_FILL,
                predicted_value=fy,
                derivation_method=f"Derived from date (fiscal year starts month {fiscal_start})",
                source_columns=[date_col],
                was_applied=True,
            )
            self.df.at[row_idx, fy_col] = fy
            return result
        
        return None
    
    def handle_sequential_id_null(self, row_idx: int, id_col: str) -> Optional[MissingValueResult]:
        """Handle: Student ID null, sequential → Suggest next."""
        # Get all values before this row
        values_before = self.df[id_col].iloc[:row_idx].tolist()
        
        suggested = suggest_next_in_sequence(values_before)
        
        if suggested is not None:
            result = MissingValueResult(
                row_idx=row_idx,
                column=id_col,
                scenario="SEQUENTIAL_ID",
                can_predict=True,
                confidence=Confidence.MEDIUM,
                action=Action.SUGGEST,
                predicted_value=suggested,
                derivation_method="Next value in detected sequence",
                source_columns=[id_col],
                was_applied=False,
            )
            self.add_flag(row_idx, id_col, "SEQUENTIAL_ID",
                         f"Suggested next in sequence: {suggested}",
                         suggested, confidence="medium")
            return result
        
        return None
    
    def handle_gender_refusal(self, row_idx: int, gender_col: str) -> Optional[MissingValueResult]:
        """Handle: Gender cell = refusal phrase → Map to 'Prefer Not to Say'."""
        val = self.df.at[row_idx, gender_col]
        
        if is_gender_refusal(val):
            result = MissingValueResult(
                row_idx=row_idx,
                column=gender_col,
                scenario="GENDER_REFUSAL",
                can_predict=True,
                confidence=Confidence.HIGH,
                action=Action.AUTO_FILL,
                predicted_value="Prefer Not to Say",
                derivation_method="Mapped refusal phrase to standard value",
                source_columns=[gender_col],
                was_applied=True,
            )
            self.df.at[row_idx, gender_col] = "Prefer Not to Say"
            return result
        
        return None
    
    def handle_gpa_from_scores(self, row_idx: int, gpa_col: str,
                                score_cols: List[str]) -> Optional[MissingValueResult]:
        """Handle: GPA null, individual scores present → Calculate."""
        scores = [self.df.at[row_idx, col] for col in score_cols if col in self.df.columns]
        
        gpa = calculate_gpa(scores)
        
        if gpa is not None:
            result = MissingValueResult(
                row_idx=row_idx,
                column=gpa_col,
                scenario="GPA_CALCULATED",
                can_predict=True,
                confidence=Confidence.HIGH,
                action=Action.AUTO_FILL,
                predicted_value=gpa,
                derivation_method="Calculated from component scores",
                source_columns=score_cols,
                was_applied=True,
            )
            self.df.at[row_idx, gpa_col] = gpa
            return result
        
        return None
    
    def handle_prompt_required(self, row_idx: int, col: str, 
                                scenario: str) -> MissingValueResult:
        """Handle: Cannot predict → Prompt user."""
        result = MissingValueResult(
            row_idx=row_idx,
            column=col,
            scenario=scenario,
            can_predict=False,
            confidence=Confidence.NONE,
            action=Action.PROMPT,
            was_applied=False,
        )
        self.add_flag(row_idx, col, scenario,
                     f"Missing value requires manual input",
                     None, confidence="none")
        return result
    
    # ========================================================================
    # COLUMN ANALYZERS
    # ========================================================================
    
    def analyze_column(self, col: str) -> MissingValueSummary:
        """Analyze missing values for a single column."""
        summary = MissingValueSummary(column=col, total_missing=0)
        htype = self.htype_map.get(col, "")
        col_lower = col.lower()
        
        # Find missing rows
        missing_mask = self.df[col].isna()
        missing_indices = self.df.index[missing_mask].tolist()
        summary.total_missing = len(missing_indices)
        
        if summary.total_missing == 0:
            return summary
        
        for row_idx in missing_indices:
            result = None
            
            # ─── Age from DOB ─────────────────────────────────────────
            if htype == "HTYPE-004" or "age" in col_lower:
                # Look for DOB column
                for c, h in self.htype_map.items():
                    if h == "HTYPE-013" or "dob" in c.lower() or "birth" in c.lower():
                        result = self.handle_age_null_dob_present(row_idx, col, c)
                        if result:
                            break
            
            # ─── Full Name from Parts ─────────────────────────────────
            elif htype == "HTYPE-001" or "full" in col_lower and "name" in col_lower:
                result = self.handle_fullname_null_parts_present(row_idx, col)
            
            # ─── Amount from Qty × Price ──────────────────────────────
            elif "amount" in col_lower or "total" in col_lower:
                # Look for qty and price columns
                qty_col = None
                price_col = None
                for c in self.df.columns:
                    c_lower = c.lower()
                    if "qty" in c_lower or "quantity" in c_lower:
                        qty_col = c
                    elif "price" in c_lower or "rate" in c_lower or "unit" in c_lower:
                        price_col = c
                if qty_col and price_col:
                    result = self.handle_amount_null_qty_price_present(
                        row_idx, col, qty_col, price_col)
            
            # ─── Percentage from Numerator/Denominator ────────────────
            elif "percent" in col_lower or "pct" in col_lower or "rate" in col_lower:
                # Look for potential numerator/denominator
                pass  # Would need semantic understanding
            
            # ─── Duration from Start/End ──────────────────────────────
            elif "duration" in col_lower or "days" in col_lower:
                start_col = None
                end_col = None
                for c in self.df.columns:
                    c_lower = c.lower()
                    if "start" in c_lower:
                        start_col = c
                    elif "end" in c_lower:
                        end_col = c
                if start_col and end_col:
                    result = self.handle_duration_null(row_idx, col, start_col, end_col)
            
            # ─── Country from City ────────────────────────────────────
            elif htype == "HTYPE-009" or "country" in col_lower:
                for c, h in self.htype_map.items():
                    if h == "HTYPE-008" or "city" in c.lower():
                        result = self.handle_country_null_city_present(row_idx, col, c)
                        if result:
                            break
            
            # ─── City from Address ────────────────────────────────────
            elif htype == "HTYPE-008" or "city" in col_lower:
                for c, h in self.htype_map.items():
                    if h == "HTYPE-010" or "address" in c.lower():
                        result = self.handle_city_null_address_present(row_idx, col, c)
                        if result:
                            break
            
            # ─── Date Interpolation ───────────────────────────────────
            elif htype in ["HTYPE-013", "HTYPE-014", "HTYPE-015", "HTYPE-016"]:
                result = self.handle_date_interpolation(row_idx, col)
            
            # ─── Quantity/Numeric Interpolation ───────────────────────
            elif htype in ["HTYPE-024", "HTYPE-025", "HTYPE-026"]:
                result = self.handle_quantity_interpolation(row_idx, col)
            
            # ─── Fiscal Year from Date ────────────────────────────────
            elif "fiscal" in col_lower or "fy" in col_lower:
                for c in self.date_columns:
                    result = self.handle_fiscal_year_null(row_idx, col, c)
                    if result:
                        break
            
            # ─── Sequential ID ────────────────────────────────────────
            elif htype in ["HTYPE-005", "HTYPE-035"] or "id" in col_lower:
                result = self.handle_sequential_id_null(row_idx, col)
            
            # ─── Cannot Predict — Prompt User ─────────────────────────
            if result is None:
                scenario = f"{col.upper()}_NULL"
                result = self.handle_prompt_required(row_idx, col, scenario)
            
            # Update summary
            self.results.append(result)
            scenario_key = result.scenario
            summary.scenarios[scenario_key] = summary.scenarios.get(scenario_key, 0) + 1
            
            if result.action == Action.AUTO_FILL:
                summary.auto_filled += 1
            elif result.action == Action.SUGGEST:
                summary.suggested += 1
            elif result.action == Action.PROMPT:
                summary.prompted += 1
            
            if result.was_applied:
                self.log_action(result)
        
        return summary
    
    def analyze_gender_refusals(self, gender_col: str):
        """Analyze and normalize gender refusal phrases."""
        if gender_col not in self.df.columns:
            return
        
        for row_idx in self.df.index:
            val = self.df.at[row_idx, gender_col]
            if not pd.isna(val) and is_gender_refusal(val):
                result = self.handle_gender_refusal(row_idx, gender_col)
                if result:
                    self.results.append(result)
    
    def run_all(self) -> Dict[str, Any]:
        """Run missing value analysis on all columns."""
        total_missing = 0
        total_auto_filled = 0
        total_suggested = 0
        total_prompted = 0
        
        # First pass: handle gender refusals (valid data, not missing)
        for col, htype in self.htype_map.items():
            if htype == "HTYPE-012" or "gender" in col.lower():
                self.analyze_gender_refusals(col)
        
        # Second pass: analyze missing values
        for col in self.df.columns:
            summary = self.analyze_column(col)
            self.column_summaries[col] = summary
            
            total_missing += summary.total_missing
            total_auto_filled += summary.auto_filled
            total_suggested += summary.suggested
            total_prompted += summary.prompted
        
        return {
            "total_missing_values": total_missing,
            "auto_filled": total_auto_filled,
            "suggested_for_review": total_suggested,
            "prompts_required": total_prompted,
            "column_summaries": {
                col: {
                    "total_missing": s.total_missing,
                    "auto_filled": s.auto_filled,
                    "suggested": s.suggested,
                    "prompted": s.prompted,
                    "scenarios": s.scenarios,
                }
                for col, s in self.column_summaries.items()
                if s.total_missing > 0
            },
        }
