#!/usr/bin/env python3
"""
OBS Scanner Tool for Huawei Cloud Resource Manager

Scans OBS buckets and objects for public access configurations including:
- Bucket ACL with public-read or public-read-write
- Object-level ACL with public access
"""

import json
import subprocess
import logging
import os
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Public permission types to check
PUBLIC_PERMISSIONS = ["public-read", "public-read-write"]


def get_credentials() -> Dict[str, str]:
    """Get Huawei Cloud credentials from environment variables."""
    return {
        'access_key': os.environ.get('HWCLOUD_ACCESS_KEY', ''),
        'secret_key': os.environ.get('HWCLOUD_SECRET_KEY', ''),
        'project_id': os.environ.get('HWCLOUD_PROJECT_ID', '')
    }


def validate_env() -> None:
    """Validate required environment variables."""
    required = ['HWCLOUD_ACCESS_KEY', 'HWCLOUD_SECRET_KEY']
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def parse_hcloud_output(stdout: str) -> Optional[Dict[str, Any]]:
    """
    Parse hcloud CLI output, filtering out API version warnings.

    Args:
        stdout: Raw stdout from hcloud command

    Returns:
        Parsed JSON response or None if parsing fails
    """
    try:
        # Filter out warning lines and extract JSON
        lines = stdout.strip().split('\n')
        json_lines = []
        for line in lines:
            line = line.strip()
            # Skip empty lines and API version warnings
            if not line:
                continue
            if 'multi-version API' in line or line.startswith('List') or line.startswith('Get'):
                continue
            json_lines.append(line)

        if not json_lines:
            return None

        json_content = '\n'.join(json_lines)
        return json.loads(json_content)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output: {e}")
        logger.debug(f"Raw output: {stdout[:500]}")
        return None


