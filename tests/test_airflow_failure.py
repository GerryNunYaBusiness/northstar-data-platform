from pathlib import Path
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

