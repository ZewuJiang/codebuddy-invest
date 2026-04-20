#!/bin/bash
# ============================================================
# 投研鸭小程序 — 每日数据更新串联脚本 v6.0（Harness v9.0）
# 执行顺序：JSON语法校验 → auto_compute.py公式计算 → validate.py自动化校验(35+项) → sparkline补全 → 上传 → 同步API
#
# 用法：bash run_daily.sh [YYYY-MM-DD] [--skip-warn]
#
# 【v9.0 改动】：
#   - 新增第0.3步：auto_compute.py 自动计算公式字段
#   - 模式检测简化：只有 standard / weekend 两档（去掉 refresh）
#   - validate.py v3.0：去掉 refresh 分支
#
# 【校验双级机制 v2.0】：
#   FATAL 级（R2/R3/R9）：不可绕过，必须修复（--skip-warn 无效）
#   WARN 级（其他）：可用 --skip-warn 紧急跳过
#
# 【依赖层级】：
#   第0步（JSON语法校验）：硬依赖
#   第0.3步（auto_compute.py）：硬依赖（公式自动计算）
#   第0.5步（validate.py）：硬依赖（FATAL 不可跳过 / WARN 可用 --skip-warn 跳过）
#   第1步（sparkline补全）：软依赖，失败不阻断
#   第2步（上传云数据库）：硬依赖
#   第3步（同步公开API）：软依赖
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYNC_DIR="$(cd "$SCRIPT_DIR/../../../.." && pwd)/workflows/investment_agent_data/miniapp_sync"

# 日期参数（默认今天北京时间）
DATE="${1:-$(date +%Y-%m-%d)}"

# --skip-warn 仅跳过 WARN 级校验，FATAL 级永远执行
SKIP_WARN=0
for arg in "$@"; do
    if [ "$arg" = "--skip-warn" ]; then
        SKIP_WARN=1
    fi
    # 向后兼容：旧的 --skip-validate 映射到 --skip-warn
    if [ "$arg" = "--skip-validate" ]; then
        SKIP_WARN=1
        echo "⚠️  --skip-validate 已废弃，已自动映射为 --skip-warn（FATAL 级校验仍然执行）"
    fi
done

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

# ── 第0.3步：公式字段自动计算（Harness v9.0 新增） ──────────────
echo "🔧 第0.3步：公式字段自动计算（auto_compute.py v1.0）..."
echo "   自动计算：trafficLights.status / riskScore / riskLevel / sentimentLabel / metrics联动"
echo ""

python3 "$SCRIPT_DIR/auto_compute.py" "$SYNC_DIR"
COMPUTE_EXIT=$?

if [ $COMPUTE_EXIT -ne 0 ]; then
    echo ""
    echo "⚠️  auto_compute.py 执行异常（退出码=$COMPUTE_EXIT），但不阻断流程"
    echo ""
fi

# ── 第0.5步：数据质量自动化校验（FATAL/WARN 双级） ──────────
echo "🔍 第0.5步：数据质量自动化校验（validate.py v3.0 — 35+ 项 FATAL/WARN 双级门禁）..."
echo ""

# 模式检测：根据星期几判断（v9.0 简化：只有 standard / weekend）
DAY_OF_WEEK=$(date +%u)
if [ "$DAY_OF_WEEK" -ge 6 ]; then
    VALIDATE_MODE="weekend"
else
    VALIDATE_MODE="standard"
fi

python3 "$SCRIPT_DIR/validate.py" "$SYNC_DIR" --mode "$VALIDATE_MODE"
VALIDATE_EXIT=$?

if [ $VALIDATE_EXIT -eq 3 ]; then
    # FATAL 级错误 — 不可绕过
    echo ""
    echo "🚫 存在 FATAL 级错误！必须修复后才能继续（--skip-warn 无法绕过 FATAL）。"
    echo "   FATAL 项（R2/R3/R9）涉及聪明钱持仓数据完整性，请检查 holdings-cache.json 并修复。"
    exit 1
