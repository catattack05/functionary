import click

from .python import py_parse


def _read_file(path):
    """
    Helper function for parse that
    gets function data from file

    Args:
        path: the path to file
    Returns:
        function_data: content of file as string
    Raises:
        ClickException if file not found or cannot be accessed
    """
    try:
        with open(path, "r") as func_file:
            function_data = func_file.read()
    except FileNotFoundError:
        raise click.ClickException("Could not find functions.py")
    except PermissionError:
        raise click.ClickException("Did not have permission to access functions.py")
    return function_data


def parse(language, path):
    """
    Parses the function implementation file and
    returns a list of function definitions

    Args:
        language: the language of the function file
        path: the location of the function file

    Returns:
        parsed_list: list of dictionaries representing functions

    Raises:
        ClickException if unsupported language
    """
    if "python" == language:
        parsed_list = py_parse(_read_file(path + "/functions.py"))
    else:
        raise click.ClickException(f"Support for {language} not currently implemented")

    return parsed_list
