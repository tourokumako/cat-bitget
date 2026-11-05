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
    """記録 → {名前の型, 照らす形, 組, 並び, 出どころの鍵}。カタログの列（observe_diag._catalog_from_config＝写す元の関数・162番まで）を上から順にたどる。"""
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


def form_spec() -> dict:
    """engine_tuner_exec.py の FORM_SPEC（条件の書き方ごとの決まりの表）を読む。走らせず、写しも持たない。"""
    import ast
    tree = ast.parse((PR / "engine_tuner_exec.py").read_text(encoding="utf-8"))
    for n in tree.body:
        if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FORM_SPEC":
            return {k.value: {kw.arg: ast.literal_eval(kw.value) for kw in v.keywords} for k, v in zip(n.value.keys, n.value.values)}
    raise SystemExit("FORM_SPEC が見つからない")


# ── 教科書の形（要素の命名の決まり＝要件定義書_レベル4_指標の構造.md の第3章の2・ToDo の271番）────────────
# ★教科書の鍵と定義表の要素の対応は、この3つの表だけに持つ。定義表の要素の名前が変わっても、番号で引くのでここは直さない。
#   教科書の鍵の名前を変えるときは、この表と見本と依頼書を直す。
TEXTBOOK_TOP = {   # 教科書の一番上の鍵 → 定義表の番号（指標の記録, 部品の記録）。None＝その記録に要素が無い
    "名前": ("②-1", "④-1"), "照らしと出どころ": ("②-9", "④-13"), "教科書の役割の候補": ("②-7", "④-12"),
    "値の単位と値域": ("②-5", "④-10"), "値の読み方の候補": ("②-6", "④-11"), "出力": ("②-3", "④-7"),
    "確定と期間": ("②-8", None), "パラメータの軸": ("②-4", "④-4"), "閾値の範囲の候補": ("②-11", "④-5"),
    # ★2026-11-05 まこさん「少なくなってないか？」＝M2〜M4 の法則の手順から足した要素（要件定義書の一覧の「CC が足した要素」）
    "計算の入力": ("②-14", None), "中心線": ("②-15", None), "先行か遅行か": ("②-16", None), "遅れの長さ": ("②-17", None),
    "効く相場と効かない相場": ("②-18", None), "線の位置": (None, "④-14"), "破れの定義": (None, "④-15")}
TEXTBOOK_TOP_EXTRA = {"置く記録", "注記", "使い方の記録", "探した記録", "閾値を持たない理由"}     # 定義表の要素でない、教科書だけの鍵
TEXTBOOK_ROW = {   # 使い方の行の鍵 → 定義表の番号
    "使い方の種類": "③-2", "場面と型": "③-3", "向き": "③-4", "閾値": "③-5", "パラメータの代表の値の候補": "③-6",
    "時間足": "③-7", "前処理": "③-8", "合図の形のパラメータ": "③-9", "玉の向き": "③-12", "使える条件の形": "③-13",
    "確認に使う相手": "③-15", "入る線と出る線": "③-16"}                                   # ★2026-11-05 足した要素
TEXTBOOK_ROW_EXTRA = {"使う出力", "時間足の組", "出どころ", "注記"}                              # ③-1・③-7・③-11 の中に入れる欄と、注記
TEXTBOOK_OLD = {"値": "候補の値", "注": "注記", "_注": "注記"}                                   # 古い形の候補の行の鍵 → 新しい名前
# 候補の行と、要素の中の欄の名前（命名の決まり＝候補の行の鍵はどの要素でも同じ）。鍵＝教科書の鍵、値＝中に書いてよい欄。"*" は候補の行の共通の欄
CAND_KEYS = {"候補の値", "挙げた値", "範囲の形", "文の時間足", "逐語", "URL", "確かめの強さ", "注記", "HTTP", "読んだ日", "当たる文"}
TEXTBOOK_SHAPE = {
    "照らしと出どころ": {"元の指標", "教科書の計算の式"},
    "教科書の計算の式": CAND_KEYS,
    "教科書の役割の候補": CAND_KEYS | {"区分"},
    "値の単位と値域": CAND_KEYS | {"単位", "値域"},
    "値域": {"有界", "分位"},
    "値の読み方の候補": CAND_KEYS | {"区分", "読み方", "向きを持つ"},
    "出力": CAND_KEYS | {"名前", "組の相手"},
    "確定と期間": CAND_KEYS | {"確定に要る本数", "未来を使う作りか"},
    "未来を使う作りか": CAND_KEYS,
    "パラメータの軸": {"名前", "資料の表の名前", "意味", "種類", "代表の値の候補", "範囲の候補", "軸どうしの決まり", "注記"},
    "代表の値の候補": {"既定", "スキャル", "デイトレ"},
    "既定": CAND_KEYS, "スキャル": CAND_KEYS, "デイトレ": CAND_KEYS,
    "範囲の候補": CAND_KEYS,
    "軸どうしの決まり": CAND_KEYS | {"決まり"},
    # ★2026-11-05 に定義表へ足した要素（候補の行の並び）
    "計算の入力": CAND_KEYS, "中心線": CAND_KEYS, "先行か遅行か": CAND_KEYS, "遅れの長さ": CAND_KEYS, "効く相場と効かない相場": CAND_KEYS,
    "確認に使う相手": CAND_KEYS | {"相手", "役目"}, "入る線と出る線": CAND_KEYS, "線の位置": CAND_KEYS | {"名前"}, "破れの定義": CAND_KEYS,
    "閾値の範囲の候補": CAND_KEYS | {"形", "単位"},
    "閾値": {"形", "単位", "代表の値の候補", "注記"},
    "合図の形のパラメータ": {"名前", "代表の値の候補", "注記"},
    "場面と型": {"場面", "型"},
    "出どころ": CAND_KEYS,
    "探した記録": {"要素", "検索の語", "開いたページ", "注記"},
    "開いたページ": CAND_KEYS,
    "閾値を持たない理由": CAND_KEYS,
}


# ── 依頼書の表を作る（ToDo の271番・恒久69番＝手で書かない。まこさん 2026-11-05「もう自動生成してくれないか？」）────────
REQUEST_MD = ROOT / ".claude" / "instructions" / "cloud_textbook_format_20261104.md"
SAMPLES = [Path(__file__).parent / "research" / "textbook_sample_rsi.json", Path(__file__).parent / "research" / "textbook_samples_20261105.json"]
REQ_START, REQ_END = "<!-- TEXTBOOK_REQ_AUTO_START", "<!-- TEXTBOOK_REQ_AUTO_END -->"
EXTRA_CHOICES = {"役割の区分の表": {"ローソクの形": {"札": "ローソク", "出どころ": "まこさん 2026-11-05「追加していい」（写しだけ・本物は取り込みの工事で）"}}}
FIRST_NINE = ("ADX", "ATR%", "BB%b", "BB幅", "DI差", "RSI", "基準線", "包み足", "帯pivot")   # 先に通す指標（要件定義書 第3章の3 の表5）
SIGNAL_PARAM_OF_FORM = {"streak": ["持続の本数"], "within_n": ["何本以内か"], "barssince": ["何本前か"], "cross": ["組の相手", "開き"],
                        "touch": ["タッチの許容幅"], "slope": ["傾きの本数"], "slope_avg": ["傾きの本数", "平均の本数"], "diff": ["組の相手"]}
ELEMENT_RENAME = {   # 定義表の名前 → （伝わる名前, engine_tuner で何に使うか, 教科書から読む物）。定義表の名前を直す工事（ToDo の275番）で、定義表そのものをこの名前にする。それまで依頼書の表はここから出す
    "名前": ("名前", "条件の中で指標を名指しする", "指標データの名前（値を入れない。RSI であって RSI14 ではない）"),
    "出力": ("出力の一覧", "条件の材料にする出力（%K・%D など）を選ぶ", "指標が出す値の一覧と、出力どうしの組"),
    "パラメータの軸": ("パラメータの一覧", "最初の段階は代表の値で固定し、最後の段階は範囲から探す", "パラメータ（期間など）ごとに、代表の値（スキャル／デイトレ）と範囲の候補、軸どうしの決まり、出どころ"),
    "値の単位と値域": ("値の単位と値域", "閾値の単位を決め、ほかの指標と比べられるかを見る", "値の単位（%・0〜100 など）と、取りうる値の幅"),
    "値の読み方": ("値の読み方", "向きを持つなら絶対値の変換を掛ける。順張り値か状態量かで条件の書き方を選ぶ", "値が大きいと何を意味するか。向きを持つか"),
    "教科書の役割": ("役割", "法則が求める役目（向き・強さ・勢い・行き過ぎ・値動きの幅・出来高・位置・ローソクの形）に当てはまる指標を選ぶ", "教科書が言う、この指標の役割。複数 持てる"),
    "確定と期間": ("確定に要る本数・未来を使わない作りか・使えるデータの期間", "未来を見ない作りかを確かめる（漏れの検査）。確定まで何本 待つかを決める", "値が確定するまでに要る足の本数。未来の足を見ずに計算できるか。使えるデータの期間"),
    "照らしと出どころ": ("教科書の出どころ・ライブラリとの対応・食い違いの記録", "値の根拠を辿る（監査が照らす）", "教科書の逐語と URL。ライブラリとの対応。食い違いの記録"),
    "閾値の範囲": ("閾値の範囲", "最後の段階で閾値を探す幅にする", "指標ごとに一つ（閾値の形が二つ以上なら形ごとに一つ）の、範囲の候補"),
    "確かめの強さ": ("確かめの強さ", "値の信頼の度合い（弱い値は後回しにできる）", "指標データの値を、教科書でどこまで確かめたか"),
    "指す物": ("使う指標と出力", "条件がどの列を読むかを決める", "この使い方の行が、どの指標（または部品）のどの出力を使うか"),
    "使い方の種類": ("使い方の種類", "条件の役目を決める（場面の判定・入る合図・入ってはいけない場面を除く条件・合図が本物かを確かめる条件・出口の水準を作る材料・出口の反転・前提崩れの印）", "教科書がその指標をどの役目で使っているか"),
    "場面と型": ("場面と入口の型", "どの場面（レンジ・上げ・下げ・スパイク）の法則で使うかを決める", "教科書が言う場面と、入口の型（down・flat_up など）"),
    "向き": ("閾値を超える向き", "条件の側（上側・下側・上へ抜ける・下へ抜ける）を決める", "閾値のどちら側で使うか"),
    "閾値": ("閾値の代表の値", "最初の段階で固定する閾値", "この使い方で使う閾値。形・単位・代表の値（スキャル／デイトレ）・出どころ"),
    "パラメータの代表の値": ("パラメータの代表の値（この使い方だけの上書き）", "使い方ごとに代表の値を変える", "この使い方だけで使うパラメータの代表の値"),
    "時間足": ("使える時間足", "条件を見る足を決める", "教科書が言う足の一覧と、二〜三本の組"),
    "前処理": ("値に掛ける変換", "条件の前に値を変換する（絶対値・二本の差・決まった数との差）", "指標の値に掛ける変換"),
    "合図の形のパラメータ": ("合図の本数と幅", "条件の書き方（streak・cross・touch・within_n・slope）の本数と幅を決める", "持続の本数・開き・タッチの許容幅・何本以内か・傾きの本数・平均の本数・組の相手"),
    "玉の向き": ("売買の方向", "ショートとロングのどちらの玉の条件にするかを決める", "教科書がその使い方をどちらの方向で言っているか"),
    "使える条件の形": ("使える条件の書き方", "条件の書き方（level・band・cross など）を選ぶ", "この使い方で使ってよい条件の書き方"),
    "計算の関数": ("計算する関数の名前", "（教科書から読まない。プログラムが持つ）", ""),
    "列を作る組": ("列の計算の設定", "（教科書から読まない。プログラムが持つ）", ""),
    "オン/オフ": ("オン/オフ", "（教科書から読まない。頼んだ側が決める）", ""),
    "オン/オフと出どころ": ("オン/オフ", "（教科書から読まない。頼んだ側が決める）", ""),
    "未来を使ってよいか": ("未来を使ってよいか", "（教科書から読まない。正解ラベルの行は作らない）", ""),
    "上位足の写し方": ("上の足の値を五分足へ写す方法", "（教科書から読まない。頼んだ側の設定が持つ）", ""),
    "使う物": ("部品が使う指標と部品", "（教科書から読まない。プログラムが持つ）", ""),
    "作り方の切り替え": ("作り方の選択肢", "（教科書から読まない。プログラムが持つ）", ""),
    # ★2026-11-05 に定義表へ足した要素（M2〜M4 の法則の手順から。要件定義書の一覧の「CC が足した要素」）
    "計算の入力": ("計算の入力", "出来高を使う指標かの区分（役割「出来高」）", "終値・高値安値・出来高のどれから計算するか"),
    "中心線": ("中心線", "中心線をまたぐ使い方（cross の閾値）", "またぐと意味が変わる線の値"),
    "先行か遅行か": ("先行か遅行か", "確認の相手の選び方（M3 手順6）", "合図が値動きより早いか遅いか"),
    "遅れの長さ": ("遅れの長さ", "確認の相手の選び方（M3 手順6）", "合図が値動きからどれだけ遅れるか"),
    "効く相場と効かない相場": ("効く相場と効かない相場", "入ってはいけない場面を除く条件の元（M3 手順5）", "どの相場で効き、どの相場で騙しが多いかの文"),
    "確認に使う相手": ("確認に使う相手", "合図が本物かを確かめる条件の相手（M3 手順6）", "この合図を確かめる相手の指標と役目"),
    "入る線と出る線": ("入る線と出る線", "判定に入る水準と抜ける水準を別にする（M2 手順7・法則 C6）", "入る線と出る線の幅"),
    "線の位置": ("線の位置", "入口の型 S1（上端で売る）・利確の線（M3 手順1・M4 手順2）", "帯の線の位置の名前（上端・中央・下端・縁）"),
    "破れの定義": ("破れの定義", "前提崩れの印（M4 手順5）", "帯の外に出たと言う条件の文"),
}

