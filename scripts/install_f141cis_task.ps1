param(
    [Parameter(Mandatory = $true)]
    [string]$ServerDestination,
    [string]$LocalExportPath = "C:\exportacoes",
    [string]$TaskTime = "17:00"
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Runner = Join-Path $ProjectRoot "scripts\run_f141cis_daily.ps1"
$LauncherDir = Join-Path $ProjectRoot ".local"
$Launcher = Join-Path $LauncherDir "seniorbot-f141cis-daily.cmd"
$TaskName = "SeniorBot F141CIS diario"

if (-not (Test-Path -LiteralPath $Runner)) {
    throw "Script diario nao encontrado: $Runner"
}

New-Item -ItemType Directory -Force -Path $LauncherDir | Out-Null

@"
@echo off
cd /d "$ProjectRoot"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$Runner" -ServerDestination "$ServerDestination" -LocalExportPath "$LocalExportPath"
"@ | Set-Content -LiteralPath $Launcher -Encoding ASCII

$TaskRun = "`"$Launcher`""

schtasks.exe /Create `
    /TN $TaskName `
    /TR $TaskRun `
    /SC DAILY `
    /ST $TaskTime `
    /F | Out-Null

if ($LASTEXITCODE -ne 0) {
    throw "Nao foi possivel criar a tarefa agendada."
}

Write-Host "Tarefa agendada criada/atualizada: $TaskName"
Write-Host "Horario: $TaskTime"
Write-Host "Destino no servidor: $ServerDestination"
Write-Host "Origem local: $LocalExportPath"
Write-Host "Script diario: $Runner"
Write-Host "Launcher: $Launcher"
