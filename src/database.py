import os
import time

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
            "Encrypt=yes;"
            "TrustServerCertificate=yes;"
        )

    return (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
        "TrustServerCertificate=yes;"
    )


def _connect_with_retry(
    connection_string: str,
    max_attempts: int = 3,
    delay_seconds: float = 2.0,
) -> pyodbc.Connection:
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            return pyodbc.connect(
                connection_string,
                timeout=5,
            )
        except pyodbc.OperationalError as exc:
            last_error = exc

            if attempt == max_attempts:
                break

            print(
                f"Database connection failed "
                f"(attempt {attempt}/{max_attempts}). "
                f"Retrying in {delay_seconds} seconds..."
            )

            time.sleep(delay_seconds)

    raise last_error


def get_source_connection() -> pyodbc.Connection:
    database = os.getenv(
        "NORTHSTAR_SOURCE_DATABASE",
        "NorthstarCommerce",
    )

    return _connect_with_retry(
        _build_connection_string(database)
    )


def get_warehouse_connection() -> pyodbc.Connection:
    database = os.getenv(
        "NORTHSTAR_WAREHOUSE_DATABASE",
        "NorthstarWarehouse",
    )

    return _connect_with_retry(
        _build_connection_string(database)
    )