from datetime import datetime
from decimal import Decimal
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ingestion.orders import OrderRecord
from validation.orders import validate_order_fields


def make_order(
    order_id: int = 5001,
    customer_id: int = 1001,
    order_date: datetime | None = datetime(2026, 10, 1, 12, 0),
    status: str = "Completed",
    total_amount: Decimal = Decimal("125.00"),
) -> OrderRecord:
    return OrderRecord(
        order_id=order_id,
        customer_id=customer_id,
        order_date=order_date,
        status=status,
        total_amount=total_amount,
    )


def test_valid_order_has_no_validation_failures():
    order = make_order()

    failures = validate_order_fields(order)

    assert failures == []


def test_invalid_order_id_fails_validation():
    order = make_order(
        order_id=-1,
    )

    failures = validate_order_fields(order)

    assert "OrderID must be greater than zero" in failures


def test_invalid_customer_id_fails_validation():
    order = make_order(
        customer_id=-1,
    )

    failures = validate_order_fields(order)

    assert "CustomerID must be greater than zero" in failures


def test_missing_order_date_fails_validation():
    order = make_order(
        order_date=None,
    )

    failures = validate_order_fields(order)

    assert "OrderDate is required" in failures


def test_invalid_status_fails_validation():
    order = make_order(
        status="Banana",
    )

    failures = validate_order_fields(order)

    assert "Invalid order status: Banana" in failures


def test_negative_total_amount_fails_validation():
    order = make_order(
        total_amount=Decimal("-1.00"),
    )

    failures = validate_order_fields(order)

    assert (
        "TotalAmount must be greater than or equal to zero"
        in failures
    )


def test_zero_total_amount_is_valid():
    order = make_order(
        total_amount=Decimal("0.00"),
    )

    failures = validate_order_fields(order)

    assert failures == []


def test_multiple_validation_failures_are_returned():
    order = make_order(
        order_id=-1,
        customer_id=-2,
        order_date=None,
        status="Banana",
        total_amount=Decimal("-50.00"),
    )

    failures = validate_order_fields(order)

    assert len(failures) == 5

    assert "OrderID must be greater than zero" in failures
    assert "CustomerID must be greater than zero" in failures
    assert "OrderDate is required" in failures
    assert "Invalid order status: Banana" in failures
    assert (
        "TotalAmount must be greater than or equal to zero"
        in failures
    )