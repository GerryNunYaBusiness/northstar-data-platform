IF OBJECT_ID('raw.PaymentBatchStage', 'U') IS NULL
BEGIN
    CREATE TABLE raw.PaymentBatchStage
    (
        PipelineRunID UNIQUEIDENTIFIER NOT NULL,

        PaymentID INT NOT NULL,
        OrderID INT NOT NULL,
        PaymentDate DATETIME2(7) NOT NULL,
        PaymentMethod NVARCHAR(50) NOT NULL,
        Amount DECIMAL(18,2) NOT NULL,
        [Status] NVARCHAR(50) NOT NULL,

        RecordHash VARBINARY(32) NOT NULL
    );
END;
GO