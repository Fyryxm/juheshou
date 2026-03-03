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


def parse_frankfurter_usd(response) -> Dict[str, Any]:
    """解析 Frankfurter 美元指数"""
    data = response.json()
    rates = data.get("rates", {})
    eur = rates.get("EUR", 0.92)
    # 美元指数近似计算
    dxy = 100 / eur
    return {
        "index": round(dxy, 2),
        "eur_rate": eur,
    }


def parse_exchange_rate_usd(response) -> Dict[str, Any]:
    """解析 Exchange Rate API 美元指数"""
    data = response.json()
    rates = data.get("conversion_rates", {})
    eur = rates.get("EUR", 0.92)
    dxy = 100 / eur
    return {
        "index": round(dxy, 2),
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
        DataSource(
            name="gold",
            url="https://api.metals.live/v1/spot/gold",
            method="GET",
            priority=1,
            timeout=3,
            parser=parse_metals_gold,
        ),
        # 备选源：GoldAPI.io (需要 API Key)
        # DataSource(
        #     name="gold",
        #     url="https://www.goldapi.io/api/XAU/USD",
        #     method="GET",
        #     headers={"x-access-token": "YOUR_API_KEY"},
        #     priority=2,
        #     parser=parse_goldapi,
        # ),
    ],
    
    "silver": [
        DataSource(
            name="silver",
            url="https://api.metals.live/v1/spot/silver",
            method="GET",
            priority=1,
            timeout=3,
            parser=parse_metals_gold,  # 同样的解析器
        ),
    ],
    
    # ========== 汇率 ==========
    "usd": [
        DataSource(
            name="usd",
            url="https://api.frankfurter.app/latest",
            method="GET",
            params={"from": "USD", "to": "EUR"},
            priority=1,
            timeout=3,
            parser=parse_frankfurter_usd,
        ),
        DataSource(
            name="usd",
            url="https://v6.exchangerate-api.com/v6/YOUR_API_KEY/latest/USD",
            method="GET",
            priority=2,
            timeout=3,
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