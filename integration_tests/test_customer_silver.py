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
from transformation.customers import (    load_silver_customers,)
from integration_tests.conftest import deployed_warehouse, warehouse_connection


TEST_CUSTOMER_ID = 910001


def make_customer(
    phone: str,
) -> CustomerRecord:
    return CustomerRecord(
        customer_id=TEST_CUSTOMER_ID,
        first_name="Integration",
        last_name="Silver",
        email="silver.integration@example.test",
        phone=phone,
        created_at=datetime(2026,1,1,12,0,0,        ),
    )


def test_silver_insert_no_change_and_update(
    deployed_warehouse,
    warehouse_connection,
):
    # ---------------------------------------------------------
    # Step 1:
    # Put a new customer into Bronze.
    # ---------------------------------------------------------

    customer = make_customer(
        phone="555-0100",
    )

    first_batch_id = uuid4()
    first_pipeline_run_id = uuid4()

    bronze_rows = load_raw_customers(
        [customer],
        first_pipeline_run_id,
        first_batch_id,
    )

    assert bronze_rows == 1

    # ---------------------------------------------------------
    # Step 2:
    # First Silver load should INSERT the customer.
    # ---------------------------------------------------------

    first_result = load_silver_customers()

    assert first_result.inserted >= 1

    cursor = warehouse_connection.cursor()

    cursor.execute(
        """
        SELECT
            FirstName,
            LastName,
            Email,
            Phone
        FROM silver.Customers
        WHERE CustomerID = ?;
        """,
        TEST_CUSTOMER_ID,
    )

    row = cursor.fetchone()

    assert row is not None
    assert row[0] == "Integration"
    assert row[1] == "Silver"
    assert row[2] == (
        "silver.integration@example.test"
    )
    assert row[3] == "555-0100"

    # ---------------------------------------------------------
    # Step 3:
    # Running Silver again without new Bronze data should
    # perform no INSERT or UPDATE.
    # ---------------------------------------------------------

    second_result = load_silver_customers()

    assert second_result.inserted == 0
    assert second_result.updated == 0

    # ---------------------------------------------------------
    # Step 4:
    # Put a changed version of the same customer into a
    # different logical batch.
    # ---------------------------------------------------------

    changed_customer = make_customer(
        phone="555-9999",
    )

    second_batch_id = uuid4()
    second_pipeline_run_id = uuid4()

    bronze_rows = load_raw_customers(
        [changed_customer],
        second_pipeline_run_id,
        second_batch_id,
    )

    assert bronze_rows == 1

    # ---------------------------------------------------------
    # Step 5:
    # Silver should detect the changed hash and UPDATE the
    # existing current-state customer.
    # ---------------------------------------------------------

    third_result = load_silver_customers()

    assert third_result.inserted == 0
    assert third_result.updated >= 1

    # ---------------------------------------------------------
    # Step 6:
    # Verify the actual persisted Silver value.
    # ---------------------------------------------------------

    cursor.execute(
        """
        SELECT
            Phone
        FROM silver.Customers
        WHERE CustomerID = ?;
        """,
        TEST_CUSTOMER_ID,
    )

    row = cursor.fetchone()

    assert row is not None
    assert row[0] == "555-9999"