# 项目长期约定（codebuddy-invest）

## Skill 唯一真源约定
- `investment-agent-daily` 的**唯一权威副本 = `~/.workbuddy/skills/investment-agent-daily/`**（用户级）。
  - 2026-08-31 已清理双副本分叉：项目级 `codebuddy-invest/.codebuddy/skills/investment-agent-daily` 已删除，其内容（2 条独有进化记录）已合并进用户级。
  - **禁止**再把它复制/同步到项目级目录。用户级 SKILL.md 顶部已写入「🔒 唯一真源声明」，自动化 prompt 亦有「禁止复制 skill」条款。
- ⚠️ 技术要点：WorkBuddy 的 skill 扫描器**不跟随符号链接**——想用软链接让项目级指向用户级是行不通的（实测 skill 会从可用列表消失，Glob 也搜不到）。要统一两份只能用「合并内容 + 删除其一」。

## 环境要点（易踩坑）
- PDF 转换依赖 markdown / weasyprint **只装在 `/opt/homebrew/bin/python3`**；PATH 中优先级更高的 WorkBuddy 内置解释器 3.13.12 没有这些包。
  执行 `md_to_pdf.py` 必须写死：`/opt/homebrew/bin/python3 md_to_pdf.py ...`
- 系统时区为纽约（America/New_York），所有交易日/日期判断必须用 `TZ='Asia/Shanghai' date`，禁止裸 `date`。
- 自动化任务按本机（纽约）时间触发，冬令时起北京时间会漂移 1 小时（10:00 → 11:00），需留意校准提示。

## Skill 版本与计数口径（改 skill 时必须同步，否则自相矛盾）
- 当前投资日报 skill = **v19.9**（2026-08-31）。以下四处数字互相绑定，改动任一处必须全改：
  1. SKILL.md 版本头（核心规则 N 条 / 终审清单 N 项 / 致命错误 N 条）
  2. SKILL.md「核心规则速查」标题 + 各行条数求和
  3. SKILL.md「致命错误清单」标题 + 实际行数
  4. SKILL.md「知识库引用索引」core-rules 条数 + core-rules.md「简易终审清单」标题与实际行数
- 现值：**核心规则 33 条 / 终审清单 26 项 / 致命错误 25 条 / 速查表各行求和 = 33**。
- v19.9 主题：美股休市检测（第零阶段强制联网确认上一美股交易日是否休市，禁凭记忆判节假日；known-pitfalls 防坑清单改为强制预读）。

## 日报产出
- 输出目录：`/Users/zewujiang/Desktop/OrbitOS/20_日常监控/每日策略简报/`
- 命名：`投资Agent-每日策略简报-{YYYYMMDD}.md/.pdf`（YYYYMMDD 取北京时间）
- 历史 PDF 体积基线 0.7–1.1MB（SKILL.md 里"2-5MB"的旧标准已过时）
