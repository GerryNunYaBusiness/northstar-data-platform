import time

from database import get_warehouse_connection


def benchmark() -> None:
    start = time.perf_counter()

    lookups = 0

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute("""
            SELECT
                RC.CustomerID,
                RC.RecordHash
            FROM raw.vw_LatestCustomers RC
            WHERE
                RC.RecordHash IS NOT NULL
                AND RC.Email LIKE '%@northstar.test';
        """)

        customers = cursor.fetchall()

        for customer in customers:
            cursor.execute(
                """
                SELECT
                    SC.RecordHash
                FROM silver.Customers SC
                WHERE SC.CustomerID = ?;
                """,
                customer.CustomerID,
            )

            cursor.fetchone()
            lookups += 1

    elapsed = time.perf_counter() - start

    print(f"Customers checked : {len(customers)}")
    print(f"SQL lookups       : {lookups}")
    print(f"Elapsed seconds   : {elapsed:.3f}")


if __name__ == "__main__":
    benchmark()