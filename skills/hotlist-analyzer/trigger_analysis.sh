#!/bin/bash
# 触发深度热点分析
# 使用方法: ./trigger_analysis.sh

echo "🔥 触发全网热点深度智能分析..."
echo ""

# 执行数据采集
cd ~/.hermes/skills/hotlist-analyzer
python3 auto_deep_analysis.py

echo ""
echo "✅ 数据采集完成!"
echo "📁 数据文件已生成:"
echo "   - data/analysis_report_data.json"
echo "   - data/ai_analysis_prompt.txt"
echo ""
echo "💡 现在你可以:"
echo "   1. 读取数据文件查看热点数据"
echo "   2. 对重点热点进行深度分析"
echo "   3. 生成完整的分析报告"
