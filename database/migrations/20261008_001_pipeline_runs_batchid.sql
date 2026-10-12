IF COL_LENGTH('ops.PipelineRuns', 'BatchID') IS NULL
BEGIN
    ALTER TABLE ops.PipelineRuns
    ADD BatchID UNIQUEIDENTIFIER NULL;
END;

IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes AS I
    WHERE I.object_id = OBJECT_ID('ops.PipelineRuns')
      AND I.name = 'IX_PipelineRuns_BatchID'
)
BEGIN
    CREATE INDEX IX_PipelineRuns_BatchID
    ON ops.PipelineRuns
    (
        BatchID,
        StartedAt
    );
END;