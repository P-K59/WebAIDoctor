$ErrorActionPreference = "Stop"

Set-Location -LiteralPath $PSScriptRoot

if (-not (Test-Path -LiteralPath ".\node_modules")) {
    npm.cmd install
}

if (-not (Test-Path -LiteralPath ".\client\dist\index.html")) {
    npm.cmd run build
}

npm.cmd start
