from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from ingestion.orders import (
    OrderRecord,
    load_raw_orders,
)


def make_order(
    order_id: int = 940001,
) -> OrderRecord:
    return OrderRecord(
        order_id=order_id,
        customer_id=1001,
        order_date=datetime(2026, 10, 1, 12, 0),
        status="Completed",
        total_amount=Decimal("125.00"),
    )

def test_new_order_batch_loads_once(
    deployed_warehouse,
    warehouse_connection,
):
    order = make_order()
    batch_id = uuid4()

    try:
        rows_inserted = load_raw_orders(
            [order],
            uuid4(),
            batch_id,
        )

        assert rows_inserted == 1

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT
                OrderID,
                CustomerID,
                [Status],
                TotalAmount
            FROM raw.Orders
            WHERE BatchID = ?
              AND OrderID = ?;
            """,
            batch_id,
            order.order_id,
        )

        row = cursor.fetchone()

        assert row is not None
        assert row.OrderID == order.order_id
        assert row.CustomerID == order.customer_id
        assert row.Status == order.status
        assert row.TotalAmount == order.total_amount

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.Orders
            WHERE BatchID = ?;
            """,
            batch_id,
        )

        warehouse_connection.commit()

def test_same_batch_order_is_not_inserted_twice(
    deployed_warehouse,
    warehouse_connection,
):
    order = make_order()
    batch_id = uuid4()

    try:
        first_rows = load_raw_orders(
            [order],
            uuid4(),
            batch_id,
        )

        second_rows = load_raw_orders(
            [order],
            uuid4(),
            batch_id,
        )

        assert first_rows == 1
        assert second_rows == 0

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.Orders
            WHERE BatchID = ?
              AND OrderID = ?;
            """,
            batch_id,
            order.order_id,
        )

        count = cursor.fetchone()[0]

        assert count == 1

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.Orders
            WHERE BatchID = ?;
            """,
            batch_id,
        )

        warehouse_connection.commit()

def test_same_order_can_exist_in_different_batches(
    deployed_warehouse,
    warehouse_connection,
):
    order = make_order()

    batch_id1 = uuid4()
    batch_id2 = uuid4()

    try:
        first_rows = load_raw_orders(
            [order],
            uuid4(),
            batch_id1,
        )

        second_rows = load_raw_orders(
            [order],
            uuid4(),
            batch_id2,
        )

        assert first_rows == 1
        assert second_rows == 1

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.Orders
            WHERE OrderID = ?
              AND BatchID IN (?, ?);
            """,
            order.order_id,
            batch_id1,
            batch_id2,
        )

        count = cursor.fetchone()[0]

        assert count == 2

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.Orders
            WHERE BatchID IN (?, ?);
            """,
            batch_id1,
            batch_id2,
        )

        warehouse_connection.commit()