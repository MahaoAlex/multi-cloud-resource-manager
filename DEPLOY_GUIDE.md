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

# 验证安装
hcloud --help
```

### 1.3 获取华为云凭证

1. 登录华为云控制台
2. 进入 "我的凭证" -> "访问密钥"
3. 创建新的访问密钥，保存 AK 和 SK

## 二、Skills 部署

### 2.1 复制 Skills 到 Claude Code 目录

```bash
# 进入项目目录
cd /home/alex/codebase/multi-cloud-resource-manager

# 复制核心 Skills
cp -r skills/huaweicloud-core/proxy-injection ~/.claude/skills/
cp -r skills/huaweicloud-core/auth-manager ~/.claude/skills/

# 复制主 Skill
cp -r skills/huaweicloud-resource-manager ~/.claude/skills/

# 验证安装
ls -la ~/.claude/skills/
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
│   └── auth_manager.py
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
# 在 Claude Code 中执行
/restart
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

### 3.3 测试 auth-manager Skill

**场景：配置华为云认证信息**

在 Claude Code 中输入：

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

### 3.8 测试完整扫描

**场景：执行完整资源扫描**

在 Claude Code 中输入：

```
执行完整的华为云资源扫描
```

或使用命令模式：

```
/huaweicloud-scan --regions=all --mode=manual
```

预期交互：
```
Claude: 开始执行完整的华为云资源扫描...

═══════════════════════════════════════════════
  Huawei Cloud Resource Manager - 完整扫描
═══════════════════════════════════════════════

扫描区域: cn-north-4, cn-south-1, cn-east-2
扫描类型: manual
开始时间: 2026-04-08 14:40:00

───────────────────────────────────────────────
[1/5] VPC 盘点与使用分析
───────────────────────────────────────────────
[1/3] cn-north-4: 发现 8 VPC, 2 未使用 [OK]
[2/3] cn-south-1: 发现 5 VPC, 1 未使用 [OK]
[3/3] cn-east-2: 发现 3 VPC, 0 未使用 [OK]
VPC 扫描完成: 总计 16 VPC, 3 未使用

───────────────────────────────────────────────
[2/5] 安全组风险扫描
───────────────────────────────────────────────
[1/3] cn-north-4: 发现 3 个高危配置 [WARN]
[2/3] cn-south-1: 发现 1 个高危配置 [WARN]
[3/3] cn-east-2: 未发现风险 [OK]
安全扫描完成: 总计 4 个高危配置

───────────────────────────────────────────────
[3/5] OBS 公开访问检测
───────────────────────────────────────────────
[1/3] cn-north-4: 发现 2 个公开存储桶 [WARN]
[2/3] cn-south-1: 未发现异常 [OK]
[3/3] cn-east-2: 未发现异常 [OK]
OBS 扫描完成: 总计 2 个公开存储桶

───────────────────────────────────────────────
[4/5] ECS 资源优化检查
───────────────────────────────────────────────
[1/3] cn-north-4: 3 个低利用率, 2 个命名违规 [WARN]
[2/3] cn-south-1: 1 个低利用率 [WARN]
[3/3] cn-east-2: 无异常 [OK]
ECS 扫描完成: 4 个低利用率, 2 个命名违规

───────────────────────────────────────────────
[5/5] EIP 未挂载检测
───────────────────────────────────────────────
[1/3] cn-north-4: 发现 2 个未挂载 EIP [WARN]
[2/3] cn-south-1: 发现 1 个未挂载 EIP [WARN]
[3/3] cn-east-2: 无异常 [OK]
EIP 扫描完成: 总计 3 个未挂载 EIP

═══════════════════════════════════════════════
  扫描完成 - 汇总报告
═══════════════════════════════════════════════

扫描统计:
┌──────────────────────┬────────┐
│ 指标                  │ 数量   │
├──────────────────────┼────────┤
│ 扫描区域              │ 3      │
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

扫描用时: 125 秒
```

## 四、定时巡检配置

### 4.1 Cron 定时任务

