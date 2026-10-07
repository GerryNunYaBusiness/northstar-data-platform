from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib

from database import get_source_connection, get_warehouse_connection

@dataclass(frozen=True)
class OrderRecord:
    order_id: int
    customer_id: int
    order_date: datetime
    status: str
    total_amount: Decimal

def calculate_order_hash(order: OrderRecord) -> bytes:
    value = "|".join(
        [
            str(order.customer_id),
            order.order_date.isoformat(),
            order.status,
            str(order.total_amount),
        ]
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).digest()

def extract_orders() -> list[OrderRecord]:
    with get_source_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                O.OrderID,
                O.CustomerID,
                O.OrderDate,
                O.[Status],
                O.TotalAmount
            FROM dbo.Orders AS O;
            """
        )

        return [
            OrderRecord(
                order_id=row.OrderID,
                customer_id=row.CustomerID,
                order_date=row.OrderDate,
                status=row.Status,
                total_amount=row.TotalAmount,
            )
            for row in cursor.fetchall()
        ]

def load_raw_orders(
    orders: list[OrderRecord],
    pipeline_run_id,
    batch_id,
) -> int:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.OrderBatchStage
            WHERE PipelineRunID = ?;
            """,
            pipeline_run_id,
        )

        if orders:
            rows = [
                (
                    pipeline_run_id,
                    order.order_id,
                    order.customer_id,
                    order.order_date,
                    order.status,
                    order.total_amount,
                    calculate_order_hash(order),
                )
                for order in orders
            ]

            cursor.fast_executemany = True

            cursor.executemany(
                """
                INSERT INTO raw.OrderBatchStage
                (
                    PipelineRunID,
                    OrderID,
                    CustomerID,
                    OrderDate,
                    [Status],
                    TotalAmount,
                    RecordHash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                rows,
            )

        cursor.execute(
            """
            EXEC raw.usp_LoadOrdersForBatch
                @BatchID = ?,
                @PipelineRunID = ?;
            """,
            batch_id,
            pipeline_run_id,
        )

        row = cursor.fetchone()

        connection.commit()

        return row.RowsInserted