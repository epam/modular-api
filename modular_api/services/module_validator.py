"""
CLI module structure validator for modular-api.

Validates Click CLI structure, naming conventions, and
modular-api commands_generator.py compatibility.

Core checks catch issues that WILL break modular-api integration:
  - __resolve_group_name() splits filenames on '_'
  - _get_group_from_module() matches obj.name == last segment
  - Nesting logic only handles depth <= 3

Extended checks (--recommendations) catch code quality issues:
  - Missing type hints, return types, docstrings
  - Parameter ordering and alignment
  - Option help text
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from modular_api.commands_generator import (
    GROUP_NAME_SEPARATOR,
    REQUIRED_PARAM_CALLBACKS as _RAW_REQUIRED_CALLBACKS,
    extract_root_group_name,
)
from modular_api.helpers.log_helper import get_logger

_LOG = get_logger(__name__)

# commands_generator only handles [0], [1], and last - max 3 segments
MAX_GROUP_DEPTH = 3
# Decorator names treated as Click group/command definitions.
# Includes standard click + known wrapper modules (e.g. m3_admin's `group`).
# Add new wrapper names here to support more modules.
GROUP_WRAPPER_NAMES: frozenset[str] = frozenset({
    "group",  # m3_admin.utils.base_click_command_interface.group
})
# Filter to actual callback function names (skip 'required=True' etc.)
REQUIRED_CALLBACK_NAMES: frozenset[str] = frozenset(
    cb for cb in _RAW_REQUIRED_CALLBACKS if '=' not in cb
)


# ---------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------

class Severity(Enum):
    ERROR = "ERROR"
    WARNING = "WARNING"
    INFO = "INFO"


SEVERITY_ORDER = {
    Severity.ERROR: 0,
    Severity.WARNING: 1,
    Severity.INFO: 2,
}


@dataclass
class Issue:
    severity: Severity
    file: str
    line: int | None
    rule: str
    message: str

    def __str__(self) -> str:
        loc = f":{self.line}" if self.line else ""
        return (
            f"[{self.severity.value}] {self.file}{loc} "
            f"({self.rule}): {self.message}"
        )


@dataclass
class OptionInfo:
    long_name: str | None
    short_name: str | None
    dest_name: str | None
    required: bool
    param_type: str | None
    multiple: bool
    line: int
    has_help: bool = False
    has_callback: bool = False
    raw_text: str = ""


@dataclass
class ParamInfo:
    name: str
    annotation: str | None
    has_default: bool
    default_value: str | None
    line: int


@dataclass
class GroupInfo:
    function_name: str
    line: int
    docstring: str | None = None
    is_hidden: bool = False
    # Click name from @group(name='chef') decorator (None = use function_name)
    explicit_name: str | None = None

    @property
    def click_name(self) -> str:
        """The name Click will register this group under."""
        return self.explicit_name or self.function_name


@dataclass
class CommandInfo:
    name: str
    function_name: str
    line: int
    decorator_options: list[OptionInfo] = field(default_factory=list)
    decorator_arguments: list[str] = field(default_factory=list)
    function_params: list[ParamInfo] = field(default_factory=list)
    has_return_type: bool = False
    return_type: str | None = None
    docstring: str | None = None
    is_hidden: bool = False
    has_pass_context: bool = False
    has_var_kwargs: bool = False


@dataclass
class FileAnalysis:
    filepath: Path
    filename: str
    groups: list[GroupInfo] = field(default_factory=list)
    commands: list[CommandInfo] = field(default_factory=list)
    add_command_calls: list[tuple[str, str, int]] = field(
        default_factory=list,
    )
    parse_error: str | None = None


@dataclass
class ValidationResult:
    """Result of validating a module's CLI structure."""
    issues: list[Issue] = field(default_factory=list)
    scanned_files: list[str] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.WARNING]

    @property
    def infos(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == Severity.INFO]

    @property
    def can_install(self) -> bool:
        """No errors - safe to install."""
        return not self.errors

    @property
    def can_install_strict(self) -> bool:
        """No errors AND no warnings - strictest gate."""
        return not self.errors and not self.warnings

    def format_report(
            self,
            show_warnings: bool = False,
            show_infos: bool = False,
            use_color: bool = False,
            strict: bool = False,
            force_install: bool = False,
    ) -> str:
        """
        Format issues as a human-readable report.

        :param show_warnings: include WARNING-level issues
        :param show_infos: include INFO-level issues
        :param use_color: use ANSI color codes
        :param strict: format footer for strict-mode evaluation
            (warnings treated as failures)
        :param force_install: format footer for --force install context
            (errors present but installation will proceed)
        """
        # Build the set of severities to include
        include = {Severity.ERROR}
        if show_warnings:
            include.add(Severity.WARNING)
        if show_infos:
            include.add(Severity.INFO)

        filtered = [
            i for i in self.issues if i.severity in include
        ]
        if not filtered:
            return "All CLI structure checks passed."

        colors: dict[Severity, str] = {}
        reset = ""
        if use_color:
            colors = {
                Severity.ERROR: "\033[91m",
                Severity.WARNING: "\033[93m",
                Severity.INFO: "\033[94m",
            }
            reset = "\033[0m"

        lines: list[str] = []

        # Group by file
        by_file: dict[str, list[Issue]] = {}
        for issue in filtered:
            by_file.setdefault(issue.file, []).append(issue)

        # Clean files
        files_with_issues = set(by_file.keys())
        clean_files = [
            f for f in self.scanned_files if f not in files_with_issues
        ]

        # Adjust wording based on what severity levels are displayed
        if show_warnings and show_infos:
            clean_label = "no issues"
            issue_label = "with issues"
        elif show_warnings:
            clean_label = "no errors or warnings"
            issue_label = "with errors or warnings"
        else:
            clean_label = "no errors"
            issue_label = "with errors"

        lines.append("")
        lines.append("=" * 70)
        lines.append("  CLI Module Validation Report")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"Scanned {len(self.scanned_files)} file(s)")
        if clean_files:
            clean_msg = (
                f"  {len(clean_files)} file(s) with {clean_label}: "
                f"{', '.join(sorted(clean_files))}"
            )
            if use_color:
                clean_msg = f"\033[92m{clean_msg}{reset}"
            lines.append(clean_msg)
        if files_with_issues:
            lines.append(
                f"  {len(files_with_issues)} file(s) {issue_label}"
            )
        lines.append("")

        for file, file_issues in sorted(by_file.items()):
            lines.append(f"  {file}")
            lines.append("  " + "-" * 50)
            for issue in file_issues:
                loc = f":{issue.line}" if issue.line else ""
                color = colors.get(issue.severity, "")
                text = (
                    f"    [{issue.severity.value}]{loc} "
                    f"({issue.rule}): {issue.message}"
                )
                if color:
                    text = f"{color}{text}{reset}"
                lines.append(text)
            lines.append("")

        # -- Summary footer ----------------------------------------------------
        lines.append("=" * 70)

        error_count = len(self.errors)
        warn_count = len(self.warnings)
        info_count = len(self.infos)
        summary_parts: list[str] = []

        # Always show error count
        if error_count:
            part = f"{error_count} error(s)"
            if use_color:
                part = f"\033[91m{part}{reset}"
            summary_parts.append(part)

        if show_warnings and warn_count:
            part = f"{warn_count} warning(s)"
            if use_color:
                part = f"\033[93m{part}{reset}"
            summary_parts.append(part)

        if show_infos and info_count:
            part = f"{info_count} info(s)"
            if use_color:
                part = f"\033[94m{part}{reset}"
            summary_parts.append(part)
        elif not show_infos and info_count:
            summary_parts.append(
                f"{info_count} info(s) hidden (use -rec to show)"
            )

        lines.append(f"  {', '.join(summary_parts)}")
        lines.append("=" * 70)

        # Verdict line — accounts for strict mode and force-install
        if error_count and force_install:
            msg = (
                "  Validation has ERRORS - installation will proceed "
                "due to --force flag."
            )
            if use_color:
                msg = f"\033[93m{msg}{reset}"
            lines.append(msg)
        elif error_count:
            fail_msg = (
                "  Validation FAILED - fix ERROR issues before "
                "installation."
            )
            if use_color:
                fail_msg = f"\033[91m{fail_msg}{reset}"
            lines.append(fail_msg)
        elif strict and warn_count:
            fail_msg = (
                "  Strict mode: warnings treated as failures. "
                "Fix WARNING issues to pass."
            )
            if use_color:
                fail_msg = f"\033[93m{fail_msg}{reset}"
            lines.append(fail_msg)
        else:
            pass_msg = (
                "  No errors found. Warnings and info items "
                "are advisory."
            )
            if use_color:
                pass_msg = f"\033[92m{pass_msg}{reset}"
            lines.append(pass_msg)
        lines.append("")

        return "\n".join(lines)


