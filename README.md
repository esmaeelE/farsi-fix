# farsi-fix

Fix mixed Persian/English bidirectional text. Single file, zero dependencies.

When Persian and English are mixed in the same line, RTL rendering engines
often scramble the English tokens. **farsi-fix** wraps each LTR token with
Unicode [LRI/PDI](https://www.unicode.org/reports/tr9/#Bidirectional_Isolates)
characters so every app renders it correctly — browsers, terminals, editors,
LibreOffice, you name it.

```
Before:   از ماژول EstateAds استفاده می‌کنیم. نسخه (v1) فعال است.
After:    از ماژول ⁦EstateAds⁩ استفاده می‌کنیم. نسخه ⁦(v1)⁩ فعال است.
                                 ↑ isolated ↑                   ↑ isolated ↑
```

## How it works

1. Strip existing bidi control characters — safe to run repeatedly (idempotent).
2. Protect content that must stay untouched: URLs, Markdown inline code, email addresses, parenthesized English.
3. Wrap every remaining LTR token with `U+2066` (LRI) and `U+2069` (PDI).
4. Restore protected regions.

## Install

No installation. Copy the script you need and run it.

```sh
# Make executable (optional)
chmod +x farsi-fix

# Or run directly
python3 farsi-fix document.md
```

## CLI — `farsi-fix`

### Basic usage

```sh
farsi-fix document.md              # print to stdout
farsi-fix document.md -o fixed.md  # write to file
farsi-fix -i document.md           # modify in place
farsi-fix -i --backup document.md  # in place + .bak backup
farsi-fix -i *.md                  # multiple files
```

### Stdin / pipes

```sh
cat document.md | farsi-fix
cat document.md | farsi-fix -o fixed.md
echo "این یک API است" | farsi-fix
```

### Check mode

```sh
farsi-fix --check document.md
```

Reports all files that need changes (one per line). Exit codes:

| Code | Meaning |
|---|---|
| `0` | All files clean |
| `1` | Some files need changes |
| `2` | Error (file not found, permission denied, etc.) |

Useful in CI:

```sh
farsi-fix --check **/*.md || echo "Run farsi-fix to fix bidi text"
```

### All flags

```
-i, --in-place     Modify files in place (requires file arguments)
-o, --output FILE  Write result to FILE (single input file only)
    --backup       Create FILE.bak before modifying (with -i)
    --check        Report files needing changes, exit 0/1/2
```

## LibreOffice Writer — `farsi-fix-writer.py`

### Install

1. Open LibreOffice Writer.
2. Go to **Tools → Macros → Organize Python Macros**.
3. Select your personal macro library and click **Import**.
4. Import `farsi-fix-writer.py`.

### Assign shortcuts

Go to **Tools → Customize → Keyboard** and assign:

| Shortcut | Macro |
|---|---|
| `Ctrl + Alt + B` | `fix_selected_text` |
| `Ctrl + Alt + Shift + B` | `fix_entire_document` |

### What it does

- **Fix selected text** — processes each text range in the current selection.
- **Fix entire document** — processes the whole document body.

Both skip content that doesn't need changes.

## Supported tokens

Every token that starts with a Latin letter or `.letter`:

| Pattern | Examples |
|---|---|
| English words | `API`, `EstateAds`, `FastAPI` |
| Versions | `v1`, `v1.2.3` |
| Dot-start | `.NET`, `.env`, `.gitignore` |
| Operators | `C++`, `C#`, `Node.js` |
| Paths | `API/v1`, `.vscode/settings.json` |
| Kebab / snake | `foo-bar`, `foo_bar` |
| Parenthesized | `(v1)` → `⁦(v1)⁩` |

## Protected content

These are left untouched — no bidi markers inserted inside them:

- **URLs** — `https://...` (trailing sentence punctuation excluded)
- **Markdown code** — `` `UserService` ``
- **Emails** — `user@example.com`
- **Parenthesized English** — `(v1)` is isolated as one block, not character-by-character

## Requirements

Python 3.10+. No third-party dependencies.

## Testing

```sh
python3 test_core.py
```
