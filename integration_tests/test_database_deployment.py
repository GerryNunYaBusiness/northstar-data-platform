from pathlib import Path
import sys


SRC_PATH = (    Path(__file__).resolve().parents[1]    / "src")

if str(SRC_PATH) not in sys.path:
    sys.path.insert(        0,        str(SRC_PATH),    )


from database_deployment import deploy_database

def test_database_deployment_creates_core_objects(
    warehouse_connection,
):
    project_root = (
        Path(__file__).resolve().parents[1]
    )

    database_directory = (
        project_root / "database"
    )

    deploy_database(
        warehouse_connection,
        database_directory,
    )

    cursor = warehouse_connection.cursor()

    cursor.execute(
        """
        SELECT
            OBJECT_ID('raw.Customers', 'U'),
            OBJECT_ID('silver.Customers', 'U'),
            OBJECT_ID('ops.PipelineRuns', 'U'),
            OBJECT_ID(
                'raw.usp_LoadCustomersForBatch',
                'P'
            ),
            OBJECT_ID(
                'silver.usp_LoadCustomers',
                'P'
            );
        """
    )

    row = cursor.fetchone()

    assert all(
        object_id is not None
        for object_id in row
    )