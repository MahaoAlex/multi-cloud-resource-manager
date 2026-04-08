#!/usr/bin/env python3
"""
Security Scanner Tool for AWS Resource Manager

Scans security groups for high-risk configurations including:
- Ports 22, 33, 44 open to 0.0.0.0/0 or ::/0
- Overly permissive outbound rules
"""

import json
import subprocess
import logging
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# High-risk ports to check
HIGH_RISK_PORTS = [22, 33, 44]

# High-risk remote IPs (open to internet)
HIGH_RISK_REMOTE_IPS = ["0.0.0.0/0", "::/0"]


def run_aws_command(service: str, operation: str, args: List[str], region: str) -> Optional[Dict[str, Any]]:
    """
    Execute AWS CLI command and return parsed JSON output.

    Args:
        service: AWS service name
        operation: API operation
        args: Command arguments as list
        region: Region to query

    Returns:
        Parsed JSON response or None if command fails
    """
    full_command = [
        "aws", service, operation,
        "--region", region,
        "--output", "json"
    ] + args

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


def parse_port_range(from_port: int, to_port: int) -> List[int]:
    """
    Parse port range into list of individual ports.

    Args:
        from_port: Starting port
        to_port: Ending port

    Returns:
        List of port numbers
    """
    if from_port == -1 and to_port == -1:
        # All ports
        return list(range(1, 65536))

    return list(range(from_port, to_port + 1))


def check_security_group_rule(rule: Dict[str, Any], direction: str = "ingress") -> Optional[Dict[str, Any]]:
    """
    Check if a security group rule has high-risk configuration.

    Args:
        rule: Security group rule dictionary
        direction: Rule direction (ingress or egress)

    Returns:
        Issue details if high-risk, None otherwise
    """
    # Get rule properties
    ip_protocol = rule.get("IpProtocol", "").lower()
    from_port = rule.get("FromPort", -1)
    to_port = rule.get("ToPort", -1)

    # Check if protocol is TCP or all
    if ip_protocol not in ["tcp", "-1"]:
        return None

    # Check IPv4 ranges
    ip_ranges = rule.get("IpRanges", [])
    has_public_ip = any(r.get("CidrIp") in HIGH_RISK_REMOTE_IPS for r in ip_ranges)

    # Check IPv6 ranges
    ipv6_ranges = rule.get("Ipv6Ranges", [])
    has_public_ipv6 = any(r.get("CidrIpv6") in HIGH_RISK_REMOTE_IPS for r in ipv6_ranges)

    if not has_public_ip and not has_public_ipv6:
        return None

    # Parse port range and check for high-risk ports
    ports = parse_port_range(from_port, to_port)
    risky_ports = [p for p in ports if p in HIGH_RISK_PORTS]

    if not risky_ports:
        return None

    # Determine risk level
    risk_level = "critical" if 22 in risky_ports else "high"

    remote_ip = "0.0.0.0/0" if has_public_ip else "::/0"

    return {
        "ports": risky_ports,
        "protocol": "all" if ip_protocol == "-1" else ip_protocol,
        "remote_ip": remote_ip,
        "direction": direction,
        "risk_level": risk_level
    }


def get_security_group_rules(security_group_id: str, region: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all rules for a security group.

    Args:
        security_group_id: Security group ID
        region: Region name

    Returns:
        Dictionary with ingress and egress rules
    """
    response = run_aws_command(
        "ec2", "describe-security-groups",
        ["--group-ids", security_group_id],
        region
    )

    if not response:
        return {"ingress": [], "egress": []}

    security_groups = response.get("SecurityGroups", [])
    if not security_groups:
        return {"ingress": [], "egress": []}

    sg = security_groups[0]
    return {
        "ingress": sg.get("IpPermissions", []),
        "egress": sg.get("IpPermissionsEgress", [])
    }


def scan_security_group(security_group: Dict[str, Any], region: str) -> List[Dict[str, Any]]:
    """
    Scan a single security group for issues.

    Args:
        security_group: Security group dictionary
        region: Region name

    Returns:
        List of security issues found
    """
    issues = []

    sg_id = security_group.get("GroupId", "unknown")
    sg_name = security_group.get("GroupName", "unknown")
    vpc_id = security_group.get("VpcId", "unknown")

    # Get all rules for this security group
    rules = get_security_group_rules(sg_id, region)

    # Check ingress rules
    for rule in rules.get("ingress", []):
        issue_details = check_security_group_rule(rule, "ingress")
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

    # Check egress rules
    for rule in rules.get("egress", []):
        issue_details = check_security_group_rule(rule, "egress")
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
                "recommendation": "restrict_destination_ip_range"
            })

    return issues


def get_security_groups(region: str) -> List[Dict[str, Any]]:
    """
    Get all security groups in a region.

    Args:
        region: Region name

    Returns:
        List of security groups
    """
    response = run_aws_command("ec2", "describe-security-groups", [], region)

    if not response:
        return []

    return response.get("SecurityGroups", [])


def scan_security_groups(regions: List[str]) -> List[Dict[str, Any]]:
    """
    Scan security groups across multiple regions for high-risk configurations.

    Args:
        regions: List of region names to scan

    Returns:
        List of security issues found across all regions
    """
    all_issues = []

    logger.info(f"Starting security group scan for {len(regions)} region(s)")

    for region in regions:
        logger.info(f"Scanning region: {region}")

        try:
            security_groups = get_security_groups(region)

            if not security_groups:
                logger.info(f"No security groups found in region {region}")
                continue

            logger.info(f"Found {len(security_groups)} security groups in {region}")

            for sg in security_groups:
                issues = scan_security_group(sg, region)
                all_issues.extend(issues)

                if issues:
                    logger.warning(
                        f"Found {len(issues)} issue(s) in security group "
                        f"{sg.get('GroupName', 'unknown')} ({sg.get('GroupId', 'unknown')})"
                    )

        except Exception as e:
            logger.error(f"Error scanning region {region}: {e}")
            continue

    logger.info(f"Security scan complete. Found {len(all_issues)} issue(s) total.")
    return all_issues


def main():
    """Main entry point for testing."""
    import os

    # Get regions from environment or use default
    regions_env = os.environ.get("AWS_REGIONS", "us-east-1")
    regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    issues = scan_security_groups(regions)

    # Output results as JSON
    print(json.dumps({"security_issues": issues}, indent=2))


if __name__ == "__main__":
    main()
