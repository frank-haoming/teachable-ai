# Apprentice AI 品牌与 v1 全量实施计划

## 摘要
- 品牌主名定为 `Apprentice AI`，副标题定为“以教促学英语语法平台”。
- 产品定位保持“学生教 AI 学生”，视觉方向走“课堂友好 + 精致美感”，不做冷硬 AI 平台风，也不做幼态化教育产品风。
- v1 仍按全量范围实施：认证、班级、Teach 对话、知识库、学生自测、教师批量测试、学习分析、长对话摘要、双入口知识修正、教师查看完整记录。
- 页面构建将使用 `ui-ux-pro-max` 产出的方向：课堂友好的教育产品配色、带一点编辑感的排版、Vue 友好的表单与可访问性约束。

## 品牌与页面
- 品牌锁定：
  - 英文主名：`Apprentice AI`
  - 中文副标题：`以教促学英语语法平台`
  - 对外一句话说明：`Teach an AI student. Learn by teaching.`
- Logo 方案默认做“图标 + 字标”双形态：
  - 图标语义：`对话气泡 + 打开的书页/卡片`，表达“教学对话”和“知识积累”
  - 风格：圆角、线性、轻几何，不做赛博发光、脑电纹路、机械机器人头
  - 使用位：
    - 顶部导航左上角 `40x40` 图标 + 字标
    - 登录/注册页居中品牌锁定版
    - 浏览器 favicon / App icon 使用纯图标版
- 主视觉默认配色：
  - Primary：`#0D9488`
  - Secondary：`#2DD4BF`
  - Accent/CTA：`#F97316`
  - Background：以暖白或浅青白为底，不用纯白大平铺
  - Text：深墨绿黑系，保证阅读稳定
- 字体默认：
  - 标题：`Crimson Pro`
  - 正文/UI：`Atkinson Hyperlegible`
  - 原则：标题有一点书卷气，正文与表单保持高可读性
- 页面结构默认：
  - 营销/入口页：`Hero -> 3步教学闭环 -> 产品界面预览 -> 教师/学生入口 -> 信任说明`
  - 应用内壳：左侧导航或顶部导航，核心页面保持清晰信息层级，不做复杂装饰
  - Teach 页：聊天区为主，知识面板为辅，右侧可折叠；输入区固定底部
- 页面实现前先用 `ui-ux-pro-max` 补一轮正式设计系统检索，产出 landing/auth/chat/dashboard 的统一视觉规则；实现完成后再按可访问性规则检查键盘交互、标签、焦点态。

## 接口与数据
- 前端使用 Vue 3 + Vite + Element Plus，后端使用 FastAPI + SQLAlchemy + Alembic + PostgreSQL，LLM 接入 DeepSeek；模型名和 API Key 全部走环境变量。
- `POST /api/auth/register` 增加 `teacher_reg_code`；只有 `role=teacher` 时校验共享注册码，注册码通过环境变量配置。
- `chat_sessions.session_type` 扩展为 `teach`、`student_test_free`、`student_test_mcq`；Teach 才触发知识提取与记忆更新。
- `chat_messages` 增加 `meta` JSONB，保存学生自测题干、选项、AI 选择等结构化数据；Teach 继续使用 `knowledge_extracted`。
- 新增 `knowledge_change_logs`，记录 `action=create/update/delete`、来源 `dialogue/direct_edit`、目标知识 ID、变更前后内容、操作者、时间；`ai_knowledge.version` 每次真实变更递增。
- 新增 `test_runs`，记录教师“对全班 AI 一键测试”的异步任务状态与进度；`POST /api/tests/papers/{id}/execute` 返回 `run_id`，`GET /api/tests/runs/{run_id}` 查询进度。
- 新增学生自测接口：创建/读取 session、发送自由问答、提交自建选择题、读取历史；学生自测保存记录但绝不写入知识库，也不做系统自动判分。
- 新增知识修正两组接口：对话式 `POST /api/knowledge/{class_id}/correct`；直接编辑式 `PUT /api/knowledge/items/{item_id}` 与 `DELETE /api/knowledge/items/{item_id}`。
- 教师端可读取学生的知识库、测试结果、Teach/Test 全部对话历史和基础分析数据。

## 实现要点
- Teach 流程固定为：学生消息入库 -> DeepSeek 提取知识 -> 语义合并已有知识 -> 更新 JSONB 知识库 -> 基于扁平知识生成学生型 AI 回复 -> 回复入库。
- 语义合并不引入 RAG；首版直接用 LLM 判断“新增/补充/改写/忽略”，与当前 JSONB 记忆模型保持一致。
- 长对话摘要只作用于 Teach；阈值默认 20 轮，后续上下文为 `System Prompt + 摘要 + 最近 6 轮消息`。
- 教师批量测试面向“全班每个学生的 AI”，后台异步执行并提供进度；v1 不引入 Redis，先用数据库任务表 + 后台 worker。
- 学生端页面：登录/注册、学生首页、Teach、知识库、自测；教师端页面：教师首页、班级管理、试卷管理、测试运行/结果、学习分析、学生详情。
- UI 组件需提前预留品牌组件：
  - `BrandMark`：图标占位或后续 SVG Logo
  - `BrandLockup`：Logo + `Apprentice AI` + 中文副标题
  - `AppShell`：统一导航、页头、品牌露出位
- 所有交互元素必须满足基础可访问性：键盘操作、可见焦点、表单标签完整，避免只靠 click 的假按钮。

## 测试计划
- 认证与权限：教师注册码校验、角色越权拦截、班级访问隔离正确。
- Teach 记忆：闲聊不入库；同义重复知识被合并；修正后知识版本与日志正确。
- 学生自测：自由问答与自建选择题均保存记录；两者都不会更新知识库；历史可回看。
- 教师批量测试：可为全班创建异步任务；任务进度可见；每个学生生成独立结果。
- 知识修正：对话修正和直接编辑都能更新知识并写日志；教师端可见变更痕迹。
- UI 与品牌：登录页、首页、Teach 页、教师页都正确显示品牌锁定；Logo 位在桌面和移动端不挤压；焦点态与表单标签通过检查。

## 假设与默认
- 当前先锁定 `Apprentice AI`，除非后续你明确要换名，否则实现中统一按这个品牌名和目录命名。
- Logo 首版可先用代码实现的 SVG 占位图标，后续再替换为正式设计稿，不阻塞开发。
- 页面风格默认优先“课堂友好 + 精致”，因此配色和排版不走紫色 AI 默认风，也不走过度卡通化路线。
- DeepSeek 作为唯一 LLM 提供方，但服务层保留 provider adapter，后续可替换模型而不改业务接口。
