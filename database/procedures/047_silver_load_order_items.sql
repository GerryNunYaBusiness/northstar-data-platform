CREATE OR ALTER PROCEDURE silver.usp_LoadOrderItems
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
            Determine all field and referential failures first,
            then create one quarantine record per OrderItem.
        */
        INSERT INTO ops.OrderItemQuarantine
        (
            PipelineRunID,
            BatchID,
            OrderItemID,
            OrderID,
            ProductID,
            Quantity,
            UnitPrice,
            FailureReason
        )
        SELECT
            @PipelineRunID,
            @BatchID,
            OI.OrderItemID,
            OI.OrderID,
            OI.ProductID,
            OI.Quantity,
            OI.UnitPrice,
            CONCAT(
                CASE
                    WHEN OI.OrderItemID <= 0
                    THEN 'OrderItemID must be greater than zero; '
                    ELSE ''
                END,
                CASE
                    WHEN OI.OrderID <= 0
                    THEN 'OrderID must be greater than zero; '
                    ELSE ''
                END,
                CASE
                    WHEN OI.ProductID <= 0
                    THEN 'ProductID must be greater than zero; '
                    ELSE ''
                END,
                CASE
                    WHEN OI.Quantity <= 0
                    THEN 'Quantity must be greater than zero; '
                    ELSE ''
                END,
                CASE
                    WHEN OI.UnitPrice <= 0
                    THEN 'UnitPrice must be greater than zero; '
                    ELSE ''
                END,

                /*
                    Only report a missing Order when OrderID itself
                    passed basic field validation.
                */
                CASE
                    WHEN OI.OrderID > 0
                         AND O.OrderID IS NULL
                    THEN 'OrderID does not exist in silver.Orders; '
                    ELSE ''
                END,

                /*
                    Same principle for ProductID.
                */
                CASE
                    WHEN OI.ProductID > 0
                         AND P.ProductID IS NULL
                    THEN 'ProductID does not exist in silver.Products; '
                    ELSE ''
                END
            )
        FROM raw.OrderItems AS OI
        LEFT JOIN silver.Orders AS O
            ON O.OrderID = OI.OrderID
        LEFT JOIN silver.Products AS P
            ON P.ProductID = OI.ProductID
        WHERE OI.BatchID = @BatchID
          AND
          (
              OI.OrderItemID <= 0
              OR OI.OrderID <= 0
              OR OI.ProductID <= 0
              OR OI.Quantity <= 0
              OR OI.UnitPrice <= 0

              OR
              (
                  OI.OrderID > 0
                  AND O.OrderID IS NULL
              )

              OR
              (
                  OI.ProductID > 0
                  AND P.ProductID IS NULL
              )
          )
          AND NOT EXISTS
          (
              SELECT 1
              FROM ops.OrderItemQuarantine AS Q
              WHERE Q.BatchID = @BatchID
                AND Q.OrderItemID = OI.OrderItemID
          );

        SET @RowsQuarantined = @@ROWCOUNT;

        /*
            Update existing trusted OrderItems only when all
            validation rules currently pass.
        */
        UPDATE S
        SET
            S.OrderID = OI.OrderID,
            S.ProductID = OI.ProductID,
            S.Quantity = OI.Quantity,
            S.UnitPrice = OI.UnitPrice,
            S.RecordHash = OI.RecordHash,
            S.SourceIngestedAt = OI.IngestedAt,
            S.ProcessedAt = SYSUTCDATETIME()
        FROM silver.OrderItems AS S
        INNER JOIN raw.OrderItems AS OI
            ON OI.OrderItemID = S.OrderItemID
        INNER JOIN silver.Orders AS O
            ON O.OrderID = OI.OrderID
        INNER JOIN silver.Products AS P
            ON P.ProductID = OI.ProductID
        WHERE OI.BatchID = @BatchID
          AND OI.OrderItemID > 0
          AND OI.OrderID > 0
          AND OI.ProductID > 0
          AND OI.Quantity > 0
          AND OI.UnitPrice > 0
          AND OI.RecordHash <> S.RecordHash;

        SET @RowsUpdated = @@ROWCOUNT;

        /*
            Insert new trusted OrderItems only when all field and
            referential validation succeeds.
        */
        INSERT INTO silver.OrderItems
        (
            OrderItemID,
            OrderID,
            ProductID,
            Quantity,
            UnitPrice,
            RecordHash,
            SourceIngestedAt
        )
        SELECT
            OI.OrderItemID,
            OI.OrderID,
            OI.ProductID,
            OI.Quantity,
            OI.UnitPrice,
            OI.RecordHash,
            OI.IngestedAt
        FROM raw.OrderItems AS OI
        INNER JOIN silver.Orders AS O
            ON O.OrderID = OI.OrderID
        INNER JOIN silver.Products AS P
            ON P.ProductID = OI.ProductID
        WHERE OI.BatchID = @BatchID
          AND OI.OrderItemID > 0
          AND OI.OrderID > 0
          AND OI.ProductID > 0
          AND OI.Quantity > 0
          AND OI.UnitPrice > 0
          AND NOT EXISTS
          (
              SELECT 1
              FROM silver.OrderItems AS S
              WHERE S.OrderItemID = OI.OrderItemID
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