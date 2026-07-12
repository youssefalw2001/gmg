#!/usr/bin/env python3
"""Quick token refresh"""
import json
import requests

with open("tokens.json") as f:
    tokens = json.load(f)

with open("cookies.json") as f:
    cookies = json.load(f)

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

HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

print("🔄 Refreshing token...")
try:
    r = requests.post(
        "https://gmgn.ai/account/account/refresh_access_token",
        params=PARAMS,
        headers=HEADERS,
        cookies=cookies,
        json={"refresh_token": tokens["refresh_token"]},
        timeout=15
    )
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        d = r.json()
        print(f"Full response: {json.dumps(d, indent=2)}")
        if d.get("code") == 0:
            data = d["data"]["data"]  # Nested data object
            new_token = data.get("token") or data.get("access_token")
            expire_at = data["expire_at"]
            print(f"✅ GOT NEW TOKEN!")
            print(f"Expires: {expire_at}")
            print(f"Token: {new_token[:80]}...")
            
            # Update tokens.json
            tokens["access_token"] = new_token
            tokens["expire_at"] = expire_at
            
            with open("tokens.json", "w") as f:
                json.dump(tokens, f, indent=2)
            
            print("\n✅ Updated tokens.json")
        else:
            print(f"Error: {d}")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Exception: {e}")
