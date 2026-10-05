IF OBJECT_ID('raw.Payments', 'U') IS NULL
BEGIN
    CREATE TABLE raw.Payments
    (
        PaymentID INT NOT NULL,
        OrderID INT NOT NULL,
        PaymentDate DATETIME2(7) NOT NULL,
        PaymentMethod NVARCHAR(50) NOT NULL,
        Amount DECIMAL(18,2) NOT NULL,
        [Status] NVARCHAR(50) NOT NULL,

        IngestedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_RawPayments_IngestedAt
            DEFAULT SYSUTCDATETIME(),

        PipelineRunID UNIQUEIDENTIFIER NOT NULL,
        BatchID UNIQUEIDENTIFIER NOT NULL,
        RecordHash VARBINARY(32) NOT NULL
    );
END;
GO