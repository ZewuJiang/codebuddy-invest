#!/usr/bin/env python3
"""
投研鸭小程序 — 公式字段自动计算脚本 v3.0
============================================================
核心理念（Harness Engineering v10.0）:
  AI 只需填写原始数值，所有公式/派生计算由本脚本机械执行，
  消除 AI 手算错误的可能性。

v3.0 新增（4/8 基准质量巩固）：
  13. markets + watchlist sparkline[-1] 自动对齐 price（消除偏差>0.5%）
  14. sparkline 尾部方向 vs change 符号矛盾自动修复（调整 spark[-2]）
  15. price="--" 自动从 sparkline[-1] 推导填充

v2.0 新增（v10.0 Harness 升级）：
  7. watchlist metrics[2] 7日涨跌 — 从 sparkline 自动计算
  8. watchlist metrics[3] 30日涨跌 — 从 chartData 自动计算
  9. watchlist metrics[5] 综合评级 — 按 calc_star_rating 规则自动计算
  10. markets.gics[] — 按 change 降序自动排序
  11. 4个JSON的 dataTime — 自动填充当前时间
  12. 4个JSON的 _meta.sourceType — 修正废弃值 refresh_update

v1.0 原有功能：
  1. trafficLights[].status — 按阈值判定 green/yellow/red
  2. riskScore — 30 + Σ(green=0, yellow=10, red=20)，封顶100
  3. riskLevel — 按 riskScore 阈值判定 low/medium/high
  4. sentimentLabel — 按 sentimentScore 查表映射
  5. watchlist.stocks[].metrics[0].value — 与 price 对齐
  6. watchlist.stocks[].metrics[1].value — 与 change 对齐（含正负号+%）

用法:
  python3 auto_compute.py <sync_dir>

退出码:
  0 = 成功
  1 = 文件缺失或JSON语法错误
  2 = 参数错误
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
REFERENCES_DIR = SCRIPT_DIR.parent / "references"
BASELINE_PATH = REFERENCES_DIR / "golden-baseline.json"

BJT = timezone(timedelta(hours=8))


def load_json(filepath):
    """加载并解析 JSON 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"  ❌ 加载失败: {filepath} — {e}")
        return None


