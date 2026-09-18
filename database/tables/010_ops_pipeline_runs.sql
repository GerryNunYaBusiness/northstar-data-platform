IF OBJECT_ID(
    'ops.PipelineRuns',
    'U'
) IS NULL
BEGIN
    CREATE TABLE [ops].[PipelineRuns](
        [PipelineRunID] [uniqueidentifier] NOT NULL,
        [PipelineName] [nvarchar](200) NOT NULL,
        [StartedAt] [datetime2](7) NOT NULL,
        [CompletedAt] [datetime2](7) NULL,
        [Status] [nvarchar](20) NOT NULL,
        [ErrorMessage] [nvarchar](4000) NULL,
    CONSTRAINT [PK_PipelineRuns] PRIMARY KEY CLUSTERED 
    (
        [PipelineRunID] ASC
    )WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
    ) ON [PRIMARY]
END;
GO
-- ALTER TABLE [ops].[PipelineStageRuns]  WITH CHECK ADD  CONSTRAINT [FK_PipelineStageRuns_PipelineRun] FOREIGN KEY([PipelineRunID])
-- REFERENCES [ops].[PipelineRuns] ([PipelineRunID])
-- GO