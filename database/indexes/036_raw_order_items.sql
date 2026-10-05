IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.OrderItems')
        AND name =            'UX_RawOrdersItems_BatchID_OrderID'
)
CREATE UNIQUE INDEX UX_RawOrdersItems_BatchID_OrderID
ON raw.OrderItems
(
    BatchID,
    OrderID
);
GO