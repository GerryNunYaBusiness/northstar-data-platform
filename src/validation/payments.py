from ingestion.payments import PaymentRecord


VALID_PAYMENT_METHODS = {
    "CreditCard",
    "DebitCard",
    "PayPal",
    "BankTransfer",
}

VALID_PAYMENT_STATUSES = {
    "Pending",
    "Completed",
    "Failed",
    "Refunded",
}


def validate_payment_fields(
    payment: PaymentRecord,
) -> list[str]:
    failures = []

    if payment.payment_id <= 0:
        failures.append(
            "PaymentID must be greater than zero"
        )

    if payment.order_id <= 0:
        failures.append(
            "OrderID must be greater than zero"
        )

    if payment.payment_date is None:
        failures.append(
            "PaymentDate is required"
        )

    if payment.payment_method not in VALID_PAYMENT_METHODS:
        failures.append(
            "Invalid payment method"
        )

    if payment.amount <= 0:
        failures.append(
            "Amount must be greater than zero"
        )

    if payment.status not in VALID_PAYMENT_STATUSES:
        failures.append(
            "Invalid payment status"
        )

    return failures