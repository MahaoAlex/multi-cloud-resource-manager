# 华为云资源管理器使用指南

## 概述

华为云资源管理器是一个 Claude Code Skill，用于统一管理和扫描华为云资源，提供 VPC 盘点、安全扫描、配额监控和多区域合规性检查功能。

### 功能特性

| 功能 | 描述 | 状态 |
|------|------|------|
| **VPC 盘点** | 枚举所有 VPC 并进行使用分析 | 已实现 |
| **安全扫描** | 检测高风险安全组配置 | 已实现 |
| **OBS 扫描** | 识别公开可访问的存储桶和对象 | 已实现 |
| **ECS 监控** | 发现低利用率实例和命名违规 | 已实现 |
| **EIP 扫描** | 检测未挂载的弹性 IP | 已实现 |
| **规则引擎** | 可配置的 YAML 合规规则 | 已实现 |
| **双层并发** | 区域级 + VPC 级并发扫描 | 已实现 |

## 一、环境准备

### 1.1 必要条件

- Claude Code 已安装并配置
- Python 3.8+
- 华为云 CLI (hcloud) 已安装
- 华为云账号及 AK/SK

### 1.2 安装华为云 CLI (KooCLI)

Huawei Cloud CLI 已更名为 **KooCLI**，但命令行工具名称仍为 `hcloud`。

**官方文档**: https://support.huaweicloud.com/intl/en-us/qs-hcli/hcli_02_003.html

```bash
# Linux (AMD64)
curl -LO https://ap-southeast-3-hwcloudcli.obs.ap-southeast-3.myhuaweicloud.com/cli/latest/huaweicloud-cli-linux-amd64.tar.gz
tar -xzf huaweicloud-cli-linux-amd64.tar.gz
sudo mv hcloud /usr/local/bin/

# 验证安装（注意：hcloud 不支持 --version，请使用 --help）
hcloud --help > /dev/null 2>&1 && echo "hcloud installed successfully" || echo "hcloud installation failed"
```

### 1.3 获取华为云凭证

1. 登录华为云控制台
2. 进入 "我的凭证" -> "访问密钥"
3. 创建新的访问密钥，保存 AK 和 SK

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

# 复制核心 Skills
cp -r skills/huaweicloud-core/proxy-injection ~/.claude/skills/
cp -r skills/huaweicloud-core/auth-manager ~/.claude/skills/

# 复制主 Skill
cp -r skills/huaweicloud-resource-manager ~/.claude/skills/

# 验证安装
ls -la ~/.claude/skills/
```

### 2.3 目录结构

```
~/.claude/skills/
├── proxy-injection/          # 代理配置
│   ├── skill.yaml
│   └── proxy_injection.py
├── auth-manager/             # 认证管理
│   ├── skill.yaml
│   ├── auth_manager.py
│   └── secure_runner.py
└── huaweicloud-resource-manager/   # 资源管理主模块
    ├── skill.yaml
    ├── main.py
    ├── tools/
    │   ├── vpc_inventory.py
    │   ├── vpc_analyzer.py
    │   ├── security_scanner.py
    │   ├── obs_scanner.py
    │   ├── ecs_monitor.py
    │   ├── eip_scanner.py
    │   ├── rule_engine.py
    │   └── report_generator.py
    └── rules/
        ├── naming-conventions.yaml
        └── security-rules.yaml
```

### 2.4 重启 Claude Code

部署完成后需要重启以加载新的 Skills：

```bash
exit
claude
```

## 三、快速开始

### 3.1 交互式配置（推荐）

使用交互式配置避免凭证暴露在命令历史中：

```
配置华为云认证
```

预期交互：
```
Claude: 我来帮你配置华为云认证信息。

步骤 1: Access Key ID
请输入华为云 Access Key ID: ********

步骤 2: Secret Access Key
请输入华为云 Secret Access Key (输入不会显示): ********

步骤 3: 区域选择
请输入要扫描的区域 (逗号分隔，或输入 'all' 扫描所有区域): cn-north-4,cn-south-1

步骤 4: 验证配置
正在验证区域 cn-north-4 的凭证...
[OK] 验证成功，发现 5 个 VPC

认证配置完成！
```

### 3.2 代理配置（如需要）

```
帮我配置华为云代理
```

### 3.3 执行扫描

**完整扫描（双层并发）：**
```
执行完整的华为云资源扫描
```

**指定参数扫描：**
```
/huaweicloud-scan full_scan \
  --regions=["cn-north-4","cn-south-1"] \
  --max_workers=3 \
  --vpc_max_workers=3
