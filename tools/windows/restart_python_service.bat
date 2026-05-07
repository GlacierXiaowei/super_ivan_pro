@echo off
setlocal

set "RELEASE_ROOT=%~dp0"
set "PACKAGED_SERVICE_SCRIPT=%RELEASE_ROOT%data\flutter_assets\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"
set "PARENT_PACKAGED_SERVICE_SCRIPT=%RELEASE_ROOT%..\data\flutter_assets\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"
set "TOOL_PACKAGED_SERVICE_SCRIPT=%RELEASE_ROOT%..\..\data\flutter_assets\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"

if exist "%PACKAGED_SERVICE_SCRIPT%" (
  set "DESKTOP_SERVICE_SCRIPT=%PACKAGED_SERVICE_SCRIPT%"
  goto service_found
)

if exist "%PARENT_PACKAGED_SERVICE_SCRIPT%" (
  set "DESKTOP_SERVICE_SCRIPT=%PARENT_PACKAGED_SERVICE_SCRIPT%"
  goto service_found
)

if exist "%TOOL_PACKAGED_SERVICE_SCRIPT%" (
  set "DESKTOP_SERVICE_SCRIPT=%TOOL_PACKAGED_SERVICE_SCRIPT%"
  goto service_found
)

pushd "%~dp0..\.." >nul 2>nul
if not errorlevel 1 (
  set "REPO_ROOT=%CD%"
  popd >nul
)

if "%REPO_ROOT%"=="" (
  set "SERVICE_SCRIPT=%~dp0..\..\build\windows\x64\runner\Release\data\flutter_assets\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"
  set "SOURCE_SERVICE_SCRIPT=%~dp0..\..\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"
) else (
  set "SERVICE_SCRIPT=%REPO_ROOT%\build\windows\x64\runner\Release\data\flutter_assets\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"
  set "SOURCE_SERVICE_SCRIPT=%REPO_ROOT%\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"
)

if exist "%SERVICE_SCRIPT%" (
  set "DESKTOP_SERVICE_SCRIPT=%SERVICE_SCRIPT%"
) else if exist "%SOURCE_SERVICE_SCRIPT%" (
  set "DESKTOP_SERVICE_SCRIPT=%SOURCE_SERVICE_SCRIPT%"
) else (
  echo desktop_service.py not found.
  echo Searched paths:
  echo   %PACKAGED_SERVICE_SCRIPT%
  echo   %PARENT_PACKAGED_SERVICE_SCRIPT%
  echo   %TOOL_PACKAGED_SERVICE_SCRIPT%
  echo   %SERVICE_SCRIPT%
  echo   %SOURCE_SERVICE_SCRIPT%
  set "EXIT_CODE=1"
  goto finish
)

:service_found
set "PYTHON_EXE="
set "PYTHON_ARGS_PREFIX="
if not "%SUPER_IVAN_DESKTOP_PYTHON%"=="" set "PYTHON_EXE=%SUPER_IVAN_DESKTOP_PYTHON%"
if "%PYTHON_EXE%"=="" where python >nul 2>nul && set "PYTHON_EXE=python"
if "%PYTHON_EXE%"=="" where py >nul 2>nul && set "PYTHON_EXE=py" && set "PYTHON_ARGS_PREFIX=-3"

if "%PYTHON_EXE%"=="" (
  echo Python was not found.
  echo Please install Python 3 and make sure python or py is available in PATH.
  set "EXIT_CODE=1"
  goto finish
)

