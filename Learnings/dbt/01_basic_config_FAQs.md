# dbt Configuration: Basic FAQs & Architectural Intuition
*Date: May 7, 2026*

This document captures the foundational knowledge of dbt configuration established during the recalibration of Project UrbanFlow.

---

### 1. The `dbt_project.yml` (The Brain)
**Q: What is the primary purpose of this file?**
**A:** It is the central configuration file for the entire project. It defines the project name, version, and most importantly, it maps how dbt should treat different folders (e.g., assigning specific schemas to the `silver` or `gold` directories).

**Q: Why must the `profile` name match?**
**A:** The `profile` field in this file acts as a pointer. It tells dbt which set of credentials in your local `profiles.yml` to use. If they don't match, dbt cannot establish a connection to the data warehouse.

---

### 2. The `profiles.yml` (The Handshake)
**Q: What does this file control?**
**A:** It holds the "Secret Handshake" (credentials, account IDs, roles, and warehouses) for Snowflake. It defines **Targets** (like `dev` and `prod`).

**Q: Why do we use Targets like `dev` and `prod`?**
**A:** To ensure **Isolation**. `dev` is a sandbox for testing and breaking code without affecting the "Source of Truth." `prod` is reserved for verified, perfect code that powers business dashboards.

---

### 3. The `sources.yml` (The Map)
**Q: Why use `sources.yml` instead of hardcoding table names in SQL?**
**A:** Two main reasons:
1.  **Resilience**: If the raw data moves to a different database, you only update **one** file (`sources.yml`) instead of searching and replacing strings in dozens of SQL files.
2.  **Lineage**: It allows dbt to build a visual "Family Tree" (DAG), showing exactly where data originates and how it flows through the system.

**Q: What is the `{{ source() }}` function?**
**A:** It is a Jinja function that tells dbt to look up the table's physical location in the `sources.yml` file. This creates a dynamic link rather than a static, brittle one.

---

### 4. The `generate_schema_name.sql` Macro (The Organizer)

{% macro generate_schema_name(custom_schema_name, node) -%}    
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}

**Q: What problem does this macro solve?**
**A:** By default, dbt appends custom schemas to your default schema (e.g., `BRONZE_SILVER`). This macro overrides that behavior to ensure "Clean" and "Professional" schema names (e.g., just `SILVER` or `GOLD`) that match industry standards for Medallion Architecture.

---

### 🎓 Summary of the dbt Workflow
1.  **Profile** says *Who* is connecting.
2.  **Project** says *What* we are building.
3.  **Source** says *Where* the raw data is.
4.  **Target** says *Which* environment we are building in.
5.  **Macro** says *How* the output should be organized.
