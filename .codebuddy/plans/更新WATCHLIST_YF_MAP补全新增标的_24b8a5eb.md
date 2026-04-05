---
name: 更新WATCHLIST_YF_MAP补全新增标的
overview: 更新 refresh_verified_snapshot.py 的 WATCHLIST_YF_MAP，补全新5板块所有美股标的，删除旧板块已移除标的，同时尝试加入港股/A股映射（yfinance支持，失败自动跳过）。
todos:
  - id: update-watchlist-yf-map
    content: 更新 refresh_verified_snapshot.py 的 WATCHLIST_YF_MAP：删除旧6只标的，补全新5板块所有美股/港股/A股映射（含.SS转换），版本号升至 v2.2，更新注释和底部打印日志
    status: completed
  - id: fix-skill-pitfalls
    content: 更新 known-pitfalls.md 和 SKILL.md，固化 A股 yfinance ticker 格式陷阱（上交所 .SH 必须改为 .SS），防止未来再犯
    status: completed
    dependencies:
      - update-watchlist-yf-map
  - id: run-and-upload
    content: 运行 refresh_verified_snapshot.py 补全 sparkline/chartData，执行 upload_to_cloud.py 上传云数据库，验证补全成功的标的数量
    status: completed
    dependencies:
      - update-watchlist-yf-map
---

## 用户需求

执行方案A：更新 `refresh_verified_snapshot.py` 中的 `WATCHLIST_YF_MAP`，将新5板块架构下所有美股、港股、A股标的的 yfinance ticker 映射补全，确保每次运行 `run_daily.sh` 时能自动下载真实历史序列（sparkline/chartData）。

## 产品概述

投研鸭小程序的 sparkline/chartData 数据补全脚本，目前映射表仍为旧7板块的15只标的，导致新增的美股（AAPL/GOOGL/ANET等）和部分港股/A股标的无法获取真实历史走势数据，fallback 为 AI 估算值。

## 核心功能

- 删除旧板块已下线标的（MRVL/MU/COST/NVO/LLY/JPM）
- 新增美股映射：AAPL/GOOGL/ANET/PLTR/RBLX/TEM/KO/OXY/AXP（+ META/AMZN 已在 markets.json M7 中，watchlist 中也需映射）
- 新增港股映射：0700.HK/9988.HK/2513.HK/0100.HK（yfinance 支持，成功则用真实数据，失败自动跳过）
- 新增 A 股映射：300308.SZ/688256.SZ/300750.SZ/002594.SZ（深交所，yfinance 格式 .SZ），600519.SS（上交所茅台，注意 yfinance 格式是 .SS 不是 .SH）
- 字节跳动（未上市）不加映射，跳过
- 更新脚本版本号、注释和底部打印说明
- 同步更新 SKILL.md 的相关说明（A股 .SS 格式教训）
- 改完后立即运行脚本补全数据并上传云数据库

## 技术栈

- Python 3，yfinance 库（已有）
- 脚本路径：`.codebuddy/skills/investment-agent-daily-app/scripts/refresh_verified_snapshot.py`
- 数据文件：`workflows/investment_agent_data/miniapp_sync/watchlist.json`

## 实现思路

**一次性改动，根治问题**：将 `WATCHLIST_YF_MAP` 从旧15只标的完整重写为新5板块30只标的的映射表。港股/A股加入映射表后，成功则自动写入真实历史数据，失败则脚本失败安全机制自动跳过保留AI估算值——无需任何额外分支逻辑，现有架构完全满足。

**港股/A股 yfinance 格式说明**：

- 港股：`0700.HK`（yfinance 格式与交易代码完全相同）
- 深交所 A 股：`300308.SZ`/`688256.SZ`/`300750.SZ`/`002594.SZ`（直接用 `.SZ`）
- 上交所 A 股：`600519.SS`（**注意**：yfinance 用 `.SS` 而非 `.SH`，必须转换）

## 关键决策

| 决策点 | 选择 | 理由 |
| --- | --- | --- |
| 港股是否加入映射 | 加入 | yfinance 支持，失败安全机制保底，有就用真实数据 |
| A股是否加入映射 | 加入 | 同上，深交所.SZ直接可用，上交所.SS需转换 |
| 字节跳动 | 不加 | 未上市，无 yfinance 数据 |
| META/AMZN | 加入 | watchlist ai_infra 板块有这两只，需补全 |
| NOW(ServiceNow) | 加入 | ai_app 板块标的 |


## 实现细节

**WATCHLIST_YF_MAP 完整重写**（按板块注释分组，便于维护）：

```python
WATCHLIST_YF_MAP: Dict[str, str] = {
    # ── ai_infra：AI算力链 ──────────────────────────────────────
    "NVDA":       "NVDA",
    "AVGO":       "AVGO",
    "TSM":        "TSM",
    "MSFT":       "MSFT",
    "GOOGL":      "GOOGL",
    "META":       "META",
    "AMZN":       "AMZN",
    "AAPL":       "AAPL",
    "ASML":       "ASML",
    "AMD":        "AMD",
    "ANET":       "ANET",
    "300308.SZ":  "300308.SZ",   # 中际旭创（深交所）
    # ── ai_app：AI应用 ────────────────────────────────────────
    "PLTR":       "PLTR",
    "TSLA":       "TSLA",
    "RBLX":       "RBLX",
    "TEM":        "TEM",
    "NOW":        "NOW",
    # ByteDance：未上市，跳过
    # ── cn_ai：国产AI（港股/A股）──────────────────────────────
    "0700.HK":    "0700.HK",     # 腾讯（港股）
    "9988.HK":    "9988.HK",     # 阿里巴巴（港股）
    "2513.HK":    "2513.HK",     # 智谱AI（港股）
    "0100.HK":    "0100.HK",     # MiniMax（港股）
    "688256.SZ":  "688256.SZ",   # 寒武纪（科创板）
    # ByteDance：未上市，跳过
    # ── smart_money：聪明钱 ───────────────────────────────────
    "BRK.B":      "BRK-B",       # 伯克希尔（yfinance特殊格式）
    "KO":         "KO",
    "OXY":        "OXY",
    "600519.SH":  "600519.SS",   # 茅台（上交所：.SH→.SS）
    "PDD":        "PDD",
    "AXP":        "AXP",
    # ── hot_topic：本期热点（动态，当前为关税主题）───────────────
    "300750.SZ":  "300750.SZ",   # 宁德时代（深交所）
    "002594.SZ":  "002594.SZ",   # 比亚迪（深交所）
}
```

**关键注意事项**：

- `hot_topic` 板块标的每期可变，但当前映射表需包含当期实际标的；未来如 hot_topic 更换标的，需同步更新映射表（或 AI 执行时提示）
- A股上交所 `.SH` → `.SS` 转换是常见陷阱，在 Skill 规范中固化

## 目录结构

```
.codebuddy/skills/investment-agent-daily-app/scripts/
    refresh_verified_snapshot.py   # [MODIFY] 重写 WATCHLIST_YF_MAP，更新版本号+注释

.codebuddy/skills/investment-agent-daily-app/
    SKILL.md                       # [MODIFY] 新增 A股 yfinance ticker 格式说明（.SH→.SS陷阱）

.codebuddy/skills/investment-agent-daily-app/references/
    known-pitfalls.md              # [MODIFY] 新增 A股 ticker 格式陷阱条目
```