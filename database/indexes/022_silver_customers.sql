
IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('silver.Customers')
        AND name =            'IX_SilverCustomers_Email'
)
CREATE NONCLUSTERED INDEX [IX_SilverCustomers_Email] ON [silver].[Customers]
(
	[Email] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO