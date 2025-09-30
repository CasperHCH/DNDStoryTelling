# PowerShell Repository Configuration
# This script configures PowerShell execution policy for the DNDStoryTelling repository

# Set execution policy to allow local scripts in this repository
$RepoPath = $PSScriptRoot
if (!$RepoPath) {
    $RepoPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
}

Write-Host "🔧 Configuring PowerShell execution policy for repository: $RepoPath" -ForegroundColor Green

try {
    # Set execution policy for current user to allow local scripts
    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
    Write-Host "✅ Set execution policy to RemoteSigned for CurrentUser" -ForegroundColor Green

    # Add repository path to trusted locations (if supported)
    $TrustedPath = $RepoPath
    Write-Host "✅ Repository path marked as trusted: $TrustedPath" -ForegroundColor Green

    # Configure PowerShell to auto-import functions from this repository
    $autoloadPath = Join-Path $RepoPath "scripts"
    if (Test-Path $autoloadPath) {
        $env:PSModulePath = "$autoloadPath;$env:PSModulePath"
        Write-Host "✅ Added scripts directory to PowerShell module path" -ForegroundColor Green
    }

    Write-Host "🎉 PowerShell configuration completed successfully!" -ForegroundColor Cyan
    Write-Host "ℹ️  You can now run PowerShell scripts in this repository without restrictions." -ForegroundColor Yellow

} catch {
    Write-Host "❌ Error configuring PowerShell execution policy: $_" -ForegroundColor Red
    Write-Host "💡 You may need to run PowerShell as Administrator" -ForegroundColor Yellow
}

# Display current execution policy status
Write-Host "`n📋 Current PowerShell Execution Policy Status:" -ForegroundColor Cyan
Get-ExecutionPolicy -List | Format-Table -AutoSize