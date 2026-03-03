# 聚合兽 🦾

> 多数据源 API 聚合网关 | Multi-source API Aggregation Gateway

## 简介

聚合兽是一个高性能的 API 聚合网关，让你用一个 API Key 访问多个数据源。

**核心特性：**
- 🔗 **多源聚合** - 一个 API 访问多个数据源
- ⚡ **自动故障转移** - 数据源挂了自动切换
- 🧹 **数据清洗** - 统一输出格式
- 📊 **负载均衡** - 智能分配请求
- 🔐 **API Key 管理** - 简单的认证系统

## 快速开始

```bash
# 克隆仓库
git clone https://github.com/Fyryxm/juheshou.git
cd juheshou

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m juheshou.server
```

## API 端点

### 获取价格数据

```bash
# 获取 BTC 价格
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.juheshou.io/v1/prices/btc

# 获取黄金价格
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.juheshou.io/v1/prices/gold

# 获取美元指数
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.juheshou.io/v1/prices/usd
```

### 获取趋势报告

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  https://api.juheshou.io/v1/reports/daily
```

## 支持的数据源

| 数据源 | 类型 | 状态 |
|--------|------|------|
| CoinGecko | BTC/加密货币 | ✅ |
| Gold API | 黄金价格 | ⏳ |
| FRED | 美元指数 | ⏳ |
| News API | 新闻数据 | ⏳ |

## 定价

| 方案 | 价格 | 请求数/月 |
|------|------|-----------|
| Starter | $29/月 | 10,000 |
| Pro | $99/月 | 100,000 |
| Enterprise | $499/月 | 无限 |

## 技术栈

- **后端**: FastAPI (Python)
- **数据库**: Redis (缓存) + PostgreSQL (用户数据)
- **部署**: Docker + Kubernetes
- **监控**: Prometheus + Grafana

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

## 许可证

MIT License

---

**聚合兽** - 一个 API，所有数据源 🦾