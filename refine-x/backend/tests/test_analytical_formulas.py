"""
Tests for Analytical Formula Set (Session 14)

Tests all 20 analytical formulas (AN-01 through AN-20):
- Statistical helper functions
- Time series analysis (YoY, MoM, QoQ, moving average, cumulative sum)
- Cohort analysis (identification, retention)
- Pareto analysis
- Trend and seasonality detection
- Distribution analysis
- Correlation detection
- Goal vs actual comparison
- Forecasting
- Concentration index
- Frequency tables
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import math

from app.services.analytical_formulas import (
    # Enums
    TrendDirection,
    SeasonalityType,
    # Data classes
    AnalyticalResult,
    TrendResult,
    CorrelationPair,
    # Statistical helpers
    calculate_mean,
    calculate_median,
    calculate_mode,
    calculate_std_dev,
    calculate_variance,
    calculate_skewness,
    calculate_kurtosis,
    calculate_percentile,
    calculate_correlation,
    linear_regression,
    # Time series helpers
    detect_date_column,
    detect_numeric_columns,
    detect_categorical_columns,
    extract_year,
    extract_month,
    extract_quarter,
    # Analytical formulas
    an_01_yoy_change,
    an_02_mom_change,
    an_03_qoq_change,
    an_04_moving_average,
    an_05_cumulative_sum,
    an_06_cohort_identification,
    an_07_cohort_retention,
    an_08_pareto_analysis,
    an_09_seasonality_detection,
    an_10_trend_detection,
    an_11_outlier_period_detection,
    an_12_rank_within_group,
    an_13_percentile_calculation,
    an_14_distribution_analysis,
    an_15_correlation_detection,
    an_16_goal_vs_actual,
    an_17_simple_forecast,
    an_18_concentration_index,
    an_19_days_between,
    an_20_frequency_table,
    # Main class
    AnalyticalFormulas,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    return db


@pytest.fixture
def sample_df():
    """Sample DataFrame with time series data."""
    dates = pd.date_range(start='2023-01-01', periods=12, freq='MS')
    return pd.DataFrame({
        "date": dates,
        "revenue": [100, 120, 110, 130, 140, 135, 150, 160, 155, 170, 180, 190],
        "units": [10, 12, 11, 13, 14, 13, 15, 16, 15, 17, 18, 19],
        "category": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
        "region": ["North", "North", "South", "South", "North", "South", "North", "South", "North", "South", "North", "South"],
    })


@pytest.fixture
def sample_htype_map():
    """Sample HTYPE mapping."""
    return {
        "date": "HTYPE-013",
        "revenue": "HTYPE-019",
        "units": "HTYPE-020",
        "category": "HTYPE-027",
        "region": "HTYPE-027",
    }


# ============================================================================
# TESTS: STATISTICAL HELPERS
# ============================================================================

class TestCalculateMean:
    """Tests for calculate_mean function."""
    
    def test_simple_mean(self):
        """Simple average."""
        assert calculate_mean([1, 2, 3, 4, 5]) == 3.0
    
    def test_empty_list(self):
        """Empty list returns 0."""
        assert calculate_mean([]) == 0.0
    
    def test_single_value(self):
        """Single value returns itself."""
        assert calculate_mean([5]) == 5.0
    
    def test_negative_values(self):
        """Handles negative values."""
        assert calculate_mean([-1, 0, 1]) == 0.0


class TestCalculateMedian:
    """Tests for calculate_median function."""
    
    def test_odd_count(self):
        """Odd number of values."""
        assert calculate_median([1, 2, 3, 4, 5]) == 3.0
    
    def test_even_count(self):
        """Even number of values."""
        assert calculate_median([1, 2, 3, 4]) == 2.5
    
    def test_empty_list(self):
        """Empty list returns 0."""
        assert calculate_median([]) == 0.0
    
    def test_unsorted(self):
        """Handles unsorted input."""
        assert calculate_median([5, 1, 3, 2, 4]) == 3.0


class TestCalculateMode:
    """Tests for calculate_mode function."""
    
    def test_single_mode(self):
        """Single mode."""
        assert calculate_mode([1, 2, 2, 3]) == 2
    
    def test_no_mode(self):
        """No mode (all unique)."""
        assert calculate_mode([1, 2, 3, 4]) is None
    
    def test_empty_list(self):
        """Empty list returns None."""
        assert calculate_mode([]) is None


class TestCalculateStdDev:
    """Tests for calculate_std_dev function."""
    
    def test_simple_std(self):
        """Simple standard deviation."""
        std = calculate_std_dev([2, 4, 4, 4, 5, 5, 7, 9])
        assert 1.9 < std < 2.2  # Approximately 2 (sample std dev)
    
    def test_zero_variance(self):
        """All same values = 0 std."""
        assert calculate_std_dev([5, 5, 5, 5]) == 0.0
    
    def test_single_value(self):
        """Single value returns 0."""
        assert calculate_std_dev([5]) == 0.0


class TestCalculateVariance:
    """Tests for calculate_variance function."""
    
    def test_simple_variance(self):
        """Simple variance."""
        var = calculate_variance([2, 4, 4, 4, 5, 5, 7, 9])
        assert 3.5 < var < 5.0  # Approximately 4 (sample variance)
    
    def test_population_variance(self):
        """Population vs sample variance."""
        sample_var = calculate_variance([1, 2, 3], sample=True)
        pop_var = calculate_variance([1, 2, 3], sample=False)
        assert sample_var > pop_var


class TestCalculateSkewness:
    """Tests for calculate_skewness function."""
    
    def test_symmetric_distribution(self):
        """Symmetric distribution has skewness near 0."""
        skew = calculate_skewness([1, 2, 3, 4, 5, 6, 7, 8, 9])
        assert abs(skew) < 0.5
    
    def test_right_skewed(self):
        """Right-skewed distribution."""
        skew = calculate_skewness([1, 1, 1, 2, 2, 3, 10, 20, 30])
        assert skew > 0
    
    def test_insufficient_data(self):
        """Less than 3 values returns 0."""
        assert calculate_skewness([1, 2]) == 0.0


class TestCalculateKurtosis:
    """Tests for calculate_kurtosis function."""
    
    def test_normal_like(self):
        """Normal-like distribution has kurtosis near 0."""
        # Generate normal-like data
        data = [1, 2, 3, 4, 5, 5, 5, 6, 7, 8, 9]
        kurt = calculate_kurtosis(data)
        assert -3 < kurt < 3
    
    def test_insufficient_data(self):
        """Less than 4 values returns 0."""
        assert calculate_kurtosis([1, 2, 3]) == 0.0


class TestCalculatePercentile:
    """Tests for calculate_percentile function."""
    
    def test_median_percentile(self):
        """50th percentile = median."""
        assert calculate_percentile([1, 2, 3, 4, 5], 50) == 3.0
    
    def test_extreme_percentiles(self):
        """0th and 100th percentiles."""
        data = [1, 2, 3, 4, 5]
        assert calculate_percentile(data, 0) == 1
        assert calculate_percentile(data, 100) == 5
    
    def test_empty_list(self):
        """Empty list returns 0."""
        assert calculate_percentile([], 50) == 0.0


class TestCalculateCorrelation:
    """Tests for calculate_correlation function."""
    
    def test_perfect_positive(self):
        """Perfect positive correlation."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        r = calculate_correlation(x, y)
        assert abs(r - 1.0) < 1e-10  # Allow floating-point precision
    
    def test_perfect_negative(self):
        """Perfect negative correlation."""
        x = [1, 2, 3, 4, 5]
        y = [10, 8, 6, 4, 2]
        r = calculate_correlation(x, y)
        assert abs(r - (-1.0)) < 1e-10  # Allow floating-point precision
    
    def test_no_correlation(self):
        """No correlation."""
        x = [1, 2, 3, 4, 5]
        y = [5, 3, 1, 4, 2]
        r = calculate_correlation(x, y)
        assert -0.5 < r < 0.5
    
    def test_unequal_lengths(self):
        """Unequal lengths returns 0."""
        assert calculate_correlation([1, 2, 3], [1, 2]) == 0.0


class TestLinearRegression:
    """Tests for linear_regression function."""
    
    def test_perfect_line(self):
        """Perfect linear relationship."""
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]
        slope, intercept, r_squared = linear_regression(x, y)
        assert slope == 2.0
        assert intercept == 0.0
        assert r_squared == 1.0
    
    def test_with_intercept(self):
        """Line with non-zero intercept."""
        x = [0, 1, 2, 3, 4]
        y = [1, 3, 5, 7, 9]  # y = 2x + 1
        slope, intercept, r_squared = linear_regression(x, y)
        assert slope == 2.0
        assert intercept == 1.0
    
    def test_insufficient_data(self):
        """Less than 2 points returns zeros."""
        slope, intercept, r_squared = linear_regression([1], [2])
        assert slope == 0.0


# ============================================================================
# TESTS: TIME SERIES HELPERS
# ============================================================================

class TestDetectDateColumn:
    """Tests for detect_date_column function."""
    
    def test_from_htype(self, sample_df, sample_htype_map):
        """Detects from HTYPE map."""
        result = detect_date_column(sample_df, sample_htype_map)
        assert result == "date"
    
    def test_from_column_name(self, sample_df):
        """Detects from column name pattern."""
        result = detect_date_column(sample_df, {})
        assert result == "date"
    
    def test_no_date_column(self):
        """Returns None when no date column."""
        df = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        assert detect_date_column(df, {}) is None


