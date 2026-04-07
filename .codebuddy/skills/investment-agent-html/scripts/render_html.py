#!/usr/bin/env python3
"""
投研鸭 HTML 报告渲染器 v1.0

读取 4 个 JSON 文件（briefing/markets/watchlist/radar）→ 渲染成单个自包含 HTML 文件。
零外部依赖（不需要微信云数据库、不需要 API Key），双击打开即可查看。

用法：
  python3 render_html.py <json_dir> <date>
  python3 render_html.py /path/to/miniapp_sync/ 2026-04-07

输出：
  <json_dir>/touyanduck-<date>.html
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─────────────────────────────────────────────────────────────────
# 路径配置
# ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
TEMPLATE_PATH = SCRIPT_DIR.parent / "templates" / "report.html"


# ─────────────────────────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────────────────────────

def load_json(filepath: Path) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def escape_html(text: str) -> str:
    """转义 HTML 特殊字符"""
    if not text:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def parse_takeaway(text: str) -> str:
    """将 takeaway 中的【xxx】转为红色高亮 span"""
    if not text:
        return ""
    escaped = escape_html(text)
    # 替换 【xxx】 为红色高亮
    result = re.sub(
        r"【([^】]+)】",
        r'<span class="takeaway-hl">【\1】</span>',
        escaped,
    )
    return result


def change_color_class(change: float) -> str:
    """根据涨跌幅返回颜色类名"""
    if change > 0:
        return "color-up"
    elif change < 0:
        return "color-down"
    return "color-flat"


def format_change(change: float) -> str:
    """格式化涨跌幅"""
    if change > 0:
        return f"+{change:.2f}%"
    return f"{change:.2f}%"


def direction_class(direction: str) -> str:
    """direction → CSS class"""
    return f"color-{direction}" if direction in ("up", "down", "flat") else "color-flat"


def signal_class(signal: str) -> str:
    """signal → CSS class"""
    return f"sm-{signal}" if signal in ("bullish", "bearish", "neutral") else "sm-neutral"


def tl_class(status: str) -> str:
    """trafficLight status → CSS class"""
    return f"tl-{status}" if status in ("green", "yellow", "red") else "tl-green"


def impact_tag(impact: str) -> str:
    """impact → tag HTML"""
    cls_map = {"high": "tag-red", "medium": "tag-yellow", "low": "tag-gray"}
    label_map = {"high": "高影响", "medium": "中影响", "low": "低影响"}
    cls = cls_map.get(impact, "tag-gray")
    label = label_map.get(impact, impact)
    return f'<span class="tag {cls}">{label}</span>'


def alert_bg_class(level: str) -> str:
    """alert level → bg class"""
    return f"alert-{level}" if level in ("danger", "warning", "info") else "alert-info"


def alert_icon(level: str) -> str:
    """alert level → emoji icon"""
    icons = {"danger": "🔴", "warning": "🟡", "info": "🟢"}
    return icons.get(level, "ℹ️")


def badge_class(badge_text: str) -> str:
    """badge 文本 → CSS 类"""
    if "巴菲特" in badge_text:
        return "badge-buffett"
    elif "段永平" in badge_text:
        return "badge-duan"
    elif "未上市" in badge_text:
        return "badge-unlisted"
    return "badge-default"


def action_type_tag(action_type: str) -> str:
    """actionHints type → tag HTML"""
    type_map = {
        "hold": ("持有", "tag-blue"),
        "add": ("加仓", "tag-red"),
        "reduce": ("减仓", "tag-green"),
        "buy": ("买入", "tag-red"),
        "sell": ("卖出", "tag-green"),
        "watch": ("关注", "tag-yellow"),
        "hedge": ("对冲", "tag-orange"),
        "stoploss": ("止损", "tag-red"),
    }
    label, cls = type_map.get(action_type, (action_type, "tag-gray"))
    return f'<span class="tag {cls}">{label}</span>'


def render_sparkline_svg(data: List[float], width: int = 80, height: int = 30, is_up: bool = True) -> str:
    """用 SVG polyline 渲染 sparkline 迷你走势图"""
    if not data or len(data) < 2:
        return '<svg class="sparkline-svg" width="{}" height="{}"></svg>'.format(width, height)

    padding = 2
    min_val = min(data)
    max_val = max(data)
    val_range = max_val - min_val
    if val_range == 0:
        val_range = 1

    step_x = (width - 2 * padding) / (len(data) - 1)
    points = []
    for i, val in enumerate(data):
        x = padding + i * step_x
        y = padding + (1 - (val - min_val) / val_range) * (height - 2 * padding)
        points.append(f"{x:.1f},{y:.1f}")

    points_str = " ".join(points)
    color = "#e74c3c" if is_up else "#27ae60"
    fill_color = "rgba(231,76,60,0.1)" if is_up else "rgba(39,174,96,0.1)"

    # 构建填充区域
    last_point = points[-1]
    first_point = points[0]
    fill_points = (
        points_str
        + f" {padding + (len(data)-1) * step_x:.1f},{height - padding}"
        + f" {padding:.1f},{height - padding}"
    )

    svg = f'''<svg class="sparkline-svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <polygon points="{fill_points}" fill="{fill_color}" />
  <polyline points="{points_str}" fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round" />
  <circle cx="{padding + (len(data)-1) * step_x:.1f}" cy="{padding + (1 - (data[-1] - min_val) / val_range) * (height - 2 * padding):.1f}" r="2" fill="{color}" />
</svg>'''
    return svg


# ─────────────────────────────────────────────────────────────────
# 页面渲染函数
# ─────────────────────────────────────────────────────────────────

def render_briefing(b: dict) -> str:
    """渲染简报页 HTML"""
    parts = []

    # 时间状态栏
    ts = b.get("timeStatus")
    if ts:
        ms = ts.get("marketStatus", "")
        ms_class = "ts-market-open" if "交易中" in ms else "ts-market-closed"
        parts.append(f'''<div class="ts-bar">
  <div class="ts-item"><div class="ts-time">{escape_html(ts.get("bjt","--"))}</div><div class="ts-label">北京时间</div></div>
  <div class="ts-divider"></div>
  <div class="ts-item"><div class="ts-time">{escape_html(ts.get("est","--"))}</div><div class="ts-label">美东时间 <span class="ts-market-tag {ms_class}">{escape_html(ms)}</span></div></div>
  <div class="ts-divider"></div>
  <div class="ts-item"><div class="ts-time">{escape_html(ts.get("refreshInterval","每日更新"))}</div><div class="ts-label">数据更新</div></div>
</div>''')

    # 今日结论 + 重点事件
    parts.append('<div class="card">')
    takeaway = b.get("takeaway", "")
    if takeaway:
        parts.append(f'<div class="card-title">📌 今日结论</div>')
        parts.append(f'<div class="takeaway-text">{parse_takeaway(takeaway)}</div>')

    ce = b.get("coreEvent")
    if ce and ce.get("chain"):
        parts.append('<div style="height:1px;background:linear-gradient(90deg,transparent,#f0f0f0 15%,#f0f0f0 85%,transparent);margin:12px 0"></div>')
        parts.append(f'<div class="card-title">🚨 重点事件</div>')
        for item in ce["chain"]:
            source_html = ""
            if item.get("url"):
                source_html = f'<div class="chain-source">📎 <a href="{escape_html(item["url"])}" target="_blank">{escape_html(item.get("source","原文"))}</a> ↗</div>'
            elif item.get("source"):
                source_html = f'<div class="chain-source" style="color:#bbb">📎 {escape_html(item["source"])}</div>'
            parts.append(f'''<div class="chain-item">
  <div class="chain-dot"></div>
  <div class="chain-body">
    <span class="chain-title">{escape_html(item.get("title",""))}</span>
    <span class="chain-brief">{escape_html(item.get("brief",""))}</span>
    {source_html}
  </div>
</div>''')
    parts.append('</div>')

    # 全球资产反应
    gr = b.get("globalReaction", [])
    if gr:
        parts.append('<div class="card">')
        parts.append('<div class="card-title">📊 全球资产反应</div>')
        parts.append('<div class="reaction-grid">')
        for item in gr:
            d = item.get("direction", "flat")
            parts.append(f'''<div class="reaction-item">
  <div class="reaction-name">{escape_html(item.get("name",""))}</div>
  <div class="reaction-value {direction_class(d)}">{escape_html(item.get("value",""))}</div>
  <div class="reaction-note">{escape_html(item.get("note",""))}</div>
</div>''')
        parts.append('</div></div>')

    # 聪明钱建议
    parts.append(_render_section("⚡ 聪明钱建议", _render_smart_money_section(b), expanded=True))

    # 风险情绪
    parts.append(_render_section("🛡️ 风险情绪", _render_risk_sentiment(b), expanded=True, extra_class="risk-sent-card"))

    # 核心判断
    parts.append(_render_section("🎯 核心判断", _render_core_judgments(b), expanded=True))

    # 数据更新时间
    dt = b.get("dataTime", "")
    if dt:
        parts.append(f'<div class="data-footer">更新时间 · {escape_html(dt)}</div>')

    return "\n".join(parts)


def _render_smart_money_section(b: dict) -> str:
    """渲染聪明钱建议模块内容"""
    parts = []

    # actionHints
    hints = b.get("actionHints", [])
    for h in hints:
        parts.append(f'''<div class="action-hint-item">
  {action_type_tag(h.get("type","watch"))}
  <div class="action-body">
    <div class="action-content">{escape_html(h.get("content",""))}</div>
    <div class="action-reason">{escape_html(h.get("reason",""))}</div>
  </div>
</div>''')

    # 聪明钱动向
    sm = b.get("smartMoney", [])
    if sm:
        if hints:
            parts.append('<div class="sm-section-title">🧠 聪明钱动向</div>')
        for item in sm:
            parts.append(f'''<div class="smart-money-item">
  <div class="sm-left">
    <div class="sm-signal {signal_class(item.get("signal","neutral"))}"></div>
    <div class="sm-source">{escape_html(item.get("source",""))}</div>
  </div>
  <div class="sm-action">{escape_html(item.get("action",""))}</div>
</div>''')

    # 持仓参考
    th = b.get("topHoldings", [])
    if th:
        parts.append('<div class="holdings-title">📋 持仓参考</div>')
        for item in th:
            parts.append(f'''<div class="holdings-item">
  <div class="holdings-name">{escape_html(item.get("name",""))}</div>
  <div class="holdings-detail">{escape_html(item.get("holdings",""))}</div>
</div>''')

    return "\n".join(parts)


def _render_risk_sentiment(b: dict) -> str:
    """渲染风险情绪模块"""
    parts = []
    score = b.get("sentimentScore", 50)
    label = b.get("sentimentLabel", "中性")

    parts.append(f'''<div class="sentiment-bar">
  <div class="sentiment-label-text">恐惧</div>
  <div class="sentiment-track">
    <div class="sentiment-fill" style="width:{score}%"></div>
    <div class="sentiment-pointer" style="left:{score}%"><div class="sentiment-pointer-dot"></div></div>
  </div>
  <div class="sentiment-label-text">贪婪</div>
</div>
<div class="sentiment-info">
  <span class="sentiment-number">{score}</span>
  <span class="sentiment-tag">{escape_html(label)}</span>
</div>''')

    rp = b.get("riskPoints", [])
    if rp:
        parts.append('<div class="risk-list">')
        for r in rp:
            parts.append(f'<div class="risk-item"><span class="risk-dot">•</span><span class="risk-item-text">{escape_html(r)}</span></div>')
        parts.append('</div>')
    elif b.get("riskNote"):
        parts.append(f'<div style="font-size:12px;color:#666;line-height:1.7;margin-top:12px">{escape_html(b["riskNote"])}</div>')

    return "\n".join(parts)


def _render_core_judgments(b: dict) -> str:
    """渲染核心判断模块"""
    parts = []
    cj = b.get("coreJudgments", [])
    for i, item in enumerate(cj):
        conf = item.get("confidence", 50)
        refs_html = ""
        refs = item.get("references", [])
        if refs:
            ref_parts = []
            for ref in refs:
                if isinstance(ref, str):
                    ref_parts.append(f'<span style="color:#2980b9">{escape_html(ref)}</span>')
                elif isinstance(ref, dict):
                    name = ref.get("name", "")
                    summary = ref.get("summary", "")
                    url = ref.get("url", "")
                    if url:
                        ref_parts.append(f'<div style="margin-top:4px"><span style="color:#1a1a2e;font-weight:600">{escape_html(name)}</span> <span style="color:#888">{escape_html(summary)}</span> <a href="{escape_html(url)}" target="_blank" style="color:#2980b9;font-size:10px">↗</a></div>')
                    else:
                        ref_parts.append(f'<div style="margin-top:4px"><span style="color:#1a1a2e;font-weight:600">{escape_html(name)}</span> <span style="color:#888">{escape_html(summary)}</span></div>')
            if ref_parts:
                refs_html = '<div class="jx-ref">📎 ' + "".join(ref_parts) + '</div>'

        # 概率+趋势标签
        tags_html = ""
        prob = item.get("probability", "")
        trend = item.get("trend", "")
        if prob or trend:
            tag_parts = []
            if prob:
                prob_cls = {"高可能性": "tag-blue", "中可能性": "tag-yellow", "低可能性": "tag-gray"}.get(prob, "tag-gray")
                tag_parts.append(f'<span class="tag {prob_cls}">{escape_html(prob)}</span>')
            if trend:
                trend_cls = {"上升": "tag-green", "下降": "tag-red", "稳定": "tag-gray"}.get(trend, "tag-gray")
                trend_arrow = {"上升": "↑", "下降": "↓", "稳定": "→"}.get(trend, "")
                tag_parts.append(f'<span class="tag {trend_cls}">{trend_arrow} {escape_html(trend)}</span>')
            tags_html = '<div class="jx-tags">' + "".join(tag_parts) + '</div>'

        parts.append(f'''<div class="judgment-item">
  <div class="judgment-header">
    <div class="judgment-num">{i+1}</div>
    <div class="judgment-title">{escape_html(item.get("title",""))}</div>
  </div>
  <div class="confidence-row">
    <div class="confidence-label">置信度</div>
    <div class="confidence-bar"><div class="confidence-fill" style="width:{conf}%"></div></div>
    <div class="confidence-value">{conf}%</div>
  </div>
  <div class="logic-text">{escape_html(item.get("logic",""))}</div>
  {tags_html}
  {refs_html}
</div>''')

    return "\n".join(parts)


def _render_section(title: str, content: str, expanded: bool = True, extra_class: str = "") -> str:
    """渲染通用 section-card"""
    cls = extra_class
    arrow_cls = "open" if expanded else ""
    body_cls = "" if expanded else "collapsed"
    if expanded:
        body_style = ""
    else:
        body_style = 'style="max-height:0;opacity:0;padding:0 16px 0"'
    return f'''<div class="section-card {cls}">
  <div class="section-header" onclick="toggleSection(this)">
    <span class="section-title">{title}</span>
    <span class="section-arrow {arrow_cls}">▾</span>
  </div>
  <div class="section-body {body_cls}" {body_style}>
    {content}
  </div>
</div>'''


def render_markets(m: dict) -> str:
    """渲染市场页 HTML"""
    parts = []

    # 子 Tab 栏
    tabs = [
        ("us", "美股"),
        ("m7", "M7"),
        ("asia", "亚太"),
        ("commodity", "大宗"),
        ("crypto", "加密"),
    ]
    parts.append('<div class="card" style="padding:0;overflow:hidden">')
    parts.append('<div class="market-tabs">')
    for i, (tid, label) in enumerate(tabs):
        active = " active" if i == 0 else ""
        parts.append(f'<div class="market-tab{active}" data-tab="{tid}" onclick="switchMarketTab(\'{tid}\')">{label}</div>')
    parts.append('</div>')

    # 美股 Tab
    parts.append(_render_market_panel("us", m.get("usInsight", ""), m.get("usMarkets", []), active=True))
    # M7 Tab
    parts.append(_render_market_panel("m7", m.get("m7Insight", ""), m.get("m7", []), header="🏆 Magnificent Seven"))
    # 亚太 Tab
    parts.append(_render_market_panel("asia", m.get("asiaInsight", ""), m.get("asiaMarkets", [])))
    # 大宗 Tab
    parts.append(_render_market_panel("commodity", m.get("commodityInsight", ""), m.get("commodities", [])))
    # 加密 Tab
    parts.append(_render_market_panel("crypto", m.get("cryptoInsight", ""), m.get("cryptos", [])))

    parts.append('</div>')  # end card

    # GICS 热力图
    gics = m.get("gics", [])
    if gics:
        gics_insight = m.get("gicsInsight", "")
        parts.append('<div class="card">')
        parts.append('<div class="gics-title">GICS 板块热力图</div>')
        if gics_insight:
            parts.append(f'<div class="market-summary" style="margin-bottom:10px">{escape_html(gics_insight)}</div>')
        max_abs = max(abs(g.get("change", 0)) for g in gics) if gics else 1
        if max_abs == 0:
            max_abs = 1
        for g in gics:
            ch = g.get("change", 0)
            bar_pct = min(abs(ch) / max_abs * 100, 100)
            bar_cls = "bar-up" if ch >= 0 else "bar-down"
            color_cls = "color-up" if ch >= 0 else "color-down"
            parts.append(f'''<div class="gics-item">
  <div class="gics-name">{escape_html(g.get("name",""))}</div>
  <div class="gics-bar"><div class="gics-bar-fill {bar_cls}" style="width:{bar_pct:.0f}%"></div></div>
  <div class="gics-change {color_cls}">{format_change(ch)}</div>
</div>''')
        parts.append('</div>')

    # 数据更新时间
    dt = m.get("date", "")
    if dt:
        parts.append(f'<div class="data-footer">数据日期 · {escape_html(dt)}</div>')

    return "\n".join(parts)


def _render_market_panel(tab_id: str, insight: str, items: list, active: bool = False, header: str = "") -> str:
    """渲染市场页子面板"""
    cls = " active" if active else ""
    parts = [f'<div class="market-panel{cls}" id="mp-{tab_id}">']
    if insight:
        parts.append(f'<div class="market-summary">{escape_html(insight)}</div>')
    if header:
        parts.append(f'<div style="padding:12px 16px 4px;font-size:15px;font-weight:700;color:#1a1a2e">{header}</div>')
    if items:
        parts.append('<div class="market-list">')
        for item in items:
            ch = item.get("change", 0)
            is_up = ch >= 0
            sparkline = item.get("sparkline", [])
            svg = render_sparkline_svg(sparkline, 80, 30, is_up)
            color_cls = change_color_class(ch)
            label = item.get("changeLabel", "")
            label_html = f'<div class="ml-label">{escape_html(label)}</div>' if label else ""
            parts.append(f'''<div class="market-list-item">
  <div class="ml-left">
    <div class="ml-name">{escape_html(item.get("name",""))}</div>
    <div class="ml-price">{escape_html(item.get("price",""))}</div>
  </div>
  <div class="ml-center">{svg}</div>
  <div class="ml-right">
    <div class="ml-change {color_cls}">{format_change(ch)}</div>
    {label_html}
  </div>
</div>''')
        parts.append('</div>')
    else:
        parts.append('<div class="empty-state"><div class="empty-icon">🦆</div>暂无数据</div>')
    parts.append('</div>')
    return "\n".join(parts)


def render_watchlist(w: dict) -> str:
    """渲染标的页 HTML"""
    parts = []
    sectors = w.get("sectors", [])
    stocks = w.get("stocks", {})

    # 板块 Tab
    parts.append('<div class="sector-tabs">')
    for i, s in enumerate(sectors):
        active = " active" if i == 0 else ""
        trend_label = {"up": "↑ 看涨", "down": "↓ 看跌", "hold": "→ 持平"}.get(s.get("trend", "hold"), "→ 持平")
        parts.append(f'<div class="sector-tab{active}" data-id="{s["id"]}" onclick="switchSector(\'{s["id"]}\')">{escape_html(s.get("name",""))}</div>')
    parts.append('</div>')

    # 板块概览 + 股票列表
    for i, s in enumerate(sectors):
        sid = s["id"]
        active = " active" if i == 0 else ""
        trend = s.get("trend", "hold")
        trend_label = {"up": "↑ 看涨", "down": "↓ 看跌", "hold": "→ 持平"}.get(trend, "→ 持平")
        trend_cls = {"up": "tag-red", "down": "tag-green", "hold": "tag-yellow"}.get(trend, "tag-yellow")
        sector_stocks = stocks.get(sid, [])

        parts.append(f'''<div class="sector-overview{active}" id="so-{sid}">
  <div class="sector-title-text">{escape_html(s.get("name",""))} <span class="tag {trend_cls}">{trend_label}</span></div>
  <div class="sector-desc">{escape_html(s.get("summary",""))}</div>
  <div class="sector-count">共 {len(sector_stocks)} 只标的 · 点击卡片展开详情</div>
</div>''')

        display = "block" if i == 0 else "none"
        parts.append(f'<div class="stock-card-group" id="sg-{sid}" style="display:{display}">')
        for stock in sector_stocks:
            parts.append(_render_stock_card(stock))
        if not sector_stocks:
            parts.append('<div class="empty-state"><div class="empty-icon">🦆</div>暂无该板块的标的数据</div>')
        parts.append('</div>')

    # 数据更新时间
    dt = w.get("dataTime", "")
    if dt:
        parts.append(f'<div class="data-footer">更新时间 · {escape_html(dt)}</div>')

    return "\n".join(parts)


def _render_stock_card(stock: dict) -> str:
    """渲染单个 stock-card"""
    is_unlisted = not stock.get("listed", True)
    unlisted_cls = " unlisted" if is_unlisted else ""
    ch = stock.get("change", 0)
    is_up = ch >= 0
    color_cls = change_color_class(ch)
    sparkline = stock.get("sparkline", [])
    chart_data = stock.get("chartData", [])

    # 头部
    price_html = f'<span class="sc-price">{escape_html(stock.get("price",""))}</span>' if not is_unlisted else '<span class="sc-unlisted-label">未上市</span>'
    spark_html = render_sparkline_svg(sparkline, 70, 24, is_up) if not is_unlisted and sparkline else ""
    change_html = f'<div class="sc-change {color_cls}">{format_change(ch)}</div>' if not is_unlisted else ""

    # badges
    badges = stock.get("badges", [])
    badges_html = ""
    if badges:
        badges_html = '<div class="sc-badges">' + "".join(f'<span class="badge {badge_class(b)}">{escape_html(b)}</span>' for b in badges) + '</div>'

    # tags
    tags = stock.get("tags", [])
    tags_html = ""
    if tags:
        tags_html = '<div class="sc-tags">' + "".join(f'<span class="tag tag-yellow">{escape_html(t)}</span>' for t in tags) + '</div>'

    # reason
    reason = stock.get("reason", "")
    reason_html = f'<div class="sc-reason">{escape_html(reason)}</div>' if reason else ""

    # 展开态：30日走势
    chart_html = ""
    if not is_unlisted and chart_data:
        chart_svg = render_sparkline_svg(chart_data, 400, 100, is_up)
        chart_html = f'<div class="sc-chart-large"><div class="sc-chart-large-title">30日走势</div>{chart_svg}</div>'

    # 展开态：metrics
    metrics = stock.get("metrics", [])
    metrics_html = ""
    if not is_unlisted and metrics:
        metrics_html = '<div class="sc-metrics-title">关键指标</div><div class="sc-metrics-grid">'
        for met in metrics:
            val = met.get("value", "")
            mc = ""
            if isinstance(val, str) and ("+" in val or (val.replace(".", "").replace("%", "").replace("-", "").isdigit())):
                if val.startswith("+"):
                    mc = " color-up"
                elif val.startswith("-"):
                    mc = " color-down"
            metrics_html += f'<div class="sc-metric-item"><div class="sc-metric-label">{escape_html(met.get("label",""))}</div><div class="sc-metric-value{mc}">{escape_html(val)}</div></div>'
        metrics_html += '</div>'

    # 展开态：analysis
    analysis = stock.get("analysis", "")
    analysis_html = f'<div class="sc-analysis">{escape_html(analysis)}</div>' if analysis else ""

    # 展开态：risks
    risks = stock.get("risks", [])
    risks_html = ""
    if risks:
        risks_html = '<div class="sc-risks"><div class="sc-risks-title">⚠️ 风险提示</div>'
        for r in risks:
            risks_html += f'<div class="sc-risk-item"><div class="sc-risk-dot"></div><span class="sc-risk-text">{escape_html(r)}</span></div>'
        risks_html += '</div>'

    return f'''<div class="stock-card{unlisted_cls}" onclick="toggleStock(this)">
  <div class="sc-header">
    <div class="sc-name-area">
      <div class="sc-name">{escape_html(stock.get("name",""))}</div>
      <div class="sc-symbol-price"><span class="sc-symbol">{escape_html(stock.get("symbol",""))}</span>{price_html}</div>
    </div>
    <div class="sc-chart-area">{spark_html}</div>
    <div class="sc-right">{change_html}<div class="sc-expand-hint">﹀</div></div>
  </div>
  {badges_html}
  {reason_html}
  {tags_html}
  <div class="sc-detail">
    {chart_html}
    {metrics_html}
    {analysis_html}
    {risks_html}
  </div>
</div>'''


def render_radar(r: dict) -> str:
    """渲染雷达页 HTML"""
    parts = []

    # 聪明钱动向
    smd = r.get("smartMoneyDetail", [])
    if smd:
        sm_content = ""
        for tier in smd:
            for fund in tier.get("funds", []):
                is_t1 = tier.get("tier", "") == "T1旗舰"
                tier_badge = '<span class="sm-tier-badge">旗舰</span>' if is_t1 else ""
                source_html = ""
                if fund.get("url"):
                    source_html = f'<span class="source-link"><a href="{escape_html(fund["url"])}" target="_blank">{escape_html(fund.get("source",""))}</a> ›</span>'
                elif fund.get("source"):
                    source_html = f'<span class="source-link">{escape_html(fund["source"])}</span>'
                sm_content += f'''<div class="sm-flat-item">
  <div class="sm-flat-header">
    <div class="sm-flat-left">
      <div class="sm-signal {signal_class(fund.get("signal","neutral"))}"></div>
      <span class="sm-flat-name">{escape_html(fund.get("name",""))}</span>
      {tier_badge}
    </div>
    {source_html}
  </div>
  <div class="sm-flat-action">{escape_html(fund.get("action",""))}</div>
</div>'''
        parts.append(_render_section("🧠 聪明钱动向", sm_content, expanded=True))

    # 聪明钱持仓
    smh = r.get("smartMoneyHoldings", [])
    if smh:
        h_content = ""
        for h in smh:
            positions_html = ""
            for pi, pos in enumerate(h.get("positions", []), 1):
                change_tag = f'<span class="holdings-change-tag">{escape_html(pos.get("change",""))}</span>' if pos.get("change") else ""
                positions_html += f'''<div class="holdings-row">
  <div style="display:flex;align-items:center;gap:6px;flex:1">
    <span class="holdings-rank">{pi}</span>
    <div class="holdings-stock-info"><span class="holdings-stock-name">{escape_html(pos.get("name",""))}</span><span class="holdings-stock-symbol">{escape_html(pos.get("symbol",""))}</span></div>
  </div>
  <div style="display:flex;align-items:center"><span class="holdings-weight">{escape_html(pos.get("weight",""))}</span>{change_tag}</div>
</div>'''
            footnote = f'<div class="holdings-footnote">{escape_html(h.get("footnote",""))}</div>' if h.get("footnote") else ""
            h_content += f'''<div class="holdings-group">
  <div class="holdings-group-header" onclick="toggleHoldings(this)">
    <div><span class="holdings-manager">{escape_html(h.get("manager",""))}</span><span class="holdings-aum">{escape_html(h.get("aum",""))}</span></div>
    <div><span class="holdings-date">{escape_html(h.get("asOf",""))}</span><span class="holdings-arrow">▲</span></div>
  </div>
  <div class="holdings-body open" style="max-height:1000px;opacity:1">{positions_html}{footnote}</div>
</div>'''
        parts.append(_render_section("💼 聪明钱持仓", h_content, expanded=True))

    # 风险判断
    risk_content = ""
    ra = r.get("riskAdvice", "")
    if ra:
        risk_content += f'<div class="risk-verdict"><div class="risk-verdict-text">{escape_html(ra)}</div></div>'
    tl = r.get("trafficLights", [])
    if tl:
        risk_content += '<div class="traffic-lights">'
        for light in tl:
            status = light.get("status", "green")
            risk_content += f'''<div class="tl-item">
  <div class="tl-dot {tl_class(status)}"></div>
  <div class="tl-name">{escape_html(light.get("name",""))}</div>
  <div class="tl-value">{escape_html(light.get("value",""))}</div>
  <div class="tl-threshold">{escape_html(light.get("threshold",""))}</div>
</div>'''
        risk_content += '</div>'
    parts.append(_render_section("🛡️ 风险判断", risk_content, expanded=True))

    # 本周前瞻
    events = r.get("events", [])
    if events:
        ev_content = ""
        for i, ev in enumerate(events):
            line_html = f'<div class="wa-line"></div>' if i < len(events) - 1 else ""
            ev_content += f'''<div class="wa-item">
  <div class="wa-left">
    <div class="wa-date-badge wa-badge-event"><div class="wa-date-text">{escape_html(ev.get("date",""))}</div></div>
    {line_html}
  </div>
  <div class="wa-right">
    <div class="wa-title-text">{escape_html(ev.get("title",""))}</div>
    <div class="wa-impact">{impact_tag(ev.get("impact","medium"))}</div>
  </div>
</div>'''
        parts.append(_render_section("📅 本周前瞻", ev_content, expanded=True))

    # 市场预测
    preds = r.get("predictions", [])
    if preds:
        pm_content = ""
        for p in preds:
            prob = p.get("probability", 0)
            ch24 = p.get("change24h", 0)
            trend = p.get("trend", "stable")
            trend_cls = {"up": "color-up", "down": "color-down", "stable": "color-flat"}.get(trend, "color-flat")
            trend_arrow = {"up": "↑", "down": "↓", "stable": "→"}.get(trend, "→")
            ch_label = f"+{ch24}" if ch24 > 0 else str(ch24)
            pm_content += f'''<div class="pm-item">
  <div class="pm-header">
    <div class="pm-title">{escape_html(p.get("title",""))}</div>
    <div class="pm-source">{escape_html(p.get("source",""))}</div>
  </div>
  <div class="pm-bar-row">
    <div class="pm-bar-track"><div class="pm-bar-fill" style="width:{prob}%"></div></div>
    <div class="pm-probability">{prob}%</div>
  </div>
  <div class="pm-change {trend_cls}">{trend_arrow} 24h {ch_label}</div>
</div>'''
        parts.append(_render_section("📊 市场预测", pm_content, expanded=True))

    # 异动信号
    alerts = r.get("alerts", [])
    if alerts:
        al_content = ""
        for a in alerts:
            lvl = a.get("level", "info")
            source_html = ""
            if a.get("url"):
                source_html = f'<div class="source-link" style="margin-top:4px"><a href="{escape_html(a["url"])}" target="_blank">{escape_html(a.get("source",""))}</a> ›</div>'
            elif a.get("source"):
                source_html = f'<div class="source-link" style="margin-top:4px">{escape_html(a["source"])}</div>'
            al_content += f'''<div class="alert-item {alert_bg_class(lvl)}">
  <div class="alert-top-row"><div class="alert-icon">{alert_icon(lvl)}</div><div class="alert-time">{escape_html(a.get("time",""))}</div></div>
  <div class="alert-text">{escape_html(a.get("text",""))}</div>
  {source_html}
</div>'''
        parts.append(_render_section("⚡ 异动信号", al_content, expanded=True))

    # 数据更新时间
    dt = r.get("dataTime", "")
    if dt:
        parts.append(f'<div class="data-footer">更新时间 · {escape_html(dt)}</div>')

    return "\n".join(parts)


# ─────────────────────────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 3:
        print("用法: python3 render_html.py <json_dir> <date>")
        print("示例: python3 render_html.py ./miniapp_sync/ 2026-04-07")
        sys.exit(1)

    data_dir = Path(sys.argv[1])
    date_str = sys.argv[2]

    print()
    print("=" * 60)
    print("🦆 投研鸭 HTML 报告渲染器 v1.0")
    print("=" * 60)
    print()

    # 加载 4 个 JSON
    print("[1/4] 加载 JSON 文件...")
    briefing = load_json(data_dir / "briefing.json")
    markets = load_json(data_dir / "markets.json")
    watchlist = load_json(data_dir / "watchlist.json")
    radar = load_json(data_dir / "radar.json")
    print("  ✅ 4 个 JSON 加载成功")

    # 渲染各页面
    print("[2/4] 渲染 4 个 Tab 页面...")
    briefing_html = render_briefing(briefing)
    markets_html = render_markets(markets)
    watchlist_html = render_watchlist(watchlist)
    radar_html = render_radar(radar)
    print("  ✅ 简报页 / 市场页 / 标的页 / 雷达页 渲染完成")

    # 加载模板
    print("[3/4] 加载 HTML 模板...")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        template = f.read()
    print(f"  ✅ 模板加载成功 ({TEMPLATE_PATH.name})")

    # 注入内容
    print("[4/4] 注入内容并输出...")
    html = template.replace("{{DATE}}", date_str)
    html = html.replace("{{BRIEFING_CONTENT}}", briefing_html)
    html = html.replace("{{MARKETS_CONTENT}}", markets_html)
    html = html.replace("{{WATCHLIST_CONTENT}}", watchlist_html)
    html = html.replace("{{RADAR_CONTENT}}", radar_html)

    # 追加生成信息
    gen_footer = f'<div class="gen-footer">投研鸭 Skill v1.0 · 生成时间 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} · 数据来源: 实时搜索</div>'
    html = html.replace("</body>", gen_footer + "\n</body>")

    # 输出
    output_path = data_dir / f"touyanduck-{date_str}.html"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = output_path.stat().st_size / 1024
    print()
    print("=" * 60)
    print(f"🎉 HTML 报告已生成！")
    print(f"   📄 文件：{output_path}")
    print(f"   📦 大小：{file_size:.0f} KB")
    print(f"   🦆 双击文件即可在浏览器中查看")
    print("=" * 60)
    print()


if __name__ == "__main__":
    main()
