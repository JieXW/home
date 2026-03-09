param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsFromCmd
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonScript = Join-Path $scriptDir "apply_site_data.py"

if (-not (Test-Path -LiteralPath $pythonScript)) {
    Write-Host "apply_site_data.py not found." -ForegroundColor Red
    exit 1
}

$sourceArg = $null
if ($ArgsFromCmd.Count -gt 0 -and $ArgsFromCmd[0]) {
    $sourceArg = $ArgsFromCmd[0]
}

if ($sourceArg) {
    Write-Host ("Using source file: " + $sourceArg)
    & python $pythonScript $sourceArg
} else {
    Write-Host "No source file specified. Auto-detecting latest site-data*.js ..."
    & python $pythonScript
}

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Generation failed." -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "Updated site-data.js and indexnew2.html"
