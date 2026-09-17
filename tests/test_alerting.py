from unittest.mock import Mock, patch
from pathlib import Path
from datetime import datetime, timezone
import sys
from uuid import uuid4
import json

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from monitoring.alerts import CompositeAlertSink, LoggingAlertSink, PipelineFailureContext, WebhookAlertSink, create_pipeline_alert_sink


SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@patch("monitoring.alerts.urlopen")
def test_webhook_alert_sink_posts_failure(
    mock_urlopen,
):
        mock_response = Mock()

        mock_urlopen.return_value.__enter__.return_value = (
            mock_response
        )
        context = PipelineFailureContext(
            pipeline_name="customer_pipeline",
            pipeline_run_id=uuid4(),
            batch_id=uuid4(),
            stage_name="silver",
            error_type="InjectedPipelineFailure",
            error_message="Controlled failure.",
            dag_run_id="manual__test",
            try_number=1,
            failed_at=datetime.now(timezone.utc),
        )
        sink = WebhookAlertSink(
            "https://example.test/pipeline-alert"
        )

        sink.send_failure(context)

        mock_urlopen.assert_called_once()
        request = mock_urlopen.call_args.args[0]

        payload = json.loads( request.data.decode("utf-8") )

        assert payload["event_type"] == "pipeline_failure"
        assert payload["pipeline_name"] == "customer_pipeline"
        assert payload["stage_name"] == "silver"
        assert payload["try_number"] == 1
        assert (
            payload["error_type"]
            == "InjectedPipelineFailure"
        )
        assert request.get_method() == "POST"
        assert (
            request.headers["Content-type"]
            == "application/json"
        )

def test_alert_factory_uses_logging_without_webhook(
    monkeypatch,
):
    monkeypatch.delenv(
        "NORTHSTAR_PIPELINE_ALERT_WEBHOOK_URL",
        raising=False,
    )

    sink = create_pipeline_alert_sink()

    assert isinstance(
        sink,
        LoggingAlertSink,
    )

def test_alert_factory_uses_webhook_when_configured(
    monkeypatch,
):
    monkeypatch.setenv(
        "NORTHSTAR_PIPELINE_ALERT_WEBHOOK_URL",
        "https://example.test/alert",
    )

    sink = create_pipeline_alert_sink()

    assert isinstance(
        sink,
        CompositeAlertSink,
    )

def test_composite_alert_sink_continues_after_sink_failure():
    failing_sink = Mock()
    successful_sink = Mock()
    logger = Mock()

    failing_sink.send_failure.side_effect = RuntimeError(
        "Webhook unavailable"
    )

    context = PipelineFailureContext(
        pipeline_name="customer_pipeline",
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
        stage_name="silver",
        error_type="InjectedPipelineFailure",
        error_message="Controlled failure.",
        dag_run_id="manual__test",
        try_number=1,
        failed_at=datetime.now(timezone.utc),
    )

    sink = CompositeAlertSink(
        [
            failing_sink,
            successful_sink,
        ],
        logger=logger,
    )

    sink.send_failure(context)

    failing_sink.send_failure.assert_called_once_with(
        context
    )

    successful_sink.send_failure.assert_called_once_with(
        context
    )

    logger.exception.assert_called_once()