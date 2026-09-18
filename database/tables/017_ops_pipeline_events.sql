IF OBJECT_ID(
    'ops.PipelineEvents',
    'U'
) IS NULL
BEGIN
    CREATE TABLE ops.PipelineEvents
    (
        PipelineEventID BIGINT IDENTITY(1,1)
            NOT NULL
            CONSTRAINT PK_PipelineEvents
            PRIMARY KEY,

        PipelineRunID UNIQUEIDENTIFIER NULL,
        BatchID UNIQUEIDENTIFIER NULL,

        PipelineName NVARCHAR(200) NOT NULL,
        StageName NVARCHAR(200) NULL,

        EventType NVARCHAR(50) NOT NULL,

        EventTime DATETIME2(3) NOT NULL
            CONSTRAINT DF_PipelineEvents_EventTime
            DEFAULT SYSUTCDATETIME(),

        DagRunID NVARCHAR(500) NULL,
        TryNumber INT NULL,
        ErrorType NVARCHAR(200) NULL,
        EventMessage NVARCHAR(4000) NULL,

        CONSTRAINT CK_PipelineEvents_EventType
        CHECK
        (
            EventType IN
            (
                'RETRY',
                'RECOVERED'
            )
        )
    );
END;
GO