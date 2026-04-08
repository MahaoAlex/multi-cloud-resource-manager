#!/usr/bin/env python3
"""
EC2 monitor module for AWS resource optimization.
Monitors EC2 instances for low CPU utilization and naming convention compliance.
"""

import os
import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any


def run_aws_command(
    service: str,
    operation: str,
    region: str,
    args: List[str] = None
) -> Dict[str, Any]:
    """
    Execute AWS CLI command and return parsed JSON response.

    Args:
        service: AWS service (ec2, cloudwatch, etc.)
        operation: Operation to perform (describe-instances, etc.)
        region: Region ID
        args: Additional command arguments

    Returns:
        dict: Parsed JSON response or error info
    """
    cmd = ['aws', service, operation, '--region', region, '--output', 'json']
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON response", "raw": result.stdout}

        return {
            "error": result.stderr.strip() or "Command failed",
            "returncode": result.returncode
        }

    except subprocess.TimeoutExpired:
        return {"error": "Command timeout"}
    except FileNotFoundError:
        return {"error": "aws CLI not found"}
    except Exception as e:
        return {"error": str(e)}


def get_ec2_instances(region: str) -> List[Dict[str, Any]]:
    """
    List all EC2 instances in a region.

    Args:
        region: Region ID

    Returns:
        list: List of EC2 instance dictionaries
    """
    response = run_aws_command('ec2', 'describe-instances', region)

    if 'error' in response:
        return []

    # Extract instances from response
    instances = []
    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instance['region'] = region
            instances.append(instance)

    return instances


def get_cpu_metrics(
    region: str,
    instance_id: str,
    days: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Get CPU utilization metrics for an EC2 instance.

    Args:
        region: Region ID
        instance_id: EC2 instance ID
        days: Number of days to query (default 1)

    Returns:
        dict: Metric data or None if failed
    """
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    # Format timestamps for AWS CloudWatch API
    from_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_time = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    metric_args = [
        '--namespace', 'AWS/EC2',
        '--metric-name', 'CPUUtilization',
        '--start-time', from_time,
        '--end-time', to_time,
        '--period', '86400',  # 1 day aggregation
        '--statistics', 'Average',
        '--dimensions', f'Name=InstanceId,Value={instance_id}'
    ]

    response = run_aws_command(
        'cloudwatch',
        'get-metric-statistics',
        region,
        metric_args
    )

    if 'error' in response:
        return None

    return response


def calculate_avg_cpu(metrics_data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate average CPU from metric data.

    Args:
        metrics_data: Metric data from CloudWatch API

    Returns:
        float: Average CPU percentage or None
    """
    datapoints = metrics_data.get('Datapoints', [])

    if not datapoints:
        return None

    values = []
    for point in datapoints:
        value = point.get('Average')
        if value is not None:
            try:
                values.append(float(value))
            except (ValueError, TypeError):
                continue

    if not values:
        return None

    return sum(values) / len(values)


def check_naming_convention(name: str) -> bool:
    """
    Check if instance name follows naming convention.
    Convention: contains at least 6 consecutive digits.

    Args:
        name: Instance name

    Returns:
        bool: True if compliant, False otherwise
    """
    if not name:
        return False

    # Check for at least 6 consecutive digits
    return bool(re.search(r'\d{6,}', name))


def get_instance_name(instance: Dict[str, Any]) -> str:
    """
    Get instance name from tags.

    Args:
        instance: EC2 instance data

    Returns:
        str: Instance name or empty string
    """
    for tag in instance.get('Tags', []):
        if tag.get('Key') == 'Name':
            return tag.get('Value', '')
    return ''


def analyze_ec2_instance(
    instance: Dict[str, Any],
    region: str
) -> Dict[str, Any]:
    """
    Analyze a single EC2 instance for issues.

    Args:
        instance: EC2 instance data
        region: Region ID

    Returns:
        dict: Analysis result with issues found
    """
    instance_id = instance.get('InstanceId', '')
    instance_name = get_instance_name(instance)
    vpc_id = instance.get('VpcId', '')

    result = {
        "instance_id": instance_id,
        "instance_name": instance_name,
        "region": region,
        "vpc_id": vpc_id,
        "issues": []
    }

    # Check naming convention
    if not check_naming_convention(instance_name):
        result["issues"].append({
            "type": "naming_violation",
            "severity": "warning",
            "details": {
                "current_name": instance_name,
                "expected_pattern": "contains at least 6 consecutive digits"
            }
        })

    # Check CPU utilization
    metrics_data = get_cpu_metrics(region, instance_id)
    if metrics_data:
        avg_cpu = calculate_avg_cpu(metrics_data)
        if avg_cpu is not None and avg_cpu < 10.0:
            result["issues"].append({
                "type": "low_cpu_usage",
                "severity": "info",
                "details": {
                    "avg_cpu_24h": f"{avg_cpu:.1f}%"
                }
            })

    return result


def monitor_ec2_instances(
    regions: List[str],
    cpu_threshold: float = 10.0,
    check_naming: bool = True
) -> List[Dict[str, Any]]:
    """
    Monitor EC2 instances across multiple regions.

    Args:
        regions: List of region IDs to scan
        cpu_threshold: CPU utilization threshold
        check_naming: Whether to check naming conventions

    Returns:
        list: List of EC2 instances with issues
    """
    all_issues = []

    for region in regions:
        print(f"  Scanning EC2 in region: {region}")

        instances = get_ec2_instances(region)

        if not instances:
            print(f"    No EC2 instances found or error occurred")
            continue

        print(f"    Found {len(instances)} EC2 instances")

        for instance in instances:
            # Only check running instances for CPU
            state = instance.get('State', {}).get('Name', '')
            if state != 'running':
                continue

            analysis = analyze_ec2_instance(instance, region)

            # Only include instances with issues
            if analysis["issues"]:
                all_issues.append(analysis)

    return all_issues


def format_ec2_report(ec2_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format EC2 monitoring results into report structure.

    Args:
        ec2_issues: List of EC2 issues

    Returns:
        dict: Formatted report
    """
    return {
        "ec2_issues": ec2_issues,
        "summary": {
            "total_instances_with_issues": len(ec2_issues),
            "low_cpu_count": sum(
                1 for i in ec2_issues
                if any(issue["type"] == "low_cpu_usage" for issue in i["issues"])
            ),
            "naming_violations": sum(
                1 for i in ec2_issues
                if any(issue["type"] == "naming_violation" for issue in i["issues"])
            )
        }
    }


if __name__ == "__main__":
    # Test mode - requires environment variables to be set
    regions_str = os.environ.get('AWS_REGIONS', 'us-east-1')
    regions = [r.strip() for r in regions_str.split(',')]

    print("EC2 Monitor - Resource Optimization Tool")
    print("=" * 60)
    print()

    issues = monitor_ec2_instances(regions)

    report = format_ec2_report(issues)

    print()
    print("Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
