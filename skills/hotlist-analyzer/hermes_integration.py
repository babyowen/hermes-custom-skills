#!/usr/bin/env python3
"""
Hermes集成模块
供Hermes Agent调用，可以使用所有工具（web_search, AI等）

使用方法：
1. Hermes调用 collect_and_analyze() 获取热点数据
2. Hermes使用AI分析数据
3. Hermes调用 search_background() 搜索背景信息
4. Hermes生成最终报告
"""

import os
import sys
import json
from typing import List, Dict, Optional
from datetime import datetime

# 确保导入路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage import HotListStorage
from analyzer import HotListAnalyzer


def collect_and_analyze(max_items: int = 10) -> Dict:
    """
    采集并分析热点数据
    
    这个函数由Hermes调用，返回结构化的热点数据
    
    Returns:
        {
            "timestamp": "...",
            "summary": {...},
            "priority_items": [...],  # 需要深度分析的热点
            "all_hotspots": [...],     # 所有热点
            "cross_platform": [...]    # 跨平台热点
        }
    """
    print("🔥 开始采集全网热点数据...")
    
    storage = HotListStorage()
    analyzer = HotListAnalyzer(storage)
    
    # 1. 采集数据
    collected = analyzer.collect_all()
    
    # 2. 基础分析
    new_hotspots = analyzer.find_new_hotspots()
    cross_platform = analyzer.find_cross_platform_topics(min_platforms=2)
    
    print(f"\n✅ 采集完成:")
    print(f"   平台: {len(collected)} 个")
    print(f"   新热点: {len(new_hotspots)} 个")
    print(f"   跨平台: {len(cross_platform)} 个")
    
    # 3. 选择优先分析的热点
    priority_items = []
    seen = set()
    
    # 跨平台热点（优先级高）
    for topic in cross_platform[:5]:
        priority_items.append({
            "title": topic["main_title"],
            "platform": f"跨平台({topic.get('platform_count', 0)}个)",
            "platforms": topic.get("platforms", []),
            "hot": f"{topic.get('total_hot', 0)/10000:.0f}万",
            "url": topic.get("items", [{}])[0].get("url", ""),
            "type": "cross_platform",
            "platform_details": topic.get("items", [])
        })
        seen.add(topic["main_title"])
    
    # 新热点
    for hotspot in new_hotspots[:max_items]:
        if hotspot["title"] not in seen:
            priority_items.append({
                "title": hotspot["title"],
                "platform": hotspot.get("platform", ""),
                "hot": hotspot.get("hot", ""),
                "url": hotspot.get("url", ""),
                "rank": hotspot.get("rank", 0),
                "type": "new"
            })
    
    result = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "platforms": len(collected),
            "total_items": sum(len(v.get("data", [])) for v in collected.values()),
            "new_hotspots": len(new_hotspots),
            "cross_platform": len(cross_platform),
            "priority_analysis": len(priority_items)
        },
        "priority_items": priority_items[:max_items],
        "new_hotspots": new_hotspots,
        "cross_platform": cross_platform,
        "platform_summaries": analyzer._summarize_by_platform()
    }
    
    # 保存数据
    _save_data(result)
    
    return result


def format_for_ai_analysis(data: Dict) -> str:
    """
    格式化数据为AI分析提示词
    
    这个提示词可以直接发送给LLM进行深度分析
    """
    
    items = data.get("priority_items", [])
    
    items_text = []
    for i, item in enumerate(items, 1):
        platforms = ", ".join(item.get("platforms", [item.get("platform", "")]))
        items_text.append(f"""
{i}. 【{item['title']}】
   平台: {platforms}
   热度: {item.get('hot', '未知')}
   链接: {item.get('url', '')}
""")
    
    prompt = f"""作为资深新闻分析师，请对以下{len(items)}条热点进行深度分析：

{chr(10).join(items_text)}

请提供：

## 📊 热点分类与重要性
每条热点的分类（科技/社会/娱乐/政治/经济/体育/国际）和重要性（🔴高/🟡中/🟢低），并说明原因

## 🔍 关键信息提取  
重要热点的核心要点、关键人物/机构/地点

## 📈 趋势预测
预测哪些热点会持续发酵，哪些是短期热点

## 🌐 跨平台分析
分析多平台热点的舆论发酵路径

## 💡 关注建议
给出具体的关注建议和潜在影响提示

请用结构化、易读的格式输出。
"""
    
    return prompt


