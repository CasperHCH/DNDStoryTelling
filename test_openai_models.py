#!/usr/bin/env python3
"""
Test script to verify OpenAI API access and model availability
"""
import asyncio
import os
from openai import AsyncOpenAI

async def test_openai_models():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        return

    client = AsyncOpenAI(api_key=api_key)

    models_to_test = ["gpt-4o", "gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]

    print("🧪 Testing OpenAI API Model Access...")
    print("=" * 50)

    for model in models_to_test:
        try:
            print(f"Testing {model}...", end=" ")
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello, this is a test!' in exactly 5 words."}
                ],
                max_tokens=20
            )
            result = response.choices[0].message.content.strip()
            print(f"✅ SUCCESS - Response: {result}")

        except Exception as e:
            error_msg = str(e)
            if "model" in error_msg.lower() and ("not found" in error_msg.lower() or "does not exist" in error_msg.lower()):
                print(f"❌ NOT AVAILABLE - {error_msg}")
            else:
                print(f"🔥 ERROR - {error_msg}")

    print("\n" + "=" * 50)
    print("✅ Model testing complete!")

if __name__ == "__main__":
    asyncio.run(test_openai_models())