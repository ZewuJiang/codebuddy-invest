# investment-agent-daily-app — 投研鸭小程序数据生产 Skill

> **版本**: v11.3 | **类型**: CodeBuddy 自定义 Skill

## 简介

独立采集全球市场数据，生成原生结构化 JSON，上传到微信云数据库，驱动投研鸭小程序实时展示。

**v11.2 四大架构升级 + Harness 深度体检 + 规范清理**：
1. **Phase 1 并行采集**：4 组并发（媒体/行情/亚太大宗/基金），采集时间减少 60-70%
2. **Context 压缩铁律**：web_fetch 后立即提取最小字段集丢弃 HTML，上下文 ~76k→~35k
3. **References 分层加载**：四批按需加载（L1/L2/L3/L4），不再一次性全部加载
4. **Generator-Verifier 内联自校验**：Phase 2 每个 JSON 写完即检（14/17 项 FATAL 前置拦截）
5. **v11.1 新增**：Checklist J3 机器可执行化 + 前端代码修复 + 废弃文件清理

**与 `investment-agent-daily` 的关系**：完全独立。`daily` 输出给人读的 MD/PDF 报告，本 Skill 输出给机器读的 JSON 数据。两者可独立触发，互不影响。

## 快速安装

### 1. 放置 Skill

将整个 `investment-agent-daily-app/` 文件夹复制到项目的 `.codebuddy/skills/` 目录下：

```
your-project/
└── .codebuddy/
    └── skills/
        └── investment-agent-daily-app/   ← 放这里
            ├── SKILL.md
            ├── README.md
            ├── references/
            ├── templates/
            └── scripts/
```

### 2. 安装 Python 依赖

```bash
cd .codebuddy/skills/investment-agent-daily-app/scripts
pip3 install -r requirements.txt
```

### 3. 配置微信云数据库

设置环境变量：

```bash
export WX_APPID="你的AppID"
export WX_APPSECRET="你的AppSecret"
export WX_CLOUD_ENV="你的云环境ID"
```

### 4. 确保云数据库集合已创建

在微信开发者工具的云开发控制台中，确保已创建以下 4 个集合：
- `briefing`
- `markets`
- `watchlist`
- `radar`

## 使用方法

在对话中输入以下任一关键词即可自动触发：

- `投资App`
- `小程序数据`
- `投研鸭数据`
- `app数据更新`
- `miniapp sync`

Skill 将自动执行完整的工作流：日期检测+模式路由 → **Phase 1 并行采集（4组并发+Context压缩）** → 完整性门禁 → **Phase 2 JSON生成+内联自校验（Generator-Verifier）** → 每日操作Checklist → 公式自动计算(auto_compute.py) → 终审(validate.py v5.7 + 55项校验 + B1-B12/Q1-Q8/W1-W9质量门禁) → sparkline补全+上传 → 执行复盘。

## 二档内容引擎

| 时机 | 模式 | 说明 |
|------|------|------|
| 周一~周五（每次执行） | **Standard** | 全量采集+分析+建议（每次都是高质量全量产出） |
| 周末/休市日 | **Weekend** | 媒体深度扫描+周度总结+前瞻 |

> v11.2 架构升级：Phase 1 并行采集（4组并发）+ Context 压缩（~76k→~35k）+ References 分层加载（L1/L2/L3/L4）+ Generator-Verifier 内联自校验（14/17项FATAL前置拦截）+ 每日操作Checklist + 前端代码修复 + 规范体系深度清理。validate.py v5.7（55项校验）。

## 文件结构

| 目录/文件 | 说明 |
|-----------|------|
| `SKILL.md` | 主控文档 v11.2（工作流+九大铁律+致命错误清单+并行采集+Context压缩+分层加载+Generator-Verifier+每日Checklist） |
| `scripts/run_daily.sh` | 一键串联脚本 v6.2（第-0.5步涨跌方向目视摘要+第-1步日期子目录同步+JSON校验→auto_compute→validate→sparkline→上传） |
| `scripts/auto_compute.py` | 公式自动计算 v3.0（riskScore/riskLevel/sentimentLabel/trafficLights.status/metrics联动/15类字段） |
| `scripts/validate.py` | 数据质量校验 v5.7（55项 FATAL/WARN 双级，17项FATAL，含V38b方向合理性） |
| `scripts/refresh_verified_snapshot.py` | sparkline/chartData 历史序列补全 v3.0 |
| `scripts/upload_to_cloud.py` | 云数据库上传+回读校验 v1.2 |
| `scripts/generate_audio.py` | 语音播报生成器 v3.0（MiniMax TTS） |
| `scripts/requirements.txt` | Python 依赖 |
| `references/json-schema.md` | **核心文件** — 4个JSON完整字段规范 v5.0（含B1-B12/Q1-Q8/W1-W9质量门禁） |
| `references/inline-verifier-rules.md` | **v11.0 新增** — Generator-Verifier 内联自校验规则 v1.0（14项可内联FATAL+修复SOP） |
| `references/data-collection-sop.md` | 数据采集SOP v3.1（含§0.4自媒体陷阱+§0.8并行分组+§0.9最小字段集+§0.10 JSON双引号防治） |
| `references/stock-universe.md` | 5板块标的池 v2.1 |
| `references/data-source-priority.md` | 数据源优先级 v1.6 + 降级路径 |
| `references/formulas.md` | 所有公式唯一权威源 v1.0 |
| `references/golden-baseline.json` | 结构化基线定义 v1.2 |
| `references/templates.md` | 交付模板集合 v1.1 |
| `references/known-pitfalls.md` | 已知堵点 v5.5（64条活跃+6条归档） |
| `references/weekend-mode.md` | Weekend 模式规范 v4.1 |
| `references/holdings-cache.json` | 持仓数据缓存（3家×Top10） |
| `references/briefing-golden-sample.json` | 黄金样本（2026-04-06版） |
| `templates/daily-standard.json` | 标准日JSON模板 v5.7 |
| `templates/monday-special.json` | 周一特别版JSON模板 v5.7 |

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
- 需要配置微信云数据库凭证才能上传
- JSON 文件始终保留在本地（即使上传失败）
- 公式字段由 `auto_compute.py` 自动计算，AI 无需手算
