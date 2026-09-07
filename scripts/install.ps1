<#
One-shot installer (PowerShell)
Symlink all `skills/` and `agents/` to user-level dirs, mirroring `scripts/install.sh`.

Usage:
  powershell -ExecutionPolicy Bypass -File scripts/install.ps1        # install
  powershell -ExecutionPolicy Bypass -File scripts/install.ps1 --unlink
  powershell -ExecutionPolicy Bypass -File scripts/install.ps1 --skills-only
  powershell -ExecutionPolicy Bypass -File scripts/install.ps1 --agents-only
  powershell -ExecutionPolicy Bypass -File scripts/install.ps1 --help

# Environment variables that override defaults:
#   CLAUDE_SKILLS_DIR or OPENCLAUDE_SKILLS_DIR
#   OPENCLAUDE_AGENTS_DIR
#>

param()

function Write-Info { param($m) Write-Host $m }
function Write-Err  { param($m) Write-Error $m }

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir "..") ).ProviderPath
$ScriptsDir = Join-Path $RepoRoot "scripts"

# Initialize git submodules if .gitmodules exists and looks unpopulated
if (Test-Path (Join-Path $RepoRoot ".gitmodules")) {
    try {
        $status = & git -C $RepoRoot submodule status --recursive 2>$null
        if ($LASTEXITCODE -ne 0 -or $status -match '^-') {
            Write-Info "--- initializing git submodules ---"
            & git -C $RepoRoot submodule update --init --recursive
            Write-Info ""
        }
    } catch {
        # ignore git errors
    }
}

$do_skills = $true
$do_agents = $true
$mode = 'link'

function Show-Usage {
    Get-Content -Path $PSScriptRoot\..\README.md -ErrorAction SilentlyContinue | Select-Object -First 12
    Write-Host "`nUsage:`n  powershell -File scripts/install.ps1 [--unlink|--skills-only|--agents-only|--help]"
    exit 0
}

# Simple args parser
for ($i = 0; $i -lt $args.Count; $i++) {
    switch ($args[$i]) {
        '--help' { Show-Usage }
        '-h'     { Show-Usage }
        '--unlink' { $mode = 'unlink' }
        '--skills-only' { $do_agents = $false }
        '--agents-only' { $do_skills = $false }
        default { Write-Err "unknown arg: $($args[$i])"; exit 2 }
    }
}

Write-Info "=== skills_of_plant_simulation installer ==="
Write-Info "repo : $RepoRoot"
Write-Info "mode : $mode"; Write-Info ""

function Pick-SkillsTarget {
    if ($env:CLAUDE_SKILLS_DIR) { return $env:CLAUDE_SKILLS_DIR }
    if ($env:OPENCLAUDE_SKILLS_DIR) { return $env:OPENCLAUDE_SKILLS_DIR }
    # Prefer ~/.openclaude/skills when OpenClaude is present, otherwise
    # fall back to ~/.claude/skills for Claude Code compatibility.
    $openCandidate = Join-Path $env:USERPROFILE ".openclaude"
    if (Test-Path $openCandidate) { return (Join-Path $openCandidate "skills") }
    return (Join-Path $env:USERPROFILE ".claude\skills")
}

function Pick-AgentsTarget {
    if ($env:OPENCLAUDE_AGENTS_DIR) { return $env:OPENCLAUDE_AGENTS_DIR }
    $candidate = Join-Path $env:USERPROFILE ".openclaude"
    if (Test-Path $candidate) { return (Join-Path $candidate "agents") }
    return (Join-Path $env:USERPROFILE ".claude\agents")
}

function Is-Symlink($path) {
    if (-not (Test-Path $path -PathType Any)) { return $false }
    try {
        $item = Get-Item -LiteralPath $path -Force
        return ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    } catch { return $false }
}

