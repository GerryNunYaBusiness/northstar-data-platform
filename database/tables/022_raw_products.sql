IF OBJECT_ID('raw.Products', 'U') IS NULL
BEGIN
    CREATE TABLE raw.Products
    (
        ProductID INT NOT NULL,
        ProductName NVARCHAR(200) NOT NULL,
        Category NVARCHAR(100) NULL,
        UnitCost DECIMAL(18, 2) NOT NULL,
        UnitPrice DECIMAL(18, 2) NOT NULL,

        IngestedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_RawProducts_IngestedAt
            DEFAULT SYSUTCDATETIME(),

        PipelineRunID UNIQUEIDENTIFIER NOT NULL,
        BatchID UNIQUEIDENTIFIER NOT NULL,
        RecordHash VARBINARY(32) NOT NULL
    );
END;
GO