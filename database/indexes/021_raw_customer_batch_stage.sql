
IF NOT EXISTS
(    SELECT 1    FROM sys.indexes
    WHERE        object_id =            OBJECT_ID('raw.CustomerBatchStage')
        AND name =            'IX_CustomerBatchStage_PipelineRun'
)
CREATE NONCLUSTERED INDEX [IX_CustomerBatchStage_PipelineRun] ON [raw].[CustomerBatchStage]
(
	[PipelineRunID] ASC,
	[CustomerID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, SORT_IN_TEMPDB = OFF, DROP_EXISTING = OFF, ONLINE = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
GO