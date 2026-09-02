import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from database import (
    get_source_connection,
    get_warehouse_connection,
)

@dataclass
class CustomerRecord:
    customer_id: int
    first_name: str | None
    last_name: str | None
    email: str | None
    phone: str | None
    created_at: datetime | None

@dataclass
class CustomerValidationError:
    customer: CustomerRecord
    rule: str
    message: str

def raw_customer_batch_exists(
    connection,
    batch_id,
) -> bool:
    row = connection.execute(
        """
        SELECT TOP (1) 1
        FROM raw.Customers AS RC
        WHERE RC.BatchID = ?
        """,
        str(batch_id),
    ).fetchone()

    return row is not None

def extract_customers() -> list[CustomerRecord]:
    customers: list[CustomerRecord] = []

    with get_source_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                C.CustomerID,
                C.FirstName,
                C.LastName,
                C.Email,
                C.Phone,
                C.CreatedAt
            FROM dbo.Customers C
            ORDER BY C.CustomerID;
        """)

        for row in cursor.fetchall():
            customers.append(
                CustomerRecord(
                    customer_id=row.CustomerID,
                    first_name=row.FirstName,
                    last_name=row.LastName,
                    email=row.Email,
                    phone=row.Phone,
                    created_at=row.CreatedAt,
                )
            )

    return customers

def validate_customers(
    customers: list[CustomerRecord],
) -> list[CustomerValidationError]:

    errors: list[CustomerValidationError] = []

    seen_customer_ids: set[int] = set()

    for customer in customers:

        if customer.customer_id in seen_customer_ids:
            errors.append(
                CustomerValidationError(
                    customer=customer,
                    rule="DUPLICATE_CUSTOMER_ID",
                    message=(
                        f"Duplicate CustomerID="
                        f"{customer.customer_id}"
                    ),
                )
            )

        seen_customer_ids.add(customer.customer_id)

        if not customer.first_name:
            errors.append(
                CustomerValidationError(
                    customer=customer,
                    rule="FIRST_NAME_REQUIRED",
                    message="FirstName is required",
                )
            )

        if not customer.last_name:
            errors.append(
                CustomerValidationError(
                    customer=customer,
                    rule="LAST_NAME_REQUIRED",
                    message="LastName is required",
                )
            )

        if customer.email and "@" not in customer.email:
            errors.append(
                CustomerValidationError(
                    customer=customer,
                    rule="EMAIL_FORMAT",
                    message=(
                        f"Invalid email "
                        f"'{customer.email}'"
                    ),
                )
            )

    return errors

def load_raw_customers(
    customers: list[CustomerRecord],
    pipeline_run_id: UUID,
    batch_id: UUID
) -> int:
    if not customers:
        return 0
    
    ingested_at = datetime.now(timezone.utc)

    rows = [
        (
            customer.customer_id,
            customer.first_name,
            customer.last_name,
            customer.email,
            customer.phone,
            customer.created_at,
            ingested_at,
            str(pipeline_run_id),
            str(batch_id),
            calculate_customer_hash(customer),
        )
        for customer in customers
    ]

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.fast_executemany = True

        cursor.executemany(
            """
            INSERT INTO raw.Customers
            (
                CustomerID,
                FirstName,
                LastName,
                Email,
                Phone,
                CreatedAt,
                IngestedAt,
                PipelineRunID,
                BatchID,
                RecordHash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?);
            """,
            rows,
        )

        connection.commit()

    return len(rows)

def quarantine_customer_errors(
    errors: list[CustomerValidationError],
    pipeline_run_id: UUID,
) -> int:

    if not errors:
        return 0

    rows = [
        (
            str(pipeline_run_id),
            error.customer.customer_id,
            error.customer.first_name,
            error.customer.last_name,
            error.customer.email,
            error.customer.phone,
            error.customer.created_at,
            error.rule,
            error.message,
        )
        for error in errors
    ]

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.fast_executemany = True

        cursor.executemany(
            """
            INSERT INTO ops.CustomerQuarantine
            (
                PipelineRunID,
                CustomerID,
                FirstName,
                LastName,
                Email,
                Phone,
                CreatedAt,
                ValidationRule,
                ValidationMessage
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
            """,
            rows,
        )

        connection.commit()

    return len(rows)

def get_valid_customers(
    customers: list[CustomerRecord],
    errors: list[CustomerValidationError],
) -> list[CustomerRecord]:

    invalid_customer_ids = {
        error.customer.customer_id
        for error in errors
    }

    return [
        customer
        for customer in customers
        if customer.customer_id not in invalid_customer_ids
    ]

def calculate_customer_hash(
    customer: CustomerRecord,
) -> bytes:

    hash_input = "|".join(
        [
            customer.first_name or "",
            customer.last_name or "",
            customer.email or "",
            customer.phone or "",
        ]
    )

    return hashlib.sha256(
        hash_input.encode("utf-8")
    ).digest()