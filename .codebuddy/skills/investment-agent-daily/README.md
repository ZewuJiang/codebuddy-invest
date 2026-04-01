# investment-agent-daily — 投资Agent每日策略简报 Skill

> **版本**: v19.3 | **类型**: CodeBuddy / Claude Code 自定义 Skill

## 简介

每日自动生成投资策略简报（MD + PDF），覆盖全球市场、AI产业链、基金大资金动向，面向高净值个人投资者。

## 最新更新

- **v19.3（2026-04-01）**：补齐 v19.2 遗留落地项，修正 `ai-supply-chain-universe.md` 正文 Ticker，升级行动建议占位为明确动作/触发条件，并清除周一模板月涨跌占位中的“—”。
- **v19.2（2026-04-01）**：修正核心规则计数、标准日报模板口径、周一模板旧引用和 AI 产业链错误Ticker，同步布伦特主指标与 `YYYYMMDD` 命名规则。

## 快速安装

### 1. 放置 Skill

将整个 `investment-agent-daily/` 文件夹复制到你的项目的 `.codebuddy/skills/` 目录下：

```
your-project/
└── .codebuddy/
    └── skills/
        └── investment-agent-daily/   ← 放这里
            ├── SKILL.md
            ├── README.md
            ├── references/
            ├── templates/
            ├── scripts/
            └── notes/
```

### 2. 安装系统级依赖（PDF转换需要）

PDF转换脚本 `scripts/md_to_pdf.py` 基于 [WeasyPrint](https://weasyprint.org/)，需要以下系统库：

**macOS**（推荐 Homebrew）：
```bash
brew install cairo pango gdk-pixbuf libffi
```

**Ubuntu / Debian**：
```bash
sudo apt-get install libcairo2-dev libpango1.0-dev libgdk-pixbuf2.0-dev libffi-dev
```

**其他平台**：参见 [WeasyPrint 官方安装文档](https://doc.courtbouillon.org/weasyprint/stable/first_steps.html)

### 3. 安装 Python 依赖

```bash
cd .codebuddy/skills/investment-agent-daily/scripts
pip3 install -r requirements.txt
```

### 4. 配置输出路径

打开 `SKILL.md`，找到 **"报告输出路径（OrbitOS）"** 部分，将默认路径替换为你的报告输出目录：

```
# 将此路径：
/Users/zewujiang/Desktop/OrbitOS/20_日常监控/每日策略简报/

# 替换为你的路径，例如：
/path/to/your/reports/每日策略简报/
```

同样，在 **"第三阶段：MD转PDF"** 部分，将脚本的 `cd` 路径替换为你的实际路径。已有注释行提供了通用格式参考。

## 使用方法

安装完成后，在对话中输入以下任一关键词即可自动触发：

- `投资Agent`
- `每日分析`
- `投资分析`
- `每日报告`
- `晨报`

Skill 将自动执行完整的五阶段工作流：数据采集 → 验证门禁 → 撰写报告 → 终审+PDF → 交付。

## 文件结构

| 目录/文件 | 说明 |
|-----------|------|
| `SKILL.md` | 主控文档（工作流+规则+版本日志） |
| `references/` | 详细规则/知识库（核心规则、数据采集SOP、AI产业链、基金清单等） |
| `templates/` | 报告模板（标准日报 + 周一特殊模板） |
| `scripts/` | PDF转换脚本 + 依赖清单 |
| `notes/` | 运行时笔记（自动生成） |

## 自定义

- **修改持仓标的**：编辑 `references/ai-supply-chain-universe.md` 和 `references/fund-universe.md`
- **调整媒体源**：编辑 `references/media-watchlist.md`
- **修改报告格式**：编辑 `references/report-format-guide.md`
- **清空进化日志**：如果不需要原始作者的进化记录，可清空 `references/evolution-log.md` 中的"进化记录"区，保留模板结构即可

## 注意事项

- Skill 需要联网环境（实时搜索采集数据）
- 周六～周日不出报告
- 每天只出一份简报（不区分晨报/晚报）
- PDF为单页长图格式，文件大小通常 2-5MB
