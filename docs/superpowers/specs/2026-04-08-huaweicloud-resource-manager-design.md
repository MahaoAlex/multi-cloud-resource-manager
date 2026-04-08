# HuaweiCloud Resource Manager Skills Design

## Overview

A Claude Code Skills suite for managing Huawei Cloud resources with focus on resource inventory, security scanning, and compliance checking. Designed for internal team use with extensible rule engine.

## Architecture

### Skill Structure

```
skills/
├── huaweicloud-core/              # Infrastructure Skills (reusable)
│   ├── proxy-injection/           # Proxy configuration tool
│   └── auth-manager/              # Authentication management tool
└── huaweicloud-resource-manager/  # Main business logic Skill
    ├── tools/
    │   ├── vpc_inventory.py       # VPC resource enumeration
    │   ├── vpc_analyzer.py        # VPC usage analysis
    │   ├── security_scanner.py    # Security group scanning
    │   ├── obs_scanner.py         # OBS public access detection
    │   ├── ecs_monitor.py         # ECS low utilization detection
    │   └── report_generator.py    # Multi-format report generation
    └── rules/                     # Built-in YAML rules
        ├── naming-conventions.yaml
        └── security-rules.yaml
```

## Core Components

### 1. huaweicloud-core (Infrastructure)

#### proxy-injection Tool

Purpose: Interactive proxy configuration for hcloud CLI

**Input:**
- http_proxy (optional)
- https_proxy (optional)
- no_proxy (optional)

**Output:**
- Environment variables exported to current session
- No persistent storage

**Constraints:**
- Must support interactive input
- Only valid for current session
- Sensitive data must not be logged

#### auth-manager Tool

Purpose: Huawei Cloud authentication setup

**Input:**
- Access Key ID
- Secret Access Key
- Regions (comma-separated, default: cn-north-4)
- Project ID (optional)

**Output:**
- Environment variables: `HWCLOUD_ACCESS_KEY`, `HWCLOUD_SECRET_KEY`, `HWCLOUD_REGIONS`
- Validates connection with `hcloud vpc ListVpcs` for each region

**Multi-Region Support:**
- Supports scanning multiple regions in one execution
- Regions specified as comma-separated list: `cn-north-4,cn-south-1,cn-east-2`
- Each region validated before scanning

**Constraints:**
- Interactive password input (masked)
- Command output must mask sensitive fields
- Validates credentials before completing

### 2. huaweicloud-resource-manager (Business Logic)

#### vpc_inventory Tool

Purpose: Enumerate all VPC resources

**Command:** `hcloud vpc ListVpcs`

**Output Structure:**
```json
{
  "vpcs": [
    {
      "id": "vpc-xxx",
      "name": "production-vpc",
      "cidr": "192.168.0.0/16",
      "region": "cn-north-4",
      "status": "ACTIVE",
      "created_at": "2024-01-15T08:30:00Z"
    }
  ],
  "regions_scanned": ["cn-north-4", "cn-south-1"],
  "total_count": 5
}
```

**Constraints:**
- Read-only operation
- Must handle pagination if applicable

#### vpc_analyzer Tool

Purpose: Analyze VPC usage status

**Analysis Logic:**
1. List all Subnets in VPC (`hcloud vpc ListSubnets`)
2. For each Subnet:
   - Check ECS instances (`hcloud ecs ListServers` with subnet filter)
   - Check NICs and IP usage (`hcloud vpc ListPorts`)
3. Determine status:
   - "in_use": Has ECS or non-default IPs in use
   - "unused": No resources found
   - "pending": Cannot determine (document limitation)

**Output Structure:**
```json
{
  "vpc_analysis": [
    {
      "vpc_id": "vpc-xxx",
      "vpc_name": "test-vpc",
      "status": "unused",
      "subnets": [
        {
          "subnet_id": "subnet-xxx",
          "has_ecs": false,
          "has_active_ips": false
        }
      ],
      "created_by": "zhangsan",
      "recommendation": "contact_owner_for_deletion"
    }
  ]
}
```

#### security_scanner Tool

Purpose: Scan security groups for high-risk configurations

**Checks:**
- Ports 22, 33, 44 open to 0.0.0.0/0
- Overly permissive outbound rules

