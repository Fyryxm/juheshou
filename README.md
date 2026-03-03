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

### 使用

```bash
# 获取 BTC 价格（自动聚合多个数据源）
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.juheshou.io/v1/aggregate/btc

# 获取黄金价格（自动降级）
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.juheshou.io/v1/aggregate/gold

# 列出所有数据源
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.juheshou.io/v1/sources
```

### 响应格式

```json
{
  "success": true,
  "data": {
    "price": 69031.00,
    "change_24h": 3.77
  },
  "source": "https://api.coingecko.com/api/v3/simple/price",
  "confidence": 0.95,
  "latency_ms": 120,
  "timestamp": "2026-03-03T11:00:00Z",
  "fallback_used": false
}
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

| 名称 | 数据源 | 优先级 |
|------|--------|--------|
| btc | CoinGecko | 1 |
| gold | Metals.live | 1 |
| usd | Frankfurter | 1 |

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
- **缓存**: 内存缓存 (可扩展 Redis)
- **部署**: Docker + Kubernetes

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT License

---

**聚合兽** - 一个 API，所有数据源，永不掉线 🦾