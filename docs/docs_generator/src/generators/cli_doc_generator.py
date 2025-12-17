"""
Automatic CLI Documentation Generator for Click-based tools
Generates Reference Guide in Markdown format with tree structure
"""
import re
import click
from pathlib import Path
from typing import Any
import importlib.util

CLI_REFERENCE_GUIDE = "CLI Reference Guide"
TABLE_HEADER = \
    "|     Option      | Type |Req| Default |         Description           |"
TABLE_SEPARATOR = \
    "|-----------------|------|----|--------|-------------------------------|"
PAGE_BREAK = "\n{{ pagebreak }}\n"
SECTION_SEPARATOR = "\n{{ pagebreak }}\n"

class ClickCommandParser:
    """Parses Click commands and extracts documentation metadata"""

    @staticmethod
    def parse_command(
            cmd: click.Command,
            cmd_path: list[str],
    ) -> dict[str, Any]:
        """Parse a single Click command and extract its metadata"""
        options: list[dict[str, Any]] = []
        arguments: list[dict[str, Any]] = []
        subcommands: list[dict[str, Any]] = []

        info: dict[str, Any] = {
            'name': cmd.name,
            'type': 'group' if isinstance(cmd, click.Group) else 'command',
            'path': cmd_path,
            'full_path': ' '.join(cmd_path),
            'help': (cmd.help or cmd.short_help or '').strip(),
            'short_help': (cmd.short_help or '').strip(),
            'deprecated': cmd.deprecated,
            'hidden': cmd.hidden,
            'options': options,
            'arguments': arguments,
            'subcommands': subcommands,
        }

        # Extract parameters (options and arguments)
        for param in cmd.params:
            param_info: dict[str, Any] = \
                ClickCommandParser._parse_parameter(param)
            if isinstance(param, click.Option):
                info['options'].append(param_info)
            elif isinstance(param, click.Argument):
                info['arguments'].append(param_info)

        # Recursively parse subcommands if it's a group
        if isinstance(cmd, click.Group):
            for subcmd_name in sorted(cmd.list_commands(click.Context(cmd))):
                subcmd = cmd.get_command(click.Context(cmd), subcmd_name)
                if subcmd and not subcmd.hidden:
                    subcmd_info = ClickCommandParser.parse_command(
                        cmd=subcmd,
                        cmd_path=cmd_path + [subcmd.name],
                    )
                    info['subcommands'].append(subcmd_info)

        return info

    @staticmethod
    def _parse_parameter(
            param: click.Parameter,
    ) -> dict[str, Any]:
        """Parse a Click parameter (option or argument)"""
        param_info = {
            'name': param.name,
            'opts': getattr(param, 'opts', []),
            'secondary_opts': getattr(param, 'secondary_opts', []),
            'type': ClickCommandParser._format_type(param.type),
            'required': param.required,
            'default': param.default if param.default is not None else None,
            'help': (getattr(param, 'help', '') or '').strip(),
            'multiple': getattr(param, 'multiple', False),
            'is_flag': isinstance(param, click.Option) and param.is_flag,
            'hidden': getattr(param, 'hidden', False),
        }

        # Handle choices
        if isinstance(param.type, click.Choice):
            param_info['choices'] = param.type.choices

        # Handle ranges
        if isinstance(param.type, (click.IntRange, click.FloatRange)):
            param_info['min'] = param.type.min
            param_info['max'] = param.type.max

        return param_info

    @staticmethod
    def _format_type(
            param_type: Any,
    ) -> str:
        """Format parameter type for documentation"""
        if isinstance(param_type, click.Choice):
            # Clean choices to avoid backtick issues
            choices = [c.replace('`', "'") for c in param_type.choices]
            return f"choice: {', '.join(choices)}"

        elif isinstance(param_type, click.IntRange):
            min_val = param_type.min
            max_val = param_type.max

            # Handle different range scenarios
            if min_val is not None and max_val is not None:
                return f"integer ({min_val} to {max_val})"
            elif min_val is not None:
                return f"integer (≥ {min_val})"
            elif max_val is not None:
                return f"integer (≤ {max_val})"
            else:
                return "integer"

        elif isinstance(param_type, click.FloatRange):
            min_val = param_type.min
            max_val = param_type.max

            # Handle different range scenarios
            if min_val is not None and max_val is not None:
                return f"float ({min_val} to {max_val})"
            elif min_val is not None:
                return f"float (≥ {min_val})"
            elif max_val is not None:
                return f"float (≤ {max_val})"
            else:
                return "float"

        elif isinstance(param_type, click.types.StringParamType):
            return "string"
        elif isinstance(param_type, click.types.IntParamType):
            return "integer"
        elif isinstance(param_type, click.types.FloatParamType):
            return "float"
        elif isinstance(param_type, click.types.BoolParamType):
            return "boolean"
        else:
            return param_type.name \
                if hasattr(param_type, 'name') else str(param_type)


