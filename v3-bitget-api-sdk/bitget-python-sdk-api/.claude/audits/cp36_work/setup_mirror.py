#!/usr/bin/env python3
"""setup_mirror.py — 監査 cp36 の作業場（本物の写し）を組み立てる。

なぜ要るか＝依頼書 cp36 の指示「本物のファイルを書き替えないでください。試すときは作業場
`.claude/audits/cp36_work/` を作り、写しで試してください」。
壊すプログラム（.claude/breaks/b76〜b90）は本物のファイルを一時的に書き替えるので、
同じ壊し方を「写し」に対して再現できる形にする。

作るもの
  mirror/       ＝リポジトリと同じ形の写し（コードと設定は写し・5分足データは読み取りのリンク）
  mirror/breaks ＝壊すプログラムの写し（ROOT を mirror に向け替えたもの）
  mirror_old/   ＝2026-09-12 の commit 0e1f1be の版（B3 の前後比較用・差分の4ファイルだけ古い版）
  run.sh        ＝写しの中のプログラムを走らせる入口
  manifest.json ＝本物と写しのハッシュ値の対応（写しが本物と同じであることの証拠）

本物のファイルは1つも書き替えない（読むだけ）。
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys

REAL_ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
REAL_SDK = REAL_ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
WORK = REAL_SDK / ".claude" / "audits" / "cp36_work"
M = WORK / "mirror"
M_SDK = M / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
OLD_COMMIT = "0e1f1be"

IGNORE = shutil.ignore_patterns("__pycache__", "archive", ".DS_Store", "*.pyc")


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def copytree(src: pathlib.Path, dst: pathlib.Path, ignore=IGNORE):
    shutil.copytree(src, dst, ignore=ignore, symlinks=False)


def build_mirror():
    if M.exists():
        shutil.rmtree(M)
    (M / ".claude").mkdir(parents=True)
    # リポジトリ直下の .claude
    copytree(REAL_ROOT / ".claude" / "tools", M / ".claude" / "tools")
    copytree(REAL_ROOT / ".claude" / "rules", M / ".claude" / "rules")
    copytree(REAL_ROOT / ".claude" / "state", M / ".claude" / "state",
             ignore=shutil.ignore_patterns("sessions", "__pycache__", ".DS_Store"))
    os.symlink(REAL_ROOT / ".claude" / "hooks", M / ".claude" / "hooks")      # 読むだけ
    # v3-bitget-api-sdk
    (M / "v3-bitget-api-sdk" / "results" / "priority_rebuild").mkdir(parents=True)
    M_SDK.mkdir(parents=True)
    (M_SDK / "scripts").mkdir()
    copytree(REAL_SDK / "scripts" / "priority_rebuild", M_SDK / "scripts" / "priority_rebuild")
    for d in sorted(p.name for p in (REAL_SDK / "scripts").iterdir()
                    if p.is_dir() and p.name != "priority_rebuild"):
        os.symlink(REAL_SDK / "scripts" / d, M_SDK / "scripts" / d)         # regime・dashboard ほか＝読むだけ
    for d in ("strategies", "runner", "cat", "data", "config"):
        if (REAL_SDK / d).exists():
            os.symlink(REAL_SDK / d, M_SDK / d)
    (M_SDK / ".claude").mkdir()
    copytree(REAL_SDK / ".claude" / "ratchet", M_SDK / ".claude" / "ratchet")
    copytree(REAL_SDK / ".claude" / "memory", M_SDK / ".claude" / "memory")
    copytree(REAL_SDK / ".claude" / "rules", M_SDK / ".claude" / "rules")
    os.symlink("../../../.claude/state", M_SDK / ".claude" / "state")        # 本物と同じ相対リンク
    # 監査レポート（gen_acceptance --verify が cp35 のレポートを読む・無いと fail-closed で止まる）
    (M_SDK / ".claude" / "audits").mkdir()
    for f in (REAL_SDK / ".claude" / "audits").glob("*.md"):
        shutil.copy2(f, M_SDK / ".claude" / "audits" / f.name)
    for f in REAL_SDK.glob("*.md"):
        shutil.copy2(f, M_SDK / f.name)
    # 壊すプログラムの写し（ROOT を写しに向ける）
    bdst = M / "breaks"
    bdst.mkdir()
    for f in sorted((REAL_ROOT / ".claude" / "breaks").glob("*.sh")):
        s = f.read_text(encoding="utf-8")
        s = s.replace('ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"', f'ROOT="{M}"')
        (bdst / f.name).write_text(s, encoding="utf-8")
        os.chmod(bdst / f.name, 0o755)


def build_old():
    old = WORK / "mirror_old"
    if old.exists():
        shutil.rmtree(old)
    shutil.copytree(M, old, symlinks=True)
    files = [
        "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py",
        "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_stage_candidates.json",
        "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regime_laws.json",
        ".claude/tools/gen_regime_kb.py",
    ]
    for rel in files:
        out = subprocess.run(["git", "-C", str(REAL_ROOT), "show", f"{OLD_COMMIT}:{rel}"],
                             capture_output=True)
        if out.returncode != 0:
            raise SystemExit(f"git show failed: {rel}: {out.stderr.decode()[:200]}")
        (old / rel).write_bytes(out.stdout)
    # 0e1f1be には無かった数える道具は古い版から消す（無かった状態を再現）
    p = old / ".claude/tools/count_builder_literals.py"
    if p.exists():
        p.unlink()
    # 古い版の breaks の写しは mirror_old を向くようにする
    for f in (old / "breaks").glob("*.sh"):
        s = f.read_text(encoding="utf-8").replace(f'ROOT="{M}"', f'ROOT="{old}"')
        f.write_text(s, encoding="utf-8")
    return old


def write_runner():
    r = WORK / "run.sh"
    r.write_text(f"""#!/bin/bash
