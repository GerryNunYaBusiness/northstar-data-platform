IF OBJECT_ID('raw.OrderBatchStage', 'U') IS NULL
BEGIN
    CREATE TABLE raw.OrderBatchStage
    (
        PipelineRunID UNIQUEIDENTIFIER NOT NULL,

        OrderID INT NOT NULL,
        CustomerID INT NOT NULL,
        OrderDate DATETIME2(7) NOT NULL,
        [Status] NVARCHAR(50) NOT NULL,
        TotalAmount DECIMAL(18, 2) NOT NULL,

        RecordHash VARBINARY(32) NOT NULL
    );
END;
GO