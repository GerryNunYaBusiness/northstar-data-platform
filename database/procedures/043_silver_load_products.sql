CREATE OR ALTER PROCEDURE silver.usp_LoadProducts
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @RowsInserted INT = 0;
    DECLARE @RowsUpdated INT = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        ;WITH LatestProducts AS
        (
            SELECT
                P.ProductID,
                P.ProductName,
                P.Category,
                P.UnitCost,
                P.UnitPrice,
                P.RecordHash,
                P.IngestedAt,
                ROW_NUMBER() OVER
                (
                    PARTITION BY P.ProductID
                    ORDER BY
                        P.IngestedAt DESC,
                        P.PipelineRunID DESC
                ) AS RowNumber
            FROM raw.Products AS P
        )
        UPDATE S
        SET
            S.ProductName = L.ProductName,
            S.Category = L.Category,
            S.UnitCost = L.UnitCost,
            S.UnitPrice = L.UnitPrice,
            S.RecordHash = L.RecordHash,
            S.SourceIngestedAt = L.IngestedAt,
            S.ProcessedAt = SYSUTCDATETIME()
        FROM silver.Products AS S
        INNER JOIN LatestProducts AS L
            ON L.ProductID = S.ProductID
        WHERE L.RowNumber = 1
          AND L.RecordHash <> S.RecordHash;

        SET @RowsUpdated = @@ROWCOUNT;

        ;WITH LatestProducts AS
        (
            SELECT
                P.ProductID,
                P.ProductName,
                P.Category,
                P.UnitCost,
                P.UnitPrice,
                P.RecordHash,
                P.IngestedAt,
                ROW_NUMBER() OVER
                (
                    PARTITION BY P.ProductID
                    ORDER BY
                        P.IngestedAt DESC,
                        P.PipelineRunID DESC
                ) AS RowNumber
            FROM raw.Products AS P
        )
        INSERT INTO silver.Products
        (
            ProductID,
            ProductName,
            Category,
            UnitCost,
            UnitPrice,
            RecordHash,
            SourceIngestedAt
        )
        SELECT
            L.ProductID,
            L.ProductName,
            L.Category,
            L.UnitCost,
            L.UnitPrice,
            L.RecordHash,
            L.IngestedAt
        FROM LatestProducts AS L
        WHERE L.RowNumber = 1
          AND NOT EXISTS
          (
              SELECT 1
              FROM silver.Products AS S
              WHERE S.ProductID = L.ProductID
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