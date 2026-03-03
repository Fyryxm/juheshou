"""
预置数据源配置
"""

from typing import Dict, Any, Callable
from ..core.aggregator import DataSource


def parse_coingecko_btc(response) -> Dict[str, Any]:
    """解析 CoinGecko BTC 价格"""
    data = response.json()
    bitcoin = data.get("bitcoin", {})
    return {
        "price": bitcoin.get("usd"),
        "change_24h": bitcoin.get("usd_24h_change", 0),
        "market_cap": bitcoin.get("usd_market_cap"),
        "volume_24h": bitcoin.get("usd_24h_vol"),
    }


def parse_coingecko_eth(response) -> Dict[str, Any]:
    """解析 CoinGecko ETH 价格"""
    data = response.json()
    ethereum = data.get("ethereum", {})
    return {
        "price": ethereum.get("usd"),
        "change_24h": ethereum.get("usd_24h_change", 0),
        "market_cap": ethereum.get("usd_market_cap"),
        "volume_24h": ethereum.get("usd_24h_vol"),
    }


def parse_metals_gold(response) -> Dict[str, Any]:
    """解析 Metals.live 黄金价格"""
    data = response.json()
    # Metals.live 返回格式可能不同，需要适配
    if isinstance(data, list) and len(data) > 0:
        return {"price": data[0].get("price", 2650)}
    return {"price": data.get("price", 2650)}


def parse_goldapi(response) -> Dict[str, Any]:
    """解析 GoldAPI.io"""
    data = response.json()
    return {
        "price": data.get("price"),
        "change_24h": data.get("ch"),
        "currency": data.get("currency", "USD"),
    }


def parse_gold_fallback(response) -> Dict[str, Any]:
    """金价 fallback（基于历史均值估算）"""
    # 2024年金均价约 $2300-2600
    # 返回估算值，标记为 fallback
    return {
        "price": 2650.0,
        "change_24h": 0.5,
        "fallback": True,
        "source": "estimated",
        "note": "Primary sources unavailable, using estimated value"
    }


def parse_silver_fallback(response) -> Dict[str, Any]:
    """白银 fallback（基于历史均值估算）"""
    # 2024年白银均价约 $28-32
    return {
        "price": 32.0,
        "change_24h": 0.3,
        "fallback": True,
        "source": "estimated",
        "note": "Primary sources unavailable, using estimated value"
    }


def parse_frankfurter_usd(response) -> Dict[str, Any]:
    """解析 Frankfurter 美元指数"""
    data = response.json()
    rates = data.get("rates", {})
    eur = rates.get("EUR", 0.92)
    # 美元指数近似计算 (DXY ≈ 100/EUR)
    dxy = round(100 / eur, 2) if eur > 0 else 110.0
    return {
        "index": dxy,
        "eur_rate": eur,
    }


def parse_exchange_rate_usd(response) -> Dict[str, Any]:
    """解析 Exchange Rate API 美元指数"""
    data = response.json()
    rates = data.get("rates", {})
    eur = rates.get("EUR", 0.85)
    dxy = round(100 / eur, 2) if eur > 0 else 110.0
    return {
        "index": dxy,
        "eur_rate": eur,
    }


def parse_openweather(response) -> Dict[str, Any]:
    """解析 OpenWeather 天气"""
    data = response.json()
    main = data.get("main", {})
    weather = data.get("weather", [{}])[0]
    return {
        "temp": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "description": weather.get("description"),
        "city": data.get("name"),
    }


def parse_newsapi(response) -> Dict[str, Any]:
    """解析 NewsAPI 头条"""
    data = response.json()
    articles = data.get("articles", [])[:5]
    return {
        "count": len(articles),
        "articles": [
            {
                "title": a.get("title"),
                "source": a.get("source", {}).get("name"),
                "url": a.get("url"),
                "published": a.get("publishedAt"),
            }
            for a in articles
        ],
    }


def parse_fred(response) -> Dict[str, Any]:
    """解析 FRED 经济数据"""
    data = response.json()
    observations = data.get("observations", [])
    if observations:
        latest = observations[-1]
        return {
            "value": float(latest.get("value", 0)),
            "date": latest.get("date"),
        }
    return {"value": None, "date": None}


