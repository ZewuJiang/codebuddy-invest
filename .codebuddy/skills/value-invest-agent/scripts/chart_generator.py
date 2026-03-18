#!/usr/bin/env python3
"""
投行级图表生成器 (Investment Bank Grade Chart Generator)
对标高盛/摩根士丹利/JPM研究报告的可视化风格
生成PNG图表，供嵌入MD报告后通过md_to_pdf.py转为PDF

色彩体系：深蓝(#0f2942) + 红(#e63946) + 蓝灰(#457b9d) + 浅灰(#edf2f4)
与md_to_pdf.py的CSS配色完全一致
"""

import os
import matplotlib
matplotlib.use('Agg')  # 非交互式后端
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
from typing import List, Optional, Dict, Tuple

# ─── 全局样式配置 ──────────────────────────────────────
# 投行报告配色（与md_to_pdf.py CSS一致）
COLORS = {
    'dark_blue': '#0f2942',
    'red': '#e63946',
    'blue_gray': '#457b9d',
    'light_blue': '#a8dadc',
    'light_gray': '#edf2f4',
    'text': '#1a1a2e',
    'text_secondary': '#2b2d42',
    'bg': '#ffffff',
    'grid': '#e8ecf1',
    'positive': '#2a9d8f',  # 正值/上涨
    'negative': '#e63946',  # 负值/下跌
}

# 多系列配色盘（8色）
PALETTE = ['#0f2942', '#e63946', '#457b9d', '#2a9d8f', '#f4a261', '#264653', '#e76f51', '#a8dadc']

# 字体配置（macOS matplotlib可用中文字体）
FONT_FAMILY = 'Heiti TC'
FONT_FALLBACK = 'STHeiti'

def _setup_style():
    """设置全局matplotlib样式（紧凑版，适配报告正文字体大小）"""
    plt.rcParams.update({
        'font.family': [FONT_FAMILY, FONT_FALLBACK, 'sans-serif'],
        'font.size': 8,
        'axes.titlesize': 10,
        'axes.titleweight': 'bold',
        'axes.labelsize': 8,
        'axes.labelcolor': COLORS['text'],
        'axes.edgecolor': COLORS['grid'],
        'axes.facecolor': COLORS['bg'],
        'axes.grid': True,
        'grid.color': COLORS['grid'],
        'grid.linewidth': 0.4,
        'grid.alpha': 0.6,
        'xtick.color': COLORS['text_secondary'],
        'ytick.color': COLORS['text_secondary'],
        'xtick.labelsize': 7.5,
        'ytick.labelsize': 7.5,
        'figure.facecolor': COLORS['bg'],
        'figure.dpi': 150,
        'savefig.dpi': 150,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.08,
        'legend.fontsize': 7,
        'legend.framealpha': 0.9,
        'legend.edgecolor': COLORS['grid'],
    })

_setup_style()


def _add_source_label(fig, source: str = ""):
    """在图表底部添加数据来源标注"""
    if source:
        fig.text(0.99, 0.01, f"数据来源: {source}", fontsize=5.5, color='#8d99ae',
                ha='right', va='bottom', style='italic')


def _add_watermark(ax, text: str = "AI Investment Research"):
    """添加浅色水印"""
    ax.text(0.5, 0.5, text, transform=ax.transAxes, fontsize=18, color='#f0f0f0',
            ha='center', va='center', rotation=30, alpha=0.12, fontweight='bold')


