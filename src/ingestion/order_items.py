from dataclasses import dataclass
from decimal import Decimal
import hashlib

from database import (
    get_source_connection,
    get_warehouse_connection,
)


@dataclass(frozen=True)
class OrderItemRecord:
    order_item_id: int
    order_id: int
    product_id: int
    quantity: int
    unit_price: Decimal

def calculate_order_item_hash(
    order_item: OrderItemRecord,
) -> bytes:
    value = "|".join(
        [
            str(order_item.order_id),
            str(order_item.product_id),
            str(order_item.quantity),
            str(order_item.unit_price),
        ]
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).digest()

def extract_order_items() -> list[OrderItemRecord]:
    with get_source_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                OI.OrderItemID,
                OI.OrderID,
                OI.ProductID,
                OI.Quantity,
                OI.UnitPrice
            FROM dbo.OrderItems AS OI;
            """
        )

        return [
            OrderItemRecord(
                order_item_id=row.OrderItemID,
                order_id=row.OrderID,
                product_id=row.ProductID,
                quantity=row.Quantity,
                unit_price=row.UnitPrice,
            )
            for row in cursor.fetchall()
        ]

def load_raw_order_items(
    order_items: list[OrderItemRecord],
    pipeline_run_id,
    batch_id,
) -> int:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.OrderItemBatchStage
            WHERE PipelineRunID = ?;
            """,
            pipeline_run_id,
        )

        if order_items:
            rows = [
                (
                    pipeline_run_id,
                    item.order_item_id,
                    item.order_id,
                    item.product_id,
                    item.quantity,
                    item.unit_price,
                    calculate_order_item_hash(item),
                )
                for item in order_items
            ]

            cursor.fast_executemany = True

            cursor.executemany(
                """
                INSERT INTO raw.OrderItemBatchStage
                (
                    PipelineRunID,
                    OrderItemID,
                    OrderID,
                    ProductID,
                    Quantity,
                    UnitPrice,
                    RecordHash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                rows,
            )

        cursor.execute(
            """
            EXEC raw.usp_LoadOrderItemsForBatch
                @BatchID = ?,
                @PipelineRunID = ?;
            """,
            batch_id,
            pipeline_run_id,
        )

        row = cursor.fetchone()

        connection.commit()

        return row.RowsInserted