from ingestion.order_items import OrderItemRecord


def validate_order_item_fields(
    order_item: OrderItemRecord,
) -> list[str]:
    failures = []

    if order_item.order_item_id <= 0:
        failures.append(
            "OrderItemID must be greater than zero"
        )

    if order_item.order_id <= 0:
        failures.append(
            "OrderID must be greater than zero"
        )

    if order_item.product_id <= 0:
        failures.append(
            "ProductID must be greater than zero"
        )

    if order_item.quantity <= 0:
        failures.append(
            "Quantity must be greater than zero"
        )

    if order_item.unit_price <= 0:
        failures.append(
            "UnitPrice must be greater than zero"
        )

    return failures