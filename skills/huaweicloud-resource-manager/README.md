# Huawei Cloud Resource Manager

A Claude Code Skill for unified Huawei Cloud resource management, providing VPC inventory, security scanning, quota monitoring, and compliance checking across multiple regions.

## Overview

This Skill provides comprehensive resource scanning capabilities for Huawei Cloud infrastructure:

| Capability | Description |
|------------|-------------|
| **VPC Inventory** | Enumerate all VPCs with usage analysis |
| **Security Scanning** | Detect high-risk security group configurations |
| **OBS Scanning** | Identify publicly accessible buckets and objects |
| **ECS Monitoring** | Find low-utilization instances and naming violations |
| **EIP Scanning** | Detect unattached Elastic IPs |
| **Rule Engine** | Configurable YAML-based compliance rules |

## Installation

1. Copy the skills to your Claude Code skills directory:

```bash
# For Claude Code
cp -r skills/huaweicloud-core/* ~/.claude/skills/
cp -r skills/huaweicloud-resource-manager ~/.claude/skills/

# For OpenClaw
cp -r skills/huaweicloud-core/* ~/.openclaw/skills/
cp -r skills/huaweicloud-resource-manager ~/.openclaw/skills/
```

2. Ensure hcloud CLI is installed and accessible in PATH.

## Quick Start

### Interactive Mode

Start a conversation with Claude:

```
User: Please scan my Huawei Cloud resources

Claude: I'll help you scan your Huawei Cloud resources. Let's start by configuring the connection.

Step 1: Authentication
Please provide your Huawei Cloud Access Key ID: [input]
Please provide your Secret Access Key: [masked input]
Please specify the regions to scan (comma-separated or 'all'): cn-north-4,cn-south-1

Step 2: Proxy Configuration (Optional)
Do you need to configure proxy? (yes/no): no

[Scan executes with progress updates...]

Report generated: ./reports/2026-04-08/manual_14-30-00.md
```

### Command Mode

```bash
# Full scan with all defaults
/huaweicloud-scan

# Scan specific regions
/huaweicloud-scan --regions=cn-north-4,cn-south-1

# Scan all available regions
/huaweicloud-scan --regions=all

# Scheduled scan (JSON only)
/huaweicloud-scan --mode=scheduled

# Scan specific resource type
/huaweicloud-scan --scan=vpc
/huaweicloud-scan --scan=security
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `HWCLOUD_ACCESS_KEY` | Huawei Cloud Access Key ID | Yes |
| `HWCLOUD_SECRET_KEY` | Huawei Cloud Secret Access Key | Yes |
| `HWCLOUD_REGIONS` | Comma-separated region IDs or 'all' | Yes |
| `HTTP_PROXY` | HTTP proxy URL | Optional |
| `HTTPS_PROXY` | HTTPS proxy URL | Optional |
| `NO_PROXY` | Comma-separated no-proxy hosts | Optional |

### Supported Regions

- `cn-north-4` - Beijing
- `cn-south-1` - Guangzhou
- `cn-east-2` - Shanghai
- `cn-east-3` - Shanghai (new)
- `cn-southwest-2` - Guiyang
- `ap-southeast-1` - Hong Kong
- `ap-southeast-2` - Bangkok
- `ap-southeast-3` - Singapore
- `eu-west-101` - Amsterdam
- `af-south-1` - Johannesburg

Use `all` to scan all available regions.

## Report Output

### Directory Structure

```
reports/
└── 2026-04-08/
    ├── scheduled_09-00-00.json     # Scheduled scan (JSON only)
    ├── scheduled_10-00-00.json
    ├── manual_14-30-00.json        # Manual scan
    └── manual_14-30-00.md          # Manual scan (human-readable)
```

### JSON Report Format

```json
{
  "scan_metadata": {
    "timestamp": "2026-04-08T14:30:00Z",
    "scan_type": "manual",
    "regions": ["cn-north-4", "cn-south-1"],
    "duration_seconds": 120
  },
  "summary": {
    "total": {
      "vpcs": 10,
      "unused_vpcs": 2,
      "security_issues": 5
    },
    "by_region": {
      "cn-north-4": { "vpcs": 6, "security_issues": 3 },
      "cn-south-1": { "vpcs": 4, "security_issues": 2 }
    }
  },
  "details": {
    "vpc_analysis": [...],
    "security_issues": [...],
    "ecs_issues": [...]
  },
  "action_items": [
    {
      "resource_type": "vpc",
      "resource_id": "vpc-xxx",
      "region": "cn-north-4",
      "severity": "warning",
      "issue": "VPC appears to be unused",
      "recommendation": "contact_owner_for_deletion"
    }
  ]
}
```

## Rule Engine

### Built-in Rules

Rules are stored in `rules/` directory:

- `naming-conventions.yaml` - Resource naming compliance
- `security-rules.yaml` - Security risk detection

### Custom Rules

Create custom rules in `./rules/` directory (user rules take precedence):

```yaml
# ./rules/custom-rules.yaml
rules:
  - id: "my-custom-rule"
    name: "My Custom Check"
    resource: "ecs"
    condition: "name !~ /-prod$/"
    severity: "warning"
    description: "Production ECS must have -prod suffix"
```

### Supported Conditions

- `name =~ /pattern/` - Name matches regex
- `name !~ /pattern/` - Name does not match regex
- `ports contains [22,33]` - Ports list contains values
- `status = value` - Exact match
- `cpu_avg_24h < 10` - Numeric comparison

## Scheduling

### Cron (Hourly)

```bash
0 * * * * cd /path/to/project && claude "/huaweicloud-scan --mode=scheduled --regions=all"
```

### Airflow DAG

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

dag = DAG(
    'huaweicloud_scan',
    start_date=datetime(2026, 4, 8),
    schedule_interval='0 * * * *'
)

scan_task = BashOperator(
    task_id='huaweicloud_scan',
    bash_command='claude "/huaweicloud-scan --mode=scheduled --regions=all"',
    dag=dag
)
```

## Tools Reference

### proxy-injection

Configure proxy settings for current session:

```
/proxy-injection configure_proxy
  --http_proxy=http://proxy.company.com:8080
  --https_proxy=http://proxy.company.com:8080
  --no_proxy="localhost,127.0.0.1"
```

### auth-manager

Configure authentication:

```
/auth-manager configure_auth
  --access_key_id=YOUR_AK
  --secret_access_key=YOUR_SK
  --regions=cn-north-4,cn-south-1
```

### huaweicloud-resource-manager

Full resource scan:

```
/huaweicloud-resource-manager full_scan
  --regions=["cn-north-4"]
  --output_dir="./reports"
  --scan_type="manual"
```

## Security Notes

- All credentials are stored in environment variables only
- No persistent storage of sensitive information
- All scan operations are read-only
- Delete operations require explicit human confirmation
- Reports contain resource metadata, not sensitive data

## License

MIT License
