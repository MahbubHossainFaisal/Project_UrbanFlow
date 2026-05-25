# 01 - dbt Basic Configuration and Project Wiring

## Purpose
This note explains the foundational dbt files in UrbanFlow. These files do not define business logic directly; they define how dbt finds the project, connects to Snowflake, installs dependencies, routes models, and organizes outputs.

Files covered:

```text
dbt/urbanflow/dbt_project.yml
dbt/urbanflow/profiles.yml
dbt/urbanflow/packages.yml
dbt/urbanflow/package-lock.yml
dbt/urbanflow/macros/generate_schema_name.sql
```

---

## Core Mental Model

```text
profiles.yml      = who/where dbt connects to
dbt_project.yml   = what dbt project contains and how it should build
packages.yml      = which external dbt packages the project needs
package-lock.yml  = exact resolved package versions
macros/           = reusable dbt logic and project behavior overrides
```

In UrbanFlow:

```text
profiles.yml connects dbt to Snowflake.
dbt_project.yml tells dbt where models, seeds, macros, tests, and snapshots live.
packages.yml adds dbt_utils.
generate_schema_name.sql keeps schemas clean as BRONZE, SILVER, and GOLD.
```

---

## `dbt_project.yml`

Location:

```text
dbt/urbanflow/dbt_project.yml
```

This is the central project configuration file.

Important fields:

```yaml
name: 'urbanflow'
version: '1.0.0'
profile: 'urbanflow'
```

Meaning:

```text
name    = project identity
version = project version metadata
profile = which credentials block dbt should use from profiles.yml
```

The `profile` value must match the top-level key in `profiles.yml`:

```yaml
urbanflow:
```

If these do not match, dbt will not know which Snowflake connection to use.

---

## dbt Folder Paths

Current path configuration:

```yaml
model-paths: ["models"]
analysis-paths: ["analyses"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]
```

Plain English:

```text
models/    = SQL transformations
analyses/  = ad hoc analytical SQL not materialized as models
tests/     = custom singular tests
seeds/     = static CSV reference data
macros/    = reusable Jinja/SQL logic
snapshots/ = slowly changing dimension tracking
```

This is dbt's project map. When dbt runs, it uses these paths to discover project resources.

---

## `clean-targets`

Current config:

```yaml
clean-targets:
  - "target"
  - "dbt_packages"
```

These are folders removed by:

```bash
dbt clean
```

Meaning:

```text
target/       = compiled SQL, run artifacts, manifest files
dbt_packages/ = installed external dbt packages
```

This does not delete Snowflake tables. It cleans local generated artifacts.

---

## Model Schema Routing

Current config:

```yaml
models:
  urbanflow:
    +schema: public

    silver:
      +schema: silver

    gold:
      +schema: gold
```

Mental model:

```text
models/silver/* -> Snowflake SILVER schema
models/gold/*   -> Snowflake GOLD schema
```

The project default is:

```yaml
+schema: public
```

But the important production paths are:

```text
silver
gold
```

This supports the Medallion architecture:

```text
Bronze = raw source tables
Silver = cleaned and enriched dbt models
Gold   = business-ready dimensional models and facts
```

---

## Seed Schema Routing

Current config:

```yaml
seeds:
  urbanflow:
    +schema: silver
```

Meaning:

```text
CSV files in dbt/urbanflow/seeds/ are loaded into the SILVER schema.
```

Why Silver?

Seeds are curated reference data, not raw operational data. In UrbanFlow, seeds such as vendors, rate codes, payment types, and emission factors behave like trusted reference inputs for downstream Gold models.

---

## `profiles.yml`

Location:

```text
dbt/urbanflow/profiles.yml
```

This file tells dbt how to connect to Snowflake.

Important structure:

```yaml
urbanflow:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: ...
      user: ...
      password: ...
      role: ...
      warehouse: ...
      database: URBANFLOW_DB
      schema: BRONZE
      threads: 1
```

Mental model:

```text
profile name = connection family
target       = active environment
outputs      = available environments
dev          = current environment configuration
```

The default target is:

```yaml
target: dev
```

So when we run:

```bash
dbt run
```

dbt uses the `dev` output unless another target is provided.

Important fields:

```text
type      = warehouse adapter, here Snowflake
account   = Snowflake account identifier
user      = Snowflake user
password  = Snowflake password
role      = Snowflake role
warehouse = Snowflake compute warehouse
database  = Snowflake database
schema    = default schema
threads   = parallel model execution count
```

Current default schema is:

```yaml
schema: BRONZE
```

This is the base schema dbt starts from. The custom `generate_schema_name` macro and `+schema` configs then route Silver and Gold models into clean schema names.

Security note:

```text
Plain-text credentials are acceptable for early local learning, but not for production.
Later, move credentials to environment variables, Airflow Connections, or a secrets manager.
```

---

## `packages.yml`

Location:

```text
dbt/urbanflow/packages.yml
```

Current package:

```yaml
packages:
  - package: dbt-labs/dbt_utils
    version: 1.3.3
```

This installs `dbt_utils`, a common utility package.

UrbanFlow uses it for patterns such as:

```text
surrogate keys
cross-database helper macros
reusable dbt utilities
```

Install packages with:

```bash
dbt deps
```

This downloads packages into:

```text
dbt/urbanflow/dbt_packages/
```

---

## `package-lock.yml`

Location:

```text
dbt/urbanflow/package-lock.yml
```

This records the exact package versions resolved by `dbt deps`.

Mental model:

```text
packages.yml     = what package range we ask for
package-lock.yml = exact resolved package version dbt installed
```

This improves repeatability. Another environment can install the same package versions instead of accidentally drifting.

---

## `generate_schema_name.sql`

Location:

```text
dbt/urbanflow/macros/generate_schema_name.sql
```

Current macro:

```sql
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
```

This overrides dbt's default schema naming behavior.

Default dbt behavior often combines:

```text
target.schema + custom schema
```

That can produce names like:

```text
BRONZE_SILVER
BRONZE_GOLD
```

UrbanFlow wants clean Medallion schemas:

```text
BRONZE
SILVER
GOLD
```

So the macro says:

```text
If a model has no custom schema, use target.schema.
If a model has a custom schema, use that exact custom schema.
```

This is why:

```yaml
silver:
  +schema: silver

gold:
  +schema: gold
```

becomes:

```text
SILVER
GOLD
```

instead of:

```text
BRONZE_SILVER
BRONZE_GOLD
```

---

## Common Commands

Run from:

```bash
cd dbt/urbanflow
```

Install packages:

```bash
dbt deps
```

Check Snowflake connection and project config:

```bash
dbt debug
```

List resources:

```bash
dbt ls
```

Build models and tests:

```bash
dbt build
```

Clean local artifacts:

```bash
dbt clean
```

---

## Staff Architect Summary

The basic dbt config files define the operating contract for the transformation layer:

```text
profiles.yml tells dbt how to connect.
dbt_project.yml tells dbt what to build and where resources live.
packages.yml adds external dbt capabilities.
package-lock.yml keeps package installs repeatable.
generate_schema_name.sql keeps Medallion schemas clean.
```

The most important UrbanFlow-specific idea is schema routing:

```text
Raw data starts in BRONZE.
dbt Silver models build into SILVER.
dbt Gold models build into GOLD.
```

This keeps the warehouse understandable, audit-friendly, and aligned with the Medallion architecture.

---

## Next File To Study

Next recommended learning note:

```text
02_Silver_Stage_Taxi_Trips.md
```

That note should focus on the first major Silver model:

```text
dbt/urbanflow/models/silver/stg_taxi_trips.sql
```
