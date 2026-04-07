# investment-agent-html — 投研鸭 HTML 报告生成器

> **版本**: v1.0 | **类型**: CodeBuddy 自定义 Skill

## 简介

独立采集全球市场数据，生成原生结构化 JSON，**渲染为单个自包含 HTML 文件**，双击浏览器打开即可查看——视觉效果对标投研鸭小程序。

**零配置 · 零环境变量 · 零微信开发者工具**

## 快速安装（2 步即可使用）

### 1. 放置 Skill

将整个 `investment-agent-html/` 文件夹复制到项目的 `.codebuddy/skills/` 目录下：

```
your-project/
└── .codebuddy/
    └── skills/
        └── investment-agent-html/   ← 放这里
            ├── SKILL.md
            ├── README.md
            ├── references/
            ├── templates/
            └── scripts/
```

### 2. 使用

在对话中输入以下任一关键词即可自动触发：

- `投资报告`
- `投资HTML`
- `投研鸭报告`
- `investment report`

Skill 将自动执行完整工作流，最终产出：

```
workflows/investment_agent_data/miniapp_sync/touyanduck-2026-04-07.html
```

**双击打开，浏览器里就是小程序同款效果 🦆**

## 产出物

每次执行产出 **4 个 JSON + 1 个 HTML 文件**：

| 文件 | 说明 |
|------|------|
| `briefing.json` | 简报数据（核心事件+判断+建议+情绪+聪明钱+风险点） |
| `markets.json` | 市场数据（美股+M7+亚太+大宗+加密+GICS热力图） |
| `watchlist.json` | 标的数据（5板块×28-35只标的+详情+metrics） |
| `radar.json` | 雷达数据（红绿灯+聪明钱+本周前瞻+预测市场） |
| **`touyanduck-YYYY-MM-DD.html`** | **自包含 HTML 报告（核心产出物）** |

## HTML 报告特性

- **单文件自包含**：CSS + JS + SVG 全部内联，零外部依赖
- **4 个 Tab**：简报 / 市场 / 标的 / 雷达，完整复刻小程序
- **SVG sparkline**：走势图用 SVG 渲染，比 Canvas 更清晰
- **折叠展开**：stock-card 点击展开详情，section-card 可折叠
- **移动端友好**：max-width 480px 居中，响应式设计
- **完全离线**：不需要网络，不需要服务器

## 文件结构

| 目录/文件 | 说明 |
|-----------|------|
| `SKILL.md` | 主控文档（工作流+八大铁律+致命错误清单） |
| `scripts/run_daily.sh` | 一键串联脚本（JSON校验→sparkline补全→渲染HTML） |
| `scripts/render_html.py` | **核心脚本** — 4个JSON → 单文件HTML |
| `scripts/refresh_verified_snapshot.py` | sparkline/chartData 历史序列补全 |
| `scripts/requirements.txt` | Python 依赖（pandas + akshare） |
| `references/` | 11个知识库文档 + 黄金样本 |
| `templates/` | JSON 模板 + HTML 模板 |

## 与 investment-agent-daily-app 的区别

| 维度 | `daily-app`（小程序版） | **本 Skill（HTML 版）** |
|------|----------------------|----------------------|
| **产出物** | 4 个 JSON + 上传云数据库 | **4 个 JSON + 1 个 HTML 文件** |
| **查看方式** | 微信开发者工具 / 手机微信 | **任何浏览器，双击打开** |
| **环境依赖** | 微信云开发 + AppID + 环境变量 | **零依赖** |
| **网络需求** | 查看时需联网 | **完全离线** |
| **数据质量** | 完全一致 | **完全一致**（共享相同的数据采集流程） |

## 注意事项

- 需要联网环境执行 Skill（实时搜索采集数据）
- HTML 文件一旦生成，查看时不需要联网
- **可选安装**：`pip3 install pandas akshare` — 安装后 sparkline 走势图使用真实历史数据（更精确）；不安装也能正常运行，走势图使用 AI 估算值
- sparkline/chartData 补全依赖 AkShare，网络不佳时会自动跳过
