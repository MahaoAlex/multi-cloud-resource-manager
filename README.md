# Huawei Cloud Resource Manager

A Claude Code Skill for Huawei Cloud resource management. Automate resource inventory, security scanning, and compliance checking across multiple regions with concurrent scanning support.

## Overview

Huawei Cloud Resource Manager provides comprehensive resource scanning capabilities through Claude Code Skills. It supports **multi-region concurrent scanning** with configurable rules and generates actionable reports for resource optimization.

### Key Features

- **Concurrent Multi-Region Scanning**: Scan up to 5 regions simultaneously for 78% time savings
- **Security-First Credential Handling**: Interactive input prevents credential exposure in shell history
- **Comprehensive Resource Coverage**: VPC, ECS, OBS, EIP, Security Groups
- **YAML-Based Rule Engine**: Customizable compliance rules
- **Multiple Report Formats**: JSON for automation, Markdown for human review

## Implemented Capabilities

| Capability | Description | Status |
|------------|-------------|--------|
| **VPC Inventory** | Enumerate VPCs and analyze usage across regions | Implemented |
| **Security Scanning** | Detect high-risk security group configurations | Implemented |
| **OBS Scanning** | Identify publicly accessible buckets and objects | Implemented |
| **ECS Monitoring** | Find low-utilization instances and naming violations | Implemented |
| **EIP Scanning** | Detect unattached Elastic IPs | Implemented |
| **Rule Engine** | YAML-based customizable compliance rules | Implemented |
| **Multi-Region** | Support scanning all Huawei Cloud regions | Implemented |
| **Concurrent Scanning** | Parallel region scanning with configurable workers | Implemented |

## Supported Regions

| Region ID | Location | Status |
|-----------|----------|--------|
| cn-north-4 | Beijing | Available |
| cn-north-1 | Beijing | Available |
| cn-south-1 | Guangzhou | Available |
| cn-east-2 | Shanghai | Available |
| cn-east-3 | Shanghai | Available |
| cn-southwest-2 | Guiyang | Available |
| ap-southeast-1 | Hong Kong | Available |
| ap-southeast-2 | Bangkok | Available |
| ap-southeast-3 | Singapore | Available |
| eu-west-101 | Amsterdam | Available |
| af-south-1 | Johannesburg | Available |

## Quick Start

### Prerequisites

- Claude Code installed and configured
- Python 3.8+
- Huawei Cloud CLI (KooCLI / hcloud) installed
- Huawei Cloud Access Key and Secret Key

### Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/MahaoAlex/multi-cloud-resource-manager.git
   cd multi-cloud-resource-manager
   ```

2. **Install Huawei Cloud CLI**
   ```bash
   # Linux (AMD64)
   curl -LO https://ap-southeast-3-hwcloudcli.obs.ap-southeast-3.myhuaweicloud.com/cli/latest/huaweicloud-cli-linux-amd64.tar.gz
   tar -xzf huaweicloud-cli-linux-amd64.tar.gz
   sudo mv hcloud /usr/local/bin/
   
   # Verify installation (note: hcloud doesn't support --version)
   hcloud --help > /dev/null 2>&1 && echo "hcloud installed"
   ```

3. **Install the Agent Skills**
   ```bash
   # Create skills directory if not exists
   mkdir -p ~/.claude/skills
   
   # Copy core skills
   cp -r skills/huaweicloud-core/proxy-injection ~/.claude/skills/
   cp -r skills/huaweicloud-core/auth-manager ~/.claude/skills/
   
   # Copy main resource manager skill
   cp -r skills/huaweicloud-resource-manager ~/.claude/skills/
   
   # Verify installation
   ls -la ~/.claude/skills/
   ```

4. **Restart Claude Code**
   ```bash
   exit
   claude
   ```

5. **Configure credentials (Secure Method)**
   
   Use interactive configuration to avoid credential exposure:
   ```
   Configure Huawei Cloud authentication
   ```
   
   Or use the secure runner script:
   ```bash
   python ~/.claude/skills/huaweicloud-core/auth-manager/secure_runner.py --setup
   ```

6. **Start scanning**
   ```
   # Interactive mode
   Execute complete Huawei Cloud resource scan
   
   # Command mode with concurrent scanning
   /huaweicloud-scan full_scan --regions=["cn-north-4","cn-south-1"] --max_workers=3
   ```

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Proxy Injection** | `Configure Huawei Cloud proxy` | Configure HTTP/HTTPS proxy for Huawei Cloud CLI |
| **Auth Manager** | `Configure Huawei Cloud authentication` | Interactive multi-region authentication setup |
| **Resource Scanner** | `/huaweicloud-scan full_scan` | Full resource scan with concurrent region support |
| **VPC Inventory** | `Scan Huawei Cloud VPC resources` | Enumerate and analyze VPC usage |
| **Security Scanner** | `Scan Huawei Cloud security risks` | Detect high-risk security group configurations |
| **OBS Scanner** | `Check Huawei Cloud OBS public access` | Identify public access configurations |
| **ECS Monitor** | `Check Huawei Cloud ECS resource optimization` | Check CPU utilization and naming compliance |
| **EIP Scanner** | `Scan Huawei Cloud unattached EIPs` | Find unattached Elastic IPs |

## Concurrent Scanning

### Performance Optimization

The resource manager supports concurrent scanning of multiple regions to significantly reduce total scan time.

| Scan Mode | Workers | Time for 5 Regions | Time Saved |
|-----------|---------|-------------------|------------|
| Serial | 1 | ~200 seconds | - |
| Low Concurrent | 2 | ~100 seconds | 50% |
| Default | 5 | ~45 seconds | 78% |

### Usage

```
# Default concurrent scan (5 workers)
/huaweicloud-scan full_scan --regions=all

# Custom concurrent workers (1-5)
/huaweicloud-scan full_scan --regions=["cn-north-4","cn-south-1","cn-east-2"] --max_workers=3

# Serial scan for debugging
/huaweicloud-scan full_scan --regions=["cn-north-4"] --max_workers=1
```

### How It Works

- **ThreadPoolExecutor**: Each region scanned by independent worker thread
- **Staggered Start**: 0.5-1.5s random delay per worker prevents API rate limiting
- **Read-Only Safety**: All scan operations are read-only, concurrent execution is safe
- **Max Workers**: Limited to 5 to prevent API throttling

## Security Scanning

The security scanner identifies the following risk patterns:

| Risk Type | Severity | Description | Recommendation |
|-----------|----------|-------------|----------------|
| Open SSH Port | Critical | Port 22 open to 0.0.0.0/0 | Restrict to specific IPs |
| Open RDP Port | Critical | Port 3389 open to internet | Use VPN or bastion host |
| Open Port 33 | Critical | Port 33 open to internet | Close unused ports |
| Open Port 44 | Critical | Port 44 open to internet | Close unused ports |
| Public OBS Bucket | High | Bucket with public-read ACL | Set to private |
| Public OBS Object | High | Object with public access | Review and restrict |
| Unattached EIP | Medium | Elastic IP not bound to resource | Release if unused |
| Low CPU ECS | Info | CPU utilization < 10% | Consider downsizing |

## Naming Convention

ECS instances must contain at least 6 consecutive digits (employee ID format):

- **Valid**: `user-00123456-web`, `test123456vm`, `00123456`
- **Invalid**: `web-server`, `test12345`, `dev-12345`

This convention helps with:
- Resource ownership identification
- Cost allocation tracking
- Audit compliance

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code Interface                        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│              Huawei Cloud Resource Manager                       │
│                    (Main Skill Controller)                       │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼────────┐ ┌────▼────┐ ┌────────▼────────┐
    │  Proxy Injection │ │  Auth   │ │  Rule Engine    │
    │     Skill        │ │ Manager │ │                 │
    └─────────┬────────┘ └────┬────┘ └─────────────────┘
              │               │
    ┌─────────▼───────────────▼─────────────────────────────┐
    │              Resource Scanner Tools                    │
    │  ┌──────────┬──────────┬──────────┬──────────┐        │
    │  │   VPC    │ Security │   OBS    │   ECS    │        │
    │  │ Inventory│ Scanner  │ Scanner  │ Monitor  │        │
    │  ├──────────┼──────────┼──────────┼──────────┤        │
    │  │   EIP    │  VPC     │  Report  │   Rule   │        │
    │  │ Scanner  │ Analyzer │ Generator│  Engine  │        │
    │  └──────────┴──────────┴──────────┴──────────┘        │
    └────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼────────┐ ┌────▼────────┐ ┌────▼────────┐
    │  cn-north-4      │ │ cn-south-1  │ │ cn-east-2   │
    │  (Worker 1)      │ │ (Worker 2)  │ │ (Worker 3)  │
    │  [Concurrent]    │ │[Concurrent] │ │[Concurrent] │
    └──────────────────┘ └─────────────┘ └─────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Main Controller** | Orchestrates concurrent scanning, aggregates results |
| **Auth Manager** | Secure credential handling, multi-region validation |
| **Proxy Injection** | Network proxy configuration for corporate environments |
| **Scanner Tools** | Individual resource type scanning implementations |
| **Rule Engine** | YAML-based compliance rule evaluation |
| **Report Generator** | JSON/Markdown report generation |

## Report Output

### Directory Structure

```
reports/
└── 2026-04-08/
    ├── scheduled_09-00-00.json     # Scheduled scan (JSON only)
    ├── manual_14-30-00.json        # Manual scan results
    └── manual_14-30-00.md          # Human-readable report
