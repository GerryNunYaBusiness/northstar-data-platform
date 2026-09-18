IF OBJECT_ID(
    'ops.SchemaMigrations',
    'U'
) IS NULL
BEGIN
    CREATE TABLE ops.SchemaMigrations
    (
        MigrationID NVARCHAR(200) NOT NULL
            CONSTRAINT PK_SchemaMigrations
            PRIMARY KEY,

        AppliedAt DATETIME2(3) NOT NULL
            CONSTRAINT DF_SchemaMigrations_AppliedAt
            DEFAULT SYSUTCDATETIME()
    );
END;
GO