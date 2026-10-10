#!/usr/bin/env python3
"""gen_indicator_switch.py — 指標のオン・オフの印（使う・使わない）の自動生成（M2-C-2・2026-09-02）

設計書＝.claude/state/acceptance.md（iter="indicator-switch-20260902"・まこさん承認 2026-09-02）。

まこさんの決定（逐語）:
  2026-08-27「本来の目的が達成できるまでは、指標一覧はta 43種にする」＋「レンジ判定で必要な指標は入れろ」
  2026-09-01「一律でtaの指標のみを使うという切り替えをする」

★すべて自動生成（CC の手書きの一覧はゼロ）:
  印は3つの源から機械で作る＝
    源1 ta の43種   … 定義表 indicator_reference_diag の ta 照合式（ext）と ta_class の欄から引く
    源2 法則の名指し … .claude/ratchet/regime_laws.json の「機械が読む判定」の family と geo
    源3 恒等レシピ   … recipes/identity_*.json 3本が実際に使う材料
  機械で対応が決まらない ta のクラスは「使わない」に倒し、一覧に出す（fail-closed）。

★印でできるのは減らすことだけ:
  使える指標は「承認済みの型の表 ∩ 印がオン」の積で決まる。印をオンにしても、型の表に無い指標は使えない。

このスクリプトがやらないこと: 売買しない・値を選ばない・採点しない・型の表を書き換えない。

使い方:
  python3 gen_indicator_switch.py --ta-candidates  … ta のクラスと材料の対応の候補を出す（まこさんが1回 見る）
  python3 gen_indicator_switch.py --write          … 印のファイルを作る
  python3 gen_indicator_switch.py --verify         … 印のファイルが手で書き換えられていないかを見る
  python3 gen_indicator_switch.py --selftest       … わざと壊して止まるかを試す
"""
from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(HERE))

import indicator_reference_diag as iref                      # noqa: E402  材料の定義表（正本）
import engine_tuner_exec as ex                               # noqa: E402  材料の種類の分岐と判定関数の正本

LAWS_JSON = SDK / ".claude/ratchet/regime_laws.json"          # 相場の法則の正本
IDENTITY = ["recipes/identity_s1_legacy.json",
            "recipes/identity_s2_legacy.json",
            "recipes/identity_l1_legacy.json"]                # 恒等レシピ3本
OUT_JSON = SDK / ".claude/ratchet/indicator_switch.json"      # 印（機械可読・engine_tuner が読む）

# ★GENERATES＝この道具が作る文書の名乗り（gen_docmap.py が集める・2026-08-16 の決まり）
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/indicator_switch.json", "まるごと"),
]

_TA_MODULES = ("ta.volume", "ta.volatility", "ta.trend", "ta.momentum", "ta.others")
_TA_CALL = re.compile(r"_ta\.(\w+)\.(\w+)")
# クラス名から落とす接尾辞（ta の命名の型。CC が指標を選んでいるのではなく、語尾を落としているだけ）
_SUFFIX = re.compile(r"(Indicator|Index|Channel|Oscillator|Bands|Average|Return)$")


# ══ 源の材料を集める ════════════════════════════════════════════════════
def ta_classes() -> list[tuple[str, str]]:
    """ta ライブラリの指標クラス（IndicatorMixin を継ぐもの）を機械で数える。手書きの一覧を持たない。"""
    import ta
    out = []
    for m in _TA_MODULES:
        mod = importlib.import_module(m)
        for n, o in vars(mod).items():
            if (inspect.isclass(o) and issubclass(o, ta.utils.IndicatorMixin)
                    and o is not ta.utils.IndicatorMixin and o.__module__ == m):
                out.append((m.split(".")[-1], n))
    return sorted(out)


def families() -> list[str]:
    """材料の種類（family）の異なり。定義表 indicator_reference_diag が正本。並びも定義表の順。"""
    seen: list[str] = []
    for e in iref.REFS:
        if e["family"] not in seen:
            seen.append(e["family"])
    return seen


