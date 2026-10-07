from dataclasses import dataclass
from uuid import UUID

from database import get_warehouse_connection


@dataclass(frozen=True)
class ProductTransformationResult:
    rows_inserted: int
    rows_updated: int


def load_silver_products(
    pipeline_run_id: UUID,
    batch_id: UUID,
) -> ProductTransformationResult:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            EXEC silver.usp_LoadProducts
                @PipelineRunID = ?,
                @BatchID = ?;
            """,
            pipeline_run_id,
            batch_id,
        )

        row = cursor.fetchone()

        connection.commit()

        return ProductTransformationResult(
            rows_inserted=row.RowsInserted,
            rows_updated=row.RowsUpdated,
        )