# Multi-Cloud Resource Manager

A unified Claude Code Skill suite for multi-cloud resource management. Automate resource inventory, security scanning, and compliance checking across **Huawei Cloud**, **Alibaba Cloud (Aliyun)**, and **AWS** with concurrent scanning support.

## Overview

Multi-Cloud Resource Manager provides comprehensive resource scanning capabilities through Claude Code Skills. It supports **multi-region concurrent scanning** across multiple cloud providers with a unified interface, configurable rules, and generates actionable reports for resource optimization.

### Key Features

- **Multi-Cloud Support**: Huawei Cloud, Alibaba Cloud (Aliyun), and AWS
- **Concurrent Multi-Region Scanning**: Scan up to 5 regions simultaneously for 78% time savings
- **Security-First Credential Handling**: Interactive input prevents credential exposure in shell history
- **Comprehensive Resource Coverage**: VPC, ECS/EC2, OBS/OSS/S3, EIP, Security Groups
- **YAML-Based Rule Engine**: Customizable compliance rules across all clouds
- **Multiple Report Formats**: JSON for automation, Markdown for human review
- **Unified Service Mapping**: Compare resources across cloud providers

## Supported Cloud Providers

| Cloud Provider | CLI Tool | Skill Name | Status |
|----------------|----------|------------|--------|
| **Huawei Cloud** | hcloud (KooCLI) | `huaweicloud-resource-manager` | Available |
| **Alibaba Cloud** | aliyun | `aliyun-resource-manager` | Available |
| **AWS** | aws | `aws-resource-manager` | Available |

## Service Mapping Across Clouds

| Resource Type | Huawei Cloud | Alibaba Cloud (Aliyun) | AWS |
|---------------|--------------|------------------------|-----|
| **Compute** | ECS | ECS | EC2 |
| **Network** | VPC | VPC | VPC |
| **Storage** | OBS | OSS | S3 |
| **Elastic IP** | EIP | EIP | Elastic IP |
| **Security Group** | Security Group | Security Group | Security Group |
| **Monitoring** | CES | CloudMonitor (CMS) | CloudWatch |
| **Subnet** | Subnet | VSwitch | Subnet |
| **Network Interface** | NIC | ENI | ENI |

## Implemented Capabilities

| Capability | Huawei Cloud | Aliyun | AWS | Description |
|------------|--------------|--------|-----|-------------|
| **VPC Inventory** | ✅ | ✅ | ✅ | Enumerate VPCs and analyze usage across regions |
| **Security Scanning** | ✅ | ✅ | ✅ | Detect high-risk security group configurations |
| **Object Storage Scanning** | ✅ (OBS) | ✅ (OSS) | ✅ (S3) | Identify publicly accessible buckets |
| **Compute Monitoring** | ✅ (ECS) | ✅ (ECS) | ✅ (EC2) | Find low-utilization instances and naming violations |
| **EIP Scanning** | ✅ | ✅ | ✅ | Detect unattached Elastic IPs |
| **Rule Engine** | ✅ | ✅ | ✅ | YAML-based customizable compliance rules |
| **Multi-Region** | ✅ | ✅ | ✅ | Support scanning all regions |
| **Concurrent Scanning** | ✅ | ✅ | ✅ | Parallel region scanning with configurable workers |

## Supported Regions

### Huawei Cloud
- cn-north-4 (Beijing), cn-north-1 (Beijing)
- cn-south-1 (Guangzhou), cn-south-4
- cn-east-2 (Shanghai), cn-east-3 (Shanghai)
- cn-southwest-2 (Guiyang)
- ap-southeast-1 (Hong Kong), ap-southeast-2 (Bangkok), ap-southeast-3 (Singapore)
- eu-west-101 (Amsterdam), af-south-1 (Johannesburg)

### Alibaba Cloud (Aliyun)
- cn-hangzhou (Hangzhou), cn-shanghai (Shanghai)
- cn-beijing (Beijing), cn-shenzhen (Shenzhen)
- cn-qingdao (Qingdao), cn-zhangjiakou (Zhangjiakou)
- cn-hongkong (Hong Kong)
- ap-southeast-1 (Singapore), ap-southeast-2 (Sydney)
- ap-northeast-1 (Tokyo)
- us-west-1 (Silicon Valley), us-east-1 (Virginia)
- eu-central-1 (Frankfurt)

