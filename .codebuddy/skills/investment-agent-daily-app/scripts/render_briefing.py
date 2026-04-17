#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
投研鸭 — JSON → Markdown 渲染脚本 v1.0
将 miniapp_sync/ 下的 4 个 JSON 合并渲染成一页人类可读的 Markdown 简报。
对标 Iran Briefing (skill.capduck.com/iran) 的输出格式。

用法:
    python3 render_briefing.py [SYNC_DIR] [OUTPUT_PATH]
    
    SYNC_DIR:    JSON 源目录（默认: ../../../../workflows/investment_agent_data/miniapp_sync）
    OUTPUT_PATH: 输出路径（默认: ../../../../touyanduck-api/api/latest/briefing.md）
"""

import json
import sys
import os
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", "..", ".."))

DEFAULT_SYNC_DIR = os.path.join(PROJECT_DIR, "workflows", "investment_agent_data", "miniapp_sync")
DEFAULT_OUTPUT = os.path.join(PROJECT_DIR, "touyanduck-api", "api", "latest", "briefing.md")


def load_json(filepath):
    """安全加载 JSON 文件"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"  ⚠️  加载 {os.path.basename(filepath)} 失败: {e}")
        return None


def sparkline_to_trend(sparkline, n=7):
    """将 sparkline 数组转换为简易趋势箭头"""
    if not sparkline or len(sparkline) < 2:
        return ""
    arr = sparkline[-n:] if len(sparkline) >= n else sparkline
    symbols = []
    for i in range(1, len(arr)):
        symbols.append("▲" if arr[i] >= arr[i - 1] else "▼")
    return "".join(symbols)


