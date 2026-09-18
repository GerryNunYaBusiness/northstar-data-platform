IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.Customers')
        AND name =            'IX_RawCustomers_Customer_Ingested'
)
CREATE NONCLUSTERED INDEX [IX_RawCustomers_Customer_Ingested] ON [raw].[Customers]
(
	[CustomerID] ASC,
	[IngestedAt] DESC
)
INCLUDE([FirstName],[LastName],[Email],[Phone],[CreatedAt],[PipelineRunID],[RecordHash]) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.Customers')
        AND name =            'UX_RawCustomers_Batch_Customer'
)
CREATE UNIQUE NONCLUSTERED INDEX [UX_RawCustomers_Batch_Customer] ON [raw].[Customers]
(
	[BatchID] ASC,
	[CustomerID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, IGNORE_DUP_KEY = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO

GO