from uuid import UUID

from database import get_warehouse_connection


def record_pipeline_event(
    *,
    pipeline_name: str,
    event_type: str,
    pipeline_run_id: UUID | None = None,
    batch_id: UUID | None = None,
    stage_name: str | None = None,
    dag_run_id: str | None = None,
    try_number: int | None = None,
    error_type: str | None = None,
    event_message: str | None = None,
) -> None:
    sql = """
        INSERT INTO ops.PipelineEvents
        (
            PipelineRunID,
            BatchID,
            PipelineName,
            StageName,
            EventType,
            DagRunID,
            TryNumber,
            ErrorType,
            EventMessage
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            sql,
            (
                str(pipeline_run_id)
                if pipeline_run_id is not None
                else None,

                str(batch_id)
                if batch_id is not None
                else None,

                pipeline_name,
                stage_name,
                event_type,
                dag_run_id,
                try_number,
                error_type,
                event_message,
            ),
        )

        connection.commit()