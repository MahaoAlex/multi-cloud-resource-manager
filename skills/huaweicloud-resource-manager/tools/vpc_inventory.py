#!/usr/bin/env python3
"""
VPC Inventory Tool for Huawei Cloud Resource Manager

Enumerates all VPC resources across multiple regions.
Supports pagination and outputs structured JSON with region information.
"""

import json
import subprocess
import logging
import os
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default page size for pagination
DEFAULT_PAGE_SIZE = 100


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
            if 'multi-version API' in line or line.startswith('List'):
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
        credentials: Optional credentials dict (access_key, secret_key, project_id)

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


def get_vpcs_in_region(
    region: str,
    credentials: Optional[Dict[str, str]] = None,
    page_size: int = DEFAULT_PAGE_SIZE
) -> List[Dict[str, Any]]:
    """
    Get all VPCs in a specific region with pagination support.

    Args:
        region: Region name
        credentials: Optional credentials dict
        page_size: Number of items per page

    Returns:
        List of VPC dictionaries
    """
    all_vpcs = []
    marker = None
    page_count = 0

    if credentials is None:
        credentials = get_credentials()

    while True:
        page_count += 1
        command = ["VPC", "ListVpcs", f"--limit={page_size}"]

        if marker:
            command.append(f"--marker={marker}")

        logger.debug(f"Fetching VPCs from {region}, page {page_count}")
        response = run_hcloud_command(command, region, credentials)

        if not response:
            logger.warning(f"Failed to get VPCs from region {region}")
            break

        # Handle different response formats
        vpcs = []
        if isinstance(response, dict):
            vpcs = response.get("vpcs", [])
            # Some APIs return items in 'resources' or directly as list
            if not vpcs and "resources" in response:
                vpcs = response.get("resources", [])
        elif isinstance(response, list):
            vpcs = response

        if not vpcs:
            break

        # Add region information to each VPC
        for vpc in vpcs:
            vpc["region"] = region

        all_vpcs.extend(vpcs)
        logger.debug(f"Retrieved {len(vpcs)} VPCs from {region}, page {page_count}")

        # Check for pagination marker
        if isinstance(response, dict):
            marker = response.get("marker") or response.get("next_marker")
            # If no more pages or we've reached the end
            if not marker or len(vpcs) < page_size:
                break
        else:
            # No pagination info in list response
            break

    logger.info(f"Retrieved {len(all_vpcs)} VPCs from region {region}")
    return all_vpcs


def format_vpc_data(vpc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format VPC data into standardized structure.

    Args:
        vpc: Raw VPC data from API

    Returns:
        Formatted VPC dictionary
    """
    return {
        "id": vpc.get("id") or vpc.get("vpc_id", "unknown"),
        "name": vpc.get("name", "unknown"),
        "cidr": vpc.get("cidr") or vpc.get("cidr_v4", "unknown"),
        "region": vpc.get("region", "unknown"),
        "status": vpc.get("status", "UNKNOWN"),
        "created_at": vpc.get("created_at") or vpc.get("create_time", ""),
        "description": vpc.get("description", ""),
        "enterprise_project_id": vpc.get("enterprise_project_id", "")
    }


def get_vpc_inventory(regions: List[str]) -> Dict[str, Any]:
    """
    Get VPC inventory across multiple regions.

    Args:
        regions: List of region names to scan

    Returns:
        Dictionary containing VPC inventory data
    """
    # Validate environment before starting
    try:
        validate_env()
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        raise

    credentials = get_credentials()
    all_vpcs = []
    regions_scanned = []
    failed_regions = []

    logger.info(f"Starting VPC inventory scan for {len(regions)} region(s)")

    for index, region in enumerate(regions, 1):
        logger.info(f"[{index}/{len(regions)}] Scanning region: {region}")

        try:
            vpcs = get_vpcs_in_region(region, credentials)

            if vpcs:
                formatted_vpcs = [format_vpc_data(vpc) for vpc in vpcs]
                all_vpcs.extend(formatted_vpcs)
                regions_scanned.append(region)
                logger.info(f"Found {len(vpcs)} VPC(s) in {region}")
            else:
                regions_scanned.append(region)
                logger.info(f"No VPCs found in {region}")

        except Exception as e:
            logger.error(f"Error scanning region {region}: {e}")
            failed_regions.append({"region": region, "error": str(e)})
            continue

    result = {
        "vpcs": all_vpcs,
        "regions_scanned": regions_scanned,
        "total_count": len(all_vpcs),
        "scan_metadata": {
            "requested_regions": regions,
            "successful_regions": regions_scanned,
            "failed_regions": failed_regions
        }
    }

    logger.info(f"VPC inventory complete. Total VPCs: {len(all_vpcs)}")
    return result


def main():
    """Main entry point for testing."""
    # Get regions from environment or use default
    regions_env = os.environ.get("HWCLOUD_REGIONS", "cn-north-4")

    if regions_env.lower() == "all":
        # Import known regions from auth_manager if available
        try:
            import sys
            sys.path.insert(0, '/home/alex/codebase/multi-cloud-resource-manager/skills/huaweicloud-core/auth-manager')
            from auth_manager import KNOWN_REGIONS
            regions = KNOWN_REGIONS
        except ImportError:
            regions = ["cn-north-4", "cn-south-1", "cn-east-2"]
    else:
        regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    inventory = get_vpc_inventory(regions)

    # Output results as JSON
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