NOT_COLLECTED = {   # 教科書で集めない要素と、その理由（定義表の要素のうち TEXTBOOK_TOP・TEXTBOOK_ROW に無い物は、全部ここに理由が要る＝無ければ止まる）
    "②-1": "指標データの名前のまま使う（教科書の `名前` に写すだけ）", "②-2": "プログラムの関数の名前。教科書には無い", "②-10": "指標を使うか使わないかの切り替え。頼んだ側が決める",
    "②-12": "プログラムが指標の列を計算するための設定。頼んだ側が持つ",
    "③-1": "その行がどの指標の物かは、教科書の `名前` で決まる。使う出力だけ `使う出力` で集める", "③-10": "正解ラベル（未来を見る答え）の行は作らない", "③-11": "出どころは行の `出どころ` で集める。オン/オフは頼んだ側が後で決める",
    "③-14": "上の足の値を5分足へ写す方法。頼んだ側の設定ファイル（observe_config.json）が持つ", "④-1": "指標データの名前のまま使う（教科書の `名前` に写すだけ）", "④-2": "部品が使う指標の名前。プログラムが持つ", "④-3": "プログラムの関数の名前。教科書には無い", "④-6": "部品の作り方の切り替え。プログラムが持つ",
    "④-8": "部品を使うか使わないかの切り替え。頼んだ側が決める", "④-9": "プログラムが部品の列を計算するための設定。頼んだ側が持つ"}
REQ_MAP = [   # 要件の行 → 教科書の欄（行の文に在るはずの語で、行がずれていないかを照らす）
    ("core_requirements_full.md", 28, "閾値", "`閾値の範囲の候補`"), ("core_requirements_full.md", 29, "パラメータ", "`パラメータの軸` の `範囲の候補`"),
    ("core_requirements_full.md", 38, "代表的な固定値", "`代表の値の候補` の `スキャル`・`デイトレ`（パラメータと閾値の両方）"),
    ("core_requirements_full.md", 47, "戦略（スキャル／デイトレ）ごと・指標ごとに", "同上"), ("core_requirements_full.md", 53, "既定の値", "`代表の値の候補` の `既定`"),
    ("core_requirements_full.md", 60, "指標ごとに1つ", "取り込みが候補の最小〜最大を一つの範囲にする（書き方の決まり 5番）"),
    ("core_requirements_full.md", 62, "指標名に閾値やパラメータの値を固定で入れて", "`名前` は指標データのまま。値は候補の行に"),
    ("core_requirements_full.md", 26, "役割に基づき、法則に則って", "`教科書の役割の候補`・使い方の行の `使い方の種類`・`場面と型`・`玉の向き`・`向き`"),
    ("core_requirements_full.md", 30, "時間足", "`時間足`・`時間足の組`・`文の時間足`（選べる語だけ）"),
    ("core_requirements_full.md", 70, "出どころにする資料", "候補の行の `逐語`・`URL`・`確かめの強さ`"),
    ("core_requirements_full.md", 95, "置き場の1か所を直せば済む", "一種・一要素の調べ直しのファイル（「出す物」）"),
    ("cat_requirements.md", 611, "USD絶対値の閾値", "`閾値` と `閾値の範囲の候補` の単位に「値段」「ドル」を書かない（書き方の決まり 12番）"),
    ("要件定義書_レベル4_指標の構造.md", 0, "1つの指標が、複数の役割を持てること", "`教科書の役割の候補` の複数行"),
    ("要件定義書_レベル4_指標の構造.md", 0, "「向きを持つ」の欄で", "`値の読み方の候補` の `向きを持つ`・`前処理` の「絶対値」"),
    ("要件定義書_レベル4_指標の構造.md", 0, "閾値の形を複数持てること", "`閾値` の行の並び（形・単位ごと）・`閾値の範囲の候補`"),
    ("要件定義書_レベル4_指標の構造.md", 0, "代表の固定値を、戦略と使い方", "`パラメータの代表の値の候補`（使い方の行）・`パラメータの軸` の `代表の値の候補`"),
    ("要件定義書_レベル4_指標の構造.md", 0, "指標の記録に、確定に要る本数と、未来を使わない作りかの印", "`確定と期間`（`確定に要る本数`・`未来を使う作りか`）"),
    ("要件定義書_レベル4_指標の構造.md", 0, "向きを、使い方（行き過ぎを見る・向きを見る）と場面", "使い方の行ごとの `向き`"),
    ("要件定義書_レベル4_指標の構造.md", 0, "複数の出力（%K と %D など）と、出力どうしの組", "`出力` の `名前`・`組の相手`"),
    ("要件定義書_レベル4_指標の構造.md", 0, "合図の型ごとのパラメータ", "`合図の形のパラメータ`"),
    ("要件定義書_レベル4_指標の構造.md", 0, "閾値の単位（値段・%・0〜100・分位）と形", "`閾値` の `形`・`単位`"),
    ("要件定義書_レベル4_指標の構造.md", 0, "帯の線を、パラメータつきの位置の指標として", "`置く記録`＝部品の記録・`使う出力`"),
    ("要件定義書_レベル4_指標の構造.md", 0, "ローソクの形の指標を、役目とパラメータつきで", "役割の区分「ローソクの形」"),
    ("要件定義書_レベル4_指標の構造.md", 0, "指標を「出口の水準を作る材料」として使えるようにする", "使い方の種類「出口の水準を作る材料」"),
    ("要件定義書_レベル4_指標の構造.md", 0, "出口用の閾値（反転の水準など）を、入口とは別に", "使い方の種類「出口の反転」の行の `閾値`"),
    ("要件定義書_レベル4_指標の構造.md", 0, "使える時間足を、段と役割ごとに", "集めない（engine_tuner の型の表が持つ）"),
    ("要件定義書_レベル4_指標の構造.md", 0, "系統ごとの本数の上限を", "集めない（探す設定 search_limits.json の k_max が持つ）"),
]
REQ_DIRS = {"core_requirements_full.md": ROOT / ".claude" / "rules", "cat_requirements.md": SDK / ".claude" / "rules",
            "要件定義書_レベル4_指標の構造.md": SDK / ".claude" / "rules"}


def _req_line(fname: str, line: int, must: str) -> tuple:
    """要件の行を実物から読む。行番号が 0 なら語で探す。語が無ければ止まる（行がずれた・文が変わった）。"""
    lines = (REQ_DIRS[fname] / fname).read_text(encoding="utf-8").splitlines()
    if line:
        text = lines[line - 1]
        if must not in text:
            raise SystemExit(f"❌ 要件の行がずれた: {fname}:{line} に「{must}」が無い")
        return line, text.strip()
    hits = [i + 1 for i, t in enumerate(lines) if must in t]
    if not hits:
        raise SystemExit(f"❌ 要件の文が無い: {fname} に「{must}」")
    return hits[0], lines[hits[0] - 1].strip()


def _sample_tags(t: dict, table: dict) -> list:
    """見本1種が示す形（走らせて見本から数える）。"""
    tags = []
    rows = t.get("使い方の記録") or []
    top_missing = [k for k in TEXTBOOK_TOP if k not in t and TEXTBOOK_TOP[k][0 if (t.get("置く記録") or "指標の記録") == "指標の記録" else 1]]
    if top_missing and "使い方の記録" not in t or (top_missing and len(top_missing) >= len(TEXTBOOK_TOP) - 2):
        tags.append("部分の見本")
    if t.get("置く記録"):
        tags.append(f"`置く記録`＝{t['置く記録']}")
    if t.get("閾値を持たない理由"):
        tags.append("`閾値を持たない理由`")
    if len(t.get("値の読み方の候補") or []) > 1:
        tags.append("値の読み方の候補が二つ以上")
    tags += [f"値の読み方の区分「{c['区分']}」" for c in t.get("値の読み方の候補") or [] if c.get("区分")]
    tags += [f"役割「{c['区分']}」" for c in t.get("教科書の役割の候補") or [] if c.get("区分")]
    fin = (t.get("確定と期間") or {}).get("未来を使う作りか")
    if fin and fin.get("候補の値") is not None:
        tags.append("`未来を使う作りか`")
    for a in t.get("パラメータの軸") or []:
        if a.get("軸どうしの決まり"):
            tags.append("軸どうしの決まり")
        rep = a.get("代表の値の候補") or {}
        if not [c for k in ("スキャル", "デイトレ") for c in rep.get(k) or [] if "候補の値" in c] and [c for c in rep.get("既定") or [] if "候補の値" in c]:
            tags.append("代表の値が既定だけの軸")
    for c in t.get("閾値の範囲の候補") or []:
        if c.get("単位") is None and c.get("形"):
            tags.append("単位が選べる語に無い閾値")
    for x in rows:
        tags += [f"条件の書き方 {f}" for f in x.get("使える条件の形") or []]
        tags += [f"前処理「{p}」" for p in x.get("前処理") or []]
        for th in x.get("閾値") or []:
            tags.append(f"閾値の形「{th.get('形')}」")
            cands = {k: [c for c in (th.get("代表の値の候補") or {}).get(k) or [] if "候補の値" in c] for k in ("スキャル", "デイトレ", "既定")}
            if cands["既定"] and not cands["スキャル"] and not cands["デイトレ"]:
                tags.append("閾値の代表の値が既定だけ")
            if len({c["候補の値"] for c in cands["既定"] + cands["スキャル"] + cands["デイトレ"]}) >= 2 and "band" in (x.get("使える条件の形") or []):
                tags.append("帯の両端が文に在る")
        for p in x.get("合図の形のパラメータ") or []:
            has = any("候補の値" in c for k in ("スキャル", "デイトレ", "既定") for c in (p.get("代表の値の候補") or {}).get(k) or [])
            tags.append(f"{p.get('名前')}の値が{'書いてある' if has else '書いていない'}行")
        if x.get("時間足の組"):
            tags.append("`時間足の組`")
        if x.get("使う出力"):
            tags.append("`使う出力`")
        st = x.get("場面と型") or {}
        if st.get("場面"):
            tags.append(f"場面「{st['場面']}」")
        if "玉の向き" not in x and x.get("使い方の種類") not in ("出口の反転", "前提崩れの印"):
            tags.append("売買の方向が文に無い行（`玉の向き` を書かない）")
        if x.get("使える条件の形") and not any(th.get("代表の値の候補") for th in x.get("閾値") or []) and not x.get("合図の形のパラメータ"):
            tags.append("合図の形のパラメータに、値も組の相手も書いていない行（空で残す）")
    return list(dict.fromkeys(tags))


