@echo off
call "%~dp0tools\windows\restart_python_service.bat"
exit /b %ERRORLEVEL%
