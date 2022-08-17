from pathlib import Path

import click
from dotenv import get_key, set_key


def save_config_value(key, value):
    """
    Save configuration key and value to config file. If key is already present,
    overwrite the current value.

    Args:
        key and value to be stored as strings

    Returns:
        Nothing

    Raises:
        ClickException from PermissionError if cannot read config file
    """
    try:
        functionary_dir = Path.home() / ".functionary"
        if not functionary_dir.exists():
            functionary_dir.mkdir()

        config_file = functionary_dir / "config"
        set_key(
            config_file,
            key,
            value,
        )
    except PermissionError:
        raise click.ClickException("Config file present, but could not be read")


def get_config_value(key):
    """
    Retrieve the value associated with a key from the config file

    Args:
        The key to be found

    Returns:
        Value associated with that key as a string

    Raises:
        ClickException if value returned is None (key doesn't exist in file)
        ClickException from PermissionError if file cannot be read
    """
    try:
        config_file = Path.home() / ".functionary" / "config"
        value = get_key(config_file, key)
        if value is None:
            raise click.ClickException(f"Could not find value for {key}")
        else:
            return value
    # if path not found or key not found, raise error
    except PermissionError:
        raise click.ClickException("Config file present, but could not be read")
