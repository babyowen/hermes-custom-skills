#!/usr/bin/env python3
"""
热点分析报告生成器
生成结构化的Markdown报告
"""

from datetime import datetime, timedelta
from typing import List, Dict
from analyzer import AnalysisResult


class HotListReporter:
    """热点报告生成器"""
    
    def __init__(self):
        self.emoji_map = {
            "今日头条": "📰",
            "澎湃新闻": "📰",
            "腾讯新闻": "📰",
            "网易新闻": "📰",
            "微博": "📱",
            "微博热搜": "🔥",
            "微博要闻": "📰",
            "抖音": "🎵",
            "知乎": "❓",
            "知乎热榜": "❓",
            "知乎日报": "📚",
            "百度": "🔍",
            "虎嗅": "🐯",
            "机核": "🎮",
            "36氪": "💼",
            "IT之家": "💻",
            "虫部落": "🐛",
            "woShiPm": "📊"
        }
    
    def generate_report(self, result: AnalysisResult, 
                       include_ai_analysis: bool = True) -> str:
        """
        生成完整的分析报告
        
        Args:
            result: 分析结果
            include_ai_analysis: 是否包含AI分析占位符
            
        Returns:
            Markdown格式的报告
        """
        lines = []
        
        # 报告标题
        lines.append("# 🔥 全网热点追踪分析报告")
        lines.append("")
        lines.append(f"**生成时间**: {result.timestamp}")
        lines.append(f"**数据来源**: 11个主流平台")
        lines.append("")
        
        # 执行摘要
        lines.append("## 📋 执行摘要")
        lines.append("")
        lines.append(f"- 🆕 新发现热点: **{len(result.new_hotspots)}** 个")
        lines.append(f"- 🌐 跨平台话题: **{len(result.cross_platform)}** 个")
        lines.append(f"- 📊 覆盖平台: **{len(result.platform_summaries)}** 个")
        lines.append("")
        
        # 新热点
        if result.new_hotspots:
            lines.append("## 🆕 新发现热点")
            lines.append("")
            lines.append("最近1-2小时内新出现或排名大幅上升的热点：")
            lines.append("")
            
            for i, hotspot in enumerate(result.new_hotspots[:10], 1):
                lines.append(self._format_new_hotspot(i, hotspot))
                lines.append("")
        
        # 跨平台热点
        if result.cross_platform:
            lines.append("---")
            lines.append("")
            lines.append("## 🌐 跨平台热点")
            lines.append("")
            lines.append("多个平台共同关注的热门话题：")
            lines.append("")
            
            for i, topic in enumerate(result.cross_platform[:8], 1):
                lines.append(self._format_cross_platform_topic(i, topic))
                lines.append("")
        
        # 各平台TOP5
        lines.append("---")
        lines.append("")
        lines.append("## 📊 各平台热点TOP5")
        lines.append("")
        
        for platform, items in result.platform_summaries.items():
            if items:
                lines.append(self._format_platform_section(platform, items[:5]))
                lines.append("")
        
        # AI分析占位符
        if include_ai_analysis:
            lines.append("---")
            lines.append("")
            lines.append("## 🤖 AI 深度洞察")
            lines.append("")
            lines.append("_AI分析将在实际运行时通过LLM生成..._")
            lines.append("")
            lines.append("<!-- AI_INSIGHTS_START -->")
            lines.append(result.ai_insights)
            lines.append("<!-- AI_INSIGHTS_END -->")
            lines.append("")
        
        # 页脚
        lines.append("---")
        lines.append("")
        lines.append("*报告由 HotList Analyzer 自动生成*")
        lines.append(f"*下次更新: {(datetime.strptime(result.timestamp, '%Y-%m-%d %H:%M:%S') + timedelta(hours=1)).strftime('%H:%M')}*")
        
        return "\n".join(lines)
    
    def generate_compact_summary(self, result: AnalysisResult) -> str:
        """
        生成精简摘要（适合聊天/推送）
        
        Returns:
            精简文本
        """
        lines = []
        lines.append(f"🔥 热点追踪报告 ({result.timestamp[-8:-3]})")
        lines.append("")
        
        # 跨平台热点（最重要）
        if result.cross_platform:
            lines.append("🌐 跨平台热点:")
            for topic in result.cross_platform[:5]:
                platforms = ", ".join(topic["platforms"][:3])
                lines.append(f"  • {topic['main_title'][:20]}... ({platforms})")
            lines.append("")
        
        # 新热点
        if result.new_hotspots:
            lines.append("🆕 新热点:")
            for hotspot in result.new_hotspots[:5]:
                emoji = self._get_platform_emoji(hotspot.get("platform", ""))
                lines.append(f"  {emoji} {hotspot['title'][:20]}...")
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_new_hotspot(self, index: int, hotspot: Dict) -> str:
        """格式化新热点"""
        title = hotspot["title"]
        platform = hotspot.get("platform", "未知")
        hot = hotspot.get("hot", "")
        change = hotspot.get("change", "new")
        url = hotspot.get("url", "")
        
        emoji = self._get_platform_emoji(platform)
        
        # 变化标识
        change_emoji = "🆕"
        if change.startswith("up_"):
            change_emoji = f"📈 上升{change.replace('up_', '')}位"
        
        lines = [
            f"### {index}. {title}",
            f"",
            f"- **来源**: {emoji} {platform}",
        ]
        
        if hot:
            lines.append(f"- **热度**: {hot}")
        
        lines.append(f"- **状态**: {change_emoji}")
        
        if url:
            lines.append(f"- **链接**: [{url[:50]}...]({url})")
        
        return "\n".join(lines)
    
    def _format_cross_platform_topic(self, index: int, topic: Dict) -> str:
        """格式化跨平台话题"""
        main_title = topic["main_title"]
        platforms = topic["platforms"]
        platform_count = topic["platform_count"]
        items = topic["items"]
        
        # 平台emoji
        platform_emojis = " ".join(
            self._get_platform_emoji(p) for p in platforms[:5]
        )
        
        lines = [
            f"### {index}. {main_title}",
            f"",
            f"- **覆盖平台**: {platform_emojis} ({platform_count}个平台)",
            f"- **各平台排名**:",
        ]
        
        # 按排名排序
        sorted_items = sorted(items, key=lambda x: x.get("rank", 999))
        for item in sorted_items[:5]:
            emoji = self._get_platform_emoji(item.get("platform", ""))
            rank = item.get("rank", "-")
            hot = item.get("hot", "")
            hot_str = f" [{hot}]" if hot else ""
            lines.append(f"  - {emoji} {item['platform']}: 第{rank}位{hot_str}")
        
        return "\n".join(lines)
    
    def _format_platform_section(self, platform: str, items: List[Dict]) -> str:
        """格式化平台热点列表"""
        platform_name = items[0].get("platform", platform) if items else platform
        emoji = self._get_platform_emoji(platform_name)
        
        lines = [f"### {emoji} {platform_name}"]
        lines.append("")
        
        for i, item in enumerate(items, 1):
            title = item.get("title", "无标题")
            hot = item.get("hot", "")
            url = item.get("url", "")
            
            hot_str = f" [{hot}]" if hot else ""
            
            if url:
                lines.append(f"{i}. [{title}]({url}){hot_str}")
            else:
                lines.append(f"{i}. {title}{hot_str}")
        
        return "\n".join(lines)
    
    def _get_platform_emoji(self, platform_name: str) -> str:
        """获取平台对应的emoji"""
        for name, emoji in self.emoji_map.items():
            if name in platform_name:
                return emoji
        return "📰"  # 默认
    
    def save_report(self, report: str, timestamp: str = None) -> str:
        """
        保存报告到文件
        
        Returns:
            保存的文件路径
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        skill_dir = __file__.rsplit("/", 1)[0]
        reports_dir = f"{skill_dir}/reports"
        
        import os
        os.makedirs(reports_dir, exist_ok=True)
        
        filename = f"{reports_dir}/hotlist_report_{timestamp}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        
        return filename


if __name__ == "__main__":
    # 测试报告生成
    from analyzer import AnalysisResult
    
    # 模拟数据
    result = AnalysisResult(
        timestamp="2026-04-12 12:00:00",
        new_hotspots=[
            {
                "title": "测试新热点1",
                "platform": "今日头条",
                "hot": "1000万",
                "change": "new"
            }
        ],
        cross_platform=[
            {
                "main_title": "跨平台测试话题",
                "platforms": ["今日头条", "抖音"],
                "platform_count": 2,
                "items": []
            }
        ],
        platform_summaries={
            "toutiao": [
                {"title": "热点1", "hot": "1000万", "index": 1},
                {"title": "热点2", "hot": "900万", "index": 2}
            ]
        },
        trends=[],
        ai_insights="{}"
    )
    
    reporter = HotListReporter()
    report = reporter.generate_report(result)
    print(report)
    
    # 保存
    path = reporter.save_report(report)
    print(f"\n报告已保存到: {path}")
