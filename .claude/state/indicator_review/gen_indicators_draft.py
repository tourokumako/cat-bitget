#!/usr/bin/env python3
"""gen_indicators_draft.py — 指標の情報を1つのデータ（scripts/priority_rebuild/indicators/indicators.json）に、いまの置き場から
プログラムで写す（元のコードは1行も直さない・読むだけ）。

まこさん（2026-10-23）「指標の情報を１つのデータに集約して、そこからしか指標の情報は取れない状態にするための修正」。
工事 m2c15-single-source-fix-20261023 の設計書1（①集める）で作り、工事 m2c15-indicator-redirect-20261031（161-1・やることの表 F-2・F-3）で、
要素の定義表（192番・まこさん OK 2026-10-31）の形で写す形に作り直した。
写す元（設計書1の 4-4 の1〜9・変えない）
  1 INDICATOR_TABLE  2 定義表 REFS（_r・MAKO_R1 が足した mako を含む）  3 計算の登録 MATERIAL_FAMILIES（_reg）
  4 observe_config.json（material_params・material_first_hidden・古い鍵）  5 計算の関数の引数の既定値
  6 indicator_params_by_strategy.json・recipes/search_limits.json  7 indicator_switch.json
  8 表の外の辞書（INDUSTRY_MAP・TA_CLASS_MAP・EXT2・CONST_REGISTRY・_EXIT_LEVEL_CONST・V9_FAMILY_MAP・CAT2LIN・HOUKOU2PROP）
  9 資料の表・調べた結果と、直す相手の一覧（fix_inventory_20261024.md）の「①写す」の行の全部（どの行を読むかは一覧から読む）
  ★161-1 で足した写す元＝10 要素の定義表（indicators.json の中・要素の名前と形はここから読む・コードに欄の名前を書かない）
    11 隠れた数字（172番の道具 gen_params_in_name.py の measure と、計算式が呼ぶ自前の関数の数の既定＝監査 CP91 の修正1）
    12 いまのカタログの列の並び（observe_diag._catalog_from_config＝写す元の関数・162番まで＝列を作る組 ②-12・④-9・171番まで。161-2 から build_catalog はこれを読む）
写す先の形（一番外の5つ）＝_作った道具・要素の定義表・指標の記録（名前を鍵にした辞書）・使い方の記録（行の並び）・部品の記録（名前を鍵にした辞書）
  指標の記録＝②の要素（名前・計算の関数・パラメータの軸・値の単位と値域・値の読み方・教科書の役割・照らしと出どころ・オン/オフ・閾値の範囲・列を作る組）
  使い方の記録＝③の要素。いまのデータが使い方を決めている4種（出口の水準の定数を持つ ADX・RSI・Stoch%K・Stoch%D）だけ＝
    出口の反転と前提崩れの印 × 玉の向き（SHORT・LONG）の16件（engine_tuner_gen.py の _EXIT_LEVEL_CONST と出口の確認の条件）
  部品の記録＝④の要素。帯の線の8種（PART_USES・指標の構造の要件定義書 第4章の C＝帯の線は部品の記録・監査 CP94 の修正10 案B）
  ★いまの23の欄を全部 読み、写せない欄が在れば止まる。値が無い要素（②-3 出力・②-8 確定と期間 ほか）は鍵を書かない＝
    読む口が「無いときの扱い」で返す（Y-16）。
  ★代表の値は、資料の表のパラメータの名前で軸に合わせる（並びの番号だけでは合わせない・監査 CP94 の修正1・まこさん「案B」2026-11-01）。
    合わない軸は「まだ決めていない」にし、合わない値の一覧を画面に出す（対応を決めるのは70番の T-3）。元の値は②-9 に元の形で残す。
使い方:
  python3 .claude/state/indicator_review/gen_indicators_draft.py --rewrite   # 写す元から作り直して indicators.json を書き替える。古い形（一番外に「記録」）
                                                                            #   なら新しい形へ写し直す。新しい形なら、違う所を全部画面に出して書き直す
                                                                            #   （162番で写す元を消すまでは、値は写す元で直し、この口で作り直す＝監査 CP94 の修正14 案B）
  python3 .claude/state/indicator_review/gen_indicators_draft.py            # 新しい形の indicators.json と、写す元から作り直した物が同じか（違えば止まる）
  python3 .claude/state/indicator_review/gen_indicators_draft.py --verify   # 書かずに、記録と写す元を1件ずつ比べる（違えば終わりのコード 1）
  python3 .claude/state/indicator_review/gen_indicators_draft.py --selftest # 自分の中の見本の古い記録を新しい形に写して確かめる（本物には書かない）
  ★写しで確かめるときは IND_ROOT=<写しの一番上> を渡す（ss_outside_probe.py の SS_ROOT と同じ形）
"""
import argparse
import ast
import contextlib
import copy
import inspect
import io
import itertools
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(os.environ.get("IND_ROOT", "/Users/tachiharamasako/Documents/GitHub/cat-bitget"))
SDK = ROOT / "v3-bitget-api-sdk/bitget-python-sdk-api"
PR = SDK / "scripts/priority_rebuild"
ST = ROOT / ".claude/state"
HERE = Path(__file__).resolve().parent
OUT = PR / "indicators" / "indicators.json"                 # F-2＝書く先（作業場には書かない）
INV = HERE / "fix_inventory_20261024.md"                    # 直す相手の一覧（「①写す」の行＝写し漏れを確かめる相手）
WORK = "m2c15-indicator-redirect-20261031"
TOP = ("_作った道具", "要素の定義表", "指標の記録", "使い方の記録", "部品の記録")   # 一番外の5つ（F-7）
MADE_BY = ".claude/state/indicator_review/gen_indicators_draft.py（手で書かない）"
UNDECIDED = "まだ決めていない"                                  # 読む口の決まり②（値の無い範囲はこの印＝CC が数字を作らない）
# いまの23の欄（設計書1の 4-8）＝写す元を集める途中の形。写す先の欄の名前はここに無い（要素の定義表から読む）
OLD_FIELDS = ("名前", "列の名前の型", "計算の関数", "照合の関数・既知答え", "代表の固定値（スキャル／デイトレ）",
              "名前に出ない軸の最初の値", "列を作る値", "コードの中の既定値", "範囲", "役割・札・値域・注記", "方向・性質",
              "オン/オフ", "mako", "ライブラリとの対応", "出口の水準", "V9 の名前", "教科書の出どころ", "閾値の値", "閾値の文",
              "閾値の代表の固定値（スキャル／デイトレ）", "閾値の範囲",
              "食い違いの記録", "ほかの置き場の値")
# 3-2 の11件目（まこさん 2026-10-24「ok」）＝方向から性質への対応の表に足す1行。いまの4つの対応（HOUKOU2PROP）に無い方向。
DECIDED_PROP = {"向きつき": dict(性質=["trend"], 出どころ="やることの表 3-2 の11件目（まこさん 2026-10-24「ok」）")}
# 写す元のうち、記録の決まった欄に入る置き場（ここに無い「①写す」の行は、代入の右辺を ast で開いて「ほかの置き場の値」に写す）
OWN = ("INDICATOR_TABLE", "REFS", "MATERIAL_FAMILIES", "INDUSTRY_MAP", "TA_CLASS_MAP", "EXT2",
       "_EXIT_LEVEL_CONST", "V9_FAMILY_MAP", "R1_KEEP_ON", "MAKO_R1", "CAT2LIN", "HOUKOU2PROP", "_r", "_reg")
JSON_PATH = {"indicator_params_by_strategy.json": ST / "indicator_params_by_strategy.json",
             "indicator_params_review.json": ST / "indicator_params_review.json",
             "indicator_roles_thresholds.json": ST / "indicator_roles_thresholds.json",
             "indicator_switch.json": SDK / ".claude/ratchet/indicator_switch.json",
             "observe_config.json": PR / "observe_config.json",
             "r1_role_map.json": HERE / "r1_role_map.json",
             "search_limits.json": PR / "recipes/search_limits.json"}
JSON_OWN = {"indicator_params_by_strategy.json": {"指標"}, "indicator_params_review.json": {"[]/種類", "[]/元にした種類"},
            "indicator_roles_thresholds.json": {"[]/種類"}, "indicator_switch.json": {"on", "off", "sources"},
            "observe_config.json": {"material_params", "material_first_hidden"},
            "search_limits.json": {"material_param_ranges"}}
# ── 161-1 で足す要素の定義表の3行と選べる値（やることの表 F-7・まこさん「★の見出しはOK」2026-10-31・ok_yarukoto_20261031）────
SRC_F7 = "やることの表 F-7（工事 m2c15-indicator-redirect-20261031・まこさん OK 2026-10-31・ok_yarukoto_20261031）"
NEW_ROWS = {
    "②-11": {"番号": "②-12", "要素の名前": "列を作る組", "置く記録": "指標の記録",
             "中身": "いまのカタログの列を作る組（名前の型・照らす形・組＝名前の型に入れる数字・カタログの並び・照らす形の値＝参照表の型で列の名前から読んだ数字・出どころの鍵）。171番まで、列の名前と並びを変えないために持つ。探す範囲ではない（範囲は ②-4・②-11）",
             "形の決まり": {"値の種類": "名前の型（文字の並び）・照らす形（文字の並び）・組の並び・並びの番号の並び・照らす形の値の並び・出どころの鍵の並び", "選べる値の名前": None, "複数持てるか": True},
             "無いときの扱い": "未設定（列を作らない種類は空の並び）", "オン/オフ": "オン", "読むプログラム": [],
             "写す元": "記録の「列の名前の型」「列を作る値」と、いまのカタログの並び（observe_diag.build_catalog）",
             "根拠": {"要件の行": ["core_requirements_full.md:55"], "構造に要ること": [], "拡張の条件": []}, "出どころ": SRC_F7},
    "③-11": {"番号": "③-12", "要素の名前": "玉の向き", "置く記録": "使い方の記録",
             "中身": "その使い方を、どの向きの玉で使うか",
             "形の決まり": {"値の種類": "選べる値から選ぶ", "選べる値の名前": "玉の向き", "複数持てるか": False},
             "無いときの扱い": "既定＝両方", "オン/オフ": "オン", "読むプログラム": [],
             "写す元": "新しく足す（出口の反転と前提崩れの印の4種＝engine_tuner_gen.py の出口の確認の条件が、玉の向きで上側か下側かを選ぶ）",
             "根拠": {"要件の行": [], "構造に要ること": [15], "拡張の条件": []}, "出どころ": SRC_F7},
    "④-8": {"番号": "④-9", "要素の名前": "列を作る組", "置く記録": "部品の記録",
            "中身": "指標の記録の「列を作る組」と同じ形（171番まで）",
            "形の決まり": {"値の種類": "名前の型（文字の並び）・照らす形（文字の並び）・組の並び・並びの番号の並び・照らす形の値の並び・出どころの鍵の並び", "選べる値の名前": None, "複数持てるか": True},
            "無いときの扱い": "未設定（列を作らない部品は空の並び）", "オン/オフ": "オン", "読むプログラム": [],
            "写す元": "記録の「列の名前の型」「列を作る値」と、いまのカタログの並び（observe_diag.build_catalog）",
            "根拠": {"要件の行": ["core_requirements_full.md:55"], "構造に要ること": [], "拡張の条件": []}, "出どころ": SRC_F7},
}
SIDE_CHOICES = ["SHORT", "LONG", "両方"]
AXIS_SRC_OLD = "「列を作る値」（代表の値の候補）「列の名前の型」（171番まで、成績表と列の名前で照らすために軸の並びとして保つ）"
MOVED_TABLES = ("役割の区分の表", "方向から性質への対応の表", "区分の言葉の表（ほかの置き場）")
# ── 部品の記録（④）に写す帯の線の8種と、使う物（監査 CP94 の修正10 案B・まこさん「CCのおすすめでOK」2026-11-01）──────────
#   帯の線は8種とも④（指標の構造の要件定義書 第4章の C「帯の線（上端・縁・中央・下端）・破れの判定・判定の束」）。
#   使う物＝その部品の計算式と、同じ線の関数（呼ぶ関数）を共有する②の記録。②の記録の出力（終値との距離%）を入力に取るのではない
#   （帯VA の計算式は値段と出来高から直接 線を作る＝observe_diag.py:1302・前日VAH の出力は終値との距離%＝:1264）。
#   ★呼ぶ関数は、部品の計算式が直に呼ぶ関数か、その関数がさらに呼ぶ関数に在ることを、写すときに照らす（帯スイングは _band_swing の中で
#     _fractal_marks を呼ぶ＝observe_diag.py:731〜738）。
#   ★1時間ATR の帯の許容幅は、1時間足の ATR ÷ 終値（×100 しない・observe_diag.py:507）× 倍率で作る（_band_tol_1h）。ATR% の記録の出力
#     （×100・列の時間足・observe_diag.py:1102）とは単位も時間足も違う（171番で使う物の出力から帯を組むときに合わせる）。
_VA = [{"指標の記録": "前日VAH", "呼ぶ関数": "_vp_by_day", "使う量": "前日の VAH の線（_vp_by_day の戻り値）"},
       {"指標の記録": "前日VAL", "呼ぶ関数": "_vp_by_day", "使う量": "前日の VAL の線（_vp_by_day の戻り値）"}]
_PV = [{"指標の記録": "前期間pivotR1", "呼ぶ関数": "_pivot_prev_period", "使う量": "前の期間の R1 の線（_pivot_prev_period の戻り値）"},
       {"指標の記録": "前期間pivotS1", "呼ぶ関数": "_pivot_prev_period", "使う量": "前の期間の S1 の線（_pivot_prev_period の戻り値）"}]
_PW = [{"指標の記録": "前週pivotR1", "呼ぶ関数": "_pivot_prev_period", "使う量": "前の週の R1 の線（_pivot_prev_period の戻り値）"},
       {"指標の記録": "前週pivotS1", "呼ぶ関数": "_pivot_prev_period", "使う量": "前の週の S1 の線（_pivot_prev_period の戻り値）"}]
_SW = [{"指標の記録": "fractal高値距離%", "呼ぶ関数": "_fractal_marks", "使う量": "確定した山（_fractal_marks の高値の側）"},
       {"指標の記録": "fractal安値距離%", "呼ぶ関数": "_fractal_marks", "使う量": "確定した谷（_fractal_marks の安値の側）"}]
_ATR = [{"指標の記録": "ATR%", "時間足": "1h", "呼ぶ関数": "_band_tol_1h",
         "使う量": "1時間足の ATR ÷ 終値（×100 しない・observe_diag.py:507）。ATR% の記録の出力（×100・列の時間足・observe_diag.py:1102）と違う"}]
PART_USES = {"帯VA": _VA, "帯VA1時間ATR": _VA + _ATR, "帯pivot": _PV, "帯pivot1時間ATR": _PV + _ATR,
             "帯pivot前週": _PW, "帯pivot前週1時間ATR": _PW + _ATR, "帯スイング": _SW, "帯スイング1時間ATR": _SW + _ATR}
PART_SRC = "observe_diag.py の _BAND_IMPL（帯の計算式の表）と _catalog_from_config の帯の for（161-2 の前は build_catalog の中に在った）"
# ── 部品の記録に足す要素の4行（監査 CP94 の修正8 案B）＝②-5〜②-7・②-9 と同じ形の行を、置く記録を部品の記録にして足す ────────
SRC_CP94 = "監査 CP94（工事 m2c15-indicator-redirect-20261031・まこさん「全部修正する」「CCのおすすめでOK」2026-11-01）"
PART_ROWS = (("②-5", "④-10"), ("②-6", "④-11"), ("②-7", "④-12"), ("②-9", "④-13"))
# ── ②-9・③-5 の写す元の文（監査 CP94 の修正9・修正7＝いまの写し先に合わせる）────────────────────────────────────────
SRC29_ADD = "・161-1 で足した写し先＝閾値の文・閾値の値（調べた結果）・出口の水準・閾値の代表の固定値（スキャル／デイトレ）・コードの中の既定値・名前に出ない軸の最初の値・代表の固定値（スキャル／デイトレ）と範囲（search_limits.json）の元の形（" + SRC_CP94 + "の修正7・修正9）"
SRC35_ADD = "（161-1 では出口の水準の定数を持つ4種だけ。ほかは②-9 に置き、70番〔T-2・T-3〕で③-5 へ写す＝" + SRC_CP94 + "の修正9）"
# ── 向きが逆の軸（資料の表の値と計算式の今の値の向きが違う＝代表の値に写さない・監査 CP94 の修正1・CP91 の修正12・T-3）───────────
REVERSED = {("close vs ALMA%", "distribution_offset"): "offset"}
# ── 使い方の記録（③）＝出口の水準の定数を持つ4種の使い方（engine_tuner_gen.py の _EXIT_LEVEL_CONST と、出口の確認の条件）────
#   反転を見る＝SHORT の玉は下側（売られ過ぎの定数）・LONG は上側／壊れたことを見る＝SHORT は上側・LONG は下側（engine_tuner_gen.py の
#   _exit_confirm の分岐＝「反転を見る＝SHORT の玉は下がり切った側で降りる」「壊れたことを見る＝SHORT の玉は上に振れた側」）
EXIT_USAGES = (("出口の反転", "SHORT", "下側", "lo"), ("出口の反転", "LONG", "上側", "hi"),
               ("前提崩れの印", "SHORT", "上側", "hi"), ("前提崩れの印", "LONG", "下側", "lo"))