# ---------------------------------------------------------------------
# AST-based parser
# ---------------------------------------------------------------------

class ClickASTParser:
    """Parses a Python file to extract Click groups, commands, options."""

    def __init__(self, filepath: Path) -> None:
        self.filepath = filepath
        self.source: str = ""

    def parse(self) -> FileAnalysis:
        analysis = FileAnalysis(
            filepath=self.filepath,
            filename=self.filepath.stem,
        )
        try:
            self.source = self.filepath.read_text(encoding="utf-8")
            tree = ast.parse(self.source, filename=str(self.filepath))
        except SyntaxError as e:
            analysis.parse_error = f"SyntaxError: {e}"
            return analysis
        except Exception as e:
            analysis.parse_error = f"Error reading file: {e}"
            return analysis

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                self._analyze_function(node, analysis)
            if isinstance(node, ast.Expr) and isinstance(
                    node.value, ast.Call
            ):
                self._check_add_command(node.value, analysis)
        return analysis

    def _analyze_function(
            self,
            func: ast.FunctionDef,
            analysis: FileAnalysis,
    ) -> None:
        is_group = False
        is_command = False
        command_name: str | None = None
        group_explicit_name: str | None = None
        is_hidden = False
        has_pass_context = False
        option_infos: list[OptionInfo] = []
        argument_names: list[str] = []

        for dec in func.decorator_list:
            info = self._parse_decorator(dec)
            if info is None:
                continue
            dec_type, dec_data = info
            if dec_type == "group":
                is_group = True
                is_hidden = dec_data.get("hidden", False)
                group_explicit_name = dec_data.get("name")
            elif dec_type == "command":
                is_command = True
                command_name = dec_data.get("name", func.name)
                is_hidden = dec_data.get("hidden", False)
            elif dec_type == "option":
                option_infos.append(dec_data)
            elif dec_type == "argument":
                if dec_data.get("name"):
                    argument_names.append(dec_data["name"])
            elif dec_type == "pass_context":
                has_pass_context = True

        if is_group:
            analysis.groups.append(GroupInfo(
                function_name=func.name,
                line=func.lineno,
                docstring=ast.get_docstring(func),
                is_hidden=is_hidden,
                explicit_name=group_explicit_name,
            ))

        if is_command:
            func_params = self._parse_function_params(func, has_pass_context)
            analysis.commands.append(CommandInfo(
                name=command_name or func.name,
                function_name=func.name,
                line=func.lineno,
                decorator_options=option_infos,
                decorator_arguments=argument_names,
                function_params=func_params,
                has_return_type=func.returns is not None,
                return_type=ast.unparse(func.returns) if func.returns else None,
                docstring=ast.get_docstring(func),
                is_hidden=is_hidden,
                has_pass_context=has_pass_context,
                has_var_kwargs=func.args.kwarg is not None,
            ))

    def _parse_decorator(
            self,
            dec: ast.expr,
    ) -> tuple[str, dict | OptionInfo] | None:
        # @click.pass_context / @click.group (no parens)
        if isinstance(dec, ast.Attribute) and isinstance(
                dec.value, ast.Name
        ):
            if dec.value.id == "click":
                if dec.attr == "pass_context":
                    return ("pass_context", {})  # noqa
                if dec.attr == "group":
                    return ("group", {})  # noqa

        # bare @pass_context
        if isinstance(dec, ast.Name) and dec.id == "pass_context":
            return ("pass_context", {})  # noqa

        # bare @group (no parens) — from a wrapper module
        if isinstance(dec, ast.Name) and dec.id in GROUP_WRAPPER_NAMES:
            return ("group", {})  # noqa

        if not isinstance(dec, ast.Call):
            return None

        func = dec.func

        # @click.pass_context()
        if (isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "click"
                and func.attr == "pass_context"):
            return ("pass_context", {})  # noqa

        # @click.group(...)
        if (isinstance(func, ast.Attribute)
                and func.attr == "group"
                and isinstance(func.value, ast.Name)
                and func.value.id == "click"):
            return ("group", {
                "hidden": self._kw_bool(dec, "hidden", False),
                "name": self._kw_str(dec, "name"),
            })

        # @group(...) — bare wrapper from a non-click module
        if isinstance(func, ast.Name) and func.id in GROUP_WRAPPER_NAMES:
            return ("group", {
                "hidden": self._kw_bool(dec, "hidden", False),
                "name": self._kw_str(dec, "name"),
            })

        # @parent.command(...)
        if isinstance(func, ast.Attribute) and func.attr == "command":
            parent = None
            if isinstance(func.value, ast.Name):
                parent = func.value.id
            return ("command", {
                "name": self._kw_str(dec, "name"),
                "parent": parent,
                "hidden": self._kw_bool(dec, "hidden", False),
            })

        # @click.option(...)
        if (isinstance(func, ast.Attribute)
                and func.attr == "option"
                and isinstance(func.value, ast.Name)
                and func.value.id == "click"):
            return ("option", self._parse_option(dec))  # noqa

        # @click.argument(...)
        if (isinstance(func, ast.Attribute)
                and func.attr == "argument"
                and isinstance(func.value, ast.Name)
                and func.value.id == "click"):
            arg_name = None
            for arg in dec.args:  # <- use 'dec'
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    arg_name = arg.value.replace("-", "_")
                    break
            return ("argument", {"name": arg_name})  # noqa

        return None

    def _parse_option(self, call: ast.Call) -> OptionInfo:
        long_name = None
        short_name = None
        dest_name = None
        required = False
        param_type = None
        multiple = False
        has_help = False
        has_callback = False

        # Click parses positional decls like this:
        #   - First long form (--foo) wins as the dest source
        #   - Subsequent long forms become CLI aliases (NOT separate dests)
        #   - Short forms (-x) are CLI aliases
        #   - A bare string (no leading dash) is an EXPLICIT dest override
        long_decls: list[str] = []
        short_decls: list[str] = []
        explicit_dest: str | None = None

        for arg in call.args:
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                val = arg.value
                if val.startswith("--"):
                    long_decls.append(val[2:])
                elif val.startswith("-") and len(val) > 1:
                    short_decls.append(val[1:])
                else:
                    # Non-flag positional => explicit dest (Click semantics)
                    explicit_dest = val

        # Canonical long name = the FIRST one (used for display + dest fallback)
        if long_decls:
            long_name = long_decls[0]
        if short_decls:
            short_name = short_decls[0]

        for kw in call.keywords:
            if kw.arg == "required" and isinstance(kw.value, ast.Constant):
                required = bool(kw.value.value)
            elif kw.arg == "type":
                param_type = ast.unparse(kw.value)
            elif kw.arg == "multiple" and isinstance(kw.value, ast.Constant):
                multiple = bool(kw.value.value)
            elif kw.arg == "help":
                has_help = True
            elif kw.arg == "callback":
                has_callback = True
                if isinstance(kw.value, ast.Name):
                    if kw.value.id in REQUIRED_CALLBACK_NAMES:
                        required = True

        # Dest precedence (matches Click):
        #   1. Explicit positional dest, if given
        #   2. First long form, normalized
        #   3. Short form (last resort)
        if explicit_dest is not None:
            dest_name = explicit_dest.replace("-", "_")
        elif long_name is not None:
            # Strip Click's flag-toggle syntax: '--shout/--no-shout' -> 'shout'
            dest_name = long_name.split("/")[0].replace("-", "_")
        elif short_name is not None:
            dest_name = short_name.replace("-", "_")

        return OptionInfo(
            long_name=long_name,
            short_name=short_name,
            dest_name=dest_name,
            required=required,
            param_type=param_type,
            multiple=multiple,
            line=call.lineno,
            has_help=has_help,
            has_callback=has_callback,
            raw_text=ast.unparse(call),
        )

    def _parse_function_params(
            self,
            func: ast.FunctionDef,
            has_pass_context: bool,
    ) -> list[ParamInfo]:
        params: list[ParamInfo] = []
        args = func.args
        num_args = len(args.args)
        num_defaults = len(args.defaults)
        first_default_idx = num_args - num_defaults

        for i, arg in enumerate(args.args):
            if arg.arg == "self":
                continue
            if has_pass_context and arg.arg in ("ctx", "context"):
                continue

            annotation = (
                ast.unparse(arg.annotation) if arg.annotation else None
            )
            has_default = i >= first_default_idx
            default_value = None
            if has_default:
                default_value = ast.unparse(
                    args.defaults[i - first_default_idx]
                )

            params.append(ParamInfo(
                name=arg.arg,
                annotation=annotation,
                has_default=has_default,
                default_value=default_value,
                line=arg.end_lineno or func.lineno,
            ))

        # Keyword-only args (after *args or *)
        for i, arg in enumerate(args.kwonlyargs):
            annotation = (
                ast.unparse(arg.annotation) if arg.annotation else None
            )
            default_node = args.kw_defaults[i] if i < len(
                args.kw_defaults) else None
            has_default = default_node is not None
            default_value = ast.unparse(default_node) if has_default else None
            params.append(ParamInfo(
                name=arg.arg,
                annotation=annotation,
                has_default=has_default,
                default_value=default_value,
                line=arg.end_lineno or func.lineno,
            ))

        # Note: *args / **kwargs are intentionally NOT counted as params,
        # since they swallow arbitrary click options and shouldn't trigger
        # PARAM_COUNT_MISMATCH. We expose a flag for the alignment check.
        return params

    def _check_add_command(
            self,
            call: ast.Call,
            analysis: FileAnalysis,
    ) -> None:
        if not (isinstance(call.func, ast.Attribute)
                and call.func.attr == "add_command"):
            return
        parent = None
        if isinstance(call.func.value, ast.Name):
            parent = call.func.value.id
        child = None
        if call.args and isinstance(call.args[0], ast.Name):
            child = call.args[0].id
        if parent and child:
            analysis.add_command_calls.append((parent, child, call.lineno))

    @staticmethod
    def _kw_str(call: ast.Call, name: str) -> str | None:
        for kw in call.keywords:
            if kw.arg == name and isinstance(kw.value, ast.Constant):
                return str(kw.value.value)
        return None

    @staticmethod
    def _kw_bool(call: ast.Call, name: str, default: bool) -> bool:
        for kw in call.keywords:
            if kw.arg == name and isinstance(kw.value, ast.Constant):
                return bool(kw.value.value)
        return default


