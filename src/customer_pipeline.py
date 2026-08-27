from dataclasses import dataclass
import uuid
from settings import get_customer_invalid_rate_threshold

from ingestion.customers import (
    extract_customers,
    get_valid_customers,
    load_raw_customers,
    quarantine_customer_errors,
    validate_customers,
)

from transformation.customers import load_silver_customers

from monitoring.pipeline_runs import (
    complete_pipeline_run,
    pipeline_stage,
    start_pipeline_run,
)

invalid_rate_threshold = (
    get_customer_invalid_rate_threshold()
)

@dataclass
class StageResult:
    name: str
    status: str
    rows_processed: int = 0
    message: str | None = None


@dataclass
class CustomerPipelineResult:
    pipeline_run_id: str
    status: str
    stages: list[StageResult]


def run_customer_pipeline() -> CustomerPipelineResult:
    pipeline_run_id = uuid.uuid4()
    stages: list[StageResult] = []

    start_pipeline_run(
        pipeline_run_id,
        "customer_pipeline",
    )

    try:

        with pipeline_stage(
            pipeline_run_id,
            "extract_customers",
        ) as stage:

            customers = extract_customers()
            stage["rows_processed"] = len(customers)

        stages.append(
            StageResult(
                name="extract_customers",
                status="SUCCESS",
                rows_processed=len(customers),
            )
        )

        with pipeline_stage(
            pipeline_run_id,
            "validate_customers",
        ) as stage:

            validation_errors = validate_customers(customers)

            valid_customers = get_valid_customers(
                customers,
                validation_errors,
            )

            total_count = len(customers)

            invalid_count = len(
                {
                    error.customer.customer_id
                    for error in validation_errors
                }
            )

            invalid_rate = (
                invalid_count / total_count
                if total_count
                else 0
            )

            stage["rows_processed"] = total_count

        stages.append(
            StageResult(
                name="validate_customers",
                status="SUCCESS",
                rows_processed=len(customers),
            )
        )

        with pipeline_stage(
            pipeline_run_id,
            "quarantine_invalid_customers",
        ) as stage:

            quarantined_rows = quarantine_customer_errors(
                validation_errors,
                pipeline_run_id,
            )

            stage["rows_processed"] = quarantined_rows

        if invalid_rate > invalid_rate_threshold:
            raise ValueError(
                "Customer validation failure rate "
                f"{invalid_rate:.2%} exceeds configured threshold "
                f"{invalid_rate_threshold:.2%}"
            )

        with pipeline_stage(
            pipeline_run_id,
            "load_bronze_customers",
        ) as stage:

            bronze_rows = load_raw_customers(
                valid_customers,
                pipeline_run_id,
            )

            stage["rows_processed"] = bronze_rows

        stages.append(
            StageResult(
                name="load_bronze_customers",
                status="SUCCESS",
                rows_processed=bronze_rows,
            )
        )

        with pipeline_stage(
            pipeline_run_id,
            "load_silver_customers",
        ) as stage:

            silver_result = load_silver_customers()

            silver_rows = (
                silver_result.inserted
                + silver_result.updated
            )

            stage["rows_processed"] = silver_rows

        stages.append(
            StageResult(
                name="load_silver_customers",
                status="SUCCESS",
                rows_processed=silver_rows,
                message=(
                    f"inserted={silver_result.inserted} "
                    f"updated={silver_result.updated}"
                ),
            )
        )

        complete_pipeline_run(
            pipeline_run_id,
            "SUCCESS",
        )

        return CustomerPipelineResult(
            pipeline_run_id=str(pipeline_run_id),
            status="SUCCESS",
            stages=stages,
        )

    except Exception as exc:

        complete_pipeline_run(
            pipeline_run_id,
            "FAILED",
            error_message=str(exc),
        )

        raise
