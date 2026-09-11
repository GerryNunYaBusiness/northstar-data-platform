from pathlib import Path
import sys
from datetime import datetime, timezone
from uuid import uuid4

import pyodbc
import pytest


SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from database import get_warehouse_connection
from ingestion.customers import CustomerRecord, load_raw_customers
from customer_pipeline import run_customer_pipeline

@pytest.fixture
def warehouse_connection():
    connection = get_warehouse_connection()

    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def insert_raw_customer(
    connection,
    customer_id,
    pipeline_run_id,
    batch_id,
):
    connection.execute(
        """
        INSERT INTO raw.Customers
        (
            CustomerID,
            FirstName,
            LastName,
            Email,
            Phone,
            CreatedAt,
            IngestedAt,
            PipelineRunID,
            BatchID,
            RecordHash
        )
        VALUES
        (
            ?, ?, ?, ?, ?, ?,
            SYSUTCDATETIME(),
            ?, ?, ?
        );
        """,
        customer_id,
        "Integration",
        "Test",
        f"integration-{uuid4()}@example.com",
        "555-0100",
        datetime.now(timezone.utc),
        str(pipeline_run_id),
        str(batch_id),
        bytes(32),
    )

def test_same_customer_same_batch_is_rejected(
    warehouse_connection,
):
    customer_id = 900001
    batch_id = uuid4()

    insert_raw_customer(
        warehouse_connection,
        customer_id=customer_id,
        pipeline_run_id=uuid4(),
        batch_id=batch_id,
    )

    with pytest.raises(pyodbc.IntegrityError):
        insert_raw_customer(
            warehouse_connection,
            customer_id=customer_id,
            pipeline_run_id=uuid4(),
            batch_id=batch_id,
        )

def test_same_customer_different_batches_is_allowed(
    warehouse_connection,
):
    customer_id = 900002

    batch_id_1 = uuid4()
    batch_id_2 = uuid4()

    insert_raw_customer(
        warehouse_connection,
        customer_id=customer_id,
        pipeline_run_id=uuid4(),
        batch_id=batch_id_1,
    )

    insert_raw_customer(
        warehouse_connection,
        customer_id=customer_id,
        pipeline_run_id=uuid4(),
        batch_id=batch_id_2,
    )

    count = warehouse_connection.execute(
        """
        SELECT COUNT(*)
        FROM raw.Customers AS RC
        WHERE RC.CustomerID = ?
          AND RC.BatchID IN (?, ?);
        """,
        customer_id,
        str(batch_id_1),
        str(batch_id_2),
    ).fetchone()[0]

    assert count == 2

def test_load_raw_customers_skips_duplicate_batch_customer():
    batch_id = uuid4()

    customer = CustomerRecord(
        customer_id=900003,
        first_name="Grace",
        last_name="Hopper",
        email=f"integration-{uuid4()}@example.com",
        phone="555-0101",
        created_at=datetime.now(timezone.utc),
    )

    try:
        first_rows_inserted = load_raw_customers(
            customers=[customer],
            pipeline_run_id=uuid4(),
            batch_id=batch_id,
        )

        assert first_rows_inserted == 1

        second_rows_inserted = load_raw_customers(
            customers=[customer],
            pipeline_run_id=uuid4(),
            batch_id=batch_id,
        )

        assert second_rows_inserted == 0

        with get_warehouse_connection() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*)
                FROM raw.Customers
                WHERE BatchID = ?
                  AND CustomerID = ?;
                """,
                str(batch_id),
                customer.customer_id,
            ).fetchone()

        assert row[0] == 1

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

def test_supplied_batch_id_is_reused():
    batch_id = uuid4()

    # Arrange mocks for extract/load/monitoring dependencies
    # so the pipeline doesn't touch SQL Server.

    result = run_customer_pipeline(
        batch_id=batch_id,
    )

    assert result.batch_id == batch_id
    assert result.pipeline_run_id != result.batch_id

def test_pipeline_generates_batch_id_when_not_supplied():
    result = run_customer_pipeline()

    assert result.batch_id is not None
    assert result.pipeline_run_id != result.batch_id


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

