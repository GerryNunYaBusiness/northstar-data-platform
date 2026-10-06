from pathlib import Path
import os
import sys

import pyodbc
import pytest

SRC_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
)

if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


from database_deployment import deploy_database

#TEST_DATABASE = "NorthstarWarehouse_IntegrationTest"
SOURCE_TEST_DATABASE = "NorthstarCommerce_IntegrationTest"
WAREHOUSE_TEST_DATABASE = "NorthstarWarehouse_IntegrationTest"

os.environ["NORTHSTAR_SOURCE_DATABASE"] = (SOURCE_TEST_DATABASE)
os.environ["NORTHSTAR_WAREHOUSE_DATABASE"] = (WAREHOUSE_TEST_DATABASE)
os.environ["NORTHSTAR_SQL_SERVER"] = "localhost,14330"
os.environ.setdefault("NORTHSTAR_SQL_DRIVER",    "ODBC Driver 17 for SQL Server",)

def get_master_connection():
    driver = os.environ[        "NORTHSTAR_SQL_DRIVER"    ]

    server = os.environ[        "NORTHSTAR_SQL_SERVER"    ]

    username = "sa"  #os.environ[        "NORTHSTAR_SQL_USERNAME"    ]

    password = os.environ[        "NORTHSTAR_INTEGRATION_SQL_PASSWORD"    ]

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        "DATABASE=master;"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(
        connection_string,
        autocommit=True,
    )

