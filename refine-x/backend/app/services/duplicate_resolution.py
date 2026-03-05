"""
Duplicate Record Resolution Protocol — Session 13

Implements the Duplicate Record Resolution Protocol from the Formula Rulebook (Section 53).

Duplicate Types:
1. Exact Duplicate — Every field identical → Auto-remove
2. Partial Duplicate — Key fields match, some differ → User comparison
3. Fuzzy Duplicate — High similarity, no exact match → Flag for review
4. Intentional Repeat — Same entity by design (e.g., orders) → User marks
5. Temporal Duplicate — Same entity in different time periods → User confirms

Logic First. AI Never.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import hashlib

import pandas as pd
import numpy as np

from app.models.cleaning_log import CleaningLog


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class DuplicateType(Enum):
    """Types of duplicate records."""
    EXACT = "exact"
    PARTIAL = "partial"
    FUZZY = "fuzzy"
    INTENTIONAL = "intentional"
    TEMPORAL = "temporal"


class ResolutionAction(Enum):
    """Actions to take for duplicates."""
    AUTO_REMOVE = "auto_remove"
    USER_COMPARE = "user_compare"
    FLAG_REVIEW = "flag_review"
    MARK_INTENTIONAL = "mark_intentional"
    CONFIRM_TEMPORAL = "confirm_temporal"
    OFFER_MERGE = "offer_merge"


@dataclass
class DuplicateGroup:
    """A group of duplicate records."""
    group_id: int
    row_indices: List[int]
    duplicate_type: DuplicateType
    action: ResolutionAction
    key_columns: List[str] = field(default_factory=list)
    similarity_score: float = 1.0
    details: Dict[str, Any] = field(default_factory=dict)
    can_merge: bool = False
    merge_conflicts: List[str] = field(default_factory=list)


@dataclass
class DuplicateSummary:
    """Summary of duplicate detection results."""
    total_duplicates: int = 0
    exact_duplicates: int = 0
    partial_duplicates: int = 0
    fuzzy_duplicates: int = 0
    rows_auto_removed: int = 0
    groups_for_review: int = 0


# ============================================================================
# CONSTANTS
# ============================================================================

# Minimum similarity score to flag as fuzzy duplicate
FUZZY_THRESHOLD = 0.85

# Hard cap on fuzzy comparisons — prevents O(n²) hangs on large files.
# Blocking strategy keeps typical comparisons well under this limit.
MAX_FUZZY_PAIRS = 2_000

# Weights for fuzzy matching components
FUZZY_WEIGHTS = {
    "name": 0.4,
    "id": 0.3,
    "contact": 0.3,
}

# Common phonetic replacements for name matching
PHONETIC_REPLACEMENTS = [
    (r'ph', 'f'),
    (r'ck', 'k'),
    (r'gh', 'g'),
    (r'sch', 'sk'),
    (r'kn', 'n'),
    (r'wr', 'r'),
    (r'wh', 'w'),
    (r'mb', 'm'),
    (r'ae', 'e'),
    (r'ie', 'i'),
    (r'oe', 'o'),
    (r'ue', 'u'),
    (r'y', 'i'),
    (r'[aeiou]+', 'a'),  # Vowel reduction
]


# ============================================================================
# HELPER FUNCTIONS — STRING SIMILARITY
# ============================================================================

def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein edit distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Edit distance (number of insertions, deletions, substitutions)
    """
    if not s1:
        return len(s2) if s2 else 0
    if not s2:
        return len(s1)
    
    m, n = len(s1), len(s2)
    
    # Use only two rows for space efficiency
    prev = list(range(n + 1))
    curr = [0] * (n + 1)
    
    for i in range(1, m + 1):
        curr[0] = i
        for j in range(1, n + 1):
            if s1[i-1] == s2[j-1]:
                curr[j] = prev[j-1]
            else:
                curr[j] = 1 + min(prev[j], curr[j-1], prev[j-1])
        prev, curr = curr, prev
    
    return prev[n]


def levenshtein_similarity(s1: str, s2: str) -> float:
    """Calculate normalized Levenshtein similarity (0-1).
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity score (1.0 = identical, 0.0 = completely different)
    """
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    distance = levenshtein_distance(s1.lower(), s2.lower())
    max_len = max(len(s1), len(s2))
    
    return 1.0 - (distance / max_len)


