# CloudBase (TCB) 配置指南

## 环境变量配置

在部署或本地测试前，需要配置以下环境变量：

### 必需配置

```bash
# 仓储提供商选择
export REPO_PROVIDER=tcb  # 使用CloudBase数据库

# CloudBase环境ID（在CloudBase控制台获取）
export TCB_ENV_ID=your-env-id

# 腾讯云API密钥（在访问管理控制台获取）
export TCB_SECRET_ID=your-secret-id
export TCB_SECRET_KEY=your-secret-key

# CloudBase区域（可选，默认使用环境配置）
export TCB_REGION=ap-guangzhou  # 或 ap-shanghai, ap-beijing 等
```

### 可选配置

```bash
# 临时密钥Token（使用临时密钥时需要）
export TCB_TOKEN=your-temp-token
```

## 获取密钥步骤

### 1. 创建CloudBase环境

1. 登录 [腾讯云CloudBase控制台](https://console.cloud.tencent.com/tcb)
2. 创建新环境或选择现有环境
3. 记录环境ID（格式如：`env-abc123xyz`）

### 2. 获取API密钥

1. 登录 [腾讯云访问管理控制台](https://console.cloud.tencent.com/cam/capi)
2. 创建或查看API密钥
3. 复制 SecretId 和 SecretKey

### 3. 创建数据库集合

在CloudBase数据库中创建以下集合：

```
users          - 用户信息
content        - 学习内容
progress       - 学习进度
vocab          - 生词本
plans          - 学习计划
orders         - 订单记录
events         - 事件埋点
wishlists      - 升级愿望单
```

### 4. 配置安全规则

参考 `cloudbase/security.rules.json` 配置数据库访问权限。

### 5. 创建索引

参考 `cloudbase/collections.indexes.json` 创建必要的数据库索引。

## 验证连接

### 方法1：使用验证脚本

```bash
cd backend
python scripts/verify_tcb_connection.py
```

### 方法2：手动验证

```python
from app.infra.config import settings
from app.infra.tcb_client import TCBClient

# 创建客户端
client = TCBClient.from_settings(settings)

# 测试查询
docs, total = client.query("users", filters={}, limit=1, offset=0)
print(f"连接成功！查询到 {total} 条用户记录")
```

## 故障排查

### 错误：TCB secret not configured

**原因**：未设置 `TCB_SECRET_ID` 或 `TCB_SECRET_KEY`

**解决**：
```bash
export TCB_SECRET_ID=your-secret-id
export TCB_SECRET_KEY=your-secret-key
```

### 错误：TCB_ENV_ID is required

**原因**：未设置环境ID

**解决**：
```bash
export TCB_ENV_ID=your-env-id
```

### 错误：Authentication failed

**原因**：密钥错误或权限不足

**解决**：
1. 确认密钥正确性
2. 检查API密钥是否有CloudBase访问权限
3. 在访问管理控制台授予 `QcloudTCBFullAccess` 权限

### 错误：Collection not found

**原因**：数据库集合未创建

**解决**：在CloudBase控制台手动创建集合

## 本地开发配置

创建 `.env` 文件：

```bash
# backend/.env
REPO_PROVIDER=memory  # 本地开发使用内存仓储
# REPO_PROVIDER=tcb   # 切换到TCB仓储时取消注释

# CloudBase配置（仅在REPO_PROVIDER=tcb时需要）
TCB_ENV_ID=env-xxx
TCB_SECRET_ID=AKIDxxx
TCB_SECRET_KEY=xxx
TCB_REGION=ap-guangzhou
```

加载环境变量：

```bash
# Linux/Mac
export $(cat .env | xargs)

# Windows PowerShell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^#][^=]+)=(.+)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
```

## 生产部署配置

### 云函数（SCF）部署

在云函数环境变量中配置：

```
REPO_PROVIDER=tcb
TCB_ENV_ID=<your-prod-env-id>
TCB_SECRET_ID=<your-secret-id>
TCB_SECRET_KEY=<your-secret-key>
TCB_REGION=ap-guangzhou
```

### Docker部署

```dockerfile
ENV REPO_PROVIDER=tcb
ENV TCB_ENV_ID=<your-env-id>
ENV TCB_SECRET_ID=<your-secret-id>
ENV TCB_SECRET_KEY=<your-secret-key>
```

或使用 `-e` 参数：

```bash
docker run -d \
  -e REPO_PROVIDER=tcb \
  -e TCB_ENV_ID=<your-env-id> \
  -e TCB_SECRET_ID=<your-secret-id> \
  -e TCB_SECRET_KEY=<your-secret-key> \
  your-app-image
```

## 安全注意事项

1. ⚠️ **永不在代码中硬编码密钥**
2. 🔐 **使用环境变量或密钥管理服务**
3. 🛡️ **定期轮换API密钥**
4. 📝 **限制API密钥权限范围**
5. 🚫 **不要将`.env`文件提交到版本控制**

## 性能优化建议

1. **索引优化**：为常用查询字段创建索引
2. **查询优化**：使用精确匹配而非全表扫描
3. **批量操作**：使用批量API减少请求次数
4. **缓存策略**：对热点数据添加缓存层
5. **连接池**：复用HTTP连接减少握手开销

## 监控与日志

建议配置以下监控指标：

- TCB API调用成功率
- TCB API响应延迟
- 数据库查询QPS
- 错误率和错误类型分布

日志会记录在应用日志中，包含：
- 请求ID追踪
- API调用详情
- 错误堆栈信息
