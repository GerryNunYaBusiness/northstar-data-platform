import sys
from pathlib import Path
from uuid import UUID

SRC_PATH = Path(__file__).resolve().parent / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from customer_pipeline import run_customer_pipeline


batch_id = UUID("11111111-2222-3333-4444-555555555555")

print(f"Running BatchID: {batch_id}")

try:
    result = run_customer_pipeline(
        batch_id=batch_id,
    )

    print(f"PipelineRunID: {result.pipeline_run_id}")
    print(f"BatchID:       {result.batch_id}")
    print(f"Status:        {result.status}")

except Exception as exc:
    print(f"Pipeline failed: {exc}")
    raise