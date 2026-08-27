import logging
import sys

from transformation.customers import load_silver_customers


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
    logger.info("Starting Silver customer load")

    try:
        result = load_silver_customers()

        logger.info(
            "Silver customer load completed "
            "inserted=%s updated=%s",
            result.inserted,
            result.updated,
        )

        return 0

    except Exception:
        logger.exception(
            "Silver customer load failed"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())