### AWS
- us-east-1 (N. Virginia), us-east-2 (Ohio)
- us-west-1 (N. California), us-west-2 (Oregon)
- eu-west-1 (Ireland), eu-west-2 (London), eu-central-1 (Frankfurt)
- ap-southeast-1 (Singapore), ap-southeast-2 (Sydney)
- ap-northeast-1 (Tokyo), ap-south-1 (Mumbai)
- sa-east-1 (Sao Paulo)

## Quick Start

### Prerequisites

- Claude Code installed and configured
- Python 3.8+
- At least one cloud provider CLI installed:
  - Huawei Cloud: hcloud (KooCLI)
  - Alibaba Cloud: aliyun
  - AWS: aws

### Important: Use Read-Only Account with Minimum Permissions

**⚠️ SECURITY WARNING ⚠️**

This tool **MUST** use **read-only accounts** with minimum necessary permissions. **NEVER** use accounts with write/delete permissions:

| Permission Level | Recommended | Risk Level | Description |
|------------------|-------------|------------|-------------|
| **Read-Only** | ✅ **REQUIRED** | Low | Can only view resources, no modification risk |
| **Read-Write** | ❌ **FORBIDDEN** | Critical | Can modify/delete resources, high operational risk |

**Why Read-Only Accounts?**
- **Operational Safety**: Prevents accidental resource modification or deletion
- **Security**: Even if AK/SK is leaked, attackers cannot damage your infrastructure
- **Compliance**: Meets security audit requirements for scanning tools
- **Least Privilege**: Follows security best practice of minimum necessary access

**Dangers of Using Write-Enabled Accounts:**
- Accidental resource deletion during scanning
- Malicious resource manipulation if credentials are compromised
- Compliance violations from excessive permissions
- Operational disasters from misconfigured automation

### Installation

1. **Clone this repository**
   ```bash
   git clone https://github.com/MahaoAlex/multi-cloud-resource-manager.git
   cd multi-cloud-resource-manager
   ```

