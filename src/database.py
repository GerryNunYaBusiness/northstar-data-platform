import os
import pyodbc


def _build_connection_string(database: str) -> str:
    server = os.getenv("NORTHSTAR_SQL_SERVER", "localhost")
    driver = os.getenv(
        "NORTHSTAR_SQL_DRIVER",
        "ODBC Driver 17 for SQL Server",
    )

    username = os.getenv("NORTHSTAR_SQL_USERNAME")
    password = os.getenv("NORTHSTAR_SQL_PASSWORD")

    if username and password:
        return (
            f"DRIVER={{{driver}}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            "TrustServerCertificate=yes;"
        )

    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


def get_source_connection() -> pyodbc.Connection:
    database = os.getenv(
        "NORTHSTAR_SOURCE_DATABASE",
        "NorthstarCommerce",
    )

    return pyodbc.connect(
        _build_connection_string(database)
    )


def get_warehouse_connection() -> pyodbc.Connection:
    database = os.getenv(
        "NORTHSTAR_WAREHOUSE_DATABASE",
        "NorthstarWarehouse",
    )

    return pyodbc.connect(
        _build_connection_string(database)
    )