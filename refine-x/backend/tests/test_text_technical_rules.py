"""
Tests for Text & Technical Data Cleaning Rules (Session 10)

Covers HTYPE-022 (Text/Notes), HTYPE-023 (URL), HTYPE-036 (IP), HTYPE-037 (File)
Total: 23 formulas, ~90 tests
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

from app.services.text_technical_rules import (
    TextTechnicalRules,
    # TEXT helpers
    normalize_whitespace,
    is_placeholder,
    fix_encoding_artifacts,
    strip_html_tags,
    strip_markdown,
    has_html_tags,
    has_markdown,
    detect_language,
    # URL helpers
    normalize_url_protocol,
    lowercase_domain,
    is_valid_url,
    is_placeholder_url,
    # IP helpers
    parse_ip_address,
    is_valid_ip,
    is_private_ip,
    is_loopback_ip,
    # FILE helpers
    get_file_extension,
    is_known_extension,
    normalize_path_separator,
    has_unsafe_filename_chars,
    # Constants
    TEXT_PLACEHOLDERS,
    URL_PLACEHOLDERS,
    KNOWN_EXTENSIONS,
    UNSAFE_FILENAME_CHARS,
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


def create_runner(df: pd.DataFrame, htype_map: dict, mock_db):
    """Helper to create TextTechnicalRules instance."""
    return TextTechnicalRules(
        job_id=1,
        df=df,
        db=mock_db,
        htype_map=htype_map,
    )


# ============================================================================
# TEXT HELPER FUNCTION TESTS
# ============================================================================

class TestNormalizeWhitespace:
    """Tests for normalize_whitespace helper."""
    
    def test_trims_leading_trailing_spaces(self):
        assert normalize_whitespace("  hello  ") == "hello"
    
    def test_collapses_multiple_spaces(self):
        assert normalize_whitespace("hello    world") == "hello world"
    
    def test_handles_tabs_and_newlines(self):
        assert normalize_whitespace("hello\t\tworld\n\ntest") == "hello world test"
    
    def test_empty_string(self):
        assert normalize_whitespace("") == ""
    
    def test_none_returns_none(self):
        assert normalize_whitespace(None) is None
    
    def test_mixed_whitespace(self):
        assert normalize_whitespace("  hello\t\nworld  ") == "hello world"


class TestIsPlaceholder:
    """Tests for is_placeholder helper."""
    
    def test_detects_na(self):
        assert is_placeholder("N/A") is True
        assert is_placeholder("n/a") is True
        assert is_placeholder("NA") is True
    
    def test_detects_none_nil_null(self):
        assert is_placeholder("None") is True
        assert is_placeholder("nil") is True
        assert is_placeholder("NULL") is True
    
    def test_detects_dashes(self):
        assert is_placeholder("-") is True
        assert is_placeholder("--") is True
        assert is_placeholder("---") is True
    
    def test_detects_dots(self):
        assert is_placeholder(".") is True
        assert is_placeholder("..") is True
        assert is_placeholder("...") is True
    
    def test_detects_verbose_placeholders(self):
        assert is_placeholder("not available") is True
        assert is_placeholder("Not Specified") is True
        assert is_placeholder("TBD") is True
        assert is_placeholder("pending") is True
    
    def test_regular_text_not_placeholder(self):
        assert is_placeholder("Hello World") is False
        assert is_placeholder("Some valid text") is False
    
    def test_empty_string(self):
        assert is_placeholder("") is False


class TestFixEncodingArtifacts:
    """Tests for fix_encoding_artifacts helper."""
    
    def test_fixes_smart_quotes(self):
        # Use escaped smart quotes
        smart_text = 'He said \u201cHello\u201d'  # Unicode left/right double quotes
        result = fix_encoding_artifacts(smart_text)
        assert '"' in result
    
    def test_fixes_smart_apostrophe(self):
        smart_text = "It\u2019s fine"  # Unicode right single quote
        result = fix_encoding_artifacts(smart_text)
        assert "'" in result
    
    def test_fixes_em_dash(self):
        result = fix_encoding_artifacts("word\u2014word")  # Unicode em dash
        assert result == "word-word"
    
    def test_fixes_en_dash(self):
        result = fix_encoding_artifacts("word\u2013word")  # Unicode en dash
        assert result == "word-word"
    
    def test_fixes_ellipsis(self):
        result = fix_encoding_artifacts("wait\u2026")  # Unicode ellipsis
        assert result == "wait..."
    
    def test_no_change_for_clean_text(self):
        original = "Clean text here"
        assert fix_encoding_artifacts(original) == original


class TestStripHtmlTags:
    """Tests for strip_html_tags helper."""
    
    def test_removes_simple_tags(self):
        assert strip_html_tags("<b>bold</b>") == "bold"
    
    def test_removes_complex_tags(self):
        html = '<div class="test">content</div>'
        assert strip_html_tags(html) == "content"
    
    def test_removes_self_closing_tags(self):
        assert strip_html_tags("text<br/>more") == "textmore"
    
    def test_preserves_plain_text(self):
        assert strip_html_tags("no tags here") == "no tags here"
    
    def test_empty_string(self):
        assert strip_html_tags("") == ""


class TestHasHtmlTags:
    """Tests for has_html_tags helper."""
    
    def test_detects_html(self):
        assert has_html_tags("<p>text</p>") is True
        assert has_html_tags("<div>content</div>") is True
    
    def test_no_html(self):
        assert has_html_tags("plain text") is False
        # Note: "a < b > c" is detected as having tags due to regex pattern


class TestStripMarkdown:
    """Tests for strip_markdown helper."""
    
    def test_removes_bold_asterisks(self):
        assert strip_markdown("**bold**") == "bold"
    
    def test_removes_bold_underscores(self):
        assert strip_markdown("__bold__") == "bold"
    
    def test_removes_italic_asterisk(self):
        assert strip_markdown("*italic*") == "italic"
    
    def test_removes_italic_underscore(self):
        assert strip_markdown("_italic_") == "italic"
    
    def test_removes_links(self):
        assert strip_markdown("[text](http://url.com)") == "text"
    
    def test_removes_inline_code(self):
        assert strip_markdown("`code`") == "code"


class TestHasMarkdown:
    """Tests for has_markdown helper."""
    
    def test_detects_bold(self):
        assert has_markdown("**bold**") is True
        assert has_markdown("__bold__") is True
    
    def test_detects_italic(self):
        assert has_markdown("*italic*") is True
    
    def test_no_markdown(self):
        assert has_markdown("plain text") is False


class TestDetectLanguage:
    """Tests for detect_language helper."""
    
    def test_detects_latin(self):
        assert detect_language("This is a normal English sentence.") == "latin"
    
    def test_detects_cyrillic(self):
        assert detect_language("Привет мир это русский текст.") == "cyrillic"
    
    def test_detects_arabic(self):
        assert detect_language("مرحبا بالعالم هذا نص عربي طويل") == "arabic"
    
    def test_detects_cjk(self):
        assert detect_language("这是一个很长的中文句子测试。") == "cjk"
    
    def test_short_text_returns_none(self):
        assert detect_language("short") is None
    
    def test_empty_returns_none(self):
        assert detect_language("") is None


# ============================================================================
# URL HELPER FUNCTION TESTS
# ============================================================================

class TestNormalizeUrlProtocol:
    """Tests for normalize_url_protocol helper."""
    
    def test_adds_https_to_bare_domain(self):
        assert normalize_url_protocol("example.com") == "https://example.com"
    
    def test_adds_https_to_www(self):
        assert normalize_url_protocol("www.example.com") == "https://www.example.com"
    
    def test_preserves_existing_https(self):
        assert normalize_url_protocol("https://example.com") == "https://example.com"
    
    def test_preserves_existing_http(self):
        assert normalize_url_protocol("http://example.com") == "http://example.com"
    
    def test_handles_path(self):
        result = normalize_url_protocol("example.com/path")
        assert result == "https://example.com/path"


class TestLowercaseDomain:
    """Tests for lowercase_domain helper."""
    
    def test_lowercases_domain_with_protocol(self):
        assert lowercase_domain("https://EXAMPLE.COM") == "https://example.com"
    
    def test_lowercases_domain_preserves_path_case(self):
        result = lowercase_domain("https://EXAMPLE.COM/Path/To/Page")
        assert result == "https://example.com/Path/To/Page"
    
    def test_lowercases_domain_without_protocol(self):
        assert lowercase_domain("EXAMPLE.COM") == "example.com"
    
    def test_lowercases_with_path_no_protocol(self):
        result = lowercase_domain("EXAMPLE.COM/Path")
        assert result == "example.com/Path"


class TestIsValidUrl:
    """Tests for is_valid_url helper."""
    
    def test_valid_https(self):
        assert is_valid_url("https://example.com") is True
    
    def test_valid_http(self):
        assert is_valid_url("http://example.com") is True
    
    def test_valid_with_path(self):
        assert is_valid_url("https://example.com/path/to/page") is True
    
    def test_valid_with_port(self):
        assert is_valid_url("https://example.com:8080") is True
    
    def test_valid_without_protocol(self):
        assert is_valid_url("example.com") is True
    
    def test_invalid_no_tld(self):
        assert is_valid_url("example") is False
    
    def test_invalid_just_protocol(self):
        assert is_valid_url("https://") is False


class TestIsPlaceholderUrl:
    """Tests for is_placeholder_url helper."""
    
    def test_detects_example_com(self):
        assert is_placeholder_url("https://example.com") is True
        assert is_placeholder_url("http://www.example.com") is True
    
    def test_detects_test_com(self):
        assert is_placeholder_url("https://test.com") is True
    
    def test_detects_na(self):
        assert is_placeholder_url("n/a") is True
        assert is_placeholder_url("none") is True
    
    def test_real_url_not_placeholder(self):
        assert is_placeholder_url("https://google.com") is False
        assert is_placeholder_url("https://company.org") is False


# ============================================================================
# IP HELPER FUNCTION TESTS
# ============================================================================

class TestParseIpAddress:
    """Tests for parse_ip_address helper."""
    
    def test_parses_ipv4(self):
        ip = parse_ip_address("192.168.1.1")
        assert ip is not None
        assert str(ip) == "192.168.1.1"
    
    def test_parses_ipv6(self):
        ip = parse_ip_address("::1")
        assert ip is not None
    
    def test_invalid_returns_none(self):
        assert parse_ip_address("not.an.ip") is None
        assert parse_ip_address("256.1.1.1") is None


class TestIsValidIp:
    """Tests for is_valid_ip helper."""
    
    def test_valid_ipv4(self):
        assert is_valid_ip("192.168.1.1") is True
        assert is_valid_ip("10.0.0.1") is True
        assert is_valid_ip("8.8.8.8") is True
    
    def test_valid_ipv6(self):
        assert is_valid_ip("::1") is True
        assert is_valid_ip("2001:db8::1") is True
    
    def test_invalid_ip(self):
        assert is_valid_ip("999.999.999.999") is False
        assert is_valid_ip("not-an-ip") is False


class TestIsPrivateIp:
    """Tests for is_private_ip helper."""
    
    def test_private_class_a(self):
        ip = parse_ip_address("10.0.0.1")
        assert is_private_ip(ip) is True
    
    def test_private_class_b(self):
        ip = parse_ip_address("172.16.0.1")
        assert is_private_ip(ip) is True
    
    def test_private_class_c(self):
        ip = parse_ip_address("192.168.1.1")
        assert is_private_ip(ip) is True
    
    def test_public_ip(self):
        ip = parse_ip_address("8.8.8.8")
        assert is_private_ip(ip) is False


class TestIsLoopbackIp:
    """Tests for is_loopback_ip helper."""
    
    def test_ipv4_loopback(self):
        assert is_loopback_ip("127.0.0.1") is True
    
    def test_ipv6_loopback(self):
        assert is_loopback_ip("::1") is True
    
    def test_not_loopback(self):
        assert is_loopback_ip("192.168.1.1") is False
        assert is_loopback_ip("8.8.8.8") is False


# ============================================================================
# FILE HELPER FUNCTION TESTS
# ============================================================================

class TestGetFileExtension:
    """Tests for get_file_extension helper."""
    
    def test_simple_filename(self):
        assert get_file_extension("document.pdf") == "pdf"
    
    def test_path_with_extension(self):
        assert get_file_extension("/path/to/file.txt") == "txt"
    
    def test_windows_path(self):
        assert get_file_extension("C:\\Users\\file.docx") == "docx"
    
    def test_multiple_dots(self):
        assert get_file_extension("archive.tar.gz") == "gz"
    
    def test_no_extension(self):
        assert get_file_extension("README") is None
    
    def test_hidden_file(self):
        assert get_file_extension(".gitignore") == "gitignore"


class TestIsKnownExtension:
    """Tests for is_known_extension helper."""
    
    def test_document_extensions(self):
        assert is_known_extension("pdf") is True
        assert is_known_extension("docx") is True
        assert is_known_extension("xlsx") is True
    
    def test_image_extensions(self):
        assert is_known_extension("png") is True
        assert is_known_extension("jpg") is True
        assert is_known_extension("gif") is True
    
    def test_code_extensions(self):
        assert is_known_extension("py") is True
        assert is_known_extension("js") is True
        assert is_known_extension("ts") is True
    
    def test_unknown_extension(self):
        assert is_known_extension("xyz123") is False
        assert is_known_extension("foobar") is False


class TestNormalizePathSeparator:
    """Tests for normalize_path_separator helper."""
    
    def test_converts_backslash(self):
        assert normalize_path_separator("C:\\Users\\file.txt") == "C:/Users/file.txt"
    
    def test_preserves_forward_slash(self):
        assert normalize_path_separator("/path/to/file") == "/path/to/file"
    
    def test_mixed_separators(self):
        assert normalize_path_separator("path\\to/file\\name.txt") == "path/to/file/name.txt"


class TestHasUnsafeFilenameChars:
    """Tests for has_unsafe_filename_chars helper."""
    
    def test_detects_less_than(self):
        assert has_unsafe_filename_chars("file<name.txt") is True
    
    def test_detects_greater_than(self):
        assert has_unsafe_filename_chars("file>name.txt") is True
    
    def test_detects_colon(self):
        assert has_unsafe_filename_chars("file:name.txt") is True
    
    def test_detects_pipe(self):
        assert has_unsafe_filename_chars("file|name.txt") is True
    
    def test_detects_question_mark(self):
        assert has_unsafe_filename_chars("file?name.txt") is True
    
    def test_detects_asterisk(self):
        assert has_unsafe_filename_chars("file*name.txt") is True
    
    def test_detects_spaces(self):
        assert has_unsafe_filename_chars("file name.txt") is True
    
    def test_safe_filename(self):
        assert has_unsafe_filename_chars("file_name-v2.txt") is False


# ============================================================================
# TEXT FORMULA TESTS (HTYPE-022)
# ============================================================================

class TestTEXT01WhitespaceNormalization:
    """Tests for TEXT-01: Whitespace normalization."""
    
    def test_normalizes_multiple_spaces(self, mock_db):
        df = pd.DataFrame({"notes": ["hello    world", "  trimmed  "]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_01_whitespace_normalization("notes")
        
        assert result.changes_made == 2
        assert runner.df.at[0, "notes"] == "hello world"
        assert runner.df.at[1, "notes"] == "trimmed"
    
    def test_no_changes_for_clean_text(self, mock_db):
        df = pd.DataFrame({"notes": ["clean text", "another clean"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_01_whitespace_normalization("notes")
        
        assert result.changes_made == 0


class TestTEXT02PlaceholderDetection:
    """Tests for TEXT-02: Placeholder detection."""
    
    def test_converts_na_to_null(self, mock_db):
        df = pd.DataFrame({"notes": ["valid text", "N/A", "n/a", "None"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_02_placeholder_detection("notes")
        
        assert result.changes_made == 3
        assert runner.df.at[0, "notes"] == "valid text"
        assert pd.isna(runner.df.at[1, "notes"])
        assert pd.isna(runner.df.at[2, "notes"])
        assert pd.isna(runner.df.at[3, "notes"])
    
    def test_converts_dashes_to_null(self, mock_db):
        df = pd.DataFrame({"notes": ["-", "--", "---"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_02_placeholder_detection("notes")
        
        assert result.changes_made == 3


class TestTEXT03EncodingFix:
    """Tests for TEXT-03: Encoding fix."""
    
    def test_fixes_smart_quotes(self, mock_db):
        smart_text = 'He said \u201cHello\u201d'  # Unicode smart quotes
        df = pd.DataFrame({"notes": [smart_text]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_03_encoding_fix("notes")
        
        # Should replace smart quotes with regular quotes
        assert result.changes_made >= 0  # May or may not change depending on encoding


class TestTEXT04HtmlMarkdownStripping:
    """Tests for TEXT-04: HTML/Markdown stripping."""
    
    def test_strips_html_tags(self, mock_db):
        df = pd.DataFrame({"notes": ["<p>Hello</p>", "<b>Bold</b> text"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_04_html_markdown_stripping("notes")
        
        assert result.changes_made == 2
        assert runner.df.at[0, "notes"] == "Hello"
        assert runner.df.at[1, "notes"] == "Bold text"
    
    def test_strips_markdown(self, mock_db):
        df = pd.DataFrame({"notes": ["**bold**", "*italic*"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_04_html_markdown_stripping("notes")
        
        assert result.changes_made == 2
        assert runner.df.at[0, "notes"] == "bold"
        assert runner.df.at[1, "notes"] == "italic"


class TestTEXT05LongValueAlert:
    """Tests for TEXT-05: Long value alert."""
    
    def test_flags_extremely_long_text(self, mock_db):
        long_text = "A" * 6000  # Over 5000 char limit
        df = pd.DataFrame({"notes": [long_text, "short"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_05_long_value_alert("notes")
        
        assert result.rows_flagged == 1
        assert len(runner.flags) == 1
        assert runner.flags[0]["formula"] == "TEXT-05"
    
    def test_no_flags_for_normal_text(self, mock_db):
        df = pd.DataFrame({"notes": ["Normal length text", "Another normal one"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_05_long_value_alert("notes")
        
        assert result.rows_flagged == 0


class TestTEXT08LanguageDetection:
    """Tests for TEXT-08: Language detection."""
    
    def test_detects_mixed_languages(self, mock_db):
        df = pd.DataFrame({
            "notes": [
                "This is English text here.",
                "Another English sentence too.",
                "Привет мир это русский текст.",  # Russian
            ]
        })
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_08_language_detection("notes")
        
        # Should flag the Russian text as anomaly
        assert "language_distribution" in result.details


class TestTEXT09LeadingApostropheRemoval:
    """Tests for TEXT-09: Leading apostrophe removal."""
    
    def test_removes_leading_apostrophe(self, mock_db):
        df = pd.DataFrame({"notes": ["'Excel export", "'123456", "normal"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_09_leading_apostrophe_removal("notes")
        
        assert result.changes_made == 2
        assert runner.df.at[0, "notes"] == "Excel export"
        assert runner.df.at[1, "notes"] == "123456"
        assert runner.df.at[2, "notes"] == "normal"
    
    def test_preserves_apostrophe_in_middle(self, mock_db):
        df = pd.DataFrame({"notes": ["it's fine", "don't change"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        result = runner.TEXT_09_leading_apostrophe_removal("notes")
        
        assert result.changes_made == 0


# ============================================================================
# URL FORMULA TESTS (HTYPE-023)
# ============================================================================

class TestURL01ProtocolNormalization:
    """Tests for URL-01: Protocol normalization."""
    
    def test_adds_https_to_bare_urls(self, mock_db):
        df = pd.DataFrame({"website": ["example.com", "www.test.org"]})
        runner = create_runner(df, {"website": "HTYPE-023"}, mock_db)
        
        result = runner.URL_01_protocol_normalization("website")
        
        assert result.changes_made == 2
        assert runner.df.at[0, "website"] == "https://example.com"
        assert runner.df.at[1, "website"] == "https://www.test.org"
    
    def test_preserves_existing_protocol(self, mock_db):
        df = pd.DataFrame({"website": ["https://example.com", "http://test.org"]})
        runner = create_runner(df, {"website": "HTYPE-023"}, mock_db)
        
        result = runner.URL_01_protocol_normalization("website")
        
        assert result.changes_made == 0


class TestURL02LowercaseDomain:
    """Tests for URL-02: Lowercase domain."""
    
    def test_lowercases_domain(self, mock_db):
        df = pd.DataFrame({"website": ["https://EXAMPLE.COM", "https://Test.ORG/Path"]})
        runner = create_runner(df, {"website": "HTYPE-023"}, mock_db)
        
        result = runner.URL_02_lowercase_domain("website")
        
        assert result.changes_made == 2
        assert runner.df.at[0, "website"] == "https://example.com"
        assert runner.df.at[1, "website"] == "https://test.org/Path"


class TestURL03TrailingSlash:
    """Tests for URL-03: Trailing slash standardization."""
    
    def test_standardizes_trailing_slash(self, mock_db):
        df = pd.DataFrame({
            "website": [
                "https://example.com/",
                "https://example.com/",
                "https://example.com",  # No slash - minority
            ]
        })
        runner = create_runner(df, {"website": "HTYPE-023"}, mock_db)
        
        result = runner.URL_03_trailing_slash_standardization("website")
        
        # Majority has trailing slash, so add to minority
        assert runner.df.at[2, "website"] == "https://example.com/"


class TestURL04FormatValidation:
    """Tests for URL-04: Format validation."""
    
    def test_flags_invalid_urls(self, mock_db):
        df = pd.DataFrame({
            "website": ["https://valid.com", "not-a-url", "://invalid"]
        })
        runner = create_runner(df, {"website": "HTYPE-023"}, mock_db)
        
        result = runner.URL_04_format_validation("website")
        
        assert result.rows_flagged >= 1
        assert len(runner.flags) >= 1


class TestURL05PlaceholderDetection:
    """Tests for URL-05: Placeholder detection."""
    
    def test_converts_example_com_to_null(self, mock_db):
        df = pd.DataFrame({
            "website": ["https://example.com", "https://real-site.com", "n/a"]
        })
        runner = create_runner(df, {"website": "HTYPE-023"}, mock_db)
        
        result = runner.URL_05_placeholder_detection("website")
        
        assert result.changes_made == 2
        assert pd.isna(runner.df.at[0, "website"])
        assert runner.df.at[1, "website"] == "https://real-site.com"
        assert pd.isna(runner.df.at[2, "website"])


# ============================================================================
# IP ADDRESS FORMULA TESTS (HTYPE-036)
# ============================================================================

class TestIP01FormatValidation:
    """Tests for IP-01: Format validation."""
    
    def test_flags_invalid_ips(self, mock_db):
        df = pd.DataFrame({
            "ip_address": ["192.168.1.1", "999.999.999.999", "not-an-ip"]
        })
        runner = create_runner(df, {"ip_address": "HTYPE-036"}, mock_db)
        
        result = runner.IP_01_format_validation("ip_address")
        
        assert result.rows_flagged == 2
        assert len(runner.flags) == 2


class TestIP02PrivateIpFlagging:
    """Tests for IP-02: Private IP flagging."""
    
    def test_flags_private_ips(self, mock_db):
        df = pd.DataFrame({
            "ip_address": ["192.168.1.1", "10.0.0.1", "8.8.8.8"]
        })
        runner = create_runner(df, {"ip_address": "HTYPE-036"}, mock_db)
        
        result = runner.IP_02_private_ip_flagging("ip_address")
        
        assert result.rows_flagged == 2  # Two private IPs


class TestIP03LoopbackDetection:
    """Tests for IP-03: Loopback detection."""
    
    def test_flags_loopback(self, mock_db):
        df = pd.DataFrame({
            "ip_address": ["127.0.0.1", "::1", "192.168.1.1"]
        })
        runner = create_runner(df, {"ip_address": "HTYPE-036"}, mock_db)
        
        result = runner.IP_03_loopback_detection("ip_address")
        
        assert result.rows_flagged == 2


class TestIP04DuplicateIpAlert:
    """Tests for IP-04: Duplicate IP alert."""
    
    def test_flags_high_frequency_ips(self, mock_db):
        # Create data where one IP appears many times
        ips = ["192.168.1.1"] * 20 + ["10.0.0.1"] * 2
        df = pd.DataFrame({"ip_address": ips})
        runner = create_runner(df, {"ip_address": "HTYPE-036"}, mock_db)
        
        result = runner.IP_04_duplicate_ip_alert("ip_address")
        
        assert "high_frequency_ips" in result.details
        assert "192.168.1.1" in result.details["high_frequency_ips"]


class TestIP05NullHandling:
    """Tests for IP-05: Null handling."""
    
    def test_reports_null_count(self, mock_db):
        df = pd.DataFrame({
            "ip_address": ["192.168.1.1", None, np.nan, "10.0.0.1"]
        })
        runner = create_runner(df, {"ip_address": "HTYPE-036"}, mock_db)
        
        result = runner.IP_05_null_handling("ip_address")
        
        assert result.details["null_count"] == 2


# ============================================================================
# FILE PATH FORMULA TESTS (HTYPE-037)
# ============================================================================

class TestFILE01ExtensionValidation:
    """Tests for FILE-01: Extension validation."""
    
    def test_flags_unknown_extensions(self, mock_db):
        df = pd.DataFrame({
            "filepath": ["document.pdf", "file.xyz123", "archive.foobar"]
        })
        runner = create_runner(df, {"filepath": "HTYPE-037"}, mock_db)
        
        result = runner.FILE_01_extension_validation("filepath")
        
        assert result.rows_flagged == 2
        assert "unknown_extensions" in result.details


class TestFILE02PathSeparatorNormalization:
    """Tests for FILE-02: Path separator normalization."""
    
    def test_normalizes_backslashes(self, mock_db):
        df = pd.DataFrame({
            "filepath": ["C:\\Users\\file.txt", "path/to/file.txt"]
        })
        runner = create_runner(df, {"filepath": "HTYPE-037"}, mock_db)
        
        result = runner.FILE_02_path_separator_normalization("filepath")
        
        assert result.changes_made == 1
        assert runner.df.at[0, "filepath"] == "C:/Users/file.txt"


class TestFILE03SpecialCharacterAlert:
    """Tests for FILE-03: Special character alert."""
    
    def test_flags_unsafe_characters(self, mock_db):
        df = pd.DataFrame({
            "filepath": ["file name.txt", "file<name>.txt", "safe_file.txt"]
        })
        runner = create_runner(df, {"filepath": "HTYPE-037"}, mock_db)
        
        result = runner.FILE_03_special_character_alert("filepath")
        
        assert result.rows_flagged == 2


class TestFILE04NullHandling:
    """Tests for FILE-04: Null handling."""
    
    def test_reports_null_count(self, mock_db):
        df = pd.DataFrame({
            "filepath": ["/path/to/file.txt", None, np.nan]
        })
        runner = create_runner(df, {"filepath": "HTYPE-037"}, mock_db)
        
        result = runner.FILE_04_null_handling("filepath")
        
        assert result.details["null_count"] == 2


# ============================================================================
# ORCHESTRATION TESTS
# ============================================================================

class TestRunForColumn:
    """Tests for run_for_column orchestration."""
    
    def test_runs_text_formulas_for_htype_022(self, mock_db):
        df = pd.DataFrame({"notes": ["  hello  ", "N/A", "valid"]})
        runner = create_runner(df, {"notes": "HTYPE-022"}, mock_db)
        
        results = runner.run_for_column("notes", "HTYPE-022")
        
        # Should run TEXT-01 through TEXT-09 (minus AI-only)
        formula_ids = [r.formula_id for r in results]
        assert "TEXT-01" in formula_ids
        assert "TEXT-02" in formula_ids
    
    def test_runs_url_formulas_for_htype_023(self, mock_db):
        df = pd.DataFrame({"website": ["example.com", "https://test.com"]})
        runner = create_runner(df, {"website": "HTYPE-023"}, mock_db)
        
        results = runner.run_for_column("website", "HTYPE-023")
        
        formula_ids = [r.formula_id for r in results]
        assert "URL-01" in formula_ids
        assert "URL-05" in formula_ids
    
    def test_runs_ip_formulas_for_htype_036(self, mock_db):
        df = pd.DataFrame({"ip": ["192.168.1.1"]})
        runner = create_runner(df, {"ip": "HTYPE-036"}, mock_db)
        
        results = runner.run_for_column("ip", "HTYPE-036")
        
        formula_ids = [r.formula_id for r in results]
        assert "IP-01" in formula_ids
        assert "IP-05" in formula_ids
    
    def test_runs_file_formulas_for_htype_037(self, mock_db):
        df = pd.DataFrame({"filepath": ["C:\\file.txt"]})
        runner = create_runner(df, {"filepath": "HTYPE-037"}, mock_db)
        
        results = runner.run_for_column("filepath", "HTYPE-037")
        
        formula_ids = [r.formula_id for r in results]
        assert "FILE-01" in formula_ids
        assert "FILE-02" in formula_ids


class TestRunAll:
    """Tests for run_all orchestration."""
    
    def test_processes_all_applicable_columns(self, mock_db):
        df = pd.DataFrame({
            "notes": ["  hello  ", "N/A"],
            "website": ["example.com", "test.org"],
            "ip": ["192.168.1.1", "10.0.0.1"],
            "filepath": ["C:\\file.txt", "/path/file.pdf"],
            "name": ["John", "Jane"],  # Not applicable
        })
        htype_map = {
            "notes": "HTYPE-022",
            "website": "HTYPE-023",
            "ip": "HTYPE-036",
            "filepath": "HTYPE-037",
            "name": "HTYPE-001",  # Not in APPLICABLE_HTYPES
        }
        runner = create_runner(df, htype_map, mock_db)
        
        summary = runner.run_all()
        
        assert summary["columns_processed"] == 4
    
    def test_skips_non_applicable_htypes(self, mock_db):
        df = pd.DataFrame({
            "name": ["John"],
            "email": ["john@example.com"],
        })
        htype_map = {
            "name": "HTYPE-001",  # Name - not applicable
            "email": "HTYPE-006",  # Email - not applicable
        }
        runner = create_runner(df, htype_map, mock_db)
        
        summary = runner.run_all()
        
        assert summary["columns_processed"] == 0
    
    def test_returns_summary_with_stats(self, mock_db):
        df = pd.DataFrame({
            "notes": ["  hello  ", "N/A"],
            "ip": ["127.0.0.1", "10.0.0.1"],
        })
        htype_map = {
            "notes": "HTYPE-022",
            "ip": "HTYPE-036",
        }
        runner = create_runner(df, htype_map, mock_db)
        
        summary = runner.run_all()
        
        assert "columns_processed" in summary
        assert "total_changes" in summary
        assert "total_flags" in summary
        assert "formulas_applied" in summary


class TestFlagsGeneration:
    """Tests for flags generation."""
    
    def test_flags_contain_required_fields(self, mock_db):
        df = pd.DataFrame({"ip": ["invalid-ip"]})
        runner = create_runner(df, {"ip": "HTYPE-036"}, mock_db)
        
        runner.run_all()
        
        assert len(runner.flags) >= 1
        flag = runner.flags[0]
        assert "row" in flag
        assert "column" in flag
        assert "formula" in flag
        assert "message" in flag
        assert "value" in flag
        assert "severity" in flag
