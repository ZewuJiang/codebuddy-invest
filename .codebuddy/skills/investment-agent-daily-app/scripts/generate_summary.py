#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_summary.py — 投研鸭历史归档摘要生成器 v1.0

从 4 个 JSON（briefing/markets/watchlist/radar）提取关键指标，
生成 ~2KB 的 summary.json，供 AI 做跨天趋势分析。

用法：
    python3 generate_summary.py <源JSON目录> <输出目录> [日期YYYY-MM-DD]

示例：
    python3 generate_summary.py ./miniapp_sync/ ./archive/2026-04-08/ 2026-04-08
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta


def load_json(filepath):
    """安全加载 JSON 文件"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  ⚠️  加载 {os.path.basename(filepath)} 失败: {e}")
        return None


def extract_us_market(markets, name_keyword):
    """从 usMarkets 数组中按名称关键词提取指标"""
    if not markets:
        return None
    for item in markets.get("usMarkets", []):
        if name_keyword in item.get("name", ""):
            price = item.get("price", "")
            change = item.get("change", 0)
            # price 可能是字符串如 "6,616.85"，转为数字
            try:
                price_num = float(str(price).replace(",", "").replace("$", "").replace("%", ""))
            except (ValueError, TypeError):
                price_num = price
            return {"price": price_num, "change": change}
    return None


def count_traffic_lights(radar):
    """统计红绿灯信号数量"""
    counts = {"red": 0, "yellow": 0, "green": 0}
    if not radar:
        return counts
    for tl in radar.get("trafficLights", []):
        status = tl.get("status", "")
        if status in counts:
            counts[status] += 1
    return counts


def extract_top_movers(markets):
    """从 m7 提取最大涨/跌标的"""
    movers = []
    if not markets:
        return movers
    m7 = markets.get("m7", [])
    if not m7:
        return movers

    # 找涨幅最大的
    sorted_up = sorted(m7, key=lambda x: x.get("change", 0), reverse=True)
    if sorted_up:
        top = sorted_up[0]
        movers.append({
            "name": top.get("symbol", top.get("name", "")),
            "change": top.get("change", 0),
            "reason": ""  # 精简版不含原因，节省空间
        })

    # 找跌幅最大的
    sorted_down = sorted(m7, key=lambda x: x.get("change", 0))
    if sorted_down and sorted_down[0].get("change", 0) < 0:
        bottom = sorted_down[0]
        movers.append({
            "name": bottom.get("symbol", bottom.get("name", "")),
            "change": bottom.get("change", 0),
            "reason": ""
        })

    return movers


def extract_smart_money_summary(briefing):
    """从 briefing 的 smartMoney 提取一句话摘要"""
    smart_money = briefing.get("smartMoney", [])
    if not smart_money:
        return ""
    parts = []
    for sm in smart_money[:3]:
        source = sm.get("source", "")
        action = sm.get("action", "")
        # 截取前30字
        short_action = action[:30] + "…" if len(action) > 30 else action
        parts.append(f"{source}: {short_action}")
    return "；".join(parts)


def extract_action_summary(briefing):
    """从 actionHints 提取行动摘要"""
    actions = briefing.get("actionHints", [])
    if not actions:
        return "暂无明确行动建议"
    # 取第一条行动建议的简短版本
    first = actions[0]
    content = first.get("content", "")
    return content[:50] + "…" if len(content) > 50 else content


def generate_summary(src_dir, output_dir, date_str):
    """主函数：从4个JSON生成summary.json"""

    # 加载数据
    briefing = load_json(os.path.join(src_dir, "briefing.json"))
    markets = load_json(os.path.join(src_dir, "markets.json"))
    radar = load_json(os.path.join(src_dir, "radar.json"))

    if not briefing:
        print("  ❌ briefing.json 不存在或无法解析，无法生成 summary.json")
        return False

    # 北京时间
    bj_tz = timezone(timedelta(hours=8))
    now_bj = datetime.now(bj_tz)

    # 提取各项指标
    sp500 = extract_us_market(markets, "标普") or extract_us_market(markets, "SP") or {}
    nasdaq = extract_us_market(markets, "纳斯达克") or extract_us_market(markets, "NASDAQ") or {}
    vix = extract_us_market(markets, "VIX") or {}

    tl_counts = count_traffic_lights(radar)
    top_movers = extract_top_movers(markets)
    smart_money_summary = extract_smart_money_summary(briefing)
    action_summary = extract_action_summary(briefing)

    # 核心事件标题
    core_event = briefing.get("coreEvent", {})
    core_event_title = core_event.get("title", "") if core_event else ""

    # 构建 summary.json
    summary = {
        "date": date_str,
        "updatedAt": now_bj.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "sentiment": {
            "score": briefing.get("sentimentScore", 0),
            "label": briefing.get("sentimentLabel", "")
        },
        "risk": {
            "score": radar.get("riskScore", 0) if radar else 0,
            "level": radar.get("riskLevel", "") if radar else ""
        },
        "trafficLights": tl_counts,
        "coreEvent": core_event_title,
        "usMarkets": {
            "sp500": sp500 if sp500 else {"price": 0, "change": 0},
            "nasdaq": nasdaq if nasdaq else {"price": 0, "change": 0},
            "vix": vix if vix else {"price": 0, "change": 0}
        },
        "topMovers": top_movers,
        "smartMoneySummary": smart_money_summary,
        "actionSummary": action_summary,
        "briefingUrl": f"archive/{date_str}/briefing.md"
    }

    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 写入文件
    output_path = os.path.join(output_dir, "summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    file_size = os.path.getsize(output_path)
    print(f"  ✅ summary.json 生成成功 ({file_size:,} bytes)")
    print(f"     日期: {date_str}")
    print(f"     情绪: {summary['sentiment']['score']}/100 {summary['sentiment']['label']}")
    print(f"     风险: {summary['risk']['score']}/100 {summary['risk']['level']}")
    print(f"     红绿灯: {tl_counts['red']}红 {tl_counts['yellow']}黄 {tl_counts['green']}绿")
    print(f"     输出: {output_path}")

    return True


def main():
    if len(sys.argv) < 3:
        print("用法: python3 generate_summary.py <源JSON目录> <输出目录> [日期YYYY-MM-DD]")
        print("示例: python3 generate_summary.py ./miniapp_sync/ ./archive/2026-04-08/ 2026-04-08")
        sys.exit(1)

    src_dir = sys.argv[1]
    output_dir = sys.argv[2]
    date_str = sys.argv[3] if len(sys.argv) > 3 else datetime.now().strftime("%Y-%m-%d")

    if not os.path.isdir(src_dir):
        print(f"❌ 源目录不存在: {src_dir}")
        sys.exit(1)

    success = generate_summary(src_dir, output_dir, date_str)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
