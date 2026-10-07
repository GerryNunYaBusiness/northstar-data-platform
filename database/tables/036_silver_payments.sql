IF OBJECT_ID('silver.Payments', 'U') IS NULL
BEGIN
    CREATE TABLE silver.Payments
    (
        PaymentID INT NOT NULL
            CONSTRAINT PK_SilverPayments PRIMARY KEY,

        OrderID INT NOT NULL,
        PaymentDate DATETIME2(7) NOT NULL,
        PaymentMethod NVARCHAR(50) NOT NULL,
        Amount DECIMAL(18,2) NOT NULL,
        [Status] NVARCHAR(50) NOT NULL,

        RecordHash VARBINARY(32) NOT NULL,
        SourceIngestedAt DATETIME2(7) NOT NULL,

        ProcessedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_SilverPayments_ProcessedAt
            DEFAULT SYSUTCDATETIME()
    );
END;
GO