# ---------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------

class ModuleValidator:
    """
    Validates a CLI module for modular-api compatibility.

    Core checks (always run):
      Catch issues that WILL break commands_generator.py integration.

    Extended checks (with extended_checks=True):
      Advisory code quality and convention checks.
    """

    def __init__(
            self,
            cli_path: Path,
            root_group_name: str,
            extended_checks: bool = False,
    ) -> None:
        """
        :param cli_path: directory containing CLI .py files
        :param root_group_name: root Click group name (from setup file)
        :param extended_checks: kept for API compatibility; all checks
            always run. Display filtering is controlled by
            ValidationResult.format_report(show_infos=...).
        """
        self.cli_path = cli_path
        self.root_group_name = root_group_name
        self.extended_checks = extended_checks
        self.analyses: dict[str, FileAnalysis] = {}

    def validate(self) -> ValidationResult:
        result = ValidationResult()

        # Parse all CLI files
        for filepath in sorted(self.cli_path.iterdir()):
            if filepath.suffix != ".py" or filepath.name.startswith("_"):
                continue
            analysis = ClickASTParser(filepath).parse()
            self.analyses[analysis.filename] = analysis
            result.scanned_files.append(filepath.name)

            if analysis.parse_error:
                result.issues.append(Issue(
                    severity=Severity.ERROR,
                    file=filepath.name,
                    line=None,
                    rule="PARSE_ERROR",
                    message=analysis.parse_error,
                ))

        # -- Core structural checks ----------------------------
        # These catch issues that WILL break commands_generator.py
        self._check_file_naming(result)
        self._check_hierarchy(result)
        self._check_group_naming(result)
        self._check_group_file_consistency(result)
        self._check_depth(result)
        self._check_duplicate_commands(result)
        self._check_command_naming(result)
        self._check_command_docstrings(result)
        self._check_group_docstrings(result)
        self._check_required_option_ordering(result)

        # -- Code quality checks -------------------------------
        # Always run; severity determines whether they surface by default.
        # WARNING-level findings here are real issues (e.g. param/decorator
        # mismatch -> runtime bug). INFO-level findings are advisory and
        # hidden unless --recommendations is used.
        self._check_type_hints(result)
        self._check_return_types(result)
        self._check_option_help_text(result)
        self._check_decorator_param_alignment(result)
        self._check_add_command_consistency(result)

        result.issues.sort(
            key=lambda i: (
                i.file, i.line or 0, SEVERITY_ORDER[i.severity],
            ),
        )
        return result

    def _add(
            self,
            result: ValidationResult,
            severity: Severity,
            file: str,
            line: int | None,
            rule: str,
            message: str,
    ) -> None:
        result.issues.append(Issue(
            severity=severity,
            file=file,
            line=line,
            rule=rule,
            message=message,
        ))

    # -- CORE: File naming --------------------------------------

    def _check_file_naming(self, result: ValidationResult) -> None:
        for filename, analysis in self.analyses.items():
            if filename == self.root_group_name:
                continue

            filepath_name = analysis.filepath.name

            if filename != filename.lower():
                self._add(
                    result, Severity.ERROR, filepath_name, None,
                    "FILE_NAMING_CASE",
                    f"Filename must be lowercase: '{filename}'",
                )

            segments = filename.split(GROUP_NAME_SEPARATOR)
            for seg in segments:
                if not seg:
                    self._add(
                        result, Severity.ERROR, filepath_name, None,
                        "FILE_NAMING_EMPTY_SEGMENT",
                        f"Filename has empty segment (double underscore): "
                        f"'{filename}'",
                    )
                elif not re.match(r'^[a-z][a-z0-9]*$', seg):
                    self._add(
                        result, Severity.ERROR, filepath_name, None,
                        "FILE_NAMING_SEGMENT",
                        f"Segment '{seg}' must be lowercase alphanumeric. "
                        f"commands_generator splits on "
                        f"'{GROUP_NAME_SEPARATOR}' so each segment becomes "
                        f"a group name",
                    )

    # -- CORE: Hierarchy integrity ------------------------------

    def _check_hierarchy(self, result: ValidationResult) -> None:
        all_filenames = set(self.analyses.keys())
        for filename in all_filenames:
            if filename == self.root_group_name:
                continue
            segments = filename.split(GROUP_NAME_SEPARATOR)
            for i in range(1, len(segments)):
                parent = GROUP_NAME_SEPARATOR.join(segments[:i])
                if parent not in all_filenames:
                    self._add(
                        result, Severity.ERROR, f"{filename}.py", None,
                        "HIERARCHY_MISSING_PARENT",
                        f"Parent file '{parent}.py' not found. "
                        f"Subgroup file '{filename}.py' requires its parent",
                    )

    # -- CORE: Group function names - no underscores ------------

    def _check_group_naming(self, result: ValidationResult) -> None:
        for filename, analysis in self.analyses.items():
            for group in analysis.groups:
                # Check the registered Click name (from @group(name='...') if
                # present, otherwise the function name).
                name = group.click_name
                if GROUP_NAME_SEPARATOR in name:
                    self._add(
                        result, Severity.ERROR, f"{filename}.py",
                        group.line,
                        "GROUP_NAME_UNDERSCORE",
                        f"Group '{name}' contains underscores. "
                        f"'{GROUP_NAME_SEPARATOR}' is the hierarchy "
                        f"separator in commands_generator",
                    )
                if name != name.lower():
                    self._add(
                        result, Severity.ERROR, f"{filename}.py",
                        group.line,
                        "GROUP_NAME_CASE",
                        f"Group name '{name}' must be lowercase",
                    )

    # -- CORE: Group function must match last filename segment --

    def _check_group_file_consistency(
            self,
            result: ValidationResult,
    ) -> None:
        """
        commands_generator._get_group_from_module() iterates dir(module)
        looking for a Group where obj.name == group_name. group_name is
        the LAST segment of the filename. If no match -> returns None ->
        group metadata (description, hidden, deprecation) is silently lost.
        """
        for filename, analysis in self.analyses.items():
            if filename == self.root_group_name:
                continue

            segments = filename.split(GROUP_NAME_SEPARATOR)
            expected = segments[-1]
            group_names = [g.click_name for g in analysis.groups]

            if not group_names:
                if len(segments) > 1 and analysis.commands:
                    self._add(
                        result, Severity.WARNING, f"{filename}.py", None,
                        "GROUP_FUNCTION_MISSING",
                        f"Subgroup file '{filename}.py' has commands "
                        f"but no @click.group() definition. Expected "
                        f"group function named '{expected}'",
                    )
                continue

            if expected not in group_names:
                self._add(
                    result, Severity.ERROR, f"{filename}.py", None,
                    "GROUP_FUNCTION_MISMATCH",
                    f"_get_group_from_module() will look for group named "
                    f"'{expected}' but file defines {group_names}. This "
                    f"will cause missing group metadata",
                )

    # -- CORE: Depth limit --------------------------------------

    def _check_depth(self, result: ValidationResult) -> None:
        """
        commands_generator.generate_valid_commands() nesting logic:
          - depth 1: body[group_name]
          - depth 2: body[seg0]['body'][group_name]
          - depth 3: body[seg0]['body'][seg1]['body'][group_name]

        Depth > 3: only [0] and [1] are used - intermediate parents
        are skipped, producing incorrect JSON structure.
        """
        for filename in self.analyses:
            if filename == self.root_group_name:
                continue
            segments = filename.split(GROUP_NAME_SEPARATOR)
            if len(segments) > MAX_GROUP_DEPTH:
                self._add(
                    result, Severity.ERROR, f"{filename}.py", None,
                    "MODULAR_API_DEPTH",
                    f"File has {len(segments)} hierarchy levels "
                    f"(segments: {segments}). commands_generator only "
                    f"supports up to {MAX_GROUP_DEPTH}. Intermediate "
                    f"parents will be silently skipped",
                )

    # -- CORE: No duplicate command names per file --------------

    def _check_duplicate_commands(self, result: ValidationResult) -> None:
        for filename, analysis in self.analyses.items():
            seen: dict[str, int] = {}
            for cmd in analysis.commands:
                if cmd.name in seen:
                    self._add(
                        result, Severity.ERROR, f"{filename}.py", cmd.line,
                        "DUPLICATE_COMMAND",
                        f"Duplicate command '{cmd.name}' (first at "
                        f"line {seen[cmd.name]}). Second definition "
                        f"overwrites the first in meta JSON",
                    )
                else:
                    seen[cmd.name] = cmd.line

    # -- CORE: Command naming ----------------------------------

    def _check_command_naming(self, result: ValidationResult) -> None:
        for filename, analysis in self.analyses.items():
            for cmd in analysis.commands:
                if cmd.name != cmd.name.lower():
                    self._add(
                        result, Severity.ERROR, f"{filename}.py", cmd.line,
                        "COMMAND_NAME_CASE",
                        f"Command name '{cmd.name}' must be lowercase",
                    )
                if not re.match(r'^[a-z][a-z0-9_]*$', cmd.name):
                    self._add(
                        result, Severity.WARNING, f"{filename}.py", cmd.line,
                        "COMMAND_NAME_CHARS",
                        f"Command name '{cmd.name}' contains unusual "
                        f"characters. Expected lowercase alphanumeric "
                        f"with underscores",
                    )

    # -- CORE: Command docstrings -------------------------------

    def _check_command_docstrings(self, result: ValidationResult) -> None:
        """commands_generator parses docstrings as command descriptions.
        Missing docstrings result in description=None in meta JSON."""
        for filename, analysis in self.analyses.items():
            for cmd in analysis.commands:
                if not cmd.docstring:
                    self._add(
                        result, Severity.WARNING, f"{filename}.py", cmd.line,
                        "MISSING_COMMAND_DOCSTRING",
                        f"Command '{cmd.name}' has no docstring. "
                        f"commands_generator uses docstrings as "
                        f"descriptions in meta JSON",
                    )

    # -- CORE: Group docstrings ---------------------------------

    def _check_group_docstrings(self, result: ValidationResult) -> None:
        for filename, analysis in self.analyses.items():
            for group in analysis.groups:
                if not group.docstring:
                    self._add(
                        result, Severity.WARNING, f"{filename}.py",
                        group.line,
                        "MISSING_GROUP_DOCSTRING",
                        f"Group '{group.function_name}' has no "
                        f"docstring",
                    )

    # -- CORE: Required options before optional -----------------

    def _check_required_option_ordering(
            self,
            result: ValidationResult,
    ) -> None:
        for filename, analysis in self.analyses.items():
            for cmd in analysis.commands:
                seen_optional = False
                first_optional: str | None = None
                for opt in cmd.decorator_options:
                    if not opt.required:
                        if not seen_optional:
                            first_optional = opt.long_name or "?"
                        seen_optional = True
                    elif seen_optional:
                        self._add(
                            result, Severity.INFO, f"{filename}.py",
                            opt.line,
                            "DECORATOR_PARAM_ORDER",
                            f"Command '{cmd.name}': required option "
                            f"'--{opt.long_name}' after optional "
                            f"'--{first_optional}'",
                        )

    # -- EXTENDED: Type hints -----------------------------------

    def _check_type_hints(self, result: ValidationResult) -> None:
        for filename, analysis in self.analyses.items():
            for cmd in analysis.commands:
                for param in cmd.function_params:
                    if param.annotation is None:
                        self._add(
                            result, Severity.INFO, f"{filename}.py",
                            param.line,
                            "MISSING_TYPE_HINT",
                            f"Command '{cmd.name}': parameter "
                            f"'{param.name}' has no type hint",
                        )

    # -- EXTENDED: Return types ---------------------------------

    def _check_return_types(self, result: ValidationResult) -> None:
        for filename, analysis in self.analyses.items():
            for cmd in analysis.commands:
                if not cmd.has_return_type:
                    self._add(
                        result, Severity.INFO, f"{filename}.py",
                        cmd.line,
                        "MISSING_RETURN_TYPE",
                        f"Command '{cmd.name}': missing return type "
                        f"annotation",
                    )

    # -- EXTENDED: Option help text -----------------------------

    def _check_option_help_text(self, result: ValidationResult) -> None:
        for filename, analysis in self.analyses.items():
            for cmd in analysis.commands:
                for opt in cmd.decorator_options:
                    if not opt.has_help:
                        self._add(
                            result, Severity.INFO, f"{filename}.py",
                            opt.line,
                            "MISSING_OPTION_HELP",
                            f"Command '{cmd.name}': option "
                            f"'--{opt.long_name}' has no help text",
                        )

    # -- EXTENDED: Decorator - function param alignment ---------

    def _check_decorator_param_alignment(
            self,
            result: ValidationResult,
    ) -> None:
        for filename, analysis in self.analyses.items():
            for cmd in analysis.commands:
                options = cmd.decorator_options
                params = cmd.function_params

                decorator_dests: list[str] = []
                for opt in options:
                    dest = opt.dest_name or opt.long_name
                    if dest:
                        decorator_dests.append(dest.replace("-", "_"))
                # arguments also become function params in click
                for arg_name in cmd.decorator_arguments:
                    decorator_dests.append(arg_name)

                param_names = [p.name for p in params]

                total_decorators = len(options) + len(cmd.decorator_arguments)
                # If function uses **kwargs, it can absorb any extra decorator
                # params - count mismatch is not a real bug.
                if (total_decorators != len(param_names)
                        and not cmd.has_var_kwargs):
                    # Decorators > params: real bug - Click will raise
                    # TypeError at runtime ('option' has no matching param).
                    # Params > decorators: usually a custom decorator
                    # (e.g. @cli_response) injects extra params at call
                    # time. Demote to INFO since it's often a false positive.
                    if total_decorators > len(param_names):
                        severity = Severity.WARNING
                    else:
                        severity = Severity.INFO
                    self._add(
                        result, severity, f"{filename}.py", cmd.line,
                        "PARAM_COUNT_MISMATCH",
                        f"Command '{cmd.name}': {total_decorators} "
                        f"decorator param(s) ({len(options)} option(s), "
                        f"{len(cmd.decorator_arguments)} argument(s)) but "
                        f"{len(param_names)} function parameter(s)",
                    )

                decorator_set = set(decorator_dests)
                param_set = set(param_names)

                only_in_decorators = sorted(decorator_set - param_set)
                only_in_params = sorted(param_set - decorator_set)

                # **kwargs absorbs unmatched decorator dests, so don't warn
                if only_in_decorators and not cmd.has_var_kwargs:
                    self._add(
                        result, Severity.WARNING, f"{filename}.py", cmd.line,
                        "PARAM_UNMATCHED_OPTIONS",
                        f"Command '{cmd.name}': decorator dest(s) "
                        f"[{', '.join(only_in_decorators)}] have no "
                        f"matching function parameter",
                    )
                if only_in_params:
                    self._add(
                        result, Severity.INFO, f"{filename}.py", cmd.line,
                        "PARAM_UNMATCHED_PARAMS",
                        f"Command '{cmd.name}': function param(s) "
                        f"[{', '.join(only_in_params)}] have no "
                        f"matching @click.option/@click.argument",
                    )

                common = decorator_set & param_set
                opt_order = [n for n in decorator_dests if n in common]
                par_order = [n for n in param_names if n in common]
                if opt_order and opt_order != par_order:
                    self._add(
                        result, Severity.INFO, f"{filename}.py", cmd.line,
                        "PARAM_ORDER_MISMATCH",
                        f"Command '{cmd.name}': decorator order "
                        f"[{', '.join(opt_order)}] differs from "
                        f"function order [{', '.join(par_order)}]",
                    )

    # -- EXTENDED: add_command consistency ----------------------

    def _check_add_command_consistency(
            self,
            result: ValidationResult,
    ) -> None:
        for filename, analysis in self.analyses.items():
            group_names = {g.function_name for g in analysis.groups}
            for parent, child, line in analysis.add_command_calls:
                if parent not in group_names:
                    continue
                # Root group children live at top level (e.g. profile.py),
                # not prefixed (e.g. stm_profile.py). Subgroup children
                # are prefixed with the parent filename.
                if filename == self.root_group_name:
                    expected = child
                else:
                    expected = f"{filename}_{child}"
                if expected not in self.analyses:
                    self._add(
                        result, Severity.INFO, f"{filename}.py", line,
                        "ADD_COMMAND_NO_FILE",
                        f"'{parent}.add_command({child})' - no file "
                        f"'{expected}.py' found. Fine if '{child}' is "
                        f"imported from another module",
                    )


