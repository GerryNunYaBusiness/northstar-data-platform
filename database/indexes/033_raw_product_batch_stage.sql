IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'IX_ProductBatchStage_PipelineRun'
      AND object_id = OBJECT_ID('raw.ProductBatchStage')
)
BEGIN
    CREATE INDEX IX_ProductBatchStage_PipelineRun
        ON raw.ProductBatchStage (
            PipelineRunID,
            ProductID
        );
END;
GO