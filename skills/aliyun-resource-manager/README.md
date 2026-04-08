# Aliyun Resource Manager

阿里云资源管理器 Claude Code Skill。

## 完整文档

详见项目文档：[阿里云完整使用指南](../../docs/aliyun-complete-guide.md)

## 快速开始

```bash
# 设置环境变量
export ALIYUN_ACCESS_KEY_ID="your-access-key-id"
export ALIYUN_ACCESS_KEY_SECRET="your-access-key-secret"
export ALIYUN_REGIONS="cn-hangzhou,cn-shanghai"

# 执行完整扫描
/aliyun-resource-manager full_scan --regions=["cn-hangzhou"] --max_workers=3 --vpc_max_workers=3
```

## 环境变量

| 变量 | 说明 |
|------|------|
| `ALIYUN_ACCESS_KEY_ID` | Access Key ID |
| `ALIYUN_ACCESS_KEY_SECRET` | Access Key Secret |
| `ALIYUN_REGIONS` | 区域列表或 'all' |

## 许可证

MIT
