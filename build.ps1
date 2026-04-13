param(
    [switch]$NoPause
)

$ErrorActionPreference = "Continue"
Set-Location -Path $PSScriptRoot

Write-Host "=== Noita Archive Manager Build ===" -ForegroundColor Cyan
$exeName = "NoitaArchiveManager-PlasmaBlue"

if (-not (Test-Path ".\main.py")) {
    Write-Host "[ERROR] main.py not found in current directory." -ForegroundColor Red
    if (-not $NoPause) { pause }
    exit 1
}

$usePyLauncher = $false
$pythonExe = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $usePyLauncher = $true
    $pythonExe = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonExe = "python"
}

if (-not $pythonExe) {
    Write-Host "[ERROR] Python 3 was not detected." -ForegroundColor Red
    if (-not $NoPause) { pause }
    exit 1
}

Write-Host "[1/3] Checking PyInstaller..." -ForegroundColor Yellow
if ($usePyLauncher) {
    & $pythonExe -3 -m pip show pyinstaller 1>$null 2>$null
} else {
    & $pythonExe -m pip show pyinstaller 1>$null 2>$null
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found, installing..." -ForegroundColor Yellow
    if ($usePyLauncher) {
        & $pythonExe -3 -m pip install pyinstaller
    } else {
        & $pythonExe -m pip install pyinstaller
    }
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install PyInstaller." -ForegroundColor Red
        if (-not $NoPause) { pause }
        exit 1
    }
}

Write-Host "[2/3] Building main.py..." -ForegroundColor Yellow
if ($usePyLauncher) {
    & $pythonExe -3 -m PyInstaller --noconfirm --clean --onefile --name $exeName main.py
} else {
    & $pythonExe -m PyInstaller --noconfirm --clean --onefile --name $exeName main.py
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Build failed, see log above." -ForegroundColor Red
    if (-not $NoPause) { pause }
    exit 1
}

$exePath = Join-Path $PSScriptRoot "dist\$exeName.exe"
Write-Host "[3/3] Build completed." -ForegroundColor Green
Write-Host "Output: $exePath" -ForegroundColor Green

if (-not $NoPause) {
    pause
}
