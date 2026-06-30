$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $ProjectRoot

python -m PyInstaller --version *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller nao esta instalado."
    Write-Host 'Instale com: pip install pyinstaller'
    exit 1
}

python -m PyInstaller `
    --onefile `
    --console `
    --name seniorbot `
    seniorbot\__main__.py

python -m PyInstaller `
    --onefile `
    --console `
    --name seniorbot-f141cis `
    seniorbot\f141cis_app.py

Write-Host ""
Write-Host "Executaveis gerados em:"
Write-Host (Join-Path $ProjectRoot "dist\seniorbot.exe")
Write-Host (Join-Path $ProjectRoot "dist\seniorbot-f141cis.exe")
