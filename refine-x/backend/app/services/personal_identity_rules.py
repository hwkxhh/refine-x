"""
Personal & Identity Rules — Session 4

Implements formula sets for:
- FNAME (14 formulas) — HTYPE-001 Full Name
- SNAME (9 formulas) — HTYPE-002 First/Last/Middle Name
- UID (11 formulas) — HTYPE-003 Unique ID
- AGE (11 formulas) — HTYPE-007 Age
- GEN (8 formulas) — HTYPE-008 Gender

These formulas apply to columns classified under the respective HTYPEs
by the HTYPE Detection Engine (Session 3).
"""

import re
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field

import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from app.models.cleaning_log import CleaningLog


# ============================================================================
# WORD-TO-NUMBER DICTIONARY (Appendix B)
# ============================================================================

WORD_TO_NUMBER: Dict[str, int] = {
    # Basic numbers
    "zero": 0, "oh": 0,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14, "fifteen": 15,
    "sixteen": 16, "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50,
    "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
    "hundred": 100, "thousand": 1000, "million": 1000000, "billion": 1000000000,
}

# Common typos mapped to correct words
WORD_TYPOS: Dict[str, str] = {
    # Zero variants
    "zeroo": "zero", "zer0": "zero",
    # One variants
    "won": "one", "wun": "one",
    # Two variants
    "too": "two", "tow": "two",
    # Three variants
    "thee": "three", "thre": "three",
    # Four variants
    "fore": "four", "fo": "four", "fourty": "forty",
    # Five variants
    "fiv": "five", "fife": "five", "fiveteen": "fifteen",
    # Six variants
    "sic": "six", "sixt": "six",
    # Seven variants
    "sven": "seven", "sevn": "seven",
    # Eight variants
    "eigt": "eight", "eigth": "eight",
    # Nine variants
    "nien": "nine", "nne": "nine",
    # Ten variants
    "tem": "ten",
    # Eleven variants
    "elven": "eleven", "elevan": "eleven", "elevn": "eleven",
    # Twelve variants
    "twleve": "twelve", "twelv": "twelve", "tweve": "twelve",
    # Thirteen variants
    "thirten": "thirteen", "thurteen": "thirteen", "thirtteen": "thirteen",
    # Fourteen variants
    "forteen": "fourteen", "fourten": "fourteen",
    # Fifteen variants
    "fiften": "fifteen",
    # Sixteen variants
    "sixten": "sixteen", "sixtteen": "sixteen",
    # Seventeen variants
    "seventen": "seventeen", "seventten": "seventeen",
    # Eighteen variants
    "eighten": "eighteen", "eightteen": "eighteen",
    # Nineteen variants
    "nineeten": "nineteen", "ninteen": "nineteen",
    # Twenty variants
    "tweny": "twenty", "twentty": "twenty", "twennty": "twenty",
    # Thirty variants
    "thrity": "thirty", "thirthy": "thirty",
    # Forty - common error
    "fourty": "forty",
    # Fifty variants
    "fify": "fifty", "fifthy": "fifty",
    # Sixty variants
    "sixthy": "sixty",
    # Eighty variants
    "eigthy": "eighty",
    # Ninety variants
    "ninty": "ninety",
    # Hundred variants
    "hunderd": "hundred", "hundrerd": "hundred",
}


# ============================================================================
# SALUTATIONS AND SUFFIXES
# ============================================================================

SALUTATIONS = {
    "mr", "mr.", "mister",
    "mrs", "mrs.", "missus",
    "ms", "ms.", "miss",
    "dr", "dr.", "doctor",
    "prof", "prof.", "professor",
    "eng", "eng.", "engineer",
    "rev", "rev.", "reverend",
    "sir",
    "col", "col.", "colonel",
    "capt", "capt.", "captain",
    "mx", "mx.",
}

NAME_SUFFIXES = {
    "jr", "jr.", "junior",
    "sr", "sr.", "senior",
    "ii", "iii", "iv", "v",
    "esq", "esq.", "esquire",
    "phd", "ph.d", "ph.d.",
    "md", "m.d", "m.d.",
}

# Placeholders that should be treated as missing
PLACEHOLDER_PATTERNS = {
    "n/a", "na", "n.a.", "none", "null", "unknown", "test", "xxx",
    "----", "---", "--", "-", ".", "..", "...", "tbd", "pending",
    "not available", "not applicable", "no data", "empty",
}

