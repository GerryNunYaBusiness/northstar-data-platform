from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from ingestion.payments import (
    PaymentRecord,
    load_raw_payments,
)
from transformation.payments import load_silver_payments


def test_quarantined_payment_is_promoted_after_order_becomes_available(
    warehouse_connection,
):
    """
    A valid Payment whose Order is missing should:

    1. Load successfully into Bronze.
    2. Be quarantined because its Order is missing.
    3. Not be promoted into Silver.
    4. Become promotable when the Order becomes available.
    5. Retain its original quarantine record as historical evidence.
    """

    payment_id = 980101
    order_id = 980101
    customer_id = 980101

    batch_id = uuid4()
    first_pipeline_run_id = uuid4()
    second_pipeline_run_id = uuid4()

    payment = PaymentRecord(
        payment_id=payment_id,
        order_id=order_id,
        payment_date=datetime(
            2026, 10, 5, 12, 0
        ),
        payment_method="CreditCard",
        amount=Decimal("100.00"),
        status="Completed",
    )

    cursor = warehouse_connection.cursor()

    try:
        # ---------------------------------------------------------
        # Arrange
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.PaymentQuarantine
            WHERE PaymentID = ?;

            DELETE FROM silver.Payments
            WHERE PaymentID = ?;

            DELETE FROM raw.Payments
            WHERE PaymentID = ?;

            DELETE FROM silver.Orders
            WHERE OrderID = ?;

            DELETE FROM silver.Customers
            WHERE CustomerID = ?;
            """,
            payment_id,
            payment_id,
            payment_id,
            order_id,
            customer_id,
        )

        warehouse_connection.commit()

        # ---------------------------------------------------------
        # Act 1:
        # Load the Payment into Bronze while its Order is missing.
        # ---------------------------------------------------------

        rows_inserted = load_raw_payments(
            [payment],
            first_pipeline_run_id,
            batch_id,
        )

        assert rows_inserted == 1

        first_result = load_silver_payments(
            first_pipeline_run_id,
            batch_id,
        )

        # ---------------------------------------------------------
        # Assert 1:
        # Payment should be quarantined and not promoted.
        # ---------------------------------------------------------

        assert first_result.rows_inserted == 0
        assert first_result.rows_updated == 0
        assert first_result.rows_quarantined == 1

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM silver.Payments
            WHERE PaymentID = ?;
            """,
            payment_id,
        )

        assert cursor.fetchone()[0] == 0

        cursor.execute(
            """
            SELECT
                FailureReason
            FROM ops.PaymentQuarantine
            WHERE BatchID = ?
              AND PaymentID = ?;
            """,
            batch_id,
            payment_id,
        )

        quarantine_row = cursor.fetchone()

        assert quarantine_row is not None

        assert (
            "OrderID does not exist in silver.Orders"
            in quarantine_row.FailureReason
        )

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.PaymentQuarantine
            WHERE BatchID = ?
              AND PaymentID = ?;
            """,
            batch_id,
            payment_id,
        )

        assert cursor.fetchone()[0] == 1

        # ---------------------------------------------------------
        # Act 2:
        # Recover the dependency.
        #
        # silver.Orders requires a CustomerID, so create the
        # synthetic Customer first.
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
                'Payment',
                'IntegrationTest',
                'payment980101@example.com',
                '555-980-0101',
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
                100.00,
                ?,
                SYSUTCDATETIME()
            );
            """,
            order_id,
            customer_id,
            datetime(
                2026, 10, 5, 11, 30
            ),
            bytes(32),
        )

        warehouse_connection.commit()

        # ---------------------------------------------------------
        # Act 3:
        # Retry Silver processing for the SAME logical batch,
        # but with a NEW execution attempt.
        # ---------------------------------------------------------

        recovery_result = load_silver_payments(
            second_pipeline_run_id,
            batch_id,
        )

        # ---------------------------------------------------------
        # Assert 2:
        # The Payment should now be promotable.
        # ---------------------------------------------------------

        assert recovery_result.rows_inserted == 1
        assert recovery_result.rows_updated == 0
        assert recovery_result.rows_quarantined == 0

        cursor.execute(
            """
            SELECT
                OrderID,
                PaymentDate,
                PaymentMethod,
                Amount,
                [Status]
            FROM silver.Payments
            WHERE PaymentID = ?;
            """,
            payment_id,
        )

        silver_row = cursor.fetchone()

        assert silver_row is not None

        assert silver_row.OrderID == payment.order_id
        assert silver_row.PaymentDate == payment.payment_date
        assert silver_row.PaymentMethod == payment.payment_method
        assert silver_row.Amount == payment.amount
        assert silver_row.Status == payment.status

        # ---------------------------------------------------------
        # Assert 3:
        # Recovery must not erase historical quarantine evidence.
        # ---------------------------------------------------------

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.PaymentQuarantine
            WHERE BatchID = ?
              AND PaymentID = ?;
            """,
            batch_id,
            payment_id,
        )

        assert cursor.fetchone()[0] == 1

    finally:
        # ---------------------------------------------------------
        # Cleanup.
        #
        # Delete dependent records before parent records.
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.PaymentQuarantine
            WHERE PaymentID = ?;

            DELETE FROM silver.Payments
            WHERE PaymentID = ?;

            DELETE FROM raw.Payments
            WHERE PaymentID = ?;

            DELETE FROM silver.Orders
            WHERE OrderID = ?;

            DELETE FROM silver.Customers
            WHERE CustomerID = ?;
            """,
            payment_id,
            payment_id,
            payment_id,
            order_id,
            customer_id,
        )

        warehouse_connection.commit()


