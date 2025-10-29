#!/bin/bash

# AI Financial Briefing 自動生成腳本
# 設定為每日早上 8:00 執行

echo "=== AI Financial Briefing 自動生成開始 ==="
echo "時間: $(date)"

# 進入專案目錄
cd "/Users/toppyhuang/Desktop/Python Code/Streamlit Project/Daily AI Financial Briefing"

# 激活虛擬環境
source .venv/bin/activate

# 執行簡報生成
echo "開始生成簡報..."
python3 "Daily AI Financial Briefing.py"

# 檢查執行結果
if [ $? -eq 0 ]; then
    echo "✅ 簡報生成成功"
    echo "生成的文件:"
    ls -la "Daily AI Financial Briefing.txt" "Daily AI Financial Briefing.md" "source_distribution.png" 2>/dev/null || echo "某些文件可能不存在"
else
    echo "❌ 簡報生成失敗"
fi

echo "=== 自動生成完成 ==="
echo "時間: $(date)"
echo ""
