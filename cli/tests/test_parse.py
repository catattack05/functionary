import pytest
import yaml
from click.testing import CliRunner

from functionary.package import genschema


@pytest.fixture(autouse=True)
def py_package_yaml(tmp_path):
    """
    Pytest fixture to create package.yaml for tests

    Args:
        tmp_path: pytest object that creates temp path for tests
    Returns:
        None, but does create package.yaml in tmp_path/sub
    """
    d = tmp_path / "sub"
    d.mkdir()
    yaml_file = d / "package.yaml"
    filedata = {
        "version": 1.0,
        "package": {"name": "test", "language": "python", "functions": []},
    }
    with open(str(d) + "/package.yaml", "w") as yaml_file:
        yaml.dump(filedata, yaml_file, sort_keys=False)


def _write_function_py_file(tmp_path, arg_str):
    """
    Helper function for tests that writes the python function file to test.

    Args:
        tmp_path: pytest object that creates temp path for tests
        py_package_yaml: the pytest fixture representing the yaml
        arg_str: the arg we want to test
    Returns:
        None, but does create functions.py with a function in tmp_path/sub
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
    func_file = tmp_path / "sub" / "functions.py"
    func_file.write_text(func)


def _run_genschema(tmp_path):
    """
    Helper function for tests that simulates the genschema command using
    CliRunner

    Args:
        tmp_path: pytest object that points to where test files are stored

    Returns:
        func_dict: Python list of dictionaries representing Python functions
    """

    runner = CliRunner()
    runner.invoke(genschema, [str(tmp_path / "sub")])

    with open(str(tmp_path / "sub") + "/package.yaml", "r") as yaml_file:
        data = yaml.safe_load(yaml_file)
    return data


"""
Tests for the general function or yaml structure
"""


def test_parser_finds_function_name(tmp_path):
    """Parser should correctly detect multiple functions"""
    arg = ""
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)
    assert func_dict["package"]["functions"][0]["name"] == "test"
    assert func_dict["package"]["functions"][1]["name"] == "test2"


"""
Tests to make sure parser can successfully handle each arg type within a function
"""


def test_correct_dict_parse(tmp_path):
    """Parser should auto-gen dict type but not auto-gen dictionary defaults"""
    arg = "dict: dict = {'a':'b'},"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "dict"
    assert func_dict["parameters"][0]["type"] == "json"
    assert "default" not in func_dict["parameters"][0].keys()
    assert func_dict["parameters"][0]["required"] is False


def test_correct_string_parse(tmp_path):
    """Parser should auto-gen str arg's type and default"""
    arg = "str: str = '5',"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "str"
    assert func_dict["parameters"][0]["type"] == "string"
    assert func_dict["parameters"][0]["required"] is False
    assert func_dict["parameters"][0]["default"] == "5"


def test_correct_int_parse(tmp_path):
    """Parser should auto-gen int arg's type and default"""
    arg = "int: int = 5,"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "int"
    assert func_dict["parameters"][0]["type"] == "integer"
    assert func_dict["parameters"][0]["required"] is False
    assert func_dict["parameters"][0]["default"] == 5


def test_correct_float_parse(tmp_path):
    """Parser should auto-gen float arg's type and default"""
    arg = "float: float = 2.0"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "float"
    assert func_dict["parameters"][0]["type"] == "float"
    assert func_dict["parameters"][0]["required"] is False
    assert func_dict["parameters"][0]["default"] == 2.0


def test_correct_bool_parse(tmp_path):
    """Parser should auto-gen bool arg's type and default"""
    arg = "bool: bool = True"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "bool"
    assert func_dict["parameters"][0]["type"] == "boolean"
    assert func_dict["parameters"][0]["required"] is False
    assert func_dict["parameters"][0]["default"] == "True"


def test_correct_date_parse(tmp_path):
    """Parser should auto-gen dat arg's type and default"""
    arg = "date: date = date(11, 11, 11)"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "date"
    assert func_dict["parameters"][0]["type"] == "date"
    assert func_dict["parameters"][0]["required"] is False
    assert func_dict["parameters"][0]["default"] == "0011-11-11"


def test_correct_datetime_parse(tmp_path):
    """Parser should auto-gen datetime arg's type and default"""
    arg = "datetime: datetime = datetime(11, 11, 11)"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "datetime"
    assert func_dict["parameters"][0]["type"] == "datetime"
    assert func_dict["parameters"][0]["required"] is False
    assert func_dict["parameters"][0]["default"] == "0011-11-11 00:00:00"


"""
Tests to make sure parser can successfully handle irregular args
"""


def test_no_type_provided(tmp_path):
    """
    Parser should not assign type or default if none given,
    but should still fill out the default if one exists
    """
    arg = "no_def, no_def2 = 2"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "no_def"
    assert "type" not in func_dict["parameters"][0].keys()
    assert "default" not in func_dict["parameters"][0].keys()
    assert func_dict["parameters"][0]["required"] is True

    assert func_dict["parameters"][1]["name"] == "no_def2"
    assert "type" not in func_dict["parameters"][0].keys()
    assert func_dict["parameters"][1]["default"] == 2
    assert func_dict["parameters"][1]["required"] is False


def test_unsupported_type_provided(tmp_path):
    """Parser should not assign type if it can read a type
    that isn't supported by functionary. However, if a default exists,
    'required' should still be false and the default should still be set.
    """
    arg = "invalid_type: test, invalid_type2: test = 2,"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "invalid_type"
    assert "type" not in func_dict["parameters"][0].keys()
    assert "default" not in func_dict["parameters"][0].keys()
    assert func_dict["parameters"][0]["required"] is True

    assert "type" not in func_dict["parameters"][1].keys()
    assert func_dict["parameters"][1]["required"] is False
    assert func_dict["parameters"][1]["default"] == 2


def test_parser_cannot_parse_type_provided(tmp_path):
    """Parser should not assign type if it cannot parse the type given.
    However, 'required' should still be set to 'False' and the default
    set if a a default exists.
    """
    arg = "unparsable_type: test(), unparsable_type2: test() = 2,"
    _write_function_py_file(tmp_path, arg)
    func_dict = _run_genschema(tmp_path)["package"]["functions"][0]

    assert func_dict["parameters"][0]["name"] == "unparsable_type"
    assert "type" not in func_dict["parameters"][0].keys()
    assert "default" not in func_dict["parameters"][0].keys()
    assert func_dict["parameters"][0]["required"] is True

    assert "type" not in func_dict["parameters"][1].keys()
    assert func_dict["parameters"][1]["required"] is False
    assert func_dict["parameters"][1]["default"] == 2
