"""
聚合兽 - 通用 API 聚合网关
支持任意数据源的聚合、降级、缓存
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from .core.config import settings
from .core.aggregator import Aggregator, DataSource
from .core.presets import register_all_sources

app = FastAPI(
    title="聚合兽 API",
    description="通用 API 聚合网关 - 一个 API Key，多个数据源，自动降级",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化聚合器
aggregator = Aggregator(cache_ttl=60)

# 注册预置数据源
register_all_sources(aggregator)


# ==================== 数据模型 ====================

class AggregatedResponse(BaseModel):
    """统一响应格式"""
    success: bool
    data: Any
    source: str
    confidence: float
    latency_ms: int
    timestamp: str
    fallback_used: bool = False


class DataSourceConfig(BaseModel):
    """数据源配置"""
    name: str
    url: str
    method: str = "GET"
    headers: Dict[str, str] = {}
    params: Dict[str, Any] = {}
    priority: int = 1
    timeout: int = 5
    enabled: bool = True


# ==================== 认证 ====================

async def verify_api_key(authorization: Optional[str] = Header(None)):
    """验证 API Key"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # TODO: 实现真正的 API Key 验证（数据库查询）
    if token == settings.master_api_key:
        return {"user_id": "master", "tier": "enterprise", "requests_limit": -1}
    
    # 临时：允许所有请求
    return {"user_id": "anonymous", "tier": "free", "requests_limit": 100}


# ==================== 核心路由 ====================

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "聚合兽",
        "version": "0.2.0",
        "description": "通用 API 聚合网关",
        "docs": "/docs",
        "endpoints": {
            "aggregate": "/v1/aggregate/{source_name}",
            "sources": "/v1/sources",
            "health": "/v1/health",
            "pricing": "/v1/pricing",
        },
    }


@app.get("/v1/sources")
async def list_sources():
    """列出所有可用数据源"""
    sources = aggregator.get_sources()
    
    # 按名称分组
    grouped = {}
    for s in sources:
        if s.name not in grouped:
            grouped[s.name] = []
        grouped[s.name].append({
            "url": s.url,
            "priority": s.priority,
            "enabled": s.enabled,
            "success_rate": s.success_count / (s.success_count + s.failure_count) if s.success_count + s.failure_count > 0 else 0,
            "avg_latency_ms": s.avg_latency_ms,
        })
    
    return {
        "count": len(grouped),
        "sources": grouped,
    }


@app.get("/v1/aggregate/{source_name}")
async def aggregate_request(
    source_name: str,
    user: dict = Depends(verify_api_key),
    fallback: bool = True,
    cache: bool = True,
):
    """
    聚合请求
    
    - **source_name**: 数据源名称（btc, eth, gold, silver, usd, weather, news）
    - **fallback**: 是否启用降级策略（默认 True）
    - **cache**: 是否使用缓存（默认 True）
    """
    import time
    start_time = time.time()
    
    try:
        result = await aggregator.fetch(
            source_name=source_name,
            use_fallback=fallback,
            use_cache=cache,
        )
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return AggregatedResponse(
            success=True,
            data=result["data"],
            source=result["source"],
            confidence=result["confidence"],
            latency_ms=latency_ms,
            timestamp=datetime.now().isoformat(),
            fallback_used=result.get("fallback", False),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"所有数据源失败: {str(e)}")


@app.get("/v1/sources/{source_name}/stats")
async def get_source_stats(source_name: str, user: dict = Depends(verify_api_key)):
    """获取数据源统计"""
    stats = aggregator.get_source_stats(source_name)
    if not stats["sources"]:
        raise HTTPException(status_code=404, detail=f"数据源不存在: {source_name}")
    return stats


@app.post("/v1/sources/register")
async def register_source(
    config: DataSourceConfig,
    user: dict = Depends(verify_api_key),
):
    """
    注册新数据源（Enterprise 功能）
    """
    if user.get("tier") not in ["enterprise", "pro"]:
        raise HTTPException(status_code=403, detail="需要 Pro 或 Enterprise 订阅")
    
    source = DataSource(
        name=config.name,
        url=config.url,
        method=config.method,
        headers=config.headers,
        params=config.params,
        priority=config.priority,
        timeout=config.timeout,
        enabled=config.enabled,
    )
    
    aggregator.register_source(source)
    
    return {"success": True, "message": f"数据源 {config.name} 已注册"}


@app.get("/v1/pricing")
async def get_pricing():
    """获取定价信息"""
    return {
        "plans": [
            {
                "name": "Free",
                "price": 0,
                "requests_per_day": 100,
                "features": ["基础数据", "延迟 5 分钟", "社区支持"],
            },
            {
                "name": "Developer",
                "price": 29,
                "price_unit": "USD/month",
                "requests_per_day": 10000,
                "features": ["实时数据", "99% SLA", "邮件支持", "5 个数据源"],
            },
            {
                "name": "Pro",
                "price": 99,
                "price_unit": "USD/month",
                "requests_per_day": 100000,
                "features": ["实时数据", "99.9% SLA", "优先支持", "无限数据源", "自定义数据源"],
            },
            {
                "name": "Enterprise",
                "price": 499,
                "price_unit": "USD/month",
                "requests_per_day": "无限",
                "features": ["实时数据", "99.99% SLA", "专属支持", "无限数据源", "自定义数据源", "私有部署"],
            },
        ],
        "contact": "support@juheshou.io",
    }


@app.get("/v1/health")
async def health_check():
    """健康检查"""
    sources = aggregator.get_sources()
    healthy_count = sum(1 for s in sources if s.last_success)
    
    return {
        "status": "healthy" if healthy_count > 0 else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": "0.2.0",
        "sources": {
            "total": len(sources),
            "healthy": healthy_count,
        },
    }