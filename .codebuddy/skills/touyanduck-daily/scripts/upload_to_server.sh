#!/bin/bash
# ============================================================
# upload_to_server.sh — 投研鸭数据上传到自建服务器 v1.0
#
# 用途：将 4 个 JSON 文件通过 scp 上传到腾讯云轻量服务器
#       替代原 upload_to_cloud.py（微信云开发，已到期）
#
# 服务器信息：
#   IP:   119.91.74.175（腾讯云轻量，广州，到期 2026-07-08）
#   用户: root
#   目标: /www/wwwroot/miniapp.touyanduck.com/api/
#   域名: https://miniapp.touyanduck.com/api/
#
# 用法：
#   bash upload_to_server.sh <JSON文件目录> [日期YYYY-MM-DD]
#
# 依赖：
#   - SSH 密钥免密登录（建议执行 ssh-copy-id root@119.91.74.175 提前配置）
#   - scp 命令（macOS 系统自带）
# ============================================================

SYNC_DIR="${1:-$(pwd)}"
DATE="${2:-$(date +%Y-%m-%d)}"

SERVER_USER="root"
SERVER_HOST="119.91.74.175"
SERVER_DIR="/www/wwwroot/miniapp.touyanduck.com/api"
VERIFY_BASE="https://miniapp.touyanduck.com/api"
SSH_KEY="$HOME/.ssh/touyanduck_server"

echo "============================================================"
echo "📤 投研鸭 — 上传 JSON 到自建服务器"
echo "   日期：$DATE"
echo "   来源：$SYNC_DIR"
echo "   目标：$SERVER_USER@$SERVER_HOST:$SERVER_DIR"
echo "============================================================"
echo ""

# ── 检查本地文件是否存在 ──────────────────────────────────────
ALL_OK=1
for f in briefing.json markets.json watchlist.json radar.json; do
    FPATH="$SYNC_DIR/$f"
    if [ ! -f "$FPATH" ]; then
        echo "❌ 本地文件不存在: $FPATH"
        ALL_OK=0
    else
        SIZE=$(wc -c < "$FPATH" | tr -d ' ')
        echo "  ✅ $f（${SIZE} bytes）"
    fi
done

if [ "$ALL_OK" -ne 1 ]; then
    echo ""
    echo "❌ 部分文件缺失，上传中止。"
    exit 1
fi

echo ""
echo "📡 开始上传..."
echo ""

# ── scp 上传（超时15秒，失败立即报错）────────────────────────
scp -i "$SSH_KEY" -o ConnectTimeout=15 -o StrictHostKeyChecking=no \
    "$SYNC_DIR/briefing.json" \
    "$SYNC_DIR/markets.json" \
    "$SYNC_DIR/watchlist.json" \
    "$SYNC_DIR/radar.json" \
    "$SERVER_USER@$SERVER_HOST:$SERVER_DIR/"

SCP_EXIT=$?

if [ $SCP_EXIT -ne 0 ]; then
    echo ""
    echo "❌ scp 上传失败（退出码=$SCP_EXIT）"
    echo ""
    echo "可能原因："
    echo "  1. SSH 未配置免密登录 → 执行：ssh-copy-id root@$SERVER_HOST"
    echo "  2. 服务器目录不存在 → SSH 登录后执行：mkdir -p $SERVER_DIR"
    echo "  3. 网络超时 → 稍后重试"
    echo ""
    echo "手动重传命令："
    echo "  scp $SYNC_DIR/{briefing,markets,watchlist,radar}.json $SERVER_USER@$SERVER_HOST:$SERVER_DIR/"
    exit 1
fi

echo ""
echo "✅ scp 上传完成，开始验证..."
echo ""

# ── 验证：通过 HTTPS 访问接口确认文件可访问 ────────────────────
VERIFY_OK=1
for name in briefing markets watchlist radar; do
    URL="$VERIFY_BASE/${name}.json"
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$URL")
    if [ "$HTTP_CODE" = "200" ]; then
        echo "  ✅ $name.json → HTTP $HTTP_CODE"
    else
        echo "  ❌ $name.json → HTTP $HTTP_CODE（URL: $URL）"
        VERIFY_OK=0
    fi
done

echo ""
if [ "$VERIFY_OK" -eq 1 ]; then
    echo "============================================================"
    echo "🎉 上传完成！小程序下次启动将自动读取最新数据。"
    echo "   验证地址：$VERIFY_BASE/briefing.json"
    echo "============================================================"
    exit 0
else
    echo "⚠️  部分接口验证失败，请检查 Nginx 配置或文件权限。"
    echo "   可在服务器上执行：chmod 644 $SERVER_DIR/*.json"
    exit 1
fi
