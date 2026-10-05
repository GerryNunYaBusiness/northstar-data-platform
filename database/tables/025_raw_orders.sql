IF OBJECT_ID('raw.Orders', 'U') IS NULL
BEGIN
    CREATE TABLE raw.Orders
    (
        OrderID INT NOT NULL,
        CustomerID INT NOT NULL,
        OrderDate DATETIME2(7) NOT NULL,
        [Status] NVARCHAR(50) NOT NULL,
        TotalAmount DECIMAL(18, 2) NOT NULL,

        IngestedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_RawOrders_IngestedAt
            DEFAULT SYSUTCDATETIME(),

        PipelineRunID UNIQUEIDENTIFIER NOT NULL,
        BatchID UNIQUEIDENTIFIER NOT NULL,
        RecordHash VARBINARY(32) NOT NULL
    );
END;
GO
