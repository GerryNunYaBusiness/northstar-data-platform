from decimal import Decimal
from pathlib import Path
import sys
from uuid import uuid4


SRC_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
)

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ingestion.products import ProductRecord, load_raw_products
from tests.test_products import make_product

from integration_tests.conftest import deployed_warehouse, warehouse_connection

def test_new_product_batch_loads_product_once(
    deployed_warehouse,
    warehouse_connection,
):
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    product = ProductRecord(
        product_id=920001,
        product_name="Integration Widget",
        category="Integration",
        unit_cost=Decimal("10.00"),
        unit_price=Decimal("15.00"),
    )

    try:
        # ACT
        rows_inserted = load_raw_products(
            [product],
            pipeline_run_id,
            batch_id,
        )

        # ASSERT
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.Products
            WHERE BatchID = ?
              AND ProductID = ?;
            """,
            str(batch_id),
            product.product_id,
        )

        count = cursor.fetchone()[0]

        assert rows_inserted == 1
        assert count == 1

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.Products
            WHERE BatchID = ?;
            """,
            str(batch_id),
        )

        warehouse_connection.commit()

def test_same_batch_product_is_not_inserted_twice(
    deployed_warehouse,
    warehouse_connection,
):
    batch_id = uuid4()
    product = make_product()

    try:
        first_run_id = uuid4()

        first_rows = load_raw_products(
            [product],
            first_run_id,
            batch_id,
        )

        second_run_id = uuid4()

        second_rows = load_raw_products(
            [product],
            second_run_id,
            batch_id,
        )

        assert first_rows == 1
        assert second_rows == 0

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.Products
            WHERE BatchID = ?
              AND ProductID = ?;
            """,
            batch_id,
            product.product_id,
        )

        count = cursor.fetchone()[0]

        assert count == 1

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.Products
            WHERE BatchID = ?;
            """,
            batch_id,
        )

        warehouse_connection.commit()

def test_same_product_can_exist_in_different_batches(
    deployed_warehouse,
    warehouse_connection,
):
    batch_id1 = uuid4()
    batch_id2 = uuid4()

    product = make_product()

    try:
        first_run_id = uuid4()

        first_rows = load_raw_products(
            [product],
            first_run_id,
            batch_id1,
        )

        second_run_id = uuid4()

        second_rows = load_raw_products(
            [product],
            second_run_id,
            batch_id2,
        )

        assert first_rows == 1
        assert second_rows == 1

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.Products
            WHERE ProductID = ?
              AND BatchID IN (?, ?);
            """,
            product.product_id,
            batch_id1,
            batch_id2,
        )

        count = cursor.fetchone()[0]

        assert count == 2

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.Products
            WHERE BatchID IN (?, ?);
            """,
            batch_id1,
            batch_id2,
        )

        warehouse_connection.commit()