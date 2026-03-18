# AI Trading 量化交易平台 - 技术方案设计文档

## 一、前端业务模块分析

### 1.1 页面结构概览

| 视图 | 文件路径 | 功能描述 |
|------|----------|----------|
| 首页 | `home-view.tsx` | 展示平台介绍、统计数据、实时动态、实时交易信号 |
| 策略大厅 | `marketplace-view.tsx` | 展示可订阅策略列表、策略详情、支付订阅 |
| 控制台 | `dashboard-view.tsx` | 用户个人中心：订阅管理、信号日志、Webhook配置 |
| 接入文档 | `docs-view.tsx` | 接入指南、FAQ |

### 1.2 需要动态交互的业务模块

#### 1.2.1 首页 (HomeView)
- **平台统计数据展示**：累计交易额、活跃用户数、系统在线率、信号延迟（需从后端获取实时/准实时数据）
- **实时交易信号**：展示最新的交易信号列表（BUY/SELL、交易对、价格、收益、时间）
- **社区动态**：展示用户评论/反馈（可后期接入真实数据）

#### 1.2.2 策略大厅 (MarketplaceView)
- **策略列表展示**：策略名称、描述、年化收益(APY)、最大回撤、胜率、价格、标签
- **策略订阅支付**：
  - 展示支付二维码（USDT-TRC20）
  - 支持连接钱包支付
  - 需要支持包月/包年订阅模式
  - 需要支持分润比例设置

#### 1.2.3 控制台 (DashboardView)
- **用户统计卡片**：活跃订阅数、本月收益、今日信号数、运行时长
- **活跃订阅管理**：展示用户当前订阅的策略列表（名称、状态、剩余天数）
- **TradingView Webhook配置**：
  - 展示Webhook Payload模板
  - 复制Payload功能
  - 发送测试信号
- **信号日志**：展示历史信号记录（时间、方向、交易对、价格、状态）
- **交易所API绑定**：（文档中提到，但UI中暂未完全展示）

#### 1.2.4 接入文档 (DocsView)
- 静态内容，无需动态数据

---

## 二、数据库模型设计

### 2.1 数据表总览

```
用户模块：users（用户表）
策略模块：strategies（策略表）、strategy_subscriptions（策略订阅表）
支付模块：payments（支付记录表）、subscription_plans（订阅套餐表）
交易模块：exchange_apis（交易所API表）、signal_logs（信号日志表）、webhook_configs（Webhook配置表）
信号模块：trading_signals（交易信号表）、signal_executions（信号执行记录表）
分润模块：profit_sharing_rules（分润规则表）、profit_sharing_records（分润记录表）
```

### 2.2 详细表结构

#### 2.2.1 用户表 (users)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| username | VARCHAR(50) | 用户名 |
| email | VARCHAR(100) | 邮箱 |
| password_hash | VARCHAR(255) | 密码哈希 |
| wallet_address | VARCHAR(100) | 钱包地址（用于支付） |
| role | ENUM | 角色：user/admin |
| status | ENUM | 状态：active/suspended |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### 2.2.2 策略表 (strategies)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| name | VARCHAR(100) | 策略名称（如：BTC趋势跟踪） |
| description | TEXT | 策略描述 |
| apy | DECIMAL(10,2) | 年化收益率 |
| max_drawdown | DECIMAL(10,2) | 最大回撤 |
| win_rate | DECIMAL(5,2) | 胜率 |
| monthly_price | DECIMAL(10,2) | 月订阅价格（USDT） |
| yearly_price | DECIMAL(10,2) | 年订阅价格（USDT） |
| tag | VARCHAR(20) | 标签（热门/稳健/专业等） |
| status | ENUM | 状态：active/inactive |
| created_at | TIMESTAMP | 创建时间 |

#### 2.2.3 订阅套餐表 (subscription_plans)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| strategy_id | UUID | 外键-策略ID |
| plan_type | ENUM | 套餐类型：monthly/yearly |
| price | DECIMAL(10,2) | 价格（USDT） |
| duration_days | INT | 订阅时长（天） |
| profit_share_percent | DECIMAL(5,2) | 分润比例（%） |
| description | VARCHAR(255) | 套餐描述 |
| is_active | BOOLEAN | 是否启用 |

