@echo off
cd /d "%~dp0"
echo Fazendo backup do Firestore...
python backup-firestore.py
echo.
pause