# ═══════════════════════════════════════════════════════
# 图表类型1：营收/利润趋势柱状图+折线图（双轴）
# ═══════════════════════════════════════════════════════
def chart_revenue_profit_trend(
    years: List[str],
    revenue: List[float],
    net_income: List[float],
    margin: List[float],
    title: str = "营收与净利润趋势",
    output_path: str = "chart_revenue_trend.png",
    source: str = "",
    revenue_label: str = "营收（亿美元）",
    income_label: str = "净利润（亿美元）",
    margin_label: str = "净利率",
    currency_symbol: str = "",
    amount_unit: str = "亿美元",
) -> str:
    """
    双轴柱状图：左轴营收+净利润柱状图，右轴净利率折线
    典型投行风格
    currency_symbol: 货币符号（如 $, HK$, ¥, ₩, €, £），为空则不加前缀
    amount_unit: 金额单位（如 亿美元, 亿港元, 亿元, 亿日元, 兆韩元, 亿欧元）
    """
    fig, ax1 = plt.subplots(figsize=(7, 3.8))

    x = np.arange(len(years))
    width = 0.35

    # 营收柱状图
    bars1 = ax1.bar(x - width/2, revenue, width, color=COLORS['dark_blue'], 
                    label=revenue_label, zorder=3, edgecolor='white', linewidth=0.5)
    # 净利润柱状图
    bars2 = ax1.bar(x + width/2, net_income, width, color=COLORS['red'],
                    label=income_label, zorder=3, edgecolor='white', linewidth=0.5)

    # 柱状图上方标注数值
    for bar in bars1:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(revenue)*0.01,
                f'{bar.get_height():,.0f}', ha='center', va='bottom', fontsize=6,
                fontweight='bold', color=COLORS['dark_blue'])
    for bar in bars2:
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(revenue)*0.01,
                f'{bar.get_height():,.0f}', ha='center', va='bottom', fontsize=6,
                fontweight='bold', color=COLORS['red'])

    ax1.set_xlabel('')
    ax1.set_ylabel(f'金额（{amount_unit}）', fontweight='bold', fontsize=7.5)
    ax1.set_xticks(x)
    ax1.set_xticklabels(years, fontweight='bold', fontsize=7)
    ax1.set_ylim(0, max(revenue) * 1.2)
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:,.0f}'))

    # 右轴：净利率折线
    ax2 = ax1.twinx()
    line = ax2.plot(x, margin, color=COLORS['blue_gray'], marker='o', linewidth=2,
                   markersize=5, markerfacecolor='white', markeredgecolor=COLORS['blue_gray'],
                   markeredgewidth=1.5, label=margin_label, zorder=5)
    for i, v in enumerate(margin):
        ax2.annotate(f'{v:.1f}%', (x[i], v), textcoords="offset points",
                    xytext=(0, 8), ha='center', fontsize=6.5, fontweight='bold',
                    color=COLORS['blue_gray'])
    ax2.set_ylabel(margin_label, fontweight='bold', color=COLORS['blue_gray'], fontsize=7.5)
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    ax2.set_ylim(min(margin) - 3, max(margin) + 5)

    # 合并图例
    bars_handles = [bars1, bars2]
    bars_labels = [revenue_label, income_label]
    line_handles, line_labels = ax2.get_legend_handles_labels()
    ax1.legend(bars_handles + line_handles, bars_labels + line_labels,
              loc='upper left', frameon=True, fancybox=True, fontsize=6.5)

    ax1.set_title(title, fontsize=10, fontweight='bold', color=COLORS['dark_blue'], pad=10)
    ax1.grid(axis='y', alpha=0.3)
    ax2.grid(False)

    _add_source_label(fig, source)
    _add_watermark(ax1)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


