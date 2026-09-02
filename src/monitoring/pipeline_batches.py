from datetime import datetime, timezone
from uuid import UUID

from database import get_warehouse_connection


def start_batch(
    batch_id: UUID,
    pipeline_name: str,
) -> None:
    with get_warehouse_connection() as connection:
        connection.execute(
            """
            INSERT INTO ops.PipelineBatches
            (
                BatchID,
                PipelineName,
                StartedAt,
                [Status]
            )
            VALUES (?, ?, ?, ?);
            """,
            str(batch_id),
            pipeline_name,
            datetime.now(timezone.utc),
            "RUNNING",
        )

        connection.commit()

def complete_batch(
    batch_id: UUID,
    status: str,
    rows_processed: int | None = None,
    error_message: str | None = None,
) -> None:
    with get_warehouse_connection() as connection:
        connection.execute(
            """
            UPDATE ops.PipelineBatches
            SET
                CompletedAt = ?,
                [Status] = ?,
                RowsProcessed = ?,
                ErrorMessage = ?
            WHERE BatchID = ?;
            """,
            datetime.now(timezone.utc),
            status,
            rows_processed,
            error_message,
            str(batch_id),
        )

        connection.commit()

def batch_is_successful(
    batch_id: UUID,
) -> bool:
    with get_warehouse_connection() as connection:
        row = connection.execute(
            """
            SELECT PB.[Status]
            FROM ops.PipelineBatches AS PB
            WHERE PB.BatchID = ?;
            """,
            str(batch_id),
        ).fetchone()

    return row is not None and row[0] == "SUCCESS"

def begin_or_retry_batch(
    batch_id: UUID,
    pipeline_name: str,
) -> None:
    with get_warehouse_connection() as connection:
        row = connection.execute(
            """
            SELECT PB.[Status]
            FROM ops.PipelineBatches AS PB
            WHERE PB.BatchID = ?;
            """,
            str(batch_id),
        ).fetchone()

        now = datetime.now(timezone.utc)

        if row is None:
            connection.execute(
                """
                INSERT INTO ops.PipelineBatches
                (
                    BatchID,
                    PipelineName,
                    StartedAt,
                    [Status]
                )
                VALUES (?, ?, ?, 'RUNNING');
                """,
                str(batch_id),
                pipeline_name,
                now,
            )

        elif row[0] == "FAILED":
            connection.execute(
                """
                UPDATE ops.PipelineBatches
                SET
                    StartedAt = ?,
                    CompletedAt = NULL,
                    [Status] = 'RUNNING',
                    RowsProcessed = NULL,
                    ErrorMessage = NULL
                WHERE BatchID = ?;
                """,
                now,
                str(batch_id),
            )

        elif row[0] == "SUCCESS":
            raise ValueError(
                f"Batch {batch_id} has already completed successfully."
            )

        elif row[0] == "RUNNING":
            raise ValueError(
                f"Batch {batch_id} is already running."
            )

        connection.commit()