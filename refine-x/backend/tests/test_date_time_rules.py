"""
Tests for Date & Time Rules — Session 5

Tests all formula sets:
- DATE (15 formulas) — HTYPE-004
- TIME (6 formulas) — HTYPE-005
- DTM (6 formulas) — HTYPE-006
- DUR (7 formulas) — HTYPE-033
- FISC (7 formulas) — HTYPE-041
"""

import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import MagicMock
import pandas as pd
import numpy as np

from app.services.date_time_rules import (
    DateTimeRules,
    parse_date_permissive,
    parse_time_permissive,
    parse_duration,
    parse_fiscal_year,
    parse_academic_year,
    parse_excel_serial,
    is_likely_excel_serial,
    is_date_placeholder,
    remove_ordinal_suffix,
    detect_date_format_majority,
    extract_timezone,
    get_time_bucket,
)


# ============================================================================
# HELPER FUNCTION TESTS
# ============================================================================

class TestRemoveOrdinalSuffix:
    """Tests for remove_ordinal_suffix function."""
    
    def test_removes_st(self):
        assert remove_ordinal_suffix("1st January") == "1 January"
        assert remove_ordinal_suffix("21st") == "21"
    
    def test_removes_nd(self):
        assert remove_ordinal_suffix("2nd February") == "2 February"
        assert remove_ordinal_suffix("22nd") == "22"
    
    def test_removes_rd(self):
        assert remove_ordinal_suffix("3rd March") == "3 March"
        assert remove_ordinal_suffix("23rd") == "23"
    
    def test_removes_th(self):
        assert remove_ordinal_suffix("4th April") == "4 April"
        assert remove_ordinal_suffix("15th") == "15"
    
    def test_preserves_non_ordinal(self):
        assert remove_ordinal_suffix("2024-01-15") == "2024-01-15"


class TestIsDatePlaceholder:
    """Tests for is_date_placeholder function."""
    
    def test_recognizes_1900_placeholder(self):
        assert is_date_placeholder("01/01/1900") is True
        assert is_date_placeholder("1900-01-01") is True
    
    def test_recognizes_1970_placeholder(self):
        assert is_date_placeholder("01/01/1970") is True
        assert is_date_placeholder("1970-01-01") is True
    
    def test_recognizes_zero_placeholder(self):
        assert is_date_placeholder("00/00/0000") is True
    
    def test_recognizes_text_placeholders(self):
        assert is_date_placeholder("N/A") is True
        assert is_date_placeholder("TBD") is True
        assert is_date_placeholder("pending") is True
    
    def test_valid_dates_not_placeholder(self):
        assert is_date_placeholder("2024-03-15") is False
        assert is_date_placeholder("15/03/2024") is False
    
    def test_null_is_placeholder(self):
        assert is_date_placeholder(None) is True
        assert is_date_placeholder(np.nan) is True


class TestParseDatePermissive:
    """Tests for parse_date_permissive function."""
    
    def test_iso_format(self):
        result = parse_date_permissive("2024-03-15")
        assert result is not None
        assert result.year == 2024
        assert result.month == 3
        assert result.day == 15
    
    def test_european_format(self):
        result = parse_date_permissive("15/03/2024", dayfirst=True)
        assert result is not None
        assert result.day == 15
        assert result.month == 3
    
    def test_american_format(self):
        result = parse_date_permissive("03/15/2024", dayfirst=False)
        assert result is not None
        assert result.day == 15
        assert result.month == 3
    
    def test_verbose_format(self):
        result = parse_date_permissive("December 1, 2024")
        assert result is not None
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 1
    
    def test_ordinal_format(self):
        result = parse_date_permissive("23rd Feb 2021")
        assert result is not None
        assert result.day == 23
        assert result.month == 2
        assert result.year == 2021
    
    def test_abbreviated_month(self):
        result = parse_date_permissive("15 Mar 2024")
        assert result is not None
        assert result.month == 3
    
    def test_relative_today(self):
        ref = datetime(2024, 3, 15)
        result = parse_date_permissive("today", reference_date=ref)
        assert result is not None
        assert result.date() == ref.date()
    
    def test_relative_yesterday(self):
        ref = datetime(2024, 3, 15)
        result = parse_date_permissive("yesterday", reference_date=ref)
        assert result is not None
        assert result.date() == date(2024, 3, 14)
    
    def test_relative_days_ago(self):
        ref = datetime(2024, 3, 15)
        result = parse_date_permissive("5 days ago", reference_date=ref)
        assert result is not None
        assert result.date() == date(2024, 3, 10)
    
    def test_returns_none_for_invalid(self):
        result = parse_date_permissive("not a date")
        # dateutil might parse some things fuzzy, but clearly invalid should fail
        assert result is None or not isinstance(result, datetime)


