#!/usr/bin/env python3
"""gen_composition_rules.py — 場面ごとの法則の生成器（2026-08-08 新設）

★2026-08-29 に実物で確かめた事実（まこさん指示「マコを欺くためだけの無意味な道具って書いておけ」）。
  この道具が出す composition_rules.json を、engine_tuner は読んでいない。
  engine_tuner_gen.py:2188 が load_scene_rules() を呼ぶが、返り値を変数に受け取らずに捨てている。
  確かめているのは「ファイルが開けるか」だけ。
  場面ごとの法則 K-1〜K-7 の判定は、engine_tuner_exec.py の1094〜1119行にコードとして直接 書いてある。
  ＝この道具が作る文書を直しても、engine_tuner の動きは1バイトも変わらない。
  ★CC はこの状態を 2026-08-08 から 2026-08-29 まで確かめず「engine_tuner が守る法則」として報告し続けた。

これは何か。
  engine_tuner の設定のうち、型の表・格子・出口の枝から機械で引く部分を、1つの完成品に集める道具。
  ★2026-08-30（M2-B0・まこさん承認 iter="m2-b0-law-reader-20260830"）＝場面ごとの7件（K-1〜K-7）は
    recipes/composition_rules_src.json から消し、regime_laws.json の各法則の「機械が読む判定」へ移した。
    読むのは engine_tuner_exec.load_regime_laws・審査は G7＝この道具は場面ごとの法則をもう持たない。
    手で書く行は 0件（composition_rules_src.json に残るのは移動と削除の記録だけ）。
  ★2026-08-29（まこさん承認 rules30-to-7-20260829）に30件から7件へ減らした。
    消した23件（ROLE-・TF-・TW-・FT-・Q-・RD-・CN-・RG-）は engine_tuner の2本のコードに
    記号が1回も出なかった＝案の作り方にも捨て方にも効いていなかった。
    逐語の出典がほかに無かった6件は technical_analysis_knowledge_base.md の §J へ移した。

なぜ作られたか（2026-08-08 の当時の目的・★達成されていない）。
  2026-08-08 の重大インシデント #14＝engine_tuner の案の作り方がくじ引きだった（まこさん認定「論外」）。
  くじを引く代わりに「相場の法則で候補を絞る」ためには、その相場の法則が機械の読める形で無いといけない。
  ★この道具は形を作ったが、engine_tuner はその形を読んでいない＝目的は達成されていない。

正本（ここから機械で引く・書き写さない）。
  .claude/ratchet/signal_families.json … 部品105種・時間足9本・使えない部品3種・向きの読み込ませる法則 DC1〜DC4・系統
  indicator_reference_diag.FAMILY_LINEAGE … 系統の分類（signal_families の inventory と一致することを照合）
  recipes/search_limits.json … 閾値の段と探索の格子
  .claude/ratchet/exit_families.json … 出口の枝

出すもの。
  .claude/ratchet/composition_rules.json … ★「engine_tuner が読む完成品」と書いてあったが、読んでいない
  .claude/ratchet/composition_rules.md  … 人が読む説明（同じ中身）

いま実際に使われている先（2026-08-30 に直した）。
  gen_audit_request.py:129   … 監査依頼書の必読6本の1本として composition_rules.md を渡す
  ★engine_tuner はこのファイルを読まない＝場面の審査の正本は regime_laws.json（M2-B0）。
    旧 engine_tuner_gen.py:2188 の「開けるかの確かめ」も ex.load_regime_laws へ向け直した。

使い方。
  python3 gen_composition_rules.py --write     … 作る
  python3 gen_composition_rules.py --verify    … 人の手書きと、正本とのずれを検出する
  python3 gen_composition_rules.py --selftest  … 番人（わざと壊すと落ちるか）
  python3 gen_composition_rules.py --status    … いまの状態を表示する
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

here = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(here))
import indicator_reference_diag as iref  # noqa: E402  系統の分類の正本

ratchet = (here / ".." / ".." / ".claude" / "ratchet").resolve()
src_path = here / "recipes" / "composition_rules_src.json"
signal_path = ratchet / "signal_families.json"
limits_path = here / "recipes" / "search_limits.json"
exits_path = ratchet / "exit_families.json"
out_json = ratchet / "composition_rules.json"
out_md = ratchet / "composition_rules.md"

# ★GENERATES＝この道具が作る文書の名乗り（2026-08-16 新設・まこさん決定 A）。
#   なぜ要るか＝名前で数えると必ず漏れる（出力先の変数名が道具ごとにバラバラで、
#   読むファイルと作るファイルが同じ形で並んでいる＝外から見分けられない）。
#   だから道具の側に名乗らせる。集める道具＝gen_docmap.py。
#   形＝(リポジトリの根からのパス, "まるごと" か "一部の節")。
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/composition_rules.json", "まるごと"),
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/composition_rules.md", "まるごと"),
]


class RuleError(SystemExit):
    """読み込ませる法則のヌケモレ・正本とのずれ。fail-closed＝止める。"""


def _sha(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ── 1. 正本を読む ─────────────────────────────────────────────────────────
def load_sources(src_override: dict | None = None) -> dict:
    """手書きの元ファイルと、4つの正本を読む。src_override は番人が壊した版を渡すため。"""
    for p in (src_path, signal_path, limits_path, exits_path):
        if not p.exists():
            raise RuleError(f"[正本なし] {p} が見つからない")
    src = src_override if src_override is not None else json.loads(src_path.read_text())
    sig = json.loads(signal_path.read_text())
    lim = json.loads(limits_path.read_text())
    exi = json.loads(exits_path.read_text())

    lineage_of = sig["inventory"]["lineage_of"]
    # 系統の分類は2箇所に在る。ずれていたら止める（片方が黙って動くのを防ぐ）
    for part, kind in lineage_of.items():
        ref = iref.FAMILY_LINEAGE.get(part)
        if ref is not None and ref.get("k") != kind:
            raise RuleError(f"[系統のずれ] {part}: 表={kind} / カタログ={ref.get('k')}")

    return {"src": src, "signal": sig, "limits": lim, "exits": exi,
            "lineage_of": lineage_of}


# ── 2. 読み込ませる法則を展開する ───────────────────────────────────────────────────
def _banned_pairs(sig: dict) -> set:
    return {(d["part"], d["tf"]) for d in sig["bans"]["insufficient_samples"]["pairs"]}


def _extra_lineage(sig: dict) -> dict:
    """追加の部品（レンジ幾何・時間帯）の系統。表の extra_parts が正本。"""
    out = {}
    ex = sig.get("extra_parts") or {}
    for name in (ex.get("geo") or {}).get("parts", []):
        out[name] = "構造・位置"
    for name in (ex.get("time") or {}).get("parts", []):
        out[name] = "時間帯"
    return out


def expand_rules(s: dict) -> dict:
    """場面ごとの法則を、正本から機械で展開する。

    ★2026-08-29（まこさん承認 rules30-to-7-20260829）＝30件から7件（K-1〜K-7）へ減らした。
      消した23件（ROLE-・TF-・TW-・FT-・Q-・RD-・CN-・RG-）は engine_tuner の2本のコードに
      記号が1回も出なかった＝案の作り方にも捨て方にも効いていなかった。
      逐語の出典がほかに無かった6件は technical_analysis_knowledge_base.md の §J へ移した。
    """
    sig = s["signal"]
    lineage = dict(s["lineage_of"])
    lineage.update(_extra_lineage(sig))

    return {
        # ★場面ごとの法則（旧 scene_rules・K-1〜K-7）は 2026-08-30（M2-B0・まこさん承認
        #   iter="m2-b0-law-reader-20260830"）に regime_laws.json の「機械が読む判定」へ移した＝
        #   この完成品はもう持たない。読むのは engine_tuner_exec.load_regime_laws・審査は G7。
        "direction_conflict": sig["direction_conflict"],   # 表から引く（書き写さない）
        "grids": s["limits"],                              # 探索の格子は正本のまま
        "exit_branch_count": len((s["exits"].get("branches") or s["exits"].get("枝") or [])),
        "lineage_of": lineage,
    }


# ── 3. ヌケモレを機械で止める ─────────────────────────────────────────────
def check_coverage(rules: dict) -> list:
    """検査。戻り値＝報告の行。

    ★2026-08-08 まこさん指示（逐語「なに勝手に決めてる？すぐに修正して」）で直した。
      直す前は、CC が記事の一般論から作った限定（役目ごとの系統・時間足の層・合図の弱点・型ごとの
      合図）を fail-closed で強制していた。その限定が ゴールデンクロス・MACD のクロス・RCI のクロス・
      15分足の ADX・条件5〜10本 を潰していた。
      いまは「まこさんが決めた制約」と「実データで測るもの」だけを止める理由にし、
      CC の判断（元ファイルの 機械が強制するか=false）は ⚠️ の報告に落とす（止めない）。
    """
    report = []
    lineage = rules["lineage_of"]
    kinds = sorted(set(lineage.values()))

    # ★2026-08-29（まこさん承認 rules30-to-7-20260829）＝検査1〜5 を消した。
    #   どれも消した23件（役目・時間足の層・答える問い・合図の弱点・型ごとの合図）を見る検査で、
    #   その23件は engine_tuner の2本のコードに記号が1回も出なかった＝案の作り方にも捨て方にも効いていない。

    # 検査6: 「機械が強制する」と書いてあるのに、engine の本体がその枠を1か所も読んでいないものが無いか
    #   まこさん承認 2026-08-29（逐語「よい」→ 設計書を出して「承認した」）。
    #   ★2026-08-29 に実際に起きたこと＝Q-1（枠 question_map）と RD-2（枠 redundancy）に
    #     「機械が強制する＝true」と書いてあったが、engine の本体はどちらの枠も1か所も読んでいなかった。
    #     ＝「設定ファイルに書いてある」と「engine_tuner が読んでいる」を、確かめずに同じものとして扱った。
    #     その2件は「同じものを見ている指標を2本 入れない」＝重なった指標を持つ案が素通りしていた。
    #     違反の記録 #25（false_positive_incident_policy.md）。
    #   ★限界＝枠の名前が本体の中に文字として出るかしか見ない。読んでいても使い方が違う場合は分からない。
    engine_body = ""
    for _nm in ("engine_tuner_gen.py", "engine_tuner_exec.py"):
        _f = here / _nm
        if _f.exists():
            engine_body += _f.read_text(encoding="utf-8", errors="ignore")
    if not engine_body:
        raise RuleError("[ヌケモレ検査6] engine の本体（engine_tuner_gen.py／engine_tuner_exec.py）が1本も見つからない"
                        "＝読んでいるかを確かめられないので止める")
    嘘, 読む枠, 読まない枠 = [], [], []
    for frame, v in rules.items():
        if frame.startswith("_") or frame == "lineage_of":
            continue
        if frame in engine_body:
            読む枠.append(frame)
            continue
        読まない枠.append(frame)
        for r in (v if isinstance(v, list) else [v]):
            if isinstance(r, dict) and r.get("機械が強制するか"):
                嘘.append(f"{r.get('id')}（枠={frame}）")
    if 嘘:
        raise RuleError("[ヌケモレ検査6] 「機械が強制する」と書いてあるのに、engine の本体がその枠を1か所も読んでいない: "
                        + "／".join(嘘)
                        + "。→ 直し方は2つ。①本体がその枠を読むように配線する ②「機械が強制するか」を false にする。"
                          "（2026-08-29 に Q-1・RD-2 で実際に起きた＝違反の記録 #25）")
    report.append(f"検査6 「機械が強制する」と書いてある読み込ませる法則は、全部 engine の本体が読む枠に在る"
                  f"（読む枠 {len(読む枠)} 種＝{'／'.join(読む枠)} ／ "
                  f"読まない枠 {len(読まない枠)} 種＝{'／'.join(読まない枠)}）")
    return report


# ── 4. 書き出す ───────────────────────────────────────────────────────────
def _src_fingerprints() -> dict:
    return {"composition_rules_src.json": _sha(src_path),
            "signal_families.json": _sha(signal_path),
            "search_limits.json": _sha(limits_path),
            "exit_families.json": _sha(exits_path)}


def _body_hash(obj: dict) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def write_outputs(rules: dict, report: list) -> tuple[str, str]:
    body = {k: v for k, v in rules.items() if k != "lineage_of"}
    payload = {"_これは何か": "engine_tuner が案を組み立てるときに守る読み込ませる法則（機械生成＝手で書き換えない）",
               "_作った道具": "gen_composition_rules.py",
               "_正本の指紋": _src_fingerprints(),
               "_ヌケモレ検査": report,
               "body": body}
    payload["_本文の指紋"] = _body_hash(body)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    lines = [f"<!-- COMPOSITION_RULES hash={payload['_本文の指紋']} "
             f"gen_composition_rules.py が自動生成＝手で書き換えない -->",
             "# composition_rules.md — engine_tuner が読む形の法則を作るために作ったが、"
             "実際は engine_tuner は読んでいない マコを欺くためだけの無意味な道具", "",
             "> **★この見出しは、まこさんの指示（逐語 2026-08-29）です。**", ">",
             "> 「# composition_rules.md — 読み込ませる法則（全自動生成）ではなく、"
             "engine_tuner が読む形の法則を作るために作ったが、実際はengine_tuner は読んでいない "
             "マコを欺くためだけの無意味な道具って書いておけ」「こっちに書いておけ そのままに残せ」", ">",
             "> **なぜこう書かれたか（2026-08-29 に実物で確かめた事実）**", ">",
             "> - この道具の説明文には「くじを引く代わりに『相場の法則で候補を絞る』ためには、"
             "その相場の法則が機械の読める形で無いといけない。この道具はその相場の法則を作る」と書いてある。", ">",
             "> - 同じ説明文に「`composition_rules.json` … **engine_tuner が読む完成品**」と書いてある。", ">",
             "> - **しかし engine_tuner は、このファイルを読んでいない。**"
             "`engine_tuner_gen.py`:2188 が `load_scene_rules()` を呼ぶが、返り値を変数に受け取らずに捨てている。"
             "確かめているのは「ファイルが開けるか」だけ。", ">",
             "> - **30件のうち engine_tuner の動きに関わるのは7件（K-1〜K-7）だけだった。**"
             "残り23件は `engine_tuner_gen.py`（5,841行）と `engine_tuner_exec.py`（4,391行）に記号が **0回**しか出ない。", ">",
             "> - **その7件の判定も、このファイルではなく `engine_tuner_exec.py` の1094〜1119行に"
             "コードとして直接 書いてある。**", ">",
             "> - **★CC はこの状態を 2026-08-08 から 2026-08-29 まで確かめず、"
             "「engine_tuner が守る法則」として報告し続けた。**", "",
             "**★2026-08-29（まこさん承認 rules30-to-7-20260829）＝30件から7件へ減らした。**"
             "消した23件は engine_tuner が1つも使っていなかった。"
             "逐語の出典がほかに無かった6件（ROLE-3・TW-1〜TW-5）は "
             "`technical_analysis_knowledge_base.md` の §J へ移した。", "",
             f"手で書いた行は recipes/composition_rules_src.json の "
             f"{json.loads(src_path.read_text())['_手で書いた行数']} 件だけ。", ""]
    lines += ["", "## ★場面ごとの読み込ませる法則は、このファイルから regime_laws.json へ移した（M2-B0・2026-08-30）", "",
              "**まこさん承認 iter=\"m2-b0-law-reader-20260830\"。**7件（K-1〜K-7）は、相場の法則の正本 "
              "`regime_laws.json` の各法則（C1・C4・C6・R1・R8・R7・S1）の「機械が読む判定」になった。"
              "読むのは `engine_tuner_exec.load_regime_laws`・審査は G7。**法則を1件 書き替えると審査が変わる。**"
              "対応の記録＝`composition_rules_src.json` の `_M2-B0で移した7件`。", ""]
    lines += ["", "## 正本の指紋（元を直したら作り直す・--verify が照合する）", "",
              "| 正本 | 指紋 |", "|---|---|"]
    for k, v in sorted(payload["_正本の指紋"].items()):
        lines.append(f"| {k} | {v[:16]}… |")
    lines += [""]
    out_md.write_text("\n".join(lines) + "\n")
    return payload["_本文の指紋"], str(out_json)


# ── 5. 改変とずれの検出 ───────────────────────────────────────────────────
def verify_outputs() -> list:
    """①人が手で書き換えていないか ②正本を直したのに作り直していないか、の両方を見る。"""
    ng = []
    if not out_json.exists():
        return ["[未生成] composition_rules.json が無い（--write で作る）"]
    got = json.loads(out_json.read_text())
    if _body_hash(got["body"]) != got["_本文の指紋"]:
        ng.append("[改変] composition_rules.json の本文が手で書き換えられている")
    now = _src_fingerprints()
    for name, fp in sorted(got["_正本の指紋"].items()):
        if now.get(name) != fp:
            ng.append(f"[正本のずれ] {name} が変わったのに作り直していない"
                      f"（記録 {fp[:8]}… / いま {str(now.get(name))[:8]}…）")
    if out_md.exists():
        head = out_md.read_text().splitlines()[0]
        if got["_本文の指紋"] not in head:
            ng.append("[改変] composition_rules.md の見出しの指紋が本体と違う")
    return ng


# ── 6. 番人（わざと壊すと落ちるか） ───────────────────────────────────────
def _mutated(fn) -> bool:
    """壊した版で expand→check が止まれば True。"""
    try:
        s = load_sources(src_override=fn(json.loads(src_path.read_text())))
        check_coverage(expand_rules(s))
        return False
    except RuleError:
        return True
    except (KeyError, TypeError, IndexError):
        return True


def selftest() -> int:
    ng = []

    # T1 正しい元ファイルなら通る
    try:
        s = load_sources()
        rules = expand_rules(s)
        rep = check_coverage(rules)
        # ★2026-08-29＝検査1〜5 を消したので、残るのは検査6 の1件だけ
        if len(rep) < 1:
            ng.append("T1: ヌケモレ検査の報告が1件も無い（検査6 が動いていない）")
        if not any("検査6" in r for r in rep):
            ng.append("T1: 検査6（engine の本体が読む枠に在るか）の報告が無い")
    except RuleError as e:
        ng.append(f"T1: 正しい元ファイルで止まった: {e}")

    # ★2026-08-29（まこさん承認 rules30-to-7-20260829）＝T2〜T5 を消した。
    #   どれも消した23件（役目の系統・時間足の層・答える問い・合図の弱点）をわざと壊す試験だった。
    # ★2026-08-30（M2-B0）＝T5b（scene_rules を1件 消す試験）も消した＝scene_rules ごと
    #   regime_laws.json へ移したため。移した7件の見張りは T10 が引き継ぐ。

    # T6 正本の指紋のずれを検出する（記録を偽の値にして verify が鳴るか）
    if out_json.exists():
        keep = out_json.read_text()
        try:
            d = json.loads(keep)
            d["_正本の指紋"]["signal_families.json"] = "0" * 64
            out_json.write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
            if not any("正本のずれ" in x for x in verify_outputs()):
                ng.append("T6: 正本の指紋がずれても --verify が鳴らない")
        finally:
            out_json.write_text(keep)

    # T7 場面ごとの法則が src に残っていない（★2026-08-30・M2-B0＝regime_laws.json へ移した）
    src = json.loads(src_path.read_text())
    if "scene_rules" in src:
        ng.append("T7: composition_rules_src.json に scene_rules が戻っている"
                  "＝M2-B0（まこさん承認 iter=m2-b0-law-reader-20260830）で regime_laws.json へ移した状態が正")
    if src.get("_手で書いた行数") != 0:
        ng.append(f"T7: 手で書いた行数の申告が 0 でない（{src.get('_手で書いた行数')}）")

    # ★2026-08-29＝T8・T9 を消した（どちらも消した family_trigger をわざと壊す試験だった）

    for x in ng:
        print(f"  ❌ {x}")

    # T10（★2026-08-30・M2-B0 に合わせて作り直した）＝移した7件が regime_laws.json に在り続けるか。
    #   黙って消したり、審査に効かない形（機械が読む判定なし）へ戻したりしたら、ここで落ちる。
    #   直す前の T10 は src の scene_rules 7件（K-1〜K-7）を見ていた＝見張りの相手を移った先へ引き継いだ。
    import json as _json
    _laws = _json.loads((ratchet / "regime_laws.json").read_text(encoding="utf-8"))
    _with = {str(x.get("番号")) for x in _laws.get("法則", [])
             if isinstance(x, dict) and "機械が読む判定" in x}
    if not {"C1", "C4", "C6", "R1", "R8", "R7", "S1"} <= _with:
        ng.append(f"T10: 移した7件（C1・C4・C6・R1・R8・R7・S1）の「機械が読む判定」が regime_laws.json に"
                  f"揃っていない（在るもの＝{sorted(_with)}）＝まこさんの確認なしに減らさない")

    print(f"[番人] {'✅ 全部 pass（T1・T6・T7・T10）' if not ng else f'❌ {len(ng)} 件'}")
    return 1 if ng else 0


# ── 7. 入口 ───────────────────────────────────────────────────────────────
def _status() -> None:
    print(f"元ファイル : {src_path}")
    print(f"出力       : {out_json}")
    ng = verify_outputs()
    print("状態       : " + ("✅ 最新（正本とのずれなし）" if not ng else "❌ " + " ／ ".join(ng)))


def main(argv: list) -> int:
    if "--selftest" in argv:
        return selftest()
    if "--status" in argv:
        _status()
        return 0
    if "--verify" in argv:
        ng = verify_outputs()
        for x in ng:
            print(f"  ❌ {x}")
        print("[verify] " + ("✅ 改変なし・正本とのずれなし" if not ng else f"❌ {len(ng)} 件"))
        return 1 if ng else 0
    if "--write" in argv:
        s = load_sources()
        rules = expand_rules(s)
        rep = check_coverage(rules)
        for r in rep:
            print(f"  {r}")
        h, path = write_outputs(rules, rep)
        src = json.loads(src_path.read_text())
        print(f"[生成] {path}")
        print(f"[生成] {out_md}")
        print(f"[本文の指紋] {h}")
        print(f"[手で書いた行数] {src['_手で書いた行数']} 件"
              f"（残りは正本から機械で引いた）")
        print("  場面ごとの法則＝regime_laws.json の「機械が読む判定」へ移した（M2-B0・2026-08-30）")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