class TestDetectNumericColumns:
    """Tests for detect_numeric_columns function."""
    
    def test_detects_numeric(self, sample_df, sample_htype_map):
        """Detects numeric columns."""
        result = detect_numeric_columns(sample_df, sample_htype_map)
        assert "revenue" in result
        assert "units" in result
        assert "category" not in result


class TestDetectCategoricalColumns:
    """Tests for detect_categorical_columns function."""
    
    def test_detects_categorical(self, sample_df, sample_htype_map):
        """Detects categorical columns."""
        result = detect_categorical_columns(sample_df, sample_htype_map)
        assert "category" in result
        assert "region" in result


class TestExtractDateParts:
    """Tests for date extraction functions."""
    
    def test_extract_year(self):
        """Extracts year."""
        series = pd.Series(["2023-01-15", "2024-06-20"])
        years = extract_year(series)
        assert list(years) == [2023, 2024]
    
    def test_extract_month(self):
        """Extracts month."""
        series = pd.Series(["2023-01-15", "2023-06-20"])
        months = extract_month(series)
        assert list(months) == [1, 6]
    
    def test_extract_quarter(self):
        """Extracts quarter."""
        series = pd.Series(["2023-01-15", "2023-06-20"])
        quarters = extract_quarter(series)
        assert list(quarters) == [1, 2]


# ============================================================================
# TESTS: ANALYTICAL FORMULAS
# ============================================================================

class TestAN01YoYChange:
    """Tests for AN-01: Year-over-Year Change."""
    
    def test_calculates_yoy(self):
        """Calculates YoY change."""
        df = pd.DataFrame({
            "date": ["2022-01-01", "2023-01-01"],
            "revenue": [100, 120],
        })
        result = an_01_yoy_change(df, "date", "revenue")
        assert result["formula_id"] == "AN-01"
        assert len(result["changes"]) == 1
        assert result["changes"][0]["yoy_change_pct"] == 20.0
    
    def test_multiple_years(self):
        """Handles multiple years."""
        df = pd.DataFrame({
            "date": ["2021-01-01", "2022-01-01", "2023-01-01"],
            "revenue": [100, 120, 150],
        })
        result = an_01_yoy_change(df, "date", "revenue")
        assert len(result["changes"]) == 2


