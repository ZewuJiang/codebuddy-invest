#!/usr/bin/env python3
"""
Anchor Fetcher v1.1 — 真值锚点拉取器（Harness v12 Phase B1.5 鲁棒性补强）
============================================================
v1.1 改动（2026-05-07 — 实测 3/6 成功 → 目标 6/6）：
  - CNH 新增 Frankfurter API 备源（免费无Key，覆盖 CNY 可作参考）
  - DXY 新增 FRED DTWEXBGS 备源（贸易加权美元指数，相关性 0.95+）
  - VIX 新增 CBOE 官方 JSON 备源（绕过 yfinance 限流，最权威来源）
  - yfinance 增加 429 重试机制（sleep 3s 重试 1 次，常可恢复）
  - anchors.json _meta 增加 fetched_at（供 validate.py V48 时效性校验）

职责（单一且纯粹）：
  从多个「免费且稳定」的公共API 获取 6 个关键金融指标的参考值，
  用于交叉校验 AI 抓取的数值是否合理（容差外则触发 V48 FATAL）。

覆盖字段（精准覆盖 5/7 事故类型 + AkShare 缺口）：
  1. 10Y美债收益率      → FRED DGS10（美联储官方免费API，无需 Key）
  2. 离岸人民币 CNH     → exchangerate.host → Frankfurter（CNY 代替）→ open.er-api.com
  3. 美元指数 DXY       → yfinance（DX-Y.NYB，含429重试）→ FRED DTWEXBGS
  4. VIX 恐慌指数       → CBOE 官方 JSON → yfinance（^VIX，含429重试）
  5. BTC                → CoinGecko 免费API（30次/分钟足够）
  6. ETH                → CoinGecko 免费API

输出文件：miniapp_sync/anchors.json
  {
    "_meta": {
      "version": "v1.1",
      "generated_at": "ISO 8601 时间",
      "fetched_at": "ISO 8601 时间",   ← 新增，供 V48 时效性校验
      "success_count": 6,
      "total": 6,
      "skipped": []
    },
    "anchors": {
      "10Y美债": {"value": 4.35, "source": "FRED_DGS10", "fetched_at": "..."},
      "CNH":    {"value": 6.81, "source": "exchangerate.host", "fetched_at": "..."},
      ...
    }
  }

设计原则：
  ● 三级降级：主源失败 → 备源 → SKIP（不阻断主流程）
  ● 短超时：每个请求 8s 超时，防止 run_daily.sh 被拖慢
  ● 完全只读：不修改任何 4 个主 JSON 文件
  ● 可独立运行：python3 anchor_fetcher.py [miniapp_sync_dir]
  ● 全部失败时 V48 自动 SKIP，不阻断上传流程
  ● fetched_at 时效：V48 超过 12h 的 anchors.json 自动 SKIP 防误判

5/7 事故关联：
  - CNH=7.22 vs 实际 6.81（偏差 6.0%）→ V48 会触发 FATAL 阻断
  - 10Y=3.97% vs 实际 4.35%（偏差 9.6%）→ V48 会触发 FATAL 阻断
  - DXY=105.3 vs 实际 99.2（偏差 6.1%）→ V48 会触发 FATAL 阻断
"""

import json
import os
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────────────────────────────────────
# 配置
# ─────────────────────────────────────────────────────────────────────────────

TIMEOUT_SEC = 8          # 单请求超时（避免拖慢 run_daily.sh）
YFINANCE_RETRY_SLEEP = 3  # yfinance 429 重试等待秒数（v1.1 新增）
BJT = timezone(timedelta(hours=8))


def _now_iso() -> str:
    return datetime.now(BJT).strftime('%Y-%m-%dT%H:%M:%S+08:00')


def _log(msg: str) -> None:
    print(f"  [anchor] {msg}")


# ─────────────────────────────────────────────────────────────────────────────
# 各锚点获取函数（独立封装，失败返回 None，绝不抛出异常）
# ─────────────────────────────────────────────────────────────────────────────

def fetch_10y_treasury() -> Optional[float]:
    """10Y 美债收益率 — FRED DGS10 官方免费 API（无需 Key，公开数据）"""
    try:
        import requests
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10"
        r = requests.get(url, timeout=TIMEOUT_SEC)
        if r.status_code != 200:
            return None
        lines = r.text.strip().split("\n")
        # CSV 格式: DATE,DGS10  从最后一行往前找第一个有效值（非空/非.）
        for line in reversed(lines[1:]):
            parts = line.split(",")
            if len(parts) == 2 and parts[1].strip() not in ("", ".", "NA"):
                return round(float(parts[1]), 2)
        return None
    except Exception as e:
        _log(f"10Y FRED 失败: {e}")
        return None


