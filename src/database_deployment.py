from pathlib import Path
import re


GO_PATTERN = re.compile(
    r"^\s*GO\s*;?\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def split_sql_batches(sql: str) -> list[str]:
    batches = GO_PATTERN.split(sql)

    return [
        batch.strip()
        for batch in batches
        if batch.strip()
    ]

def read_deployment_manifest(
    database_directory: Path,
) -> list[Path]:
    return read_manifest(
        database_directory
        / "deploy_manifest.txt",
        database_directory,
    )

def get_applied_migrations(
    connection,
) -> set[str]:
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT SM.MigrationID
        FROM ops.SchemaMigrations AS SM;
        """
    )

    return {
        row[0]
        for row in cursor.fetchall()
    }

def get_migration_id(
    script_path: Path,
) -> str:
    return script_path.stem

def read_migration_manifest(
    database_directory: Path,
) -> list[Path]:
    migrations_directory = (
        database_directory / "migrations"
    )

    return read_manifest(
        migrations_directory
        / "migrations.txt",
        migrations_directory,
    )

def apply_migration(
    connection,
    script_path: Path,
) -> None:
    migration_id = get_migration_id(
        script_path
    )

    execute_sql_script(
        connection,
        script_path,
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO ops.SchemaMigrations
        (
            MigrationID
        )
        VALUES (?);
        """,
        migration_id,
    )

def apply_pending_migrations(
    connection,
    database_directory: Path,
) -> None:
    migration_paths = (
        read_migration_manifest(
            database_directory
        )
    )

    applied = get_applied_migrations(
        connection
    )

    for script_path in migration_paths:
        migration_id = get_migration_id(
            script_path
        )

        if migration_id in applied:
            print(
                f"Skipping migration: "
                f"{migration_id}"
            )
            continue

        print(
            f"Applying migration: "
            f"{migration_id}"
        )

        apply_migration(
            connection,
            script_path,
        )

def read_manifest(
    manifest_path: Path,
    base_directory: Path,
) -> list[Path]:
    lines = manifest_path.read_text(
        encoding="utf-8"
    ).splitlines()

    script_paths = []

    for line in lines:
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        script_path = (
            base_directory / line
        )

        if not script_path.is_file():
            raise FileNotFoundError(
                "Deployment script does not exist: "
                f"{script_path}"
            )

        script_paths.append(script_path)

    return script_paths

def execute_sql_script(
    connection,
    script_path: Path,
) -> None:
    sql = script_path.read_text(
        encoding="utf-8"
    )

    batches = split_sql_batches(sql)

    cursor = connection.cursor()

    for batch in batches:
        cursor.execute(batch)

def deploy_database(
    connection,
    database_directory: Path,
) -> None:
    script_paths = read_deployment_manifest(
        database_directory
    )

    try:
        for script_path in script_paths:
            print(
                "Applying: "
                f"{script_path.relative_to(database_directory)}"
            )

            execute_sql_script(
                connection,
                script_path,
            )

        apply_pending_migrations(
            connection,
            database_directory,
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise


#This is runable as a script for DB object deployment.
if __name__ == "__main__":
    from database import (
        get_warehouse_connection,
    )

    project_root = (
        Path(__file__).resolve().parents[1]
    )

    database_directory = (
        project_root / "database"
    )

    connection = get_warehouse_connection()

    try:
        deploy_database(
            connection,
            database_directory,
        )

        print(
            "Database deployment completed successfully."
        )

    finally:
        connection.close()