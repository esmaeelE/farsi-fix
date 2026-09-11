#!/usr/bin/env python3
"""
LibreOffice Writer Bidi Fixer
=============================

Fix mixed Persian/Arabic + English text in LibreOffice Writer.

Macros:
    fix_selected_text       Fix currently selected text.
    fix_entire_document     Fix the entire document.

Recommended shortcuts:
    Ctrl + Alt + B          Fix selected text.
    Ctrl + Alt + Shift + B  Fix entire document.
"""

import re

from com.sun.star.document import XDocument
from com.sun.star.frame import XController
from com.sun.star.script import XScriptContext
from com.sun.star.text import XText, XTextRange


# ============================================================================
# Unicode Bidirectional Characters
# ============================================================================

LRI = "\u2066"
PDI = "\u2069"

_PLACEHOLDER_START = "\ue000"
_PLACEHOLDER_END = "\ue001"


def _make_placeholder(index: int) -> str:
    return _PLACEHOLDER_START + str(index) + _PLACEHOLDER_END


# ============================================================================
# Regular Expressions
# ============================================================================

BIDI_CONTROLS = re.compile(
    r"[\u061C\u200E\u200F\u202A-\u202E\u2066-\u2069]"
)

# URLs — lookbehind strips trailing sentence punctuation (.,;:!?).
URL_PATTERN = re.compile(
    r"""https?://[^\s<>()]+(?<=[A-Za-z0-9/\-])""",
    re.VERBOSE | re.IGNORECASE,
)

MARKDOWN_CODE_PATTERN = re.compile(r"`[^`\n]+`")

EMAIL_PATTERN = re.compile(
    r"""[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}""",
    re.VERBOSE,
)

PARENTHESIS_PATTERN = re.compile(
    r"""\([^()\n]*[A-Za-z][^()\n]*\)""",
    re.VERBOSE,
)

LTR_PATTERN = re.compile(
    r"""
    (?:
        \.[A-Za-z]
        |
        [A-Za-z]
    )
    [A-Za-z0-9_.:+/#@%$&=~\-]*
    """,
    re.VERBOSE,
)


# ============================================================================
# Bidi Processing
# ============================================================================


def remove_bidi_controls(text: str) -> str:
    return BIDI_CONTROLS.sub("", text)


def protect_regions(text: str) -> tuple[str, list[tuple[str, str]]]:
    protected: list[tuple[str, str]] = []

    def _replace(match: re.Match[str]) -> str:
        original = match.group(0)
        placeholder = _make_placeholder(len(protected))
        protected.append((placeholder, original))
        return placeholder

    for pattern in (URL_PATTERN, MARKDOWN_CODE_PATTERN, EMAIL_PATTERN, PARENTHESIS_PATTERN):
        text = pattern.sub(_replace, text)

    return text, protected


def restore_regions(text: str, protected: list[tuple[str, str]]) -> str:
    for placeholder, original in protected:
        if PARENTHESIS_PATTERN.fullmatch(original):
            replacement = LRI + original + PDI
        else:
            replacement = original
        text = text.replace(placeholder, replacement)
    return text


def isolate_ltr(text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        return LRI + match.group(0) + PDI

    return LTR_PATTERN.sub(_replace, text)


def fix_bidi(text: str) -> str:
    text = remove_bidi_controls(text)
    text, protected = protect_regions(text)
    text = isolate_ltr(text)
    text = restore_regions(text, protected)
    return text


# ============================================================================
# LibreOffice Helpers
# ============================================================================


def get_document() -> XDocument:
    return XSCRIPTCONTEXT.getDocument()


def get_selection() -> XTextRange | None:
    document: XDocument = get_document()
    controller: XController = document.getCurrentController()
    return controller.getSelection()


# ============================================================================
# Macro: Fix Selected Text
# ============================================================================


def fix_selected_text(*args) -> None:
    selection = get_selection()
    if selection is None:
        return

    count = selection.getCount()
    if count == 0:
        return

    for index in range(count - 1, -1, -1):
        text_range = selection.getByIndex(index)
        original = text_range.getString()
        if not original:
            continue
        fixed = fix_bidi(original)
        if fixed == original:
            continue
        text_range.setString(fixed)


# ============================================================================
# Macro: Fix Entire Document
# ============================================================================


def fix_entire_document(*args) -> None:
    document: XDocument = get_document()
    if document is None:
        return

    text: XText = document.getText()
    original = text.getString()
    if not original:
        return

    fixed = fix_bidi(original)
    if fixed == original:
        return

    text.setString(fixed)


# ============================================================================
# LibreOffice Macro Registration
# ============================================================================

g_exportedScripts = (
    fix_selected_text,
    fix_entire_document,
)
