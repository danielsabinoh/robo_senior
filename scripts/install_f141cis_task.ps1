$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$Launcher = Join-Path $ProjectRoot "launchers\seniorbot-f141cis-scheduled.cmd"
$TaskName = "SeniorBot F141CIS diario"
$TaskTime = "17:00"

if (-not (Test-Path $Launcher)) {
    throw "Launcher nao encontrado: $Launcher"
}

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
Write-Host "Launcher: $Launcher"
Write-Host "Pasta de trabalho: $ProjectRoot"
