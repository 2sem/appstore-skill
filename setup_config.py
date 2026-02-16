#!/usr/bin/env python3
"""
App Store CS Configuration Setup
Run this once to save your API credentials
"""

import os
import json


def main():
    print("=" * 60)
    print("App Store CS Configuration Setup")
    print("=" * 60)
    print()

    print("Enter your App Store Connect API credentials:")
    print()

    key_id = input("Key ID (e.g., UM6QWFFGHQ): ").strip()
    issuer_id = input(
        "Issuer ID (e.g., 69a6de91-d0d3-47e3-e053-5b8c7c11a4d1): "
    ).strip()
    private_key_path = input("Private key path (e.g., ~/github/cs.p8): ").strip()

    private_key_path = os.path.expanduser(private_key_path)

    if not all([key_id, issuer_id, private_key_path]):
        print("\nERROR: All fields are required!")
        return

    if not os.path.exists(private_key_path):
        print(f"\nWARNING: File not found at {private_key_path}")
        response = input("Continue anyway? (y/n): ").strip().lower()
        if response != "y":
            return

    config = {
        "key_id": key_id,
        "issuer_id": issuer_id,
        "private_key_path": private_key_path,
    }

    skill_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(skill_dir, "config.json")

    with open(config_path, "w") as f:
        json.dump(config, f)

    print()
    print("=" * 60)
    print("Configuration saved!")
    print(f"Config file: {config_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
