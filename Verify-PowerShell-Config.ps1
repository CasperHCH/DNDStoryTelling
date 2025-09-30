#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Verify PowerShell configuration for DNDStoryTelling repository

.DESCRIPTION
    This script verifies that PowerShell execution policy and security settings
    are correctly configured for running scripts in this repository.
#>

Write-Host "🔍 Verifying PowerShell configuration for DNDStoryTelling repository..." -ForegroundColor Cyan

$success = $true

try {
    # Check execution policy
    Write-Host "`n📋 Checking execution policy..." -ForegroundColor Yellow
    $policy = Get-ExecutionPolicy -Scope CurrentUser
    if ($policy -in @('RemoteSigned', 'Unrestricted', 'Bypass')) {
        Write-Host "✅ Execution policy is configured correctly: $policy" -ForegroundColor Green
    } else {
        Write-Host "❌ Execution policy needs configuration: $policy" -ForegroundColor Red
        $success = $false
    }

    # Check if we can read PowerShell scripts
    Write-Host "`n📄 Checking script accessibility..." -ForegroundColor Yellow
    $scripts = Get-ChildItem -Path "scripts" -Filter "*.ps1" -ErrorAction SilentlyContinue
    if ($scripts) {
        Write-Host "✅ Found $($scripts.Count) PowerShell script(s):" -ForegroundColor Green
        foreach ($script in $scripts) {
            Write-Host "  • $($script.Name)" -ForegroundColor White

            # Test if we can read the script content
            try {
                $null = Get-Content $script.FullName -TotalCount 1
                Write-Host "    ✓ Readable" -ForegroundColor Green
            } catch {
                Write-Host "    ✗ Cannot read: $($_.Exception.Message)" -ForegroundColor Red
                $success = $false
            }
        }
    } else {
        Write-Host "⚠️  No PowerShell scripts found in scripts directory" -ForegroundColor Yellow
    }

    # Check VS Code settings
    Write-Host "`n🛠️  Checking VS Code configuration..." -ForegroundColor Yellow
    $vscodeSettings = ".vscode\settings.json"
    if (Test-Path $vscodeSettings) {
        Write-Host "✅ VS Code settings configured: $vscodeSettings" -ForegroundColor Green
    } else {
        Write-Host "⚠️  VS Code settings not found (this is optional)" -ForegroundColor Yellow
    }

    # Test actual script execution (if test-docker.ps1 exists)
    Write-Host "`n🧪 Testing script execution..." -ForegroundColor Yellow
    $testScript = "scripts\test-docker.ps1"
    if (Test-Path $testScript) {
        try {
            # Just validate the script syntax without executing
            $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $testScript -Raw), [ref]$null)
            Write-Host "✅ test-docker.ps1 syntax is valid" -ForegroundColor Green
        } catch {
            Write-Host "❌ test-docker.ps1 syntax error: $($_.Exception.Message)" -ForegroundColor Red
            $success = $false
        }
    }

    # Summary
    Write-Host "`n📊 Configuration Summary:" -ForegroundColor Cyan
    Get-ExecutionPolicy -List | Format-Table -AutoSize

    if ($success) {
        Write-Host "🎉 PowerShell configuration verification completed successfully!" -ForegroundColor Green
        Write-Host "ℹ️  All PowerShell scripts in this repository can be executed without restrictions." -ForegroundColor White
        Write-Host "ℹ️  You can run any .ps1 script using: .\script-name.ps1" -ForegroundColor White
    } else {
        Write-Host "❌ PowerShell configuration has issues that need to be resolved." -ForegroundColor Red
        Write-Host "💡 Run .\Setup-PowerShell.ps1 to fix configuration issues." -ForegroundColor Yellow
    }

} catch {
    Write-Host "❌ Error during verification: $($_.Exception.Message)" -ForegroundColor Red
    $success = $false
}

# Return appropriate exit code
if ($success) {
    exit 0
} else {
    exit 1
}