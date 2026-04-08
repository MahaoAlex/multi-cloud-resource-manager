# AWS 资源管理器使用指南

## 概述

AWS 资源管理器是一个 Claude Code Skill，用于统一管理和扫描 AWS 资源，提供 VPC 盘点、安全扫描、配额监控和多区域合规性检查功能。

### 功能特性

| 功能 | 描述 | 状态 |
|------|------|------|
| **VPC 盘点** | 枚举所有 VPC 并进行使用分析 | 已实现 |
| **安全扫描** | 检测高风险安全组配置 | 已实现 |
| **S3 扫描** | 识别公开可访问的存储桶 | 已实现 |
| **EC2 监控** | 发现低利用率实例和命名违规 | 已实现 |
| **EIP 扫描** | 检测未挂载的弹性 IP | 已实现 |
| **规则引擎** | 可配置的 YAML 合规规则 | 已实现 |
| **双层并发** | 区域级 + VPC 级并发扫描 | 已实现 |

## 一、环境准备

### 1.1 必要条件

- Claude Code 已安装并配置
- Python 3.8+
- AWS CLI 已安装
- AWS 账号及 Access Key

### 1.2 安装 AWS CLI

```bash
# 下载并安装 AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# 验证安装
aws --version

# 配置凭证
aws configure
```

### 1.3 获取 AWS 凭证

1. 登录 AWS 控制台
2. 进入 IAM -> 用户 -> 安全凭证
3. 创建新的 Access Key，保存 AK 和 SK

## 二、部署安装

### 2.1 下载项目

```bash
# 克隆仓库
git clone https://github.com/MahaoAlex/multi-cloud-resource-manager.git
cd multi-cloud-resource-manager
```

### 2.2 安装 Skills

```bash
# 创建 Claude Code skills 目录
mkdir -p ~/.claude/skills

# 复制 AWS Skill
cp -r skills/aws-resource-manager ~/.claude/skills/

# 验证安装
ls -la ~/.claude/skills/
```

### 2.3 目录结构

```
~/.claude/skills/
└── aws-resource-manager/
    ├── skill.yaml
    ├── main.py
    ├── tools/
    │   ├── vpc_inventory.py
    │   ├── vpc_analyzer.py
    │   ├── security_scanner.py
    │   ├── s3_scanner.py
    │   ├── ec2_monitor.py
    │   ├── eip_scanner.py
    │   ├── rule_engine.py
    │   └── report_generator.py
    └── rules/
        ├── naming-conventions.yaml
        └── security-rules.yaml
```

### 2.4 重启 Claude Code

```bash
exit
claude
```

## 三、快速开始

### 3.1 配置凭证

```bash
# 设置环境变量
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGIONS="us-east-1,us-west-2"
```

### 3.2 执行扫描

**完整扫描（双层并发）：**
```
/aws-resource-manager full_scan \
  --regions=["us-east-1","us-west-2"] \
  --max_workers=3 \
  --vpc_max_workers=3
```

**单独扫描 VPC：**
```
/aws-resource-manager scan_vpcs \
  --regions=["us-east-1"]
```

**安全扫描：**
```
/aws-resource-manager scan_security \
  --regions=["us-east-1"] \
  --check_ports=[22, 3389]
```

**S3 扫描：**
```
/aws-resource-manager scan_s3 \
  --regions=["us-east-1"]
```

**EC2 监控：**
```
/aws-resource-manager scan_ec2 \
  --regions=["us-east-1"] \
  --cpu_threshold=10 \
  --check_naming=true
```

## 四、双层并发扫描

### 4.1 并发架构

```
第一层：区域级别并发 (max_workers)
    ├── 区域 1 Worker (us-east-1)
    │       └── 第二层：VPC 级别并发 (vpc_max_workers)
    │               ├── VPC A Worker
    │               ├── VPC B Worker
    │               └── VPC C Worker
    ├── 区域 2 Worker (us-west-2)
    │       └── VPC D/E/F Workers
    └── 区域 3 Worker (eu-west-1)
            └── VPC G/H/I Workers
```

### 4.2 参数说明

| 参数 | 层级 | 默认 | 说明 |
|------|------|------|------|
| `max_workers` | 第一层 | 5 | 同时扫描几个区域（1-5）|
| `vpc_max_workers` | 第二层 | 3 | 每个区域内同时分析几个 VPC（1-5）|

### 4.3 性能对比

假设扫描 3 个区域，每个区域 10 个 VPC：

