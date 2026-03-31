$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PycacheDir = Join-Path $ProjectRoot ".cache\pycache"

if (-not (Test-Path $PycacheDir)) {
    New-Item -Path $PycacheDir -ItemType Directory -Force | Out-Null
}

$env:PYTHONPYCACHEPREFIX = $PycacheDir

python (Join-Path $ProjectRoot "src\agent_core\main.py")
