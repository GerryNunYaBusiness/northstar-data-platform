from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from pathlib import Path
import sys


SRC_PATH = (Path(__file__).resolve().parents[1] / "src")

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ingestion.orders import (
    OrderRecord,
    load_raw_orders,
)
from transformation.orders import load_silver_orders


def test_quarantined_order_is_promoted_after_customer_becomes_available(
    deployed_warehouse,
    warehouse_connection,
):
    customer_id = 950001
    order_id = 950001

    batch_id = uuid4()
    first_pipeline_run_id = uuid4()
    recovery_pipeline_run_id = uuid4()

    order = OrderRecord(
        order_id=order_id,
        customer_id=customer_id,
        order_date=datetime(2026, 10, 1, 13, 0),
        status="Completed",
        total_amount=Decimal("100.00"),
    )

    cursor = warehouse_connection.cursor()

    try:
        # ---------------------------------------------------------
        # Arrange
        #
        # Make sure this test begins without the Customer, Order,
        # or previous quarantine history.
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.OrderQuarantine
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM silver.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM raw.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM silver.Customers
            WHERE CustomerID = ?;
            """,
            customer_id,
        )

        warehouse_connection.commit()

        # ---------------------------------------------------------
        # Act 1
        #
        # Load the Order into Bronze.
        # The referenced Customer does not exist in Silver.
        # ---------------------------------------------------------

        bronze_rows = load_raw_orders(
            [order],
            first_pipeline_run_id,
            batch_id,
        )

        assert bronze_rows == 1

        first_result = load_silver_orders(
            first_pipeline_run_id,
            batch_id,
        )

        # ---------------------------------------------------------
        # Assert 1
        #
        # Order should be quarantined rather than promoted.
        # ---------------------------------------------------------

        assert first_result.rows_inserted == 0
        assert first_result.rows_updated == 0
        assert first_result.rows_quarantined == 1

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM silver.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        silver_order_count = cursor.fetchone()[0]

        assert silver_order_count == 0

        cursor.execute(
            """
            SELECT
                OrderID,
                CustomerID,
                FailureReason
            FROM ops.OrderQuarantine
            WHERE BatchID = ?
              AND OrderID = ?;
            """,
            batch_id,
            order_id,
        )

        quarantine_row = cursor.fetchone()

        assert quarantine_row is not None
        assert quarantine_row.OrderID == order_id
        assert quarantine_row.CustomerID == customer_id
        assert (
            quarantine_row.FailureReason
            == "CustomerID does not exist in silver.Customers"
        )

        # ---------------------------------------------------------
        # Arrange recovery
        #
        # Simulate the upstream Customer problem being resolved.
        #
        # We use the admin test fixture here because this is test
        # setup, not application behavior.
        # ---------------------------------------------------------

        cursor.execute(
            """
            INSERT INTO silver.Customers
            (
                CustomerID,
                FirstName,
                LastName,
                Email,
                Phone,
                RecordHash,
                SourceIngestedAt,
                ProcessedAt
            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?,
                ?,
                SYSUTCDATETIME(),
                SYSUTCDATETIME()
            );
            """,
            customer_id,
            "Integration",
            "Customer",
            "integration.customer@example.com",
            "555-0100",
            bytes(32),
        )

        warehouse_connection.commit()

        # ---------------------------------------------------------
        # Act 2
        #
        # Retry the SAME logical batch with a NEW execution/run ID.
        # ---------------------------------------------------------

        recovery_result = load_silver_orders(
            recovery_pipeline_run_id,
            batch_id,
        )

        # ---------------------------------------------------------
        # Assert 2
        #
        # The previously quarantined Order should now be promotable.
        # ---------------------------------------------------------

        assert recovery_result.rows_inserted == 1
        assert recovery_result.rows_updated == 0
        assert recovery_result.rows_quarantined == 0

        cursor.execute(
            """
            SELECT
                OrderID,
                CustomerID,
                [Status],
                TotalAmount
            FROM silver.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        silver_order = cursor.fetchone()

        assert silver_order is not None
        assert silver_order.OrderID == order_id
        assert silver_order.CustomerID == customer_id
        assert silver_order.Status == "Completed"
        assert silver_order.TotalAmount == Decimal("100.00")

        # ---------------------------------------------------------
        # Assert 3
        #
        # Recovery must NOT erase the historical quarantine record.
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.OrderQuarantine
            WHERE BatchID = ?
              AND OrderID = ?
              AND FailureReason =
                  'CustomerID does not exist in silver.Customers';
            """,
            batch_id,
            order_id,
        )

        quarantine_count = cursor.fetchone()[0]

        assert quarantine_count == 1

    finally:
        # ---------------------------------------------------------
        # Cleanup
        #
        # Test infrastructure uses the admin connection so we don't
        # broaden northstar_pipeline permissions merely for tests.
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.OrderQuarantine
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM silver.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM raw.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM silver.Customers
            WHERE CustomerID = ?;
            """,
            customer_id,
        )

        warehouse_connection.commit()

def test_invalid_order_record_is_quarantined(deployed_warehouse, warehouse_connection):
    order_id = 950002
    customer_id = 950002

    batch_id = uuid4()
    pipeline_run_id = uuid4()

    order = OrderRecord(
        order_id=order_id,
        customer_id=customer_id,
        order_date=datetime(2026, 10, 1, 13, 0),
        status="InvalidStatus",
        total_amount=Decimal("-25.00"),
    )

    cursor = warehouse_connection.cursor()

    try:
        # ---------------------------------------------------------
        # Arrange
        #
        # Make sure this test begins without the Customer, Order,
        # or previous quarantine history.
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.OrderQuarantine
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM silver.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM raw.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        warehouse_connection.commit()

        # ---------------------------------------------------------
        # Act
        #
        # Load the invalid Order into Bronze and then attempt to
        # promote it to Silver.
        # ---------------------------------------------------------

        bronze_rows = load_raw_orders(
            [order],
            pipeline_run_id,
            batch_id,
        )

        assert bronze_rows == 1

        result = load_silver_orders(
            pipeline_run_id,
            batch_id,
        )
        assert result.rows_inserted == 0
        assert result.rows_updated == 0
        assert result.rows_quarantined == 1

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM silver.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        silver_order_count = cursor.fetchone()[0]

        assert silver_order_count == 0

        cursor.execute(
            """
            SELECT
                FailureReason
            FROM ops.OrderQuarantine
            WHERE BatchID = ?
            AND OrderID = ?;
            """,
            batch_id,
            order_id,
        )
        
        row = cursor.fetchone()

        assert "Invalid order status" in row.FailureReason
        assert (
            "TotalAmount must be greater than or equal to zero"
            in row.FailureReason
        )
    finally:
        # ---------------------------------------------------------
        # Cleanup
        #
        # Test infrastructure uses the admin connection so we don't
        # broaden northstar_pipeline permissions merely for tests.
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.OrderQuarantine
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM silver.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        cursor.execute(
            """
            DELETE FROM raw.Orders
            WHERE OrderID = ?;
            """,
            order_id,
        )

        warehouse_connection.commit()