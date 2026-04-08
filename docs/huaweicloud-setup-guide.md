# Huawei Cloud Resource Manager Skills 部署指南

本文档指导你如何在 Claude Code 中部署和测试华为云资源管理 Skills。

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

## 二、Skills 部署

### 2.1 下载并部署 Skills

```bash
# 创建临时目录下载项目
cd /tmp
git clone https://github.com/MahaoAlex/multi-cloud-resource-manager.git
cd multi-cloud-resource-manager

# 复制核心 Skills 到 Claude Code 目录
cp -r skills/huaweicloud-core/proxy-injection ~/.claude/skills/
cp -r skills/huaweicloud-core/auth-manager ~/.claude/skills/

# 复制主 Skill
cp -r skills/huaweicloud-resource-manager ~/.claude/skills/

# 验证安装
ls -la ~/.claude/skills/

# 清理临时文件(可选)
cd /tmp
rm -rf multi-cloud-resource-manager
```

### 2.2 目录结构验证

安装完成后，Claude Code skills 目录应包含：

```
~/.claude/skills/
├── proxy-injection/
│   ├── skill.yaml
│   └── proxy_injection.py
├── auth-manager/
│   ├── skill.yaml
│   ├── auth_manager.py
│   └── secure_runner.py
└── huaweicloud-resource-manager/
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

## 三、端到端测试流程

### 3.1 重启 Claude Code

部署 Skills 后需要重启 Claude Code 以加载新的 Skills：

```bash
# 退出 Claude Code
exit

# 重新启动 Claude Code
claude
```

### 3.2 测试 proxy-injection Skill

**场景：需要代理才能访问华为云**

在 Claude Code 中输入：

```
帮我配置华为云代理
```

预期交互：
```
Claude: 我来帮你配置华为云 CLI 的代理设置。

