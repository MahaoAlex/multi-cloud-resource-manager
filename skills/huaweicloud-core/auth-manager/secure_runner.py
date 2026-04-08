#!/usr/bin/env python3
"""
Secure runner for Huawei Cloud authentication.
Prevents sensitive credentials from appearing in command history or logs.
"""

import os
import sys
import getpass
import argparse


def secure_set_env():
    """
    Securely set environment variables for Huawei Cloud authentication.
    Uses interactive input to prevent credentials from appearing in shell history.
    """
    print("=" * 60)
    print("Secure Huawei Cloud Environment Setup")
    print("=" * 60)
    print()
    print("This script securely sets environment variables without exposing")
    print("credentials in command history or process listings.")
    print()

    # Check if already configured
    existing_ak = os.environ.get('HWCLOUD_ACCESS_KEY')
    if existing_ak:
        masked = '*' * (len(existing_ak) - 4) + existing_ak[-4:] if len(existing_ak) > 4 else '*' * len(existing_ak)
        print(f"Current Access Key: {masked}")
        overwrite = input("Overwrite existing credentials? (y/N): ").strip().lower()
        if overwrite != 'y':
            print("Keeping existing credentials.")
            return

    print()

    # Securely read Access Key
    while True:
        access_key = getpass.getpass("Enter Huawei Cloud Access Key ID: ").strip()
        if access_key:
            break
        print("Access Key ID cannot be empty. Please try again.")

    # Securely read Secret Key
    while True:
        secret_key = getpass.getpass("Enter Huawei Cloud Secret Access Key: ").strip()
        if len(secret_key) >= 20:
            break
        print("Secret Key must be at least 20 characters. Please try again.")

    # Read regions
    print()
    print("Enter regions (comma-separated, default: cn-north-4):")
    print("Examples: cn-north-4, cn-south-1, ap-southeast-1")
    regions = input("Regions: ").strip()
    if not regions:
        regions = "cn-north-4"

    # Read optional Project ID
    print()
    print("Enter Project ID (optional, press Enter to skip):")
    print("Note: Required for IAM sub-users")
    project_id = input("Project ID: ").strip()

    # Set environment variables
    os.environ['HWCLOUD_ACCESS_KEY'] = access_key
    os.environ['HWCLOUD_SECRET_KEY'] = secret_key
    os.environ['HWCLOUD_REGIONS'] = regions

    if project_id:
        os.environ['HWCLOUD_PROJECT_ID'] = project_id

    print()
    print("Environment variables set successfully.")
    print("These variables are only valid for the current session.")
    print("=" * 60)


def verify_env():
    """Verify that required environment variables are set."""
    required = ['HWCLOUD_ACCESS_KEY', 'HWCLOUD_SECRET_KEY', 'HWCLOUD_REGIONS']
    missing = [var for var in required if not os.environ.get(var)]

    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("Run this script with --setup to configure credentials.")
        sys.exit(1)

    # Show masked status
    ak = os.environ.get('HWCLOUD_ACCESS_KEY', '')
    regions = os.environ.get('HWCLOUD_REGIONS', '')
    masked_ak = '*' * (len(ak) - 4) + ak[-4:] if len(ak) > 4 else '*' * len(ak)

    print("Environment Status:")
    print(f"  HWCLOUD_ACCESS_KEY: {masked_ak}")
    print(f"  HWCLOUD_SECRET_KEY: {'*' * 20} (set)")
    print(f"  HWCLOUD_REGIONS: {regions}")
    if os.environ.get('HWCLOUD_PROJECT_ID'):
        print(f"  HWCLOUD_PROJECT_ID: {'*' * 20} (set)")


def main():
    parser = argparse.ArgumentParser(
        description="Securely set Huawei Cloud environment variables"
    )
    parser.add_argument(
        '--setup', '-s',
        action='store_true',
        help='Interactive setup of credentials'
    )
    parser.add_argument(
        '--verify', '-v',
        action='store_true',
        help='Verify environment variables are set'
    )

    args = parser.parse_args()

    if args.setup:
        secure_set_env()
    elif args.verify:
        verify_env()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
