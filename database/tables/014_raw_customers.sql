IF OBJECT_ID(
    'raw.Customers',
    'U'
) IS NULL
BEGIN
    CREATE TABLE [raw].[Customers](
	[CustomerID] [int] NOT NULL,
	[FirstName] [nvarchar](100) NULL,
	[LastName] [nvarchar](100) NULL,
	[Email] [nvarchar](255) NULL,
	[Phone] [nvarchar](50) NULL,
	[CreatedAt] [datetime2](7) NULL,
	[IngestedAt] [datetime2](7) NOT NULL,
	[PipelineRunID] [uniqueidentifier] NOT NULL,
	[RecordHash] [varbinary](32) NULL,
	[BatchID] [uniqueidentifier] NOT NULL
) ON [PRIMARY]
END;
GO

