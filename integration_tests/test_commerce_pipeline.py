from uuid import uuid4
from datetime import datetime
from decimal import Decimal

from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from commerce_pipeline import run_commerce_pipeline

CUSTOMER_ID = 990001
PRODUCT_ID = 990001
ORDER_ID = 990001
ORDER_ITEM_ID = 990001
PAYMENT_ID = 990001


def test_commerce_pipeline_end_to_end(
    source_connection,
    warehouse_connection,
):
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    source_cursor = source_connection.cursor()
    warehouse_cursor = warehouse_connection.cursor()

    try:
        # =========================================================
        # ARRANGE
        #
        # Clean source records first so the test is deterministic.
        # Children must be removed before parents.
        # =========================================================

        source_cursor.execute(
            """
            DELETE FROM dbo.Payments
            WHERE PaymentID = ?;

            DELETE FROM dbo.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM dbo.Orders
            WHERE OrderID = ?;

            DELETE FROM dbo.Products
            WHERE ProductID = ?;

            DELETE FROM dbo.Customers
            WHERE CustomerID = ?;
            """,
            PAYMENT_ID,
            ORDER_ITEM_ID,
            ORDER_ID,
            PRODUCT_ID,
            CUSTOMER_ID,
        )

        source_connection.commit()

        # =========================================================
        # Insert one complete commerce graph into the source.
        # =========================================================

        source_cursor.execute(
            """
            INSERT INTO dbo.Customers
            (
                CustomerID,
                FirstName,
                LastName,
                Email,
                Phone,
                CreatedAt
            )
            VALUES
            (
                ?,
                'Commerce',
                'IntegrationTest',
                'commerce990001@example.com',
                '555-990-0001',
                ?
            );
            """,
            CUSTOMER_ID,
            datetime(2026, 10, 6, 9, 0),
        )

        source_cursor.execute(
            """
            INSERT INTO dbo.Products
            (
                ProductID,
                ProductName,
                Category,
                UnitCost,
                UnitPrice
            )
            VALUES
            (
                ?,
                'Integration Test Product',
                'Testing',
                ?,
                ?
            );
            """,
            PRODUCT_ID,
            Decimal("40.00"),
            Decimal("50.00"),
        )

        source_cursor.execute(
            """
            INSERT INTO dbo.Orders
            (
                OrderID,
                CustomerID,
                OrderDate,
                [Status],
                TotalAmount
            )
            VALUES
            (
                ?,
                ?,
                ?,
                'Completed',
                ?
            );
            """,
            ORDER_ID,
            CUSTOMER_ID,
            datetime(2026, 10, 6, 10, 0),
            Decimal("100.00"),
        )

        source_cursor.execute(
            """
            INSERT INTO dbo.OrderItems
            (
                OrderItemID,
                OrderID,
                ProductID,
                Quantity,
                UnitPrice
            )
            VALUES
            (
                ?,
                ?,
                ?,
                ?,
                ?
            );
            """,
            ORDER_ITEM_ID,
            ORDER_ID,
            PRODUCT_ID,
            2,
            Decimal("50.00"),
        )

        source_cursor.execute(
            """
            INSERT INTO dbo.Payments
            (
                PaymentID,
                OrderID,
                PaymentDate,
                PaymentMethod,
                Amount,
                [Status]
            )
            VALUES
            (
                ?,
                ?,
                ?,
                'CreditCard',
                ?,
                'Completed'
            );
            """,
            PAYMENT_ID,
            ORDER_ID,
            datetime(2026, 10, 6, 10, 5),
            Decimal("100.00"),
        )

        source_connection.commit()

        # =========================================================
        # Clean any warehouse state left by a previous failed test.
        # =========================================================

        warehouse_cursor.execute(
            """
            DELETE FROM ops.PaymentQuarantine
            WHERE PaymentID = ?;

            DELETE FROM ops.OrderItemQuarantine
            WHERE OrderItemID = ?;

            DELETE FROM ops.OrderQuarantine
            WHERE OrderID = ?;

            DELETE FROM silver.Payments
            WHERE PaymentID = ?;

            DELETE FROM silver.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM silver.Orders
            WHERE OrderID = ?;

            DELETE FROM silver.Products
            WHERE ProductID = ?;

            DELETE FROM silver.Customers
            WHERE CustomerID = ?;

            DELETE FROM raw.Payments
            WHERE PaymentID = ?;

            DELETE FROM raw.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM raw.Orders
            WHERE OrderID = ?;

            DELETE FROM raw.Products
            WHERE ProductID = ?;

            DELETE FROM raw.Customers
            WHERE CustomerID = ?;
            """,
            PAYMENT_ID,
            ORDER_ITEM_ID,
            ORDER_ID,
            PAYMENT_ID,
            ORDER_ITEM_ID,
            ORDER_ID,
            PRODUCT_ID,
            CUSTOMER_ID,
            PAYMENT_ID,
            ORDER_ITEM_ID,
            ORDER_ID,
            PRODUCT_ID,
            CUSTOMER_ID,
        )

        warehouse_connection.commit()

        # =========================================================
        # ACT
        # =========================================================

        result = run_commerce_pipeline(
            pipeline_run_id,
            batch_id,
        )

        # =========================================================
        # ASSERT — pipeline result
        # =========================================================

        assert result.status == "SUCCESS"
        assert result.pipeline_run_id == pipeline_run_id
        assert result.batch_id == batch_id

        assert [
            stage.stage_name
            for stage in result.stages
        ] == [
            "customers_bronze",
            "customers_silver",
            "products_bronze",
            "products_silver",
            "orders_bronze",
            "orders_silver",
            "order_items_bronze",
            "order_items_silver",
            "payments_bronze",
            "payments_silver",
        ]

        # =========================================================
        # ASSERT — Bronze
        # =========================================================

        bronze_checks = [
            (
                "raw.Customers",
                "CustomerID",
                CUSTOMER_ID,
            ),
            (
                "raw.Products",
                "ProductID",
                PRODUCT_ID,
            ),
            (
                "raw.Orders",
                "OrderID",
                ORDER_ID,
            ),
            (
                "raw.OrderItems",
                "OrderItemID",
                ORDER_ITEM_ID,
            ),
            (
                "raw.Payments",
                "PaymentID",
                PAYMENT_ID,
            ),
        ]

        for table_name, key_name, key_value in bronze_checks:
            warehouse_cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE {key_name} = ?
                  AND BatchID = ?;
                """,
                key_value,
                batch_id,
            )

            assert warehouse_cursor.fetchone()[0] == 1

        # =========================================================
        # ASSERT — Silver
        # =========================================================

        silver_checks = [
            (
                "silver.Customers",
                "CustomerID",
                CUSTOMER_ID,
            ),
            (
                "silver.Products",
                "ProductID",
                PRODUCT_ID,
            ),
            (
                "silver.Orders",
                "OrderID",
                ORDER_ID,
            ),
            (
                "silver.OrderItems",
                "OrderItemID",
                ORDER_ITEM_ID,
            ),
            (
                "silver.Payments",
                "PaymentID",
                PAYMENT_ID,
            ),
        ]

        for table_name, key_name, key_value in silver_checks:
            warehouse_cursor.execute(
                f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE {key_name} = ?;
                """,
                key_value,
            )

            assert warehouse_cursor.fetchone()[0] == 1

        # =========================================================
        # ASSERT — dependency-sensitive business values
        # =========================================================

        warehouse_cursor.execute(
            """
            SELECT
                O.CustomerID,
                O.[Status],
                O.TotalAmount
            FROM silver.Orders AS O
            WHERE O.OrderID = ?;
            """,
            ORDER_ID,
        )

        order_row = warehouse_cursor.fetchone()

        assert order_row is not None
        assert order_row.CustomerID == CUSTOMER_ID
        assert order_row.Status == "Completed"
        assert order_row.TotalAmount == Decimal("100.00")

        warehouse_cursor.execute(
            """
            SELECT
                OI.OrderID,
                OI.ProductID,
                OI.Quantity,
                OI.UnitPrice
            FROM silver.OrderItems AS OI
            WHERE OI.OrderItemID = ?;
            """,
            ORDER_ITEM_ID,
        )

        order_item_row = warehouse_cursor.fetchone()

        assert order_item_row is not None
        assert order_item_row.OrderID == ORDER_ID
        assert order_item_row.ProductID == PRODUCT_ID
        assert order_item_row.Quantity == 2
        assert order_item_row.UnitPrice == Decimal("50.00")

        warehouse_cursor.execute(
            """
            SELECT
                P.OrderID,
                P.PaymentMethod,
                P.Amount,
                P.[Status]
            FROM silver.Payments AS P
            WHERE P.PaymentID = ?;
            """,
            PAYMENT_ID,
        )

        payment_row = warehouse_cursor.fetchone()

        assert payment_row is not None
        assert payment_row.OrderID == ORDER_ID
        assert payment_row.PaymentMethod == "CreditCard"
        assert payment_row.Amount == Decimal("100.00")
        assert payment_row.Status == "Completed"

        # =========================================================
        # ASSERT — no dependency records were quarantined
        # =========================================================

        warehouse_cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.OrderQuarantine
            WHERE OrderID = ?;
            """,
            ORDER_ID,
        )

        assert warehouse_cursor.fetchone()[0] == 0

        warehouse_cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.OrderItemQuarantine
            WHERE OrderItemID = ?;
            """,
            ORDER_ITEM_ID,
        )

        assert warehouse_cursor.fetchone()[0] == 0

        warehouse_cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.PaymentQuarantine
            WHERE PaymentID = ?;
            """,
            PAYMENT_ID,
        )

        assert warehouse_cursor.fetchone()[0] == 0

        # =========================================================
        # ASSERT — pipeline observability
        #
        # Adjust column names here if your existing ops schema uses
        # slightly different names.
        # =========================================================

        warehouse_cursor.execute(
            """
            SELECT
                PR.[Status]
            FROM ops.PipelineRuns AS PR
            WHERE PR.PipelineRunID = ?;
            """,
            pipeline_run_id,
        )

        pipeline_row = warehouse_cursor.fetchone()

        assert pipeline_row is not None
        assert pipeline_row.Status == "SUCCESS"

        warehouse_cursor.execute(
            """
            SELECT
                PSR.StageName,
                PSR.[Status]
            FROM ops.PipelineStageRuns AS PSR
            WHERE PSR.PipelineRunID = ?
            ORDER BY PSR.StartedAt;
            """,
            pipeline_run_id,
        )

        stage_rows = warehouse_cursor.fetchall()

        assert len(stage_rows) == 10

        assert [
            row.StageName
            for row in stage_rows
        ] == [
            "customers_bronze",
            "customers_silver",
            "products_bronze",
            "products_silver",
            "orders_bronze",
            "orders_silver",
            "order_items_bronze",
            "order_items_silver",
            "payments_bronze",
            "payments_silver",
        ]

        assert all(
            row.Status == "SUCCESS"
            for row in stage_rows
        )

    finally:
        # =========================================================
        # CLEANUP — warehouse
        #
        # Operational records first if PipelineStageRuns references
        # PipelineRuns.
        # =========================================================

        warehouse_cursor.execute(
            """
            DELETE FROM ops.PipelineStageRuns
            WHERE PipelineRunID = ?;

            DELETE FROM ops.PipelineRuns
            WHERE PipelineRunID = ?;

            DELETE FROM ops.PaymentQuarantine
            WHERE PaymentID = ?;

            DELETE FROM ops.OrderItemQuarantine
            WHERE OrderItemID = ?;

            DELETE FROM ops.OrderQuarantine
            WHERE OrderID = ?;

            DELETE FROM silver.Payments
            WHERE PaymentID = ?;

            DELETE FROM silver.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM silver.Orders
            WHERE OrderID = ?;

            DELETE FROM silver.Products
            WHERE ProductID = ?;

            DELETE FROM silver.Customers
            WHERE CustomerID = ?;

            DELETE FROM raw.Payments
            WHERE PaymentID = ?;

            DELETE FROM raw.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM raw.Orders
            WHERE OrderID = ?;

            DELETE FROM raw.Products
            WHERE ProductID = ?;

            DELETE FROM raw.Customers
            WHERE CustomerID = ?;
            """,
            pipeline_run_id,
            pipeline_run_id,
            PAYMENT_ID,
            ORDER_ITEM_ID,
            ORDER_ID,
            PAYMENT_ID,
            ORDER_ITEM_ID,
            ORDER_ID,
            PRODUCT_ID,
            CUSTOMER_ID,
            PAYMENT_ID,
            ORDER_ITEM_ID,
            ORDER_ID,
            PRODUCT_ID,
            CUSTOMER_ID,
        )

        warehouse_connection.commit()

        # =========================================================
        # CLEANUP — source
        # =========================================================

        source_cursor.execute(
            """
            DELETE FROM dbo.Payments
            WHERE PaymentID = ?;

            DELETE FROM dbo.OrderItems
            WHERE OrderItemID = ?;

            DELETE FROM dbo.Orders
            WHERE OrderID = ?;

            DELETE FROM dbo.Products
            WHERE ProductID = ?;

            DELETE FROM dbo.Customers
            WHERE CustomerID = ?;
            """,
            PAYMENT_ID,
            ORDER_ITEM_ID,
            ORDER_ID,
            PRODUCT_ID,
            CUSTOMER_ID,
        )

        source_connection.commit()