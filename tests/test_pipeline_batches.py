from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
from uuid import uuid4

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
from monitoring.pipeline_batches import batch_is_successful


@patch("monitoring.pipeline_batches.get_warehouse_connection")
def test_successful_batch_returns_true(
    mock_get_connection,
):
    connection = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = connection

    connection.execute.return_value.fetchone.return_value = (
        "SUCCESS",
    )

    result = batch_is_successful(uuid4())

    assert result is True

@patch("monitoring.pipeline_batches.get_warehouse_connection")
def test_failed_batch_returns_false(
    mock_get_connection,
):
    connection = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = connection

    connection.execute.return_value.fetchone.return_value = (
        "FAILED",
    )

    result = batch_is_successful(uuid4())

    assert result is False

@patch("monitoring.pipeline_batches.get_warehouse_connection")
def test_missing_batch_returns_false(
    mock_get_connection,
):
    connection = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = connection

    connection.execute.return_value.fetchone.return_value = None

    result = batch_is_successful(uuid4())

    assert result is False