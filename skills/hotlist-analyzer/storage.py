#!/usr/bin/env python3
"""
热点数据存储管理模块
使用SQLite存储历史热点数据，支持查询、对比和清理
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class HotItem:
    """单条热点数据结构"""
    platform: str
    platform_name: str
    title: str
    hot: str
    url: str
    index: int
    timestamp: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> "HotItem":
        return cls(**data)


class HotListStorage:
    """热点数据存储管理器"""
    
    def __init__(self, db_path: Optional[str] = None):
        """
        初始化存储
        
        Args:
            db_path: 数据库路径，默认使用技能目录下的data/hotlist.db
        """
        if db_path is None:
            skill_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(skill_dir, "data")
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "hotlist.db")
        
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表结构"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 热点数据表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS hot_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                platform_name TEXT NOT NULL,
                title TEXT NOT NULL,
                hot TEXT,
                url TEXT,
                idx INTEGER,
                timestamp TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 采集记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collection_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                platform_count INTEGER,
                item_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 创建索引加速查询
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON hot_items(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_platform ON hot_items(platform)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_title ON hot_items(title)")
        
        conn.commit()
        conn.close()
    
    def save_hotlist(self, platform: str, platform_name: str, 
                     items: List[Dict], timestamp: Optional[str] = None):
        """
        保存热榜数据
        
        Args:
            platform: 平台key
            platform_name: 平台名称
            items: 热点列表
            timestamp: 时间戳，默认使用当前时间
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in items:
            cursor.execute("""
                INSERT INTO hot_items 
                (platform, platform_name, title, hot, url, idx, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                platform,
                platform_name,
                item.get("title", ""),
                item.get("hot", ""),
                item.get("url", ""),
                int(item.get("index", 0)),
                timestamp
            ))
        
        conn.commit()
        conn.close()
    
    def get_latest_by_platform(self, platform: str, 
                               limit: int = 50) -> Tuple[str, List[HotItem]]:
        """
        获取指定平台的最新数据
        
        Returns:
            (timestamp, items)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取最新时间戳
        cursor.execute("""
            SELECT timestamp FROM hot_items 
            WHERE platform = ? 
            ORDER BY timestamp DESC LIMIT 1
        """, (platform,))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None, []
        
        latest_time = result[0]
        
        # 获取该时间点的数据
        cursor.execute("""
            SELECT platform, platform_name, title, hot, url, idx, timestamp
            FROM hot_items 
            WHERE platform = ? AND timestamp = ?
            ORDER BY idx ASC
            LIMIT ?
        """, (platform, latest_time, limit))
        
        items = []
        for row in cursor.fetchall():
            items.append(HotItem(*row))
        
        conn.close()
        return latest_time, items
    
    def get_previous_by_platform(self, platform: str, 
                                  current_time: str,
                                  limit: int = 50) -> Tuple[str, List[HotItem]]:
        """
        获取指定平台上一次的数据（用于对比）
        
        Args:
            platform: 平台key
            current_time: 当前时间戳，找这个时间之前的数据
            limit: 返回条数
            
        Returns:
            (timestamp, items)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取当前时间之前最新的一次数据
        cursor.execute("""
            SELECT DISTINCT timestamp FROM hot_items 
            WHERE platform = ? AND timestamp < ?
            ORDER BY timestamp DESC LIMIT 1
        """, (platform, current_time))
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None, []
        
        prev_time = result[0]
        
        # 获取该时间点的数据
        cursor.execute("""
            SELECT platform, platform_name, title, hot, url, idx, timestamp
            FROM hot_items 
            WHERE platform = ? AND timestamp = ?
            ORDER BY idx ASC
            LIMIT ?
        """, (platform, prev_time, limit))
        
        items = []
        for row in cursor.fetchall():
            items.append(HotItem(*row))
        
        conn.close()
        return prev_time, items
    
    def get_all_latest(self, limit_per_platform: int = 30) -> Dict[str, List[HotItem]]:
        """
        获取所有平台的最新数据
        
        Returns:
            {platform: [HotItem, ...]}
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 获取每个平台最新时间戳
        cursor.execute("""
            SELECT platform, MAX(timestamp) as latest_time
            FROM hot_items
            GROUP BY platform
        """)
        
        platform_times = cursor.fetchall()
        result = {}
        
        for platform, latest_time in platform_times:
            cursor.execute("""
                SELECT platform, platform_name, title, hot, url, idx, timestamp
                FROM hot_items 
                WHERE platform = ? AND timestamp = ?
                ORDER BY idx ASC
                LIMIT ?
            """, (platform, latest_time, limit_per_platform))
            
            items = []
            for row in cursor.fetchall():
                items.append(HotItem(*row))
            
            result[platform] = items
        
        conn.close()
        return result
    
    def log_collection(self, timestamp: str, platform_count: int, item_count: int):
        """记录采集日志"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO collection_logs (timestamp, platform_count, item_count)
            VALUES (?, ?, ?)
        """, (timestamp, platform_count, item_count))
        
        conn.commit()
        conn.close()
    
    def get_collection_history(self, hours: int = 24) -> List[Dict]:
        """获取采集历史记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute("""
            SELECT timestamp, platform_count, item_count, created_at
            FROM collection_logs
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
        """, (since,))
        
        history = []
        for row in cursor.fetchall():
            history.append({
                "timestamp": row[0],
                "platform_count": row[1],
                "item_count": row[2],
                "created_at": row[3]
            })
        
        conn.close()
        return history
    
    def clean_old_data(self, days: int = 7):
        """清理过期数据"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")
        
        # 删除旧的热点数据
        cursor.execute("DELETE FROM hot_items WHERE timestamp < ?", (cutoff,))
        hot_deleted = cursor.rowcount
        
        # 删除旧的日志
        cursor.execute("DELETE FROM collection_logs WHERE timestamp < ?", (cutoff,))
        log_deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return {"hot_items_deleted": hot_deleted, "logs_deleted": log_deleted}
    
    def get_stats(self) -> Dict:
        """获取数据库统计信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM hot_items")
        total_items = cursor.fetchone()[0]
        
        # 平台数量
        cursor.execute("SELECT COUNT(DISTINCT platform) FROM hot_items")
        platform_count = cursor.fetchone()[0]
        
        # 时间范围
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM hot_items")
        time_range = cursor.fetchone()
        
        # 采集次数
        cursor.execute("SELECT COUNT(*) FROM collection_logs")
        collection_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_items": total_items,
            "platform_count": platform_count,
            "earliest": time_range[0],
            "latest": time_range[1],
            "collection_count": collection_count
        }


if __name__ == "__main__":
    # 测试存储功能
    storage = HotListStorage()
    
    # 保存测试数据
    test_items = [
        {"title": "测试热点1", "hot": "100万", "url": "http://test1.com", "index": 1},
        {"title": "测试热点2", "hot": "90万", "url": "http://test2.com", "index": 2},
    ]
    
    storage.save_hotlist("test", "测试平台", test_items)
    
    # 查询
    timestamp, items = storage.get_latest_by_platform("test")
    print(f"最新数据时间: {timestamp}")
    for item in items:
        print(f"  {item.index}. {item.title} [{item.hot}]")
    
    # 统计
    stats = storage.get_stats()
    print(f"\n统计: {stats}")
