#!/usr/bin/env python3
"""
generate_audio.py — 投研鸭语音播报生成器 v3.0

从 briefing.json / markets.json / watchlist.json / radar.json 提取重点内容，
按八段式结构组装播报文稿，调用 MiniMax TTS API 生成播报音频。

设计原则（对标高盛晨会/伯克希尔致股东信风格）：
  - 结论先行，判断驱动
  - 每段只贡献不可替代的增量信息，绝不重复
  - 搜索范围大（不漏），产出精选（不凑数）
  - 大老板听的是"少而精的决策信号"

播报结构：
  §0 开场白 → §1 核心判断 → §2 驱动事件 → §3 市场全景 →
  §4 重点标的 → §5 聪明钱 → §6 风险与日历 → §7 深度判断 → §8 结尾

用法：
    python3 generate_audio.py <JSON文件目录> <日期YYYY-MM-DD>

前提条件：
    设置环境变量 MINIMAX_API_KEY="你的MiniMax API Key"

v1.0 — 2026-04-06：初始版本
v2.0 — 2026-04-06：十段式播报结构，跨 JSON 数据整合
v3.0 — 2026-04-06：精选模式重构，去重+增量信息优先，对标机构晨会标准
"""

import sys
import os
import json
import re
import time

try:
    import requests
except ImportError:
    print("❌ 缺少 requests 库，请先安装：pip3 install requests")
    sys.exit(1)


# ═══════════════════════════════════════════════════════════════
# 配置
# ═══════════════════════════════════════════════════════════════

CONFIG = {
    'API_KEY': os.environ.get('MINIMAX_API_KEY', ''),
    'MODEL': 'speech-2.8-hd',
    'VOICE_ID': 'male-qn-jingying-jingpin',  # 精英青年-beta，专业播报感
    'SPEED': 1.0,
    'VOL': 1.0,
    'PITCH': 0,
    'SAMPLE_RATE': 32000,
    'BITRATE': 128000,
    'FORMAT': 'mp3',
}

# MiniMax T2A v2 API 端点
API_URL = "https://api.minimaxi.com/v1/t2a_v2"


# ═══════════════════════════════════════════════════════════════
# 播报文本组装
# ═══════════════════════════════════════════════════════════════

def _clean_text(text):
    """
    清理播报文本：去除标记、口播化金额、修正 TTS 不友好的符号。
    设计原则：TTS 引擎读到的每一个字都应该能被正确朗读。
    """
    if not text:
        return ''
    # 去除【】高亮标记
    text = re.sub(r'[【】]', '', text)
    # $320万 / $6500亿 → 320万美元 / 6500亿美元（带中文量词先处理）
    text = re.sub(r'\$([0-9,]+\.?\d*)(万|亿|千)', r'\1\2美元', text)
    # $4.08/加仑 → 4.08美元每加仑（带单位的特殊处理）
    text = re.sub(r'\$([0-9,]+\.?\d*)/(\w+)', r'\1美元每\2', text)
    # $305-309 → 305至309美元（范围格式）
    text = re.sub(r'\$([0-9,]+\.?\d*)\s*[-~]\s*\$?([0-9,]+\.?\d*)', r'\1至\2美元', text)
    # $109.03 → 109美元（去掉小数点后的部分，整数更口语化）
    text = re.sub(r'\$([0-9,]+)\.\d+', r'\1美元', text)
    # $109 → 109美元（整数金额）
    text = re.sub(r'\$([0-9,]+)', r'\1美元', text)
    # ¥128.50 → 128元
    text = re.sub(r'¥([0-9,]+)\.?\d*', r'\1元', text)
    # HK$485.00 → 485港元
    text = re.sub(r'HK\$([0-9,]+)\.?\d*', r'\1港元', text)
    # +1.45% / -14% → 涨1.45% / 跌14%（正负号转中文）
    text = re.sub(r'\+(\d+\.?\d*)%', r'涨\1%', text)
    text = re.sub(r'-(\d+\.?\d*)%', r'跌\1%', text)
    # 日期格式 3/30 4/4 → 3月30日 4月4日（数字/数字 且两边非字母）
    text = re.sub(r'(?<![A-Za-z])(\d{1,2})/(\d{1,2})(?![A-Za-z])', r'\1月\2日', text)
    # Model S/X → Model S和X（产品型号中的斜杠）
    text = re.sub(r'(Model\s+\w)\s*/\s*(\w)', r'\1和\2', text)
    # 30+ → 30以上
    text = re.sub(r'(\d+)\+', r'\1以上', text)
    # 30%+ → 30%以上（百分比后面的加号）
    text = re.sub(r'(\d+%)\+', r'\1以上', text)
    # 股票代码括号去掉：CoreWeave(CRWV) → CoreWeave
    text = re.sub(r'\(([A-Z]{1,5}(?:\.[A-Z]{2})?)\)', '', text)
    # 加号连接词转口语：A+B → A、B 或 A以及B
    text = re.sub(r'(\S)\+(\S)', r'\1、\2', text)
    # 10Y美债 → 十年期美债（口语化）
    text = re.sub(r'10Y', '十年期', text)
    # XAU → 黄金（去掉交易代码）
    text = text.replace('黄金XAU', '黄金')
    text = text.replace('XAU', '黄金')
    # → 符号转口语化连接词
    text = text.replace(' → ', '，进而')
    text = text.replace('→', '，进而')
    # 去掉多余的连续标点
    text = re.sub(r'。。+', '。', text)
    text = re.sub(r'，，+', '，', text)
    text = re.sub(r'，+。', '。', text)
    return text.strip()


