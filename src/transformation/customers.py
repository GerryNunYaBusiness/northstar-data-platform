from dataclasses import dataclass
from uuid import UUID

from database import get_warehouse_connection


@dataclass
class SilverLoadResult:
    rows_inserted: int
    rows_updated: int


def load_silver_customers(
    pipeline_run_id: UUID,
    batch_id: UUID,
) -> SilverLoadResult:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            EXEC silver.usp_LoadCustomers
                @PipelineRunID = ?,
                @BatchID = ?;
            """,
            pipeline_run_id,
            batch_id,
        )
        row = cursor.fetchone()
        connection.commit()

        if row is None:
            raise RuntimeError(
                "Silver customer load returned no result."
            )

        return SilverLoadResult(
            rows_inserted=row.RowsInserted,
            rows_updated=row.RowsUpdated,
        )