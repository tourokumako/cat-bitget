#!/usr/bin/env python3
"""監査 CP27＝壊すプログラム b38・b39・b40 と同じ壊し方を、監査が自分で再現して測る。

なぜ要るか＝依頼書 §4 の9＝承認のときの b38〜b40 の測り（rc=1）は、その後の直し（H2 の番人と
read-only 診断の番人で見つかった2件）より前のコードで測ったもの。直した後も止まるかを確かめる。
★`.claude/breaks/*.sh` は、監査のセッションでも土台ゲート（require_acceptance_before_impl.sh）に
  止められて走らせられないので、同じ壊し方（同じ正規表現・同じ文字列）をここで写して再現する。

やること（1本ごと）
  1. 触るファイルを控えへ写し、ハッシュ値を覚える
  2. 壊す（b38・b39・b40 の .sh に書いてある置き換えと1文字も変えない）
  3. 測る対象のコマンドを走らせ、終了コードを覚える
  4. 必ず控えから戻す（例外でも戻す）
  5. 戻したあとハッシュ値を照らし、1文字でも違えば 99 で落ちる

使い方: python3 .claude/audits/audit_m2d_cp27_breaks.py
期待  : 3本とも 壊すと rc=1（壊さないと rc=0）
"""
from __future__ import annotations
import hashlib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
PR = ROOT / "scripts" / "priority_rebuild"
OBS = PR / "observe_diag.py"
GEN = PR / "engine_tuner_gen.py"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(cmd: list[str]) -> int:
    return subprocess.run(cmd, capture_output=True).returncode


# --- b38 = ranked_materials の需給の枝（5行）を消す（b38 の .sh の正規表現をそのまま写す） ---
def break_b38(s: str) -> str:
    out = re.sub(
        r'\n *if nm in iref\.DEMAND_REF:'
        r'\n *if not ex\.demand_enabled\(nm\):'
        r'\n *continue'
        r'\n *rows\.append\(\(abs\(float\(acc\) - 0\.5\), str\(col\), float\(acc\), lab, str\(hor\)\)\)'
        r'\n *continue',
        '', s, count=1)
    if out == s:
        raise SystemExit("b38 の壊す対象の行が見つからない（前提が変わった）")
    return out


# --- b39 = merge_demand_into_ranking の「足す」部分を消す ---
def break_b39(s: str) -> str:
    target = 'merged = [list(x) for x in kept] + [[c, float(a)] for c, a in new]'
    if target not in s:
        raise SystemExit("b39 の壊す対象の行が見つからない（前提が変わった）")
    return s.replace(target, 'merged = [list(x) for x in kept]', 1)


# --- b40 = 足した後に指標の行の分離力を1つ書き換える行を注入する ---
def break_b40(s: str) -> str:
    anchor = '                order[role].setdefault(lab, {})[key] = merged\n'
    if anchor not in s:
        raise SystemExit("b40 の壊す対象の行が見つからない（前提が変わった）")
    inject = ('                if merged and not _demand_rank_name(str(merged[0][0])): '
              'merged[0][1] = 0.999  # b40\n')
    return s.replace(anchor, anchor + inject, 1)


CASES = [
    ("b38", GEN, break_b38, [sys.executable, str(GEN), "--selftest-rank-demand"]),
    ("b39", OBS, break_b39, [sys.executable, str(OBS), "--selftest-rank-demand"]),
    ("b40", OBS, break_b40, [sys.executable, str(OBS), "--selftest-rank-demand"]),
]


def main() -> int:
    bad = 0
    print("=" * 96)
    print("[壊すプログラムの再現] b38・b39・b40 と同じ壊し方を監査が写して測る")
    print("=" * 96)
    for name, target, breaker, cmd in CASES:
        orig = target.read_bytes()
        h0 = sha(target)
        base = run(cmd)
        print(f"  {name}: 壊す前の {target.name} = {h0[:16]} / 壊さないときの rc = {base}")
        try:
            target.write_text(breaker(orig.decode("utf-8")), encoding="utf-8")
            rc = run(cmd)
        finally:
            target.write_bytes(orig)
        h1 = sha(target)
        restored = (h0 == h1)
        good = (base == 0 and rc == 1 and restored)
        print(f"  {name}: 壊したときの rc = {rc} / 戻した後 = {h1[:16]}"
              f" / 戻せた = {restored} → {'OK' if good else 'NG'}")
        if not restored:
            print(f"  {name}: ❌ 元に戻せていない（{target}）")
            return 99
        if not good:
            bad += 1
    print("=" * 96)
    print(f"壊すプログラムの再現: NG {bad} 件（期待＝壊さないと rc=0・壊すと rc=1）")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