class MarkdownGenerator:
    """Generates Markdown documentation from parsed command data"""
    # Configuration constants
    MAX_DEFAULT_LENGTH = 20  # Maximum length for default values
    MAX_TOC_DESCRIPTION_LENGTH = 200  # Maximum length for TOC descriptions

    def __init__(
            self,
            title: str = CLI_REFERENCE_GUIDE,
    ) -> None:
        self.title = title
        self.content: list[str] = []

    def _sort_command_tree(
            self,
            command_tree: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Recursively sort command tree:
        1. Groups first, then commands
        2. Alphabetically within each category

        Args:
            command_tree: Command tree dictionary

        Returns:
            Sorted command tree dictionary
        """
        # Create a copy to avoid modifying the original
        sorted_tree = command_tree.copy()

        # Sort subcommands if they exist
        if 'subcommands' in sorted_tree and sorted_tree['subcommands']:
            # Sort by: 1) type (commands first), 2) name (alphabetically)
            sorted_subcommands = sorted(
                sorted_tree['subcommands'],
                key=lambda cmd: (
                    1 if cmd['type'] == 'group' else 0,
                    cmd['name'].lower()
                )
            )

            # Recursively sort each subcommand's children
            sorted_tree['subcommands'] = [
                self._sort_command_tree(subcmd)
                for subcmd in sorted_subcommands
            ]

        return sorted_tree

    def generate(
            self,
            command_tree: dict[str, Any],
    ) -> str:
        """Generate complete markdown documentation with sorted commands"""
        self.content = []

        # Sort the command tree before generating documentation
        sorted_tree = self._sort_command_tree(command_tree)

        # Header
        self._add_header()
        # Table of contents
        self._add_toc(
            command_tree=sorted_tree,
            max_description_length=self.MAX_TOC_DESCRIPTION_LENGTH,
        )
        # Detailed command documentation (NEW PAGE)
        self._add_detailed_docs(sorted_tree)

        return '\n'.join(self.content)

    def _add_header(self) -> None:
        """Add document header"""
        self.content.append(f"# {self.title}\n")
        self.content.append("*Auto-generated documentation*\n")
        self.content.append("---\n")

    def _add_toc(
            self,
            command_tree: dict[str, Any],
            max_description_length: int = MAX_TOC_DESCRIPTION_LENGTH,
    ) -> None:
        """Add table of contents with links and descriptions"""
        # Add an anchor that we can link back to
        self.content.append('<a id="table-of-contents"></a>\n')
        self.content.append("## Table of Contents\n")
        self._generate_toc_recursive(
            cmd=command_tree,
            level=0,
            max_length=max_description_length,
        )
        self.content.append("---\n")

    def _generate_toc_recursive(
            self,
            cmd: dict[str, Any],
            level: int,
            max_length: int,
            depth: int = 0,
    ) -> None:
        """Generate TOC recursively with descriptions and type labels"""
        indent = "  " * level
        prefix_type = "group-" if cmd['type'] == 'group' else "command-"
        full_path = prefix_type + cmd['full_path'].replace(' ', '-')

        # Determine the label
        if depth == 0:
            # Root level - this is the CLI entry point
            label = "[CLI]"
            line = f"{indent}- **{label} [{cmd['name']}](#{full_path})**"
        elif cmd['type'] == 'group':
            # Groups
            label = "[Group]"
            line = f"{indent}- **{label} [{cmd['name']}](#{full_path})**"
        else:
            # Commands
            label = "[Command]"
            line = f"{indent}- {label} [`{cmd['name']}`](#{full_path})"

        # Add description for:
        # - All groups (including root)
        # - Top-level commands only (depth 1)
        should_add_description = (
                (cmd['type'] == 'group') or
                (cmd['type'] == 'command' and depth == 1)
        )

        if should_add_description and cmd['help']:
            # Clean description
            description = cmd['help'].strip()
            description = ' '.join(description.split())

            # Truncate if needed
            if len(description) > max_length:
                description = description[:max_length - 3] + "..."

            # Add in italics
            line += f" - *{description}*"

        self.content.append(line)

        # Process subcommands
        for subcmd in cmd.get('subcommands', []):
            self._generate_toc_recursive(
                cmd=subcmd,
                level=level + 1,
                max_length=max_length,
                depth=depth + 1,
            )

    def _add_detailed_docs(
            self,
            command_tree: dict[str, Any],
    ) -> None:
        """Add detailed documentation for all commands"""
        # Add page break before detailed docs
        self.content.append(PAGE_BREAK)

        self.content.append("## Detailed Command Reference\n")
        self._generate_detailed_docs_recursive(
            command_tree,
            level=2,
            parent_is_root=True,
        )

    def _generate_detailed_docs_recursive(
            self,
            cmd: dict[str, Any],
            level: int,
            parent_is_root: bool = False,
    ) -> None:
        """
        Recursively generate detailed documentation

        Args:
            cmd: Command dictionary
            level: Heading level (for markdown headers)
            parent_is_root: True if parent is the root CLI command
        """
        # Add anchor for linking back to this section
        prefix_type = "group-" if cmd['type'] == 'group' else "command-"
        full_path = prefix_type + cmd['full_path'].replace(' ', '-')
        self.content.append(f'<a id="{full_path}"></a>\n')

        # Command header
        header_prefix = "#" * level
        header_type = "Group" if cmd['type'] == 'group' else "Command"
        self.content.append(
            f"{header_prefix} {header_type}: `{cmd['full_path']}`\n"
        )

        # Description
        if cmd['help']:
            self.content.append("**Description:**\n")
            self.content.append(f"{cmd['help']}\n")

        # Usage
        self._add_usage(cmd)

        # Arguments
        if cmd['arguments']:
            self._add_arguments(cmd['arguments'])

        # Options
        if cmd['options']:
            self._add_options(cmd['options'])

        self.content.append(
            "[↑ Back to Table of Contents](#table-of-contents)\n"
        )

        # Recurse into subcommands
        subcommands = cmd.get('subcommands', [])
        for i, subcmd in enumerate(subcommands):
            if parent_is_root and i > 0:
                self.content.append(SECTION_SEPARATOR)

            self._generate_detailed_docs_recursive(
                cmd=subcmd,
                level=level + 1,
                parent_is_root=False,
            )

    def _add_usage(
            self,
            cmd: dict[str, Any],
    ) -> None:
        """Add usage section"""
        self.content.append("**Usage:**\n")
        usage = f"{cmd['full_path']}"

        # Add arguments
        for arg in cmd['arguments']:
            arg_str = arg['name'].upper()
            if not arg['required']:
                arg_str = f"[{arg_str}]"
            if arg['multiple']:
                arg_str += "..."
            usage += f" {arg_str}"

        # Add options indicator
        if cmd['options']:
            usage += " [OPTIONS]"

        self.content.append(f"```bash\n{usage}\n```\n")

    def _add_arguments(
            self,
            arguments: list[dict[str, Any]],
    ) -> None:
        """Add arguments section"""
        self.content.append("**Arguments:**\n")
        self.content.append("| Argument | Type | Required | Description |")
        self.content.append("|----------|------|----------|-------------|")

        for arg in arguments:
            name = arg['name'].upper()
            arg_type = arg['type']
            required = "✓" if arg['required'] else "✗"
            help_text = arg['help'] or "—"

            if arg['multiple']:
                name += "..."

            self.content.append(
                f"| `{name}` | {arg_type} | {required} | {help_text} |"
            )

        self.content.append("")

    def _add_options(
            self,
            options: list[dict[str, Any]],
    ) -> None:
        """Add all options in table format"""
        self.content.append("**Options:**\n")

        # Ensure blank line before table
        if self.content and self.content[-1].strip():
            self.content.append("")

        self.content.append(TABLE_HEADER)
        self.content.append(TABLE_SEPARATOR)

        for opt in options:
            # Get option names
            opt_names = ", ".join([f"`{o}`" for o in opt['opts']])

            # Type
            opt_type = self._format_option_type(opt)

            # Required
            required = "✓" if opt['required'] else "✗"

            # Default
            default = self._format_default_value(
                opt=opt,
                max_length=self.MAX_DEFAULT_LENGTH,
            )

            # Description - get base help text
            help_text = opt.get('help', '').strip()

            # Append choices to description if present
            if 'choices' in opt:
                choices_str = ', '.join(opt['choices'])
                if help_text:
                    help_text += f". Available choices: {choices_str}"
                else:
                    help_text = f"Available choices: {choices_str}"

            # Clean and escape the final description
            help_text = self._clean_description(help_text)

            self.content.append(
                f"| {opt_names} | {opt_type} | {required} | {default} | {help_text} |"
            )

        # Ensure blank line after table
        self.content.append("")

    @staticmethod
    def _format_option_type(
            opt: dict[str, Any],
    ) -> str:
        """Format option type for table display"""
        if opt.get('is_flag', False):
            return "flag"

        opt_type = opt['type']

        if 'choices' in opt:
            # Just return "choice" - the actual choices will be in description
            return "choice"

        return opt_type

    @staticmethod
    def _format_default_value(
            opt: dict[str, Any],
            max_length: int = MAX_DEFAULT_LENGTH,
    ) -> str:
        """
        Format default value for display

        Args:
            opt: Option dictionary
            max_length: Maximum length before truncation
        """
        if opt['is_flag']:
            return "`False`"

        default_val = opt['default']

        # Handle Sentinel values (like click.UNSET)
        if default_val is None or 'Sentinel' in str(type(default_val)) \
                or str(default_val) == 'Sentinel.UNSET':
            return "—"

        # Handle special characters and whitespace
        if isinstance(default_val, str):
            # Replace common special characters with their escaped versions
            replacements = {
                '\n': '\\n',
                '\r': '\\r',
                '\t': '\\t',
            }

            # Check if it's just whitespace
            if default_val.strip() == '':
                if default_val == '\n':
                    return '`\\n`'
                elif default_val == '\r':
                    return '`\\r`'
                elif default_val == '\t':
                    return '`\\t`'
                elif default_val == ' ':
                    return '` `'
                else:
                    return f'`{repr(default_val)}`'

            # Escape backslashes first
            formatted_val = default_val.replace('\\', '\\\\')

            # Replace special characters
            for char, replacement in replacements.items():
                if char in formatted_val:
                    formatted_val = formatted_val.replace(char, replacement)

            # Truncate if too long (account for backticks in length)
            if len(formatted_val) > max_length:
                # Truncate and add ellipsis
                formatted_val = formatted_val[:max_length - 3] + '...'

            return f'`{formatted_val}`'

        # Handle lists/tuples
        if isinstance(default_val, (list, tuple)):
            str_val = str(default_val)
            if len(str_val) > max_length:
                str_val = str_val[:max_length - 3] + '...'
            return f'`{str_val}`'

        # Handle dicts
        if isinstance(default_val, dict):
            str_val = str(default_val)
            if len(str_val) > max_length:
                str_val = str_val[:max_length - 3] + '...'
            return f'`{str_val}`'

        # Handle other types (int, float, bool, etc.)
        str_val = str(default_val)
        if len(str_val) > max_length:
            str_val = str_val[:max_length - 3] + '...'

        return f'`{str_val}`'

    def _clean_description(
            self,
            text: str,
    ) -> str:
        """Clean and format description text for table cells"""
        if not text:
            return "—"

        # Replace actual newlines with space
        text = text.replace('\n', ' ')

        # Replace multiple spaces with single space
        text = ' '.join(text.split())

        # Fix problematic backtick patterns (e.g., "command`s" -> "command's")
        # This handles cases like: command`s, option`s, etc.
        text = re.sub(r'(\w)`s\b', r"\1's", text)

        # Remove stray backticks that aren't part of code formatting
        # Keep backticks only if they're in pairs around code
        # Simple approach: if odd number of backticks, remove them all
        if text.count('`') % 2 != 0:
            text = text.replace('`', "'")

        # Escape pipe characters that would break Markdown tables
        text = text.replace('|', '\\|')

        return text.strip() or "—"


class CLIDocGenerator:
    """Main documentation generator class"""

    def __init__(
            self,
            cli_entry_point: click.Group,
            title: str = CLI_REFERENCE_GUIDE,
            output_file: str | None = None,
    ) -> None:
        """
        Initialize the documentation generator

        Args:
            cli_entry_point: The root Click group/command
            title: Title for the documentation
            output_file: Optional output file path
        """
        self.cli_entry_point = cli_entry_point
        self.title = title
        self.output_file = output_file
        self.parser = ClickCommandParser()
        self.markdown_gen = MarkdownGenerator(title)

    def generate(self) -> str:
        """Generate the documentation"""
        # Parse the command tree
        command_tree = self.parser.parse_command(
            cmd=self.cli_entry_point,
            cmd_path=[self.cli_entry_point.name],
        )

        # Generate markdown
        markdown_content = self.markdown_gen.generate(command_tree)

        # Save to file if specified
        if self.output_file:
            self.save_to_file(markdown_content)

        return markdown_content

    def save_to_file(
            self,
            content: str,
    ) -> None:
        """Save documentation to file"""
        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ Documentation generated: {output_path}")

    @staticmethod
    def from_module(
            module_path: str,
            entry_point_name: str = 'cli',
            **kwargs,
    ) -> 'CLIDocGenerator':
        """
        Create generator from a module path

        Args:
            module_path: Path to the Python module (e.g., 'srecli.group.sre')
            entry_point_name: Name of the Click group/command variable
            **kwargs: Additional arguments for CLIDocGenerator
        """
        # Import the module
        module = importlib.import_module(module_path)
        # Get the CLI entry point
        cli_entry_point = getattr(module, entry_point_name)

        if not isinstance(cli_entry_point, (click.Group, click.Command)):
            raise ValueError(
                f"{entry_point_name} is not a Click command or group"
            )

        return CLIDocGenerator(cli_entry_point, **kwargs)

    @staticmethod
    def from_file(
            file_path: str,
            entry_point_name: str = 'cli',
            **kwargs,
    ) -> 'CLIDocGenerator':
        """
        Create generator from a file path

        Args:
            file_path: Path to the Python file
            entry_point_name: Name of the Click group/command variable
            **kwargs: Additional arguments for CLIDocGenerator
        """
        import sys
        from pathlib import Path

        file_path = Path(file_path).resolve()

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        # Simple heuristic: go up until we find a directory containing
        # a subdirectory with __init__.py (likely the package root)
        # For: /path/to/project/package/group/file.py
        # Find: /path/to/project (contains package/)

        package_root = None
        current = file_path.parent

        # Check up to 5 levels up
        for _ in range(5):
            parent = current.parent

            # If current dir has __init__.py, its parent is likely the package root
            if (current / '__init__.py').exists():
                package_root = parent

            # Also check for common project indicators
            if (parent / 'setup.py').exists() \
                    or (parent / 'pyproject.toml').exists():
                package_root = parent
                break

            if parent == current:  # Reached filesystem root
                break

            current = parent

        # Default to parent of parent if nothing found
        if package_root is None:
            package_root = file_path.parent.parent

        # Store original sys.path
        original_path = sys.path.copy()

        # Add package root to sys.path
        if str(package_root) not in sys.path:
            sys.path.insert(0, str(package_root))

        try:
            # Load module from file
            spec = importlib.util.spec_from_file_location(
                name="cli_module",
                location=file_path,
            )
            if spec is None or spec.loader is None:
                raise ImportError(f"Could not load module from {file_path}")

            module = importlib.util.module_from_spec(spec)
            sys.modules['cli_module'] = module

            spec.loader.exec_module(module)

            # Get the CLI entry point
            if not hasattr(module, entry_point_name):
                raise ValueError(
                    f"Module does not have attribute '{entry_point_name}'"
                )

            cli_entry_point = getattr(module, entry_point_name)

            if not isinstance(cli_entry_point, (click.Group, click.Command)):
                raise ValueError(
                    f"{entry_point_name} is not a Click command or group"
                )

            return CLIDocGenerator(cli_entry_point, **kwargs)

        finally:
            # Restore original sys.path
            sys.path = original_path
            # Clean up
            if 'cli_module' in sys.modules:
                del sys.modules['cli_module']

    def generate_docx(
            self,
            docx_file: str | None = None,
            add_title_page: bool = True,
            title_page_config: dict[str, Any] | None= None,
    ) -> str:
        """
        Generate DOCX documentation directly

        Args:
            docx_file: Optional path for the DOCX output file
            add_title_page: Whether to add a title page
            title_page_config: Custom title page configuration

        Returns:
            Path to the generated DOCX file
        """
        from converters.md_to_docx_converter import convert_md_to_docx
        import tempfile
        from datetime import datetime

        # Generate markdown first
        markdown_content = self.generate()

        # Create temporary MD file if no output file was specified
        if not self.output_file:
            with tempfile.NamedTemporaryFile(
                    mode='w',
                    suffix='.md',
                    delete=False,
                    encoding='utf-8',
            ) as tmp_md:
                tmp_md.write(markdown_content)
                temp_md_path = tmp_md.name
        else:
            temp_md_path = self.output_file

        # Determine DOCX output path
        if not docx_file:
            if self.output_file:
                docx_file = str(Path(self.output_file).with_suffix('.docx'))
            else:
                docx_file = f"{self.cli_entry_point.name}_reference.docx"

        # Prepare title page config if enabled
        if add_title_page and title_page_config is None:
            title_page_config = {
                'cli_name': self.cli_entry_point.name.upper(),
                'document_code': f"{self.cli_entry_point.name.upper()}-REF-01",
                'version': 'Version 1.0',
                'date': datetime.now().strftime('%B %Y'),
            }
        elif not add_title_page:
            title_page_config = None

        # Convert to DOCX
        try:
            output_path = convert_md_to_docx(
                md_file=temp_md_path,
                docx_file=docx_file,
                title_page_config=title_page_config,
            )
            print(f"✓ DOCX documentation generated: {output_path}")
            return str(output_path)
        finally:
            # Clean up temp file if we created one
            if not self.output_file and Path(temp_md_path).exists():
                Path(temp_md_path).unlink()


# Convenience function
def generate_cli_docs(
        cli_entry_point: click.Group,
        output_file: str,
        title: str = CLI_REFERENCE_GUIDE,
) -> str:
    """
    Convenience function to generate CLI documentation

    Args:
        cli_entry_point: The root Click group/command
        output_file: Output file path for the markdown
        title: Documentation title

    Returns:
        Generated markdown content
    """
    generator = CLIDocGenerator(cli_entry_point, title, output_file)
    return generator.generate()