EXIT_SRC = "engine_tuner_gen.py の _EXIT_LEVEL_CONST（出口の水準の条件に使える名前つき定数）と、出口の確認の条件（反転を見るとき／壊れたことを見るとき）"
#   上側と下側に同じ定数を使う種類（いまは ADX の ADX_TREND）は、値が向きを持たない＝使い方の記録は、いまのコードの分岐の写しで、
#   教科書の使い方ではない（監査 CP94 の修正20・まこさん「足してよい」2026-11-01・使い方を教科書から決めるのは70番）
EXIT_NOTE_SAME = "・engine_tuner_gen.py の分岐の写し（教科書の使い方ではない・上側と下側に同じ定数を使う＝値が向きを持たない。使い方を教科書から決めるのは70番＝監査 CP94 の修正20）"
# ── 隠れた数字の軸の、意味の対応表（監査 CP91 の修正4＝名前でも並びでも合わないとき、コードの引数の名前 → 資料の表のパラメータの名前で範囲を拾う。
#    今の値が資料の表の範囲の中に在るときだけ拾う。範囲の外なら拾わずに「まだ決めていない」のまま）。対象＝修正4 が名指した8種の軸。
MEANING_MAP = {("Stoch%K", "smooth_k"): "%K の平滑（slow）", ("Stoch%D", "smooth_k"): "%K の平滑（slow）",
               ("EMA傾き", "slope_n"): "slope_lookback_k",
               ("Keltner上", "atr_n"): "ATR の期間", ("Keltner下", "atr_n"): "ATR の期間",
               ("STC", "tcl"): "cycle",
               ("UO", "fast"): "短い本数", ("UO", "medium"): "中の本数", ("UO", "slow"): "長い本数",
               ("PSAR加速", "af0"): "step（開始値と増やす幅）", ("PSAR加速", "af"): "step（開始値と増やす幅）", ("PSAR加速", "max_af"): "maximum"}
MEANING_SRC = "indicator_params_by_strategy.json の範囲（意味の対応表で拾った＝監査 CP91 の修正4・まこさん「修正はすべて」2026-10-29）"


def jload(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:                                   # noqa: BLE001
        raise SystemExit(f"❌ 写す元のファイルが読めない: {p}（{e}）")


sys.path.insert(0, str(PR))
_cwd = os.getcwd()
os.chdir(PR)
with contextlib.redirect_stdout(io.StringIO()):
    import indicator_reference_diag as iref  # noqa: E402
    import observe_diag as od  # noqa: E402
os.chdir(_cwd)
TABLE = iref.INDICATOR_TABLE
# CP88 の修正10＝別枠の材料（INDICATOR_TABLE の301種に無い種類）の定義の表。名前 → (群, 定義)。群はオン/オフの鍵と計算の関数を選ぶのに使う
EXTRA = {"レンジ幾何": iref.RANGE_GEO_REF, "需給": iref.DEMAND_REF, "時間帯": iref.TIME_REF}


def _carry(tb: dict) -> dict:
    """定義の表の「同上」を、表の並びで1つ前の行の値に置き換える（記録は1種ずつ読むので「同上」では読めない・CP89）。"""
    out, prev = {}, {}
    for nm, d in tb.items():
        e = {k: (prev.get(k, v) if v == "同上" else v) for k, v in d.items()}
        out[nm], prev = e, e
    return out


_dup = sorted(nm for nm in {n for tb in EXTRA.values() for n in tb} if sum(nm in tb for tb in EXTRA.values()) > 1)
if _dup:
    raise SystemExit(f"❌ 別枠の材料の名前が、別枠の表どうしで重なる: {_dup}")
EXTRA_OF = {nm: (grp, d) for grp, tb in EXTRA.items() for nm, d in _carry(tb).items()}


def module_assign(path: Path, name: str):
    """ファイルの一番外の代入 name の右辺を、ast で開いて値にする（import しない）。返り値＝(値, 行)。"""
    for n in ast.parse(path.read_text(encoding="utf-8")).body:
        tg = n.targets if isinstance(n, ast.Assign) else [n.target] if isinstance(n, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == name for t in tg):
            return ast.literal_eval(n.value), n.lineno
    raise SystemExit(f"❌ 写す元が読めない＝{path.name} に {name} の代入が無い")


def plain(x):
    """json に書ける形にする（関数は名前、正規表現は型の文字、組は一覧）。"""
    if isinstance(x, re.Pattern):
        return x.pattern
    if callable(x):
        return getattr(x, "__name__", repr(x))
    if isinstance(x, dict):
        return {str(k): plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, set, frozenset)):
        return [plain(v) for v in (sorted(x, key=str) if isinstance(x, (set, frozenset)) else x)]
    if isinstance(x, (str, int, float, bool)) or x is None:
        return x
    return repr(x)


def src_text(fn) -> str:
    try:
        return inspect.getsource(fn).strip()
    except (OSError, TypeError):
        return repr(fn)


def called(fn) -> list:
    """lambda の中で呼ぶ関数の名前（観察の道具と定義表の、一番外に在る関数だけ）。"""
    code = getattr(fn, "__code__", None)
    if code is None:
        return []
    out = []
    for nm in code.co_names:
        for m in (od, iref):
            f = getattr(m, nm, None)
            if inspect.isfunction(f) and nm not in out:
                out.append(nm)
    return out


def defaults(fn) -> dict:
    """呼ぶ関数の引数の既定値と、式の中に直に書いた数（4-8 の「コードの中の既定値」）。"""
    def sig(f):
        try:
            return {k: v.default for k, v in inspect.signature(f).parameters.items() if v.default is not inspect.Parameter.empty}
        except (TypeError, ValueError):
            return {}
    d = {}
    own = sig(fn)                                             # lambda 自身の引数（None＝呼ぶライブラリの既定値を使う）
    if own:
        d["<lambda>"] = plain(own)
    for nm in called(fn):
        ps = sig(getattr(od, nm, None) or getattr(iref, nm, None))
        if ps:
            d[nm] = plain(ps)
    code = getattr(fn, "__code__", None)
    gl = getattr(fn, "__globals__", {})
    codes, i = ([code] if code else []), 0                    # 中の lambda（例 HT_DCPHASE の _cyc に渡す lambda）も見る
    while i < len(codes):
        codes += [c for c in codes[i].co_consts if inspect.iscode(c)]
        i += 1
    names = [nm for c in codes for nm in c.co_names]
    for nm in names:                                          # 呼ぶライブラリの関数（例 _pta6.uo）の引数の既定値
        mod = gl.get(nm)
        if inspect.ismodule(mod):
            for attr in names:
                f = getattr(mod, attr, None)
                if callable(f) and not inspect.isclass(f):
                    ps = sig(f)
                    if ps:
                        d[f"{nm}.{attr}"] = plain(ps)
    nums = [k for c in codes for k in c.co_consts if isinstance(k, (int, float)) and not isinstance(k, bool)]
    return {"引数の既定値": d, "式の中の数": nums}


_RESOLVE: dict = {}


def resolve(s):
    """文字 → 種類の名前（表の名前そのもの、または列の名前を定義表の find でたどった種類）。当たらなければ None。"""
    if not isinstance(s, str):
        return None
    if s not in _RESOLVE:
        e, _p = iref.find(s)
        _RESOLVE[s] = s if (s in TABLE or s in EXTRA_OF) else (e["family"] if e else None)
    return _RESOLVE[s]


def kinds_in(v) -> set:
    if isinstance(v, str):
        k = resolve(v)
        return {k} if k else set()
    if isinstance(v, dict):
        return set().union(*(kinds_in(k) | kinds_in(x) for k, x in v.items())) if v else set()
    if isinstance(v, (list, tuple, set, frozenset)):
        return set().union(*(kinds_in(x) for x in v)) if v else set()
    return set()


def narrow(v, kind):
    """値のうち、その種類に当たる所だけを残す（辞書は鍵が種類なら値ごと・一覧は種類を含む要素ごと）。"""
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if resolve(k) == kind:
                out[k] = x
            elif kind in kinds_in(x):
                out[k] = narrow(x, kind)
        return out
    if isinstance(v, (list, tuple, set, frozenset)):
        return [x for x in v if (resolve(x) == kind if isinstance(x, str) else kind in kinds_in(x))]
    return v


def norm(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True)


def decide(t: dict, role_table: dict, prop_table: dict):
    """札と性質を、2つの表から決める（F-7）。表に無い区分・方向は、止める物として返す。返り値＝(札, 性質の一覧, 無い区分, 無い方向)。
    札は、区分が在る種類だけを表から決める（区分が2つ以上なら、いまの札に合う区分＝gen_indicator_table.py の compute と同じ決め方）。"""
    cats = t["役割"]["区分"] or []
    miss_role = [c for c in cats if c not in role_table]
    cands = [role_table[c]["札"] for c in cats if c in role_table]
    lin = (t["札"] if t["札"] in cands else cands[0]) if cands else t["札"]
    hk = t["方向"]["区分"]
    miss_dir = [] if hk in prop_table else [hk]
    return lin, list(prop_table.get(hk, {}).get("性質", [])), miss_role, miss_dir


def nums(x):
    """パラメータの値の並びを、数の組の一覧にそろえる（値の食い違いの一覧と同じ比べ方）。"""
    if x is None:
        return None
    return sorted(tuple(v) if isinstance(v, list) else (v,) for v in (x if isinstance(x, list) else [x]))


# ══ 直す相手の一覧の「①写す」の行（4-4 の9）════════════════════════════════════════════════
def inventory() -> list:
    """全部の行の節（669行）・拾えなかった行の節・json の節・古い鍵の節から、「①写す」の行を読む。"""
    rows, sec = [], ""
    for ln in INV.read_text(encoding="utf-8").splitlines():
        if ln.startswith("## "):
            sec = ln[3:]
            continue
        if not ln.startswith("| ") or ln.startswith("|---"):
            continue
        c = [x.strip() for x in ln.strip().strip("|").split("|")]
        if sec.startswith("全部の行") and len(c) == 5 and c[4].startswith("①写す"):
            rows.append(dict(節="全部の行", ファイル=c[0], 行=c[1], 中身=c[3]))
        elif sec.startswith("エージェントの行で") and len(c) == 7 and c[6].startswith("①写す"):
            rows.append(dict(節="拾えなかった行", ファイル=c[0], 行=c[1], 中身=c[3]))
        elif sec.startswith("json") and len(c) == 4 and c[3].startswith("①写す"):
            rows.append(dict(節="json", ファイル=c[0], 行="", 中身=c[1]))
        elif sec.startswith("observe_config.json の古い鍵") and len(c) == 3 and c[0] != "鍵":
            rows.append(dict(節="古い鍵", ファイル="observe_config.json", 行="", 中身=c[0]))
    return rows


def row_name(r) -> str:
    m = re.match(r"`?\(?\s*([A-Za-z_]\w*)", r["中身"])
    return m.group(1) if m else ""


def row_target(r) -> str:
    """一覧の行の、置き場の名前の全部（例＝`sel['geo']`・`(res_lo, res_hi, sup_lo, sup_h`＝一覧は30字で切る）。"""
    return r["中身"].split("（")[0].strip().strip("`")


def _ntext(s: str) -> str:
    """置き場の名前を比べる形（空白と括弧を除く）。"""
    return re.sub(r"[\s()]", "", str(s))


def _same_target(have: str, want: str) -> bool:
    """実物の代入の相手（have）が、一覧の行の名前（want）か。一覧が30字で切っていれば、頭が合えばよい。"""
    h, w = _ntext(have), _ntext(want)
    return h == w or (len(want) >= 28 and h.startswith(w))


_AST: dict = {}


def parsed(path: Path):
    if not path.exists():
        raise SystemExit(f"❌ 写す元のファイルが読めない: {path}")
    if path not in _AST:
        text = path.read_text(encoding="utf-8")
        _AST[path] = (text, ast.parse(text))
    return _AST[path]


def row_line(r) -> int:
    return int(re.split(r"[-〜]", r["行"])[0])


def enclosing_fn(tree, line: int):
    """その行を含む、いちばん内側の関数（無ければ None）。"""
    best = None
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.lineno <= line <= n.end_lineno:
            if best is None or (n.end_lineno - n.lineno) < (best.end_lineno - best.lineno):
                best = n
    return best


def in_selftest(r) -> bool:
    """その行が、自己テストの関数（一番外の関数で、名前が selftest で始まる物）の中か。
    見本は記録に写す物ではない（worklog 20261024:357 の決定）。"""
    _text, tree = parsed(PR / r["ファイル"])
    lo = row_line(r)
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("selftest")
               and n.lineno < lo <= n.end_lineno for n in tree.body)


def row_kind(r) -> str:
    """その行が、記録のどの欄で写されるか（決まった欄・json・古い鍵・自己テストの見本・ほかの置き場）。"""
    if r["節"] == "古い鍵":
        return "古い鍵"
    if r["節"] == "json":
        return "json"
    if "設定の鍵から読まない" in r["中身"]:
        return "コードの中の既定値"
    if row_name(r) in OWN:
        return "決まった欄"
    return "自己テストの見本" if in_selftest(r) else "ほかの置き場"


def _target_text(n) -> str:
    """代入の相手の文字（一覧を作るプログラムと同じ ast.unparse の形）。"""
    if isinstance(n, ast.Assign):
        return ", ".join(ast.unparse(t) for t in n.targets)
    if isinstance(n, ast.AnnAssign):
        return ast.unparse(n.target)
    if isinstance(n, ast.keyword):
        return n.arg or ""
    return ""


def _assigns_named(node, target: str) -> list:
    """node の中（入れ子の関数の中は除く）で、target（代入の相手の名前＝名前・組・添字つき）へ代入する文と、同じ名前のキーワード引数。"""
    out = []
    stack = list(ast.iter_child_nodes(node))
    while stack:
        n = stack.pop(0)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue                                          # 別の関数の中は、その関数の置き場
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.keyword)) and _same_target(_target_text(n), target):
            out.append(n)
        stack += list(ast.iter_child_nodes(n))
    return sorted(out, key=lambda n: n.lineno)


def find_by_name(path: Path, name: str, lo: int, hi: int, ordinal: int, n_same: int) -> list:
    """「①写す」の行の置き場を、行の範囲でなく名前で探す（やることの表 F-2・4-5）。返り値＝置き場の文（1つ以上）。
    探す範囲＝一覧の行が関数の中なら、その関数の中。外なら、ファイルの一番外（関数の中は除く）。
    0か所＝止まる。2か所以上＝一覧に同じ名前の行が同じ数だけ在れば、行の順に対応させる。違えば止まる。
    ★名前が関数の名前のとき（例＝engine_tuner_exec.py の「_check_cond の時刻の範囲」）＝その関数の中で、一覧の行の範囲に掛かる文（一番外の物）。"""
    _text, tree = parsed(path)
    scope = enclosing_fn(tree, lo)
    nodes = _assigns_named(scope if scope is not None else tree, name)
    where = f"{path.name}:{lo} {name}（{'関数 ' + scope.name + ' の中' if scope is not None else 'ファイルの一番外'}）"
    if not nodes:
        m = re.match(r"[A-Za-z_]\w*", name.strip())
        fname = m.group(0) if m else ""
        fdefs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fname]
        if len(fdefs) == 1:
            fd = fdefs[0]
            cand = [n for n in ast.walk(fd) if isinstance(n, (ast.stmt, ast.keyword)) and lo <= getattr(n, "lineno", 0) <= hi and n is not fd]

            def inside(n, m):
                if m is n or not (m.lineno <= n.lineno and n.end_lineno <= m.end_lineno):
                    return False
                sm, sn = m.end_lineno - m.lineno, n.end_lineno - n.lineno
                return sm > sn or (sm == sn and isinstance(m, ast.stmt) and isinstance(n, ast.keyword))
            starts = sorted((n for n in cand if not any(inside(n, m) for m in cand)), key=lambda n: n.lineno)
            if starts:
                return starts
            raise SystemExit(f"❌ 置き場が見つからない（関数 {name} は在るが、一覧の行 {lo}〜{hi} に文が無い＝行がずれた）: {where}")
        # ★一覧の行の関数（古い行の番号で決めた範囲）に無いときは、ファイル全体（全部の関数と一番外）を名前で探す。
        #   1か所なら写し、2か所以上なら止まる（別の関数の同じ名前の代入を黙って写さない＝監査 CP94 の修正13）
        alln = sorted((n for n in ast.walk(tree) if isinstance(n, (ast.Assign, ast.AnnAssign, ast.keyword)) and _same_target(_target_text(n), name)),
                      key=lambda n: n.lineno)
        if len(alln) == 1:
            return alln
        if len(alln) >= 2:
            raise SystemExit(f"❌ 置き場が2つ以上（一覧の行の範囲に無く、ファイル全体で同じ名前の代入が {len(alln)} か所）: {where}")
        raise SystemExit(f"❌ 置き場が見つからない（名前で探した・行がずれたか、名前が変わった）: {where}")
    if len(nodes) == 1:
        return [nodes[0]]
    exact = [n for n in nodes if n.lineno == lo]              # 一覧が新しい（行がずれていない）なら、行で1つに決まる
    if len(exact) == 1:
        return exact
    if len(nodes) == n_same and ordinal < len(nodes):
        return [nodes[ordinal]]
    raise SystemExit(f"❌ 置き場が2つ以上（同じ名前への代入が {len(nodes)} か所・一覧の行は {n_same} 行・行 {lo} に当たる物も無い）: {where}")


