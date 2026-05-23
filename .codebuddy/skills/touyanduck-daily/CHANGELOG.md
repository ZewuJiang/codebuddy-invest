# 投研鸭小程序数据生产 — 完整版本历史

> **用途**：归档 SKILL.md 的完整变更历史。SKILL.md 主控只保留当前版本号，历史版本在此查阅。

---

## v14.0（2026-05-23）— 数据分发通道迁移：微信云开发 → 自建服务器

**背景**：微信云开发环境 `cloud1-3g6wj06h84f38ea8` 到期，小程序数据全部无法显示，迁移至自建腾讯云轻量服务器。

**变更内容**：

1. **`run_daily.sh` v6.5→v6.6**：
   - 第2步由 `python3 upload_to_cloud.py` 改为 `bash upload_to_server.sh`
   - 原 `upload_to_cloud.py` 保留文件但不再调用

2. **新增 `upload_to_server.sh` v1.0**：
   - 通过 scp 将 4 个 JSON 上传到腾讯云轻量服务器
   - 服务器：`root@119.91.74.175:/www/wwwroot/miniapp.touyanduck.com/api/`
   - 上传后自动通过 HTTPS 验证 4 个接口返回 HTTP 200
   - SSH 密钥：`~/.ssh/touyanduck_server`

3. **小程序代码 v5.0→v6.0**（`touyanduck_appid/`）：
   - `app.js`：移除 `wx.cloud.init`，新增 `apiBaseUrl: https://miniapp.touyanduck.com/api`
   - `services/api.js` v7.0→v8.0：`wx.cloud.database()` 全面替换为 `wx.request()` HTTP 请求
   - `app.json`：移除 `"cloud": true`

4. **服务器配置**（腾讯云轻量 `lhins-1x1cx0o1`）：
   - 域名：`miniapp.touyanduck.com`（DNS A记录 → 119.91.74.175）
   - Nginx 静态托管，数据目录：`/www/wwwroot/miniapp.touyanduck.com/api/`
   - Let's Encrypt SSL 证书（到期 2026-08-21，自动续签）
   - 微信公众平台 request 合法域名：`https://miniapp.touyanduck.com`

---

## v13.1（2026-05-08）— 全链路稳定性修复

**背景**：5/6-5/8 连续多日 WARN 阻断上传，小程序数据停更，触发全面排查。

**变更内容**：

1. **`validate.py` v6.1→v6.2**：
   - V5 升级为 FATAL：markets.commodities/usMarkets/m7/gics 为空数组时不可绕过
   - 防止 AI 漏写大宗商品后被 --skip-warn 跳过直接上传空数据

2. **`golden-baseline.json`**：
   - 修复 R7_dyp_weight_pattern：`\d+\.\d%` → `\d+\.\d+%`（支持多位小数，如50.30%）
   - 旧正则永远匹配不到实际格式，导致 R7 每次都误报 WARN

3. **`upload_to_cloud.py` v1.3 多处修复**：
   - 修复 `main()` IndentationError（516-519行缩进错误，导致上传必崩）
   - VERIFY_FIELDS["radar"] 移除 `alerts`（空数组 `[]` 被误判为"字段缺失"）
   - 删除残留音频函数 `upload_audio_to_cloud` + `get_audio_temp_url`（v13.0 应清理）

4. **`~/.local/bin/app-sync.sh` v2.1**：
   - WARN 处理策略改为：FATAL=0 时自动 --skip-warn 重试上传（旧策略：直接 FAIL，小程序拿不到数据）
   - 新增状态 `SUCCESS_SKIP_WARN`（有WARN但已上传）

5. **`~/Library/LaunchAgents/com.codebuddy.appsync.plist`**：
   - 清理残留 MINIMAX_API_KEY 环境变量（语音功能已永久移除）

6. **`SKILL.md` v13.1**：
   - Phase 1.5 数据完整性门禁强化 commodities 6项说明（5/8事故教训）
   - Phase 3 validate.py 描述更新为 v6.2
   - inline-verifier-rules.md 描述更新为 v1.2

7. **`references/inline-verifier-rules.md` v1.2**：
   - 移除 V35，新增 V36/V48/V49，统计更新（15可内联/4不可内联）

**涉及文件**：validate.py, golden-baseline.json, upload_to_cloud.py, app-sync.sh(~/.local), com.codebuddy.appsync.plist, SKILL.md, inline-verifier-rules.md, README.md

---

## v13.0（2026-05-07）— 语音功能永久移除 + 规范瘦身