def _build_stock_highlight(stock):
    """
    为单只标的构建一句话播报。
    核心：说清楚"涨/跌多少 + 因为什么（今日催化）"，不说入选理由。
    """
    name = stock.get('name', '')
    change = stock.get('change', 0)
    direction = '涨' if change > 0 else '跌'

    # 从 analysis 第一段提取"今日发生了什么"
    analysis = stock.get('analysis', '')
    reason = stock.get('reason', '')

    # analysis 第一句通常是最有信息量的
    catalyst = ''
    if analysis:
        first_line = analysis.split('\n')[0].strip()
        # 去掉开头的标的名（避免"特斯拉跌5.4%，特斯拉Q1交付…"这种重复）
        if first_line.startswith(name):
            first_line = first_line[len(name):]
            # 去掉紧跟的标点或空白
            first_line = first_line.lstrip('，。：:、 ')
        if len(first_line) > 55:
            for sep in ('，', '。', '；'):
                idx = first_line.find(sep, 15)
                if 0 < idx < 55:
                    first_line = first_line[:idx]
                    break
            else:
                first_line = first_line[:50]
        catalyst = first_line

    if not catalyst and reason:
        catalyst = reason[:50] if len(reason) > 50 else reason

    badges = stock.get('badges', [])
    badge_str = f"，{badges[0]}" if badges else ''

    result = f"{name}{direction}{abs(change)}%{badge_str}，{_clean_text(catalyst)}"
    # 去掉末尾多余的句号（外层 join 会加）
    return result.rstrip('。')


def _filter_notable_stocks(watchlist_data):
    """
    从 watchlist 中筛选值得播报的标的。
    筛选逻辑：|涨跌幅| ≥ 2.5% 或 有 badges（聪明钱关注）。
    去重：同一只股票可能出现在多个板块中。
    返回按 |涨跌幅| 排序的前 5 只。
    """
    seen_symbols = set()
    results = []
    stocks_dict = watchlist_data.get('stocks', {})

    for sector_id, stocks in stocks_dict.items():
        for s in stocks:
            if not s.get('listed', True):
                continue
            symbol = s.get('symbol', '')
            if symbol in seen_symbols:
                continue
            seen_symbols.add(symbol)

            change = abs(s.get('change', 0))
            badges = s.get('badges', [])

            if change >= 2.5 or len(badges) > 0:
                results.append(s)

    # 按涨跌幅绝对值排序，取前5
    results.sort(key=lambda x: abs(x.get('change', 0)), reverse=True)
    return results[:5]


