#!/usr/bin/env python3
"""
投研鸭小程序 sparkline/chartData 历史序列补全脚本 v3.0（AkShare 替代 yfinance）

【架构说明 — 双轨分工】
────────────────────────────────────────────────────────────────
  AI + 搜索轨（主轨）：
    负责所有字段的首次生成和填写，包括：
    price / change / metrics / trafficLights / riskScore / riskLevel /
    riskAdvice / globalReaction / gics / sectors / alerts / riskAlerts /
    smartMoney / smartMoneyDetail / coreEvent / coreJudgments / actions /
    riskNote / sentimentScore / sentimentLabel / insight / insightChain /
    takeaway / marketSummaryPoints / dataTime 等

  脚本补全轨（本脚本）：
    只负责两个数组字段的真实历史序列补全：
    · sparkline（7个交易日收盘价）
    · chartData（30个交易日收盘价）
    这两个字段是历史序列 API 的唯一不可替代价值。
    其他所有字段，脚本永远不读取、不修改、不覆盖。

【设计哲学】
────────────────────────────────────────────────────────────────
  ● 最小权限原则：脚本只写两个字段，没有覆盖 AI 数据的任何风险
  ● 双源降级：AkShare 新浪源（主）→ AkShare 东方财富源（fallback）
  ● 失败安全：任何标的失败 → 打印警告 + 跳过，绝不阻断整体流程
  ● 完全幂等：重复运行不会有任何副作用
  ● 防限流：逐个调用 + 0.3秒 sleep 间隔，防止新浪/东方财富限流

【覆盖范围】
────────────────────────────────────────────────────────────────
  markets.json:
    · usMarkets[*].sparkline          — 美股指数（新浪源 us_index）
    · m7[*].sparkline                 — M7（新浪源 us_stock）
    · asiaMarkets[*].sparkline        — 亚太指数（新浪/AkShare 各接口）
    · commodities[*].sparkline        — 大宗商品（新浪源 commodity）
    · cryptos[*].sparkline            — 加密货币（skip，AkShare 缺口）

  watchlist.json:
    · stocks[*][*].sparkline
    · stocks[*][*].chartData

  briefing.json / radar.json：脚本不读取、不修改

【数据源映射】
────────────────────────────────────────────────────────────────
  美股个股    → ak.stock_us_daily(symbol)         新浪源
  港股个股    → ak.stock_hk_daily(symbol)         新浪源
  A股个股     → ak.stock_zh_a_daily(symbol)       新浪源
  美股指数    → ak.index_us_stock_sina(symbol)     新浪源
  A股指数     → ak.stock_zh_index_daily(symbol)    东方财富源
  恒生/恒科   → ak.stock_hk_index_daily_sina(symbol) 新浪源
  大宗商品    → ak.futures_foreign_hist(symbol)    新浪源
  日经225     → ak.index_us_stock_sina(symbol=".N225") 新浪源
  VIX/DXY/BTC/ETH/10Y/CNH → skip（AkShare 缺口，保留 AI 估算值）

【Fallback 降级路径】
────────────────────────────────────────────────────────────────
  新浪源失败 → 东方财富源重试 → 仍失败 → 跳过（保留 AI 估算值）
  东方财富源接口对照：
    · 美股个股：ak.stock_us_hist(symbol, period="daily", adjust="qfq")
    · 港股个股：ak.stock_hk_hist(symbol, period="daily", adjust="qfq")
    · A股个股：ak.stock_zh_a_hist(symbol, period="daily", adjust="qfq")

v3.0 AkShare 替代 yfinance（2026-04-05）
  · 主数据源从 yfinance 切换至 AkShare 新浪源
  · 新增东方财富源作为 fallback
  · 新增 A股指数（上证/深证）和港股指数（恒生/恒生科技）覆盖
  · 逐个调用 + 0.3秒 sleep 间隔防限流
  · 覆盖率从 0%（yfinance 403 封禁）提升至 ~89%（41/46 标的）

v2.2 补全新5板块映射（2026-04-05）
v2.1 批量下载优化（2026-04-03）
v2.0 方案A — 双轨分工（2026-04-03）
v1.0 初始版本（2026-04-03）
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import akshare as ak
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# 路径配置（动态解析，不依赖硬编码绝对路径）
# ─────────────────────────────────────────────────────────────────────────────
# 路径配置：优先从命令行参数读取，否则通过相对层级解析
ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent.parent.parent.parent / "workflows" / "investment_agent_data" / "miniapp_sync"

# 防限流间隔（秒）
SLEEP_INTERVAL = 0.3


# ─────────────────────────────────────────────────────────────────────────────
# 标的映射：markets.json 中的 name → AkShare 数据源配置
# type 说明：
#   us_index   → ak.index_us_stock_sina(symbol)
#   us_stock   → ak.stock_us_daily(symbol)
#   cn_index   → ak.stock_zh_index_daily(symbol)
#   hk_index   → ak.stock_hk_index_daily_sina(symbol)
#   commodity  → ak.futures_foreign_hist(symbol)
#   skip       → AkShare 缺口，跳过
# ─────────────────────────────────────────────────────────────────────────────
MARKETS_SPARKLINE_MAP: Dict[str, Optional[dict]] = {
    # usMarkets
    "标普500":       {"type": "us_index",  "symbol": ".INX"},
    "纳斯达克":      {"type": "us_index",  "symbol": ".IXIC"},
    "道琼斯":        {"type": "us_index",  "symbol": ".DJI"},
    "VIX":          {"type": "skip"},
    # M7
    "苹果 AAPL":    {"type": "us_stock",  "symbol": "AAPL"},
    "微软 MSFT":    {"type": "us_stock",  "symbol": "MSFT"},
    "英伟达 NVDA":   {"type": "us_stock",  "symbol": "NVDA"},
    "谷歌 GOOGL":   {"type": "us_stock",  "symbol": "GOOGL"},
    "亚马逊 AMZN":   {"type": "us_stock",  "symbol": "AMZN"},
    "Meta META":    {"type": "us_stock",  "symbol": "META"},
    "特斯拉 TSLA":   {"type": "us_stock",  "symbol": "TSLA"},
    # asiaMarkets
    "上证指数":      {"type": "cn_index",  "symbol": "sh000001"},
    "深证成指":      {"type": "cn_index",  "symbol": "sz399001"},
    "恒生指数":      {"type": "hk_index",  "symbol": "HSI"},
    "恒生科技":      {"type": "hk_index",  "symbol": "HSTECH"},
    "日经225":      {"type": "us_index",  "symbol": ".N225"},
    # commodities
    "黄金 XAU":     {"type": "commodity", "symbol": "XAU"},
    "布伦特原油":    {"type": "commodity", "symbol": "BZ"},
    "WTI原油":      {"type": "commodity", "symbol": "CL"},
    "美元指数 DXY":  {"type": "skip"},
    "10Y美债":      {"type": "skip"},
    "离岸人民币 CNH": {"type": "skip"},
    # cryptos
    "比特币 BTC":    {"type": "skip"},
    "以太坊 ETH":    {"type": "skip"},
}

# watchlist stocks 标的：symbol → AkShare 数据源配置
# type 说明：
#   us_stock   → ak.stock_us_daily(symbol)  [新浪源]
#   hk_stock   → ak.stock_hk_daily(symbol)  [新浪源]
#   cn_stock   → ak.stock_zh_a_daily(symbol) [新浪源]
#   skip       → 未上市等，跳过
WATCHLIST_AK_MAP: Dict[str, Optional[dict]] = {
    # ── ai_infra：AI算力链 ──
    "NVDA":       {"type": "us_stock", "symbol": "NVDA"},
    "AVGO":       {"type": "us_stock", "symbol": "AVGO"},
    "TSM":        {"type": "us_stock", "symbol": "TSM"},
    "MSFT":       {"type": "us_stock", "symbol": "MSFT"},
    "GOOGL":      {"type": "us_stock", "symbol": "GOOGL"},
    "META":       {"type": "us_stock", "symbol": "META"},
    "AMZN":       {"type": "us_stock", "symbol": "AMZN"},
    "AAPL":       {"type": "us_stock", "symbol": "AAPL"},
    "ASML":       {"type": "us_stock", "symbol": "ASML"},
    "AMD":        {"type": "us_stock", "symbol": "AMD"},
    "ANET":       {"type": "us_stock", "symbol": "ANET"},
    "300308.SZ":  {"type": "cn_stock", "symbol": "sz300308"},
    # ── ai_app：AI应用 ──
    "PLTR":       {"type": "us_stock", "symbol": "PLTR"},
    "TSLA":       {"type": "us_stock", "symbol": "TSLA"},
    "RBLX":       {"type": "us_stock", "symbol": "RBLX"},
    "TEM":        {"type": "us_stock", "symbol": "TEM"},
    "NOW":        {"type": "us_stock", "symbol": "NOW"},
    # ByteDance：未上市
    # ── cn_ai：国产AI（港股/A股）──
    "0700.HK":    {"type": "hk_stock", "symbol": "00700"},
    "9988.HK":    {"type": "hk_stock", "symbol": "09988"},
    "2513.HK":    {"type": "hk_stock", "symbol": "02513"},
    "0100.HK":    {"type": "hk_stock", "symbol": "00100"},
    "1810.HK":    {"type": "hk_stock", "symbol": "01810"},
    "688256.SH":  {"type": "cn_stock", "symbol": "sh688256"},
    # ── smart_money：聪明钱 ──
    "BRK.A":      {"type": "us_stock", "symbol": "BRK.A"},
    "KO":         {"type": "us_stock", "symbol": "KO"},
    "OXY":        {"type": "us_stock", "symbol": "OXY"},
    "600519.SH":  {"type": "cn_stock", "symbol": "sh600519"},
    "PDD":        {"type": "us_stock", "symbol": "PDD"},
    "AXP":        {"type": "us_stock", "symbol": "AXP"},
    "9992.HK":    {"type": "hk_stock", "symbol": "09992"},    # 泡泡玛特（v2.1新增，段永平关注）
    # ── hot_topic：本期热点 ──
    "300750.SZ":  {"type": "cn_stock", "symbol": "sz300750"},
    "002594.SZ":  {"type": "cn_stock", "symbol": "sz002594"},
}


# ─────────────────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────────────────

def load_json(name: str) -> dict:
    with open(ROOT / name, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(name: str, data: dict) -> None:
    with open(ROOT / name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _extract_close_series(df: pd.DataFrame, days: int = 45) -> Optional[List[float]]:
    """
    从 AkShare 返回的 DataFrame 中提取收盘价序列。
    AkShare 不同接口的列名不同，这里做统一适配。
    """
    if df is None or df.empty:
        return None

    # 尝试多种可能的列名
    close_col = None
    for col_name in ["close", "收盘", "Close", "收盘价"]:
        if col_name in df.columns:
            close_col = col_name
            break

    if close_col is None:
        return None

    values = df[close_col].dropna().tolist()
    values = [round(float(x), 2) for x in values if float(x) > 0]

    if len(values) < 7:
        return None

    return values[-days:]


def _make_result(values: List[float]) -> Dict[str, List[float]]:
    """从收盘价序列生成 sparkline(7天) + chartData(30天)"""
    sparkline = values[-7:]
    chart_data = values[-30:] if len(values) >= 30 else values
    return {"sparkline": sparkline, "chartData": chart_data}


# ─────────────────────────────────────────────────────────────────────────────
# AkShare 数据获取 — 分类型调用
# ─────────────────────────────────────────────────────────────────────────────

def _fetch_us_stock_sina(symbol: str) -> Optional[List[float]]:
    """美股个股 — 新浪源（先尝试 adjust=qfq，失败则不带 adjust 重试）"""
    for adjust in ["qfq", ""]:
        try:
            if adjust:
                df = ak.stock_us_daily(symbol=symbol, adjust=adjust)
            else:
                df = ak.stock_us_daily(symbol=symbol)
            result = _extract_close_series(df)
            if result:
                return result
        except Exception:
            continue
    print(f"    [新浪源失败] us_stock {symbol}")
    return None


def _fetch_us_stock_em(symbol: str) -> Optional[List[float]]:
    """美股个股 — 东方财富源 fallback"""
    try:
        df = ak.stock_us_hist(symbol=symbol, period="daily", adjust="qfq")
        return _extract_close_series(df)
    except Exception as e:
        print(f"    [东方财富源失败] us_stock {symbol}: {e}")
        return None


def _fetch_hk_stock_sina(symbol: str) -> Optional[List[float]]:
    """港股个股 — 新浪源"""
    try:
        df = ak.stock_hk_daily(symbol=symbol, adjust="qfq")
        return _extract_close_series(df)
    except Exception as e:
        print(f"    [新浪源失败] hk_stock {symbol}: {e}")
        return None


def _fetch_hk_stock_em(symbol: str) -> Optional[List[float]]:
    """港股个股 — 东方财富源 fallback"""
    try:
        df = ak.stock_hk_hist(symbol=symbol, period="daily", adjust="qfq")
        return _extract_close_series(df)
    except Exception as e:
        print(f"    [东方财富源失败] hk_stock {symbol}: {e}")
        return None


def _fetch_cn_stock_sina(symbol: str) -> Optional[List[float]]:
    """A股个股 — 新浪源（先尝试 adjust=qfq，失败则不带 adjust）"""
    for adjust in ["qfq", ""]:
        try:
            if adjust:
                df = ak.stock_zh_a_daily(symbol=symbol, adjust=adjust)
            else:
                df = ak.stock_zh_a_daily(symbol=symbol)
            result = _extract_close_series(df)
            if result:
                return result
        except Exception:
            continue
    print(f"    [新浪源失败] cn_stock {symbol}")
    return None


def _fetch_cn_stock_em(symbol: str) -> Optional[List[float]]:
    """A股个股 — 东方财富源 fallback"""
    try:
        # 东方财富源需要纯数字代码
        code = symbol.replace("sz", "").replace("sh", "")
        df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
        return _extract_close_series(df)
    except Exception as e:
        print(f"    [东方财富源失败] cn_stock {symbol}: {e}")
        return None


def _fetch_us_index(symbol: str) -> Optional[List[float]]:
    """美股指数 / 日经 — 新浪源"""
    try:
        df = ak.index_us_stock_sina(symbol=symbol)
        return _extract_close_series(df)
    except Exception as e:
        print(f"    [新浪源失败] us_index {symbol}: {e}")
        return None


def _fetch_cn_index(symbol: str) -> Optional[List[float]]:
    """A股指数 — 东方财富源（新浪源无可靠的 A 股指数接口）"""
    try:
        df = ak.stock_zh_index_daily(symbol=symbol)
        return _extract_close_series(df)
    except Exception as e:
        print(f"    [东方财富源失败] cn_index {symbol}: {e}")
        return None


def _fetch_hk_index(symbol: str) -> Optional[List[float]]:
    """港股指数 — 新浪源"""
    try:
        df = ak.stock_hk_index_daily_sina(symbol=symbol)
        return _extract_close_series(df)
    except Exception as e:
        print(f"    [新浪源失败] hk_index {symbol}: {e}")
        return None


def _fetch_commodity(symbol: str) -> Optional[List[float]]:
    """大宗商品 — 新浪源"""
    try:
        df = ak.futures_foreign_hist(symbol=symbol)
        return _extract_close_series(df)
    except Exception as e:
        print(f"    [新浪源失败] commodity {symbol}: {e}")
        return None


# ─────────────────────────────────────────────────────────────────────────────
# 统一调度：根据 type 选择数据源，自带 fallback
# ─────────────────────────────────────────────────────────────────────────────

def fetch_akshare(config: dict) -> Optional[Dict[str, List[float]]]:
    """
    根据配置获取历史数据。主用新浪源，失败时降级到东方财富源。
    返回 {"sparkline": [...7个值...], "chartData": [...30个值...]}
    失败返回 None。
    """
    data_type = config.get("type")
    symbol = config.get("symbol", "")

    if data_type == "skip":
        return None

    values = None

    # ── 新浪源（主） ──
    if data_type == "us_stock":
        values = _fetch_us_stock_sina(symbol)
        if values is None:
            time.sleep(SLEEP_INTERVAL)
            values = _fetch_us_stock_em(symbol)  # fallback

    elif data_type == "hk_stock":
        values = _fetch_hk_stock_sina(symbol)
        if values is None:
            time.sleep(SLEEP_INTERVAL)
            values = _fetch_hk_stock_em(symbol)  # fallback

    elif data_type == "cn_stock":
        values = _fetch_cn_stock_sina(symbol)
        if values is None:
            time.sleep(SLEEP_INTERVAL)
            values = _fetch_cn_stock_em(symbol)  # fallback

    elif data_type == "us_index":
        values = _fetch_us_index(symbol)

    elif data_type == "cn_index":
        values = _fetch_cn_index(symbol)

    elif data_type == "hk_index":
        values = _fetch_hk_index(symbol)

    elif data_type == "commodity":
        values = _fetch_commodity(symbol)

    else:
        return None

    if values is None or len(values) < 7:
        return None

    return _make_result(values)


# ─────────────────────────────────────────────────────────────────────────────
# 批量获取所有标的
# ─────────────────────────────────────────────────────────────────────────────

def batch_fetch_all() -> Dict[str, Dict[str, List[float]]]:
    """
    逐个获取所有标的的历史数据。
    返回 {标识key: {"sparkline": [...], "chartData": [...]}} 字典。
    """
    result: Dict[str, Dict[str, List[float]]] = {}
    total = 0
    success = 0

    # 收集所有需要获取的标的（去重）
    all_items: List[tuple] = []  # (key, config)
    seen_symbols = set()

    # markets 标的
    for name, config in MARKETS_SPARKLINE_MAP.items():
        if config is None or config.get("type") == "skip":
            continue
        key = f"market:{name}"
        sym = config.get("symbol", "")
        if sym not in seen_symbols:
            all_items.append((key, config))
            seen_symbols.add(sym)

    # watchlist 标的
    for symbol, config in WATCHLIST_AK_MAP.items():
        if config is None or config.get("type") == "skip":
            continue
        key = f"watch:{symbol}"
        sym = config.get("symbol", "")
        if sym not in seen_symbols:
            all_items.append((key, config))
            seen_symbols.add(sym)
        else:
            # 已从 markets 获取过，复用
            for existing_key, existing_config in all_items:
                if existing_config.get("symbol") == sym and existing_key in result:
                    result[key] = result[existing_key]
                    break

    print(f"[INFO] 开始逐个获取 {len(all_items)} 个标的历史数据...")
    print(f"[INFO] 数据源：AkShare 新浪源（主）+ 东方财富源（fallback）")
    print(f"[INFO] 防限流间隔：{SLEEP_INTERVAL}秒")
    print()

    for key, config in all_items:
        total += 1
        sym = config.get("symbol", "")
        data_type = config.get("type", "")

        hist = fetch_akshare(config)
        if hist:
            result[key] = hist
            # 如果是 markets 标的，同时检查 watchlist 是否有同 symbol 的标的
            if key.startswith("market:"):
                for w_symbol, w_config in WATCHLIST_AK_MAP.items():
                    if w_config and w_config.get("symbol") == sym:
                        result[f"watch:{w_symbol}"] = hist
            success += 1
            print(f"  ✅ [{data_type}] {sym}: sparkline({len(hist['sparkline'])}天) / chartData({len(hist['chartData'])}天)")
        else:
            print(f"  ❌ [{data_type}] {sym}: 全部数据源失败，跳过")

        time.sleep(SLEEP_INTERVAL)

    print()
    print(f"[INFO] 获取完成：{success}/{total} 成功")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 更新 markets.json — 只写 sparkline
# ─────────────────────────────────────────────────────────────────────────────

def patch_markets(markets: dict, hist_map: Dict[str, Dict[str, List[float]]]) -> int:
    updated = 0

    def _patch_list(items: list) -> None:
        nonlocal updated
        for item in items:
            name = item.get("name", "")
            key = f"market:{name}"
            hist = hist_map.get(key)
            if hist:
                item["sparkline"] = hist["sparkline"]
                updated += 1

    for section in ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"]:
        _patch_list(markets.get(section, []))

    return updated


# ─────────────────────────────────────────────────────────────────────────────
# 更新 watchlist.json — 只写 sparkline + chartData
# ─────────────────────────────────────────────────────────────────────────────

def patch_watchlist(watchlist: dict, hist_map: Dict[str, Dict[str, List[float]]]) -> int:
    updated = 0

    for sector_id, items in watchlist.get("stocks", {}).items():
        for item in items:
            symbol = item.get("symbol", "")
            key = f"watch:{symbol}"
            hist = hist_map.get(key)
            if hist:
                item["sparkline"] = hist["sparkline"]
                item["chartData"] = hist["chartData"]
                updated += 1

    return updated


# ─────────────────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("=" * 60)
    print("投研鸭 sparkline/chartData 历史序列补全 v3.0")
    print("  数据源：AkShare 新浪源（主）+ 东方财富源（fallback）")
    print("=" * 60)
    print()
    print("【脚本边界】")
    print("  ✅ 只写：sparkline（7天）/ chartData（30天）")
    print("  ❌ 不碰：price / change / metrics / trafficLights /")
    print("           riskScore / riskLevel / riskAdvice /")
    print("           globalReaction / gics / 任何文字字段")
    print("  📦 数据源：AkShare 新浪源（主）+ 东方财富源（fallback）")
    print("  🛡️ 防限流：逐个调用 + 0.3s 间隔")
    print()

    # 获取所有历史数据
    hist_map = batch_fetch_all()

    if not hist_map:
        print()
        print("❌ 所有标的获取均失败，可能是网络问题。JSON 文件保持不变。")
        sys.exit(1)

    # 加载 JSON（只读取需要修改的文件）
    print()
    print("[INFO] 加载 JSON 文件...")
    markets = load_json("markets.json")
    watchlist = load_json("watchlist.json")

    # 打补丁
    m_updated = patch_markets(markets, hist_map)
    w_updated = patch_watchlist(watchlist, hist_map)

    # 回写
    dump_json("markets.json", markets)
    dump_json("watchlist.json", watchlist)

    print()
    print("=" * 60)
    print(f"✅ 补全完成：")
    print(f"   markets.json  → {m_updated} 个标的 sparkline 已更新")
    print(f"   watchlist.json → {w_updated} 个标的 sparkline + chartData 已更新")
    print(f"   briefing.json / radar.json → 未读取，未修改")
    print()
    print("   数据源：AkShare 新浪源（主）+ 东方财富源（fallback）")
    print("   AkShare 缺口（保留 AI 估算值）：")
    print("     VIX / 美元指数DXY / 10Y美债 / 离岸人民币CNH / BTC / ETH")
    print()
    print("   字节跳动（ByteDance）：未上市，跳过")
    print("   港股/A股：已加入映射表，双源获取（新浪→东方财富 fallback）")
    print("   A股格式：深交所 sz+代码 / 上交所 sh+代码")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
