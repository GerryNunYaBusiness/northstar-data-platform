IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE
        object_id =
            OBJECT_ID('ops.PipelineEvents')
        AND name =
            'IX_PipelineEvents_EventType_EventTime'
)
BEGIN
    CREATE INDEX
        IX_PipelineEvents_EventType_EventTime
    ON ops.PipelineEvents
    (
        EventType,
        EventTime
    )
    INCLUDE
    (
        PipelineRunID,
        StageName
    );
END;
GO