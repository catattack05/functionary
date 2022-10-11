import ast
import datetime

import click

type_map = {
    "str": "string",
    "int": "integer",
    "float": "float",
    "bool": "boolean",
    "date": "date",
    "datetime": "datetime",
    "json": "json",
    "dict": "json",
}


def _retrieve_function_nodes(data):
    """
    Helper function for py_parse to retrieve
    ast function nodes.

    Args:
        data: string representing python code
    Returns:
        function_nodes: list containing top level
        ast function nodes
    Raises:
        ClickException if incorrect python syntax in data
    """
    function_nodes = []
    try:
        for node in ast.parse(data).body:
            if isinstance(node, ast.FunctionDef):
                function_nodes.append(node)
    except SyntaxError:
        raise click.ClickException(
            "Syntax error in function.py file. Please correct code and try again"
        )
    return function_nodes


def _create_argument_list(node):
    """
    Helper function for py_parse to create
    a list of dictionaries representing function
    args. If parser cannot detect arg type, alert
    user that they must manually fill out package.yaml

    Args:
        node: ast node representing function
    Returns:
        arg_list: list of dictionaries containing arg info
    """
    args = node.args.args
    arg_list = []

    for arg in args:
        arg_dict = {}
        arg_dict["name"] = arg.arg

        type = None
        if arg.annotation:
            try:
                if isinstance(arg.annotation, ast.Name):
                    type = arg.annotation.id
                elif isinstance(arg.annotation, ast.Attribute):
                    type = arg.annotation.attr

                if type:
                    arg_dict["type"] = type_map[type]
            except KeyError:
                type = None

        # Set as required now, will update later if needed when handling defaults
        arg_dict["required"] = True
        arg_list.append(arg_dict)

        if type is None:
            click.echo(
                f"The argument type of {arg.arg} in function {node.name} could "
                "not be parsed, was not specified, or is an unsupported type. "
                "Please update package.yaml with arg type manually prior to "
                "publishing package to ensure a successful build.\n"
            )
    return arg_list


def _assign_defaults(node, arg_list):
    """
    Helper function for py_parse. If arg in list
    has a default, fill out arg's dictionary with
    that default

    Args:
        node: ast node representing function
        arg_list: list of dictionaries representing args
    Returns:
        arg_list: list of dictionaries representing args,
        now with defaults filled out as needed
    """
    defaults = node.args.defaults

    default_start = len(arg_list) - len(defaults)
    has_default = arg_list[default_start:]
    no_default = arg_list[:default_start]

    for arg, default in zip(has_default, defaults):
        arg_default = None

        if "type" in arg.keys():
            if arg["type"] == type_map["date"] and isinstance(default, ast.Call):
                default_params = [arg.value for arg in default.args]
                arg_default = str(datetime.date(*default_params))
            elif arg["type"] == type_map["datetime"] and isinstance(default, ast.Call):
                default_params = [arg.value for arg in default.args]
                arg_default = str(datetime.datetime(*default_params))
            elif arg["type"] == type_map["dict"]:
                click.echo(
                    "Automatic function generation for default dictionary"
                    " not currently implemented. Please add dictionary"
                    " default manually\n"
                )
            elif arg["type"] == type_map["bool"]:
                arg_default = str(default.value)
            elif hasattr(default, "value"):
                arg_default = default.value

        elif hasattr(default, "value"):
            arg_default = default.value

        if arg_default:
            arg["default"] = arg_default
        else:
            click.echo(
                f"Cannot parse default for {arg['name']} in {node.name}. "
                "Please update package.yaml with default manually prior to "
                "publishing package to ensure an accurate build.\n"
            )

        arg["required"] = False

    arg_list = no_default + has_default
    return arg_list


def py_parse(filedata):
    """
    Parses a python file
    and returns a list of dictionaries representing
    each function in the file

    Args:
        path: the location of the function file

    Returns:
        parsed_list: list of dictionaries representing functions

    Raises:
        ClickException if issue accessing file, syntax issue
        in file or function arg type not valid
    """

    function_nodes = _retrieve_function_nodes(filedata)

    parsed_list = []

    for node in function_nodes:
        function_dict = {}
        function_dict["name"] = node.name

        if ast.get_docstring(node):
            function_dict["description"] = ast.get_docstring(node)

        arg_list = _create_argument_list(node)

        if arg_list:
            arg_list = _assign_defaults(node, arg_list)

        function_dict["parameters"] = arg_list
        parsed_list.append(function_dict)

    return parsed_list
