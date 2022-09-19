import click

from .python import py_parse


def parse(language, path):
    """
    Parses a function file
    and returns a list of dictionaries

    Args:
        language: the language of the function file
        path: the location of the function file

    Returns:
        parsed_list: list of dictionaries representing functions

    Raises:
        ClickException if unsupported language
    """
    if "python" == language:
        parsed_list = py_parse(path)
    else:
        raise click.ClickException(f"Support for {language} not currently implemented")

    return parsed_list
