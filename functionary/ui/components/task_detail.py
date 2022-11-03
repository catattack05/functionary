import csv

from django.core.exceptions import PermissionDenied
from django_unicorn.components import PollUpdate, UnicornView

from core.auth import Permission

FINISHED_STATUS = ["COMPLETE", "ERROR"]


class TaskDetailView(UnicornView):
    """View for handling the task detail view along with the various dynamically
    rendered elements"""

    output_format = None
    format_error = None
    formatted_result = None

    def hydrate(self):
        # NOTE: hydrate is the only method that gets called on every access, so
        # permissions checks must happen here.
        if not self.request.user.has_perm(Permission.TASK_READ, self.task.environment):
            raise PermissionDenied

    def mount(self):
        """Set values as appropriate at view initialization"""
        self.display_raw()

    def refresh_task(self):
        """Reload the task instance from the database and update the appropriate view
        properties to ensure the proper page components are rendered"""
        self.task.refresh_from_db()
        self.display_raw()

        if not self.should_refresh():
            return PollUpdate(disable=True, method="refresh_task")

    def display_raw(self):
        """Set the results output one of the available raw display formats"""
        if type(self.task.result) in [list, dict]:
            self.output_format = "json"
        else:
            self.output_format = "string"

    def display_table(self):
        """Set the results output format to table and format the results data for
        table rendering if possible"""
        self.output_format = "table"

        try:
            self.formatted_result = _format_table(self.task.result)
            self.format_error = None
        except Exception:
            self.format_error = "Result data is unsuitable for table output"

    def should_refresh(self):
        """Determines if the dynamic elements of the page should continue refreshing"""
        return self.task_complete() is False

    def show_output_selector(self):
        """Determines if the output format selector should be rendered"""
        if not self.task_complete():
            return False

        result_type = type(self.task.result)

        if result_type is list:
            show_selector = True
        elif result_type is str:
            show_selector = _detect_csv(self.task.result)
        else:
            show_selector = False

        return show_selector

    def task_complete(self):
        """Determines if the task has reached a terminal status"""
        return self.task.status in FINISHED_STATUS


def _detect_csv(results):
    """Attempt to determine if the provided results are valid CSV"""
    try:
        csv.Sniffer().sniff(results, delimiters=",")
    except Exception:
        return False

    return True


def _format_csv_table(result: str) -> dict:
    """Convert a string of CSV into a format suitable for table rendering"""
    csv_data = csv.reader(result.splitlines())
    formatted_result = {
        "headers": next(csv_data),
        "data": [row for row in csv_data],
    }

    return formatted_result


def _format_json_table(result: list) -> dict:
    """Convert a JSON list into a format suitable for table rendering"""
    headers = [key for key in result[0].keys()]
    res_data = []

    for row in result:
        r = []
        for key in headers:
            r.append(row[key])
        res_data.append(r)

    return {"headers": headers, "data": res_data}


def _format_table(result):
    """Convert a result to a table friendly format

    This will take in a "string" or "json" result and return
    the headers and a list of rows for the data. A result_type of
    string is assumed to be csv formatted data - a csv reader
    parses the data into the resulting header and data.

    A result type of json should be of the following format:
    [
        {"prop1":"value1", "prop2":"value2"},
        {"prop1":"value3", "prop2":"value4"}
    ]
    The headers are derived from the keys of the first entry in the list.
    """
    if type(result) is str:
        return _format_csv_table(result)
    elif type(result) is list and len(result) > 0:
        return _format_json_table(result)
    else:
        raise ValueError("Unable to convert result to table")
