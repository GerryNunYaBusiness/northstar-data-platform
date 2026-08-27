import pyodbc

connection_string = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=localhost;"
    "DATABASE=NorthstarWarehouse;"
    "Trusted_Connection=yes;"
)

try:
    with pyodbc.connect(connection_string) as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT TOP (5)
                PRL.PipelineRunID,
                PRL.PipelineName,
                PRL.[Status],
                PRL.RowsInserted,
                PRL.RowsUpdated
            FROM dbo.PipelineRunLog PRL
            ORDER BY PRL.PipelineRunID DESC;
        """)

        for row in cursor.fetchall():
            print(row)

except pyodbc.Error as exc:
    print("Database connection failed.")
    print(exc)
    raise