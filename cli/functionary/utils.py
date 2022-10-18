import datetime

from rich.console import Console
from rich.table import Table


def flatten(results, object_fields):
    """Flattens any nested objects in results.

    The keys from each dict in results is checked for a replacement
    in object_fields. If found in object_fields, the original value
    will be replaced by new entries for each mapping specified.

    Args:
        results: List of dict objects to process
        object_fields: mapping of keys from a nested object in each
            result item that should be in used instead of the object.
            For example:
                object_fields={
                    "package": [("name", "package")],
                    "user": [("first_name", "first"), ("last_name", "last")],
                }
            will return:
                [ ...,
                  "package": <package.name>,
                  "first": <user.first_name>,
                  "last": <user.last_name>,
                  ...
                ]

    Returns:
        The input list with the replacements from object_fields included
    """
    new_results = []

    for item in results:
        new_item = {}
        for key, value in item.items():
            if key in object_fields:
                replacements = object_fields[key]
                for nested_key, label in replacements:
                    new_item[label] = value[nested_key] if value else None
            else:
                new_item[key] = value
        new_results.append(new_item)

    return new_results


def _fix_datetime_display(value):
    """
    Helper function for format_results to remove milliseconds from datetime

    Args:
        value: string representing datetime value
    Returns:
        value as a string representing datetime value without milliseconds
    """
    value = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%f%z")
    return value.strftime("%Y-%m-%d %H:%M:%S%Z")


def format_results(results, title="", excluded_fields=[]):
    """
    Helper function to organize table results using Rich

    Args:
        results: Results to format as a List
        title: Optional table title as a String
        excluded_fields: Optional list of keys to filter out

    Returns:
        None
    """
    table = Table(title=title, show_lines=True, title_justify="left")
    console = Console()
    first_row = True

    for item in results:
        row_data = []
        for key, value in item.items():
            if key in excluded_fields:
                continue
            if first_row:
                table.add_column(key.capitalize())
            if key.endswith("_at"):
                value = _fix_datetime_display(value)
            row_data.append(str(value) if value else None)
        table.add_row(*row_data)
        first_row = False
    console.print(table)
