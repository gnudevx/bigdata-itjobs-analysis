from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Đảm bảo Airflow có thể import module crawler
sys.path.append('/opt/airflow/crawler')

# Import hàm chính từ script crawl_topcv.py
from Code.crawl_topcv import run_topcv_crawler

# Cấu hình mặc định cho DAG
default_args = {
    'owner': 'ducdung',
    'depends_on_past': False,
    'email': ['alert@example.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=10),
}

# Định nghĩa DAG
with DAG(
    dag_id='crawler_dag31',
    default_args=default_args,
    description='Crawl TopCV jobs automatically every day',
    schedule='@daily',  
    start_date=datetime(2025, 10, 1),
    catchup=False,
    tags=['crawler', 'topcv'],
) as dag:

    crawl_topcv_task = PythonOperator(
        task_id='crawl_topcv',
        python_callable=run_topcv_crawler
    )

    crawl_topcv_task
