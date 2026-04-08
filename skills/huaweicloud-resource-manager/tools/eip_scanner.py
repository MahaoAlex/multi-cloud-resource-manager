#!/usr/bin/env python3
"""
EIP scanner module for Huawei Cloud resource optimization.
Detects unattached Elastic IPs that may be wasting resources.
"""

import os
import subprocess
import json
import logging
from typing import List, Dict, Any, Optional

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
            if 'multi-version API' in line or line.startswith('List'):
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
        service: Huawei Cloud service (eip, etc.)
        action: Action to perform (ListPublicips, etc.)
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


def get_eips(region: str, credentials: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    List all Elastic IPs in a region.

    Args:
        region: Region ID
        credentials: Optional credentials dict

    Returns:
        list: List of EIP dictionaries
    """
    response = run_hcloud_command('EIP', 'ListPublicips', region, credentials=credentials)

    if 'error' in response:
        logger.warning(f"Failed to get EIPs: {response.get('error')}")
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


def scan_unattached_eips(
    regions: List[str],
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan for unattached EIPs across multiple regions.

    Args:
        regions: List of region IDs to scan
        credentials: Optional credentials dict

    Returns:
        list: List of unattached EIP information
    """
    # Validate environment before starting
    try:
        validate_env()
    except ValueError as e:
        logger.error(f"Environment validation failed: {e}")
        raise

    if credentials is None:
        credentials = get_credentials()

    unattached_eips = []

    for region in regions:
        logger.info(f"Scanning EIPs in region: {region}")

        eips = get_eips(region, credentials)

        if not eips:
            logger.info(f"No EIPs found in {region}")
            continue

        logger.info(f"Found {len(eips)} EIPs in {region}")

        unattached_count = 0
        for eip in eips:
            if is_eip_unattached(eip):
                eip_info = extract_eip_info(eip, region)
                unattached_eips.append(eip_info)
                unattached_count += 1

        if unattached_count > 0:
            logger.info(f"Found {unattached_count} unattached EIPs in {region}")

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
