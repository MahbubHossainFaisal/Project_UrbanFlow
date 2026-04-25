# Snowflake Role-Based Access Control (RBAC)

In Snowflake's Role-Based Access Control (RBAC) model, the built-in system roles are structured in a strict hierarchy. To understand the difference, it helps to divide them by their primary responsibilities: **Data/Compute Objects** vs. **Access/Security** vs. **Account/Billing**.

Here is the breakdown of the three top-level roles:

## 1. SYSADMIN (System Administrator)

> [!NOTE]
> The master of the "Data and Compute" layer. If a task involves creating, altering, or dropping structural objects (like databases or virtual warehouses), it belongs here.

**Primary Function**: To manage compute resources (Warehouses) and data storage structures (Databases, Schemas).

- **What it does**: Creates and manages databases, schemas, tables, views, and virtual warehouses.
- **What it cannot do**: It cannot create new users or roles, grant permissions, view billing/credit usage, or manage account-level security policies.

> [!TIP]
> **Best Practice**: Every custom role you create for a project should eventually be granted to `SYSADMIN` (as shown in the previous script). This ensures that a system administrator can still manage the tables and objects created by your project roles.

---

## 2. SECURITYADMIN (Security Administrator)

> [!NOTE]
> The master of the "Access" layer. If a task involves managing who is allowed to see or do what, it belongs here.

**Primary Function**: To manage grants, access privileges, and user/role creation.

- **What it does**: It can grant or revoke any privilege to any role or user across the entire Snowflake account globally. It also inherits the privileges of the `USERADMIN` role, meaning it can create, alter, and drop users and roles.
- **What it cannot do**: By default, it does not have the ability to look inside the data tables or create new databases/warehouses (unless it is explicitly granted those rights).

> [!TIP]
> **Best Practice**: Use this role (or `USERADMIN`) to run `GRANT` statements and manage the security hierarchy, keeping security management separate from data management.

---

## 3. ACCOUNTADMIN (Account Administrator)

> [!IMPORTANT]
> The "Super User" of the account. It encapsulates the powers of both `SYSADMIN` and `SECURITYADMIN` and adds top-level administrative privileges.

**Primary Function**: To manage billing, global account settings, and data sharing.

- **What it does**: Can view credit usage, set up billing, manage resource monitors (to cut off compute if you spend too much), configure network policies (like IP allowlisting), set up cloud storage integrations, and manage Snowflake Data Sharing.
- **What it cannot do**: Nothing. It is the highest level of access.

> [!WARNING]
> **Best Practice**: This role should be heavily restricted to a very small number of trusted administrators. It should *never* be used to create standard project tables, views, or run daily ETL pipelines.

---

## Quick Comparison Table

| Feature / Capability | SYSADMIN | SECURITYADMIN | ACCOUNTADMIN |
| :--- | :--- | :--- | :--- |
| **Hierarchy Level** | High | High | Maximum (Super User) |
| **Create/Drop Databases & Warehouses** | ✅ Yes | ❌ No | ✅ Yes |
| **Create/Drop Users & Roles** | ❌ No | ✅ Yes | ✅ Yes |
| **Grant Privileges Globally** | ❌ No | ✅ Yes | ✅ Yes |
| **View Billing & Credit Usage** | ❌ No | ❌ No | ✅ Yes |
| **Manage Account Integrations** | ❌ No | ❌ No | ✅ Yes |