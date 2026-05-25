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

This matters because Docker can mark a container as running before the service inside the container is ready to accept real work.

For Postgres:

```text
container started = Postgres process has begun
service ready = Postgres can accept database connections
```

Airflow needs Postgres to be ready because it must read and write metadata such as DAG runs, task states, users, connections, variables, and scheduler state.

There are two readiness levels:

```text
1. Postgres readiness = database can accept connections
2. Airflow metadata readiness = Airflow tables and admin user are prepared
```

---

## Additional Compose Keywords Learned

### `depends_on:`

`depends_on` defines the startup relationship between services.

Basic form:

```yaml
depends_on:
  - postgres
```

Meaning:

```text
Start postgres before this service.
```

Stronger health-based form:

```yaml
depends_on:
  postgres:
    condition: service_healthy
```

Meaning:

```text
Start this service only after postgres passes its healthcheck.
```

For webserver and scheduler, we also added:

```yaml
airflow-init:
  condition: service_completed_successfully
```

Meaning:

```text
Start webserver and scheduler only after airflow-init exits successfully.
```

Final intended startup flow:

```text
postgres starts
postgres becomes healthy
airflow-init runs
airflow-init completes successfully
airflow-webserver starts
airflow-scheduler starts
```

### `ports:`

`ports` exposes a container port to the host machine.

Example:

```yaml
ports:
  - "8080:8080"
```

Format:

```text
HOST_PORT:CONTAINER_PORT
```

Meaning:

```text
localhost:8080 on the laptop
goes to port 8080 inside the airflow-webserver container
```

Mental model:

```text
ports = doorway from laptop into container
```

Only `airflow-webserver` needs this because the browser on the laptop needs access to the Airflow UI.

Postgres does not need a host port for this project because Airflow reaches it through Docker's internal network using the service name `postgres`.

### `volumes:`

`volumes` mount files or folders into a container.

Format:

```text
HOST_PATH:CONTAINER_PATH
```

Example:

```yaml
- ./dags:/opt/airflow/dags
```

Meaning:

```text
D:\Project_UrbanFlow\dags on the laptop
appears as
/opt/airflow/dags inside the Airflow container
```

Mental model:

```text
Dockerfile = baked dependencies
volumes = live project files
```

Use the Dockerfile for dependencies that should be installed into the image:

```text
pandas
snowflake connector
dbt packages
python-dotenv
requests
```

Use volumes for files that change frequently during development:

```text
dags
scripts
dbt project
```

Important rule:

```text
Dependency changed -> rebuild image
Code/model/DAG changed -> volume updates live
```

### Named Volume for Postgres

We added:

```yaml
services:
  postgres:
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data

volumes:
  postgres-db-volume:
```

Meaning:

```text
Store Postgres database files in a Docker-managed persistent volume.
```

Mental model:

```text
Container = replaceable machine
Volume = persistent disk
```

This protects Airflow metadata from disappearing when the Postgres container is recreated.

It preserves things like:

```text
Airflow admin user
DAG run history
task states
Airflow connections
Airflow variables
scheduler metadata
```

It does not store UrbanFlow business data. Business data still lives in Snowflake.

### `env_file:`

`env_file` explicitly injects environment variables from a file into the container process environment.

Example:

```yaml
env_file:
  - .env
```

Meaning:

```text
Docker Compose reads .env and injects those key-value pairs into the container.
```

Then Python can read values with:

```python
os.getenv("SNOWFLAKE_USER")
```

Important distinction:

```text
volume-mounted .env = file is visible inside container
env_file = variables are injected into container environment
```

Mounting:

```yaml
- ./.env:/opt/airflow/.env
```

only makes the file available. The code still needs to load it using something like:

```python
load_dotenv("/opt/airflow/.env")
```

Using `env_file` is more explicit for container runtime configuration.

---

## Service Networking

Docker Compose services can communicate by service name.

Airflow connects to Postgres using:

```text
postgresql+psycopg2://airflow:airflow@postgres/airflow
```

The host part is:

```text
postgres
```

That refers to the Compose service name:

```yaml
postgres:
```

Important lesson:

```text
localhost changes meaning depending on where you are standing.
```

From the laptop:

```text
localhost = the laptop
```

From the Airflow container:

```text
localhost = the Airflow container itself
```

So Airflow must use:

```text
postgres
```

not:

```text
localhost
```

to reach the separate Postgres container.

---

## Airflow Init Hardening

Original command:

```bash
airflow db init &&
airflow users create --username admin ...
```

Problem:

```text
After adding a persistent Postgres volume, the admin user may already exist on later runs.
Trying to create the same user again can fail.
```

Better command:

```bash
airflow db migrate &&
(airflow users list | grep -q admin ||
airflow users create --username admin ...)
```

Meaning:

```text
1. Run Airflow database migrations.
2. If migration succeeds, check whether admin exists.
3. If admin exists, skip creation.
4. If admin does not exist, create admin.
```

### `airflow db migrate`

`airflow db migrate` prepares or updates Airflow's metadata database schema.

It makes Postgres contain the internal tables Airflow needs for the current Airflow version.

It does not:

```text
run dbt
load Snowflake
migrate UrbanFlow business data
run DAGs
```

It only manages Airflow's own metadata schema in Postgres.

### `|` vs `||`

Pipe:

```bash
airflow users list | grep -q admin
```

Meaning:

```text
Send the output of the left command into the right command.
```

`||` fallback:

```bash
grep -q admin || airflow users create ...
```

Meaning:

```text
If the left command fails, run the right command.
```

So:

```bash
airflow users list | grep -q admin || airflow users create ...
```

means:

```text
Check if admin exists.
If admin does not exist, create it.
```

Parentheses matter:

```bash
airflow db migrate &&
(airflow users list | grep -q admin || airflow users create ...)
```

This ensures user logic only runs if database migration succeeds.

---

## Current Docker Compose Hardening Completed

Current Compose state:

```text
Postgres metadata persists through a named volume.
Postgres has a readiness healthcheck.
airflow-init waits for healthy Postgres.
webserver and scheduler wait for successful airflow-init.
airflow-init uses airflow db migrate.
admin user creation is safe to rerun.
Airflow services receive project environment variables through env_file.
DAGs, scripts, and dbt project are mounted as live folders.
```

Validation command:

```bash
docker compose config
```

Result:

```text
Compose file is structurally valid.
```

Warning observed:

```text
the attribute `version` is obsolete, it will be ignored
```

Meaning:

```text
version: '3.8' is no longer needed in modern Docker Compose.
It is not breaking anything, but can be removed later for cleanliness.
```

Security note:

```text
docker compose config renders env_file values, including secrets.
Do not share that output publicly.
```

---

## Exact Resume Point

Next session should start from runtime validation:

```text
Run the Dockerized Airflow stack and verify that Airflow starts correctly.
```

Then continue with:

```text
docker compose up
airflow-init completion
webserver startup
scheduler startup
Airflow UI at localhost:8080
```

After runtime validation, continue with:

```text
minimal proof DAG
then UrbanFlow orchestration DAG
```