class TestAN02MoMChange:
    """Tests for AN-02: Month-over-Month Change."""
    
    def test_calculates_mom(self):
        """Calculates MoM change."""
        df = pd.DataFrame({
            "date": ["2023-01-01", "2023-02-01"],
            "revenue": [100, 110],
        })
        result = an_02_mom_change(df, "date", "revenue")
        assert result["formula_id"] == "AN-02"
        assert len(result["changes"]) == 1
        assert result["changes"][0]["mom_change_pct"] == 10.0


class TestAN03QoQChange:
    """Tests for AN-03: Quarter-over-Quarter Change."""
    
    def test_calculates_qoq(self):
        """Calculates QoQ change."""
        df = pd.DataFrame({
            "date": ["2023-01-01", "2023-04-01"],
            "revenue": [100, 125],
        })
        result = an_03_qoq_change(df, "date", "revenue")
        assert result["formula_id"] == "AN-03"
        assert len(result["changes"]) == 1
        assert result["changes"][0]["qoq_change_pct"] == 25.0


class TestAN04MovingAverage:
    """Tests for AN-04: Moving Average."""
    
    def test_simple_ma(self):
        """Simple 3-period moving average."""
        values = [1, 2, 3, 4, 5]
        result = an_04_moving_average(values, n=3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 2.0  # (1+2+3)/3
        assert result[3] == 3.0  # (2+3+4)/3
        assert result[4] == 4.0  # (3+4+5)/3
    
    def test_insufficient_data(self):
        """Not enough data for window."""
        values = [1, 2]
        result = an_04_moving_average(values, n=3)
        assert all(v is None for v in result)


class TestAN05CumulativeSum:
    """Tests for AN-05: Cumulative Sum."""
    
    def test_cumsum(self):
        """Simple cumulative sum."""
        values = [1, 2, 3, 4, 5]
        result = an_05_cumulative_sum(values)
        assert result == [1, 3, 6, 10, 15]
    
    def test_with_nan(self):
        """Handles NaN values."""
        values = [1, np.nan, 3]
        result = an_05_cumulative_sum(values)
        assert result == [1, 1, 4]


class TestAN06CohortIdentification:
    """Tests for AN-06: Cohort Identification."""
    
    def test_identifies_cohorts(self):
        """Identifies cohorts by year."""
        df = pd.DataFrame({
            "user_id": ["A", "B", "C", "A", "B"],
            "date": ["2022-01-15", "2022-03-20", "2023-02-10", "2022-06-01", "2023-01-05"],
        })
        result = an_06_cohort_identification(df, "date", "user_id", period="Y")
        assert "2022" in result
        assert "2023" in result
        assert "A" in result["2022"]


class TestAN07CohortRetention:
    """Tests for AN-07: Cohort Retention."""
    
    def test_calculates_retention(self):
        """Calculates retention rates."""
        # User A active in Jan, Feb; User B only in Jan
        df = pd.DataFrame({
            "user_id": ["A", "A", "B"],
            "date": ["2023-01-15", "2023-02-15", "2023-01-20"],
        })
        result = an_07_cohort_retention(df, "date", "user_id", periods=2)
        assert "formula_id" in result
        assert "cohorts" in result


class TestAN08ParetoAnalysis:
    """Tests for AN-08: Pareto Analysis."""
    
    def test_pareto_ranking(self):
        """Ranks categories by contribution."""
        df = pd.DataFrame({
            "product": ["A", "A", "B", "C", "C", "C"],
            "revenue": [100, 50, 25, 10, 5, 10],
        })
        result = an_08_pareto_analysis(df, "product", "revenue")
        assert result["formula_id"] == "AN-08"
        assert len(result["categories"]) == 3
        # First category should have highest value
        assert result["categories"][0]["category"] == "A"
    
    def test_cumulative_percentage(self):
        """Calculates cumulative percentages."""
        df = pd.DataFrame({
            "product": ["A", "B"],
            "revenue": [80, 20],
        })
        result = an_08_pareto_analysis(df, "product", "revenue")
        assert result["categories"][0]["cumulative_pct"] == 80.0
        assert result["categories"][1]["cumulative_pct"] == 100.0


class TestAN09SeasonalityDetection:
    """Tests for AN-09: Seasonality Detection."""
    
    def test_no_seasonality_short_series(self):
        """Short series returns no seasonality."""
        values = [1, 2, 3, 4, 5]
        result = an_09_seasonality_detection(values)
        assert result["seasonality_type"] == "none"
    
    def test_detects_pattern(self):
        """Detects seasonal pattern in longer series."""
        # Create monthly pattern
        values = [10, 20, 30, 10, 20, 30, 10, 20, 30, 10, 20, 30] * 2
        result = an_09_seasonality_detection(values, frequency="monthly")
        assert "formula_id" in result


class TestAN10TrendDetection:
    """Tests for AN-10: Trend Detection."""
    
    def test_upward_trend(self):
        """Detects upward trend."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = an_10_trend_detection(values)
        assert result.direction == TrendDirection.UP
        assert result.slope > 0
    
    def test_downward_trend(self):
        """Detects downward trend."""
        values = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
        result = an_10_trend_detection(values)
        assert result.direction == TrendDirection.DOWN
        assert result.slope < 0
    
    def test_flat_trend(self):
        """Detects flat trend."""
        values = [5, 5, 5, 5, 5]
        result = an_10_trend_detection(values)
        assert result.direction == TrendDirection.FLAT


class TestAN11OutlierPeriodDetection:
    """Tests for AN-11: Outlier Period Detection."""
    
    def test_detects_outlier(self):
        """Detects outlier periods."""
        values = [10, 11, 12, 13, 100, 15, 16, 17, 18]  # 100 is outlier
        result = an_11_outlier_period_detection(values)
        assert len(result) > 0
        assert result[0]["period_index"] == 4
    
    def test_no_outliers(self):
        """No outliers in smooth series."""
        values = [1, 2, 3, 4, 5]
        result = an_11_outlier_period_detection(values)
        assert len(result) == 0


class TestAN12RankWithinGroup:
    """Tests for AN-12: Ranking Within Group."""
    
    def test_ranks_correctly(self):
        """Ranks within groups."""
        df = pd.DataFrame({
            "region": ["A", "A", "B", "B"],
            "sales": [100, 200, 150, 50],
        })
        result = an_12_rank_within_group(df, "region", "sales")
        assert "sales_rank" in result.columns
        # Highest in each group should be rank 1
        assert result.loc[result["sales"] == 200, "sales_rank"].values[0] == 1.0


class TestAN13PercentileCalculation:
    """Tests for AN-13: Percentile Calculation."""
    
    def test_calculates_percentiles(self):
        """Calculates P25, P50, P75, P90."""
        values = list(range(1, 101))  # 1 to 100
        result = an_13_percentile_calculation(values)
        # Allow for different interpolation methods
        assert 25 <= result["P25"] <= 26
        assert 50 <= result["P50"] <= 51
        assert 75 <= result["P75"] <= 76
    
    def test_empty_list(self):
        """Empty list returns zeros."""
        result = an_13_percentile_calculation([])
        assert result["P50"] == 0.0


class TestAN14DistributionAnalysis:
    """Tests for AN-14: Distribution Analysis."""
    
    def test_full_analysis(self):
        """Returns all distribution metrics."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = an_14_distribution_analysis(values)
        assert "mean" in result
        assert "median" in result
        assert "std_dev" in result
        assert "skewness" in result
        assert "kurtosis" in result
        assert result["count"] == 10
    
    def test_empty_list(self):
        """Empty list returns zeros."""
        result = an_14_distribution_analysis([])
        assert result["count"] == 0


class TestAN15CorrelationDetection:
    """Tests for AN-15: Correlation Detection."""
    
    def test_finds_correlation(self):
        """Finds strongly correlated pairs."""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 6, 8, 10],  # Perfect correlation with x
            "z": [5, 3, 1, 4, 2],   # Low correlation
        })
        result = an_15_correlation_detection(df, ["x", "y", "z"])
        # Should find x-y correlation
        correlated = [c for c in result if c.correlation > 0.9]
        assert len(correlated) >= 1


