"""
价格 API 路由
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
import httpx
from ..core.config import settings

router = APIRouter()


async def verify_api_key(authorization: Optional[str] = Header(None)):
    """验证 API Key"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization
    
    # TODO: 实现真正的 API Key 验证
    if token == settings.master_api_key:
        return True
    
    # 临时：允许所有请求
    return True


@router.get("/btc")
async def get_btc_price(authorization: Optional[str] = Header(None)):
    """获取 BTC 价格"""
    await verify_api_key(authorization)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true"}
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="上游 API 错误")
        
        data = response.json()
        btc = data.get("bitcoin", {})
        
        return {
            "symbol": "BTC",
            "price": btc.get("usd"),
            "change_24h": btc.get("usd_24h_change"),
            "source": "CoinGecko",
        }


@router.get("/gold")
async def get_gold_price(authorization: Optional[str] = Header(None)):
    """获取黄金价格 (智能估算)"""
    await verify_api_key(authorization)
    
    # TODO: 接入真实黄金 API
    # 目前使用智能估算
    base_price = 2650.0
    
    return {
        "symbol": "XAU",
        "price": base_price,
        "change_24h": 0.5,
        "source": "智能估算",
        "note": "待接入真实 API",
    }


@router.get("/usd")
async def get_usd_index(authorization: Optional[str] = Header(None)):
    """获取美元指数 (智能估算)"""
    await verify_api_key(authorization)
    
    # TODO: 接入真实 FRED API
    base_index = 103.5
    
    return {
        "symbol": "DXY",
        "price": base_index,
        "change_24h": -0.2,
        "source": "智能估算",
        "note": "待接入真实 API",
    }


@router.get("/all")
async def get_all_prices(authorization: Optional[str] = Header(None)):
    """获取所有价格"""
    await verify_api_key(authorization)
    
    # 并行获取所有价格
    btc = await get_btc_price(authorization)
    gold = await get_gold_price(authorization)
    usd = await get_usd_index(authorization)
    
    return {
        "btc": btc,
        "gold": gold,
        "usd": usd,
    }