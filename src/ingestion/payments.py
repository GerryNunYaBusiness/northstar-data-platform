from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
import hashlib
from uuid import UUID

from database import (
    get_source_connection,
    get_warehouse_connection,
)


@dataclass(frozen=True)
class PaymentRecord:
    payment_id: int
    order_id: int
    payment_date: datetime
    payment_method: str
    amount: Decimal
    status: str


def calculate_payment_hash(
    payment: PaymentRecord,
) -> bytes:
    value = "|".join(
        [
            str(payment.order_id),
            payment.payment_date.isoformat(),
            payment.payment_method,
            str(payment.amount),
            payment.status,
        ]
    )

    return hashlib.sha256(
        value.encode("utf-8")
    ).digest()


def extract_payments() -> list[PaymentRecord]:
    with get_source_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                P.PaymentID,
                P.OrderID,
                P.PaymentDate,
                P.PaymentMethod,
                P.Amount,
                P.[Status]
            FROM dbo.Payments AS P;
            """
        )

        return [
            PaymentRecord(
                payment_id=row.PaymentID,
                order_id=row.OrderID,
                payment_date=row.PaymentDate,
                payment_method=row.PaymentMethod,
                amount=row.Amount,
                status=row.Status,
            )
            for row in cursor.fetchall()
        ]

def load_raw_payments(
    payments: list[PaymentRecord],
    pipeline_run_id: UUID,
    batch_id: UUID,
) -> int:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        # Remove stale staging rows belonging to a previous
        # attempt using this PipelineRunID.
        cursor.execute(
            """
            DELETE FROM raw.PaymentBatchStage
            WHERE PipelineRunID = ?;
            """,
            pipeline_run_id,
        )

        if payments:
            rows = [
                (
                    pipeline_run_id,
                    payment.payment_id,
                    payment.order_id,
                    payment.payment_date,
                    payment.payment_method,
                    payment.amount,
                    payment.status,
                    calculate_payment_hash(payment),
                )
                for payment in payments
            ]

            cursor.fast_executemany = True

            cursor.executemany(
                """
                INSERT INTO raw.PaymentBatchStage
                (
                    PipelineRunID,
                    PaymentID,
                    OrderID,
                    PaymentDate,
                    PaymentMethod,
                    Amount,
                    [Status],
                    RecordHash
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
                rows,
            )

        cursor.execute(
            """
            EXEC raw.usp_LoadPaymentsForBatch
                @BatchID = ?,
                @PipelineRunID = ?;
            """,
            batch_id,
            pipeline_run_id,
        )

        row = cursor.fetchone()

        connection.commit()

        return row.RowsInserted