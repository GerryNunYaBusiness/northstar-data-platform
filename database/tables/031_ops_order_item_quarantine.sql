IF OBJECT_ID('ops.OrderItemQuarantine', 'U') IS NULL
BEGIN
    CREATE TABLE ops.OrderItemQuarantine
    (
        OrderItemQuarantineID BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_OrderItemQuarantine PRIMARY KEY,

        PipelineRunID UNIQUEIDENTIFIER NOT NULL,
        BatchID UNIQUEIDENTIFIER NOT NULL,

        OrderItemID INT NULL,
        OrderID INT NULL,
        ProductID INT NULL,
        Quantity INT NULL,
        UnitPrice DECIMAL(18,2) NULL,

        FailureReason NVARCHAR(1000) NOT NULL,

        QuarantinedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_OrderItemQuarantine_QuarantinedAt
            DEFAULT SYSUTCDATETIME()
    );
END;
GO