def code_copy(r, ordinal: int = 0, n_same: int = 1) -> list:
    """「①写す」の行の置き場を名前で探し、ast で開いて写す。返り値＝[{置き場, 名前, 値, 種類}]。"""
    path = PR / r["ファイル"]
    text, tree = parsed(path)
    lines = text.splitlines()
    name = row_target(r)
    lo, hi = (int(x) for x in (re.split(r"[-〜]", r["行"]) + [r["行"]])[:2])
    if r["節"] == "拾えなかった行":
        # エージェントの報告の行（文は報告のまま＝「MAKO_K3・K7・K3B・B1S1・K3C」「direction_conflict DC1-4」のように、名前が略されている・
        # 名前の後ろに説明が付く）＝文の中の名前の語を1つずつ探す。略された名前は、1つ目の名前の頭（MAKO_）を付けて探す。
        toks = re.findall(r"[A-Za-z_]\w*", r["中身"].split("[")[0])
        scope = enclosing_fn(tree, lo)
        nodes, pre = [], (toks[0].rsplit("_", 1)[0] + "_" if toks and "_" in toks[0] else "")
        for tok in toks:
            got = _assigns_named(scope if scope is not None else tree, tok) or (_assigns_named(scope if scope is not None else tree, pre + tok) if pre else [])
            nodes += [n for n in got if n not in nodes]
        if not nodes and toks:
            nodes = find_by_name(path, toks[0], lo, hi, 0, 1)
        if not nodes:
            raise SystemExit(f"❌ 置き場が見つからない（報告の行の名前の語で探した）: {r['ファイル']}:{r['行']} {r['中身'][:40]}")
        nodes = sorted(nodes, key=lambda n: n.lineno)
    else:
        nodes = find_by_name(path, name, lo, hi, ordinal, n_same)
    out = []
    for n in nodes:
        val = None
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.keyword)) and getattr(n, "value", None) is not None:
            with contextlib.suppress(ValueError, SyntaxError, TypeError):
                val = ast.literal_eval(n.value)
        if val is None:
            val = "\n".join(lines[n.lineno - 1:n.end_lineno])
            strs = [c.value for c in ast.walk(n) if isinstance(c, ast.Constant) and isinstance(c.value, str)]
            kinds = kinds_in(strs)
        else:
            kinds = kinds_in(val)
        nm = _target_text(n) or name
        out.append(dict(置き場=f"{r['ファイル']}:{n.lineno}", 名前=nm, 値=plain(val), 種類=sorted(kinds)))
    return out


def json_copy(r) -> list:
    """json の行のうち、決まった欄に入らない鍵を写す。"""
    js = jload(JSON_PATH[r["ファイル"]])
    out = []
    for key in [t.split()[0] for t in r["中身"].split("・")]:
        if key in JSON_OWN.get(r["ファイル"], set()):
            continue
        val = js if key.startswith("[]") else js.get(key)
        out.append(dict(置き場=f"{r['ファイル']} の {key}", 名前=key, 値=plain(val), 種類=sorted(kinds_in(val))))
    return out


# ══ 1 いまの置き場から、23の欄の形で集める（設計書1の 4-4 の1〜11＝変えない）═══════════════════════════════════════
def build_old() -> tuple:
    """いまの置き場から、23の欄の形で集める。返り値＝(記録, 役割の区分の表, 方向から性質への対応の表, 区分の言葉の表, 「①写す」の行)。"""
    cfg = jload(PR / "observe_config.json")
    mp, first_hidden = cfg.get("material_params", {}), cfg.get("material_first_hidden", {})
    lim = jload(PR / "recipes/search_limits.json").get("material_param_ranges", {})
    sw = jload(SDK / ".claude/ratchet/indicator_switch.json")
    on, off = set(sw.get("on", [])), set(sw.get("off", []))
    roles = {x["種類"]: x for x in jload(ST / "indicator_roles_thresholds.json")}
    bys = {x["種類"]: x for x in jload(ST / "indicator_params_by_strategy.json")["指標"]}
    rev = {x["種類"]: x for x in jload(ST / "indicator_params_review.json")}
    outw = {x["種類"]: x for i in range(1, 5) for x in jload(HERE / f"research/out_w{i}.json")}
    trole = {x["種類"]: x for x in jload(HERE / "research/threshold_role.json")}
    mat = jload(SDK / ".claude/ratchet/materials.json")["body"]
    mrows, mper = {x.get("名前"): x for x in mat.get("rows", [])}, mat.get("engine", {}).get("期間", {})
    cat2lin, ln_c = module_assign(PR / "gen_indicator_table.py", "CAT2LIN")
    h2p, ln_h = module_assign(PR / "gen_indicator_table.py", "HOUKOU2PROP")
    exit_lv, _ln = module_assign(PR / "engine_tuner_gen.py", "_EXIT_LEVEL_CONST")
    v9map, _ln = module_assign(PR / "gen_signal_families.py", "V9_FAMILY_MAP")

    # 2つの表（F-7）＝区分と対応は、プログラムの中に書かず、いまの値から1回だけ写す
    role_table = {k: dict(札=v, 出どころ=f"gen_indicator_table.py:{ln_c} の CAT2LIN") for k, v in cat2lin.items()}
    prop_table = {k: dict(性質=[v], 出どころ=f"gen_indicator_table.py:{ln_h} の HOUKOU2PROP") for k, v in h2p.items()}
    prop_table.update(copy.deepcopy(DECIDED_PROP))

    # 3 計算の登録 → 種類（F-5＝名前の違う種類も、表の名前1つにそろえる。つながらない登録が在れば止まる）
    regs, unmapped = {}, []
    for rf, (tpl, directional, fn) in od.MATERIAL_FAMILIES.items():
        fam = None
        for combo in itertools.product(["14", "2.0", "3", "0.5"], repeat=tpl.count("{}")):
            fam = resolve(tpl.format(*combo))
            if fam:
                break
        if fam is None:
            unmapped.append(rf)
            continue
        regs.setdefault(fam, []).append((rf, tpl, directional, fn))
    if unmapped:
        raise SystemExit(f"❌ 計算の登録の名前が、INDICATOR_TABLE の名前1つにつながらない: {unmapped}")
    refs = {}
    for e in iref.REFS:
        refs.setdefault(e["family"], []).append(e)

    # 4 列を作る値＝いまのカタログの列を、定義表の find でたどった値。出どころの鍵は、鍵を1つずつ空にして列が減る種類で決める
    def cols(c):
        got = {}
        # ★2026-11-01（工事 m2c15-catalog-redirect-20261101・やることの表 F-4）＝写す元は、設定から列を作る _catalog_from_config（162番まで）。
        #   build_catalog は読む口の列を作る組から作るので、写す元にすると indicators.json を indicators.json から作ることになる。
        for nm, _f, _d in od._catalog_from_config(c):
            e, p = iref.find(nm)
            if e:
                got.setdefault(e["family"], set()).add(tuple(p or ()))
        return got
    base = cols(cfg)
    cfg0 = copy.deepcopy(cfg)
    cfg0["material_params"] = {}
    cfg0["drop_columns"] = type(cfg0.get("drop_columns", []))()
    base0 = {k: len(v) for k, v in cols(cfg0).items()}
    keydep = {}
    for k, v in cfg0.items():
        if k.startswith("_") or k in ("material_params", "drop_columns") or not isinstance(v, (list, dict)) or not v:
            continue
        c2 = copy.deepcopy(cfg0)
        c2[k] = type(v)()
        try:
            now = cols(c2)
        except (Exception, SystemExit):                      # noqa: BLE001  空にすると止まる鍵は、その種類の出どころにしない
            continue
        for f, n in base0.items():
            if len(now.get(f, ())) < n:
                keydep.setdefault(f, []).append(k)

    v9_other = getattr(od, "_V9_LABEL_TO_FAMILIES", {})
    ta_names = set(iref.TA_CLASS_MAP)
    recs, unknown_role, unknown_dir = {}, [], []
    for f in sorted(TABLE):
        t = TABLE[f]
        fr, fg = refs.get(f, []), regs.get(f, [])
        lin, props, miss_role, miss_dir = decide(t, role_table, prop_table)
        if miss_role:
            unknown_role.append((f, miss_role))
        if miss_dir:
            unknown_dir.append((f, miss_dir[0]))
        mreg = [rf for rf, *_x in fg]
        src_keys = ((["observe_config.json の material_params"] if (f in mp or any(x in mp for x in mreg)) else [])
                    + keydep.get(f, [])) or ["計算の関数の中（設定の鍵から読まない）"]
        b, rv, ro = bys.get(f) or {}, rev.get(f) or {}, roles.get(f) or {}
        conflicts = []

        def conflict(field, chosen, where, others, skip_empty=True):
            """選んだ値と違う置き場の値を残す（選んだ値が空のときは比べない＝値の食い違いの一覧と同じ比べ方）。"""
            if skip_empty and chosen in (None, "", []):
                return
            got = {k: v for k, v in others.items() if v not in (None, "", []) and norm(v) != norm(chosen)}
            if got:
                conflicts.append(dict(欄=field, 選んだ値=chosen, 選んだ置き場=where, 選ばなかった=got))

        conflict("系統", lin, "INDICATOR_TABLE の札（役割の区分の表で決めた）",
                 {"roles の今の系統": ro.get("今の系統"), "by_strategy の系統": b.get("系統"), "review の系統": rv.get("系統"),
                  "materials の系統": (mrows.get(f) or {}).get("系統")})
        made = sorted(base.get(f, set()))
        conflict("列を作る値", nums([list(x) for x in made]), "いまのカタログの列（observe_config.json）",
                 {"observe_config の material_params": nums(mp.get(f)), "by_strategy の今の値": nums(b.get("今の値")),
                  "review の今のパラメータの組": nums(rv.get("今のパラメータの組")), "materials の期間": nums(mper.get(f))})
        conflict("範囲", [[d.get("lo"), d.get("hi")] for d in lim.get(f) or []] or None, "search_limits.json の material_param_ranges",
                 {"by_strategy の範囲": [[d.get("下限"), d.get("上限")] for d in b.get("範囲") or []]}, skip_empty=False)
        state = "オン" if f in on else "オフ" if f in off else "どちらにも無い"
        eng = (mrows.get(f) or {}).get("engine_tuner")
        if state == "オン" and (eng is None or not str(eng).startswith("選べる")):
            conflicts.append(dict(欄="オン/オフ", 選んだ値=state, 選んだ置き場="indicator_switch.json",
                                  選ばなかった={"materials の engine_tuner": eng}))
        conflict("性質", props, "方向から性質への対応の表", {"INDICATOR_TABLE の性質": [t["性質"]] if t["性質"] else None})
        v9 = sorted(lab for lab, fams in v9map.items() if f in fams)
        conflict("V9 の名前", v9, "gen_signal_families.py の V9_FAMILY_MAP",
                 {"observe_diag.py の _V9_LABEL_TO_FAMILIES": sorted(lab for lab, fams in v9_other.items() if f in fams)},
                 skip_empty=False)
        ta_have = sorted(c for c, ks in iref.TA_CLASS_MAP.items() if f in ks)
        ta_used = sorted({nm for e in fr for nm in getattr(getattr(e.get("ext"), "__code__", None), "co_names", ())} & ta_names)
        if set(ta_used) - set(ta_have):                     # 照合で使う ta のクラスが、TA_CLASS_MAP ではこの種類に向いていない
            conflicts.append(dict(欄="ライブラリとの対応", 選んだ値=ta_have, 選んだ置き場="indicator_reference_diag.py の TA_CLASS_MAP",
                                  選ばなかった={"照合の関数 ext が使う ta のクラス": ta_used}))
        recs[f] = {
            "名前": f,
            "列の名前の型": dict(照らす形=[e["pat"].pattern for e in fr], 列を作る形=[tpl for _rf, tpl, *_x in fg]),
            "計算の関数": [dict(登録の名前=rf, 名前の型=tpl, 向きを持つ=d, 関数の名前=called(fn), 式の文=src_text(fn))
                       for rf, tpl, d, fn in fg],
            "照合の関数・既知答え": [dict(定義=e.get("teigi"), 流儀=e.get("ryugi"), tb=plain(e.get("tb")), ext=plain(e.get("ext")),
                                  known=src_text(e["known"]) if callable(e.get("known")) else plain(e.get("known")),
                                  tol=e.get("tol"), tb_kind=e.get("tb_kind")) for e in fr],
            "代表の固定値（スキャル／デイトレ）": dict(スキャル=b.get("最初の値（スキャル）"), デイトレ=b.get("最初の値（デイトレ）")),
            "名前に出ない軸の最初の値": first_hidden.get(f),
            "列を作る値": dict(値=[list(x) for x in made], 出どころ=src_keys),
            "コードの中の既定値": {rf: defaults(fn) for rf, _tpl, _d, fn in fg},
            "範囲": lim.get(f),
            "役割・札・値域・注記": dict(役割=t["役割"], 札=lin, 値域=t["値域"], 注記=t.get("注記", "")),
            "方向・性質": dict(方向=t["方向"], 性質=props),
            "オン/オフ": dict(状態=state, 源=sorted(k for k, v in (sw.get("sources") or {}).items() if f in v)),
            "mako": next((e["mako"] for e in fr if e.get("mako")), None),
            "ライブラリとの対応": dict(INDUSTRY_MAP=plain(iref.INDUSTRY_MAP.get(f)), TA_CLASS_MAP=ta_have,
                                 EXT2=plain(iref.EXT2.get(f))),
            "出口の水準": list(exit_lv.get(f) or []) or None,
            "V9 の名前": v9,
            "教科書の出どころ": dict(review=rv or None, roles=ro or None,
                                 by_strategy={k: v for k, v in b.items() if k not in
                                              ("種類", "系統", "今の値", "最初の値（スキャル）", "最初の値（デイトレ）", "範囲")} or None),
            "閾値の値": dict(定数={c: plain(iref.CONST_REGISTRY[c]) for c in (exit_lv.get(f) or []) if c in iref.CONST_REGISTRY},
                          調べた結果={k: v for k, v in (outw.get(f) or {}).items() if k != "種類"} or None),
            "閾値の文": {k: v for k, v in (trole.get(f) or {}).items() if k != "種類"} or None,
            "閾値の代表の固定値（スキャル／デイトレ）": dict(スキャル=None, デイトレ=None),   # CP88 の修正11＝値は T-2・T-3 で埋める
            "閾値の範囲": None,
            "食い違いの記録": conflicts,
            "ほかの置き場の値": [],
        }
        if list(recs[f]) != list(OLD_FIELDS):
            raise SystemExit(f"❌ {f} の記録の欄が、設計書1の 4-8 の23の欄と違う")

    # CP88 の修正10＝別枠の材料の13種の記録。値は定義の表（RANGE_GEO_REF・DEMAND_REF・TIME_REF）・FAMILY_LINEAGE・indicator_switch.json から写す。
    #   時間帯の2種は、計算が engine_tuner_exec.py の _col_array の中に在る（関数として切り出すのは設計書2）ので、計算の関数の欄は空
    calc_fn = {"レンジ幾何": od.build_range_geometry, "需給": od.load_demand, "時間帯": None}
    known_fn = {"レンジ幾何": "range_geo_known_check（indicator_reference_diag.py）"}
    for f, (grp, d) in sorted(EXTRA_OF.items()):
        if f in recs:
            raise SystemExit(f"❌ 別枠の材料の名前 {f} が、INDICATOR_TABLE の名前と重なる")
        fn = calc_fn[grp]
        state = "オン" if f in set(sw.get({"レンジ幾何": "geo_on", "需給": "demand_on", "時間帯": "time_on"}[grp], [])) else "オフ"
        recs[f] = {
            "名前": f,
            "列の名前の型": dict(照らす形=[], 列を作る形=[]),
            "計算の関数": [dict(登録の名前=None, 名前の型=None, 向きを持つ=None, 関数の名前=[fn.__name__], 式の文=src_text(fn))] if fn else [],
            "照合の関数・既知答え": [dict(定義=d.get("teigi"), 流儀=d.get("ryugi"), tb=None, ext=None, known=known_fn.get(grp),
                                  tol=None, tb_kind=None)],
            "代表の固定値（スキャル／デイトレ）": dict(スキャル=None, デイトレ=None),
            "名前に出ない軸の最初の値": None,
            "列を作る値": dict(値=[], 出どころ=[]),
            "コードの中の既定値": {},
            "範囲": None,
            "役割・札・値域・注記": dict(役割=None, 札=(iref.FAMILY_LINEAGE.get(f) or iref.FAMILY_LINEAGE.get(grp) or {}).get("k"),
                                   値域=dict(種別=d["kind"]) if d.get("kind") else None, 注記=""),
            "方向・性質": dict(方向=dict(区分=(d.get("houkou") or "").split("＝")[0] or None, 読み方=d.get("houkou")), 性質=[]),
            "オン/オフ": dict(状態=state, 源=sorted(k for k, v in (sw.get("sources") or {}).items() if f in v)),
            "mako": d.get("mako"),
            "ライブラリとの対応": None,
            "出口の水準": None,
            "V9 の名前": [],
            "教科書の出どころ": dict(source=d["source"]) if d.get("source") else None,
            "閾値の値": dict(定数={}, 調べた結果=None),
            "閾値の文": None,
            "閾値の代表の固定値（スキャル／デイトレ）": dict(スキャル=None, デイトレ=None),
            "閾値の範囲": None,
            "食い違いの記録": [],
            "ほかの置き場の値": [],
        }
        if list(recs[f]) != list(OLD_FIELDS):
            raise SystemExit(f"❌ {f} の記録の欄が、設計書1の 4-8 の23の欄と違う")
    # CP89 の修正1＝別枠の材料と時刻の、直す相手の一覧に無いパラメータと閾値の置き場を写す（読むだけ・ast で開く）
    dash = SDK / "scripts/dashboard"
    geo_params = []
    for p, nm in ((PR / "e37_scalp.py", "V25_K"), (dash / "build_range_gate_dashboard.py", "ZONE_TOL"),
                  (dash / "build_range_gate_dashboard.py", "ZONE_TOUCH"), (dash / "build_range_gate_dashboard.py", "ZONE_LOOKBACK")):
        v, ln = module_assign(p, nm)
        geo_params.append(dict(置き場=f"{p.relative_to(SDK / 'scripts').as_posix()}:{ln}", 名前=nm, 値=v))
    for n in ast.parse((dash / "build_regime_gate_rg.py").read_text(encoding="utf-8")).body:
        if isinstance(n, ast.FunctionDef) and n.name == "_adaptive_tol_1h":
            a = n.args
            geo_params.append(dict(置き場=f"dashboard/build_regime_gate_rg.py:{n.lineno}", 名前="_adaptive_tol_1h の引数の既定値",
                                   値={x.arg: ast.literal_eval(d) for x, d in zip(a.args[len(a.args) - len(a.defaults):], a.defaults)}))
    if len(geo_params) != 5:
        raise SystemExit("❌ レンジ幾何のパラメータの置き場が読めない（build_regime_gate_rg.py に _adaptive_tol_1h が無い）")
    for f, (grp, _d) in EXTRA_OF.items():
        if grp == "レンジ幾何":
            recs[f]["ほかの置き場の値"] += copy.deepcopy(geo_params)
    recs["時刻"]["閾値の範囲"] = [dict(jload(PR / "recipes/search_limits.json")["hour_range"],
                                   出どころ="recipes/search_limits.json の hour_range（engine_tuner_exec.py:1057〜1066）")]
    if unknown_dir:
        raise SystemExit("❌ 方向が、方向から性質への対応の表に無い種類が在る（表に1行を足すと通る）: "
                         + "・".join(f"{f}（{h}）" for f, h in unknown_dir))
    if unknown_role:
        raise SystemExit("❌ 役割の区分が、役割の区分の表に無い種類が在る（表に1行を足すと通る）: "
                         + "・".join(f"{f}（{'・'.join(m)}）" for f, m in unknown_role))
    if len(recs) != len(TABLE) + len(EXTRA_OF):
        raise SystemExit(f"❌ 記録の数 {len(recs)} が、INDICATOR_TABLE の種類の数 {len(TABLE)} と別枠の材料の数 {len(EXTRA_OF)} の和と合わない")

    # 9 直す相手の一覧の「①写す」の行のうち、決まった欄に入らない置き場を写す（置き場は名前で探す＝F-2）
    rows = inventory()
    others = {}                                               # 置き場 → 写した物（同じ置き場が2つの節に出ても1回だけ写す）
    same = {}                                                 # (ファイル, 名前, 関数) → その名前の行の並び（2か所以上のときの対応）
    for r in rows:
        if row_kind(r) == "ほかの置き場":
            _t, tree = parsed(PR / r["ファイル"])
            fn = enclosing_fn(tree, row_line(r))
            same.setdefault((r["ファイル"], _ntext(row_target(r)), fn.name if fn else ""), []).append(r["行"])
    for r in rows:
        k = row_kind(r)
        if k == "ほかの置き場":
            _t, tree = parsed(PR / r["ファイル"])
            fn = enclosing_fn(tree, row_line(r))
            key = (r["ファイル"], _ntext(row_target(r)), fn.name if fn else "")
            got = code_copy(r, same[key].index(r["行"]), len(same[key]))
        elif k == "json":
            got = json_copy(r)
        else:
            got = []
        for o in got:
            others.setdefault(o["置き場"], o)
    kubun = []
    for o in others.values():
        if not o["種類"]:
            kubun.append({x: o[x] for x in ("置き場", "名前", "値")})
        for f in o["種類"]:
            val = narrow(o["値"], f) if not isinstance(o["値"], str) else o["値"]
            recs[f]["ほかの置き場の値"].append(dict(置き場=o["置き場"], 名前=o["名前"], 値=val))
    recs = json.loads(json.dumps(recs, ensure_ascii=False, default=repr))
    return recs, role_table, prop_table, kubun, rows


