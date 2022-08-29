from pathlib import Path

import click
from dotenv import get_key, set_key


def save_config_value(key, value):
    """
    Save configuration key and value to config file. If key is already present,
    overwrite the current value.

    Args:
        key: the configuration parameter to set
        value: the value to set the configutation parameter to

    Returns:
        None

    Raises:
        ClickException: Received a PermissionError when opening config file
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
        raise click.ClickException(f"Failed to open {config_file}: Permission Denied")


def get_config_value(key, raise_exception=False):
    """
    Retrieve the value associated with a key from the config file

    Args:
        key: the configuration parameter to retrieve the value of

    Returns:
        Value associated with that key as a string

    Raises:
        ClickException: Received PermissionError when opening file or no configuration
        parameter matching the provided key exists
    """
    try:
        config_file = Path.home() / ".functionary" / "config"
        value = get_key(config_file, key)
        if value is None:
            if raise_exception is False:
                return None
            else:
                raise click.ClickException(f"Could not find value for {key}")
        else:
            return value
    # if path not found or key not found, raise error
    except PermissionError:
        raise click.ClickException(f"Failed to open {config_file}: Permission Denied")
