# QuantFlow Backend

QuantFlow 量化交易平台后端 API，基于 FastAPI + SQLAlchemy (async) + PostgreSQL (asyncpg)。

## 快速开始

### 1) 安装依赖

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
```

### 2) 配置环境变量

复制 `.env.example` 为 `.env` 并修改至少以下配置：

- `DATABASE_URL` (PostgreSQL，格式：`postgresql+asyncpg://user:pass@host:port/db?ssl=require`)
- `SECRET_KEY` (生产环境务必替换)
- `DEBUG` (生产建议 `False`)

### 3) 启动服务

```bash
.\.venv\Scripts\python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

启动后访问：

- Swagger UI: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## 管理员账号

后端不会自动创建默认管理员账号。

使用脚本创建初始管理员（从 `backend/` 目录执行）：

```bash
.\.venv\Scripts\python scripts/create_admin.py --username admin --email admin@example.com
```

密码可通过 `--password` / `ADMIN_PASSWORD` 传入，或运行时安全输入。

## 数据库与迁移 (Alembic)

- 开发环境：当 `DEBUG=True` 时，应用启动会自动 `create_all` 创建缺失表（仅建议用于开发/测试）。
- 生产环境：建议使用 Alembic 管理迁移。

常用命令（从 `backend/` 目录执行）：

```bash
.\.venv\Scripts\python -m alembic upgrade head
```

如果你的数据库已经存在表结构（曾经通过 `create_all` 或手工建表创建），可以先基线标记：

```bash
.\.venv\Scripts\python -m alembic stamp head
```

## 测试

```bash
cd backend
.\.venv\Scripts\python -m pytest
```

## Webhook 示例

```bash
curl -X POST "http://localhost:8000/api/webhook/receive" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "buy",
    "ticker": "BTCUSDT",
    "order_type": "market",
    "quantity": 0.05,
    "passphrase": "your_tradingview_passphrase",
    "exchange": "okx",
    "leverage": 3,
    "strategy_id": 1
  }'
```

