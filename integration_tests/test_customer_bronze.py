from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import uuid4


SRC_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
)

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from ingestion.customers import (
    CustomerRecord,
    load_raw_customers,
)

from integration_tests.conftest import deployed_warehouse, warehouse_connection

def make_customer(
    customer_id: int,
) -> CustomerRecord:
    return CustomerRecord(
        customer_id=customer_id,
        first_name="Integration",
        last_name="Customer",
        email=(
            f"customer{customer_id}"
            "@example.test"
        ),
        phone="555-0100",
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc,        ),
    )

def test_new_batch_loads_customers_once(
    deployed_warehouse,
    warehouse_connection,
):
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    customers = [
        make_customer(900001),
        make_customer(900002),
    ]

    rows_inserted = load_raw_customers(
        customers,
        pipeline_run_id,
        batch_id,
    )

    assert rows_inserted == 2

    cursor = warehouse_connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM raw.Customers
        WHERE BatchID = ?;
        """,
        batch_id,
    )

    count = cursor.fetchone()[0]

    assert count == 2

def test_same_batch_customer_is_not_inserted_twice(
    deployed_warehouse,
    warehouse_connection,
):
    batch_id = uuid4()

    customer = make_customer(900003)

    first_run_id = uuid4()

    first_rows = load_raw_customers(
        [customer],
        first_run_id,
        batch_id,
    )

    second_run_id = uuid4()

    second_rows = load_raw_customers(
        [customer],
        second_run_id,
        batch_id,
    )

    assert first_rows == 1
    assert second_rows == 0

    cursor = warehouse_connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM raw.Customers
        WHERE
            BatchID = ?
            AND CustomerID = ?;
        """,
        batch_id,
        customer.customer_id,
    )

    count = cursor.fetchone()[0]

    assert count == 1

def test_same_customer_can_exist_in_different_batches(
    deployed_warehouse,
    warehouse_connection,
):
    customer = make_customer(900004)

    first_batch_id = uuid4()
    second_batch_id = uuid4()

    first_rows = load_raw_customers(
        [customer],
        uuid4(),
        first_batch_id,
    )

    second_rows = load_raw_customers(
        [customer],
        uuid4(),
        second_batch_id,
    )

    assert first_rows == 1
    assert second_rows == 1

    cursor = warehouse_connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM raw.Customers
        WHERE CustomerID = ?;
        """,
        customer.customer_id,
    )

    count = cursor.fetchone()[0]

    assert count == 2