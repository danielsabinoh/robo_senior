@echo off
setlocal

cd /d "%~dp0\.."

python -m seniorbot f141cis --yes --use-today --delay 0 --serie 036 --cfops 5101 5102 6101 6102 5910 6910
