param(
  [string]$ReleaseDir = (Join-Path $PSScriptRoot '..\..\build\windows\x64\runner\Release'),
  [string]$OutputDir = (Join-Path $PSScriptRoot '..\..\dist\SuperIvanPro-Windows-Portable'),
  [string]$WechatDecryptRoot = '',
  [switch]$CreateZip
)

$ErrorActionPreference = 'Stop'

function Resolve-AbsolutePath {
  param([string]$PathValue)
  return [System.IO.Path]::GetFullPath($PathValue)
}

function Copy-DirectoryContents {
  param(
    [string]$SourceDir,
    [string]$DestinationDir
  )

  New-Item -ItemType Directory -Force -Path $DestinationDir | Out-Null
  Copy-Item -Path (Join-Path $SourceDir '*') -Destination $DestinationDir -Recurse -Force
}

function Write-WrapperBat {
  param(
    [string]$TargetPath,
    [string]$RelativeScript
  )

  $content = @(
    '@echo off',
    ('call "%~dp0{0}"' -f $RelativeScript),
    'exit /b %ERRORLEVEL%'
  ) -join "`r`n"
  Set-Content -LiteralPath $TargetPath -Value $content -Encoding ASCII
}

function New-UnicodeName {
  param(
    [int[]]$CodePoints,
    [string]$Suffix
  )

  return ([string]::Concat(($CodePoints | ForEach-Object { [char]$_ })) + $Suffix)
}

$resolvedReleaseDir = Resolve-AbsolutePath $ReleaseDir
$resolvedOutputDir = Resolve-AbsolutePath $OutputDir

$releaseExe = Join-Path $resolvedReleaseDir 'super_ivan_pro.exe'
if (-not (Test-Path -LiteralPath $releaseExe)) {
  throw "super_ivan_pro.exe not found under release dir: $resolvedReleaseDir"
}

if (Test-Path -LiteralPath $resolvedOutputDir) {
  try {
    Remove-Item -LiteralPath $resolvedOutputDir -Recurse -Force
  } catch {
    $resolvedOutputDir = "$resolvedOutputDir-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
  }
}

New-Item -ItemType Directory -Force -Path $resolvedOutputDir | Out-Null
Copy-DirectoryContents -SourceDir $resolvedReleaseDir -DestinationDir $resolvedOutputDir

$sourceToolsDir = Resolve-AbsolutePath (Join-Path $PSScriptRoot '.')
$targetToolsDir = Join-Path $resolvedOutputDir 'tools\windows'
if (Test-Path -LiteralPath $targetToolsDir) {
  Remove-Item -LiteralPath $targetToolsDir -Recurse -Force
}
Copy-DirectoryContents -SourceDir $sourceToolsDir -DestinationDir $targetToolsDir

if ($WechatDecryptRoot) {
  $resolvedWechatDecryptRoot = Resolve-AbsolutePath $WechatDecryptRoot
  $wechatDecryptMain = Join-Path $resolvedWechatDecryptRoot 'main.py'
  if (-not (Test-Path -LiteralPath $wechatDecryptMain)) {
    throw "main.py not found under WechatDecryptRoot: $resolvedWechatDecryptRoot"
  }

  $targetWechatDecryptRoot = Join-Path $resolvedOutputDir 'runtime\wechat-decrypt'
  if (Test-Path -LiteralPath $targetWechatDecryptRoot) {
    Remove-Item -LiteralPath $targetWechatDecryptRoot -Recurse -Force
  }
  Copy-DirectoryContents -SourceDir $resolvedWechatDecryptRoot -DestinationDir $targetWechatDecryptRoot
}

$initBatName = New-UnicodeName -CodePoints @(0x9996, 0x6B21, 0x521D, 0x59CB, 0x5316) -Suffix '.bat'
$restartBatName = New-UnicodeName -CodePoints @(0x91CD, 0x542F, 0x540E, 0x53F0) -Suffix '.bat'
$rebuildCacheBatName = New-UnicodeName -CodePoints @(0x91CD, 0x5EFA, 0x804A, 0x5929, 0x7F13, 0x5B58) -Suffix '.bat'
$readmeName = New-UnicodeName -CodePoints @(0x4F7F, 0x7528, 0x8BF4, 0x660E) -Suffix '.md'
$portableReadmeAlias = 'README.md'

$existingRootBats = Get-ChildItem -LiteralPath $resolvedOutputDir -Filter '*.bat' -File -ErrorAction SilentlyContinue
foreach ($existingRootBat in $existingRootBats) {
  Remove-Item -LiteralPath $existingRootBat.FullName -Force
}

Write-WrapperBat -TargetPath (Join-Path $resolvedOutputDir $initBatName) -RelativeScript 'tools\windows\init_first_run.bat'
Write-WrapperBat -TargetPath (Join-Path $resolvedOutputDir $restartBatName) -RelativeScript 'tools\windows\restart_python_service.bat'
Write-WrapperBat -TargetPath (Join-Path $resolvedOutputDir $rebuildCacheBatName) -RelativeScript 'tools\windows\build_wechat_cache.bat'

$docsRoot = Resolve-AbsolutePath (Join-Path $PSScriptRoot '..\..\docs')
$docPath = Join-Path $docsRoot 'windows-portable-user-guide.zh-CN.md'
if (Test-Path -LiteralPath $docPath) {
  $portableReadmePath = Join-Path $resolvedOutputDir $readmeName
  Copy-Item -LiteralPath $docPath -Destination $portableReadmePath -Force
  Copy-Item -LiteralPath $docPath -Destination (Join-Path $resolvedOutputDir $portableReadmeAlias) -Force
}

Write-Host "portable_release_dir=$resolvedOutputDir"
Write-Host "release_dir=$resolvedReleaseDir"
Write-Host "bundled_python=False"
Write-Host "system_python_required=True"
Write-Host "bundled_wechat_decrypt=$([bool]$WechatDecryptRoot)"

if ($CreateZip) {
  $zipPath = "$resolvedOutputDir.zip"
  if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
  }

  $tarCommand = Get-Command 'tar.exe' -ErrorAction SilentlyContinue
  if ($tarCommand) {
    $parentDir = Split-Path -Parent $resolvedOutputDir
    $leafDir = Split-Path -Leaf $resolvedOutputDir
    & $tarCommand.Source -a -c -f $zipPath -C $parentDir $leafDir
    if ($LASTEXITCODE -ne 0) {
      throw "tar.exe failed while creating zip archive: $zipPath"
    }
  } else {
    Compress-Archive -Path (Join-Path $resolvedOutputDir '*') -DestinationPath $zipPath
  }

  Write-Host "portable_release_zip=$zipPath"
}