def test_invalid_payment_is_quarantined_with_all_failure_reasons(
    warehouse_connection,
):
    """
    A Payment with multiple field/domain failures should produce
    one quarantine record containing all applicable failure reasons.

    Referential validation should not add a secondary missing-Order
    failure when the Payment already fails field/domain validation.
    """

    payment_id = 980102
    order_id = 980102

    batch_id = uuid4()
    pipeline_run_id = uuid4()

    payment = PaymentRecord(
        payment_id=payment_id,
        order_id=order_id,
        payment_date=datetime(
            2026, 10, 5, 12, 0
        ),
        payment_method="GoldBars",
        amount=Decimal("-50.00"),
        status="Exploded",
    )

    cursor = warehouse_connection.cursor()

    try:
        # ---------------------------------------------------------
        # Arrange
        # ---------------------------------------------------------

        cursor.execute(
            """
            DELETE FROM ops.PaymentQuarantine
            WHERE PaymentID = ?;

            DELETE FROM silver.Payments
            WHERE PaymentID = ?;

            DELETE FROM raw.Payments
            WHERE PaymentID = ?;

            DELETE FROM silver.Orders
            WHERE OrderID = ?;
            """,
            payment_id,
            payment_id,
            payment_id,
            order_id,
        )

        warehouse_connection.commit()

        # ---------------------------------------------------------
        # Act:
        # Bronze should preserve the invalid business values.
        # ---------------------------------------------------------

        rows_inserted = load_raw_payments(
            [payment],
            pipeline_run_id,
            batch_id,
        )

        assert rows_inserted == 1

        result = load_silver_payments(
            pipeline_run_id,
            batch_id,
        )

        # ---------------------------------------------------------
        # Assert:
        # One bad source record -> one quarantine record.
        # ---------------------------------------------------------

        assert result.rows_inserted == 0
        assert result.rows_updated == 0
        assert result.rows_quarantined == 1

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM silver.Payments
            WHERE PaymentID = ?;
            """,
            payment_id,
        )

        assert cursor.fetchone()[0] == 0

        cursor.execute(
            """
            SELECT
                FailureReason
            FROM ops.PaymentQuarantine
            WHERE BatchID = ?
              AND PaymentID = ?;
            """,
            batch_id,
            payment_id,
        )

        quarantine_row = cursor.fetchone()

        assert quarantine_row is not None

        assert (
            "Invalid payment method"
            in quarantine_row.FailureReason
        )

        assert (
            "Amount must be greater than zero"
            in quarantine_row.FailureReason
        )

        assert (
            "Invalid payment status"
            in quarantine_row.FailureReason
        )

        # This is important: because field/domain validation failed,
        # we do not want a cascading referential failure.
        assert (
            "OrderID does not exist in silver.Orders"
            not in quarantine_row.FailureReason
        )

        # Multiple failures belong to ONE quarantine record.
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM ops.PaymentQuarantine
            WHERE BatchID = ?
              AND PaymentID = ?;
            """,
            batch_id,
            payment_id,
        )

        assert cursor.fetchone()[0] == 1

    finally:
        cursor.execute(
            """
            DELETE FROM ops.PaymentQuarantine
            WHERE PaymentID = ?;

            DELETE FROM silver.Payments
            WHERE PaymentID = ?;

            DELETE FROM raw.Payments
            WHERE PaymentID = ?;

            DELETE FROM silver.Orders
            WHERE OrderID = ?;
            """,
            payment_id,
            payment_id,
            payment_id,
            order_id,
        )

        warehouse_connection.commit()