from pathlib import Path

import click
from dotenv import dotenv_values


def save_config_value(parameter, value):
    functionary_dir = Path.home() / ".functionary"
    if not functionary_dir.exists():
        functionary_dir.mkdir()

    config_file = functionary_dir / "config"

    # if the parameter does not exist already, write it
    if parameter not in dotenv_values(config_file):
        with config_file.open("a") as f:
            f.write(f"{parameter}={value}\n")

    else:  # if the parameter already has a value, overwrite it
        with open(config_file, "r", encoding="utf-8") as file:
            data = file.readlines()
            index = -1
            for line in data:
                if parameter in line:
                    index = data.index(line)
            data[index] = f"{parameter}={value}\n"
        with open(config_file, "w", encoding="utf-8") as file:
            file.writelines(data)


def get_config_value(parameter):
    try:
        config_file = Path.home() / ".functionary" / "config"

        config = {
            **dotenv_values(str(config_file)),
        }
        return config[parameter]
    # if path not found or key not found, raise error
    except KeyError:
        raise click.ClickException("Could not find config parameter")
