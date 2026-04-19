# Apprentice AI

> **以教促学** · Learning by Teaching

`Apprentice AI` 是一个英语语法学习平台。学生扮演"老师"，把语法规则和例子教给 AI 学生。AI 会记住每个学生独立教过的内容，教师再对 AI 进行批量测试——从而揭示学生自身理解的盲点。

---

## 核心流程

```
学生讲解语法 → AI 提取知识点写入记忆 → 教师出题 → AI 基于记忆作答 → 暴露学习漏洞
```

1. **Teach 区**：学生用自然语言教 AI，系统自动提取知识并合并到该学生的专属知识库
2. **自测区**：学生向 AI 提问或自己出选择题测试 AI（不写入记忆）
3. **知识库**：查看、编辑、追溯 AI 的每一条已学记忆
4. **教师测试**：上传题目，系统并行让所有学生的 AI 作答，横向对比
5. **班级分析**：教师查看全班知识覆盖率和每位学生的对话完整记录

---

## 截图

| 页面 | 说明 |
|------|------|
| ![Teach 区](docs/screenshots/teach.png) | 学生 Teach 区：对话 + 焦点芯片 + 知识面板 |
| ![知识库](docs/screenshots/knowledge.png) | 学生知识库：实时展示 AI 记忆及最近改动 |
| ![班级管理](docs/screenshots/class-manage.png) | 教师班级管理：课程范围编辑 + 学生列表 |
| ![分析面板](docs/screenshots/analytics.png) | 教师分析面板：学生知识覆盖热力图 |

> 📸 如需更新截图：启动前后端后截图并存入 `docs/screenshots/`。

---

## 本地开发

### 无需 API Key（推荐初次上手）

```bash
# 1. 后端
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env 中 MOCK_AI_ENABLED=true 已默认开启 — 无需 DeepSeek Key
uvicorn app.main:app --reload        # :8000

# 2. 前端（新终端）
cd frontend
npm install
cp .env.example .env                 # VITE_API_BASE_URL=http://localhost:8000
npm run dev                          # :5173
```

### 接入 DeepSeek API

在 `backend/.env` 中设置：

```ini
MOCK_AI_ENABLED=false
DEEPSEEK_API_KEY=your-key-here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

---

## Docker（一键启动）

```bash
cp backend/.env.example backend/.env   # 配置好 .env
docker compose up --build
```

---

## 服务器部署（生产）

```bash
cp deploy/.env.server.example deploy/.env.server
# 编辑 deploy/.env.server，填入：
#   POSTGRES_PASSWORD / JWT_SECRET / TEACHER_REG_CODE
#   FRONTEND_URL / CORS_ORIGINS（你的域名）
#   DEEPSEEK_API_KEY（已旋转的新 Key）

docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml logs -f
```

生产部署包含：PostgreSQL 持久化 · FastAPI + Worker 容器 · Nginx 静态前端 + `/api` 反代。

---

## 功能清单

### 学生端
- **Teach 区**：多会话对话，自动知识提取，"保存记忆"手动触发提取，焦点芯片（定义 / 基本结构 / 例子…），历史会话切换
- **AI 起名**：为每个班级的 AI 学生取专属名字（跨设备隔离，不会污染同班其他同学）
- **自测区**：自由问答 + 自建选择题，历史保留但不写入记忆，内容校验
- **知识库**：扁平展示所有规则与例句，直接编辑，对话修正跳转，最近改动日志

### 教师端
- **班级管理**：邀请码，课程范围 & 知识维度编辑器，学生列表
- **出卷 & 批测**：选择题 / 开放题，异步并行测试所有学生的 AI，实时状态
- **分析面板**：班级知识覆盖热力图，单个学生知识树 + 完整对话记录

### 后端
- JWT 认证，学生 / 教师双角色
- 每个 (学生, 班级) 独立 JSONB 知识库，语义合并（new / supplement / revise / ignore）
- 会话摘要（超过 20 轮自动摘要）+ 近 6 条消息滚动窗口
- 异步测试 Worker（数据库轮询，无需 Redis）
- 知识变更审计日志

---

## 说明

- `TEACHER_REG_CODE` 默认值见 `.env.example`，生产环境请务必修改
- 开发环境 `AUTO_CREATE_SCHEMA=true` 自动建表；生产环境请用 `alembic upgrade head`
- 测试：`cd backend && PYTHONPATH=. pytest tests/ -q`
