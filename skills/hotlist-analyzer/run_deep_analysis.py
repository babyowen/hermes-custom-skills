#!/usr/bin/env python3
"""
深度分析执行脚本 - 供Hermes调用

这个脚本在Hermes环境中执行，可以：
1. 采集热点数据
2. 使用web_search搜索背景信息
3. 使用AI进行深度分析
4. 生成综合报告
"""

import os
import sys
import json
from datetime import datetime

# 确保导入路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/ubuntu/.hermes/hermes-agent')

from storage import HotListStorage
from analyzer import HotListAnalyzer


def run_analysis_pipeline():
    """
    运行完整的分析流程
    
    这个函数会被Hermes的cronjob调用
    """
    
    print("=" * 70)
    print("🔥 HotList 智能深度分析启动")
    print("=" * 70)
    
    # Step 1: 采集数据
    print("\n📥 Step 1: 采集全网热点数据...")
    storage = HotListStorage()
    analyzer = HotListAnalyzer(storage)
    
    collected = analyzer.collect_all()
    print(f"   ✅ 采集完成: {len(collected)}个平台")
    
    # Step 2: 基础分析
    print("\n🔍 Step 2: 检测新热点和跨平台话题...")
    new_hotspots = analyzer.find_new_hotspots()
    cross_platform = analyzer.find_cross_platform_topics(min_platforms=2)
    
    print(f"   🆕 新热点: {len(new_hotspots)} 个")
    print(f"   🌐 跨平台: {len(cross_platform)} 个")
    
    # Step 3: 准备分析数据
    print("\n📊 Step 3: 准备分析数据...")
    
    # 合并热点（跨平台优先）
    priority_items = []
    seen_titles = set()
    
    # 先添加跨平台热点
    for topic in cross_platform[:5]:
        priority_items.append({
            "title": topic["main_title"],
            "platform": "跨平台",
            "platforms": topic.get("platforms", []),
            "hot": f"{topic.get('total_hot', 0)/10000:.0f}万",
            "url": topic.get("items", [{}])[0].get("url", ""),
            "type": "cross_platform"
        })
        seen_titles.add(topic["main_title"])
    
    # 添加新热点（去重）
    for hotspot in new_hotspots[:8]:
        if hotspot["title"] not in seen_titles:
            priority_items.append({
                "title": hotspot["title"],
                "platform": hotspot.get("platform", ""),
                "hot": hotspot.get("hot", ""),
                "url": hotspot.get("url", ""),
                "type": "new"
            })
    
    print(f"   📌 优先分析: {len(priority_items)} 条热点")
    
    # Step 4: 返回结构化数据（供Hermes进一步处理）
    analysis_result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "platforms": len(collected),
            "total_items": sum(len(v.get("data", [])) for v in collected.values()),
            "new_hotspots": len(new_hotspots),
            "cross_platform": len(cross_platform),
            "priority_analysis": len(priority_items)
        },
        "priority_items": priority_items,
        "new_hotspots": new_hotspots[:10],
        "cross_platform": cross_platform[:5],
        "platform_summaries": analyzer._summarize_by_platform()
    }
    
    # 保存分析数据
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = f"{skill_dir}/data/latest_analysis.json"
    
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=2)
    
    print(f"   💾 数据已保存: {data_file}")
    
    # 返回结果
    return analysis_result


def generate_ai_analysis_prompt(analysis_data: dict) -> str:
    """
    生成AI分析提示词
    
    这个提示词会被发送给LLM进行深度分析
    """
    
    # 格式化优先分析的热点
    items_text = []
    for i, item in enumerate(analysis_data.get("priority_items", []), 1):
        platforms = ", ".join(item.get("platforms", [item.get("platform", "")]))
        items_text.append(f"""
{i}. 【{item['title']}】
   平台: {platforms}
   热度: {item.get('hot', '未知')}
   链接: {item.get('url', '')}
""")
    
    prompt = f"""你是一位资深新闻分析师。请对以下{len(analysis_data.get('priority_items', []))}条热点新闻进行深度分析：

{chr(10).join(items_text)}

请完成以下分析任务：

## 1. 热点分类与重要性评估
对每个热点进行分类和重要性评估：
- 🔴 高重要性：需要立即关注，可能产生重大影响
- 🟡 中重要性：值得了解，可能持续发酵  
- 🟢 低重要性：一般信息，了解即可

格式：
1. 【标题】
   分类: 科技/社会/娱乐/政治/经济/体育/国际
   重要性: 🔴高/🟡中/🟢低
   原因: [为什么这样评估]

## 2. 关键信息提取
对每个重要热点（🔴高和🟡中），提取：
- 核心要点（3-4点）
- 涉及的关键人物、机构、地点
- 事件背景（如果 obvious）

## 3. 趋势预测
预测每个热点的后续发展：
- 持续发酵：会继续升温
- 短期热点：很快会消退
- 周期性：可能反复出现

## 4. 跨平台分析
分析为什么某些话题能在多个平台同时热门：
- 不同平台的关注角度差异
- 舆论场的发酵路径

## 5. 综合建议
- 哪些热点最值得立即关注？
- 有什么潜在影响需要警惕？
- 给出具体的关注建议

请用清晰、结构化的格式输出。
"""
    
    return prompt


def format_analysis_for_user(analysis_data: dict, ai_analysis: str = "") -> str:
    """
    格式化分析结果供用户阅读
    """
    lines = []
    
    summary = analysis_data.get("summary", {})
    
    lines.append("=" * 60)
    lines.append("🔥 全网热点智能追踪报告")
    lines.append("=" * 60)
    lines.append(f"生成时间: {analysis_data.get('timestamp', '')}")
    lines.append("")
    
    # 数据概览
    lines.append("📊 数据概览:")
    lines.append(f"  • 覆盖平台: {summary.get('platforms', 0)} 个")
    lines.append(f"  • 采集条目: {summary.get('total_items', 0)} 条")
    lines.append(f"  • 新热点: {summary.get('new_hotspots', 0)} 个")
    lines.append(f"  • 跨平台话题: {summary.get('cross_platform', 0)} 个")
    lines.append("")
    
    # 优先关注的热点
    priority_items = analysis_data.get("priority_items", [])
    if priority_items:
        lines.append("📌 重点热点TOP5:")
        for i, item in enumerate(priority_items[:5], 1):
            platforms = ", ".join(item.get("platforms", [item.get("platform", "")])[:3])
            lines.append(f"  {i}. {item['title'][:35]}...")
            lines.append(f"     📍 {platforms} | 🔥 {item.get('hot', '')}")
        lines.append("")
    
    # AI分析结果
    if ai_analysis:
        lines.append("=" * 60)
        lines.append("🤖 AI深度分析")
        lines.append("=" * 60)
        lines.append(ai_analysis)
    else:
        lines.append("💡 提示: 如需AI深度分析，请提供上述数据给AI进行分析")
    
    lines.append("")
    lines.append("=" * 60)
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 运行分析流程
    result = run_analysis_pipeline()
    
    # 生成AI提示词
    print("\n" + "=" * 70)
    print("🤖 AI分析提示词已生成（请提供给AI进行深度分析）")
    print("=" * 70)
    
    ai_prompt = generate_ai_analysis_prompt(result)
    
    # 保存提示词
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file = f"{skill_dir}/data/ai_prompt.txt"
    
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(ai_prompt)
    
    print(f"\n💾 AI提示词已保存: {prompt_file}")
    print("\n" + ai_prompt)
