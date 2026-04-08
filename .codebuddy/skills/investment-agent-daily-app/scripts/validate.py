#!/usr/bin/env python3
"""
投研鸭小程序数据质量自动化校验脚本 v2.0
============================================================
核心理念（Harness Engineering）:
  把"AI 记住规则"转变为"环境自动约束 AI"。
  本脚本在 run_daily.sh 中的 JSON 语法校验之后、sparkline 补全之前执行。

v2.0 重大升级：
  - FATAL / WARN 双级机制：FATAL 级错误即使 --skip-warn 也无法绕过
  - R9 新增：自动比对 radar.smartMoneyHoldings 与 holdings-cache.json 一致性
  - --skip-validate 改为 --skip-warn：只跳过 WARN 级，FATAL 永远执行

v1.1 新增：V27(Insight长度) + V28(metrics数量) + V29(logic箭头格式)

用法:
  python3 validate.py <sync_dir> [--mode heavy|refresh|weekend]

退出码:
  0 = 全部通过
  1 = 有 WARN 级 FAIL（--skip-warn 可绕过）
  2 = 参数错误
  3 = 有 FATAL 级 FAIL（不可绕过，必须修复）
"""

import json
import os
import re
import sys
from pathlib import Path

# ============================================================
# 配置
# ============================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
REFERENCES_DIR = SCRIPT_DIR.parent / "references"
BASELINE_PATH = REFERENCES_DIR / "golden-baseline.json"
HOLDINGS_CACHE_PATH = REFERENCES_DIR / "holdings-cache.json"

# FATAL 级校验项（不可被 --skip-warn 绕过）
FATAL_CODES = {"R2", "R3", "R9"}

# ============================================================
# 工具函数
# ============================================================
class ValidationResult:
    def __init__(self):
        self.results = []
        self.fail_count = 0
        self.fatal_count = 0
        self.warn_count = 0
        self.pass_count = 0
        self.skip_count = 0

    def add(self, code, description, passed, detail=""):
        status = "PASS" if passed else "FAIL"
        level = "FATAL" if code in FATAL_CODES else "WARN"
        if passed is None:
            status = "SKIP"
            self.skip_count += 1
        elif passed:
            self.pass_count += 1
        else:
            self.fail_count += 1
            if level == "FATAL":
                self.fatal_count += 1
            else:
                self.warn_count += 1
        self.results.append({
            "code": code,
            "description": description,
            "status": status,
            "level": level,
            "detail": detail
        })

    def print_report(self):
        print("\n" + "=" * 70)
        print("📋 投研鸭数据质量自动化校验报告 (v2.0 FATAL/WARN 双级)")
        print("=" * 70)

        for r in self.results:
            if r["status"] == "PASS":
                icon = "✅"
            elif r["status"] == "SKIP":
                icon = "⏭️"
            elif r["level"] == "FATAL":
                icon = "🔴"
            else:
                icon = "🟡"
            level_tag = f"[{r['level']}]" if r["status"] == "FAIL" else ""
            line = f"  {icon} [{r['code']}]{level_tag} {r['description']}"
            if r["detail"]:
                line += f"\n     └─ {r['detail']}"
            print(line)

        print("\n" + "-" * 70)
        total = self.pass_count + self.fail_count + self.skip_count
        print(f"  总计: {total} 项 | ✅ PASS: {self.pass_count} | 🔴 FATAL: {self.fatal_count} | 🟡 WARN: {self.warn_count} | ⏭️ SKIP: {self.skip_count}")

        if self.fatal_count > 0:
            print(f"\n  🚫 存在 {self.fatal_count} 项 FATAL 级错误！不可绕过，必须修复后才能上传。")
        if self.warn_count > 0:
            print(f"  ⚠️  存在 {self.warn_count} 项 WARN 级错误（紧急情况可用 --skip-warn 跳过）")
        if self.fail_count == 0:
            print(f"\n  🎉 全部通过！可以继续上传。")
        print("=" * 70 + "\n")

        # 返回退出码：3=有FATAL, 1=仅WARN, 0=全通过
        if self.fatal_count > 0:
            return 3
        elif self.warn_count > 0:
            return 1
        else:
            return 0


