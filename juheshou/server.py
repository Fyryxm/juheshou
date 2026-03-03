"""
聚合兽 - 通用 API 聚合网关
支持任意数据源的聚合、降级、缓存
"""

from fastapi import FastAPI, HTTPException, Header, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import time
import hashlib
from pathlib import Path
from .core.config import settings
from .core.aggregator import Aggregator, DataSource
from .core.presets import register_all_sources
from .core.usage import tracker
from .core.keys import key_manager

app = FastAPI(
    title="聚合兽 API",
    description="通用 API 聚合网关 - 一个 API Key，多个数据源，自动降级",
    version="0.3.0",
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
    remaining_requests: int = 0


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


class CreateKeyRequest(BaseModel):
    """创建 API Key 请求"""
    name: str
    tier: str = "free"


# ==================== 认证 ====================

def hash_key(key: str) -> str:
    """哈希 API Key"""
    return hashlib.sha256(key.encode()).hexdigest()[:32]


async def verify_api_key(authorization: Optional[str] = Header(None)):
    """验证 API Key"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # 检查主 Key
    if token == settings.master_api_key:
        return {
            "key_hash": "master",
            "tier": "enterprise",
            "requests_limit": -1,
            "name": "Master Key",
        }
    
    # 验证用户 Key
    api_key = key_manager.verify_key(token)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    
    return {
        "key_hash": api_key.key_hash,
        "tier": api_key.tier,
        "requests_limit": api_key.requests_limit,
        "name": api_key.name,
    }


async def check_quota(user: dict):
    """检查配额"""
    if user["tier"] == "enterprise":
        return  # 企业版无限
    
    quota = tracker.check_quota(user["key_hash"])
    if not quota["allowed"]:
        raise HTTPException(
            status_code=429,
            detail=f"配额已用完。今日已使用 {quota['requests_today']} 次，限额 {quota['limit']} 次。"
        )
    
    return quota


# ==================== 核心路由 ====================

@app.get("/")
async def root():
    """API 根路径"""
    return {
        "name": "聚合兽",
        "version": "0.3.0",
        "description": "通用 API 聚合网关",
        "docs": "/docs",
        "endpoints": {
            "aggregate": "/v1/aggregate/{source_name}",
            "sources": "/v1/sources",
            "health": "/v1/health",
            "pricing": "/v1/pricing",
            "usage": "/v1/usage",
            "keys": "/v1/keys (需要认证)",
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
    request: Request,
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
    start_time = time.time()
    
    # 检查配额
    quota = await check_quota(user)
    
    success = False
    source_url = ""
    confidence = 0.0
    fallback_used = False
    
    try:
        result = await aggregator.fetch(
            source_name=source_name,
            use_fallback=fallback,
            use_cache=cache,
        )
        
        success = True
        source_url = result["source"]
        confidence = result["confidence"]
        fallback_used = result.get("fallback", False)
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 记录使用
        tracker.record_request(
            key_hash=user["key_hash"],
            endpoint=f"/v1/aggregate/{source_name}",
            source=source_url,
            latency_ms=latency_ms,
            success=True,
            confidence=confidence,
            fallback_used=fallback_used,
            tier=user["tier"],
            requests_limit=user["requests_limit"],
        )
        
        remaining = quota["remaining"] - 1 if quota else -1
        
        return AggregatedResponse(
            success=True,
            data=result["data"],
            source=source_url,
            confidence=confidence,
            latency_ms=latency_ms,
            timestamp=datetime.now().isoformat(),
            fallback_used=fallback_used,
            remaining_requests=remaining,
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        
        # 记录失败
        tracker.record_request(
            key_hash=user["key_hash"],
            endpoint=f"/v1/aggregate/{source_name}",
            source=source_url or "unknown",
            latency_ms=latency_ms,
            success=False,
            confidence=0,
            fallback_used=False,
            tier=user["tier"],
            requests_limit=user["requests_limit"],
        )
        
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


# ==================== API Key 管理 ====================

@app.post("/v1/keys")
async def create_api_key(
    req: CreateKeyRequest,
    user: dict = Depends(verify_api_key),
):
    """创建新的 API Key（需要 Master Key）"""
    if user["key_hash"] != "master":
        raise HTTPException(status_code=403, detail="需要 Master Key")
    
    result = key_manager.create_key(name=req.name, tier=req.tier)
    return result


@app.get("/v1/keys")
async def list_api_keys(user: dict = Depends(verify_api_key)):
    """列出所有 API Keys（需要 Master Key）"""
    if user["key_hash"] != "master":
        raise HTTPException(status_code=403, detail="需要 Master Key")
    
    return key_manager.list_keys()


@app.get("/v1/usage")
async def get_usage(user: dict = Depends(verify_api_key)):
    """获取当前 API Key 使用统计"""
    return tracker.get_usage_stats(user["key_hash"])


# ==================== 定价 ====================

@app.get("/v1/pricing")
async def get_pricing():
    """获取定价信息"""
    return {
        "plans": [
            {
                "name": "Free",
                "price": 0,
                "price_unit": "USD/month",
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
        "version": "0.3.0",
        "sources": {
            "total": len(sources),
            "healthy": healthy_count,
        },
    }


# ==================== 管理后台 ====================

@app.get("/admin")
async def admin_dashboard():
    """管理后台"""
    admin_path = Path(__file__).parent.parent / "admin" / "index.html"
    if admin_path.exists():
        return FileResponse(admin_path)
    return {"error": "Admin dashboard not found"}


@app.delete("/v1/keys/{key_hash}")
async def revoke_api_key(
    key_hash: str,
    user: dict = Depends(verify_api_key),
):
    """吊销 API Key（需要 Master Key）"""
    if user["key_hash"] != "master":
        raise HTTPException(status_code=403, detail="需要 Master Key")
    
    success = key_manager.revoke_key(key_hash)
    if not success:
        raise HTTPException(status_code=404, detail="API Key 不存在")
    
    return {"success": True, "message": f"API Key {key_hash[:8]}... 已吊销"}