每小时执行一次巡检：

```bash
# 编辑 crontab
crontab -e

# 添加以下行
0 * * * * cd /path/to/project && claude "/huaweicloud-scan --mode=scheduled --regions=all" >> /var/log/huaweicloud-scan.log 2>&1
```

### 4.2 Airflow DAG

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
        bash_command='cd /path/to/project && claude "/huaweicloud-scan --mode=scheduled --regions=all"',
    )

    scan_task
```

## 五、报告查看与处理

### 5.1 查看报告

```bash
# 查看 Markdown 报告
cat ./reports/2026-04-08/manual_14-40-00.md

# 查看 JSON 报告
cat ./reports/2026-04-08/scheduled_15-00-00.json | jq
```

### 5.2 集成到 IM 通知

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
    
    summary = data['summary']['total']
    
    message = {
        "msgtype": "markdown",
        "markdown": {
            "title": "华为云资源巡检报告",
            "text": f"""### 华为云资源巡检报告
**扫描时间**: {data['scan_metadata']['timestamp']}
**扫描区域**: {', '.join(data['scan_metadata']['regions'])}

**汇总统计**:
- VPC 总数: {summary['vpcs']} (未使用: {summary['unused_vpcs']})
- 安全问题: {summary['security_issues']}
- 公开 OBS: {summary['public_obs_buckets']}
- 低利用率 ECS: {summary['low_utilization_ecs']}
- 未挂载 EIP: {summary['unattached_eips']}

**待处理事项**: {len(data['action_items'])} 项

[点击查看详情](http://your-report-server/reports/)
"""
        }
    }
    
    requests.post(DINGTALK_WEBHOOK, json=message)

if __name__ == "__main__":
    send_report(sys.argv[1])
```

## 六、自定义规则

### 6.1 创建自定义规则文件

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
```

### 6.2 规则生效

自定义规则会自动生效，优先级高于内置规则。

## 七、故障排查

### 7.1 常见问题

**Q: hcloud 命令找不到**
```bash
# 检查 hcloud 是否在 PATH 中
which hcloud

# 如果没有，添加到 PATH
export PATH=$PATH:/usr/local/bin
```

**Q: 认证失败**
```bash
# 检查环境变量
echo $HWCLOUD_ACCESS_KEY
echo $HWCLOUD_SECRET_KEY
echo $HWCLOUD_REGIONS

# 手动测试 hcloud 连接
hcloud vpc ListVpcs --region=cn-north-4
```

**Q: 代理连接失败**
```bash
# 测试代理连接
curl -x http://proxy:8080 https://myhuaweicloud.com

# 检查 NO_PROXY 设置
echo $NO_PROXY
```

### 7.2 调试模式

在 Claude Code 中启用详细日志：

```
/huaweicloud-scan --debug
```

## 八、安全注意事项

1. **凭证保护**
   - AK/SK 仅存储在环境变量中
   - 不要提交到 Git 仓库
   - 定期轮换凭证

2. **报告安全**
   - 报告文件包含资源信息，注意访问控制
   - 定期清理历史报告（默认保留7天）

3. **操作安全**
   - 所有扫描操作均为只读
   - 删除操作需要人工确认
   - 生产环境建议先测试

## 九、附录

### 9.1 支持的华为云服务

| 服务 | 检测内容 |
|------|----------|
| VPC | 资源枚举、使用分析 |
| ECS | CPU 利用率、命名规范 |
| OBS | 公开存储桶、公开对象 |
| EIP | 未挂载检测 |
| Security Group | 高危端口开放 |

### 9.2 工号命名规范

- 要求：ECS 名称包含至少 6 位连续数字
- 匹配：`user-00123456-web`、`test123456vm`
- 不匹配：`web-server`、`test12345`

### 9.3 高危端口定义

- 22: SSH 远程登录
- 33: 未使用端口（常被滥用）
- 44: 未使用端口（常被滥用）

---

**文档版本**: 1.0
**更新日期**: 2026-04-08