# ══ 2 要素の定義表（F-7＝3行と選べる値を足し、3つの表を「選べる値」の下へ移す）══════════════════════════════════════
def read_table() -> dict:
    """いまの indicators.json の要素の定義表（古い形でも新しい形でも、一番外に在る）。無ければ止まる。"""
    if not OUT.exists():
        raise SystemExit(f"❌ {OUT} が無い（192番の工事で要素の定義表を足した indicators.json が要る）")
    have = jload(OUT)
    if "要素の定義表" not in have:
        raise SystemExit(f"❌ {OUT} に要素の定義表が無い（192番の工事の承認と実装が先）")
    return have


def table_update(table: dict, role_table: dict, prop_table: dict, kubun: list) -> dict:
    """F-7＝要素の定義表に ②-12・③-12・④-9 を足し、選べる値に「玉の向き」を足し、3つの表を「選べる値」の下へ置く。
    ②-4 の写す元から「列を作る値」「列の名前の型」を外す（②-12 へ移した）。2回 呼んでも同じ物になる（足した行は足さない）。"""
    t = copy.deepcopy(table)
    have = {e["番号"]: e for e in t["要素"]}
    for after, row in NEW_ROWS.items():
        if row["番号"] in have:
            continue
        idx = next(i for i, e in enumerate(t["要素"]) if e["番号"] == after)
        t["要素"].insert(idx + 1, copy.deepcopy(row))
    # 監査 CP94 の修正8 案B＝部品の記録に、②-5〜②-7・②-9 と同じ形の4行（④-10〜④-13）を足す（入れ子にしない＝決まり①④が要素ごとに掛かる）
    have = {e["番号"]: e for e in t["要素"]}
    after = "④-9"
    for src_no, new_no in PART_ROWS:
        if new_no not in have:
            row = copy.deepcopy(have[src_no])
            row.update({"番号": new_no, "置く記録": "部品の記録", "読むプログラム": [],
                        "写す元": f"{src_no} と同じ（部品の記録＝帯の線の8種）", "出どころ": SRC_CP94 + "の修正8 案B"})
            idx = next(i for i, e in enumerate(t["要素"]) if e["番号"] == after)
            t["要素"].insert(idx + 1, row)
        after = new_no
    e24 = next(e for e in t["要素"] if e["番号"] == "②-4")
    if AXIS_SRC_OLD in e24["写す元"]:
        e24["写す元"] = e24["写す元"].replace(AXIS_SRC_OLD, "（列を作る値と列の名前の型は ②-12 へ移した）")
        e24["出どころ"] = e24["出どころ"] + "・" + SRC_F7
    for no, add in (("②-9", SRC29_ADD), ("③-5", SRC35_ADD)):         # 監査 CP94 の修正9＝写す元の文を、いまの写し先に合わせる
        e = next(x for x in t["要素"] if x["番号"] == no)
        if add not in e["写す元"]:
            e["写す元"] = e["写す元"] + add
    # ★2026-11-01（工事 m2c15-catalog-redirect-20261101・やることの表 F-4）＝列を作る組の写す元は _catalog_from_config（162番まで）、
    #   読むのは build_catalog になった。要素の定義表の ②-12・④-9 の「写す元」と「読むプログラム」を、いまの形に合わせる（2回 呼んでも同じ物）
    for no in ("②-12", "④-9"):
        e = next(x for x in t["要素"] if x["番号"] == no)
        e["写す元"] = e["写す元"].replace("（observe_diag.build_catalog）", "（observe_diag._catalog_from_config＝写す元の関数・162番まで）")
        if "observe_diag.build_catalog" not in e["読むプログラム"]:
            e["読むプログラム"] = list(e["読むプログラム"]) + ["observe_diag.build_catalog"]
    cv = t["選べる値"]
    cv.setdefault("玉の向き", list(SIDE_CHOICES))
    cv["役割の区分の表"] = copy.deepcopy(role_table)
    cv["方向から性質への対応の表"] = copy.deepcopy(prop_table)
    cv["区分の言葉の表（ほかの置き場）"] = copy.deepcopy(kubun)
    if SRC_F7 not in t.get("_出どころ", ""):
        t["_出どころ"] = t.get("_出どころ", "") + "・列を作る組（②-12・④-9）と玉の向き（③-12）と、選べる値の下の3つの表＝" + SRC_F7
    return t


def elem_names(table: dict) -> dict:
    """番号 → 要素の名前（欄の名前はここからだけ読む＝読む口の決まり①）。"""
    return {e["番号"]: e["要素の名前"] for e in table["要素"]}


