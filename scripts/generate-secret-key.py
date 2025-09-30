#!/usr/bin/env python3
"""
Generate a secure SECRET_KEY for production deployment on Synology NAS.
This script creates a cryptographically secure 64-character secret key.
"""

import secrets
import string
import os

def generate_secret_key(length=64):
    """Generate a cryptographically secure secret key."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*(-_=+)"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    # Generate a secure secret key
    secret_key = generate_secret_key()

    print("🔐 Generated Secure SECRET_KEY for Production:")
    print(f"SECRET_KEY={secret_key}")
    print()
    print("📝 Add this to your Synology environment:")
    print("1. Save this key in a secure location")
    print("2. Set as environment variable in docker-compose.synology.yml")
    print("3. Or create a .env file with this value")
    print()
    print("⚠️  Keep this key secret and secure!")
    print("⚠️  Never commit this key to version control!")

    # Optionally save to a file
    env_file = "synology.env"
    try:
        with open(env_file, "w") as f:
            f.write(f"SECRET_KEY={secret_key}\n")
            f.write("# Add other production environment variables here\n")
            f.write("ENVIRONMENT=production\n")
            f.write("DEBUG=false\n")
        print(f"✅ Secret key also saved to {env_file}")
    except Exception as e:
        print(f"❌ Could not save to file: {e}")