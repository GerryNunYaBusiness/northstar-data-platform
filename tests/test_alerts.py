from pathlib import Path
import sys
from uuid import uuid4
from unittest.mock import Mock, patch
import pytest
import os
from exceptions import DataQualityError
from customer_pipeline import (
    run_customer_bronze,
    #run_customer_silver,
)
from pipeline_context import PipelineContext


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from monitoring.alerts import LoggingAlertSink, PipelineFailureContext


def test_pipeline_failure_context_preserves_failure_details():
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    context = PipelineFailureContext(
        pipeline_name="customer_pipeline",
        pipeline_run_id=pipeline_run_id,
        batch_id=batch_id,
        stage_name="bronze",
        error_type="DataQualityError",
        error_message="Invalid customer rate exceeded threshold.",
    )

    assert context.pipeline_name == "customer_pipeline"
    assert context.pipeline_run_id == pipeline_run_id
    assert context.batch_id == batch_id
    assert context.stage_name == "bronze"
    assert context.error_type == "DataQualityError"
    assert (
        context.error_message
        == "Invalid customer rate exceeded threshold."
    )

def test_logging_alert_sink_logs_failure_context():
    mock_logger = Mock()
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    context = PipelineFailureContext(
        pipeline_name="customer_pipeline",
        pipeline_run_id=pipeline_run_id,
        batch_id=batch_id,
        stage_name="bronze",
        error_type="DataQualityError",
        error_message="Invalid customer rate exceeded threshold.",
    )

    sink = LoggingAlertSink(mock_logger)

    #with patch("monitoring.alerts.logger.error") as mock_error:
    sink.send_failure(context)
    mock_logger.error.assert_called_once()
    #mock_error.assert_called_once()

    #args = mock_error.call_args.args

    # assert pipeline_run_id in args
    # assert batch_id in args
    # assert "bronze" in args
    # assert "DataQualityError" in args
    # assert "Invalid customer rate exceeded threshold." in args

