IF OBJECT_ID(
    'ops.PipelineBatches',
    'U'
) IS NULL
BEGIN
    CREATE TABLE [ops].[PipelineBatches](
	[BatchID] [uniqueidentifier] NOT NULL,
	[PipelineName] [nvarchar](200) NOT NULL,
	[StartedAt] [datetime2](3) NOT NULL,
	[CompletedAt] [datetime2](3) NULL,
	[Status] [nvarchar](20) NOT NULL,
	[RowsProcessed] [int] NULL,
	[ErrorMessage] [nvarchar](4000) NULL,
 CONSTRAINT [PK_PipelineBatches] PRIMARY KEY CLUSTERED 
(
	[BatchID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

ALTER TABLE [ops].[PipelineBatches]  WITH CHECK ADD  CONSTRAINT [CK_PipelineBatches_Status] CHECK  (([Status]='FAILED' OR [Status]='SUCCESS' OR [Status]='RUNNING'))

ALTER TABLE [ops].[PipelineBatches] CHECK CONSTRAINT [CK_PipelineBatches_Status]

END;