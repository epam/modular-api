"""
Style configuration constants.
Edit this file to customize document styles.
"""
from docx.shared import Pt, RGBColor

TIMES_NEW_ROMAN = 'Times New Roman'

# ============================================================================
# COLOR DEFINITIONS
# ============================================================================
# Format: RGBColor(Red, Green, Blue) - values from 0-255
COLORS = {
    'heading1': RGBColor(70, 69, 71),      # Dark Gray
    'heading2': RGBColor(26, 156, 176),    # Teal
    'heading3': RGBColor(44, 196, 201),    # Light Teal
    'heading4': RGBColor(0, 0, 0),         # Black
    'heading5': RGBColor(0, 0, 0),         # Black
    'heading6': RGBColor(0, 0, 0),         # Black
    'normal': RGBColor(0, 0, 0),           # Black
    'code': RGBColor(0, 0, 0),             # Black
    'table_border': '000000',              # Hex color for borders
    'code_border': '000000',               # Hex color for code block borders
}

# ============================================================================
# FONT DEFINITIONS
# ============================================================================
FONTS = {
    'default': 'Arial',
    'headings': 'Arial',
    'code': 'Consolas',
    'normal': 'Arial',
}

# ============================================================================
# FONT SIZE DEFINITIONS
# ============================================================================
# Format: Pt(size) - size in points
SIZES = {
    'heading1': Pt(20),
    'heading2': Pt(16),
    'heading3': Pt(12),
    'heading4': Pt(10),
    'heading5': Pt(10),
    'heading6': Pt(10),
    'normal': Pt(12),
    'normal_base': Pt(10),  # Base normal style
    'code': Pt(11),
}

# ============================================================================
# MARGIN DEFINITIONS
# ============================================================================
# Margins in inches
MARGINS = {
    'default': 0.5,
    'narrow': 0.5,
    'normal': 1.0,
    'wide': 1.5,
}

# ============================================================================
# SPACING DEFINITIONS
# ============================================================================
# Spacing in points
SPACING = {
    'code_left': Pt(10),
    'code_right': Pt(10),
    'code_before': Pt(5),
    'code_after': Pt(5),
}

# ============================================================================
# BORDER DEFINITIONS
# ============================================================================
BORDERS = {
    'table_size': 12,      # Border width for tables
    'code_size': 4,        # Border width for code blocks
    'border_style': 'single',
}

# ============================================================================
# PRESET CONFIGURATIONS
# ============================================================================
# You can create different presets and switch between them

PRESETS = {
    'default': {
        'name': 'Default Style',
        'colors': COLORS,
        'fonts': FONTS,
        'sizes': SIZES,
        'margins': MARGINS,
    },
    'corporate': {
        'name': 'Corporate Style',
        'colors': {
            'heading1': RGBColor(0, 51, 102),      # Navy Blue
            'heading2': RGBColor(0, 102, 204),     # Blue
            'heading3': RGBColor(102, 102, 102),   # Gray
            'heading4': RGBColor(0, 0, 0),
            'heading5': RGBColor(0, 0, 0),
            'heading6': RGBColor(0, 0, 0),
            'normal': RGBColor(0, 0, 0),
            'code': RGBColor(0, 0, 0),
            'table_border': '333333',
            'code_border': '666666',
        },
        'fonts': {
            'default': 'Calibri',
            'headings': 'Calibri',
            'code': 'Courier New',
            'normal': 'Calibri',
        },
        'sizes': SIZES,  # Use default sizes
        'margins': {'default': 1.0},  # Normal margins
    },
    'minimal': {
        'name': 'Minimal Style',
        'colors': {
            'heading1': RGBColor(0, 0, 0),
            'heading2': RGBColor(50, 50, 50),
            'heading3': RGBColor(100, 100, 100),
            'heading4': RGBColor(0, 0, 0),
            'heading5': RGBColor(0, 0, 0),
            'heading6': RGBColor(0, 0, 0),
            'normal': RGBColor(0, 0, 0),
            'code': RGBColor(0, 0, 0),
            'table_border': '000000',
            'code_border': '000000',
        },
        'fonts': {
            'default': TIMES_NEW_ROMAN,
            'headings': TIMES_NEW_ROMAN,
            'code': 'Courier New',
            'normal': TIMES_NEW_ROMAN,
        },
        'sizes': {
            'heading1': Pt(18),
            'heading2': Pt(14),
            'heading3': Pt(12),
            'heading4': Pt(11),
            'heading5': Pt(11),
            'heading6': Pt(11),
            'normal': Pt(11),
            'normal_base': Pt(11),
            'code': Pt(10),
        },
        'margins': {'default': 1.0},
    },
}

# Active preset - change this to switch styles
ACTIVE_PRESET = 'default'  # Options: 'default', 'corporate', 'minimal'


def get_active_style():
    if ACTIVE_PRESET not in PRESETS:
        raise ValueError(
            f"Unknown preset: {ACTIVE_PRESET}. Available: {list(PRESETS.keys())}"
        )
    return PRESETS[ACTIVE_PRESET]
