from pathlib import Path
import sys
from unittest.mock import patch

import pyodbc
import pytest


SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from database import _connect_with_retry


def test_connection_succeeds_first_attempt():
    fake_connection = object()

    with patch(
        "database.pyodbc.connect",
        return_value=fake_connection,
    ) as mock_connect:
        result = _connect_with_retry(
            "fake-connection-string",
            max_attempts=3,
            delay_seconds=0,
        )

    assert result is fake_connection
    assert mock_connect.call_count == 1


def test_connection_retries_then_succeeds():
    fake_connection = object()

    with patch(
        "database.pyodbc.connect",
        side_effect=[
            pyodbc.OperationalError("temporary failure"),
            pyodbc.OperationalError("temporary failure"),
            fake_connection,
        ],
    ) as mock_connect:
        result = _connect_with_retry(
            "fake-connection-string",
            max_attempts=3,
            delay_seconds=0,
        )

    assert result is fake_connection
    assert mock_connect.call_count == 3


def test_connection_raises_after_max_attempts():
    with patch(
        "database.pyodbc.connect",
        side_effect=pyodbc.OperationalError(
            "database unavailable"
        ),
    ) as mock_connect:
        with pytest.raises(pyodbc.OperationalError):
            _connect_with_retry(
                "fake-connection-string",
                max_attempts=3,
                delay_seconds=0,
            )

    assert mock_connect.call_count == 3