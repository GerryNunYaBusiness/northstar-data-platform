IF OBJECT_ID(
    'ops.PipelineStageRuns',
    'U'
) IS NULL
BEGIN
    CREATE TABLE ops.[PipelineStageRuns](
	[PipelineStageRunID] [bigint] IDENTITY(1,1) NOT NULL,
	[PipelineRunID] [uniqueidentifier] NOT NULL,
	[StageName] [nvarchar](200) NOT NULL,
	[StartedAt] [datetime2](7) NOT NULL,
	[CompletedAt] [datetime2](7) NULL,
	[Status] [nvarchar](20) NOT NULL,
	[RowsProcessed] [int] NULL,
	[ErrorMessage] [nvarchar](4000) NULL,
 CONSTRAINT [PK_PipelineStageRuns] PRIMARY KEY CLUSTERED 
(
	[PipelineStageRunID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]

ALTER TABLE [ops].[PipelineStageRuns]  WITH CHECK ADD  CONSTRAINT [FK_PipelineStageRuns_PipelineRun] FOREIGN KEY([PipelineRunID])
REFERENCES [ops].[PipelineRuns] ([PipelineRunID])

ALTER TABLE [ops].[PipelineStageRuns] CHECK CONSTRAINT [FK_PipelineStageRuns_PipelineRun]

END;