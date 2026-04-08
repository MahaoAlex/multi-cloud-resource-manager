#!/usr/bin/env python3
"""
Main entry point for Huawei Cloud Resource Manager Skill.

Coordinates all scanning tools and generates comprehensive reports.
Supports both interactive and command-line modes.
"""

import os
import sys
import time
import json
import logging
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Add tools directory to path
tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

# Import tools
from vpc_inventory import get_vpc_inventory
from vpc_analyzer import analyze_vpc_usage, analyze_vpcs_concurrent
from security_scanner import scan_security_groups
from obs_scanner import scan_obs_buckets
from ecs_monitor import monitor_ecs_instances
from eip_scanner import scan_unattached_eips
from cce_scanner import scan_cce_clusters
from report_generator import ReportGenerator
from rule_engine import RuleEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_regions_from_env() -> List[str]:
    """Get list of regions from environment variable."""
    regions_env = os.environ.get("HWCLOUD_REGIONS", "cn-north-4")

    if regions_env.lower() == "all":
        # Known Huawei Cloud regions
        return [
            "cn-north-4",    # Beijing
            "cn-north-1",    # Beijing (old)
            "cn-south-1",    # Guangzhou
            "cn-east-2",     # Shanghai
            "cn-east-3",     # Shanghai (new)
            "cn-southwest-2", # Guiyang
            "ap-southeast-1", # Hong Kong
            "ap-southeast-2", # Bangkok
            "ap-southeast-3", # Singapore
            "eu-west-101",    # Amsterdam
            "af-south-1"      # Johannesburg
        ]

    return [r.strip() for r in regions_env.split(",") if r.strip()]


def validate_environment():
    """Validate required environment variables."""
    required = ['HWCLOUD_ACCESS_KEY', 'HWCLOUD_SECRET_KEY']
    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def scan_vpcs(
    regions: Optional[List[str]] = None,
    output_dir: str = "./reports",
    scan_type: str = "manual"
) -> Dict[str, Any]:
    """
    Scan VPC resources across regions.

    Args:
        regions: List of regions to scan
        output_dir: Directory for reports
        scan_type: 'manual' or 'scheduled'

    Returns:
        Scan results dictionary
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting VPC scan for {len(regions)} region(s)")
    start_time = time.time()

    # Get VPC inventory
    inventory = get_vpc_inventory(regions)
    vpcs = inventory.get("vpcs", [])

    # Analyze each VPC
    vpc_analysis = []
    for vpc in vpcs:
        region = vpc.get("region")
        vpc_id = vpc.get("id")
        try:
            analysis = analyze_vpc_usage(vpc_id, region)
            vpc_analysis.append(analysis)
        except Exception as e:
            logger.error(f"Failed to analyze VPC {vpc_id}: {e}")
            vpc_analysis.append({
                "vpc_id": vpc_id,
                "vpc_name": vpc.get("name"),
                "region": region,
                "status": "error",
                "error": str(e)
            })

    duration = int(time.time() - start_time)

    results = {
        "regions": regions,
        "duration_seconds": duration,
        "summary": {
            "vpcs": len(vpcs),
            "unused_vpcs": len([v for v in vpc_analysis if v.get("status") == "unused"])
        },
        "vpc_analysis": vpc_analysis
    }

    # Generate report
    generator = ReportGenerator(output_dir)
    files = generator.generate_report(results, scan_type=scan_type)

    logger.info(f"VPC scan complete. Reports: {files}")
    return results


def scan_security(
    regions: Optional[List[str]] = None,
    check_ports: Optional[List[int]] = None
) -> List[Dict[str, Any]]:
    """
    Scan security groups for high-risk configurations.

    Args:
        regions: List of regions to scan
        check_ports: Ports to check (default: [22, 33, 44])

    Returns:
        List of security issues
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting security scan for {len(regions)} region(s)")

    issues = scan_security_groups(regions)

    logger.info(f"Security scan complete. Found {len(issues)} issue(s)")
    return issues