#### 2.2.4 策略订阅表 (strategy_subscriptions)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键-用户ID |
| strategy_id | UUID | 外键-策略ID |
| plan_id | UUID | 外键-套餐ID |
| start_date | TIMESTAMP | 订阅开始时间 |
| end_date | TIMESTAMP | 订阅结束时间 |
| status | ENUM | 状态：active/expired/cancelled |
| profit_share_percent | DECIMAL(5,2) | 实际分润比例 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### 2.2.5 支付记录表 (payments)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键-用户ID |
| subscription_id | UUID | 外键-订阅ID |
| amount | DECIMAL(10,2) | 支付金额（USDT） |
| payment_method | ENUM | 支付方式：nowpayments/manual_wallet |
| tx_hash | VARCHAR(100) | 交易哈希（链上交易ID） |
| status | ENUM | 状态：pending/completed/failed/refunded |
| paid_at | TIMESTAMP | 支付时间 |
| verified_at | TIMESTAMP | 验证时间 |
| verified_by | UUID | 审核人ID（人工审核时使用） |
| created_at | TIMESTAMP | 创建时间 |

#### 2.2.6 交易所API表 (exchange_apis)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键-用户ID |
| exchange | ENUM | 交易所：okx/binance |
| api_key | VARCHAR(255) | API密钥（AES加密存储） |
| api_secret | VARCHAR(255) | API密钥（AES加密存储） |
| passphrase | VARCHAR(255) | Passphrase（OKX需要，AES加密） |
| is_active | BOOLEAN | 是否启用 |
| last_verified_at | TIMESTAMP | 最后验证时间 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### 2.2.7 Webhook配置表 (webhook_configs)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键-用户ID |
| strategy_id | UUID | 外键-策略ID |
| webhook_url | VARCHAR(255) | Webhook接收地址 |
| secret_key | VARCHAR(255) | 密钥（用于验证请求） |
| allowed_ips | TEXT | 允许的IP白名单（JSON数组） |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### 2.2.8 交易信号表 (trading_signals)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| strategy_id | UUID | 外键-策略ID |
| action | ENUM | 动作：buy/sell |
| ticker | VARCHAR(20) | 交易对（如：BTCUSDT） |
| order_type | ENUM | 订单类型：market/limit |
| quantity | DECIMAL(20,8) | 数量 |
| price | DECIMAL(20,8) | 价格 |
| leverage | INT | 杠杆倍数 |
| exchange | ENUM | 交易所：okx/binance |
| raw_payload | JSON | 原始Webhook Payload |
| received_at | TIMESTAMP | 接收时间 |
| processed_at | TIMESTAMP | 处理时间 |
| status | ENUM | 状态：pending/processing/completed/failed |

#### 2.2.9 信号执行记录表 (signal_executions)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| signal_id | UUID | 外键-信号ID |
| user_id | UUID | 外键-用户ID |
| subscription_id | UUID | 外键-订阅ID |
| exchange_api_id | UUID | 外键-交易所API ID |
| order_id | VARCHAR(100) | 交易所订单ID |
| executed_price | DECIMAL(20,8) | 实际成交价格 |
| executed_quantity | DECIMAL(20,8) | 实际成交数量 |
| execution_status | ENUM | 状态：success/failed/partial |
| error_message | TEXT | 错误信息 |
| executed_at | TIMESTAMP | 执行时间 |
| created_at | TIMESTAMP | 创建时间 |

#### 2.2.10 分润规则表 (profit_sharing_rules)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| strategy_id | UUID | 外键-策略ID |
| plan_type | ENUM | 套餐类型：monthly/yearly |
| share_percent | DECIMAL(5,2) | 分润比例（%） |
| min_profit_threshold | DECIMAL(20,8) | 最小盈利阈值 |
| is_active | BOOLEAN | 是否启用 |
| created_at | TIMESTAMP | 创建时间 |

