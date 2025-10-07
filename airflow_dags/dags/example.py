from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'airflow',
    'retries': 5,
    'retry_delay': timedelta(minutes=2)
}

with DAG(
    dag_id='01_example',
    default_args=default_args,
    description='first example DAG',
    start_date=datetime(2025, 10, 3),   
    schedule='@daily',                  
    catchup=False                       
) as dag:
    task1 = BashOperator(
        task_id='first_task',
        bash_command='echo "hello world"'
    )
    task2 = BashOperator(
        task_id='second_task',
        bash_command='echo "task 2 here"')

    task1.set_downstream(task2)
