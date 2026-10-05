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


def make_order(
    customer_id=1001,
    status="Completed",
    total_amount=Decimal("125.00"),
):
    return OrderRecord(
        order_id=5001,
        customer_id=customer_id,
        order_date=datetime(2026, 10, 1, 10, 30),
        status=status,
        total_amount=total_amount,
    )


def test_same_order_data_produces_same_hash():
    first = make_order()
    second = make_order()

    assert calculate_order_hash(first) == calculate_order_hash(second)


def test_status_change_changes_hash():
    first = make_order(status="Pending")
    second = make_order(status="Completed")

    assert calculate_order_hash(first) != calculate_order_hash(second)


def test_total_amount_change_changes_hash():
    first = make_order(total_amount=Decimal("125.00"))
    second = make_order(total_amount=Decimal("150.00"))

    assert calculate_order_hash(first) != calculate_order_hash(second)


def test_customer_change_changes_hash():
    first = make_order(customer_id=1001)
    second = make_order(customer_id=1002)

    assert calculate_order_hash(first) != calculate_order_hash(second)

