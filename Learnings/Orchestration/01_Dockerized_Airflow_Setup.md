# 01 - Dockerized Airflow Setup

## Session Focus
This note captures the first foundation lesson for Sprint 5.2: understanding why the UrbanFlow project needs a `Dockerfile` and a `docker-compose.yml` for Airflow orchestration.

The goal was not to memorize syntax. The goal was to understand why each piece exists.

---

## Core Mental Model

```text
Dockerfile = recipe for building one custom image
docker-compose.yml = blueprint for running multiple containers/services together
```

For UrbanFlow:

```text
Dockerfile builds the custom Airflow environment.
docker-compose.yml runs Airflow + Postgres as a local orchestration platform.
```

Compose is not combining multiple images into one image. It starts multiple separate containers and wires them together through configuration, networking, ports, volumes, and environment variables.

---

## Dockerfile Understanding

Current `Dockerfile`:

```dockerfile
FROM apache/airflow:2.10.0-python3.12

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt
```

### `FROM apache/airflow:2.10.0-python3.12`

Start from the official Airflow image.

This means we are not building Airflow from zero. We are extending an existing Airflow runtime.

### `COPY requirements.txt .`

Copy the project dependency list into the image build context.

The `.` means the current working directory inside the image.

### `RUN pip install --no-cache-dir -r requirements.txt`

Install UrbanFlow's Python dependencies inside the image.

This matters because Airflow tasks run inside the Airflow container, not directly on the laptop.

Important lesson:

```text
If Airflow runs the task inside a container,
the required Python packages must exist inside that container.
```

Final image mental model:

```text
Base Airflow image
        +
UrbanFlow Python requirements
        =
Custom UrbanFlow Airflow image
```

Both `airflow-webserver` and `airflow-scheduler` should use this custom image because both parse DAG files, and the scheduler also executes task logic.

---

## Why Docker Compose Exists Here

Airflow is not just one process. To work locally as a platform, it needs several capabilities:

```text
Need memory        -> postgres
Need setup         -> airflow-init
Need UI/control    -> airflow-webserver
Need decisioning   -> airflow-scheduler
```

So our Compose file defines multiple services:

```text
postgres
airflow-init
airflow-webserver
airflow-scheduler
```

Vocabulary:

```text
service = blueprint entry inside docker-compose.yml
container = running instance created from that service
```

---

## Airflow Services: Why They Exist

### `postgres`

Postgres is Airflow's metadata database.

It stores Airflow operational memory:

```text
DAG run history
task instance state
success / failed / skipped status
retry counts
scheduled run timestamps
manual trigger records
Airflow users
Airflow connections
Airflow variables
metadata needed by scheduler and UI
```

Important distinction:

```text
DAG files store the workflow definition.
Postgres stores runtime state and metadata.
```

Postgres is not the UrbanFlow business warehouse. UrbanFlow business data lives in Snowflake.

### `airflow-init`

`airflow-init` is a one-time setup service.

It prepares the Airflow metadata database and creates the Airflow UI admin user.

It does jobs like:

```text
1. Create or migrate Airflow metadata tables in Postgres.
2. Create the Airflow admin user for UI login.
3. Exit.
```

It does not run DAGs, schedule tasks, load Snowflake, or run dbt.

Mental model:

```text
airflow-init = installer
```

### `airflow-webserver`

The webserver is the Airflow UI.

It lets humans:

```text
see DAGs
trigger DAGs manually
pause / unpause DAGs
inspect task status
inspect logs
manage Airflow UI interaction
```

Mental model:

```text
airflow-webserver = face / control room
```

### `airflow-scheduler`

The scheduler is the Airflow decision engine.

It reads DAG files and decides:

```text
Is it time to create a DAG run?
Which task is ready now?
Did the upstream task succeed?
Should the failed task retry?
Should downstream tasks wait?
```

The scheduler does not create DAG code. The engineer writes DAGs inside the `dags/` folder.

Mental model:

```text
airflow-scheduler = brain / decision engine
```

---

## Important Correction Learned

`airflow-init` creates the Airflow UI admin user, not the Postgres database user.

Postgres user/password/database are configured in the `postgres` service:

```yaml
environment:
  - POSTGRES_USER=airflow
  - POSTGRES_PASSWORD=airflow
  - POSTGRES_DB=airflow
```

Airflow UI admin user is created by:

```bash
airflow users create --username admin --password admin
```

So:

```text
Postgres user/password = database login used by Airflow services
Airflow admin user/password = UI login used by the human user
```

---

## Compose Keywords Covered So Far

### `services:`

The main section listing the container roles Compose should manage.

Example:

```yaml
services:
  postgres:
  airflow-webserver:
  airflow-scheduler:
  airflow-init:
```

Plain English:

```text
Here are the containers/services I want Docker Compose to run.
```

### `image: postgres:13`

Use an existing prebuilt image from Docker Hub.

Postgres uses this because no project-specific customization is needed.

### `build: .`

Build a custom image using the `Dockerfile` in the current project directory.

Airflow services use this because UrbanFlow dependencies must be installed into the Airflow image.

### `environment:`

Pass runtime configuration values into a container.

For Postgres:

```yaml
POSTGRES_USER=airflow
POSTGRES_PASSWORD=airflow
POSTGRES_DB=airflow
```

These create the initial database user, password, and database.

Airflow then consumes those values through its SQLAlchemy connection string:

```text
postgresql+psycopg2://airflow:airflow@postgres/airflow
```

Breakdown:

```text
postgresql+psycopg2:// USER : PASSWORD @ HOST / DATABASE
postgresql+psycopg2:// airflow : airflow @ postgres / airflow
```

Important lesson:

```text
One service provides something.
Another service consumes it using matching configuration.
```

Here:

```text
Postgres provides a metadata database.
Airflow consumes that metadata database.
```

If the password in Postgres and the password in Airflow's connection string do not match, Airflow will fail to connect.

### `healthcheck:`

Checks whether a container is healthy and ready.

For Postgres:

```yaml
healthcheck:
  test: ["CMD-SHELL", "pg_isready -U airflow"]
  interval: 10s
  timeout: 5s
  retries: 5
```

Meaning:

```text
Run pg_isready with user airflow.
Check every 10 seconds.
Each check must finish within 5 seconds.
After 5 failed checks, mark the service unhealthy.
```

Key distinction:

```text
Container started != service ready
```

This is where the session stopped.

---

## Exact Resume Point

Next session should start from this question:

```text
Why is "Postgres container started" not the same as "Postgres is ready to accept Airflow connections"?
```

Then continue with:

```text
healthcheck
depends_on
ports
volumes
Airflow environment variables
service-to-service networking
```

After the compose file is understood line by line, continue to hardening:

```text
persistent Postgres volume
health-based startup dependency
cleaner Airflow init behavior
credential handling strategy
```
