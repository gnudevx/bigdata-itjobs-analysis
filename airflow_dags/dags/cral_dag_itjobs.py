from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import sys
import os

# Đảm bảo Airflow có thể import module crawler
sys.path.append('/opt/airflow/crawler')

# Import hàm chính từ script crawl_topcv.py
from Code.modules.topcv_crawler import run_topcv_crawler
from Code.modules.vnwork_crawler import run_vnwork_crawler
from Code.modules.merge_results import merge_crawl_results

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
    dag_id='crawler_data_itjobs1',
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

    crawl_vnwork_task = PythonOperator(
        task_id='crawl_vnwork',
        python_callable=run_vnwork_crawler
    )

    merge_task = PythonOperator(
        task_id='merge_results',
        python_callable=merge_crawl_results
    )

    [crawl_topcv_task >> crawl_vnwork_task] >> merge_task # (bước này là tui lấy dữ liệu về xong rồi đưa vào merge) -> sau đấy là mấy bước xử lí sau ....
    
