from datetime import datetime, timedelta
from uuid import UUID

from airflow.sdk import dag, task

from customer_pipeline import run_customer_pipeline


@dag(
    dag_id="northstar_customer_pipeline",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
)
def northstar_customer_pipeline():

    @task(retries=2, retry_delay=timedelta(minutes=1))
    def run_pipeline():
        result = run_customer_pipeline()

        return {
            "pipeline_run_id": str(result.pipeline_run_id),
            "batch_id": str(result.batch_id),
            "status": result.status,
        }

    run_pipeline()


northstar_customer_pipeline()