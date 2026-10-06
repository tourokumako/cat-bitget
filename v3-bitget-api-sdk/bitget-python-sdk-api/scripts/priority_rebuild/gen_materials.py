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

import ast
import hashlib
import json
import pathlib
import re
import sys

_HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import indicator_reference_diag as iref   # noqa: E402

_RATCHET = _HERE.parent.parent / ".claude" / "ratchet"
# ★GENERATES＝この道具が作る文書の名乗り（2026-08-16 新設・まこさん決定 A）。
#   なぜ要るか＝名前で数えると必ず漏れる（出力先の変数名が道具ごとにバラバラで、
#   読むファイルと作るファイルが同じ形で並んでいる＝外から見分けられない）。
#   だから道具の側に名乗らせる。集める道具＝gen_docmap.py。
#   形＝(リポジトリの根からのパス, "まるごと" か "一部の節")。
GENERATES = [
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.md", "まるごと"),
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.json", "まるごと"),
    # ★「作ってはいけないものとの照合」の表（2026-08-26・64回目）＝印の間だけを書き換える。
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones.md", "一部の節"),
    ("v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/engine_tuner_milestones2.md", "一部の節"),
]

_MD = _RATCHET / "materials.md"
_JSON = _RATCHET / "materials.json"
_SIGFAM = _RATCHET / "signal_families.json"

_GROUP_TBD = "（段8 で埋める）"
_TBD = "（未定・材料に足すときに決める＝段6）"
_EEM = _RATCHET / "entry_exit_matrix.md"

# ── 段5（足すものの一覧）で使う「選べるか」の言い方（1か所に置く＝表記ゆれ防止）──
_SEL_OK = "選べる"
_SEL_NO_TPL = "選べない（名前の組み立てが未登録＝G6 で拒否）"
_SEL_NO_COL = "選べない（材料カタログに列が無い）"
_SEL_NO_H6 = "使えない（価格そのもの＝placement の幾何参照専用・H6）"
_SEL_NA = "—（まだ材料に入っていない）"


def _quiet(fn, *a, **kw):
    """observe_diag は import と実行で画面に出すので、ここでは黙らせて戻り値だけ使う。"""
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **kw)


def _engine_view() -> dict:
    """engine_tuner がいま「条件の材料として選べる」ものを、実物から機械で数える（段5・2026-08-09 新設）。

    ★なぜ要るか。materials.md の『在る』は『参照表に登録済み』という意味しか無かった。
      ところが engine_tuner の生成器が条件に選べるのは、そのうちの一部だけ。
      まこさんが『在る 65』を読んで『65 使える』と受け取ると、実物と食い違う。
    ★どこから引くか（書き写さない）。
      engine_tuner_exec.FAMILY_TEMPLATES … 生成器が名前を組み立てられる指標の種類（G6 の線）
      engine_tuner_gen.material_pool     … (指標, 期間) の候補と時間足＝いま探せる範囲そのもの
      observe_diag.build_catalog          … 材料カタログの部品（生成器の入口①）
      signal_families.json extra_parts    … レンジ幾何・時間帯（生成器の入口②③）
    """
    import json as _j

    def _load():
        import engine_tuner_exec as ex
        import engine_tuner_gen as g
        import observe_diag as od
        cfg = od.load_config()
        pool, tfs, cat_total = g.material_pool(cfg)
        names = [nm for nm, _f, _d in od.build_catalog(cfg)]
        return dict(tpl=dict(ex.FAMILY_TEMPLATES), pool=pool, tfs=list(tfs),
                    cat_total=int(cat_total), names=names,
                    demand=list(od._DEMAND_FILES), tf_list=list(cfg["timeframes"]))
    v = _quiet(_load)
    extra = (_j.loads(_SIGFAM.read_text(encoding="utf-8")).get("extra_parts") or {})
    v["geo_ok"] = list((extra.get("geo") or {}).get("parts") or [])
    v["time_ok"] = list((extra.get("time") or {}).get("parts") or [])
    # ★2026-09-05（M2-C-4）＝需給の別枠。型の表から機械で引く（手書きの一覧を作らない）
    v["demand_ok"] = list((extra.get("demand") or {}).get("parts") or [])
    fams = list(dict.fromkeys(e["family"] for e in iref.REFS))
    v["selectable_fams"] = sorted({p["family"] for p in v["pool"]})
    v["unselectable_fams"] = [f for f in fams if f not in set(v["selectable_fams"])]
    v["cols_selectable"] = len(v["pool"]) * len(v["tfs"])
    # 期間がいま「点」で固定されている実測（マイルストーン③の対象・段5 は事実を出すだけ）
    # ★2026-08-11（段6 の 6-7）＝数字の持ち方が3つになった（1つ／並び／無し）ので、
    #   int() に丸めず、そのままの形で集める。数字を持たない指標（包み足 ほか）はこの表に出さない。
    per: dict[str, list] = {}
    for p in v["pool"]:
        if p["param"] is None:
            continue
        per.setdefault(p["family"], []).append(p["param"])
    v["params"] = {k: sorted(set(x)) for k, x in sorted(per.items())}
    return v


# ★段6（材料を足す作業）の前の材料の一覧＝git のこの commit の materials.md（2026-08-09・段5 の分）。
#   ここを起点に「うちが元から持っていた指標が1件も消えていないか」を毎回 照らす（6-9②）。
_STAGE6_BASE_COMMIT = "03aad50"


def _kept_since_stage6(commit: str = _STAGE6_BASE_COMMIT) -> tuple[list[str], int]:
    """段6 の前に「在る」だった指標が、いまも材料に在るかを照らす。戻り＝(消えた名前, 元の件数)。

    ★一覧は git から取り出す（記憶や書き写しではない）。git が使えない環境では空を返す
      （＝この検査は黙って通る。番人の出力に「照らせなかった」と出す作りにはしていない＝
      次に触る人が気づけるよう、ここに書いておく）。
    """
    import subprocess
    rel = "v3-bitget-api-sdk/bitget-python-sdk-api/.claude/ratchet/materials.md"
    try:
        old = subprocess.run(["git", "show", f"{commit}:{rel}"], capture_output=True, text=True,
                             cwd=str(_HERE.parents[3]), timeout=60)
        if old.returncode != 0:
            return [], 0
    except Exception:                                            # noqa: BLE001
        return [], 0
    base = [ln.split("|")[1].strip() for ln in old.stdout.splitlines()
            if ln.startswith("|") and "| 在る |" in ln]
    rows = build_body()["rows"]
    now = {r["名前"] for r in rows if r["状態"] == "在る"}
    # ★「同じ挙動なので省いた」と設定に理由つきで書いてあるものは、消えたとみなさない
    #   （まこさん OK 2026-08-11・逐語「同じ挙動ならどちらかは使わないようにしていいよ」）。
    #   ＝黙って消えた場合だけ ❌ にする。設定 observe_config.json の drop_columns が根拠。
    dropped_fams = set()
    for d, _k in _dropped_columns():
        ent = iref.find(d)[0]
        if ent is not None:
            dropped_fams.add(ent["family"])
    lost = [b for b in base if b not in now and b not in dropped_fams]
    return lost, len(base)


def _dropped_columns() -> list[tuple[str, str]]:
    """同じ挙動なので省いた列の一覧（左＝省いた列・右＝残した列）。出どころ＝observe_config.json。"""
    import json as _j
    p = _HERE / "observe_config.json"
    try:
        return [(a, b) for a, b in (_j.loads(p.read_text(encoding="utf-8")).get("drop_columns") or [])]
    except Exception:                                            # noqa: BLE001
        return []


def _row_engine(row: dict, ev: dict) -> str:
    """1行が engine_tuner から選べるかを返す（上の _engine_view の実測だけで決める）。"""
    if row["状態"] != "在る":
        return _SEL_NA
    nm = row["名前"]
    if nm.startswith("レンジ幾何 "):
        part = nm.split(" ", 1)[1]
        if part in ev["geo_ok"]:
            return _SEL_OK + "（レンジ幾何）"
        return _SEL_NO_H6
    if nm in ev["time_ok"]:
        # 型の表は許すが、生成器が実際に作るかは別（曜日は閾値の格子が未定義＝engine_tuner_gen.py:256）
        return (_SEL_OK + "（時間帯）") if nm == "時刻" else \
            "選べない（型の表は許すが、閾値の格子が未定義＝engine_tuner_gen.py:256）"
    if nm in ev["demand"]:
        # ★2026-09-05（M2-C-4・まこさん承認 iter="m2c4-add-parts-20260905"）＝需給は
        #   型の表の別枠（extra_parts.demand）に入った＝engine_tuner が条件の材料に選べる。
        #   直す前は「需給なら一律に選べない」と書く作りで、別枠に入った後もそのままだった
        #   ＝文書が実物と食い違う（違反の記録25番と同じ型）。
        #   ★判定は型の表そのものから引く＝CC の手書きの一覧は作らない。
        return (_SEL_OK + "（需給・別枠）") if nm in ev.get("demand_ok", []) else _SEL_NO_COL
    return _SEL_OK if nm in set(ev["selectable_fams"]) else _SEL_NO_TPL


def _demand_missing(ev: dict) -> list[str]:
    """需給のうち、材料カタログにも 型の表の別枠にも無いもの（＝本当に「これから足す」もの）。

    ★2026-09-06（監査 cp24 の §6-10 の4件目・設計書 H）に新設。
      直す前＝参照表に在る需給3件を、そのまま「これから足す候補」に数えていた。
      いま＝型の表の `extra_parts.demand.parts` に在るものは、もう足し終わっている（別枠で使える）。
      ★手で 0 と書かない＝表から機械で引いて差を数える（表から外れれば、また候補に戻る）。
    """
    extra = (json.loads(_SIGFAM.read_text(encoding="utf-8")).get("extra_parts") or {})
    have = set((extra.get("demand") or {}).get("parts") or [])
    return [d for d in ev["demand"] if d not in have]


def _gaps(ev: dict, body_counts: dict, add_n: int, skip: list) -> list[dict]:
    """段5＝足すものの一覧。4か所に散っている不足を1つにまとめる（数は全部 実物から）。"""
    # 検査9（向きの穴）
    def _dg():
        import observe_diag as od
        return od._direction_gap(ev["names"])
    _dist, _slope, gap = _quiet(_dg)
    # 検査7（軸カタログ E-c の未実装）
    ec = [ln for ln in _EEM.read_text(encoding="utf-8").splitlines()
          if ln.lstrip().startswith("- **E-c")]
    ax_un: list[str] = []
    if len(ec) == 1:
        _ng, rows = iref.axis_ec_check(ec[0], ev["names"] + ev["demand"])
        ax_un = [f"{r['cat']}＝{r['token']}" for r in rows if r["status"] != "あり"]
    return [
        dict(印="A", 何を足すか="業界のライブラリに在って、うちの材料に無い指標",
             数=add_n, 単位="種類", 出どころ="検査10（observe_diag）",
             中身="下の『材料の一覧』で状態が「足す」の行"),
        dict(印="B", 何を足すか="★うちの材料カタログに在るのに、engine_tuner が条件に選べない指標",
             数=len(ev["unselectable_fams"]), 単位="種類", 出どころ="段5 で新しく数えた（検査には無い）",
             中身="・".join(ev["unselectable_fams"])),
        # ★2026-09-06（監査 cp24 の §6-10 の4件目・設計書 H）＝「別枠で使えるようになったもの」を除く。
        #   直す前＝参照表に在る需給3件を、そのまま「これから足す候補」に数えていた。
        #     ＝2026-09-05 に3件とも足し終わった（まこさん決定「需給は『使う』にする」・型の表の
        #     extra_parts.demand に3件）のに、いつまでも「足りない3件」と出ていた。
        #     ＝M2-C-6 の確かめ方（★1 の該当行が0件）を満たせない状態だった。
        #   ★手で 0 と書かない＝型の表の別枠（extra_parts）から機械で引いて、差を数える。
        #     型の表から需給が外れれば、また候補に戻る（数字を焼かない）。
        dict(印="C", 何を足すか="★参照表に在るのに、材料カタログにも別枠にも無い（需給）",
             数=len(_demand_missing(ev)), 単位="件",
             出どころ="段5 で新しく数えた（検査7 は『あり』と出る＝別の道で見ている）"
                      "／2026-09-06 に「型の表の別枠に在るものは除く」を足した",
             中身="・".join(_demand_missing(ev)) or "（無し＝3件とも型の表の別枠に在る）"),
        dict(印="D", 何を足すか="「終値と◯◯の距離%」に対する「◯◯ そのものの向き」",
             数=len(gap), 単位="件", 出どころ="検査9（observe_diag）", 中身="・".join(gap)),
        dict(印="E", 何を足すか="軸カタログ（入口 E-c）の未実装",
             数=len(ax_un), 単位="件", 出どころ="検査7（observe_diag）", 中身="・".join(ax_un) or "（無し）"),
        dict(印="F", 何を足すか="時間足（1分足・3分足）",
             数=2, 単位="本", 出どころ="要件 R15（フロー 段7 で足す）",
             中身=f"いま {len(ev['tf_list'])} 本＝" + "・".join(ev["tf_list"])),
        dict(印="G", 何を足すか="★型の表は許すが、閾値の格子が無くて選べない部品",
             数=sum(1 for t in ev["time_ok"] if t != "時刻"), 単位="件",
             出どころ="段5 で新しく数えた（engine_tuner_gen.py:256 の逐語）",
             中身="・".join(t for t in ev["time_ok"] if t != "時刻") or "（無し）"),
    ]


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


# ══ 段A の A-1｜「決まった数字だけ」の場所を機械で数える（2026-08-12 新設）═══════════════════
#
# 何を数えるか。
#   engine_tuner が試せる数字が、あらかじめ並べてある一覧に限られている場所。
#   ＝要件の「作ってはいけないもの」2番（原文＝探す値を、CC が先に「点の一覧」で限定するもの）に
#     当たっている場所を、実物のファイルを開いて機械で数える。
#
# なぜ機械で数えるか。
#   CC が手で一覧を書くと、書き忘れたものは誰にも見えない（インシデント #15 と同じ型）。
#   数字は1つも手で書かない＝下の4つの関数が毎回 実物から数え直す。
#
# 数え方（1か所に書く＝表記ゆれ防止）。
#   「数の並び」＝要素が全部 数字の並び（例＝[7, 9, 14, 21]）を 1 と数える。
#   説明のための鍵（`_` で始まるもの）は数えない＝機械が読む場所に説明が混ざっているため。
#   検収専用の値は数えない＝`engine_tuner_gen.py` の `selftest` と `KENSHU_LIMITS`。
#     出どころ＝`recipes/search_limits.json` の `_note` の逐語
#     「検収専用の値は engine_tuner_gen.py の selftest の中にだけ存在する」。
#
# 番人＝T12（4か所のどれかに架空の数の並びを1つ 足すと、その場所の件数がちょうど1 増える）。

_A1_CFG = _HERE / "observe_config.json"
_A1_LIM = _HERE / "recipes" / "search_limits.json"
_A1_GEN = _HERE / "engine_tuner_gen.py"
_A1_E38 = _HERE / "e38_logics.json"


# ══ 「作ってはいけないものとの照合」を実物から数える（2026-08-26・64回目・承認 b034352a6940f601…）══
#
# なぜ要るか。
#   要件定義書に「作ってはいけないもの」の表が在り、作業に入る前に CC が1件ずつ照合して
#   「当たる／当たらない」を書く決まり（恒久の決まり §1）。その答えの欄を CC が文章で書いていた。
#   2026-08-23 に、その欄が嘘だったことが分かった（next_step.md §6 の78番・まこさん認定＝重大な不正）。
#   当たっているのに「当たりません」と書いてあった。
#
# まこさんの指示（逐語 2026-08-23）。
#   「作ってはいけないものとの照合」を、手書きの表から、実物を数えて自動で作る表に変える。
#   （消すもの）CC が「当たりません」と書ける欄が消える。
#
# 何をするか。
#   ① 一覧そのものを要件の json から読む（CC が写さない）
#   ② 実物を数える（乱数の呼び出し／法則の表を読む所／決まった数字だけの一覧／範囲を通さずに作る所）
#   ③ 数字から答えを決める（返す文字列は下の4つだけ・プログラムに固定）
#   ④ 2つの文書へ印つきで差し込む（手で書き換えると --verify が落ちる）
#
# ★止めない。見えるようにするだけ（設計書 §3.3）。
_FB_REQ_JSON = _RATCHET / "engine_tuner_requirements.json"
_FB_START = ("<!-- FORBIDDEN_CHECK_START hash={h} "
             "ここは gen_materials.py が自動生成＝手で書き換えない -->")
_FB_START_RE = re.compile(r"<!-- FORBIDDEN_CHECK_START hash=[0-9a-f]* [^>]*-->")
_FB_END = "<!-- FORBIDDEN_CHECK_END -->"
_FB_TARGETS = [
    (_RATCHET / "engine_tuner_milestones.md", "マイルストーン①のフローと やることリスト"),
    (_RATCHET / "engine_tuner_milestones2.md", "マイルストーン②（場面の判定）"),
]

# ══ B-4｜やることリストの確かめ方を、要件の逐語と並べて出す（2026-08-26・承認 a3be50c30e7ea827）══
#
# まこさんの指示（逐語 2026-08-23）＝「やることリストの『確かめ方』欄を、要件の逐語から降ろす形にする
#   （CC が自由に書かない）」／消えるもの＝「CC が合格の条件を書く欄が消える」。
#
# 何をするか
#   ① やることリスト2本から、表の行（# ／ やること ／ 触るファイル ／ 出るもの・確かめ方 ／ 状態）を機械で拾う
#   ② 対応表 milestone_req_map.json から「その行がどの要件に効くか」を引く（★どの要件かを選ぶのは作る側の判断）
#   ③ 要件の正本 engine_tuner_requirements.json から accept の全文を引く（★何をもって満たしたと言うかは要件の側）
#   ④ 4列の表にして、2つの文書へ印つきで差し込む
#
# ★CC が文を書く欄は、対応表の basis だけ。差し込む4列は全部 実物からの複写。
# ★止める条件（--verify が落ちる）＝行が対応表に無い／要件の番号が正本に無い／basis が空／
#   差し込んだ逐語が正本と1文字でも違う。
_RA_REQ_JSON = _RATCHET / "engine_tuner_requirements.json"
_REQ_MAP = _RATCHET / "milestone_req_map.json"
_RA_START = ("<!-- REQ_ACCEPT_START hash={h} "
             "ここは gen_materials.py が自動生成＝手で書き換えない -->")
_RA_START_RE = re.compile(r"<!-- REQ_ACCEPT_START hash=[0-9a-f]* [^>]*-->")
_RA_END = "<!-- REQ_ACCEPT_END -->"
_RA_HEAD = ["#", "やること", "触るファイル", "出るもの・確かめ方", "状態"]

# ══ B-5｜「満たした」の根拠を、走らせた出力に限る（2026-08-26・承認 03f797a70c978b3e）══
#
# まこさんが貼った5番の逐語（session_worklog_20260823.md の §29）＝
#   「✅済 の根拠を、走らせた出力に限る（手で打った数字を弾く）／CC が数字を打ち込む欄が消える」。
#
# 何が問題だったか（実測 2026-08-26・worklog §62）
#   要件の state（完了／作業中）も progress（いまどこまで）も CC の手書き。
#   実例＝R3 の progress「完了の線9項目のうち7項目を満たす」。この 7 を書いたのは CC で、走らせた出力ではない。
#   ★CC の「完了」と、機械が見える数字がずれている要件が 2件（R8・R10）。
#   ★✅済 63件のうち、走らせた記録の指し先（§NN）が無い行が 30件。
#
# 何をするか
#   ① progress の「達成度の数字」を弾く（--verify が落ちる）。★日付は止めない。
#   ② 要件17件について「効く行 N件／うち ✅済 M件／state とのずれ」を機械で出す。
#   ③ ✅済 なのに走らせた記録の指し先が無い行を、件数つきで出す（★止めない・見せるだけ）。
#
# ★入っていないもの＝「要件を本当に満たしたか」の判定は入れない。
#   やることリストが全部 ✅済 でも、要件を満たしたとは限らない（要件は別の作業でも満たせる）。判定は まこさん。
_ACH_NUM = re.compile(r"\d+\s*項目|\d+\s*つとも|\d+\s*つのうち|\d+\s*件とも")
_EVIDENCE = re.compile(r"§\s*\d+|worklog")

# ★答えの文字列＝この4つだけ（設計書 §3.2・番人 F5 が「4つ以外が出ない」を確かめる）。
_FB_MISS = "当たりません"
_FB_HIT = "当たっています"
_FB_SUSPECT = "当たっている疑いあり"
_FB_TBD = "測り方が未定"
_FB_VERDICTS = (_FB_MISS, _FB_HIT, _FB_SUSPECT, _FB_TBD)

# 乱数を「引く操作」の名前＝呼び出しの最後の名前がこれなら1件と数える。
#   ★2段の書き方（rng.choice）だけでなく、3段の書き方（np.random.default_rng）も拾う。
#   57回目の設計書は2段だけを見ていて、実物の29件を丸ごと落としていた（worklog 20260826 §28.1）。
_FB_DRAW_METHODS = frozenset({
    "choice", "integers", "random", "uniform", "permutation", "normal", "shuffle",
    "standard_normal", "exponential", "beta", "poisson", "binomial", "randint",
    "randrange", "sample", "gauss", "default_rng", "Random", "seed", "spawn", "bit_generator",
})

# 法則の表（承認済みの型の表・場面の決まり・パラメータの範囲の表）を読む関数。
#   ★乱数だけで組んでいるなら、この表を1つも読まないはず＝1番の白黒の材料。
_FB_LAW_FUNCS = frozenset({
    "load_signal_table", "load_regime_laws", "material_ranges", "ranked_groups",
    "role_lineage", "forms_where", "regime_draw_order",
})   # ★2026-08-30（M2-B-2b・next_step §6 の126番）＝消した load_scene_rules を外し、新しい正本 load_regime_laws を足した


def _is_num(x) -> bool:
    """真偽値は数字に数えない（True/False は「本当に選択肢」であって点の一覧ではない）。"""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _num_lists(obj, key: str = "") -> list[tuple[str, list]]:
    """入れ子をたどって「数の並び」を全部 拾う。戻り＝(その並びが載っている鍵, 並び)。"""
    out: list[tuple[str, list]] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).startswith("_"):
                continue
            out += _num_lists(v, str(k))
    elif isinstance(obj, list):
        if obj and all(_is_num(x) for x in obj):
            out.append((key, obj))
        else:
            for v in obj:
                out += _num_lists(v, key)
    return out


