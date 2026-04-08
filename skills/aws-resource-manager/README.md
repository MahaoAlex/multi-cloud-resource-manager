# AWS Resource Manager

A comprehensive skill for managing and scanning AWS resources.

## Overview

This skill provides unified resource management for AWS, supporting:

- VPC inventory and usage analysis
- Security group scanning for high-risk configurations
- S3 bucket public access detection
- EC2 instance monitoring (CPU utilization, naming compliance)
- EIP scanning for unattached resources
- Comprehensive reporting in JSON and Markdown formats

## Available Tools

### 1. scan_vpcs
Enumerate and analyze all VPC resources across configured regions.

**Usage:**
```
/aws-resource-manager scan_vpcs
  --regions=["us-east-1", "us-west-2"]
  --scan_type="manual"
```

### 2. scan_security
Scan security groups for high-risk configurations (ports 22, 33, 44 open to 0.0.0.0/0).

**Usage:**
```
/aws-resource-manager scan_security
  --regions=["us-east-1"]
  --check_ports=[22, 33, 44]
```

### 3. scan_s3
Detect publicly accessible S3 buckets.

**Usage:**
```
/aws-resource-manager scan_s3
  --regions=["us-east-1"]
```

### 4. scan_ec2
Monitor EC2 instances for low CPU utilization and naming compliance.

**Usage:**
```
/aws-resource-manager scan_ec2
  --regions=["us-east-1"]
  --cpu_threshold=10
  --check_naming=true
```

### 5. scan_eips
Detect unattached Elastic IPs.

**Usage:**
```
/aws-resource-manager scan_eips
  --regions=["us-east-1"]
```

### 6. full_scan
Perform complete resource scan across all categories.

**Usage:**
```
/aws-resource-manager full_scan
  --regions=["us-east-1", "us-west-2"]
  --scan_type="manual"
  --output_dir="./reports"
```

### 7. list_rules
List all loaded rules and their configurations.

**Usage:**
```
/aws-resource-manager list_rules
```

### 8. run_custom_rule
Run a custom rule against resources.

**Usage:**
```
/aws-resource-manager run_custom_rule
  --rule_file="./rules/custom-rules.yaml"
  --resource_type="ec2"
```

## Prerequisites

1. AWS CLI must be installed
2. Environment variables must be set:
   - `AWS_ACCESS_KEY_ID` - Access Key ID
   - `AWS_SECRET_ACCESS_KEY` - Secret Access Key
   - `AWS_REGIONS` - Comma-separated region list or 'all'

### Installing AWS CLI

```bash
# Download and install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure credentials
aws configure
```

## Quick Start

1. Configure authentication:
```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGIONS="us-east-1,us-west-2"
```

2. Run full scan:
```
/aws-resource-manager full_scan
```

## Report Output

Reports are saved to `./reports/YYYY-MM-DD/`:
- Manual scans: JSON + Markdown
- Scheduled scans: JSON only

## Supported Regions

- us-east-1 (N. Virginia)
- us-east-2 (Ohio)
- us-west-1 (N. California)
- us-west-2 (Oregon)
- eu-west-1 (Ireland)
- eu-west-2 (London)
- eu-central-1 (Frankfurt)
- ap-southeast-1 (Singapore)
- ap-southeast-2 (Sydney)
- ap-northeast-1 (Tokyo)
- ap-south-1 (Mumbai)
- sa-east-1 (Sao Paulo)

Use `all` to scan all available regions.

## Service Mapping (AWS vs Huawei Cloud / Aliyun)

| Huawei Cloud | Aliyun | AWS |
|--------------|--------|-----|
| VPC | VPC | VPC |
| ECS | ECS | EC2 |
| OBS | OSS | S3 |
| EIP | EIP | Elastic IP |
| Security Group | Security Group | Security Group |
| CES | CMS | CloudWatch |
| Subnet | VSwitch | Subnet |
| NIC | ENI | ENI |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | Access Key ID | Required |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key | Required |
| `AWS_REGIONS` | Comma-separated regions or 'all' | us-east-1 |
| `S3_CHECK_OBJECTS` | Enable object-level S3 scanning | false |

### Custom Rules

Place custom rule files in `./rules/` directory. See `rules/security-rules.yaml` for examples.

## License

MIT
