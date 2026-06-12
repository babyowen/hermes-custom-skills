#!/usr/bin/env python3
"""
AI智能分析引擎
与Hermes集成，使用LLM分析热点内容，搜索背景信息
"""

import os
import sys
import json
import re
from typing import List, Dict, Optional
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


@dataclass
class AIAnalysisResult:
    """AI分析结果"""
    title: str
    url: str
    platform: str
    summary: str = ""  # AI生成的摘要
    key_points: List[str] = field(default_factory=list)
    entities: List[str] = field(default_factory=list)
    category: str = ""  # 分类
    importance: str = "medium"  # 重要性
    sentiment: str = "neutral"  # 情感倾向
    trend_prediction: str = ""  # 趋势预测
    background_needed: bool = False
    search_queries: List[str] = field(default_factory=list)  # 建议搜索词
    full_analysis: str = ""  # 完整分析文本


class AIAnalyzer:
    """
    AI分析器
    
    工作流程：
    1. 构建分析提示词
    2. 调用Hermes的AI能力分析内容
    3. 解析结构化结果
    4. 返回分析结果
    """
    
    def __init__(self):
        self.categories = ["科技", "社会", "娱乐", "政治", "经济", "体育", "国际", "其他"]
        
    def build_analysis_prompt(self, title: str, content: str = "", 
                             platform: str = "", hot: str = "") -> str:
        """构建AI分析提示词"""
        
        content_section = f"""
【新闻正文】
{content[:2000] if content else "[正文暂未提取，请基于标题进行分析]"}
""" if content else "[正文暂未提取，请基于标题进行分析]"
        
        prompt = f"""你是一位资深新闻分析师，请对以下热点新闻进行深度分析：

【新闻标题】{title}
【来源平台】{platform}
【热度】{hot}
{content_section}

请提供以下分析（严格按JSON格式输出）：

```json
{{
  "summary": "用100-150字概括新闻核心内容",
  "key_points": ["关键要点1", "关键要点2", "关键要点3", "关键要点4"],
  "entities": ["涉及的人名", "公司/机构", "地点/国家", "关键概念"],
  "category": "选择最符合的分类: 科技/社会/娱乐/政治/经济/体育/国际/其他",
  "importance": "评估重要性: high(高)/medium(中)/low(低)",
  "sentiment": "情感倾向: positive(正面)/negative(负面)/neutral(中性)",
  "trend_prediction": "预测该热点的后续发展趋势（50字以内）",
  "background_needed": true/false,
  "search_queries": ["如果需要背景信息，提供3-5个搜索关键词"]
}}
```

分析要求：
1. 客观准确，基于新闻事实
2. 如果内容不足，background_needed设为true
3. 评估该新闻对用户的重要性（high=值得立即关注, medium=值得了解, low=一般信息）
4. 预测热点持续时间（爆发式/持续发酵/快速消退）
5. 识别新闻中的关键实体（人物、机构、地点）

请只输出JSON，不要有其他内容。
"""
        return prompt
    
    def build_background_search_prompt(self, title: str, 
                                       entities: List[str],
                                       category: str) -> str:
        """构建背景搜索提示词"""
        
        entities_str = ", ".join(entities[:5]) if entities else ""
        
        prompt = f"""基于以下新闻信息，生成搜索查询以获取更多背景：

【新闻标题】{title}
【涉及实体】{entities_str}
【分类】{category}

请生成3-5个搜索查询，帮助了解：
1. 事件的前因后果
2. 相关人物/机构的背景
3. 类似历史事件
4. 专家观点或数据分析

请输出JSON格式：
```json
{{
  "search_queries": ["查询1", "查询2", "查询3", "查询4", "查询5"],
  "reason": "为什么需要这些背景信息"
}}
```
"""
        return prompt
    
    def parse_ai_response(self, response: str) -> Dict:
        """解析AI返回的JSON"""
        try:
            # 尝试从代码块中提取JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', 
                                   response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 直接尝试解析整个响应
                json_str = response
            
            result = json.loads(json_str)
            return result
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {str(e)[:100]}")
            # 返回默认值
            return {
                "summary": "AI分析结果解析失败",
                "key_points": ["要点提取失败"],
                "entities": [],
                "category": "其他",
                "importance": "medium",
                "sentiment": "neutral",
                "trend_prediction": "无法预测",
                "background_needed": False,
                "search_queries": []
            }
    
    def analyze(self, title: str, content: str = "", 
                platform: str = "", hot: str = "") -> AIAnalysisResult:
        """
        分析单条新闻
        
        注意：这个方法在Hermes环境中会调用LLM
        现在先返回结构化的分析框架
        """
        
        # 构建提示词
        prompt = self.build_analysis_prompt(title, content, platform, hot)
        
        # 在Hermes环境中，这里应该调用AI
        # 现在我们返回一个待填充的结构
        result = AIAnalysisResult(
            title=title,
            url="",
            platform=platform,
            summary="[AI分析待执行]",
            key_points=["要点待提取"],
            entities=[],
            category="待分类",
            importance="medium",
            search_queries=[title[:20]]
        )
        
        return result
    
    def batch_analyze(self, items: List[Dict]) -> List[AIAnalysisResult]:
        """批量分析"""
        results = []
        
        for item in items:
            result = self.analyze(
                title=item.get("title", ""),
                content=item.get("content", ""),
                platform=item.get("platform", ""),
                hot=item.get("hot", "")
            )
            result.url = item.get("url", "")
            results.append(result)
        
        return results


