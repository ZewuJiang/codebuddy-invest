#!/usr/bin/env python3
"""
投研鸭小程序 — 执行前清单自动生成器 v1.0
============================================================
核心理念（Harness Engineering v10.0）:
  AI 不再需要"记住"今天该执行什么、该注意什么。
  本脚本在每次执行前运行，自动生成针对今天的精确清单。

功能：
  1. 模式判定（Standard/Weekend）
  2. 今天需要执行的采集批次清单
  3. 13F 窗口期判定
  4. 上次校验的 WARN 项（需要本次关注）
  5. 上次产出的数据新鲜度检查

用法:
  python3 checklist_generator.py [sync_dir]
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BJT = timezone(timedelta(hours=8))
SCRIPT_DIR = Path(__file__).parent.resolve()
SYNC_DIR_DEFAULT = SCRIPT_DIR.parent.parent.parent / "workflows" / "investment_agent_data" / "miniapp_sync"

# 13F 窗口期（每年的 2/5/8/11 月 10-20 日）
THIRTEEN_F_MONTHS = {2, 5, 8, 11}
THIRTEEN_F_DAY_START = 10
THIRTEEN_F_DAY_END = 20

# 美国主要休市日（月-日格式，2026年）
US_HOLIDAYS_2026 = {
    (1, 1),   # 新年
    (1, 19),  # MLK Day
    (2, 16),  # Presidents Day
    (4, 3),   # Good Friday
    (5, 25),  # Memorial Day
    (6, 19),  # Juneteenth
    (7, 4),   # Independence Day (observed 7/3)
    (9, 7),   # Labor Day
    (11, 26), # Thanksgiving
    (12, 25), # Christmas
}


def load_json(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def is_weekend(dt):
    return dt.weekday() >= 5


def is_us_holiday(dt):
    return (dt.month, dt.day) in US_HOLIDAYS_2026


def is_13f_window(dt):
    return dt.month in THIRTEEN_F_MONTHS and THIRTEEN_F_DAY_START <= dt.day <= THIRTEEN_F_DAY_END


def get_next_13f_window(dt):
    months = sorted(THIRTEEN_F_MONTHS)
    for m in months:
        if m > dt.month or (m == dt.month and dt.day < THIRTEEN_F_DAY_START):
            return f"2026-{m:02d}-{THIRTEEN_F_DAY_START}"
    # 下一年
    return f"2027-{months[0]:02d}-{THIRTEEN_F_DAY_START}"


def check_data_freshness(sync_dir):
    """检查上次数据的新鲜度"""
    briefing = load_json(os.path.join(sync_dir, "briefing.json"))
    if not briefing:
        return "❌ briefing.json 不存在"

    data_time = briefing.get("dataTime", "")
    if not data_time:
        return "⚠️ dataTime 为空"

    return f"上次更新: {data_time}"


def check_last_validation(sync_dir):
    """模拟检查上次的 WARN 项"""
    # 实际运行 validate.py 太重，这里检查已知的常见问题点
    issues = []

    briefing = load_json(os.path.join(sync_dir, "briefing.json"))
    if briefing:
        # 检查 topHoldings 段永平权重
        for th in briefing.get("topHoldings", []):
            if "段永平" in th.get("name", ""):
                import re
                holdings = th.get("holdings", "")
                weights = re.findall(r'\d+\.\d%', holdings)
                if len(weights) < 3:
                    issues.append("R7: 段永平 topHoldings 缺权重百分比（需从 holdings-cache 引用完整权重）")

    # 检查 _meta.sourceType
    for fname in ["briefing.json", "markets.json", "watchlist.json", "radar.json"]:
        data = load_json(os.path.join(sync_dir, fname))
        if data and data.get("_meta", {}).get("sourceType") == "refresh_update":
            issues.append(f"V4: {fname} sourceType 仍为废弃值 refresh_update")
            break

    return issues


def main():
    now = datetime.now(BJT)
    sync_dir = sys.argv[1] if len(sys.argv) > 1 else str(SYNC_DIR_DEFAULT)

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    weekday_name = weekday_names[now.weekday()]

    print(f"\n{'='*60}")
    print(f"📋 投研鸭执行前清单 — {now.strftime('%Y-%m-%d')} {weekday_name}")
    print(f"{'='*60}")

    # 1. 模式判定
    if is_weekend(now) or is_us_holiday(now):
        mode = "Weekend"
        source_type = "weekend_insight"
        reason = "周末" if is_weekend(now) else "美股休市日"
    else:
        mode = "Standard"
        source_type = "heavy_analysis"
        reason = "工作日"

    print(f"\n🎯 模式: {mode} ({reason})")
    print(f"   _meta.sourceType = '{source_type}'")

    # 2. 采集批次
    print(f"\n📦 采集批次:")
    if mode == "Standard":
        batches = [
            "0  → 全球媒体头条扫描 (2-3次)",
            "0a → 深度媒体补充 (1-2次)",
            "0b → AI产业链专项 (1-2次)",
            "1a → M7个股精确数据 (7次 web_fetch)",
            "1b → 美股指数+VIX (3-4次 web_fetch)",
            "1c → GICS 11板块ETF (11次 web_fetch)",
            "1d → 焦点个股 (2-5次 web_fetch)",
            "2  → 亚太/港股数据 (2-3次)",
            "3  → 大宗/汇率/加密 (2-3次)",
            "4  → 基金&大资金动向 (8-12次)",
            "5  → watchlist 标的详情 (15-20次)",
            "6  → 事件日历+风险矩阵 (1-2次)",
            "A  → 情绪与预测数据 (1-3次, 可选)",
        ]
        if now.weekday() == 0:  # 周一
            batches.extend([
                "7  → 上周市场周度数据 (2-3次) ⚡周一额外",
                "8  → 本周关键事件日历 (2-3次) ⚡周一额外",
                "9  → 周末重大新闻 (2-3次) ⚡周一额外",
            ])
    else:
        batches = [
            "W0 → 全球媒体周末深度报道 (3-5次)",
            "W1 → 地缘政治/宏观进展 (2-3次)",
            "W2 → 下周事件日历+风险前瞻 (2次)",
            "W3 → 机构/策略师最新观点 (4-6次)",
            "WA → Polymarket 最新数据 (1-2次, 可选)",
        ]

    for b in batches:
        print(f"  ✅ {b}")

    # 3. 13F 窗口
    print(f"\n🗓️ 13F 窗口:")
    if is_13f_window(now):
        print(f"  🔴 当前处于 13F 窗口期! 必须 web_search 查证最新持仓数据")
        print(f"  📌 检查 SEC EDGAR / WhaleWisdom 是否有 {now.year}Q1 13F 新披露")
    else:
        next_window = get_next_13f_window(now)
        print(f"  🟢 非 13F 窗口 — 直接引用 holdings-cache.json")
        print(f"  📌 下次窗口: {next_window}")

    # 4. 上次产出检查
    print(f"\n🕐 数据新鲜度:")
    freshness = check_data_freshness(sync_dir)
    print(f"  {freshness}")

    # 5. 上次已知问题
    print(f"\n⚠️ 已知需关注项:")
    issues = check_last_validation(sync_dir)
    if issues:
        for issue in issues:
            print(f"  🟡 {issue}")
    else:
        print(f"  ✅ 无已知问题")

    # 6. 月度审计检查
    if now.day == 1:
        print(f"\n📋 ⚡月度规范审计触发!")
        print(f"  → 本次执行需额外执行月度审计（trafficLights阈值/堵点清单/数据源健康度/枚举值审计）")
    
    print(f"\n{'='*60}")
    print(f"✅ 清单生成完毕 — 开始执行 {mode} 模式工作流")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