def ta_map_from_ext() -> dict[str, set[str]]:
    """ta 照合式（ext）のソースから「ta のクラス → 材料の種類」を機械で取る（確定分）。"""
    out: dict[str, set[str]] = {}
    for e in iref.REFS:
        if e["ext"] is None:
            continue
        try:
            src = inspect.getsource(e["ext"])
        except (OSError, TypeError):
            continue
        for _mod, cls in _TA_CALL.findall(src):
            out.setdefault(cls, set()).add(e["family"])
    return out


def _abbrev(cls: str) -> list[str]:
    """ta のクラス名から、照合に使う略号を機械で作る（CC が指標ごとに決めない）。

    2通りだけ＝①接尾辞を落とした語（AroonIndicator → AROON）②大文字の頭文字
    （PercentagePriceOscillator → PPO）。当たらなければ「対応が決まらない」に倒す。
    """
    base = _SUFFIX.sub("", cls)
    head = "".join(c for c in cls if c.isupper())
    return [base.upper(), head.upper()]


def ta_map_by_abbrev(exclude: set[str]) -> dict[str, set[str]]:
    """略号の一致で「ta のクラス → 材料の種類」の候補を作る。exclude＝確定済みのクラス。

    ★これは候補であって、印には入れない（まこさんが1回 見て決めたものだけが ta_class の欄に入る）。
    """
    fams = families()
    out: dict[str, set[str]] = {}
    for _grp, cls in ta_classes():
        if cls in exclude:
            continue
        hit = set()
        for ab in _abbrev(cls):
            if len(ab) < 3:                       # 2文字以下は当たりすぎる（ER・AR など）＝使わない
                continue
            for f in fams:
                fu = f.upper()
                if fu == ab or fu.startswith(ab) or fu.startswith("CLOSE VS " + ab):
                    hit.add(f)
        if hit:
            out[cls] = hit
    return out


def ta_map_approved() -> dict[str, set[str]]:
    """定義表に書き込まれた承認済みの対応（indicator_reference_diag.TA_CLASS_MAP）を読む。

    ★まこさんが1回だけ見て承認した対応が、ここに入る（設計書 §9.1 の案A・承認 2026-09-02）。
    ★1か所の辞書で持つ理由＝材料38件それぞれの登録行に書き足すと、手の作業が38回になって
      打ち間違いが混じる。1か所なら、下の --selftest が名前の実在を毎回 確かめられる。
    """
    m = getattr(iref, "TA_CLASS_MAP", {}) or {}
    return {cls: set(fams) for cls, fams in m.items()}


def source_ta() -> tuple[set[str], list[str]]:
    """源1＝ta の43種に対応する材料の種類。戻り＝(種類の集合, 対応が決まらない ta のクラス)。"""
    m = ta_map_from_ext()
    for cls, fs in ta_map_approved().items():
        m.setdefault(cls, set()).update(fs)
    fams: set[str] = set()
    for fs in m.values():
        fams |= fs
    unresolved = [c for _g, c in ta_classes() if c not in m]
    return fams, unresolved


def law_named() -> tuple[set[str], set[str], set[str]]:
    """相場の法則が「機械が読む判定」で名指ししている中身を、そのまま取り出す。

    戻り＝(family の集合, 系統の集合, 性質の集合)。★ここでは材料に展開しない（生のまま返す）。
    ★下の source_law と、--selftest の照合が、別々にこれを使う＝同じ展開を2回 書かない。
    """
    d = json.loads(LAWS_JSON.read_text(encoding="utf-8"))
    fams: set[str] = set()
    lins: set[str] = set()
    props: set[str] = set()
    for law in d.get("法則", []):
        cnt = (law.get("機械が読む判定") or {}).get("数える部品") or {}
        for f in (cnt.get("family") or []):
            fams.add(f)
        for k in (cnt.get("系統") or []):
            lins.add(k)
        p = cnt.get("性質")
        if p:
            props.add(str(p))
    return fams, lins, props


