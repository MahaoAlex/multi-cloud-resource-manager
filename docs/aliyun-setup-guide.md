# 阿里云资源管理工具配置指导

## 概述

本文档介绍如何配置和使用阿里云资源管理工具（aliyun-resource-manager），用于扫描和管理阿里云资源。

## 前置要求

### 1. 安装阿里云CLI

```bash
# 下载并安装aliyun CLI
curl -O https://aliyuncli.alicdn.com/aliyun-cli-linux-latest-amd64.tgz
tar -xzf aliyun-cli-linux-latest-amd64.tgz
sudo mv aliyun /usr/local/bin/

# 验证安装
aliyun --version
```

### 2. 配置阿里云凭证

方式一：使用环境变量

```bash
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"
```

方式二：使用aliyun configure配置

```bash
aliyun configure
# 按提示输入Access Key ID和Access Key Secret
```

## 环境变量配置

### 必需环境变量

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `ALIYUN_ACCESS_KEY_ID` | 阿里云Access Key ID | LTAI5t8Z3y8Y7Z7Z7Z7Z7Z7Z |
| `ALIYUN_ACCESS_KEY_SECRET` | 阿里云Access Key Secret | xxxxxxxxxxxxxxxxxxxxxxxxxxx |
| `ALIYUN_REGIONS` | 扫描的Region列表，逗号分隔或使用'all' | cn-hangzhou,cn-shanghai |

### 可选环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `OSS_CHECK_OBJECTS` | 是否检查OSS对象级权限 | true |

## 配置示例

### 基础配置

```bash
# 设置凭证
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"

# 设置扫描区域（单个区域）
export ALIYUN_REGIONS="cn-hangzhou"

# 设置扫描区域（多个区域）
export ALIYUN_REGIONS="cn-hangzhou,cn-shanghai,cn-beijing"

# 扫描所有支持的区域
export ALIYUN_REGIONS="all"
```

### 支持的Region列表

| Region ID | 区域名称 |
|-----------|----------|
| cn-hangzhou | 华东1（杭州） |
| cn-shanghai | 华东2（上海） |
| cn-beijing | 华北2（北京） |
| cn-shenzhen | 华南1（深圳） |
| cn-qingdao | 华北1（青岛） |
| cn-zhangjiakou | 华北3（张家口） |
| cn-hongkong | 中国香港 |
| ap-southeast-1 | 新加坡 |
| ap-southeast-2 | 悉尼 |
| ap-northeast-1 | 东京 |
| us-west-1 | 硅谷 |
| us-east-1 | 弗吉尼亚 |
| eu-central-1 | 法兰克福 |

## 使用方法

### 1. 完整扫描

```bash
/aliyun-resource-manager full_scan
```

带参数扫描：

```bash
/aliyun-resource-manager full_scan \
  --regions=["cn-hangzhou","cn-shanghai"] \
  --scan_type="manual" \
  --output_dir="./reports"
```

### 2. 单独扫描VPC

```bash
/aliyun-resource-manager scan_vpcs --regions=["cn-hangzhou"]
```

### 3. 扫描安全组

```bash
/aliyun-resource-manager scan_security --regions=["cn-hangzhou"]
```

### 4. 扫描OSS

```bash
/aliyun-resource-manager scan_oss --regions=["cn-hangzhou"]
```

### 5. 扫描ECS

```bash
/aliyun-resource-manager scan_ecs \
  --regions=["cn-hangzhou"] \
  --cpu_threshold=10 \
  --check_naming=true
```

### 6. 扫描EIP

```bash
/aliyun-resource-manager scan_eips --regions=["cn-hangzhou"]
```

### 7. 列出所有规则

```bash
/aliyun-resource-manager list_rules
```

## 扫描结果

扫描报告将保存在 `./reports/YYYY-MM-DD/` 目录下：

- **手动扫描**：生成JSON和Markdown两种格式
- **定时扫描**：仅生成JSON格式

### 报告内容

报告包含以下信息：

1. **VPC分析**：未使用的VPC列表
2. **安全问题**：安全组开放端口配置
3. **OSS问题**：公开访问的存储桶
4. **ECS问题**：低CPU使用率和命名规范违规
5. **EIP问题**：未绑定的弹性IP
6. **行动建议**：按严重级别排序的待办事项

## 自定义规则

### 创建自定义规则文件

创建文件 `./rules/custom-rules.yaml`：

```yaml
rules:
  - id: custom-ec2-tag-check
    name: EC2 Instance Missing Cost Center Tag
    resource: ecs
    condition: 'tags !~ /CostCenter/'
    severity: warning
    description: ECS实例应包含CostCenter标签用于成本分摊
```

### 运行自定义规则

```bash
/aliyun-resource-manager run_custom_rule \
  --rule_file="./rules/custom-rules.yaml" \
  --resource_type="ecs"
```

## 常见问题

### 1. CLI未找到

**问题**：`aliyun CLI not found`

**解决**：确保aliyun CLI已安装并在PATH中

```bash
which aliyun
# 如果没有输出，重新安装并添加到PATH
```

### 2. 权限不足

**问题**：API调用返回权限错误

**解决**：确保Access Key具有足够的权限，需要以下权限：

- `AliyunECSReadOnlyAccess` - ECS只读权限
- `AliyunVPCReadOnlyAccess` - VPC只读权限
- `AliyunOSSReadOnlyAccess` - OSS只读权限
- `AliyunEIPReadOnlyAccess` - EIP只读权限
- `AliyunCloudMonitorReadOnlyAccess` - 云监控只读权限

### 3. Region配置错误

**问题**：无法获取某些Region的资源

**解决**：检查Region ID拼写，使用支持的Region列表中的值

## 服务对应关系

| 阿里云 | 华为云 | AWS |
|--------|--------|-----|
| VPC | VPC | VPC |
| ECS | ECS | EC2 |
| OSS | OBS | S3 |
| EIP | EIP | Elastic IP |
| 安全组 | 安全组 | Security Group |
| CMS | CES | CloudWatch |
| VSwitch | Subnet | Subnet |
| ENI | NIC | ENI |

## 注意事项

1. **API调用频率**：扫描会调用阿里云API，请注意API调用频率限制
2. **费用**：工具本身免费，但可能会产生少量的API调用费用
3. **数据安全**：扫描结果保存在本地，不会上传到任何远程服务器
4. **权限最小化**：建议使用只读权限的Access Key

## 更新日志

### v1.0.0

- 初始版本发布
- 支持VPC、安全组、OSS、ECS、EIP扫描
- 支持多Region扫描
- 支持自定义规则
