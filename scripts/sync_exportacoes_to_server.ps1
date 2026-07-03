$ErrorActionPreference = "Stop"

param(
    [string]$Source = "C:\exportacoes",
    [Parameter(Mandatory = $true)]
    [string]$Destination
)

if (-not (Test-Path -LiteralPath $Source)) {
    throw "Pasta de origem nao encontrada: $Source"
}

if (-not (Test-Path -LiteralPath $Destination)) {
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
}

$LogDir = Join-Path (Resolve-Path (Join-Path $PSScriptRoot "..")) "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogPath = Join-Path $LogDir "sync-exportacoes-$Timestamp.log"

robocopy $Source $Destination /E /XO /FFT /R:3 /W:5 /NP /LOG:$LogPath
$ExitCode = $LASTEXITCODE

if ($ExitCode -ge 8) {
    throw "Falha ao copiar exportacoes para o servidor. Codigo robocopy: $ExitCode. Log: $LogPath"
}

Write-Host "Copia concluida."
Write-Host "Origem: $Source"
Write-Host "Destino: $Destination"
Write-Host "Log: $LogPath"
