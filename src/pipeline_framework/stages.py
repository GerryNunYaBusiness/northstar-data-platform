from collections.abc import Callable
# from typing import Any
from uuid import UUID
from typing import TypeVar

TRecord = TypeVar("TRecord")

from pipeline_framework.context import PipelineContext
from pipeline_framework.results import StageResult
from monitoring.pipeline_runs import pipeline_stage
from pipeline_framework.contracts import SilverResult

def execute_bronze_stage(
    stage_name: str,
    context: PipelineContext,
    extractor: Callable[[], list[TRecord]],
    loader: Callable[[list[TRecord], UUID, UUID], int,    ],
) -> StageResult:
    with pipeline_stage(
        context.pipeline_run_id,
        stage_name,
    ):
        records = extractor()

        rows_inserted = loader(
            records,
            context.pipeline_run_id,
            context.batch_id,
        )

    return StageResult(
        stage_name=stage_name,
        rows_inserted=rows_inserted,
    )

def execute_silver_stage(
    stage_name: str,
    context: PipelineContext,
    loader: Callable[[UUID, UUID], SilverResult,    ],
) -> StageResult:
    with pipeline_stage(
        context.pipeline_run_id,
        stage_name,
    ):
        result = loader(
            context.pipeline_run_id,
            context.batch_id,
        )

    return StageResult(
        stage_name=stage_name,
        rows_inserted=result.rows_inserted,
        rows_updated=result.rows_updated,
        rows_quarantined=getattr(
            result,
            "rows_quarantined",
            0,
        ),
    )