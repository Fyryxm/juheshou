"""
报告 API 路由
"""

from fastapi import APIRouter, HTTPException, Header
from typing import Optional
from datetime import datetime
from ..api.prices import get_btc_price, get_gold_price, get_usd_index

router = APIRouter()


@router.get("/daily")
async def get_daily_report(authorization: Optional[str] = Header(None)):
    """获取每日市场报告"""
    
    # 获取所有价格
    btc = await get_btc_price(authorization)
    gold = await get_gold_price(authorization)
    usd = await get_usd_index(authorization)
    
    # 计算市场情绪
    btc_change = btc.get("change_24h", 0)
    gold_change = gold.get("change_24h", 0)
    
    if btc_change > 2 and gold_change < 0:
        sentiment = "风险偏好 (Risk-On)"
    elif btc_change < -2 and gold_change > 0:
        sentiment = "避险情绪 (Risk-Off)"
    else:
        sentiment = "中性震荡 (Neutral)"
    
    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "prices": {
            "btc": btc,
            "gold": gold,
            "usd": usd,
        },
        "analysis": {
            "sentiment": sentiment,
            "btc_vs_gold": btc_change - gold_change,
            "recommendation": "观望" if sentiment == "中性震荡 (Neutral)" else "顺势操作",
        },
    }


@router.get("/weekly")
async def get_weekly_report(authorization: Optional[str] = Header(None)):
    """获取每周市场报告"""
    # TODO: 实现周报
    return {
        "message": "周报功能开发中",
        "available": False,
    }