def _fmt_nums(v: list) -> str:
    return "・".join(str(x) for x in v)


_A1_OD = _HERE / "observe_diag.py"


def _catalog_keys(od_src: str | None = None) -> set[str]:
    """`observe_diag.build_catalog` が読む設定の鍵を、コードから機械で拾う。

    ★なぜ鍵の名前（`*_periods`）で決めないか。実物には `*_periods` でない指標のパラメータが在る
      （`bb_sigma`・`keltner`・`supertrend`・`ichimoku`・`macd_params`・`*_windows`・`sr_tol`・`w_tol`）。
      名前で数えると、それを丸ごと取りこぼす＝A-1 が「全部 数える」にならない。
      だから「材料カタログを作る関数が実際に読んでいる鍵か」で決める。
    """
    import ast
    src = _A1_OD.read_text(encoding="utf-8") if od_src is None else od_src
    fn = next((n for n in ast.walk(ast.parse(src))
               if isinstance(n, ast.FunctionDef) and n.name == "build_catalog"), None)
    keys: set[str] = set()
    if fn is None:
        return keys
    for n in ast.walk(fn):
        if isinstance(n, ast.Subscript) and isinstance(n.value, ast.Name) and n.value.id == "cfg" \
                and isinstance(n.slice, ast.Constant) and isinstance(n.slice.value, str):
            keys.add(n.slice.value)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "get" \
                and isinstance(n.func.value, ast.Name) and n.func.value.id == "cfg" \
                and n.args and isinstance(n.args[0], ast.Constant) \
                and isinstance(n.args[0].value, str):
            keys.add(n.args[0].value)
    return keys


def _a1_place1(cfg: dict, cat_keys: set[str]) -> dict:
    """場所1＝`observe_config.json` の、指標のパラメータ（材料カタログを作る関数が読む鍵）。

    ★観察の道具（observe_diag）だけが使う格子（`sl_grid`・`wait_grid` ほか）は別に数える。
      engine_tuner が条件の材料として振る値ではないため。
    """
    lists = _num_lists(cfg)
    ind = sorted((k, v) for k, v in lists if k in cat_keys)
    obs = sorted({k for k, _v in lists if k not in cat_keys})
    return dict(並び=len(ind), 数字=sum(len(v) for _k, v in ind), 範囲=0,
                観察だけの格子=obs,
                明細=[dict(鍵=k, 中身=_fmt_nums(v)) for k, v in ind])


def _a1_place2(lim: dict) -> dict:
    """場所2＝`recipes/search_limits.json`（使い方の中の本数・閾値の段・上限）。"""
    lists = _num_lists(lim)
    # 範囲＝下限と上限の組で持っているもの。
    # ★2026-08-13（段A の A-5）に、鍵の名前を決め打ちにするのをやめた。
    #   直す前は `hold_range_by_role` だけを見ていたので、範囲を新しく足しても この欄が増えなかった。
    #   いまは中身の形（下限と上限の組を持つか）で見る＝範囲が増えれば機械が自分で数える。
    def _is_range(v) -> bool:
        return isinstance(v, dict) and any(
            {lo, hi} <= set(v) for lo, hi in (("lo", "hi"), ("lo_bars", "hi_bars")))

    rng_rows = []
    for k, v in lim.items():
        if str(k).startswith("_"):
            continue
        if _is_range(v):
            rng_rows.append(k)
        elif isinstance(v, dict):                      # 入れ子（役割ごとの保有時間の上限）
            rng_rows += [f"{k}.{k2}" for k2, v2 in v.items() if _is_range(v2)]
    # 分位の段＝文字の並び（"q10" …）＝数ではないが、段の数は決まっている
    # ★2026-08-15（段A の A-5-3）＝`quantile_range` が在れば、分位は「決まった段だけ」ではなく
    #   範囲になった。`quantile_grid` はほかの道具がまだ読むので残してある（int_grid と同じ扱い）
    #   ＝残っているからといって「9段だけ」と書かない（実物は範囲）。
    qg = lim.get("quantile_grid")
    qr = lim.get("quantile_range")
    q_rng = None
    if isinstance(qr, dict) and qr.get("lo") is not None and qr.get("hi") is not None:
        q_lo, q_hi = int(qr["lo"]), int(qr["hi"])
        q_rng = f"q{q_lo}〜q{q_hi}（{q_hi - q_lo + 1} 通り）"
    q_n = 0 if q_rng else (len(qg) if isinstance(qg, list) else 0)
    single = sorted(k for k, v in lim.items() if not str(k).startswith("_") and _is_num(v))
    nocap = sorted(k for k, v in lim.items()
                   if not str(k).startswith("_") and isinstance(v, str) and v == "無制限")
    return dict(並び=len(lists), 数字=sum(len(v) for _k, v in lists), 範囲=len(rng_rows),
                分位の段=q_n, 分位の範囲=q_rng, 単独の数字=single, 無制限=nocap,
                明細=[dict(鍵=k, 中身=_fmt_nums(v)) for k, v in sorted(lists)],
                範囲の明細=sorted(rng_rows))


def _a1_place3(src: str) -> dict:
    """場所3＝`engine_tuner_gen.py` が数字を選んでいる行（コードに直に書いた数字）。"""
    import ast
    tree = ast.parse(src)
    skip: set[int] = set()                       # 検収専用＝本走・採否に使わないので数えない
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and "selftest" in n.name:
            skip.update(range(n.lineno, (n.end_lineno or n.lineno) + 1))
        if isinstance(n, ast.Assign) and any(
                getattr(t, "id", "") == "KENSHU_LIMITS" for t in n.targets):
            skip.update(range(n.lineno, (n.end_lineno or n.lineno) + 1))
    menu: list[tuple[int, str, int]] = []
    prob: list[tuple[int, str]] = []
    for n in ast.walk(tree):
        ln = getattr(n, "lineno", None)
        if ln is None or ln in skip:
            continue
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in ("choice", "choices", "integers", "uniform"):
            cnt = 0
            for a in ast.walk(n):
                if isinstance(a, (ast.List, ast.Tuple)) and a.elts and all(
                        isinstance(e, ast.Constant) and _is_num(e.value) for e in a.elts):
                    cnt += len(a.elts)
            if cnt:
                menu.append((ln, ast.unparse(n), cnt))
        if isinstance(n, ast.Compare) and any(
                isinstance(c, ast.Constant) and _is_num(c.value) for c in n.comparators):
            s = ast.unparse(n)
            if "random()" in s:
                prob.append((ln, s))
    menu.sort()
    prob.sort()
    return dict(並び=len(menu), 数字=sum(c for _l, _s, c in menu), 範囲=0, 確率=len(prob),
                明細=[dict(行=str(ln), 中身=s) for ln, s, _c in menu],
                確率の明細=[dict(行=str(ln), 中身=s) for ln, s in prob])


def _a1_place4(e38: dict) -> dict:
    """場所4＝`e38_logics.json` の `search_space`（E38 の探索が振る値）。"""
    specs: list[tuple[str, dict]] = []

    def flat(o, path: str = "") -> None:
        """鍵は「どのロジックの、どの値か」で持つ（S5 と L5 の grid_n を区別するため）。"""
        if not isinstance(o, dict):
            return
        for k, v in o.items():
            if str(k).startswith("_") or not isinstance(v, dict):
                continue
            if "type" in v:
                specs.append((f"{path}{k}", v))
            else:
                flat(v, f"{path}{k}.")

    def find(o) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "search_space" and isinstance(v, dict):
                    flat(v)
                else:
                    find(v)
        elif isinstance(o, list):
            for v in o:
                find(v)
    find(e38)
    q = [k for k, v in specs if v.get("type") == "quantile"]
    cat_num = [(k, v.get("choices") or []) for k, v in specs
               if v.get("type") == "cat" and (v.get("choices") or [])
               and all(_is_num(x) for x in v["choices"])]
    cat_oth = [k for k, v in specs if v.get("type") == "cat"
               and not (v.get("choices") and all(_is_num(x) for x in v["choices"]))]
    rng_rows = [k for k, v in specs if v.get("type") in ("float", "int")]
    empty = [k for k, v in specs if v.get("type") in ("float", "int")
             and (v.get("lo") is None or v.get("hi") is None)]
    return dict(並び=len(cat_num), 数字=sum(len(c) for _k, c in cat_num), 範囲=len(rng_rows),
                分位=len(q), 選択肢=len(cat_oth), 合計=len(specs), 値が空=sorted(empty),
                明細=[dict(鍵=k, 中身=_fmt_nums(c)) for k, c in sorted(cat_num)])


def _param_kinds(params: dict) -> dict:
    """パラメータを「本数（整数）」と「倍数・許容幅・係数（小数）」に分ける。

    ★なぜ要るか。2026-08-11 まで ★3 の説明文は「ここで言う数字は、ローソク足の本数です」と
      書いていたが、実物には本数でないものが混ざっていた（BB の 2.0＝標準偏差の倍数、
      Supertrend の 3.0＝ATR の倍数、S-Rタッチ数の 0.003＝値段の許容幅、LRSI の 0.5＝減衰の係数）。
      本数だけだと思って直すと、A-3 で「整数の範囲」しか作らず、小数を扱えなくなる。
      ＝分ける判定も機械でやる（CC が一覧を手で書かない）。
    """
    def flat(v):
        for x in v:
            if isinstance(x, (list, tuple)):
                yield from x
            else:
                yield x
    ints, dec = [], []
    for k, v in params.items():
        xs = [float(x) for x in flat(v)]
        (dec if any(x != int(x) for x in xs) else ints).append(k)
    return dict(本数=sorted(ints), 小数=sorted(dec))


def fixed_number_places(cfg: dict | None = None, lim: dict | None = None,
                        gen_src: str | None = None, e38: dict | None = None,
                        od_src: str | None = None) -> dict:
    """段A の A-1＝「決まった数字だけ」の4か所を、実物から機械で数える。

    引数は番人（T12）が架空の数の並びを混ぜるためだけに在る。既定は全部 実物から読む。
    """
    cfg = json.loads(_A1_CFG.read_text(encoding="utf-8")) if cfg is None else cfg
    lim = json.loads(_A1_LIM.read_text(encoding="utf-8")) if lim is None else lim
    gen_src = _A1_GEN.read_text(encoding="utf-8") if gen_src is None else gen_src
    e38 = json.loads(_A1_E38.read_text(encoding="utf-8")) if e38 is None else e38
    p1 = _a1_place1(cfg, _catalog_keys(od_src))
    p2, p3, p4 = _a1_place2(lim), _a1_place3(gen_src), _a1_place4(e38)
    places = [
        dict(番号="1", 場所="scripts/priority_rebuild/observe_config.json",
             何の数字か="指標を作るときのパラメータ（RSI14 の 14）", **p1),
        dict(番号="2", 場所="scripts/priority_rebuild/recipes/search_limits.json",
             何の数字か="使い方の中の本数（slope の n）・閾値の段・上限", **p2),
        dict(番号="3", 場所="scripts/priority_rebuild/engine_tuner_gen.py",
             何の数字か="生成器が数字を選ぶときに、コードに直に書いた数字", **p3),
        dict(番号="4", 場所="scripts/priority_rebuild/e38_logics.json の search_space",
             何の数字か="E38 の探索が振る値", **p4),
    ]
    return dict(places=places,
                合計並び=sum(x["並び"] for x in places),
                合計数字=sum(x["数字"] for x in places),
                合計範囲=sum(x["範囲"] for x in places))


def _probe_points(spec: dict) -> list[tuple]:
    """範囲の中から確かめる値を作る＝下限・上限・まん中（軸が2つ以上ならその組）。

    ★新しい数字を作っているのではありません。範囲そのものの端と中を取っているだけです。
    """
    per_axis = []
    for ax in spec["axes"]:
        lo, hi = float(ax["lo"]), float(ax["hi"])
        vals = [lo, hi, (lo + hi) / 2]
        if ax["kind"] == "int":
            vals = [int(round(v)) for v in vals]
        else:
            vals = [round(v, int(ax["dec"]) or 1) for v in vals]
        per_axis.append(sorted(set(vals)))
    n = max(len(v) for v in per_axis)
    return [tuple(v[min(i, len(v) - 1)] for v in per_axis) for i in range(n)]


def param_range_both_ways(break_family: str | None = None) -> tuple[int, list[str]]:
    """段A の A-6｜パラメータの範囲を「両方向」で確かめる（2026-08-16 新設・まこさん指示）。

    まこさんの指示（逐語 2026-08-16）＝
      「『範囲の中の数字が全部 計算できるか』を両方向で確かめる形にします」。

    ★なぜ要るか（この番人が生まれた事故）。
      2026-08-13（段A の A-4）に、engine_tuner が指標のパラメータを「点の一覧」でなく
      「範囲」から引く形にした。そのとき確かめたのは **片方向だけ** だった。
        方向1（外）＝範囲の外の数字は止まるか … 確かめた
        方向2（中）＝範囲の中の数字は本当に計算できるか … **確かめていなかった**
      その結果、MMAR が「範囲は 10〜35 なのに、実際に作れるのは 10・15・20・25・30・35 の
      6個だけ」の状態で3日間 残った。engine_tuner が 21 を引くと列が作れず、
      **走行が丸ごと止まった**（2026-08-16 実測＝案100本のうち33本目で停止）。

    ★この番人が見るもの（両方向）。
      方向1（外）＝範囲の外の値・整数でない値を、検証器 param_in_range が止めること。
      方向2（中）＝数字を持つ指標 **全種類** について、範囲の中の値（下限・上限・まん中）で
        ①列の名前を組み立てられる ②材料の表がその名前を分解できる
        ③組み立て直すと同じ名前に戻る ④実際に計算が通る、の4つが全部 成り立つこと。

    break_family＝メタ確認用。その指標だけ「範囲の中なのに作れない」状態を作って、
      この番人がちゃんと落ちるかを確かめるために使う（本走では None）。
    """
    import numpy as _np
    import pandas as _pd
    ng: list[str] = []
    import engine_tuner_exec as exe
    import engine_tuner_gen as gen
    import observe_diag as od
    ranges = _quiet(gen.material_ranges)
    idx = _pd.date_range("2024-01-01", periods=1500, freq="5min")
    rng = _np.random.default_rng(20260816)
    close = _pd.Series(30000 + _np.cumsum(rng.normal(0, 20, 1500)), index=idx)
    bars = _pd.DataFrame({"open": close.shift(1).fillna(close.iloc[0]), "high": close + 15,
                          "low": close - 15, "close": close,
                          "volume": _pd.Series(rng.uniform(1, 9, 1500), index=idx)}, index=idx)
    keep = None
    if break_family is not None:                     # メタ確認＝MMAR と同じ壊れ方を1つ作る
        keep = od.MATERIAL_FAMILIES[break_family]
        tpl, direc, fn = keep
        allowed = {p for pp in _probe_points(ranges[break_family])[:1] for p in pp}

        def _broken(d, *p, _fn=fn, _ok=allowed):
            if p and p[0] not in _ok:
                raise KeyError(f"わざと壊した（{p[0]} は作れない）")
            return _fn(d, *p)
        od.MATERIAL_FAMILIES[break_family] = (tpl, direc, _broken)
        od._MAT_RE.clear()
    tried = 0
    try:
        for fam, spec in sorted(ranges.items()):
            if not spec["axes"]:
                continue
            # ── 方向1（外）＝範囲の外・整数でない値は止まる ──
            out_lo = [float(a["lo"]) - 1 for a in spec["axes"]]
            ok_out, _why = gen.param_in_range(fam, out_lo[0] if len(out_lo) == 1 else tuple(out_lo), ranges)
            if ok_out:
                ng.append(f"方向1: {fam} の範囲の外の値 {out_lo} を検証器が通した")
            # ── 方向2（中）＝範囲の中の値は、実際に列を作れる ──
            for prm in _probe_points(spec):
                tried += 1
                p = prm[0] if len(prm) == 1 else prm
                ok_in, why = gen.param_in_range(fam, p, ranges)
                if not ok_in:
                    ng.append(f"方向2: {fam} の範囲の中の値 {p} を検証器が拒否した（{why}）")
                    continue
                try:
                    name = exe.build_name({"family": fam, "param": p})
                except BaseException as e:           # noqa: BLE001
                    ng.append(f"方向2: {fam} {p} の列名を組み立てられない（{type(e).__name__}）")
                    continue
                fam2, prm2 = od.find_material(name)
                if fam2 is None:
                    ng.append(f"方向2: {name} を材料の表が分解できない（範囲の中の値なのに作れない）")
                    continue
                try:
                    name2, fn2, _dd = od.make_material(fam2, *prm2)
                except BaseException as e:           # noqa: BLE001
                    ng.append(f"方向2: {name} を組み立て直せない（{type(e).__name__}: {str(e)[:60]}）")
                    continue
                if name2 != name:
                    ng.append(f"方向2: 名前が往復しない（{name} → {name2}）")
                    continue
                try:
                    _quiet(fn2, bars)
                except BaseException as e:           # noqa: BLE001
                    ng.append(f"方向2: {name} が計算できない（{type(e).__name__}: {str(e)[:60]}）"
                              f"＝範囲の中の値なのに engine_tuner が引くと走行が止まる")
    finally:
        if keep is not None:
            od.MATERIAL_FAMILIES[break_family] = keep
            od._MAT_RE.clear()
    return tried, ng


def forms_table() -> list[dict]:
    """★使い方（条件の形）の一覧を、実物から機械で引く（まこさん指示 2026-08-11「すべて自動生成にして」）。

    引く先は2つ。どちらも実物で、この道具は1行も手で書かない。
      ①形の名前と数 … engine_tuner_exec.FORMS（実行器が本当に実行できる形＝これが正）
      ②何をするか・必要な値 … engine_tuner_step2_condition_format.md §2.2 の表（人が読む説明）
    ★①に在って②に無い形が1つでもあれば ❌ にする（実物と説明のずれを黙らせない）。
    ★なぜ材料の正本に入れるか＝「材料（指標）に列が無い＝作れない」と CC が誤判定した事案
      （2026-08-11・RSI の差）の対策。指標の一覧と使い方の一覧が別の場所に在ると突き合わせられない。
    """
    import engine_tuner_exec as ex
    doc = _RATCHET / "engine_tuner_step2_condition_format.md"
    rows, ng = [], []
    text = doc.read_text(encoding="utf-8") if doc.exists() else ""
    desc = {}
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 4:
            continue
        key = cells[0].split()[0]                      # 「level 水準」→「level」
        if key in ex.FORMS:
            desc[key] = dict(和名=cells[0], 材料=cells[1], 必要な値=cells[2], 実例=cells[3])
    # ★入れ子の欄の意味＝streak・within_n は「外側になる形」（内側に条件を1つ包む）。
    #   それ以外は「内側に置ける」（設計書 §2.2 の逐語「単純形＝入れ子形以外の全部」）。
    for f in ex.FORMS:
        nest = "外側になる形（中に条件を1つ包む）" if f in ex.NEST_FORMS else "内側に置ける"
        d = desc.get(f)
        if d is None:
            ng.append(f)
            rows.append(dict(形=f, 和名="？", 材料="？", 必要な値="？", 実例="？", 入れ子=nest))
            continue
        # 「level 水準」→「水準」（形の名前は左の欄に在るので、説明だけにする）
        wa = d["和名"].split(" ", 1)[1] if " " in d["和名"] else d["和名"]
        rows.append(dict(形=f, 和名=wa, 材料=d["材料"], 必要な値=d["必要な値"],
                         実例=d["実例"], 入れ子=nest))
    # ── ★M2-2-3b（2026-08-21 まこさん承認 e4b86277…）＝説明の表と、形の性質表を突き合わせる ──
    #   なぜ要るか＝この節は直す前、**形の名前しか照らしていなかった**（①に在って②に無い形）。
    #     説明の欄（材料・必要な値）と、プログラムが実際に使う性質表（FORM_SPEC）がずれても
    #     気づけなかった。M2-2-3b で性質表を作ったので、そこと1件ずつ照らす。
    #   ★照らすのは「材料の本数」と「帯の値を持つか」の2つ＝説明の欄から機械で読み取れるもの。
    #     ほかの欄（向き・本数）は説明の書き方が1つに決まっていないので照らさない（正直に書く）。
    for r in rows:
        f = r["形"]
        sp = ex.FORM_SPEC.get(f)
        if sp is None:
            ng.append(f"{f}: 形の性質表（FORM_SPEC）に無い")
            continue
        mat = r["材料"]
        want_pair = {"1": "列1本", "2": "列2本", "2or1th": "列2本",
                     "inner": "内側の条件1つ",
                     "inner2": "内側の条件2つ",     # ★状態を保つ形（入る on・出る off）＝M2-2-5
                     "none": "ローソク列"}[sp["pair"]]
        if want_pair not in mat:
            ng.append(f"{f}: 説明の「材料」（{mat}）と性質表（{sp['pair']}＝{want_pair}）が食い違う")
        has_band_txt = ("下限" in r["必要な値"]) and ("上限" in r["必要な値"])
        if has_band_txt != bool(sp["band"]):
            ng.append(f"{f}: 説明の「必要な値」に下限・上限が"
                      f"{'在る' if has_band_txt else '無い'}のに、性質表の帯は {sp['band']}")
    return dict(rows=rows, ng=ng, n_forms=len(ex.FORMS),
                doc=".claude/ratchet/" + doc.name)


