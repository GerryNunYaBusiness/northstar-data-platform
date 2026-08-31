import os

def get_customer_pipeline_name() -> str:
    return os.getenv(
        "NORTHSTAR_CUSTOMER_PIPELINE_NAME",
        "customer_pipeline"
    )

def get_customer_invalid_rate_threshold() -> float:
    raw_value = os.getenv(
        "NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD",
        "0.05",
    )

    try:
        threshold = float(raw_value)
    except ValueError as exc:
        raise ValueError(
            "NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD "
            f"must be numeric, received '{raw_value}'"
        ) from exc

    if not 0 <= threshold <= 1:
        raise ValueError(
            "NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD "
            "must be between 0 and 1"
        )

    return threshold

def get_database_retry_attempts() -> int:
    raw_value = os.getenv(
        "NORTHSTAR_DATABASE_RETRY_ATTEMPTS",
        "3",
    )

    attempts = int(raw_value)

    if attempts < 1:
        raise ValueError(
            "NORTHSTAR_DATABASE_RETRY_ATTEMPTS "
            "must be at least 1"
        )

    return attempts


def get_database_retry_delay_seconds() -> float:
    raw_value = os.getenv(
        "NORTHSTAR_DATABASE_RETRY_DELAY_SECONDS",
        "2",
    )

    delay = float(raw_value)

    if delay < 0:
        raise ValueError(
            "NORTHSTAR_DATABASE_RETRY_DELAY_SECONDS "
            "cannot be negative"
        )

    return delay