```

**单独扫描 VPC：**
```
扫描华为云 VPC 资源
```

**安全扫描：**
```
扫描华为云安全风险
```

## 四、双层并发扫描

### 4.1 并发架构

```
第一层：区域级别并发 (max_workers)
    ├── 区域 1 Worker
    │       └── 第二层：VPC 级别并发 (vpc_max_workers)
    │               ├── VPC A Worker
    │               ├── VPC B Worker
    │               └── VPC C Worker
    ├── 区域 2 Worker
    │       └── VPC D/E/F Workers
    └── 区域 3 Worker
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
/huaweicloud-scan full_scan --max_workers=5 --vpc_max_workers=5

# 低并发（API 限流时使用）
/huaweicloud-scan full_scan --max_workers=2 --vpc_max_workers=2

# 串行模式（调试使用）
/huaweicloud-scan full_scan --max_workers=1 --vpc_max_workers=1
```

## 五、配置参数

### 5.1 环境变量

| 变量 | 说明 | 必需 |
|------|------|------|
| `HWCLOUD_ACCESS_KEY` | Access Key ID | 是 |
| `HWCLOUD_SECRET_KEY` | Secret Access Key | 是 |
| `HWCLOUD_REGIONS` | 区域列表或 'all' | 是 |
| `HWCLOUD_PROJECT_ID` | IAM 子用户项目 ID | 否 |
| `HTTP_PROXY` | HTTP 代理 | 否 |
| `HTTPS_PROXY` | HTTPS 代理 | 否 |
| `NO_PROXY` | 代理例外地址 | 否 |

### 5.2 支持区域

| 区域 ID | 位置 | 状态 |
|---------|------|------|
| cn-north-4 | 北京 | 可用 |
| cn-north-1 | 北京 | 可用 |
| cn-south-1 | 广州 | 可用 |
| cn-east-2 | 上海 | 可用 |
| cn-east-3 | 上海 | 可用 |
| cn-southwest-2 | 贵阳 | 可用 |
| ap-southeast-1 | 香港 | 可用 |
| ap-southeast-2 | 曼谷 | 可用 |
| ap-southeast-3 | 新加坡 | 可用 |
| eu-west-101 | 阿姆斯特丹 | 可用 |
| af-south-1 | 约翰内斯堡 | 可用 |

## 六、报告输出

### 6.1 目录结构

```
reports/
└── 2026-04-09/
    ├── manual_14-30-00.json    # JSON 格式报告
    └── manual_14-30-00.md      # Markdown 可读报告
```

### 6.2 报告格式

- **手动扫描**：生成 JSON 和 Markdown 两种格式
- **定时扫描**：仅生成 JSON 格式
- **保留期限**：自动清理 7 天前的报告

### 6.3 报告示例

```json
{
  "scan_metadata": {
    "timestamp": "2026-04-09T14:30:00Z",
    "scan_type": "manual",
    "regions": ["cn-north-4", "cn-south-1"],
    "duration_seconds": 52,
    "scan_config": {
      "max_workers": 3,
      "vpc_max_workers": 3
    }
  },
  "summary": {
    "vpcs": 16,
    "unused_vpcs": 3,
    "security_issues": 4,
    "public_obs_buckets": 2,
    "low_utilization_ecs": 4,
    "unattached_eips": 3
  },
  "action_items": [
    {
      "severity": "CRITICAL",
      "resource": "sg-001",
      "issue": "端口 22 对公网开放",
      "recommendation": "立即限制源 IP 范围"
    }
  ]
}
```

## 七、规则引擎

### 7.1 内置规则

规则存储在 `rules/` 目录：

- `naming-conventions.yaml` - 资源命名合规
- `security-rules.yaml` - 安全风险检测

### 7.2 自定义规则

创建 `./rules/custom-rules.yaml`：

```yaml
rules:
  - id: "ecs-owner-tag-check"
    name: "ECS 必须包含 Owner 标签"
    resource: "ecs"
    condition: "tags !contains ['Owner']"
    severity: "warning"
    description: "ECS 实例必须包含 Owner 标签用于责任追溯"
```

### 7.3 支持的条件

- `name =~ /pattern/` - 名称匹配正则
- `name !~ /pattern/` - 名称不匹配正则
- `ports contains [22,33]` - 端口列表包含值
- `status = value` - 精确匹配
- `cpu_avg_24h < 10` - 数值比较

## 八、定时巡检

### 8.1 Cron 定时任务

```bash
# 每小时执行一次
crontab -e

# 添加以下行
0 * * * * source /path/to/huaweicloud-env.sh && claude "/huaweicloud-scan --mode=scheduled --regions=all --max_workers=3" >> /var/log/huaweicloud-scan.log 2>&1
```

### 8.2 Airflow DAG

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'cloudops',
    'depends_on_past': False,
    'email': ['ops@company.com'],
    'email_on_failure': True,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'huaweicloud_resource_scan',
    default_args=default_args,
    description='华为云资源安全扫描',
    schedule_interval='0 * * * *',
    start_date=datetime(2026, 4, 9),
    catchup=False,
) as dag:

    scan_task = BashOperator(
        task_id='resource_scan',
        bash_command='source /path/to/huaweicloud-env.sh && claude "/huaweicloud-scan --mode=scheduled --regions=all --max_workers=3"',
    )
```