2. **Install Cloud Provider CLIs**

   **Huawei Cloud (hcloud):**
   ```bash
   curl -LO https://ap-southeast-3-hwcloudcli.obs.ap-southeast-3.myhuaweicloud.com/cli/latest/huaweicloud-cli-linux-amd64.tar.gz
   tar -xzf huaweicloud-cli-linux-amd64.tar.gz
   sudo mv hcloud /usr/local/bin/
   # Note: hcloud doesn't support --version, use --help
   hcloud --help > /dev/null 2>&1 && echo "hcloud installed"
   ```

   **Alibaba Cloud (aliyun):**
   ```bash
   curl -O https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz
   tar -xzf aliyun-cli-linux-latest-amd64.tgz
   sudo mv aliyun /usr/local/bin/
   aliyun --version
   ```

   **AWS:**
   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip
   sudo ./aws/install
   aws --version
   ```

3. **Install the Skills**
   ```bash
   # Create skills directory if not exists
   mkdir -p ~/.claude/skills
   
   # Copy Huawei Cloud skills
   cp -r skills/huaweicloud-core/proxy-injection ~/.claude/skills/
   cp -r skills/huaweicloud-core/auth-manager ~/.claude/skills/
   cp -r skills/huaweicloud-resource-manager ~/.claude/skills/
   
   # Copy Alibaba Cloud skills
   cp -r skills/aliyun-resource-manager ~/.claude/skills/
   
   # Copy AWS skills
   cp -r skills/aws-resource-manager ~/.claude/skills/
   
   # Verify installation
   ls -la ~/.claude/skills/
   ```

4. **Restart Claude Code**
   ```bash
   exit
   claude
   ```

5. **Configure credentials for your cloud provider(s)**

   **Huawei Cloud (Secure Method):**
   ```
   Configure Huawei Cloud authentication
   ```
   
   **Alibaba Cloud:**
   ```bash
   export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
   export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"
   export ALIYUN_REGIONS="cn-hangzhou,cn-shanghai"
   ```
   
   **AWS:**
   ```bash
   export AWS_ACCESS_KEY_ID="your-access-key-id"
   export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
   export AWS_REGIONS="us-east-1,us-west-2"
   ```

6. **Start scanning**
   
   **Huawei Cloud:**
   ```
   Execute complete Huawei Cloud resource scan
   ```
   
   **Alibaba Cloud:**
   ```
   /aliyun-resource-manager full_scan --regions=["cn-hangzhou","cn-shanghai"]
   ```
   
   **AWS:**
   ```
   /aws-resource-manager full_scan --regions=["us-east-1","us-west-2"]
   ```

## Available Skills by Cloud Provider

### Huawei Cloud Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Proxy Injection** | `Configure Huawei Cloud proxy` | Configure HTTP/HTTPS proxy for hcloud CLI |
| **Auth Manager** | `Configure Huawei Cloud authentication` | Interactive multi-region authentication |
| **Resource Scanner** | `/huaweicloud-scan full_scan` | Full resource scan with concurrent support |
| **VPC Inventory** | `Scan Huawei Cloud VPC resources` | Enumerate and analyze VPC usage |
| **Security Scanner** | `Scan Huawei Cloud security risks` | Detect high-risk security groups |
| **OBS Scanner** | `Check Huawei Cloud OBS public access` | Identify public OBS buckets |
| **ECS Monitor** | `Check Huawei Cloud ECS resource optimization` | Check CPU and naming compliance |
| **EIP Scanner** | `Scan Huawei Cloud unattached EIPs` | Find unattached Elastic IPs |

### Alibaba Cloud Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Resource Scanner** | `/aliyun-resource-manager full_scan` | Full resource scan across all categories |
| **VPC Inventory** | `/aliyun-resource-manager scan_vpcs` | Enumerate VPCs across regions |
| **Security Scanner** | `/aliyun-resource-manager scan_security` | Scan security group configurations |
| **OSS Scanner** | `/aliyun-resource-manager scan_oss` | Detect public OSS buckets |
| **ECS Monitor** | `/aliyun-resource-manager scan_ecs` | Monitor ECS instances |
| **EIP Scanner** | `/aliyun-resource-manager scan_eips` | Find unattached EIPs |

### AWS Skills

| Skill | Command | Description |
|-------|---------|-------------|
| **Resource Scanner** | `/aws-resource-manager full_scan` | Full resource scan across all categories |
| **VPC Inventory** | `/aws-resource-manager scan_vpcs` | Enumerate VPCs across regions |
| **Security Scanner** | `/aws-resource-manager scan_security` | Scan security group configurations |
| **S3 Scanner** | `/aws-resource-manager scan_s3` | Detect public S3 buckets |
| **EC2 Monitor** | `/aws-resource-manager scan_ec2` | Monitor EC2 instances |
| **EIP Scanner** | `/aws-resource-manager scan_eips` | Find unattached Elastic IPs |

## Concurrent Scanning

### Performance Optimization

All cloud providers support concurrent scanning of multiple regions:

| Scan Mode | Workers | Time for 5 Regions | Time Saved |
|-----------|---------|-------------------|------------|
| Serial | 1 | ~200 seconds | - |
| Low Concurrent | 2 | ~100 seconds | 50% |
| Default | 5 | ~45 seconds | 78% |

### Usage Examples

**Huawei Cloud:**
```
/huaweicloud-scan full_scan --regions=all --max_workers=3
```

**Alibaba Cloud:**
```
/aliyun-resource-manager full_scan --regions=["cn-hangzhou","cn-shanghai"] --max_workers=3
```

**AWS:**
```
/aws-resource-manager full_scan --regions=["us-east-1","us-west-2"] --max_workers=3
```

### How It Works

- **ThreadPoolExecutor**: Each region scanned by independent worker thread
- **Staggered Start**: 0.5-1.5s random delay per worker prevents API rate limiting
- **Read-Only Safety**: All scan operations are read-only, concurrent execution is safe
- **Max Workers**: Limited to 5 to prevent API throttling

## Security Scanning

The security scanner identifies the following risk patterns across all cloud providers:

| Risk Type | Severity | Description | Affected Services |
|-----------|----------|-------------|-------------------|
| Open SSH Port | Critical | Port 22 open to 0.0.0.0/0 | Security Groups |
| Open RDP Port | Critical | Port 3389 open to internet | Security Groups |
| Open Port 33/44 | Critical | Ports commonly abused | Security Groups |
| Public Object Storage | High | Bucket with public-read ACL | OBS/OSS/S3 |
| Public Object | High | Object with public access | OBS/OSS/S3 |
| Unattached EIP | Medium | Elastic IP not bound to resource | EIP |
| Low CPU Utilization | Info | CPU < 10% for 24 hours | ECS/EC2 |

## Naming Convention

Compute instances (ECS/EC2) must contain at least 6 consecutive digits (employee ID format):

- **Valid**: `user-00123456-web`, `test123456vm`, `00123456`
- **Invalid**: `web-server`, `test12345`, `dev-12345`

This convention helps with resource ownership identification and cost allocation tracking across all clouds.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Claude Code Interface                        │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│              Multi-Cloud Resource Manager                        │
│                   (Unified Controller)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼────────┐   ┌────────▼────────┐   ┌───────▼────────┐
│  Huawei Cloud  │   │  Alibaba Cloud  │   │      AWS       │
│   Resources    │   │    Resources    │   │   Resources    │
│                │   │                 │   │                │
│ ┌────────────┐ │   │ ┌────────────┐  │   │ ┌────────────┐ │
│ │   VPC      │ │   │ │   VPC      │  │   │ │   VPC      │ │
│ │   ECS      │ │   │ │   ECS      │  │   │ │   EC2      │ │
│ │   OBS      │ │   │ │   OSS      │  │   │ │   S3       │ │
│ │   EIP      │ │   │ │   EIP      │  │   │ │   EIP      │ │
│ └────────────┘ │   │ └────────────┘  │   │ └────────────┘ │
└────────────────┘   └─────────────────┘   └────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
    ┌─────────▼────────┐ ┌────▼────────┐ ┌────▼────────┐
    │  Region 1        │ │ Region 2    │ │ Region 3    │
    │  (Worker 1)      │ │ (Worker 2)  │ │ (Worker 3)  │
    │  [Concurrent]    │ │[Concurrent] │ │[Concurrent] │
    └──────────────────┘ └─────────────┘ └─────────────┘
```

