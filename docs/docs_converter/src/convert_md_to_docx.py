#!/usr/bin/env python3
"""
Simple Markdown to DOCX Converter
Converts MD files to DOCX with custom styling using pandoc.

Usage:
    python convert_md_to_docx.py input.md -o output.docx
    python convert_md_to_docx.py input.md -o output.docx --no-styles
"""
import argparse
import logging
import subprocess
import shutil
import sys
from pathlib import Path
from styles.docx_styles import apply_custom_styles

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
_LOG = logging.getLogger(__name__)


def check_pandoc_installed() -> bool:
    """Check if pandoc is available in system PATH."""
    return shutil.which('pandoc') is not None


def convert_md_to_docx(
        input_md: Path | str,
        output_docx: Path | str,
        apply_styles: bool = True,
        pandoc_extra_args: list[str] | None = None,
) -> None:
    """
    Convert Markdown to DOCX using pandoc and apply custom styles.

    Args:
        input_md: Path to input Markdown file
        output_docx: Path to output DOCX file
        apply_styles: Whether to apply custom styles (default: True)
        pandoc_extra_args: Additional arguments to pass to pandoc

    Raises:
        FileNotFoundError: If input file doesn't exist
        RuntimeError: If pandoc not found or conversion fails
    """
    # Check pandoc first
    if not check_pandoc_installed():
        raise RuntimeError(
            "Pandoc not found. Please install it from: "
            "https://pandoc.org/installing.html"
        )

    input_path = Path(input_md)
    output_path = Path(output_docx)

    # Validate inputs
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_md}")

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Build pandoc command
    pandoc_cmd = [
        'pandoc',
        str(input_path),
        '-o', str(output_path),
        '--from', 'markdown',
        '--to', 'docx',
        '--standalone',
    ]

    # Add extra arguments if provided
    if pandoc_extra_args:
        pandoc_cmd.extend(pandoc_extra_args)

    try:
        _LOG.debug(f"Running pandoc: {' '.join(pandoc_cmd)}")

        result = subprocess.run(
            pandoc_cmd,
            check=True,
            capture_output=True,
            text=True,
        )

        if result.stderr:
            _LOG.warning(f"Pandoc warnings: {result.stderr}")

        _LOG.info(f"✓ Pandoc conversion completed: {output_path}")

        # Apply custom styles if requested
        if apply_styles:
            _LOG.debug("Applying custom styles...")
            apply_custom_styles(str(output_path))
            _LOG.info("✓ Custom styles applied")

    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Pandoc conversion failed: {e.stderr}") from e


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Convert Markdown to DOCX with custom styling',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  python convert_md_to_docx.py input.md -o output.docx

  # Without custom styles
  python convert_md_to_docx.py input.md -o output.docx --no-styles

  # With verbose logging
  python convert_md_to_docx.py input.md -o output.docx --verbose

Note:
  To merge multiple markdown files, use cat/type command first:
    Unix/Linux/Mac: cat file1.md file2.md > merged.md
    Windows:        type file1.md file2.md > merged.md
        """,
    )

    parser.add_argument(
        'input',
        help='Input Markdown file',
    )
    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output DOCX file',
    )
    parser.add_argument(
        '--no-styles',
        action='store_true',
        help='Skip applying custom styles',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable debug logging',
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        input_file = Path(args.input)

        if not input_file.exists():
            _LOG.error(f"Input file not found: {input_file}")
            return 1

        # Convert to DOCX
        _LOG.info(f"Converting {input_file.name} to DOCX...")
        convert_md_to_docx(
            input_md=input_file,
            output_docx=args.output,
            apply_styles=not args.no_styles,
        )

        _LOG.info(f"✓ Successfully converted to: {args.output}")
        return 0

    except Exception as e:
        _LOG.error(f"Conversion failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
