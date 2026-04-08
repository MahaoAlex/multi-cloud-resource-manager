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
from report_generator import ReportGenerator
from rule_engine import RuleEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


def full_scan(
    regions: Optional[List[str]] = None,
    output_dir: str = "./reports",
    scan_type: str = "manual",
    retention_days: int = 7
) -> Dict[str, Any]:
    """
    Perform complete resource scan across all categories.

    Args:
        regions: List of regions to scan
        output_dir: Directory for reports
        scan_type: 'manual' or 'scheduled'
        retention_days: Days to keep reports

    Returns:
        Complete scan results
    """
    if regions is None:
        regions = get_regions_from_env()

    logger.info(f"Starting full scan for {len(regions)} region(s)")
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
        "unattached_eips": [],
        "naming_violations": [],
        "failed_regions": []
    }

    # Scan each region
    for i, region in enumerate(regions, 1):
        logger.info(f"[{i}/{len(regions)}] Scanning region: {region}")

        try:
            # VPC inventory and analysis
            vpc_data = get_vpc_inventory([region])
            for vpc in vpc_data.get("vpcs", []):
                analysis = analyze_vpc_usage(vpc.get("id"), region)
                all_results["vpc_analysis"].append(analysis)

            # Security scan
            sec_issues = scan_security_groups([region])
            all_results["security_issues"].extend(sec_issues)

            # OSS scan
            oss_issues = scan_oss_buckets([region])
            all_results["oss_issues"].extend(oss_issues)

            # ECS scan
            ecs_issues = monitor_ecs_instances([region])
            all_results["ecs_issues"].extend(ecs_issues)

            # Naming violations from ECS issues
            for ecs in ecs_issues:
                for issue in ecs.get("issues", []):
                    if issue.get("type") == "naming_violation":
                        all_results["naming_violations"].append({
                            "resource_type": "ecs",
                            "resource_id": ecs.get("instance_id"),
                            "resource_name": ecs.get("instance_name"),
                            "region": region
                        })

            # EIP scan
            eips = scan_unattached_eips([region])
            all_results["unattached_eips"].extend(eips)

            # Update region summary
            all_results["summary_by_region"][region] = {
                "vpcs": len(vpc_data.get("vpcs", [])),
                "security_issues": len(sec_issues),
                "oss_issues": len(oss_issues),
                "ecs_issues": len(ecs_issues),
                "unattached_eips": len(eips)
            }

        except Exception as e:
            logger.error(f"Error scanning region {region}: {e}")
            all_results["failed_regions"].append({"region": region, "error": str(e)})

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
        "naming_violations": len(all_results["naming_violations"])
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

    args = parser.parse_args()

    # Set regions if provided
    if args.regions:
        os.environ["ALIYUN_REGIONS"] = args.regions

    # Run scan
    if args.scan == "full":
        results = full_scan(output_dir=args.output, scan_type=args.mode)
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
