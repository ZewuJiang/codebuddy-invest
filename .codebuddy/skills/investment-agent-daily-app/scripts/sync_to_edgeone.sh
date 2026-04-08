#!/bin/bash
# ============================================================
# 投研鸭 — 公开 API 数据同步脚本 v3.0
#
# 将 miniapp_sync/ 下的 4 个 JSON 同步到：
#   1. 本地 touyanduck-api/api/latest/（本地副本）
#   2. GitHub Pages（公网 HTTPS 端点）
#
# 用法（由 run_daily.sh 或手动调用）：
#   bash sync_to_edgeone.sh [YYYY-MM-DD]
#   日期参数可选，默认取今天
#
# 数据流：
#   miniapp_sync/*.json
#     → touyanduck-api/api/latest/*.json + meta.json（本地）
#     → 复制到 github-pages/ → git push → GitHub Pages 自动更新
#     → https://zewujiang.github.io/touyanduck-api/ 全球可访问
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SYNC_DIR="$PROJECT_DIR/workflows/investment_agent_data/miniapp_sync"
API_DIR="$PROJECT_DIR/touyanduck-api/api/latest"

# 日期参数（默认今天）
DATE="${1:-$(date +%Y-%m-%d)}"

echo "============================================================"
echo "🌐 投研鸭公开 API 数据同步 v3.0 — ${DATE}"
echo "============================================================"
echo ""

# ── 第0.5步：渲染 Markdown 简报 ──────────────────────────────
echo "📝 第0.5步：渲染 briefing.md（JSON → Markdown）..."
python3 "$SCRIPT_DIR/render_briefing.py" "$SYNC_DIR" "$PROJECT_DIR/touyanduck-api/api/latest/briefing.md"
RENDER_EXIT=$?
if [ $RENDER_EXIT -eq 0 ]; then
    echo "  ✅ briefing.md 渲染成功"
else
    echo "  ⚠️  briefing.md 渲染失败（不影响 JSON 同步）"
fi
echo ""

# ── 第1步：检查源文件 + JSON 校验 ──────────────────────────────
if [ ! -d "$SYNC_DIR" ]; then
    echo "❌ 源数据目录不存在: $SYNC_DIR"
    exit 1
fi

mkdir -p "$API_DIR"

echo "📋 第1步：复制 JSON 到本地 API 目录..."
echo ""

COPY_OK=1
for f in briefing.json markets.json watchlist.json radar.json; do
    SRC="$SYNC_DIR/$f"
    DST="$API_DIR/$f"

    if [ ! -f "$SRC" ]; then
        echo "  ⚠️  源文件不存在: $f，跳过"
        COPY_OK=0
        continue
    fi

    python3 -m json.tool "$SRC" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "  ❌ JSON 语法错误: $f，跳过（不覆盖已有数据）"
        COPY_OK=0
        continue
    fi

    cp "$SRC" "$DST"
    SIZE=$(du -k "$SRC" | cut -f1)
    echo "  ✅ $f → api/latest/$f (${SIZE}KB)"
done

echo ""

# ── 第2步：生成 meta.json ─────────────────────────────────────
echo "📝 第2步：生成 meta.json..."
python3 "$SCRIPT_DIR/generate_meta.py" "$DATE" "$API_DIR"

if [ $? -ne 0 ]; then
    echo "  ❌ meta.json 生成失败"
    exit 1
fi

echo ""

# ── 总结 ────────────────────────────────────────────────────
echo "============================================================"
if [ $COPY_OK -eq 1 ]; then
    echo "🎉 本地 API 数据同步完成！"
    echo "   本地目录: $API_DIR"
    echo "   文件列表:"
    ls -la "$API_DIR"/*.json 2>/dev/null | awk '{print "     " $NF " (" $5 " bytes)"}'
    echo ""
    echo "   🌐 公网 API: https://zewujiang.github.io/touyanduck-api/ (GitHub Pages)"
    echo "   📌 下一步：复制到 github-pages/ 并 git push"
else
    echo "⚠️  数据同步完成（部分文件跳过）"
    echo "   请检查源数据目录: $SYNC_DIR"
fi
echo "============================================================"
