"""
Analytical Formula Set (Post-Cleaning) — Session 14

Implements the Analytical Formula Set from the Formula Rulebook (Section 54).
These formulas run after cleaning is complete, producing insights and derived
metrics for visualization and reporting.

Formula IDs: AN-01 through AN-20

Logic First. AI Never.
"""

import re
import math
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

import pandas as pd
import numpy as np

from app.models.cleaning_log import CleaningLog


# ============================================================================
# ENUMS AND DATA CLASSES
# ============================================================================

class TrendDirection(Enum):
    """Trend direction indicators."""
    UP = "up"
    DOWN = "down"
    FLAT = "flat"


class SeasonalityType(Enum):
    """Types of seasonality patterns."""
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    NONE = "none"


@dataclass
class AnalyticalResult:
    """Result from an analytical formula."""
    formula_id: str
    formula_name: str
    column: str
    result: Any
    details: Dict[str, Any] = field(default_factory=dict)
    visualization_type: str = "table"  # table, line, bar, pie, etc.


@dataclass
class TrendResult:
    """Result from trend detection."""
    direction: TrendDirection
    slope: float
    r_squared: float
    confidence: str  # HIGH, MEDIUM, LOW


@dataclass
class CorrelationPair:
    """A pair of correlated columns."""
    column1: str
    column2: str
    correlation: float
    strength: str  # STRONG, MODERATE, WEAK


# ============================================================================
# HELPER FUNCTIONS — STATISTICS
# ============================================================================

def calculate_mean(values: List[float]) -> float:
    """Calculate arithmetic mean."""
    if not values:
        return 0.0
    return sum(values) / len(values)


