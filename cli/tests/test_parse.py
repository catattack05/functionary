from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from functionary.package import genschema


@pytest.fixture(autouse=True)
def py_package_yaml(fakefs):
    """
    Pytest fixture to create package.yaml for tests

    Args:
        fakefs: pytest fixture that holds test files
    Returns:
        None, but does create package.yaml in fakefs/test
    """
    path = str(Path.home() / "parse-test" / "package.yaml")
    fakefs.create_file(path)
    filedata = {
        "version": 1.0,
        "package": {"name": "test", "language": "python", "functions": []},
    }
    with open(str(path), "w") as yaml_file:
        yaml.dump(filedata, yaml_file, sort_keys=False)


def _write_function_py_file(fakefs, arg_str):
    """
    Helper function for tests that writes the python function file to test.

    Args:
        fakefs: pytest fixture that holds test files
        arg_str: the arg we want to test
    Returns:
        None, but does create functions.py with a function in fakefs/test
    """

    func = (
        "from datetime import date, datetime\n"
        + "def test("
        + arg_str
        + "):\n"
        + "    pass\n"
        + "def test2():"
        + "    pass"
    )
    path = str(Path.home() / "parse-test" / "functions.py")
    fakefs.create_file(path)

    with open(path, "w") as file_:
        file_.write(func)


def _run_genschema(fakefs):
    """
    Helper function for tests that simulates the genschema command using
    CliRunner

    Args:
        fakefs: pytest object that points to where test files are stored

    Returns:
        func_dict: Python list of dictionaries representing Python functions
    """

    runner = CliRunner()
    runner.invoke(genschema, [str(Path.home() / "parse-test")])

    path = Path.home() / "parse-test" / "package.yaml"

    with open(str(path), "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
    return data


def test_parser_finds_function_name(fakefs):
    """Parser should correctly detect multiple functions"""
    arg = ""
    _write_function_py_file(fakefs, arg)
    dict = _run_genschema(fakefs)

    functions = dict["package"]["functions"]

    assert functions[0]["name"] == "test"
    assert functions[1]["name"] == "test2"


def test_correct_dict_parse(fakefs):
    """Parser should auto-gen dict type"""
    arg = "param: dict = {'a':'b'},"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param = func_dict["parameters"][0]

    assert test_param["name"] == "param"
    assert test_param["type"] == "json"
    assert test_param["required"] is False


def test_correct_string_parse(fakefs):
    """Parser should auto-gen str arg's type and default"""
    arg = "param: str = '5',"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param = func_dict["parameters"][0]

    assert test_param["name"] == "param"
    assert test_param["type"] == "string"
    assert test_param["required"] is False
    assert test_param["default"] == "5"


def test_correct_int_parse(fakefs):
    """Parser should auto-gen int arg's type and default"""
    arg = "param: int = 5,"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param = func_dict["parameters"][0]

    assert test_param["name"] == "param"
    assert test_param["type"] == "integer"
    assert test_param["required"] is False
    assert test_param["default"] == 5


def test_correct_float_parse(fakefs):
    """Parser should auto-gen float arg's type and default"""
    arg = "param: float = 2.0"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param = func_dict["parameters"][0]

    assert test_param["name"] == "param"
    assert test_param["type"] == "float"
    assert test_param["required"] is False
    assert test_param["default"] == 2.0


def test_correct_bool_parse(fakefs):
    """Parser should auto-gen bool arg's type and default"""
    arg = "param: bool = True"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param = func_dict["parameters"][0]

    assert test_param["name"] == "param"
    assert test_param["type"] == "boolean"
    assert test_param["required"] is False
    assert test_param["default"] == "True"


def test_correct_date_parse(fakefs):
    """Parser should auto-gen dat arg's type and default"""
    arg = "param: date = date(11, 11, 11)"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param = func_dict["parameters"][0]

    assert test_param["name"] == "param"
    assert test_param["type"] == "date"
    assert test_param["required"] is False
    assert test_param["default"] == "0011-11-11"


def test_correct_datetime_parse(fakefs):
    """Parser should auto-gen datetime arg's type and default"""
    arg = "param: datetime = datetime(11, 11, 11)"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param = func_dict["parameters"][0]

    assert test_param["name"] == "param"
    assert test_param["type"] == "datetime"
    assert test_param["required"] is False
    assert test_param["default"] == "0011-11-11 00:00:00"


def test_no_type_provided(fakefs):
    """
    Parser should not assign type or default if none given,
    but should still fill out the default if one exists
    """
    arg = "no_type, no_type_with_def = 2"
    _write_function_py_file(fakefs, arg)
    func_dict = _run_genschema(fakefs)["package"]["functions"][0]

    test_param1 = func_dict["parameters"][0]
    test_param2 = func_dict["parameters"][1]

    assert test_param1["name"] == "no_type"
    assert "type" not in test_param1.keys()
    assert "default" not in test_param1.keys()
    assert test_param1["required"] is True

    assert test_param2["name"] == "no_type_with_def"
    assert "type" not in test_param2.keys()
    assert test_param2["default"] == 2
    assert test_param2["required"] is False


def test_unsupported_type_provided(fakefs):
    """Parser should not assign type if it can read a type
    that isn't supported by functionary. However, if a default exists,
    'required' should still be false and the default should still be set.
    """
    arg = "invalid_type: test, invalid_type2: test = 2,"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param1 = func_dict["parameters"][0]
    test_param2 = func_dict["parameters"][1]

    assert test_param1["name"] == "invalid_type"
    assert "type" not in test_param1.keys()
    assert "default" not in test_param1.keys()
    assert test_param1["required"] is True

    assert test_param2["name"] == "invalid_type2"
    assert "type" not in test_param2.keys()
    assert test_param2["required"] is False
    assert test_param2["default"] == 2


def test_parser_cannot_parse_type_provided(fakefs):
    """Parser should not assign type if it cannot parse the type given.
    However, 'required' should still be set to 'False' and the default
    set if a a default exists.
    """
    arg = "unparsable_type: test(), unparsable_type2: test() = 2,"
    _write_function_py_file(fakefs, arg)

    func_dict = _run_genschema(fakefs)["package"]["functions"][0]
    test_param1 = func_dict["parameters"][0]
    test_param2 = func_dict["parameters"][1]

    assert test_param1["name"] == "unparsable_type"
    assert "type" not in test_param1.keys()
    assert "default" not in test_param1.keys()
    assert test_param1["required"] is True

    assert test_param2["name"] == "unparsable_type2"
    assert "type" not in test_param2.keys()
    assert test_param2["required"] is False
    assert test_param2["default"] == 2
