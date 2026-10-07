IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.PaymentBatchStage')
        AND name =            'IX_RawPaymentBatchStage_PipelineRunID_PaymentID'
)
CREATE INDEX IX_RawPaymentBatchStage_PipelineRunID_PaymentID
ON raw.PaymentBatchStage
(
    PipelineRunID,
    PaymentID
);
GO