**变更内容**：

1. **语音功能永久移除**：
   - 物理删除 `scripts/generate_audio.py`（MiniMax TTS 语音生成器）
   - `scripts/upload_to_cloud.py` v1.2→v1.3：删除 `upload_audio_to_cloud()` / `get_audio_temp_url()` / 音频检测逻辑（约150行）
   - `scripts/validate.py` v6.0→v6.1：删除 `validate_audio_url()` 函数及主流程调用（V35），FATAL 项 20→19，校验项 58→57
   - `scripts/requirements.txt`：注释更新，移除 MiniMax TTS 说明
   - 前端 `briefing.js` v7.1→v7.2：删除 `audioUrl/isPlaying/audioLoading` 三个 data 字段、`_audioCtx` 实例变量、`onVoiceTap/_playAudio/_destroyAudio` 三个方法（约80行）
   - 前端 `briefing.wxml` v7.1→v7.2：删除语音播报按钮整块（ts-voice-btn）
   - 前端 `briefing.wxss`：删除语音播报按钮 CSS（约60行）

2. **规范瘦身（SKILL.md 503行→~280行）**：
   - v11.0-v12.2 全部 Changelog 迁至 CHANGELOG.md，SKILL.md 只保留版本号标题
   - Checklist（J1-J10/P1-P5/V1-V4/故障排查）迁至 `references/daily-checklist.md`
   - Phase 3.5（语音播报）整节删除
   - Generator-Verifier 中 V35 引用注释清除

3. **冗余清理**：
   - `🚨🚨🚨` 三重强调 → 单 `🚨`
   - "每次执行都是全量高质量产出，确保数据一致性" → 删除
   - References 分层加载警告措辞精简
   - 版本历史尾部冗余说明删除

**涉及文件（12个）**：SKILL.md, README.md, CHANGELOG.md, validate.py, upload_to_cloud.py, requirements.txt, daily-checklist.md(新建), briefing.js, briefing.wxml, briefing.wxss，generate_audio.py(删除)

---

## v12.2（2026-05-07）— Phase B1.5 锚点鲁棒性补强 + 上传一致性门禁

**anchor_fetcher.py v1.1**（实测 3/6 → 目标 6/6）
- CNH 备源补充：Frankfurter API + open.er-api.com 三级降级链
- DXY 备源补充：FRED DTWEXBGS，标记 `skip_v48=True` 避免量级误比对
- VIX 备源升级：CBOE 官方 JSON 提升为主源，yfinance 降为备源
- yfinance 重试机制：429 错误 sleep 3s 重试 1 次
- fetched_at 时效字段：anchors.json `_meta.fetched_at` 供 V48 时效性校验（超 12h 整体 SKIP）

**validate.py v6.0**（58项，20 FATAL）
- V48 增强：读取 `fetched_at` 做时效性校验；跳过 `skip_v48=True` 条目
- 新增 V49 [FATAL]：本地文件 hash vs `.last_upload_hash.json` 一致性校验（堵死堵点 #65）

**run_daily.sh v6.5**
- 第2步上传成功后新增第2.5步：写入 `.last_upload_hash.json`（4文件 sha256 + uploaded_at 时间戳）

---

## v12.1（2026-05-07）— 真值锚点防线 Phase B1

- **⚓ 新增 `anchor_fetcher.py` v1.0**：独立真值锚点拉取器，覆盖 AkShare 缺口 6 字段（10Y美债/CNH/DXY/VIX/BTC/ETH），三级降级，输出 `miniapp_sync/anchors.json`
- **🛡️ validate.py v5.9 — V48 [FATAL]**：AI 抓取值 vs 锚点容差校验（CNH:1.5% / DXY:1.5% / 10Y债:3% / VIX:15% / BTC/ETH:10%）
- **🔧 run_daily.sh v6.4**：新增第0.4步（anchor_fetcher.py）
- **📋 requirements.txt**：新增 `yfinance>=0.2.40`
- **5/7 事故验证**：CNH=7.22 vs 6.81 偏差 6.0% >> 1.5% → FATAL 阻断永不上传

---

## v12.0（2026-05-07）— 紧急止血 P0 门禁加固

