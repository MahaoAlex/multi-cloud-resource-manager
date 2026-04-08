# AWS资源管理工具配置指导

## 概述

本文档介绍如何配置和使用AWS资源管理工具（aws-resource-manager），用于扫描和管理Amazon Web Services资源。

## 前置要求

### 1. 安装AWS CLI

```bash
# 下载并安装AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 验证安装
aws --version
```

### 2. 配置AWS凭证

方式一：使用环境变量

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
```

方式二：使用aws configure配置

```bash
aws configure
# 按提示输入Access Key ID、Secret Access Key、默认Region和输出格式
```

方式三：使用IAM角色（推荐用于EC2实例）

如果在AWS EC2实例上运行，可以为实例附加IAM角色，无需配置凭证文件。

## 环境变量配置

### 必需环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `AWS_ACCESS_KEY_ID` | AWS Access Key ID | AKIAIOSFODNN7EXAMPLE |
| `AWS_SECRET_ACCESS_KEY` | AWS Secret Access Key | wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY |
| `AWS_REGIONS` | 扫描的Region列表，逗号分隔或使用'all' | us-east-1,us-west-2 |

### 可选环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `S3_CHECK_OBJECTS` | 是否检查S3对象级权限 | false |
| `AWS_DEFAULT_REGION` | 默认Region | us-east-1 |

## 配置示例

### 基础配置

```bash
# 设置凭证
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"

# 设置扫描区域（单个区域）
export AWS_REGIONS="us-east-1"

# 设置扫描区域（多个区域）
export AWS_REGIONS="us-east-1,us-west-2,eu-west-1"

# 扫描所有支持的区域
export AWS_REGIONS="all"
```

### 支持的Region列表

| Region ID | 区域名称 |
|-----------|----------|
| us-east-1 | 美国东部（弗吉尼亚北部） |
| us-east-2 | 美国东部（俄亥俄） |
| us-west-1 | 美国西部（加利福尼亚北部） |
| us-west-2 | 美国西部（俄勒冈） |
| eu-west-1 | 欧洲（爱尔兰） |
| eu-west-2 | 欧洲（伦敦） |
| eu-central-1 | 欧洲（法兰克福） |
| ap-southeast-1 | 亚太地区（新加坡） |
| ap-southeast-2 | 亚太地区（悉尼） |
| ap-northeast-1 | 亚太地区（东京） |
| ap-south-1 | 亚太地区（孟买） |
| sa-east-1 | 南美洲（圣保罗） |

## 使用方法

### 1. 完整扫描

```bash
/aws-resource-manager full_scan
```

带参数扫描：

```bash
/aws-resource-manager full_scan \
  --regions=["us-east-1","us-west-2"] \
  --scan_type="manual" \
  --output_dir="./reports"
```

### 2. 单独扫描VPC

```bash
/aws-resource-manager scan_vpcs --regions=["us-east-1"]
```

### 3. 扫描安全组

```bash
/aws-resource-manager scan_security --regions=["us-east-1"]
```

### 4. 扫描S3

```bash
/aws-resource-manager scan_s3 --regions=["us-east-1"]
```

注意：S3是全局服务，但bucket有地理位置属性。

### 5. 扫描EC2

```bash
/aws-resource-manager scan_ec2 \
  --regions=["us-east-1"] \
  --cpu_threshold=10 \
  --check_naming=true
```

### 6. 扫描EIP

```bash
/aws-resource-manager scan_eips --regions=["us-east-1"]
```

### 7. 列出所有规则

```bash
/aws-resource-manager list_rules
```

## 扫描结果

扫描报告将保存在 `./reports/YYYY-MM-DD/` 目录下：

- **手动扫描**：生成JSON和Markdown两种格式
- **定时扫描**：仅生成JSON格式

### 报告内容

报告包含以下信息：

1. **VPC分析**：未使用的VPC列表
2. **安全问题**：安全组开放端口配置（如22、3389等端口对0.0.0.0/0开放）
3. **S3问题**：公开访问的存储桶（ACL和Policy检查）
4. **EC2问题**：低CPU使用率（默认<10%）和命名规范违规
5. **EIP问题**：未绑定的弹性IP
6. **行动建议**：按严重级别排序的待办事项（Critical > High > Warning > Info）

## 自定义规则

### 创建自定义规则文件

创建文件 `./rules/custom-rules.yaml`：

```yaml
rules:
  - id: custom-ec2-cost-tag
    name: EC2 Instance Missing Cost Center Tag
    resource: ec2
    condition: 'tags !~ /CostCenter/'
    severity: warning
    description: EC2实例应包含CostCenter标签用于成本分摊

  - id: custom-s3-encryption
    name: S3 Bucket Without Encryption
    resource: s3_bucket
    condition: 'encryption = disabled'
    severity: high
    description: S3存储桶应启用服务器端加密
