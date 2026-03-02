"""
Cross-Column Conditional Validation Rules — Session 15

Implements the COND formula set from the Formula Rulebook (Section 51).
These rules enforce logical relationships between columns that cannot be
validated by looking at a single column alone.

Formula IDs: COND-01 through COND-12

Logic First. AI Never.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from collections import defaultdict
from enum import Enum

import pandas as pd
import numpy as np

from app.models.cleaning_log import CleaningLog


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"          # Definite logical inconsistency
    WARNING = "warning"      # Possible inconsistency, needs review
    INFO = "info"            # Informational, may be intentional


class ValidationStatus(Enum):
    """Status of validation check."""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"      # Not applicable (columns not present)


@dataclass
class ValidationResult:
    """Result from a single validation check."""
    formula_id: str
    formula_name: str
    status: ValidationStatus
    severity: ValidationSeverity
    affected_rows: List[int] = field(default_factory=list)
    affected_columns: List[str] = field(default_factory=list)
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationSummary:
    """Summary of all validation results."""
    total_checks: int = 0
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    errors: int = 0
    warnings: int = 0


# ============================================================================
# CONSTANTS
# ============================================================================

# Status values that indicate completion/discharge
COMPLETED_STATUSES = {
    "discharged", "completed", "closed", "finished", "ended",
    "terminated", "graduated", "released", "resolved", "done",
}

# Status values that indicate payment
PAID_STATUSES = {
    "paid", "settled", "cleared", "complete", "processed", "confirmed",
}

# Title to gender mapping for consistency check
TITLE_GENDER_MAP = {
    "mr": "male",
    "mr.": "male",
    "mister": "male",
    "sir": "male",
    "ms": "female",
    "ms.": "female",
    "mrs": "female",
    "mrs.": "female",
    "miss": "female",
    "madam": "female",
    "madame": "female",
}

# Country to phone code prefix mapping (simplified)
COUNTRY_PHONE_CODES = {
    "united states": "+1",
    "usa": "+1",
    "us": "+1",
    "canada": "+1",
    "united kingdom": "+44",
    "uk": "+44",
    "india": "+91",
    "australia": "+61",
    "germany": "+49",
    "france": "+33",
    "japan": "+81",
    "china": "+86",
    "nepal": "+977",
    "brazil": "+55",
    "mexico": "+52",
    "south korea": "+82",
    "italy": "+39",
    "spain": "+34",
    "russia": "+7",
    "south africa": "+27",
}

# Status values for active/inactive checking
ACTIVE_STATUSES = {"active", "enabled", "open", "current", "ongoing"}
INACTIVE_STATUSES = {"inactive", "disabled", "closed", "expired", "terminated", "cancelled"}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def normalize_status(value: Any) -> str:
    """Normalize a status value for comparison."""
    if pd.isna(value):
        return ""
    return str(value).strip().lower()


def parse_date(value: Any) -> Optional[date]:
    """Parse a value to date."""
    if pd.isna(value):
        return None
    
    if isinstance(value, (datetime, date)):
        if isinstance(value, datetime):
            return value.date()
        return value
    
    try:
        parsed = pd.to_datetime(value, errors='coerce')
        if pd.isna(parsed):
            return None
        return parsed.date()
    except Exception:
        return None


def calculate_age_from_dob(dob: date, reference_date: Optional[date] = None) -> int:
    """Calculate age from date of birth."""
    if reference_date is None:
        reference_date = date.today()
    
    age = reference_date.year - dob.year
    if (reference_date.month, reference_date.day) < (dob.month, dob.day):
        age -= 1
    
    return age


def extract_phone_prefix(phone: str) -> Optional[str]:
    """Extract country code prefix from phone number."""
    if not phone:
        return None
    
    phone = str(phone).strip()
    
    # Check for + prefix
    if phone.startswith("+"):
        # Extract first few digits after +
        match = re.match(r'\+(\d{1,4})', phone)
        if match:
            return "+" + match.group(1)
    
    # Check for 00 prefix (international)
    if phone.startswith("00"):
        match = re.match(r'00(\d{1,4})', phone)
        if match:
            return "+" + match.group(1)
    
    return None


def find_columns_by_pattern(columns: List[str], patterns: List[str]) -> List[str]:
    """Find columns matching any of the patterns."""
    matches = []
    for col in columns:
        col_lower = col.lower()
        for pattern in patterns:
            if pattern in col_lower:
                matches.append(col)
                break
    return matches


def find_status_column(columns: List[str]) -> Optional[str]:
    """Find the status column."""
    patterns = ["status", "state", "condition"]
    matches = find_columns_by_pattern(columns, patterns)
    return matches[0] if matches else None


def find_date_columns(columns: List[str]) -> List[str]:
    """Find date columns."""
    patterns = ["date", "time", "_at", "_on", "timestamp"]
    return find_columns_by_pattern(columns, patterns)


def find_amount_columns(columns: List[str]) -> List[str]:
    """Find amount/value columns."""
    patterns = ["amount", "total", "price", "cost", "value", "payment", "paid"]
    return find_columns_by_pattern(columns, patterns)


def find_quantity_columns(columns: List[str]) -> List[str]:
    """Find quantity columns."""
    patterns = ["quantity", "qty", "count", "units", "number"]
    return find_columns_by_pattern(columns, patterns)


def find_id_columns(columns: List[str]) -> List[str]:
    """Find ID columns."""
    patterns = ["_id", "id_", "code", "number", "key"]
    return find_columns_by_pattern(columns, patterns)


# ============================================================================
# COND VALIDATION FUNCTIONS
# ============================================================================

def cond_01_status_date_dependency(df: pd.DataFrame,
                                    status_col: str,
                                    date_col: str,
                                    completed_statuses: Optional[Set[str]] = None) -> ValidationResult:
    """COND-01: Status-Date Dependency.
    
    If status indicates completion (e.g., "Discharged"), then the corresponding
    date column (e.g., "discharge_date") must not be null.
    """
    result = ValidationResult(
        formula_id="COND-01",
        formula_name="Status-Date Dependency",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.ERROR,
        affected_columns=[status_col, date_col],
    )
    
    if status_col not in df.columns or date_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {status_col}, {date_col}"
        return result
    
    if completed_statuses is None:
        completed_statuses = COMPLETED_STATUSES
    
    violations = []
    
    for idx in df.index:
        status = normalize_status(df.loc[idx, status_col])
        date_val = df.loc[idx, date_col]
        
        if status in completed_statuses and pd.isna(date_val):
            violations.append(idx)
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows where status indicates completion but date is null"
        result.details = {
            "completed_statuses_checked": list(completed_statuses),
            "sample_violations": violations[:5],
        }
    else:
        result.message = "All completed status rows have corresponding dates"
    
    return result


def cond_02_status_amount_dependency(df: pd.DataFrame,
                                      status_col: str,
                                      amount_col: str,
                                      paid_statuses: Optional[Set[str]] = None) -> ValidationResult:
    """COND-02: Status-Amount Dependency.
    
    If status = "Paid" then amount_paid must be > 0.
    """
    result = ValidationResult(
        formula_id="COND-02",
        formula_name="Status-Amount Dependency",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.ERROR,
        affected_columns=[status_col, amount_col],
    )
    
    if status_col not in df.columns or amount_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {status_col}, {amount_col}"
        return result
    
    if paid_statuses is None:
        paid_statuses = PAID_STATUSES
    
    violations = []
    
    for idx in df.index:
        status = normalize_status(df.loc[idx, status_col])
        amount = df.loc[idx, amount_col]
        
        if status in paid_statuses:
            if pd.isna(amount):
                violations.append(idx)
            else:
                try:
                    if float(amount) <= 0:
                        violations.append(idx)
                except (ValueError, TypeError):
                    violations.append(idx)
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows where status is 'paid' but amount is null/zero/negative"
        result.details = {
            "paid_statuses_checked": list(paid_statuses),
        }
    else:
        result.message = "All paid status rows have positive amounts"
    
    return result


def cond_03_date_sequence_chain(df: pd.DataFrame,
                                 date_columns: List[str]) -> ValidationResult:
    """COND-03: Date Sequence Chain.
    
    Validates that dates are in expected order:
    e.g., application_date ≤ interview_date ≤ offer_date ≤ joining_date
    """
    result = ValidationResult(
        formula_id="COND-03",
        formula_name="Date Sequence Chain",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.ERROR,
        affected_columns=date_columns,
    )
    
    # Filter to columns that exist
    existing_cols = [c for c in date_columns if c in df.columns]
    
    if len(existing_cols) < 2:
        result.status = ValidationStatus.SKIPPED
        result.message = "Need at least 2 date columns for sequence validation"
        return result
    
    violations = []
    violation_details = []
    
    for idx in df.index:
        dates = []
        for col in existing_cols:
            d = parse_date(df.loc[idx, col])
            dates.append((col, d))
        
        # Check sequence
        for i in range(len(dates) - 1):
            col1, date1 = dates[i]
            col2, date2 = dates[i + 1]
            
            if date1 is not None and date2 is not None:
                if date1 > date2:
                    violations.append(idx)
                    violation_details.append({
                        "row": idx,
                        "earlier_col": col1,
                        "earlier_date": str(date1),
                        "later_col": col2,
                        "later_date": str(date2),
                    })
                    break
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = list(set(violations))
        result.message = f"Found {len(violations)} rows with out-of-sequence dates"
        result.details = {
            "sequence_expected": existing_cols,
            "sample_violations": violation_details[:5],
        }
    else:
        result.message = f"All rows follow date sequence: {' ≤ '.join(existing_cols)}"
    
    return result


def cond_04_referential_integrity(df: pd.DataFrame,
                                   foreign_key_col: str,
                                   reference_values: Set[Any]) -> ValidationResult:
    """COND-04: Referential Integrity Check.
    
    Every ID in the main table must exist in the reference set.
    """
    result = ValidationResult(
        formula_id="COND-04",
        formula_name="Referential Integrity Check",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.ERROR,
        affected_columns=[foreign_key_col],
    )
    
    if foreign_key_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Column not found: {foreign_key_col}"
        return result
    
    orphaned_rows = []
    orphaned_values = set()
    
    for idx in df.index:
        val = df.loc[idx, foreign_key_col]
        if not pd.isna(val) and val not in reference_values:
            orphaned_rows.append(idx)
            orphaned_values.add(val)
    
    if orphaned_rows:
        result.status = ValidationStatus.FAILED
        result.affected_rows = orphaned_rows
        result.message = f"Found {len(orphaned_rows)} rows with orphaned references ({len(orphaned_values)} unique values)"
        result.details = {
            "orphaned_values": list(orphaned_values)[:20],
            "reference_count": len(reference_values),
        }
    else:
        result.message = "All references are valid"
    
    return result


def cond_05_age_dob_consistency(df: pd.DataFrame,
                                 age_col: str,
                                 dob_col: str,
                                 tolerance_years: int = 1) -> ValidationResult:
    """COND-05: Age-DOB Consistency.
    
    If both age and dob are present, verifies that age ≈ today − dob.
    Flags discrepancies > tolerance_years.
    """
    result = ValidationResult(
        formula_id="COND-05",
        formula_name="Age-DOB Consistency",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.WARNING,
        affected_columns=[age_col, dob_col],
    )
    
    if age_col not in df.columns or dob_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {age_col}, {dob_col}"
        return result
    
    violations = []
    violation_details = []
    today = date.today()
    
    for idx in df.index:
        age_val = df.loc[idx, age_col]
        dob_val = df.loc[idx, dob_col]
        
        if pd.isna(age_val) or pd.isna(dob_val):
            continue
        
        try:
            stated_age = int(float(age_val))
        except (ValueError, TypeError):
            continue
        
        dob = parse_date(dob_val)
        if dob is None:
            continue
        
        calculated_age = calculate_age_from_dob(dob, today)
        difference = abs(stated_age - calculated_age)
        
        if difference > tolerance_years:
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "stated_age": stated_age,
                "calculated_age": calculated_age,
                "dob": str(dob),
                "difference": difference,
            })
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows where age doesn't match DOB (tolerance: ±{tolerance_years} years)"
        result.details = {
            "tolerance_years": tolerance_years,
            "sample_violations": violation_details[:5],
        }
    else:
        result.message = "All age values are consistent with DOB"
    
    return result


def cond_06_score_pass_consistency(df: pd.DataFrame,
                                    score_col: str,
                                    pass_col: str,
                                    pass_threshold: float = 40.0) -> ValidationResult:
    """COND-06: Score-Pass Consistency.
    
    If score >= threshold, status should be "Pass".
    If score < threshold, status should be "Fail".
    """
    result = ValidationResult(
        formula_id="COND-06",
        formula_name="Score-Pass Consistency",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.ERROR,
        affected_columns=[score_col, pass_col],
    )
    
    if score_col not in df.columns or pass_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {score_col}, {pass_col}"
        return result
    
    violations = []
    violation_details = []
    
    pass_values = {"pass", "passed", "p", "yes", "true", "1"}
    fail_values = {"fail", "failed", "f", "no", "false", "0"}
    
    for idx in df.index:
        score_val = df.loc[idx, score_col]
        pass_val = df.loc[idx, pass_col]
        
        if pd.isna(score_val) or pd.isna(pass_val):
            continue
        
        try:
            score = float(score_val)
        except (ValueError, TypeError):
            continue
        
        status = normalize_status(pass_val)
        
        # Check consistency
        if score >= pass_threshold and status in fail_values:
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "score": score,
                "status": status,
                "expected": "Pass (score >= threshold)",
            })
        elif score < pass_threshold and status in pass_values:
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "score": score,
                "status": status,
                "expected": "Fail (score < threshold)",
            })
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows with score/pass status inconsistency (threshold: {pass_threshold})"
        result.details = {
            "pass_threshold": pass_threshold,
            "sample_violations": violation_details[:5],
        }
    else:
        result.message = "All score/pass values are consistent"
    
    return result


def cond_07_gender_title_consistency(df: pd.DataFrame,
                                      title_col: str,
                                      gender_col: str) -> ValidationResult:
    """COND-07: Gender-Title Consistency.
    
    If title = "Mr." and gender = "Female" — flags possible mismatch.
    Never auto-corrects.
    """
    result = ValidationResult(
        formula_id="COND-07",
        formula_name="Gender-Title Consistency",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.WARNING,  # Warning, not error
        affected_columns=[title_col, gender_col],
    )
    
    if title_col not in df.columns or gender_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {title_col}, {gender_col}"
        return result
    
    violations = []
    violation_details = []
    
    for idx in df.index:
        title_val = df.loc[idx, title_col]
        gender_val = df.loc[idx, gender_col]
        
        if pd.isna(title_val) or pd.isna(gender_val):
            continue
        
        title = normalize_status(title_val)
        gender = normalize_status(gender_val)
        
        # Check title mapping
        if title in TITLE_GENDER_MAP:
            expected_gender = TITLE_GENDER_MAP[title]
            
            # Normalize gender values
            if gender in ["m", "male", "man", "boy"]:
                actual_gender = "male"
            elif gender in ["f", "female", "woman", "girl"]:
                actual_gender = "female"
            else:
                continue  # Can't determine, skip
            
            if expected_gender != actual_gender:
                violations.append(idx)
                violation_details.append({
                    "row": idx,
                    "title": title_val,
                    "gender": gender_val,
                    "expected_gender": expected_gender,
                })
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows with possible title/gender mismatch (review recommended)"
        result.details = {
            "note": "These may be intentional - please review",
            "sample_violations": violation_details[:5],
        }
    else:
        result.message = "All title/gender combinations appear consistent"
    
    return result


def cond_08_country_phone_consistency(df: pd.DataFrame,
                                       country_col: str,
                                       phone_col: str) -> ValidationResult:
    """COND-08: Country-Phone Code Consistency.
    
    If country = "Nepal" but phone starts with +1 (US code) — flags for review.
    """
    result = ValidationResult(
        formula_id="COND-08",
        formula_name="Country-Phone Code Consistency",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.WARNING,
        affected_columns=[country_col, phone_col],
    )
    
    if country_col not in df.columns or phone_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {country_col}, {phone_col}"
        return result
    
    violations = []
    violation_details = []
    
    for idx in df.index:
        country_val = df.loc[idx, country_col]
        phone_val = df.loc[idx, phone_col]
        
        if pd.isna(country_val) or pd.isna(phone_val):
            continue
        
        country = normalize_status(country_val)
        phone = str(phone_val).strip()
        
        # Get expected phone code for country
        expected_code = None
        for c, code in COUNTRY_PHONE_CODES.items():
            if c in country or country in c:
                expected_code = code
                break
        
        if expected_code is None:
            continue  # Unknown country
        
        # Get actual phone prefix
        actual_prefix = extract_phone_prefix(phone)
        
        if actual_prefix and not actual_prefix.startswith(expected_code[:3]):
            # Check if it's a different country code entirely
            # Allow some flexibility for similar codes
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "country": country_val,
                "phone": phone,
                "expected_code": expected_code,
                "actual_prefix": actual_prefix,
            })
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows with possible country/phone code mismatch"
        result.details = {
            "sample_violations": violation_details[:5],
        }
    else:
        result.message = "All country/phone code combinations appear consistent"
    
    return result


def cond_09_quantity_amount_sign(df: pd.DataFrame,
                                  quantity_col: str,
                                  amount_col: str) -> ValidationResult:
    """COND-09: Quantity-Amount Sign Consistency.
    
    If quantity > 0 then amount should also be > 0 (unless returns/credits).
    """
    result = ValidationResult(
        formula_id="COND-09",
        formula_name="Quantity-Amount Sign Consistency",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.WARNING,
        affected_columns=[quantity_col, amount_col],
    )
    
    if quantity_col not in df.columns or amount_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {quantity_col}, {amount_col}"
        return result
    
    violations = []
    violation_details = []
    
    for idx in df.index:
        qty_val = df.loc[idx, quantity_col]
        amt_val = df.loc[idx, amount_col]
        
        if pd.isna(qty_val) or pd.isna(amt_val):
            continue
        
        try:
            qty = float(qty_val)
            amt = float(amt_val)
        except (ValueError, TypeError):
            continue
        
        # Check sign consistency
        if qty > 0 and amt < 0:
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "quantity": qty,
                "amount": amt,
                "issue": "Positive quantity with negative amount",
            })
        elif qty < 0 and amt > 0:
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "quantity": qty,
                "amount": amt,
                "issue": "Negative quantity with positive amount",
            })
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows with quantity/amount sign mismatch (may be returns/credits)"
        result.details = {
            "note": "Sign mismatches may be intentional for returns/credits",
            "sample_violations": violation_details[:5],
        }
    else:
        result.message = "All quantity/amount signs are consistent"
    
    return result


def cond_10_admission_graduation_date(df: pd.DataFrame,
                                       admission_col: str,
                                       graduation_col: str,
                                       min_years: int = 1,
                                       max_years: int = 10) -> ValidationResult:
    """COND-10: Admission-Graduation Date.
    
    Graduation date should be after admission date.
    Typical range 1–10 years. Flags outliers.
    """
    result = ValidationResult(
        formula_id="COND-10",
        formula_name="Admission-Graduation Date",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.ERROR,
        affected_columns=[admission_col, graduation_col],
    )
    
    if admission_col not in df.columns or graduation_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {admission_col}, {graduation_col}"
        return result
    
    violations = []
    violation_details = []
    
    for idx in df.index:
        adm_val = df.loc[idx, admission_col]
        grad_val = df.loc[idx, graduation_col]
        
        if pd.isna(adm_val) or pd.isna(grad_val):
            continue
        
        adm_date = parse_date(adm_val)
        grad_date = parse_date(grad_val)
        
        if adm_date is None or grad_date is None:
            continue
        
        # Check order
        if grad_date < adm_date:
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "admission": str(adm_date),
                "graduation": str(grad_date),
                "issue": "Graduation before admission",
            })
            continue
        
        # Check range
        days_diff = (grad_date - adm_date).days
        years_diff = days_diff / 365.25
        
        if years_diff < min_years or years_diff > max_years:
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "admission": str(adm_date),
                "graduation": str(grad_date),
                "years_between": round(years_diff, 1),
                "issue": f"Duration outside {min_years}-{max_years} year range",
            })
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows with admission/graduation date issues"
        result.details = {
            "expected_range_years": f"{min_years}-{max_years}",
            "sample_violations": violation_details[:5],
        }
    else:
        result.message = "All admission/graduation dates are consistent"
    
    return result


def cond_11_total_equals_sum(df: pd.DataFrame,
                              total_col: str,
                              component_cols: List[str],
                              tolerance: float = 0.01) -> ValidationResult:
    """COND-11: Total = Sum of Components.
    
    Verifies that total = sum of component columns.
    """
    result = ValidationResult(
        formula_id="COND-11",
        formula_name="Total = Sum of Components",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.ERROR,
        affected_columns=[total_col] + component_cols,
    )
    
    if total_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Total column not found: {total_col}"
        return result
    
    existing_components = [c for c in component_cols if c in df.columns]
    if len(existing_components) < 2:
        result.status = ValidationStatus.SKIPPED
        result.message = "Need at least 2 component columns"
        return result
    
    violations = []
    violation_details = []
    
    for idx in df.index:
        total_val = df.loc[idx, total_col]
        
        if pd.isna(total_val):
            continue
        
        try:
            total = float(total_val)
        except (ValueError, TypeError):
            continue
        
        # Sum components
        component_sum = 0.0
        has_all_components = True
        
        for col in existing_components:
            comp_val = df.loc[idx, col]
            if pd.isna(comp_val):
                has_all_components = False
                break
            try:
                component_sum += float(comp_val)
            except (ValueError, TypeError):
                has_all_components = False
                break
        
        if not has_all_components:
            continue
        
        # Check if totals match within tolerance
        if abs(total - component_sum) > tolerance * max(abs(total), 1):
            violations.append(idx)
            violation_details.append({
                "row": idx,
                "total": total,
                "sum_of_components": round(component_sum, 2),
                "difference": round(total - component_sum, 2),
            })
    
    if violations:
        result.status = ValidationStatus.FAILED
        result.affected_rows = violations
        result.message = f"Found {len(violations)} rows where total doesn't equal sum of components"
        result.details = {
            "total_column": total_col,
            "component_columns": existing_components,
            "tolerance": tolerance,
            "sample_violations": violation_details[:5],
        }
    else:
        result.message = "All totals match sum of components"
    
    return result


def cond_12_duplicate_id_conflicting_status(df: pd.DataFrame,
                                             id_col: str,
                                             status_col: str) -> ValidationResult:
    """COND-12: Duplicate ID, Conflicting Status.
    
    Same entity ID with both Active and Inactive status in different rows.
    """
    result = ValidationResult(
        formula_id="COND-12",
        formula_name="Duplicate ID, Conflicting Status",
        status=ValidationStatus.PASSED,
        severity=ValidationSeverity.ERROR,
        affected_columns=[id_col, status_col],
    )
    
    if id_col not in df.columns or status_col not in df.columns:
        result.status = ValidationStatus.SKIPPED
        result.message = f"Required columns not found: {id_col}, {status_col}"
        return result
    
    # Group by ID and collect statuses
    id_statuses = defaultdict(set)
    id_rows = defaultdict(list)
    
    for idx in df.index:
        id_val = df.loc[idx, id_col]
        status_val = df.loc[idx, status_col]
        
        if pd.isna(id_val):
            continue
        
        status = normalize_status(status_val)
        id_statuses[id_val].add(status)
        id_rows[id_val].append(idx)
    
    # Find IDs with conflicting statuses
    conflicts = []
    conflict_details = []
    
    for id_val, statuses in id_statuses.items():
        has_active = bool(statuses.intersection(ACTIVE_STATUSES))
        has_inactive = bool(statuses.intersection(INACTIVE_STATUSES))
        
        if has_active and has_inactive:
            conflicts.extend(id_rows[id_val])
            conflict_details.append({
                "id": id_val,
                "statuses": list(statuses),
                "row_count": len(id_rows[id_val]),
            })
    
    if conflicts:
        result.status = ValidationStatus.FAILED
        result.affected_rows = conflicts
        result.message = f"Found {len(conflict_details)} IDs with conflicting active/inactive statuses"
        result.details = {
            "conflicting_ids": len(conflict_details),
            "total_affected_rows": len(conflicts),
            "sample_conflicts": conflict_details[:5],
        }
    else:
        result.message = "No conflicting statuses found for duplicate IDs"
    
    return result


# ============================================================================
# MAIN CLASS
# ============================================================================

class ConditionalValidation:
    """Cross-Column Conditional Validation engine."""
    
    def __init__(self, job_id: int, df: pd.DataFrame, db,
                 htype_map: Dict[str, str],
                 reference_data: Optional[Dict[str, Set[Any]]] = None,
                 pass_threshold: float = 40.0):
        """Initialize the validation engine.
        
        Args:
            job_id: Upload job ID for logging
            df: DataFrame to validate
            db: Database session
            htype_map: Mapping of column names to their HTYPEs
            reference_data: Optional dict of reference sets for referential integrity
            pass_threshold: Threshold for pass/fail consistency check
        """
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.htype_map = htype_map
        self.reference_data = reference_data or {}
        self.pass_threshold = pass_threshold
        
        self.results: List[ValidationResult] = []
        self.flags: List[Dict[str, Any]] = []
        
        # Build column type mappings
        self._build_column_maps()
    
    def _build_column_maps(self):
        """Build mappings of columns by type from HTYPE map and column names."""
        self.columns = list(self.df.columns)
        
        # Status columns
        self.status_cols = find_columns_by_pattern(self.columns, ["status", "state"])
        
        # Date columns
        self.date_cols = []
        for col, htype in self.htype_map.items():
            if htype in ["HTYPE-013", "HTYPE-014", "HTYPE-015", "HTYPE-016"]:
                self.date_cols.append(col)
        if not self.date_cols:
            self.date_cols = find_date_columns(self.columns)
        
        # Amount columns
        self.amount_cols = []
        for col, htype in self.htype_map.items():
            if htype == "HTYPE-019":  # AMT
                self.amount_cols.append(col)
        if not self.amount_cols:
            self.amount_cols = find_amount_columns(self.columns)
        
        # Quantity columns
        self.quantity_cols = []
        for col, htype in self.htype_map.items():
            if htype == "HTYPE-020":  # QTY
                self.quantity_cols.append(col)
        if not self.quantity_cols:
            self.quantity_cols = find_quantity_columns(self.columns)
        
        # ID columns
        self.id_cols = []
        for col, htype in self.htype_map.items():
            if htype == "HTYPE-005":  # ID
                self.id_cols.append(col)
        if not self.id_cols:
            self.id_cols = find_id_columns(self.columns)
        
        # Age columns
        self.age_cols = find_columns_by_pattern(self.columns, ["age"])
        
        # DOB columns
        self.dob_cols = find_columns_by_pattern(self.columns, ["dob", "birth", "born"])
        
        # Score columns
        self.score_cols = find_columns_by_pattern(self.columns, ["score", "mark", "grade", "point"])
        
        # Pass/fail columns
        self.pass_cols = find_columns_by_pattern(self.columns, ["pass", "result", "outcome"])
        
        # Title columns
        self.title_cols = find_columns_by_pattern(self.columns, ["title", "salutation", "prefix"])
        
        # Gender columns
        self.gender_cols = find_columns_by_pattern(self.columns, ["gender", "sex"])
        
        # Country columns
        self.country_cols = find_columns_by_pattern(self.columns, ["country", "nation"])
        
        # Phone columns
        self.phone_cols = find_columns_by_pattern(self.columns, ["phone", "mobile", "cell", "tel"])
        
        # Total columns
        self.total_cols = find_columns_by_pattern(self.columns, ["total", "sum", "grand"])
    
    def add_flag(self, result: ValidationResult):
        """Add a flag for user review."""
        if result.status == ValidationStatus.FAILED:
            self.flags.append({
                "formula_id": result.formula_id,
                "formula_name": result.formula_name,
                "severity": result.severity.value,
                "affected_rows": result.affected_rows[:20],  # Limit for storage
                "affected_row_count": len(result.affected_rows),
                "affected_columns": result.affected_columns,
                "message": result.message,
                "details": result.details,
            })
    
    def log_action(self, action: str, details: str):
        """Log action to database."""
        try:
            log = CleaningLog(
                job_id=self.job_id,
                action=f"COND: {action} - {details}",
                timestamp=datetime.utcnow(),
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            self.db.rollback()
    
    # ========================================================================
    # VALIDATION METHODS
    # ========================================================================
    
    def run_cond_01(self) -> ValidationResult:
        """Run COND-01: Status-Date Dependency."""
        # Find status and date column pairs
        if not self.status_cols:
            return ValidationResult(
                formula_id="COND-01",
                formula_name="Status-Date Dependency",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="No status column found",
            )
        
        status_col = self.status_cols[0]
        
        # Try to find corresponding date column
        date_col = None
        for dc in self.date_cols:
            if "discharge" in dc.lower() or "complete" in dc.lower() or "end" in dc.lower():
                date_col = dc
                break
        
        if date_col is None and self.date_cols:
            date_col = self.date_cols[-1]  # Use last date column as fallback
        
        if date_col is None:
            return ValidationResult(
                formula_id="COND-01",
                formula_name="Status-Date Dependency",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="No date column found",
            )
        
        result = cond_01_status_date_dependency(self.df, status_col, date_col)
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_02(self) -> ValidationResult:
        """Run COND-02: Status-Amount Dependency."""
        if not self.status_cols or not self.amount_cols:
            return ValidationResult(
                formula_id="COND-02",
                formula_name="Status-Amount Dependency",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="Required columns not found",
            )
        
        result = cond_02_status_amount_dependency(
            self.df, self.status_cols[0], self.amount_cols[0]
        )
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_03(self) -> ValidationResult:
        """Run COND-03: Date Sequence Chain."""
        if len(self.date_cols) < 2:
            return ValidationResult(
                formula_id="COND-03",
                formula_name="Date Sequence Chain",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="Need at least 2 date columns",
            )
        
        # Sort date columns by common naming patterns
        sequence_keywords = [
            "application", "apply", "submit", "start", "begin",
            "interview", "review", "assess",
            "offer", "accept",
            "join", "enroll", "admit", "hire",
            "complete", "graduate", "end", "finish", "discharge",
        ]
        
        def sort_key(col):
            col_lower = col.lower()
            for i, kw in enumerate(sequence_keywords):
                if kw in col_lower:
                    return i
            return len(sequence_keywords)
        
        sorted_date_cols = sorted(self.date_cols, key=sort_key)
        
        result = cond_03_date_sequence_chain(self.df, sorted_date_cols)
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_04(self) -> List[ValidationResult]:
        """Run COND-04: Referential Integrity Check."""
        results = []
        
        for col, ref_set in self.reference_data.items():
            if col in self.df.columns:
                result = cond_04_referential_integrity(self.df, col, ref_set)
                self.results.append(result)
                self.add_flag(result)
                results.append(result)
        
        return results
    
    def run_cond_05(self) -> ValidationResult:
        """Run COND-05: Age-DOB Consistency."""
        if not self.age_cols or not self.dob_cols:
            return ValidationResult(
                formula_id="COND-05",
                formula_name="Age-DOB Consistency",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.WARNING,
                message="Age or DOB column not found",
            )
        
        result = cond_05_age_dob_consistency(
            self.df, self.age_cols[0], self.dob_cols[0]
        )
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_06(self) -> ValidationResult:
        """Run COND-06: Score-Pass Consistency."""
        if not self.score_cols or not self.pass_cols:
            return ValidationResult(
                formula_id="COND-06",
                formula_name="Score-Pass Consistency",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="Score or pass/fail column not found",
            )
        
        result = cond_06_score_pass_consistency(
            self.df, self.score_cols[0], self.pass_cols[0], self.pass_threshold
        )
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_07(self) -> ValidationResult:
        """Run COND-07: Gender-Title Consistency."""
        if not self.title_cols or not self.gender_cols:
            return ValidationResult(
                formula_id="COND-07",
                formula_name="Gender-Title Consistency",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.WARNING,
                message="Title or gender column not found",
            )
        
        result = cond_07_gender_title_consistency(
            self.df, self.title_cols[0], self.gender_cols[0]
        )
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_08(self) -> ValidationResult:
        """Run COND-08: Country-Phone Code Consistency."""
        if not self.country_cols or not self.phone_cols:
            return ValidationResult(
                formula_id="COND-08",
                formula_name="Country-Phone Code Consistency",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.WARNING,
                message="Country or phone column not found",
            )
        
        result = cond_08_country_phone_consistency(
            self.df, self.country_cols[0], self.phone_cols[0]
        )
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_09(self) -> ValidationResult:
        """Run COND-09: Quantity-Amount Sign Consistency."""
        if not self.quantity_cols or not self.amount_cols:
            return ValidationResult(
                formula_id="COND-09",
                formula_name="Quantity-Amount Sign Consistency",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.WARNING,
                message="Quantity or amount column not found",
            )
        
        result = cond_09_quantity_amount_sign(
            self.df, self.quantity_cols[0], self.amount_cols[0]
        )
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_10(self) -> ValidationResult:
        """Run COND-10: Admission-Graduation Date."""
        # Find admission and graduation columns
        admission_col = None
        graduation_col = None
        
        for col in self.date_cols:
            col_lower = col.lower()
            if "admission" in col_lower or "enroll" in col_lower or "start" in col_lower:
                admission_col = col
            if "graduation" in col_lower or "graduate" in col_lower or "complete" in col_lower:
                graduation_col = col
        
        if admission_col is None or graduation_col is None:
            return ValidationResult(
                formula_id="COND-10",
                formula_name="Admission-Graduation Date",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="Admission or graduation date column not found",
            )
        
        result = cond_10_admission_graduation_date(
            self.df, admission_col, graduation_col
        )
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_11(self) -> ValidationResult:
        """Run COND-11: Total = Sum of Components."""
        if not self.total_cols:
            return ValidationResult(
                formula_id="COND-11",
                formula_name="Total = Sum of Components",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="No total column found",
            )
        
        # Find potential component columns
        total_col = self.total_cols[0]
        total_lower = total_col.lower()
        
        # Try to find component columns with similar naming
        component_cols = []
        for col in self.df.columns:
            if col == total_col:
                continue
            col_lower = col.lower()
            # Look for columns that could be components
            if any(kw in col_lower for kw in ["male", "female", "other", "part", "component"]):
                component_cols.append(col)
        
        if len(component_cols) < 2:
            # Try numeric columns
            component_cols = [
                col for col in self.df.columns 
                if col != total_col and pd.api.types.is_numeric_dtype(self.df[col])
            ][:5]  # Limit to 5
        
        if len(component_cols) < 2:
            return ValidationResult(
                formula_id="COND-11",
                formula_name="Total = Sum of Components",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="Not enough component columns found",
            )
        
        result = cond_11_total_equals_sum(self.df, total_col, component_cols)
        self.results.append(result)
        self.add_flag(result)
        return result
    
    def run_cond_12(self) -> ValidationResult:
        """Run COND-12: Duplicate ID, Conflicting Status."""
        if not self.id_cols or not self.status_cols:
            return ValidationResult(
                formula_id="COND-12",
                formula_name="Duplicate ID, Conflicting Status",
                status=ValidationStatus.SKIPPED,
                severity=ValidationSeverity.ERROR,
                message="ID or status column not found",
            )
        
        result = cond_12_duplicate_id_conflicting_status(
            self.df, self.id_cols[0], self.status_cols[0]
        )
        self.results.append(result)
        self.add_flag(result)
        return result
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_all(self) -> Dict[str, Any]:
        """Run all COND validation rules.
        
        Returns:
            Comprehensive validation results
        """
        summary = ValidationSummary()
        
        # Run all COND rules
        self.run_cond_01()
        self.run_cond_02()
        self.run_cond_03()
        self.run_cond_04()
        self.run_cond_05()
        self.run_cond_06()
        self.run_cond_07()
        self.run_cond_08()
        self.run_cond_09()
        self.run_cond_10()
        self.run_cond_11()
        self.run_cond_12()
        
        # Calculate summary
        for result in self.results:
            summary.total_checks += 1
            
            if result.status == ValidationStatus.PASSED:
                summary.passed += 1
            elif result.status == ValidationStatus.FAILED:
                summary.failed += 1
                if result.severity == ValidationSeverity.ERROR:
                    summary.errors += 1
                else:
                    summary.warnings += 1
            else:
                summary.skipped += 1
        
        self.log_action(
            "VALIDATION_COMPLETE",
            f"Ran {summary.total_checks} checks: {summary.passed} passed, "
            f"{summary.failed} failed ({summary.errors} errors, {summary.warnings} warnings), "
            f"{summary.skipped} skipped"
        )
        
        return {
            "total_checks": summary.total_checks,
            "passed": summary.passed,
            "failed": summary.failed,
            "skipped": summary.skipped,
            "errors": summary.errors,
            "warnings": summary.warnings,
            "results": [
                {
                    "formula_id": r.formula_id,
                    "formula_name": r.formula_name,
                    "status": r.status.value,
                    "severity": r.severity.value,
                    "affected_row_count": len(r.affected_rows),
                    "message": r.message,
                }
                for r in self.results
            ],
        }
