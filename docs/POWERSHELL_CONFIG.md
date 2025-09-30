# PowerShell Configuration for DNDStoryTelling Repository

This repository includes PowerShell scripts and has been configured to allow unrestricted execution of scripts within the repository.

## 🔧 Automatic Configuration

The repository includes automatic PowerShell configuration that:

- ✅ Sets appropriate execution policy (`RemoteSigned`)
- ✅ Configures VS Code PowerShell extension settings
- ✅ Enables script analysis and formatting
- ✅ Trusts all scripts within this repository

## 🚀 Quick Setup

If you're setting up this repository for the first time:

```powershell
# Run the setup script (one-time setup)
.\Setup-PowerShell.ps1

# Verify configuration is working
.\Verify-PowerShell-Config.ps1
```

## 📜 Available PowerShell Scripts

- `Setup-PowerShell.ps1` - Initial repository PowerShell configuration
- `Verify-PowerShell-Config.ps1` - Verify PowerShell configuration status
- `scripts\test-docker.ps1` - Run Docker-based tests
- `scripts\Deploy-Synology.ps1` - Deploy to Synology NAS

## 🛡️ Security Configuration

### Execution Policy
The repository is configured with `RemoteSigned` execution policy, which:
- Allows local scripts to run without signatures
- Requires remote scripts to be signed
- Provides good security while enabling development workflow

### VS Code Integration
The `.vscode/settings.json` file configures:
- PowerShell extension settings
- Script analysis rules
- Code formatting preferences
- Terminal integration with correct execution policy

## 🔍 Troubleshooting

### If scripts won't run:
```powershell
# Check current execution policy
Get-ExecutionPolicy -List

# Fix execution policy if needed
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run verification
.\Verify-PowerShell-Config.ps1
```

### If you get "cannot be loaded because running scripts is disabled":
1. Run PowerShell as Administrator
2. Execute: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine`
3. Restart PowerShell
4. Run `.\Setup-PowerShell.ps1` again

## ✅ Current Status

PowerShell configuration is **fully configured** and ready for use. All scripts in this repository can be executed without additional prompts or restrictions.

---

*This configuration ensures secure and seamless PowerShell script execution for the DNDStoryTelling project.*