import sys
from pathlib import Path

import pytest


SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from settings import get_customer_invalid_rate_threshold


def test_default_threshold(monkeypatch):
    monkeypatch.delenv(
        "NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD",
        raising=False,
    )

    threshold = (
        get_customer_invalid_rate_threshold()
    )

    assert threshold == 0.05

def test_threshold_can_be_configured(monkeypatch):
    monkeypatch.setenv(
        "NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD",
        "0.02",
    )

    threshold = (
        get_customer_invalid_rate_threshold()
    )

    assert threshold == 0.02

def test_threshold_rejects_non_numeric_value(
    monkeypatch,
):
    monkeypatch.setenv(
        "NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD",
        "banana",
    )

    with pytest.raises(ValueError):
        get_customer_invalid_rate_threshold()

def test_threshold_rejects_value_greater_than_one(
    monkeypatch,
):
    monkeypatch.setenv(
        "NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD",
        "1.5",
    )

    with pytest.raises(ValueError):
        get_customer_invalid_rate_threshold()