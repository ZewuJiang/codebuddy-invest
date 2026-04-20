# 已知堵点与应对策略 — App版（v4.5）

> **用途**：投研鸭小程序数据生产过程中的已知堵点与应对方案（共56条活跃）。
> **核心原则**：先保真，再发布。核心行情缺失时宁可阻断，也不能用估算值顶上。

---

## 数据采集堵点

| # | 堵点 | 降级路径 | 频率 |
|---|------|---------|------|
| 1 | Google Finance 403/超时 | → web_search → 东方财富/StockAnalysis | 高 |
| 2 | sparkline 历史数据无法获取 | → 回到采集批次重试；仍失败 → **阻断发布** | 高 |
| 3 | chartData 30天数据缺失 | → 回到数据源重采，**禁止插值/估算** | 中 |
| 4 | metrics PE(TTM) 缺失 | → 标注"—"，不阻断 | 中 |
| 5 | 某板块标的全部失败 | → stock-universe.md 备选标的替代 | 低 |
| 6 | 港股/A股数据获取困难 | → 东方财富/同花顺 → 智通财经 | 中 |
| 7 | 大宗期货 Google 不支持 | → OilPrice.com → 金投网 | 中 |
| 8 | AkShare CNH 历史序列失败 | → **阻断发布**，禁止退化到 CNY=X 估算 | 中 |
| 9 | 北向资金净买额永久为空 | 2024-08-19起永久停止披露。替代方案：港股均涨跌幅代理外资偏好，`calc_foreign_capital_proxy()` 自动计算 | 永久 |
| 10 | 日经225 量级校验失败（超18000-55000） | → 切换 AkShare 备用通道；仍失败 → 阻断 | 低 |
| 11 | KOSPI 量级校验失败（超1500-4500） | → 标注"数据待核实"，不阻断 | 低 |
| 13 | actions.type 用了 bullish/bearish | → 必须用操作动词：hold/add/reduce/buy/sell/watch/hedge/stoploss | 高 |
| 14 | 来源链接跨媒体伪造 | → 付费墙(Bloomberg/FT/WSJ)：只填 source 不填 url，前端灰色不可点 | 高 |
| 15 | coreJudgments.logic 散文体 | → **强制**：短句 + `→` 三段式：`触发 → 传导 → 结论` | 高 |
| 16 | takeaway 缺少【】标红 | → 每条 3-5 个【】关键词，前端 parseTakeaway() 正则渲染红色高亮 | 高 |
| 17 | chain[].url / references 被漏填 | → 非付费墙 source 必有 url；每条 coreJudgments 必有 references | 高 |
| 20 | riskNote 散文段落 | → v3.1：升级为 `riskPoints[]` 数组(2-3条)，前端 `wx:for` 循环渲染 | 高 |
| 21 | sentimentLabel 用了非标枚举 | → 强制6枚举：极度恐惧/偏恐惧/中性/偏贪婪/贪婪/极度贪婪，按 score 区间查表 | 高 |
| 22 | marketStatus 休市日无枚举 | → v2.3：新增第5枚举 `美股休市` | 中 |
| 23 | WATCHLIST_AK_MAP 未同步新标的 | → 每次调整板块标的后必须同步 AkShare 映射表 | 高 |
| 24 | AkShare 新浪/东财源限流 | → 0.3秒 sleep 间隔 + 新浪主力东财 fallback + 失败跳过不阻断 | 中 |
| 25 | riskPoints 包含操作建议 | → **禁止**。风险模块只描述风险，操作建议统一在 actionHints | 高 |
| 26 | actionHints 每天凑操作建议 | → 大多数日子为空数组 `[]`，只在极高置信机会时填入 | 高 |
| 27 | 持仓数据凭 AI 记忆编造 | → **致命**。必须 web_search 查证权威源(13Radar/Whalewisdom)，禁止凭记忆 | 致命 |
| 28 | briefing 与 radar 持仓不一致 | → 先写 radar 详版 → 提取 briefing 简版，禁止独立生成 | 高 |
| 29 | sentimentScore 机械对齐 F&G | → 必须基于 VIX/Put-Call/信用利差等多维度独立打分，禁止简单对齐 | 中 |
| 30 | coreEvent.title 信息堆砌 | → 收紧为 20-50 字，只抓 1-2 个核心矛盾 | 中 |
| 31 | 行情数据凭 AI 记忆编造 | → **致命**。所有 price/value 必须从实时行情源查证，trafficLights 按阈值机械判定 | 致命 |
| 32 | riskAdvice 含操作建议+机械引用 F&G | → 只描述风险+催化剂，禁止操作建议和 F&G 单值引用 | 高 |
| 33 | sparkline[-1] 与 price 不一致 | → 终审逐标的比对，偏差>1% 标记异常 | 中 |

