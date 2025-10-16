from airflow import DAG
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from datetime import datetime

with DAG(
    dag_id="test_spark_connection_fixed2",
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
) as dag:

    SparkSubmitOperator(
        task_id='spark_test',
        application='/opt/airflow/spark_jobs/test.py',
        conn_id='spark_no_master',
        verbose=True,
    )
