CREATE OR ALTER view [raw].[vw_LatestCustomers]
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
		RC.RecordHash,
        ROW_NUMBER() OVER
        (
            PARTITION BY RC.CustomerID
            ORDER BY RC.IngestedAt DESC
        ) AS RowNum
    FROM raw.Customers RC
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
	RecordHash
FROM RankedCustomers
WHERE RowNum = 1;
GO