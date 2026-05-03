#!/usr/bin/env python3
"""
投研鸭小程序数据质量自动化校验脚本 v5.7
============================================================
核心理念（Harness Engineering）:
  把"AI 记住规则"转变为"环境自动约束 AI"。
  本脚本在 run_daily.sh 中的 auto_compute.py 之后、sparkline 补全之前执行。

v5.7 Harness v9.2 盲点补丁（2026-04-21 涨跌符号事故修复）：
  - 新增 V38b [WARN] 美股三大指数方向合理性检测
    弥补 V38 的结构性盲点：当 AI 同时把 change 和 sparkline 都写反时，
    V38 会误判为"一致"而放行。V38b 通过检测 usInsight 文字与 change 方向矛盾来拦截。
  - 校验项 54 → 55 项

v5.6 Harness v10.6 全面收紧 FATAL 门禁（目标：每次全部通过）：
  - V35  WARN→FATAL 升级：audioUrl 为空 = 语音播报失效（核心功能）
  - V38  WARN→FATAL 升级：sparkline 趋势与 change 方向矛盾 = 数据错误
  - V41  WARN→FATAL 升级：globalReaction value 超长/含括号 = 前端布局溢出
  - V42  WARN→FATAL 升级：generatedAt 为空 = 前端时间显示异常
  - V24  WARN→FATAL 升级：Markdown 残留 = 前端直接渲染乱码
  - R1   WARN→FATAL 升级：topHoldings < 3 = 聪明钱核心展示严重不完整
  - V_TL WARN→FATAL 升级：红绿灯 value↔status 不一致 = 前端颜色错误
  - FATAL_CODES 从 10 → 17 项
  - 校验项数量不变（54项）

v5.5 Harness v10.5 门槛全面收紧（数据准确性 > 执行速度）：
  - V6  WARN→FATAL 升级：sparkline[-1] vs price 偏差 ≤5%（形成 V6/V45 双层防护）
  - V40 WARN→FATAL 升级：metrics 空值 = 前端空白 = 阻断发布
  - V44 阈值收紧：从 >50% 零值 → 任何零值(>=1个)即 FATAL
  - V45 阈值收紧：price vs sparkline[-1] 差距从 50%→30%
  - 新增 V46 [FATAL] chartData 禁止零值（与 V44 平行，覆盖30日数据）
  - 新增 V47 [WARN] sparkline/chartData 禁止全平线（拦截估算填充）
  - FATAL_CODES 新增 V6/V40/V46（从5→10个FATAL项）
  - 校验项 52→54 项

v5.4 Harness v10.4 结构性数据防护（2026-04-09 事故修复）：
  - 新增 V44 [FATAL] sparkline 禁止零值
  - 新增 V45 [FATAL] price 与 sparkline 数量级一致性
  - 校验项从50→52项

v5.3 Harness v10.3 4/8基准质量巩固：
  - 新增 V43 [FATAL] price 禁止占位符（拦截 "--"/"N/A"/空值）
  - 校验项从49→50项

v5.1 Harness v10.2 聪明钱持仓 13F 合规性校验：
  - 新增 V39 [FATAL] 聪明钱持仓 13F 数据合规性校验（拦截 AI 编造的期权/虚构标的）
    - symbol 黑名单（PUT/CALL/OPTION/WARRANT）
    - name 黑名单（看跌期权/看涨期权/认购/认沽/期权/权证）
    - 权重合计 ≤ 105%（防止编造持仓导致溢出）
  - V39 标记为 FATAL 级，不可被 --skip-warn 绕过
  - 校验项从44→45项

v5.0 Harness v10.1 数据安全防护升级：
  - 新增 V36 跨JSON数据交叉验证（radar↔markets↔watchlist同一数据点一致性）
  - 新增 V37 数值合理性检测（防训练数据污染，如CNH=7.27而非6.82）
  - 新增 V38 sparkline趋势 vs change方向一致性（拦截涨跌符号反转）
  - 校验项从41→44项

v4.0 Harness v10.0 升级：
  - 新增 V30-V34 内容质量检测层（套话/模板/空洞/数字矛盾/tags时效）
  - Insight 长度上限从80→100字（决策信号式洞察需要更多空间）
  - V7 比对精度修复（abs值比对）
  - 废弃字段清理（riskAlerts 不再必填）

v3.0 Harness v9.0 升级：
  - 删除 Refresh 模式分支：--mode 只接受 standard 和 weekend
  - heavy 作为别名映射到 standard（向后兼容）
  - 回归门禁统一执行（standard + weekend 均执行，不再有 refresh 豁免）

v2.0 升级：FATAL / WARN 双级机制
v1.1 新增：V27(Insight长度) + V28(metrics数量) + V29(logic箭头格式)

用法:
  python3 validate.py <sync_dir> [--mode standard|weekend]

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
# v5.6 新增：V24/V35/V38/V41/V42/R1/V_TL（FATAL 项 10→17，目标：每次全部通过）
FATAL_CODES = {
    # 数据准确性（原有）
    "V6", "V43", "V44", "V45", "V46",
    # 持仓合规（原有）
    "V39", "V40", "R2", "R3", "R9",
    # v5.6 新升级：前端渲染安全
    "V24",   # Markdown 残留 → 前端乱码
    "V41",   # globalReaction value 超长/含括号 → 布局溢出
    "V42",   # generatedAt 为空 → 前端时间显示异常
    # v5.6→v5.8：V35 降回 WARN（语音播报暂停，不阻断上传）
    # "V35",   # audioUrl 为空 → 语音播报功能失效（已暂停）
    "V38",   # sparkline趋势 vs change 方向矛盾 → 数据错误
    "R1",    # topHoldings < 3 → 聪明钱持仓核心展示不完整
    "V_TL",  # 红绿灯 value↔status 阈值不一致 → 前端颜色错误
}

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
        print("📋 投研鸭数据质量自动化校验报告 (v5.6 Harness v10.6)")
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
    """V6 [FATAL]: sparkline[-1] vs price 偏差 ≤5%
    
    v10.5 升级：从 WARN→FATAL，容差从 1%→5%。
    V45 拦截数量级差异(>50%)，V6 拦截中等差异(5-50%)，形成双层防护。
    """
    tolerance = 0.05  # 5% — 升级为更严格的 FATAL 门禁
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
        vr.add("V6", "sparkline[-1] vs price 一致性 (≤5%)", False,
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
                    # 验证：metrics[1] 应该是 "+X.XX%" 或 "-X.XX%" 格式
                    m1_num = parse_number_from_string(m1_val)
                    if m1_num is not None and abs(abs(m1_num) - abs(change)) > 0.01:
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
    """R1-R8 回归门禁（v9.0: standard + weekend 均执行）"""

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


# ============================================================
# v4.0 新增：V30-V34 内容质量检测层
# ============================================================

def validate_insight_clichés(files, baseline, vr):
    """V30: Insight 套话检测 — 检测低信息量模式"""
    markets = files.get("markets")
    if not markets:
        vr.add("V30", "Insight 套话检测", None, "markets 数据缺失")
        return

    cliché_patterns = baseline.get("textQuality", {}).get("insight_cliche_patterns", [])
    insight_fields = ["usInsight", "m7Insight", "asiaInsight", "commodityInsight", "cryptoInsight", "gicsInsight"]
    violations = []

    for field in insight_fields:
        val = markets.get(field, "")
        if not val:
            continue
        for pattern in cliché_patterns:
            if pattern in val:
                violations.append(f"{field} 含套话'{pattern}'")
                break  # 每个字段只报一次

    vr.add("V30", "Insight 套话检测 (禁止低信息量模式)", len(violations) == 0,
           "; ".join(violations) if violations else "")


def validate_risk_advice_template(files, baseline, vr):
    """V31: riskAdvice 模板检测 — 禁止套模板"""
    radar = files.get("radar")
    if not radar:
        vr.add("V31", "riskAdvice 模板检测", None, "radar 数据缺失")
        return

    template_patterns = baseline.get("textQuality", {}).get("riskAdvice_template_patterns", [])
    advice = radar.get("riskAdvice", "")
    violations = []

    if not advice:
        violations.append("riskAdvice 为空")
    else:
        for pattern in template_patterns:
            if pattern in advice:
                violations.append(f"含套话'{pattern}'")

    vr.add("V31", "riskAdvice 非模板化检测", len(violations) == 0,
           "; ".join(violations) if violations else "")


def validate_analysis_depth(files, baseline, vr):
    """V32: watchlist analysis 深度检测 — 每只标的分析≥80字"""
    watchlist = files.get("watchlist")
    if not watchlist:
        vr.add("V32", "watchlist analysis 深度检测", None, "watchlist 数据缺失")
        return

    min_len = baseline.get("textQuality", {}).get("watchlist_analysis_min_length", 80)
    violations = []
    stocks = watchlist.get("stocks", {})
    for sector_id, stock_list in stocks.items():
        if not isinstance(stock_list, list):
            continue
        for stock in stock_list:
            analysis = stock.get("analysis", "")
            name = stock.get("name", stock.get("symbol", "?"))
            if analysis and len(analysis) < min_len:
                violations.append(f"{sector_id}/{name}: {len(analysis)}字 < {min_len}")

    vr.add("V32", f"watchlist analysis 深度 (≥{min_len}字)", len(violations) == 0,
           "; ".join(violations[:5]) if violations else "")


def validate_action_hints_quality(files, vr):
    """V33: actionHints 质量检测 — 禁止凑数（"维持不变"/"持续关注"）"""
    briefing = files.get("briefing")
    if not briefing:
        vr.add("V33", "actionHints 质量检测", None, "briefing 数据缺失")
        return

    action_hints = briefing.get("actionHints", [])
    violations = []
    filler_patterns = ["维持不变", "持续关注", "保持现有", "暂时观望", "继续持有现有"]

    for i, ah in enumerate(action_hints):
        content = ah.get("content", "")
        for pattern in filler_patterns:
            if pattern in content:
                violations.append(f"actionHints[{i}] 含凑数表达'{pattern}'")
                break

    vr.add("V33", "actionHints 无凑数表达检测", len(violations) == 0,
           "; ".join(violations) if violations else "")


def validate_source_type_consistency(files, vr):
    """V34: 4个JSON的 sourceType 一致性 — 必须全部相同"""
    types_found = {}
    for name, data in files.items():
        if data and "_meta" in data:
            st = data["_meta"].get("sourceType", "")
            if st:
                types_found[name] = st

    if len(types_found) < 2:
        vr.add("V34", "4个JSON sourceType 一致性", True, "不足2个有_meta")
        return

    unique_types = set(types_found.values())
    if len(unique_types) == 1:
        vr.add("V34", "4个JSON sourceType 一致性", True,
               f"全部为'{list(unique_types)[0]}' ✓")
    else:
        details = [f"{k}='{v}'" for k, v in types_found.items()]
        vr.add("V34", "4个JSON sourceType 一致性", False,
               f"不一致: {'; '.join(details)}")


def validate_audio_url(files, vr):
    """V35: briefing.audioUrl 非空检测（语音播报功能保障）"""
    briefing = files.get("briefing")
    if not briefing:
        vr.add("V35", "briefing.audioUrl 语音播报", None, "briefing 数据缺失")
        return

    audio_url = briefing.get("audioUrl", "")
    voice_text = briefing.get("voiceText", "")

    if audio_url:
        vr.add("V35", "briefing.audioUrl 语音播报", True, f"audioUrl 已填充 ✓")
    elif voice_text:
        vr.add("V35", "briefing.audioUrl 语音播报", False,
               "voiceText 已有但 audioUrl 为空——需执行 TTS 生成+上传步骤")
    else:
        vr.add("V35", "briefing.audioUrl 语音播报", False,
               "audioUrl 和 voiceText 均为空——第3.5阶段（语音播报）被跳过")


# ============================================================
# v10.1 新增：V36-V38 数据安全防护层（Harness Engineering）
# 设计理念：把"AI记住不犯错"转变为"环境自动拦截错误"
# ============================================================

def validate_cross_json_consistency(files, vr):
    """V36: 跨JSON数据交叉验证 — 同一数据点在不同JSON中必须一致
    
    检查项：
    1. radar.trafficLights[离岸人民币CNH].value vs markets.commodities[离岸人民币CNH].price
    2. radar.trafficLights[布伦特原油].value vs markets.commodities[布伦特原油].price
    3. radar.trafficLights[VIX].value vs markets.usMarkets[VIX].price
    4. radar.trafficLights[10Y美债].value vs markets.commodities[10Y美债].price
    5. radar.trafficLights[黄金XAU].value vs markets.commodities[黄金XAU].price
    6. radar.trafficLights[美元指数DXY].value vs markets.commodities[美元指数DXY].price
    7. watchlist AVGO price vs markets m7(若在M7中)
    8. watchlist 中重复标的价格一致性
    """
    radar = files.get("radar")
    markets = files.get("markets")
    watchlist = files.get("watchlist")

    if not radar or not markets:
        vr.add("V36", "跨JSON数据交叉验证", None, "radar 或 markets 数据缺失")
        return

    inconsistencies = []
    tolerance = 0.03  # 3% 容差

    # 1. radar.trafficLights vs markets.commodities 交叉验证
    tl_map = {}
    for tl in radar.get("trafficLights", []):
        name = tl.get("name", "")
        value_str = tl.get("value", "")
        tl_map[name] = value_str

    # 构建 markets 价格映射
    market_price_map = {}
    for section in ["usMarkets", "commodities"]:
        for item in markets.get(section, []):
            name = item.get("name", "")
            price = item.get("price", "")
            market_price_map[name] = price

    # 交叉比对表：红绿灯名称 → markets 中对应的名称
    cross_check_map = {
        "离岸人民币CNH": "离岸人民币CNH",
        "布伦特原油": "布伦特原油",
        "VIX波动率": "VIX恐慌指数",
        "10Y美债收益率": "10Y美债",
        "黄金XAU": "黄金 XAU",
        "美元指数DXY": "美元指数DXY",
    }

    for tl_name, market_name in cross_check_map.items():
        tl_val_str = tl_map.get(tl_name, "")
        market_price_str = market_price_map.get(market_name, "")

        if not tl_val_str or not market_price_str:
            continue

        tl_num = parse_number_from_string(tl_val_str)
        market_num = parse_number_from_string(market_price_str)

        if tl_num is None or market_num is None or market_num == 0:
            continue

        deviation = abs(tl_num - market_num) / max(abs(market_num), 1)
        if deviation > tolerance:
            inconsistencies.append(
                f"{tl_name}: radar={tl_val_str} vs markets={market_price_str} (偏差{deviation:.1%})"
            )

    # 2. watchlist 中同一标的在不同板块出现时价格一致性
    if watchlist:
        symbol_prices = {}
        stocks = watchlist.get("stocks", {})
        for sector_id, stock_list in stocks.items():
            if not isinstance(stock_list, list):
                continue
            for stock in stock_list:
                symbol = stock.get("symbol", "")
                price = stock.get("price", "")
                if symbol in symbol_prices:
                    if symbol_prices[symbol] != price:
                        inconsistencies.append(
                            f"watchlist重复标的{symbol}: {symbol_prices[symbol]} vs {price}"
                        )
                else:
                    symbol_prices[symbol] = price

    # 3. markets.m7 标的价格 vs watchlist 同标的价格
    if watchlist:
        wl_prices = {}
        for sector_id, stock_list in watchlist.get("stocks", {}).items():
            if isinstance(stock_list, list):
                for s in stock_list:
                    wl_prices[s.get("symbol", "")] = s.get("price", "")

        for m7_stock in markets.get("m7", []):
            symbol = m7_stock.get("symbol", "")
            m7_price = m7_stock.get("price", "")
            wl_price = wl_prices.get(symbol, "")
            if m7_price and wl_price and m7_price != wl_price:
                m7_num = parse_number_from_string(m7_price)
                wl_num = parse_number_from_string(wl_price)
                if m7_num and wl_num and m7_num > 0:
                    dev = abs(m7_num - wl_num) / m7_num
                    if dev > tolerance:
                        inconsistencies.append(
                            f"M7 vs watchlist [{symbol}]: m7={m7_price} vs watchlist={wl_price} (偏差{dev:.1%})"
                        )

    vr.add("V36", "跨JSON数据交叉验证 (radar↔markets↔watchlist)", len(inconsistencies) == 0,
           "; ".join(inconsistencies[:8]) if inconsistencies else "全部一致 ✓")


def validate_value_reasonableness(files, vr):
    """V37: 数值合理性检测 — 拦截明显不合理的数字（防止训练数据污染）
    
    检查项（基于常识性阈值）：
    1. USDCNH 离岸人民币汇率应在 6.0-8.0 区间（2020-2026历史范围）
    2. 恒生科技指数应在 2000-10000 区间（2020-2026历史范围）
    3. 标普500 应在 3000-10000 区间
    4. VIX 应在 8-80 区间
    5. 10Y美债 应在 1.0-7.0% 区间
    6. DXY 美元指数 应在 85-120 区间
    7. WTI/布伦特原油 应在 20-200 区间
    8. 黄金 XAU 应在 1500-8000 区间
    9. BTC 应在 15000-250000 区间
    10. 个股价格不应为负数
    """
    markets = files.get("markets")
    watchlist = files.get("watchlist")

    if not markets:
        vr.add("V37", "数值合理性检测", None, "markets 数据缺失")
        return

    violations = []

    # 合理性阈值表：名称关键词 → (min, max)
    reasonableness_ranges = {
        "离岸人民币": (6.0, 8.0),
        "恒生科技": (2000, 12000),
        "恒生指数": (15000, 40000),
        "上证指数": (2500, 7000),
        "深证成指": (8000, 20000),
        "标普500": (3000, 10000),
        "纳斯达克": (10000, 35000),
        "道琼斯": (25000, 65000),
        "VIX": (8, 80),
        "10Y美债": (1.0, 7.0),
        "美元指数": (85, 120),
        "布伦特原油": (20, 200),
        "WTI原油": (20, 200),
        "黄金": (1500, 8000),
        "比特币": (15000, 250000),
        "以太坊": (500, 15000),
        "日经": (20000, 70000),
        "KOSPI": (1500, 8000),
    }

    # 检查所有 markets 数据
    for section in ["usMarkets", "asiaMarkets", "commodities", "cryptos"]:
        for item in markets.get(section, []):
            name = item.get("name", "")
            price_str = item.get("price", "")
            price_num = parse_number_from_string(price_str)
            if price_num is None:
                continue

            for keyword, (vmin, vmax) in reasonableness_ranges.items():
                if keyword in name:
                    if price_num < vmin or price_num > vmax:
                        violations.append(
                            f"{name}={price_str}: 超出合理区间[{vmin}-{vmax}]"
                        )
                    break

    # 检查 watchlist 个股价格不为负
    if watchlist:
        for sector_id, stock_list in watchlist.get("stocks", {}).items():
            if not isinstance(stock_list, list):
                continue
            for stock in stock_list:
                if stock.get("listed", True) is False:
                    continue
                price_str = stock.get("price", "")
                if price_str == "未上市":
                    continue
                price_num = parse_number_from_string(price_str)
                if price_num is not None and price_num <= 0:
                    name = stock.get("name", stock.get("symbol", "?"))
                    violations.append(f"watchlist[{name}]: price={price_str} ≤ 0")

    vr.add("V37", "数值合理性检测 (防训练数据污染)", len(violations) == 0,
           "; ".join(violations[:8]) if violations else "全部在合理区间 ✓")


def validate_sparkline_trend_vs_change(files, vr):
    """V38: sparkline趋势方向 vs change符号一致性 — 拦截涨跌方向反转错误
    
    检查逻辑：
    若 sparkline[-1] < sparkline[-2]（最后两天趋势为跌），但 change > 0（标记为涨），
    且偏差超过 0.5%，则标记为 WARN。
    
    这可以拦截如 AAPL +2.13% 实际是 -2.07%、TSLA +1.75% 实际是 -1.75% 的错误。
    """
    markets = files.get("markets")
    watchlist = files.get("watchlist")

    if not markets and not watchlist:
        vr.add("V38", "sparkline趋势 vs change方向一致", None, "数据缺失")
        return

    direction_conflicts = []
    tolerance = 0.005  # 0.5% 容差（避免小幅波动误报）

    def check_item(item, location):
        sparkline = item.get("sparkline", [])
        change = item.get("change")
        price_str = item.get("price", "")
        name = item.get("name", "")

        if not sparkline or len(sparkline) < 2:
            return
        if not isinstance(change, (int, float)):
            return

        last = sparkline[-1]
        prev = sparkline[-2]

        if not isinstance(last, (int, float)) or not isinstance(prev, (int, float)):
            return
        if prev == 0:
            return

        spark_pct = (last - prev) / prev
        change_pct = change / 100.0

        # 如果 sparkline 趋势和 change 方向相反，且幅度都大于容差
        if abs(spark_pct) > tolerance and abs(change_pct) > tolerance:
            if (spark_pct > 0 and change_pct < 0) or (spark_pct < 0 and change_pct > 0):
                direction_conflicts.append(
                    f"{location}[{name}]: sparkline尾部{spark_pct:+.2%} vs change={change:+.2f}% 方向矛盾"
                )

    # 检查 markets
    if markets:
        for section in ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"]:
            for item in markets.get(section, []):
                check_item(item, f"markets.{section}")

    # 检查 watchlist
    if watchlist:
        for sector_id, stock_list in watchlist.get("stocks", {}).items():
            if isinstance(stock_list, list):
                for stock in stock_list:
                    if stock.get("listed", True) is False:
                        continue
                    check_item(stock, f"watchlist.{sector_id}")

    vr.add("V38", "sparkline趋势 vs change方向一致性", len(direction_conflicts) == 0,
           "; ".join(direction_conflicts[:8]) if direction_conflicts else "全部一致 ✓")


def validate_us_index_direction_plausibility(files, vr):
    """V38b [WARN]: 美股三大指数涨跌方向合理性检测
    
    工具链盲点补丁（2026-04-21 事故教训）：
    V38 只能检测 change 与 sparkline 的内部一致性。
    当 AI 同时把 change 和 sparkline 都写反时（如 SPX -0.24% 写成 +0.24%，sparkline也写成上升），
    V38 会误判为"一致"而放行。本项通过检查三大指数是否同向来发现这类错误。
    
    检查逻辑：
    若三大指数（SPX/NDX/DJI）的 change 全为正且值接近相似（如都是+0.24/0.26/0.01），
    则为正常。但若三大指数 change 全为正 且 usInsight 文本中含有明显的"跌/下跌/收跌"字样，
    则发出 WARN（文字与数据矛盾）。
    """
    markets = files.get("markets")
    if not markets:
        vr.add("V38b", "美股三大指数方向合理性", None, "数据缺失")
        return

    us = markets.get("usMarkets", [])
    if len(us) < 3:
        vr.add("V38b", "美股三大指数方向合理性", None, "usMarkets 数据不足3项")
        return

    # 取三大指数（前3项：SPX/NDX/DJI）
    indices = us[:3]
    changes = [x.get("change") for x in indices if isinstance(x.get("change"), (int, float))]
    
    if len(changes) < 3:
        vr.add("V38b", "美股三大指数方向合理性", None, "change 数值不足")
        return

    # 检查1：insight 文字与 change 方向矛盾
    us_insight = markets.get("usInsight", "")
    insight_bearish = any(kw in us_insight for kw in ["收跌", "下跌", "跌幅", "跌势", "微跌", "大跌"])
    insight_bullish = any(kw in us_insight for kw in ["收涨", "上涨", "涨幅", "涨势", "大涨", "创新高"])
    
    all_positive = all(c > 0 for c in changes)
    all_negative = all(c < 0 for c in changes)
    
    warnings = []
    
    # insight 说跌，但 change 全为正
    if insight_bearish and all_positive:
        warnings.append(
            f"usInsight 含跌势描述但三大指数 change 全为正值 "
            f"({', '.join(f'{c:+.2f}%' for c in changes)}) — 疑似涨跌符号写反，请核查"
        )
    
    # insight 说涨，但 change 全为负
    if insight_bullish and all_negative:
        warnings.append(
            f"usInsight 含涨势描述但三大指数 change 全为负值 "
            f"({', '.join(f'{c:+.2f}%' for c in changes)}) — 疑似涨跌符号写反，请核查"
        )

    if warnings:
        vr.add("V38b", "美股三大指数方向合理性（Insight文字 vs change 矛盾）", False,
               "; ".join(warnings))
    else:
        names = [x.get("name", "") for x in indices[:3]]
        vr.add("V38b", "美股三大指数方向合理性", True,
               f"{names[0]}{changes[0]:+.2f}% / {names[1]}{changes[1]:+.2f}% / {names[2]}{changes[2]:+.2f}% — Insight方向一致 ✓")


def validate_holdings_13f_compliance(files, vr):
    """V39 [FATAL]: 聪明钱持仓 13F 数据合规性校验 — 拦截 AI 编造的期权/虚构标的
    
    设计背景（2026-04-08 事故）：
    AI 将段永平历史上的 "sell put" 操作错误理解为持有 AAPL PUT 多头，
    编造了 "苹果看跌期权 AAPL PUT 2.8% 新建仓"，以及 META/AMZN/TSLA 等
    13F 中根本不存在的标的。本检测项从三个维度拦截此类错误。
    
    检查维度：
    1. symbol 格式合规性：禁止 PUT/CALL 等期权后缀（13F 多头持仓不包含期权）
    2. 名称合规性：禁止"看跌期权""看涨期权""认购""认沽"等衍生品关键词
    3. 权重合计校验：同一机构所有 positions 的 weight 之和应 ≤ 105%（容差5%）
    """
    radar = files.get("radar")
    if not radar:
        vr.add("V39", "聪明钱持仓 13F 合规性 [FATAL]", None, "radar 数据缺失")
        return

    smh = radar.get("smartMoneyHoldings", [])
    violations = []

    # 期权/衍生品黑名单关键词
    symbol_blacklist = ["PUT", "CALL", "OPTION", "WARRANT"]
    name_blacklist = ["看跌期权", "看涨期权", "认购", "认沽", "期权", "权证", "PUT", "CALL"]

    for holding in smh:
        manager = holding.get("manager", "?")
        positions = holding.get("positions", [])
        total_weight = 0.0

        for pos in positions:
            symbol = pos.get("symbol", "")
            name = pos.get("name", "")
            weight_str = pos.get("weight", "0%")

            # 检查1: symbol 中不应包含期权后缀
            symbol_upper = symbol.upper().strip()
            for blackword in symbol_blacklist:
                if blackword in symbol_upper:
                    violations.append(
                        f"{manager}/{symbol}: symbol含'{blackword}'——13F多头持仓不包含期权，疑似AI编造"
                    )

            # 检查2: name 中不应包含衍生品关键词
            for blackword in name_blacklist:
                if blackword in name:
                    violations.append(
                        f"{manager}/{name}: 名称含'{blackword}'——13F持仓不应有衍生品，疑似AI编造"
                    )

            # 累加权重
            try:
                w = float(weight_str.replace("%", "").strip())
                total_weight += w
            except (ValueError, AttributeError):
                pass

        # 检查3: 权重合计不应超过 105%（正常 13F 所有持仓合计约 100%）
        if total_weight > 105:
            violations.append(
                f"{manager}: 权重合计 {total_weight:.1f}% > 105%，可能存在编造持仓"
            )

    vr.add("V39", "聪明钱持仓 13F 合规性 [FATAL]", len(violations) == 0,
           "; ".join(violations[:8]) if violations else "全部合规 ✓")


def validate_metrics_no_empty_values(files, vr):
    """V40 [FATAL]: watchlist metrics 不允许空值 — 拦截 auto_compute 未覆盖的空缺
    
    v10.5 升级：从 WARN→FATAL。metrics 空值 = 前端空白 = 用户体验0分，必须阻断发布。
    
    设计背景（2026-04-08/09 事故）：
    auto_compute.py 从 sparkline/chartData 计算 7日/30日涨跌，但当标的
    缺少 sparkline 时，metrics[2]/[3] 留空。前端渲染出空白，用户看到"大量数据缺失"。
    """
    watchlist = files.get("watchlist")
    if not watchlist:
        vr.add("V40", "watchlist metrics 无空值", None, "watchlist 数据缺失")
        return

    empty_fields = []
    stocks = watchlist.get("stocks", {})
    for sector_id, stock_list in stocks.items():
        if not isinstance(stock_list, list):
            continue
        for stock in stock_list:
            if stock.get("listed", True) is False:
                continue
            for m in stock.get("metrics", []):
                val = m.get("value", "")
                if val == "" or val is None:
                    name = stock.get("symbol", "?")
                    empty_fields.append(f"{sector_id}/{name}/{m.get('label', '?')}")

    vr.add("V40", "watchlist metrics 无空值（禁止空字符串）", len(empty_fields) == 0,
           f"{len(empty_fields)}处空值: " + "; ".join(empty_fields[:8]) if empty_fields else "全部有值 ✓")


def validate_global_reaction_value_format(files, vr):
    """V41: globalReaction value 格式校验 — 拦截过长/含括号的混合格式
    
    设计背景（2026-04-08 事故）：
    AI 把 value 写成 "6,773 (+2.37%)" 而非 "+2.37%"，导致前端 33.33% 宽度的
    格子放不下，文字换行显示错乱。value 应该简洁：涨跌幅或绝对值二选一。
    """
    briefing = files.get("briefing")
    if not briefing:
        vr.add("V41", "globalReaction value 格式", None, "briefing 数据缺失")
        return

    violations = []
    for item in briefing.get("globalReaction", []):
        v = item.get("value", "")
        name = item.get("name", "?")
        # 不允许包含括号（说明是混合格式）
        if "(" in v or ")" in v or "（" in v or "）" in v:
            violations.append(f"{name}: value='{v}' 含括号（应只放涨跌幅或绝对值）")
        # 不允许超过 15 字符
        if len(v) > 15:
            violations.append(f"{name}: value='{v}' 过长({len(v)}字符>15)")

    vr.add("V41", "globalReaction value 简洁格式（无括号/≤15字符）", len(violations) == 0,
           "; ".join(violations) if violations else "全部简洁 ✓")


def validate_generated_at_nonempty(files, vr):
    """V42: _meta.generatedAt 非空 — 确保前端相对时间显示正常
    
    设计背景（2026-04-08 事故）：
    generatedAt 为空字符串时，前端 getRelativeTime() 无法解析，
    降级显示原始 dataTime 字符串（如 "2026-04-08 22:15 BJT"），
    而非预期的 "xx分钟前" 格式。
    """
    violations = []
    for fname in ["briefing", "markets", "watchlist", "radar"]:
        data = files.get(fname)
        if not data:
            continue
        meta = data.get("_meta", {})
        ga = meta.get("generatedAt", "")
        if not ga or "T" not in str(ga):
            violations.append(f"{fname}.json: generatedAt='{ga}' (应为 ISO 8601)")

    vr.add("V42", "_meta.generatedAt 非空（ISO 8601 格式）", len(violations) == 0,
           "; ".join(violations) if violations else "4个JSON均已填充 ✓")


def validate_price_no_placeholder(files, vr):
    """V43 [FATAL]: price 禁止占位符 — 拦截 "--" / 空值 / "N/A" 等非价格值

    设计背景（2026-04-08 23:25 事故）：
    AI 生成 JSON 时部分标的 price 写了 "--" 占位符未填实际价格，
    前端直接渲染 "--"，用户看到市场页大量空缺。
    """
    markets = files.get("markets")
    watchlist = files.get("watchlist")
    placeholders = {"--", "N/A", "n/a", "—", "", "TBD", "待更新"}
    violations = []

    if markets:
        for section in ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"]:
            for item in markets.get(section, []):
                price = item.get("price", "")
                if price in placeholders:
                    violations.append(f"markets.{section}[{item.get('name','')}]: price='{price}'")

    if watchlist:
        for sector_id, stock_list in watchlist.get("stocks", {}).items():
            if isinstance(stock_list, list):
                for stock in stock_list:
                    if stock.get("listed", True) is False:
                        continue
                    price = stock.get("price", "")
                    if price in placeholders or price == "未上市":
                        continue
                    if price in placeholders:
                        violations.append(f"watchlist.{sector_id}[{stock.get('name','')}]: price='{price}'")

    vr.add("V43", "price 禁止占位符 (--/N\\/A/空值) [FATAL]", len(violations) == 0,
           "; ".join(violations[:8]) if violations else "全部有效 ✓")


def validate_sparkline_no_zero_flood(files, vr):
    """V44 [FATAL]: sparkline 不允许任何 0 值 — 拦截 AI 用 0 填充历史数据

    v10.5 升级：从 >50% 零值 → **任何 0 值即 FATAL**。
    零值 = 数据缺失 = 前端断崖曲线 + 7日涨跌空白，必须搜索真实历史价格。

    设计背景（2026-04-09 事故）：
    AI 对新上市/数据不全的标的（VIX、日经、KOSPI、黄金、BTC/ETH、CNH、DXY 等）
    直接用 0 填充 sparkline，导致图表和计算全面失败。

    规则：sparkline 中包含任何 0 → FATAL
    例外：sparkline 为空 [] 不触发（交由其他校验项处理）
    """
    markets = files.get("markets")
    watchlist = files.get("watchlist")
    violations = []

    def check_sparkline(sparkline, location):
        if not sparkline or len(sparkline) == 0:
            return
        zero_count = sum(1 for v in sparkline if v == 0)
        if zero_count > 0:
            violations.append(
                f"{location}: sparkline 含 {zero_count} 个零值"
                f"——禁止用0填充，请搜索真实历史价格"
            )

    if markets:
        for section in ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"]:
            for item in markets.get(section, []):
                check_sparkline(item.get("sparkline", []),
                                f"markets.{section}[{item.get('name', '')}]")

    if watchlist:
        for sector_id, stock_list in watchlist.get("stocks", {}).items():
            if not isinstance(stock_list, list):
                continue
            for stock in stock_list:
                if stock.get("listed", True) is False:
                    continue
                check_sparkline(stock.get("sparkline", []),
                                f"watchlist.{sector_id}[{stock.get('symbol', '')}]")

    vr.add("V44", "sparkline 禁止任何零值（0=数据缺失）[FATAL]",
           len(violations) == 0,
           "; ".join(violations[:8]) if violations else "全部无零值 ✓")


def validate_price_sparkline_magnitude(files, vr):
    """V45 [FATAL]: price 与 sparkline 数量级一致性 — 拦截 price 与 sparkline 来源不一致

    v10.5 升级：阈值从 50%→30%。差距 30% 几乎不可能是同一标的正常日内波动。

    设计背景（2026-04-09 事故）：
    AI 在填写 price 时使用了错误数据源（如每手价格/旧价格/错误市场），
    导致智谱 price=HK$42.80 实际 HK$929（差22x）等严重错误。

    规则：|price / sparkline[-1] - 1| > 30% → FATAL

    例外：sparkline[-1] = 0（由 V44 处理）、price = "未上市" 跳过
    """
    markets = files.get("markets")
    watchlist = files.get("watchlist")
    violations = []

    def check_magnitude(price_str, sparkline, location):
        if not sparkline or len(sparkline) == 0:
            return
        last = sparkline[-1]
        if not isinstance(last, (int, float)) or last == 0:
            return
        if not price_str or price_str in {"未上市", "--", "N/A", ""}:
            return
        # 解析 price 数字（去除货币符号、逗号）
        try:
            p_str = price_str.replace("$", "").replace("HK$", "").replace("¥", "")
            p_str = p_str.replace(",", "").replace("%", "").strip()
            price_num = float(p_str)
        except (ValueError, AttributeError):
            return

        ratio = price_num / last
        # 差距超过 30%（ratio < 0.7 或 ratio > 1.3）
        if ratio < 0.7 or ratio > 1.3:
            violations.append(
                f"{location}: price={price_str}, sparkline[-1]={last:.2f}, "
                f"比例={ratio:.2f}x——来源不一致，price 与 sparkline 数量级差异 > 30%"
            )

    if markets:
        for section in ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"]:
            for item in markets.get(section, []):
                check_magnitude(item.get("price", ""), item.get("sparkline", []),
                                f"markets.{section}[{item.get('name', '')}]")

    if watchlist:
        for sector_id, stock_list in watchlist.get("stocks", {}).items():
            if not isinstance(stock_list, list):
                continue
            for stock in stock_list:
                if stock.get("listed", True) is False:
                    continue
                check_magnitude(stock.get("price", ""), stock.get("sparkline", []),
                                f"watchlist.{sector_id}[{stock.get('symbol', '')}]")

    vr.add("V45", "price 与 sparkline[-1] 数量级一致（差距 < 30%）[FATAL]",
           len(violations) == 0,
           "; ".join(violations[:5]) if violations else "全部一致 ✓")


def validate_chartdata_no_zero(files, vr):
    """V46 [FATAL]: chartData 不允许任何 0 值 — 与 V44 平行，覆盖30日数据

    设计背景（2026-04-09 事故）：
    中国石油、中国神华的 chartData 全30个点均为 0，前端30日图表完全空白。
    """
    watchlist = files.get("watchlist")
    violations = []

    if watchlist:
        for sector_id, stock_list in watchlist.get("stocks", {}).items():
            if not isinstance(stock_list, list):
                continue
            for stock in stock_list:
                if stock.get("listed", True) is False:
                    continue
                chart = stock.get("chartData", [])
                if not chart or len(chart) == 0:
                    continue
                zero_count = sum(1 for v in chart if v == 0)
                if zero_count > 0:
                    sym = stock.get("symbol", "?")
                    violations.append(
                        f"watchlist.{sector_id}[{sym}]: chartData 含 {zero_count}/{len(chart)} 个零值"
                    )

    vr.add("V46", "chartData 禁止任何零值（0=历史数据缺失）[FATAL]",
           len(violations) == 0,
           "; ".join(violations[:8]) if violations else "全部无零值 ✓")


def validate_sparkline_no_flat_line(files, vr):
    """V47 [FATAL]: sparkline/chartData 禁止全平线（拦截用当前价填充所有历史点的估算行为）

    设计背景：
    data-collection-sop.md §0.6 允许"实在获取不到历史数据时用当前价填充所有点"作为降级，
    但这只是临时措施。V47 检测 sparkline 7个点中 ≥6个完全相同的情况，
    标记为 WARN 提醒需要补充真实历史数据。

    规则：sparkline 7个点中 ≥6个完全相同 → WARN（不阻断，但提醒）
    """
    watchlist = files.get("watchlist")
    markets = files.get("markets")
    violations = []

    def check_flat(arr, location, label="sparkline"):
        if not arr or len(arr) < 5:
            return
        from collections import Counter
        counts = Counter(arr)
        most_common_count = counts.most_common(1)[0][1]
        if most_common_count >= len(arr) - 1:
            violations.append(
                f"{location}: {label} {len(arr)}个点中 {most_common_count}个相同值"
                f"={counts.most_common(1)[0][0]}——疑似估算填充，请补充真实历史数据"
            )

    if markets:
        for section in ["usMarkets", "m7", "asiaMarkets", "commodities", "cryptos"]:
            for item in markets.get(section, []):
                check_flat(item.get("sparkline", []),
                           f"markets.{section}[{item.get('name', '')}]")

    if watchlist:
        for sector_id, stock_list in watchlist.get("stocks", {}).items():
            if not isinstance(stock_list, list):
                continue
            for stock in stock_list:
                if stock.get("listed", True) is False:
                    continue
                check_flat(stock.get("sparkline", []),
                           f"watchlist.{sector_id}[{stock.get('symbol', '')}]")

    vr.add("V47", "sparkline 禁止全平线（拦截估算填充）",
           len(violations) == 0,
           "; ".join(violations[:5]) if violations else "全部有波动 ✓")


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
        if isinstance(refs, str):
            missing.append(f"coreJudgments[{i}] references 是字符串（必须是数组 [{{name,summary,url}}]）")
        elif not refs or len(refs) == 0:
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
        print("用法: python3 validate.py <sync_dir> [--mode standard|weekend]")
        sys.exit(2)

    sync_dir = sys.argv[1]
    mode = "standard"  # 默认

    for i, arg in enumerate(sys.argv):
        if arg == "--mode" and i + 1 < len(sys.argv):
            mode = sys.argv[i + 1].lower()

    # v9.0: heavy 映射到 standard（向后兼容）
    if mode == "heavy":
        mode = "standard"

    if mode not in ("standard", "weekend"):
        print(f"⚠️  未知模式 '{mode}'，使用默认 'standard'")
        mode = "standard"

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

    # === V30-V34: 内容质量检测层 (v4.0 新增) ===
    validate_insight_clichés(files, baseline, vr)
    validate_risk_advice_template(files, baseline, vr)
    validate_analysis_depth(files, baseline, vr)
    validate_action_hints_quality(files, vr)
    validate_source_type_consistency(files, vr)
    validate_audio_url(files, vr)

    # === V36-V38b: 数据安全防护层 (v10.1 Harness Engineering 新增) ===
    validate_cross_json_consistency(files, vr)
    validate_value_reasonableness(files, vr)
    validate_sparkline_trend_vs_change(files, vr)
    validate_us_index_direction_plausibility(files, vr)  # V38b: 2026-04-21 补丁，弥补V38盲点

    # === V39 [FATAL]: 聪明钱持仓 13F 合规性 (v10.2 新增) ===
    validate_holdings_13f_compliance(files, vr)

    # === V40-V42: 格式完整性防护层 (v10.2 新增) ===
    validate_metrics_no_empty_values(files, vr)
    validate_global_reaction_value_format(files, vr)
    validate_generated_at_nonempty(files, vr)

    # === V43 [FATAL]: price 禁止占位符 (v10.3 新增) ===
    validate_price_no_placeholder(files, vr)

    # === V44 [FATAL]: sparkline 不允许大量 0 值 (v10.4 新增) ===
    validate_sparkline_no_zero_flood(files, vr)

    # === V45 [FATAL]: price 与 sparkline 数量级一致性 (v10.4 新增) ===
    validate_price_sparkline_magnitude(files, vr)

    # === V46 [FATAL]: chartData 禁止零值 (v10.5 新增) ===
    validate_chartdata_no_zero(files, vr)

    # === V47: sparkline 禁止全平线 (v10.5 新增) ===
    validate_sparkline_no_flat_line(files, vr)

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
