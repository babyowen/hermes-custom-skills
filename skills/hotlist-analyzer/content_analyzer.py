#!/usr/bin/env python3
"""
深度内容分析模块
提取新闻正文、AI分析要点、搜索背景信息
"""

import os
import sys
import json
import asyncio
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
import requests

# 使用Firecrawl提取内容
sys.path.insert(0, '/home/ubuntu/.hermes/hermes-agent')
from tools.web_tools import web_extract_tool


@dataclass
class NewsAnalysis:
    """单条新闻的分析结果"""
    title: str
    url: str
    platform: str
    hot: str
    summary: str = ""  # AI生成的摘要
    key_points: List[str] = None  # 关键要点
    entities: List[str] = None  # 涉及实体（人名、公司、地点等）
    sentiment: str = ""  # 情感倾向
    category: str = ""  # 分类
    importance: str = ""  # 重要性评估
    background_search_needed: bool = False  # 是否需要背景搜索
    background_info: str = ""  # 背景信息
    related_news: List[Dict] = None  # 相关新闻
    
    def __post_init__(self):
        if self.key_points is None:
            self.key_points = []
        if self.entities is None:
            self.entities = []
        if self.related_news is None:
            self.related_news = []


class ContentAnalyzer:
    """内容分析器 - 深入分析新闻内容"""
    
    def __init__(self):
        self.max_concurrent = 3  # 并发数限制
        self.extract_timeout = 30  # 提取超时
        
    async def analyze_hotspots(self, hotspots: List[Dict], 
                               max_analyze: int = 5) -> List[NewsAnalysis]:
        """
        批量分析热点新闻
        
        Args:
            hotspots: 热点列表（从新热点检测或跨平台热点获取）
            max_analyze: 最多分析多少条（避免超时）
            
        Returns:
            分析结果列表
        """
        results = []
        
        # 选择最值得分析的热点
        selected = self._select_priority_hotspots(hotspots, max_analyze)
        
        print(f"\n🔍 深度分析 {len(selected)} 条热点新闻...")
        
        # 串行处理（避免API限制）
        for i, hotspot in enumerate(selected, 1):
            print(f"  [{i}/{len(selected)}] 分析: {hotspot['title'][:40]}...")
            
            try:
                analysis = await self._analyze_single(hotspot)
                results.append(analysis)
                
                # 如果需要背景搜索，进行补充研究
                if analysis.background_search_needed:
                    print(f"    📚 搜索背景信息...")
                    await self._search_background(analysis)
                    
            except Exception as e:
                print(f"    ❌ 分析失败: {str(e)[:50]}")
                # 创建基础分析结果
                results.append(NewsAnalysis(
                    title=hotspot.get("title", ""),
                    url=hotspot.get("url", ""),
                    platform=hotspot.get("platform", ""),
                    hot=hotspot.get("hot", ""),
                    summary=f"分析失败: {str(e)[:100]}"
                ))
        
        return results
    
    def _select_priority_hotspots(self, hotspots: List[Dict], 
                                  max_count: int) -> List[Dict]:
        """选择优先级最高的热点进行分析"""
        # 优先级：跨平台热点 > 高热度 > 新热点
        scored = []
        
        for h in hotspots:
            score = 0
            # 跨平台加分
            if h.get("platform_count", 0) > 1:
                score += 100 * h["platform_count"]
            # 热度加分
            hot_num = self._parse_hot_number(h.get("hot", "0"))
            score += hot_num / 10000
            # 新热点加分
            if h.get("change") == "new":
                score += 50
            
            scored.append((score, h))
        
        # 排序并选择前N个
        scored.sort(key=lambda x: x[0], reverse=True)
        return [h for _, h in scored[:max_count]]
    
    async def _analyze_single(self, hotspot: Dict) -> NewsAnalysis:
        """分析单条热点"""
        title = hotspot.get("title", "")
        url = hotspot.get("url", "")
        platform = hotspot.get("platform", "")
        hot = hotspot.get("hot", "")
        
        # 1. 提取新闻正文
        content = await self._extract_content(url, title)
        
        # 2. AI分析内容
        analysis_result = await self._ai_analyze(title, content, platform)
        
        # 3. 创建分析对象
        analysis = NewsAnalysis(
            title=title,
            url=url,
            platform=platform,
            hot=hot,
            summary=analysis_result.get("summary", ""),
            key_points=analysis_result.get("key_points", []),
            entities=analysis_result.get("entities", []),
            sentiment=analysis_result.get("sentiment", ""),
            category=analysis_result.get("category", ""),
            importance=analysis_result.get("importance", ""),
            background_search_needed=analysis_result.get("need_background", False)
        )
        
        return analysis
    
    async def _extract_content(self, url: str, title: str) -> str:
        """提取新闻正文内容"""
        if not url:
            return ""
        
        try:
            # 使用Firecrawl提取内容
            # 注意：这里我们模拟调用，实际应该在Hermes环境中使用web_extract工具
            
            # 简单HTTP请求获取内容（备用方案）
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # 针对特定平台优化
            domain = urlparse(url).netloc
            
            # 今日头条特殊处理
            if 'toutiao.com' in domain:
                return await self._extract_toutiao(url)
            
            # 通用提取
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # 简单文本提取（去除HTML标签）
                import re
                text = re.sub(r'<[^>]+>', '', response.text)
                text = re.sub(r'\s+', ' ', text)
                
                # 限制长度
                return text[:5000]
            
        except Exception as e:
            print(f"    ⚠️ 内容提取失败: {str(e)[:50]}")
        
        return ""
    
    async def _extract_toutiao(self, url: str) -> str:
        """专门提取今日头条内容"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.toutiao.com/'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                import re
                # 尝试提取article-content
                content_match = re.search(r'article-content">(.*?)<\/div>', 
                                         response.text, re.DOTALL)
                if content_match:
                    text = re.sub(r'<[^>]+>', '', content_match.group(1))
                    return text[:3000]
                
                # 备用方案
                text = re.sub(r'<[^>]+>', '', response.text)
                text = re.sub(r'\s+', ' ', text)
                return text[:3000]
                
        except Exception as e:
            print(f"    ⚠️ 头条提取失败: {str(e)[:50]}")
        
        return ""
    
    async def _ai_analyze(self, title: str, content: str, 
                         platform: str) -> Dict:
        """使用AI分析新闻内容"""
        
        # 构建分析提示词
        prompt = self._build_analysis_prompt(title, content, platform)
        
        # 在Hermes环境中，这里会调用LLM
        # 现在我们先返回一个结构化的分析框架
        # 实际运行时，这个函数应该调用Hermes的AI能力
        
        return {
            "summary": f"【待AI分析】{title}",
            "key_points": ["要点1待提取", "要点2待提取", "要点3待提取"],
            "entities": [],
            "sentiment": "待分析",
            "category": "待分类",
            "importance": "待评估",
            "need_background": len(content) < 500  # 内容太短可能需要背景
        }
    
    def _build_analysis_prompt(self, title: str, content: str, 
                              platform: str) -> str:
        """构建AI分析提示词"""
        
        prompt = f"""请分析以下新闻内容，提供结构化分析：

