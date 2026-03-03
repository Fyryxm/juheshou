"""
聚合兽 - 通用 API 聚合网关
支持任意数据源的聚合、降级、缓存
"""

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List, Callable
from pydantic import BaseModel
from datetime import datetime
import asyncio
import httpx
from .core.config import settings
from .core.aggregator import Aggregator, DataSource

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
aggregator = Aggregator()


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
    priority: int = 1  # 1 最高
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
        return {"user_id": "master", "tier": "enterprise"}
    
    # 临时：允许所有请求
    return {"user_id": "anonymous", "tier": "free"}


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
        },
    }


@app.get("/v1/sources")
async def list_sources(user: dict = Header(None)):
    """列出所有数据源"""
    sources = aggregator.get_sources()
    return {
        "count": len(sources),
        "sources": [
            {
                "name": s.name,
                "priority": s.priority,
                "enabled": s.enabled,
                "last_success": s.last_success,
                "avg_latency_ms": s.avg_latency_ms,
            }
            for s in sources
        ],
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
    
    - source_name: 数据源名称（如 "gold", "btc", "weather"）
    - fallback: 是否启用降级策略
    - cache: 是否使用缓存
    """
    start_time = datetime.now()
    
    try:
        result = await aggregator.fetch(
            source_name=source_name,
            use_fallback=fallback,
            use_cache=cache,
        )
        
        latency_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return AggregatedResponse(
            success=True,
            data=result["data"],
            source=result["source"],
            confidence=result["confidence"],
            latency_ms=latency_ms,
            timestamp=datetime.now().isoformat(),
            fallback_used=result.get("fallback", False),
        )
        
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"所有数据源失败: {str(e)}")


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


# ==================== 预置数据源 ====================

def init_default_sources():
    """初始化预置数据源"""
    
    # BTC 价格（多源）
    aggregator.register_source(DataSource(
        name="btc",
        url="https://api.coingecko.com/api/v3/simple/price",
        method="GET",
        params={"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"},
        priority=1,
        parser=lambda r: {
            "price": r.json()["bitcoin"]["usd"],
            "change_24h": r.json()["bitcoin"].get("usd_24h_change", 0),
        },
    ))
    
    # 黄金价格（多源降级）
    aggregator.register_source(DataSource(
        name="gold",
        url="https://api.metals.live/v1/spot/gold",
        method="GET",
        priority=1,
        timeout=3,
        parser=lambda r: {"price": r.json().get("price", 2650)},
    ))
    
    # 美元指数
    aggregator.register_source(DataSource(
        name="usd",
        url="https://api.frankfurter.app/latest",
        method="GET",
        params={"from": "USD", "to": "EUR"},
        priority=1,
        parser=lambda r: {"index": 100 / r.json()["rates"]["EUR"]},
    ))


# 启动时初始化
init_default_sources()