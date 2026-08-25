# 📌 网址收藏夹（Bookmarks Web）

一个自托管的「网址收藏夹」：贴入网址即可收藏，自动抓取网页标题与正文并转成 Markdown 保存，支持分类、标签、搜索、拖拽排序，数据持久化在 MySQL。前端 Vue 3，后端 Python（FastAPI），Docker 一键部署。

## ✨ 功能特性

- **贴网址即收藏**：自动抓取网页标题、描述、favicon。
- **正文转 Markdown**：用 trafilatura（+ readability 兜底）提取正文并转 Markdown，可随时「重新抓取」。
- **分类 + 标签**：分类支持层级；标签多对多；两者都支持**右键重命名/删除**、**折叠/展开**，且**可手动输入新名称自动创建**。
- **关键词搜索**：检索标题 / 描述 / 正文。
- **完整 CRUD**：新增、查看、编辑、删除、星标。
- **拖拽排序**：「全部 / 分类 / 标签」视图下可拖拽卡片排序，各作用域排序互相独立、持久化。
- **计数实时刷新**：新增/删除/编辑书签后，侧边栏分类与标签数量即时更新。
- **数据持久化**：MySQL 8.0 + Docker volume，重启/重建容器数据不丢。
- **安全**：抓取任意网址带 SSRF 防护（拦截内网/保留地址）、体积与超时限制。

## 🧱 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vite + TypeScript + Element Plus + Pinia + Vue Router + Axios + SortableJS + markdown-it |
| 后端 | Python 3.12 + FastAPI + SQLAlchemy 2.0（异步）+ asyncmy |
| 抓取 | httpx + trafilatura + readability-lxml + markdownify + BeautifulSoup4 |
| 数据库 | MySQL 8.0 |
| 部署 | Docker Compose + Nginx |

## 📁 目录结构

```
Bookmarks-Web/
├── docker-compose.yml        # 三服务编排（mysql / backend / frontend）
├── .env.example              # 环境变量模板（复制为 .env 后改密码）
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py           # FastAPI 入口 + 启动建表/轻量迁移
│       ├── config.py         # 配置（读环境变量）
│       ├── database.py       # 异步引擎/会话
│       ├── models.py         # ORM 模型（bookmarks/categories/tags/bookmark_order）
│       ├── schemas.py        # Pydantic 模型
│       ├── routers/          # bookmarks / tags / categories
│       └── services/         # fetcher / extractor / ssrf
└── frontend/
    ├── Dockerfile            # 多阶段：node 构建 → nginx 托管
    ├── package.json
    ├── vite.config.ts        # dev 代理 /api → localhost:8000
    ├── nginx.conf            # 静态托管 + /api 反代到 backend
    └── src/
        ├── views/            # 列表页 / 详情页
        ├── components/       # 侧边栏 / 顶栏 / 卡片 / 弹窗
        ├── stores/           # bookmarks / meta（Pinia）
        └── api/              # axios 封装
```

## 🚀 Docker 一键部署（云服务器）

前置：服务器已安装 Docker 与 Docker Compose（Docker 20.10+）。

```bash
# 1. 进入项目目录
cd Bookmarks-Web

# 2. 准备环境变量（复制模板并修改密码）
cp .env.example .env
# 编辑 .env，至少修改 MYSQL_ROOT_PASSWORD 和 DB_PASSWORD

# 3. 构建并启动
docker compose up -d --build

# 4. 查看状态（三个服务都应为 running/healthy）
docker compose ps
```

启动后浏览器访问 **`http://服务器IP`**（默认 80 端口）即可使用。

常用命令：

```bash
docker compose logs -f backend     # 查看后端日志
docker compose down                # 停止（数据仍在 ./data/mysql）
docker compose up -d --build       # 更新代码后重建并启动
```

数据持久化在 `./data/mysql`（挂载卷），删除容器/重建都不丢数据。

## 🛠 本地开发

需要本机或 Docker 起一个 MySQL（可只启动 mysql 容器）：

```bash
docker compose up -d mysql
```

**后端**（另开终端）：

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# 确保 .env 里的 DB_HOST=127.0.0.1（本机连接）
uvicorn app.main:app --reload
```

后端 API 文档（Swagger）：http://localhost:8000/docs

**前端**（另开终端）：

```bash
cd frontend
npm install
npm run dev     # http://localhost:5173 ，已配置 /api 代理到 8000
```

## ⚙️ 配置说明

`.env`（部署用，Docker Compose 读取）：

| 变量 | 说明 |
|---|---|
| `MYSQL_ROOT_PASSWORD` | MySQL root 密码 |
| `DB_NAME` | 业务库名（默认 bookmarks） |
| `DB_USER` | 业务账号 |
| `DB_PASSWORD` | 业务账号密码 |

后端运行时还会读取环境变量 `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME`（docker-compose 已自动注入，本地开发时可在 `.env` 里设 `DB_HOST=127.0.0.1`）。

抓取相关参数在 `backend/app/config.py`（超时、体积上限、重定向上限、User-Agent），如需调整可改默认值或设环境变量。

## ❓ 常见问题

**1. 国内构建/拉取镜像慢或失败？**
在 Docker Desktop 的 Docker Engine 配置里设置镜像加速，例如：
```json
"registry-mirrors": ["https://docker.1ms.run", "https://docker.m.daocloud.io"]
```
后端 `Dockerfile` 已用清华 PyPI 源、前端已用 npmmirror 加速依赖安装。

**2. 后端启动报 `cryptography` 相关错误？**
确保 `requirements.txt` 里包含 `cryptography`（已内置），这是 asyncmy 连 MySQL 8 的 `caching_sha2_password` 认证所需。

**3. 贴网址报「抓取失败 / 网络请求失败」？**
- 确认目标网址可访问、是静态网页（本项目是「静态优先」抓取，JS 动态渲染的 SPA 站点可能抓不到正文，但书签仍会保存）。
- 内网地址、无效域名会被 SSRF 校验拦截（属正常保护）。

**4. 某些网页正文抓取不完整？**
正文提取为三级降级：trafilatura(Markdown) → readability → 整页文本。可在详情页点「重新抓取」重试。

**5. 如何改端口？**
编辑 `docker-compose.yml` 里 frontend 的 `ports`，例如 `"8080:80"`，然后 `docker compose up -d`。

## 📄 License

MIT
