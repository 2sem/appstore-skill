#!/usr/bin/env python3
"""
App Store Review Response Submitter
Usage: python submit_response.py {review_id} "{response_text}"

Example:
    python submit_response.py 00000046-ea46-3002-cf40-2d5b00000000 "Thank you for your feedback!"
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

    priv_key_path: str = PRIVATE_KEY_PATH  # type: ignore
    with open(priv_key_path, "r") as f:
        PRIVATE_KEY = f.read()

    now = int(time.time())
    payload = {"iss": ISSUER_ID, "exp": now + 1200, "aud": "appstoreconnect-v1"}
    headers = {"alg": "ES256", "kid": KEY_ID, "typ": "JWT"}
    token = jwt.encode(payload, PRIVATE_KEY, algorithm="ES256", headers=headers)
    return token


def check_review_response(review_id: str):
    """Check if a review already has a response"""
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


def submit_response(review_id: str, response_text: str):
    """Submit a response to a review

    CRITICAL: Use 'responseBody' NOT 'body' in the payload!
    Using 'body' will cause a 409 Conflict error.
    """
    token = create_token()
    auth_headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    url = "https://api.appstoreconnect.apple.com/v1/customerReviewResponses"

    # CRITICAL: Use responseBody, NOT body!
    payload = {
        "data": {
            "attributes": {
                "responseBody": response_text  # This must be 'responseBody', NOT 'body'!
            },
            "type": "customerReviewResponses",
            "relationships": {
                "review": {"data": {"id": review_id, "type": "customerReviews"}}
            },
        }
    }

    response = requests.post(url, json=payload, headers=auth_headers)

    if response.status_code not in [200, 201]:
        raise Exception(
            f"Failed to submit response: {response.status_code} - {response.text}"
        )

    return response.json()


def main():
    if len(sys.argv) < 3:
        print('Usage: python submit_response.py {review_id} "{response_text}"')
        print(
            'Example: python submit_response.py 00000046-ea46-3002-cf40-2d5b00000000 "Thank you!"'
        )
        sys.exit(1)

    review_id = sys.argv[1]
    response_text = sys.argv[2]

    print("=" * 70)
    print("SUBMIT REVIEW RESPONSE")
    print("=" * 70)
    print(f"Review ID: {review_id}")
    print(f"Response: {response_text}")
    print()

    try:
        # Check if already responded
        has_response, existing = check_review_response(review_id)

        if has_response:
            print(f"WARNING: Review already has a response: {existing or '(empty)'}")
            print("Skipping submission.")
            return

        # Submit response
        result = submit_response(review_id, response_text)

        print("SUCCESS: Response submitted!")
        print(f"Response ID: {result.get('data', {}).get('id', 'N/A')}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
