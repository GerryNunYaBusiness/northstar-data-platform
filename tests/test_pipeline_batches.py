from pathlib import Path
import sys
from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from monitoring.pipeline_batches import batch_is_successful
from ingestion.customers import CustomerRecord, load_raw_customers
from database import get_warehouse_connection

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

def test_load_raw_customers_resumes_partial_batch():
    batch_id = uuid4()

    customer_1 = CustomerRecord(
        customer_id=900010,
        first_name="Partial",
        last_name="Existing",
        email=f"{uuid4()}@example.com",
        phone="555-0110",
        created_at=datetime.now(timezone.utc),
    )

    customer_2 = CustomerRecord(
        customer_id=900011,
        first_name="Partial",
        last_name="Missing",
        email=f"{uuid4()}@example.com",
        phone="555-0111",
        created_at=datetime.now(timezone.utc),
    )

    try:
        first_count = load_raw_customers(
            customers=[customer_1],
            pipeline_run_id=uuid4(),
            batch_id=batch_id,
        )

        assert first_count == 1

        retry_count = load_raw_customers(
            customers=[customer_1, customer_2],
            pipeline_run_id=uuid4(),
            batch_id=batch_id,
        )

        assert retry_count == 1

        with get_warehouse_connection() as connection:
            count = connection.execute(
                """
                SELECT COUNT(*)
                FROM raw.Customers AS RC
                WHERE RC.BatchID = ?;
                """,
                str(batch_id),
            ).fetchone()[0]

        assert count == 2

    finally:
        with get_warehouse_connection() as connection:
            connection.execute(
                """
                DELETE FROM raw.Customers
                WHERE BatchID = ?;
                """,
                str(batch_id),
            )
            connection.commit()