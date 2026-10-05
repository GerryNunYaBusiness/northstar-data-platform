from datetime import datetime
from decimal import Decimal
from uuid import uuid4
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ingestion.payments import PaymentRecord
from validation.payments import validate_payment_fields    

def make_payment(
    payment_id: int = 990001,
    order_id: int = 990001,
    payment_date=datetime(
                2026, 10, 1, 14, 0
            ),
    payment_method: str = "CreditCard",
    amount: Decimal = Decimal("100.00"),
    status: str = "Completed"
) -> PaymentRecord:
    return PaymentRecord(
        payment_id=payment_id,
        order_id=order_id,
        payment_date=payment_date,
        payment_method=payment_method,
        amount=amount,
        status=status,
    )

def test_valid_payment_has_no_failures():
    payment = make_payment()

    failures = validate_payment_fields(payment)

    assert failures == []


def test_invalid_payment_id():
    payment = make_payment(
        payment_id=0,
    )

    failures = validate_payment_fields(payment)

    assert failures == [
        "PaymentID must be greater than zero"
    ]


def test_invalid_order_id():
    payment = make_payment(
        order_id=0,
    )

    failures = validate_payment_fields(payment)

    assert failures == [
        "OrderID must be greater than zero"
    ]

def test_missing_payment_date():
    payment = make_payment(
        payment_date=None,
    )

    failures = validate_payment_fields(payment)

    assert failures == [
        "PaymentDate is required"
    ]

def test_invalid_payment_method():
    payment = make_payment(
        payment_method="Cash",
    )

    failures = validate_payment_fields(payment)

    assert failures == [
        "Invalid payment method"
    ]

def test_invalid_amount():
    payment = make_payment(
        amount=Decimal("-100.00"),
    )

    failures = validate_payment_fields(payment)

    assert failures == [
        "Amount must be greater than zero"
    ]

def test_invalid_payment_status():
    payment = make_payment(
        status="Unknown",
    )

    failures = validate_payment_fields(payment)

    assert failures == [
        "Invalid payment status"
    ]

def test_multiple_failures():
    payment = make_payment(
        payment_id=0,
        order_id=0,
        payment_date=None,
        payment_method="Cash",
        amount=Decimal("-100.00"),
        status="Unknown",
    )

    failures = validate_payment_fields(payment)

    assert failures == [
        "PaymentID must be greater than zero",
        "OrderID must be greater than zero",
        "PaymentDate is required",
        "Invalid payment method",
        "Amount must be greater than zero",
        "Invalid payment status"
    ]

def test_refunded_payment_with_positive_amount_is_valid():
    payment = make_payment(
        amount=Decimal("100.00"),
        status="Refunded",
    )

    failures = validate_payment_fields(payment)

    assert failures == []