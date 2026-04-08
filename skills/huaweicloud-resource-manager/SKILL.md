---
name: huaweicloud-resource-manager
description: Unified Huawei Cloud resource management tool for VPC inventory, security scanning, OBS scanning, ECS monitoring, EIP scanning, and compliance checking across multiple regions.
allowed-tools: [Read, Write, Bash, Edit, Grep, Glob]
---

# Huawei Cloud Resource Manager

A comprehensive skill for managing and scanning Huawei Cloud resources.

## Available Tools

### 1. scan_vpcs
Enumerate and analyze all VPC resources across configured regions.

**Usage:**
```
/huaweicloud-resource-manager scan_vpcs
  --regions=["cn-north-4", "cn-south-1"]
  --scan_type="manual"
```

### 2. scan_security
Scan security groups for high-risk configurations (ports 22, 33, 44 open to 0.0.0.0/0).

**Usage:**
```
/huaweicloud-resource-manager scan_security
  --regions=["cn-north-4"]
  --check_ports=[22, 33, 44]
```

### 3. scan_obs
Detect publicly accessible OBS buckets and objects.

**Usage:**
```
/huaweicloud-resource-manager scan_obs
  --regions=["cn-north-4"]
```

### 4. scan_ecs
Monitor ECS instances for low CPU utilization and naming compliance.

**Usage:**
```
/huaweicloud-resource-manager scan_ecs
  --regions=["cn-north-4"]
  --cpu_threshold=10
  --check_naming=true
```

### 5. scan_eips
Detect unattached Elastic IPs.

**Usage:**
```
/huaweicloud-resource-manager scan_eips
  --regions=["cn-north-4"]
```

### 6. full_scan
Perform complete resource scan across all categories.

**Usage:**
```
/huaweicloud-resource-manager full_scan
  --regions=["cn-north-4", "cn-south-1"]
  --scan_type="manual"
  --output_dir="./reports"
```

### 7. list_rules
List all loaded rules and their configurations.

**Usage:**
```
/huaweicloud-resource-manager list_rules
```

### 8. run_custom_rule
Run a custom rule against resources.

**Usage:**
```
/huaweicloud-resource-manager run_custom_rule
  --rule_file="./rules/custom-rules.yaml"
  --resource_type="ecs"
```

## Prerequisites

1. Huawei Cloud CLI (hcloud/KooCLI) must be installed
2. Environment variables must be set:
   - `HWCLOUD_ACCESS_KEY` - Access Key ID
   - `HWCLOUD_SECRET_KEY` - Secret Access Key
   - `HWCLOUD_REGIONS` - Comma-separated region list or 'all'

## Quick Start

1. Configure proxy (if needed): `/proxy-injection`
2. Configure authentication: `/auth-manager`
3. Run full scan: `/huaweicloud-resource-manager full_scan`

## Report Output

Reports are saved to `./reports/YYYY-MM-DD/`:
- Manual scans: JSON + Markdown
- Scheduled scans: JSON only

## Supported Regions

- cn-north-4 (Beijing)
- cn-south-1 (Guangzhou)
- cn-east-2 (Shanghai)
- cn-east-3 (Shanghai)
- cn-southwest-2 (Guiyang)
- ap-southeast-1 (Hong Kong)
- ap-southeast-2 (Bangkok)
- ap-southeast-3 (Singapore)
- eu-west-101 (Amsterdam)
- af-south-1 (Johannesburg)

Use `all` to scan all available regions.
