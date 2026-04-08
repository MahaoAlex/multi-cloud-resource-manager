# 阿里云资源管理器使用指南

## 概述

阿里云资源管理器是一个 Claude Code Skill，用于统一管理和扫描阿里云资源，提供 VPC 盘点、安全扫描、配额监控和多区域合规性检查功能。

### 功能特性

| 功能 | 描述 | 状态 |
|------|------|------|
| **VPC 盘点** | 枚举所有 VPC 并进行使用分析 | 已实现 |
| **安全扫描** | 检测高风险安全组配置 | 已实现 |
| **OSS 扫描** | 识别公开可访问的存储桶和对象 | 已实现 |
| **ECS 监控** | 发现低利用率实例和命名违规 | 已实现 |
| **EIP 扫描** | 检测未挂载的弹性 IP | 已实现 |
| **规则引擎** | 可配置的 YAML 合规规则 | 已实现 |
| **双层并发** | 区域级 + VPC 级并发扫描 | 已实现 |

## 一、环境准备

### 1.1 必要条件

- Claude Code 已安装并配置
- Python 3.8+
- 阿里云 CLI (aliyun) 已安装
- 阿里云账号及 AK/SK

### 1.2 安装阿里云 CLI

```bash
# 下载并安装 aliyun CLI
curl -O https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz
tar -xzf aliyun-cli-linux-latest-amd64.tgz
sudo mv aliyun /usr/local/bin/

# 验证安装
aliyun --version

# 配置凭证
aliyun configure
```

### 1.3 获取阿里云凭证

1. 登录阿里云控制台
2. 进入 "AccessKey 管理"
3. 创建新的 AccessKey，保存 AK 和 SK

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

# 复制阿里云 Skill
cp -r skills/aliyun-resource-manager ~/.claude/skills/

# 验证安装
ls -la ~/.claude/skills/
```

### 2.3 目录结构

```
~/.claude/skills/
└── aliyun-resource-manager/
    ├── skill.yaml
    ├── main.py
    ├── tools/
    │   ├── vpc_inventory.py
    │   ├── vpc_analyzer.py
    │   ├── security_scanner.py
    │   ├── oss_scanner.py
    │   ├── ecs_monitor.py
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
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"
export ALIYUN_REGIONS="cn-hangzhou,cn-shanghai"
```

### 3.2 执行扫描

**完整扫描（双层并发）：**
```
/aliyun-resource-manager full_scan \
  --regions=["cn-hangzhou","cn-shanghai"] \
  --max_workers=3 \
  --vpc_max_workers=3
```

**单独扫描 VPC：**
```
/aliyun-resource-manager scan_vpcs \
  --regions=["cn-hangzhou"]
```

**安全扫描：**
```
/aliyun-resource-manager scan_security \
  --regions=["cn-hangzhou"] \
  --check_ports=[22, 3389]
```

**OSS 扫描：**
```
/aliyun-resource-manager scan_oss \
  --regions=["cn-hangzhou"]
```

**ECS 监控：**
```
/aliyun-resource-manager scan_ecs \
  --regions=["cn-hangzhou"] \
  --cpu_threshold=10 \
  --check_naming=true
```

## 四、双层并发扫描

### 4.1 并发架构

```
第一层：区域级别并发 (max_workers)
    ├── 区域 1 Worker (杭州)
    │       └── 第二层：VPC 级别并发 (vpc_max_workers)
    │               ├── VPC A Worker
    │               ├── VPC B Worker
    │               └── VPC C Worker
    ├── 区域 2 Worker (上海)
    │       └── VPC D/E/F Workers
    └── 区域 3 Worker (北京)
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
aliyun-resource-manager full_scan --max_workers=5 --vpc_max_workers=5

# 低并发（API 限流时使用）
aliyun-resource-manager full_scan --max_workers=2 --vpc_max_workers=2

