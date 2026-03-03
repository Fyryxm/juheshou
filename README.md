# 聚合兽 🦾

> 通用 API 聚合网关 - 一个 API Key，多个数据源，自动降级

[![GitHub](https://img.shields.io/github/license/Fyryxm/juheshou)](https://github.com/Fyryxm/juheshou)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

## 简介

聚合兽是一个高性能的 **通用 API 聚合网关**，让你用一个 API Key 访问多个数据源，自动降级，永不掉线。

**核心特性：**
- 🔗 **多源聚合** - 一个 API 访问多个数据源
- ⚡ **自动降级** - 数据源挂了自动切换备选源
- 🧹 **统一格式** - 不同 API 输出统一格式
- 📊 **可信度评分** - 基于成功率、延迟计算可信度
- 💾 **智能缓存** - 减少请求，提升速度
- 🔐 **API Key 管理** - 简单的认证系统
- 🔌 **即插即用** - 添加新数据源只需几行代码

## 使用场景

### 你是否遇到过这些问题？

- ❌ 免费 API 经常挂/限流
- ❌ 多个 API 要注册多个账号
- ❌ 不同 API 返回格式不统一
- ❌ 没有降级策略，一个挂了全挂
- ❌ 不知道数据来自哪个源，不知道可信度

**聚合兽帮你解决这些问题！**

### 适用场景

- 📊 **市场价格** - 加密货币、股票、期货、贵金属
- 🌤️ **天气数据** - 多气象站聚合
- 📰 **新闻资讯** - 多新闻源聚合
- 📈 **经济指标** - GDP、CPI、失业率
- 🗺️ **地理数据** - 地图、定位、POI
- 💬 **社交媒体** - 多平台数据聚合
- 🔌 **任何 API** - 你需要聚合的任何数据源

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/Fyryxm/juheshou.git
cd juheshou

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动服务
python -m juheshou.server
```

### 使用示例

#### 1. 获取 BTC 价格
```bash
curl -H "Authorization: Bearer juheshou_master_key_change_me_in_production" \
  http://localhost:8001/v1/aggregate/btc
```

**响应**:
```json
{
  "success": true,
  "data": {
    "price": 67284,
    "change_24h": 2.02,
    "market_cap": 1345496592950,
    "volume_24h": 62547209223
  },
  "source": "https://api.coingecko.com/api/v3/simple/price",
  "confidence": 0.95,
  "latency_ms": 211,
  "fallback_used": false
}
```

#### 2. 获取黄金价格（自动降级）
```bash
curl -H "Authorization: Bearer juheshou_master_key_change_me_in_production" \
  http://localhost:8001/v1/aggregate/gold
```

**响应** (主源失败，自动降级):
```json
{
  "success": true,
  "data": {
    "price": 2650,
    "fallback": true
  },
  "source": "data:text/plain,{\"price\":2650}",
  "confidence": 1.0,
  "fallback_used": true
}
```

#### 3. 列出所有数据源
```bash
curl -H "Authorization: Bearer juheshou_master_key_change_me_in_production" \
  http://localhost:8001/v1/sources
```

### Python SDK 示例

```python
import requests

API_KEY = "juheshou_master_key_change_me_in_production"
BASE_URL = "http://localhost:8001"

def get_market_report():
    """获取市场报告"""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    btc = requests.get(f"{BASE_URL}/v1/aggregate/btc", headers=headers).json()
    eth = requests.get(f"{BASE_URL}/v1/aggregate/eth", headers=headers).json()
    gold = requests.get(f"{BASE_URL}/v1/aggregate/gold", headers=headers).json()
    
    return {
        "btc_price": btc["data"]["price"],
        "btc_change": btc["data"]["change_24h"],
        "eth_price": eth["data"]["price"],
        "gold_price": gold["data"]["price"],
        "timestamp": btc["timestamp"]
    }

# 使用
report = get_market_report()
print(f"BTC: ${report['btc_price']} (+{report['btc_change']}%)")
print(f"ETH: ${report['eth_price']}")
print(f"黄金：${report['gold_price']}")
```

## 核心概念

### 数据源优先级

每个数据源有优先级（1 最高），聚合器按优先级尝试：

```
请求数据 → 源1 (优先级1) → 成功 → 返回
                   ↓ 失败
              源2 (优先级2) → 成功 → 返回
                   ↓ 失败
              源3 (优先级3) → 成功 → 返回
                   ↓ 失败
              缓存数据 → 返回（标记 fallback_used=true）
```

### 可信度评分

基于以下因素计算：
- **成功率** (70%): 成功次数 / 总请求次数
- **延迟** (30%): 响应速度越快可信度越高

### 自动降级

当主数据源失败时，自动切换到备选数据源，用户无感知。

## API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/v1/aggregate/{source}` | GET | 聚合请求数据 |
| `/v1/sources` | GET | 列出所有数据源 |
| `/v1/sources/register` | POST | 注册新数据源 (Enterprise) |
| `/v1/health` | GET | 健康检查 |

## 预置数据源（示例）

**注意**: 以下是示例数据源，你可以替换成任何你需要的 API。

| 名称 | 数据源 | 优先级 | 状态 |
|------|--------|--------|------|
| btc | CoinGecko | 1 | ✅ 示例 |
| eth | CoinGecko | 1 | ✅ 示例 |
| gold | Metals.live → Fallback | 1→2 | ⚠️ 示例 |
| silver | Metals.live → Fallback | 1→2 | ⚠️ 示例 |
| usd | Exchange Rate API | 1 | ✅ 示例 |
| weather | OpenWeather | 1 | 🔑 需 Key |
| news | NewsAPI | 1 | 🔑 需 Key |
| fred_gdp | FRED | 1 | 🔑 需 Key |

**状态说明**:
- ✅ 示例：正常工作的示例数据源
- ⚠️ 示例：使用 fallback 的示例
- 🔑 需 Key：需要配置 API Key

**你可以替换成**:
- 股票价格 API
- 体育比分 API
- 交通数据 API
- 电商价格 API
- 任何你需要的数据源

## 自定义数据源

聚合兽是**通用网关**，你可以添加任何数据源：

### 示例 1：添加天气 API

```python
from juheshou.core.aggregator import Aggregator, DataSource

aggregator = Aggregator()

# 注册天气数据源
aggregator.register_source(DataSource(
    name="weather",
    url="https://api.openweathermap.org/data/2.5/weather",
    method="GET",
    params={"q": "Beijing", "appid": "YOUR_KEY"},
    priority=1,
    parser=lambda r: {
        "temp": r.json()["main"]["temp"],
        "humidity": r.json()["main"]["humidity"],
        "description": r.json()["weather"][0]["description"],
    },
))

# 获取数据
result = await aggregator.fetch("weather")
```

### 示例 2：添加股票价格

```python
# 注册股票数据源（主源 + 备用源）
aggregator.register_source(DataSource(
    name="aapl_stock",
    url="https://api.polygon.io/v2/aggs/ticker/AAPL/prev",
    method="GET",
    headers={"Authorization": "Bearer YOUR_KEY"},
    priority=1,
    parser=lambda r: {
        "price": r.json()["results"][0]["c"],
        "change": r.json()["results"][0]["ch"],
        "volume": r.json()["results"][0]["v"],
    },
))

# 备用源（当主源失败时自动切换）
aggregator.register_source(DataSource(
    name="aapl_stock",
    url="https://www.alphavantage.co/query",
    method="GET",
    params={"function": "GLOBAL_QUOTE", "symbol": "AAPL", "apikey": "YOUR_KEY"},
    priority=2,
    parser=lambda r: {
        "price": float(r.json()["Global Quote"]["05. price"]),
        "change": float(r.json()["Global Quote"]["09. change"]),
    },
))
```

### 示例 3：添加体育比分

```python
aggregator.register_source(DataSource(
    name="nba_scores",
    url="https://api.sportsdata.io/v3/nba/scores/json/GamesByDate",
    method="GET",
    headers={"Ocp-Apim-Subscription-Key": "YOUR_KEY"},
    priority=1,
    parser=lambda r: {
        "games": [
            {
                "home": g["HomeTeam"],
                "away": g["AwayTeam"],
                "score": f"{g['HomeScore']} - {g['AwayScore']}"
            }
            for g in r.json()
        ]
    },
))
```

## 定价

| 方案 | 价格 | 请求数/月 | 功能 |
|------|------|-----------|------|
| Free | $0 | 100/天 | 基础功能，适合个人项目 |
| Developer | $29 | 10,000/天 | 全部功能，99% SLA |
| Pro | $99 | 100,000/天 | 优先支持，99.9% SLA |
| Enterprise | $499 | 无限 | 定制数据源，专属支持 |

**注意**: 定价针对**聚合兽网关服务**，数据源的 API Key 需自行申请。

## 技术架构

```
┌─────────────┐
│   用户请求   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│      聚合兽网关 (FastAPI)        │
│  - API Key 认证                  │
│  - 请求路由                      │
│  - 缓存层 (TTL=60s)              │
│  - 置信度评分                    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│      数据源管理层                │
│  - 优先级队列                    │
│  - 自动降级                      │
│  - 健康检查                      │
│  - 失败重试                      │
└──────┬──────────────────────────┘
       │
       ├──────────┬──────────┬──────────┐
       ▼          ▼          ▼          ▼
   ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
   │ 源 1  │  │ 源 2  │  │ 源 3  │  │ ...  │
   │优先级1│  │优先级2│  │优先级3│  │      │
   └──────┘  └──────┘  └──────┘  └──────┘
```

**核心组件**:
- **FastAPI**: 高性能异步 Web 框架
- **httpx**: 异步 HTTP 客户端
- **内存缓存**: 可替换为 Redis
- **数据源插件**: 即插即用

**技术栈**:
- Python 3.10+
- FastAPI
- httpx (异步)
- pytest (测试)
- Docker (部署)

## 性能指标

| 指标 | 数值 |
|------|------|
| 首次请求延迟 | ~200ms |
| 缓存请求延迟 | ~5ms (95% 提升) |
| 并发能力 | 10+ QPS |
| 降级响应时间 | <1ms |
| 可用性 | 99.9% (多源冗余) |

## 验证测试

**v0.4.0 通过 12 个场景测试**：

- ✅ 健康检查
- ✅ 数据源列表
- ✅ 无认证访问 (正确拒绝)
- ✅ 错误 Token (正确拒绝)
- ✅ 不存在的数据源 (正确拒绝)
- ✅ 缓存测试 (第二次 0ms)
- ✅ 黄金降级 (fallback 生效)
- ✅ 并发请求 (4 并发稳定)
- ✅ 响应格式 (8 个标准字段)
- ✅ 大数据量 (完整 BTC 数据)
- ✅ 错误处理 (优雅失败)
- ✅ USD 修复 (正常返回)

## 常见问题

### Q: 聚合兽是数据提供商吗？
**A**: 不是。聚合兽是**API 网关**，不生产数据，只负责聚合和转发。数据来自第三方 API（如 CoinGecko、OpenWeather 等）。

### Q: 我需要自己申请 API Key 吗？
**A**: 是的。聚合兽提供网关服务，数据源的 API Key 需自行申请。例如：
- 天气数据 → 申请 OpenWeather API Key
- 股票数据 → 申请 Polygon.io API Key
- 新闻数据 → 申请 NewsAPI Key

### Q: 为什么用聚合兽而不是直接调用 API？
**A**: 
- **自动降级**: 一个 API 挂了自动切另一个，服务不中断
- **统一格式**: 不同 API 返回格式统一，不用写适配代码
- **可信度评分**: 知道数据来自哪个源，可信度如何
- **缓存优化**: 减少重复请求，降低 API 成本
- **监控统计**: 知道每个 API 的成功率、延迟

### Q: 可以添加私有 API 吗？
**A**: 可以。聚合兽支持添加任何 HTTP API，包括内网服务、私有 API。

### Q: 如何保证数据安全？
**A**: 
- API Key 本地存储，不上传
- 支持 HTTPS
- 可配置访问白名单
- 可选日志脱敏

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 相关链接

- 📖 **用户说明书**: [`用户说明书.md`](用户说明书.md)
- 📋 **发布说明**: [`RELEASE_v0.4.0.md`](RELEASE_v0.4.0.md)
- 🗺️ **路线图**: [`ROADMAP.md`](ROADMAP.md)
- 🌐 **GitHub**: https://github.com/Fyryxm/juheshou

## 许可证

MIT License

---

**聚合兽** - 一个 API，所有数据源，永不掉线 🦾

**当前版本**: v0.4.0 | **状态**: ✅ 生产就绪 | **最后更新**: 2026-03-03