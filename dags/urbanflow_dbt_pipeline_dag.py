from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator


DBT_PROJECT_DIR = "/opt/airflow/dbt/urbanflow"
DEFAULT_TASK_ARGS = {
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="urbanflow_dbt_pipeline",
    description="Run the UrbanFlow dbt seed, model, and test pipeline",
    start_date=datetime(2026, 5, 27),
    schedule=None,
    catchup=False,
    default_args=DEFAULT_TASK_ARGS,
    max_active_runs=1,
    tags=["urbanflow", "dbt", "pipeline"],
) as dag:
    start = EmptyOperator(task_id="start")

    dbt_debug = BashOperator(
        task_id="dbt_debug",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt debug",
        execution_timeout=timedelta(minutes=10),
    )

    dbt_seed = BashOperator(
        task_id="dbt_seed",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt seed",
        execution_timeout=timedelta(minutes=15),
    )

    dbt_run_silver = BashOperator(
        task_id="dbt_run_silver",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --select path:models/silver",
        execution_timeout=timedelta(minutes=60),
    )

    dbt_run_gold = BashOperator(
        task_id="dbt_run_gold",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt run --select path:models/gold",
        execution_timeout=timedelta(minutes=60),
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {DBT_PROJECT_DIR} && dbt test",
        execution_timeout=timedelta(minutes=30),
    )

    end = EmptyOperator(task_id="end")

    start >> dbt_debug >> dbt_seed >> dbt_run_silver >> dbt_run_gold >> dbt_test >> end
