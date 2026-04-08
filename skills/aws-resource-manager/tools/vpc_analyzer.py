#!/usr/bin/env python3
"""
VPC Analyzer Tool for AWS Resource Manager

Analyzes VPC usage status by checking:
- Subnets within each VPC
- EC2 instances in each subnet
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


def run_aws_command(service: str, operation: str, args: List[str], region: str) -> Optional[Dict[str, Any]]:
    """
    Execute AWS CLI command and return parsed JSON output.

    Args:
        service: AWS service name
        operation: API operation
        args: Command arguments as list
        region: Region to query

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


def get_subnets_in_vpc(vpc_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get all subnets within a VPC.

    Args:
        vpc_id: VPC ID
        region: Region name

    Returns:
        List of subnet dictionaries
    """
    response = run_aws_command(
        "ec2", "describe-subnets",
        ["--filters", f"Name=vpc-id,Values={vpc_id}"],
        region
    )

    if not response:
        return []

    return response.get("Subnets", [])


def get_ec2_in_subnet(subnet_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get EC2 instances in a specific subnet.

    Args:
        subnet_id: Subnet ID
        region: Region name

    Returns:
        List of EC2 instance dictionaries
    """
    response = run_aws_command(
        "ec2", "describe-instances",
        ["--filters", f"Name=subnet-id,Values={subnet_id}"],
        region
    )

    if not response:
        return []

    instances = []
    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            instance['region'] = region
            instances.append(instance)

    return instances


def get_enis_in_subnet(subnet_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get all ENIs (Elastic Network Interfaces) in a specific subnet.

    Args:
        subnet_id: Subnet ID
        region: Region name

    Returns:
        List of ENI dictionaries
    """
    response = run_aws_command(
        "ec2", "describe-network-interfaces",
        ["--filters", f"Name=subnet-id,Values={subnet_id}"],
        region
    )

    if not response:
        return []

    return response.get("NetworkInterfaces", [])


def check_subnet_usage(subnet_id: str, region: str) -> Dict[str, Any]:
    """
    Check the usage status of a subnet.

    Args:
        subnet_id: Subnet ID
        region: Region name

    Returns:
        Dictionary with usage information
    """
    logger.debug(f"Checking subnet usage: {subnet_id} in {region}")

    # Get EC2 instances in subnet
    ec2_instances = get_ec2_in_subnet(subnet_id, region)
    has_ec2 = len(ec2_instances) > 0

    # Get ENIs in subnet
    enis = get_enis_in_subnet(subnet_id, region)

    # Check for active ENIs (exclude those in pending or deleted state)
    active_enis = []
    for eni in enis:
        status = eni.get("Status", "").lower()
        if status == "in-use" or status == "available":
            active_enis.append(eni)

    has_active_enis = len(active_enis) > 0

    return {
        "subnet_id": subnet_id,
        "has_ec2": has_ec2,
        "ec2_count": len(ec2_instances),
        "has_active_enis": has_active_enis,
        "active_eni_count": len(active_enis),
        "total_eni_count": len(enis),
        "ec2_instances": [
            {
                "id": ec2.get("InstanceId", "unknown"),
                "name": next((t.get("Value", "unknown") for t in ec2.get("Tags", []) if t.get("Key") == "Name"), "unknown"),
                "status": ec2.get("State", {}).get("Name", "unknown")
            }
            for ec2 in ec2_instances
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
    response = run_aws_command(
        "ec2", "describe-vpcs",
        ["--vpc-ids", vpc_id],
        region
    )

    if not response:
        return None

    vpcs = response.get("Vpcs", [])
    return vpcs[0] if vpcs else None


def extract_created_by(vpc: Dict[str, Any]) -> Optional[str]:
    """
    Extract created_by information from VPC tags.

    Args:
        vpc: VPC dictionary

    Returns:
        Creator name or None
    """
    tags = vpc.get("Tags", [])

    for tag in tags:
        if tag.get("Key") in ["created_by", "owner", "CreatedBy", "Owner"]:
            return tag.get("Value")

    return None


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
        # Extract name from tags
        for tag in vpc_details.get("Tags", []):
            if tag.get("Key") == "Name":
                vpc_name = tag.get("Value", "unknown")
                break
        created_by = extract_created_by(vpc_details)

    # Get all subnets in VPC
    subnets = get_subnets_in_vpc(vpc_id, region)

    if not subnets:
        logger.warning(f"No subnets found in VPC {vpc_id}")
        return {
            "vpc_id": vpc_id,
            "vpc_name": vpc_name,
            "region": region,
            "status": "unused",
            "reason": "no_subnets",
            "subnets": [],
            "created_by": created_by,
            "recommendation": "consider_deletion_if_not_needed"
        }

    # Analyze each subnet
    subnet_analysis = []
    total_ec2 = 0
    has_active_resources = False

    for subnet in subnets:
        subnet_id = subnet.get("SubnetId", "unknown")
        usage = check_subnet_usage(subnet_id, region)
        subnet_analysis.append(usage)

        total_ec2 += usage["ec2_count"]
        if usage["has_ec2"] or usage["has_active_enis"]:
            has_active_resources = True

    # Determine VPC status
    if has_active_resources:
        status = "in_use"
        recommendation = "none"
    elif total_ec2 == 0 and not any(s["has_active_enis"] for s in subnet_analysis):
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
        "subnets": subnet_analysis,
        "total_ec2": total_ec2,
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
        regions = ["us-east-1"]

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
    regions_env = os.environ.get("AWS_REGIONS", "us-east-1")

    if regions_env.lower() == "all":
        regions = [
            "us-east-1", "us-east-2", "us-west-1", "us-west-2",
            "eu-west-1", "eu-west-2", "eu-central-1",
            "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
            "ap-south-1", "sa-east-1"
        ]
    else:
        regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    analysis = analyze_vpcs(regions=regions)

    # Output results as JSON
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
