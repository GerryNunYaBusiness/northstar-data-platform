IF OBJECT_ID('silver.OrderItems', 'U') IS NULL
BEGIN
    CREATE TABLE silver.OrderItems
    (
        OrderItemID INT NOT NULL
            CONSTRAINT PK_SilverOrderItems PRIMARY KEY,

        OrderID INT NOT NULL,
        ProductID INT NOT NULL,
        Quantity INT NOT NULL,
        UnitPrice DECIMAL(18,2) NOT NULL,

        RecordHash VARBINARY(32) NOT NULL,
        SourceIngestedAt DATETIME2(7) NOT NULL,

        ProcessedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_SilverOrderItems_ProcessedAt
            DEFAULT SYSUTCDATETIME()
    );
END;
GO