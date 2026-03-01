#!/usr/bin/env python3
"""
SSL Fix Helper - Run this if you have SSL certificate issues
"""
import os
import ssl
import httplib2

# Disable SSL verification (for development/testing only)
# NOT RECOMMENDED for production use
def disable_ssl_verification():
    print("⚠️  WARNING: Disabling SSL verification")
    print("   This is NOT secure and should only be used for testing")
    print("   with corporate proxies or firewall issues")

    # For httplib2
    httplib2.RETRIES = 1
    httplib2.Http.disable_ssl_certificate_validation = True

    # Set environment variables
    os.environ['PYTHONHTTPSVERIFY'] = '0'

    # Create unverified SSL context
    ssl._create_default_https_context = ssl._create_unverified_context

    print("✅ SSL verification disabled")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--confirm', action='store_true', help='Confirm you want to disable SSL verification')
    args = parser.parse_args()

    if args.confirm:
        disable_ssl_verification()
    else:
        print("To disable SSL verification (not recommended), run:")
        print("  python fix_ssl.py --confirm")