## JSON 生成堵点

| # | 堵点 | 解决方案 |
|---|------|---------|
| 1 | 必填字段数据缺失 | 核心行情 → 阻断；辅助字段(PE等) → "—" |
| 2 | sparkline 全为 0 或相同值 | 重新采集，禁止估算微调 |
| 3 | analysis 含 markdown | 去除 `**`/`|`/`>`/`- ` |
| 4 | change 类型错误(string) | `parseFloat(change)` |
| 5 | 枚举值越界 | 映射到最近合法枚举 |
| 6 | metrics 6项结构不符 | 统一方案C：最新价/单日涨跌/7日涨跌/30日涨跌/PE(TTM)/综合评级 |

## 上传堵点

| # | 堵点 | 解决方案 |
|---|------|---------|
| 1 | access_token 获取失败 | 检查 WX_APPID/WX_APPSECRET |
| 2 | 云数据库写入失败 | JSON 保留本地，可手动重传 |
| 3 | 特殊字符导致 query 解析失败 | upload_to_cloud.py 已内置清洗 |
| 4 | 部分集合上传成功/失败 | 成功生效，失败保持旧数据 |
| 5 | 上传后字段缺失/dataTime 不一致 | v1.1 `verify_upload()` 回读校验 |

## 质量退化堵点

| # | 堵点 | 降级路径 | 频率 |
|---|------|---------|------|
| 37 | topHoldings 退化(3→2家) | → R1 门禁 ≥3 硬约束 + holdings-cache.json 兜底 | 致命 |
| 38 | positions 退化(Top10→Top5) | → R2 门禁 ≥Top10 硬约束 + holdings-cache.json 兜底 | 致命 |
| 39 | 权重全写"待更新" | → 非13F窗口期引用 holdings-cache.json，禁止写"待更新" | 高 |
| 40 | 规范膨胀致 AI 注意力分散 | → R1-R8 回归门禁 + holdings-cache + diff 输出 + validate.py 自动化 + auto_compute.py 公式自动计算 | 系统性 |

## Harness Engineering 堵点

