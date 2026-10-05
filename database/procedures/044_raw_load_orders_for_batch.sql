CREATE OR ALTER PROCEDURE raw.usp_LoadOrdersForBatch
    @BatchID UNIQUEIDENTIFIER,
    @PipelineRunID UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @RowsInserted INT = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO raw.Orders
        (
            OrderID,
            CustomerID,
            OrderDate,
            [Status],
            TotalAmount,
            PipelineRunID,
            BatchID,
            RecordHash
        )
        SELECT
            S.OrderID,
            S.CustomerID,
            S.OrderDate,
            S.[Status],
            S.TotalAmount,
            @PipelineRunID,
            @BatchID,
            S.RecordHash
        FROM raw.OrderBatchStage AS S
        WHERE S.PipelineRunID = @PipelineRunID
          AND NOT EXISTS
          (
              SELECT 1
              FROM raw.Orders AS O
              WHERE O.BatchID = @BatchID
                AND O.OrderID = S.OrderID
          );

        SET @RowsInserted = @@ROWCOUNT;

        DELETE S
        FROM raw.OrderBatchStage AS S
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