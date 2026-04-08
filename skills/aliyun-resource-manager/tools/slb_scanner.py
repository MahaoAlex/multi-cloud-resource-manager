#!/usr/bin/env python3
"""
SLB (Server Load Balancer) Scanner for Aliyun Resource Manager

Scans SLB instances for security and configuration issues:
- HTTP listeners (not HTTPS)
- Weak SSL/TLS protocols
- Public exposure
- Unattached load balancers
"""

import json
import subprocess
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_aliyun_command(service: str, action: str, args: List[str], region: str) -> Optional[Dict[str, Any]]:
    """
    Execute aliyun CLI command and return parsed JSON output.
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


def get_slb_instances(region: str) -> List[Dict[str, Any]]:
    """
    Get all SLB instances in a region.
    """
    response = run_aliyun_command("slb", "DescribeLoadBalancers", ["--PageSize=100"], region)

    if not response:
        return []

    load_balancers = response.get("LoadBalancers", {}).get("LoadBalancer", [])
    return load_balancers if isinstance(load_balancers, list) else [load_balancers]


def get_slb_listeners(load_balancer_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get all listeners for an SLB instance.
    """
    # Get HTTP/HTTPS listeners
    response = run_aliyun_command(
        "slb",
        "DescribeLoadBalancerHTTPListenerAttribute",
        [f"--LoadBalancerId={load_balancer_id}"],
        region
    )

    listeners = []

    if response:
        # Check if listener exists (returns error if not)
        if "ListenerPort" in response:
            listeners.append({
                "type": "http",
                "port": response.get("ListenerPort"),
                "protocol": response.get("ListenerProtocol", "http"),
                "backend_port": response.get("BackendServerPort"),
                "bandwidth": response.get("Bandwidth"),
                "status": response.get("Status")
            })

    # Get TCP/UDP listeners
    response = run_aliyun_command(
        "slb",
        "DescribeLoadBalancerTCPListenerAttribute",
        [f"--LoadBalancerId={load_balancer_id}"],
        region
    )

    if response:
        if "ListenerPort" in response:
            listeners.append({
                "type": "tcp",
                "port": response.get("ListenerPort"),
                "protocol": "tcp",
                "backend_port": response.get("BackendServerPort"),
                "bandwidth": response.get("Bandwidth"),
                "status": response.get("Status")
            })

    return listeners


def get_slb_https_listeners(load_balancer_id: str, region: str) -> List[Dict[str, Any]]:
    """
    Get HTTPS listener details including SSL policy.
    """
    response = run_aliyun_command(
        "slb",
        "DescribeLoadBalancerHTTPSListenerAttribute",
        [f"--LoadBalancerId={load_balancer_id}"],
        region
    )

    listeners = []

    if response and "ListenerPort" in response:
        listeners.append({
            "type": "https",
            "port": response.get("ListenerPort"),
            "protocol": "https",
            "backend_port": response.get("BackendServerPort"),
            "bandwidth": response.get("Bandwidth"),
            "status": response.get("Status"),
            "ssl_protocol": response.get("SslProtocols"),
            "tls_version": response.get("TlsCipherPolicy", "unknown"),
            "enable_http2": response.get("EnableHttp2", False)
        })

    return listeners


def scan_slb_instance(slb: Dict[str, Any], region: str) -> List[Dict[str, Any]]:
    """
    Scan a single SLB instance for issues.
    """
    issues = []
    slb_id = slb.get("LoadBalancerId", "unknown")
    slb_name = slb.get("LoadBalancerName", "")
    address_type = slb.get("AddressType", "unknown")

    # Check for internet-facing load balancer
    if address_type == "internet":
        # Check listeners
        http_listeners = get_slb_listeners(slb_id, region)
        https_listeners = get_slb_https_listeners(slb_id, region)

        # Check for HTTP listeners on internet-facing LB
        for listener in http_listeners:
            if listener.get("type") == "http":
                issues.append({
                    "resource_type": "slb",
                    "resource_id": slb_id,
                    "resource_name": slb_name,
                    "region": region,
                    "risk_level": "high",
                    "issue_type": "http_on_internet",
                    "details": {
                        "address_type": address_type,
                        "listener_port": listener.get("port"),
                        "protocol": "HTTP",
                        "address": slb.get("Address", "")
                    },
                    "recommendation": "enable_https_or_restrict_access"
                })

        # Check for weak SSL policies
        for listener in https_listeners:
            tls_policy = listener.get("tls_version", "")
            if tls_policy and "tls_1_0" in tls_policy.lower():
                issues.append({
                    "resource_type": "slb",
                    "resource_id": slb_id,
                    "resource_name": slb_name,
                    "region": region,
                    "risk_level": "medium",
                    "issue_type": "weak_ssl_policy",
                    "details": {
                        "address_type": address_type,
                        "listener_port": listener.get("port"),
                        "tls_version": tls_policy,
                        "ssl_protocol": listener.get("ssl_protocol")
                    },
                    "recommendation": "upgrade_tls_version"
                })

    # Check for load balancers with no backend servers
    backend_servers = slb.get("BackendServers", {}).get("BackendServer", [])
    if not backend_servers:
        issues.append({
            "resource_type": "slb",
            "resource_id": slb_id,
            "resource_name": slb_name,
            "region": region,
            "risk_level": "low",
            "issue_type": "no_backend_servers",
            "details": {
                "address_type": address_type,
                "address": slb.get("Address", ""),
                "status": slb.get("LoadBalancerStatus", "")
            },
            "recommendation": "configure_backend_servers_or_delete"
        })

    return issues


def scan_slb_instances(regions: List[str]) -> List[Dict[str, Any]]:
    """
    Scan SLB instances across multiple regions.
    """
    all_issues = []

    logger.info(f"Starting SLB scan for {len(regions)} region(s)")

    for region in regions:
        logger.info(f"Scanning SLB in region: {region}")

        try:
            instances = get_slb_instances(region)

            if not instances:
                logger.info(f"No SLB instances found in region {region}")
                continue

            logger.info(f"Found {len(instances)} SLB instance(s) in {region}")

            for slb in instances:
                issues = scan_slb_instance(slb, region)
                all_issues.extend(issues)

                if issues:
                    logger.warning(
                        f"Found {len(issues)} issue(s) in SLB {slb.get('LoadBalancerId')}"
                    )

        except Exception as e:
            logger.error(f"Error scanning SLB in region {region}: {e}")
            continue

    logger.info(f"SLB scan complete. Found {len(all_issues)} issue(s) total.")
    return all_issues


def format_slb_report(slb_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format SLB scanning results into report structure.
    """
    return {
        "slb_issues": slb_issues,
        "summary": {
            "total_instances_with_issues": len(set(
                i["resource_id"] for i in slb_issues
            )),
            "http_on_internet_count": sum(
                1 for i in slb_issues
                if i["issue_type"] == "http_on_internet"
            ),
            "weak_ssl_count": sum(
                1 for i in slb_issues
                if i["issue_type"] == "weak_ssl_policy"
            ),
            "no_backend_count": sum(
                1 for i in slb_issues
                if i["issue_type"] == "no_backend_servers"
            )
        }
    }


if __name__ == "__main__":
    import os

    regions_str = os.environ.get('ALIYUN_REGIONS', 'cn-hangzhou')
    regions = [r.strip() for r in regions_str.split(',')]

    print("SLB Scanner - Security Assessment Tool")
    print("=" * 60)
    print()

    issues = scan_slb_instances(regions)

    report = format_slb_report(issues)

    print()
    print("Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