def law_geo() -> set[str]:
    """相場の法則が名指しするレンジ幾何の列（例＝W%）。"""
    d = json.loads(LAWS_JSON.read_text(encoding="utf-8"))
    out: set[str] = set()
    for law in d.get("法則", []):
        cnt = (law.get("機械が読む判定") or {}).get("数える部品") or {}
        g = cnt.get("geo")
        if isinstance(g, list):
            out.update(g)
    return out


def source_law() -> tuple[set[str], set[str]]:
    """源2＝相場の法則が名指しする指標。戻り＝(種類の集合, レンジ幾何の集合)。

    ★設計書 §3.3 の逐語＝「regime_laws.json の「機械が読む判定」から、family・系統・性質・geo の
      4通りを展開」。**4通り全部を展開する。**

    ★2026-09-02 の直し（まこさん指摘「設計通りに実装したのか」）＝
      直す前は family と geo の2通りしか展開しておらず、系統（構造・位置）と性質（vol）を落としていた。
      その結果、レンジ判定の核心部品（fractal・S-Rタッチ数・pivot・POC/VAH/VAL・n本高安・swing・W字）が
      全部「使わない」に倒れ、既存の自己テストが落ちた。**設計書は最初から4通りと書いてあった。**
    """
    fams, lins, props = law_named()
    out = set(fams)
    if lins:                                   # ③系統での名指し（R1・R3＝構造・位置）
        out |= {f for f in families()
                if iref.FAMILY_LINEAGE.get(f, {}).get("k") in lins}
    if props:                                  # ④性質での名指し（R10＝vol）
        out |= {e["family"] for e in iref.REFS if e["prop"] in props}
    return out, law_geo()


def source_identity() -> tuple[set[str], set[str]]:
    """源3＝恒等レシピ3本が実際に使う材料。戻り＝(種類の集合, レンジ幾何の集合)。

    ★この源が無いと、ta にも法則にも入らない材料（実測＝volume_ratio）が「使わない」になり、
      恒等レシピ S2 が壊れる。だから飾りではない（設計書 §1 の実測）。

    ★2026-09-06（監査 cp24 の §6-6・Major・設計書 D-1）＝`legacy_col` を持つ材料の
      `family` ラベルを拾わないようにした。
      直す前＝`walk` が全部の `family` を拾っていたので、`BB`（identity_s1_legacy.json）と
        `レンジ幾何`（identity_l1_legacy.json）という **定義表に無い名前**が源3 に混じっていた
        （監査の実測＝源3 は 8件と出るが、定義表に在るのは 6件）。
      なぜ混じるか＝その2件は `{"legacy_col": "e37_v47_bb2", "family": "BB", …}` の形で、
        **`family` は説明のラベル**（実際に指しているのは昔からの列）。
      なぜ拾ってはいけないか＝オン・オフの対象は「昔からの列を含めない」と決めた
        （監査 §6-5・設計書 C）。対象外にしたものを材料として数えているのが食い違い。
      ★いま実害は出ていない（審査は `tf` を持つ材料にしかオン・オフを当てないため）。
        将来、昔からの列をカタログの列に置き換えたときに、黙ってオフ側に落ちる。
    """
    fams: set[str] = set()
    geos: set[str] = set()

    def walk(o):
        if isinstance(o, dict):
            f = o.get("family")
            if isinstance(f, str) and "legacy_col" not in o:
                fams.add(f)
            g = o.get("geo")
            if isinstance(g, str):
                geos.add(g)
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for rel in IDENTITY:
        walk(json.loads((HERE / rel).read_text(encoding="utf-8")))
    return fams, geos


