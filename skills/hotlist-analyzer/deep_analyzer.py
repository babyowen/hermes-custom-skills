#!/usr/bin/env python3
"""
深度分析集成模块
整合热点检测、内容提取、AI分析、背景搜索
"""

import os
import sys
import json
from typing import List, Dict, Tuple
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from analyzer import HotListAnalyzer
from content_analyzer import ContentAnalyzer, NewsAnalysis, analyze_hotspots_sync
from storage import HotListStorage


class DeepHotListAnalyzer:
    """
    深度热点分析器
    
    工作流程：
    1. 采集所有平台热点
    2. 检测新热点和跨平台热点
    3. 对重要热点提取正文内容
    4. AI分析内容要点
    5. 必要时搜索背景信息
    6. 生成综合深度报告
    """
    
    def __init__(self):
        self.storage = HotListStorage()
        self.analyzer = HotListAnalyzer(self.storage)
        self.content_analyzer = ContentAnalyzer()
        
    def run_deep_analysis(self, max_deep_analyze: int = 5) -> Dict:
        """
        执行完整的深度分析流程
        
        Args:
            max_deep_analyze: 最多深度分析多少条热点
            
        Returns:
            包含所有分析结果的字典
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("=" * 70)
        print("🔥 启动深度热点分析")
        print("=" * 70)
        
        # Step 1: 采集数据
        print("\n📥 Step 1: 采集全网热点数据...")
        collected = self.analyzer.collect_all()
        
        # Step 2: 基础分析（新热点 + 跨平台）
        print("\n🔍 Step 2: 基础分析（新热点检测 + 跨平台关联）...")
        
        new_hotspots = self.analyzer.find_new_hotspots()
        cross_platform = self.analyzer.find_cross_platform_topics(min_platforms=2)
        
        print(f"   🆕 新热点: {len(new_hotspots)} 个")
        print(f"   🌐 跨平台话题: {len(cross_platform)} 个")
        
        # Step 3: 深度内容分析
        print(f"\n📚 Step 3: 深度内容分析（最多{max_deep_analyze}条）...")
        
        # 合并新热点和跨平台热点，去重
        priority_hotspots = self._merge_priority_hotspots(
            new_hotspots, cross_platform
        )
        
        print(f"   选择 {len(priority_hotspots[:max_deep_analyze])} 条高优先级热点进行深度分析")
        
        # 执行深度分析
        if priority_hotspots:
            deep_analyses, deep_report = analyze_hotspots_sync(
                priority_hotspots[:max_deep_analyze],
                max_analyze=max_deep_analyze
            )
        else:
            deep_analyses = []
            deep_report = "未找到需要深度分析的热点"
        
        # Step 4: 整合结果
        print("\n📊 Step 4: 整合分析结果...")
        
        result = {
            "timestamp": timestamp,
            "summary": {
                "platforms": len(collected),
                "new_hotspots": len(new_hotspots),
                "cross_platform": len(cross_platform),
                "deep_analyzed": len(deep_analyses)
            },
            "new_hotspots": new_hotspots[:15],
            "cross_platform": cross_platform[:8],
            "deep_analyses": [
                self._analysis_to_dict(a) for a in deep_analyses
            ],
            "deep_report": deep_report,
            "platform_summaries": self.analyzer._summarize_by_platform()
        }
        
        print("\n✅ 深度分析完成!")
        print(f"   分析了 {len(collected)} 个平台")
        print(f"   发现 {len(new_hotspots)} 个新热点")
        print(f"   识别 {len(cross_platform)} 个跨平台话题")
        print(f"   深度分析 {len(deep_analyses)} 条重要热点")
        
        return result
    
    def _merge_priority_hotspots(self, new_hotspots: List[Dict], 
                                 cross_platform: List[Dict]) -> List[Dict]:
        """合并并去重优先级热点"""
        seen_titles = set()
        merged = []
        
        # 首先添加跨平台热点（优先级更高）
        for topic in cross_platform:
            main_title = topic.get("main_title", "")
            normalized = self._normalize_title(main_title)
            
            if normalized and normalized not in seen_titles:
                seen_titles.add(normalized)
                
                # 转换为统一格式
                merged.append({
                    "title": main_title,
                    "platform": f"跨平台 ({topic.get('platform_count', 0)}个平台)",
                    "hot": f"{topic.get('total_hot', 0)/10000:.0f}万综合热度",
                    "url": topic.get("items", [{}])[0].get("url", ""),
                    "platform_count": topic.get("platform_count", 0),
                    "is_cross_platform": True,
                    "platforms": topic.get("platforms", [])
                })
        
        # 然后添加新热点
        for hotspot in new_hotspots:
            title = hotspot.get("title", "")
            normalized = self._normalize_title(title)
            
            if normalized and normalized not in seen_titles:
                seen_titles.add(normalized)
                merged.append(hotspot)
        
        return merged
    
    def _normalize_title(self, title: str) -> str:
        """标准化标题用于去重"""
        import re
        # 移除标点符号和空格
        normalized = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', title)
        return normalized.lower().strip()
    
    def _analysis_to_dict(self, analysis: NewsAnalysis) -> Dict:
        """将NewsAnalysis转换为字典"""
        return {
            "title": analysis.title,
            "url": analysis.url,
            "platform": analysis.platform,
            "hot": analysis.hot,
            "summary": analysis.summary,
            "key_points": analysis.key_points,
            "entities": analysis.entities,
            "sentiment": analysis.sentiment,
            "category": analysis.category,
            "importance": analysis.importance,
            "background_info": analysis.background_info,
            "related_news": analysis.related_news
        }
    
    def generate_executive_summary(self, result: Dict) -> str:
        """生成执行摘要（适合快速阅读）"""
        summary = result["summary"]
        deep_analyses = result.get("deep_analyses", [])
        
        lines = []
        lines.append("=" * 60)
        lines.append("🔥 热点追踪执行摘要")
        lines.append("=" * 60)
        lines.append(f"生成时间: {result['timestamp']}")
        lines.append("")
        
        # 统计信息
        lines.append(f"📊 数据概览:")
        lines.append(f"  • 覆盖平台: {summary['platforms']} 个")
        lines.append(f"  • 新发现热点: {summary['new_hotspots']} 个")
        lines.append(f"  • 跨平台话题: {summary['cross_platform']} 个")
        lines.append(f"  • 深度分析: {summary['deep_analyzed']} 条")
        lines.append("")
        
        # 重点热点（高重要性）
        if deep_analyses:
            high_importance = [a for a in deep_analyses if a.get("importance") == "high"]
            if high_importance:
                lines.append(f"🔴 重点关注 ({len(high_importance)}条):")
                for i, item in enumerate(high_importance[:3], 1):
                    lines.append(f"  {i}. {item['title'][:40]}...")
                    if item.get("summary"):
                        lines.append(f"     📌 {item['summary'][:60]}...")
                lines.append("")
        
        # 跨平台热点
        cross_platform = result.get("cross_platform", [])
        if cross_platform:
            lines.append(f"🌐 跨平台热点TOP3:")
            for i, topic in enumerate(cross_platform[:3], 1):
                title = topic.get("main_title", "")
                platforms = ", ".join(topic.get("platforms", [])[:3])
                lines.append(f"  {i}. {title[:30]}... ({platforms})")
            lines.append("")
        
        # 分类统计
        if deep_analyses:
            categories = {}
            for a in deep_analyses:
                cat = a.get("category", "其他")
                categories[cat] = categories.get(cat, 0) + 1
            
            if categories:
                lines.append("📂 热点分类:")
                for cat, count in sorted(categories.items(), key=lambda x: -x[1]):
                    lines.append(f"  • {cat}: {count}条")
                lines.append("")
        
        lines.append("=" * 60)
        lines.append("💡 提示: 输入'查看详细报告'获取完整分析")
        
        return "\n".join(lines)


def generate_full_report(result: Dict) -> str:
    """生成完整报告（Markdown格式）"""
    lines = []
    
    # 报告头部
    lines.append("# 🔥 全网热点深度追踪报告")
    lines.append(f"**生成时间**: {result['timestamp']}")
    lines.append(f"**分析覆盖**: {result['summary']['platforms']} 个平台")
    lines.append("")
    
    # 执行摘要
    lines.append("## 📋 执行摘要")
    lines.append("")
    lines.append(f"- 🆕 新发现热点: **{result['summary']['new_hotspots']}** 个")
    lines.append(f"- 🌐 跨平台话题: **{result['summary']['cross_platform']}** 个")
    lines.append(f"- 📚 深度分析: **{result['summary']['deep_analyzed']}** 条")
    lines.append("")
    
    # 深度分析结果
    deep_analyses = result.get("deep_analyses", [])
    if deep_analyses:
        lines.append("---")
        lines.append("")
        lines.append("## 📚 深度分析热点")
        lines.append("")
        
        for i, analysis in enumerate(deep_analyses, 1):
            importance = analysis.get("importance", "medium")
            emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(importance, "⚪")
            
            lines.append(f"### {i}. {emoji} {analysis['title']}")
            lines.append(f"**来源**: {analysis['platform']} | **热度**: {analysis['hot']}")
            lines.append(f"**链接**: [{analysis['url'][:50]}...]({analysis['url']})")
            lines.append("")
            
            if analysis.get("summary"):
                lines.append(f"**📝 内容摘要**: {analysis['summary']}")
                lines.append("")
            
            if analysis.get("key_points"):
                lines.append("**🔑 关键要点**:")
                for point in analysis["key_points"]:
                    lines.append(f"  • {point}")
                lines.append("")
            
            if analysis.get("entities"):
                lines.append(f"**👥 涉及实体**: {', '.join(analysis['entities'])}")
                lines.append("")
            
            if analysis.get("category"):
                lines.append(f"**📂 分类**: {analysis['category']}")
                lines.append("")
            
            if analysis.get("background_info"):
                lines.append(f"**📚 背景信息**:")
                lines.append(f"> {analysis['background_info']}")
                lines.append("")
            
            lines.append("---")
            lines.append("")
    
    # 新热点列表
    new_hotspots = result.get("new_hotspots", [])
    if new_hotspots:
        lines.append("## 🆕 新发现热点")
        lines.append("")
        for i, hotspot in enumerate(new_hotspots[:10], 1):
            lines.append(f"{i}. **{hotspot['title']}** ({hotspot['platform']}) [{hotspot['hot']}]")
        lines.append("")
    
    # 跨平台热点
    cross_platform = result.get("cross_platform", [])
    if cross_platform:
        lines.append("## 🌐 跨平台热点")
        lines.append("")
        for i, topic in enumerate(cross_platform, 1):
            lines.append(f"### {i}. {topic['main_title']}")
            lines.append(f"**覆盖平台**: {', '.join(topic.get('platforms', []))}")
            lines.append("")
        
        lines.append("")
    
    # 页脚
    lines.append("---")
    lines.append("")
    lines.append("*报告由 HotList Deep Analyzer 自动生成*")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 测试深度分析
    print("启动深度分析测试...\n")
    
    deep_analyzer = DeepHotListAnalyzer()
    result = deep_analyzer.run_deep_analysis(max_deep_analyze=3)
    
    # 打印执行摘要
    print("\n" + deep_analyzer.generate_executive_summary(result))
    
    # 保存完整报告
    report = generate_full_report(result)
    print("\n\n完整报告已生成")
