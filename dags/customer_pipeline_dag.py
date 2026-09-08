"""
Airflow DAG for the Northstar customer data pipeline.
"""
from datetime import datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

import pendulum

from airflow.sdk import dag, get_current_context, task

from customer_pipeline import run_customer_pipeline


@dag(
    dag_id="northstar_customer_pipeline",
    schedule="0 2 * * *",
    start_date=pendulum.datetime(2026,9,8, tz="America/New_York",    ),
    catchup=False,
    tags=["northstar", "customers"],
)

def northstar_customer_pipeline():
    @task
    def start():
        print("Northstar customer workflow starting")

    @task(retries=2, retry_delay=timedelta(minutes=1),    )

    def run_pipeline():
        context = get_current_context()

        dag_run = context["dag_run"]

        batch_id = uuid5( NAMESPACE_URL, f"northstar:{dag_run.run_id}",        )

        print(f"Airflow RunID: {dag_run.run_id}")
        print(f"Northstar BatchID: {batch_id}")

        result = run_customer_pipeline(  batch_id=batch_id,        )

        # print(f"PipelineRunID: {result.pipeline_run_id}")
        # print(f"Status: {result.status}")

        return {
            "pipeline_run_id": str(result.pipeline_run_id),
            "batch_id": str(result.batch_id),
            "status": result.status,
        }

    @task
    def finish(result: dict):
        print("Northstar customer workflow finished")
        print(f"PipelineRunID: {result['pipeline_run_id']}")
        print(f"BatchID: {result['batch_id']}")
        print(f"Status: {result['status']}")

    start_task = start()
    pipeline_result = run_pipeline()
    finish_task = finish(pipeline_result)


northstar_customer_pipeline()