def source_mako() -> tuple[set[str], set[str]]:
    """源4＝まこさんが個別に「使う」と決めたもの。戻り＝(種類の集合, 需給の列の集合)。

    ★2026-09-05（M2-C-4・まこさんの決定「案A にします」）に足した。
      まこさんの逐語（2026-09-05）＝「1・2・4・5・6 を足す／3 は外す／**需給は「使う」にする**」
      ＋「§6 の8番に3つ目の源「まこさんが個別に決めたもの」を足してください。
         そこに 需給3種と MMI の両方が入ります。…**手書きの一覧は作らないこと**」。

    ★だから中身は2つとも機械で引く（CC の手書きの一覧はゼロ）:
      ①需給3種＝`indicator_reference_diag.DEMAND_REF` の鍵（定義・流儀・出典が既に在る正本）
      ②材料の定義表 `REFS` のうち `mako` の欄が書かれているもの（いまは MMI の1件）

    ★なぜ需給を種類の集合に入れないか＝需給は元データが5分足の1本しかなく、時間足11本に
      展開できない。だからレンジ幾何（geo）や時間帯（time）と同じ「別枠」で持つ
      （型の表の extra_parts）。印でも別の欄（demand_on）に置く。
    """
    fams = {e["family"] for e in iref.REFS if e.get("mako")}
    return fams, set(iref.DEMAND_REF)


def source_time() -> set[str]:
    """時間帯の列（別枠）＝`indicator_reference_diag.TIME_REF` の鍵。

    ★2026-09-06（監査 cp24 の §6-1・Critical・設計書 A-3）に足した。
      直す前＝印に time_on の欄そのものが無く、時間帯だけオン・オフの外に在った。
      ＝生成器が m = {"time": "時刻"} を無条件で作れた（監査の実測＝has("time_on") が false）。
    ★中身＝時刻 と 曜日 の両方（まこさん決定 2026-09-06・逐語「3は時刻と曜日を入れる」）。
    ★手書きの一覧は作らない（まこさんの指示 2026-09-05「手書きの一覧は作らないこと」）＝
      定義表 TIME_REF の鍵をそのまま使う。型の表 signal_families.json の
      extra_parts.time.parts と同じ2件（一致は gen_indicator_switch.py --selftest が見る）。
    """
    return set(iref.TIME_REF)


# ══ 印を組み立てる ═════════════════════════════════════════════════════
def source_mako_geo() -> set[str]:
    """源4 のレンジ幾何＝`indicator_reference_diag.RANGE_GEO_REF` のうち、mako の欄（まこさんの決定の逐語）が書かれた列。

    ★2026-10-09（工事 m2c15-shape-structure-20261009・まこさん「よい」の3＝ok_k3b_design_20261009）に足した。
      直す前の geo_on は法則（law_geo）と恒等レシピ（source_identity）の2つだけから作り、まこさんが個別に決めた列を入れる道が無かった
      （mako の欄は材料の定義表 REFS にしか効かない＝source_mako）。下半分位置（監査 CP60 の修正65）を「使う」にするため。
    ★手書きの一覧は作らない＝定義表の欄を機械で読む。"""
    return {g for g, r in iref.RANGE_GEO_REF.items() if r.get("mako")}