def condition_parts() -> dict:
    """★条件の部品の一覧を出す（段C の C-1・2026-08-11 新設・まこさん OK）。

    なぜ要るか。
      いまの engine_tuner は「条件の形」を11個の名前で持っている（engine_tuner_exec.FORMS）。
      11個は 2026-08-01 の commit 254066a で一度に手で書かれ、以降1個も増えていない。
      ＝私が思いついたら1語 足す運用になっていた（まこさん指摘 2026-08-11
      「これは手書きで思い付いたら増やす。みたいな運用になるのか？すごい原始的なんだが。」）。
      11個を実物のコードで分解すると、全部が同じ小さい部品の組み合わせだった。

    どこから引くか。
      中身 … .claude/ratchet/condition_parts.json（業界5件と照らして決めた・判定の理由つき）
      ★下の4つは毎回 実物から取り直す（json の記録がずれたら ❌ を出す）。

    毎回 機械で確かめること（番人4件）。
      ①いまの形（FORMS）が、分解の表に全部 載っているか（逆に、表に在って実物に無い形が無いか）
      ②分解の表が使っている部品の名前が、「いま在る部品」に全部 在るか
      ③pandas-ta の「使い方」の関数の数が、記録と合っているか（入っているので毎回 数え直す）
      ④「閾値とのクロス」が、いまも本当に書けないか（実行器の検証器に渡して拒否されること）
    """
    import engine_tuner_exec as ex
    src = _RATCHET / "condition_parts.json"
    if not src.exists():
        return dict(ng=[f"正本が無い: {src}"], rows_have=[], rows_missing=[],
                    rows_no=[], sources=[], forms={}, live={})
    d = json.loads(src.read_text(encoding="utf-8"))
    ng: list[str] = []

    # ── 番人① いまの形が、分解の表に全部 載っているか（両向き）──
    dec = {k: v for k, v in d["form_decomposition"].items() if not k.startswith("_")}
    miss = [f for f in ex.FORMS if f not in dec]
    extra = [f for f in dec if f not in ex.FORMS]
    if miss:
        ng.append(f"実行器に在るのに分解の表に無い形: {miss}")
    if extra:
        ng.append(f"分解の表に在るのに実行器に無い形: {extra}")

    # ── 番人② 分解の表が使っている部品が、「いま在る部品」に全部 在るか ──
    have_ids = {p["id"] for p in d["have"]}
    used = {pid for v in dec.values() for pid in v}
    unknown = sorted(used - have_ids)
    if unknown:
        ng.append(f"分解の表が知らない部品を指している: {unknown}")
    unused = sorted(have_ids - used)

    # ── 番人③ pandas-ta の「使い方」の関数を数え直す ──
    live: dict = {}
    rec = {s["id"]: s for s in d["sources"]}
    try:
        import pandas_ta_classic.utils as _U
        key = ("above", "below", "cross", "signals", "lag")
        fns = sorted(n for n in dir(_U)
                     if not n.startswith("_") and callable(getattr(_U, n))
                     and any(k in n.lower() for k in key))
        live["pandas_ta"] = fns
        if len(fns) != rec["pandas_ta"]["n"]:
            ng.append(f"pandas-ta の使い方の関数が {rec['pandas_ta']['n']} 件の記録と違う（実測 {len(fns)} 件）")
    except Exception as e:                       # 入っていない時は黙らせず理由を出す
        live["pandas_ta"] = []
        ng.append(f"pandas-ta を数えられなかった: {str(e)[:60]}")

    # ── 番人④「閾値とのクロス」（cross_val）の在る/無いが、実物と一致しているか ──
    #   ★2026-08-13（段C の C-6・部品①）に両向きの検査へ直した。
    #     直す前＝「拒否されること」だけを見ていた（書けるようになったら ❌ を出す片向き）。
    #     直したあと＝json の側が「在る」なら通ること・「足りない」なら拒否されることを見る。
    #     ＝どちらに動いても、表と実物がずれたら ❌ が出る。判定は json から引く＝ここに答えを書かない。
    _m14 = [{"family": "RSI", "param": 14, "tf": "5m"}]
    _cv_have = "cross_val" in have_ids

    def _probe(cond, label):
        try:
            ex._check_cond(cond, "legacy", f"番人（{label}）", [])
            return True, "通った"
        except SystemExit as e:
            return False, f"拒否（{str(e)[:50]}）"

    #   ★閾値は整数グリッドの値で渡す（_check_value は n が int でないと拒否する＝実行器:246）。
    ok_th, msg_th = _probe({"form": "cross", "value": {"direction": "up", "th": {"n": 70}},
                            "material": _m14}, "閾値とのクロス")
    ok_no, msg_no = _probe({"form": "cross", "value": {"direction": "up"},
                            "material": _m14}, "閾値の無い列1本の cross")
    live["cross_value"] = (f"閾値つき＝{msg_th} ／ 閾値なし＝{msg_no}"
                           f"（部品の一覧では{'『在る』' if _cv_have else '『足りない』'}）")
    if _cv_have and not ok_th:
        ng.append("「閾値とのクロス」が部品の一覧では『在る』のに、実行器の検証器が拒否する"
                  f"＝{msg_th}")
    if (not _cv_have) and ok_th:
        ng.append("「閾値とのクロス」が通るようになっている＝部品の一覧が古い（cross_val を『在る』へ移す）")
    if ok_no:
        ng.append("閾値の無い列1本の cross が通る＝閾値の書き忘れを検証器が捕まえていない")

    # ── 番人⑤ 分解の表が、実際に動くコード（condition_parts_diag の組み立て）と一致するか ──
    #   ★表だけを直しても、動くコードと食い違えばここで落ちる（2026-08-11 の C-2 で
    #    「読んで分解した表」に3つの抜けが在ったため、表と実装を機械で結んだ）。
    live["decomposition"] = _parts_from_diag(dec, ng)

    return dict(ng=ng, unused=unused, sources=d["sources"], forms=dec,
                rows_have=d["have"], rows_missing=d["missing"], rows_no=d["not_needed"],
                live=live, note=d["_why"], scope=d["_scope"], how=d["_how_decided"],
                c2=d.get("_c2_found", ""))


def parts_matrix() -> dict:
    """★指標 × 部品 の突き合わせ（段C の C-3・2026-08-11）。

    何を出すか。
      ①指標 244種類を「パラメータの数」で分ける＝列を2本 並べられるかが決まる
      ②部品を「何が要るか」で分けて、使える指標の数を出す
      ③★業界の定番のクロスを1件ずつ、実行器と生成器の両方で機械判定する

    判定の根拠（全部 実物・CC が結果を手で書かない）。
      実行器 … engine_tuner_exec._check_cond に実際に条件を渡して、通るか拒否されるか
      生成器 … engine_tuner_gen._pair_materials の決まり（同じ指標でパラメータが2つ以上／
               Stoch%K と %D の直書きの対だけ）
    """
    import collections
    import engine_tuner_exec as ex
    import engine_tuner_gen as gen
    pool, tfs, _tot = _quiet(gen.material_pool)
    by: dict[str, list] = collections.defaultdict(list)
    for b in pool:
        by[b["family"]].append(b["param"])
    n_multi = sum(1 for ps in by.values() if len({str(p) for p in ps}) >= 2)
    n_one = sum(1 for ps in by.values() if len({str(p) for p in ps}) == 1 and ps[0] is not None)
    n_none = sum(1 for ps in by.values() if all(p is None for p in ps))

    src = _RATCHET / "condition_parts.json"
    d = json.loads(src.read_text(encoding="utf-8")) if src.exists() else {"classic_crosses": []}
    rows = []
    for cc in d.get("classic_crosses", []):
        a, b = cc["a"], cc["b"]
        pa, pb = by.get(a), by.get(b)
        if pa is None or pb is None:
            rows.append(dict(name=cc["name"], a=a, b=b, exec_ok="—（材料に無い）",
                             gen_ok="—", note=cc.get("note", "")))
            continue
        # ① 実行器＝実際に検証器へ渡す
        if a == b:
            ps = sorted({str(x): x for x in pa}.values(), key=str)
            m1, m2 = {"family": a, "param": ps[0], "tf": "5m"}, {"family": b, "param": ps[-1], "tf": "5m"}
        else:
            m1, m2 = {"family": a, "param": pa[0], "tf": "5m"}, {"family": b, "param": pb[0], "tf": "5m"}
        cond = {"form": "cross", "value": {"direction": "up"}, "material": [m1, m2]}
        try:
            ex._check_cond(cond, "legacy", "C-3", [])
            e_ok = "✅ 受け付ける"
        except SystemExit as e:
            e_ok = f"❌ 拒否（{str(e)[:40]}）"
        except Exception as e:
            e_ok = f"❌ {type(e).__name__}"
        # ② 生成器＝決まりの実物（engine_tuner_gen.pair_allowed）を呼ぶ。
        #    ★決まりをここに書き写さない（2026-08-11・段C の C-5）。書き写すと、生成器だけ直って
        #      この判定が古いまま残る＝「直したのに ❌ のまま」「直していないのに ✅」が起きる。
        g_ok = "✅ 作る" if gen.pair_allowed(a, b, pa, pb) else "❌ 作らない（別の指標どうし）"
        rows.append(dict(name=cc["name"], a=a, b=b, exec_ok=e_ok, gen_ok=g_ok, note=cc.get("note", "")))

    ng = []
    blocked = [r for r in rows if r["gen_ok"].startswith("❌") and r["exec_ok"].startswith("✅")]
    return dict(n_fam=len(by), n_multi=n_multi, n_one=n_one, n_none=n_none,
                n_tf=len(tfs), rows=rows, blocked=len(blocked), ng=ng)


def section_ng() -> list[str]:
    """★materials.md の節が印字する ❌ を、1か所に集める（2026-08-13 新設・まこさん指示）。

    何を守るか。
      節（★5 使い方の一覧／★6 条件の部品／★7 指標 × 部品）は、それぞれ自分の ❌ を
      文書の中に印字する。ところが `--selftest` は、その ❌ を1件も見ていなかった。
      ＝**文書に「❌ 1 件」と書いてあるのに、番人が「✅ 全部 pass」と出す**状態が作れた。
      2026-08-13 に実際に起きた（番人④に渡す閾値を小数で書いた誤りが、文書には ❌ として
      出ていたのに、`--selftest` は ✅ を出した。見つけたのは番人ではなく、人が文書を開いたとき）。
    ★ここで集めた ❌ は、`--selftest` の T11 が落とす。`--write` は止めない
      （❌ は文書に出すためのもの＝出せないと、まこさんが読めなくなる）。
    """
    out: list[str] = []
    for name, fn in (("★5 使い方の一覧", forms_table),
                     ("★6 条件の部品", condition_parts),
                     ("★7 指標 × 部品", parts_matrix),
                     ("★9 M2-2 の基準値", _m2_baseline_view)):
        try:
            d = _quiet(fn)
        except Exception as e:                                   # noqa: BLE001
            out.append(f"{name}: 節そのものを作れない（{type(e).__name__}: {str(e)[:60]}）")
            continue
        out += [f"{name}: {x}" for x in (d.get("ng") or [])]
    return out


def _parts_from_diag(dec: dict, ng: list) -> str:
    """condition_parts_diag.py の組み立て（_c_◯◯）が、どの部品（p_◯◯）を使っているかを構文木で数え、
    json の分解の表と1件ずつ突き合わせる。★入れ子（_c_streak が _c_level を呼ぶ）は辿って足す。"""
    import ast
    src = _HERE / "condition_parts_diag.py"
    if not src.exists():
        ng.append(f"C-2 の突き合わせの道具が無い: {src.name}")
        return "道具なし"
    tree = ast.parse(src.read_text(encoding="utf-8"))
    calls: dict[str, set] = {}
    for n in tree.body:
        if isinstance(n, ast.FunctionDef) and n.name.startswith("_c_"):
            calls[n.name] = {c.func.id for c in ast.walk(n)
                             if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                             and (c.func.id.startswith("p_") or c.func.id.startswith("_c_"))}
    def _resolve(fn: str, seen: set) -> set:              # 入れ子を辿る
        out: set = set()
        for c in calls.get(fn, ()):
            if c.startswith("p_"):
                out.add(c[2:])
            elif c not in seen:
                out |= _resolve(c, seen | {c})
        return out
    bad = 0
    for form, want in dec.items():
        got = _resolve("_c_" + form, {"_c_" + form})
        if got != set(want):
            bad += 1
            ng.append(f"分解の表と、動くコードが食い違う（{form}）＝表 {sorted(want)} ／ 実装 {sorted(got)}")
    return f"{len(dec) - bad}/{len(dec)} 一致"


def _regime_decl_view(names: tuple | None = None, decls: list | None = None,
                      builder_cols: list | None = None) -> dict:
    """M2-1-1（2026-08-20 まこさん承認）＝売買を回すプログラム（engine_tuner_exec.py）が要求する
    「相場の宣言」の形を、実物から数える。CC が決める数字は0件（全部 実物からの引き写し）。

    どこから引くか（書き写さない）:
      tuner_adapters.REGIME_NAMES          … 相場の名前の一覧（正本＝cat_requirements §1.2.1 の写し）
      tuner_adapters.check_regime          … 実行前の検査（接続ファイルの宣言を見る・RegimeDeclError）
      engine_tuner_exec._check_regime_meta … レシピの読み込み時の検査（G5）
      engine_tuner_exec._regime_series     … 実行時の検査（列が実データに無ければ止める・fail-closed）
    宣言の鍵（name・entry_col・block_col）も手で書かない＝検査のコードが実際に読む鍵
    （rg.get("…")）から正規表現で引く。

    names 引数＝番人（T15）専用。わざと1件 消した一覧を渡すと、数がちょうど1 減ることを確かめる。
    decls・builder_cols 引数＝番人（T16・M2-1-2）専用。架空の宣言や列の写しを渡すと、
    名前ごとの表の欄が変わることを確かめる。実物のファイルは1バイトも書き換えない。

    ★M2-1-2（2026-08-20 まこさん承認）で足した分＝名前ごとの判定の列の表。
      宣言＝e38_logics.json の global.regime ＋ tuner_adapters/e37.py の REGIME（ソースから引く）。
      列を作る側＝e37_scalp._apply_rg5_to_5m のソースの df["…"] = の列名（★2026-08-20 一本化後の正本）。
      ⚠️ 照合は「列を付けるコードに在るか」＝実データは読み込まない（軽く保ち毎回 数え直すため）。
        データそのものの突き合わせは M2-1-7（range_ok_rg5 と1バーずつ）でやる。
    """
    import inspect
    import re as _re

    import engine_tuner_exec as _ex
    import tuner_adapters as _ta
    nm = tuple(names) if names is not None else tuple(_ta.REGIME_NAMES)
    src_pre = inspect.getsource(_ta.check_regime)
    src_meta = inspect.getsource(_ex._check_regime_meta)
    src_run = inspect.getsource(_ex._regime_series)
    keys = list(dict.fromkeys(_re.findall(r'rg\.get\("([a-z_]+)"\)', src_meta)))
    cols = [k for k in keys if k.endswith("_col")]
    checks = [
        dict(どこで="実行前（接続ファイルの宣言の検査）", 実物="`tuner_adapters.check_regime`",
             件数=src_pre.count("raise RegimeDeclError")),
        dict(どこで="レシピの読み込み時（G5）", 実物="`engine_tuner_exec._check_regime_meta`",
             件数=src_meta.count("_fail(")),
        dict(どこで="実行時（列が実データに無ければ止める・fail-closed）", 実物="`engine_tuner_exec._regime_series`",
             件数=src_run.count("raise RecipeError")),
    ]
    # ── ④ 名前ごとの判定の列（M2-1-2・2026-08-20 まこさん承認）──────────────────────
    import ast as _ast
    if decls is None:
        e38rg = (json.loads(_A1_E38.read_text(encoding="utf-8"))["global"].get("regime") or {})
        _e37src = (_HERE / "tuner_adapters" / "e37.py").read_text(encoding="utf-8")
        _m37 = _re.search(r"^REGIME = (\{.*\})", _e37src, _re.M)
        e37rg = _ast.literal_eval(_m37.group(1)) if _m37 else {}
        decls = [dict(誰が="e38（`e38_logics.json` の global.regime）",
                      **{k: e38rg.get(k) for k in ("name", "entry_col", "block_col")}),
                 dict(誰が="e37（`tuner_adapters/e37.py` の REGIME）",
                      **{k: e37rg.get(k) for k in ("name", "entry_col", "block_col")})]
    if builder_cols is None:
        # ★2026-08-20 一本化（まこさん決定）の後＝_apply_rg5_to_5m の正本は e37_scalp.py。
        #   e37_range_scalp.py の複製は import に置き換えられて定義が消えた＝読み先を正本へ変えた。
        _bsrc = (_HERE / "e37_scalp.py").read_text(encoding="utf-8")
        _mfn = _re.search(r"def _apply_rg5_to_5m.*?(?=\ndef )", _bsrc, _re.S)
        builder_cols = sorted(set(_re.findall(r'df\["([A-Za-z0-9_]+)"\]\s*=', _mfn.group(0)))) if _mfn else []

    def _cell(cols_for_name: list) -> str:
        if not cols_for_name:
            return "宣言なし"
        out = []
        for col in dict.fromkeys(cols_for_name):
            ok = "列を作る側に在る" if col in builder_cols else "★列を作る側に無い"
            out.append(f"`{col}`（{ok}）")
        return "・".join(out)

    per_name = []
    for n in nm:
        ent = [d["entry_col"] for d in decls if d.get("name") == n and d.get("entry_col")]
        blk = [d["block_col"] for d in decls if d.get("name") == n and d.get("block_col")]
        per_name.append(dict(名前=n, 建ててよい列=_cell(ent), 止める列=_cell(blk)))

    return dict(名前の一覧=list(nm), 名前の数=len(nm), 鍵=keys, 要る列=cols,
                検査=checks, 検査の合計=sum(c["件数"] for c in checks),
                宣言=decls, 列を作る側の列=builder_cols, 名前ごと=per_name)


def _m2_baseline_view(forms: tuple | None = None, parts: list | None = None) -> dict:
    """M2-2-1（2026-08-20 まこさん承認）＝M2-2 で足す前の数（基準値）を、実物から数える。

    なぜ要るか。
      M2-2 は「足りない条件の形と部品を、全部 足す」フェーズ（書けない9件 → 0件）。
      足したあとに「何が いくつ 増えたか」を、CC の申告ではなく プログラムの数え直しで示すため、
      **直す前の数をここに固定する。**CC が決める数字は0件（全部 実物からの引き写し）。

    どこから引くか（書き写さない）:
      engine_tuner_exec.FORMS           … 条件の形
      engine_tuner_exec.NEST_FORMS      … そのうち「外側になる形」（中に条件を1つ包む）
      engine_tuner_exec._walk           … 束ね方（つなぎ木が受ける鍵）＝ソースから正規表現で引く
      engine_tuner_exec._walk_build_tree … 判定の中身（build）の側の鍵＝同じ束ね方か・build 専用の形は何か
      engine_tuner_exec.MATERIAL_PRE    … 材料の前処理
      engine_tuner_exec.PAIR_OPS        … 材料2本の組み方
      signal_families.json の parts / timeframes … 部品と時間足

    ★束ね方は2通りで引いて突き合わせる（片方だけだと、コードが変わっても気づけない）。
      ①止める文の逐語（「つなぎ木のノードが all/any/if-then/条件 のどれでもない」）
      ②コードの鍵（`"all" in node` の形）
      2つが食い違ったら ❌ を出す。

    forms・parts 引数＝番人（T17）専用。わざと1種 消した写しを渡すと、数がちょうど1 減ることを
      確かめる。★実物のファイルは1バイトも書き換えない（写しを渡すだけ）。
    """
    import inspect
    import re as _re

    import engine_tuner_exec as _ex
    ng: list[str] = []
    fm = tuple(forms) if forms is not None else tuple(_ex.FORMS)
    nest = tuple(f for f in _ex.NEST_FORMS if f in fm)

    # ── 束ね方＝つなぎ木の実物から2通りで引いて、両方が合うことを確かめる ──
    src_walk = inspect.getsource(_ex._walk)
    keys_node = list(dict.fromkeys(_re.findall(r'"([a-z]+)" in node', src_walk)))
    _m = _re.search(r"つなぎ木のノードが ([a-z/\-]+)/条件", src_walk)
    joins = _m.group(1).split("/") if _m else []
    atoms = [a for j in joins for a in j.split("-")]
    if not joins:
        ng.append("束ね方を止める文から引けない（`_walk` の逐語が変わった）")
    elif sorted(atoms) != sorted(keys_node):
        ng.append(f"束ね方の引き方が2通りで食い違う（止める文＝{joins} ／ コードの鍵＝{keys_node}）")

    # ── 判定の中身（build）の側＝同じ束ね方を受けるか・build だけで使える形は何か ──
    src_build = inspect.getsource(_ex._walk_build_tree)
    keys_build = list(dict.fromkeys(_re.findall(r'"([a-z_]+)" in node', src_build)))
    lack = [a for a in atoms if a not in keys_build]
    if lack:
        ng.append(f"判定の中身（build）の側が受けない束ね方がある: {lack}")
    build_only = [k for k in keys_build if k not in set(atoms) and k not in fm]

    # ── 部品と時間足＝承認済みの型の表から ──
    _sf = _RATCHET / "signal_families.json"
    sf = json.loads(_sf.read_text(encoding="utf-8")) if _sf.exists() else {"parts": [], "timeframes": []}
    if not _sf.exists():
        ng.append(f"型の表が無い: {_sf}")
    pt = list(parts) if parts is not None else list(sf["parts"])
    tfs = list(sf["timeframes"])

    def _join(xs) -> str:
        return "・".join(f"`{x}`" for x in xs) if xs else "（無し）"

    rows = [
        dict(何="条件の形", 数=len(fm), 単位="種", 実物="`engine_tuner_exec.FORMS`", 中身=_join(fm)),
        dict(何="うち 外側になる形（中に条件を1つ包む）", 数=len(nest), 単位="種",
             実物="`engine_tuner_exec.NEST_FORMS`", 中身=_join(nest)),
        dict(何="判定の中身（build）の中だけで使える形", 数=len(build_only), 単位="種",
             実物="`engine_tuner_exec._walk_build_tree`", 中身=_join(build_only)),
        dict(何="束ね方", 数=len(joins), 単位="通り", 実物="`engine_tuner_exec._walk`", 中身=_join(joins)),
        dict(何="部品", 数=len(pt), 単位="種", 実物="`signal_families.json` の `parts`",
             中身="（一覧は ★2 と ★7）"),
        dict(何="時間足", 数=len(tfs), 単位="本", 実物="`signal_families.json` の `timeframes`",
             中身=_join(tfs)),
        dict(何="材料の列（部品 × 時間足）", 数=len(pt) * len(tfs), 単位="列",
             実物="上の2つの掛け算", 中身="—"),
        dict(何="材料の前処理", 数=len(_ex.MATERIAL_PRE), 単位="種",
             実物="`engine_tuner_exec.MATERIAL_PRE`", 中身=_join(_ex.MATERIAL_PRE)),
        dict(何="材料2本の組み方", 数=len(_ex.PAIR_OPS), 単位="種",
             実物="`engine_tuner_exec.PAIR_OPS`", 中身=_join(_ex.PAIR_OPS)),
    ]
    return dict(rows=rows, ng=ng, 形の数=len(fm), 部品の数=len(pt), 時間足の数=len(tfs),
                束ね方=joins, buildだけの形=build_only)