#### 2.2.11 分润记录表 (profit_sharing_records)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| user_id | UUID | 外键-用户ID |
| strategy_id | UUID | 外键-策略ID |
| subscription_id | UUID | 外键-订阅ID |
| period_start | DATE | 结算周期开始 |
| period_end | DATE | 结算周期结束 |
| total_profit | DECIMAL(20,8) | 总盈利（USDT） |
| platform_share | DECIMAL(20,8) | 平台分润（USDT） |
| user_share | DECIMAL(20,8) | 用户保留（USDT） |
| status | ENUM | 状态：pending/paid |
| paid_at | TIMESTAMP | 支付时间 |
| created_at | TIMESTAMP | 创建时间 |

#### 2.2.12 系统统计表 (system_stats)
| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | UUID | 主键 |
| stat_date | DATE | 统计日期 |
| total_volume | DECIMAL(20,8) | 累计交易额 |
| active_users | INT | 活跃用户数 |
| total_signals | INT | 总信号数 |
| avg_latency_ms | INT | 平均延迟（毫秒） |
| created_at | TIMESTAMP | 创建时间 |

---

## 三、RESTful API 接口规划

### 3.1 接口总览

```
认证模块：/api/auth/*
用户模块：/api/users/*
策略模块：/api/strategies/*
支付模块：/api/payments/*
订阅模块：/api/subscriptions/*
交易所模块：/api/exchanges/*
Webhook模块：/api/webhook/*
信号模块：/api/signals/*
统计模块：/api/stats/*
```

### 3.2 详细接口定义

#### 3.2.1 认证模块 (/api/auth)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| POST | /api/auth/logout | 用户登出 |
| POST | /api/auth/refresh | 刷新Token |
| GET | /api/auth/me | 获取当前用户信息 |

#### 3.2.2 用户模块 (/api/users)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/users/profile | 获取用户资料 |
| PUT | /api/users/profile | 更新用户资料 |
| PUT | /api/users/wallet | 更新钱包地址 |

#### 3.2.3 策略模块 (/api/strategies)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/strategies | 获取策略列表（支持分页、筛选） |
| GET | /api/strategies/:id | 获取策略详情 |
| GET | /api/strategies/:id/plans | 获取策略订阅套餐 |

#### 3.2.4 支付模块 (/api/payments)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/payments/create | 创建支付订单 |
| POST | /api/payments/verify | 提交TxHash验证（人工审核模式） |
| GET | /api/payments/history | 获取支付历史 |
| GET | /api/payments/:id | 获取支付详情 |

**NowPayments回调接口**
| 方法 | 路径 | 描述 |
|------|------|------|
| POST | /api/payments/nowpayments/callback | NowPayments支付回调 |

#### 3.2.5 订阅模块 (/api/subscriptions)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/subscriptions | 获取用户订阅列表 |
| POST | /api/subscriptions | 创建订阅（支付后调用） |
| PUT | /api/subscriptions/:id/cancel | 取消订阅 |
| GET | /api/subscriptions/:id | 获取订阅详情 |

#### 3.2.6 交易所模块 (/api/exchanges)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/exchanges/apis | 获取用户绑定的API列表 |
| POST | /api/exchanges/apis | 绑定交易所API |
| PUT | /api/exchanges/apis/:id | 更新交易所API |
| DELETE | /api/exchanges/apis/:id | 删除交易所API |
| POST | /api/exchanges/apis/:id/verify | 验证API连接 |

#### 3.2.7 Webhook模块 (/api/webhook)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/webhook/config | 获取用户Webhook配置 |
| POST | /api/webhook/config | 创建/更新Webhook配置 |
| POST | /api/webhook/test | 发送测试信号 |
| POST | /api/webhook/receive | **接收TradingView信号（公开接口，需IP白名单+Secret验证）** |

#### 3.2.8 信号模块 (/api/signals)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/signals | 获取信号日志（当前用户） |
| GET | /api/signals/recent | 获取最近信号（公开，用于首页展示） |
| GET | /api/signals/:id | 获取信号详情 |
| GET | /api/signals/:id/executions | 获取信号执行记录 |

#### 3.2.9 统计模块 (/api/stats)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | /api/stats/platform | 获取平台统计数据 |
| GET | /api/stats/user | 获取用户个人统计 |

---

## 四、核心模块优化设计

### 4.1 高并发与防滑点处理（核心交易引擎）

#### 4.1.1 架构设计

