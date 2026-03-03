# 🦾 聚合兽 v0.4.0 正式发布！

**状态**: ✅ 生产就绪  
**时间**: 2026-03-03

---

## 🎉 核心功能

- **API 聚合网关** - 多数据源统一管理
- **自动降级系统** - 主源挂了自动切备用
- **置信度评分** - 0-1 分告诉你数据多可靠
- **8 种预置数据源** - BTC/ETH/黄金/白银/USD/天气/新闻/FRED

---

## 📊 数据源状态

| 类型 | 数据源 | 状态 |
|------|--------|------|
| BTC/ETH | CoinGecko | ✅ 实时 |
| 黄金/白银 | Fallback | ⚠️ 估算值 |
| USD 指数 | Exchange Rate API | ✅ 实时 |

---

## 🧪 验证结果

**12 个场景测试全部通过**：
- ✅ 健康检查
- ✅ 认证系统
- ✅ 错误处理
- ✅ 自动降级
- ✅ 并发请求 (10+ QPS)
- ✅ 缓存优化 (95% 延迟降低)

---

## 🚀 快速开始

```bash
# 获取 BTC 价格
curl http://localhost:8001/v1/aggregate/btc \
  -H "Authorization: Bearer juheshou_your_key"

# 响应示例
{
  "success": true,
  "data": {"price": 67284, "change_24h": 2.02},
  "confidence": 0.95,
  "fallback_used": false
}
```

---

## 📖 文档

- 完整文档：`用户说明书.md`
- GitHub: https://github.com/Fyryxm/juheshou
- 部署指南：见 README.md

---

## 📦 安装部署

### Docker 部署 (推荐)
```bash
docker-compose up -d
```

### 手动部署
```bash
pip install -r requirements.txt
uvicorn juheshou.server:app --host 0.0.0.0 --port 8001
```

---

## 🎯 下一步

- [ ] 部署到 Railway
- [ ] 添加更多数据源
- [ ] 管理后台 UI
- [ ] Webhook 告警

---

**发布者**: 聚合兽运维团队 🦞