def request_block() -> str:
    """依頼書の表の部分を、定義表・FORM_SPEC・法則の条件の書き方・見本・要件の文書・オン/オフの表から作る。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("indicators_reader", PR / "indicators" / "indicators.py")
    ind = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ind)
    data = ind.load().data
    table = data["要素の定義表"]
    E = {e["番号"]: e for e in table["要素"]}
    cv = copy.deepcopy(table["選べる値"])
    for k, v in EXTRA_CHOICES.items():
        cv[k] = {**cv[k], **v}
    forms = [f["名前"] for f in jload(PR / "laws" / "laws.json")["条件の書き方"]]
    sw = jload(SDK / ".claude" / "ratchet" / "indicator_switch.json")
    targets = sorted(set(sw["sources"]["ta"]) | set(sw["sources"]["law"]) | {"包み足"})
    missing_nine = [n for n in FIRST_NINE if n not in targets]
    if missing_nine:
        raise SystemExit(f"❌ 先に通す指標が相手に無い: {missing_nine}")
    samples = []
    for p in SAMPLES:
        got = jload(p)
        samples += got if isinstance(got, list) else [got]
    sig_names = sorted({n for v in SIGNAL_PARAM_OF_FORM.values() for n in v})
    out = []
    # 0 作る要素の一覧（engine_tuner が法則に沿って指標を組み合わせるために、教科書から JSON へ読み込む要素。名前は ELEMENT_RENAME）
    inside0 = {"②-13": "候補の行の `確かめの強さ`"}
    where = {}
    for key, (a, b) in TEXTBOOK_TOP.items():
        for no in (a, b):
            if no:
                where[no] = f"`{key}`"
    for key, no in TEXTBOOK_ROW.items():
        where[no] = f"`使い方の記録` の行の `{key}`"
    for no, w in inside0.items():
        where[no] = w
    out += ["### 作る要素の一覧（プログラムが定義表から作った）", "",
            "engine_tuner は、トレードの法則に沿って指標の要素を組み合わせ、条件を作ります。そのために教科書から JSON へ読み込む要素が、下の表です。",
            "「要素」が、意味の分かる名前です。「教科書での項目の名前」が、教科書のファイル（JSON）に書く項目の名前です（今は定義表の古い名前のままです。定義表の名前を直す工事が別に在り、直った後は「要素」と同じ名前になります）。",
            "「置き場」は、指標データの中のどこに在る要素かです＝指標の記録（指標そのものの情報）・使い方の記録（その指標をいつ・どう使うかの行）・部品の記録（帯の線など、指標から作る部品）。指標の記録と部品の記録に同じ要素が在る物は、一行にまとめてあります。", "",
            "| 要素 | engine_tuner で何に使うか | 教科書から読む物 | 置き場 | 教科書での項目の名前（JSON の key） |", "|---|---|---|---|---|"]
    def _no_key(no):
        mark, num = no.split("-", 1)
        return ("①②③④".find(mark), int(num) if num.isdigit() else 999)
    place = {"②": "指標の記録", "③": "使い方の記録", "④": "部品の記録"}
    rows0, seen0, skipped0 = [], {}, []
    for no in sorted(E, key=_no_key):
        e = E[no]
        old = e["要素の名前"]
        if old not in ELEMENT_RENAME:
            raise SystemExit(f"❌ ELEMENT_RENAME に無い定義表の名前: {old}（{no}）")
        new, use, read = ELEMENT_RENAME[old]
        if no in where:
            k = (old, where[no])
            if k in seen0 and no[0] == "④":                  # 指標の記録と同じ要素が部品の記録にも在る＝一行にまとめる
                rows0[seen0[k]]["置き場"] += "・部品の記録"
                continue
            seen0[k] = len(rows0)
            rows0.append({"要素": new, "使う": use, "読む": read, "置き場": place[no[0]], "鍵": where[no]})
        elif no in NOT_COLLECTED:
            if new not in [s[0] for s in skipped0]:
                skipped0.append((new, NOT_COLLECTED[no]))
        else:
            raise SystemExit(f"❌ 定義表の要素で、集めるとも集めないとも決めていない物: {no}")
    for r in rows0:
        out.append(f"| {r['要素']} | {r['使う']} | {r['読む']} | {r['置き場']} | {r['鍵']} |")
    out += ["", "定義表に在るが、教科書からは読まない要素（プログラムか頼んだ側が持つ物）＝" + "、".join(f"{n}（{w}）" for n, w in skipped0) + "。", ""]
    # 1 見本が示す形
    out += ["### 見本に入っている書き方の実例（どの見本を開けば、その書き方の例が見られるか。プログラムが見本から数えた）", "",
            "書き方に迷ったら、この表で、その書き方の実例が入っている見本を探して開いてください。例＝「条件の書き方 level」は、その指標の使い方の行に、条件の書き方 level（値がある線を超えたら、という書き方）の実例が入っている、という意味です。「役割「勢い」」は、役割の候補に「勢い」と書いた実例が入っている、という意味です。", "",
            "| 指標 | 入っている書き方の実例 |", "|---|---|"]
    seen_tags = set()
    for t in samples:
        tags = _sample_tags(t, table)
        seen_tags |= set(tags)
        out.append(f"| {t['名前']} | {'、'.join(tags)} |")
    # 2 見本に実例が無い物（選べる語ごとに数える）
    def seen_in(kind):
        s = set()
        for t in samples:
            for x in t.get("使い方の記録") or []:
                if kind == "使える条件の形":
                    s |= set(x.get(kind) or [])
                elif kind == "前処理":
                    s |= set(x.get(kind) or [])
                elif kind == "閾値の形":
                    s |= {th.get("形") for th in x.get("閾値") or []}
                elif kind == "合図の形のパラメータの名前":
                    s |= {p.get("名前") for p in x.get("合図の形のパラメータ") or []}
                elif kind == "場面":
                    s.add((x.get("場面と型") or {}).get("場面"))
                elif kind == "玉の向き":
                    s.add(x.get("玉の向き", "欄なし"))
                elif kind in ("向き", "使い方の種類"):
                    s.add(x.get(kind))
            if kind == "役割の区分":
                s |= {c.get("区分") for c in t.get("教科書の役割の候補") or []}
            if kind == "値の読み方の区分":
                s |= {c.get("区分") for c in t.get("値の読み方の候補") or []}
        return s - {None}
    same_as = {"barssince": "within_n（何本前以内＝何本以内・FORM_SPEC の説明）", "何本前か": "何本以内か（barssince は within_n で受ける）"}   # 別の語で受ける物
    checks = [("使える条件の形", [f for f in forms if f not in same_as]), ("閾値の形", cv["閾値の形"]), ("前処理", cv["前処理"]),
              ("合図の形のパラメータの名前", [n for n in sig_names if n not in same_as]),
              ("使い方の種類", [u for u in cv["使い方の種類"] if u != "正解ラベル"]), ("場面", cv["場面"]), ("玉の向き", list(cv["玉の向き"]) + ["欄なし"]),
              ("向き", cv["向き"]), ("役割の区分", list(cv["役割の区分の表"])), ("値の読み方の区分", list(cv["方向から性質への対応の表"]))]
    out += ["", "### 見本に実例が入っていない書き方（選べる語のうち、どの見本にも書いていない物。プログラムが選べる語と見本を照らした・0 なら全部に実例が在る）", "", "| どの項目の選べる語か | 実例の無い語 |", "|---|---|"]
    n_missing = 0
    for kind, allowed in checks:
        miss = [a for a in allowed if a not in seen_in(kind)]
        n_missing += len(miss)
        out.append(f"| {kind} | {'・'.join(miss) if miss else '（全部に実例が在る）'} |")
    out.append(f"| 合計 | {n_missing} |")
    out += ["", "選べる語の中で、見本では別の語の行に書く物（だから実例が無くてもよい）＝" + "、".join(f"「{k}」は「{v}」" for k, v in same_as.items()) + "。「何本前」「何本以内」の文は、どちらも条件の書き方 within_n の行に書き、合図の形のパラメータの名前「何本以内か」に本数を書きます。barssince の行は作りません。「部分の見本」は、調べていない要素の項目を書いていない見本です。項目が無い要素は「まだ調べていない」と読みます。この依頼では、全部の要素を調べます。"]
    # 3 教科書の鍵と定義表の要素
    out += ["", "### 教科書の項目の名前と、定義表の要素の対応（プログラムが定義表と対応の表から作った）", "",
            "教科書のファイル（JSON）の中の項目の名前は、定義表の要素の名前に合わせています。この表は、教科書の項目一つにつき一行で、定義表のどの要素に当たるか（指標の記録の番号 ／ 部品の記録の番号）と、その項目の中に書く欄の名前を示します。", "",
            "| 教科書の項目の名前（JSON の key） | 定義表の要素（指標の記録／部品の記録） | その項目の中に書く欄 |", "|---|---|---|"]
    for key, (a, b) in TEXTBOOK_TOP.items():
        nm = " ／ ".join(f"{no} {E[no]['要素の名前']}" if no else "（無い）" for no in (a, b))
        out.append(f"| `{key}` | {nm} | {'・'.join(f'`{k}`' for k in sorted(TEXTBOOK_SHAPE.get(key, set())))} |")
    row_nm = "・".join(f"{no} {E[no]['要素の名前']}" for no in TEXTBOOK_ROW.values())
    out.append(f"| `使い方の記録` の行 | {row_nm} | {'・'.join(f'`{k}`' for k in sorted(set(TEXTBOOK_ROW) | TEXTBOOK_ROW_EXTRA))} |")
    out += ["", f"候補の行の共通の欄＝{'・'.join(f'`{k}`' for k in sorted(CAND_KEYS))}。"]
    inside = {"②-13": "候補の行の `確かめの強さ`"}                 # 要素としてではなく、候補の行の欄として集める物
    covered = {no for a, b in TEXTBOOK_TOP.values() for no in (a, b) if no} | set(TEXTBOOK_ROW.values()) | set(inside)
    rest = [no for no in E if no not in covered]
    bad = [no for no in rest if no not in NOT_COLLECTED]
    if bad:
        raise SystemExit(f"❌ 定義表の要素で、集めるとも集めないとも決めていない物: {bad}")
    out += ["", f"定義表の要素は {len(E)} 件。集める物 {len(covered)} 件（うち " + "、".join(f"{no} {E[no]['要素の名前']}＝{w}" for no, w in inside.items())
            + f"）。集めない物 {len(rest)} 件＝" + "、".join(f"{no} {E[no]['要素の名前']}（{NOT_COLLECTED[no]}）" for no in rest) + "。"]
    # 4 選べる語
    out += ["", "### 選べる語（プログラムが定義表の選べる値と法則の条件の書き方から作った）", "", "| どの項目の選べる語か | 選べる語 |", "|---|---|"]
    tf = json.loads((PR / "observe_config.json").read_text(encoding="utf-8"))["timeframes"]
    rows = [("教科書の役割の区分", list(cv["役割の区分の表"])), ("閾値の形", cv["閾値の形"]), ("値の単位（値の単位と値域だけ。閾値には「値段」「ドル」を書かない）", cv["値の単位"]),
            ("使い方の種類（正解ラベルは作らない）", [u for u in cv["使い方の種類"] if u != "正解ラベル"]), ("場面", cv["場面"]), ("玉の向き", cv["玉の向き"]), ("向き", cv["向き"]),
            ("時間足・文の時間足", tf), ("前処理", cv["前処理"]), ("軸の意味", cv["軸の意味"]), ("使える条件の形", forms), ("確かめの強さ", cv["確かめの強さ"]),
            ("値の読み方の区分", list(cv["方向から性質への対応の表"])), ("合図の形のパラメータの名前", sig_names), ("売買スタイル（代表の値の候補の鍵）", list(cv["売買スタイル"]) + ["既定"])]
    for k, v in rows:
        out.append(f"| {k} | {'・'.join(v)} |")
    out += ["", "合図の形のパラメータの名前と条件の形の対応＝" + "、".join(f"{f}→{'・'.join(v)}" for f, v in SIGNAL_PARAM_OF_FORM.items())
            + "。ただし barssince の行は作らず、「何本前」の文も within_n の行に「何本以内か」で書きます（名前「何本前か」は選べる語に在りますが、使いません）。"]
    # 5 相手
    ordered = list(FIRST_NINE) + [n for n in targets if n not in FIRST_NINE]
    out += ["", "### 調べる相手（プログラムがオン/オフの表から数えた）", "",
            f"相手は、ta（Python の指標ライブラリ）の指標と、相場の法則が名指しする指標と、「包み足」の和集合で、{len(targets)} 種です。順番は、先に通す9種（{'・'.join(FIRST_NINE)}）を先頭にし、残りは名前の文字の並び（Python の sorted の順）です。先に通す9種は全部 相手に在ります。",
            "", f"**今回の第一回で作る9種（先に通す指標。この順）＝** {'・'.join(FIRST_NINE)}", "",
            f"続きの順（横展開のとき。参考）＝ {'・'.join(ordered[9:])}"]
    # 6 要件との対応
    out += ["", "### 要件との対応（プログラムが要件の文書の行を読んで作った）", "", "| 要件の行 | 中身（実物の行） | 教科書のどこに入るか |", "|---|---|---|"]
    for fname, line, must, where in REQ_MAP:
        ln, text = _req_line(fname, line, must)
        out.append(f"| {fname}:{ln} | {text[:90].replace('|', '／')} | {where} |")
    # 7 後で直す定義表
    out += ["", "### この依頼の後の工事で直す定義表（プログラムが定義表と照らした・取り込みの工事の設計書に入れる）", ""]
    fixes = []
    for k, v in EXTRA_CHOICES.items():
        for name in v:
            if name not in table["選べる値"][k]:
                fixes.append(f"{k}に「{name}」を足す（テストの口は写しにだけ足して通している）")
    missing_sig = [n for n in sig_names if n not in E["③-9"]["中身"]]
    if missing_sig:
        fixes.append(f"③-9 合図の形のパラメータの中身の文に {'・'.join(missing_sig)} を足す（engine_tuner の FORM_SPEC が持つ）")
    for key, (a, b) in TEXTBOOK_TOP.items():
        if a and not b:
            fixes.append(f"部品の記録に {E[a]['要素の名前']} を足す（教科書の `{key}` の置き場が無い）")
    if "組" not in E["③-7"]["中身"] or True:
        fixes.append("③-7 時間足に、足の組を置く形を決める（今は出どころの中に `時間足の組` を置く）")
    out += [f"- {f}" for f in fixes]
    return "\n".join(out) + "\n"


def textbook_shape_errors(t: dict) -> list:
    """教科書の中の欄の名前を、TEXTBOOK_SHAPE と照らす（候補の行・軸の中・使い方の行の中まで）。違う鍵の道を返す。"""
    out = []

    def walk(x, allowed, where):
        if isinstance(x, dict):
            for k, v in x.items():
                if allowed is not None and k not in allowed:
                    out.append(f"{where}/{k}")
                    continue
                nxt = TEXTBOOK_SHAPE.get(k)
                if k == "パラメータの代表の値の候補":              # {軸の名前: {既定・スキャル・デイトレ}}＝軸の名前は何でもよい
                    for ax, v2 in (v or {}).items():
                        walk(v2, TEXTBOOK_SHAPE["代表の値の候補"], f"{where}/{k}/{ax}")
                    continue
                walk(v, nxt, f"{where}/{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, allowed, f"{where}[{i}]")

    for key, val in t.items():
        if key == "使い方の記録":
            walk(val, set(TEXTBOOK_ROW) | TEXTBOOK_ROW_EXTRA, f"{t.get('名前')}/{key}")
        elif key in TEXTBOOK_SHAPE:
            walk(val, TEXTBOOK_SHAPE[key], f"{t.get('名前')}/{key}")
    return out


def textbook_new_form(t: dict) -> dict:
    """古い形の教科書（out_t1_01.json・前の見本）を、命名の決まりの形へ直す。値と文は変えない。"""
    def rn(x):
        if isinstance(x, dict):
            return {TEXTBOOK_OLD.get(k, k): rn(v) for k, v in x.items()}
        return [rn(v) for v in x] if isinstance(x, list) else x

    def row_new(x: dict) -> dict:
        r = {"使い方の種類": x.get("使い方の種類"), "場面と型": {"場面": x.get("場面"), "型": x.get("型")}, "向き": x.get("向き"),
             "時間足": x.get("時間足") or [], "前処理": x.get("前処理") or [], "使える条件の形": x.get("使える条件の形") or []}
        if x.get("玉の向き"):                                    # 文に売買の方向が無い行は欄を書かない（読む口は既定＝両方で読む）
            r["玉の向き"] = x["玉の向き"]
        if x.get("パラメータの代表の値"):
            r["パラメータの代表の値の候補"] = x["パラメータの代表の値"]
        r["合図の形のパラメータ"] = []
        for p in x.get("合図の形のパラメータ") or []:
            one = {"候補の値": p.get("代表の値")}
            if p.get("注記"):
                one["注記"] = p["注記"]
            r["合図の形のパラメータ"].append({"名前": p.get("名前"), "代表の値の候補": {"既定": [one]}})
        th = x.get("閾値") or {}
        cands = {k: th[k] for k in ("スキャル", "デイトレ", "既定") if th.get(k)}
        r["閾値"] = [{"形": th.get("形"), "単位": th.get("単位"), "代表の値の候補": cands}] if cands else []
        r["出どころ"] = x.get("根拠") or {}
        if x.get("注記"):
            r["注記"] = x["注記"]
        return r

    t = rn(t)
    out = {"名前": t["名前"]}
    if t.get("記録の種類"):
        out["置く記録"] = t["記録の種類"]
    if t.get("注記"):
        out["注記"] = t["注記"]
    out["照らしと出どころ"] = {"元の指標": t.get("元の指標"), "教科書の計算の式": t.get("計算の式")}
    out["教科書の役割の候補"] = t.get("教科書の役割") or []
    u = dict(t.get("値の単位と値域") or {})
    lo, hi = u.pop("下限", None), u.pop("上限", None)
    out["値の単位と値域"] = {"単位": u.pop("単位", None), "値域": {"有界": [lo, hi], "分位": None}, **u}
    out["値の読み方の候補"] = [{"区分": None, **(t.get("値の読み方") or {})}]
    out["出力"] = t.get("出力") or []
    out["確定と期間"] = t.get("確定と期間") or {}
    axes = []
    for a in t.get("パラメータの軸") or []:
        one = {k: v for k, v in a.items() if k not in ("既定", "スキャル", "デイトレ", "範囲の文")}
        one["代表の値の候補"] = {k: a.get(k) or [] for k in ("既定", "スキャル", "デイトレ")}
        one["範囲の候補"] = a.get("範囲の文") or []
        one["軸どうしの決まり"] = []
        axes.append(one)
    out["パラメータの軸"] = axes
    out["閾値の範囲の候補"] = t.get("閾値の範囲の文") or []
    if t.get("閾値の注"):
        out["閾値を持たない理由"] = t["閾値の注"]
    out["使い方の記録"] = [row_new(x) for x in t.get("使い方") or []]
    out["探した記録"] = t.get("探した記録") or []
    return out


def textbook_convert(src: str, dst: str) -> int:
    """--textbook-new-form＝古い形の教科書のファイルを、新しい形のファイルへ直す（値は変えない）。"""
    got = jload(Path(src))
    res = textbook_new_form(got) if isinstance(got, dict) else [textbook_new_form(x) for x in got]
    Path(dst).write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"直した＝{src} → {dst}（{1 if isinstance(got, dict) else len(got)} 種）")
    return 0


def textbook_merge(paths: list) -> list:
    """教科書のファイルを読み、同じ指標は要素の単位で後のファイルの値に差し替える（一種・一要素だけの調べ直しを入れる口）。"""
    merged, replaced = {}, []
    for one in paths:
        got = jload(Path(one))
        for t in (got if isinstance(got, list) else [got]):
            if t["名前"] in merged:
                replaced.extend(f"{t['名前']} の {k}" for k in t if k != "名前")
            merged.setdefault(t["名前"], {}).update(t)
    for r in replaced:
        print("差し替えた：", r)
    return list(merged.values())


def try_textbook_many(paths: list, box_out: str = None) -> int:
    """教科書の並びを、定義表と照らして箱の形へ直し、読む口へ通す（本物の indicators.json は書かない・ToDo の271番）。
    足りない要素は止めず、「まだ調べていない要素」として出す。定義表に無い鍵と古い名前は止める。値の正しさと engine_tuner は見ない。
    box_out＝取り込みの写し（全部の教科書を箱に入れた指標データ）を書く先。本物の置き場は拒む。"""
    import importlib.util
    spec_of = form_spec()

    def old_names(x, where=""):
        """古い形の鍵が残っていないか（命名の決まり）。"""
        out = []
        if isinstance(x, dict):
            for k, v in x.items():
                if k in TEXTBOOK_OLD or k in ("根拠", "閾値の範囲の文", "範囲の文", "使い方", "計算の式", "閾値の注", "記録の種類"):
                    out.append(f"{where}/{k}")
                out += old_names(v, f"{where}/{k}")
        elif isinstance(x, list):
            for v in x:
                out += old_names(v, where)
        return out

    def usable_row(u) -> bool:
        """FORM_SPEC の決まりで、条件を組むのに要る欄がそろうか。入れ子の形（streak ほか）は中の条件で見る。"""
        rep = any(th.get("代表の値") for th in u["閾値"])
        pair = any(p.get("名前") == "組の相手" for p in u["合図の形のパラメータ"])
        for f in u["使える条件の形"]:
            s = spec_of.get(f) or {}
            if s.get("nest") or s.get("pair") == "inner2":
                continue
            if s.get("needs_side") and not u["向き"]:
                continue
            if s.get("band"):
                ends = [c for th in u["閾値"] for k in ("スキャル", "デイトレ", "既定") for c in (th["出どころ"].get(k) or []) if "候補の値" in c]
                if len({c["候補の値"] for c in ends}) >= 2:      # 帯は両端が要る
                    return True
                continue
            p = s.get("pair")
            if p == "none" or (p == "1" and (rep or f.startswith("slope"))) or (p == "2" and pair) or (p == "2or1th" and (pair or rep)):
                return True
        return False

    spec = importlib.util.spec_from_file_location("indicators_reader", PR / "indicators" / "indicators.py")
    ind = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ind)
    base = ind.load().data
    E = {e["番号"]: e["要素の名前"] for e in base["要素の定義表"]["要素"]}
    src = lambda c: {k: v for k, v in (c or {}).items() if k not in ("候補の値", "区分", "挙げた値")}
    pick = lambda rows: next((c["候補の値"] for c in rows if "候補の値" in c), None)
    kind_of = lambda t: t.get("置く記録") or "指標の記録"
    gaps, ng = [], 0

    def el(t, key):                                            # 教科書の鍵 → いまの定義表の要素の名前（無ければ None）
        no = TEXTBOOK_TOP[key][0 if kind_of(t) == "指標の記録" else 1]
        return E[no] if no else None

    def count_cands(x) -> int:                                 # 候補の値か挙げた値を持つ行の数（箱へ移して減っていないかを見る）
        if isinstance(x, dict):
            return (1 if "候補の値" in x or "挙げた値" in x else 0) + sum(count_cands(v) for v in x.values())
        return sum(count_cands(v) for v in x) if isinstance(x, list) else 0

    # ── 要素ごとの箱への移し方（教科書の鍵 → 関数）。表に無い鍵は、教科書の値をそのまま置く ────────────────────
    # ★要素を足すとき＝定義表に1行・TEXTBOOK_TOP に1行。箱へ移す所は直さない（形を変えて置くときだけ、ここに関数を1つ足す）。
    def cands(rep):                                            # 代表の値の候補 → 値の在る行（既定・スキャル・デイトレ）
        return tuple([c for c in (rep or {}).get(k) or [] if "候補の値" in c] for k in ("既定", "スキャル", "デイトレ"))

    def box_axes(v, old):
        axes = []
        for a in v:
            df, sc, dt = cands(a.get("代表の値の候補"))
            vals = [c["候補の値"] for c in df + sc + dt] + [x for c in a.get("範囲の候補") or [] for x in c.get("挙げた値", [])]
            chosen = {"スキャル": pick(sc or df), "デイトレ": pick(dt or df)}   # 要件＝教科書に無ければ既定の値（core_requirements_full.md:53）
            axes.append({"名前": a["名前"], "意味": a.get("意味"), "種類": a.get("種類"),
                         "範囲": {"kind": "int" if a.get("種類") == "整数" else "float", "lo": min(vals, default=None), "hi": max(vals, default=None)},
                         "代表の値": {k: [x] for k, x in chosen.items() if x is not None}, "確かめの強さ": "ページの文で確かめた",
                         "軸どうしの決まり": a.get("軸どうしの決まり") or [], "出どころ": {"代表の値の候補": a.get("代表の値の候補"), "範囲の候補": a.get("範囲の候補")}})
        return axes

    def box_role(v, old):
        return {"区分": list(dict.fromkeys(c["区分"] for c in v if c.get("区分"))), "出どころ": [src(c) for c in v], "札": (old or {}).get("札")}

    def box_unit(v, old):
        return {"単位": v.get("単位"), "値域": v.get("値域"), "出どころ": {k: x for k, x in v.items() if k not in ("単位", "値域")}}

    def box_read(v, old):
        first = v[0] if v else {}
        return {"区分": next((c["区分"] for c in v if c.get("区分")), None), "読み方": first.get("読み方"), "向きを持つ": first.get("向きを持つ"),
                "性質": None, "出どころ": [src(c) for c in v]}

    def box_fin(v, old):
        f = v.get("未来を使う作りか") or {}
        return {"確定に要る本数": v.get("確定に要る本数"), "未来を使わない作りか": (None if f.get("候補の値") is None else not f["候補の値"]),
                "出どころ": {**src(v), "未来を使う作りか": f}}

    def box_refs(v, old):
        return {**(old or {}), "元の指標": v.get("元の指標"), "教科書の計算の式": v.get("教科書の計算の式")}

    def box_thr_range(v, old):
        ranges = {}
        for c in v:
            ranges.setdefault((c.get("形"), c.get("単位")), []).append(c)
        return [{"形": k[0], "単位": k[1], "範囲": {"kind": "float", "lo": min((x for c in cs for x in c.get("挙げた値", [])), default=None),
                                                 "hi": max((x for c in cs for x in c.get("挙げた値", [])), default=None)},
                 "確かめの強さ": "ページの文で確かめた", "出どころ": cs} for k, cs in ranges.items()]

    BOX = {"パラメータの軸": box_axes, "教科書の役割の候補": box_role, "値の単位と値域": box_unit, "値の読み方の候補": box_read,
           "確定と期間": box_fin, "照らしと出どころ": box_refs, "閾値の範囲の候補": box_thr_range}

    META = {"逐語", "URL", "確かめの強さ", "注記", "読んだ日", "HTTP", "当たる文", "範囲の形", "文の時間足"}

    def has_value(v) -> bool:                                  # 教科書の値が在るか（出どころの欄だけの物・空・null は無い）
        if isinstance(v, dict):
            return any(has_value(x) for k, x in v.items() if k not in META)
        return any(has_value(x) for x in v) if isinstance(v, list) else v is not None

    def box(t, top=None, Em=None) -> tuple:
        """教科書1種 → 箱の形（指標の記録の要素と、使い方の記録の行）。top＝教科書の鍵→定義表の番号・Em＝番号→要素の名前（試しで差し替える）。"""
        top, Em = top or TEXTBOOK_TOP, Em or E
        old = base[kind_of(t)][t["名前"]]
        recs = {}
        for key in top:
            if key not in t:
                continue
            no = top[key][0 if kind_of(t) == "指標の記録" else 1]
            name = Em[no] if no else None
            if name is None:                                   # その記録に要素が無い（部品の記録の確定と期間ほか）
                if has_value(t[key]):
                    print("❌ 箱に欄が無く、教科書の値が在る要素：", t["名前"], key)
                    gaps.append((t["名前"], key))
                else:
                    print("箱に欄が無い要素（教科書の値も無い）：", t["名前"], key)
                continue
            recs[name] = BOX.get(key, lambda v, o: v)(t[key], old.get(name))
        uses = []
        for x in t.get("使い方の記録") or []:
            ptr = {kind_of(t): t["名前"]}
            if x.get("使う出力"):
                ptr["使う出力"] = x["使う出力"]
            on = {"状態": "オン", "出どころ": x.get("出どころ")}
            if x.get("時間足の組"):                              # ③-7 の組は、いまの指標データの時間足の形に置けないので出どころの中に置く（改名の工事で直す）
                on["時間足の組"] = x["時間足の組"]
            row = {E["③-1"]: ptr, E["③-2"]: x["使い方の種類"], E["③-4"]: x.get("向き"), E["③-7"]: x.get("時間足") or [], E["③-8"]: x.get("前処理") or [],
                   E["③-13"]: x.get("使える条件の形") or [], E["③-11"]: on, E["③-5"]: [], E["③-9"]: []}
            if x.get("玉の向き"):
                row[E["③-12"]] = x["玉の向き"]
            st = x.get("場面と型") or {}
            if st.get("場面") or st.get("型"):
                row[E["③-3"]] = {"場面": st.get("場面"), "型": st.get("型")}
            for p in x.get("合図の形のパラメータ") or []:
                c = p.get("代表の値の候補") or {}
                row[E["③-9"]].append({"名前": p.get("名前"), "代表の値": pick((c.get("スキャル") or []) + (c.get("既定") or [])), "出どころ": c})
            if x.get("パラメータの代表の値の候補"):
                row[E["③-6"]] = {k: {st_: [pick((v.get(st_) or []) or (v.get("既定") or []))] for st_ in ("スキャル", "デイトレ") if pick((v.get(st_) or []) or (v.get("既定") or [])) is not None}
                                 for k, v in x["パラメータの代表の値の候補"].items()}
            for th in x.get("閾値") or []:
                c = th.get("代表の値の候補") or {}
                rep = {st_: pick((c.get(st_) or []) or (c.get("既定") or [])) for st_ in ("スキャル", "デイトレ")}
                row[E["③-5"]].append({"形": th.get("形"), "単位": th.get("単位"), "代表の値": {k: v for k, v in rep.items() if v is not None}, "出どころ": c})
            uses.append(row)
        return recs, uses

    def filled(items) -> dict:
        d = copy.deepcopy(base)
        # 役割の区分「ローソクの形」＝まこさん 2026-11-05「追加していい」。本物の定義表へ足すのは取り込みの工事（設計書と監査）。写しにだけ足す
        d["要素の定義表"]["選べる値"]["役割の区分の表"].setdefault("ローソクの形", {"札": "ローソク", "出どころ": "まこさん 2026-11-05「追加していい」（写しだけ・本物は取り込みの工事で）"})
        for kind, nm, recs, uses in items:
            d[kind][nm].update(recs)
            d["使い方の記録"] = d["使い方の記録"] + uses
        return d

    data = textbook_merge(paths)
    known_top = set(TEXTBOOK_TOP) | TEXTBOOK_TOP_EXTRA
    known_row = set(TEXTBOOK_ROW) | TEXTBOOK_ROW_EXTRA
    wrong = set()                                              # 名前が違う教科書は、箱へ移さずに止める
    suspect_header_shown = [False]                             # 書き写し忘れの疑いの説明は、最初の一行の前に一度だけ出す
    for t in data:                                            # 定義表（TEXTBOOK_*）と照らす。無い鍵は止めず、余る鍵と古い名前は止める
        extra = (set(t) - known_top) | {k for x in t.get("使い方の記録") or [] for k in x if k not in known_row}
        olds = old_names(t, t["名前"]) + textbook_shape_errors(t)   # 一番上・行・候補の行・軸の中の鍵まで照らす
        if extra or olds:
            print("❌ 定義表と名前が違う：", t["名前"], "余る", sorted(extra), "古い名前か中の欄", olds[:5])
            ng += 1
            wrong.add(t["名前"])
            continue
        short =sorted(set(TEXTBOOK_TOP) - set(t) - {k for k in TEXTBOOK_TOP if TEXTBOOK_TOP[k][0 if kind_of(t) == "指標の記録" else 1] is None})
        if short:
            print("まだ調べていない要素：", t["名前"], short)
        for i, x in enumerate(t.get("使い方の記録") or []):      # 依頼書の決まり＝玉の向きは null にしない（文に無ければ欄を書かない）
            if "玉の向き" in x and x["玉の向き"] is None:
                print(f"❌ 玉の向きが null（文に無ければ欄を書かない決まり）：{t['名前']} の使い方 {i}")
                ng += 1
            # ★書き写し忘れの疑いを出す検査（2026-11-05・まこさんの指摘で説明の形に直した）
            # 前提＝教科書の使い方の一行には、三つの物が入っている。
            #   逐語＝調べたページから写した英文そのもの。
            #   閾値の欄＝その英文が言っている「この値を超えたら」の値を、プログラムが読める形で書く欄。
            #   合図の形のパラメータの欄＝「何本続いたら」「どれだけ上がったら」の本数や幅を書く欄。
            # 抜けの例＝ADX の見本の一行。逐語には「ADX が安値から四つ上がるまで待て」と書いてあったのに、
            #   二つの欄が両方 空だった。クラウドが英文は写したのに、その中の値を欄に書き写していなかった。
            #   engine_tuner は英文を読まないので、書き写さない値は使われない。
            # 検査がすること＝英文の中に数字が在る行を探す。その行の二つの欄が両方 空なら、
            #   「書き写し忘れの疑い」として画面に出す。
            # なぜ止めないか＝英文の中の数字が、全部 値とは限らない。包み足の見本には本の頁の番号が、
            #   DI差の見本には「次の足」の足の番号が入っていた。これは欄に写す物ではない。
            #   プログラムは、値か頁の番号かを見分けられない。だから止めずに出し、出た行を人が読んで決める。
            import re
            nums = re.findall(r"\d+(?:\.\d+)?", (x.get("出どころ") or {}).get("逐語") or "")
            has_th = any("候補の値" in c for th in x.get("閾値") or [] for k in ("スキャル", "デイトレ", "既定") for c in (th.get("代表の値の候補") or {}).get(k) or [])
            has_sig = any("候補の値" in c for p in x.get("合図の形のパラメータ") or [] for k in ("スキャル", "デイトレ", "既定") for c in (p.get("代表の値の候補") or {}).get(k) or [])
            if nums and not has_th and not has_sig:
                if not suspect_header_shown[0]:
                    print("▼ 書き写し忘れの疑いの行（止めない）。意味＝写した英文の中に数字が在るのに、閾値の欄も合図の形のパラメータの欄も空の行。"
                          "英文の数字が値なら、クラウドが欄に書き写し忘れた抜け。頁の番号や足の番号なら抜けではない。"
                          "プログラムには見分けられないので、下の行を人が読んで決める。")
                    suspect_header_shown[0] = True
                print(f"  書き写し忘れの疑い：{t['名前']} の使い方 {i}（{x.get('使い方の種類')}・英文の中の数字＝{nums[:4]}）")
    table, done = [], []
    with tempfile.TemporaryDirectory() as tmp:
        def read(d):
            p = Path(tmp) / f"t{len(list(Path(tmp).iterdir()))}.json"   # 読む口は同じパスを1回しか読まない（indicators.py:416）
            p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
            return ind.load(p)
        for t in data:
            nm, kind = t["名前"], kind_of(t)
            if nm in wrong:
                continue
            try:
                recs, uses = box(t)
                r = read(filled([(kind, nm, recs, uses)]))
            except ind.IndicatorsError as e:
                print("止まった文：", nm, str(e)[:150])
                ng += 1
                continue
            bad = [k for k, v in recs.items() if r.element(nm, k) != v]
            got = r.usages(nm)
            off = (base[kind][nm].get(E["②-10"]) or base[kind][nm].get(E["④-8"]) or {}).get("状態") == "オフ"
            same = len(uses) if off else sum(1 for u in uses if u in got)   # オフの指標の使い方は読む口が返さない（決まり⑤）
            if off:
                print("オフの指標（使い方が返らないのは決まりのとおり）：", nm)
            before = count_cands([t.get("パラメータの軸") or [], t.get("閾値の範囲の候補") or [], [x.get("閾値") for x in t.get("使い方の記録") or []]])
            after = count_cands([recs.get(el(t, "パラメータの軸")) or [], recs.get(el(t, "閾値の範囲の候補")) or [], [u[E["③-5"]] for u in uses]])
            lost = before - after
            ng += len(bad) + (len(uses) - same) + (1 if lost else 0)
            usable = [dict(u, 閾値=u[E["③-5"]], 合図の形のパラメータ=u[E["③-9"]], 使える条件の形=u[E["③-13"]], 向き=u[E["③-4"]]) for u in uses]
            usable = [u for u in usable if usable_row(u)]
            rng = [u for u in usable if (u.get(E["③-3"]) or {}).get("場面") == "レンジ" and u.get(E["③-12"], "両方") in ("SHORT", "両方")]
            done.append((kind, nm, recs, uses))
            table.append((nm, "通る", len(bad), f"{same}/{len(uses)}", lost, len(usable), len(rng)))
        print("名前\t読む口\t要素の違い\t使い方が返る\t減った候補\t条件にできる行\tうちレンジ×SHORTか両方")
        for row in table:
            print("\t".join(str(c) for c in row))
        if not done:
            print("合計の違い＝", ng, "（通った教科書が無い）")
            return 1
        r_all = read(filled(done))                             # 全部を同時に入れても止まらないか
        print(f"全部を同時に入れた読む口＝通った（{len(done)} 種・使い方 {sum(len(x[3]) for x in done)} 行）")
        broken = copy.deepcopy(next((x for x in done if x[3]), None))
        if broken:
            broken[3][0][E["③-4"]] = "書いてない"
            try:
                read(filled([broken]))
                print("❌ わざと壊した行（向き「書いてない」）を読む口が止めなかった")
                ng += 1
            except ind.IndicatorsError as e:
                print("✅ わざと壊した行で読む口が止まった：", str(e)[:100])
        # 増減のしやすさ＝定義表に要素を足しても、前に作った教科書は読み直さずに通る（足した要素は「まだ決めていない」で返る）
        more = filled(done)
        more["要素の定義表"]["要素"].append(dict(next(e for e in more["要素の定義表"]["要素"] if e["番号"] == "②-8"),
                                               **{"番号": "②-99", "要素の名前": "試しに足した要素", "無いときの扱い": "未設定"}))
        r_more = read(more)
        same_more = all(r_more.element(nm, "試しに足した要素") == ind.UNDECIDED for kind, nm, _r, _u in done if kind == "指標の記録")
        ng += 0 if same_more else 1
        print(("✅" if same_more else "❌"), "定義表に要素を足しても、教科書を作り直さずに読める")
        # 増減のしやすさ②＝教科書に要素を足す（定義表に1行・対応の表に1行）。箱へ移す所を直さずに、その要素が箱へ入る
        first = next(x for x in done if x[0] == "指標の記録")
        top2 = dict(TEXTBOOK_TOP, **{"試しに足した要素": ("②-99", None)})
        E2 = {e["番号"]: e["要素の名前"] for e in more["要素の定義表"]["要素"]}
        recs2, _ = box({"名前": first[1], "試しに足した要素": {"候補の値": 1, "逐語": "試し"}}, top2, E2)
        more2 = copy.deepcopy(more)
        more2["指標の記録"][first[1]].update(recs2)
        ok_add = ind.Indicators(more2).element(first[1], "試しに足した要素") == {"候補の値": 1, "逐語": "試し"}
        ng += 0 if ok_add else 1
        print(("✅" if ok_add else "❌"), "教科書に要素を足すと、箱へ移す所を直さずに入る（定義表と対応の表の各1行だけ）")
        # 増減のしやすさ③＝要素を消す（対応の表から1行消す）＝その鍵は「余る」で止まる
        first_tb = next(t for t in data if t["名前"] == first[1])
        top3 = {k: v for k, v in TEXTBOOK_TOP.items() if k != "出力"}
        ok_del = "出力" in first_tb and "出力" in {k for k in first_tb if k not in (set(top3) | TEXTBOOK_TOP_EXTRA)}
        ng += 0 if ok_del else 1
        print(("✅" if ok_del else "❌"), "対応の表から要素を消すと、その鍵の教科書は止まる")
        # 増減のしやすさ④＝定義表の要素の名前を変える＝番号で引くので、教科書も箱へ移す所も直さない
        ren = copy.deepcopy(filled(done))
        for e in ren["要素の定義表"]["要素"]:
            if e["番号"] == "②-3":
                e["要素の名前"] = "出力の一覧（試し）"
        for rec in ren["指標の記録"].values():
            if "出力" in rec:
                rec["出力の一覧（試し）"] = rec.pop("出力")
        E3 = {e["番号"]: e["要素の名前"] for e in ren["要素の定義表"]["要素"]}
        recs3, _ = box(first_tb, None, E3)
        ok_ren = "出力の一覧（試し）" in recs3 and "出力" not in recs3 and ind.Indicators(ren).element(first[1], "出力の一覧（試し）") is not None
        ng += 0 if ok_ren else 1
        print(("✅" if ok_ren else "❌"), "定義表の要素の名前を変えても、教科書と箱へ移す所を直さずに入る")
        if box_out:                                            # 取り込みの写し＝全部の教科書を箱に入れた指標データを、本物とは別の場所に書く
            outp = Path(box_out)
            if outp.resolve() == OUT.resolve():
                raise SystemExit("❌ 本物の indicators.json には書かない（取り込みは設計書と監査の後の工事）")
            outp.write_text(json.dumps(filled(done), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
            n_el = sum(len(x[2]) for x in done)
            print(f"取り込みの写しを書いた＝{outp}（{len(done)} 種・要素 {n_el}・使い方 {sum(len(x[3]) for x in done)} 行）")
        sl = importlib.util.spec_from_file_location("laws_reader", PR / "laws" / "laws.py")
        lw = importlib.util.module_from_spec(sl)
        sl.loader.exec_module(lw)
        la = lw.Laws(jload(PR / "laws" / "laws.json"), reader=r_all)
        print("--- laws.py で見つかる指標（SHORT・場面レンジ。見るのは今回の指標だけ）")
        names = {x[1] for x in done}
        for use in ("場面の判定", "入る合図", "入ってはいけない場面を除く条件"):
            for role in ("向き", "強さ", "勢い", "行き過ぎ", "値動きの幅", "出来高", "位置"):
                hit = la._usages_of({"指す物": {"使い方の種類": use, "教科書の役割": role, "場面": "レンジ"}}, {"SHORT"}, [])
                got_n = sorted({(h.get("指す物") or {}).get("指標の記録") or (h.get("指す物") or {}).get("部品の記録") for h in hit} & names)
                print(f"  {use}・{role}：", got_n if got_n else "なし")
    ng += len(gaps)
    print("合計の違い＝", ng, "（止まる・要素の違い・返らない行・減った候補・箱に欄が無い要素・定義表と違う名前の合計）")
    return 0 if not ng else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rewrite", action="store_true")
    ap.add_argument("--try-textbook-many", metavar="教科書の並びのパス", nargs="+")
    ap.add_argument("--textbook-new-form", metavar=("古い形のパス", "新しい形のパス"), nargs=2)
    ap.add_argument("--box-out", metavar="取り込みの写しを書く先", help="--try-textbook-many と一緒に＝全部を箱に入れた指標データの写しを書く（本物には書かない）")
    ap.add_argument("--write-request", action="store_true", help="依頼書の表の部分を、定義表・FORM_SPEC・見本・要件の文書から作り直す")
    ap.add_argument("--verify-request", action="store_true", help="依頼書の表の部分が、作り直した物と同じかを見る")
    a = ap.parse_args()
    if a.write_request:
        return write_request()
    if a.verify_request:
        return write_request(verify=True)
    if a.textbook_new_form:
        return textbook_convert(*a.textbook_new_form)
    if a.try_textbook_many:
        return try_textbook_many(a.try_textbook_many, a.box_out)
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




# ── 依頼書の全文（プログラムが作る。手で書き換えない＝--verify-request が検出する）──────────────────────
REQUEST_DATE = "2026-11-05"
REQUEST_TEXT = """# 依頼書｜先に通す9種の指標の教科書を、見本と同じ書き方で作る（第一回）

