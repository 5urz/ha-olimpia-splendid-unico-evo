@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" helper.py
) else (
  py -3 helper.py
)
if errorlevel 1 (
  echo.
  echo Start fehlgeschlagen. Python 3 mit Tkinter wird benoetigt.
  echo Bitte LIESMICH.md lesen. Dieses Fenster enthaelt keine Geraeteschluessel.
  pause
)
