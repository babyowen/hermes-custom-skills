#!/usr/bin/env python3
"""
WC2026 比赛预测工具

用法:
  python3 predict.py --team1 巴西 --team2 塞尔维亚
  python3 predict.py --group C
  python3 predict.py --team1 巴西 --team2 塞尔维亚 --json
"""
import argparse
import json
import os
import sys
sys.path.insert(0, os.path.expanduser("~/wc2026"))

def load_team_data(team_name: str) -> dict:
    """从 entities/ 加载球队数据"""
    entity_path = os.path.expanduser(f"~/wc2026/entities/{team_name}.md")
    if not os.path.exists(entity_path):
        # 尝试去除.md后缀
        entity_path = os.path.expanduser(f"~/wc2026/entities/{team_name}")
    if not os.path.exists(entity_path):
        return {"error": f"未找到球队: {team_name}"}
    
    with open(entity_path) as f:
        content = f.read()
    
    # 提取 frontmatter
    import re
    fm_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    fm = {}
    if fm_match:
        for line in fm_match.group(1).split('\n'):
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"').strip("'")
    
    return {
        "name": team_name,
        "frontmatter": fm,
        "content": content
    }

def get_group_teams(group: str) -> list:
    """获取某小组的所有球队"""
    group_map = {
        "A": ["墨西哥", "韩国", "南非", "捷克"],
        "B": ["加拿大", "瑞士", "卡塔尔", "波黑"],
        "C": ["巴西", "摩洛哥", "苏格兰", "海地"],
        "D": ["美国", "巴拉圭", "澳大利亚", "土耳其"],
        "E": ["德国", "厄瓜多尔", "科特迪瓦", "库拉索"],
        "F": ["荷兰", "日本", "突尼斯", "瑞典"],
        "G": ["比利时", "伊朗", "埃及", "新西兰"],
        "H": ["西班牙", "乌拉圭", "沙特阿拉伯", "佛得角"],
        "I": ["法国", "塞内加尔", "挪威", "伊拉克"],
        "J": ["阿根廷", "奥地利", "阿尔及利亚", "约旦"],
        "K": ["葡萄牙", "哥伦比亚", "乌兹别克斯坦", "刚果（金）"],
        "L": ["英格兰", "克罗地亚", "巴拿马", "加纳"],
    }
    return group_map.get(group.upper(), [])

def main():
    parser = argparse.ArgumentParser(description="WC2026 比赛预测")
    parser.add_argument("--team1", help="球队1")
    parser.add_argument("--team2", help="球队2")
    parser.add_argument("--group", help="小组字母 (A-L)")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    
    args = parser.parse_args()
    
    if args.group:
        teams = get_group_teams(args.group)
        result = {
            "group": args.group.upper(),
            "teams": teams,
            "matches": []
        }
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                result["matches"].append(f"{teams[i]} vs {teams[j]}")
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📋 {args.group.upper()} 组球队: {', '.join(teams)}")
            print(f"比赛配对 ({len(result['matches'])}场):")
            for m in result["matches"]:
                print(f"  ⚽ {m}")
        return
    
    if args.team1 and args.team2:
        t1 = load_team_data(args.team1)
        t2 = load_team_data(args.team2)
        print(f"⚽ {args.team1} vs {args.team2}")
        print(f"  {args.team1}: FIFA {t1.get('frontmatter', {}).get('FIFA排名', '?')}")
        print(f"  {args.team2}: FIFA {t2.get('frontmatter', {}).get('FIFA排名', '?')}")
        return
    
    parser.print_help()

if __name__ == "__main__":
    main()
