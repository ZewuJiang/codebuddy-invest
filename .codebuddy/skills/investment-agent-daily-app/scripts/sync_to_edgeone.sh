#!/bin/bash
# ============================================================
# 投研鸭 — 公开 API 数据同步脚本 v5.0
#
# 将 miniapp_sync/ 下的 4 个 JSON 同步到：
#   1. 本地 touyanduck-api/api/latest/（本地副本）
#   2. touyanduck-api/public/（EdgeOne Pages 静态文件）
#   3. touyanduck-api/github-pages/（GitHub Pages 最新）
#   4. touyanduck-api/github-pages/archive/{date}/（历史归档）
#   5. EdgeOne Pages KV 存储（动态 API 数据源）
#
# v5.0 变更：
#   - 新增第3.5步：同步到 github-pages/（覆盖最新）
#   - 新增第3.7步：历史归档到 github-pages/archive/{date}/
#   - 新增 archive/index.json 自动维护
#   - 依赖 generate_summary.py 生成精简摘要
#
# 用法（由 run_daily.sh 或手动调用）：
#   bash sync_to_edgeone.sh [YYYY-MM-DD]
#   日期参数可选，默认取今天
#
# 数据流：
#   miniapp_sync/*.json
#     → touyanduck-api/api/latest/*.json + meta.json（本地）
#     → touyanduck-api/public/（EdgeOne Pages 静态文件）
#     → touyanduck-api/github-pages/（GitHub Pages 最新版）
#     → touyanduck-api/github-pages/archive/{date}/（历史归档）
#     → EdgeOne Pages KV（POST /api/sync 动态数据）
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)"
SYNC_DIR="$PROJECT_DIR/workflows/investment_agent_data/miniapp_sync"
API_DIR="$PROJECT_DIR/touyanduck-api/api/latest"

# 日期参数（默认今天）
DATE="${1:-$(date +%Y-%m-%d)}"

echo "============================================================"
echo "🌐 投研鸭公开 API 数据同步 v5.0 — ${DATE}"
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

# ── 第3步：同步静态文件到 public/（EdgeOne Pages） ─────────────
echo "📦 第3步：同步静态文件到 EdgeOne Pages public/ 目录..."
PUBLIC_DIR="$PROJECT_DIR/touyanduck-api/public"
mkdir -p "$PUBLIC_DIR"

for f in briefing.json markets.json watchlist.json radar.json meta.json briefing.md; do
    SRC="$API_DIR/$f"
    if [ -f "$SRC" ]; then
        cp "$SRC" "$PUBLIC_DIR/$f"
        echo "  ✅ $f → public/$f"
    fi
done
echo ""

# ── 第3.5步：同步到 github-pages/（覆盖最新） ─────────────────
echo "📄 第3.5步：同步到 GitHub Pages（最新版覆盖）..."
GHPAGES_DIR="$PROJECT_DIR/touyanduck-api/github-pages"
mkdir -p "$GHPAGES_DIR"

for f in briefing.json markets.json watchlist.json radar.json meta.json briefing.md; do
    SRC="$API_DIR/$f"
    if [ -f "$SRC" ]; then
        cp "$SRC" "$GHPAGES_DIR/$f"
        echo "  ✅ $f → github-pages/$f"
    fi
done
echo ""

# ── 第3.7步：历史归档到 github-pages/archive/{date}/ ──────────
echo "📚 第3.7步：历史归档到 archive/${DATE}/..."
ARCHIVE_DIR="$GHPAGES_DIR/archive/${DATE}"
mkdir -p "$ARCHIVE_DIR"

# 3.7.1 复制 briefing.md 到归档
if [ -f "$API_DIR/briefing.md" ]; then
    cp "$API_DIR/briefing.md" "$ARCHIVE_DIR/briefing.md"
    echo "  ✅ briefing.md → archive/${DATE}/briefing.md"
else
    echo "  ⚠️  briefing.md 不存在，跳过归档"
fi

# 3.7.2 生成 summary.json
echo "  📝 生成 summary.json..."
python3 "$SCRIPT_DIR/generate_summary.py" "$SYNC_DIR" "$ARCHIVE_DIR" "$DATE"
SUMMARY_EXIT=$?
if [ $SUMMARY_EXIT -eq 0 ]; then
    echo "  ✅ summary.json 生成并归档完成"
else
    echo "  ⚠️  summary.json 生成失败"
fi

# 3.7.3 更新 archive/index.json
echo "  📝 更新 archive/index.json..."
INDEX_FILE="$GHPAGES_DIR/archive/index.json"

# 如果 index.json 存在，读取现有日期列表；否则创建新的
if [ -f "$INDEX_FILE" ]; then
    # 用 python 安全更新 index.json（追加日期 + 去重 + 倒序排列）
    python3 -c "
import json, sys
from datetime import datetime, timezone, timedelta

index_file = '$INDEX_FILE'
new_date = '$DATE'
bj_tz = timezone(timedelta(hours=8))
now_bj = datetime.now(bj_tz)