def extract_voice_text(briefing_data, markets_data=None, watchlist_data=None, radar_data=None):
    """
    从多个 JSON 提取重点内容，组装播报文稿。

    设计原则（对标高盛晨会/伯克希尔致股东信风格）：
    - 结论先行，判断驱动
    - 每段只贡献不可替代的增量信息，绝不重复
    - 搜索范围大（不漏），产出精选（不凑数）
    - 大老板听的是"少而精的决策信号"

    播报结构：
    §0 开场白
    §1 今日核心判断 — 一句话定调
    §2 驱动事件 — 今日为什么是这个结论
    §3 市场全景 — 数字+各市场一句话摘要（合并原大盘速览和市场概览，去重）
    §4 重点标的异动 — 有催化的才提
    §5 聪明钱信号 — 只说有行动增量的
    §6 风险与日历 — 风险+红灯+前瞻事件
    §7 深度判断 — 三大核心判断压轴
    §8 结尾
    """
    markets_data = markets_data or {}
    watchlist_data = watchlist_data or {}
    radar_data = radar_data or {}

    sections = []

    # ── §0 开场白 ──
    date = briefing_data.get('date', '')
    if date:
        try:
            parts = date.split('-')
            month = int(parts[1])
            day = int(parts[2])
            date_str = f"{month}月{day}日"
        except (IndexError, ValueError):
            date_str = date
    else:
        date_str = '今日'
    sections.append(f"投研鸭，{date_str}，二级市场简报。")

    # ── §1 今日核心判断 ──
    # takeaway 是整篇的灵魂，直接播出
    takeaway = briefing_data.get('takeaway', '')
    if takeaway:
        sections.append(f"今日核心判断：{_clean_text(takeaway)}")

    # ── §2 驱动事件 ──
    # 只念事件标题 + 精炼的一句 brief，因为 takeaway 已经给了结论
    core_event = briefing_data.get('coreEvent', {})
    chain = core_event.get('chain', [])
    if chain:
        event_lines = []
        for evt in chain[:5]:
            title = _clean_text(evt.get('title', ''))
            brief = _clean_text(evt.get('brief', ''))
            if title and brief:
                # brief 截取到第一个有意义的断句处，避免太长
                if len(brief) > 45:
                    for sep in ('，', '。', '；'):
                        idx = brief.find(sep, 15)
                        if 0 < idx < 45:
                            brief = brief[:idx]
                            break
                    else:
                        brief = brief[:40]
                event_lines.append(f"{title}，{brief}")
            elif title:
                event_lines.append(title)
        if event_lines:
            sections.append(f"本期驱动事件：{'。'.join(event_lines)}。")

    # ── §3 市场全景 ──
    # 合并"大盘速览"和"各市场概览"，避免重复
    # 先报核心数字（标普/纳指/VIX），再报各市场一句话结论
    panorama_parts = []

    # 3a: 核心指数一句话
    us_markets = markets_data.get('usMarkets', [])
    if us_markets:
        idx_lines = []
        for m in us_markets:
            name = m.get('name', '')
            price = m.get('price', '')
            change = m.get('change', 0)
            if name and price:
                direction = '涨' if change > 0 else ('跌' if change < 0 else '平')
                idx_lines.append(f"{name}报{price}，{direction}{abs(change)}%")
        if idx_lines:
            panorama_parts.append('，'.join(idx_lines))

    # 3b: 关键大宗商品（只从 globalReaction 取非股指项，去掉 BTC）
    global_reaction = briefing_data.get('globalReaction', [])
    skip_names = {'标普500', '纳斯达克', 'BTC'}
    commodity_items = []
    for g in global_reaction:
        gname = _clean_text(g.get('name', ''))
        if g.get('name', '') in skip_names:
            continue
        gval = _clean_text(g.get('value', ''))
        gnote = g.get('note', '')
        if gname and gval:
            commodity_items.append(f"{gname}{gval}{'，' + gnote if gnote else ''}")
    if commodity_items:
        panorama_parts.append('。'.join(commodity_items))

    # 3c: 情绪指标
    sentiment_score = briefing_data.get('sentimentScore', '')
    sentiment_label = briefing_data.get('sentimentLabel', '')
    if sentiment_score and sentiment_label:
        panorama_parts.append(f"市场情绪{sentiment_score}分，{sentiment_label}")

    # 3d: 各市场增量结论（跳过美股——已在数字中体现，加密精简）
    insight_map = [
        ('m7Insight', 'M7巨头'),
        ('asiaInsight', '亚太'),
        ('commodityInsight', '大宗'),
        ('cryptoInsight', '加密'),
    ]
    for key, label in insight_map:
        insight = markets_data.get(key, '')
        if insight:
            clean = _clean_text(insight)
            # 加密市场精简到一句
            if key == 'cryptoInsight' and len(clean) > 25:
                for sep in ('，', '。', '；'):
                    idx = clean.find(sep)
                    if idx > 0:
                        clean = clean[:idx]
                        break
            panorama_parts.append(f"{label}，{clean}")

    if panorama_parts:
        sections.append(f"市场全景：{'。'.join(panorama_parts)}。")

    # ── §4 重点标的异动 ──
    notable_stocks = _filter_notable_stocks(watchlist_data)
    if notable_stocks:
        stock_lines = [_build_stock_highlight(s) for s in notable_stocks]
        sections.append(f"重点标的：{'。'.join(stock_lines)}。")

    # ── §5 聪明钱信号 ──
    # 去重逻辑：如果聪明钱动作已在标的段落提到过（如段永平+泡泡玛特），精简处理
    smart_money = briefing_data.get('smartMoney', [])
    if smart_money:
        sm_lines = []
        for sm in smart_money[:4]:
            source = sm.get('source', '')
            action = _clean_text(sm.get('action', ''))
            if source and action:
                sm_lines.append(f"{source}：{action}")
        if sm_lines:
            sections.append(f"聪明钱信号：{'。'.join(sm_lines)}。")

    # ── §6 风险与日历 ──
    risk_parts = []

    # 红灯指标
    traffic_lights = radar_data.get('trafficLights', [])
    red_lights = [tl for tl in traffic_lights if tl.get('status') == 'red']
    for rl in red_lights:
        rl_name = _clean_text(rl.get('name', ''))
        rl_value = _clean_text(rl.get('value', ''))
        if rl_name and rl_value:
            risk_parts.append(f"红灯信号：{rl_name}{rl_value}，避险情绪极端")

    # 风险点
    risk_points = briefing_data.get('riskPoints', [])
    for rp in risk_points[:3]:
        risk_parts.append(_clean_text(rp))

    # 前瞻日历（只从 radar.events 取，不和事件链重复）
    events = radar_data.get('events', [])
    if events:
        event_briefs = []
        for evt in events[:3]:
            evt_date = evt.get('date', '')
            evt_title = _clean_text(evt.get('title', ''))
            if evt_title:
                # 截取到破折号前
                dash_idx = evt_title.find('——')
                if dash_idx > 0:
                    evt_title = evt_title[:dash_idx]
                event_briefs.append(f"{evt_date}，{evt_title}")
        if event_briefs:
            risk_parts.append(f"前瞻日历：{'。'.join(event_briefs)}")

    if risk_parts:
        sections.append(f"风险与日历：{'。'.join(risk_parts)}。")

    # ── §7 深度判断 ──
    core_judgments = briefing_data.get('coreJudgments', [])
    if core_judgments:
        judgment_lines = []
        for j in core_judgments:
            j_title = _clean_text(j.get('title', ''))
            j_conf = j.get('confidence', 0)
            j_logic = _clean_text(j.get('logic', ''))
            if j_title:
                line = f"{j_title}，置信度{j_conf}%"
                if j_logic:
                    line += f"。逻辑：{j_logic}"
                judgment_lines.append(line)
        if judgment_lines:
            sections.append(f"深度判断：{'。'.join(judgment_lines)}。")

    # ── §8 结尾 ──
    sections.append("以上是今日简报，详细内容请查看投研鸭小程序。")

    full_text = '\n\n'.join(sections)

    # 安全截断：MiniMax 单次限制 10000 字符
    if len(full_text) > 9000:
        full_text = full_text[:9000] + '\n\n以上是今日播报重点，详细内容请查看投研鸭小程序。'

    return full_text


