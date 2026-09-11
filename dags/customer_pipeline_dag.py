"""
Airflow DAG for the Northstar customer data pipeline.
"""
from datetime import datetime, timedelta
from multiprocessing import context
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from dataclasses import dataclass
from uuid import UUID

from monitoring.failure_handler import handle_pipeline_failure

import pendulum

from airflow.sdk import (
    ExceptionRetryPolicy,
    RetryAction,
    RetryRule,
    TriggerRule, 
    dag,
    get_current_context,
    task,
)
from customer_pipeline import (
    run_customer_bronze,
    run_customer_silver,
)
from monitoring.pipeline_batches import (
    begin_or_retry_batch,
    complete_batch,
)
from monitoring.pipeline_runs import (
    complete_pipeline_run,
    start_pipeline_run,
)
from pipeline_context import PipelineContext
from settings import get_customer_pipeline_name
from exceptions import DataQualityError, TransientPipelineError

# from monitoring.alerts import (
#     LoggingAlertSink,
#     PipelineFailureContext,
# )

BRONZE_RETRY_POLICY = ExceptionRetryPolicy(
        rules=[
            RetryRule(
                exception=DataQualityError,
                action=RetryAction.FAIL,
                reason="Data-quality failures are not retryable.",
            ),
            # RetryRule(
            #     exception=ConnectionError,
            #     action=RetryAction.RETRY,
            #     retry_delay=timedelta(minutes=1),
            #     reason="Transient connection failure.",
            # ),
            RetryRule(
                exception=TransientPipelineError,
                action=RetryAction.RETRY,
                retry_delay=timedelta(minutes=1),
                reason="Transient pipeline failure.",
            ),
    ]
)

@dag(
    dag_id="northstar_customer_pipeline",
    schedule="0 2 * * *",
    start_date=pendulum.datetime(2026,9,8, tz="America/New_York",    ),
    catchup=False,
    tags=["northstar", "customers"],
)

def northstar_customer_pipeline():

    @task
    def prepare_run() -> dict:
        airflow_context = get_current_context()
        dag_run = airflow_context["dag_run"]

        batch_id = uuid5(
            NAMESPACE_URL,
            f"northstar:{dag_run.run_id}",
        )

        pipeline_run_id = uuid4()
        pipeline_name = get_customer_pipeline_name()

        start_pipeline_run(
            pipeline_run_id,
            pipeline_name,
        )

        begin_or_retry_batch(
            batch_id,
            pipeline_name,
        )

        return {
            "pipeline_run_id": str(pipeline_run_id),
            "batch_id": str(batch_id),
        }

    @task(
        retries=2,
        retry_delay=timedelta(minutes=1),
        retry_policy=BRONZE_RETRY_POLICY,
    )
    def bronze(run_info: dict) -> dict:
        context = PipelineContext(
            pipeline_run_id=UUID(
                run_info["pipeline_run_id"]
            ),
            batch_id=UUID(
                run_info["batch_id"]
            ),
        )

        print(
            "Starting customer Bronze stage "
            f"PipelineRunID={context.pipeline_run_id} "
            f"BatchID={context.batch_id}"
        )

        result = run_customer_bronze(context)

        print(
            "Customer Bronze stage completed "
            f"PipelineRunID={context.pipeline_run_id} "
            f"BatchID={context.batch_id} "
            f"RowsProcessed={result.rows_processed}"
        )

        return {
            **run_info,
            "bronze_rows_processed": result.rows_processed,
        }

    @task(
        retries=2,
        retry_delay=timedelta(minutes=1),
    )
    def silver(run_info: dict) -> dict:
        context = PipelineContext(
            pipeline_run_id=UUID(
                run_info["pipeline_run_id"]
            ),
            batch_id=UUID(
                run_info["batch_id"]
            ),
        )

        result = run_customer_silver(context)

        return {
            **run_info,
            "silver_rows_inserted": result.rows_inserted,
            "silver_rows_updated": result.rows_updated,
        }

    @task
    def complete_success(run_info: dict):
        pipeline_run_id = UUID(
            run_info["pipeline_run_id"]
        )

        batch_id = UUID(
            run_info["batch_id"]
        )

        complete_batch(
            batch_id,
            status="SUCCESS",
            rows_processed=run_info[
                "bronze_rows_processed"
            ],
        )

        complete_pipeline_run(
            pipeline_run_id,
            "SUCCESS",
        )

        print(
            f"PipelineRunID: {pipeline_run_id}"
        )
        print(
            f"BatchID: {batch_id}"
        )
        print("Status: SUCCESS")

    @task(trigger_rule=TriggerRule.ONE_FAILED)
    def complete_failure(run_info: dict):
        handle_pipeline_failure(
            pipeline_name="customer_pipeline",
            pipeline_run_id=UUID(run_info["pipeline_run_id"]),
            batch_id=UUID(run_info["batch_id"]),
            stage_name="airflow",
            error_type="PipelineFailure",
            error_message=(
                "Airflow customer pipeline failed. "
                "See Airflow task logs for the underlying error."
            ),
        )
    # @task(trigger_rule=TriggerRule.ONE_FAILED)
    # def complete_failure(run_info: dict):
    #     pipeline_run_id = UUID(run_info["pipeline_run_id"]        )
    #     batch_id = UUID(run_info["batch_id"]        )

    #     error_message = (
    #         "Airflow customer pipeline failed. "
    #         "See Airflow task logs for the underlying error."
    #     )

    #     complete_batch(
    #         batch_id,
    #         status="FAILED",
    #         error_message=error_message,
    #     )

    #     complete_pipeline_run(
    #         pipeline_run_id,
    #         "FAILED",
    #         error_message=error_message,
    #     )
    #     context = PipelineFailureContext(
    #         pipeline_name="customer_pipeline",
    #         pipeline_run_id=pipeline_run_id,
    #         batch_id=batch_id,
    #         stage_name="airflow",
    #         error_type="PipelineFailure",
    #         error_message=error_message,
    #     )

    #     LoggingAlertSink().send_failure(context)

    

        # print(f"PipelineRunID: {pipeline_run_id}")
        # print(f"BatchID: {batch_id}")
        # print("Status: FAILED")

    run_info = prepare_run()
    bronze_result = bronze(run_info)
    silver_result = silver(bronze_result)
    success_task = complete_success(silver_result)
    failure_task = complete_failure(run_info)

    [bronze_result, silver_result] >> failure_task

northstar_customer_pipeline()