import pytest


@pytest.fixture(autouse=True)
def clear_failure_injection_environment(
    monkeypatch,
):
    monkeypatch.delenv(
        "NORTHSTAR_TEST_FAILURE_STAGE",
        raising=False,
    )

    monkeypatch.delenv(
        "NORTHSTAR_TEST_TRANSIENT_FAILURE_STAGE",
        raising=False,
    )