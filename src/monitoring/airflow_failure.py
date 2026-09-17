from dataclasses import dataclass
from datetime import datetime, timezone

@dataclass(frozen=True)
class AirflowFailureDetails:
    task_id: str
    error_type: str
    error_message: str
    dag_run_id: str
    try_number: int

from unittest.mock import Mock

from exceptions import InjectedPipelineFailure
#from dags.customer_pipeline_dag import capture_task_failure 
import logging

logger = logging.getLogger(__name__)

def capture_task_failure(context):
    task_instance = context["ti"]
    exception = context.get("exception")

    failure_details = {
        "task_id": task_instance.task_id,
        "error_type": (
            type(exception).__name__
            if exception is not None
            else "UnknownError"
        ),
        "error_message": (
            str(exception)
            if exception is not None
            else "Task failed without an exception."
        ),
        "dag_run_id": task_instance.run_id,
        "try_number": task_instance.try_number,
        "failed_at": datetime.now(timezone.utc).isoformat(),
    }

    # logger.error(
    #     "Capturing task failure details: %s",
    #     failure_details,
    # )

    task_instance.xcom_push(
        key="failure_details",
        value=failure_details,
    )

def normalize_failure_details(
    failure_details: dict | None,
) -> dict:
    if failure_details is None:
        return {
            "task_id": "unknown",
            "error_type": "PipelineFailure",
            "error_message": (
                "Airflow customer pipeline failed. "
                "See task logs for details."
            ),
            "dag_run_id": None,
            "try_number": None,
            "failed_at": None,
        }

    return {
        "task_id": failure_details.get(
            "task_id",
            "unknown",
        ),
        "error_type": failure_details.get(
            "error_type",
            "PipelineFailure",
        ),
        "error_message": failure_details.get(
            "error_message",
            "Airflow customer pipeline failed. "
            "See task logs for details.",
        ),
        "dag_run_id": failure_details.get(
            "dag_run_id"
        ),
        "try_number": failure_details.get(
            "try_number"
        ),
        "failed_at": failure_details.get(
            "failed_at"
        ),
    }

def test_capture_task_failure_pushes_failure_details():
    ti = Mock()
    ti.task_id = "bronze"
    ti.run_id = "manual__2026-09-11T18:00:00+00:00"
    ti.try_number = 3

    exception = InjectedPipelineFailure("Controlled failure.")

    capture_task_failure(
        {
            "ti": ti,
            "run_id": ti.run_id,
            "exception": exception,
        }
    )

    # ti.xcom_push.assert_called_once_with(
    #     key="failure_details",
    #     value={
    #         "task_id": "bronze",
    #         "error_type": "InjectedPipelineFailure",
    #         "error_message": "Controlled failure.",
    #         "dag_run_id": ("test_DAG__2026-09-11T18:00:00+00:00"),
    #         "try_number": 3,
    #     },
    # )
        # Get the dictionary that capture_task_failure()
    # passed to xcom_push().
    call = ti.xcom_push.call_args.kwargs
    failure_details = call["value"]

    assert failure_details["task_id"] == "bronze"
    assert failure_details["error_type"] == "InjectedPipelineFailure"
    assert failure_details["error_message"] == "Controlled failure."
    assert failure_details["dag_run_id"] == ti.run_id
    assert failure_details["try_number"] == 3

    # Don't assert an exact timestamp because the test's
    # execution time changes on every run.
    assert failure_details["failed_at"] is not None

    parsed = datetime.fromisoformat(
        failure_details["failed_at"]
    )

    # Proves that failed_at is timezone-aware.
    assert parsed.tzinfo is not None