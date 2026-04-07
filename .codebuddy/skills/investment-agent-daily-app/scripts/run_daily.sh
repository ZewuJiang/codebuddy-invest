#!/bin/bash
# ============================================================
# 投研鸭小程序 — 每日数据更新串联脚本 v3.0（AkShare 替代 yfinance）
# 执行顺序：JSON语法校验 → sparkline/chartData 历史序列补全（软依赖） → 上传云数据库
#
# 用法（AI 直接调用，无需用户手动操作）：
#   bash run_daily.sh [YYYY-MM-DD]
#   日期参数可选，默认取今天（北京时间）
#
# 【方案A 架构说明】：
#   AI + 搜索轨（主轨）：负责所有字段的生成，包括 price / change / metrics /
#     trafficLights / riskScore / riskLevel / riskAdvice / globalReaction /
#     gics / sectors / 所有文字字段等。AI 从 Google Finance / OilPrice.com /
#     FRED / web_search 等直接行情源采集，准确性由 RULE ZERO-A 独立保障。
#
#   脚本补全轨（refresh_verified_snapshot.py v3.0）：
#     只负责两个数组字段：sparkline（7天）/ chartData（30天）。
#     数据源：AkShare 新浪源（主）+ 东方财富源（fallback），替代已被 403 封禁的 yfinance。
#     只补 markets.json 和 watchlist.json。
#     briefing.json / radar.json 完全不读取、不修改。
#     任何标的失败 → 跳过该标的，不阻断整体流程。
#
# 【依赖层级】：
#   第0步（JSON语法校验）：硬依赖，失败则阻断
#   第1步（sparkline补全）：软依赖，失败时跳过，直接上传 AI 生成数据
#   第2步（上传云数据库）：硬依赖，失败则保留本地文件
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)/workflows/investment_agent_data/miniapp_sync"

# 日期参数（默认今天北京时间）
DATE="${1:-$(date +%Y-%m-%d)}"

echo "============================================================"
echo "🦆 投研鸭小程序每日数据更新 — ${DATE}"
echo "============================================================"
echo ""

# ── 第0步：JSON 语法预校验 ────────────────────────────────────
echo "🔍 第0步：JSON 语法校验（确保 AI 生成的 4 个文件合法）..."
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
        echo "  ❌ JSON 语法错误: $f（请检查 AI 生成的内容）"
        JSON_OK=0
    else
        echo "  ✅ $f"
    fi
done

if [ "$JSON_OK" -ne 1 ]; then
    echo ""
    echo "❌ JSON 语法校验失败，请修复上述文件后重新运行。"
    exit 1
fi

echo ""
echo "✅ JSON 语法校验通过"
echo ""

# ── 第1步：sparkline/chartData 历史序列补全（软依赖 — 失败时警告并跳过，不阻断） ─
echo "📡 第1步：sparkline / chartData 历史序列补全（AkShare 新浪源 + 东方财富 fallback）..."
echo "   目标字段：markets.json + watchlist.json 的 sparkline（7天）/ chartData（30天）"
echo "   不覆盖：price / change / metrics / trafficLights / 任何文字字段"
echo "   模式：软依赖（失败时使用 AI 生成的原始数据上传，不阻断全流程）"
echo ""

cd "$SCRIPT_DIR"

API_CORRECTED=0

# 最多重试2次（应对 AkShare 偶发限流）
for attempt in 1 2; do
    python3 refresh_verified_snapshot.py
    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        API_CORRECTED=1
        break
    fi
    if [ $attempt -lt 2 ]; then
        echo ""
        echo "⚠️  第${attempt}次校正失败，5秒后重试..."
        sleep 5
    fi
done

echo ""
if [ $API_CORRECTED -eq 1 ]; then
    echo "✅ sparkline/chartData 补全完成（markets.json + watchlist.json 已更新真实历史序列）"
else
    echo "⚠️  sparkline/chartData 补全失败（已重试2次），跳过补全步骤，使用 AI 生成数据上传"
    echo "   常见原因：网络超时 / AkShare 新浪源+东方财富源均限流"
    echo "   影响范围：sparkline/chartData 为 AI 估算值；price/change/metrics 由 AI 采集，准确性独立保障"
    echo "   可事后手动补跑：python3 refresh_verified_snapshot.py && python3 upload_to_cloud.py \"$SYNC_DIR\" \"$DATE\""
fi
echo ""

# ── 第2步：上传到微信云数据库 ──────────────────────────────────
echo "☁️  第2步：上传校正后的 JSON 到微信云数据库..."
echo ""

python3 upload_to_cloud.py "$SYNC_DIR" "$DATE"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ 上传失败！JSON 文件已保留在本地，可手动重传："
    echo "   python3 upload_to_cloud.py \"$SYNC_DIR\" \"$DATE\""
    exit 1
fi

echo ""

# ── 第3步：同步到公开 API（本地打包 + 远程上传供 ClawHub Skill 消费） ──
echo "🌐 第3步：同步 JSON 到公开 API（AnyDev 服务器）..."
echo ""

bash "$SCRIPT_DIR/sync_to_edgeone.sh" "$DATE"
SYNC_EXIT=$?

echo ""

# ── 总结 ─────────────────────────────────────────────────────
echo "============================================================"
if [ $API_CORRECTED -eq 1 ]; then
    echo "🎉 全流程完成！大老板刷新小程序即可看到最新数据"
    echo "   日期：${DATE}"
    echo "   数据来源：AI 采集（price/change/metrics/trafficLights/文字）+ AkShare（sparkline/chartData）"
else
    echo "🎉 全流程完成（sparkline补全已跳过）！大老板刷新小程序即可看到最新数据"
    echo "   日期：${DATE}"
    echo "   数据来源：AI 采集（全量）| sparkline/chartData 为 AI 估算值（非真实历史序列）"
    echo "   建议：网络恢复后可手动补跑 refresh_verified_snapshot.py 提升 sparkline 精度"
fi
if [ $SYNC_EXIT -eq 0 ]; then
    echo "   🌐 公开 API 本地数据已同步 + 上传包已准备（需 AI 推送到 AnyDev 服务器）"
    echo "   📌 远程推送：AI 调用 AnyDev file_upload 上传 /tmp/touyanduck-api-latest.tar.gz"
    echo "   📌 手动验证：curl -s http://21.214.207.96:8080/api/latest/meta.json"
else
    echo "   ⚠️  公开 API 同步失败，不影响小程序数据（可手动重跑 sync_to_edgeone.sh）"
fi
echo "============================================================"
