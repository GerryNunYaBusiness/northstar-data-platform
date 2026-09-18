IF OBJECT_ID(
    'ops.CustomerQuarantine',
    'U'
) IS NULL
BEGIN
    CREATE TABLE ops.[CustomerQuarantine](
	[QuarantineID] [bigint] IDENTITY(1,1) NOT NULL,
	[PipelineRunID] [uniqueidentifier] NOT NULL,
	[CustomerID] [int] NULL,
	[FirstName] [nvarchar](100) NULL,
	[LastName] [nvarchar](100) NULL,
	[Email] [nvarchar](255) NULL,
	[Phone] [nvarchar](50) NULL,
	[CreatedAt] [datetime2](7) NULL,
	[ValidationRule] [nvarchar](200) NOT NULL,
	[ValidationMessage] [nvarchar](1000) NOT NULL,
	[QuarantinedAt] [datetime2](7) NOT NULL,
	[ResolvedAt] [datetime2](7) NULL,
 CONSTRAINT [PK_CustomerQuarantine] PRIMARY KEY CLUSTERED 
(
	[QuarantineID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]


ALTER TABLE [ops].[CustomerQuarantine] ADD  CONSTRAINT [DF_CustomerQuarantine_QuarantinedAt]  DEFAULT (sysutcdatetime()) FOR [QuarantinedAt]
END;