"""
Tests for Numeric & Financial Cleaning Rules — Session 7

Tests all formulas for:
- HTYPE-015: Amount/Currency (AMT-01 to AMT-13)
- HTYPE-016: Quantity/Count (QTY-01 to QTY-09)
- HTYPE-017: Percentage/Rate (PCT-01 to PCT-06)
- HTYPE-021: Score/Rating/Grade (SCORE-01 to SCORE-13)
- HTYPE-042: Currency Code (CUR-01 to CUR-05)
- HTYPE-043: Rank/Ordinal (RANK-01 to RANK-05)
- HTYPE-044: Calculated/Derived (CALC-01 to CALC-05)
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

from app.services.numeric_financial_rules import (
    # Currency helpers
    extract_currency_symbol,
    remove_thousand_separators,
    detect_european_notation,
    convert_european_notation,
    parse_numeric_value,
    standardize_decimals,
    detect_outliers_iqr,
    detect_outliers_zscore,
    # Word to number helpers
    word_to_number,
    extract_number_with_approximation,
    extract_number_with_unit,
    # Percentage helpers
    parse_percentage,
    detect_percentage_format,
    # Score/Grade helpers
    detect_score_scale,
    letter_to_gpa,
    gpa_to_letter,
    parse_rating_ratio,
    fix_grade_descriptor_typo,
    # Rank helpers
    parse_ordinal,
    check_rank_uniqueness,
    check_rank_sequence,
    # Calculated column helpers
    discover_formula,
    verify_calculated_value,
    # Scientific notation
    is_scientific_notation,
    convert_scientific_notation,
    # Main class
    NumericFinancialRules,
)


# ============================================================================
# CURRENCY HELPER TESTS
# ============================================================================

class TestExtractCurrencySymbol:
    def test_dollar_prefix(self):
        code, value = extract_currency_symbol("$100.00")
        assert code == "USD"
        assert value == "100.00"
    
    def test_euro_prefix(self):
        code, value = extract_currency_symbol("€500")
        assert code == "EUR"
        assert value == "500"
    
    def test_rupee_prefix(self):
        code, value = extract_currency_symbol("₹1000")
        assert code == "INR"
        assert value == "1000"
    
    def test_nepali_rupee(self):
        code, value = extract_currency_symbol("रु500")
        assert code == "NPR"
        assert value == "500"
    
    def test_usd_text_prefix(self):
        code, value = extract_currency_symbol("USD 100")
        assert code == "USD"
        assert value == "100"
    
    def test_no_currency(self):
        code, value = extract_currency_symbol("100.00")
        assert code is None
        assert value == "100.00"


class TestRemoveThousandSeparators:
    def test_single_comma(self):
        assert remove_thousand_separators("1,000") == "1000"
    
    def test_multiple_commas(self):
        assert remove_thousand_separators("1,250,000") == "1250000"
    
    def test_decimal_preserved(self):
        assert remove_thousand_separators("1,000.50") == "1000.50"
    
    def test_no_separators(self):
        assert remove_thousand_separators("1000") == "1000"


class TestDetectEuropeanNotation:
    def test_european_format(self):
        assert detect_european_notation("1.234,56") is True
    
    def test_us_format(self):
        assert detect_european_notation("1,234.56") is False
    
    def test_comma_decimal(self):
        assert detect_european_notation("100,50") is True


class TestConvertEuropeanNotation:
    def test_conversion(self):
        # European 1.234,56 -> periods removed, comma becomes period
        result = convert_european_notation("1.234,56")
        # Result is "1234.56" - periods removed, comma converted to decimal
        assert result == "1234.56"


class TestParseNumericValue:
    def test_integer(self):
        assert parse_numeric_value("100") == 100.0
    
    def test_decimal(self):
        assert parse_numeric_value("100.50") == 100.5
    
    def test_with_commas(self):
        assert parse_numeric_value("1,250,000") == 1250000.0
    
    def test_with_currency(self):
        assert parse_numeric_value("$100") == 100.0
    
    def test_negative(self):
        assert parse_numeric_value("-500") == -500.0
    
    def test_none(self):
        assert parse_numeric_value(None) is None
    
    def test_empty_string(self):
        assert parse_numeric_value("") is None


class TestStandardizeDecimals:
    def test_rounds_to_2(self):
        assert standardize_decimals(100.5555, 2) == 100.56
    
    def test_adds_decimals(self):
        assert standardize_decimals(100.0, 2) == 100.0


class TestDetectOutliers:
    def test_iqr_method(self):
        # Need more data points for IQR to work properly
        series = pd.Series([10, 11, 12, 10, 11, 12, 10, 11, 12, 10, 11, 12, 200])  # 200 is outlier
        outliers = detect_outliers_iqr(series)
        assert outliers.iloc[-1] == True  # Last item (200) is outlier
    
    def test_zscore_method(self):
        # Need larger sample for z-score
        series = pd.Series([10, 11, 12, 10, 11, 12, 10, 11, 12, 10, 11, 12, 10, 11, 12, 1000])
        outliers = detect_outliers_zscore(series, threshold=3.0)
        assert outliers.iloc[-1] == True  # Last item (1000) is outlier


# ============================================================================
# WORD TO NUMBER TESTS
# ============================================================================

class TestWordToNumber:
    def test_single_word(self):
        assert word_to_number("five") == 5.0
    
    def test_teen(self):
        assert word_to_number("seventeen") == 17.0
    
    def test_tens(self):
        assert word_to_number("fifty") == 50.0
    
    def test_compound(self):
        assert word_to_number("twenty one") == 21.0
    
    def test_hundred(self):
        assert word_to_number("one hundred") == 100.0
    
    def test_complex(self):
        assert word_to_number("one thousand two hundred thirty four") == 1234.0
    
    def test_million(self):
        assert word_to_number("one million") == 1000000.0
    
    def test_typo_correction(self):
        assert word_to_number("elven") == 11.0  # "elven" -> "eleven"
    
    def test_ordinal_suffix(self):
        assert word_to_number("1st") == 1.0
        assert word_to_number("2nd") == 2.0
    
    def test_invalid(self):
        assert word_to_number("hello") is None


class TestExtractNumberWithApproximation:
    def test_approx_prefix(self):
        num, is_approx = extract_number_with_approximation("approx 50")
        assert num == 50.0
        assert is_approx is True
    
    def test_about_prefix(self):
        num, is_approx = extract_number_with_approximation("about 100")
        assert num == 100.0
        assert is_approx is True
    
    def test_tilde_prefix(self):
        num, is_approx = extract_number_with_approximation("~200")
        assert num == 200.0
        assert is_approx is True
    
    def test_no_approximation(self):
        num, is_approx = extract_number_with_approximation("100")
        assert num == 100.0
        assert is_approx is False


class TestExtractNumberWithUnit:
    def test_kg(self):
        num, unit = extract_number_with_unit("50 kg")
        assert num == 50.0
        assert unit == "kg"
    
    def test_units(self):
        num, unit = extract_number_with_unit("200 units")
        assert num == 200.0
        assert unit == "units"
    
    def test_percentage(self):
        num, unit = extract_number_with_unit("85%")
        assert num == 85.0
        assert unit == "%"


# ============================================================================
# PERCENTAGE HELPER TESTS
# ============================================================================

class TestParsePercentage:
    def test_with_symbol(self):
        assert parse_percentage("85%") == 85.0
    
    def test_without_symbol(self):
        assert parse_percentage("85") == 85.0
    
    def test_decimal(self):
        assert parse_percentage("0.85") == 0.85


class TestDetectPercentageFormat:
    def test_decimal_format(self):
        series = pd.Series([0.1, 0.5, 0.75, 0.95])
        assert detect_percentage_format(series) == "decimal"
    
    def test_whole_format(self):
        series = pd.Series([10, 50, 75, 95])
        assert detect_percentage_format(series) == "whole"


# ============================================================================
# SCORE/GRADE HELPER TESTS
# ============================================================================

class TestDetectScoreScale:
    def test_gpa_4(self):
        series = pd.Series([3.5, 3.7, 4.0, 2.8])
        scale_type, min_val, max_val = detect_score_scale(series)
        assert scale_type == "gpa_4"
    
    def test_scale_10(self):
        series = pd.Series([7.5, 8.0, 9.5, 6.0])
        scale_type, min_val, max_val = detect_score_scale(series)
        assert scale_type == "scale_10"
    
    def test_scale_100(self):
        series = pd.Series([75, 80, 95, 60])
        scale_type, min_val, max_val = detect_score_scale(series)
        assert scale_type == "scale_100"


class TestLetterToGpa:
    def test_a_plus(self):
        assert letter_to_gpa("A+") == 4.0
    
    def test_b(self):
        assert letter_to_gpa("B") == 3.0
    
    def test_c_minus(self):
        assert letter_to_gpa("C-") == 1.7
    
    def test_f(self):
        assert letter_to_gpa("F") == 0.0


class TestGpaToLetter:
    def test_4_0(self):
        assert gpa_to_letter(4.0) == "A"
    
    def test_3_5(self):
        assert gpa_to_letter(3.5) == "B+"
    
    def test_2_0(self):
        assert gpa_to_letter(2.0) == "C"


class TestParseRatingRatio:
    def test_slash_format(self):
        assert parse_rating_ratio("4/5") == 80.0
    
    def test_out_of_format(self):
        assert parse_rating_ratio("8 out of 10") == 80.0
    
    def test_of_format(self):
        assert parse_rating_ratio("3 of 4") == 75.0


class TestFixGradeDescriptorTypo:
    def test_excellent_typo(self):
        fixed, was_typo = fix_grade_descriptor_typo("excelent")
        assert fixed == "Excellent"
        assert was_typo is True
    
    def test_satisfactory_typo(self):
        fixed, was_typo = fix_grade_descriptor_typo("satisfacory")
        assert fixed == "Satisfactory"
        assert was_typo is True
    
    def test_no_typo(self):
        fixed, was_typo = fix_grade_descriptor_typo("Excellent")
        assert was_typo is False


# ============================================================================
# RANK HELPER TESTS
# ============================================================================

class TestParseOrdinal:
    def test_1st(self):
        assert parse_ordinal("1st") == 1
    
    def test_2nd(self):
        assert parse_ordinal("2nd") == 2
    
    def test_3rd(self):
        assert parse_ordinal("3rd") == 3
    
    def test_first(self):
        assert parse_ordinal("first") == 1
    
    def test_second(self):
        assert parse_ordinal("second") == 2


class TestCheckRankUniqueness:
    def test_no_duplicates(self):
        series = pd.Series([1, 2, 3, 4, 5])
        duplicates = check_rank_uniqueness(series)
        assert len(duplicates) == 0
    
    def test_has_duplicates(self):
        series = pd.Series([1, 2, 2, 4, 5])
        duplicates = check_rank_uniqueness(series)
        assert len(duplicates) > 0


class TestCheckRankSequence:
    def test_complete_sequence(self):
        series = pd.Series([1, 2, 3, 4, 5])
        missing = check_rank_sequence(series)
        assert len(missing) == 0
    
    def test_missing_ranks(self):
        series = pd.Series([1, 2, 4, 5])  # Missing 3
        missing = check_rank_sequence(series)
        assert 3 in missing


# ============================================================================
# CALCULATED COLUMN HELPER TESTS
# ============================================================================

class TestDiscoverFormula:
    def test_multiply(self):
        df = pd.DataFrame({
            "qty": [1, 2, 3, 4, 5],
            "price": [10, 10, 10, 10, 10],
            "total": [10, 20, 30, 40, 50],
        })
        result = discover_formula(df, "total")
        assert result is not None
        assert result[0] == "multiply"
    
    def test_add(self):
        df = pd.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [10, 20, 30, 40, 50],
            "sum": [11, 22, 33, 44, 55],
        })
        result = discover_formula(df, "sum")
        assert result is not None
        assert result[0] == "add"


class TestVerifyCalculatedValue:
    def test_correct_multiply(self):
        row = pd.Series({"qty": 5, "price": 10, "total": 50})
        assert verify_calculated_value(row, "multiply", ["qty", "price"], "total") is True
    
    def test_incorrect_multiply(self):
        row = pd.Series({"qty": 5, "price": 10, "total": 100})  # Wrong
        assert verify_calculated_value(row, "multiply", ["qty", "price"], "total") is False


# ============================================================================
# SCIENTIFIC NOTATION TESTS
# ============================================================================

class TestScientificNotation:
    def test_is_scientific(self):
        assert is_scientific_notation("1.25e6") is True
        assert is_scientific_notation("1.25E-3") is True
        assert is_scientific_notation("1250000") is False
    
    def test_convert_scientific(self):
        result = convert_scientific_notation("1.25e6")
        assert float(result) == 1250000.0


# ============================================================================
# AMT FORMULA TESTS
# ============================================================================

class TestAmtFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_AMT_01_currency_removal(self, mock_db):
        """AMT-01: Remove currency symbols."""
        df = pd.DataFrame({
            "price": ["$100.00", "€500", "£250"]
        })
        htype_map = {"price": "HTYPE-015"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.AMT_01_currency_symbol_removal("price")
        
        assert result.changes_made >= 3
        assert runner.df.loc[0, "price"] == 100.0
    
    def test_AMT_02_thousand_separator(self, mock_db):
        """AMT-02: Remove thousand separators."""
        df = pd.DataFrame({
            "amount": ["1,250,000", "500,000", "1000"]
        })
        htype_map = {"amount": "HTYPE-015"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.AMT_02_thousand_separator_removal("amount")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "amount"] == 1250000.0
    
    def test_AMT_08_type_coercion(self, mock_db):
        """AMT-08: Convert string to float."""
        df = pd.DataFrame({
            "value": ["100.50", "200.75", "300"]
        })
        htype_map = {"value": "HTYPE-015"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.AMT_08_type_coercion("value")
        
        assert result.changes_made >= 3
        assert runner.df.loc[0, "value"] == 100.50
    
    def test_AMT_12_scientific_notation(self, mock_db):
        """AMT-12: Convert scientific notation."""
        df = pd.DataFrame({
            "value": ["1.25e6", "5e3", "100"]
        })
        htype_map = {"value": "HTYPE-015"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.AMT_12_scientific_notation_conversion("value")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "value"] == 1250000.0


# ============================================================================
# QTY FORMULA TESTS
# ============================================================================

class TestQtyFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_QTY_01_word_to_number(self, mock_db):
        """QTY-01: Convert word numbers."""
        df = pd.DataFrame({
            "count": ["five", "twelve", "100"]
        })
        htype_map = {"count": "HTYPE-016"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.QTY_01_word_to_number("count")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "count"] == 5
        assert runner.df.loc[1, "count"] == 12
    
    def test_QTY_04_integer_enforcement(self, mock_db):
        """QTY-04: Enforce integer values."""
        df = pd.DataFrame({
            "qty": [10.0, 15.001, 20.5]  # 15.001 is minor rounding, 20.5 is flagged
        })
        htype_map = {"qty": "HTYPE-016"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.QTY_04_integer_enforcement("qty")
        
        assert result.rows_flagged >= 1  # 20.5 should be flagged
    
    def test_QTY_05_negative_rejection(self, mock_db):
        """QTY-05: Flag negative quantities."""
        df = pd.DataFrame({
            "qty": [10, -5, 20]
        })
        htype_map = {"qty": "HTYPE-016"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.QTY_05_negative_rejection("qty")
        
        assert result.rows_flagged >= 1


# ============================================================================
# PCT FORMULA TESTS
# ============================================================================

class TestPctFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_PCT_01_symbol_removal(self, mock_db):
        """PCT-01: Remove % symbol."""
        df = pd.DataFrame({
            "rate": ["85%", "90%", "75"]
        })
        htype_map = {"rate": "HTYPE-017"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.PCT_01_percentage_symbol_removal("rate")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "rate"] == 85.0
    
    def test_PCT_02_range_validation(self, mock_db):
        """PCT-02: Flag out of range percentages."""
        df = pd.DataFrame({
            "rate": [50, 150, -10]  # 150 and -10 out of range
        })
        htype_map = {"rate": "HTYPE-017"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.PCT_02_range_validation("rate")
        
        assert result.rows_flagged >= 2
    
    def test_PCT_03_decimal_detection(self, mock_db):
        """PCT-03: Detect and convert decimal format."""
        df = pd.DataFrame({
            "rate": [0.5, 0.75, 0.9]  # Decimal format
        })
        htype_map = {"rate": "HTYPE-017"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.PCT_03_decimal_vs_whole_detection("rate")
        
        assert result.changes_made >= 3
        assert runner.df.loc[0, "rate"] == 50.0  # 0.5 * 100


# ============================================================================
# SCORE FORMULA TESTS
# ============================================================================

class TestScoreFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_SCORE_01_scale_detection(self, mock_db):
        """SCORE-01: Detect score scale."""
        df = pd.DataFrame({
            "gpa": [3.5, 3.7, 4.0, 2.8]
        })
        htype_map = {"gpa": "HTYPE-021"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.SCORE_01_scale_detection("gpa")
        
        assert result.details["scale_type"] == "gpa_4"
    
    def test_SCORE_03_letter_to_gpa(self, mock_db):
        """SCORE-03: Convert letter grades to GPA."""
        df = pd.DataFrame({
            "grade": ["A", "B+", "C", "F"]
        })
        htype_map = {"grade": "HTYPE-021"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.SCORE_03_gpa_4_scale("grade")
        
        assert result.changes_made >= 4
        assert runner.df.loc[0, "grade"] == 4.0
        assert runner.df.loc[3, "grade"] == 0.0
    
    def test_SCORE_12_rating_normalization(self, mock_db):
        """SCORE-12: Normalize rating ratios."""
        df = pd.DataFrame({
            "rating": ["4/5", "8/10", "3 out of 4"]
        })
        htype_map = {"rating": "HTYPE-021"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.SCORE_12_rating_scale_normalization("rating")
        
        assert result.changes_made >= 3
        assert runner.df.loc[0, "rating"] == 80.0
    
    def test_SCORE_13_typo_correction(self, mock_db):
        """SCORE-13: Fix grade descriptor typos."""
        df = pd.DataFrame({
            "grade": ["excelent", "satisfacory", "Good"]
        })
        htype_map = {"grade": "HTYPE-021"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.SCORE_13_grade_descriptor_typo("grade")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "grade"] == "Excellent"


# ============================================================================
# CUR FORMULA TESTS
# ============================================================================

class TestCurFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_CUR_02_uppercase(self, mock_db):
        """CUR-02: Uppercase currency codes."""
        df = pd.DataFrame({
            "currency": ["usd", "eur", "NPR"]
        })
        htype_map = {"currency": "HTYPE-042"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.CUR_02_uppercase_standardization("currency")
        
        assert result.changes_made >= 2
        assert runner.df.loc[0, "currency"] == "USD"
    
    def test_CUR_03_symbol_to_code(self, mock_db):
        """CUR-03: Convert symbols to ISO codes."""
        df = pd.DataFrame({
            "currency": ["$", "€", "£"]
        })
        htype_map = {"currency": "HTYPE-042"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.CUR_03_symbol_to_code("currency")
        
        assert result.changes_made >= 3
        assert runner.df.loc[0, "currency"] == "USD"
        assert runner.df.loc[1, "currency"] == "EUR"


# ============================================================================
# RANK FORMULA TESTS
# ============================================================================

class TestRankFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_RANK_01_ordinal_conversion(self, mock_db):
        """RANK-01: Convert ordinals to integers."""
        df = pd.DataFrame({
            "rank": ["1st", "2nd", "third", "4"]
        })
        htype_map = {"rank": "HTYPE-043"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.RANK_01_ordinal_to_numeric("rank")
        
        assert result.changes_made >= 3
        assert runner.df.loc[0, "rank"] == 1
        assert runner.df.loc[2, "rank"] == 3
    
    def test_RANK_04_negative_rejection(self, mock_db):
        """RANK-04: Flag non-positive ranks."""
        df = pd.DataFrame({
            "rank": [1, 0, -1, 2]
        })
        htype_map = {"rank": "HTYPE-043"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.RANK_04_negative_rejection("rank")
        
        assert result.rows_flagged >= 2  # 0 and -1


# ============================================================================
# CALC FORMULA TESTS
# ============================================================================

class TestCalcFormulas:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_CALC_01_formula_discovery(self, mock_db):
        """CALC-01: Discover formula."""
        df = pd.DataFrame({
            "qty": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "price": [10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
            "total": [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
        })
        htype_map = {"total": "HTYPE-044"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.CALC_01_formula_discovery("total")
        
        assert "formula_type" in result.details
        assert result.details["formula_type"] == "multiply"


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestNumericFinancialRulesIntegration:
    @pytest.fixture
    def mock_db(self):
        db = MagicMock()
        db.add = MagicMock()
        db.flush = MagicMock()
        return db
    
    def test_run_all_amount_column(self, mock_db):
        """Test run_all processes amount columns."""
        df = pd.DataFrame({
            "price": ["$100.00", "$1,500.50", "€200"]
        })
        htype_map = {"price": "HTYPE-015"}
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 1
        assert "AMT-01" in result["formulas_applied"]
    
    def test_run_all_multiple_htypes(self, mock_db):
        """Test run_all with multiple numeric columns."""
        df = pd.DataFrame({
            "price": ["$100.00"],
            "qty": ["five"],
            "rate": ["85%"],
            "rank": ["1st"],
        })
        htype_map = {
            "price": "HTYPE-015",
            "qty": "HTYPE-016",
            "rate": "HTYPE-017",
            "rank": "HTYPE-043",
        }
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 4
        assert result["total_changes"] > 0
    
    def test_run_all_ignores_non_numeric_htypes(self, mock_db):
        """Test run_all ignores non-numeric HTYPEs."""
        df = pd.DataFrame({
            "name": ["John Doe"],
            "email": ["john@test.com"],
        })
        htype_map = {
            "name": "HTYPE-001",
            "email": "HTYPE-010",
        }
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert result["columns_processed"] == 0
    
    def test_flags_are_collected(self, mock_db):
        """Test that flags are properly collected."""
        df = pd.DataFrame({
            "rate": [50, 150, -10],  # 150 and -10 out of range
            "qty": [10, -5, 20],      # -5 is negative
        })
        htype_map = {
            "rate": "HTYPE-017",
            "qty": "HTYPE-016",
        }
        
        runner = NumericFinancialRules(job_id=1, df=df, db=mock_db, htype_map=htype_map)
        result = runner.run_all()
        
        assert "total_flags" in result
        assert len(runner.flags) > 0
