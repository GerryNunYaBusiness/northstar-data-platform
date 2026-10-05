CREATE OR ALTER PROCEDURE raw.usp_LoadOrderItemsForBatch
    @BatchID UNIQUEIDENTIFIER,
    @PipelineRunID UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @RowsInserted INT = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO raw.OrderItems
        (
            OrderItemID,
            OrderID,
            ProductID,
            Quantity,
            UnitPrice,
            PipelineRunID,
            BatchID,
            RecordHash
        )
        SELECT
            S.OrderItemID,
            S.OrderID,
            S.ProductID,
            S.Quantity,
            S.UnitPrice,
            @PipelineRunID,
            @BatchID,
            S.RecordHash
        FROM raw.OrderItemBatchStage AS S
        WHERE S.PipelineRunID = @PipelineRunID
          AND NOT EXISTS
          (
              SELECT 1
              FROM raw.OrderItems AS OI
              WHERE OI.BatchID = @BatchID
                AND OI.OrderItemID = S.OrderItemID
          );

        SET @RowsInserted = @@ROWCOUNT;

        DELETE S
        FROM raw.OrderItemBatchStage AS S
        WHERE S.PipelineRunID = @PipelineRunID;

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