const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.title = "台积电 TSM 2026Q1 财报";
pres.author = "AI Research";

// ── 配色方案 ──────────────────────────────────────────────
const C = {
  navy:    "0D2341",   // 主色：深海军蓝（封面背景）
  teal:    "0A7EA4",   // 辅色：科技蓝
  accent:  "00C3A0",   // 强调色：青绿
  light:   "E8F4F8",   // 浅底色
  white:   "FFFFFF",
  gray1:   "F5F7FA",   // 卡片背景
  gray2:   "94A3B8",   // 次要文字
  gray3:   "475569",   // 正文
  dark:    "1E293B",   // 深色文字
  red:     "EF4444",
  green:   "22C55E",
  amber:   "F59E0B",
};

const makeShadow = () => ({
  type: "outer", blur: 8, offset: 3, angle: 135, color: "000000", opacity: 0.1
});

// ═══════════════════════════════════════════════════════════════
// 幻灯片 1：封面
// ═══════════════════════════════════════════════════════════════
{
  const sl = pres.addSlide();
  sl.background = { color: C.navy };

  // 左侧青绿色竖条
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 0.15, h: 5.625, fill: { color: C.accent }, line: { color: C.accent }
  });

  // 右下角装饰圆形（半透明）
  sl.addShape(pres.shapes.OVAL, {
    x: 7.8, y: 3.2, w: 3.5, h: 3.5,
    fill: { color: C.teal, transparency: 80 }, line: { color: C.teal, transparency: 80 }
  });
  sl.addShape(pres.shapes.OVAL, {
    x: 8.5, y: 2.6, w: 2.5, h: 2.5,
    fill: { color: C.accent, transparency: 85 }, line: { color: C.accent, transparency: 85 }
  });

  // 公司名
  sl.addText("【台积电 TSMC】", {
    x: 0.5, y: 0.8, w: 8, h: 0.55,
    fontSize: 16, color: C.accent, bold: true, fontFace: "Arial", margin: 0
  });

  // 主标题
  sl.addText("2026年第一季度财报", {
    x: 0.5, y: 1.45, w: 8, h: 1.0,
    fontSize: 40, color: C.white, bold: true, fontFace: "Arial", margin: 0
  });

  // 副标题
  sl.addText("业绩全面超预期 · 毛利率历史性突破66% · AI超级周期持续兑现", {
    x: 0.5, y: 2.55, w: 8.5, h: 0.5,
    fontSize: 14, color: "B8D4E8", italic: false, fontFace: "Arial", margin: 0
  });

  // 分隔线
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0.5, y: 3.2, w: 5.5, h: 0.03,
    fill: { color: C.teal }, line: { color: C.teal }
  });

  // 数据标注行
  const tags = [
    { label: "营收", val: "$35.9B", sub: "+40.6% YoY" },
    { label: "净利润", val: "$18.1B", sub: "+58.3% YoY" },
    { label: "毛利率", val: "66.2%", sub: "历史新高" },
  ];
  tags.forEach((t, i) => {
    const x = 0.5 + i * 3.1;
    sl.addText(t.val, {
      x, y: 3.5, w: 2.8, h: 0.55,
      fontSize: 24, color: C.white, bold: true, fontFace: "Arial", margin: 0
    });
    sl.addText(t.label + "  " + t.sub, {
      x, y: 4.1, w: 2.8, h: 0.3,
      fontSize: 11, color: C.accent, fontFace: "Arial", margin: 0
    });
  });

  // 日期
  sl.addText("财报发布日期：2026年4月16日", {
    x: 0.5, y: 5.1, w: 5, h: 0.3,
    fontSize: 10, color: C.gray2, fontFace: "Arial", margin: 0
  });
}

