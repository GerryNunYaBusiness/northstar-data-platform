import logging
import sys

from customer_pipeline import run_customer_pipeline


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
    logger.info("Starting customer pipeline")

    try:
        result = run_customer_pipeline()

        logger.info(
            "Pipeline finished "
            "pipeline_run_id=%s status=%s",
            result.pipeline_run_id,
            result.status,
        )

        for stage in result.stages:
            logger.info(
                "Pipeline stage "
                "name=%s status=%s "
                "rows_processed=%s message=%s",
                stage.name,
                stage.status,
                stage.rows_processed,
                stage.message,
            )

        if result.status != "SUCCESS":
            return 1

        return 0

    except Exception:
        logger.exception(
            "Unhandled customer pipeline failure"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())