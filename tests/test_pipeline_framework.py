from contextlib import nullcontext
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from dataclasses import dataclass

from pathlib import Path
import sys
SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from pipeline_framework.context import PipelineContext
from pipeline_framework.stages import execute_bronze_stage, execute_silver_stage
from pipeline_framework.entity import EntityPipeline, execute_entity_pipeline
from pipeline_framework.results import StageResult

@dataclass(frozen=True)
class FakeSilverResult:
    rows_inserted: int
    rows_updated: int

@dataclass(frozen=True)
class FakeQuarantineSilverResult:
    rows_inserted: int
    rows_updated: int
    rows_quarantined: int

@patch("pipeline_framework.stages.pipeline_stage",    side_effect=lambda *args, **kwargs: nullcontext(),)
def test_execute_bronze_stage_extracts_and_loads_records(
    mock_pipeline_stage,
):
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    context = PipelineContext(
        pipeline_run_id=pipeline_run_id,
        batch_id=batch_id,
    )

    records = [
        {"id": 1},
        {"id": 2},
    ]

    extractor = Mock(
        return_value=records,
    )

    loader = Mock(
        return_value=2,
    )

    result = execute_bronze_stage(
        stage_name="test_bronze",
        context=context,
        extractor=extractor,
        loader=loader,
    )

    extractor.assert_called_once_with()

    loader.assert_called_once_with(
        records,
        pipeline_run_id,
        batch_id,
    )

    assert result.stage_name == "test_bronze"
    assert result.rows_inserted == 2
    assert result.rows_updated == 0
    assert result.rows_quarantined == 0

@patch("pipeline_framework.stages.pipeline_stage",    side_effect=lambda *args, **kwargs: nullcontext(),)
def test_execute_bronze_stage_propagates_loader_failure(
    mock_pipeline_stage,
):
    context = PipelineContext(
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    extractor = Mock(
        return_value=[{"id": 1}],
    )

    loader = Mock(
        side_effect=RuntimeError("Bronze load failed"),
    )

    # try:
    with pytest.raises(RuntimeError, match="Bronze load failed"):
        execute_bronze_stage(
            stage_name="test_bronze",
            context=context,
            extractor=extractor,
            loader=loader,
        )

    #     assert False, "Expected RuntimeError"

    # except RuntimeError as exc:
    #     assert str(exc) == "Bronze load failed"

@patch("pipeline_framework.stages.pipeline_stage",    side_effect=lambda *args, **kwargs: nullcontext(),)
def test_execute_silver_stage_returns_insert_and_update_counts(
    mock_pipeline_stage,
):
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    context = PipelineContext(
        pipeline_run_id=pipeline_run_id,
        batch_id=batch_id,
    )

    loader = Mock(
        return_value=FakeSilverResult(
            rows_inserted=4,
            rows_updated=2,
        )
    )

    result = execute_silver_stage(
        stage_name="test_silver",
        context=context,
        loader=loader,
    )

    loader.assert_called_once_with(
        pipeline_run_id,
        batch_id,
    )

    assert result.stage_name == "test_silver"
    assert result.rows_inserted == 4
    assert result.rows_updated == 2
    assert result.rows_quarantined == 0

@patch(    "pipeline_framework.stages.pipeline_stage",    side_effect=lambda *args, **kwargs: nullcontext(),)
def test_execute_silver_stage_returns_quarantine_count(
    mock_pipeline_stage,
):
    context = PipelineContext(
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    loader = Mock(
        return_value=FakeQuarantineSilverResult(
            rows_inserted=3,
            rows_updated=1,
            rows_quarantined=7,
        )
    )

    result = execute_silver_stage(
        stage_name="test_silver",
        context=context,
        loader=loader,
    )

    assert result.rows_inserted == 3
    assert result.rows_updated == 1
    assert result.rows_quarantined == 7

@patch("pipeline_framework.stages.pipeline_stage",    side_effect=lambda *args, **kwargs: nullcontext(),)
def test_execute_silver_stage_propagates_loader_failure(
    mock_pipeline_stage,
):
    context = PipelineContext(
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    loader = Mock(
        side_effect=RuntimeError("Silver load failed"),
    )

    # try:
    with pytest.raises(RuntimeError, match="Silver load failed"):
        execute_silver_stage(
            stage_name="test_silver",
            context=context,
            loader=loader,
        )

@patch("pipeline_framework.entity.execute_silver_stage")
@patch("pipeline_framework.entity.execute_bronze_stage")
def test_execute_entity_pipeline_runs_bronze_then_silver(
    mock_execute_bronze_stage,
    mock_execute_silver_stage,
):
    context = PipelineContext(
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    extractor = Mock()
    bronze_loader = Mock()
    silver_loader = Mock()

    entity = EntityPipeline(
        name="customers",
        extractor=extractor,
        bronze_loader=bronze_loader,
        silver_loader=silver_loader,
    )
    '''Refactor: Use side_effect to record call order and return results'''
    # bronze_result = StageResult(
    #     stage_name="customers_bronze",
    #     rows_inserted=5,
    # )

    # silver_result = StageResult(
    #     stage_name="customers_silver",
    #     rows_inserted=4,
    #     rows_updated=1,
    # )

    # mock_execute_bronze_stage.return_value = bronze_result
    # mock_execute_silver_stage.return_value = silver_result
    call_order = []

    bronze_result = StageResult(
        stage_name="customers_bronze",
        rows_inserted=5,
    )

    silver_result = StageResult(
        stage_name="customers_silver",
        rows_inserted=4,
        rows_updated=1,
    )

    def bronze_side_effect(*args, **kwargs):
        call_order.append("bronze")
        return bronze_result

    def silver_side_effect(*args, **kwargs):
        call_order.append("silver")
        return silver_result

    mock_execute_bronze_stage.side_effect = bronze_side_effect
    mock_execute_silver_stage.side_effect = silver_side_effect

    results = execute_entity_pipeline(
        entity=entity,
        context=context,
    )

    mock_execute_bronze_stage.assert_called_once_with(
        stage_name="customers_bronze",
        context=context,
        extractor=extractor,
        loader=bronze_loader,
    )

    mock_execute_silver_stage.assert_called_once_with(
        stage_name="customers_silver",
        context=context,
        loader=silver_loader,
    )

    assert results == [
        bronze_result,
        silver_result,
    ]

    assert call_order == [
        "bronze",
        "silver",
    ]    