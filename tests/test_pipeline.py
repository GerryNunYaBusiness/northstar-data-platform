import sys
from datetime import datetime
from pathlib import Path

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ingestion.customers import (
    CustomerRecord,
    calculate_customer_hash,
    get_valid_customers,
    validate_customers,
)


def make_customer(
    customer_id: int = 1,
    first_name: str | None = "Alice",
    last_name: str | None = "Johnson",
    email: str | None = "alice@example.com",
    phone: str | None = "555-0100",
) -> CustomerRecord:
    return CustomerRecord(
        customer_id=customer_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        created_at=datetime(2026, 1, 1),
    )

def test_valid_customer_has_no_validation_errors():
    customer = make_customer()

    errors = validate_customers([customer])

    assert errors == []

def test_invalid_email_is_detected():
    customer = make_customer(
        email="not-an-email"
    )

    errors = validate_customers([customer])

    assert len(errors) == 1
    assert errors[0].rule == "EMAIL_FORMAT"
    assert errors[0].customer.customer_id == 1

def test_missing_first_name_is_detected():
    customer = make_customer(
        first_name=None
    )

    errors = validate_customers([customer])

    assert len(errors) == 1
    assert errors[0].rule == "FIRST_NAME_REQUIRED"

def test_missing_last_name_is_detected():
    customer = make_customer(
        last_name=None
    )

    errors = validate_customers([customer])

    assert len(errors) == 1
    assert errors[0].rule == "LAST_NAME_REQUIRED"

def test_customer_can_have_multiple_validation_errors():
    customer = make_customer(
        first_name=None,
        email="bad-email",
    )

    errors = validate_customers([customer])

    rules = {
        error.rule
        for error in errors
    }

    assert rules == {
        "FIRST_NAME_REQUIRED",
        "EMAIL_FORMAT",
    }

def test_duplicate_customer_id_is_detected():
    first = make_customer(
        customer_id=10,
        email="first@example.com",
    )

    second = make_customer(
        customer_id=10,
        email="second@example.com",
    )

    errors = validate_customers(
        [first, second]
    )

    assert any(
        error.rule == "DUPLICATE_CUSTOMER_ID"
        for error in errors
    )

def test_invalid_customer_is_removed_from_valid_set():
    valid_customer = make_customer(
        customer_id=1,
        email="valid@example.com",
    )

    invalid_customer = make_customer(
        customer_id=2,
        email="invalid-email",
    )

    customers = [
        valid_customer,
        invalid_customer,
    ]

    errors = validate_customers(customers)

    valid_customers = get_valid_customers(
        customers,
        errors,
    )

    assert len(valid_customers) == 1
    assert valid_customers[0].customer_id == 1

def test_same_customer_data_produces_same_hash():
    first = make_customer()
    second = make_customer()

    assert (
        calculate_customer_hash(first)
        == calculate_customer_hash(second)
    )

def test_changed_phone_changes_hash():
    original = make_customer(
        phone="555-0100"
    )

    changed = make_customer(
        phone="555-9999"
    )

    assert (
        calculate_customer_hash(original)
        != calculate_customer_hash(changed)
    )