def drop_database(
    connection,
    database_name: str,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""
        IF DB_ID('{database_name}') IS NOT NULL
        BEGIN
            ALTER DATABASE [{database_name}]
                SET SINGLE_USER
                WITH ROLLBACK IMMEDIATE;

            DROP DATABASE [{database_name}];
        END;
        """
    )

def create_database(
    connection,
    database_name: str,
):
    cursor = connection.cursor()

    cursor.execute(
        f"""
        CREATE DATABASE [{database_name}];
        """
    )

@pytest.fixture(scope="session")
def integration_databases():
    connection = get_master_connection()

    password = os.environ[        "NORTHSTAR_SQL_PASSWORD"    ]
    # print(f" Creating integration test databases: {SOURCE_TEST_DATABASE}, {WAREHOUSE_TEST_DATABASE}")
    create_pipeline_login(
        connection,
        password,
    )

    drop_database(
        connection,
        SOURCE_TEST_DATABASE,
    )

    drop_database(
        connection,
        WAREHOUSE_TEST_DATABASE,
    )

    create_database(
        connection,
        SOURCE_TEST_DATABASE,
    )

    create_database(
        connection,
        WAREHOUSE_TEST_DATABASE,
    )

    connection.close()

    yield {
        "source": SOURCE_TEST_DATABASE,
        "warehouse": WAREHOUSE_TEST_DATABASE,
    }

    connection = get_master_connection()

    drop_database(
        connection,
        SOURCE_TEST_DATABASE,
    )

    drop_database(
        connection,
        WAREHOUSE_TEST_DATABASE,
    )

    connection.close()

@pytest.fixture(scope="session")
def warehouse_connection(
    # integration_databases,
    deployed_warehouse,
):
    # database_name = (
    #     integration_databases["warehouse"]
    # )

    # connection = get_admin_database_connection(
    #     database_name
    # )
    connection = get_admin_database_connection(
        deployed_warehouse
    )

    yield connection

    connection.close()

@pytest.fixture(scope="session")
def source_connection(
    synthetic_source,
    integration_databases,
):
    connection = get_admin_database_connection(
        integration_databases["source"]
    )

    try:
        yield connection
    finally:
        connection.close()

def create_pipeline_login(
    connection,
    password: str,
):
    cursor = connection.cursor()

    escaped_password = password.replace(
        "'",
        "''",
    )

    cursor.execute(
        f"""
        IF SUSER_ID('northstar_pipeline') IS NULL
        BEGIN
            CREATE LOGIN northstar_pipeline
            WITH PASSWORD = '{escaped_password}';
        END
        ELSE
        BEGIN
            ALTER LOGIN northstar_pipeline
            WITH PASSWORD = '{escaped_password}';
        END;
        """
    )

def get_admin_database_connection(
    database_name: str,
):
    driver = os.environ[        "NORTHSTAR_SQL_DRIVER"    ]

    server = os.environ[        "NORTHSTAR_SQL_SERVER"    ]

    username = "sa" # os.environ[        "NORTHSTAR_SQL_USERNAME"    ]

    password = os.environ[        "NORTHSTAR_INTEGRATION_SQL_PASSWORD"    ]

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database_name};"
        f"UID={username};"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(
        connection_string
    )

def get_pipeline_database_connection(
    database_name: str,
):
    driver = os.environ[        "NORTHSTAR_SQL_DRIVER"    ]

    server = os.environ[        "NORTHSTAR_SQL_SERVER"    ]

    password = os.environ[        "NORTHSTAR_INTEGRATION_PIPELINE_PASSWORD"    ]

    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server};"
        f"DATABASE={database_name};"
        "UID=northstar_pipeline;"
        f"PWD={password};"
        "Encrypt=yes;"
        "TrustServerCertificate=yes;"
    )

    return pyodbc.connect(
        connection_string
    )

@pytest.fixture(scope="session")
def source_database(integration_databases):
    database_name = (
        integration_databases["source"]
    )
    print(f"Setting up source database: {database_name}")
    connection = get_admin_database_connection(
        database_name
    )

    cursor = connection.cursor()

    # cursor.execute(
    #     """
    #     CREATE TABLE dbo.Customers
    #     (
    #         CustomerID INT NOT NULL
    #             CONSTRAINT PK_Customers
    #             PRIMARY KEY,

    #         FirstName NVARCHAR(100) NOT NULL,
    #         LastName NVARCHAR(100) NOT NULL,
    #         Email NVARCHAR(255) NULL,
    #         Phone NVARCHAR(50) NULL,
    #         CreatedAt DATETIME2(3) NOT NULL
    #     );
    #     """
    # )
    cursor.execute(
        """
        INSERT INTO dbo.Customers
        (
            CustomerID,
            FirstName,
            LastName,
            Email,
            Phone,
            CreatedAt
        )
        VALUES
            (
                1,
                'Ada',
                'Lovelace',
                'ada@example.test',
                '555-0101',
                '2026-01-01T12:00:00'
            ),
            (
                2,
                'Grace',
                'Hopper',
                'grace@example.test',
                '555-0102',
                '2026-01-02T12:00:00'
            );
        """
    )

    connection.commit()
    connection.close()
    print(f"Source database {database_name} setup complete.")

    grant_source_permissions(    database_name)

    return database_name

@pytest.fixture(scope="session")
def deployed_warehouse(
    integration_databases,
    # warehouse_connection,
):
    project_root = (
        Path(__file__).resolve().parents[1]
    )

    database_directory = (
        project_root / "database"
    )

    database_name = (
        integration_databases["warehouse"]
    )
    deployment_connection = get_admin_database_connection(
        database_name
    )

    # print("calling DEPLOY_DATABASE ")
    # deploy_database(
    #     warehouse_connection,
    #     database_directory,
    # )

    try:
        deploy_database(
            deployment_connection,
            database_directory,
        )

        yield database_name

    finally:
        deployment_connection.close()

def test_database_deployment_creates_core_objects(
    deployed_warehouse,
    warehouse_connection,
):
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

def grant_source_permissions(
    database_name: str,
):
    connection = get_admin_database_connection(
        database_name
    )

    cursor = connection.cursor()

    cursor.execute(
        """
        IF USER_ID('northstar_pipeline') IS NULL
        BEGIN
            CREATE USER northstar_pipeline
            FOR LOGIN northstar_pipeline;
        END;
        """
    )

    cursor.execute(
        """
        GRANT SELECT
        ON dbo.Customers
        TO northstar_pipeline;
        """
    )
    #print ("Granted SELECT permission on dbo.Customers to northstar_pipeline")

    connection.commit()
    connection.close()


@pytest.fixture(scope="session")
def synthetic_source(
    integration_databases,
):
    database_name = integration_databases["source"]

    connection = get_admin_database_connection(
        database_name
    )

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            IF OBJECT_ID('dbo.Payments', 'U') IS NOT NULL
                DROP TABLE dbo.Payments;

            IF OBJECT_ID('dbo.OrderItems', 'U') IS NOT NULL
                DROP TABLE dbo.OrderItems;

            IF OBJECT_ID('dbo.Orders', 'U') IS NOT NULL
                DROP TABLE dbo.Orders;

            IF OBJECT_ID('dbo.Products', 'U') IS NOT NULL
                DROP TABLE dbo.Products;

            IF OBJECT_ID('dbo.Customers', 'U') IS NOT NULL
                DROP TABLE dbo.Customers;
            """
        )

        # Customers
        cursor.execute(
            """
            CREATE TABLE dbo.Customers
            (
                CustomerID INT NOT NULL
                    CONSTRAINT PK_TestCustomers PRIMARY KEY,

                FirstName NVARCHAR(100) NOT NULL,
                LastName NVARCHAR(100) NOT NULL,
                Email NVARCHAR(255) NULL,
                Phone NVARCHAR(50) NULL,
                CreatedAt DATETIME2(7) NOT NULL
            );
            """
        )

        # Products
        cursor.execute(
            """
            CREATE TABLE dbo.Products
            (
                ProductID INT NOT NULL
                    CONSTRAINT PK_TestProducts PRIMARY KEY,

                ProductName NVARCHAR(255) NOT NULL,
                Category NVARCHAR(100) NOT NULL,
                UnitCost DECIMAL(18,2) NOT NULL,
                UnitPrice DECIMAL(18,2) NOT NULL
            );
            """
        )

        # Orders
        cursor.execute(
            """
            CREATE TABLE dbo.Orders
            (
                OrderID INT NOT NULL
                    CONSTRAINT PK_TestOrders PRIMARY KEY,

                CustomerID INT NOT NULL,
                OrderDate DATETIME2(7) NOT NULL,
                [Status] NVARCHAR(50) NOT NULL,
                TotalAmount DECIMAL(18,2) NOT NULL
            );
            """
        )

        # OrderItems
        cursor.execute(
            """
            CREATE TABLE dbo.OrderItems
            (
                OrderItemID INT NOT NULL
                    CONSTRAINT PK_TestOrderItems PRIMARY KEY,

                OrderID INT NOT NULL,
                ProductID INT NOT NULL,
                Quantity INT NOT NULL,
                UnitPrice DECIMAL(18,2) NOT NULL
            );
            """
        )

        # Payments
        cursor.execute(
            """
            CREATE TABLE dbo.Payments
            (
                PaymentID INT NOT NULL
                    CONSTRAINT PK_TestPayments PRIMARY KEY,

                OrderID INT NOT NULL,
                PaymentDate DATETIME2(7) NOT NULL,
                PaymentMethod NVARCHAR(50) NOT NULL,
                Amount DECIMAL(18,2) NOT NULL,
                [Status] NVARCHAR(50) NOT NULL
            );
            """
        )

        # escaped_password = os.environ[        "NORTHSTAR_SQL_PASSWORD"    ].replace( "'", "''", )

        # cursor.execute(
        #     """
        #     IF SUSER_ID('northstar_pipeline') IS NULL
        #     BEGIN
        #         CREATE LOGIN northstar_pipeline
        #         WITH PASSWORD = '{escaped_password}';
        #     END
        #     ELSE
        #     BEGIN
        #         ALTER LOGIN northstar_pipeline
        #         WITH PASSWORD = '{escaped_password}';
        #     END;
        #     """
        # )
        
        # create_pipeline_login(
        #     connection,
        #     os.environ[        "NORTHSTAR_SQL_PASSWORD"    ],
        # )
        # connection.commit()

        # Permissions for northstar_pipeline user
        cursor.execute(
            """
            IF DATABASE_PRINCIPAL_ID('northstar_pipeline') IS NULL
            BEGIN
                CREATE USER northstar_pipeline
                FOR LOGIN northstar_pipeline;
            END;            
            GRANT SELECT ON dbo.Customers TO northstar_pipeline;
            GRANT SELECT ON dbo.Products TO northstar_pipeline;
            GRANT SELECT ON dbo.Orders TO northstar_pipeline;
            GRANT SELECT ON dbo.OrderItems TO northstar_pipeline;
            GRANT SELECT ON dbo.Payments TO northstar_pipeline;
            """
        )

        connection.commit()

        yield database_name

    finally:
        connection.close()