"""
Airflow DAG for the Northstar Commerce pipeline.
"""

from datetime import timedelta
from uuid import NAMESPACE_URL, uuid4, uuid5

import pendulum

from airflow.sdk import (
    dag,
    get_current_context,
    task,
    ExceptionRetryPolicy,
    RetryAction,
    RetryRule,
)


from exceptions import (
    DataQualityError,
    TransientPipelineError,
)

from commerce_pipeline import run_commerce_pipeline

from monitoring.airflow_failure import capture_task_failure
from monitoring.retry_observability import (
    capture_task_retry,
    capture_task_success,
)

COMMERCE_RETRY_POLICY = ExceptionRetryPolicy(
    rules=[
        RetryRule(
            exception=DataQualityError,
            action=RetryAction.FAIL,
            reason="Data-quality failures are not retryable.",
        ),
        RetryRule(
            exception=TransientPipelineError,
            action=RetryAction.RETRY,
            retry_delay=timedelta(minutes=1),
            reason="Transient infrastructure failure.",
        ),
    ]
)

@dag(
    dag_id="northstar_commerce_pipeline",
    schedule=None,
    start_date=pendulum.datetime(
        2026, 10, 12,
        tz="America/New_York",
    ),
    catchup=False,
    tags=["northstar", "commerce"],
)
def northstar_commerce_pipeline():

    @task(
        retries=2,
        retry_delay=timedelta(minutes=1),
        retry_policy=COMMERCE_RETRY_POLICY,
        on_failure_callback=capture_task_failure,
        on_retry_callback=capture_task_retry,
        on_success_callback=capture_task_success,
    )
    def execute_commerce() -> dict:

        airflow_context = get_current_context()
        dag_run = airflow_context["dag_run"]

        batch_id = uuid5(
            NAMESPACE_URL,
            f"northstar:commerce:{dag_run.run_id}",
        )

        # A new execution attempt gets a new PipelineRunID.
        pipeline_run_id = uuid4()

        result = run_commerce_pipeline(
            pipeline_run_id=pipeline_run_id,
            batch_id=batch_id,
        )

        return {
            "pipeline_run_id": str(result.pipeline_run_id),
            "batch_id": str(result.batch_id),
            "status": result.status,
        }

    execute_commerce()


northstar_commerce_pipeline()