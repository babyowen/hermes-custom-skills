#!/usr/bin/env python3
"""
WC2026 比赛预测工具

用法:
  python3 predict.py --team1 巴西 --team2 塞尔维亚
  python3 predict.py --team1 巴西 --team2 塞尔维亚 --json
  python3 predict.py --group C
  python3 predict.py --group C --json
"""
import argparse
import json
import os
import re
import sys
sys.path.insert(0, os.path.expanduser("~/wc2026"))

REF_FILE = os.path.expanduser("~/.hermes/skills/wc2026-predictor/references/fifa-ranking-48-teams.md")

def load_team_data(team_name: str) -> dict:
    """从 entities/ 加载球队数据"""
    entity_path = os.path.expanduser(f"~/wc2026/entities/{team_name}.md")
    if not os.path.exists(entity_path):
        entity_path = os.path.expanduser(f"~/wc2026/entities/{team_name}")
    if not os.path.exists(entity_path):
        return {"error": f"未找到球队: {team_name}"}

    with open(entity_path, encoding='utf-8') as f:
        content = f.read()

    # 提取 frontmatter
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


def load_group_map() -> dict:
    """从 fifa-ranking-48-teams.md 解析小组分组（单一数据源）"""
    if not os.path.exists(REF_FILE):
        return {}

    groups = {}
    with open(REF_FILE, encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 匹配表格行: | 排名 | 中文名 | 英文名 | 积分 | 小组 |
            m = re.match(r'^\|\s*\d+\s*\|\s*(.+?)\s*\|\s*.+?\s*\|\s*[^\|]*\s*\|\s*([A-Z])组\s*\|', line)
            if m:
                team = m.group(1).strip()
                group_letter = m.group(2).strip()
                groups.setdefault(group_letter, []).append(team)
    return groups


def main():
    parser = argparse.ArgumentParser(description="WC2026 比赛预测")
    parser.add_argument("--team1", help="球队1")
    parser.add_argument("--team2", help="球队2")
    parser.add_argument("--group", help="小组字母 (A-L)")
    parser.add_argument("--json", action="store_true", help="JSON 输出")

    args = parser.parse_args()

    group_map = load_group_map()

    if args.group:
        teams = group_map.get(args.group.upper(), [])
        if not teams:
            msg = f"错误: 不存在的小组 '{args.group}' (可用 A-L)"
            if args.json:
                print(json.dumps({"error": msg}, ensure_ascii=False))
            else:
                print(msg, file=sys.stderr)
            sys.exit(1)

        matches = []
        for i in range(len(teams)):
            for j in range(i+1, len(teams)):
                matches.append(f"{teams[i]} vs {teams[j]}")

        result = {
            "group": args.group.upper(),
            "teams": teams,
            "matches": matches
        }
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"📋 {args.group.upper()} 组球队: {', '.join(teams)}")
            print(f"比赛配对 ({len(matches)}场):")
            for m in matches:
                print(f"  ⚽ {m}")
        return

    if args.team1 and args.team2:
        t1 = load_team_data(args.team1)
        t2 = load_team_data(args.team2)

        if "error" in t1:
            msg = f"错误: {t1['error']}"
            print(msg, file=sys.stderr)
            sys.exit(1)
        if "error" in t2:
            msg = f"错误: {t2['error']}"
            print(msg, file=sys.stderr)
            sys.exit(1)

        rank1 = t1.get('frontmatter', {}).get('FIFA排名', '?')
        rank2 = t2.get('frontmatter', {}).get('FIFA排名', '?')

        if args.json:
            print(json.dumps({
                "team1": {"name": args.team1, "fifa_rank": rank1},
                "team2": {"name": args.team2, "fifa_rank": rank2}
            }, ensure_ascii=False, indent=2))
        else:
            print(f"⚽ {args.team1} vs {args.team2}")
            print(f"  {args.team1}: FIFA {rank1}")
            print(f"  {args.team2}: FIFA {rank2}")
        return

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