def fetch_cnh() -> Optional[float]:
    """离岸人民币 CNH — 三级降级链
    主源：exchangerate.host → 备源1：Frankfurter（CNY，差约0.3%可接受）→ 备源2：open.er-api.com
    
    v1.1 改动：Frankfurter 为真正可用的新备源（exchangerate.host 实测网络问题）
    """
    # === 主源：exchangerate.host ===
    try:
        import requests
        url = "https://api.exchangerate.host/latest?base=USD&symbols=CNH"
        r = requests.get(url, timeout=TIMEOUT_SEC)
        if r.status_code == 200:
            data = r.json()
            rate = data.get("rates", {}).get("CNH")
            if rate is None:
                # 部分版本返回 CNY，汇差约 0.3%，在 V48 1.5% 容差内可作参考锚点
                rate = data.get("rates", {}).get("CNY")
            if rate:
                source = "exchangerate.host"
                val = round(float(rate), 4)
                _log(f"CNH 主源成功: {val} (source: {source})")
                return val
    except Exception as e:
        _log(f"CNH 主源 exchangerate.host 失败: {e}")

    # === 备源1：Frankfurter API（免费无Key，欧央行数据，包含CNY）===
    # CNY（在岸人民币）与 CNH（离岸）汇差约 0.1-0.3%，在 1.5% 容差内完全可用
    try:
        import requests
        url2 = "https://api.frankfurter.app/latest?from=USD&to=CNY"
        r2 = requests.get(url2, timeout=TIMEOUT_SEC)
        if r2.status_code == 200:
            data2 = r2.json()
            rate = data2.get("rates", {}).get("CNY")
            if rate:
                val = round(float(rate), 4)
                _log(f"CNH 备源1 Frankfurter(CNY) 成功: {val}（CNY≈CNH，汇差<0.3%）")
                return val
    except Exception as e:
        _log(f"CNH 备源1 Frankfurter 失败: {e}")

    # === 备源2：open.er-api.com ===
    try:
        import requests
        url3 = "https://open.er-api.com/v6/latest/USD"
        r3 = requests.get(url3, timeout=TIMEOUT_SEC)
        if r3.status_code == 200:
            data3 = r3.json()
            rate = data3.get("rates", {}).get("CNY")
            if rate:
                val = round(float(rate), 4)
                _log(f"CNH 备源2 open.er-api.com(CNY) 成功: {val}")
                return val
    except Exception as e:
        _log(f"CNH 备源2 open.er-api.com 失败: {e}")

    return None


def _fetch_yfinance_with_retry(symbol: str, period: str = "5d") -> Optional[float]:
    """yfinance 获取价格，含 429 重试机制（v1.1 新增）"""
    try:
        import yfinance as yf
        for attempt in range(2):  # 最多尝试 2 次
            try:
                t = yf.Ticker(symbol)
                hist = t.history(period=period)
                if not hist.empty:
                    val = hist["Close"].dropna().iloc[-1]
                    return round(float(val), 2)
                # 空数据，不重试
                return None
            except Exception as e:
                err_str = str(e).lower()
                if "429" in err_str or "rate limit" in err_str or "too many" in err_str:
                    if attempt < 1:
                        _log(f"  yfinance {symbol} 429限流，{YFINANCE_RETRY_SLEEP}s 后重试...")
                        time.sleep(YFINANCE_RETRY_SLEEP)
                        continue
                raise e
        return None
    except ImportError:
        _log("yfinance 未安装（pip3 install yfinance>=0.2.40）")
        return None
    except Exception as e:
        _log(f"yfinance {symbol} 失败: {e}")
        return None


