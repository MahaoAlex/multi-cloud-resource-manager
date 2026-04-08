# Huawei Cloud Resource Manager

A Claude Code Skill for Huawei Cloud resource management. Automate resource inventory, security scanning, and compliance checking across multiple regions.

## Overview

Huawei Cloud Resource Manager provides comprehensive resource scanning capabilities through Claude Code Skills. It supports multi-region scanning with configurable rules and generates actionable reports for resource optimization.

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

## Supported Regions

- cn-north-4 (Beijing)
- cn-north-1 (Beijing)
- cn-south-1 (Guangzhou)
- cn-east-2 (Shanghai)
- cn-east-3 (Shanghai)
- cn-southwest-2 (Guiyang)
- ap-southeast-1 (Hong Kong)
- ap-southeast-2 (Bangkok)
- ap-southeast-3 (Singapore)
- eu-west-101 (Amsterdam)
- af-south-1 (Johannesburg)

## Quick Start

### Prerequisites

- Claude Code installed
- Huawei Cloud CLI (hcloud) installed
- Huawei Cloud Access Key and Secret Key

### Installation

1. Clone this repository
   ```bash
   git clone https://github.com/your-org/multi-cloud-resource-manager.git
   cd multi-cloud-resource-manager
   ```

2. Install the Agent Skills
   ```bash
   # For Claude Code
   cp -r skills/huaweicloud-core/* ~/.claude/skills/
   cp -r skills/huaweicloud-resource-manager ~/.claude/skills/
   ```

3. Configure Huawei Cloud credentials
   ```bash
   export HWCLOUD_ACCESS_KEY="your-access-key"
   export HWCLOUD_SECRET_KEY="your-secret-key"
   export HWCLOUD_REGIONS="cn-north-4,cn-south-1"
   ```

4. Start using the Skills
   ```
   # Interactive mode
   Please scan my Huawei Cloud resources

   # Command mode
   /huaweicloud-scan --regions=cn-north-4,cn-south-1
   ```

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| Proxy Injection | `/proxy-injection` | Configure HTTP/HTTPS proxy for hcloud CLI |
| Auth Manager | `/auth-manager` | Configure multi-region authentication |
| Resource Scanner | `/huaweicloud-scan` | Full resource scan across all categories |
| VPC Inventory | Scan VPCs | Enumerate and analyze VPC usage |
| Security Scanner | Scan security groups | Detect high-risk port configurations |
| OBS Scanner | Scan OBS buckets | Identify public access configurations |
| ECS Monitor | Monitor ECS | Check CPU utilization and naming compliance |
| EIP Scanner | Scan EIPs | Find unattached Elastic IPs |

## Security Scanning

The security scanner identifies the following risk patterns:

| Risk Type | Severity | Description |
|-----------|----------|-------------|
| Open SSH Port | Critical | Port 22 open to 0.0.0.0/0 |
| Open Port 33 | Critical | Port 33 open to internet |
| Open Port 44 | Critical | Port 44 open to internet |
| Public OBS Bucket | High | Bucket with public-read or public-read-write |
| Public OBS Object | High | Object with public access |

## Naming Convention

ECS instances must contain at least 6 consecutive digits (employee ID format):

- Valid: `user-00123456-web`, `test123456vm`, `00123456`
- Invalid: `web-server`, `test12345`

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Agent Interface                        │
│                   (Claude Code)                         │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│           Huawei Cloud Resource Manager                 │
│  ┌──────────────┬──────────────┬─────────────────────┐  │
│  │   VPC        │   Security   │   OBS Scanner       │  │
│  │   Inventory  │   Scanner    │                     │  │
│  ├──────────────┼──────────────┼─────────────────────┤  │
│  │   ECS        │   EIP        │   Rule Engine       │  │
│  │   Monitor    │   Scanner    │                     │  │
│  └──────────────┴──────────────┴─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼────┐  ┌────▼────┐  ┌────▼────┐
         │cn-north-│  │cn-south-│  │cn-east-2│
         │   4     │  │   1     │  │         │
         └─────────┘  └─────────┘  └─────────┘
```

## Report Output

### Directory Structure

```
reports/
└── 2026-04-08/
    ├── scheduled_09-00-00.json     # Scheduled scan (JSON only)
    ├── manual_14-30-00.json        # Manual scan
    └── manual_14-30-00.md          # Manual scan (human-readable)
```

### Report Formats

- **Manual scans**: Generate both JSON and Markdown reports
- **Scheduled scans**: Generate JSON reports only
- **Retention**: Automatically clean reports older than 7 days

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| HWCLOUD_ACCESS_KEY | Huawei Cloud Access Key | Yes |
| HWCLOUD_SECRET_KEY | Huawei Cloud Secret Key | Yes |
| HWCLOUD_REGIONS | Comma-separated regions or 'all' | Yes |
| HTTP_PROXY | HTTP proxy URL | Optional |
| HTTPS_PROXY | HTTPS proxy URL | Optional |
| NO_PROXY | Comma-separated no-proxy hosts | Optional |

### Custom Rules

Create custom rules in `./rules/` directory:

```yaml
# rules/custom-rules.yaml
rules:
  - id: "my-rule"
    name: "My Custom Check"
    resource: "ecs"
    condition: "name !~ /-prod$/"
    severity: "warning"
    description: "Production ECS must have -prod suffix"
```

## Documentation

- [Deployment Guide](./DEPLOY_GUIDE.md) - Complete Chinese deployment and testing guide
- [Design Specification](./docs/superpowers/specs/2026-04-08-huaweicloud-resource-manager-design.md) - Technical design document

## Security Best Practices

> **Warning: Security First Approach**

- Never store plaintext credentials - Use environment variables
- All skills operate with read-only permissions
- Delete operations require explicit human confirmation
- Resource data is processed locally
- Reports contain metadata only, not sensitive data

## Scheduling

Configure hourly scans using cron:

```bash
0 * * * * cd /path/to/project && claude "/huaweicloud-scan --mode=scheduled --regions=all"
```

## Contributing

We welcome contributions! Areas for contribution:

- Additional scanning rules
- New resource types
- Report format improvements
- Performance optimizations

## License

This project is licensed under the [MIT License](./LICENSE).

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/multi-cloud-resource-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/multi-cloud-resource-manager/discussions)

---

**Secure Your Huawei Cloud Infrastructure with Confidence**

Built with the [Claude Agent Skills Specification](https://docs.anthropic.com/)
