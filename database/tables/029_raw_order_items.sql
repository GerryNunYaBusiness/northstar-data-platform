IF OBJECT_ID('raw.OrderItems', 'U') IS NULL
BEGIN
    CREATE TABLE raw.OrderItems
    (
        OrderItemID INT NOT NULL,
        OrderID INT NOT NULL,
        ProductID INT NOT NULL,
        Quantity INT NOT NULL,
        UnitPrice DECIMAL(18, 2) NOT NULL,

        IngestedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_RawOrderItems_IngestedAt
            DEFAULT SYSUTCDATETIME(),

        PipelineRunID UNIQUEIDENTIFIER NOT NULL,
        BatchID UNIQUEIDENTIFIER NOT NULL,
        RecordHash VARBINARY(32) NOT NULL
    );
END;
GO