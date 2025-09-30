# D&D Story Telling - Synology NAS Deployment Script (PowerShell)
# This script helps prepare files for deployment on Synology DS718+

param(
    [Parameter(Position=0)]
    [ValidateSet("Deploy", "Check", "Status", "Stop", "Restart")]
    [string]$Action = "Deploy",

    [string]$SynologyHost = "",
    [string]$SynologyUser = "admin",
    [string]$DeploymentPath = "/volume1/docker/dndstorytelling"
)

# Initialize logging
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARNING" { "Yellow" }
        "SUCCESS" { "Green" }
        default { "White" }
    }

    Write-Host "[$timestamp] [$Level] $Message" -ForegroundColor $color
}

function Test-Prerequisites {
    Write-Log "Checking prerequisites..." "INFO"

    # Check if Docker files exist
    $requiredFiles = @(
        "docker-compose.synology.yml",
        "Dockerfile",
        "requirements.txt",
        "app"
    )

    $missing = @()
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missing += $file
        }
    }

    if ($missing.Count -gt 0) {
        Write-Log "Missing required files: $($missing -join ', ')" "ERROR"
        return $false
    }

    # Check if SSH/SCP is available (for remote deployment)
    if ($SynologyHost) {
        try {
            $null = Get-Command ssh -ErrorAction Stop
            $null = Get-Command scp -ErrorAction Stop
            Write-Log "SSH tools available for remote deployment" "SUCCESS"
        }
        catch {
            Write-Log "SSH tools not found. Install OpenSSH or use manual file transfer." "WARNING"
        }
    }

    Write-Log "Prerequisites check completed" "SUCCESS"
    return $true
}

function New-DeploymentPackage {
    Write-Log "Creating deployment package..." "INFO"

    $packageName = "dndstorytelling-synology-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
    $packagePath = ".\$packageName"

    # Create package directory
    New-Item -ItemType Directory -Path $packagePath -Force | Out-Null

    # Copy required files
    $filesToCopy = @{
        "docker-compose.synology.yml" = "docker-compose.yml"
        "Dockerfile" = "Dockerfile"
        "requirements.txt" = "requirements.txt"
        "wait-for-it.sh" = "wait-for-it.sh"
        "scripts\deploy-synology.sh" = "deploy.sh"
    }

    foreach ($source in $filesToCopy.Keys) {
        $destination = Join-Path $packagePath $filesToCopy[$source]
        if (Test-Path $source) {
            Copy-Item $source $destination
            Write-Log "Copied $source -> $($filesToCopy[$source])" "INFO"
        }
    }

    # Copy application directory
    if (Test-Path "app") {
        Copy-Item "app" "$packagePath\app" -Recurse
        Write-Log "Copied application code" "INFO"
    }

    # Copy PostgreSQL config if exists
    if (Test-Path "postgres\synology-postgresql.conf") {
        New-Item -ItemType Directory -Path "$packagePath\postgres" -Force | Out-Null
        Copy-Item "postgres\synology-postgresql.conf" "$packagePath\postgres\"
        Write-Log "Copied PostgreSQL configuration" "INFO"
    }

    # Create environment template
    $envTemplate = @"
# D&D Story Telling Configuration for Synology NAS
# IMPORTANT: Configure these values before deployment

# Required API Keys (MUST be configured)
OPENAI_API_KEY=your_openai_api_key_here
CONFLUENCE_API_TOKEN=your_confluence_token_here
CONFLUENCE_URL=https://your-domain.atlassian.net

# Security (CHANGE THESE)
SECRET_KEY=synology_secret_key_change_me_to_something_secure_32chars_min
POSTGRES_PASSWORD=change_this_secure_database_password

# Optional Settings
CONFLUENCE_PARENT_PAGE_ID=123456789
"@

    Set-Content "$packagePath\.env.template" $envTemplate

    # Create deployment instructions
    $instructions = @"
# D&D Story Telling - Synology Deployment Instructions

## Quick Start

1. **Configure Environment**
   - Copy `.env.template` to `.env`
   - Edit `.env` with your actual API keys and settings

2. **Deploy via SSH (Recommended)**
   ```bash
   # Upload files to your Synology NAS
   scp -r * admin@your-nas-ip:/volume1/docker/dndstorytelling/

   # SSH into your NAS and run deployment
   ssh admin@your-nas-ip
   cd /volume1/docker/dndstorytelling
   chmod +x deploy.sh
   ./deploy.sh
   ```

3. **Manual Deployment**
   - Upload all files to `/volume1/docker/dndstorytelling/` on your NAS
   - SSH into your NAS
   - Run: `cd /volume1/docker/dndstorytelling && docker-compose up -d`

## Configuration Required

### Environment Variables (.env file)
- **OPENAI_API_KEY**: Your OpenAI API key for GPT-4 and Whisper
- **CONFLUENCE_API_TOKEN**: API token for Confluence Cloud
- **CONFLUENCE_URL**: Your Confluence instance URL
- **SECRET_KEY**: Secure random string (32+ characters)
- **POSTGRES_PASSWORD**: Secure database password

### Resource Requirements
- **RAM**: Minimum 1.5GB available (application uses ~1GB)
- **Storage**: ~2GB for images and application data
- **CPU**: ARM64 compatible (DS718+ supported)

## Post-Deployment

1. **Health Check**: http://your-nas-ip:8000/health
2. **Application**: http://your-nas-ip:8000
3. **Logs**: `docker-compose logs -f`

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs web
docker-compose logs db

# Check resource usage
docker stats

# Restart services
docker-compose restart
```

### Out of Memory
- Reduce max_connections in PostgreSQL config
- Restart Docker service: `sudo systemctl restart docker`
- Free memory: `echo 3 > /proc/sys/vm/drop_caches`

### Permission Issues
```bash
# Fix ownership
sudo chown -R 1000:1000 /volume1/docker/dndstorytelling
sudo chmod -R 755 /volume1/docker/dndstorytelling
```

## Commands Reference

```bash
# Deploy application
./deploy.sh

# Check status
./deploy.sh --status

# View logs
./deploy.sh --logs

# Stop application
./deploy.sh --stop

# Restart application
./deploy.sh --restart

# Health check
./deploy.sh --check-health
```
"@

    Set-Content "$packagePath\DEPLOYMENT.md" $instructions

    # Create ZIP package
    try {
        $zipPath = "$packageName.zip"
        Compress-Archive -Path "$packagePath\*" -DestinationPath $zipPath -Force
        Write-Log "Created deployment package: $zipPath" "SUCCESS"

        # Clean up temporary directory
        Remove-Item $packagePath -Recurse -Force

        return $zipPath
    }
    catch {
        Write-Log "Failed to create ZIP package: $($_.Exception.Message)" "ERROR"
        return $packagePath
    }
}

function Deploy-ToSynology {
    param([string]$PackagePath)

    if (-not $SynologyHost) {
        Write-Log "No Synology host specified. Package created for manual deployment." "WARNING"
        Write-Log "Upload contents to your NAS at: $DeploymentPath" "INFO"
        return
    }

    Write-Log "Deploying to Synology NAS: $SynologyHost" "INFO"

    try {
        # Create remote directory
        $createDirCmd = "ssh $SynologyUser@$SynologyHost 'mkdir -p $DeploymentPath'"
        Invoke-Expression $createDirCmd

        # Upload files
        if (Test-Path $PackagePath -PathType Container) {
            $uploadCmd = "scp -r '$PackagePath\*' $SynologyUser@$SynologyHost`:$DeploymentPath/"
        } else {
            # Extract and upload ZIP
            $tempDir = "$env:TEMP\dnd-deploy-$(Get-Random)"
            Expand-Archive -Path $PackagePath -DestinationPath $tempDir
            $uploadCmd = "scp -r '$tempDir\*' $SynologyUser@$SynologyHost`:$DeploymentPath/"
        }

        Write-Log "Uploading files..." "INFO"
        Invoke-Expression $uploadCmd

        # Make scripts executable and run deployment
        $deployCmd = @"
