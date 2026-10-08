from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, TypeVar
from uuid import UUID

from pipeline_framework.contracts import SilverResult
from pipeline_framework.context import PipelineContext
from pipeline_framework.results import StageResult
from pipeline_framework.stages import execute_bronze_stage,    execute_silver_stage

TRecord = TypeVar("TRecord")


@dataclass(frozen=True)
class EntityPipeline(Generic[TRecord]):
    name: str
    extractor: Callable[[], list[TRecord]]
    bronze_loader: Callable[
        [list[TRecord], UUID, UUID],
        int,
    ]
    silver_loader: Callable[
        [UUID, UUID],
        SilverResult,
    ]

def execute_entity_pipeline(
    entity: EntityPipeline[TRecord],
    context: PipelineContext,
) -> list[StageResult]:
    bronze_result = execute_bronze_stage(
        stage_name=f"{entity.name}_bronze",
        context=context,
        extractor=entity.extractor,
        loader=entity.bronze_loader,
    )

    silver_result = execute_silver_stage(
        stage_name=f"{entity.name}_silver",
        context=context,
        loader=entity.silver_loader,
    )

    return [
        bronze_result,
        silver_result,
    ]