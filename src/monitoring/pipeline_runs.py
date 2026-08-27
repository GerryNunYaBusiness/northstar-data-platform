from datetime import datetime, timezone
from uuid import UUID
from contextlib import contextmanager
from collections.abc import Iterator

from database import get_warehouse_connection

@contextmanager
def pipeline_stage(
    pipeline_run_id: UUID,
    stage_name: str,
) -> Iterator[dict]:

    stage_run_id = start_stage(
        pipeline_run_id,
        stage_name,
    )

    stage_info = {
        "stage_run_id": stage_run_id,
        "rows_processed": None,
    }

    try:
        yield stage_info

    except Exception as exc:
        complete_stage(
            stage_run_id,
            "FAILED",
            rows_processed=stage_info["rows_processed"],
            error_message=str(exc),
        )

        raise

    else:
        complete_stage(
            stage_run_id,
            "SUCCESS",
            rows_processed=stage_info["rows_processed"],
        )

def start_pipeline_run(
    pipeline_run_id: UUID,
    pipeline_name: str,
) -> None:

    started_at = datetime.now(timezone.utc)

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO ops.PipelineRuns
            (
                PipelineRunID,
                PipelineName,
                StartedAt,
                [Status]
            )
            VALUES (?, ?, ?, 'RUNNING');
            """,
            str(pipeline_run_id),
            pipeline_name,
            started_at,
        )

        connection.commit()

def complete_pipeline_run(
    pipeline_run_id: UUID,
    status: str,
    error_message: str | None = None,
) -> None:

    completed_at = datetime.now(timezone.utc)

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE PR
            SET
                PR.CompletedAt = ?,
                PR.[Status] = ?,
                PR.ErrorMessage = ?
            FROM ops.PipelineRuns PR
            WHERE PR.PipelineRunID = ?;
            """,
            completed_at,
            status,
            error_message,
            str(pipeline_run_id),
        )

        connection.commit()

def start_stage(
    pipeline_run_id: UUID,
    stage_name: str,
) -> int:

    started_at = datetime.now(timezone.utc)

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO ops.PipelineStageRuns
            (
                PipelineRunID,
                StageName,
                StartedAt,
                [Status]
            )
            OUTPUT inserted.PipelineStageRunID
            VALUES (?, ?, ?, 'RUNNING');
            """,
            str(pipeline_run_id),
            stage_name,
            started_at,
        )

        row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                "Failed to create pipeline stage record."
            )

        stage_run_id = row.PipelineStageRunID

        connection.commit()

    return stage_run_id

def complete_stage(
    stage_run_id: int,
    status: str,
    rows_processed: int | None = None,
    error_message: str | None = None,
) -> None:

    completed_at = datetime.now(timezone.utc)

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE PSR
            SET
                PSR.CompletedAt = ?,
                PSR.[Status] = ?,
                PSR.RowsProcessed = ?,
                PSR.ErrorMessage = ?
            FROM ops.PipelineStageRuns PSR
            WHERE PSR.PipelineStageRunID = ?;
            """,
            completed_at,
            status,
            rows_processed,
            error_message,
            stage_run_id,
        )

        connection.commit()