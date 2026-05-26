# 02 - Airflow DAG Runtime and dbt Readiness

## Session Focus
This note captures what we learned while validating the Dockerized Airflow runtime and preparing it to orchestrate dbt for UrbanFlow.

The goal was not to build the full production DAG yet. The goal was to prove the platform can run a simple DAG, then prove the Airflow container can run dbt and connect to Snowflake.

---

## Big Picture
Airflow is an orchestration tool.

It does not replace dbt, Snowflake, or Python scripts. Instead, it coordinates when those tools should run and in what order.

For UrbanFlow, the intended role is:

```text
Airflow = orchestrator
dbt = transformation tool
Snowflake = warehouse
Docker Compose = local runtime environment
```

Today we validated this path:

```text
Docker Compose
  -> Airflow webserver and scheduler
  -> DAG discovery
  -> task execution
  -> dbt runtime inside Airflow container
  -> Snowflake connection
```

---

## DAG Mental Model
A DAG is a workflow definition.

In Airflow, a DAG is usually a Python file placed inside the `dags/` folder.

For UrbanFlow:

```text
D:\Project_UrbanFlow\dags
```

is mounted into the Airflow containers as:

```text
/opt/airflow/dags
```

So when we create a file on the laptop:

```text
dags/urbanflow_smoke_test_dag.py
```

Airflow sees it inside the container at:

```text
/opt/airflow/dags/urbanflow_smoke_test_dag.py
```

Important lesson:

```text
The DAG file defines the workflow.
The Airflow scheduler reads the DAG file and decides when tasks should run.
The Airflow UI shows DAGs, runs, task status, and logs.
```

---

## Task Mental Model
A task is one unit of work inside a DAG.

In today's smoke test, the DAG had one task:

```text
print_runtime_message
```

The task did not transform data. It only printed a message and listed the DAG folder contents.

That was intentional. The first DAG should be small because we were testing the Airflow runtime, not business logic.

The smoke test answered:

```text
Can Airflow discover a DAG file?
Can the scheduler parse it?
Can Airflow run a task?
Can we see the run status in the UI?
Can we inspect logs?
```

Once all of those were true, we knew the platform was ready for a more useful DAG.

---

## Operator Mental Model
An operator defines what kind of work a task performs.

Common examples:

```text
BashOperator     -> run a shell command
PythonOperator   -> run Python code
EmptyOperator    -> placeholder task
```

Today we used `BashOperator`.

Reason:

```text
dbt commands are CLI commands.
BashOperator is the simplest way to run CLI commands from Airflow.
```

For example, this kind of task:

```python
BashOperator(
    task_id="dbt_debug",
    bash_command="cd /opt/airflow/dbt/urbanflow && dbt debug",
)
```

means:

```text
Inside the Airflow container, go to the dbt project folder and run dbt debug.
```

---

## The Smoke Test DAG
The smoke test DAG used this shape:

```python
from datetime import datetime

from airflow import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id="urbanflow_smoke_test",
    description="Minimal DAG to verify the UrbanFlow Airflow runtime",
    start_date=datetime(2026, 5, 26),
    schedule=None,
    catchup=False,
    tags=["urbanflow", "smoke-test"],
) as dag:
    print_runtime_message = BashOperator(
        task_id="print_runtime_message",
        bash_command=(
            'echo "UrbanFlow Airflow smoke test passed"; '
            'echo "Current container time: $(date)"; '
            'echo "DAG folder contents:"; '
            "ls -la /opt/airflow/dags"
        ),
    )
```

### `dag_id`

```python
dag_id="urbanflow_smoke_test"
```

This is the name shown in the Airflow UI.

### `start_date`

```python
start_date=datetime(2026, 5, 26)
```

This tells Airflow when the DAG becomes eligible to run.

For manual smoke tests, this only needs to be a fixed date in the past or present.

### `schedule=None`

```python
schedule=None
```

This means:

```text
Do not run automatically on a schedule.
Only run when manually triggered.
```

This is useful for smoke tests.

### `catchup=False`

```python
catchup=False
```

This tells Airflow not to create old missed scheduled runs.

For manual and learning DAGs, this keeps behavior simple.

### `tags`

```python
tags=["urbanflow", "smoke-test"]
```

Tags help organize and filter DAGs in the Airflow UI.

---

## Reading the Airflow UI Result
The smoke test result showed:

```text
Total Runs Displayed: 1
Total success: 1
Total Tasks: 1
BashOperator: 1
```

Meaning:

```text
Airflow saw the DAG.
The DAG was triggered once.
The run succeeded.
The DAG had one task.
That task used BashOperator.
```