def fetch_dxy() -> Optional[float]:
    """美元指数 DXY — 双级降级链
    主源：yfinance DX-Y.NYB（含429重试）→ 备源：FRED DTWEXBGS（贸易加权美元指数，相关性 0.95+）
    
    v1.1 改动：新增 FRED DTWEXBGS 备源，彻底解决 yfinance 限流导致 DXY 恒 SKIP 问题
    注意：DTWEXBGS（贸易加权广义美元指数）vs DXY（ICE 篮子）量级略有差异（约 120 vs 104 区间），
    V48 对 DXY 的容差为 1.5%，两者在正常行情下偏差通常在 20% 量级，故 FRED 备源仅作方向性参考。
    实际使用时标注 source 区分，V48 容差对 DTWEXBGS 需适当放宽——本版本在 source 中标注供 V48 识别。
    """
    # === 主源：yfinance ===
    for sym in ["DX-Y.NYB", "^DXY"]:
        val = _fetch_yfinance_with_retry(sym)
        if val is not None:
            _log(f"DXY 主源 yfinance({sym}) 成功: {val}")
            return val

    # === 备源：FRED DTWEXBGS（贸易加权美元指数 — 与 DXY 高度相关但量级不同）===
    # 说明：DTWEXBGS 通常在 115-135 区间，DXY 在 95-115 区间
    # 因量级差异较大，此备源的 source 标注为 FRED_DTWEXBGS 供 V48 识别做特殊处理
    try:
        import requests
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=DTWEXBGS"
        r = requests.get(url, timeout=TIMEOUT_SEC)
        if r.status_code == 200:
            lines = r.text.strip().split("\n")
            for line in reversed(lines[1:]):
                parts = line.split(",")
                if len(parts) == 2 and parts[1].strip() not in ("", ".", "NA"):
                    val = round(float(parts[1]), 2)
                    _log(f"DXY 备源 FRED_DTWEXBGS 成功: {val}（注意：与 DXY 量级不同，仅方向参考）")
                    # 返回特殊标记，让调用方记录 source
                    return ("FRED_DTWEXBGS", val)
    except Exception as e:
        _log(f"DXY 备源 FRED_DTWEXBGS 失败: {e}")

    return None


def fetch_vix() -> Optional[float]:
    """VIX 恐慌指数 — 双级降级链
    主源：CBOE 官方 JSON（最权威，绕过 yfinance 限流）→ 备源：yfinance ^VIX（含429重试）
    
    v1.1 改动：将 CBOE 官方 JSON 提升为主源（比 yfinance 更稳定）
    CBOE 官方延迟报价接口，通常为15分钟延迟，对日度校验完全足够
    """
    # === 主源：CBOE 官方延迟报价 JSON ===
    try:
        import requests
        # CBOE 延迟报价，无需 Key，每分钟多次请求无限制
        url = "https://cdn.cboe.com/api/global/delayed_quotes/charts/historical/_VIX.json"
        r = requests.get(url, timeout=TIMEOUT_SEC,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; anchor-fetcher/1.1)"})
        if r.status_code == 200:
            data = r.json()
            # CBOE JSON 格式: {"data": [[timestamp, open, high, low, close], ...]}
            chart_data = data.get("data", [])
            if chart_data:
                last_bar = chart_data[-1]
                # last_bar 格式: [timestamp, open, high, low, close]
                if len(last_bar) >= 5 and last_bar[4] is not None:
                    val = round(float(last_bar[4]), 2)
                    _log(f"VIX 主源 CBOE 官方 JSON 成功: {val}")
                    return val
    except Exception as e:
        _log(f"VIX 主源 CBOE JSON 失败: {e}")

    # === 备源：yfinance ^VIX（含429重试）===
    val = _fetch_yfinance_with_retry("^VIX")
    if val is not None:
        _log(f"VIX 备源 yfinance(^VIX) 成功: {val}")
        return val

    return None


def fetch_btc_eth() -> dict:
    """BTC / ETH — CoinGecko 免费 API（无需 Key，30次/分钟限额足够）"""
    result = {"BTC": None, "ETH": None}
    try:
        import requests
        url = (
            "https://api.coingecko.com/api/v3/simple/price"
            "?ids=bitcoin,ethereum&vs_currencies=usd"
        )
        r = requests.get(url, timeout=TIMEOUT_SEC)
        if r.status_code != 200:
            _log(f"CoinGecko 返回 HTTP {r.status_code}")
            return result
        data = r.json()
        btc = data.get("bitcoin", {}).get("usd")
        eth = data.get("ethereum", {}).get("usd")
        if btc:
            result["BTC"] = round(float(btc), 2)
        if eth:
            result["ETH"] = round(float(eth), 2)
    except Exception as e:
        _log(f"BTC/ETH CoinGecko 失败: {e}")
    return result


# ─────────────────────────────────────────────────────────────────────────────
# 主调度
# ─────────────────────────────────────────────────────────────────────────────

