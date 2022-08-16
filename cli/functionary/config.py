from pathlib import Path

import click
from dotenv import get_key, set_key


def save_config_value(key, value):
    functionary_dir = Path.home() / ".functionary"
    if not functionary_dir.exists():
        functionary_dir.mkdir()

    config_file = functionary_dir / "config"
    set_key(
        config_file,
        key,
        value,
        quote_mode="always",
        export=False,
        encoding="utf-8",
    )


def get_config_value(key):
    try:
        config_file = Path.home() / ".functionary" / "config"
        value = get_key(config_file, key)
        return value
    # if path not found or key not found, raise error
    except KeyError:
        raise click.ClickException("Could not find config parameter")
