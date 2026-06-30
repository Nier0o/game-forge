<#
.SYNOPSIS
    Optional Docker Compose smoke check for the Game Forge stack.

.DESCRIPTION
    Brings up the full Compose stack with Godot export disabled
    (SKIP_GODOT_EXPORT=true) and verifies that every long-running service
    answers its health endpoint, that MinIO is live, and that the Mongo
    container is running. This is intentionally SEPARATE from the per-service
    unit/integration suites (`npm test` / `pytest`) and is NOT part of the
    default test command. It does not exercise live LLMs, Stability AI, or a
    real Godot HTML5 export.

.NOTES
    Requires Docker + Docker Compose. Run from the `game-forge/` directory.
    Image builds on a cold cache can take several minutes.

.EXAMPLE
    pwsh ./scripts/docker-smoke-check.ps1
    pwsh ./scripts/docker-smoke-check.ps1 -KeepUp   # leave the stack running
#>
param(
    [switch]$KeepUp,
    [int]$TimeoutSeconds = 180
)

$ErrorActionPreference = 'Stop'
$composeDir = Split-Path -Parent $PSScriptRoot
Set-Location $composeDir

# Godot export is the slow, environment-sensitive step; skip it for smoke checks.
$env:SKIP_GODOT_EXPORT = 'true'

$healthTargets = @(
    @{ Name = 'backend'; Url = 'http://localhost:5000/api/health' },
    @{ Name = 'server';  Url = 'http://localhost:6100/health' },
    @{ Name = 'planner'; Url = 'http://localhost:6101/health' },
    @{ Name = 'asset';   Url = 'http://localhost:6102/health' },
    @{ Name = 'code';    Url = 'http://localhost:6103/health' },
    @{ Name = 'builder'; Url = 'http://localhost:6104/health' },
    @{ Name = 'minio';   Url = 'http://localhost:9000/minio/health/live' }
)

function Test-Endpoint {
    param([string]$Url, [int]$Retries = 30, [int]$DelaySeconds = 5)
    for ($i = 0; $i -lt $Retries; $i++) {
        try {
            $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
            if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 300) { return $true }
        } catch {
            Start-Sleep -Seconds $DelaySeconds
        }
    }
    return $false
}

$failed = @()
try {
    Write-Host '== Building and starting the stack (SKIP_GODOT_EXPORT=true) ==' -ForegroundColor Cyan
    docker compose up -d --build

    Write-Host '== Probing health endpoints ==' -ForegroundColor Cyan
    $retries = [Math]::Max(1, [int]($TimeoutSeconds / 5))
    foreach ($t in $healthTargets) {
        if (Test-Endpoint -Url $t.Url -Retries $retries) {
            Write-Host ("  OK   {0,-8} {1}" -f $t.Name, $t.Url) -ForegroundColor Green
        } else {
            Write-Host ("  FAIL {0,-8} {1}" -f $t.Name, $t.Url) -ForegroundColor Red
            $failed += $t.Name
        }
    }

    Write-Host '== Checking Mongo container ==' -ForegroundColor Cyan
    $mongoState = (docker inspect -f '{{.State.Running}}' game-forge-mongo) 2>$null
    if ($mongoState -eq 'true') {
        Write-Host '  OK   mongo    container running' -ForegroundColor Green
    } else {
        Write-Host '  FAIL mongo    container not running' -ForegroundColor Red
        $failed += 'mongo'
    }
}
finally {
    if (-not $KeepUp) {
        Write-Host '== Tearing down ==' -ForegroundColor Cyan
        docker compose down
    } else {
        Write-Host '== Leaving stack up (-KeepUp). Run `docker compose down` when done. ==' -ForegroundColor Yellow
    }
}

if ($failed.Count -gt 0) {
    Write-Host ("SMOKE CHECK FAILED: {0}" -f ($failed -join ', ')) -ForegroundColor Red
    exit 1
}
Write-Host 'SMOKE CHECK PASSED: all services healthy.' -ForegroundColor Green
