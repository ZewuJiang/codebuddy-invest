#!/bin/bash
# ============================================================
# 投研鸭 — 公开 API 数据同步脚本 v2.0
#
# 将 miniapp_sync/ 下的 4 个 JSON 同步到：
#   1. 本地 touyanduck-api/api/latest/（本地副本）
#   2. AnyDev 远程服务器 /data/touyanduck-api/api/latest/（公网 API）
#
# 用法（由 run_daily.sh 或手动调用）：
#   bash sync_to_edgeone.sh [YYYY-MM-DD]
#   日期参数可选，默认取今天
#
# 数据流：
#   miniapp_sync/*.json
#     → touyanduck-api/api/latest/*.json + meta.json（本地）
#     → 打包 tar.gz → AnyDev file_upload → webshell 解压（远程）
#     → http://21.214.207.96:8080/api/latest/ 公网可访问
#
# 远程同步说明：
#   本脚本负责本地渲染（render_briefing.py）+ 打包（tar.gz）。
#   AnyDev 远程上传（file_upload + webshell 解压）由 daily-app SKILL.md
#   第4.3阶段统一调用，手动运行本脚本时仅执行本地部分（第0.5-3步）。
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SYNC_DIR="$PROJECT_DIR/workflows/investment_agent_data/miniapp_sync"
API_DIR="$PROJECT_DIR/touyanduck-api/api/latest"

# AnyDev 远程服务器配置
REMOTE_IP="21.214.207.96"
REMOTE_API_DIR="/data/touyanduck-api/api/latest"
REMOTE_PORT=8080

# 日期参数（默认今天）
DATE="${1:-$(date +%Y-%m-%d)}"

echo "============================================================"
echo "🌐 投研鸭公开 API 数据同步 v2.0 — ${DATE}"
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

# ── 第3步：打包用于远程上传的 tar.gz ──────────────────────────
echo "📦 第3步：打包 API 数据用于远程同步..."

UPLOAD_ARCHIVE="/tmp/touyanduck-api-latest.tar.gz"
cd "$API_DIR"
tar -czf "$UPLOAD_ARCHIVE" briefing.json markets.json watchlist.json radar.json meta.json briefing.md 2>/dev/null

if [ $? -eq 0 ]; then
    ARCHIVE_SIZE=$(du -k "$UPLOAD_ARCHIVE" | cut -f1)
    echo "  ✅ 打包完成: $UPLOAD_ARCHIVE (${ARCHIVE_SIZE}KB)"
    echo ""
    echo "  📌 远程同步提示："
    echo "     本脚本已准备好上传包: $UPLOAD_ARCHIVE"
    echo "     远程目标: ${REMOTE_IP}:${REMOTE_PORT} → ${REMOTE_API_DIR}/"
    echo "     上传方式: 由 CodeBuddy AI 通过 AnyDev Integration API 自动完成"
    echo "     手动验证: curl -s http://${REMOTE_IP}:${REMOTE_PORT}/api/latest/meta.json"
else
    echo "  ⚠️  打包失败，远程同步跳过（本地数据已更新）"
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
    echo "   🌐 备用 API: http://${REMOTE_IP}:${REMOTE_PORT}/api/latest/ (AnyDev 内网)"
    echo "   📦 上传包: $UPLOAD_ARCHIVE（等待 AI 推送到 AnyDev 服务器）"
else
    echo "⚠️  数据同步完成（部分文件跳过）"
    echo "   请检查源数据目录: $SYNC_DIR"
fi
echo "============================================================"
