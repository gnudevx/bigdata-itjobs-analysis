from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import sys, os
os.environ['PYSPARK_PYTHON'] = '/home/airflow/.local/bin/python3'
os.environ['PYSPARK_DRIVER_PYTHON'] = '/home/airflow/.local/bin/python3'
sys.path.extend([
    '/opt/airflow/crawler',
    '/opt/airflow/spark_jobs',
    '/opt/airflow/ml_jobs'
])

# Import module
from Code.modules.topcv_crawler import run_topcv_crawler
from Code.modules.vnwork_crawler import run_vnwork_crawler
from Code.modules.merge_results import merge_crawl_results
from clean_skills_and_features import clean_skills_main
from preprocess import preprocess_main
from train_model import train_main
from evaluate_model import evaluate_main
from incremental_train import incremental_train
from visualize_feature import visualize_main

default_args = {
    'owner': 'ducdung',
    'depends_on_past': False,
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

with DAG(
    dag_id='crawler_data_itjobs_with_ml1',
    default_args=default_args,
    description='Crawl + Clean + ML pipeline for IT jobs',
    schedule=timedelta(days=3),
    start_date=datetime(2025, 10, 1),
    catchup=False,
    tags=['crawler', 'spark', 'ml'],
) as dag:

    crawl_topcv_task = PythonOperator(
        task_id='crawl_topcv',
        python_callable=run_topcv_crawler
    )

    crawl_vnwork_task = PythonOperator(
        task_id='crawl_vnwork',
        python_callable=run_vnwork_crawler
    )

    merge_task = PythonOperator(
        task_id='merge_results',
        python_callable=merge_crawl_results
    )

    clean_task = SparkSubmitOperator(
        task_id='spark_clean',
        application='/opt/airflow/spark_jobs/Code/clean_with_spark.py',
        conn_id='spark_no_master',
        verbose=True,
        conf={
            "spark.master": "spark://hadoop-master:7077",
            "spark.driver.bindAddress": "0.0.0.0",
            "spark.submit.deployMode": "client",
            "spark.pyspark.python": "/usr/bin/python3",
            "spark.pyspark.driver.python": "/usr/bin/python3"
        }
    )

    clean_skills_task = PythonOperator(
        task_id='clean_skills_main',
        python_callable=clean_skills_main
    )

    preprocess_task = PythonOperator(
        task_id='preprocess_for_ml',
        python_callable=preprocess_main
    )

    train_task = PythonOperator(
        task_id='train_salary_model',
        python_callable=train_main
    )

    evaluate_task = PythonOperator(
        task_id='evaluate_model',
        python_callable=evaluate_main
    )

    incremental_train_task = PythonOperator(
        task_id='incremental_train',
        python_callable=incremental_train
    )
    
    visualize_task = PythonOperator(
        task_id='visualize_main',
        python_callable=visualize_main
    )

    # === DAG dependencies ===
    [crawl_topcv_task >> crawl_vnwork_task] >> merge_task >> clean_task \
    >> clean_skills_task >> preprocess_task >> train_task \
    >> evaluate_task >> incremental_train_task >> visualize_task
