from pathlib import Path
import sys
from uuid import uuid4
from unittest.mock import ANY, patch
import pytest
from contextlib import contextmanager

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from customer_pipeline import run_customer_pipeline

@contextmanager
def fake_pipeline_stage(*args, **kwargs):
    yield {"rows_processed": 0}

@patch("customer_pipeline.pipeline_stage", side_effect=fake_pipeline_stage)
@patch("customer_pipeline.complete_pipeline_run")
@patch("customer_pipeline.start_pipeline_run")
@patch("customer_pipeline.complete_batch")
@patch("customer_pipeline.begin_or_retry_batch")
@patch("customer_pipeline.load_silver_customers")
@patch("customer_pipeline.load_bronze_for_batch")
@patch("customer_pipeline.quarantine_customer_errors")
@patch("customer_pipeline.get_valid_customers")
@patch("customer_pipeline.validate_customers")
@patch("customer_pipeline.extract_customers")
def test_successful_pipeline_completes_batch_successfully(
    mock_extract,
    mock_validate,
    mock_get_valid,
    mock_quarantine,
    mock_load_bronze,
    mock_load_silver,
    mock_begin_batch,
    mock_complete_batch,
    mock_start_pipeline,
    mock_complete_pipeline,
    mock_pipeline_stage,
):
    batch_id = uuid4()

    mock_extract.return_value = []
    mock_validate.return_value = []
    mock_get_valid.return_value = []
    mock_load_bronze.return_value = 0
    mock_pipeline_stage.return_value.__enter__.return_value = {
        "rows_processed": 0
    }

    result = run_customer_pipeline(batch_id=batch_id)

    assert result.status == "SUCCESS"
    assert result.batch_id == batch_id

    mock_begin_batch.assert_called_once()

    mock_complete_batch.assert_called_once_with(
        batch_id=batch_id,
        status="SUCCESS",
        rows_processed=0,
    )

    mock_complete_pipeline.assert_called_once()

@patch("customer_pipeline.pipeline_stage", side_effect=fake_pipeline_stage)
@patch("customer_pipeline.complete_pipeline_run")
@patch("customer_pipeline.start_pipeline_run")
@patch("customer_pipeline.complete_batch")
@patch("customer_pipeline.begin_or_retry_batch")
@patch("customer_pipeline.extract_customers")
def test_failed_pipeline_marks_batch_failed(
    mock_extract,
    mock_begin_batch,
    mock_complete_batch,
    mock_start_pipeline,
    mock_complete_pipeline,
    mock_pipeline_stage,
):
    batch_id = uuid4()

    mock_extract.side_effect = RuntimeError("Simulated extract failure")
    mock_pipeline_stage.return_value.__enter__.return_value = {
        "rows_processed": 0
    }

    with pytest.raises(
        RuntimeError,
        match="Simulated extract failure",
    ):
        run_customer_pipeline(batch_id=batch_id)

    mock_begin_batch.assert_called_once()

    mock_complete_batch.assert_called_once_with(
        batch_id=batch_id,
        status="FAILED",
        error_message="Simulated extract failure",
    )

    mock_complete_pipeline.assert_called_once_with(
    ANY,
    "FAILED",
    error_message="Simulated extract failure",
    )

@patch("customer_pipeline.complete_pipeline_run")
@patch("customer_pipeline.start_pipeline_run")
@patch("customer_pipeline.complete_batch")
@patch("customer_pipeline.begin_or_retry_batch")
def test_rejected_batch_does_not_overwrite_batch_status(
    mock_begin_batch,
    mock_complete_batch,
    mock_start_pipeline,
    mock_complete_pipeline,
):
    batch_id = uuid4()

    mock_begin_batch.side_effect = ValueError(
        f"Batch {batch_id} has already completed successfully."
    )

    with pytest.raises(
        ValueError,
        match="already completed successfully",
    ):
        run_customer_pipeline(batch_id=batch_id)

    mock_begin_batch.assert_called_once()

    mock_complete_batch.assert_not_called()

    mock_complete_pipeline.assert_called_once()