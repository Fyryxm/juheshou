"""
聚合兽 API 服务器
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import prices, reports, health
from .core.config import settings

app = FastAPI(
    title="聚合兽 API",
    description="多数据源 API 聚合网关",
    version="0.1.0",
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

# 注册路由
app.include_router(prices.router, prefix="/v1/prices", tags=["价格"])
app.include_router(reports.router, prefix="/v1/reports", tags=["报告"])
app.include_router(health.router, prefix="/v1", tags=["健康检查"])


@app.get("/")
async def root():
    return {
        "name": "聚合兽",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/v1/health",
    }