This validated the Airflow runtime before we moved to dbt.

---

## Manual Container Command vs Airflow Task
We ran dbt manually inside the scheduler container with:

```powershell
docker compose exec airflow-scheduler bash -lc "cd /opt/airflow/dbt/urbanflow && dbt debug"
```

Breakdown:

```text
docker compose exec airflow-scheduler
```

Run a command inside the already-running `airflow-scheduler` container.

```text
bash -lc "..."
```

Run the command through a Linux shell inside the container.

```text
cd /opt/airflow/dbt/urbanflow
```

Move to the dbt project directory inside the container.

```text
dbt debug
```

Ask dbt to validate project config, profile config, dependencies, and warehouse connection.

Important distinction:

```text
Manual docker compose exec = human runs a command inside the container.
Airflow BashOperator = Airflow runs a command inside a task.
```

The manual command is a readiness check before creating the Airflow dbt DAG.

---

## Why the First dbt Debug Failed
The first `dbt debug` result was mixed.

Working parts:

```text
profiles.yml file [OK found and valid]
dbt_project.yml file [OK found and valid]
Connection test: [OK connection ok]
```

Failed part:

```text
git [ERROR]
Could not find command: "git"
```

Meaning:

```text
dbt could find the UrbanFlow project.
dbt could find the Snowflake profile.
dbt could connect to Snowflake.
But the container did not include the git CLI.
```

The key lesson:

```text
Your laptop tools and container tools are separate.
If Airflow runs dbt inside a container, the container must contain everything dbt needs.
```

Even if we are not actively using Git branches, dbt checks for Git because dbt may need Git for package and project workflows.

---

## Dockerfile Update for Git
The Dockerfile was updated to install Git:

```dockerfile
FROM apache/airflow:2.10.0-python3.12

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
```

Important ideas:

```text
USER root
```

Temporarily switch to the Linux root user because installing system packages requires elevated permissions.

```text
apt-get install git
```

Install the Git command-line tool into the image.

```text
USER airflow
```

Switch back to the normal Airflow user after system package installation.

Airflow should not run as root in normal operation.

```text
pip install -r requirements.txt
```

Install Python dependencies after the system-level setup.

Important distinction:

```text
apt-get installs operating system packages.
pip installs Python packages.
```

Git is an operating system command, so it belongs in `apt-get`, not `requirements.txt`.

---

## Final dbt Debug Result
After rebuilding the image and restarting the stack, `dbt debug` passed:

```text
profiles.yml file [OK found and valid]
dbt_project.yml file [OK found and valid]
git [OK found]
Connection test: [OK connection ok]
All checks passed!
```

Meaning:

```text
The Airflow container has dbt installed.
The Airflow container can see the mounted dbt project.
The Airflow container can read the dbt profile.
The Airflow container has Git installed.
The Airflow container can connect to Snowflake.
```

This is the readiness point we needed before building a dbt DAG.

---

## Next Learning Step
The next DAG should be a dbt smoke test DAG:

```text
urbanflow_dbt_smoke_test
```

Suggested task order:

```text
dbt_debug -> dbt_ls
```

Meaning:

```text
First prove dbt can validate the environment.
Then list dbt project resources.
Only run dbt_ls if dbt_debug succeeds.
```

In Airflow code, task order would be written as:

```python
dbt_debug >> dbt_ls
```

This is the bridge from:

```text
manual dbt check
```

to:

```text
Airflow-orchestrated dbt workflow
```

---

## Overall UrbanFlow Orchestration Direction
Once the dbt smoke DAG succeeds, the first real UrbanFlow orchestration DAG can follow this high-level flow:

```text
start
  -> dbt_debug
  -> dbt_seed
  -> dbt_run_silver
  -> dbt_run_gold
  -> dbt_test
  -> end
```

This flow is intentionally staged.

Reason:

```text
Run environment validation first.
Load/update seeds before models that depend on seeds.
Build silver models before gold models.
Run tests after models are built.
```

Airflow's value is making this order explicit, visible, repeatable, and observable.

---

## Key Takeaways
*   Start with a tiny DAG before building a full orchestration workflow.
*   A successful DAG run proves more than Python syntax; it proves scheduler, task execution, metadata tracking, and UI visibility.
*   Airflow tasks run inside the container environment, not directly on the laptop.
*   If dbt runs inside Airflow, dbt dependencies must exist inside the Airflow image.
*   `dbt debug` is a good readiness check before orchestrating dbt.
*   `BashOperator` is a practical starting point for running dbt CLI commands from Airflow.
*   The next logical proof is `dbt_debug -> dbt_ls` as an Airflow DAG.
