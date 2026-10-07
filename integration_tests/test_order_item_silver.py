from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from ingestion.order_items import (
    OrderItemRecord,
    load_raw_order_items,
)
from transformation.order_items import load_silver_order_items


def test_quarantined_order_item_is_promoted_after_dependencies_become_available(
    # deployed_warehouse,
    warehouse_connection,
):
    cursor = warehouse_connection.cursor()
    cursor.execute(
        """
        SELECT
            @@SERVERNAME AS ServerName,
            DB_NAME() AS DatabaseName;
        """
    )

    database_info = cursor.fetchone()

    # print(
    #     "TEST DATABASE:",
    #     database_info.ServerName,
    #     database_info.DatabaseName,
    # )
    cursor.execute(
        """
        SELECT
            S.name AS SchemaName,
            O.name AS ObjectName,
            O.type_desc AS ObjectType
        FROM sys.objects AS O
        INNER JOIN sys.schemas AS S
            ON S.schema_id = O.schema_id
        WHERE O.name = 'OrderItemQuarantine';
        """
    )

    objects = cursor.fetchall()

    # print(
    #     "OrderItemQuarantine objects:",
    #     objects,
    # )
    """
    An OrderItem whose Order and Product are both missing should:

    1. Load successfully into Bronze.
    2. Be quarantined once with both failure reasons.
    3. Remain blocked when only the Product becomes available.
    4. Be promoted to Silver after the Order also becomes available.
    5. Retain its original quarantine record as historical evidence.
    """

    order_item_id = 970001
    order_id = 970001
    product_id = 970001
    customer_id = 970001

    batch_id = uuid4()
    first_pipeline_run_id = uuid4()
    second_pipeline_run_id = uuid4()
    third_pipeline_run_id = uuid4()

    order_item = OrderItemRecord(
        order_item_id=order_item_id,
        order_id=order_id,
        product_id=product_id,
        quantity=2,
        unit_price=Decimal("25.00"),
    )

    cursor = warehouse_connection.cursor()

    try:
        # ---------------------------------------------------------
        # Arrange: ensure all test-specific data is absent.
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.OrderItemQuarantine
            WHERE OrderItemID = ?;

            DELETE FROM silver.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM raw.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM silver.Orders
            WHERE OrderID = ?;

            DELETE FROM silver.Products
            WHERE ProductID = ?;

            DELETE FROM silver.Customers
            WHERE CustomerID = ?;
            """,
            order_item_id,
            order_item_id,
            order_item_id,
            order_id,
            product_id,
            customer_id,
        )

        warehouse_connection.commit()

        # ---------------------------------------------------------
        # Act 1:
        # Load the OrderItem into Bronze while BOTH dependencies
        # are missing.
        # ---------------------------------------------------------

        rows_inserted = load_raw_order_items(
            [order_item],
            first_pipeline_run_id,
            batch_id,
        )

        assert rows_inserted == 1

        first_result = load_silver_order_items(
            first_pipeline_run_id,
            batch_id,
        )

        # ---------------------------------------------------------
        # Assert 1:
        # It cannot enter Silver and should produce ONE quarantine
        # record containing BOTH failure reasons.
        # ---------------------------------------------------------

        assert first_result.rows_inserted == 0
        assert first_result.rows_updated == 0
        assert first_result.rows_quarantined == 1

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM silver.OrderItems
            WHERE OrderItemID = ?;
            """,
            order_item_id,
        )

        assert cursor.fetchone()[0] == 0

        cursor.execute(
            """
            SELECT
                FailureReason
            FROM ops.OrderItemQuarantine
            WHERE BatchID = ?
              AND OrderItemID = ?;
            """,
            batch_id,
            order_item_id,
        )

        quarantine_row = cursor.fetchone()

        assert quarantine_row is not None

        assert (
            "OrderID does not exist in silver.Orders"
            in quarantine_row.FailureReason
        )

        assert (
            "ProductID does not exist in silver.Products"
            in quarantine_row.FailureReason
        )

        # There should be exactly one quarantine record even though
        # two dependency failures were detected.
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.OrderItemQuarantine
            WHERE BatchID = ?
              AND OrderItemID = ?;
            """,
            batch_id,
            order_item_id,
        )

        assert cursor.fetchone()[0] == 1

        # ---------------------------------------------------------
        # Act 2:
        # Recover only ONE dependency: Product.
        #
        # The Order is still missing, so the OrderItem must remain
        # blocked from Silver.
        # ---------------------------------------------------------

        cursor.execute(
            """
            INSERT INTO silver.Products
            (
                ProductID,
                ProductName,
                Category,
                UnitCost,
                UnitPrice,
                RecordHash,
                SourceIngestedAt
            )
            VALUES
            (
                ?,
                'Integration Test Product',
                'Integration Test',
                10.00,
                25.00,
                ?,
                SYSUTCDATETIME()
            );
            """,
            product_id,
            bytes(32),
        )

        warehouse_connection.commit()

        second_result = load_silver_order_items(
            second_pipeline_run_id,
            batch_id,
        )

        # ---------------------------------------------------------
        # Assert 2:
        # Product now exists, but Order does not.
        # ---------------------------------------------------------

        assert second_result.rows_inserted == 0
        assert second_result.rows_updated == 0

        # We preserve the original historical quarantine rather than
        # creating another quarantine row for the same batch/item.
        assert second_result.rows_quarantined == 0

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM silver.OrderItems
            WHERE OrderItemID = ?;
            """,
            order_item_id,
        )

        assert cursor.fetchone()[0] == 0

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.OrderItemQuarantine
            WHERE BatchID = ?
              AND OrderItemID = ?;
            """,
            batch_id,
            order_item_id,
        )

        assert cursor.fetchone()[0] == 1

        # ---------------------------------------------------------
        # Act 3:
        # Recover the remaining dependency.
        #
        # silver.Orders requires a CustomerID, so create the Customer
        # first and then create the Order.
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
                'Integration',
                'Customer',
                'integration970001@example.com',
                '555-970-0001',
                ?,
                SYSUTCDATETIME(),
                SYSUTCDATETIME()
            );
            """,
            customer_id,
            bytes(32),
        )

        cursor.execute(
            """
            INSERT INTO silver.Orders
            (
                OrderID,
                CustomerID,
                OrderDate,
                [Status],
                TotalAmount,
                RecordHash,
                SourceIngestedAt
            )
            VALUES
            (
                ?,
                ?,
                ?,
                'Completed',
                50.00,
                ?,
                SYSUTCDATETIME()
            );
            """,
            order_id,
            customer_id,
            datetime(2026, 10, 1, 14, 0),
            bytes(32),
        )

        warehouse_connection.commit()

        third_result = load_silver_order_items(
            third_pipeline_run_id,
            batch_id,
        )

        # ---------------------------------------------------------
        # Assert 3:
        # Both dependencies now exist, so the previously quarantined
        # OrderItem becomes promotable.
        # ---------------------------------------------------------

        assert third_result.rows_inserted == 1
        assert third_result.rows_updated == 0
        assert third_result.rows_quarantined == 0

        cursor.execute(
            """
            SELECT
                OrderID,
                ProductID,
                Quantity,
                UnitPrice
            FROM silver.OrderItems
            WHERE OrderItemID = ?;
            """,
            order_item_id,
        )

        silver_row = cursor.fetchone()

        assert silver_row is not None
        assert silver_row.OrderID == order_id
        assert silver_row.ProductID == product_id
        assert silver_row.Quantity == 2
        assert silver_row.UnitPrice == Decimal("25.00")

        # ---------------------------------------------------------
        # Assert 4:
        # Promotion does NOT delete historical quarantine evidence.
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                COUNT(*)
            FROM ops.OrderItemQuarantine
            WHERE BatchID = ?
              AND OrderItemID = ?;
            """,
            batch_id,
            order_item_id,
        )

        assert cursor.fetchone()[0] == 1

    finally:
        # ---------------------------------------------------------
        # Cleanup:
        # use the admin integration-test connection rather than the
        # least-privilege application identity.
        #
        # Delete children before parents.
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.OrderItemQuarantine
            WHERE OrderItemID = ?;

            DELETE FROM silver.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM raw.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM silver.Orders
            WHERE OrderID = ?;

            DELETE FROM silver.Products
            WHERE ProductID = ?;

            DELETE FROM silver.Customers
            WHERE CustomerID = ?;
            """,
            order_item_id,
            order_item_id,
            order_item_id,
            order_id,
            product_id,
            customer_id,
        )

        warehouse_connection.commit()