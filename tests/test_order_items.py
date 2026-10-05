from decimal import Decimal
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
    
from ingestion.order_items import (
    OrderItemRecord,
    calculate_order_item_hash,
)


def make_order_item(
    order_id: int = 5001,
    product_id: int = 2001,
    quantity: int = 2,
    unit_price: Decimal = Decimal("25.00"),
) -> OrderItemRecord:
    return OrderItemRecord(
        order_item_id=7001,
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
    )


def test_same_order_item_data_produces_same_hash():
    first = make_order_item()
    second = make_order_item()

    assert (
        calculate_order_item_hash(first)
        == calculate_order_item_hash(second)
    )


def test_order_change_changes_hash():
    first = make_order_item(
        order_id=5001,
    )

    second = make_order_item(
        order_id=5002,
    )

    assert (
        calculate_order_item_hash(first)
        != calculate_order_item_hash(second)
    )


def test_product_change_changes_hash():
    first = make_order_item(
        product_id=2001,
    )

    second = make_order_item(
        product_id=2002,
    )

    assert (
        calculate_order_item_hash(first)
        != calculate_order_item_hash(second)
    )


def test_quantity_change_changes_hash():
    first = make_order_item(
        quantity=2,
    )

    second = make_order_item(
        quantity=3,
    )

    assert (
        calculate_order_item_hash(first)
        != calculate_order_item_hash(second)
    )


def test_unit_price_change_changes_hash():
    first = make_order_item(
        unit_price=Decimal("25.00"),
    )

    second = make_order_item(
        unit_price=Decimal("30.00"),
    )

    assert (
        calculate_order_item_hash(first)
        != calculate_order_item_hash(second)
    )