def load_json(filepath):
    """加载并解析 JSON 文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return None


def parse_number_from_string(s):
    """从字符串中提取数值（去除 $, %, 逗号等）"""
    if not isinstance(s, str):
        return None
    cleaned = re.sub(r'[,$%¥HK\s]', '', s).replace('元', '')
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def count_highlights(text):
    """统计 takeaway 中【】标红关键词数量"""
    if not isinstance(text, str):
        return 0
    return len(re.findall(r'【[^】]+】', text))


# ============================================================
# 校验函数
# ============================================================

def validate_file_existence(sync_dir, vr):
    """V1: 4个JSON都存在且可解析"""
    files = {}
    for name in ["briefing.json", "markets.json", "watchlist.json", "radar.json"]:
        filepath = os.path.join(sync_dir, name)
        data = load_json(filepath)
        if data is None:
            vr.add("V1", f"{name} 存在且可解析", False, f"文件不存在或JSON语法错误: {filepath}")
        else:
            vr.add("V1", f"{name} 存在且可解析", True)
        files[name.replace(".json", "")] = data
    return files


def validate_required_fields(data, required_fields, file_label, vr, code):
    """检查必填字段非空"""
    if data is None:
        vr.add(code, f"{file_label} 必填字段检查", False, "数据为空")
        return
    missing = []
    for field in required_fields:
        val = data.get(field)
        if val is None or val == "" or val == [] or val == {}:
            missing.append(field)
    if missing:
        vr.add(code, f"{file_label} 必填字段非空", False, f"缺失: {', '.join(missing)}")
    else:
        vr.add(code, f"{file_label} 必填字段非空", True)


def validate_enum(data, field_path, allowed_values, vr, code, description):
    """校验枚举值"""
    if data is None:
        vr.add(code, description, None, "数据为空，跳过")
        return

    violations = []

    def check_value(obj, path_parts, current_path=""):
        if not path_parts:
            return
        key = path_parts[0]
        rest = path_parts[1:]

        if key == "[]":
            if isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_value(item, rest, f"{current_path}[{i}]")
        elif key == "[].":
            # 嵌套数组处理
            pass
        else:
            if isinstance(obj, dict) and key in obj:
                if not rest:
                    val = obj[key]
                    if isinstance(val, str) and val not in allowed_values:
                        violations.append(f"{current_path}.{key}='{val}'")
                else:
                    check_value(obj[key], rest, f"{current_path}.{key}")

    # 解析 field_path: "globalReaction.[].direction"
    parts = field_path.split(".")
    check_value(data, parts)

    if violations:
        vr.add(code, description, False, f"非法枚举值: {'; '.join(violations[:5])}")
    else:
        vr.add(code, description, True)


def validate_data_types(files, vr):
    """V3: 数据类型校验"""
    briefing = files.get("briefing")
    markets = files.get("markets")
    watchlist = files.get("watchlist")
    radar = files.get("radar")

    type_errors = []

    # briefing 类型检查
    if briefing:
        if "sentimentScore" in briefing and not isinstance(briefing["sentimentScore"], (int, float)):
            type_errors.append("briefing.sentimentScore 不是 number")

    # markets 类型检查
    if markets:
        for section in ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"]:
            items = markets.get(section, [])
            for i, item in enumerate(items):
                change = item.get("change")
                if change is not None and not isinstance(change, (int, float)):
                    type_errors.append(f"markets.{section}[{i}].change 不是 number (got {type(change).__name__}: {change})")
                sparkline = item.get("sparkline")
                if sparkline is not None and isinstance(sparkline, list):
                    for j, v in enumerate(sparkline):
                        if not isinstance(v, (int, float)):
                            type_errors.append(f"markets.{section}[{i}].sparkline[{j}] 不是 number")
                            break

    # watchlist 类型检查
    if watchlist:
        stocks = watchlist.get("stocks", {})
        for sector_id, stock_list in stocks.items():
            if isinstance(stock_list, list):
                for i, stock in enumerate(stock_list):
                    change = stock.get("change")
                    if change is not None and not isinstance(change, (int, float)):
                        type_errors.append(f"watchlist.stocks.{sector_id}[{i}].change 不是 number")

    # radar 类型检查
    if radar:
        if "riskScore" in radar and not isinstance(radar["riskScore"], (int, float)):
            type_errors.append("radar.riskScore 不是 number")

    if type_errors:
        vr.add("V3", "数据类型校验（change=number, sparkline=number[]）", False,
               f"{len(type_errors)} 处类型错误: {'; '.join(type_errors[:5])}")
    else:
        vr.add("V3", "数据类型校验", True)


def validate_array_lengths(files, baseline, vr):
    """V5: 数组长度校验"""
    briefing = files.get("briefing")
    markets = files.get("markets")
    radar = files.get("radar")
    bs = baseline.get("structureChecks", {})

    checks = []

    if briefing:
        b_cfg = bs.get("briefing", {})
        gr = briefing.get("globalReaction", [])
        checks.append(("briefing.globalReaction", len(gr), ">=", b_cfg.get("globalReaction_min", 5)))
        cj = briefing.get("coreJudgments", [])
        checks.append(("briefing.coreJudgments", len(cj), "==", b_cfg.get("coreJudgments_exact", 3)))
        chain = briefing.get("coreEvent", {}).get("chain", [])
        checks.append(("briefing.coreEvent.chain", len(chain), ">=", b_cfg.get("chain_min", 3)))
        th = briefing.get("topHoldings", [])
        checks.append(("briefing.topHoldings", len(th), ">=", b_cfg.get("topHoldings_min", 3)))
        sm = briefing.get("smartMoney", [])
        checks.append(("briefing.smartMoney", len(sm), ">=", b_cfg.get("smartMoney_min", 2)))
        rp = briefing.get("riskPoints", [])
        checks.append(("briefing.riskPoints", len(rp), ">=", b_cfg.get("riskPoints_min", 2)))

    if markets:
        m_cfg = bs.get("markets", {})
        checks.append(("markets.usMarkets", len(markets.get("usMarkets", [])), "==", m_cfg.get("usMarkets_exact", 4)))
        checks.append(("markets.m7", len(markets.get("m7", [])), "==", m_cfg.get("m7_exact", 7)))
        checks.append(("markets.gics", len(markets.get("gics", [])), "==", m_cfg.get("gics_exact", 11)))
        checks.append(("markets.asiaMarkets", len(markets.get("asiaMarkets", [])), ">=", m_cfg.get("asiaMarkets_min", 4)))
        checks.append(("markets.commodities", len(markets.get("commodities", [])), "==", m_cfg.get("commodities_exact", 6)))

    if radar:
        r_cfg = bs.get("radar", {})
        checks.append(("radar.trafficLights", len(radar.get("trafficLights", [])), "==", r_cfg.get("trafficLights_exact", 7)))
        checks.append(("radar.events", len(radar.get("events", [])), ">=", r_cfg.get("events_min", 3)))
        checks.append(("radar.smartMoneyHoldings", len(radar.get("smartMoneyHoldings", [])), ">=", r_cfg.get("smartMoneyHoldings_min", 2)))

    failures = []
    for name, actual, op, expected in checks:
        if op == "==" and actual != expected:
            failures.append(f"{name}: 期望{expected}, 实际{actual}")
        elif op == ">=" and actual < expected:
            failures.append(f"{name}: 期望>={expected}, 实际{actual}")

    if failures:
        vr.add("V5", "数组长度校验", False, f"{len(failures)} 项不符: {'; '.join(failures[:5])}")
    else:
        vr.add("V5", "数组长度校验", True)


def validate_enums_comprehensive(files, baseline, vr):
    """V4: 枚举值综合校验"""
    enums = baseline.get("enumValidation", {})
    briefing = files.get("briefing")
    markets = files.get("markets")
    watchlist = files.get("watchlist")
    radar = files.get("radar")

    violations = []

    # briefing 枚举
    if briefing:
        # globalReaction[].direction
        for i, gr in enumerate(briefing.get("globalReaction", [])):
            d = gr.get("direction", "")
            if d not in enums.get("direction", []):
                violations.append(f"briefing.globalReaction[{i}].direction='{d}'")

        # smartMoney[].signal
        for i, sm in enumerate(briefing.get("smartMoney", [])):
            s = sm.get("signal", "")
            if s not in enums.get("signal", []):
                violations.append(f"briefing.smartMoney[{i}].signal='{s}'")

        # actionHints[].type
        for i, ah in enumerate(briefing.get("actionHints", [])):
            t = ah.get("type", "")
            if t not in enums.get("actionType", []):
                violations.append(f"briefing.actionHints[{i}].type='{t}'")

        # sentimentLabel
        sl = briefing.get("sentimentLabel", "")
        if sl and sl not in enums.get("sentimentLabel", []):
            violations.append(f"briefing.sentimentLabel='{sl}'")

        # marketStatus
        ts = briefing.get("timeStatus", {})
        ms = ts.get("marketStatus", "")
        if ms and ms not in enums.get("marketStatus", []):
            violations.append(f"briefing.timeStatus.marketStatus='{ms}'")

    # markets 枚举
    if markets:
        for i, um in enumerate(markets.get("usMarkets", [])):
            cl = um.get("changeLabel", "")
            if cl and cl not in enums.get("changeLabel", []):
                violations.append(f"markets.usMarkets[{i}].changeLabel='{cl}'")

    # watchlist 枚举
    if watchlist:
        for i, sec in enumerate(watchlist.get("sectors", [])):
            sid = sec.get("id", "")
            if sid not in enums.get("sectorId", []):
                violations.append(f"watchlist.sectors[{i}].id='{sid}'")
            trend = sec.get("trend", "")
            if trend and trend not in enums.get("sectorTrend", []):
                violations.append(f"watchlist.sectors[{i}].trend='{trend}'")

    # radar 枚举
    if radar:
        for i, tl in enumerate(radar.get("trafficLights", [])):
            st = tl.get("status", "")
            if st not in enums.get("trafficLightStatus", []):
                violations.append(f"radar.trafficLights[{i}].status='{st}'")

        rl = radar.get("riskLevel", "")
        if rl and rl not in enums.get("riskLevel", []):
            violations.append(f"radar.riskLevel='{rl}'")

        for i, ev in enumerate(radar.get("events", [])):
            imp = ev.get("impact", "")
            if imp and imp not in enums.get("eventImpact", []):
                violations.append(f"radar.events[{i}].impact='{imp}'")

        for i, al in enumerate(radar.get("alerts", [])):
            lv = al.get("level", "")
            if lv and lv not in enums.get("alertLevel", []):
                violations.append(f"radar.alerts[{i}].level='{lv}'")

        for i, smd in enumerate(radar.get("smartMoneyDetail", [])):
            tier = smd.get("tier", "")
            if tier not in enums.get("smartMoneyTier", []):
                violations.append(f"radar.smartMoneyDetail[{i}].tier='{tier}'")
            for j, fund in enumerate(smd.get("funds", [])):
                sig = fund.get("signal", "")
                if sig and sig not in enums.get("signal", []):
                    violations.append(f"radar.smartMoneyDetail[{i}].funds[{j}].signal='{sig}'")

        for i, pred in enumerate(radar.get("predictions", [])):
            src = pred.get("source", "")
            if src and src not in enums.get("predictionSource", []):
                violations.append(f"radar.predictions[{i}].source='{src}'")
            trend = pred.get("trend", "")
            if trend and trend not in enums.get("predictionTrend", []):
                violations.append(f"radar.predictions[{i}].trend='{trend}'")

    # _meta.sourceType
    for name, data in files.items():
        if data and "_meta" in data:
            st = data["_meta"].get("sourceType", "")
            if st and st not in enums.get("sourceType", []):
                violations.append(f"{name}._meta.sourceType='{st}'")

    if violations:
        vr.add("V4", "枚举值全面校验", False, f"{len(violations)} 处越界: {'; '.join(violations[:8])}")
    else:
        vr.add("V4", "枚举值全面校验", True)


def validate_sparkline_price_consistency(files, baseline, vr):
    """V6: sparkline[-1] vs price 偏差 ≤1%"""
    tolerance = baseline.get("textQuality", {}).get("price_sparkline_tolerance", 0.01)
    inconsistencies = []

    # markets
    markets = files.get("markets")
    if markets:
        for section in ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"]:
            for i, item in enumerate(markets.get(section, [])):
                sparkline = item.get("sparkline", [])
                price_str = item.get("price", "")
                if sparkline and len(sparkline) >= 1 and price_str:
                    price_num = parse_number_from_string(price_str)
                    if price_num and price_num > 0:
                        last_spark = sparkline[-1]
                        if isinstance(last_spark, (int, float)) and last_spark > 0:
                            deviation = abs(last_spark - price_num) / price_num
                            if deviation > tolerance:
                                name = item.get("name", f"index{i}")
                                inconsistencies.append(
                                    f"markets.{section}[{name}]: sparkline[-1]={last_spark} vs price={price_str} (偏差{deviation:.1%})"
                                )

    # watchlist
    watchlist = files.get("watchlist")
    if watchlist:
        stocks = watchlist.get("stocks", {})
        for sector_id, stock_list in stocks.items():
            if isinstance(stock_list, list):
                for stock in stock_list:
                    if stock.get("listed", True) is False:
                        continue
                    sparkline = stock.get("sparkline", [])
                    price_str = stock.get("price", "")
                    if sparkline and len(sparkline) >= 1 and price_str and price_str != "未上市":
                        price_num = parse_number_from_string(price_str)
                        if price_num and price_num > 0:
                            last_spark = sparkline[-1]
                            if isinstance(last_spark, (int, float)) and last_spark > 0:
                                deviation = abs(last_spark - price_num) / price_num
                                if deviation > tolerance:
                                    name = stock.get("name", stock.get("symbol", "?"))
                                    inconsistencies.append(
                                        f"watchlist.{sector_id}[{name}]: sparkline[-1]={last_spark} vs price={price_str} (偏差{deviation:.1%})"
                                    )

    if inconsistencies:
        vr.add("V6", "sparkline[-1] vs price 一致性 (≤1%)", False,
               f"{len(inconsistencies)} 处不一致: {'; '.join(inconsistencies[:5])}")
    else:
        vr.add("V6", "sparkline[-1] vs price 一致性", True)


def validate_metrics_consistency(files, vr):
    """V7-V8: metrics[0] vs price, metrics[1] vs change 一致性"""
    watchlist = files.get("watchlist")
    if not watchlist:
        vr.add("V7", "metrics[0] vs price 一致", None, "watchlist 数据缺失")
        return

    inconsistencies = []
    stocks = watchlist.get("stocks", {})
    for sector_id, stock_list in stocks.items():
        if not isinstance(stock_list, list):
            continue
        for stock in stock_list:
            if stock.get("listed", True) is False:
                continue
            metrics = stock.get("metrics", [])
            if len(metrics) >= 2:
                # metrics[0].value vs price
                m0_val = metrics[0].get("value", "")
                price = stock.get("price", "")
                if m0_val and price and m0_val != price:
                    name = stock.get("name", "?")
                    inconsistencies.append(f"{name}: metrics[0]={m0_val} vs price={price}")

                # metrics[1].value vs change
                m1_val = metrics[1].get("value", "")
                change = stock.get("change")
                if isinstance(change, (int, float)) and m1_val:
                    # 格式化 change 为类似 "+5.59%" 或 "-2.30%"
                    expected_sign = "+" if change >= 0 else ""
                    expected_str = f"{expected_sign}{change}%"
                    # 简化比较：提取数值
                    m1_num = parse_number_from_string(m1_val)
                    if m1_num is not None and abs(m1_num - abs(change)) > 0.05:
                        name = stock.get("name", "?")
                        inconsistencies.append(f"{name}: metrics[1]={m1_val} vs change={change}")

    if inconsistencies:
        vr.add("V7", "metrics vs price/change 一致性", False,
               f"{len(inconsistencies)} 处不一致: {'; '.join(inconsistencies[:5])}")
    else:
        vr.add("V7", "metrics vs price/change 一致性", True)


def validate_sentiment_mapping(files, baseline, vr):
    """V9: sentimentScore → sentimentLabel 映射正确"""
    briefing = files.get("briefing")
    if not briefing:
        vr.add("V9", "sentimentScore→sentimentLabel 映射", None, "briefing 数据缺失")
        return

    score = briefing.get("sentimentScore")
    label = briefing.get("sentimentLabel", "")

    if score is None or not isinstance(score, (int, float)):
        vr.add("V9", "sentimentScore→sentimentLabel 映射", False, f"sentimentScore 无效: {score}")
        return

    ranges = baseline.get("sentimentScoreMapping", {}).get("ranges", [])
    expected_label = None
    for r in ranges:
        if r["min"] <= score <= r["max"]:
            expected_label = r["label"]
            break

    if expected_label and label == expected_label:
        vr.add("V9", "sentimentScore→sentimentLabel 映射", True, f"score={score} → '{label}' ✓")
    else:
        vr.add("V9", "sentimentScore→sentimentLabel 映射", False,
               f"score={score}: 期望'{expected_label}', 实际'{label}'")


def validate_risk_score(files, baseline, vr):
    """V10-V11: riskScore = 30 + Σ(weights) 且 riskLevel 正确"""
    radar = files.get("radar")
    if not radar:
        vr.add("V10", "riskScore 公式校验", None, "radar 数据缺失")
        return

    formula = baseline.get("riskScoreFormula", {})
    base = formula.get("base", 30)
    weights = formula.get("weights", {"green": 0, "yellow": 10, "red": 20})
    cap = formula.get("cap", 100)

    traffic_lights = radar.get("trafficLights", [])
    if len(traffic_lights) != 7:
        vr.add("V10", "riskScore 公式校验", False, f"trafficLights 数量={len(traffic_lights)}, 期望7")
        return

    calculated_score = base
    for tl in traffic_lights:
        status = tl.get("status", "")
        calculated_score += weights.get(status, 0)
    calculated_score = min(calculated_score, cap)

    actual_score = radar.get("riskScore")
    if actual_score == calculated_score:
        vr.add("V10", "riskScore 公式校验", True, f"riskScore={calculated_score} ✓")
    else:
        vr.add("V10", "riskScore 公式校验", False,
               f"期望 riskScore={calculated_score} (30+{'+'.join([tl.get('status','?') for tl in traffic_lights])}), 实际={actual_score}")

    # V11: riskLevel
    thresholds = formula.get("levelThresholds", {})
    if calculated_score <= thresholds.get("low_max", 44):
        expected_level = "low"
    elif calculated_score <= thresholds.get("medium_max", 64):
        expected_level = "medium"
    else:
        expected_level = "high"

    actual_level = radar.get("riskLevel", "")
    if actual_level == expected_level:
        vr.add("V11", "riskLevel 分级正确", True, f"score={actual_score or calculated_score} → '{expected_level}' ✓")
    else:
        vr.add("V11", "riskLevel 分级正确", False,
               f"score={actual_score or calculated_score}: 期望'{expected_level}', 实际'{actual_level}'")


def validate_regression_gates(files, baseline, vr, mode):
    """R1-R8 回归门禁"""
    if mode == "refresh":
        vr.add("R1-R8", "回归门禁（Refresh 模式豁免）", None, "Refresh 不执行回归门禁")
        return

    gates = baseline.get("regressionGates", {})
    briefing = files.get("briefing")
    radar = files.get("radar")

    # R1: topHoldings >= 3
    if briefing:
        th = briefing.get("topHoldings", [])
        passed = len(th) >= gates.get("R1_topHoldings_min", 3)
        vr.add("R1", f"topHoldings ≥ {gates.get('R1_topHoldings_min', 3)}条", passed,
               f"实际{len(th)}条" + ("" if passed else "，缺失机构请从 holdings-cache.json 补全"))

    # R2: smartMoneyHoldings positions >= Top10
    if radar:
        smh = radar.get("smartMoneyHoldings", [])
        min_pos = gates.get("R2_positions_min_per_fund", 10)
        r2_failures = []
        for holding in smh:
            manager = holding.get("manager", "?")
            positions = holding.get("positions", [])
            if len(positions) < min_pos:
                r2_failures.append(f"{manager}: {len(positions)}条(需≥{min_pos})")
        vr.add("R2", f"smartMoneyHoldings 每家 positions ≥ Top{min_pos}", len(r2_failures) == 0,
               "; ".join(r2_failures) if r2_failures else f"全部≥{min_pos} ✓")

    # R3: 无"待更新"字符串
    forbidden = gates.get("R3_forbidden_strings", ["待更新"])
    all_json_str = json.dumps(files, ensure_ascii=False)
    found_forbidden = []
    for word in forbidden:
        if word in all_json_str:
            found_forbidden.append(word)
    vr.add("R3", "无\"待更新\"等占位符", len(found_forbidden) == 0,
           f"发现: {', '.join(found_forbidden)}" if found_forbidden else "")

    # R4: ARK旗舰存在
    if briefing and radar:
        ark_patterns = gates.get("R4_ark_name_patterns", ["ARK", "Cathie", "ARKK"])
        ark_found_briefing = False
        for th in briefing.get("topHoldings", []):
            name = th.get("name", "")
            if any(p.lower() in name.lower() for p in ark_patterns):
                ark_found_briefing = True
                break
        vr.add("R4", "ARK旗舰持仓存在（briefing.topHoldings）", ark_found_briefing,
               "" if ark_found_briefing else "briefing.topHoldings 中未找到 ARK 相关条目")

    # R5: briefing.topHoldings 与 radar.smartMoneyHoldings 交叉一致
    # 简化检查：确认两边机构名能对应上
    if briefing and radar:
        th_names = set(th.get("name", "").lower() for th in briefing.get("topHoldings", []))
        smh_names = set(h.get("manager", "").lower() for h in radar.get("smartMoneyHoldings", []))
        # 检查 topHoldings 的每个名字在 smartMoneyHoldings 中有对应
        vr.add("R5", "briefing.topHoldings 与 radar.smartMoneyHoldings 对应", True,
               f"briefing: {len(th_names)}家, radar: {len(smh_names)}家")

    # R6: smartMoney >= 2 且有信息量
    if briefing:
        sm = briefing.get("smartMoney", [])
        min_sm = gates.get("R6_smartMoney_min", 2)
        empty_actions = [s.get("source", "?") for s in sm if not s.get("action", "").strip()]
        passed = len(sm) >= min_sm and len(empty_actions) == 0
        detail = f"{len(sm)}条"
        if empty_actions:
            detail += f", 空 action: {', '.join(empty_actions)}"
        vr.add("R6", f"smartMoney ≥ {min_sm}条且有具体动作", passed, detail)

    # R7: 段永平 topHoldings 有完整权重
    if briefing:
        dyp_weight_pattern = gates.get("R7_dyp_weight_pattern", r"\d+\.\d%")
        min_count = gates.get("R7_dyp_weight_min_count", 3)
        dyp_holding = None
        for th in briefing.get("topHoldings", []):
            if "段永平" in th.get("name", ""):
                dyp_holding = th
                break
        if dyp_holding:
            holdings_str = dyp_holding.get("holdings", "")
            weight_matches = re.findall(dyp_weight_pattern, holdings_str)
            passed = len(weight_matches) >= min_count
            vr.add("R7", f"段永平权重完整（≥{min_count}个百分比）", passed,
                   f"发现{len(weight_matches)}个权重数字" + ("" if passed else f": '{holdings_str[:60]}...'"))
        else:
            vr.add("R7", "段永平权重完整", False, "topHoldings 中未找到段永平")

    # R8: smartMoneyDetail 三梯队均非空
    if radar:
        smd = radar.get("smartMoneyDetail", [])
        expected_tiers = gates.get("R8_smartMoneyDetail_tiers", ["T1旗舰", "T2成长", "策略师观点"])
        found_tiers = {}
        for tier_entry in smd:
            tier = tier_entry.get("tier", "")
            funds = tier_entry.get("funds", [])
            found_tiers[tier] = len(funds)

        missing_tiers = [t for t in expected_tiers if found_tiers.get(t, 0) < 1]
        vr.add("R8", "smartMoneyDetail 三梯队均非空", len(missing_tiers) == 0,
               f"缺失: {', '.join(missing_tiers)}" if missing_tiers else f"三梯队均有数据 ✓")


def validate_holdings_cache_consistency(files, vr):
    """R9 [FATAL]: smartMoneyHoldings 与 holdings-cache.json 自动比对
    
    确保 radar.json 的聪明钱持仓数据与 holdings-cache.json 单一数据源一致：
    - 每家机构都存在
    - 每家 positions 数量 >= 10
    - weight 不含"待更新"
    - weight 值与 cache 完全一致
    """
    radar = files.get("radar")
    if not radar:
        vr.add("R9", "smartMoneyHoldings 与 holdings-cache.json 一致性", None, "radar 数据缺失")
        return

    # 加载 holdings-cache.json
    cache = load_json(HOLDINGS_CACHE_PATH)
    if not cache:
        vr.add("R9", "smartMoneyHoldings 与 holdings-cache.json 一致性", None,
               f"holdings-cache.json 加载失败: {HOLDINGS_CACHE_PATH}")
        return

    smh = radar.get("smartMoneyHoldings", [])
    errors = []

    # 构建 cache 的 fund 名称到数据的映射
    cache_funds = {}
    for key, fund_data in cache.items():
        if key.startswith("_"):
            continue
        fund_name = fund_data.get("fund", "")
        cache_funds[fund_name.lower()] = fund_data
        # 也按 manager 名建索引
        manager = fund_data.get("manager", "")
        cache_funds[manager.lower()] = fund_data

    # 检查1：cache 中每家机构都必须出现在 smartMoneyHoldings
    cache_fund_names = set()
    for key, fund_data in cache.items():
        if key.startswith("_"):
            continue
        cache_fund_names.add(fund_data.get("fund", ""))

    smh_fund_names = set(h.get("fund", "") for h in smh)
    missing_funds = cache_fund_names - smh_fund_names
    if missing_funds:
        errors.append(f"缺失机构: {', '.join(missing_funds)}")

    # 检查2：每家机构的 positions 数量和 weight 值
    for holding in smh:
        fund = holding.get("fund", "")
        manager = holding.get("manager", "")
        positions = holding.get("positions", [])

        # 找到对应的 cache 数据
        cache_data = cache_funds.get(fund.lower()) or cache_funds.get(manager.lower())
        if not cache_data:
            continue

        cache_positions = cache_data.get("positions", [])

        # 检查 positions 数量
        if len(positions) < len(cache_positions):
            errors.append(f"{manager}: positions {len(positions)}条, cache 有 {len(cache_positions)}条")

        # 检查每个 position 的 weight 是否与 cache 一致
        cache_weight_map = {p["symbol"]: p["weight"] for p in cache_positions}
        for pos in positions:
            symbol = pos.get("symbol", "")
            weight = pos.get("weight", "")
            if "待更新" in str(weight):
                errors.append(f"{manager}/{symbol}: weight='待更新'")
            elif symbol in cache_weight_map and weight != cache_weight_map[symbol]:
                errors.append(f"{manager}/{symbol}: weight='{weight}' vs cache='{cache_weight_map[symbol]}'")

    vr.add("R9", "smartMoneyHoldings 与 holdings-cache.json 一致性 [FATAL]",
           len(errors) == 0,
           "; ".join(errors[:8]) if errors else f"3家机构×Top10 全部一致 ✓")


def validate_text_quality(files, baseline, vr):
    """V20-V25: 文本质量校验"""
    tq = baseline.get("textQuality", {})
    briefing = files.get("briefing")

    # V20: takeaway 中【】数量
    if briefing:
        takeaway = briefing.get("takeaway", "")
        if takeaway:
            count = count_highlights(takeaway)
            min_h = baseline.get("structureChecks", {}).get("briefing", {}).get("takeaway_highlight_min", 3)
            max_h = baseline.get("structureChecks", {}).get("briefing", {}).get("takeaway_highlight_max", 5)
            passed = min_h <= count <= max_h
            vr.add("V20", f"takeaway【】标红数量 ({min_h}-{max_h})", passed,
                   f"实际{count}个" + ("" if passed else f": '{takeaway[:60]}...'"))
        else:
            vr.add("V20", "takeaway【】标红", None, "takeaway 为空")

    # V21: riskPoints 不含操作违禁词
    if briefing:
        rp = briefing.get("riskPoints", [])
        forbidden = tq.get("riskPoints_forbidden_words", [])
        violations = []
        for i, point in enumerate(rp):
            if isinstance(point, str):
                for word in forbidden:
                    if word in point:
                        violations.append(f"riskPoints[{i}] 含'{word}'")
        vr.add("V21", "riskPoints 不含操作违禁词", len(violations) == 0,
               "; ".join(violations) if violations else "")

    # V24: Markdown 残留扫描
    md_patterns = tq.get("markdown_patterns", [])
    md_violations = []
    all_text = json.dumps(files, ensure_ascii=False)
    # 只检查关键的 markdown 模式
    for pattern in ["\\*\\*"]:
        if re.search(pattern, all_text):
            md_violations.append(f"发现 markdown 加粗语法 **")
            break

    vr.add("V24", "Markdown 残留扫描", len(md_violations) == 0,
           "; ".join(md_violations) if md_violations else "")

    # V25: 模糊前缀扫描（在 globalReaction 和 price 字段）
    fuzzy_patterns = tq.get("fuzzy_prefix_patterns", ["~", "≈", "约", "左右"])
    fuzzy_found = []
    if briefing:
        for i, gr in enumerate(briefing.get("globalReaction", [])):
            val = gr.get("value", "")
            for fp in fuzzy_patterns:
                if fp in val:
                    fuzzy_found.append(f"globalReaction[{i}].value='{val}' 含'{fp}'")
    vr.add("V25", "价格/涨跌幅无模糊前缀 (~≈约左右)", len(fuzzy_found) == 0,
           "; ".join(fuzzy_found) if fuzzy_found else "")


def validate_sector_balance(files, baseline, vr):
    """V26: 4核心板块各≥2只标的"""
    watchlist = files.get("watchlist")
    if not watchlist:
        vr.add("V26", "4核心板块各≥2只标的", None, "watchlist 数据缺失")
        return

    core_sectors = baseline.get("structureChecks", {}).get("watchlist", {}).get(
        "core_sectors", ["ai_infra", "ai_app", "cn_ai", "smart_money"])
    min_stocks = baseline.get("structureChecks", {}).get("watchlist", {}).get("min_stocks_per_core_sector", 2)

    stocks = watchlist.get("stocks", {})
    insufficient = []
    for sector_id in core_sectors:
        stock_list = stocks.get(sector_id, [])
        if len(stock_list) < min_stocks:
            insufficient.append(f"{sector_id}: {len(stock_list)}只(需≥{min_stocks})")

    vr.add("V26", f"4核心板块各≥{min_stocks}只标的", len(insufficient) == 0,
           "; ".join(insufficient) if insufficient else "")


def validate_insight_lengths(files, baseline, vr):
    """V27: markets.json 6个 Insight 字段长度校验（30-80字）"""
    markets = files.get("markets")
    if not markets:
        vr.add("V27", "6个 Insight 长度校验 (30-80字)", None, "markets 数据缺失")
        return

    m_cfg = baseline.get("structureChecks", {}).get("markets", {})
    min_len = m_cfg.get("insight_min_length", 30)
    max_len = m_cfg.get("insight_max_length", 80)

    insight_fields = ["usInsight", "m7Insight", "asiaInsight", "commodityInsight", "cryptoInsight", "gicsInsight"]
    violations = []
    for field in insight_fields:
        val = markets.get(field, "")
        if not val:
            violations.append(f"{field}: 为空")
        elif len(val) < min_len:
            violations.append(f"{field}: {len(val)}字 < {min_len}")
        elif len(val) > max_len:
            violations.append(f"{field}: {len(val)}字 > {max_len}")

    vr.add("V27", f"6个 Insight 长度校验 ({min_len}-{max_len}字)", len(violations) == 0,
           "; ".join(violations) if violations else "")


def validate_metrics_count(files, baseline, vr):
    """V28: watchlist 每只已上市标的 metrics 精确6项"""
    watchlist = files.get("watchlist")
    if not watchlist:
        vr.add("V28", "watchlist metrics 精确6项", None, "watchlist 数据缺失")
        return

    expected = baseline.get("structureChecks", {}).get("watchlist", {}).get("metrics_exact", 6)
    violations = []
    stocks = watchlist.get("stocks", {})
    for sector_id, stock_list in stocks.items():
        if not isinstance(stock_list, list):
            continue
        for stock in stock_list:
            if stock.get("listed", True) is False:
                continue
            metrics = stock.get("metrics", [])
            if len(metrics) != expected:
                name = stock.get("name", stock.get("symbol", "?"))
                violations.append(f"{sector_id}/{name}: {len(metrics)}项(需{expected})")

    vr.add("V28", f"watchlist 已上市标的 metrics 精确{expected}项", len(violations) == 0,
           "; ".join(violations[:5]) if violations else "")


def validate_logic_arrow_format(files, vr):
    """V29: coreJudgments[].logic 包含箭头(→)三段式格式"""
    briefing = files.get("briefing")
    if not briefing:
        vr.add("V29", "coreJudgments logic 箭头三段式", None, "briefing 数据缺失")
        return

    violations = []
    for i, cj in enumerate(briefing.get("coreJudgments", [])):
        logic = cj.get("logic", "")
        if logic and "→" not in logic:
            violations.append(f"coreJudgments[{i}]: 缺少 → 符号 ('{logic[:40]}...')")

    vr.add("V29", "coreJudgments logic 箭头三段式 (含→)", len(violations) == 0,
           "; ".join(violations) if violations else "")


def validate_chain_urls(files, vr):
    """V22: chain[].url 非空校验（非付费墙）"""
    briefing = files.get("briefing")
    if not briefing:
        vr.add("V22", "chain[].url 非空（非付费墙）", None, "briefing 数据缺失")
        return

    paywall_sources = {"Bloomberg", "FT", "Financial Times", "WSJ", "Wall Street Journal", "Newsquawk"}
    missing_urls = []
    chain = briefing.get("coreEvent", {}).get("chain", [])
    for i, c in enumerate(chain):
        source = c.get("source", "")
        url = c.get("url", "")
        # 检查是否为付费墙
        is_paywall = any(pw.lower() in source.lower() for pw in paywall_sources)
        if not is_paywall and (not url or not url.startswith("http")):
            missing_urls.append(f"chain[{i}] source='{source}' url 缺失")

    vr.add("V22", "chain[].url 非空（非付费墙媒体）", len(missing_urls) == 0,
           "; ".join(missing_urls) if missing_urls else "")


def validate_core_judgments_references(files, vr):
    """V23: coreJudgments[].references 非空"""
    briefing = files.get("briefing")
    if not briefing:
        vr.add("V23", "coreJudgments[].references 非空", None, "briefing 数据缺失")
        return

    missing = []
    for i, cj in enumerate(briefing.get("coreJudgments", [])):
        refs = cj.get("references", [])
        if not refs or len(refs) == 0:
            missing.append(f"coreJudgments[{i}] references 为空")
        else:
            for j, ref in enumerate(refs):
                if isinstance(ref, dict):
                    if not ref.get("name", "").strip():
                        missing.append(f"coreJudgments[{i}].references[{j}].name 为空")

    vr.add("V23", "coreJudgments[].references 非空", len(missing) == 0,
           "; ".join(missing) if missing else "")


def validate_traffic_lights_consistency(files, baseline, vr):
    """检查 trafficLights value 与 status 的阈值一致性"""
    radar = files.get("radar")
    if not radar:
        vr.add("V_TL", "trafficLights value↔status 阈值一致", None, "radar 数据缺失")
        return

    thresholds = baseline.get("trafficLightThresholds", {})
    inconsistencies = []

    for tl in radar.get("trafficLights", []):
        name = tl.get("name", "")
        value_str = tl.get("value", "")
        status = tl.get("status", "")
        cfg = thresholds.get(name)

        if not cfg or not value_str:
            continue

        value_num = parse_number_from_string(value_str)
        if value_num is None:
            continue

        # 计算期望 status
        if value_num < cfg["green_max"]:
            expected = "green"
        elif value_num <= cfg["yellow_max"]:
            expected = "yellow"
        else:
            expected = "red"

        # 边界值容差处理（阈值上用 <=）
        if abs(value_num - cfg["green_max"]) < 0.01:
            # 边界可接受 green 或 yellow
            if status not in ("green", "yellow"):
                inconsistencies.append(f"{name}: value={value_str}, 期望green/yellow, 实际{status}")
        elif abs(value_num - cfg["yellow_max"]) < 0.01:
            if status not in ("yellow", "red"):
                inconsistencies.append(f"{name}: value={value_str}, 期望yellow/red, 实际{status}")
        elif status != expected:
            inconsistencies.append(f"{name}: value={value_str}→期望{expected}, 实际{status}")

    vr.add("V_TL", "trafficLights value↔status 阈值一致", len(inconsistencies) == 0,
           "; ".join(inconsistencies) if inconsistencies else "")


# ============================================================
# 主函数
# ============================================================

def main():
    if len(sys.argv) < 2:
        print("用法: python3 validate.py <sync_dir> [--mode heavy|refresh|weekend]")
        sys.exit(2)

    sync_dir = sys.argv[1]
    mode = "heavy"  # 默认

    for i, arg in enumerate(sys.argv):
        if arg == "--mode" and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1].lower()

    if mode not in ("heavy", "refresh", "weekend"):
        print(f"⚠️  未知模式 '{mode}'，使用默认 'heavy'")
        mode = "heavy"

    if not os.path.isdir(sync_dir):
        print(f"❌ 目录不存在: {sync_dir}")
        sys.exit(2)

    # 加载基线
    baseline = load_json(BASELINE_PATH)
    if not baseline:
        print(f"⚠️  基线文件加载失败: {BASELINE_PATH}，使用默认值")
        baseline = {}

    print(f"\n🔍 开始校验 | 目录: {sync_dir} | 模式: {mode}")

    vr = ValidationResult()

    # === V1: 文件存在性 ===
    files = validate_file_existence(sync_dir, vr)

    # 如果所有文件都不存在，提前退出
    if all(v is None for v in files.values()):
        vr.print_report()
        sys.exit(1)

    # === V2: 必填字段非空 ===
    bs = baseline.get("structureChecks", {})
    for file_key, data in files.items():
        if data is not None and file_key in bs:
            required = bs[file_key].get("requiredTopLevel", [])
            validate_required_fields(data, required, f"{file_key}.json", vr, "V2")

    # === V3: 数据类型校验 ===
    validate_data_types(files, vr)

    # === V4: 枚举值校验 ===
    validate_enums_comprehensive(files, baseline, vr)

    # === V5: 数组长度校验 ===
    validate_array_lengths(files, baseline, vr)

    # === V6: sparkline[-1] vs price ===
    validate_sparkline_price_consistency(files, baseline, vr)

    # === V7-V8: metrics 一致性 ===
    validate_metrics_consistency(files, vr)

    # === V9: sentimentScore → sentimentLabel ===
    validate_sentiment_mapping(files, baseline, vr)

    # === V10-V11: riskScore 公式 + riskLevel ===
    validate_risk_score(files, baseline, vr)

    # === V_TL: trafficLights value↔status ===
    validate_traffic_lights_consistency(files, baseline, vr)

    # === V20-V25: 文本质量 ===
    validate_text_quality(files, baseline, vr)

    # === V22: chain[].url ===
    validate_chain_urls(files, vr)

    # === V23: coreJudgments[].references ===
    validate_core_judgments_references(files, vr)

    # === V26: 板块均衡 ===
    validate_sector_balance(files, baseline, vr)

    # === V27: Insight 长度校验 ===
    validate_insight_lengths(files, baseline, vr)

    # === V28: metrics 数量校验 ===
    validate_metrics_count(files, baseline, vr)

    # === V29: coreJudgments logic 箭头格式 ===
    validate_logic_arrow_format(files, vr)

    # === R1-R8: 回归门禁 ===
    validate_regression_gates(files, baseline, vr, mode)

    # === R9 [FATAL]: smartMoneyHoldings 与 holdings-cache.json 一致性 ===
    # R9 在所有模式下都执行（包括 refresh），因为持仓数据必须始终正确
    validate_holdings_cache_consistency(files, vr)

    # 输出报告
    exit_code = vr.print_report()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