# ═══════════════════════════════════════════════════════
# 图表类型2：业务结构饼图/环形图
# ═══════════════════════════════════════════════════════
def chart_business_mix(
    labels: List[str],
    sizes: List[float],
    title: str = "业务营收构成",
    output_path: str = "chart_business_mix.png",
    source: str = "",
    highlight_idx: int = 0,
    currency_symbol: str = "",
    amount_unit: str = "亿",
) -> str:
    """
    投行风格环形图（Donut Chart）
    currency_symbol: 货币符号（如 $, HK$, ¥, ₩, €, £），为空则不加前缀
    amount_unit: 金额单位（如 亿, 兆 等），用于图例标注
    """
    fig, ax = plt.subplots(figsize=(6, 4.2))

    colors = PALETTE[:len(labels)]
    explode = [0.03] * len(labels)
    if 0 <= highlight_idx < len(labels):
        explode[highlight_idx] = 0.08

    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct='%1.1f%%', startangle=90,
        colors=colors, explode=explode, pctdistance=0.78,
        wedgeprops=dict(width=0.45, edgecolor='white', linewidth=1.5)
    )

    for t in autotexts:
        t.set_fontsize(7)
        t.set_fontweight('bold')
        t.set_color('white')

    # 外侧标签
    cs = currency_symbol or ''
    au = amount_unit or '亿'
    ax.legend(wedges, [f'{l}  ({cs}{s:,.0f}{au})' for l, s in zip(labels, sizes)],
             title="业务板块", loc="center left", bbox_to_anchor=(0.92, 0, 0.5, 1),
             fontsize=7, title_fontsize=8)

    # 中心文字
    total = sum(sizes)
    ax.text(0, 0, f'总计\n{cs}{total:,.0f}{au}', ha='center', va='center',
            fontsize=10, fontweight='bold', color=COLORS['dark_blue'])

    ax.set_title(title, fontsize=10, fontweight='bold', color=COLORS['dark_blue'], pad=12)

    _add_source_label(fig, source)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


# ═══════════════════════════════════════════════════════
# 图表类型3：毛利率/估值指标趋势折线图
# ═══════════════════════════════════════════════════════
def chart_metric_trend(
    years: List[str],
    metrics: Dict[str, List[float]],
    title: str = "关键指标趋势",
    output_path: str = "chart_metric_trend.png",
    source: str = "",
    y_format: str = "percent",  # "percent", "number", "dollar"
    y_label: str = "",
) -> str:
    """
    多指标折线图，支持多条线
    """
    fig, ax = plt.subplots(figsize=(7, 3.8))

    x = np.arange(len(years))
    for i, (name, values) in enumerate(metrics.items()):
        color = PALETTE[i % len(PALETTE)]
        # 安全处理：将None替换为0，确保matplotlib不崩溃
        safe_values = [v if v is not None else 0 for v in values]
        ax.plot(x, safe_values, marker='o', linewidth=2, markersize=5,
               markerfacecolor='white', markeredgecolor=color, markeredgewidth=1.5,
               color=color, label=name, zorder=5)
        # 数据标注
        for j, v in enumerate(safe_values):
            fmt = f'{v:.1f}%' if y_format == 'percent' else (f'${v:,.0f}' if y_format == 'dollar' else f'{v:,.1f}')
            ax.annotate(fmt, (x[j], v), textcoords="offset points",
                       xytext=(0, 8), ha='center', fontsize=6, fontweight='bold',
                       color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(years, fontweight='bold', fontsize=7)
    if y_format == 'percent':
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{v:.0f}%'))
    elif y_format == 'dollar':
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'${v:,.0f}'))

    if y_label:
        ax.set_ylabel(y_label, fontweight='bold', fontsize=7.5)

    ax.legend(loc='best', frameon=True, fancybox=True, fontsize=7)
    ax.set_title(title, fontsize=10, fontweight='bold', color=COLORS['dark_blue'], pad=10)
    ax.grid(axis='both', alpha=0.3)

    _add_source_label(fig, source)
    _add_watermark(ax)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