def build_body() -> dict:
    """表の中身を作る（正本から機械で引く）。"""
    rbl = _roles_by_lineage()
    lib = _lib_funcs()
    rows = []
    # ★いま材料カタログに実際に列が在る family を機械で数える（2026-08-11 に足した）。
    #   理由＝この表は参照表 REFS から作っている。同じ挙動の列を省くと、カタログには無いのに
    #   ここだけ「在る」と書いてしまう（正本が嘘をつく＝L-430・L-436 と同じ型）。
    _drop_map = dict(_dropped_columns())

    def _live_families() -> dict:
        import contextlib as _c
        import io as _i
        with _c.redirect_stdout(_i.StringIO()):
            import observe_diag as _od
            _cfg = _od.load_config()
            _names = [n for n, _f, _d in _od.build_catalog(_cfg)]
        out: dict[str, int] = {}
        for n in _names:
            ent = iref.find(n)[0]
            if ent is not None:
                out[ent["family"]] = out.get(ent["family"], 0) + 1
        return out
    live = _live_families()
    # ── 状態「在る」＝いま材料カタログに在る指標の種類 ──
    for e in iref.REFS:
        fam = e["family"]
        lin = iref.FAMILY_LINEAGE.get(fam, {}).get("k", "")
        q = iref.LINEAGE_QUESTION.get(lin, ("", ""))[0]
        if live.get(fam, 0) == 0:
            keep = next((k for d, k in _drop_map.items() if (iref.find(d)[0] or {}).get("family") == fam), "")
            st = ("省いた（同じ挙動＝残したのは " + keep + "）") if keep else "省いた（列が無い）"
        else:
            st = "在る"
        rows.append(dict(名前=fam, 系統=lin, 答える問い=q,
                         使える役割="・".join(rbl.get(lin, [])) or "（どの役割にも割り当てが無い）",
                         計算の出どころ=_source_note(fam, e["ext"] is not None),
                         グループ=_GROUP_TBD, 状態=st))
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
    # ── 段5（2026-08-09 追加）＝engine_tuner が選べるか ＋ 足すものの一覧 ＋ 入れない一覧 ──
    ev = _engine_view() if lib else None
    if ev is not None:
        for r in rows:
            r["engine_tuner"] = _row_engine(r, ev)
        # ★承認の欄（2026-08-10 新設）＝まこさんが実際に承認した19件（2026-08-09）だけを ✅ にする。
        #   それ以降に CC が足したものは ★未承認。文書が全件を「承認済み」と書いていたのを是正した。
        skip_rows = [dict(名前=fn, 理由=iref.INDUSTRY_SKIP[fn],
                          承認=iref.SKIP_APPROVED.get(fn, "★未承認"))
                     for fn in iref.INDUSTRY_SKIP if fn in lib]
        gaps = _gaps(ev, counts, counts["足す"], skip_rows)
        engine = dict(選べる指標の種類=len(ev["selectable_fams"]),
                      選べない指標の種類=len(ev["unselectable_fams"]),
                      選べる組=len(ev["pool"]), 時間足=len(ev["tfs"]),
                      選べる列=ev["cols_selectable"], カタログ総列数=ev["cat_total"],
                      レンジ幾何=ev["geo_ok"], 時間帯=ev["time_ok"], 期間=ev["params"])
    else:
        for r in rows:
            r["engine_tuner"] = _SEL_NA
        skip_rows, gaps, engine = [], [], {}
    return dict(rows=rows, counts=counts,
                lineage_question={k: dict(問い=v[0], 出典=v[1]) for k, v in iref.LINEAGE_QUESTION.items()},
                library_ready=bool(lib), library_funcs=len(lib),
                gaps=gaps, skip_rows=skip_rows, engine=engine,
                a1=fixed_number_places(),   # 段A の A-1＝「決まった数字だけ」の4か所（2026-08-12）
                regime_decl=_regime_decl_view(),   # M2-1-1＝相場の宣言の形（2026-08-20 まこさん承認）
                m2_baseline=_m2_baseline_view())   # M2-2-1＝足す前の数（2026-08-20 まこさん承認）


