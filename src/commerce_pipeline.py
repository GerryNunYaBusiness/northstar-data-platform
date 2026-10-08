from dataclasses import dataclass
# from multiprocessing import context
from uuid import UUID, uuid4

# from pipeline_context import PipelineContext

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
# from monitoring.pipeline_runs import pipeline_stage

from pipeline_framework.context import PipelineContext
from pipeline_framework.results import StageResult
# from pipeline_framework.stages import execute_bronze_stage, execute_silver_stage
from pipeline_framework.entity import EntityPipeline, execute_entity_pipeline

# @dataclass(frozen=True)
# class CommerceStageResult:
#     stage_name: str
#     rows_inserted: int = 0
#     rows_updated: int = 0
#     rows_quarantined: int = 0

@dataclass(frozen=True)
class CommercePipelineResult:
    pipeline_run_id: UUID
    batch_id: UUID
    status: str
    stages: list[StageResult]

CUSTOMERS_PIPELINE = EntityPipeline(
    name="customers",
    extractor=extract_customers,
    bronze_loader=load_raw_customers,
    silver_loader=load_silver_customers,
)

PRODUCTS_PIPELINE = EntityPipeline(
    name="products",
    extractor=extract_products,
    bronze_loader=load_raw_products,
    silver_loader=load_silver_products,
)

ORDERS_PIPELINE = EntityPipeline(
    name="orders",
    extractor=extract_orders,
    bronze_loader=load_raw_orders,
    silver_loader=load_silver_orders,
)

ORDER_ITEMS_PIPELINE = EntityPipeline(
    name="order_items",
    extractor=extract_order_items,
    bronze_loader=load_raw_order_items,
    silver_loader=load_silver_order_items,
)

PAYMENTS_PIPELINE = EntityPipeline(
    name="payments",
    extractor=extract_payments,
    bronze_loader=load_raw_payments,
    silver_loader=load_silver_payments,
)

COMMERCE_PIPELINES = [
    CUSTOMERS_PIPELINE,
    PRODUCTS_PIPELINE,
    ORDERS_PIPELINE,
    ORDER_ITEMS_PIPELINE,
    PAYMENTS_PIPELINE,
]


def run_commerce_pipeline(
    pipeline_run_id: UUID,
    batch_id: UUID,
) -> CommercePipelineResult:
    stages: list[StageResult] = []

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

        for entity in COMMERCE_PIPELINES:
            stages.extend(
                execute_entity_pipeline(
                    entity=entity,
                    context=context,
                )
            )

        #---------------------------------------------------------
        # Process Completion
        #---------------------------------------------------------

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