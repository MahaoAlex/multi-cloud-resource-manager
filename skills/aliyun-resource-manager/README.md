# Aliyun Resource Manager

A comprehensive skill for managing and scanning Alibaba Cloud (Aliyun) resources.

## Overview

This skill provides unified resource management for Alibaba Cloud, supporting:

- VPC inventory and usage analysis
- Security group scanning for high-risk configurations
- OSS bucket public access detection
- ECS instance monitoring (CPU utilization, naming compliance)
- EIP scanning for unattached resources
- Comprehensive reporting in JSON and Markdown formats

## Available Tools

### 1. scan_vpcs
Enumerate and analyze all VPC resources across configured regions.

**Usage:**
```
/aliyun-resource-manager scan_vpcs
  --regions=["cn-hangzhou", "cn-shanghai"]
  --scan_type="manual"
```

### 2. scan_security
Scan security groups for high-risk configurations (ports 22, 33, 44 open to 0.0.0.0/0).

**Usage:**
```
/aliyun-resource-manager scan_security
  --regions=["cn-hangzhou"]
  --check_ports=[22, 33, 44]
```

### 3. scan_oss
Detect publicly accessible OSS buckets and objects.

**Usage:**
```
/aliyun-resource-manager scan_oss
  --regions=["cn-hangzhou"]
```

### 4. scan_ecs
Monitor ECS instances for low CPU utilization and naming compliance.

**Usage:**
```
/aliyun-resource-manager scan_ecs
  --regions=["cn-hangzhou"]
  --cpu_threshold=10
  --check_naming=true
```

### 5. scan_eips
Detect unattached Elastic IPs.

**Usage:**
```
/aliyun-resource-manager scan_eips
  --regions=["cn-hangzhou"]
```

### 6. full_scan
Perform complete resource scan across all categories.

**Usage:**
```
/aliyun-resource-manager full_scan
  --regions=["cn-hangzhou", "cn-shanghai"]
  --scan_type="manual"
  --output_dir="./reports"
```

### 7. list_rules
List all loaded rules and their configurations.

**Usage:**
```
/aliyun-resource-manager list_rules
```

### 8. run_custom_rule
Run a custom rule against resources.

**Usage:**
```
/aliyun-resource-manager run_custom_rule
  --rule_file="./rules/custom-rules.yaml"
  --resource_type="ecs"
```

## Prerequisites

1. Alibaba Cloud CLI (aliyun) must be installed
2. Environment variables must be set:
   - `ALIYUN_ACCESS_KEY_ID` - Access Key ID
   - `ALIYUN_ACCESS_KEY_SECRET` - Access Key Secret
   - `ALIYUN_REGIONS` - Comma-separated region list or 'all'

### Installing Aliyun CLI

```bash
# Download and install aliyun CLI
curl -O https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz
tar -xzf aliyun-cli-linux-latest-amd64.tgz
sudo mv aliyun /usr/local/bin/

# Configure credentials
aliyun configure
```

## Quick Start

1. Configure authentication:
```bash
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"
export ALIYUN_REGIONS="cn-hangzhou,cn-shanghai"
```

2. Run full scan:
```
/aliyun-resource-manager full_scan
```

## Report Output

Reports are saved to `./reports/YYYY-MM-DD/`:
- Manual scans: JSON + Markdown
- Scheduled scans: JSON only

## Supported Regions

- cn-hangzhou (Hangzhou)
- cn-shanghai (Shanghai)
- cn-beijing (Beijing)
- cn-shenzhen (Shenzhen)
- cn-qingdao (Qingdao)
- cn-zhangjiakou (Zhangjiakou)
- cn-hongkong (Hong Kong)
- ap-southeast-1 (Singapore)
- ap-southeast-2 (Sydney)
- ap-northeast-1 (Tokyo)
- us-west-1 (Silicon Valley)
- us-east-1 (Virginia)
- eu-central-1 (Frankfurt)

Use `all` to scan all available regions.

## Service Mapping (Aliyun vs Huawei Cloud)

| Huawei Cloud | Aliyun (Alibaba Cloud) |
|--------------|------------------------|
| VPC | VPC |
| ECS | ECS |
| OBS | OSS |
| EIP | EIP |
| Security Group | Security Group |
| CES (monitoring) | CloudMonitor (CMS) |
| Subnet | VSwitch |
| NIC | ENI |

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ALIYUN_ACCESS_KEY_ID` | Access Key ID | Required |
| `ALIYUN_ACCESS_KEY_SECRET` | Access Key Secret | Required |
| `ALIYUN_REGIONS` | Comma-separated regions or 'all' | cn-hangzhou |
| `OSS_CHECK_OBJECTS` | Enable object-level OSS scanning | true |

### Custom Rules

Place custom rule files in `./rules/` directory. See `rules/security-rules.yaml` for examples.

## License

MIT
