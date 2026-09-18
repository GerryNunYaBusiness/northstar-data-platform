IF OBJECT_ID(
    'raw.CustomerBatchStage',
    'U'
) IS NULL
BEGIN
    CREATE TABLE [raw].[CustomerBatchStage](
	[CustomerID] [int] NOT NULL,
	[FirstName] [nvarchar](100) NULL,
	[LastName] [nvarchar](100) NULL,
	[Email] [nvarchar](320) NULL,
	[Phone] [nvarchar](50) NULL,
	[CreatedAt] [datetime2](3) NULL,
	[RecordHash] [varbinary](32) NOT NULL,
	[PipelineRunID] [uniqueidentifier] NOT NULL
) ON [PRIMARY]
END;
GO