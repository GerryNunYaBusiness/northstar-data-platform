IF OBJECT_ID('raw.OrderItemBatchStage', 'U') IS NULL
BEGIN
    CREATE TABLE raw.OrderItemBatchStage
    (
        PipelineRunID UNIQUEIDENTIFIER NOT NULL,

        OrderItemID INT NOT NULL,
        OrderID INT NOT NULL,
        ProductID INT NOT NULL,
        Quantity INT NOT NULL,
        UnitPrice DECIMAL(18, 2) NOT NULL,

        RecordHash VARBINARY(32) NOT NULL
    );
END;
GO