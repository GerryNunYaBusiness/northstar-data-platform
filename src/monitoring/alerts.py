from dataclasses import dataclass
import logging
from pathlib import Path
from uuid import UUID

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class PipelineFailureContext:
    pipeline_name: str
    pipeline_run_id: UUID
    batch_id: UUID
    stage_name: str
    error_type: str
    error_message: str

class PipelineAlertSink:
    def send_failure(self, context: PipelineFailureContext) -> None:
        raise NotImplementedError

# class LoggingAlertSink(PipelineAlertSink):
#     def send_failure(self, context: PipelineFailureContext) -> None:
#         logger.error(
#             "Pipeline failure alert | "
#             "pipeline=%s | "
#             "pipeline_run_id=%s | "
#             "batch_id=%s | "
#             "stage=%s | "
#             "error_type=%s | "
#             "error_message=%s",
#             context.pipeline_name,
#             context.pipeline_run_id,
#             context.batch_id,
#             context.stage_name,
#             context.error_type,
#             context.error_message,
#         )

class LoggingAlertSink(PipelineAlertSink):
    def __init__(
        self,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)

    def send_failure(self, context: PipelineFailureContext) -> None:
        self.logger.error(
            "Pipeline failure alert | "
            "pipeline=%s | "
            "pipeline_run_id=%s | "
            "batch_id=%s | "
            "stage=%s | "
            "error_type=%s | "
            "error_message=%s",
            context.pipeline_name,
            context.pipeline_run_id,
            context.batch_id,
            context.stage_name,
            context.error_type,
            context.error_message,
        )