def phonetic_normalize(name: str) -> str:
    """Apply phonetic normalization to a name.
    
    Args:
        name: Input name
        
    Returns:
        Phonetically normalized name
    """
    if not name:
        return ""
    
    result = name.lower().strip()
    
    # Remove non-alphabetic characters
    result = re.sub(r'[^a-z\s]', '', result)
    
    # Apply phonetic replacements
    for pattern, replacement in PHONETIC_REPLACEMENTS:
        result = re.sub(pattern, replacement, result)
    
    # Remove duplicate letters
    result = re.sub(r'(.)\1+', r'\1', result)
    
    return result


def phonetic_similarity(s1: str, s2: str) -> float:
    """Calculate phonetic similarity between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Phonetic similarity score (0-1)
    """
    norm1 = phonetic_normalize(s1)
    norm2 = phonetic_normalize(s2)
    
    return levenshtein_similarity(norm1, norm2)


def name_similarity(name1: str, name2: str) -> float:
    """Calculate combined name similarity using Levenshtein and phonetic matching.
    
    Args:
        name1: First name
        name2: Second name
        
    Returns:
        Combined similarity score (0-1)
    """
    if not name1 or not name2:
        return 0.0
    
    # Direct similarity
    direct = levenshtein_similarity(name1, name2)
    
    # Phonetic similarity
    phonetic = phonetic_similarity(name1, name2)
    
    # Take the higher of the two
    return max(direct, phonetic)


def token_sort_similarity(s1: str, s2: str) -> float:
    """Calculate token sort ratio — compares words regardless of order.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Token sort similarity (0-1)
    """
    if not s1 or not s2:
        return 0.0
    
    # Split into tokens and sort
    tokens1 = sorted(s1.lower().split())
    tokens2 = sorted(s2.lower().split())
    
    # Rejoin and compare
    sorted1 = " ".join(tokens1)
    sorted2 = " ".join(tokens2)
    
    return levenshtein_similarity(sorted1, sorted2)


# ============================================================================
# HELPER FUNCTIONS — ROW COMPARISON
# ============================================================================

def row_hash(row: pd.Series) -> str:
    """Create a hash of a row for exact duplicate detection.
    
    Args:
        row: DataFrame row
        
    Returns:
        Hash string
    """
    # Convert row to string representation
    values = []
    for val in row:
        if pd.isna(val):
            values.append("__NULL__")
        else:
            values.append(str(val))
    
    row_str = "|".join(values)
    return hashlib.md5(row_str.encode()).hexdigest()


def rows_are_identical(row1: pd.Series, row2: pd.Series) -> bool:
    """Check if two rows are exactly identical.
    
    Args:
        row1: First row
        row2: Second row
        
    Returns:
        True if identical
    """
    if len(row1) != len(row2):
        return False
    
    for v1, v2 in zip(row1, row2):
        # Both null
        if pd.isna(v1) and pd.isna(v2):
            continue
        # One null
        if pd.isna(v1) or pd.isna(v2):
            return False
        # Different values
        if str(v1) != str(v2):
            return False
    
    return True


def get_key_match(row1: pd.Series, row2: pd.Series, 
                  key_columns: List[str]) -> bool:
    """Check if key columns match between two rows.
    
    Args:
        row1: First row
        row2: Second row
        key_columns: List of key column names
        
    Returns:
        True if all key columns match
    """
    for col in key_columns:
        if col not in row1.index or col not in row2.index:
            continue
        
        v1 = row1[col]
        v2 = row2[col]
        
        # Skip if either is null
        if pd.isna(v1) or pd.isna(v2):
            continue
        
        # Must match
        if str(v1).strip().lower() != str(v2).strip().lower():
            return False
    
    return True


def get_differing_columns(row1: pd.Series, row2: pd.Series) -> List[str]:
    """Get list of columns where two rows differ.
    
    Args:
        row1: First row
        row2: Second row
        
    Returns:
        List of differing column names
    """
    diffs = []
    
    for col in row1.index:
        if col not in row2.index:
            diffs.append(col)
            continue
        
        v1 = row1[col]
        v2 = row2[col]
        
        # Both null = same
        if pd.isna(v1) and pd.isna(v2):
            continue
        
        # One null = different
        if pd.isna(v1) or pd.isna(v2):
            diffs.append(col)
            continue
        
        # Compare values
        if str(v1) != str(v2):
            diffs.append(col)
    
    return diffs


