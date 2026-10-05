from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from ingestion.payments import (
    PaymentRecord,
    load_raw_payments,
)

def make_payment(
    payment_id: int = 980001,
) -> PaymentRecord:
    return PaymentRecord(
        payment_id=payment_id,
        order_id=980001,
        payment_date=datetime(
            2026, 10, 1, 14, 0
        ),
        payment_method="CreditCard",
        amount=Decimal("100.00"),
        status="Completed",
    )

def test_new_payment_batch_loads_once(
    # deployed_warehouse,
    warehouse_connection,
):
    PAYMENT = make_payment()
    BATCH_ID = uuid4()
    PIPELINE_RUN_ID = uuid4()


    try:
        rows_inserted = load_raw_payments(
            [PAYMENT],
            pipeline_run_id= PIPELINE_RUN_ID,
            batch_id= BATCH_ID,
        )

        assert rows_inserted == 1

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT
                PaymentID,
                OrderID,
                PaymentDate,
                PaymentMethod,
                Amount,
                Status
            FROM raw.Payments
            WHERE BatchID = ?
              AND PaymentId = ?;
            """,
            BATCH_ID,
            PAYMENT.payment_id,
        )

        row = cursor.fetchone()

        assert row is not None
        assert row.OrderID == PAYMENT.order_id
        assert row.PaymentID == PAYMENT.payment_id
        assert row.PaymentDate == PAYMENT.payment_date
        assert row.PaymentMethod == PAYMENT.payment_method
        assert row.Amount == PAYMENT.amount
        assert row.Status == PAYMENT.status

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

def test_same_batch_payment_is_not_inserted_twice(
    # deployed_warehouse,
    warehouse_connection,
):
    PAYMENT = make_payment()
    BATCH_ID = uuid4()

    try:
        first_rows = load_raw_payments(
            [PAYMENT],
            pipeline_run_id=uuid4(),
            batch_id=BATCH_ID,
        )

        second_rows = load_raw_payments(
            [PAYMENT],
            pipeline_run_id=uuid4(),
            batch_id=BATCH_ID,
        )

        assert first_rows == 1
        assert second_rows == 0

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.Payments
            WHERE BatchID = ?
              AND PaymentID = ?;
            """,
            BATCH_ID,
            PAYMENT.payment_id,
        )

        count = cursor.fetchone()[0]

        assert count == 1

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.Payments
            WHERE BatchID = ?;
            """,
            BATCH_ID,
        )

        warehouse_connection.commit()

def test_same_payment_can_exist_in_different_batches(
    # deployed_warehouse,
    warehouse_connection,
):
    PAYMENT = make_payment()

    batch_id1 = uuid4()
    batch_id2 = uuid4()

    try:
        first_rows = load_raw_payments(
            [PAYMENT],
            uuid4(),
            batch_id1,
        )

        second_rows = load_raw_payments(
            [PAYMENT],
            pipeline_run_id=uuid4(),
            batch_id=batch_id2,
        )

        assert first_rows == 1
        assert second_rows == 1

        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM raw.Payments
            WHERE PaymentID = ?
              AND BatchID IN (?, ?);
            """,
            PAYMENT.payment_id,
            batch_id1,
            batch_id2,
        )

        count = cursor.fetchone()[0]

        assert count == 2

    finally:
        cursor = warehouse_connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.Payments
            WHERE BatchID IN (?, ?);
            """,
            batch_id1,
            batch_id2,
        )

        warehouse_connection.commit()