| # | 堵点 | 降级路径 | 频率 |
|---|------|---------|------|
| 41 | validate.py 被绕过(直接调 upload) | → **禁止**直接调 upload_to_cloud.py，必须通过 run_daily.sh；--skip-warn 仅跳过 WARN 级 | 系统性 |
| 42 | Heavy 产出 smartMoneyHoldings 不引用 holdings-cache.json，凭记忆写不完整数据（只有5条+"待更新"） | → **R9 [FATAL]** validate.py 自动比对 holdings-cache.json，不一致则阻断上传（不可绕过）；同时 R2(≥Top10) + R3(禁止"待更新") 也标记为 FATAL | 高频 |
| 43 | --skip-validate 成为万能逃生口，一旦有任何 FAIL 就整体跳过，连带放过致命错误 | → v2.0 FATAL/WARN 双级机制：--skip-validate 已废弃→--skip-warn；FATAL 级(R2/R3/R9)永远执行不可跳过 | 系统性 |
| 44 | smartMoneyHoldings manager/asOf 文字过长，小程序一行放不下 | → v10.0：前端 radar.js 自动去括号紧凑化 + CSS 溢出截断。**数据侧规则**：manager≤10中文字、asOf≤12中文字，括号内补充信息不影响渲染 | 高 |
| 45 | 语音播报功能在全量更新时被遗漏（audioUrl/voiceText 为空） | → **v10.6：V35 已升级为 [FATAL]**，audioUrl 为空直接阻断上传，不可 --skip-warn 绕过。必须完成第3.5阶段 TTS 生成+上传后方可发布 | 高 |
| 46 | AI 编造期权/虚构标的进入聪明钱持仓（如"AAPL PUT 2.8% 新建仓"） | → **致命**。V39 [FATAL] 自动拦截 symbol 含 PUT/CALL/OPTION 以及 name 含"期权/权证"等衍生品关键词。**根因**：AI 将 Sell PUT（卖出看跌期权，不产生多头持仓）误解为 Buy PUT（持有看跌期权多头），编造了 13F 中不存在的标的。**唯一数据源**：SEC 13F-HR 原始文件（StockZoa/13Radar/WhaleeWisdom 解析版），禁止凭社交媒体传闻或 AI 训练记忆推断持仓 | 致命 |
| 47 | 聪明钱持仓 change 字段（加仓/减持/新建仓等）凭记忆编写而非对比 Q3→Q4 13F 差异 | → 必须对比相邻两个季度的 13F 数据来判定 change。无法确认时填"持仓不变"（保守策略），禁止编造"大幅增持"等需要 Q3 基准的判断 | 高 |
| 48 | globalReaction.value 混合格式（如"6,773 (+2.37%)"），导致前端33%宽度格子溢出换行 | → V41 校验：禁止括号，≤15字符。value 只放涨跌幅（"+2.37%"）或绝对值（"$4,774"），二选一。前端 `.reaction-item` 宽度 33.33%，长字符串必然溢出 | 高 |
| 49 | watchlist metrics[2]/[3]（7日/30日涨跌）为空字符串，前端渲染为空白格子 | → V40 校验：禁止任何 metrics.value 为空字符串。auto_compute.py 从 sparkline/chartData 自动计算，无数据时填"—"（非空字符串） | 致命 |
| 50 | _meta.generatedAt 不更新：第二批及后续批次执行时，AI（尤其 GLM 模型）跳过 auto_compute.py 调用，generatedAt 保留首批写入值（如06:00），小程序显示"4小时前""10小时前"等错误时间 | → **根本修复**：run_daily.sh 在 upload_to_cloud 之前新增第1.5步，无条件用 python 内联强制覆盖全部4个JSON的 generatedAt 为当前时间。此步骤不依赖 AI 行为，100% 保证执行。auto_compute.py 同步升级 v2.2 保持一致 | 高 |
| 51 | AI 生成 JSON 时 price 写了 "--" 占位符未填实际价格，前端直接显示 "--" | → **致命**。V43 [FATAL] 拦截 price 为 "--"/"N/A"/空值。auto_compute.py v3.0 自动从 sparkline[-1] 推导填充兜底。**根因**：AI 在第二阶段查不到某些标的价格时用占位符先跳过，但后续未回填 | 致命 |
| 52 | sparkline[-1] 与 price 偏差大（有的>80%），前端走势图末尾与顶部价格矛盾 | → auto_compute.py v3.0 自动将 sparkline[-1] 对齐 price（偏差>0.5%时修正），同时修复 sparkline 尾部方向与 change 符号的矛盾 | 高 |
| 53 | chain[].url 和 coreJudgments[].references 被漏填，信源链可信度降低 | → V22/V23 校验拦截。AI 在第二阶段写 coreEvent.chain 时必须同步填 url（付费墙除外），写 coreJudgments 时必须填 references | 高 |
| 54 | **price 与 sparkline 来自不同数据源，数量级差异 2-26 倍**（智谱price=HK$42实际929，MiniMax price=HK$38实际999，AVGO/TSM/ASML/AMD等15个标的全错） | → **致命**。V45 [FATAL] 拦截 price/sparkline[-1] 差距>30%。V6 [FATAL] 拦截>5%偏差。**根因**：AI 搜到 price 和 sparkline 分别来自不同来源（每手价格/旧缓存/错误市场）。**强制规则**：price 必须等于 sparkline[-1]（误差≤5%），两者必须来自同一 web_fetch 请求 | 致命 |
| 55 | **sparkline 用 0 填充历史数据**（VIX/日经/KOSPI/黄金/BTC/ETH/DXY/CNH/布伦特/META/中国石油/中国神华共13个标的） | → **致命**。V44 [FATAL] 零容忍任何零值。V46 [FATAL] chartData 同理。**根因**：AI 搜不到历史数据时直接用 0 占位而非重试。**强制规则**：4级降级搜索重试（Google Finance→StockAnalysis→web_search→东方财富），全部失败才降级为平线填充 | 致命 |
| 56 | **7日/30日涨跌全部为空字符串**（全部32个标的metrics[2][3]=""） | → **致命**。V40 [FATAL] 拦截所有 metrics 空值。**根因**：auto_compute 从错误的 sparkline（含0）计算涨跌→返回None→前端空白。**强制规则**：sparkline 必须全部>0（V44），确保 auto_compute 能正确计算；或直接从 Google Finance 5D/1M 视图取涨跌幅直填 | 致命 |