def _body_hash(body: dict) -> str:
    return hashlib.sha256(json.dumps(body, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def _render_parts(p: dict) -> list[str]:
    """★6｜条件の部品の一覧（段C の C-1）。中身は condition_parts.json＝ここで新しい事実を書かない。"""
    L = ["", "## ★6｜条件の部品の一覧（engine_tuner が条件を組み立てる部品）", "",
         "**★この節は機械が作ります（手書きゼロ）。**中身の正本＝`.claude/ratchet/condition_parts.json`。", "",
         f"**対象**＝{p.get('scope', '')}", "",
         "**なぜ部品で持つか。**" + p.get("note", ""), "",
         "**どうやって決めたか。**" + p.get("how", ""), ""]
    L += ["**照らした相手（業界の実物）**", "",
          "| 出どころ | 部品の数 | 取り方 | 中身 |", "|---|---|---|---|"]
    for s in p["sources"]:
        n = "—" if s.get("n") is None else str(s["n"])
        how = "**毎回 機械で数え直す**" if s["how"] == "live" else "記録（機械では数え直せない）"
        # 出どころが URL でないもの（このプロジェクトに入っているライブラリ）はリンクにしない
        nm = f"[{s['name']}]({s['url']})" if s["url"].startswith("http") else f"{s['name']}（このプロジェクトに入っている）"
        L.append(f"| {nm} | {n} | {how} | {s['detail']} |")
    L += ["", f"**いま在る部品＝{len(p['rows_have'])} 個。足りない部品＝{len(p['rows_missing'])} 個。"
              f"合計 {len(p['rows_have']) + len(p['rows_missing'])} 個。**", ""]
    L += ["### いま在る部品", "", "| # | 部品 | どこに在るか | 実物 | 業界の同じもの |", "|---|---|---|---|---|"]
    for i, r in enumerate(p["rows_have"], 1):
        L.append(f"| {i} | **{r['name']}** | {r['where']} | {r['impl']} | {'・'.join(r['src'])} |")
    L += ["", "### 足りない部品", "", "| # | 部品 | これがあると書ける条件 | 業界の同じもの |", "|---|---|---|---|"]
    for i, r in enumerate(p["rows_missing"], len(p["rows_have"]) + 1):
        L.append(f"| {i} | **{r['name']}** | {r['can_write']} | {'・'.join(r['src'])} |")
    L += ["", "### 要らないと判断したもの（理由つき・★判定は CC が書きました）", "",
          "| 業界に在る部品 | 要らない理由 |", "|---|---|"]
    for r in p["rows_no"]:
        L.append(f"| {r['name']} | {r['why']} |")
    L += ["", "### いまの11個の形が、どの部品でできているか（実物のコードを分解した）", "",
          "| 形 | 部品 |", "|---|---|"]
    for f, ps in p["forms"].items():
        L.append(f"| `{f}` | {'・'.join(ps)} |")
    L += ["", "### 番人（毎回 実物で確かめる）", ""]
    L.append(f"- pandas-ta の「使い方」の関数＝実測 **{len(p['live'].get('pandas_ta', []))} 件**"
             f"（{'・'.join(p['live'].get('pandas_ta', []))}）")
    L.append(f"- 「閾値とのクロス」（RSI が 70 を上抜けた）を実行器の検証器に渡した結果＝**{p['live'].get('cross_value','')}**")
    if p.get("unused"):
        # ★2026-08-13＝ただ「使っていない」と出すのをやめ、どこで使うかを正本の欄から引いて出す。
        #   例＝どれか満たす（OR）は「形」ではなく、条件の木（発火経路）で使う部品。
        _w = {r["id"]: str(r.get("where", "")) for r in p["rows_have"]}
        L.append("- 上の「形の分解」に出てこない部品（＝形ではなく、条件の木やつなぎ方で使うもの）＝"
                 + " ／ ".join(f"**{u}**（{_w.get(u, '？')}）" for u in p["unused"]))
    if p["ng"]:
        L += ["", f"**❌ {len(p['ng'])} 件**"] + [f"- {x}" for x in p["ng"]]
    else:
        L += ["", "**✅ ずれ 0 件**（形の数・部品の名前・業界の数・閾値とのクロス、すべて実物と一致）"]
    return L


def _render_matrix(m: dict) -> list[str]:
    """★7｜指標 × 部品 の突き合わせ（段C の C-3）。判定は毎回 機械が実物に当てて出す。"""
    L = ["", "## ★7｜指標 × 部品 の突き合わせ（どの指標に、どの部品が使えるか）", "",
         "**★この節は機械が作ります（手書きゼロ）。**判定のたびに、実行器の検証器へ実際に条件を渡して確かめます。", "",
         "### 指標の内訳（列を2本 並べられるかが、ここで決まる）", "",
         "| 何 | 数 |", "|---|---|",
         f"| 指標の種類 | **{m['n_fam']}** |",
         f"| うち **パラメータを2つ以上 持つ**（同じ指標のパラメータ違いで 2本 並べられる） | **{m['n_multi']}** |",
         f"| うち パラメータが1つだけ | {m['n_one']} |",
         f"| うち パラメータが無い | {m['n_none']} |",
         f"| 時間足 | {m['n_tf']} |", "",
         "### 部品を「何が要るか」で分けると", "",
         "| 何が要るか | 部品 | 使える指標の数 |", "|---|---|---|",
         f"| **材料 1本** | 値を持ってくる・n本 ずらす・n本の平均・絶対値・比べる・掛け算・値が在るか"
         f"（＋足りない部品の n本の最大値・最小値・順位・ばらつき） | **{m['n_fam']}（全部）** |",
         f"| **材料 2本** | 引き算（差・クロス・タッチ）（＋足りない部品の 割り算・2本の相関） | "
         f"**{m['n_multi']}**（同じ指標のパラメータ違いに限る） |",
         "| **条件を受ける** | かつ・でない・n本のうち 全部／どれか・条件を n本 ずらす（＋足りない部品の どれか満たす・何本前に成立したか） | 指標に依らない |",
         "", "### ★業界の定番のクロスが、いま作れるか（1件ずつ 機械が判定）", "",
         "**実行器**＝条件を検証器に渡して通るか。**生成器**＝engine_tuner が実際にその組を作るか。", "",
         "| 定番のクロス | 実行器 | 生成器 | 注 |", "|---|---|---|---|"]
    for r in m["rows"]:
        L.append(f"| {r['name']} | {r['exec_ok']} | {r['gen_ok']} | {r['note']} |")
    if m["blocked"]:
        L += ["", f"**❌ 実行器は受け付けるのに、生成器が作らない定番のクロス＝{m['blocked']} 件。**", "",
              "**理由**＝生成器が「列2本の形」を作るとき、**同じ指標のパラメータ違い**しか組みません",
              "（`engine_tuner_gen._pair_materials`）。**別の指標どうしの組は、Stoch%K と %D の1組だけが",
              "コードに直書きで例外扱いされています。**", "",
              "**＝MACD のクロスは、engine_tuner が何回 走っても出てきません。**",
              "これは 2026-08-08 のインシデント #15（組み立ての決まりで MACD のクロスを潰した）と同じものが、",
              "別の場所（生成器の対の作り方）に残っていたということです。", "",
              "**★直すのはマイルストーン②です。**この節は「いまどうなっているか」を出すところまでです。"]
    else:
        L += ["", "**✅ 定番のクロスは全部 作れます。**"]
    return L


def _render_regime(rd: dict) -> list[str]:
    """★8｜相場の宣言（M2-1-1・2026-08-20 まこさん承認）。数字と一覧は全部 _regime_decl_view が実物から引く。"""
    L = ["", "## ★8｜相場の宣言（M2-1-1）＝売買を回すプログラムが要求する形", "",
         "**★この節は機械が実物から引いて書きます（数字と一覧の手書きゼロ・まこさん承認 2026-08-20）。**",
         "レシピの `meta.regime` がこの宣言を持ち、3か所の検査が守ります。",
         "M2-1 の実装（engine_tuner が組み立てた判定を、売買に渡す道）は、この形の上に乗ります。", "",
         f"**① 相場の名前の一覧＝{rd['名前の数']} 件**"
         "（実物＝`tuner_adapters.REGIME_NAMES`・正本＝`cat_requirements.md` §1.2.1 の4局面の写し）", "",
         "| 名前 |", "|---|"]
    for n in rd["名前の一覧"]:
        L.append(f"| `{n}` |")
    L += ["", f"**② 宣言に要る鍵＝{len(rd['鍵'])} 件（うち列の名前は {len(rd['要る列'])} 件）**",
          "検査のコード（`_check_regime_meta`）が実際に読む鍵から機械で引きました。", "",
          "| 鍵 | 何か |", "|---|---|"]
    for k in rd["鍵"]:
        if k in rd["要る列"]:
            imi = ("このバーだけ玉を建ててよい、を表す列の名前（真偽値）" if k == "entry_col"
                   else "このバーでは新規の発注を止める、を表す列の名前（要らなければ null）")
        else:
            imi = "相場の名前（上の一覧のどれか）"
        L.append(f"| `{k}` | {imi} |")
    L += ["", f"**③ 止める検査＝合計 {rd['検査の合計']} 件（3か所・件数は関数の実物から数えた）**", "",
          "| どこで | 実物 | 検査の数 |", "|---|---|---|"]
    for c in rd["検査"]:
        L.append(f"| {c['どこで']} | {c['実物']} | {c['件数']} 件 |")
    L += ["", "**④ 名前ごとの、いま在る判定の列（M2-1-2・宣言と、列を作る側の照合）**", "",
          "| 名前 | 建ててよい列（entry_col） | 止める列（block_col） |", "|---|---|---|"]
    for r in rd["名前ごと"]:
        L.append(f"| `{r['名前']}` | {r['建ててよい列']} | {r['止める列']} |")
    L += ["",
          "**宣言の出どころ（実物）**＝" + "／".join(d["誰が"] for d in rd["宣言"]) + "。",
          f"**列を作る側（`e37_scalp._apply_rg5_to_5m`＝一本化後の正本）が付ける列＝{len(rd['列を作る側の列'])} 本**"
          f"（{'・'.join('`' + c + '`' for c in rd['列を作る側の列'])}）。",
          "⚠️ `rg5_uptrend` は上げトレンドの判定の列ですが、宣言の上では range の止める列として使われています",
          "＝uptrend の行に宣言はありません（M2-6 で上げの判定を組むときの、比べる相手になります）。",
          "**正直に書く注意**＝この照合は「列を付けるコードに在るか」であって、実データは読み込みません。",
          "データそのものの突き合わせは M2-1-7（`range_ok_rg5` と1バーずつ）でやります。", "",
          "**⚠️ 名前を書いただけでは、その相場を扱えません。**判定の列が実データに無ければ、実行時に止まります",
          "（`_regime_series` の逐語＝「判定を作る処理が要ります（engine_tuner の外側の作業）」）。",
          "**★いまの engine_tuner は、判定の中身を組み立てられません**（できあがった列の名前を読むだけ）。",
          "組み立てて渡す道を作るのが M2-1 です（やることリスト＝`engine_tuner_milestones2.md` §4）。",
          "番人＝`--selftest` の T15（名前を わざと1件 消すと数がちょうど1 減ること）と",
          "T16（架空の列を宣言の写しに足すと、欄が変わり「★列を作る側に無い」と出ること）。"]
    return L


def _render_m2_baseline(b: dict) -> list[str]:
    """★9｜M2-2 の基準値（M2-2-1・2026-08-20 まこさん承認）。数字は全部 _m2_baseline_view が実物から引く。"""
    L = ["", "## ★9｜M2-2 の基準値（M2-2-1）＝足す前の数", "",
         "**★M2-2 で増える前の数（基準値）＝2026-08-20 時点。**", "",
         "**★この節は機械が実物から引いて書きます（数字の手書きゼロ・まこさん承認 2026-08-20）。**",
         "**なぜ要るか。**M2-2 は「足りない条件の形と部品を、全部 足す」フェーズです。",
         "足したあとに「何が いくつ 増えたか」を、私の申告ではなく、プログラムの数え直しで示します。",
         "そのために、直す前の数をここに固定します。", "",
         "| 何 | 数 | 実物（どこから数えたか） | 中身 |", "|---|---|---|---|"]
    for r in b["rows"]:
        L.append(f"| {r['何']} | **{r['数']} {r['単位']}** | {r['実物']} | {r['中身']} |")
    L += ["",
          "**M2-2 で足すもの（やることリスト §4 の M2-2-4）**＝否定（not）／状態を保つ形"
          "（入る線と出る線・続く長さは探す値）／帯を作る形（山谷の確定遅延・束ね・連動する閾値）／"
          "切り上げの部品。**この節の数が、そのぶん増えます。**", "",
          "**★数の読み方（大事なところ）**", "",
          "- **「条件の形」と「束ね方」は別のものです。**形＝1つの条件の書き方（水準・クロスなど）。",
          "  束ね方＝条件どうしのつなぎ方（`all`＝全部・`any`＝どれか・`if-then`＝ならば）。",
          "- **「判定の中身（build）の中だけで使える形」**は、M2-1 で足した最小の1つです"
          "（真偽の列を参照する形）。入口の条件では使えません。",
          "- **「材料の列」は掛け算です**（部品 × 時間足）。部品が1種 増えると、列は時間足の本数ぶん 増えます。", ""]
    if b["ng"]:
        L += [f"**❌ {len(b['ng'])} 件**"] + [f"- {x}" for x in b["ng"]] + [""]
    else:
        L += ["**✅ ずれ 0 件**（束ね方を2通りで引いて一致・判定の中身の側も同じ束ね方を受ける）", ""]
    L += ["番人＝`--selftest` の T17（形と部品を わざと1種 消した写しを渡すと、"
          "数がちょうど1 減ること）。"]
    return L


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
         "> ★「入れない」の承認は**1件ずつ ★4 の表に出しています**（全部が承認済みではありません）。",
         "> 既定は「入れる」です（まこさん決定＝「利益最大化するために完全に不要な指標以外はすべて入れてほしい」）。",
         "> ですからここに載っているのは「指標ではないもの」だけです。", "",
         "> ⚠️ 「グループ」の欄は、この段では全部 空です（フロー 段8 で埋めます）。", ""]
    e = body.get("engine") or {}
    a1 = body.get("a1") or {}                # 段A の A-1＝「決まった数字だけ」の4か所（2026-08-12）
    if e:
        L += ["## ★1｜足すものの一覧（フロー 段5・まこさんが見るのはここです）", "",
              "**4か所に散っていた不足を、機械が1つにまとめました。**下の A〜G が、これから足す候補の全部です。",
              "**この段では1件も足しません。**足すのは段6 です。", "",
              "| 印 | 何を足すか | 数 | 出どころ |", "|---|---|---|---|"]

        for g in body["gaps"]:
            L.append(f"| {g['印']} | {g['何を足すか']} | **{g['数']} {g['単位']}** | {g['出どころ']} |")
        L += ["", "**中身（名前の一覧）**", ""]
        for g in body["gaps"]:
            L.append(f"- **{g['印']}（{g['数']} {g['単位']}）** … {g['中身']}")
        L += ["",
              "> ★印 B・C・G は、検査9・検査10・検査7 が出したものではありません。**段5 で新しく数えたものです。**",
              "> 段6 で A（業界の指標）だけを材料カタログに足しても、engine_tuner はそれを条件に選べません。",
              "> 選べるようにするには B の入口（下の ★2）も一緒に直す必要があります。", "",
              "## ★2｜engine_tuner がいま条件の材料として選べるもの（段5 で機械が数えた）", "",
              "**材料カタログに在ることと、engine_tuner が条件に選べることは別です。**",
              "下は、生成器（engine_tuner_gen）が実際に選べるものを実物から数えた結果です。", "",
              "| 何 | 数 |", "|---|---|",
              f"| 材料カタログの列（部品 × 時間足） | {e['カタログ総列数']} 列 |",
              f"| **engine_tuner が選べる列** | **{e['選べる列']} 列"
              f"（{100.0 * e['選べる列'] / max(e['カタログ総列数'], 1):.1f}%）** |",
              f"| engine_tuner が選べる指標の種類 | **{e['選べる指標の種類']} 種類** |",
              f"| **engine_tuner が選べない指標の種類** | **{e['選べない指標の種類']} 種類**（上の一覧 B） |",
              f"| そのほかに選べるもの（レンジ幾何） | {'・'.join(e['レンジ幾何']) or '（無し）'} |",
              f"| そのほかに選べるもの（時間帯） | 時刻だけ（型の表は {'・'.join(e['時間帯'])} を許す） |",
              "",
              "**何が「選べる」を決めているか**＝実行器の `FAMILY_TEMPLATES`（列名の組み立て表）に",
              "載っていない指標は、レシピの読み込みの段階で `G6` が拒否します。",
              "**★2026-08-11（段6 の 6-7）に、この表を「手書き19件」から「参照表から機械で作る」形に変えました。**",
              "参照表 `indicator_reference_diag.REFS`（材料カタログの列名の正本）の正規表現から、",
              "名前の組み立ての型を機械で作ります＝材料カタログに列が増えれば、そのまま選べるようになります。",
              "**直す前は 232種類 が選べませんでした**（MACD・BB%b・一目の転換線と基準線・ローソク足の形 ほか。",
              "5,049列 のうち選べるのは 432列＝8.6% だけ）。**直したあとの実測は上の表のとおりです。**",
              "番人＝`engine_tuner_exec.py --selftest` の往復テスト（カタログの全列名を分解して組み立て直し、",
              "1文字も違わないこと＋わざと型を1件 壊すと落ちること）。", "",
              "> ⚠️ **ここで言う「選べる」は、レシピの読み込みが拒否しないという意味です。**",
              "> 生成器が実際にその部品を引くかどうかは、承認済みの型の表（`signal_families.json`）に",
              "> その部品が載っているかで決まります（材料が増えたぶんを表に反映するのが 6-6 です）。", "",
              "## ★3｜「決まった数字だけ」に固定されている場所（4か所）", "",
              "**（マイルストーン③の対象。★この節は事実を出すだけで、直しません。"
              "直すのは 段A です。場所ごとに行が分かれています＝"
              "場所1 は A-2・A-3・A-4・A-6 ／ 場所2 は A-5（int_grid）・A-5-2（残り9件）・"
              "A-5-3（分位の段）／ 場所3 は A-5-4 ／ 場所4 は A-5-5。）**", "",
              "**「決まった数字だけ」とは何か。**engine_tuner が試せる数字が、"
              "あらかじめ並べてある一覧に限られている状態のことです。",
              "**その一覧に無い数字は、何回 試しても永久に出てきません。**",
              "例＝RSI で試せるのは 7本・9本・14本・21本 の4つだけで、RSI12 も RSI30 も出てきません。",
              "本来の形は「範囲で探す」＝下限と上限の間の、どの数字でもよい、という探し方です。",
              "いまは、要件の「作ってはいけないもの」2番"
              "（原文＝探す値を、CC が先に「点の一覧」で限定するもの）に当たる状態です。", "",
              "**★数え方（この節の数字は、機械が実物のファイルを開いて毎回 数え直しています）**", "",
              "- **「数の並び」**＝要素が全部 数字の並び（例＝`[7, 9, 14, 21]`）を **1** と数えます。",
              "- 説明のための鍵（`_` で始まるもの）は数えません。",
              "- 検収専用の値は数えません＝`engine_tuner_gen.py` の `selftest` と `KENSHU_LIMITS`"
              "（出どころ＝`recipes/search_limits.json` の `_note` の逐語"
              "「検収専用の値は engine_tuner_gen.py の selftest の中にだけ存在する」）。",
              "- **番人**＝この4か所のどれかに架空の数の並びを1つ 足すと、"
              "その場所の件数がちょうど 1 増えます（`--selftest` の T12・わざと壊して確かめています）。", "",
              f"**★4か所 合わせて 数の並び {a1['合計並び']} 件（数字 {a1['合計数字']} 個）。"
              f"範囲で探せるのは {a1['合計範囲']} 件だけです。**", "",
              "| # | 場所 | 何の数字か | 決まった数字だけ（数の並び） | その中の数字 | 範囲で探せる |",
              "|---|---|---|---|---|---|"]
        for p in a1["places"]:
            L.append(f"| {p['番号']} | {p['場所']} | {p['何の数字か']} | "
                     f"**{p['並び']} 件** | {p['数字']} 個 | {p['範囲']} 件 |")
        L += ["",
              "**★この欄の「範囲で探せる」は、設定ファイルそのものに 下限と上限の形で書いてある項目の数です。**",
              "2026-08-13（段A の A-4・A-5）から、**engine_tuner は 場所1 の数字を「範囲の両端」として使います**"
              "＝いちばん小さい数字と いちばん大きい数字の間なら、どの数字でも試せます"
              "（例＝RSI は 7〜21 の整数 全部。設定ファイルに並んでいるのは 7・9・14・21 の4つだけ）。"
              "範囲の正本＝`engine_tuner_gen.material_ranges`。"
              "**設定の範囲の置き場所＝`recipes/search_limits.json` の `material_param_ranges`（2026-10-06 から、修正対応表の範囲をプログラムが写したもの）。**",
              "", "**場所ごとの中身（全部 実物から）**", "",
              f"- **場所1**＝指標のパラメータ。この {a1['places'][0]['並び']} 件の並びが、"
              f"下の表の {len(e['期間'])} 種類・{sum(len(v) for v in e['期間'].values())} 通りに広がります。"
              "★数える鍵は「名前が `_periods` で終わるもの」ではなく、"
              "**材料カタログを作る関数（`observe_diag.build_catalog`）が実際に読む鍵**です"
              "（名前で数えると `bb_sigma`・`keltner`・`supertrend`・`ichimoku`・`macd_params`・"
              "`*_windows`・`sr_tol`・`w_tol` を丸ごと取りこぼします）。"
              f"観察の道具だけが使う格子 {len(a1['places'][0]['観察だけの格子'])} 件"
              f"（{'・'.join('`' + x + '`' for x in a1['places'][0]['観察だけの格子'])}）は、"
              "engine_tuner が振る値ではないので ここでは数えていません。",
              "- **場所2**＝ほかに "
              + (f"分位（閾値の段）＝**範囲 {a1['places'][1]['分位の範囲']}**（`quantile_range`・"
                 "★2026-08-15 の段A の A-5-3 で 9段のメニューから範囲にした。"
                 "`quantile_grid` の9段は ほかの道具がまだ読む分として残してある）"
                 if a1['places'][1].get('分位の範囲') else
                 f"分位の段 {a1['places'][1]['分位の段']} 段（`quantile_grid`）")
              + f"／単独の数字 {len(a1['places'][1]['単独の数字'])} 件"
              f"（{'・'.join('`' + x + '`' for x in a1['places'][1]['単独の数字'])}）／"
              f"上限を置かないもの {len(a1['places'][1]['無制限'])} 件"
              f"（{'・'.join('`' + x + '`' for x in a1['places'][1]['無制限'])}"
              "＝まこさん決定 2026-08-12）。",
              f"- **場所3**＝ほかに、案を作るときの**確率の数字**が {a1['places'][2]['確率']} か所"
              "（`rng.random() < 0.3` の形）。これは探す値ではありませんが、"
              "CC がコードに直に書いた数字なので一緒に数えています。",
              f"- **場所4**＝`search_space` は全部で {a1['places'][3]['合計']} 件です。"
              f"内訳＝分位 {a1['places'][3]['分位']} ／メニュー {a1['places'][3]['並び'] + a1['places'][3]['選択肢']}"
              f"（うち数の並び {a1['places'][3]['並び']}・本当に選択肢 {a1['places'][3]['選択肢']}）／"
              f"範囲 {a1['places'][3]['範囲']}。"
              + (f"★このうち {len(a1['places'][3]['値が空'])} 件は値が空です"
                 f"（{'・'.join('`' + x + '`' for x in a1['places'][3]['値が空'])}"
                 "＝まこさんの判断待ち・値が入るまで engine_tuner は走りません）。"
                 if a1["places"][3]["値が空"] else ""), ""]
        for p in a1["places"]:
            key = "明細"
            if not p.get(key):
                continue
            head = "| 鍵 | 決まった数字 |" if "鍵" in p[key][0] else "| 行 | 数字を選んでいる書き方 |"
            L += [f"**場所{p['番号']} の明細（{len(p[key])} 件）**", "", head, "|---|---|"]
            for r in p[key]:
                a, b = (r["鍵"], r["中身"]) if "鍵" in r else (r["行"], "`" + r["中身"] + "`")
                L.append(f"| `{a}` | {b} |")
            L.append("")
        _pk = _param_kinds(e["期間"])
        _pk1 = _param_kinds({r["鍵"]: [float(x) for x in r["中身"].split("・")]
                             for r in a1["places"][0]["明細"]})
        L += ["**★パラメータは「ローソク足の本数」だけではありません（2026-08-12 に是正）。**", "",
              "2026-08-11 まで、この節は「ここで言う数字は、ローソク足の本数です」と書いていました。",
              "**実物には本数でないものが混ざっています。**倍数（標準偏差・ATR の何倍か）・",
              "許容幅（値段の何%まで同じ水準とみなすか）・係数（減衰の強さ）です。",
              "**分けないまま A-3 を直すと、整数の範囲しか作らず、小数を扱えなくなります。**", "",
              "**★ここは正直に書きます。「本数か・倍数か」は、数字だけを見ても機械では分けられません。**",
              "位置と鍵の名前で決まるからです（例＝`keltner` の `20・2.0` は 20 が本数・2.0 が ATR の倍数）。",
              "**2.0 や 3.0 は きりのよい数なので、機械には本数と区別が付きません。**",
              "機械で分かるのは「小数が入っているかどうか」だけです。下の表がその実測です。", "",
              "| 機械で分かること | 件数 | 中身 |", "|---|---|---|",
              f"| 小数が入っている鍵 | {len(_pk1['小数'])} 件 | "
              + ("・".join("`" + x + "`" for x in _pk1["小数"]) or "—") + " |",
              f"| 整数だけの鍵 | {len(_pk1['本数'])} 件 | "
              "★この中に `bb_sigma`（標準偏差の倍数 2.0・3.0）のような"
              "「本数でない きりのよい数」が混ざります |", "",
              "**A-3 で範囲に直すときは、鍵ごとに「整数の範囲か・小数の範囲か」を1件ずつ決めます。**",
              "下の指標ごとの表でも、小数が混ざるものには「本数ではない」と付けています"
              f"（{len(_pk['小数'])} 種類）。", "",
              "**これは「パラメータ」です。「閾値」ではありません。**",
              "パラメータ＝指標を作るときの設定（RSI14 の 14＝本数）。",
              "閾値＝できあがった値の区切り（「RSI が 70 を超えたら」の 70）。"
              "**下の表に閾値は出てきません。**", "",
              f"**下の表は、上の 場所1 が広がった姿です（{len(e['期間'])} 種類）。**", "",
              "| 指標の種類 | いま試せるパラメータ |", "|---|---|"]
        for k, v in e["期間"].items():
            # ★数字が2つ以上の指標（MACD線%(12,26) のような形）は、組で1通りと数える（6-7・2026-08-11）
            if any(isinstance(x, (list, tuple)) for x in v):
                s = "・".join("(" + ",".join(str(y) for y in x) + ")" for x in v)
                L.append(f"| {k} | {s}（{len(v)} 通り・数字が2つ以上の指標は組で1通り） |")
            elif all(float(x) == int(x) for x in v):
                L.append(f"| {k} | {' 本・'.join(str(x) for x in v)} 本（{len(v)} 通り） |")
            else:
                # ★小数は本数ではない（倍数・許容幅・係数）＝「本」を付けない（2026-08-12 是正）
                L.append(f"| {k} | {'・'.join(str(x) for x in v)}（{len(v)} 通り・本数ではない） |")
        # ★★使い方（条件の形）の一覧＝2026-08-11 まこさん指示で材料の正本に入れた。
        #   逐語＝「一覧の正本は materials.md だと思うけど。そこには使い方一覧は入れないの？」
        #        「すべて自動生成にして」。だから この節は1行も手で書かず、実物から機械で引く。
        _fm = forms_table()
        L += ["", "## ★5｜使い方の一覧（条件の形）＝指標をどう条件にするか", "",
              "**★この節は機械が実物から引いて書きます（手書きゼロ）。**",
              f"形の名前と数＝`engine_tuner_exec.py` の `FORMS`（実行器が本当に実行できる形）。",
              f"何をするか・必要な値＝`{_fm['doc']}` の §2.2 の表。", "",
              "**なぜ材料の正本に入れるか。**指標の一覧だけを見て「この列が無い＝engine_tuner は作れない」と",
              "判定すると間違えます。**2026-08-11 に実際に間違えました**（RSI の差の列が無いことを理由に",
              "「作れない」と報告したが、下の `slope` で作れた）。**指標と使い方は、同じ1枚で突き合わせます。**", "",
              f"**いま実行器が実行できる形＝{_fm['n_forms']} 種類。**", "",
              "| 形 | 何をするか | 使う材料 | 必要な値 | 実例 | 入れ子 |",
              "|---|---|---|---|---|---|"]
        for r in _fm["rows"]:
            L.append(f"| `{r['形']}` | {r['和名']} | {r['材料']} | {r['必要な値']} | {r['実例']} | {r['入れ子']} |")
        if _fm["ng"]:
            L += ["", f"**❌ 実行器に在るのに説明が見つからない形が {len(_fm['ng'])} 件**"
                      f"（{'・'.join(_fm['ng'])}）＝実物と説明がずれています。"]
        else:
            L += ["", "**✅ 実行器の形すべてに説明が付いています（実物と説明のずれ 0 件）。**"]
        L += ["", "**★使い方の側にも「決まった数字だけ」の縛りがあります。**",
              "例＝`slope`（いまの値 − n本前の値）の n として engine_tuner が選べるのは、",
              "`recipes/search_limits.json` の `int_grid` に並んだ数字だけです。**ここも ★3 と同じで、",
              "マイルストーン③（範囲で探せるようにする）の対象です。**"]
        L += _render_parts(condition_parts())
        L += _render_matrix(parts_matrix())
        _ok = sum(1 for s in body["skip_rows"] if s.get("承認", "").startswith("✅"))
        _po = sum(1 for s in body["skip_rows"] if s.get("承認", "").startswith("◯"))
        _no = len(body["skip_rows"]) - _ok - _po
        L += ["", "## ★4｜入れないと判断したもの（理由つき・★承認の欄を1件ずつ出します）", "",
              f"**{len(body['skip_rows'])} 件です。**既定は「入れる」なので、ここに載るのは",
              "**指標ではないもの**と、**うちに既に同じものが在るもの**だけです。",
              "（まこさん決定＝「利益最大化するために完全に不要な指標以外はすべて入れてほしい」）", "",
              "**★印は3種類です**（まこさん OK 2026-08-10）。"
              "**まこさんが見る必要があるのは ★未承認 だけです。**", "",
              "| 印 | 意味 | 件数 |",
              "|---|---|---|",
              f"| ✅ | **まこさんが名指しで「入れない」と言われたもの**"
              f"（2026-08-09「1,2,3,4全部いれないくていい」「willrは入れない」／2026-08-10「３は入れない」） | **{_ok} 件** |",
              f"| ◯ | **まこさんが方針を承認したもの**（2026-08-09 の逐語「他にも同じ挙動の指標があれば"
              f"紛らわしいので片方を省いていく」）。★**同じ挙動かどうかの判定は CC が実測でやりました**"
              f"＝まこさんは1件ずつ見ていません | **{_po} 件** |",
              f"| ★未承認 | **上のどちらにも当たらないもの** | **{_no} 件** |", "",
              "⚠️ 2026-08-10 まで、この文書は全件を「承認済み」と書いていました（承認の偽装）。是正しました。", "",
              "| ライブラリの関数 | 承認 | 入れない理由 |", "|---|---|---|"]
        for s in body["skip_rows"]:
            L.append(f"| {s['名前']} | {s.get('承認', '★未承認')} | {s['理由']} |")
        L += [""]
    if body.get("regime_decl"):
        L += _render_regime(body["regime_decl"])
        L += [""]
    if body.get("m2_baseline"):
        L += _render_m2_baseline(body["m2_baseline"])
        L += [""]
    L += ["## 答える問いの出どころ（系統ごと・1行ずつ）", "",
          "| 系統 | 答える問い | 出典 |", "|---|---|---|"]
    for k, v in body["lineage_question"].items():
        L.append(f"| {k} | {v['問い']} | {v['出典']} |")
    cols = ("名前", "系統", "答える問い", "使える役割", "計算の出どころ",
            "グループ", "状態", "engine_tuner")
    L += ["", "## 材料の一覧", "",
          "| " + " | ".join(cols) + " |",
          "|" + "---|" * len(cols)]
    for r in body["rows"]:
        L.append("| " + " | ".join(r[k] for k in cols) + " |")
    L += ["", "## この表の作り方（正本＝ここから機械で引いています）", "",
          "| 欄 | どこから引いたか |", "|---|---|",
          "| 名前 | `indicator_reference_diag.REFS` の family（指標の種類 53 件） |",
          "| 系統 | `indicator_reference_diag.FAMILY_LINEAGE` |",
          "| 答える問い | `indicator_reference_diag.LINEAGE_QUESTION`（上の表に出典つきで出しています） |",
          "| 使える役割 | `.claude/ratchet/signal_families.json` の `role_lineage.roles`（役割ごとに使える系統） |",
          "| 計算の出どころ | `INDUSTRY_MAP`（ライブラリに同じものが在るか）＋ `REFS[ext]`・`EXT2`（照合の相手） |",
          "| グループ | 空（フロー 段8 で埋める） |",
          "| 状態 | 在る＝参照表に登録済み ／ 足す・入れない＝`pandas_ta_classic.Category` と `INDUSTRY_SKIP` |",
          "| engine_tuner | `engine_tuner_exec.FAMILY_TEMPLATES`（生成器が名前を組み立てられる指標）"
          "＋ `engine_tuner_gen.material_pool`（実際の候補）＋ `signal_families.json` の `extra_parts` |",
          "", f"（業界のライブラリの関数 {body['library_funcs']} 種類を読み込みました"
          f"{'' if body['library_ready'] else '＝★入っていないので 足す・入れない の行が出ていません'}）", ""]
    return "\n".join(L) + "\n"


def forbidden_items(req_json: dict | None = None) -> list[dict]:
    """要件の json から「作ってはいけないもの」の一覧を読み取る（★CC が写さない）。

    形＝`| 番号 | 文 | いつ・なぜ足したか |` の表の行。まこさんが3番を足せば、自動で3番が現れる。
    引数は番人（F1）が架空の番号を混ぜるためだけに在る。既定は実物から読む。
    """
    d = json.loads(_FB_REQ_JSON.read_text(encoding="utf-8")) if req_json is None else req_json
    out: list[dict] = []
    for s in d.get("purpose_reading", []):
        if not isinstance(s, str) or "作ってはいけないもの" not in s:
            continue
        for line in s.split("\n"):
            line = line.strip()
            if not line.startswith("|"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 2 or not cells[0].isdigit():
                continue          # 見出しの行と区切りの行はここで落ちる
            out.append({"番号": cells[0], "文": cells[1]})
    return out


def _fb_dotted(f) -> list[str]:
    """呼び出しの名前を点で分けた並びにする（np.random.default_rng → [np, random, default_rng]）。"""
    parts: list[str] = []
    while isinstance(f, ast.Attribute):
        parts.append(f.attr)
        f = f.value
    parts.append(f.id if isinstance(f, ast.Name) else "?")
    return list(reversed(parts))


def _fb_enclosing(node, parent: dict) -> str:
    """その呼び出しを囲んでいる関数の名前。"""
    while node in parent:
        node = parent[node]
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return node.name
    return "(モジュール直下)"


def count_random_draws(src: str | None = None) -> dict:
    """案を作るプログラムの中の乱数の呼び出しを、構文木で数える（1番の材料）。

    数え方＝呼び出しの名前を点でつないだ全体にして、
      ・最後の名前が「引く操作」の一覧（_FB_DRAW_METHODS）に在る、または
      ・途中に `random` が在る（np.random.… の形）
    のどちらかなら 1 件。
    ★引数は番人（F2）が写しに1件 足すためだけに在る。既定は実物から読む。
    """
    src = _A1_GEN.read_text(encoding="utf-8") if src is None else src
    tree = ast.parse(src)
    parent: dict = {}
    for n in ast.walk(tree):
        for ch in ast.iter_child_nodes(n):
            parent[ch] = n
    per: dict[str, int] = {}
    total = 0
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
            continue
        segs = _fb_dotted(n.func)
        if "random" in segs[:-1] or segs[-1] in _FB_DRAW_METHODS:
            total += 1
            k = _fb_enclosing(n, parent)
            per[k] = per.get(k, 0) + 1
    return {"合計": total, "内訳": sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))}


def count_law_reads(src: str | None = None) -> dict:
    """法則の表を読む呼び出しを、構文木で数える（1番の白黒の材料）。

    ★乱数だけで条件をつないでいるなら、承認済みの型の表も 場面の決まりも 範囲の表も読まない。
    だから「乱数が在る」だけでは白黒が付かず、「法則の表を1つも読まない」で初めて当たると言える。
    """
    src = _A1_GEN.read_text(encoding="utf-8") if src is None else src
    tree = ast.parse(src)
    per: dict[str, int] = {}
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in _FB_LAW_FUNCS:
            per[n.func.id] = per.get(n.func.id, 0) + 1
    return {"合計": sum(per.values()), "内訳": sorted(per.items(), key=lambda kv: (-kv[1], kv[0]))}


def _fb_outside_range() -> tuple[int | None, str]:
    """範囲から引く処理を通さずに材料を作っている所の件数（2番の材料その2）。

    ★関数の名前を決め打ちしない。engine_tuner_gen が自分で持っている検査を呼ぶ。
      理由＝59回目に 78番を直したとき、間に2つ 処理をはさむ形になった。
      名前を決め打ちすると、直っているのに「当たっています」と出る（設計書 §1.5）。
    戻り＝(件数, 理由)。読み込めなければ (None, 理由)＝表に「測れませんでした」と出す。
    """
    import contextlib
    import io
    try:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            import engine_tuner_gen as _g               # noqa: PLC0415
            rc = _g.lint_provenance(verbose=False)
        return (0 if rc == 0 else 1), ""
    except Exception as e:                              # noqa: BLE001
        return None, f"{type(e).__name__}: {str(e)[:60]}"


def forbidden_verdict(no: str, m: dict) -> str:
    """実物を数えた数字から、答えの文字列を決める（設計書 §3.2）。

    ★返すのは _FB_VERDICTS の4つだけ。CC が文章で上書きできる欄はここに無い。
    """
    if no == "1":
        if m.get("乱数", 0) == 0:
            return _FB_MISS
        return _FB_HIT if m.get("法則", 0) == 0 else _FB_SUSPECT
    if no == "2":
        if m.get("数の並び", 0) > 0 or m.get("範囲を通さない", 0) > 0:
            return _FB_HIT
        return _FB_MISS
    return _FB_TBD


def forbidden_block(req_json: dict | None = None, gen_src: str | None = None) -> str:
    """差し込む固まり（印つき）を作る。★引数は番人が写しを渡すためだけに在る。"""
    items = forbidden_items(req_json)
    rnd = count_random_draws(gen_src)
    law = count_law_reads(gen_src)
    fx = fixed_number_places()
    out_n, out_why = _fb_outside_range()
    m = {"乱数": rnd["合計"], "法則": law["合計"],
         "数の並び": fx["合計並び"], "範囲を通さない": (out_n or 0)}

    rnd_top = "／".join(f"{k} {v}" for k, v in rnd["内訳"][:6])
    law_top = "／".join(f"{k} {v}" for k, v in law["内訳"][:6])
    places = "／".join(f"場所{p['番号']} {p['並び']}" for p in fx["places"])
    outside = (f"{out_n}件（{'合格' if out_n == 0 else '不合格'}）" if out_n is not None
               else f"測れませんでした（{out_why}）")
    facts = {
        "1": (f"乱数の呼び出し **{rnd['合計']}件**（{rnd_top}）"
              f"・法則の表を読む所 **{law['合計']}件**（{law_top}）"),
        "2": (f"決まった数字だけの一覧 **{fx['合計並び']}件**（{places}）"
              f"・範囲を通さずに作っている所 **{outside}**"),
    }
    L = ["| # | 作ってはいけないもの | 実物を数えた結果 | 答え |", "|---|---|---|---|"]
    for it in items:
        no = it["番号"]
        L.append(f"| {no} | {it['文']} | {facts.get(no, '（この番号の測り方はまだ在りません）')}"
                 f" | **{forbidden_verdict(no, m)}** |")
    L += [
        "",
        "> **この表は `gen_materials.py` が実物を数えて作ります。手で書き換えると `--verify` が落ちます。**",
        "> 一覧そのものも `.claude/ratchet/engine_tuner_requirements.json` からの複写です（CC が写しません）。",
        "> **数え方**＝乱数の呼び出し（`engine_tuner_gen.py` の構文木）／法則の表を読む呼び出し／"
        "決まった数字だけの一覧（4か所）／範囲を通さずに作っている所（`engine_tuner_gen.lint_provenance`）。",
        "> **限界**＝1番は白黒が付かない場合があります。乱数が「案の骨格を決めている」のか"
        "「同じ点数のときの並び順を決めている」のかは、構文木では分けられません。**白黒は まこさんが付けます。**",
    ]
    body = "\n".join(L)
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return _FB_START.format(h=h) + "\n" + body + "\n" + _FB_END


