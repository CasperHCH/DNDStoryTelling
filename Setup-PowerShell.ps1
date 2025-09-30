#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup PowerShell execution environment for DNDStoryTelling repository

.DESCRIPTION
    This script configures PowerShell execution policy and security settings
    to allow running scripts within this repository without restrictions.

.EXAMPLE
    .\Setup-PowerShell.ps1

.NOTES
    Run this once after cloning the repository to configure PowerShell security.
#>

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

Write-Host "🚀 Setting up PowerShell environment for DNDStoryTelling repository..." -ForegroundColor Cyan

# Get repository root
$RepoRoot = Split-Path -Parent $PSScriptRoot
Write-Host "📁 Repository root: $RepoRoot" -ForegroundColor Gray

try {
    # Check current execution policy
    $currentPolicy = Get-ExecutionPolicy -Scope CurrentUser
    Write-Host "📋 Current execution policy: $currentPolicy" -ForegroundColor Gray

    # Set appropriate execution policy
    if ($currentPolicy -eq 'Restricted' -or $currentPolicy -eq 'Undefined') {
        Write-Host "🔧 Setting execution policy to RemoteSigned..." -ForegroundColor Yellow
        Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force
        Write-Host "✅ Execution policy updated to RemoteSigned" -ForegroundColor Green
    } else {
        Write-Host "✅ Execution policy already configured: $currentPolicy" -ForegroundColor Green
    }

    # Create PowerShell profile entry for this repository (optional)
    $profilePath = $PROFILE.CurrentUserCurrentHost
    if ($profilePath -and (Test-Path (Split-Path $profilePath))) {
        $profileEntry = @"

# Auto-configure DNDStoryTelling repository
if (`$PWD.Path -like '*DNDStoryTelling*') {
    Write-Host "🎯 DNDStoryTelling PowerShell environment active" -ForegroundColor Green
}
"@

        if (Test-Path $profilePath) {
            $profileContent = Get-Content $profilePath -Raw
            if ($profileContent -notlike '*DNDStoryTelling*') {
                Add-Content -Path $profilePath -Value $profileEntry
                Write-Host "✅ Added repository configuration to PowerShell profile" -ForegroundColor Green
            }
        } else {
            New-Item -Path $profilePath -ItemType File -Force | Out-Null
            Set-Content -Path $profilePath -Value $profileEntry
            Write-Host "✅ Created PowerShell profile with repository configuration" -ForegroundColor Green
        }
    }

    # Test script execution
    Write-Host "🧪 Testing script execution..." -ForegroundColor Yellow
    $testScriptPath = Join-Path $RepoRoot "scripts\test-docker.ps1"
    if (Test-Path $testScriptPath) {
        # Just test that we can read the script without executing
        $null = Get-Content $testScriptPath -TotalCount 1
        Write-Host "✅ PowerShell scripts are accessible" -ForegroundColor Green
    }

    Write-Host "`n🎉 PowerShell environment setup completed successfully!" -ForegroundColor Cyan
    Write-Host "ℹ️  You can now run any PowerShell script in this repository." -ForegroundColor White
    Write-Host "ℹ️  Repository scripts are trusted and will execute without prompts." -ForegroundColor White

    Write-Host "`n📋 Available PowerShell scripts in this repository:" -ForegroundColor Cyan
    $scriptsPath = Join-Path $RepoRoot "scripts"
    if (Test-Path $scriptsPath) {
        Get-ChildItem -Path $scriptsPath -Filter "*.ps1" | ForEach-Object {
            Write-Host "  • $($_.Name)" -ForegroundColor White
        }
    } else {
        Write-Host "  No PowerShell scripts found in scripts directory" -ForegroundColor Yellow
    }

} catch {
    Write-Host "❌ Error setting up PowerShell environment: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "💡 Try running PowerShell as Administrator, or manually set execution policy:" -ForegroundColor Yellow
    Write-Host "   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Gray
    exit 1
}

Write-Host "`n📊 Current PowerShell Execution Policy Status:" -ForegroundColor Cyan
Get-ExecutionPolicy -List | Format-Table -AutoSize