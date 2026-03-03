"""
聚合器核心模块
实现多数据源聚合、自动降级、缓存
"""

from typing import Dict, Any, Optional, Callable, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import asyncio
import httpx
import time


@dataclass
class DataSource:
    """数据源配置"""
    name: str
    url: str
    method: str = "GET"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1 最高优先级
    timeout: int = 5
    enabled: bool = True
    
    # 响应解析器
    parser: Optional[Callable] = None
    
    # 统计信息
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: int = 0
    total_latency_ms: int = 0


class Aggregator:
    """
    API 聚合器
    
    功能:
    - 多数据源管理
    - 自动降级策略
    - 响应缓存
    - 健康检查
    - 统计追踪
    """
    
    def __init__(self, cache_ttl: int = 60):
        self.sources: Dict[str, List[DataSource]] = {}
        self.cache: Dict[str, Dict] = {}
        self.cache_ttl = cache_ttl
    
    def register_source(self, source: DataSource):
        """注册数据源"""
        if source.name not in self.sources:
            self.sources[source.name] = []
        self.sources[source.name].append(source)
        # 按优先级排序
        self.sources[source.name].sort(key=lambda s: s.priority)
    
    def get_sources(self) -> List[DataSource]:
        """获取所有数据源"""
        all_sources = []
        for sources in self.sources.values():
            all_sources.extend(sources)
        return all_sources
    
    async def fetch(
        self,
        source_name: str,
        use_fallback: bool = True,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        获取数据
        
        Args:
            source_name: 数据源名称
            use_fallback: 是否启用降级策略
            use_cache: 是否使用缓存
            
        Returns:
            {
                "data": 解析后的数据,
                "source": 数据源名称,
                "confidence": 可信度 (0-1),
                "fallback": 是否使用了降级,
            }
        """
        # 检查缓存
        cache_key = f"cache:{source_name}"
        if use_cache and cache_key in self.cache:
            cached = self.cache[cache_key]
            if datetime.now() - cached["timestamp"] < timedelta(seconds=self.cache_ttl):
                return {
                    "data": cached["data"],
                    "source": cached["source"],
                    "confidence": 0.95,  # 缓存数据可信度高
                    "fallback": False,
                }
        
        # 获取数据源列表
        sources = self.sources.get(source_name, [])
        if not sources:
            raise ValueError(f"未找到数据源: {source_name}")
        
        errors = []
        
        # 按优先级尝试每个数据源
        for source in sources:
            if not source.enabled:
                continue
            
            try:
                result = await self._fetch_from_source(source)
                
                # 更新统计
                source.last_success = datetime.now()
                source.success_count += 1
                
                # 缓存结果
                if use_cache:
                    self.cache[cache_key] = {
                        "data": result,
                        "source": source.url,
                        "timestamp": datetime.now(),
                    }
                
                return {
                    "data": result,
                    "source": source.url,
                    "confidence": self._calculate_confidence(source),
                    "fallback": False,
                }
                
            except Exception as e:
                source.last_failure = datetime.now()
                source.failure_count += 1
                errors.append(f"{source.url}: {str(e)}")
                
                if not use_fallback:
                    raise
        
        # 所有数据源都失败
        raise Exception(f"所有数据源失败: {'; '.join(errors)}")
    
    async def _fetch_from_source(self, source: DataSource) -> Any:
        """从单个数据源获取数据"""
        start_time = time.time()
        
        # 处理 data: URL (内置响应)
        if source.url.startswith("data:"):
            # 解析 data URL
            import json
            data_str = source.url.split(",", 1)[1]
            result = json.loads(data_str)
            
            # 模拟延迟
            latency_ms = 10
            source.total_latency_ms += latency_ms
            source.avg_latency_ms = source.total_latency_ms // max(1, source.success_count)
            
            return result
        
        async with httpx.AsyncClient(timeout=source.timeout) as client:
            if source.method.upper() == "GET":
                response = await client.get(
                    source.url,
                    headers=source.headers,
                    params=source.params,
                )
            else:
                response = await client.post(
                    source.url,
                    headers=source.headers,
                    json=source.params,
                )
            
            response.raise_for_status()
            
            # 更新延迟统计
            latency_ms = int((time.time() - start_time) * 1000)
            source.total_latency_ms += latency_ms
            source.avg_latency_ms = source.total_latency_ms // source.success_count if source.success_count > 0 else latency_ms
            
            # 解析响应
            if source.parser:
                return source.parser(response)
            else:
                return response.json()
    
    def _calculate_confidence(self, source: DataSource) -> float:
        """计算数据可信度"""
        if source.success_count == 0:
            return 0.5
        
        success_rate = source.success_count / (source.success_count + source.failure_count)
        
        # 延迟因子：延迟越低可信度越高
        latency_factor = max(0.5, 1 - source.avg_latency_ms / 1000)
        
        # 综合可信度
        confidence = success_rate * 0.7 + latency_factor * 0.3
        
        return round(confidence, 2)
    
    def get_source_stats(self, source_name: str) -> Dict[str, Any]:
        """获取数据源统计"""
        sources = self.sources.get(source_name, [])
        return {
            "name": source_name,
            "sources": [
                {
                    "url": s.url,
                    "priority": s.priority,
                    "enabled": s.enabled,
                    "success_rate": s.success_count / (s.success_count + s.failure_count) if s.success_count + s.failure_count > 0 else 0,
                    "avg_latency_ms": s.avg_latency_ms,
                    "last_success": s.last_success.isoformat() if s.last_success else None,
                    "last_failure": s.last_failure.isoformat() if s.last_failure else None,
                }
                for s in sources
            ],
        }
    
    def clear_cache(self, source_name: Optional[str] = None):
        """清除缓存"""
        if source_name:
            self.cache.pop(f"cache:{source_name}", None)
        else:
            self.cache.clear()
    
    def disable_source(self, source_url: str):
        """禁用数据源"""
        for sources in self.sources.values():
            for source in sources:
                if source.url == source_url:
                    source.enabled = False
    
    def enable_source(self, source_url: str):
        """启用数据源"""
        for sources in self.sources.values():
            for source in sources:
                if source.url == source_url:
                    source.enabled = True