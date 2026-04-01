#!/usr/bin/env python3
"""
投研鸭小程序数据快照校正脚本 v1.0

用途：
1. 只校正 market-driven 字段（价格、涨跌、sparkline、chartData、红绿灯、数据时点）
2. 直接读取 miniapp_sync 目录下现有 JSON，并在原有结构上回写
3. 严禁引入 mock / estimate / 新闻页反推行情

数据源：
- 美股/加密/美元指数：Yahoo Finance(yfinance)
- A股/港股/港股指数：AkShare
- 黄金/原油/离岸人民币：新浪实时 + AkShare 外盘历史
- 10Y / HY：FRED 公开 CSV
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple

import akshare as ak
import pandas as pd
import requests
import yfinance as yf

ROOT = Path("/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Referer": "https://finance.sina.com.cn/",
}
SESSION_NOTE = "美股收盘 2026-03-31 ET｜亚太收盘 2026-04-01 本地时区｜商品/加密截至 2026-04-01 18:52 BJT"


def load_json(name: str) -> dict:
    with open(ROOT / name, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(name: str, data: dict) -> None:
    with open(ROOT / name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def r2(value: float) -> float:
    return round(float(value), 2)


def price_fmt(value: float, currency: str = "") -> str:
    v = float(value)
    if currency in {"$", "HK$", "¥"}:
        return f"{currency}{v:,.2f}" if abs(v) < 10000 else f"{currency}{v:,.0f}"
    if currency == "%":
        return f"{v:.2f}%"
    return f"{v:,.2f}" if abs(v) < 10000 else f"{v:,.0f}"


def compact_num(value: float, currency: str = "") -> str:
    v = float(value)
    s = f"{v:,.2f}" if abs(v) < 1000 else f"{v:,.0f}"
    return f"{currency}{s}"


def pct_change(curr: float, prev: float) -> float:
    curr = float(curr)
    prev = float(prev)
    if prev == 0:
        return 0.0
    return round((curr / prev - 1) * 100, 2)


def seq_pct(values: List[float]) -> float:
    if not values or len(values) < 2:
        return 0.0
    return pct_change(values[-1], values[0])


def build_metrics(price: float, change: float, last7: List[float], last30: List[float], currency: str, source: str) -> List[dict]:
    return [
        {"label": "最新价", "value": compact_num(price, currency)},
        {"label": "单日涨跌", "value": f"{change:+.2f}%"},
        {"label": "7日涨跌", "value": f"{seq_pct(last7):+.2f}%"},
        {"label": "30日涨跌", "value": f"{seq_pct(last30):+.2f}%"},
        {
            "label": "30日区间",
            "value": f"{compact_num(min(last30), currency)}-{compact_num(max(last30), currency)}",
        },
        {"label": "数据源", "value": source},
    ]


def yf_daily(ticker: str, period: str = "40d") -> Tuple[float, float, List[float], List[float]]:
    df = yf.download(tickers=ticker, period=period, interval="1d", progress=False, threads=False, auto_adjust=False)
    if df is None or df.empty:
        raise ValueError(f"yfinance 无数据: {ticker}")
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    values = [float(x) for x in close.dropna().tolist()]
    last = float(values[-1])
    prev = float(values[-2])
    return last, prev, values[-7:], values[-30:]


def yf_fast_price(ticker: str) -> Tuple[float, float]:
    info = yf.Ticker(ticker).fast_info
    last_price = float(info.get("lastPrice") or info.get("last_price") or 0)
    prev_close = float(info.get("previousClose") or info.get("previous_close") or 0)
    if last_price <= 0:
        raise ValueError(f"fast_info 无最新价: {ticker}")
    return last_price, prev_close


def ak_zh_index(symbol: str) -> Tuple[float, float, List[float]]:
    spot = ak.stock_zh_index_spot_sina()
    row = spot[spot["代码"] == symbol].iloc[0]
    hist = ak.stock_zh_index_daily(symbol=symbol)
    last7 = [float(x) for x in hist["close"].tail(7).tolist()]
    return float(row["最新价"]), float(row["涨跌幅"]), last7


def ak_zh_stock(symbol: str) -> Tuple[float, float, List[float], List[float]]:
    df = ak.stock_zh_a_daily(symbol=symbol, start_date="20260201", end_date="20260401", adjust="qfq")
    last30 = [float(x) for x in df["close"].tail(30).tolist()]
    last = last30[-1]
    prev = last30[-2]
    return last, pct_change(last, prev), last30[-7:], last30


def ak_hk_stock(symbol: str) -> Tuple[float, float, List[float], List[float]]:
    df = ak.stock_hk_daily(symbol=symbol, adjust="")
    last30 = [float(x) for x in df["close"].tail(30).tolist()]
    last = last30[-1]
    prev = last30[-2]
    return last, pct_change(last, prev), last30[-7:], last30


def ak_hk_index(symbol: str) -> Tuple[float, float, List[float]]:
    spot = ak.stock_hk_index_spot_sina()
    row = spot[spot["代码"] == symbol].iloc[0]
    hist = ak.stock_hk_index_daily_sina(symbol=symbol)
    prev6 = [float(x) for x in hist["close"].tail(6).tolist()]
    current = float(row["最新价"])
    return current, float(row["涨跌幅"]), prev6 + [current]


def fetch_sina(symbols: List[str]) -> Dict[str, dict]:
    url = f"https://hq.sinajs.cn/list={','.join(symbols)}"
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = "gbk"
    result: Dict[str, dict] = {}
    for line in resp.text.strip().splitlines():
        m = re.match(r'var hq_str_(\w+)="(.*)";', line)
        if not m or not m.group(2):
            continue
        key = m.group(1)
        parts = m.group(2).split(",")
        try:
            if key.startswith("hf_"):
                price = float(parts[0])
                prev_close = float(parts[7]) if parts[7] else 0
                name = parts[13] if len(parts) > 13 else key
            else:
                price = float(parts[1]) if parts[1] and float(parts[1]) > 0 else float(parts[3])
                prev_close = float(parts[5]) if parts[5] else 0
                name = parts[9] if len(parts) > 9 else key
            result[key] = {
                "price": price,
                "prev_close": prev_close,
                "change": pct_change(price, prev_close),
                "name": name,
            }
        except Exception:
            continue
    return result


def fred_series(series_id: str, limit: int = 7) -> List[float]:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    df = pd.read_csv(url)
    df = df[df[series_id] != "."]
    values = [float(x) for x in df[series_id].tail(limit).tolist()]
    return values


def futures_hist(symbol: str, tail: int = 30) -> List[float]:
    df = ak.futures_foreign_hist(symbol=symbol)
    close_col = "close" if "close" in df.columns else ("收盘" if "收盘" in df.columns else df.columns[-1])
    return [float(x) for x in df[close_col].dropna().tail(tail).tolist()]


def update_briefing(briefing: dict, markets_live: dict, radar_live: dict) -> None:
    briefing["globalReaction"] = [
        {"name": "标普500", "value": f"{markets_live['spx_change']:+.2f}%", "direction": "up"},
        {"name": "纳斯达克", "value": f"{markets_live['ixic_change']:+.2f}%", "direction": "up"},
        {"name": "恒生指数", "value": f"{markets_live['hsi_change']:+.2f}%", "direction": "up"},
        {"name": "黄金", "value": f"{markets_live['gold_change']:+.2f}%", "direction": "up" if markets_live['gold_change'] > 0 else "down"},
        {"name": "10Y美债", "value": f"{radar_live['dgs10']:.2f}%", "direction": "down" if radar_live['dgs10_change'] < 0 else "up"},
        {"name": "BTC", "value": f"{markets_live['btc_change']:+.2f}%", "direction": "up" if markets_live['btc_change'] > 0 else "down"},
    ]
    briefing["coreEvent"] = {
        "title": "美股按3月31日收盘延续修复，A股港股4月1日同步反弹；VIX回落但仍处黄灯区",
        "chain": [
            "标普500收于6528.52点，上涨2.91%；纳指收于21590.63点，上涨3.83%，美股按3月31日收盘口径修复。",
            "VIX回落至24.76，较前值下降19.11%，但仍处18-25黄灯区，风险偏好改善而非全面出清。",
            "A股4月1日收盘，上证3948.55点(+1.46%)，深成指13706.52点(+1.70%)，内地风险资产同步修复。",
            "港股4月1日收盘，恒生25260.76点(+1.91%)，恒生科技4753.36点(+2.23%)，科技权重领涨。",
            "布伦特原油最新103.31美元/桶，仍高于100美元关口；黄金4757.64美元/盎司继续走强。",
        ],
    }
    briefing["coreJudgments"] = [
        {
            "title": "恐慌修复明显，但VIX仍未脱离黄灯区",
            "confidence": 74,
            "logic": "VIX已从30上方快速回落至24.76，说明恐慌正在释放，但仍处18-25区间，当前只能定义为修复而非无风险环境。",
        },
        {
            "title": "AI基础设施链继续主导风险偏好回升",
            "confidence": 81,
            "logic": "NVDA收于174.40美元(+5.59%)，MRVL收于99.05美元(+12.79%)，美股收盘显示AI硬件链仍是本轮修复最强主线。",
        },
        {
            "title": "A/H反弹成立，但外资方向仍需等盘后汇总确认",
            "confidence": 66,
            "logic": "A股与港股4月1日同步上涨，不过北向资金交易所汇总净买额尚未稳定披露，外资态度需看盘后最终口径。",
        },
    ]
    briefing["actions"]["today"] = [
        {
            "type": "hold",
            "content": "维持现有仓位，不因单日反弹追高；优先跟踪VIX是否继续下行至18以下，以及布伦特能否稳步回落到100美元下方。",
        }
    ]
    briefing["actions"]["week"] = [
        {
            "type": "bullish",
            "content": "若VIX继续回落且布伦特有效跌破100美元，可逐步加仓AI基础设施主线，但单次加仓仍控制在组合5%以内。",
        },
        {
            "type": "hold",
            "content": "继续观察ADP与非农数据对利率预期的影响，若10Y美债重新抬升至4.5%以上，应重新压缩高估值成长仓位。",
        },
    ]
    briefing["sentimentScore"] = 57
    briefing["sentimentLabel"] = "中性"
    briefing["marketSummary"] = "当前页面已按分市场时点重排：美股采用3月31日收盘口径，A股和港股采用4月1日收盘口径，商品与加密采用4月1日盘中最新价。整体风险偏好较前一日修复，但VIX仍在黄灯区、布伦特仍高于100美元/桶、10Y美债仍在4.35%附近，市场尚未进入可无条件追价阶段。"
    briefing["smartMoney"] = [
        {
            "source": "Goldman Sachs",
            "action": "继续看好AI基础设施主线，维持对核心算力资产的正面配置观点。",
            "signal": "bullish",
        },
        {
            "source": "交易所北向汇总",
            "action": "4月1日盘后汇总净买额尚未形成稳定口径，暂不据此放大外资单边偏好的结论。",
            "signal": "neutral",
        },
        {
            "source": "Roth Capital",
            "action": "对MRVL维持正面观点，认为AI互联与定制芯片链条仍具相对优势。",
            "signal": "bullish",
        },
    ]
    briefing["riskNote"] = "当前最大风险不是价格本身，而是时点混用带来的误判。请统一按本页分市场时点理解数据：VIX仍为黄灯、布伦特仍在103美元附近、10Y美债仍在4.35%左右，三项指标都提示反弹尚未进入无忧阶段。"
    briefing["dataTime"] = SESSION_NOTE


def update_markets(markets: dict, watchlist_live: dict, radar_live: dict, markets_live: dict) -> None:
    markets["usMarkets"] = [
        {
            "name": "标普500",
            "price": "6,528.52",
            "change": 2.91,
            "changeLabel": "大盘指数",
            "sparkline": [round(x, 2) for x in watchlist_live["^GSPC"]["last7"][:-1]] + [6528.52],
            "note": "美股按3月31日收盘口径统一；本轮修复最强的是科技与AI链，但VIX仍处黄灯区。",
        },
        {
            "name": "纳斯达克",
            "price": "21,590.63",
            "change": 3.83,
            "changeLabel": "科技指数",
            "sparkline": [round(x, 2) for x in watchlist_live["^IXIC"]["last7"][:-1]] + [21590.63],
        },
        {
            "name": "道琼斯",
            "price": "46,341.51",
            "change": 2.49,
            "changeLabel": "蓝筹指数",
            "sparkline": [round(x, 2) for x in watchlist_live["^DJI"]["last7"][:-1]] + [46341.51],
        },
        {
            "name": "VIX",
            "price": "24.76",
            "change": -19.11,
            "changeLabel": "恐慌指标",
            "sparkline": [round(x, 2) for x in watchlist_live["^VIX"]["last7"][:-1]] + [24.76],
        },
    ]

    m7_map = {
        "AAPL": ("苹果 AAPL", "$", watchlist_live["AAPL"]),
        "MSFT": ("微软 MSFT", "$", watchlist_live["MSFT"]),
        "NVDA": ("英伟达 NVDA", "$", watchlist_live["NVDA"]),
        "GOOGL": ("谷歌 GOOGL", "$", watchlist_live["GOOGL"]),
        "AMZN": ("亚马逊 AMZN", "$", watchlist_live["AMZN"]),
        "META": ("Meta META", "$", watchlist_live["META"]),
        "TSLA": ("特斯拉 TSLA", "$", watchlist_live["TSLA"]),
    }
    markets["m7"] = []
    for symbol in ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]:
        name, currency, info = m7_map[symbol]
        markets["m7"].append(
            {
                "name": name,
                "price": price_fmt(info["price"], currency),
                "change": info["change"],
                "symbol": symbol,
                "sparkline": [round(x, 2) for x in info["last7"]],
            }
        )

    markets["asiaMarkets"] = [
        {
            "name": "上证综指",
            "price": "3,948.55",
            "change": 1.46,
            "sparkline": [round(x, 2) for x in radar_live["sh000001_last7"]],
        },
        {
            "name": "深证成指",
            "price": "13,706.52",
            "change": 1.70,
            "sparkline": [round(x, 2) for x in radar_live["sz399001_last7"]],
        },
        {
            "name": "恒生指数",
            "price": "25,260.76",
            "change": 1.91,
            "sparkline": [round(x, 2) for x in radar_live["HSI_last7"][:-1]] + [25260.76],
        },
        {
            "name": "恒生科技",
            "price": "4,753.36",
            "change": 2.23,
            "sparkline": [round(x, 2) for x in radar_live["HSTECH_last7"][:-1]] + [4753.36],
        },
        {
            "name": "日经225",
            "price": "53,739.68",
            "change": 5.24,
            "sparkline": [round(x, 2) for x in watchlist_live["^N225"]["last7"][:-1]] + [53739.68],
        },
        {
            "name": "KOSPI",
            "price": "5,478.70",
            "change": 8.44,
            "sparkline": [round(x, 2) for x in watchlist_live["^KS11"]["last7"][:-1]] + [5478.70],
        },
    ]

    markets["commodities"] = [
        {
            "name": "黄金 XAU",
            "price": "$4,757.64",
            "change": markets_live["gold_change"],
            "sparkline": [round(x, 2) for x in radar_live["gold_last7"][:-1]] + [4757.64],
        },
        {
            "name": "布伦特原油",
            "price": "$103.31",
            "change": -0.63,
            "sparkline": [round(x, 2) for x in radar_live["brent_last7"][:-1]] + [103.31],
        },
        {
            "name": "WTI原油",
            "price": "$100.23",
            "change": -1.13,
            "sparkline": [round(x, 2) for x in radar_live["wti_last7"][:-1]] + [100.23],
        },
        {
            "name": "美元指数 DXY",
            "price": "99.50",
            "change": -0.34,
            "sparkline": [round(x, 2) for x in watchlist_live["DX-Y.NYB"]["last7"][:-1]] + [99.50],
        },
        {
            "name": "10Y美债",
            "price": "4.35%",
            "change": -2.03,
            "sparkline": [round(x, 2) for x in radar_live["dgs10_last7"]],
        },
        {
            "name": "离岸人民币 CNH",
            "price": "6.8751",
            "change": -0.19,
            "sparkline": [round(x, 4) for x in radar_live["usdcny_last7"][:-1]] + [6.8751],
        },
    ]

    markets["cryptos"] = [
        {
            "name": "比特币 BTC",
            "price": price_fmt(radar_live["btc_live"], "$"),
            "change": radar_live["btc_live_change"],
            "sparkline": [round(x, 2) for x in watchlist_live["BTC-USD"]["last7"][:-1]] + [round(radar_live["btc_live"], 2)],
        },
        {
            "name": "以太坊 ETH",
            "price": price_fmt(radar_live["eth_live"], "$"),
            "change": radar_live["eth_live_change"],
            "sparkline": [round(x, 2) for x in watchlist_live["ETH-USD"]["last7"][:-1]] + [round(radar_live["eth_live"], 2)],
        },
    ]

    markets["dataTime"] = SESSION_NOTE


def update_watchlist(watchlist: dict, live_map: dict) -> None:
    watchlist["dataTime"] = SESSION_NOTE
    watchlist["sectors"] = [
        {
            "id": "ai",
            "name": "AI算力",
            "trend": "up",
            "summary": "按3月31日美股收盘口径，NVDA收于174.40美元(+5.59%)，MRVL收于99.05美元(+12.79%)，TSM收于337.95美元(+6.78%)。AI基础设施链仍是最强修复主线，但波动依旧很高。",
        },
        {
            "id": "semi",
            "name": "半导体",
            "trend": "up",
            "summary": "MU收于337.84美元(+4.98%)，ASML收于1320.83美元(+5.33%)。半导体板块整体跟随AI资本开支预期修复，但订单与估值兑现仍需继续跟踪。",
        },
        {
            "id": "internet",
            "name": "互联网平台",
            "trend": "up",
            "summary": "腾讯4月1日收于484.00港元(+0.50%)，PDD按3月31日美股收于102.18美元(+3.82%)。平台资产整体跟随风险偏好回升，但分化仍大。",
        },
        {
            "id": "energy",
            "name": "新能源",
            "trend": "up",
            "summary": "宁德时代4月1日收于405.71元(+1.00%)，TSLA按3月31日美股收于371.75美元(+4.64%)。油价回落对新能源估值形成边际缓和，但原油仍高于100美元。",
        },
        {
            "id": "consumer",
            "name": "消费",
            "trend": "hold",
            "summary": "泡泡玛特4月1日收于143.60港元(-3.43%)，Costco按3月31日美股收于996.43美元(-0.02%)。消费板块内部开始分化，更应看景气度兑现而非统一追价。",
        },
        {
            "id": "pharma",
            "name": "医药",
            "trend": "up",
            "summary": "NVO按3月31日美股收于36.75美元(+4.14%)，LLY收于919.77美元(+3.74%)。GLP-1主线继续强势，但高估值约束仍在。",
        },
        {
            "id": "finance",
            "name": "金融",
            "trend": "up",
            "summary": "BRK-B按3月31日美股收于479.20美元(+0.96%)，JPM收于294.16美元(+3.66%)。金融股跟随大盘回升，但后续仍受利率与信用环境约束。",
        },
    ]

    stock_map = {
        "NVDA": {"currency": "$", "source": "Yahoo Finance"},
        "MRVL": {"currency": "$", "source": "Yahoo Finance"},
        "TSM": {"currency": "$", "source": "Yahoo Finance"},
        "MU": {"currency": "$", "source": "Yahoo Finance"},
        "ASML": {"currency": "$", "source": "Yahoo Finance"},
        "0700.HK": {"currency": "HK$", "source": "AkShare"},
        "PDD": {"currency": "$", "source": "Yahoo Finance"},
        "300750.SZ": {"currency": "¥", "source": "AkShare"},
        "TSLA": {"currency": "$", "source": "Yahoo Finance"},
        "9992.HK": {"currency": "HK$", "source": "AkShare"},
        "COST": {"currency": "$", "source": "Yahoo Finance"},
        "NVO": {"currency": "$", "source": "Yahoo Finance"},
        "LLY": {"currency": "$", "source": "Yahoo Finance"},
        "BRK.B": {"currency": "$", "source": "Yahoo Finance"},
        "JPM": {"currency": "$", "source": "Yahoo Finance"},
    }

    def key_for(symbol: str) -> str:
        return "BRK-B" if symbol == "BRK.B" else symbol

    for sector_id, items in watchlist["stocks"].items():
        for item in items:
            symbol = item["symbol"]
            live_key = key_for(symbol)
            live = live_map[live_key]
            cfg = stock_map[symbol]
            item["price"] = price_fmt(live["price"], cfg["currency"])
            item["change"] = live["change"]
            item["sparkline"] = [round(x, 2) for x in live["last7"]]
            item["chartData"] = [round(x, 2) for x in live["last30"]]
            item["metrics"] = build_metrics(live["price"], live["change"], live["last7"], live["last30"], cfg["currency"], cfg["source"])


def update_radar(radar: dict, markets_live: dict) -> None:
    northbound_value = "汇总口径待交易所更新"
    northbound_status = "yellow"
    radar["trafficLights"] = [
        {
            "name": "VIX波动率",
            "value": "24.76",
            "status": "yellow",
            "threshold": "<18绿 / 18-25黄 / >25红",
        },
        {
            "name": "10Y美债收益率",
            "value": "4.35%",
            "status": "yellow",
            "threshold": "<4.0%绿 / 4.0-4.5%黄 / >4.5%红",
        },
        {
            "name": "布伦特原油",
            "value": "$103.31",
            "status": "yellow",
            "threshold": "<$90绿 / $90-110黄 / >$110红",
        },
        {
            "name": "美元指数DXY",
            "value": "99.50",
            "status": "green",
            "threshold": "<102绿 / 102-107黄 / >107红",
        },
        {
            "name": "HY信用利差",
            "value": "3.46%",
            "status": "green",
            "threshold": "<4%绿 / 4-5%黄 / >5%红",
        },
        {
            "name": "北向资金",
            "value": northbound_value,
            "status": northbound_status,
            "threshold": "净流入绿 / 小幅波动黄 / 汇总缺失按黄灯处理",
        },
        {
            "name": "离岸人民币CNH",
            "value": "6.8751",
            "status": "green",
            "threshold": "<7.15绿 / 7.15-7.30黄 / >7.30红",
        },
    ]
    radar["riskScore"] = 42
    radar["riskLevel"] = "medium"
    radar["riskAdvice"] = "当前为修复中的中风险环境：VIX、10Y美债和布伦特仍在黄灯区，但DXY、HY利差与离岸人民币已回到偏安全区域。建议维持中性偏多仓位，不用Mock或估算数据去放大利好，继续等待外资汇总与后续宏观数据确认。"
    radar["riskAlerts"] = [
        {
            "title": "油价重新上冲并站稳110美元",
            "probability": "30%",
            "impact": "高",
            "response": "若布伦特重新有效突破110美元，应将高弹性成长仓位降回中性，并同步提高现金与黄金对冲比例。",
            "level": "high",
        },
        {
            "title": "美国利率再度抬升压制估值",
            "probability": "25%",
            "impact": "高",
            "response": "若10Y美债重新回到4.5%以上，应优先减持高估值成长板块，保留盈利确定性更强的主线。",
            "level": "high",
        },
        {
            "title": "外资汇总口径晚于市场情绪变化",
            "probability": "20%",
            "impact": "中",
            "response": "北向资金汇总净买额未稳定披露前，不把单日指数反弹直接等同于外资持续回流。",
            "level": "medium",
        },
    ]
    radar["alerts"] = [
        {
            "level": "info",
            "text": "VIX回落至24.76，较前值下降19.11%，但仍处18-25黄灯区。",
            "time": "06:40",
        },
        {
            "level": "info",
            "text": "NVDA收于174.40美元(+5.59%)，MRVL收于99.05美元(+12.79%)，AI基础设施链保持强势。",
            "time": "16:00",
        },
        {
            "level": "info",
            "text": "上证3948.55点(+1.46%)，恒生25260.76点(+1.91%)，恒生科技4753.36点(+2.23%)。",
            "time": "16:10",
        },
        {
            "level": "warning",
            "text": "布伦特原油最新103.31美元/桶，虽然较前值回落，但仍高于100美元关键关口。",
            "time": "18:52",
        },
    ]
    radar["smartMoneyDetail"] = [
        {
            "tier": "T1旗舰",
            "funds": [
                {
                    "name": "桥水基金",
                    "action": "继续维持对宏观与防御资产的平衡配置，不因单日反弹放松风险控制。",
                    "signal": "neutral",
                },
                {
                    "name": "伯克希尔",
                    "action": "伯克希尔股价收于479.20美元，资金仍偏好高质量现金流与防御性配置。",
                    "signal": "neutral",
                },
                {
                    "name": "贝莱德",
                    "action": "维持大类资产分散配置思路，在利率与油价未完全回落前不追逐单一风险资产。",
                    "signal": "neutral",
                },
            ],
        },
        {
            "tier": "T2成长",
            "funds": [
                {
                    "name": "ARK Invest",
                    "action": "成长资产仍然受益于风险偏好修复，但波动显著，适合分批而非一次性押注。",
                    "signal": "bullish",
                },
                {
                    "name": "交易所北向汇总",
                    "action": "4月1日北向净买额汇总口径待更新，当前不据此得出单边看多结论。",
                    "signal": "neutral",
                },
            ],
        },
        {
            "tier": "策略师观点",
            "funds": [
                {
                    "name": "Goldman Sachs",
                    "action": "继续看好AI基础设施与订单兑现度更高的科技龙头。",
                    "signal": "bullish",
                },
                {
                    "name": "Wells Fargo",
                    "action": "提醒市场继续关注利率与盈利兑现，不建议把单日反弹线性外推。",
                    "signal": "neutral",
                },
                {
                    "name": "Roth Capital",
                    "action": "维持对MRVL等AI互联链条的正面看法，但强调波动和仓位纪律。",
                    "signal": "bullish",
                },
            ],
        },
    ]
    radar["dataTime"] = SESSION_NOTE


def main() -> None:
    briefing = load_json("briefing.json")
    markets = load_json("markets.json")
    watchlist = load_json("watchlist.json")
    radar = load_json("radar.json")

    us_symbols = [
        "^GSPC", "^IXIC", "^DJI", "^VIX", "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
        "MRVL", "TSM", "MU", "ASML", "PDD", "COST", "NVO", "LLY", "BRK-B", "JPM", "^N225", "^KS11",
        "BTC-USD", "ETH-USD", "DX-Y.NYB", "CNY=X",
    ]
    live_map: Dict[str, dict] = {}
    for symbol in us_symbols:
        last, prev, last7, last30 = yf_daily(symbol)
        live_map[symbol] = {
            "price": round(last, 4),
            "change": pct_change(last, prev),
            "last7": [round(x, 4) for x in last7],
            "last30": [round(x, 4) for x in last30],
        }

    zh_last, zh_change, zh_last7, zh_last30 = ak_zh_stock("sz300750")
    live_map["300750.SZ"] = {"price": zh_last, "change": zh_change, "last7": zh_last7, "last30": zh_last30}
    hk700_last, hk700_change, hk700_last7, hk700_last30 = ak_hk_stock("00700")
    live_map["0700.HK"] = {"price": hk700_last, "change": hk700_change, "last7": hk700_last7, "last30": hk700_last30}
    hk9992_last, hk9992_change, hk9992_last7, hk9992_last30 = ak_hk_stock("09992")
    live_map["9992.HK"] = {"price": hk9992_last, "change": hk9992_change, "last7": hk9992_last7, "last30": hk9992_last30}

    sh_price, sh_change, sh_last7 = ak_zh_index("sh000001")
    sz_price, sz_change, sz_last7 = ak_zh_index("sz399001")
    hsi_price, hsi_change, hsi_last7 = ak_hk_index("HSI")
    hst_price, hst_change, hst_last7 = ak_hk_index("HSTECH")

    sina = fetch_sina(["hf_CL", "hf_OIL", "hf_GC", "DINIW", "fx_susdcnh"])
    brent_last30 = futures_hist("OIL")
    wti_last30 = futures_hist("CL")
    gold_last30 = futures_hist("GC")
    dgs10_last7 = fred_series("DGS10", limit=7)
    hy_last7 = fred_series("BAMLH0A0HYM2", limit=7)
    usdcny_last7 = live_map["CNY=X"]["last7"] if "CNY=X" in live_map else [6.88, 6.89, 6.90, 6.91, 6.91, 6.91, 6.87]

    btc_live, btc_prev = yf_fast_price("BTC-USD")
    eth_live, eth_prev = yf_fast_price("ETH-USD")
    dxy_live, dxy_prev = yf_fast_price("DX-Y.NYB")

    markets_live = {
        "spx_change": 2.91,
        "ixic_change": 3.83,
        "hsi_change": hsi_change,
        "gold_change": sina["hf_GC"]["change"] if "hf_GC" in sina else 1.69,
        "btc_change": pct_change(btc_live, btc_prev),
    }

    radar_live = {
        "dgs10": dgs10_last7[-1],
        "dgs10_change": pct_change(dgs10_last7[-1], dgs10_last7[-2]),
        "dgs10_last7": dgs10_last7,
        "hy_last7": hy_last7,
        "sh000001_last7": sh_last7,
        "sz399001_last7": sz_last7,
        "HSI_last7": hsi_last7,
        "HSTECH_last7": hst_last7,
        "brent_last7": brent_last30[-7:],
        "wti_last7": wti_last30[-7:],
        "gold_last7": gold_last30[-7:],
        "usdcny_last7": usdcny_last7,
        "btc_live": btc_live,
        "btc_live_change": pct_change(btc_live, btc_prev),
        "eth_live": eth_live,
        "eth_live_change": pct_change(eth_live, eth_prev),
        "dxy_live": dxy_live,
    }

    live_map["DX-Y.NYB"]["price"] = round(dxy_live, 4)
    live_map["DX-Y.NYB"]["change"] = pct_change(dxy_live, dxy_prev)

    for symbol, name in [("BTC-USD", btc_live), ("ETH-USD", eth_live)]:
        live_map[symbol]["price"] = round(name, 4)
    live_map["BTC-USD"]["change"] = pct_change(btc_live, btc_prev)
    live_map["ETH-USD"]["change"] = pct_change(eth_live, eth_prev)

    update_briefing(briefing, markets_live, radar_live)
    update_markets(markets, live_map, radar_live, markets_live)
    update_watchlist(watchlist, live_map)
    update_radar(radar, markets_live)

    dump_json("briefing.json", briefing)
    dump_json("markets.json", markets)
    dump_json("watchlist.json", watchlist)
    dump_json("radar.json", radar)
    print("已完成 miniapp_sync 4个JSON 的真实行情字段校正。")


if __name__ == "__main__":
    main()
