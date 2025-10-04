
# backend/run-server.ps1
$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python nicht gefunden. Bitte Python 3.10+ installieren und PATH setzen."
  exit 1
}

$here = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $here

if (-Not (Test-Path ".\venv")) {
  python -m venv venv
  Write-Host "Venv erstellt."
}
& .\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt

if (-Not (Test-Path ".\outputs")) { New-Item -ItemType Directory -Path ".\outputs" | Out-Null }
if (-Not (Test-Path ".\outputs\thumbs")) { New-Item -ItemType Directory -Path ".\outputs\thumbs" | Out-Null }

python server.py
