#!/usr/bin/env python3
"""
App Store Utility Commands
Usage:
    python appstore.py getappid {bundle_id}
"""

import jwt
import time
import requests
import sys
import os
import json


def load_config():
    """Load configuration from skill directory"""
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(skill_dir, "config.json")

    if not os.path.exists(config_path):
        print("ERROR: Config file not found!")
        print(f"Please run: python {os.path.join(skill_dir, 'setup_config.py')}")
        sys.exit(1)

    try:
        with open(config_path, "r") as f:
            config = json.load(f)
            KEY_ID = config.get("key_id")
            ISSUER_ID = config.get("issuer_id")
            PRIVATE_KEY_PATH = config.get("private_key_path")
    except Exception as e:
        print(f"ERROR: Failed to read config: {e}")
        sys.exit(1)

    KEY_ID = KEY_ID or os.environ.get("APPSTORE_KEY_ID")
    ISSUER_ID = ISSUER_ID or os.environ.get("APPSTORE_ISSUER_ID")
    PRIVATE_KEY_PATH = PRIVATE_KEY_PATH or os.environ.get("APPSTORE_PRIVATE_KEY_PATH")

    if not all([KEY_ID, ISSUER_ID, PRIVATE_KEY_PATH]):
        print("ERROR: Missing configuration!")
        sys.exit(1)

    return KEY_ID, ISSUER_ID, PRIVATE_KEY_PATH


def create_token():
    """Create JWT token for App Store Connect API"""
    KEY_ID, ISSUER_ID, PRIVATE_KEY_PATH = load_config()

    priv_key_path: str = PRIVATE_KEY_PATH  # type: ignore
    with open(priv_key_path, "r") as f:
        PRIVATE_KEY = f.read()

    now = int(time.time())
    payload = {"iss": ISSUER_ID, "exp": now + 1200, "aud": "appstoreconnect-v1"}
    headers = {"alg": "ES256", "kid": KEY_ID, "typ": "JWT"}
    return jwt.encode(payload, PRIVATE_KEY, algorithm="ES256", headers=headers)


def get_app_id_by_bundle_id(bundle_id: str):
    """Get numeric app ID from bundle ID"""
    token = create_token()
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = "https://api.appstoreconnect.apple.com/v1/apps"
    response = requests.get(
        url,
        params={"filter[bundleId]": bundle_id},
        headers=auth_headers,
    )

    if response.status_code != 200:
        raise Exception(f"Failed to find app: {response.status_code} - {response.text}")

    data = response.json()
    if not data.get("data"):
        raise Exception(f"App not found for bundle ID: {bundle_id}")

    app = data["data"][0]
    return app["id"], app["attributes"].get("name", "Unknown")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python appstore.py getappid {bundle_id}")
        print()
        print("Example:")
        print("  python appstore.py getappid com.credif.relatedstocks")
        sys.exit(1)

    command = sys.argv[1]

    if command == "getappid":
        if len(sys.argv) < 3:
            print("Usage: python appstore.py getappid {bundle_id}")
            print("Example: python appstore.py getappid com.credif.relatedstocks")
            sys.exit(1)
        bundle_id = sys.argv[2]
        print("=" * 70)
        print(f"GET APP ID FOR: {bundle_id}")
        print("=" * 70)
        try:
            app_id, app_name = get_app_id_by_bundle_id(bundle_id)
            print(f"\nApp Name: {app_name}")
            print(f"Bundle ID: {bundle_id}")
            print(f"Numeric App ID: {app_id}")
            print("\nUse this app ID for other commands.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        print(f"Unknown command: {command}")
        print("Available commands: getappid")
        sys.exit(1)


if __name__ == "__main__":
    main()
