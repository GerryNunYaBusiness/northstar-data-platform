from unittest.mock import patch
from uuid import uuid4
from pathlib import Path
import sys
from contextlib import nullcontext

import pytest

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
    
from commerce_pipeline import run_commerce_pipeline
from pipeline_framework.results import StageResult

# @patch("commerce_pipeline.complete_pipeline_run")
# @patch("commerce_pipeline.start_pipeline_run")
def test_commerce_pipeline_runs_entities_in_dependency_order(
    # mock_start_pipeline_run,
    # mock_complete_pipeline_run,
):
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    call_order = []

    def execute_entity_side_effect(entity, context):
        call_order.append(entity.name)

        return [
            StageResult(
                stage_name=f"{entity.name}_bronze",
            ),
            StageResult(
                stage_name=f"{entity.name}_silver",
            ),
        ]

    with (
        patch("commerce_pipeline.start_pipeline_run"        ),
        patch("commerce_pipeline.complete_pipeline_run"        ),
        patch("commerce_pipeline.execute_entity_pipeline", side_effect=execute_entity_side_effect,        ),
    ):
        result = run_commerce_pipeline(
            pipeline_run_id=pipeline_run_id,
            batch_id=batch_id,
        )

    assert call_order == [
        "customers",
        "products",
        "orders",
        "order_items",
        "payments",
    ]

    assert result.status == "SUCCESS"


def test_commerce_pipeline_stops_after_failed_dependency():
    pipeline_run_id = uuid4()
    batch_id = uuid4()

    call_order = []

    def execute_entity_side_effect(entity, context):
        call_order.append(entity.name)

        if entity.name == "orders":
            raise RuntimeError("Orders pipeline failed")

        return [
            StageResult(stage_name=f"{entity.name}_bronze",            ),
            StageResult(stage_name=f"{entity.name}_silver",            ),
        ]

    with (
        patch("commerce_pipeline.start_pipeline_run"        ) as mock_start_pipeline_run, 
        patch("commerce_pipeline.complete_pipeline_run"        ) as mock_complete_pipeline_run,
        patch("commerce_pipeline.execute_entity_pipeline", side_effect=execute_entity_side_effect,        ),
    ):
        with pytest.raises(RuntimeError, match="Orders pipeline failed",    ):
            run_commerce_pipeline(
                pipeline_run_id=pipeline_run_id,
                batch_id=batch_id,
            )

    assert call_order == [
        "customers",
        "products",
        "orders",
    ]

    mock_start_pipeline_run.assert_called_once()

    mock_complete_pipeline_run.assert_called_once_with(
        pipeline_run_id,
        "FAILED",
        error_message="Orders pipeline failed",
    )


'''Pre-Entity refactor Pipeline Tests'''
# # @patch("commerce_pipeline.fail_pipeline_run")
# @patch("commerce_pipeline.complete_pipeline_run")
# @patch("commerce_pipeline.start_pipeline_run")
# # @patch("commerce_pipeline.pipeline_stage", side_effect=lambda *args, **kwargs: nullcontext(),)
# @patch("pipeline_framework.stages.pipeline_stage", side_effect=lambda *args, **kwargs: nullcontext(),)
# def test_commerce_pipeline_runs_entities_in_dependency_order(
#     # mock_framework_pipeline_stage,
#     mock_pipeline_stage,
#     mock_start_pipeline_run,
#     mock_complete_pipeline_run,
#     # mock_fail_pipeline_run,
# ):
#     pipeline_run_id = uuid4()
#     batch_id = uuid4()

#     call_order = []

#     def record_call(name, result=None):
#         def inner(*args, **kwargs):
#             call_order.append(name)
#             return result

#         return inner

#     class SilverResult:
#         rows_inserted = 1
#         rows_updated = 0
#         rows_quarantined = 0

#     silver_result = SilverResult()