- **🚑 5/7 数据修复**：radar.json 三个红绿灯值（CNH 7.22→6.81、10Y 3.97%→4.35%、DXY 97.83→98.02）修复并重新上传
- **V36 WARN→FATAL**：跨JSON一致性矛盾不可被 `--skip-warn` 绕过
- **cross_check_map 2处名称失配Bug修复**：VIX/黄金两项长期静默跳过，现已对齐真实生效
- **app-sync.sh v2.1**：移除盲跳 `--skip-warn` 逻辑，WARN 失败改为写入 `.needs-attention` 标记

---

## v11.5（2026-05-06）— Phase 3 自我守卫约束

- **根因**：5/4-5/5 连续 6 次 AI 被 token 截断，从未执行 Phase 3，数据未上传
- Phase 3 新增自我守卫强制约束块
- `app-sync.sh` 重写为 v2 双阶段守卫架构
- 删除 app-sync.sh 中"只刷 generatedAt"的虚假兜底
- 健康日志改为 4 种真实状态（SUCCESS_FULL / FAIL_AI_INCOMPLETE / FAIL_VALIDATE / FAIL_SCRIPT_MISSING）

---

## v11.4（2026-05-03）— 彻底移除公开API同步模块

- run_daily.sh v6.3：删除第3步（sync_to_edgeone.sh），微信云数据库为唯一终点
- 物理删除脚本：sync_to_edgeone.sh / render_briefing.py / generate_summary.py / generate_meta.py
- touyanduck-api/ 目录整体删除

---

## v11.3（2026-04-21 21:40）— 全面细节审查（13处精准修复）

**优化内容**：

1. **Phase 0 废弃物清理**：
   - 删除 `refresh-mode.md`（v9.0 已废弃 Refresh 模式，该 392 行文件为纯噪音，AI 可能误读激活废弃逻辑）

2. **Phase 1 全量版本对齐**：
   - README.md 版本 v11.0→v11.1；脚本版本号全面对齐（run_daily.sh v6.2, validate.py v5.7, data-collection-sop v3.1, known-pitfalls v5.5）
   - SKILL.md 引用索引 known-pitfalls 描述从"60条"更新为"65条 v5.4"
   - CHANGELOG.md v11.0 条目补全标题行（原文缺少版本号标题）

3. **Phase 2 减噪瘦身**：
   - SKILL.md v11.0 Changelog 从 ~8 行精简为 2 行摘要（节省 ~400 token）
   - json-schema.md 底部版本日志从 8 条裁剪为 3 条（节省 ~500 token）
   - fund-universe.md 底部版本日志从 5 条裁剪为 3 条（节省 ~800 token）
   - data-collection-sop.md 底部版本日志裁剪
   - known-pitfalls.md 底部版本日志从 14 条裁剪为 4 条（节省 ~600 token）
   - known-pitfalls.md #64（P0路径Bug）已被 v6.1 永久修复，移入归档区

4. **Phase 3 质量信号优化**：
   - SKILL.md 规范健康度快照新增 `known-pitfalls.md` 版本行
   - 堵点计数更精确：64条活跃 + 6条归档

**版本号变更**：known-pitfalls.md v5.4→v5.5

**总体效果**：
- 清除 ~2300 token 噪音（refresh-mode 392行 + Changelog/版本日志裁剪）
- 消除 1 个 P0 级误导风险（废弃的 Refresh 模式规范文件）
- 修复 ~15 处版本/描述不对齐
- 提升 AI 的"有效注意力比"——references 每一个文件都是活跃的、每一行都是有用的

---

## v11.1（2026-04-21 12:30）— 数据链路 P0 Bug 修复 + 前端 asOf 显示修正

**根因**：2026-04-21 排查发现小程序前端数据不更新，追溯到两处系统性缺陷。

**修复内容**：

1. **run_daily.sh v6.0→v6.1（P0 路径 Bug 修复）**
   - 新增「第-1步」：在 JSON 语法校验前，自动将 `miniapp_sync/YYYY-MM-DD/*.json` 复制到 `miniapp_sync/*.json` 根目录
   - 根因：AI（v11.0）将 JSON 写入日期子目录，工具链（upload/validate/sync）全链路读根目录旧文件，导致微信云数据库和 GitHub Pages 始终用旧数据，小程序前端永远不更新
   - 堵点 #64 已固化到 known-pitfalls.md v5.3

2. **radar.js asOf 括号清理加强（v7.0→v7.1）**
   - 原正则两条独立替换（`/（[^）]+）/` + `/\([^)]+\)/`）遇到嵌套或中英混用括号时失效
   - 新正则：`/[（(][^）)]*[）)]/g` 一次性处理中英文括号，输出纯净 `YYYY-MM-DD` 或 `YYYYQN·月份`

