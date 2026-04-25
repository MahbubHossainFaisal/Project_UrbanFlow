# Snowflake Role-Based Access Control (RBAC)

## ACCOUNTADMIN (Account Administrator)

> [!IMPORTANT]
> The "Super User" of the account. It encapsulates the powers of both `SYSADMIN` and `SECURITYADMIN` and adds top-level administrative privileges.

**Primary Function**: To manage billing, global account settings, and data sharing.

### Key Capabilities

**What it does:**
- Can view credit usage and set up billing.
- Manage resource monitors (to cut off compute if you spend too much).
- Configure network policies (like IP allowlisting).
- Set up cloud storage integrations.
- Manage Snowflake Data Sharing.

**What it cannot do:** 
- Nothing. It is the highest level of access.

> [!TIP]
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