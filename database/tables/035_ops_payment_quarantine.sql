IF OBJECT_ID('ops.PaymentQuarantine', 'U') IS NULL
BEGIN
    CREATE TABLE ops.PaymentQuarantine
    (
        PaymentQuarantineID BIGINT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_PaymentQuarantine PRIMARY KEY,

        PipelineRunID UNIQUEIDENTIFIER NOT NULL,
        BatchID UNIQUEIDENTIFIER NOT NULL,

        PaymentID INT NULL,
        OrderID INT NULL,
        PaymentDate DATETIME2(7) NULL,
        PaymentMethod NVARCHAR(50) NULL,
        Amount DECIMAL(18,2) NULL,
        [Status] NVARCHAR(50) NULL,

        FailureReason NVARCHAR(1000) NOT NULL,

        QuarantinedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_PaymentQuarantine_QuarantinedAt
            DEFAULT SYSUTCDATETIME()
    );
END;
GO