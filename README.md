# Apprentice AI

`Apprentice AI` 是一个“以教促学”英语语法平台。学生扮演老师去教 AI 学生，系统把 Teach 对话、AI 记忆、自测、教师批量测试和学习分析串成一套完整流程。

## 目录

- `backend/`: FastAPI + SQLAlchemy + PostgreSQL/SQLite
- `frontend/`: Vue 3 + Vite + Element Plus
- `design-system/apprentice-ai/`: 品牌与页面设计系统

## 本地开发

1. 后端：
   - `cd backend`
   - `python3 -m venv .venv`
   - `source .venv/bin/activate`
   - `pip install -r requirements.txt`
   - `cp .env.example .env`
   - `uvicorn app.main:app --reload`
2. 前端：
   - `cd frontend`
   - `npm install`
   - `cp .env.example .env`
   - `npm run dev`

## Docker

先执行 `cp backend/.env.example backend/.env` 并填好正式配置，再运行 `docker compose up --build`。
Docker Compose 会读取 `backend/.env`，并同时启动 PostgreSQL、FastAPI 和 Vite 开发服务器。

## 服务器部署

如果服务器已经安装了 Docker CE，建议直接使用生产部署文件：

1. `cp deploy/.env.server.example deploy/.env.server`
2. 编辑 `deploy/.env.server`
   - 把 `POSTGRES_PASSWORD`、`JWT_SECRET`、`TEACHER_REG_CODE` 改成你自己的值
   - 把 `FRONTEND_URL` 和 `CORS_ORIGINS` 改成你的域名；如果暂时没有域名，可以先填 `http://你的服务器IP`
   - 把 `DEEPSEEK_API_KEY` 换成你已经旋转过的新 key
3. 在项目根目录运行：
   - `docker compose -f docker-compose.prod.yml up -d --build`
4. 查看状态：
   - `docker compose -f docker-compose.prod.yml ps`
   - `docker compose -f docker-compose.prod.yml logs -f`

生产部署文件会：
- 使用 PostgreSQL 容器持久化数据
- 使用单个 FastAPI 后端容器承载 API 和测试 worker
- 将前端构建为静态文件并由 Nginx 对外提供服务
- 通过 Nginx 将 `/api` 反向代理到后端容器

## 当前实现范围

- 品牌系统：`Apprentice AI` Logo 位、Favicon、品牌壳与页面视觉基线
- 认证：学生注册 / 教师注册码注册 / 登录 / 当前用户
- 班级：创建、加入、详情、二维码邀请码
- 对话：Teach、学生自由自测、学生 MCQ 自测
- 知识库：提取、扁平查看、对话修正、直接编辑、删除、修正日志
- 教师测试：试卷、题目、异步测试任务、结果查看
- 教师分析：班级概览、学生概览、单个学生详情和完整对话

## 说明

- 默认 `MOCK_AI_ENABLED=true`，在没有配置 DeepSeek API Key 时也可以跑通主要流程。
- 当前后台异步测试 worker 基于数据库任务表和应用内轮询，不依赖 Redis。
- 初始 schema 默认由应用启动时自动创建；如需切 Alembic，可在此基础上继续补 migration。
