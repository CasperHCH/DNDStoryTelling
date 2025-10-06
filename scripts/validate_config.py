#!/usr/bin/env python3
"""
Configuration validation script for D&D Story Telling application.
Run this script to validate your environment configuration before starting the server.
"""

import os
import sys
from pathlib import Path

# Add the app directory to Python path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

def format_file_size(size_bytes):
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes / (1024**2):.1f} MB"
    else:
        return f"{size_bytes / (1024**3):.1f} GB"

def validate_config():
    """Validate configuration and display current settings."""
    try:
        from app.config import get_settings

        print("=" * 60)
        print("D&D Story Telling - Configuration Validation")
        print("=" * 60)

        settings = get_settings()

        # Environment Information
        print(f"\n🌍 Environment Configuration:")
        print(f"   Environment: {settings.ENVIRONMENT}")
        print(f"   Debug Mode: {settings.DEBUG}")
        print(f"   App Name: {settings.APP_NAME}")
        print(f"   Version: {settings.VERSION}")

        # Server Configuration
        print(f"\n🖥️  Server Configuration:")
        print(f"   Host: {settings.HOST}")
        print(f"   Port: {settings.PORT}")
        print(f"   Health Check: {settings.HEALTH_CHECK_ENDPOINT}")

        # Database Configuration
        print(f"\n🗄️  Database Configuration:")
        print(f"   Database URL: {settings.DATABASE_URL}")
        print(f"   Pool Size: {settings.DB_POOL_SIZE}")
        print(f"   Max Overflow: {settings.DB_MAX_OVERFLOW}")
        print(f"   Pool Timeout: {settings.DB_POOL_TIMEOUT}s")

        # File Upload Configuration
        print(f"\n📁 File Upload Configuration:")
        print(f"   Max File Size: {format_file_size(settings.MAX_FILE_SIZE)}")
        print(f"   Upload Directory: {settings.UPLOAD_DIR}")
        print(f"   Supported Formats: {', '.join(settings.supported_audio_formats_list)}")

        # Security Configuration
        print(f"\n🔒 Security Configuration:")
        print(f"   Secret Key: {'Set' if settings.SECRET_KEY else 'NOT SET (REQUIRED)'}")
        print(f"   Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
        print(f"   Allowed Hosts: {', '.join(settings.allowed_hosts_list)}")
        print(f"   CORS Origins: {', '.join(settings.cors_origins_list)}")

        # API Configuration
        print(f"\n🔑 API Configuration:")
        print(f"   OpenAI API Key: {'Set' if settings.OPENAI_API_KEY else 'Not Set'}")
        print(f"   Confluence URL: {settings.CONFLUENCE_URL or 'Not Set'}")
        print(f"   Confluence Token: {'Set' if settings.CONFLUENCE_API_TOKEN else 'Not Set'}")
        print(f"   Confluence Parent ID: {settings.CONFLUENCE_PARENT_PAGE_ID or 'Not Set'}")

        # Rate Limiting
        print(f"\n⏱️  Rate Limiting:")
        print(f"   Requests per Window: {settings.RATE_LIMIT_REQUESTS}")
        print(f"   Window Duration: {settings.RATE_LIMIT_WINDOW}s ({settings.RATE_LIMIT_WINDOW//3600}h)")

        # Logging Configuration
        print(f"\n📝 Logging Configuration:")
        print(f"   Log Level: {settings.LOG_LEVEL}")
        print(f"   Log File: {settings.LOG_FILE or 'Console (stdout)'}")

        # Socket.IO Configuration
        print(f"\n🔌 Socket.IO Configuration:")
        print(f"   Ping Interval: {settings.SOCKETIO_PING_INTERVAL}ms")
        print(f"   Ping Timeout: {settings.SOCKETIO_PING_TIMEOUT}ms")
        print(f"   Max Buffer Size: {format_file_size(settings.SOCKETIO_MAX_HTTP_BUFFER_SIZE)}")

        # Validation Checks
        print(f"\n✅ Validation Results:")

        errors = []
        warnings = []

        # Required settings
        if not settings.SECRET_KEY:
            errors.append("SECRET_KEY is required but not set")
        elif len(settings.SECRET_KEY) < 32 and not settings.is_testing:
            warnings.append("SECRET_KEY should be at least 32 characters for production")

        if not settings.DATABASE_URL:
            errors.append("DATABASE_URL is required but not set")

        # Recommendations
        if not settings.OPENAI_API_KEY:
            warnings.append("OPENAI_API_KEY not set - AI story generation will not work")

        if settings.MAX_FILE_SIZE > 10 * 1024**3:  # 10GB
            warnings.append(f"MAX_FILE_SIZE is very large ({format_file_size(settings.MAX_FILE_SIZE)}) - ensure sufficient disk space")

        if settings.DEBUG and settings.is_production:
            warnings.append("DEBUG is enabled in production environment - consider disabling")

        # Display results
        if errors:
            print("   ❌ Errors found:")
            for error in errors:
                print(f"      • {error}")

        if warnings:
            print("   ⚠️  Warnings:")
            for warning in warnings:
                print(f"      • {warning}")

        if not errors and not warnings:
            print("   ✅ All configuration looks good!")

        print(f"\n{'='*60}")

        if errors:
            print("❌ Configuration has errors - please fix before starting the server")
            return False
        else:
            print("✅ Configuration is valid - ready to start the server")
            return True

    except ImportError as e:
        print(f"❌ Error importing configuration: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Error validating configuration: {e}")
        return False

def main():
    """Main function."""
    success = validate_config()

    print(f"\n💡 Tips:")
    print(f"   • Copy .env.example to .env and customize your settings")
    print(f"   • Set OPENAI_API_KEY for AI story generation")
    print(f"   • Use environment-specific files: .env.development, .env.production")
    print(f"   • Start server with: python scripts/start_server.py")

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()