#     with (
#         patch("commerce_pipeline.extract_customers",        side_effect=record_call("extract_customers",[],),        ),
#         patch("commerce_pipeline.load_raw_customers",       side_effect=record_call("customers_bronze",1,),        ),
#         patch("commerce_pipeline.load_silver_customers",    side_effect=record_call("customers_silver",silver_result,),        ),
#         patch("commerce_pipeline.extract_products",         side_effect=record_call("extract_products",[],),        ),
#         patch("commerce_pipeline.load_raw_products",        side_effect=record_call("products_bronze",1,),        ),
#         patch("commerce_pipeline.load_silver_products",     side_effect=record_call("products_silver",silver_result,),        ),
#         patch("commerce_pipeline.extract_orders",           side_effect=record_call("extract_orders",[],),        ),
#         patch("commerce_pipeline.load_raw_orders",          side_effect=record_call("orders_bronze",1,),        ),
#         patch("commerce_pipeline.load_silver_orders",       side_effect=record_call("orders_silver",silver_result,),        ),
#         patch("commerce_pipeline.extract_order_items",      side_effect=record_call("extract_order_items",[],),        ),
#         patch("commerce_pipeline.load_raw_order_items",     side_effect=record_call("order_items_bronze",1,),        ),
#         patch("commerce_pipeline.load_silver_order_items",  side_effect=record_call("order_items_silver",silver_result,),        ),
#         patch("commerce_pipeline.extract_payments",         side_effect=record_call("extract_payments",[],),        ),
#         patch("commerce_pipeline.load_raw_payments",        side_effect=record_call("payments_bronze",1,),        ),
#         patch("commerce_pipeline.load_silver_payments",     side_effect=record_call("payments_silver",silver_result,),        ),
#     ):
#         result = run_commerce_pipeline(
#             pipeline_run_id,
#             batch_id,
#         )

#     assert result.status == "SUCCESS"

#     assert call_order == [
#         "extract_customers",    "customers_bronze",     "customers_silver",
#         "extract_products",     "products_bronze",      "products_silver",
#         "extract_orders",       "orders_bronze",        "orders_silver",
#         "extract_order_items",  "order_items_bronze",   "order_items_silver",
#         "extract_payments",     "payments_bronze",      "payments_silver",
#     ]

#     mock_start_pipeline_run.assert_called_once()
#     mock_complete_pipeline_run.assert_called_once()
#     mock_complete_pipeline_run.assert_called_once_with(
#         pipeline_run_id=pipeline_run_id,
#         status="SUCCESS",
#     )
#     # mock_fail_pipeline_run.assert_not_called()

'''Pre-Entity refactor Pipeline Tests'''
# # @patch("commerce_pipeline.fail_pipeline_run")
# @patch("commerce_pipeline.complete_pipeline_run")
# @patch("commerce_pipeline.start_pipeline_run")
# # @patch("commerce_pipeline.pipeline_stage", side_effect=lambda *args, **kwargs: nullcontext(),)
# @patch("pipeline_framework.stages.pipeline_stage", side_effect=lambda *args, **kwargs: nullcontext(),)
# def test_commerce_pipeline_stops_after_failed_dependency(
#     # mock_framework_pipeline_stage,
#     mock_pipeline_stage,
#     mock_start_pipeline_run,
#     mock_complete_pipeline_run,
#     # mock_fail_pipeline_run,
# ):
#     pipeline_run_id = uuid4()
#     batch_id = uuid4()

#     class SilverResult:
#         rows_inserted = 1
#         rows_updated = 0
#         rows_quarantined = 0

#     silver_result = SilverResult()

#     with (
#         patch("commerce_pipeline.extract_customers",return_value=[],        ),
#         patch("commerce_pipeline.load_raw_customers",return_value=1,        ),
#         patch("commerce_pipeline.load_silver_customers",return_value=silver_result,        ),
#         patch("commerce_pipeline.extract_products",return_value=[],        ),
#         patch("commerce_pipeline.load_raw_products",return_value=1,        ),
#         patch("commerce_pipeline.load_silver_products",return_value=silver_result,        ),
#         patch("commerce_pipeline.extract_orders",return_value=[],        ),
#         patch("commerce_pipeline.load_raw_orders",return_value=1,        ),
#         patch("commerce_pipeline.load_silver_orders",side_effect=RuntimeError("Orders Silver failed"),        ),
#         patch("commerce_pipeline.extract_order_items",) as extract_order_items,
#         patch("commerce_pipeline.extract_payments",) as extract_payments,
#     ):
#         try:
#             run_commerce_pipeline(
#                 pipeline_run_id,
#                 batch_id,
#             )

#             assert False, "Expected pipeline failure"

#         except RuntimeError as error:
#             assert str(error) == "Orders Silver failed"

#     extract_order_items.assert_not_called()
#     extract_payments.assert_not_called()
#     mock_start_pipeline_run.assert_called_once()
#     mock_complete_pipeline_run.assert_called_once_with(
#         pipeline_run_id,
#         "FAILED",
#         error_message="Orders Silver failed",
#     )
#     # mock_fail_pipeline_run.assert_called_once()