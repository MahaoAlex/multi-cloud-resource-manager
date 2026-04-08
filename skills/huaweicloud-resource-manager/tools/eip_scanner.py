#!/usr/bin/env python3
"""
EIP scanner module for Huawei Cloud resource optimization.
Detects unattached Elastic IPs that may be wasting resources.
"""

import os
import subprocess
import json
from typing import List, Dict, Any


def run_hcloud_command(
    service: str,
    action: str,
    region: str,
    args: List[str] = None
) -> Dict[str, Any]:
    """
    Execute hcloud CLI command and return parsed JSON response.

    Args:
        service: Huawei Cloud service (eip, etc.)
        action: Action to perform (ListPublicips, etc.)
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


def get_eips(region: str) -> List[Dict[str, Any]]:
    """
    List all Elastic IPs in a region.

    Args:
        region: Region ID

    Returns:
        list: List of EIP dictionaries
    """
    response = run_hcloud_command('eip', 'ListPublicips', region)

    if 'error' in response:
        return []

    # Extract publicips from response
    eips = response.get('publicips', [])

    # Add region to each EIP
    for eip in eips:
        eip['region'] = region

    return eips


def is_eip_unattached(eip: Dict[str, Any]) -> bool:
    """
    Check if an EIP is unattached.

    Args:
        eip: EIP data dictionary

    Returns:
        bool: True if unattached, False otherwise
    """
    status = eip.get('status', '').lower()

    # Status values that indicate unattached state
    unattached_statuses = ['down', 'unattached', 'free', 'inactive']

    return status in unattached_statuses


def extract_eip_info(eip: Dict[str, Any], region: str) -> Dict[str, Any]:
    """
    Extract relevant information from EIP data.

    Args:
        eip: EIP data dictionary
        region: Region ID

    Returns:
        dict: Formatted EIP information
    """
    eip_id = eip.get('id', '')
    eip_address = eip.get('public_ip_address', eip.get('public_ip', ''))
    status = eip.get('status', 'unknown')

    # Extract created_by from tags if available
    tags = eip.get('tags', [])
    created_by = None

    for tag in tags:
        if isinstance(tag, dict):
            if tag.get('key') == 'created_by':
                created_by = tag.get('value')
                break

    # Try to get from metadata if not in tags
    if not created_by:
        created_by = eip.get('created_by', eip.get('user_id', ''))

    result = {
        "eip_id": eip_id,
        "eip_address": eip_address,
        "region": region,
        "status": status
    }

    if created_by:
        result["created_by"] = created_by

    return result


def scan_unattached_eips(regions: List[str]) -> List[Dict[str, Any]]:
    """
    Scan for unattached EIPs across multiple regions.

    Args:
        regions: List of region IDs to scan

    Returns:
        list: List of unattached EIP information
    """
    unattached_eips = []

    for region in regions:
        print(f"  Scanning EIPs in region: {region}")

        eips = get_eips(region)

        if not eips:
            print(f"    No EIPs found or error occurred")
            continue

        print(f"    Found {len(eips)} EIPs")

        unattached_count = 0
        for eip in eips:
            if is_eip_unattached(eip):
                eip_info = extract_eip_info(eip, region)
                unattached_eips.append(eip_info)
                unattached_count += 1

        if unattached_count > 0:
            print(f"    Found {unattached_count} unattached EIPs")

    return unattached_eips


def format_eip_report(unattached_eips: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format EIP scanning results into report structure.

    Args:
        unattached_eips: List of unattached EIP information

    Returns:
        dict: Formatted report
    """
    # Group by region for summary
    by_region = {}
    for eip in unattached_eips:
        region = eip.get('region', 'unknown')
        if region not in by_region:
            by_region[region] = 0
        by_region[region] += 1

    return {
        "unattached_eips": unattached_eips,
        "summary": {
            "total_unattached": len(unattached_eips),
            "by_region": by_region
        }
    }


if __name__ == "__main__":
    # Test mode - requires environment variables to be set
    regions_str = os.environ.get('HWCLOUD_REGIONS', 'cn-north-4')
    regions = [r.strip() for r in regions_str.split(',')]

    print("EIP Scanner - Resource Optimization Tool")
    print("=" * 60)
    print()

    unattached = scan_unattached_eips(regions)

    report = format_eip_report(unattached)

    print()
    print("Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