class TestAN16GoalVsActual:
    """Tests for AN-16: Goal vs Actual Comparison."""
    
    def test_goal_met(self):
        """Target met scenario."""
        values = [100, 150, 200]
        result = an_16_goal_vs_actual(values, target=400)
        assert result["actual"] == 450
        assert result["status"] == "MET"
        assert result["achievement_pct"] > 100
    
    def test_goal_not_met(self):
        """Target not met scenario."""
        values = [50, 50, 50]
        result = an_16_goal_vs_actual(values, target=200)
        assert result["actual"] == 150
        assert result["status"] == "NOT_MET"
        assert result["achievement_pct"] == 75.0


class TestAN17SimpleForecast:
    """Tests for AN-17: Forecast (Simple)."""
    
    def test_linear_forecast(self):
        """Linear trend forecast."""
        values = [10, 20, 30, 40, 50]
        result = an_17_simple_forecast(values, periods=3, method="linear")
        assert len(result) == 3
        assert result[0]["method"] == "linear"
        # Should project upward
        assert result[0]["forecast_value"] > values[-1]
    
    def test_exponential_forecast(self):
        """Exponential smoothing forecast."""
        values = [10, 20, 30, 40, 50]
        result = an_17_simple_forecast(values, periods=2, method="exponential")
        assert len(result) == 2
        assert result[0]["method"] == "exponential"


