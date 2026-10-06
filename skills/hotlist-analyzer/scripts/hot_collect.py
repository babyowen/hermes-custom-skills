#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hot_collect.py — 8 平台热榜采集（纯标准库，cron / 交互通用）

为什么存在：以前每次运行都让 LLM 现写一个一次性脚本丢到 /tmp，命名靠编，撞上历史残留就会触发
write_file 的「陈旧写保护」而写盘失败（2026-10-06 实例：/tmp/hot_collect_100500.py 与 10-03 残留重名）。
采集逻辑是稳定的，固化成脚本后：不写临时文件、不撞名、省 token、平台清单只维护一处。

用法:
  python3 hot_collect.py                      # 人读：逐平台打印 TOP20（默认）
  python3 hot_collect.py --top 30             # 只看前 30 条
  python3 hot_collect.py --json               # 机器读：JSON 打到 stdout
  python3 hot_collect.py --platforms toutiao,zhihuDay
  python3 hot_collect.py --timeout 20 --retries 2
  python3 hot_collect.py --no-save            # 不落原始快照

退出码: 0=全部平台正常 ｜ 2=部分平台失败（报告里标 ⚠️ 降级运行）｜ 1=全部平台失败

原始快照默认落到 ~/.hermes/cache/hotlist/raw_<YYYYMMDD-HHMM>.json（带时间戳，天然不重名）
"""
import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime

PLATFORMS = ["toutiao", "douyinHot", "pengPai", "qqNews", "itNews", "zhihuDay", "huXiu", "chongBluo"]
BASE = "https://hot-api.vhan.eu.org/v2?type="
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
DEFAULT_SNAPSHOT_DIR = os.path.expanduser("~/.hermes/cache/hotlist")


def fetch(platform, timeout, retries):
    """返回 (items, err)。items 为规范化后的列表；err 为 None 表示成功。"""
    last = "unknown"
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(BASE + platform, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read().decode("utf-8", "replace")
            d = json.loads(raw)
            if isinstance(d, dict) and isinstance(d.get("data"), list) and d["data"]:
                items = []
                for it in d["data"]:
                    if not isinstance(it, dict):
                        continue
                    items.append({
                        "title": str(it.get("title", "")).strip().replace("\n", " "),
                        # hot 可能是字符串（"5098.1万"）也可能是数值
                        "hot": str(it.get("hot", "")),
                        "url": str(it.get("url") or it.get("mobilUrl") or it.get("link") or ""),
                        "desc": str(it.get("desc") or it.get("digest") or "").strip().replace("\n", " ")[:200],
                    })
                return items, None
            last = "空返回或结构异常: " + raw[:160].replace("\n", " ")
        except Exception as e:  # noqa: BLE001 - 网络异常种类多，统一降级
            last = "%s: %s" % (type(e).__name__, str(e)[:160])
        if attempt < retries:
            time.sleep(1)
    return [], last


def main():
    ap = argparse.ArgumentParser(description="8 平台热榜采集")
    ap.add_argument("--platforms", default=",".join(PLATFORMS),
                    help="逗号分隔，默认全部 8 个：" + ",".join(PLATFORMS))
    ap.add_argument("--timeout", type=float, default=15.0, help="单平台超时秒数（默认 15）")
    ap.add_argument("--retries", type=int, default=1, help="每平台失败重试次数（默认 1）")
    ap.add_argument("--top", type=int, default=20, help="人读模式每平台打印条数（默认 20）")
    ap.add_argument("--json", dest="as_json", action="store_true", help="输出 JSON（机器读）")
    ap.add_argument("--no-save", dest="save", action="store_false", help="不落原始快照")
    ap.add_argument("--snapshot", default=None, help="原始快照路径（默认 ~/.hermes/cache/hotlist/raw_<时间戳>.json）")
    a = ap.parse_args()

    plats = [p.strip() for p in a.platforms.split(",") if p.strip()]
    if not plats:
        print("错误: --platforms 为空", file=sys.stderr)
        return 1

    result, failed = {}, []
    for p in plats:
        items, err = fetch(p, a.timeout, a.retries)
        if err is None:
            result[p] = {"ok": True, "count": len(items), "items": items}
        else:
            result[p] = {"ok": False, "count": 0, "items": [], "error": err}
            failed.append(p)

    ok_n = len(plats) - len(failed)
    total_n = sum(v["count"] for v in result.values())
    payload = {
        "ok": ok_n == len(plats),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "stats": {"platforms_n": len(plats), "ok_n": ok_n, "failed": failed, "total_n": total_n},
        "platforms": result,
    }

    snapshot = None
    if a.save:
        snapshot = a.snapshot or os.path.join(
            DEFAULT_SNAPSHOT_DIR, "raw_%s.json" % datetime.now().strftime("%Y%m%d-%H%M"))
        try:
            os.makedirs(os.path.dirname(snapshot), exist_ok=True)
            with open(snapshot, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=1)
        except Exception as e:  # noqa: BLE001 - 快照失败不影响采集结果
            snapshot = None
            print("⚠️ 快照写入失败（不影响采集）: %s" % e, file=sys.stderr)

    if a.as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=1))
    else:
        for p in plats:
            v = result[p]
            print("=" * 8, p, "=" * 8)
            if not v["ok"]:
                print("  ⚠️ 失败:", v["error"])
                continue
            for i, it in enumerate(v["items"][:a.top], 1):
                print("%d. [%s] %s" % (i, it["hot"], it["title"]))
                if it["url"]:
                    print("   URL:", it["url"])
                if it["desc"]:
                    print("   DESC:", it["desc"][:120])
        print("-" * 40)
        print("采集状态 %d/%d 平台正常 ｜ 共 %d 条%s"
              % (ok_n, len(plats), total_n,
                 (" ｜ ⚠️ 降级: " + ",".join(failed)) if failed else " ｜ 无降级"))
        if snapshot:
            print("原始快照:", snapshot)

    if ok_n == 0:
        return 1          # 全部失败
    if failed:
        return 2          # 部分失败 → 报告里标 ⚠️ 降级运行
    return 0


if __name__ == "__main__":
    sys.exit(main())
