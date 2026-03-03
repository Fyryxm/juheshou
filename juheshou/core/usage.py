"""
使用追踪模块
记录每个 API Key 的请求数、延迟、错误率
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import json
from pathlib import Path


@dataclass
class UsageRecord:
    """使用记录"""
    timestamp: str
    endpoint: str
    source: str
    latency_ms: int
    success: bool
    confidence: float
    fallback_used: bool


@dataclass
class APIKeyUsage:
    """API Key 使用统计"""
    key_hash: str
    tier: str = "free"
    requests_limit: int = 100
    requests_today: int = 0
    requests_total: int = 0
    avg_latency_ms: int = 0
    error_rate: float = 0.0
    last_request: Optional[str] = None
    records: list = field(default_factory=list)
    
    # 时间窗口统计
    hourly_requests: Dict[str, int] = field(default_factory=dict)  # {"2026-03-03T11": 50}
    daily_requests: Dict[str, int] = field(default_factory=dict)   # {"2026-03-03": 100}


class UsageTracker:
    """
    使用追踪器
    
    功能:
    - 记录每个 API Key 的请求
    - 计算统计数据
    - 配额检查
    - 持久化存储
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "~/.juheshou/usage.json"
        self.usage_data: Dict[str, APIKeyUsage] = {}
        self._load()
    
    def _load(self):
        """从文件加载使用数据"""
        path = Path(self.storage_path).expanduser()
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    for key_hash, usage in data.items():
                        self.usage_data[key_hash] = APIKeyUsage(
                            key_hash=usage.get('key_hash', key_hash),
                            tier=usage.get('tier', 'free'),
                            requests_limit=usage.get('requests_limit', 100),
                            requests_today=usage.get('requests_today', 0),
                            requests_total=usage.get('requests_total', 0),
                            avg_latency_ms=usage.get('avg_latency_ms', 0),
                            error_rate=usage.get('error_rate', 0.0),
                            last_request=usage.get('last_request'),
                            hourly_requests=usage.get('hourly_requests', {}),
                            daily_requests=usage.get('daily_requests', {}),
                        )
            except Exception as e:
                print(f"加载使用数据失败: {e}")
    
    def _save(self):
        """保存使用数据到文件"""
        path = Path(self.storage_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for key_hash, usage in self.usage_data.items():
            data[key_hash] = {
                'key_hash': usage.key_hash,
                'tier': usage.tier,
                'requests_limit': usage.requests_limit,
                'requests_today': usage.requests_today,
                'requests_total': usage.requests_total,
                'avg_latency_ms': usage.avg_latency_ms,
                'error_rate': usage.error_rate,
                'last_request': usage.last_request,
                'hourly_requests': usage.hourly_requests,
                'daily_requests': usage.daily_requests,
            }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def record_request(
        self,
        key_hash: str,
        endpoint: str,
        source: str,
        latency_ms: int,
        success: bool,
        confidence: float = 1.0,
        fallback_used: bool = False,
        tier: str = "free",
        requests_limit: int = 100,
    ):
        """记录一次请求"""
        now = datetime.now()
        today = now.strftime("%Y-%m-%d")
        hour = now.strftime("%Y-%m-%dT%H")
        
        # 获取或创建使用记录
        if key_hash not in self.usage_data:
            self.usage_data[key_hash] = APIKeyUsage(
                key_hash=key_hash,
                tier=tier,
                requests_limit=requests_limit,
            )
        
        usage = self.usage_data[key_hash]
        
        # 更新统计
        usage.requests_total += 1
        usage.requests_today += 1
        usage.last_request = now.isoformat()
        
        # 时间窗口统计
        usage.daily_requests[today] = usage.daily_requests.get(today, 0) + 1
        usage.hourly_requests[hour] = usage.hourly_requests.get(hour, 0) + 1
        
        # 平均延迟
        if usage.avg_latency_ms == 0:
            usage.avg_latency_ms = latency_ms
        else:
            usage.avg_latency_ms = (usage.avg_latency_ms + latency_ms) // 2
        
        # 错误率
        if not success:
            total = usage.requests_total
            errors = int(usage.error_rate * (total - 1)) + 1
            usage.error_rate = errors / total
        
        # 保存
        self._save()
    
    def check_quota(self, key_hash: str) -> Dict[str, Any]:
        """检查配额"""
        if key_hash not in self.usage_data:
            return {"allowed": True, "remaining": 100}
        
        usage = self.usage_data[key_hash]
        
        # 清理旧数据（每天重置）
        today = datetime.now().strftime("%Y-%m-%d")
        if today not in usage.daily_requests:
            usage.requests_today = 0
            usage.daily_requests[today] = 0
        
        remaining = usage.requests_limit - usage.requests_today
        allowed = remaining > 0 or usage.tier == "enterprise"
        
        return {
            "allowed": allowed,
            "remaining": max(0, remaining),
            "limit": usage.requests_limit,
            "tier": usage.tier,
            "requests_today": usage.requests_today,
            "requests_total": usage.requests_total,
            "reset_at": f"{today}T23:59:59",
        }
    
    def get_usage_stats(self, key_hash: str) -> Dict[str, Any]:
        """获取使用统计"""
        if key_hash not in self.usage_data:
            return {"error": "API Key not found"}
        
        usage = self.usage_data[key_hash]
        
        return {
            "key_hash": usage.key_hash[:8] + "...",
            "tier": usage.tier,
            "requests_today": usage.requests_today,
            "requests_total": usage.requests_total,
            "requests_limit": usage.requests_limit,
            "avg_latency_ms": usage.avg_latency_ms,
            "error_rate": round(usage.error_rate * 100, 2),
            "last_request": usage.last_request,
            "daily_requests": dict(list(usage.daily_requests.items())[-7:]),  # 最近 7 天
            "hourly_requests": dict(list(usage.hourly_requests.items())[-24:]),  # 最近 24 小时
        }
    
    def cleanup_old_data(self, days: int = 30):
        """清理旧数据"""
        cutoff = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")
        
        for usage in self.usage_data.values():
            # 清理每日数据
            usage.daily_requests = {
                k: v for k, v in usage.daily_requests.items()
                if k >= cutoff_str
            }
            
            # 清理每小时数据
            cutoff_hour = cutoff.strftime("%Y-%m-%dT%H")
            usage.hourly_requests = {
                k: v for k, v in usage.hourly_requests.items()
                if k >= cutoff_hour
            }
        
        self._save()


# 全局使用追踪器
tracker = UsageTracker()