3. **data-collection-sop.md v3.0→v3.1（JSON 双引号防治）**
   - 新增 §0.10：JSON 字符串内禁止直接使用英文双引号，必须用 `\"` 转义或改用中文弯引号 `""`
   - 根因：`"right business"` 和 `"保险公司正式开张"` 在 briefing.json/radar.json 中用了未转义 ASCII `"`，导致 JSON 语法错误，run_daily.sh 第0步本应拦截但读的是旧根目录文件（#64 Bug 导致）

4. **ARK 持仓 asOf 每日更新规则强化**
   - holdings-cache.json 注记：ARK 每日披露，不适用「非窗口期引用缓存」规则，每次必须更新 asOf 为当日日期
   - 已在 known-pitfalls.md #63 堵点描述中强化

**涉及文件**：
- `scripts/run_daily.sh`：v6.0→v6.1
- `touyanduck_appid/pages/radar/radar.js`：v7.0→v7.1
- `references/data-collection-sop.md`：v3.0→v3.1
- `references/known-pitfalls.md`：v5.2→v5.3（+#64）
- `SKILL.md`：规范健康度快照更新

---

## v11.0（2026-04-20 20:00）— Phase 1 并行采集 + Context 压缩 + References 分层加载 + Generator-Verifier 内联自校验

**原则**：Phase 1 采集效率倍增 + AI 上下文负担大幅减轻 + Phase 2 前置拦截 FATAL 错误。工具链零改动。

**四大核心改造**：

1. **Phase 1 并行采集**（data-collection-sop.md v2.1→v3.0）：
   - 10个串行批次改为4组并行（P1媒体/P2行情/P3亚太大宗/P4基金）+ 1组串行（S1依赖P2）
   - 新增§0.8 并行采集分组规范（分组定义+同步屏障+失败处理）
   - 采集时间预期减少 60-70%

2. **Context 压缩铁律**（data-collection-sop.md §0.9）：
   - 为11个采集批次定义精确的最小字段集提取规范
   - web_fetch/web_search 后必须立即提取结构化字段，丢弃原始 HTML/snippet
   - Phase 1 上下文从 ~76k 压缩至 ~35k，腾出 ~40k 余量

3. **References 分层加载**（SKILL.md 新增章节）：
   - L1 Phase 0：schema-compact + formulas + golden-baseline
   - L2 Phase 1 前：data-collection-sop + data-source-priority + 各组知识库
   - L3 Phase 2 前：json-schema + stock-universe + holdings-cache + inline-verifier-rules
   - L4 Phase 4：templates + known-pitfalls

4. **Generator-Verifier 内联自校验**（新建 inline-verifier-rules.md v1.0）：
   - Phase 2 每个JSON写完后立即执行内联校验
   - 从validate.py 17项FATAL提取14项可内联检测+关键WARN
   - 最多2次修复重试，避免Phase 3 FATAL后整体重来
   - 3项不可内联（R9/V35/V_TL）由Phase 3脚本终裁

**涉及文件**：
- SKILL.md：v10.6→v11.0（重写工作流+新增3大机制章节+引用索引分层化）
- references/data-collection-sop.md：v2.1→v3.0（+§0.8并行分组+§0.9最小字段集）
- references/inline-verifier-rules.md：**新建** v1.0（内联自校验规则）
- references/known-pitfalls.md：v4.5→v5.0（+#57-#60并行堵点，活跃56→60）
- CHANGELOG.md：新增v11.0变更记录
- README.md：v9.0→v11.0

**向后兼容声明**：
- 工具链零改动（validate.py/auto_compute.py/run_daily.sh/upload_to_cloud.py等全部不变）
- JSON Schema零改动（json-schema.md/golden-baseline.json/templates/不变）
- 知识库零改动（stock-universe/fund-universe/ai-supply-chain-universe/media-watchlist/holdings-cache不变）
- 九大铁律（RULE ZERO ~ RULE EIGHT）全部保持
- 54项校验/17项FATAL全部保持
- 4个JSON产出物格式完全兼容

---

## v10.6（2026-04-13 11:05）— Harness v10.6 FATAL 项全面升级

**原则**：目标每次全部通过，零 WARN。前端渲染安全与核心功能完整性纳入 FATAL 门禁。

