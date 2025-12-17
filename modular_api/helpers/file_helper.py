from typing import Any, NoReturn
import json

from modular_api.helpers.exceptions import ModularApiConfigurationException


def open_json_file(
        file_path: str,
        error_message: str | None = None,
) -> Any:
    """
    Open and parse a JSON file.

    Args:
        file_path: Path to the JSON file
        error_message: Optional custom error message (overrides specific messages)

    Returns:
        Parsed JSON data (dict, list, str, int, float, bool, or None)

    Raises:
        ModularApiConfigurationException: If file cannot be opened or parsed
    """
    def raise_config_exception(
            msg: str,
            exception: Exception,
    ) -> NoReturn:
        final_msg = error_message or msg
        raise ModularApiConfigurationException(final_msg) from exception

    try:
        with open(file_path) as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        message = (
            f"Failed to read JSON file {file_path!r}. "
            f"Syntax error at line {e.lineno}, column {e.colno}: {e.msg}. "
            f"Check for missing quotes, commas, or braces."
        )
        raise_config_exception(
            msg=message,
            exception=e,
        )
    except FileNotFoundError as e:
        message = (
            f"The file {file_path!r} was not found. Please check the file path."
        )
        raise_config_exception(
            msg=message,
            exception=e,
        )
    except PermissionError as e:
        raise_config_exception(
            msg=f"Permission denied when trying to read {file_path!r}.",
            exception=e,
        )
    except Exception as e:
        raise_config_exception(
            msg="Error occurred while opening file.",
            exception=e,
        )
