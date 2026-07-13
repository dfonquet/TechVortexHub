$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$siteRoot = Split-Path -Parent $scriptDir
$nodeScript = Join-Path $scriptDir "update-lab-metrics.js"
$bundledNode = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue

if ($nodeCommand) {
  & $nodeCommand.Source $nodeScript
  exit $LASTEXITCODE
}

if (Test-Path $bundledNode) {
  & $bundledNode $nodeScript
  exit $LASTEXITCODE
}

throw "Node.js was not found. Install Node.js or run this script from Codex with the bundled runtime available."
