#!/usr/bin/env python3
"""
Authentication manager module for Huawei Cloud CLI.
Handles credential configuration, validation, and environment setup.
"""

import os
import subprocess
import re
import json
from getpass import getpass
from typing import List, Tuple, Dict, Optional


# Default Huawei Cloud regions
DEFAULT_REGIONS = ["cn-north-4"]

# All known Huawei Cloud regions
KNOWN_REGIONS = [
    "cn-north-1", "cn-north-4", "cn-north-9",
    "cn-south-1", "cn-south-4",
    "cn-east-2", "cn-east-3",
    "cn-southwest-2",
    "ap-southeast-1", "ap-southeast-2", "ap-southeast-3",
    "af-south-1",
    "sa-brazil-1",
    "na-mexico-1",
    "la-south-2"
]


def mask_string(value: str, visible_chars: int = 4) -> str:
    """
    Mask a string, showing only last few characters.

    Args:
        value: String to mask
        visible_chars: Number of characters to show at end

    Returns:
        Masked string
    """
    if not value:
        return ""
    if len(value) <= visible_chars:
        return "*" * len(value)
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def validate_access_key(access_key: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Access Key ID format.

    Args:
        access_key: Access Key ID to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not access_key:
        return False, "Access Key ID is required."

    if len(access_key) < 10:
        return False, "Access Key ID must be at least 10 characters."

    # Huawei Cloud AK typically starts with specific prefixes
    # but we'll be lenient and just check for alphanumeric
    if not re.match(r'^[A-Za-z0-9_-]+$', access_key):
        return False, "Access Key ID contains invalid characters."

    return True, None


def validate_secret_key(secret_key: str) -> Tuple[bool, Optional[str]]:
    """
    Validate Secret Access Key format.

    Args:
        secret_key: Secret Access Key to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not secret_key:
        return False, "Secret Access Key is required."

    if len(secret_key) < 20:
        return False, "Secret Access Key must be at least 20 characters."

    return True, None


def parse_regions(regions_input: str) -> List[str]:
    """
    Parse regions input into list of region IDs.

    Args:
        regions_input: Comma-separated regions or 'all'

    Returns:
        List of region IDs
    """
    if not regions_input or regions_input.strip().lower() == 'all':
        return KNOWN_REGIONS.copy()

    # Split by comma and clean up
    regions = [r.strip() for r in regions_input.split(',') if r.strip()]

    # Remove duplicates while preserving order
    seen = set()
    unique_regions = []
    for r in regions:
        if r not in seen:
            seen.add(r)
            unique_regions.append(r)

    return unique_regions if unique_regions else DEFAULT_REGIONS


def get_project_id(access_key: str, secret_key: str, region: str) -> Optional[str]:
    """
    Try to discover project ID from IAM API.

    Args:
        access_key: Access Key ID
        secret_key: Secret Access Key
        region: Region ID

    Returns:
        Project ID if found, None otherwise
    """
    try:
        env = os.environ.copy()
        env['HWCLOUD_ACCESS_KEY'] = access_key
        env['HWCLOUD_SECRET_KEY'] = secret_key

        # Query IAM for projects
        result = subprocess.run(
            ['hcloud', 'IAM', 'KeystoneListAuthProjects',
             f'--cli-access-key={access_key}',
             f'--cli-secret-key={secret_key}',
             f'--cli-region={region}'],
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            # Parse output to extract project ID
            output_lines = result.stdout.strip().split('\n')
            json_lines = []
            for line in output_lines:
                if line.strip() and 'multi-version API' not in line:
                    json_lines.append(line)

            if json_lines:
                try:
                    data = json.loads('\n'.join(json_lines))
                    projects = data.get('projects', [])
                    if projects:
                        # Find the default project for this region
                        for proj in projects:
                            if region in proj.get('name', ''):
                                return proj.get('id')
                        # Return first project if no match
                        return projects[0].get('id')
                except json.JSONDecodeError:
                    pass

        return None

    except Exception:
        return None


def validate_region(access_key: str, secret_key: str, region: str, project_id: str = None) -> Tuple[bool, Optional[str]]:
    """
    Validate credentials against a specific region using hcloud CLI.

    Args:
        access_key: Huawei Cloud Access Key ID
        secret_key: Huawei Cloud Secret Access Key
        region: Region ID to validate against
        project_id: Optional Project ID for IAM sub-users

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Build command with authentication
        cmd = ['hcloud', 'VPC', 'ListVpcs',
               f'--cli-access-key={access_key}',
               f'--cli-secret-key={secret_key}',
               f'--cli-region={region}']

        if project_id:
            cmd.append(f'--cli-project-id={project_id}')

        # Run hcloud vpc ListVpcs to validate credentials
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return True, None

        # Check for specific error messages
        stderr = result.stderr.lower()
        stdout = result.stdout.lower()

        if 'unauthorized' in stderr or 'authentication' in stderr:
            return False, "Authentication failed. Please check your credentials."
        if 'project' in stderr or 'project' in stdout:
            if not project_id:
                return False, f"Project ID required. This account may be an IAM sub-user."
            else:
                return False, f"Invalid Project ID for region '{region}'."
        if 'region' in stderr:
            return False, f"Region '{region}' not found or not accessible."

        return False, f"Validation failed: {result.stderr.strip() or 'Unknown error'}"

    except subprocess.TimeoutExpired:
        return False, "Connection timeout. Please check your network or proxy settings."
    except FileNotFoundError:
        return False, "hcloud CLI not found. Please install Huawei Cloud CLI."
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def configure_auth(access_key: str, secret_key: str, regions: List[str], project_id: str = None) -> Dict:
    """
    Configure authentication environment variables.

    Args:
        access_key: Huawei Cloud Access Key ID
        secret_key: Huawei Cloud Secret Access Key
        regions: List of region IDs
        project_id: Optional Project ID (strongly recommended for IAM sub-users)

    Returns:
        dict: Configuration result with status
    """
    result = {
        "success": False,
        "configured": [],
        "errors": [],
        "validated_regions": [],
        "failed_regions": [],
        "masked_access_key": mask_string(access_key),
        "project_id": project_id
    }

    # Validate input
    ak_valid, ak_error = validate_access_key(access_key)
    if not ak_valid:
        result["errors"].append(f"Access Key: {ak_error}")
        return result

    sk_valid, sk_error = validate_secret_key(secret_key)
    if not sk_valid:
        result["errors"].append(f"Secret Key: {sk_error}")
        return result

    # Try to auto-discover project ID if not provided
    if not project_id and regions:
        print("  Attempting to discover Project ID...")
        discovered = get_project_id(access_key, secret_key, regions[0])
        if discovered:
            print(f"  Discovered Project ID: {discovered}")
            project_id = discovered
            result["project_id"] = project_id
        else:
            print("  Could not auto-discover Project ID.")

    # Validate credentials against each region
    print("\nValidating credentials...")
    for region in regions:
        is_valid, error = validate_region(access_key, secret_key, region, project_id)
        if is_valid:
            result["validated_regions"].append(region)
            print(f"  Region {region}: OK")
        else:
            result["failed_regions"].append({"region": region, "error": error})
            print(f"  Region {region}: FAILED - {error}")

    # Only proceed if at least one region validated successfully
    if not result["validated_regions"]:
        result["errors"].append("No regions could be validated. Please check your credentials and network.")
        if not project_id:
            result["errors"].append("Hint: If using an IAM sub-user, Project ID is required.")
        return result

    # Set environment variables
    os.environ['HWCLOUD_ACCESS_KEY'] = access_key
    os.environ['HWCLOUD_SECRET_KEY'] = secret_key
    os.environ['HWCLOUD_REGIONS'] = ','.join(result["validated_regions"])

    result["configured"].extend(['HWCLOUD_ACCESS_KEY', 'HWCLOUD_SECRET_KEY', 'HWCLOUD_REGIONS'])

    if project_id:
        os.environ['HWCLOUD_PROJECT_ID'] = project_id
        result["configured"].append('HWCLOUD_PROJECT_ID')

    result["success"] = True
    return result


def get_current_auth_config() -> Dict[str, str]:
    """
    Get current authentication configuration from environment.

    Returns:
        dict: Current auth settings with masked values
    """
    access_key = os.environ.get('HWCLOUD_ACCESS_KEY', '')
    secret_key = os.environ.get('HWCLOUD_SECRET_KEY', '')

    return {
        "HWCLOUD_ACCESS_KEY": mask_string(access_key) if access_key else "",
        "HWCLOUD_SECRET_KEY": mask_string(secret_key) if secret_key else "",
        "HWCLOUD_REGIONS": os.environ.get('HWCLOUD_REGIONS', ''),
        "HWCLOUD_PROJECT_ID": os.environ.get('HWCLOUD_PROJECT_ID', '')
    }


def interactive_auth_setup():
    """
    Run interactive authentication configuration.
    Prompts user for credentials and validates them.

    Returns:
        dict: Configuration result
    """
    print("=" * 60)
    print("Huawei Cloud Authentication Configuration")
    print("=" * 60)
    print()
    print("Configure authentication credentials for hcloud CLI.")
    print("Your credentials will be validated before being applied.")
    print()
    print("NOTE: For IAM sub-users, Project ID is required.")
    print("      Main account users can leave Project ID blank.")
    print()

    # Show current configuration
    current = get_current_auth_config()
    if any(current.values()):
        print("Current configuration:")
        for key, value in current.items():
            if value:
                print(f"  {key}: {value}")
        print()

    # Prompt for credentials
    print("Enter your Huawei Cloud credentials:")
    print()

    access_key = getpass("Access Key ID: ").strip()
    if not access_key:
        print("Error: Access Key ID is required.")
        return {"success": False, "errors": ["Access Key ID is required."]}

    secret_key = getpass("Secret Access Key: ").strip()
    if not secret_key:
        print("Error: Secret Access Key is required.")
        return {"success": False, "errors": ["Secret Access Key is required."]}

    print()
    print("Available regions:")
    print(f"  {', '.join(KNOWN_REGIONS[:5])}, ...")
    print(f"  (and {len(KNOWN_REGIONS) - 5} more)")
    print()
    print("Enter regions to use (comma-separated) or 'all' for all regions:")
    regions_input = input(f"Regions [default: {','.join(DEFAULT_REGIONS)}]: ").strip()

    regions = parse_regions(regions_input if regions_input else ','.join(DEFAULT_REGIONS))

    # Project ID - strongly recommended for IAM sub-users
    print()
    print("Project ID:")
    print("  - Required for IAM sub-users")
    print("  - Optional for main account users")
    print("  - Format: 32-character hex string (e.g., b6c0fd8b70114e2fad507fb0f2f39227)")
    project_id = input("Project ID (press Enter to skip): ").strip()

    print()

    # Configure authentication
    result = configure_auth(
        access_key=access_key,
        secret_key=secret_key,
        regions=regions,
        project_id=project_id if project_id else None
    )

    # Display results
    print()
    if result["success"]:
        print("Authentication configured successfully.")
        print()
        print("Environment variables set:")
        for var in result["configured"]:
            if var == 'HWCLOUD_ACCESS_KEY':
                print(f"  {var}={result['masked_access_key']}")
            elif var == 'HWCLOUD_SECRET_KEY':
                print(f"  {var}=****************")
            else:
                print(f"  {var}={os.environ.get(var, '')}")

        print()
        print(f"Validated regions ({len(result['validated_regions'])}):")
        for region in result["validated_regions"]:
            print(f"  - {region}")

        if result["failed_regions"]:
            print()
            print(f"Failed regions ({len(result['failed_regions'])}):")
            for fail in result["failed_regions"]:
                print(f"  - {fail['region']}: {fail['error']}")

        # Warn if no project_id for IAM sub-users
        if not result.get("project_id"):
            print()
            print("WARNING: No Project ID configured.")
            print("         If you are an IAM sub-user, please reconfigure with Project ID.")
    else:
        print("Configuration failed:")
        for error in result["errors"]:
            print(f"  - {error}")

    print()
    print("Note: These settings are only valid for the current session.")
    print("=" * 60)

    return result


if __name__ == "__main__":
    interactive_auth_setup()
