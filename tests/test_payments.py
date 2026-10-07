from datetime import datetime
from decimal import Decimal
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ingestion.orders import (
    OrderRecord,
    calculate_order_hash,
)

from ingestion.payments import (
    PaymentRecord,
    calculate_payment_hash,
)


def make_payment(
    order_id: int = 5001,
    payment_date: datetime = datetime(
        2026, 10, 1, 14, 0
    ),
    payment_method: str = "CreditCard",
    amount: Decimal = Decimal("100.00"),
    status: str = "Completed",
) -> PaymentRecord:
    return PaymentRecord(
        payment_id=8001,
        order_id=order_id,
        payment_date=payment_date,
        payment_method=payment_method,
        amount=amount,
        status=status,
    )


def test_same_payment_data_produces_same_hash():
    first = make_payment()
    second = make_payment()

    assert (
        calculate_payment_hash(first)
        == calculate_payment_hash(second)
    )


def test_order_change_changes_hash():
    first = make_payment(
        order_id=5001,
    )

    second = make_payment(
        order_id=5002,
    )

    assert (
        calculate_payment_hash(first)
        != calculate_payment_hash(second)
    )


def test_payment_date_change_changes_hash():
    first = make_payment(
        payment_date=datetime(
            2026, 10, 1, 14, 0
        )
    )

    second = make_payment(
        payment_date=datetime(
            2026, 10, 2, 14, 0
        )
    )

    assert (
        calculate_payment_hash(first)
        != calculate_payment_hash(second)
    )


def test_payment_method_change_changes_hash():
    first = make_payment(
        payment_method="CreditCard",
    )

    second = make_payment(
        payment_method="PayPal",
    )

    assert (
        calculate_payment_hash(first)
        != calculate_payment_hash(second)
    )


def test_amount_change_changes_hash():
    first = make_payment(
        amount=Decimal("100.00"),
    )

    second = make_payment(
        amount=Decimal("125.00"),
    )

    assert (
        calculate_payment_hash(first)
        != calculate_payment_hash(second)
    )


def test_status_change_changes_hash():
    first = make_payment(
        status="Completed",
    )

    second = make_payment(
        status="Refunded",
    )

    assert (
        calculate_payment_hash(first)
        != calculate_payment_hash(second)
    )