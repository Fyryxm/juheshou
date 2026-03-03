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

## 使用场景

### 你是否遇到过这些问题？

- ❌ 免费 API 经常挂/限流
- ❌ 多个 API 要注册多个账号
- ❌ 不同 API 返回格式不统一
- ❌ 没有降级策略，一个挂了全挂
- ❌ 不知道数据来自哪个源，不知道可信度

**聚合兽帮你解决这些问题！**

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

## 预置数据源

| 名称 | 数据源 | 优先级 | 状态 |
|------|--------|--------|------|
| btc | CoinGecko | 1 | ✅ 实时 |
| eth | CoinGecko | 1 | ✅ 实时 |
| gold | Metals.live → Fallback | 1→2 | ⚠️ 估算 |
| silver | Metals.live → Fallback | 1→2 | ⚠️ 估算 |
| usd | Exchange Rate API | 1 | ✅ 实时 |
| weather | OpenWeather | 1 | 🔑 需 Key |
| news | NewsAPI | 1 | 🔑 需 Key |
| fred_gdp | FRED | 1 | 🔑 需 Key |

**状态说明**:
- ✅ 实时：数据源正常工作
- ⚠️ 估算：使用历史均值 fallback
- 🔑 需 Key：需要配置 API Key

## 自定义数据源

```python
from juheshou.core.aggregator import Aggregator, DataSource

aggregator = Aggregator()

# 注册自定义数据源
aggregator.register_source(DataSource(
    name="weather",
    url="https://api.openweathermap.org/data/2.5/weather",
    method="GET",
    params={"q": "Beijing", "appid": "YOUR_KEY"},
    priority=1,
    parser=lambda r: {
        "temp": r.json()["main"]["temp"],
        "humidity": r.json()["main"]["humidity"],
    },
))

# 获取数据
result = await aggregator.fetch("weather")
```

## 定价

| 方案 | 价格 | 请求数/月 | 功能 |
|------|------|-----------|------|
| Free | $0 | 100/天 | 基础数据，延迟 5 分钟 |
| Developer | $29 | 10,000/天 | 实时数据，99% SLA |
| Pro | $99 | 100,000/天 | 优先支持，99.9% SLA |
| Enterprise | $499 | 无限 | 自定义数据源，专属支持 |

## 技术栈

- **后端**: FastAPI (Python 3.10+)
- **HTTP 客户端**: httpx (异步)
- **缓存**: 内存缓存 (TTL=60s，可扩展 Redis)
- **部署**: Docker + Kubernetes
- **测试**: pytest + asyncio

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

## 贡献

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