function Link-Skills {
    $SKILLS_SRC = Join-Path $RepoRoot 'skills'
    if (-not (Test-Path $SKILLS_SRC)) { Write-Err "ERR: $SKILLS_SRC does not exist"; exit 1 }
    $TARGET_DIR = Pick-SkillsTarget
    New-Item -ItemType Directory -Path $TARGET_DIR -Force | Out-Null
    Write-Info "target dir: $TARGET_DIR"

    $modeLocal = $mode

    Get-ChildItem -LiteralPath $SKILLS_SRC -Directory -Force | ForEach-Object {
        $name = $_.Name
        $src = $_.FullName
        $target = Join-Path $TARGET_DIR $name
        if ($modeLocal -eq 'unlink') {
            if (Is-Symlink $target) {
                Remove-Item -LiteralPath $target -Force
                Write-Info "unlinked: $target"
            } elseif (Test-Path $target) {
                Write-Info "skip (not a symlink, refusing to delete real dir): $target"
            } else {
                Write-Info "skip (not present): $target"
            }
        } else {
            if (-not (Test-Path $src -PathType Container)) { Write-Info "skip (not a dir): $src"; return }
            if ((Test-Path $target -PathType Any) -or (Is-Symlink $target)) {
                Write-Info "skip (exists): $target"
            } else {
                try {
                    New-Item -ItemType SymbolicLink -Path $target -Target $src | Out-Null
                    Write-Info "linked: $target -> $src"
                } catch {
                    Write-Err "failed to link: $target -> $src ($($_.Exception.Message))"
                }
            }
        }
    }

    Write-Info "`n done. mode=$modeLocal, target=$TARGET_DIR"
}

function Link-Agents {
    $AGENTS_SRC = Join-Path $RepoRoot 'agents'
    if (-not (Test-Path $AGENTS_SRC)) { Write-Err "ERR: $AGENTS_SRC does not exist"; exit 1 }
    $TARGET_DIR = Pick-AgentsTarget
    New-Item -ItemType Directory -Path $TARGET_DIR -Force | Out-Null
    Write-Info "target dir: $TARGET_DIR"

    $modeLocal = $mode

    Get-ChildItem -LiteralPath $AGENTS_SRC -File -Filter *.md -Force | ForEach-Object {
        if ($_.Name -eq 'README.md') { return }
        $name = $_.Name
        $src = $_.FullName
        $target = Join-Path $TARGET_DIR $name
        if ($modeLocal -eq 'unlink') {
            if (Is-Symlink $target) {
                Remove-Item -LiteralPath $target -Force
                Write-Info "unlinked: $target"
            } elseif (Test-Path $target) {
                Write-Info "skip (not a symlink, refusing to delete real file): $target"
            } else {
                Write-Info "skip (not present): $target"
            }
        } else {
            if (-not (Test-Path $src -PathType Leaf)) { Write-Info "skip (not a file): $src"; return }
            if ((Test-Path $target -PathType Any) -or (Is-Symlink $target)) {
                Write-Info "skip (exists): $target"
            } else {
                try {
                    New-Item -ItemType SymbolicLink -Path $target -Target $src | Out-Null
                    Write-Info "linked: $target -> $src"
                } catch {
                    Write-Err "failed to link: $target -> $src ($($_.Exception.Message))"
                }
            }
        }
    }

    Write-Info "`n done. mode=$modeLocal, target=$TARGET_DIR"
}

if ($do_skills) {
    Write-Info "--- skills ---"
    Link-Skills
    Write-Info ""
}

if ($do_agents) {
    Write-Info "--- agents ---"
    Link-Agents
    Write-Info ""
}

Write-Info "=== done ==="
Write-Info "verify:" 
Write-Info "  ls -la \"${env:OPENCLAUDE_AGENTS_DIR:-$($env:USERPROFILE)\\.openclaude\\agents}\" | Select-String plant-simulation"
Write-Info "  ls -la \"${env:OPENCLAUDE_SKILLS_DIR:-$($env:USERPROFILE)\\.claude\\skills}\" | Select-String local-simtalk"
