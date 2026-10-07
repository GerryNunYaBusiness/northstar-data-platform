IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.OrderBatchStage')
        AND name =            'IX_RawOrderBatchStage_PipelineRunID_OrderID'
)
CREATE INDEX IX_RawOrderBatchStage_PipelineRunID_OrderID
ON raw.OrderBatchStage
(
    PipelineRunID,
    OrderID
);
GO