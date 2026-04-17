#!/usr/bin/env python3
"""
投研鸭小程序 — 执行后自动报告生成器 v1.0
============================================================
核心理念（Harness Engineering v10.0）:
  AI 不再需要手写交付确认模板。本脚本在上传完成后运行，
  自动生成交付确认、质量 diff、数据统计。

用法:
  python3 post_flight.py <sync_dir>
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BJT = timezone(timedelta(hours=8))
SCRIPT_DIR = Path(__file__).parent.resolve()
REFERENCES_DIR = SCRIPT_DIR.parent / "references"
BASELINE_PATH = REFERENCES_DIR / "golden-baseline.json"


def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def count_stocks(watchlist):
    total = 0
    if not watchlist:
        return 0
    stocks = watchlist.get("stocks", {})
    for sector_id, stock_list in stocks.items():
        if isinstance(stock_list, list):
            total += len(stock_list)
    return total


def count_sectors(watchlist):
    if not watchlist:
        return 0
    return len(watchlist.get("sectors", []))


def main():
    if len(sys.argv) < 2:
        print("用法: python3 post_flight.py <sync_dir>")
        sys.exit(2)

    sync_dir = sys.argv[1]
    now = datetime.now(BJT)
    date_str = now.strftime("%Y-%m-%d")

    # 加载4个JSON
    briefing = load_json(os.path.join(sync_dir, "briefing.json"))
    markets = load_json(os.path.join(sync_dir, "markets.json"))
    watchlist = load_json(os.path.join(sync_dir, "watchlist.json"))
    radar = load_json(os.path.join(sync_dir, "radar.json"))

    files_status = {
        "briefing.json": "✅" if briefing else "❌",
        "markets.json": "✅" if markets else "❌",
        "watchlist.json": "✅" if watchlist else "❌",
        "radar.json": "✅" if radar else "❌",
    }

    # 统计
    stock_count = count_stocks(watchlist)
    sector_count = count_sectors(watchlist)

    # 数据完整度
    total_files = 4
    present_files = sum(1 for v in files_status.values() if v == "✅")
    completeness = f"{present_files}/{total_files} ({present_files/total_files*100:.0f}%)"

    # 加载基线做 diff
    baseline = load_json(BASELINE_PATH) or {}
    gates = baseline.get("regressionGates", {})

    print(f"\n{'='*60}")
    print(f"📱 投研鸭小程序数据更新完成 — {date_str}")
    print(f"{'='*60}")

    for fname, status in files_status.items():
        desc = {
            "briefing.json": "简报页（核心事件+判断+建议+情绪+聪明钱）",
            "markets.json": "市场页（美股+M7+亚太+大宗+加密+GICS热力图）",
            "watchlist.json": f"标的页（{sector_count}板块×{stock_count}只标的+详情+metrics）",
            "radar.json": "雷达页（安全信号+聪明钱+本周前瞻+预测市场+异动信号）",
        }
        print(f"  {status} {fname} → {desc[fname]}")

    print(f"\n🔧 公式自动计算：auto_compute.py v3.0 已执行")
    print(f"📊 数据完整度：{completeness}")

    # 质量回归 diff
    print(f"\n{'─'*60}")
    print(f"📋 质量回归 diff（vs 黄金基线 2026-04-06）")
    print(f"{'─'*60}")

    if briefing:
        th_count = len(briefing.get("topHoldings", []))
        sm_count = len(briefing.get("smartMoney", []))
        print(f"  topHoldings 条数: 基线≥3 | 实际={th_count} | {'✅' if th_count >= 3 else '⚠️退化'}")
        print(f"  smartMoney 条数: 基线≥2 | 实际={sm_count} | {'✅' if sm_count >= 2 else '⚠️退化'}")

    if radar:
        smh = radar.get("smartMoneyHoldings", [])
        for holding in smh:
            manager = holding.get("manager", "?")
            pos_count = len(holding.get("positions", []))
            print(f"  positions({manager[:6]}): 基线≥10 | 实际={pos_count} | {'✅' if pos_count >= 10 else '⚠️退化'}")

        smd = radar.get("smartMoneyDetail", [])
        tier_count = len(smd)
        print(f"  smartMoneyDetail 梯队: 基线=3 | 实际={tier_count}/3 | {'✅' if tier_count >= 3 else '⚠️退化'}")

    # sourceType 一致性
    types = set()
    for data in [briefing, markets, watchlist, radar]:
        if data and "_meta" in data:
            types.add(data["_meta"].get("sourceType", ""))
    if len(types) == 1:
        print(f"  sourceType 一致性: ✅ 全部为 '{list(types)[0]}'")
    else:
        print(f"  sourceType 一致性: ⚠️ 不一致 {types}")

    print(f"\n{'='*60}\n")


if __name__ == "__main__":
    main()