## Report Output

### Directory Structure

```
reports/
└── 2026-04-08/
    ├── huaweicloud_manual_14-30-00.json
    ├── huaweicloud_manual_14-30-00.md
    ├── aliyun_manual_14-35-00.json
    ├── aliyun_manual_14-35-00.md
    ├── aws_manual_14-40-00.json
    └── aws_manual_14-40-00.md
```

### Report Formats

- **Manual scans**: Generate both JSON and Markdown reports
- **Scheduled scans**: Generate JSON reports only (lightweight)
- **Retention**: Automatically clean reports older than 7 days

### Sample Cross-Cloud Report Structure

```json
{
  "cloud_provider": "huaweicloud",
  "regions": ["cn-north-4", "cn-south-1"],
  "duration_seconds": 52,
  "summary": {
    "vpcs": 16,
    "unused_vpcs": 3,
    "security_issues": 4,
    "public_storage_buckets": 2,
    "low_utilization_compute": 4,
    "unattached_eips": 3
  },
  "summary_by_region": {
    "cn-north-4": {
      "vpcs": 8,
      "security_issues": 3,
      "storage_issues": 2,
      "compute_issues": 5,
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

### Environment Variables by Cloud Provider

#### Huawei Cloud

| Variable | Description | Required |
|----------|-------------|----------|
| `HWCLOUD_ACCESS_KEY` | Access Key ID | Yes |
| `HWCLOUD_SECRET_KEY` | Secret Access Key | Yes |
| `HWCLOUD_REGIONS` | Comma-separated regions or 'all' | Yes |
| `HWCLOUD_PROJECT_ID` | Project ID for IAM sub-users | No |

#### Alibaba Cloud

| Variable | Description | Required |
|----------|-------------|----------|
| `ALIYUN_ACCESS_KEY_ID` | Access Key ID | Yes |
| `ALIYUN_ACCESS_KEY_SECRET` | Access Key Secret | Yes |
| `ALIYUN_REGIONS` | Comma-separated regions or 'all' | Yes |
| `OSS_CHECK_OBJECTS` | Enable object-level scanning | No (default: true) |

#### AWS

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_ACCESS_KEY_ID` | Access Key ID | Yes |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key | Yes |
| `AWS_REGIONS` | Comma-separated regions or 'all' | Yes |
| `S3_CHECK_OBJECTS` | Enable object-level scanning | No (default: false) |

