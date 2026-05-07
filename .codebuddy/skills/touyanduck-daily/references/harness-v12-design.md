# Harness Engineering v12 — 详细架构设计文档

> **版本**: DRAFT v1.0 (2026-05-07)
> **性质**: B 方案根治架构——「确定性骨架（Skeleton） + AI 文字最后一公里（Last-Mile）」
> **目标**: 将小程序自动化可用率从 ~70% 提升至 >99%，从根源消除数字字段错误

---

## 一、架构范式转换

### 当前（v11.x）— AI 全权生产

```
用户触发 → codebuddy AI → 800+ 字段（价格+汇率+指标+sparkline+全部文字）→ 校验 → 上传
                ↑
        100% 依赖 AI 不犯错
        Token 313万/次，31分钟，15%+ 错误率
```

### v12.0 — Harness 分工架构

```
用户触发
   │
   ├── [步骤A] skeleton_builder.py（~3分钟，确定性，0错误率）
   │       ↓
   │   骨架JSON（600个量化字段全部填满，精度由 AkShare/yfinance 保证）
   │       ↓
   ├── [步骤B] codebuddy AI（~15分钟，专注文字，Token 降75%）
   │       ↓
   │   AI 只填 200个文字字段（analysis/insight/reason/summary/coreJudgments 等）
   │       ↓
   ├── [步骤C] merge_skeleton.py（~10秒）
   │       ↓
   │   合并：AI文字 + 骨架数字 = 完整JSON
   │       ↓
   └── [步骤D] run_daily.sh（validate+upload，现有流程不变）
```

---

## 二、骨架数据层（skeleton_builder.py）设计

### 2.1 覆盖字段清单

| 数据类别 | JSON 文件 | 字段 | 数据源 |
|---------|---------|------|-------|
| 美股三大指数 | markets | usMarkets[].price/change/sparkline | AkShare `stock_us_index_spot_sina` |
| M7 巨头 | markets | m7[].price/change/sparkline | AkShare `stock_us_spot_em` |
| GICS 11板块 ETF | markets | sectors[].price/change/sparkline | AkShare `stock_us_spot_em` |
| 亚太指数 | markets | asiaPacific[].price/change | AkShare `stock_zh_index_spot_sina` |
| 大宗商品 | markets | commodities[].price/change | AkShare `futures_foreign_detail` |
| 汇率 CNH/DXY | markets | commodities 中 CNH/DXY | AkShare `currency_boc_sina` |
| 10Y美债 | markets/radar | commodities 中 10Y + trafficLights | AkShare `bond_zh_us_rate` |
| 黄金 XAU | markets/radar | commodities 中黄金 + trafficLights | AkShare `futures_foreign_detail` |
| VIX | markets/radar | usMarkets 中 VIX + trafficLights | AkShare `stock_vix` |
| watchlist 行情 | watchlist | stocks[].price/change/sparkline | AkShare（按 symbol 查询） |
| chartData 30天 | markets/watchlist | chartData | AkShare 历史 K 线 |
| sparkline 7天 | markets/watchlist | sparkline | AkShare 历史 K 线（取后7条）|

**注意**：以上字段由脚本确定性填入，**AI 不需要也不允许填写这些字段**。

### 2.2 骨架 JSON 格式

```json
{
  "_skeleton_meta": {
    "version": "v12.0",
    "generated_at": "2026-05-07T09:00:00+08:00",
    "source": "akshare",
    "fields_filled": 612,
    "fields_pending_ai": 201,
    "status": "ready_for_ai"
  },
  "usMarkets": [
    {
      "name": "标普500",
      "symbol": "SPX",
      "price": "5631.22",     ← 骨架填入
      "change": 1.46,          ← 骨架填入
      "sparkline": [...],      ← 骨架填入（7日）
      "analysis": "__AI_FILL__" ← AI 需填写标记
    }
  ]
}
```

AI 收到骨架后，**只处理 `__AI_FILL__` 标记的字段**，数字字段已锁定不可修改。

### 2.3 降级策略（Graceful Degradation）