with open(index_file, 'r', encoding='utf-8') as f:
    index = json.load(f)

dates = index.get('dates', [])
if new_date not in dates:
    dates.append(new_date)

# 倒序排列（最新在前）
dates.sort(reverse=True)

index['latest'] = dates[0]
index['count'] = len(dates)
index['dates'] = dates
index['updatedAt'] = now_bj.strftime('%Y-%m-%dT%H:%M:%S+08:00')

with open(index_file, 'w', encoding='utf-8') as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print(f'     日期数: {len(dates)}, 最新: {dates[0]}')
"
else
    # 创建全新的 index.json
    python3 -c "
import json, os
from datetime import datetime, timezone, timedelta

ghpages_dir = '$GHPAGES_DIR'
archive_base = os.path.join(ghpages_dir, 'archive')
new_date = '$DATE'
bj_tz = timezone(timedelta(hours=8))
now_bj = datetime.now(bj_tz)

# 扫描所有已有归档目录
dates = []
if os.path.isdir(archive_base):
    for d in os.listdir(archive_base):
        dpath = os.path.join(archive_base, d)
        if os.path.isdir(dpath) and len(d) == 10 and d[4] == '-' and d[7] == '-':
            dates.append(d)

if new_date not in dates:
    dates.append(new_date)

dates.sort(reverse=True)

index = {
    'latest': dates[0],
    'count': len(dates),
    'dates': dates,
    'updatedAt': now_bj.strftime('%Y-%m-%dT%H:%M:%S+08:00')
}

index_file = os.path.join(archive_base, 'index.json')
with open(index_file, 'w', encoding='utf-8') as f:
    json.dump(index, f, ensure_ascii=False, indent=2)

print(f'     新建 index.json — 日期数: {len(dates)}, 最新: {dates[0]}')
"
fi
echo "  ✅ archive/index.json 更新完成"
echo ""

# ── 第4步：推送数据到 EdgeOne Pages KV ────────────────────────
echo "🚀 第4步：推送数据到 EdgeOne Pages KV..."
python3 "$SCRIPT_DIR/sync_to_edgeone_kv.py" "$SYNC_DIR" "$DATE"
KV_EXIT=$?

if [ $KV_EXIT -eq 0 ]; then
    echo "  ✅ EdgeOne KV 同步成功"
else
    echo "  ⚠️  EdgeOne KV 同步失败（不影响本地数据和小程序）"
fi
echo ""

# ── 第5步：推送 github-pages/ 到 GitHub Pages ─────────────────
echo "🚀 第5步：推送 GitHub Pages..."

# github-pages/ 目录本身就是 git 仓库（ZewuJiang/touyanduck-api）
if [ -d "$GHPAGES_DIR/.git" ]; then
    cd "$GHPAGES_DIR"
    git add -A
    CHANGES=$(git diff --cached --stat)
    if [ -n "$CHANGES" ]; then
        git commit -m "📊 投研鸭每日简报 ${DATE} — 含历史归档"
        git push origin main 2>/dev/null || git push origin master 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "  ✅ GitHub Pages 推送成功"
        else
            echo "  ⚠️  GitHub Pages 推送失败（请手动推送）"
        fi
    else
        echo "  ℹ️  无变更，跳过推送"
    fi
    cd "$PROJECT_DIR"
else
    echo "  ⚠️  github-pages/ 不是 git 仓库"
    echo "     请手动将 github-pages/ 内容推送到 GitHub"
    echo "     提示: cd $GHPAGES_DIR && git init && git remote add origin https://github.com/ZewuJiang/touyanduck-api.git && git push"
fi
echo ""

# ── 总结 ────────────────────────────────────────────────────
echo "============================================================"
if [ $COPY_OK -eq 1 ]; then
    echo "🎉 v5.0 数据同步完成！"
    echo ""
    echo "   📁 本地 API: $API_DIR"
    echo "   📁 EdgeOne:  $PUBLIC_DIR"
    echo "   📁 GitHub:   $GHPAGES_DIR"
    echo ""
    echo "   📚 历史归档: $GHPAGES_DIR/archive/${DATE}/"
    ls -la "$GHPAGES_DIR/archive/${DATE}/" 2>/dev/null | awk '{if(NR>1) print "      " $NF " (" $5 " bytes)"}'
    echo ""
    # 显示归档索引摘要
    if [ -f "$GHPAGES_DIR/archive/index.json" ]; then
        ARCHIVE_COUNT=$(python3 -c "import json; d=json.load(open('$GHPAGES_DIR/archive/index.json')); print(d.get('count',0))" 2>/dev/null)
        echo "   📊 归档总天数: ${ARCHIVE_COUNT:-?}"
    fi
    echo ""
    if [ $KV_EXIT -eq 0 ]; then
        echo "   ☁️  EdgeOne KV: 已同步"
    fi
else
    echo "⚠️  数据同步完成（部分文件跳过）"
    echo "   请检查源数据目录: $SYNC_DIR"
fi
echo "============================================================"