# ══ 3 隠れた数字（F-3＝172番の道具の measure と、計算式が呼ぶ自前の関数の数の既定＝監査 CP91 の修正1）═══════════════════
def _numdef(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def probe_called_defaults(fn, P0: tuple, df, hsh, skip: set) -> list:
    """計算式が呼ぶ自前の関数の、数の既定のうち、計算式から渡していない物を1つずつ別の値にして、列が変わるかを測る（CP91 の修正1）。
    返り値＝[{引数, 値, 出どころ}]。列が変わらない既定は、隠れた数字ではない。"""
    out = []
    try:
        base = hsh(fn(df, *P0))
    except Exception:                                         # noqa: BLE001  見本の値動きで計算できない式は測れない
        return out
    for nm in called(fn):
        f = getattr(od, nm, None)
        if not inspect.isfunction(f):
            continue
        try:
            sig = inspect.signature(f)
        except (TypeError, ValueError):
            continue
        for p, prm in sig.parameters.items():
            if p in skip or not _numdef(prm.default):
                continue
            v = prm.default
            alts = [v + 2, v + 6] if isinstance(v, int) else [v + 0.1, v * 2 + 0.3]
            moved = False
            for alt in alts:
                def wrapper(*a, _f=f, _sig=sig, _p=p, _alt=alt, **k):
                    b = _sig.bind_partial(*a, **k)
                    if _p not in b.arguments:                  # 計算式から渡していないときだけ、別の値にする
                        k = {**k, _p: _alt}
                    return _f(*a, **k)
                setattr(od, nm, wrapper)
                try:
                    h = hsh(fn(df, *P0))
                except Exception:                             # noqa: BLE001
                    h = base
                finally:
                    setattr(od, nm, f)
                if h != base:
                    moved = True
                    break
            if moved:
                out.append({"引数": p, "値": v, "出どころ": f"{nm} の引数の既定値（observe_diag.py・計算式から渡していない）"})
    return out


def hidden_numbers(old: dict, sets: dict) -> tuple:
    """隠れた数字＝①172番の道具 gen_params_in_name.measure（計算式の引数の既定のうち列が変わる物・資料の表との範囲の合わせ）
    ②計算式が呼ぶ自前の関数の数の既定で、計算式から渡していない物（CP91 の修正1）。返り値＝({記録: [軸]}, 止まった理由, ②で見つけた一覧)。"""
    sys.path.insert(0, str(HERE))
    import gen_params_in_name as gp  # noqa: E402  172番の道具（読むだけ・測る）
    res = gp.measure()
    if res["止まった理由"]:
        raise SystemExit("❌ 隠れた数字を測る道具が止まった: " + "／".join(res["止まった理由"]))
    reg2rec = {c["登録の名前"]: nm for nm, r in old.items() for c in r["計算の関数"] if c["登録の名前"]}
    bys = {x["種類"]: x for x in jload(ST / "indicator_params_by_strategy.json")["指標"]}
    hidden = {}
    for fam, v in res["一覧"].items():
        if not v["オン"]:
            continue                                          # オフの登録（移動平均の for で一緒に変わる物）は相手でない（172番の Y-1）
        rec = reg2rec.get(fam)
        if rec is None:
            raise SystemExit(f"❌ 隠れた数字の登録 {fam} が、記録の計算の関数の登録の名前に無い")
        k = len(v["列を作る値"][0]) - len(v["隠れた数字"]) if v["列を作る値"] else 0
        axes = []
        for j, h in enumerate(v["隠れた数字"]):
            r = v["範囲"][k + j] if k + j < len(v["範囲"]) else {}
            src = v["範囲の出どころ"][k + j] if k + j < len(v["範囲の出どころ"]) else ""
            ax = {"引数": h["引数"], "値": h["値"], "出どころ": f"{h['出どころ']}（gen_params_in_name.measure）",
                  "範囲": None if src.startswith("固定") else {k2: r[k2] for k2 in ("kind", "lo", "hi", "dec") if r.get(k2) is not None},
                  "範囲の出どころ": src}                       # ★dec も残す（監査 CP94 の修正7）
            if ax["範囲"] is None and (rec, h["引数"]) in MEANING_MAP:      # CP91 の修正4＝意味の対応表で、資料の表の範囲を拾う
                pname = MEANING_MAP[(rec, h["引数"])]
                by = bys.get(rec) or {}
                names, ranges = list(by.get("パラメータの名前") or []), list(by.get("範囲") or [])
                if pname in names and names.index(pname) < len(ranges):
                    br = ranges[names.index(pname)]
                    if br.get("下限") is not None and float(br["下限"]) <= float(h["値"]) <= float(br["上限"]):
                        ax["範囲"] = {"lo": br["下限"], "hi": br["上限"], "kind": "int" if isinstance(h["値"], int) else "float"}
                        if ax["範囲"]["kind"] == "float":                       # ★dec も残す（監査 CP94 の修正7）
                            ax["範囲"]["dec"] = _range_dec([br["下限"], br["上限"], h["値"]])
                        ax["範囲の出どころ"] = MEANING_SRC
                    else:
                        ax["範囲の出どころ"] = f"今の値 {h['値']} が資料の表の範囲（{pname}）の外＝拾わずに固定のまま（CP91 の修正4）"
                ax["資料の表の名前"] = pname
            axes.append(ax)
        hidden[rec] = axes
    # ②計算式が呼ぶ自前の関数の数の既定（帯VA・帯VA1時間ATR の va_pct・rows ほか）
    df, hsh = gp.synth(), gp.hsh
    cases = {"W字確定谷": lambda: iref._w_case(24, 100.2)}
    for bf in ("帯スイング", "帯スイング1時間ATR"):
        cases[bf] = lambda: iref._band_case("swing", 4)
    sw_on = set(jload(SDK / ".claude/ratchet/indicator_switch.json")["on"])
    extra = {}
    for nm, r in old.items():
        if nm not in sw_on or not r["計算の関数"] or not sets.get(nm, {}).get("組"):
            continue
        rf = r["計算の関数"][0]["登録の名前"]
        if rf not in od.MATERIAL_FAMILIES:
            continue
        fn = od.MATERIAL_FAMILIES[rf][2]
        P0 = tuple(sets[nm]["組"][0])
        skip = {h["引数"] for h in hidden.get(nm, [])}
        got = probe_called_defaults(fn, P0, cases[rf]() if rf in cases else df, hsh, skip)
        if got:
            extra[nm] = got
            hidden.setdefault(nm, [])
            for h in got:
                hidden[nm].append({"引数": h["引数"], "値": h["値"], "出どころ": h["出どころ"], "範囲": None,
                                   "範囲の出どころ": "固定（資料の表に意味の同じ軸が無い・範囲は70番の T-3 で教科書から決める）"})
    return hidden, res["数"], extra


# ══ 4 いまのカタログの列の並び（②-12・④-9）═══════════════════════════════════════════════════════════════════════
def catalog_sets(old: dict) -> dict:
    """記録 → {名前の型, 照らす形, 組, 並び, 出どころの鍵}。カタログの列（observe_diag.build_catalog）を上から順にたどる。"""
    cfg = jload(PR / "observe_config.json")
    cat = od._catalog_from_config(cfg)                    # 写す元＝設定から列を作る関数（162番まで・161-2 のやることの表 F-4）
    reg2rec = {c["登録の名前"]: nm for nm, r in old.items() for c in r["計算の関数"] if c["登録の名前"]}
    #   組＝登録の名前の型に入れる数字（build_catalog が make_material に渡す物）。照らす形の値＝参照表の型で列の名前から読んだ数字
    #   （記録の「列を作る値」・RVGI({},4) のように型に固定の数字が在る種類は、組より1つ多い）。どちらも捨てない。
    sets = {nm: {"名前の型": list(r["列の名前の型"]["列を作る形"]), "照らす形": list(r["列の名前の型"]["照らす形"]), "組": [], "並び": [],
                 "照らす形の値": list(r["列を作る値"]["値"]), "出どころの鍵": list(r["列を作る値"]["出どころ"])} for nm, r in old.items()}
    for i, (nm, _fn, _d) in enumerate(cat):
        fam, prm = od.find_material(nm)
        if fam is None or fam not in reg2rec:
            raise SystemExit(f"❌ カタログの列 {nm} が、記録の計算の関数の登録につながらない")
        sets[reg2rec[fam]]["組"].append(list(prm))
        sets[reg2rec[fam]]["並び"].append(i)
    for nm, s in sets.items():
        if len(s["組"]) != len(old[nm]["列を作る値"]["値"]):
            raise SystemExit(f"❌ {nm} のカタログの列の数が、記録の「列を作る値」と違う: {len(s['組'])} ／ {len(old[nm]['列を作る値']['値'])}")
    return sets


# ══ 5 23の欄 → ②③④の要素（要素の名前は要素の定義表から）═══════════════════════════════════════════════════════════
class _Used(dict):
    """読んだ欄を覚える辞書（写せない欄が在れば止めるため）。"""
    def __init__(self, d):
        super().__init__(d)
        self.used = set()

    def __getitem__(self, k):
        self.used.add(k)
        return super().__getitem__(k)


def _kind_of(v) -> str:
    return "整数" if isinstance(v, int) and not isinstance(v, bool) else "小数"


def _range_dec(vals) -> int:
    """小数の桁（engine_tuner_gen.material_ranges:290 と同じ決め方）。"""
    return int(max((len(str(v).split(".")[1]) if "." in str(v) else 0) for v in vals)) if vals else 0


def catalog_range(vals) -> dict:
    """カタログの列の値の最小〜最大（engine_tuner_gen.material_ranges:286〜293 と同じ作り＝いまの engine_tuner が探している範囲・監査 CP94 の修正4 案A）。"""
    is_int = all(float(v).is_integer() and not isinstance(v, float) for v in vals)
    return {"kind": "int" if is_int else "float", "lo": min(vals), "hi": max(vals), "dec": _range_dec(vals)}


def name_token(s) -> str:
    """資料の表のパラメータの名前の語（括弧の前・小文字＝gen_params_in_name.name_token と同じ）。"""
    return re.split(r"[（(]", str(s))[0].strip().lower()


def _same_num(a, b) -> bool:
    try:
        return float(a) == float(b)
    except (TypeError, ValueError):
        return False


# 合わない値（資料の表の名前が、どの軸にも合わなかった値）＝写すプログラムが画面に出す（監査 CP94 の修正1・まこさん「案B」2026-11-01）
UNPLACED: list = []
HOW_SRC = "合わせ方＝名前の語／計算式の渡し方／意味の対応表／並びの値が今の値と合う／残った1組（監査 CP94 の修正1・まこさん「案B」2026-11-01）"


def match_params(rec: str, axes: list, cur: list, pnames: list, firsts: list, src: str) -> tuple:
    """資料の表のパラメータの名前を、軸に合わせる。並びの番号だけでは合わせない（監査 CP94 の修正1・まこさん「案B」）。
    合わせ方の順＝①名前の語が引数の名前と同じ ②計算式がその引数を、ライブラリの同じ名前の引数に渡している（例＝signal=g_）
    ③意味の対応表（MEANING_MAP）④資料の表の最初の値（かライブラリの既定）が、軸の並びどおりに今の値と合う（gen_params_in_name.measure の pos_ok）
    ⑤名前が合わず、資料の表の名前と軸が1つずつだけ残った組。
    返り値＝({軸の番号: (資料の表の番号, 合わせ方)}, どの軸にも合わなかった資料の表の番号の並び)。1本の軸に2つの名前が当たれば止まる。"""
    toks = [name_token(p) for p in pnames]
    got, used = {}, set()

    def put(ai, pi, how, share=False):
        if ai in got:
            if got[ai][0] == pi:
                return
            raise SystemExit(f"❌ 代表の値を写せない（1本の軸に2つの名前が当たる）: {rec} の軸 {axes[ai]} ／ 資料の表 {pnames[got[ai][0]]}・{pnames[pi]}")
        if pi in used and not share:
            return                                            # 1つの名前は1本の軸だけ（意味の対応表で明記した物だけ2本に当てる）
        got[ai] = (pi, how)
        used.add(pi)
    for ai, a in enumerate(axes):                             # ①名前の語
        hits = [pi for pi, t in enumerate(toks) if t == str(a).lower()]
        if len(hits) == 1:
            put(ai, hits[0], "名前の語")
    for pi, t in enumerate(toks):                             # ②計算式の渡し方
        if pi in used or not re.fullmatch(r"[a-z_][a-z0-9_]*", t):
            continue
        hits = [ai for ai, a in enumerate(axes) if ai not in got and re.search(rf"\b{re.escape(t)}\s*=\s*{re.escape(str(a))}\b", src or "")]
        if len(hits) == 1:
            put(hits[0], pi, "計算式の渡し方")
    for ai, a in enumerate(axes):                             # ③意味の対応表
        p = MEANING_MAP.get((rec, a))
        if ai not in got and p in pnames:
            put(ai, pnames.index(p), "意味の対応表", share=True)
    if len(pnames) == len(axes) and any(isinstance(s, list) and len(s) == len(axes) and all(_same_num(x, y) for x, y in zip(s, cur)) for s in firsts):
        for ai in range(len(axes)):                           # ④並びの値が今の値と合う
            if ai not in got and ai not in used:
                put(ai, ai, "並びの値が今の値と合う")
    la = [ai for ai in range(len(axes)) if ai not in got]
    lp = [pi for pi in range(len(pnames)) if pi not in used]
    if len(la) == 1 and len(lp) == 1:                         # ⑤残った1組
        put(la[0], lp[0], "残った1組")
    return got, [pi for pi in range(len(pnames)) if pi not in used]


def axes_for(o: dict, hidden: list, sets: dict, fn) -> list:
    """②-4／④-4 パラメータの軸＝名前に出る軸（カタログの列の数字）と隠れた数字の軸（F-3・Y-16）。
    範囲＝名前に出る軸は search_limits.json の範囲、無ければ、いまの engine_tuner と同じカタログの値の最小〜最大（監査 CP94 の修正4 案A）。
    隠れた数字は measure と意味の対応表の範囲と、名前で合った資料の表の範囲。どこにも無い軸は「まだ決めていない」。dec を残す（修正7）。
    代表の値＝資料の表の名前で合った軸だけに写す（修正1・案B）。最初の値が無い戦略は資料の表のライブラリの既定、無ければ「まだ決めていない」（修正17 案A）。
    合わない名前に出る軸は「まだ決めていない」・合わない隠れた数字の軸は いまの値（F-3）。向きが逆の軸（REVERSED）は「まだ決めていない」。"""
    rec = o["名前"]
    hidden = list(hidden)                                                         # ★隠れた数字を軸へ（F-3）
    tpls = o["列の名前の型"]["列を作る形"]
    k = tpls[0].count("{}") if tpls else 0
    pos = []
    if fn is not None:
        try:
            pos = [p.name for p in list(inspect.signature(fn).parameters.values())[1:] if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
        except (TypeError, ValueError):
            pos = []
    by = (o["教科書の出どころ"] or {}).get("by_strategy") or {}
    pnames = list(by.get("パラメータの名前") or [])
    libd = ((by.get("ライブラリの既定") or {}).get("値") if isinstance(by.get("ライブラリの既定"), dict) else None) or []
    old_ranges = o["範囲"] or []
    rep = o["代表の固定値（スキャル／デイトレ）"] or {}
    fh = o["名前に出ない軸の最初の値"] or {}
    by_ranges = list(by.get("範囲") or [])
    names = [pos[i] if i < len(pos) else f"{i + 1}つ目" for i in range(k)] + [h["引数"] for h in hidden]
    cur = [(sets["組"][0][i] if sets["組"] else None) for i in range(k)] + [h["値"] for h in hidden]
    firsts = [s for g in ("スキャル", "デイトレ") for s in ((rep.get(g) or []) + (fh.get(g) or []))] + ([libd] if libd else [])
    src = ((o["計算の関数"] or [{}])[0] or {}).get("式の文") or ""
    got, left = match_params(rec, names, cur, pnames, firsts, src)
    for pi in left:                                           # 合わない値の一覧（画面に出す・対応は70番の T-3）
        vals = {g: [s[pi] for s in (rep.get(g) or []) if isinstance(s, list) and len(s) == len(pnames)] for g in ("スキャル", "デイトレ")}
        if vals["スキャル"] or vals["デイトレ"]:
            UNPLACED.append({"記録": rec, "資料の表の名前": pnames[pi], "最初の値": vals})

    def rep_of(ai):
        pi = got[ai][0]
        out = {}
        for g in ("スキャル", "デイトレ"):
            v = [s[pi] for s in (rep.get(g) or []) if isinstance(s, list) and len(s) == len(pnames)]
            v = v or [s[pi] for s in (fh.get(g) or []) if isinstance(s, list) and len(s) == len(pnames)]
            v = v or ([libd[pi]] if len(libd) == len(pnames) else [])
            out[g] = v or UNDECIDED
        return out
    axes = []
    for ai, nm in enumerate(names):
        hidden_ax = ai >= k
        h = hidden[ai - k] if hidden_ax else None
        rev = REVERSED.get((rec, nm))
        how = got.get(ai, (None, None))[1]
        if hidden_ax:
            v = h["値"]
            rg = dict(h["範囲"]) if h.get("範囲") else None
            rg_src = h.get("範囲の出どころ") or "無し"
            if rg is None and how and not rev:               # 名前で合った資料の表の範囲（今の値が範囲の中に在るときだけ）
                b = by_ranges[got[ai][0]] if got[ai][0] < len(by_ranges) else {}
                if b.get("下限") is not None and _same_num(b["下限"], b["下限"]) and float(b["下限"]) <= float(v) <= float(b["上限"]):
                    rg = {"kind": "int" if isinstance(v, int) else "float", "lo": b["下限"], "hi": b["上限"]}
                    if rg["kind"] == "float":
                        rg["dec"] = _range_dec([b["下限"], b["上限"], v])
                    rg_src = f"indicator_params_by_strategy.json の範囲（{pnames[got[ai][0]]}・{how}）"
            ax = {"名前": nm, "種類": _kind_of(v), "範囲": rg or UNDECIDED,
                  "代表の値": UNDECIDED if rev else (rep_of(ai) if how else ({"スキャル": UNDECIDED, "デイトレ": UNDECIDED} if any(u["記録"] == rec for u in UNPLACED) else {"スキャル": [v], "デイトレ": [v]})),
                  "出どころ": {"値": h["出どころ"], "範囲": rg_src,
                            "代表の値": (f"資料の表の {rev} の値（{[s[i] for i, p in enumerate(pnames) if name_token(p) == rev for s in (rep.get('スキャル') or []) if isinstance(s, list) and len(s) == len(pnames)]}）は、計算式の今の値（{v}）と向きが逆＝写さない（CP91 の修正12・70番の T-3）" if rev else
                                     f"indicator_params_by_strategy.json の最初の値（{how}）" if how else
                                     f"資料の表の名前と合わない（この記録には資料の表の合わない値が在る＝いまの値 {v} は代表の値にしない・対応は70番の T-3・監査 CP95）" if any(u["記録"] == rec for u in UNPLACED) else
                                     "いまの値（コードの既定値）・資料の表に、この軸に当てる値が無い（要件5 の②＝既定の値・監査 CP95）")}}
        else:
            vals = [p[ai] for p in sets["組"]] if sets["組"] else []
            rg0 = old_ranges[ai] if ai < len(old_ranges) else None                     # ★範囲を軸へ写す（search_limits.json）
            rg = dict(rg0) if rg0 else (catalog_range(vals) if vals else None)
            ax = {"名前": nm,
                  "種類": _kind_of(vals[0]) if vals else ("整数" if (rg or {}).get("kind") == "int" else "小数"),
                  "範囲": rg or UNDECIDED,
                  "代表の値": UNDECIDED if rev else (rep_of(ai) if how else {"スキャル": UNDECIDED, "デイトレ": UNDECIDED}),
                  "出どころ": {"範囲": ("recipes/search_limits.json の material_param_ranges" if rg0 else
                                     "engine_tuner_gen.material_ranges の catalog（カタログの列の値の最小〜最大・engine_tuner_gen.py:286〜293）" if vals else "無し"),
                            "代表の値": (f"indicator_params_by_strategy.json の最初の値（{how}）" if how else
                                     "資料の表の名前と合わない（対応は70番の T-3）" if pnames else
                                     "資料の表にパラメータの名前が無い（名前で合わせる相手が無い・70番の T-3・監査 CP95）"),
                            "名前": "計算式の引数の名前"}}
        if how:
            ax["資料の表の名前"] = pnames[got[ai][0]]
            ax["出どころ"]["合わせ方"] = how
        axes.append(ax)
    # CP91 の修正4 の後半＝資料の表に意味の同じ軸の範囲が在り、今の値がその中に在るのに「まだ決めていない」にした隠れた数字の軸が在れば止まる
    for ai in range(k, len(names)):
        if ai in got and not REVERSED.get((rec, names[ai])) and axes[ai]["範囲"] == UNDECIDED:
            b = by_ranges[got[ai][0]] if got[ai][0] < len(by_ranges) else {}
            if b.get("下限") is not None and float(b["下限"]) <= float(hidden[ai - k]["値"]) <= float(b["上限"]):
                raise SystemExit(f"❌ {rec} の隠れた数字 {names[ai]}: 資料の表に意味の同じ軸の範囲（{pnames[got[ai][0]]}）が在るのに「まだ決めていない」にした")
    return axes


def calls_deep(names) -> set:
    """計算式が直に呼ぶ関数と、その関数がさらに呼ぶ観察の道具の関数（2段まで・帯スイングの _band_swing → _fractal_marks）。"""
    out = set(names or [])
    for nm in list(out):
        f = getattr(od, nm, None)
        if inspect.isfunction(f):
            out |= {x for x in f.__code__.co_names if inspect.isfunction(getattr(od, x, None))}
    return out


def to_new(old: dict, table: dict, hidden: dict, sets: dict) -> dict:
    """23の欄の記録 → 一番外の5つ（要素の名前は要素の定義表から読む）。写せない欄が在れば止まる。"""
    E = elem_names(table)
    need = ("②-1", "②-2", "②-4", "②-5", "②-6", "②-7", "②-9", "②-10", "②-11", "②-12",
            "③-1", "③-2", "③-4", "③-5", "③-11", "③-12", "④-1", "④-2", "④-3", "④-4", "④-7", "④-8", "④-9",
            "④-10", "④-11", "④-12", "④-13")
    miss = [n for n in need if n not in E]
    if miss:
        raise SystemExit(f"❌ 要素の定義表に無い番号: {miss}（F-7 の3行を足してから写す）")
    cv = table["選べる値"]
    prop_keys = set(cv.get("方向から性質への対応の表") or {})
    ind, uses, parts = {}, [], {}
    reg_fn = {rf: v[2] for rf, v in od.MATERIAL_FAMILIES.items()}
    for nm in sorted(old):
        o = _Used(old[nm])
        c0 = o["計算の関数"][0] if o["計算の関数"] else None
        calc = ({"登録の名前": c0["登録の名前"], "関数の名前": c0["関数の名前"], "式の文": c0["式の文"]} if c0 else
                {"登録の名前": None, "関数の名前": [], "式の文": None, "注記": "計算は engine_tuner_exec.py の _col_array の中に在る（関数として切り出すのは171番）"})
        fn = reg_fn.get(c0["登録の名前"]) if c0 and c0["登録の名前"] else None
        axes = axes_for(o, hidden.get(nm, []), sets[nm], fn)
        rz = o["役割・札・値域・注記"]
        hk = o["方向・性質"]
        read = {"区分": hk["方向"]["区分"], "読み方": hk["方向"]["読み方"], "向きを持つ": c0["向きを持つ"] if c0 else None, "性質": hk["性質"]}
        if read["区分"] is not None and read["区分"] not in prop_keys:
            # 別枠の材料（需給・レンジ幾何・時間帯）の方向は、定義の表の文（例＝「需給」「価格水準」）で、対応の表の区分でない。
            # 値は捨てずに「区分（元の形）」に残し、区分は空にする（読む口の決まり④＝選べる値に無い値は止まる、に掛からない形）
            read = {"区分": None, "区分（元の形）": read["区分"], "読み方": read["読み方"], "向きを持つ": read["向きを持つ"], "性質": read["性質"]}
        role = {"区分": rz["役割"]["区分"] if rz["役割"] else None, "出どころ": rz["役割"]["出どころ"] if rz["役割"] else None, "札": rz["札"]}
        refs = {"照合の関数・既知答え": o["照合の関数・既知答え"], "ライブラリとの対応": o["ライブラリとの対応"], "V9 の名前": o["V9 の名前"],
                "教科書の出どころ": o["教科書の出どころ"], "注記": rz["注記"], "閾値の文": o["閾値の文"], "閾値の値の調べた結果": o["閾値の値"]["調べた結果"],
                "出口の水準": o["出口の水準"], "閾値の代表の固定値（スキャル／デイトレ）": o["閾値の代表の固定値（スキャル／デイトレ）"],
                "コードの中の既定値": o["コードの中の既定値"], "名前に出ない軸の最初の値": o["名前に出ない軸の最初の値"],
                "代表の固定値（スキャル／デイトレ）": o["代表の固定値（スキャル／デイトレ）"], "範囲（search_limits.json）": o["範囲"],
                "食い違いの記録": o["食い違いの記録"], "ほかの置き場の値": o["ほかの置き場の値"]}   # ★元の形のまま残す（監査 CP94 の修正7）
        onoff = {"状態": o["オン/オフ"]["状態"], "源": o["オン/オフ"]["源"], "mako": o["mako"]}
        if len(o["列を作る値"]["値"]) != len(sets[nm]["組"]) or o["列を作る値"]["出どころ"] != sets[nm]["出どころの鍵"]:
            raise SystemExit(f"❌ {nm}: 記録の「列を作る値」とカタログの組が違う")
        colset = {"名前の型": sets[nm]["名前の型"], "照らす形": sets[nm]["照らす形"], "組": sets[nm]["組"], "並び": sets[nm]["並び"],
                  "照らす形の値": sets[nm]["照らす形の値"], "出どころの鍵": sets[nm]["出どころの鍵"]}
        thr_ranges = o["閾値の範囲"]
        rec = {E["②-1"]: o["名前"], E["②-2"]: calc, E["②-4"]: axes, E["②-5"]: {"値域": rz["値域"]}, E["②-6"]: read, E["②-7"]: role,
               E["②-9"]: refs, E["②-10"]: onoff, E["②-12"]: colset}
        if thr_ranges:
            # ★単位は書かない（「時（0〜23）」は写す元に無い言葉・選べる値の「値の単位」にも無い）。hour_range の kind を残す（監査 CP94 の修正21）
            rec[E["②-11"]] = [{"形": "値", "範囲": {k2: r[k2] for k2 in ("kind", "lo", "hi") if r.get(k2) is not None}, "出どころ": r.get("出どころ")}
                              for r in thr_ranges]
        consts = o["閾値の値"]["定数"]
        if o["出口の水準"]:
            hi_c, lo_c = o["出口の水準"]
            unit = "0〜100" if (rz["値域"] or {}).get("有界") == [0.0, 100.0] else None
            for usage, side, sd, which in EXIT_USAGES:
                cst = hi_c if which == "hi" else lo_c
                c = consts.get(cst) or {}
                thr = {"形": "値", "代表の値": {"スキャル": c.get("value"), "デイトレ": c.get("value")},
                       "出どころ": f"CONST_REGISTRY の {cst}（{c.get('source')}・{c.get('imi')}）"}
                if unit:
                    thr["単位"] = unit
                uses.append({E["③-1"]: {"指標の記録": nm}, E["③-2"]: usage, E["③-12"]: side, E["③-4"]: sd, E["③-5"]: [thr],
                             E["③-11"]: {"状態": "オン", "出どころ": EXIT_SRC + (EXIT_NOTE_SAME if hi_c == lo_c else "")}})
        if nm in PART_USES:
            for u in PART_USES[nm]:
                if u["指標の記録"] not in old:
                    raise SystemExit(f"❌ 部品 {nm} の使う物 {u['指標の記録']} が記録に無い")
                if c0 is None or u["呼ぶ関数"] not in calls_deep(c0["関数の名前"]):
                    raise SystemExit(f"❌ 部品 {nm} の計算式が {u['呼ぶ関数']} を呼んでいない（PART_USES が実物と合わない）")
                uc = old[u["指標の記録"]]["計算の関数"]
                if "時間足" not in u and u["呼ぶ関数"] not in calls_deep(uc[0]["関数の名前"] if uc else []):
                    raise SystemExit(f"❌ 部品 {nm} の使う物 {u['指標の記録']} の計算式が {u['呼ぶ関数']} を呼んでいない")
            teigi = o["照合の関数・既知答え"][0]["定義"] if o["照合の関数・既知答え"] else None
            # ★②-5〜②-7・②-9 に当たる値は、入れ子にせず ④-10〜④-13 に置く（監査 CP94 の修正8 案B）
            parts[nm] = {E["④-1"]: o["名前"], E["④-2"]: [{k2: v2 for k2, v2 in u.items()} for u in PART_USES[nm]], E["④-3"]: calc,
                         E["④-4"]: axes, E["④-7"]: [teigi] if teigi else [],
                         E["④-8"]: {"状態": onoff["状態"], "源": onoff["源"], "mako": onoff["mako"],
                                   "作った元": f"INDICATOR_TABLE の記録「{nm}」と {PART_SRC}"},
                         E["④-9"]: colset, E["④-10"]: {"値域": rz["値域"]}, E["④-11"]: read, E["④-12"]: role, E["④-13"]: refs}
            if thr_ranges:
                raise SystemExit(f"❌ 部品 {nm} に閾値の範囲が在る（④-5 の形は未定）")
        else:
            ind[nm] = rec
        left = set(OLD_FIELDS) - o.used
        if left:
            raise SystemExit(f"❌ {nm}: 写す先の要素が無い欄: {sorted(left)}")
    return {TOP[0]: MADE_BY, TOP[1]: table, TOP[2]: ind, TOP[3]: uses, TOP[4]: parts}


def build() -> tuple:
    """新しい形の全部を、写す元から作る。返り値＝(データ, 「①写す」の行, 隠れた数字の数, ②で見つけた一覧)。"""
    UNPLACED.clear()                                           # 合わない値の一覧は、作るたびに作り直す
    old, role_table, prop_table, kubun, rows = build_old()
    table = table_update(read_table()["要素の定義表"], role_table, prop_table, kubun)
    sets = catalog_sets(old)
    hidden, n_hidden, extra = hidden_numbers(old, sets)
    data = to_new(old, table, hidden, sets)
    data = json.loads(json.dumps(data, ensure_ascii=False, default=repr))
    return data, rows, {"measure": n_hidden, "記録": len(hidden), "呼ぶ関数の既定": extra}, old


# ══ 6 照らす（「①写す」の行が全部 記録に入ったか・新しい形が写す元と同じか）═══════════════════════════════════════════
def _has_assign(path: Path, name: str) -> bool:
    """そのファイルのどこか（関数の中を含む）に、name への代入か、同じ名前のキーワード引数が在るか。"""
    if not path.exists():
        return False
    _t, tree = parsed(path)
    return any(isinstance(n, (ast.Assign, ast.AnnAssign, ast.keyword)) and _same_target(_target_text(n), name) for n in ast.walk(tree))


def coverage(data: dict, rows: list, strict: bool = True) -> list:
    """直す相手の一覧の「①写す」の行のうち、記録にも選べる値の表にも入らない行（4-5）。"""
    E = elem_names(data[TOP[1]])
    placed = set()
    src_keys = set()
    for r in data[TOP[2]].values():
        placed |= {o["置き場"] for o in r[E["②-9"]]["ほかの置き場の値"]}
        src_keys |= set(r[E["②-12"]]["出どころの鍵"])
    for r in data[TOP[4]].values():
        placed |= {o["置き場"] for o in r[E["④-13"]]["ほかの置き場の値"]}
        src_keys |= set(r[E["④-9"]]["出どころの鍵"])
    placed_items = [o for r in data[TOP[2]].values() for o in r[E["②-9"]]["ほかの置き場の値"]] + \
        [o for r in data[TOP[4]].values() for o in r[E["④-13"]]["ほかの置き場の値"]] + \
        list(data[TOP[1]]["選べる値"].get("区分の言葉の表（ほかの置き場）", []))
    placed |= {o["置き場"] for o in placed_items}

    def fn_of(file, line):
        """その行を含む関数の名前（一番外なら空）＝照らしの3つ目（監査 CP94 の修正13）。"""
        p = PR / file
        if not p.exists():
            return ""
        f = enclosing_fn(parsed(p)[1], line)
        return f.name if f is not None else ""
    _pl = [o for o in placed_items if ":" in o["置き場"] and o["置き場"].rsplit(":", 1)[1].isdigit()]
    placed_names = [(o["置き場"].rsplit(":", 1)[0], str(o["名前"]), fn_of(o["置き場"].rsplit(":", 1)[0], int(o["置き場"].rsplit(":", 1)[1]))) for o in _pl]
    placed_lines = [int(o["置き場"].rsplit(":", 1)[1]) for o in _pl]
    recs = {**data[TOP[2]], **data[TOP[4]]}

    def code_defaults(f):
        r = recs.get(f)
        if r is None:
            return False
        refs = r[E["②-9"]] if f in data[TOP[2]] else r[E["④-13"]]
        return any(v["引数の既定値"] or v["式の中の数"] for v in refs["コードの中の既定値"].values())
    miss = []
    want_n: dict = {}                                          # ★（ファイル・名前・関数）ごとの「①写す」の行の置き場の数（監査 CP94 の修正13）
    for r in rows:                                             #   同じ行を別の面から書いた行（例＝AXIS_EC の「区分の言葉」と「名前」）は、置き場1つと数える
        if row_kind(r) == "ほかの置き場" and r["節"] != "拾えなかった行":
            key = (r["ファイル"], _ntext(row_target(r)), fn_of(r["ファイル"], row_line(r)) if strict else "")
            want_n.setdefault(key, set()).add(row_line(r))
    want_n = {k: len(v) for k, v in want_n.items()}
    for r in rows:
        k = row_kind(r)
        if k == "古い鍵":
            ok = r["中身"] in src_keys
        elif k == "コードの中の既定値":
            ok = code_defaults(r["中身"].split(" のパラメータ")[0])
        elif k in ("決まった欄", "自己テストの見本"):        # 見本は写さない（worklog 20261024:357）
            ok = True
        elif k == "json":
            keys = [t.split()[0] for t in r["中身"].split("・")]
            ok = all(key in JSON_OWN.get(r["ファイル"], set()) or f"{r['ファイル']} の {key}" in placed for key in keys)
        elif r["節"] == "拾えなかった行":
            # 報告の行＝名前の語（略された名前は1つ目の頭を付ける）のうち、そのファイルに代入が在る物が全部 写っていればよい（監査 CP94 の修正13）
            toks = re.findall(r"[A-Za-z_]\w*", r["中身"].split("[")[0])
            pre = toks[0].rsplit("_", 1)[0] + "_" if toks and "_" in toks[0] else ""
            if any(f == r["ファイル"] and _ntext(nm) == _ntext(row_target(r)) for f, nm, _fn in placed_names):
                ok = True
            else:
                need_t = [t for t in toks if _has_assign(PR / r["ファイル"], t) or (pre and _has_assign(PR / r["ファイル"], pre + t))]
                ok = bool(need_t) and all(any(f == r["ファイル"] and (_ntext(nm) == t or (pre and _ntext(nm) == pre + t)) for f, nm, _fn in placed_names)
                                          for t in need_t)
        else:
            # 置き場は名前で探すので、ファイル・名前・その行を含む関数の3つで照らし、写した置き場の数が「①写す」の行の数と合うかも見る（監査 CP94 の修正13）。
            # ★strict でない＝写し直しの1回目（一覧が古く、行がずれていてよい）＝ファイルと名前だけで照らす。2回目と --verify・旗なしは strict。
            rf = fn_of(r["ファイル"], row_line(r)) if strict else None
            lines_hit = {ln for (f, nm, fn), ln in zip(placed_names, placed_lines)
                         if f == r["ファイル"] and _same_target(nm, row_target(r)) and (rf is None or fn == rf)}
            key = (r["ファイル"], _ntext(row_target(r)), rf if strict else "")
            ok = len(lines_hit) >= max(1, want_n.get(key, 1) if strict else 1)
        if not ok:
            miss.append(f"{r['ファイル']}:{r['行']} {r['中身'][:40]}")
    return miss


def compare(have: dict, want: dict) -> list:
    """新しい形どうしを、要素ごとに比べる。"""
    bad = []
    if norm(have.get(TOP[1])) != norm(want[TOP[1]]):
        bad.append("要素の定義表が写す元と違う")
    for kind in (TOP[2], TOP[4]):
        hr, wr = have.get(kind) or {}, want[kind]
        for f in sorted(set(hr) | set(wr)):
            if f not in hr or f not in wr:
                bad.append(f"{kind} {f}: 記録が{'無い' if f not in hr else '写す元に無い'}")
                continue
            for fld in sorted(set(hr[f]) | set(wr[f])):
                if norm(hr[f].get(fld)) != norm(wr[f].get(fld)):
                    bad.append(f"{kind} {f}: 要素「{fld}」が写す元と違う（記録 {norm(hr[f].get(fld))[:80]} ／ 写す元 {norm(wr[f].get(fld))[:80]}）")
    hu, wu = have.get(TOP[3]) or [], want[TOP[3]]
    if norm(hu) != norm(wu):
        bad.append(f"使い方の記録が写す元と違う（記録 {len(hu)} 件 ／ 写す元 {len(wu)} 件）")
    return bad


def ranges_vs_engine(data: dict) -> list:
    """オンの種類の名前に出る軸の範囲が、engine_tuner_gen.material_ranges() と1本ずつ同じか（監査 CP94 の修正4 案A）。違う軸の一覧を返す。"""
    if str(PR) not in sys.path:
        sys.path.insert(0, str(PR))
    with contextlib.redirect_stdout(io.StringIO()):
        import engine_tuner_gen as etg  # noqa: E402  読むだけ（いまの engine_tuner が探している範囲）
        mr = etg.material_ranges()
    E = elem_names(data[TOP[1]])
    recs = {**{k: v.get(E["②-4"]) or [] for k, v in (data.get(TOP[2]) or {}).items()},
            **{k: v.get(E["④-4"]) or [] for k, v in (data.get(TOP[4]) or {}).items()}}
    bad = []
    for fam, spec in sorted(mr.items()):
        axes = recs.get(fam)
        if axes is None:
            bad.append(f"範囲: {fam} が記録に無い（engine_tuner_gen.material_ranges には在る）")
            continue
        for i, want in enumerate(spec["axes"]):
            have = axes[i]["範囲"] if i < len(axes) else None
            if norm(have) != norm(dict(want)):
                bad.append(f"範囲: {fam} の軸 {i + 1}（{axes[i]['名前'] if i < len(axes) else '無い'}）が いまの engine_tuner と違う"
                           f"（記録 {norm(have)[:80]} ／ engine_tuner {norm(dict(want))[:80]}）")
    return bad


def print_unplaced(data: dict) -> None:
    """資料の表の最初の値のうち、名前がどの軸にも合わなかった物（記録ごとに1行・オンとオフを分けて数える）。"""
    E = elem_names(data[TOP[1]])
    on = {k for kind in (TOP[2], TOP[4]) for k, v in (data.get(kind) or {}).items()
          if ((v.get(E["②-10"]) if kind == TOP[2] else v.get(E["④-8"])) or {}).get("状態") == "オン"}
    by_rec: dict = {}
    for u in UNPLACED:
        by_rec.setdefault(u["記録"], []).append(u["資料の表の名前"])
    n_on = sum(len(v) for k, v in by_rec.items() if k in on)
    print(f"合わない値（資料の表の名前が、どの軸にも合わなかった最初の値・対応は70番の T-3）＝オン {n_on}（{sum(1 for k in by_rec if k in on)} 種）"
          f"・オフ {sum(len(v) for k, v in by_rec.items() if k not in on)}（{sum(1 for k in by_rec if k not in on)} 種）")
    for k in sorted(by_rec, key=lambda x: (x not in on, x)):
        print(f"  ・{'オン' if k in on else 'オフ'} {k}: {'・'.join(by_rec[k])}")


def verify() -> int:
    """indicators.json（新しい形）の値と、写す元から作り直した値を1件ずつ比べる。書かない。違えば 1。"""
    have = read_table()
    if "記録" in have:
        print("❌ indicators.json は古い形（一番外に「記録」）＝先に --rewrite で写し直す")
        return 1
    want, rows, n_hidden, _old = build()
    bad = compare(have, want)
    miss = coverage(want, rows)
    bad += [f"直す相手の一覧の「①写す」の行が、記録にも選べる値の表にも入らない: {m}" for m in miss]
    bad += ranges_vs_engine(have)                              # ★名前に出る軸の範囲＝いまの engine_tuner と同じか（監査 CP94 の修正4 案A）
    print_unplaced(have)                                       # ★合わない値の一覧（止めない・対応は70番の T-3＝監査 CP94 の修正31・案B）
    E = elem_names(want[TOP[1]])
    print(f"照らした＝指標の記録 {len(have.get(TOP[2]) or {})} 件・使い方の記録 {len(have.get(TOP[3]) or [])} 件・部品の記録 {len(have.get(TOP[4]) or {})} 件"
          f"・要素 {len(E)} 行・直す相手の一覧の「①写す」の行 {len(rows)} 行・隠れた数字を持つ記録 {n_hidden['記録']}")
    for b in bad:
        print("  ❌", b)
    print("✅ 違い 0 件" if not bad else f"❌ 違い {len(bad)} 件")
    return 0 if not bad else 1


def diff_old(have: dict, want_old: dict) -> list:
    """古い形の記録（いまの indicators.json）と、写す元から集め直した23の欄を1件ずつ比べる（写し直しで値が変わる種類を画面に出す）。"""
    bad = []
    hr = have.get("記録", {})
    for f in sorted(set(hr) | set(want_old)):
        if f not in hr or f not in want_old:
            bad.append(f"{f}: 記録が{'無い' if f not in hr else '写す元に無い'}")
            continue
        for fld in OLD_FIELDS:
            if norm(hr[f].get(fld)) != norm(want_old[f].get(fld)):
                bad.append(f"{f}: 欄「{fld}」（記録 {norm(hr[f].get(fld))[:60]} ／ 写す元 {norm(want_old[f].get(fld))[:60]}）")
    return bad


def summary(data: dict, n_hidden: dict) -> None:
    E = elem_names(data[TOP[1]])
    print(f"指標の記録 {len(data[TOP[2]])} 件・使い方の記録 {len(data[TOP[3]])} 件・部品の記録 {len(data[TOP[4]])} 件・要素の定義表 {len(E)} 行"
          f"・選べる値 {len(data[TOP[1]]['選べる値'])} 個・列を作る組 {sum(len(r[E['②-12']]['組']) for r in data[TOP[2]].values()) + sum(len(r[E['④-9']]['組']) for r in data[TOP[4]].values())} 組")
    print("隠れた数字＝measure:", n_hidden["measure"], "・隠れた数字を持つ記録", n_hidden["記録"], "・呼ぶ関数の既定で見つけた記録",
          len(n_hidden["呼ぶ関数の既定"]), ":", "・".join(f"{k}={[h['引数'] for h in v]}" for k, v in n_hidden["呼ぶ関数の既定"].items()))
    for kind in (TOP[2], TOP[4]):
        names = [e["要素の名前"] for e in data[TOP[1]]["要素"] if e["置く記録"] == kind]
        print(f"{kind} の要素ごとの在る記録の数:", "・".join(f"{n} {sum(1 for r in data[kind].values() if n in r)}" for n in names))
    axes_n = sum(len(r[E["②-4"]]) for r in data[TOP[2]].values()) + sum(len(r[E["④-4"]]) for r in data[TOP[4]].values())
    all_axes = [a for r in data[TOP[2]].values() for a in r[E["②-4"]]] + [a for r in data[TOP[4]].values() for a in r[E["④-4"]]]
    with_range = sum(1 for a in all_axes if a["範囲"] != UNDECIDED)
    # ★途中で測る数字＝下限＜上限の軸の数（1点の範囲は探す幅が0なので数えない＝監査 CP94 の修正22）
    can_search = sum(1 for a in all_axes if isinstance(a["範囲"], dict) and _same_num(a["範囲"]["lo"], a["範囲"]["lo"]) and float(a["範囲"]["lo"]) < float(a["範囲"]["hi"]))
    print(f"パラメータの軸 {axes_n} 本（範囲を持つ {with_range}＝うち下限＜上限 {can_search}・1点 {with_range - can_search}／まだ決めていない {axes_n - with_range}）")
    print_unplaced(data)


def rewrite() -> int:
    """F-7＝写す元から作り直して indicators.json を書き替える。変わる所を全部画面に出す。
    古い形なら新しい形へ写し直す（2段＝一覧を作り直してもう1回）。新しい形なら、写す元から作り直した物と違う所を全部出して書き直す
    （162番で写す元を消すまでは、値は写す元で直し、この口で作り直す＝indicators.json を手で直さない・監査 CP94 の修正14 案B）。"""
    have = read_table()
    data, rows, n_hidden, old = build()
    miss = coverage(data, rows, strict="記録" not in have)     # 1回目（古い形）は一覧が古いので、ファイルと名前だけで照らす（修正13）
    if miss:
        raise SystemExit("❌ 直す相手の一覧の「①写す」の行のうち、記録にも選べる値の表にも入らない行が在る: " + "／".join(miss))
    if "記録" not in have:
        bad = compare(have, data)
        if not bad:
            print(f"{OUT} はもう新しい形で、写す元から作り直した物と同じ（書かない）")
            summary(data, n_hidden)
            return 0
        print(f"写す元から作り直した物と違う所＝{len(bad)} 件（162番までは写す元が正＝作り直して書く・監査 CP94 の修正14 案B）")
        for b in bad:
            print("  ・", b)
        OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        print("書いた", OUT, "（新しい形を、写す元から作り直した）")
        summary(data, n_hidden)
        return 0
    changed = diff_old(have, old)
    print(f"写し直しで値が変わる所（古い形の記録と、写す元から集め直した23の欄の違い）＝{len(changed)} 件")
    for c in changed:
        print("  ・", c)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")   # 控えは作らない（古い形は git に在る・恒久79番の4）
    print("書いた", OUT, "（1回目＝いまの直す相手の一覧で）")
    # ★直す相手の一覧（fix_inventory_20261024.md）は、名前を読む口から読む（F-4）＝新しい形を書いた後でないと作り直せない。
    #   一覧が変わると「①写す」の行（写す置き場）が変わるので、作り直した一覧でもう1回 写し、違えば書き直す（4-4 の2と3を1つの口で行う）。
    import subprocess
    r = subprocess.run([sys.executable, str(HERE / "gen_fix_inventory.py")], capture_output=True, text=True, env={**os.environ, "IND_ROOT": str(ROOT)})
    if r.returncode != 0:
        raise SystemExit("❌ 直す相手の一覧を作り直せない（gen_fix_inventory.py）: " + (r.stdout + r.stderr)[-800:])
    print("直す相手の一覧を作り直した（gen_fix_inventory.py）:", (r.stdout.strip().splitlines() or [""])[2][:200] if len(r.stdout.strip().splitlines()) > 2 else "")
    _AST.clear()
    data2, rows2, n_hidden2, old2 = build()
    miss2 = coverage(data2, rows2)
    if miss2:
        raise SystemExit("❌ 作り直した一覧の「①写す」の行のうち、記録にも選べる値の表にも入らない行が在る: " + "／".join(miss2))
    if compare(data, data2):
        changed2 = diff_old(have, old2)
        OUT.write_text(json.dumps(data2, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"書いた {OUT}（2回目＝作り直した一覧で。「①写す」の行 {len(rows)} → {len(rows2)}・古い形との違い {len(changed)} → {len(changed2)} 件）")
        for c in changed2:
            if c not in changed:
                print("  ・", c)
        data, n_hidden = data2, n_hidden2
    else:
        print("作り直した一覧でも同じ（2回目は書かない）")
    summary(data, n_hidden)
    return 0


# ══ 自己テスト（見本の古い記録を新しい形に写す・本物には書かない）═══════════════════════════════════════════════════
def _sample_old(name: str, part: bool = False) -> dict:
    o = {k: None for k in OLD_FIELDS}
    o.update({"名前": name, "列の名前の型": {"照らす形": [f"^{name}(\\d+)$"], "列を作る形": [f"{name}{{}}"]},
              "計算の関数": [{"登録の名前": name, "名前の型": f"{name}{{}}", "向きを持つ": True, "関数の名前": ["_rsi"], "式の文": "lambda d, n: _rsi(d.close, n)"}],
              "照合の関数・既知答え": [{"定義": "見本の定義", "流儀": "見本", "tb": None, "ext": None, "known": None, "tol": 1e-6, "tb_kind": None}],
              "代表の固定値（スキャル／デイトレ）": {"スキャル": [[7]], "デイトレ": [[14]]}, "名前に出ない軸の最初の値": None,
              "列を作る値": {"値": [[7], [14]], "出どころ": ["rsi_periods"]}, "コードの中の既定値": {name: {"引数の既定値": {}, "式の中の数": []}},
              "範囲": [{"kind": "int", "lo": 2, "hi": 21}],
              "役割・札・値域・注記": {"役割": {"区分": ["行き過ぎ"], "出どころ": "見本"}, "札": "オシレーター", "値域": {"有界": [0.0, 100.0], "分位": None}, "注記": ""},
              "方向・性質": {"方向": {"区分": "順張り値", "読み方": "大きいほど上昇の勢い"}, "性質": ["trend"]},
              "オン/オフ": {"状態": "オン", "源": ["ta"]}, "mako": None, "ライブラリとの対応": {"INDUSTRY_MAP": None, "TA_CLASS_MAP": [], "EXT2": None},
              "出口の水準": ["RSI_OB", "RSI_OS"], "V9 の名前": ["RSI"],
              "教科書の出どころ": {"by_strategy": {"パラメータの名前": ["n（期間）"]}},
              "閾値の値": {"定数": {"RSI_OB": {"value": 70.0, "imi": "買われ過ぎ", "source": "Wilder"}, "RSI_OS": {"value": 30.0, "imi": "売られ過ぎ", "source": "Wilder"}}, "調べた結果": None},
              "閾値の文": None, "閾値の代表の固定値（スキャル／デイトレ）": {"スキャル": None, "デイトレ": None}, "閾値の範囲": None,
              "食い違いの記録": [], "ほかの置き場の値": [{"置き場": "observe_diag.py:1", "名前": "見本", "値": {}}]})
    if part:
        o.update({"列の名前の型": {"照らす形": ["^帯VA\\(([\\d.]+)\\)$"], "列を作る形": ["帯VA({})"]},
                  "計算の関数": [{"登録の名前": name, "名前の型": "帯VA({})", "向きを持つ": False, "関数の名前": ["_band_lines", "_vp_by_day"],
                              "式の文": "lambda d, t: _band_lines(d, *_vp_by_day(d.close, d.volume, \"前日\")[1:], t)"}],
                  "代表の固定値（スキャル／デイトレ）": {"スキャル": [], "デイトレ": []}, "列を作る値": {"値": [[0.0015], [0.003]], "出どころ": ["sr_tol"]},
                  "コードの中の既定値": {name: {"引数の既定値": {"_vp_by_day": {"va_pct": 0.7, "rows": 24}}, "式の中の数": [1]}},
                  "範囲": None, "出口の水準": None, "閾値の値": {"定数": {}, "調べた結果": None}, "教科書の出どころ": None,
                  "役割・札・値域・注記": {"役割": {"区分": ["位置"], "出どころ": "見本"}, "札": "構造・位置", "値域": {"有界": None, "分位": None}, "注記": ""},
                  "方向・性質": {"方向": {"区分": "状態量", "読み方": "1 は帯の中"}, "性質": ["none"]}})
    return o


def selftest() -> int:
    ok = []

    def t(name, good):
        ok.append((name, bool(good)))
    # 1 名前で探す（一覧の行がずれても置き場を見つける・0か所と2か所以上は止まる）
    tmp = Path(tempfile.mkdtemp())
    p = tmp / "sample_mod.py"
    p.write_text("A = 1\nBANDS = {'ADX': 1}\n\n\ndef f1():\n    table = {'a': 1}\n    return table\n\n\ndef f2():\n    x = 0\n    table = {'b': 2}\n    sel['geo'] = 1\n    (res_lo, res_hi, sup_lo, sup_hi, mid) = 1, 2, 3, 4, 5\n    return table\n", encoding="utf-8")
    try:
        n = find_by_name(p, "BANDS", 99, 99, 0, 1)
        t("名前で探す: 一番外の代入を、行がずれていても見つける", n[0].lineno == 2)
        n = find_by_name(p, "table", 12, 12, 0, 1)
        t("名前で探す: 関数の中の代入は、その関数の中で見つける（f2 の table）", n[0].lineno == 12)
        n = find_by_name(p, "sel['geo']", 12, 12, 0, 1)
        t("名前で探す: 添字つきの相手（sel['geo']）を見つける", n[0].lineno == 13)
        n = find_by_name(p, "(res_lo, res_hi, sup_lo, sup_h", 12, 12, 0, 1)
        t("名前で探す: 組の相手を、一覧が30字で切っていても見つける", n[0].lineno == 14)
        n = find_by_name(p, "f1", 6, 7, 0, 1)
        t("名前で探す: 名前が関数の名前なら、その関数の中の行の範囲の文", [x.lineno for x in n] == [6, 7])
        try:
            find_by_name(p, "ZZZ", 1, 1, 0, 1)
            t("名前で探す: 0か所なら止まる", False)
        except SystemExit as e:
            t("名前で探す: 0か所なら止まる", "置き場が見つからない" in str(e))
        p.write_text("B = 1\nB = 2\n", encoding="utf-8")
        _AST.pop(p, None)
        try:
            find_by_name(p, "B", 5, 5, 0, 1)
            t("名前で探す: 2か所以上で一覧の行が1行（行もずれている）なら止まる", False)
        except SystemExit as e:
            t("名前で探す: 2か所以上で一覧の行が1行（行もずれている）なら止まる", "置き場が2つ以上" in str(e))
        t("名前で探す: 2か所以上でも、一覧の行がずれていなければ、その行の物", find_by_name(p, "B", 2, 2, 0, 1)[0].lineno == 2)
        t("名前で探す: 2か所で一覧の行も2行（行はずれている）なら、行の順に対応させる", find_by_name(p, "B", 7, 7, 1, 2)[0].lineno == 2)
    finally:
        _AST.pop(p, None)
        shutil.rmtree(tmp, ignore_errors=True)                # ★一時のフォルダを残さない（監査 CP94 の修正24）
    # 2 要素の定義表の3行と選べる値（F-7）
    table = read_table()["要素の定義表"]
    rt = {"位置": {"札": "構造・位置", "出どころ": "見本"}, "行き過ぎ": {"札": "オシレーター", "出どころ": "見本"}}
    pt_ = {"順張り値": {"性質": ["trend"], "出どころ": "見本"}, "状態量": {"性質": ["none"], "出どころ": "見本"}}
    t2 = table_update(table, rt, pt_, [])
    E = elem_names(t2)
    n_add = sum(1 for n in ("②-12", "③-12", "④-9", "④-10", "④-11", "④-12", "④-13") if n not in elem_names(table))   # 本物がもう新しい形なら、足す行は無い
    t("F-7: ②-12・③-12・④-9 が要素の定義表に在る", all(n in E for n in ("②-12", "③-12", "④-9")) and len(t2["要素"]) == len(table["要素"]) + n_add)
    e_by = {e["番号"]: e for e in t2["要素"]}
    t("F-7: 部品の記録に ④-10〜④-13 が、②-5〜②-7・②-9 と同じ形で在る（監査 CP94 の修正8 案B）",
      all(e_by[nw]["置く記録"] == "部品の記録" and e_by[nw]["形の決まり"] == e_by[sr]["形の決まり"] for sr, nw in PART_ROWS))
    t("F-7: ②-9・③-5 の写す元の文が、いまの写し先に合う（監査 CP94 の修正9）", SRC29_ADD in e_by["②-9"]["写す元"] and SRC35_ADD in e_by["③-5"]["写す元"])
    t("F-7: 選べる値に玉の向きと3つの表が在る", t2["選べる値"].get("玉の向き") == SIDE_CHOICES and all(k in t2["選べる値"] for k in MOVED_TABLES))
    e24 = next(e for e in t2["要素"] if e["番号"] == "②-4")
    t("F-7: ②-4 の写す元から「列を作る値」「列の名前の型」が外れた", AXIS_SRC_OLD not in e24["写す元"] and "②-12 へ移した" in e24["写す元"])
    t("F-7: 2回 呼んでも同じ", norm(table_update(t2, rt, pt_, [])) == norm(t2))
    # 3 見本の古い記録1件（RSI の形）と帯VA の形を、②③④へ写す
    old = {"RSI": _sample_old("RSI"), "帯VA": _sample_old("帯VA", part=True), "前日VAH": _sample_old("前日VAH"), "前日VAL": _sample_old("前日VAL")}
    for nm in ("前日VAH", "前日VAL"):
        old[nm]["計算の関数"][0]["関数の名前"] = ["_vp_by_day"]
        old[nm]["出口の水準"] = None
        old[nm]["閾値の値"] = {"定数": {}, "調べた結果": None}
    sets = {nm: {"名前の型": o["列の名前の型"]["列を作る形"], "照らす形": o["列の名前の型"]["照らす形"], "組": o["列を作る値"]["値"],
                 "並び": list(range(len(o["列を作る値"]["値"]))), "照らす形の値": o["列を作る値"]["値"], "出どころの鍵": o["列を作る値"]["出どころ"]}
            for nm, o in old.items()}
    base = 0
    for nm in sets:
        sets[nm]["並び"] = list(range(base, base + len(sets[nm]["組"])))
        base += len(sets[nm]["組"])
    hidden = {"RSI": [{"引数": "smooth_k", "値": 1, "出どころ": "見本", "範囲": {"lo": 1, "hi": 3, "kind": "int"}, "範囲の出どころ": "見本の資料の表"}],
              "帯VA": [{"引数": "va_pct", "値": 0.7, "出どころ": "_vp_by_day の既定値", "範囲": None, "範囲の出どころ": "固定"},
                      {"引数": "rows", "値": 24, "出どころ": "_vp_by_day の既定値", "範囲": None, "範囲の出どころ": "固定"}]}
    data = to_new(old, t2, hidden, sets)
    t("写す: 一番外が5つ", list(data) == list(TOP))
    r = data[TOP[2]]["RSI"]
    ax = r[E["②-4"]]
    t("写す: 名前に出る軸に範囲（2〜21）と代表の値（7／14）が写る", len(ax) == 2 and (ax[0]["範囲"]["lo"], ax[0]["範囲"]["hi"]) == (2, 21)
      and ax[0]["代表の値"] == {"スキャル": [7], "デイトレ": [14]} and ax[0]["名前"] == "n" and ax[0].get("資料の表の名前") == "n（期間）")
    t("写す: 範囲の kind を残す（監査 CP94 の修正7）", ax[0]["範囲"].get("kind") == "int")
    t("写す: 隠れた数字が軸に写る（smooth_k・範囲 1〜3）", ax[1]["名前"] == "smooth_k" and (ax[1]["範囲"]["lo"], ax[1]["範囲"]["hi"]) == (1, 3) and ax[1]["代表の値"] == {"スキャル": [1], "デイトレ": [1]})
    t("写す: 元の代表の固定値と範囲を②-9 に元の形で残す（監査 CP94 の修正7）", r[E["②-9"]]["代表の固定値（スキャル／デイトレ）"] == {"スキャル": [[7]], "デイトレ": [[14]]}
      and r[E["②-9"]]["範囲（search_limits.json）"] == [{"kind": "int", "lo": 2, "hi": 21}])
    t("写す: 列を作る組が ②-12 に在る（組と並び）", r[E["②-12"]]["組"] == [[7], [14]] and r[E["②-12"]]["並び"] == [0, 1] and r[E["②-12"]]["出どころの鍵"] == ["rsi_periods"])
    t("写す: 列を作る値・列の名前の型が ②-4 に残っていない", all("列" not in k for a in ax for k in a))
    t("写す: 23の欄を全部 写した（写せない欄が在れば止まる）", "照合の関数・既知答え" in r[E["②-9"]] and r[E["②-9"]]["ほかの置き場の値"][0]["置き場"] == "observe_diag.py:1")
    us = [u for u in data[TOP[3]] if u[E["③-1"]]["指標の記録"] == "RSI"]
    t("写す: 使い方の記録が4件（出口の反転・前提崩れの印 × SHORT・LONG）", len(us) == 4 and {(u[E["③-2"]], u[E["③-12"]]) for u in us}
      == {("出口の反転", "SHORT"), ("出口の反転", "LONG"), ("前提崩れの印", "SHORT"), ("前提崩れの印", "LONG")})
    rev_s = next(u for u in us if u[E["③-2"]] == "出口の反転" and u[E["③-12"]] == "SHORT")
    t("写す: SHORT の出口の反転は下側で売られ過ぎの定数（30）", rev_s[E["③-4"]] == "下側" and rev_s[E["③-5"]][0]["代表の値"]["スキャル"] == 30.0 and rev_s[E["③-5"]][0]["単位"] == "0〜100")
    pt = data[TOP[4]]["帯VA"]
    t("写す: 帯VA が部品の記録に写り、使う物が前日VAH・前日VAL", "帯VA" not in data[TOP[2]] and [u["指標の記録"] for u in pt[E["④-2"]]] == ["前日VAH", "前日VAL"])
    pax = pt[E["④-4"]]
    t("写す: 帯VA の va_pct と rows が部品の軸に写る（CP91 の修正1〜3）", [a["名前"] for a in pax] == ["t", "va_pct", "rows"]
      and pax[1]["代表の値"] == {"スキャル": [0.7], "デイトレ": [0.7]} and pax[2]["範囲"] == UNDECIDED)
    t("写す: 出力は照合の定義の文", pt[E["④-7"]] == ["見本の定義"])
    t("写す: 帯VA の名前に出る軸 t の範囲は、カタログの値の最小〜最大（監査 CP94 の修正4 案A）", pax[0]["範囲"] == {"kind": "float", "lo": 0.0015, "hi": 0.003, "dec": 4})
    t("写す: 部品の教科書の役割と照らしと出どころは ④-12・④-13 に在り、④-8 に入れ子にしない（監査 CP94 の修正8 案B）",
      pt[E["④-12"]]["区分"] == ["位置"] and "照合の関数・既知答え" in pt[E["④-13"]] and set(pt[E["④-8"]]) == {"状態", "源", "mako", "作った元"})
    adx = {"ADX見本": _sample_old("ADX見本")}                  # 上側と下側に同じ定数を使う種類の形（ADX の ADX_TREND）
    adx["ADX見本"].update({"出口の水準": ["ADX_TREND", "ADX_TREND"],
                          "閾値の値": {"定数": {"ADX_TREND": {"value": 25.0, "imi": "トレンド成立の目安", "source": "Wilder"}}, "調べた結果": None}})
    a_sets = {"ADX見本": {"名前の型": ["ADX見本{}"], "照らす形": ["^ADX見本(\\d+)$"], "組": [[7], [14]], "並び": [0, 1],
                          "照らす形の値": [[7], [14]], "出どころの鍵": ["rsi_periods"]}}
    au = to_new(adx, t2, {}, a_sets)[TOP[3]]
    t("写す: 上側と下側に同じ定数を使う種類（ADX の形）の使い方の記録4件の出どころに、分岐の写し（教科書の使い方ではない）と書く（監査 CP94 の修正20）",
      len(au) == 4 and all(EXIT_NOTE_SAME in u[E["③-11"]]["出どころ"] for u in au)
      and not any(EXIT_NOTE_SAME in u[E["③-11"]]["出どころ"] for u in us))
    # 3-2 代表の値を、資料の表のパラメータの名前で軸に合わせる（並びの番号だけでは合わせない・監査 CP94 の修正1・まこさん「案B」）
    kst_p = ["roc1", "roc2", "roc3", "roc4", "sma1", "sma2", "sma3", "sma4", "signal"]
    kst_v = [10, 15, 20, 30, 10, 10, 10, 15, 9]

    def _one(name, tpl, pnames, rep, hid, fn, src, combos, ranges=None):
        o = _sample_old(name)
        o.update({"列の名前の型": {"照らす形": [], "列を作る形": [tpl]}, "教科書の出どころ": {"by_strategy": {"パラメータの名前": pnames}},
                  "代表の固定値（スキャル／デイトレ）": rep, "名前に出ない軸の最初の値": None, "範囲": ranges,
                  "計算の関数": [{"登録の名前": name, "名前の型": tpl, "向きを持つ": True, "関数の名前": [], "式の文": src}]})
        hh = [{"引数": a, "値": v, "出どころ": "見本", "範囲": None, "範囲の出どころ": "固定"} for a, v in hid]
        return axes_for(o, hh, {"組": combos}, fn)
    UNPLACED.clear()
    kst = _one("KSTシグナル", "KSTシグナル{}", kst_p, {"スキャル": [kst_v], "デイトレ": [kst_v]}, list(zip(kst_p[:8], kst_v[:8])),
               lambda d, g_, roc1=None: 0, "lambda d, g_, roc1=None: _pta6.kst(close=d.close, signal=g_, roc1=roc1)", [[9]],
               [{"kind": "int", "lo": 9, "hi": 9}])
    t("写す: KSTシグナルの形＝名前に出る軸 g_ に資料の表の signal の値（9）が写り、roc1 に roc1 の値（10）が写る（並びの番号で割り当てない）",
      kst[0]["名前"] == "g_" and kst[0]["代表の値"] == {"スキャル": [9], "デイトレ": [9]} and kst[0].get("資料の表の名前") == "signal"
      and kst[1]["名前"] == "roc1" and kst[1]["代表の値"] == {"スキャル": [10], "デイトレ": [10]} and kst[1].get("資料の表の名前") == "roc1")
    kama = _one("KAMA傾き%", "KAMA傾き%{}", ["er_period", "fast_sc", "slow_sc"], {"スキャル": [[10, 2, 30]], "デイトレ": [[10, 2, 30]]},
                [("fast", 2), ("slow", 30), ("slope_n", 5)], lambda d, n, f=None, slope_n=5, **kw: 0,
                "lambda d, n, f=_mafn, slope_n=5, **kw: f(d, n, **kw).pct_change(slope_n) * 100", [[10]])
    t("写す: KAMA傾き% の形＝名前の合わない軸に、資料の表の値を並びで入れない（資料の表に合わない値が在るので、n も fast も「まだ決めていない」・監査 CP95）",
      kama[0]["代表の値"] == {"スキャル": UNDECIDED, "デイトレ": UNDECIDED} and kama[1]["代表の値"] == {"スキャル": UNDECIDED, "デイトレ": UNDECIDED}
      and "資料の表の名前" not in kama[1])
    tenkan = _one("転換線", "close vs 転換線%({})", ["転換線の期間", "基準線の期間", "先行スパンBの期間"], {"スキャル": [[9, 26, 52]], "デイトレ": [[9, 26, 52]]},
                  [], lambda d, t_: 0, "lambda d, t_: 0", [[9]])
    t("写す: 転換線の形＝名前の合わない名前に出る軸は、空の並びでなく「まだ決めていない」", tenkan[0]["代表の値"] == {"スキャル": UNDECIDED, "デイトレ": UNDECIDED})
    t("写す: 合わない値の一覧に、KAMA傾き% の3つと転換線の3つが入る", sum(1 for u in UNPLACED if u["記録"] in ("KAMA傾き%", "転換線")) == 6
      and not any(u["記録"] == "KSTシグナル" for u in UNPLACED))
    alma = _one("close vs ALMA%", "close vs ALMA%{}", ["window（本数）", "offset", "sigma"], {"スキャル": [[9, 0.85, 6]], "デイトレ": [[9, 0.85, 6]]},
                [("distribution_offset", 0.15), ("sigma", 6)], lambda d, n, f=None, **kw: 0, "lambda d, n, f=_mafn, **kw: 0", [[9]])
    t("写す: 向きが逆の軸（ALMA の distribution_offset）には写さず、出どころに書く（監査 CP94 の修正1・CP91 の修正12）",
      alma[1]["代表の値"] == UNDECIDED and "向きが逆" in alma[1]["出どころ"]["代表の値"] and alma[2]["代表の値"] == {"スキャル": [6], "デイトレ": [6]})
    bad = old["RSI"].copy()
    old2 = dict(old)
    old2["RSI"] = bad
    try:
        to_new(old2, {**table, "要素": [e for e in table["要素"] if e["番号"] != "②-12"]}, hidden, sets)   # ②-12 を除いた表（本物の表が新しい形でも、②-12 が無い表で試す＝監査 CP95 の修正1）
        t("写す: 要素の定義表に ②-12 が無ければ止まる", False)
    except SystemExit as e:
        t("写す: 要素の定義表に ②-12 が無ければ止まる", "要素の定義表に無い番号" in str(e))
    # 4 読む口が新しい形を読める（決まり5つの読む口で開く）
    sys.path.insert(0, str(PR / "indicators"))
    import indicators as ind  # noqa: E402
    try:
        rd = ind.Indicators(copy.deepcopy(data), timeframes=["5m"])
        t("読む口: 写した物を読み込める（選べる値の照らしを通る）", rd.names("指標の記録") == ["RSI", "前日VAH", "前日VAL"] and list(rd.parts()) == ["帯VA"])
        t("読む口: 列を作る組を並びの順で返す", [x["記録"] for x in rd.column_sets()] == ["RSI", "RSI", "帯VA", "帯VA", "前日VAH", "前日VAH", "前日VAL", "前日VAL"])
    except SystemExit as e:
        t(f"読む口: 写した物を読み込める（{e}）", False)
    # 5 写す元（161-2 のやることの表 F-4）＝列を作る組と出どころの鍵を作る所（build_old の cols・catalog_sets）は、
    #   build_catalog でなく写す元の関数 _catalog_from_config を呼ぶ（構文の木で、呼んでいる属性の名前を見る）
    import ast as _ast5
    _calls5 = {}
    for _n5 in _ast5.walk(_ast5.parse(Path(__file__).read_text(encoding="utf-8"))):
        if isinstance(_n5, _ast5.FunctionDef) and _n5.name in ("build_old", "catalog_sets"):
            _calls5[_n5.name] = {c.func.attr for c in _ast5.walk(_n5) if isinstance(c, _ast5.Call) and isinstance(c.func, _ast5.Attribute)}
    t("写す: 写す元は _catalog_from_config で、build_catalog を呼ばない（161-2 の F-4）",
      len(_calls5) == 2 and all("_catalog_from_config" in v and "build_catalog" not in v for v in _calls5.values()))
    for name, good in ok:
        print(f"  {'✅' if good else '❌'} {name}")
    n_ng = sum(1 for _n, g in ok if not g)
    print(f"写すプログラムの自己テスト＝{len(ok) - n_ng}/{len(ok)}")
    return 0 if n_ng == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rewrite", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.verify:
        return verify()
    if a.rewrite:
        return rewrite()
    have = read_table()
    if "記録" in have:
        raise SystemExit(f"❌ {OUT} は古い形（一番外に「記録」）＝--rewrite で1回だけ写し直す")
    data, rows, n_hidden, _old = build()
    miss = coverage(data, rows)
    if miss:
        raise SystemExit("❌ 直す相手の一覧の「①写す」の行のうち、記録にも選べる値の表にも入らない行が在る: " + "／".join(miss))
    if compare(have, data):
        raise SystemExit(f"❌ {OUT} はもう在り、写す元から作り直した物と違う（違いは --verify で見る。162番までは、値を写す元で直し、--rewrite で作り直す＝監査 CP94 の修正14 案B）")
    print(f"{OUT} はもう在り、写す元から作り直した物と同じ（書かない）")
    summary(data, n_hidden)
    return 0


if __name__ == "__main__":
    sys.exit(main())
