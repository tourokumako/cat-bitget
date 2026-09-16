#!/usr/bin/env python3
"""gen_session_todo.py — そのセッションの ToDo を、元データから作る。

まこさん指示 2026-09-16（逐語）＝「やるべきことをすべて整理して自動生成でtodo作成しろ」。

なぜ要るか
  103回目の私は ToDo を手で書き、ヌケモレを3件 出した（未決2件の直し・cp37 との突き合わせ・
  Minor を §6 に積む）。まこさんの問い「このtodoではヌケモレ、矮小化、虚偽はないと証明できる？」に
  「証明できません」と答えた。手で書く限り、出どころと照らす仕組みが無い。
  ＝出どころ（まこさんの指示・監査の指摘・決まり・設計書の直す項目）を元データに置き、
    どのやることにも紐づかない出どころが在れば、プログラムが数えて止める。
  恒久69番（文書はプログラムで作る）／next_step §6 の188番（監査と設計書以外の文書も）。

使い方
  python3 .claude/tools/gen_session_todo.py --write    元データから ToDo を作る（置き場は下の決め方）
  python3 .claude/tools/gen_session_todo.py --verify   いまの ToDo が、元データから作ったままかを見る
  python3 .claude/tools/gen_session_todo.py --dry      画面に出すだけ（書かない）
  （--session <id> で置き場を指定できる。省くと、いちばん新しく書かれた置き場）

ヌケモレの数え方（この道具がやること）
  ① 出どころの1件ずつが、やることのどれかの「出どころ」に書かれているか。
     紐づかない出どころが1件でも在れば ❌（rc=1）＝やることに足すか、出どころから外す。
  ② やることが書いた出どころの id が、出どころの一覧に在るか（打ち間違いの検出）。
  ③ ToDo ゲート（enforce_todo_declaration.py）が求める形＝★いまここ が1件だけ・
     状態が3語のどれか・✅済 の記録の欄に worklog の節の番号（§NN）。

限界（正直に）
  ① 出どころの一覧そのものが足りなければ、このプログラムは何も言えない（一覧は私が書く）。
  ② やることの中身が正しいかは見ない（紐づいているかだけ）。
  ③ 元データを手で書き替えれば通る。--verify は「ToDo が元データと合っているか」しか見ない。
  ④ 恒久71番＝文書を作る道具なので、壊すプログラムと自己テストは付けない。走らせて確かめる。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

ROOT = "/Users/tachiharamasako/Documents/GitHub/cat-bitget"
SRC = os.path.join(ROOT, ".claude", "state", "todo_src.json")
SESSIONS = os.path.join(ROOT, ".claude", "state", "sessions")
STATES = ("✅済", "★いまここ", "まだ")
MARK = "<!-- gen_session_todo:"


def newest_session() -> str:
    """いちばん新しく書かれた ToDo の置き場（hook と同じ選び方）。"""
    best, best_t = "", -1.0
    if os.path.isdir(SESSIONS):
        for sid in os.listdir(SESSIONS):
            p = os.path.join(SESSIONS, sid, "session_todo.md")
            if os.path.isfile(p) and os.path.getmtime(p) > best_t:
                best, best_t = sid, os.path.getmtime(p)
    return best


def out_path(sid: str) -> str:
    """書いてよい先＝.claude/state/sessions/<id>/session_todo.md だけ。

    ★名前だけで土台ゲートを通す道具は、Bash から好きなファイルを書ける道になるので、
      書く先を道具の側で限る（gen_audit_docs.py の out_ok と同じ考え方）。
    """
    sid = sid or newest_session()
    if not sid:
        raise SystemExit("[gen_session_todo] ToDo の置き場が見つからない（--session <id> で指定してください）")
    p = os.path.realpath(os.path.join(SESSIONS, sid, "session_todo.md"))
    base = os.path.realpath(SESSIONS)
    if not p.startswith(base + os.sep) or os.path.basename(p) != "session_todo.md":
        raise SystemExit(f"[gen_session_todo] 書いてよい先ではありません: {p}")
    return p


def load() -> dict:
    with open(SRC, encoding="utf-8") as f:
        return json.load(f)


def link_errors(d: dict) -> list:
    """出どころとやることの紐づきを数える（fail-closed）。"""
    errs = []
    ids = [s["id"] for s in d["出どころ"]]
    dup = {i for i in ids if ids.count(i) > 1}
    if dup:
        errs.append(f"出どころの id が重なっている: {sorted(dup)}")
    used = set()
    for t in d["やること"]:
        for sid in t.get("出どころ") or []:
            used.add(sid)
            if sid not in ids:
                errs.append(f"やること {t['番号']} が、出どころの一覧に無い id を書いている: {sid}")
        if not (t.get("出どころ") or []):
            errs.append(f"やること {t['番号']} に出どころが1つも書かれていない")
        if t.get("状態") not in STATES:
            errs.append(f"やること {t['番号']} の状態が3語のどれでもない: {t.get('状態')}")
        if t.get("状態") == "✅済" and "§" not in (t.get("記録") or ""):
            errs.append(f"やること {t['番号']} が ✅済 なのに、記録の欄に worklog の節の番号（§NN）が無い")
    miss = [s for s in d["出どころ"] if s["id"] not in used]
    for s in miss:
        errs.append(f"出どころ「{s['id']}」（{s['何']}）が、どのやることにも入っていない＝ヌケモレ")
    n_here = sum(1 for t in d["やること"] if t.get("状態") == "★いまここ")
    if n_here != 1:
        errs.append(f"★いまここ が {n_here} 件（1件だけにする）")
    return errs


def page(d: dict) -> str:
    ts = d["やること"]
    done = sum(1 for t in ts if t["状態"] == "✅済")
    here = next((t for t in ts if t["状態"] == "★いまここ"), None)
    out = []
    out.append(f"【いまの工程】{d['工程']}")
    out.append(f"【ToDo】全{len(ts)}件のうち {done} 件が ✅済。"
               f"{here['番号'] if here else '—'}（{_head(here)}）が ★いまここ")
    out.append(f"【止まっているもの】{d.get('止まっているもの') or 'なし'}")
    out.append(f"【次】{d.get('次') or _next_line(ts, here)}")
    out.append("")
    out.append("| 番号 | やること | 状態 | 記録 | 出どころ |")
    out.append("|---|---|---|---|---|")
    for t in ts:
        out.append(f"| {t['番号']} | {t['やること']} | {t['状態']} | {t['記録']} | {' ／ '.join(t['出どころ'])} |")
    out.append("")
    out.append("### ★出どころと、やることの対応（★この表はプログラムが作ります）")
    out.append("")
    out.append("| 出どころ | 何 | 出典 | 入っている番号 |")
    out.append("|---|---|---|---|")
    for s in d["出どころ"]:
        ns = [str(t["番号"]) for t in ts if s["id"] in (t.get("出どころ") or [])]
        out.append(f"| {s['id']} | {s['何']} | {s['出典']} | {' ／ '.join(ns) or '**無し**'} |")
    out.append("")
    out.append(f"**出どころ {len(d['出どころ'])} 件のうち、やることに入っていないもの＝"
               f"{sum(1 for s in d['出どころ'] if not any(s['id'] in (t.get('出どころ') or []) for t in ts))} 件。**")
    out.append("")
    oi = d["順番の意図"]
    out.append("### ★順番の意図（恒久58番・3つ書きます）")
    out.append("")
    out.append(f"**まとまりの分け方**＝{oi['まとまりの分け方']}")
    out.append("")
    out.append("**前のものが無いと次ができない関係**")
    out.append("")
    for x in oi["前のものが無いと次ができない関係"]:
        out.append(f"- {x}")
    out.append("")
    out.append(f"**承認と hook で止まる番号**＝{oi['承認と hook で止まる番号']}")
    out.append("")
    out.append("### ★この ToDo に入れていないもの")
    out.append("")
    for x in d["入れていないもの"]:
        out.append(f"- **{x['中身']}**＝{x['理由']}")
    out.append("")
    for x in d["末尾の注記"]:
        out.append(x)
    body = "\n".join(out) + "\n"
    return body + f"\n{MARK} src_sha256={sha_text(json.dumps(d, ensure_ascii=False, sort_keys=True))} -->\n"


def _head(t) -> str:
    if not t:
        return "—"
    s = t["やること"].replace("**", "")
    s = s.split("＝")[0].split("。")[0]
    return s[:28]


def _next_line(ts, here) -> str:
    if not here:
        return "（★いまここ が無い）"
    # ★2026-09-16＝番号の大小でなく、並び順で いまここ より下の「まだ」の最初の1件（25 が 15 と 16 の間に在り、終わった 25 を選んでいた）
    nxt = next((t for t in ts[ts.index(here) + 1:] if t["状態"] == "まだ"), None)
    return (f"私は {here['番号']}（{_head(here)}）をやります。"
            + (f"終わったら {nxt['番号']}（{_head(nxt)}）に進みます。" if nxt else ""))


def sha_text(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--session", default="")
    ap.add_argument("-h", "--help", action="store_true")
    a = ap.parse_args()
    if a.help or not (a.write or a.verify or a.dry):
        print(__doc__)
        return 2
    d = load()
    errs = link_errors(d)
    for e in errs:
        print(f"❌ {e}")
    if errs:
        print(f"ヌケモレと形の食い違い {len(errs)} 件（fail-closed＝直すまで書きません）")
        return 1
    print(f"✅ 出どころ {len(d['出どころ'])} 件とも、やることに入っている"
          f"（やること {len(d['やること'])} 件）")
    body = page(d)
    if a.dry:
        print(body)
        return 0
    p = out_path(a.session)
    if a.verify:
        cur = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""
        same = cur == body
        print(("✅" if same else "❌") + f" --verify: {os.path.relpath(p, ROOT)} は"
              + ("元データから作ったままです" if same else "元データと食い違います（--write で作り直す）"))
        return 0 if same else 1
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(body)
    print(f"✅ --write 完了: {os.path.relpath(p, ROOT)}（{len(body.splitlines())}行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