### Proxy Configuration (All Clouds)

| Variable | Description |
|----------|-------------|
| `HTTP_PROXY` | HTTP proxy URL |
| `HTTPS_PROXY` | HTTPS proxy URL |
| `NO_PROXY` | Comma-separated no-proxy hosts |

### Secure Credential Configuration

**Recommended: Interactive Configuration (Huawei Cloud)**
```
Configure Huawei Cloud authentication
```

**⚠️ Security Warning:**
```bash
# DON'T DO THIS - Credentials will be saved in shell history!
export HWCLOUD_ACCESS_KEY="your-secret-key"

# If you must use direct export, clear history immediately
history -c
```

### Custom Rules

Create custom rules in `./rules/` directory. Rules work across all cloud providers:

```yaml
# rules/custom-rules.yaml
rules:
  - id: "compute-owner-tag-check"
    name: "Compute Instance Owner Tag Required"
    resource: "ecs"  # Works for ECS/EC2
    condition: "tags !contains ['Owner']"
    severity: "warning"
    description: "Compute instances must have an Owner tag"

  - id: "vpc-environment-tag"
    name: "VPC Environment Tag"
    resource: "vpc"
    condition: "name !~ /-(dev|prod|test|staging)-/"
    severity: "info"
    description: "VPC names should include environment identifier"
```

## Scheduling

### Cron (All Cloud Providers)

Configure hourly scans:

```bash
# Huawei Cloud
0 * * * * source /path/to/huaweicloud-env.sh && claude "/huaweicloud-scan --mode=scheduled --regions=all --max_workers=3"

# Alibaba Cloud
0 * * * * source /path/to/aliyun-env.sh && claude "/aliyun-resource-manager full_scan --regions=all --max_workers=3"

# AWS
0 * * * * source /path/to/aws-env.sh && claude "/aws-resource-manager full_scan --regions=all --max_workers=3"
```

## Documentation

- **[Huawei Cloud Complete Guide](./docs/huaweicloud-complete-guide.md)** (中文) - 华为云完整使用指南
- **[Alibaba Cloud Complete Guide](./docs/aliyun-complete-guide.md)** (中文) - 阿里云完整使用指南  
- **[AWS Complete Guide](./docs/aws-complete-guide.md)** (中文) - AWS 完整使用指南
- **[CLAUDE.md](./CLAUDE.md)** - Development guidelines and code specifications
- **[CLAUDE.md](./CLAUDE.md)** - Development guidelines and code specifications

## Required IAM Permissions & How to Apply

This section details the **minimum read-only permissions** required for each cloud provider and how to apply through the web console.

### Permission Overview

| Cloud Provider | Account Type | Access Mode | Permission Level |
|----------------|--------------|-------------|------------------|
| **Huawei Cloud** | IAM User | Programmatic Access | Read-Only |
| **Alibaba Cloud** | RAM User | Programmatic Access | Read-Only |
| **AWS** | IAM User | Programmatic Access | Read-Only |

---

### Huawei Cloud Permissions

#### Required Permissions List

| Service | Permission | Purpose |
|---------|------------|---------|
| **VPC** | `vpc:vpcs:list` | List VPCs |
| | `vpc:subnets:list` | List subnets |
| | `vpc:securityGroups:list` | List security groups |
| | `vpc:securityGroupRules:list` | List security group rules |
| **ECS** | `ecs:servers:list` | List ECS instances |
| | `ecs:serverVolumeAttachments:list` | List attached volumes |
| | `ecs:serverInterfaces:list` | List network interfaces |
| **OBS** | `obs:bucket:list` | List OBS buckets |
| | `obs:bucket:getBucketAcl` | Get bucket ACL |
| | `obs:bucket:getBucketPolicy` | Get bucket policy |
| **EIP** | `vpc:publicIps:list` | List Elastic IPs |
| **CES** | `ces:metrics:list` | List metrics |
| | `ces:data:list` | Get metric data |
| **CCE** | `cce:clusters:list` | List CCE clusters |
| | `cce:nodes:list` | List CCE nodes |

