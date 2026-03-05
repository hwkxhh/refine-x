"""
value_safety.py — Defensive value conversion helpers for the cleaning pipeline.

RULES:
  • Every formula function must call to_native() on raw cell values FIRST.
  • Never call .lower() / .strip() / .replace() on a raw cell value — use to_str() first.
  • Never call float() / int() / bool() directly — use to_float() / to_int() / to_bool().
  • is_null() handles None, float NaN, empty strings, and numpy NA uniformly.
  • All functions are safe to call on ANY Python or numpy type — they never crash.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Core type normalisation
# ─────────────────────────────────────────────────────────────────────────────

def to_native(value):
    """
    Convert any numpy scalar to the equivalent native Python type.
    Leaves native Python types (str, int, float, bool, None) unchanged.
    Converts numpy arrays to lists.
    """
    if value is None:
        return None
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        v = float(value)
        return None if (math.isnan(v) or math.isinf(v)) else v
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    # pandas NA / NaT
    try:
        import pandas as pd
        if isinstance(value, type(pd.NaT)) or pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return value


def is_null(value) -> bool:
    """
    Return True if the value represents a missing / empty / null state.
    Handles: None, float NaN/Inf, numpy NA, empty string, whitespace-only string.
    """
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    if isinstance(value, np.floating) and (np.isnan(value) or np.isinf(value)):
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    # pandas NA
    try:
        import pandas as pd
        if value is pd.NA or value is pd.NaT:
            return True
        if isinstance(value, type(pd.NaT)):
            return True
    except Exception:
        pass
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Safe string conversion
# ─────────────────────────────────────────────────────────────────────────────

def to_str(value) -> Optional[str]:
    """
    Safely convert any value to a stripped string suitable for string operations.
    Returns None if the value is null/empty.

    Usage pattern:
        s = to_str(value)
        if s and s.lower() in {...}:   # always safe
    """
    value = to_native(value)
    if is_null(value):
        return None
    return str(value).strip()


# ─────────────────────────────────────────────────────────────────────────────
# Safe numeric conversions
# ─────────────────────────────────────────────────────────────────────────────

# Characters stripped before numeric parsing
_STRIP_CHARS = str.maketrans("", "", ",$£€¥%()")

def to_float(value) -> Optional[float]:
    """
    Safely convert any value to float.
    Strips common currency symbols, commas, spaces before parsing.
    Returns None if the value is null or cannot be converted.
    """
    value = to_native(value)
    if is_null(value):
        return None
    if isinstance(value, bool):
        return float(value)
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().translate(_STRIP_CHARS).replace(" ", "")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def to_int(value) -> Optional[int]:
    """
    Safely convert any value to int.
    Returns None if the value is null, non-numeric, or has a fractional part.
    """
    f = to_float(value)
    if f is None:
        return None
    if f != int(f):
        return None  # has a decimal component — not a clean integer
    return int(f)


# ─────────────────────────────────────────────────────────────────────────────
# Safe boolean conversion
# ─────────────────────────────────────────────────────────────────────────────

_TRUE_STRINGS  = frozenset({"true", "yes", "y", "1", "on",  "active",  "enabled",  "applicable", "checked"})
_FALSE_STRINGS = frozenset({"false","no",  "n", "0", "off", "inactive","disabled", "not applicable", "unchecked"})


def to_bool(value) -> Optional[bool]:
    """
    Safely convert any value to bool.
    Handles: True/False, 1/0, 1.0/0.0, 'yes'/'no', 'true'/'false', 'y'/'n',
             'on'/'off', 'active'/'inactive', 'enabled'/'disabled'.
    Returns None if the value is null or unrecognisable as boolean.
    Never crashes.
    """
    value = to_native(value)
    if is_null(value):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value == 1:
            return True
        if value == 0:
            return False
        return None
    s = to_str(value)
    if s is None:
        return None
    normalized = s.lower()
    if normalized in _TRUE_STRINGS:
        return True
    if normalized in _FALSE_STRINGS:
        return False
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Column-level safe numeric conversion (avoids the bool-string crash)
# ─────────────────────────────────────────────────────────────────────────────

_BOOL_LIKE = frozenset({"true", "false", "yes", "no", "y", "n"})

def safe_to_numeric_column(series):
    """
    Convert a pandas Series to numeric only when it is safe to do so.

    - If >50 % of non-null values are boolean strings → do NOT convert (it's a
      boolean column, not numeric).  Returns (series_unchanged, 'HTYPE-018').
    - Otherwise, coerce with errors='coerce' (bad values → NaN).
      If ≥80 % converted successfully → return (converted, 'numeric').
      Otherwise → return (series_unchanged, 'string').

    This prevents the 'Invalid value "True" for dtype float64' crash.
    """
    import pandas as pd

    non_null = series.dropna()
    if len(non_null) == 0:
        return series, "empty"

    str_vals = non_null.astype(str).str.strip().str.lower()
    bool_ratio = str_vals.isin(_BOOL_LIKE).mean()
    if bool_ratio > 0.5:
        return series, "HTYPE-018"

    converted = pd.to_numeric(series, errors="coerce")
    conversion_rate = converted.notna().sum() / max(non_null.notna().sum(), 1)
    if conversion_rate >= 0.8:
        return converted, "numeric"

    return series, "string"
