#!/bin/bash
# 每日定时运行脚本

set -e  # 遇到错误立即退出

# 配置
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
DATE=$(date +%Y-%m-%d)
LOG_FILE="$LOG_DIR/run_$DATE.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 记录开始时间
echo "========================================" | tee -a "$LOG_FILE"
echo "Newsloom Daily Report - $DATE" | tee -a "$LOG_FILE"
echo "Started at: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 切换到项目目录
cd "$PROJECT_DIR"

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "Activating virtual environment..." | tee -a "$LOG_FILE"
    source venv/bin/activate
fi

# 运行 pipeline
echo "Running pipeline..." | tee -a "$LOG_FILE"
python3 run.py --layers fetch,filter,analyze,generate 2>&1 | tee -a "$LOG_FILE"

# 记录结束时间
echo "========================================" | tee -a "$LOG_FILE"
echo "Completed at: $(date)" | tee -a "$LOG_FILE"
echo "Log saved to: $LOG_FILE" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 清理旧日志（保留30天）
find "$LOG_DIR" -name "run_*.log" -mtime +30 -delete

echo "✅ Daily report generated successfully!"
