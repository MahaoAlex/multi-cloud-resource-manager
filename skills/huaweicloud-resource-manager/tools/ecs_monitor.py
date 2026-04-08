#!/usr/bin/env python3
"""
ECS monitor module for Huawei Cloud resource optimization.
Monitors ECS instances for low CPU utilization and naming convention compliance.
"""

import os
import subprocess
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any


def run_hcloud_command(
    service: str,
    action: str,
    region: str,
    args: List[str] = None
) -> Dict[str, Any]:
    """
    Execute hcloud CLI command and return parsed JSON response.

    Args:
        service: Huawei Cloud service (ecs, ces, etc.)
        action: Action to perform (ListServers, ListMetrics, etc.)
        region: Region ID
        args: Additional command arguments

    Returns:
        dict: Parsed JSON response or error info
    """
    cmd = ['hcloud', service, action]
    if args:
        cmd.extend(args)

    try:
        env = os.environ.copy()
        env['HWCLOUD_REGION'] = region

        result = subprocess.run(
            cmd,
            env=env,
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
        return {"error": "hcloud CLI not found"}
    except Exception as e:
        return {"error": str(e)}


def get_ecs_instances(region: str) -> List[Dict[str, Any]]:
    """
    List all ECS instances in a region.

    Args:
        region: Region ID

    Returns:
        list: List of ECS instance dictionaries
    """
    response = run_hcloud_command('ecs', 'ListServers', region)

    if 'error' in response:
        return []

    # Extract servers from response
    servers = response.get('servers', [])
    if not servers and 'servers' in str(response):
        # Try alternative response format
        servers = response.get('servers', [])

    # Add region to each server
    for server in servers:
        server['region'] = region

    return servers


def get_cpu_metrics(
    region: str,
    instance_id: str,
    days: int = 1
) -> Optional[Dict[str, Any]]:
    """
    Get CPU utilization metrics for an ECS instance.

    Args:
        region: Region ID
        instance_id: ECS instance ID
        days: Number of days to query (default 1)

    Returns:
        dict: Metric data or None if failed
    """
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)

    # Format timestamps for Huawei Cloud CES API
    from_time = start_time.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_time = end_time.strftime('%Y-%m-%dT%H:%M:%SZ')

    # First, list metrics to get the correct metric name
    list_response = run_hcloud_command(
        'ces',
        'ListMetrics',
        region,
        ['--namespace', 'SYS.ECS', '--dim.0', f'instance_id,{instance_id}']
    )

    if 'error' in list_response:
        return None

    metrics = list_response.get('metrics', [])
    cpu_metric = None

    for metric in metrics:
        if metric.get('metric_name') == 'cpu_util':
            cpu_metric = metric
            break

    if not cpu_metric:
        return None

    # Get metric data
    metric_args = [
        '--namespace', 'SYS.ECS',
        '--metric-name', 'cpu_util',
        '--from', from_time,
        '--to', to_time,
        '--period', '86400',  # 1 day aggregation
        '--filter', 'average',
        '--dim.0', f'instance_id,{instance_id}'
    ]

    data_response = run_hcloud_command(
        'ces',
        'ShowMetricData',
        region,
        metric_args
    )

    if 'error' in data_response:
        return None

    return data_response


def calculate_avg_cpu(metrics_data: Dict[str, Any]) -> Optional[float]:
    """
    Calculate average CPU from metric data.

    Args:
        metrics_data: Metric data from CES API

    Returns:
        float: Average CPU percentage or None
    """
    datapoints = metrics_data.get('datapoints', [])

    if not datapoints:
        return None

    values = []
    for point in datapoints:
        value = point.get('average')
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


def analyze_ecs_instance(
    instance: Dict[str, Any],
    region: str
) -> Dict[str, Any]:
    """
    Analyze a single ECS instance for issues.

    Args:
        instance: ECS instance data
        region: Region ID

    Returns:
        dict: Analysis result with issues found
    """
    instance_id = instance.get('id', '')
    instance_name = instance.get('name', '')
    vpc_id = instance.get('vpc_id', instance.get('metadata', {}).get('vpc_id', ''))

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


def monitor_ecs_instances(regions: List[str]) -> List[Dict[str, Any]]:
    """
    Monitor ECS instances across multiple regions.

    Args:
        regions: List of region IDs to scan

    Returns:
        list: List of ECS instances with issues
    """
    all_issues = []

    for region in regions:
        print(f"  Scanning ECS in region: {region}")

        instances = get_ecs_instances(region)

        if not instances:
            print(f"    No ECS instances found or error occurred")
            continue

        print(f"    Found {len(instances)} ECS instances")

        for instance in instances:
            analysis = analyze_ecs_instance(instance, region)

            # Only include instances with issues
            if analysis["issues"]:
                all_issues.append(analysis)

    return all_issues


def format_ecs_report(ecs_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format ECS monitoring results into report structure.

    Args:
        ecs_issues: List of ECS issues

    Returns:
        dict: Formatted report
    """
    return {
        "ecs_issues": ecs_issues,
        "summary": {
            "total_instances_with_issues": len(ecs_issues),
            "low_cpu_count": sum(
                1 for i in ecs_issues
                if any(issue["type"] == "low_cpu_usage" for issue in i["issues"])
            ),
            "naming_violations": sum(
                1 for i in ecs_issues
                if any(issue["type"] == "naming_violation" for issue in i["issues"])
            )
        }
    }


if __name__ == "__main__":
    # Test mode - requires environment variables to be set
    regions_str = os.environ.get('HWCLOUD_REGIONS', 'cn-north-4')
    regions = [r.strip() for r in regions_str.split(',')]

    print("ECS Monitor - Resource Optimization Tool")
    print("=" * 60)
    print()

    issues = monitor_ecs_instances(regions)

    report = format_ecs_report(issues)

    print()
    print("Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
