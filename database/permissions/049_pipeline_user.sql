IF USER_ID('northstar_pipeline') IS NULL
BEGIN
    CREATE USER northstar_pipeline
        FOR LOGIN northstar_pipeline;
END;
GO