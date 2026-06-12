#!/usr/bin/env python3
"""
HotList Analyzer 命令行入口
提供采集、分析、深度分析、报告生成的一体化操作
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import argparse
import json
from datetime import datetime

from storage import HotListStorage
from analyzer import HotListAnalyzer
from reporter import HotListReporter


def cmd_collect(args):
    """采集数据命令"""
    print("=" * 70)
    print("🚀 开始采集全网热点数据")
    print("=" * 70)
    
    analyzer = HotListAnalyzer()
    results = analyzer.collect_all()
    
    print(f"\n✅ 采集完成！共 {len(results)} 个平台")
    
    return results


def cmd_analyze(args):
    """基础分析命令"""
    storage = HotListStorage()
    analyzer = HotListAnalyzer(storage)
    reporter = HotListReporter()
    
    # 检查是否需要先采集
    stats = storage.get_stats()
    if stats["collection_count"] == 0 or args.refresh:
        print("⚠️  没有找到历史数据，先执行采集...\n")
        analyzer.collect_all()
    
    print("=" * 70)
    print("🔍 开始基础热点分析")
    print("=" * 70)
    
    # 执行分析
    result = analyzer.run_full_analysis()
    
    # 生成报告
    print("\n📝 生成报告...")
    report = reporter.generate_report(result, include_ai_analysis=not args.no_ai)
    
    # 显示精简版
    print("\n" + "=" * 70)
    print("📊 分析摘要")
    print("=" * 70)
    
    compact = reporter.generate_compact_summary(result)
    print(compact)
    
    # 保存完整报告
    if args.output:
        filepath = args.output
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n💾 完整报告已保存: {filepath}")
    else:
        filepath = reporter.save_report(report, result.timestamp.replace(":", "").replace(" ", "_"))
        print(f"\n💾 完整报告已保存: {filepath}")
    
    # 是否打印完整报告
    if args.verbose:
        print("\n" + "=" * 70)
        print("📄 完整报告")
        print("=" * 70)
        print(report)
    
    return result


def cmd_deep(args):
    """
    深度分析命令 - 整合AI分析
    
    这个命令会：
    1. 采集所有平台数据
    2. 检测新热点和跨平台热点
    3. 生成适合AI分析的提示词
    4. 输出结构化的分析数据（供Hermes AI进一步处理）
    """
    print("=" * 70)
    print("🔥 启动深度智能分析")
    print("=" * 70)
    
    storage = HotListStorage()
    analyzer = HotListAnalyzer(storage)
    
    # Step 1: 采集数据
    print("\n📥 Step 1: 采集全网热点...")
    collected = analyzer.collect_all()
    
    # Step 2: 基础分析
    print("\n🔍 Step 2: 基础分析（新热点 + 跨平台）...")
    new_hotspots = analyzer.find_new_hotspots()
    cross_platform = analyzer.find_cross_platform_topics(min_platforms=2)
    
    print(f"   🆕 新热点: {len(new_hotspots)} 个")
    print(f"   🌐 跨平台: {len(cross_platform)} 个")
    
    # Step 3: 准备AI分析数据
    print("\n🤖 Step 3: 准备AI深度分析...")
    
    # 合并优先级热点
    priority_items = []
    
    # 添加跨平台热点（优先级更高）
    for topic in cross_platform[:5]:
        priority_items.append({
            "title": topic["main_title"],
            "platforms": topic.get("platforms", []),
            "platform": f"跨平台({topic.get('platform_count', 0)}个)",
            "hot": f"{topic.get('total_hot', 0)/10000:.0f}万",
            "url": topic.get("items", [{}])[0].get("url", ""),
            "type": "cross_platform",
            "platform_details": topic.get("items", [])
        })
    
    # 添加新热点
    for hotspot in new_hotspots[:10]:
        # 检查是否已存在（去重）
        is_duplicate = any(
            h["title"] == hotspot["title"] for h in priority_items
        )
        if not is_duplicate:
            priority_items.append({
                "title": hotspot["title"],
                "platform": hotspot.get("platform", ""),
                "hot": hotspot.get("hot", ""),
                "url": hotspot.get("url", ""),
                "rank": hotspot.get("rank", 0),
                "change": hotspot.get("change", ""),
                "type": "new"
            })
    
    # Step 4: 生成AI分析提示词
    print(f"\n📝 Step 4: 生成AI分析提示词（共{len(priority_items)}条）...")
    
    from ai_analyzer import create_hermes_analysis_prompt
    ai_prompt = create_hermes_analysis_prompt(priority_items)
    
    # 保存数据供Hermes使用
    analysis_data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "platforms": len(collected),
            "new_hotspots": len(new_hotspots),
            "cross_platform": len(cross_platform),
            "priority_items": len(priority_items)
        },
        "priority_items": priority_items,
        "new_hotspots": new_hotspots[:15],
        "cross_platform": cross_platform[:8],
        "platform_summaries": analyzer._summarize_by_platform(),
        "ai_analysis_prompt": ai_prompt
    }
    
    # 保存JSON数据
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    data_file = f"{skill_dir}/data/latest_analysis.json"
    
    os.makedirs(os.path.dirname(data_file), exist_ok=True)
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(analysis_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 分析数据已保存: {data_file}")
    
    # Step 5: 输出AI提示词（供Hermes使用）
    print("\n" + "=" * 70)
    print("🤖 AI深度分析提示词（请复制给AI进行分析）")
    print("=" * 70)
    print(ai_prompt)
    
    # 如果指定了输出文件，也保存提示词
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(ai_prompt)
        print(f"\n💾 AI提示词已保存: {args.output}")
    
    return analysis_data


def cmd_stats(args):
    """查看统计信息命令"""
    storage = HotListStorage()
    stats = storage.get_stats()
    
    print("=" * 70)
    print("📈 数据库统计")
    print("=" * 70)
    print(f"总记录数: {stats['total_items']:,}")
    print(f"平台数量: {stats['platform_count']}")
    print(f"采集次数: {stats['collection_count']}")
    print(f"最早数据: {stats['earliest']}")
    print(f"最新数据: {stats['latest']}")
    
    # 显示最近采集历史
    print("\n📅 最近采集记录:")
    history = storage.get_collection_history(hours=24)
    for record in history[:5]:
        print(f"  {record['timestamp']}: {record['platform_count']}平台, {record['item_count']}条")


def cmd_clean(args):
    """清理数据命令"""
    storage = HotListStorage()
    days = args.days or 7
    
    print(f"🧹 清理 {days} 天前的数据...")
    result = storage.clean_old_data(days)
    
    print(f"✅ 清理完成")
    print(f"  删除热点数据: {result['hot_items_deleted']} 条")
    print(f"  删除日志记录: {result['logs_deleted']} 条")


def cmd_interactive(args):
    """交互模式"""
    print("=" * 70)
    print("🎯 HotList Analyzer 交互模式")
    print("=" * 70)
    print("\n可用命令:")
    print("  1 - 采集数据")
    print("  2 - 基础分析")
    print("  3 - 深度分析（含AI提示词）")
    print("  4 - 查看统计")
    print("  5 - 清理数据")
    print("  q - 退出")
    print()
    
    while True:
        choice = input("请输入命令 [1/2/3/4/5/q]: ").strip().lower()
        
        if choice == "1":
            cmd_collect(None)
        elif choice == "2":
            cmd_analyze(argparse.Namespace(refresh=False, no_ai=False, output=None, verbose=False))
        elif choice == "3":
            cmd_deep(argparse.Namespace(output=None))
        elif choice == "4":
            cmd_stats(None)
        elif choice == "5":
            days = input("清理多少天前的数据? [默认7]: ").strip()
            cmd_clean(argparse.Namespace(days=int(days) if days else 7))
        elif choice == "q":
            print("👋 再见!")
            break
        else:
            print("❌ 无效命令")
        
        print()


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="HotList Analyzer - 智能热点追踪分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 采集数据
  python3 cli.py collect
  
  # 基础分析
  python3 cli.py analyze
  
  # 深度分析（生成AI提示词）
  python3 cli.py deep
  
  # 深度分析并保存提示词
  python3 cli.py deep -o ai_prompt.txt
  
  # 查看统计
  python3 cli.py stats
  
  # 交互模式
  python3 cli.py interactive
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # collect 命令
    collect_parser = subparsers.add_parser("collect", help="采集全网热点数据")
    collect_parser.set_defaults(func=cmd_collect)
    
    # analyze 命令
    analyze_parser = subparsers.add_parser("analyze", help="基础热点分析")
    analyze_parser.add_argument("--refresh", "-r", action="store_true", 
                               help="先刷新数据再分析")
    analyze_parser.add_argument("--no-ai", action="store_true",
                               help="不包含AI分析部分")
    analyze_parser.add_argument("--output", "-o", type=str,
                               help="输出文件路径")
    analyze_parser.add_argument("--verbose", "-v", action="store_true",
                               help="显示完整报告")
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # deep 命令（新）
    deep_parser = subparsers.add_parser("deep", help="深度分析（生成AI提示词）")
    deep_parser.add_argument("--output", "-o", type=str,
                            help="保存AI提示词到文件")
    deep_parser.set_defaults(func=cmd_deep)
    
    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="查看数据统计")
    stats_parser.set_defaults(func=cmd_stats)
    
    # clean 命令
    clean_parser = subparsers.add_parser("clean", help="清理过期数据")
    clean_parser.add_argument("--days", "-d", type=int,
                             help="清理多少天前的数据 (默认7天)")
    clean_parser.set_defaults(func=cmd_clean)
    
    # interactive 命令
    interactive_parser = subparsers.add_parser("interactive", help="交互模式")
    interactive_parser.set_defaults(func=cmd_interactive)
    
    args = parser.parse_args()
    
    if args.command:
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
