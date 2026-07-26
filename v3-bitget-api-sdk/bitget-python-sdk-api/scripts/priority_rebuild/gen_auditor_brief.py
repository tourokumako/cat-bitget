#!/usr/bin/env python3
"""gen_auditor_brief.py — 監査テンプレの「プロジェクトの現在地」を実体から機械生成する（まこさん指摘 2026-07-27）

なぜ作ったか
--------------------------------------------------------------------------
`.claude/auditor_template.md` の最終更新は 2026-05-21 で、2ヶ月止まっていた（2026-07-27 実測）。
中身は廃止済みの8工程フロー（Phase 0〜7・LightGBM 14ラベル独立学習・k-means）で、
期間も現行と違い、現行の戦略と道具（E35〜E38／observe_diag／engine_tuner／fast-mode）が1件も出てこない。
このまま監査を起動すると、監査する側は**存在しない枠組み**でプロジェクトを見る。

監査の7つの観点（統計・リスク管理・認知バイアス・ソフトウェア工学・設計判断・実行プロセス・
主エージェントのバイアス）は普遍なので残す。**腐るのは「現在地」と「参照先」だけ**なので、そこだけ機械化する。

何を差し込むか（すべて実体から）
--------------------------------------------------------------------------
  ① いまの現在地（WORKFLOW.md の現在地の行）
  ② 検証に使う期間（periods.py・gen_windows の表を再利用）
  ③ 戦略と役割（adopted_strategies.md の機械可読マーカー）
  ④ 使う道具（gen_filemap の索引を再利用）
  ⑤ 守る制約（cat_requirements.md §4.6 の H 番号と要件名）
  ⑥ まこさんが最近決めたこと（decisions.md の先頭）

使い方
--------------------------------------------------------------------------
  python3 scripts/priority_rebuild/gen_auditor_brief.py --write     # 差し込む
  python3 scripts/priority_rebuild/gen_auditor_brief.py --verify    # 改変・未更新の検出
  python3 scripts/priority_rebuild/gen_auditor_brief.py --selftest  # 材料が実体から取れているかの番人
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import sys

import gen_filemap
import gen_windows

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TARGET = ROOT / ".claude" / "auditor_template.md"
WORKFLOW = ROOT / "WORKFLOW.md"
ADOPTED = ROOT / ".claude" / "ratchet" / "adopted_strategies.md"
REQS = ROOT / ".claude" / "rules" / "cat_requirements.md"
DECISIONS = ROOT / ".claude" / "ratchet" / "decisions.md"

START = "<!-- AUDITOR_CONTEXT_START hash={h} ここは gen_auditor_brief.py が自動生成＝手で書き換えない -->"
START_RE = re.compile(r"<!-- AUDITOR_CONTEXT_START hash=[0-9a-f]* [^>]*-->")
END = "<!-- AUDITOR_CONTEXT_END -->"


def _now_line() -> str:
    for line in WORKFLOW.read_text(encoding="utf-8").splitlines():
        if line.startswith("## 🔴 現在地"):
            t = re.sub(r"\*\*|`", "", line)
            return (t[:430] + "…") if len(t) > 440 else t
    return "（WORKFLOW.md に現在地の行が無い）"


def _strategies() -> list[str]:
    txt = ADOPTED.read_text(encoding="utf-8")
    rm = re.search(r"<!-- ROLE_CHECK:(.+?)-->", txt, re.S)
    role = dict(re.findall(r"(\w+)=(\w+)", rm.group(1))) if rm else {}
    out = []
    m = re.search(r"<!-- STRATEGY_ANCHOR:(.+?)-->", txt, re.S)
    if m:
        for item in m.group(1).split(";"):
            item = item.strip()
            if not item or "=" not in item:
                continue
            tok, spec = item.split("=", 1)
            tok = tok.strip()
            f = [x.strip() for x in spec.split(",")] + ["", "", ""]
            out.append(f"| {tok.upper()} | {f[0]} | {f[1]} | {role.get(tok, f[2] or '—')} |")
    pc = re.search(r"<!-- PORTFOLIO_CHECK:(.+?)-->", txt)
    if pc:
        out.append(f"| （採用の柱） | {pc.group(1).strip()} | — | — |")
    return out


def _hard_constraints() -> list[str]:
    out = []
    for line in REQS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(H\d+)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            out.append(f"{m.group(1)}＝{m.group(2).strip()}")
    return out


def _decisions(n: int = 8) -> list[str]:
    if not DECISIONS.exists():
        return []
    out = []
    for line in DECISIONS.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(20\d\d-\d\d-\d\d)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|", line)
        if m:
            d = re.sub(r"\*\*|`", "", m.group(3).strip())
            out.append(f"- {m.group(1)}（{m.group(2).strip()}）{(d[:110] + '…') if len(d) > 115 else d}")
        if len(out) >= n:
            break
    return out


def block_body() -> str:
    L = ["### いまのプロジェクトの現在地（gen_auditor_brief.py が実体から機械生成＝手で書き換えない）",
         "",
         "⚠️ **監査する人へ**: 本テンプレの他の節には 2026-05 時点の記述が残っています。"
         "特に文中の「Phase 0〜7」「LightGBM 14 ラベル独立学習」「k-means クラスタリング」は"
         "**廃止された旧フロー**です。いまのプロジェクトの姿はこの節が唯一の正しい情報です。"
         "矛盾したらこの節が正です。",
         "",
         "**いま何をしているか**", "",
         _now_line(), "",
         "**検証に使う期間（periods.py が唯一の正本）**", "",
         gen_windows.table(), "",
         "> 値決め窓は「値動きの構造が採点窓に近い期間」で選んでいます。時間の近さでは選んでいません。"
         "経緯は .claude/ratchet/windows.md にあります。",
         "",
         "**戦略と役割（adopted_strategies.md の機械可読マーカー）**", "",
         "| 戦略 | 担当する局面 | 方向 | 役割 |", "|---|---|---|---|"]
    L += _strategies()
    L += ["",
          "**使う道具（迷ったら .claude/ratchet/filemap.md）**", "",
          "| やりたいこと | 使うもの |", "|---|---|"]
    L += [f"| {w} | `{n}` |" for w, n, _y in gen_filemap.INDEX]
    L += ["",
          "**守る制約（cat_requirements.md §4.6・違反は最重大インシデント）**", ""]
    L += [f"- {c}" for c in _hard_constraints()]
    L += ["",
          "**まこさんが最近決めたこと（decisions.md・提案の前に必ず読む）**", ""]
    L += _decisions() or ["- （decisions.md から読めなかった）"]
    L += ["",
          "**機械生成の正本（手書きの要約を信用しない）**",
          "",
          "- `.claude/ratchet/windows.md`＝期間の意味と経緯",
          "- `.claude/ratchet/filemap.md`＝何がどこにあるか",
          "- `.claude/ratchet/v9_exits.md`＝V9 の Exit 実装（実コードから抽出）",
          "- `.claude/ratchet/decisions.md`＝まこさんの決定の一覧",
          "- `.claude/state/next_step.md`＝次にやること",
          "",
          "> これらは実体から機械生成され、改変検出がついています。"
          "**手書きの要約は実装とずれている前例があります**"
          "（2026-07-27＝V9 Exit の手書き要約5点のうち2点が実装と食い違っていた）。"]
    return "\n".join(L)


def block() -> str:
    body = block_body()
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return START.format(h=h) + "\n" + body + "\n" + END


def write() -> int:
    t = TARGET.read_text(encoding="utf-8")
    m = START_RE.search(t)
    if not m or END not in t[m.end():]:
        print(f"⚠️ {TARGET.name} に AUDITOR_CONTEXT_START/END の印がない（先に印を置く）")
        return 1
    e = t.index(END, m.end()) + len(END)
    new = t[:m.start()] + block() + t[e:]
    if new != t:
        TARGET.write_text(new, encoding="utf-8")
        print(f"[差し込み] {TARGET.relative_to(ROOT)}")
    else:
        print(f"[変更なし] {TARGET.relative_to(ROOT)}")
    return 0


def verify() -> int:
    t = TARGET.read_text(encoding="utf-8")
    m = START_RE.search(t)
    if not m or END not in t[m.end():]:
        print(f"❌ {TARGET.name} に印がない"); return 1
    cur = t[m.start():t.index(END, m.end()) + len(END)]
    if cur != block():
        print(f"❌ {TARGET.name} の差し込みが実体と食い違う＝手で書き換えたか、実体が動いた")
        print("   直し方: python3 scripts/priority_rebuild/gen_auditor_brief.py --write"); return 1
    print(f"✅ {TARGET.name} の差し込みは実体と一致"); return 0


def selftest() -> int:
    ng = []
    if "現在地" not in _now_line():
        ng.append("WORKFLOW.md から現在地を取れていない")
    if len(_strategies()) < 4:
        ng.append(f"戦略が {len(_strategies())} 件しか取れていない（台帳のマーカーを確認）")
    if len(_hard_constraints()) < 10:
        ng.append(f"ハード制約が {len(_hard_constraints())} 件しか取れていない")
    if not _decisions():
        ng.append("まこさんの決定を1件も取れていない")
    b = block_body()
    for need in ("値決め", "採点", "封印"):
        if need not in b:
            ng.append(f"期間の表に「{need}」が出ていない")
    if block() != block():
        ng.append("実行のたびに中身が変わる")
    if ng:
        print("❌ 自己検査 NG:")
        for x in ng:
            print(f"   - {x}")
        return 1
    print(f"✅ 自己検査 OK（戦略 {len(_strategies())} 件・制約 {len(_hard_constraints())} 件・"
          f"決定 {len(_decisions())} 件・道具 {len(gen_filemap.INDEX)} 件・hash 安定）")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="監査テンプレの現在地を実体から機械生成する")
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.verify:
        sys.exit(verify())
    if a.write:
        sys.exit(write())
    print(block())


if __name__ == "__main__":
    main()
