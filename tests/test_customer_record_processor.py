from contextlib import nullcontext
from unittest.mock import patch
import pytest
from uuid import uuid4

from pathlib import Path
import sys

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from ingestion.customers import CustomerRecord
from pipeline_framework.context import PipelineContext
from transformation.customer_record_processor import (
    process_customer_records,
)
from exceptions import DataQualityError


def test_invalid_customers_are_filtered_and_quarantined():
    context = PipelineContext(
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    customers = [
        CustomerRecord(
            customer_id=1,
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="555-0101",
            created_at=None,
        ),
        CustomerRecord(
            customer_id=2,
            first_name="Bob",
            last_name="Jones",
            email="invalid-email",
            phone="555-0102",
            created_at=None,
        ),
    ]

    with (
        patch(
            "transformation.customer_record_processor.pipeline_stage",
            side_effect=lambda *args, **kwargs: nullcontext({}),
        ),
        patch(
            "transformation.customer_record_processor.quarantine_customer_errors"
        ) as mock_quarantine,
        patch(
            "transformation.customer_record_processor.get_customer_invalid_rate_threshold",
            return_value=0.60,
        ),
    ):
        valid_customers = process_customer_records(
            customers,
            context,
        )

    assert [customer.customer_id for customer in valid_customers] == [1]

    mock_quarantine.assert_called_once()

    errors, pipeline_run_id = mock_quarantine.call_args.args

    assert pipeline_run_id == context.pipeline_run_id
    assert len(errors) == 1
    assert errors[0].rule == "EMAIL_FORMAT"

def test_customer_invalid_rate_above_threshold_raises():
    context = PipelineContext(
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    customers = [
        CustomerRecord(
            customer_id=1,
            first_name="Alice",
            last_name="Smith",
            email="alice@example.com",
            phone="555-0101",
            created_at=None,
        ),
        CustomerRecord(
            customer_id=2,
            first_name="Bob",
            last_name="Jones",
            email="invalid-email",
            phone="555-0102",
            created_at=None,
        ),
    ]

    with (
        patch(
            "transformation.customer_record_processor.pipeline_stage",
            side_effect=lambda *args, **kwargs: nullcontext({}),
        ),
        patch(
            "transformation.customer_record_processor.quarantine_customer_errors"
        ) as mock_quarantine,
        patch(
            "transformation.customer_record_processor.get_customer_invalid_rate_threshold",
            return_value=0.05,
        ),
    ):
        with pytest.raises(
            DataQualityError,
            match="Customer invalid rate",
        ):
            process_customer_records(
                customers,
                context,
            )

    mock_quarantine.assert_called_once()