#!/bin/bash
# ============================================================
# 投研鸭 HTML 报告 — 每日数据更新串联脚本 v1.0
# 执行顺序：JSON语法校验 → sparkline/chartData 历史序列补全（软依赖） → 渲染 HTML
#
# 用法（AI 直接调用，无需用户手动操作）：
#   bash run_daily.sh [YYYY-MM-DD]
#   日期参数可选，默认取今天（北京时间）
#
# 与原 daily-app 版的区别：
#   - 第2步从「上传云数据库」改为「渲染 HTML 报告」
#   - 无需微信云开发凭证
#   - 输出 touyanduck-YYYY-MM-DD.html 单文件
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)/workflows/investment_agent_data/miniapp_sync"

# 日期参数（默认今天北京时间）
DATE="${1:-$(date +%Y-%m-%d)}"

echo "============================================================"
echo "🦆 投研鸭 HTML 报告生成 — ${DATE}"
echo "============================================================"
echo ""

# ── 第0步：JSON 语法预校验 ────────────────────────────────────
echo "🔍 第0步：JSON 语法校验..."
echo ""

JSON_OK=1
for f in briefing.json markets.json watchlist.json radar.json; do
    FPATH="$SYNC_DIR/$f"
    if [ ! -f "$FPATH" ]; then
        echo "  ❌ 文件不存在: $f"
        JSON_OK=0
        continue
    fi
    python3 -m json.tool "$FPATH" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "  ❌ JSON 语法错误: $f"
        JSON_OK=0
    else
        echo "  ✅ $f"
    fi
done

if [ "$JSON_OK" -ne 1 ]; then
    echo ""
    echo "❌ JSON 语法校验失败，请修复后重新运行。"
    exit 1
fi

echo ""
echo "✅ JSON 语法校验通过"
echo ""

# ── 第1步：sparkline/chartData 历史序列补全（软依赖） ─────────
echo "📡 第1步：sparkline/chartData 补全（AkShare）..."
echo ""

cd "$SCRIPT_DIR"

API_CORRECTED=0
for attempt in 1 2; do
    python3 refresh_verified_snapshot.py "$SYNC_DIR"
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        API_CORRECTED=1
        break
    fi
    if [ $attempt -lt 2 ]; then
        echo ""
        echo "⚠️  第${attempt}次失败，5秒后重试..."
        sleep 5
    fi
done

echo ""
if [ $API_CORRECTED -eq 1 ]; then
    echo "✅ sparkline/chartData 补全完成"
else
    echo "⚠️  sparkline 补全失败，跳过，使用 AI 生成数据渲染"
fi
echo ""

# ── 第2步：渲染 HTML 报告 ────────────────────────────────────
echo "📄 第2步：渲染 HTML 报告..."
echo ""

python3 render_html.py "$SYNC_DIR" "$DATE"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ HTML 渲染失败！"
    exit 1
fi

echo ""
echo "============================================================"
echo "🎉 全流程完成！"
echo "   日期：${DATE}"
echo "   报告：${SYNC_DIR}/touyanduck-${DATE}.html"
echo "   双击文件即可在浏览器中查看 🦆"
echo "============================================================"