# ═══════════════════════════════════════════════════════
# 图表类型4：估值对比横向柱状图
# ═══════════════════════════════════════════════════════
def chart_valuation_comparison(
    companies: List[str],
    metrics: Dict[str, List[float]],
    title: str = "估值对比",
    output_path: str = "chart_valuation_comp.png",
    source: str = "",
    highlight_company: str = "",
) -> str:
    """
    横向分组柱状图，对比多公司多指标
    """
    n_companies = len(companies)
    n_metrics = len(metrics)
    fig, axes = plt.subplots(1, n_metrics, figsize=(2.8 * n_metrics, 3.5))
    if n_metrics == 1:
        axes = [axes]

    for idx, (metric_name, values) in enumerate(metrics.items()):
        ax = axes[idx]
        y = np.arange(n_companies)
        colors = []
        for i, c in enumerate(companies):
            if c == highlight_company:
                colors.append(COLORS['red'])
            else:
                colors.append(COLORS['dark_blue'])

        bars = ax.barh(y, values, color=colors, height=0.55, edgecolor='white', linewidth=0.5)

        # 数值标注
        for bar, val in zip(bars, values):
            ax.text(bar.get_width() + max(values) * 0.02, bar.get_y() + bar.get_height()/2,
                   f'{val:.1f}x' if 'PE' in metric_name or 'PEG' in metric_name or 'EV' in metric_name
                   else (f'{val:.1f}%' if val < 100 else f'{val:,.0f}'),
                   ha='left', va='center', fontsize=7, fontweight='bold',
                   color=COLORS['text'])

        ax.set_yticks(y)
        ax.set_yticklabels(companies, fontweight='bold', fontsize=7)
        ax.set_title(metric_name, fontsize=9, fontweight='bold', color=COLORS['dark_blue'])
        ax.set_xlim(0, max(values) * 1.3)
        ax.invert_yaxis()
        ax.grid(axis='x', alpha=0.3)
        ax.set_axisbelow(True)

    fig.suptitle(title, fontsize=10, fontweight='bold', color=COLORS['dark_blue'], y=1.02)
    _add_source_label(fig, source)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


# ═══════════════════════════════════════════════════════
# 图表类型5：风险矩阵散点图
# ═══════════════════════════════════════════════════════
def chart_risk_matrix(
    risks: List[Dict],
    title: str = "风险评估矩阵",
    output_path: str = "chart_risk_matrix.png",
    source: str = "",
) -> str:
    """
    风险矩阵气泡图
    risks: [{"name": "关税", "probability": 0.7, "impact": 0.9, "level": "高"}, ...]
    probability和impact取值0-1
    """
    fig, ax = plt.subplots(figsize=(6.5, 4.8))

    # 背景色块（四象限）
    ax.axhspan(0.5, 1.0, xmin=0.5, xmax=1.0, alpha=0.08, color='#e63946')  # 高概率高影响
    ax.axhspan(0.5, 1.0, xmin=0, xmax=0.5, alpha=0.05, color='#f4a261')     # 低概率高影响
    ax.axhspan(0, 0.5, xmin=0.5, xmax=1.0, alpha=0.05, color='#f4a261')     # 高概率低影响
    ax.axhspan(0, 0.5, xmin=0, xmax=0.5, alpha=0.03, color='#2a9d8f')       # 低概率低影响

    level_colors = {'高': '#e63946', '中高': '#f4a261', '中': '#457b9d', '中低': '#2a9d8f', '低': '#a8dadc'}

    for r in risks:
        color = level_colors.get(r.get('level', '中'), COLORS['blue_gray'])
        size = 120 + r['impact'] * 180
        ax.scatter(r['probability'], r['impact'], s=size, c=color,
                  alpha=0.75, edgecolors='white', linewidth=1.5, zorder=5)
        ax.annotate(r['name'], (r['probability'], r['impact']),
                   textcoords="offset points", xytext=(10, 6),
                   fontsize=6.5, fontweight='bold', color=COLORS['text'],
                   bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor=COLORS['grid']))

    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel('发生概率 →', fontsize=8, fontweight='bold')
    ax.set_ylabel('影响程度 →', fontsize=8, fontweight='bold')
    ax.set_title(title, fontsize=10, fontweight='bold', color=COLORS['dark_blue'], pad=10)

    # 象限标签
    ax.text(0.25, 0.95, '低概率 / 高影响\n（黑天鹅）', ha='center', va='top',
            fontsize=6.5, color='#8d99ae', style='italic')
    ax.text(0.75, 0.95, '高概率 / 高影响\n（核心风险）', ha='center', va='top',
            fontsize=6.5, color='#e63946', fontweight='bold')
    ax.text(0.25, 0.05, '低概率 / 低影响\n（可忽略）', ha='center', va='bottom',
            fontsize=6.5, color='#8d99ae', style='italic')
    ax.text(0.75, 0.05, '高概率 / 低影响\n（日常管理）', ha='center', va='bottom',
            fontsize=6.5, color='#8d99ae', style='italic')

    ax.axhline(y=0.5, color=COLORS['grid'], linewidth=1, linestyle='--', alpha=0.5)
    ax.axvline(x=0.5, color=COLORS['grid'], linewidth=1, linestyle='--', alpha=0.5)

    _add_source_label(fig, source)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


