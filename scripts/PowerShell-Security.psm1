# PowerShell Repository Security Configuration
# This file defines trusted scripts and security settings for the DNDStoryTelling repository

# Repository root path
$REPO_ROOT = Split-Path -Parent $PSScriptRoot

# Trusted script paths within this repository
$TRUSTED_SCRIPTS = @(
    "scripts\test-docker.ps1"
    "scripts\Deploy-Synology.ps1"
    "scripts\generate-secret-key.py"
    ".powershell-config.ps1"
)

# Function to check if a script is trusted
function Test-TrustedScript {
    param([string]$ScriptPath)

    $relativePath = [System.IO.Path]::GetRelativePath($REPO_ROOT, $ScriptPath)
    return $TRUSTED_SCRIPTS -contains $relativePath
}

# Auto-configure execution policy if not already set
if ((Get-ExecutionPolicy -Scope CurrentUser) -eq 'Restricted') {
    try {
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        Write-Host "✅ PowerShell execution policy configured for repository" -ForegroundColor Green
    } catch {
        Write-Warning "Could not set execution policy. Run as Administrator or set manually."
    }
}

# Export functions for use in other scripts
Export-ModuleMember -Function Test-TrustedScript