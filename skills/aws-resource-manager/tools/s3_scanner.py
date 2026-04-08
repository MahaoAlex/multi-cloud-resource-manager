#!/usr/bin/env python3
"""
S3 Scanner Tool for AWS Resource Manager

Scans S3 buckets for public access configurations including:
- Bucket ACL with public-read or public-read-write
- Bucket policy with public access
- Block Public Access settings
"""

import json
import subprocess
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_aws_command(service: str, operation: str, args: List[str], region: str = "us-east-1") -> Optional[Dict[str, Any]]:
    """
    Execute AWS CLI command and return parsed JSON output.

    Args:
        service: AWS service name
        operation: API operation
        args: Command arguments as list
        region: Region to query (S3 is global but API calls need a region)

    Returns:
        Parsed JSON response or None if command fails
    """
    full_command = [
        "aws", service, operation,
        "--region", region,
        "--output", "json"
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


def get_bucket_acl(bucket_name: str) -> Optional[Dict[str, Any]]:
    """
    Get ACL for a specific bucket.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Bucket ACL dictionary or None if failed
    """
    return run_aws_command(
        "s3api", "get-bucket-acl",
        ["--bucket", bucket_name]
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

    grants = bucket_acl.get("Grants", [])

    for grant in grants:
        grantee = grant.get("Grantee", {})
        permission = grant.get("Permission", "")

        # Check for AllUsers (public access)
        if grantee.get("URI") == "http://acs.amazonaws.com/groups/global/AllUsers":
            if permission == "READ":
                return "public-read"
            elif permission == "WRITE":
                return "public-read-write"

        # Check for AuthenticatedUsers (authenticated users access)
        if grantee.get("URI") == "http://acs.amazonaws.com/groups/global/AuthenticatedUsers":
            if permission in ["READ", "WRITE"]:
                return "authenticated-users"

    return None


def get_bucket_policy(bucket_name: str) -> Optional[Dict[str, Any]]:
    """
    Get policy for a specific bucket.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Bucket policy dictionary or None if failed
    """
    result = run_aws_command(
        "s3api", "get-bucket-policy",
        ["--bucket", bucket_name]
    )

    if not result:
        return None

    # Policy is returned as a string, need to parse it
    policy_str = result.get("Policy", "")
    if policy_str:
        try:
            return json.loads(policy_str)
        except json.JSONDecodeError:
            return None

    return None


def check_bucket_policy_public_access(policy: Dict[str, Any]) -> bool:
    """
    Check if bucket policy allows public access.

    Args:
        policy: Bucket policy dictionary

    Returns:
        True if public access found, False otherwise
    """
    if not policy:
        return False

    statements = policy.get("Statement", [])

    for statement in statements:
        principal = statement.get("Principal", {})

        # Check for wildcard principal
        if isinstance(principal, str) and principal == "*":
            return True
        if isinstance(principal, dict) and principal.get("AWS") == "*":
            return True
        if isinstance(principal, list) and "*" in principal:
            return True

    return False


def get_bucket_public_access_block(bucket_name: str) -> Optional[Dict[str, Any]]:
    """
    Get public access block configuration for a bucket.

    Args:
        bucket_name: Name of the bucket

    Returns:
        Public access block configuration or None
    """
    return run_aws_command(
        "s3api", "get-public-access-block",
        ["--bucket", bucket_name]
    )


def check_public_access_block(block_config: Dict[str, Any]) -> bool:
    """
    Check if public access is blocked at bucket level.

    Args:
        block_config: Public access block configuration

    Returns:
        True if public access is fully blocked, False otherwise
    """
    if not block_config:
        return False

    config = block_config.get("PublicAccessBlockConfiguration", {})

    return all([
        config.get("BlockPublicAcls", False),
        config.get("IgnorePublicAcls", False),
        config.get("BlockPublicPolicy", False),
        config.get("RestrictPublicBuckets", False)
    ])


def scan_bucket(bucket_name: str, region: str, check_objects: bool = False) -> Optional[Dict[str, Any]]:
    """
    Scan a single bucket for public access issues.

    Args:
        bucket_name: Name of the bucket
        region: Region name
        check_objects: Whether to check individual objects

    Returns:
        Issue details if public access found, None otherwise
    """
    # Get bucket ACL
    bucket_acl = get_bucket_acl(bucket_name)
    bucket_permission = check_bucket_public_access(bucket_acl)

    # Get bucket policy
    bucket_policy = get_bucket_policy(bucket_name)
    has_public_policy = check_bucket_policy_public_access(bucket_policy)

    # Get public access block
    block_config = get_bucket_public_access_block(bucket_name)
    is_blocked = check_public_access_block(block_config)

    # If fully blocked, no public access issue
    if is_blocked and not bucket_permission and not has_public_policy:
        return None

    issue = None

    if bucket_permission or has_public_policy:
        issue = {
            "bucket_name": bucket_name,
            "region": region,
            "issue_type": "public_bucket",
            "permission": bucket_permission if bucket_permission else "public-policy",
            "risk_level": "high" if bucket_permission == "public-read-write" or has_public_policy else "medium",
            "has_public_access_block": is_blocked,
            "objects": [],
            "recommendation": "enable_public_access_block" if not is_blocked else "review_bucket_acl_and_policy"
        }

    return issue


def list_buckets() -> List[Dict[str, Any]]:
    """
    List all S3 buckets.

    Returns:
        List of bucket dictionaries
    """
    response = run_aws_command("s3api", "list-buckets", [])

    if not response:
        return []

    buckets = response.get("Buckets", [])

    # Get bucket locations
    result = []
    for bucket in buckets:
        bucket_name = bucket.get("Name", "")
        if bucket_name:
            # Get bucket location
            location_response = run_aws_command(
                "s3api", "get-bucket-location",
                ["--bucket", bucket_name]
            )
            region = location_response.get("LocationConstraint", "us-east-1") if location_response else "us-east-1"
            if region is None:
                region = "us-east-1"

            result.append({
                "name": bucket_name,
                "region": region,
                "creation_date": bucket.get("CreationDate", "")
            })

    return result


def scan_s3_buckets(regions: List[str], check_objects: bool = False) -> List[Dict[str, Any]]:
    """
    Scan S3 buckets for public access.

    Args:
        regions: List of region names to scan (for filtering)
        check_objects: Whether to check individual object ACLs

    Returns:
        List of S3 issues found
    """
    all_issues = []

    logger.info("Starting S3 scan")

    try:
        buckets = list_buckets()

        if not buckets:
            logger.info("No S3 buckets found")
            return []

        logger.info(f"Found {len(buckets)} bucket(s)")

        for bucket in buckets:
            bucket_name = bucket.get("name", "")
            bucket_region = bucket.get("region", "us-east-1")

            # Filter by region if specified
            if regions and bucket_region not in regions:
                continue

            try:
                issue = scan_bucket(bucket_name, bucket_region, check_objects)

                if issue:
                    all_issues.append(issue)
                    logger.warning(
                        f"Found public access in bucket {issue['bucket_name']}: "
                        f"{issue['issue_type']} ({issue['permission']})"
                    )
            except Exception as e:
                logger.error(f"Error scanning bucket {bucket_name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scanning S3: {e}")

    logger.info(f"S3 scan complete. Found {len(all_issues)} issue(s) total.")
    return all_issues


def main():
    """Main entry point for testing."""
    import os

    # Get regions from environment or use default
    regions_env = os.environ.get("AWS_REGIONS", "us-east-1")
    regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    # Check if object scanning is enabled
    check_objects = os.environ.get("S3_CHECK_OBJECTS", "false").lower() == "true"

    issues = scan_s3_buckets(regions, check_objects)

    # Output results as JSON
    print(json.dumps({"s3_issues": issues}, indent=2))


if __name__ == "__main__":
    main()
