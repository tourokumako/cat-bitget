#!/usr/bin/env python3
"""gen_stage0_match.py — §2.2 の候補と、成績表の材料を突き合わせる（段0 の①）。

なぜ作るか
----------
まこさん指示 2026-09-09（逐語）＝「その突き合わせを作る。」

何が問題か（2026-09-09 に実測して分かったこと）
  §2.2（レンジ判定の検索方法・まこさん決定 2026-09-01）は、探す候補を
  **指標の名前**で書いている（例＝「転換線・基準線」「帯内位置%」）。
  ところが engine_tuner は、材料を **役割**（env／location／sufficiency／trigger）で引く。
  この2つが噛み合っているかを、誰も突き合わせていなかった。
  実測の例＝段1 は location から引く段だが、そこが名指しする「転換線・基準線」は
  成績表の location に0列で、132列は全部 env に入っていた。

何をするか
----------
  §2.2 の段ごとの候補を1つずつ、成績表（material_ranking.json）で探し、
  「どの役割の・どの性質に・何列 在るか」を表にする。
  その段が引く役割に0列なら、その候補はその段では引けない＝表に ❌ と出す。

  --write   突き合わせ表を stage0_match.md に書く
  --show    書かずに画面に出す

★候補の一覧は、元データ `.claude/ratchet/m2_stage_candidates.json` から読む（2026-09-11 に直した）。
  ★直す前は、この道具の中に手で書いていた（50行）。まこさん指示 2026-09-11（逐語）＝
    「手書きで書き換えられないようにプログラムが読める対応付けをすればいいのでは？」
    「この文書の指標の表記が正本通りじゃないのであれば、正本から自動生成する形で修正すべきなのでは？」
  ★元データに書ける指標の名前は、正本（indicator_reference_diag.FAMILY_LINEAGE・263件）に
    実在するものだけ＝`gen_regime_kb.py --write stage` が照らして、外れたら止まる。

fail-closed（黙って通さない・3つ）
  1. 成績表が読めない → 止まる
  2. 候補の元データが無い・段が0件 → 止まる（段を黙って飛ばさない）
  3. 指標の正本を読めない → 止まる（系統を指標の名前に展開できないため）

限界（正直に）
  ・名前で探すので、成績表の列名と §2.2 の書き方がずれていると「無い」と出る。
    ずれか、本当に無いかは、出た表を人が見て判じる。
  ・この道具は「在るか無いか」を数えるだけ。使うべきかどうかは判じない。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
RATCHET = SDK / ".claude" / "ratchet"

RANKING = RATCHET / "material_ranking.json"
DEST = RATCHET / "stage0_match.md"

# ── §2.2 の段ごとの候補 ──
#   ★2026-09-11（まこさん指示・逐語）＝「手書きで書き換えられないようにプログラムが読める
#     対応付けをすればいいのでは？」「この文書の指標の表記が正本通りじゃないのであれば、
#     正本から自動生成する形で修正すべきなのでは？」
#   ★直す前は、この場所に候補の一覧を手で書いていた（50行）。私が書き換えられる状態で、
#     実際に本数が監査の実測に近づくまで絞り方を3回 書き換えた（618本 → 444本 → 完全一致）。
#   ★直した後＝元データ `m2_stage_candidates.json` から読む。その元データは、書いてある
#     指標の名前が正本に実在するかを `gen_regime_kb.py --write stage` が照らす（fail-closed）。
CANDS = RATCHET / "m2_stage_candidates.json"

ROLES = ("env", "location", "sufficiency", "trigger")


def load_stages() -> list:
    """§2.2 の候補の一覧を、元データから読む（★指標の名前を手で書かない・2026-09-11）。

    戻り＝[(段の名前, その段が引く役割, [(候補の名前, 成績表で探す文字), ...]), ...]
    ★指標の候補を持たない段（数字の候補＝段3）は、理由つきで空の一覧にして返す。
    ★展開（語 → 正本の指標の名前）は `gen_regime_kb.expand_stage` の1か所に置く。
      この道具・engine_tuner・§2.2 の表 の3つが、同じ関数を呼ぶ＝判定を書き写さない。
    """
    if not CANDS.exists():
        raise SystemExit(f"[gen_stage0_match] 候補の元データが無い: {CANDS}（fail-closed）")
    try:
        import gen_regime_kb as grk                            # 同じ .claude/tools に在る
    except Exception as e:                                     # noqa: BLE001
        raise SystemExit(f"[gen_stage0_match] 展開の道具を読めない: {e}（fail-closed）")
    ex = grk.expand_stage()
    fam_lin, _l, _g, _p = grk._load_indicator_refs()
    out = []
    for _k, s in ex.items():
        cands = []
        # ★レンジ幾何は、指標の名前ではなく その中の列（W%・帯内位置%）で探す
        for c in (s.get("geo_cols") or []):
            cands.append((f"{c}（レンジ幾何の列）", c))
        for f in (s.get("families") or []):
            if f == "レンジ幾何":
                continue                                       # 列は上で出した
            cands.append((f, f))
        # ★系統でまとめて足した分を、正本から指標の名前に展開する
        for ln in (s.get("lineages") or []):
            for f, v in fam_lin.items():
                if (v or {}).get("k") == ln:
                    cands.append((f"{f}（{ln} の系統）", f))
        if s.get("bool_col"):
            cands.append((f"{s['bool_col']}（真偽の列）", s["bool_col"]))
        out.append((s.get("stage"), s.get("role"), cands))
    if not out:
        raise SystemExit("[gen_stage0_match] 段が0件（fail-closed）")
    return out


def load_ranking() -> dict:
    """成績表を読む。読めなければ止まる（fail-closed の1つ目）。"""
    if not RANKING.exists():
        raise SystemExit(f"[gen_stage0_match] 成績表が無い: {RANKING}（fail-closed）")
    return json.loads(RANKING.read_text(encoding="utf-8"))


def columns_of(rank: dict, role: str) -> list:
    """その役割に載っている列の名前を全部 集める。戻り＝[(列名, 性質), ...]。"""
    out = []
    for label, by_horizon in (rank.get("順位", {}).get(role) or {}).items():
        for _hor, rows in (by_horizon or {}).items():
            for r in rows:
                out.append((str(r[0]), label))
    return out


def count_hits(cols: list, needle: str) -> tuple:
    """その文字を含む列が何本 在るか。戻り＝(本数, 性質ごとの内訳)。"""
    hit = [(c, lab) for (c, lab) in cols if needle in c]
    by_label = {}
    for _c, lab in hit:
        by_label[lab] = by_label.get(lab, 0) + 1
    return len(hit), by_label


def build() -> str:
    """突き合わせ表を組み立てる。"""
    rank = load_ranking()
    cols_by_role = {r: columns_of(rank, r) for r in ROLES}

    L = []
    add = L.append
    add("# 段0 の①｜§2.2 の候補と、成績表の材料の突き合わせ")
    add("")
    add("**★この表はプログラムが作ります（手で書き換えない）。**"
        "出どころ＝`engine_tuner_milestones2.md` の §2.2 の段の表と、"
        "`material_ranking.json`。")
    add("")
    add("**なぜ在るか**＝§2.2 は探す候補を**指標の名前**で書き、"
        "engine_tuner は材料を**役割**で引きます。その2つが噛み合っているかを、"
        "誰も突き合わせていませんでした。")
    add("")
    add("**読み方**＝「その段の役割」の欄が **0** なら、その候補はその段では引けません。"
        "他の役割に列が在るなら、役割がずれているということです。")
    add("")

    ng_total = 0
    for stage, role, cands in load_stages():
        if role not in cols_by_role:
            # ★役割を持たない段（段2b＝真偽の列 rg5_uptrend の借用）。成績表の材料ではないので
            #   突き合わせられない。黙って飛ばさず、理由を出す。
            add(f"## {stage}")
            add("")
            add("**この段は、成績表の材料を引きません**（候補は真偽の列の借用＝"
                + "・".join(f"`{n}`" for _nm, n in cands) + "）。"
                "**だから突き合わせの対象外です。**")
            add("")
            continue
        if not cands:
            # ★指標の候補を持たない段（段3＝続く本数と緩め幅の数字）。黙って飛ばさず、理由を出す。
            add(f"## {stage}")
            add("")
            add("**この段は、指標の候補を持ちません**（候補は数字＝続く本数と緩め幅）。"
                "**だから成績表との突き合わせの対象外です。**")
            add("")
            continue
        add(f"## {stage}")
        add("")
        add(f"**この段が引く役割＝`{role}`**")
        add("")
        add("| 候補（§2.2 の書き方） | この段の役割に何列 | 性質の内訳 | 他の役割に在る分 | 判定 |")
        add("|---|---|---|---|---|")
        for name, needle in cands:
            n, by_label = count_hits(cols_by_role[role], needle)
            others = []
            for r in ROLES:
                if r == role:
                    continue
                m, _b = count_hits(cols_by_role[r], needle)
                if m:
                    others.append(f"{r} {m}")
            inner = "・".join(f"{k} {v}" for k, v in sorted(by_label.items())) if by_label else "—"
            other_s = "・".join(others) if others else "—"
            if n > 0:
                verdict = "✅ 引ける"
            elif others:
                verdict = "❌ 役割がずれている"
                ng_total += 1
            else:
                # ★2026-09-11＝「成績表に無い」と断じない。この道具は「列名にその文字が含まれるか」で
                #   数えるだけで、成績表の列名は 指標の名前＋期間＋札 の形（例＝`close vs 24本高値%`・
                #   `EMA20傾き%`）。engine_tuner は列を指標の名前に解いてから引くので、ここで 0 でも
                #   引けることが在る。本当に引けるかは engine_tuner 側の自己テスト（条件12 の④）で測る。
                verdict = "⚠️ この探し方では当たらない（列名の形が違う・engine_tuner は引ける場合あり）"
                ng_total += 1
            add(f"| {name} | **{n}** | {inner} | {other_s} | {verdict} |")
        add("")

    add("## まとめ")
    add("")
    add(f"**この探し方で当たらなかった候補＝{ng_total}件。**")
    add("")
    add("**当たらない理由は2通りです。**①役割がずれているもの（成績表の別の役割に列が在る）"
        "②**この道具の探し方では当たらないもの**。②は「成績表に無い」とは限りません。"
        "この道具は「列名にその文字が含まれるか」で数えるだけで、成績表の列名は"
        "**指標の名前＋期間＋札**の形です（例＝`close vs 24本高値%`・`EMA20傾き%`）。"
        "**engine_tuner は列を指標の名前に解いてから引くので、ここで 0 でも引けます。**"
        "本当に引けるかは engine_tuner 側の自己テスト（完成の条件の条件12 の④）で測ります。")
    add("")
    add("**★この表は「この探し方で当たるか」を数えただけです。**どうするかは決めていません。")
    add("")
    return "\n".join(L)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--write", action="store_true", help="突き合わせ表を書く")
    p.add_argument("--show", action="store_true", help="書かずに画面に出す")
    a = p.parse_args()
    body = build()
    if a.write:
        DEST.write_text(body, encoding="utf-8")
        print(f"✅ --write 完了: {DEST}（{len(body.splitlines())}行）")
        return 0
    print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