# ═══════════════════════════════════════════════════════════════
# MiniMax TTS API 调用
# ═══════════════════════════════════════════════════════════════

def call_minimax_tts(text, output_path):
    """
    调用 MiniMax T2A v2 API 生成语音文件。

    参数：
        text: 待合成的文本
        output_path: 输出音频文件路径

    返回：
        True/False 表示是否成功
    """
    api_key = CONFIG['API_KEY']
    if not api_key:
        print("❌ 未设置 MINIMAX_API_KEY 环境变量！")
        print("   请执行：export MINIMAX_API_KEY=\"你的API Key\"")
        return False

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": CONFIG['MODEL'],
        "text": text,
        "stream": False,
        "voice_setting": {
            "voice_id": CONFIG['VOICE_ID'],
            "speed": CONFIG['SPEED'],
            "vol": CONFIG['VOL'],
            "pitch": CONFIG['PITCH']
        },
        "audio_setting": {
            "sample_rate": CONFIG['SAMPLE_RATE'],
            "bitrate": CONFIG['BITRATE'],
            "format": CONFIG['FORMAT']
        },
        "output_format": "hex"
    }

    print(f"   🎤 正在调用 MiniMax TTS API（{CONFIG['MODEL']}）...")
    print(f"   📝 播报文本长度：{len(text)} 字符")

    try:
        resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)

        if resp.status_code != 200:
            print(f"   ❌ API 请求失败，状态码: {resp.status_code}")
            print(f"   响应内容: {resp.text[:500]}")
            return False

        result = resp.json()

        # 检查 API 返回是否包含错误
        if result.get('base_resp', {}).get('status_code', 0) != 0:
            error_msg = result.get('base_resp', {}).get('status_msg', '未知错误')
            print(f"   ❌ TTS 合成失败: {error_msg}")
            return False

        # 提取音频数据（hex 编码）
        audio_hex = result.get('data', {}).get('audio', '')
        if not audio_hex:
            # 兼容：部分版本 API 直接返回 audio_hex 在顶层
            audio_hex = result.get('audio_hex', '') or result.get('data', {}).get('audio_hex', '')

        if not audio_hex:
            print(f"   ❌ API 返回中未找到音频数据")
            print(f"   响应结构: {list(result.keys())}")
            if 'data' in result:
                print(f"   data 结构: {list(result['data'].keys()) if isinstance(result['data'], dict) else type(result['data'])}")
            return False

        # 将 hex 字符串转为二进制，写入文件
        audio_bytes = bytes.fromhex(audio_hex)
        with open(output_path, 'wb') as f:
            f.write(audio_bytes)

        file_size_kb = len(audio_bytes) / 1024
        print(f"   ✅ 音频生成成功：{output_path}")
        print(f"   📊 文件大小：{file_size_kb:.1f} KB")
        return True

    except requests.exceptions.Timeout:
        print("   ❌ API 请求超时（60秒）")
        return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ 网络请求异常: {e}")
        return False
    except (ValueError, KeyError) as e:
        print(f"   ❌ 解析 API 响应失败: {e}")
        return False


