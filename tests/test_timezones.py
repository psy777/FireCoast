import pathlib
import sys

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import app as firenotes_app


def test_format_datetime_uses_provided_timezone():
    naive_value = "2024-05-01 09:30"

    formatted = firenotes_app._format_datetime_for_display(
        naive_value, "America/New_York"
    )

    assert formatted == "May 01, 2024 09:30 AM EDT"
