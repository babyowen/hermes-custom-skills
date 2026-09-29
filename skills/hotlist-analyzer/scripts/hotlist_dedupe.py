#!/usr/bin/env python3
"""热榜条目去重（早晚两期不重复报同一件事）。

状态文件：~/.hermes/cache/hotlist/state.json
指纹规则：标题归一化（去空白/标点/emoji，转小写）后取前 20 字符；
          两条标题若一方是另一方的前缀（≥10 字符）也判为同一件事。

用法：
  # 检查候选：输入 JSON（["标题1", "标题2"] 或 [{"title": "..."}]）
  python3 hotlist_dedupe.py --check /tmp/candidates.json
  # 报告发出后回写：把本期已报条目登记进状态
  python3 hotlist_dedupe.py --mark /tmp/reported.json
  # 查看状态
  python3 hotlist_dedupe.py --show

输出：JSON（{ok, new|marked, duplicates, state_path, window_hours}）；出错 exit 1。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

STATE = os.path.expanduser('~/.hermes/cache/hotlist/state.json')
WINDOW_HOURS = 48
_PUNCT = re.compile(r'[^\w\u4e00-\u9fff]+')


def norm(title: str) -> str:
    """标题归一化：去标点空白、统一小写，保留中英文与数字。"""
    return _PUNCT.sub('', str(title or '')).lower()


def fp(title: str) -> str:
    return norm(title)[:20]


def load_state(path: str = STATE) -> list:
    try:
        with open(path, encoding='utf-8') as fh:
            data = json.load(fh)
        return data if isinstance(data, list) else []
    except FileNotFoundError:
        return []
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({'ok': False, 'error': 'state 无法解析: %s' % exc}, ensure_ascii=False))
        sys.exit(1)


def prune(items: list, window_hours: int) -> list:
    cutoff = time.time() - window_hours * 3600
    return [it for it in items if it.get('last_reported_ts', 0) >= cutoff]


def titles_of(path: str) -> list:
    with open(path, encoding='utf-8') as fh:
        data = json.load(fh)
    out = []
    for x in data if isinstance(data, list) else []:
        if isinstance(x, str):
            out.append(x)
        elif isinstance(x, dict):
            t = x.get('title') or x.get('name') or ''
            if t:
                out.append(str(t))
    return out


def is_dup(cand_norm: str, state_norm: str) -> bool:
    if not cand_norm or not state_norm:
        return False
    if cand_norm == state_norm:
        return True
    short, long_ = (cand_norm, state_norm) if len(cand_norm) <= len(state_norm) else (state_norm, cand_norm)
    return len(short) >= 10 and long_.startswith(short)


def main() -> int:
    ap = argparse.ArgumentParser(description='热榜条目去重')
    ap.add_argument('--check', metavar='FILE', help='候选标题 JSON，输出哪些是新的')
    ap.add_argument('--mark', metavar='FILE', help='本期已报标题 JSON，登记进状态')
    ap.add_argument('--show', action='store_true', help='打印当前状态')
    ap.add_argument('--window-hours', type=int, default=WINDOW_HOURS)
    ap.add_argument('--state', default=STATE)
    ap.add_argument('--json', action='store_true')
    args = ap.parse_args()

    state_path = os.path.expanduser(args.state)
    items = prune(load_state(state_path), args.window_hours)
    known = [(it, norm(it.get('title', ''))) for it in items]

    try:
        if args.check:
            new, dup = [], []
            for t in titles_of(args.check):
                cn = norm(t)
                hit = next((it for it, sn in known if is_dup(cn, sn)), None)
                if hit:
                    dup.append({'title': t, 'seen_before': hit.get('title'),
                                'last_reported': hit.get('last_reported')})
                else:
                    new.append(t)
            result = {'ok': True, 'state_path': state_path, 'window_hours': args.window_hours,
                      'new': new, 'duplicates': dup, 'new_count': len(new), 'dup_count': len(dup)}
        elif args.mark:
            now = time.time()
            stamp = time.strftime('%Y-%m-%d %H:%M', time.localtime(now))
            marked = 0
            for t in titles_of(args.mark):
                cn, f = norm(t), fp(t)
                hit = next((it for it in items if is_dup(cn, norm(it.get('title', '')))), None)
                if hit:
                    hit['last_reported'] = stamp
                    hit['last_reported_ts'] = now
                    hit['count'] = int(hit.get('count', 1)) + 1
                else:
                    items.append({'fp': f, 'title': t, 'first_seen': stamp,
                                  'last_reported': stamp, 'last_reported_ts': now, 'count': 1})
                marked += 1
            os.makedirs(os.path.dirname(state_path), exist_ok=True)
            with open(state_path, 'w', encoding='utf-8') as fh:
                json.dump(items, fh, ensure_ascii=False, indent=1)
            result = {'ok': True, 'state_path': state_path, 'window_hours': args.window_hours,
                      'marked': marked, 'state_size': len(items)}
        elif args.show:
            result = {'ok': True, 'state_path': state_path, 'window_hours': args.window_hours,
                      'items': items}
        else:
            ap.print_help()
            return 0
    except FileNotFoundError as exc:
        print(json.dumps({'ok': False, 'error': '输入文件不存在: %s' % exc}, ensure_ascii=False))
        return 1
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False))
        return 1

    if args.json or True:
        print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
