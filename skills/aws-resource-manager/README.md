# AWS Resource Manager

AWS 资源管理器 Claude Code Skill。

## 完整文档

详见项目文档：[AWS 完整使用指南](../../docs/aws-complete-guide.md)

## 快速开始

```bash
# 设置环境变量
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGIONS="us-east-1,us-west-2"

# 执行完整扫描
/aws-resource-manager full_scan --regions=["us-east-1"] --max_workers=3 --vpc_max_workers=3
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `AWS_ACCESS_KEY_ID` | Access Key ID |
| `AWS_SECRET_ACCESS_KEY` | Secret Access Key |
| `AWS_REGIONS` | 区域列表或 'all' |

## 许可证

MIT
