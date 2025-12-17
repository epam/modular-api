# Style Customization Guide

Complete guide to customizing the appearance of your generated DOCX documents.

## Table of Contents

- [Quick Start](#quick-start)
- [Built-in Presets](#built-in-presets)
- [Creating Custom Presets](#creating-custom-presets)
- [Customizable Elements](#customizable-elements)
- [Style Configuration Reference](#style-configuration-reference)
- [Examples](#examples)
- [Testing Your Styles](#testing-your-styles)
- [Tips & Best Practices](#tips--best-practices)

---

## Quick Start

### Switching Between Presets

Edit `src/styles/style_config.py`:

```python
# Line ~135
ACTIVE_PRESET = 'corporate'  # Change this line
```

**Available options:**
- `'default'` - Colorful modern style
- `'corporate'` - Professional business style
- `'minimal'` - Classic clean style
- `'your_custom'` - Any custom preset you create

**Apply changes:** Just save the file and run the converter again. No restart needed.

---

## Built-in Presets

### Default Preset

**Use case:** Modern documentation, technical guides, colorful reports

```python
'default': {
    'name': 'Default Style',
    'colors': {
        'heading1': RGBColor(70, 69, 71),      # Dark Gray
        'heading2': RGBColor(26, 156, 176),    # Teal
        'heading3': RGBColor(44, 196, 201),    # Light Teal
        'heading4': RGBColor(0, 0, 0),         # Black
        'normal': RGBColor(0, 0, 0),           # Black
        'code': RGBColor(0, 0, 0),             # Black
    },
    'fonts': {
        'headings': 'Arial',
        'normal': 'Arial',
        'code': 'Consolas',
    },
    'sizes': {
        'heading1': Pt(20),
        'heading2': Pt(16),
        'heading3': Pt(12),
        'normal': Pt(12),
        'code': Pt(11),
    },
    'margins': {'default': 0.5},  # inches
}
```

**Preview:**
```
Heading 1 - Large Dark Gray, Arial, 20pt
Heading 2 - Teal, Arial, 16pt
Heading 3 - Light Teal, Arial, 12pt
Normal Text - Black, Arial, 12pt
Code - Black, Consolas, 11pt with borders
```

---

### Corporate Preset

**Use case:** Business reports, formal documentation, executive summaries

```python
'corporate': {
    'name': 'Corporate Style',
    'colors': {
        'heading1': RGBColor(0, 51, 102),      # Navy Blue
        'heading2': RGBColor(0, 102, 204),     # Blue
        'heading3': RGBColor(102, 102, 102),   # Gray
        'heading4': RGBColor(0, 0, 0),         # Black
        'normal': RGBColor(0, 0, 0),           # Black
        'code': RGBColor(0, 0, 0),             # Black
    },
    'fonts': {
        'headings': 'Calibri',
        'normal': 'Calibri',
        'code': 'Courier New',
    },
    'sizes': {
        'heading1': Pt(20),
        'heading2': Pt(16),
        'heading3': Pt(12),
        'normal': Pt(12),
        'code': Pt(11),
    },
    'margins': {'default': 1.0},  # Standard 1-inch margins
}
```

**Preview:**
```
Heading 1 - Navy Blue, Calibri, 20pt
Heading 2 - Blue, Calibri, 16pt
Heading 3 - Gray, Calibri, 12pt
Normal Text - Black, Calibri, 12pt
Code - Black, Courier New, 11pt
```

---

### Minimal Preset

**Use case:** Academic papers, classic documents, distraction-free reading

```python
'minimal': {
    'name': 'Minimal Style',
    'colors': {
        'heading1': RGBColor(0, 0, 0),         # Black
        'heading2': RGBColor(50, 50, 50),      # Dark Gray
        'heading3': RGBColor(100, 100, 100),   # Medium Gray
        'heading4': RGBColor(0, 0, 0),         # Black
        'normal': RGBColor(0, 0, 0),           # Black
        'code': RGBColor(0, 0, 0),             # Black
    },
    'fonts': {
        'headings': 'Times New Roman',
        'normal': 'Times New Roman',
        'code': 'Courier New',
    },
    'sizes': {
        'heading1': Pt(18),
        'heading2': Pt(14),
        'heading3': Pt(12),
        'normal': Pt(11),
        'code': Pt(10),
    },
    'margins': {'default': 1.0},
}
```

**Preview:**
```
Heading 1 - Black, Times New Roman, 18pt
Heading 2 - Dark Gray, Times New Roman, 14pt
Heading 3 - Medium Gray, Times New Roman, 12pt
Normal Text - Black, Times New Roman, 11pt
Code - Black, Courier New, 10pt
```

---

## Creating Custom Presets

### Step 1: Add Your Preset

Edit `src/styles/style_config.py` and add your preset to the `PRESETS` dictionary:

```python
PRESETS = {
    'default': { ... },
    'corporate': { ... },
    'minimal': { ... },
    
    # Add your custom preset here
    'my_style': {
        'name': 'My Custom Style',
        'colors': {
            'heading1': RGBColor(255, 0, 0),   # Red
            'heading2': RGBColor(0, 128, 0),   # Green
            'heading3': RGBColor(0, 0, 255),   # Blue
            'heading4': RGBColor(0, 0, 0),
            'heading5': RGBColor(0, 0, 0),
            'heading6': RGBColor(0, 0, 0),
            'normal': RGBColor(0, 0, 0),
            'code': RGBColor(0, 0, 0),
            'table_border': '000000',
            'code_border': '666666',
        },
        'fonts': {
            'default': 'Georgia',
            'headings': 'Georgia',
            'normal': 'Georgia',
            'code': 'Consolas',
        },
        'sizes': {
            'heading1': Pt(24),
            'heading2': Pt(20),
            'heading3': Pt(16),
            'heading4': Pt(14),
            'heading5': Pt(12),
            'heading6': Pt(12),
            'normal': Pt(11),
            'normal_base': Pt(11),
            'code': Pt(10),
        },
        'margins': {'default': 0.75},
    },
}
```

### Step 2: Activate Your Preset

```python
# At the bottom of style_config.py
ACTIVE_PRESET = 'my_style'  # Use your preset name
```

### Step 3: Test

```bash
python convert_md_to_docx.py test.md -o test.docx
```

Open `test.docx` and verify your styles are applied.

---

## Customizable Elements

### Colors

**RGB Color Format:**
```python
RGBColor(Red, Green, Blue)  # Values: 0-255
```

**Available color settings:**

| Setting | Description | Format |
|---------|-------------|--------|
| `heading1` | H1 heading color | `RGBColor(R, G, B)` |
| `heading2` | H2 heading color | `RGBColor(R, G, B)` |
| `heading3` | H3 heading color | `RGBColor(R, G, B)` |
| `heading4` | H4 heading color | `RGBColor(R, G, B)` |
| `heading5` | H5 heading color | `RGBColor(R, G, B)` |
| `heading6` | H6 heading color | `RGBColor(R, G, B)` |
| `normal` | Body text color | `RGBColor(R, G, B)` |
| `code` | Code block text color | `RGBColor(R, G, B)` |
| `table_border` | Table border color | `'RRGGBB'` (hex) |
| `code_border` | Code block border color | `'RRGGBB'` (hex) |

**Common Colors:**
```python
# Basic
RGBColor(0, 0, 0)           # Black
RGBColor(255, 255, 255)     # White
RGBColor(128, 128, 128)     # Gray

# Primary
RGBColor(255, 0, 0)         # Red
RGBColor(0, 255, 0)         # Green
RGBColor(0, 0, 255)         # Blue

# Professional
RGBColor(0, 51, 102)        # Navy Blue
RGBColor(70, 130, 180)      # Steel Blue
RGBColor(34, 139, 34)       # Forest Green
RGBColor(139, 0, 0)         # Dark Red
RGBColor(75, 0, 130)        # Indigo

# Modern
RGBColor(26, 156, 176)      # Teal
RGBColor(230, 126, 34)      # Orange
RGBColor(231, 76, 60)       # Coral
RGBColor(46, 204, 113)      # Emerald
RGBColor(155, 89, 182)      # Amethyst
```

---

### Fonts

**Available font settings:**

| Setting | Description | Example |
|---------|-------------|---------|
| `default` | Default font (fallback) | `'Arial'` |
| `headings` | Font for all headings | `'Calibri'` |
| `normal` | Body text font | `'Times New Roman'` |
| `code` | Code block font | `'Consolas'` |

**Common Font Choices:**

**Sans-serif (modern, clean):**
```
'Arial'
'Calibri'
'Helvetica'
'Verdana'
'Tahoma'
'Segoe UI'
```

**Serif (classic, formal):**
```
'Times New Roman'
'Georgia'
'Garamond'
'Book Antiqua'
'Palatino Linotype'
```

**Monospace (code):**
```
'Consolas'
'Courier New'
'Monaco'
'Lucida Console'
'Menlo'
```

---

### Font Sizes

**Point Size Format:**
```python
Pt(size)  # size in points (pt)
```

**Available size settings:**

| Setting | Description | Recommended Range |
|---------|-------------|-------------------|
| `heading1` | H1 size | 18-24 pt |
| `heading2` | H2 size | 14-20 pt |
| `heading3` | H3 size | 12-16 pt |
| `heading4` | H4 size | 10-14 pt |
| `heading5` | H5 size | 10-12 pt |
| `heading6` | H6 size | 10-12 pt |
| `normal` | Body text size | 10-12 pt |
| `normal_base` | Base style size | 10-12 pt |
| `code` | Code block size | 9-11 pt |

**Size Guidelines:**
```python
# Large document (lots of white space)
'heading1': Pt(24),
'heading2': Pt(20),
'normal': Pt(12),

# Standard document
'heading1': Pt(20),
'heading2': Pt(16),
'normal': Pt(11),

# Compact document (save space)
'heading1': Pt(16),
'heading2': Pt(14),
'normal': Pt(10),
```

---

### Margins

**Margin Format:**
```python
'margins': {'default': 1.0}  # inches
```

**Common Margin Settings:**

| Style | Inches | Description |
|-------|--------|-------------|
| Narrow | `0.5` | Maximize content, modern look |
| Normal | `1.0` | Standard Word default |
| Moderate | `0.75` | Balance between narrow and normal |
| Wide | `1.5` | Classic, lots of white space |
| Custom | `0.3` - `2.0` | Any value you prefer |

**Examples:**
```
# Maximize content
'margins': {'default': 0.5}

# Standard document
'margins': {'default': 1.0}

# Print-ready with binding space
'margins': {'default': 1.25}
```

---

### Spacing

**Spacing for code blocks:**

```python
SPACING = {
    'code_left': Pt(10),      # Left indent
    'code_right': Pt(10),     # Right indent
    'code_before': Pt(5),     # Space above
    'code_after': Pt(5),      # Space below
}
```

**Adjustment Examples:**
```python
# Tight spacing
SPACING = {
    'code_left': Pt(5),
    'code_right': Pt(5),
    'code_before': Pt(3),
    'code_after': Pt(3),
}

# Generous spacing
SPACING = {
    'code_left': Pt(20),
    'code_right': Pt(20),
    'code_before': Pt(10),
    'code_after': Pt(10),
}
```

---

### Borders

**Border settings:**

```python
BORDERS = {
    'table_size': 12,          # Border width (1/8 pt units)
    'code_size': 4,            # Code border width
    'border_style': 'single',  # Border style
}
```

**Border Width Guidelines:**
- `4` - Thin, subtle
- `8` - Standard
- `12` - Medium, visible
- `16` - Thick, prominent

**Border Styles:**
- `'single'` - Solid line (most common)
- `'double'` - Double line
- `'dashed'` - Dashed line
- `'dotted'` - Dotted line

---

## Style Configuration Reference

### Complete Preset Template

Copy this template to create a new preset:

```python
'preset_name': {
    'name': 'Display Name',
    
    # Colors (RGB format)
    'colors': {
        'heading1': RGBColor(0, 0, 0),
        'heading2': RGBColor(0, 0, 0),
        'heading3': RGBColor(0, 0, 0),
        'heading4': RGBColor(0, 0, 0),
        'heading5': RGBColor(0, 0, 0),
        'heading6': RGBColor(0, 0, 0),
        'normal': RGBColor(0, 0, 0),
        'code': RGBColor(0, 0, 0),
        'table_border': '000000',    # Hex
        'code_border': '000000',     # Hex
    },
    
    # Fonts
    'fonts': {
        'default': 'Arial',
        'headings': 'Arial',
        'normal': 'Arial',
        'code': 'Consolas',
    },
    
    # Sizes (Point format)
    'sizes': {
        'heading1': Pt(20),
        'heading2': Pt(16),
        'heading3': Pt(12),
        'heading4': Pt(10),
        'heading5': Pt(10),
        'heading6': Pt(10),
        'normal': Pt(12),
        'normal_base': Pt(10),
        'code': Pt(11),
    },
    
    # Margins (inches)
    'margins': {'default': 1.0},
},
```

---

## Examples

### Example 1: Vibrant Tech Style

```python
'tech_vibrant': {
    'name': 'Vibrant Tech Style',
    'colors': {
        'heading1': RGBColor(230, 126, 34),   # Orange
        'heading2': RGBColor(46, 204, 113),   # Emerald
        'heading3': RGBColor(52, 152, 219),   # Light Blue
        'heading4': RGBColor(155, 89, 182),   # Purple
        'heading5': RGBColor(0, 0, 0),
        'heading6': RGBColor(0, 0, 0),
        'normal': RGBColor(0, 0, 0),
        'code': RGBColor(0, 0, 0),
        'table_border': '95A5A6',
        'code_border': '3498DB',
    },
    'fonts': {
        'default': 'Segoe UI',
        'headings': 'Segoe UI',
        'normal': 'Segoe UI',
        'code': 'Consolas',
    },
    'sizes': {
        'heading1': Pt(22),
        'heading2': Pt(18),
        'heading3': Pt(14),
        'heading4': Pt(12),
        'heading5': Pt(11),
        'heading6': Pt(11),
        'normal': Pt(11),
        'normal_base': Pt(11),
        'code': Pt(10),
    },
    'margins': {'default': 0.6},
},
```

---

### Example 2: Academic Paper Style

```python
'academic': {
    'name': 'Academic Paper Style',
    'colors': {
        'heading1': RGBColor(0, 0, 0),
        'heading2': RGBColor(0, 0, 0),
        'heading3': RGBColor(0, 0, 0),
        'heading4': RGBColor(0, 0, 0),
        'heading5': RGBColor(0, 0, 0),
        'heading6': RGBColor(0, 0, 0),
        'normal': RGBColor(0, 0, 0),
        'code': RGBColor(0, 0, 0),
        'table_border': '000000',
        'code_border': '000000',
    },
    'fonts': {
        'default': 'Times New Roman',
        'headings': 'Times New Roman',
        'normal': 'Times New Roman',
        'code': 'Courier New',
    },
    'sizes': {
        'heading1': Pt(16),
        'heading2': Pt(14),
        'heading3': Pt(12),
        'heading4': Pt(11),
        'heading5': Pt(11),
        'heading6': Pt(11),
        'normal': Pt(12),
        'normal_base': Pt(12),
        'code': Pt(10),
    },
    'margins': {'default': 1.0},
},
```

---

### Example 3: Dark Mode Inspired

```python
'dark_inspired': {
    'name': 'Dark Mode Inspired',
    'colors': {
        'heading1': RGBColor(100, 181, 246),  # Light Blue
        'heading2': RGBColor(129, 199, 132),  # Light Green
        'heading3': RGBColor(255, 183, 77),   # Light Orange
        'heading4': RGBColor(206, 147, 216),  # Light Purple
        'heading5': RGBColor(100, 100, 100),
        'heading6': RGBColor(100, 100, 100),
        'normal': RGBColor(50, 50, 50),
        'code': RGBColor(50, 50, 50),
        'table_border': '90A4AE',
        'code_border': '607D8B',
    },
    'fonts': {
        'default': 'Verdana',
        'headings': 'Verdana',
        'normal': 'Verdana',
        'code': 'Consolas',
    },
    'sizes': {
        'heading1': Pt(20),
        'heading2': Pt(16),
        'heading3': Pt(13),
        'heading4': Pt(11),
        'heading5': Pt(11),
        'heading6': Pt(11),
        'normal': Pt(11),
        'normal_base': Pt(11),
        'code': Pt(10),
    },
    'margins': {'default': 0.7},
},
```

---

### Example 4: Executive Report

```python
'executive': {
    'name': 'Executive Report',
    'colors': {
        'heading1': RGBColor(0, 32, 96),      # Deep Navy
        'heading2': RGBColor(0, 102, 204),    # Corporate Blue
        'heading3': RGBColor(102, 102, 102),  # Gray
        'heading4': RGBColor(0, 0, 0),
        'heading5': RGBColor(0, 0, 0),
        'heading6': RGBColor(0, 0, 0),
        'normal': RGBColor(0, 0, 0),
        'code': RGBColor(0, 0, 0),
        'table_border': '003366',
        'code_border': '666666',
    },
    'fonts': {
        'default': 'Garamond',
        'headings': 'Garamond',
        'normal': 'Garamond',
        'code': 'Courier New',
    },
    'sizes': {
        'heading1': Pt(24),
        'heading2': Pt(18),
        'heading3': Pt(14),
        'heading4': Pt(12),
        'heading5': Pt(12),
        'heading6': Pt(12),
        'normal': Pt(11),
        'normal_base': Pt(11),
        'code': Pt(10),
    },
    'margins': {'default': 1.25},
},
```

---

## Testing Your Styles

### Quick Test Markdown

Create `test.md`:

```markdown
# Heading 1

This is normal text with **bold** and *italic*.

## Heading 2

### Heading 3

#### Heading 4

##### Heading 5

###### Heading 6

Here's a code block:

```python
def hello():
    print("Hello, World!")
```

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Data 1   | Data 2   | Data 3   |
| Data 4   | Data 5   | Data 6   |

{{ pagebreak }}

## Second Page

More content here.
```

### Test Command

```bash
python convert_md_to_docx.py test.md -o test.docx
```

### Checklist

Open `test.docx` and verify:
- ✅ Heading 1-6 colors and sizes
- ✅ Normal text font and size
- ✅ Code block styling and borders
- ✅ Table borders and header formatting
- ✅ Page breaks working
- ✅ Margins look correct

---

## Tips & Best Practices

### Color Selection

✅ **DO:**
- Use consistent color scheme (2-3 main colors)
- Ensure good contrast (dark text on light background)
- Test printed output (some colors don't print well)
- Use professional colors for business docs

❌ **DON'T:**
- Use too many bright colors
- Use low contrast (gray on white)
- Mix warm and cool tones randomly
- Use neon colors in formal documents

### Font Selection

✅ **DO:**
- Use 1-2 font families maximum
- Pair serif with sans-serif (e.g., Georgia headings + Arial body)
- Use monospace for code
- Test readability at intended size

❌ **DON'T:**
- Mix too many fonts
- Use decorative fonts for body text
- Use fonts that aren't widely available
- Sacrifice readability for style

### Size Hierarchy

✅ **DO:**
- Maintain clear hierarchy (H1 > H2 > H3)
- Use consistent spacing between levels
- Keep body text readable (10-12pt)
- Scale proportionally

❌ **DON'T:**
- Make headings too similar in size
- Use tiny fonts (< 9pt for body)
- Make H1 overwhelmingly large (> 28pt)
- Skip heading levels

### Margin Guidelines

| Document Type | Recommended Margin |
|---------------|-------------------|
| Online reading | 0.5" |
| Standard document | 1.0" |
| Printed report | 1.0" - 1.25" |
| Binding required | 1.5" (left) |
| Compact handout | 0.75" |

### Performance Tips

- Styles are applied once during conversion
- Changing styles requires re-running converter
- Use `--no-styles` flag for quick Pandoc-only conversion
- Test with small files first

---

## Advanced: Modifying Style Code

If you need more control than presets allow, edit `src/styles/docx_styles.py`.

### Common Modifications

**Change code block background:**
```python
# In create_code_block_style()
# Add background color (requires XML manipulation)
```

**Adjust table cell padding:**
```python
# In set_cell_borders()
# Modify cell properties
```

**Add custom paragraph spacing:**
```python
# In _apply_paragraph_style()
# Set para.paragraph_format.space_before
```

> ⚠**Warning:** Modifying `docx_styles.py` requires understanding of python-docx library and XML structure.

---

## Color Palette Generator

Use these tools to create color schemes:

- [Coolors.co](https://coolors.co/) - Generate color palettes
- [Adobe Color](https://color.adobe.com/) - Color wheel and schemes
- [Material Design Colors](https://materialui.co/colors) - Google's color system
- [ColorHunt](https://colorhunt.co/) - Curated color palettes

**Convert hex to RGB:**
```python
# Hex: #1A9CB0
# R = 1A (hex) = 26 (decimal)
# G = 9C (hex) = 156 (decimal)
# B = B0 (hex) = 176 (decimal)
RGBColor(26, 156, 176)
```

---

## Troubleshooting Customization

### Colors not showing correctly

**Check:**
- RGB values are 0-255 (not percentages)
- Border colors are hex strings without `#`
- Correct key names (`'heading1'` not `'h1'`)

### Fonts not applying

**Check:**
- Font name spelled correctly
- Font installed on system opening DOCX
- Use common fonts for compatibility

### Sizes look wrong

**Check:**
- Using `Pt()` wrapper for sizes
- Values are reasonable (10-24pt typically)
- Not mixing different units

### Preset not found error

**Check:**
- Preset name in quotes: `'my_preset'`
- Preset exists in `PRESETS` dictionary
- No typos in `ACTIVE_PRESET` value

---

## Version Compatibility

**Tested with:**
- Python 3.10+
- python-docx 0.8.11+
- Microsoft Word 2016+

**Known Issues:**
- Some advanced fonts may not render in all applications
- Border styles beyond 'single' may not work in all viewers
- Complex color schemes may look different in Google Docs

---

## Getting Help

If customization isn't working:

1. **Test with built-in preset first** - Verify basic conversion works
2. **Check logs with --verbose** - See styling errors
3. **Validate Python syntax** - Check for typos in config
4. **Test minimal changes** - Start simple, add complexity gradually
5. **Compare with working preset** - Use a built-in preset as template

---

**Last Updated:** November 2025  
**Version:** 1.0.0
