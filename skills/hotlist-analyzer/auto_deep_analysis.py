#!/usr/bin/env python3
"""
自动深度分析脚本 - 供Cronjob调用

这个脚本执行完整的分析流程，并生成结构化的Markdown报告
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hermes_integration import collect_and_analyze, format_for_ai_analysis


def run_auto_analysis():
    """执行自动深度分析"""
    
    # 1. 采集和分析数据
    print("🔥 正在采集全网热点数据...")
    data = collect_and_analyze(max_items=8)
    
    # 2. 生成AI分析提示词
    ai_prompt = format_for_ai_analysis(data)
    
    # 3. 保存提示词到文件（供AI读取）
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file = f"{skill_dir}/data/ai_analysis_prompt.txt"
    
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(ai_prompt)
    
    # 4. 生成结构化数据文件（供AI读取）
    report_data = {
        "timestamp": data["timestamp"],
        "summary": data["summary"],
        "priority_items": data["priority_items"][:5],  # 只取前5条
        "cross_platform": data["cross_platform"][:5],
        "analysis_ready": True
    }
    
    report_file = f"{skill_dir}/data/analysis_report_data.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    
    # 5. 输出生成的文件路径
    print(f"\n✅ 数据采集完成!")
    print(f"   平台: {data['summary']['platforms']} 个")
    print(f"   条目: {data['summary']['total_items']} 条")
    print(f"   新热点: {data['summary']['new_hotspots']} 个")
    print(f"   跨平台: {data['summary']['cross_platform']} 个")
    print(f"\n📁 生成的文件:")
    print(f"   1. {report_file}")
    print(f"   2. {prompt_file}")
    
    return report_file, prompt_file


def print_analysis_instructions():
    """输出分析指导"""
    
    instructions = """
╔══════════════════════════════════════════════════════════════════════╗
║              🔥 HotList 深度分析报告生成指导                          ║
╚══════════════════════════════════════════════════════════════════════╝

分析数据已准备就绪。请按以下步骤生成完整报告：

Step 1: 读取分析数据文件
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
读取文件：~/.hermes/skills/hotlist-analyzer/data/analysis_report_data.json

这个文件包含：
  • timestamp: 分析时间
  • summary: 数据概览（平台数、条目数、新热点数、跨平台数）
  • priority_items: 优先级热点列表（已排序，取前5条）
  • cross_platform: 跨平台热点列表（前3条）

Step 2: 选择重点热点进行深度分析
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
从 priority_items 中选择 5 条最重要热点（优先跨平台热点）

对每条热点，请进行：
  1. 使用 web_extract 提取新闻正文（如有URL）
  2. 使用 web_search 搜索背景信息（如需要）
  3. AI分析：分类、重要性、趋势、关键要点、建议

Step 3: 生成结构化报告
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
按照以下格式输出：

🔥 全网热点深度追踪报告
生成时间: [时间]

📊 数据概览
  • 覆盖平台: X 个
  • 采集条目: X 条
  • 新热点: X 个
  • 跨平台话题: X 个

🔴 重点关注（高重要性）
📌 [热点标题]
   ├─ 热度: XXX万 | 平台: XXX
   ├─ 分类: 科技/社会/娱乐/政治/经济/体育/国际
   ├─ 重要性: 🔴 高（说明原因）
   ├─ 趋势: 持续发酵/短期热点/快速消退
   ├─ 关键要点:
   │   • 要点1
   │   • 要点2
   │   • 要点3
   └─ 建议: [具体建议]

🟡 适度关注（中重要性）
[同上格式]

🟢 了解即可（低重要性）
[同上格式]

🌐 跨平台分析
分析跨平台热点的特征和不同平台关注角度

💡 综合建议
✅ 立即关注: ...
✅ 持续跟踪: ...

⏰ 下次更新: 2小时后
"""
    
    print(instructions)


if __name__ == "__main__":
    # 运行自动分析
    report_file, prompt_file = run_auto_analysis()
    
    # 输出分析指导
    print_analysis_instructions()
    
    print(f"\n✅ 分析数据准备完成!")
    print(f"   报告数据: {report_file}")
    print(f"   AI提示词: {prompt_file}")
