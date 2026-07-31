# Build a standalone Windows executable for the rheology-fit desktop GUI.
#
# Usage (from the repository root):
#   powershell -ExecutionPolicy Bypass -File packaging\build_exe.ps1
#
# Output: dist\rheology-fit-gui\rheology-fit-gui.exe (plus its supporting files
# in the same folder - this is a --onedir build, not a single-file exe, since
# --onefile is noticeably slower to start for a numpy/scipy/pandas/matplotlib
# stack and onedir is easier to debug if a hidden import is missing).

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$venvPython = ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    throw "No .venv found at $venvPython. Create it first: python -m venv .venv; .venv\Scripts\python.exe -m pip install -e .[gui,build]"
}

Write-Host "Ensuring pyinstaller and the [gui] extra are installed..."
& $venvPython -m pip install --quiet -e ".[gui,build]"

Write-Host "Building rheology-fit-gui.exe with PyInstaller..."
& $venvPython -m PyInstaller `
    --name rheology-fit-gui `
    --onedir `
    --windowed `
    --icon "$repoRoot\resources\icon.ico" `
    --collect-all customtkinter `
    --noconfirm `
    --distpath dist `
    --workpath build\pyinstaller `
    --specpath packaging `
    src\rheology_fit\gui.py

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed (exit code $LASTEXITCODE)"
}

Write-Host ""
Write-Host "Build complete: dist\rheology-fit-gui\rheology-fit-gui.exe"
