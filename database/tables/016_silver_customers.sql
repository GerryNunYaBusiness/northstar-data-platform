IF OBJECT_ID(
    'silver.Customers',
    'U'
) IS NULL
BEGIN
    CREATE TABLE [silver].[Customers](
	[CustomerID] [int] NOT NULL,
	[FirstName] [nvarchar](100) NOT NULL,
	[LastName] [nvarchar](100) NOT NULL,
	[Email] [nvarchar](255) NULL,
	[Phone] [nvarchar](50) NULL,
	[CreatedAt] [datetime2](7) NULL,
	[RecordHash] [varbinary](32) NOT NULL,
	[SourceIngestedAt] [datetime2](7) NOT NULL,
	[ProcessedAt] [datetime2](7) NOT NULL,
 CONSTRAINT [PK_SilverCustomers] PRIMARY KEY CLUSTERED 
(
	[CustomerID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
END;
GO