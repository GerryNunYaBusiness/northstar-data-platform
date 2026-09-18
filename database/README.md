# Northstar Database Deployment

The `database` directory contains the version-controlled SQL
definition required by the Northstar customer data pipeline.

## Deployment

From the repository root:

    python src/database_deployment.py

The target warehouse is controlled by:

    NORTHSTAR_WAREHOUSE_DATABASE

When the variable is not supplied, the application defaults to:

    NorthstarWarehouse

## Deployment order

Scripts are executed according to:

    database/deploy_manifest.txt

The current phases are:

1. Schemas
2. Tables
3. Indexes
4. Stored procedures
5. Views
6. Permissions

## Clean deployment testing

A clean deployment can be tested against a temporary database such as:

    NorthstarWarehouse_DeploymentTest

Set the environment variable before deployment:

    $env:NORTHSTAR_WAREHOUSE_DATABASE =
        "NorthstarWarehouse_DeploymentTest"

Then run:

    python src/database_deployment.py

The deployment should also succeed when run a second time.

For integration validation, Airflow can temporarily be pointed at
the same test warehouse by setting the environment variable before
recreating the Airflow containers.

Remove the environment override and recreate Airflow after testing.

## Security

Credentials and webhook URLs must not be committed to this directory.

The deployment assumes the SQL Server login `northstar_pipeline`
already exists. The deployment creates the corresponding database
user and applies the required object-level permissions.