elif [ $VALIDATE_EXIT -eq 1 ]; then
    # 仅 WARN 级错误
    if [ $SKIP_WARN -eq 1 ]; then
        echo ""
        echo "⚠️  存在 WARN 级错误，已通过 --skip-warn 跳过（FATAL 级已确认通过）"
        echo ""
    else
        echo ""
        echo "❌ 数据质量校验未通过！请根据上方报告修复后重新运行。"
        echo "   💡 提示：修复 JSON 文件中的问题后，重新执行 run_daily.sh 即可。"
        echo "   ⏭️ 若需跳过 WARN 级校验（仅限紧急情况）：bash run_daily.sh $DATE --skip-warn"
        echo "   📌 注意：FATAL 级错误（R2/R3/R9）无法跳过，必须修复。"
        exit 1
    fi
elif [ $VALIDATE_EXIT -eq 0 ]; then
    echo ""
    echo "✅ 数据质量校验全部通过（含 FATAL 级）"
    echo ""
fi

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

# ── 第1.5步：强制刷新 _meta.generatedAt（确保前端时间显示准确）────
# 【设计说明】此步骤是 shell 层硬保障，不依赖 AI 行为，无论何种模型/跳过何种步骤，
#            upload 前 generatedAt 必被更新为当前执行时间。
echo "🕐 第1.5步：强制刷新 _meta.generatedAt 为当前时间..."
echo ""

python3 -c "
import json, os
from datetime import datetime, timezone, timedelta

sync_dir = '$SYNC_DIR'
bjt = timezone(timedelta(hours=8))
now_val = datetime.now(bjt).strftime('%Y-%m-%dT%H:%M:%S+08:00')

for fname in ['briefing.json', 'markets.json', 'watchlist.json', 'radar.json']:
    fpath = os.path.join(sync_dir, fname)
    if not os.path.exists(fpath):
        print(f'  ⚠️  {fname} 不存在，跳过')
        continue
    with open(fpath, 'r', encoding='utf-8') as f:
        d = json.load(f)
    meta = d.get('_meta')
    if meta is None:
        d['_meta'] = {}
        meta = d['_meta']
    old = meta.get('generatedAt', '')
    meta['generatedAt'] = now_val
    with open(fpath, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
    print(f'  ✅ {fname}: {old!r} → {now_val!r}')
"

if [ $? -eq 0 ]; then
    echo "  ✅ 全部 _meta.generatedAt 刷新完成"
else
    echo "  ❌ generatedAt 刷新失败，请检查 JSON 文件是否完整"
    exit 1
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

# ── 第3步：同步到公开 API（本地渲染 + 准备 GitHub Pages 推送） ──
echo "🌐 第3步：同步 JSON 到公开 API（GitHub Pages）..."
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
    echo "   公式计算：auto_compute.py（riskScore/riskLevel/sentimentLabel/trafficLights.status）"
else
    echo "🎉 全流程完成（sparkline补全已跳过）！大老板刷新小程序即可看到最新数据"
    echo "   日期：${DATE}"
    echo "   数据来源：AI 采集（全量）| sparkline/chartData 为 AI 估算值（非真实历史序列）"
    echo "   公式计算：auto_compute.py（riskScore/riskLevel/sentimentLabel/trafficLights.status）"
    echo "   建议：网络恢复后可手动补跑 refresh_verified_snapshot.py 提升 sparkline 精度"
fi
if [ $SYNC_EXIT -eq 0 ]; then
    echo "   🌐 公开 API 本地数据已同步"
    echo "   📌 GitHub Pages 推送由 daily-app Skill 第4.3阶段自动完成"
    echo "   📌 手动验证: curl -s https://api.touyanduck.com/briefing.md | head -3"
else
    echo "   ⚠️  公开 API 同步失败，不影响小程序数据（可手动重跑 sync_to_edgeone.sh）"
fi
echo "============================================================"
