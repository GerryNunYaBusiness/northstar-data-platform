import logging
from uuid import UUID

from monitoring.pipeline_events import (    record_pipeline_event,)

logger = logging.getLogger(__name__)


def capture_task_retry(context) -> None:
    # print("DEBUG: capture_task_retry WAS CALLED")

    task_instance = context["ti"]
    exception = context.get("exception")

    run_info = _get_run_info(task_instance)

    if run_info is None:
        return

    error_type = (
        type(exception).__name__
        if exception is not None
        else "UnknownError"
    )

    error_message = (
        str(exception)
        if exception is not None
        else "Task retry requested without an exception."
    )

    logger.warning(
        "Pipeline task retry | "
        "task=%s | "
        "dag_run_id=%s | "
        "try_number=%s | "
        "error_type=%s | "
        "error_message=%s",
        task_instance.task_id,
        task_instance.run_id,
        task_instance.try_number,
        error_type,
        error_message,
    )

    record_pipeline_event(
        pipeline_name="customer_pipeline",
        pipeline_run_id=UUID(
            run_info["pipeline_run_id"]
        ),
        batch_id=UUID(
            run_info["batch_id"]
        ),
        stage_name=task_instance.task_id,
        event_type="RETRY",
        dag_run_id=task_instance.run_id,
        try_number=task_instance.try_number,
        error_type=error_type,
        event_message=error_message,
    )


def capture_task_success(context) -> None:
    task_instance = context["ti"]
    
    run_info = _get_run_info(task_instance)

    if task_instance.try_number <= 1:
        return

    logger.info(
        "Pipeline task recovered | "
        "task=%s | "
        "dag_run_id=%s | "
        "try_number=%s",
        task_instance.task_id,
        task_instance.run_id,
        task_instance.try_number,
    )

    record_pipeline_event(
        pipeline_name="customer_pipeline",
        pipeline_run_id=UUID(run_info["pipeline_run_id"]        ),
        batch_id=UUID(run_info["batch_id"]        ),
        stage_name=task_instance.task_id,
        event_type="RECOVERED",
        dag_run_id=task_instance.run_id,
        try_number=task_instance.try_number,
        event_message=(
            "Task succeeded after one or more retries."
        ),
    )

def _get_run_info(task_instance) -> dict | None:
    return task_instance.xcom_pull(
        task_ids="prepare_run"
    )