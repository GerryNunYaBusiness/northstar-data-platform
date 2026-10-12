
from ingestion.customers import extract_customers
from ingestion.customers  import (
    validate_customers,
    get_valid_customers,
    quarantine_customer_errors
)
from monitoring.pipeline_runs import pipeline_stage
from settings import get_customer_invalid_rate_threshold
from exceptions import DataQualityError

# Adjust import paths to match your existing project.

def extract_validated_customers(
    pipeline_run_id,
):
    with pipeline_stage(
        pipeline_run_id,
        "customers_extract",
    ) as stage:
        customers = extract_customers()
        stage["rows_processed"] = len(customers)

    with pipeline_stage(
        pipeline_run_id,
        "customers_validate",
    ) as stage:
        errors = validate_customers(customers)
        stage["rows_processed"] = len(customers)

    if errors:
        with pipeline_stage(
            pipeline_run_id,
            "customers_quarantine",
        ) as stage:
            quarantine_customer_errors(
                errors,
                pipeline_run_id,
            )
            stage["rows_processed"] = len(errors)

    invalid_customer_ids = {
        error.customer.customer_id
        for error in errors
    }

    invalid_rate = (
        len(invalid_customer_ids) / len(customers)
        if customers
        else 0
    )

    threshold = get_customer_invalid_rate_threshold()

    if invalid_rate > threshold:
        raise DataQualityError(
            f"Customer invalid rate {invalid_rate:.2%} "
            f"exceeds threshold {threshold:.2%}"
        )

    return get_valid_customers(
        customers,
        errors,
    )