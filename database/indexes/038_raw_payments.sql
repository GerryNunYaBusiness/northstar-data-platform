IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.Payments')
        AND name =            'UX_RawPayments_BatchID_PaymentID'
)
CREATE UNIQUE INDEX UX_RawPayments_BatchID_PaymentID
ON raw.Payments
(
    BatchID,
    PaymentID
);
GO