# Hermes集成辅助函数
def create_hermes_analysis_prompt(hotspots_data: List[Dict]) -> str:
    """
    创建适合Hermes执行的完整分析提示词
    
    这个函数生成一个提示词，让Hermes可以：
    1. 分析热点重要性
    2. 搜索背景信息
    3. 生成综合报告
    """
    
    # 格式化热点数据
    hotspots_text = []
    for i, h in enumerate(hotspots_data[:10], 1):
        platforms = h.get("platforms", [h.get("platform", "")])
        platforms_str = ", ".join(platforms[:3])
        
        hotspots_text.append(f"""
{i}. 【{h.get('title', '')}】
   平台: {platforms_str}
   热度: {h.get('hot', '未知')}
   链接: {h.get('url', '')}
""")
    
    prompt = f"""你是一位资深新闻分析师。请对以下热点新闻进行深度分析：

{chr(10).join(hotspots_text)}

请完成以下任务：

1. **热点分类与重要性评估**
   对每个热点进行分类（科技/社会/娱乐/政治/经济/体育/国际）
   评估重要性（🔴高/🟡中/🟢低）
   说明为什么重要

2. **关键信息提取**
   提取每个热点的核心要点（3-4点）
   识别涉及的关键人物、机构、地点
   分析情感倾向（正面/负面/中性）

3. **趋势预测**
   预测哪些热点会持续发酵
   哪些可能是短期热点
   给出关注建议

4. **跨平台分析**
   分析为什么某些话题能在多个平台同时热门
   识别不同平台的关注角度差异

5. **综合建议**
   哪些热点最值得立即关注？
   哪些需要持续跟踪？
   有什么潜在影响？

请用结构化格式输出，便于阅读。
"""
    
    return prompt


def create_background_search_queries(analyses: List[AIAnalysisResult]) -> List[str]:
    """为背景搜索生成查询词"""
    queries = []
    
    for analysis in analyses:
        if analysis.background_needed or analysis.importance == "high":
            # 基础查询
            queries.append(analysis.title)
            
            # 实体查询
            for entity in analysis.entities[:2]:
                queries.append(f"{entity} {analysis.category}")
    
    # 去重
    unique_queries = list(set(queries))
    return unique_queries[:10]  # 最多10个查询


if __name__ == "__main__":
    # 测试AI分析器
    analyzer = AIAnalyzer()
    
    test_item = {
        "title": "十项促进两岸交流合作政策措施发布",
        "platform": "今日头条",
        "hot": "7000万",
        "url": "https://example.com"
    }
    
    result = analyzer.analyze(**test_item)
    
    print("AI分析结果:")
    print(f"标题: {result.title}")
    print(f"摘要: {result.summary}")
    print(f"分类: {result.category}")
    print(f"重要性: {result.importance}")
