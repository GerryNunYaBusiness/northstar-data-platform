from uuid import UUID

from monitoring.alerts import (
    LoggingAlertSink,
    PipelineAlertSink,
    PipelineFailureContext,
)
from monitoring.pipeline_batches import complete_batch
from monitoring.pipeline_runs import complete_pipeline_run


def handle_pipeline_failure(
    *,
    pipeline_name: str,
    pipeline_run_id: UUID,
    batch_id: UUID,
    stage_name: str,
    error_type: str,
    error_message: str,
    alert_sink: PipelineAlertSink | None = None,
) -> None:
    complete_batch(
        batch_id,
        status="FAILED",
        error_message=error_message,
    )

    complete_pipeline_run(
        pipeline_run_id,
        "FAILED",
        error_message=error_message,
    )

    context = PipelineFailureContext(
        pipeline_name=pipeline_name,
        pipeline_run_id=pipeline_run_id,
        batch_id=batch_id,
        stage_name=stage_name,
        error_type=error_type,
        error_message=error_message,
    )

    sink = alert_sink or LoggingAlertSink()
    sink.send_failure(context)