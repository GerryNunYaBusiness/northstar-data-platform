from dataclasses import dataclass
from uuid import UUID, uuid4
from database import get_warehouse_connection
from monitoring.pipeline_batches import batch_is_successful
from pipeline_context import PipelineContext
from settings import get_customer_invalid_rate_threshold , get_customer_pipeline_name

from exceptions import InjectedPipelineFailure
from settings import get_test_failure_stage

from ingestion.customers import (
    extract_customers,
    get_valid_customers,
    load_raw_customers,
    quarantine_customer_errors,
    raw_customer_batch_exists,
    validate_customers,
)

from transformation.customers import load_silver_customers

from monitoring.pipeline_runs import (
    complete_pipeline_run,
    pipeline_stage,
    start_pipeline_run,
)

from monitoring.pipeline_batches import (
    begin_or_retry_batch,
    complete_batch,
)

from exceptions import DataQualityError, TransientPipelineError

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
    pipeline_run_id: UUID
    status: str
    batch_id: UUID
    stages: list[StageResult]

@dataclass(frozen=True)
class BronzeStageResult:
    rows_processed: int
    stages: list[StageResult]

@dataclass(frozen=True)
class SilverStageResult:
    rows_inserted: int
    rows_updated: int

    @property
    def rows_processed(self) -> int:
        return self.rows_inserted + self.rows_updated

def load_bronze_for_batch(
    customers,
    pipeline_run_id,
    batch_id,
):
    if batch_is_successful(batch_id):
        return 0

    return load_raw_customers(
        customers,
        pipeline_run_id,
        batch_id,
    )

def run_customer_pipeline(
    batch_id: UUID | None = None,
    pipeline_run_id: UUID | None = None,
) -> CustomerPipelineResult:
    
    if batch_id is None:
        batch_id = uuid4()
    if pipeline_run_id is None:
        pipeline_run_id = uuid4()

    context = PipelineContext(
        pipeline_run_id=pipeline_run_id,
        batch_id=batch_id,
    )


    pipeline_name = get_customer_pipeline_name()


    start_pipeline_run(
        pipeline_run_id=context.pipeline_run_id,
        pipeline_name=pipeline_name,
    )

    stages: list[StageResult] = []

    # start_pipeline_run(
    #     pipeline_run_id,
    #     "customer_pipeline",
    # )
    batch_started = False

    try:
        begin_or_retry_batch(
            batch_id=context.batch_id,
            pipeline_name=pipeline_name,
        )

        batch_started = True
        bronze_result = run_customer_bronze(
            context,
        )

        silver_result = run_customer_silver(
            context,
        )

        complete_batch(
            batch_id=context.batch_id,
            status="SUCCESS",
            rows_processed=bronze_result.rows_processed,
        )

        complete_pipeline_run(
            context.pipeline_run_id,
            "SUCCESS",
        )

        return CustomerPipelineResult(
            pipeline_run_id=context.pipeline_run_id,
            status="SUCCESS",
            batch_id=context.batch_id,
            stages=stages,
        )

    except Exception as exc:

        if batch_started:
            complete_batch(
                batch_id=context.batch_id,
                status="FAILED",
                error_message=str(exc),
            )

        complete_pipeline_run(
            context.pipeline_run_id,
            "FAILED",
            error_message=str(exc),
        )

        raise


def run_customer_bronze(
    context: PipelineContext,
) -> BronzeStageResult:
    stages: list[StageResult] = []

    # Use for manual testing of simulated Bronze pipeline failure
    # raise TransientPipelineError(
    #     "Simulated transient infrastructure failure."
    # )
    with pipeline_stage(
        context.pipeline_run_id,
        "customer_bronze",
    ) as stage:
        if get_test_failure_stage() == "bronze":
            raise InjectedPipelineFailure(
                "Controlled Bronze failure requested by "
                "NORTHSTAR_TEST_FAILURE_STAGE."
            )
        
    with pipeline_stage(
        context.pipeline_run_id,
        "extract",
    ) as stage:
        customers = extract_customers()
        stage["rows_processed"] = len(customers)

    with pipeline_stage(
        context.pipeline_run_id,
        "validate",
    ) as stage:
        validation_errors = validate_customers(customers)
        invalid_customer_ids = {
            error.customer.customer_id
            for error in validation_errors
        }

        stage["rows_processed"] = len(customers)

    if validation_errors:
        with pipeline_stage(
            context.pipeline_run_id,
            "quarantine_invalid_customers",
        ) as stage:
            quarantine_customer_errors(
                validation_errors,
                context.pipeline_run_id,
            )
            stage["rows_processed"] = len(validation_errors)

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

    valid_customers = get_valid_customers(
        customers,
        validation_errors,
    )

    with pipeline_stage(
        context.pipeline_run_id,
        "load_bronze_customers",
    ) as stage:
        rows_inserted = load_raw_customers(
            valid_customers,
            context.pipeline_run_id,
            context.batch_id,
        )
        stage["rows_processed"] = rows_inserted

    return BronzeStageResult(
        rows_processed=rows_inserted,
        stages=stages,
    )

def run_customer_silver(
    context: PipelineContext,
) -> SilverStageResult:
    with pipeline_stage(
        context.pipeline_run_id,
        "customer_silver",
    ) as stage:
        if get_test_failure_stage() == "silver":
            raise InjectedPipelineFailure(
                "Controlled Silver failure requested by "
                "NORTHSTAR_TEST_FAILURE_STAGE."
            )
        
        result = load_silver_customers(
            context.pipeline_run_id,
            context.batch_id,
        )

        stage["rows_processed"] = (
            result.rows_inserted
            + result.rows_updated
        )

    return SilverStageResult(
        rows_inserted=result.rows_inserted,
        rows_updated=result.rows_updated,
    )
