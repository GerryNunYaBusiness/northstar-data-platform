IF NOT EXISTS
(
    SELECT 1
    FROM sys.indexes
    WHERE name = 'UX_RawProducts_Batch_Product'
      AND object_id = OBJECT_ID('raw.Products')
)
BEGIN
    CREATE UNIQUE INDEX UX_RawProducts_Batch_Product
        ON raw.Products (BatchID, ProductID);
END;
GO