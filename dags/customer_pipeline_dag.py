"""
Airflow DAG for the Northstar customer data pipeline.
"""
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

import pendulum

from airflow.sdk import TriggerRule, dag, get_current_context, task

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

        result = run_customer_bronze(context)

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
        pipeline_run_id = UUID(
            run_info["pipeline_run_id"]
        )
        batch_id = UUID(
            run_info["batch_id"]
        )

        error_message = (
            "Airflow customer pipeline failed. "
            "See Airflow task logs for the underlying error."
        )

        complete_batch(
            batch_id,
            status="FAILED",
            error_message=error_message,
        )

        complete_pipeline_run(
            pipeline_run_id,
            "FAILED",
            error_message=error_message,
        )

        print(f"PipelineRunID: {pipeline_run_id}")
        print(f"BatchID: {batch_id}")
        print("Status: FAILED")

    run_info = prepare_run()
    bronze_result = bronze(run_info)
    silver_result = silver(bronze_result)
    success_task = complete_success(silver_result)
    failure_task = complete_failure(run_info)

    [bronze_result, silver_result] >> failure_task

northstar_customer_pipeline()