```

### 运行自定义规则

```bash
/aws-resource-manager run_custom_rule \
  --rule_file="./rules/custom-rules.yaml" \
  --resource_type="ec2"
```

## 内置规则说明

### 安全规则（security-rules.yaml）

| 规则ID | 检查内容 | 严重级别 |
|--------|----------|----------|
| sg-ssh-open-internet | SSH(22)端口对互联网开放 | critical |
| sg-rdp-open-internet | RDP(3389)端口对互联网开放 | critical |
| sg-mysql-open-internet | MySQL(3306)端口对互联网开放 | critical |
| sg-postgres-open-internet | PostgreSQL(5432)端口对互联网开放 | critical |
| sg-redis-open-internet | Redis(6379)端口对互联网开放 | critical |
| s3-public-read | S3存储桶公开读取 | high |
| s3-public-write | S3存储桶公开写入 | critical |

### 命名规范规则（naming-conventions.yaml）

| 规则ID | 检查内容 | 严重级别 |
|--------|----------|----------|
| ec2-naming-convention | EC2实例名应包含6位以上数字 | warning |
| vpc-naming-convention | VPC名应以环境前缀开头 | info |
| ec2-tag-owner | EC2实例应有Owner标签 | warning |

## 常见问题

### 1. CLI未找到

**问题**：`aws CLI not found`

**解决**：确保AWS CLI已安装并在PATH中

```bash
which aws
# 如果没有输出，重新安装并添加到PATH
```

### 2. 权限不足

**问题**：API调用返回权限错误

**解决**：确保IAM用户或角色具有足够的权限。建议附加以下AWS托管策略：

- `AmazonEC2ReadOnlyAccess` - EC2只读权限
- `AmazonVPCReadOnlyAccess` - VPC只读权限
- `AmazonS3ReadOnlyAccess` - S3只读权限
- `CloudWatchReadOnlyAccess` - CloudWatch只读权限

或者创建自定义策略：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "s3:GetBucket*",
        "s3:ListBucket*",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

### 3. Region配置错误

**问题**：无法获取某些Region的资源

**解决**：检查Region ID拼写，使用支持的Region列表中的值

### 4. S3扫描速度慢

**问题**：S3扫描耗时较长

**解决**：S3是全局服务，扫描所有bucket可能需要较长时间。建议：
- 按Region过滤bucket
- 关闭对象级扫描（默认已关闭）

## 服务对应关系

| AWS | 阿里云 | 华为云 |
|-----|--------|--------|
| VPC | VPC | VPC |
| EC2 | ECS | ECS |
| S3 | OSS | OBS |
| Elastic IP | EIP | EIP |
| Security Group | 安全组 | 安全组 |
| CloudWatch | CMS | CES |
| Subnet | VSwitch | Subnet |
| ENI | ENI | NIC |

## 最佳实践

### 1. IAM权限最小化

创建专用的IAM用户或角色用于资源扫描，仅授予只读权限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ResourceScanning",
      "Effect": "Allow",
      "Action": [
        "ec2:Describe*",
        "s3:Get*",
        "s3:List*",
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics"
      ],
      "Resource": "*"
    }
  ]
}
```

### 2. 定期扫描

建议设置定时任务进行定期扫描：

```bash
# 使用cron每天凌晨2点执行扫描
0 2 * * * cd /path/to/repo && /usr/local/bin/claude aws-resource-manager full_scan --scan_type="scheduled"
```

### 3. 报告保留策略

默认保留7天的报告，可通过`retention_days`参数调整：

```bash
/aws-resource-manager full_scan --retention_days=30
```

## 注意事项

1. **API调用频率**：AWS有API速率限制，工具已内置适当的延迟，但大量资源扫描可能需要较长时间
2. **费用**：工具本身免费，但CloudWatch API调用可能产生少量费用
3. **数据安全**：扫描结果保存在本地，不会上传到任何远程服务器
4. **跨区域扫描**：扫描多个Region会增加扫描时间

## 故障排除

### 启用调试模式

如果遇到问题，可以查看详细的日志输出：

```bash
export LOG_LEVEL=DEBUG
/aws-resource-manager full_scan
```

### 测试单个Region

先测试单个Region确保配置正确：

```bash
export AWS_REGIONS="us-east-1"
/aws-resource-manager scan_vpcs
```

## 更新日志

### v1.0.0

- 初始版本发布
- 支持VPC、安全组、S3、EC2、EIP扫描
- 支持多Region扫描
- 支持自定义规则
- 支持Public Access Block检测

## 获取帮助

如有问题，请查看：
1. 本文档的常见问题部分
2. 工具内置帮助：`/aws-resource-manager --help`
3. 项目GitHub Issues页面