def traffic_light_emoji(status):
    """安全信号状态→emoji"""
    return {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(status, "⚪")


def direction_arrow(direction):
    """方向→箭头"""
    return {"up": "↑", "down": "↓", "flat": "→"}.get(direction, "")


def change_fmt(change):
    """格式化涨跌幅"""
    if change is None:
        return "—"
    prefix = "+" if change > 0 else ""
    return f"{prefix}{change}%"


def render(briefing, markets, watchlist, radar):
    """主渲染函数：4个JSON → 1个Markdown字符串"""
    lines = []

    # ── 标题 & 元信息 ──
    date = briefing.get("date", "")
    data_time = briefing.get("dataTime", "")
    meta = briefing.get("_meta", {})
    generated_at = meta.get("generatedAt", "")
    version = meta.get("skillVersion", "v7.2")

    lines.append(f"# 🦆 投研鸭 — 二级市场每日策略简报")
    lines.append(f"Updated: {generated_at or data_time} | 数据来源: 实时行情+聪明钱+财经媒体 | 版本: {version}")
    lines.append("")

    # ── Situation Assessment ──
    lines.append("## Situation Assessment")
    lines.append("")

    sentiment_score = briefing.get("sentimentScore", "—")
    sentiment_label = briefing.get("sentimentLabel", "")
    risk_score = radar.get("riskScore", "—") if radar else "—"
    risk_level = radar.get("riskLevel", "") if radar else ""

    lines.append(f"**情绪: {sentiment_score}/100 {sentiment_label}** | **风险评分: {risk_score}/100 {risk_level}**")
    lines.append("")

    # 红绿灯
    if radar and radar.get("trafficLights"):
        for tl in radar["trafficLights"]:
            emoji = traffic_light_emoji(tl.get("status", ""))
            lines.append(f"- {emoji} {tl['name']}: {tl['value']}（{tl.get('threshold', '')}）")
        lines.append("")

        # 统计红黄绿
        counts = {"red": 0, "yellow": 0, "green": 0}
        for tl in radar["trafficLights"]:
            s = tl.get("status", "")
            if s in counts:
                counts[s] += 1
        lines.append(f"> 红绿灯: {counts['red']}红 {counts['yellow']}黄 {counts['green']}绿 → 风险评分 {risk_score}/100 {risk_level}")
        lines.append("")

    # ── 核心结论 ──
    lines.append("## 📌 核心结论")
    lines.append("")
    lines.append(briefing.get("takeaway", ""))
    lines.append("")

    # ── 核心事件链 ──
    core_event = briefing.get("coreEvent", {})
    if core_event:
        lines.append("## 📰 核心事件链")
        lines.append("")
        lines.append(f"**{core_event.get('title', '')}**")
        lines.append("")
        for item in core_event.get("chain", []):
            source = item.get("source", "")
            url = item.get("url", "")
            source_count = item.get("source_count", 1)
            # 证据强度标记
            marker = "◆" if source_count >= 2 else "◇"
            source_link = f"[{source}]({url})" if url else source
            lines.append(f"- {marker} {item['title']} — {item.get('brief', '')} ({source_link})")
        lines.append("")
        lines.append("> Evidence: ◆ strong (≥2 sources) ◇ moderate (1 source)")
        lines.append("")

    # ── 市场数据 ──
    if markets:
        lines.append("## 📊 市场数据")
        lines.append("")

        # 美股指数
        us_markets = markets.get("usMarkets", [])
        if us_markets:
            lines.append("### 🇺🇸 美股指数")
            lines.append("| 指数 | 收盘价 | 涨跌 | 7日趋势 |")
            lines.append("|------|--------|------|---------|")
            for m in us_markets:
                trend = sparkline_to_trend(m.get("sparkline"))
                lines.append(f"| {m['name']} | {m['price']} | {change_fmt(m.get('change'))} | {trend} |")
            lines.append("")
            if markets.get("usInsight"):
                lines.append(f"> {markets['usInsight']}")
                lines.append("")

        # M7
        m7 = markets.get("m7", [])
        if m7:
            lines.append("### 🤖 M7 七巨头")
            lines.append("| 名称 | 价格 | 涨跌 | 7日趋势 |")
            lines.append("|------|------|------|---------|")
            for s in m7:
                trend = sparkline_to_trend(s.get("sparkline"))
                lines.append(f"| {s['name']} | {s['price']} | {change_fmt(s.get('change'))} | {trend} |")
            lines.append("")
            if markets.get("m7Insight"):
                lines.append(f"> {markets['m7Insight']}")
                lines.append("")

        # 亚太市场
        asia = markets.get("asiaMarkets", [])
        if asia:
            lines.append("### 🌏 亚太市场")
            lines.append("| 指数 | 收盘价 | 涨跌 |")
            lines.append("|------|--------|------|")
            for m in asia:
                lines.append(f"| {m['name']} | {m['price']} | {change_fmt(m.get('change'))} |")
            lines.append("")
            if markets.get("asiaInsight"):
                lines.append(f"> {markets['asiaInsight']}")
                lines.append("")

        # 大宗商品
        commodities = markets.get("commodities", [])
        if commodities:
            lines.append("### 🛢️ 大宗商品 & 汇率")
            lines.append("| 品种 | 价格 | 涨跌 |")
            lines.append("|------|------|------|")
            for c in commodities:
                lines.append(f"| {c['name']} | {c['price']} | {change_fmt(c.get('change'))} |")
            lines.append("")
            if markets.get("commodityInsight"):
                lines.append(f"> {markets['commodityInsight']}")
                lines.append("")

        # 加密货币
        cryptos = markets.get("cryptos", [])
        if cryptos:
            lines.append("### ₿ 加密货币")
            lines.append("| 币种 | 价格 | 涨跌 |")
            lines.append("|------|------|------|")
            for c in cryptos:
                lines.append(f"| {c['name']} | {c['price']} | {change_fmt(c.get('change'))} |")
            lines.append("")
            if markets.get("cryptoInsight"):
                lines.append(f"> {markets['cryptoInsight']}")
                lines.append("")

        # GICS 板块
        gics = markets.get("gics", [])
        if gics:
            lines.append("### 📊 GICS 11 板块")
            lines.append("| 板块 | 涨跌 | ETF |")
            lines.append("|------|------|-----|")
            for g in gics:
                emoji = "🟩" if g.get("change", 0) >= 0 else "🟥"
                lines.append(f"| {emoji} {g['name']} | {change_fmt(g.get('change'))} | {g.get('etf', '')} |")
            lines.append("")
            if markets.get("gicsInsight"):
                lines.append(f"> {markets['gicsInsight']}")
                lines.append("")

    # ── 三大核心判断 ──
    judgments = briefing.get("coreJudgments", [])
    if judgments:
        lines.append("## 🎯 三大核心判断")
        lines.append("")
        for i, j in enumerate(judgments, 1):
            lines.append(f"{i}. **{j['title']}**（置信度 {j.get('confidence', '—')}%）")
            lines.append(f"   {j.get('logic', '')}")
            refs = j.get("references", [])
            if refs:
                ref = refs[0]
                ref_url = ref.get("url", "")
                ref_name = ref.get("name", "")
                if ref_url:
                    lines.append(f"   参考: [{ref_name}]({ref_url})")
                elif ref_name:
                    lines.append(f"   参考: {ref_name}")
            lines.append("")

    # ── 行动建议 ──
    actions = briefing.get("actionHints", [])
    if actions:
        lines.append("## ⚡ 行动建议")
        lines.append("")
        for a in actions:
            lines.append(f"- **[{a.get('type', 'watch')}]** {a.get('content', '')}")
        lines.append("")

    # ── 聪明钱动向 ──
    smart_money_detail = radar.get("smartMoneyDetail", []) if radar else []
    if smart_money_detail:
        lines.append("## 💰 聪明钱动向")
        lines.append("")
        for tier_group in smart_money_detail:
            tier = tier_group.get("tier", "")
            lines.append(f"### {tier}")
            for fund in tier_group.get("funds", []):
                name = fund.get("name", "")
                action = fund.get("action", "")
                signal = fund.get("signal", "")
                signal_emoji = {"bullish": "📈", "bearish": "📉", "neutral": "➡️"}.get(signal, "")
                source = fund.get("source", "")
                url = fund.get("url", "")
                source_link = f"[{source}]({url})" if url else source
                lines.append(f"- **{name}** {signal_emoji}: {action}")
                if source_link:
                    lines.append(f"  来源: {source_link}")
            lines.append("")

    # ── 持仓快照 ──
    holdings = radar.get("smartMoneyHoldings", []) if radar else []
    if holdings:
        lines.append("## 📋 重点持仓快照")
        lines.append("")
        for h in holdings:
            manager = h.get("manager", "")
            as_of = h.get("asOf", "")
            lines.append(f"### {manager}")
            lines.append(f"*{as_of}*")
            lines.append("")
            positions = h.get("positions", [])
            if positions:
                lines.append("| 标的 | 代码 | 权重 | 变动 |")
                lines.append("|------|------|------|------|")
                for p in positions:
                    lines.append(f"| {p.get('name','')} | {p.get('symbol','')} | {p.get('weight','')} | {p.get('change','')} |")
                lines.append("")
            footnote = h.get("footnote", "")
            if footnote:
                lines.append(f"> {footnote}")
                lines.append("")

    # ── 预测市场 ──
    predictions = radar.get("predictions", []) if radar else []
    if predictions:
        lines.append("## 🔮 预测市场")
        lines.append("")
        lines.append("| 问题 | 概率 | 趋势 | 24h变化 | 来源 |")
        lines.append("|------|------|------|---------|------|")
        for p in predictions:
            trend_emoji = "↑" if p.get("trend") == "up" else "↓"
            c24 = p.get("change24h", 0)
            c24_str = f"+{c24}%" if c24 > 0 else f"{c24}%"
            lines.append(f"| {p['title']} | {p['probability']}% | {trend_emoji} | {c24_str} | {p.get('source','')} |")
        lines.append("")

    # ── 本周前瞻 ──
    events = radar.get("events", []) if radar else []
    if events:
        lines.append("## 📅 本周前瞻")
        lines.append("")
        for e in events:
            impact = e.get("impact", "")
            impact_emoji = "🔴" if impact == "high" else "🟡" if impact == "medium" else "🟢"
            source = e.get("source", "")
            url = e.get("url", "")
            source_link = f"[{source}]({url})" if url else source
            lines.append(f"- **{e.get('date', '')}** {impact_emoji} {e.get('title', '')} ({source_link})")
        lines.append("")

    # ── 异动信号 ──
    alerts = radar.get("alerts", []) if radar else []
    if alerts:
        lines.append("## ⚠️ 异动信号")
        lines.append("")
        for a in alerts:
            level = a.get("level", "info")
            level_emoji = {"danger": "🔴", "warning": "🟡", "info": "🟢"}.get(level, "ℹ️")
            source = a.get("source", "")
            url = a.get("url", "")
            source_link = f"[{source}]({url})" if url else source
            time_str = a.get("time", "")
            lines.append(f"- {level_emoji} {a.get('text', '')} ({time_str}) {source_link}")
        lines.append("")

    # ── 全球反应 ──
    global_reaction = briefing.get("globalReaction", [])
    if global_reaction:
        lines.append("## 🌍 全球反应")
        lines.append("")
        for gr in global_reaction:
            arrow = direction_arrow(gr.get("direction", ""))
            lines.append(f"- {gr['name']} {gr['value']} {arrow} {gr.get('note', '')}")
        lines.append("")

    # ── 风险提示 ──
    risk_points = briefing.get("riskPoints", [])
    if risk_points:
        lines.append("## ⚠️ 风险提示")
        lines.append("")
        for rp in risk_points:
            lines.append(f"- {rp}")
        lines.append("")

    # ── 关于 & 板块概览（来自 watchlist） ──
    if watchlist:
        sectors = watchlist.get("sectors", [])
        if sectors:
            lines.append("## 📁 板块概览")
            lines.append("")
            for s in sectors:
                trend_map = {"up": "📈上行", "down": "📉下行", "hold": "➡️横盘"}
                trend_label = trend_map.get(s.get("trend", ""), s.get("trend", ""))
                lines.append(f"### {s['name']} — {trend_label}")
                lines.append(f"{s.get('summary', '')}")
                lines.append("")

    # ── 市场要点（marketSummaryPoints） ──
    summary_points = briefing.get("marketSummaryPoints", [])
    if summary_points:
        lines.append("## 📝 市场要点")
        lines.append("")
        for sp in summary_points:
            lines.append(f"- {sp}")
        lines.append("")

    # ── AI 交互引导（动态生成，放在页脚前） ──
    lines.append("---")
    lines.append("## 🧭 你可以继续问我")
    lines.append("")
    lines.append("根据今日简报，以下是高价值的追问方向：")
    lines.append("")

    guide_items = []

    # 从核心判断提取追问
    if judgments:
        for j in judgments[:2]:
            title = j.get("title", "")
            confidence = j.get("confidence", 0)
            if title:
                # 高置信度判断 → 建议追问逻辑
                if confidence >= 75:
                    guide_items.append(f"「**{title}**」——逻辑链是什么？如何应对？")
                else:
                    guide_items.append(f"「**{title}**」——这个判断成立的前提条件是什么？")

    # 从行动建议提取追问
    if actions:
        for a in actions[:1]:
            content = a.get("content", "")
            atype = a.get("type", "")
            if content and atype == "watch":
                # 截取前20字作为问题引导
                short = content[:25] + "..." if len(content) > 25 else content
                guide_items.append(f"「**关注点追问**」——{short}，后续如何？")

    # 从预测市场提取追问
    if predictions:
        for p in predictions[:1]:
            prob = p.get("probability", 0)
            title_p = p.get("title", "")
            if title_p:
                guide_items.append(f"「**{title_p}**」——{prob}% 概率，背后的逻辑和关键变量是什么？")

    # 从聪明钱提取追问
    if smart_money_detail:
        for tier_group in smart_money_detail[:1]:
            funds = tier_group.get("funds", [])
            if funds:
                fund_names = "、".join([f.get("name", "") for f in funds[:2] if f.get("name")])
                if fund_names:
                    guide_items.append(f"「**{fund_names} 在做什么**」——最新仓位和信号含义？")

    # 从前瞻事件提取追问
    if events:
        high_impact = [e for e in events if e.get("impact") == "high"]
        if high_impact:
            e = high_impact[0]
            date_str = e.get("date", "")
            title_e = e.get("title", "")
            if title_e:
                short_e = title_e[:20] + "..." if len(title_e) > 20 else title_e
                guide_items.append(f"「**{date_str} {short_e}**」——预期影响和应对策略？")

    # 固定引导项（保底）
    guide_items.append("「**今天整体适合买入还是观望？**」——综合风险评分和行动建议")

    # 输出（最多5条）
    for i, item in enumerate(guide_items[:5], 1):
        lines.append(f"{i}. {item}")

    lines.append("")
    lines.append("> 💡 直接把上面任意一句发给我，我从简报中展开分析。")
    lines.append("")

    # ── 页脚 ──
    lines.append("---")
    lines.append(f"🦆 投研鸭 {version} | 九大铁律+29条零容忍+17项FATAL门禁 | 每工作日更新")
    lines.append(f"📱 微信小程序: 搜索「投研鸭」 | ⚠️ 仅供参考，不构成投资建议")
    lines.append("")

    return "\n".join(lines)


def main():
    sync_dir = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SYNC_DIR
    output_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT

    print(f"📝 render_briefing.py — JSON → Markdown 渲染")
    print(f"   源目录: {sync_dir}")
    print(f"   输出: {output_path}")
    print("")

    # 加载 4 个 JSON
    briefing = load_json(os.path.join(sync_dir, "briefing.json"))
    markets = load_json(os.path.join(sync_dir, "markets.json"))
    watchlist = load_json(os.path.join(sync_dir, "watchlist.json"))
    radar = load_json(os.path.join(sync_dir, "radar.json"))

    if not briefing:
        print("❌ briefing.json 加载失败，无法渲染。")
        sys.exit(1)

    # 渲染
    md_content = render(briefing, markets, watchlist, radar)

    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # 写入
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    file_size = os.path.getsize(output_path)
    print(f"  ✅ briefing.md 渲染完成 ({file_size:,} bytes)")
    print(f"     输出路径: {output_path}")


if __name__ == "__main__":
    main()