```
主路径: AkShare（免费，纯Python，覆盖广）
  ↓ 失败（限流/超时/字段不存在）
备路径: yfinance（美股/ETF 补充）
  ↓ 失败
兜底路径: 使用上一次骨架数据（holdings-cache.json 类似模式）
  ↓ 失败
最终兜底: 写入空骨架（全字段 `__AI_FILL__`），降级回 v11 模式（AI 全部填写）
```

---

## 三、AI 文字层重构（SKILL.md v12 改造）

### 3.1 Phase 0 新增：读取骨架

```
Phase 0 新增子步骤：
  - 读取 skeleton_{DATE}.json（由 skeleton_builder.py 预生成）
  - 确认 _skeleton_meta.status == "ready_for_ai"
  - 打印已填字段数量（让 AI 明确知道"数字字段已锁定"）
```

### 3.2 Phase 1 大幅简化

```
v11.5 Phase 1（当前）：
  P2: Batch 1a-1d — 美股行情 web_fetch（22-27次）← 全部移除
  P3: Batch 2+3 — 亚太+大宗/汇率/加密（4-6次）← 移除汇率/大宗部分
  
v12 Phase 1（新）：
  P1: 媒体+AI产业链扫描（保留，信号层）
  P4: 基金动向（保留，持仓层）
  S1: 新闻/事件/宏观文字解读（保留）
  
  移除：所有行情数字采集（由骨架替代）
  新增：骨架数据摘要确认（AI 只读，不修改）
```

### 3.3 Phase 2 改造：只填文字字段

```
AI 在生成 JSON 时：
  - 数字字段（price/change/sparkline/chartData/trafficLights.value）
    → 从骨架直接复制，禁止修改
  - 文字字段（analysis/reason/insight/summary/coreJudgments/riskAdvice 等）
    → AI 独立生成，高质量输出
  - 公式字段（status/riskLevel/sentimentLabel）
    → auto_compute.py 计算（现有流程不变）
```

### 3.4 铁律精简（从 9 大铁律 → 3 大铁律）

v12 时代，RULE ZERO/ZERO-A/ZERO-B（禁止凭记忆填数字）已从根源消除，无需再作为铁律约束。

```
v12 保留铁律：
  RULE ONE: JSON 完整性（每个 __AI_FILL__ 字段必须填写）
  RULE FIVE: 板块均衡
  RULE EIGHT: 聪明钱持仓 13F 唯一数据源
  
v12 废弃铁律（架构层面已消除，保留注释说明）：
  RULE ZERO/ZERO-A/ZERO-B: 骨架已锁定数字，AI 无法填写错误数字
  RULE FOUR: sparkline 由脚本填入，AI 禁止碰
  RULE SIX: watchlist 行情由骨架填入，无捏造空间
```

---

## 四、merge_skeleton.py 设计

### 职责

将 AI 产出的「文字JSON」与骨架数据合并：
- 文字字段：来自 AI 输出
- 数字字段：强制使用骨架数据（即使 AI 意外填了数字也被覆盖）
- 公式字段：auto_compute.py 计算

### 合并规则（伪代码）

```python
def merge(ai_json: dict, skeleton_json: dict) -> dict:
    """
    数字字段强制使用骨架，文字字段使用AI输出
    """
    NUMERIC_FIELDS = {"price", "change", "sparkline", "chartData", "value"}  # trafficLights.value
    
    merged = deep_copy(ai_json)
    
    # 递归遍历骨架中的所有字段
    for path, skeleton_val in flatten(skeleton_json):
        field_name = path.split(".")[-1]
        if field_name in NUMERIC_FIELDS:
            # 强制用骨架数字覆盖AI可能填的值
            set_nested(merged, path, skeleton_val)
    
    return merged
```

### 校验新增：骨架覆盖审计

```python
# 在 validate.py 新增 V_SKELETON 校验（FATAL级）
# 检查最终JSON中的数字字段是否与骨架完全一致
# 若不一致，说明 merge 步骤失败，必须修复
```

---

## 五、实施路线图

### Phase A（P0，已完成 2026-05-07）

