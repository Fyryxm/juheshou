"""
配置管理
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # 服务配置
    app_name: str = "聚合兽"
    app_version: str = "0.1.0"
    debug: bool = False
    
    # API 配置
    api_prefix: str = "/v1"
    
    # 数据源 API Keys
    coingecko_api_key: Optional[str] = None
    gold_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None
    news_api_key: Optional[str] = None
    
    # Redis 配置
    redis_url: str = "redis://localhost:6379"
    
    # 认证
    master_api_key: str = "juheshou_master_key_change_me"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()