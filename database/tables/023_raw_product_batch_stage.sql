IF OBJECT_ID('raw.ProductBatchStage', 'U') IS NULL
BEGIN
    CREATE TABLE raw.ProductBatchStage
    (
        PipelineRunID UNIQUEIDENTIFIER NOT NULL,
        ProductID INT NOT NULL,
        ProductName NVARCHAR(200) NOT NULL,
        Category NVARCHAR(100) NULL,
        UnitCost DECIMAL(18, 2) NOT NULL,
        UnitPrice DECIMAL(18, 2) NOT NULL,
        RecordHash VARBINARY(32) NOT NULL
    );
END;
GO