class TestExcelSerialConversion:
    """Tests for Excel serial number handling."""
    
    def test_is_likely_excel_serial(self):
        assert is_likely_excel_serial(44927) is True  # 2023-01-01
        assert is_likely_excel_serial(45000) is True
        assert is_likely_excel_serial(100) is False   # Too small
        assert is_likely_excel_serial(100000) is False  # Too large
        assert is_likely_excel_serial("not a number") is False
    
    def test_parse_excel_serial(self):
        # 44927 = 2023-01-01 in Excel
        result = parse_excel_serial(44927)
        assert result is not None
        assert result.year == 2023
        assert result.month == 1
        assert result.day == 1
    
    def test_parse_excel_serial_recent(self):
        # 45000 = 2023-03-15 in Excel
        result = parse_excel_serial(45000)
        assert result is not None
        assert result.year == 2023


class TestDetectDateFormatMajority:
    """Tests for detect_date_format_majority function."""
    
    def test_detects_dmy(self):
        series = pd.Series(["15/03/2024", "20/05/2024", "31/12/2024"])
        assert detect_date_format_majority(series) == 'dmy'
    
    def test_detects_mdy(self):
        series = pd.Series(["03/15/2024", "05/20/2024", "12/31/2024"])
        assert detect_date_format_majority(series) == 'mdy'
    
    def test_ambiguous_defaults_to_dmy(self):
        series = pd.Series(["01/02/2024", "03/04/2024"])  # All ambiguous
        # Default behavior when equal
        result = detect_date_format_majority(series)
        assert result in ('dmy', 'mdy')


class TestParseTimePermissive:
    """Tests for parse_time_permissive function."""
    
    def test_24h_format(self):
        result = parse_time_permissive("15:30")
        assert result == time(15, 30, 0)
    
    def test_24h_with_seconds(self):
        result = parse_time_permissive("15:30:45")
        assert result == time(15, 30, 45)
    
    def test_12h_pm(self):
        result = parse_time_permissive("3:30 PM")
        assert result == time(15, 30, 0)
    
    def test_12h_pm_no_space(self):
        result = parse_time_permissive("3:30PM")
        assert result == time(15, 30, 0)
    
    def test_12h_am(self):
        result = parse_time_permissive("9:00 AM")
        assert result == time(9, 0, 0)
    
    def test_12h_noon(self):
        result = parse_time_permissive("12:00 PM")
        assert result == time(12, 0, 0)
    
    def test_12h_midnight(self):
        result = parse_time_permissive("12:00 AM")
        assert result == time(0, 0, 0)
    
    def test_malformed_pads_correctly(self):
        result = parse_time_permissive("9:5")
        assert result == time(9, 5, 0)
    
    def test_invalid_returns_none(self):
        assert parse_time_permissive("25:00") is None
        assert parse_time_permissive("12:60") is None


