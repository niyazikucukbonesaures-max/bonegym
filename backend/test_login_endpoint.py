#!/usr/bin/env python3
"""
Login endpoint'ini test et
"""

import asyncio
import aiohttp
import json


async def test_login():
    """Login endpoint'ini test et."""
    
    url = "http://localhost:8000/api/auth/login"
    
    login_data = {
        "email": "admin@fitness.com",
        "password": "admin123"
    }
    
    print("🧪 Login Endpoint Testi")
    print("=" * 30)
    print(f"URL: {url}")
    print(f"Data: {json.dumps(login_data, indent=2)}")
    print()
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=login_data) as response:
                print(f"Status: {response.status}")
                print(f"Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    result = await response.json()
                    print("✅ Login başarılı!")
                    print(f"Token: {result['access_token'][:20]}...")
                    print(f"User: {result['user']['email']}")
                    
                    # Token ile /me endpoint'ini test et
                    await test_me_endpoint(session, result['access_token'])
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Login başarısız: {response.status}")
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"❌ Bağlantı hatası: {e}")


async def test_me_endpoint(session, token):
    """Me endpoint'ini test et."""
    
    print(f"\n🧪 Me Endpoint Testi")
    print("-" * 30)
    
    url = "http://localhost:8000/api/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        async with session.get(url, headers=headers) as response:
            print(f"Status: {response.status}")
            
            if response.status == 200:
                result = await response.json()
                print("✅ Me endpoint başarılı!")
                print(f"User: {result['email']}")
            else:
                error_text = await response.text()
                print(f"❌ Me endpoint başarısız: {response.status}")
                print(f"Error: {error_text}")
                
    except Exception as e:
        print(f"❌ Me endpoint hatası: {e}")


if __name__ == "__main__":
    asyncio.run(test_login())