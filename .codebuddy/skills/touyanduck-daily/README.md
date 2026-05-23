# touyanduck-daily — 投研鸭小程序数据生产 Skill

> **版本**: v14.0 | **类型**: CodeBuddy 自定义 Skill

## 简介

独立采集全球市场数据，生成原生结构化 JSON，通过 HTTP 上传到自建服务器（miniapp.touyanduck.com），驱动投研鸭小程序实时展示。

**v11.4+ 核心架构**：
1. **Phase 1 并行采集**：4 组并发（媒体/行情/亚太大宗/基金），采集时间减少 60-70%
2. **Context 压缩铁律**：web_fetch 后立即提取最小字段集丢弃 HTML，上下文 ~76k→~35k
3. **References 分层加载**：四批按需加载（L1/L2/L3/L4），不再一次性全部加载
4. **Generator-Verifier 内联自校验**：Phase 2 每个 JSON 写完即检（16/20 项 FATAL 前置拦截）

**与 `investment-agent-daily` 的关系**：完全独立。`daily` 输出给人读的 MD/PDF 报告，本 Skill（`touyanduck-daily`）输出给机器读的 JSON 数据。两者可独立触发，互不影响。

## 快速安装

### 1. 放置 Skill

将整个 `touyanduck-daily/` 文件夹复制到项目的 `.codebuddy/skills/` 目录下：

```
your-project/
└── .codebuddy/
    └── skills/
        └── touyanduck-daily/   ← 放这里
            ├── SKILL.md
            ├── README.md
            ├── references/
            ├── templates/
            └── scripts/
```

### 2. 安装 Python 依赖

```bash
cd .codebuddy/skills/touyanduck-daily/scripts
pip3 install -r requirements.txt
```

## 使用方法

在对话中输入以下任一关键词即可自动触发：

- `投资App`
- `小程序数据`
- `投研鸭数据`
- `app数据更新`
- `miniapp sync`

Skill 将自动执行完整的工作流：日期检测+模式路由 → **Phase 1 并行采集（4组并发+Context压缩）** → 完整性门禁 → **Phase 2 JSON生成+内联自校验（Generator-Verifier）** → 每日操作Checklist → 公式自动计算(auto_compute.py) → 终审(validate.py v6.2 + 57项校验 + 20项FATAL门禁) → sparkline补全 → 上传自建服务器 → 执行复盘。

## 二档内容引擎

| 时机 | 模式 | 说明 |
|------|------|------|
| 周一~周五（每次执行） | **Standard** | 全量采集+分析+建议（每次都是高质量全量产出） |
| 周末/休市日 | **Weekend** | 媒体深度扫描+周度总结+前瞻 |

## 文件结构

| 目录/文件 | 说明 |
|-----------|------|
| `SKILL.md` | 主控文档（工作流+九大铁律+致命错误清单+并行采集+Context压缩+分层加载+Generator-Verifier） |
| `scripts/run_daily.sh` | 一键串联脚本（子目录同步+JSON校验→auto_compute→anchor_fetcher→validate→sparkline→上传） |
| `scripts/upload_to_server.sh` | HTTP 上传到自建服务器（SCP → miniapp.touyanduck.com） |
| `scripts/auto_compute.py` | 公式自动计算（riskScore/riskLevel/sentimentLabel/trafficLights.status/metrics联动/16类字段） |
| `scripts/validate.py` | 数据质量校验（57项 FATAL/WARN 双级，20项FATAL，V48/V49真值锚点+上传一致性门禁） |
| `scripts/anchor_fetcher.py` | 真值锚点拉取（FRED/yfinance/CoinGecko，CNH/DXY/VIX全备源补强） |
| `scripts/refresh_verified_snapshot.py` | sparkline/chartData 历史序列补全 |
| `scripts/requirements.txt` | Python 依赖 |
| `references/json-schema.md` | **核心文件** — 4个JSON完整字段规范（含B1-B12/Q1-Q8/W1-W9质量门禁） |
| `references/inline-verifier-rules.md` | Generator-Verifier 内联自校验规则（16项可内联FATAL+修复SOP） |
| `references/data-collection-sop.md` | 数据采集SOP（含§0.4自媒体陷阱+§0.8并行分组+§0.9最小字段集+§0.10 JSON双引号防治） |
| `references/stock-universe.md` | 5板块标的池 |
| `references/data-source-priority.md` | 数据源优先级 + 降级路径 |
| `references/formulas.md` | 所有公式唯一权威源 |
| `references/golden-baseline.json` | 结构化基线定义 |
| `references/templates.md` | 交付模板集合 |
| `references/known-pitfalls.md` | 已知堵点（65条活跃+6条归档） |
| `references/daily-checklist.md` | 完整每日操作Checklist（J1-J10/P1-P5/V1-V4/故障排查） |
| `references/weekend-mode.md` | Weekend 模式规范 |
| `references/holdings-cache.json` | 持仓数据缓存（3家×Top10） |
| `references/briefing-golden-sample.json` | 黄金样本（2026-04-06版） |
| `templates/daily-standard.json` | 标准日JSON模板 |
| `templates/monday-special.json` | 周一特别版JSON模板 |

## 产出物

每次执行产出 4 个 JSON 文件：

| 文件 | 小程序页面 | 关键数据 |
|------|-----------|---------|
| `briefing.json` | 简报页 | 核心事件+判断+actionHints+情绪+聪明钱+topHoldings+风险点 |
| `markets.json` | 市场页 | 美股+M7+亚太+大宗+加密+sparkline+GICS热力图+6条Insight |
| `watchlist.json` | 标的页 | 5板块×28-35只标的+详情+metrics+analysis+sparkline+chartData |
| `radar.json` | 雷达页 | 7项红绿灯+聪明钱三梯队+持仓快照+本周前瞻+预测市场+异动信号 |

## 注意事项

- 需要联网环境（实时搜索采集数据）
- 支持 Weekend 模式（周末/休市日产出周度深度分析）
- JSON 文件始终保留在本地（即使上传失败）
- 公式字段由 `auto_compute.py` 自动计算，AI 无需手算
