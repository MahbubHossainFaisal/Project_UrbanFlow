# Project UrbanFlow

## Project Setup & Commands Used

Below is a list of the unique commands that have been used to initialize and set up this project, along with an explanation of how they work.

### 1. Python Environment Setup (using `uv`)

We use [`uv`](https://github.com/astral-sh/uv) to manage our Python virtual environment and dependencies because of its speed.

*   `pip install uv`
    *   **Explanation**: Installs the `uv` package manager globally.
*   `uv venv --python 3.12`
    *   **Explanation**: Creates an isolated Python virtual environment (stored in the `.venv` folder) specifically using Python 3.12. This ensures our project dependencies do not conflict with other Python projects on the system.
*   `.venv\Scripts\activate`
    *   **Explanation**: Activates the virtual environment in PowerShell. Once activated, any `python` or `pip` commands will run within this isolated environment.
*   `uv add requirements.txt`
    *   **Explanation**: Uses `uv` to quickly resolve and install the project dependencies listed in the `requirements.txt` file (like `dbt-snowflake`).

### 2. dbt (Data Build Tool) Initialization

*   `dbt init urbanflow`
    *   **Explanation**: Initializes a new dbt project folder named `urbanflow`. It creates the necessary directory structure (models, macros, tests) and configuration files (`dbt_project.yml`, `profiles.yml`) needed to build data transformations.

### 3. Custom dbt Wrapper (Environment Variable Management)

By default, dbt does not automatically read `.env` files. To keep our Snowflake credentials secure and out of version control, we use a custom PowerShell script (`run_dbt.ps1`) to inject `.env` variables before running dbt.

*   `.\run_dbt.ps1 debug`
    *   **Explanation**: Runs our custom PowerShell script. The script reads the `.env` file, sets the contents as temporary environment variables in the terminal, changes the directory to `dbt\urbanflow`, and then executes `python -m dbt debug --profiles-dir .` to test the connection to Snowflake.
*   `function dbt { D:\Project_UrbanFlow\run_dbt.ps1 $args }`
    *   **Explanation**: Creates a PowerShell alias (function) named `dbt`. It intercepts any standard `dbt` command you type and redirects it to the `run_dbt.ps1` wrapper script. This allows you to use standard dbt syntax seamlessly while still loading the `.env` variables under the hood.
*   `dbt debug`
    *   **Explanation**: Because of the custom function above, typing `dbt debug` now automatically executes the wrapper. It verifies that dbt can successfully connect to the Snowflake data warehouse using the credentials mapped in `profiles.yml` via the loaded environment variables.