// ═══════════════════════════════════════════════════════════════
// 幻灯片 2：核心财务数据
// ═══════════════════════════════════════════════════════════════
{
  const sl = pres.addSlide();
  sl.background = { color: C.white };

  // 顶部色块
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.navy }, line: { color: C.navy }
  });
  sl.addText("核心财务数据", {
    x: 0.4, y: 0, w: 8, h: 0.9,
    fontSize: 22, color: C.white, bold: true, fontFace: "Arial", valign: "middle", margin: 0
  });
  sl.addText("2026 Q1", {
    x: 8.2, y: 0, w: 1.6, h: 0.9,
    fontSize: 13, color: C.accent, bold: true, fontFace: "Arial", valign: "middle", align: "right", margin: 0
  });

  // 4个核心KPI卡片
  const kpis = [
    { title: "总收入", main: "$35.9B", yoy: "+40.6%", qoq: "+6.4%", color: C.teal },
    { title: "净利润", main: "$18.1B", yoy: "+58.3%", qoq: "+13.2%", color: C.accent },
    { title: "摊薄EPS", main: "$3.49", yoy: "+58.3%", qoq: "—", color: "6366F1" },
    { title: "毛利率", main: "66.2%", yoy: "历史新高", qoq: "+3.9ppt", color: C.amber },
  ];

  kpis.forEach((k, i) => {
    const x = 0.25 + i * 2.42;
    // 卡片背景
    sl.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.05, w: 2.2, h: 2.4,
      fill: { color: C.gray1 }, line: { color: "E2E8F0", width: 1 },
      shadow: makeShadow()
    });
    // 顶部色条
    sl.addShape(pres.shapes.RECTANGLE, {
      x, y: 1.05, w: 2.2, h: 0.08,
      fill: { color: k.color }, line: { color: k.color }
    });
    sl.addText(k.title, {
      x: x + 0.12, y: 1.18, w: 2.0, h: 0.35,
      fontSize: 12, color: C.gray3, fontFace: "Arial", margin: 0
    });
    sl.addText(k.main, {
      x: x + 0.1, y: 1.55, w: 2.0, h: 0.65,
      fontSize: 26, color: C.dark, bold: true, fontFace: "Arial", margin: 0
    });
    sl.addText("同比 " + k.yoy, {
      x: x + 0.12, y: 2.25, w: 2.0, h: 0.3,
      fontSize: 11, color: C.green, bold: true, fontFace: "Arial", margin: 0
    });
    sl.addText("环比 " + k.qoq, {
      x: x + 0.12, y: 2.55, w: 2.0, h: 0.28,
      fontSize: 11, color: C.gray2, fontFace: "Arial", margin: 0
    });
  });

  // 利润率指标行
  const margins = [
    { label: "营业利益率", val: "58.1%" },
    { label: "净利率", val: "50.5%", note: "突破50%历史性节点" },
    { label: "2026全年资本开支", val: "$520-560亿" },
    { label: "Q2营收指引", val: "$390-402亿" },
  ];

  margins.forEach((m, i) => {
    const x = 0.25 + i * 2.42;
    sl.addShape(pres.shapes.RECTANGLE, {
      x, y: 3.6, w: 2.2, h: 1.6,
      fill: { color: C.navy }, line: { color: C.navy },
      shadow: makeShadow()
    });
    sl.addText(m.label, {
      x: x + 0.12, y: 3.7, w: 2.0, h: 0.45,
      fontSize: 11, color: "A0B8CC", fontFace: "Arial", margin: 0
    });
    sl.addText(m.val, {
      x: x + 0.1, y: 4.12, w: 2.0, h: 0.52,
      fontSize: 20, color: C.white, bold: true, fontFace: "Arial", margin: 0
    });
    if (m.note) {
      sl.addText(m.note, {
        x: x + 0.12, y: 4.67, w: 2.0, h: 0.3,
        fontSize: 9, color: C.accent, fontFace: "Arial", margin: 0
      });
    }
  });
}

