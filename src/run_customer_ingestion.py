import logging
import sys
import uuid

from ingestion.customers import (
    extract_customers,
    load_raw_customers,
    validate_customers,
)


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s "
        "%(levelname)s "
        "%(name)s "
        "%(message)s"
    ),
)

logger = logging.getLogger(__name__)


def main() -> int:
    pipeline_run_id = uuid.uuid4()

    logger.info(
        "Starting customer ingestion pipeline_run_id=%s",
        pipeline_run_id,
    )

    try:
        customers = extract_customers()

        logger.info(
            "Extracted customers count=%s",
            len(customers),
        )

        errors = validate_customers(customers)

        if errors:
            for error in errors:
                logger.error(
                    "Customer validation error: %s",
                    error,
                )

            logger.error(
                "Customer ingestion aborted "
                "validation_errors=%s",
                len(errors),
            )

            return 1

        rows_loaded = load_raw_customers(
            customers,
            pipeline_run_id,
        )

        logger.info(
            "Customer ingestion completed "
            "pipeline_run_id=%s rows_loaded=%s",
            pipeline_run_id,
            rows_loaded,
        )

        return 0

    except Exception:
        logger.exception(
            "Customer ingestion failed "
            "pipeline_run_id=%s",
            pipeline_run_id,
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())