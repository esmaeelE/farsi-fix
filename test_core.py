#!/usr/bin/env python3
"""Tests for core bidi processing."""

from importlib.machinery import SourceFileLoader
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

# farsi-fix has no .py extension — provide loader explicitly
_spec = spec_from_file_location(
    "farsi_fix",
    str(Path(__file__).parent / "farsi-fix"),
    loader=SourceFileLoader("farsi_fix", str(Path(__file__).parent / "farsi-fix")),
)
_mod = module_from_spec(_spec)
_spec.loader.exec_module(_mod)

fix_bidi = _mod.fix_bidi
LRI = _mod.LRI
PDI = _mod.PDI
remove_bidi_controls = _mod.remove_bidi_controls
protect_regions = _mod.protect_regions
restore_regions = _mod.restore_regions
isolate_ltr = _mod.isolate_ltr


def test_pure_english():
    """English text gets LRI/PDI wrapped (each word separately)."""
    result = fix_bidi("Hello World")
    assert LRI in result
    assert PDI in result
    assert f"{LRI}Hello{PDI}" in result
    assert f"{LRI}World{PDI}" in result


def test_pure_persian():
    """Pure Persian text is unchanged."""
    text = "سلام دنیا"
    assert fix_bidi(text) == text


def test_mixed_text():
    """Mixed Persian + English token."""
    result = fix_bidi("این یک API است")
    assert "API" in result
    assert result.startswith("این یک ")
    assert result.endswith(" است")


def test_idempotent():
    """Running twice produces same result."""
    text = "این یک API (v1) است"
    first = fix_bidi(text)
    second = fix_bidi(first)
    assert first == second


def test_url_protected():
    """URLs are not modified."""
    url = "https://example.com/api/v1"
    result = fix_bidi(f"بازدید از {url}")
    # URL should appear verbatim (no LRI/PDI inside)
    assert url in result
    assert LRI + url + PDI not in result


def test_markdown_code_protected():
    """Inline code is not modified."""
    code = "`UserService`"
    result = fix_bidi(f"کلاس {code} را ببینید")
    assert code in result
    assert LRI + code + PDI not in result


def test_email_protected():
    """Email addresses are not modified."""
    email = "user@example.com"
    result = fix_bidi(f"ایمیل {email} را بفرستید")
    assert email in result


def test_parenthesis_isolated():
    """Parenthesized English becomes one LTR block."""
    result = fix_bidi("ورژن (v1) است")
    # The entire (v1) should be wrapped as one LTR block
    assert f"{LRI}(v1){PDI}" in result


def test_remove_bidi_controls():
    """Existing bidi controls are stripped."""
    dirty = f"{LRI}Hello{PDI} World"
    clean = remove_bidi_controls(dirty)
    assert LRI not in clean
    assert PDI not in clean
    assert "Hello World" == clean


def test_dotslash_token():
    """.NET, .env etc. are recognized as LTR."""
    result = fix_bidi("فایل .env را بررسی کن")
    assert f"{LRI}.env{PDI}" in result


def test_numbers_not_wrapped():
    """Pure numbers (no Latin chars) are not wrapped."""
    result = fix_bidi("قیمت ۱۲۳ تومان")
    assert LRI not in result
    assert PDI not in result


def test_empty_string():
    """Empty input produces empty output."""
    assert fix_bidi("") == ""


def test_protect_restore_roundtrip():
    """protect + restore preserves original text."""
    text = "بازدید https://example.com و `code` و user@test.com"
    protected_text, protected = protect_regions(text)
    restored = restore_regions(protected_text, protected)
    assert restored == text


def test_ltr_pattern_standalone():
    """isolate_ltr wraps known tokens."""
    result = isolate_ltr("API version")
    assert f"{LRI}API{PDI}" in result
    assert f"{LRI}version{PDI}" in result


def test_slash_token():
    """API/v1 style tokens recognized."""
    result = fix_bidi("نسخه API/v1 فعال است")
    assert f"{LRI}API/v1{PDI}" in result


def test_cpp_token():
    """C++ and C# recognized."""
    result = fix_bidi("زبان C++ را دوست دارم")
    assert f"{LRI}C++{PDI}" in result


def test_url_trailing_period():
    """Trailing period from sentence is not captured in URL."""
    result = fix_bidi("بازدید https://example.com. سلام")
    assert f"{LRI}https://example.com{PDI}" not in result  # URL is protected, not isolated
    assert "https://example.com." in result  # original text preserved
    assert "https://example.com" in result


def test_url_trailing_comma():
    """Trailing comma from sentence is not captured in URL."""
    result = fix_bidi("ببینید https://example.com, و ادامه")
    assert "https://example.com," in result


def test_url_no_trailing_punctuation():
    """URL without trailing punctuation works normally."""
    result = fix_bidi("بازدید https://example.com/path")
    assert "https://example.com/path" in result


def test_check_multiple_reports_all():
    """--check reports all files needing changes."""
    import tempfile
    from pathlib import Path as P

    with tempfile.TemporaryDirectory() as d:
        a = P(d) / "a.md"
        b = P(d) / "b.md"
        c = P(d) / "c.md"
        a.write_text("این API است", encoding="utf-8")
        b.write_text("سلام", encoding="utf-8")  # no English, no change needed
        c.write_text("فایل .env را ببینید", encoding="utf-8")
        # We can't easily test the CLI exit code here, but we can test fix_bidi
        assert fix_bidi(a.read_text(encoding="utf-8")) != a.read_text(encoding="utf-8")
        assert fix_bidi(b.read_text(encoding="utf-8")) == b.read_text(encoding="utf-8")
        assert fix_bidi(c.read_text(encoding="utf-8")) != c.read_text(encoding="utf-8")


if __name__ == "__main__":
    import sys
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"FAIL: {test.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    sys.exit(1 if failed else 0)