この依頼書は、プログラム `gen_indicators_draft.py`（`--write-request`）が作ります。手で書き換えません（`--verify-request` が検出します）。文はプログラムの中に持ち、表は指標データの定義表・見本・要件の文書（`.claude/rules/core_requirements_full.md`・`SDK/.claude/rules/cat_requirements.md`・`SDK/.claude/rules/要件定義書_レベル4_指標の構造.md`）・指標のオン/オフの表（`SDK/.claude/ratchet/indicator_switch.json`）から作ります。

パスは全部、リポジトリ（cat-bitget）の一番上からの相対パスです。`SDK` は `v3-bitget-api-sdk/bitget-python-sdk-api` の略です。

<!-- TEXTBOOK_REQ_AUTO_START hash=<<HASH>> -->

## 一 件名・依頼者・依頼先・依頼日

| 項目 | 中身 |
|---|---|
| 件名 | 先に通す9種の指標の教科書を、見本と同じ書き方で作る（第一回） |
| 依頼者 | まこさん（CAT プロジェクト）。この依頼書は、まこさんの指示で、このリポジトリの Claude Code（CC）がプログラムで作った |
| 依頼先 | クラウドで走る Claude Code のセッション（このリポジトリを取って作業する） |
| 依頼日 | <<DATE>> |