```

### Report Formats

- **Manual scans**: Generate both JSON and Markdown reports
- **Scheduled scans**: Generate JSON reports only (lightweight)
- **Retention**: Automatically clean reports older than 7 days

### Sample Report Structure

```json
{
  "regions": ["cn-north-4", "cn-south-1"],
  "duration_seconds": 52,
  "summary": {
    "vpcs": 16,
    "unused_vpcs": 3,
    "security_issues": 4,
    "public_obs_buckets": 2,
    "low_utilization_ecs": 4,
    "unattached_eips": 3
  },
  "summary_by_region": {
    "cn-north-4": {
      "vpcs": 8,
      "security_issues": 3,
      "obs_issues": 2,
      "ecs_issues": 5,
      "unattached_eips": 2
    }
  },
  "action_items": [
    {
      "severity": "CRITICAL",
      "resource": "sg-001",
      "issue": "Port 22 open to 0.0.0.0/0",
      "recommendation": "Restrict to specific IP ranges"
    }
  ]
}
```

## Configuration

### Environment Variables

| Variable | Description | Required | Example |
|----------|-------------|----------|---------|
| `HWCLOUD_ACCESS_KEY` | Huawei Cloud Access Key ID | Yes | `HPUA0A...` |
| `HWCLOUD_SECRET_KEY` | Huawei Cloud Secret Access Key | Yes | `DDpL6T...` |
| `HWCLOUD_REGIONS` | Comma-separated regions or 'all' | Yes | `cn-north-4,cn-south-1` |
| `HWCLOUD_PROJECT_ID` | Project ID for IAM sub-users | No | `0a1b2c...` |
| `HTTP_PROXY` | HTTP proxy URL | No | `http://proxy:8080` |
| `HTTPS_PROXY` | HTTPS proxy URL | No | `http://proxy:8080` |
| `NO_PROXY` | Comma-separated no-proxy hosts | No | `localhost,127.0.0.1` |

### Secure Credential Configuration

**Recommended: Interactive Configuration**
```
Configure Huawei Cloud authentication
```

**Alternative: Secure Script**
```bash
python ~/.claude/skills/huaweicloud-core/auth-manager/secure_runner.py --setup
```

**⚠️ Warning: Avoid Direct Export**
```bash
# DON'T DO THIS - Credentials will be saved in shell history!
export HWCLOUD_ACCESS_KEY="your-secret-key"
export HWCLOUD_SECRET_KEY="your-secret-key"

# If you must use direct export, clear history immediately
history -c
```

### Custom Rules

Create custom rules in `./rules/` directory:

