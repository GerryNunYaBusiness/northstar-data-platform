IF NOT EXISTS
(    SELECT 1     FROM sys.schemas    WHERE name = 'raw')
BEGIN
    EXEC('CREATE SCHEMA raw');
END;
GO

IF NOT EXISTS
(    SELECT 1    FROM sys.schemas    WHERE name = 'silver')
BEGIN
    EXEC('CREATE SCHEMA silver');
END;
GO

IF NOT EXISTS
(    SELECT 1    FROM sys.schemas    WHERE name = 'ops')
BEGIN
    EXEC('CREATE SCHEMA ops');
END;
GO