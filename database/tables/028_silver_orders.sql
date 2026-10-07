IF OBJECT_ID('silver.Orders', 'U') IS NULL
BEGIN
    CREATE TABLE silver.Orders
    (
        OrderID INT NOT NULL
            CONSTRAINT PK_SilverOrders PRIMARY KEY,

        CustomerID INT NOT NULL,
        OrderDate DATETIME2(7) NOT NULL,
        [Status] NVARCHAR(50) NOT NULL,
        TotalAmount DECIMAL(18, 2) NOT NULL,

        RecordHash VARBINARY(32) NOT NULL,
        SourceIngestedAt DATETIME2(7) NOT NULL,

        ProcessedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_SilverOrders_ProcessedAt
            DEFAULT SYSUTCDATETIME()
    );
END;
GO