def calculate_median(values: List[float]) -> float:
    """Calculate median."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    mid = n // 2
    if n % 2 == 0:
        return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2
    return sorted_vals[mid]


def calculate_mode(values: List[float]) -> Optional[float]:
    """Calculate mode (most frequent value)."""
    if not values:
        return None
    counts = defaultdict(int)
    for v in values:
        counts[v] += 1
    max_count = max(counts.values())
    if max_count == 1:
        return None  # No mode
    modes = [k for k, v in counts.items() if v == max_count]
    return modes[0] if modes else None


def calculate_std_dev(values: List[float], sample: bool = True) -> float:
    """Calculate standard deviation."""
    if len(values) < 2:
        return 0.0
    mean = calculate_mean(values)
    squared_diffs = [(x - mean) ** 2 for x in values]
    variance = sum(squared_diffs) / (len(values) - 1 if sample else len(values))
    return math.sqrt(variance)


def calculate_variance(values: List[float], sample: bool = True) -> float:
    """Calculate variance."""
    if len(values) < 2:
        return 0.0
    mean = calculate_mean(values)
    squared_diffs = [(x - mean) ** 2 for x in values]
    return sum(squared_diffs) / (len(values) - 1 if sample else len(values))


def calculate_skewness(values: List[float]) -> float:
    """Calculate skewness (measure of asymmetry)."""
    if len(values) < 3:
        return 0.0
    n = len(values)
    mean = calculate_mean(values)
    std = calculate_std_dev(values, sample=False)
    if std == 0:
        return 0.0
    skew = sum(((x - mean) / std) ** 3 for x in values) * n / ((n - 1) * (n - 2))
    return skew


def calculate_kurtosis(values: List[float]) -> float:
    """Calculate kurtosis (measure of tail heaviness)."""
    if len(values) < 4:
        return 0.0
    n = len(values)
    mean = calculate_mean(values)
    std = calculate_std_dev(values, sample=False)
    if std == 0:
        return 0.0
    kurt = sum(((x - mean) / std) ** 4 for x in values) * n * (n + 1) / ((n - 1) * (n - 2) * (n - 3))
    kurt -= 3 * (n - 1) ** 2 / ((n - 2) * (n - 3))  # Excess kurtosis
    return kurt


def calculate_percentile(values: List[float], p: float) -> float:
    """Calculate percentile (0-100)."""
    if not values:
        return 0.0
    sorted_vals = sorted(values)
    n = len(sorted_vals)
    k = (p / 100) * (n - 1)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return sorted_vals[int(k)]
    return sorted_vals[f] * (c - k) + sorted_vals[c] * (k - f)


def calculate_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    n = len(x)
    mean_x = calculate_mean(x)
    mean_y = calculate_mean(y)
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denom_x = math.sqrt(sum((xi - mean_x) ** 2 for xi in x))
    denom_y = math.sqrt(sum((yi - mean_y) ** 2 for yi in y))
    
    if denom_x == 0 or denom_y == 0:
        return 0.0
    
    return numerator / (denom_x * denom_y)


def linear_regression(x: List[float], y: List[float]) -> Tuple[float, float, float]:
    """Calculate linear regression coefficients.
    
    Returns:
        Tuple of (slope, intercept, r_squared)
    """
    if len(x) != len(y) or len(x) < 2:
        return 0.0, 0.0, 0.0
    
    n = len(x)
    mean_x = calculate_mean(x)
    mean_y = calculate_mean(y)
    
    ss_xy = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    ss_xx = sum((xi - mean_x) ** 2 for xi in x)
    ss_yy = sum((yi - mean_y) ** 2 for yi in y)
    
    if ss_xx == 0:
        return 0.0, mean_y, 0.0
    
    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x
    
    r_squared = (ss_xy ** 2) / (ss_xx * ss_yy) if ss_yy != 0 else 0.0
    
    return slope, intercept, r_squared


# ============================================================================
# HELPER FUNCTIONS — TIME SERIES
# ============================================================================

def detect_date_column(df: pd.DataFrame, htype_map: Dict[str, str]) -> Optional[str]:
    """Detect the primary date column for time series analysis."""
    # First check HTYPE map
    for col, htype in htype_map.items():
        if htype in ["HTYPE-013", "HTYPE-014", "HTYPE-015"]:  # DATE, TIME, DTM
            if col in df.columns:
                return col
    
    # Fall back to column name patterns
    date_patterns = ["date", "time", "timestamp", "created", "updated", "period"]
    for col in df.columns:
        col_lower = col.lower()
        if any(p in col_lower for p in date_patterns):
            return col
    
    return None


def detect_numeric_columns(df: pd.DataFrame, htype_map: Dict[str, str]) -> List[str]:
    """Detect numeric columns suitable for analysis."""
    numeric_cols = []
    
    for col in df.columns:
        # Check if numeric dtype
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
        # Or check HTYPE
        elif col in htype_map and htype_map[col] in [
            "HTYPE-019", "HTYPE-020", "HTYPE-021", "HTYPE-022",  # AMT, QTY, PCT, SCORE
            "HTYPE-023", "HTYPE-024", "HTYPE-025"  # CUR, RANK, CALC
        ]:
            numeric_cols.append(col)
    
    return numeric_cols


def detect_categorical_columns(df: pd.DataFrame, htype_map: Dict[str, str]) -> List[str]:
    """Detect categorical columns."""
    cat_cols = []
    
    for col in df.columns:
        # Check HTYPE
        if col in htype_map and htype_map[col] in [
            "HTYPE-027", "HTYPE-028", "HTYPE-029", "HTYPE-030"  # BOOL, CAT, STAT, SURV
        ]:
            cat_cols.append(col)
        # Or check if string with low cardinality
        elif df[col].dtype == object:
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio < 0.1:  # Less than 10% unique
                cat_cols.append(col)
    
    return cat_cols


def parse_dates(series: pd.Series) -> pd.Series:
    """Parse a series to datetime."""
    try:
        return pd.to_datetime(series, errors='coerce')
    except Exception:
        return series


def extract_year(date_series: pd.Series) -> pd.Series:
    """Extract year from date series."""
    try:
        dt = pd.to_datetime(date_series, errors='coerce')
        return dt.dt.year
    except Exception:
        return pd.Series([None] * len(date_series))


def extract_month(date_series: pd.Series) -> pd.Series:
    """Extract month from date series."""
    try:
        dt = pd.to_datetime(date_series, errors='coerce')
        return dt.dt.month
    except Exception:
        return pd.Series([None] * len(date_series))


def extract_quarter(date_series: pd.Series) -> pd.Series:
    """Extract quarter from date series."""
    try:
        dt = pd.to_datetime(date_series, errors='coerce')
        return dt.dt.quarter
    except Exception:
        return pd.Series([None] * len(date_series))


# ============================================================================
# ANALYTICAL FORMULAS
# ============================================================================

def an_01_yoy_change(df: pd.DataFrame, date_col: str, 
                      value_col: str) -> Dict[str, Any]:
    """AN-01: Year-over-Year (YoY) Change.
    
    (Current Year Value − Previous Year Value) / Previous Year Value × 100
    """
    result = {
        "formula_id": "AN-01",
        "formula_name": "Year-over-Year Change",
        "column": value_col,
        "changes": [],
    }
    
    try:
        df_copy = df.copy()
        df_copy["_year"] = extract_year(df_copy[date_col])
        
        # Group by year and sum
        yearly = df_copy.groupby("_year")[value_col].sum().sort_index()
        
        for i in range(1, len(yearly)):
            prev_year = yearly.index[i - 1]
            curr_year = yearly.index[i]
            prev_val = yearly.iloc[i - 1]
            curr_val = yearly.iloc[i]
            
            if prev_val != 0:
                yoy = ((curr_val - prev_val) / prev_val) * 100
                result["changes"].append({
                    "from_year": int(prev_year),
                    "to_year": int(curr_year),
                    "previous_value": float(prev_val),
                    "current_value": float(curr_val),
                    "yoy_change_pct": round(yoy, 2),
                })
    except Exception:
        pass
    
    return result


def an_02_mom_change(df: pd.DataFrame, date_col: str, 
                      value_col: str) -> Dict[str, Any]:
    """AN-02: Month-over-Month (MoM) Change."""
    result = {
        "formula_id": "AN-02",
        "formula_name": "Month-over-Month Change",
        "column": value_col,
        "changes": [],
    }
    
    try:
        df_copy = df.copy()
        df_copy["_date"] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy["_period"] = df_copy["_date"].dt.to_period("M")
        
        monthly = df_copy.groupby("_period")[value_col].sum().sort_index()
        
        for i in range(1, len(monthly)):
            prev_period = str(monthly.index[i - 1])
            curr_period = str(monthly.index[i])
            prev_val = monthly.iloc[i - 1]
            curr_val = monthly.iloc[i]
            
            if prev_val != 0:
                mom = ((curr_val - prev_val) / prev_val) * 100
                result["changes"].append({
                    "from_period": prev_period,
                    "to_period": curr_period,
                    "previous_value": float(prev_val),
                    "current_value": float(curr_val),
                    "mom_change_pct": round(mom, 2),
                })
    except Exception:
        pass
    
    return result


def an_03_qoq_change(df: pd.DataFrame, date_col: str, 
                      value_col: str) -> Dict[str, Any]:
    """AN-03: Quarter-over-Quarter (QoQ) Change."""
    result = {
        "formula_id": "AN-03",
        "formula_name": "Quarter-over-Quarter Change",
        "column": value_col,
        "changes": [],
    }
    
    try:
        df_copy = df.copy()
        df_copy["_date"] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy["_period"] = df_copy["_date"].dt.to_period("Q")
        
        quarterly = df_copy.groupby("_period")[value_col].sum().sort_index()
        
        for i in range(1, len(quarterly)):
            prev_period = str(quarterly.index[i - 1])
            curr_period = str(quarterly.index[i])
            prev_val = quarterly.iloc[i - 1]
            curr_val = quarterly.iloc[i]
            
            if prev_val != 0:
                qoq = ((curr_val - prev_val) / prev_val) * 100
                result["changes"].append({
                    "from_period": prev_period,
                    "to_period": curr_period,
                    "previous_value": float(prev_val),
                    "current_value": float(curr_val),
                    "qoq_change_pct": round(qoq, 2),
                })
    except Exception:
        pass
    
    return result


def an_04_moving_average(values: List[float], n: int = 3) -> List[Optional[float]]:
    """AN-04: Rolling / Moving Average.
    
    MA(t) = (v(t) + v(t-1) + ... + v(t-n+1)) / n
    """
    if len(values) < n:
        return [None] * len(values)
    
    result = [None] * (n - 1)
    
    for i in range(n - 1, len(values)):
        window = values[i - n + 1:i + 1]
        result.append(sum(window) / n)
    
    return result


def an_05_cumulative_sum(values: List[float]) -> List[float]:
    """AN-05: Cumulative Sum (running total)."""
    result = []
    total = 0.0
    for v in values:
        total += v if not pd.isna(v) else 0
        result.append(total)
    return result


def an_06_cohort_identification(df: pd.DataFrame, date_col: str,
                                 id_col: str, period: str = "Y") -> Dict[str, List[Any]]:
    """AN-06: Cohort Identification.
    
    Groups records by entry period.
    """
    result = {}
    
    try:
        df_copy = df.copy()
        df_copy["_date"] = pd.to_datetime(df_copy[date_col], errors='coerce')
        
        # Get first date per ID
        first_dates = df_copy.groupby(id_col)["_date"].min()
        
        # Group by period
        if period == "Y":
            cohorts = first_dates.dt.year
        elif period == "Q":
            cohorts = first_dates.dt.to_period("Q").astype(str)
        else:
            cohorts = first_dates.dt.to_period("M").astype(str)
        
        for cohort_name, ids in cohorts.groupby(cohorts):
            result[str(cohort_name)] = ids.index.tolist()
    except Exception:
        pass
    
    return result


def an_07_cohort_retention(df: pd.DataFrame, date_col: str,
                            id_col: str, periods: int = 6) -> Dict[str, Any]:
    """AN-07: Cohort Retention.
    
    Tracks what % of each cohort remains active over subsequent periods.
    """
    result = {
        "formula_id": "AN-07",
        "cohorts": {},
    }
    
    try:
        df_copy = df.copy()
        df_copy["_date"] = pd.to_datetime(df_copy[date_col], errors='coerce')
        df_copy["_period"] = df_copy["_date"].dt.to_period("M")
        
        # Get first period per ID
        first_periods = df_copy.groupby(id_col)["_period"].min()
        
        # Group by cohort (first period)
        for cohort_period in first_periods.unique():
            cohort_ids = first_periods[first_periods == cohort_period].index
            cohort_size = len(cohort_ids)
            
            if cohort_size == 0:
                continue
            
            retention = {"period_0": 100.0}
            
            # Track retention over subsequent periods
            for p in range(1, periods + 1):
                target_period = cohort_period + p
                active_in_period = df_copy[
                    (df_copy[id_col].isin(cohort_ids)) &
                    (df_copy["_period"] == target_period)
                ][id_col].nunique()
                
                retention[f"period_{p}"] = round((active_in_period / cohort_size) * 100, 2)
            
            result["cohorts"][str(cohort_period)] = {
                "cohort_size": cohort_size,
                "retention": retention,
            }
    except Exception:
        pass
    
    return result


def an_08_pareto_analysis(df: pd.DataFrame, category_col: str,
                           value_col: str) -> Dict[str, Any]:
    """AN-08: Pareto / 80-20 Analysis.
    
    Ranks categories by contribution to total.
    """
    result = {
        "formula_id": "AN-08",
        "formula_name": "Pareto Analysis",
        "categories": [],
        "top_20_pct_contribution": 0.0,
    }
    
    try:
        # Sum by category
        totals = df.groupby(category_col)[value_col].sum().sort_values(ascending=False)
        grand_total = totals.sum()
        
        if grand_total == 0:
            return result
        
        cumulative = 0.0
        top_20_threshold = len(totals) * 0.2
        top_20_value = 0.0
        
        for i, (cat, val) in enumerate(totals.items()):
            pct = (val / grand_total) * 100
            cumulative += pct
            
            if i < top_20_threshold:
                top_20_value += pct
            
            result["categories"].append({
                "category": str(cat),
                "value": float(val),
                "percentage": round(pct, 2),
                "cumulative_pct": round(cumulative, 2),
            })
        
        result["top_20_pct_contribution"] = round(top_20_value, 2)
    except Exception:
        pass
    
    return result


def an_09_seasonality_detection(values: List[float], 
                                 frequency: str = "monthly") -> Dict[str, Any]:
    """AN-09: Seasonality Detection.
    
    Identifies recurring patterns using autocorrelation.
    """
    result = {
        "formula_id": "AN-09",
        "formula_name": "Seasonality Detection",
        "seasonality_type": SeasonalityType.NONE.value,
        "peaks": [],
        "troughs": [],
    }
    
    if len(values) < 12:  # Need at least 2 cycles
        return result
    
    try:
        # Calculate autocorrelation at different lags
        n = len(values)
        mean = calculate_mean(values)
        variance = calculate_variance(values, sample=False)
        
        if variance == 0:
            return result
        
        # Check different seasonal periods
        lags_to_check = {
            "weekly": 7,
            "monthly": 12,
            "quarterly": 4,
        }
        
        best_lag = None
        best_correlation = 0.0
        
        for season_type, lag in lags_to_check.items():
            if n < lag * 2:
                continue
            
            # Calculate autocorrelation at this lag
            autocorr = 0.0
            for i in range(n - lag):
                autocorr += (values[i] - mean) * (values[i + lag] - mean)
            autocorr /= (n - lag) * variance
            
            if abs(autocorr) > abs(best_correlation) and abs(autocorr) > 0.5:
                best_correlation = autocorr
                best_lag = season_type
        
        if best_lag:
            result["seasonality_type"] = best_lag
            result["autocorrelation"] = round(best_correlation, 3)
            
            # Find peaks and troughs
            for i in range(1, n - 1):
                if values[i] > values[i-1] and values[i] > values[i+1]:
                    result["peaks"].append({"index": i, "value": values[i]})
                if values[i] < values[i-1] and values[i] < values[i+1]:
                    result["troughs"].append({"index": i, "value": values[i]})
    except Exception:
        pass
    
    return result


def an_10_trend_detection(values: List[float]) -> TrendResult:
    """AN-10: Trend Detection.
    
    Determines if metric is trending up, down, or flat.
    """
    if len(values) < 2:
        return TrendResult(
            direction=TrendDirection.FLAT,
            slope=0.0,
            r_squared=0.0,
            confidence="LOW",
        )
    
    x = list(range(len(values)))
    slope, intercept, r_squared = linear_regression(x, values)
    
    # Determine direction
    if abs(slope) < 0.01 * calculate_mean(values):
        direction = TrendDirection.FLAT
    elif slope > 0:
        direction = TrendDirection.UP
    else:
        direction = TrendDirection.DOWN
    
    # Confidence based on R²
    if r_squared >= 0.8:
        confidence = "HIGH"
    elif r_squared >= 0.5:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"
    
    return TrendResult(
        direction=direction,
        slope=round(slope, 4),
        r_squared=round(r_squared, 4),
        confidence=confidence,
    )


def an_11_outlier_period_detection(values: List[float]) -> List[Dict[str, Any]]:
    """AN-11: Outlier Period Detection.
    
    Identifies periods where |actual − predicted| > 2 std dev.
    """
    if len(values) < 3:
        return []
    
    outliers = []
    x = list(range(len(values)))
    slope, intercept, _ = linear_regression(x, values)
    
    # Calculate predicted values
    predicted = [slope * i + intercept for i in x]
    
    # Calculate residuals
    residuals = [values[i] - predicted[i] for i in range(len(values))]
    std_residual = calculate_std_dev(residuals)
    
    if std_residual == 0:
        return []
    
    # Find outliers (> 2 std dev)
    for i, (actual, pred, resid) in enumerate(zip(values, predicted, residuals)):
        if abs(resid) > 2 * std_residual:
            outliers.append({
                "period_index": i,
                "actual_value": actual,
                "predicted_value": round(pred, 2),
                "deviation": round(resid, 2),
                "std_devs": round(resid / std_residual, 2),
            })
    
    return outliers


def an_12_rank_within_group(df: pd.DataFrame, group_col: str,
                             value_col: str, ascending: bool = False) -> pd.DataFrame:
    """AN-12: Ranking Within Group.
    
    Ranks records within each group.
    """
    df_copy = df.copy()
    
    try:
        df_copy[f"{value_col}_rank"] = df_copy.groupby(group_col)[value_col].rank(
            method="min", ascending=ascending
        )
    except Exception:
        df_copy[f"{value_col}_rank"] = None
    
    return df_copy


def an_13_percentile_calculation(values: List[float]) -> Dict[str, float]:
    """AN-13: Percentile Calculation.
    
    Calculates P25, P50 (median), P75, P90.
    """
    clean_values = [v for v in values if not pd.isna(v)]
    
    if not clean_values:
        return {"P25": 0.0, "P50": 0.0, "P75": 0.0, "P90": 0.0}
    
    return {
        "P25": round(calculate_percentile(clean_values, 25), 2),
        "P50": round(calculate_percentile(clean_values, 50), 2),
        "P75": round(calculate_percentile(clean_values, 75), 2),
        "P90": round(calculate_percentile(clean_values, 90), 2),
    }


def an_14_distribution_analysis(values: List[float]) -> Dict[str, Any]:
    """AN-14: Distribution Analysis.
    
    Mean, median, mode, std dev, skewness, kurtosis.
    """
    clean_values = [v for v in values if not pd.isna(v)]
    
    if not clean_values:
        return {
            "count": 0,
            "mean": 0.0,
            "median": 0.0,
            "mode": None,
            "std_dev": 0.0,
            "variance": 0.0,
            "skewness": 0.0,
            "kurtosis": 0.0,
            "min": 0.0,
            "max": 0.0,
        }
    
    return {
        "count": len(clean_values),
        "mean": round(calculate_mean(clean_values), 4),
        "median": round(calculate_median(clean_values), 4),
        "mode": calculate_mode(clean_values),
        "std_dev": round(calculate_std_dev(clean_values), 4),
        "variance": round(calculate_variance(clean_values), 4),
        "skewness": round(calculate_skewness(clean_values), 4),
        "kurtosis": round(calculate_kurtosis(clean_values), 4),
        "min": min(clean_values),
        "max": max(clean_values),
    }


def an_15_correlation_detection(df: pd.DataFrame, 
                                 numeric_cols: List[str],
                                 threshold: float = 0.7) -> List[CorrelationPair]:
    """AN-15: Correlation Detection.
    
    Identifies pairs with |r| ≥ threshold.
    """
    correlations = []
    
    for i, col1 in enumerate(numeric_cols):
        for col2 in numeric_cols[i + 1:]:
            try:
                # Get clean paired values
                mask = df[[col1, col2]].notna().all(axis=1)
                x = df.loc[mask, col1].tolist()
                y = df.loc[mask, col2].tolist()
                
                if len(x) < 3:
                    continue
                
                r = calculate_correlation(x, y)
                
                if abs(r) >= threshold:
                    if abs(r) >= 0.9:
                        strength = "VERY_STRONG"
                    elif abs(r) >= 0.7:
                        strength = "STRONG"
                    else:
                        strength = "MODERATE"
                    
                    correlations.append(CorrelationPair(
                        column1=col1,
                        column2=col2,
                        correlation=round(r, 4),
                        strength=strength,
                    ))
            except Exception:
                continue
    
    return correlations


def an_16_goal_vs_actual(actual_values: List[float], 
                          target: float) -> Dict[str, Any]:
    """AN-16: Goal vs Actual Comparison.
    
    Calculates variance and % achievement.
    """
    clean_values = [v for v in actual_values if not pd.isna(v)]
    total_actual = sum(clean_values)
    
    variance = total_actual - target
    achievement_pct = (total_actual / target * 100) if target != 0 else 0
    
    return {
        "formula_id": "AN-16",
        "target": target,
        "actual": round(total_actual, 2),
        "variance": round(variance, 2),
        "achievement_pct": round(achievement_pct, 2),
        "status": "MET" if total_actual >= target else "NOT_MET",
    }


def an_17_simple_forecast(values: List[float], 
                           periods: int = 3,
                           method: str = "linear") -> List[Dict[str, Any]]:
    """AN-17: Forecast (Simple).
    
    Projects next N periods using linear trend or exponential smoothing.
    """
    forecasts = []
    
    if len(values) < 3:
        return forecasts
    
    if method == "linear":
        x = list(range(len(values)))
        slope, intercept, r_squared = linear_regression(x, values)
        
        for i in range(1, periods + 1):
            future_x = len(values) + i - 1
            forecast_value = slope * future_x + intercept
            forecasts.append({
                "period": i,
                "forecast_value": round(forecast_value, 2),
                "method": "linear",
                "confidence": "HIGH" if r_squared > 0.8 else "MEDIUM" if r_squared > 0.5 else "LOW",
            })
    
    elif method == "exponential":
        # Simple exponential smoothing
        alpha = 0.3
        smoothed = values[0]
        for v in values[1:]:
            smoothed = alpha * v + (1 - alpha) * smoothed
        
        for i in range(1, periods + 1):
            forecasts.append({
                "period": i,
                "forecast_value": round(smoothed, 2),
                "method": "exponential",
                "alpha": alpha,
            })
    
    return forecasts


def an_18_concentration_index(values: List[float]) -> Dict[str, Any]:
    """AN-18: Concentration Index (HHI-style).
    
    Measures how concentrated a distribution is.
    """
    clean_values = [v for v in values if not pd.isna(v) and v > 0]
    
    if not clean_values:
        return {"hhi": 0, "interpretation": "N/A"}
    
    total = sum(clean_values)
    if total == 0:
        return {"hhi": 0, "interpretation": "N/A"}
    
    # Calculate market shares squared
    shares_squared = [(v / total) ** 2 for v in clean_values]
    hhi = sum(shares_squared) * 10000  # Scale to 0-10000
    
    if hhi >= 2500:
        interpretation = "HIGHLY_CONCENTRATED"
    elif hhi >= 1500:
        interpretation = "MODERATELY_CONCENTRATED"
    else:
        interpretation = "UNCONCENTRATED"
    
    return {
        "hhi": round(hhi, 2),
        "interpretation": interpretation,
        "top_share_pct": round(max(clean_values) / total * 100, 2),
    }


def an_19_days_between(df: pd.DataFrame, date_col1: str, 
                        date_col2: str) -> pd.Series:
    """AN-19: Days-Between Derivation.
    
    Calculates number of days between two date columns.
    """
    try:
        d1 = pd.to_datetime(df[date_col1], errors='coerce')
        d2 = pd.to_datetime(df[date_col2], errors='coerce')
        return (d2 - d1).dt.days
    except Exception:
        return pd.Series([None] * len(df))


def an_20_frequency_table(series: pd.Series) -> Dict[str, Any]:
    """AN-20: Frequency Table.
    
    Produces count + % per category.
    """
    counts = series.value_counts()
    total = len(series.dropna())
    
    table = []
    for value, count in counts.items():
        pct = (count / total * 100) if total > 0 else 0
        table.append({
            "value": str(value),
            "count": int(count),
            "percentage": round(pct, 2),
        })
    
    return {
        "formula_id": "AN-20",
        "total_non_null": total,
        "unique_values": len(counts),
        "frequencies": table,
    }


# ============================================================================
# MAIN CLASS
# ============================================================================

class AnalyticalFormulas:
    """Analytical Formula Set engine (Post-Cleaning)."""
    
    def __init__(self, job_id: int, df: pd.DataFrame, db,
                 htype_map: Dict[str, str],
                 targets: Optional[Dict[str, float]] = None):
        """Initialize the analytical engine.
        
        Args:
            job_id: Upload job ID for logging
            df: Cleaned DataFrame to analyze
            db: Database session
            htype_map: Mapping of column names to their HTYPEs
            targets: Optional dict of target values {column: target}
        """
        self.job_id = job_id
        self.df = df.copy()
        self.db = db
        self.htype_map = htype_map
        self.targets = targets or {}
        
        self.results: List[AnalyticalResult] = []
        self.insights: List[Dict[str, Any]] = []
        
        # Detect column types
        self.date_col = detect_date_column(df, htype_map)
        self.numeric_cols = detect_numeric_columns(df, htype_map)
        self.categorical_cols = detect_categorical_columns(df, htype_map)
    
    def log_action(self, action: str, details: str):
        """Log action to database."""
        try:
            log = CleaningLog(
                job_id=self.job_id,
                action=f"ANALYTIC: {action} - {details}",
                timestamp=datetime.utcnow(),
            )
            self.db.add(log)
            self.db.commit()
        except Exception:
            self.db.rollback()
    
    def add_insight(self, formula_id: str, insight_type: str, 
                    description: str, data: Any):
        """Add an insight for the frontend."""
        self.insights.append({
            "formula_id": formula_id,
            "type": insight_type,
            "description": description,
            "data": data,
        })
    
    # ========================================================================
    # ANALYSIS METHODS
    # ========================================================================
    
    def run_time_series_analysis(self) -> Dict[str, Any]:
        """Run time-series analyses (AN-01 through AN-05)."""
        results = {
            "yoy_changes": [],
            "mom_changes": [],
            "qoq_changes": [],
        }
        
        if not self.date_col:
            return results
        
        for col in self.numeric_cols:
            # AN-01: YoY
            yoy = an_01_yoy_change(self.df, self.date_col, col)
            if yoy["changes"]:
                results["yoy_changes"].append(yoy)
                self.add_insight("AN-01", "time_series", 
                               f"Year-over-year changes detected for {col}",
                               yoy)
            
            # AN-02: MoM
            mom = an_02_mom_change(self.df, self.date_col, col)
            if mom["changes"]:
                results["mom_changes"].append(mom)
            
            # AN-03: QoQ
            qoq = an_03_qoq_change(self.df, self.date_col, col)
            if qoq["changes"]:
                results["qoq_changes"].append(qoq)
        
        return results
    
    def run_trend_analysis(self) -> Dict[str, Any]:
        """Run trend and seasonality analysis (AN-09, AN-10, AN-11)."""
        results = {
            "trends": {},
            "seasonality": {},
            "outlier_periods": {},
        }
        
        for col in self.numeric_cols:
            values = self.df[col].dropna().tolist()
            
            if len(values) >= 3:
                # AN-10: Trend
                trend = an_10_trend_detection(values)
                results["trends"][col] = {
                    "direction": trend.direction.value,
                    "slope": trend.slope,
                    "r_squared": trend.r_squared,
                    "confidence": trend.confidence,
                }
                
                if trend.direction != TrendDirection.FLAT:
                    self.add_insight("AN-10", "trend",
                                   f"{col} shows {trend.direction.value} trend with {trend.confidence} confidence",
                                   results["trends"][col])
                
                # AN-11: Outlier periods
                outliers = an_11_outlier_period_detection(values)
                if outliers:
                    results["outlier_periods"][col] = outliers
            
            if len(values) >= 12:
                # AN-09: Seasonality
                seasonality = an_09_seasonality_detection(values)
                if seasonality["seasonality_type"] != "none":
                    results["seasonality"][col] = seasonality
                    self.add_insight("AN-09", "seasonality",
                                   f"{col} shows {seasonality['seasonality_type']} seasonality",
                                   seasonality)
        
        return results
    
    def run_distribution_analysis(self) -> Dict[str, Any]:
        """Run distribution analyses (AN-13, AN-14)."""
        results = {
            "percentiles": {},
            "distributions": {},
        }
        
        for col in self.numeric_cols:
            values = self.df[col].tolist()
            
            # AN-13: Percentiles
            results["percentiles"][col] = an_13_percentile_calculation(values)
            
            # AN-14: Distribution
            dist = an_14_distribution_analysis(values)
            results["distributions"][col] = dist
            
            # Add insight for highly skewed distributions
            if abs(dist.get("skewness", 0)) > 1:
                self.add_insight("AN-14", "distribution",
                               f"{col} has highly skewed distribution (skewness: {dist['skewness']})",
                               dist)
        
        return results
    
    def run_correlation_analysis(self) -> List[Dict[str, Any]]:
        """Run correlation analysis (AN-15)."""
        if len(self.numeric_cols) < 2:
            return []
        
        correlations = an_15_correlation_detection(self.df, self.numeric_cols)
        
        result = []
        for corr in correlations:
            result.append({
                "column1": corr.column1,
                "column2": corr.column2,
                "correlation": corr.correlation,
                "strength": corr.strength,
            })
            
            self.add_insight("AN-15", "correlation",
                           f"{corr.column1} and {corr.column2} are {corr.strength.lower()} correlated (r={corr.correlation})",
                           result[-1])
        
        return result
    
    def run_pareto_analysis(self) -> List[Dict[str, Any]]:
        """Run Pareto analysis (AN-08) for categorical + numeric pairs."""
        results = []
        
        for cat_col in self.categorical_cols:
            for num_col in self.numeric_cols:
                pareto = an_08_pareto_analysis(self.df, cat_col, num_col)
                if pareto["categories"]:
                    pareto["category_column"] = cat_col
                    pareto["value_column"] = num_col
                    results.append(pareto)
                    
                    if pareto["top_20_pct_contribution"] >= 70:
                        self.add_insight("AN-08", "pareto",
                                       f"Top 20% of {cat_col} drive {pareto['top_20_pct_contribution']}% of {num_col}",
                                       pareto)
        
        return results
    
    def run_frequency_analysis(self) -> Dict[str, Any]:
        """Run frequency analysis (AN-20) for categorical columns."""
        results = {}
        
        for col in self.categorical_cols:
            freq = an_20_frequency_table(self.df[col])
            freq["column"] = col
            results[col] = freq
        
        return results
    
    def run_goal_analysis(self) -> Dict[str, Any]:
        """Run goal vs actual analysis (AN-16)."""
        results = {}
        
        for col, target in self.targets.items():
            if col in self.df.columns:
                values = self.df[col].tolist()
                goal_result = an_16_goal_vs_actual(values, target)
                goal_result["column"] = col
                results[col] = goal_result
                
                status = goal_result["status"]
                pct = goal_result["achievement_pct"]
                self.add_insight("AN-16", "goal",
                               f"{col}: {status} - {pct}% of target achieved",
                               goal_result)
        
        return results
    
    def run_forecast(self, periods: int = 3) -> Dict[str, Any]:
        """Run simple forecasting (AN-17)."""
        results = {}
        
        for col in self.numeric_cols:
            values = self.df[col].dropna().tolist()
            if len(values) >= 3:
                forecast = an_17_simple_forecast(values, periods)
                if forecast:
                    results[col] = forecast
        
        return results
    
    def run_concentration_analysis(self) -> Dict[str, Any]:
        """Run concentration index analysis (AN-18)."""
        results = {}
        
        for col in self.numeric_cols:
            values = self.df[col].tolist()
            conc = an_18_concentration_index(values)
            results[col] = conc
            
            if conc["interpretation"] == "HIGHLY_CONCENTRATED":
                self.add_insight("AN-18", "concentration",
                               f"{col} is highly concentrated (HHI: {conc['hhi']})",
                               conc)
        
        return results
    
    # ========================================================================
    # ORCHESTRATION
    # ========================================================================
    
    def run_all(self) -> Dict[str, Any]:
        """Run all analytical formulas.
        
        Returns:
            Comprehensive analysis results
        """
        summary = {
            "time_series": self.run_time_series_analysis(),
            "trends": self.run_trend_analysis(),
            "distributions": self.run_distribution_analysis(),
            "correlations": self.run_correlation_analysis(),
            "pareto": self.run_pareto_analysis(),
            "frequencies": self.run_frequency_analysis(),
            "goals": self.run_goal_analysis(),
            "forecasts": self.run_forecast(),
            "concentration": self.run_concentration_analysis(),
            "insights": self.insights,
            "columns_analyzed": {
                "date_column": self.date_col,
                "numeric_columns": self.numeric_cols,
                "categorical_columns": self.categorical_cols,
            },
        }
        
        self.log_action("ANALYSIS_COMPLETE", 
                       f"Generated {len(self.insights)} insights from {len(self.numeric_cols)} numeric and {len(self.categorical_cols)} categorical columns")
        
        return summary