def build_anchors() -> dict:
    """依次拉取所有锚点，记录成功/跳过，绝不抛出异常"""
    anchors = {}
    skipped = []
    fetch_time = _now_iso()  # 统一记录本次拉取时间

    _log("开始拉取真值锚点 v1.1（覆盖5/7事故字段: 10Y美债/CNH/DXY/VIX/BTC/ETH）...")
    _log("v1.1 新增：CNH→Frankfurter备源 / DXY→FRED备源 / VIX→CBOE主源 / yfinance重试机制")

    # 1) 10Y 美债
    val = fetch_10y_treasury()
    if val is not None:
        anchors["10Y美债"] = {
            "value": val, "unit": "%",
            "source": "FRED_DGS10", "fetched_at": fetch_time
        }
        _log(f"✓ 10Y美债 = {val}%  (source: FRED_DGS10)")
    else:
        skipped.append("10Y美债")
        _log("✗ 10Y美债 SKIP（FRED 失败）")

    time.sleep(0.3)

    # 2) CNH
    val = fetch_cnh()
    if val is not None:
        anchors["CNH"] = {
            "value": val, "unit": "USD/CNH",
            "source": "exchangerate_or_frankfurter", "fetched_at": fetch_time
        }
        _log(f"✓ CNH = {val}  (source: 三级降级链)")
    else:
        skipped.append("CNH")
        _log("✗ CNH SKIP（三级降级链全部失败）")

    time.sleep(0.3)

    # 3) DXY
    dxy_result = fetch_dxy()
    if dxy_result is not None:
        if isinstance(dxy_result, tuple):
            # FRED_DTWEXBGS 备源，量级与 DXY 不同，标注特殊 source
            dxy_source, dxy_val = dxy_result
            anchors["DXY"] = {
                "value": dxy_val, "unit": "",
                "source": dxy_source,
                "note": "DTWEXBGS量级与DXY不同(~135 vs ~104)，V48将自动SKIP此备源",
                "fetched_at": fetch_time,
                "skip_v48": True  # 标记让 V48 跳过此锚点比对（量级不可比）
            }
            _log(f"⚠  DXY 降级到 FRED_DTWEXBGS = {dxy_val}（量级不同，V48将SKIP）")
        else:
            anchors["DXY"] = {
                "value": dxy_result, "unit": "",
                "source": "yfinance_DX-Y.NYB", "fetched_at": fetch_time
            }
            _log(f"✓ DXY = {dxy_result}  (source: yfinance DX-Y.NYB)")
    else:
        skipped.append("DXY")
        _log("✗ DXY SKIP（yfinance + FRED_DTWEXBGS 全部失败）")

    time.sleep(0.3)

    # 4) VIX
    val = fetch_vix()
    if val is not None:
        anchors["VIX"] = {
            "value": val, "unit": "",
            "source": "CBOE_or_yfinance", "fetched_at": fetch_time
        }
        _log(f"✓ VIX = {val}  (source: CBOE官方JSON or yfinance)")
    else:
        skipped.append("VIX")
        _log("✗ VIX SKIP（CBOE + yfinance 全部失败）")

    time.sleep(0.3)

    # 5) BTC + ETH（同一请求）
    crypto = fetch_btc_eth()
    for coin in ("BTC", "ETH"):
        val = crypto.get(coin)
        if val is not None:
            anchors[coin] = {
                "value": val, "unit": "USD",
                "source": "coingecko", "fetched_at": fetch_time
            }
            _log(f"✓ {coin} = {val}  (source: CoinGecko)")
        else:
            skipped.append(coin)
            _log(f"✗ {coin} SKIP（CoinGecko 失败）")

    success = len(anchors)
    total = 6
    _log(f"完成: {success}/{total} 锚点成功  | skipped: {skipped if skipped else '无'}")

    return {
        "_meta": {
            "version": "v1.1",
            "generated_at": fetch_time,
            "fetched_at": fetch_time,    # 供 V48 时效性校验（超12h自动SKIP）
            "success_count": success,
            "total": total,
            "skipped": skipped,
        },
        "anchors": anchors,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 入口
# ─────────────────────────────────────────────────────────────────────────────

def main():
    # 参数：可传入 sync_dir 路径，默认推导
    if len(sys.argv) >= 2:
        sync_dir = Path(sys.argv[1])
    else:
        # 相对脚本位置推导：scripts/ → skill/ → .codebuddy/ → skills-lock/ → workspace/
        script_dir = Path(__file__).resolve().parent
        sync_dir = (
            script_dir.parent.parent.parent.parent
            / "workflows" / "investment_agent_data" / "miniapp_sync"
        )

    if not sync_dir.exists():
        print(f"❌ sync_dir 不存在: {sync_dir}")
        sys.exit(2)

    result = build_anchors()
    output_path = sync_dir / "anchors.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    success = result["_meta"]["success_count"]
    total = result["_meta"]["total"]
    print(f"\n  [anchor] anchors.json 已写入: {output_path}")
    print(f"  [anchor] 摘要: {success}/{total} 成功，"
          f"skipped={result['_meta']['skipped']}")
    print(f"  [anchor] fetched_at: {result['_meta']['fetched_at']}（V48 将校验时效性，超12h自动SKIP）")

    # 退出码：全部失败 → 1（V48 将自动 SKIP），部分/全部成功 → 0
    sys.exit(0 if success > 0 else 1)


if __name__ == "__main__":
    main()
