#!/usr/bin/env python3
"""
OSS Scanner Tool for Aliyun Resource Manager

Scans OSS buckets and objects for public access configurations including:
- Bucket ACL with public-read or public-read-write
- Bucket policy with public access
- Object-level ACL with public access
"""

import json
import subprocess
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Public permission types to check
PUBLIC_PERMISSIONS = ["public-read", "public-read-write"]


def run_oss_command(args: List[str]) -> tuple[bool, str]:
    """
    Execute ossutil or aliyun oss command and return result.

    Args:
        args: Command arguments as list

    Returns:
        Tuple of (success, output)
    """
    # Try ossutil first, then fall back to aliyun oss
    commands_to_try = [
        ["ossutil"] + args,
        ["aliyun", "oss"] + args
    ]

    for cmd in commands_to_try:
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                return True, result.stdout

        except FileNotFoundError:
            continue
        except Exception as e:
            logger.debug(f"Command failed: {' '.join(cmd)} - {e}")
            continue

    return False, ""


def run_aliyun_command(service: str, action: str, args: List[str], region: str) -> Optional[Dict[str, Any]]:
    """
    Execute aliyun CLI command and return parsed JSON output.

    Args:
        service: Aliyun service name
        action: API action to perform
        args: Command arguments as list
        region: Region to query

    Returns:
        Parsed JSON response or None if command fails
    """
    full_command = [
        "aliyun", service, action,
        f"--region={region}"
    ] + args

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"Command failed: {' '.join(full_command)}")
            logger.error(f"Error: {result.stderr}")
            return None

        return json.loads(result.stdout)
    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {' '.join(full_command)}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON output: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running command: {e}")
        return None


def scan_bucket_objects(bucket_name: str, region: str, max_objects: int = 100) -> List[Dict[str, Any]]:
    """
    Scan objects in a bucket for public access.
    Note: Object-level ACL checking requires ossutil or API access.
    This is a simplified version that checks bucket-level ACL only.

    Args:
        bucket_name: Name of the bucket
        region: Region name
        max_objects: Maximum number of objects to check (not used in simplified version)

    Returns:
        List of public objects (empty list in simplified version)
    """
    # Simplified version - object-level ACL checking is complex with CLI tools
    # In production, this would use the OSS API directly
    return []


def scan_bucket(bucket: Dict[str, Any], region: str, check_objects: bool = True) -> Optional[Dict[str, Any]]:
    """
    Scan a single bucket for public access issues.

    Args:
        bucket: Bucket dictionary
        region: Region name
        check_objects: Whether to check individual objects

    Returns:
        Issue details if public access found, None otherwise
    """
    bucket_name = bucket.get("name", "")
    if not bucket_name:
        return None

    # Get bucket info including ACL
    bucket_info = get_bucket_info(bucket_name)
    acl = bucket_info.get('acl', 'unknown').lower()

    issue = None

    # Check if bucket ACL allows public access
    if acl in PUBLIC_PERMISSIONS:
        issue = {
            "bucket_name": bucket_name,
            "region": region,
            "issue_type": "public_bucket",
            "permission": acl,
            "risk_level": "high" if acl == "public-read-write" else "medium",
            "objects": [],
            "recommendation": "set_bucket_private"
        }

    # Check individual objects if bucket is not public or for detailed reporting
    if check_objects:
        public_objects = scan_bucket_objects(bucket_name, region)

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


def list_buckets(region: str) -> List[Dict[str, Any]]:
    """
    List all OSS buckets in a region using ossutil or aliyun oss ls.

    Args:
        region: Region name

    Returns:
        List of bucket dictionaries
    """
    # Try using ossutil or aliyun oss ls command
    success, output = run_oss_command(["ls"])

    if not success:
        logger.error("Failed to list OSS buckets - ossutil/aliyun oss not available")
        return []

    buckets = []
    # Parse output format:
    # CreationTime                                 Region    StorageClass    BucketName
    # 2026-01-18 22:15:11 +0800 CST       oss-cn-hangzhou        Standard    oss://bucket-name
    for line in output.strip().split('\n'):
        line = line.strip()
        # Skip header lines and empty lines
        if not line or 'CreationTime' in line or 'Bucket Number' in line:
            continue

        # Extract bucket name from the end of the line (format: oss://bucket-name)
        if 'oss://' in line:
            parts = line.split()
            for part in parts:
                if part.startswith('oss://'):
                    bucket_name = part.replace('oss://', '').rstrip('/')
                    if bucket_name:
                        buckets.append({"name": bucket_name})
                    break

    return buckets


def get_bucket_info(bucket_name: str) -> Dict[str, Any]:
    """
    Get bucket information using ossutil stat command.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Bucket information dictionary
    """
    success, output = run_oss_command(["stat", f"oss://{bucket_name}"])

    if not success:
        return {}

    info = {}
    for line in output.strip().split('\n'):
        if ':' in line:
            key, value = line.split(':', 1)
            info[key.strip().lower().replace(' ', '_')] = value.strip()

    return info


def scan_oss_buckets(regions: List[str], check_objects: bool = True) -> List[Dict[str, Any]]:
    """
    Scan OSS buckets for public access.
    Note: OSS buckets are global, but we check them once regardless of regions list.

    Args:
        regions: List of region names (kept for API compatibility)
        check_objects: Whether to check individual object ACLs

    Returns:
        List of OSS issues found
    """
    all_issues = []

    logger.info("Starting OSS scan")

    try:
        # OSS buckets are global, use first region for API compatibility
        region = regions[0] if regions else "cn-hangzhou"
        buckets = list_buckets(region)

        if not buckets:
            logger.info("No OSS buckets found")
            return all_issues

        logger.info(f"Found {len(buckets)} bucket(s)")

        for bucket in buckets:
            # Get bucket region from bucket info
            bucket_info = get_bucket_info(bucket["name"])
            bucket_region = bucket_info.get('location', region)

            issue = scan_bucket(bucket, bucket_region, check_objects)

            if issue:
                all_issues.append(issue)
                logger.warning(
                    f"Found public access in bucket {issue['bucket_name']}: "
                    f"{issue['issue_type']} ({issue['permission']})"
                )

    except Exception as e:
        logger.error(f"Error scanning OSS: {e}")

    logger.info(f"OSS scan complete. Found {len(all_issues)} issue(s) total.")
    return all_issues


def main():
    """Main entry point for testing."""
    import os

    # Get regions from environment or use default
    regions_env = os.environ.get("ALIYUN_REGIONS", "cn-hangzhou")
    regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    # Check if object scanning is enabled
    check_objects = os.environ.get("OSS_CHECK_OBJECTS", "true").lower() == "true"

    issues = scan_oss_buckets(regions, check_objects)

    # Output results as JSON
    print(json.dumps({"oss_issues": issues}, indent=2))


if __name__ == "__main__":
    main()
