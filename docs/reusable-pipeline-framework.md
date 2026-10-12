# Northstar Data Platform — Reusable Pipeline Framework

## 1. Purpose

The reusable pipeline framework provides standardized execution mechanics for the Northstar Data Platform's Bronze and Silver data processing stages.

Its purpose is to eliminate duplicated orchestration logic while preserving entity-specific business rules and explicit pipeline dependency ordering.

The framework supports:

- Reusable Bronze extraction and loading
- Reusable Silver transformation execution
- Standardized stage monitoring
- Consistent execution result reporting
- Exception propagation
- Strongly typed execution contracts
- Declarative entity pipeline definitions

The framework does not replace Airflow, SQL Server stored procedures, or entity-specific transformation logic.

## 2. Architectural Overview

The commerce pipeline processes five business entities in dependency-safe order:

1. Customers
2. Products
3. Orders
4. OrderItems
5. Payments

Each entity executes two stages:

1. Bronze — Extract source records and load them into raw SQL Server tables.
2. Silver — Validate and transform Bronze records into Silver tables.

Execution architecture:

```text
run_commerce_pipeline()
        |
        v
COMMERCE_PIPELINES
        |
        v
EntityPipeline
        |
        v
execute_entity_pipeline()
        |
        +--> execute_bronze_stage()
        |        |
        |        +--> Extract records
        |        +--> Load Bronze
        |        +--> Record stage metrics
        |
        +--> execute_silver_stage()
                 |
                 +--> Execute Silver transformation
                 +--> Collect result counts
                 +--> Record stage metrics
```

The commerce orchestrator owns the overall pipeline lifecycle. The framework owns individual stage execution.

## 3. Framework File Reference

### `src/pipeline_framework/__init__.py`

Identifies `pipeline_framework` as a Python package.

### `src/pipeline_framework/context.py`

Defines `PipelineContext`, an immutable dataclass containing:

- `pipeline_run_id`: Unique identifier for an execution attempt.
- `batch_id`: Unique identifier for a logical source-data batch.

A retry of the same logical batch uses the same BatchID but a new PipelineRunID.

### `src/pipeline_framework/results.py`

Defines `StageResult`, an immutable dataclass containing:

- `stage_name`
- `rows_inserted`
- `rows_updated`
- `rows_quarantined`

All row-count fields default to zero.

This provides a consistent operational result structure across Bronze and Silver stages.

### `src/pipeline_framework/contracts.py`

Defines the `SilverResult` Protocol.

A compatible Silver transformation result must expose readable integer properties:

- `rows_inserted`
- `rows_updated`

The framework uses structural typing. Entity-specific result classes do not need to inherit from a common base class.

An optional `rows_quarantined` attribute is read when available; otherwise, the framework reports zero.

### `src/pipeline_framework/stages.py`

Defines two execution functions.

**`execute_bronze_stage()`**

Responsibilities:

- Start monitored stage execution.
- Invoke the entity extractor.
- Pass extracted records and execution identifiers to the Bronze loader.
- Return a standardized `StageResult`.
- Allow exceptions to propagate.

**`execute_silver_stage()`**

Responsibilities:

- Start monitored stage execution.
- Invoke the entity Silver loader.
- Collect inserted, updated, and optional quarantined row counts.
- Return a standardized `StageResult`.
- Allow exceptions to propagate.

Both functions use `pipeline_stage` from `src/monitoring/pipeline_runs.py` for stage observability.

### `src/pipeline_framework/entity.py`

Defines:

**`EntityPipeline`**

An immutable, generic configuration object containing:

- Entity name
- Extractor function
- Bronze loader function
- Silver loader function

**`execute_entity_pipeline()`**

Executes Bronze followed by Silver for a single entity and returns both stage results.

A Bronze failure prevents that entity's Silver stage from executing.

## 4. Commerce Orchestration

### `src/commerce_pipeline.py`

Defines the five entity configurations and their execution order in `COMMERCE_PIPELINES`.

The orchestrator is responsible for:

- Creating execution context
- Starting the overall pipeline run
- Executing entities in dependency-safe order
- Collecting stage results
- Marking successful runs as `SUCCESS`
- Marking failed runs as `FAILED`
- Propagating failures to the caller

The framework does not determine entity dependency ordering.

The ordered list is maintained explicitly because dependencies are currently known and manageable.

## 5. Entity-Specific Implementation Files

Entity-specific logic remains outside the framework.

| Entity | Bronze ingestion | Silver transformation |
|---|---|---|
| Customers | `src/ingestion/customers.py` | `src/transformation/customers.py` |
| Products | `src/ingestion/products.py` | `src/transformation/products.py` |
| Orders | `src/ingestion/orders.py` | `src/transformation/orders.py` |
| OrderItems | `src/ingestion/order_items.py` | `src/transformation/order_items.py` |
| Payments | `src/ingestion/payments.py` | `src/transformation/payments.py` |

These modules own entity-specific behavior, including extraction queries, business-column hashing, and calls to database loading procedures.

SQL Server procedures own the corresponding database transformations, validation, and quarantine operations.

The reusable framework must not contain entity-specific SQL or business validation rules.

## 6. Batch and Execution Semantics

Northstar distinguishes logical data batches from execution attempts.

**BatchID**

Identifies the logical source snapshot being processed.

**PipelineRunID**

Identifies a particular attempt to process that batch.

Examples:

- New source snapshot: New BatchID and new PipelineRunID.
- Retry of failed batch: Existing BatchID and new PipelineRunID.

Bronze loading must preserve batch-level idempotency.

A repeated attempt must not create duplicate records for the same entity and BatchID.

The framework passes these identifiers to loaders but does not implement SQL Server deduplication itself.

## 7. Data Quality and Quarantine

