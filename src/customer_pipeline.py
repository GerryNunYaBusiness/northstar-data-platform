from dataclasses import dataclass
from uuid import UUID, uuid4
from database import get_warehouse_connection
from monitoring.pipeline_batches import batch_is_successful
from pipeline_context import PipelineContext
from settings import get_customer_invalid_rate_threshold , get_customer_pipeline_name

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
        ''' Moved code to run_customer_bronze function '''
        # with pipeline_stage(
        #     context.pipeline_run_id,
        #     "extract_customers",
        # ) as stage:

        #     customers = extract_customers()
        #     stage["rows_processed"] = len(customers)

        # stages.append(
        #     StageResult(
        #         name="extract_customers",
        #         status="SUCCESS",
        #         rows_processed=len(customers),
        #     )
        # )

        # with pipeline_stage(
        #     pipeline_run_id,
        #     "validate_customers",
        # ) as stage:

        #     validation_errors = validate_customers(customers)

        #     valid_customers = get_valid_customers(
        #         customers,
        #         validation_errors,
        #     )

        #     total_count = len(customers)

        #     invalid_count = len(
        #         {
        #             error.customer.customer_id
        #             for error in validation_errors
        #         }
        #     )

        #     invalid_rate = (
        #         invalid_count / total_count
        #         if total_count
        #         else 0
        #     )

        #     stage["rows_processed"] = total_count

        # stages.append(
        #     StageResult(
        #         name="validate_customers",
        #         status="SUCCESS",
        #         rows_processed=len(customers),
        #     )
        # )

        # with pipeline_stage(
        #     context.pipeline_run_id,
        #     "quarantine_invalid_customers",
        # ) as stage:

        #     quarantined_rows = quarantine_customer_errors(
        #         validation_errors,
        #         context.pipeline_run_id,
        #     )

        #     stage["rows_processed"] = quarantined_rows

        # if invalid_rate > invalid_rate_threshold:
        #     raise ValueError(
        #         "Customer validation failure rate "
        #         f"{invalid_rate:.2%} exceeds configured threshold "
        #         f"{invalid_rate_threshold:.2%}"
        #     )

        # with pipeline_stage(
        #     context.pipeline_run_id,
        #     "load_bronze_customers",
        # ) as stage:
        #     if raw_customer_batch_exists(
        #         get_warehouse_connection(),
        #         context.batch_id,
        #     ):
        #         bronze_rows = 0
        #     else:
        #         bronze_rows = load_raw_customers(
        #             valid_customers,
        #             context.pipeline_run_id,
        #             context.batch_id,
        #     )

        #     stage["rows_processed"] = bronze_rows

        # stages.append(
        #     StageResult(
        #         name="load_bronze_customers",
        #         status="SUCCESS",
        #         rows_processed=bronze_rows,
        #     )
        # )

        silver_result = run_customer_silver(
            context,
        )
        ''' Moved silver customer loading to run_customer_silver function '''
        # with pipeline_stage(
        #     context.pipeline_run_id,
        #     "load_silver_customers",
        # ) as stage:

        #     silver_result = load_silver_customers()

        #     silver_rows = (
        #         silver_result.inserted
        #         + silver_result.updated
        #     )

        #     stage["rows_processed"] = silver_rows

        # stages.append(
        #     StageResult(
        #         name="load_silver_customers",
        #         status="SUCCESS",
        #         rows_processed=silver_rows,
        #         message=(
        #             f"inserted={silver_result.inserted} "
        #             f"updated={silver_result.updated}"
        #         ),
        #     )
        # )

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
        "load_silver_customers",
    ) as stage:
        result = load_silver_customers()

        stage["rows_processed"] = (
            result.inserted
            + result.updated
        )

    return SilverStageResult(
        rows_inserted=result.inserted,
        rows_updated=result.updated,
    )