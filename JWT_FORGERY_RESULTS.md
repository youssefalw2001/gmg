# JWT Forgery Attack Results — gmgn.ai

**Date:** 2026-07-12  
**Target:** `POST /account/account/refresh_access_token`  
**Objective:** Forge refresh tokens to impersonate ANY user  
**Result:** ALL 53 FORGERY MUTATIONS FAILED — ES256 signature validation is solid  

---

## Executive Summary

We ran the complete wraith JWT mutation matrix (53 variants across 9 attack classes) against gmgn.ai's token refresh endpoint. **Every single forgery attempt was rejected** with `code: -16202 "refresh access token fail !"`.

**gmgn.ai's JWT signature verification is properly implemented.** You CANNOT forge refresh tokens through any known JWT attack vector.

---

## Attack Classes Tested

### 1. `alg:none` Bypass (7 variants) — FAILED
All case variants of `alg:none` (none, None, NONE, nOnE, NoNe) with empty signatures.
- Server rejects: validates algorithm against whitelist

### 2. Empty/Missing/Truncated Signature (3 variants) — FAILED
- Empty third segment (`header.payload.`)
- No third segment (`header.payload`)
- Half-length signature
- Server rejects: requires valid ES256 signature

### 3. ES256→HS256 Algorithm Confusion (7 variants) — FAILED
Signed with server's public key as HMAC secret using:
- Raw EC point (0x04 || x || y)
- PEM-encoded SubjectPublicKeyInfo
- X coordinate only
- Y coordinate only
- X+Y concatenated
- HS384 and HS512 variants
- Server rejects: does NOT fall back to HMAC verification

### 4. Weak HS256 Secret Brute Force (23 variants) — FAILED
Tried: secret, password, 123456, gmgn, gmgn.ai, gmgn_secret, gmgn_signer,
signer, jwt_secret, your-256-bit-secret, HS256-secret, empty, key, test,
default, changeme, admin, supersecret, gmgn.ai/signer, gmgn.ai/access,
gmgn.ai/refresh, access_token_secret, refresh_token_secret
- Server rejects: not using HS256 at all

### 5. `kid` Injection (8 variants) — FAILED
- `/dev/null` path traversal (empty key)
- Deep traversal `../../../../../../dev/null`
- Empty kid
- URL-based kid
- SQL injection in kid (got 403 from Cloudflare WAF)
- kid + HS256 with empty secret
- Server rejects: doesn't use kid-based key lookup

### 6. `jku`/`x5u` URL Swap (1 variant) — FAILED
- Pointed to attacker-controlled JWKS endpoint
- Server rejects: doesn't fetch external key material

### 7. Claim Tampering with Original Signature (2 variants) — FAILED
- Changed user_id in payload, kept original signature
- Bumped exp to year 2286, kept original signature
- Server rejects: signature covers the payload (obviously)

### 8. Embedded JWK (1 variant) — FAILED
- Embedded attacker's HS256 key in JWT header
- Server rejects: doesn't use header-embedded keys

### 9. Cross-Token Signature (1 variant) — FAILED
- Used access token's signature on forged refresh payload
- Server rejects: tokens have separate signing contexts

---

## Server Behavior Analysis

| Input | Response Code | HTTP Status | Meaning |
|-------|---------------|-------------|---------|
| Valid refresh token | `0` | 200 | Success |
| Any forged token | `-16202` | 400 | Signature verification failed |
| SQL injection in header | WAF block | 403 | Cloudflare intercepted |
| Empty body | `-109901` | 400 | Field validation (Go struct) |
| Null/empty refresh_token | `-109901` | 400 | Required field missing |

**The server uses proper ES256 (P-256 ECDSA) with server-side private key signing.** The only way to forge tokens would be to obtain the private signing key itself.

---

## Additional Discovery: MPC Wallet Binding Chain

During the attack, we discovered live endpoints for the MPC wallet binding flow:

### Endpoint: `/account/trade_token`
- Requires: `secret` + `wallet_address` + `chain`
- Returns `403 "wallet not owned by user"` for ALL wallets (including our own bot addresses)
- **Bug:** Validates against `eth_address`/`sol_address` (empty for email accounts), NOT `bot_*_address`
- **Impact:** Email-only users can NEVER get a trade token through this endpoint

### Endpoint: `/account/mfa/txn/v1/verify_wallet_signature`
- Requires: `txn_id` (snake_case), `message`, `signature`, `address`, `chain`, `usage`
- `txn_id` must be 64 hex characters (server-generated)
- Returns `"invalid verify transaction, txn_id is invalid or expired"` with valid format

### Endpoint: `/account/bind_wallet`
- Requires: `txn_id` + `wallet_address` + `chain`
- `txn_id` format: 64 hex characters
- Returns `"invalid txn_id"` — needs server-generated value

### Endpoint: `/account/unbind_wallet`
- Same `txn_id` requirement as bind_wallet

### Missing: txn_id Mint Endpoint
- NOT at `/account/postNonce` (404)
- NOT at `/account/wc_init` (404)
- NOT at `/account/mfa/txn/v1/create` (404)
- Likely requires browser-side wallet interaction (WalletConnect/MetaMask)

---

## Conclusion: Token Forgery is NOT Possible

The refresh token forgery hypothesis is **DISPROVEN**. gmgn.ai properly:
1. Uses ES256 (ECDSA P-256) with server-held private key
2. Validates algorithm field (rejects alg:none, HS256 downgrade)
3. Verifies full signature over header+payload
4. Does NOT expose JWKS publicly
5. Does NOT use kid-based key selection
6. Does NOT accept embedded keys from headers
7. Returns consistent `-16202` error for ALL invalid signatures

### What IS Possible (Confirmed):
1. **XSS → Token Theft** — localStorage tokens + non-httpOnly `sid` cookie
2. **Stolen Token → Permanent Access** — refresh_access_token works with valid stolen tokens
3. **IDOR Exploits** — bind_invite, dividend_info, sol/claiming all work with ANY wallet address
4. **trade_token Bug** — validates against wrong address fields

### The Only Path to "Forge Any User":
- Steal their refresh_token via XSS (requires stored/reflected XSS)
- Steal their `sid` cookie via XSS (not httpOnly)
- There is NO cryptographic forgery method

---

## Session Status

**NOTE:** During endpoint enumeration, `/account/logout` was accidentally hit, invalidating the current session. A new token will be needed from the user's browser to continue testing.
