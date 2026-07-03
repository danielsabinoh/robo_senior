@echo off
setlocal

cd /d "%~dp0\.."

echo Use scripts\install_f141cis_task.ps1 com -ServerDestination para criar a tarefa completa.
echo Exemplo:
echo powershell -ExecutionPolicy Bypass -File scripts\install_f141cis_task.ps1 -ServerDestination "\\srv-banco\Compartilhado\exportacoes"
exit /b 1
