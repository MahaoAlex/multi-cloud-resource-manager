#!/usr/bin/env python3
"""
ECS monitor module for Huawei Cloud resource optimization.
Monitors ECS instances for low CPU utilization and naming convention compliance.
"""

import os
import subprocess
import json
import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
            if 'multi-version API' in line or line.startswith('List') or line.startswith('Nova'):
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
    service: str,
    action: str,
    region: str,
    args: List[str] = None,
    credentials: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Execute hcloud CLI command and return parsed JSON response.

    Args:
        service: Huawei Cloud service (ecs, ces, etc.)
        action: Action to perform (ListServers, ListMetrics, etc.)
        region: Region ID
        args: Additional command arguments
        credentials: Optional credentials dict

    Returns:
        dict: Parsed JSON response or error info
    """
    if credentials is None:
        credentials = get_credentials()

    cmd = ['hcloud', service, action]
    if args:
        cmd.extend(args)

    # Add authentication parameters
    if credentials.get('access_key'):
        cmd.extend([f"--cli-access-key={credentials['access_key']}"])
    if credentials.get('secret_key'):
        cmd.extend([f"--cli-secret-key={credentials['secret_key']}"])
    if credentials.get('project_id'):
        cmd.extend([f"--cli-project-id={credentials['project_id']}"])

    # Add region
    cmd.extend([f"--cli-region={region}"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            parsed = parse_hcloud_output(result.stdout)
            if parsed is not None:
                return parsed
            return {"error": "Invalid JSON response", "raw": result.stdout[:500]}

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


def get_ecs_instances(region: str, credentials: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    List all ECS instances in a region.

    Args:
        region: Region ID
        credentials: Optional credentials dict

    Returns:
        list: List of ECS instance dictionaries
    """
    response = run_hcloud_command('ECS', 'NovaListServers', region, credentials=credentials)

    if 'error' in response:
        logger.warning(f"Failed to get ECS instances: {response.get('error')}")
        return []

    # Extract servers from response
    servers = response.get('servers', [])

    # Add region to each server
    for server in servers:
        server['region'] = region

    return servers


def get_cpu_metrics(
    region: str,
    instance_id: str,
    days: int = 1,
    credentials: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Get CPU utilization metrics for an ECS instance.

    Args:
        region: Region ID
        instance_id: ECS instance ID
        days: Number of days to query (default 1)
        credentials: Optional credentials dict

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
    list_args = [
        '--namespace', 'SYS.ECS',
        '--dim.0', f'instance_id,{instance_id}'
    ]

    list_response = run_hcloud_command(
        'CES',
        'ListMetrics',
        region,
        list_args,
        credentials
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
        'CES',
        'ShowMetricData',
        region,
        metric_args,
        credentials
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
    region: str,
    credentials: Optional[Dict[str, str]] = None,
    cpu_threshold: float = 10.0
) -> Dict[str, Any]:
    """
    Analyze a single ECS instance for issues.

    Args:
        instance: ECS instance data
        region: Region ID
        credentials: Optional credentials dict
        cpu_threshold: CPU utilization threshold for low usage warning

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
    metrics_data = get_cpu_metrics(region, instance_id, credentials=credentials)
    if metrics_data:
        avg_cpu = calculate_avg_cpu(metrics_data)
        if avg_cpu is not None and avg_cpu < cpu_threshold:
            result["issues"].append({
                "type": "low_cpu_usage",
                "severity": "info",
                "details": {
                    "avg_cpu_24h": f"{avg_cpu:.1f}%"
                }
            })

    return result


def monitor_ecs_instances(
    regions: List[str],
    cpu_threshold: float = 10.0,
    check_naming: bool = True,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Monitor ECS instances across multiple regions.

    Args:
        regions: List of region IDs to scan
        cpu_threshold: CPU utilization threshold for low usage warning
        check_naming: Whether to check naming convention compliance
        credentials: Optional credentials dict

    Returns:
        list: List of ECS instances with issues
    """
    # Validate environment before starting
    try:
        validate_env()
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        raise

    if credentials is None:
        credentials = get_credentials()

    all_issues = []

    for region in regions:
        logger.info(f"Scanning ECS in region: {region}")

        instances = get_ecs_instances(region, credentials)

        if not instances:
            logger.info(f"No ECS instances found in {region}")
            continue

        logger.info(f"Found {len(instances)} ECS instances in {region}")

        for instance in instances:
            analysis = analyze_ecs_instance(instance, region, credentials, cpu_threshold)

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
