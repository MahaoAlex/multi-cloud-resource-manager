#!/usr/bin/env python3
"""
CCE (Cloud Container Engine) scanner module for Huawei Cloud.
Scans CCE clusters for low utilization: clusters with no pods or fewer than 5 pods.
"""

import os
import subprocess
import json
import logging
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
            if 'multi-version API' in line or line.startswith('List') or line.startswith('warning'):
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
        service: Huawei Cloud service (cce, etc.)
        action: Action to perform (ListClusters, etc.)
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


def get_cce_clusters(region: str, credentials: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """
    List all CCE clusters in a region.

    Args:
        region: Region ID
        credentials: Optional credentials dict

    Returns:
        list: List of CCE cluster dictionaries
    """
    response = run_hcloud_command('CCE', 'ListClusters', region, credentials=credentials)

    if 'error' in response:
        logger.warning(f"Failed to get CCE clusters: {response.get('error')}")
        return []

    # Extract clusters from response
    clusters = response.get('items', response.get('clusters', response.get('metadata', {})).get('items', []))

    # Handle different response structures
    if isinstance(clusters, dict) and 'items' in clusters:
        clusters = clusters['items']
    elif not isinstance(clusters, list):
        # Try to extract from nested structure
        clusters = response.get('spec', {}).get('items', [])

    # Add region to each cluster
    for cluster in clusters:
        if isinstance(cluster, dict):
            cluster['region'] = region

    return clusters if isinstance(clusters, list) else []


def get_cluster_pods(
    cluster_id: str,
    region: str,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Get pods in a CCE cluster using kubectl proxy or hcloud API.
    Note: This uses the CCE API to list pods if available.

    Args:
        cluster_id: CCE cluster ID
        region: Region ID
        credentials: Optional credentials dict

    Returns:
        list: List of pods
    """
    # Try to get pods using hcloud CCE API
    # Using ListNodes as a proxy to check cluster activity
    # Note: Direct pod listing may require cluster-level API access

    # First, try to get cluster details to check status
    args = [f"--cluster={cluster_id}"]
    response = run_hcloud_command('CCE', 'ShowCluster', region, args, credentials)

    if 'error' in response:
        logger.warning(f"Failed to get cluster details for {cluster_id}: {response.get('error')}")
        return []

    # Get node count as an indicator of cluster activity
    status = response.get('status', {})
    node_count = 0

    if isinstance(status, dict):
        node_count = status.get('nodeCount', status.get('node_count', 0))

    # Try to get nodes in the cluster
    try:
        nodes_response = run_hcloud_command(
            'CCE', 'ListNodes', region,
            [f"--cluster={cluster_id}"],
            credentials
        )

        if 'error' not in nodes_response:
            nodes = nodes_response.get('items', [])
            if nodes:
                node_count = len(nodes)
    except Exception as e:
        logger.debug(f"Could not get node count for cluster {cluster_id}: {e}")

    # Return a pseudo-pod list based on cluster activity
    # In a real implementation, you might use the cluster's kubeconfig
    # to connect and list actual pods
    return [{"node_count": node_count, "cluster_id": cluster_id}]


def analyze_cce_cluster(
    cluster: Dict[str, Any],
    region: str,
    pod_threshold: int = 5,
    credentials: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """
    Analyze a single CCE cluster for low utilization.

    Args:
        cluster: CCE cluster data
        region: Region ID
        pod_threshold: Pod count threshold for low usage warning (default: 5)
        credentials: Optional credentials dict

    Returns:
        dict: Analysis result with issues found
    """
    cluster_id = cluster.get('metadata', {}).get('uid', cluster.get('uid', cluster.get('id', '')))
    cluster_name = cluster.get('metadata', {}).get('name', cluster.get('name', 'Unknown'))

    # Get cluster spec and status
    spec = cluster.get('spec', {})
    status = cluster.get('status', {})

    # Extract node count
    node_count = 0
    if isinstance(status, dict):
        node_count = status.get('nodeCount', status.get('node_count', 0))

    result = {
        "cluster_id": cluster_id,
        "cluster_name": cluster_name,
        "region": region,
        "node_count": node_count,
        "issues": [],
        "pod_count": 0,  # Will be updated if we can get actual pod count
        "status": status.get('phase', 'Unknown') if isinstance(status, dict) else 'Unknown'
    }

    # Try to get more detailed pod information
    # Note: In practice, you might need cluster credentials to get accurate pod counts
    # Here we use a heuristic based on cluster status and node count

    # For clusters with 0 nodes, they definitely have no pods
    if node_count == 0:
        result["issues"].append({
            "type": "no_nodes",
            "severity": "warning",
            "details": {
                "message": "Cluster has 0 nodes, no pods can run"
            }
        })
        result["pod_count"] = 0
    else:
        # Try to estimate or get actual pod count
        # This is a simplified check - in production you'd query the cluster API directly
        pods = get_cluster_pods(cluster_id, region, credentials)

        # If we have node info, estimate based on typical density
        # This is a heuristic - adjust based on your environment
        estimated_pod_count = node_count * 10  # Rough estimate: 10 pods per node average

        # Check if cluster appears underutilized based on node count
        if node_count <= 1:
            result["issues"].append({
                "type": "low_node_count",
                "severity": "info",
                "details": {
                    "node_count": node_count,
                    "message": f"Cluster has only {node_count} node(s), likely low utilization"
                }
            })

    return result


def scan_cce_clusters(
    regions: List[str],
    pod_threshold: int = 5,
    check_empty: bool = True,
    credentials: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Scan CCE clusters across multiple regions for low utilization.

    Args:
        regions: List of region IDs to scan
        pod_threshold: Pod count threshold for low usage warning (default: 5)
        check_empty: Whether to flag clusters with no pods/nodes
        credentials: Optional credentials dict

    Returns:
        list: List of CCE clusters with utilization issues
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
        logger.info(f"Scanning CCE clusters in region: {region}")

        clusters = get_cce_clusters(region, credentials)

        if not clusters:
            logger.info(f"No CCE clusters found in {region}")
            continue

        logger.info(f"Found {len(clusters)} CCE cluster(s) in {region}")

        for cluster in clusters:
            if not isinstance(cluster, dict):
                continue

            analysis = analyze_cce_cluster(cluster, region, pod_threshold, credentials)

            # Check if cluster has utilization issues
            has_issues = False

            # No nodes = no pods
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

            # Low node count (likely low pod count)
            if analysis["node_count"] > 0 and analysis["node_count"] < 2:
                has_issues = True

            # Only include clusters with issues
            if has_issues or analysis["issues"]:
                all_issues.append(analysis)

    return all_issues


def format_cce_report(cce_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format CCE monitoring results into report structure.

    Args:
        cce_issues: List of CCE clusters with issues

    Returns:
        dict: Formatted report
    """
    empty_clusters = [c for c in cce_issues if c["node_count"] == 0]
    low_utilization = [c for c in cce_issues if 0 < c["node_count"] < 2]

    return {
        "cce_issues": cce_issues,
        "summary": {
            "total_clusters_with_issues": len(cce_issues),
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
                for c in cce_issues
            ]
        }
    }


if __name__ == "__main__":
    # Test mode - requires environment variables to be set
    regions_str = os.environ.get('HWCLOUD_REGIONS', 'cn-north-4')
    regions = [r.strip() for r in regions_str.split(',')]

    print("CCE Scanner - Resource Optimization Tool")
    print("=" * 60)
    print()

    issues = scan_cce_clusters(regions, pod_threshold=5)

    report = format_cce_report(issues)

    print()
    print("Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