class TestAN18ConcentrationIndex:
    """Tests for AN-18: Concentration Index."""
    
    def test_highly_concentrated(self):
        """Highly concentrated distribution."""
        values = [90, 5, 3, 2]  # One dominates
        result = an_18_concentration_index(values)
        assert result["interpretation"] == "HIGHLY_CONCENTRATED"
    
    def test_unconcentrated(self):
        """Evenly distributed."""
        values = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
        result = an_18_concentration_index(values)
        assert result["interpretation"] == "UNCONCENTRATED"


class TestAN19DaysBetween:
    """Tests for AN-19: Days-Between Derivation."""
    
    def test_calculates_days(self):
        """Calculates days between dates."""
        df = pd.DataFrame({
            "start": ["2023-01-01", "2023-02-01"],
            "end": ["2023-01-10", "2023-02-15"],
        })
        result = an_19_days_between(df, "start", "end")
        assert list(result) == [9, 14]


class TestAN20FrequencyTable:
    """Tests for AN-20: Frequency Table."""
    
    def test_creates_table(self):
        """Creates frequency table."""
        series = pd.Series(["A", "A", "A", "B", "B", "C"])
        result = an_20_frequency_table(series)
        assert result["formula_id"] == "AN-20"
        assert result["total_non_null"] == 6
        assert result["unique_values"] == 3
        assert len(result["frequencies"]) == 3


# ============================================================================
# TESTS: MAIN CLASS
# ============================================================================

class TestAnalyticalFormulasClass:
    """Tests for AnalyticalFormulas main class."""
    
    def test_initialization(self, mock_db, sample_df, sample_htype_map):
        """Initializes correctly."""
        engine = AnalyticalFormulas(
            job_id=1, df=sample_df, db=mock_db, htype_map=sample_htype_map
        )
        assert engine.date_col == "date"
        assert len(engine.numeric_cols) >= 2
        assert len(engine.categorical_cols) >= 1
    
    def test_run_all(self, mock_db, sample_df, sample_htype_map):
        """Runs all analyses."""
        engine = AnalyticalFormulas(
            job_id=1, df=sample_df, db=mock_db, htype_map=sample_htype_map
        )
        result = engine.run_all()
        assert "time_series" in result
        assert "trends" in result
        assert "distributions" in result
        assert "correlations" in result
        assert "insights" in result
    
    def test_with_targets(self, mock_db, sample_df, sample_htype_map):
        """Handles target values."""
        engine = AnalyticalFormulas(
            job_id=1, df=sample_df, db=mock_db, htype_map=sample_htype_map,
            targets={"revenue": 1500}
        )
        result = engine.run_all()
        assert "goals" in result
        if "revenue" in result["goals"]:
            assert "status" in result["goals"]["revenue"]