# 串行模式（调试使用）
aliyun-resource-manager full_scan --max_workers=1 --vpc_max_workers=1
```

## 五、配置参数

### 5.1 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `ALIYUN_ACCESS_KEY_ID` | Access Key ID | 是 |
| `ALIYUN_ACCESS_KEY_SECRET` | Access Key Secret | 是 |
| `ALIYUN_REGIONS` | 区域列表或 'all' | 是 |
| `OSS_CHECK_OBJECTS` | 检查 OSS 对象级权限 | 否（默认 true）|

### 5.2 支持区域

| 区域 ID | 位置 | 状态 |
|---------|------|------|
| cn-hangzhou | 华东1（杭州） | 可用 |
| cn-shanghai | 华东2（上海） | 可用 |
| cn-beijing | 华北2（北京） | 可用 |
| cn-shenzhen | 华南1（深圳） | 可用 |
| cn-qingdao | 华北1（青岛） | 可用 |
| cn-zhangjiakou | 华北3（张家口） | 可用 |
| cn-hongkong | 中国香港 | 可用 |
| ap-southeast-1 | 新加坡 | 可用 |
| ap-southeast-2 | 悉尼 | 可用 |
| ap-northeast-1 | 东京 | 可用 |
| us-west-1 | 硅谷 | 可用 |
| us-east-1 | 弗吉尼亚 | 可用 |
| eu-central-1 | 法兰克福 | 可用 |

## 六、报告输出

### 6.1 目录结构

```
reports/
└── 2026-04-09/
    ├── aliyun_manual_14-30-00.json
    └── aliyun_manual_14-30-00.md
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
  - id: "custom-ecs-tag-check"
    name: "ECS 必须包含 CostCenter 标签"
    resource: "ecs"
    condition: 'tags !~ /CostCenter/'
    severity: "warning"
    description: "ECS 实例应包含 CostCenter 标签用于成本分摊"

  - id: "custom-vpc-naming"
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
0 * * * * source /path/to/aliyun-env.sh && claude "/aliyun-resource-manager full_scan --regions=all --max_workers=3" >> /var/log/aliyun-scan.log 2>&1
```

### 8.2 环境变量文件

```bash
# /path/to/aliyun-env.sh
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"
export ALIYUN_REGIONS="cn-hangzhou,cn-shanghai"
chmod 600 /path/to/aliyun-env.sh
```

## 九、故障排查

### 9.1 常见问题

**Q: aliyun CLI 未找到**
```bash
which aliyun
export PATH=$PATH:/usr/local/bin
```

**Q: 权限不足**

确保 AccessKey 具有以下权限。详细的权限说明见下文"十、安全注意事项"中的"所需 RAM 权限"部分。

快速修复：为 IAM 用户附加以下系统策略：
- `AliyunECSReadOnlyAccess`
- `AliyunVPCReadOnlyAccess`
- `AliyunOSSReadOnlyAccess`
- `AliyunEIPReadOnlyAccess`
- `AliyunCloudMonitorReadOnlyAccess`

**Q: 某些区域扫描失败**

检查区域 ID 拼写，参考支持区域列表。

## 十、安全注意事项

### 10.1 凭证安全

避免在命令行直接设置凭证：
```bash
# 不要这样做！
export ALIYUN_ACCESS_KEY_ID="your-key"

# 使用环境变量文件更安全
source /path/to/aliyun-env.sh
chmod 600 /path/to/aliyun-env.sh
```

### 10.2 所需 RAM 权限

为了完成完整的资源扫描，AccessKey 对应的 RAM 用户需要以下权限：

#### ECS 相关权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `ecs:DescribeInstances` | 查询 ECS 实例列表 | 是 |
| `ecs:DescribeInstanceAttribute` | 获取 ECS 实例详情 | 是 |
| `ecs:DescribeDisks` | 查询云盘信息 | 否 |
| `ecs:DescribeNetworkInterfaces` | 查询网卡信息 | 是 |

#### VPC 相关权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `vpc:DescribeVpcs` | 查询 VPC 列表 | 是 |
| `vpc:DescribeVSwitches` | 查询 VSwitch 列表 | 是 |
| `vpc:DescribeSecurityGroups` | 查询安全组列表 | 是 |
| `vpc:DescribeSecurityGroupAttribute` | 获取安全组详情 | 是 |
| `vpc:DescribeEipAddresses` | 查询 EIP 列表 | 是 |

#### OSS 相关权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `oss:ListBuckets` | 查询 OSS 桶列表 | 是 |
| `oss:GetBucketAcl` | 获取桶 ACL 权限 | 是 |
| `oss:ListObjects` | 查询对象列表（对象级扫描） | 否 |
| `oss:GetObjectAcl` | 获取对象 ACL 权限（对象级扫描） | 否 |

#### CMS 监控权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `cms:DescribeMetricList` | 查询监控指标数据 | 是 |
| `cms:DescribeMetricMetaList` | 查询监控指标列表 | 是 |

#### 自定义权限策略（JSON）

```json
{
  "Version": "1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeInstances",
        "ecs:DescribeInstanceAttribute",
        "ecs:DescribeNetworkInterfaces",
        "vpc:DescribeVpcs",
        "vpc:DescribeVSwitches",
        "vpc:DescribeSecurityGroups",
        "vpc:DescribeSecurityGroupAttribute",
        "vpc:DescribeEipAddresses",
        "oss:ListBuckets",
        "oss:GetBucketAcl",
        "cms:DescribeMetricList",
        "cms:DescribeMetricMetaList"
      ],
      "Resource": ["*"]
    }
  ]
}
```

#### 使用系统策略

阿里云提供了内置的只读策略，可以直接附加到 RAM 用户：

| 策略名称 | 说明 |
|----------|------|
| `AliyunECSReadOnlyAccess` | ECS 只读访问权限 |
| `AliyunVPCReadOnlyAccess` | VPC 只读访问权限 |
| `AliyunOSSReadOnlyAccess` | OSS 只读访问权限 |
| `AliyunEIPReadOnlyAccess` | EIP 只读访问权限 |
| `AliyunCloudMonitorReadOnlyAccess` | 云监控只读权限 |

**注意**：`AliyunOSSReadOnlyAccess` 策略可能包含 bucket 内容读取权限，如果只需要元数据扫描，建议创建自定义策略。

### 10.3 运营安全

- 所有扫描操作均为**只读**
- 删除操作需要人工确认
- 资源数据本地处理，不上传服务器

## 十一、服务映射

| 资源类型 | 阿里云 |
|----------|--------|
| 计算 | ECS |
| 网络 | VPC |
| 存储 | OSS |
| 弹性 IP | EIP |
| 安全组 | Security Group |
| 监控 | CloudMonitor (CMS) |
| 子网 | VSwitch |
| 网卡 | ENI |

---

**文档版本**: 2.0  
**更新日期**: 2026-04-09
