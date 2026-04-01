#!/usr/bin/env python3
"""
extract_data.py — 投研鸭数据提取器 v1.0
从投资Agent每日策略简报的 Markdown 文件中提取结构化数据，
生成4个JSON文件，供 upload_to_cloud.py 上传到微信云数据库。

用法：
    python3 extract_data.py "{MD文件路径}" "{输出目录}"

输出文件：
    briefing.json  — 简报页数据（§1+§2摘要+§4摘要）
    markets.json   — 市场行情数据（§2全部）
    watchlist.json — 标的/自选数据（§3）
    radar.json     — 雷达/风险数据（§5+§4详情）

注意：本脚本采用"宽容解析"策略 —— 尽力提取，解析失败的字段用合理默认值填充，
确保即使 MD 格式有微小变化也不会导致整体失败。
"""

import sys
import os
import re
import json
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def read_md_file(filepath):
    """读取 MD 文件内容"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def extract_section(content, section_pattern, next_section_pattern=None):
    """提取 MD 中某个段落的内容"""
    match = re.search(section_pattern, content, re.MULTILINE)
    if not match:
        return ""
    start = match.end()
    if next_section_pattern:
        next_match = re.search(next_section_pattern, content[start:], re.MULTILINE)
        if next_match:
            return content[start:start + next_match.start()].strip()
    return content[start:].strip()


def parse_table(text):
    """
    解析 Markdown 表格，返回列表（每行是一个字典）
    支持格式：
    | 列1 | 列2 | 列3 |
    |-----|-----|-----|
    | 值1 | 值2 | 值3 |
    """
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    if len(lines) < 3:
        return []

    # 找到表头行（第一个包含 | 的行）
    header_line = None
    data_start = 0
    for i, line in enumerate(lines):
        if '|' in line and '---' not in line:
            header_line = line
            data_start = i + 2  # 跳过分隔行
            break

    if not header_line:
        return []

    headers = [h.strip() for h in header_line.split('|') if h.strip()]
    rows = []
    for line in lines[data_start:]:
        if '|' not in line or '---' in line:
            continue
        cells = [c.strip() for c in line.split('|') if c.strip()]
        if len(cells) >= len(headers):
            row = {}
            for j, h in enumerate(headers):
                row[h] = cells[j] if j < len(cells) else ""
            rows.append(row)
    return rows


def parse_change(change_str):
    """解析涨跌幅字符串为浮点数"""
    if not change_str:
        return 0.0
    cleaned = re.sub(r'[^\d.\-+]', '', str(change_str).replace('−', '-'))
    try:
        return round(float(cleaned), 2)
    except (ValueError, TypeError):
        return 0.0


def parse_price_str(price_str):
    """清理价格字符串（保留原始格式）"""
    return str(price_str).strip() if price_str else "N/A"


def determine_direction(value_str):
    """根据数值字符串判断方向"""
    if not value_str:
        return "flat"
    if '+' in str(value_str) or (re.search(r'[0-9]', str(value_str)) and '-' not in str(value_str)):
        return "up"
    elif '-' in str(value_str) or '−' in str(value_str):
        return "down"
    return "flat"


def determine_status(name, value):
    """根据指标名和数值判断红绿灯状态"""
    try:
        num = float(re.sub(r'[^\d.\-]', '', str(value).replace('−', '-')))
    except (ValueError, TypeError):
        return "yellow"

    thresholds = {
        'VIX': {'green': 18, 'yellow': 25},
        '美债': {'green': 4.0, 'yellow': 4.5},
        '原油': {'green': 80, 'yellow': 95},
        'DXY': {'green': 102, 'yellow': 107},
        '信用利差': {'green': 4.0, 'yellow': 5.0},
        'CNH': {'green': 7.15, 'yellow': 7.30},
    }

    for key, t in thresholds.items():
        if key in name:
            if num < t['green']:
                return 'green'
            elif num < t['yellow']:
                return 'yellow'
            else:
                return 'red'

    # 北向资金特殊处理
    if '北向' in name or '南向' in name:
        if num > 20:
            return 'green'
        elif num > -50:
            return 'yellow'
        else:
            return 'red'

    return 'yellow'


# ═══════════════════════════════════════════════════════════════
# 核心提取函数
# ═══════════════════════════════════════════════════════════════

def extract_briefing(content):
    """
    提取简报页数据（对应小程序 briefing 页面）
    来源：§1 今日核心结论 + §2 摘要 + §4 摘要
    """
    data = {}

    # --- 核心事件 ---
    # 通常在 §1 的第一个标题/引用块中
    s1 = extract_section(content, r'##\s*§?1', r'##\s*§?2')

    # 提取核心事件标题（通常是加粗或引用的第一行）
    event_title = ""
    event_chain = []

    # 尝试从引用块提取
    quote_match = re.search(r'>\s*\*\*(.+?)\*\*', s1)
    if quote_match:
        event_title = quote_match.group(1).strip()
    else:
        # 尝试从 ### 标题提取
        h3_match = re.search(r'###\s*.*?核心.*?[：:]\s*(.+)', s1)
        if h3_match:
            event_title = h3_match.group(1).strip()
        else:
            # 尝试第一个加粗文本
            bold_match = re.search(r'\*\*(.{10,})\*\*', s1)
            if bold_match:
                event_title = bold_match.group(1).strip()

    # 提取传导链（通常是 → 或 ① ② 格式的列表）
    chain_patterns = [
        r'[①②③④⑤⑥]\s*(.+)',  # ①②③ 格式
        r'→\s*(.+)',  # → 格式
        r'\d\.\s+(.+)',  # 1. 2. 3. 格式
        r'[-•]\s+(.+)',  # 列表格式
    ]
    for pattern in chain_patterns:
        chains = re.findall(pattern, s1)
        if len(chains) >= 2:
            event_chain = [c.strip().rstrip('。；;') for c in chains[:6]]
            break

    data['coreEvent'] = {
        'title': event_title or '市场综合动态',
        'chain': event_chain[:6] if event_chain else ['详见完整报告']
    }

    # --- 全球资产反应 ---
    global_reaction = []
    # 尝试从表格提取
    reaction_table = re.search(r'全球.*?反应.*?\n(\|.+\|[\s\S]*?\n)(?=\n[^|]|\n\n|\Z)', s1)
    if reaction_table:
        rows = parse_table(reaction_table.group(0))
        for row in rows:
            name = list(row.values())[0] if row else ""
            value = list(row.values())[1] if len(row) > 1 else ""
            global_reaction.append({
                'name': name,
                'value': value,
                'direction': determine_direction(value)
            })
    else:
        # 尝试从行内提取
        assets = re.findall(r'([\w\d/]+)\s*[：:]\s*([+-]?[\d.]+%?)', s1)
        for name, value in assets[:6]:
            global_reaction.append({
                'name': name,
                'value': value,
                'direction': determine_direction(value)
            })

    data['globalReaction'] = global_reaction if global_reaction else [
        {'name': '标普500', 'value': '--', 'direction': 'flat'}
    ]

    # --- 三大核心判断 ---
    core_judgments = []
    # 匹配 "判断X" 或 "① 判断" 格式
    judgment_patterns = [
        r'[判断]+\s*[①②③\d][.：:]\s*\*?\*?(.+?)\*?\*?\s*[（(]置信度[：:]?\s*(\d+)%?[）)].*?(?:逻辑|推理|理由)[：:]\s*(.+)',
        r'[①②③]\s*\*?\*?(.+?)\*?\*?.*?(?:置信|confidence)[：:]\s*(\d+).*?(?:逻辑|logic)[：:]\s*(.+)',
    ]
    for pattern in judgment_patterns:
        matches = re.findall(pattern, s1, re.MULTILINE)
        if matches:
            for m in matches[:3]:
                core_judgments.append({
                    'title': m[0].strip(),
                    'confidence': int(m[1]) if m[1].isdigit() else 70,
                    'logic': m[2].strip()
                })
            break

    # 如果上面没匹配到，尝试更宽松的匹配
    if not core_judgments:
        # 找包含置信度的行
        conf_lines = re.findall(r'(.+?)(?:置信度|confidence|可信度)[：:]*\s*(\d+)\s*%?', s1)
        for title, conf in conf_lines[:3]:
            core_judgments.append({
                'title': re.sub(r'[*#>•\-①②③④⑤\d.]', '', title).strip(),
                'confidence': int(conf),
                'logic': ''
            })

    data['coreJudgments'] = core_judgments if core_judgments else [
        {'title': '详见完整报告', 'confidence': 70, 'logic': ''}
    ]

    # --- 行动建议 ---
    actions = {'today': [], 'week': []}
    action_section = re.search(r'(?:行动建议|操作建议|Action)[\s\S]*?(?=###|\n##|\Z)', s1)
    if action_section:
        action_text = action_section.group(0)
        # 提取今日/本周建议
        today_items = re.findall(r'(?:今日|当日|Today)[^\n]*[-•]\s*(.+)', action_text)
        week_items = re.findall(r'(?:本周|未来|Week)[^\n]*[-•]\s*(.+)', action_text)

        if not today_items:
            today_items = re.findall(r'[-•]\s*(.+)', action_text)

        for item in today_items[:3]:
            action_type = 'hold'
            if any(w in item for w in ['加仓', '买入', '建仓', '增持']):
                action_type = 'buy'
            elif any(w in item for w in ['减持', '卖出', '止损', '减仓']):
                action_type = 'sell'
            elif any(w in item for w in ['关注', '观察', '等待']):
                action_type = 'bullish'
            actions['today'].append({'type': action_type, 'content': item.strip()})

        for item in week_items[:3]:
            action_type = 'hold'
            if any(w in item for w in ['看多', '看好', '机会']):
                action_type = 'bullish'
            elif any(w in item for w in ['减持', '卖出', '回避']):
                action_type = 'sell'
            actions['week'].append({'type': action_type, 'content': item.strip()})

    data['actions'] = actions

    # --- 市场情绪 ---
    sentiment_match = re.search(r'(?:情绪.*?分数|贪婪.*?恐惧|Fear.*?Greed)[：:]*\s*(\d+)', content)
    if sentiment_match:
        score = int(sentiment_match.group(1))
    else:
        score = 50
    data['sentimentScore'] = score

    labels = {
        (0, 35): '极度恐惧', (35, 45): '偏恐惧', (45, 55): '中性',
        (55, 65): '偏贪婪', (65, 75): '贪婪', (75, 101): '极度贪婪'
    }
    data['sentimentLabel'] = '中性'
    for (lo, hi), label in labels.items():
        if lo <= score < hi:
            data['sentimentLabel'] = label
            break

    # --- 市场概要 ---
    s2 = extract_section(content, r'##\s*§?2', r'##\s*§?3')
    summary_match = re.search(r'>\s*(.{20,})', s2)
    data['marketSummary'] = summary_match.group(1).strip() if summary_match else ''

    # --- 聪明钱速览 ---
    smart_money = []
    s4 = extract_section(content, r'##\s*§?4', r'##\s*§?5')
    # 尝试从表格提取
    fund_table = re.search(r'\|.*?(?:基金|机构|名称).*?\|[\s\S]*?\n(?:\|.+\|[\s\n]*)+', s4)
    if fund_table:
        rows = parse_table(fund_table.group(0))
        for row in rows[:3]:
            vals = list(row.values())
            signal = 'neutral'
            action_text = vals[1] if len(vals) > 1 else ''
            if any(w in action_text for w in ['增持', '加仓', '买入', '看多', '看好']):
                signal = 'bullish'
            elif any(w in action_text for w in ['减持', '卖出', '看空', '减仓']):
                signal = 'bearish'
            smart_money.append({
                'source': vals[0] if vals else '',
                'action': action_text,
                'signal': signal
            })
    else:
        # 尝试从列表提取
        fund_items = re.findall(r'[-•]\s*\*?\*?(.+?)\*?\*?[：:]\s*(.+)', s4)
        for name, action in fund_items[:3]:
            signal = 'neutral'
            if any(w in action for w in ['增持', '加仓', '买入', '看多']):
                signal = 'bullish'
            elif any(w in action for w in ['减持', '卖出', '看空']):
                signal = 'bearish'
            smart_money.append({
                'source': name.strip(),
                'action': action.strip(),
                'signal': signal
            })

    data['smartMoney'] = smart_money if smart_money else [
        {'source': '暂无数据', 'action': '详见完整报告', 'signal': 'neutral'}
    ]

    # --- 风险提示 ---
    s5 = extract_section(content, r'##\s*§?5', None)
    risk_note = ""
    risk_match = re.search(r'(?:风险提示|注意事项|Risk)[：:]*\s*(.{10,})', s5)
    if risk_match:
        risk_note = risk_match.group(1).strip()
    data['riskNote'] = risk_note

    # --- 数据截止时间 ---
    now = datetime.now()
    data['dataTime'] = now.strftime('%Y-%m-%d %H:%M BJT')

    return data


def extract_markets(content):
    """
    提取市场行情数据（对应小程序 markets 页面）
    来源：§2 全球市场隔夜速览
    """
    s2 = extract_section(content, r'##\s*§?2', r'##\s*§?3')
    data = {
        'usMarkets': [],
        'm7': [],
        'asiaMarkets': [],
        'commodities': [],
        'cryptos': [],
        'gics': []
    }

    # 提取所有表格
    tables = re.findall(r'(\|.+\|(?:\n\|.+\|)*)', s2)

    for table_text in tables:
        rows = parse_table(table_text)
        if not rows:
            continue

        headers = list(rows[0].keys())
        header_str = ' '.join(headers).lower()

        for row in rows:
            vals = list(row.values())
            if len(vals) < 2:
                continue

            name = vals[0].strip()
            # 去除Markdown加粗
            name = re.sub(r'\*\*(.+?)\*\*', r'\1', name)

            # 判断这行数据属于哪个分类
            entry = {'name': name}

            # 找价格列和涨跌幅列
            price_val = ""
            change_val = 0.0
            for h, v in row.items():
                h_lower = h.lower()
                if any(k in h_lower for k in ['收盘', '价格', 'price', '收盘价', '最新']):
                    price_val = v.strip()
                elif any(k in h_lower for k in ['涨跌', 'change', '变动', '幅度', '日涨跌']):
                    change_val = parse_change(v)

            entry['price'] = price_val
            entry['change'] = change_val

            # 分类逻辑
            if any(k in name for k in ['标普', 'SPX', 'S&P']):
                entry['changeLabel'] = '大盘指数'
                # 尝试找note
                for h, v in row.items():
                    if any(k in h for k in ['备注', '说明', 'note', '事件']):
                        entry['note'] = v.strip()
                data['usMarkets'].append(entry)
            elif any(k in name for k in ['纳斯达克', 'NDX', 'NASDAQ', 'QQQ', '纳指']):
                entry['changeLabel'] = '科技指数'
                data['usMarkets'].append(entry)
            elif any(k in name for k in ['道琼斯', 'DJI', 'DJIA', '道指']):
                entry['changeLabel'] = '蓝筹指数'
                data['usMarkets'].append(entry)
            elif 'VIX' in name.upper():
                entry['changeLabel'] = '恐慌指标'
                data['usMarkets'].append(entry)
            elif any(k in name for k in ['AAPL', '苹果']):
                entry['symbol'] = 'AAPL'
                data['m7'].append(entry)
            elif any(k in name for k in ['MSFT', '微软']):
                entry['symbol'] = 'MSFT'
                data['m7'].append(entry)
            elif any(k in name for k in ['NVDA', '英伟达']):
                entry['symbol'] = 'NVDA'
                data['m7'].append(entry)
            elif any(k in name for k in ['GOOGL', '谷歌', 'Google']):
                entry['symbol'] = 'GOOGL'
                data['m7'].append(entry)
            elif any(k in name for k in ['AMZN', '亚马逊']):
                entry['symbol'] = 'AMZN'
                data['m7'].append(entry)
            elif any(k in name for k in ['META', 'Meta']):
                entry['symbol'] = 'META'
                data['m7'].append(entry)
            elif any(k in name for k in ['TSLA', '特斯拉']):
                entry['symbol'] = 'TSLA'
                data['m7'].append(entry)
            elif any(k in name for k in ['上证', 'SSEC', '沪指']):
                data['asiaMarkets'].append(entry)
            elif any(k in name for k in ['深证', '深成', 'SZSE']):
                data['asiaMarkets'].append(entry)
            elif any(k in name for k in ['恒生指数', 'HSI']) and '科技' not in name:
                data['asiaMarkets'].append(entry)
            elif any(k in name for k in ['恒生科技', 'HSTECH']):
                data['asiaMarkets'].append(entry)
            elif any(k in name for k in ['日经', 'N225', 'NIKKEI']):
                data['asiaMarkets'].append(entry)
            elif any(k in name for k in ['KOSPI', '韩国']):
                data['asiaMarkets'].append(entry)
            elif any(k in name for k in ['黄金', 'XAU', 'Gold']):
                data['commodities'].append(entry)
            elif any(k in name for k in ['布伦特', 'Brent']):
                data['commodities'].append(entry)
            elif any(k in name for k in ['WTI']):
                data['commodities'].append(entry)
            elif any(k in name for k in ['美元指数', 'DXY']):
                data['commodities'].append(entry)
            elif any(k in name for k in ['美债', 'US10Y', '10Y', '10年']):
                data['commodities'].append(entry)
            elif any(k in name for k in ['人民币', 'CNH', 'CNY']):
                data['commodities'].append(entry)
            elif any(k in name for k in ['比特币', 'BTC', 'Bitcoin']):
                data['cryptos'].append(entry)
            elif any(k in name for k in ['以太坊', 'ETH', 'Ethereum']):
                data['cryptos'].append(entry)
            elif any(k in name for k in ['SOL', 'Solana']):
                data['cryptos'].append(entry)

    # --- GICS 板块 ---
    s3 = extract_section(content, r'##\s*§?3', r'##\s*§?4')
    gics_table = re.search(r'(?:GICS|板块|行业).*?\n(\|.+\|(?:\n\|.+\|)*)', s3, re.IGNORECASE)
    if gics_table:
        rows = parse_table(gics_table.group(0))
        for row in rows:
            vals = list(row.values())
            if len(vals) >= 2:
                name = re.sub(r'\*\*(.+?)\*\*', r'\1', vals[0].strip())
                change = parse_change(vals[1])
                etf = ''
                # 从名称中提取ETF代码
                etf_match = re.search(r'(XL[A-Z]|XLRE)', name)
                if etf_match:
                    etf = etf_match.group(1)
                data['gics'].append({
                    'name': name,
                    'change': change,
                    'etf': etf
                })

    # 按涨跌幅排序
    data['gics'].sort(key=lambda x: x.get('change', 0), reverse=True)

    return data


def extract_watchlist(content):
    """
    提取标的/自选数据（对应小程序 watchlist 页面）
    来源：§3 重点标的与行业分析
    """
    s3 = extract_section(content, r'##\s*§?3', r'##\s*§?4')

    # 默认板块结构
    default_sectors = [
        {'id': 'ai', 'name': 'AI算力', 'trend': 'up', 'summary': ''},
        {'id': 'semi', 'name': '半导体', 'trend': 'up', 'summary': ''},
        {'id': 'internet', 'name': '互联网平台', 'trend': 'up', 'summary': ''},
        {'id': 'energy', 'name': '新能源', 'trend': 'hold', 'summary': ''},
        {'id': 'consumer', 'name': '消费', 'trend': 'hold', 'summary': ''},
        {'id': 'pharma', 'name': '医药', 'trend': 'hold', 'summary': ''},
        {'id': 'finance', 'name': '金融', 'trend': 'hold', 'summary': ''},
    ]

    # 从 §3 表格提取个股数据
    stock_data = {}
    for sector in default_sectors:
        stock_data[sector['id']] = []

    # 提取所有表格行
    tables = re.findall(r'(\|.+\|(?:\n\|.+\|)*)', s3)
    for table_text in tables:
        rows = parse_table(table_text)
        for row in rows:
            vals = list(row.values())
            if len(vals) < 3:
                continue

            name = re.sub(r'\*\*(.+?)\*\*', r'\1', vals[0].strip())
            symbol = ''
            price = ''
            change = 0.0

            for h, v in row.items():
                h_lower = h.lower()
                if any(k in h_lower for k in ['代码', 'symbol', 'ticker']):
                    symbol = v.strip()
                elif any(k in h_lower for k in ['收盘', '价格', 'price']):
                    price = v.strip()
                elif any(k in h_lower for k in ['涨跌', 'change']):
                    change = parse_change(v)

            if not symbol:
                # 从名称中提取
                sym_match = re.search(r'([A-Z]{2,5})', name)
                if sym_match:
                    symbol = sym_match.group(1)

            # 分类到板块
            sector_id = 'ai'  # 默认
            if any(k in name + symbol for k in ['NVDA', '英伟达', 'AVGO', '博通', 'TSM', '台积电', 'MSFT', '微软', 'ORCL', '甲骨文']):
                sector_id = 'ai'
            elif any(k in name + symbol for k in ['AMD', 'ASML', 'SK海力士', '000660', 'MU', '美光']):
                sector_id = 'semi'
            elif any(k in name + symbol for k in ['腾讯', '0700', 'PDD', '拼多多', '美团', '3690', 'BABA', '阿里']):
                sector_id = 'internet'
            elif any(k in name + symbol for k in ['宁德', '300750', '比亚迪', '002594', '特斯拉', 'TSLA']):
                sector_id = 'energy'
            elif any(k in name + symbol for k in ['泡泡玛特', '9992', 'COST', 'Costco']):
                sector_id = 'consumer'
            elif any(k in name + symbol for k in ['NVO', '诺和诺德', 'LLY', '礼来']):
                sector_id = 'pharma'
            elif any(k in name + symbol for k in ['BRK', '伯克希尔', 'JPM', '摩根']):
                sector_id = 'finance'

            stock_entry = {
                'name': name,
                'symbol': symbol,
                'change': change,
                'price': price,
                'tags': [],
                'reason': '',
                'analysis': '',
                'metrics': [],
                'risks': []
            }

            # 尝试从 §3 展开部分提取更详细信息
            detail_match = re.search(
                rf'(?:###|####)\s*.*?{re.escape(name[:2])}.*?\n([\s\S]*?)(?=(?:###|####)\s|\Z)',
                s3
            )
            if detail_match:
                detail = detail_match.group(1)
                # 提取标签
                tag_match = re.findall(r'标签[：:]\s*(.+)', detail)
                if tag_match:
                    stock_entry['tags'] = [t.strip() for t in tag_match[0].split('、')[:2]]
                # 提取理由
                reason_match = re.search(r'(?:理由|推荐|核心逻辑)[：:]\s*(.+)', detail)
                if reason_match:
                    stock_entry['reason'] = reason_match.group(1).strip()

            if stock_entry['symbol']:
                stock_data[sector_id].append(stock_entry)

    data = {
        'sectors': default_sectors,
        'stocks': stock_data
    }

    return data


def extract_radar(content):
    """
    提取雷达/风险数据（对应小程序 radar 页面）
    来源：§5 风险与机会雷达 + §4 基金&大资金动向
    """
    s5 = extract_section(content, r'##\s*§?5', None)
    s4 = extract_section(content, r'##\s*§?4', r'##\s*§?5')

    data = {}

    # --- 红绿灯 ---
    traffic_lights = []
    # 从红绿灯表格提取
    tl_table = re.search(r'(?:红绿灯|交通灯|信号灯|Traffic).*?\n(\|.+\|(?:\n\|.+\|)*)', s5, re.IGNORECASE)
    if tl_table:
        rows = parse_table(tl_table.group(0))
        for row in rows:
            vals = list(row.values())
            if len(vals) >= 2:
                name = re.sub(r'\*\*(.+?)\*\*', r'\1', vals[0].strip())
                value = vals[1].strip() if len(vals) > 1 else ''
                # 尝试获取状态
                status = ''
                for h, v in row.items():
                    if any(k in h for k in ['状态', '信号', 'status', '灯']):
                        status = v.strip().lower()
                        if '绿' in status or 'green' in status:
                            status = 'green'
                        elif '红' in status or 'red' in status:
                            status = 'red'
                        else:
                            status = 'yellow'

                if not status:
                    status = determine_status(name, value)

                # 获取阈值
                threshold = ''
                for h, v in row.items():
                    if any(k in h for k in ['阈值', '标准', 'threshold']):
                        threshold = v.strip()

                traffic_lights.append({
                    'name': name,
                    'value': value,
                    'status': status,
                    'threshold': threshold
                })

    data['trafficLights'] = traffic_lights if traffic_lights else [
        {'name': 'VIX波动率', 'value': '--', 'status': 'yellow', 'threshold': '<18绿 / 18-25黄 / >25红'}
    ]

    # --- 风险分数 ---
    risk_score_match = re.search(r'(?:风险.*?分数|综合.*?评分|Risk.*?Score)[：:]*\s*(\d+)', s5)
    data['riskScore'] = int(risk_score_match.group(1)) if risk_score_match else 50

    if data['riskScore'] < 30:
        data['riskLevel'] = 'low'
        data['riskAdvice'] = '当前市场处于低风险区间，可适当提高仓位至7-8成。'
    elif data['riskScore'] < 50:
        data['riskLevel'] = 'medium'
        data['riskAdvice'] = '当前市场处于中等风险区间，建议维持6成仓位。'
    else:
        data['riskLevel'] = 'high'
        data['riskAdvice'] = '当前市场风险偏高，建议降低仓位至4成以下。'

    # --- 监控阈值表 ---
    monitor_table = []
    mt_match = re.search(r'(?:监控|阈值|触发).*?\n(\|.+\|(?:\n\|.+\|)*)', s5, re.IGNORECASE)
    if mt_match:
        rows = parse_table(mt_match.group(0))
        for row in rows:
            vals = list(row.values())
            if len(vals) >= 2:
                monitor_table.append({
                    'condition': vals[0].strip(),
                    'action': vals[1].strip()
                })

    data['monitorTable'] = monitor_table

    # --- 风险预警 ---
    risk_alerts = []
    alert_match = re.search(r'(?:风险预警|风险矩阵|Risk Alert).*?\n(\|.+\|(?:\n\|.+\|)*)', s5, re.IGNORECASE)
    if alert_match:
        rows = parse_table(alert_match.group(0))
        for row in rows:
            vals = list(row.values())
            if len(vals) >= 3:
                level = 'medium'
                for h, v in row.items():
                    if any(k in h for k in ['级别', '等级', 'level']):
                        if '高' in v or 'high' in v.lower():
                            level = 'high'
                        elif '低' in v or 'low' in v.lower():
                            level = 'low'

                risk_alerts.append({
                    'title': vals[0].strip(),
                    'probability': vals[1].strip() if len(vals) > 1 else '',
                    'impact': vals[2].strip() if len(vals) > 2 else '',
                    'response': vals[3].strip() if len(vals) > 3 else '',
                    'level': level
                })

    data['riskAlerts'] = risk_alerts

    # --- 本周重要事件 ---
    events = []
    event_match = re.search(r'(?:重要事件|本周日历|Event).*?\n(\|.+\|(?:\n\|.+\|)*)', s5, re.IGNORECASE)
    if event_match:
        rows = parse_table(event_match.group(0))
        for row in rows:
            vals = list(row.values())
            if len(vals) >= 2:
                impact = 'medium'
                for h, v in row.items():
                    if any(k in h for k in ['影响', 'impact']):
                        if '高' in v or 'high' in v.lower():
                            impact = 'high'
                        elif '低' in v or 'low' in v.lower():
                            impact = 'low'
                events.append({
                    'date': vals[0].strip(),
                    'title': vals[1].strip(),
                    'impact': impact
                })

    data['events'] = events

    # --- 实时快讯 ---
    data['alerts'] = []  # 快讯由上传时实时数据填充，或留空

    # --- 聪明钱详情（来自 §4）---
    smart_money_detail = []
    # 尝试按梯队提取
    tiers = [
        ('T1旗舰', r'(?:一级|T1|核心|旗舰)'),
        ('T2成长', r'(?:二级|T2|成长|追踪)'),
        ('策略师观点', r'(?:策略师|分析师|观点)')
    ]
    for tier_name, tier_pattern in tiers:
        tier_section = re.search(rf'{tier_pattern}[\s\S]*?(?=(?:###|####|一级|二级|三级|T1|T2|策略师)\s|\Z)', s4)
        if tier_section:
            tier_text = tier_section.group(0)
            funds = []
            # 从表格提取
            fund_table = re.search(r'\|.+\|(?:\n\|.+\|)*', tier_text)
            if fund_table:
                rows = parse_table(fund_table.group(0))
                for row in rows:
                    vals = list(row.values())
                    if len(vals) >= 2:
                        signal = 'neutral'
                        action_text = vals[1] if len(vals) > 1 else ''
                        if any(w in action_text for w in ['增持', '加仓', '买入', '看多', '看好']):
                            signal = 'bullish'
                        elif any(w in action_text for w in ['减持', '卖出', '看空']):
                            signal = 'bearish'
                        funds.append({
                            'name': vals[0].strip(),
                            'action': action_text.strip(),
                            'signal': signal
                        })
            if funds:
                smart_money_detail.append({
                    'tier': tier_name,
                    'funds': funds
                })

    data['smartMoneyDetail'] = smart_money_detail

    # --- 数据截止时间 ---
    now = datetime.now()
    data['dataTime'] = now.strftime('%Y-%m-%d %H:%M BJT')

    return data


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 3:
        print("用法: python3 extract_data.py <MD文件路径> <输出目录>")
        print("示例: python3 extract_data.py report.md ./output/")
        sys.exit(1)

    md_path = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.exists(md_path):
        print(f"❌ MD文件不存在: {md_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    print(f"📄 读取 MD 文件: {md_path}")
    content = read_md_file(md_path)
    print(f"   文件大小: {len(content)} 字符")

    # 提取4个数据集
    extractors = {
        'briefing': ('简报页', extract_briefing),
        'markets': ('市场页', extract_markets),
        'watchlist': ('标的页', extract_watchlist),
        'radar': ('雷达页', extract_radar),
    }

    for name, (desc, func) in extractors.items():
        try:
            print(f"\n🔍 正在提取 {desc} 数据...")
            data = func(content)
            filepath = os.path.join(output_dir, f'{name}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"   ✅ {name}.json 已保存 ({os.path.getsize(filepath)} bytes)")
        except Exception as e:
            print(f"   ⚠️ {name} 提取出现问题: {e}")
            # 写入空壳数据，确保不阻塞流程
            filepath = os.path.join(output_dir, f'{name}.json')
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump({'_error': str(e), '_fallback': True}, f, ensure_ascii=False, indent=2)
            print(f"   📝 已写入降级数据")

    print(f"\n🎉 数据提取完成！文件保存在: {output_dir}")


if __name__ == '__main__':
    main()
