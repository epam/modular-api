"""
Markdown to DOCX converter with custom styling
"""

import pypandoc
from pathlib import Path
from typing import Any
import logging

from generators.title_page import add_cli_title_page, add_custom_title_page
from styles.docx_styles import apply_custom_styles

logger = logging.getLogger(__name__)


class MarkdownToDocxConverter:
    """Converts Markdown files to styled DOCX documents"""

    def __init__(
            self,
            md_file: str,
            docx_file: str | None = None,
            apply_styles: bool = True,
            title_page_config: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the converter

        Args:
            md_file: Path to the markdown file
            docx_file: Path for the output DOCX file (optional)
            apply_styles: Whether to apply custom styling
            title_page_config: Configuration for title page (optional)
                Example: {
                    'cli_name': 'SRE CLI',
                    'document_code': 'SRE-DOC-01',
                    'version': 'Version 1.0',
                    'date': 'January 2025'
                }
        """
        self.md_file = Path(md_file)

        if docx_file:
            self.docx_file = Path(docx_file)
        else:
            self.docx_file = self.md_file.with_suffix('.docx')

        self.apply_styles = apply_styles
        self.title_page_config = title_page_config

        if not self.md_file.exists():
            raise FileNotFoundError(f"Markdown file not found: {md_file}")

    def convert(
            self,
    ) -> Path:
        """
        Convert markdown to DOCX with styling and optional title page

        Returns:
            Path to the generated DOCX file
        """
        logger.info(f"Converting {self.md_file} to {self.docx_file}")

        try:
            # Convert MD to DOCX using pypandoc
            self._convert_with_pandoc()

            # Apply custom styles if enabled
            if self.apply_styles:
                apply_custom_styles(str(self.docx_file))

            # Add title page if configured
            if self.title_page_config:
                self._add_title_page()

            logger.info(f"✓ Successfully created: {self.docx_file}")
            return self.docx_file

        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            raise

    def _convert_with_pandoc(
            self,
    ) -> None:
        """Convert using pypandoc with specific options"""
        extra_args = [
            '--highlight-style=tango',  # Code highlighting
            '--reference-links',  # Use reference-style links
            '--shift-heading-level-by=0',  # Don't promote headings
            '--markdown-headings=atx',  # Use ATX-style headings
        ]

        try:
            pypandoc.convert_file(
                str(self.md_file),
                'docx',
                outputfile=str(self.docx_file),
                extra_args=extra_args,
            )
            logger.info("Pandoc conversion successful")

        except RuntimeError as e:
            if 'Pandoc died' in str(e):
                logger.error(
                    "Pandoc error. Make sure Pandoc is installed correctly. "
                    "Visit https://pandoc.org/installing.html"
                )
            raise

    def _add_title_page(
            self,
    ) -> None:
        """Add title page to the document"""
        try:
            config = self.title_page_config

            # Check if using simple CLI format or custom format
            if 'cli_name' in config:
                add_cli_title_page(
                    docx_path=str(self.docx_file),
                    cli_name=config.get('cli_name', 'CLI Tool'),
                    document_code=config.get('document_code'),
                    version=config.get('version'),
                    date=config.get('date'),
                )
            else:
                add_custom_title_page(
                    docx_path=str(self.docx_file),
                    main_title=config.get('main_title', 'Documentation'),
                    subtitle=config.get('subtitle'),
                    author=config.get('author'),
                    organization=config.get('organization'),
                    version=config.get('version'),
                    date=config.get('date'),
                )

            logger.info("Title page added successfully")

        except Exception as e:
            logger.warning(f"Failed to add title page: {e}")


def convert_md_to_docx(
        md_file: str,
        docx_file: str | None = None,
        apply_styles: bool = True,
        title_page_config: dict[str, Any] | None = None,
) -> Path:
    """
    Convenience function to convert markdown to DOCX

    Args:
        md_file: Path to the markdown file
        docx_file: Path for the output DOCX file (optional)
        apply_styles: Whether to apply custom styling
        title_page_config: Configuration for title page (optional)

    Returns:
        Path to the generated DOCX file
    """
    converter = MarkdownToDocxConverter(
        md_file,
        docx_file,
        apply_styles,
        title_page_config,
    )
    return converter.convert()
