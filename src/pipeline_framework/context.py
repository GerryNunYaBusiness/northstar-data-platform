from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class PipelineContext:
    pipeline_run_id: UUID
    batch_id: UUID