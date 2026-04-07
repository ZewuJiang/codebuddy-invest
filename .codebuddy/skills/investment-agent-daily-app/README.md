# investment-agent-daily-app — 投研鸭小程序数据生产 Skill

> **版本**: v7.1 | **类型**: CodeBuddy 自定义 Skill

## 简介

独立采集全球市场数据，生成原生结构化 JSON，上传到微信云数据库，驱动投研鸭小程序实时展示。

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

Skill 将自动执行完整的七阶段工作流：日期检测+模式路由 → 数据采集 → 完整性门禁 → JSON生成 → 终审（含B1-B12/Q1-Q8/W1-W9质量门禁） → sparkline补全+上传 → 执行复盘。

## 四档内容引擎

| 时机 | 模式 | 说明 |
|------|------|------|
| 周一（盘后/当天首次） | Heavy + 周一特别版 | 全量采集+上周回顾+本周展望 |
| 周二～周五（当天首次） | Heavy | 全量采集+分析+建议 |
| 工作日后续每4小时 | **Refresh**（v7.0新增） | **刷新行情+红绿灯+异动信号，保留深度分析** |
| 周末/休市日 | Weekend | 媒体深度扫描+周度总结+前瞻 |

## 文件结构

| 目录/文件 | 说明 |
|-----------|------|
| `SKILL.md` | 主控文档（工作流+八大铁律+致命错误清单+版本日志） |
| `scripts/run_daily.sh` | 一键串联脚本 v3.0（JSON校验→sparkline补全→上传） |
| `scripts/refresh_verified_snapshot.py` | sparkline/chartData 历史序列补全脚本 v3.0（AkShare 新浪源+东方财富 fallback，方案A：只写 sparkline/chartData 两个字段） |
| `scripts/upload_to_cloud.py` | 云数据库上传+回读校验脚本 v1.1 |
| `scripts/requirements.txt` | Python 依赖（requests + pandas + akshare） |
| `references/json-schema.md` | **核心文件** — 4个JSON完整字段规范 v4.4（含B1-B12/Q1-Q8/W1-W9质量门禁） |
| `references/stock-universe.md` | 5板块标的池 v2.1（ai_infra/ai_app/cn_ai/smart_money/hot_topic） |
| `references/data-collection-sop.md` | 数据采集SOP v1.9（含Batch A情绪数据+Refresh精简批次R0-R3+R1 M7默认策略） |
| `references/data-source-priority.md` | 数据源优先级 v1.6 + 降级路径 |
| `references/ai-supply-chain-universe.md` | AI产业链24环标的知识库 |
| `references/fund-universe.md` | 三梯队26家基金+策略师知识库 v18.0 |
| `references/media-watchlist.md` | 三级媒体清单+扫描SOP |
| `references/known-pitfalls.md` | App版已知堵点 v3.2（36条，含Refresh模式堵点） |
| `references/weekend-mode.md` | Weekend 模式完整规范（采集+产出+工作流） |
| `references/refresh-mode.md` | **Refresh 模式完整规范 v1.1**（精简采集+字段边界表+精简终审+工作流+sentimentScore微调规则+refreshCount） |
| `references/briefing-golden-sample.json` | 简报页黄金样本（2026-04-06版，质量基准） |
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
