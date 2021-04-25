import os.path
from logging.config import dictConfig

from dynaconf import Dynaconf

__all__ = ["settings"]

settings = Dynaconf(
    environments=True,
    envvar_prefix="DYNACONF",
    settings_files=[
        os.path.join(os.path.dirname(__file__), filename)
        for filename in ("settings.toml", ".secrets.toml")
    ],
)

dictConfig(settings.logging)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load this files in the order.
