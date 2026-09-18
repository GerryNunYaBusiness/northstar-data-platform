CREATE OR ALTER VIEW ops.vw_CustomerPipelineHealth
AS

WITH QuarantineMetrics AS
(
    SELECT
        CQ.PipelineRunID,
        COUNT(DISTINCT CQ.CustomerID) AS InvalidCustomers,
        COUNT(*) AS ValidationErrors
    FROM ops.CustomerQuarantine AS CQ
    GROUP BY CQ.PipelineRunID
),
EventMetrics AS
(    SELECT
        PE.PipelineRunID,
		SUM( CASE WHEN PE.EventType = 'RETRY' THEN 1  ELSE 0  END ) AS RetryCount,
        SUM( CASE WHEN PE.EventType = 'RECOVERED' THEN 1 ELSE 0 END ) AS RecoveryCount
    FROM ops.PipelineEvents AS PE
    GROUP BY PE.PipelineRunID
),
StageMetrics AS
(    SELECT
        PSM.PipelineRunID,
        SUM( CASE  WHEN PSM.StageName = 'bronze' THEN PSM.RowsProcessed  ELSE 0 END ) AS BronzeRowsProcessed, 
        SUM( CASE  WHEN PSM.StageName = 'silver' THEN PSM.RowsProcessed  ELSE 0 END ) AS SilverRowsProcessed, 
        SUM( CASE  WHEN PSM.StageName = 'bronze' THEN PSM.DurationMs     ELSE 0 END ) AS BronzeDurationMs, 
        SUM( CASE  WHEN PSM.StageName = 'silver' THEN PSM.DurationMs     ELSE 0 END ) AS SilverDurationMs
    FROM ops.vw_PipelineStageMetrics AS PSM
    GROUP BY PSM.PipelineRunID
)

SELECT
    PRM.PipelineRunID,
    PRM.PipelineName,
    PRM.StartedAt,
    PRM.CompletedAt,
    PRM.[Status],
    PRM.DurationMs,

    COALESCE( SM.BronzeRowsProcessed,  0    ) AS BronzeRowsProcessed,
    COALESCE( SM.SilverRowsProcessed,  0    ) AS SilverRowsProcessed,
    --COALESCE( SM.BronzeDurationMs,     0    ) AS BronzeDurationMs,
    --COALESCE( SM.SilverDurationMs,     0    ) AS SilverDurationMs,
	SM.BronzeDurationMs AS BronzeDurationMs,
    SM.SilverDurationMs  AS SilverDurationMs,
    COALESCE( QM.InvalidCustomers,     0    ) AS InvalidCustomers,
    COALESCE( QM.ValidationErrors,     0    ) AS ValidationErrors,
    COALESCE( EM.RetryCount,           0    ) AS RetryCount,
	COALESCE( EM.RecoveryCount,        0    ) AS RecoveryCount,
    PRM.ErrorMessage
FROM ops.vw_PipelineRunMetrics AS PRM
	LEFT JOIN StageMetrics AS SM         ON SM.PipelineRunID = PRM.PipelineRunID
	LEFT JOIN QuarantineMetrics AS QM    ON QM.PipelineRunID = PRM.PipelineRunID
	LEFT JOIN EventMetrics AS EM         ON EM.PipelineRunID = PRM.PipelineRunID
WHERE PRM.PipelineName =
    'customer_pipeline';
GO

CREATE OR ALTER VIEW ops.vw_CustomerPipelineDailyMetrics
AS

SELECT
    CAST(CPH.StartedAt AS DATE) AS MetricDate,
    COUNT(*) AS TotalRuns,
    SUM( CASE WHEN CPH.[Status] = 'SUCCESS' THEN 1 ELSE 0 END ) AS SuccessfulRuns,
    SUM( CASE WHEN CPH.[Status] = 'FAILED'  THEN 1 ELSE 0 END ) AS FailedRuns,
    CAST( 100.0 * SUM( CASE WHEN CPH.[Status] = 'SUCCESS' THEN 1 ELSE 0 END ) / NULLIF(COUNT(*), 0) AS DECIMAL(5, 2)  ) AS SuccessRatePct, 
    SUM(CPH.RetryCount) AS RetryCount, 
    SUM(CPH.RecoveryCount) AS RecoveryCount, 
    SUM(CPH.InvalidCustomers)  AS InvalidCustomers, 
    SUM(CPH.ValidationErrors)  AS ValidationErrors, 
    CAST( AVG( CAST( CPH.DurationMs AS DECIMAL(18, 2) ) ) AS DECIMAL(18, 2) ) AS AverageDurationMs, 
    MAX(CPH.DurationMs) AS MaxDurationMs, 
    CAST( AVG( CAST( CPH.BronzeDurationMs AS DECIMAL(18, 2)  ) ) AS DECIMAL(18, 2) ) AS AverageBronzeDurationMs, 
    CAST( AVG( CAST( CPH.SilverDurationMs AS DECIMAL(18, 2) ) )  AS DECIMAL(18, 2) ) AS AverageSilverDurationMs

FROM ops.vw_CustomerPipelineHealth AS CPH
WHERE CPH.CompletedAt IS NOT NULL
GROUP BY    CAST(CPH.StartedAt AS DATE);
GO