def parse_goldprice_org(response) -> Dict[str, Any]:
    """解析 goldprice.org 网页金价"""
    import re
    text = response.text
    
    # 查找金价模式：$2,650.50 或 2650.50
    patterns = [
        r'\$([0-9,]+\.?\d*)\s*(?:USD|per|oz)',
        r'Gold.*?([0-9,]+\.?\d*)\s*USD',
        r'XAU.*?([0-9,]+\.?\d*)',
        r'price[^0-9]*([0-9,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return {"price": float(price_str)}
            except ValueError:
                continue
    
    # 备用：返回估算值（基于历史平均）
    return {"price": 2650.0, "fallback": True}


def parse_kitco_gold(response) -> Dict[str, Any]:
    """解析 Kitco 金价"""
    import re
    text = response.text
    
    # Kitco 格式：Gold $2,650.30
    patterns = [
        r'Gold[^0-9]*\$?([0-9,]+\.?\d*)',
        r'XAU[^0-9]*([0-9,]+\.?\d*)',
        r'price[^0-9]*([0-9,]+\.\d{2})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return {"price": float(price_str)}
            except ValueError:
                continue
    
    return {"price": 2650.0, "fallback": True}


def parse_silverprice_org(response) -> Dict[str, Any]:
    """解析白银价格"""
    import re
    text = response.text
    
    patterns = [
        r'\$([0-9,]+\.?\d*)\s*(?:USD|per|oz)',
        r'Silver[^0-9]*\$?([0-9,]+\.?\d*)',
        r'XAG[^0-9]*([0-9,]+\.?\d*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            price_str = match.group(1).replace(',', '')
            try:
                return {"price": float(price_str)}
            except ValueError:
                continue
    
    return {"price": 32.0, "fallback": True}


# ==================== 数据源配置 ====================

PRESET_SOURCES = {
    # ========== 加密货币 ==========
    "btc": [
        DataSource(
            name="btc",
            url="https://api.coingecko.com/api/v3/simple/price",
            method="GET",
            params={"ids": "bitcoin", "vs_currencies": "usd", "include_24hr_change": "true", "include_market_cap": "true", "include_24hr_vol": "true"},
            priority=1,
            timeout=5,
            parser=parse_coingecko_btc,
        ),
        # 备选源可以在这里添加
    ],
    
    "eth": [
        DataSource(
            name="eth",
            url="https://api.coingecko.com/api/v3/simple/price",
            method="GET",
            params={"ids": "ethereum", "vs_currencies": "usd", "include_24hr_change": "true", "include_market_cap": "true", "include_24hr_vol": "true"},
            priority=1,
            timeout=5,
            parser=parse_coingecko_eth,
        ),
    ],
    
    # ========== 贵金属 ==========
    "gold": [
        # 主源：metals.live（当前 SSL 问题，保留）
        DataSource(
            name="gold",
            url="https://api.metals.live/v1/spot/gold",
            method="GET",
            priority=1,
            timeout=3,
            parser=parse_metals_gold,
        ),
        # Fallback：估算值（基于历史均值）
        DataSource(
            name="gold",
            url="data:text/plain,{\"price\":2650,\"fallback\":true}",
            method="GET",
            priority=2,
            timeout=1,
            parser=parse_gold_fallback,
        ),
    ],
    
    "silver": [
        # 主源：metals.live（当前 SSL 问题，保留）
        DataSource(
            name="silver",
            url="https://api.metals.live/v1/spot/silver",
            method="GET",
            priority=1,
            timeout=3,
            parser=parse_metals_gold,
        ),
        # Fallback：估算值（基于历史均值）
        DataSource(
            name="silver",
            url="data:text/plain,{\"price\":32,\"fallback\":true}",
            method="GET",
            priority=2,
            timeout=1,
            parser=parse_silver_fallback,
        ),
    ],
    
    # ========== 汇率 ==========
    "usd": [
        DataSource(
            name="usd",
            url="https://api.exchangerate-api.com/v4/latest/USD",
            method="GET",
            priority=1,
            timeout=5,
            parser=parse_exchange_rate_usd,
        ),
    ],
    
    # ========== 天气 ==========
    "weather": [
        DataSource(
            name="weather",
            url="https://api.openweathermap.org/data/2.5/weather",
            method="GET",
            params={"q": "Beijing", "appid": "YOUR_API_KEY", "units": "metric"},
            priority=1,
            timeout=3,
            parser=parse_openweather,
        ),
    ],
    
    # ========== 新闻 ==========
    "news": [
        DataSource(
            name="news",
            url="https://newsapi.org/v2/top-headlines",
            method="GET",
            params={"country": "us", "apiKey": "YOUR_API_KEY"},
            priority=1,
            timeout=5,
            parser=parse_newsapi,
        ),
    ],
    
    # ========== 经济数据 ==========
    "fred_gdp": [
        DataSource(
            name="fred_gdp",
            url="https://api.stlouisfed.org/fred/series/observations",
            method="GET",
            params={"series_id": "GDP", "api_key": "YOUR_API_KEY", "file_type": "json"},
            priority=1,
            timeout=5,
            parser=parse_fred,
        ),
    ],
}


def get_preset_sources() -> Dict[str, list]:
    """获取预置数据源"""
    return PRESET_SOURCES


def register_all_sources(aggregator):
    """注册所有预置数据源到聚合器"""
    for source_name, sources in PRESET_SOURCES.items():
        for source in sources:
            aggregator.register_source(source)