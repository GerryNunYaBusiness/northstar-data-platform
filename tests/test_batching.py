from pathlib import Path
import sys
from unittest import result
from unittest.mock import MagicMock, patch
from uuid import uuid4

from datetime import datetime, timezone

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from database import get_warehouse_connection

from ingestion.customers import load_raw_customers, raw_customer_batch_exists,CustomerRecord
from customer_pipeline import run_customer_pipeline, load_bronze_for_batch

def test_raw_customer_batch_exists_returns_true():
    batch_id = uuid4()

    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = (1,)

    result = raw_customer_batch_exists(
        connection,
        batch_id,
    )

    assert result is True

    connection.execute.assert_called_once()

def test_raw_customer_batch_exists_returns_false():
    batch_id = uuid4()

    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = None

    result = raw_customer_batch_exists(
        connection,
        batch_id,
    )

    assert result is False

def test_raw_customer_batch_exists_queries_expected_batch():
    batch_id = uuid4()

    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = None

    raw_customer_batch_exists(
        connection,
        batch_id,
    )

    sql, parameter = connection.execute.call_args.args

    assert "BatchID" in sql
    assert parameter == str(batch_id)


@patch("customer_pipeline.load_raw_customers")
@patch("customer_pipeline.raw_customer_batch_exists")
def test_existing_batch_skips_bronze_load(
    mock_batch_exists,
    mock_load_raw,
):
    mock_batch_exists.return_value = True

    #batch_id = uuid4()
    #pipeline_run_id = uuid4()

    # Call your Bronze-stage function here.
    result = load_bronze_for_batch(
        customers=[],
        pipeline_run_id=uuid4(),
        batch_id=uuid4(),
    )

    assert result == 0
    mock_load_raw.assert_not_called()


@patch("customer_pipeline.load_raw_customers")
@patch("customer_pipeline.raw_customer_batch_exists")
def test_new_batch_loads_bronze(
    mock_batch_exists,
    mock_load_raw,
):
    mock_batch_exists.return_value = False
    mock_load_raw.return_value = 1

    customer = CustomerRecord(
        customer_id=1,
        first_name="Ada",
        last_name="Lovelace",
        email="ada@example.com",
        phone="555-0100",
        created_at=datetime(2026, 1, 1),
    )

    pipeline_run_id = uuid4()
    batch_id = uuid4()

    result = load_bronze_for_batch(
        customers=[customer],
        pipeline_run_id=pipeline_run_id,
        batch_id=batch_id,
    )
    
    assert result == 1

    mock_batch_exists.assert_called_once()
    
    mock_load_raw.assert_called_once_with(
        [customer],
        pipeline_run_id,
        batch_id,
    )

    #assert result == 6

def test_supplied_batch_id_is_reused():
    batch_id = uuid4()

    # Arrange mocks for extract/load/monitoring dependencies
    # so the pipeline doesn't touch SQL Server.

    result = run_customer_pipeline(
        batch_id=batch_id,
    )

    assert result.batch_id == batch_id
    assert result.pipeline_run_id != result.batch_id

def test_pipeline_generates_batch_id_when_not_supplied():
    result = run_customer_pipeline()

    assert result.batch_id is not None
    assert result.pipeline_run_id != result.batch_id
    
#@dataclass
#class TestCustomerRecord:
#    BatchID: UUID
#    PipelineRunID: UUID
#    CustomerID: int


#def get_test_customer(connection:pyodbc.Connection ) -> TestCustomerRecord:
    
#    cursor = connection.cursor()

#    row = cursor.execute("""
#        SELECT TOP (1) 
#        BatchID,
#        PipelineRunID,
#        CustomerID
#        FROM raw.Customers AS RC
#        """).fetchone()
#    if row is None:
#        raise ValueError("No records found in raw.customers")
    
#    return TestCustomerRecord(
#        BatchID=UUID(str(row.BatchID)),
#        PipelineRunID=UUID(str(row.PipelineRunID)),
#        CustomerID=int(row.CustomerID),
#    )