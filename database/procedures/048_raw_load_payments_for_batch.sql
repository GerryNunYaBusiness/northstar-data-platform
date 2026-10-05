CREATE OR ALTER PROCEDURE raw.usp_LoadPaymentsForBatch
    @BatchID UNIQUEIDENTIFIER,
    @PipelineRunID UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @RowsInserted INT = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO raw.Payments
        (
            PaymentID,
            OrderID,
            PaymentDate,
            PaymentMethod,
            Amount,
            [Status],
            PipelineRunID,
            BatchID,
            RecordHash
        )
        SELECT
            S.PaymentID,
            S.OrderID,
            S.PaymentDate,
            S.PaymentMethod,
            S.Amount,
            S.[Status],
            @PipelineRunID,
            @BatchID,
            S.RecordHash
        FROM raw.PaymentBatchStage AS S
        WHERE S.PipelineRunID = @PipelineRunID
          AND NOT EXISTS
          (
              SELECT 1
              FROM raw.Payments AS P
              WHERE P.BatchID = @BatchID
                AND P.PaymentID = S.PaymentID
          );

        SET @RowsInserted = @@ROWCOUNT;

        DELETE S
        FROM raw.PaymentBatchStage AS S
        WHERE S.PipelineRunID = @PipelineRunID;

        COMMIT TRANSACTION;

        SELECT
            @RowsInserted AS RowsInserted;

    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO