# CLI Documentation Generator

A comprehensive documentation generator for Click-based CLI applications. Automatically generates professional reference documentation in both Markdown and DOCX formats with customizable styling, title pages, and structured command references.

## Overview

This tool analyzes Click-based command-line interfaces and generates complete reference documentation including:

- **Title Page**: Customizable cover page with document code, version, and date
- **Table of Contents**: Auto-generated with hyperlinks to all commands
- **Command Tree Structure**: Visual ASCII tree showing command hierarchy
- **Detailed Command Reference**: Complete documentation for each command including:
  - Command descriptions and usage patterns
  - Arguments and options with types and defaults
  - Grouped commands with proper organization

## Prerequisites

### Required Software

1. **Python 3.10+**
   - Ensure Python is installed and added to your system PATH

2. **Pandoc** (Universal Document Converter)
   - Download from: [https://pandoc.org/installing.html](https://pandoc.org/installing.html)
   - Follow the installation instructions for your operating system
   - Verify installation: `pandoc --version`

3. **Python Dependencies**
   - Install required packages using the requirements file:
     ```bash
     pip install -r requirements.txt
     ```

### Dependencies Include

- `click` - CLI framework (required by the target CLI)
- `pypandoc` - Python interface for Pandoc
- `python-docx` - DOCX file manipulation
- Additional dependencies as needed by your CLI application

## Installation

1. **Clone or download the documentation generator files:**
   ```bash
   cd /path/to/docs_generator
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Pandoc installation:**
   ```bash
   pandoc --version
   ```

## Usage

### Basic Command Structure

```bash
python generate_cli_docx.py [OPTIONS]
```

You must provide either `--module` or `--file` option to specify the CLI source.

### Common Usage Examples

#### 1. Generate Documentation from File (Recommended)

```bash
python generate_cli_docx.py \
  -f "C:\path\to\cli\module.py" \
  -e cli_entry_point \
  -o output_docs.docx \
  --generate-md
```

#### 2. Generate with Custom Title Page

```bash
python generate_cli_docx.py \
  -f "C:\path\to\cli\module.py" \
  -e cli_entry_point \
  -o output_docs.docx \
  -t "My CLI Reference Guide" \
  --doc-code "CLI-REF-01" \
  --version "Version 2.0" \
  --date "January 2025"
```

#### 3. Generate from Python Module

```bash
python generate_cli_docx.py \
  -m my_package.cli.main \
  -e cli \
  -o output_docs.docx
```

#### 4. Generate Without Title Page

```bash
python generate_cli_docx.py \
  -f "C:\path\to\cli\module.py" \
  -e cli_entry_point \
  -o output_docs.docx \
  --no-title-page
```

#### 5. Generate Only Markdown

```bash
python generate_cli_docx.py \
  -f "C:\path\to\cli\module.py" \
  -e cli_entry_point \
  -o output_docs.md \
  --generate-md
```

### Real-World Example

For a CLI defined in `srecli/group/sre.py` with entry point `sre`:

```bash
python generate_cli_docx.py \
  -f "C:\Maestro3\test_ecc_cli\syndicate-rule-engine\cli\srecli\group\sre.py" \
  -e sre \
  -o sre_docs.docx \
  -t "SRE CLI Reference Guide" \
  --doc-code "SRE-REF-2025-01" \
  --version "Version 3.0" \
  --generate-md
```


## Command-Line Options

| Option | Short | Required | Description |
|--------|-------|----------|-------------|
| `--module` | `-m` | * | Python module path (e.g., `srecli.group.sre`) |
| `--file` | `-f` | * | Path to Python file containing CLI definition |
| `--entry-point` | `-e` | No | Name of Click group/command variable (default: `cli`) |
| `--output` | `-o` | No | Output file path (default: `{name}_reference.docx`) |
| `--title` | `-t` | No | Documentation title (default: `CLI Reference Guide`) |
| `--generate-md` | | No | Also generate markdown file alongside DOCX |
| `--no-title-page` | | No | Disable automatic title page generation |
| `--doc-code` | `-dc` | No | Document code for title page (e.g., `SRE-DOC-01`) |
| `--version` | `-v` | No | Version string for title page (default: `Version 1.0`) |
| `--date` | | No | Date for title page (default: current month/year) |

**Note:** You must provide either `--module` or `--file` option, but not both.

## Output Structure

### Generated DOCX Document

The generated DOCX file contains the following sections:

1. **Title Page** (Optional)
   - CLI name (centered, large font)
   - Document code
   - Date
   - Version number

2. **Table of Contents**
   - Hierarchical list of all commands
   - Clickable links to each command section

3. **Command Tree Structure** (New Page)
   - Visual ASCII tree representation
   - Shows groups and commands hierarchy
   - Type indicators: `[GROUP]` or `[COMMAND]`

4. **Detailed Command Reference** (New Page)
   - Each command documented with:
     - Full command path
     - Type (Group or Command)
     - Description
     - Usage syntax
     - Arguments table (name, type, required, description)
     - Options table (name, type, required, default, description)

### Example Output Structure

```
My CLI Tool
├── [GROUP] config
│   ├── [COMMAND] show
│   └── [COMMAND] set
├── [GROUP] deploy
│   ├── [COMMAND] start
│   └── [COMMAND] stop
└── [COMMAND] version
```

## File Locations

After generation, you will find:

- **DOCX File**: Specified by `-o` option or default `{name}_reference.docx`
- **Markdown File**: Same location as DOCX with `.md` extension (if `--generate-md` is used)
- **Generated files are saved in**: Current directory or specified path

Example:
```
C:\Maestro3\docs\
├── sre_reference.docx
└── sre_reference.md (if --generate-md was used)
```

## Advanced Features

### Custom Styling

The DOCX generator applies professional styling automatically:

- **Headings**: Color-coded hierarchy (blue shades)
- **Tables**: Bordered cells with gray headers
- **Code Blocks**: Monospace font with light gray background
- **Margins**: 0.4 inches on all sides
- **Page Breaks**: Automatic breaks before major sections

### Markdown Markers

The following special markers are supported in the generation process:

- `{{ pagebreak }}` - Insert page break in DOCX

[//]: # (- `{{ newline }}` - Insert single line break)
[//]: # (- `{{ newline:N }}` - Insert N line breaks)
[//]: # (- `{{ br }}` - Alias for newline)

### Command Sorting

Commands are automatically sorted:
1. Commands first, then groups
2. Alphabetically within each category

This ensures consistent and easy-to-navigate documentation.

## Troubleshooting

### Common Issues

**1. "No module named 'click'"**
```bash
# Solution: Install the CLI application's dependencies
pip install click
# Or install the entire CLI package
pip install -e /path/to/cli/package
```

**2. "Pandoc not found"**
```bash
# Solution: Install Pandoc and add to PATH
# Verify: pandoc --version
# If still not found, restart terminal/command prompt
```

**3. "Module 'X' has no attribute 'cli'"**
```bash
# Solution: Specify correct entry point name
python generate_cli_docx.py -f file.py -e correct_entry_point_name
```

**4. Import errors when loading CLI module**
```bash
# Solution: Ensure CLI module's dependencies are installed
# Add CLI module path to PYTHONPATH if needed
export PYTHONPATH=/path/to/cli/root:$PYTHONPATH  # Linux/Mac
set PYTHONPATH=C:\path\to\cli\root;%PYTHONPATH%  # Windows
```

### Tips for Best Results

1. **Use File Path Method**: More reliable than module imports
   ```bash
   python generate_cli_docx.py -f /path/to/file.py -e entry_point
   ```

2. **Always Specify Entry Point**: Explicitly set `-e` to avoid confusion
   ```bash
   -e sre  # if your CLI entry point is named 'sre'
   ```

3. **Test with Markdown First**: Use `--generate-md` to preview structure
   ```bash
   python generate_cli_docx.py -f file.py -e cli --generate-md
   # Review the .md file before generating DOCX
   ```

4. **Keep CLI Code Clean**: Ensure all Click decorators are properly applied
   - Use `help` parameter in all commands
   - Document all options and arguments
   - Provide short_help for commands

## Converting to PDF

To convert the generated DOCX to PDF:

### Option 1: Using Microsoft Word
1. Open the `.docx` file in Microsoft Word
2. File → Save As → PDF
3. Adjust any formatting if needed

### Option 2: Using LibreOffice
```bash
libreoffice --headless --convert-to pdf output_docs.docx
```

### Option 3: Using Pandoc
```bash
pandoc output_docs.docx -o output_docs.pdf --pdf-engine=xelatex
```

## Project Structure

```
docs_generator/
    ├── examples/                         # Example files
    ├── src/                              # Source code
    │   ├── converters/
    │   │   ├── __init__.py
    │   │   └── md_to_docx_converter.py   # Markdown to DOCX converter
    │   ├── generators/
    │   │   ├── __init__.py
    │   │   ├── cli_doc_generator.py      # Core documentation generator
    │   │   └── title_page.py             # Title page generator
    │   ├── styles/
    │   │   ├── __init__.py
    │   │   ├── docx_styles.py            # DOCX styling functions
    │   │   └── style_config.py           # Style configuration constants
    │   ├── __init__.py
    │   └── generate_cli_docx.py          # Main CLI entry point
    ├── CHANGELOG.md                      # Changelog file
    ├── README.md                         # This file
    └── requirements.txt             # Python dependencies
```

## Getting Help

### View All Options
```bash
python generate_cli_docx.py --help
```

### Command Help Output
```
Usage: generate_cli_docx.py [OPTIONS]

  Generate DOCX documentation for Click-based CLI tools

Options:
  -m, --module TEXT        Python module path
  -f, --file PATH          Path to Python file
  -e, --entry-point TEXT   Click entry point variable name
  -o, --output PATH        Output DOCX file path
  -t, --title TEXT         Documentation title
  --generate-md            Also generate markdown file
  --no-title-page          Disable title page
  -dc, --doc-code TEXT     Document code for title page
  -v, --version TEXT       Version string
  --date TEXT              Date for title page
  --help                   Show this message and exit
```

## Support

For issues, questions, or contributions:
- Check the troubleshooting section above
- Review the example files
- Ensure all prerequisites are properly installed

## License

This documentation generator is provided as-is for generating CLI documentation from Click-based applications.

---

**Last Updated**: October 2025  
**Version**: 1.0