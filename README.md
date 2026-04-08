# Multi-Cloud Resource Manager

A unified multi-cloud resource management solution built on the Claude Agent Skills specification. Seamlessly manage resources across AWS, Azure, Alibaba Cloud, Tencent Cloud, Huawei Cloud, and more — all within Claude Code or OpenClaw.

## Overview

Multi-Cloud Resource Manager provides centralized control over your cloud infrastructure through intelligent Agent Skills. It automates resource inventory, quota monitoring, and security scanning across multiple cloud providers.

## Core Capabilities

| Capability | Description |
|------------|-------------|
| **Resource Inventory** | Automated discovery and archival of cloud resource lists across all supported providers |
| **Quota Monitoring** | Real-time tracking of resource quotas and usage limits with proactive alerts |
| **Security Scanning** | Detection of high-risk resources: open ports, public access exposure, expired credentials, etc. |
| **Multi-Provider Support** | Unified interface for AWS, Azure, Alibaba Cloud, Tencent Cloud, and Huawei Cloud |

## Supported Cloud Providers

- **AWS** - Amazon Web Services
- **Azure** - Microsoft Azure
- **Alibaba Cloud** - 阿里云
- **Tencent Cloud** - 腾讯云
- **Huawei Cloud** - 华为云

## Quick Start

### Prerequisites

- Claude Code or OpenClaw installed
- Cloud provider credentials configured (following least-privilege principles)

### Installation

1. Clone this repository
   ```bash
   git clone https://github.com/your-org/multi-cloud-resource-manager.git
   cd multi-cloud-resource-manager
   ```

2. Install the Agent Skills
   ```bash
   # For Claude Code
   cp -r skills/* ~/.claude/skills/

   # For OpenClaw
   cp -r skills/* ~/.openclaw/skills/
   ```

3. Configure cloud provider credentials via environment variables or your preferred secret manager

4. Start managing your multi-cloud resources
   ```
   /cloud-inventory      # Generate resource inventory
   /quota-check          # Check quota usage across providers
   /security-scan        # Scan for high-risk resources
   ```

## Available Skills

| Skill | Command | Description |
|-------|---------|-------------|
| Cloud Inventory | `/cloud-inventory` | Discover and archive all cloud resources |
| Quota Monitor | `/quota-check` | Check resource quotas and limits |
| Security Scanner | `/security-scan` | Identify high-risk configurations |
| Cost Analyzer | `/cost-analyze` | Analyze resource costs and optimization opportunities |

## Security Best Practices

> **Warning: Security First Approach**

- **Never store plaintext credentials** - Use environment variables or secret managers
- **Encrypt API keys** - Store keys using cloud KMS or HashiCorp Vault
- **Least privilege access** - All skills operate with minimal required permissions
- **Audit logging** - All resource operations are logged for audit purposes
- **No data retention** - Resource data is processed locally, not sent to external servers

### Recommended Credential Setup

```bash
# AWS
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"

# Azure
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"

# Alibaba Cloud
export ALICLOUD_ACCESS_KEY="your-access-key"
export ALICLOUD_SECRET_KEY="your-secret-key"

# Tencent Cloud
export TENCENTCLOUD_SECRET_ID="your-secret-id"
export TENCENTCLOUD_SECRET_KEY="your-secret-key"

# Huawei Cloud
export HWCLOUD_ACCESS_KEY="your-access-key"
export HWCLOUD_SECRET_KEY="your-secret-key"
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Agent Interface                        │
│              (Claude Code / OpenClaw)                   │
└─────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────┐
│              Multi-Cloud Resource Manager               │
│  ┌──────────────┬──────────────┬─────────────────────┐  │
│  │   Inventory  │   Quota      │   Security Scan     │  │
│  │   Manager    │   Monitor    │   Engine            │  │
│  └──────────────┴──────────────┴─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐       ┌────▼────┐       ┌────▼────┐
   │  AWS    │       │  Azure  │       │ Alibaba │
   └─────────┘       └─────────┘       └─────────┘
   ┌─────────┐       ┌─────────┐
   │ Tencent │       │ Huawei  │
   └─────────┘       └─────────┘
```

## Documentation

- [Getting Started Guide](./docs/GETTING_STARTED.md)
- [Cloud Provider Setup](./docs/PROVIDER_SETUP.md)
- [Security Scan Rules](./docs/SECURITY_RULES.md)
- [API Reference](./docs/API_REFERENCE.md)
- [Contributing Guide](./CONTRIBUTING.md)

## High-Risk Resources Detection

The security scanner identifies the following risk patterns:

| Risk Type | Severity | Description |
|-----------|----------|-------------|
| Open Security Groups | Critical | Security groups allowing 0.0.0.0/0 on sensitive ports |
| Public S3 Buckets | Critical | S3 buckets with public read/write access |
| Exposed Databases | High | Databases accessible from the internet |
| Expired Credentials | High | IAM keys not rotated within 90 days |
| Overprivileged Roles | Medium | Roles with wildcard (*) permissions |
| Unencrypted Storage | Medium | Volumes or buckets without encryption |

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](./CONTRIBUTING.md) for details.

### Areas for Contribution

- Additional cloud provider support
- New security scanning rules
- Cost optimization recommendations
- Multi-region deployment guides

## License

This project is licensed under the [MIT License](./LICENSE).

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/multi-cloud-resource-manager/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/multi-cloud-resource-manager/discussions)

---

**Secure Your Multi-Cloud Infrastructure with Confidence**

Built with the [Claude Agent Skills Specification](https://docs.anthropic.com/)
