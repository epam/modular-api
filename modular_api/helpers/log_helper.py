import os # Must set env vars before importing ddtrace
os.environ["DD_TRACE_LOGGING_ENABLED"] = "true"
import ddtrace.auto # noqa
import logging
import logging.config
import sys
from pathlib import Path

from modular_api.helpers.constants import (
    API_LOG_FILE_NAME,
    CLI_LOG_FILE_NAME,
    Env,
    LOGS_FORMAT
)

# ============================================================
# IMPORTANT: Import modular_sdk BEFORE configuring logging
# This ensures modular_sdk's NullHandler config runs first,
# then our config overwrites it.
# ============================================================
try:
    import modular_sdk.commons.log_helper  # noqa: F401 - Force modular_sdk logging init
except ImportError:
    pass  # modular_sdk not installed

# Environment variable name for modular_sdk logging
MODULAR_SDK_LOG_LEVEL_ENV = 'MODULAR_SDK_LOG_LEVEL'


def _reconfigure_std_streams_to_utf8() -> None:
    """
    Force stdout/stderr to UTF-8 so that non-ASCII characters (e.g. '≤')
    do not raise UnicodeEncodeError on consoles using legacy encodings
    such as Windows cp1252.

    'backslashreplace' guarantees that even un-encodable characters are
    rendered as escapes instead of crashing the process.
    """
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding='utf-8', errors='backslashreplace')
        except (AttributeError, ValueError):
            # Stream is not a reconfigurable io.TextIOWrapper (e.g. it was
            # replaced by a test capture / IDE redirect / detached stream).
            # Non-fatal: Utf8StreamHandler below is the real safety net.
            # Do NOT log here - logging is not configured yet at this point.
            pass


# Reconfigure as early as possible (before any handler writes)
_reconfigure_std_streams_to_utf8()


class Utf8StreamHandler(logging.StreamHandler):
    """
    StreamHandler that guarantees UTF-8 output and never raises on
    encoding errors. Falls back to 'backslashreplace' so a bad character
    can never crash the logging subsystem.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            stream = self.stream
            try:
                stream.write(msg + self.terminator)
            except UnicodeEncodeError:
                # Last-resort safe encoding for legacy consoles
                safe = (msg + self.terminator).encode(
                    'utf-8', 'backslashreplace'
                ).decode('utf-8', 'backslashreplace')
                stream.write(safe)
            self.flush()
        except RecursionError:  # See logging.Handler.emit
            raise
        except Exception:  # noqa
            self.handleError(record)


def _get_logs_path() -> Path:
    """
    Returns logs that exists
    :return:
    """
    path = os.getenv(Env.LOG_PATH, Env.LOG_PATH.default)
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        default = Env.LOG_PATH.default
        logging.getLogger().warning(
            f'Cannot access {path}. Writing logs to {default}'
        )
        path = default
        os.makedirs(path, exist_ok=True)
    return Path(path).resolve()


def _get_modular_sdk_log_level() -> str | None:
    """
    Returns modular_sdk log level if env var is set and valid, None otherwise.
    If env var is not set - modular_sdk logging is disabled.
    If env var is set - modular_sdk logging is enabled with specified level.
    """
    level = os.getenv(MODULAR_SDK_LOG_LEVEL_ENV)
    if level is None:
        return None
    level = level.upper()
    if level not in {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}:
        logging.getLogger().warning(
            f"Invalid {MODULAR_SDK_LOG_LEVEL_ENV}='{level}'. "
            f"Must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL. "
            f"Defaulting to DEBUG"
        )
        return 'DEBUG'
    return level


LOGS_PATH = _get_logs_path()
API_LOGS_FILE = LOGS_PATH / API_LOG_FILE_NAME
CLI_LOGS_FILE = LOGS_PATH / CLI_LOG_FILE_NAME

# Build logging config
logging_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        # 'console_formatter': {
        #     'format': LOGS_FORMAT
        # },
        'file_formatter': {
            'format': LOGS_FORMAT
        },
        'init_formatter': {
            'format': '[%(levelname)s] %(message)s'
        }
    },
    'handlers': {
        # 'console_handler': {
        #     'class': 'logging.StreamHandler',
        #     'formatter': 'console_formatter'
        # },
        'api_file_handler': {
            'class': 'logging.FileHandler',
            'filename': API_LOGS_FILE,
            'formatter': 'file_formatter',
            'encoding': 'utf-8',  # <-- UTF-8 log files
        },
        'cli_file_handler': {
            'class': 'logging.FileHandler',
            'filename': CLI_LOGS_FILE,
            'formatter': 'file_formatter',
            'encoding': 'utf-8',  # <-- UTF-8 log files
        },
        'init_handler': {
            # UTF-8 safe console handler (never crashes on bad chars).
            # Use '()' with the class object (NOT a dotted string) to avoid a
            # circular import during dictConfig: this module is still being
            # imported when dictConfig() runs at the bottom of this file, so
            # resolving the string
            # 'modular_api.helpers.log_helper.Utf8StreamHandler' would fail
            # with: "cannot access submodule 'log_helper' ... circular import".
            '()': Utf8StreamHandler,
            'formatter': 'init_formatter'
        }
    },
    'loggers': {
        'modular_api': {
            'level': os.getenv(Env.SERVER_LOG_LEVEL,
                               Env.SERVER_LOG_LEVEL.default),
            'handlers': ['api_file_handler']  # + 'console_handler'
        },
        'modular_api_cli': {
            'level': os.getenv(Env.CLI_LOG_LEVEL, Env.CLI_LOG_LEVEL.default),
            'handlers': ['cli_file_handler']
        },
        'init': {
            'level': 'DEBUG',
            'handlers': ['init_handler']
        }
    }
}

# Conditionally add modular_sdk logger only if env var is set
_modular_sdk_level = _get_modular_sdk_log_level()
if _modular_sdk_level:
    logging_config['loggers']['modular_sdk'] = {
        'level': _modular_sdk_level,
        'handlers': ['api_file_handler'],
        'propagate': False,
    }

# This runs AFTER modular_sdk's log_helper, so it OVERWRITES the NullHandler
logging.config.dictConfig(logging_config)


def get_logger(name: str, level=None) -> logging.Logger:
    log = logging.getLogger(name)
    if level:
        log.setLevel(level)
    return log


def init_console_handler():
    # todo, since modular_api_cli module reuses a lot of code from
    #  modular_api module we cannot add logging.StreamHandler to modular_api.*
    #  logger because than each cli command will output a lot of junk. So,
    #  I think we should not use modules from modular_api in CLI. But
    #  for now this kludge: add StreamHandler only of server is running
    #  (this function is used only when user stars the server)
    h = Utf8StreamHandler()  # <-- UTF-8 safe
    h.setFormatter(logging.Formatter(LOGS_FORMAT))
    logging.getLogger('modular_api').addHandler(h)
