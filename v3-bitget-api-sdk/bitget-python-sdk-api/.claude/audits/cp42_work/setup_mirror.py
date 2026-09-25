#!/usr/bin/env python3
"""setup_mirror.py — 監査 cp42 の作業場（本物の写し）を組み立てる。

なぜ要るか＝依頼書 cp42 の指示「本物のファイルを書き替えないでください。壊して確かめるときは、
作業場 cp42_work に写しを作ってください」。壊すプログラム b101・b102 は本物の
apply_audit_fix.py を一時的に書き替えるので、同じ壊し方を写しに対して再現できる形にする。
手本＝cp36_work/setup_mirror.py（監査 cp36 の auditor が作ったもの）。

★写しの中だけ、根のパスを写しに向け替える＝本物の道具（apply_audit_fix.py・gen_audit_docs.py ほか）と
  壊すプログラムの lib.sh は、根のパスを固定の文字で持っているため。書き替えるのは、その1行だけ。

作るもの
  mirror/          ＝リポジトリと同じ形の写し（コード・設定・状態ファイルは写し・5分足データなどは読み取りのリンク）
  pristine/        ＝組み立て直後の写し（壊した後に戻すための元）
  run.sh           ＝写しの中のプログラムを走らせる入口
  mirror_edit.py   ＝写しのファイルを壊す・戻す
  manifest.json    ＝本物と写しのハッシュ値の対応（根のパスの1行を除けば同じ、の証拠）

本物のファイルは1つも書き替えない（読むだけ）。
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import sys

REAL_ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
REAL_SDK = REAL_ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
WORK = REAL_SDK / ".claude" / "audits" / "cp42_work"
M = WORK / "mirror"
M_SDK = M / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
PR = WORK / "pristine"

IGNORE = shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc")
ROOT_LINE_PY = 'ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"'
ROOT_LINE_SH = 'ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"'

# 壊す・戻すの相手（鍵 → 写しの中の相対パス）
KEYS = {
    "aaf":      ".claude/tools/apply_audit_fix.py",
    "gen_acc":  ".claude/tools/gen_acceptance.py",
    "gad":      ".claude/tools/gen_audit_docs.py",
    "acc":      ".claude/state/acceptance.md",
    "approved": ".claude/state/acceptance.approved",
    "src":      "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json",
    "b101":     ".claude/breaks/b101_design_apply_no_approval.sh",
    "b102":     ".claude/breaks/b102_design_apply_no_precheck.sh",
    "lib":      ".claude/breaks/lib.sh",
}


def sha(p) -> str:
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def copytree(src: pathlib.Path, dst: pathlib.Path, ignore=IGNORE):
    shutil.copytree(src, dst, ignore=ignore, symlinks=False)


def repoint_py(d: pathlib.Path) -> list:
    """写しの .py の中の、根のパスの固定の1行だけを写しに向け替える。向け替えたファイル名を返す。"""
    done = []
    for f in sorted(d.glob("*.py")):
        s = f.read_text(encoding="utf-8")
        if ROOT_LINE_PY in s:
            f.write_text(s.replace(ROOT_LINE_PY, f'ROOT = "{M}"'), encoding="utf-8")
            done.append(f.name)
    return done


def build_mirror() -> dict:
    if M.exists():
        shutil.rmtree(M)
    (M / ".claude").mkdir(parents=True)
    # リポジトリ直下の .claude
    copytree(REAL_ROOT / ".claude" / "tools", M / ".claude" / "tools")
    copytree(REAL_ROOT / ".claude" / "rules", M / ".claude" / "rules")
    copytree(REAL_ROOT / ".claude" / "state", M / ".claude" / "state",
             ignore=shutil.ignore_patterns("sessions", "__pycache__", ".DS_Store"))
    os.symlink(REAL_ROOT / ".claude" / "hooks", M / ".claude" / "hooks")      # 読むだけ
    repointed = repoint_py(M / ".claude" / "tools")
    # 壊すプログラムの写し（lib.sh と各 .sh の根のパスを写しに向ける）
    bdst = M / ".claude" / "breaks"
    bdst.mkdir()
    for f in sorted((REAL_ROOT / ".claude" / "breaks").glob("*.sh")):
        s = f.read_text(encoding="utf-8").replace(ROOT_LINE_SH, f'ROOT="{M}"')
        (bdst / f.name).write_text(s, encoding="utf-8")
        os.chmod(bdst / f.name, 0o755)
    # v3-bitget-api-sdk
    (M / "v3-bitget-api-sdk" / "results" / "priority_rebuild").mkdir(parents=True)
    M_SDK.mkdir(parents=True)
    (M_SDK / "scripts").mkdir()
    copytree(REAL_SDK / "scripts" / "priority_rebuild", M_SDK / "scripts" / "priority_rebuild",
             ignore=shutil.ignore_patterns("__pycache__", "archive", ".DS_Store", "*.pyc", "*.log"))
    for d in sorted(p.name for p in (REAL_SDK / "scripts").iterdir()
                    if p.is_dir() and p.name != "priority_rebuild"):
        os.symlink(REAL_SDK / "scripts" / d, M_SDK / "scripts" / d)         # 読むだけ
    for d in ("strategies", "runner", "cat", "data", "config"):
        if (REAL_SDK / d).exists():
            os.symlink(REAL_SDK / d, M_SDK / d)
    (M_SDK / ".claude").mkdir()
    for d in ("ratchet", "memory", "rules"):
        copytree(REAL_SDK / ".claude" / d, M_SDK / ".claude" / d)
    os.symlink("../../../.claude/state", M_SDK / ".claude" / "state")        # 本物と同じ相対リンク
    # 監査の文書（テンプレ・依頼書・結果）
    (M_SDK / ".claude" / "audits").mkdir()
    for f in (REAL_SDK / ".claude" / "audits").glob("*.md"):
        shutil.copy2(f, M_SDK / ".claude" / "audits" / f.name)
    copytree(REAL_SDK / ".claude" / "audits" / "inputs", M_SDK / ".claude" / "audits" / "inputs")
    for f in REAL_SDK.glob("*.md"):
        shutil.copy2(f, M_SDK / f.name)
    return {"repointed_tools": repointed}


def write_pristine():
    if PR.exists():
        shutil.rmtree(PR)
    PR.mkdir()
    for k, rel in KEYS.items():
        p = M / rel
        if p.exists():
            shutil.copy2(p, PR / k)


def write_runner():
    r = WORK / "run.sh"
    r.write_text(f"""#!/bin/bash
