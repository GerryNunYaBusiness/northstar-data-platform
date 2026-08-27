from dataclasses import dataclass

from database import get_warehouse_connection


@dataclass
class PipelineResult:
    pipeline_run_id: int
    status: str
    rows_inserted: int
    rows_updated: int
    error_message: str | None


def run_warehouse_pipeline() -> PipelineResult:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("EXEC dbo.usp_LoadNorthstarWarehouse;")

        cursor.execute("""
            SELECT TOP (1)
                PRL.PipelineRunID,
                PRL.[Status],
                PRL.RowsInserted,
                PRL.RowsUpdated,
                PRL.ErrorMessage
            FROM dbo.PipelineRunLog PRL
            ORDER BY PRL.PipelineRunID DESC;
        """)

        row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                "Pipeline executed but no PipelineRunLog record was found."
            )

        return PipelineResult(
            pipeline_run_id=row.PipelineRunID,
            status=row.Status,
            rows_inserted=row.RowsInserted or 0,
            rows_updated=row.RowsUpdated or 0,
            error_message=row.ErrorMessage,
        )