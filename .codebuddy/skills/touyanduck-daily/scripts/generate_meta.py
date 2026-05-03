#!/usr/bin/env python3
"""
generate_meta.py — 投研鸭 EdgeOne Pages 元数据生成器 v1.0

生成 meta.json，告诉 ClawHub Skill 消费者这份数据的版本、时效和来源信息。

用法：
    python3 generate_meta.py <日期YYYY-MM-DD> <输出目录>

示例：
    python3 generate_meta.py 2026-04-07 /path/to/touyanduck-api/api/latest/
"""

import sys
import os
import json
from datetime import datetime, timezone, timedelta


def generate_meta(date_str: str, output_dir: str):
    """生成 meta.json 文件"""

    # 北京时间
    bj_tz = timezone(timedelta(hours=8))
    now_bj = datetime.now(bj_tz)

    # 检查 4 个数据文件是否存在
    collections = ["briefing", "markets", "watchlist", "radar"]
    available = []
    total_size_kb = 0

    for name in collections:
        filepath = os.path.join(output_dir, f"{name}.json")
        if os.path.exists(filepath):
            available.append(name)
            total_size_kb += os.path.getsize(filepath) / 1024

    meta = {
        "version": "7.1",
        "date": date_str,
        "updatedAt": now_bj.strftime("%Y-%m-%dT%H:%M:%S+08:00"),
        "sourceType": "heavy_analysis",
        "refreshInterval": "每工作日更新（日内可手动刷新）",
        "collections": available,
        "collectionsCount": len(available),
        "totalSizeKB": round(total_size_kb, 1),
        "skillVersion": "v7.1",
        "author": "投研鸭 touyanduck",
        "description": "二级市场每日策略简报 — 覆盖美股/M7/GICS/亚太/大宗/加密/聪明钱/AI产业链",
        "qualityChecks": [
            "八大铁律",
            "29条致命错误零容忍",
            "14项JSON完整性终审",
            "Top10快速终审"
        ],
        "dataSources": [
            "Google Finance",
            "AkShare",
            "英为财情",
            "OilPrice.com",
            "FRED",
            "CoinGecko"
        ],
        "disclaimer": "本数据仅供投资参考，不构成投资建议。数据虽经严格审核，仍可能存在延迟或偏差。"
    }

    # 写入文件
    output_path = os.path.join(output_dir, "meta.json")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"   ✅ meta.json 生成成功")
    print(f"      日期: {date_str}")
    print(f"      更新时间: {meta['updatedAt']}")
    print(f"      可用集合: {', '.join(available)} ({len(available)}/4)")
    print(f"      总数据量: {meta['totalSizeKB']} KB")

    return meta


def main():
    if len(sys.argv) < 3:
        print("用法: python3 generate_meta.py <日期YYYY-MM-DD> <输出目录>")
        print("示例: python3 generate_meta.py 2026-04-07 ./touyanduck-api/api/latest/")
        sys.exit(1)

    date_str = sys.argv[1]
    output_dir = sys.argv[2]

    if not os.path.isdir(output_dir):
        print(f"❌ 输出目录不存在: {output_dir}")
        sys.exit(1)

    generate_meta(date_str, output_dir)


if __name__ == '__main__':
    main()
