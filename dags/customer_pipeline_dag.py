"""
Airflow DAG for the Northstar customer data pipeline.
"""
from datetime import datetime, timedelta
from multiprocessing import context
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5
from dataclasses import dataclass
from uuid import UUID


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

from monitoring.failure_handler import handle_pipeline_failure
from monitoring.alerts import LoggingAlertSink, PipelineFailureContext, create_pipeline_alert_sink
from monitoring.retry_observability import capture_task_retry, capture_task_success

from customer_pipeline import (    run_customer_bronze,    run_customer_silver,)
from monitoring.pipeline_batches import (    begin_or_retry_batch,    complete_batch,)
from monitoring.pipeline_runs import (    complete_pipeline_run,    start_pipeline_run,)

from pipeline_context import PipelineContext
from settings import (get_customer_pipeline_name, get_test_transient_failure_stage, get_test_failure_stage,)
from exceptions import DataQualityError, InjectedPipelineFailure, TransientPipelineError
from monitoring.airflow_failure import (    capture_task_failure,    normalize_failure_details,)

import logging

log = logging.getLogger(__name__)

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

# def capture_task_failure(context):
#     task_instance = context["ti"]
#     exception = context.get("exception")

#     error_type = (
#         type(exception).__name__
#         if exception is not None
#         else "UnknownError"
#     )

#     error_message = (
#         str(exception)
#         if exception is not None
#         else "Task failed without an exception in callback context."
#     )

#     task_instance.xcom_push(
#         key="failure_details",
#         value={
#             "task_id": task_instance.task_id,
#             "error_type": error_type,
#             "error_message": error_message,
#             "dag_run_id": task_instance.run_id,
#             "try_number": task_instance.try_number,
#         },
#     )

@dag(
    dag_id="northstar_customer_pipeline",
    schedule="0 2 * * *",
    start_date=pendulum.datetime(2026,9,8, tz="America/New_York",    ),
    catchup=False,
    tags=["northstar", "customers"],
)

def northstar_customer_pipeline():

    @task(    on_failure_callback=capture_task_failure,)
    def prepare_run() -> dict:
        airflow_context = get_current_context()
        dag_run = airflow_context["dag_run"]

        batch_id = uuid5(
            NAMESPACE_URL,
            f"northstar:{dag_run.run_id}",
        )

        pipeline_run_id = uuid4()
        pipeline_name = get_customer_pipeline_name()

        if get_test_failure_stage() == "prepare_run":
            raise InjectedPipelineFailure(
                "Controlled prepare_run failure requested by "
                "NORTHSTAR_TEST_FAILURE_STAGE."
            )

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
        on_failure_callback=capture_task_failure,
        on_retry_callback=capture_task_retry,
        on_success_callback=capture_task_success,
    )
    def bronze(run_info: dict) -> dict:
        pipeline_context = PipelineContext(
            pipeline_run_id=UUID(
                run_info["pipeline_run_id"]
            ),
            batch_id=UUID(
                run_info["batch_id"]
            ),
        )
        airflow_context  = get_current_context()
        ti = airflow_context["ti"]

        if (
            get_test_transient_failure_stage() == "bronze"
            and ti.try_number == 1
        ):
            raise TransientPipelineError(
                "Controlled transient Bronze failure."
            )


        print(
            "Starting customer Bronze stage "
            f"PipelineRunID={pipeline_context.pipeline_run_id} "
            f"BatchID={pipeline_context.batch_id}"
        )

        result = run_customer_bronze(pipeline_context)

        print(
            "Customer Bronze stage completed "
            f"PipelineRunID={pipeline_context.pipeline_run_id} "
            f"BatchID={pipeline_context.batch_id} "
            f"RowsProcessed={result.rows_processed}"
        )

        return {
            **run_info,
            "bronze_rows_processed": result.rows_processed,
        }

    @task(
        retries=2,
        retry_delay=timedelta(minutes=1),
        on_failure_callback=capture_task_failure,
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
    def complete_failure(run_info: dict | None):
        context = get_current_context()
        ti = context["ti"]

        prepare_failure = ti.xcom_pull(
            task_ids="prepare_run",
            key="failure_details",
        )

        bronze_failure = ti.xcom_pull(
            task_ids="bronze",
            key="failure_details",
        )

        silver_failure = ti.xcom_pull(
            task_ids="silver",
            key="failure_details",
        )

        failure_details = normalize_failure_details(
            prepare_failure
            or bronze_failure
            or silver_failure
        )

        failed_at_raw = failure_details.get("failed_at")

        failed_at = (
            datetime.fromisoformat(failed_at_raw)
            if failed_at_raw
            else None
        )
        #removing due to being replaced by normalize_failure_details
        # if failure_details is None:
        #     failure_details = {
        #         "task_id": "unknown",
        #         "error_type": "PipelineFailure",
        #         "error_message": (
        #             "Airflow customer pipeline failed. "
        #             "See task logs for details."
        #         ),
        #         "dag_run_id": ("test_DAG__2026-09-11T18:00:00+00:00"),
        #         "try_number": 3,
        #         "failed_at": failed_at,
        #     }

        # error_message = (
        #     "Airflow customer pipeline failed. "
        #     "See Airflow task logs for the underlying error."
        # )

        if run_info is None:
            context = PipelineFailureContext(
                pipeline_name="customer_pipeline",
                pipeline_run_id=None,
                batch_id=None,
                stage_name=failure_details["task_id"],
                error_type=failure_details["error_type"],
                error_message=failure_details["error_message"],
                dag_run_id=failure_details.get("dag_run_id"),
                try_number=failure_details.get("try_number"),
                failed_at=failed_at,
            )

            LoggingAlertSink(log).send_failure(context)
            return

        handle_pipeline_failure(
            pipeline_name="customer_pipeline",
            pipeline_run_id=UUID(run_info["pipeline_run_id"]),
            batch_id=UUID(run_info["batch_id"]),
            stage_name=failure_details["task_id"],
            error_type=failure_details["error_type"],
            error_message=failure_details["error_message"],
            dag_run_id=failure_details.get("dag_run_id"),
            try_number=failure_details.get("try_number"),
            failed_at=failed_at,
            #alert_sink=LoggingAlertSink(log),
            alert_sink=create_pipeline_alert_sink(log),
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