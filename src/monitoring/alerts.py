from dataclasses import dataclass
from datetime import datetime
import logging
from pathlib import Path
from uuid import UUID
import json
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class PipelineFailureContext:
    pipeline_name: str
    pipeline_run_id: UUID | None
    batch_id: UUID | None
    stage_name: str
    error_type: str
    error_message: str
    dag_run_id: str | None = None
    try_number: int | None = None
    failed_at: datetime | None = None

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
            "dag_run_id=%s | "
            "try_number=%s | "
            "failed_at=%s | "
            "error_type=%s | "
            "error_message=%s",
            context.pipeline_name,
            context.pipeline_run_id,
            context.batch_id,
            context.stage_name,
            context.dag_run_id,
            context.try_number,
            context.failed_at,
            context.error_type,
            context.error_message,
        )

class WebhookAlertSink(PipelineAlertSink):
    def __init__(
        self,
        webhook_url: str,
        timeout_seconds: float = 5.0,
    ) -> None:
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def send_failure(
        self,
        context: PipelineFailureContext,
    ) -> None:
        payload = {
            "event_type": "pipeline_failure",
            "pipeline_name": context.pipeline_name,
            "pipeline_run_id": (
                str(context.pipeline_run_id)
                if context.pipeline_run_id
                else None
            ),
            "batch_id": (
                str(context.batch_id)
                if context.batch_id
                else None
            ),
            "stage_name": context.stage_name,
            "dag_run_id": context.dag_run_id,
            "try_number": context.try_number,
            "failed_at": (
                context.failed_at.isoformat()
                if context.failed_at
                else None
            ),
            "error_type": context.error_type,
            "error_message": context.error_message,
        }

        request = Request(
            self.webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urlopen(
            request,
            timeout=self.timeout_seconds,
        ) as response:
            response.read()

def create_pipeline_alert_sink(
    logger: logging.Logger | None = None,
) -> PipelineAlertSink:
    from settings import get_pipeline_alert_webhook_url

    logging_sink = LoggingAlertSink(logger)

    webhook_url = get_pipeline_alert_webhook_url()

    if not webhook_url:
        return logging_sink

    return CompositeAlertSink(
        [
            logging_sink,
            WebhookAlertSink(webhook_url),
        ],
        logger=logger,
    )

class CompositeAlertSink(PipelineAlertSink):
    def __init__(
        self,
        sinks: list[PipelineAlertSink],
        logger: logging.Logger | None = None,
    ) -> None:
        self.sinks = sinks
        self.logger = logger or logging.getLogger(__name__)

    def send_failure(
        self,
        context: PipelineFailureContext,
    ) -> None:
        for sink in self.sinks:
            try:
                sink.send_failure(context)
            except Exception:
                self.logger.exception(
                    "Pipeline alert sink failed | sink=%s",
                    type(sink).__name__,
                )