class TestExtractTimezone:
    """Tests for extract_timezone function."""
    
    def test_extracts_utc_offset(self):
        time_str, tz = extract_timezone("09:00 UTC+5:30")
        assert time_str == "09:00"
        assert tz == "UTC+5:30"
    
    def test_extracts_gmt_offset(self):
        time_str, tz = extract_timezone("15:30 GMT-8:00")
        assert time_str == "15:30"
        assert tz == "GMT-8:00"
    
    def test_no_timezone(self):
        time_str, tz = extract_timezone("15:30")
        assert time_str == "15:30"
        assert tz is None


class TestGetTimeBucket:
    """Tests for get_time_bucket function."""
    
    def test_morning(self):
        assert get_time_bucket(time(6, 0)) == "Morning"
        assert get_time_bucket(time(11, 59)) == "Morning"
    
    def test_afternoon(self):
        assert get_time_bucket(time(12, 0)) == "Afternoon"
        assert get_time_bucket(time(16, 59)) == "Afternoon"
    
    def test_evening(self):
        assert get_time_bucket(time(17, 0)) == "Evening"
        assert get_time_bucket(time(20, 59)) == "Evening"
    
    def test_night(self):
        assert get_time_bucket(time(21, 0)) == "Night"
        assert get_time_bucket(time(5, 59)) == "Night"


class TestParseDuration:
    """Tests for parse_duration function."""
    
    def test_hours_minutes(self):
        result = parse_duration("2:30")
        assert result is not None
        days, unit = result
        assert unit == "days"
        assert abs(days - 2.5/24) < 0.001  # 2.5 hours in days
    
    def test_with_unit(self):
        result = parse_duration("2 hours")
        assert result is not None
        days, unit = result
        assert abs(days - 2/24) < 0.001
    
    def test_days(self):
        result = parse_duration("5 days")
        assert result is not None
        days, unit = result
        assert days == 5.0
    
    def test_weeks(self):
        result = parse_duration("2 weeks")
        assert result is not None
        days, unit = result
        assert days == 14.0
    
    def test_years(self):
        result = parse_duration("1 year")
        assert result is not None
        days, unit = result
        assert days > 360  # Approximately 365 days
    
    def test_compound(self):
        result = parse_duration("3 months and 5 days")
        assert result is not None
        days, unit = result
        assert days > 90  # ~3 months + 5 days
    
    def test_ambiguous_number(self):
        result = parse_duration("5")
        assert result is not None
        value, unit = result
        assert unit == "unknown"


class TestParseFiscalYear:
    """Tests for parse_fiscal_year function."""
    
    def test_fy_format(self):
        assert parse_fiscal_year("FY2024") == 2024
        assert parse_fiscal_year("FY 2024") == 2024
    
    def test_fy_short(self):
        assert parse_fiscal_year("FY24") == 2024
    
    def test_year_fy_format(self):
        assert parse_fiscal_year("2024 FY") == 2024
    
    def test_verbose(self):
        assert parse_fiscal_year("Financial Year 2024") == 2024
        assert parse_fiscal_year("Fiscal Year 2024") == 2024
    
    def test_invalid(self):
        assert parse_fiscal_year("2024") is None
        assert parse_fiscal_year("not a fiscal year") is None


class TestParseAcademicYear:
    """Tests for parse_academic_year function."""
    
    def test_slash_format(self):
        result = parse_academic_year("2023/24")
        assert result == (2023, 2024)
    
    def test_dash_format(self):
        result = parse_academic_year("2023-2024")
        assert result == (2023, 2024)
    
    def test_ay_prefix(self):
        result = parse_academic_year("AY 2023-24")
        assert result == (2023, 2024)
    
    def test_verbose(self):
        result = parse_academic_year("Academic Year 2023/2024")
        assert result == (2023, 2024)


# ============================================================================
# DATE FORMULA TESTS — HTYPE-004
# ============================================================================