// ═══════════════════════════════════════════════════════════════
// 幻灯片 3：主营业务收入（平台拆分）
// ═══════════════════════════════════════════════════════════════
{
  const sl = pres.addSlide();
  sl.background = { color: C.white };

  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.navy }, line: { color: C.navy }
  });
  sl.addText("主营业务收入", {
    x: 0.4, y: 0, w: 7, h: 0.9,
    fontSize: 22, color: C.white, bold: true, fontFace: "Arial", valign: "middle", margin: 0
  });
  sl.addText("按平台拆分 2026 Q1", {
    x: 6.5, y: 0, w: 3.2, h: 0.9,
    fontSize: 13, color: C.accent, fontFace: "Arial", valign: "middle", align: "right", margin: 0
  });

  // 左侧：饼图
  sl.addChart(pres.charts.DOUGHNUT, [{
    name: "平台营收占比",
    labels: ["HPC（高性能计算）", "智能手机", "IoT（物联网）", "汽车", "其他"],
    values: [61, 26, 6, 4, 3]
  }], {
    x: 0.3, y: 1.0, w: 4.2, h: 4.3,
    chartColors: [C.teal, "6366F1", C.amber, C.accent, "94A3B8"],
    showPercent: true,
    dataLabelColor: C.white,
    dataLabelFontSize: 11,
    showLegend: true,
    legendPos: "b",
    legendFontSize: 10,
    legendColor: C.dark,
    chartArea: { fill: { color: C.white } },
    holeSize: 55,
  });

  // 右侧：业务明细列表
  const platforms = [
    {
      icon: "▲", name: "HPC（高性能计算）", pct: "61%", qoq: "+20%",
      desc: "AI加速器、数据中心GPU/CPU，首次突破60%",
      est: "约 $21.9B", color: C.teal, up: true
    },
    {
      icon: "▼", name: "智能手机", pct: "26%", qoq: "-11%",
      desc: "季节性回落，苹果A19系列3nm在产",
      est: "约 $9.3B", color: "6366F1", up: false
    },
    {
      icon: "▲", name: "IoT（物联网）", pct: "6%", qoq: "+12%",
      desc: "物联网终端需求持续恢复",
      est: "约 $2.2B", color: C.amber, up: true
    },
    {
      icon: "▼", name: "汽车", pct: "4%", qoq: "-7%",
      desc: "客户仍处于去库存阶段",
      est: "约 $1.4B", color: "EF4444", up: false
    },
  ];

  platforms.forEach((p, i) => {
    const y = 1.05 + i * 1.08;
    sl.addShape(pres.shapes.RECTANGLE, {
      x: 4.8, y, w: 4.95, h: 0.95,
      fill: { color: C.gray1 }, line: { color: "E2E8F0", width: 1 },
      shadow: makeShadow()
    });
    // 左色条
    sl.addShape(pres.shapes.RECTANGLE, {
      x: 4.8, y, w: 0.07, h: 0.95,
      fill: { color: p.color }, line: { color: p.color }
    });
    sl.addText(p.name, {
      x: 5.0, y: y + 0.08, w: 2.5, h: 0.3,
      fontSize: 12, color: C.dark, bold: true, fontFace: "Arial", margin: 0
    });
    sl.addText(p.pct, {
      x: 7.5, y: y + 0.05, w: 0.8, h: 0.38,
      fontSize: 22, color: p.color, bold: true, fontFace: "Arial", align: "center", margin: 0
    });
    sl.addText("环比 " + p.qoq, {
      x: 8.35, y: y + 0.1, w: 1.3, h: 0.28,
      fontSize: 11, color: p.up ? C.green : C.red, bold: true, fontFace: "Arial", margin: 0
    });
    sl.addText(p.desc + "  " + p.est, {
      x: 5.0, y: y + 0.55, w: 4.6, h: 0.3,
      fontSize: 10, color: C.gray2, fontFace: "Arial", margin: 0
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// 幻灯片 4：先进制程收入结构
// ═══════════════════════════════════════════════════════════════
{
  const sl = pres.addSlide();
  sl.background = { color: C.white };

  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.navy }, line: { color: C.navy }
  });
  sl.addText("先进制程收入结构", {
    x: 0.4, y: 0, w: 7, h: 0.9,
    fontSize: 22, color: C.white, bold: true, fontFace: "Arial", valign: "middle", margin: 0
  });
  sl.addText("Technology Node 2026 Q1", {
    x: 6.2, y: 0, w: 3.6, h: 0.9,
    fontSize: 13, color: C.accent, fontFace: "Arial", valign: "middle", align: "right", margin: 0
  });

  // 左侧条形图（制程占比）
  sl.addChart(pres.charts.BAR, [{
    name: "占比 %",
    labels: ["3nm (N3)", "5nm (N5/N4)", "7nm及以下其他", "成熟制程 (>7nm)"],
    values: [25, 36, 0, 39]
  }], {
    x: 0.3, y: 1.0, w: 5.5, h: 4.3,
    barDir: "col",
    chartColors: [C.accent, C.teal, "94A3B8", "CBD5E1"],
    chartArea: { fill: { color: C.white } },
    catAxisLabelColor: C.gray3,
    valAxisLabelColor: C.gray3,
    valGridLine: { color: "E2E8F0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelColor: C.dark,
    dataLabelFontSize: 12,
    showLegend: false,
    valAxisMaxVal: 50,
    showTitle: false,
  });

  // 右侧：制程说明卡片
  const nodes = [
    {
      node: "3nm（N3系列）",
      pct: "25%",
      note: "Apple A19 · Nvidia Blackwell Ultra · 高通",
      color: C.accent
    },
    {
      node: "5nm（N5/N4系列）",
      pct: "36%",
      note: "Nvidia H100/H200 · AMD MI300 · AI ASIC",
      color: C.teal
    },
    {
      node: "先进制程合计（≤7nm）",
      pct: "61%",
      note: "创历史新高，持续提升",
      color: "6366F1"
    },
    {
      node: "N2（2nm）量产进展",
      pct: "1月量产",
      note: "Fab20/22已量产，良率65-80%，Q4起贡献营收",
      color: C.amber
    },
  ];

  nodes.forEach((n, i) => {
    const y = 1.05 + i * 1.08;
    sl.addShape(pres.shapes.RECTANGLE, {
      x: 6.1, y, w: 3.6, h: 0.95,
      fill: { color: C.gray1 }, line: { color: "E2E8F0", width: 1 },
      shadow: makeShadow()
    });
    sl.addShape(pres.shapes.RECTANGLE, {
      x: 6.1, y, w: 0.07, h: 0.95,
      fill: { color: n.color }, line: { color: n.color }
    });
    sl.addText(n.node, {
      x: 6.28, y: y + 0.07, w: 2.4, h: 0.32,
      fontSize: 11, color: C.dark, bold: true, fontFace: "Arial", margin: 0
    });
    sl.addText(n.pct, {
      x: 8.75, y: y + 0.05, w: 0.85, h: 0.38,
      fontSize: 20, color: n.color, bold: true, fontFace: "Arial", align: "center", margin: 0
    });
    sl.addText(n.note, {
      x: 6.28, y: y + 0.58, w: 3.3, h: 0.28,
      fontSize: 9.5, color: C.gray2, fontFace: "Arial", margin: 0
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// 幻灯片 5：历史年度营收趋势
// ═══════════════════════════════════════════════════════════════
{
  const sl = pres.addSlide();
  sl.background = { color: C.white };

  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.navy }, line: { color: C.navy }
  });
  sl.addText("历史年度营收数据", {
    x: 0.4, y: 0, w: 7, h: 0.9,
    fontSize: 22, color: C.white, bold: true, fontFace: "Arial", valign: "middle", margin: 0
  });
  sl.addText("单位：Billion USD  2016–2025", {
    x: 6.0, y: 0, w: 3.7, h: 0.9,
    fontSize: 13, color: C.accent, fontFace: "Arial", valign: "middle", align: "right", margin: 0
  });

  // 年度营收柱状图
  sl.addChart(pres.charts.BAR, [{
    name: "年度营收（$B）",
    labels: ["2016", "2017", "2018", "2019", "2020", "2021", "2022", "2023", "2024", "2025"],
    values: [29.4, 30.4, 34.1, 35.7, 47.4, 56.8, 75.9, 70.4, 88.3, 122.3]
  }], {
    x: 0.3, y: 1.05, w: 7.5, h: 4.2,
    barDir: "col",
    chartColors: ["0A7EA4", "0A7EA4", "0A7EA4", "0A7EA4", "0A7EA4", "0A7EA4", "0A7EA4", "94A3B8", "00C3A0", "00C3A0"],
    chartArea: { fill: { color: C.white } },
    catAxisLabelColor: C.gray3,
    valAxisLabelColor: C.gray3,
    valGridLine: { color: "E2E8F0", size: 0.5 },
    catGridLine: { style: "none" },
    showValue: true,
    dataLabelColor: C.dark,
    dataLabelFontSize: 10,
    showLegend: false,
    showTitle: false,
  });

  // 右侧关键增速标注
  const annots = [
    { year: "2025", val: "$122.3B", chg: "+38.5%", note: "AI驱动历史新高" },
    { year: "2024", val: "$88.3B",  chg: "+25.4%", note: "AI基础设施需求" },
    { year: "26Q1", val: "$35.9B",  chg: "+40.6%", note: "连续四季创历史高" },
  ];

  annots.forEach((a, i) => {
    const y = 1.2 + i * 1.35;
    sl.addShape(pres.shapes.RECTANGLE, {
      x: 7.95, y, w: 1.8, h: 1.15,
      fill: { color: C.navy }, line: { color: C.navy },
      shadow: makeShadow()
    });
    sl.addText(a.year, {
      x: 8.05, y: y + 0.07, w: 1.6, h: 0.28,
      fontSize: 11, color: C.accent, fontFace: "Arial", bold: true, margin: 0
    });
    sl.addText(a.val, {
      x: 8.05, y: y + 0.35, w: 1.6, h: 0.35,
      fontSize: 16, color: C.white, bold: true, fontFace: "Arial", margin: 0
    });
    sl.addText(a.chg + "  " + a.note, {
      x: 8.05, y: y + 0.75, w: 1.6, h: 0.28,
      fontSize: 8.5, color: C.accent, fontFace: "Arial", margin: 0
    });
  });
}

// ═══════════════════════════════════════════════════════════════
// 幻灯片 6：管理层展望 & 风险提示
// ═══════════════════════════════════════════════════════════════
{
  const sl = pres.addSlide();
  sl.background = { color: C.white };

  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.navy }, line: { color: C.navy }
  });
  sl.addText("管理层展望 & 风险提示", {
    x: 0.4, y: 0, w: 9, h: 0.9,
    fontSize: 22, color: C.white, bold: true, fontFace: "Arial", valign: "middle", margin: 0
  });

  // 左侧：展望 / 亮点
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 0.25, y: 1.0, w: 4.55, h: 0.45,
    fill: { color: C.teal }, line: { color: C.teal }
  });
  sl.addText("核心亮点 & 前瞻指引", {
    x: 0.35, y: 1.0, w: 4.35, h: 0.45,
    fontSize: 14, color: C.white, bold: true, fontFace: "Arial", valign: "middle", margin: 0
  });

  const highlights = [
    "Q2 2026营收指引 $390-402亿，环比+10%，毛利率65.5-67.5%",
    "AI加速器2024-2029年CAGR预期从45%上调至54-56%",
    "2026全年资本开支$520-560亿，同比+27-40%",
    "N2（2nm）已量产，早期良率65-80%，显著优于三星同期",
    "CoWoS封装产能年底将扩至月产127,000片（vs 2025初约45K）",
    "先进封装2026年预计贡献超10%营收（约$50亿+）",
    "CEO魏哲家：AI需求极其强劲，但\"我也很紧张\"",
  ];

  sl.addText(highlights.map((h, i) => ({
    text: h,
    options: { bullet: true, breakLine: i < highlights.length - 1 }
  })), {
    x: 0.25, y: 1.5, w: 4.55, h: 3.8,
    fontSize: 11, color: C.dark, fontFace: "Arial",
    paraSpaceAfter: 4
  });

  // 右侧：风险提示
  sl.addShape(pres.shapes.RECTANGLE, {
    x: 5.2, y: 1.0, w: 4.55, h: 0.45,
    fill: { color: C.red }, line: { color: C.red }
  });
  sl.addText("主要风险提示", {
    x: 5.3, y: 1.0, w: 4.35, h: 0.45,
    fontSize: 14, color: C.white, bold: true, fontFace: "Arial", valign: "middle", margin: 0
  });

  const risks = [
    "客户集中度：前10大AI设计公司贡献HPC营收80%+",
    "N2爬坡稀释：预计稀释2026全年毛利率2-3ppt",
    "Arizona成本：海外工厂毛利率低于台湾约10ppt",
    "资本开支回报：$560亿高度依赖AI需求预测兑现",
    "地缘政治：80%+产能集中台湾，台海风险为尾部风险",
    "估值偏高：前瞻P/E约21.9x，已隐含乐观情景",
    "中国市场萎缩：先进制程受出口管制持续收紧",
  ];

  sl.addText(risks.map((r, i) => ({
    text: r,
    options: { bullet: true, breakLine: i < risks.length - 1 }
  })), {
    x: 5.2, y: 1.5, w: 4.55, h: 3.8,
    fontSize: 11, color: C.dark, fontFace: "Arial",
    paraSpaceAfter: 4
  });
}

// ─── 保存文件 ────────────────────────────────────────────────
pres.writeFile({ fileName: "TSM-台积电-26Q1财报.pptx" })
  .then(() => console.log("✅ PPT生成成功：TSM-台积电-26Q1财报.pptx"))
  .catch(err => console.error("❌ 生成失败:", err));