# ═══════════════════════════════════════════════════════
# 图表类型6：DCF敏感性热力图
# ═══════════════════════════════════════════════════════
def chart_sensitivity_heatmap(
    row_labels: List[str],
    col_labels: List[str],
    values: List[List[float]],
    title: str = "DCF敏感性分析",
    output_path: str = "chart_sensitivity.png",
    source: str = "",
    row_title: str = "WACC",
    col_title: str = "永续增长率",
    current_price: float = None,
    fmt: str = None,
    currency_symbol: str = "$",
) -> str:
    """
    估值敏感性热力图
    currency_symbol: 货币符号，用于格式化数值和标注
    fmt: 数值格式字符串，为None时自动根据currency_symbol生成
    """
    if fmt is None:
        fmt = f"{currency_symbol}{{:.0f}}"
    fig, ax = plt.subplots(figsize=(6.5, 4))

    data = np.array(values)
    vmin, vmax = data.min(), data.max()

    # 自定义颜色映射：低于当前价红色，高于当前价绿色
    from matplotlib.colors import LinearSegmentedColormap
    if current_price:
        # 红→白→绿
        cmap = LinearSegmentedColormap.from_list('valuation',
            ['#e63946', '#fce4e4', '#ffffff', '#d4edda', '#2a9d8f'])
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
    else:
        cmap = LinearSegmentedColormap.from_list('valuation',
            ['#edf2f4', '#457b9d', '#0f2942'])
        norm = None

    im = ax.imshow(data, cmap=cmap, aspect='auto', norm=norm)

    # 标注数值
    for i in range(len(row_labels)):
        for j in range(len(col_labels)):
            val = data[i, j]
            color = 'white' if (current_price and abs(val - current_price) > (vmax - vmin) * 0.3) else COLORS['text']
            weight = 'bold' if (current_price and abs(val - current_price) < (vmax - vmin) * 0.1) else 'normal'
            # 当前价格附近加框
            text = fmt.format(val)
            if current_price and abs(val - current_price) < (vmax - vmin) * 0.08:
                text = f'★{text}★'
                weight = 'bold'
            ax.text(j, i, text, ha='center', va='center', fontsize=7.5,
                   fontweight=weight, color=color)

    ax.set_xticks(np.arange(len(col_labels)))
    ax.set_yticks(np.arange(len(row_labels)))
    ax.set_xticklabels(col_labels, fontweight='bold', fontsize=7)
    ax.set_yticklabels(row_labels, fontweight='bold', fontsize=7)
    ax.set_xlabel(col_title, fontsize=8, fontweight='bold')
    ax.set_ylabel(row_title, fontsize=8, fontweight='bold')
    ax.set_title(title, fontsize=10, fontweight='bold', color=COLORS['dark_blue'], pad=10)

    if current_price:
        ax.text(len(col_labels) - 0.5, -0.7, f'当前股价: {currency_symbol}{current_price:.2f}',
               ha='right', fontsize=7.5, fontweight='bold', color=COLORS['red'])

    # 颜色条
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cbar.ax.set_ylabel(f'每股价值 ({currency_symbol})', fontweight='bold', fontsize=7)
    cbar.ax.tick_params(labelsize=6.5)

    _add_source_label(fig, source)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