【标题】{title}
【来源】{platform}

【正文内容】
{content[:2000] if content else "[未能提取正文，仅根据标题分析]"}

请提供以下分析（JSON格式）：
{{
  "summary": "100字以内的新闻摘要",
  "key_points": ["关键要点1", "关键要点2", "关键要点3"],
  "entities": ["涉及的人名", "公司/机构", "地点"],
  "sentiment": "positive/negative/neutral",
  "category": "科技/社会/娱乐/政治/经济/体育/其他",
  "importance": "high/medium/low",
  "need_background": true/false,
  "background_reason": "为什么需要背景信息"
}}

分析要求：
1. 客观准确，不要过度解读
2. 如果正文内容不足，标记need_background为true
3. 评估新闻的重要性和影响力
4. 识别关键实体（人物、机构、地点）
"""
        return prompt
    
    async def _search_background(self, analysis: NewsAnalysis):
        """搜索背景信息"""
        try:
            # 构建搜索查询
            query = f"{analysis.title} { ' '.join(analysis.entities[:3])}"
            
            # 在Hermes环境中，这里会调用web_search
            # 现在我们创建一个占位结果
            analysis.background_info = f"【背景信息待搜索】关于: {query}"
            
            # 搜索相关新闻
            analysis.related_news = [
                {"title": "相关新闻1", "source": "待搜索"},
                {"title": "相关新闻2", "source": "待搜索"}
            ]
            
        except Exception as e:
            print(f"    ⚠️ 背景搜索失败: {str(e)[:50]}")
            analysis.background_info = "背景搜索失败"
    
    def _parse_hot_number(self, hot_str: str) -> int:
        """解析热度数字"""
        if not hot_str:
            return 0
        try:
            if "万" in hot_str:
                return int(float(hot_str.replace("万", "")) * 10000)
            return int(float(hot_str))
        except:
            return 0
    
    def generate_deep_report(self, analyses: List[NewsAnalysis]) -> str:
        """生成深度分析报告"""
        lines = []
        
        lines.append("# 🔥 全网热点深度分析报告")
        lines.append(f"**分析时间**: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"**分析数量**: {len(analyses)} 条热点")
        lines.append("")
        lines.append("=" * 60)
        lines.append("")
        
        # 按重要性排序
        importance_order = {"high": 0, "medium": 1, "low": 2}
        sorted_analyses = sorted(
            analyses, 
            key=lambda x: importance_order.get(x.importance, 3)
        )
        
        for i, analysis in enumerate(sorted_analyses, 1):
            lines.append(self._format_single_analysis(i, analysis))
            lines.append("")
            lines.append("-" * 60)
            lines.append("")
        
        return "\n".join(lines)
    
    def _format_single_analysis(self, index: int, 
                                analysis: NewsAnalysis) -> str:
        """格式化单条新闻分析"""
        lines = []
        
        # 标题和来源
        importance_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
            analysis.importance, "⚪"
        )
        
        lines.append(f"### {index}. {importance_emoji} {analysis.title}")
        lines.append(f"**来源**: {analysis.platform} | **热度**: {analysis.hot}")
        lines.append(f"**链接**: [{analysis.url[:50]}...]({analysis.url})")
        lines.append("")
        
        # AI分析摘要
        if analysis.summary:
            lines.append(f"**📝 内容摘要**: {analysis.summary}")
            lines.append("")
        
        # 关键要点
        if analysis.key_points:
            lines.append("**🔑 关键要点**:")
            for point in analysis.key_points:
                lines.append(f"  • {point}")
            lines.append("")
        
        # 涉及实体
        if analysis.entities:
            lines.append(f"**👥 涉及实体**: {', '.join(analysis.entities)}")
            lines.append("")
        
        # 分类和情感
        if analysis.category:
            sentiment_emoji = {
                "positive": "😊", "negative": "😔", "neutral": "😐"
            }.get(analysis.sentiment, "😐")
            lines.append(f"**📂 分类**: {analysis.category} | **情感**: {sentiment_emoji} {analysis.sentiment}")
            lines.append("")
        
        # 背景信息
        if analysis.background_info:
            lines.append(f"**📚 背景信息**: {analysis.background_info}")
            lines.append("")
        
        return "\n".join(lines)


# 同步包装函数（方便在同步代码中调用）
def analyze_hotspots_sync(hotspots: List[Dict], 
                         max_analyze: int = 5) -> Tuple[List[NewsAnalysis], str]:
    """
    同步方式分析热点（供Hermes调用）
    
    Returns:
        (分析结果列表, 深度报告文本)
    """
    analyzer = ContentAnalyzer()
    
    # 运行异步分析
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        analyses = loop.run_until_complete(
            analyzer.analyze_hotspots(hotspots, max_analyze)
        )
        
        # 生成报告
        report = analyzer.generate_deep_report(analyses)
        
        return analyses, report
    finally:
        loop.close()


if __name__ == "__main__":
    # 测试内容分析器
    test_hotspots = [
        {
            "title": "十项促进两岸交流合作政策措施发布",
            "platform": "今日头条",
            "hot": "7000万",
            "url": "https://www.toutiao.com/trending/...",
            "change": "new",
            "platform_count": 3
        }
    ]
    
    print("测试内容分析...")
    analyses, report = analyze_hotspots_sync(test_hotspots, max_analyze=1)
    
    print("\n生成的报告:")
    print(report)
