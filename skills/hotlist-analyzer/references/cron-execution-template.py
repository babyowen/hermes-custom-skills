#!/usr/bin/env python3
"""
hotlist-analyzer: 8平台热点采集模板（async 并行版）
被 SKILL.md Cron执行流程 Step 1 引用。
每次执行时直接运行，禁止读本地缓存文件。

相比同步 for 循环，async 并行约 1.6 秒完成（同步约 5-8 秒）。
"""
import asyncio
import httpx
import json
from datetime import datetime

PLATFORMS = {
    "toutiao": "今日头条",
    "douyinHot": "抖音热点",
    "pengPai": "澎湃新闻",
    "qqNews": "腾讯新闻",
    "itNews": "IT之家",
    "zhihuDay": "知乎日报",
    "huXiu": "虎嗅",
    "chongBluo": "虫部落",
}

BASE_URL = "https://hot-api.vhan.eu.org/v2"


async def fetch_one(client: httpx.AsyncClient, key: str, name: str) -> dict:
    """采集单平台，返回 {平台名: 数据}"""
    url = f"{BASE_URL}?type={key}"
    try:
        resp = await client.get(url, timeout=10)
        data = resp.json()
        items = data.get("data", [])
        if isinstance(items, list):
            return {
                name: {
                    "count": len(items),
                    "update_time": data.get("update_time", "?"),
                    "top5": [
                        {
                            "title": i["title"],
                            "hot": i.get("hot", ""),
                            "url": i.get("url", ""),
                        }
                        for i in items[:5]
                    ],
                }
            }
        return {name: {"count": 0, "error": "data not list"}}
    except Exception as e:
        return {name: {"error": str(e)}}


async def collect_all() -> dict:
    """并行采集所有平台"""
    async with httpx.AsyncClient() as client:
        tasks = [fetch_one(client, key, name) for key, name in PLATFORMS.items()]
        results_list = await asyncio.gather(*tasks)
    results = {}
    for r in results_list:
        results.update(r)
    return results


def main():
    results = asyncio.run(collect_all())
    print(f"=== 热点采集报告 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===")
    for name, data in results.items():
        status = "❌" if "error" in data else "✅"
        detail = data.get("error", f"{data['count']}条")
        print(f"  {status} {name} ({detail})")
        if "error" not in data and data.get("top5"):
            for item in data["top5"][:3]:
                print(f"      [{item['hot']}] {item['title']}")


if __name__ == "__main__":
    main()
