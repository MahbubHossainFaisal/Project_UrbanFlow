# run_dbt.ps1
$envFile = ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^([^=]+)=(.*)$') {
            [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
        }
    }
    Write-Host "Environment variables loaded from $envFile"
} else {
    Write-Warning ".env file not found"
}

# Now run any dbt command, pointing to the project
Set-Location dbt\urbanflow
python -m dbt $args --profiles-dir .