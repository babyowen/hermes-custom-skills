#!/usr/bin/env python3
"""agent-router-models 技能验收测试（只读接口；只写 /tmp，不用管道/heredoc）。

用法: python3 scripts/selftest.py    # 退出码 0=全通过，1=有失败项
"""
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "check_models.py")

spec = importlib.util.spec_from_file_location("cm", SCRIPT)
cm = importlib.util.module_from_spec(spec)  # type: ignore
spec.loader.exec_module(cm)                 # type: ignore

results = []


def rec(name, ok, detail):
    results.append((name, ok, detail))


def run_cli(args):
    p = subprocess.run([sys.executable, SCRIPT] + args, capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def call_fail(desc, fn):
    buf = io.StringIO()
    code = None
    try:
        with contextlib.redirect_stdout(buf):
            fn()
    except SystemExit as exc:
        code = exc.code
    payload = {}
    try:
        payload = json.loads(buf.getvalue())
    except Exception:
        pass
    rec(desc, code == 1 and payload.get("_run_failed") is True,
        "exit=%s error=%s" % (code, payload.get("error")))


# A. 不变场景：把今日快照改造成基线后重跑
d_a = "/tmp/ar_selftest_a"
os.makedirs(d_a, exist_ok=True)
run_cli(["--cache-dir", d_a])
snap_dir = os.path.join(d_a, "snapshots")
today_file = os.path.join(snap_dir, "2026-09-22.json")
if os.path.exists(today_file):
    snap = json.load(open(today_file, encoding="utf-8"))
    snap["date"] = "2026-09-21"
    json.dump(snap, open(os.path.join(snap_dir, "2026-09-21.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    os.remove(today_file)
rc, out, err = run_cli(["--cache-dir", d_a])
try:
    d = json.loads(out)
    rec("A 无变化场景 → verdict=unchanged",
        rc == 0 and d["verdict"] == "unchanged" and not d["added"] and not d["removed"] and not d["changed"],
        "verdict=%s added=%d removed=%d changed=%d unchanged=%s"
        % (d["verdict"], len(d["added"]), len(d["removed"]), len(d["changed"]), d["unchanged_count"]))
except Exception as exc:
    rec("A 无变化场景", False, "解析失败 %s | stderr=%s" % (exc, err[:200]))

# B. 错误 Key → 401 → exit 1
call_fail("B 错误 Key → HTTP 401 → exit 1",
          lambda: cm.fetch_models("http://api.agent-router.cn/v1", "sk-this-key-is-invalid-000"))

# C. 主机不可达 → exit 1
call_fail("C 主机不可达 → exit 1",
          lambda: cm.fetch_models("http://127.0.0.1:9/v1", "sk-x"))

# D. 指定的基线快照不存在 → exit 1（不能抛裸异常）
rc_d, out_d, _ = run_cli(["--cache-dir", "/tmp/ar_selftest_d", "--baseline", "1999-01-01"])
try:
    pd = json.loads(out_d)
except Exception:
    pd = {}
rec("D 基线快照缺失 → exit 1",
    rc_d == 1 and pd.get("_run_failed") is True and "不存在" in str(pd.get("error")),
    "exit=%s error=%s" % (rc_d, pd.get("error")))

# E. --history / --list 可用
rc_h, out_h, _ = run_cli(["--cache-dir", d_a, "--history"])
rc_l, out_l, _ = run_cli(["--cache-dir", "/tmp/ar_selftest_e", "--list"])
try:
    hist, lst = json.loads(out_h), json.loads(out_l)
    rec("E --history / --list 可用",
        rc_h == 0 and rc_l == 0 and hist["count"] >= 1 and lst["total"] > 0,
        "history=%s list_total=%s" % (hist["dates"], lst["total"]))
except Exception as exc:
    rec("E --history / --list", False, str(exc))

# F. --keep 生效且正常返回
rc_k, _, _ = run_cli(["--cache-dir", "/tmp/ar_selftest_f", "--keep", "1"])
left = sorted(os.listdir("/tmp/ar_selftest_f/snapshots")) if os.path.isdir("/tmp/ar_selftest_f/snapshots") else []
rec("F --keep 参数生效", rc_k == 0 and len(left) <= 1, "snapshots=%s" % left)

print("=" * 60)
fails = 0
for name, ok, detail in results:
    print(("PASS  " if ok else "FAIL  ") + name + "  |  " + detail)
    fails += 0 if ok else 1
print("=" * 60)
print("TOTAL: %d 项，失败 %d 项" % (len(results), fails))
sys.exit(1 if fails else 0)
