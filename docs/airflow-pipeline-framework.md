## Airflow Orchestration

Northstar Data Platform maintains two Airflow DAGs:

| DAG | Purpose |
|---|---|
| `northstar_customer_pipeline` | Original Customer-only pipeline with separate Airflow tasks for preparation, Bronze, Silver, and completion. |
| `northstar_commerce_pipeline` | Five-entity Commerce pipeline that delegates execution to the reusable Python pipeline framework. |

The Commerce DAG uses a single `execute_commerce` task to invoke `run_commerce_pipeline()`.

The Commerce DAG is initially configured with `schedule=None` so that it can be validated through manual runs before automated scheduling is enabled.

### Separation of Responsibilities

**Airflow is responsible for:**

- Scheduling and triggering DAG runs.
- Managing task attempts and retries.
- Applying exception-aware retry policies.
- Invoking task-level monitoring callbacks.
- Displaying execution history in the Airflow UI.

**The Commerce orchestrator is responsible for:**

- Starting and completing pipeline execution records.
- Beginning or retrying logical batches.
- Executing entities in dependency order.
- Recording batch completion or failure.
- Propagating exceptions to Airflow.

**The reusable framework is responsible for:**

- Executing entity Bronze and Silver stages.
- Invoking optional record processors.
- Recording stage-level monitoring information.
- Returning standardized stage results.

This separation prevents duplicate lifecycle operations between Airflow and the Python orchestrator.

## Commerce Execution Order

The Commerce pipeline executes five entities in the following dependency order:

1. Customers
2. Products
3. Orders
4. OrderItems
5. Payments

Each entity executes Bronze processing before Silver processing.

The Commerce orchestrator stops processing downstream entities if an earlier entity fails.

The entity dependency order is explicitly defined by `COMMERCE_PIPELINES` in `src/commerce_pipeline.py`.

The framework does not implement a general-purpose dependency scheduler or replace Airflow.

## Customer Record Processing and Data Quality

The reusable framework supports an optional entity-specific record processor between extraction and Bronze loading.

The execution flow is:

```text
Extract records
    |
    v
Optional record processor
    |
    v
Load records into Bronze
    |
    v
Execute Silver transformation
```

The Customer pipeline configures `process_customer_records()` as its record processor.

The processor:

- Validates duplicate CustomerIDs.
- Requires nonempty first and last names.
- Checks email addresses for the expected basic format.
- Writes validation errors to `ops.CustomerQuarantine`.
- Calculates the invalid-customer rate.
- Enforces `NORTHSTAR_CUSTOMER_INVALID_RATE_THRESHOLD`.
- Returns only valid Customer records for Bronze loading.

Customer quarantine records are stored per validation error, so a Customer with multiple validation failures may produce multiple quarantine rows.

If the invalid-customer rate exceeds the configured threshold, the processor raises `DataQualityError`. The Bronze loader is not called, and the Commerce execution fails.

The quarantine operation commits its records before threshold enforcement, preserving the errors for investigation.

Orders, OrderItems, and Payments retain entity-specific SQL validation and quarantine logic in their Silver transformations.

The framework does not contain entity-specific validation rules.

## Batch Identity and Execution Attempts

The platform distinguishes between a logical source batch and an individual execution attempt.

| Identifier | Meaning |
|---|---|
| `BatchID` | Identifies a logical source batch. |
| `PipelineRunID` | Identifies a single pipeline execution attempt. |
| `PipelineStageRunID` | Identifies an individual recorded stage execution. |

A failed batch can be retried using its original BatchID and a new PipelineRunID.

For Airflow-triggered Commerce executions, the DAG derives BatchID deterministically from the Airflow DAG run identifier:

```python
batch_id = uuid5(
    NAMESPACE_URL,
    f"northstar:commerce:{dag_run.run_id}",
)
```

A new PipelineRunID is generated for each task execution attempt:

```python
pipeline_run_id = uuid4()
```

Therefore, retries of the same Airflow DAG run retain the same BatchID while creating separate pipeline execution records.

## Operational Database Relationships

The operational monitoring tables provide the following logical hierarchy:

```text
ops.PipelineBatches
    BatchID
        |
        +-- ops.PipelineRuns
                PipelineRunID
                BatchID
                    |
                    +-- ops.PipelineStageRuns
                            PipelineStageRunID
                            PipelineRunID
```

- `ops.PipelineBatches` records the current state of each logical batch.
- `ops.PipelineRuns` records individual execution attempts, including BatchID.
- `ops.PipelineStageRuns` records execution details for individual stages.

The `BatchID` column in `ops.PipelineRuns` is nullable for compatibility with historical records created before the column was introduced.

Historical NULL BatchID values should not be backfilled without a reliable source-to-batch mapping.

## Batch Lifecycle and Retry Safety

The Commerce orchestrator uses the existing batch lifecycle functions:

- `begin_or_retry_batch()`
- `complete_batch()`

The supported transitions are:

