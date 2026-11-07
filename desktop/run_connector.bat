@echo off
REM Galvin Crafts desktop connector (Windows)
cd /d "%~dp0coreldraw_connector"
python main.py %*
if errorlevel 1 pause