# ═══════════════════════════════════════════════════════
# 图表类型7：估值方法对比瀑布图/区间图
# ═══════════════════════════════════════════════════════
def chart_valuation_range(
    methods: List[str],
    low: List[float],
    mid: List[float],
    high: List[float],
    current_price: float,
    title: str = "估值交叉验证",
    output_path: str = "chart_valuation_range.png",
    source: str = "",
    currency_symbol: str = "$",
) -> str:
    """
    估值区间对比图（football field chart），投行最经典的图表之一
    currency_symbol: 货币符号（$, HK$, ¥, ₩, €, £）
    """
    fig, ax = plt.subplots(figsize=(7, 3.5))

    y = np.arange(len(methods))
    height = 0.45

    for i in range(len(methods)):
        # 区间横条
        ax.barh(y[i], high[i] - low[i], left=low[i], height=height,
               color=COLORS['light_blue'], alpha=0.6, edgecolor=COLORS['blue_gray'], linewidth=0.8)
        # 中枢标记
        ax.plot(mid[i], y[i], 'D', color=COLORS['dark_blue'], markersize=5.5, zorder=5)
        # 标注
        ax.text(low[i] - 2, y[i], f'{currency_symbol}{low[i]:.0f}', ha='right', va='center', fontsize=6.5, color=COLORS['text_secondary'])
        ax.text(high[i] + 2, y[i], f'{currency_symbol}{high[i]:.0f}', ha='left', va='center', fontsize=6.5, color=COLORS['text_secondary'])
        ax.text(mid[i], y[i] + 0.28, f'{currency_symbol}{mid[i]:.0f}', ha='center', va='bottom', fontsize=7,
               fontweight='bold', color=COLORS['dark_blue'])

    # 当前股价竖线
    ax.axvline(x=current_price, color=COLORS['red'], linewidth=1.5, linestyle='--', zorder=4)
    ax.text(current_price, len(methods) - 0.3, f'  当前: {currency_symbol}{current_price:.0f}', fontsize=7.5,
           fontweight='bold', color=COLORS['red'], va='bottom')

    ax.set_yticks(y)
    ax.set_yticklabels(methods, fontweight='bold', fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel(f'每股价值 ({currency_symbol})', fontsize=8, fontweight='bold')
    ax.set_title(title, fontsize=10, fontweight='bold', color=COLORS['dark_blue'], pad=10)
    ax.grid(axis='x', alpha=0.3)
    ax.set_axisbelow(True)

    # 图例
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [
        Patch(facecolor=COLORS['light_blue'], alpha=0.6, edgecolor=COLORS['blue_gray'], label='估值区间'),
        Line2D([0], [0], marker='D', color='w', markerfacecolor=COLORS['dark_blue'], markersize=5.5, label='中枢值'),
        Line2D([0], [0], color=COLORS['red'], linewidth=1.5, linestyle='--', label=f'当前股价 {currency_symbol}{current_price:.0f}'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', frameon=True, fancybox=True, fontsize=6.5)

    _add_source_label(fig, source)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


# ═══════════════════════════════════════════════════════
# 图表类型8：EPS冲击瀑布图
# ═══════════════════════════════════════════════════════
def chart_eps_waterfall(
    base_eps: float,
    impacts: List[Tuple[str, float]],
    title: str = "风险情景EPS冲击分析",
    output_path: str = "chart_eps_waterfall.png",
    source: str = "",
    currency_symbol: str = "$",
) -> str:
    """
    瀑布图展示各风险因素对EPS的影响
    impacts: [("关税", -1.20), ("反垄断", -0.44), ...]
    currency_symbol: 货币符号（$, HK$, ¥, ₩, €, £）
    """
    fig, ax = plt.subplots(figsize=(7, 3.8))

    labels = ['基准EPS'] + [i[0] for i in impacts] + ['调整后EPS']
    values = [base_eps] + [i[1] for i in impacts] + [0]

    # 计算累计值
    cumulative = [base_eps]
    for _, v in impacts:
        cumulative.append(cumulative[-1] + v)
    adjusted_eps = cumulative[-1]
    values[-1] = adjusted_eps

    x = np.arange(len(labels))
    colors = []
    bottoms = []

    # 基准
    colors.append(COLORS['dark_blue'])
    bottoms.append(0)

    # 各影响项
    running = base_eps
    for _, v in impacts:
        if v < 0:
            colors.append(COLORS['negative'])
            bottoms.append(running + v)
        else:
            colors.append(COLORS['positive'])
            bottoms.append(running)
        running += v

    # 调整后
    colors.append(COLORS['blue_gray'])
    bottoms.append(0)

    bar_values = [base_eps] + [abs(v) for _, v in impacts] + [adjusted_eps]

    bars = ax.bar(x, bar_values, bottom=bottoms, color=colors, width=0.55,
                 edgecolor='white', linewidth=1, zorder=3)

    # 连接线
    for i in range(len(labels) - 1):
        top = bottoms[i] + bar_values[i]
        ax.plot([x[i] + 0.3, x[i+1] - 0.3], [top, top] if i == 0 else [bottoms[i] + bar_values[i], bottoms[i] + bar_values[i]],
               color=COLORS['grid'], linewidth=1, linestyle=':', zorder=2)

    # 数值标注
    for i, bar in enumerate(bars):
        val = values[i] if i == 0 or i == len(labels) - 1 else values[i]
        y_pos = bottoms[i] + bar_values[i] + 0.05
        text = f'{currency_symbol}{val:+.2f}' if i > 0 and i < len(labels) - 1 else f'{currency_symbol}{bar_values[i]:.2f}'
        color = COLORS['negative'] if val < 0 else (COLORS['dark_blue'] if i == 0 else COLORS['blue_gray'])
        ax.text(bar.get_x() + bar.get_width()/2, y_pos, text,
               ha='center', va='bottom', fontsize=7, fontweight='bold', color=color)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=20, ha='right', fontweight='bold', fontsize=6.5)
    ax.set_ylabel(f'EPS ({currency_symbol})', fontsize=8, fontweight='bold')
    ax.set_title(title, fontsize=10, fontweight='bold', color=COLORS['dark_blue'], pad=10)
    ax.set_ylim(0, base_eps * 1.25)
    ax.grid(axis='y', alpha=0.3)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f'{currency_symbol}{v:.2f}'))

    _add_source_label(fig, source)
    _add_watermark(ax)

    fig.tight_layout()
    fig.savefig(output_path)
    plt.close(fig)
    return output_path


# ═══════════════════════════════════════════════════════
# 主函数：示例用法
# ═══════════════════════════════════════════════════════
if __name__ == '__main__':
    print("📊 投行级图表生成器已加载")
    print("可用图表类型：")
    print("  1. chart_revenue_profit_trend  - 营收/利润趋势（双轴柱状+折线）")
    print("  2. chart_business_mix          - 业务结构环形图")
    print("  3. chart_metric_trend          - 关键指标趋势折线图")
    print("  4. chart_valuation_comparison  - 估值对比横向柱状图")
    print("  5. chart_risk_matrix           - 风险评估矩阵散点图")
    print("  6. chart_sensitivity_heatmap   - DCF敏感性热力图")
    print("  7. chart_valuation_range       - 估值区间对比图（Football Field）")
    print("  8. chart_eps_waterfall          - EPS冲击瀑布图")
