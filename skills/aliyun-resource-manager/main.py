#!/usr/bin/env python3
"""
Main entry point for Aliyun Resource Manager Skill.

Coordinates all scanning tools and generates comprehensive reports.
Supports both interactive and command-line modes.
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

# Add tools directory to path
tools_dir = Path(__file__).parent / "tools"
sys.path.insert(0, str(tools_dir))

# Import tools
from vpc_inventory import get_vpc_inventory
from vpc_analyzer import analyze_vpc_usage
from security_scanner import scan_security_groups
from oss_scanner import scan_oss_buckets
from ecs_monitor import monitor_ecs_instances
from eip_scanner import scan_unattached_eips
from rds_scanner import scan_rds_instances
from slb_scanner import scan_slb_instances
from report_generator import ReportGenerator
from rule_engine import RuleEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def retry_on_error(max_retries=3, delay=1, backoff=2):
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retry_delay = delay
            last_exception = None

            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}. "
                            f"Retrying in {retry_delay}s..."
                        )
                        time.sleep(retry_delay)
                        retry_delay *= backoff
                    else:
                        logger.error(f"All {max_retries} attempts failed for {func.__name__}: {e}")

            raise last_exception
        return wrapper
    return decorator


# Wrap scan functions with retry
@retry_on_error(max_retries=3, delay=1, backoff=2)
def get_vpc_inventory_with_retry(regions):
    return get_vpc_inventory(regions)


@retry_on_error(max_retries=3, delay=1, backoff=2)
def scan_security_groups_with_retry(regions):
    return scan_security_groups(regions)


@retry_on_error(max_retries=3, delay=1, backoff=2)
def monitor_ecs_instances_with_retry(regions):
    return monitor_ecs_instances(regions)


@retry_on_error(max_retries=3, delay=1, backoff=2)
def scan_unattached_eips_with_retry(regions):
    return scan_unattached_eips(regions)


def get_regions_from_env() -> List[str]:
    """Get list of regions from environment variable."""
    regions_env = os.environ.get("ALIYUN_REGIONS", "cn-hangzhou")

    if regions_env.lower() == "all":
        # Known Aliyun regions
        return [
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

    return [r.strip() for r in regions_env.split(",") if r.strip()]


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


def scan_oss(regions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Scan OSS buckets for public access.

    Args:
        regions: List of regions to scan

    Returns:
        List of OSS issues
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting OSS scan for {len(regions)} region(s)")

    issues = scan_oss_buckets(regions)

    logger.info(f"OSS scan complete. Found {len(issues)} issue(s)")
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


def scan_single_region(region: str) -> Dict[str, Any]:
    """
    Scan a single region for all resource types.

    Args:
        region: Region name

    Returns:
        Dictionary containing all scan results for the region
    """
    result = {
        "region": region,
        "vpcs": [],
        "vpc_analysis": [],
        "security_issues": [],
        "ecs_issues": [],
        "rds_issues": [],
        "slb_issues": [],
        "unattached_eips": [],
        "naming_violations": [],
        "error": None
    }

    try:
        # VPC inventory and analysis (with retry)
        vpc_data = get_vpc_inventory_with_retry([region])
        result["vpcs"] = vpc_data.get("vpcs", [])
        for vpc in vpc_data.get("vpcs", []):
            analysis = analyze_vpc_usage(vpc.get("id"), region)
            result["vpc_analysis"].append(analysis)

        # Security scan (with retry)
        result["security_issues"] = scan_security_groups_with_retry([region])

        # ECS scan (with retry)
        result["ecs_issues"] = monitor_ecs_instances_with_retry([region])

        # Naming violations from ECS issues
        for ecs in result["ecs_issues"]:
            for issue in ecs.get("issues", []):
                if issue.get("type") == "naming_violation":
                    result["naming_violations"].append({
                        "resource_type": "ecs",
                        "resource_id": ecs.get("instance_id"),
                        "resource_name": ecs.get("instance_name"),
                        "region": region
                    })

        # EIP scan (with retry)
        result["unattached_eips"] = scan_unattached_eips_with_retry([region])

        # RDS scan (with retry)
        try:
            result["rds_issues"] = scan_rds_instances([region])
        except Exception as e:
            logger.warning(f"RDS scan failed for region {region}: {e}")
            result["rds_issues"] = []

        # SLB scan (with retry)
        try:
            result["slb_issues"] = scan_slb_instances([region])
        except Exception as e:
            logger.warning(f"SLB scan failed for region {region}: {e}")
            result["slb_issues"] = []

    except Exception as e:
        logger.error(f"Error scanning region {region}: {e}")
        result["error"] = str(e)

    return result


def full_scan(
    regions: Optional[List[str]] = None,
    output_dir: str = "./reports",
    scan_type: str = "manual",
    retention_days: int = 7,
    max_workers: int = 5
) -> Dict[str, Any]:
    """
    Perform complete resource scan across all categories with concurrent region scanning.

    Args:
        regions: List of regions to scan
        output_dir: Directory for reports
        scan_type: 'manual' or 'scheduled'
        retention_days: Days to keep reports
        max_workers: Maximum number of concurrent region scans

    Returns:
        Complete scan results
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting full scan for {len(regions)} region(s) with {max_workers} workers")
    start_time = time.time()

    # Collect all scan results
    all_results = {
        "regions": regions,
        "duration_seconds": 0,
        "summary": {},
        "summary_by_region": {},
        "vpc_analysis": [],
        "security_issues": [],
        "oss_issues": [],
        "ecs_issues": [],
        "rds_issues": [],
        "slb_issues": [],
        "unattached_eips": [],
        "naming_violations": [],
        "failed_regions": []
    }

    # Scan regions concurrently
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_region = {
            executor.submit(scan_single_region, region): region
            for region in regions
        }

        for i, future in enumerate(as_completed(future_to_region), 1):
            region = future_to_region[future]
            logger.info(f"[{i}/{len(regions)}] Completed scan for region: {region}")

            try:
                region_result = future.result()

                if region_result["error"]:
                    all_results["failed_regions"].append({
                        "region": region,
                        "error": region_result["error"]
                    })

                # Merge results
                all_results["vpc_analysis"].extend(region_result["vpc_analysis"])
                all_results["security_issues"].extend(region_result["security_issues"])
                all_results["ecs_issues"].extend(region_result["ecs_issues"])
                all_results["rds_issues"].extend(region_result["rds_issues"])
                all_results["slb_issues"].extend(region_result["slb_issues"])
                all_results["unattached_eips"].extend(region_result["unattached_eips"])
                all_results["naming_violations"].extend(region_result["naming_violations"])

                # Update region summary
                all_results["summary_by_region"][region] = {
                    "vpcs": len(region_result["vpcs"]),
                    "security_issues": len(region_result["security_issues"]),
                    "oss_issues": 0,  # OSS is global, scanned separately
                    "ecs_issues": len(region_result["ecs_issues"]),
                    "rds_issues": len(region_result["rds_issues"]),
                    "slb_issues": len(region_result["slb_issues"]),
                    "unattached_eips": len(region_result["unattached_eips"])
                }

            except Exception as e:
                logger.error(f"Error processing results for region {region}: {e}")
                all_results["failed_regions"].append({"region": region, "error": str(e)})

    # Scan OSS globally (not region-specific)
    logger.info("Scanning OSS buckets (global)")
    try:
        all_results["oss_issues"] = scan_oss_buckets(regions[:1] if regions else ["cn-hangzhou"])
    except Exception as e:
        logger.error(f"Error scanning OSS: {e}")

    # Calculate totals
    all_results["summary"] = {
        "vpcs": len(all_results["vpc_analysis"]),
        "unused_vpcs": len([v for v in all_results["vpc_analysis"] if v.get("status") == "unused"]),
        "security_issues": len(all_results["security_issues"]),
        "public_oss_buckets": len(set(b.get("bucket_name") for b in all_results["oss_issues"])),
        "low_utilization_ecs": len([
            e for e in all_results["ecs_issues"]
            if any(i.get("type") == "low_cpu_usage" for i in e.get("issues", []))
        ]),
        "unattached_eips": len(all_results["unattached_eips"]),
        "naming_violations": len(all_results["naming_violations"]),
        "rds_issues": len(all_results["rds_issues"]),
        "slb_issues": len(all_results["slb_issues"])
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

    parser = argparse.ArgumentParser(description="Aliyun Resource Manager")
    parser.add_argument("--regions", help="Comma-separated regions or 'all'")
    parser.add_argument("--output", default="./reports", help="Output directory")
    parser.add_argument("--mode", choices=["manual", "scheduled"], default="manual")
    parser.add_argument("--scan", choices=["vpc", "security", "oss", "ecs", "eip", "full"], default="full")
    parser.add_argument("--max-workers", type=int, default=5, help="Maximum concurrent region scans (default: 5)")

    args = parser.parse_args()

    # Set regions if provided
    if args.regions:
        os.environ["ALIYUN_REGIONS"] = args.regions

    # Run scan
    if args.scan == "full":
        results = full_scan(output_dir=args.output, scan_type=args.mode, max_workers=args.max_workers)
    elif args.scan == "vpc":
        results = scan_vpcs(output_dir=args.output, scan_type=args.mode)
    elif args.scan == "security":
        results = scan_security()
    elif args.scan == "oss":
        results = scan_oss()
    elif args.scan == "ecs":
        results = scan_ecs()
    elif args.scan == "eip":
        results = scan_eips()

    print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
