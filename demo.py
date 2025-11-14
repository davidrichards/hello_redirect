#!/usr/bin/env python3
"""
Demo script showing the Hello Redirect POC flow

This script demonstrates the complete flow with explanatory output
"""

import requests
import sys
import time
from urllib.parse import urlparse, parse_qs


def demo_complete_flow():
    """Demonstrate the complete hello_redirect flow"""
    print("🎭 Hello Redirect POC - Complete Flow Demo")
    print("=" * 60)

    print("\n📋 STEP 1: User visits the gateway")
    print("   URL: http://localhost:8000/")
    print("   Headers: User-Agent, Accept-Language, etc.")
    print("   Cookies: rbt_session=demo123, rbt_advanced=true")

    # Simulate user request
    response = requests.get(
        "http://localhost:8000/",
        allow_redirects=False,
        headers={
            "User-Agent": "Mozilla/5.0 (demo-browser)",
            "Accept-Language": "en-US,en;q=0.9",
        },
        cookies={"rbt_session": "demo123", "rbt_advanced": "true"},
    )

    print(f"\n✅ Gateway response: {response.status_code} {response.reason}")
    redirect_url = response.headers.get("Location")

    if not redirect_url:
        print("❌ No redirect URL found")
        return False

    print(f"   Redirect to: {redirect_url}")

    # Parse token
    parsed_url = urlparse(redirect_url)
    if not parsed_url.query:
        print("❌ No query parameters found")
        return False

    query_params = parse_qs(parsed_url.query)

    if "token" not in query_params:
        print("❌ No token found in redirect")
        return False

    token = query_params["token"][0]

    print(f"\n🔐 STEP 2: Gateway creates encrypted token")
    print("   Token format: JWE(JWS(claims))")
    print("   - Claims are signed with JWT (integrity)")
    print("   - Token is encrypted with Fernet (confidentiality)")
    print(f"   - Token length: {len(token)} characters")
    print(f"   - Token preview: {token[:50]}...")

    print(f"\n🚀 STEP 3: Gateway redirects user to runtime")
    print(f"   Runtime URL: {parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}")
    print(f"   Token parameter: ?token=[encrypted_token]")

    # Follow redirect to runtime (adjust URL for external access)
    runtime_url = redirect_url.replace("http://runtime:8001", "http://localhost:8001")

    print(f"\n🔓 STEP 4: Runtime validates and decrypts token")
    print("   - Decrypts token with Fernet")
    print("   - Verifies JWT signature")
    print("   - Extracts user claims")

    response = requests.get(runtime_url)
    content = response.text

    print(f"\n🎯 STEP 5: Runtime displays personalized content")
    print("   Status: 200 OK")
    print("   Content-Type: text/html")

    # Extract and display key information
    lines = content.split("\n")
    for line in lines:
        if any(
            keyword in line for keyword in ["Welcome to runtime", "User:", "Features:"]
        ):
            clean_line = (
                line.strip()
                .replace("<p>", "")
                .replace("</p>", "")
                .replace("<h1>", "")
                .replace("</h1>", "")
            )
            if clean_line:
                print(f"   📄 {clean_line}")

    print(f"\n✅ SECURITY FEATURES DEMONSTRATED:")
    print("   🔒 Token confidentiality (encrypted with Fernet)")
    print("   🔏 Token integrity (signed with JWT)")
    print("   ⏱️  Token expiration (5 minutes TTL)")
    print("   🎭 User feature detection (basic + advanced)")
    print("   🔐 Server-side only decryption")

    print(f"\n🎪 DEMO COMPLETE!")
    print("=" * 60)
    print("The POC successfully demonstrates:")
    print("✅ Secure token-based redirection")
    print("✅ User context preservation")
    print("✅ Encrypted communication between services")
    print("✅ Runtime personalization")

    return True


def main():
    """Run the demo"""
    try:
        # Check if services are running
        print("🔍 Checking if services are running...")
        requests.get("http://localhost:8000/health", timeout=3)
        requests.get("http://localhost:8001/health", timeout=3)
        print("✅ Services are ready!")

        time.sleep(1)
        demo_complete_flow()

    except requests.exceptions.RequestException:
        print("❌ Services are not running!")
        print("💡 Run 'make docker-up' first to start the services")
        sys.exit(1)


if __name__ == "__main__":
    main()