def can_merge_rows(row1: pd.Series, row2: pd.Series) -> Tuple[bool, List[str]]:
    """Check if two rows can be merged (complementary missing data).
    
    Args:
        row1: First row
        row2: Second row
        
    Returns:
        Tuple of (can_merge, conflicting_columns)
    """
    conflicts = []
    
    for col in row1.index:
        if col not in row2.index:
            continue
        
        v1 = row1[col]
        v2 = row2[col]
        
        # Both null or both same = OK
        if pd.isna(v1) and pd.isna(v2):
            continue
        
        # One null = complementary, OK
        if pd.isna(v1) or pd.isna(v2):
            continue
        
        # Both have values — check if same
        if str(v1) != str(v2):
            conflicts.append(col)
    
    return len(conflicts) == 0, conflicts


def merge_rows(row1: pd.Series, row2: pd.Series) -> pd.Series:
    """Merge two rows, filling nulls from the other row.
    
    Args:
        row1: First row (takes priority)
        row2: Second row
        
    Returns:
        Merged row
    """
    merged = row1.copy()
    
    for col in row2.index:
        if col in merged.index and pd.isna(merged[col]):
            merged[col] = row2[col]
    
    return merged


# ============================================================================
# HELPER FUNCTIONS — FUZZY MATCHING
# ============================================================================

def calculate_fuzzy_score(row1: pd.Series, row2: pd.Series,
                          name_cols: List[str],
                          id_cols: List[str],
                          contact_cols: List[str]) -> float:
    """Calculate composite fuzzy similarity score.
    
    Args:
        row1: First row
        row2: Second row
        name_cols: Name column names
        id_cols: ID column names
        contact_cols: Contact (email/phone) column names
        
    Returns:
        Composite similarity score (0-1)
    """
    scores = {
        "name": 0.0,
        "id": 0.0,
        "contact": 0.0,
    }
    
    # Name similarity
    if name_cols:
        name_scores = []
        for col in name_cols:
            if col in row1.index and col in row2.index:
                v1 = row1[col]
                v2 = row2[col]
                if not pd.isna(v1) and not pd.isna(v2):
                    # Use token sort for full names
                    if "full" in col.lower() or " " in str(v1):
                        sim = max(name_similarity(str(v1), str(v2)),
                                 token_sort_similarity(str(v1), str(v2)))
                    else:
                        sim = name_similarity(str(v1), str(v2))
                    name_scores.append(sim)
        
        if name_scores:
            scores["name"] = sum(name_scores) / len(name_scores)
    
    # ID similarity
    if id_cols:
        for col in id_cols:
            if col in row1.index and col in row2.index:
                v1 = row1[col]
                v2 = row2[col]
                if not pd.isna(v1) and not pd.isna(v2):
                    if str(v1).strip() == str(v2).strip():
                        scores["id"] = 1.0
                    else:
                        # Partial ID match
                        scores["id"] = levenshtein_similarity(str(v1), str(v2))
                    break
    
    # Contact similarity
    if contact_cols:
        contact_scores = []
        for col in contact_cols:
            if col in row1.index and col in row2.index:
                v1 = row1[col]
                v2 = row2[col]
                if not pd.isna(v1) and not pd.isna(v2):
                    v1_clean = str(v1).strip().lower()
                    v2_clean = str(v2).strip().lower()
                    if v1_clean == v2_clean:
                        contact_scores.append(1.0)
                    else:
                        contact_scores.append(levenshtein_similarity(v1_clean, v2_clean))
        
        if contact_scores:
            scores["contact"] = max(contact_scores)  # Any matching contact is strong signal
    
    # Weighted composite
    composite = (
        scores["name"] * FUZZY_WEIGHTS["name"] +
        scores["id"] * FUZZY_WEIGHTS["id"] +
        scores["contact"] * FUZZY_WEIGHTS["contact"]
    )
    
    return composite


# ============================================================================
# MAIN CLASS
# ============================================================================