#### How to Apply (Huawei Cloud Console)

**Step 1: Create IAM User**

1. Login to [Huawei Cloud IAM Console](https://console.huaweicloud.com/iam/)
2. In the left navigation menu, click **Users**
3. Click **Create User** button
4. Configure user details:
   - **User Name**: `resource-scanner` (or your preferred name)
   - **Credential Type**: Select **Programmatic access** only (do not enable console access)
   - **Description**: `Read-only account for resource scanning tool`
5. Click **Next**

**Step 2: Assign Permissions**

Option A - Use System Policy (Quick Setup):
1. On the permissions page, switch to **Attach policies by policy**
2. In the search box, type: `Tenant Guest`
3. Check the box for **Tenant Guest** policy (provides read-only access to most services)
4. Click **Next**

Option B - Use Custom Policy (Fine-grained Control):
1. Click **Create Policy** (if you don't have a custom policy yet)
2. Select **JSON** tab and paste the following policy:

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
        "obs:bucket:getBucketPolicy",
        "vpc:publicIps:list",
        "ces:metrics:list",
        "ces:data:list",
        "cce:clusters:list",
        "cce:nodes:list"
      ],
      "Resource": ["*"]
    }
  ]
}
```

3. Click **Check** to validate the policy
4. Enter policy name: `ResourceScannerReadOnly`
5. Click **OK** to create the policy
6. Return to user creation and attach this custom policy

**Step 3: Complete User Creation**

1. Review the user configuration
2. Click **Create User**
3. **IMPORTANT**: On the success page, you will see:
   - **Access Key ID** (e.g., `HWI...`)
   - **Secret Access Key** (click **Download CSV** or copy immediately)
4. **Save these credentials securely** - the Secret Key will NOT be shown again
5. Store in a password manager or secure location

**Step 4: (Optional) Assign to Multiple Projects**

If you need to scan resources across multiple projects:

1. Go to **Users** > Click on the user you created
2. Click **Modify** in the **Project** section
3. Select all projects that need to be scanned
4. Ensure the read-only policy is applied to each project

---

### Alibaba Cloud Permissions

#### Required Permissions List

| Service | RAM Policy Name | Purpose |
|---------|-----------------|---------|
| **ECS** | `AliyunECSReadOnlyAccess` | Full ECS read access |
| **VPC** | `AliyunVPCReadOnlyAccess` | Full VPC read access |
| **OSS** | `AliyunOSSReadOnlyAccess` | Full OSS read access |
| **EIP** | `AliyunEIPReadOnlyAccess` | Full EIP read access |
| **CMS** | `AliyunCloudMonitorReadOnlyAccess` | CloudMonitor read access |
| **RDS** | `AliyunRDSReadOnlyAccess` | RDS read access (optional) |
| **SLB** | `AliyunSLBReadOnlyAccess` | SLB read access (optional) |

#### Custom RAM Policy (JSON)

If you need fine-grained control instead of system policies:

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:Describe*",
        "vpc:Describe*",
        "oss:GetBucket*",
        "oss:ListBucket*",
        "eip:Describe*",
        "cms:Describe*",
        "cms:Query*"
      ],
      "Resource": "*"
    }
  ]
}
```

#### How to Apply (Alibaba Cloud Console)

**Step 1: Create RAM User**