# ---------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------

def resolve_root_group_name(setup_file_path: str | Path) -> str:
    """
    Read a setup file (pyproject.toml, setup.cfg, setup.py) and resolve
    the root Click group name from console_scripts / project.scripts.

    Thin wrapper around commands_generator.extract_root_group_name.
    """
    with open(setup_file_path) as f:
        content = f.readlines()
    return extract_root_group_name(file_content=content)


def validate_module_cli(
        cli_path: str | Path,
        root_group_name: str,
        extended_checks: bool = False,
) -> ValidationResult:
    """
    Validate a CLI module's structure for modular-api compatibility.

    :param cli_path: Directory containing CLI .py files
    :param root_group_name: Root Click group name (from setup file)
    :param extended_checks: Include advisory code quality checks
    :return: ValidationResult with all issues
    """
    cli_path = Path(cli_path)
    if not cli_path.is_dir():
        result = ValidationResult()
        result.issues.append(Issue(
            severity=Severity.ERROR,
            file=str(cli_path),
            line=None,
            rule="INVALID_PATH",
            message=f"CLI path '{cli_path}' is not a directory",
        ))
        return result

    validator = ModuleValidator(
        cli_path=cli_path,
        root_group_name=root_group_name,
        extended_checks=extended_checks,
    )
    result = validator.validate()
    return result