**Command:** `hcloud vpc ListSecurityGroups`, `hcloud vpc ListSecurityGroupRules`

**Output Structure:**
```json
{
  "security_issues": [
    {
      "security_group_id": "sg-xxx",
      "security_group_name": "default",
      "vpc_id": "vpc-xxx",
      "risk_level": "critical",
      "issue_type": "open_ports",
      "details": {
        "ports": [22, 33, 44],
        "protocol": "tcp",
        "remote_ip": "0.0.0.0/0"
      },
      "recommendation": "restrict_source_ip_range"
    }
  ]
}
```

#### obs_scanner Tool

Purpose: Detect publicly accessible OBS buckets and objects

**Checks:**
- Bucket ACL with public-read or public-read-write
- Object ACL with public access

**Commands:**
- `hcloud obs ListBuckets`
- `hcloud obs GetBucketAcl`
- `hcloud obs ListObjects` + `hcloud obs GetObjectAcl`

**Output Structure:**
```json
{
  "obs_issues": [
    {
      "bucket_name": "my-bucket",
      "issue_type": "public_bucket",
      "permission": "public-read-write",
      "region": "cn-north-4",
      "risk_level": "high",
      "objects": [
        {"key": "sensitive-data.xlsx", "permission": "public-read"}
      ],
      "recommendation": "set_bucket_private"
    }
  ]
}
```

#### ecs_monitor Tool

Purpose: Monitor ECS instances for low utilization and naming compliance

**Checks:**
- Average CPU usage < 10% over last 24 hours
- Name matches pattern `/^00\d{6}/` (employee ID format)

**Commands:**
- `hcloud ecs ListServers`
- `hcloud ces ListMetrics` + `hcloud ces ShowMetricData` (for CPU metrics)

**Output Structure:**
```json
{
  "ecs_issues": [
    {
      "instance_id": "ecs-xxx",
      "instance_name": "test-server",
      "vpc_id": "vpc-xxx",
      "issues": [
        {
          "type": "low_cpu_usage",
          "severity": "info",
          "details": {"avg_cpu_24h": "5.2%"}
        },
        {
          "type": "naming_violation",
          "severity": "warning",
          "details": {"expected_pattern": "00XXXXXX"}
        }
      ],
      "created_by": "lisi",
      "recommendation": "optimize_or_release"
    }
  ]
}
```

#### eip_scanner Tool

Purpose: Detect unattached Elastic IPs

**Commands:** `hcloud eip ListPublicips`

**Output Structure:**
```json
{
  "unattached_eips": [
    {
      "eip_id": "eip-xxx",
      "eip_address": "123.45.67.89",
      "status": "unattached",
      "region": "cn-north-4",
      "created_by": "wangwu",
      "recommendation": "release_if_not_needed"
    }
  ]
}
```

#### report_generator Tool

Purpose: Generate reports in multiple formats

**Input:** Combined results from all scanner tools

**Output Formats:**

1. **JSON** (primary): Structured data for system integration
2. **Markdown** (manual only): Human-readable report
3. **Message templates**: For IM integration (user-configurable)

**Report Structure:**
```json
{
  "scan_metadata": {
    "timestamp": "2026-04-08T09:00:00Z",
    "scan_type": "scheduled|manual",
    "regions": ["cn-north-4", "cn-south-1", "cn-east-2"],
    "duration_seconds": 350
  },
  "summary": {
    "total": {
      "vpcs": 25,
      "unused_vpcs": 5,
      "security_issues": 12,
      "public_obs_buckets": 3,
      "low_utilization_ecs": 8,
      "unattached_eips": 5,
      "naming_violations": 10
    },
    "by_region": {
      "cn-north-4": {
        "vpcs": 10,
        "unused_vpcs": 2,
        "security_issues": 5,
        "public_obs_buckets": 1,
        "low_utilization_ecs": 3,
        "unattached_eips": 2,
        "naming_violations": 4
      },
      "cn-south-1": {
        "vpcs": 8,
        "unused_vpcs": 2,
        "security_issues": 4,
        "public_obs_buckets": 1,
        "low_utilization_ecs": 3,
        "unattached_eips": 2,
        "naming_violations": 3
      },
      "cn-east-2": {
        "vpcs": 7,
        "unused_vpcs": 1,
        "security_issues": 3,
        "public_obs_buckets": 1,
        "low_utilization_ecs": 2,
        "unattached_eips": 1,
        "naming_violations": 3
      }
    }
  },
  "details": {
    "vpc_analysis": [
      {
        "vpc_id": "vpc-xxx",
        "vpc_name": "test-vpc",
        "region": "cn-north-4",
        "status": "unused",
        ...
      }
    ],
    "security_issues": [
      {
        "security_group_id": "sg-xxx",
        "region": "cn-north-4",
        ...
      }
    ],
    "obs_issues": [...],
    "ecs_issues": [...],
    "unattached_eips": [...]
  },
  "action_items": [
    {
      "resource_type": "vpc",
      "resource_id": "vpc-xxx",
      "region": "cn-north-4",
      "action": "contact_owner",
      "owner": "zhangsan",
      "reason": "unused_for_30_days"
    }
  ]
}
```

