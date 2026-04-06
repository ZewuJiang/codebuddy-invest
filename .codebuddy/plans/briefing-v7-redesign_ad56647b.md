---
name: briefing-v7-redesign
overview: 将简报页从v6.0的10模块平铺架构，重构为v7.0的三段式5模块精简架构，核心目标是"少而精的决策信号"，提升大老板的阅读效率和决策闭环体验。
todos:
  - id: merge-event-card
    content: 合并简报页模块②：将 takeaway-card 和 event-card 合并为单一 combined-event-card，删除 coreEvent.title 渲染，修改 briefing.wxml 和 briefing.wxss
    status: completed
  - id: merge-action-smart
    content: 提权合并模块④：将聪明钱动向移入行动建议卡片内，调整 wxml 模块顺序为 event→reaction→action+smart→risk+sentiment→judgment，更新 animation-delay 编排
    status: completed
    dependencies:
      - merge-event-card
  - id: merge-risk-sentiment
    content: 合并模块⑤：删除独立市场情绪和风险提示模块，新建 risk-sentiment-card，情绪条在上+riskPoints在下，删除 marketSummaryPoints 渲染，新增对应 wxss 样式
    status: completed
    dependencies:
      - merge-action-smart
  - id: collapse-judgment
    content: 降权模块⑥：核心判断 section-card 改为 expanded=false 默认折叠，清理 briefing.js 中 marketSummaryPoints 映射的无用引用，整体代码收尾检查
    status: completed
    dependencies:
      - merge-risk-sentiment
---

## 用户需求

### 产品概述

将简报页从当前 v6.0（10个模块，信息堆砌）重构为 v7.0（7个渲染单元，三段式精简架构），核心原则：**少而精的决策信号**，大老板2-3屏内获取全部关键信息。

### 核心功能变更

**模块合并与重排（10 → 7 个渲染单元）**

| 新序号 | 新模块 | 变化说明 |
| --- | --- | --- |
| 1 | 时间状态栏 | 保留不变 |
| 2 | 今日结论 + 重点事件（合并） | takeaway 作顶部红色高亮一句话；chain 列表跟随其下；删除 coreEvent.title 渲染（与 takeaway 重复） |
| 3 | 全球资产反应 | 保留不变，6格数字卡片 |
| 4 | 行动建议 + 聪明钱（合并，提权） | 聪明钱从第8位提至第3位；今日/本周行动在上，聪明钱列表在下，底部保留"查看更多"跳转雷达页 |
| 5 | 风险与情绪（合并，精简） | 情绪条+分数在上；riskPoints 精选2-3条在下；删除 marketSummaryPoints 5条 bullet 渲染 |
| 6 | 核心判断（降权，默认折叠） | 从第5位降至第6位；collapsible=true，expanded=false（默认收起） |
| 7 | 数据更新时间 | 保留不变 |


**删除渲染内容（JSON字段保留，前端忽略）**

- `coreEvent.title` 不再渲染
- `marketSummaryPoints` 不再渲染

**视觉效果目标**

- 大老板打开即见：今日结论一句话（红色高亮关键词） + 事件链
- 第2屏：6格资产数字
- 第3屏：行动建议（可操作指令）+ 聪明钱动向（佐证）
- 第4屏：风险情绪（一句话底线）+ 核心判断（折叠，按需展开）

## 技术栈

微信小程序原生框架（WXML + WXSS + JS），复用现有 section-card 组件，不引入新依赖。

## 实现方案

**纯前端重组，零 JSON Schema 破坏性变更**：所有改动限于 briefing.wxml / briefing.wxss / briefing.js 三文件。JSON 数据字段全部保留（向后兼容），仅改变前端渲染逻辑（忽略 coreEvent.title 和 marketSummaryPoints）。

### 关键技术决策

**1. 模块②：takeaway + coreEvent 合并为单卡片**

- wxml：将原 takeaway-card 和 event-card 合并为一个 `combined-event-card`
- 卡片顶部保留 takeaway 富文本（【】红色标红），紧跟分割线，chain 列表在下
- `coreEvent.title` 对应的 `event-title` div 直接删除（不渲染，不影响 JS 数据映射）
- JS `_applyData` 无需改动（coreEvent.title 字段继续存在于数据对象，只是不渲染）

**2. 模块④：行动建议 + 聪明钱合并**

- wxml：删除原独立的聪明钱 section-card，在行动建议 section-card 内部追加聪明钱列表
- 新增内部分隔标题行"🧠 聪明钱佐证"，视觉区分两个子区块
- 底部"查看更多聪明钱动向 ›"跳转雷达页逻辑保留（onSmartMoneyTap）
- JS 无需改动（smartMoney 数组数据映射逻辑不变）

**3. 模块⑤：风险与情绪合并**

- wxml：删除原独立的市场情绪 section-card 和风险提示 section-card
- 新建 `risk-sentiment-card` section-card，内部布局：情绪条行（情绪条 + 分数 + 标签） + 风险点列表（riskPoints，保留 2-3 条渲染逻辑）
- `marketSummaryPoints` 列表彻底不渲染（wxml 中删除对应 wx:for 循环）
- JS 中 `marketSummaryPoints` 数据映射逻辑保留（不产生 lint 错误，字段依然存在），只是模板不使用

**4. 模块⑥：核心判断默认折叠**

- wxml：将 `section-card` 的 `expanded="{{true}}"` 改为 `expanded="{{false}}"`
- 无其他改动，现有手风琴参考源逻辑全部保留

**5. 模块顺序调整**

- wxml 中调整各模块物理顺序：combined-event-card → reaction-card → action+smartmoney section-card → risk-sentiment section-card → judgment section-card → data-footer

### 性能说明

- 模块数量从10减为7，setData 负载降低，渲染树节点减少约30%
- 情绪数字滚动动画（animateInteger）逻辑保留，不受影响

## 实现注意事项

- `section-card` 组件的 `expanded` prop 需确认组件支持 false 初始值（当前代码 `collapsible="{{true}}" expanded="{{true}}"` 已验证用法，改为 `expanded="{{false}}"` 即可）
- 合并卡片的入场动画 animation-delay 需重新编排（原10个模块的 stagger delay 需压缩为7个节奏）
- 聪明钱列表放入行动建议 section-card 后，`onSmartMoneyTap` bindtap 需绑定在新位置的"查看更多"行上，路径不变
- riskPoints 渲染条数：wxml 层直接 `wx:for` 全量渲染，精选2-3条由 AI 产出侧保证（前端不截断，保持灵活性）
- 新样式类命名遵循现有 BEM 风格，前缀按模块区分（`combined-`、`decision-`、`risk-sent-` 等）

## 目录结构

```
touyanduck_appid/pages/briefing/
├── briefing.wxml   [MODIFY] 核心改动：模块合并重排，约235行 → 约200行
├── briefing.wxss   [MODIFY] 新增合并卡片样式，删除冗余样式，约891行 → 约850行
├── briefing.js     [MODIFY] 微小改动：入场动画 delay 编排调整，其余逻辑不变
└── briefing.json   [NO CHANGE] 页面配置无需改动
```