ssh $SynologyUser@$SynologyHost 'cd $DeploymentPath && chmod +x deploy.sh && ./deploy.sh'
"@

        Write-Log "Running deployment script..." "INFO"
        Invoke-Expression $deployCmd

        Write-Log "Deployment completed!" "SUCCESS"
        Write-Log "Application should be available at: http://$SynologyHost:8000" "INFO"

    }
    catch {
        Write-Log "Deployment failed: $($_.Exception.Message)" "ERROR"
        Write-Log "Try manual deployment using the created package" "INFO"
    }
}

function Invoke-RemoteCommand {
    param([string]$Command)

    if (-not $SynologyHost) {
        Write-Log "No Synology host specified" "ERROR"
        return
    }

    try {
        $remoteCmd = "ssh $SynologyUser@$SynologyHost 'cd $DeploymentPath && $Command'"
        Invoke-Expression $remoteCmd
    }
    catch {
        Write-Log "Remote command failed: $($_.Exception.Message)" "ERROR"
    }
}

# Main execution
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host "D&D Story Telling - Synology Deployment Tool" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host

if (-not (Test-Prerequisites)) {
    Write-Log "Prerequisites check failed. Please ensure all required files are present." "ERROR"
    exit 1
}

switch ($Action) {
    "Deploy" {
        $package = New-DeploymentPackage

        if ($SynologyHost) {
            Deploy-ToSynology $package
        } else {
            Write-Log "Deployment package created: $package" "SUCCESS"
            Write-Log "To deploy manually:" "INFO"
            Write-Log "1. Extract the package to your Synology NAS at $DeploymentPath" "INFO"
            Write-Log "2. SSH into your NAS and run: cd $DeploymentPath && chmod +x deploy.sh && ./deploy.sh" "INFO"
            Write-Log "3. Or specify -SynologyHost parameter for automatic deployment" "INFO"
        }
    }

    "Check" {
        Invoke-RemoteCommand "./deploy.sh --check-health"
    }

    "Status" {
        Invoke-RemoteCommand "./deploy.sh --status"
    }

    "Stop" {
        Invoke-RemoteCommand "./deploy.sh --stop"
    }

    "Restart" {
        Invoke-RemoteCommand "./deploy.sh --restart"
    }
}

Write-Log "Operation completed!" "SUCCESS"