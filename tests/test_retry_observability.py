from unittest.mock import Mock, patch
from pathlib import Path
import sys
from uuid import uuid4

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from exceptions import TransientPipelineError

from monitoring.retry_observability import capture_task_retry, capture_task_success

def test_retry_logs_warning():
    ti = Mock()
    ti.task_id = "bronze"
    ti.run_id = "test_run"
    ti.try_number = 1
    ti.xcom_pull.return_value = {
        "pipeline_run_id": str(uuid4()),
        "batch_id": str(uuid4()),
    }

    exception = TransientPipelineError(
        "Temporary SQL connectivity failure."
    )

    with patch(
        "monitoring.retry_observability.logger"
    ) as mock_logger:
        with patch(
            "monitoring.retry_observability.record_pipeline_event"
        ) as mock_record_event:
                capture_task_retry(
                    {
                        "ti": ti,
                        "exception": exception,
                    }
                )

    mock_record_event.assert_called_once()

    kwargs = mock_record_event.call_args.kwargs

    assert kwargs["event_type"] == "RETRY"
    assert kwargs["stage_name"] == "bronze"
    assert kwargs["try_number"] == 1
    assert (kwargs["error_type"] == "TransientPipelineError" )

    mock_logger.warning.assert_called_once()

    args = mock_logger.warning.call_args.args

    assert "Pipeline task retry" in args[0]
    assert "bronze" in args
    assert "TransientPipelineError" in args

def test_first_attempt_success_does_not_log_recovery():
    ti = Mock()
    ti.task_id = "bronze"
    ti.run_id = "test_run"
    ti.try_number = 1
    ti.xcom_pull.return_value = {
        "pipeline_run_id": str(uuid4()),
        "batch_id": str(uuid4()),
    }

    with patch(
        "monitoring.retry_observability.logger"
    ) as mock_logger:
        with patch(
            "monitoring.retry_observability.record_pipeline_event"
        ) as mock_record_event:
            capture_task_success({"ti": ti})

    mock_record_event.assert_not_called()
    mock_logger.info.assert_not_called()

def test_success_after_retry_logs_recovery():
    ti = Mock()
    ti.task_id = "bronze"
    ti.run_id = "test_run"
    ti.try_number = 2
    ti.xcom_pull.return_value = {
        "pipeline_run_id": str(uuid4()),
        "batch_id": str(uuid4()),
    }

    with patch(
        "monitoring.retry_observability.logger"
    ) as mock_logger:
        with patch(
            "monitoring.retry_observability.record_pipeline_event"
        ) as mock_record_event:
            capture_task_success({"ti": ti})

    mock_record_event.assert_called_once()

    kwargs = mock_record_event.call_args.kwargs

    assert kwargs["event_type"] == "RECOVERED"
    assert kwargs["stage_name"] == "bronze"
    assert kwargs["try_number"] == 2
    mock_logger.info.assert_called_once()

    args = mock_logger.info.call_args.args

    assert "Pipeline task recovered" in args[0]
    assert "bronze" in args