```yaml
# rules/custom-rules.yaml
rules:
  - id: "ecs-owner-tag-check"
    name: "ECS Owner Tag Required"
    resource: "ecs"
    condition: "tags !contains ['Owner']"
    severity: "warning"
    description: "ECS instances must have an Owner tag for accountability"

  - id: "vpc-environment-tag"
    name: "VPC Environment Tag"
    resource: "vpc"
    condition: "name !~ /-(dev|prod|test|staging)-/"
    severity: "info"
    description: "VPC names should include environment identifier"
```

## Scheduling

### Cron (Recommended)

Configure hourly scans:

```bash
# Edit crontab
crontab -e

# Add line (use env file for security)
0 * * * * source /path/to/huaweicloud-env.sh && claude "/huaweicloud-scan --mode=scheduled --regions=all --max_workers=3" >> /var/log/huaweicloud-scan.log 2>&1
```

### Airflow DAG

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'cloudops',
    'depends_on_past': False,
    'email': ['ops@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'huaweicloud_resource_scan',
    default_args=default_args,
    description='Huawei Cloud resource security scan',
    schedule_interval='0 * * * *',
    start_date=datetime(2026, 4, 8),
    catchup=False,
) as dag:

    scan_task = BashOperator(
        task_id='resource_scan',
        bash_command='source /path/to/huaweicloud-env.sh && claude "/huaweicloud-scan --mode=scheduled --regions=all --max_workers=3"',
    )
```

## Documentation

- **[Setup Guide](./docs/huaweicloud-setup-guide.md)** - Complete deployment, configuration, and troubleshooting guide (Chinese)
- **[CLAUDE.md](./CLAUDE.md)** - Development guidelines and code specifications

## Security Best Practices

### Credential Security

- **Never** store plaintext credentials in command history
- Use interactive configuration methods
- Set environment variable file permissions to `600`
- Rotate credentials every 90 days
- Use IAM sub-accounts with minimal permissions

### Required IAM Permissions

```json
{
  "Version": "1.1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "vpc:vpcs:list",
        "vpc:subnets:list",
        "vpc:securityGroups:list",
        "vpc:securityGroupRules:list",
        "ecs:servers:list",
        "ecs:serverVolumeAttachments:list",
        "ecs:serverInterfaces:list",
        "obs:bucket:list",
        "obs:bucket:getBucketAcl",
        "obs:object:getObjectAcl",
        "ces:metrics:list",
        "ces:data:list"
      ],
      "Resource": ["*"]
    }
  ]
}
```

### Operational Security

- All scanning operations are **read-only**
- Delete operations require explicit human confirmation
- Resource data is processed locally
- No data is sent to external servers
- Reports contain metadata only, not sensitive credentials

## Troubleshooting

### Common Issues

**Issue**: `Failed to parse JSON output` warnings during concurrent scan

**Solution**: This is normal for empty resources. Reduce workers if needed:
```
/huaweicloud-scan full_scan --max_workers=2
```

**Issue**: Authentication failures

**Solution**: Verify credentials using secure method:
```bash
python ~/.claude/skills/huaweicloud-core/auth-manager/secure_runner.py --verify
```

**Issue**: API rate limiting

**Solution**: Reduce concurrent workers:
```
/huaweicloud-scan full_scan --max_workers=1
```

For more troubleshooting, see the [Setup Guide](./docs/huaweicloud-setup-guide.md).

## Contributing

We welcome contributions! Areas for contribution:

- Additional scanning rules
- New resource types (RDS, ELB, etc.)
- Report format improvements
- Performance optimizations
- Documentation translations

## License

This project is licensed under the [MIT License](./LICENSE).

## Support

- **Issues**: [GitHub Issues](https://github.com/MahaoAlex/multi-cloud-resource-manager/issues)
- **Documentation**: See [Setup Guide](./docs/huaweicloud-setup-guide.md) for detailed instructions

---

**Secure Your Huawei Cloud Infrastructure with Confidence**

Built with the [Claude Agent Skills Specification](https://docs.anthropic.com/)
