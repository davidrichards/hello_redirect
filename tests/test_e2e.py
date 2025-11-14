#!/usr/bin/env python3
"""
End-to-end test for the hello_redirect POC

This script tests the complete flow:
1. Gateway receives request
2. Gateway allocates runtime and creates encrypted token
3. Gateway redirects to runtime with token
4. Runtime decrypts and validates token
5. Runtime displays user information
"""

import requests
import sys
import time
from urllib.parse import urlparse, parse_qs


def test_health_endpoints():
    """Test that both services are healthy"""
    print("🔍 Testing health endpoints...")

    # Test gateway health
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        response.raise_for_status()
        gateway_health = response.json()
        print(f"✅ Gateway health: {gateway_health}")
    except Exception as e:
        print(f"❌ Gateway health check failed: {e}")
        return False

    # Test runtime health
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        response.raise_for_status()
        runtime_health = response.json()
        print(f"✅ Runtime health: {runtime_health}")
    except Exception as e:
        print(f"❌ Runtime health check failed: {e}")
        return False

    return True


def test_gateway_redirect():
    """Test that gateway creates proper redirect with encrypted token"""
    print("🔍 Testing gateway redirect...")

    try:
        # Make request to gateway without following redirects
        response = requests.get(
            "http://localhost:8000/",
            allow_redirects=False,
            timeout=5,
            headers={
                "User-Agent": "python-requests/test-agent",
                "Accept-Language": "en-US,en;q=0.9",
            },
            cookies={"rbt_session": "test-session-123", "rbt_advanced": "true"},
        )

        if response.status_code != 307:
            print(f"❌ Expected 307 redirect, got {response.status_code}")
            return None

        redirect_url = response.headers.get("Location")
        if not redirect_url:
            print("❌ No redirect location found")
            return None

        print(f"✅ Gateway redirect: {redirect_url}")

        # Parse the redirect URL to extract token
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)

        if "token" not in query_params:
            print("❌ No token found in redirect URL")
            return None

        token = query_params["token"][0]
        print(f"✅ Encrypted token extracted (length: {len(token)})")

        return redirect_url

    except Exception as e:
        print(f"❌ Gateway redirect test failed: {e}")
        return None


def test_runtime_token_validation(redirect_url):
    """Test that runtime can validate and decrypt the token"""
    print("🔍 Testing runtime token validation...")

    try:
        # The redirect URL will point to the internal docker network (runtime:8001)
        # but we need to test from outside docker, so replace with localhost
        test_url = redirect_url.replace("http://runtime:8001", "http://localhost:8001")

        print(f"   📡 Following redirect: {test_url}")

        # Follow the redirect to the runtime
        response = requests.get(test_url, timeout=5)
        response.raise_for_status()

        content = response.text

        # Check that the response contains expected elements
        if "Welcome to runtime" not in content:
            print("❌ Runtime welcome message not found")
            return False

        if "User:" not in content:
            print("❌ User information not found in runtime response")
            return False

        if "Features:" not in content:
            print("❌ Features information not found in runtime response")
            return False

        if "Token was verified and decrypted" not in content:
            print("❌ Token verification message not found")
            return False

        print("✅ Runtime successfully validated and decrypted token")
        print("✅ Runtime displayed user information correctly")

        # Print some sample content for verification
        lines = content.split("\n")
        for line in lines:
            if any(
                keyword in line
                for keyword in ["User:", "Features:", "Welcome to runtime"]
            ):
                print(f"   📄 {line.strip()}")

        return True

    except Exception as e:
        print(f"❌ Runtime token validation failed: {e}")
        return False


def test_complete_flow():
    """Test the complete end-to-end flow"""
    print("🚀 Starting end-to-end test...")
    print("=" * 50)

    # Test 1: Health checks
    if not test_health_endpoints():
        print("❌ Health check failed - services may not be running")
        return False

    print()

    # Test 2: Gateway redirect
    redirect_url = test_gateway_redirect()
    if not redirect_url:
        print("❌ Gateway redirect failed")
        return False

    print()

    # Test 3: Runtime token validation
    if not test_runtime_token_validation(redirect_url):
        print("❌ Runtime token validation failed")
        return False

    print()
    print("🎉 End-to-end test completed successfully!")
    print("=" * 50)
    print("✅ Gateway receives requests and creates encrypted tokens")
    print("✅ Gateway redirects to runtime with secure tokens")
    print("✅ Runtime validates and decrypts tokens")
    print("✅ Runtime displays user information securely")

    return True


def wait_for_services(max_wait=30):
    """Wait for services to be ready"""
    print(f"⏳ Waiting for services to be ready (max {max_wait}s)...")

    start_time = time.time()
    while time.time() - start_time < max_wait:
        try:
            gateway_ready = (
                requests.get("http://localhost:8000/health", timeout=2).status_code
                == 200
            )
            runtime_ready = (
                requests.get("http://localhost:8001/health", timeout=2).status_code
                == 200
            )

            if gateway_ready and runtime_ready:
                print("✅ Services are ready!")
                return True

        except requests.exceptions.RequestException:
            pass

        time.sleep(1)
        print(".", end="", flush=True)

    print("\n❌ Services did not become ready in time")
    return False


if __name__ == "__main__":
    print("🔬 Hello Redirect POC - End-to-End Test")
    print("=" * 50)

    # Wait for services to be ready
    if not wait_for_services():
        print("💡 Make sure to run 'make docker-up' first")
        sys.exit(1)

    # Run the complete test
    success = test_complete_flow()

    if success:
        print("\n🎯 All tests passed! Your POC is working correctly.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check the logs above for details.")
        sys.exit(1)
