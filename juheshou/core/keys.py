"""
API Key 管理模块
"""

from typing import Dict, Optional
from datetime import datetime
import hashlib
import secrets
from dataclasses import dataclass
import json
from pathlib import Path


@dataclass
class APIKey:
    """API Key 配置"""
    key: str
    key_hash: str
    name: str
    tier: str = "free"
    requests_limit: int = 100
    created_at: str = ""
    expires_at: Optional[str] = None
    enabled: bool = True


class KeyManager:
    """
    API Key 管理器
    
    功能:
    - 创建 API Key
    - 验证 API Key
    - 管理配额
    - 持久化存储
    """
    
    TIERS = {
        "free": {"limit": 100, "price": 0},
        "developer": {"limit": 10000, "price": 29},
        "pro": {"limit": 100000, "price": 99},
        "enterprise": {"limit": -1, "price": 499},  # -1 = 无限
    }
    
    def __init__(self, storage_path: str = None):
        self.storage_path = storage_path or "~/.juheshou/api_keys.json"
        self.keys: Dict[str, APIKey] = {}
        self._load()
    
    def _load(self):
        """从文件加载 API Keys"""
        path = Path(self.storage_path).expanduser()
        if path.exists():
            try:
                with open(path, 'r') as f:
                    data = json.load(f)
                    for key_hash, key_data in data.items():
                        self.keys[key_hash] = APIKey(
                            key=key_data.get('key', ''),
                            key_hash=key_hash,
                            name=key_data.get('name', ''),
                            tier=key_data.get('tier', 'free'),
                            requests_limit=key_data.get('requests_limit', 100),
                            created_at=key_data.get('created_at', ''),
                            expires_at=key_data.get('expires_at'),
                            enabled=key_data.get('enabled', True),
                        )
            except Exception as e:
                print(f"加载 API Keys 失败: {e}")
    
    def _save(self):
        """保存 API Keys 到文件"""
        path = Path(self.storage_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {}
        for key_hash, key in self.keys.items():
            data[key_hash] = {
                'key': key.key,
                'name': key.name,
                'tier': key.tier,
                'requests_limit': key.requests_limit,
                'created_at': key.created_at,
                'expires_at': key.expires_at,
                'enabled': key.enabled,
            }
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _hash_key(self, key: str) -> str:
        """哈希 API Key"""
        return hashlib.sha256(key.encode()).hexdigest()[:32]
    
    def create_key(self, name: str, tier: str = "free") -> Dict[str, Any]:
        """创建新的 API Key"""
        # 生成随机 Key
        key = f"juheshou_{secrets.token_hex(16)}"
        key_hash = self._hash_key(key)
        
        # 获取配额
        tier_config = self.TIERS.get(tier, self.TIERS["free"])
        
        # 创建记录
        api_key = APIKey(
            key=key,
            key_hash=key_hash,
            name=name,
            tier=tier,
            requests_limit=tier_config["limit"],
            created_at=datetime.now().isoformat(),
        )
        
        self.keys[key_hash] = api_key
        self._save()
        
        return {
            "key": key,  # 只返回一次
            "key_hash": key_hash,
            "name": name,
            "tier": tier,
            "requests_limit": tier_config["limit"],
            "created_at": api_key.created_at,
        }
    
    def verify_key(self, key: str) -> Optional[APIKey]:
        """验证 API Key"""
        key_hash = self._hash_key(key)
        
        if key_hash not in self.keys:
            return None
        
        api_key = self.keys[key_hash]
        
        # 检查是否启用
        if not api_key.enabled:
            return None
        
        # 检查是否过期
        if api_key.expires_at:
            if datetime.now() > datetime.fromisoformat(api_key.expires_at):
                return None
        
        return api_key
    
    def get_key_info(self, key_hash: str) -> Optional[Dict]:
        """获取 API Key 信息"""
        if key_hash not in self.keys:
            return None
        
        api_key = self.keys[key_hash]
        
        return {
            "key_hash": api_key.key_hash[:8] + "...",
            "name": api_key.name,
            "tier": api_key.tier,
            "requests_limit": api_key.requests_limit,
            "created_at": api_key.created_at,
            "expires_at": api_key.expires_at,
            "enabled": api_key.enabled,
        }
    
    def list_keys(self) -> list:
        """列出所有 API Keys"""
        return [
            self.get_key_info(key_hash)
            for key_hash in self.keys
        ]
    
    def revoke_key(self, key_hash: str) -> bool:
        """吊销 API Key"""
        if key_hash not in self.keys:
            return False
        
        self.keys[key_hash].enabled = False
        self._save()
        return True
    
    def delete_key(self, key_hash: str) -> bool:
        """删除 API Key"""
        if key_hash not in self.keys:
            return False
        
        del self.keys[key_hash]
        self._save()
        return True
    
    def upgrade_tier(self, key_hash: str, tier: str) -> bool:
        """升级套餐"""
        if key_hash not in self.keys:
            return False
        
        if tier not in self.TIERS:
            return False
        
        tier_config = self.TIERS[tier]
        self.keys[key_hash].tier = tier
        self.keys[key_hash].requests_limit = tier_config["limit"]
        self._save()
        return True


from typing import Any

# 全局 Key 管理器
key_manager = KeyManager()