## Rule Engine

### YAML Rule Format

```yaml
# rules/naming-conventions.yaml
rules:
  - id: "ecs-naming-convention"
    name: "ECS Naming Convention Check"
    resource: "ecs"
    condition: "name !~ /\d{6,}/"
    severity: "warning"
    description: "ECS instance name must contain employee ID (at least 6 consecutive digits)"

  - id: "sg-high-risk-ports"
    name: "High Risk Port Exposure"
    resource: "security_group"
    condition: "ports contains [22,33,44] and source = 0.0.0.0/0"
    severity: "critical"
    description: "Security group has high-risk ports open to internet"

  - id: "low-cpu-usage"
    name: "Low CPU Utilization"
    resource: "ecs"
    condition: "cpu_avg_24h < 10"
    severity: "info"
    description: "Average CPU utilization below 10% in last 24 hours"
```

### Rule Loading Priority

1. User rules: `./rules/*.yaml` (if exists)
2. Built-in rules: `skills/huaweicloud-resource-manager/rules/*.yaml`

### Python Extension Point

For complex rules, users can create Python files in `./rules/custom/`:

```python
# rules/custom/advanced_check.py
from huaweicloud_resource_manager.rules import Rule

class AdvancedSecurityCheck(Rule):
    def evaluate(self, resource):
        # Custom logic
        pass
```

## Report Storage

### Directory Structure

```
reports/
└── 2026-04-08/
    ├── scheduled_09-00-00.json
    ├── scheduled_10-00-00.json
    ├── scheduled_11-00-00.json
    ├── manual_14-30-00.json
    └── manual_14-30-00.md
```

### Naming Convention

- **Scheduled scans**: `scheduled_HH-MM-SS.json`
- **Manual scans**: `manual_HH-MM-SS.{json,md}`

### Retention Policy

- Automatically delete reports older than 7 days
- Configurable via `--retention-days` parameter (default: 7)

## Interaction Modes

### Interactive Mode (Default)

```
User: Please scan Huawei Cloud resources

Claude: I'll help you scan your Huawei Cloud resources. First, let's configure the connection.

Step 1: Authentication
Please provide your Huawei Cloud Access Key ID: [input]
Please provide your Secret Access Key: [masked input]
Please specify the regions to scan (comma-separated, e.g., cn-north-4,cn-south-1):
- Available regions: cn-north-4, cn-south-1, cn-east-2, cn-north-1
- Or type "all" to scan all available regions
- Default: cn-north-4: [input]

Step 2: Proxy Configuration (Optional)
Do you need to configure proxy? (yes/no): [input]
If yes:
  HTTP_PROXY: [input]
  HTTPS_PROXY: [input]
  NO_PROXY: [input]

Step 3: Scan Scope
Scan all VPCs? (yes/no): [input]
If no:
  Please specify VPC IDs (comma-separated): [input]

[Scan executes...]

Report generated: ./reports/2026-04-08/manual_09-15-30.md
```

### Command Mode

```bash
# Quick scan with all defaults (single region)
/huaweicloud-scan

# Scan multiple regions
/huaweicloud-scan --regions=cn-north-4,cn-south-1,cn-east-2

# Scan all available regions
/huaweicloud-scan --regions=all

# Specify output path
/huaweicloud-scan --regions=cn-south-1 --output=./my-reports/

# Scheduled scan mode (JSON only, no Markdown)
/huaweicloud-scan --mode=scheduled --timestamp=2026-04-08T09:00:00Z --regions=all

# Skip interactive prompts (use environment variables)
/huaweicloud-scan --non-interactive
```