# Gender mappings
GENDER_MALE = {"male", "m", "man", "boy", "gents", "gentleman", "mr"}
GENDER_FEMALE = {"female", "f", "woman", "girl", "ladies", "lady", "mrs", "ms", "miss"}
GENDER_NON_BINARY = {"non-binary", "nonbinary", "nb", "genderqueer", "genderfluid", "enby"}
GENDER_TRANSGENDER = {"transgender", "trans"}
GENDER_OTHER = {"other", "others"}
GENDER_PREFER_NOT_TO_SAY = {
    "prefer not to say", "prefer not to disclose", "do not want to tell",
    "not willing to share", "decline to state", "rather not say",
    "private", "confidential", "no comment", "undisclosed", "withheld",
}

# Numeric gender codes
GENDER_CODE_MAP = {
    1: "Male", 2: "Female", 3: "Non-Binary", 4: "Prefer Not to Say",
    0: "Other", 9: "Other",
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def word_to_number(text: str) -> Optional[int]:
    """
    Convert written number words to integer.
    Handles: "twenty five", "twenty-five", "one hundred and twenty", etc.
    """
    if not text or not isinstance(text, str):
        return None
    
    text = text.lower().strip()
    
    # Direct lookup
    if text in WORD_TO_NUMBER:
        return WORD_TO_NUMBER[text]
    
    # Check typos
    if text in WORD_TYPOS:
        corrected = WORD_TYPOS[text]
        if corrected in WORD_TO_NUMBER:
            return WORD_TO_NUMBER[corrected]
    
    # Parse compound numbers like "twenty five" or "twenty-five"
    text = text.replace("-", " ").replace(" and ", " ")
    words = text.split()
    
    if not words:
        return None
    
    # Correct typos in each word
    corrected_words = []
    for word in words:
        if word in WORD_TYPOS:
            corrected_words.append(WORD_TYPOS[word])
        else:
            corrected_words.append(word)
    
    # Parse the number
    total = 0
    current = 0
    
    for word in corrected_words:
        if word not in WORD_TO_NUMBER:
            return None  # Unknown word
        
        value = WORD_TO_NUMBER[word]
        
        if value == 100:
            current = (current or 1) * 100
        elif value == 1000:
            current = (current or 1) * 1000
            total += current
            current = 0
        elif value == 1000000:
            current = (current or 1) * 1000000
            total += current
            current = 0
        elif value == 1000000000:
            current = (current or 1) * 1000000000
            total += current
            current = 0
        else:
            current += value
    
    return total + current


def is_placeholder(value: Any) -> bool:
    """Check if a value is a placeholder that should be treated as missing."""
    if pd.isna(value):
        return True
    
    if not isinstance(value, str):
        return False
    
    normalized = value.lower().strip()
    return normalized in PLACEHOLDER_PATTERNS


def strip_salutation(name: str) -> Tuple[str, Optional[str]]:
    """
    Remove salutation from the beginning of a name.
    Returns: (cleaned_name, salutation_found)
    """
    if not name:
        return name, None
    
    words = name.split()
    if not words:
        return name, None
    
    first_word = words[0].lower().rstrip(".")
    if first_word in SALUTATIONS or f"{first_word}." in SALUTATIONS:
        salutation = words[0]
        cleaned = " ".join(words[1:])
        return cleaned.strip(), salutation
    
    return name, None


def extract_suffix(name: str) -> Tuple[str, Optional[str]]:
    """
    Extract suffix from the end of a name.
    Returns: (name_without_suffix, suffix)
    """
    if not name:
        return name, None
    
    words = name.split()
    if len(words) < 2:
        return name, None
    
    last_word = words[-1].lower().rstrip(".,")
    if last_word in NAME_SUFFIXES or f"{last_word}." in NAME_SUFFIXES:
        suffix = words[-1]
        cleaned = " ".join(words[:-1])
        return cleaned.strip(), suffix
    
    return name, None


def normalize_name_case(name: str) -> str:
    """
    Convert name to title case, handling special cases like O'Brien, McDonald.
    """
    if not name:
        return name
    
    # Handle special prefixes
    def title_word(word: str) -> str:
        # Handle apostrophe names (O'Brien)
        if "'" in word:
            parts = word.split("'")
            return "'".join(p.capitalize() for p in parts)
        # Handle hyphenated names (Al-Hassan)
        if "-" in word:
            parts = word.split("-")
            return "-".join(p.capitalize() for p in parts)
        # Handle Mc/Mac prefixes
        lower = word.lower()
        if lower.startswith("mc") and len(word) > 2:
            return "Mc" + word[2:].capitalize()
        if lower.startswith("mac") and len(word) > 3:
            return "Mac" + word[3:].capitalize()
        return word.capitalize()
    
    words = name.split()
    return " ".join(title_word(w) for w in words)


def clean_whitespace(text: str) -> str:
    """Remove extra whitespace and normalize spacing."""
    if not text:
        return text
    # Collapse multiple spaces and strip
    return " ".join(text.split())


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings."""
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


def detect_name_swap(name: str) -> Tuple[bool, str]:
    """
    Detect "Last, First" format and swap to "First Last".
    Returns: (was_swapped, corrected_name)
    """
    if not name or "," not in name:
        return False, name
    
    parts = name.split(",", 1)
    if len(parts) == 2:
        last = parts[0].strip()
        first = parts[1].strip()
        if first and last:
            return True, f"{first} {last}"
    
    return False, name


def calculate_numeric_ratio(value: str) -> float:
    """Calculate the ratio of digits to total characters."""
    if not value:
        return 0.0
    digits = sum(1 for c in value if c.isdigit())
    return digits / len(value) if len(value) > 0 else 0.0


def is_initials_only(name: str) -> bool:
    """Check if name consists only of initials like 'J.D.' or 'A. B. C.'"""
    if not name:
        return False
    # Pattern: one or more capital letter + period sequences
    cleaned = name.replace(" ", "")
    return bool(re.match(r'^([A-Z]\.)+$', cleaned))


# ============================================================================
# FORMULA CLASSES
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


class PersonalIdentityRules:
    """
    Applies personal and identity data cleaning rules based on HTYPE classification.
    """
    
    def __init__(
        self,
        job_id: int,
        df: pd.DataFrame,
        db: Session,
        htype_map: Dict[str, str],
    ):
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.htype_map = htype_map
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
        
        # Log each change individually (CleaningLog uses single row_index)
        for i, idx in enumerate(row_indices[:100]):  # Limit logged entries
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
            "affected_rows": affected_rows[:50],  # Limit for UI
            "affected_count": len(affected_rows),
            "suggested_action": suggested_action,
            "details": details or {},
        })
    
    # ========================================================================
    # FNAME FORMULAS — Full Name (HTYPE-001)
    # ========================================================================
    
    def FNAME_01_title_case(self, col: str) -> CleaningResult:
        """Convert names to title case."""
        result = CleaningResult(column=col, formula_id="FNAME-01")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            normalized = normalize_name_case(val)
            if normalized != val:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(normalized)
                self.df.at[idx, col] = normalized
        
        if changed_indices:
            self._log("FNAME-01", col, "Title case normalization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FNAME_02_whitespace_removal(self, col: str) -> CleaningResult:
        """Remove extra whitespace from names."""
        result = CleaningResult(column=col, formula_id="FNAME-02")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            cleaned = clean_whitespace(val)
            if cleaned != val:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(cleaned)
                self.df.at[idx, col] = cleaned
        
        if changed_indices:
            self._log("FNAME-02", col, "Extra whitespace removal",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FNAME_03_salutation_stripping(self, col: str) -> CleaningResult:
        """Remove salutations from names."""
        result = CleaningResult(column=col, formula_id="FNAME-03")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            cleaned, salutation = strip_salutation(val)
            if salutation and cleaned:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(cleaned)
                self.df.at[idx, col] = cleaned
        
        if changed_indices:
            self._log("FNAME-03", col, "Salutation stripping",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FNAME_04_special_char_filter(self, col: str) -> CleaningResult:
        """Remove invalid special characters, keeping hyphens and apostrophes."""
        result = CleaningResult(column=col, formula_id="FNAME-04")
        
        # Valid characters: letters, spaces, hyphens, apostrophes
        valid_pattern = re.compile(r"[^A-Za-z '\-]")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            cleaned = valid_pattern.sub("", val)
            cleaned = clean_whitespace(cleaned)
            
            if cleaned != val:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(cleaned)
                self.df.at[idx, col] = cleaned
        
        if changed_indices:
            self._log("FNAME-04", col, "Special character removal",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FNAME_05_numeric_rejection(self, col: str) -> CleaningResult:
        """Flag names with >30% numeric content (ask-first)."""
        result = CleaningResult(column=col, formula_id="FNAME-05", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            if calculate_numeric_ratio(val) > 0.3:
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "FNAME-05", col,
                "Names contain >30% numeric characters",
                flagged_indices,
                "Review and correct or mark as invalid",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def FNAME_06_placeholder_detection(self, col: str) -> CleaningResult:
        """Treat placeholder values as missing (auto)."""
        result = CleaningResult(column=col, formula_id="FNAME-06")
        
        changed_indices = []
        before_vals = []
        
        for idx, val in self.df[col].items():
            if is_placeholder(val):
                if not pd.isna(val):  # Only log if actually changing
                    changed_indices.append(idx)
                    before_vals.append(val)
                    self.df.at[idx, col] = np.nan
        
        if changed_indices:
            self._log("FNAME-06", col, "Placeholder to null conversion",
                     changed_indices, before_vals, [None] * len(before_vals))
            result.changes_made = len(changed_indices)
        
        return result
    
    def FNAME_07_duplicate_detection(self, col: str) -> CleaningResult:
        """Flag duplicate names for review (ask-first)."""
        result = CleaningResult(column=col, formula_id="FNAME-07", was_auto_applied=False)
        
        # Find duplicates
        name_counts = self.df[col].value_counts()
        duplicates = name_counts[name_counts > 1]
        
        if len(duplicates) > 0:
            dup_names = duplicates.index.tolist()
            flagged_indices = self.df[self.df[col].isin(dup_names)].index.tolist()
            
            self._flag(
                "FNAME-07", col,
                f"Found {len(duplicates)} duplicate name values",
                flagged_indices,
                "Review duplicates - may be valid (same person multiple records) or data issue",
                {
                    "duplicate_names": dup_names[:10],
                    "counts": duplicates.head(10).to_dict()
                }
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def FNAME_08_single_word_alert(self, col: str) -> CleaningResult:
        """Flag single-word names for confirmation (ask-first)."""
        result = CleaningResult(column=col, formula_id="FNAME-08", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            # Single word = no spaces after stripping
            if " " not in val.strip():
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "FNAME-08", col,
                "Single-word names detected (may be valid for some cultures)",
                flagged_indices,
                "Confirm if these are complete names or missing surname",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def FNAME_09_initials_prompt(self, col: str) -> CleaningResult:
        """Flag initial-only names for expansion (ask-first)."""
        result = CleaningResult(column=col, formula_id="FNAME-09", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            if is_initials_only(val):
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "FNAME-09", col,
                "Names contain only initials",
                flagged_indices,
                "Provide full names if available",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def FNAME_10_name_swap(self, col: str) -> CleaningResult:
        """Detect and fix 'Last, First' format (auto)."""
        result = CleaningResult(column=col, formula_id="FNAME-10")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            was_swapped, corrected = detect_name_swap(val)
            if was_swapped:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(corrected)
                self.df.at[idx, col] = corrected
        
        if changed_indices:
            self._log("FNAME-10", col, "Name swap correction (Last, First → First Last)",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def FNAME_11_fuzzy_duplicate(self, col: str) -> CleaningResult:
        """Flag near-duplicate names with Levenshtein ≤ 2 (ask-first)."""
        result = CleaningResult(column=col, formula_id="FNAME-11", was_auto_applied=False)
        
        # Get unique non-null names
        unique_names = self.df[col].dropna().unique().tolist()
        
        if len(unique_names) > 500:
            # Too many to compare - skip or sample
            return result
        
        fuzzy_pairs = []
        seen_pairs: Set[Tuple[str, str]] = set()
        
        for i, name1 in enumerate(unique_names):
            for name2 in unique_names[i+1:]:
                if (name1, name2) in seen_pairs or (name2, name1) in seen_pairs:
                    continue
                
                # Compare normalized versions
                n1 = str(name1).lower().strip()
                n2 = str(name2).lower().strip()
                
                if n1 != n2 and levenshtein_distance(n1, n2) <= 2:
                    fuzzy_pairs.append((name1, name2))
                    seen_pairs.add((name1, name2))
        
        if fuzzy_pairs:
            # Find all rows with these similar names
            affected_names = set()
            for n1, n2 in fuzzy_pairs:
                affected_names.add(n1)
                affected_names.add(n2)
            
            flagged_indices = self.df[self.df[col].isin(affected_names)].index.tolist()
            
            self._flag(
                "FNAME-11", col,
                f"Found {len(fuzzy_pairs)} potential duplicate name pairs (similar spelling)",
                flagged_indices,
                "Review if these are the same person with spelling variations",
                {"similar_pairs": fuzzy_pairs[:10]}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def FNAME_14_suffix_separation(self, col: str) -> CleaningResult:
        """Extract name suffixes to separate column (auto)."""
        result = CleaningResult(column=col, formula_id="FNAME-14")
        
        suffix_col = f"{col}_suffix"
        if suffix_col not in self.df.columns:
            # Initialize with object dtype to allow string values
            self.df[suffix_col] = pd.Series([None] * len(self.df), dtype=object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or not isinstance(val, str):
                continue
            
            cleaned, suffix = extract_suffix(val)
            if suffix:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(cleaned)
                self.df.at[idx, col] = cleaned
                self.df.at[idx, suffix_col] = suffix
        
        if changed_indices:
            self._log("FNAME-14", col, f"Suffix extraction to {suffix_col}",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
            result.details["suffix_column_created"] = suffix_col
        
        return result
    
    # ========================================================================
    # SNAME FORMULAS — First/Last/Middle Name (HTYPE-002)
    # ========================================================================
    
    def SNAME_01_title_case(self, col: str) -> CleaningResult:
        """Title case for name components."""
        return self.FNAME_01_title_case(col)  # Same logic
    
    def SNAME_02_whitespace_strip(self, col: str) -> CleaningResult:
        """Strip whitespace from name components."""
        return self.FNAME_02_whitespace_removal(col)  # Same logic
    
    def SNAME_03_salutation_removal(self, col: str) -> CleaningResult:
        """Remove salutations from name components."""
        return self.FNAME_03_salutation_stripping(col)  # Same logic
    
    def SNAME_05_last_name_suffix(self, col: str) -> CleaningResult:
        """Handle suffixes in last name column."""
        return self.FNAME_14_suffix_separation(col)  # Same logic
    
    def SNAME_08_placeholder_rejection(self, col: str) -> CleaningResult:
        """Treat placeholders as missing."""
        return self.FNAME_06_placeholder_detection(col)  # Same logic
    
    # ========================================================================
    # UID FORMULAS — Unique ID (HTYPE-003)
    # ========================================================================
    
    def UID_01_uniqueness_check(self, col: str) -> CleaningResult:
        """Flag duplicate IDs (ask-first - critical)."""
        result = CleaningResult(column=col, formula_id="UID-01", was_auto_applied=False)
        
        # Find duplicates
        id_counts = self.df[col].value_counts()
        duplicates = id_counts[id_counts > 1]
        
        if len(duplicates) > 0:
            dup_ids = duplicates.index.tolist()
            flagged_indices = self.df[self.df[col].isin(dup_ids)].index.tolist()
            
            self._flag(
                "UID-01", col,
                f"CRITICAL: {len(duplicates)} duplicate ID values found",
                flagged_indices,
                "Resolve duplicate IDs - each record must have unique identifier",
                {
                    "duplicate_ids": dup_ids[:20],
                    "counts": duplicates.head(20).to_dict()
                }
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def UID_02_format_standardization(self, col: str) -> CleaningResult:
        """Zero-pad IDs to consistent length (auto)."""
        result = CleaningResult(column=col, formula_id="UID-02")
        
        # First, ensure string type
        self.df[col] = self.df[col].astype(str)
        
        # Find non-null values
        non_null = self.df[col].replace("nan", np.nan).dropna()
        
        if len(non_null) == 0:
            return result
        
        # Check if all are numeric (possibly with prefix)
        # Extract numeric portions
        def extract_prefix_and_number(val: str) -> Tuple[str, str]:
            match = re.match(r'^([A-Za-z]*)(\d+)$', str(val))
            if match:
                return match.group(1), match.group(2)
            return "", val
        
        parts = non_null.apply(extract_prefix_and_number)
        prefixes = parts.apply(lambda x: x[0])
        numbers = parts.apply(lambda x: x[1])
        
        # Check if we have consistent prefix
        unique_prefixes = prefixes.unique()
        if len(unique_prefixes) != 1:
            return result  # Mixed prefixes - handled by UID-03
        
        prefix = unique_prefixes[0]
        
        # Check if numbers have consistent length
        num_lengths = numbers.str.len()
        max_len = num_lengths.max()
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val) or str(val) == "nan":
                continue
            
            p, n = extract_prefix_and_number(str(val))
            if p == prefix and len(n) < max_len:
                padded = prefix + n.zfill(max_len)
                if padded != str(val):
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(padded)
                    self.df.at[idx, col] = padded
        
        if changed_indices:
            self._log("UID-02", col, "Zero-pad format standardization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def UID_03_prefix_consistency(self, col: str) -> CleaningResult:
        """Flag mixed prefix patterns (ask-first)."""
        result = CleaningResult(column=col, formula_id="UID-03", was_auto_applied=False)
        
        # Extract prefixes
        def get_prefix(val):
            if pd.isna(val):
                return None
            match = re.match(r'^([A-Za-z]+)', str(val))
            return match.group(1).upper() if match else ""
        
        prefixes = self.df[col].apply(get_prefix)
        prefix_counts = prefixes.value_counts()
        
        if len(prefix_counts) > 1:
            # Multiple prefixes found
            self._flag(
                "UID-03", col,
                "Mixed ID prefix patterns detected",
                list(range(len(self.df))),  # All rows affected
                "Standardize ID prefixes or confirm mixed patterns are intentional",
                {"prefix_counts": prefix_counts.to_dict()}
            )
            result.rows_flagged = len(self.df)
        
        return result
    
    def UID_04_leading_zero_preservation(self, col: str) -> CleaningResult:
        """Ensure IDs are stored as strings to preserve leading zeros (auto)."""
        result = CleaningResult(column=col, formula_id="UID-04")
        
        # Convert to string
        original_dtype = self.df[col].dtype
        self.df[col] = self.df[col].astype(str)
        
        # Replace 'nan' strings with actual NaN
        self.df[col] = self.df[col].replace("nan", np.nan)
        
        if str(original_dtype) != "object":
            result.changes_made = 1
            result.details["original_dtype"] = str(original_dtype)
        
        return result
    
    def UID_05_null_id_detection(self, col: str) -> CleaningResult:
        """Flag null IDs as critical (ask-first)."""
        result = CleaningResult(column=col, formula_id="UID-05", was_auto_applied=False)
        
        null_mask = self.df[col].isna() | (self.df[col].astype(str) == "nan")
        null_indices = self.df[null_mask].index.tolist()
        
        if null_indices:
            self._flag(
                "UID-05", col,
                f"CRITICAL: {len(null_indices)} records have null ID",
                null_indices,
                "Assign unique IDs to these records - ID is required",
            )
            result.rows_flagged = len(null_indices)
        
        return result
    
    def UID_07_data_type_lock(self, col: str) -> CleaningResult:
        """Ensure ID column is string type (auto)."""
        return self.UID_04_leading_zero_preservation(col)  # Same action
    
    def UID_08_special_char_cleaning(self, col: str) -> CleaningResult:
        """Remove unintended spaces/symbols from IDs (auto)."""
        result = CleaningResult(column=col, formula_id="UID-08")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val)
            # Remove spaces and common unwanted symbols
            cleaned = re.sub(r'[\s\-_]+', '', val_str)
            
            if cleaned != val_str:
                changed_indices.append(idx)
                before_vals.append(val_str)
                after_vals.append(cleaned)
                self.df.at[idx, col] = cleaned
        
        if changed_indices:
            self._log("UID-08", col, "Special character removal from IDs",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    # ========================================================================
    # AGE FORMULAS — Age (HTYPE-007)
    # ========================================================================
    
    def AGE_01_word_to_number(self, col: str) -> CleaningResult:
        """Convert written number words to integers (auto)."""
        result = CleaningResult(column=col, formula_id="AGE-01")
        
        # Convert to object dtype first to allow mixed types during conversion
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_str = str(val).strip()
            
            # Skip if already numeric
            try:
                float(val_str)
                continue
            except ValueError:
                pass
            
            # Try word-to-number conversion
            num = word_to_number(val_str)
            if num is not None:
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(num)
                self.df.loc[idx, col] = num
        
        if changed_indices:
            self._log("AGE-01", col, "Word-to-number conversion",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def AGE_03_numeric_validation(self, col: str) -> CleaningResult:
        """Flag non-numeric values after word conversion (ask-first)."""
        result = CleaningResult(column=col, formula_id="AGE-03", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                float(val)
            except (ValueError, TypeError):
                flagged_indices.append(idx)
        
        if flagged_indices:
            self._flag(
                "AGE-03", col,
                "Non-numeric values remain in age column",
                flagged_indices,
                "Correct or remove invalid age values",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def AGE_04_range_check(self, col: str) -> CleaningResult:
        """Flag ages outside 0-120 range (ask-first)."""
        result = CleaningResult(column=col, formula_id="AGE-04", was_auto_applied=False)
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                age = float(val)
                if age < 0 or age > 120:
                    flagged_indices.append(idx)
            except (ValueError, TypeError):
                pass  # Handled by AGE-03
        
        if flagged_indices:
            self._flag(
                "AGE-04", col,
                "Ages outside valid range (0-120)",
                flagged_indices,
                "Review and correct invalid ages",
                {"sample_values": self.df.loc[flagged_indices[:5], col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def AGE_05_decimal_rounding(self, col: str) -> CleaningResult:
        """Round decimal ages appropriately (auto)."""
        result = CleaningResult(column=col, formula_id="AGE-05")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                age = float(val)
                if age != int(age):  # Has decimal
                    if age <= 2:
                        # Infants: keep 1 decimal
                        rounded = round(age, 1)
                    else:
                        # Others: round to integer
                        rounded = round(age)
                    
                    if rounded != age:
                        changed_indices.append(idx)
                        before_vals.append(val)
                        after_vals.append(rounded)
                        self.df.at[idx, col] = rounded
            except (ValueError, TypeError):
                pass
        
        if changed_indices:
            self._log("AGE-05", col, "Decimal age rounding",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def AGE_09_negative_rejection(self, col: str) -> CleaningResult:
        """Flag negative ages (ask-first - critical)."""
        result = CleaningResult(column=col, formula_id="AGE-09", was_auto_applied=False)
        
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
                "AGE-09", col,
                "CRITICAL: Negative age values detected",
                flagged_indices,
                "Correct negative ages - these are invalid",
                {"values": self.df.loc[flagged_indices, col].tolist()}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    def AGE_10_string_to_int(self, col: str) -> CleaningResult:
        """Convert string ages to integers (auto)."""
        result = CleaningResult(column=col, formula_id="AGE-10")
        
        # Convert to object dtype to allow type changes
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                if isinstance(val, str):
                    # Use round() to properly round decimal values
                    num = round(float(val))
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(num)
                    self.df.loc[idx, col] = num
            except (ValueError, TypeError):
                pass
        
        if changed_indices:
            self._log("AGE-10", col, "String to integer conversion",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    # ========================================================================
    # GEN FORMULAS — Gender (HTYPE-008)
    # ========================================================================
    
    def GEN_01_binary_standardization(self, col: str) -> CleaningResult:
        """Standardize male/female variants (auto)."""
        result = CleaningResult(column=col, formula_id="GEN-01")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_lower = str(val).lower().strip()
            new_val = None
            
            if val_lower in GENDER_MALE:
                new_val = "Male"
            elif val_lower in GENDER_FEMALE:
                new_val = "Female"
            
            if new_val and new_val != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(new_val)
                self.df.at[idx, col] = new_val
        
        if changed_indices:
            self._log("GEN-01", col, "Binary gender standardization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def GEN_02_nonbinary_standardization(self, col: str) -> CleaningResult:
        """Standardize non-binary and other categories (auto)."""
        result = CleaningResult(column=col, formula_id="GEN-02")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_lower = str(val).lower().strip()
            new_val = None
            
            if val_lower in GENDER_NON_BINARY:
                new_val = "Non-Binary"
            elif val_lower in GENDER_TRANSGENDER:
                new_val = "Transgender"
            elif val_lower in GENDER_OTHER:
                new_val = "Other"
            
            if new_val and new_val != str(val):
                changed_indices.append(idx)
                before_vals.append(val)
                after_vals.append(new_val)
                self.df.at[idx, col] = new_val
        
        if changed_indices:
            self._log("GEN-02", col, "Non-binary/other gender standardization",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def GEN_03_refusal_mapping(self, col: str) -> CleaningResult:
        """Map refusal phrases to 'Prefer Not to Say' - valid data, not missing (auto)."""
        result = CleaningResult(column=col, formula_id="GEN-03")
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            val_lower = str(val).lower().strip()
            
            if val_lower in GENDER_PREFER_NOT_TO_SAY:
                if str(val) != "Prefer Not to Say":
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append("Prefer Not to Say")
                    self.df.at[idx, col] = "Prefer Not to Say"
        
        if changed_indices:
            self._log("GEN-03", col, "Refusal phrase standardization (valid data)",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def GEN_04_numeric_code_mapping(self, col: str) -> CleaningResult:
        """Map numeric codes to gender labels (auto)."""
        result = CleaningResult(column=col, formula_id="GEN-04")
        
        # Convert to object dtype to allow mixed types
        self.df[col] = self.df[col].astype(object)
        
        changed_indices = []
        before_vals = []
        after_vals = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            try:
                code = int(float(val))
                if code in GENDER_CODE_MAP:
                    new_val = GENDER_CODE_MAP[code]
                    changed_indices.append(idx)
                    before_vals.append(val)
                    after_vals.append(new_val)
                    self.df.loc[idx, col] = new_val
            except (ValueError, TypeError):
                pass
        
        if changed_indices:
            self._log("GEN-04", col, "Numeric gender code mapping",
                     changed_indices, before_vals, after_vals)
            result.changes_made = len(changed_indices)
        
        return result
    
    def GEN_05_invalid_flagging(self, col: str) -> CleaningResult:
        """Flag unrecognized gender values (ask-first)."""
        result = CleaningResult(column=col, formula_id="GEN-05", was_auto_applied=False)
        
        # Valid values after standardization
        valid_values = {"Male", "Female", "Non-Binary", "Transgender", "Other", "Prefer Not to Say"}
        
        flagged_indices = []
        
        for idx, val in self.df[col].items():
            if pd.isna(val):
                continue
            
            if str(val) not in valid_values:
                flagged_indices.append(idx)
        
        if flagged_indices:
            invalid_values = self.df.loc[flagged_indices, col].unique().tolist()
            self._flag(
                "GEN-05", col,
                "Unrecognized gender values",
                flagged_indices,
                "Review and standardize or confirm custom categories",
                {"invalid_values": invalid_values[:10]}
            )
            result.rows_flagged = len(flagged_indices)
        
        return result
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_for_column(self, col: str, htype: str) -> List[CleaningResult]:
        """Run all applicable formulas for a column based on its HTYPE."""
        results = []
        
        if htype == "HTYPE-001":  # Full Name
            # Auto formulas (order matters)
            results.append(self.FNAME_02_whitespace_removal(col))
            results.append(self.FNAME_06_placeholder_detection(col))
            results.append(self.FNAME_03_salutation_stripping(col))
            results.append(self.FNAME_10_name_swap(col))
            results.append(self.FNAME_04_special_char_filter(col))
            results.append(self.FNAME_01_title_case(col))
            results.append(self.FNAME_14_suffix_separation(col))
            # Ask-first formulas (flags for review)
            results.append(self.FNAME_05_numeric_rejection(col))
            results.append(self.FNAME_08_single_word_alert(col))
            results.append(self.FNAME_09_initials_prompt(col))
            results.append(self.FNAME_07_duplicate_detection(col))
            results.append(self.FNAME_11_fuzzy_duplicate(col))
        
        elif htype == "HTYPE-002":  # First/Last/Middle Name
            results.append(self.SNAME_02_whitespace_strip(col))
            results.append(self.SNAME_08_placeholder_rejection(col))
            results.append(self.SNAME_03_salutation_removal(col))
            results.append(self.SNAME_01_title_case(col))
            results.append(self.SNAME_05_last_name_suffix(col))
        
        elif htype == "HTYPE-003":  # Unique ID
            results.append(self.UID_04_leading_zero_preservation(col))
            results.append(self.UID_08_special_char_cleaning(col))
            results.append(self.UID_02_format_standardization(col))
            # Ask-first (critical)
            results.append(self.UID_01_uniqueness_check(col))
            results.append(self.UID_05_null_id_detection(col))
            results.append(self.UID_03_prefix_consistency(col))
        
        elif htype == "HTYPE-007":  # Age
            results.append(self.AGE_01_word_to_number(col))
            results.append(self.AGE_10_string_to_int(col))     # Convert strings to int (truncates decimals)
            results.append(self.AGE_05_decimal_rounding(col))  # Round any remaining floats
            # Ask-first
            results.append(self.AGE_09_negative_rejection(col))
            results.append(self.AGE_04_range_check(col))
            results.append(self.AGE_03_numeric_validation(col))
        
        elif htype == "HTYPE-008":  # Gender
            results.append(self.GEN_04_numeric_code_mapping(col))
            results.append(self.GEN_01_binary_standardization(col))
            results.append(self.GEN_02_nonbinary_standardization(col))
            results.append(self.GEN_03_refusal_mapping(col))
            # Ask-first
            results.append(self.GEN_05_invalid_flagging(col))
        
        return results
    
    def run_all(self) -> Dict[str, Any]:
        """
        Run personal identity rules for all columns based on HTYPE classification.
        """
        all_results = []
        formulas_applied = set()
        
        for col, htype in self.htype_map.items():
            if col not in self.df.columns:
                continue
            
            if htype in ("HTYPE-001", "HTYPE-002", "HTYPE-003", "HTYPE-007", "HTYPE-008"):
                col_results = self.run_for_column(col, htype)
                all_results.extend(col_results)
                
                for r in col_results:
                    if r.changes_made > 0 or r.rows_flagged > 0:
                        formulas_applied.add(r.formula_id)
        
        # Commit all logs
        self.db.flush()
        
        return {
            "personal_identity_rules_applied": list(formulas_applied),
            "total_changes": sum(r.changes_made for r in all_results),
            "total_flags": len(self.flags),
            "columns_processed": len([c for c, h in self.htype_map.items() 
                                      if h in ("HTYPE-001", "HTYPE-002", "HTYPE-003", 
                                              "HTYPE-007", "HTYPE-008")]),
        }