## 二 目的と背景

### この依頼書で使う語

| 語 | 意味 |
|---|---|
| CAT プロジェクト | BTC の売買 BOT を作るプロジェクト。目標は、本番で全部の月の net（手数料を引いた利益）が決めた額以上になること |
| engine_tuner | net を最大にする条件の組み合わせ（指標・閾値・パラメータ・時間足）を探すプログラム |
| 法則 | 相場から見つけた知識を文で書いた物（例＝「レンジでは帯の上端で売る」）。engine_tuner は、法則に沿って条件を組む |
| 指標データ | `SDK/scripts/priority_rebuild/indicators/indicators.json`。全部の指標の情報を置く、ただ一つのファイル。中は「指標の記録」（②）・「使い方の記録」（③）・「部品の記録」（④）に分かれる |
| 定義表 | 指標データの中の `要素の定義表`。指標データの要素（項目）の名前・意味・選べる値を決めた表。この依頼の要素の一覧は、ここから作っている |
| 教科書 | この依頼で作る物。その指標についてページに書いてある文（逐語）と、その文から読み取った値を、プログラムが読める形（JSON）で並べたファイル |
| 読む口 | `SDK/scripts/priority_rebuild/indicators/indicators.py`。指標データを読むプログラム。テスト `--try-textbook-many` は、この読む口で教科書を読めるかを試す |
| ta | Python の指標ライブラリ（`ta`）。指標データの指標の多くは、このライブラリのクラスに当たる |
| 正解ラベル | そのバーが実際にレンジだったかを、未来の値動きから後で付けた答え。判定の成績を測るときだけ使う。この依頼では作らない |
| 資料の表 | 前に Web で調べて作った三つの表＝`.claude/state/indicator_params_review.json`・`indicator_params_by_strategy.json`・`indicator_roles_thresholds.json` |
| 前の依頼 | 全指標306種を調べた依頼（依頼書 `.claude/instructions/cloud_textbook_all_20261103.md`）。結果は「五」の材料の表に在る |
| ToDo の274番 | 頼んだ側の やることリストの番号。この教科書を指標データに取り込む工事。あなたは読まなくてよい |
| G2・H2・材料の検査 | 頼んだ側が engine_tuner を走らせる前に通す検査の名前。この環境では走らせない |
| 先に通す9種 | 頼んだ側が、engine_tuner の全工程を最初に通すと決めた9種の指標（ADX・ATR%・BB%b・BB幅・DI差・RSI・基準線・包み足・帯pivot）。だから相手の並びの先頭に置く |
| 探し方の段階（最初の段階・最後の段階） | engine_tuner の探し方。最初の段階は、パラメータと閾値を代表の固定値にして、指標と役割の組み合わせを絞る。最後の段階は、残った組み合わせのパラメータと閾値を範囲から探す。だから教科書には、代表の値と範囲の両方が要る |
| 入口の型 | 玉を建てるときの売り方の種類（例＝down・flat_up）。文に在る語をそのまま写す |
| 軸どうしの決まり | 一つの指標の二つのパラメータの間の決まり（例＝短い期間は長い期間より小さい） |
| テスト | `--try-textbook-many`（「五」のプログラム）。教科書を読む口で読めるかを試す |
| 要件 H6 | `SDK/.claude/rules/cat_requirements.md` の決まり＝USD の絶対値の閾値を禁じる |
| FORM_SPEC | engine_tuner の中の表。条件の書き方（level・band・cross など）ごとの決まり（材料が何本要るか、など） |
| 指標の名前 | 指標データに在る名前をそのまま使う（例＝AROOND・BB%b・帯pivot）。綴りを直さない |

