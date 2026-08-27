import logging
import sys

import pyodbc

from pipeline import run_warehouse_pipeline


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
    logger.info("Starting Northstar warehouse pipeline")

    try:
        result = run_warehouse_pipeline()

        logger.info(
            "Pipeline completed "
            "pipeline_run_id=%s status=%s "
            "rows_inserted=%s rows_updated=%s",
            result.pipeline_run_id,
            result.status,
            result.rows_inserted,
            result.rows_updated,
        )

        if result.status != "SUCCESS":
            logger.error(
                "Pipeline reported failure "
                "pipeline_run_id=%s error=%s",
                result.pipeline_run_id,
                result.error_message,
            )
            return 1

        return 0

    except pyodbc.Error:
        logger.exception(
            "Database error while running pipeline"
        )
        return 1

    except Exception:
        logger.exception(
            "Unexpected pipeline error"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())