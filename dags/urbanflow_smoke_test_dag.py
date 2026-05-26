from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="urbanflow_smoke_test",
    description="Minimal DAG to verify the UrbanFlow Airflow runtime",
    start_date=datetime(2026,5,26),
    schedule=None,
    catchup=False,
    tags=["urbanflow","smoke-test"]
) as dag:
    print_runtime_message = BashOperator(
        task_id="print_runtime_message",
        bash_command=(
            'echo "UrbanFlow Airflow smoke test passed"; '
            'echo "Current container time: $(date)"; '
            'echo "DAG folder contents:"; '
            "ls -la /opt/airflow/dags"
        )
    )