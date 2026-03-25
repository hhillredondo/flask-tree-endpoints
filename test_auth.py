#!/usr/bin/env python3
"""
Test script for Flask authentication middleware
"""

import json
import os
import sys

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app


def test_health_check():
    """Test the health check endpoint (no auth required)"""
    print("🔍 Testing health check endpoint...")
    
    with app.test_client() as client:
        response = client.get('/')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.get_json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Health check passed!")
            return True
        else:
            print("❌ Health check failed!")
            return False

def test_protected_endpoint_without_auth():
    """Test a protected endpoint without authentication"""
    print("\n🔍 Testing protected endpoint without authentication...")
    
    with app.test_client() as client:
        response = client.get('/auth/me')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.get_json(), indent=2)}")
        
        if response.status_code == 401:
            print("✅ Authentication required - as expected!")
            return True
        else:
            print("❌ Expected 401 but got different status code!")
            return False

def test_protected_endpoint_with_invalid_auth():
    """Test a protected endpoint with invalid authentication"""
    print("\n🔍 Testing protected endpoint with invalid authentication...")
    
    with app.test_client() as client:
        headers = {'Authorization': 'Bearer invalid-token'}
        response = client.get('/auth/me', headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.get_json(), indent=2)}")
        
        if response.status_code == 401:
            print("✅ Invalid token rejected - as expected!")
            return True
        else:
            print("❌ Expected 401 but got different status code!")
            return False

def test_protected_endpoint_with_valid_auth():
    """Test a protected endpoint with valid authentication (requires real token)"""
    print("\n🔍 Testing protected endpoint with valid authentication...")
    print("⚠️  This test requires a valid JWT token from your Amplify app")
    print("   You can get this token by logging into your Amplify app and")
    print("   checking the browser's developer tools for the Authorization header")
    
    # You can uncomment and modify this section to test with a real token
    """
    with app.test_client() as client:
        # Replace with your actual JWT token from Amplify
        valid_token = "your-jwt-token-here"
        headers = {'Authorization': f'Bearer {valid_token}'}
        response = client.get('/auth/me', headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.get_json(), indent=2)}")
        
        if response.status_code == 200:
            print("✅ Valid token accepted!")
            return True
        else:
            print("❌ Valid token rejected!")
            return False
    """
    
    print("⏭️  Skipping this test - add your JWT token to test")
    return True

def main():
    """Run all authentication tests"""
    print("🚀 Starting Flask Authentication Tests\n")
    
    tests = [
        test_health_check,
        test_protected_endpoint_without_auth,
        test_protected_endpoint_with_invalid_auth,
        test_protected_endpoint_with_valid_auth,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Authentication middleware is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the implementation.")

if __name__ == "__main__":
    main()
