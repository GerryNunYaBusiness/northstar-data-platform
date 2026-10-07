CREATE OR ALTER PROCEDURE raw.usp_LoadProductsForBatch
    @BatchID UNIQUEIDENTIFIER,
    @PipelineRunID UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @RowsInserted INT = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO raw.Products
        (
            ProductID,
            ProductName,
            Category,
            UnitCost,
            UnitPrice,
            PipelineRunID,
            BatchID,
            RecordHash
        )
        SELECT
            S.ProductID,
            S.ProductName,
            S.Category,
            S.UnitCost,
            S.UnitPrice,
            @PipelineRunID,
            @BatchID,
            S.RecordHash
        FROM raw.ProductBatchStage AS S
        WHERE S.PipelineRunID = @PipelineRunID
          AND NOT EXISTS
          (
              SELECT 1
              FROM raw.Products AS P
              WHERE P.BatchID = @BatchID
                AND P.ProductID = S.ProductID
          );

        SET @RowsInserted = @@ROWCOUNT;

        DELETE FROM raw.ProductBatchStage
        WHERE PipelineRunID = @PipelineRunID;

        COMMIT TRANSACTION;

        SELECT @RowsInserted AS RowsInserted;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO