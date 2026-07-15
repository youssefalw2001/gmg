#!/usr/bin/env python3
"""
Setup script for authorized security testing.

This script prepares the test environment with credentials for TWO accounts
owned by the SAME user for authorized security research.
"""

import json

def setup_test_environment():
    """
    Setup test environment with account credentials.
    
    Note: Both accounts belong to the same user conducting authorized testing.
    """
    print("=" * 70)
    print("AUTHORIZED SECURITY TEST SETUP")
    print("=" * 70)
    print("\nThis will set up credentials for authorized security testing.")
    print("\n⚠️  IMPORTANT:")
    print("   • Both accounts must be owned by YOU")
    print("   • This is for authorized security research only")
    print("   • Do not use on accounts you don't own")
    print("\n" + "=" * 70)
    
    # Get Account 1 token
    print("\n[1] Account 1 (Your primary testing account):")
    print("    This is YOUR account that will attempt cross-account actions")
    account1_token = input("\n    Enter Account 1 access token: ").strip()
    
    # Save Account 1 token
    with open('account1_token.txt', 'w') as f:
        f.write(account1_token)
    
    print("    [✓] Account 1 token saved")
    
    # Get Account 2 wallets
    print("\n[2] Account 2 (Your secondary testing account):")
    print("    This is YOUR second account used as the test target")
    print("    Note: Must be a gmgn MPC wallet address (bot_sol_address)")
    
    account2_sol = input("\n    Enter Account 2 SOL MPC wallet: ").strip()
    account2_bsc = input("    Enter Account 2 BSC MPC wallet (or press Enter to skip): ").strip()
    
    if not account2_bsc:
        account2_bsc = None
    
    # Save Account 2 wallets
    account2_data = {
        'sol_wallet': account2_sol,
        'bsc_wallet': account2_bsc,
        'note': 'These are MY accounts used for authorized security testing'
    }
    
    with open('account2_wallets.json', 'w') as f:
        json.dump(account2_data, f, indent=2)
    
    print("    [✓] Account 2 wallets saved")
    
    # Confirmation
    print("\n" + "=" * 70)
    print("SETUP COMPLETE")
    print("=" * 70)
    print("\n[✓] Test environment configured:")
    print(f"    • Account 1 Token: {account1_token[:50]}...")
    print(f"    • Account 2 SOL: {account2_sol}")
    if account2_bsc:
        print(f"    • Account 2 BSC: {account2_bsc}")
    
    print("\n[!] Ready to run authorized security tests")
    print("    Run: python3 run_authorized_test.py")
    
    print("\n⚠️  REMINDER:")
    print("   • Both accounts must be owned by you")
    print("   • This is authorized security research")
    print("   • All tests are within legal and ethical boundaries")
    print("\n" + "=" * 70)


if __name__ == "__main__":
    setup_test_environment()
