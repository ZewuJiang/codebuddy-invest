#!/bin/bash
# ============================================================
# 投研鸭小程序 - 每4小时自动数据更新
# 只触发 touyanduck-daily（小程序JSON数据）
# 不触发 investment-agent-daily（PDF日报）
#
# 运行环境：macOS launchd（不加载 .zshrc/.bash_profile）
# 环境变量由 plist EnvironmentVariables 注入
# ============================================================

PROJECT_DIR="$HOME/Desktop/AICo/codebuddy-invest"
LOG_DIR="$PROJECT_DIR/logs"
mkdir -p "$LOG_DIR"

# ============================================================
# 互斥锁：防止多个实例并发执行
# ============================================================
LOCK_FILE="$LOG_DIR/.app-sync.lock"

# 检查是否已有实例在运行
if [ -f "$LOCK_FILE" ]; then
    OLD_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        echo "[$(date)] ⚠️ 已有实例在运行 (PID=$OLD_PID)，跳过本次执行" >> "$LOG_DIR/app-sync-skipped.log"
        exit 0
    else
        # 锁文件存在但进程已不在，清理旧锁
        rm -f "$LOCK_FILE"
    fi
fi

# 写入当前 PID 作为锁
echo $$ > "$LOCK_FILE"

# 确保退出时清理锁文件和子进程
cleanup() {
    rm -f "$LOCK_FILE"
    # 如果 codebuddy 子进程还在运行，也一并终止
    if [ -n "$CMD_PID" ] && kill -0 "$CMD_PID" 2>/dev/null; then
        kill -TERM "$CMD_PID" 2>/dev/null
    fi
}
trap cleanup EXIT INT TERM

TODAY=$(date +%Y-%m-%d)
NOW=$(date +%Y%m%d-%H%M)
LOG_FILE="$LOG_DIR/app-sync-${NOW}.log"

echo "========================================" >> "$LOG_FILE"
echo "开始执行: $(date)" >> "$LOG_FILE"
echo "环境: PATH=$PATH" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

cd "$PROJECT_DIR"

# 加载 nvm（launchd 环境不会自动加载 nvm，必须显式引入）
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 验证 codebuddy 可用
CODEBUDDY_BIN=$(which codebuddy 2>/dev/null)
if [ -z "$CODEBUDDY_BIN" ]; then
    echo "❌ codebuddy 未找到！当前 PATH: $PATH" >> "$LOG_FILE"
    echo "尝试直接使用 nvm node bin 路径..." >> "$LOG_FILE"
    CODEBUDDY_BIN="$HOME/.nvm/versions/node/v22.15.0/bin/codebuddy"
    if [ ! -f "$CODEBUDDY_BIN" ] && [ ! -L "$CODEBUDDY_BIN" ]; then
        echo "❌ 备用路径也不存在: $CODEBUDDY_BIN" >> "$LOG_FILE"
        exit 1
    fi
fi
echo "✅ codebuddy 路径: $CODEBUDDY_BIN" >> "$LOG_FILE"

# macOS 无 GNU timeout，用后台进程+轮询实现超时控制
# v10.0 全量模式（Standard）实测需要 ~15-25分钟，网络慢时可能更长
# 超时设为7200秒（2小时），留足余量避免误杀
"$CODEBUDDY_BIN" -p \
  "投研鸭小程序 app 内容和数据更新，日期为${TODAY}，执行 touyanduck-daily Skill 全流程" \
  -y \
  --output-format json \
  >> "$LOG_FILE" 2>&1 &
CMD_PID=$!

# 等待最多7200秒（2小时）
TIMEOUT=7200
ELAPSED=0
while kill -0 "$CMD_PID" 2>/dev/null; do
    if [ "$ELAPSED" -ge "$TIMEOUT" ]; then
        echo "⚠️ 执行超时（${TIMEOUT}秒=2小时），强制终止 PID=$CMD_PID" >> "$LOG_FILE"
        kill -TERM "$CMD_PID" 2>/dev/null
        sleep 2
        kill -9 "$CMD_PID" 2>/dev/null
        break
    fi
    sleep 5
    ELAPSED=$((ELAPSED + 5))
done

wait "$CMD_PID" 2>/dev/null
EXIT_CODE=$?

echo "========================================" >> "$LOG_FILE"
echo "执行结束: $(date), 退出码: $EXIT_CODE, 耗时: ${ELAPSED}秒" >> "$LOG_FILE"
echo "========================================" >> "$LOG_FILE"

# 清理30天前旧日志
find "$LOG_DIR" -name "app-sync-*.log" -mtime +30 -delete 2>/dev/null
# 清理 launchd 追加日志（超过 10MB 时截断保留最后 1000 行）
for logfile in "$LOG_DIR"/launchd-appsync*.log; do
    if [ -f "$logfile" ] && [ "$(stat -f%z "$logfile" 2>/dev/null || echo 0)" -gt 10485760 ]; then
        tail -1000 "$logfile" > "${logfile}.tmp" && mv "${logfile}.tmp" "$logfile"
        echo "[$(date)] 日志已截断（>10MB）" >> "$logfile"
    fi
done

exit $EXIT_CODE
