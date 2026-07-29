#!/usr/bin/env python3
"""gen_engine_tuner_requirements.py — engine_tuner の要件定義書を機械生成する（手書き禁止・2026-07-27 まこさん指示）

なぜ機械生成か
--------------------------------------------------------------------------
要件は動かしながら変わる（まこさん確定 2026-07-27・逐語「現状で抜けてるものはわからないので、
作ってみて実際に動かして必要な機能を足していきたい」）。手書きの要件定義書は、要件が変わるたびに
書き直しが要り、実体とずれる。要件を json に置いて文書を機械生成すれば、json を1行直して
作り直すだけで済む。gen_design.py / gen_flow.py / gen_observe_manual.py / gen_engine_tuner_manual.py の5本目。

説明書（engine_tuner_manual.md）との違い
--------------------------------------------------------------------------
  説明書   = いま実体が何をできるかの記録（材料＝コードと設定ファイル）
  要件定義書 = これから何をできるようにするかの正本（材料＝engine_tuner_requirements.json）
2つが揃うと「今どこまで来たか」が機械で見える。

使い方
--------------------------------------------------------------------------
  python3 gen_engine_tuner_requirements.py --write     # 生成して .claude/ratchet/ に書く
  python3 gen_engine_tuner_requirements.py --verify    # 手書き改変の検出（ハッシュ照合）
  python3 gen_engine_tuner_requirements.py --selftest  # 自己検査（材料が json から取れているかの番人）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]                                   # bitget-python-sdk-api/
REQ = ROOT / ".claude" / "ratchet" / "engine_tuner_requirements.json"
OUT = ROOT / ".claude" / "ratchet" / "engine_tuner_requirements.md"
MANUAL = ROOT / ".claude" / "ratchet" / "engine_tuner_manual.md"

NEED_KEYS = ("id", "title", "source", "decided", "why", "accept", "state")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def _c(s) -> str:
    """表のセルに入れる文字列を無害化する（縦棒と改行で表が崩れるため）。"""
    return str(s).replace("|", "\\|").replace("\n", " ").strip()


def _load() -> dict:
    raw = REQ.read_text(encoding="utf-8")
    # ★手書き秒数の検出（CP2 監査 4-23 への対応・2026-07-30 まこさん確認済み fix_map）
    #   実測の秒数は engine_tuner_timing.json が正本＝json に「N秒」「N.N秒」を手で書いたら生成を止める。
    #   背景＝「1試行およそ7秒」（別の道具の値）と「0.41秒／2.79秒」の手書きが2回続けて混入した。
    import re as _re
    hand = _re.findall(r"\d+(?:\.\d+)?秒", raw)
    if hand:
        raise SystemExit(f"[手書き数値エラー] json に秒数のリテラルがある: {sorted(set(hand))}"
                         "＝実測は engine_tuner_timing.json が正本。文言を「timing.json が正本」に直すこと")
    return json.loads(raw)


def build() -> str:
    d = _load()
    reqs = d["requirements"]
    L: list[str] = []
    L.append("# engine_tuner 要件定義書（gen_engine_tuner_requirements.py が自動生成＝手書き禁止）")
    L.append("")
    L.append("⚠️ このファイルを手で書き換えないでください。中身は")
    L.append(f"   `{REQ.relative_to(ROOT)}` から機械で取っています。")
    L.append("   要件を足す・変えるときは、その json を直してから作り直します。")
    L.append("")
    L.append("```")
    L.append("python3 scripts/priority_rebuild/gen_engine_tuner_requirements.py --write   # 作り直す")
    L.append("python3 scripts/priority_rebuild/gen_engine_tuner_requirements.py --verify  # 改変の検出")
    L.append("```")
    L.append("")

    L.append("## この文書は何か")
    L.append("")
    L.append("**これから engine_tuner に何をできるようにするかの正本です。**")
    L.append("")
    L.append("いま実体が何をできるかの記録は別にあります。")
    L.append(f"`{MANUAL.relative_to(ROOT)}`（実体のコードと設定ファイルから機械生成）です。")
    L.append("2つを並べると、今どこまで来たかが分かります。")
    L.append("")

    L.append("## 進め方の方針")
    L.append("")
    for p in d.get("policy", []):
        L.append(f"- {p}")
    L.append("")

    L.append("## この道具の目的")
    L.append("")
    for p in d["purpose"]:
        L.append(f"- {p}")
    L.append("")
    L.append(f"出典: {d.get('purpose_source', '')}")
    L.append("")

    # ★目的の正確な意味（まこさん指示 2026-07-27・逐語「新セッションで記憶のないCCが、誤解や矮小化のない
    #   正確な理解が伝わるような文章にして、engine_tunerの要件定義の目的とかに目立つように書いておいて」）。
    #   ここが消えると、次の CC が目的を「値の微調整」や「768列から選ぶ」や「V9 のコピー」に読み替える。
    #   2026-07-27 に実際に5回外した型を、名指しで残してある。selftest が消失を検出する。
    if d.get("purpose_reading"):
        L.append("---")
        L.append("")
        L.append("## ★★ この目的の正確な意味（読み替え防止・着手の前に必ず読む）")
        L.append("")
        prev_item = False
        for para in d["purpose_reading"]:
            is_item = para.lstrip().startswith("- ")
            if prev_item and not is_item:
                L.append("")                       # 箇条書きが終わったら段落との間を空ける
            L.append(para)
            if para.strip() and not is_item:
                L.append("")
            prev_item = is_item
        L.append("---")
        L.append("")

    u = d.get("usage", {})
    if u:
        L.append("## 使う順番")
        L.append("")
        L.append("```")
        L.append("▼既存のロジックを直すとき")
        L.append(f"  {u.get('existing', '')}")
        L.append("")
        L.append("▼新しいロジックを作るとき")
        L.append(f"  {u.get('new', '')}")
        L.append("```")
        L.append("")
        if u.get("note"):
            L.append(f"> {u['note']}")
            L.append("")

    # 進み具合（state の集計）＝「作って動かして足す」の現在地が1行で見える
    states: dict[str, int] = {}
    for r in reqs:
        states[r["state"]] = states.get(r["state"], 0) + 1
    L.append("## 進み具合")
    L.append("")
    L.append(f"要件は全部で {len(reqs)} 件です。" + "／".join(f"{k} {v} 件" for k, v in states.items()) + "。")
    L.append("")

    L.append("## 要件の一覧")
    L.append("")
    L.append("| # | 何をできるようにするか | 状態 | いまどこまで |")
    L.append("|---|---|---|---|")
    for r in reqs:
        L.append(f"| {_c(r['id'])} | {_c(r['title'])} | {_c(r['state'])} | {_c(r.get('progress', '—'))} |")
    L.append("")

    L.append("## 要件の中身")
    L.append("")
    for r in reqs:
        L.append(f"### {r['id']} — {r['title']}")
        L.append("")
        L.append(f"- **決めたこと**: {r['decided']}")
        L.append(f"- **なぜ要るか**: {r['why']}")
        L.append(f"- **何ができたら満たしたと言えるか**: {r['accept']}")
        if r.get("precondition"):
            L.append(f"- **前提**: {r['precondition']}")
        L.append(f"- **どこから来たか**: {r['source']}")
        L.append(f"- **状態**: {r['state']}")
        if r.get("progress"):
            L.append(f"- **いまどこまで**: {r['progress']}")
        # ★どう作るか（設計）＝まこさんが中身を判断するための節。承認の前にここを埋める
        #   （2026-07-27 まこさん指摘「知見が浅いまま浅い提案をするな」＝根拠と出典つきで出す）。
        if r.get("design"):
            L.append("")
            L.append(f"#### {r['id']} をどう作るか（設計・まこさんの承認待ち）")
            L.append("")
            # ★表の行と空行のあとには空行を足さない（2026-07-27）。
            #   一律に空行を挟むと、表の行が1行ずつ分断されて表として描画されなくなる。
            for para in r["design"]:
                L.append(para)
                if para.strip() and not para.lstrip().startswith("|"):
                    L.append("")
        if r.get("design_sources"):
            L.append("**この設計の出どころ**")
            L.append("")
            for s in r["design_sources"]:
                L.append(f"- {s}")
        L.append("")

    L.append("## この道具でやらないこと")
    L.append("")
    for x in d.get("out_of_scope", []):
        L.append(f"- {x}")
    L.append("")

    L.append("## 守る制約")
    L.append("")
    for x in d.get("constraints", []):
        L.append(f"- {x}")
    L.append("")

    L.append("## できたことをどう確かめるか")
    L.append("")
    for x in d.get("verification", []):
        L.append(f"- {x}")
    L.append("")

    body = "\n".join(L).rstrip() + "\n"
    return f"<!-- REQ_HASH={_sha(body)} -->\n{body}"


def verify() -> int:
    if not OUT.exists():
        print(f"❌ 要件定義書が無い: {OUT}")
        return 1
    txt = OUT.read_text(encoding="utf-8")
    head, _, body = txt.partition("\n")
    want = head.replace("<!-- REQ_HASH=", "").replace(" -->", "").strip()
    got = _sha(body)
    if want != got:
        print(f"❌ 手書きで書き換えられている（ハッシュ不一致 期待 {want} / 実際 {got}）")
        return 1
    print(f"✅ 改変なし（ハッシュ {got}）")
    return 0


def selftest() -> int:
    ng = []
    if not REQ.exists():
        print(f"❌ 要件の json が無い: {REQ}")
        return 1
    d = _load()
    reqs = d.get("requirements") or []
    if len(reqs) < 1:
        ng.append("要件が1件も無い")
    for r in reqs:
        miss = [k for k in NEED_KEYS if not r.get(k)]
        if miss:
            ng.append(f"{r.get('id', '?')} に必須の項目が無い: {miss}")
    ids = [r.get("id") for r in reqs]
    if len(ids) != len(set(ids)):
        ng.append("要件の id が重複している")
    if len(d.get("purpose") or []) < 2:
        ng.append("目的が2項目そろっていない（まこさん確定 2026-07-27 は2項目）")
    for need in ("組み合わせロジックを見つけ", "改善すべき点を見つけ", "利益最大化、損失最小化するまで調整する"):
        if not any(need in p for p in d.get("purpose", [])):
            ng.append(f"目的の逐語が欠けている: {need}")
    # ★目的の正確な意味が消えていないこと（まこさん指示 2026-07-27）＝ここが消えると次の CC が読み替える
    if not d.get("purpose_reading"):
        ng.append("目的の正確な意味（purpose_reading）が消えている＝次の CC が目的を読み替える")
    for need in ("ロジックそのものを組み立てられる器", "V9 は到達目標ではありません",
                 "やってはいけない読み替え", "設定した戦略や条件に沿った"):
        if not any(need in p for p in d.get("purpose_reading", [])):
            ng.append(f"目的の正確な意味の逐語が欠けている: {need}")
    if not d.get("out_of_scope"):
        ng.append("やらないことが書かれていない（範囲が閉じない）")
    if not d.get("constraints"):
        ng.append("守る制約が書かれていない")
    # 「作って動かして足す」の方針が消えないこと（まこさん確定 2026-07-27）
    if not any("作ってみて実際に動かして" in p for p in d.get("policy", [])):
        ng.append("進め方の方針の逐語が欠けている: 作ってみて実際に動かして")
    txt = build()
    for must in ("この文書は何か", "進め方の方針", "この道具の目的",
                 "この目的の正確な意味", "使う順番", "進み具合",
                 "要件の一覧", "要件の中身", "この道具でやらないこと", "守る制約",
                 "できたことをどう確かめるか"):
        if must not in txt:
            ng.append(f"要件定義書に見出しが無い: {must}")
    for r in reqs:
        if r["id"] not in txt or r["title"] not in txt:
            ng.append(f"要件が文書に出ていない: {r['id']}")
    # 番人＝json を差し替えたら生成物も変わること（＝json から取っている証拠）。
    # ★退避は「生のテキスト」で取る（2026-07-27 修正）。json.dumps で取り直すと整形と空行が失われ、
    #   自己検査を走らせるたびに正本の json が1行に潰れる（最初の実装のバグ・実走で検出）。
    keep = REQ.read_text(encoding="utf-8")
    try:
        d2 = json.loads(keep)
        d2["requirements"].append({"id": "R99", "title": "番人用のダミー", "source": "番人",
                                   "decided": "番人", "why": "番人", "accept": "番人", "state": "未着手"})
        REQ.write_text(json.dumps(d2, ensure_ascii=False, indent=1), encoding="utf-8")
        if "番人用のダミー" not in build():
            ng.append("要件の一覧が json を見ていない（json を変えても文書が変わらない）")
    finally:
        REQ.write_text(keep, encoding="utf-8")
    print("=" * 80)
    print("gen_engine_tuner_requirements 自己検査")
    print("=" * 80)
    print(f"  要件 {len(reqs)} 件 / やらないこと {len(d.get('out_of_scope', []))} 件 / "
          f"制約 {len(d.get('constraints', []))} 件")
    print(f"  出力先 {OUT}")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="engine_tuner の要件定義書を機械生成する")
    ap.add_argument("--write", action="store_true", help="生成して書き出す")
    ap.add_argument("--verify", action="store_true", help="手書き改変の検出")
    ap.add_argument("--selftest", action="store_true", help="自己検査")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    if a.verify:
        sys.exit(verify())
    txt = build()
    if a.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(txt, encoding="utf-8")
        print(f"✅ 書き出した: {OUT}（{len(txt.splitlines())}行）")
    else:
        print(txt)


if __name__ == "__main__":
    main()
