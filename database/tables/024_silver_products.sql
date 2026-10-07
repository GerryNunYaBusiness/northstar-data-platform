IF OBJECT_ID('silver.Products', 'U') IS NULL
BEGIN
    CREATE TABLE silver.Products
    (
        ProductID INT NOT NULL
            CONSTRAINT PK_SilverProducts PRIMARY KEY,

        ProductName NVARCHAR(200) NOT NULL,
        Category NVARCHAR(100) NULL,
        UnitCost DECIMAL(18, 2) NOT NULL,
        UnitPrice DECIMAL(18, 2) NOT NULL,

        RecordHash VARBINARY(32) NOT NULL,
        SourceIngestedAt DATETIME2(7) NOT NULL,

        ProcessedAt DATETIME2(7) NOT NULL
            CONSTRAINT DF_SilverProducts_ProcessedAt
            DEFAULT SYSUTCDATETIME()
    );
END;
GO