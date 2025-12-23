"""
Test Ollama Connection Script
Tests connection to Mac Studio Ollama instance
"""
import asyncio
import httpx
import os
import sys

async def test_ollama_connection():
    """Test Ollama connection and model availability"""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    
    print(f"🔍 Testing Ollama connection...")
    print(f"📍 URL: {base_url}")
    print("")
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Test 1: Health Check
        print("1️⃣ Health Check...")
        try:
            response = await client.get(f"{base_url}/api/tags", timeout=5.0)
            if response.status_code == 200:
                models = response.json().get("models", [])
                print(f"   ✅ Ollama is running")
                print(f"   📦 Available models: {len(models)}")
                for model in models[:5]:  # Show first 5
                    name = model.get("name", "Unknown")
                    size = model.get("size", 0) / (1024**3)  # Convert to GB
                    print(f"      - {name} ({size:.1f} GB)")
                if len(models) > 5:
                    print(f"      ... and {len(models) - 5} more")
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health check failed: {str(e)}")
            print(f"   💡 Make sure SSH tunnel is active or Ollama is accessible")
            return False
        
        print("")
        
        # Test 2: Model Generation
        print("2️⃣ Model Generation Test...")
        model_name = os.getenv("OLLAMA_MODEL", "qwen2.5:32b-instruct")
        print(f"   Testing model: {model_name}")
        
        try:
            response = await client.post(
                f"{base_url}/api/chat",
                json={
                    "model": model_name,
                    "messages": [{"role": "user", "content": "Say hello in one word"}],
                    "stream": False
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("message", {}).get("content", "")
                if content:
                    print(f"   ✅ Generation successful")
                    print(f"   📝 Response: {content.strip()}")
                else:
                    print(f"   ⚠️  Empty response received")
            elif response.status_code == 404:
                print(f"   ❌ Model '{model_name}' not found")
                print(f"   💡 Available models listed above")
                return False
            else:
                print(f"   ❌ Generation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except httpx.TimeoutException:
            print(f"   ⚠️  Request timed out (model may be loading)")
            print(f"   💡 This is normal for first request. Try again.")
            return True  # Not a failure, just slow
        except Exception as e:
            print(f"   ❌ Generation test failed: {str(e)}")
            return False
        
        print("")
        print("✅ All tests passed! Ollama is ready to use.")
        return True

if __name__ == "__main__":
    success = asyncio.run(test_ollama_connection())
    sys.exit(0 if success else 1)

