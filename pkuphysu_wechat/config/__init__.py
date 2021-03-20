import os.path

from dynaconf import Dynaconf

settings = Dynaconf(
    environments=True,
    env="FLASK_ENV",
    envvar_prefix="DYNACONF",
    settings_files=[
        os.path.join(os.path.dirname(__file__), filename)
        for filename in ("settings.toml", ".secrets.toml")
    ],
)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load this files in the order.
