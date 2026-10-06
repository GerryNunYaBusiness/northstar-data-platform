CREATE OR ALTER PROCEDURE silver.usp_LoadCustomers
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
            Update Customers that already exist in Silver
            when their business state has changed.

            BatchID scopes this transformation to the
            specific logical source snapshot being processed.
        */
        UPDATE S
        SET
            S.FirstName = R.FirstName,
            S.LastName = R.LastName,
            S.Email = R.Email,
            S.Phone = R.Phone,
            S.RecordHash = R.RecordHash,
            S.SourceIngestedAt = R.IngestedAt,
            S.ProcessedAt = SYSUTCDATETIME()
        FROM silver.Customers AS S
        INNER JOIN raw.Customers AS R
            ON R.CustomerID = S.CustomerID
        WHERE R.BatchID = @BatchID
          AND R.RecordHash <> S.RecordHash;

        SET @RowsUpdated = @@ROWCOUNT;

        /*
            Insert Customers from this batch that do not
            currently exist in Silver.
        */
        INSERT INTO silver.Customers
        (
            CustomerID,
            FirstName,
            LastName,
            Email,
            Phone,
            RecordHash,
            SourceIngestedAt,
            ProcessedAt
        )
        SELECT
            R.CustomerID,
            R.FirstName,
            R.LastName,
            R.Email,
            R.Phone,
            R.RecordHash,
            R.IngestedAt,
            SYSUTCDATETIME()
        FROM raw.Customers AS R
        WHERE R.BatchID = @BatchID
          AND NOT EXISTS
          (
              SELECT 1
              FROM silver.Customers AS S
              WHERE S.CustomerID = R.CustomerID
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