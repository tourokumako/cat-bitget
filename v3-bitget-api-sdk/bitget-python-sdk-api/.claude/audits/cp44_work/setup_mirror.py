#!/usr/bin/env python3
"""setup_mirror.py — 束2 の設計書（m2e-bundle2-20260926）の修正19 のための作業場（本物の写し）を組み立てる。
本物のファイルは1つも書き替えない（読むだけ）。

なぜ要るか
  設計書のリスクの行（監査 CP44 の修正19）＝「承認の後、本物に当てる前に、作業場の写しに実装の指示を当て、
  py_compile・observe_diag.py --selftest-atr1h・壊すプログラム4本を写しで走らせ、出力を worklog に残す。
  1件でも落ちたら本物に当てずに まこさんに報告する」。

手本＝監査 CP39 の作業場の setup_mirror.py（cp39_work/setup_mirror.py）。
  ★写しの中だけ、根のパスの固定の1行（tools の ROOT・breaks/lib.sh の ROOT）を写しに向け替える。
  ★engine_tuner の読み込みの控え（tuner_cache）は写さない＝この段で走らせるのは観察の道具の番人と壊すプログラムだけで、
    どちらも控えを読まない。
  ★hook は写しに結び付けるだけ（読むだけ）。
"""
from __future__ import annotations
import hashlib, json, os, pathlib, shutil, sys

REAL_ROOT = pathlib.Path("/Users/tachiharamasako/Documents/GitHub/cat-bitget")
REAL_SDK = REAL_ROOT / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
WORK = REAL_SDK / ".claude" / "audits" / "cp44_work"
M = WORK / "mirror"
M_SDK = M / "v3-bitget-api-sdk" / "bitget-python-sdk-api"
ROOT_LINE_PY = 'ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"'
ROOT_LINE_SH = 'ROOT="/Users/tachiharamasako/Documents/GitHub/cat-bitget"'
IGN = shutil.ignore_patterns("__pycache__", ".DS_Store", "*.pyc")

KEYS = {
    "diag":  "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_diag.py",
    "ref":   "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/indicator_reference_diag.py",
    "cfg":   "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/observe_config.json",
    "gen":   "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/engine_tuner_gen.py",
    "src":   "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/acceptance_src.json",
    "acc":   ".claude/state/acceptance.md",
    "appr":  ".claude/state/acceptance.approved",
    "aaf":   ".claude/tools/apply_audit_fix.py",
    "lib":   ".claude/breaks/lib.sh",
    "b77":   ".claude/breaks/b77_no_streak.sh",
}


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def build():
    if M.exists():
        shutil.rmtree(M)
    (M / ".claude").mkdir(parents=True)
    shutil.copytree(REAL_ROOT / ".claude" / "tools", M / ".claude" / "tools", ignore=IGN)
    shutil.copytree(REAL_ROOT / ".claude" / "rules", M / ".claude" / "rules", ignore=IGN)
    shutil.copytree(REAL_ROOT / ".claude" / "state", M / ".claude" / "state",
                    ignore=shutil.ignore_patterns("sessions", "__pycache__", ".DS_Store"))
    os.symlink(REAL_ROOT / ".claude" / "hooks", M / ".claude" / "hooks")          # 読むだけ
    rep = []
    for f in sorted((M / ".claude" / "tools").glob("*.py")):
        s = f.read_text(encoding="utf-8")
        if ROOT_LINE_PY in s:
            f.write_text(s.replace(ROOT_LINE_PY, f'ROOT = "{M}"'), encoding="utf-8")
            rep.append(f.name)
    bd = M / ".claude" / "breaks"
    bd.mkdir()
    for f in sorted((REAL_ROOT / ".claude" / "breaks").glob("*.sh")):
        s = f.read_text(encoding="utf-8").replace(ROOT_LINE_SH, f'ROOT="{M}"')
        (bd / f.name).write_text(s, encoding="utf-8")
        os.chmod(bd / f.name, 0o755)
    M_SDK.mkdir(parents=True)
    (M_SDK / "scripts").mkdir()
    shutil.copytree(REAL_SDK / "scripts" / "priority_rebuild", M_SDK / "scripts" / "priority_rebuild",
                    ignore=shutil.ignore_patterns("__pycache__", "archive", ".DS_Store", "*.pyc", "*.log"))
    for d in sorted(p.name for p in (REAL_SDK / "scripts").iterdir() if p.is_dir() and p.name != "priority_rebuild"):
        os.symlink(REAL_SDK / "scripts" / d, M_SDK / "scripts" / d)
    for d in ("strategies", "runner", "cat", "data", "config"):
        if (REAL_SDK / d).exists():
            os.symlink(REAL_SDK / d, M_SDK / d)
    (M_SDK / ".claude").mkdir()
    for d in ("ratchet", "memory", "rules"):
        shutil.copytree(REAL_SDK / ".claude" / d, M_SDK / ".claude" / d, ignore=IGN)
    os.symlink("../../../.claude/state", M_SDK / ".claude" / "state")
    return rep


def manifest(rep):
    rows = []
    for k, rel in KEYS.items():
        real, mir = REAL_ROOT / rel, M / rel
        same = real.exists() and mir.exists() and sha(real) == sha(mir)
        note = ""
        if real.exists() and mir.exists() and not same:
            a = (real.read_text(encoding="utf-8", errors="ignore")
                 .replace(ROOT_LINE_PY, f'ROOT = "{M}"').replace(ROOT_LINE_SH, f'ROOT="{M}"'))
            note = "根のパスの1行だけ違う" if a == mir.read_text(encoding="utf-8", errors="ignore") else "★根のパス以外も違う"
        rows.append({"key": k, "file": rel, "real": sha(real) if real.exists() else None,
                     "mirror": sha(mir) if mir.exists() else None, "same": same, "note": note})
    (WORK / "manifest.json").write_text(json.dumps({"mirror": str(M), "repointed": rep, "files": rows},
                                                   ensure_ascii=False, indent=1), encoding="utf-8")
    ok = True
    for r in rows:
        good = r["same"] or r["note"] == "根のパスの1行だけ違う"
        ok = ok and good
        print(("✅" if good else "❌"), r["key"], (r["real"] or "-")[:16], (r["mirror"] or "-")[:16], r["note"])
    print("根のパスを写しに向けた道具:", rep)
    return ok


if __name__ == "__main__":
    rep = build()
    ok = manifest(rep)
    print("写し =", M)
    sys.exit(0 if ok else 1)
