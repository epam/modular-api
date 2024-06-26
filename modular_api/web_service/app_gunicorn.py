from gunicorn.app.base import BaseApplication
from typing import Callable


class ModularAdminGunicornApplication(BaseApplication):
    def __init__(self, app: Callable, options: dict | None = None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        return self.application
