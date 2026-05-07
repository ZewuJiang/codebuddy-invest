# 投研鸭每日操作 Checklist v1.1

> **级别**：🔴=阻断，🟡=建议修复，✅=已确认

---

## Phase 2 结束后（写完 JSON 立即检查）

| # | 检查项 | 命令/方法 | 级别 |
|---|--------|---------|------|
| J1 | 4个 JSON 语法合法 | `for f in briefing markets watchlist radar; do python3 -m json.tool $SYNC_DIR/$DATE/$f.json > /dev/null && echo "✅ $f" \|\| echo "❌ $f"; done` | 🔴 |
| J2 | 4个 JSON 的 `date` 字段 = 今日 | `python3 -c "import json; [print(f,json.load(open(f)).get('date')) for f in [...]]"` | 🔴 |
| J3 | JSON 内不含未转义 ASCII 双引号 | `python3 -c "import json; [json.load(open(f)) for f in ['$SYNC_DIR/$DATE/briefing.json','$SYNC_DIR/$DATE/markets.json','$SYNC_DIR/$DATE/watchlist.json','$SYNC_DIR/$DATE/radar.json']]; print('✅ 双引号校验通过')"` | 🔴 |
| J4 | ARK `asOf` = 今日 `YYYY-MM-DD`，不含括号 | 目视检查 radar.json smartMoneyHoldings ARK条目 | 🟡 |
| J5 | `globalReaction[].value` 无括号且≤15字 | 目视检查每条 value | 🔴 |
| J6 | `trafficLights` 共7条，value↔status 自洽 | 对照 formulas.md 阈值表 | 🔴 |
| J7 | `sentimentScore` 与 `sentimentLabel` 枚举匹配 | 40-60=中性/60-75=偏贪婪/等 | 🔴 |
| J8 | `riskScore`/`riskLevel` 自洽（<40低/40-70中/≥70高） | 目视 | 🟡 |
| J9 | `alerts` 非空（VIX>20当日） | 若 VIX>20 但 `alerts=[]` → WARN，检查异动信号填充 | 🟡 |
| J10 | `riskAlerts` 非空（有持续性高风险事件时） | 若当日有 high impact 持续事件但 `riskAlerts=[]` → WARN，补充风险提示 | 🟡 |

---

## Phase 3 执行（run_daily.sh）

```bash
bash /Users/zewujiang/Desktop/AICo/codebuddy-invest/.codebuddy/skills/touyanduck-daily/scripts/run_daily.sh YYYY-MM-DD
```

| # | 检查项 | 预期输出 | 级别 |
|---|--------|---------|------|
| P1 | 第-1步日期子目录同步 | `✅ 已复制: YYYY-MM-DD/*.json → *.json` (4条) | 🔴 |
| P2 | 第0步 JSON 语法 | `✅ JSON 语法校验通过` | 🔴 |
| P3 | validate.py | `FATAL: 0` | 🔴 |
| P4 | 上传微信云数据库 | `4 成功 / 0 失败` | 🔴 |
| P5 | 上传 date = **今日** | 确认上传日志里的日期参数 | 🔴 |

---

## Phase 3 完成后验证

| # | 检查项 | 命令 | 级别 |
|---|--------|------|------|
| V1 | 云数据库中今日数据存在 | 上传日志 `发现已有数据，执行更新` 或 `新增成功` | 🔴 |
| V2 | 根目录 4 个 JSON 的 date = 今日 | `python3 -c "import json; d=json.load(open('miniapp_sync/markets.json')); print(d['date'])"` | 🔴 |
| V2b | 手工修正数据后必须重新上传 | `python3 upload_to_cloud.py "$SYNC_DIR" "YYYY-MM-DD"` | 🔴 |
| V4 | 小程序下拉刷新后显示今日数据 | 手机打开小程序下拉 | ✅ |

---

## 常见故障快速排查

| 症状 | 根因 | 修复 |
|------|------|------|
| 小程序数据不更新 | 上传了旧日期数据 | `python3 upload_to_cloud.py "$SYNC_DIR" "YYYY-MM-DD"` |
| JSON 语法错误 | 含未转义双引号或语法问题 | `python3 -m json.tool xxx.json` 定位错误行 |
| validate.py 报 FATAL | 数据质量问题 | 看报告修复对应字段后重跑 |
| ARK asOf 显示带括号 | 数据写了 `"2026-04-21（ARK每日...）"` | 直接写 `"2026-04-21"` |
| 小程序显示昨日数据 | app.js 取今日日期查询，但云库只有昨日 | 确认上传命令日期参数是今日 |
| 涨跌方向全错（+/-符号反） | AI 首版 JSON change 符号错误 | 修正 JSON 后重新上传 |
