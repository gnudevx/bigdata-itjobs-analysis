from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
import sys, os
# os.environ['PYSPARK_PYTHON'] = '/home/airflow/.local/bin/python3'
# os.environ['PYSPARK_DRIVER_PYTHON'] = '/home/airflow/.local/bin/python3'
sys.path.extend([
    '/opt/airflow/crawler',
    '/opt/airflow/ml_jobs'
])

# Import module
from Code.modules.topcv_crawler import run_topcv_crawler
from Code.modules.vnwork_crawler import run_vnwork_crawler
from Code.modules.merge_results import merge_crawl_results
from Code.clean_skills_and_features import clean_skills_main
from Code.preprocess import preprocess_main
from Code.train_model import train_main
from Code.evaluate_model import evaluate_main
from Code.incremental_train import incremental_train
from Code.visualize_feature import visualize_main

os.environ["HADOOP_USER_NAME"] = "hadoopducdung"
default_args = {
    'owner': 'ducdung',
    'depends_on_past': False,
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}
with DAG(
    dag_id='data_itjobs_pipeline1',
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
        conn_id='spark_no_master',   # Định nghĩa trong Airflow Connections
        verbose=True,
        conf={
            "spark.driver.bindAddress": "0.0.0.0",
            "spark.hadoop.yarn.resourcemanager.address": "ducdung-master:8032",
            "spark.hadoop.yarn.application.classpath": "/usr/local/hadoop/share/hadoop/*/*",
            "spark.yarn.access.hadoopFileSystems": "hdfs://hadoop-master:9000",
        },
        application_args=[],  
        driver_memory='1g',
        executor_memory='1g',
        num_executors=2,
        name='spark_clean_job',
        execution_timeout=timedelta(minutes=30)
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
        python_callable=incremental_train,
        op_kwargs={"execution_date": "{{ ds }}"},
    )
    
    visualize_task = PythonOperator(
        task_id='visualize_main',
        python_callable=visualize_main
    )

    # === DAG dependencies ===
    [crawl_topcv_task >> crawl_vnwork_task] >> merge_task >> clean_task \
    >> clean_skills_task >> preprocess_task >> train_task \
    >> evaluate_task >> incremental_train_task >> visualize_task
