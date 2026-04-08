#!/usr/bin/env python3
"""
VPC Analyzer Tool for Huawei Cloud Resource Manager

Analyzes VPC usage status by checking:
- Subnets within each VPC
- ECS instances in each subnet
- NICs and IP usage

Determines status: "in_use", "unused", or "pending"
"""

import json
import subprocess
import logging
import os
import random
import time
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default page size for pagination
DEFAULT_PAGE_SIZE = 100

# Lock for thread-safe operations
_vpc_analysis_lock = Lock()


def run_hcloud_command(command: List[str], region: str) -> Optional[Dict[str, Any]]:
    """
    Execute hcloud CLI command and return parsed JSON output.

    Args:
        command: Command and arguments as list
        region: Region to query

    Returns:
        Parsed JSON response or None if command fails
    """
    full_command = ["hcloud"] + command + [f"--region={region}"]

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
    response = run_hcloud_command(
        ["vpc", "ListSubnets", f"--vpc_id={vpc_id}"],
        region
    )

    if not response:
        return []

    # Handle different response formats
    if isinstance(response, dict):
        return response.get("subnets", [])
    elif isinstance(response, list):
        return response

    return []


def get_ecs_in_subnet(subnet_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get ECS instances in a specific subnet.

    Args:
        subnet_id: Subnet ID
        region: Region name

    Returns:
        List of ECS instance dictionaries
    """
    # Try to filter by subnet using different possible filter names
    filters = [
        f"--subnet_id={subnet_id}",
        f"--network_id={subnet_id}",
    ]

    all_servers = []

    for filter_param in filters:
        response = run_hcloud_command(
            ["ecs", "ListServers", filter_param],
            region
        )

        if response:
            servers = []
            if isinstance(response, dict):
                servers = response.get("servers", [])
            elif isinstance(response, list):
                servers = response

            # Validate that servers are actually in this subnet
            for server in servers:
                # Check if server has addresses in this subnet
                addresses = server.get("addresses", {})
                for network_name, network_ips in addresses.items():
                    for ip_info in network_ips:
                        if isinstance(ip_info, dict):
                            # Check various fields that might contain subnet info
                            if (ip_info.get("subnet_id") == subnet_id or
                                ip_info.get("network_id") == subnet_id):
                                if server not in all_servers:
                                    all_servers.append(server)
                                break

            if all_servers:
                break

    return all_servers


def get_ports_in_subnet(subnet_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get all ports (NICs) in a specific subnet.

    Args:
        subnet_id: Subnet ID
        region: Region name

    Returns:
        List of port dictionaries
    """
    response = run_hcloud_command(
        ["vpc", "ListPorts", f"--network_id={subnet_id}"],
        region
    )

    if not response:
        # Try alternative filter name
        response = run_hcloud_command(
            ["vpc", "ListPorts", f"--subnet_id={subnet_id}"],
            region
        )

    if not response:
        return []

    # Handle different response formats
    if isinstance(response, dict):
        return response.get("ports", [])
    elif isinstance(response, list):
        return response

    return []


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

    # Get ECS instances in subnet
    ecs_instances = get_ecs_in_subnet(subnet_id, region)
    has_ecs = len(ecs_instances) > 0

    # Get ports/NICs in subnet
    ports = get_ports_in_subnet(subnet_id, region)

    # Check for active IPs (exclude default gateway and DHCP ports)
    active_ports = []
    for port in ports:
        device_owner = port.get("device_owner", "")
        # Filter out network:dhcp and network:router_interface ports
        if device_owner and not device_owner.startswith("network:"):
            active_ports.append(port)

    has_active_ips = len(active_ports) > 0

    return {
        "subnet_id": subnet_id,
        "has_ecs": has_ecs,
        "ecs_count": len(ecs_instances),
        "has_active_ips": has_active_ips,
        "active_port_count": len(active_ports),
        "total_port_count": len(ports),
        "ecs_instances": [
            {
                "id": ecs.get("id") or ecs.get("server_id", "unknown"),
                "name": ecs.get("name", "unknown"),
                "status": ecs.get("status", "UNKNOWN")
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
    response = run_hcloud_command(
        ["vpc", "ShowVpc", f"--vpc_id={vpc_id}"],
        region
    )

    if not response:
        return None

    # Handle different response formats
    if isinstance(response, dict):
        if "vpc" in response:
            return response["vpc"]
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
    # Try various fields where creator info might be stored
    tags = vpc.get("tags", [])

    if isinstance(tags, list):
        for tag in tags:
            if isinstance(tag, dict):
                if tag.get("key") == "created_by":
                    return tag.get("value")
                if tag.get("key") == "owner":
                    return tag.get("value")

    # Check metadata fields
    metadata = vpc.get("metadata", {})
    if isinstance(metadata, dict):
        return metadata.get("created_by") or metadata.get("owner")

    # Check direct fields
    return vpc.get("created_by") or vpc.get("owner") or vpc.get("user_id")


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
        vpc_name = vpc_details.get("name", "unknown")
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
    total_ecs = 0
    has_active_resources = False

    for subnet in subnets:
        subnet_id = subnet.get("id") or subnet.get("subnet_id", "unknown")
        usage = check_subnet_usage(subnet_id, region)
        subnet_analysis.append(usage)

        total_ecs += usage["ecs_count"]
        if usage["has_ecs"] or usage["has_active_ips"]:
            has_active_resources = True

    # Determine VPC status
    if has_active_resources:
        status = "in_use"
        recommendation = "none"
    elif total_ecs == 0 and not any(s["has_active_ips"] for s in subnet_analysis):
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
        "total_ecs": total_ecs,
        "created_by": created_by,
        "recommendation": recommendation
    }


def analyze_vpcs_concurrent(
    vpc_ids: Optional[List[str]] = None,
    region: str = "cn-north-4",
    max_workers: int = 3
) -> Dict[str, Any]:
    """
    Analyze VPCs concurrently within a region.

    Args:
        vpc_ids: Optional list of specific VPC IDs to analyze
        region: Region to scan
        max_workers: Maximum concurrent VPC analysis workers (default: 3)

    Returns:
        Dictionary containing VPC analysis results
    """
    if not vpc_ids:
        # Get all VPCs in region
        from vpc_inventory import get_vpcs_in_region
        vpcs = get_vpcs_in_region(region)
        vpc_ids = [vpc.get("id") or vpc.get("vpc_id") for vpc in vpcs if vpc.get("id") or vpc.get("vpc_id")]

    if not vpc_ids:
        logger.info(f"No VPCs to analyze in {region}")
        return {
            "vpc_analysis": [],
            "summary": {"total_vpcs": 0, "in_use": 0, "unused": 0, "pending": 0},
            "failed_vpcs": []
        }

    logger.info(f"Analyzing {len(vpc_ids)} VPC(s) in {region} with {max_workers} workers")

    all_analysis = []
    failed_vpcs = []
    completed = 0

    # Use ThreadPoolExecutor for concurrent VPC analysis
    with ThreadPoolExecutor(max_workers=min(max_workers, 5)) as executor:
        # Submit all VPC analysis tasks with staggered delays
        future_to_vpc = {}
        for index, vpc_id in enumerate(vpc_ids):
            if not vpc_id:
                continue
            # Add small staggered delay to avoid API rate limiting
            delay = random.uniform(0.1, 0.5) * (index % max_workers)
            future = executor.submit(_analyze_vpc_with_delay, vpc_id, region, delay)
            future_to_vpc[future] = vpc_id

        # Process completed results as they finish
        for future in as_completed(future_to_vpc):
            vpc_id = future_to_vpc[future]
            completed += 1

            try:
                analysis = future.result()
                if analysis:
                    with _vpc_analysis_lock:
                        all_analysis.append(analysis)

                    status_icon = "✓" if analysis["status"] == "in_use" else "⚠"
                    logger.info(f"  [{completed}/{len(vpc_ids)}] {status_icon} VPC {vpc_id}: {analysis['status']}")
                else:
                    failed_vpcs.append({"vpc_id": vpc_id, "region": region, "error": "Analysis returned None"})

            except Exception as e:
                logger.error(f"Error analyzing VPC {vpc_id}: {e}")
                failed_vpcs.append({"vpc_id": vpc_id, "region": region, "error": str(e)})

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

    logger.info(f"VPC analysis complete for {region}. Total: {len(all_analysis)}, "
                f"In use: {status_counts['in_use']}, "
                f"Unused: {status_counts['unused']}")

    return result


def _analyze_vpc_with_delay(vpc_id: str, region: str, delay: float) -> Optional[Dict[str, Any]]:
    """
    Analyze a single VPC with initial delay for staggered execution.

    Args:
        vpc_id: VPC ID to analyze
        region: Region name
        delay: Initial delay in seconds

    Returns:
        VPC analysis result or None
    """
    time.sleep(delay)
    return analyze_vpc_usage(vpc_id, region)


def analyze_vpcs(vpc_ids: Optional[List[str]] = None, regions: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze VPCs across multiple regions (serial execution, legacy method).
    For concurrent analysis, use analyze_vpcs_concurrent().

    Args:
        vpc_ids: Optional list of specific VPC IDs to analyze
        regions: List of regions to scan

    Returns:
        Dictionary containing VPC analysis results
    """
    if not regions:
        regions = ["cn-north-4"]

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
                target_vpcs = [vpc.get("id") or vpc.get("vpc_id") for vpc in vpcs if vpc.get("id") or vpc.get("vpc_id")]

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

                    status_icon = "✓" if analysis["status"] == "in_use" else "⚠"
                    logger.info(f"  {status_icon} VPC {vpc_id}: {analysis['status']}")

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
    regions_env = os.environ.get("HWCLOUD_REGIONS", "cn-north-4")

    if regions_env.lower() == "all":
        try:
            import sys
            sys.path.insert(0, '/home/alex/codebase/multi-cloud-resource-manager/skills/huaweicloud-core/auth-manager')
            from auth_manager import KNOWN_REGIONS
            regions = KNOWN_REGIONS
        except ImportError:
            regions = ["cn-north-4", "cn-south-1", "cn-east-2"]
    else:
        regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    analysis = analyze_vpcs(regions=regions)

    # Output results as JSON
    print(json.dumps(analysis, indent=2))


if __name__ == "__main__":
    main()
