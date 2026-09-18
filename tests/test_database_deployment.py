

import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

SRC_PATH = Path(__file__).resolve().parents[1] / "src"

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))
    
from database_deployment import apply_migration, apply_pending_migrations, deploy_database, read_deployment_manifest, split_sql_batches,get_migration_id


def test_split_sql_batches():
    sql = """        SELECT 1;
                    GO        
                    SELECT 2;
                    go 
                    SELECT 3;    """

    batches = split_sql_batches(sql)

    assert len(batches) == 3
    assert "SELECT 1" in batches[0]
    assert "SELECT 2" in batches[1]
    assert "SELECT 3" in batches[2]

def test_split_sql_batches_only_splits_go_on_own_line():
    sql = """        SELECT 'GO is text';
                    SELECT 2;    """

    batches = split_sql_batches(sql)

    assert len(batches) == 1

def test_manifest_preserves_script_order(
    tmp_path,
):
    first = tmp_path / "001.sql"
    second = tmp_path / "002.sql"

    first.write_text(        "SELECT 1;",        encoding="utf-8",    )

    second.write_text(        "SELECT 2;",        encoding="utf-8",    )

    manifest = (        tmp_path / "deploy_manifest.txt"    )

    manifest.write_text(        "001.sql\n002.sql\n",        encoding="utf-8",    )

    result = read_deployment_manifest(        tmp_path    )

    assert result == [        first,        second,    ]

def test_manifest_rejects_missing_script(
    tmp_path,
):
    manifest = (        tmp_path / "deploy_manifest.txt"    )

    manifest.write_text(        "missing.sql\n",        encoding="utf-8",    )

    with pytest.raises(FileNotFoundError):
        read_deployment_manifest(            tmp_path        )

@patch(
    "database_deployment.execute_sql_script"
)
@patch(
    "database_deployment.read_deployment_manifest"
)
def test_deployment_rolls_back_on_failure(
    mock_manifest,
    mock_execute,
    tmp_path,
):
    connection = Mock()

    script = tmp_path / "001.sql"

    mock_manifest.return_value = [
        script
    ]

    mock_execute.side_effect = RuntimeError(
        "Deployment failed"
    )

    with pytest.raises(
        RuntimeError,
        match="Deployment failed",
    ):
        deploy_database(
            connection,
            tmp_path,
        )

    connection.rollback.assert_called_once()
    connection.commit.assert_not_called()

def test_get_migration_id():
    path = Path(
        "20260918_001_add_event_hostname.sql"
    )

    assert get_migration_id(path) == (
        "20260918_001_add_event_hostname"
    )

@patch(
    "database_deployment.apply_migration"
)
@patch(
    "database_deployment.get_applied_migrations"
)
def test_pending_migrations_skip_applied(
    mock_applied,
    mock_apply,
    tmp_path,
):
    migrations = tmp_path / "migrations"
    migrations.mkdir()

    first = migrations / "001_first.sql"
    second = migrations / "002_second.sql"

    first.write_text(
        "SELECT 1;",
        encoding="utf-8",
    )

    second.write_text(
        "SELECT 2;",
        encoding="utf-8",
    )

    (
        migrations / "migrations.txt"
    ).write_text(
        "001_first.sql\n"
        "002_second.sql\n",
        encoding="utf-8",
    )

    mock_applied.return_value = {
        "001_first"
    }

    connection = Mock()

    apply_pending_migrations(
        connection,
        tmp_path,
    )

    mock_apply.assert_called_once_with(
        connection,
        second,
    )

@patch(
    "database_deployment.execute_sql_script"
)
def test_apply_migration_records_history(
    mock_execute,
    tmp_path,
):
    script = (
        tmp_path
        / "20260918_001_test.sql"
    )

    script.write_text(
        "SELECT 1;",
        encoding="utf-8",
    )

    connection = Mock()
    cursor = connection.cursor.return_value

    apply_migration(
        connection,
        script,
    )

    mock_execute.assert_called_once_with(
        connection,
        script,
    )

    cursor.execute.assert_called_once()

    sql, migration_id = (
        cursor.execute.call_args.args
    )

    assert "SchemaMigrations" in sql

    assert migration_id == (
        "20260918_001_test"
    )