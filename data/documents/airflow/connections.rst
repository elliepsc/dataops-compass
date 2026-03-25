Connections
===========

A connection is a set of parameters - such as hostname, port, login, password, and extra - that Airflow uses to connect to external systems.

Connections are stored in the Airflow metadata database and can be managed via the UI, CLI, or environment variables.

Managing Connections
--------------------

Via the UI
~~~~~~~~~~
Go to **Admin > Connections** to add, edit, or delete connections.

Via the CLI
~~~~~~~~~~~
.. code-block:: bash

    airflow connections add 'my_conn' \
        --conn-type 'postgres' \
        --conn-host 'localhost' \
        --conn-port '5432' \
        --conn-login 'user' \
        --conn-password 'password' \
        --conn-schema 'mydb'

Via Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~
Connections can be defined using environment variables with the format:

.. code-block:: bash

    AIRFLOW_CONN_{CONN_ID}='{connection-uri}'

For example:

.. code-block:: bash

    AIRFLOW_CONN_MY_POSTGRES='postgresql://user:password@localhost:5432/mydb'

Connection Types
----------------

Airflow supports many connection types including:

- **HTTP**: For HTTP/HTTPS connections
- **PostgreSQL**: For PostgreSQL databases
- **MySQL**: For MySQL databases  
- **S3**: For Amazon S3
- **Google Cloud**: For GCP services
- **Slack**: For Slack notifications

Using Connections in Hooks
--------------------------

Connections are typically used via Hooks:

.. code-block:: python

    from airflow.hooks.postgres_hook import PostgresHook

    hook = PostgresHook(postgres_conn_id='my_postgres_conn')
    records = hook.get_records('SELECT * FROM my_table')

Custom Connection Types
-----------------------

You can create custom connection types by subclassing ``BaseHook`` and defining a ``conn_type`` property.

Testing Connections
-------------------

From Airflow 2.7+, you can test connections directly from the UI by clicking the **Test** button on the connection form.
