#!/usr/bin/env python3
"""
RDS Scanner for Aliyun Resource Manager

Scans RDS instances for security and configuration issues:
- Public network access enabled
- SSL not enabled
- Backup policy issues
- Encryption not enabled
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


def get_rds_instances(region: str) -> List[Dict[str, Any]]:
    """
    Get all RDS instances in a region.
    """
    response = run_aliyun_command("rds", "DescribeDBInstances", ["--PageSize=100"], region)

    if not response:
        return []

    instances = response.get("Items", {}).get("DBInstance", [])
    return instances if isinstance(instances, list) else [instances]


def get_rds_instance_detail(instance_id: str, region: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about an RDS instance.
    """
    response = run_aliyun_command(
        "rds",
        "DescribeDBInstanceAttribute",
        [f"--DBInstanceId={instance_id}"],
        region
    )

    if not response:
        return None

    items = response.get("Items", {}).get("DBInstanceAttribute", [])
    return items[0] if isinstance(items, list) and items else items


def scan_rds_instance(instance: Dict[str, Any], region: str) -> List[Dict[str, Any]]:
    """
    Scan a single RDS instance for issues.
    """
    issues = []
    instance_id = instance.get("DBInstanceId", "unknown")
    instance_name = instance.get("DBInstanceDescription", "")

    # Check for public network access
    if instance.get("DBInstanceNetType") == "Internet":
        issues.append({
            "resource_type": "rds",
            "resource_id": instance_id,
            "resource_name": instance_name,
            "region": region,
            "risk_level": "high",
            "issue_type": "public_network_access",
            "details": {
                "net_type": instance.get("DBInstanceNetType"),
                "connection_string": instance.get("ConnectionString", "")
            },
            "recommendation": "disable_public_network_access"
        })

    # Check SSL status
    if instance.get("SSLMode") == "Disabled":
        issues.append({
            "resource_type": "rds",
            "resource_id": instance_id,
            "resource_name": instance_name,
            "region": region,
            "risk_level": "medium",
            "issue_type": "ssl_disabled",
            "details": {
                "ssl_mode": instance.get("SSLMode"),
                "engine": instance.get("Engine", ""),
                "engine_version": instance.get("EngineVersion", "")
            },
            "recommendation": "enable_ssl"
        })

    # Check TDE (Transparent Data Encryption) status
    if instance.get("TDEStatus") == "Disabled":
        issues.append({
            "resource_type": "rds",
            "resource_id": instance_id,
            "resource_name": instance_name,
            "region": region,
            "risk_level": "medium",
            "issue_type": "encryption_disabled",
            "details": {
                "tde_status": instance.get("TDEStatus"),
                "engine": instance.get("Engine", "")
            },
            "recommendation": "enable_tde_encryption"
        })

    # Check if auto-backup is enabled
    if instance.get("BackupMode") != "Automated":
        issues.append({
            "resource_type": "rds",
            "resource_id": instance_id,
            "resource_name": instance_name,
            "region": region,
            "risk_level": "medium",
            "issue_type": "backup_not_automated",
            "details": {
                "backup_mode": instance.get("BackupMode", "Unknown"),
                "retention_period": instance.get("BackupRetentionPeriod", 0)
            },
            "recommendation": "enable_automated_backup"
        })

    return issues


def scan_rds_instances(regions: List[str]) -> List[Dict[str, Any]]:
    """
    Scan RDS instances across multiple regions.
    """
    all_issues = []

    logger.info(f"Starting RDS scan for {len(regions)} region(s)")

    for region in regions:
        logger.info(f"Scanning RDS in region: {region}")

        try:
            instances = get_rds_instances(region)

            if not instances:
                logger.info(f"No RDS instances found in region {region}")
                continue

            logger.info(f"Found {len(instances)} RDS instance(s) in {region}")

            for instance in instances:
                instance_id = instance.get("DBInstanceId")

                # Get detailed instance info
                detail = get_rds_instance_detail(instance_id, region)
                if detail:
                    instance.update(detail)

                issues = scan_rds_instance(instance, region)
                all_issues.extend(issues)

                if issues:
                    logger.warning(
                        f"Found {len(issues)} issue(s) in RDS instance {instance_id}"
                    )

        except Exception as e:
            logger.error(f"Error scanning RDS in region {region}: {e}")
            continue

    logger.info(f"RDS scan complete. Found {len(all_issues)} issue(s) total.")
    return all_issues


def format_rds_report(rds_issues: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Format RDS scanning results into report structure.
    """
    return {
        "rds_issues": rds_issues,
        "summary": {
            "total_instances_with_issues": len(set(
                i["resource_id"] for i in rds_issues
            )),
            "public_access_count": sum(
                1 for i in rds_issues
                if i["issue_type"] == "public_network_access"
            ),
            "ssl_disabled_count": sum(
                1 for i in rds_issues
                if i["issue_type"] == "ssl_disabled"
            ),
            "encryption_disabled_count": sum(
                1 for i in rds_issues
                if i["issue_type"] == "encryption_disabled"
            ),
            "backup_issues_count": sum(
                1 for i in rds_issues
                if i["issue_type"] == "backup_not_automated"
            )
        }
    }


if __name__ == "__main__":
    import os

    regions_str = os.environ.get('ALIYUN_REGIONS', 'cn-hangzhou')
    regions = [r.strip() for r in regions_str.split(',')]

    print("RDS Scanner - Security Assessment Tool")
    print("=" * 60)
    print()

    issues = scan_rds_instances(regions)

    report = format_rds_report(issues)

    print()
    print("Results:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
