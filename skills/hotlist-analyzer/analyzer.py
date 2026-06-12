#!/usr/bin/env python3
"""
热点分析引擎
实现新热点检测、跨平台关联分析、趋势分析等功能
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import re
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Set
from difflib import SequenceMatcher
from dataclasses import dataclass
from collections import defaultdict

from storage import HotListStorage, HotItem

# 导入热点获取模块
sys.path.insert(0, '/home/ubuntu/.hermes/skills/hotlist-tracker')
from hotlist import get_hotlist, PLATFORMS


@dataclass
class AnalysisResult:
    """分析结果数据结构"""
    timestamp: str
    new_hotspots: List[Dict]
    cross_platform: List[Dict]
    platform_summaries: Dict[str, List[Dict]]
    trends: List[Dict]
    ai_insights: str = ""


class HotListAnalyzer:
    """热点分析器"""
    
    def __init__(self, storage: HotListStorage = None):
        """初始化分析器"""
        self.storage = storage or HotListStorage()
        self.similarity_threshold = 0.6  # 文本相似度阈值
    
    def collect_all(self) -> Dict[str, Dict]:
        """
        采集所有可用平台的热点数据
        
        Returns:
            {platform_key: api_response_data}
        """
        results = {}
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 只采集可用的平台
        available_platforms = [k for k, v in PLATFORMS.items() if v.get("status") == "ok"]
        
        print(f"开始采集 {len(available_platforms)} 个平台的数据...")
        
        for platform in available_platforms:
            try:
                data = get_hotlist(platform, limit=30)
                if "error" not in data:
                    results[platform] = data
                    # 保存到数据库
                    self.storage.save_hotlist(
                        platform=platform,
                        platform_name=data.get("name", platform),
                        items=data.get("data", []),
                        timestamp=timestamp
                    )
                    print(f"  ✅ {data.get('name', platform)}: {len(data.get('data', []))}条")
                else:
                    print(f"  ❌ {platform}: {data['error']}")
            except Exception as e:
                print(f"  ❌ {platform}: {str(e)}")
        
        # 记录采集日志
        total_items = sum(len(d.get("data", [])) for d in results.values())
        self.storage.log_collection(timestamp, len(results), total_items)
        
        print(f"\n采集完成: {len(results)}个平台, {total_items}条数据")
        return results
    
    def find_new_hotspots(self, hours_back: int = 2) -> List[Dict]:
        """
        发现新热点（最近出现的热点）
        
        Args:
            hours_back: 回溯多少小时对比
            
        Returns:
            新热点列表，包含热度变化信息
        """
        new_hotspots = []
        
        # 获取所有平台最新数据
        latest_data = self.storage.get_all_latest(limit_per_platform=30)
        
        for platform, current_items in latest_data.items():
            if not current_items:
                continue
            
            current_time = current_items[0].timestamp
            
            # 获取上一次的数据
            prev_time, prev_items = self.storage.get_previous_by_platform(
                platform, current_time, limit=50
            )
            
            if not prev_items:
                # 没有历史数据，所有都是新的
                for item in current_items[:10]:  # 只取前10
                    new_hotspots.append({
                        "title": item.title,
                        "platform": item.platform_name,
                        "platform_key": item.platform,
                        "hot": item.hot,
                        "url": item.url,
                        "rank": item.index,
                        "change": "new",
                        "previous_rank": None,
                        "first_seen": current_time
                    })
                continue
            
            # 构建上一次数据的标题集合
            prev_titles = {self._normalize_title(i.title) for i in prev_items}
            prev_items_dict = {self._normalize_title(i.title): i for i in prev_items}
            
            # 检查当前数据中的新热点
            for item in current_items:
                normalized = self._normalize_title(item.title)
                
                # 完全匹配或高度相似
                if normalized not in prev_titles:
                    # 检查是否有相似内容
                    similar = self._find_similar(normalized, prev_titles)
                    
                    if not similar:
                        # 全新热点
                        new_hotspots.append({
                            "title": item.title,
                            "platform": item.platform_name,
                            "platform_key": item.platform,
                            "hot": item.hot,
                            "url": item.url,
                            "rank": item.index,
                            "change": "new",
                            "previous_rank": None,
                            "first_seen": current_time
                        })
                    else:
                        # 相似内容，检查排名变化
                        prev_item = prev_items_dict[similar]
                        rank_change = prev_item.index - item.index
                        
                        if rank_change >= 5:  # 排名上升超过5位
                            new_hotspots.append({
                                "title": item.title,
                                "platform": item.platform_name,
                                "platform_key": item.platform,
                                "hot": item.hot,
                                "url": item.url,
                                "rank": item.index,
                                "change": f"up_{rank_change}",
                                "previous_rank": prev_item.index,
                                "first_seen": current_time
                            })
        
        # 按热度排序
        new_hotspots.sort(key=lambda x: self._parse_hot(x.get("hot", "0")), reverse=True)
        return new_hotspots[:20]  # 返回前20个新热点
    
    def find_cross_platform_topics(self, min_platforms: int = 2) -> List[Dict]:
        """
        发现跨平台热点（多个平台都在讨论的话题）
        
        Args:
            min_platforms: 最少需要出现在多少个平台
            
        Returns:
            跨平台热点列表
        """
        # 获取所有平台最新数据
        all_data = self.storage.get_all_latest(limit_per_platform=20)
        
        # 提取所有标题并分组
        topic_groups = []
        processed = set()
        
        all_items = []
        for platform, items in all_data.items():
            for item in items:
                all_items.append(item)
        
        # 两两比较找相似
        for i, item1 in enumerate(all_items):
            if i in processed:
                continue
            
            group = [item1]
            processed.add(i)
            
            for j, item2 in enumerate(all_items[i+1:], start=i+1):
                if j in processed:
                    continue
                
                if self._is_similar(item1.title, item2.title):
                    group.append(item2)
                    processed.add(j)
            
            if len(group) >= min_platforms:
                # 计算综合热度
                total_hot = sum(self._parse_hot(item.hot) for item in group)
                platforms = list(set(item.platform_name for item in group))
                
                topic_groups.append({
                    "main_title": group[0].title,
                    "titles": [item.title for item in group],
                    "platforms": platforms,
                    "platform_count": len(platforms),
                    "total_hot": total_hot,
                    "items": [
                        {
                            "platform": item.platform_name,
                            "title": item.title,
                            "rank": item.index,
                            "hot": item.hot,
                            "url": item.url
                        }
                        for item in group
                    ]
                })
        
        # 按平台数量和热度排序
        topic_groups.sort(key=lambda x: (x["platform_count"], x["total_hot"]), reverse=True)
        return topic_groups[:15]
    
    def analyze_trends(self) -> List[Dict]:
        """
        分析热度趋势
        
        Returns:
            趋势分析结果
        """
        trends = []
        
        # 获取最近3次采集的数据
        history = self.storage.get_collection_history(hours=6)
        
        if len(history) < 2:
            return trends
        
        # 分析每个平台的趋势
        platform_stats = defaultdict(list)
        
        for record in history[:3]:  # 最近3次
            timestamp = record["timestamp"]
            # 这里可以获取详细数据对比
            # 简化版本：只返回采集统计
            platform_stats["collection_count"].append({
                "time": timestamp,
                "platforms": record["platform_count"],
                "items": record["item_count"]
            })
        
        return platform_stats["collection_count"]
    
    def generate_ai_insights(self, new_hotspots: List[Dict], 
                            cross_platform: List[Dict]) -> str:
        """
        生成AI洞察分析
        
        注意：这个函数在Hermes中会通过LLM调用实现
        这里返回需要分析的原始数据
        """
        insights_data = {
            "new_hotspots_count": len(new_hotspots),
            "cross_platform_count": len(cross_platform),
            "top_new": new_hotspots[:5] if new_hotspots else [],
            "top_cross": cross_platform[:3] if cross_platform else []
        }
        
        return json.dumps(insights_data, ensure_ascii=False, indent=2)
    
    def run_full_analysis(self) -> AnalysisResult:
        """
        执行完整的分析流程
        
        Returns:
            完整的分析结果
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print("\n🔍 开始分析...")
        
        # 1. 发现新热点
        print("  1️⃣ 检测新热点...")
        new_hotspots = self.find_new_hotspots()
        print(f"     发现 {len(new_hotspots)} 个新热点")
        
        # 2. 跨平台关联
        print("  2️⃣ 分析跨平台话题...")
        cross_platform = self.find_cross_platform_topics(min_platforms=2)
        print(f"     发现 {len(cross_platform)} 个跨平台话题")
        
        # 3. 各平台汇总
        print("  3️⃣ 汇总各平台数据...")
        platform_summaries = self._summarize_by_platform()
        
        # 4. 趋势分析
        print("  4️⃣ 分析趋势...")
        trends = self.analyze_trends()
        
        # 5. AI洞察数据准备
        print("  5️⃣ 准备AI分析数据...")
        ai_data = self.generate_ai_insights(new_hotspots, cross_platform)
        
        print("\n✅ 分析完成!")
        
        return AnalysisResult(
            timestamp=timestamp,
            new_hotspots=new_hotspots,
            cross_platform=cross_platform,
            platform_summaries=platform_summaries,
            trends=trends,
            ai_insights=ai_data
        )
    
    def _summarize_by_platform(self) -> Dict[str, List[Dict]]:
        """按平台汇总热点"""
        summaries = {}
        latest_data = self.storage.get_all_latest(limit_per_platform=10)
        
        for platform, items in latest_data.items():
            summaries[platform] = [
                {
                    "title": item.title,
                    "hot": item.hot,
                    "url": item.url,
                    "rank": item.index
                }
                for item in items[:10]
            ]
        
        return summaries
    
    def _normalize_title(self, title: str) -> str:
        """标准化标题用于对比"""
        # 移除特殊字符、空格，转为小写
        title = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9]', '', title)
        return title.lower().strip()
    
    def _is_similar(self, title1: str, title2: str) -> bool:
        """判断两个标题是否相似"""
        # 快速检查：如果长度差异太大，不相似
        if abs(len(title1) - len(title2)) > max(len(title1), len(title2)) * 0.5:
            return False
        
        # 使用SequenceMatcher计算相似度
        norm1 = self._normalize_title(title1)
        norm2 = self._normalize_title(title2)
        
        if not norm1 or not norm2:
            return False
        
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity >= self.similarity_threshold
    
    def _find_similar(self, title: str, candidates: Set[str]) -> str:
        """在候选集中找最相似的标题"""
        best_match = None
        best_ratio = 0
        
        norm_title = self._normalize_title(title)
        
        for candidate in candidates:
            ratio = SequenceMatcher(None, norm_title, candidate).ratio()
            if ratio > best_ratio and ratio >= self.similarity_threshold:
                best_ratio = ratio
                best_match = candidate
        
        return best_match
    
    def _parse_hot(self, hot_str: str) -> int:
        """解析热度字符串为数字"""
        if not hot_str:
            return 0
        
        try:
            # 处理 "7827.0万" 格式
            if "万" in hot_str:
                return int(float(hot_str.replace("万", "")) * 10000)
            # 处理纯数字
            return int(float(hot_str))
        except:
            return 0


if __name__ == "__main__":
    # 测试分析器
    analyzer = HotListAnalyzer()
    
    # 采集数据
    print("=" * 60)
    print("热点数据采集")
    print("=" * 60)
    analyzer.collect_all()
    
    # 运行分析
    print("\n" + "=" * 60)
    print("热点数据分析")
    print("=" * 60)
    result = analyzer.run_full_analysis()
    
    # 输出结果摘要
    print(f"\n📊 分析摘要:")
    print(f"  新热点: {len(result.new_hotspots)} 个")
    print(f"  跨平台话题: {len(result.cross_platform)} 个")
    print(f"  分析时间: {result.timestamp}")
