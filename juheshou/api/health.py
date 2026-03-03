"""
健康检查 API 路由
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "聚合兽",
        "version": "0.1.0",
    }


@router.get("/ready")
async def readiness_check():
    """就绪检查"""
    # TODO: 检查数据库、Redis 连接
    return {
        "status": "ready",
        "checks": {
            "api": True,
            "redis": True,  # TODO: 实际检查
        },
    }