# run.sh — 写しの中のプログラムを走らせる入口（監査 cp42 の作業場・本物は触らない）
#   bash run.sh aaf <args>        → 写しの apply_audit_fix（例: --selftest ／ --design <設計書> --dry）
#   bash run.sh acc <args>        → 写しの gen_acceptance（例: --selftest ／ --verify ／ --dry-run）
#   bash run.sh gad <args>        → 写しの gen_audit_docs
#   bash run.sh tool <名前> <args> → 写しの .claude/tools/<名前>.py（.py は付けない）
#   bash run.sh break <bNN_name>   → 写しの壊すプログラム（.sh は付けても付けなくてもよい）
#   ── 写しのファイルを直接 壊す・戻す ──
#   鍵＝{" / ".join(KEYS)}
#   bash run.sh path <鍵> ／ hash <鍵> ／ restore <鍵> ／ restore-all
#   bash run.sh patch <鍵> <前の文字> <後の文字>   → 1か所だけ置き換える（1か所に定まらなければ止まる）
#   bash run.sh pyedit <鍵> <python の文>          → p（パス）・s（中身）・json・re を渡して走らせる
#   ★作業場所は写しの根（mirror）。hook の都合で、コマンドの文字列に本物の道具のパスを書かない形にしてある
set -u
W="{WORK}"
M="$W/mirror"
T="$M/.claude/tools"
cmd="${{1:-}}"; shift || true
case "$cmd" in
  aaf)   cd "$M" && exec python3 "$T/apply_audit_fix.py" "$@";;
  acc)   cd "$M" && exec python3 "$T/gen_acceptance.py" "$@";;
  gad)   cd "$M" && exec python3 "$T/gen_audit_docs.py" "$@";;
  tool)  n="${{1%.py}}"; shift; cd "$M" && exec python3 "$T/$n.py" "$@";;
  break) b="${{1%.sh}}"; shift; cd "$M" && exec bash "$M/.claude/breaks/$b.sh" "$@";;
  path|hash|restore|restore-all|patch|pyedit)
        exec python3 "$W/mirror_edit.py" "$cmd" "$@";;
  *) echo "usage: run.sh aaf|acc|gad|tool|break|path|hash|restore|restore-all|patch|pyedit ..." >&2; exit 2;;