1. Login to [Alibaba Cloud RAM Console](https://ram.console.aliyun.com/)
2. In the left navigation menu, click **Users** under **Identities**
3. Click **Create User** button
4. Configure user details:
   - **User Account Information**:
     - **Logon Name**: `resource-scanner`
     - **Display Name**: `Resource Scanner`
   - **Access Mode**: Check **OpenAPI Access** (Programmatic access)
   - **Console Access**: Do NOT enable (keep unchecked for security)
5. Click **OK**

**Step 2: Assign Permissions**

Option A - Use System Policies (Quick Setup):

1. On the success page, click **Add Permissions** (or go to Users > click user name > Permissions > Add Permissions)
2. Select **System Policy** tab
3. In the search box, search for and select these policies one by one:
   | Policy Name | Purpose |
   |-------------|---------|
   | `AliyunECSReadOnlyAccess` | ECS read access |
   | `AliyunVPCReadOnlyAccess` | VPC read access |
   | `AliyunOSSReadOnlyAccess` | OSS read access |
   | `AliyunEIPReadOnlyAccess` | Elastic IP read access |
   | `AliyunCloudMonitorReadOnlyAccess` | CloudMonitor metrics |
4. Click **OK** to confirm

Option B - Use Custom Policy:

1. Before adding permissions, go to **Policies** > **Create Policy**
2. Select **Script** configuration mode
3. Paste the custom JSON policy shown above
4. Enter policy name: `ResourceScannerReadOnly`
5. Click **OK**
6. Return to user permissions and attach this custom policy

**Step 3: Create AccessKey**

1. Go to **Users** > Click on `resource-scanner` user name
2. Click **Create AccessKey** in the **User AccessKey Information** section
3. **Security Verification**: Complete SMS or email verification as required
4. **IMPORTANT**: On the success page, you will see:
   - **AccessKey ID** (e.g., `LTAI...`)
   - **AccessKey Secret** (click **Copy** or **Download CSV File**)
5. **Save these credentials immediately** - the Secret will NOT be shown again
6. Store securely in a password manager or secure vault

**Step 4: (Optional) Configure MFA for Account Security**

Even for read-only accounts, consider enabling MFA:

1. In user details page, click **Enable Virtual MFA Device**
2. Follow the prompts to bind an MFA device
3. Note: MFA may affect programmatic access in some scenarios

---

### AWS Permissions

#### Required Permissions List

| Service | Permission | Purpose |
|---------|------------|---------|
| **EC2** | `ec2:DescribeInstances` | List EC2 instances |
| | `ec2:DescribeVpcs` | List VPCs |
| | `ec2:DescribeSubnets` | List subnets |
| | `ec2:DescribeSecurityGroups` | List security groups |
| | `ec2:DescribeSecurityGroupRules` | List security group rules |
| | `ec2:DescribeAddresses` | List Elastic IPs |
| | `ec2:DescribeNetworkInterfaces` | List ENIs |
| **S3** | `s3:GetBucketAcl` | Get bucket ACL |
| | `s3:GetBucketPolicy` | Get bucket policy |
| | `s3:GetBucketPublicAccessBlock` | Check public access settings |
| | `s3:ListAllMyBuckets` | List all buckets |
| | `s3:ListBucket` | List bucket contents |
| **CloudWatch** | `cloudwatch:GetMetricData` | Get metrics |
| | `cloudwatch:ListMetrics` | List metrics |

#### IAM Policy Document (JSON)

If creating a custom policy, use this JSON:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "EC2ReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVpcs",
        "ec2:DescribeSubnets",
        "ec2:DescribeSecurityGroups",
        "ec2:DescribeSecurityGroupRules",
        "ec2:DescribeAddresses",
        "ec2:DescribeNetworkInterfaces"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3ReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketAcl",
        "s3:GetBucketPolicy",
        "s3:GetBucketPublicAccessBlock",
        "s3:ListAllMyBuckets",
        "s3:ListBucket"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchReadOnly",
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricData",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

#### How to Apply (AWS Console)

**Step 1: Create IAM User**

1. Login to [AWS IAM Console](https://console.aws.amazon.com/iam/)
2. In the left navigation menu, click **Users**
3. Click **Add users** button
4. Configure user details:
   - **User name**: `resource-scanner`
   - **Select AWS credential type**: Check **Access key - Programmatic access**
   - Do NOT enable **Password - AWS Management Console access**
5. Click **Next: Permissions**

**Step 2: Assign Permissions**

Option A - Use AWS Managed Policies (Quick Setup):

1. On the permissions page, select **Attach existing policies directly**
2. In the search filter, search for and check these policies:
   | Policy Name | Purpose |
   |-------------|---------|
   | `AmazonEC2ReadOnlyAccess` | EC2 read access |
   | `AmazonS3ReadOnlyAccess` | S3 read access |
   | `CloudWatchReadOnlyAccess` | CloudWatch metrics |
3. Ensure all three policies are checked
4. Click **Next: Tags**

Option B - Use Custom Policy (Fine-grained Control):

1. Before creating the user, go to **Policies** > **Create policy**
2. Click **JSON** tab
3. Paste the custom JSON policy shown above
4. Click **Review policy**
5. Enter policy name: `ResourceScannerReadOnly`
6. Click **Create policy**
7. Return to user creation and attach this custom policy

**Step 3: Add Tags (Optional)**

1. Add metadata tags for organization:
   - Key: `Project`, Value: `ResourceScanner`
   - Key: `Environment`, Value: `Production`
2. Click **Next: Review**

**Step 4: Review and Create**

1. Review the user configuration:
   - User name: `resource-scanner`
   - AWS access type: `Programmatic access`
   - Permissions: The read-only policies selected
2. Click **Create user**

**Step 5: Save Credentials**

1. **IMPORTANT**: On the success page, you will see:
   - **Access key ID** (e.g., `AKIA...`)
   - **Secret access key** (click **Show** to reveal)
2. **Save these credentials immediately** - the Secret Key will NOT be shown again
3. Options to save:
   - Click **Download .csv** to download a CSV file
   - Click **Copy** to copy to clipboard
   - Store in a secure password manager
4. Click **Close**

**Step 6: (Optional) Configure Additional Security**

1. Return to the user list and click on `resource-scanner`
2. Under **Security credentials** tab:
   - **Sign-in credentials**: Ensure console access is disabled
   - **Assigned MFA device**: Consider enabling MFA for extra security (may affect some programmatic scenarios)
   - **Access keys**: You can create a second access key for rotation purposes

**Step 7: (Optional) Cross-Account Access**

If scanning multiple AWS accounts:

1. In the target account, create a role instead of a user
2. Use the following trust relationship policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::SCANNER_ACCOUNT_ID:root"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

3. Attach the same read-only permissions to this role
4. In the scanner account, grant the user permission to assume this role

---

## Security Best Practices

### Credential Security

- **Never** store plaintext credentials in command history
- Use interactive configuration methods when available
- Set environment variable file permissions to `600`
- Rotate credentials every 90 days
- **Use read-only accounts with minimum permissions - NEVER use write-enabled accounts**
- Use IAM/sub-accounts with minimal permissions

### Operational Security

- All scanning operations are **read-only**
- Delete operations require explicit human confirmation
- Resource data is processed locally
- No data is sent to external servers
- Reports contain metadata only, not sensitive credentials

## Troubleshooting

### Common Issues

**Issue**: `CLI not found` errors

**Solution**: Verify CLI installation:
```bash
# Huawei Cloud
hcloud --help > /dev/null 2>&1 && echo "hcloud OK"

# Alibaba Cloud
aliyun --version

# AWS
aws --version
```

**Issue**: Authentication failures

**Solution**: Check environment variables for your cloud provider:
```bash
# Huawei Cloud
echo "AK: ${HWCLOUD_ACCESS_KEY:0:4}****${HWCLOUD_ACCESS_KEY: -4}"

# Alibaba Cloud
echo "AK: ${ALIYUN_ACCESS_KEY_ID:0:4}****${ALIYUN_ACCESS_KEY_ID: -4}"

# AWS
echo "AK: ${AWS_ACCESS_KEY_ID:0:4}****${AWS_ACCESS_KEY_ID: -4}"
```

**Issue**: `Failed to parse JSON output` during concurrent scan

**Solution**: Reduce concurrent workers:
```
# Any cloud provider
full_scan --max_workers=2
```

For more troubleshooting, see the cloud-specific setup guides.

## Contributing

We welcome contributions! Areas for contribution:

- Additional cloud providers (Azure, GCP)
- New resource types (RDS, ELB, etc.)
- Cross-cloud comparison features
- Report format improvements
- Performance optimizations
- Documentation translations

## License

This project is licensed under the [MIT License](./LICENSE).

## Support

- **Issues**: [GitHub Issues](https://github.com/MahaoAlex/multi-cloud-resource-manager/issues)
- **Documentation**: See cloud-specific setup guides for detailed instructions

---

**Secure Your Multi-Cloud Infrastructure with Confidence**

Built with the [Claude Agent Skills Specification](https://docs.anthropic.com/)
