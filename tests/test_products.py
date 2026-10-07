from decimal import Decimal
from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
    
from ingestion.products import (
    ProductRecord,
    calculate_product_hash,
)


def make_product(
    *,
    product_name: str = "Northstar Widget",
    category: str | None = "Widgets",
    unit_cost: Decimal = Decimal("10.00"),
    unit_price: Decimal = Decimal("15.00"),
) -> ProductRecord:
    return ProductRecord(
        product_id=1001,
        product_name=product_name,
        category=category,
        unit_cost=unit_cost,
        unit_price=unit_price,
    )

def test_same_product_data_produces_same_hash():
    first = make_product()
    second = make_product()

    assert (
        calculate_product_hash(first)
        == calculate_product_hash(second)
    )

def test_changed_unitprice_changes_hash():
    original = make_product(
        unit_price=Decimal("15.00")
    )

    changed = make_product(
        unit_price=Decimal("20.00")
    )

    assert (
        calculate_product_hash(original)
        != calculate_product_hash(changed)
    )

def test_changed_unitcost_changes_hash():
    original = make_product(
        unit_cost=Decimal("10.00")
    )

    changed = make_product(
        unit_cost=Decimal("15.00")
    )

    assert (
        calculate_product_hash(original)
        != calculate_product_hash(changed)
    )
