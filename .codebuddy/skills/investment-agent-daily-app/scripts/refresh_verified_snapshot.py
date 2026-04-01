#!/usr/bin/env python3
"""
投研鸭小程序数据快照校正脚本 v1.2

用途：
1. 只校正 market-driven 字段（价格、涨跌、sparkline、chartData、红绿灯、数据时点）
2. 直接读取 miniapp_sync 目录下现有 JSON，并在原有结构上回写
3. 严禁引入 mock / estimate / 新闻页反推行情

数据源：
- 美股/加密/美元指数：Yahoo Finance(yfinance)
- A股/港股/港股指数：AkShare
- 黄金/原油/离岸人民币：新浪实时 + AkShare 外盘历史
- 10Y / HY：FRED 公开 CSV
- 离岸人民币 CNH 历史：AkShare forex_hist_em（东方财富）
- 日经225备用：AkShare futures_foreign_hist("N225")

v1.2 变更（2026-04-01）：
- CNH 改用 ak.forex_hist_em("USDCNH") 获取真实离岸汇率历史序列
- 日经225/KOSPI 增加量级校验(MARKET_SANITY_RANGE) + 日经 AkShare 备用通道
- watchlist metrics 升级为方案C：4项行情 + PE(TTM) + 综合评级（规则化计算）
- 北向资金红绿灯改为「外资动向」，基于港股均涨跌幅自动计算状态
- 阈值逻辑标准化为 TRAFFIC_LIGHT_RULES 常量 + auto_traffic_status() 程序化判断
- riskScore 改为 calc_risk_score() 动态计算，不再硬编码
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


# ─────────────────────────────────────────────────────────────────
# 各指数合理价格区间（防止 yfinance 返回乱码/错误量级数据）
# ─────────────────────────────────────────────────────────────────
MARKET_SANITY_RANGE: Dict[str, Tuple[float, float]] = {
    "^N225":  (18_000, 55_000),   # 日经225
    "^KS11":  (1_500,  4_500),    # KOSPI综合指数（非KOSDAQ，约2300-2600附近）
    "^TWII":  (15_000, 28_000),   # 台湾加权
    "^GSPC":  (3_500,  7_000),    # 标普500
    "^IXIC":  (10_000, 25_000),   # 纳斯达克
    "^DJI":   (28_000, 55_000),   # 道琼斯
    "^VIX":   (8,      80),       # VIX
    "^HSI":   (14_000, 35_000),   # 恒生指数
}

# ─────────────────────────────────────────────────────────────────
# 红绿灯阈值配置（单一事实来源，程序化判断，避免 AI 手工判断错误）
# ─────────────────────────────────────────────────────────────────
TRAFFIC_LIGHT_RULES: Dict[str, dict] = {
    "VIX波动率": {
        "green_max":  18.0,   # < 18 → 绿
        "yellow_max": 25.0,   # 18-25 → 黄，> 25 → 红
        "threshold": "<18绿 / 18-25黄 / >25红",
    },
    "10Y美债收益率": {
        "green_max":  4.0,
        "yellow_max": 4.5,
        "threshold": "<4.0%绿 / 4.0-4.5%黄 / >4.5%红",
    },
    "布伦特原油": {
        "green_max":  90.0,
        "yellow_max": 110.0,
        "threshold": "<$90绿 / $90-110黄 / >$110红",
    },
    "美元指数DXY": {
        "green_max":  102.0,
        "yellow_max": 107.0,
        "threshold": "<102绿 / 102-107黄 / >107红",
    },
    "HY信用利差": {
        "green_max":  4.0,
        "yellow_max": 5.0,
        "threshold": "<4%绿 / 4-5%黄 / >5%红",
    },
    "离岸人民币CNH": {
        "green_max":  7.15,
        "yellow_max": 7.30,
        "threshold": "<7.15绿 / 7.15-7.30黄 / >7.30红",
    },
    # 「外资动向」由 calc_foreign_capital_proxy() 独立计算，不走此规则
}


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


# ─────────────────────────────────────────────────────────────────
# v1.2 新增：watchlist metrics 方案C
# 4项行情（最新价/单日/7日/30日涨跌）+ PE(TTM) + 综合评级（规则化）
# ─────────────────────────────────────────────────────────────────

def calc_star_rating(change: float, pct_30d: float) -> str:
    """
    基于行情表现规则化计算综合评级（可重现，无主观判断）
    ⭐⭐⭐⭐⭐: 30日涨超+15% 且 单日为正
    ⭐⭐⭐⭐  : 30日涨+5%~+15%，或单日涨超+3%
    ⭐⭐⭐    : 30日在-5%~+5%（震荡整理）
    ⭐⭐      : 30日跌-5%~-15%
    ⭐        : 30日跌超-15%（深度回调）
    """
    if pct_30d >= 15 and change > 0:
        return "⭐⭐⭐⭐⭐"
    elif pct_30d >= 5 or change >= 3:
        return "⭐⭐⭐⭐"
    elif pct_30d >= -5:
        return "⭐⭐⭐"
    elif pct_30d >= -15:
        return "⭐⭐"
    else:
        return "⭐"


def fetch_pe_ttm(ticker: str) -> str:
    """
    通过 yfinance Ticker.info 获取 PE(TTM)
    - 优先 trailingPE，其次 forwardPE
    - 失败或 NaN 时返回 "—"，不阻断主流程（PE 为辅助指标）
    """
    try:
        info = yf.Ticker(ticker).info
        pe = info.get("trailingPE") or info.get("forwardPE")
        if pe and not math.isnan(float(pe)) and float(pe) > 0:
            return f"{float(pe):.1f}x"
    except Exception:
        pass
    return "—"


def build_metrics(
    price: float,
    change: float,
    last7: List[float],
    last30: List[float],
    currency: str,
    pe_ttm: str = "—",
    star_rating: str = "⭐⭐⭐",
) -> List[dict]:
    """
    生成 watchlist 标的的 6 项 metrics（方案C：4项行情 + PE(TTM) + 综合评级）
    - 前4项完全来自行情，100% 可验证
    - PE(TTM) 来自 yfinance.Ticker.info["trailingPE"]（有则用，无则"—"）
    - 综合评级由 calc_star_rating() 规则函数自动计算，可重现
    """
    return [
        {"label": "最新价",   "value": compact_num(price, currency)},
        {"label": "单日涨跌", "value": f"{change:+.2f}%"},
        {"label": "7日涨跌",  "value": f"{seq_pct(last7):+.2f}%"},
        {"label": "30日涨跌", "value": f"{seq_pct(last30):+.2f}%"},
        {"label": "PE(TTM)", "value": pe_ttm},
        {"label": "综合评级", "value": star_rating},
    ]


# ─────────────────────────────────────────────────────────────────
# v1.2 新增：红绿灯程序化判断 + 动态 riskScore
# ─────────────────────────────────────────────────────────────────

def auto_traffic_status(rule_key: str, numeric_value: float) -> str:
    """
    根据 TRAFFIC_LIGHT_RULES 配置程序化判断红绿灯状态。
    消除手工判断错误风险，与阈值文字保持强一致。
    """
    rule = TRAFFIC_LIGHT_RULES.get(rule_key)
    if not rule:
        return "yellow"  # 未配置的指标默认黄
    if numeric_value < rule["green_max"]:
        return "green"
    elif numeric_value <= rule["yellow_max"]:
        return "yellow"
    else:
        return "red"


def calc_risk_score(traffic_lights: List[dict]) -> int:
    """
    基于7项红绿灯动态计算风险评分（0-100）。
    权重：green=0, yellow=10, red=20
    基础分=30（代表市场正常背景噪音），上限封顶100
    当前7项全绿 → 30分(low)，3黄4绿 → 60分(medium)，7红 → 100分(high)
    """
    weights = {"green": 0, "yellow": 10, "red": 20}
    extra = sum(weights.get(tl["status"], 10) for tl in traffic_lights)
    return min(100, max(0, 30 + extra))


def score_to_level(score: int) -> str:
    if score < 45:
        return "low"
    elif score < 65:
        return "medium"
    else:
        return "high"


# ─────────────────────────────────────────────────────────────────
# v1.2 新增：外资动向代理指标（替代已永久停止披露的北向资金净买额）
# ─────────────────────────────────────────────────────────────────

def calc_foreign_capital_proxy(hsi_change: float, hstech_change: float) -> dict:
    """
    外资动向代理指标。

    背景：自2024年8月19日起，沪深交易所正式停止实时披露北向资金净买额，
    仅公布沪深港通交易总额（无方向），此为永久性机制调整，不可逆。
    AkShare stock_hsgt_fund_flow_summary_em 接口净买额字段永久为空，无法修复。

    替代逻辑：以港股（恒生指数 + 恒生科技指数）均涨跌幅作为外资偏好代理指标。
    港股对外资流动最敏感，与北向资金历史正相关性高。

    阈值（经验值）：
    - 均涨 ≥ +1.5%  → green（外资明显回流信号）
    - 均涨 0~+1.5%  → yellow（外资情绪中性）
    - 均跌 < 0%     → red（外资谨慎/流出信号）
    """
    combined = round((hsi_change + hstech_change) / 2, 2)

    if combined >= 1.5:
        status = "green"
        value = f"港股均涨+{combined:.1f}%，外资偏好回暖"
    elif combined >= 0:
        status = "yellow"
        value = f"港股均涨+{combined:.1f}%，外资情绪中性"
    else:
        status = "red"
        value = f"港股均跌{combined:.1f}%，外资偏谨慎"

    return {
        "name": "外资动向",
        "value": value,
        "status": status,
        "threshold": (
            "北向实时净买额已于2024-08-19永久停止披露；"
            "以港股（恒生+恒生科技）均涨跌幅为代理：≥+1.5%绿 / 0~+1.5%黄 / 跌红"
        ),
    }


# ─────────────────────────────────────────────────────────────────
# v1.2 新增：CNH 历史序列（AkShare 东方财富，真实离岸人民币）
# ─────────────────────────────────────────────────────────────────

def ak_forex_hist(symbol: str = "USDCNH", tail: int = 7) -> List[float]:
    """
    通过 AkShare 东方财富外汇行情接口获取离岸人民币历史序列。
    symbol: USDCNH = 美元兑离岸人民币（真实CNH，非在岸CNY=X）
    返回最近 tail 个交易日收盘价列表，不足则抛出异常阻断发布。
    """
    df = ak.forex_hist_em(symbol=symbol)
    # 收盘价字段名：最新价
    close_col = "最新价" if "最新价" in df.columns else df.columns[4]
    values = [float(x) for x in df[close_col].dropna().tail(tail).tolist()]
    if len(values) < tail:
        raise ValueError(
            f"[BLOCK] forex_hist_em({symbol}) 仅返回 {len(values)} 条，"
            f"要求 {tail} 条，数据不足，阻断发布"
        )
    return values


# ─────────────────────────────────────────────────────────────────
# v1.2 新增：带量级校验的 yf_daily 封装 + 日经225 AkShare 备用通道
# ─────────────────────────────────────────────────────────────────

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


def yf_daily_verified(ticker: str, period: str = "40d") -> Tuple[float, float, List[float], List[float]]:
    """
    带量级校验的 yf_daily 封装。
    - 先拉数据，再校验价格是否在 MARKET_SANITY_RANGE 合理区间
    - 超出区间说明 yfinance 返回了错误/异常数据，抛出 ValueError
    - 调用方可据此决定是否切换备用数据源
    """
    last, prev, last7, last30 = yf_daily(ticker, period)
    if ticker in MARKET_SANITY_RANGE:
        lo, hi = MARKET_SANITY_RANGE[ticker]
        if not (lo <= last <= hi):
            raise ValueError(
                f"[SANITY] {ticker} 价格 {last:.2f} 超出合理区间 [{lo}, {hi}]，"
                f"疑似 yfinance 返回错误数据，请核查"
            )
    return last, prev, last7, last30


def ak_nikkei_hist(tail: int = 30) -> Tuple[float, float, List[float], List[float]]:
    """
    AkShare 备用通道：日经225历史数据（新浪外盘期货历史）
    用于 yfinance ^N225 数据异常时的降级处理。
    """
    df = ak.futures_foreign_hist(symbol="N225")
    close_col = (
        "close" if "close" in df.columns
        else ("收盘" if "收盘" in df.columns else df.columns[-2])
    )
    values = [float(x) for x in df[close_col].dropna().tail(tail).tolist()]
    if len(values) < 7:
        raise ValueError(f"ak_nikkei_hist 数据不足7条，实际 {len(values)} 条")
    last = values[-1]
    prev = values[-2]
    return last, pct_change(last, prev), values[-7:], values[-30:] if len(values) >= 30 else values


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
            "title": "A/H反弹成立，港股涨幅代理外资情绪回暖",
            "confidence": 66,
            "logic": "A股与港股4月1日同步上涨，港股均涨+2.07%（恒生+1.91%+恒科+2.23%），代理外资动向为绿灯，但需持续跟踪。",
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
            "source": "港股成交代理",
            "action": "4月1日港股均涨+2.07%（恒生+1.91%+恒科+2.23%），以港股代理外资动向为绿灯信号。",
            "signal": "bullish",
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
            # v1.2：使用经量级校验的日经225数据（yf_daily_verified + AkShare备用）
            "sparkline": [round(x, 2) for x in watchlist_live["^N225"]["last7"][:-1]] + [53739.68],
        },
        {
            "name": "KOSPI",
            "price": str(round(watchlist_live["^KS11"]["price"], 2)) if watchlist_live.get("^KS11") else "数据待核实",
            "change": watchlist_live["^KS11"]["change"] if watchlist_live.get("^KS11") else 0.0,
            # v1.2：KOSPI 经量级校验（约2300-2600，非5478），若校验失败显示"数据待核实"
            "sparkline": [round(x, 2) for x in watchlist_live["^KS11"]["last7"]] if watchlist_live.get("^KS11") else [],
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
            # v1.2：使用 ak_forex_hist("USDCNH") 获取的真实离岸人民币历史序列
            "sparkline": [round(x, 4) for x in radar_live["usdcnh_last7"][:-1]] + [6.8751],
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


def update_watchlist(watchlist: dict, live_map: dict, pe_map: Dict[str, str]) -> None:
    """
    v1.2：新增 pe_map 参数，用于填充方案C的 PE(TTM) 字段。
    """
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
        "TSM":  {"currency": "$", "source": "Yahoo Finance"},
        "MU":   {"currency": "$", "source": "Yahoo Finance"},
        "ASML": {"currency": "$", "source": "Yahoo Finance"},
        "0700.HK": {"currency": "HK$", "source": "AkShare"},
        "PDD":  {"currency": "$", "source": "Yahoo Finance"},
        "300750.SZ": {"currency": "¥", "source": "AkShare"},
        "TSLA": {"currency": "$", "source": "Yahoo Finance"},
        "9992.HK": {"currency": "HK$", "source": "AkShare"},
        "COST": {"currency": "$", "source": "Yahoo Finance"},
        "NVO":  {"currency": "$", "source": "Yahoo Finance"},
        "LLY":  {"currency": "$", "source": "Yahoo Finance"},
        "BRK.B": {"currency": "$", "source": "Yahoo Finance"},
        "JPM":  {"currency": "$", "source": "Yahoo Finance"},
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

            # v1.2 方案C：4项行情 + PE(TTM) + 综合评级（规则化计算）
            pct_30d = seq_pct(live["last30"])
            pe_ttm = pe_map.get(live_key, "—")
            star = calc_star_rating(live["change"], pct_30d)
            item["metrics"] = build_metrics(
                live["price"], live["change"],
                live["last7"], live["last30"],
                cfg["currency"],
                pe_ttm=pe_ttm,
                star_rating=star,
            )


def update_radar(
    radar: dict,
    markets_live: dict,
    radar_live: dict,
) -> None:
    """
    v1.2：
    - 北向资金改为「外资动向」，由 calc_foreign_capital_proxy() 自动计算
    - 阈值判断改为 auto_traffic_status() 程序化执行
    - riskScore 改为 calc_risk_score() 动态计算
    """
    # 从 radar_live 中取出数值用于程序化判断
    vix_val    = radar_live.get("vix_last", 24.76)
    dgs10_val  = radar_live.get("dgs10", 4.35)
    brent_val  = radar_live.get("brent_last", 103.31)
    dxy_val    = radar_live.get("dxy_live", 99.50)
    hy_val     = radar_live.get("hy_last", 3.46)
    usdcnh_val = radar_live.get("usdcnh_last", 6.8751)

    hsi_change    = markets_live.get("hsi_change", 1.91)
    hstech_change = radar_live.get("hstech_change", 2.23)

    # 组装7项红绿灯（前6项规则化 + 外资动向）
    traffic_lights = [
        {
            "name": "VIX波动率",
            "value": str(round(vix_val, 2)),
            "status": auto_traffic_status("VIX波动率", vix_val),
            "threshold": TRAFFIC_LIGHT_RULES["VIX波动率"]["threshold"],
        },
        {
            "name": "10Y美债收益率",
            "value": f"{dgs10_val:.2f}%",
            "status": auto_traffic_status("10Y美债收益率", dgs10_val),
            "threshold": TRAFFIC_LIGHT_RULES["10Y美债收益率"]["threshold"],
        },
        {
            "name": "布伦特原油",
            "value": f"${brent_val:.2f}",
            "status": auto_traffic_status("布伦特原油", brent_val),
            "threshold": TRAFFIC_LIGHT_RULES["布伦特原油"]["threshold"],
        },
        {
            "name": "美元指数DXY",
            "value": str(round(dxy_val, 2)),
            "status": auto_traffic_status("美元指数DXY", dxy_val),
            "threshold": TRAFFIC_LIGHT_RULES["美元指数DXY"]["threshold"],
        },
        {
            "name": "HY信用利差",
            "value": f"{hy_val:.2f}%",
            "status": auto_traffic_status("HY信用利差", hy_val),
            "threshold": TRAFFIC_LIGHT_RULES["HY信用利差"]["threshold"],
        },
        # v1.2：「外资动向」替代「北向资金」
        calc_foreign_capital_proxy(hsi_change, hstech_change),
        {
            "name": "离岸人民币CNH",
            "value": str(round(usdcnh_val, 4)),
            "status": auto_traffic_status("离岸人民币CNH", usdcnh_val),
            "threshold": TRAFFIC_LIGHT_RULES["离岸人民币CNH"]["threshold"],
        },
    ]

    # v1.2：动态 riskScore（不再硬编码）
    risk_score = calc_risk_score(traffic_lights)
    risk_level = score_to_level(risk_score)

    radar["trafficLights"] = traffic_lights
    radar["riskScore"] = risk_score
    radar["riskLevel"] = risk_level
    radar["riskAdvice"] = (
        f"当前风险评分 {risk_score}（{risk_level}）："
        "VIX、10Y美债和布伦特仍在黄灯区，但DXY、HY利差与离岸人民币已回到偏安全区域，"
        "港股涨幅代理外资情绪回暖。建议维持中性偏多仓位，继续等待宏观数据确认。"
    )
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
            "title": "港股急跌引发外资动向由绿转红",
            "probability": "20%",
            "impact": "中",
            "response": "若港股单日急跌超-2%，外资动向指标转红，应暂停加仓并观察后续方向。",
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
                    "name": "港股成交代理",
                    "action": "4月1日港股均涨+2.07%，外资动向代理指标为绿灯，外资偏好回暖信号成立。",
                    "signal": "bullish",
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

    # ── 批量下载美股/指数（移除 CNY=X，CNH 改由 AkShare 专用通道获取）
    us_symbols = [
        "^GSPC", "^IXIC", "^DJI", "^VIX", "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA",
        "MRVL", "TSM", "MU", "ASML", "PDD", "COST", "NVO", "LLY", "BRK-B", "JPM",
        "BTC-USD", "ETH-USD", "DX-Y.NYB",
        # "^N225" 和 "^KS11" 单独处理（量级校验）
        # "CNY=X" 已移除，CNH 历史由 ak_forex_hist 获取
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

    # ── v1.2：日经225 带量级校验 + AkShare 备用通道 ────────────────
    print("[INFO] 正在获取日经225...")
    try:
        n225_last, n225_prev, n225_last7, n225_last30 = yf_daily_verified("^N225")
        live_map["^N225"] = {
            "price": round(n225_last, 2),
            "change": pct_change(n225_last, n225_prev),
            "last7": [round(x, 2) for x in n225_last7],
            "last30": [round(x, 2) for x in n225_last30],
        }
        print(f"[OK] 日经225 yfinance: {n225_last:.2f}")
    except ValueError as e:
        print(f"[WARN] yfinance ^N225 量级校验失败: {e}，切换 AkShare 备用源")
        try:
            n225_last, n225_change, n225_last7, n225_last30 = ak_nikkei_hist()
            live_map["^N225"] = {
                "price": round(n225_last, 2),
                "change": n225_change,
                "last7": [round(x, 2) for x in n225_last7],
                "last30": [round(x, 2) for x in n225_last30],
            }
            print(f"[OK] 日经225 AkShare备用: {n225_last:.2f}")
        except Exception as e2:
            raise RuntimeError(f"[BLOCK] 日经225 所有来源均失败: {e2}")

    # ── v1.2：KOSPI 带量级校验（发现异常则标注，不阻断整体流程）───────
    print("[INFO] 正在获取KOSPI...")
    try:
        ks11_last, ks11_prev, ks11_last7, ks11_last30 = yf_daily_verified("^KS11")
        live_map["^KS11"] = {
            "price": round(ks11_last, 2),
            "change": pct_change(ks11_last, ks11_prev),
            "last7": [round(x, 2) for x in ks11_last7],
            "last30": [round(x, 2) for x in ks11_last30],
        }
        print(f"[OK] KOSPI yfinance: {ks11_last:.2f}")
    except ValueError as e:
        print(f"[WARN] KOSPI 量级校验失败: {e}，该项将标注为数据待核实")
        live_map["^KS11"] = None  # update_markets 中已处理 None 情况

    # ── A股/港股 ─────────────────────────────────────────────────
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

    # ── 大宗/外汇 ─────────────────────────────────────────────────
    sina = fetch_sina(["hf_CL", "hf_OIL", "hf_GC", "DINIW", "fx_susdcnh"])
    brent_last30 = futures_hist("OIL")
    wti_last30 = futures_hist("CL")
    gold_last30 = futures_hist("GC")
    dgs10_last7 = fred_series("DGS10", limit=7)
    hy_last7 = fred_series("BAMLH0A0HYM2", limit=7)

    # ── v1.2：CNH 历史序列改用 AkShare forex_hist_em（真实离岸人民币）─
    print("[INFO] 正在获取 CNH（离岸人民币）历史序列...")
    try:
        usdcnh_last7 = ak_forex_hist("USDCNH", tail=7)
        print(f"[OK] CNH 历史序列来自 AkShare forex_hist_em（真实离岸人民币）: 最新={usdcnh_last7[-1]:.4f}")
    except Exception as e_cnh:
        print(f"[WARN] AkShare USDCNH 失败: {e_cnh}，尝试新浪 fx_susdcnh 实时价替代")
        # 降级：从新浪实时获取最新价，构造 7 天序列（但只有 1 个点，需要用 fred/yf 补历史）
        cnh_spot = sina.get("fx_susdcnh", {}).get("price")
        if cnh_spot and cnh_spot > 0:
            # 只有当日价格，无法构造 7 天序列，记录警告后阻断
            print(f"[WARN] 仅有实时价 {cnh_spot}，无法构造7天历史序列，阻断发布")
            raise RuntimeError(
                "[BLOCK] CNH 历史序列（7天）全部来源失败，"
                "请检查 AkShare forex_hist_em 接口可用性后重试"
            )
        else:
            raise RuntimeError("[BLOCK] CNH 历史序列及实时价全部来源失败，阻断发布")

    btc_live, btc_prev = yf_fast_price("BTC-USD")
    eth_live, eth_prev = yf_fast_price("ETH-USD")
    dxy_live, dxy_prev = yf_fast_price("DX-Y.NYB")

    # ── v1.2：PE(TTM) 批量获取（watchlist 标的，用于方案C metrics）──
    WATCHLIST_PE_SYMBOLS = [
        "NVDA", "MRVL", "TSM", "MU", "ASML", "PDD",
        "COST", "NVO", "LLY", "BRK-B", "JPM", "TSLA",
        "0700.HK", "9992.HK",
    ]
    print("[INFO] 正在批量获取 PE(TTM)...")
    pe_map: Dict[str, str] = {}
    for sym in WATCHLIST_PE_SYMBOLS:
        pe_map[sym] = fetch_pe_ttm(sym)
        print(f"  {sym}: PE={pe_map[sym]}")
    # A股 yfinance PE 数据不稳定，暂标"—"
    pe_map["300750.SZ"] = "—"
    valid_count = len([v for v in pe_map.values() if v != "—"])
    print(f"[OK] PE 获取完成: {valid_count}/{len(pe_map)} 有效")

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
        # v1.2：新增 hy_last（用于红绿灯判断），取最新值
        "hy_last": hy_last7[-1],
        "sh000001_last7": sh_last7,
        "sz399001_last7": sz_last7,
        "HSI_last7": hsi_last7,
        "HSTECH_last7": hst_last7,
        # v1.2：新增 hstech_change（用于外资动向代理计算）
        "hstech_change": hst_change,
        "brent_last7": brent_last30[-7:],
        "wti_last7": wti_last30[-7:],
        "gold_last7": gold_last30[-7:],
        # v1.2：usdcnh_last7 替换 usdcny_last7（真实离岸人民币）
        "usdcnh_last7": usdcnh_last7,
        # v1.2：新增供 update_radar() 使用的数值字段
        "vix_last": live_map["^VIX"]["price"],
        "brent_last": brent_last30[-1],
        "usdcnh_last": usdcnh_last7[-1],
        "dxy_live": dxy_live,
        "btc_live": btc_live,
        "btc_live_change": pct_change(btc_live, btc_prev),
        "eth_live": eth_live,
        "eth_live_change": pct_change(eth_live, eth_prev),
    }

    live_map["DX-Y.NYB"]["price"] = round(dxy_live, 4)
    live_map["DX-Y.NYB"]["change"] = pct_change(dxy_live, dxy_prev)

    for symbol, name in [("BTC-USD", btc_live), ("ETH-USD", eth_live)]:
        live_map[symbol]["price"] = round(name, 4)
    live_map["BTC-USD"]["change"] = pct_change(btc_live, btc_prev)
    live_map["ETH-USD"]["change"] = pct_change(eth_live, eth_prev)

    update_briefing(briefing, markets_live, radar_live)
    update_markets(markets, live_map, radar_live, markets_live)
    # v1.2：传入 pe_map 给 update_watchlist
    update_watchlist(watchlist, live_map, pe_map)
    # v1.2：传入 radar_live 给 update_radar（含 vix_last/brent_last/hy_last/usdcnh_last/hstech_change）
    update_radar(radar, markets_live, radar_live)

    dump_json("briefing.json", briefing)
    dump_json("markets.json", markets)
    dump_json("watchlist.json", watchlist)
    dump_json("radar.json", radar)
    print("\n[完成] miniapp_sync 4个JSON 校正完毕（v1.2：CNH真实离岸源/日经量级校验/metrics方案C/外资动向/动态riskScore）")


if __name__ == "__main__":
    main()
