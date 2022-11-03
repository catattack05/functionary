import time


def output_json(input: dict):
    """Demo JSON rendering by accepting JSON input and mirroring it back out"""
    return input


def output_text(input: str):
    """Demo text rendering by accepting string input and mirroring it back out. CSV
    formatted strings will present the option of rendering as a table"""
    return input


def long_running_process(duration: int = 60):
    """Simulates a long running process"""
    time.sleep(duration)
