#!/usr/bin/env python3
"""
Security Scanner Tool for Huawei Cloud Resource Manager

Scans security groups for high-risk configurations including:
- Ports 22, 33, 44 open to 0.0.0.0/0 or ::/0
- Overly permissive outbound rules
"""

import json
import subprocess
import logging
import os
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# High-risk ports to check
HIGH_RISK_PORTS = [22, 33, 44, 3389, 3306, 5432, 6379, 1433]

# High-risk remote IPs (open to internet)
HIGH_RISK_REMOTE_IPS = ["0.0.0.0/0", "::/0"]


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
    command: List[str],
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> Optional[Dict[str, Any]]:
    """
    Execute hcloud CLI command and return parsed JSON output.

    Args:
        command: Command and arguments as list
        region: Region to query
        credentials: Optional credentials dict

    Returns:
        Parsed JSON response or None if command fails
    """
    if credentials is None:
        credentials = get_credentials()

    # Build command with proper CLI parameters
    full_command = ["hcloud"] + command

    # Add authentication parameters
    if credentials.get('access_key'):
        full_command.extend([f"--cli-access-key={credentials['access_key']}"])
    if credentials.get('secret_key'):
        full_command.extend([f"--cli-secret-key={credentials['secret_key']}"])
    if credentials.get('project_id'):
        full_command.extend([f"--cli-project-id={credentials['project_id']}"])

    # Add region
    full_command.extend([f"--cli-region={region}"])

    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            logger.error(f"Command failed: {' '.join(command)}")
            logger.error(f"Error: {result.stderr}")
            return None

        return parse_hcloud_output(result.stdout)

    except subprocess.TimeoutExpired:
        logger.error(f"Command timeout: {' '.join(command)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error running command: {e}")
        return None


def parse_port_range(port_range: str) -> List[int]:
    """
    Parse port range string into list of individual ports.

    Args:
        port_range: Port range string (e.g., "22", "20-30", "1-65535")

    Returns:
        List of port numbers
    """
    ports = []

    if not port_range or port_range.lower() in ["any", "", None]:
        # If port is 'any', it means all ports
        return list(range(1, 65536))

    if "-" in str(port_range):
        try:
            start, end = str(port_range).split("-")
            ports = list(range(int(start), int(end) + 1))
        except ValueError:
            logger.warning(f"Invalid port range format: {port_range}")
    else:
        try:
            ports = [int(port_range)]
        except ValueError:
            logger.warning(f"Invalid port format: {port_range}")

    return ports


def check_security_group_rule(rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Check if a security group rule has high-risk configuration.

    Args:
        rule: Security group rule dictionary

    Returns:
        Issue details if high-risk, None otherwise
    """
    # Get rule properties
    protocol = rule.get("protocol", "").lower()
    remote_ip = rule.get("remote_ip_prefix", "")
    port_range = rule.get("multiport") or rule.get("port_range", "")
    direction = rule.get("direction", "ingress")

    # Only check ingress rules
    if direction != "ingress":
        return None

    # Check if remote IP is open to internet
    if remote_ip not in HIGH_RISK_REMOTE_IPS:
        return None

    # Check if protocol is TCP or ALL
    if protocol not in ["tcp", "all", "any", "", None]:
        return None

    # Parse port range and check for high-risk ports
    ports = parse_port_range(port_range)
    risky_ports = [p for p in ports if p in HIGH_RISK_PORTS]

    if not risky_ports:
        return None

    # Determine risk level
    if 22 in risky_ports or 3389 in risky_ports:
        risk_level = "critical"
    elif any(p in [3306, 5432, 6379, 1433] for p in risky_ports):
        risk_level = "high"
    else:
        risk_level = "medium"

    return {
        "ports": risky_ports,
        "protocol": protocol if protocol else "all",
        "remote_ip": remote_ip,
        "direction": direction,
        "risk_level": risk_level
    }


def get_security_group_rules(
    security_group_id: str,
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Get all rules for a security group.

    Args:
        security_group_id: Security group ID
        region: Region name
        credentials: Optional credentials dict

    Returns:
        List of security group rules
    """
    if credentials is None:
        credentials = get_credentials()

    # Use proper parameter format for ListSecurityGroupRules
    command = ["VPC", "ListSecurityGroupRules", f"--security_group_id={security_group_id}"]

    response = run_hcloud_command(command, region, credentials)

    if not response:
        return []

    # Handle different response formats
    if isinstance(response, dict):
        return response.get("security_group_rules", [])
    elif isinstance(response, list):
        return response

    return []


def scan_security_group(
    security_group: Dict[str, Any],
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan a single security group for issues.

    Args:
        security_group: Security group dictionary
        region: Region name
        credentials: Optional credentials dict

    Returns:
        List of security issues found
    """
    if credentials is None:
        credentials = get_credentials()

    issues = []

    sg_id = security_group.get("id") or security_group.get("security_group_id", "unknown")
    sg_name = security_group.get("name", "unknown")
    vpc_id = security_group.get("vpc_id", "unknown")

    # Get all rules for this security group
    rules = get_security_group_rules(sg_id, region, credentials)

    for rule in rules:
        issue_details = check_security_group_rule(rule)
        if issue_details:
            issues.append({
                "security_group_id": sg_id,
                "security_group_name": sg_name,
                "vpc_id": vpc_id,
                "region": region,
                "risk_level": issue_details["risk_level"],
                "issue_type": "open_ports",
                "details": {
                    "ports": issue_details["ports"],
                    "protocol": issue_details["protocol"],
                    "remote_ip": issue_details["remote_ip"],
                    "direction": issue_details["direction"]
                },
                "recommendation": "restrict_source_ip_range"
            })

    return issues


def get_security_groups(
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Get all security groups in a region.

    Args:
        region: Region name
        credentials: Optional credentials dict

    Returns:
        List of security groups
    """
    if credentials is None:
        credentials = get_credentials()

    response = run_hcloud_command(["VPC", "ListSecurityGroups"], region, credentials)

    if not response:
        return []

    # Handle different response formats
    if isinstance(response, dict):
        return response.get("security_groups", [])
    elif isinstance(response, list):
        return response

    return []


def scan_security_groups(
    regions: List[str],
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan security groups across multiple regions for high-risk configurations.

    Args:
        regions: List of region names to scan
        credentials: Optional credentials dict

    Returns:
        List of security issues found across all regions
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

    logger.info(f"Starting security group scan for {len(regions)} region(s)")

    for region in regions:
        logger.info(f"Scanning region: {region}")

        try:
            security_groups = get_security_groups(region, credentials)

            if not security_groups:
                logger.info(f"No security groups found in region {region}")
                continue

            logger.info(f"Found {len(security_groups)} security groups in {region}")

            for sg in security_groups:
                issues = scan_security_group(sg, region, credentials)
                all_issues.extend(issues)

                if issues:
                    logger.warning(
                        f"Found {len(issues)} issue(s) in security group "
                        f"{sg.get('name', 'unknown')} ({sg.get('id', 'unknown')})"
                    )

        except Exception as e:
            logger.error(f"Error scanning region {region}: {e}")
            continue

    logger.info(f"Security scan complete. Found {len(all_issues)} issue(s) total.")
    return all_issues


def main():
    """Main entry point for testing."""
    # Get regions from environment or use default
    regions_env = os.environ.get("HWCLOUD_REGIONS", "cn-north-4")
    regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    issues = scan_security_groups(regions)

    # Output results as JSON
    print(json.dumps({"security_issues": issues}, indent=2))


if __name__ == "__main__":
    main()
