CREATE OR ALTER VIEW raw.vw_LatestCustomers
AS
WITH RankedCustomers AS
(
    SELECT
        RC.CustomerID,
        RC.FirstName,
        RC.LastName,
        RC.Email,
        RC.Phone,
        RC.CreatedAt,
        RC.IngestedAt,
        RC.PipelineRunID,
        RC.BatchID,
        RC.RecordHash,
        ROW_NUMBER() OVER
        (
            PARTITION BY RC.CustomerID
            ORDER BY
                RC.IngestedAt DESC,
                RC.BatchID DESC
        ) AS RowNum
    FROM raw.Customers AS RC
)
SELECT
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
FROM RankedCustomers
WHERE RowNum = 1;
GO