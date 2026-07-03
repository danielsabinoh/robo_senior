param(
    [string]$Source = "C:\exportacoes",
    [Parameter(Mandatory = $true)]
    [string]$Destination,
    [switch]$DeleteSourceAfterCopy
)

$ErrorActionPreference = "Stop"

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

$SourceRoot = (Resolve-Path -LiteralPath $Source).Path.TrimEnd("\")
$DestinationRoot = $Destination.TrimEnd("\")
if ($SourceRoot.Equals($DestinationRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Origem e destino sao iguais. Operacao cancelada para evitar perda de dados."
}

$Copied = 0
$Deleted = 0
$Skipped = 0
$Lines = @()

foreach ($File in Get-ChildItem -LiteralPath $SourceRoot -Recurse -File) {
    $RelativePath = $File.FullName.Substring($SourceRoot.Length).TrimStart("\")
    $DestinationFile = Join-Path $DestinationRoot $RelativePath
    $DestinationDir = Split-Path -Parent $DestinationFile

    if (-not (Test-Path -LiteralPath $DestinationDir)) {
        New-Item -ItemType Directory -Force -Path $DestinationDir | Out-Null
    }

    $ShouldCopy = $true
    if (Test-Path -LiteralPath $DestinationFile) {
        $Existing = Get-Item -LiteralPath $DestinationFile
        $ShouldCopy = ($Existing.Length -ne $File.Length) -or ($Existing.LastWriteTimeUtc -lt $File.LastWriteTimeUtc)
    }

    if ($ShouldCopy) {
        Copy-Item -LiteralPath $File.FullName -Destination $DestinationFile -Force
        $Copied++
        $Lines += "COPIED $RelativePath"
    }
    else {
        $Skipped++
        $Lines += "SKIPPED $RelativePath"
    }

    if ($DeleteSourceAfterCopy) {
        $CopiedFile = Get-Item -LiteralPath $DestinationFile -ErrorAction SilentlyContinue
        if ($null -ne $CopiedFile -and $CopiedFile.Length -eq $File.Length) {
            Remove-Item -LiteralPath $File.FullName -Force
            $Deleted++
            $Lines += "DELETED_SOURCE $RelativePath"
        }
        else {
            throw "Arquivo nao confirmado no destino, origem preservada: $($File.FullName)"
        }
    }
}

$Lines | Set-Content -LiteralPath $LogPath -Encoding UTF8

Write-Host "Copia concluida."
Write-Host "Origem: $Source"
Write-Host "Destino: $Destination"
Write-Host "Copiados: $Copied"
Write-Host "Ignorados: $Skipped"
Write-Host "Apagados da origem: $Deleted"
Write-Host "Log: $LogPath"
