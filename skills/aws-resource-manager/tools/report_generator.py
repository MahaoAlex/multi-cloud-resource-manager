#!/usr/bin/env python3
"""
Report Generator for AWS Resource Manager

Generates multi-format reports (JSON, Markdown) from scan results.
Supports multi-region aggregation and action item generation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default retention days
DEFAULT_RETENTION_DAYS = 7


class ReportGenerator:
    """Generates reports in multiple formats."""

    def __init__(self, output_dir: str = "./reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        scan_results: Dict[str, Any],
        scan_type: str = "manual",
        timestamp: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate reports in multiple formats.

        Args:
            scan_results: Combined scan results from all tools
            scan_type: 'scheduled' or 'manual'
            timestamp: Optional timestamp string

        Returns:
            Dictionary with file paths for each format
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

        # Parse timestamp for filename
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H-%M-%S")

        # Create date subdirectory
        report_dir = self.output_dir / date_str
        report_dir.mkdir(parents=True, exist_ok=True)

        # Clean old reports
        self._clean_old_reports()

        # Generate filenames
        prefix = f"{scan_type}_{time_str}"
        files = {}

        # Always generate JSON
        json_file = report_dir / f"{prefix}.json"
        self._generate_json(scan_results, json_file, scan_type, timestamp)
        files['json'] = str(json_file)
        logger.info(f"Generated JSON report: {json_file}")

        # Generate Markdown only for manual scans
        if scan_type == "manual":
            md_file = report_dir / f"{prefix}.md"
            self._generate_markdown(scan_results, md_file, scan_type, timestamp)
            files['markdown'] = str(md_file)
            logger.info(f"Generated Markdown report: {md_file}")

        return files

    def _generate_json(
        self,
        data: Dict[str, Any],
        filepath: Path,
        scan_type: str,
        timestamp: str
    ) -> None:
        """Generate JSON report."""
        report = {
            "scan_metadata": {
                "timestamp": timestamp,
                "scan_type": scan_type,
                "regions": data.get("regions", []),
                "duration_seconds": data.get("duration_seconds", 0),
                "total_resources": data.get("total_resources", {})
            },
            "summary": {
                "total": data.get("summary", {}),
                "by_region": data.get("summary_by_region", {})
            },
            "details": {
                "vpc_analysis": data.get("vpc_analysis", []),
                "security_issues": data.get("security_issues", []),
                "s3_issues": data.get("s3_issues", []),
                "ec2_issues": data.get("ec2_issues", []),
                "unattached_eips": data.get("unattached_eips", []),
                "naming_violations": data.get("naming_violations", [])
            },
            "action_items": self._generate_action_items(data)
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

    def _generate_markdown(
        self,
        data: Dict[str, Any],
        filepath: Path,
        scan_type: str,
        timestamp: str
    ) -> None:
        """Generate Markdown report."""
        lines = []

        # Header
        lines.append("# AWS Resource Scan Report")
        lines.append("")
        lines.append(f"**Scan Type:** {scan_type.capitalize()}")
        lines.append(f"**Timestamp:** {timestamp}")
        lines.append(f"**Regions:** {', '.join(data.get('regions', []))}")
        lines.append(f"**Duration:** {data.get('duration_seconds', 0)} seconds")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        summary = data.get("summary", {})
        lines.append(f"- **Total VPCs:** {summary.get('vpcs', 0)}")
        lines.append(f"- **Unused VPCs:** {summary.get('unused_vpcs', 0)}")
        lines.append(f"- **Security Issues:** {summary.get('security_issues', 0)}")
        lines.append(f"- **Public S3 Buckets:** {summary.get('public_s3_buckets', 0)}")
        lines.append(f"- **Low Utilization EC2:** {summary.get('low_utilization_ec2', 0)}")
        lines.append(f"- **Unattached EIPs:** {summary.get('unattached_eips', 0)}")
        lines.append(f"- **Naming Violations:** {summary.get('naming_violations', 0)}")
        lines.append("")

        # Region Summary
        lines.append("## Summary by Region")
        lines.append("")
        for region, region_summary in data.get("summary_by_region", {}).items():
            lines.append(f"### {region}")
            lines.append(f"- VPCs: {region_summary.get('vpcs', 0)}")
            lines.append(f"- Security Issues: {region_summary.get('security_issues', 0)}")
            lines.append(f"- EC2 Issues: {region_summary.get('ec2_issues', 0)}")
            lines.append("")

        # Action Items (High Priority)
        action_items = self._generate_action_items(data)
        if action_items:
            lines.append("## Action Items (Require Attention)")
            lines.append("")

            # Critical/High items
            critical_items = [i for i in action_items if i.get('severity') in ['critical', 'high']]
            if critical_items:
                lines.append("### Critical/High Priority")
                lines.append("")
                for item in critical_items:
                    lines.append(f"- **[{item['severity'].upper()}]** {item['resource_type']} `{item['resource_id']}`")
                    lines.append(f"  - Region: {item.get('region', 'unknown')}")
                    lines.append(f"  - Issue: {item['issue']}")
                    lines.append(f"  - Recommendation: {item['recommendation']}")
                    lines.append("")

            # Unused VPCs
            unused_vpcs = [v for v in data.get("vpc_analysis", []) if v.get("status") == "unused"]
            if unused_vpcs:
                lines.append("### Unused VPCs (Contact Owner for Deletion)")
                lines.append("")
                lines.append("| VPC ID | VPC Name | Region | Created By |")
                lines.append("|--------|----------|--------|------------|")
                for vpc in unused_vpcs:
                    lines.append(f"| {vpc.get('vpc_id', 'N/A')} | {vpc.get('vpc_name', 'N/A')} | "
                               f"{vpc.get('region', 'N/A')} | {vpc.get('created_by', 'unknown')} |")
                lines.append("")

            # Security Issues
            sec_issues = data.get("security_issues", [])
            if sec_issues:
                lines.append("### Security Issues")
                lines.append("")
                lines.append("| Resource | Region | Issue | Severity |")
                lines.append("|----------|--------|-------|----------|")
                for issue in sec_issues[:20]:  # Limit to 20
                    lines.append(f"| {issue.get('security_group_id', 'N/A')} | "
                               f"{issue.get('region', 'N/A')} | "
                               f"{issue.get('issue_type', 'N/A')} | "
                               f"{issue.get('risk_level', 'N/A')} |")
                lines.append("")

            # Low Utilization EC2
            low_cpu = [e for e in data.get("ec2_issues", []) if e.get('issues') and
                      any(i.get('type') == 'low_cpu_usage' for i in e['issues'])]
            if low_cpu:
                lines.append("### Low CPU Utilization EC2")
                lines.append("")
                lines.append("| Instance ID | Name | Region | Avg CPU |")
                lines.append("|-------------|------|--------|---------|")
                for ec2 in low_cpu[:20]:
                    cpu_info = next((i for i in ec2.get('issues', []) if i.get('type') == 'low_cpu_usage'), {})
                    lines.append(f"| {ec2.get('instance_id', 'N/A')} | "
                               f"{ec2.get('instance_name', 'N/A')} | "
                               f"{ec2.get('region', 'N/A')} | "
                               f"{cpu_info.get('details', {}).get('avg_cpu_24h', 'N/A')} |")
                lines.append("")

            # Naming Violations
            naming = [e for e in data.get("ec2_issues", []) if e.get('issues') and
                     any(i.get('type') == 'naming_violation' for i in e['issues'])]
            if naming:
                lines.append("### Naming Convention Violations")
                lines.append("")
                lines.append("| Instance ID | Current Name | Region | Expected Pattern |")
                lines.append("|-------------|--------------|--------|------------------|")
                for ec2 in naming[:20]:
                    lines.append(f"| {ec2.get('instance_id', 'N/A')} | "
                               f"{ec2.get('instance_name', 'N/A')} | "
                               f"{ec2.get('region', 'N/A')} | 6+ consecutive digits |")
                lines.append("")

            # Unattached EIPs
            eips = data.get("unattached_eips", [])
            if eips:
                lines.append("### Unattached Elastic IPs")
                lines.append("")
                lines.append("| EIP ID | IP Address | Region | Domain |")
                lines.append("|--------|------------|--------|--------|")
                for eip in eips:
                    lines.append(f"| {eip.get('eip_id', 'N/A')} | "
                               f"{eip.get('eip_address', 'N/A')} | "
                               f"{eip.get('region', 'N/A')} | "
                               f"{eip.get('domain', 'N/A')} |")
                lines.append("")

            # Public S3
            s3 = data.get("s3_issues", [])
            if s3:
                lines.append("### Public S3 Buckets")
                lines.append("")
                for issue in s3:
                    lines.append(f"- **{issue.get('bucket_name', 'N/A')}** ({issue.get('region', 'N/A')})")
                    lines.append(f"  - Permission: {issue.get('permission', 'unknown')}")
                    lines.append(f"  - Risk Level: {issue.get('risk_level', 'unknown')}")
                    lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by AWS Resource Manager*")
        lines.append(f"*Report saved to: {filepath}*")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

    def _generate_action_items(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate action items from scan results."""
        action_items = []

        # Unused VPCs
        for vpc in data.get("vpc_analysis", []):
            if vpc.get("status") == "unused":
                action_items.append({
                    "resource_type": "vpc",
                    "resource_id": vpc.get("vpc_id"),
                    "region": vpc.get("region"),
                    "severity": "warning",
                    "issue": "VPC appears to be unused (no active resources)",
                    "recommendation": "contact_owner_for_deletion",
                    "owner": vpc.get("created_by", "unknown")
                })

        # Security issues
        for issue in data.get("security_issues", []):
            action_items.append({
                "resource_type": "security_group",
                "resource_id": issue.get("security_group_id"),
                "region": issue.get("region"),
                "severity": issue.get("risk_level", "high"),
                "issue": f"{issue.get('issue_type')}: {issue.get('details', {})}",
                "recommendation": issue.get("recommendation", "review_configuration"),
                "owner": "unknown"
            })

        # EC2 issues
        for ec2 in data.get("ec2_issues", []):
            for issue in ec2.get("issues", []):
                if issue.get("type") == "low_cpu_usage":
                    action_items.append({
                        "resource_type": "ec2",
                        "resource_id": ec2.get("instance_id"),
                        "region": ec2.get("region"),
                        "severity": "info",
                        "issue": f"Low CPU utilization: {issue.get('details', {}).get('avg_cpu_24h')}",
                        "recommendation": "optimize_or_release",
                        "owner": ec2.get("created_by", "unknown")
                    })
                elif issue.get("type") == "naming_violation":
                    action_items.append({
                        "resource_type": "ec2",
                        "resource_id": ec2.get("instance_id"),
                        "region": ec2.get("region"),
                        "severity": "warning",
                        "issue": "Naming convention violation (missing employee ID)",
                        "recommendation": "rename_with_employee_id",
                        "owner": ec2.get("created_by", "unknown")
                    })

        # Unattached EIPs
        for eip in data.get("unattached_eips", []):
            action_items.append({
                "resource_type": "eip",
                "resource_id": eip.get("eip_id"),
                "region": eip.get("region"),
                "severity": "info",
                "issue": "EIP is not attached to any resource",
                "recommendation": "release_if_not_needed",
                "owner": eip.get("created_by", "unknown")
            })

        # Public S3
        for s3 in data.get("s3_issues", []):
            action_items.append({
                "resource_type": "s3_bucket",
                "resource_id": s3.get("bucket_name"),
                "region": s3.get("region"),
                "severity": s3.get("risk_level", "high"),
                "issue": f"Public access: {s3.get('permission')}",
                "recommendation": "enable_public_access_block",
                "owner": "unknown"
            })

        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "warning": 2, "info": 3}
        action_items.sort(key=lambda x: severity_order.get(x.get("severity", "info"), 4))

        return action_items

    def _clean_old_reports(self, retention_days: int = DEFAULT_RETENTION_DAYS) -> None:
        """Clean reports older than retention_days."""
        try:
            cutoff = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)

            for date_dir in self.output_dir.iterdir():
                if not date_dir.is_dir():
                    continue

                # Check if directory is older than retention period
                dir_mtime = date_dir.stat().st_mtime
                if dir_mtime < cutoff:
                    import shutil
                    shutil.rmtree(date_dir)
                    logger.info(f"Cleaned old report directory: {date_dir}")

        except Exception as e:
            logger.error(f"Error cleaning old reports: {e}")


