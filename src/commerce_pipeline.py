from dataclasses import dataclass
# from multiprocessing import context
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CommerceStageResult:
    stage_name: str
    rows_inserted: int = 0
    rows_updated: int = 0
    rows_quarantined: int = 0


@dataclass(frozen=True)
class CommercePipelineResult:
    pipeline_run_id: UUID
    batch_id: UUID
    status: str
    stages: list[CommerceStageResult]

from pipeline_context import PipelineContext

from ingestion.customers import extract_customers, load_raw_customers
from ingestion.products import extract_products, load_raw_products
from ingestion.orders import extract_orders, load_raw_orders
from ingestion.order_items import extract_order_items, load_raw_order_items
from ingestion.payments import extract_payments, load_raw_payments

from transformation.customers import load_silver_customers, SilverLoadResult
from transformation.products import load_silver_products
from transformation.orders import load_silver_orders
from transformation.order_items import load_silver_order_items
from transformation.payments import load_silver_payments

from monitoring.pipeline_runs import start_pipeline_run, complete_pipeline_run
from monitoring.pipeline_batches import  begin_or_retry_batch, complete_batch
from monitoring.pipeline_runs import pipeline_stage


def run_commerce_pipeline(
    pipeline_run_id: UUID,
    batch_id: UUID,
) -> CommercePipelineResult:
    stages: list[CommerceStageResult] = []

    if batch_id is None:
        batch_id = uuid4()
    if pipeline_run_id is None:
        pipeline_run_id = uuid4()

    pipeline_name = "commerce"
    context = PipelineContext(
        pipeline_run_id=pipeline_run_id,
        batch_id=batch_id,
    )

    try:
        start_pipeline_run(
            pipeline_run_id,
            pipeline_name,
        )

        # begin_or_retry_batch(
        #     batch_id=batch_id,
        #     pipeline_name=pipeline_name,
        # )
        # ---------------------------------------------------------
        # Customers
        # ---------------------------------------------------------

        with pipeline_stage(
            pipeline_run_id,
            "customers_bronze",
        ):
            customers = extract_customers()

            customer_rows_inserted = load_raw_customers(
                customers,
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="customers_bronze",
                    rows_inserted=customer_rows_inserted,
                )
            )

        with pipeline_stage(
            pipeline_run_id,
            "customers_silver",
        ):
            customer_result = load_silver_customers(
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="customers_silver",
                    rows_inserted=customer_result.rows_inserted,
                    rows_updated=customer_result.rows_updated,
                    rows_quarantined=getattr(
                        customer_result,
                        "rows_quarantined",
                        0,
                    ),
                )
            )

        # ---------------------------------------------------------
        # Products
        # ---------------------------------------------------------
        with pipeline_stage(
            pipeline_run_id,
            "products_bronze",
        ):
            products = extract_products()

            product_rows_inserted = load_raw_products(
                products,
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="products_bronze",
                    rows_inserted=product_rows_inserted,
                )
            )

        with pipeline_stage(
            pipeline_run_id,
            "products_silver",
        ):
            product_result = load_silver_products(
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="products_silver",
                    rows_inserted=product_result.rows_inserted,
                    rows_updated=product_result.rows_updated,
                )
            )

        # ---------------------------------------------------------
        # Orders
        # ---------------------------------------------------------
        with pipeline_stage(
            pipeline_run_id,
            "orders_bronze",
        ):
            orders = extract_orders()

            order_rows_inserted = load_raw_orders(
                orders,
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="orders_bronze",
                    rows_inserted=order_rows_inserted,
                )
            )
        with pipeline_stage(
            pipeline_run_id,
            "orders_silver",
        ):
            order_result = load_silver_orders(
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="orders_silver",
                    rows_inserted=order_result.rows_inserted,
                    rows_updated=order_result.rows_updated,
                    rows_quarantined=order_result.rows_quarantined,
                )
            )

        # ---------------------------------------------------------
        # OrderItems
        # ---------------------------------------------------------
        with pipeline_stage(
            pipeline_run_id,
            "order_items_bronze",
        ):
            order_items = extract_order_items()

            order_item_rows_inserted = load_raw_order_items(
                order_items,
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="order_items_bronze",
                    rows_inserted=order_item_rows_inserted,
                )
            )

        with pipeline_stage(
            pipeline_run_id,
            "order_items_silver",
        ):
            order_item_result = load_silver_order_items(
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="order_items_silver",
                    rows_inserted=order_item_result.rows_inserted,
                    rows_updated=order_item_result.rows_updated,
                    rows_quarantined=order_item_result.rows_quarantined,
                )
            )

        # ---------------------------------------------------------
        # Payments
        # ---------------------------------------------------------
        with pipeline_stage(
            pipeline_run_id,
            "payments_bronze",
        ):
            payments = extract_payments()

            payment_rows_inserted = load_raw_payments(
                payments,
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="payments_bronze",
                    rows_inserted=payment_rows_inserted,
                )
            )

        with pipeline_stage(
            pipeline_run_id,
            "payments_silver",
        ):
            payment_result = load_silver_payments(
                pipeline_run_id,
                batch_id,
            )

            stages.append(
                CommerceStageResult(
                    stage_name="payments_silver",
                    rows_inserted=payment_result.rows_inserted,
                    rows_updated=payment_result.rows_updated,
                    rows_quarantined=payment_result.rows_quarantined,
                )
            )

        complete_pipeline_run(
            pipeline_run_id = pipeline_run_id,
            status = "SUCCESS",
        )

        return CommercePipelineResult(
            pipeline_run_id=pipeline_run_id,
            batch_id=batch_id,
            status="SUCCESS",
            stages=stages,
        )
    
    except Exception as exc:
        # fail_pipeline_run(
        #     pipeline_run_id,
        # )
        complete_pipeline_run(
            pipeline_run_id,
            "FAILED",
            error_message=str(exc),
        )

        raise