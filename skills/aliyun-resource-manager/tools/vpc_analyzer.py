#!/usr/bin/env python3
"""
VPC Analyzer Tool for Aliyun Resource Manager

Analyzes VPC usage status by checking:
- VSwitchs within each VPC
- ECS instances in each VSwitch
- ENIs and IP usage

Determines status: "in_use", "unused", or "pending"
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


def get_vswitchs_in_vpc(vpc_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get all VSwitchs within a VPC.

    Args:
        vpc_id: VPC ID
        region: Region name

    Returns:
        List of VSwitch dictionaries
    """
    response = run_aliyun_command(
        "vpc", "DescribeVSwitches",
        [f"--VpcId={vpc_id}"],
        region
    )

    if not response:
        return []

    # Handle Aliyun response format
    if isinstance(response, dict):
        return response.get("VSwitches", {}).get("VSwitch", [])

    return []


def get_ecs_in_vswitch(vswitch_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get ECS instances in a specific VSwitch.

    Args:
        vswitch_id: VSwitch ID
        region: Region name

    Returns:
        List of ECS instance dictionaries
    """
    response = run_aliyun_command(
        "ecs", "DescribeInstances",
        [f"--VSwitchId={vswitch_id}"],
        region
    )

    if not response:
        return []

    # Handle Aliyun response format
    instances = []
    if isinstance(response, dict):
        instances = response.get("Instances", {}).get("Instance", [])

    # Add region to each instance
    for instance in instances:
        instance['region'] = region

    return instances


def get_enis_in_vswitch(vswitch_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get all ENIs (Elastic Network Interfaces) in a specific VSwitch.

    Args:
        vswitch_id: VSwitch ID
        region: Region name

    Returns:
        List of ENI dictionaries
    """
    response = run_aliyun_command(
        "ecs", "DescribeNetworkInterfaces",
        [f"--VSwitchId={vswitch_id}"],
        region
    )

    if not response:
        return []

    # Handle Aliyun response format
    if isinstance(response, dict):
        return response.get("NetworkInterfaces", {}).get("NetworkInterface", [])

    return []


def check_vswitch_usage(vswitch_id: str, region: str) -> Dict[str, Any]:
    """
    Check the usage status of a VSwitch.

    Args:
        vswitch_id: VSwitch ID
        region: Region name

    Returns:
        Dictionary with usage information
    """
    logger.debug(f"Checking VSwitch usage: {vswitch_id} in {region}")

    # Get ECS instances in VSwitch
    ecs_instances = get_ecs_in_vswitch(vswitch_id, region)
    has_ecs = len(ecs_instances) > 0

    # Get ENIs in VSwitch
    enis = get_enis_in_vswitch(vswitch_id, region)

    # Check for active ENIs (exclude those in pending or deleted state)
    active_enis = []
    for eni in enis:
        status = eni.get("Status", "").lower()
        if status == "inuse" or status == "available":
            active_enis.append(eni)

    has_active_enis = len(active_enis) > 0

    return {
        "vswitch_id": vswitch_id,
        "has_ecs": has_ecs,
        "ecs_count": len(ecs_instances),
        "has_active_enis": has_active_enis,
        "active_eni_count": len(active_enis),
        "total_eni_count": len(enis),
        "ecs_instances": [
            {
                "id": ecs.get("InstanceId", "unknown"),
                "name": ecs.get("InstanceName", "unknown"),
                "status": ecs.get("Status", "UNKNOWN")
            }
            for ecs in ecs_instances
        ]
    }


def get_vpc_details(vpc_id: str, region: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about a VPC.

    Args:
        vpc_id: VPC ID
        region: Region name

    Returns:
        VPC details dictionary or None
    """
    response = run_aliyun_command(
        "vpc", "DescribeVpcAttribute",
        [f"--VpcId={vpc_id}"],
        region
    )

    if not response:
        return None

    # Handle Aliyun response format
    if isinstance(response, dict):
        return response

    return None


def extract_created_by(vpc: Dict[str, Any]) -> Optional[str]:
    """
    Extract created_by information from VPC metadata.

    Args:
        vpc: VPC dictionary

    Returns:
        Creator name or None
    """
    # Try tags
    tags = vpc.get("Tags", {}).get("Tag", [])
    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, dict):
                if tag.get("Key") == "created_by" or tag.get("Key") == "owner":
                    return tag.get("Value")

    # Check direct fields
    return vpc.get("OwnerId") or vpc.get("ResourceGroupId")


def analyze_vpc_usage(vpc_id: str, region: str) -> Dict[str, Any]:
    """
    Analyze the usage status of a VPC.

    Args:
        vpc_id: VPC ID
        region: Region name

    Returns:
        Dictionary with VPC analysis results
    """
    logger.info(f"Analyzing VPC: {vpc_id} in region {region}")

    # Get VPC details
    vpc_details = get_vpc_details(vpc_id, region)

    vpc_name = "unknown"
    created_by = None

    if vpc_details:
        vpc_name = vpc_details.get("VpcName", "unknown")
        created_by = extract_created_by(vpc_details)

    # Get all VSwitchs in VPC
    vswitchs = get_vswitchs_in_vpc(vpc_id, region)

    if not vswitchs:
        logger.warning(f"No VSwitchs found in VPC {vpc_id}")
        return {
            "vpc_id": vpc_id,
            "vpc_name": vpc_name,
            "region": region,
            "status": "unused",
            "reason": "no_vswitchs",
            "vswitchs": [],
            "created_by": created_by,
            "recommendation": "consider_deletion_if_not_needed"
        }

    # Analyze each VSwitch
    vswitch_analysis = []
    total_ecs = 0
    has_active_resources = False

    for vswitch in vswitchs:
        vswitch_id = vswitch.get("VSwitchId", "unknown")
        usage = check_vswitch_usage(vswitch_id, region)
        vswitch_analysis.append(usage)

        total_ecs += usage["ecs_count"]
        if usage["has_ecs"] or usage["has_active_enis"]:
            has_active_resources = True

    # Determine VPC status
    if has_active_resources:
        status = "in_use"
        recommendation = "none"
    elif total_ecs == 0 and not any(s["has_active_enis"] for s in vswitch_analysis):
        status = "unused"
        recommendation = "contact_owner_for_deletion"
    else:
        status = "pending"
        recommendation = "manual_review_required"

    return {
        "vpc_id": vpc_id,
        "vpc_name": vpc_name,
        "region": region,
        "status": status,
        "vswitchs": vswitch_analysis,
        "total_ecs": total_ecs,
        "created_by": created_by,
        "recommendation": recommendation
    }


def analyze_vpcs(vpc_ids: Optional[List[str]] = None, regions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze VPCs across multiple regions.

    Args:
        vpc_ids: Optional list of specific VPC IDs to analyze
        regions: List of regions to scan

    Returns:
        Dictionary containing VPC analysis results
    """
    if not regions:
        regions = ["cn-hangzhou"]

    all_analysis = []
    failed_vpcs = []

    logger.info(f"Starting VPC analysis for {len(regions)} region(s)")

    for region_index, region in enumerate(regions, 1):
        logger.info(f"[{region_index}/{len(regions)}] Analyzing region: {region}")

        try:
            if vpc_ids:
                # Analyze specific VPCs
                target_vpcs = vpc_ids
            else:
                # Get all VPCs in region
                from vpc_inventory import get_vpcs_in_region
                vpcs = get_vpcs_in_region(region)
                target_vpcs = [vpc.get("VpcId") for vpc in vpcs if vpc.get("VpcId")]

            if not target_vpcs:
                logger.info(f"No VPCs to analyze in {region}")
                continue

            logger.info(f"Analyzing {len(target_vpcs)} VPC(s) in {region}")

            for vpc_index, vpc_id in enumerate(target_vpcs, 1):
                if not vpc_id:
                    continue

                logger.info(f"  [{vpc_index}/{len(target_vpcs)}] Analyzing VPC: {vpc_id}")

                try:
                    analysis = analyze_vpc_usage(vpc_id, region)
                    all_analysis.append(analysis)

                    status_str = "[OK]" if analysis["status"] == "in_use" else "[WARN]"
                    logger.info(f"  {status_str} VPC {vpc_id}: {analysis['status']}")

                except Exception as e:
                    logger.error(f"Error analyzing VPC {vpc_id}: {e}")
                    failed_vpcs.append({"vpc_id": vpc_id, "region": region, "error": str(e)})
                    continue

        except Exception as e:
            logger.error(f"Error analyzing region {region}: {e}")
            continue

    # Calculate summary statistics
    status_counts = {"in_use": 0, "unused": 0, "pending": 0}
    for analysis in all_analysis:
        status = analysis.get("status", "pending")
        status_counts[status] = status_counts.get(status, 0) + 1

    result = {
        "vpc_analysis": all_analysis,
        "summary": {
            "total_vpcs": len(all_analysis),
            "in_use": status_counts["in_use"],
            "unused": status_counts["unused"],
            "pending": status_counts["pending"]
        },
        "failed_vpcs": failed_vpcs
    }

    logger.info(f"VPC analysis complete. Total: {len(all_analysis)}, "
                f"In use: {status_counts['in_use']}, "
                f"Unused: {status_counts['unused']}, "
                f"Pending: {status_counts['pending']}")

    return result


def main():
    """Main entry point for testing."""
    # Get regions from environment or use default
    regions_env = os.environ.get("ALIYUN_REGIONS", "cn-hangzhou")

    if regions_env.lower() == "all":
        regions = [
            "cn-hangzhou", "cn-shanghai", "cn-beijing", "cn-shenzhen",
            "cn-qingdao", "cn-zhangjiakou", "cn-hongkong",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
            "us-west-1", "us-east-1", "eu-central-1"
        ]
    else:
        regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    analysis = analyze_vpcs(regions=regions)

    # Output results as JSON
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