### 何に使うか

engine_tuner は、net を最大にする条件の組み合わせを探すプログラムです。指標・閾値・パラメータ・時間足を、法則に沿って組みます。そのための指標の情報は、指標データに集めます。

この依頼で作る教科書は、指標データへ入れる材料です。出来上がった教科書は、後の工事（ToDo の274番）でプログラムが指標データに取り込み、engine_tuner が代表の値と範囲を探しに使います。

**この作業は、値を決めません。データもプログラムも直しません。** 候補を全部並べます。一つを選ぶのは、後の工事の設計書と監査です。

### なぜ今 要るか

いま指標データには、閾値の範囲と、入る合図などの使い方が、ほとんど入っていません。前の依頼で全指標306種を調べましたが、書き方が指標データと違うので、そのままでは入りません（値が文字で書いてある・「書いてない」という語が値の欄に在る）。そこで RSI 一種の見本を作り、読む口で読めることをテストで確かめました。この依頼は、その見本と同じ書き方で、残りの指標を作ります。今回の相手が137種なのは、306種のうち指標データに在る物（ta の指標・法則が名指しする指標・包み足）に絞ったからです。

教科書は、誤りが見つかったときに、その指標のその要素だけを調べ直して差し替えられる作りにします（「八」の調べ直しのファイル）。

## 三 依頼の内容

### 作る物

指標一種につき、教科書を一件（JSON）作ります。書き方は見本と同じです。見本は「五 提供する資料」に在ります。**作業の始め（「四」の進め方の二番）で、見本を全部読みます。**

今回は、下の「対象の範囲」の9種（先に通す指標）だけを作ります。9種を一本のファイル `out_t1_01.json` に入れてプッシュし、報告して作業を終えます。残りの指標には進みません。頼んだ人が9種を確かめてから、続き（横展開）を頼みます。

### 対象の範囲

相手の全部と、今回の9種は、次の表のとおりです。

<<相手>>

相手の全部を出す命令は次のとおりです（並べ替えは `unique` の順なので、上の順とは違います。上の順が正です）。

```
jq -r '[.sources.ta[], .sources.law[], "包み足"] | unique | .[]' SDK/.claude/ratchet/indicator_switch.json
```