## 小程序端兼容性堵点

| # | 堵点 | 解决方案 |
|---|------|---------|
| 1 | sparkline 缺失致 mini-chart 空白 | 前端显示空状态 |
| 2 | 板块标的为空数组 | 显示"暂无数据" |
| 3 | 红绿灯不足7项 | 按实际数组长度渲染 |
| 4 | 新增字段未适配 | 向后兼容，忽略未识别字段 |

---

## 端到端零堵点保障

1. 数据源异常 → 自动切换备选源（禁止退化到估算）
2. sparkline 缺失 → 回采重试，禁止估算
3. 板块标的不足 → 使用备选标的
4. JSON 无法生成 → `_fallback: true`，不上传该集合
5. 上传失败 → 保留本地文件
6. 上传成功 → `verify_upload()` 回读校验
7. **任何环节不停下等用户**

---

<details>
<summary>归档区（已永久解决，仅供历史参考）</summary>

| # | 堵点 | 状态 |
|---|------|------|
| 18 | refresh_verified_snapshot.py API 失败阻断全流程 | 方案A v2.0 已解决：脚本只写 sparkline/chartData |
| 19 | refresh_verified_snapshot.py 脚本边界混乱 | 方案A v2.0 已解决：攻击面从 15+ 字段降到 2 个 |
| 34 | Refresh 启动时基准 JSON 不完整 | v9.0 归档：Refresh 模式已删除，每次都全量执行 |
| 35 | Refresh 行情数据时态混乱 | v9.0 归档：Refresh 模式已删除 |
| 36 | Refresh 误修改保留字段 | v9.0 归档：Refresh 模式已删除，不再有"保留字段"概念 |

</details>

---

> v4.5 — 2026-04-13 | **Harness v10.6**：堵点 #45 更新（V35 升级为 FATAL），活跃堵点数不变 56条。
> v4.4 — 2026-04-09 | **Harness v10.5**：新增堵点 #54/#55/#56（数据源错误/sparkline零值/7日涨跌空白），活跃堵点数 48→56。
> v4.1 — 2026-04-08 | **13F 合规性防护**：新增堵点 #46(AI编造期权/虚构标的进聪明钱持仓)/#47(change字段凭记忆编写)，对应 validate.py V39 [FATAL]，活跃堵点数 40→42。
> v4.0 — 2026-04-08 | **Harness v9.0**：Refresh 堵点 #34/#35/#36 移入归档区（Refresh 模式已删除），堵点 #40 更新（新增 auto_compute.py），活跃堵点数 43→40。
> v3.6 — 2026-04-08 | 新增堵点 #42(Heavy不引用cache)/#43(skip-validate万能逃生口)，FATAL/WARN双级机制落地，堵点总数41→43。
> v3.5 — 2026-04-08 | 全文精简（去除冗余描述，保留核心信息），堵点总数不变 41条。
> v3.4 — 2026-04-08 | 新增堵点 #41（Harness Engineering 绕过风险）。
> v3.3 — 2026-04-08 | 新增堵点 #37~#40（质量退化类）。
> v3.2 — 2026-04-07 | 修正堵点总数。
> v3.1 — 2026-04-07 | 新增 #34/#35/#36（Refresh 模式）。
> v3.0 — 2026-04-06 | Fear & Greed 废弃。