esac
""", encoding="utf-8")
    os.chmod(r, 0o755)


def write_editor():
    (WORK / "mirror_edit.py").write_text(f'''#!/usr/bin/env python3
"""mirror_edit.py — 写しのファイルを壊す・戻す（run.sh から呼ぶ・本物は触らない）。"""
import hashlib, json, pathlib, re, shutil, sys
M = pathlib.Path({str(M)!r})
PR = pathlib.Path({str(PR)!r})
KEYS = {json.dumps(KEYS, ensure_ascii=False)}
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
    if n != 1: raise SystemExit(f"[patch] 前の文字が1か所に定まらない（{{n}} 件）: {{old[:80]!r}}")
    p.write_text(s.replace(old, new, 1), encoding="utf-8"); print("✅ patched", k, sha(p)[:16])
elif cmd == "pyedit":
    k, code = args[0], args[1]
    p = str(path(k)); s = pathlib.Path(p).read_text(encoding="utf-8")
    exec(code, {{"p": p, "s": s, "json": json, "re": re, "pathlib": pathlib}})
    print("✅ pyedit", k, sha(p)[:16])
else:
    raise SystemExit("unknown cmd")
''', encoding="utf-8")


def manifest(info: dict) -> bool:
    rows = []
    for k, rel in KEYS.items():
        real = REAL_ROOT / rel
        mir = M / rel
        same = real.exists() and mir.exists() and sha(real) == sha(mir)
        note = ""
        if real.exists() and mir.exists() and not same:
            a = real.read_text(encoding="utf-8", errors="ignore")
            b = mir.read_text(encoding="utf-8", errors="ignore")
            a2 = a.replace(ROOT_LINE_PY, f'ROOT = "{M}"').replace(ROOT_LINE_SH, f'ROOT="{M}"')
            note = "根のパスの1行だけ違う" if a2 == b else "★根のパス以外も違う"
        rows.append({"key": k, "file": rel, "real": sha(real) if real.exists() else None,
                     "mirror": sha(mir) if mir.exists() else None, "same": same, "note": note})
    out = {"mirror": str(M), "repointed_tools": info.get("repointed_tools"), "files": rows}
    (WORK / "manifest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    ok = True
    for r in rows:
        good = r["same"] or r["note"] == "根のパスの1行だけ違う"
        ok = ok and good
        print(("✅" if good else "❌"), r["key"], r["file"], (r["real"] or "-")[:16], (r["mirror"] or "-")[:16], r["note"])
    print("根のパスを向け替えた道具:", ", ".join(info.get("repointed_tools") or []))
    return ok


if __name__ == "__main__":
    WORK.mkdir(parents=True, exist_ok=True)
    info = build_mirror()
    write_pristine()
    write_runner()
    write_editor()
    ok = manifest(info)
    print("mirror =", M)
    print("run.sh =", WORK / "run.sh")
    sys.exit(0 if ok else 1)