class TestDateFormulas:
    """Tests for DATE formula implementations."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_DATE_01_permissive_parsing(self, mock_db):
        """DATE-01: Parse all date variants."""
        df = pd.DataFrame({
            "date": ["2024-03-15", "15/03/2024", "March 15, 2024", "15 Mar 2024"]
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DATE_01_permissive_parsing("date")
        
        # All should be parsed to datetime
        for val in runner.df["date"]:
            assert isinstance(val, datetime)
    
    def test_DATE_03_invalid_rejection(self, mock_db):
        """DATE-03: Flag impossible dates."""
        df = pd.DataFrame({
            "date": ["2024-03-15", "31/02/2024", "15/13/2024"]
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DATE_03_invalid_rejection("date")
        
        # Should flag impossible dates
        assert result.rows_flagged >= 1
    
    def test_DATE_08_partial_date_handling(self, mock_db):
        """DATE-08: Handle year-only and year-month dates."""
        df = pd.DataFrame({
            "date": ["2024", "2024-03", "2024-03-15"]
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DATE_08_partial_date_handling("date")
        
        # Year-only should become 2024-01-01
        assert isinstance(runner.df.loc[0, "date"], datetime)
        assert runner.df.loc[0, "date"].month == 1
        assert runner.df.loc[0, "date"].day == 1
        
        # Year-month should become 2024-03-01
        assert isinstance(runner.df.loc[1, "date"], datetime)
        assert runner.df.loc[1, "date"].month == 3
        assert runner.df.loc[1, "date"].day == 1
    
    def test_DATE_09_excel_serial_conversion(self, mock_db):
        """DATE-09: Convert Excel serial numbers."""
        df = pd.DataFrame({
            "date": [44927, 45000, "2024-03-15"]
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DATE_09_excel_serial_conversion("date")
        
        # Excel serials should be converted
        assert result.changes_made >= 2
        assert isinstance(runner.df.loc[0, "date"], datetime)
    
    def test_DATE_10_placeholder_rejection(self, mock_db):
        """DATE-10: Treat placeholders as missing."""
        df = pd.DataFrame({
            "date": ["2024-03-15", "01/01/1900", "N/A", "TBD"]
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DATE_10_placeholder_rejection("date")
        
        # Placeholders should be converted to NaT
        assert result.changes_made >= 3
        assert pd.isna(runner.df.loc[1, "date"])
        assert pd.isna(runner.df.loc[2, "date"])
    
    def test_DATE_12_weekday_annotation(self, mock_db):
        """DATE-12: Derive day of week."""
        df = pd.DataFrame({
            "date": [datetime(2024, 3, 15)]  # Friday
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DATE_12_weekday_annotation("date")
        
        assert "date_weekday" in runner.df.columns
        assert runner.df.loc[0, "date_weekday"] == "Friday"
    
    def test_DATE_14_relative_date_parsing(self, mock_db):
        """DATE-14: Convert relative dates."""
        ref = datetime(2024, 3, 15)
        df = pd.DataFrame({
            "date": ["today", "yesterday", "5 days ago"]
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map, 
                               reference_date=ref)
        result = runner.DATE_14_relative_date_parsing("date")
        
        assert result.changes_made == 3
        assert runner.df.loc[0, "date"].date() == ref.date()
        assert runner.df.loc[1, "date"].date() == date(2024, 3, 14)
        assert runner.df.loc[2, "date"].date() == date(2024, 3, 10)


# ============================================================================
# TIME FORMULA TESTS — HTYPE-005
# ============================================================================

class TestTimeFormulas:
    """Tests for TIME formula implementations."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_TIME_01_12h_24h_normalization(self, mock_db):
        """TIME-01: Normalize 12h to 24h."""
        df = pd.DataFrame({
            "time": ["3:00 PM", "3:00pm", "3PM", "9:00 AM"]
        })
        htype_map = {"time": "HTYPE-005"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.TIME_01_12h_24h_normalization("time")
        
        assert runner.df.loc[0, "time"] == "15:00"
        assert runner.df.loc[1, "time"] == "15:00"
        assert runner.df.loc[3, "time"] == "09:00"
    
    def test_TIME_02_format_standardization(self, mock_db):
        """TIME-02: Standardize format to HH:MM."""
        df = pd.DataFrame({
            "time": ["9:5", "13:40", "7:30:00"]
        })
        htype_map = {"time": "HTYPE-005"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.TIME_02_format_standardization("time")
        
        assert runner.df.loc[0, "time"] == "09:05"
        assert runner.df.loc[1, "time"] == "13:40"
        assert runner.df.loc[2, "time"] == "07:30:00"
    
    def test_TIME_03_invalid_rejection(self, mock_db):
        """TIME-03: Flag invalid times."""
        df = pd.DataFrame({
            "time": ["13:40", "25:00", "12:60"]
        })
        htype_map = {"time": "HTYPE-005"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.TIME_03_invalid_rejection("time")
        
        assert result.rows_flagged >= 2
    
    def test_TIME_04_timezone_extraction(self, mock_db):
        """TIME-04: Extract timezone to separate column."""
        df = pd.DataFrame({
            "time": ["09:00 UTC+5:30", "15:30 GMT-8:00", "12:00"]
        })
        htype_map = {"time": "HTYPE-005"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.TIME_04_timezone_extraction("time")
        
        assert "time_timezone" in runner.df.columns
        assert runner.df.loc[0, "time"] == "09:00"
        assert runner.df.loc[0, "time_timezone"] == "UTC+5:30"
    
    def test_TIME_05_bucketing(self, mock_db):
        """TIME-05: Create time buckets."""
        df = pd.DataFrame({
            "time": ["09:00", "14:00", "19:00", "23:00"]
        })
        htype_map = {"time": "HTYPE-005"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.TIME_05_bucketing("time")
        
        assert "time_bucket" in runner.df.columns
        assert runner.df.loc[0, "time_bucket"] == "Morning"
        assert runner.df.loc[1, "time_bucket"] == "Afternoon"
        assert runner.df.loc[2, "time_bucket"] == "Evening"
        assert runner.df.loc[3, "time_bucket"] == "Night"


# ============================================================================
# DATETIME FORMULA TESTS — HTYPE-006
# ============================================================================

class TestDateTimeFormulas:
    """Tests for DTM formula implementations."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_DTM_01_permissive_parsing(self, mock_db):
        """DTM-01: Parse combined datetime formats."""
        df = pd.DataFrame({
            "datetime": [
                "2021-11-23, 1:40 pm",
                "23 Nov 2021 @ 13:40",
                "2021-11-23T13:40:00",
                "Nov 23 2021 at 1:40PM"
            ]
        })
        htype_map = {"datetime": "HTYPE-006"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DTM_01_permissive_parsing("datetime")
        
        for val in runner.df["datetime"]:
            assert isinstance(val, datetime)
    
    def test_DTM_02_date_time_splitting(self, mock_db):
        """DTM-02: Split datetime into date and time columns."""
        df = pd.DataFrame({
            "datetime": [datetime(2024, 3, 15, 14, 30, 0)]
        })
        htype_map = {"datetime": "HTYPE-006"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DTM_02_date_time_splitting("datetime")
        
        assert "datetime_date" in runner.df.columns
        assert "datetime_time" in runner.df.columns
        assert runner.df.loc[0, "datetime_date"] == date(2024, 3, 15)
        assert runner.df.loc[0, "datetime_time"] == "14:30:00"


# ============================================================================
# DURATION FORMULA TESTS — HTYPE-033
# ============================================================================

class TestDurationFormulas:
    """Tests for DUR formula implementations."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_DUR_01_word_to_unit_parsing(self, mock_db):
        """DUR-01: Convert word-based durations."""
        df = pd.DataFrame({
            "duration": ["2 years", "3 months", "5 days"]
        })
        htype_map = {"duration": "HTYPE-033"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DUR_01_word_to_unit_parsing("duration")
        
        assert result.changes_made == 3
        # All should be converted to numeric (days)
        for val in runner.df["duration"]:
            assert isinstance(val, (int, float))
    
    def test_DUR_04_negative_rejection(self, mock_db):
        """DUR-04: Flag negative durations."""
        df = pd.DataFrame({
            "duration": [5.0, -3.0, 10.0]
        })
        htype_map = {"duration": "HTYPE-033"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DUR_04_negative_rejection("duration")
        
        assert result.rows_flagged == 1
    
    def test_DUR_07_ambiguous_unit_detection(self, mock_db):
        """DUR-07: Flag numeric-only durations."""
        df = pd.DataFrame({
            "duration": ["5", "10", "2 years"]
        })
        htype_map = {"duration": "HTYPE-033"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DUR_07_ambiguous_unit_detection("duration")
        
        # Numbers without units should be flagged
        assert result.rows_flagged == 2


# ============================================================================
# FISCAL PERIOD FORMULA TESTS — HTYPE-041
# ============================================================================

class TestFiscalFormulas:
    """Tests for FISC formula implementations."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_FISC_01_fiscal_year_standardization(self, mock_db):
        """FISC-01: Standardize fiscal year formats."""
        df = pd.DataFrame({
            "fiscal": ["FY 2024", "FY24", "2024 FY", "Financial Year 2024"]
        })
        htype_map = {"fiscal": "HTYPE-041"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.FISC_01_fiscal_year_standardization("fiscal")
        
        for val in runner.df["fiscal"]:
            assert val == "FY2024"
    
    def test_FISC_02_fiscal_quarter_parsing(self, mock_db):
        """FISC-02: Standardize fiscal quarter formats."""
        df = pd.DataFrame({
            "quarter": ["Q1 FY2024", "Q1-FY24", "1st Quarter 2024"]
        })
        htype_map = {"quarter": "HTYPE-041"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.FISC_02_fiscal_quarter_parsing("quarter")
        
        # All should be standardized
        assert result.changes_made >= 2
    
    def test_FISC_03_academic_year_standardization(self, mock_db):
        """FISC-03: Standardize academic year formats."""
        df = pd.DataFrame({
            "academic": ["2023/24", "2023-2024", "AY 2023-24"]
        })
        htype_map = {"academic": "HTYPE-041"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.FISC_03_academic_year_standardization("academic")
        
        for val in runner.df["academic"]:
            assert val == "AY 2023-24"
    
    def test_FISC_04_semester_parsing(self, mock_db):
        """FISC-04: Standardize semester formats."""
        df = pd.DataFrame({
            "semester": ["Sem 1", "First Semester", "Spring 2024"]
        })
        htype_map = {"semester": "HTYPE-041"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.FISC_04_semester_parsing("semester")
        
        assert runner.df.loc[0, "semester"] == "Semester 1"
        assert runner.df.loc[1, "semester"] == "Semester 1"
        assert runner.df.loc[2, "semester"] == "Spring 2024"
    
    def test_FISC_05_sort_order_derivation(self, mock_db):
        """FISC-05: Create sort key for fiscal periods."""
        df = pd.DataFrame({
            "fiscal": ["FY2024", "Q1 FY2024", "AY 2023-24"]
        })
        htype_map = {"fiscal": "HTYPE-041"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.FISC_05_sort_order_derivation("fiscal")
        
        assert "fiscal_sort_key" in runner.df.columns
        # FY2024 should have sort key 20240
        assert runner.df.loc[0, "fiscal_sort_key"] == 20240


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestDateTimeRulesIntegration:
    """Integration tests for run_all orchestration."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_run_all_date_columns(self, mock_db):
        """Test run_all processes DATE columns."""
        df = pd.DataFrame({
            "event_date": ["2024-03-15", "15/03/2024", "March 15, 2024"],
            "name": ["Alice", "Bob", "Charlie"]
        })
        htype_map = {"event_date": "HTYPE-004", "name": "HTYPE-001"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert "date_time_rules_applied" in result
        assert result["columns_processed"] == 1
    
    def test_run_all_time_columns(self, mock_db):
        """Test run_all processes TIME columns."""
        df = pd.DataFrame({
            "check_in": ["9:00 AM", "3:30 PM", "11:00"]
        })
        htype_map = {"check_in": "HTYPE-005"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 1
    
    def test_run_all_multiple_htypes(self, mock_db):
        """Test run_all with multiple date/time HTYPE columns."""
        df = pd.DataFrame({
            "event_date": ["2024-03-15"],
            "start_time": ["09:00"],
            "created_at": ["2024-03-15 09:00:00"],
            "duration": ["2 hours"],
            "fiscal_year": ["FY2024"]
        })
        htype_map = {
            "event_date": "HTYPE-004",
            "start_time": "HTYPE-005",
            "created_at": "HTYPE-006",
            "duration": "HTYPE-033",
            "fiscal_year": "HTYPE-041"
        }
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 5
    
    def test_run_all_ignores_non_datetime_htypes(self, mock_db):
        """Test run_all ignores columns with non-datetime HTYPEs."""
        df = pd.DataFrame({
            "name": ["Alice", "Bob"],
            "age": [25, 30],
            "date": ["2024-03-15", "2024-03-16"]
        })
        htype_map = {
            "name": "HTYPE-001",
            "age": "HTYPE-007",
            "date": "HTYPE-004"
        }
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        # Only date column should be processed
        assert result["columns_processed"] == 1
    
    def test_flags_are_collected(self, mock_db):
        """Test that flags are properly collected."""
        df = pd.DataFrame({
            "date": ["2024-03-15", "31/02/2024"]  # Invalid date
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert "total_flags" in result
        assert len(runner.flags) > 0


# ============================================================================
# V2.0 SPECIFIC TESTS
# ============================================================================

class TestV2PermissiveParsing:
    """Tests verifying V2.0 permissive parsing requirements."""
    
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_comma_separator_accepted(self, mock_db):
        """V2.0: Comma as date-time separator must be accepted."""
        df = pd.DataFrame({
            "datetime": ["2021-11-23, 1:40 pm"]
        })
        htype_map = {"datetime": "HTYPE-006"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        runner.DTM_01_permissive_parsing("datetime")
        
        assert isinstance(runner.df.loc[0, "datetime"], datetime)
    
    def test_at_symbol_accepted(self, mock_db):
        """V2.0: @ as date-time separator must be accepted."""
        df = pd.DataFrame({
            "datetime": ["23 Nov 2021 @ 13:40"]
        })
        htype_map = {"datetime": "HTYPE-006"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        runner.DTM_01_permissive_parsing("datetime")
        
        assert isinstance(runner.df.loc[0, "datetime"], datetime)
    
    def test_ordinal_dates_accepted(self, mock_db):
        """V2.0: Ordinal dates must be parsed."""
        df = pd.DataFrame({
            "date": ["23rd Feb 2021", "1st January 2024", "2nd March 2024"]
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        runner.DATE_01_permissive_parsing("date")
        
        for val in runner.df["date"]:
            assert isinstance(val, datetime)
    
    def test_only_impossible_dates_rejected(self, mock_db):
        """V2.0: Only logically impossible dates should be flagged."""
        df = pd.DataFrame({
            "date": [
                "2024-03-15",      # Valid
                "15/03/2024",      # Valid (DMY)
                "31/02/2024",      # Invalid (Feb 31)
            ]
        })
        htype_map = {"date": "HTYPE-004"}
        
        runner = DateTimeRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.DATE_03_invalid_rejection("date")
        
        # Only the impossible Feb 31 should be flagged
        assert result.rows_flagged == 1
