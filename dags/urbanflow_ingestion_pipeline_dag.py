from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator


PROJECT_DIR = "/opt/airflow"
DEFAULT_TASK_ARGS = {
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


with DAG(
    dag_id="urbanflow_ingestion_pipeline",
    description="Run UrbanFlow bronze ingestion jobs, then trigger the dbt pipeline",
    start_date=datetime(2026, 5, 30),
    schedule="0 6 15 * *",
    catchup=False,
    default_args=DEFAULT_TASK_ARGS,
    max_active_runs=1,
    params={
        "taxi_year": "auto",
        "taxi_month": "auto",
    },
    tags=["urbanflow", "ingestion", "bronze"],
) as dag:
    start = EmptyOperator(task_id="start")

    ingest_zone_lookup = BashOperator(
        task_id="ingest_zone_lookup",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m scripts.data_ingestion.ingest_zone_lookup"
        ),
        execution_timeout=timedelta(minutes=15),
    )

    ingest_weather = BashOperator(
        task_id="ingest_weather",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m scripts.data_ingestion.ingest_weather"
        ),
        execution_timeout=timedelta(minutes=30),
    )

    ingest_taxi = BashOperator(
        task_id="ingest_taxi",
        bash_command=(
            f"cd {PROJECT_DIR} && "
            "python -m scripts.data_ingestion.ingestion_taxi_class "
            "--year {{ logical_date.strftime('%Y') if params.taxi_year == 'auto' else params.taxi_year }} "
            "--month {{ logical_date.strftime('%m') if params.taxi_month == 'auto' else params.taxi_month }}"
        ),
        execution_timeout=timedelta(minutes=120),
    )

    trigger_dbt_pipeline = TriggerDagRunOperator(
        task_id="trigger_dbt_pipeline",
        trigger_dag_id="urbanflow_dbt_pipeline",
        conf={"triggered_by": "urbanflow_ingestion_pipeline"},
        wait_for_completion=False,
    )

    end = EmptyOperator(task_id="end")

    start >> ingest_zone_lookup >> ingest_weather >> ingest_taxi >> trigger_dbt_pipeline >> end
