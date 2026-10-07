from dataclasses import dataclass

from ingestion.orders import OrderRecord


@dataclass(frozen=True)
class OrderValidationResult:
    order: OrderRecord
    is_valid: bool
    failure_reason: str | None

VALID_ORDER_STATUSES = {
    "Pending",
    "Processing",
    "Completed",
    "Cancelled",
}


def validate_order_fields(
    order: OrderRecord,
) -> list[str]:
    failures = []

    if order.order_id <= 0:
        failures.append("OrderID must be greater than zero")

    if order.customer_id <= 0:
        failures.append("CustomerID must be greater than zero")

    if order.order_date is None:
        failures.append("OrderDate is required")

    if order.status not in VALID_ORDER_STATUSES:
        failures.append(
            f"Invalid order status: {order.status}"
        )

    if order.total_amount < 0:
        failures.append(
            "TotalAmount must be greater than or equal to zero"
        )

    return failures