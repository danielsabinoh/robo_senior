param(
    [Parameter(Mandatory = $true)]
    [string]$ServerDestination,
    [string]$LocalExportPath = "C:\exportacoes"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$SyncScript = Join-Path $PSScriptRoot "sync_exportacoes_to_server.ps1"

Set-Location $ProjectRoot

python -m seniorbot f141cis --open-rdp --yes --use-today --delay 0 --serie 036 --cfops 5101 5102 6101 6102 5910 6910
if ($LASTEXITCODE -ne 0) {
    throw "Exportacao F141CIS falhou. Codigo: $LASTEXITCODE"
}

& $SyncScript -Source $LocalExportPath -Destination $ServerDestination -DeleteSourceAfterCopy
