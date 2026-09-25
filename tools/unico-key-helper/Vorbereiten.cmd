@echo off
setlocal
cd /d "%~dp0"
echo Erstellt eine lokale Python-Umgebung und laedt Frida von PyPI.
echo Android, OS Home und der UNICO werden dabei nicht veraendert.
pause
py -3 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
echo Fertig. Jetzt Start.cmd oeffnen.
pause
exit /b 0
:failed
echo Vorbereitung fehlgeschlagen. Siehe LIESMICH.md. Keine App neu installieren oder zuruecksetzen.
pause
exit /b 1
