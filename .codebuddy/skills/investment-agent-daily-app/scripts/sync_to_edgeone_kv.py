#!/usr/bin/env python3
"""
sync_to_edgeone_kv.py — 将每日产出数据同步到 EdgeOne Pages KV 存储
通过调用 /api/sync 端点推送数据

用法:
    python3 sync_to_edgeone_kv.py <miniapp_sync_dir> <date> [--api-url URL] [--token TOKEN]

示例:
    python3 sync_to_edgeone_kv.py \
        "/Users/zewujiang/Desktop/AICo/codebuddy-invest/workflows/investment_agent_data/miniapp_sync/" \
        "2026-04-08"
"""

import json
import sys
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

# ── 配置 ───────────────────────────────────────────────────
# EdgeOne Pages 部署后的 URL（部署后替换为实际域名）
DEFAULT_API_URL = os.environ.get(
    'TOUYANDUCK_API_URL',
    'https://touyanduck-api.edgeone.run'
)

# 同步鉴权 Token（和 sync.js 中的 DEFAULT_TOKEN 保持一致）
DEFAULT_SYNC_TOKEN = os.environ.get(
    'TOUYANDUCK_SYNC_TOKEN',
    'touyanduck-sync-2026'
)

# briefing.md 的位置
PROJECT_DIR = Path(__file__).resolve().parent.parent.parent.parent  # 项目根目录


def load_json(filepath):
    """加载 JSON 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_text(filepath):
    """加载文本文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def sync_to_kv(sync_dir, date, api_url=None, token=None):
    """
    将数据同步到 EdgeOne Pages KV

    参数:
        sync_dir: miniapp_sync 目录路径
        date: 日期字符串 (YYYY-MM-DD)
        api_url: EdgeOne Pages API URL
        token: 同步鉴权 Token
    """
    api_url = api_url or DEFAULT_API_URL
    token = token or DEFAULT_SYNC_TOKEN
    sync_path = Path(sync_dir)

    print(f"📦 开始同步 {date} 的数据到 EdgeOne Pages KV...")
    print(f"   数据目录: {sync_path}")
    print(f"   API URL: {api_url}")

    # 加载 4 个 JSON
    briefing_path = sync_path / 'briefing.json'
    markets_path = sync_path / 'markets.json'
    radar_path = sync_path / 'radar.json'
    watchlist_path = sync_path / 'watchlist.json'

    if not briefing_path.exists():
        print(f"❌ 错误: {briefing_path} 不存在")
        sys.exit(1)

    payload = {
        'date': date,
        'briefing': load_json(briefing_path),
    }

    if markets_path.exists():
        payload['markets'] = load_json(markets_path)
        print(f"   ✅ markets.json 已加载")
    else:
        print(f"   ⚠️ markets.json 不存在，跳过")

    if radar_path.exists():
        payload['radar'] = load_json(radar_path)
        print(f"   ✅ radar.json 已加载")
    else:
        print(f"   ⚠️ radar.json 不存在，跳过")

    if watchlist_path.exists():
        payload['watchlist'] = load_json(watchlist_path)
        print(f"   ✅ watchlist.json 已加载")
    else:
        print(f"   ⚠️ watchlist.json 不存在，跳过")

    # 加载 briefing.md
    md_path = PROJECT_DIR / 'touyanduck-api' / 'api' / 'latest' / 'briefing.md'
    if md_path.exists():
        payload['briefingMd'] = load_text(md_path)
        print(f"   ✅ briefing.md 已加载 ({md_path.stat().st_size} bytes)")
    else:
        print(f"   ⚠️ briefing.md 不存在: {md_path}")

    print(f"   📊 Payload 大小: {len(json.dumps(payload, ensure_ascii=False)) / 1024:.1f} KB")

    # 发送 POST 请求到 /api/sync
    sync_url = f"{api_url.rstrip('/')}/api/sync"
    data = json.dumps(payload, ensure_ascii=False).encode('utf-8')

    req = urllib.request.Request(
        sync_url,
        data=data,
        headers={
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {token}',
        },
        method='POST',
    )

    try:
        print(f"\n🚀 正在推送到 {sync_url}...")
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            print(f"✅ 同步成功!")
            print(f"   日期: {result.get('date', 'N/A')}")
            print(f"   写入 KV 键数: {result.get('kvKeysWritten', 'N/A')}")
            print(f"   历史日期总数: {result.get('totalDates', 'N/A')}")
            print(f"   消息: {result.get('message', 'N/A')}")
            return True

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8') if e.fp else 'N/A'
        print(f"❌ HTTP 错误 {e.code}: {error_body}")
        return False

    except urllib.error.URLError as e:
        print(f"❌ 连接失败: {e.reason}")
        print(f"   提示: 请确认 EdgeOne Pages 已部署且 URL 正确")
        return False

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def main():
    if len(sys.argv) < 3:
        print("用法: python3 sync_to_edgeone_kv.py <miniapp_sync_dir> <date> [--api-url URL] [--token TOKEN]")
        print("示例: python3 sync_to_edgeone_kv.py ./workflows/investment_agent_data/miniapp_sync/ 2026-04-08")
        sys.exit(1)

    sync_dir = sys.argv[1]
    date = sys.argv[2]

    # 解析可选参数
    api_url = None
    token = None

    i = 3
    while i < len(sys.argv):
        if sys.argv[i] == '--api-url' and i + 1 < len(sys.argv):
            api_url = sys.argv[i + 1]
            i += 2
        elif sys.argv[i] == '--token' and i + 1 < len(sys.argv):
            token = sys.argv[i + 1]
            i += 2
        else:
            i += 1

    # 验证日期格式
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        print(f"❌ 日期格式错误: {date}，请使用 YYYY-MM-DD 格式")
        sys.exit(1)

    success = sync_to_kv(sync_dir, date, api_url, token)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
