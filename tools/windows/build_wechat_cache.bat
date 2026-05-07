@echo off
setlocal

set "RELEASE_ROOT=%~dp0"
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

echo Building WeChat decrypted history cache...
echo Using python executable:
echo   %PYTHON_EXE%
if not "%PYTHON_ARGS_PREFIX%"=="" echo Python args prefix: %PYTHON_ARGS_PREFIX%

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$pythonExe=$env:PYTHON_EXE;" ^
  "$pythonArgsPrefix=$env:PYTHON_ARGS_PREFIX;" ^
  "$versionArgs=@(); if ($pythonArgsPrefix) { $versionArgs += $pythonArgsPrefix }; $versionArgs += '--version';" ^
  "try { & $pythonExe @versionArgs | Out-Host; if ($LASTEXITCODE -ne 0) { throw ('Python exited with code ' + $LASTEXITCODE) } } catch { throw ('Python 3 is required. Install Python or set SUPER_IVAN_DESKTOP_PYTHON. ' + $_.Exception.Message) }" ^
  "$configPath=Join-Path $env:LOCALAPPDATA 'SuperIvanPro\wechat_automation\config\runtime.local.json';" ^
  "if (-not (Test-Path -LiteralPath $configPath)) { throw ('runtime.local.json not found: ' + $configPath) }" ^
  "$config=Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json;" ^
  "$root=[string]$config.wechat_decrypt_root;" ^
  "if (-not $root) { $root=$env:SUPER_IVAN_WECHAT_DECRYPT_ROOT }" ^
  "if (-not $root) { throw 'wechat_decrypt_root is not configured in runtime.local.json.' }" ^
  "$main=Join-Path $root 'main.py';" ^
  "if (-not (Test-Path -LiteralPath $main)) { throw ('main.py not found under wechat_decrypt_root: ' + $root) }" ^
  "Write-Host ('wechat_decrypt_root=' + $root);" ^
  "Push-Location -LiteralPath $root;" ^
  "try { $decryptArgs=@(); if ($pythonArgsPrefix) { $decryptArgs += $pythonArgsPrefix }; $decryptArgs += @('main.py','decrypt'); & $pythonExe @decryptArgs; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE } } finally { Pop-Location }"

if errorlevel 1 (
  echo Failed to build WeChat cache.
  set "EXIT_CODE=1"
  goto finish
)

echo WeChat cache build finished.
set "EXIT_CODE=0"

:finish
echo.
echo Press any key to close this window...
pause >nul
exit /b %EXIT_CODE%
