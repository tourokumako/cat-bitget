#!/usr/bin/env python3
"""gen_materials.py — 材料の正本の生成器（2026-08-09 新設・マイルストーン①のフロー 段4）

これは何か。
  engine_tuner と observe_diag が条件の材料として使える指標を、1枚の表にする道具。
  ★新しい事実を1つも書かない。既に在るものから機械で引くだけ（フロー 段4 の本文）。

なぜ要るか。
  まこさんの指示（逐語 2026-08-08）＝「入れる材料一覧を正本として自動生成して私が確認できる状態にしてほしい」。
  いまは、材料の一覧が observe_diag のコード・signal_families.md・参照表・検査10 の出力に散っていて、
  1枚で読めない。

1行が何か。
  ★1行＝1つの「指標の種類」。期間で行を分けない（CCI9・CCI20・CCI50 を別の行にしない）。
  理由＝要件の「作ってはいけないもの」2番＝探す値を先に点の一覧で限定するもの、に当たるため。
  期間は範囲の軸として engine_tuner が探す（教訓 L-413）。

欄は7つ（フロー 段4 の本文のとおり）。
  名前 ／ 系統 ／ 答える問い ／ 使える役割 ／ 計算の出どころ ／ グループ ／ 状態

正本（ここから機械で引く・書き写さない）。
  indicator_reference_diag.REFS            … 指標の種類 53 件（名前）
  indicator_reference_diag.FAMILY_LINEAGE  … 系統
  indicator_reference_diag.LINEAGE_QUESTION… 答える問い（出典つき）
  .claude/ratchet/signal_families.json     … 役割ごとに使える系統（role_lineage.roles）
  indicator_reference_diag.INDUSTRY_MAP / EXT2 / REFS[ext] … 計算の出どころと照合の相手
  pandas_ta_classic.Category               … 業界のライブラリの関数（足す候補の出どころ）
  indicator_reference_diag.INDUSTRY_SKIP   … 入れない候補（★まこさんの承認はまだ）

出すもの。
  .claude/ratchet/materials.md   … 人が読む1枚
  .claude/ratchet/materials.json … 機械が読む同じ中身

使い方。
  python3 gen_materials.py --write     … 作る
  python3 gen_materials.py --verify    … 手で書き換えられていないか／正本とずれていないかを検出する
  python3 gen_materials.py --selftest  … 番人（わざと壊すと落ちるか）
  python3 gen_materials.py --status    … いまの状態を表示する
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import indicator_reference_diag as iref   # noqa: E402

_RATCHET = _HERE.parent.parent / ".claude" / "ratchet"
_MD = _RATCHET / "materials.md"
_JSON = _RATCHET / "materials.json"
_SIGFAM = _RATCHET / "signal_families.json"

_GROUP_TBD = "（段8 で埋める）"
_TBD = "（未定・材料に足すときに決める＝段6）"


def _roles_by_lineage() -> dict[str, list[str]]:
    """signal_families.json の role_lineage から「系統 → 使える役割」を作る（書き写さない）。"""
    d = json.loads(_SIGFAM.read_text(encoding="utf-8"))
    roles = d["role_lineage"]["roles"]
    out: dict[str, list[str]] = {}
    for role, v in roles.items():
        for lin in v.get("lineages", []):
            out.setdefault(lin, []).append(role)
    return out


def _lib_funcs() -> dict[str, str]:
    """業界のライブラリの関数名 → カテゴリ。入っていなければ空。"""
    try:
        import pandas_ta_classic as pt
        return {fn: cat for cat, fns in pt.Category.items() for fn in fns}
    except Exception:                                           # noqa: BLE001
        return {}


def _source_note(fam: str, ext_ok: bool) -> str:
    """計算の出どころ＝式は全部 うちの自前。ライブラリに同じものが在るかと、照合の相手を書く。"""
    fns, _note = iref.INDUSTRY_MAP.get(fam, ((), ""))
    x2 = iref.EXT2.get(fam)
    checks = []
    if ext_ok:
        checks.append("ta")
    if x2 is not None:
        checks.append(x2[1])
    lib = f"ライブラリに同じものが在る（{'・'.join(fns)}）" if fns else "ライブラリに相当なし"
    chk = f"照合の相手: {'・'.join(checks)}" if checks else "照合の相手: 無し（手計算の既知答えで担保）"
    return f"うちの自前の式／{lib}／{chk}"


def build_body() -> dict:
    """表の中身を作る（正本から機械で引く）。"""
    rbl = _roles_by_lineage()
    lib = _lib_funcs()
    rows = []
    # ── 状態「在る」＝いま材料カタログに在る指標の種類 ──
    for e in iref.REFS:
        fam = e["family"]
        lin = iref.FAMILY_LINEAGE.get(fam, {}).get("k", "")
        q = iref.LINEAGE_QUESTION.get(lin, ("", ""))[0]
        rows.append(dict(名前=fam, 系統=lin, 答える問い=q,
                         使える役割="・".join(rbl.get(lin, [])) or "（どの役割にも割り当てが無い）",
                         計算の出どころ=_source_note(fam, e["ext"] is not None),
                         グループ=_GROUP_TBD, 状態="在る"))
    # ── 状態「在る」の続き＝参照表 REFS の外にある材料（別の定義表で管理されているもの）──
    #   ★2026-08-09 に、最初この3種類が抜けた材料の正本を出してしまい、自分で気づいて足した。
    #     「答える問い」の表に 需給・時間帯 が在るのに、その系統の行が1つも無かったのが手がかり。
    def _extra(name: str, ref: str, where: str, note: str = "", lin_key: str | None = None) -> None:
        lin = iref.FAMILY_LINEAGE.get(lin_key or name, {}).get("k", "")
        rows.append(dict(名前=name, 系統=lin,
                         答える問い=iref.LINEAGE_QUESTION.get(lin, ("", ""))[0],
                         使える役割=("・".join(rbl.get(lin, [])) or "（どの役割にも割り当てが無い）") + note,
                         計算の出どころ=f"うちの自前の式／定義表 {where}／照合の相手: {ref}",
                         グループ=_GROUP_TBD, 状態="在る"))
    for nm in iref.DEMAND_REF:
        _extra(nm, "検査6（元データの重複・整合・欠け・被覆）", "indicator_reference_diag.DEMAND_REF")
    for nm in getattr(iref, "TIME_REF", {}):
        _extra(nm, "無し（時刻と曜日は元データそのもの）", "indicator_reference_diag.TIME_REF")
    for nm, v in iref.RANGE_GEO_REF.items():
        # kind=price の帯の4隅と mid は、条件の材料に使えない（H6 価格非依存）。
        # 出どころ＝signal_families.json の extra_parts.geo.rule（機械で引く・書き写さない）。
        ng_note = ("（★ただし条件の材料には使えない＝placement の幾何参照専用・H6）"
                   if v.get("kind") == "price" else "")
        _extra(f"レンジ幾何 {nm}", "検査8（定義表・既知答え・切り詰め再計算・被覆）",
               "indicator_reference_diag.RANGE_GEO_REF", ng_note, lin_key="レンジ幾何")
    # ── 状態「足す」「入れない」＝ライブラリに在って、うちの材料に無いもの ──
    covered = {fn for fns, _n in iref.INDUSTRY_MAP.values() for fn in fns}
    for fn, cat in lib.items():
        if fn in covered:
            continue
        skip = iref.INDUSTRY_SKIP.get(fn)
        rows.append(dict(名前=fn, 系統=f"（未定・ライブラリの分類は {cat}）",
                         答える問い=("（指標ではない）" if skip else _TBD),
                         使える役割=("（指標ではない）" if skip else _TBD),
                         計算の出どころ="ライブラリ pandas-ta-classic",
                         グループ=_GROUP_TBD,
                         状態=(f"入れない（{skip}）" if skip else "足す")))
    counts = {"在る": sum(1 for r in rows if r["状態"] == "在る"),
              "足す": sum(1 for r in rows if r["状態"] == "足す"),
              "入れない": sum(1 for r in rows if r["状態"].startswith("入れない"))}
    return dict(rows=rows, counts=counts,
                lineage_question={k: dict(問い=v[0], 出典=v[1]) for k, v in iref.LINEAGE_QUESTION.items()},
                library_ready=bool(lib), library_funcs=len(lib))


def _body_hash(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def render_md(body: dict) -> str:
    h = _body_hash(body)
    c = body["counts"]
    L = [f"<!-- MATERIALS hash={h} gen_materials.py が自動生成＝手で書き換えない -->",
         "# materials.md — 材料の正本（1枚・全自動生成・CC の手書きの行ゼロ）", "",
         "**1行＝1つの指標の種類です。**期間で行を分けていません（CCI9 と CCI20 を別の行にしない）。",
         "理由＝要件の「作ってはいけないもの」2番（探す値を先に点の一覧で限定するもの）に当たるためです。",
         "期間は範囲の軸として engine_tuner が探します。", "",
         f"**いまの数＝在る {c['在る']} 件 ／ 足す {c['足す']} 件 ／ 入れない {c['入れない']} 件"
         f"（合計 {len(body['rows'])} 行）。**", "",
         "> ⚠️ 「入れない」は**まこさんの承認がまだ**です（next_step §5 の10番）。",
         "> 既定は「入れる」です（まこさん決定＝「利益最大化するために完全に不要な指標以外はすべて入れてほしい」）。",
         "> ですからここに載っているのは「指標ではないもの」だけです。", "",
         "> ⚠️ 「グループ」の欄は、この段では全部 空です（フロー 段8 で埋めます）。", ""]
    L += ["## 答える問いの出どころ（系統ごと・1行ずつ）", "",
          "| 系統 | 答える問い | 出典 |", "|---|---|---|"]
    for k, v in body["lineage_question"].items():
        L.append(f"| {k} | {v['問い']} | {v['出典']} |")
    L += ["", "## 材料の一覧", "",
          "| 名前 | 系統 | 答える問い | 使える役割 | 計算の出どころ | グループ | 状態 |",
          "|---|---|---|---|---|---|---|"]
    for r in body["rows"]:
        L.append("| " + " | ".join(r[k] for k in
                                   ("名前", "系統", "答える問い", "使える役割",
                                    "計算の出どころ", "グループ", "状態")) + " |")
    L += ["", "## この表の作り方（正本＝ここから機械で引いています）", "",
          "| 欄 | どこから引いたか |", "|---|---|",
          "| 名前 | `indicator_reference_diag.REFS` の family（指標の種類 53 件） |",
          "| 系統 | `indicator_reference_diag.FAMILY_LINEAGE` |",
          "| 答える問い | `indicator_reference_diag.LINEAGE_QUESTION`（上の表に出典つきで出しています） |",
          "| 使える役割 | `.claude/ratchet/signal_families.json` の `role_lineage.roles`（役割ごとに使える系統） |",
          "| 計算の出どころ | `INDUSTRY_MAP`（ライブラリに同じものが在るか）＋ `REFS[ext]`・`EXT2`（照合の相手） |",
          "| グループ | 空（フロー 段8 で埋める） |",
          "| 状態 | 在る＝参照表に登録済み ／ 足す・入れない＝`pandas_ta_classic.Category` と `INDUSTRY_SKIP` |",
          "", f"（業界のライブラリの関数 {body['library_funcs']} 種類を読み込みました"
          f"{'' if body['library_ready'] else '＝★入っていないので 足す・入れない の行が出ていません'}）", ""]
    return "\n".join(L) + "\n"


def write() -> int:
    body = build_body()
    if not body["library_ready"]:
        print("❌ pandas-ta-classic が入っていない＝『足す』『入れない』の行が作れない。requirements.txt の版で入れる")
        return 1
    _MD.write_text(render_md(body), encoding="utf-8")
    _JSON.write_text(json.dumps(dict(body=body, _本文の指紋=_body_hash(body)),
                                ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    c = body["counts"]
    print(f"[作成] {_MD}（{len(render_md(body).splitlines())} 行）")
    print(f"[作成] {_JSON}")
    print(f"  在る {c['在る']} ／ 足す {c['足す']} ／ 入れない {c['入れない']} ／ 指紋 {_body_hash(body)}")
    return 0


def verify() -> list[str]:
    """手で書き換えられていないか／正本とずれていないかを検出する。"""
    ng: list[str] = []
    if not _MD.exists():
        return ["[未生成] materials.md が無い（--write で作る）"]
    body = build_body()
    if not body["library_ready"]:
        return ["pandas-ta-classic が入っていない＝突き合わせ不能"]
    want = render_md(body)
    got = _MD.read_text(encoding="utf-8")
    if got != want:
        ng.append("materials.md が正本と一致しない（手で書き換えたか、元が変わったのに作り直していない）"
                  f"＝いまの指紋 {_body_hash(body)}")
    if _JSON.exists():
        j = json.loads(_JSON.read_text(encoding="utf-8"))
        if j.get("_本文の指紋") != _body_hash(body):
            ng.append("materials.json の指紋が正本と合わない（--write で作り直す）")
    else:
        ng.append("materials.json が無い（--write で作る）")
    return ng


def selftest() -> int:
    ng: list[str] = []
    body = build_body()
    rows = body["rows"]
    # T1 在るの行数＝4つの定義表の件数の合計と一致する（1つでも取りこぼしたら落ちる）
    want_n = (len(iref.REFS) + len(iref.DEMAND_REF) + len(getattr(iref, "TIME_REF", {}))
              + len(iref.RANGE_GEO_REF))
    if body["counts"]["在る"] != want_n:
        ng.append(f"T1: 『在る』の行数 {body['counts']['在る']} が定義表の合計 {want_n} 件と合わない"
                  f"（参照表 {len(iref.REFS)}＋需給 {len(iref.DEMAND_REF)}"
                  f"＋時間帯 {len(getattr(iref, 'TIME_REF', {}))}＋レンジ幾何 {len(iref.RANGE_GEO_REF)}）")
    # T1-2 「答える問い」の表に在る系統は、材料の行にも必ず出てくる（表だけ在って中身が無いのを防ぐ）
    used_lin = {r["系統"] for r in rows if r["状態"] == "在る"}
    for lin in iref.LINEAGE_KINDS:
        if lin not in used_lin:
            ng.append(f"T1-2: 系統『{lin}』の材料が1行も無い（答える問いの表にだけ在る状態）")
    # T2 在るの行に、系統・答える問い・使える役割の空欄が無い
    for r in rows:
        if r["状態"] != "在る":
            continue
        for k in ("系統", "答える問い"):
            if not r[k]:
                ng.append(f"T2: 『{r['名前']}』の{k}が空（正本から引けていない）")
        if r["系統"] not in iref.LINEAGE_KINDS:
            ng.append(f"T2: 『{r['名前']}』の系統『{r['系統']}』が系統の一覧に無い")
    # T3 グループの欄はこの段では全部 空（段8 の前）
    if any(r["グループ"] != _GROUP_TBD for r in rows):
        ng.append("T3: グループの欄が埋まっている行がある（埋めるのは段8）")
    # T4 期間で行を分けていない。
    #   ★数字が入っているかでは見ない（pivotR1 の「1」は期間ではなく水準の名前）。
    #   参照表の照合にかけて「パラメータが付いた形（RSI14 など）」になっていないかで見る。
    got_names = {r["名前"] for r in rows if r["状態"] == "在る"}
    want_names = ({e["family"] for e in iref.REFS} | set(iref.DEMAND_REF)
                  | set(getattr(iref, "TIME_REF", {}))
                  | {f"レンジ幾何 {k}" for k in iref.RANGE_GEO_REF})
    if got_names != want_names:
        ng.append(f"T4: 『在る』の名前が参照表の指標の種類と一致しない"
                  f"（余分 {sorted(got_names - want_names)[:3]} ／ 欠け {sorted(want_names - got_names)[:3]}）")
    for nm in sorted(got_names):
        _e, _p = iref.find(nm)
        if _e is not None and _p:
            ng.append(f"T4: 『{nm}』は期間つきの名前（1行＝指標の種類の決まりに反する）")
    # T5 答える問いの出どころが、系統の数だけ揃っている
    if set(body["lineage_question"]) != set(iref.LINEAGE_KINDS):
        ng.append("T5: 答える問いの表が、系統の一覧と食い違う")
    # T6 わざと書き換えると --verify が鳴る（メタ確認）
    if _MD.exists():
        keep = _MD.read_text(encoding="utf-8")
        try:
            _MD.write_text(keep + "この行は手で足しました\n", encoding="utf-8")
            if not verify():
                ng.append("T6: 手で書き足しても --verify が鳴らない（改変検出が死んでいる）")
        finally:
            _MD.write_text(keep, encoding="utf-8")
        if verify():
            ng.append("T6: 元に戻したのに --verify が鳴る（番人の後始末ができていない）")
    else:
        ng.append("T6: materials.md が無いので改変検出を確かめられない（先に --write）")
    print("=" * 70)
    print("gen_materials 自己検査")
    print("=" * 70)
    for x in ng:
        print("  ❌ " + x)
    print("  ✅ 全部 pass" if not ng else f"  ❌ {len(ng)} 件")
    return 1 if ng else 0


def status() -> int:
    body = build_body()
    c = body["counts"]
    print(f"materials.md: {'在る' if _MD.exists() else '無い'} ／ 在る {c['在る']} ／ 足す {c['足す']}"
          f" ／ 入れない {c['入れない']} ／ 指紋 {_body_hash(body)}")
    for x in verify():
        print("  ❌ " + x)
    return 0


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--verify" in argv:
        ng = verify()
        for x in ng:
            print("  ❌ " + x)
        print("  ✅ 一致（手で書き換えられていない）" if not ng else "")
        return 1 if ng else 0
    if "--write" in argv:
        return write()
    if "--status" in argv:
        return status()
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