echo Restarting Super Ivan Python desktop service on 127.0.0.1:18090...
echo Using desktop_service.py:
echo   %DESKTOP_SERVICE_SCRIPT%
echo Using python executable:
echo   %PYTHON_EXE%
if not "%PYTHON_ARGS_PREFIX%"=="" echo Python args prefix: %PYTHON_ARGS_PREFIX%

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$serviceScript=$env:DESKTOP_SERVICE_SCRIPT;" ^
  "$pythonExe=$env:PYTHON_EXE;" ^
  "$pythonArgsPrefix=$env:PYTHON_ARGS_PREFIX;" ^
  "if (-not (Test-Path -LiteralPath $serviceScript)) { throw ('desktop_service.py not found: ' + $serviceScript) }" ^
  "$versionArgs=@(); if ($pythonArgsPrefix) { $versionArgs += $pythonArgsPrefix }; $versionArgs += '--version';" ^
  "try { & $pythonExe @versionArgs | Out-Host; if ($LASTEXITCODE -ne 0) { throw ('Python exited with code ' + $LASTEXITCODE) } } catch { throw ('Python 3 is required. Install Python or set SUPER_IVAN_DESKTOP_PYTHON. ' + $_.Exception.Message) }" ^
  "$statusBefore=$null;" ^
  "try { $statusBefore=Invoke-RestMethod -Uri 'http://127.0.0.1:18090/status' -Method Get -TimeoutSec 2 } catch { }" ^
  "if ($statusBefore -and [bool]$statusBefore.armed) { Write-Host 'armed=true detected. Disarming before restart to avoid accidental sending.'; try { $statusBefore=Invoke-RestMethod -Uri 'http://127.0.0.1:18090/arm-state' -Method Post -ContentType 'application/json' -Body '{\"enabled\":false}' -TimeoutSec 8 } catch { throw ('Failed to disarm before restart: ' + $_.Exception.Message) } }" ^
  "if ($statusBefore) { try { Invoke-RestMethod -Uri 'http://127.0.0.1:18090/services/stop' -Method Post -ContentType 'application/json' -Body '{}' -TimeoutSec 8 | Out-Null } catch { Write-Warning $_.Exception.Message } }" ^
  "$conn=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 18090 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1;" ^
  "if ($conn) { $proc=Get-CimInstance Win32_Process -Filter ('ProcessId=' + $conn.OwningProcess); if ($proc.CommandLine -notmatch 'desktop_service.py') { throw ('Port 18090 is not desktop_service.py: ' + $proc.CommandLine) }; Stop-Process -Id $conn.OwningProcess -Force }" ^
  "$deadline=(Get-Date).AddSeconds(15);" ^
  "do { Start-Sleep -Milliseconds 200; $still=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 18090 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1; if ($still) { $stillProc=Get-CimInstance Win32_Process -Filter ('ProcessId=' + $still.OwningProcess) -ErrorAction SilentlyContinue; if ($stillProc -and $stillProc.CommandLine -notmatch 'desktop_service.py') { throw ('Port 18090 is not desktop_service.py: ' + $stillProc.CommandLine) }; Stop-Process -Id $still.OwningProcess -Force -ErrorAction SilentlyContinue } } while ($still -and (Get-Date) -lt $deadline);" ^
  "if ($still) { throw 'Port 18090 did not stop.' }" ^
  "$serviceArgs=@(); if ($pythonArgsPrefix) { $serviceArgs += $pythonArgsPrefix }; $serviceArgs += @($serviceScript,'--host','127.0.0.1','--port','18090');" ^
  "Start-Process -FilePath $pythonExe -ArgumentList $serviceArgs -WindowStyle Hidden;" ^
  "$deadline=(Get-Date).AddSeconds(10); $statusAfter=$null;" ^
  "do { Start-Sleep -Milliseconds 200; try { $statusAfter=Invoke-RestMethod -Uri 'http://127.0.0.1:18090/status' -Method Get -TimeoutSec 2 } catch { $statusAfter=$null } } while (-not $statusAfter -and (Get-Date) -lt $deadline);" ^
  "if (-not $statusAfter) { throw 'desktop service did not become available.' }" ^
  "if ([bool]$statusAfter.armed) { Write-Host 'armed=true after wrapper restart. Disarming before managed service start.'; $statusAfter=Invoke-RestMethod -Uri 'http://127.0.0.1:18090/arm-state' -Method Post -ContentType 'application/json' -Body '{\"enabled\":false}' -TimeoutSec 8 }" ^
  "if ($statusBefore -and $statusBefore.service_state -eq 'running') { $statusAfter=Invoke-RestMethod -Uri 'http://127.0.0.1:18090/services/start' -Method Post -ContentType 'application/json' -Body '{}' -TimeoutSec 20 }" ^
  "Write-Host ('service_state=' + $statusAfter.service_state);" ^
  "Write-Host ('watcher_state=' + $statusAfter.watcher_state);" ^
  "Write-Host ('watcher_error=' + $statusAfter.watcher_error);" ^
  "Write-Host ('armed=' + $statusAfter.armed);" ^
  "Write-Host ('mode=' + $statusAfter.mode);"

if errorlevel 1 (
  echo Failed to restart Python desktop service.
  set "EXIT_CODE=1"
  goto finish
)

echo Python desktop service restarted.
set "EXIT_CODE=0"

:finish
echo.
echo Press any key to close this window...
pause >nul
exit /b %EXIT_CODE%
