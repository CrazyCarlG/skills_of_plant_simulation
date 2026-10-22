param(
    [Parameter(Mandatory = $true)]
    [string]$HostName,
    [Parameter(Mandatory = $true)]
    [int]$Port,
    [Parameter(Mandatory = $true)]
    [string]$LogPath,
    [int]$TimeoutSeconds = 480
)

$url = "http://${HostName}:${Port}/health"
$startedAt = Get-Date
$logJob = Start-Job -ArgumentList $LogPath -ScriptBlock {
    param($path)
    while (-not (Test-Path -LiteralPath $path)) {
        Start-Sleep -Milliseconds 250
    }
    Get-Content -LiteralPath $path -Tail 0 -Wait
}
$ready = $false

try {
    while (((Get-Date) - $startedAt).TotalSeconds -lt $TimeoutSeconds) {
        Receive-Job -Job $logJob | ForEach-Object { Write-Host $_ }

        try {
            $health = Invoke-RestMethod -Uri $url -TimeoutSec 2
            if ($health.agent_ready -eq $true) {
                $ready = $true
                break
            }
        }
        catch {
            $health = $null
        }

        $elapsed = [int]((Get-Date) - $startedAt).TotalSeconds
        if ($elapsed -gt 0 -and $elapsed % 10 -lt 2) {
            if ($null -eq $health) {
                Write-Host "[CoPilot] Waiting for /health... (${elapsed}s)"
            }
            else {
                Write-Host "[CoPilot] HTTP is responding; agent is still initializing (${elapsed}s)."
            }
        }
        Start-Sleep -Seconds 2
    }
}
finally {
    Receive-Job -Job $logJob | ForEach-Object { Write-Host $_ }
    Stop-Job -Job $logJob -ErrorAction SilentlyContinue
    Remove-Job -Job $logJob -Force -ErrorAction SilentlyContinue
}

if (-not $ready) {
    Write-Host "[CoPilot] Timed out waiting for agent_ready=true."
    exit 1
}

exit 0