# run.sh — 写しの中のプログラムを走らせる入口（監査 cp36 の作業場・本物は触らない）
#   bash run.sh gen  <args>      → 写しの engine_tuner_gen.py
#   bash run.sh exec <args>      → 写しの engine_tuner_exec.py
#   bash run.sh r9   <args>      → 写しの regime_r9_diag.py
#   bash run.sh count            → 写しの数える道具（count_builder_literals）
#   bash run.sh kb <args>        → 写しの gen_regime_kb（例: --write stage ／ --verify）
#   bash run.sh acc <args>       → 写しの gen_acceptance（例: --verify）
#   bash run.sh rb <args>        → 写しの run_breaks（例: --selftest）
#   bash run.sh old-gen / old-r9 / old-kb → mirror_old（0e1f1be の版）
#   bash run.sh break <bNN_name>  → 写しの壊すプログラム（.sh は付けても付けなくてもよい）
#   bash run.sh old-break <bNN_name> → mirror_old の壊すプログラム
#   ★hook の都合で、コマンドの文字列に .py を書かない形にしてある（写しの中のプログラムだけを走らせる）
set -u
W="{WORK}"
M="$W/mirror"; O="$W/mirror_old"
SDK="v3-bitget-api-sdk/bitget-python-sdk-api"
PR="$M/$SDK/scripts/priority_rebuild"; OPR="$O/$SDK/scripts/priority_rebuild"
T="$M/.claude/tools"; OT="$O/.claude/tools"
cmd="${{1:-}}"; shift || true
case "$cmd" in
  gen)   exec python3 "$PR/engine_tuner_gen.py" "$@";;
  exec)  exec python3 "$PR/engine_tuner_exec.py" "$@";;
  r9)    exec python3 "$PR/regime_r9_diag.py" "$@";;
  count) exec python3 "$T/count_builder_literals.py" "$@";;
  kb)    exec python3 "$T/gen_regime_kb.py" "$@";;
  acc)   exec python3 "$T/gen_acceptance.py" "$@";;
  rb)    exec python3 "$T/run_breaks.py" "$@";;
  old-gen)  exec python3 "$OPR/engine_tuner_gen.py" "$@";;
  old-r9)   exec python3 "$OPR/regime_r9_diag.py" "$@";;
  old-kb)   exec python3 "$OT/gen_regime_kb.py" "$@";;
  break)     b="${{1%.sh}}"; shift; exec bash "$M/breaks/$b.sh" "$@";;
  old-break) b="${{1%.sh}}"; shift; exec bash "$O/breaks/$b.sh" "$@";;
  # ── 写しのファイルを直接 壊す・戻す（追加の壊し方を試すため）──
  #   鍵＝gen / exec / r9 / laws / cands / acc / mile / kb / rb / count / limits
  #   bash run.sh path <鍵>                 → 写しの中のそのファイルのパスを出す
  #   bash run.sh hash <鍵>                 → いまのハッシュ値と、組み立て直後（pristine）のハッシュ値
  #   bash run.sh restore <鍵>              → pristine から戻す（戻したあとハッシュ値を照らす）
  #   bash run.sh restore-all               → 全部の鍵を戻す
  #   bash run.sh patch <鍵> <前の文字> <後の文字>  → 文字を1か所だけ置き換える（1か所に定まらなければ止まる）
  #   bash run.sh pyedit <鍵> <python の文>  → p（パス）・s（中身）・json・re を渡して python の文を走らせる。
  #                                            s を書き替えて `open(p,'w').write(s)` するか、json を書き戻す
  path|hash|restore|restore-all|patch|pyedit)
        exec python3 "$W/mirror_edit.py" "$cmd" "$@";;
  *) echo "usage: run.sh gen|exec|r9|count|kb|acc|rb|old-gen|old-r9|old-kb|break|old-break|path|hash|restore|restore-all|patch|pyedit ..." >&2; exit 2;;
