@echo off
setlocal

for %%I in ("%~dp0..\..") do set "REPO_ROOT=%%~fI"
set "SERVICE_SCRIPT=%REPO_ROOT%\build\windows\x64\runner\Release\data\flutter_assets\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"
set "SOURCE_SERVICE_SCRIPT=%REPO_ROOT%\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation\scripts\desktop_service.py"
set "PYTHON_EXE=python"
if not "%SUPER_IVAN_DESKTOP_PYTHON%"=="" set "PYTHON_EXE=%SUPER_IVAN_DESKTOP_PYTHON%"

echo Restarting Super Ivan Python desktop service on 127.0.0.1:18090...

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$serviceScript=$env:SERVICE_SCRIPT;" ^
  "if (-not (Test-Path -LiteralPath $serviceScript)) { $serviceScript=$env:SOURCE_SERVICE_SCRIPT }" ^
  "if (-not (Test-Path -LiteralPath $serviceScript)) { throw 'desktop_service.py not found. Build Windows first or check repo path.' }" ^
  "$statusBefore=$null;" ^
  "try { $statusBefore=Invoke-RestMethod -Uri 'http://127.0.0.1:18090/status' -Method Get -TimeoutSec 2 } catch { }" ^
  "if ($statusBefore -and [bool]$statusBefore.armed) { throw 'Refusing to restart because armed=true. Disarm in the app first.' }" ^
  "if ($statusBefore) { try { Invoke-RestMethod -Uri 'http://127.0.0.1:18090/services/stop' -Method Post -ContentType 'application/json' -Body '{}' -TimeoutSec 8 | Out-Null } catch { Write-Warning $_.Exception.Message } }" ^
  "$conn=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 18090 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1;" ^
  "if ($conn) { $proc=Get-CimInstance Win32_Process -Filter ('ProcessId=' + $conn.OwningProcess); if ($proc.CommandLine -notmatch 'desktop_service.py') { throw ('Port 18090 is not desktop_service.py: ' + $proc.CommandLine) }; Stop-Process -Id $conn.OwningProcess -Force }" ^
  "$deadline=(Get-Date).AddSeconds(5);" ^
  "do { Start-Sleep -Milliseconds 100; $still=Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort 18090 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 } while ($still -and (Get-Date) -lt $deadline);" ^
  "if ($still) { throw 'Port 18090 did not stop.' }" ^
  "Start-Process -FilePath $env:PYTHON_EXE -ArgumentList @($serviceScript,'--host','127.0.0.1','--port','18090') -WindowStyle Hidden;" ^
  "$deadline=(Get-Date).AddSeconds(10); $statusAfter=$null;" ^
  "do { Start-Sleep -Milliseconds 200; try { $statusAfter=Invoke-RestMethod -Uri 'http://127.0.0.1:18090/status' -Method Get -TimeoutSec 2 } catch { $statusAfter=$null } } while (-not $statusAfter -and (Get-Date) -lt $deadline);" ^
  "if (-not $statusAfter) { throw 'desktop service did not become available.' }" ^
  "if ([bool]$statusAfter.armed) { throw 'Refusing to start managed services because armed=true after wrapper restart.' }" ^
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