- 帯の8種（帯VA・帯VA1時間ATR・帯pivot・帯pivot1時間ATR・帯pivot前週・帯pivot前週1時間ATR・帯スイング・帯スイング1時間ATR）は、部品の記録に在ります。元になる pivot・Value Area・スイングについて、教科書の文を探し、ほかの指標と同じ要素（役割の候補・値の読み方の候補・閾値の範囲の候補・使い方の記録）に書きます。帯の幅の数（プロジェクトが決めた定数）は、教科書の文に無ければ、パラメータの軸の代表の値の候補を空にして注記に「見つからなかった」と書きます。部品の記録に置く指標には、`確定と期間` を書きません（置き場が無い。後の工事で足す）。
- パラメータの軸の名前は、指標データの名前を使います。次の命令で見られます。

```
jq '.["指標の記録"]["RSI"]["パラメータの軸"]' SDK/scripts/priority_rebuild/indicators/indicators.json
jq '.["部品の記録"]["帯pivot"]["パラメータの軸"]' SDK/scripts/priority_rebuild/indicators/indicators.json
```

### 作る要素

<<要素一覧>>

要素ごとの書き方（項目の中に書く欄・選べる語・見本のどこに実例が在るか）は、「五 提供する資料」の表に在ります。

### やらないこと

- 値を決めません。おすすめを書きません。候補を全部並べます。
- 上の一覧で「集めない」の要素は書きません。
- 正解ラベルの行は作りません（使い方の種類の選べる語に無い物は書きません）。
- 取引の道具の関数の説明（ProRealCode の BarsSince など）だけの文は、使い方の行にしません。
- 見本に無い書き方が出たら、推測で書かず、「四」の「進め方」のとおりに止まります。

## 四 条件と制約

### 進め方（質問してから量産する）

頼んだ人は、このセッションで質問に答えられます。次の順で進めます。

1. **最初に、プッシュできるかを確かめます。** `git ls-remote origin research/textbook-format-2` で、結果を置くブランチが在るかを見ます。在れば、そのブランチの続きから始め、そのブランチの `out_t1_01.json` に既に在る指標を飛ばします（調べ直しを頼まれた指標と要素は、飛ばさずに調べ直しのファイルへ書きます）。無ければ、ブランチ `refactor/e35-e36-split-strat-base` の最新の版から `research/textbook-format-2` を作り、ファイルを足さずにそのブランチをプッシュします。**プッシュが失敗したら、調べを始めません。** 失敗のエラーの文を報告して、作業を終えます。
2. **先に質問します。** 依頼書・見本・材料を読み、9種の先頭の数種について、材料から見本の書き方へ写すことを試します。書き方で迷う点を一覧にして、**結果のファイルを作らずに止まります。** 迷う点が無ければ、無いと書いて止まります。質問してよいのは、書き方の読み方だけです。どの値を選ぶかは聞きません。
3. **答えを受けて量産します。** 答えをもらってから、9種を作り、報告して止まります。
4. **途中で迷ったら止まります。** 見本に無い書き方が出たら、推測で書かず、その場で止まって聞きます。

始めた時刻と終えた時刻を `date -u` で測ります。会話の記録が要約に置き換わったときは、この依頼書の「三」「四」「七」を読み直します。

### 一種ごとの手順

1. 材料（「五」の表）を読み、在る値を見本の書き方へ写します。文字で書いてある値は、逐語を読んで数に直します。
2. 全部の要素を照らし、空の要素を挙げます。
3. **空の要素は、Web で探します。必須です。** 時間を理由に省きません。開発者の原典、定番の教育サイト、ライブラリの説明書、短い足やスキャルの資料の順に探します。暗号資産の資料が在れば、それも探します。
4. ページは curl と Chromium の両方で開き、本文に逐語が在ることを照らします。開けないページと、404 と書かれたページは、web.archive.org も見ます。それでも開けないページは、確かめの強さを「未確認」にし、注記に HTTP の番号を書きます。
5. 探しても無い要素は、空にして注記に「見つからなかった」と書きます。使った検索の語と開いたページを、`探した記録` に残します。hook に止められた・会話が切れた、などで探し終えずに作業を終える要素は、`探した記録` に「探していない」と書きます（「見つからなかった」とは別です）。
6. 9種が終わったら、「七 受入の条件」の確かめを自分で走らせ、通ってからコミットします。

**とくに必ず探す要素：** パラメータの代表の値（スキャルとデイトレ）、パラメータの範囲の候補、閾値の代表の値（スキャルとデイトレ）、閾値の範囲の候補、使い方の行（使い方の種類・場面・玉の向き・向き）です。代表の値と範囲は、パラメータと閾値の両方について、スキャル・デイトレの文を探します（要件＝最初の段階は戦略ごとの代表の固定値、最後の段階は範囲）。使い方の種類は、7種の全部について探します。場面は、レンジ・上げ・下げ・スパイクの全部について探します。入る合図の文が在る指標は、その合図の弱点を見る「入ってはいけない場面を除く条件」の文も探します（`SDK/.claude/memory/indicator_combination_kb.md` の §3＝合図の弱点を見る条件の節）。期間違いの2本の組（クロスほか）の文は、`合図の形のパラメータ` に、組の相手の名前と両方の期間を書きます（同 §10.2＝期間違いの2本の組の節）。時間足は、文に書いてある足だけを書きます。足を探すための検索はしません（足は役目で決まる・同 §4 の4）。

### 探し方の決まり

Web で調べる依頼は、使える手段を全部使って調べ切ります。「探していない」を「無い」と書きません（まこさん指示 2026-11-04・逐語「今後こんな手抜き検索しないでほしいんだが。」）。

1. 候補が無い欄と見つからなかった欄は、WebSearch で探します。
2. ページは curl と Chromium の両方で開きます。WebFetch が使えれば、WebFetch でも開きます。
3. 開けないページと、404 と書かれたページは、過去のページの保存（web.archive.org）も見ます。
4. 見つからなかった物には、検索した語・開いたページ・無かったことを書きます。探していない物は「探していない」と書き、その件数を報告の先頭に書きます。
5. 時間の制限が無いのに、「時間の都合」を探さない理由にしません。

### 教科書の書き方の決まり

項目の名前と並びは、見本のとおりです。項目の名前は、定義表の要素の今の名前にします。まだ一つに決めていない候補の欄は、名前に「の候補」を付けます。候補の行の欄は、どの要素でも同じです（「五」の表「候補の行の共通の欄」）。名前を漢字一文字で新しく作りません。説明の無い項目を足しません。足したい項目が在れば、止まって聞きます。名前の決まりの全文は `SDK/.claude/rules/要件定義書_レベル4_指標の構造.md` の「要素の命名の決まり」に在ります。選べる語は、「五」の表「選べる語」のとおりで、ほかの語を書きません。役割の区分は複数の行で持てます。

追加の決まりは次のとおりです。

**名前と値の書き方**

1. **指標の名前は2つ書きます。** `名前` は指標データの名前のまま（プログラムが読む名前）です。`照らしと出どころ` の中の `元の指標` は、英語の正式名と開発者です（例＝RSI（Relative Strength Index・Wilder））。前の依頼の結果の `元の指標` の欄と、資料の表の `元の指標` の欄から写します。無い指標は Web で探します。検索には `元の指標` の英語の名前を使います。
2. **値の欄に「書いてない」「持たない」を書きません。** 文が無ければ、`null` か空の並びにします。
3. **値は数で書きます。** 1つの候補の行に1つの値です。「7 to 9」のような文は、値 7 と値 9 の2行にします。
4. **候補を全部並べます。** 1つに選びません。代表の値の候補は、スキャル・デイトレ・既定に分けます。文に「scalping」「day trading」（スキャル・デイトレ）の語が在るときだけ、その側に入れます。足の名前だけの文は `既定` に入れ、候補の `文の時間足` に足を書きます。どちらとも読めなければ `既定` に入れて注記に書きます。
5. **範囲の候補は、必ず探します。** パラメータの `範囲の候補` と `閾値の範囲の候補` は、スキャル・デイトレの代表の値と並ぶ必須の要素です（要件＝最後の段階で範囲から探す・指標ごとに一つ）。文の値は `挙げた値` に書き、`範囲の形` の欄に「文に両端が在る」か「値を挙げただけ」と書きます。文が「入力できる範囲」（例＝期間は 2〜500 まで入力できる）や「強さの区切り」（例＝0〜25 は弱い・25〜50 は強い）を言っているときは、`範囲の形` にその語を書きます。範囲の数そのものは作りません。取り込みが、候補の全部の値の最小から最大までを、その指標の一つの範囲にします。両端の文が無い指標は、代表の値の候補だけからでも範囲ができます。文が一つも無ければ空にして注記に「見つからなかった」と書きます。
6. **逐語は1文字も変えず、文を切らずに全部写します。** 前の依頼の結果で途中で切れている文は、ページを開いて全部写します。
7. **選べない足（週足・月足ほか）は、時間足の欄に書きません。** 候補の `文の時間足` を `null` にし、注記に原文を書きます。
8. **閾値を持たない指標は、** `閾値の範囲の候補` を空にして、`閾値を持たない理由` に理由と逐語を書きます。
9. **文の分類は、語の有無でなく意味で読みます。** 「true range」の range はレンジの話ではありません。「short-term」の short はショートの話ではありません。別の線の文（基準線の行に転換線の文ほか）を混ぜません。
10. 計算の式は `照らしと出どころ` の中の `教科書の計算の式` に、式の文と URL を書きます。文が無ければ `null` にします。
11. 指標データや前の依頼の結果と食い違う値は、消さずに候補に並べ、注記に書きます。どちらが正しいかは書きません。
12. **閾値の単位に「値段」「ドル」を書きません**（要件 H6）。値段や USD で書かれた閾値の文は、`閾値の範囲の候補` に `単位` を `null` で写し、`注記` に「値段の絶対値の文」と書きます。使い方の行の `閾値` には入れません。`値の単位と値域` の単位には「値段」「ドル」を書けます（値域の説明のため）。
13. **選べる語に無い単位**（CMF の値の幅ほか）は、単位を `null` にして、`値の単位と値域` の候補の行の `値域` の中の `有界`（下限と上限の組）に、文の両端の値を書きます（見本の CMF）。語を足しません。
14. **部品の記録に置く指標**は、一番上に `置く記録` を書きます（値＝部品の記録）。指標の記録に置く指標には書きません。

**使い方の行の書き方**

15. **`場面と型` の中の `型` と `時間足` は、文に書いてあるときだけ書きます。** `型` は入口の型の名前（down・flat_up など、文に在る語をそのまま）です。無ければ `型` は `null`、`時間足` は空の並びにします。足の組が文に在れば `時間足の組` に書きます。足は法則と engine_tuner が決める物なので、推測で埋めません。
16. **`出どころ` の文に数値が在れば、その行の `閾値` に必ず書きます。** 文に足の名指しが無ければ、`既定` に入れて注記に書きます。同じ値を `閾値の範囲の候補` に書いていても、行の `閾値` にもう一度 書きます。
17. **文に売買の方向が無い行は、`玉の向き` の欄を書きません。** `null` にしません。プログラムは、欄が無ければ「両方」と読みます。文に方向が在るときだけ、選べる語で書きます。
18. **`向き` は、level・slope・slope_avg・diff の行で必ず文から読みます。** 読めなければ `null` にして注記に書きます。band・cross・touch ほかの行は、文に無ければ `null` のままです。
19. **向きを持つ指標を絶対値で使う文**（DI差の大きさほか）は、`前処理` に「絶対値」と書きます。
20. **閾値の文が無い指標**（ATR% ほか）は、閾値を空にして注記に「見つからなかった」と書きます。数を作りません。倍率の文（ATR の2倍ほか）は、形「倍率」・単位「ATR の倍数」で書きます。
21. **帯（band）の行は、文に在る数を書きます。** 両端が在れば、行を分けて両方書きます。中心の値だけなら、その値だけを書き、注記に「中心の値だけが文に在る」と書きます。両端を作りません。
22. **線どうしのクロス（cross）は、** `合図の形のパラメータ` に、名前「組の相手」の行を書き、`代表の値の候補` の `既定` の `候補の値` に指標データの名前を書きます（見本の DI差）。水準を抜けるクロスは、組の相手でなく `閾値` に書きます。どちらも文に無ければ空のままにして、注記に書きます。文に期間の組が在れば、`パラメータの代表の値の候補` に軸ごとに書きます。
23. **本数や幅の文**（何本続いたら・何本以内に・どれだけ開いたら）は、`合図の形のパラメータ` に、名前「持続の本数」「何本以内か」「開き」などの行で書きます。数が文に無ければ、候補を空にして `注記` に書きます。
24. **傾き（slope・slope_avg）の行は、** 名前「傾きの本数」（何本前との差か）を `合図の形のパラメータ` に書きます。平均を取る文は、名前「平均の本数」も書きます。文に本数が無ければ候補を空にします（見本の ADX・RSI）。