步骤 1: HTTP 代理
请输入 HTTP 代理地址 (例如: http://proxy.company.com:8080，如不需要请直接回车): http://proxy.company.com:8080

步骤 2: HTTPS 代理
请输入 HTTPS 代理地址 (默认使用 HTTP 代理): http://proxy.company.com:8080

步骤 3: 例外地址
请输入不需要代理的地址 (逗号分隔，例如: localhost,127.0.0.1): localhost,127.0.0.1,myhuaweicloud.com

配置完成！环境变量已设置：
- HTTP_PROXY=http://proxy.company.com:8080
- HTTPS_PROXY=http://proxy.company.com:8080
- NO_PROXY=localhost,127.0.0.1,myhuaweicloud.com

注意：这些设置仅在当前会话有效。
```

### 3.3 测试 auth-manager Skill（安全方式）

**场景：配置华为云认证信息（推荐方式）**

使用交互式配置，避免凭证出现在命令历史中：

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
可选区域:
- cn-north-4 (北京)
- cn-south-1 (广州)
- cn-east-2 (上海)
- cn-east-3 (上海)
- ap-southeast-1 (香港)
- ... (其他区域)

步骤 4: 验证配置
正在验证区域 cn-north-4 的凭证...
[OK] 验证成功，发现 5 个 VPC

正在验证区域 cn-south-1 的凭证...
[OK] 验证成功，发现 3 个 VPC

认证配置完成！环境变量已设置：
- HWCLOUD_ACCESS_KEY=******** (已脱敏)
- HWCLOUD_SECRET_KEY=******** (已脱敏)
- HWCLOUD_REGIONS=cn-north-4,cn-south-1
```

### 3.4 测试 VPC 盘点功能

**场景：盘点所有 VPC 资源**

在 Claude Code 中输入：

```
扫描华为云 VPC 资源
```

预期交互：
```
Claude: 开始扫描华为云 VPC 资源...

当前阶段: 正在枚举 VPC
执行动作: 执行 hcloud vpc ListVpcs 命令
所依据的官方文档约束: https://support.huaweicloud.com/intl/en-us/qs-hcli/hcli_02_003.html

[1/2] 扫描区域: cn-north-4
  - 发现 5 个 VPC
  - 正在分析 VPC 使用情况...
  - vpc-001 (production-vpc): 在使用中 (3 个子网，12 个 ECS)
  - vpc-002 (test-vpc): 未使用 (0 个子网)
  [OK] 完成 (15s)

[2/2] 扫描区域: cn-south-1
  - 发现 3 个 VPC
  - 正在分析 VPC 使用情况...
  - vpc-003 (staging-vpc): 在使用中 (2 个子网，8 个 ECS)
  [OK] 完成 (12s)

结果:
- 总计 VPC: 8 个
- 在使用中: 7 个
- 未使用: 1 个 (test-vpc)

风险与下一步: 
发现 1 个未使用的 VPC，建议在报告中查看详细信息并联系负责人确认删除。

正在生成报告...
报告已生成: ./reports/2026-04-08/manual_14-30-00.md
```

### 3.5 测试安全扫描功能

**场景：扫描高危安全组配置**

在 Claude Code 中输入：

```
扫描华为云安全风险
```

预期交互：
```
Claude: 开始扫描华为云安全风险...

当前阶段: 正在扫描安全组配置
执行动作: 检查安全组规则中的高危端口开放情况

[1/2] 扫描区域: cn-north-4
  - 发现 12 个安全组
  - 检查规则...
  [WARN] 发现高危配置:
    - sg-001 (default): 端口 22,33,44 对 0.0.0.0/0 开放 [CRITICAL]
    - sg-002 (web-sg): 端口 22 对 0.0.0.0/0 开放 [CRITICAL]

[2/2] 扫描区域: cn-south-1
  - 发现 8 个安全组
  - 检查规则...
  [WARN] 发现高危配置:
    - sg-003 (app-sg): 端口 22 对 0.0.0.0/0 开放 [CRITICAL]

结果:
- 总计检查: 20 个安全组
- 发现问题: 3 个高危配置
- 风险等级: 2 个 Critical, 1 个 High

风险与下一步:
发现安全组对公网开放高危端口，建议立即限制访问源IP范围。

正在生成报告...
报告已生成: ./reports/2026-04-08/manual_14-35-00.md
```

### 3.6 测试 OBS 扫描功能

**场景：检测公开 OBS 存储桶**

在 Claude Code 中输入：

```
检查华为云 OBS 公开访问
```

预期交互：
```
Claude: 开始检查 OBS 存储桶的公开访问状态...

当前阶段: 正在扫描 OBS 存储桶
执行动作: 检查存储桶 ACL 和对象权限

[1/2] 扫描区域: cn-north-4
  - 发现 10 个存储桶
  - 检查 ACL...
  [WARN] 发现公开存储桶:
    - bucket-001 (data-bucket): public-read 权限 [HIGH]
      - 公开对象: data.xlsx, report.pdf
    - bucket-002 (backup): public-read-write 权限 [CRITICAL]

[2/2] 扫描区域: cn-south-1
  - 发现 5 个存储桶
  - 检查 ACL...
  [OK] 所有存储桶均为私有

结果:
- 总计检查: 15 个存储桶
- 发现问题: 2 个公开存储桶
- 公开对象: 4 个

风险与下一步:
发现公开可访问的 OBS 存储桶，建议立即设置为私有权限，防止数据泄露。

正在生成报告...
```

### 3.7 测试 ECS 监控功能

**场景：检查 ECS 低利用率和命名规范**

在 Claude Code 中输入：

```
检查华为云 ECS 资源优化
```

预期交互：
```
Claude: 开始检查 ECS 资源优化情况...

当前阶段: 正在扫描 ECS 实例
执行动作: 检查 CPU 利用率(24小时平均)和命名规范

[1/2] 扫描区域: cn-north-4
  - 发现 25 个 ECS 实例
  - 获取 CPU 指标 (过去24小时)...
  - 检查命名规范...
  
  发现低利用率实例:
    - ecs-001 (web-server): CPU 5.2% [INFO]
    - ecs-002 (test-vm): CPU 3.1% [INFO]
    - ecs-003 (dev-server): CPU 8.5% [INFO]
  
  发现命名违规:
    - ecs-004 (web-server): 缺少工号信息 [WARNING]
    - ecs-005 (api-gateway): 缺少工号信息 [WARNING]
    - ecs-006 (database): 缺少工号信息 [WARNING]

[2/2] 扫描区域: cn-south-1
  - 发现 15 个 ECS 实例
  - 获取 CPU 指标...
  - 检查命名规范...
  - 无异常

结果:
- 总计 ECS: 40 个
- 低利用率 (<10%): 3 个
- 命名违规: 3 个
- 资源优化潜力: 高

风险与下一步:
建议优化或释放低利用率 ECS 实例，修改不合规的实例名称加入工号信息。

正在生成报告...
```

### 3.8 测试完整扫描（并发扫描）

**场景：执行完整资源扫描**

在 Claude Code 中输入：

```
执行完整的华为云资源扫描
```

或使用命令模式：

```
/huaweicloud-scan full_scan --regions=["cn-north-4","cn-south-1"] --max_workers=3
```

预期交互：
```
Claude: 开始执行完整的华为云资源扫描...

═══════════════════════════════════════════════
  Huawei Cloud Resource Manager - 完整扫描
═══════════════════════════════════════════════

扫描区域: cn-north-4, cn-south-1, cn-east-2
并发数: 3 workers
扫描类型: manual
开始时间: 2026-04-08 14:40:00

───────────────────────────────────────────────
[1/3] 并发扫描区域: cn-north-4 (延迟 0.6s)
───────────────────────────────────────────────
  - VPC 盘点: 8 个 VPC, 2 未使用
  - 安全组: 3 个高危配置
  - OBS: 2 个公开存储桶
  - ECS: 3 个低利用率, 2 个命名违规
  - EIP: 2 个未挂载
  [OK] 完成 (45s)

───────────────────────────────────────────────
[2/3] 并发扫描区域: cn-south-1 (延迟 1.1s)
───────────────────────────────────────────────
  - VPC 盘点: 5 个 VPC, 1 未使用
  - 安全组: 1 个高危配置
  - OBS: 未发现异常
  - ECS: 1 个低利用率
  - EIP: 1 个未挂载
  [OK] 完成 (42s)

───────────────────────────────────────────────
[3/3] 并发扫描区域: cn-east-2 (延迟 0.8s)
───────────────────────────────────────────────
  - VPC 盘点: 3 个 VPC, 0 未使用
  - 安全组: 未发现风险
  - OBS: 未发现异常
  - ECS: 无异常
  - EIP: 无异常
  [OK] 完成 (38s)

═══════════════════════════════════════════════
  扫描完成 - 汇总报告
═══════════════════════════════════════════════

扫描统计:
┌──────────────────────┬────────┐
│ 指标                  │ 数量   │
├──────────────────────┼────────┤
│ 扫描区域              │ 3      │
│ 并发 Workers          │ 3      │
│ 总 VPC 数            │ 16     │
│ 未使用 VPC           │ 3      │
│ 安全高危配置          │ 4      │
│ 公开 OBS 存储桶      │ 2      │
│ 低利用率 ECS         │ 4      │
│ 命名违规 ECS         │ 2      │
│ 未挂载 EIP           │ 3      │
└──────────────────────┴────────┘

区域分布:
- cn-north-4: VPC=8, 安全问题=3, OBS=2, ECS=5, EIP=2
- cn-south-1: VPC=5, 安全问题=1, OBS=0, ECS=1, EIP=1
- cn-east-2:  VPC=3, 安全问题=0, OBS=0, ECS=0, EIP=0

═══════════════════════════════════════════════
  待处理事项 (需人工确认)
═══════════════════════════════════════════════

[CRITICAL] 安全组高危端口开放
  - sg-001 (cn-north-4): 22,33,44 对公网开放
  - 建议: 立即限制源IP范围

[HIGH] 公开 OBS 存储桶
  - bucket-001 (cn-north-4): public-read 权限
  - bucket-002 (cn-north-4): public-read-write 权限
  - 建议: 立即设置为私有

[WARNING] 未使用 VPC
  - vpc-002 (cn-north-4): test-vpc, 负责人: zhangsan
  - vpc-006 (cn-south-1): temp-vpc, 负责人: lisi
  - 建议: 联系负责人确认删除

[INFO] 低利用率 ECS
  - ecs-001 (cn-north-4): CPU 5.2%, 建议优化或释放
  - ecs-002 (cn-north-4): CPU 3.1%, 建议优化或释放
  - ecs-003 (cn-north-4): CPU 8.5%, 建议优化或释放
  - ecs-012 (cn-south-1): CPU 6.2%, 建议优化或释放

[INFO] 未挂载 EIP
  - eip-001 (cn-north-4): 123.45.67.89
  - eip-002 (cn-north-4): 123.45.67.90
  - eip-003 (cn-south-1): 223.45.67.88
  - 建议: 如不需要请释放

═══════════════════════════════════════════════

报告文件已生成:
- JSON: ./reports/2026-04-08/manual_14-40-00.json
- Markdown: ./reports/2026-04-08/manual_14-40-00.md

扫描用时: 52 秒 (并发扫描节省约 58% 时间)
```

## 四、性能优化与并发扫描

### 4.1 并发扫描说明

完整扫描（full_scan）支持并发扫描多个区域，可显著减少总扫描时间。

**并发原理：**
- 每个区域由独立的 worker 线程扫描
- 默认最大并发数：5（可配置范围 1-5）
- 每个 worker 启动时有 0.5-1.5s 随机延迟，避免 API 限流
- 扫描操作为只读，并发执行安全

**使用建议：**

| 场景 | 推荐并发数 | 说明 |
|------|-----------|------|
| 1-3 个区域 | 3 | 平衡速度与稳定性 |
| 4-10 个区域 | 5 | 最大化并发效率 |
| 网络不稳定 | 2 | 降低并发避免超时 |
| API 限流 | 1 | 串行扫描 |

### 4.2 并发扫描参数

```
/huaweicloud-scan full_scan \
  --regions=["cn-north-4","cn-south-1","cn-east-2"] \
  --max_workers=3 \
  --scan_type="manual"
```

参数说明：
- `regions`: 要扫描的区域列表
- `max_workers`: 并发 worker 数量（1-5，默认 5）
- `scan_type`: manual 或 scheduled

### 4.3 性能对比

假设扫描 5 个区域，每个区域耗时约 40 秒：

| 扫描方式 | Workers | 预计耗时 | 时间节省 |
|---------|---------|---------|---------|
| 串行扫描 | 1 | ~200 秒 | - |
| 低并发 | 2 | ~100 秒 | 50% |
| 默认并发 | 5 | ~45 秒 | 78% |

## 五、安全凭证配置

### 5.1 安全配置方式（推荐）

使用交互式配置，避免凭证出现在 shell 历史中：

```bash
# 方式一：使用 Claude Code Skill
配置华为云认证

# 方式二：使用安全脚本
python skills/huaweicloud-core/auth-manager/secure_runner.py --setup

# 方式三：使用交互式输入
read -s HWCLOUD_ACCESS_KEY
read -s HWCLOUD_SECRET_KEY
export HWCLOUD_ACCESS_KEY HWCLOUD_SECRET_KEY
```

### 5.2 不安全的配置方式（避免使用）

```bash
# 以下方式会在 shell 历史中留下凭证记录！
export HWCLOUD_ACCESS_KEY="HPUA0AEHXL3JK6PVYUDD"
export HWCLOUD_SECRET_KEY="DDpL6T4vUkHQ7vg8aRAakN1LwTNMAy0royPv1ajz"

# 清理历史记录
history -c
```

### 5.3 凭证验证

配置完成后验证：

```bash
# 方式一
python skills/huaweicloud-core/auth-manager/secure_runner.py --verify

# 方式二
/huaweicloud-scan show_auth_status
```

## 六、定时巡检配置

### 6.1 Cron 定时任务

每小时执行一次巡检：

```bash
# 编辑 crontab
crontab -e

# 添加以下行（注意：需要先配置环境变量或使用包装脚本）
0 * * * * cd /path/to/project && source /path/to/env.sh && claude "/huaweicloud-scan --mode=scheduled --regions=all" >> /var/log/huaweicloud-scan.log 2>&1
```

**安全建议**：不要在 crontab 中直接写 AK/SK，使用环境变量文件：

```bash
# /path/to/env.sh
export HWCLOUD_ACCESS_KEY="${HWCLOUD_ACCESS_KEY}"
export HWCLOUD_SECRET_KEY="${HWCLOUD_SECRET_KEY}"
export HWCLOUD_REGIONS="cn-north-4,cn-south-1"
chmod 600 /path/to/env.sh
```

### 6.2 Airflow DAG

```python
from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'cloudops',
    'depends_on_past': False,
    'email': ['ops@company.com'],
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'huaweicloud_resource_scan',
    default_args=default_args,
    description='Huawei Cloud resource security scan',
    schedule_interval='0 * * * *',  # 每小时
    start_date=datetime(2026, 4, 8),
    catchup=False,
) as dag:

    scan_task = BashOperator(
        task_id='resource_scan',
        bash_command='source /path/to/env.sh && claude "/huaweicloud-scan --mode=scheduled --regions=all --max_workers=3"',
    )

    scan_task
```

## 七、报告查看与处理

### 7.1 查看报告

```bash
# 查看 Markdown 报告
cat ./reports/2026-04-08/manual_14-40-00.md

# 查看 JSON 报告
cat ./reports/2026-04-08/scheduled_15-00-00.json | jq

# 查找最新报告
ls -lt ./reports/*/manual_*.md | head -1
```

### 7.2 集成到 IM 通知

示例：将报告发送到钉钉/飞书

```python
#!/usr/bin/env python3
"""发送扫描报告到钉钉"""
import json
import requests
import sys
from pathlib import Path

DINGTALK_WEBHOOK = "https://oapi.dingtalk.com/robot/send?access_token=xxx"

def send_report(report_file):
    with open(report_file) as f:
        data = json.load(f)
    
    summary = data['summary']
    
    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": "华为云资源巡检报告",
            "text": f"""### 华为云资源巡检报告
**扫描时间**: {data.get('timestamp', 'N/A')}
**扫描区域**: {', '.join(data.get('regions', []))}
**扫描用时**: {data.get('duration_seconds', 0)} 秒

**汇总统计**:
- VPC 总数: {summary.get('vpcs', 0)} (未使用: {summary.get('unused_vpcs', 0)})
- 安全问题: {summary.get('security_issues', 0)}
- 公开 OBS: {summary.get('public_obs_buckets', 0)}
- 低利用率 ECS: {summary.get('low_utilization_ecs', 0)}
- 未挂载 EIP: {summary.get('unattached_eips', 0)}

**严重问题**: {summary.get('security_issues', 0)} 项需立即处理

[点击查看详情](http://your-report-server/reports/)
"""
        }
    }
    
    requests.post(DINGTALK_WEBHOOK, json=message)

if __name__ == "__main__":
    send_report(sys.argv[1])
```

## 八、自定义规则

### 8.1 创建自定义规则文件

在项目目录创建 `./rules/custom-rules.yaml`：

```yaml
rules:
  - id: "custom-ecs-tag-check"
    name: "ECS Tag Check"
    resource: "ecs"
    condition: "tags !contains ['Owner']"
    severity: "warning"
    description: "ECS 实例必须包含 Owner 标签"

  - id: "custom-vpc-naming"
    name: "VPC Department Tag"
    resource: "vpc"
    condition: "name !~ /-(dev|prod|test|staging)-/"
    severity: "info"
    description: "VPC 名称应包含环境标识 (dev/prod/test/staging)"

  - id: "custom-obs-encryption"
    name: "OBS Bucket Encryption"
    resource: "obs"
    condition: "encryption_status == 'disabled'"
    severity: "high"
    description: "OBS 存储桶应启用加密"
```

### 8.2 规则生效

自定义规则会自动生效，优先级高于内置规则。

### 8.3 列出所有规则

```
/huaweicloud-scan list_rules
```

## 九、故障排查

### 9.1 常见问题

**Q: hcloud 命令找不到**
```bash
# 检查 hcloud 是否在 PATH 中
which hcloud

# 如果没有，添加到 PATH
export PATH=$PATH:/usr/local/bin
```

**Q: 认证失败**
```bash
# 检查环境变量是否设置（已脱敏显示）
echo "AK: ${HWCLOUD_ACCESS_KEY:0:4}****${HWCLOUD_ACCESS_KEY: -4}"
echo "SK: ${HWCLOUD_SECRET_KEY:0:4}****${HWCLOUD_SECRET_KEY: -4}"
echo "Regions: $HWCLOUD_REGIONS"

# 手动测试 hcloud 连接
hcloud VPC ListVpcs --cli-region=cn-north-4
```

**Q: 并发扫描时出现 "Failed to parse JSON output" 警告**

这是正常现象，可能原因：
1. 某些区域没有特定资源（如没有 ECS 实例）
2. API 响应包含警告信息而非纯 JSON
3. 并发请求导致短暂超时

解决方案：
```bash
# 降低并发数
/huaweicloud-scan full_scan --max_workers=2

# 或串行扫描
/huaweicloud-scan full_scan --max_workers=1
```

**Q: 代理连接失败**
```bash
# 测试代理连接
curl -x http://proxy:8080 https://myhuaweicloud.com

# 检查 NO_PROXY 设置
echo $NO_PROXY
```

**Q: 扫描超时**
```bash
# 减少扫描区域
/huaweicloud-scan full_scan --regions=["cn-north-4"]

# 降低并发数
/huaweicloud-scan full_scan --max_workers=2
```

### 9.2 调试模式

启用详细日志：

```bash
# 设置日志级别
export LOG_LEVEL=DEBUG

# 或在 Claude Code 中
/huaweicloud-scan full_scan --debug
```

### 9.3 查看执行日志

```bash
# 查看最近的错误
grep -i error ./reports/*/manual_*.json | tail -20

# 查看特定区域的日志
/huaweicloud-scan scan_vpcs --regions=["cn-north-4"] --verbose
```

## 十、安全注意事项

### 10.1 凭证保护
- AK/SK 仅存储在环境变量中，不写入文件
- 不要提交到 Git 仓库（已添加 .gitignore）
- 定期轮换凭证（建议 90 天）
- 使用最小权限原则的 IAM 账号

### 10.2 防止凭证泄露到命令历史

**问题**: 在命令行中直接设置环境变量会导致 AK/SK 出现在 shell 历史记录中：
```bash
# 不安全的方式 - 会记录在命令历史中
export HWCLOUD_ACCESS_KEY="your-secret-key"
```

**解决方案**: 

1. **使用 Claude Code Skill（推荐）**
   ```
   配置华为云认证
   ```

2. **使用安全脚本**
   ```bash
   python skills/huaweicloud-core/auth-manager/secure_runner.py --setup
   ```

3. **使用环境变量文件**
   ```bash
   # .env 文件（权限 600）
   source .env
   ```

4. **定期清理历史**
   ```bash
   history -c
   ```

### 10.3 报告安全
- 报告文件包含资源信息，注意访问控制
- 建议设置报告目录权限：`chmod 700 ./reports`
- 定期清理历史报告（默认保留 7 天）
- 不要将报告提交到 Git

### 10.4 操作安全
- 所有扫描操作均为只读，不会修改资源
- 删除操作需要人工确认
- 生产环境建议先测试单个区域
- 建议在非工作时间执行全面扫描

## 十一、附录

### 11.1 支持的华为云服务

| 服务 | 检测内容 | API 权限要求 |
|------|----------|-------------|
| VPC | 资源枚举、使用分析 | VPC ReadOnly |
| ECS | CPU 利用率、命名规范 | ECS ReadOnly, CES ReadOnly |
| OBS | 公开存储桶、公开对象 | OBS ReadOnly |
| EIP | 未挂载检测 | VPC ReadOnly |
| Security Group | 高危端口开放 | VPC ReadOnly |

### 11.2 华为云 CLI 注意事项

**hcloud 版本检查**：
```bash
# 正确方式（hcloud 不支持 --version）
hcloud --help > /dev/null 2>&1 && echo "installed"

# 错误方式（会报错）
hcloud --version  # 不支持！
```

### 11.3 工号命名规范

- 要求：ECS 名称包含至少 6 位连续数字
- 匹配：`user-00123456-web`、`test123456vm`
- 不匹配：`web-server`、`test12345`

### 11.4 高危端口定义

| 端口 | 服务 | 风险等级 |
|------|------|---------|
| 22 | SSH 远程登录 | Critical |
| 3389 | RDP 远程桌面 | Critical |
| 3306 | MySQL | High |
| 5432 | PostgreSQL | High |
| 6379 | Redis | High |
| 27017 | MongoDB | High |

### 11.5 环境变量参考

| 变量名 | 必需 | 说明 |
|--------|------|------|
| HWCLOUD_ACCESS_KEY | 是 | Access Key ID |
| HWCLOUD_SECRET_KEY | 是 | Secret Access Key |
| HWCLOUD_REGIONS | 是 | 扫描区域，逗号分隔 |
| HWCLOUD_PROJECT_ID | 否 | IAM 子用户需要 |
| HTTP_PROXY | 否 | HTTP 代理 |
| HTTPS_PROXY | 否 | HTTPS 代理 |
| NO_PROXY | 否 | 代理例外地址 |

---

**文档版本**: 2.0
**更新日期**: 2026-04-08
