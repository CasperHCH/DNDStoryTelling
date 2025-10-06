#!/usr/bin/env python3
"""
Check OpenAI API quota and billing status.
Run this script to diagnose OpenAI API issues.
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.config import get_settings
import openai
from openai import AsyncOpenAI

async def check_openai_status():
    """Check OpenAI API key validity and quota status."""
    print("🔍 Checking OpenAI API Status...\n")

    # Load configuration
    settings = get_settings()
    api_key = settings.OPENAI_API_KEY

    if not api_key:
        print("❌ No OpenAI API key found in configuration!")
        print("   Set OPENAI_API_KEY in your .env file")
        return False

    print(f"✅ API Key found: {api_key[:8]}...{api_key[-4:]}")

    # Initialize client
    client = AsyncOpenAI(api_key=api_key)

    # Test 1: Check if we can access the API at all
    print("\n🧪 Testing API Access...")
    try:
        # Simple API call to check authentication
        models = await client.models.list()
        print(f"✅ API Authentication successful")
        print(f"   Available models: {len(models.data)}")

        # List some key models we need
        available_models = [model.id for model in models.data]
        required_models = ["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

        print("\n📋 Model Availability:")
        for model in required_models:
            if model in available_models:
                print(f"   ✅ {model} - Available")
            else:
                print(f"   ❌ {model} - Not available")

    except Exception as e:
        print(f"❌ API Authentication failed: {e}")
        if "quota" in str(e).lower():
            print("\n💳 QUOTA ISSUE DETECTED!")
            print("   Your OpenAI account has exceeded its usage quota.")
            print("   Solutions:")
            print("   • Check billing: https://platform.openai.com/account/billing")
            print("   • Add payment method or credits")
            print("   • Upgrade your plan if needed")
            print("   • Wait for quota reset (if on free tier)")
        return False

    # Test 2: Try a simple completion
    print("\n🎯 Testing Story Generation...")
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheaper model for testing
            messages=[
                {"role": "user", "content": "Say 'Test successful' if you can read this."}
            ],
            max_tokens=10
        )

        result = response.choices[0].message.content.strip()
        print(f"✅ Story generation test successful")
        print(f"   Response: {result}")

    except Exception as e:
        print(f"❌ Story generation test failed: {e}")
        if "quota" in str(e).lower() or "insufficient_quota" in str(e).lower():
            print("\n💳 QUOTA EXCEEDED!")
            print("   Your OpenAI API quota has been exhausted.")
            print("\n🔄 To restore functionality:")
            print("   1. Visit: https://platform.openai.com/account/billing")
            print("   2. Check your current usage and limits")
            print("   3. Add credits or upgrade your plan")
            print("   4. Monitor usage to avoid future quota issues")
        return False

    print("\n🎉 All tests passed! OpenAI integration should work properly.")
    return True

def main():
    """Main function to run the quota check."""
    print("=" * 60)
    print("         OpenAI API Quota & Status Checker")
    print("=" * 60)

    try:
        result = asyncio.run(check_openai_status())

        if result:
            print("\n✅ Your OpenAI integration is ready to use!")
            print("   Try uploading an audio file or using the chat feature.")
        else:
            print("\n❌ OpenAI integration needs attention.")
            print("   The app will run in demo mode until issues are resolved.")

    except KeyboardInterrupt:
        print("\n⏹️  Check cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")

    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()