def build() -> dict:
    """3つの源から印を組み立てる。CC の手書きの一覧はゼロ。"""
    ta_f, unresolved = source_ta()
    law_f, law_g = source_law()
    id_f, id_g = source_identity()
    mako_f, mako_demand = source_mako()          # 源4（2026-09-05・案A）
    mako_g = source_mako_geo()                   # 源4 のレンジ幾何（2026-10-09・K-3b）
    time_on = source_time()                      # 別枠の時間帯（2026-09-06・監査 cp24 の §6-1）
    all_f = families()
    want = ta_f | law_f | id_f | mako_f
    on = [f for f in all_f if f in want]           # 定義表に在る種類だけ（並びも定義表に合わせる）
    off = [f for f in all_f if f not in want]
    d = {
        "_これは何か": "engine_tuner が読む指標の種類ごとの「使う・使わない」の印（M2-C-2）。",
        "_作り方": "gen_indicator_switch.py が3つの源から機械で作る。手で書き換えない（--verify が検出する）。",
        "_源": {
            "1_ta": "定義表の ta 照合式（ext）と ta_class の欄から引いた種類",
            "2_法則": "regime_laws.json の「機械が読む判定」の family と geo",
            "3_恒等レシピ": "recipes/identity_*.json 3本が実際に使う材料",
            "4_まこさんが個別に決めたもの":
                "①需給3種＝indicator_reference_diag.DEMAND_REF の鍵"
                "（まこさんの逐語 2026-09-05「需給は「使う」にする」）"
                "②材料の定義表 REFS の mako の欄が書かれているもの（いまは MMI）。"
                "③レンジ幾何の定義表 RANGE_GEO_REF の mako の欄が書かれている列（2026-10-09・K-3b）。"
                "★どちらも機械で引く＝CC の手書きの一覧はゼロ（まこさんの指示「手書きの一覧は作らないこと」）",
        },
        "_できること": "減らすことだけ。型の表に無い指標は、印をオンにしても使えない。",
        "built_by": "gen_indicator_switch.py（全自動生成・CC の手書きの行ゼロ）",
        "counts": {
            "定義表の種類": len(all_f),
            "使う": len(on),
            "使わない": len(off),
            "源1_ta": len(ta_f),
            "源2_法則": len(law_f),
            # ★2026-09-06（監査 cp24 の §6-6・設計書 D-2）＝「拾ったラベルの数」でなく
            #   「定義表に実在して、実際にオンに入った数」を出す。
            #   直す前＝len(id_f) だったので、定義表に無い名前（BB・レンジ幾何）も1件として数えていた。
            "源3_恒等レシピ": len(id_f & set(all_f)),
            "源4_まこさんが個別に決めたもの": len(mako_f) + len(mako_demand) + len(mako_g),
            "対応が決まらない_taのクラス": len(unresolved),
        },
        "on": on,
        "off": off,
        # ★2026-10-09（工事 m2c15-shape-structure-20261009・まこさん「よい」の3）＝まこさんが個別に決めたレンジ幾何の列（RANGE_GEO_REF の mako の欄）も使う
        "geo_on": sorted(law_g | id_g | mako_g),
        "demand_on": sorted(mako_demand),        # 需給の列（別枠・2026-09-05・案A）
        # ★2026-09-06（監査 cp24 の §6-1・Critical）＝時間帯の列（別枠）。
        #   これが無いと「一律で切り替えられる」を満たさない（時間帯だけ印の外に在った）。
        "time_on": sorted(time_on),
        "sources": {"ta": sorted(ta_f), "law": sorted(law_f), "identity": sorted(id_f),
                    "mako": sorted(mako_f | mako_demand | mako_g)},
        "ta_unresolved": sorted(unresolved),
    }
    d["fingerprint"] = _fp(d)
    return d


def _fp(d: dict) -> str:
    """印の指紋＝中身（fingerprint 以外）の sha256 の先頭16文字。"""
    x = {k: v for k, v in d.items() if k != "fingerprint"}
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


