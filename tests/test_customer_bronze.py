from pathlib import Path
import os
import sys
from unittest.mock import patch
from uuid import uuid4

from datetime import datetime
import pytest

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from customer_pipeline import run_customer_bronze
from exceptions import DataQualityError
from pipeline_context import PipelineContext
from ingestion.customers import CustomerRecord, CustomerValidationError
from exceptions import InjectedPipelineFailure


def make_customer(
    customer_id: int = 1,
    first_name: str | None = "Alice",
    last_name: str | None = "Johnson",
    email: str | None = "alice@example.com",
    phone: str | None = "555-0100",
) -> CustomerRecord:
    return CustomerRecord(
        customer_id=customer_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        created_at=datetime(2026, 1, 1),
    )

def test_zero_invalid_rate_threshold_fails_bronze():
    context = PipelineContext(
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    customer1 = make_customer(customer_id=1)
    customer2 = make_customer(customer_id=2)

    validation_error = CustomerValidationError(
        customer=customer2,
        rule="EMAIL_FORMAT",
        message="Invalid email format.",
    )

    with patch.dict(
        os.environ,
        {
            "NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD": "0",
        },
        clear=False,
    ):
        with (
            patch(
                "customer_pipeline.pipeline_stage"
            ) as mock_pipeline_stage,
            patch(
                "customer_pipeline.extract_customers",
                return_value=[customer1, customer2],
            ),
            patch(
                "customer_pipeline.validate_customers",
                return_value=[validation_error],
            ),
            patch(
                "customer_pipeline.quarantine_customer_errors",
            ),
        ):
            mock_pipeline_stage.return_value.__enter__.return_value = {
                "rows_processed": 0,
            }

            with pytest.raises(DataQualityError):
                run_customer_bronze(context)

def test_bronze_can_inject_controlled_failure():
    context = PipelineContext(
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    with patch.dict(
        os.environ,
        {"NORTHSTAR_TEST_FAILURE_STAGE": "bronze"},
        clear=False,
    ):
        with patch(
            "customer_pipeline.pipeline_stage"
        ) as mock_pipeline_stage:
            mock_pipeline_stage.return_value.__enter__.return_value = {
                "rows_processed": 0,
            }

            with pytest.raises(
                InjectedPipelineFailure,
                match="Controlled Bronze failure",
            ):
                run_customer_bronze(context)