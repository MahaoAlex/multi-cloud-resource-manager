#!/usr/bin/env python3
"""
ACK (Container Service for Kubernetes) scanner module for Aliyun.
Scans ACK clusters for low utilization: clusters with no nodes or fewer than threshold nodes.
"""

import os
import subprocess
import json
import logging
from typing import List, Dict, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_aliyun_command(
    service: str,
    action: str,
    region: str,
    args: List[str] = None
) -> Dict[str, Any]:
    """
    Execute aliyun CLI command and return parsed JSON response.

    Args:
        service: Aliyun service (cs, etc.)
        action: Action to perform or REST path (GET /clusters, etc.)
        region: Region ID
        args: Additional command arguments

    Returns:
        dict: Parsed JSON response or error info
    """
    cmd = ['aliyun', service, action, f'--region={region}']
    if args:
        cmd.extend(args)

    try:
        env = os.environ.copy()

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
        return {"error": "aliyun CLI not found"}
    except Exception as e:
        return {"error": str(e)}


def get_ack_clusters(region: str) -> List[Dict[str, Any]]:
    """
    List all ACK clusters in a region.

    Args:
        region: Region ID

    Returns:
        list: List of ACK cluster dictionaries
    """
    response = run_aliyun_command('cs', 'GET', region, ['/clusters'])

    if 'error' in response:
        # Fallback: try DescribeClustersV1 OpenAPI style
        response = run_aliyun_command('cs', 'DescribeClustersV1', region)

    if 'error' in response:
        logger.warning(f"Failed to get ACK clusters: {response.get('error')}")
        return []

    clusters = []
    if isinstance(response, list):
        clusters = response
    elif isinstance(response, dict):
        clusters = response.get('clusters', response.get('Clusters', response.get('items', [])))

    # Filter by region if the API returns all clusters
    filtered = []
    for cluster in clusters:
        if isinstance(cluster, dict):
            cluster_region = cluster.get('region_id', cluster.get('RegionId', cluster.get('region', region)))
            if cluster_region == region:
                cluster['region'] = region
                filtered.append(cluster)
            elif 'region_id' not in cluster and 'RegionId' not in cluster:
                # If no region info, assume it belongs to queried region
                cluster['region'] = region
                filtered.append(cluster)

    return filtered


def get_cluster_nodes(cluster_id: str, region: str) -> int:
    """
    Get node count for an ACK cluster.

    Args:
        cluster_id: ACK cluster ID
        region: Region ID

    Returns:
        int: Number of nodes in the cluster
    """
    response = run_aliyun_command('cs', 'GET', region, [f'/clusters/{cluster_id}/nodes'])

    if 'error' in response:
        # Fallback: try DescribeClusterNodes
        response = run_aliyun_command('cs', 'DescribeClusterNodes', region, [f'--ClusterId={cluster_id}'])

    if 'error' in response:
        logger.debug(f"Failed to get nodes for cluster {cluster_id}: {response.get('error')}")
        return 0

    if isinstance(response, list):
        return len(response)
    elif isinstance(response, dict):
        nodes = response.get('nodes', response.get('Nodes', response.get('items', [])))
        return len(nodes) if isinstance(nodes, list) else 0

    return 0


def analyze_ack_cluster(
    cluster: Dict[str, Any],
    region: str,
    node_threshold: int = 2,
    credentials: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Analyze a single ACK cluster for low utilization.

    Args:
        cluster: ACK cluster data
        region: Region ID
        node_threshold: Node count threshold for low usage warning (default: 2)
        credentials: Optional credentials dict (unused, for API compatibility)

    Returns:
        dict: Analysis result with issues found
    """
    cluster_id = cluster.get('cluster_id', cluster.get('ClusterId', cluster.get('id', '')))
    cluster_name = cluster.get('name', cluster.get('Name', 'Unknown'))
    state = cluster.get('state', cluster.get('State', 'unknown'))

    # Get actual node count
    node_count = get_cluster_nodes(cluster_id, region)

    result = {
        "cluster_id": cluster_id,
        "cluster_name": cluster_name,
        "region": region,
        "node_count": node_count,
        "status": state,
        "issues": []
    }

    # Check for empty cluster
    if node_count == 0:
        result["issues"].append({
            "type": "no_nodes",
            "severity": "warning",
            "details": {
                "message": "Cluster has 0 nodes, no pods can run"
            }
        })
    elif node_count < node_threshold:
        result["issues"].append({
            "type": "low_node_count",
            "severity": "info",
            "details": {
                "node_count": node_count,
                "message": f"Cluster has only {node_count} node(s), likely low utilization"
            }
        })

    return result


def scan_ack_clusters(
    regions: List[str],
    node_threshold: int = 2,
    check_empty: bool = True,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan ACK clusters across multiple regions for low utilization.

    Args:
        regions: List of region IDs to scan
        node_threshold: Node count threshold for low usage warning (default: 2)
        check_empty: Whether to flag clusters with no nodes
        credentials: Optional credentials dict (unused, for API compatibility)

    Returns:
        list: List of ACK clusters with utilization issues
    """
    all_issues = []

    for region in regions:
        logger.info(f"Scanning ACK clusters in region: {region}")

        clusters = get_ack_clusters(region)

        if not clusters:
            logger.info(f"No ACK clusters found in {region}")
            continue

        logger.info(f"Found {len(clusters)} ACK cluster(s) in {region}")

        for cluster in clusters:
            if not isinstance(cluster, dict):
                continue

            analysis = analyze_ack_cluster(cluster, region, node_threshold, credentials)

            has_issues = False

            if check_empty and analysis["node_count"] == 0:
                has_issues = True
                if not any(i.get("type") == "no_nodes" for i in analysis["issues"]):
                    analysis["issues"].append({
                        "type": "empty_cluster",
                        "severity": "warning",
                        "details": {
                            "message": "Cluster has no nodes - no workloads running"
                        }
                    })

            if analysis["node_count"] > 0 and analysis["node_count"] < node_threshold:
                has_issues = True

            if has_issues or analysis["issues"]:
                all_issues.append(analysis)

    return all_issues


def format_ack_report(ack_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format ACK monitoring results into report structure.

    Args:
        ack_issues: List of ACK clusters with issues

    Returns:
        dict: Formatted report
    """
    empty_clusters = [c for c in ack_issues if c["node_count"] == 0]
    low_utilization = [c for c in ack_issues if 0 < c["node_count"] < 2]

    return {
        "ack_issues": ack_issues,
        "summary": {
            "total_clusters_with_issues": len(ack_issues),
            "empty_clusters": len(empty_clusters),
            "low_utilization_clusters": len(low_utilization),
            "clusters": [
                {
                    "cluster_id": c["cluster_id"],
                    "cluster_name": c["cluster_name"],
                    "region": c["region"],
                    "node_count": c["node_count"],
                    "status": c["status"]
                }
                for c in ack_issues
            ]
        }
    }


if __name__ == "__main__":
    # Test mode - requires environment variables to be set
    regions_str = os.environ.get('ALIYUN_REGIONS', 'cn-hangzhou')
    regions = [r.strip() for r in regions_str.split(',')]

    print("ACK Scanner - Resource Optimization Tool")
    print("=" * 60)
    print()

    issues = scan_ack_clusters(regions, node_threshold=2)

    report = format_ack_report(issues)

    print()
    print("Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