# ══ 出し入れ ═══════════════════════════════════════════════════════════
def cmd_write() -> int:
    d = build()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(d, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    c = d["counts"]
    print(f"✅ --write 完了: {OUT_JSON.name}（使う {c['使う']} 種／使わない {c['使わない']} 種"
          f"／指紋 {d['fingerprint']}）")
    print(f"   源の内訳＝ta {c['源1_ta']} 種／法則 {c['源2_法則']} 種／恒等レシピ {c['源3_恒等レシピ']} 種"
          f"（重なりを含む・和集合が「使う」）")
    if d["ta_unresolved"]:
        print(f"   ⚠️ 対応が決まらない ta のクラス {len(d['ta_unresolved'])} 件（使わないに倒した）")
        print("   → --ta-candidates で候補を出し、まこさんが1回 見て決める（設計書 §9.1 の案A）")
    return 0


def cmd_verify() -> int:
    if not OUT_JSON.exists():
        print(f"❌ --verify: {OUT_JSON.name} が無い（--write で作る）")
        return 1
    now = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    want = build()
    if now.get("fingerprint") != _fp(now):
        print("❌ --verify: 印のファイルが手で書き換えられている（中身と指紋が合わない）")
        return 1
    if now.get("fingerprint") != want["fingerprint"]:
        print(f"❌ --verify: 源が変わっている（いま {now.get('fingerprint')} ／ 作り直すと {want['fingerprint']}）")
        print("   → --write で作り直す")
        return 1
    print(f"✅ --verify: 印は機械が書いたままです（指紋 {now['fingerprint']}"
          f"／使う {now['counts']['使う']} 種）")
    return 0


def cmd_ta_candidates() -> int:
    """ta のクラスと材料の種類の対応の候補を出す（まこさんが1回 見て決める・設計書 §9.1 の案A）。"""
    fixed = ta_map_from_ext()
    for cls, fs in ta_map_approved().items():
        fixed.setdefault(cls, set()).update(fs)
    cand = ta_map_by_abbrev(set(fixed))
    allc = ta_classes()
    print(f"ta のクラス {len(allc)} 件")
    print(f"  ① 照合式・承認済みで確定 … {len(fixed)} 件")
    print(f"  ② 略号の一致で候補が出た  … {len(cand)} 件（★まこさんが見て決める）")
    print(f"  ③ 候補が出なかった        … {len(allc) - len(fixed) - len(cand)} 件")
    print()
    print("② 候補（略号の一致・機械が出したもの）")
    for cls in sorted(cand):
        print(f"   {cls:<32} -> {sorted(cand[cls])}")
    print()
    print("③ 候補が出なかった ta のクラス（このままなら「使わない」に倒す）")
    for _g, cls in allc:
        if cls not in fixed and cls not in cand:
            print(f"   {cls}")
    return 0


# ══ わざと壊して止まるか試すテスト ═══════════════════════════════════════
def cmd_selftest() -> int:
    ng: list[str] = []
    d = build()
    all_f = families()

    id_f, _ = source_identity()
    if [f for f in id_f if f in d["off"]]:
        ng.append("T1")                            # 恒等レシピの材料が「使わない」に入った
    law_f, _ = source_law()
    if [f for f in law_f if f in d["off"]]:
        ng.append("T2")                            # 法則が名指しする指標が「使わない」に入った
    if len(d["on"]) + len(d["off"]) != len(all_f):
        ng.append("T3")                            # 取りこぼしが在る
    if set(d["on"]) & set(d["off"]):
        ng.append("T4")                            # 同じ種類が両方に在る
    d2 = json.loads(json.dumps(d, ensure_ascii=False))
    d2["on"] = d2["on"][:-1]
    if _fp(d2) == d["fingerprint"]:
        ng.append("T5")                            # 中身を変えても指紋が変わらない
    if build()["fingerprint"] != d["fingerprint"]:
        ng.append("T6")                            # 2回 作ると違う（決定論でない）
    if not set(d["on"]) <= set(all_f):
        ng.append("T7")                            # 定義表に無い種類が「使う」に入った

    # T8 承認済みの対応に書いた材料の名前が、定義表に実在するか（打ち間違いをここで止める）
    bad8 = sorted({f for fs in ta_map_approved().values() for f in fs if f not in all_f})
    if bad8:
        ng.append("T8")
        print(f"      T8 の中身＝定義表に無い材料の名前: {bad8}")

    # T9 承認済みの対応の ta のクラス名が、ta ライブラリに実在するか
    known = {c for _g, c in ta_classes()}
    bad9 = sorted(c for c in ta_map_approved() if c not in known)
    if bad9:
        ng.append("T9")
        print(f"      T9 の中身＝ta に無いクラス名: {bad9}")

    # T10 源3（恒等レシピ）が拾った材料の名前が、定義表に実在するか（監査 cp24 の §6-6・設計書 D-3）
    #   なぜ要るか＝T8 は「承認済みの対応」にしか掛かっておらず、源3 は素通りだった。
    #   その結果、定義表に無い名前（BB・レンジ幾何）が源3 に混じっても誰も気づかなかった。
    bad10 = sorted(id_f - set(all_f))
    if bad10:
        ng.append("T10")
        print(f"      T10 の中身＝定義表に無い材料の名前（源3）: {bad10}")

    # T11 オン・オフの対象にする材料の種類が、実装の分岐と1件ずつ合うか（監査 cp24 の §6-5・設計書 C）
    #   ★一覧を手書きで決め打ちしない＝実行器の _material_name が分岐する鍵を機械で拾い、
    #     対象（印で切り替える）＋対象外（切り替えない）が、その分岐の全部と一致するかを見る。
    #     分岐が1つ増えたら合わなくなって落ちる＝新しい種類を黙って足せない。
    #   ★対象・対象外の決め方の出どころ＝監査 cp24 の §6-5（相場を測る材料か／自分の玉の話か／
    #     恒等の走行が使うか）。
    #   ★2026-09-06 の実測＝分岐は 6つ（family・geo・demand・time・legacy_col・state）。
    #     監査 §6-5 は tf・param も対象外に挙げていたが、**その2つは種別の分岐ではない**
    #     （指標に付く時間足と数字＝family の材料の中身）。だからこの検査の相手にしない。
    _ON_KINDS = {"family", "geo", "demand", "time"}      # 印で切り替える（一律＝M2-C の見出し）
    _OFF_KINDS = {"legacy_col", "state"}                 # 切り替えない（理由＝監査 §6-5）
    _src = inspect.getsource(ex._material_name)          # noqa: SLF001  実物の分岐を機械で拾う
    _kinds = set(re.findall(r'"(\w+)" in m\b', _src))
    if _kinds != (_ON_KINDS | _OFF_KINDS):
        ng.append("T11")
        print(f"      T11 の中身＝実装の分岐 {sorted(_kinds)} と "
              f"対象+対象外 {sorted(_ON_KINDS | _OFF_KINDS)} が食い違う")
    if _ON_KINDS & _OFF_KINDS:
        ng.append("T11")
        print("      T11 の中身＝対象と対象外に同じ種類が在る")
    # ★対象の4つには、実行器に判定関数が在ること（無ければ「切り替えられる」と言えない）
    _missing = [k for k, fn in (("family", "indicator_enabled"), ("geo", "geo_enabled"),
                                ("demand", "demand_enabled"), ("time", "time_enabled"))
                if not hasattr(ex, fn)]
    if _missing:
        ng.append("T11")
        print(f"      T11 の中身＝対象なのに判定関数が無い種類: {_missing}")

    # T12 まこさんが個別に決めたレンジ幾何の列（RANGE_GEO_REF の mako の欄）は、必ず geo_on に入る
    #   （2026-10-09・工事 m2c15-shape-structure-20261009・まこさん「よい」の3）
    bad12 = sorted(g for g in source_mako_geo() if g not in d["geo_on"])
    if bad12:
        ng.append("T12")
        print(f"      T12 の中身＝mako の欄が在るのに geo_on に無い列: {bad12}")

    names = {"T1": "恒等レシピの材料は必ず使う", "T2": "法則の名指しは必ず使う",
             "T3": "取りこぼしゼロ", "T4": "重なりゼロ", "T5": "指紋は中身から決まる",
             "T6": "2回 作って同じ", "T7": "定義表に無い種類は増やせない",
             "T8": "承認済みの対応の材料名が実在する", "T9": "承認済みの対応の ta クラス名が実在する",
             "T10": "源3 が拾った材料名が定義表に実在する",
             "T11": "オン・オフの対象4つ（family・geo・demand・time）＋対象外2つ"
                    "（legacy_col・state）が、実装の分岐6つと一致する",
             "T12": "まこさんが個別に決めたレンジ幾何の列は必ず使う"}
    for t, nm in names.items():
        print(f"   {t} {nm} → {'ng' if t in ng else 'pass'}")
    if ng:
        print(f"\n❌ selftest {len(names) - len(ng)}/{len(names)} pass（落ちた＝{', '.join(ng)}）")
        return 1
    print(f"\n✅ selftest {len(names)}/{len(names)} pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--ta-candidates", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.write:
        return cmd_write()
    if a.verify:
        return cmd_verify()
    if a.ta_candidates:
        return cmd_ta_candidates()
    if a.selftest:
        return cmd_selftest()
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