## Security Considerations

1. **Credential Handling**
   - AK/SK only stored in environment variables
   - Never written to files or logs
   - Commands displayed with masked sensitive data

2. **Access Control**
   - All scan operations are read-only
   - No deletion capability
   - Recommendations require human action

3. **Data Privacy**
   - Reports stored locally only
   - No data sent to external services
   - User responsible for report access control

## Multi-Region Scanning

### Scanning Strategy

When multiple regions are specified, the tool follows this execution flow:

1. **Region Discovery** (if `--regions=all`)
   - Query IAM service for all accessible regions
   - Validate connectivity to each region

2. **Sequential Scanning**
   - Scan regions one by one to avoid rate limiting
   - Progress is reported per region
   - Failed regions are logged but don't stop the entire scan

3. **Result Aggregation**
   - Combine results from all regions
   - Maintain region context in every resource record
   - Provide both global and per-region summaries

### Progress Reporting

During multi-region scans, real-time progress is reported:

```
[1/3] Scanning region: cn-north-4
  - VPC inventory: 10 found
  - Security scan: 2 issues
  - ECS monitoring: 3 low utilization
  [OK] Completed (45s)

[2/3] Scanning region: cn-south-1
  - VPC inventory: 8 found
  - Security scan: 1 issue
  [OK] Completed (38s)

[3/3] Scanning region: cn-east-2
  - VPC inventory: 7 found
  - Security scan: 0 issues
  [OK] Completed (42s)

Report generated: ./reports/2026-04-08/manual_09-15-30.md
Total resources across 3 regions: VPCs=25, ECS=45, OBS=12
```

### Error Handling

If a specific region fails during multi-region scan:
- Error is recorded in `scan_metadata.failed_regions`
- Other regions continue scanning
- Final report includes partial results with warning notes

```json
{
  "scan_metadata": {
    "regions": ["cn-north-4", "cn-south-1", "cn-east-2"],
    "successful_regions": ["cn-north-4", "cn-south-1"],
    "failed_regions": [
      {
        "region": "cn-east-2",
        "error": "Connection timeout after 30s"
      }
    ]
  }
}
```

## Implementation Phases

### Phase 1: Core Infrastructure
- huaweicloud-core skills (proxy-injection, auth-manager)
- Basic report generator

### Phase 2: VPC Management
- vpc_inventory tool
- vpc_analyzer tool

### Phase 3: Security Scanning
- security_scanner tool
- obs_scanner tool

### Phase 4: Resource Optimization
- ecs_monitor tool
- eip_scanner tool
- Rule engine (YAML + Python)

### Phase 5: Integration
- Message templates
- Documentation
- CI/CD examples

## Appendix

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| HWCLOUD_ACCESS_KEY | Huawei Cloud Access Key | Yes |
| HWCLOUD_SECRET_KEY | Huawei Cloud Secret Key | Yes |
| HWCLOUD_REGIONS | Comma-separated region IDs (e.g., cn-north-4,cn-south-1) | Yes |
| HWCLOUD_PROJECT_ID | Project ID | Optional |
| HTTP_PROXY | HTTP proxy URL | Optional |
| HTTPS_PROXY | HTTPS proxy URL | Optional |
| NO_PROXY | Comma-separated no-proxy hosts | Optional |

**Note:** When `HWCLOUD_REGIONS=all`, the tool will automatically discover and scan all available regions.

### CLI Reference

All hcloud commands follow official documentation:
https://support.huaweicloud.com/intl/en-us/productdesc-hcli/hcli_01.html

### Scheduling Examples

**Cron (hourly):**
```bash
0 * * * * cd /path/to/project && claude "run huaweicloud scan in scheduled mode"
```

**Airflow DAG:**
```python
from airflow import DAG
from airflow.operators.bash import BashOperator

dag = DAG('huaweicloud_scan', schedule_interval='0 * * * *')
scan_task = BashOperator(
    task_id='scan',
    bash_command='claude "/huaweicloud-scan --mode=scheduled"',
    dag=dag
)
```
