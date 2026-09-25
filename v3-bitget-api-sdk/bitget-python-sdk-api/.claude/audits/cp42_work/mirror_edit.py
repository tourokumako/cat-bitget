#!/usr/bin/env python3
"""mirror_edit.py — 写しのファイルを壊す・戻す（run.sh から呼ぶ・本物は触らない）。"""
import hashlib, json, pathlib, re, shutil, sys
M = pathlib.Path('/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/mirror')
PR = pathlib.Path('/Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api/.claude/audits/cp42_work/pristine')
KEYS = {"aaf": ".claude/tools/apply_audit_fix.py", "gen_acc": ".claude/tools/gen_acceptance.py", "gad": ".claude/tools/gen_audit_docs.py", "acc": ".claude/state/acceptance.md", "approved": ".claude/state/acceptance.approved", "src": "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json", "b101": ".claude/breaks/b101_design_apply_no_approval.sh", "b102": ".claude/breaks/b102_design_apply_no_precheck.sh", "lib": ".claude/breaks/lib.sh"}
def sha(p): return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def path(k):
    if k not in KEYS: raise SystemExit("unknown key: " + k + " (keys=" + ",".join(KEYS) + ")")
    return M / KEYS[k]
cmd, args = sys.argv[1], sys.argv[2:]
if cmd == "path":
    print(path(args[0]))
elif cmd == "hash":
    p = path(args[0]); print("now     ", sha(p)); print("pristine", sha(PR / args[0]), "same" if sha(p) == sha(PR / args[0]) else "DIFFERENT")
elif cmd == "restore":
    p = path(args[0]); shutil.copy2(PR / args[0], p); ok = sha(p) == sha(PR / args[0]); print(("✅ restored " if ok else "❌ restore failed ") + args[0], sha(p)[:16]); sys.exit(0 if ok else 1)
elif cmd == "restore-all":
    bad = 0
    for k in KEYS:
        if not (PR / k).exists(): continue
        p = path(k); shutil.copy2(PR / k, p); ok = sha(p) == sha(PR / k); bad += (not ok); print(("✅ " if ok else "❌ ") + k)
    sys.exit(1 if bad else 0)
elif cmd == "patch":
    k, old, new = args[0], args[1], args[2]
    p = path(k); s = p.read_text(encoding="utf-8"); n = s.count(old)
    if n != 1: raise SystemExit(f"[patch] 前の文字が1か所に定まらない（{n} 件）: {old[:80]!r}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8"); print("✅ patched", k, sha(p)[:16])
elif cmd == "pyedit":
    k, code = args[0], args[1]
    p = str(path(k)); s = pathlib.Path(p).read_text(encoding="utf-8")
    exec(code, {"p": p, "s": s, "json": json, "re": re, "pathlib": pathlib})
    print("✅ pyedit", k, sha(p)[:16])
else:
    raise SystemExit("unknown cmd")
