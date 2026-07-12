#!/usr/bin/env python3
"""
AGGRESSIVE XSS SCANNER
Brute force test EVERY possible endpoint pattern
"""
import json
import requests
import time

with open("tokens.json") as f:
    tokens = json.load(f)

with open("cookies.json") as f:
    cookies = json.load(f)

ACCESS_TOKEN = tokens["access_token"]

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

PARAMS = {
    "device_id": "acf898c7-5063-4d0f-b992-d1e5d568409e",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260712-1986-3641f8b",
    "from_app": "gmgn",
    "app_ver": "20260712-1986-3641f8b",
    "tz_name": "Asia/Aden",
    "tz_offset": "10800",
    "app_lang": "en-US",
    "os": "web",
    "worker": "0"
}

print("="*80)
print("🦊 AGGRESSIVE XSS SCANNER - BRUTE FORCE MODE")
print("="*80)

# ALL possible endpoint patterns to test
ENDPOINTS = [
    # Account/Profile
    ("/api/v1/user/update", {"username": "XSS", "bio": "XSS", "nickname": "XSS"}),
    ("/api/v2/user/update", {"username": "XSS", "bio": "XSS"}),
    ("/account/user/update", {"bio": "XSS", "username": "XSS"}),
    ("/account/update", {"bio": "XSS"}),
    ("/account/profile/update", {"bio": "XSS", "display_name": "XSS"}),
    ("/account/settings", {"bio": "XSS", "nickname": "XSS"}),
    ("/xapi/v1/user/update", {"bio": "XSS"}),
    
    # Wallet
    ("/account/wallet/update", {"address": "0x0000000000000000000000000000000000000001", "nickname": "XSS", "chain": "bsc"}),
    ("/account/wallet/add", {"address": "0x0000000000000000000000000000000000000001", "nickname": "XSS", "chain": "bsc"}),
    ("/api/v1/wallet/update", {"address": "0x0000000000000000000000000000000000000001", "label": "XSS"}),
    ("/xapi/v1/wallet/update", {"address": "0x0000000000000000000000000000000000000001", "nickname": "XSS"}),
    
    # Token notes/comments
    ("/api/v1/token/note", {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "note": "XSS", "chain": "bsc"}),
    ("/api/v1/note/create", {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "content": "XSS", "chain": "bsc"}),
    ("/xapi/v1/token/note", {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "note": "XSS"}),
    
    # Watchlist/Portfolio
    ("/api/v1/watchlist/create", {"name": "XSS", "description": "XSS"}),
    ("/xapi/v1/watchlist/create", {"name": "XSS", "chain": "bsc"}),
    ("/api/v1/portfolio/create", {"name": "XSS", "note": "XSS"}),
    
    # Settings
    ("/account/settings/update", {"nickname": "XSS", "bio": "XSS"}),
    ("/api/v1/settings/update", {"username": "XSS"}),
]

results = []

for endpoint, payload in ENDPOINTS:
    print(f"\n[TESTING] {endpoint}")
    
    try:
        r = requests.post(
            f"https://gmgn.ai{endpoint}",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json=payload,
            timeout=10,
            allow_redirects=False
        )
        
        status = r.status_code
        print(f"  Status: {status}", end="")
        
        if status == 200:
            try:
                data = r.json()
                code = data.get("code", -1)
                print(f" | Code: {code}", end="")
                
                if code == 0:
                    print(f" | ✅ ACCEPTS INPUT!")
                    results.append({
                        "endpoint": endpoint,
                        "payload": payload,
                        "response": data
                    })
                elif code == 40101600:
                    print(f" | ⚠️ Trading auth required")
                else:
                    print(f" | ❌ Rejected")
            except:
                print(f" | Not JSON")
                
        elif status == 404:
            print(f" | Not found")
        elif status == 403:
            print(f" | WAF blocked")
        else:
            print(f" | Other error")
            
    except Exception as e:
        print(f"  Error: {str(e)[:60]}")
    
    time.sleep(0.3)

print("\n" + "="*80)
print("🎯 ENDPOINTS THAT ACCEPT INPUT:")
print("="*80)

if results:
    for r in results:
        print(f"\n✅ {r['endpoint']}")
        print(f"   Payload: {r['payload']}")
        print(f"   Response: {json.dumps(r['response'], indent=2)[:200]}")
    
    print(f"\n💀 Found {len(results)} working endpoints!")
    print("\n🚀 NEXT: Test XSS payloads in these fields")
    
    with open("working_endpoints.json", "w") as f:
        json.dump(results, f, indent=2)
    
else:
    print("\n❌ No working endpoints found")
    print("\n💡 The endpoints either:")
    print("  1. Have different paths than we guessed")
    print("  2. Require different authentication")
    print("  3. Are only accessible via browser")

print("\n" + "="*80)
