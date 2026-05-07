@echo off
setlocal

set "RELEASE_ROOT=%~dp0"
set "PACKAGE_ROOT="
if exist "%RELEASE_ROOT%data\flutter_assets" set "PACKAGE_ROOT=%RELEASE_ROOT%"
if "%PACKAGE_ROOT%"=="" if exist "%RELEASE_ROOT%..\data\flutter_assets" set "PACKAGE_ROOT=%RELEASE_ROOT%..\\"
if "%PACKAGE_ROOT%"=="" if exist "%RELEASE_ROOT%..\..\data\flutter_assets" set "PACKAGE_ROOT=%RELEASE_ROOT%..\\..\\"

if "%PACKAGE_ROOT%"=="" (
  echo Failed to resolve package root from "%~dp0".
  set "EXIT_CODE=1"
  goto finish
)

set "BUNDLED_WECHAT_DECRYPT_ROOT=%PACKAGE_ROOT%runtime\wechat-decrypt"
set "BUNDLED_WECHAT_DECRYPT_MAIN=%BUNDLED_WECHAT_DECRYPT_ROOT%\main.py"
set "CONFIG_PATH=%LOCALAPPDATA%\SuperIvanPro\wechat_automation\config\runtime.local.json"

if not exist "%BUNDLED_WECHAT_DECRYPT_MAIN%" (
  echo Bundled wechat-decrypt not found:
  echo   %BUNDLED_WECHAT_DECRYPT_MAIN%
  set "EXIT_CODE=1"
  goto finish
)

echo Initializing Super Ivan portable runtime config...
echo Package root:
echo   %PACKAGE_ROOT%
echo Bundled wechat-decrypt:
echo   %BUNDLED_WECHAT_DECRYPT_ROOT%

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$configPath=$env:CONFIG_PATH;" ^
  "$configDir=Split-Path -Parent $configPath;" ^
  "$bundledRoot=$env:BUNDLED_WECHAT_DECRYPT_ROOT;" ^
  "New-Item -ItemType Directory -Force -Path $configDir | Out-Null;" ^
  "$payload=@{};" ^
  "if (Test-Path -LiteralPath $configPath) { $loaded=Get-Content -LiteralPath $configPath -Raw -Encoding UTF8 | ConvertFrom-Json; if ($loaded -is [pscustomobject]) { foreach ($property in $loaded.PSObject.Properties) { $payload[$property.Name]=$property.Value } } }" ^
  "$payload.wechat_decrypt_root=$bundledRoot;" ^
  "$payload.watcher_url='http://127.0.0.1:5678';" ^
  "if (-not $payload.ContainsKey('sender_backend') -or [string]::IsNullOrWhiteSpace([string]$payload.sender_backend)) { $payload.sender_backend='current_chat' }" ^
  "if (-not $payload.ContainsKey('dry_run')) { $payload.dry_run=$false }" ^
  "$json=$payload | ConvertTo-Json -Depth 8;" ^
  "$utf8NoBom=New-Object System.Text.UTF8Encoding($false);" ^
  "[System.IO.File]::WriteAllText($configPath, $json, $utf8NoBom);" ^
  "Write-Host ('runtime.local.json=' + $configPath);"

if errorlevel 1 (
  echo Failed to initialize portable runtime config.
  set "EXIT_CODE=1"
  goto finish
)

echo Portable runtime config initialized.
set "EXIT_CODE=0"

:finish
echo.
echo Press any key to close this window...
pause >nul
exit /b %EXIT_CODE%
