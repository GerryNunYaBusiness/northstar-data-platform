CREATE OR ALTER PROCEDURE [silver].[usp_LoadCustomers]
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @ProcessedAt DATETIME2 = SYSUTCDATETIME();
    DECLARE @RowsInserted INT = 0;
    DECLARE @RowsUpdated INT = 0;

    BEGIN TRY

        BEGIN TRANSACTION;

        /* Update existing customers whose source data changed */

        UPDATE SC
        SET
            SC.FirstName = RC.FirstName,
            SC.LastName = RC.LastName,
            SC.Email = RC.Email,
            SC.Phone = RC.Phone,
            SC.CreatedAt = RC.CreatedAt,
            SC.RecordHash = RC.RecordHash,
            SC.SourceIngestedAt = RC.IngestedAt,
            SC.ProcessedAt = @ProcessedAt
        FROM silver.Customers SC
        INNER JOIN raw.vw_LatestCustomers RC
            ON RC.CustomerID = SC.CustomerID
        WHERE
            RC.RecordHash IS NOT NULL
            AND SC.RecordHash <> RC.RecordHash;

        SET @RowsUpdated = @@ROWCOUNT;


        /* Insert customers that do not exist in Silver */

        INSERT INTO silver.Customers
        (
            CustomerID,
            FirstName,
            LastName,
            Email,
            Phone,
            CreatedAt,
            RecordHash,
            SourceIngestedAt,
            ProcessedAt
        )
        SELECT
            RC.CustomerID,
            RC.FirstName,
            RC.LastName,
            RC.Email,
            RC.Phone,
            RC.CreatedAt,
            RC.RecordHash,
            RC.IngestedAt,
            @ProcessedAt
        FROM raw.vw_LatestCustomers RC
        WHERE
            RC.RecordHash IS NOT NULL
            AND NOT EXISTS
            (
                SELECT 1
                FROM silver.Customers SC
                WHERE SC.CustomerID = RC.CustomerID
            );

        SET @RowsInserted = @@ROWCOUNT;

        COMMIT TRANSACTION;

        SELECT
            @RowsInserted AS RowsInserted,
            @RowsUpdated AS RowsUpdated;

    END TRY
    BEGIN CATCH

        IF @@TRANCOUNT > 0
            ROLLBACK TRANSACTION;

        THROW;

    END CATCH;
END;