- [x] validate.py V36 升级为 FATAL
- [x] cross_check_map 名称失配修复
- [x] app-sync.sh 移除盲跳 --skip-warn
- [x] `.needs-attention` 静默标记机制
- [x] 5/7 radar.json 数据修复+重新上传

### Phase B（本周，目标 2026-05-09 前）

- [ ] `skeleton_builder.py` — 核心骨架生成脚本
  - AkShare 接口调研+适配（美股/亚太/大宗/汇率/10Y债）
  - watchlist 标的行情批量拉取
  - 骨架JSON生成+降级策略
  - 耗时目标：< 3 分钟
- [ ] `merge_skeleton.py` — 骨架合并脚本
- [ ] `run_daily.sh` 新增 Phase 0（骨架生成）+ Phase 2.5（合并）
- [ ] SKILL.md v12 改造（精简 Phase 1 采集，AI 只填文字）
- [ ] validate.py 新增 V_SKELETON 骨架一致性校验

### Phase C（灰度验证，2026-05-09 至 2026-05-14）

- [ ] 3-5 个交易日并行对比运行：骨架数字 vs AI 数字（取骨架，AI 仅供参考）
- [ ] 记录 Token 消耗变化（预期降低 ~75%）
- [ ] 验证数字字段零错误率
- [ ] 确认 AI 文字质量不降（文字字段 Token 实际上更充裕了）

### Phase D（上线，2026-05-14 后）

- [ ] SKILL.md v12.0 正式版（移除所有已废弃铁律）
- [ ] 更新 README.md + 架构图

---

## 六、预期效果对比

| 维度 | v11.5（当前） | v12.0（目标） |
|------|-------------|-------------|
| **数字字段错误率** | ~5%（CNH/10Y/DXY 等常见错误） | **0%**（AkShare 直采，确定性） |
| **Token 消耗** | ~313万/次（31分钟） | **~80万/次**（AI只处理文字）|
| **AI 任务复杂度** | 800字段+17FATAL+9RULE | **200文字字段+3保留铁律** |
| **Phase 3 被截断率** | ~30% | **<1%**（Token 充裕，不会截断） |
| **跨文件数据矛盾** | 频发（radar vs markets） | **物理消除**（同一骨架源） |
| **月度自动化可用率** | ~70% | **>99%** |
| **调试难度** | 高（AI黑箱，每次错法不同） | **低**（数字有确定源头，文字是可读文本）|
| **SKILL.md 复杂度** | 16个references + 铁律9条 | **7个references + 铁律3条** |

---

## 七、关键风险与缓解

| 风险 | 概率 | 缓解方案 |
|------|------|---------|
| AkShare 限流/宕机 | 中 | 三级降级：AkShare → yfinance → 上次骨架 |
| 骨架字段覆盖不全 | 低 | V_SKELETON FATAL 校验 + 灰度期并行对比 |
| AI 文字质量下降 | 极低 | 实际上文字 Token 更充裕，质量会提升 |
| 股票代号失配 | 低 | symbol 映射表维护（参考 data-source-priority.md）|
| 港股/A股行情覆盖 | 中 | AkShare 港股/A股接口质量足够，但需适配字段 |

---

## 八、文件变更清单

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `scripts/skeleton_builder.py` | **新建** | 骨架生成器（核心新增） |
| `scripts/merge_skeleton.py` | **新建** | 骨架合并器 |
| `scripts/run_daily.sh` | **改造** | 新增 Phase 0（骨架生成）和 Phase 2.5（合并） |
| `scripts/validate.py` | **改造** | 新增 V_SKELETON 校验 |
| `SKILL.md` | **改造** | Phase 1 精简，Phase 2 文字专注，铁律精简 |
| `references/data-collection-sop.md` | **改造** | Phase 1 移除行情采集部分 |
| `references/inline-verifier-rules.md` | **改造** | 骨架字段不再需要 AI 内联校验 |

---

*此文档为 B 方案设计草稿，实施前需确认 AkShare 接口可用性和字段覆盖度。*
*Phase B 开始前，请先执行 `python3 -c "import akshare as ak; print(ak.__version__)"` 确认依赖可用。*
