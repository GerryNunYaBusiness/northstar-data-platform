IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.OrderItemBatchStage')
        AND name =            'IX_RawOrderItemBatchStage_PipelineRunID_OrderID'
)
CREATE INDEX IX_RawOrderItemBatchStage_PipelineRunID_OrderID
ON raw.OrderItemBatchStage
(
    PipelineRunID,
    OrderID
);
GO