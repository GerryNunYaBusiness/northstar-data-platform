from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from ingestion.order_items import (
    OrderItemRecord,
    load_raw_order_items,
)

def make_order_item(
    order_item_id=960001,
):
    return OrderItemRecord(
        order_item_id=order_item_id,
        order_id=960001,
        product_id=960001,
        quantity=2,
        unit_price=Decimal("25.00"),
    )

def test_new_orderitem_batch_loads_once(
    deployed_warehouse,
    warehouse_connection,
):
    ORDERITEM = make_order_item()
    BATCH_ID = uuid4()
    PIPELINE_RUN_ID = uuid4()


    try:
        rows_inserted = load_raw_order_items(
            [ORDERITEM],
            pipeline_run_id= PIPELINE_RUN_ID,
            batch_id= BATCH_ID,
        )

        assert rows_inserted == 1

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT
                OrderID,
                ProductID,
                Quantity,
                UnitPrice
            FROM raw.OrderItems
            WHERE BatchID = ?
              AND OrderID = ?;
            """,
            BATCH_ID,
            ORDERITEM.order_item_id,
        )

        row = cursor.fetchone()

        assert row is not None
        assert row.OrderID == ORDERITEM.order_item_id
        assert row.ProductID == ORDERITEM.product_id
        assert row.Quantity == ORDERITEM.quantity
        assert row.UnitPrice == ORDERITEM.unit_price

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.OrderItems
            WHERE BatchID = ?;
            """,
            BATCH_ID,
        )

        warehouse_connection.commit()

def test_same_batch_order_is_not_inserted_twice(
    deployed_warehouse,
    warehouse_connection,
):
    ORDERITEM = make_order_item()
    BATCH_ID = uuid4()    

    try:
        first_rows = load_raw_order_items(
            [ORDERITEM],
            pipeline_run_id=uuid4(),
            batch_id=BATCH_ID,
        )

        second_rows = load_raw_order_items(
            [ORDERITEM],
            pipeline_run_id=uuid4(),
            batch_id=BATCH_ID,
        )

        assert first_rows == 1
        assert second_rows == 0

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.OrderItems
            WHERE BatchID = ?
              AND OrderID = ?;
            """,
            BATCH_ID,
            ORDERITEM.order_id,
        )

        count = cursor.fetchone()[0]

        assert count == 1

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.OrderItems
            WHERE BatchID = ?;
            """,
            BATCH_ID,
        )

        warehouse_connection.commit()

def test_same_order_can_exist_in_different_batches(
    deployed_warehouse,
    warehouse_connection,
):
    ORDERITEM = make_order_item()

    batch_id1 = uuid4()
    batch_id2 = uuid4()

    try:
        first_rows = load_raw_order_items(
            [ORDERITEM],
            uuid4(),
            batch_id1,
        )

        second_rows = load_raw_order_items(
            [ORDERITEM],
            pipeline_run_id=uuid4(),
            batch_id=batch_id2,
        )

        assert first_rows == 1
        assert second_rows == 1

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.OrderItems
            WHERE OrderID = ?
              AND BatchID IN (?, ?);
            """,
            ORDERITEM.order_id,
            batch_id1,
            batch_id2,
        )

        count = cursor.fetchone()[0]

        assert count == 2

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.OrderItems
            WHERE BatchID IN (?, ?);
            """,
            batch_id1,
            batch_id2,
        )

        warehouse_connection.commit()