def run_hcloud_command(
    command: List[str],
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Execute hcloud CLI command and return parsed JSON output.

    Args:
        command: Command and arguments as list
        region: Region to query
        credentials: Optional credentials dict

    Returns:
        Parsed JSON response or None if command fails
    """
    if credentials is None:
        credentials = get_credentials()

    # Build command with proper CLI parameters
    full_command = ["hcloud"] + command

    # Add authentication parameters
    if credentials.get('access_key'):
        full_command.extend([f"--cli-access-key={credentials['access_key']}"])
    if credentials.get('secret_key'):
        full_command.extend([f"--cli-secret-key={credentials['secret_key']}"])
    if credentials.get('project_id'):
        full_command.extend([f"--cli-project-id={credentials['project_id']}"])

    # Add region
    full_command.extend([f"--cli-region={region}"])

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error: {result.stderr}")
            return None

        return parse_hcloud_output(result.stdout)

    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {' '.join(command)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running command: {e}")
        return None


def get_bucket_acl(
    bucket_name: str,
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get ACL for a specific bucket.

    Args:
        bucket_name: Name of the bucket
        region: Region name
        credentials: Optional credentials dict

    Returns:
        Bucket ACL dictionary or None if failed
    """
    return run_hcloud_command(
        ["OBS", "GetBucketAcl", f"--bucket={bucket_name}"],
        region,
        credentials
    )


def check_bucket_public_access(bucket_acl: Dict[str, Any]) -> Optional[str]:
    """
    Check if bucket ACL allows public access.

    Args:
        bucket_acl: Bucket ACL dictionary

    Returns:
        Permission string if public access found, None otherwise
    """
    if not bucket_acl:
        return None

    # Check ACL grants
    grants = bucket_acl.get("grants", [])

    for grant in grants:
        permission = grant.get("permission", "").lower()
        grantee = grant.get("grantee", {})

        # Check for public access (AllUsers group)
        grantee_uri = grantee.get("uri", "")
        if "AllUsers" in grantee_uri:
            if permission in ["read", "public-read"]:
                return "public-read"
            elif permission in ["write", "public-read-write"]:
                return "public-read-write"

    # Check for public-read or public-read-write in ACL directly
    acl = bucket_acl.get("acl", "").lower()
    if acl in PUBLIC_PERMISSIONS:
        return acl

    return None


def list_objects(
    bucket_name: str,
    region: str,
    max_keys: int = 100,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    List objects in a bucket.

    Args:
        bucket_name: Name of the bucket
        region: Region name
        max_keys: Maximum number of objects to list
        credentials: Optional credentials dict

    Returns:
        List of object dictionaries
    """
    response = run_hcloud_command(
        ["OBS", "ListObjects", f"--bucket={bucket_name}", f"--max-keys={max_keys}"],
        region,
        credentials
    )

    if not response:
        return []

    # Handle different response formats
    if isinstance(response, dict):
        return response.get("contents", [])
    elif isinstance(response, list):
        return response

    return []


def get_object_acl(
    bucket_name: str,
    object_key: str,
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get ACL for a specific object.

    Args:
        bucket_name: Name of the bucket
        object_key: Object key (path)
        region: Region name
        credentials: Optional credentials dict

    Returns:
        Object ACL dictionary or None if failed
    """
    return run_hcloud_command(
        ["OBS", "GetObjectAcl", f"--bucket={bucket_name}", f"--key={object_key}"],
        region,
        credentials
    )


def check_object_public_access(object_acl: Dict[str, Any]) -> Optional[str]:
    """
    Check if object ACL allows public access.

    Args:
        object_acl: Object ACL dictionary

    Returns:
        Permission string if public access found, None otherwise
    """
    if not object_acl:
        return None

    # Check ACL grants
    grants = object_acl.get("grants", [])

    for grant in grants:
        permission = grant.get("permission", "").lower()
        grantee = grant.get("grantee", {})

        # Check for public access (AllUsers group)
        grantee_uri = grantee.get("uri", "")
        if "AllUsers" in grantee_uri:
            if permission in ["read", "public-read"]:
                return "public-read"
            elif permission in ["write", "public-read-write"]:
                return "public-read-write"

    # Check for public-read or public-read-write in ACL directly
    acl = object_acl.get("acl", "").lower()
    if acl in PUBLIC_PERMISSIONS:
        return acl

    return None


def scan_bucket_objects(
    bucket_name: str,
    region: str,
    max_objects: int = 100,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan objects in a bucket for public access.

    Args:
        bucket_name: Name of the bucket
        region: Region name
        max_objects: Maximum number of objects to check
        credentials: Optional credentials dict

    Returns:
        List of public objects
    """
    public_objects = []

    objects = list_objects(bucket_name, region, max_objects, credentials)

    for obj in objects:
        object_key = obj.get("key", "")
        if not object_key:
            continue

        object_acl = get_object_acl(bucket_name, object_key, region, credentials)
        public_permission = check_object_public_access(object_acl)

        if public_permission:
            public_objects.append({
                "key": object_key,
                "permission": public_permission,
                "size": obj.get("size", 0),
                "last_modified": obj.get("last_modified", "")
            })

    return public_objects


def scan_bucket(
    bucket: Dict[str, Any],
    region: str,
    check_objects: bool = True,
    credentials: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Scan a single bucket for public access issues.

    Args:
        bucket: Bucket dictionary
        region: Region name
        check_objects: Whether to check individual objects
        credentials: Optional credentials dict

    Returns:
        Issue details if public access found, None otherwise
    """
    bucket_name = bucket.get("name", "")
    if not bucket_name:
        return None

    # Get bucket ACL
    bucket_acl = get_bucket_acl(bucket_name, region, credentials)
    bucket_permission = check_bucket_public_access(bucket_acl)

    issue = None

    if bucket_permission:
        issue = {
            "bucket_name": bucket_name,
            "region": region,
            "issue_type": "public_bucket",
            "permission": bucket_permission,
            "risk_level": "high" if bucket_permission == "public-read-write" else "medium",
            "objects": [],
            "recommendation": "set_bucket_private"
        }

    # Check individual objects if bucket is not public or for detailed reporting
    if check_objects:
        public_objects = scan_bucket_objects(bucket_name, region, credentials=credentials)

        if public_objects:
            if issue:
                # Add public objects to existing bucket issue
                issue["objects"] = public_objects
            else:
                # Create issue for objects only
                issue = {
                    "bucket_name": bucket_name,
                    "region": region,
                    "issue_type": "public_objects",
                    "permission": public_objects[0].get("permission", "public-read"),
                    "risk_level": "medium",
                    "objects": public_objects,
                    "recommendation": "set_objects_private"
                }

    return issue


def list_buckets(
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    List all OBS buckets in a region.

    Args:
        region: Region name
        credentials: Optional credentials dict

    Returns:
        List of bucket dictionaries
    """
    response = run_hcloud_command(["OBS", "ListBuckets"], region, credentials)

    if not response:
        return []

    # Handle different response formats
    if isinstance(response, dict):
        return response.get("buckets", [])
    elif isinstance(response, list):
        return response

    return []


def scan_obs_buckets(
    regions: List[str],
    check_objects: bool = True,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan OBS buckets across multiple regions for public access.

    Args:
        regions: List of region names to scan
        check_objects: Whether to check individual object ACLs
        credentials: Optional credentials dict

    Returns:
        List of OBS issues found across all regions
    """
    # Validate environment before starting
    try:
        validate_env()
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        raise

    if credentials is None:
        credentials = get_credentials()

    all_issues = []

    logger.info(f"Starting OBS scan for {len(regions)} region(s)")

    for region in regions:
        logger.info(f"Scanning OBS in region: {region}")

        try:
            buckets = list_buckets(region, credentials)

            if not buckets:
                logger.info(f"No OBS buckets found in region {region}")
                continue

            logger.info(f"Found {len(buckets)} bucket(s) in {region}")

            for bucket in buckets:
                issue = scan_bucket(bucket, region, check_objects, credentials)

                if issue:
                    all_issues.append(issue)
                    logger.warning(
                        f"Found public access in bucket {issue['bucket_name']}: "
                        f"{issue['issue_type']} ({issue['permission']})"
                    )

        except Exception as e:
            logger.error(f"Error scanning OBS in region {region}: {e}")
            continue

    logger.info(f"OBS scan complete. Found {len(all_issues)} issue(s) total.")
    return all_issues


def main():
    """Main entry point for testing."""
    import os

    # Get regions from environment or use default
    regions_env = os.environ.get("HWCLOUD_REGIONS", "cn-north-4")
    regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    # Check if object scanning is enabled
    check_objects = os.environ.get("OBS_CHECK_OBJECTS", "true").lower() == "true"

    issues = scan_obs_buckets(regions, check_objects)

    # Output results as JSON
    print(json.dumps({"obs_issues": issues}, indent=2))


if __name__ == "__main__":
    main()
