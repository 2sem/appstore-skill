#!/usr/bin/env python3
"""
App Store Reviews Fetcher
Usage: python fetch_reviews.py {app_id} [count]

Example:
    python fetch_reviews.py 123456789      # Fetch 1 review
    python fetch_reviews.py 123456789 5    # Fetch 5 reviews
"""

import jwt
import time
import requests
import sys
import os
import json

KEY_ID = None
ISSUER_ID = None
PRIVATE_KEY_PATH = None


def validate_config(key_id: str, issuer_id: str, private_key_path: str) -> bool:
    """Validate configuration and return True if valid"""
    errors = []

    if not key_id:
        errors.append("key_id is missing")
    if not issuer_id:
        errors.append("issuer_id is missing")
    if not private_key_path:
        errors.append("private_key_path is missing")
    elif not os.path.exists(private_key_path):
        errors.append(f"Private key file not found: {private_key_path}")

    if errors:
        print("ERROR: Invalid configuration!")
        for err in errors:
            print(f"  - {err}")
        return False
    return True


def load_config():
    """Load and validate configuration from skill directory"""
    global KEY_ID, ISSUER_ID, PRIVATE_KEY_PATH

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
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to read config: {e}")
        sys.exit(1)

    KEY_ID = KEY_ID or os.environ.get("APPSTORE_KEY_ID")
    ISSUER_ID = ISSUER_ID or os.environ.get("APPSTORE_ISSUER_ID")
    PRIVATE_KEY_PATH = PRIVATE_KEY_PATH or os.environ.get("APPSTORE_PRIVATE_KEY_PATH")

    if not validate_config(str(KEY_ID), str(ISSUER_ID), str(PRIVATE_KEY_PATH)):
        print()
        print("To configure, run: python setup_config.py")
        sys.exit(1)


def create_token():
    """Create JWT token for App Store Connect API"""
    load_config()

    if not PRIVATE_KEY_PATH:
        print("ERROR: Private key path not configured!")
        sys.exit(1)

    priv_key_path = PRIVATE_KEY_PATH  # type: ignore
    with open(priv_key_path, "r") as f:
        PRIVATE_KEY = f.read()

    now = int(time.time())
    payload = {"iss": ISSUER_ID, "exp": now + 1200, "aud": "appstoreconnect-v1"}
    headers = {"alg": "ES256", "kid": KEY_ID, "typ": "JWT"}
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="ES256", headers=headers)
    return token


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


def get_reviews(app_id: str, limit: int = 1):
    """Fetch reviews from App Store Connect API"""
    token = create_token()
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    reviews_url = (
        f"https://api.appstoreconnect.apple.com/v1/apps/{app_id}/customerReviews"
    )
    response = requests.get(
        reviews_url,
        params={"sort": "-createdDate", "limit": limit},
        headers=auth_headers,
    )

    if response.status_code != 200:
        raise Exception(
            f"Failed to get reviews: {response.status_code} - {response.text}"
        )

    reviews_data = response.json()
    return reviews_data.get("data", [])


def check_review_response(review_id: str):
    """Check if a review has a response"""
    token = create_token()
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = (
        f"https://api.appstoreconnect.apple.com/v1/customerReviews/{review_id}/response"
    )
    response = requests.get(url, headers=auth_headers)

    if response.status_code == 200:
        data = response.json()
        if data.get("data"):
            return True, data["data"].get("attributes", {}).get("body", "")
        return False, None
    elif response.status_code == 404:
        return False, None
    else:
        raise Exception(f"Error checking response: {response.text}")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python fetch_reviews.py reviews {app_id} [count]")
        print("  python fetch_reviews.py getappid {bundle_id}")
        print()
        print("Examples:")
        print("  python fetch_reviews.py reviews 123456789 5")
        print("  python fetch_reviews.py getappid com.credif.relatedstocks")
        sys.exit(1)

    command = sys.argv[1]

    if command == "getappid":
        if len(sys.argv) < 3:
            print("Usage: python fetch_reviews.py getappid {bundle_id}")
            print("Example: python fetch_reviews.py getappid com.credif.relatedstocks")
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
            print("\nUse this app ID for 'reviews' command.")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
        return

    if command == "reviews":
        if len(sys.argv) < 3:
            print("Usage: python fetch_reviews.py reviews {app_id} [count]")
            print("Example: python fetch_reviews.py reviews 1189758512 5")
            print()
            print("If you don't know the app ID, use main skill first:")
            print("  getappid com.credif.relatedstocks")
            sys.exit(1)
        app_id = sys.argv[2]
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    else:
        # Backward compatibility: treat first arg as app_id
        app_id = command
        count = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    print("=" * 70)
    print(f"APP STORE REVIEWS (Latest {count})")
    print("=" * 70)

    try:
        reviews = get_reviews(app_id, count)

        if not reviews:
            print("No reviews found!")
            return

        for i, review in enumerate(reviews, 1):
            review_id = review["id"]
            attrs = review["attributes"]

            print(f"\n--- Review #{i} ---")
            print(f"Review ID: {review_id}")
            print(f"Rating: {attrs['rating']} stars")
            print(f"Title: {attrs.get('title', 'N/A')}")
            print(f"Review: {attrs['body']}")
            print(f"Created: {attrs['createdDate']}")
            print(f"Territory: {attrs.get('territory', 'N/A')}")

            has_response, response_text = check_review_response(review_id)

            if has_response:
                print(f"Response: {response_text or '(empty)'}")
            else:
                print("Response: NEEDS RESPONSE")

        print("\n" + "=" * 70)
        print(f"Total: {len(reviews)} review(s)")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