```
TradingView信号
      ↓
[Webhook接收服务] ← IP白名单校验
      ↓
[信号队列] (Redis/内存队列)
      ↓
[异步分发引擎] ← FastAPI BackgroundTasks / asyncio.gather
      ↓
并发执行 → [用户1下单] [用户2下单] [用户3下单] ... [用户N下单]
      ↓
[执行结果聚合]
      ↓
[日志记录]
```

#### 4.1.2 技术实现

```python
# 伪代码示例
from fastapi import BackgroundTasks
import asyncio

@app.post("/api/webhook/receive")
async def receive_webhook(payload: WebhookPayload, background_tasks: BackgroundTasks):
    # 1. 验证请求（IP白名单 + Secret Key）
    await verify_webhook_request(request)
    
    # 2. 保存信号到数据库
    signal = await save_signal(payload)
    
    # 3. 提交异步任务处理分发
    background_tasks.add_task(process_signal_async, signal.id)
    
    return {"status": "received", "signal_id": signal.id}

async def process_signal_async(signal_id: str):
    """异步处理信号分发"""
    signal = await get_signal(signal_id)
    
    # 获取所有订阅此策略的活跃用户
    subscriptions = await get_active_subscriptions(signal.strategy_id)
    
    # 并发执行下单（使用asyncio.gather）
    tasks = [
        execute_order_for_user(sub, signal)
        for sub in subscriptions
    ]
    
    # 并发执行，等待全部完成
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 记录执行结果
    await save_execution_results(signal_id, results)

async def execute_order_for_user(subscription, signal):
    """为单个用户执行订单"""
    try:
        exchange_api = await get_exchange_api(subscription.user_id, signal.exchange)
        order = await place_order(exchange_api, signal)
        return {"user_id": subscription.user_id, "status": "success", "order": order}
    except Exception as e:
        return {"user_id": subscription.user_id, "status": "failed", "error": str(e)}
```

#### 4.1.3 未来扩展（Redis消息队列）

```
Phase 1 (MVP): FastAPI BackgroundTasks + asyncio.gather
Phase 2 (扩展): Redis + Celery/RQ 实现分布式任务队列
Phase 3 (高可用): 独立信号处理服务 + Kafka/RabbitMQ
```

### 4.2 Webhook安全加固

#### 4.2.1 多层安全防护

```
┌─────────────────────────────────────────────────────────┐
│                    安全防护层                            │
├─────────────────────────────────────────────────────────┤
│  Layer 1: IP白名单                                       │
│  - 仅允许 TradingView 官方服务器IP网段访问                │
│  - 可配置的IP白名单列表                                   │
├─────────────────────────────────────────────────────────┤
│  Layer 2: Secret Key验证                                 │
│  - 每个用户独立的Secret Key                              │
│  - HMAC-SHA256签名验证                                   │
├─────────────────────────────────────────────────────────┤
│  Layer 3: 请求频率限制                                    │
│  - 单用户单策略限流（如：每秒最多1个信号）                 │
│  - 全局限流保护                                           │
├─────────────────────────────────────────────────────────┤
│  Layer 4: 请求内容验证                                    │
│  - Payload格式校验                                        │
│  - 必填字段检查                                           │
└─────────────────────────────────────────────────────────┘
```

#### 4.2.2 TradingView官方IP网段

```python
# TradingView Webhook IP白名单（示例）
TRADINGVIEW_IP_WHITELIST = [
    "52.89.214.238",
    "34.212.75.30",
    "54.218.48.199",
    # ... 其他官方IP
    # 支持CIDR格式
    "52.89.0.0/16",
    "34.212.0.0/16",
]
```

#### 4.2.3 中间件实现

```python
# 伪代码示例
from fastapi import Request, HTTPException
from ipaddress import ip_address, ip_network

class WebhookSecurityMiddleware:
    async def __call__(self, request: Request, call_next):
        # 仅对webhook路径生效
        if not request.url.path.startswith("/api/webhook/receive"):
            return await call_next(request)
        
        # 1. IP白名单检查
        client_ip = request.client.host
        if not self.is_ip_allowed(client_ip):
            raise HTTPException(status_code=403, detail="IP not allowed")
        
        # 2. Secret Key验证（在请求头或payload中）
        # 在视图函数中处理
        
        response = await call_next(request)
        return response
    
    def is_ip_allowed(self, ip: str) -> bool:
        client_ip = ip_address(ip)
        for allowed_ip in TRADINGVIEW_IP_WHITELIST:
            if "/" in allowed_ip:
                if client_ip in ip_network(allowed_ip):
                    return True
            elif client_ip == ip_address(allowed_ip):
                return True
        return False
```

