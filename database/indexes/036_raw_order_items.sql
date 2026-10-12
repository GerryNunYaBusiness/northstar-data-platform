IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.OrderItems')
        AND name =            'UX_RawOrderItems_BatchID_OrderItemID'
)
CREATE UNIQUE INDEX UX_RawOrderItems_BatchID_OrderItemID
ON raw.OrderItems (BatchID, OrderItemID);
GO