IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.Orders')
        AND name =            'UX_RawOrders_BatchID_OrderID'
)
CREATE UNIQUE INDEX UX_RawOrders_BatchID_OrderID
ON raw.Orders
(
    BatchID,
    OrderID
);
GO