# ============================================================================
# TESTS: ENUMS AND DATA CLASSES
# ============================================================================

class TestEnums:
    """Tests for enum values."""
    
    def test_trend_direction(self):
        """TrendDirection values."""
        assert TrendDirection.UP.value == "up"
        assert TrendDirection.DOWN.value == "down"
        assert TrendDirection.FLAT.value == "flat"
    
    def test_seasonality_type(self):
        """SeasonalityType values."""
        assert SeasonalityType.WEEKLY.value == "weekly"
        assert SeasonalityType.MONTHLY.value == "monthly"
        assert SeasonalityType.QUARTERLY.value == "quarterly"
        assert SeasonalityType.YEARLY.value == "yearly"
        assert SeasonalityType.NONE.value == "none"


class TestDataClasses:
    """Tests for data class initialization."""
    
    def test_trend_result(self):
        """TrendResult initialization."""
        result = TrendResult(
            direction=TrendDirection.UP,
            slope=0.5,
            r_squared=0.9,
            confidence="HIGH",
        )
        assert result.direction == TrendDirection.UP
        assert result.slope == 0.5
    
    def test_correlation_pair(self):
        """CorrelationPair initialization."""
        pair = CorrelationPair(
            column1="x",
            column2="y",
            correlation=0.95,
            strength="VERY_STRONG",
        )
        assert pair.column1 == "x"
        assert pair.correlation == 0.95


# ============================================================================
# TESTS: EDGE CASES
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_empty_dataframe(self, mock_db, sample_htype_map):
        """Empty DataFrame handled gracefully."""
        df = pd.DataFrame()
        engine = AnalyticalFormulas(
            job_id=1, df=df, db=mock_db, htype_map=sample_htype_map
        )
        result = engine.run_all()
        assert "columns_analyzed" in result
    
    def test_single_row(self, mock_db, sample_htype_map):
        """Single row DataFrame."""
        df = pd.DataFrame({
            "date": ["2023-01-01"],
            "value": [100],
        })
        engine = AnalyticalFormulas(
            job_id=1, df=df, db=mock_db, htype_map={"date": "HTYPE-013", "value": "HTYPE-019"}
        )
        result = engine.run_all()
        assert "trends" in result
    
    def test_all_null_column(self, mock_db, sample_htype_map):
        """Column with all null values."""
        df = pd.DataFrame({
            "date": ["2023-01-01", "2023-02-01"],
            "value": [None, None],
        })
        engine = AnalyticalFormulas(
            job_id=1, df=df, db=mock_db, htype_map={"date": "HTYPE-013"}
        )
        result = engine.run_all()
        assert "distributions" in result
    
    def test_no_numeric_columns(self, mock_db):
        """DataFrame with no numeric columns."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "city": ["NYC", "LA"],
        })
        engine = AnalyticalFormulas(
            job_id=1, df=df, db=mock_db, htype_map={}
        )
        result = engine.run_all()
        assert len(result["correlations"]) == 0
    
    def test_negative_values(self, mock_db, sample_htype_map):
        """Handles negative values correctly."""
        df = pd.DataFrame({
            "date": ["2023-01-01", "2023-02-01", "2023-03-01"],
            "profit": [100, -50, 75],
        })
        engine = AnalyticalFormulas(
            job_id=1, df=df, db=mock_db, htype_map={"date": "HTYPE-013", "profit": "HTYPE-019"}
        )
        result = engine.run_all()
        assert "distributions" in result
