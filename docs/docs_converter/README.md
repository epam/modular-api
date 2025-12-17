# Markdown to DOCX Converter

Convert Markdown files to professionally styled Word documents using Pandoc.

## Features

- **Custom Styling** - Professional fonts, colors, and formatting
- **Page Breaks** - Use `{{ pagebreak }}` markers in Markdown
- **Style Presets** - Default, Corporate, and Minimal themes
- **Tables & Code** - Styled tables and syntax-highlighted code blocks
- **Simple CLI** - One command to convert

## Prerequisites

- **Python 3.10+**
- **Pandoc** - [Install from pandoc.org](https://pandoc.org/installing.html)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify Pandoc
pandoc --version
```

## Quick Start

**Basic conversion:**
```bash
python convert_md_to_docx.py input.md -o output.docx
```

**Without custom styles:**
```bash
python convert_md_to_docx.py input.md -o output.docx --no-styles
```

**With debug output:**
```bash
python convert_md_to_docx.py input.md -o output.docx --verbose
```

## Usage

```bash
python convert_md_to_docx.py <input.md> -o <output.docx> [OPTIONS]
```

### Options

| Option | Description |
|--------|-------------|
| `-o, --output` | Output DOCX file path (required) |
| `--no-styles` | Skip applying custom styles |
| `--verbose` | Enable debug logging |
| `--help` | Show help message |

### Merging Multiple Files

Use system commands to merge files first:

```bash
# Windows
type file1.md file2.md > merged.md

# Linux/Mac
cat file1.md file2.md > merged.md

# Then convert
python convert_md_to_docx.py merged.md -o output.docx
```

## Page Breaks

Insert page breaks anywhere in your Markdown:

```markdown
# Section 1

Content here.

{{ pagebreak }}

# Section 2

This starts on a new page.
```

## Changing Styles

Edit `src/styles/style_config.py`:

```python
# Switch between presets
ACTIVE_PRESET = 'default'  # Options: 'default', 'corporate', 'minimal'
```

### Available Presets

- **default** - Colorful modern style (teal/blue headings, Arial)
- **corporate** - Professional business style (navy/gray, Calibri)
- **minimal** - Classic clean style (black/gray, Times New Roman)

> See [CUSTOMIZATION.md](CUSTOMIZATION.md) for creating custom styles

## Supported Markdown Features

✅ Headings, bold, italic, code  
✅ Lists (ordered and unordered)  
✅ Tables  
✅ Links and images  
✅ Code blocks  
✅ Block quotes  

## Troubleshooting

### "Pandoc not found"
**Solution:** Install Pandoc from [pandoc.org](https://pandoc.org/installing.html) and restart terminal

### "Input file not found"
**Solution:** Use absolute paths or check file exists
```bash
python convert_md_to_docx.py C:\full\path\to\file.md -o output.docx
```

### "No module named 'docx'"
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Styles not applied
**Solution:** Remove `--no-styles` flag or check `style_config.py`

## Converting to PDF

**Microsoft Word**  
Open DOCX → File → Save As → PDF

## Project Structure

```
docs_converter/
├── src/
│   ├── styles/
│   │   ├── docx_styles.py       # Styling engine
│   │   └── style_config.py      # Configuration
│   └── convert_md_to_docx.py    # Main script
├── examples/
│   └── commands.sh              # Usage examples
├── CHANGELOG.md                 # Version history
├── CUSTOMIZATION.md             # Style customization guide
├── README.md                    # This file
└── requirements.txt             # Dependencies
```

**Check first:**
- Verify Pandoc is installed: `pandoc --version`
- Ensure Python 3.10+: `python --version`
- Use `--verbose` flag for detailed errors

**Version**: 1.0.0  
**Last Updated**: November 2025  
