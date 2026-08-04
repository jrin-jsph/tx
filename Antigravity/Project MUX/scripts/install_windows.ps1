# MUX Windows PowerShell Installation Script
$ErrorActionPreference = "Stop"

Write-Host "Installing MUX on Windows..." -ForegroundColor Cyan
python -m pip install --upgrade pip
python -m pip install -e .

Write-Host "Checking installation..." -ForegroundColor Cyan
python -m mux status