| Existing state | Requested action | Outcome |
|---|---|---|
| No batch exists | Begin batch | Create RUNNING batch |
| FAILED | Retry same pipeline | Transition to RUNNING |
| RUNNING | Begin or retry | Reject |
| SUCCESS | Begin or retry | Reject |
| Any existing state | Retry under different pipeline | Reject |

A batch belongs to the pipeline that originally created it. Its BatchID cannot be reused by a different pipeline.

Batch-start transitions use transactional SQL Server locking to prevent concurrent execution attempts from claiming the same batch.

The orchestrator records batch completion or failure only after successfully claiming the batch. A rejected attempt does not overwrite the existing batch's state.

## Airflow Retry Policy

The Commerce DAG uses exception-aware retry rules.

| Exception | Behavior |
|---|---|
| `DataQualityError` | Fail without automatic retry |
| `TransientPipelineError` | Eligible for retry |
| Other exceptions | Follow the task's configured default retry behavior |

The Commerce DAG initially permits up to two retries with a one-minute retry delay.

The retry policy prevents repeated execution of known data-quality failures while allowing recovery from explicitly classified transient infrastructure failures.

Task-level retry, success, and failure callbacks provide operational observability through the existing monitoring components.

A new PipelineRunID is created on each retry, while BatchID remains stable for the Airflow DAG run.

## OrderItems Bronze Uniqueness

The Bronze OrderItems table uses the unique index:

`UX_RawOrderItems_BatchID_OrderItemID`

Its uniqueness key is:

```sql
(BatchID, OrderItemID)
```

This allows multiple order items to belong to the same order within a batch, while preventing the same OrderItemID from being inserted twice into that batch.

OrderItems Bronze ingestion and its associated SQL procedures must preserve this order-item-level grain.

## Verified Local Recovery Scenario

On October 12, 2026, the Commerce pipeline was executed locally against the development warehouse.

The first execution failed during OrderItems Bronze ingestion because of an incorrect uniqueness constraint.

After correcting the constraint, the same logical BatchID was retried with a new PipelineRunID.

The retry completed successfully.

The operational database recorded:

- One logical Commerce batch.
- Two pipeline execution attempts.
- A FAILED first attempt.
- A SUCCESS second attempt.
- A final batch status of SUCCESS.
- A reported batch RowsProcessed value of 14.

This demonstrates local recovery using a stable logical batch identity and distinct execution-attempt identities.

This local execution does not, by itself, establish that the Commerce Airflow DAG and all its retry callbacks have been tested successfully.

## Local Execution

The Commerce orchestrator can be executed directly without Airflow.

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1

$env:PYTHONPATH = "src"

python -c "from uuid import uuid4; from commerce_pipeline import run_commerce_pipeline; result = run_commerce_pipeline(pipeline_run_id=uuid4(), batch_id=uuid4()); print(result)"
```

The command runs the five-entity Commerce pipeline using the configured source and warehouse database connections.

Before running it, confirm that environment variables point to the intended development databases.

For retry testing, reuse the BatchID from a failed execution and generate a new PipelineRunID.

## Verification and Testing

The project includes unit tests for:

- Bronze extraction and loading.
- Optional record processor invocation.
- Prevention of Bronze loading when record processing fails.
- Silver result normalization.
- Entity execution order.
- Failure propagation.
- Customer validation, quarantine, and threshold enforcement.
- Commerce batch lifecycle behavior.

SQL Server integration tests exercise database-backed behavior, including batch ownership and retry safety.

Run:

```powershell
python -m pytest tests -v
python -m pytest integration_tests -v
```

Airflow validation is a separate checkpoint. Before enabling the Commerce DAG schedule, verify that the DAG imports, manual execution succeeds, retry rules behave as intended, and monitoring callbacks produce the expected operational events.

## Design Principles

The reusable framework follows these principles:

**Separation of concerns:** Generic stage execution is separated from entity-specific business rules.

**Explicit dependencies:** Commerce entity ordering remains visible and deterministic.

**Idempotent batch processing:** Retries reuse a logical BatchID while recording distinct execution attempts.

**Operational traceability:** Batch, pipeline-run, and stage-run records support investigation and recovery.

**Extensibility:** New entities can reuse the framework without duplicating Bronze and Silver execution mechanics.

**Airflow compatibility:** Airflow provides scheduling and retry coordination without duplicating the Commerce orchestrator's lifecycle responsibilities.

## Maintenance Guidance

When modifying the framework:

1. Keep entity-specific validation and quarantine rules outside generic stage execution.
2. Preserve BatchID across retries of the same logical batch.
3. Generate a new PipelineRunID for each new execution attempt.
4. Do not allow different pipelines to claim the same BatchID.
5. Preserve the business grain and uniqueness keys of Bronze tables.
6. Update the canonical database deployment scripts alongside schema migrations.
7. Add unit and integration regression tests for changes to lifecycle behavior.
8. Verify Airflow orchestration separately from direct Python execution.
9. Keep this document aligned with implemented behavior rather than planned functionality.