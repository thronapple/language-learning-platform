[English](./README_EN.md) | 中文

# LangPod - 语言学习平台

微信小程序语言学习应用，提供自适应测评、场景对话练习、SRS 词汇复习和个性化学习计划。

## 功能概览

- **自适应水平测评** — 基于 IRT 算法的英语水平评估，覆盖 A1-C2 全级别
- **场景对话练习** — 旅行、商务、学术、日常等 10+ 真实场景，多轮对话配音频
- **SRS 词汇管理** — 间隔重复记忆系统，智能安排复习时间
- **学习计划** — 根据测评结果生成个性化学习路径，追踪连续打卡
- **内容导入/导出** — 支持从文本或 URL 导入学习内容，导出学习卡片
- **TTS 语音合成** — Edge TTS 生成自然发音音频

## 技术架构

```
miniprogram/          # 微信小程序前端 (WXML/WXSS/TypeScript)
├── pages/            # 15 个页面
├── components/       # 9 个可复用组件
├── services/         # API 服务层
├── store/            # 全局状态管理
└── custom-tab-bar/   # 自定义底部导航

backend/              # FastAPI 后端
├── app/
│   ├── domain/       # 领域模型
│   ├── infra/        # 基础设施 (配置/中间件/JWT/限流)
│   ├── repositories/ # 数据访问层 (内存/云开发)
│   ├── routes/       # 路由模块
│   ├── schemas/      # 请求/响应模型
│   └── services/     # 业务逻辑层
└── tests/            # 测试用例

data/                 # 种子数据 (题库/对话/场景)
```

## 快速开始

### 环境要求

- Python 3.11+
- [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
- FFmpeg（音频处理）

### 后端启动

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置必要参数

# 启动服务
uvicorn app.main:app --reload --port 8000
```

服务启动后访问 `http://localhost:8000/docs` 查看 API 文档。

### 前端启动

1. 用微信开发者工具打开 `miniprogram/` 目录
2. 在 `app.js` 中配置后端地址
3. 编译运行

### Docker 部署

```bash
cd backend
docker build -t langpod-backend .
docker run -p 80:80 --env-file .env langpod-backend
```

## API 概览

| 模块 | 端点 | 说明 |
|------|------|------|
| 认证 | `POST /auth/me` | 微信登录，返回 JWT |
| 内容 | `GET /content` | 学习内容列表 |
| 词汇 | `POST /vocab` | 添加生词 |
| 词汇 | `GET /vocab/due` | 获取待复习词汇 |
| 测评 | `POST /api/assessment/start` | 开始水平测评 |
| 场景 | `POST /api/scenarios/start` | 开始场景学习 |
| 计划 | `GET /plan/stats` | 学习统计 |
| 导入 | `POST /import` | 导入文本/URL 内容 |

完整 API 文档见 `/docs` 端点 (Swagger UI)。

## 配置说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ENV` | 运行环境 | `dev` |
| `REPO_PROVIDER` | 数据存储 (`memory` / `tcb`) | `memory` |
| `JWT_SECRET` | JWT 签名密钥 | 开发默认值 |
| `WECHAT_AUTH_ENABLED` | 启用微信真实登录 | `false` |
| `STORAGE_PROVIDER` | 文件存储 (`local` / `cos`) | `local` |

## 测试

```bash
cd backend
pytest
```

## 项目状态

MVP 功能已全部完成，59+ 测试通过。

### 生产部署清单

- [ ] 配置 `REPO_PROVIDER=tcb` 及云开发凭据
- [ ] 设置生产级 `JWT_SECRET`
- [ ] 微信后台配置服务器域名白名单
- [ ] 启用微信登录认证
- [ ] 部署至微信云托管

## 许可证

MIT
