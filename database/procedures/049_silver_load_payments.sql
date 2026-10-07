CREATE OR ALTER PROCEDURE silver.usp_LoadPayments
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

        /*
            Create one quarantine record containing all failures
            detected for this Payment.
        */
        INSERT INTO ops.PaymentQuarantine
        (
            PipelineRunID,
            BatchID,
            PaymentID,
            OrderID,
            PaymentDate,
            PaymentMethod,
            Amount,
            [Status],
            FailureReason
        )
        SELECT
            @PipelineRunID,
            @BatchID,
            P.PaymentID,
            P.OrderID,
            P.PaymentDate,
            P.PaymentMethod,
            P.Amount,
            P.[Status],

            CONCAT(
                CASE
                    WHEN P.PaymentID <= 0
                    THEN 'PaymentID must be greater than zero; '
                    ELSE ''
                END,

                CASE
                    WHEN P.OrderID <= 0
                    THEN 'OrderID must be greater than zero; '
                    ELSE ''
                END,

                CASE
                    WHEN P.PaymentMethod NOT IN
                    (
                        'CreditCard',
                        'DebitCard',
                        'PayPal',
                        'BankTransfer'
                    )
                    THEN 'Invalid payment method; '
                    ELSE ''
                END,

                CASE
                    WHEN P.Amount <= 0
                    THEN 'Amount must be greater than zero; '
                    ELSE ''
                END,

                CASE
                    WHEN P.[Status] NOT IN
                    (
                        'Pending',
                        'Completed',
                        'Failed',
                        'Refunded'
                    )
                    THEN 'Invalid payment status; '
                    ELSE ''
                END,

                CASE
                    WHEN P.OrderID > 0
                        AND P.PaymentID > 0
                        AND P.PaymentMethod IN
                        (
                            'CreditCard',
                            'DebitCard',
                            'PayPal',
                            'BankTransfer'
                        )
                        AND P.Amount > 0
                        AND P.[Status] IN
                        (
                            'Pending',
                            'Completed',
                            'Failed',
                            'Refunded'
                        )
                        AND O.OrderID IS NULL
                    THEN 'OrderID does not exist in silver.Orders; '
                    ELSE ''
                END
            )
        FROM raw.Payments AS P
        LEFT JOIN silver.Orders AS O
            ON O.OrderID = P.OrderID
        WHERE P.BatchID = @BatchID
          AND
          (
              P.PaymentID <= 0
              OR P.OrderID <= 0

              OR P.PaymentMethod NOT IN
              (
                  'CreditCard',
                  'DebitCard',
                  'PayPal',
                  'BankTransfer'
              )

              OR P.Amount <= 0

              OR P.[Status] NOT IN
              (
                  'Pending',
                  'Completed',
                  'Failed',
                  'Refunded'
              )

              OR
              (
                P.PaymentID > 0
                AND P.OrderID > 0
                AND P.PaymentMethod IN
                (
                    'CreditCard',
                    'DebitCard',
                    'PayPal',
                    'BankTransfer'
                )
                AND P.Amount > 0
                AND P.[Status] IN
                (
                    'Pending',
                    'Completed',
                    'Failed',
                    'Refunded'
                )
                AND O.OrderID IS NULL
              )
          )
          AND NOT EXISTS
          (
              SELECT 1
              FROM ops.PaymentQuarantine AS Q
              WHERE Q.BatchID = @BatchID
                AND Q.PaymentID = P.PaymentID
          );

        SET @RowsQuarantined = @@ROWCOUNT;

        /*
            Update existing Silver Payments only when the current
            Bronze state is valid and its business state changed.
        */
        UPDATE S
        SET
            S.OrderID = P.OrderID,
            S.PaymentDate = P.PaymentDate,
            S.PaymentMethod = P.PaymentMethod,
            S.Amount = P.Amount,
            S.[Status] = P.[Status],
            S.RecordHash = P.RecordHash,
            S.SourceIngestedAt = P.IngestedAt,
            S.ProcessedAt = SYSUTCDATETIME()
        FROM silver.Payments AS S
        INNER JOIN raw.Payments AS P
            ON P.PaymentID = S.PaymentID
        INNER JOIN silver.Orders AS O
            ON O.OrderID = P.OrderID
        WHERE P.BatchID = @BatchID
          AND P.PaymentID > 0
          AND P.OrderID > 0
          AND P.PaymentMethod IN
          (
              'CreditCard',
              'DebitCard',
              'PayPal',
              'BankTransfer'
          )
          AND P.Amount > 0
          AND P.[Status] IN
          (
              'Pending',
              'Completed',
              'Failed',
              'Refunded'
          )
          AND P.RecordHash <> S.RecordHash;

        SET @RowsUpdated = @@ROWCOUNT;

        /*
            Insert new valid Payments whose Order dependency exists.
        */
        INSERT INTO silver.Payments
        (
            PaymentID,
            OrderID,
            PaymentDate,
            PaymentMethod,
            Amount,
            [Status],
            RecordHash,
            SourceIngestedAt
        )
        SELECT
            P.PaymentID,
            P.OrderID,
            P.PaymentDate,
            P.PaymentMethod,
            P.Amount,
            P.[Status],
            P.RecordHash,
            P.IngestedAt
        FROM raw.Payments AS P
        INNER JOIN silver.Orders AS O
            ON O.OrderID = P.OrderID
        WHERE P.BatchID = @BatchID
          AND P.PaymentID > 0
          AND P.OrderID > 0
          AND P.PaymentMethod IN
          (
              'CreditCard',
              'DebitCard',
              'PayPal',
              'BankTransfer'
          )
          AND P.Amount > 0
          AND P.[Status] IN
          (
              'Pending',
              'Completed',
              'Failed',
              'Refunded'
          )
          AND NOT EXISTS
          (
              SELECT 1
              FROM silver.Payments AS S
              WHERE S.PaymentID = P.PaymentID
          );

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