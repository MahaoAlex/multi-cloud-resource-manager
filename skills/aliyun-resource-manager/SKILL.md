# Aliyun Resource Manager Skill

## Description

Unified Alibaba Cloud resource management tool for VPC inventory, security scanning, OSS scanning, ECS monitoring, EIP scanning, and compliance checking across multiple regions.

## Tools Reference

### scan_vpcs
Enumerate and analyze all VPC resources across configured regions.

**Parameters:**
- `regions` (array): List of regions to scan (defaults to ALIYUN_REGIONS env var)
- `output_dir` (string): Directory to save reports (default: ./reports)
- `scan_type` (string): Type of scan - manual generates both JSON and Markdown, scheduled generates JSON only

### scan_security
Scan security groups for high-risk configurations.

**Parameters:**
- `regions` (array): List of regions to scan
- `check_ports` (array): List of ports to check (default: [22, 33, 44])

### scan_oss
Detect publicly accessible OSS buckets and objects.

**Parameters:**
- `regions` (array): List of regions to scan

### scan_ecs
Monitor ECS instances for low utilization and naming compliance.

**Parameters:**
- `regions` (array): List of regions to scan
- `cpu_threshold` (number): CPU utilization threshold percentage (default: 10)
- `check_naming` (boolean): Whether to check naming conventions (default: true)

### scan_eips
Detect unattached Elastic IPs.

**Parameters:**
- `regions` (array): List of regions to scan

### full_scan
Perform complete resource scan across all categories.

**Parameters:**
- `regions` (array): List of regions to scan (default: all configured regions)
- `output_dir` (string): Directory to save reports (default: ./reports)
- `scan_type` (string): Type of scan
- `retention_days` (integer): Number of days to keep reports (default: 7)

### generate_report
Generate formatted reports from scan results.

**Parameters:**
- `scan_results` (object): Raw scan results data
- `format` (string): Output format (json, markdown, both)
- `output_path` (string): Output file path

### list_rules
List all loaded rules and their configurations.

**Parameters:** None

### run_custom_rule
Run a custom rule against resources.

**Parameters:**
- `rule_file` (string): Path to custom rule YAML file
- `resource_type` (string): Type of resources to check

## Examples

### Basic VPC Scan
```
/aliyun-resource-manager scan_vpcs --regions=["cn-hangzhou"]
```

### Security Scan
```
/aliyun-resource-manager scan_security --regions=["cn-hangzhou", "cn-shanghai"]
```

### Full Resource Scan
```
/aliyun-resource-manager full_scan --regions=["cn-hangzhou"] --scan_type="manual"
```

### List All Rules
```
/aliyun-resource-manager list_rules
```

## Dependencies

- proxy-injection
- auth-manager

## File Structure

```
aliyun-resource-manager/
├── skill.yaml              # Skill definition
├── main.py                 # Main entry point
├── SKILL.md               # This file
├── README.md              # User documentation
├── rules/                 # Rule definitions
│   ├── security-rules.yaml
│   └── naming-conventions.yaml
└── tools/                 # Tool implementations
    ├── vpc_inventory.py
    ├── vpc_analyzer.py
    ├── security_scanner.py
    ├── oss_scanner.py
    ├── ecs_monitor.py
    ├── eip_scanner.py
    ├── report_generator.py
    └── rule_engine.py
```
