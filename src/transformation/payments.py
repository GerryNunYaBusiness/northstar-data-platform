from dataclasses import dataclass
from uuid import UUID

from database import get_warehouse_connection


@dataclass(frozen=True)
class PaymentTransformationResult:
    rows_inserted: int
    rows_updated: int
    rows_quarantined: int


def load_silver_payments(
    pipeline_run_id: UUID,
    batch_id: UUID,
) -> PaymentTransformationResult:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            EXEC silver.usp_LoadPayments
                @PipelineRunID = ?,
                @BatchID = ?;
            """,
            pipeline_run_id,
            batch_id,
        )

        row = cursor.fetchone()

        connection.commit()

        return PaymentTransformationResult(
            rows_inserted=row.RowsInserted,
            rows_updated=row.RowsUpdated,
            rows_quarantined=row.RowsQuarantined,
        )