Bronze preserves source data, including records that may fail business validation.

Silver transformations apply entity-specific rules and quarantine invalid records.

Examples include:

- Invalid identifiers
- Missing required values
- Unsupported business status values
- Invalid amounts or quantities
- Missing referenced customers, orders, or products

Where applicable, multiple validation failures for a source record are consolidated into one quarantine record containing the relevant reasons.

The framework reports quarantine counts when provided by the Silver transformation result.

It does not decide which records are valid.

## 8. Error Handling and Observability

Individual stages are monitored through `pipeline_stage`.

The monitoring layer records stage execution outcomes and associated operational information.

Exceptions are not silently swallowed by framework executors.

Failure behavior:

```text
Entity Bronze or Silver failure
          |
          v
Framework propagates exception
          |
          v
Commerce orchestrator catches exception
          |
          v
Pipeline marked FAILED
          |
          v
Exception re-raised
```

Downstream entities must not execute after an upstream entity fails.

The existing monitoring infrastructure includes pipeline-run and stage-run records and related operational events.

## 9. Adding a New Entity

To introduce a new entity, such as Shipments:

1. Implement the source extractor.
2. Implement the Bronze loader and required database objects.
3. Implement the Silver transformation and required database objects.
4. Define an `EntityPipeline` configuration.
5. Add the configuration to `COMMERCE_PIPELINES` in dependency-safe order.
6. Add unit tests and integration tests.
7. Update deployment manifests and relevant documentation.

Example:

```python
SHIPMENTS_PIPELINE = EntityPipeline(
    name="shipments",
    extractor=extract_shipments,
    bronze_loader=load_raw_shipments,
    silver_loader=load_silver_shipments,
)
```

The extractor must return a list of entity records.

The Bronze loader must accept records, PipelineRunID, and BatchID, returning an inserted-row count.

The Silver loader must accept PipelineRunID and BatchID, returning an object compatible with the `SilverResult` Protocol.

Adding a standard entity should not require modifications to the reusable execution functions.

## 10. Testing Strategy

### Framework Unit Tests

Location: `tests/test_pipeline_framework.py`

Tests cover:

- Bronze extractor and loader invocation
- Bronze exception propagation
- Silver result normalization
- Optional quarantine counts
- Silver exception propagation
- Entity Bronze-before-Silver sequencing
- Correct function wiring and result aggregation

These tests must not connect to SQL Server.

### Commerce Orchestration Tests

Location: `tests/test_commerce_pipeline.py`

Tests verify:

- Dependency-safe entity execution order
- Pipeline lifecycle behavior
- Failure propagation
- Prevention of downstream execution after failure

The entity execution boundary is mocked to isolate orchestration behavior.

### Integration Tests

Location: `integration_tests/`

Integration tests exercise actual SQL Server behavior using disposable test databases.

They validate database loading, transformation behavior, permissions, and end-to-end pipeline execution.

Application operations use the dedicated least-privilege pipeline identity.

Test infrastructure uses a separate administrative identity.

### Commands

Unit tests:

```powershell
python -m pytest tests -v
```

Integration tests:

```powershell
python -m pytest integration_tests -v
```

Combined validation:

```powershell
python -m pytest tests integration_tests -v
```

The project's `pytest.ini` defaults test discovery to `tests`, so integration tests must be explicitly selected.

## 11. Design Principles and Boundaries

The framework follows these principles:

**Single Responsibility**

The orchestrator, framework, and entity implementations have distinct responsibilities.

**Reusability**

Standard stage mechanics are shared across business entities.

**Extensibility**

New standard entities are introduced through configuration and entity-specific implementations.

**Explicit Dependencies**

Entity ordering remains visible in the commerce pipeline configuration.

**Strong Typing**

Generics and Protocols express relationships between extractors, loaders, and transformation results.

**Test Isolation**

Unit tests mock external boundaries. SQL Server behavior belongs in integration tests.

**Separation of Business Rules**

Entity validation, transformation SQL, and quarantine policies remain outside the framework.

## 12. Intentional Non-Goals

The current framework does not:

- Dynamically discover entity implementations
- Automatically resolve dependency graphs
- Replace Airflow scheduling or orchestration
- Generate SQL Server transformations
- Implement entity-specific validation rules
- Manage database deployment
- Implement database-level transaction or retry policies
- Replace the existing monitoring infrastructure

Additional abstraction should be introduced only when supported by a demonstrated operational or maintenance requirement.

## 13. Maintenance Guidance for Developers and AI Agents

When modifying the pipeline framework:

1. Preserve the distinction between BatchID and PipelineRunID.
2. Preserve Bronze-before-Silver sequencing.
3. Preserve dependency-safe entity ordering.
4. Do not suppress exceptions inside framework executors.
5. Do not introduce SQL Server access into framework unit tests.
6. Keep business-specific rules outside generic framework modules.
7. Maintain the `StageResult` and `SilverResult` contracts, or explicitly update their consumers and tests.
8. Keep pipeline-level lifecycle management in the orchestrator.
9. Update unit and integration tests when execution contracts change.
10. Verify compatibility with the database deployment manifest when database objects change.

The framework is intended to remain small, readable, and predictable. Avoid introducing a generic execution engine unless a concrete requirement justifies the additional complexity.

## 14. Related Project Components

- `src/commerce_pipeline.py` — Commerce orchestration
- `src/monitoring/pipeline_runs.py` — Pipeline and stage observability
- `src/ingestion/` — Source extraction and Bronze loading
- `src/transformation/` — Silver transformation entry points
- `database/` — SQL Server database objects and deployment scripts
- `tests/` — Unit tests
- `integration_tests/` — SQL Server integration tests
- `database/deploy_manifest.txt` — Database deployment ordering
