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
from validation.order_items import validate_order_item_fields


def make_order_item(
    order_item_id: int = 7001,
    order_id: int = 5001,
    product_id: int = 2001,
    quantity: int = 2,
    unit_price: Decimal = Decimal("25.00"),
) -> OrderItemRecord:
    return OrderItemRecord(
        order_item_id=order_item_id,
        order_id=order_id,
        product_id=product_id,
        quantity=quantity,
        unit_price=unit_price,
    )


def test_valid_order_item_has_no_failures():
    order_item = make_order_item()

    failures = validate_order_item_fields(order_item)

    assert failures == []


def test_invalid_order_item_id():
    order_item = make_order_item(
        order_item_id=0,
    )

    failures = validate_order_item_fields(order_item)

    assert failures == [
        "OrderItemID must be greater than zero"
    ]


def test_invalid_order_id():
    order_item = make_order_item(
        order_id=0,
    )

    failures = validate_order_item_fields(order_item)

    assert failures == [
        "OrderID must be greater than zero"
    ]


def test_invalid_product_id():
    order_item = make_order_item(
        product_id=0,
    )

    failures = validate_order_item_fields(order_item)

    assert failures == [
        "ProductID must be greater than zero"
    ]


def test_zero_quantity_is_invalid():
    order_item = make_order_item(
        quantity=0,
    )

    failures = validate_order_item_fields(order_item)

    assert failures == [
        "Quantity must be greater than zero"
    ]


def test_negative_quantity_is_invalid():
    order_item = make_order_item(
        quantity=-1,
    )

    failures = validate_order_item_fields(order_item)

    assert failures == [
        "Quantity must be greater than zero"
    ]


def test_zero_unit_price_is_invalid():
    order_item = make_order_item(
        unit_price=Decimal("0.00"),
    )

    failures = validate_order_item_fields(order_item)

    assert failures == [
        "UnitPrice must be greater than zero"
    ]


def test_negative_unit_price_is_invalid():
    order_item = make_order_item(
        unit_price=Decimal("-10.00"),
    )

    failures = validate_order_item_fields(order_item)

    assert failures == [
        "UnitPrice must be greater than zero"
    ]


def test_multiple_failures_are_returned():
    order_item = make_order_item(
        order_item_id=0,
        order_id=-1,
        product_id=0,
        quantity=-5,
        unit_price=Decimal("-25.00"),
    )

    failures = validate_order_item_fields(order_item)

    assert failures == [
        "OrderItemID must be greater than zero",
        "OrderID must be greater than zero",
        "ProductID must be greater than zero",
        "Quantity must be greater than zero",
        "UnitPrice must be greater than zero",
    ]