class DuplicateResolution:
    """Duplicate Record Resolution Protocol engine."""
    
    def __init__(self, job_id: int, df: pd.DataFrame, db,
                 htype_map: Dict[str, str],
                 key_columns: Optional[List[str]] = None):
        """Initialize the resolution engine.
        
        Args:
            job_id: Upload job ID for logging
            df: DataFrame to process
            db: Database session
            htype_map: Mapping of column names to their HTYPEs
            key_columns: Optional list of key columns for partial duplicate detection
        """
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.htype_map = htype_map
        self.key_columns = key_columns or []
        
        self.groups: List[DuplicateGroup] = []
        self.flags: List[Dict[str, Any]] = []
        self.removed_rows: List[int] = []
        
        # Build column type mappings
        self._build_column_maps()
        
        # Auto-detect key columns if not provided
        if not self.key_columns:
            self._detect_key_columns()
    
    def _build_column_maps(self):
        """Build mappings of columns by type."""
        self.name_columns: List[str] = []
        self.id_columns: List[str] = []
        self.contact_columns: List[str] = []
        self.date_columns: List[str] = []
        
        for col, htype in self.htype_map.items():
            col_lower = col.lower()
            
            # Name columns
            if htype in ["HTYPE-001", "HTYPE-002", "HTYPE-003"]:
                self.name_columns.append(col)
            elif "name" in col_lower and col not in self.name_columns:
                self.name_columns.append(col)
            
            # ID columns
            if htype == "HTYPE-005":
                self.id_columns.append(col)
            elif ("id" in col_lower or "number" in col_lower) and col not in self.id_columns:
                self.id_columns.append(col)
            
            # Contact columns
            if htype in ["HTYPE-006", "HTYPE-007"]:
                self.contact_columns.append(col)
            elif ("email" in col_lower or "phone" in col_lower) and col not in self.contact_columns:
                self.contact_columns.append(col)
            
            # Date columns
            if htype in ["HTYPE-013", "HTYPE-014", "HTYPE-015", "HTYPE-016"]:
                self.date_columns.append(col)
    
    def _detect_key_columns(self):
        """Auto-detect key columns from HTYPE map and column names."""
        # ID columns are usually keys
        for col, htype in self.htype_map.items():
            if htype == "HTYPE-005":  # ID type
                self.key_columns.append(col)
        
        # Also check column names
        for col in self.df.columns:
            col_lower = col.lower()
            if col not in self.key_columns:
                if any(kw in col_lower for kw in ["student_id", "employee_id", "customer_id",
                                                   "user_id", "record_id", "unique_id"]):
                    self.key_columns.append(col)
    
    def add_flag(self, group: DuplicateGroup):
        """Add a flag for user review."""
        self.flags.append({
            "group_id": group.group_id,
            "row_indices": group.row_indices,
            "duplicate_type": group.duplicate_type.value,
            "action": group.action.value,
            "key_columns": group.key_columns,
            "similarity_score": group.similarity_score,
            "can_merge": group.can_merge,
            "merge_conflicts": group.merge_conflicts,
            "details": group.details,
        })
    
    def log_action(self, action: str, details: str):
        """Log action to database."""
        try:
            log = CleaningLog(
                job_id=self.job_id,
                action=f"DUP: {action} - {details}",
                timestamp=datetime.utcnow(),
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            self.db.rollback()
    
    # ========================================================================
    # DETECTION METHODS
    # ========================================================================
    
    def detect_exact_duplicates(self) -> List[DuplicateGroup]:
        """Detect exact duplicate rows (all fields identical).
        
        Returns:
            List of duplicate groups
        """
        groups = []
        
        # Hash all rows
        row_hashes = {}
        for idx in self.df.index:
            h = row_hash(self.df.loc[idx])
            if h not in row_hashes:
                row_hashes[h] = []
            row_hashes[h].append(idx)
        
        # Find duplicates
        group_id = len(self.groups)
        for h, indices in row_hashes.items():
            if len(indices) > 1:
                group = DuplicateGroup(
                    group_id=group_id,
                    row_indices=indices,
                    duplicate_type=DuplicateType.EXACT,
                    action=ResolutionAction.AUTO_REMOVE,
                    similarity_score=1.0,
                    details={
                        "type": "exact",
                        "count": len(indices),
                    },
                )
                groups.append(group)
                group_id += 1
        
        return groups
    
    def detect_partial_duplicates(self) -> List[DuplicateGroup]:
        """Detect partial duplicates (key fields match, some fields differ).
        
        Returns:
            List of duplicate groups
        """
        groups = []
        
        if not self.key_columns:
            return groups
        
        # Group by key columns
        key_groups = defaultdict(list)
        
        for idx in self.df.index:
            row = self.df.loc[idx]
            key_values = []
            for col in self.key_columns:
                if col in row.index:
                    val = row[col]
                    if pd.isna(val):
                        key_values.append("__NULL__")
                    else:
                        key_values.append(str(val).strip().lower())
            
            if key_values and not all(v == "__NULL__" for v in key_values):
                key = tuple(key_values)
                key_groups[key].append(idx)
        
        # Find duplicates
        group_id = len(self.groups)
        for key, indices in key_groups.items():
            if len(indices) > 1:
                # Check if these are exact or partial
                first_row = self.df.loc[indices[0]]
                all_exact = all(
                    rows_are_identical(first_row, self.df.loc[idx])
                    for idx in indices[1:]
                )
                
                if not all_exact:
                    # This is a partial duplicate
                    # Check if rows can be merged
                    can_merge_all = True
                    all_conflicts = []
                    
                    for i in range(len(indices)):
                        for j in range(i + 1, len(indices)):
                            can_m, conflicts = can_merge_rows(
                                self.df.loc[indices[i]],
                                self.df.loc[indices[j]]
                            )
                            if not can_m:
                                can_merge_all = False
                                all_conflicts.extend(conflicts)
                    
                    action = ResolutionAction.OFFER_MERGE if can_merge_all else ResolutionAction.USER_COMPARE
                    
                    group = DuplicateGroup(
                        group_id=group_id,
                        row_indices=indices,
                        duplicate_type=DuplicateType.PARTIAL,
                        action=action,
                        key_columns=self.key_columns,
                        similarity_score=1.0,
                        can_merge=can_merge_all,
                        merge_conflicts=list(set(all_conflicts)),
                        details={
                            "type": "partial",
                            "key_values": list(key),
                            "differing_columns": get_differing_columns(
                                self.df.loc[indices[0]],
                                self.df.loc[indices[1]]
                            ),
                        },
                    )
                    groups.append(group)
                    group_id += 1
        
        return groups
    
    def detect_fuzzy_duplicates(self, 
                                 exclude_indices: Optional[Set[int]] = None) -> List[DuplicateGroup]:
        """Detect fuzzy duplicates using similarity scoring.
        
        Args:
            exclude_indices: Row indices to exclude (already in other groups)
            
        Returns:
            List of duplicate groups
        """
        groups = []
        exclude = exclude_indices or set()

        # Only do fuzzy matching if we have name/contact columns
        if not self.name_columns and not self.contact_columns:
            return groups

        candidates = [idx for idx in self.df.index if idx not in exclude]
        if len(candidates) < 2:
            return groups

        # ── Blocking strategy ─────────────────────────────────────────────
        # Group candidates by the first 3 lowercase characters of the best
        # available block column (first name col, then first contact col).
        # Only rows within the same block are compared — reduces O(n²) to
        # O(n × avg_block_size²) which is << total pairs in practice.
        block_col = next(
            (c for c in self.name_columns + self.contact_columns
             if c in self.df.columns),
            None,
        )
        if block_col:
            blocks: dict = defaultdict(list)
            for idx in candidates:
                raw = self.df.at[idx, block_col]
                key = (
                    str(raw).strip().lower()[:3]
                    if (raw is not None and not pd.isna(raw))
                    else "__null__"
                )
                blocks[key].append(idx)
            block_lists = [b for b in blocks.values() if len(b) >= 2]
        else:
            block_lists = [candidates]

        # ── Compare within blocks, hard-capped at MAX_FUZZY_PAIRS ─────────
        fuzzy_pairs = []
        pairs_checked = 0

        for block in block_lists:
            if pairs_checked >= MAX_FUZZY_PAIRS:
                break
            for i in range(len(block)):
                if pairs_checked >= MAX_FUZZY_PAIRS:
                    break
                for j in range(i + 1, len(block)):
                    if pairs_checked >= MAX_FUZZY_PAIRS:
                        break
                    idx1, idx2 = block[i], block[j]
                    score = calculate_fuzzy_score(
                        self.df.loc[idx1], self.df.loc[idx2],
                        self.name_columns, self.id_columns, self.contact_columns,
                    )
                    if score >= FUZZY_THRESHOLD:
                        fuzzy_pairs.append((idx1, idx2, score))
                    pairs_checked += 1

        # ── Group fuzzy matches ────────────────────────────────────────────
        group_id = len(self.groups)
        processed = set()
        
        for idx1, idx2, score in fuzzy_pairs:
            if idx1 in processed and idx2 in processed:
                continue
            
            # Find all indices in this fuzzy group
            group_indices = {idx1, idx2}
            
            # Expand group with transitively connected pairs
            changed = True
            while changed:
                changed = False
                for i1, i2, _ in fuzzy_pairs:
                    if (i1 in group_indices or i2 in group_indices) and not (i1 in group_indices and i2 in group_indices):
                        group_indices.add(i1)
                        group_indices.add(i2)
                        changed = True
            
            if len(group_indices) > 1:
                processed.update(group_indices)
                
                group = DuplicateGroup(
                    group_id=group_id,
                    row_indices=list(group_indices),
                    duplicate_type=DuplicateType.FUZZY,
                    action=ResolutionAction.FLAG_REVIEW,
                    similarity_score=score,
                    details={
                        "type": "fuzzy",
                        "matching_signals": {
                            "name_columns": self.name_columns,
                            "contact_columns": self.contact_columns,
                        },
                    },
                )
                groups.append(group)
                group_id += 1
        
        return groups
    
    def detect_temporal_duplicates(self) -> List[DuplicateGroup]:
        """Detect temporal duplicates (same entity in different time periods).
        
        Returns:
            List of duplicate groups
        """
        groups = []
        
        if not self.date_columns or not self.key_columns:
            return groups
        
        # This requires user context — we flag potential temporal patterns
        # Group by key columns
        key_groups = defaultdict(list)
        
        for idx in self.df.index:
            row = self.df.loc[idx]
            key_values = []
            for col in self.key_columns:
                if col in row.index:
                    val = row[col]
                    if not pd.isna(val):
                        key_values.append(str(val).strip().lower())
            
            if key_values:
                key = tuple(key_values)
                # Include date info
                date_vals = []
                for dc in self.date_columns:
                    if dc in row.index and not pd.isna(row[dc]):
                        date_vals.append(str(row[dc]))
                
                key_groups[key].append((idx, date_vals))
        
        # Find keys with multiple entries and different dates
        group_id = len(self.groups)
        for key, entries in key_groups.items():
            if len(entries) > 1:
                # Check if dates differ
                all_dates = [e[1] for e in entries]
                unique_dates = set(tuple(d) for d in all_dates if d)
                
                if len(unique_dates) > 1:
                    # Different dates for same key — potential temporal duplicate
                    indices = [e[0] for e in entries]
                    
                    group = DuplicateGroup(
                        group_id=group_id,
                        row_indices=indices,
                        duplicate_type=DuplicateType.TEMPORAL,
                        action=ResolutionAction.CONFIRM_TEMPORAL,
                        key_columns=self.key_columns,
                        details={
                            "type": "temporal",
                            "key_values": list(key),
                            "date_columns": self.date_columns,
                            "note": "Same entity appears with different dates — may be intentional time series",
                        },
                    )
                    groups.append(group)
                    group_id += 1
        
        return groups
    
    # ========================================================================
    # RESOLUTION METHODS
    # ========================================================================
    
    def resolve_exact_duplicates(self, groups: List[DuplicateGroup]) -> int:
        """Auto-remove exact duplicates, keeping first occurrence.
        
        Args:
            groups: List of exact duplicate groups
            
        Returns:
            Number of rows removed
        """
        removed = 0
        
        for group in groups:
            if group.duplicate_type != DuplicateType.EXACT:
                continue
            
            # Keep first, remove rest
            to_remove = group.row_indices[1:]
            
            for idx in to_remove:
                if idx in self.df.index:
                    self.removed_rows.append(idx)
                    removed += 1
            
            self.log_action(
                "EXACT_DUPLICATE_REMOVED",
                f"Removed {len(to_remove)} duplicate rows, kept row {group.row_indices[0]}"
            )
        
        # Actually remove from DataFrame
        self.df = self.df.drop(self.removed_rows, errors='ignore')
        
        return removed
    
    def prepare_merge_suggestion(self, group: DuplicateGroup) -> Optional[Dict[str, Any]]:
        """Prepare a merge suggestion for complementary rows.
        
        Args:
            group: Duplicate group
            
        Returns:
            Merge suggestion dict or None
        """
        if not group.can_merge or len(group.row_indices) < 2:
            return None
        
        # Start with first row
        merged = self.df.loc[group.row_indices[0]].copy()
        
        # Fill nulls from subsequent rows
        for idx in group.row_indices[1:]:
            row = self.df.loc[idx]
            for col in row.index:
                if col in merged.index and pd.isna(merged[col]) and not pd.isna(row[col]):
                    merged[col] = row[col]
        
        return {
            "merged_row": merged.to_dict(),
            "source_rows": group.row_indices,
            "filled_from": {
                idx: [col for col in self.df.loc[idx].index 
                      if not pd.isna(self.df.loc[idx][col]) 
                      and pd.isna(self.df.loc[group.row_indices[0]][col])]
                for idx in group.row_indices[1:]
            },
        }
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_all(self) -> Dict[str, Any]:
        """Run full duplicate detection and resolution.
        
        Returns:
            Summary dict
        """
        summary = DuplicateSummary()
        
        # Step 1: Detect exact duplicates
        exact_groups = self.detect_exact_duplicates()
        self.groups.extend(exact_groups)
        summary.exact_duplicates = sum(len(g.row_indices) - 1 for g in exact_groups)
        
        # Auto-remove exact duplicates
        summary.rows_auto_removed = self.resolve_exact_duplicates(exact_groups)
        
        # Step 2: Detect partial duplicates
        partial_groups = self.detect_partial_duplicates()
        self.groups.extend(partial_groups)
        summary.partial_duplicates = len(partial_groups)
        
        for group in partial_groups:
            # Prepare merge suggestions
            if group.can_merge:
                group.details["merge_suggestion"] = self.prepare_merge_suggestion(group)
            self.add_flag(group)
        
        # Step 3: Detect fuzzy duplicates (exclude rows already in groups)
        already_grouped = set()
        for g in exact_groups + partial_groups:
            already_grouped.update(g.row_indices)

        # Guard: skip fuzzy dedup for large DataFrames — O(n²) would OOM.
        if len(self.df) > 10000:
            self.log_action(
                "FUZZY_DEDUP_SKIPPED",
                f"DataFrame has {len(self.df)} rows (limit: 10,000). "
                "Exact deduplication was still applied.",
            )
            fuzzy_groups = []
        else:
            fuzzy_groups = self.detect_fuzzy_duplicates(exclude_indices=already_grouped)
        self.groups.extend(fuzzy_groups)
        summary.fuzzy_duplicates = len(fuzzy_groups)
        
        for group in fuzzy_groups:
            self.add_flag(group)
        
        # Step 4: Detect temporal duplicates
        temporal_groups = self.detect_temporal_duplicates()
        # Only add if not already in another group
        for group in temporal_groups:
            indices_set = set(group.row_indices)
            if not indices_set.intersection(already_grouped):
                self.groups.append(group)
                self.add_flag(group)
        
        # Calculate totals
        summary.total_duplicates = (
            summary.exact_duplicates + 
            summary.partial_duplicates + 
            summary.fuzzy_duplicates
        )
        summary.groups_for_review = len([
            g for g in self.groups 
            if g.action != ResolutionAction.AUTO_REMOVE
        ])
        
        return {
            "total_duplicates_found": summary.total_duplicates,
            "exact_duplicates": summary.exact_duplicates,
            "partial_duplicates": summary.partial_duplicates,
            "fuzzy_duplicates": summary.fuzzy_duplicates,
            "rows_auto_removed": summary.rows_auto_removed,
            "groups_for_review": summary.groups_for_review,
            "key_columns_used": self.key_columns,
            "groups": [
                {
                    "group_id": g.group_id,
                    "type": g.duplicate_type.value,
                    "action": g.action.value,
                    "row_count": len(g.row_indices),
                    "similarity": g.similarity_score,
                }
                for g in self.groups
            ],
        }
