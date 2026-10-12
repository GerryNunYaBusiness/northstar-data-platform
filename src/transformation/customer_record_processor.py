from uuid import UUID

from ingestion.customers import CustomerRecord
from pipeline_framework.context import PipelineContext

# Adjust these imports to the actual modules in your project.
from ingestion.customers import (
    validate_customers,
    get_valid_customers,
    quarantine_customer_errors,
)
from monitoring.pipeline_runs import pipeline_stage
from settings import get_customer_invalid_rate_threshold
from exceptions import DataQualityError


def process_customer_records(
    customers: list[CustomerRecord],
    context: PipelineContext,
) -> list[CustomerRecord]:

    # ---------------------------------------------
    # Validate Customers
    # ---------------------------------------------
    with pipeline_stage(
        context.pipeline_run_id,
        "customers_validate",
    ) as stage:
        validation_errors = validate_customers(customers)
        stage["rows_processed"] = len(customers)

    # ---------------------------------------------
    # Identify invalid Customers
    # ---------------------------------------------
    invalid_customer_ids = {
        error.customer.customer_id
        for error in validation_errors
    }

    # ---------------------------------------------
    # Quarantine Invalid Customers
    # ---------------------------------------------
    if validation_errors:
        with pipeline_stage(
            context.pipeline_run_id,
            "customers_quarantine",
        ) as stage:
            quarantine_customer_errors(
                validation_errors,
                context.pipeline_run_id,
            )
            stage["rows_processed"] = len(validation_errors)

    # ---------------------------------------------
    # Calculate Invalid Rate
    # ---------------------------------------------
    invalid_rate = (
        len(invalid_customer_ids) / len(customers)
        if customers
        else 0
    )

    threshold = get_customer_invalid_rate_threshold()

    if invalid_rate > threshold:
        raise DataQualityError(
            "Customer invalid rate "
            f"{invalid_rate:.2%} exceeds threshold "
            f"{threshold:.2%}"
        )

    # ---------------------------------------------
    # Return Valid Records Only
    # ---------------------------------------------
    return get_valid_customers(
        customers,
        validation_errors,
    )