### 禁止

1. データ・プログラム・文書を直しません。作ってよいのは、「八」の出す物だけです。とくに、リポジトリの一番上の `.claude/rules/` と `SDK/.claude/rules/` を直しません。
2. 値を決めません。おすすめを書きません。
3. 書いてないことを、推測で埋めません。検索結果の要約だけで書きません。要約の文しか得られないときは、「未確認」にします。
4. 乱数を使いません。
5. engine_tuner と、その前に通す検査（G2・H2・材料の検査）を走らせません。5分足のデータがこの環境に無いので、走らせても止まります。
6. hook（書き込みや実行の前に走る検査のプログラム）に止められたら、回り込まず、止められたときの文を報告に書いて作業を終えます。
7. 短いスクリプトと途中の出力は、リポジトリの外の一時フォルダに置きます。

## 五 提供する資料

### 見本（書き方の正本）

- `.claude/state/indicator_review/research/textbook_sample_rsi.json`：全部の要素が在る指標の見本です。
- `.claude/state/indicator_review/research/textbook_samples_20261105.json`：書き方の違う指標の見本です。どの見本にどの書き方の実例が入っているかは、下の表「見本に入っている書き方の実例」を見てください。見本には、今回の相手に無い指標（LeeMykland・DPO教科書% など）も入っています。書き方の例として読むだけで、作る相手には入れません。

```
git fetch origin refactor/e35-e36-split-strat-base
git show FETCH_HEAD:.claude/state/indicator_review/research/textbook_sample_rsi.json
git show FETCH_HEAD:.claude/state/indicator_review/research/textbook_samples_20261105.json
```

### 要素ごとの書き方の表（プログラムが作った）

<<項目の欄>>

<<選べる語>>

<<実例>>

<<実例なし>>

### 読む物

| 読む物 | 置き場 | なぜ読むか |
|---|---|---|
| 定義表 | `SDK/scripts/priority_rebuild/indicators/indicators.json` の `要素の定義表` | 要素の名前と選べる値の正本 |
| 名前の読み方 | 前の依頼の依頼書 `.claude/instructions/cloud_textbook_all_20261103.md` の「名前の読み方」 | 指標の名前の意味 |
| 指標の組み合わせの知識 | `SDK/.claude/memory/indicator_combination_kb.md` の §3・§4・§10.2 | 合図の弱点を見る条件・足の決め方・期間違いの2本の組 |

### 材料（前の依頼までに調べた物。先に読み、在る値はここから写す）

**在る値は、Web で探し直しません。下の材料から見本の書き方へ写します。** 材料は全部読みます。表の「ブランチ」は、このリポジトリの origin のブランチの名前です。ファイルは、そのブランチの中の書いてある場所に在ります。

| 材料 | ブランチ | ファイル |
|---|---|---|
| 全指標の調べ（前の依頼の結果） | `research/textbook-all-1`〜`research/textbook-all-5` | `.claude/state/indicator_review/research/out_c1.json`〜`out_c5.json` |
| 同上の続き | `research/textbook-all-6` | `.claude/state/indicator_review/research/out_c6_01.json`〜`out_c6_08.json` |
| 9種の文書 | `research/textbook-9-kinds` | `SDK/.claude/memory/textbook_9kinds_kb.md` |
| 9種の確かめ直しと候補 | `research/textbook-recheck-264` | `.claude/state/indicator_review/research/out_textbook_recheck_264.json`（基準線の転換線の文の誤りなどが書いてある） |
| 閾値とパラメータの範囲の文 | `research/textbook-ranges-270` | `.claude/state/indicator_review/research/out_textbook_ranges_270.json` |
| 指標データとの照らし | `research/textbook-compare-222` | `.claude/state/indicator_review/research/out_textbook_compare_222.json` |
| 前に作った教科書（古い書き方。今回の書き方へ写す相手） | `research/textbook-format-1` | `.claude/state/indicator_review/research/out_t1_01.json`。今回の成果物と同じ名前ですが、別のブランチの別のファイルです。文と値はここから写します。書き方は `--textbook-new-form` で直します（下の「プログラム」）。足りない要素はその後で足します |
| 資料の表と閾値の調べ | `refactor/e35-e36-split-strat-base` | `.claude/state/indicator_params_review.json`・`indicator_params_by_strategy.json`・`indicator_roles_thresholds.json`、`.claude/state/indicator_review/research/out_w1.json`〜`out_w4.json`・`threshold_role.json` |

### プログラム

- `python3 .claude/state/indicator_review/gen_indicators_draft.py --try-textbook-many <教科書のファイル…>`：書き方のテスト。読む口が全部の要素を読めるかを試し、定義表と違う名前・古い名前・玉の向きが null の行で止まります。最後の行に「合計の違い」（見つけた問題の数の合計）を出します。
- `python3 .claude/state/indicator_review/gen_indicators_draft.py --textbook-new-form <古い書き方のファイル> <新しい書き方で書く先>`：前に作った教科書を、今回の書き方へ写します。

## 六 納期・工数

- 期限は決めません。9種で一区切りです。9種を作ったら、プッシュして報告し、作業を終えます。
- 始めた時刻と終えた時刻を `date -u` で測り、報告に書きます。
- 時間を理由に、探すことを省きません（「四」の探し方の決まり）。

## 七 受入の条件

次の全部が通れば、完成です。コミットの前に、自分で確かめます。

1. `jq 'length' out_t1_01.json` が 9 を返す。
2. `jq -r '.. | strings | select(. == "書いてない" or . == "持たない")' out_t1_01.json` が何も返さない。
3. `python3 .claude/state/indicator_review/gen_indicators_draft.py --try-textbook-many out_t1_01.json` の最後の行の「合計の違い」が 0。
4. 同じテストが出す「書き写し忘れの疑い」の行を、全部 読んで処理した。意味は次のとおりです。
   - 教科書の使い方の一行には、三つの物が入っています。逐語（調べたページから写した英文そのもの）と、閾値の欄（その英文が言っている「この値を超えたら」の値を書く欄）と、合図の形のパラメータの欄（「何本続いたら」「どれだけ上がったら」の本数や幅を書く欄）です。
   - 抜けの例＝ADX の見本の一行では、逐語に「ADX が安値から四つ上がるまで待て」と書いてあったのに、二つの欄が両方 空でした。英文は写したのに、その中の値を欄に書き写していない状態です。engine_tuner は英文を読まないので、書き写さない値は使われません。
   - テストは、英文の中に数字が在るのに二つの欄が両方 空の行を、「書き写し忘れの疑い」として出します。英文の数字が、全部 値とは限りません。本の頁の番号や、「次の足」の足の番号も数字です。プログラムには見分けられないので、出た行をあなたが読み、値なら欄に書き写し、頁の番号などなら注記に「閾値ではない」と書いてください。
5. 「探していない」物の件数を、報告の先頭に書いた。
6. ブランチ `research/textbook-format-2` にプッシュできた。

## 八 報告と連絡

### 出す物

ブランチは `research/textbook-format-2` です。置き場は `.claude/state/indicator_review/research/` です。このフォルダは .gitignore の対象なので、コミットのときに `git add -f` を使います。master へは入れません。

**1. `.claude/state/indicator_review/research/out_t1_01.json`** は、今回の9種の配列です（今回 作るのは、この一本だけです。続きの回では `out_t1_02.json`、… と番号を進めます）。1件の書き方は見本のとおりで、次の2つの項目を足します。

- `探した記録`：要素ごとに、検索した語と、開いたページを書きます。形＝`[{"要素": "", "検索の語": [""], "開いたページ": [{"URL": "", "HTTP": 200, "読んだ日": "", "当たる文": "在る"}]}]`。`当たる文` には、そのページにその要素の文が在ったかを「在る」か「無い」で書きます。
- `閾値を持たない理由`：閾値を持たない指標だけ。

**調べ直しのファイル：** 頼んだ人が指標と要素を指定して調べ直しを頼んだときは、`out_t1_redo_01.json`、… に書きます。項目は `名前` と、調べ直した要素だけです。テスト（`--try-textbook-many`）に元のファイルの後ろに並べて渡すと、同じ指標の同じ要素だけが差し替わります。定義表に要素が増えたときも、同じ書き方で足した要素だけを書きます。前のファイルは書き替えません。

**2. `.claude/state/indicator_review/research/out_t1_summary.md`** は、人が読むまとめです。結論を先に書きます。探していない物の件数（先頭）、相手の数と作った数、要素ごとの値が在る指標の数と見つからなかった指標の数、確かめられなかった物とその理由、始めた時刻と終えた時刻、を書きます。

### 終わったときの報告（会話で返す）

1. 探していない物の件数（先頭に書きます）。
2. ブランチの名前と、最後のコミットの番号。
3. 作った指標の数と、ファイルの数。
4. 要素ごとの、値が在る数と見つからなかった数。
5. かかった時間。
6. 確かめられなかった物と、その理由。

### 質問の仕方

書き方の読み方で迷ったら、結果のファイルを作らずに止まり、迷う点を一覧にして会話で聞きます（「四」の進め方）。

## 付録（頼んだ側の記録。あなたは読まなくてよい）

<<要件>>

<<後で直す>>
<!-- TEXTBOOK_REQ_AUTO_END -->
"""


def request_doc() -> str:
    """依頼書の全文を作る（REQUEST_TEXT の文に、request_block() の表を差し込む）。"""
    block = request_block()
    parts = {}
    for chunk in ("\n" + block).split("\n### ")[1:]:
        parts[chunk.split("\n", 1)[0]] = "#### " + chunk.rstrip("\n")       # 文の見出し（###）の下に入るので、一段 下げる
    def part(prefix):
        hits = [v for k, v in parts.items() if k.startswith(prefix)]
        if len(hits) != 1:
            raise SystemExit(f"❌ 依頼書の表「{prefix}」が request_block() にちょうど一つ無い: {len(hits)}")
        return hits[0]
    doc = REQUEST_TEXT
    req = SDK / ".claude" / "rules" / "要件定義書_レベル4_指標の構造.md"          # 要素の一覧の正本（まこさん 2026-11-05「要件定義書に一覧つくって」「それを正本として」）
    txt = req.read_text(encoding="utf-8")
    s0, e0 = txt.find("## 指標の教科書に載せる要素の一覧"), txt.find("## 要素の命名の決まり")
    if s0 < 0 or e0 < 0 or e0 < s0:
        raise SystemExit(f"❌ 要件定義書に「指標の教科書に載せる要素の一覧」の節が無い: {req}")
    sec = "#### 作る要素の一覧（正本＝要件定義書_レベル4_指標の構造.md の「指標の教科書に載せる要素の一覧」。プログラムがそのまま写した）\n\n" + txt[s0:e0].split("\n", 1)[1].strip("\n").replace("\n**", "\n**")
    doc = doc.replace("<<要素一覧>>", sec)
    for ph, prefix in (("<<項目の欄>>", "教科書の項目の名前"), ("<<選べる語>>", "選べる語"),
                       ("<<実例>>", "見本に入っている書き方の実例"), ("<<実例なし>>", "見本に実例が入っていない書き方"),
                       ("<<相手>>", "調べる相手"), ("<<要件>>", "要件との対応"), ("<<後で直す>>", "この依頼の後の工事で直す定義表")):
        doc = doc.replace(ph, part(prefix))
    left = [p for p in ("<<要素一覧>>", "<<項目の欄>>", "<<選べる語>>", "<<実例>>", "<<実例なし>>", "<<相手>>", "<<要件>>", "<<後で直す>>") if p in doc]
    if left:
        raise SystemExit(f"❌ 依頼書に差し込めていない表: {left}")
    return doc.replace("<<DATE>>", REQUEST_DATE)


def write_request(verify: bool = False) -> int:
    """--write-request＝依頼書の全文を作って書く。--verify-request＝手で書き換えられていないかを見る。"""
    import hashlib
    body = request_doc()
    h = hashlib.sha256(body.encode("utf-8")).hexdigest()[:12]
    doc = body.replace("<<HASH>>", h)
    if verify:
        cur = REQUEST_MD.read_text(encoding="utf-8") if REQUEST_MD.exists() else ""
        ok = cur == doc
        print(("✅" if ok else "❌") + " 依頼書は" + ("作り直した物と同じ" if ok else "作り直した物と違う（--write-request で作り直す）"))
        return 0 if ok else 1
    REQUEST_MD.write_text(doc, encoding="utf-8")
    print(f"依頼書の全文を作り直した＝{REQUEST_MD}（hash {h}・{len(doc.splitlines())} 行）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
