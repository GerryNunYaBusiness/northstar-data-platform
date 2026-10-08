from dataclasses import dataclass


@dataclass(frozen=True)
class StageResult:
    stage_name: str
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_quarantined: int = 0