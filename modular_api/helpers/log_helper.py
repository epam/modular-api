import os # Must set env vars before importing ddtrace
os.environ["DD_TRACE_LOGGING_ENABLED"] = "true"
import ddtrace.auto # noqa
import logging
import logging.config
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
        },
        'cli_file_handler': {
            'class': 'logging.FileHandler',
            'filename': CLI_LOGS_FILE,
            'formatter': 'file_formatter',
        },
        'init_handler': {
            'class': 'logging.StreamHandler',
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
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter(LOGS_FORMAT))
    logging.getLogger('modular_api').addHandler(h)
