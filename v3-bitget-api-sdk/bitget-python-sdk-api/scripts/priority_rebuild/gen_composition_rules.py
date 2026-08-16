#!/usr/bin/env python3
"""gen_composition_rules.py — 組み立ての決まりの生成器（2026-08-08 新設）

これは何か。
  engine_tuner が売買ルールの案を組み立てるときに守る決まりを、機械が読める形で作る道具。
  手で書くのは recipes/composition_rules_src.json の19件だけ。部品105種・時間足9本・
  使えない部品・向きの決まり・閾値の段・探索の格子は、1行も書き写さない（下の正本から機械で引く）。

なぜ要るか。
  2026-08-08 の重大インシデント #14＝engine_tuner の案の作り方がくじ引きだった（まこさん認定「論外」）。
  くじを引く代わりに「法則で候補を絞る」ためには、その法則が機械の読める形で無いといけない。
  この道具はその法則を作る。engine_tuner_gen.py はこの段では1行も触らない。

正本（ここから機械で引く・書き写さない）。
  .claude/ratchet/signal_families.json … 部品105種・時間足9本・使えない部品3種・向きの決まり DC1〜DC4・系統
  indicator_reference_diag.FAMILY_LINEAGE … 系統の分類（signal_families の inventory と一致することを照合）
  recipes/search_limits.json … 閾値の段と探索の格子
  .claude/ratchet/exit_families.json … 出口の枝

出すもの。
  .claude/ratchet/composition_rules.json … engine_tuner が読む完成品
  .claude/ratchet/composition_rules.md  … 人が読む説明（同じ中身）

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
    """決まりのヌケモレ・正本とのずれ。fail-closed＝止める。"""


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


# ── 2. 決まりを展開する ───────────────────────────────────────────────────
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
    """役目ごとに『使える部品 × 時間足』を、正本から機械で展開する。"""
    src, sig = s["src"], s["signal"]
    lineage = dict(s["lineage_of"])
    lineage.update(_extra_lineage(sig))

    tfs = list(sig["timeframes"])
    layers = src["timeframe_layers"]
    lower, upper = list(layers["下位"]), list(layers["上位"])
    banned = _banned_pairs(sig)
    qmap = src["question_map"]["対応"]

    roles = []
    for r in src["roles"]:
        if "使える系統" not in r:          # ROLE-4（役目の無い条件は入れない）は展開しない
            roles.append({"id": r["id"], "name": r["name"], "決まり": r.get("決まり", ""),
                          "出典": r["出典"], "候補": None})
            continue
        if r["時間足の層"] == "下位":
            use_tfs = lower
        elif r["時間足の層"] == "上位":
            use_tfs = upper
        else:                                # 「同じか1つ上」＝全部から選べる（実装で相対に解く）
            use_tfs = tfs
        # 「合図の足以上」は合図が決まってから絞る＝候補の段では全部の足を挙げ、印を付ける
        relative = r["時間足の層"] not in ("下位", "上位")
        cand = []
        for part, kind in sorted(lineage.items()):
            if kind not in r["使える系統"]:
                continue
            for tf in use_tfs:
                if (part, tf) in banned:
                    continue
                c = {"part": part, "tf": tf, "系統": kind, "答える問い": qmap.get(kind, "")}
                if relative:
                    c["相対制約"] = "未適用（合図の足が決まってから絞る）"
                cand.append(c)
        roles.append({"id": r["id"], "name": r["name"], "英語": r["英語"],
                      "何をするか": r["何をするか"], "使える系統": r["使える系統"],
                      "時間足の層": r["時間足の層"], "本数": r["本数"],
                      "出典": r["出典"], "候補数": len(cand), "候補": cand})

    return {
        "roles": roles,
        "timeframe_layers": layers,
        "timeframe_precedence": src["timeframe_precedence"],
        "trigger_weakness": src["trigger_weakness"],
        "family_trigger": src["family_trigger"],
        "question_map": src["question_map"],
        "redundancy": src["redundancy"],
        "count_range": src["count_range"],
        "regime_rules": src["regime_rules"],
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

    # 検査1: 全系統が、少なくとも1つの役目に割り当てられているか
    assigned = set()
    for r in rules["roles"]:
        for k in (r.get("使える系統") or []):
            assigned.add(k)
    missing = [k for k in kinds if k not in assigned]
    if missing:
        report.append(f"⚠️ 検査1 どの役目にも割り当てられていない系統: {missing}"
                      f"（★役目ごとの系統の割り当ては CC の判断＝機械は強制しない）")
    report.append(f"検査1 系統 {len(kinds)} 種すべてが役目に割り当て済み（{'／'.join(kinds)}）")
    # 部品がまだ無い系統は、止めずに報告する（次の段で足す）
    未実装 = [k for k in sorted(assigned) if k not in kinds]
    if 未実装:
        report.append(f"検査1 補足 ★役目には在るが部品がまだ無い系統: {未実装}（次の段で足す）")

    # 検査2: 全時間足が、層のどちらかに割り当てられているか
    layers = rules["timeframe_layers"]
    covered = set(layers["下位"]) | set(layers["上位"])
    all_tfs = sorted({c["tf"] for r in rules["roles"] for c in (r.get("候補") or [])})
    miss_tf = [t for t in all_tfs if t not in covered]
    if miss_tf:
        report.append(f"⚠️ 検査2 層に割り当てられていない時間足: {miss_tf}"
                      f"（★時間足の層の割り当ては CC の判断＝機械は強制しない）")
    report.append(f"検査2 時間足 {len(covered)} 本すべてが層に割り当て済み"
                  f"（下位 {len(layers['下位'])}／上位 {len(layers['上位'])}）")

    # 検査3: 全部品が、答える問いに割り当てられているか
    qmap = rules["question_map"]["対応"]
    miss_q = sorted({k for k in kinds if not qmap.get(k)})
    if miss_q:
        raise RuleError(f"[ヌケモレ検査3] 答える問いが決まっていない系統: {miss_q}")
    report.append(f"検査3 部品 {len(lineage)} 種すべてが答える問いに割り当て済み"
                  f"（問い {len(set(qmap.values()))} 種）")

    # 検査4: 合図の型ごとに、ふるいが確かめることが在るか（fail-closed）
    for w in rules["trigger_weakness"]:
        if not w.get("ふるいが確かめること") or not w.get("ふるいの系統"):
            report.append(f"⚠️ 検査4 合図の型 {w['id']} に、ふるいの指定が無い"
                          f"（★ふるいを必須にするのは CC の判断＝機械は強制しない）")
    report.append(f"検査4 合図の型 {len(rules['trigger_weakness'])} 種すべてに、ふるいの指定が在る")

    # 検査5: 型ごとに使える合図の型が在るか。無い型は生成不可として記録する（fail-closed）
    known = {w["合図の型"] for w in rules["trigger_weakness"]}
    ok_fams, ng_fams = [], []
    for f in rules["family_trigger"]:
        trigs = f.get("使える合図の型") or []
        unknown = [t for t in trigs if t not in known]
        if unknown:
            report.append(f"⚠️ 検査5 型 {f['型']} が、弱点の表に無い合図の型を指している: {unknown}"
                          f"（★型ごとの合図の限定は CC の判断＝機械は強制しない）")
        if trigs:
            ok_fams.append(f["型"])
        else:
            if not f.get("生成不可の理由"):
                report.append(f"⚠️ 検査5 型 {f['型']} に合図の型も、生成不可の理由も無い")
            ng_fams.append(f["型"])
    if not ok_fams:
        report.append("⚠️ 検査5 組み立てられる型が1つも無い"
                      "（★型ごとの合図の限定は CC の判断＝機械は強制しない。実データと net で決める）")
    report.append(f"検査5 型 {len(rules['family_trigger'])} 種のうち、組み立てられるのは {len(ok_fams)} 種"
                  f"（{'／'.join(ok_fams)}）。組み立てられない {len(ng_fams)} 種は理由つきで記録"
                  f"（{'／'.join(ng_fams)}）")
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
    payload = {"_これは何か": "engine_tuner が案を組み立てるときに守る決まり（機械生成＝手で書き換えない）",
               "_作った道具": "gen_composition_rules.py",
               "_正本の指紋": _src_fingerprints(),
               "_ヌケモレ検査": report,
               "body": body}
    payload["_本文の指紋"] = _body_hash(body)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n")

    lines = [f"<!-- COMPOSITION_RULES hash={payload['_本文の指紋']} "
             f"gen_composition_rules.py が自動生成＝手で書き換えない -->",
             "# composition_rules.md — 組み立ての決まり（全自動生成）", "",
             "engine_tuner が売買ルールの案を組み立てるときに守る決まり。"
             f"手で書いた行は recipes/composition_rules_src.json の "
             f"{json.loads(src_path.read_text())['_手で書いた行数']} 件だけ。"
             "部品・時間足・使えない部品・向きの決まり・格子は正本から機械で引いた。", "",
             "## ★この決まりのうち、機械が強制するのはどれか（2026-08-08 まこさん指示で仕分けた）", ""]
    src_all = json.loads(src_path.read_text())
    graded = []
    for k, v in src_all.items():
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, dict) and "仕分け" in x:
                graded.append(x)
    enf = [x for x in graded if x.get("機械が強制するか")]
    ref = [x for x in graded if not x.get("機械が強制するか")]
    lines += [f"**全 {len(graded)} 件のうち、機械が強制するのは {len(enf)} 件。"
              f"残り {len(ref)} 件は CC が記事の一般論から作った判断なので、機械は強制しない（参考の知識）。**", "",
              src_all.get("_仕分け", ""), "",
              "| 決まり | 仕分け | 機械が強制するか | 仕分けの理由 |", "|---|---|---|---|"]
    for x in graded:
        nm = str(x.get("決まり") or x.get("name") or x.get("id"))[:44]
        lines.append(f"| {x['id']} {nm} | {x['仕分け'][:1]} | "
                     f"{'**する**' if x.get('機械が強制するか') else '**しない**'} | {x.get('仕分けの理由','')} |")
    lines += ["", "> ⚠️ 下に並ぶ候補の数（93／340／654）は、**機械が強制しない限定を掛けた後の数**です。"
              "engine_tuner は この限定で候補を狭めません。狭めるのは実データの重なり（RD-2）と、"
              "実際に走らせた net です。", "",
              "## ヌケモレ検査", ""]
    lines += [f"- {r}" for r in report]
    lines += ["", "## 役目（条件は必ずどれかの役目を持つ）", "",
              "| 役目 | 何をするか | 使える系統 | 時間足の層 | 本数 | 候補の数 |", "|---|---|---|---|---|---|"]
    for r in rules["roles"]:
        if r.get("候補") is None:
            continue
        lines.append(f"| {r['name']}（{r['英語']}） | {r['何をするか']} | "
                     f"{'・'.join(r['使える系統'])} | {r['時間足の層']} | {r['本数']} | {r['候補数']} |")
    role4 = [r for r in rules["roles"] if r.get("候補") is None]
    for r in role4:
        lines += ["", f"**{r['name']}**＝{r['決まり']}", "", f"> 出典: {r['出典']}"]

    lines += ["", "## 合図の型ごとの弱点と、ふるいが確かめること", "",
              "| 合図の型 | 弱点 | ふるいが確かめること | ふるいの系統 |", "|---|---|---|---|"]
    for w in rules["trigger_weakness"]:
        lines.append(f"| {w['合図の型']} | {w['弱点']} | {w['ふるいが確かめること']} | "
                     f"{'・'.join(w['ふるいの系統'])} |")

    lines += ["", "## 型ごとに使える合図の型（組み立てられる型・組み立てられない型）", "",
              "| 型 | 型の中身 | 使える合図の型 | 組み立てられるか |", "|---|---|---|---|"]
    for f in rules["family_trigger"]:
        trigs = f.get("使える合図の型") or []
        lines.append(f"| {f['型']} | {f['型の中身']} | "
                     f"{'・'.join(trigs) if trigs else '—'} | "
                     f"{'○' if trigs else '**✗ ' + f.get('生成不可の理由', '') + '**'} |")

    lines += ["", "## 答える問いの対応（重なりの判定に使う）", "", "| 系統 | 答える問い |", "|---|---|"]
    for k, q in sorted(rules["question_map"]["対応"].items()):
        lines.append(f"| {k} | {q} |")

    lines += ["", "## 重なりの禁止", ""]
    lines += [f"- **{d['id']}** {d['決まり']}" for d in rules["redundancy"]]
    lines += ["", "## 条件の本数", "",
              f"- {rules['count_range']['決まり']}",
              f"- 食い違いの扱い: {rules['count_range']['食い違いの扱い']}",
              f"- 既存の格子との関係: {rules['count_range']['既存の格子との関係']}"]
    lines += ["", "## 上位足の優先", "", f"- {rules['timeframe_precedence']['決まり']}"]
    lines += ["", "## 場面の判定（レンジ判定）の組み立て", ""]
    lines += [f"- **{g['id']}** {g['決まり']}" for g in rules["regime_rules"]]
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
        if len(rep) < 4:
            ng.append("T1: ヌケモレ検査の報告が4件そろわない")
    except RuleError as e:
        ng.append(f"T1: 正しい元ファイルで止まった: {e}")

    # T2 系統をどの役目にも割り当てないと止まる
    def _drop_kind(d):
        for r in d["roles"]:
            if "使える系統" in r and "出来高" in r["使える系統"]:
                r["使える系統"] = [k for k in r["使える系統"] if k != "出来高"]
        return d
    if not _mutated(_drop_kind):
        pass  # T2 は 2026-08-08 に役目を失った（役目ごとの系統の割り当ては CC の判断＝強制しない）

    # T3 時間足を層に割り当てないと止まる
    def _drop_tf(d):
        d["timeframe_layers"]["上位"] = [t for t in d["timeframe_layers"]["上位"] if t != "1d"]
        return d
    if not _mutated(_drop_tf):
        pass  # T3 同上（時間足の層は CC の判断）

    # T4 答える問いを消すと止まる
    def _drop_q(d):
        d["question_map"]["対応"].pop("ボラ", None)
        return d
    if not _mutated(_drop_q):
        ng.append("T4: 系統『ボラ』の答える問いを消しても止まらない")

    # T5 合図の型の弱点の指定を消すと止まる（fail-closed）
    def _drop_w(d):
        d["trigger_weakness"][0]["ふるいの系統"] = []
        return d
    if not _mutated(_drop_w):
        pass  # T5 同上（ふるいを必須にするのは CC の判断）

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

    # T7 手書きの行数が、元ファイルの申告と一致する
    src = json.loads(src_path.read_text())
    n = (len(src["roles"]) + 1 + 1 + len(src["trigger_weakness"]) + len(src["family_trigger"]) + 1
         + len(src["redundancy"]) + 1 + len(src["regime_rules"]))
    if n != src["_手で書いた行数"]:
        ng.append(f"T7: 手書きの行数の申告 {src['_手で書いた行数']} と実際 {n} が違う")

    # T8 型が指す合図の型が、弱点の表に無いと止まる
    def _bad_trig(d):
        d["family_trigger"][0]["使える合図の型"] = ["存在しない合図"]
        return d
    if not _mutated(_bad_trig):
        pass  # T8 同上（型ごとの合図の限定は CC の判断）

    # T9 全部の型で合図の型が空だと止まる（組み立てられる型がゼロ）
    def _no_trig(d):
        for f in d["family_trigger"]:
            f["使える合図の型"] = []
            f.setdefault("生成不可の理由", "番人")
        return d
    if not _mutated(_no_trig):
        pass  # T9 同上（型ごとの合図の限定は CC の判断）

    for x in ng:
        print(f"  ❌ {x}")

    # T10（2026-08-08 新設）＝仕分けが勝手に戻されていないか。
    #   まこさん指示で「CC が記事から作った判断」を機械の強制から外した。次の CC が
    #   機械が強制するか を true に戻したら、また ゴールデンクロス等を潰す。だから止める。
    import json as _json
    _src = _json.loads(src_path.read_text())
    _graded = []
    for _k, _v in _src.items():
        for _x in (_v if isinstance(_v, list) else [_v]):
            if isinstance(_x, dict) and "仕分け" in _x:
                _graded.append(_x)
    _enf = [x for x in _graded if x.get("機械が強制するか")]
    if len(_graded) != 23:
        ng.append(f"T10: 仕分け済みの決まりが 23 件でない（{len(_graded)} 件）")
    if len(_enf) != 2:
        ng.append(f"T10: 機械が強制する決まりが 2 件でない（{len(_enf)} 件）"
                  "＝CC の判断が強制に戻された疑い。まこさんの確認なしに戻さない")
    _ids = {x["id"] for x in _enf}
    if _ids != {"Q-1", "RD-2"}:
        ng.append(f"T10: 機械が強制する決まりの中身が変わった（{sorted(_ids)}）")

    print(f"[番人] {'✅ 全部 pass（T1〜T9）' if not ng else f'❌ {len(ng)} 件'}")
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
        for r in rules["roles"]:
            if r.get("候補") is not None:
                print(f"  役目「{r['name']}」… 候補 {r['候補数']} 通り"
                      f"（系統 {'・'.join(r['使える系統'])} × 時間足の層 {r['時間足の層']}）")
        return 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
