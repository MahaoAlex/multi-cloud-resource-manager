#!/usr/bin/env python3
"""
VPC Inventory Tool for Aliyun Resource Manager

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
DEFAULT_PAGE_SIZE = 50


def run_aliyun_command(action: str, args: List[str], region: str) -> Optional[Dict[str, Any]]:
    """
    Execute aliyun CLI command and return parsed JSON output.

    Args:
        action: API action to perform
        args: Command arguments as list
        region: Region to query

    Returns:
        Parsed JSON response or None if command fails
    """
    full_command = [
        "aliyun", "vpc", action,
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


def get_vpcs_in_region(region: str, page_size: int = DEFAULT_PAGE_SIZE) -> List[Dict[str, Any]]:
    """
    Get all VPCs in a specific region with pagination support.

    Args:
        region: Region name
        page_size: Number of items per page

    Returns:
        List of VPC dictionaries
    """
    all_vpcs = []
    page_number = 1

    while True:
        args = [
            f"--PageSize={page_size}",
            f"--PageNumber={page_number}"
        ]

        logger.debug(f"Fetching VPCs from {region}, page {page_number}")
        response = run_aliyun_command("DescribeVpcs", args, region)

        if not response:
            logger.warning(f"Failed to get VPCs from region {region}")
            break

        # Handle Aliyun response format
        vpcs = []
        if isinstance(response, dict):
            vpcs = response.get("Vpcs", {}).get("Vpc", [])

        if not vpcs:
            break

        # Add region information to each VPC
        for vpc in vpcs:
            vpc["region"] = region

        all_vpcs.extend(vpcs)
        logger.debug(f"Retrieved {len(vpcs)} VPCs from {region}, page {page_number}")

        # Check for pagination
        total_count = response.get("TotalCount", 0)
        if page_number * page_size >= total_count:
            break

        page_number += 1

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
        "id": vpc.get("VpcId", "unknown"),
        "name": vpc.get("VpcName", "unknown"),
        "cidr": vpc.get("CidrBlock", "unknown"),
        "region": vpc.get("region", "unknown"),
        "status": vpc.get("Status", "Unknown"),
        "created_at": vpc.get("CreationTime", ""),
        "description": vpc.get("Description", ""),
        "resource_group_id": vpc.get("ResourceGroupId", "")
    }


def get_vpc_inventory(regions: List[str]) -> Dict[str, Any]:
    """
    Get VPC inventory across multiple regions.

    Args:
        regions: List of region names to scan

    Returns:
        Dictionary containing VPC inventory data
    """
    all_vpcs = []
    regions_scanned = []
    failed_regions = []

    logger.info(f"Starting VPC inventory scan for {len(regions)} region(s)")

    for index, region in enumerate(regions, 1):
        logger.info(f"[{index}/{len(regions)}] Scanning region: {region}")

        try:
            vpcs = get_vpcs_in_region(region)

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
    regions_env = os.environ.get("ALIYUN_REGIONS", "cn-hangzhou")

    if regions_env.lower() == "all":
        regions = [
            "cn-hangzhou",    # Hangzhou
            "cn-shanghai",    # Shanghai
            "cn-beijing",     # Beijing
            "cn-shenzhen",    # Shenzhen
            "cn-qingdao",     # Qingdao
            "cn-zhangjiakou", # Zhangjiakou
            "cn-hongkong",    # Hong Kong
            "ap-southeast-1", # Singapore
            "ap-southeast-2", # Sydney
            "ap-northeast-1", # Tokyo
            "us-west-1",      # Silicon Valley
            "us-east-1",      # Virginia
            "eu-central-1",   # Frankfurt
        ]
    else:
        regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    inventory = get_vpc_inventory(regions)

    # Output results as JSON
    print(json.dumps(inventory, indent=2))


if __name__ == "__main__":
    main()
