from datetime import datetime, timezone
from pathlib import Path
import sys
from uuid import uuid4


SRC_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
)

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


def test_pipeline_login_can_read_source_customers(
    source_database,
):
    from integration_tests.conftest import (
        get_pipeline_database_connection,
    )

    connection = (
        get_pipeline_database_connection(
            source_database
        )
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM dbo.Customers;
        """
    )

    count = cursor.fetchone()[0]

    connection.close()

    assert count >= 1

def test_pipeline_login_can_access_raw_customers(
    deployed_warehouse,
):
    from integration_tests.conftest import (
        get_pipeline_database_connection,
    )

    connection = (
        get_pipeline_database_connection(
            deployed_warehouse
        )
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM raw.Customers;
        """
    )

    count = cursor.fetchone()[0]

    connection.close()

    assert count >= 0

def test_pipeline_login_has_silver_execute_permission(
    deployed_warehouse,
):
    from integration_tests.conftest import (
        get_pipeline_database_connection,
    )

    connection = (
        get_pipeline_database_connection(
            deployed_warehouse
        )
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT HAS_PERMS_BY_NAME(
            'silver.usp_LoadCustomers',
            'OBJECT',
            'EXECUTE'
        );
        """
    )

    has_permission = cursor.fetchone()[0]

    connection.close()

    assert has_permission == 1