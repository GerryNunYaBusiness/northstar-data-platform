from unittest.mock import MagicMock, patch
import pytest

@patch("monitoring.pipeline_batches.get_warehouse_connection")
def test_batch_with_different_pipeline_name_raises_value_error(
    mock_get_connection,
):
    connection = MagicMock()
    mock_get_connection.return_value.__enter__.return_value = connection

    connection.execute.return_value.fetchone.return_value = (
        "RUNNING",
        "different_pipeline",
    )

    with patch("monitoring.pipeline_batches.get_warehouse_connection", return_value=connection):
        from monitoring.pipeline_batches import begin_or_retry_batch
        from uuid import uuid4

        existing_batch_id = uuid4()
        pipeline_name = "test_pipeline"

        with pytest.raises(ValueError, match="belongs to pipeline"):
            begin_or_retry_batch(
                batch_id=existing_batch_id,
                pipeline_name="commerce",
            )