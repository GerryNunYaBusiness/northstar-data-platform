CREATE OR ALTER PROCEDURE silver.usp_LoadOrders
    @PipelineRunID UNIQUEIDENTIFIER,
    @BatchID UNIQUEIDENTIFIER
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    DECLARE @RowsInserted INT = 0;
    DECLARE @RowsUpdated INT = 0;
    DECLARE @RowsQuarantined INT = 0;

    BEGIN TRY
        BEGIN TRANSACTION;

        INSERT INTO ops.OrderQuarantine
        (
            PipelineRunID,
            BatchID,
            OrderID,
            CustomerID,
            OrderDate,
            [Status],
            TotalAmount,
            FailureReason
        )
        SELECT
            @PipelineRunID,
            @BatchID,
            O.OrderID,
            O.CustomerID,
            O.OrderDate,
            O.[Status],
            O.TotalAmount,
            CONCAT(
                CASE
                    WHEN O.OrderID <= 0
                    THEN 'OrderID must be greater than zero; '
                    ELSE ''
                END,
                CASE
                    WHEN O.CustomerID <= 0
                    THEN 'CustomerID must be greater than zero; '
                    ELSE ''
                END,
                CASE
                    WHEN O.[Status] NOT IN
                    (
                        'Pending',
                        'Processing',
                        'Completed',
                        'Cancelled'
                    )
                    THEN 'Invalid order status; '
                    ELSE ''
                END,
                CASE
                    WHEN O.TotalAmount < 0
                    THEN 'TotalAmount must be greater than or equal to zero; '
                    ELSE ''
                END
            )
        FROM raw.Orders AS O
        WHERE O.BatchID = @BatchID
        AND
        (
            O.OrderID <= 0
            OR O.CustomerID <= 0
            OR O.[Status] NOT IN
            (
                'Pending',
                'Processing',
                'Completed',
                'Cancelled'
            )
            OR O.TotalAmount < 0
        )
        AND NOT EXISTS
        (
            SELECT 1
            FROM ops.OrderQuarantine AS Q
            WHERE Q.BatchID = @BatchID
                AND Q.OrderID = O.OrderID
        );

        SET @RowsQuarantined =
            @RowsQuarantined + @@ROWCOUNT;

        /*
            Quarantine Orders whose CustomerID does not currently
            exist in the trusted Silver Customer dataset.

            The quarantine record is historical evidence. It does
            NOT permanently exclude the Order from future processing.
        */
        INSERT INTO ops.OrderQuarantine
        (
            PipelineRunID,
            BatchID,
            OrderID,
            CustomerID,
            OrderDate,
            [Status],
            TotalAmount,
            FailureReason
        )
        SELECT
            @PipelineRunID,
            @BatchID,
            O.OrderID,
            O.CustomerID,
            O.OrderDate,
            O.[Status],
            O.TotalAmount,
            'CustomerID does not exist in silver.Customers'
        FROM raw.Orders AS O
        WHERE O.BatchID = @BatchID
          AND O.OrderID > 0
          AND O.CustomerID > 0
          AND O.[Status] IN
          (
            'Pending',
            'Processing',
            'Completed',
            'Cancelled'
          )
          AND O.TotalAmount >= 0
          AND NOT EXISTS
          (
              SELECT 1
              FROM silver.Customers AS C
              WHERE C.CustomerID = O.CustomerID
          )
          AND NOT EXISTS
          (
              SELECT 1
              FROM ops.OrderQuarantine AS Q
              WHERE Q.BatchID = @BatchID
                AND Q.OrderID = O.OrderID
                AND Q.FailureReason =
                    'CustomerID does not exist in silver.Customers'
          );

        SET @RowsQuarantined =
            @RowsQuarantined + @@ROWCOUNT;

        /*
            Update existing Silver Orders only when:
              1. the Order belongs to this batch
              2. its Customer now exists
              3. its business state changed
        */
        UPDATE S
        SET
            S.CustomerID = O.CustomerID,
            S.OrderDate = O.OrderDate,
            S.[Status] = O.[Status],
            S.TotalAmount = O.TotalAmount,
            S.RecordHash = O.RecordHash,
            S.SourceIngestedAt = O.IngestedAt,
            S.ProcessedAt = SYSUTCDATETIME()
        FROM silver.Orders AS S
        INNER JOIN raw.Orders AS O
            ON O.OrderID = S.OrderID
        INNER JOIN silver.Customers AS C
            ON C.CustomerID = O.CustomerID
        WHERE O.BatchID = @BatchID
          AND O.RecordHash <> S.RecordHash
          AND O.OrderID > 0
            AND O.CustomerID > 0
            AND O.[Status] IN
            (
                'Pending',
                'Processing',
                'Completed',
                'Cancelled'
            )
            AND O.TotalAmount >= 0;

        SET @RowsUpdated = @@ROWCOUNT;

        /*
            Insert Orders that are not yet in Silver and whose
            CustomerID now resolves successfully.
        */
        INSERT INTO silver.Orders
        (
            OrderID,
            CustomerID,
            OrderDate,
            [Status],
            TotalAmount,
            RecordHash,
            SourceIngestedAt
        )
        SELECT
            O.OrderID,
            O.CustomerID,
            O.OrderDate,
            O.[Status],
            O.TotalAmount,
            O.RecordHash,
            O.IngestedAt
        FROM raw.Orders AS O
        INNER JOIN silver.Customers AS C
            ON C.CustomerID = O.CustomerID
        WHERE O.BatchID = @BatchID
          AND NOT EXISTS
          (
              SELECT 1
              FROM silver.Orders AS S
              WHERE S.OrderID = O.OrderID
          )
          AND O.OrderID > 0
          AND O.CustomerID > 0
          AND O.[Status] IN
            (
                'Pending',
                'Processing',
                'Completed',
                'Cancelled'
            )
          AND O.TotalAmount >= 0;

        SET @RowsInserted = @@ROWCOUNT;

        COMMIT TRANSACTION;

        SELECT
            @RowsInserted AS RowsInserted,
            @RowsUpdated AS RowsUpdated,
            @RowsQuarantined AS RowsQuarantined;

    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;

        THROW;
    END CATCH;
END;
GO