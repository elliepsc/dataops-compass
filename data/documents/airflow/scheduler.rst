Scheduler
=========

The Airflow scheduler monitors all DAGs and tasks, triggers task instances when their dependencies are met, and manages the executor.

How the Scheduler Works
-----------------------

1. The scheduler reads DAG files from the DAG directory
2. It stores DAG structure in the metadata database
3. It checks for DAGs that need to be run based on their schedule
4. It submits tasks to the executor when dependencies are satisfied
5. It monitors running tasks and updates their state

Schedule Intervals
------------------

DAGs can be scheduled using:

**Cron expressions**

.. code-block:: python

    dag = DAG(
        'my_dag',
        schedule='0 12 * * *',  # Every day at noon
    )

**Preset schedules**

.. code-block:: python

    dag = DAG(
        'my_dag',
        schedule='@daily',   # Once a day at midnight
        # Other presets: @hourly, @weekly, @monthly, @yearly, @once
    )

**Timedelta objects**

.. code-block:: python

    from datetime import timedelta

    dag = DAG(
        'my_dag',
        schedule=timedelta(hours=6),  # Every 6 hours
    )

**Dataset-driven scheduling**

.. code-block:: python

    from airflow.datasets import Dataset

    my_dataset = Dataset('s3://my-bucket/my-file.csv')

    dag = DAG(
        'my_dag',
        schedule=[my_dataset],  # Triggered when dataset is updated
    )

Catchup and Backfill
--------------------

**Catchup**: When enabled, the scheduler creates DAG runs for all intervals between ``start_date`` and now.

.. code-block:: python

    dag = DAG(
        'my_dag',
        start_date=datetime(2024, 1, 1),
        catchup=False,  # Disable catchup
    )

**Backfill**: Manually trigger historical runs via CLI:

.. code-block:: bash

    airflow dags backfill \
        --start-date 2024-01-01 \
        --end-date 2024-01-31 \
        my_dag

Scheduler Configuration
-----------------------

Key scheduler settings in ``airflow.cfg``:

.. code-block:: ini

    [scheduler]
    # How often to check for new DAGs (seconds)
    dag_dir_list_interval = 300
    
    # Number of threads to parse DAGs
    parsing_processes = 2
    
    # Minimum time between DAG runs (seconds)
    min_file_process_interval = 30

High Availability
-----------------

From Airflow 2.0+, multiple schedulers can run simultaneously for high availability:

.. code-block:: bash

    # Start multiple scheduler instances
    airflow scheduler

Each scheduler uses database-level locking to avoid duplicate task scheduling.