esac
""", encoding="utf-8")
    os.chmod(r, 0o755)


KEYS = {
    "gen":    "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py",
    "exec":   "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py",
    "r9":     "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py",
    "laws":   "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regime_laws.json",
    "cands":  "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_stage_candidates.json",
    "mile":   "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md",
    "limits": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json",
    "acc":    ".claude/state/acceptance.md",
    "kb":     ".claude/tools/gen_regime_kb.py",
    "rb":     ".claude/tools/run_breaks.py",
    "count":  ".claude/tools/count_builder_literals.py",
    "acc_tool": ".claude/tools/gen_acceptance.py",
}


def write_pristine_and_editor():
    pr = WORK / "pristine"
    if pr.exists():
        shutil.rmtree(pr)
    pr.mkdir()
    for k, rel in KEYS.items():
        shutil.copy2(M / rel, pr / k)
    (WORK / "mirror_edit.py").write_text(f'''#!/usr/bin/env python3
"""mirror_edit.py — 写しのファイルを壊す・戻す（run.sh から呼ぶ・本物は触らない）。"""
import hashlib, json, pathlib, re, shutil, sys
M = pathlib.Path({str(M)!r})
PR = pathlib.Path({str(pr)!r})
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


def manifest(old):
    keys = [
        "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py",
        "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_exec.py",
        "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/regime_r9_diag.py",
        "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/regime_laws.json",
        "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/m2_stage_candidates.json",
        "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md",
        "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/signal_families.json",
        "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/material_ranking.json",
        "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/recipes/search_limits.json",
        ".claude/state/acceptance.md",
        ".claude/tools/count_builder_literals.py",
        ".claude/tools/gen_regime_kb.py",
        ".claude/tools/gen_acceptance.py",
        ".claude/tools/run_breaks.py",
    ]
    rows = []
    for rel in keys:
        real = REAL_ROOT / rel
        mir = M / rel
        o = old / rel
        rows.append({
            "file": rel,
            "real": sha(real) if real.exists() else None,
            "mirror": sha(mir) if mir.exists() else None,
            "same": (real.exists() and mir.exists() and sha(real) == sha(mir)),
            "old_0e1f1be": sha(o) if o.exists() else None,
        })
    brk = []
    for f in sorted((REAL_ROOT / ".claude" / "breaks").glob("b7[6-9]*.sh")) + \
             sorted((REAL_ROOT / ".claude" / "breaks").glob("b8*.sh")) + \
             sorted((REAL_ROOT / ".claude" / "breaks").glob("b90*.sh")) + \
             [REAL_ROOT / ".claude" / "breaks" / "lib.sh"]:
        brk.append({"file": f.name, "real": sha(f), "mirror_copy": sha(M / "breaks" / f.name),
                    "note": "mirror の写しは ROOT の1行だけ書き替えてある"})
    out = {"mirror": str(M), "mirror_old": str(old), "old_commit": OLD_COMMIT,
           "files": rows, "breaks": brk}
    (WORK / "manifest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for r in rows:
        print(("✅" if r["same"] else "❌"), r["file"], (r["real"] or "-")[:16], (r["mirror"] or "-")[:16],
              "old=" + ((r["old_0e1f1be"] or "-")[:16]))
    return all(r["same"] for r in rows if r["real"])


if __name__ == "__main__":
    WORK.mkdir(parents=True, exist_ok=True)
    build_mirror()
    old = build_old()
    write_runner()
    write_pristine_and_editor()
    ok = manifest(old)
    print("mirror =", M)
    print("mirror_old =", old)
    print("run.sh =", WORK / "run.sh")
    sys.exit(0 if ok else 1)
