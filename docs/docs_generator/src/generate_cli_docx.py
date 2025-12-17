"""
Script to generate CLI documentation in DOCX format
"""

import click
from pathlib import Path
import sys
import logging
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from generators.cli_doc_generator import CLIDocGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.command()
@click.option(
    '--module', '-m',
    help='Python module path (e.g., srecli.group.sre)',
)
@click.option(
    '--file', '-f', type=click.Path(exists=True),
    help='Path to Python file containing CLI definition',
)
@click.option(
    '--entry-point', '-e', default='cli',
    help='Name of the Click group/command variable (default: cli)',
)
@click.option(
    '--output', '-o', type=click.Path(),
    help='Output DOCX file path',
)
@click.option(
    '--title', '-t', default='CLI Reference Guide',
    help='Documentation title',
)
@click.option(
    '--generate-md', is_flag=True,
    help='Also generate markdown file',
)
@click.option(
    '--no-title-page', is_flag=True,
    help='Do not add a title page to DOCX',
)
@click.option(
    '--doc-code', '-dc',
    help='Document code for title page (e.g., SRE-DOC-01)',
)
@click.option(
    '--version', '-v', default='Version 1.0',
    help='Version string for title page',
)
@click.option(
    '--date',
    help='Date for title page (defaults to current month/year)',
)
def docs_generator(
        module: str,
        file: str,
        entry_point: str,
        output: str,
        title: str,
        generate_md: bool,
        no_title_page: bool,
        doc_code: str,
        version: str,
        date: str,
) -> None:
    """Generate DOCX documentation for Click-based CLI tools

    You must provide either --module or --file option.

    Examples:

        # Basic usage from file
        python generate_cli_docx.py -f path/to/sre.py -e sre -o sre_docs.docx

        # With custom title page
        python generate_cli_docx.py -f path/to/sre.py -e sre -o sre_docs.docx --doc-code SRE-REF-01 --version "Version 2.0"

        # Without title page
        python generate_cli_docx.py -f path/to/sre.py -e sre -o sre_docs.docx --no-title-page

        # Generate both MD and DOCX
        python generate_cli_docx.py -f path/to/sre.py -e sre -o sre_docs.docx --generate-md
    """

    try:
        # Validate input: must provide either module or file
        if not module and not file:
            raise click.UsageError(
                "You must provide either --module/-m or --file/-f option"
            )

        if module and file:
            raise click.UsageError(
                "Please provide only one of --module or --file, not both"
            )

        # Determine source type and name
        if file:
            source_type = "file"
            source = file
            default_name = Path(file).stem
        else:
            source_type = "module"
            source = module
            default_name = module.split('.')[-1]

        # Determine output paths
        if not output:
            output = f"{default_name}_reference.docx"

        output_path = Path(output)
        md_path = output_path.with_suffix('.md') if generate_md else None

        # Display info
        click.echo(f"Source type: {source_type}")
        click.echo(f"Source: {source}")
        click.echo(f"Entry point: {entry_point}")
        click.echo(f"Output: {output_path}")
        click.echo(f"Title: {title}")
        if generate_md:
            click.echo(f"Markdown: {md_path}")
        if not no_title_page:
            click.echo("Title page: Enabled")
        click.echo()

        # Generate documentation based on source type
        if file:
            generator = CLIDocGenerator.from_file(
                file_path=file,
                entry_point_name=entry_point,
                title=title,
                output_file=str(md_path) if md_path else None,
            )
        else:
            generator = CLIDocGenerator.from_module(
                module_path=module,
                entry_point_name=entry_point,
                title=title,
                output_file=str(md_path) if md_path else None,
            )

        # Prepare title page config
        add_title_page = not no_title_page
        title_page_config = None

        if add_title_page:
            cli_name = entry_point.upper()
            title_page_config = {
                'cli_name': cli_name,
                'document_code': doc_code or f"{cli_name}-REF-01",
                'version': version,
                'date': date or datetime.now().strftime('%B %Y'),
            }

        # Generate DOCX
        click.echo("Generating documentation...")
        docx_path = generator.generate_docx(
            str(output_path),
            add_title_page=add_title_page,
            title_page_config=title_page_config,
        )

        # Success message
        click.echo()
        click.echo(click.style(
            "✓ Documentation generated successfully!",
            fg='green',
            bold=True
        ))
        click.echo(f"  DOCX: {docx_path}")

        if md_path and Path(md_path).exists():
            click.echo(f"  Markdown: {md_path}")

    except click.UsageError as e:
        click.echo(click.style(
            f"\n✗ Usage Error: {str(e)}",
            fg='red',
            bold=True
        ), err=True)
        click.echo("\nUse --help for usage information")
        sys.exit(1)

    except Exception as e:
        click.echo(click.style(
            f"\n✗ Error: {str(e)}",
            fg='red',
            bold=True
        ), err=True)
        logging.exception("Full error traceback:")
        sys.exit(1)


if __name__ == '__main__':
    docs_generator()
