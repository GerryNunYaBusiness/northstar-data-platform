from decimal import Decimal
from uuid import uuid4

from ingestion.products import (
    ProductRecord,
    load_raw_products,
)
from transformation.products import load_silver_products

TEST_PRODUCT_ID = 930001

def make_product(
    product_id: int,
    unit_price: str,
) -> ProductRecord:
    return ProductRecord(
        product_id=TEST_PRODUCT_ID,
        product_name="Silver Integration Widget",
        category="Integration",
        unit_cost=Decimal("10.00"),
        unit_price=Decimal(unit_price),
    )


def test_silver_insert_no_change_and_update(
    deployed_warehouse,
    warehouse_connection,
):
    try:
        # ---------------------------------------------------------
        # Step 0:
        # Clean up any existing test data.
        # ---------------------------------------------------------

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM silver.Products
            WHERE ProductID = ?;
            """,
            TEST_PRODUCT_ID,
        )

        warehouse_connection.commit()
        # ---------------------------------------------------------
        # Step 1:
        # Put a new product into Bronze.
        # ---------------------------------------------------------

        product = make_product(
            product_id=TEST_PRODUCT_ID,
            unit_price="15.00"
        )

        first_batch_id = uuid4()
        first_pipeline_run_id = uuid4()

        bronze_rows = load_raw_products(
            [product],
            first_pipeline_run_id,
            first_batch_id,
        )

        assert bronze_rows == 1
        
        # ---------------------------------------------------------
        # Step 2:
        # First Silver load should INSERT the product.
        # ---------------------------------------------------------
        first_result = load_silver_products()

        assert first_result.rows_inserted >= 1

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT
                ProductName,
                Category,
                UnitCost,
                UnitPrice
            FROM silver.Products
            WHERE ProductID = ?;
            """,
            TEST_PRODUCT_ID,
        )

        row = cursor.fetchone()

        assert row.ProductName == "Silver Integration Widget"
        assert row.Category == "Integration"
        assert row.UnitCost == Decimal("10.00")
        assert row.UnitPrice == Decimal("15.00")

        # ---------------------------------------------------------
        # Step 3:
        # Running Silver again without new Bronze data should
        # perform no INSERT or UPDATE.
        # ---------------------------------------------------------

        second_result = load_silver_products()

        assert second_result.rows_inserted == 0
        assert second_result.rows_updated == 0

        # ---------------------------------------------------------
        # Step 4:
        # Put a changed version of the same customer into a
        # different logical batch.
        # ---------------------------------------------------------

        changed_product = make_product(
            product_id=TEST_PRODUCT_ID,
            unit_price="17.50"
        )

        changed_bronze_rows = load_raw_products(
            [changed_product],
            uuid4(),
            uuid4(),
        )

        assert changed_bronze_rows == 1

        # ---------------------------------------------------------
        # Step 5:
        # Silver should detect the changed hash and UPDATE the
        # existing current-state customer.
        # ---------------------------------------------------------

        third_result = load_silver_products()

        assert third_result.rows_updated >= 1

        # ---------------------------------------------------------
        # Step 6:
        # Verify the actual persisted Silver value.
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT
                ProductName,
                Category,
                UnitCost,
                UnitPrice
            FROM silver.Products
            WHERE ProductID = ?;
            """,
            TEST_PRODUCT_ID,
        )

        row = cursor.fetchone()

        assert row.UnitPrice == Decimal("17.50")
    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM silver.Products
            WHERE ProductID = ?;
            """,
            TEST_PRODUCT_ID,
        )

        cursor.execute(
            """
            DELETE FROM raw.Products
            WHERE ProductID = ?;
            """,
            TEST_PRODUCT_ID,
        )

        warehouse_connection.commit()
