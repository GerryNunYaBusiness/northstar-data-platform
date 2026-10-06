CREATE OR ALTER PROCEDURE silver.usp_LoadProducts
    @PipelineRunID UNIQUEIDENTIFIER,
    @BatchID UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @RowsInserted INT = 0;
    DECLARE @RowsUpdated INT = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        /*
            Update Products that already exist in Silver
            when their business state has changed.
        */
        UPDATE S
        SET
            S.ProductName = R.ProductName,
            S.Category = R.Category,
            S.UnitCost = R.UnitCost,
            S.UnitPrice = R.UnitPrice,
            S.RecordHash = R.RecordHash,
            S.SourceIngestedAt = R.IngestedAt,
            S.ProcessedAt = SYSUTCDATETIME()
        FROM silver.Products AS S
        INNER JOIN raw.Products AS R
            ON R.ProductID = S.ProductID
        WHERE R.BatchID = @BatchID
          AND R.RecordHash <> S.RecordHash;

        SET @RowsUpdated = @@ROWCOUNT;

        /*
            Insert Products from this batch that do not
            currently exist in Silver.
        */
        INSERT INTO silver.Products
        (
            ProductID,
            ProductName,
            Category,
            UnitCost,
            UnitPrice,
            RecordHash,
            SourceIngestedAt,
            ProcessedAt
        )
        SELECT
            R.ProductID,
            R.ProductName,
            R.Category,
            R.UnitCost,
            R.UnitPrice,
            R.RecordHash,
            R.IngestedAt,
            SYSUTCDATETIME()
        FROM raw.Products AS R
        WHERE R.BatchID = @BatchID
          AND NOT EXISTS
          (
              SELECT 1
              FROM silver.Products AS S
              WHERE S.ProductID = R.ProductID
          );

        SET @RowsInserted = @@ROWCOUNT;

        COMMIT TRANSACTION;

        SELECT
            @RowsInserted AS RowsInserted,
            @RowsUpdated AS RowsUpdated;

    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO