from dataclasses import dataclass
from uuid import UUID

from database import get_warehouse_connection


@dataclass(frozen=True)
class OrderTransformationResult:
    rows_inserted: int
    rows_updated: int
    rows_quarantined: int


def load_silver_orders(
    pipeline_run_id: UUID,
    batch_id: UUID,
) -> OrderTransformationResult:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            EXEC silver.usp_LoadOrders
                @PipelineRunID = ?,
                @BatchID = ?;
            """,
            pipeline_run_id,
            batch_id,
        )

        row = cursor.fetchone()

        connection.commit()

        return OrderTransformationResult(
            rows_inserted=row.RowsInserted,
            rows_updated=row.RowsUpdated,
            rows_quarantined=row.RowsQuarantined,
        )