from pathlib import Path
from datetime import datetime, timezone
import sys
from unittest.mock import Mock,patch
from uuid import uuid4
from unittest.mock import patch

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
DAGS_PATH = Path(__file__).resolve().parents[1] / "dags"

for path in (SRC_PATH, DAGS_PATH):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

#from dags.customer_pipeline_dag import complete_failure
from monitoring.failure_handler import handle_pipeline_failure
from monitoring.airflow_failure import (    capture_task_failure,    normalize_failure_details,)

def test_handle_pipeline_failure_marks_failed_and_sends_alert():
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    mock_sink = Mock()

    with (
        patch(
            "monitoring.failure_handler.complete_batch"
        ) as mock_complete_batch,
        patch(
            "monitoring.failure_handler.complete_pipeline_run"
        ) as mock_complete_pipeline_run,
    ):
        handle_pipeline_failure(
            pipeline_name="customer_pipeline",
            pipeline_run_id=pipeline_run_id,
            batch_id=batch_id,
            stage_name="bronze",
            error_type="DataQualityError",
            error_message="Invalid customer rate exceeded threshold.",
            dag_run_id= ("test_airflow_failure_2026-09-11T18:00:00+00:00"),
            try_number= 3,
            failed_at=datetime.now(timezone.utc),
            alert_sink=mock_sink,
        )

    mock_complete_batch.assert_called_once_with(
        batch_id,
        status="FAILED",
        error_message="Invalid customer rate exceeded threshold.",
    )

    mock_complete_pipeline_run.assert_called_once_with(
        pipeline_run_id,
        "FAILED",
        error_message="Invalid customer rate exceeded threshold.",
    )

    mock_sink.send_failure.assert_called_once()

    context = mock_sink.send_failure.call_args.args[0]

    assert context.pipeline_name == "customer_pipeline"
    assert context.pipeline_run_id == pipeline_run_id
    assert context.batch_id == batch_id
    assert context.stage_name == "bronze"
    assert context.error_type == "DataQualityError"

def test_normalize_failure_details_handles_none():
    result = normalize_failure_details(None)

    assert result["task_id"] == "unknown"
    assert result["error_type"] == "PipelineFailure"
    assert result["error_message"] == (
        "Airflow customer pipeline failed. "
        "See task logs for details."
    )
    assert result["dag_run_id"] is None
    assert result["try_number"] is None
    assert result["failed_at"] is None

def test_normalize_failure_details_handles_partial_metadata():
    result = normalize_failure_details(
        {
            "task_id": "bronze",
            "error_type": "DataQualityError",
            "error_message": "Invalid customer rate exceeded.",
        }
    )

    assert result["task_id"] == "bronze"
    assert result["error_type"] == "DataQualityError"
    assert (
        result["error_message"]
        == "Invalid customer rate exceeded."
    )

    assert result["dag_run_id"] is None
    assert result["try_number"] is None
    assert result["failed_at"] is None

def test_normalize_failure_details_preserves_metadata():
    failure_details = {
        "task_id": "silver",
        "error_type": "TransientPipelineError",
        "error_message": "SQL connection failed.",
        "dag_run_id": "manual__test",
        "try_number": 3,
        "failed_at": "2026-09-15T15:00:00+00:00",
    }

    result = normalize_failure_details(
        failure_details
    )

    assert result == failure_details

def test_normalize_prepare_run_failure():
    result = normalize_failure_details(
        {
            "task_id": "prepare_run",
            "error_type": "InjectedPipelineFailure",
            "error_message": (
                "Controlled prepare_run failure."
            ),
            "dag_run_id": "manual__prepare_test",
            "try_number": 1,
            "failed_at": (
                "2026-09-15T18:00:00+00:00"
            ),
        }
    )

    assert result["task_id"] == "prepare_run"
    assert (
        result["error_type"]
        == "InjectedPipelineFailure"
    )
    assert result["try_number"] == 1