def scan_obs(regions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Scan OBS buckets for public access.

    Args:
        regions: List of regions to scan

    Returns:
        List of OBS issues
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting OBS scan for {len(regions)} region(s)")

    # Import here to avoid dependency issues
    from obs_scanner import scan_obs_buckets
    issues = scan_obs_buckets(regions)

    logger.info(f"OBS scan complete. Found {len(issues)} issue(s)")
    return issues


def scan_ecs(
    regions: Optional[List[str]] = None,
    cpu_threshold: float = 10.0,
    check_naming: bool = True
) -> List[Dict[str, Any]]:
    """
    Monitor ECS instances.

    Args:
        regions: List of regions to scan
        cpu_threshold: CPU utilization threshold
        check_naming: Whether to check naming conventions

    Returns:
        List of ECS issues
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting ECS scan for {len(regions)} region(s)")

    issues = monitor_ecs_instances(regions, cpu_threshold, check_naming)

    logger.info(f"ECS scan complete. Found {len(issues)} issue(s)")
    return issues


def scan_eips(regions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Scan for unattached Elastic IPs.

    Args:
        regions: List of regions to scan

    Returns:
        List of unattached EIPs
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting EIP scan for {len(regions)} region(s)")

    eips = scan_unattached_eips(regions)

    logger.info(f"EIP scan complete. Found {len(eips)} unattached EIP(s)")
    return eips


def scan_cce(
    regions: Optional[List[str]] = None,
    pod_threshold: int = 5
) -> List[Dict[str, Any]]:
    """
    Scan CCE clusters for low utilization.
    Identifies clusters with no pods or fewer than threshold pods.

    Args:
        regions: List of regions to scan
        pod_threshold: Pod count threshold for low usage warning

    Returns:
        List of CCE clusters with utilization issues
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting CCE scan for {len(regions)} region(s)")

    issues = scan_cce_clusters(regions, pod_threshold=pod_threshold)

    logger.info(f"CCE scan complete. Found {len(issues)} cluster(s) with low utilization")
    return issues


# Lock for thread-safe logging
_scan_lock = Lock()
_scan_counter = 0


def _scan_single_region(region: str, vpc_max_workers: int = 3) -> Dict[str, Any]:
    """
    Scan a single region with all resource types.
    This function is designed to be run concurrently across regions,
    and also performs concurrent VPC analysis within the region.

    Args:
        region: Region ID to scan
        vpc_max_workers: Maximum concurrent workers for VPC analysis (default: 3)

    Returns:
        Dictionary containing scan results for the region
    """
    global _scan_counter

    # Add staggered delay to avoid concurrent API storm
    # Each region starts with 0.5-1.5s delay to spread out requests
    with _scan_lock:
        _scan_counter += 1
        delay = random.uniform(0.5, 1.5)
    time.sleep(delay)

    logger.info(f"Scanning region: {region} (after {delay:.2f}s delay, VPC workers: {vpc_max_workers})")
    region_result = {
        "region": region,
        "vpc_analysis": [],
        "security_issues": [],
        "obs_issues": [],
        "ecs_issues": [],
        "cce_issues": [],
        "naming_violations": [],
        "unattached_eips": [],
        "summary": {},
        "error": None
    }

    try:
        # VPC inventory
        vpc_data = get_vpc_inventory([region])
        vpc_ids = [vpc.get("id") for vpc in vpc_data.get("vpcs", []) if vpc.get("id")]

        if vpc_ids:
            # Analyze VPCs concurrently
            vpc_results = analyze_vpcs_concurrent(
                vpc_ids=vpc_ids,
                region=region,
                max_workers=vpc_max_workers
            )
            region_result["vpc_analysis"] = vpc_results.get("vpc_analysis", [])
        else:
            logger.info(f"No VPCs found in region {region}")

        # Security scan
        sec_issues = scan_security_groups([region])
        region_result["security_issues"].extend(sec_issues)

        # OBS scan
        obs_issues = scan_obs_buckets([region])
        region_result["obs_issues"].extend(obs_issues)

        # ECS scan
        ecs_issues = monitor_ecs_instances([region])
        region_result["ecs_issues"].extend(ecs_issues)

        # Naming violations from ECS issues
        for ecs in ecs_issues:
            for issue in ecs.get("issues", []):
                if issue.get("type") == "naming_violation":
                    region_result["naming_violations"].append({
                        "resource_type": "ecs",
                        "resource_id": ecs.get("instance_id"),
                        "resource_name": ecs.get("instance_name"),
                        "region": region
                    })

        # EIP scan
        eips = scan_unattached_eips([region])
        region_result["unattached_eips"].extend(eips)

        # CCE scan
        try:
            cce_issues = scan_cce_clusters([region], pod_threshold=5)
            region_result["cce_issues"].extend(cce_issues)
        except Exception as e:
            logger.warning(f"CCE scan failed for region {region}: {e}")
            region_result["cce_issues"] = []

        # Update region summary
        region_result["summary"] = {
            "vpcs": len(region_result["vpc_analysis"]),
            "security_issues": len(sec_issues),
            "obs_issues": len(obs_issues),
            "ecs_issues": len(ecs_issues),
            "unattached_eips": len(eips),
            "cce_issues": len(region_result["cce_issues"])
        }

        logger.info(f"Completed scanning region: {region} "
                    f"({len(region_result['vpc_analysis'])} VPCs analyzed)")

    except Exception as e:
        logger.error(f"Error scanning region {region}: {e}")
        region_result["error"] = str(e)

    return region_result


def full_scan(
    regions: Optional[List[str]] = None,
    output_dir: str = "./reports",
    scan_type: str = "manual",
    retention_days: int = 7,
    max_workers: int = 5,
    vpc_max_workers: int = 3
) -> Dict[str, Any]:
    """
    Perform complete resource scan across all categories with concurrent region and VPC scanning.

    Args:
        regions: List of regions to scan
        output_dir: Directory for reports
        scan_type: 'manual' or 'scheduled'
        retention_days: Days to keep reports
        max_workers: Maximum concurrent region workers (default: 5)
        vpc_max_workers: Maximum concurrent VPC workers per region (default: 3)

    Returns:
        Complete scan results
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting concurrent full scan for {len(regions)} region(s) "
                f"with max {max_workers} region workers, {vpc_max_workers} VPC workers per region")
    start_time = time.time()

    # Collect all scan results
    all_results = {
        "regions": regions,
        "duration_seconds": 0,
        "summary": {},
        "summary_by_region": {},
        "vpc_analysis": [],
        "security_issues": [],
        "obs_issues": [],
        "ecs_issues": [],
        "cce_issues": [],
        "unattached_eips": [],
        "naming_violations": [],
        "failed_regions": [],
        "scan_config": {
            "max_workers": max_workers,
            "vpc_max_workers": vpc_max_workers
        }
    }

    # Use ThreadPoolExecutor for concurrent region scanning
    # Limit max_workers to 5 as specified for safe API usage
    with ThreadPoolExecutor(max_workers=min(max_workers, 5)) as executor:
        # Submit all region scan tasks with VPC worker configuration
        future_to_region = {
            executor.submit(_scan_single_region, region, vpc_max_workers): region
            for region in regions
        }

        # Process completed results as they finish
        completed = 0
        for future in as_completed(future_to_region):
            region = future_to_region[future]
            completed += 1

            try:
                region_result = future.result()

                if region_result["error"]:
                    all_results["failed_regions"].append({
                        "region": region,
                        "error": region_result["error"]
                    })
                else:
                    # Merge region results into all_results
                    all_results["vpc_analysis"].extend(region_result["vpc_analysis"])
                    all_results["security_issues"].extend(region_result["security_issues"])
                    all_results["obs_issues"].extend(region_result["obs_issues"])
                    all_results["ecs_issues"].extend(region_result["ecs_issues"])
                    all_results["cce_issues"].extend(region_result["cce_issues"])
                    all_results["naming_violations"].extend(region_result["naming_violations"])
                    all_results["unattached_eips"].extend(region_result["unattached_eips"])
                    all_results["summary_by_region"][region] = region_result["summary"]

                logger.info(f"[{completed}/{len(regions)}] Processed region: {region}")

            except Exception as e:
                logger.error(f"Error processing region {region}: {e}")
                all_results["failed_regions"].append({"region": region, "error": str(e)})

    # Calculate totals
    all_results["summary"] = {
        "vpcs": len(all_results["vpc_analysis"]),
        "unused_vpcs": len([v for v in all_results["vpc_analysis"] if v.get("status") == "unused"]),
        "security_issues": len(all_results["security_issues"]),
        "public_obs_buckets": len(set(b.get("bucket_name") for b in all_results["obs_issues"])),
        "low_utilization_ecs": len([
            e for e in all_results["ecs_issues"]
            if any(i.get("type") == "low_cpu_usage" for i in e.get("issues", []))
        ]),
        "unattached_eips": len(all_results["unattached_eips"]),
        "naming_violations": len(all_results["naming_violations"]),
        "cce_clusters_low_utilization": len(all_results["cce_issues"]),
        "cce_empty_clusters": len([c for c in all_results["cce_issues"] if c.get("node_count", 0) == 0])
    }

    all_results["duration_seconds"] = int(time.time() - start_time)

    # Generate report
    generator = ReportGenerator(output_dir)
    files = generator.generate_report(all_results, scan_type=scan_type)

    logger.info(f"Full scan complete in {all_results['duration_seconds']}s")
    logger.info(f"Reports generated: {files}")

    return all_results


def generate_report(
    scan_results: Dict[str, Any],
    format: str = "both",
    output_path: Optional[str] = None
) -> Dict[str, str]:
    """
    Generate formatted reports from scan results.

    Args:
        scan_results: Raw scan results
        format: 'json', 'markdown', or 'both'
        output_path: Optional output path

    Returns:
        Dictionary with file paths
    """
    generator = ReportGenerator(output_path or "./reports")

    scan_type = scan_results.get("scan_type", "manual")
    files = generator.generate_report(scan_results, scan_type=scan_type)

    return files


def list_rules() -> Dict[str, Any]:
    """List all loaded rules."""
    engine = RuleEngine()
    engine.load_rules()

    rules_summary = engine.get_rules_summary()
    rules_details = [
        {
            "id": rule.id,
            "name": rule.name,
            "resource": rule.resource,
            "severity": rule.severity,
            "description": rule.description
        }
        for rule in engine.rules
    ]

    return {
        "summary": rules_summary,
        "rules": rules_details
    }


def run_custom_rule(rule_file: str, resource_type: str) -> List[Dict[str, Any]]:
    """
    Run a custom rule against resources.

    Args:
        rule_file: Path to custom rule file
        resource_type: Type of resources to check

    Returns:
        List of violations
    """
    logger.info(f"Running custom rule {rule_file} against {resource_type}")

    # TODO: Implement custom rule execution
    return []


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(description="Huawei Cloud Resource Manager")
    parser.add_argument("--regions", help="Comma-separated regions or 'all'")
    parser.add_argument("--output", default="./reports", help="Output directory")
    parser.add_argument("--mode", choices=["manual", "scheduled"], default="manual")
    parser.add_argument("--scan", choices=["vpc", "security", "obs", "ecs", "eip", "cce", "full"], default="full")

    args = parser.parse_args()

    # Validate environment
    try:
        validate_environment()
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        sys.exit(1)

    # Set regions if provided
    if args.regions:
        os.environ["HWCLOUD_REGIONS"] = args.regions

    # Run scan
    if args.scan == "full":
        results = full_scan(output_dir=args.output, scan_type=args.mode)
    elif args.scan == "vpc":
        results = scan_vpcs(output_dir=args.output, scan_type=args.mode)
    elif args.scan == "security":
        results = scan_security()
    elif args.scan == "obs":
        results = scan_obs()
    elif args.scan == "ecs":
        results = scan_ecs()
    elif args.scan == "eip":
        results = scan_eips()
    elif args.scan == "cce":
        results = scan_cce()

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