### 4.3 支付模块务实化设计

#### 4.3.1 支付流程对比

| 方案 | 复杂度 | 适用阶段 | 说明 |
|------|--------|----------|------|
| 自研TRC20节点监听 | 极高 | 不推荐 | 需要搭建节点、处理区块同步、异常处理 |
| **NowPayments（推荐）** | 低 | MVP/正式 | 成熟的加密货币支付网关，支持多种币种 |
| **人工审核模式（MVP备选）** | 极低 | MVP初期 | 用户提交TxHash，管理员后台审核 |

#### 4.3.2 NowPayments接入方案

```
用户选择策略 → 点击订阅 → 创建支付订单
      ↓
[后端] 调用NowPayments API创建发票
      ↓
返回支付地址/二维码给用户
      ↓
用户完成链上转账
      ↓
NowPayments确认收款 → 回调通知后端
      ↓
后端激活用户订阅
```

**NowPayments API集成**

```python
# 伪代码示例
import requests

NOWPAYMENTS_API_KEY = "your_api_key"
NOWPAYMENTS_API_URL = "https://api.nowpayments.io/v1"

async def create_payment_order(user_id: str, strategy_id: str, plan_type: str):
    plan = await get_subscription_plan(strategy_id, plan_type)
    
    payload = {
        "price_amount": float(plan.price),
        "price_currency": "usd",  # 法币计价
        "pay_currency": "usdttrc20",  # 用户支付币种
        "order_id": f"sub_{user_id}_{strategy_id}_{int(time.time())}",
        "order_description": f"订阅 {plan.strategy_name} - {plan.plan_type}",
        "ipn_callback_url": "https://your-domain.com/api/payments/nowpayments/callback",
        "success_url": "https://your-domain.com/payment/success",
        "cancel_url": "https://your-domain.com/payment/cancel",
    }
    
    response = requests.post(
        f"{NOWPAYMENTS_API_URL}/payment",
        json=payload,
        headers={"x-api-key": NOWPAYMENTS_API_KEY}
    )
    
    payment_data = response.json()
    
    # 保存支付记录到数据库
    await save_payment({
        "user_id": user_id,
        "strategy_id": strategy_id,
        "plan_id": plan.id,
        "amount": plan.price,
        "payment_method": "nowpayments",
        "external_id": payment_data["payment_id"],
        "status": "pending",
        "payment_address": payment_data["pay_address"],  # 用户支付地址
    })
    
    return {
        "payment_id": payment_data["payment_id"],
        "pay_address": payment_data["pay_address"],
        "pay_amount": payment_data["pay_amount"],
        "qr_code": generate_qr_code(payment_data["pay_address"]),
    }
```

#### 4.3.3 人工审核模式（MVP备选）

```
用户选择策略 → 点击订阅 → 显示支付信息
      ↓
显示：收款地址 + 金额 + 订单号
      ↓
用户手动转账后 → 提交TxHash
      ↓
[管理员后台] 查看待审核订单列表
      ↓
管理员人工验证链上交易
      ↓
确认收款 → 点击通过 → 激活订阅
```

**人工审核后台功能**

```python
# 管理员API
GET  /api/admin/payments/pending    # 获取待审核支付列表
POST /api/admin/payments/:id/verify  # 审核通过
POST /api/admin/payments/:id/reject  # 审核拒绝
```

### 4.4 TradingView信号接入流程

#### 4.4.1 用户接入流程

```
Step 1: 用户支付订阅策略
      ↓
Step 2: 用户在控制台获取专属Webhook URL
        - URL格式: https://api.your-domain.com/api/webhook/receive?key={user_key}
        - 获取Secret Key用于签名验证
      ↓
Step 3: 用户绑定交易所API（OKX或Binance）
      ↓
Step 4: 用户在TradingView配置Alert
        - Webhook URL: 填入专属URL
        - Message: 使用平台提供的JSON模板
      ↓
Step 5: 用户发送测试信号验证链路
      ↓
Step 6: 正式启用，开始接收信号并自动交易
```

