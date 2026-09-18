CREATE OR ALTER PROCEDURE
    raw.usp_LoadCustomersForBatch
    @BatchID UNIQUEIDENTIFIER,
    @PipelineRunID UNIQUEIDENTIFIER
AS
BEGIN
        SET NOCOUNT ON;
        SET XACT_ABORT ON;

        BEGIN TRY
            BEGIN TRANSACTION;

            INSERT INTO raw.Customers
            (
                CustomerID,
                FirstName,
                LastName,
                Email,
                Phone,
                CreatedAt,
                IngestedAt,
                PipelineRunID,
                BatchID,
                RecordHash
            )
            SELECT
                S.CustomerID,
                S.FirstName,
                S.LastName,
                S.Email,
                S.Phone,
                S.CreatedAt,
                SYSUTCDATETIME(),
                @PipelineRunID,
                @BatchID,
                S.RecordHash
            FROM raw.CustomerBatchStage AS S
            WHERE S.PipelineRunID = @PipelineRunID
            AND NOT EXISTS
            (
                SELECT 1
                FROM raw.Customers AS RC
                WHERE RC.BatchID = @BatchID
                    AND RC.CustomerID = S.CustomerID
            );

            DECLARE @RowsInserted INT = @@ROWCOUNT;

            DELETE FROM raw.CustomerBatchStage
            WHERE PipelineRunID = @PipelineRunID;

            COMMIT TRANSACTION;

            SELECT @RowsInserted AS RowsInserted;
        END TRY
        BEGIN CATCH
            IF @@TRANCOUNT > 0
                ROLLBACK TRANSACTION;

            THROW;
        END CATCH;

END;
GO