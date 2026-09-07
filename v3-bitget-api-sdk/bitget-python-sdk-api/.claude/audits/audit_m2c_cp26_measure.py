#!/usr/bin/env python3
"""audit_m2c_cp26_measure.py — 監査 CP26 が「守りが本物か」を自分で壊して測る

なぜ在るか:
  まこさん指示 2026-09-07「手で数えるのを禁じる → audit_m2c_scan.py」。
  cp25 の `audit_m2c_cp25_measure.py` は「案に出るか」「印から外すと消えるか」を測ります。
  この回（cp26）で新しく足された守りは、それでは測れません。

  ★測れない理由＝壊すプログラム b35・b36 を監査からは走らせられません
    （土台ゲートが `.claude/breaks/*.sh` の実行を止める＝cp24・cp25 と同じ壁）。
  だから、b35・b36 と**同じ壊し方**を、このプログラムが自分でやって測ります。

測るもの（4つ）:
  A 基準＝いまの終了コードと、かかった時間
  B 審査の別枠3枝（レンジ幾何・需給・時間帯）を **1本ずつ** 消すと、T33-g が落ちるか
    ★b35 が壊すのは需給の1本だけ。残り2本も落ちるかは b35 では測れない
  C 候補を作る所の印の判定を **1本ずつ** 消すと、b33 の測り方（--count-extra-candidates）
    で見抜けるか
  D 共通の道から需給を載せる呼び出しを消すと、実行器の自己検査が落ちるか（b36 と同じ）

必ず元に戻します:
  ・触る前に中身（bytes）と更新時刻を控え、finally で必ず書き戻します。
  ・戻したあと sha256 と更新時刻を照らし、1文字でも違えば ❌ を出して終了コード 9 で落ちます。

正直な限界:
  ・壊し方は「その行を消す」1通りだけです。別の壊し方（意味を変えずに書き替える等）は試しません。
  ・終了コードだけを見ます。落ちた理由が本当にその枝かは、出力の最後の行で確かめます。
  ・このプログラム自身は凍結されていません（承認の対象外）。
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
import time

SDK = pathlib.Path(__file__).resolve().parents[2]
PR = SDK / "scripts/priority_rebuild"
GEN = PR / "engine_tuner_gen.py"
EXE = PR / "engine_tuner_exec.py"
SW = SDK / ".claude/ratchet/indicator_switch.json"


def sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run(args: list[str], timeout: int = 900) -> tuple[int, str, float]:
    t0 = time.time()
    r = subprocess.run([sys.executable] + args, cwd=str(SDK),
                       capture_output=True, text=True, timeout=timeout)
    dt = time.time() - t0
    tail = [x for x in (r.stdout + r.stderr).strip().splitlines() if x.strip()]
    return r.returncode, (tail[-1][:110] if tail else ""), dt


class Keeper:
    """触るファイルの中身と更新時刻を控え、必ず戻す。"""

    def __init__(self, *paths: pathlib.Path):
        self.paths = list(paths)
        self.raw = {p: p.read_bytes() for p in self.paths}
        self.st = {p: (p.stat().st_atime, p.stat().st_mtime) for p in self.paths}
        self.sha0 = {p: sha(p) for p in self.paths}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        bad = []
        for p in self.paths:
            p.write_bytes(self.raw[p])
            os.utime(p, self.st[p])
            if sha(p) != self.sha0[p]:
                bad.append(p.name)
        if bad:
            print(f"❌ 元に戻せていません: {bad}")
            raise SystemExit(9)
        return False


# ── 壊し方（b35・b36 と同じ形の置き換え）────────────────────────────────────
GATE_CUT = {
    "geo": (r'\n *elif not ex\.geo_enabled\(str\(m\["geo"\]\)\):'
            r'\n *bad\(f"印が「使わない」のレンジ幾何の列[^\n]*\)'),
    "demand": (r'\n *elif not ex\.demand_enabled\(str\(m\["demand"\]\)\):'
               r'\n *bad\(f"印が「使わない」の需給の列[^\n]*\)'),
    "time": (r'\n *elif not ex\.time_enabled\(str\(m\["time"\]\)\):'
             r'\n *bad\(f"印が「使わない」の時間帯の材料[^\n]*\)'),
}

CAND_CUT = {
    "geo": (r'if ex\.geo_enabled\(str\(g\)\)\]', r']'),
    "demand": (r'\n *if ex\.demand_enabled\(str\(d\)\)\]', r']'),
    "time": (r'if ex\.time_enabled\(str\(t\)\) and limits', r'if limits'),
}

ATTACH_CUT = (r'\n *_dem = demand_cols_in\(recipe\)'
              r'\n *if _dem:'
              r'\n *out = attach_demand_columns\(out, sorted\(_dem\)\)')


def cut(p: pathlib.Path, pat: str, rep: str = "") -> None:
    s = p.read_text(encoding="utf-8")
    s2 = re.sub(pat, rep, s, count=1)
    if s2 == s:
        raise SystemExit(f"❌ 壊す対象の行が見つからない（前提が変わった）: {pat[:50]}")
    p.write_text(s2, encoding="utf-8")


def main() -> int:
    L: list[str] = []
    L.append("<!-- SCAN26_START audit_m2c_cp26_measure.py が実物を壊して測る＝手で書き換えない -->")
    L.append("")

    # ── A 基準 ───────────────────────────────────────────────────────────
    L.append("### C-1｜基準（壊す前）")
    L.append("")
    L.append("| コマンド | 終了コード | かかった時間 | 出力の最後の行 |")
    L.append("|---|---|---|---|")
    base = {}
    for tag, args in (("gate", [str(GEN), "--selftest-extra-gate"]),
                      ("cand", [str(GEN), "--count-extra-candidates"]),
                      ("exec", [str(EXE), "--selftest"])):
        rc, tail, dt = run(args)
        base[tag] = (rc, tail, dt)
        L.append(f"| `{pathlib.Path(args[0]).name} {args[1]}` | **{rc}** | {dt:.1f}秒 | {tail} |")
    L.append("")

    # ── B 審査の別枠3枝を1本ずつ消す ────────────────────────────────────
    L.append("### C-2｜案の審査の別枠3枝を **1本ずつ** 消すと、T33-g が落ちるか")
    L.append("")
    L.append("> ★b35 が壊すのは需給の1本だけ。ここでは3本とも試す（b35 では測れない所）。")
    L.append("")
    L.append("| 消した枝 | `--selftest-extra-gate` の終了コード | 出力の最後の行 | 判定 |")
    L.append("|---|---|---|---|")
    for kind, pat in GATE_CUT.items():
        with Keeper(GEN):
            cut(GEN, pat)
            rc, tail, _dt = run([str(GEN), "--selftest-extra-gate"])
        ok = "✅ 落ちた" if rc != 0 else "❌ 落ちない（守れていない）"
        L.append(f"| {kind} | **{rc}** | {tail} | {ok} |")
    L.append("")

    # ── C 候補を作る所の印の判定を1本ずつ消す ───────────────────────────
    L.append("### C-3｜候補を作る所の印の判定を **1本ずつ** 消すと、b33 の測り方で見抜けるか")
    L.append("")
    L.append("> b33 の測り方＝印の別枠3欄を空にして `--count-extra-candidates` を打ち、"
             "**0 になれば「印が効いている」**とする。判定を消すと 0 にならない＝b33 が落ちる。")
    L.append("")
    L.append("| 消した判定 | 印を空にした時の別枠の候補 | 判定 |")
    L.append("|---|---|---|")

    def empty_switch(d: dict) -> None:
        for k in ("geo_on", "demand_on", "time_on"):
            d[k] = []

    # まず「何も消していない状態で印を空にすると 0 になるか」＝b33 が今 通るか
    with Keeper(SW):
        d = json.loads(SW.read_text(encoding="utf-8"))
        empty_switch(d)
        SW.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rc, tail, _ = run([str(GEN), "--count-extra-candidates"])
    L.append(f"| （何も消さない＝b33 そのもの） | **{tail}** | "
             f"{'✅ 0件＝印が効いている' if tail.strip() == '0' else '❌ 残っている'} |")

    for kind, (pat, rep) in CAND_CUT.items():
        with Keeper(GEN, SW):
            cut(GEN, pat, rep)
            d = json.loads(SW.read_text(encoding="utf-8"))
            empty_switch(d)
            SW.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            rc, tail, _ = run([str(GEN), "--count-extra-candidates"])
        ok = ("✅ b33 が落ちる（0 でない）" if tail.strip() not in ("0", "")
              else "❌ b33 は見抜けない")
        L.append(f"| {kind} | **{tail}** | {ok} |")
    L.append("")

    # ── D 共通の道から需給を載せる呼び出しを消す（b36 と同じ）─────────────
    L.append("### C-4｜共通の道から需給を載せる呼び出しを消すと、実行器の自己検査が落ちるか（b36 と同じ）")
    L.append("")
    with Keeper(EXE):
        cut(EXE, ATTACH_CUT)
        rc, tail, dt = run([str(EXE), "--selftest"])
    L.append(f"- 終了コード＝**{rc}**（{dt:.1f}秒）／出力の最後の行＝{tail}")
    L.append(f"- 判定＝{'✅ 落ちた' if rc != 0 else '❌ 落ちない（守れていない）'}")
    L.append("")

    # ── E 戻ったか ───────────────────────────────────────────────────────
    L.append("### C-5｜触ったファイルが元に戻っているか（sha256 の先頭16文字）")
    L.append("")
    for p in (GEN, EXE, SW):
        L.append(f"- `{p.name}`＝`{sha(p)[:16]}`")
    L.append("")
    L.append("<!-- SCAN26_END -->")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
