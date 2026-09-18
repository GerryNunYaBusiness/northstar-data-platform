CREATE OR ALTER VIEW ops.vw_PipelineRunMetrics
AS

SELECT
    PR.PipelineRunID,
    PR.PipelineName,
    PR.StartedAt,
    PR.CompletedAt,
    PR.[Status],

    DATEDIFF(
        MILLISECOND,
        PR.StartedAt,
        PR.CompletedAt
    ) AS DurationMs,

    PR.ErrorMessage
FROM ops.PipelineRuns AS PR;
GO

CREATE OR ALTER VIEW ops.vw_PipelineStageMetrics
AS

SELECT
    PSR.PipelineStageRunID,
    PSR.PipelineRunID,
    PSR.StageName,
    PSR.StartedAt,
    PSR.CompletedAt,
    PSR.[Status],
    PSR.RowsProcessed,

    DATEDIFF(
        MILLISECOND,
        PSR.StartedAt,
        PSR.CompletedAt
    ) AS DurationMs,

    PSR.ErrorMessage
FROM ops.PipelineStageRuns AS PSR;
GO
GO