| 模式 | 预计时间 | 说明 |
|------|---------|------|
| 串行扫描 | ~600秒 | 逐个 VPC 分析 |
| 仅区域并发 | ~200秒 | 3 区域同时，但 VPC 串行 |
| **双层并发** | **~70秒** | **最优配置** |

### 4.4 使用建议

```bash
# 高并发（适合 VPC 多的场景）
aws-resource-manager full_scan --max_workers=5 --vpc_max_workers=5

# 低并发（API 限流时使用）
aws-resource-manager full_scan --max_workers=2 --vpc_max_workers=2

# 串行模式（调试使用）
aws-resource-manager full_scan --max_workers=1 --vpc_max_workers=1
```

## 五、配置参数

### 5.1 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `AWS_ACCESS_KEY_ID` | Access Key ID | 是 |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key | 是 |
| `AWS_REGIONS` | 区域列表或 'all' | 是 |
| `S3_CHECK_OBJECTS` | 检查 S3 对象级权限 | 否（默认 false）|

### 5.2 支持区域

| 区域 ID | 位置 | 状态 |
|---------|------|------|
| us-east-1 | 弗吉尼亚北部 | 可用 |
| us-east-2 | 俄亥俄 | 可用 |
| us-west-1 | 加利福尼亚北部 | 可用 |
| us-west-2 | 俄勒冈 | 可用 |
| eu-west-1 | 爱尔兰 | 可用 |
| eu-west-2 | 伦敦 | 可用 |
| eu-central-1 | 法兰克福 | 可用 |
| ap-southeast-1 | 新加坡 | 可用 |
| ap-southeast-2 | 悉尼 | 可用 |
| ap-northeast-1 | 东京 | 可用 |
| ap-south-1 | 孟买 | 可用 |
| sa-east-1 | 圣保罗 | 可用 |

## 六、报告输出

### 6.1 目录结构

```
reports/
└── 2026-04-09/
    ├── aws_manual_14-30-00.json
    └── aws_manual_14-30-00.md
```

### 6.2 报告格式

- **手动扫描**：生成 JSON 和 Markdown 两种格式
- **定时扫描**：仅生成 JSON 格式
- **保留期限**：自动清理 7 天前的报告

## 七、规则引擎

### 7.1 自定义规则

创建 `./rules/custom-rules.yaml`：

```yaml
rules:
  - id: "ec2-owner-tag-check"
    name: "EC2 必须包含 Owner 标签"
    resource: "ec2"
    condition: "tags !contains ['Owner']"
    severity: "warning"
    description: "EC2 实例必须包含 Owner 标签用于责任追溯"

  - id: "vpc-environment-tag"
    name: "VPC 环境标识"
    resource: "vpc"
    condition: "name !~ /-(dev|prod|test|staging)-/"
    severity: "info"
    description: "VPC 名称应包含环境标识 (dev/prod/test/staging)"
```

## 八、定时巡检

### 8.1 Cron 定时任务

```bash
# 每小时执行一次
crontab -e

# 添加以下行
0 * * * * source /path/to/aws-env.sh && claude "/aws-resource-manager full_scan --regions=all --max_workers=3" >> /var/log/aws-scan.log 2>&1
```

### 8.2 环境变量文件

```bash
# /path/to/aws-env.sh
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGIONS="us-east-1,us-west-2"
chmod 600 /path/to/aws-env.sh
```

## 九、故障排查

### 9.1 常见问题

**Q: AWS CLI 未找到**
```bash
which aws
export PATH=$PATH:/usr/local/bin
```

**Q: 权限不足**

确保 IAM 用户/角色具有以下权限：
- `ec2:Describe*`
- `s3:Get*`, `s3:List*`
- `cloudwatch:Get*`, `cloudwatch:List*`

**Q: 某些区域扫描失败**

检查区域 ID 拼写，参考支持区域列表。

## 十、安全注意事项

### 10.1 凭证安全

避免在命令行直接设置凭证：
```bash
# 不要这样做！
export AWS_ACCESS_KEY_ID="your-key"

# 使用环境变量文件更安全
source /path/to/aws-env.sh
chmod 600 /path/to/aws-env.sh
```

### 10.2 运营安全

- 所有扫描操作均为**只读**
- 删除操作需要人工确认
- 资源数据本地处理，不上传服务器

## 十一、服务映射

| 资源类型 | AWS |
|----------|-----|
| 计算 | EC2 |
| 网络 | VPC |
| 存储 | S3 |
| 弹性 IP | Elastic IP |
| 安全组 | Security Group |
| 监控 | CloudWatch |
| 子网 | Subnet |
| 网卡 | ENI |

---

**文档版本**: 2.0  
**更新日期**: 2026-04-09
