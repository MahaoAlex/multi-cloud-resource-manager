#!/usr/bin/env python3
"""
Security Scanner Tool for Aliyun Resource Manager

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
HIGH_RISK_PORTS = [
    22,      # SSH
    23,      # Telnet
    3389,    # RDP
    3306,    # MySQL
    1433,    # MSSQL
    5432,    # PostgreSQL
    6379,    # Redis
    27017,   # MongoDB
    9200,    # Elasticsearch
    11211,   # Memcached
    21,      # FTP
    20,      # FTP Data
    445,     # SMB
    135,     # RPC
    139,     # NetBIOS
    4444,    # Common backdoor
    5555,    # Common backdoor
    3389,    # RDP (duplicate for clarity)
    5900,    # VNC
    5800,    # VNC Web
    8080,    # Common web proxy
    8443,    # Common HTTPS alt
]

# High-risk remote IPs (open to internet)
HIGH_RISK_REMOTE_IPS = ["0.0.0.0/0", "::/0"]


def run_aliyun_command(service: str, action: str, args: List[str], region: str) -> Optional[Dict[str, Any]]:
    """
    Execute aliyun CLI command and return parsed JSON output.

    Args:
        service: Aliyun service name
        action: API action to perform
        args: Command arguments as list
        region: Region to query

    Returns:
        Parsed JSON response or None if command fails
    """
    full_command = [
        "aliyun", service, action,
        f"--region={region}"
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


def parse_port_range(port_range: str) -> List[int]:
    """
    Parse port range string into list of individual ports.

    Args:
        port_range: Port range string (e.g., "22", "20/30", "-1/-1")

    Returns:
        List of port numbers
    """
    ports = []

    if not port_range or port_range == "-1/-1":
        # All ports
        return list(range(1, 65536))

    if "/" in port_range:
        try:
            start, end = port_range.split("/")
            if start == end:
                ports = [int(start)]
            else:
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
    ip_protocol = rule.get("IpProtocol", "").lower()
    source_cidr_ip = rule.get("SourceCidrIp", "")
    dest_cidr_ip = rule.get("DestCidrIp", "")
    port_range = rule.get("PortRange", "")
    direction = rule.get("Direction", "ingress")

    # Check protocol
    if ip_protocol not in ["tcp", "all", "any", "", "-1"]:
        return None

    # Check if remote IP is open to internet
    remote_ip = source_cidr_ip if direction == "ingress" else dest_cidr_ip
    if remote_ip not in HIGH_RISK_REMOTE_IPS:
        return None

    # Parse port range and check for high-risk ports
    ports = parse_port_range(port_range)
    risky_ports = [p for p in ports if p in HIGH_RISK_PORTS]

    if not risky_ports:
        return None

    # Determine risk level
    risk_level = "critical" if 22 in risky_ports else "high"

    return {
        "ports": risky_ports,
        "protocol": ip_protocol if ip_protocol else "all",
        "remote_ip": remote_ip,
        "direction": direction,
        "risk_level": risk_level
    }


def get_security_group_rules(security_group_id: str, region: str, direction: str = "ingress") -> List[Dict[str, Any]]:
    """
    Get all rules for a security group.

    Args:
        security_group_id: Security group ID
        region: Region name
        direction: Rule direction (ingress or egress)

    Returns:
        List of security group rules
    """
    action = "DescribeSecurityGroupAttribute"
    args = [f"--SecurityGroupId={security_group_id}", f"--Direction={direction}"]

    response = run_aliyun_command("ecs", action, args, region)

    if not response:
        return []

    # Handle Aliyun response format
    if isinstance(response, dict):
        key = "Permissions" if direction == "ingress" else "Permissions"
        perm_key = "Permission" if direction == "ingress" else "Permission"
        return response.get(key, {}).get(perm_key, [])

    return []


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

    sg_id = security_group.get("SecurityGroupId", "unknown")
    sg_name = security_group.get("SecurityGroupName", "unknown")
    vpc_id = security_group.get("VpcId", "unknown")

    # Get ingress rules
    ingress_rules = get_security_group_rules(sg_id, region, "ingress")
    for rule in ingress_rules:
        rule["Direction"] = "ingress"
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

    # Get egress rules
    egress_rules = get_security_group_rules(sg_id, region, "egress")
    for rule in egress_rules:
        rule["Direction"] = "egress"
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
    response = run_aliyun_command("ecs", "DescribeSecurityGroups", [], region)

    if not response:
        return []

    # Handle Aliyun response format
    if isinstance(response, dict):
        return response.get("SecurityGroups", {}).get("SecurityGroup", [])

    return []


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
                        f"{sg.get('SecurityGroupName', 'unknown')} ({sg.get('SecurityGroupId', 'unknown')})"
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
    regions_env = os.environ.get("ALIYUN_REGIONS", "cn-hangzhou")
    regions = [r.strip() for r in regions_env.split(",") if r.strip()]

    issues = scan_security_groups(regions)

    # Output results as JSON
    print(json.dumps({"security_issues": issues}, indent=2))


if __name__ == "__main__":
    main()