**validate.py v5.5→v5.6**：
- V35  **WARN→FATAL**：audioUrl 为空 = 语音播报失效，不可绕过
- V38  **WARN→FATAL**：sparkline 趋势与 change 方向矛盾 = 数据错误
- V41  **WARN→FATAL**：globalReaction value 超长/含括号 = 前端布局溢出
- V42  **WARN→FATAL**：generatedAt 为空 = 前端时间显示异常
- V24  **WARN→FATAL**：Markdown 残留 = 前端乱码
- R1   **WARN→FATAL**：topHoldings < 3 = 聪明钱核心展示不完整
- V_TL **WARN→FATAL**：红绿灯 value↔status 不一致 = 前端颜色错误
- **FATAL 项**：10 → **17 个**
- **校验项**：54 项（不变）

**SKILL.md**：
- 第3.5阶段语音播报标注升级为 🔴 FATAL 级强制
- 质量宪章 WARN 上限从 ≤3 → 目标 0 WARN（≤1 可接受）

---

## v10.5（2026-04-09 22:19）— Harness v10.5 门槛全面收紧

**原则**：数据准确性 > 执行速度。宁可多搜几轮花多几分钟，也不能让错误数据发布。

**validate.py v5.4→v5.5**：
- V6  **WARN→FATAL** 升级：sparkline[-1] vs price 偏差容差从 1%→5%（FATAL 级，形成 V6/V45 双层防护）
- V40 **WARN→FATAL** 升级：metrics 空值 = 前端空白 = 阻断发布
- V44 **阈值收紧**：从 >50% 零值 → **任何零值（>=1个）即 FATAL**
- V45 **阈值收紧**：price vs sparkline[-1] 差距从 50%→**30%**
- 新增 **V46 [FATAL]** chartData 禁止零值（与 V44 平行，覆盖30日数据）
- 新增 **V47 [WARN]** sparkline 禁止全平线（拦截估算填充）
- **FATAL 项**：从 5 → **10 个**（V6/V39/V40/V43/V44/V45/V46/R2/R3/R9）
- **校验项**：52 → **54 项**

**data-collection-sop.md v2.0→v2.1**：
- 新增 §0.7 质量门禁与重试机制（4道门禁 + 4级搜索重试 SOP + 10项FATAL清单表格）

---

## v10.4（2026-04-09 21:53）— Harness v10.4 结构性数据防护

**根因**：2026-04-09 发现两类系统性结构错误：
1. AI 对新上市/无历史数据标的（VIX/日经/KOSPI/黄金/BTC/ETH/CNH/DXY等）直接用 `0` 填充 sparkline → 图表断崖+7日涨跌空白
2. AI 填写 price 时使用错误来源（智谱 HK$42.80 实为 HK$929，MiniMax HK$38.50 实为 HK$999，AVGO $179.83 实为 $353.81 等 13 个标的错误）— **价格与 sparkline 数量级不一致**

**修复**：
- **数据修复**：watchlist.json 修正 13 个标的 price + 全部 32 个标的补全 7日/30日涨跌；markets.json 修复 VIX/META/日经/KOSPI/黄金/布伦特/DXY/10Y美债/CNH/BTC/ETH 共 11 个 sparkline
- validate.py **v5.3→v5.4**：
  - 新增 V44 [FATAL] sparkline 禁止大量0值（>50%为0 → FATAL，拦截AI零值填充历史数据）
  - 新增 V45 [FATAL] price 与 sparkline[-1] 数量级一致性（差距>50% → FATAL，拦截数据来源不一致）
  - FATAL_CODES 新增 V44/V45
  - 校验项 50→52 项

**结构性教训**：
- 直接能取的数不应让 AI 计算（5D/1M 涨跌 Google Finance 直接有）
- sparkline 一律从历史行情搜索，禁止 AI 手写估算值
- price 与 sparkline 必须来自同一数据源

---

## v10.0（2026-04-08 17:30）— Harness v10.0 工具链全面升级
- **核心理念**：AI 只做搜索+写分析，其余全部由工具链接管
- auto_compute.py v1.0→v2.0：新增6类自动计算（metrics[2-5]+gics排序+dataTime+sourceType修正），总计12类
- validate.py v3.0→v4.0：新增 V30-V34 内容质量检测层 + Insight 上限扩展 + V7 修复 + riskAlerts 废弃
- 新增 checklist_generator.py v1.0：执行前自动清单
- 新增 post_flight.py v1.0：执行后自动报告
- 新增 schema-compact.json v1.0：AI 紧凑 Schema 参照
- golden-baseline.json v1.1→v1.2：sourceType 精简 + 内容质量参数 + Insight 上限100
- 校验结果：36项→41项，WARN 6→3

