IF OBJECT_ID('ops.OrderQuarantine', 'U') IS NULL
BEGIN
    CREATE TABLE ops.OrderQuarantine
    (
        OrderQuarantineID BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_OrderQuarantine PRIMARY KEY,

        PipelineRunID UNIQUEIDENTIFIER NOT NULL,
        BatchID UNIQUEIDENTIFIER NOT NULL,

        OrderID INT NULL,
        CustomerID INT NULL,
        OrderDate DATETIME2(7) NULL,
        [Status] NVARCHAR(50) NULL,
        TotalAmount DECIMAL(18, 2) NULL,

        FailureReason NVARCHAR(500) NOT NULL,

        QuarantinedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_OrderQuarantine_QuarantinedAt
            DEFAULT SYSUTCDATETIME()
    );
END;
GO