## 九、故障排查

### 9.1 常见问题

**Q: hcloud 命令找不到**
```bash
which hcloud
# 如果没有，添加到 PATH
export PATH=$PATH:/usr/local/bin
```

**Q: Failed to parse JSON output 警告**

这是正常现象，可能原因：
- 某些区域没有特定资源
- API 响应包含警告信息

解决方案：
```bash
# 降低并发数
/huaweicloud-scan full_scan --max_workers=2 --vpc_max_workers=2
```

**Q: 认证失败**
```bash
# 使用安全脚本验证
python ~/.claude/skills/huaweicloud-core/auth-manager/secure_runner.py --verify
```

**Q: 扫描超时**
```bash
# 减少并发
/huaweicloud-scan full_scan --max_workers=2 --vpc_max_workers=1
```

### 9.2 调试模式

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
```

## 十、安全注意事项

### 10.1 凭证安全

**推荐方式（交互式）：**
```
配置华为云认证
```

**避免使用（会暴露在命令历史）：**
```bash
# 不要这样做！
export HWCLOUD_ACCESS_KEY="your-secret-key"

# 如果必须这样做，立即清理历史
history -c
```

### 10.2 所需 IAM 权限

为了完成完整的资源扫描，AK/SK 对应的 IAM 用户需要以下权限：

#### VPC 相关权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `vpc:vpcs:list` | 查询 VPC 列表 | 是 |
| `vpc:vpcs:get` | 获取 VPC 详情 | 是 |
| `vpc:subnets:list` | 查询子网列表 | 是 |
| `vpc:securityGroups:list` | 查询安全组列表 | 是 |
| `vpc:securityGroupRules:list` | 查询安全组规则 | 是 |
| `vpc:ports:list` | 查询端口（网卡）信息 | 是 |

#### ECS 相关权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `ecs:servers:list` | 查询 ECS 实例列表 | 是 |
| `ecs:servers:get` | 获取 ECS 实例详情 | 是 |
| `ecs:serverVolumeAttachments:list` | 查询云硬盘挂载信息 | 否 |
| `ecs:serverInterfaces:list` | 查询网卡信息 | 是 |

#### OBS 相关权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `obs:bucket:list` | 查询 OBS 桶列表 | 是 |
| `obs:bucket:getBucketAcl` | 获取桶 ACL 权限 | 是 |
| `obs:object:getObjectAcl` | 获取对象 ACL 权限（对象级扫描） | 否 |

#### EIP 相关权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `vpc:publicIps:list` | 查询弹性 IP 列表 | 是 |

#### CES 监控权限

| 权限 Action | 用途 | 必需 |
|-------------|------|------|
| `ces:metrics:list` | 查询监控指标列表 | 是 |
| `ces:data:list` | 获取监控数据（CPU 利用率） | 是 |

#### 完整权限策略（JSON）

```json
{
  "Version": "1.1",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "vpc:vpcs:list",
        "vpc:vpcs:get",
        "vpc:subnets:list",
        "vpc:securityGroups:list",
        "vpc:securityGroupRules:list",
        "vpc:ports:list",
        "vpc:publicIps:list",
        "ecs:servers:list",
        "ecs:servers:get",
        "ecs:serverInterfaces:list",
        "obs:bucket:list",
        "obs:bucket:getBucketAcl",
        "ces:metrics:list",
        "ces:data:list"
      ],
      "Resource": ["*"]
    }
  ]
}
```

#### 使用内置策略

也可以使用华为云内置的只读策略：

1. **VPC ReadOnlyAccess** - VPC 只读访问权限
2. **ECS ReadOnlyAccess** - ECS 只读访问权限
3. **OBS ReadOnlyAccess** - OBS 只读访问权限
4. **CES ReadOnlyAccess** - 云监控只读权限

将这些策略附加到 IAM 用户即可。

### 10.3 运营安全

- 所有扫描操作均为**只读**
- 删除操作需要人工确认
- 资源数据本地处理，不上传服务器
- 报告仅包含元数据，不含敏感信息

## 十一、服务映射

| 资源类型 | 华为云 |
|----------|--------|
| 计算 | ECS |
| 网络 | VPC |
| 存储 | OBS |
| 弹性 IP | EIP |
| 安全组 | Security Group |
| 监控 | CES |
| 子网 | Subnet |
| 网卡 | NIC |

---

**文档版本**: 2.0  
**更新日期**: 2026-04-09