def milestone_rows(paths=None) -> list[dict]:
    """やることリストの表の行を機械で拾う。

    ★見出しの行と「完全に一致」する表だけを見る。
      理由＝本文に「確かめ方＝…」と書いてある行を見出しと取り違えると、そこで表が切れる
      （2026-08-26 に実際に起き、34行しか数えられなかった＝worklog §49）。
    戻り: [{"file": 名前, "id": 行の番号, "todo": やること, "check": 確かめ方の欄}, ...]
    """
    out = []
    for p, _why in (paths or _FB_TARGETS):
        if not p.exists():
            continue
        idx = None
        for ln in p.read_text(encoding="utf-8").splitlines():
            s = ln.strip()
            if not s.startswith("|"):
                idx = None
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            if [re.sub(r"\*+", "", c).strip() for c in cells] == _RA_HEAD:
                idx = _RA_HEAD.index("出るもの・確かめ方")
                continue
            if set(s) <= set("|-: "):
                continue
            if idx is None or len(cells) <= idx:
                continue
            out.append({"file": p.name,
                        "id": re.sub(r"\*+", "", cells[0]).strip(),
                        "todo": re.sub(r"\*+", "", cells[1]).strip(),
                        "check": cells[idx],
                        # ★状態の欄（2026-08-26・B-5）＝✅済 かどうかと、その根拠の指し先を見るため
                        "state": cells[_RA_HEAD.index("状態")] if len(cells) > 4 else ""})
    return out


def req_state_rows(rows=None, mp=None, idx=None) -> list[dict]:
    """要件17件について、機械で数えた実測を作る（★CC が打つ数字は1つも無い・2026-08-26・B-5）。

    戻り: [{"id","title","state","n","done","gap"}, ...]
      state ＝ CC が手書きした 完了／作業中（そのまま出す）
      n     ＝ その要件に効くやることリストの行の数（機械が数える）
      done  ＝ そのうち ✅済 の数（機械が数える）
      gap   ＝ state が「完了」なのに done < n（機械が判定する）
    ★n == done でも「要件を満たした」とは限らない（要件は やることリスト以外の作業でも満たせる）。
      だから gap は「ずれ」であって「未達」ではない。判定は まこさん。
    """
    rows = milestone_rows() if rows is None else rows
    mp = _req_map() if mp is None else mp
    idx = _req_index() if idx is None else idx
    done_by_id = {r["id"]: ("✅済" in str(r.get("state", ""))) for r in rows}
    out = []
    for rid, meta in idx.items():
        ids = [k for k, v in mp.items() if rid in (v.get("req") or [])]
        n = len(ids)
        d = sum(1 for k in ids if done_by_id.get(k))
        st = str(meta.get("state", ""))
        out.append({"id": rid, "title": meta.get("title", ""), "state": st,
                    "n": n, "done": d, "gap": (st == "完了" and n > 0 and d < n)})
    return out


def req_progress_problems(idx=None) -> list[str]:
    """progress に「達成度の数字」が在れば止める（★日付は止めない・2026-08-26・B-5）。

    なぜ＝その数字は走らせた出力ではなく CC が打ったもの。
    まこさんの逐語（2026-08-23）＝「✅済 の根拠を、走らせた出力に限る（手で打った数字を弾く）」。
    """
    idx = _req_index() if idx is None else idx
    ng = []
    for rid, meta in idx.items():
        m = _ACH_NUM.search(str(meta.get("progress", "")))
        if m:
            ng.append(f"要件 {rid}: progress に手で打った達成度の数字が在る（『{m.group(0)}』）"
                      "＝機械が出す欄に任せる（日付や説明はそのままでよい）")
    return ng


def unevidenced_done(rows=None) -> list[str]:
    """✅済 なのに、走らせた記録の指し先（§NN / worklog）が無い行（★止めない・見せるだけ）。"""
    rows = milestone_rows() if rows is None else rows
    return [r["id"] for r in rows
            if "✅済" in str(r.get("state", "")) and not _EVIDENCE.search(str(r.get("state", "")))]


def _req_index(path=_RA_REQ_JSON) -> dict:
    """要件の正本から {番号: {title, accept, state}} を作る（★複写・縮めない）。"""
    try:
        j = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {r["id"]: {"title": r.get("title", ""), "accept": r.get("accept", ""),
                      "state": r.get("state", ""), "progress": r.get("progress", "")}
            for r in j.get("requirements", [])}


def _req_map(path=_REQ_MAP) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("map", {})
    except Exception:
        return {}


def req_accept_problems(rows=None, mp=None, idx=None) -> list[str]:
    """止める条件（4つのうち、対応表そのものを見る3つ）。1件でも在れば --verify が落ちる。"""
    rows = milestone_rows() if rows is None else rows
    mp = _req_map() if mp is None else mp
    idx = _req_index() if idx is None else idx
    ng = []
    for r in rows:
        if r["id"] not in mp:
            ng.append(f"やることリストの行 {r['id']}（{r['file']}）が対応表 milestone_req_map.json に無い")
    for k, v in mp.items():
        if not str(v.get("basis", "")).strip():
            ng.append(f"対応表 {k}: basis（なぜその要件かの1行）が空")
        for rid in v.get("req", []):
            if rid not in idx:
                ng.append(f"対応表 {k}: 要件の番号 {rid} が要件の正本に無い")
    return ng


