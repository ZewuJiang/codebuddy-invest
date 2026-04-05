# investment-agent-daily-app — 投研鸭小程序数据生产 Skill

> **版本**: v1.0 | **类型**: CodeBuddy 自定义 Skill

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

Skill 将自动执行完整的六阶段工作流：交易日检测 → 数据采集 → 完整性门禁 → JSON生成 → 终审 → 上传云数据库。

## 文件结构

| 目录/文件 | 说明 |
|-----------|------|
| `SKILL.md` | 主控文档（工作流+铁律+版本日志） |
| `scripts/refresh_verified_snapshot.py` | sparkline/chartData 历史序列补全脚本 v2.1（方案A：只写这两个数组字段，其他所有字段由 AI 独立保障，脚本永远不触碰） |
| `references/json-schema.md` | **核心文件** — 4个JSON的完整字段规范 |
| `references/stock-universe.md` | 7板块标的池 + 分类规则 |
| `references/data-collection-sop.md` | 数据采集SOP（含sparkline/metrics额外采集） |
| `references/data-source-priority.md` | 数据源优先级 + 降级路径 |
| `references/ai-supply-chain-universe.md` | AI产业链知识库（复用自 daily） |
| `references/fund-universe.md` | 基金&大资金知识库（复用自 daily） |
| `references/media-watchlist.md` | 媒体追踪清单（复用自 daily） |
| `references/known-pitfalls.md` | App 版已知堵点 |
| `scripts/upload_to_cloud.py` | 云数据库上传脚本（复用自 daily） |
| `templates/` | JSON 模板文件 |

## 产出物

每次执行产出 4 个 JSON 文件：

| 文件 | 小程序页面 | 关键数据 |
|------|-----------|---------|
| `briefing.json` | 简报页 | 核心事件+判断+建议+情绪+聪明钱 |
| `markets.json` | 市场页 | 美股+M7+亚太+大宗+加密+sparkline+GICS热力图 |
| `watchlist.json` | 标的页 | 7板块×标的+详情+metrics+analysis+sparkline |
| `radar.json` | 雷达页 | 7项红绿灯+风险矩阵+事件日历+聪明钱详情 |

## 注意事项

- 需要联网环境（实时搜索采集数据）
- 周六～周日不执行
- 需要配置微信云数据库凭证才能上传
- JSON 文件始终保留在本地（即使上传失败）