def save_json(filepath, data):
    """保存 JSON 文件（保持中文可读）"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def parse_number_from_string(s):
    """从字符串中提取数值（去除 $, %, 逗号, HK$, ¥ 等）"""
    if not isinstance(s, str):
        return None
    cleaned = re.sub(r'[,$%¥\s]', '', s).replace('HK', '').replace('元', '')
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


# ============================================================
# 计算函数（v1.0 原有）
# ============================================================

def compute_traffic_light_status(value_str, thresholds_cfg):
    """根据阈值计算红绿灯 status"""
    value_num = parse_number_from_string(value_str)
    if value_num is None:
        return None

    green_max = thresholds_cfg.get("green_max", 0)
    yellow_max = thresholds_cfg.get("yellow_max", 0)

    if value_num < green_max:
        return "green"
    elif value_num <= yellow_max:
        return "yellow"
    else:
        return "red"


def compute_risk_score(traffic_lights, formula):
    """计算 riskScore = base + Σ(weights)，封顶 cap"""
    base = formula.get("base", 30)
    weights = formula.get("weights", {"green": 0, "yellow": 10, "red": 20})
    cap = formula.get("cap", 100)

    score = base
    for tl in traffic_lights:
        status = tl.get("status", "")
        score += weights.get(status, 0)

    return min(score, cap)


def compute_risk_level(risk_score, formula):
    """根据 riskScore 计算 riskLevel"""
    thresholds = formula.get("levelThresholds", {})
    if risk_score <= thresholds.get("low_max", 44):
        return "low"
    elif risk_score <= thresholds.get("medium_max", 64):
        return "medium"
    else:
        return "high"


def compute_sentiment_label(score, mapping_ranges):
    """根据 sentimentScore 查表映射 sentimentLabel"""
    if not isinstance(score, (int, float)):
        return None
    for r in mapping_ranges:
        if r["min"] <= score <= r["max"]:
            return r["label"]
    return None


def compute_metrics_alignment(stock):
    """对齐 metrics[0] 与 price，metrics[1] 与 change"""
    metrics = stock.get("metrics", [])
    if len(metrics) < 2:
        return False

    price = stock.get("price", "")
    if price and price != "未上市":
        metrics[0]["value"] = price

    change = stock.get("change")
    if isinstance(change, (int, float)):
        sign = "+" if change >= 0 else ""
        metrics[1]["value"] = f"{sign}{change}%"

    return True


# ============================================================
# v2.0 新增计算函数
# ============================================================

def compute_pct_change(data_array, label):
    """从价格数组计算涨跌幅百分比"""
    if not data_array or not isinstance(data_array, list) or len(data_array) < 2:
        return None
    first = data_array[0]
    last = data_array[-1]
    if not isinstance(first, (int, float)) or not isinstance(last, (int, float)):
        return None
    if first == 0:
        return None
    pct = ((last - first) / first) * 100
    return round(pct, 2)


def calc_star_rating(change, pct_30d, rules):
    """按规则计算综合评级星星"""
    if pct_30d is None:
        return "⭐⭐⭐"  # 默认3星

    # 5星：30日涨超+15% 且 单日为正
    if pct_30d > 15 and isinstance(change, (int, float)) and change > 0:
        return "⭐⭐⭐⭐⭐"
    # 4星：30日涨+5%~+15%，或单日涨超+3%
    if 5 <= pct_30d <= 15:
        return "⭐⭐⭐⭐"
    if isinstance(change, (int, float)) and change > 3:
        return "⭐⭐⭐⭐"
    # 3星：30日在-5%~+5%
    if -5 <= pct_30d < 5:
        return "⭐⭐⭐"
    # 2星：30日跌-5%~-15%
    if -15 <= pct_30d < -5:
        return "⭐⭐"
    # 1星：30日跌超-15%
    if pct_30d < -15:
        return "⭐"

    return "⭐⭐⭐"


def compute_extended_metrics(stock, star_rules):
    """v2.0: 自动计算 metrics[2](7日涨跌)、metrics[3](30日涨跌)、metrics[5](综合评级)"""
    metrics = stock.get("metrics", [])
    if len(metrics) < 6:
        return 0

    changes_made = 0
    change = stock.get("change")
    sparkline = stock.get("sparkline", [])
    chart_data = stock.get("chartData", [])

    # metrics[2] = 7日涨跌 — 从 sparkline 计算
    if sparkline and len(sparkline) >= 2:
        pct_7d = compute_pct_change(sparkline, "7日")
        if pct_7d is not None:
            sign = "+" if pct_7d >= 0 else ""
            new_val = f"{sign}{pct_7d}%"
            if metrics[2].get("value") != new_val:
                metrics[2]["value"] = new_val
                changes_made += 1

    # metrics[3] = 30日涨跌 — 从 chartData 计算
    pct_30d = None
    if chart_data and len(chart_data) >= 2:
        pct_30d = compute_pct_change(chart_data, "30日")
        if pct_30d is not None:
            sign = "+" if pct_30d >= 0 else ""
            new_val = f"{sign}{pct_30d}%"
            if metrics[3].get("value") != new_val:
                metrics[3]["value"] = new_val
                changes_made += 1

    # metrics[5] = 综合评级 — 从 change + pct_30d 计算
    if pct_30d is None and metrics[3].get("value"):
        pct_30d = parse_number_from_string(metrics[3].get("value", ""))

    new_rating = calc_star_rating(change, pct_30d, star_rules)
    if metrics[5].get("value") != new_rating:
        old_rating = metrics[5].get("value", "未设置")
        metrics[5]["value"] = new_rating
        changes_made += 1

    return changes_made


def sort_gics_by_change(markets):
    """v2.0: gics[] 按 change 降序排序"""
    gics = markets.get("gics", [])
    if not gics or len(gics) < 2:
        return False

    original_order = [g.get("etf", "") for g in gics]
    gics.sort(key=lambda x: x.get("change", 0), reverse=True)
    new_order = [g.get("etf", "") for g in gics]

    if original_order != new_order:
        markets["gics"] = gics
        return True
    return False


def fix_data_time(data, file_label):
    """v2.0: 自动填充 dataTime 为当前北京时间"""
    now = datetime.now(BJT)
    new_dt = now.strftime("%Y-%m-%d %H:%M BJT")
    old_dt = data.get("dataTime", "")
    if old_dt != new_dt:
        data["dataTime"] = new_dt
        return True
    return False


def fix_generated_at(data, file_label):
    """v2.2: 每次执行都强制更新 _meta.generatedAt 为当前时间（确保前端显示准确）"""
    meta = data.get("_meta", {})
    if not meta:
        return False
    from datetime import datetime, timezone, timedelta
    bjt = timezone(timedelta(hours=8))
    now_bjt = datetime.now(bjt)
    new_val = now_bjt.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    old_val = meta.get("generatedAt", "")
    meta["generatedAt"] = new_val
    if old_val != new_val:
        print(f"  🔄 {file_label}._meta.generatedAt: '{old_val}' → '{new_val}'")
        return True
    return False


def fix_source_type(data, file_label):
    """v2.0: 修正废弃的 sourceType 值"""
    meta = data.get("_meta", {})
    if not meta:
        return False

    old_type = meta.get("sourceType", "")
    deprecated = {"refresh_update"}

    if old_type in deprecated:
        # 根据星期判断应该是哪个
        now = datetime.now(BJT)
        weekday = now.weekday()  # 0=Mon, 6=Sun
        if weekday >= 5:
            meta["sourceType"] = "weekend_insight"
        else:
            meta["sourceType"] = "heavy_analysis"
        # 同时清理废弃字段
        if "refreshCount" in meta:
            del meta["refreshCount"]
        print(f"  🔄 {file_label}._meta.sourceType: '{old_type}' → '{meta['sourceType']}'")
        return True
    return False


# ============================================================
# v3.0 新增：sparkline 对齐 + price 填充 + 方向修复
# ============================================================

def _format_price(value, has_dollar=False, has_pct=False, has_hk=False, has_yen=False):
    """根据原始 price 格式，将数值格式化为对应字符串"""
    if has_pct:
        return f"{value}%"
    if value >= 10000:
        formatted = f"{value:,.0f}"
    elif value >= 100:
        formatted = f"{value:,.2f}"
    else:
        formatted = f"{value:.2f}"
    if has_dollar:
        return f"${formatted}"
    if has_hk:
        return f"HK${formatted}"
    if has_yen:
        return f"¥{formatted}"
    return formatted


def fix_sparkline_alignment(data, file_label, sections):
    """v3.0: markets sparkline[-1]→price对齐 + price='--'填充 + 方向修复"""
    fixes = 0
    for section in sections:
        for item in data.get(section, []):
            spark = item.get("sparkline", [])
            price_str = item.get("price", "")
            change = item.get("change", 0)

            if not spark or len(spark) < 2:
                continue

            # 1) price="--" → 从 sparkline[-1] 推导
            if price_str == "--" and isinstance(spark[-1], (int, float)):
                val = spark[-1]
                item["price"] = _format_price(val)
                print(f"  🔄 {file_label}.{section}[{item.get('name','')}]: price '--' → '{item['price']}' (从sparkline推导)")
                fixes += 1
                price_str = item["price"]

            # 解析price
            price_num = parse_number_from_string(price_str)
            if price_num is None or price_num == 0:
                continue

            # 2) sparkline[-1] 对齐 price（偏差>0.5%时修正）
            last = spark[-1]
            if isinstance(last, (int, float)) and abs(last - price_num) / price_num > 0.005:
                spark[-1] = price_num
                fixes += 1

            # 3) 方向修复：spark[-2] vs spark[-1] 方向应匹配 change
            if len(spark) >= 2 and isinstance(change, (int, float)):
                tail_dir = spark[-1] - spark[-2]
                if abs(change) > 0.5 and abs(tail_dir) / max(abs(spark[-1]), 0.01) > 0.005:
                    if (change > 0 and tail_dir < 0) or (change < 0 and tail_dir > 0):
                        if change > 0:
                            spark[-2] = round(spark[-1] * 0.995, 2)
                        else:
                            spark[-2] = round(spark[-1] * 1.005, 2)
                        fixes += 1

    if fixes > 0:
        print(f"  🔄 {file_label} sparkline: {fixes} 处对齐/方向/price修复")
    else:
        print(f"  ✅ {file_label} sparkline: 全部对齐")
    return fixes


def fix_sparkline_alignment_watchlist(watchlist):
    """v3.0: watchlist sparkline[-1]→price对齐 + 方向修复"""
    fixes = 0
    stocks = watchlist.get("stocks", {})
    for sector_id, stock_list in stocks.items():
        if not isinstance(stock_list, list):
            continue
        for stock in stock_list:
            if stock.get("listed", True) is False:
                continue
            spark = stock.get("sparkline", [])
            price_str = stock.get("price", "")
            change = stock.get("change", 0)

            if not spark or len(spark) < 2 or not price_str or price_str == "未上市":
                continue

            price_num = parse_number_from_string(price_str)
            if price_num is None or price_num == 0:
                continue

            # sparkline[-1] 对齐 price
            last = spark[-1]
            if isinstance(last, (int, float)) and abs(last - price_num) / price_num > 0.005:
                spark[-1] = price_num
                fixes += 1

            # 方向修复
            if len(spark) >= 2 and isinstance(change, (int, float)):
                tail_dir = spark[-1] - spark[-2]
                if abs(change) > 0.5 and abs(tail_dir) / max(abs(spark[-1]), 0.01) > 0.005:
                    if (change > 0 and tail_dir < 0) or (change < 0 and tail_dir > 0):
                        if change > 0:
                            spark[-2] = round(spark[-1] * 0.995, 2)
                        else:
                            spark[-2] = round(spark[-1] * 1.005, 2)
                        fixes += 1

    if fixes > 0:
        print(f"  🔄 watchlist sparkline: {fixes} 处对齐/方向修复")
    else:
        print(f"  ✅ watchlist sparkline: 全部对齐")
    return fixes


# ============================================================
# 主函数
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("用法: python3 auto_compute.py <sync_dir>")
        sys.exit(2)

    sync_dir = sys.argv[1]

    if not os.path.isdir(sync_dir):
        print(f"❌ 目录不存在: {sync_dir}")
        sys.exit(2)

    # 加载基线配置
    baseline = load_json(BASELINE_PATH)
    if not baseline:
        print(f"⚠️  基线文件加载失败: {BASELINE_PATH}，使用默认值")
        baseline = {}

    star_rules = baseline.get("starRatingRules", {}).get("rules", [])

    print(f"\n🔧 auto_compute.py v3.0 — 公式字段自动计算")
    print(f"   目录: {sync_dir}")

    changes_made = 0

    # ── 1. radar.json: trafficLights.status + riskScore + riskLevel ──
    radar_path = os.path.join(sync_dir, "radar.json")
    radar = load_json(radar_path)
    if radar:
        thresholds = baseline.get("trafficLightThresholds", {})
        formula = baseline.get("riskScoreFormula", {})

        # 1a. trafficLights[].status 自动判定
        tl_updated = 0
        for tl in radar.get("trafficLights", []):
            name = tl.get("name", "")
            cfg = thresholds.get(name)
            if cfg:
                new_status = compute_traffic_light_status(tl.get("value", ""), cfg)
                if new_status and new_status != tl.get("status"):
                    old_status = tl.get("status", "未设置")
                    tl["status"] = new_status
                    tl_updated += 1
                    print(f"  🔄 {name}: status {old_status} → {new_status} (value={tl.get('value')})")
                elif new_status:
                    tl["status"] = new_status

        if tl_updated > 0:
            changes_made += tl_updated
            print(f"  ✅ trafficLights: {tl_updated} 项 status 已更新")
        else:
            print(f"  ✅ trafficLights: 全部 status 已正确")

        # 1b. riskScore 自动计算
        new_risk_score = compute_risk_score(radar.get("trafficLights", []), formula)
        old_risk_score = radar.get("riskScore")
        if old_risk_score != new_risk_score:
            radar["riskScore"] = new_risk_score
            changes_made += 1
            print(f"  🔄 riskScore: {old_risk_score} → {new_risk_score}")
        else:
            print(f"  ✅ riskScore: {new_risk_score} (正确)")

        # 1c. riskLevel 自动判定
        new_risk_level = compute_risk_level(new_risk_score, formula)
        old_risk_level = radar.get("riskLevel")
        if old_risk_level != new_risk_level:
            radar["riskLevel"] = new_risk_level
            changes_made += 1
            print(f"  🔄 riskLevel: {old_risk_level} → {new_risk_level}")
        else:
            print(f"  ✅ riskLevel: {new_risk_level} (正确)")

        # v2.0: 修正 sourceType + dataTime
        if fix_generated_at(radar, "radar"):
            changes_made += 1
        if fix_source_type(radar, "radar"):
            changes_made += 1
        if fix_data_time(radar, "radar"):
            changes_made += 1

        save_json(radar_path, radar)
    else:
        print(f"  ⚠️  radar.json 加载失败，跳过")

    # ── 2. briefing.json: sentimentLabel + sourceType + dataTime ──
    briefing_path = os.path.join(sync_dir, "briefing.json")
    briefing = load_json(briefing_path)
    if briefing:
        score = briefing.get("sentimentScore")
        mapping_ranges = baseline.get("sentimentScoreMapping", {}).get("ranges", [])
        new_label = compute_sentiment_label(score, mapping_ranges)

        if new_label:
            old_label = briefing.get("sentimentLabel")
            if old_label != new_label:
                briefing["sentimentLabel"] = new_label
                changes_made += 1
                print(f"  🔄 sentimentLabel: '{old_label}' → '{new_label}' (score={score})")
            else:
                print(f"  ✅ sentimentLabel: '{new_label}' (score={score}, 正确)")

        # v2.0: 修正 sourceType + dataTime
        if fix_generated_at(briefing, "briefing"):
            changes_made += 1
        if fix_source_type(briefing, "briefing"):
            changes_made += 1
        if fix_data_time(briefing, "briefing"):
            changes_made += 1

        # v3.0: coreJudgments[].references 字符串→数组自动修复（前端需要数组）
        for cj in briefing.get("coreJudgments", []):
            refs = cj.get("references", "")
            if isinstance(refs, str) and refs:
                parts = [p.strip() for p in refs.split(";") if p.strip()]
                cj["references"] = [{"name": p, "summary": "", "url": ""} for p in parts]
                changes_made += 1
                print(f"  🔄 coreJudgments references: str → array ({len(parts)} items)")
            elif not refs:
                cj["references"] = []

        # v2.0: 清理 refreshInterval 旧值
        ts = briefing.get("timeStatus", {})
        if ts.get("refreshInterval") and "4小时" in ts.get("refreshInterval", ""):
            ts["refreshInterval"] = "每日更新"
            changes_made += 1
            print(f"  🔄 briefing.timeStatus.refreshInterval: → '每日更新'")

        save_json(briefing_path, briefing)
    else:
        print(f"  ⚠️  briefing.json 加载失败，跳过")

    # ── 3. markets.json: gics排序 + sourceType + dataTime ──
    markets_path = os.path.join(sync_dir, "markets.json")
    markets = load_json(markets_path)
    if markets:
        # v2.0: gics 按 change 降序排序
        if sort_gics_by_change(markets):
            changes_made += 1
            print(f"  🔄 gics[]: 已按 change 降序重排")
        else:
            print(f"  ✅ gics[]: 顺序已正确")

        # v3.0: sparkline[-1] 对齐 price + price="--" 填充 + 方向修复
        spark_fixes = fix_sparkline_alignment(markets, "markets", ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"])
        changes_made += spark_fixes

        # v2.0: 修正 sourceType + dataTime
        if fix_generated_at(markets, "markets"):
            changes_made += 1
        if fix_source_type(markets, "markets"):
            changes_made += 1
        if fix_data_time(markets, "markets"):
            changes_made += 1

        save_json(markets_path, markets)
    else:
        print(f"  ⚠️  markets.json 加载失败，跳过")

    # ── 4. watchlist.json: metrics 全量自动计算 ──
    watchlist_path = os.path.join(sync_dir, "watchlist.json")
    watchlist = load_json(watchlist_path)
    if watchlist:
        metrics_basic_count = 0
        metrics_extended_count = 0
        stocks = watchlist.get("stocks", {})
        for sector_id, stock_list in stocks.items():
            if not isinstance(stock_list, list):
                continue
            for stock in stock_list:
                if stock.get("listed", True) is False:
                    continue
                # v1.0: metrics[0]/[1] 对齐
                if compute_metrics_alignment(stock):
                    metrics_basic_count += 1
                # v2.0: metrics[2]/[3]/[5] 自动计算
                ext_changes = compute_extended_metrics(stock, star_rules)
                if ext_changes > 0:
                    metrics_extended_count += ext_changes

        if metrics_basic_count > 0:
            print(f"  ✅ watchlist metrics[0]/[1]: {metrics_basic_count} 只标的已对齐")
        if metrics_extended_count > 0:
            changes_made += metrics_extended_count
            print(f"  🔄 watchlist metrics[2]/[3]/[5]: {metrics_extended_count} 处已自动计算")
        else:
            print(f"  ✅ watchlist metrics[2]/[3]/[5]: 全部已正确")

        # v3.0: watchlist sparkline[-1] 对齐 price + 方向修复
        wl_spark_fixes = fix_sparkline_alignment_watchlist(watchlist)
        changes_made += wl_spark_fixes

        # v2.0: 修正 sourceType + dataTime
        if fix_generated_at(watchlist, "watchlist"):
            changes_made += 1
        if fix_source_type(watchlist, "watchlist"):
            changes_made += 1
        if fix_data_time(watchlist, "watchlist"):
            changes_made += 1

        save_json(watchlist_path, watchlist)
    else:
        print(f"  ⚠️  watchlist.json 加载失败，跳过")

    # ── 总结 ──
    print(f"\n{'='*50}")
    if changes_made > 0:
        print(f"  🔧 共修正 {changes_made} 处公式/派生字段")
    else:
        print(f"  ✅ 所有公式字段已正确，无需修正")
    print(f"{'='*50}\n")

    sys.exit(0)


if __name__ == "__main__":
    main()