def req_accept_block(rows=None, mp=None, idx=None) -> str:
    """差し込む固まり（印つき）を作る。★4列とも実物からの複写＝CC が文を書く欄は無い。"""
    rows = milestone_rows() if rows is None else rows
    mp = _req_map() if mp is None else mp
    idx = _req_index() if idx is None else idx
    n_empty = sum(1 for r in rows if not (mp.get(r["id"], {}).get("req") or []))
    # ★B-5（2026-08-26）＝要件ごとの実測を、この差し込みの先頭に置く。新しい印も文書も作らない。
    st = req_state_rows(rows, mp, idx)
    n_gap = sum(1 for s in st if s["gap"])
    unev = unevidenced_done(rows)
    L = [
        "## ① 要件17件の実測（機械が数えた数字と、CC が手書きした宣言を並べます）",
        "",
        f"- **CC の宣言と、機械が見える数字がずれている要件＝{n_gap} 件**"
        "（`state` が『完了』なのに、効くやることリストの行が全部 `✅済` になっていない）",
        f"- **`✅済` なのに、走らせた記録の指し先（`§NN`）が無い行＝{len(unev)} 件**",
        "",
        "> **★『効く行が全部 `✅済`』＝『要件を満たした』ではありません。**"
        "要件は やることリストに載っていない作業でも満たせます。**判定は まこさんがします。**",
        "> **★`progress` に「N項目のうち」のような達成度の数字は書けません**"
        "（`--verify` が落ちます）。その数字は走らせた出力ではなく CC が打ったものだからです。",
        "",
        "| 要件 | 題 | CC が書いた `state` | 効く行 | うち `✅済` | ずれ |",
        "|---|---|---|---|---|---|",
    ]
    for s in st:
        L.append(f"| {s['id']} | {str(s['title']).replace('|', chr(92) + '|')}"
                 f" | {s['state']} | {s['n']} | {s['done']} | {'**★ずれ**' if s['gap'] else '—'} |")
    if unev:
        L += ["",
              f"**`✅済` なのに走らせた記録の指し先が無い行（{len(unev)} 件）**＝"
              + "・".join(unev),
              "> **★この設計では止めません。**いま在る分を見えるようにするところまでです。"]
    L += [
        "",
        "## ② やることリストの行 × 要件の逐語",
        "",
        f"**やることリストの行 {len(rows)} 件を、要件の逐語と並べた表です。**",
        "",
        f"- **どの要件も指していない行＝{n_empty} 件**"
        "（要件17件のどれにも直接は効かない行。理由は『なぜその要件か』の欄に書いてあります）",
        "- **要件の欄と『なぜその要件か』の欄は、対応表 `milestone_req_map.json` からの複写です**"
        "（どの要件に効くかを選ぶのは作る側の判断＝まこさんの承認をもらいます）。",
        "- **『要件の逐語』の欄は `engine_tuner_requirements.json` の `accept` の全文です**"
        "（★縮めません。何をもって満たしたと言うかは要件の側が持ちます）。",
        "- **『いま確かめ方の欄に書いてあること』は、やることリストの表の4列目そのままです。**",
        "",
        "| 行 | 要件 | 要件の逐語（何ができたら満たしたと言えるか） | いま確かめ方の欄に書いてあること | なぜその要件か |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        v = mp.get(r["id"], {})
        ids = v.get("req") or []
        if ids:
            req_cell = "・".join(ids)
            acc = "<br>".join(f"**{i}**（{idx[i]['title']}）: {idx[i]['accept']}"
                              for i in ids if i in idx)
        else:
            req_cell = "**★無し**"
            acc = "**（どの要件も指していません）**"
        cell = lambda s: str(s).replace("|", "\\|")          # noqa: E731
        L.append(f"| {cell(r['id'])} | {cell(req_cell)} | {cell(acc)}"
                 f" | {cell(r['check'])} | {cell(v.get('basis', ''))} |")
    L += [
        "",
        "> **この表は `gen_materials.py` が実物から作ります。手で書き換えると `--verify` が落ちます。**",
        "> **`--verify` が落ちる条件4つ**＝①やることリストの行が対応表に無い ②対応表の要件の番号が正本に無い"
        " ③『なぜその要件か』が空 ④差し込んだ逐語が要件の正本と1文字でも違う。",
        "> **★入っていないもの**＝「確かめ方が要件を満たしているか」の判定は、この表には在りません。"
        "**並べて出すまでです。判定は まこさんがします**"
        "（出どころ＝`session_worklog_20260823.md` の §39.6 の段D）。",
    ]
    body = "\n".join(L)
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return _RA_START.format(h=h) + "\n" + body + "\n" + _RA_END


def _ra_splice(text: str, blk: str) -> tuple[str, bool]:
    """REQ_ACCEPT_START〜END を差し替える。印が無ければ差し込まない（False）。"""
    mt = _RA_START_RE.search(text)
    if not mt or _RA_END not in text[mt.end():]:
        return text, False
    e = text.index(_RA_END, mt.end()) + len(_RA_END)
    return text[:mt.start()] + blk + text[e:], True


def _fb_splice(text: str, blk: str) -> tuple[str, bool]:
    """FORBIDDEN_CHECK_START〜END を差し替える。印が無ければ差し込まない（False）。"""
    mt = _FB_START_RE.search(text)
    if not mt or _FB_END not in text[mt.end():]:
        return text, False
    e = text.index(_FB_END, mt.end()) + len(_FB_END)
    return text[:mt.start()] + blk + text[e:], True


# ══ 向きを持たない部品の件数を、知識の正本へ書き出す（2026-09-05・監査 cp21 の C1）═══════
#   ★なぜ機械にしたか＝CC が手で「126件」と書いた15分後に型の表を作り直したら実物は 148件になり、
#     文書だけが古いまま残った（監査 cp21 が実測）。手で数字を書ける場所を残す限り、同じことが起きる。
_BANS_START = "<!-- BANS_COUNT_START gen_materials.py --write が型の表から書き出す＝手で書き換えない -->"
_BANS_END = "<!-- BANS_COUNT_END -->"
_BANS_TARGET = _HERE.parent.parent / ".claude" / "memory" / "regime_detection_kb.md"
# ★2026-09-06（再監査 cp22 の N-3）＝KB §12-5 の表の 5〜8番も機械が書き出す。
_COUNTS_START = "<!-- COUNTS_START gen_materials.py --write が実物から書き出す＝手で書き換えない -->"
_COUNTS_END = "<!-- COUNTS_END -->"


def bans_count_block(kind: str = "bans") -> str:
    """KB に差し込む「機械が数えた件数」の文を作る（CC は数字を書かない）。

    kind="bans"  ＝ 向きを持たない部品の件数（型の表の bans から数える）
    kind="counts" ＝ ★2026-09-06（再監査 cp22 の N-3）に足した。
      KB §12-5 の表の 5〜8番（指標の種類・材料の一覧の行・部品の件数・膨らむ理由）。
      **なぜ足したか**＝この4つは手書きで、この工事で古くなった（監査が実測＝
      種類 256→実際は選べる140／材料 261→263／部品 551→573）。
      cp21 の P1 が「手で数字を書ける場所を残す限り、注意では止まらない」と診断したのに、
      P1 の対策を入れた**同じファイルの10行 下**で同じ事故が起きていた。
    """
    t = json.loads((_RATCHET / "signal_families.json").read_text(encoding="utf-8"))
    if kind == "bans":
        st = list((t.get("bans") or {}).get("direction_stateful", {}).get("parts") or [])
        nt = list((t.get("bans") or {}).get("direction_note", {}).get("parts") or [])
        ov = len(set(st) & set(nt))
        total = len(st) + len(nt) - ov
        return (f"{_BANS_START}\n"
                f"5. 逆に、仕分けで消えるものは在る＝向きを持たない部品**{total}件**（型の表の bans）は"
                f"「向き」の物差しには使えない。内訳は `direction_stateful`（状態量・ボラ量）**{len(st)}件**"
                f" ＋ `direction_note`（カタログ注記）**{len(nt)}件**、重なり **{ov}件**。\n"
                f"{_BANS_END}")
    b = build_body()
    ev = _engine_view()
    sel = len(ev["selectable_fams"])
    unsel = len(ev["unselectable_fams"])
    parts = len(t.get("parts") or [])
    extra = sum(len((v or {}).get("parts") or []) for v in (t.get("extra_parts") or {}).values())
    return (f"{_COUNTS_START}\n"
            f"| 5 | 指標の種類 | **{sel + unsel}種類**"
            f"（engine_tuner が選べる **{sel}**／選べない **{unsel}**） |"
            f" materials.md の「engine_tuner が選べる指標の種類」の行 |\n"
            f"| 6 | 材料の一覧の行 | **{b['counts']['在る']}件**（在る。ほかに「入れない」"
            f"{b['counts']['入れない']}件） | materials.md の一覧 |\n"
            f"| 7 | パラメータまで展開した部品 | **{parts}件**（＋別枠 {extra}件＝**{parts + extra}**） |"
            f" signal_families.json の parts と extra_parts |\n"
            f"| 8 | ★{parts + extra} に膨らむ理由 | ADX7・ADX14・ADX21 のように、"
            f"同じ指標のパラメータ違いを別々に数えているため | 部品の名前の実測 |\n"
            f"{_COUNTS_END}")


def _bans_splice(text: str, blk: str, start: str = "", end: str = "") -> tuple[str, bool]:
    """印の START〜END を差し替える。印が無ければ差し込まない（False）。

    ★2026-09-06（再監査 cp22 の N-3）＝印を引数で受けられるようにした（既定は BANS）。
    """
    start = start or _BANS_START
    end = end or _BANS_END
    if start not in text or end not in text:
        return text, False
    s = text.index(start)
    e = text.index(end, s) + len(end)
    return text[:s] + blk + text[e:], True


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
    # ★節の中に ❌ が残っていたら、作った直後にここでも出す（2026-08-13・まこさん指示）。
    #   書き出しは止めない（❌ は文書に出すためのもの）。落とすのは --selftest の T11。
    _sng = section_ng()
    if _sng:
        print(f"  ❌ 節の中に ❌ が {len(_sng)} 件 残っています（--selftest の T11 が落ちます）")
        for _x in _sng[:5]:
            print(f"     - {_x[:140]}")
    # ★「作ってはいけないものとの照合」の差し込み（2026-08-26・64回目）
    blk = forbidden_block()
    for p, _why in _FB_TARGETS:
        if not p.exists():
            print(f"  ⚠️ [未差し込み] {p.name}: ファイルが無い")
            continue
        t = p.read_text(encoding="utf-8")
        new, ok = _fb_splice(t, blk)
        if not ok:
            print(f"  ⚠️ [未差し込み] {p.name}: FORBIDDEN_CHECK_START/END の印が無い（先に印を置く）")
            continue
        if new != t:
            p.write_text(new, encoding="utf-8")
            print(f"  [差し込み] {p.name}（作ってはいけないものとの照合）")
        else:
            print(f"  [変更なし] {p.name}（作ってはいけないものとの照合）")
    # ★向きを持たない部品の件数を、知識の正本へ書き出す（2026-09-05・監査 cp21 の C1）
    if not _BANS_TARGET.exists():
        print(f"  ⚠️ [未差し込み] {_BANS_TARGET.name}: ファイルが無い")
    else:
        _bt = _BANS_TARGET.read_text(encoding="utf-8")
        _bn, _bok = _bans_splice(_bt, bans_count_block())
        if not _bok:
            print(f"  ⚠️ [未差し込み] {_BANS_TARGET.name}: BANS_COUNT_START/END の印が無い（先に印を置く）")
        elif _bn != _bt:
            _BANS_TARGET.write_text(_bn, encoding="utf-8")
            print(f"  [差し込み] {_BANS_TARGET.name}（向きを持たない部品の件数）")
        else:
            print(f"  [変更なし] {_BANS_TARGET.name}（向きを持たない部品の件数）")
        # ★KB §12-5 の表の 5〜8番も書き出す（2026-09-06・再監査 cp22 の N-3）
        _ct = _BANS_TARGET.read_text(encoding="utf-8")
        _cn, _cok = _bans_splice(_ct, bans_count_block("counts"), _COUNTS_START, _COUNTS_END)
        if not _cok:
            print(f"  ⚠️ [未差し込み] {_BANS_TARGET.name}: COUNTS_START/END の印が無い（先に印を置く）")
        elif _cn != _ct:
            _BANS_TARGET.write_text(_cn, encoding="utf-8")
            print(f"  [差し込み] {_BANS_TARGET.name}（指標の種類・材料の行・部品の件数）")
        else:
            print(f"  [変更なし] {_BANS_TARGET.name}（指標の種類・材料の行・部品の件数）")
    # ★「やることリストの確かめ方 × 要件の逐語」の差し込み（2026-08-26・B-4）
    _ra_ng = req_accept_problems()
    if _ra_ng:
        print(f"  ❌ 要件との対応に {len(_ra_ng)} 件の不足（--verify が落ちます）")
        for _x in _ra_ng[:5]:
            print(f"     - {_x}")
    rblk = req_accept_block()
    for p, _why in _FB_TARGETS:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        new, ok = _ra_splice(t, rblk)
        if not ok:
            print(f"  ⚠️ [未差し込み] {p.name}: REQ_ACCEPT_START/END の印が無い（先に印を置く）")
            continue
        if new != t:
            p.write_text(new, encoding="utf-8")
            print(f"  [差し込み] {p.name}（やることリストの確かめ方 × 要件の逐語）")
        else:
            print(f"  [変更なし] {p.name}（やることリストの確かめ方 × 要件の逐語）")
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
    # ★「作ってはいけないものとの照合」の差し込みが、実物と一致するか（2026-08-26・64回目）
    blk = forbidden_block()
    for p, _why in _FB_TARGETS:
        if not p.exists():
            ng.append(f"{p.name}: ファイルが無い（作ってはいけないものとの照合の差し込み先）")
            continue
        t = p.read_text(encoding="utf-8")
        mt = _FB_START_RE.search(t)
        if not mt or _FB_END not in t[mt.end():]:
            ng.append(f"{p.name}: FORBIDDEN_CHECK_START/END の印が無い")
            continue
        cur = t[mt.start():t.index(_FB_END, mt.end()) + len(_FB_END)]
        if cur != blk:
            ng.append(f"{p.name}: 作ってはいけないものとの照合の差し込みが実物と食い違う"
                      "（手で書き換えたか、元が変わったのに作り直していない）")
    # ★向きを持たない部品の件数（2026-09-05・監査 cp21 の C1）＝手で書き換えたか、
    #   型の表が変わったのに書き直していないかを、両方 検出する
    if not _BANS_TARGET.exists():
        ng.append(f"{_BANS_TARGET.name}: ファイルが無い（向きを持たない部品の件数の差し込み先）")
    else:
        _bt = _BANS_TARGET.read_text(encoding="utf-8")
        if _BANS_START not in _bt or _BANS_END not in _bt:
            ng.append(f"{_BANS_TARGET.name}: BANS_COUNT_START/END の印が無い")
        else:
            _s = _bt.index(_BANS_START)
            _cur = _bt[_s:_bt.index(_BANS_END, _s) + len(_BANS_END)]
            if _cur != bans_count_block():
                ng.append(f"{_BANS_TARGET.name}: 向きを持たない部品の件数が型の表と食い違う"
                          "（手で書き換えたか、型の表が変わったのに作り直していない）")
        # ★KB §12-5 の表の 5〜8番（2026-09-06・再監査 cp22 の N-3）
        if _COUNTS_START not in _bt or _COUNTS_END not in _bt:
            ng.append(f"{_BANS_TARGET.name}: COUNTS_START/END の印が無い")
        else:
            _s2 = _bt.index(_COUNTS_START)
            _cur2 = _bt[_s2:_bt.index(_COUNTS_END, _s2) + len(_COUNTS_END)]
            if _cur2 != bans_count_block("counts"):
                ng.append(f"{_BANS_TARGET.name}: 指標の種類・材料の行・部品の件数が実物と食い違う"
                          "（手で書き換えたか、実物が変わったのに作り直していない）")
    # ★「やることリストの確かめ方 × 要件の逐語」（2026-08-26・B-4）＝止める条件4つ
    ng += req_accept_problems()                       # ①行が対応表に無い ②番号が正本に無い ③basis が空
    ng += req_progress_problems()                     # ★B-5＝progress に手で打った達成度の数字が在る
    rblk = req_accept_block()
    for p, _why in _FB_TARGETS:
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        mt = _RA_START_RE.search(t)
        if not mt or _RA_END not in t[mt.end():]:
            ng.append(f"{p.name}: REQ_ACCEPT_START/END の印が無い")
            continue
        cur = t[mt.start():t.index(_RA_END, mt.end()) + len(_RA_END)]
        if cur != rblk:                               # ④差し込んだ逐語が正本と1文字でも違う
            ng.append(f"{p.name}: やることリストの確かめ方 × 要件の逐語 の差し込みが実物と食い違う"
                      "（手で書き換えたか、元が変わったのに作り直していない）")
    return ng


def selftest() -> int:
    ng: list[str] = []
    # ★2026-09-06（監査 cp23 の X-5・設計書 iter="cp23-selftest-audit-req-20260906"）
    #   ＝当てる相手が1件も無くて飛ばした番人の名前を、ここに集める。
    #   直す前は画面に出すだけで、合否の数にも出力にも残らなかった＝「✅ 全部 pass」が
    #   「番人を全部 当てた」を意味しない状態だった（このファイルの :988・:2411 が禁じている状態）。
    skipped: list[str] = []
    body = build_body()
    rows = body["rows"]
    # T1 在るの行数＝4つの定義表の件数の合計と一致する（1つでも取りこぼしたら落ちる）
    want_n = (len(iref.REFS) + len(iref.DEMAND_REF) + len(getattr(iref, "TIME_REF", {}))
              + len(iref.RANGE_GEO_REF))
    # ★「省いた（同じ挙動）」の行も定義表の側では数える（2026-08-11・まこさん OK で省いたため）
    _kept_or_dropped = body["counts"]["在る"] + sum(
        1 for r in rows if str(r["状態"]).startswith("省いた"))
    if _kept_or_dropped != want_n:
        ng.append(f"T1: 『在る』＋『省いた』の行数 {_kept_or_dropped} が定義表の合計 {want_n} 件と合わない"
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
    # ★「省いた（同じ挙動）」の行も、定義表には在る＝名前の突き合わせでは同じ側に数える
    #   （2026-08-11・まこさん OK で同じ挙動の列を省いたため）。
    got_names = {r["名前"] for r in rows if r["状態"] == "在る" or r["状態"].startswith("省いた")}
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
    # ── 段5（2026-08-09 追加）の番人 ──
    # T7 engine_tuner の欄が全行に在り、「在る」の行に判定不能が混ざっていない
    for r in rows:
        if not r.get("engine_tuner"):
            ng.append(f"T7: 『{r['名前']}』に engine_tuner の欄が無い")
        elif r["状態"] == "在る" and r["engine_tuner"] == _SEL_NA:
            ng.append(f"T7: 『{r['名前']}』は材料に在るのに engine_tuner の欄が『まだ入っていない』")
    # T8 足すものの一覧の数が、いま材料の一覧に出ている「足す」の件数と一致する（表と一覧の食い違い防止）
    ga = {g["印"]: g for g in body.get("gaps", [])}
    if ga and ga["A"]["数"] != body["counts"]["足す"]:
        ng.append(f"T8: 足すものの一覧 A の {ga['A']['数']} が、材料の一覧の『足す』{body['counts']['足す']} 件と合わない")
    # T8-2 「選べない指標の種類」の数が、一覧 B の数と一致する
    if ga and ga["B"]["数"] != body["engine"]["選べない指標の種類"]:
        ng.append("T8-2: 一覧 B の数が engine_tuner の集計と合わない")
    # T10 段6 の前に「在る」だった指標が、いま1件も消えていない（2026-08-11・段6 の 6-9②）
    #   ★何を守るか＝業界のライブラリの指標を大量に足す作業（段6）の途中で、うちが元から持っていた
    #     指標（cat 独自のもの＝外部に照合の相手がいないものを含む）を うっかり消していないこと。
    #     一覧は git から取り出す＝記憶や書き写しではない。
    _lost, _base_n = _kept_since_stage6()
    if _lost:
        ng.append(f"T10: 段6 の前に在った指標が消えている（{len(_lost)}/{_base_n} 件）: {'・'.join(_lost)}")
    # T9 わざと FAMILY_TEMPLATES から1件 消すと「選べない」が1件 増える（この検査が生きていることの確認）
    try:
        import engine_tuner_exec as _ex
        _keep = dict(_ex.FAMILY_TEMPLATES)
        _base = len(_engine_view()["unselectable_fams"])
        _ex.FAMILY_TEMPLATES.pop("RSI", None)
        _cut = len(_engine_view()["unselectable_fams"])
        if _cut != _base + 1:
            ng.append(f"T9: FAMILY_TEMPLATES から1件 消しても『選べない』が増えない（{_base} → {_cut}）")
    except Exception as _e:                                      # noqa: BLE001
        ng.append(f"T9: 実行器を読み込めないので『選べるか』の検査を確かめられない（{str(_e)[:60]}）")
    finally:
        try:
            _ex.FAMILY_TEMPLATES.clear()
            _ex.FAMILY_TEMPLATES.update(_keep)
        except Exception:                                        # noqa: BLE001
            pass
    # ── T11 節の中の ❌ を、番人が見ているか（2026-08-13 新設・まこさん指示）──────────────
    #   何を守るか＝materials.md の中に「❌ N 件」と印字されているのに、--selftest が
    #   「✅ 全部 pass」と出す状態を作らない。2026-08-13 にそれが実際に起きた。
    #   ★見つけたのは番人ではなく、人が文書を開いたとき。だから番人の側に足す。
    _sng = section_ng()
    if _sng:
        ng.append(f"T11: materials.md の節の中に ❌ が {len(_sng)} 件 残っている"
                  f"（1件目＝{_sng[0][:100]}）")
    # T11 メタ確認＝わざと節の判定を壊すと、上の集め方が拾うか（拾わなければ T11 は飾り）
    try:
        import engine_tuner_exec as _ex11

        def _boom(*_a, **_k):
            raise _ex11.RecipeError("T11 メタ確認：わざと壊した")
        _keep11 = _ex11._check_cond
        _ex11._check_cond = _boom
        try:
            if not section_ng():
                ng.append("T11 メタ確認: 節の判定をわざと壊しても ❌ が1件も出ない"
                          "（節の ❌ を集める処理が効いていない）")
        finally:
            _ex11._check_cond = _keep11
    except Exception as _e11:                                    # noqa: BLE001
        ng.append(f"T11 メタ確認: 確かめられなかった（{type(_e11).__name__}: {str(_e11)[:60]}）")

    # ── T12 A-1｜「決まった数字だけ」の4か所の数え上げ（2026-08-12 新設・段A の A-1）─────────
    #   何を守るか＝4か所のどれかに新しい「数の並び」が増えたのに、★3 の表が気づかない状態を作らない。
    #   確かめ方＝架空の数の並びを1つ 足すと、その場所の件数がちょうど 1 増えること（4か所とも）。
    #   ★実物のファイルは1バイトも書き換えない（読み込んだ中身の写しに混ぜるだけ）。
    try:
        _b12 = fixed_number_places()
        _cfg12 = json.loads(_A1_CFG.read_text(encoding="utf-8"))
        _lim12 = json.loads(_A1_LIM.read_text(encoding="utf-8"))
        _src12 = _A1_GEN.read_text(encoding="utf-8")
        _e3812 = json.loads(_A1_E38.read_text(encoding="utf-8"))
        _cfg12["zzz_uso_periods"] = [11, 13, 17]
        _lim12["zzz_uso_grid"] = [11, 13, 17]
        _src12 += "\n_zzz_uso = rng.choice([11, 13, 17])\n"
        (_e3812.get("search_space") or {})["zzz_uso"] = {"type": "cat", "choices": [11, 13, 17]}
        # ★場所1 は「設定に鍵が在る」だけでは数えない（材料カタログを作る関数が読む鍵だけを数える）。
        #   だから番人も、設定の鍵と、それを読む行の両方を足す＝実物と同じ形で1件 増やす。
        _od12 = _A1_OD.read_text(encoding="utf-8")
        _od12 = _od12.replace("def build_catalog(cfg: dict) -> list[tuple]:\n",
                              "def build_catalog(cfg: dict) -> list[tuple]:\n"
                              '    _zzz_uso = cfg["zzz_uso_periods"]\n', 1)
        _cases = [("1", dict(cfg=_cfg12, od_src=_od12)), ("2", dict(lim=_lim12)),
                  ("3", dict(gen_src=_src12)), ("4", dict(e38=_e3812))]
        for _no, _kw in _cases:
            _got = fixed_number_places(**_kw)
            _i = [p["番号"] for p in _b12["places"]].index(_no)
            _was = _b12["places"][_i]["並び"]
            _now = _got["places"][_i]["並び"]
            if _now != _was + 1:
                ng.append(f"T12: 場所{_no} に架空の数の並びを1つ 足しても件数が1 増えない"
                          f"（{_was} → {_now}）＝A-1 の数え上げがその場所を見ていない")
            # 足した1件のぶん以外が動いていないこと（別の場所を巻き込んでいない）
            for _j, _p in enumerate(_got["places"]):
                if _j != _i and _p["並び"] != _b12["places"][_j]["並び"]:
                    ng.append(f"T12: 場所{_no} を触ったのに 場所{_p['番号']} の件数まで動いた"
                              f"（{_b12['places'][_j]['並び']} → {_p['並び']}）")
    except Exception as _e12:                                    # noqa: BLE001
        ng.append(f"T12: A-1 の数え上げを確かめられなかった（{type(_e12).__name__}: {str(_e12)[:80]}）")
    # T12-2 検収専用の値（selftest／KENSHU_LIMITS）を数えていないこと＝本走の数字だけを数える
    try:
        _src13 = _A1_GEN.read_text(encoding="utf-8")
        _base13 = _a1_place3(_src13)["並び"]
        _src13 += "\n\ndef selftest_zzz_uso():\n    return rng.choice([11, 13, 17])\n"
        if _a1_place3(_src13)["並び"] != _base13:
            ng.append("T12-2: 検収専用（selftest）の中の数字まで数えている＝本走の数字と混ざる")
    except Exception as _e13:                                    # noqa: BLE001
        ng.append(f"T12-2: 確かめられなかった（{type(_e13).__name__}: {str(_e13)[:80]}）")

    # ── T13 A-5-5｜E38 の探索の宣言に「数字だけのメニュー」を戻させない（2026-08-16 新設）──
    #   何を守るか＝engine_tuner は「メニューに無い数字を、何回 走らせても出せない」。段A の A-5-5 で
    #   e38_logics.json の search_space から 数字だけのメニュー 5 件（tmax_bars・be_wait・L2.k_bars・
    #   S3.confirm_bars・L3.confirm_bars）を範囲（type=int）に直した。ここが黙って戻る状態を作らない。
    #   ★2段で守る。① 数え上げ（場所4 の「並び」が 0 件）② 物理の止め（接続ファイルの
    #     tuner_adapters/e38.assert_no_number_menu が探索の宣言を作る瞬間に落とす）。
    #   ★E37 は対象外（まこさん決定 2026-08-08「E37とは保留」）＝E37 の接続ファイルには
    #     数字だけのメニューが 3 件 残っている（next_step.md の §6 に記録した）。
    try:
        _p4 = fixed_number_places()["places"][3]
        if _p4["並び"] != 0:
            ng.append(f"T13: 場所4（e38_logics.json の search_space）に 数字だけのメニューが"
                      f" {_p4['並び']} 件 在る＝A-5-5 が戻っている"
                      f"（{'／'.join(r['鍵'] for r in _p4['明細'])}）")
        # ① のメタ確認＝写しに架空の数の並びを1件 混ぜたら、ちゃんと 1 件と数えること
        _e3814 = json.loads(_A1_E38.read_text(encoding="utf-8"))
        (_e3814.get("search_space") or {})["zzz_uso_a55"] = {"type": "cat", "choices": [4, 8]}
        if fixed_number_places(e38=_e3814)["places"][3]["並び"] != 1:
            ng.append("T13: 数字だけのメニューを1件 混ぜても 場所4 が 0 件のまま＝数え上げが効いていない")
        # ② 物理の止め＝接続ファイルの番人が、数字のメニューで落ち・数字でないメニューでは落ちない
        import tuner_adapters.e38 as _ad38
        try:
            _ad38.assert_no_number_menu({"zzz_uso": {"type": "cat", "choices": [1, 2, 3]}})
            ng.append("T13: 接続ファイルの番人が 数字だけのメニューを止めない（物理の止めが死んでいる）")
        except SystemExit:
            pass
        try:
            _ad38.assert_no_number_menu({"tp_mode": {"type": "cat", "choices": ["zone", "pct"]},
                                         "tmax_bars": {"type": "int", "lo": 1, "hi": 12, "step": 1}})
        except SystemExit:
            ng.append("T13: 接続ファイルの番人が 止めすぎている"
                      "（数字でない選択肢のメニューと 範囲の宣言まで落とした）")
        # ② の本走＝いま実物が返す宣言そのものが、番人を通ること（11本 全部）
        for _lg in json.loads(_A1_E38.read_text(encoding="utf-8"))["logics"]:
            try:
                _ad38.space(_lg["id"])
            except SystemExit as _se38:
                if "数字だけのメニュー" in str(_se38):
                    ng.append(f"T13: 実物の宣言が番人に落ちた（{_lg['id']}）＝{str(_se38)[:80]}")
    except Exception as _e14:                                    # noqa: BLE001
        ng.append(f"T13: 確かめられなかった（{type(_e14).__name__}: {str(_e14)[:100]}）")

    # ── T14 A-6｜パラメータの範囲を「両方向」で確かめる（2026-08-16 新設・まこさん指示）──
    #   まこさんの指示（逐語 2026-08-16）＝「『範囲の中の数字が全部 計算できるか』を両方向で確かめる形にします」。
    #   中身の説明は param_range_both_ways の説明文に全部 書いた（ここでは呼ぶだけ）。
    #   ★2段で守る。① 本走＝落ちた組が 0 件 ② メタ確認＝わざと1つ壊したら、この番人が鳴ること。
    try:
        _n14, _ng14 = param_range_both_ways()
        if _n14 < 100:
            ng.append(f"T14: 確かめた組が {_n14} 件しか無い＝範囲を持つ指標を取りこぼしている")
        for _m14 in _ng14:
            ng.append(f"T14: {_m14}")
        _n14b, _ng14b = param_range_both_ways(break_family="RSI")
        if not _ng14b:
            ng.append("T14: わざと『範囲の中なのに作れない』指標を作っても鳴らない"
                      "（片方向に戻っている＝2026-08-16 の MMAR の事故と同じ穴）")
        _n14c, _ng14c = param_range_both_ways()
        if _ng14c:
            ng.append(f"T14: メタ確認のあと元に戻っていない（{_ng14c[0]}）")
    except Exception as _e15:                                    # noqa: BLE001
        ng.append(f"T14: 確かめられなかった（{type(_e15).__name__}: {str(_e15)[:100]}）")

    # ── T15 M2-1-1｜相場の宣言の数え上げ（2026-08-20 新設・まこさん承認）─────────────────
    #   何を守るか＝★7 の節（相場の名前・鍵・止める検査）が、実物とずれた数字を出さないこと。
    #   確かめ方＝やることリストの逐語「名前の一覧から わざと1件 消すと、件数が 4 → 3 に変わること」。
    #   ★実物の REGIME_NAMES は1バイトも書き換えない（写しを渡すだけ）。
    try:
        import tuner_adapters as _ta15
        _rd15 = _regime_decl_view()
        if _rd15["名前の数"] != len(_ta15.REGIME_NAMES):
            ng.append(f"T15: 名前の数 {_rd15['名前の数']} が実物 REGIME_NAMES の"
                      f" {len(_ta15.REGIME_NAMES)} 件と合わない")
        _cut15 = _regime_decl_view(names=_ta15.REGIME_NAMES[:-1])
        if _cut15["名前の数"] != _rd15["名前の数"] - 1:
            ng.append(f"T15: 名前を わざと1件 消しても数がちょうど1 減らない"
                      f"（{_rd15['名前の数']} → {_cut15['名前の数']}）")
        if _rd15["要る列"] != ["entry_col", "block_col"]:
            ng.append(f"T15: 宣言の列の鍵が entry_col・block_col でない: {_rd15['要る列']}"
                      "（検査のコードから鍵を引けていない）")
        for _c15 in _rd15["検査"]:
            if _c15["件数"] <= 0:
                ng.append(f"T15: 『{_c15['どこで']}』の検査の数が 0＝数え上げがその場所を見ていない")
    except Exception as _e16:                                    # noqa: BLE001
        ng.append(f"T15: 確かめられなかった（{type(_e16).__name__}: {str(_e16)[:80]}）")

    # ── T16 M2-1-2｜名前ごとの判定の列の表（2026-08-20 新設・まこさん承認）─────────────────
    #   確かめ方＝やることリストの逐語「架空の列を1本 足すと欄が変わること」。
    #   ★実物のファイルは1バイトも書き換えない（宣言の写しを渡すだけ）。
    try:
        _rd16 = _regime_decl_view()
        _row16 = {r["名前"]: r for r in _rd16["名前ごと"]}
        if "range_ok_rg5" not in _row16["range"]["建ててよい列"] or "列を作る側に在る" not in _row16["range"]["建ててよい列"]:
            ng.append(f"T16: range の建ててよい列が実物と合わない: {_row16['range']['建ててよい列']}")
        if _row16["downtrend"]["建ててよい列"] != "宣言なし" or _row16["spike"]["建ててよい列"] != "宣言なし":
            ng.append("T16: 宣言の無い名前（downtrend・spike）の欄が「宣言なし」になっていない")
        _fake16 = list(_rd16["宣言"]) + [dict(誰が="番人の試験", name="downtrend",
                                              entry_col="zzz_uso_col", block_col=None)]
        _cut16 = _regime_decl_view(decls=_fake16)
        _dcell = {r["名前"]: r for r in _cut16["名前ごと"]}["downtrend"]["建ててよい列"]
        if "zzz_uso_col" not in _dcell:
            ng.append(f"T16: 架空の列を宣言の写しに足しても欄が変わらない: {_dcell}")
        elif "★列を作る側に無い" not in _dcell:
            ng.append(f"T16: 架空の列（列を作る側に無いはず）が「無い」と出ない: {_dcell}")
    except Exception as _e17:                                    # noqa: BLE001
        ng.append(f"T16: 確かめられなかった（{type(_e17).__name__}: {str(_e17)[:80]}）")

    # ── T17 M2-2-1｜M2-2 の基準値（2026-08-20 新設・まこさん承認）─────────────────────────
    #   確かめ方＝受け入れ条件の逐語「わざと1種 消した写しを渡すと、数がちょうど1 減ること
    #   （形・部品の2か所で確かめる）」。★実物のファイルは1バイトも書き換えない（写しを渡すだけ）。
    try:
        import engine_tuner_exec as _ex17
        _b17 = _m2_baseline_view()
        _row17 = {r["何"]: r for r in _b17["rows"]}
        # ① 実物の数と一致するか（形・部品・時間足・前処理・2本組み）
        for _nm17, _got17, _want17 in (
                ("条件の形", _b17["形の数"], len(_ex17.FORMS)),
                ("材料の前処理", _row17["材料の前処理"]["数"], len(_ex17.MATERIAL_PRE)),
                ("材料2本の組み方", _row17["材料2本の組み方"]["数"], len(_ex17.PAIR_OPS))):
            if _got17 != _want17:
                ng.append(f"T17: 『{_nm17}』の数 {_got17} が実物の {_want17} と合わない")
        _sf17 = json.loads((_RATCHET / "signal_families.json").read_text(encoding="utf-8"))
        if _b17["部品の数"] != len(_sf17["parts"]) or _b17["時間足の数"] != len(_sf17["timeframes"]):
            ng.append(f"T17: 部品 {_b17['部品の数']}・時間足 {_b17['時間足の数']} が型の表の"
                      f" {len(_sf17['parts'])}・{len(_sf17['timeframes'])} と合わない")
        # ② 材料の列は掛け算になっているか
        if _row17["材料の列（部品 × 時間足）"]["数"] != _b17["部品の数"] * _b17["時間足の数"]:
            ng.append("T17: 材料の列が『部品 × 時間足』の掛け算になっていない"
                      f"（{_row17['材料の列（部品 × 時間足）']['数']}）")
        # ③ わざと1種 消すと、数がちょうど1 減るか（形）
        _cutf = _m2_baseline_view(forms=tuple(_ex17.FORMS)[:-1])
        if _cutf["形の数"] != _b17["形の数"] - 1:
            ng.append(f"T17: 形を わざと1種 消しても数がちょうど1 減らない"
                      f"（{_b17['形の数']} → {_cutf['形の数']}）")
        # ④ わざと1種 消すと、数がちょうど1 減るか（部品）＋ 掛け算も追随するか
        _cutp = _m2_baseline_view(parts=list(_sf17["parts"])[:-1])
        _rowp = {r["何"]: r for r in _cutp["rows"]}
        if _cutp["部品の数"] != _b17["部品の数"] - 1:
            ng.append(f"T17: 部品を わざと1種 消しても数がちょうど1 減らない"
                      f"（{_b17['部品の数']} → {_cutp['部品の数']}）")
        elif _rowp["材料の列（部品 × 時間足）"]["数"] != (_b17["部品の数"] - 1) * _b17["時間足の数"]:
            ng.append("T17: 部品を1種 消しても、材料の列の掛け算が追随しない")
        # ⑤ 束ね方が実物から引けているか（2通りの引き方が食い違えば ng に出る）
        if len(_b17["束ね方"]) == 0:
            ng.append("T17: 束ね方を1つも引けていない")
    except Exception as _e18:                                    # noqa: BLE001
        ng.append(f"T17: 確かめられなかった（{type(_e18).__name__}: {str(_e18)[:80]}）")

    # ── F1〜F6｜「作ってはいけないものとの照合」（2026-08-26・64回目・承認 b034352a6940f601…）──
    #   何を守るか＝照合の答えの欄が、CC の文章でなく実物の数字から出ていること。
    #   ★F1〜F5 は写しを渡して確かめる（実物のファイルは1バイトも書き換えない）。
    try:
        _fb_req = json.loads(_FB_REQ_JSON.read_text(encoding="utf-8"))
        _fb_gen = _A1_GEN.read_text(encoding="utf-8")
        _fb_items0 = forbidden_items()
        _fb_rnd0 = count_random_draws()
        _fb_law0 = count_law_reads()

        # F1 要件の json の写しに架空の3番を足す → 表に3番が出て、答えが「測り方が未定」
        _fb_req_u = json.loads(json.dumps(_fb_req, ensure_ascii=False))
        for _i, _s in enumerate(_fb_req_u.get("purpose_reading", [])):
            if isinstance(_s, str) and _s.lstrip().startswith("| # | 作ってはいけないもの"):
                _fb_req_u["purpose_reading"][_i] = _s + "\n| 3 | **架空の3番（番人）** | 番人が足した |"
                break
        _fb_items_u = forbidden_items(_fb_req_u)
        if len(_fb_items_u) != len(_fb_items0) + 1:
            ng.append(f"F1: 要件の写しに3番を足しても一覧がちょうど1 増えない"
                      f"（{len(_fb_items0)} → {len(_fb_items_u)}）＝一覧を json から読めていない")
        elif forbidden_verdict("3", {}) != _FB_TBD:
            ng.append(f"F1: 測り方の無い番号の答えが『{_FB_TBD}』にならない")
        elif f"| 3 | **架空の3番（番人）** |" not in forbidden_block(req_json=_fb_req_u):
            ng.append("F1: 差し込みの表に3番が出ない（一覧が表に反映されない）")

        # F2 生成器の写しに乱数の呼び出しを1つ 足す → 合計がちょうど1 増える
        _fb_gen_u = _fb_gen + "\n\ndef _zzz_uso_fb2(rng):\n    return rng.choice([1, 2, 3])\n"
        _got2 = count_random_draws(_fb_gen_u)["合計"]
        if _got2 != _fb_rnd0["合計"] + 1:
            ng.append(f"F2: 乱数の呼び出しを1つ 足しても合計がちょうど1 増えない"
                      f"（{_fb_rnd0['合計']} → {_got2}）")
        # ★3段の書き方も拾えること（57回目の数え方はここを落としていた）
        _fb_gen_u3 = _fb_gen + "\n\ndef _zzz_uso_fb2b():\n    return np.random.default_rng(1)\n"
        if count_random_draws(_fb_gen_u3)["合計"] != _fb_rnd0["合計"] + 1:
            ng.append("F2: 3段の書き方（np.random.default_rng）を数えていない")

        # F3 設定ファイルの写しに架空の数の並びを1つ 足す → その場所の件数がちょうど1 増える
        #     （既存の T12 と同じ形＝ここでは 場所2 で1件だけ確かめる）
        _fb_lim_u = json.loads(_A1_LIM.read_text(encoding="utf-8"))
        _fb_lim_u["zzz_uso_fb3_grid"] = [11, 13, 17]
        _fb_base3 = fixed_number_places()["places"][1]["並び"]
        _fb_got3 = fixed_number_places(lim=_fb_lim_u)["places"][1]["並び"]
        if _fb_got3 != _fb_base3 + 1:
            ng.append(f"F3: 数の並びを1つ 足しても件数がちょうど1 増えない（{_fb_base3} → {_fb_got3}）")

        # F4 写しから法則の表を読む呼び出しを全部 消す → 1番の答えが「疑いあり」→「当たっています」
        _m_now = {"乱数": _fb_rnd0["合計"], "法則": _fb_law0["合計"]}
        if forbidden_verdict("1", _m_now) != _FB_SUSPECT:
            ng.append(f"F4: いまの1番の答えが『{_FB_SUSPECT}』でない"
                      f"（乱数 {_fb_rnd0['合計']}件・法則 {_fb_law0['合計']}件）")
        if forbidden_verdict("1", {"乱数": _fb_rnd0["合計"], "法則": 0}) != _FB_HIT:
            ng.append("F4: 法則の表を1つも読まない状態でも『当たっています』にならない"
                      "＝1番が永久に白黒の付かない検査になっている")
        if forbidden_verdict("1", {"乱数": 0, "法則": 0}) != _FB_MISS:
            ng.append("F4: 乱数が0件でも『当たりません』にならない")
        # ★数え方のメタ確認＝法則の表を読む呼び出しを写しから消すと、件数が減ること
        _fb_gen_nolaw = _fb_gen
        for _fn in sorted(_FB_LAW_FUNCS):
            _fb_gen_nolaw = _fb_gen_nolaw.replace(f"{_fn}(", f"_zzz_uso_{_fn}_(")
        if count_law_reads(_fb_gen_nolaw)["合計"] != 0:
            ng.append("F4: 法則の表を読む呼び出しを全部 消しても件数が 0 にならない")

        # F5 答えの文字列が4種類だけ（決めた4つ以外が1つも出ない）
        _seen = set()
        for _no in ("1", "2", "3", "99"):
            for _mm in ({"乱数": 0, "法則": 0, "数の並び": 0, "範囲を通さない": 0},
                        {"乱数": 5, "法則": 0, "数の並び": 0, "範囲を通さない": 0},
                        {"乱数": 5, "法則": 9, "数の並び": 3, "範囲を通さない": 0},
                        {"乱数": 5, "法則": 9, "数の並び": 0, "範囲を通さない": 2}):
                _seen.add(forbidden_verdict(_no, _mm))
        if not _seen <= set(_FB_VERDICTS):
            ng.append(f"F5: 決めた4種類 以外の答えが出た: {sorted(_seen - set(_FB_VERDICTS))}")
        if len(_FB_VERDICTS) != 4 or len(set(_FB_VERDICTS)) != 4:
            ng.append(f"F5: 答えの文字列の一覧が4つでない（{len(set(_FB_VERDICTS))}）")

        # F6 差し込みを1文字 変えると --verify が鳴る（メタ確認・実物を必ず元へ戻す）
        #   ★先に「いまの差し込みが最新か」を見る。古いまま壊すと、鳴った理由が
        #     「私が壊したから」なのか「元から古いから」なのか区別できない（106番と同じ型）。
        _fb_p = _FB_TARGETS[0][0]
        _fb_msg = "作ってはいけないものとの照合の差し込みが実物と食い違う"
        if not (_fb_p.exists() and _FB_START_RE.search(_fb_p.read_text(encoding="utf-8"))):
            ng.append("F6: 差し込みの印がまだ無いので改変検出を確かめられない（先に印を置いて --write）")
        elif any(_fb_msg in x for x in verify()):
            ng.append(f"F6: 壊す前から差し込みが古い＝先に --write が要る（{_fb_p.name}）")
        else:
            _keep_fb = _fb_p.read_text(encoding="utf-8")
            try:
                _fb_p.write_text(_keep_fb.replace(_FB_END, "書き換えました\n" + _FB_END, 1),
                                 encoding="utf-8")
                if not any(_fb_msg in x for x in verify()):
                    ng.append("F6: 差し込みを書き換えても --verify が鳴らない（改変検出が死んでいる）")
            finally:
                _fb_p.write_text(_keep_fb, encoding="utf-8")
            if any(_fb_msg in x for x in verify()):
                ng.append("F6: 元に戻したのに --verify が鳴る（番人の後始末ができていない）")
    except Exception as _efb:                                    # noqa: BLE001
        ng.append(f"F1〜F6: 確かめられなかった（{type(_efb).__name__}: {str(_efb)[:100]}）")

    # T6 わざと書き換えると --verify が鳴る（メタ確認）
    # ★2026-08-26（64回目）＝見るのは materials.md についての言い分だけにした。
    #   理由＝verify() に「作ってはいけないものとの照合の差し込み」の検査を足したので、
    #   差し込みが古いだけでも verify() が鳴る。それを T6 が「後始末ができていない」と
    #   誤って説明していた（実測で確認）。106番と同じ型なので、範囲を絞って直した。
    _t6_msg = "materials.md が正本と一致しない"
    if not _MD.exists():
        ng.append("T6: materials.md が無いので改変検出を確かめられない（先に --write）")
    elif any(_t6_msg in x for x in verify()):
        # ★2026-09-06（監査 cp23 の X-4）＝素の状態で鳴っていたら、壊して戻す番人は成立しない。
        #   直す前はそのまま実行し、戻しても鳴るので「後始末ができていない」が必ず立った
        #   ＝赤の原因が本当の欠陥かどうかを、この番人では区別できなかった。
        ng.append("T6: 素の状態で --verify が鳴っている（先に --write で直す）"
                  "＝壊して戻す番人を当てられない")
    else:
        keep = _MD.read_text(encoding="utf-8")
        try:
            _MD.write_text(keep + "この行は手で足しました\n", encoding="utf-8")
            if not any(_t6_msg in x for x in verify()):
                ng.append("T6: 手で書き足しても --verify が鳴らない（改変検出が死んでいる）")
        finally:
            _MD.write_text(keep, encoding="utf-8")
        if any(_t6_msg in x for x in verify()):
            ng.append("T6: 元に戻したのに --verify が鳴る（番人の後始末ができていない）")
    # ══ B-4｜やることリストの確かめ方 × 要件の逐語（2026-08-26・承認 a3be50c30e7ea827）══
    #   ★設計書 §11 の10件と1件ずつ対応する。わざと壊して、止まることを確かめる。
    _ra_msg = "やることリストの確かめ方 × 要件の逐語"
    try:
        _rows = milestone_rows()
        _mp = _req_map()
        _idx = _req_index()

        # R1 対応表に無い行を1つ作ると落ちる
        _fake = _rows + [{"file": "x.md", "id": "M9-9-9", "todo": "架空", "check": "架空"}]
        if not req_accept_problems(_fake, _mp, _idx):
            ng.append("R1: 対応表に無い行を足しても落ちない（対応の抜けを見ていない）")

        # R2 要件に無い番号を書くと落ちる
        _bad = dict(_mp); _bad["M2-1-1"] = {"req": ["R99"], "basis": "架空"}
        if not req_accept_problems(_rows, _bad, _idx):
            ng.append("R2: 要件の正本に無い番号（R99）を書いても落ちない")

        # R3 basis を空にすると落ちる
        _bad = dict(_mp); _bad["M2-1-1"] = {"req": ["R5"], "basis": "  "}
        if not req_accept_problems(_rows, _bad, _idx):
            ng.append("R3: なぜその要件かの1行が空でも落ちない")

        # R7 いまの状態は問題ゼロ
        if req_accept_problems(_rows, _mp, _idx):
            ng.append("R7: いまの対応表に不足が在る（--write の前に直す）")

        # ★B1・B2（2026-09-06・再監査 cp22 の N-4）＝KB の件数の差し込みに番人が0件だったので足す。
        #   B1＝差し込んだ件数を1文字 変えると verify が ❌ を出す ／ B2＝元に戻すと出ない。
        #   ★実物のファイルを一度だけ書き換えて、必ず元に戻す（try/finally）。
        # ★2026-09-06（監査 cp23 の X-4・X-5・設計書 iter="cp23-selftest-audit-req-20260906"）＝2つ直した。
        #   ①**素の状態で verify が鳴っていたら、番人を実行せず不合格に数える。**
        #     直す前は print するだけで先へ進み、壊して戻しても鳴ったままなので
        #     「元に戻したのに鳴る」が必ず立った＝赤の原因が本当の欠陥かどうか分からなかった。
        #   ②**COUNTS の差し込みにも同じ壊し方を当てる（B3・B4）。**
        #     直す前は bans の差し込みだけを壊していた＝cp22 の N-3 で足した COUNTS は番人ゼロだった。
        _bt_now = _BANS_TARGET.read_text(encoding="utf-8") if _BANS_TARGET.exists() else ""
        for _bn, _bmark, _bkind, _bmsg in (
            ("B1・B2", _BANS_START, "bans", "向きを持たない部品の件数"),
            ("B3・B4", _COUNTS_START, "counts", "指標の種類・材料の行・部品の件数"),
        ):
            if _bmark not in _bt_now:
                print(f"     [{_bn}] KB に {_bkind} の差し込みの印が無い＝この番人は今回は当てられない")
                skipped.append(_bn)
                continue
            if any(_bmsg in x for x in (verify() or [])):
                ng.append(f"{_bn}: 素の状態で verify が鳴っている（先に --write で直す）"
                          "＝壊して戻す番人を当てられない")
                continue
            _b_keep = _BANS_TARGET.read_text(encoding="utf-8")
            try:
                _b_cur = bans_count_block(_bkind)
                _BANS_TARGET.write_text(
                    _b_keep.replace(_b_cur, _b_cur.replace("件**", "件★**", 1)), encoding="utf-8")
                if not any(_bmsg in x for x in (verify() or [])):
                    ng.append(f"{_bn}: KB の件数を書き換えても verify が ❌ を出さない（番人が効いていない）")
            finally:
                _BANS_TARGET.write_text(_b_keep, encoding="utf-8")
            if any(_bmsg in x for x in (verify() or [])):
                ng.append(f"{_bn}: 元に戻したのに verify が ❌ を出す（書き換えが残っている）")

        # R6 要件の accept を1文字 変えると、差し込む表も同じだけ変わる（写しではない）
        # ★2026-09-06（再監査 cp22 の N-5）＝壊す相手の鍵を焼き込むのをやめた。
        #   直す前は "R5" と書いていたが、やることリストが M2-C・M2-D へ進んで
        #   差し込む表に R5 の行が出なくなり、わざと壊しても落ちなくなっていた（空振り）。
        #   手本＝同じ自己テストの S6（その場で実物から選ぶ形）。
        #   ★選ぶ相手は「やることリストに在る行が指している要件」＝差し込む表に実際に出るもの。
        _r6_key = next((rid for r in _rows
                        for rid in (_mp.get(r["id"], {}).get("req") or [])
                        if rid in _idx), None)
        if _r6_key is None:
            print("     [R6] 差し込む表に出る要件が1件も無い＝この番人は今回は当てられない")
            skipped.append("R6")
        else:
            _idx2 = {k: dict(v) for k, v in _idx.items()}
            _idx2[_r6_key]["accept"] = _idx2[_r6_key]["accept"] + "＿番人"
            if req_accept_block(_rows, _mp, _idx) == req_accept_block(_rows, _mp, _idx2):
                ng.append(f"R6: 要件の逐語（{_r6_key}）を変えても差し込む表が変わらない（その場で引いていない）")

        # R8 やることリストの確かめ方の欄を変えると、差し込む表の欄も変わる
        _rows2 = [dict(r) for r in _rows]
        _rows2[0]["check"] = _rows2[0]["check"] + "＿番人"
        if req_accept_block(_rows, _mp, _idx) == req_accept_block(_rows2, _mp, _idx):
            ng.append("R8: 確かめ方の欄を変えても差し込む表が変わらない（実物から引いていない）")

        # R9 対応表から1件 消すと落ちる（R1 と同じ道）
        # ★2026-09-06（再監査 cp22 の N-5）＝壊す相手の鍵を焼き込むのをやめた。
        #   直す前は "M2-1-1" と書いていたが、やることリストが M2-C・M2-D へ進んで
        #   その行が2本の md から消え（実測＝どちらも 0件）、わざと壊しても落ちなくなっていた。
        _r9_key = next((r["id"] for r in _rows if r["id"] in _mp), None)
        if _r9_key is None:
            print("     [R9] やることリストと対応表の両方に在る行が1件も無い＝この番人は今回は当てられない")
            skipped.append("R9")
        else:
            _bad = {k: v for k, v in _mp.items() if k != _r9_key}
            if not req_accept_problems(_rows, _bad, _idx):
                ng.append(f"R9: 対応表から1件（{_r9_key}）消しても落ちない")

        # R4 差し込んだ逐語を手で1文字 変えると --verify が鳴る（メタ確認）
        # R5 印を消すと「印が無い」で鳴る
        # R10 印の外の本文を変えても鳴らない
        _ra_p = _FB_TARGETS[0][0]
        if _ra_p.exists() and _RA_START_RE.search(_ra_p.read_text(encoding="utf-8")):
            _keep = _ra_p.read_text(encoding="utf-8")
            try:
                _ra_p.write_text(_keep.replace(_RA_END, "手で足しました\n" + _RA_END, 1),
                                 encoding="utf-8")
                if not any(_ra_msg in x for x in verify()):
                    ng.append("R4: 差し込みを書き換えても --verify が鳴らない（改変検出が死んでいる）")
                _ra_p.write_text(_keep.replace(_RA_END, "", 1), encoding="utf-8")
                if not any("REQ_ACCEPT_START/END の印が無い" in x for x in verify()):
                    ng.append("R5: 印を消しても --verify が鳴らない")
                _ra_p.write_text(_keep + "\n印の外に足した行\n", encoding="utf-8")
                if any(_ra_msg in x for x in verify()):
                    ng.append("R10: 印の外を変えただけで鳴る（印の間だけを見ていない）")
            finally:
                _ra_p.write_text(_keep, encoding="utf-8")
            if any(_ra_msg in x for x in verify()):
                ng.append("R4: 元に戻したのに --verify が鳴る（番人の後始末ができていない）")
        else:
            ng.append("R4・R5・R10: 印が無いので改変検出を確かめられない（先に印を置く）")
    except Exception as _era:                                    # noqa: BLE001
        ng.append(f"R1〜R10: 確かめられなかった（{type(_era).__name__}: {str(_era)[:100]}）")

    # ══ B-5｜「満たした」の根拠を、走らせた出力に限る（2026-08-26・承認 03f797a70c978b3e）══
    #   ★設計書 §11 の10件のうち、9番（差し込みを手で書き換えると落ちる）と
    #     10番（印の外を変えても落ちない）は、B-4 の番人 R4・R10 が同じことを確かめている。
    #     だからここで新しく足すのは 8件（S1〜S8）。
    try:
        _s_rows = milestone_rows()
        _s_mp = _req_map()
        _s_idx = _req_index()

        # S1 progress に「9項目のうち7項目を満たす」を入れると落ちる
        _i = {k: dict(v) for k, v in _s_idx.items()}
        _i["R3"]["progress"] = "完了の線9項目のうち7項目を満たす。"
        if not req_progress_problems(_i):
            ng.append("S1: progress に『9項目のうち7項目』を入れても落ちない（手で打った数字を弾いていない）")

        # S2 「2つとも満たした」でも落ちる
        _i = {k: dict(v) for k, v in _s_idx.items()}
        _i["R1"]["progress"] = "完了の条件2つとも満たした＝①②。"
        if not req_progress_problems(_i):
            ng.append("S2: progress に『2つとも』を入れても落ちない")

        # S3 日付だけなら落ちない（★日付は止めない）
        _i = {k: dict(v) for k, v in _s_idx.items()}
        _i["R1"]["progress"] = "完了（2026-08-02）。engine_tuner から S1 と L1 を回せる。"
        if req_progress_problems(_i):
            ng.append("S3: 日付だけの progress で落ちる（日付まで止めてしまっている）")

        # S4 いまの17件は落ちない
        if req_progress_problems(_s_idx):
            ng.append("S4: いまの要件の progress に達成度の数字が残っている（先に外す）")

        # S5 state=完了 の要件の行を1つ「まだ」に変えると、ずれが1 増える
        _base_gap = sum(1 for s in req_state_rows(_s_rows, _s_mp, _s_idx) if s["gap"])
        _done_ok = [r for r in _s_rows
                    if "✅済" in str(r.get("state", ""))
                    and any(_s_idx.get(x, {}).get("state") == "完了"
                            for x in (_s_mp.get(r["id"], {}).get("req") or []))]
        if _done_ok:
            _r2 = [dict(r) for r in _s_rows]
            for r in _r2:
                if r["id"] == _done_ok[0]["id"]:
                    r["state"] = "まだ"
            if sum(1 for s in req_state_rows(_r2, _s_mp, _s_idx) if s["gap"]) <= _base_gap:
                ng.append("S5: ✅済 を1つ『まだ』に変えても、ずれの件数が増えない")
        else:
            # ★2026-09-06（再監査 cp22 の N-5）＝相手が居ないときに ❌ を出すのをやめた。
            #   やることリストが進むと「state=完了 の要件に効く ✅済 の行」は普通に0件になる。
            #   0件は「番人が壊れている」ではなく「今回は当てる相手が居ない」＝画面に出すだけにする。
            print("     [S5] state=完了 の要件に効く ✅済 の行が0件＝この番人は今回は当てられない")
            skipped.append("S5")

        # S6 対応表から1件 消すと、効く行の数が変わる
        _k = next((k for k, v in _s_mp.items() if v.get("req")), None)
        if _k:
            _m2 = {k: v for k, v in _s_mp.items() if k != _k}
            if req_state_rows(_s_rows, _s_mp, _s_idx) == req_state_rows(_s_rows, _m2, _s_idx):
                ng.append("S6: 対応表から1件 消しても、効く行の数が変わらない（実物から引いていない）")

        # S7 ✅済 の行から根拠の指し先を消すと、件数が1 増える
        _with = [r for r in _s_rows
                 if "✅済" in str(r.get("state", "")) and _EVIDENCE.search(str(r.get("state", "")))]
        if _with:
            _r3 = [dict(r) for r in _s_rows]
            for r in _r3:
                if r["id"] == _with[0]["id"]:
                    r["state"] = "✅済（2026-08-20）"
            if len(unevidenced_done(_r3)) <= len(unevidenced_done(_s_rows)):
                ng.append("S7: 根拠の指し先を消しても、件数が増えない")
        else:
            ng.append("S7: 確かめる相手（根拠の指し先が在る ✅済 の行）が見つからない")

        # S8 要件の題を1文字 変えると、差し込む表も同じだけ変わる
        _i = {k: dict(v) for k, v in _s_idx.items()}
        _i["R1"]["title"] = _i["R1"]["title"] + "＿番人"
        if req_accept_block(_s_rows, _s_mp, _s_idx) == req_accept_block(_s_rows, _s_mp, _i):
            ng.append("S8: 要件の題を変えても差し込む表が変わらない（その場で引いていない）")
    except Exception as _es:                                     # noqa: BLE001
        ng.append(f"S1〜S8: 確かめられなかった（{type(_es).__name__}: {str(_es)[:100]}）")

    print("=" * 70)
    print("gen_materials 自己検査")
    print("=" * 70)
    for x in ng:
        print("  ❌ " + x)
    # ★2026-09-06（監査 cp23 の X-5）＝当てられなかった番人を、合否の行に必ず出す。
    #   直す前は「✅ 全部 pass」だけで、飛ばした番人が在ることが合否の行から分からなかった。
    _sk = f"（該当なし {len(skipped)}件: {'・'.join(skipped)}）" if skipped else ""
    print(f"  ✅ 全部 pass{_sk}" if not ng else f"  ❌ {len(ng)} 件{_sk}")
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
