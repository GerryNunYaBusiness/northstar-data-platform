from dataclasses import dataclass

from database import get_warehouse_connection


@dataclass
class SilverLoadResult:
    inserted: int
    updated: int


def load_silver_customers() -> SilverLoadResult:
    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("EXEC silver.usp_LoadCustomers;")

        row = cursor.fetchone()

        if row is None:
            raise RuntimeError(
                "Silver customer load returned no result."
            )

        return SilverLoadResult(
            inserted=row.RowsInserted,
            updated=row.RowsUpdated,
        )