## v9.0（2026-04-08 17:00）— Harness v9.0 架构级重构
- **🏗️ 从"越做越厚"到"结构性简洁"**：
  - 删除 Refresh 模式：四档→二档引擎（Standard + Weekend），消除 413行 refresh-mode.md + 模式路由决策树 + 字段边界表
  - 新增 `auto_compute.py` v1.0：自动计算 riskScore/riskLevel/sentimentLabel/trafficLights.status/metrics联动，AI 不再手算公式
  - validate.py v2.0→v3.0：去掉 refresh 分支，heavy 映射 standard，统一校验
  - run_daily.sh v5.0→v6.0：新增第0.3步 auto_compute，模式检测简化
  - data-collection-sop.md v1.9→v2.0：删除第九章 Refresh 精简采集批次
  - known-pitfalls.md v3.6→v4.0：Refresh 堵点归档，活跃堵点 43→40
  - json-schema.md v4.6→v5.0：清理 refresh_update 枚举引用
  - templates.md v1.0→v1.1：删除 Refresh 复盘模板
  - golden-baseline.json v1.0→v1.1：sourceType 枚举清理
  - weekend-mode.md v4.0→v4.1：术语 Heavy→Standard
  - 规范总行数减少约 660行（-15%），AI 认知负荷显著降低

## v8.2（2026-04-08 13:15）
- validate.py v1.1→v2.0：FATAL/WARN 双级机制——R2/R3/R9 为 FATAL 级
- 新增 R9 校验：自动比对 radar.smartMoneyHoldings 与 holdings-cache.json
- run_daily.sh v4.0→v5.0：--skip-validate 废弃→--skip-warn
- known-pitfalls.md v3.5→v3.6：新增堵点 #42/#43

## v8.1（2026-04-08 11:30）
- validate.py v1.0→v1.1：新增 V27(Insight长度) + V28(metrics数量) + V29(logic箭头格式)
- run_daily.sh v3.0→v4.0：版本号更新
- known-pitfalls.md v3.4→v3.5：全文精简

## v8.0（2026-04-08 10:30）
- 🏗️ Harness Engineering 架构升级（系统性治理规范膨胀）
- 新增 validate.py v1.0（30+项自动化校验）
- 新增 golden-baseline.json v1.0
- 新增 formulas.md v1.0、templates.md v1.0、CHANGELOG.md
- SKILL.md 从 972行→≤300行瘦身

## v7.5（2026-04-08 09:28）
- 质量守护体系三层防护：R1-R8回归门禁+holdings-cache.json+diff输出
- known-pitfalls.md v3.2→v3.3：新增堵点 #37~#40
- json-schema.md v4.5→v4.6：topHoldings/smartMoneyHoldings 硬约束强化
- GitHub Pages 作为唯一公网端点

## v7.3（2026-04-07 20:40）
- 新增第4.3阶段：公开API同步

## v7.2（2026-04-07 18:30）
- 工程化改造（对标 Iran Briefing skill）
- sync_to_edgeone.sh v1.0→v3.0
- refreshInterval 统一修正
- json-schema.md v4.2→v4.5

## v7.1（2026-04-07 13:00）
- P0 残留 Bug 修复（3处）
- refresh-mode.md v1.0→v1.1
- data-collection-sop.md R1 批次明确化

## v7.0（2026-04-07 12:00）
- 新增 Refresh 模式（每4小时增量刷新）
- 三档升级为四档引擎
- 新建 refresh-mode.md v1.0
- known-pitfalls.md v3.0→v3.1

## v6.1（2026-04-06 19:20）
- 播报文本生成器全面重构 v1.0→v3.0

## v6.0（2026-04-06 17:59）
- 新增语音播报功能（MiniMax TTS）

## v5.9（2026-04-06 15:30）
- 小程序前端 + Skill 联动工程优化

## v5.7（2026-04-06 14:07）
- 简报页+标的页质量基线门禁固化
- 黄金样本固化
- 执行质量五项加固

## v5.6 及更早版本
v5.1 持仓数据铁律 → v5.0 简报页架构优化 → v4.8 聪明钱搜索深度 → v4.6 Batch 4 分层修复 → v4.5 雷达页升级 → v4.4 雷达页重构 → v4.3 AkShare 替代 yfinance → v4.2 watchlist 5板块 → v4.0 三档引擎 → v3.x 数据治理 → v2.x 架构演进 → v1.0 初始版本

详见 git log。