def extract_content_for_analysis(item: Dict) -> str:
    """
    提取单条热点的正文内容（供AI分析使用）
    
    注意：这个函数在Hermes环境中可以使用web_extract工具
    """
    url = item.get("url", "")
    if not url:
        return ""
    
    # 这里只是一个占位，实际的提取应该在Hermes环境中使用web_extract
    return f"[正文待提取: {url}]"


def generate_search_queries(items: List[Dict]) -> List[str]:
    """
    生成背景搜索查询词
    
    基于热点标题生成搜索关键词，用于搜索背景信息
    """
    queries = []
    
    for item in items[:5]:  # 最多5条
        title = item.get("title", "")
        
        # 基础查询
        queries.append(title)
        
        # 如果是跨平台热点，添加"为什么"查询
        if item.get("type") == "cross_platform":
            queries.append(f"{title[:20]} 原因")
        
        # 添加时间限制（最近）
        queries.append(f"{title} 2026")
    
    # 去重
    unique_queries = list(set(queries))
    return unique_queries[:10]


def compile_final_report(data: Dict, ai_analysis: str = "", 
                        background_info: str = "") -> str:
    """
    编译最终报告
    
    整合所有分析结果生成最终报告
    """
    lines = []
    
    summary = data.get("summary", {})
    timestamp = data.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    # 报告头部
    lines.append("=" * 70)
    lines.append("🔥 全网热点智能追踪深度报告")
    lines.append("=" * 70)
    lines.append(f"生成时间: {timestamp}")
    lines.append("")
    
    # 数据概览
    lines.append("📊 数据概览")
    lines.append("-" * 70)
    lines.append(f"  • 覆盖平台: {summary.get('platforms', 0)} 个")
    lines.append(f"  • 采集条目: {summary.get('total_items', 0)} 条")
    lines.append(f"  • 新发现热点: {summary.get('new_hotspots', 0)} 个")
    lines.append(f"  • 跨平台话题: {summary.get('cross_platform', 0)} 个")
    lines.append("")
    
    # AI分析结果
    if ai_analysis:
        lines.append("=" * 70)
        lines.append("🤖 AI深度分析")
        lines.append("=" * 70)
        lines.append(ai_analysis)
        lines.append("")
    
    # 背景信息
    if background_info:
        lines.append("=" * 70)
        lines.append("📚 背景信息补充")
        lines.append("=" * 70)
        lines.append(background_info)
        lines.append("")
    
    # 重点热点列表
    priority_items = data.get("priority_items", [])
    if priority_items:
        lines.append("=" * 70)
        lines.append("📌 重点热点详情")
        lines.append("=" * 70)
        
        for i, item in enumerate(priority_items, 1):
            lines.append(f"\n{i}. {item['title']}")
            lines.append(f"   来源: {item.get('platform', '')}")
            lines.append(f"   热度: {item.get('hot', '')}")
            if item.get('url'):
                lines.append(f"   链接: {item['url']}")
        
        lines.append("")
    
    # 页脚
    lines.append("=" * 70)
    lines.append("💡 本报告由 HotList Analyzer 自动生成")
    lines.append("📅 下次更新: 2小时后")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def _save_data(data: Dict):
    """保存分析数据到文件"""
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = f"{skill_dir}/data/latest_analysis.json"
    
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_saved_data() -> Optional[Dict]:
    """读取保存的分析数据"""
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = f"{skill_dir}/data/latest_analysis.json"
    
    if os.path.exists(data_file):
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# 便捷函数（供Hermes直接调用）
def quick_analysis() -> str:
    """
    快速分析 - 一键执行完整流程
    
    Returns:
        格式化后的分析报告文本
    """
    # 1. 采集和分析
    data = collect_and_analyze(max_items=8)
    
    # 2. 生成AI提示词
    ai_prompt = format_for_ai_analysis(data)
    
    # 3. 生成搜索查询
    search_queries = generate_search_queries(data.get("priority_items", []))
    
    # 4. 编译报告（不带AI分析，需要Hermes添加）
    report = compile_final_report(data)
    
    # 5. 返回报告和AI提示词
    full_output = f"""{report}

{"=" * 70}
🤖 AI深度分析提示词（请提供给AI进行分析）
{"=" * 70}
{ai_prompt}

{"=" * 70}
🔍 建议搜索查询（如需背景信息）
{"=" * 70}
"""
    for i, query in enumerate(search_queries, 1):
        full_output += f"{i}. {query}\n"
    
    return full_output


if __name__ == "__main__":
    # 测试运行
    print("运行快速分析...\n")
    result = quick_analysis()
    print(result)
