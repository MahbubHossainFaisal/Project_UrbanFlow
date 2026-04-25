-- Switch to the recommended role for identity creation
USE ROLE ACCOUNTADMIN;

-- 1. Create the dedicated project role
CREATE OR REPLACE ROLE MAHBUB_DE_ROLE
  COMMENT = 'Dedicated role for URBANFLOW project';

-- 2. Create the dedicated user
-- Note: Replace 'StrongPassword123!' and the default warehouse with your actual values.
CREATE OR REPLACE USER URBANFLOW_USER
  PASSWORD = '[PASSWORD]'
  LOGIN_NAME = '[USER_NAME]'
  DISPLAY_NAME = 'Urbanflow User Account'
  DEFAULT_ROLE = MAHBUB_DE_ROLE
  DEFAULT_WAREHOUSE = compute_wh 
  MUST_CHANGE_PASSWORD = FALSE -- Recommended if a human is logging in for the first time
  COMMENT = 'Service user dedicated to the data engineering project pipeline';

-- Switch to SECURITYADMIN to manage privilege grants
USE ROLE SECURITYADMIN;

-- 3. Assign the new role to the newly created user
GRANT ROLE MAHBUB_DE_ROLE TO USER URBANFLOW_USER;

-- 4. Grant the new role to SYSADMIN (Crucial Best Practice)
-- This ensures that any tables/objects created by this new role can still be managed by your system administrators.
GRANT ROLE MAHBUB_DE_ROLE TO ROLE SYSADMIN;


-- Switch to SYSADMIN to grant access to objects
USE ROLE SYSADMIN;

-- 5. Grant usage on the compute warehouse
GRANT USAGE ON WAREHOUSE compute_wh TO ROLE MAHBUB_DE_ROLE;

-- 6. Grant access to the target database and schema
GRANT USAGE ON DATABASE URBANFLOW TO ROLE MAHBUB_DE_ROLE;
GRANT USAGE ON SCHEMA URBANFLOW.BRONZE TO ROLE MAHBUB_DE_ROLE;
GRANT USAGE ON SCHEMA URBANFLOW.SILVER TO ROLE MAHBUB_DE_ROLE;
GRANT USAGE ON SCHEMA URBANFLOW.GOLD TO ROLE MAHBUB_DE_ROLE;

-- 7. Grant the ability to create new objects (like tables or views) in that schema
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA URBANFLOW.BRONZE TO ROLE MAHBUB_DE_ROLE;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA URBANFLOW.SILVER TO ROLE MAHBUB_DE_ROLE;
GRANT CREATE TABLE, CREATE VIEW ON SCHEMA URBANFLOW.GOLD TO ROLE MAHBUB_DE_ROLE;

-- 8. Grant read/write access to existing tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA URBANFLOW.BRONZE TO ROLE MAHBUB_DE_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA URBANFLOW.SILVER TO ROLE MAHBUB_DE_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA URBANFLOW.GOLD TO ROLE MAHBUB_DE_ROLE;

-- Optional: Ensure future tables created in this schema also get these permissions automatically
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA URBANFLOW.BRONZE TO ROLE MAHBUB_DE_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA URBANFLOW.SILVER TO ROLE MAHBUB_DE_ROLE;
GRANT SELECT, INSERT, UPDATE, DELETE ON FUTURE TABLES IN SCHEMA URBANFLOW.GOLD TO ROLE MAHBUB_DE_ROLE;