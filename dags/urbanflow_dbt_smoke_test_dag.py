from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id ="urbanflow_dbt_smoke_test",
    description="Smoke test to verify Airflow can run dbt commands",
    start_date= datetime(2026,5,27),
    schedule=None,
    catchup=False,
    tags=["urbanflow","dbt","smoke-test"]
) as dag:
    dbt_debug = BashOperator(
        task_id = "dbt_debug",
        bash_command =(
            "cd /opt/airflow/dbt/urbanflow && "
            "dbt debug"
        ),
    )
    
    dbt_ls = BashOperator(
        task_id = "dbt_ls",
        bash_command = (
            "cd /opt/airflow/dbt/urbanflow && "
            "dbt ls"
        )
    )

    dbt_debug >> dbt_ls