#### 4.4.2 TradingView Alert配置模板

```json
{
  "action": "{{strategy.order.action}}",
  "ticker": "{{ticker}}",
  "order_type": "market",
  "quantity": "{{strategy.position_size}}",
  "price": "{{close}}",
  "timestamp": "{{timenow}}",
  "passphrase": "your_secret_key",
  "exchange": "okx",
  "leverage": "3",
  "strategy_id": "your_strategy_id"
}
```

#### 4.4.3 用户上传TradingView配置信息

用户支付后，需要在控制台填写以下信息：

| 信息项 | 说明 | 用途 |
|--------|------|------|
| 选择交易所 | OKX / Binance | 确定下单目标交易所 |
| API Key | 交易所API密钥 | 下单认证 |
| API Secret | 交易所API密钥 | 下单认证 |
| Passphrase | OKX必填 | 下单认证 |
| TradingView用户名 | 可选 | 用于验证信号来源 |
| 期望杠杆倍数 | 1-125倍 | 下单参数 |
| 单笔仓位比例 | 如：10% | 风险控制 |

---

## 五、系统架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              前端层 (Next.js)                            │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   首页    │  │   策略大厅    │  │   控制台     │  │   接入文档    │    │
│  └──────────┘  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           API网关层 (FastAPI)                            │
│  - 统一认证 (JWT)                                                        │
│  - 限流保护                                                              │
│  - 请求日志                                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           业务服务层                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │   用户服务    │  │   策略服务    │  │   支付服务    │  │   信号服务    ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘│
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                   │
│  │   订阅服务    │  │   交易所服务  │  │   Webhook服务 │                   │
│  └──────────────┘  └──────────────┘  └──────────────┘                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           核心引擎层                                      │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                    信号分发引擎 (异步并发)                         │  │
│  │  - FastAPI BackgroundTasks                                       │  │
│  │  - asyncio.gather 并发下单                                        │  │
│  │  - 预留Redis消息队列扩展                                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                           数据层                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │   PostgreSQL      │  │     Redis        │  │   外部API        │      │
│  │   (主数据库)      │  │   (缓存/队列)     │  │   - OKX API      │      │
│  │                  │  │                  │  │   - Binance API  │      │
│  │                  │  │                  │  │   - NowPayments  │      │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 六、技术栈选型

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | FastAPI (Python) | 高性能异步框架，自动生成API文档 |
| 数据库 | PostgreSQL | 关系型数据库，支持复杂查询 |
| 缓存/队列 | Redis | 缓存、消息队列、限流 |
| ORM | SQLAlchemy 2.0 | 异步ORM，类型安全 |
| 认证 | JWT (python-jose) | 无状态认证 |
| 加密 | cryptography | AES-256加密API密钥 |
| 任务队列 | BackgroundTasks / Celery | 异步任务处理 |
| 外部API | CCXT / 官方SDK | 交易所API接入 |
| 支付网关 | NowPayments | 加密货币支付 |

---

## 七、开发阶段规划

### Phase 1: MVP核心功能
1. 用户注册/登录
2. 策略展示（静态数据）
3. 人工审核支付流程
4. 交易所API绑定
5. Webhook接收信号（IP白名单+Secret验证）
6. 异步信号分发执行
7. 控制台基础功能

### Phase 2: 支付优化
1. NowPayments自动支付接入
2. 分润系统实现
3. 订阅续费提醒

### Phase 3: 高可用优化
1. Redis消息队列
2. 分布式信号处理
3. 监控告警系统

---

## 八、安全注意事项

1. **API密钥加密**：所有交易所API密钥必须使用AES-256加密存储
2. **传输安全**：所有API通信必须使用HTTPS/TLS 1.3
3. **IP白名单**：Webhook接口必须配置IP白名单
4. **请求签名**：Webhook请求必须验证HMAC签名
5. **权限最小化**：交易所API只开启交易权限，禁止提币权限
6. **日志脱敏**：日志中不得记录明文API密钥

---

*文档版本: v1.0*  
*更新日期: 2026-03-09*
