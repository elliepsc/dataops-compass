Hooks
=====

Hooks are interfaces to external platforms and databases, built on top of Python libraries or APIs. They abstract the connection and interaction logic, and use Connections to retrieve authentication parameters.

Why Use Hooks
-------------

Hooks provide:

- A consistent interface to external systems
- Reusable connection logic across operators
- Automatic connection management

Built-in Hooks
--------------

Airflow includes many built-in hooks:

**Database Hooks**

- ``PostgresHook``: Connect to PostgreSQL
- ``MySqlHook``: Connect to MySQL
- ``SqliteHook``: Connect to SQLite
- ``BigQueryHook``: Connect to Google BigQuery

**Cloud Hooks**

- ``GCSHook``: Google Cloud Storage
- ``S3Hook``: Amazon S3
- ``AzureDataFactoryHook``: Azure Data Factory

**Other Hooks**

- ``HttpHook``: HTTP requests
- ``SlackHook``: Slack notifications
- ``SFTPHook``: SFTP file transfers

Using a Hook
------------

.. code-block:: python

    from airflow.providers.postgres.hooks.postgres import PostgresHook

    def my_task():
        hook = PostgresHook(postgres_conn_id='my_postgres_conn')
        
        # Execute a query
        hook.run('INSERT INTO logs VALUES (%s)', parameters=['value'])
        
        # Get records
        records = hook.get_records('SELECT * FROM my_table')
        
        # Get pandas DataFrame
        df = hook.get_pandas_df('SELECT * FROM my_table')

Creating Custom Hooks
---------------------

.. code-block:: python

    from airflow.hooks.base import BaseHook

    class MyCustomHook(BaseHook):
        conn_name_attr = 'my_conn_id'
        default_conn_name = 'my_default_conn'
        conn_type = 'my_type'
        
        def __init__(self, my_conn_id='my_default_conn'):
            super().__init__()
            self.my_conn_id = my_conn_id
        
        def get_conn(self):
            conn = self.get_connection(self.my_conn_id)
            # Return your connection object
            return conn
        
        def my_method(self):
            conn = self.get_conn()
            # Do something with the connection

Hook vs Operator
----------------

- **Hook**: Low-level interface to external system. Reusable across operators.
- **Operator**: Defines a unit of work in a DAG. Often uses a Hook internally.

Most operators accept a ``conn_id`` parameter that is passed to the underlying Hook.
