from dataclasses import dataclass
from decimal import Decimal
import hashlib
from database import get_source_connection
from uuid import UUID
from database import (
    get_source_connection,
    get_warehouse_connection,
)

@dataclass(frozen=True)
class ProductRecord:
    product_id: int
    product_name: str
    category: str | None
    unit_cost: Decimal
    unit_price: Decimal


def calculate_product_hash(product: ProductRecord) -> bytes:
    hash_input = "|".join(
        [
            product.product_name,
            product.category or "",
            str(product.unit_cost),
            str(product.unit_price),
        ]
    )

    return hashlib.sha256(
        hash_input.encode("utf-8")
    ).digest()

def extract_products() -> list[ProductRecord]:
    with get_source_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                ProductID,
                ProductName,
                Category,
                UnitCost,
                UnitPrice
            FROM dbo.Products;
            """
        )

        return [
            ProductRecord(
                product_id=row.ProductID,
                product_name=row.ProductName,
                category=row.Category,
                unit_cost=row.UnitCost,
                unit_price=row.UnitPrice,
            )
            for row in cursor.fetchall()
        ]

def load_raw_products(
    products: list[ProductRecord],
    pipeline_run_id: UUID,
    batch_id: UUID,
) -> int:
    if not products:
        return 0

    stage_rows = [
        (
            str(pipeline_run_id),
            product.product_id,
            product.product_name,
            product.category,
            product.unit_cost,
            product.unit_price,
            calculate_product_hash(product),
        )
        for product in products
    ]

    with get_warehouse_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM raw.ProductBatchStage
            WHERE PipelineRunID = ?;
            """,
            str(pipeline_run_id),
        )

        cursor.fast_executemany = True

        cursor.executemany(
            """
            INSERT INTO raw.ProductBatchStage
            (
                PipelineRunID,
                ProductID,
                ProductName,
                Category,
                UnitCost,
                UnitPrice,
                RecordHash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?);
            """,
            stage_rows,
        )

        cursor.execute(
            """
            EXEC raw.usp_LoadProductsForBatch
                @BatchID = ?,
                @PipelineRunID = ?;
            """,
            str(batch_id),
            str(pipeline_run_id),
        )

        row = cursor.fetchone()

        rows_inserted = row.RowsInserted

        connection.commit()

        return rows_inserted