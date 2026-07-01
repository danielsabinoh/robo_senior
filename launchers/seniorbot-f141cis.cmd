@echo off
setlocal

cd /d "%~dp0\.."

echo SeniorBot - Exportacao F141CIS
echo.
echo Deixe o Senior aberto na tela inicial antes de continuar.
echo.

python -m seniorbot f141cis --serie 036 --cfops 5101 5102 6101 6102 5910 6910

echo.
pause