# ═══════════════════════════════════════════════════════════════
# 主流程
# ═══════════════════════════════════════════════════════════════

def _load_json(filepath, label):
    """安全加载 JSON 文件，不存在时返回空 dict 并打印警告"""
    if not os.path.exists(filepath):
        print(f"   ⚠️  {label} 不存在: {filepath}（播报将省略该部分）")
        return {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   ✅ {label} 已加载")
        return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"   ⚠️  {label} 读取失败: {e}")
        return {}


def main():
    if len(sys.argv) < 3:
        print("=" * 60)
        print("投研鸭 — 语音播报生成器 v3.0")
        print("=" * 60)
        print()
        print("用法: python3 generate_audio.py <JSON目录> <日期>")
        print()
        print("示例:")
        print("  python3 generate_audio.py ./output/ 2026-04-06")
        print()
        print("前提:")
        print("  设置环境变量 MINIMAX_API_KEY")
        print()
        sys.exit(1)

    data_dir = sys.argv[1]
    date = sys.argv[2]

    print("=" * 60)
    print(f"🦆 投研鸭语音播报生成 v3.0 — {date}")
    print("=" * 60)

    # 检查 API Key
    if not CONFIG['API_KEY']:
        print()
        print("⚠️  MINIMAX_API_KEY 未设置！")
        print("   请执行：export MINIMAX_API_KEY=\"你的API Key\"")
        print()
        sys.exit(1)

    # 读取所有 JSON 数据源
    print(f"\n📖 读取数据文件...")
    briefing_path = os.path.join(data_dir, 'briefing.json')
    if not os.path.exists(briefing_path):
        print(f"❌ briefing.json 不存在: {briefing_path}")
        sys.exit(1)

    with open(briefing_path, 'r', encoding='utf-8') as f:
        briefing_data = json.load(f)
    print(f"   ✅ briefing.json 已加载")

    # 判断播报文稿来源：优先使用 AI 撰写的 voiceText，无则 fallback 到代码拼接
    existing_voice_text = briefing_data.get('voiceText', '')

    if existing_voice_text and len(existing_voice_text) > 200:
        # ── 模式A：AI 已撰写播报文稿，直接使用 ──
        voice_text = existing_voice_text
        print(f"\n📝 使用 AI 撰写的播报文稿（{len(voice_text)}字符，预估{len(voice_text) * 60 // 300}秒）")
        print(f"   来源：briefing.json → voiceText（AI 审读版）")
    else:
        # ── 模式B：Fallback，代码从多个 JSON 拼接 ──
        markets_data = _load_json(os.path.join(data_dir, 'markets.json'), 'markets.json')
        watchlist_data = _load_json(os.path.join(data_dir, 'watchlist.json'), 'watchlist.json')
        radar_data = _load_json(os.path.join(data_dir, 'radar.json'), 'radar.json')

        print(f"\n📝 briefing.json 中无 voiceText，自动拼接播报文稿（fallback 模式）...")
        voice_text = extract_voice_text(briefing_data, markets_data, watchlist_data, radar_data)
        print(f"   播报文稿（{len(voice_text)}字符，预估{len(voice_text) * 60 // 300}秒）")

    # 打印前300字预览
    preview = voice_text[:300] + ('...' if len(voice_text) > 300 else '')
    print(f"   {preview}")

    # 生成音频文件
    audio_filename = f"briefing-{date}.mp3"
    audio_path = os.path.join(data_dir, audio_filename)

    print(f"\n🎵 生成音频...")
    success = call_minimax_tts(voice_text, audio_path)

    if not success:
        print(f"\n❌ 音频生成失败，跳过 audioUrl 写入")
        sys.exit(1)

    # 将音频文件路径写入 briefing.json（本地路径标记，后续上传脚本会替换为云存储 fileID）
    briefing_data['audioFile'] = audio_filename
    briefing_data['voiceText'] = voice_text

    with open(briefing_path, 'w', encoding='utf-8') as f:
        json.dump(briefing_data, f, ensure_ascii=False, indent=2)

    print(f"\n   ✅ briefing.json 已更新：audioFile = {audio_filename}")

    # 总结
    print(f"\n{'=' * 60}")
    print(f"🎉 语音播报生成完成！")
    print(f"   音频文件: {audio_path}")
    print(f"   播报时长: 约 {len(voice_text) * 60 // 300} 秒（估算，按300字/分钟）")
    print(f"   下一步: 运行 upload_to_cloud.py 将音频+数据同步到云端")
    print("=" * 60)


if __name__ == '__main__':
    main()