def main():
    """Main entry point for testing."""
    # Create test data
    test_data = {
        "regions": ["us-east-1", "us-west-2"],
        "duration_seconds": 120,
        "summary": {
            "vpcs": 10,
            "unused_vpcs": 2,
            "security_issues": 3,
            "public_s3_buckets": 1,
            "low_utilization_ec2": 2,
            "unattached_eips": 1,
            "naming_violations": 3
        },
        "summary_by_region": {
            "us-east-1": {"vpcs": 6, "security_issues": 2, "ec2_issues": 2},
            "us-west-2": {"vpcs": 4, "security_issues": 1, "ec2_issues": 1}
        },
        "vpc_analysis": [
            {
                "vpc_id": "vpc-001",
                "vpc_name": "test-vpc",
                "region": "us-east-1",
                "status": "unused",
                "created_by": "zhangsan"
            }
        ],
        "security_issues": [
            {
                "security_group_id": "sg-001",
                "region": "us-east-1",
                "risk_level": "critical",
                "issue_type": "open_ports",
                "details": {"ports": [22], "remote_ip": "0.0.0.0/0"},
                "recommendation": "restrict_source_ip_range"
            }
        ],
        "s3_issues": [
            {
                "bucket_name": "public-bucket",
                "region": "us-east-1",
                "risk_level": "high",
                "permission": "public-read"
            }
        ],
        "ec2_issues": [
            {
                "instance_id": "i-001",
                "instance_name": "web-server",
                "region": "us-east-1",
                "issues": [
                    {"type": "low_cpu_usage", "details": {"avg_cpu_24h": "5.2%"}}
                ],
                "created_by": "lisi"
            }
        ],
        "unattached_eips": [
            {
                "eip_id": "eipalloc-001",
                "eip_address": "123.45.67.89",
                "region": "us-east-1",
                "domain": "vpc"
            }
        ]
    }

    generator = ReportGenerator()

    # Generate manual report
    print("Generating manual report...")
    files = generator.generate_report(test_data, scan_type="manual")
    print(f"Generated: {files}")

    # Generate scheduled report
    print("\nGenerating scheduled report...")
    files = generator.generate_report(test_data, scan_type="scheduled")
    print(f"Generated: {files}")


if __name__ == "__main__":
    main()
