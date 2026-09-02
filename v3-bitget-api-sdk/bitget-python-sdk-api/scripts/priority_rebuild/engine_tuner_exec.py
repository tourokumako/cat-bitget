#!/usr/bin/env python3
"""engine_tuner_exec.py — 歩3 実行器（レシピ＝条件データを読んで共通の売買ループで売買する）

形式の正本＝.claude/ratchet/engine_tuner_step2_condition_format.md（CP3 反映版・まこさん GO 2026-07-30）。
本ファイルは 歩3 の3部品を持つ:
  ① スキーマ検証器 validate_recipe＝生成の物理制約 G1〜G6（設計書 §4）。壊れたレシピは読み込みで拒否。
  ② 実行器 run_recipe＝レシピを読んで入口と出口を判定する共通売買ループ（設計書 §1〜§7）。
  ③ 恒等検収 --identity＝現行 S2（e38_logic_parts.generic_logic_loop）をレシピで書き写し、
     売買記録が md5 完全一致すること（設計書 §8）。番人＝枝順入れ替えで不一致・R14＝avg/separate の両形。

守る制約: H2＝材料は当該バーまでの確定値のみ／H5＝エントリー執行仕様（指値 close×(1∓offset)・TTL3・
post_only）は本実行器のグローバル定数＝レシピは上書きできない（設計書 §1）／H8＝期間は periods.py／
H13＝score.py・eval_engine に触れない（記録は e37._record を import 再利用＝会計は既存系のまま）／
値の4区分（分位・名前つき定数・整数グリッド・legacy）＝生の数字のフィールドは存在しない（設計書 §2.4）。
legacy 値・legacy 材料列は lane="legacy"（恒等検収・過去資産の書き写し）専用＝探索レシピでは検証器が拒否。

採点はしない・売買記録CSVは書かない・score.py は呼ばない（恒等はメモリ上の md5 比較）。
自己検査: python3 engine_tuner_exec.py --selftest（壊したレシピ21種で全部止まる・正しい3種は通る・歩4/歩6-1 拡張の既知答え込み）
恒等検収: python3 engine_tuner_exec.py --identity（S2・値決め窓）／--identity-quick（短窓デバッグ）
恒等検収 L1: python3 engine_tuner_exec.py --identity-l1（歩6-1＝採用中 L1 の書き写し）／--identity-l1-quick
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import pathlib
import re
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import e37_scalp as e37                      # noqa: E402  _record（記録＝会計の既存系）・SCALP_FLOOR 等
import e38_logic_parts as parts              # noqa: E402  恒等検収の対象実装・prepare_df（材料の実体）
import indicator_reference_diag as iref      # noqa: E402  材料・系統・定数レジストリの正本
import score as _score                       # noqa: E402  出口理由の maker/taker 登録の正本（H13・読むだけ）
from strat_base import ENTRY_OFFSET, TTL     # noqa: E402  H5 執行仕様（レシピは上書きできない）

HERE = pathlib.Path(__file__).resolve().parent
RECIPE_DIR = HERE / "recipes"

# ── 実行器のグローバル定数（H5・設計書 §1「エントリーの執行仕様はレシピに持たない」）──
UNIT_LOT = parts.UNIT_LOT                    # 0.012 BTC/lot（S1/L1 と同じ lot 幾何）
GAP_DIAG = 0.5 / 100.0                       # ceil_type 診断の gap（v26_gap と同じ・net 不関与・診断列のみ）

# ── 形（11種・設計書 §2.2）と役割（§2.1）──
FORMS = ("level", "band", "band_exclude", "slope", "slope_avg", "cross",
         "streak", "within_n", "barssince", "diff", "touch", "candle_dir", "hysteresis")
# ★hysteresis（入る線と出る線を別にして、状態を保つ形）＝M2-2-5・2026-08-21 まこさん承認 24a453d6…。
#   法則＝U10（一度「上げ」と判定したら解除まで保つ）・C6（安定させる仕組みは2つ・別物）・
#         C7（続く長さは探す値）。正本＝.claude/memory/regime_detection_kb.md §11。
#   ★名前の出どころ＝同 KB §4-6 の逐語 "Use hysteresis. Entry threshold: P(Bear) > 0.6.
#     Exit threshold: P(Bear) < 0.4."（CC が作った造語ではない）。
#   ★既存の streak（何本 続いたら成立）とは別物＝混ぜない（C6 が「2つ・別のもの」と明記）。
#   ★末尾に足した理由＝生成器の並び（_STATE_ORDER）の順番を1つも動かさないため
#     （順番が変わると、同じ種から違う案が出る＝過去の探索をやり直せない・M2-2-3b の教訓 L-514）。
# 入れ子形（内側は単純形のみ・1段まで）＝「条件に掛ける部品」。
# ★barssince（何本前に成立したか・2026-08-12・段C の C-6）を足した。
#   出どころ＝.claude/ratchet/condition_parts.json の部品 barssince（業界の同じもの＝pine:ta.barssince）。
#   中身＝内側の条件が最後に成立してから 何本 経ったかを数え、その本数を閾値と比べる。
#   ★within_n との違い（大事）。
#     barssince ≤ k は「過去 k+1 本のどこかで成立」＝ within_n(n=k+1) と同じ結果になる。
#     **新しく書けるのは above の側**＝「最後に成立してから n本 以上 経っている」。
#     直す前は、これを書く方法が1つも無かった（within_n は『経った』を書けない）。

# ══ 形の性質表（M2-2-3b・2026-08-21 まこさん承認 e4b86277…）════════════════════════════
#   なぜ要るか。
#     形の「性質」（材料が何本 要るか・帯の値を持つか・向きが要るか…）が、直す前は
#     **13か所に手で書き写されていた**（M2-2-3 の数え上げ＝プログラムに構文木を読ませて実測）。
#     ＝形を1つ足したとき、13か所のどれかに入れ忘れると、**足した形が黙って効かない。**
#     いちばん効いたのは engine_tuner_gen.py:1047（出口で使う形を5件に手で絞る）。
#     ★これを「性質を1か所に持ち、使う側はそこから作る」形に変えた。
#     形を足すときは、この表に1行 書くだけでよい。
#   ★中身は、直す前の手書きの並びを1件も変えずに写したもの。
#     写しが1件も違わないことは selftest（form_spec_selftest）が毎回 照合する。
#   ★人が読む説明の表（.claude/ratchet/engine_tuner_step2_condition_format.md §2.2）にも
#     「材料」「必要な値」の欄が在る。gen_materials.forms_table がこの表と突き合わせる。
#
#   欄の意味（★「だいたい同じだからまとめる」をしない＝同じにならない所は別の欄にした）:
#     nest        … 入れ子形（内側に条件を1つ包む）           → NEST_FORMS
#     pair        … 材料の本数。"1"／"2"（必ず2本）／"2or1th"（2本 か 1本＋閾値）／"none"／"inner"
#                   ／"inner2"（内側の条件2つ＝入る on と 出る off・M2-2-5 で足した）
#     band        … 下限・上限（lo/hi）を持つ                 → 帯の形
#     needs_side  … 向き（side）が要る（入れ子の外側で見る分） → level・diff・slope・slope_avg
#     slope_n     … 傾きの本数 n を探索の枠に出す             → slope・slope_avg
#     pre_ok      … 材料に前処理を付けられる                  → level・band・band_exclude
#     state_free  … 玉の状態を見ない                          → STATE_FORMS（cross 以外）
#     exit_ok     … 出口の確認条件で使ってよい                → level・cross・slope・diff・candle_dir
#     trigger_ok  … 引き金（縁で発火）に置いてよい            → TRIGGER_FORMS
#   ★trigger_ok は、最初の数え上げが取りこぼした欄。
#     理由＝TRIGGER_FORMS の並びに、形ではない名前（cross_val＝生成器の中だけの呼び名）が
#     混ざっていて、「全部が形の名前」で探す数え方に引っかからなかった。
#     取りこぼしを見つけたあと、「形の名前が2件以上 混ざった並び」で数え直したら、この1件だけだった。
FORM_SPEC = {
    "level":        dict(nest=False, pair="1",      band=False, needs_side=True,  slope_n=False, pre_ok=True,  state_free=True,  exit_ok=True,  trigger_ok=True),
    "band":         dict(nest=False, pair="1",      band=True,  needs_side=False, slope_n=False, pre_ok=True,  state_free=True,  exit_ok=False, trigger_ok=False),
    "band_exclude": dict(nest=False, pair="1",      band=True,  needs_side=False, slope_n=False, pre_ok=True,  state_free=True,  exit_ok=False, trigger_ok=False),
    "slope":        dict(nest=False, pair="1",      band=False, needs_side=True,  slope_n=True,  pre_ok=False, state_free=True,  exit_ok=True,  trigger_ok=True),
    "slope_avg":    dict(nest=False, pair="1",      band=False, needs_side=True,  slope_n=True,  pre_ok=False, state_free=True,  exit_ok=False, trigger_ok=False),
    "cross":        dict(nest=False, pair="2or1th", band=False, needs_side=False, slope_n=False, pre_ok=False, state_free=False, exit_ok=True,  trigger_ok=True),
    "streak":       dict(nest=True,  pair="inner",  band=False, needs_side=False, slope_n=False, pre_ok=False, state_free=True,  exit_ok=False, trigger_ok=True),
    "within_n":     dict(nest=True,  pair="inner",  band=False, needs_side=False, slope_n=False, pre_ok=False, state_free=True,  exit_ok=False, trigger_ok=True),
    "barssince":    dict(nest=True,  pair="inner",  band=False, needs_side=False, slope_n=False, pre_ok=False, state_free=True,  exit_ok=False, trigger_ok=True),
    "diff":         dict(nest=False, pair="2",      band=False, needs_side=True,  slope_n=False, pre_ok=False, state_free=True,  exit_ok=True,  trigger_ok=True),
    "touch":        dict(nest=False, pair="2",      band=False, needs_side=False, slope_n=False, pre_ok=False, state_free=True,  exit_ok=False, trigger_ok=False),
    "candle_dir":   dict(nest=False, pair="none",   band=False, needs_side=False, slope_n=False, pre_ok=False, state_free=True,  exit_ok=True,  trigger_ok=True),
    # ★hysteresis（M2-2-5）＝材料を直接は取らない（on と off の中の条件が取る）。
    #   trigger_ok=False の理由＝縁で発火する形ではない（状態を保つ形）。C5＝場面の判定はふるいであって
    #   「いま建てろ」の合図ではない。exit_ok=False の理由＝出口の確認条件は玉ごとの判定で、
    #   状態を保つ形の意味（相場の場面が続いているか）と噛み合わないため（要るなら別途 承認をもらう）。
    "hysteresis":   dict(nest=False, pair="inner2", band=False, needs_side=False, slope_n=False, pre_ok=False, state_free=True,  exit_ok=False, trigger_ok=False),
}


def forms_where(field: str, want=True) -> tuple:
    """性質表から「その性質を持つ形」の並びを作る。★手で並べない（M2-2-3b）。

    並びは FORMS の順を保つ（同じ入力なら同じ並び＝再現できる・next_step §6 の56番と同じ思想）。
    """
    return tuple(f for f in FORMS if FORM_SPEC[f][field] == want)


def forms_pair_in(*kinds: str) -> tuple:
    """材料の本数の種類で絞る（例＝forms_pair_in("2", "2or1th")）。"""
    return tuple(f for f in FORMS if FORM_SPEC[f]["pair"] in kinds)


NEST_FORMS = forms_where("nest")                             # ★手書きから性質表由来へ（M2-2-3b）
ROLES = ("env", "trigger", "sufficiency", "location")
# 側の比較（歩6-1 里程標6 で strict を追加）。above/below は境界を含む（≥ / ≤）。
# above_strict/below_strict は境界を含まない（> / <）＝過去実装が「〜未満」で書いている枝の写しに要る。
SIDES = ("above", "below", "above_strict", "below_strict")
EXEC_METHODS = ("maker", "taker", "post_only", "stop")          # 歩3 で実行できる方式
EXEC_REGISTERED_ONLY = ("iceberg", "twap", "vwap")              # 登録済みだが実行不能＝拒否側（CP3 Q1）
# 出口理由は score.py の maker/taker 登録と一致していること（H13・acceptance_checklist D）。
# ★2026-08-02（歩6-1 里程標9）に出どころを score.py 本体へ変えた。理由を書く。
#   前は REASONS_MAKER を e37_scalp の _MAKER_EXIT から、REASONS_TAKER を手書きの4個から作っていた。
#   ところが e37_scalp の _MAKER_EXIT には TREND_CAUGHT_TP が入っておらず、score.py の
#   MAKER_EXIT_REASONS には入っている＝2つが食い違っていた（e37 側のコメントは「score.py と完全同期」
#   と書いてあるが実際は同期していない）。この検査が見るべき正本は審判 score.py なので、そこから直接
#   読む形にした。手書きの写しを置くと、また黙ってずれる。
#   ⚠️ 別途まこさんへ報告する事実＝e37_scalp が売買記録CSVに書く net_usd の列は、TREND_CAUGHT_TP を
#   成行（taker）として計算している。score.py は指値（maker）として計算し直す。公式の net は score.py が
#   出すので採否は正しいが、e37 の画面表示と CSV の net 列だけが実際より悲観的に出る。
REASONS_MAKER = set(_score.MAKER_EXIT_REASONS)
REASONS_TAKER = set(_score.TAKER_EXIT_REASONS)

# ── 指標のオン・オフの印（M2-C-2・設計書 iter="indicator-switch-20260902"・まこさん承認 2026-09-02）──
# 何のためか＝まこさん決定 2026-08-27（逐語「本来の目的が達成できるまでは、指標一覧はta 43種にする」）を
#   engine_tuner に効かせる。印は .claude/ratchet/indicator_switch.json（gen_indicator_switch.py が機械で作る）。
#
# ★判定はこの1つの関数だけ。生成器（engine_tuner_gen）も実行器も、ここを呼ぶ＝同じ判定を2か所に書き写さない。
# ★印でできるのは減らすことだけ＝承認済みの型の表に無い指標は、印をオンにしても使えない
#   （使える指標＝型の表 ∩ 印がオン の積）。だから型の表の承認とハッシュ値は、印を切り替えても変わらない。
# ★印が無ければ止まる（fail-closed）＝「印を消せば全部 使える」という緩む方向の道を作らない。
INDICATOR_SWITCH_PATH = HERE.parents[1] / ".claude" / "ratchet" / "indicator_switch.json"
_SWITCH_CACHE: dict | None = None


def load_indicator_switch() -> dict:
    """指標のオン・オフの印を読む。無ければ止まる（fail-closed・M2-C-2）。"""
    global _SWITCH_CACHE
    if _SWITCH_CACHE is None:
        if not INDICATOR_SWITCH_PATH.exists():
            raise SystemExit(
                f"[指標の印] {INDICATOR_SWITCH_PATH.name} が無い"
                "（python3 gen_indicator_switch.py --write で作る・fail-closed・M2-C-2）")
        d = json.loads(INDICATOR_SWITCH_PATH.read_text(encoding="utf-8"))
        d["_on_set"] = set(d.get("on") or [])
        d["_geo_set"] = set(d.get("geo_on") or [])
        _SWITCH_CACHE = d
    return _SWITCH_CACHE


def indicator_enabled(name: str) -> bool:
    """材料が「使う」に入っているか。name＝カタログの部品名（RSI14）でも 種類名（RSI）でもよい。

    ★種類名で照らす＝印は種類に付く（M2-C-2）。部品名で渡されたときは、参照表で種類に直してから見る。
    """
    sw = load_indicator_switch()
    if name in sw["_on_set"]:
        return True
    ent, _prm = iref.find(name)
    return bool(ent is not None and ent["family"] in sw["_on_set"])


def geo_enabled(name: str) -> bool:
    """レンジ幾何の列（W%・帯内位置%）が「使う」に入っているか。"""
    return name in load_indicator_switch()["_geo_set"]


def indicator_switch_fingerprint() -> str:
    """印の指紋（走行の再開のときに、前回と同じ印かを照らすため）。"""
    return str(load_indicator_switch().get("fingerprint", ""))


# ── 材料の名前組み立て（family×param×tf → カタログ名・G6 fail-closed）──
# ★2026-08-11（マイルストーン①のフロー 段6 の 6-7）に、手書き19件から「参照表から機械で作る」形へ
#   変えた。理由を残す。
#   前は「指標の名前 ＋ 数字1つ」の形だけを手で19件 並べていた（2026-08-01 の commit 254066a で
#   作られ、一度も増えていない。当時のコメントの逐語＝「単純数値パラメータの family だけ登録
#   （複合パラメータ＝MACD 等は歩4 で拡張＝未登録は生成不可）」。その歩4 は同じ 2026-08-01 に
#   承認されて終わり、拡張されなかった）。
#   そのため、材料カタログに列が在っても engine_tuner が条件の材料に選べない指標が 232種類 あった
#   （2026-08-09 実測＝MACD・BB%b・一目の転換線と基準線・ローソク足の形 ほか。5,049列 のうち
#   選べるのは 432列＝8.6% だけ）。載っていない指標はレシピの読み込みの段階で G6 が拒否する。
#   いまは参照表 indicator_reference_diag.REFS（材料カタログの列名の正本）の正規表現から、
#   名前の組み立ての型を機械で作る。＝カタログに列が増えれば、そのまま選べるようになる
#   （手書きの表に足し忘れる穴が構造的に消える）。
#   番人＝--selftest の往復テスト＝材料カタログの全列名を family と数字に分解し、この表で組み立て
#   直して1文字も違わないことを確かめる（違えば表が実物とずれている）。
def _template_from_pattern(pat) -> str:
    """参照表の正規表現 → 名前の組み立ての型。数字を捕まえる所を {} に置き換え、正規表現の印を外す。

    例＝ ^MACD線%\\((\\d+),(\\d+)\\)$ → MACD線%({},{}) ／ ^RSI(\\d+)$ → RSI{} ／ ^包み足$ → 包み足
    """
    body = pat.pattern
    if body.startswith("^"):
        body = body[1:]
    if body.endswith("$"):
        body = body[:-1]
    body = re.sub(r"\((?:\\d\+|\[\\d\.\]\+)\)", "\x00", body)   # 捕獲グループ＝数字の入る所
    body = body.replace("\\", "")                                # \( \) \+ \. のエスケープを外す
    return body.replace("\x00", "{}")


FAMILY_TEMPLATES = {e["family"]: _template_from_pattern(e["pat"]) for e in iref.REFS}


def build_name(m: dict) -> str:
    """材料の指定（family と数字）→ 材料カタログの列名。

    数字の渡し方は3つ＝①数字1つ（RSI14 のような形）②数字の並び（MACD線%(12,26) のような形）
    ③無し（包み足のように数字を持たない形）。組み立ての型が要る個数と合わなければ G6 で拒否する。
    """
    fam = m.get("family")
    tpl = FAMILY_TEMPLATES.get(fam)
    if tpl is None:
        _fail("G6", f"family の名前組み立てが未登録: {fam}（参照表 indicator_reference_diag に無い）")
    prm = m.get("param")
    vals = [] if prm is None else (list(prm) if isinstance(prm, (list, tuple)) else [prm])
    need = tpl.count("{}")
    if len(vals) != need:
        _fail("G6", f"材料の数字の個数が合わない: {fam} は {need} 個 要る（渡された数字＝{vals}）")
    for v in vals:
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            _fail("G6", f"材料の数字が数でない: {fam} の {v!r}")
    return tpl.format(*vals)
# 実行時の列の別名（カタログ名 → prepare_df が付ける部品列）。式は同一＝e38_logic_parts が
# 出典を observe_diag に固定した部品（prepare_df の各式と build_catalog の式が同式であること）。
RUNTIME_ALIAS = {
    "ROC24__2h": "e38_htf_roc24_2h",             # d2h close.pct_change(24)×100（同式）
    "DI差7__4h": "e38_htf_di7_4h",               # _adx_di_htf＝observe_diag._adx_di と同式
    "ADX14__2h": "e38_htf_adx14_2h",
    "Stoch%D14__2h": "e38_htf_stochd14_2h",      # raw K14 の3本平均（同式）
    "volume_ratio20__15m": "e38_vol_volr20_15m",
    "volume_ratio50__15m": "e38_vol_volr50_15m",
    "Donchian幅%20__1d": "e38_vol_donch20_1d",
}
GEO_COLS = tuple(iref.RANGE_GEO_REF)         # レンジ幾何（歩3 冒頭①で登録済み・ratio だけ条件の材料可）


class RecipeError(SystemExit):
    """スキーマ検証器の拒否（G1〜G6）＝読み込みの段階で止める（fail-closed）。"""


def _fail(code: str, msg: str):
    raise RecipeError(f"[レシピ拒否 {code}] {msg}")


# ══ ① スキーマ検証器（G1〜G6・設計書 §4）══════════════════════════════════════════════
def _is_cond(node) -> bool:
    return isinstance(node, dict) and "form" in node


def _check_not_node(node: dict, in_not: bool, where: str) -> None:
    """否定のノードの形を見る（M2-2-5・2026-08-21 まこさん承認 24a453d6…・法則 R8）。

    ★禁止2＝否定の中に否定は書けない（二重の否定は元の条件と同じ＝形を1つに決める。
      入れ子の本数 1 を禁じている既存の決まり［正規形・CP3 提案7］と同じ考え方）。
    ★これで潰れる条件はありません（二重の否定は、否定を外した式と同じ結果になるため）。
    """
    if in_not:
        _fail("G5", f"{where}: 否定の中に否定は書けない（二重の否定は元の条件と同じ＝正規形）")
    extra = set(node) - {"not"}
    if extra:
        _fail("G5", f"{where}: 否定のノードに未知のフィールド {sorted(extra)}（書けるのは not だけ）")


def _walk(node, depth=0, out=None, depths=None, in_not=False):
    """つなぎ木を歩いて (条件, 深さ) を集める。未知ノードは拒否。"""
    out = [] if out is None else out
    depths = [] if depths is None else depths
    if _is_cond(node):
        out.append(node)
        depths.append(depth)
        return out, depths
    if not isinstance(node, dict):
        _fail("G5", f"つなぎ木に不明なノード: {node!r}")
    if "not" in node:
        # ★否定（M2-2-5・法則 R8）。内側も数え上げに乗せる
        #   ＝役割の数え方・系統の数え方・条件の本数が、否定の中でも同じに効く。
        #   ★禁止1（否定の中に引き金を置けない）＝validate_recipe が明示のメッセージで止める。
        #     加えて、既存の G1（引き金は経路の最上位 all の直下にだけ置ける）でも弾かれる＝二重に守る。
        _check_not_node(node, in_not, "つなぎ木")
        _walk(node["not"], depth + 1, out, depths, in_not=True)
        return out, depths
    if "all" in node or "any" in node:
        for ch in node.get("all", node.get("any", [])):
            _walk(ch, depth + 1, out, depths, in_not)
        return out, depths
    if "if" in node and "then" in node:
        _walk(node["if"], depth + 1, out, depths, in_not)
        _walk(node["then"], depth + 1, out, depths, in_not)
        return out, depths
    _fail("G5", f"つなぎ木のノードが not/all/any/if-then/条件 のどれでもない: {list(node)}")


def _conds_under_not(node) -> list:
    """否定（not）の中に在る条件を集める（M2-2-5・2026-08-21）。

    ★何のためか＝**禁止1＝引き金（trigger）を否定の中に置かせない**ため。
      引き金は「縁で発火する」もので、その否定は「発火していないほとんど全部のバー」になります。
      経路ごとに引き金はちょうど1本、という決まり（G1）が意味を失います。
    ★既存の G1（引き金は経路の最上位 all の直下にだけ置ける）でも弾かれますが、
      そのメッセージでは「なぜ止まったか」が読み取れないので、この検査で名指しにします＝二重に守る。
    """
    out = []
    if not isinstance(node, dict):
        return out
    if "not" in node:
        inner, _d = _walk(node["not"], in_not=True)
        return inner
    if "all" in node or "any" in node:
        for ch in node.get("all", node.get("any", [])):
            out += _conds_under_not(ch)
        return out
    if "if" in node and "then" in node:
        return _conds_under_not(node["if"]) + _conds_under_not(node["then"])
    return out


def _tree_depth(node, depth=0) -> int:
    if _is_cond(node):
        return depth
    if isinstance(node, dict) and "not" in node:       # ★否定も1段と数える（M2-2-5）
        return _tree_depth(node["not"], depth + 1)
    if "all" in node or "any" in node:
        kids = node.get("all", node.get("any", []))
        return max([_tree_depth(ch, depth + 1) for ch in kids] + [depth])
    if "if" in node:
        return max(_tree_depth(node["if"], depth + 1), _tree_depth(node["then"], depth + 1))
    return depth


# ══ 材料の前処理（部品・2026-08-13・段C の C-6）══════════════════════════════════════
#   材料1本に "pre" を付けると、その列に部品を1つ掛けてから条件に使う。
#   ★形（FORMS）を増やさない。1つの仕組みで、全部の形・全部の指標に一度に効く。
#     形を1個ずつ手で足す運用は、まこさんが 2026-08-11 に指摘した形そのもの
#     （逐語＝「これは手書きで思い付いたら増やす。みたいな運用になるのか？すごい原始的なんだが。」）。
#   ★いまのバーを含めない（直前の n本を見る）。理由は2つ。
#     ①部品の正本の「これがあると書ける条件」＝「過去20本の高値を更新した（新高値）」を書くため。
#       いまのバーを含めると、自分自身を超えられない＝クロスで「更新した瞬間」を書けない。
#     ②過去だけを見る＝未来参照なし（H2）。
#   一覧の正本＝.claude/ratchet/condition_parts.json の "have"（id が下の鍵と同じ）。
#   ★`same_unit`＝掛けたあとの値が、元の列と同じ単位のままか。
#     ts_max・ts_min は同じ単位（RSI の最大値は RSI と同じ 0〜100）＝元の列と大小を比べられる
#     ＝列2本の形（クロス・差・タッチ）に使える。
#     ts_rank は 0〜1・ts_std はばらつきの幅で、元の列とは単位が違う＝元の列と大小を比べても
#     意味が無い（RSI 0〜100 と 順位 0〜1 を比べても、いつも RSI の方が大きいだけ）。
#     だから列2本の形には使わず、水準（level・band）で閾値と比べる形で使う。
#     ★これは好みの決まりではなく、単位が違うものは比べられないという算数です。
#     ★これで潰れる条件＝ありません（ts_rank・ts_std は 2026-08-12（18回目） まで1つも書けなかった）。
#   ★2026-08-21（M2-2-5・まこさん承認 24a453d6…）＝状態に入って以降を見る部品を3つ 足した。
#     これが無いと、まこさんの実例の9番（「前回解除以降かつ直近90分」の安値から+1.0%）と
#     11番（解除＝半値戻し）が1行も書けない（決まった長さの窓しか見られないため）。
#     ★窓の長さを数字で決めない＝区間は「状態を保つ形（hysteresis）が真である間」が決める。
#     ★どの状態を基準にするかは `state`（真偽の列の名前）で指定する（`n` は書かない）。
MATERIAL_PRE = {
    "ts_max": {"desc": "直前の n本の最大値（いまのバーを含めない）", "same_unit": True},
    "ts_min": {"desc": "直前の n本の最小値（いまのバーを含めない）", "same_unit": True},
    "ts_rank": {"desc": "いまの値が 直近 n本の中で何番目か（0〜1・いまのバーを含める）",
                "same_unit": False},
    "ts_std": {"desc": "直近 n本のばらつき（標準偏差・いまのバーを含める）", "same_unit": False},
    "since_min": {"desc": "指定した状態に入って以降の最小値（状態の外は値なし）",
                  "same_unit": True, "needs_state": True},
    "since_max": {"desc": "指定した状態に入って以降の最大値（状態の外は値なし）",
                  "same_unit": True, "needs_state": True},
    "at_entry": {"desc": "指定した状態に入ったバーの値（状態の外は値なし）",
                 "same_unit": True, "needs_state": True},
}
SINCE_OPS = tuple(k for k, v in MATERIAL_PRE.items() if v.get("needs_state"))


def pre_ops(same_unit: bool | None = None, needs_state: bool | None = None) -> list[str]:
    """前処理の部品の名前を返す。same_unit・needs_state を指定すると、その種類だけに絞る。

    ★needs_state は 2026-08-21（48回目・M2-2-8）に足した。理由を書く。
      M2-2-5 で「状態に入って以降」の3つ（since_min・since_max・at_entry）を足したとき、
      3つとも same_unit=True で登録した（元の列と同じ単位だから・これは正しい）。
      ところが案を作るプログラムは `pre_ops(same_unit=True)` を使って前処理を引いていたので、
      **この3つも引くようになり、`{"op": ..., "n": ...}` の形で出していた。**
      3つは n（本数）ではなく state（基準にする状態の列の名前）が要るので、
      **出した案は必ず拒否される**（`[レシピ拒否 G5] 材料の前処理 since_max に state が無い`）。
      ＝`engine_tuner_gen --selftest` が 47回目から丸ごと止まっていた（2026-08-21 に実測して発見）。
      ★案を作る側は、まだ状態の列の名前を決められない（状態の列は判定の中身が作る）ので、
        この3つは引かせない＝needs_state=False で絞る。
    """
    return sorted(k for k, v in MATERIAL_PRE.items()
                  if (same_unit is None or v["same_unit"] is same_unit)
                  and (needs_state is None or bool(v.get("needs_state")) is needs_state))


def _since_stat(a: np.ndarray, state: np.ndarray, op: str) -> np.ndarray:
    """状態に入って以降の 最小・最大・入ったバーの値（M2-2-5・2026-08-21 まこさん承認 24a453d6…）。

    ★窓の長さを数字で決めない＝区間は「状態が真である間」が決める。
      これで、まこさんの実例の「前回解除以降かつ直近90分の安値」（since_min）と
      「解除＝半値戻し」（at_entry と since_max の組み合わせ）が書けるようになる。
    ★状態の外は値なし（NaN）＝条件は既定 na=fail で不成立になる。
    ★未来を見ない（H2）＝`cummin`・`cummax`・`maximum.accumulate` はどれも過去だけを積み上げる。
      うしろのバーの値は1つも使わない。
    """
    idx = np.arange(len(a))
    prev = np.roll(state, 1)
    prev[0] = False
    entry = state & ~prev                          # 状態に入ったバー（前が偽・いまが真）
    seg = np.cumsum(entry)                         # 何回目の状態か（0＝まだ一度も入っていない）
    s = pd.Series(a)
    if op == "since_min":
        v = s.groupby(seg).cummin().to_numpy(float)
    elif op == "since_max":
        v = s.groupby(seg).cummax().to_numpy(float)
    else:                                          # at_entry
        last_entry = np.maximum.accumulate(np.where(entry, idx, -1))
        v = np.where(last_entry >= 0, a[np.maximum(last_entry, 0)], np.nan)
    return np.where(state, v, np.nan)


def _apply_pre(a: np.ndarray, pre: dict, df: pd.DataFrame | None = None) -> np.ndarray:
    """材料の列に前処理の部品を1つ掛ける。★いまのバーを含めるかは部品ごとに違う（下に理由を書く）。"""
    op = pre["op"]
    if op in SINCE_OPS:                            # ★状態に入って以降（M2-2-5）
        col = pre["state"]
        if df is None or col not in df.columns:
            raise RecipeError(
                f"[実行器] 前処理 {op} の基準にする状態の列 {col} がデータにありません"
                "（状態を保つ形［hysteresis］が作る列を、先に判定の中身［build］で作る・fail-closed）")
        return _since_stat(a, df[col].to_numpy(bool), op)
    n = int(pre["n"])
    s = pd.Series(a)
    if op == "ts_max":
        # H2OK: shift(1) は過去だけを見る（未来は見ない）。いまのバーを含めない理由＝上のブロック参照。
        return s.shift(1).rolling(n).max().to_numpy(float)
    if op == "ts_min":
        # H2OK: shift(1) は過去だけを見る（未来は見ない）。ts_max と同じ理由で いまのバーを含めない。
        return s.shift(1).rolling(n).min().to_numpy(float)
    if op == "ts_rank":
        # ★いまのバーを含める。書きたい条件が「いまの値が 過去100本で上位20%」だから
        #   （いまの値を外すと、いまの値の順位を出せない）。rolling は過去 n本だけ＝未来は見ない。
        #   pct=True＝順位を 0〜1 に直す（一番小さい値が 1/n・一番大きい値が 1.0）。
        return s.rolling(n).rank(pct=True).to_numpy(float)
    if op == "ts_std":
        # ★いまのバーを含める。「直近 n本のばらつき」＝いまを含めた n本の散らばりを見るため。
        #   rolling は過去 n本だけ＝未来は見ない。
        return s.rolling(n).std().to_numpy(float)
    raise RecipeError(f"[実行器] 材料の前処理 {op} の実行が未実装")


def _pre_of(m: dict) -> dict | None:
    return m.get("pre") if isinstance(m, dict) else None


# ══ 材料2本を組む部品（2026-08-12・段C の C-6・部品 div・corr）══════════════════════════
#   ★これは何か。列2本の形（diff）が、材料2本を「どう1本の列にまとめるか」の一覧。
#     直す前は引き算（a − b）の1通りだけがコードに直接 書いてあった。
#   ★材料の前処理（MATERIAL_PRE）と同じ作りにした＝**表に1行 足すと、組める材料の組 全部に
#     一度に効く。**形（FORMS）を1個ずつ手で増やす運用はしない（まこさん指摘 2026-08-11・逐語
#     ＝「これは手書きで思い付いたら増やす。みたいな運用になるのか？すごい原始的なんだが。」）。
#   ★出どころ＝`.claude/ratchet/condition_parts.json` の足りない部品 div（alphagen:Div ／
#     gplearn:div）と corr（alphagen:Corr）。CC が思いつきで足していない。
#   ★書き方（value）。
#     sub  … value 自体が閾値（2026-08-12 より前と1文字も変えない＝既に在るレシピを壊さない）
#     div  … value.th が閾値（「a が b の 1.2倍 を超えた」＝a ÷ b と閾値を比べる）
#     corr … value.th が閾値・value.n が窓の本数（slope と同じ書き方＝n が窓・th が閾値）
#   ★これで潰れる条件＝ありません（div・corr は 2026-08-12 まで1本も書けなかった。sub は無変更）。
PAIR_OPS = {
    "sub":  {"desc": "引き算（a − b）", "sym": "−", "needs_n": False},
    "div":  {"desc": "割り算（a ÷ b）＝比", "sym": "÷", "needs_n": False},
    "corr": {"desc": "2本の相関（直近 n本・−1〜1）", "sym": "~", "needs_n": True},
}


def pair_ops() -> list[str]:
    """材料2本を組む部品の名前（正本＝PAIR_OPS）。生成器がここから引く＝手で一覧を書かない。"""
    return sorted(PAIR_OPS)


def _pair_op_of(v: dict) -> str:
    """条件の値から、材料2本の組み方を読む。書いていなければ引き算（＝直す前と同じ）。"""
    return str((v or {}).get("op", "sub"))


def _pair_key(akey: str, bkey: str, op: str, n=None) -> str:
    """分位の解決表の鍵。★sub は 2026-08-12 より前と1文字も変えない（既に在る解決表を壊さない）。"""
    sym = PAIR_OPS[op]["sym"]
    return f"corr{int(n)}:{akey}{sym}{bkey}" if op == "corr" else f"{akey}{sym}{bkey}"


def _pair_series(a: np.ndarray, b: np.ndarray, op: str, n=None) -> np.ndarray:
    """材料2本 → 1本の列。

    ★実行器（_eval_cond）と 分位の解決表（engine_tuner_gen.build_qtable）が、どちらもこれを呼ぶ
      ＝式を2か所に書き写さない（書き写すと片方だけ直って黙って腐る）。
    """
    if op == "sub":
        return a - b
    if op == "div":
        # 0 で割ると無限になる。無限は「値なし（NaN）」に直す＝条件の既定 na=fail で不成立になる。
        with np.errstate(invalid="ignore", divide="ignore"):
            out = np.divide(a, b, out=np.full(len(a), np.nan, float), where=(b != 0))
        return np.where(np.isfinite(out), out, np.nan)
    if op == "corr":
        # 直近 n本の相関（−1〜1）。rolling は過去 n本だけを見る＝未来は見ない。
        # ばらつきがゼロの区間（値が動かない）は相関を出せない＝NaN になる（不成立）。
        return pd.Series(a).rolling(int(n)).corr(pd.Series(b)).to_numpy(float)
    raise RecipeError(f"[実行器] 材料2本の部品 {op} の実行が未実装")


def _material_name(m: dict, lane: str) -> tuple[str, str]:
    """材料1本を検証して (種別, 解決名) を返す。種別＝col/geo/state/time/legacy_col。

    ★解決名は「前処理を外した素の列名」を返す（2026-08-13）。材料の組み立て（attach_materials）と
      実行時の列引きが、この名前で実データの列を探すため。前処理は _col_array が掛ける。
    """
    if not isinstance(m, dict):
        _fail("G6", f"材料が dict でない: {m!r}")
    pre = _pre_of(m)
    if pre is not None:
        if not isinstance(pre, dict):
            _fail("G6", f"材料の pre が dict でない: {pre!r}")
        bad = set(pre) - {"op", "n", "state"}
        if bad:
            _fail("G6", f"材料の pre に未知のフィールド {sorted(bad)}（使えるのは op・n・state）")
        if pre.get("op") not in MATERIAL_PRE:
            _fail("G6", f"材料の前処理に無い部品: {pre.get('op')}"
                        f"（使えるのは {sorted(MATERIAL_PRE)}／正本＝condition_parts.json）")
        if pre["op"] in SINCE_OPS:                 # ★状態に入って以降（M2-2-5）＝窓の本数ではなく状態が区間を決める
            if not isinstance(pre.get("state"), str) or not pre["state"]:
                _fail("G5", f"材料の前処理 {pre['op']} に state（基準にする状態の列の名前）が無い")
            if "n" in pre:
                _fail("G5", f"材料の前処理 {pre['op']} に n は書けない"
                            "（区間は『状態が真である間』が決める＝本数では決めない）")
        else:
            if "state" in pre:
                _fail("G5", f"材料の前処理 {pre['op']} に state は書けない（本数 n で窓を決める形）")
            if not isinstance(pre.get("n"), int) or isinstance(pre.get("n"), bool) or pre["n"] < 2:
                _fail("G5", f"材料の前処理の本数が不正: {pre.get('n')!r}（2 以上の整数）")
    # ★種別の鍵は1つだけ（97番の設計 v3 やること3(g)・監査 cp7b 新1・2026-08-25）。
    #   直す前は上から順に見る（legacy_col → geo → state → time → family）だけで、2つ書いても止まらず、
    #   出口の実行（_exit_fire_ok）は state を先に見ていた＝検査は「列」・実行は「玉の状態」の黙って別物。
    #   種別を決める規則は、この関数の1か所だけにする（実行の側は別の規則を持たない）。
    #   ★例外＝legacy_col の材料には family を添えてよい。恒等レシピ3本（recipes/identity_*_legacy.json）に
    #     8か所 在る既存の書き方で、family は注記ではなく系統の判定（gen の _lineage_of・下の G3）が読む鍵。
    #     設計書 v3 やること3(g) の文「5つの鍵が2つ以上なら拒否」からの差＝実装の記録 §9 に書いた（2026-08-25）。
    _excl = [k for k in ("legacy_col", "geo", "state", "time") if k in m]
    if len(_excl) >= 2:
        _fail("G6", f"材料の種別の鍵が2つ以上 在る {_excl}（種別は1つだけ書く）: {m}")
    if "family" in m and _excl and _excl != ["legacy_col"]:
        _fail("G6", f"材料の種別の鍵が2つ以上 在る {_excl + ['family']}（family を添えてよいのは legacy_col だけ）: {m}")
    if "legacy_col" in m:
        if lane != "legacy":
            _fail("G6", f"legacy 材料列は恒等検収レーン専用（探索は生成できない・§2.4-④）: {m['legacy_col']}")
        return "legacy_col", str(m["legacy_col"])
    if "geo" in m:
        g = m["geo"]
        if g not in iref.RANGE_GEO_REF:
            _fail("G6", f"レンジ幾何に未登録の列: {g}（登録済み＝{list(iref.RANGE_GEO_REF)}）")
        return "geo", g
    if "state" in m:
        s = m["state"]
        if s not in iref.STATE_COLS:
            _fail("G6", f"ポジション状態列に無い名前: {s}（使えるのは {iref.STATE_COLS}）")
        return "state", s
    if "time" in m:
        t = m["time"]
        if t not in iref.TIME_REF:
            _fail("G6", f"時間帯の材料に無い名前: {t}")
        return "time", t
    fam, tf = m.get("family"), m.get("tf")
    if not fam or not tf:
        _fail("G6", f"材料の2軸（family×tf）が欠けている: {m}（数字は family によって 0〜3 個）")
    name = build_name(m)                      # 数字の個数の検査も build_name の中でやる（G6）
    ent, _p = iref.find(name)
    if ent is None:
        _fail("G6", f"カタログに無い材料: {name}（indicator_reference_diag に未登録）")
    if ent["family"] != fam:
        _fail("G6", f"材料の family がカタログと食い違う: {fam} → {name} は {ent['family']}")
    if lane != "legacy":
        _check_param_range(fam, m.get("param"))
    return "col", f"{name}__{tf}"


_INT_RANGE_MEMO = None


def _check_int_range(n, where: str) -> None:
    """★2026-08-13（段A の A-5）＝使い方の中の本数が「探せる範囲」の中かを見る（fail-closed）。

    範囲の正本＝`engine_tuner_gen.int_range_of`（`recipes/search_limits.json` の `int_range`）。
    ★恒等検収のレーン（lane="legacy"）は対象外＝**過去の実装の書き写しには範囲の外の本数が実際に在る**
      （実測 2026-08-13＝`identity_l1_legacy.json` と `identity_s1_legacy.json` に 240本、
        `identity_s2_legacy.json` に 30本）。これを止めると恒等検収が壊れる。
    ★循環 import を避けるため、呼ばれた時に読む。
    """
    global _INT_RANGE_MEMO
    if _INT_RANGE_MEMO is None:                  # 設定ファイルは1回だけ読む（条件ごとに読むと遅い）
        import engine_tuner_gen as _gen
        lm, _w = _gen.load_limits()
        _INT_RANGE_MEMO = _gen.int_range_of(lm)
    lo, hi = _INT_RANGE_MEMO
    if not (lo <= int(n) <= hi):
        _fail("G5", f"{where}: 本数 {n} が探せる範囲の外（{lo}〜{hi}・recipes/search_limits.json の int_range）")


def _check_param_range(fam: str, param) -> None:
    """★2026-08-13（段A の A-4）＝パラメータが「その指標の範囲」の中かを見る（fail-closed）。

    範囲の正本＝`engine_tuner_gen.material_ranges`（材料カタログ由来の範囲＋まこさんが決めた範囲）。
    ★これが無いと、生成器の側だけを直しても、手で書いたレシピが範囲の外の数字で走ってしまう。
    ★恒等検収のレーン（lane="legacy"）は対象外＝過去の実装の書き写しを壊さない。
    ★循環 import を避けるため、呼ばれた時に読む（生成器は実行器を import している）。
    """
    import engine_tuner_gen as _gen
    ok, why = _gen.param_in_range(fam, param)
    if not ok:
        _fail("G6", f"材料のパラメータが範囲の外: {why}")


_NUM_RANGE_LIMITS = None


def _check_num_range(key: str, v, where: str) -> None:
    """★2026-08-15（段A の A-5-2）＝出口の枝などの数字が「探せる範囲」の中かを見る（fail-closed）。

    範囲の正本＝`engine_tuner_gen.num_range_of`（`recipes/search_limits.json` の `*_range`）。
    ★これが無いと、生成器の側だけを直しても、手で書いたレシピが範囲の外の数字で走ってしまう。
    ★恒等検収のレーン（lane="legacy"）は対象外＝過去の実装の書き写しを壊さない
      （`_check_param_range`・`_check_int_range` と同じ扱い）。
    ★いま当てているのは2件だけです（正直に書く）。
      ①玉の積み増しの回数（`position.max_adds`）②時刻の閾値（材料が「時刻」のときの value.n）。
      出口の枝の中の数字（手数料床の倍数・部分利確の割合・ピークからの戻し ほか）は、
      レシピの中で別の形に変わって入る（例＝倍数は {"const": "SCALP_FLOOR", "mult": 1.2}）ので、
      ここでは見ていません。＝**生成器は範囲から引くが、手で書いたレシピの出口の枝は機械が止めません。**
    """
    global _NUM_RANGE_LIMITS
    if _NUM_RANGE_LIMITS is None:                # 設定ファイルは1回だけ読む（条件ごとに読むと遅い）
        import engine_tuner_gen as _gen0
        _NUM_RANGE_LIMITS, _w0 = _gen0.load_limits()
    import engine_tuner_gen as _gen
    ok, why = _gen.num_in_range(_NUM_RANGE_LIMITS, key, v)
    if not ok:
        _fail("G5", f"{where}: {why}")


_Q_RANGE_LIMITS = None


def _check_q_range(q, where: str) -> None:
    """★2026-08-15（段A の A-5-3）＝分位（閾値の段）が「探せる範囲」の中かを見る（fail-closed）。

    範囲の正本＝`engine_tuner_gen.q_range_of`（`recipes/search_limits.json` の `quantile_range`）。
    ★これが無いと、生成器の側だけを直しても、手で書いたレシピが範囲の外の分位で走ってしまう。
    ★恒等検収のレーン（lane="legacy"）は対象外＝過去の実装の書き写しを壊さない
      （`_check_int_range`・`_check_num_range`・`_check_param_range` と同じ扱い）。
    ★循環 import を避けるため、呼ばれた時に読む。
    """
    global _Q_RANGE_LIMITS
    if _Q_RANGE_LIMITS is None:                  # 設定ファイルは1回だけ読む
        import engine_tuner_gen as _gen0
        _Q_RANGE_LIMITS, _w0 = _gen0.load_limits()
    import engine_tuner_gen as _gen
    ok, why = _gen.q_in_range(_Q_RANGE_LIMITS, q)
    if not ok:
        _fail("G5", f"{where}: {why}")


def _material_family(m: dict) -> str:
    """系統マップ（G3）に使う family 名。"""
    if "geo" in m:
        return "レンジ幾何"
    if "time" in m:
        return m["time"]
    if "legacy_col" in m:
        return m.get("family", "レンジ幾何" if m["legacy_col"] in GEO_COLS else "legacy")
    return m.get("family", "?")


def _check_value(v: dict, lane: str, cond_desc: str, legacy_used: list):
    """値の4区分（設計書 §2.4）＝分位・名前つき定数・整数グリッド・legacy。生の数字は拒否（G6）。
    lo/hi（band 系の下限・上限＝§2.2）と th（slope 系の閾値）は入れ子の値＝再帰で同じ検査を通す（歩4 拡張）。"""
    if not isinstance(v, dict):
        _fail("G6", f"{cond_desc}: 値が dict でない（生の数字の閾値は禁止・§2.4）: {v!r}")
    known = {"threshold_q", "const", "mult", "side_sign", "n", "legacy", "direction", "dir", "na", "offset",
             "lo", "hi", "th", "m", "op",     # op＝材料2本の組み方（PAIR_OPS・2026-08-12・段C の C-6）
             "ref", "clip_lo", "clip_hi"}     # ★連動する閾値（M2-2-5・2026-08-21）
    bad = set(v) - known
    if bad:
        _fail("G6", f"{cond_desc}: 値に未知のフィールド {sorted(bad)}（生の数字の閾値の混入経路＝拒否）")
    # ══ 他の材料に連動する閾値（M2-2-5・2026-08-21 まこさん承認 24a453d6…・法則 R1／実例の3番）══
    #   ★何を書けるようになるか＝「価格帯 clamp(0.5×ATR%_1h, 0.15%, 0.6%)」のような、
    #     1バーごとに動く閾値。直す前の4区分（分位・名前つき定数・整数グリッド・恒等検収専用）は
    #     4つとも「その場で数字1つに決まる」形だった。
    #   ★H6（値段の絶対値を使わない）の守り＝連動先に使えるのは比率の列だけ。
    #     価格そのものの列（帯の4隅）と、玉の状態の列は拒否する（下）。
    if "ref" in v:
        if "legacy" in v:
            _fail("G6", f"{cond_desc}: 連動する閾値（ref）と legacy は一緒に書けない")
        kind_r, name_r = _material_name(v["ref"], lane)
        if kind_r == "geo" and iref.RANGE_GEO_REF[name_r]["kind"] != "ratio":
            _fail("G6", f"{cond_desc}: 連動する閾値の材料に、価格水準のレンジ幾何列 {name_r} は使えない（H6）")
        if kind_r == "state":
            _fail("G6", f"{cond_desc}: 連動する閾値の材料に、ポジション状態列 {name_r} は使えない"
                        "（入口では建玉が無い）")
        if lane != "legacy":
            _check_num_range("ref_mult_range", float(v.get("mult", 1.0)), f"{cond_desc}: 連動する閾値の係数")
        for sub in ("clip_lo", "clip_hi"):
            if sub in v:
                _check_value(v[sub], lane, f"{cond_desc}/{sub}", legacy_used)
    elif "clip_lo" in v or "clip_hi" in v:
        _fail("G5", f"{cond_desc}: clip_lo／clip_hi は連動する閾値（ref）と一緒にだけ書ける")
    if "legacy" in v and lane != "legacy":
        _fail("G6", f"{cond_desc}: legacy 値は恒等検収レーン専用（探索は生成できない・§2.4-④）")
    if "legacy" in v:
        legacy_used.append(f"{cond_desc}: legacy={v['legacy']}")
    if "const" in v and v["const"] not in iref.CONST_REGISTRY:
        _fail("G6", f"{cond_desc}: 名前つき定数レジストリに無い定数: {v['const']}")
    # ★2026-08-15（段A の A-5-3）＝分位が探せる範囲の中かを見る（恒等検収のレーンは対象外）。
    if "threshold_q" in v and lane != "legacy":
        _check_q_range(v["threshold_q"], f"{cond_desc}: 閾値の段")
    # ★2026-08-15（段A の A-5-4）＝ずらす本数が探せる範囲の中かを見る（恒等検収のレーンは対象外）。
    #   直す前は `offset` を「知っている鍵」として通すだけで、値を1つも見ていなかった
    #   ＝生成器の側だけを直しても、手で書いたレシピが範囲の外の本数で走ってしまう。
    if "offset" in v and lane != "legacy":
        if not isinstance(v["offset"], int) or isinstance(v["offset"], bool):
            _fail("G5", f"{cond_desc}: ずらす本数が整数でない: {v['offset']!r}")
        _check_num_range("nest_offset_range", v["offset"], f"{cond_desc}: ずらす本数")
    if "n" in v and (not isinstance(v["n"], int) or v["n"] < 1):
        _fail("G5", f"{cond_desc}: 整数グリッドの n が不正: {v['n']}")
    if "m" in v and (not isinstance(v["m"], int) or v["m"] < 1):
        _fail("G5", f"{cond_desc}: 整数グリッドの m が不正: {v['m']}")
    for sub in ("lo", "hi", "th"):
        if sub in v:
            _check_value(v[sub], lane, f"{cond_desc}/{sub}", legacy_used)


def _check_hysteresis(c: dict, lane: str, where: str, legacy_used: list,
                      in_nest: bool, in_build: bool) -> None:
    """状態を保つ形の検査（M2-2-5・2026-08-21 まこさん承認 24a453d6…・法則 U10・C6・C7）。

    形＝{"form":"hysteresis", "on": <条件または木>, "off": <条件または木>, "value": {"n": 本数}}
      on  … この条件が成立したバーから、真になる
      off … この条件が成立したバーで、偽に戻る
      どちらも成立しないバー … 前のバーの値を保つ（＝状態を保つ）
      value.n … 真を保てる最大の本数。ここを超えたら自動で偽に戻る（＝C7 の「続く長さ」＝範囲で探す）
    ★入る線と出る線を別にできる＝on と off に別の閾値を書ける（C6 の②）。
      既存の streak（何本 続いたら成立＝C6 の①）とは別物。混ぜない。
    ★内側に引き金を置けない＝縁で発火する形ではないため（否定と同じ理由・C5）。
    """
    if in_nest:
        _fail("G5", f"{where}: 状態を保つ形（hysteresis）は入れ子の内側に置けない"
                    "（入れ子の内側は単純形のみ・設計書 §2.2）")
    extra = set(c) - {"form", "on", "off", "value", "role"}
    if extra:
        _fail("G5", f"{where}: hysteresis に未知のフィールド {sorted(extra)}"
                    "（書けるのは on・off・value・role）")
    for slot in ("on", "off"):
        if not isinstance(c.get(slot), dict) or not c[slot]:
            _fail("G5", f"{where}: hysteresis に {slot} が無い"
                        "（入る条件 on と 出る条件 off を、別々に書く）")
    v = c.get("value") or {}
    if set(v) - {"n"}:
        _fail("G5", f"{where}: hysteresis の value に書けるのは n だけ（{sorted(set(v) - {'n'})}）")
    n = v.get("n")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        _fail("G5", f"{where}: hysteresis の value.n（真を保てる最大の本数）が 1以上の整数でない: {n!r}")
    if lane != "legacy":
        _check_num_range("state_hold_bars_range", n, f"{where}: 真を保てる最大の本数")
    for slot in ("on", "off"):
        node = c[slot]
        if in_build:
            _walk_build_tree(node, lane, f"{where}/{slot}", legacy_used)   # build の中は bool_col も可
        else:
            inner, _d = _walk(node)
            for ic in inner:
                if ic.get("role") == "trigger":
                    _fail("G1", f"{where}/{slot}: 引き金を状態を保つ形の中に置けない"
                                "＝この形は縁で発火するものではなく、状態が続いているかを表すため"
                                "（否定の中に置けないのと同じ理由）")
                _check_cond(ic, lane, f"{where}/{slot}", legacy_used)


def _has_ref(v) -> bool:
    """value の中（lo・hi・th の入れ子を含む）に連動する閾値 ref が在るか。"""
    if isinstance(v, dict):
        return "ref" in v or any(_has_ref(x) for x in v.values())
    return False


def _check_exit_fire_cond(c: dict, lane: str, where: str) -> None:
    """出口の発火条件（fire）だけに掛ける検査（97番の設計 v3 やること3・全部 fail-closed・2026-08-25）。

    なぜ要るか＝直す前は形の書式（_check_cond）しか見ておらず、実行（_exit_fire_ok）は形を見なかった。
    出口でも形を見るようにした先で「検査が通す × 実行が黙って別物」が残らないよう、出口で使える形と
    材料の組み合わせをここで閉じる（監査 cp7・cp7b が直呼びで実測した5件＝strict・状態の pre・ref・
    混在・種別の鍵の二重、に当たるもの）。拒否コード＝形・側・値の書式は G5／材料の種別は G6。
      (a) 指標の条件の形は性質表 exit_ok の形だけ【G5】
      (b) 玉の状態の条件は形 level だけ・値は n／const／legacy だけ（分位・ref は解決表を持たない）【G6】
      (c) needs_side の形（level 以外）で side が strict なら拒否＝入口の評価器 _eval_cond の3行が strict を
          逆向きに評価する（next_step §6 の101番）が直るまで。外す判断は まこさん【G5】
      (d) 玉の状態の材料に pre・pre_ok=False の形の材料に pre は拒否（性質表 pre_ok を検査に接続）【G6】
      (e) value に ref（連動する閾値）は拒否＝出口の枝では使えない（_vnum_q の決まりの前倒し）【G5】
      (f) 玉の状態の材料と指標の材料を1つの条件に混ぜない【G6】
      (g) 種別の鍵が2つ以上＝_material_name が入口・出口とも拒否【G6】
      (h) candle_dir に材料は書けない（黙って捨てない）【G5】
    """
    form = c.get("form")
    mats = c.get("material") or []
    v = c.get("value") or {}
    if form == "candle_dir":
        if mats:
            _fail("G5", f"{where}: 形 candle_dir に材料は書けない（ローソクそのものを見る形・材料は黙って捨てない）: {mats}")
        return
    kinds = [_material_name(m, lane)[0] for m in mats]
    if "state" in kinds and any(k != "state" for k in kinds):
        _fail("G6", f"{where}: 玉の状態の材料と指標の材料を1つの条件に混ぜられない"
                    f"（玉の状態は指標と組み合わせて評価できない）: {kinds}")
    if kinds and all(k == "state" for k in kinds):
        if form != "level":
            _fail("G6", f"{where}: 玉の状態の条件は形 level だけ（{form} は列の形＝玉ごとの値には掛けられない）")
        if "threshold_q" in v or _has_ref(v):
            _fail("G6", f"{where}: 玉の状態の条件の値に分位（threshold_q）・連動する閾値（ref）は書けない"
                        f"（玉の状態は分位の解決表を持たない・値は n／const／legacy）: {v}")
        if not any(k in v for k in ("n", "const", "legacy")):
            _fail("G6", f"{where}: 玉の状態の条件の値は n／const／legacy のどれかが要る: {v}")
        for m in mats:
            if _pre_of(m) is not None:
                _fail("G6", f"{where}: 玉の状態の材料に前処理（pre）は掛けられない（実行が黙って無視する形を残さない）: {m}")
        return
    if form not in forms_where("exit_ok"):
        _fail("G5", f"{where}: 形 {form} は出口の発火条件で使えない（使えるのは {forms_where('exit_ok')}＝性質表 exit_ok）")
    if form in forms_where("needs_side") and form != "level" and c.get("side") in ("above_strict", "below_strict"):
        _fail("G5", f"{where}: 形 {form} の向き {c.get('side')}（strict）は出口で使えない"
                    "（評価器がこの3形の strict を逆向きに評価する＝next_step §6 の101番が直るまで拒否）")
    if not FORM_SPEC[form]["pre_ok"]:
        for m in mats:
            if _pre_of(m) is not None:
                _fail("G6", f"{where}: 形 {form} の材料に前処理（pre）は掛けられない（性質表 pre_ok＝level・band・band_exclude だけ）: {m}")
    if _has_ref(v):
        _fail("G5", f"{where}: 出口の発火条件の値に連動する閾値（ref）は書けない（出口の枝では使えない）: {v}")


def _check_cond(c: dict, lane: str, where: str, legacy_used: list, in_nest=False, in_build=False):
    """条件1つ＝役割・形・材料・側・値（設計書 §2）の検査。"""
    form = c.get("form")
    if form not in FORMS:
        _fail("G6", f"{where}: 対応表に無い形: {form}")
    if form == "hysteresis":                          # ★状態を保つ形（M2-2-5）＝材料を直接は取らない
        _check_hysteresis(c, lane, where, legacy_used, in_nest, in_build)
        return
    # ★2026-08-13（段A の A-5）＝「使い方の中の本数」が探せる範囲の中かを見る。
    #   当てる形を限る＝value.n は形によって意味が違う（下の形は本数だが、出口の枝の hold_min は「分」）。
    #   本数＝連続・以内・何本前（入れ子の形）／傾き（slope・slope_avg）の遡る本数と平均の本数。
    if lane != "legacy" and (form in NEST_FORMS or form in forms_where("slope_n")):
        _v5 = c.get("value") or {}
        for _k5 in ("n", "m"):
            if isinstance(_v5.get(_k5), int):
                _check_int_range(_v5[_k5], f"{where}: {_k5}")
    if form in NEST_FORMS:
        if in_nest:
            _fail("G5", f"{where}: 入れ子は1段まで（{form} の中に入れ子形）")
        inner = c.get("inner")
        if not _is_cond(inner):
            _fail("G5", f"{where}: {form} の内側の条件が無い")
        if inner.get("form") in NEST_FORMS:
            _fail("G5", f"{where}: {form} の内側は単純形のみ（設計書 §2.2）")
        n = (c.get("value") or {}).get("n")
        if form == "barssince":
            # ★何本前に成立したか（2026-08-12・段C の C-6）＝数えた本数を閾値と比べる形なので side が要る。
            #   value.n の意味は「閾値の本数」（streak・within_n の窓の本数とは別）。
            #   n==1 の禁止（正規形・CP3 提案7）は当てない＝barssince ≤ 1 は「いま か 1本前に成立」で、
            #   素の条件（いま成立）とは違うため（within_n(n=2) と同じもの）。
            if c.get("side") not in SIDES:
                _fail("G5", f"{where}: 形 barssince に side（{'/'.join(SIDES)}）が無い")
        elif n == 1:
            _fail("G5", f"{where}: {form}(N=1) は素の条件と同値＝生成禁止（正規形・CP3 提案7）")
        _check_value(c.get("value", {}), lane, f"{where}/{form}", legacy_used)
        _check_cond(inner, lane, f"{where}/{form}の内側", legacy_used, in_nest=True)
        return
    if form in forms_where("needs_side") and c.get("side") not in SIDES:
        _fail("G5", f"{where}: 形 {form} に side（{'/'.join(SIDES)}）が無い")
    if form == "cross" and (c.get("value") or {}).get("direction") not in ("up", "down"):
        _fail("G5", f"{where}: cross に向き（up/down）が無い")
    if form in forms_where("band"):
        vv = c.get("value") or {}
        if "lo" not in vv or "hi" not in vv:
            _fail("G5", f"{where}: 形 {form} は value.lo と value.hi（下限・上限）が要る（§2.2）")
    if form == "slope" and not isinstance((c.get("value") or {}).get("n"), int):
        _fail("G5", f"{where}: 形 slope は value.n（遡る本数＝整数グリッド）が要る（§2.2）")
    if form == "slope_avg":
        vv = c.get("value") or {}
        if not isinstance(vv.get("n"), int) or not isinstance(vv.get("m"), int):
            _fail("G5", f"{where}: 形 slope_avg は value.n（遡る本数）と value.m（平均の本数）が要る（§2.2）")
    # ★材料2本の組み方（部品 div・corr・2026-08-12・段C の C-6）＝正本は PAIR_OPS（上のブロック）。
    #   書いていなければ引き算（sub）＝2026-08-12 より前と同じ意味になる（既に在るレシピを壊さない）。
    if form == "diff":
        vv = c.get("value") or {}
        op = _pair_op_of(vv)
        if op not in PAIR_OPS:
            _fail("G6", f"{where}: 材料2本の組み方に無い部品: {op}"
                        f"（使えるのは {pair_ops()}／正本＝condition_parts.json）")
        if op != "sub" and "th" not in vv:
            _fail("G5", f"{where}: 形 diff の組み方 {op} は value.th（閾値）が要る"
                        "（引き算だけが value 自体を閾値にする書き方＝2026-08-12 より前の形）")
        if PAIR_OPS[op]["needs_n"] and not isinstance(vv.get("n"), int):
            _fail("G5", f"{where}: 形 diff の組み方 {op} は value.n（窓の本数＝整数）が要る（§2.2 slope と同じ書き方）")
    mats = c.get("material") or []
    # ★2026-08-15（段A の A-5-2）＝時刻の閾値が「探せる範囲」の中かを見る（fail-closed）。
    #   範囲の正本＝recipes/search_limits.json の hour_range（直す前は 6・12・18 の3つだけだった）。
    #   当てるのは材料が「時刻」のときだけ＝曜日など別の時間帯の材料には当てない（意味が違うため）。
    if lane != "legacy" and any(m.get("time") == "時刻" for m in mats):
        _v52 = c.get("value") or {}
        if isinstance(_v52.get("n"), int):
            _check_num_range("hour_range", _v52["n"], f"{where}: 時刻の閾値")
        for _s52 in ("lo", "hi", "th"):
            _in52 = _v52.get(_s52)
            if isinstance(_in52, dict) and isinstance(_in52.get("n"), int):
                _check_num_range("hour_range", _in52["n"], f"{where}: 時刻の閾値（{_s52}）")
    # ★2026-08-13（段C の C-6・部品①＝閾値とのクロス cross_val）＝cross は2通りの書き方を受ける。
    #   ①列2本（MACD線% × MACDシグナル線% のようなクロス）
    #   ②列1本 ＋ 閾値（「RSI が 70 を上抜けた」）★これが 2026-08-13 まで書けなかった
    #   閾値の書き方は level と同じ value（分位・名前つき定数・整数グリッド）を value.th に入れる形。
    #   出どころ＝.claude/ratchet/condition_parts.json の部品 cross_val（業界の同じもの＝pandas-ta の
    #   cross_value）。生の数字は _check_value が従来どおり拒否する（G6）。
    if form == "cross" and len(mats) == 1 and "th" not in (c.get("value") or {}):
        _fail("G5", f"{where}: 列1本の cross は value.th（閾値）が要る"
                    "（閾値とのクロス＝『RSI が 70 を上抜けた』・部品 cross_val）")
    need2 = form in forms_pair_in("2") or (form == "cross" and len(mats) != 1)
    if need2 and len(mats) != 2:
        _fail("G6", f"{where}: 形 {form} は列2本の材料が要る（{len(mats)}本）"
                    + ("／閾値とのクロスなら列1本＋value.th" if form == "cross" else ""))
    if form == "candle_dir":
        mats = []                                 # ローソク列＝バーそのもの（材料指定なし）
    elif not need2 and len(mats) != 1:
        _fail("G6", f"{where}: 形 {form} は列1本の材料（{len(mats)}本）")
    # ★列2本の形（クロス・差・タッチ）には、単位の変わる前処理は使わせない（2026-08-12（18回目）・段C の 4-2）。
    #   理由＝単位が違うものを大小で比べても意味が無い（RSI 0〜100 と 順位 0〜1）。一覧＝MATERIAL_PRE。
    if form in forms_pair_in("2", "2or1th") and len(mats) == 2:
        for m in mats:
            p = _pre_of(m)
            # ★一覧に無い部品名・不正な本数は、この下の _material_name が拒否する（ここでは見ない）。
            if p and MATERIAL_PRE.get(p.get("op"), {}).get("same_unit") is False:
                _fail("G5", f"{where}: 列2本の形 {form} に、単位の変わる前処理 {p['op']} は使えない"
                            f"（使えるのは {pre_ops(same_unit=True)}／{p['op']} は水準 level・band で使う）")
    # ★前処理（pre）を掛けた材料にも分位（threshold_q）を使える（2026-08-12（18回目）・段C の 4-2）。
    #   2026-08-13 はここで拒否していた（fail-closed）＝分位の解決表（engine_tuner_gen.build_qtable）が
    #   前処理を見ずに素の列の分布から閾値を作っていて、許すと嘘の閾値になったため。
    #   いまは解決表が列を読んだあとに実行器の _apply_pre を掛けてから分位を出す（鍵も _mat_key が
    #   前処理込みで分ける）ので、拒否を外した。番人＝engine_tuner_gen の T1-C6c ③。
    for m in mats:
        kind, name = _material_name(m, lane)
        if kind == "geo" and iref.RANGE_GEO_REF[name]["kind"] != "ratio":
            _fail("G6", f"{where}: 価格水準のレンジ幾何列 {name} は条件の材料に使えない"
                        f"（placement の幾何参照専用・H6）")
        if kind == "state" and not where.startswith("exit"):
            _fail("G6", f"{where}: ポジション状態列 {name} は出口 fire の材料専用（入口では建玉が無い）")
    _check_value(c.get("value", {}), lane, where, legacy_used)


# ══ 相場の宣言（監査 4-19／要件 R5・2026-08-03 新設）══════════════════════════════════
#   それまで、この実行器のコードには レンジ判定の列の名前 range_ok_rg5 が3か所に直接書いてあった
#   （875行・1052行・1614行）。だから engine_tuner はレンジ以外の相場を扱えなかった。
#   いまは レシピの meta.regime が列の名前を持つ。実行器は そこに書いてある名前の列を見る。
#   meta.regime の形（辞書）:
#     name       … 相場の名前（一覧の正本＝cat_requirements.md §1.2.1・写し＝tuner_adapters.REGIME_NAMES）
#     entry_col  … このバーだけ玉を建ててよい、を表す列の名前
#     block_col  … このバーでは新規の発注を止める、を表す列の名前（要らなければ null）
#   ⚠️ 名前を downtrend にしても下げ相場は扱えない。判定の列そのものが要る（実行時に列の有無を検査する）。
def _check_bool_cond(c: dict, where: str) -> None:
    """build 専用の形 bool_col＝真偽の列の参照（M2-1-4 の決めごと3・2026-08-20 まこさん承認）。

    ★bool_col は build（判定の中身）の中だけで使える。入口の条件の木（_walk）は form の無い
      辞書を拒否するので、入口に書くと従来どおり G5 で止まる＝場面の判定はふるい（C5）を保つ。
    ★列が実データに在るかは、ここでは見られない（データがまだ無い）＝実行時に fail-closed で
      止める（_regime_series と同じ思想・実装は M2-1-6）。
    """
    extra = set(c) - {"bool_col", "want"}
    if extra:
        _fail("G5", f"{where}: bool_col に未知のフィールド {sorted(extra)}")
    if not c.get("bool_col") or not isinstance(c["bool_col"], str):
        _fail("G5", f"{where}: bool_col の列の名前が文字列でない: {c.get('bool_col')!r}")
    if not isinstance(c.get("want"), bool):
        _fail("G5", f"{where}: bool_col の want が true/false でない: {c.get('want')!r}")


def _walk_build_tree(node, lane: str, where: str, legacy_used: list, depth: int = 0,
                     in_not: bool = False) -> None:
    """build の木を検査する（M2-1-5・2026-08-20 まこさん承認）。

    入口の木（_walk）との違い＝bool_col を条件として受けること だけ。
    普通の条件は入口と同じ _check_cond に通す＝G5/G6・分位の範囲検査（_check_q_range）が
    そのまま掛かる＝束の中の閾値（threshold_q）は engine_tuner の探索の対象になる（決めごと2）。
    ★2026-08-21（M2-2-5）＝否定（not）を足した。入口の木と同じ形・同じ禁止（二重の否定は不可）。
    """
    if isinstance(node, dict) and "bool_col" in node:
        _check_bool_cond(node, where)
        return
    if _is_cond(node):
        _check_cond(node, lane, where, legacy_used, in_build=True)   # ★build の中＝内側に bool_col も可
        return
    if isinstance(node, dict) and "not" in node:
        _check_not_node(node, in_not, where)
        _walk_build_tree(node["not"], lane, f"{where}/not", legacy_used, depth + 1, in_not=True)
        return
    if isinstance(node, dict) and ("all" in node or "any" in node):
        kids = node.get("all", node.get("any", []))
        if not isinstance(kids, list) or not kids:
            _fail("G5", f"{where}: build の all/any の中身が空")
        for ch in kids:
            _walk_build_tree(ch, lane, where, legacy_used, depth + 1, in_not)
        return
    if isinstance(node, dict) and "if" in node and "then" in node:
        _walk_build_tree(node["if"], lane, where, legacy_used, depth + 1, in_not)
        _walk_build_tree(node["then"], lane, where, legacy_used, depth + 1, in_not)
        return
    _fail("G5", f"{where}: build の木のノードが bool_col/条件/not/all/any/if-then のどれでもない: "
                f"{sorted(node) if isinstance(node, dict) else node!r}")


# ══ G7 場面ごとの相場の法則（M2-B0・2026-08-30 まこさん承認 iter="m2-b0-law-reader-20260830"）══════
#   正本＝.claude/ratchet/regime_laws.json の「機械が読む判定」を持つ相場の法則（C1・C4・C6・R1・R7・R8・S1）。
#   ★判定はファイルから読む＝コードに直書きしない。法則を1件 書き替えると、この審査はそのとおり変わる
#     （直す前は K-1〜K-7 としてここに直書き＝法則のファイルを直しても動きが変わらなかった）。
#   照合の対象＝meta.regime.build を持つレシピの entry の木だけ。
#     ・build の無いレシピ（列名の宣言だけ＝いまの E38 の全レシピ・後方互換）には掛けない＝既存を壊さない。
#     ・恒等検収レーン（lane="legacy"）には掛けない＝RG-v5 の写しは生成物ではない（G6 の legacy と同じ思想）。
#     ・block の木には掛けない＝block は補助の止める列で、場面の判定そのものは entry が持つ。
#   ★数字は1つも持たない＝閾値・本数の上限・保つ長さは既存の範囲検査（G5/G6）が見る。
#   語彙＝「向きを持たない部品」の一覧だけ、型の表（signal_families.json の bans）から引く（部品そのものの
#     性質で、法則ごとに変わらないため）。幅・比の一覧は法則の側（R7・S1 の「機械が読む判定」）に在る。

_SCENE_DIRLESS = None                   # 向きを持たない部品の一覧（型の表の bans・遅延で1回だけ読む）


def _dirless_parts() -> set:
    """向きを持たない部品の一覧（型の表 signal_families.json の bans が正本＝2026-08-06 の全種実測・まこさん OK）。"""
    global _SCENE_DIRLESS
    if _SCENE_DIRLESS is None:
        import gen_signal_families as gsf
        t = json.loads(gsf.OUT_JSON.read_text(encoding="utf-8"))
        out = set()
        for key in ("direction_note", "direction_stateful"):
            out.update((t.get("bans") or {}).get(key, {}).get("parts") or [])
        _SCENE_DIRLESS = out
    return _SCENE_DIRLESS


LAWS_PATH = HERE.parent.parent / ".claude" / "ratchet" / "regime_laws.json"
_REGIME_LAWS = None                     # 読んだ法則の覚え（既定の読み込みだけ覚える）
_LAW_SCENES = ("range", "uptrend", "downtrend", "spike")
# ★M2-B-2b（2026-08-30・まこさん承認 iter="m2-b-2b-range-laws-20260830"）＝型を1つ・形を1つ・鍵を3つ 広げた。
#   型「系統を重ねない」（R2）／形 streak（R4）／鍵「側」（R5・R6・R7＝on 側の部品だけを数える）・
#   「かつ」（R3＝同じ1本で系統と時間足を満たす）・「性質」（R10＝REFS の prop を読む）。
#   「判定の置き場」（R9）＝判定を持たない法則が、どこで持つかを書く欄（load_regime_laws が数える）。
_LAW_TYPES = ("部品を数える", "形を持つ", "系統を重ねない")
_LAW_FORMS = ("hysteresis", "not", "streak")
_LAW_PICK_KEYS = ("向きを持つ", "時間足", "系統", "family", "geo", "側", "かつ", "性質")
_LAW_SIDES = ("above", "below")
_REGIME_LAW_COUNTS = None               # 読み込みの数え（審査に使う／置き場あり／持たない）
_REFS_PROP = None                       # family → REFS の prop（性質）・遅延で1回だけ作る


def _refs_prop() -> dict:
    """family → 性質（indicator_reference_diag.REFS の prop）。★一覧を手で書かない（R10 の鍵「性質」の正本）。"""
    global _REFS_PROP
    if _REFS_PROP is None:
        _REFS_PROP = {r["family"]: r.get("prop") for r in iref.REFS
                      if isinstance(r, dict) and r.get("family") and r.get("prop")}
    return _REFS_PROP


def regime_law_counts() -> dict:
    """読み込みの数え＝{審査に使う, 置き場あり, 持たない}（M2-B-2b・黙って無視しない）。"""
    load_regime_laws()
    return dict(_REGIME_LAW_COUNTS or {})


def _validate_law(no: str, j: dict) -> None:
    """「機械が読む判定」1件の形の検査（fail-closed＝知らない型・場面名・系統名は止める・設計書 §1（c））。"""
    scenes = j.get("掛かる場面")
    if not isinstance(scenes, list) or not scenes or any(s not in _LAW_SCENES for s in scenes):
        raise SystemExit(f"[相場の法則] {no}: 掛かる場面が不正: {scenes}"
                         f"（使える名前＝{list(_LAW_SCENES)}・fail-closed）")
    typ = j.get("型")
    if typ not in _LAW_TYPES:
        raise SystemExit(f"[相場の法則] {no}: 知らない型: {typ}"
                         f"（使える型＝{list(_LAW_TYPES)}・fail-closed）")
    if typ == "形を持つ":
        if j.get("形") not in _LAW_FORMS:
            raise SystemExit(f"[相場の法則] {no}: 知らない形: {j.get('形')}（使える形＝{list(_LAW_FORMS)}・fail-closed）")
        return
    kinds = {(v or {}).get("k") for v in iref.FAMILY_LINEAGE.values()}
    if typ == "系統を重ねない":                       # ★R2（M2-B-2b）＝同じ系統の部品を上限より多く入れない
        exk = j.get("除く系統")
        if not isinstance(exk, list) or any(k not in kinds for k in exk):
            raise SystemExit(f"[相場の法則] {no}: 除く系統が不正: {exk}（系統名の一覧・fail-closed）")
        lim = j.get("上限")
        if not isinstance(lim, int) or isinstance(lim, bool) or lim < 1:
            raise SystemExit(f"[相場の法則] {no}: 上限が不正: {lim}（1以上の整数・fail-closed）")
        return
    sel = j.get("数える部品")
    if not isinstance(sel, dict) or not sel or any(k not in _LAW_PICK_KEYS for k in sel):
        raise SystemExit(f"[相場の法則] {no}: 数える部品が不正: {sel}（使える鍵＝{list(_LAW_PICK_KEYS)}・fail-closed）")
    for k in (sel.get("系統") or []):
        if k not in kinds:
            raise SystemExit(f"[相場の法則] {no}: 知らない系統名: {k}（fail-closed）")
    side = sel.get("側")                              # ★R5・R6・R7（M2-B-2b）＝family／geo ごとに above か below
    if side is not None:
        fams = list(sel.get("family") or [])
        geos = [] if sel.get("geo") in (None, "any") else list(sel.get("geo") or [])
        if not isinstance(side, dict) or not side or not (fams or geos):
            raise SystemExit(f"[相場の法則] {no}: 側が不正: {side}（family か geo と一緒に、名前ごとに above／below を書く・fail-closed）")
        for f, s in side.items():
            if f not in fams and f not in geos:
                raise SystemExit(f"[相場の法則] {no}: 側の名前 {f} が family／geo の一覧に無い（fail-closed）")
            if s not in _LAW_SIDES:
                raise SystemExit(f"[相場の法則] {no}: 側の値が不正: {f}={s}（{'/'.join(_LAW_SIDES)}・fail-closed）")
    if "かつ" in sel and not isinstance(sel.get("かつ"), bool):      # ★R3（M2-B-2b）
        raise SystemExit(f"[相場の法則] {no}: かつ が真偽でない: {sel.get('かつ')!r}（fail-closed）")
    if "性質" in sel and sel.get("性質") not in set(_refs_prop().values()):   # ★R10（M2-B-2b）
        raise SystemExit(f"[相場の法則] {no}: 知らない性質: {sel.get('性質')}"
                         f"（使える値＝REFS の prop {sorted(set(_refs_prop().values()))}・fail-closed）")
    n = j.get("本数")
    if not isinstance(n, int) or isinstance(n, bool) or n < 1:
        raise SystemExit(f"[相場の法則] {no}: 本数が不正: {n}（1以上の整数・fail-closed）")


def load_regime_laws(path: pathlib.Path | None = None) -> list:
    """相場の法則の正本（regime_laws.json）から「機械が読む判定」を持つ法則を読む（M2-B0・fail-closed）。

    戻り＝[{"番号", "一文", "判定"}, ...]。「機械が読む判定」を持たない法則（R9・R10 ほか）は審査に
    使わない（黙って無視ではない＝正本の全件と戻りの件数の差で見える）。1回 読んだら覚える。
    path はテスト用＝指定したときは覚えに触らない。
    """
    global _REGIME_LAWS, _REGIME_LAW_COUNTS
    if path is None and _REGIME_LAWS is not None:
        return _REGIME_LAWS
    p = path if path is not None else LAWS_PATH
    if not p.exists():
        raise SystemExit(f"[相場の法則] {p} が無い（M2-B0・fail-closed）")
    try:
        body = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:                                     # 壊れた json も止める（fail-closed）
        raise SystemExit(f"[相場の法則] {p} が読めない: {e}（fail-closed）")
    laws = body.get("法則")
    if not isinstance(laws, list) or not laws:
        raise SystemExit(f"[相場の法則] {p} に「法則」の一覧が無い（fail-closed）")
    # ★M2-B-2b＝「判定を揃えた場面」（json の上の欄・今回＝レンジ）の法則は、「機械が読む判定」か
    #   「判定の置き場」のどちらかを必ず持つ。どちらも無ければ止まる（fail-closed・黙って無視しない）。
    ready = body.get("判定を揃えた場面") or []
    if not isinstance(ready, list) or any(not isinstance(s, str) for s in ready):
        raise SystemExit(f"[相場の法則] {p} の「判定を揃えた場面」が一覧でない: {ready!r}（fail-closed）")
    out = []
    counts = {"審査に使う": 0, "置き場あり": 0, "持たない": 0}
    for law in laws:
        if not isinstance(law, dict):
            continue
        no = str(law.get("番号"))
        if "機械が読む判定" in law:
            j = law["機械が読む判定"]
            _validate_law(no, j)
            out.append({"番号": no, "一文": str(law.get("一文") or ""), "判定": j})
            counts["審査に使う"] += 1
        elif law.get("判定の置き場"):
            if not isinstance(law["判定の置き場"], str):
                raise SystemExit(f"[相場の法則] {no}: 判定の置き場が文字でない: {law['判定の置き場']!r}（fail-closed）")
            counts["置き場あり"] += 1
        else:
            counts["持たない"] += 1
            if law.get("場面") in ready:
                raise SystemExit(f"[相場の法則] {no}: 判定を揃えた場面（{law.get('場面')}）なのに"
                                 "「機械が読む判定」も「判定の置き場」も無い（M2-B-2b・fail-closed）")
    if not out:
        raise SystemExit(f"[相場の法則] {p} に「機械が読む判定」を持つ法則が0件（fail-closed）")
    if path is None:
        _REGIME_LAWS = out
        _REGIME_LAW_COUNTS = counts
    return out


def _upper_tfs() -> set:
    """執行足（5m）より上の時間足の一覧（型の表の tfs の並びから・数字を持たない）。"""
    import engine_tuner_gen as _gen
    tfs_all = _gen.load_signal_table()["tfs"]
    base = tfs_all.index("5m")
    return {t for t in tfs_all if tfs_all.index(t) > base}


def _law_count_and(sel: dict, seen: dict) -> int:
    """「かつ」＝同じ1本の部品が、書かれた鍵を全部 満たすときだけ数える（R3・M2-B-2b）。
    family の部品＝系統・時間足・向きを持つ・family・側・性質 の全部。geo の部品＝geo の鍵（と側）で数える。
    ★数えるのは on 側の部品だけ（hysteresis の off の中は数えない）。"""
    n = 0
    up = _upper_tfs() if sel.get("時間足") == "執行足より上" else None
    side = sel.get("側") or {}
    pm = _refs_prop() if "性質" in sel else None
    for p in seen["on_parts"]:
        if p["geo"] is not None:
            g = sel.get("geo")
            if g is None or not (g == "any" or p["geo"] in g):
                continue
            if side and side.get(p["geo"]) != p["side"]:
                continue
            n += 1
            continue
        if "系統" in sel and p["kind"] not in (sel.get("系統") or []):
            continue
        if up is not None and p["tf"] not in up:
            continue
        if sel.get("向きを持つ") and (p["name"] is None or p["name"] in _dirless_parts()):
            continue
        if "family" in sel and p["fam"] not in (sel.get("family") or []):
            continue
        if side and side.get(p["fam"]) != p["side"]:
            continue
        if pm is not None and pm.get(p["fam"]) != sel["性質"]:
            continue
        n += 1
    return n


def _law_count(sel: dict, seen: dict) -> int:
    """束の中で「数える部品」の条件に合う数を数える（鍵が複数なら いずれか＝合算。「かつ」が真なら全部）。"""
    if sel.get("かつ"):
        return _law_count_and(sel, seen)
    n = 0
    if sel.get("向きを持つ"):
        n += sum(1 for pt in seen["parts"] if pt not in _dirless_parts())
    if sel.get("時間足") == "執行足より上":
        import engine_tuner_gen as _gen
        tfs_all = _gen.load_signal_table()["tfs"]
        base = tfs_all.index("5m")
        n += sum(1 for t in seen["tfs"] if t in tfs_all and tfs_all.index(t) > base)
    for k in (sel.get("系統") or []):
        n += sum(1 for f in seen["fams"] if (iref.FAMILY_LINEAGE.get(f) or {}).get("k") == k)
    fams = set(sel.get("family") or [])
    side = sel.get("側")
    if fams:
        if side:                                   # ★「側」（M2-B-2b）＝on 側の部品だけ・名前ごとの向きが合うものだけ
            n += sum(1 for p in seen["on_parts"]
                     if p["fam"] in fams and p["side"] is not None and side.get(p["fam"]) == p["side"])
        else:
            n += len(seen["fams"] & fams)
    if "性質" in sel:                              # ★「性質」（M2-B-2b・R10）＝REFS の prop が同じ family（on 側）
        pm = _refs_prop()
        n += sum(1 for p in seen["on_parts"] if p["fam"] and pm.get(p["fam"]) == sel["性質"])
    geo = sel.get("geo")
    if geo is not None and side:                   # 側つきの geo＝on 側・向きが合うものだけ
        n += sum(1 for p in seen["on_parts"]
                 if p["geo"] is not None and (geo == "any" or p["geo"] in geo)
                 and p["side"] is not None and side.get(p["geo"]) == p["side"])
    elif geo == "any":
        n += len(seen["geo"])
    elif geo:
        n += len(seen["geo"] & set(geo))
    return n


def _scene_scan(node, seen: dict, in_off: bool = False, neg: bool = False) -> None:
    """build の木から、G7 の照合に要る事実だけを集める（形の検査はしない＝_walk_build_tree が済ませている）。

    ★M2-B-2b（2026-08-30）で足した2つ＝
      ・seen["forms"]＝通った形の名前の全部（hysteresis・not・streak …）＝「形を持つ」の判定はこれを見る。
      ・seen["on_parts"]＝on 側の部品の一覧（fam／tf／geo／side／kind／name）＝「側」「かつ」「性質」「系統を重ねない」が見る。
        hysteresis の off の中の部品は入れない（組む側が off に「側を反転した写し」を置くため）。
        not の中の部品は side を反転する（not（ADX above）＝ADX below）。
    既存の集合（geo／fams／tfs／parts／not／hysteresis）は変えない＝直す前の7件の判定は同じ結果。
    """
    if not isinstance(node, dict):
        return
    if "bool_col" in node:
        return
    if "not" in node:
        seen["not"] = True
        seen["forms"].add("not")
        _scene_scan(node["not"], seen, in_off, not neg)
        return
    if "all" in node or "any" in node:
        for ch in (node.get("all") or node.get("any") or []):
            _scene_scan(ch, seen, in_off, neg)
        return
    if "if" in node and "then" in node:
        _scene_scan(node["if"], seen, in_off, neg)
        _scene_scan(node["then"], seen, in_off, neg)
        return
    if node.get("form") == "hysteresis":
        seen["hysteresis"] = True
        seen["forms"].add("hysteresis")
        _scene_scan(node.get("on"), seen, in_off, neg)
        _scene_scan(node.get("off"), seen, True, neg)
        return
    if node.get("form"):
        seen["forms"].add(str(node["form"]))
    s = node.get("side")
    side = "above" if s in ("above", "above_strict") else ("below" if s in ("below", "below_strict") else None)
    if side is not None and neg:
        side = "below" if side == "above" else "above"
    for m in (node.get("material") or []):
        if not isinstance(m, dict):
            continue
        if "geo" in m:
            seen["geo"].add(str(m["geo"]))
            if not in_off:
                seen["on_parts"].append({"fam": None, "tf": None, "geo": str(m["geo"]), "side": side,
                                         "kind": None, "name": None})
        fam = m.get("family")
        if fam:
            seen["fams"].add(str(fam))
            if m.get("tf"):
                seen["tfs"].add(str(m["tf"]))
            name = None
            try:
                name = build_name(m)
                seen["parts"].add(name)
            except SystemExit:
                pass                       # 名前が組めない材料は _walk_build_tree が既に拒否している
            if not in_off:
                seen["on_parts"].append({"fam": str(fam), "tf": str(m.get("tf") or ""), "geo": None, "side": side,
                                         "kind": (iref.FAMILY_LINEAGE.get(str(fam)) or {}).get("k"), "name": name})
    inner = node.get("inner")
    if isinstance(inner, dict):
        _scene_scan(inner, seen, in_off, neg)


def _check_scene_rules(rg: dict, lane: str) -> None:
    """G7＝場面ごとの相場の法則（正本＝regime_laws.json の「機械が読む判定」・M2-B0・2026-08-30）。"""
    if lane == "legacy":
        return
    bd = rg.get("build")
    if not isinstance(bd, dict) or not isinstance(bd.get("entry"), dict):
        return
    name = rg.get("name")
    seen = {"geo": set(), "fams": set(), "tfs": set(), "parts": set(),
            "not": False, "hysteresis": False, "forms": set(), "on_parts": []}
    _scene_scan((bd["entry"] or {}).get("tree"), seen)

    ng = []
    for law in load_regime_laws():
        j = law["判定"]
        if name not in j["掛かる場面"]:
            continue
        if j["型"] == "形を持つ":
            if j["形"] not in seen["forms"]:
                ng.append(f"{law['番号']}: {j['形']} の形が束に無い（法則 {law['番号']}＝{law['一文']}）")
        elif j["型"] == "系統を重ねない":            # ★R2（M2-B-2b）＝on 側の部品を系統ごとに数える
            from collections import Counter as _Cnt
            exk = set(j.get("除く系統") or [])
            cnt = _Cnt(p["kind"] for p in seen["on_parts"] if p["kind"] and p["kind"] not in exk)
            over = [(k, c) for k, c in sorted(cnt.items()) if c > int(j["上限"])]
            if over:
                ng.append(f"{law['番号']}: 同じ系統が重なっている＝" + "・".join(f"{k} {c}本" for k, c in over)
                          + f"（上限 {int(j['上限'])}本・除く系統＝{sorted(exk)}）（法則 {law['番号']}＝{law['一文']}）")
        else:
            got = _law_count(j["数える部品"], seen)
            if got < int(j["本数"]):
                want = "・".join(f"{k}={v}" for k, v in j["数える部品"].items())
                ng.append(f"{law['番号']}: 条件に合う部品が {got}本（{int(j['本数'])}本 要る・"
                          f"数える部品＝{want}）（法則 {law['番号']}＝{law['一文']}）")
    if ng:
        _fail("G7", f"場面ごとの相場の法則（{name}）に反する: " + " ／ ".join(ng)
                    + "（正本＝regime_laws.json の「機械が読む判定」・M2-B0 まこさん承認 2026-08-30）")


def _check_regime_meta(meta: dict, lane: str = "", legacy_used: list | None = None) -> None:
    """meta.regime の形を検査する（G5）。壊れていたらレシピを読み込まない。

    ★2026-08-20（M2-1-5・まこさん承認）＝meta.regime.build（判定の中身＝条件の束）を受け取れるように
      広げた。build は書かなくてもよい（後方互換＝entry_col・block_col の読む道はそのまま）。
      build の形＝entry（out_col＝作る列の名前・tree＝条件の束）と block（null 可・在れば同じ形）。
    """
    from tuner_adapters import REGIME_NAMES
    rg = meta.get("regime")
    if not isinstance(rg, dict):
        _fail("G5", f"meta.regime が辞書でない: {rg!r}"
                    "（形＝name・entry_col・block_col／監査 4-19 で文字列から辞書へ変えた）")
    if rg.get("name") not in REGIME_NAMES:
        _fail("G5", f"meta.regime.name が一覧に無い: {rg.get('name')!r}"
                    f"（使えるのは {', '.join(REGIME_NAMES)}／正本＝cat_requirements.md §1.2.1）")
    if not rg.get("entry_col") or not isinstance(rg.get("entry_col"), str):
        _fail("G5", "meta.regime.entry_col が無い（玉を建ててよいバーを表す列の名前が要る）")
    if rg.get("block_col") is not None and not isinstance(rg.get("block_col"), str):
        _fail("G5", f"meta.regime.block_col が文字列でない: {rg.get('block_col')!r}（要らないときは null）")
    # ── build（判定の中身・M2-1-4 の決定・2026-08-20 まこさん承認）────────────────────
    bd = rg.get("build")
    if bd is None:
        return
    legacy_used = [] if legacy_used is None else legacy_used
    if not isinstance(bd, dict):
        _fail("G5", f"meta.regime.build が辞書でない: {bd!r}（形＝entry・block）")
    extra = set(bd) - {"entry", "block"}
    if extra:
        _fail("G5", f"meta.regime.build に未知のフィールド {sorted(extra)}（形＝entry・block）")
    if bd.get("entry") is None:
        _fail("G5", "meta.regime.build.entry が無い（out_col と tree が要る・block だけの build は不可）")
    for slot in ("entry", "block"):
        one = bd.get(slot)
        if one is None:
            continue                                   # block は null 可
        if not isinstance(one, dict) or not one.get("out_col") or not isinstance(one.get("out_col"), str):
            _fail("G5", f"meta.regime.build.{slot} に out_col（作る列の名前）が無い")
        if one["out_col"] in (rg.get("entry_col"), rg.get("block_col")):
            _fail("G5", f"meta.regime.build.{slot}.out_col が宣言の列と同じ名前（上書きの防止）: {one['out_col']}")
        if "tree" not in one:
            _fail("G5", f"meta.regime.build.{slot} に tree（条件の束）が無い")
        _walk_build_tree(one["tree"], lane, f"meta.regime.build.{slot}", legacy_used)
    _check_scene_rules(rg, lane)               # G7＝場面ごとの決まり（M2-4-3・2026-08-22 まこさん承認）


def regime_cols(recipe: dict) -> tuple[str, str | None]:
    """レシピの meta.regime から、使う列の名前2つを読み取る（検査は validate_recipe が済ませている）。"""
    rg = (recipe.get("meta") or {}).get("regime") or {}
    return rg["entry_col"], rg.get("block_col")


def _regime_series(df: pd.DataFrame, recipe: dict) -> tuple[np.ndarray, np.ndarray]:
    """宣言された列を実データから読み出す。列が無ければ止める（fail-closed）。

    ★ここが「相場の名前を書いただけでは扱えない」を物理で示す場所。
      判定の列が実データに無ければ、名前が何であっても走らない。
    """
    ent, blk = regime_cols(recipe)
    if ent not in df.columns:
        name = (recipe.get("meta") or {}).get("regime", {}).get("name")
        raise RecipeError(
            f"[相場の列が無い] 宣言された相場は {name} で、玉を建ててよいバーの列は {ent} です。"
            f"しかしデータにその列がありません。判定を作る処理が要ります（engine_tuner の外側の作業）。")
    ok = df[ent].to_numpy(bool)
    if blk is None:
        up = np.zeros(len(df), dtype=bool)
    else:
        if blk not in df.columns:
            raise RecipeError(
                f"[相場の列が無い] 新規の発注を止める列 {blk} がデータにありません。")
        up = df[blk].to_numpy(bool)
    return ok, up


NO_CAP = "無制限"
# ★上限を置かない、という まこさんの決定を表す印（2026-08-12・逐語「Aはすべて上限ナシでいいのでは」）。
#   null（未確定＝まこさん待ち）と区別する。null は本走を止める（fail-closed）が、この印は止めない。
#   背景＝上限5件（k_max・role_max・count_range・depth_max・p_max）は 2026-08-01 に CC が一度に埋めた
#   たたき台で、実物と照らすと k_max と count_range の根拠が実物と食い違っていた（2026-08-12 に機械で確認）。


def cap_of(lm: dict, key: str):
    """上限を引く。戻り＝(上限の値, まこさん待ちか)。
    ★『無制限』＝上限を置かない（まこさん決定）＝待ちでない。None＝未確定＝待ち。"""
    v = lm.get(key)
    if v == NO_CAP:
        return None, False
    return v, v is None


def validate_recipe(recipe: dict, limits: dict | None = None, samples: dict | None = None) -> dict:
    """スキーマ検証器＝G1〜G6。壊れたレシピは RecipeError（読み込み拒否）。
    limits＝まこさん判断の値（n_min/k_max/depth_max/p_max/r_min/role_max/count_range）。
    未確定（None）は『値待ち』として報告し、構造の検査だけ行う（§11＝値はまこさんが決める）。
    『無制限』（NO_CAP）は上限を置かない＝その検査を飛ばす（まこさん決定 2026-08-12）。
    samples＝列ごとの補正後独立標本数（検査5 の機械出力・G2 の基礎データ）。戻り値＝機械出力の報告。"""
    lm = limits or {}
    rep = {"値待ち": [], "legacy使用": [], "経路数": 0, "条件数": 0, "系統": {}, "触れた列": []}
    lane = recipe.get("meta", {}).get("lane", "")
    meta = recipe.get("meta") or {}
    for key in ("strategy", "logic_id", "side", "regime"):
        if not meta.get(key):
            _fail("G5", f"meta.{key} が無い")
    if meta["side"] not in ("SHORT", "LONG"):
        _fail("G5", f"meta.side が不正: {meta['side']}")
    _check_regime_meta(meta, lane, rep["legacy使用"])
    # record（記録スタイル）＝過去資産の書き写しで診断列（W_entry/k_entry）の出し方を実装に合わせる指定。
    # 歩6-1（L1）で追加。net に不関与の診断列だが、md5 恒等の対象なので実装と同じ出し方が要る。
    # 恒等検収レーン専用＝探索レシピには存在しない（生成器は作らない・番人で隔離）。
    rec_style = recipe.get("record")
    if rec_style is not None:
        if lane != "legacy":
            _fail("G6", "record（記録スタイル＝W_entry/k_entry の再現指定）は恒等検収レーン専用（探索は生成できない）")
        if rec_style.get("w_entry", "range") not in ("range", "zone"):
            _fail("G5", f"record.w_entry が range/zone でない: {rec_style.get('w_entry')}")
        if rec_style.get("k_entry", "stoch") not in ("stoch", "none"):
            _fail("G5", f"record.k_entry が stoch/none でない: {rec_style.get('k_entry')}")
    ent = recipe.get("entry") or {}
    # entry 構造の拡張点（設計書 §12・CP3 提案7）＝既定 edge_trigger。歩6-1 で ceiling_resting を追加
    # （S1 の書き写し＝型別の天井に売り指値を置いて待つ・恒等レーン専用＝探索は生成できない）。
    # グリッド/MM の別型（複数指値の同時管理）は後続の拡張点。未知の型は fail-closed。
    et = ent.get("type", "edge_trigger")
    if et == "ceiling_resting":
        if lane != "legacy":
            _fail("G6", "entry.type=ceiling_resting は恒等検収レーン専用（探索は生成できない・歩6-1）")
        sp = ent.get("split") or {}
        for key in ("gap_pct", "down_window_hours", "max_age_hours"):
            if key not in sp:
                _fail("G5", f"ceiling_resting の split.{key} が無い（e37 v26 切り分けの値）")
            _check_value(sp[key], lane, f"entry.split.{key}", rep["legacy使用"])
        if not isinstance(sp.get("down_no_age", False), bool):
            _fail("G5", "ceiling_resting の split.down_no_age が bool でない（v40 の免除）")
        if "rearm_delay_bars" in sp:                  # v56（里程標2）＝uptrend 解除直後の若いレンジでは建てない（flat_up 限定）
            _check_value(sp["rearm_delay_bars"], lane, "entry.split.rearm_delay_bars", rep["legacy使用"])
        cl = ent.get("ceiling") or {}                 # 里程標3＝flat_up 天井のクランプ群（v35/v36/v37/v38）
        if cl.get("flat_up_top") not in (None, "range_high"):
            _fail("G6", f"ceiling.flat_up_top は range_high のみ（v35）: {cl.get('flat_up_top')}")
        for key in ("near_fallback", "clamp_prev_fill", "climb_guard"):
            if key in cl and not isinstance(cl[key], bool):
                _fail("G5", f"ceiling.{key} が bool でない（v36/v38/v37 の有無）")
        if cl.get("near_fallback") and cl.get("flat_up_top") != "range_high":
            _fail("G5", "ceiling.near_fallback（v36）は flat_up_top=range_high（v35）の上にだけ載る")
    elif et != "edge_trigger":
        _fail("G6", f"entry.type={et} は未実装（edge_trigger／ceiling_resting[legacy] のみ・grid 等は拡張点）")
    # position_exits（位置＝保有全体に掛かる出口・歩6-1）＝uptrend 畳みと構造破れ。恒等レーン専用。
    pex = recipe.get("position_exits")
    if pex is not None:
        if lane != "legacy":
            _fail("G6", "position_exits は恒等検収レーン専用（探索は生成できない・歩6-1）")
        uc = pex.get("uptrend_cut")
        if uc is not None:
            # mode＝close（成行で全部確定・既定）／mark（確定させず印を付けて保持・里程標9＝e37_scalp 1109-1115行）。
            mode = uc.get("mode", "close")
            if mode not in ("close", "mark"):
                _fail("G6", f"uptrend_cut.mode が close/mark でない: {mode}（歩6-1 里程標9）")
            if mode == "close":
                if uc.get("reason") not in REASONS_TAKER:
                    _fail("G6", f"uptrend_cut.reason が taker 登録に無い: {uc.get('reason')}（H13）")
            elif uc.get("state") != "trend_caught":
                _fail("G6", "uptrend_cut.mode=mark の state は trend_caught のみ"
                            "（付けた印に当たる枝は scope.trend_caught で受ける・歩6-1 里程標9）")
        rb = pex.get("range_break")
        if rb is not None:
            if rb.get("reason") not in REASONS_TAKER:
                _fail("G6", f"range_break.reason が taker 登録に無い: {rb.get('reason')}（H13）")
            for key in ("bars", "vol_n"):
                if key not in rb:
                    _fail("G5", f"range_break.{key} が無い（v15 構造破れの値）")
                _check_value(rb[key], lane, f"position_exits.range_break.{key}", rep["legacy使用"])
    tree = ent.get("connective")
    if tree is None and et == "ceiling_resting":
        tree = {"all": []}                            # 天井型＝発火は engine 側の幾何（条件の木は空でよい）
    if tree is None:
        _fail("G5", "entry.connective（つなぎ木）が無い")
    # 発火経路＝最上位 any の各枝（設計書 §2.1・P22 型 OR・まこさん GO）
    paths = tree["any"] if (isinstance(tree, dict) and set(tree) == {"any"}) else [tree]
    rep["経路数"] = len(paths)
    p_max, _wait = cap_of(lm, "p_max")
    if _wait:
        rep["値待ち"].append("P_MAX（経路数の上限・§11-8）")
    elif p_max is not None and len(paths) > p_max:
        _fail("G1", f"発火経路が {len(paths)} 本 > P_MAX={p_max}")
    all_conds = []
    for pi, path in enumerate(paths):
        conds, depths = _walk(path)
        all_conds += conds
        if et == "ceiling_resting":
            if conds:
                _fail("G5", "ceiling_resting の entry は条件の木を持たない（発火は天井の幾何＝engine 側・歩6-1）")
            continue
        # ★否定の中に引き金を置けない（M2-2-5 の禁止1・2026-08-21 まこさん承認 24a453d6…）
        for c in _conds_under_not(path):
            if c.get("role") == "trigger":
                _fail("G1", f"経路{pi + 1}: 引き金を否定（not）の中に置けない"
                            "＝引き金は縁で発火するもので、その否定は『発火していないほとんど全部のバー』"
                            "になり、経路ごとに引き金ちょうど1本 の決まりが意味を失う")
        trigs = [c for c in conds if c.get("role") == "trigger"]
        if len(trigs) == 0:
            _fail("G1", f"経路{pi + 1}: 引き金がゼロ（原理的に発火しない構成は作れない）")
        if len(trigs) > 1:
            _fail("G1", f"経路{pi + 1}: 引き金が {len(trigs)} 本（発火経路ごとにちょうど1本）")
        # 引き金は経路の最上位 all の直下にだけ置ける（any/if-then の内側は不可・CP3 提案4-②）
        top = path.get("all", [path] if _is_cond(path) else []) if isinstance(path, dict) else []
        if trigs[0] not in top:
            _fail("G1", f"経路{pi + 1}: 引き金が経路の最上位 all の直下に無い（any/if-then の内側は不可）")
    for c in recipe.get("pre_filter", []):
        if c.get("role") == "trigger":
            _fail("G1", "pre_filter に引き金は置けない（状態評価のみ・設計書 §1）")
        _check_cond(c, lane, "pre_filter", rep["legacy使用"])
    for i, c in enumerate(all_conds):
        if c.get("role") not in ROLES:
            _fail("G5", f"条件{i + 1}: 役割が無い/不正: {c.get('role')}（G1 の前提＝役割の欄）")
        _check_cond(c, lane, f"entry条件{i + 1}", rep["legacy使用"])
    rep["条件数"] = len(all_conds)
    cr, _wait = cap_of(lm, "count_range")
    if _wait:
        rep["値待ち"].append("条件の合計本数の範囲（§11-4）")
    elif cr is not None and not (cr[0] <= len(all_conds) <= cr[1]):
        _fail("G5", f"条件の合計本数 {len(all_conds)} が範囲 {cr} の外")
    role_max, _wait = cap_of(lm, "role_max")
    if _wait:
        rep["値待ち"].append("E_MAX/S_MAX/L_MAX（役割ごとの本数上限・§11-3）")
    elif role_max is not None:
        from collections import Counter
        rc = Counter(c["role"] for c in all_conds)
        for r, mx in role_max.items():
            if rc.get(r, 0) > mx:
                _fail("G5", f"役割 {r} が {rc[r]} 本 > 上限 {mx}")
    dmax, _wait = cap_of(lm, "depth_max")
    depth = _tree_depth(tree)
    if _wait:
        rep["値待ち"].append("木の深さ上限（§11-7）")
    elif dmax is not None and depth > dmax:
        _fail("G5", f"つなぎ木の深さ {depth} > 上限 {dmax}")
    # G3 同系統の重ね掛け制限（同一系統は同一役割に1本まで＝構造規則・K_MAX＝まこさん）
    seen_role_kind = set()
    from collections import Counter as _C
    kind_count = _C()
    for c in all_conds + list(recipe.get("pre_filter", [])):
        for m in (c.get("material") or []):
            fam = _material_family(m)
            lin = iref.FAMILY_LINEAGE.get(fam)
            if lin is None and "legacy_col" not in m:
                _fail("G3", f"系統マップに無い family: {fam}（載っていない family は生成不可）")
            kind = lin["k"] if lin else "legacy"
            rep["系統"][fam] = kind
        # ★並びの決まる形にする（2026-08-16・A-1a-0 の2番）。
        #   直す前は set をそのまま上から順に見ていた＝Python は走らせるたびに文字列の置き場所を
        #   変えるので、違反が2つ以上あるときに どちらのメッセージが先に出るかが実行ごとに変わった。
        #   通る／止まるの結果は変わらないが、囲いが無いこと自体を塞ぐ
        #   （2026-08-16 に生成器で同じ型の事故が実際に起きた＝worklog 20260816 §4）。
        fams = sorted({_material_family(m) for m in (c.get("material") or [])})
        kinds = sorted({iref.FAMILY_LINEAGE[f]["k"] for f in fams if f in iref.FAMILY_LINEAGE})
        for kind in kinds:
            key = (c.get("role"), kind)
            if key in seen_role_kind and c.get("role") != "trigger":
                _fail("G3", f"同一系統 {kind} を同一役割 {c.get('role')} に2本（1本まで）")
            seen_role_kind.add(key)
            kind_count[kind] += 1
    k_max, _wait = cap_of(lm, "k_max")
    if _wait:
        rep["値待ち"].append("K_MAX（同系統のレシピ全体での上限・§11-5）")
    elif k_max is not None:
        for kind, n in kind_count.items():
            if n > k_max:
                _fail("G3", f"系統 {kind} が {n} 本 > K_MAX={k_max}")
    # G2 適合制約（補正後独立標本数 ≥ N_MIN・値決め窓・検査5 の機械出力が基礎データ）
    used_cols = []
    for c in all_conds + list(recipe.get("pre_filter", [])):
        for m in (c.get("material") or []):
            kind, name = _material_name(m, lane)
            if kind in ("col", "geo"):
                used_cols.append(name)
    rep["触れた列"] = sorted(set(used_cols))
    n_min = lm.get("n_min")
    if n_min is None:
        rep["値待ち"].append("N_MIN（補正後独立標本数の下限・§11-1）")
    else:
        for col in used_cols:
            if samples is None:
                _fail("G2", "N_MIN があるのに補正後独立標本数の表（検査5）が無い＝判定できない（fail-closed）")
            got = samples.get(col)
            if got is None or got < n_min:
                _fail("G2", f"補正後独立標本数が不足: {col}＝{got}（N_MIN={n_min}・検査5 が基礎データ）")
    # 出口の枝（§6）と G4
    exits = recipe.get("exits") or []
    if not exits:
        _fail("G5", "exits（出口の枝）が空")
    names = set()
    for b in exits:
        nm = b.get("name")
        if not nm or nm in names:
            _fail("G5", f"枝の name が無い/重複: {nm}")
        names.add(nm)
        reason = b.get("reason")
        if reason not in REASONS_MAKER | REASONS_TAKER:
            _fail("G6", f"枝 {nm}: 出口理由 {reason} が score.py の maker/taker 登録に無い（H13）")
        ex = b.get("exec") or {}
        if ex.get("method") in EXEC_REGISTERED_ONLY:
            _fail("G6", f"枝 {nm}: 執行方式 {ex['method']} は登録済みだが歩3 では実行不能＝拒否側（CP3 Q1）")
        if ex.get("method") not in EXEC_METHODS:
            _fail("G6", f"枝 {nm}: 執行方式が不正: {ex.get('method')}（X-k のうち実行可能＝{EXEC_METHODS}）")
        pl = ex.get("placement") or {}
        if pl.get("kind") not in ("resting", "on_close"):
            _fail("G6", f"枝 {nm}: placement.kind が resting/on_close でない: {pl.get('kind')}")
        if pl.get("kind") == "resting":
            _check_level(pl.get("level"), lane, f"exit枝{nm}", rep["legacy使用"])
            if pl.get("fill") not in ("profit", "adverse"):
                _fail("G6", f"枝 {nm}: resting の fill（profit/adverse）が無い")
        fire = b.get("fire")
        if fire is not None:
            conds, _d = _walk(fire)
            for c in conds:
                _check_cond({**c, "role": c.get("role", "env")}, lane, f"exit枝{nm}", rep["legacy使用"])
                _check_exit_fire_cond(c, lane, f"exit枝{nm}")     # ★出口だけの検査8つ（97番の設計 v3）
        bw = ex.get("be_wait")
        if bw is not None:
            _check_level(bw.get("level"), lane, f"exit枝{nm}/be_wait", rep["legacy使用"])
            _check_value(bw.get("ttl", {}), lane, f"exit枝{nm}/be_wait.ttl", rep["legacy使用"])
        sr = b.get("size_ratio")
        if not (isinstance(sr, (int, float)) and 0 < sr <= 1):
            _fail("G5", f"枝 {nm}: size_ratio が (0,1] でない: {sr}")
        sc = b.get("scope")
        if sc is not None:
            if "adds" in sc and not (isinstance(sc["adds"], list) and len(sc["adds"]) == 2):
                _fail("G5", f"枝 {nm}: scope.adds は [下限, 上限]")
            if "trend_caught" in sc:           # 里程標9＝印が付いた玉だけに当たる枝（v24/MFE_STALE）
                if not isinstance(sc["trend_caught"], bool):
                    _fail("G5", f"枝 {nm}: scope.trend_caught が bool でない")
                if lane != "legacy":
                    _fail("G6", f"枝 {nm}: scope.trend_caught は恒等検収レーン専用"
                                f"（印を付けるのは position_exits の mark＝恒等レーン専用・探索は生成できない）")
                if (recipe.get("position_exits") or {}).get("uptrend_cut", {}).get("mode") != "mark":
                    _fail("G5", f"枝 {nm}: scope.trend_caught があるのに印を付ける側"
                                f"（position_exits.uptrend_cut.mode=mark）が無い＝この枝は一度も発火しない")
    has_sl = any(b.get("reason") == "SL_FILLED" for b in exits)
    has_losscap = any(b.get("risk") == "loss_cap" for b in exits)
    if not has_sl and not has_losscap:
        _fail("G4", "SL 系の枝も1トレード許容損失枝（X-d(11)）も無い（リスクリワード事前担保・生成拒否）")
    if lm.get("r_min") is None:
        rep["値待ち"].append("R_MIN（リスクリワード比の下限・§11-2）")
    # 玉の持ち方（§7）
    pos = recipe.get("position") or {}
    if pos.get("mode") not in ("separate", "avg"):
        _fail("G5", f"position.mode が separate/avg でない: {pos.get('mode')}")
    if not (isinstance(pos.get("max_adds"), int) and pos["max_adds"] >= 1):
        _fail("G5", f"position.max_adds が不正: {pos.get('max_adds')}")
    # ★2026-08-15（段A の A-5-2）＝積み増しの回数が「探せる範囲」の中かを見る（fail-closed）。
    #   範囲の正本＝recipes/search_limits.json の max_adds_range（直す前は 1・2・3・5 の4つだけ）。
    if lane != "legacy":
        _check_num_range("max_adds_range", pos["max_adds"], "position.max_adds")
    if pos["mode"] == "avg" and (pos.get("add_trigger") or {}).get("kind") not in ("resignal", "adverse_pct", "time", "profit_confirm"):
        _fail("G5", f"avg 形の add_trigger.kind が X-i(9) の4種でない: {pos.get('add_trigger')}")
    return rep


def _check_level(lv, lane: str, where: str, legacy_used: list):
    """placement の価格水準（設計書 §6＝幾何参照／建値比／定数の3種＋mix・zone_sl の具体形）。"""
    if not isinstance(lv, dict):
        _fail("G6", f"{where}: placement.level が無い")
    kind = lv.get("kind")
    if kind == "zone":
        if lv.get("target") not in ("mid", "opp"):
            _fail("G6", f"{where}: zone.target が mid/opp でない")
        if lv.get("target") == "opp":
            _check_value(lv.get("buf", {}), lane, f"{where}/buf", legacy_used)
            if lv.get("fallback") not in (None, "mid"):
                _fail("G6", f"{where}: zone.fallback は mid のみ（v18 の幾何防御＝中央超え/非有限は中央へ・歩6-1）")
    elif kind == "zone_sl":
        if lv.get("w", "range") not in ("range", "zone", "inner"):
            _fail("G6", f"{where}: zone_sl.w が range/zone/inner でない: {lv.get('w')}"
                        f"（range＝レンジ全幅 res_hi−sup_lo／zone＝同じ側の帯幅／inner＝帯の内側の隙間 res_lo−sup_hi・歩6-1）")
        _check_value(lv.get("k", {}), lane, f"{where}/k", legacy_used)
    elif kind == "mix":
        has_to = bool(lv.get("to")) or isinstance(lv.get("to_level"), dict)
        if lv.get("from") != "entry" or not has_to:
            _fail("G6", f"{where}: mix は from=entry と to=<枝名>（または to_level=<水準>・歩6-1）が要る")
        if isinstance(lv.get("to_level"), dict):
            _check_level(lv["to_level"], lane, f"{where}/to_level", legacy_used)
        _check_value(lv.get("frac", {}), lane, f"{where}/frac", legacy_used)
    elif kind == "pct":
        if lv.get("base") not in ("entry", "avg"):
            _fail("G6", f"{where}: pct.base が entry/avg でない")
        _check_value(lv.get("k", {}), lane, f"{where}/k", legacy_used)
    elif kind == "peak_giveback":
        # v27 型のピーク反転ロック（歩6-1 里程標5）＝武装 arm%・戻し giveback・下限 floor（建値フロア）。
        for key in ("arm", "giveback", "floor"):
            if key not in lv:
                _fail("G5", f"{where}: peak_giveback.{key} が無い（arm＝武装%／giveback＝戻す割合／floor＝建値フロア）")
            _check_value(lv[key], lane, f"{where}/{key}", legacy_used)
    elif kind == "shrink":
        # v13 deadline shrink（歩6-1・S1 の書き写し）＝from 枝の水準から建値フロアへ残り時間比で縮む maker TP。
        if lv.get("from") is None:
            _fail("G6", f"{where}: shrink.from（縮み始めの枝名・例 TP2）が無い")
        for key in ("tmax", "floor"):
            if key not in lv:
                _fail("G5", f"{where}: shrink.{key} が無い（tmax＝縮み切るまでの本数／floor＝建値フロアの床）")
            _check_value(lv[key], lane, f"{where}/{key}", legacy_used)
    elif kind == "swing":
        # v22 アンカー（歩6-1 里程標9・e37_scalp 1531-1541行）＝利確の基準を直近 m 本の安値（SHORT）に置く。
        # target＝low（SHORT の利確側）／high（LONG の利確側）。当該バーは含めない（H2＝rolling().shift(1)）。
        # buf＝返す水準に掛ける余白（SHORT は ×(1+buf)＝安値のすぐ手前）。
        # gate_buf＝「その水準が建値より利益側にあるか」を判定する時に使う余白（省略時は buf と同じ）。
        # fallback＝判定に落ちた時／安値が欠損の時に使う水準（入れ子＝TP2 なら反対側ゾーン・TP1 なら中央）。
        # ★TP1 と TP2 は同じ判定を各自で評価する＝同じバー・同じ値なので必ず同時に切り替わる（実装と同じ連動）。
        if lv.get("target") not in ("low", "high"):
            _fail("G6", f"{where}: swing.target が low/high でない: {lv.get('target')}")
        if "m" not in lv:
            _fail("G5", f"{where}: swing.m（さかのぼる本数）が無い")
        _check_value(lv["m"], lane, f"{where}/m", legacy_used)
        for key in ("buf", "gate_buf"):
            if key in lv:
                _check_value(lv[key], lane, f"{where}/{key}", legacy_used)
        if not isinstance(lv.get("fallback"), dict):
            _fail("G5", f"{where}: swing.fallback（判定に落ちた時に使う水準）が無い"
                        f"（幾何が成立しない時に黙って建てないのでなく、元の置き方へ戻す＝実装と同じ）")
        _check_level(lv["fallback"], lane, f"{where}/fallback", legacy_used)
    else:
        _fail("G6", f"{where}: level.kind が zone/zone_sl/mix/pct/shrink/swing でない: {kind}")


# ══ ② 実行器（共通の売買ループ・設計書 §1〜§7 の意味論）══════════════════════════════
def _side_cmp(val, th, side: str):
    """側の比較（above=≥／below=≤／above_strict=>／below_strict=<）。配列でも単値でも同じ式で使う。"""
    if side == "above":
        return val >= th
    if side == "below":
        return val <= th
    if side == "above_strict":
        return val > th
    return val < th


def _vnum(v: dict) -> float:
    """値の解決（数値）＝legacy/定数/整数のみ。分位は _vnum_q（解決表つき・歩4）で解く。"""
    if "legacy" in v:
        return float(v["legacy"])
    if "const" in v:
        val = float(iref.CONST_REGISTRY[v["const"]]["value"])
        return val * float(v.get("mult", 1.0))
    if "n" in v:
        return float(v["n"])
    raise RecipeError(f"[実行器] 値を解決できない（分位は解決表＝qtable が要る）: {v}")


def _vnum_q(v: dict, qkey: str, qtable: dict | None, ctx: tuple | None = None):
    """値の解決（分位対応・歩4）。threshold_q は解決表（値決め窓の分布から探索開始時に1回固定・§2.4-①・
    §5-4）でしか実値にならない＝表に無ければ止まる（fail-closed・rolling 解決の混入経路を持たない）。

    ★2026-08-21（M2-2-5・まこさん承認 24a453d6…）＝連動する閾値（ref）を足した。
      ref が在るときだけ、戻り値が「1バーごとの並び」になる（ほかは今までどおり数字1つ）。
      比べる側（_side_cmp・帯の中か・クロス・差）は、数字1つでも並びでも同じ式で動く。
      ctx＝(df, geo, lane)。入口と判定の中身の条件からしか渡されない＝出口の枝では使えない。
    ★未来を見ない（H2）＝連動先の列は、その材料をそのまま読むだけ（うしろのバーは見ない）。
    """
    if "ref" in v:
        if ctx is None:
            raise RecipeError("[実行器] 連動する閾値（ref）は、入口と判定の中身の条件でだけ使える"
                              "（出口の枝では使えない・fail-closed）")
        _df, _geo, _lane = ctx
        out = _col_array(_df, v["ref"], _geo, _lane) * float(v.get("mult", 1.0))
        if "clip_lo" in v:
            out = np.maximum(out, _vnum_q(v["clip_lo"], qkey, qtable, ctx))
        if "clip_hi" in v:
            out = np.minimum(out, _vnum_q(v["clip_hi"], qkey, qtable, ctx))
        return out
    if "threshold_q" in v:
        q = v["threshold_q"]
        if qtable is None or qkey not in qtable or q not in qtable[qkey]:
            raise RecipeError(f"[実行器] 分位 {q} の解決表に {qkey} が無い"
                              f"（解決表＝探索開始時に1回固定・§5-4・生成器が作って渡す）")
        return float(qtable[qkey][q]) * float(v.get("mult", 1.0))
    return _vnum(v)


# ══ 材料をその場で作る（段A の A-2b・2026-08-13）══════════════════════════════════════
#   ★直す前＝走らせる前に「案が使う列」を全部 作って表に足していた（engine_tuner_gen.attach_materials）。
#     その形だと、作れるのは材料カタログに名前が並んでいる列だけ＝設定ファイルの数字に縛られる。
#   ★直したあと＝条件が「指標の種類・パラメータ・時間足」を渡すと、その組だけをここで計算する。
#     同じ組が2回目に来たら、1回目の結果を使い回す。
#   ★時間足の扱い（上位足に直す → 足が閉じた時刻へずらす → 5分足に合わせる）は書き写さない。
#     observe_diag.build_features をそのまま呼ぶ（式を2か所に持つと片方だけ直って黙って腐る）。
#   ★入れものの鍵に「渡された終値そのものの指紋」を入れる＝データを1本でも切ると計算し直す
#     （未来を見ない・observe_diag の _CYC_MEMO と同じ作り）。
_MAT_MEMO: dict = {"sig": None, "v": {}}


def material_array(df: pd.DataFrame, full: str) -> np.ndarray:
    """カタログ名の列（例＝`RSI12__15m`）を、その場で計算して返す。"""
    close = df["close"].to_numpy(dtype=float)
    sig = (len(df), hashlib.md5(close.tobytes()).hexdigest())
    if _MAT_MEMO["sig"] != sig:
        _MAT_MEMO["sig"], _MAT_MEMO["v"] = sig, {}
    if full in _MAT_MEMO["v"]:
        return _MAT_MEMO["v"][full]
    if "__" not in full:
        raise RecipeError(f"[実行器] 材料の名前に時間足が無い: {full}")
    base, tf = full.rsplit("__", 1)
    if iref.find(base)[0] is None:
        raise RecipeError(f"[実行器] カタログに無い材料: {base}（indicator_reference_diag に未登録）")
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import observe_diag as _od
        fam, prm = _od.find_material(base)
        if fam is None:
            raise RecipeError(f"[実行器] 材料の表に無い名前: {base}（observe_diag の MATERIAL_FAMILIES）")
        cfg = _od.load_config()
        drop = {a for a, _b in (cfg.get("drop_columns") or [])}
        if base in drop:
            raise RecipeError(f"[実行器] 省く設定に載っている材料: {base}（observe_config の drop_columns）")
        if tf not in cfg["timeframes"]:
            raise RecipeError(f"[実行器] 使えない時間足: {tf}（使えるのは {cfg['timeframes']}）")
        cfg_tf = dict(cfg)
        cfg_tf["timeframes"] = [tf]
        bars = df.set_index(pd.to_datetime(df["ts"]))[["open", "high", "low", "close", "volume"]]
        one = _od.make_material(fam, *prm)
        feats, meta = _od.build_features(bars, cfg_tf, catalog=[one])
    if full not in feats.columns:
        raise RecipeError(f"[実行器] 材料 {full} をその場で作れなかった（{meta.get(full)}）")
    a = feats[full].to_numpy(float)
    _MAT_MEMO["v"][full] = a
    return a


def _col_array(df: pd.DataFrame, m: dict, geo: dict, lane: str) -> np.ndarray:
    """材料1本 → 各バーの値。★前処理（pre）が在れば、最後に部品を1つ掛ける（2026-08-13）。"""
    pre = _pre_of(m)
    if pre is not None:
        # ★df も渡す（M2-2-5）＝状態に入って以降を見る部品（since_min ほか）が、基準の列を読むため
        return _apply_pre(_col_array(df, {k: v for k, v in m.items() if k != "pre"}, geo, lane), pre, df)
    kind, name = _material_name(m, lane)
    if kind == "geo":
        return geo[name]
    if kind == "legacy_col":
        if name not in df.columns:
            raise RecipeError(f"[実行器] legacy 材料列が実行データに無い: {name}")
        return df[name].to_numpy(float)
    if kind == "time":
        ts = pd.DatetimeIndex(df["ts"])
        return (ts.hour if name == "時刻" else ts.weekday).to_numpy(float)
    if kind == "col":
        # 歩4 拡張＝カタログ名の列が実行データに直接あればそれを使う（生成器が observe_diag
        # build_features で必要列だけ組み立てて df に付けて渡す）。無ければ従来の別名（恒等系）。
        if name in df.columns:
            return df[name].to_numpy(float)
        run_col = RUNTIME_ALIAS.get(name)
        if run_col is not None and run_col in df.columns:
            return df[run_col].to_numpy(float)
        # ★2026-08-13（段A の A-2b）＝ここで、その場で計算する（列を先に全部 作らない）。
        return material_array(df, name)
    raise RecipeError(f"[実行器] 入口の材料に使えない種別: {kind}（{name}）")


def _mat_key(m: dict, lane: str) -> str:
    """分位の解決表の鍵＝材料の解決名（列名）。★前処理が在れば分布が変わるので鍵も分ける（2026-08-13）。"""
    name = _material_name(m, lane)[1]
    pre = _pre_of(m)
    if not pre:
        return name
    if pre["op"] in SINCE_OPS:                     # ★状態に入って以降（M2-2-5）＝基準の状態ごとに分布が違う
        return f"{pre['op']}:{pre['state']}:{name}"
    return f"{pre['op']}{pre['n']}:{name}"


def _hold_state(on: np.ndarray, off: np.ndarray, n: int) -> np.ndarray:
    """入る条件・出る条件・保てる最大の本数 → 各バーの真偽（M2-2-5・状態を保つ形の中身）。

    決めごと（設計 24a453d6… のとおり）:
      ① on が成立したバーから真になる。
      ② off が成立したバーで偽に戻る。
      ③ どちらも成立しないバーは、前のバーの値を保つ。
      ④ 真になってから n本 経ったら、off が来なくても偽に戻る（＝C7 の「続く長さ」）。
         ★**on がもう一度 成立したら、そこから数え直す**＝続いているあいだは保つ。
           出どころ＝RG-v5 の実物の「継続」（`scripts/dashboard/build_regime_gate_rg.py`:19 の逐語
           「解除後24h内に前回高値+0.3%超え＝継続再発火」）。＝上げが続いているのに n本 で必ず切る、
           という作りにはしない。
      ⑤ 同じバーで on と off が両方 成立したら、off を優先する（出る側を優先＝安全側）。
    ★未来を見ない（H2）＝`np.maximum.accumulate` は「そのバーまでの最後の成立の位置」を作る。
      うしろのバーの値は1つも使わない。
    ★1バーずつのループで書いても同じ結果になる（①〜⑤のとおりに書いた場合）。走らせる回数が多い
      （案 × 158,112バー）ので並びの計算で書いた。両方が同じ結果になることは selftest（T-HYST）が
      乱数200通りで実測する。★最初、④を「最初の on から数える」と読んで書いたループ版とは
      200通り中131通りで食い違った＝どちらの意味かを決めずに書くと、ここがずれる。
    """
    idx = np.arange(len(on))
    last_on = np.maximum.accumulate(np.where(on, idx, -1))     # そのバーまでで on が真だった最後の位置
    last_off = np.maximum.accumulate(np.where(off, idx, -1))   # 同じく off
    held = idx - last_on                                        # 真になってから何本 経ったか
    return (last_on > last_off) & (held < int(n))               # off と同じバーなら偽＝⑤


def _eval_cond(c: dict, df: pd.DataFrame, geo: dict, lane: str, qtable: dict | None = None) -> np.ndarray:
    """条件1つ → 各バーの真偽（状態評価）。na=fail が既定（欠損は不成立）。"""
    form = c["form"]
    v = c.get("value", {})
    na_pass = (v.get("na") == "pass")
    if form == "hysteresis":                       # ★状態を保つ形（M2-2-5・法則 U10・C6・C7）
        on = _eval_tree(c["on"], df, geo, lane, qtable, allow_bool_col=True)
        off = _eval_tree(c["off"], df, geo, lane, qtable, allow_bool_col=True)
        return _hold_state(on, off, int(v["n"]))
    if form in NEST_FORMS:
        inner = _eval_cond(c["inner"], df, geo, lane, qtable)
        n = int(v["n"])
        off = int(v.get("offset", 0))
        s = pd.Series(inner.astype(float))
        if form == "streak":
            out = (s.rolling(n).sum() >= n).to_numpy()
        elif form == "barssince":
            # ★何本前に成立したか（部品 barssince・2026-08-12・段C の C-6）。
            #   内側の条件が最後に成立したバーからの距離を数え、その本数を閾値 n と比べる。
            #   まだ一度も成立していない所は「値なし」＝既定 na=fail で不成立になる。
            #   数えるのは過去に成立したバーだけ＝未来は見ない。
            idx = np.arange(len(inner))
            last = np.maximum.accumulate(np.where(inner, idx, -1))
            bs = np.where(last >= 0, idx - last, np.nan).astype(float)
            ok = _side_cmp(bs, float(n), c.get("side"))
            out = np.where(np.isfinite(bs), ok, na_pass).astype(bool)
        else:                                     # within_n＝過去N本のどこかで1回でも成立
            out = (s.rolling(n).max() >= 1).to_numpy()
        if off:
            out = np.roll(out, off)
            out[:off] = False
        return out
    if form == "candle_dir":
        o = df["open"].to_numpy(float)
        cl = df["close"].to_numpy(float)
        return (cl > o) if v.get("dir") == "bull" else (cl < o)
    ctx = (df, geo, lane)          # ★連動する閾値（ref）が材料の列を引くための持ち物（M2-2-5）
    mats = c.get("material") or []
    a = _col_array(df, mats[0], geo, lane)
    akey = _mat_key(mats[0], lane)
    if form == "level":
        th = _vnum_q(v, akey, qtable, ctx)
        ok = _side_cmp(a, th, c.get("side"))
        res = np.where(np.isfinite(a), ok, na_pass)
        return res.astype(bool)
    if form in forms_where("band"):
        lo = _vnum_q(v["lo"], akey, qtable, ctx)
        hi = _vnum_q(v["hi"], akey, qtable, ctx)
        if lo > hi:
            lo, hi = hi, lo                       # 分位の取り違えで帯が裏返っても空帯にしない（正規化）
        inside = (a >= lo) & (a <= hi)
        ok = inside if form == "band" else ~inside
        return np.where(np.isfinite(a), ok, na_pass).astype(bool)
    if form == "slope":
        n = int(v["n"])
        d = a - np.roll(a, n)
        d[:n] = np.nan
        th = _vnum_q(v["th"], f"Δ{n}:{akey}", qtable, ctx) if "th" in v else 0.0
        ok = (d >= th) if c.get("side") == "above" else (d <= th)
        return np.where(np.isfinite(d), ok, na_pass).astype(bool)
    if form == "slope_avg":
        n, m_ = int(v["n"]), int(v["m"])
        ma = pd.Series(a).rolling(m_).mean().to_numpy()
        d = ma - np.roll(ma, n)
        d[:n + m_] = np.nan
        th = _vnum_q(v["th"], f"Δ{n}:MA{m_}:{akey}", qtable, ctx) if "th" in v else 0.0
        ok = (d >= th) if c.get("side") == "above" else (d <= th)
        return np.where(np.isfinite(d), ok, na_pass).astype(bool)
    b = _col_array(df, mats[1], geo, lane) if len(mats) > 1 else None
    if form == "cross":
        if b is None:
            # ★閾値とのクロス（部品 cross_val・2026-08-13・段C の C-6）＝相手の列の代わりに
            #   閾値の定数を置く。閾値の解決は level と同じ（同じ鍵 akey の分位・定数・整数）。
            #   ここから下の式は列2本のときと1文字も変えない＝同じ意味論で動く。
            b = np.full(len(a), _vnum_q(v["th"], akey, qtable, ctx), dtype=float)
        pa, pb = np.roll(a, 1), np.roll(b, 1)
        pa[0] = pb[0] = np.nan
        fin = np.isfinite(a) & np.isfinite(b)
        if v.get("direction") == "down":
            out = fin & (pa >= pb) & (a < b)
        else:
            out = fin & (pa <= pb) & (a > b)
        return out.astype(bool)
    if form == "diff":
        # ★材料2本の組み方（部品 div・corr・2026-08-12・段C の C-6）＝正本は PAIR_OPS。
        #   書いていなければ引き算＝鍵も式も 2026-08-12 より前と1文字も変わらない。
        op = _pair_op_of(v)
        n_win = int(v["n"]) if PAIR_OPS[op]["needs_n"] else None
        d = _pair_series(a, b, op, n_win)
        th = _vnum_q(v.get("th", v), _pair_key(akey, _mat_key(mats[1], lane), op, n_win), qtable, ctx)
        ok = (d >= th) if c.get("side") == "above" else (d <= th)
        return np.where(np.isfinite(d), ok, na_pass).astype(bool)
    if form == "touch":
        tol = _vnum(v)                            # 許容幅＝名前つき定数（§2.2・分位は使わない）
        d = np.abs(a - b)
        return np.where(np.isfinite(d), d <= tol * np.abs(b), na_pass).astype(bool)
    raise RecipeError(f"[実行器] 形 {form} の実行が未実装")


def _eval_tree(node, df: pd.DataFrame, geo: dict, lane: str, qtable: dict | None = None,
               allow_bool_col: bool = False) -> np.ndarray:
    """条件の木 → 各バーの真偽（M2-2-5 で1か所にまとめた）。

    ★直す前は、同じ式が3か所（入口の発火・判定の中身・…）に書き写されていた。
      いまは、入口の発火（_entry_fire）・判定の中身（build_regime_columns）・状態を保つ形の
      内側（_eval_cond の hysteresis）が、この1つを呼ぶ＝式を書き写さない
      （書き写すと片方だけ直って黙って腐る＝M2-2-3b と同じ思想）。
    ★意味は直す前と1つも変えていない＝all（全部 真）・any（どれか真）・if-then（if が真なら then を要求）。
      足したのは not（否定）だけ。
    ★bool_col（真偽の列の参照）は判定の中身（build）の中だけ＝入口では検査が先に拒否する（C5）。
    """
    if isinstance(node, dict) and "bool_col" in node:
        if not allow_bool_col:
            raise RecipeError("[実行器] bool_col は判定の中身（build）の中だけで使える（入口では使えない）")
        col = node["bool_col"]
        if col not in df.columns:
            raise RecipeError(
                f"[相場の列が無い] build の bool_col {col} がデータにありません"
                f"（判定の材料の列が要ります・fail-closed）")
        arr = df[col].to_numpy(bool)
        return arr if node["want"] else ~arr
    if _is_cond(node):
        return _eval_cond(node, df, geo or {}, lane, qtable)
    if "not" in node:                                  # ★否定（M2-2-5・法則 R8）
        return ~_eval_tree(node["not"], df, geo, lane, qtable, allow_bool_col)
    if "all" in node:
        out = np.ones(len(df), bool)
        for ch in node["all"]:
            out &= _eval_tree(ch, df, geo, lane, qtable, allow_bool_col)
        return out
    if "any" in node:
        out = np.zeros(len(df), bool)
        for ch in node["any"]:
            out |= _eval_tree(ch, df, geo, lane, qtable, allow_bool_col)
        return out
    cond_if = _eval_tree(node["if"], df, geo, lane, qtable, allow_bool_col)
    cond_th = _eval_tree(node["then"], df, geo, lane, qtable, allow_bool_col)
    return ~cond_if | cond_th                          # if-then＝if が真のときだけ then を要求


def build_regime_columns(df: pd.DataFrame, recipe: dict, geo: dict | None = None,
                         qtable: dict | None = None) -> None:
    """meta.regime.build（判定の中身＝条件の束）から真偽の列を作って df に足す（M2-1-6・2026-08-20 まこさん承認）。

    - build が無いレシピでは何もしない（後方互換＝既存のレシピは1バイトも動きが変わらない）。
    - bool_col＝df の列を真偽で読む（want=false なら反転）。列が無ければ止める（fail-closed・_regime_series と同じ思想）。
    - 普通の条件＝入口と同じ _eval_cond を再利用（二重に作らない）。束ね方も入口と同じ意味論
      （all＝全部 真／any＝どれか真／if-then＝if が真なら then を要求＝_entry_fire の _eval_tree と同式）。
    - できた列は out_col の名前で df に足す。df に同名の列が既に在れば止める（上書きの防止）。
    - 同じ df に2回 呼ばれたら2回目は何もしない（run_recipe が作った列を _ceiling_fire の経路がそのまま読む。
      作った列の名前は df.attrs に覚える＝「元から在った同名の列」との区別）。
    ★この段（M2-1）では、できた列はまだ売買の判定に使われない＝entry_col が指す列は従来どおり。
      中身の確かめ（range_ok_rg5 との1バーずつ一致）は M2-1-7。判定の差し替えは M2-11。
    """
    rg = (recipe.get("meta") or {}).get("regime") or {}
    bd = rg.get("build")
    if not bd:
        return
    lane = (recipe.get("meta") or {}).get("lane", "")
    built = df.attrs.setdefault("_regime_built", set())

    # ★木の評価は _eval_tree（モジュールの関数）を呼ぶ＝入口と同じ1つの式（M2-2-5 で1か所にまとめた）
    for slot in ("entry", "block"):
        one = bd.get(slot)
        if one is None:
            continue
        out_col = one["out_col"]
        if out_col in built:
            continue
        if out_col in df.columns:
            raise RecipeError(
                f"[上書きの防止] build.{slot}.out_col {out_col} と同じ名前の列が、データに既にあります")
        df[out_col] = _eval_tree(one["tree"], df, geo or {}, lane, qtable, allow_bool_col=True)
        built.add(out_col)


def _entry_fire(recipe: dict, df: pd.DataFrame, geo: dict, qtable: dict | None = None) -> np.ndarray:
    """エントリー発火＝経路の木が当バーで真 ∧ その経路の引き金が当バーで縁（設計書 §2.1・確定意味論）。"""
    lane = recipe["meta"].get("lane", "")
    tree = recipe["entry"]["connective"]
    paths = tree["any"] if (isinstance(tree, dict) and set(tree) == {"any"}) else [tree]
    pre = np.ones(len(df), bool)
    for c in recipe.get("pre_filter", []):
        pre &= _eval_cond(c, df, geo, lane, qtable)
    fire = np.zeros(len(df), bool)

    # ★木の評価は _eval_tree（モジュールの関数）＝判定の中身（build）と同じ1つの式（M2-2-5）
    for path in paths:
        conds, _d = _walk(path)
        trig = next(c for c in conds if c.get("role") == "trigger")
        t_true = _eval_cond(trig, df, geo, lane, qtable)
        edge = t_true & ~np.roll(t_true, 1)       # 縁＝前バー不成立→今バー成立（cross は形が縁を内包）
        edge[0] = False
        fire |= _eval_tree(path, df, geo, lane, qtable) & edge & pre
    return fire


def _swing_key(lv: dict) -> str:
    """swing 水準（直近 m 本の安値／高値）の配列の鍵。run_recipe がループの前に作って geo へ入れる。"""
    return f"swing:{lv['target']}:{int(_vnum(lv['m']))}"


def _swing_specs(recipe: dict) -> list[tuple[str, int]]:
    """レシピの中の swing 水準を全部集める（入れ子の fallback と mix の to_level も辿る・里程標9）。"""
    out: list[tuple[str, int]] = []

    def _walk_lv(lv):
        if not isinstance(lv, dict):
            return
        if lv.get("kind") == "swing":
            out.append((lv["target"], int(_vnum(lv["m"]))))
            _walk_lv(lv.get("fallback"))
        elif lv.get("kind") == "mix":
            _walk_lv(lv.get("to_level"))

    for b in recipe.get("exits") or []:
        ex = b.get("exec") or {}
        _walk_lv((ex.get("placement") or {}).get("level"))
        _walk_lv((ex.get("be_wait") or {}).get("level"))
    return out


def _static_level_px(lv: dict, i: int, lim: float, side: str, geo: dict) -> float:
    """エントリー時に1回だけ解ける水準を1つ解決する（zone／zone_sl／pct／swing）。
    swing の fallback で入れ子になるので再帰にしてある（歩6-1 里程標9 で分離）。"""
    sgn = -1.0 if side == "SHORT" else 1.0        # profit 側の符号（SHORT は下が利益）
    kind = lv["kind"]
    if kind == "zone":
        if lv["target"] == "mid":
            px = geo["mid"][i]
        else:                                     # opp＝反対側ゾーン手前×バッファ（v18 と同じ幾何）
            buf = _vnum(lv.get("buf", {"const": "V11_SL_BUF"}))
            px = geo["sup_hi"][i] * (1 + buf) if side == "SHORT" else geo["res_lo"][i] * (1 - buf)
            if lv.get("fallback") == "mid":       # v18 幾何防御＝非有限/中央超えは中央へ（e37_scalp 1524-1530行と同式）
                _mid = geo["mid"][i]
                if not (np.isfinite(px) and (px < _mid if side == "SHORT" else px > _mid)):
                    px = _mid
    elif kind == "zone_sl":
        k = _vnum(lv["k"])
        if lv.get("w", "range") == "zone":        # 同じ側の帯幅（L1＝sup_hi−sup_lo・run_long_support 1634行と同式）
            w = max((geo["res_hi"][i] - geo["res_lo"][i]) if side == "SHORT"
                    else (geo["sup_hi"][i] - geo["sup_lo"][i]), 1e-9)
        elif lv.get("w") == "inner":              # 帯の内側の隙間（S1＝res_lo−sup_hi・e37_scalp 1513/1549行と同式・下駄なし）
            w = geo["res_lo"][i] - geo["sup_hi"][i]
        else:                                     # range＝レンジ全幅（S2 恒等と同じ既定）
            w = max(geo["res_hi"][i] - geo["sup_lo"][i], 1e-9)   # 実装と同じ下駄（幅0の防御・S2 恒等）
        px = geo["res_hi"][i] + k * w if side == "SHORT" else geo["sup_lo"][i] - k * w
    elif kind == "pct":
        base = lim                                # entry 基準（avg 基準は arm 時に解決＝be_wait）
        kv = _vnum(lv["k"])
        if lv["k"].get("side_sign") == "profit":
            kv = abs(kv) * sgn
        px = base * (1 + kv)
    elif kind == "swing":
        # v22 アンカー（里程標9・e37_scalp 1531-1541行）＝直近 m 本の安値（SHORT）を利確の基準にする。
        key = _swing_key(lv)
        arr = geo.get(key)
        if arr is None:
            raise RecipeError(f"[実行器] swing の配列 {key} が用意されていない（run_recipe が事前に作る）")
        raw = float(arr[i])
        buf = _vnum(lv["buf"]) if "buf" in lv else 0.0
        gbuf = _vnum(lv["gate_buf"]) if "gate_buf" in lv else buf
        if side == "SHORT":
            gate_px = raw * (1.0 + gbuf)
            use = bool(np.isfinite(raw) and gate_px < lim)   # 安値のすぐ手前が建値より下＝利益側にある
            px = raw * (1.0 + buf)
        else:
            gate_px = raw * (1.0 - gbuf)
            use = bool(np.isfinite(raw) and gate_px > lim)
            px = raw * (1.0 - buf)
        if not use:                               # 幾何の防御＝元の置き方へ戻す（e37_scalp 1540-1541行と同じ）
            px = _static_level_px(lv["fallback"], i, lim, side, geo)
    else:
        raise RecipeError(f"[実行器] level.kind 未実装: {kind}")
    return float(px)


def _resolve_levels(exits: list, i: int, lim: float, side: str, geo: dict, lane: str) -> dict:
    """resting 枝の価格水準をシグナルバー i で解決（設計書 §6・エントリー時に指値を置く）。"""
    lv_out: dict[str, float] = {}
    mixes = []
    for b in exits:
        pl = (b.get("exec") or {}).get("placement") or {}
        if pl.get("kind") != "resting":
            continue
        lv = pl["level"]
        if lv["kind"] in ("shrink", "peak_giveback"):
            continue                              # 毎バーの水準（歩6-1）＝ここでは解決しない（ループ側で計算）
        if lv["kind"] == "mix":
            mixes.append((b["name"], lv))
            continue
        lv_out[b["name"]] = _static_level_px(lv, i, lim, side, geo)
    for name, lv in mixes:                        # mix は他の枝の水準に依存＝後で解決
        if isinstance(lv.get("to_level"), dict):  # to_level＝枝でなく水準そのもの（S1 の TP1＝mid 基準・歩6-1）
            to = _static_level_px(lv["to_level"], i, lim, side, geo)
        else:
            to = lv_out.get(lv["to"])
            if to is None:
                raise RecipeError(f"[実行器] mix の参照先 {lv['to']} が resting 枝に無い")
        frac = _vnum(lv["frac"])
        lv_out[name] = float(lim + frac * (to - lim))
    return lv_out


def _ceiling_fire(recipe: dict, df: pd.DataFrame, geo: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ceiling_resting の発火の前提と指値水準（歩6-1＝e37 v26 切り分けの書き写し・1459〜1495行と同式）。
    戻り: (fire_pre, ceil_arr＝型別の天井, isdn_arr＝down 型か)。
    ★fire_pre に「天井 > 現値」は含めない＝その判定はループ側（v38 クランプ後の水準で見る必要があるため）。
    すべて当該バーの確定値のみ（H2）。"""
    sp = recipe["entry"]["split"]
    gap = _vnum(sp["gap_pct"]) / 100.0
    dn_h = _vnum(sp["down_window_hours"])
    age_h = _vnum(sp["max_age_hours"])
    no_age_dn = bool(sp.get("down_no_age", False))
    c = df["close"].to_numpy(float)
    h = df["high"].to_numpy(float)
    build_regime_columns(df, recipe, geo)         # M2-1-6＝build が在れば判定の列を作る（2回目は何もしない）
    ok, _up = _regime_series(df, recipe)          # 監査 4-19＝列の名前はレシピの宣言から読む（直書きをやめた）
    res_lo = geo["res_lo"]
    res_hi = geo["res_hi"]
    n = len(df)
    with np.errstate(invalid="ignore"):
        isdn = np.isfinite(res_lo) & (res_lo > c * (1.0 + gap))          # 下落系＝レジ帯下端が価格の上に gap 超（e37 1460行）
    mbar = max(2, int(round(dn_h * 12)))
    rhdn = pd.Series(h).rolling(mbar, min_periods=2).max().shift(1).to_numpy(float)   # 直近高値（前バーまで＝H2・e37 961行）
    ceil_arr = np.where(isdn, rhdn, res_hi)                              # down=直近高値／flat_up=res_hi（e37 1461行）
    cl = recipe["entry"].get("ceiling") or {}
    if cl.get("flat_up_top") == "range_high":                            # v35（e37 1475〜1483行）: flat_up の天井＝
        if "v35_range_top" not in df.columns:                            # 今のレンジ開始以降の実測高値×(1−tol)
            raise RecipeError("[実行器] v35 の材料列 v35_range_top が実行データに無い（恒等ハーネスが付ける）")
        t35 = df["v35_range_top"].to_numpy(float)
        near = c * (1.0 + ENTRY_OFFSET)                                  # 現値のすぐ上（maker 成立の下限）
        with np.errstate(invalid="ignore"):
            use35 = (~isdn) & np.isfinite(t35) & (t35 > near)
        ceil_arr = np.where(use35, t35, ceil_arr)
        if cl.get("near_fallback"):                                      # v36（e37 1479〜1481行）: t35 が現値以下＝
            use36 = (~isdn) & np.isfinite(t35) & (~use35)                # 上端圏に居る瞬間は現値すぐ上に置く
            ceil_arr = np.where(use36, near, ceil_arr)
    idxn = np.arange(n)
    fi = np.where(~ok, idxn, -1)                                         # range_ok 連続バー数（e37 965-966行）
    age = (idxn - np.maximum.accumulate(fi)).astype(float)
    age_ok = age <= age_h * 12
    if no_age_dn:
        age_ok = age_ok | isdn                                           # v40＝down 型は年齢免除（e37 1491-1492行）
    # 発火の前提（e37 1494行のうち「天井 > 現値」を除いた分＝その判定は v38 クランプ後にループ側で行う）
    fire = ok & np.isfinite(ceil_arr) & age_ok
    if "rearm_delay_bars" in sp:                                         # v56（里程標2・e37 1507行）: uptrend 解除から
        rd = int(_vnum(sp["rearm_delay_bars"]))                          # rd 本未満の若いレンジ窓では flat_up 型を建てない
        up = df["rg5_uptrend"].to_numpy(bool)                            # （down 型は対象外・e37 last_up26＝直近 uptrend バー）
        lastup = np.maximum.accumulate(np.where(up, idxn, -10 ** 9))
        young = (idxn - lastup) < rd
        fire = fire & ~(young & ~isdn)
    return fire, ceil_arr, isdn


def _guards_ok(guards: dict, lv: dict, lim: float, side: str) -> bool:
    """entry_guards（S2 の floor_ok と同じ物理＝手数料床・TP2 が建値の内側・SL が有限）。"""
    if not guards:
        return True
    t2 = guards.get("tp_inside")
    if t2 is not None:
        px = lv.get(t2)
        if px is None or not np.isfinite(px) or not (px < lim if side == "SHORT" else px > lim):
            return False
    t1 = guards.get("fee_floor_vs")
    if t1 is not None:
        floor = _vnum(guards.get("fee_floor", {"const": "SCALP_FLOOR"}))
        px = lv.get(t1)
        gap = (lim - px) if side == "SHORT" else (px - lim)
        if px is None or not np.isfinite(px) or gap < lim * floor:
            return False
    for nm in guards.get("require_finite", []):
        if nm not in lv or not np.isfinite(lv[nm]):
            return False
    return True


def _peak_giveback_level(lv: dict, lot: dict, side: str) -> float | None:
    """v27 型のピーク反転ロックの水準（e37_scalp 1208-1217行と同式・歩6-1 里程標5）。
    武装＝前バーまでの含み益ピークが建値から arm% 以上。水準＝ピーク利益の giveback 分を戻した所
    （下限＝建値フロア＝損ゼロ級）。武装していなければ None（＝この枝は不発）。"""
    pk = lot.get("pk_prev", lot["max_fav"])
    arm = abs(_vnum(lv["arm"])) / 100.0
    gb = _vnum(lv["giveback"])
    fl = abs(_vnum(lv["floor"]))
    avg = lot["avg"]
    gain = (avg - pk) if side == "SHORT" else (pk - avg)
    if not (np.isfinite(gain) and gain >= avg * arm):
        return None
    if side == "SHORT":
        return float(min(pk + gb * gain, avg * (1.0 - fl)))
    return float(max(pk - gb * gain, avg * (1.0 + fl)))


def _fire_key(c: dict) -> str:
    """出口の発火条件1つの鍵＝条件の canonical JSON（97番の設計 v3 やること1）。
    印（_num_src など）は生成器が実行器へ渡す直前に外す（strip_marks）＝鍵に入らない。
    json にできない値（numpy の int64・bool_ など）が混じったら、黙って別の鍵にせず止める。"""
    try:
        return json.dumps(c, sort_keys=True, ensure_ascii=False)
    except TypeError as e:
        raise RecipeError(f"[実行器] 出口の発火条件を鍵にできない（json にできない値が混じっている）: {e}") from None


def _collect_fire_cols(recipe: dict, df: pd.DataFrame, geo: dict, lane: str,
                       qtable: dict | None = None) -> dict:
    """出口 fire の条件を、ループの前に1回だけ「条件ごとの真偽の配列」にする（97番の設計 v3 やること1・2026-08-25）。

    直す前（歩6-1 里程標7）＝材料の生の値の配列を鍵「素の列名」で持ち、_exit_fire_ok が値と数字を1点比較していた
    ＝形（傾き・交差・差・ローソク）を見なかった（97番・60回目に実測で確定）。同じ列に違う pre を掛けた2条件は
    鍵が衝突して先勝ちだった（監査 cp7 実測⑩）。
    いま＝指標の条件（材料の種別が state でないもの・材料の無い candle_dir を含む）は、入口と同じ評価器
    _eval_cond で全バーの真偽の配列にする（評価の式をここに書き写さない＝2か所に同じ式を持たない）。
    玉の状態の条件は玉ごとに値が変わるので配列にせず、種別と名前だけ記録して _exit_fire_ok が1点比較する。
    ★種別は _material_name の1か所で決める（"state" in m で決めない＝監査 cp7b 新1）。
    戻り値＝{"by_key": {鍵: ("bool", 配列) or ("state", 状態の名前)}, "by_id": {id(条件): 鍵}}。
    by_id は同じ辞書をループの中で毎バー json にしないための控え＝鍵の正本は canonical JSON。
    """
    out: dict = {"by_key": {}, "by_id": {}}
    for b in recipe.get("exits") or []:
        fire = b.get("fire")
        if fire is None:
            continue
        conds, _d = _walk(fire)
        for c in conds:
            key = _fire_key(c)
            out["by_id"][id(c)] = key
            if key in out["by_key"]:
                continue
            mats = c.get("material") or []
            kinds = [_material_name(m, lane)[0] for m in mats]
            if kinds and all(k == "state" for k in kinds):
                out["by_key"][key] = ("state", str(mats[0]["state"]))
            else:
                out["by_key"][key] = ("bool", _eval_cond(c, df, geo, lane, qtable))
    return out


def _exit_fire_ok(b: dict, lot: dict, i: int, df: pd.DataFrame, geo: dict, lane: str,
                  fire_cols: dict | None = None) -> bool:
    """出口 fire（材料＝ポジション状態列・on_close 評価）。scope（adds・hold_min・ceil_type）もここで見る。"""
    sc = b.get("scope")
    hold_min = (i - lot["first_idx"]) * 5
    if sc:
        lo, hi = sc.get("adds", [1, 10**9])
        if hi is None:
            hi = 10**9
        if not (lo <= lot["add_count"] <= hi):
            return False
        ct = sc.get("ceil_type")               # 型別の枝（歩6-1＝v27/v47/v53 等は flat_up 限定・down 限定がある）
        if ct is not None and lot.get("ceil_type") != ct:
            return False
        tc = sc.get("trend_caught")            # 里程標9＝上げトレンドに捕まった玉だけに当たる枝（v24/MFE_STALE）
        if tc is not None and bool(lot.get("trend_caught")) != bool(tc):
            return False
        if "hold_min" in sc:
            lo2, hi2 = sc["hold_min"]
            if not (lo2 <= hold_min <= (10**9 if hi2 is None else hi2)):
                return False
    fire = b.get("fire")
    if fire is None:
        return True
    state = {"hold_min": hold_min, "add_count": lot["add_count"],
             "peak_age_bars": i - lot.get("peak_idx", lot["first_idx"]),
             "trend_caught": 1.0 if lot.get("trend_caught") else 0.0}   # 里程標9（1/0・印は uptrend_cut が付ける）
    sgn = -1.0 if lot["side"] == "SHORT" else 1.0
    avg = lot["avg"]
    state["mfe_pct"] = (lot["max_fav"] - avg) / avg * 100.0 * sgn
    state["mfe_prev_pct"] = (lot.get("pk_prev", lot["max_fav"]) - avg) / avg * 100.0 * sgn
    state["mae_pct"] = (lot["max_adv"] - avg) / avg * 100.0 * sgn
    c = float(df["close"].iloc[i])
    state["unreal_pct"] = (c - avg) / avg * 100.0 * sgn
    state["dist_be_pct"] = abs(c - avg) / avg * 100.0

    def _ev(node) -> bool:
        if _is_cond(node):
            # ★97番の設計 v3 やること2（2026-08-25）＝指標の条件は、ループの前に入口と同じ評価器で作った
            #   「全バーの真偽の配列」の i 番目を引くだけ（形はそこで見ている）。玉の状態の条件は、いままでどおり
            #   玉ごとの値と数字の1点比較（値の評価の式は変えない・欠損の既定は104番＝範囲外）。
            #   どちらかは _collect_fire_cols が _material_name で決めて記録した種別で分ける
            #   （直す前の m.get("state") は消した＝検査と実行で種別の規則を2つ持たない）。
            fc = fire_cols or {}
            key = fc.get("by_id", {}).get(id(node)) or _fire_key(node)
            ent = fc.get("by_key", {}).get(key)
            if ent is None:
                raise RecipeError(f"[実行器] 出口 fire の条件が解決されていない（ループの前に _collect_fire_cols を通す）: {key[:120]}")
            kind, payload = ent
            if kind == "bool":
                return bool(payload[i])
            val = state[payload]
            th = _vnum(node.get("value", {}))
            return bool(_side_cmp(val, th, node.get("side")))
        if "not" in node:                          # ★否定（97番の設計 v3 やること2＝入口の _eval_tree と同じ意味）
            return not _ev(node["not"])
        if "all" in node:
            return all(_ev(ch) for ch in node["all"])
        if "any" in node:
            return any(_ev(ch) for ch in node["any"])
        return (not _ev(node["if"])) or _ev(node["then"])
    return bool(_ev(fire))


def run_recipe(df: pd.DataFrame, recipe: dict, limits: dict | None = None,
               samples: dict | None = None, qtable: dict | None = None) -> tuple[list, dict]:
    """レシピを共通の売買ループで走らせ、売買記録（e37._record の行）と検証報告を返す。
    ループの意味論＝設計書 §1〜§7（H5 執行・恒等の対象＝generic_logic_loop と同じ規則）。
    qtable＝分位の解決表（生成器が値決め窓から探索開始時に1回固定して渡す・§5-4・歩4）。"""
    rep = validate_recipe(recipe, limits, samples)
    meta = recipe["meta"]
    side = meta["side"]
    lane = meta.get("lane", "")
    exits = recipe["exits"]
    posz = recipe["position"]
    mode, max_adds = posz["mode"], int(posz["max_adds"])
    guards = recipe.get("entry_guards", {})
    rec_style = recipe.get("record") or {}        # 記録スタイル（恒等レーン専用・validate_recipe が検査済み）
    o = df["open"].to_numpy(float)
    h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float)
    ts = df["ts"].to_numpy()
    atr = df["atr"].to_numpy(float)
    adx = df["adx"].to_numpy(float)
    kk = df["stoch_k"].to_numpy(float)
    res_lo = df["v11_res_lo"].to_numpy(float)
    res_hi = df["v11_res_hi"].to_numpy(float)
    sup_lo = df["v11_sup_lo"].to_numpy(float)
    sup_hi = df["v11_sup_hi"].to_numpy(float)
    mid = df["v11_mid"].to_numpy(float)
    span = res_hi - mid
    with np.errstate(invalid="ignore", divide="ignore"):
        pos_arr = np.where(np.isfinite(span) & (span > 0), (c - mid) / span, np.nan)
        wpct_arr = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), (res_hi - sup_lo) / c * 100.0, np.nan)
    geo = {"res_hi": res_hi, "res_lo": res_lo, "sup_hi": sup_hi, "sup_lo": sup_lo,
           "mid": mid, "W%": wpct_arr, "帯内位置%": pos_arr}
    # ★M2-1-6（2026-08-20 まこさん承認）＝build が在れば、幾何（geo）を組んだ直後・宣言の列を読む前に
    #   判定の列を作る（build の中の普通の条件が W% などの幾何を使えるように、この位置に置いた）。
    build_regime_columns(df, recipe, geo, qtable)
    ok, up = _regime_series(df, recipe)           # 監査 4-19＝列の名前はレシピの宣言から読む（直書きをやめた）
    for _tgt, _m in _swing_specs(recipe):         # v22 アンカー（里程標9）＝直近 m 本の安値／高値
        _k = f"swing:{_tgt}:{_m}"                 # 当該バーは含めない（shift(1)＝H2・e37_scalp 984行と同式）
        if _k in geo:
            continue
        _src = pd.Series(l if _tgt == "low" else h)
        geo[_k] = ((_src.rolling(_m).min() if _tgt == "low" else _src.rolling(_m).max())
                   .shift(1).to_numpy(float))
    is_ceiling = (recipe.get("entry") or {}).get("type") == "ceiling_resting"
    clamp_prev = climb_guard = False
    warn_arr = None
    if is_ceiling:                                # 歩6-1: S1 型＝天井への resting（fire と指値水準を幾何で作る）
        fire, ceil_arr, isdn_arr = _ceiling_fire(recipe, df, geo)
        _cl = (recipe["entry"].get("ceiling") or {})
        clamp_prev = bool(_cl.get("clamp_prev_fill"))     # v38＝前玉より高くは売らない
        climb_guard = bool(_cl.get("climb_guard"))        # v37＝前兆 ∩ 前玉より高い指値なら建てない
        if climb_guard:
            if "v22_warning" not in df.columns:
                raise RecipeError("[実行器] v37 の材料列 v22_warning が実行データに無い（恒等ハーネスが付ける）")
            warn_arr = df["v22_warning"].to_numpy(bool)
    else:
        fire = _entry_fire(recipe, df, geo, qtable)
        ceil_arr = isdn_arr = None
    last_fup_px = None                            # 同一レンジ内の直近 flat_up 約定価格（e37 956行・v37/v38 の基準）
    fire_cols = _collect_fire_cols(recipe, df, geo, lane, qtable)   # 出口 fire の条件ごとの真偽の配列（ループ前に1回・97番）
    pex = recipe.get("position_exits") or {}
    uc = pex.get("uptrend_cut")
    uc_mark = (uc is not None and uc.get("mode") == "mark")   # 里程標9＝確定させず印を付けるだけ
    rb = pex.get("range_break")
    vol_arr = vol_sma_prev = None
    rb_bars = 0
    if rb is not None:                            # v15 構造破れの材料（e37_scalp 858-860行と同式＝当該バー除外の出来高平均）
        vol_arr = df["volume"].to_numpy(float)
        vol_sma_prev = df["volume"].rolling(int(_vnum(rb["vol_n"]))).mean().shift(1).to_numpy(float)
        rb_bars = int(_vnum(rb["bars"]))
    brk_cnt, brk_vol = 0, False
    pre_mfe = bool(pex)                           # 位置の出口がある時＝mfe/mae は e37 と同じ位置（枝の前・全 lot 一括）で更新
    n = len(df)
    trades: list = []
    lots: list = []
    pend = None
    for i in range(1, n):
        if pend is not None:                       # pend 約定（約定バーの次以降＝H2・maker fill）
            el = i - pend["placed_idx"]
            filled = (h[i] >= pend["limit"]) if side == "SHORT" else (l[i] <= pend["limit"])
            if el > TTL:
                pend = None
            elif el >= 1 and filled:
                if mode == "avg" and lots:         # 平均建値へ積み増す（§7・best/worst は保持）
                    p0 = lots[0]
                    tot = p0["size"] + UNIT_LOT
                    p0["avg"] = (p0["avg"] * p0["size"] + pend["limit"] * UNIT_LOT) / tot
                    p0["size"] = tot
                    p0["add_count"] += 1
                    p0["last_fill_idx"] = i
                    p0["lv"] = pend["lv"]          # 積み増しバーの幾何で置き直し（機械出力で見える）
                else:
                    _newlot = {"side": side, "avg": pend["limit"], "size": UNIT_LOT,
                               "add_count": len(lots) + 1 if mode == "separate" else 1,
                               "first_idx": i, "last_fill_idx": i,
                               "atr_entry": atr[i], "adx_entry": adx[i],
                               "k_entry": (np.nan if rec_style.get("k_entry") == "none" else kk[i]),
                               "W_entry": pend["W_pct"],
                               "max_fav": h[i] if side == "LONG" else l[i],
                               "max_adv": l[i] if side == "LONG" else h[i],
                               "pos_frac": pend["pos_frac"], "mid_frac": pend["mid_frac"],
                               "res_zone_pos": np.nan, "ceil_type": pend["ceil_type"],
                               "zone_top": pend.get("zone_top", np.nan),
                               "lv": pend["lv"], "done": set(), "be_lvl": np.nan, "be_dl": -1}
                    if rec_style.get("style") == "s1":
                        # S1 の診断列＝約定バーの幾何で出す（e37_scalp 1066-1075行と同式・net 不関与だが md5 恒等の対象）
                        _lim1 = pend["limit"]
                        _rng1 = (res_hi[i] - sup_hi[i]) if (np.isfinite(res_hi[i]) and np.isfinite(sup_hi[i])) else np.nan
                        _newlot["pos_frac"] = ((_lim1 - sup_hi[i]) / _rng1) if (np.isfinite(_rng1) and _rng1 > 0) else np.nan
                        _newlot["mid_frac"] = ((mid[i] - sup_hi[i]) / _rng1) if (np.isfinite(_rng1) and _rng1 > 0) else np.nan
                        _newlot["res_zone_pos"] = (((_lim1 - res_lo[i]) / (res_hi[i] - res_lo[i]))
                                                   if (np.isfinite(res_lo[i]) and np.isfinite(res_hi[i]) and res_hi[i] > res_lo[i]) else np.nan)
                    if not lots:
                        brk_cnt, brk_vol = 0, False    # position 開始＝破れカウンタ撤去（e37_scalp 1081-1084行）
                    lots.append(_newlot)
                if (clamp_prev or climb_guard) and pend["ceil_type"] == "flat_up":
                    last_fup_px = float(pend["limit"])  # v37/v38 の基準＝直近 flat_up 約定価格（e37 1087-1088行）
                pend = None
        if (clamp_prev or climb_guard) and not ok[i]:
            last_fup_px = None                     # レンジ切れ＝基準リセット（e37 1094-1095行・次のレンジへ持ち越さない）
        if up[i]:                                  # uptrend 発火＝新規停止（保有は SL/TIME が守る）
            pend = None
            if uc is not None:                     # 歩6-1: uptrend 畳み（e37_scalp 1096-1145行の v20 経路）
                if uc_mark:                        # 里程標9＝成行で投げず「捕まった玉」の印を付けて保持（e37 1109-1115行）
                    if not lots:
                        continue                   # 保有なし＝e37 1144-1145行と同じ（以降の処理へ進まない）
                    for lot in lots:
                        if not lot.get("trend_caught"):
                            lot["trend_caught"] = True
                            lot["tc_idx"] = i      # 印が付いた時刻（e37 1113行・v39 の起点＝v39 OFF では読まれない）
                    # ★ここで continue しない＝e37 は lots を keep して以降の Exit ループへ進む（1115行のコメント）
                else:                              # 既定＝保有全 lot を成行で確定（里程標1〜8 の形）
                    for lot in lots:               # mfe/mae は更新前＝e37 と同じ（1096行は 1177行の更新より前）
                        e37._record(trades, lot, c[i], uc["reason"], i, ts)
                    lots = []
                    brk_cnt, brk_vol = 0, False
                    continue                       # e37 1144-1145行＝uptrend バーは以降の処理へ進まない
        if pre_mfe:                                # e37_scalp 1177-1181行＝mfe/mae は枝の前に全 lot 一括更新
            for lot in lots:
                lot["pk_prev"] = lot["max_fav"]    # 前バーまでの含み益ピーク（e37 1179行・同一バー楽観の排除）
                if side == "LONG":
                    lot["max_fav"] = max(lot["max_fav"], h[i])
                    lot["max_adv"] = min(lot["max_adv"], l[i])
                else:
                    lot["max_fav"] = min(lot["max_fav"], l[i])
                    lot["max_adv"] = max(lot["max_adv"], h[i])
        if rb is not None and lots:                # 歩6-1: v15 構造破れ（e37_scalp 1191-1203行・判定関数は e37 のものを再利用）
            _ztop = max(x.get("zone_top", np.nan) for x in lots)
            brk_cnt, brk_vol, _fire_rb = e37.range_break_check_v15(
                c[i], bool(ok[i]), _ztop, vol_arr[i], vol_sma_prev[i], brk_cnt, brk_vol, rb_bars)
            if _fire_rb:
                for lot in lots:
                    e37._record(trades, lot, c[i], rb["reason"], i, ts)
                lots = []
                pend = None
                brk_cnt, brk_vol = 0, False
                continue
        still = []
        for lot in lots:
            if i <= lot["last_fill_idx"]:
                still.append(lot)
                continue
            if not pre_mfe:                        # 位置の出口がある時は上で一括更新済み（e37 と同じ順序）
                lot["pk_prev"] = lot["max_fav"]
                if side == "LONG":
                    lot["max_fav"] = max(lot["max_fav"], h[i])
                    lot["max_adv"] = min(lot["max_adv"], l[i])
                else:
                    lot["max_fav"] = min(lot["max_fav"], l[i])
                    lot["max_adv"] = max(lot["max_adv"], h[i])
            closed = False
            if lot["be_dl"] >= 0:                  # 建値フロア待機（v31 型＝SL→BE→期限の順・§8 行11）
                # ★待機中でも評価する枝（歩6-1 里程標5）＝e37 では v27 が待機ブロックの前にあり、
                #   待機中の玉にも当たる（1208行 v27 → 1218行 SL → 1220行 待機）。印が無い枝は従来どおり飛ばす。
                _wclosed = False
                for bi, b in enumerate(exits):
                    if (not b.get("while_waiting")) or bi in lot["done"]:
                        continue
                    _pl = (b.get("exec") or {}).get("placement") or {}
                    _lvw = _pl.get("level") or {}
                    if _lvw.get("kind") != "peak_giveback":
                        raise RecipeError("[実行器] while_waiting は peak_giveback 枝だけが持てる（歩6-1）")
                    _lvl = _peak_giveback_level(_lvw, lot, side)
                    if _lvl is None:
                        continue
                    _hit = (h[i] >= _lvl) if side == "SHORT" else (l[i] <= _lvl)
                    if _hit and _exit_fire_ok(b, lot, i, df, geo, lane, fire_cols):
                        _px = (max(_lvl, o[i]) if side == "SHORT" else min(_lvl, o[i])) \
                            if _pl.get("pessimistic") else _lvl
                        e37._record(trades, lot, _px, b["reason"], i, ts)
                        _wclosed = True
                        break
                if _wclosed:
                    continue
                slb = next((b for b in exits if b.get("reason") == "SL_FILLED"), None)
                if slb is not None:
                    slv = lot["lv"].get(slb["name"], np.nan)
                    sl_hit = (h[i] >= slv) if side == "SHORT" else (l[i] <= slv)
                    if np.isfinite(slv) and sl_hit:
                        px = max(slv, o[i]) if side == "SHORT" else min(slv, o[i])
                        e37._record(trades, lot, px, "SL_FILLED", i, ts)
                        continue
                be_hit = (l[i] <= lot["be_lvl"]) if side == "SHORT" else (h[i] >= lot["be_lvl"])
                if be_hit:
                    e37._record(trades, lot, lot["be_lvl"], "BE_EXIT", i, ts)
                    continue
                if i >= lot["be_dl"]:
                    e37._record(trades, lot, c[i], "TIME_EXIT", i, ts)
                    continue
                still.append(lot)
                continue
            for bi, b in enumerate(exits):         # 枝リスト＝上から先勝ち（並び順がデータ・§6）
                if bi in lot["done"]:
                    continue
                pl = (b.get("exec") or {}).get("placement") or {}
                _lvs = pl.get("level") or {}
                if pl.get("kind") == "resting" and _lvs.get("kind") == "peak_giveback":
                    # v27 型のピーク反転ロック（歩6-1 里程標5・e37_scalp 1208-1217行と同式）
                    _lvl = _peak_giveback_level(_lvs, lot, side)
                    if _lvl is None:
                        continue                   # 武装していない＝この枝は不発
                    _hit = (h[i] >= _lvl) if side == "SHORT" else (l[i] <= _lvl)
                    if _hit and _exit_fire_ok(b, lot, i, df, geo, lane, fire_cols):
                        _px = (max(_lvl, o[i]) if side == "SHORT" else min(_lvl, o[i])) \
                            if pl.get("pessimistic") else _lvl
                        e37._record(trades, lot, _px, b["reason"], i, ts)
                        closed = True
                        break
                    continue
                if pl.get("kind") == "resting" and _lvs.get("kind") == "shrink":
                    # v13 deadline shrink（歩6-1）＝from 枝の水準から建値フロアへ残り時間比で縮む maker TP
                    # （e37_scalp 1386-1405行と同式・r=1 で from の水準・r=0 で建値フロア）
                    src = lot["lv"].get(_lvs["from"], np.nan)
                    if not np.isfinite(src):
                        continue
                    _tmb = int(_vnum(_lvs["tmax"]))
                    _fl = abs(_vnum(_lvs["floor"]))
                    _bef = lot["avg"] * (1.0 - _fl) if side == "SHORT" else lot["avg"] * (1.0 + _fl)
                    _r = max(0.0, (_tmb - (i - lot["first_idx"])) / _tmb)
                    _lvl = src + (_bef - src) * (1.0 - _r)
                    _hit = (l[i] <= _lvl) if side == "SHORT" else (h[i] >= _lvl)
                    if _hit and _exit_fire_ok(b, lot, i, df, geo, lane, fire_cols):
                        e37._record(trades, lot, _lvl, b["reason"], i, ts)
                        closed = True
                        break
                    continue
                if pl.get("kind") == "resting":
                    lvl = lot["lv"].get(b["name"], np.nan)
                    if not np.isfinite(lvl):
                        continue
                    if pl["fill"] == "adverse":
                        hit = (h[i] >= lvl) if side == "SHORT" else (l[i] <= lvl)
                        px = (max(lvl, o[i]) if side == "SHORT" else min(lvl, o[i])) if pl.get("pessimistic") else lvl
                    else:
                        hit = (l[i] <= lvl) if side == "SHORT" else (h[i] >= lvl)
                        px = lvl
                    if not (hit and _exit_fire_ok(b, lot, i, df, geo, lane, fire_cols)):
                        continue
                    ratio = float(b.get("size_ratio", 1.0))
                    if ratio < 1.0:
                        half = dict(lot)
                        half["size"] = lot["size"] * ratio
                        e37._record(trades, half, px, b["reason"], i, ts)
                        lot["size"] = lot["size"] * (1 - ratio)
                        if b.get("once", True):
                            lot["done"].add(bi)
                        continue                   # 部分決済＝残りは後続の枝を同バーで見る
                    e37._record(trades, lot, px, b["reason"], i, ts)
                    closed = True
                    break
                # on_close 枝（バー確定時に fire を評価）
                if not _exit_fire_ok(b, lot, i, df, geo, lane, fire_cols):
                    continue
                bw = (b.get("exec") or {}).get("be_wait")
                if bw is not None:                 # TIME→建値フロア待機へ移行（on_close→resting・§6）
                    kv = _vnum(bw["level"]["k"])
                    if bw["level"]["k"].get("side_sign") == "profit":
                        kv = abs(kv) * (-1.0 if side == "SHORT" else 1.0)
                    lot["be_lvl"] = lot["avg"] * (1 + kv)
                    lot["be_dl"] = i + int(_vnum(bw["ttl"]))
                    closed = False
                    break                          # このバーは待機開始のみ（S2 恒等＝still へ）
                e37._record(trades, lot, c[i], b["reason"], i, ts)
                closed = True
                break
            if closed:
                continue
            still.append(lot)
        lots = still
        # 帯の物理ゲート＝range_ok と mid の有限だけを課す（歩6-1 で res_hi/sup_lo の有限要件を外した＝
        # L1 は res 帯が無いバーでも建てる実装のため。res/sup の有限は、実際に使う側＝条件（帯内位置% は
        # res_hi 依存で na=fail）と placement の解決＋require_finite ガード（SL は sup_lo/res_hi 依存）が課す。
        # S2 恒等の非退行は --identity の md5 で機械確認（緩和はこの依存関係により S2 の挙動を変えない）。
        band_ok = ok[i] and np.isfinite(mid[i])
        can_add = (len(lots) < max_adds) if mode == "separate" else \
            (not lots or (lots[0]["add_count"] < max_adds and (posz.get("add_trigger") or {}).get("kind") == "resignal"))
        if pex and not lots and brk_cnt:
            brk_cnt, brk_vol = 0, False            # position 終了＝破れカウンタ撤去（e37_scalp 1432-1433行）
        _fire_i = bool(fire[i])
        _lim_c = np.nan
        if is_ceiling and _fire_i:
            _lim_c = float(ceil_arr[i])
            if clamp_prev and (not isdn_arr[i]) and last_fup_px is not None \
                    and np.isfinite(_lim_c) and _lim_c > last_fup_px:
                _lim_c = float(last_fup_px)        # v38（e37 1484-1487行）＝前玉より高くは売らない
            if not (np.isfinite(_lim_c) and _lim_c > c[i]):
                _fire_i = False                    # e37 1494行の「天井が現在価格の上」
            elif (climb_guard and (not isdn_arr[i]) and warn_arr[i]
                  and last_fup_px is not None and _lim_c > last_fup_px):
                _fire_i = False                    # v37（e37 1496-1499行）＝前兆 ∩ 前玉より高い指値は建てない
        if (not up[i]) and pend is None and can_add and band_ok and _fire_i:
            if is_ceiling:                         # S1 型＝指値は型別の天井（e37_scalp 1502行・close±offset ではない）
                lim = _lim_c
                w_in = res_lo[i] - sup_hi[i]       # 帯の内側の隙間（e37_scalp 1513行 w_px）
                if not (np.isfinite(w_in) and w_in > 0):
                    continue                       # e37_scalp 1542行＝幾何不成立は建てない
            else:
                lim = c[i] * (1 + ENTRY_OFFSET) if side == "SHORT" else c[i] * (1 - ENTRY_OFFSET)
            lv = _resolve_levels(exits, i, lim, side, geo, lane)
            if _guards_ok(guards, lv, lim, side):
                W = max(res_hi[i] - sup_lo[i], 1e-9)
                if rec_style.get("w_entry") == "zone":   # L1 の W_entry＝同じ側の帯幅（run_long_support 1634行と同式）
                    Wr = max((res_hi[i] - res_lo[i]) if side == "SHORT" else (sup_hi[i] - sup_lo[i]), 1e-9)
                elif is_ceiling:
                    Wr = res_lo[i] - sup_hi[i]     # S1 の W_entry＝帯の内側の隙間（e37_scalp 1550行）
                else:
                    Wr = W
                isdn = bool(isdn_arr[i]) if is_ceiling else \
                    bool(np.isfinite(res_lo[i]) and res_lo[i] > c[i] * (1.0 + GAP_DIAG))
                pend = {"limit": lim, "placed_idx": i, "lv": lv,
                        "W_pct": Wr / c[i] * 100.0, "ceil_type": "down" if isdn else "flat_up",
                        "zone_top": res_hi[i],
                        "pos_frac": ((lim - sup_lo[i]) / W) if W > 0 else np.nan,
                        "mid_frac": ((mid[i] - sup_lo[i]) / W) if W > 0 else np.nan}
    for lot in lots:
        e37._record(trades, lot, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    for r in trades:
        r["logic"] = meta["logic_id"]
    return trades, rep


# ══ ③ 恒等検収（設計書 §8・fix_map 歩3 の検収の定義）════════════════════════════════
def identity_recipe() -> dict:
    p = RECIPE_DIR / "identity_s2_legacy.json"
    return json.loads(p.read_text(encoding="utf-8"))


def engine_params_from_recipe(recipe: dict) -> tuple[dict, dict, int]:
    """恒等レシピ → 現行 S2 の引数を機械で導出（両側が同じ値を共有＝値のずれの物理封鎖）。"""
    conds, _d = _walk(recipe["entry"]["connective"])
    by_role = {c["role"]: c for c in conds}
    ep = {"pos_min": by_role["location"]["value"]["legacy"], "confirm": "stoch_dc",
          "confirm_htf": "roc24_2h", "th_roc24_2h": by_role["env"]["value"]["legacy"],
          "confirm_vol": "volr20_15m", "th_volr20_15m": by_role["sufficiency"]["value"]["legacy"],
          "ceil_filter": None}
    bx = {b["name"]: b for b in recipe["exits"]}
    xp = {"tp1_frac": bx["TP1"]["exec"]["placement"]["level"]["frac"]["legacy"],
          "tp2_target": bx["TP2"]["exec"]["placement"]["level"]["target"],
          "sl_zone_k": bx["SL"]["exec"]["placement"]["level"]["k"]["legacy"],
          "tmax_bars": int(bx["TIME"]["fire"]["all"][0]["value"]["n"]) // 5,
          "be_wait": 1 if bx["TIME"]["exec"].get("be_wait") else 0}
    return ep, xp, int(recipe["position"]["max_adds"])


def _sentinel_df() -> pd.DataFrame:
    """番人用の合成5分足（実データを使わない＝累積の試行を汚さない）。

    バー17 で『保有30分の TIME 発火』と『SL 触り』を同時に起こす形にしてある
    （枝順の番人が運任せにならないため）。監査 4-19 の番人⑤ もこのデータを使う。
    """
    n = 60
    t0, tfill, tconf = 10, 11, 17
    idx = pd.date_range("2024-05-01", periods=n, freq="5min")
    c = np.full(n, 106.0)
    o = np.full(n, 106.0)
    h = np.full(n, 106.05)
    l = np.full(n, 105.9)
    h[tfill] = 106.2                               # pend 約定（limit=106×(1+offset)）
    h[tconf] = 131.0                               # SL(=130) 触り ∩ TIME(保有30分) の競合バー
    k = np.full(n, 50.0)
    k[t0:] = 40.0                                  # t0 でデッドクロス（1回だけ）
    d = np.full(n, 45.0)
    return pd.DataFrame({"ts": idx, "open": o, "high": h, "low": l, "close": c, "volume": 1.0,
                         "atr": 1.0, "adx": 20.0, "stoch_k": k, "e38_stoch_d": d,
                         "rsi9": 50.0, "dev_z": 0.0,
                         "range_ok_rg5": True, "rg5_uptrend": False,
                         "v11_res_hi": 110.0, "v11_res_lo": 109.0, "v11_sup_hi": 91.0,
                         "v11_sup_lo": 90.0, "v11_mid": 100.0,
                         "e38_htf_roc24_2h": 0.0, "e38_vol_volr20_15m": 2.0})


def _ordering_sentinel() -> bool:
    """番人＝枝順（exits の並び）が結果を変えることを、競合バーを必ず含む合成データで機械確認する。
    実データの窓では TIME と SL が同じバーで競合するとは限らない（短窓で実測＝競合ゼロだと差が出ない）
    ため、番人は運任せにしない＝バー17で『保有30分の TIME 発火』と『SL 触り』を同時に起こす。
    [TIME,SL] の順＝建値フロア待機へ → 後で BE_EXIT ／ [SL,TIME] の順＝その場で SL_FILLED ＝ md5 が変わる。"""
    df = _sentinel_df()
    recipe = identity_recipe()
    t_a, _r = run_recipe(df, recipe)
    swapped = json.loads(json.dumps(recipe))
    ex = swapped["exits"]
    ti = next(i for i, b in enumerate(ex) if b["name"] == "TIME")
    si = next(i for i, b in enumerate(ex) if b["name"] == "SL")
    ex[ti], ex[si] = ex[si], ex[ti]
    t_b, _r2 = run_recipe(df, swapped)
    ha = hashlib.md5(pd.DataFrame(t_a).to_csv(index=False).encode()).hexdigest()
    hb = hashlib.md5(pd.DataFrame(t_b).to_csv(index=False).encode()).hexdigest()
    ra = [x["exit_reason"] for x in t_a]
    rb = [x["exit_reason"] for x in t_b]
    print(f"[番人 枝順入れ替え・合成競合バー] [TIME,SL]={ra} / [SL,TIME]={rb} → "
          f"{'✅ 不一致（枝順が効いている）' if ha != hb else '❌ 一致（枝順が死んでいる）'}")
    return ha != hb


def _md5_trades(trades: list, start, end) -> tuple[str, int]:
    t = pd.DataFrame(trades)
    if len(t):
        et = pd.to_datetime(t["entry_time"])
        t = t[(et >= start) & (et < end)].reset_index(drop=True)
    return hashlib.md5(t.to_csv(index=False).encode()).hexdigest(), len(t)


def run_identity(quick: bool = False) -> int:
    import periods
    from tuner_adapters import e38 as ad
    import engine_tuner as tuner
    s, e = periods.SEARCH_START, periods.SEARCH_END
    if quick:
        s, e = periods.SEARCH_START, periods.SEARCH_START + pd.Timedelta(days=90)
    assert s >= periods.SEARCH_START and e <= periods.SEARCH_END, "恒等は値決め窓の中だけ（採点窓不使用）"
    print(f"[恒等検収] 窓 {s.date()}〜{(e - pd.Timedelta('1D')).date()}（値決め窓の中・採点はしない・CSV は書かない）")
    (dfp,) = tuner.load_windows_cached(ad, [(s, e)], tuner.WARM, use_cache=not quick)
    recipe = identity_recipe()
    ep, xp, max_lots = engine_params_from_recipe(recipe)
    print(f"[恒等検収] レシピ→エンジン引数（機械導出）: entry={ep} / exit={xp} / max_lots={max_lots}")
    ng = 0
    # 恒等1: separate 形＝現行 S2 と md5 完全一致（入口と出口の両方）
    t_ref = parts.generic_logic_loop(dfp, "pullback_short", ep, xp, max_lots=max_lots,
                                     logic_id=recipe["meta"]["logic_id"])
    for r in t_ref:
        r["logic"] = recipe["meta"]["logic_id"]
    h_ref, n_ref = _md5_trades(t_ref, s, e)
    t_new, rep = run_recipe(dfp, recipe)
    h_new, n_new = _md5_trades(t_new, s, e)
    same = (h_ref == h_new)
    print(f"[恒等1 separate] 現行 S2: {n_ref} 行 md5 {h_ref}")
    print(f"[恒等1 separate] レシピ実行器: {n_new} 行 md5 {h_new} → {'✅ 完全一致' if same else '❌ 不一致'}")
    tr = pd.DataFrame(t_ref)
    if len(tr):
        et_r = pd.to_datetime(tr["entry_time"])
        cnt = tr[(et_r >= s) & (et_r < e)]["exit_reason"].value_counts().to_dict()
        print(f"[恒等1 separate] 出口理由の内訳（入口と出口の両方が恒等の対象）: {cnt}")
    print(f"[検証器の報告] 経路 {rep['経路数']} / 条件 {rep['条件数']} / 触れた列 {rep['触れた列']}")
    print(f"[検証器の報告] legacy 使用 {len(rep['legacy使用'])} 件（恒等レーン）/ 値待ち {rep['値待ち']}")
    ng += 0 if same else 1
    # 番人: 枝順を入れ替えたら不一致になること（先勝ち＝順番はデータ、の実証・合成競合バーで確定判定）
    ng += 0 if _ordering_sentinel() else 1
    swapped = json.loads(json.dumps(recipe))
    exits = swapped["exits"]
    ti = next(i for i, b in enumerate(exits) if b["name"] == "TIME")
    si = next(i for i, b in enumerate(exits) if b["name"] == "SL")
    exits[ti], exits[si] = exits[si], exits[ti]
    t_sw, _rep2 = run_recipe(dfp, swapped)
    h_sw, _n_sw = _md5_trades(t_sw, s, e)
    print(f"[参考 実データで枝順入れ替え] TIME↔SL: md5 {h_sw}"
          f"（{'不一致＝この窓に競合バーあり' if h_sw != h_new else '一致＝この窓には TIME∩SL の競合バーが無い（番人は合成データで確認済み）'}）")
    # 恒等2（R14）: max_adds=1 で separate と avg が現行 S2（max_lots=1）と3者一致
    t_ref1 = parts.generic_logic_loop(dfp, "pullback_short", ep, xp, max_lots=1,
                                      logic_id=recipe["meta"]["logic_id"])
    for r in t_ref1:
        r["logic"] = recipe["meta"]["logic_id"]
    h_ref1, n1 = _md5_trades(t_ref1, s, e)
    r_sep = json.loads(json.dumps(recipe))
    r_sep["position"]["max_adds"] = 1
    h_sep1, _ = _md5_trades(run_recipe(dfp, r_sep)[0], s, e)
    r_avg = json.loads(json.dumps(recipe))
    r_avg["position"] = {"mode": "avg", "max_adds": 1, "add_trigger": {"kind": "resignal"}, "unit": UNIT_LOT}
    h_avg1, _ = _md5_trades(run_recipe(dfp, r_avg)[0], s, e)
    ok14 = (h_ref1 == h_sep1 == h_avg1)
    print(f"[恒等2 R14] 現行(max_lots=1) {h_ref1} / separate形 {h_sep1} / avg形 {h_avg1}"
          f"（{n1} 行）→ {'✅ 3者一致' if ok14 else '❌ 不一致'}")
    ng += 0 if ok14 else 1
    # R14 の実証: 出口の枝が積み増し回数で実際に切り替わること（avg・adds ゲート・売買記録で確認）
    r_demo = json.loads(json.dumps(recipe))
    r_demo["position"] = {"mode": "avg", "max_adds": 3, "add_trigger": {"kind": "resignal"}, "unit": UNIT_LOT}
    for b in r_demo["exits"]:
        if b["name"] == "TIME":
            b["scope"] = {"adds": [1, 1]}
    r_demo["exits"].insert(0, {
        "name": "TIME_ADDED", "reason": "TIME_EXIT",
        "fire": {"all": [{"role": "env", "form": "level", "material": [{"state": "hold_min"}],
                          "side": "above", "value": {"n": 60}}]},
        "exec": {"method": "taker", "placement": {"kind": "on_close"}},
        "scope": {"adds": [2, 99]}, "size_ratio": 1.0})
    t_demo, _rep3 = run_recipe(dfp, r_demo)
    td = pd.DataFrame(t_demo)
    if len(td):
        et = pd.to_datetime(td["entry_time"])
        td = td[(et >= s) & (et < e)]
        pivot = td.groupby(["add_count", "exit_reason"]).size().unstack(fill_value=0)
        print("[R14 実証] avg 形（max_adds=3・TIME 枝を adds でゲート）の 出口×積み増し回数:")
        print(pivot.to_string())
        multi = td[td["add_count"] >= 2]
        print(f"[R14 実証] 積み増し2回以上の玉 {len(multi)} 行（枝の切り替わりが売買記録に出ている）")
    print(f"\n[恒等検収まとめ] {'✅ 全部一致' if ng == 0 else f'❌ 不一致 {ng} 件'}")
    return ng


# ══ 材料列の付け足し（歩6・監査 4-17 の接続・まこさん GO 2026-08-02）════════════════════════
#   ★これまで、この処理は恒等ハーネスの中に埋まっていた（run_identity_s1 と run_identity_l1）。
#     engine_tuner の接続ファイルからも同じ列が要るので、1本の関数へ切り出した。
#     切り出しの検収＝恒等の md5 が切り出しの前後で1文字も変わらないこと（値は1つも変えていない）。
#   ★知らない材料列が在れば止める（fail-closed）＝列が無いまま黙って走らせない。
_LEGACY_COL_SOURCE = {                      # 材料列の名前 → それを作る処理の名前
    "e37_v59_di14": "v59", "e37_v59_kijun26": "v59",
    "e37_v47_rsi9_15m": "v47", "e37_v47_bb2": "v47",
    "e37_l1_in_sup": "l1", "e37_l1_isdn": "l1",
}


def legacy_cols_in(recipe: dict) -> set:
    """レシピの中で使っている legacy 材料列の名前を全部拾う（入れ子の中まで）。"""
    found: set = set()

    def walk(node):
        if isinstance(node, dict):
            v = node.get("legacy_col")
            if isinstance(v, str):
                found.add(v)
            for x in node.values():
                walk(x)
        elif isinstance(node, list):
            for x in node:
                walk(x)

    walk(recipe)
    return found


def source_logic(recipe: dict) -> dict:
    """レシピの元になった設定（e38_logics.json のロジック）＝値の正本。レシピに数字を二重化しない。"""
    from tuner_adapters import e38 as ad
    lid = str(recipe["meta"]["logic_id"])
    src = lid[:-2] if lid.endswith("ID") else lid
    lg = next((x for x in ad.config()["logics"] if x["id"] == src), None)
    if lg is None:
        raise RecipeError(f"[実行器] レシピ {lid} の元になる設定 {src} が e38_logics.json に無い")
    return lg


def attach_recipe_columns(dfp: pd.DataFrame, recipe: dict) -> pd.DataFrame:
    """レシピが要る材料列だけを付けて返す（要らなければそのまま返す）。

    付ける順番は恒等ハーネスと同じ＝天井の材料（v35・v37）→ v59 → v47 → L1。
    列を足すだけなので順番は値に影響しないが、切り出し前と同じにして差分をゼロにする。
    """
    out = dfp
    cl = ((recipe.get("entry") or {}).get("ceiling") or {})
    if cl.get("flat_up_top") == "range_high" and "v35_range_top" not in out.columns:
        out = out.copy()
        out["v35_range_top"] = e37._v35_range_top(out)    # v35＝今のレンジ開始以降の実測高値×(1−tol)
    if cl.get("climb_guard") and "v22_warning" not in out.columns:
        out = e37.v22_uptrend_warning(out)                # v37＝uptrend 前兆フラグ（確定15分足のみ＝H2）
    need = legacy_cols_in(recipe)
    unknown = sorted(n for n in need if n not in _LEGACY_COL_SOURCE and n not in out.columns)
    if unknown:
        raise RecipeError(f"[実行器] レシピが使う材料列の作り方が登録されていない: {unknown}"
                          "（_LEGACY_COL_SOURCE に付け方を登録すること）")
    src = {_LEGACY_COL_SOURCE[n] for n in need if n in _LEGACY_COL_SOURCE}
    if "v59" in src and "e37_v59_di14" not in out.columns:
        out = _attach_v59_cols(out)
    if "v47" in src and "e37_v47_rsi9_15m" not in out.columns:
        out = _attach_v47_cols(out)
    if "l1" in src and "e37_l1_in_sup" not in out.columns:
        out = _l1_attach_legacy_cols(out, float(source_logic(recipe)["params"]["gap_pct"]),
                                     regime_cols(recipe)[0])
    return out


# ══ ③-2 恒等検収 L1（歩6-1・まこさん GO 2026-08-02＝採用中 L1 をレシピで書き写す・fix_map 歩6）═════
def identity_l1_recipe() -> dict:
    p = RECIPE_DIR / "identity_l1_legacy.json"
    return json.loads(p.read_text(encoding="utf-8"))


def l1_engine_params(recipe: dict) -> tuple[int, float, int]:
    """恒等レシピ → 現行 L1（e37.run_long_support）の引数を機械で導出（両側が同じ値を共有）。"""
    bx = {b["name"]: b for b in recipe["exits"]}
    tmax = int(bx["TIME"]["fire"]["all"][0]["value"]["n"]) // 5
    sl_k = float(bx["SL"]["exec"]["placement"]["level"]["k"]["legacy"])
    return tmax, sl_k, int(recipe["position"]["max_adds"])


def _l1_attach_legacy_cols(dfp: pd.DataFrame, gap_pct: float, entry_col: str) -> pd.DataFrame:
    """L1 恒等用の legacy 材料列（run_long_support 1594-1595 / 1636 行と同式・当該バーのみ＝H2）。

    entry_col＝玉を建ててよいバーを表す列の名前（監査 4-19＝レシピの宣言から受け取る・直書きをやめた）。
    """
    if entry_col not in dfp.columns:
        raise RecipeError(f"[相場の列が無い] L1 の材料列を作れない: {entry_col} がデータにありません。")
    ok = dfp[entry_col].to_numpy(bool)
    sup_hi = dfp["v11_sup_hi"].to_numpy(float)
    sup_lo = dfp["v11_sup_lo"].to_numpy(float)
    res_lo = dfp["v11_res_lo"].to_numpy(float)
    lo = dfp["low"].to_numpy(float)
    cl = dfp["close"].to_numpy(float)
    in_sup = ok & np.isfinite(sup_hi) & np.isfinite(sup_lo) & (lo <= sup_hi) & (cl > sup_lo)
    isdn = np.isfinite(res_lo) & (res_lo > cl * (1.0 + gap_pct / 100.0))
    out = dfp.copy()
    out["e37_l1_in_sup"] = in_sup.astype(float)
    out["e37_l1_isdn"] = isdn.astype(float)
    return out


def run_identity_l1(quick: bool = False) -> int:
    """L1 恒等＝レシピ実行器と現行 L1（e37.run_long_support・v59d_164 の L1 側と同じ引数）の md5 比較。
    採点はしない・売買記録CSVは書かない・score.py は呼ばない（メモリ上の比較・値決め窓の中だけ）。"""
    import periods
    from tuner_adapters import e38 as ad
    import engine_tuner as tuner
    s, e = periods.SEARCH_START, periods.SEARCH_END
    if quick:
        s, e = periods.SEARCH_START, periods.SEARCH_START + pd.Timedelta(days=90)
    assert s >= periods.SEARCH_START and e <= periods.SEARCH_END, "恒等は値決め窓の中だけ（採点窓不使用）"
    print(f"[恒等検収 L1] 窓 {s.date()}〜{(e - pd.Timedelta('1D')).date()}（値決め窓の中・採点はしない・CSV は書かない）")
    ng = 0
    # 値の出所＝e38_logics.json の L1（v59d_164 恒等移植の正本）。レシピと食い違えば止める（写し間違いの物理封鎖）
    lg = next(x for x in ad.config()["logics"] if x["id"] == "L1")
    pr = lg.get("params", {})
    gp = float(pr["gap_pct"])
    recipe = identity_l1_recipe()
    tmax, sl_k, max_lots = l1_engine_params(recipe)
    checks = [
        ("tmax_bars", int(pr["tmax_bars"]), tmax),
        ("sl_zone_k", float(pr["sl_zone_k"]), sl_k),
        ("max_lots", int(pr["max_lots"]), max_lots),
        ("flat_up_only", True, bool(lg["engine_flags"].get("v57_long_flat_up_only"))),
        ("sl_pct(null)", None, lg["engine_flags"].get("v57_long_sl_pct")),
        ("vol_gate(null)", None, lg["engine_flags"].get("v57_long_vol_gate")),
    ]
    for nm, want, got in checks:
        okc = (want == got)
        print(f"[恒等検収 L1] 値の照合 {nm}: e38_logics={want} / レシピ側={got} → {'✅' if okc else '❌'}")
        ng += 0 if okc else 1
    (dfp,) = tuner.load_windows_cached(ad, [(s, e)], tuner.WARM, use_cache=not quick)
    # 現行 L1（v59d_164 の L1 側と同じ引数＝run_long_support を直接呼ぶ・E37 本体は無変更）
    t_ref = e37.run_long_support(dfp, max_lots=int(pr["max_lots"]), tmax=int(pr["tmax_bars"]),
                                 sl_pct=None, vol_gate=None, gap_pct=gp, flat_up_only=True)
    for r in t_ref:
        r["logic"] = recipe["meta"]["logic_id"]
    h_ref, n_ref = _md5_trades(t_ref, s, e)
    dfl = attach_recipe_columns(dfp, recipe)      # 歩6 で切り出した共通処理（中身は _l1_attach_legacy_cols）
    t_new, rep = run_recipe(dfl, recipe)
    h_new, n_new = _md5_trades(t_new, s, e)
    same = (h_ref == h_new)
    print(f"[恒等 L1] 現行 L1（run_long_support）: {n_ref} 行 md5 {h_ref}")
    print(f"[恒等 L1] レシピ実行器: {n_new} 行 md5 {h_new} → {'✅ 完全一致' if same else '❌ 不一致'}")
    tr = pd.DataFrame(t_ref)
    if len(tr):
        et_r = pd.to_datetime(tr["entry_time"])
        cnt = tr[(et_r >= s) & (et_r < e)]["exit_reason"].value_counts().to_dict()
        print(f"[恒等 L1] 出口理由の内訳（入口と出口の両方が恒等の対象）: {cnt}")
    print(f"[検証器の報告] 経路 {rep['経路数']} / 条件 {rep['条件数']} / 触れた列 {rep['触れた列']}")
    print(f"[検証器の報告] legacy 使用 {len(rep['legacy使用'])} 件（恒等レーン）/ 値待ち {rep['値待ち']}")
    ng += 0 if same else 1
    print(f"\n[恒等検収 L1 まとめ] {'✅ 全部一致' if ng == 0 else f'❌ 不一致 {ng} 件'}")
    return ng


# ══ ③-3 恒等検収 S1 里程標1（歩6-1 後半・まこさん指示 2026-08-02「S1 の書き写しを続けて」）═════════
def identity_s1_recipe() -> dict:
    p = RECIPE_DIR / "identity_s1_legacy.json"
    return json.loads(p.read_text(encoding="utf-8"))


def s1_engine_params(recipe: dict) -> dict:
    """恒等レシピ → 現行 S1（e37.run_continuous_v11）の里程標1 構成を機械で導出（両側が同じ値を共有）。"""
    sp = recipe["entry"]["split"]
    bx = {b["name"]: b for b in recipe["exits"]}
    rbx = recipe["position_exits"]["range_break"]
    tmax_sh = int(_vnum(bx["SHRINK"]["exec"]["placement"]["level"]["tmax"]))
    tmax_ti = int(bx["TIME"]["fire"]["all"][0]["value"]["n"]) // 5
    if tmax_sh != tmax_ti:
        raise SystemExit(f"[S1 恒等] SHRINK.tmax={tmax_sh} と TIME={tmax_ti}本 が食い違う（e37 は同じ tmax 48）")
    return {"gap": _vnum(sp["gap_pct"]), "down_hours": _vnum(sp["down_window_hours"]),
            "max_age_hours": _vnum(sp["max_age_hours"]), "down_no_age": bool(sp.get("down_no_age", False)),
            "rearm_bars": (int(_vnum(sp["rearm_delay_bars"])) if "rearm_delay_bars" in sp else None),
            "ceiling": (recipe["entry"].get("ceiling") or {}),
            "be_wait": ((bx["TIME"].get("exec") or {}).get("be_wait")),
            "peaklock": (((bx["PEAKLOCK"].get("exec") or {}).get("placement") or {}).get("level")
                         if "PEAKLOCK" in bx else None),
            "fastcut": (bx["FASTCUT"] if "FASTCUT" in bx else None),
            "v59": ({"down": bx["V59DOWN"], "flat": bx["V59FLAT"]}
                    if ("V59DOWN" in bx and "V59FLAT" in bx) else None),
            "mtfcut": (bx["MTFCUT"] if "MTFCUT" in bx else None),
            # 里程標9＝v22 アンカー／v24 の捕まった玉の利確／v48 の失速切りの建値待ち。
            "anchor": (bx["TP2"]["exec"]["placement"]["level"]
                       if bx["TP2"]["exec"]["placement"]["level"].get("kind") == "swing" else None),
            "tcaught": (bx["TCTP"] if "TCTP" in bx else None),
            "stale": (bx["MFESTALE"] if "MFESTALE" in bx else None),
            "uptrend_mark": (recipe["position_exits"]["uptrend_cut"].get("mode") == "mark"),
            "sl_far": _vnum(bx["SL"]["exec"]["placement"]["level"]["k"]),
            "tmax": tmax_sh, "break_bars": int(_vnum(rbx["bars"])), "vol_n": int(_vnum(rbx["vol_n"])),
            "max_lots": int(recipe["position"]["max_adds"])}


def _attach_v59_cols(dfp: pd.DataFrame) -> pd.DataFrame:
    """v59 の材料列（歩6-1 里程標7）＝e37_scalp 1026-1044行の式をそのまま写す。
    ★写しが正しいことは恒等そのものが守る＝両側を毎回走らせて md5 を比べるので、式がずれれば不一致で止まる。
    （e37 側はこの式が run_continuous_v11 の中に埋まっていて、関数として呼び出せないため写している）。"""
    c = dfp["close"].to_numpy(float)
    h = dfp["high"].to_numpy(float)
    l = dfp["low"].to_numpy(float)
    cs, hs, ls = pd.Series(c), pd.Series(h), pd.Series(l)
    up, dn = hs.diff(), -ls.diff()
    p = pd.Series(np.where((up > dn) & (up > 0), up, 0.0))
    m = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0))
    tr = pd.concat([hs - ls, (hs - cs.shift()).abs(), (ls - cs.shift()).abs()], axis=1).max(axis=1)
    atr14 = tr.ewm(alpha=1.0 / 14, adjust=False).mean()
    pdi14 = 100 * p.ewm(alpha=1.0 / 14, adjust=False).mean() / atr14
    mdi14 = 100 * m.ewm(alpha=1.0 / 14, adjust=False).mean() / atr14
    kij26 = (hs.rolling(26).max() + ls.rolling(26).min()) / 2.0
    out = dfp.copy()
    out["e37_v59_di14"] = (pdi14 - mdi14).to_numpy(float)
    out["e37_v59_kijun26"] = ((cs / kij26) - 1.0).to_numpy(float) * 100.0
    return out


def _attach_v47_cols(dfp: pd.DataFrame) -> pd.DataFrame:
    """v47 の材料列（歩6-1 里程標8）＝e37_scalp 993-1002行（15分足 RSI9）と 1011-1012行（BB+2σ）の写し。
    ★15分足 RSI9 は「閉じた15分バーの次の5分バーから有効」＝当該バー内の値は使わない（H2）。
    ★写しの正しさは恒等そのものが守る（両側を毎回走らせて md5 を比べる）。"""
    ts = dfp["ts"].to_numpy()
    c = dfp["close"].to_numpy(float)
    n = len(dfp)
    min15 = (pd.to_datetime(pd.Series(ts)).dt.minute % 15) == 10   # 15分足を閉じる5分バー
    c15 = pd.Series(c)[min15.to_numpy()]
    d15 = c15.diff()
    u15 = d15.clip(lower=0).ewm(alpha=1.0 / 9, adjust=False).mean()
    n15 = (-d15.clip(upper=0)).ewm(alpha=1.0 / 9, adjust=False).mean()
    r15 = 100 - 100 / (1 + u15 / n15.replace(0, np.nan))
    tmp = np.full(n, np.nan)
    tmp[c15.index.to_numpy()] = r15.to_numpy(float)
    cs = pd.Series(c)
    sm20, sd20 = cs.rolling(20).mean(), cs.rolling(20).std()
    out = dfp.copy()
    out["e37_v47_rsi9_15m"] = pd.Series(tmp).shift(1).ffill().to_numpy(float)
    out["e37_v47_bb2"] = (cs > sm20 + 2 * sd20).to_numpy(float)     # 1=BB+2σ 上抜け／0=それ以外
    return out


def run_identity_s1(quick: bool = False) -> int:
    """S1 里程標1 の恒等＝レシピ実行器と現行 run_continuous_v11（同じ構成・引数はレシピから機械導出）の md5 比較。
    構成＝v12+v13+v18+v20(RG-v5)+v26 切り分け(+v40)＝v59d の入口骨格と v18 基本出口。残りレバーは次の里程標。
    採点はしない・売買記録CSVは書かない・score.py は呼ばない（メモリ上の比較・値決め窓の中だけ）。"""
    import periods
    from tuner_adapters import e38 as ad
    import engine_tuner as tuner
    s, e = periods.SEARCH_START, periods.SEARCH_END
    if quick:
        s, e = periods.SEARCH_START, periods.SEARCH_START + pd.Timedelta(days=90)
    assert s >= periods.SEARCH_START and e <= periods.SEARCH_END, "恒等は値決め窓の中だけ（採点窓不使用）"
    print(f"[恒等検収 S1]窓 {s.date()}〜{(e - pd.Timedelta('1D')).date()}（値決め窓の中・採点はしない・CSV は書かない）")
    ng = 0
    recipe = identity_s1_recipe()
    prm = s1_engine_params(recipe)
    # 値の照合＝e38_logics.json の S1（v59d_164 恒等移植の正本）と、実行器の定数（構造破れの窓）
    lg = next(x for x in ad.config()["logics"] if x["id"] == "S1")
    ef = lg["engine_flags"]
    checks = [
        ("v26_gap", float(ef["v26_gap"]), prm["gap"]),
        ("v26_down_hours", float(ef["v26_down_hours"]), prm["down_hours"]),
        ("v26_max_age_hours", float(ef["v26_max_age_hours"]), prm["max_age_hours"]),
        ("v40_down_no_age", bool(ef["v40_down_no_age"]), prm["down_no_age"]),
        ("v26_split_ceiling", True, bool(ef["v26_split_ceiling"])),
        ("break_bars(V15)", int(e37.V15_BREAK_BARS), prm["break_bars"]),
        ("vol_n(V15)", int(e37.V15_BREAK_VOL_N), prm["vol_n"]),
    ]
    if prm["rearm_bars"] is not None:              # 里程標2＝v56（e38_logics S1 の v56_rearm_delay が正本）
        checks.append(("v56_rearm_delay", True, bool(ef.get("v56_rearm_delay"))))
        checks.append(("V56_REARM_BARS", int(e37.V56_REARM_BARS), prm["rearm_bars"]))
    _cl = prm["ceiling"]                           # 里程標3＝クランプ群（レシピに書いた分だけ現行側も ON にする）
    if _cl.get("flat_up_top") == "range_high":
        checks.append(("v35_flatup_range", True, bool(ef.get("v35_flatup_range"))))
    if _cl.get("near_fallback"):
        checks.append(("v36_flatup_near", True, bool(ef.get("v36_flatup_near"))))
    if _cl.get("clamp_prev_fill"):
        checks.append(("v38_flatup_clamp", True, bool(ef.get("v38_flatup_clamp"))))
    if _cl.get("climb_guard"):
        checks.append(("v37_flatup_climb", True, bool(ef.get("v37_flatup_climb"))))
    if prm["be_wait"] is not None:                 # 里程標4＝v31（TIME 満了を成行でなく建値フロアの resting maker へ）
        checks.append(("v31_time_be", True, bool(ef.get("v31_time_be"))))
        checks.append(("V31_TTL_BARS", int(e37.V31_TTL_BARS), int(_vnum(prm["be_wait"]["ttl"]))))
    if prm["peaklock"] is not None:                # 里程標5＝v27（flat_up 限定のピーク反転 建値ロック）
        checks.append(("v27_flatup_lock", True, bool(ef.get("v27_flatup_lock"))))
        checks.append(("V27_ARM_PCT", float(e37.V27_ARM_PCT), float(_vnum(prm["peaklock"]["arm"]))))
        checks.append(("V27_GIVEBACK", float(e37.V27_GIVEBACK), float(_vnum(prm["peaklock"]["giveback"]))))
    if prm["fastcut"] is not None:                 # 里程標6＝v53（flat_up 限定の幾何早切り・未搭乗ゲート）
        _fc = prm["fastcut"]
        checks.append(("v53_flatup_fast_cut", True, bool(ef.get("v53_flatup_fast_cut"))))
        checks.append(("V53_FAST_MIN", int(e37.V53_FAST_MIN), int(_fc["scope"]["hold_min"][1])))
        checks.append(("V53_ADV_PCT", float(e37.V53_ADV_PCT),
                       float(_vnum(_fc["exec"]["placement"]["level"]["k"])) * 100.0))
        checks.append(("未搭乗の線＝maker 往復fee",
                       round(2.0 * e37.ee.MAKER_FEE * 100.0, 6),
                       round(float(_vnum(_fc["fire"]["all"][0]["value"])), 6)))
    if prm["v59"] is not None:                     # 里程標7＝v59（型別シグナル早切り・待ち20分・型別の窓）
        _dn, _fl = prm["v59"]["down"], prm["v59"]["flat"]
        checks += [
            ("v59_adx_cut", True, bool(ef.get("v59_adx_cut"))),
            ("V59_WAIT_MIN(down)", int(e37.V59_WAIT_MIN), int(_dn["scope"]["hold_min"][0])),
            ("V59_WAIT_MIN(flat)", int(e37.V59_WAIT_MIN), int(_fl["scope"]["hold_min"][0])),
            ("V59_DOWN_WIN_MIN(0=窓なし)", int(e37.V59_DOWN_WIN_MIN), 0 if _dn["scope"]["hold_min"][1] is None else -1),
            ("V59_FLAT_WIN_MIN", int(e37.V59_FLAT_WIN_MIN), int(_fl["scope"]["hold_min"][1])),
            ("V59_DOWN_SIG", str(e37.V59_DOWN_SIG), "di14"),
            ("V59_FLAT_SIG", str(e37.V59_FLAT_SIG), "kijun26"),
            ("V59_DOWN_ADX7_TH", float(e37.V59_DOWN_ADX7_TH), float(_vnum(_dn["fire"]["all"][0]["value"]))),
            ("V59_FLAT_DID7_TH", float(e37.V59_FLAT_DID7_TH), float(_vnum(_fl["fire"]["all"][0]["value"]))),
            ("V59_DOWN_ADV_PCT", float(e37.V59_DOWN_ADV_PCT),
             float(_vnum(_dn["exec"]["placement"]["level"]["k"])) * 100.0),
            ("V59_FLAT_ADV_PCT", float(e37.V59_FLAT_ADV_PCT),
             float(_vnum(_fl["exec"]["placement"]["level"]["k"])) * 100.0),
            ("V59_CUT_MODE(stop=悲観側)", str(e37.V59_CUT_MODE),
             "stop" if _dn["exec"]["placement"].get("pessimistic") else "close"),
        ]
    if prm["mtfcut"] is not None:                  # 里程標8＝v47（15分過熱×BB のカット）＋v50（切らずに待機へ回す）
        _mc = prm["mtfcut"]
        _f3 = {}                                   # 材料の名前で条件を引ける形（state か legacy_col の名前が鍵）
        for _x in _mc["fire"]["all"]:
            _m3 = (_x.get("material") or [{}])[0]
            _f3[_m3.get("state") or _m3.get("legacy_col") or "?"] = _x
        checks += [
            ("v47_mtf_cut", True, bool(ef.get("v47_mtf_cut"))),
            ("v50_trend_wait", True, bool(ef.get("v50_trend_wait"))),
            ("v47 RSI9(15分)の線", 75.0, float(_vnum(_f3["e37_v47_rsi9_15m"]["value"]))),
            # ★v47 の未搭乗の線は v53 と別の定数（V24_TREND_TP_PCT 0.08%）＝e37_scalp 1234行。
            #   v53 は maker 往復fee 0.028%。同じ「未搭乗」でも枝によって線が違う（2026-08-02 に写し間違えて恒等が
            #   不一致になり、この照合行を足して固定した）。
            ("v47 未搭乗の線(V24_TREND_TP_PCT)", float(e37.V24_TREND_TP_PCT),
             float(_vnum(_f3["mfe_prev_pct"]["value"]))),
            ("V48_TTL_BARS(v50 の待ち)", int(e37.V48_TTL_BARS),
             int(_vnum(_mc["exec"]["be_wait"]["ttl"]))),
        ]
    if prm["anchor"] is not None:                  # 里程標9＝v22 アンカー（利確の基準を直近 M 本の安値へ）
        _an = prm["anchor"]
        checks += [
            ("v22_set", True, bool(ef.get("v22_set"))),
            ("v22 の M（V24_FIXED_V22 の cell0）", int(e37.V24_FIXED_V22["v22_anchor"][0]), int(_vnum(_an["m"]))),
            ("v22 の余白 V11_SL_BUF（TP2 側）", float(e37.V11_SL_BUF), float(_vnum(_an["buf"]))),
            ("v22 の判定に使う余白（TP2 側）", float(e37.V11_SL_BUF),
             float(_vnum(_an.get("gate_buf", _an["buf"])))),
            ("v22 の落ちた時の戻り先（TP2）", "zone/opp", f"{_an['fallback']['kind']}/{_an['fallback']['target']}"),
        ]
        _bx9 = {b["name"]: b for b in recipe["exits"]}
        _tp1lv = _bx9["TP1"]["exec"]["placement"]["level"]["to_level"]   # TP1 側も同じ M・同じ判定余白であること
        checks += [
            ("v22 の M（TP1 側・TP2 と同じであること）", int(_vnum(_an["m"])), int(_vnum(_tp1lv["m"]))),
            ("v22 の判定に使う余白（TP1 側）", float(e37.V11_SL_BUF), float(_vnum(_tp1lv["gate_buf"]))),
            # ★TP1 は安値そのものを基準にする（安値×(1+余白) ではない・e37_scalp 1538行）＝buf を持たない。
            ("v22 の TP1 は安値そのもの（余白なし）", False, "buf" in _tp1lv),
            ("v22 の落ちた時の戻り先（TP1）", "zone/mid",
             f"{_tp1lv['fallback']['kind']}/{_tp1lv['fallback']['target']}"),
        ]
    if prm["tcaught"] is not None:                 # 里程標9＝v24（捕まった玉の建値−L% resting maker 利確）
        _tc = prm["tcaught"]
        checks += [
            ("v24_trend_maker_tp", True, bool(ef.get("v24_trend_maker_tp"))),
            ("uptrend で成行に投げず印を付ける（v23）", True, bool(prm["uptrend_mark"])),
            ("V24_TREND_TP_PCT", float(e37.V24_TREND_TP_PCT),
             round(float(_vnum(_tc["exec"]["placement"]["level"]["k"])) * 100.0, 6)),
        ]
    if prm["stale"] is not None:                   # 里程標9＝MFE_STALE（失速切り）＋v48（切らずに待機へ回す）
        _st9 = prm["stale"]
        checks += [
            ("v48_stale_wait", True, bool(ef.get("v48_stale_wait"))),
            # ★V23_STALE_MIN は run_continuous_v11 の局所変数（e37_scalp 977行）＝モジュール定数として引けない。
            #   だからここは数字で書く。正しさは恒等の md5 が守る（ずれれば全窓で不一致になる）。
            ("V23_STALE_MIN（保有分・e37_scalp 977行の局所値）", 30, int(_st9["scope"]["hold_min"][0])),
            ("MFE_STALE の未搭乗の線＝往復 maker fee（V23_RT_FEE）",
             round(2.0 * e37.ee.MAKER_FEE * 100.0, 6),
             round(float(_vnum(_st9["fire"]["all"][0]["value"])), 6)),
            ("V48_TTL_BARS（v48 の待ち）", int(e37.V48_TTL_BARS),
             int(_vnum(_st9["exec"]["be_wait"]["ttl"]))),
        ]
    # ★網羅の番人（里程標9 で新設）＝e38_logics.json の S1 のフラグを1個も取りこぼしていないこと。
    #   恒等の md5 が一致しても、それは「この恒等ハーネスが載せた構成どうし」の一致でしかない。
    #   採用土台 v59d_164 が持つフラグのうち1個でもハーネスが知らないものが在れば、書き写しは未完である。
    #   だからフラグの一覧を機械で突き合わせ、知らないフラグが在れば止める（fail-closed）。
    #   値は下の checks が1つずつ照合している。ここが見るのは「扱ったかどうか」だけ。
    _cover = {
        "v11": "骨格＝v15 経路（v15_params を渡すこと自体）",
        "v12_open_range": "run_continuous_v11 の引数 v12_open_range=True",
        "v13_time_maker": "run_continuous_v11 の引数 v13_time_maker=True",
        "v18_tp2_far": "v15p['tp2_far']=True（TP2＝反対側ゾーン手前）",
        "v22_set": "レシピの TP1/TP2 の swing アンカー", "v24_trend_maker_tp": "レシピの TCTP 枝",
        "v26_split_ceiling": "レシピの entry.type=ceiling_resting", "v26_gap": "entry.split.gap_pct",
        "v26_down_hours": "entry.split.down_window_hours", "v26_max_age_hours": "entry.split.max_age_hours",
        "v27_flatup_lock": "レシピの PEAKLOCK 枝", "v31_time_be": "TIME 枝の be_wait",
        "v35_flatup_range": "entry.ceiling.flat_up_top", "v36_flatup_near": "entry.ceiling.near_fallback",
        "v37_flatup_climb": "entry.ceiling.climb_guard", "v38_flatup_clamp": "entry.ceiling.clamp_prev_fill",
        "v40_down_no_age": "entry.split.down_no_age", "v47_mtf_cut": "レシピの MTFCUT 枝",
        "v48_stale_wait": "MFESTALE 枝の be_wait", "v50_trend_wait": "MTFCUT 枝の be_wait",
        "v53_flatup_fast_cut": "レシピの FASTCUT 枝", "v56_rearm_delay": "entry.split.rearm_delay_bars",
        "v59_adx_cut": "レシピの V59DOWN / V59FLAT 枝",
    }
    _unknown = sorted(set(ef) - set(_cover))
    _stale_cover = sorted(set(_cover) - set(ef))
    print(f"[恒等検収 S1] 網羅の番人＝S1 のフラグ {len(ef)} 個／このハーネスが扱う {len(_cover)} 個 → "
          f"{'✅ 取りこぼしなし' if not (_unknown or _stale_cover) else '❌'}")
    if _unknown:
        print(f"  ❌ ハーネスが知らないフラグ: {_unknown}（書き写しが未完＝この分は恒等で確かめられていない）")
        ng += len(_unknown)
    if _stale_cover:
        print(f"  ❌ 設定に無いフラグをハーネスが扱っている: {_stale_cover}（設定側が変わった＝表を直す）")
        ng += len(_stale_cover)
    for nm, want, got in checks:
        okc = (want == got)
        print(f"[恒等検収 S1] 値の照合 {nm}: 正本={want} / レシピ側={got} → {'✅' if okc else '❌'}")
        ng += 0 if okc else 1
    (dfp,) = tuner.load_windows_cached(ad, [(s, e)], tuner.WARM, use_cache=not quick)
    # 材料列＝レシピを読んで要るものだけを付ける（歩6 で attach_recipe_columns へ切り出した共通処理）。
    # 中身は v35／v37／v59／v47 の付け足しで、式は e37 の関数と写しをそのまま使う（出典を e37 に固定）。
    # 両側（現行 run_continuous_v11 とレシピ実行器）に同じ df を渡す＝材料の食い違いを物理的に作らない。
    dfp = attach_recipe_columns(dfp, recipe)
    # 現行側＝run_continuous_v11 を同じ構成で（v18 base18 と同じ形の v15_params・run_e37 2419-2429 行と同式）
    v15p = {"ladder": None, "sl_far": prm["sl_far"], "tmax": prm["tmax"], "down": None, "ret": {}, "dd": {},
            "cell_fn": (lambda k_, a_, w_: 0), "cell_fixed": True, "v16": True, "v17": True,
            "guard": {}, "guard_all": None, "cooldown": e37.V16_COOLDOWN[0], "be_time": {},
            "tmax_map": {}, "down_map": {}, "tp1_f": {}, "tp2_f": {}, "size0": {},
            "break_mode": None, "break_bars": prm["break_bars"], "tp2_far": True,
            "v26_split": True, "v26_gap": prm["gap"], "v26_down_hours": prm["down_hours"],
            "v26_max_age_hours": prm["max_age_hours"], "v40_down_no_age": prm["down_no_age"]}
    if prm["rearm_bars"] is not None:              # 里程標2＝v56（レシピに書いてあるレバーだけ現行側でも ON にする）
        v15p["v56_rearm_delay"] = True
    _lv = ["v26 型別天井", "v40 down 免除", "v18 TP2 反対側", "v13 縮む TP", "uptrend 畳み", "構造破れ"]
    if prm["rearm_bars"] is not None:
        _lv.append("v56 再武装遅延")
    for _key, _flag, _name in (("flat_up_top", "v35_flatup_range", "v35 レンジ実測高値"),
                               ("near_fallback", "v36_flatup_near", "v36 近傍フォールバック"),
                               ("clamp_prev_fill", "v38_clamp_prev", "v38 前玉クランプ"),
                               ("climb_guard", "v37_climb_guard", "v37 階段売り上がり停止")):
        _on = (_cl.get(_key) == "range_high") if _key == "flat_up_top" else bool(_cl.get(_key))
        if _on:
            v15p[_flag] = True
            _lv.append(_name)
    if prm["be_wait"] is not None:                 # 里程標4＝v31（TIME 満了後の建値フロア待機・既存の待機機構で書ける）
        v15p["v31_time_be"] = True
        _lv.append("v31 建値フロア待機")
    if prm["peaklock"] is not None:                # 里程標5＝v27（ピーク反転の建値ロック・待機中も評価される）
        v15p["v27_flatup_lock"] = True
        _lv.append("v27 ピーク反転ロック")
    if prm["fastcut"] is not None:                 # 里程標6＝v53（幾何早切り）
        v15p["v53_flatup_fast_cut"] = True
        _lv.append("v53 幾何早切り")
    if prm["v59"] is not None:                     # 里程標7＝v59（型別シグナル早切り）
        v15p["v59_adx_cut"] = True                 # 材料列は attach_recipe_columns が付け済み
        _lv.append("v59 型別シグナル早切り")
    if prm["mtfcut"] is not None:                  # 里程標8＝v47（15分過熱×BB のカット）＋v50（待機へ回す）
        v15p["v47_mtf_cut"] = True                 # 材料列は attach_recipe_columns が付け済み
        v15p["v50_trend_wait"] = True
        _lv.append("v47 15分過熱カット→v50 待機")
    if prm["anchor"] is not None:                  # 里程標9＝v22 アンカー（run_e37 2431-2440行の v22_set 相当）
        v15p["v22_anchor"] = {0: int(_vnum(prm["anchor"]["m"]))}   # V24_FIXED_V22 と同じ形（cell0→M）
        # ★run_e37 の v22_set は、TP アンカー以外に v21 の2つの値も一緒に入れる（2434-2435行）。
        #   採用土台と同じ引数にするため、ここでも同じものを入れる。この2つは v26 の型別天井（1459行）が
        #   _fire21 を丸ごと上書きするので入口には効かず、畳みの分岐も v23 の枝が先に取るので効かない。
        #   「効かないはず」を口で言わず、入れた上で恒等が取れることで示す。
        v15p["v21_entry"] = dict(e37.V22_FIXED_V21_ENTRY)
        v15p["v21_fold"] = dict(e37.V22_FIXED_V21_FOLD)
        _lv.append("v22 TP アンカー（直近24本の安値）")
    if prm["tcaught"] is not None:                 # 里程標9＝v23/v24（捕まった玉の状態機械・run_e37 2441-2446行）
        v15p["v23_trend_exit"] = True
        v15p["v24_trend_maker_tp"] = True
        _lv.append("v23/v24 捕まった玉の建値−0.08% 利確")
    if prm["stale"] is not None:                   # 里程標9＝v48（失速切りを成行にせず建値フロア待機へ）
        v15p["v48_stale_wait"] = True
        _lv.append("v48 失速切りの建値待ち")
    print(f"[恒等検収 S1] 載せたレバー: {' / '.join(_lv)}（レシピが正本＝現行側の引数はレシピから機械導出）")
    box_tf = ad.config()["global"]["box_tf"]
    up_arr = dfp["rg5_uptrend"].to_numpy(bool)
    t_ref = e37.run_continuous_v11(dfp, box_tf, v12_open_range=True, v13_time_maker=True,
                                   v20_uptrend=up_arr, short_lots=prm["max_lots"], v15_params=v15p)
    for r in t_ref:
        r["logic"] = recipe["meta"]["logic_id"]
    h_ref, n_ref = _md5_trades(t_ref, s, e)
    # ★配線が生きている証拠＝現行側が数えたレバーの発火回数。0 のレバーは「両側が一致した」だけで、
    #   この窓では一度も動いていない＝書き写しの正しさをその窓では確かめられていない（正直に出す）。
    _st = {k: v for k, v in (v15p.get("_stats") or {}).items()
           if isinstance(v, int) and v > 0 and not k.endswith("$")}
    print(f"[恒等検収 S1] 現行側のレバー発火回数（0 のレバーはこの窓で動いていない）: {_st}")
    t_new, rep = run_recipe(dfp, recipe)
    h_new, n_new = _md5_trades(t_new, s, e)
    same = (h_ref == h_new)
    print(f"[恒等 S1]現行（run_continuous_v11・里程標1 構成）: {n_ref} 行 md5 {h_ref}")
    print(f"[恒等 S1]レシピ実行器: {n_new} 行 md5 {h_new} → {'✅ 完全一致' if same else '❌ 不一致'}")
    tr = pd.DataFrame(t_ref)
    if len(tr):
        et_r = pd.to_datetime(tr["entry_time"])
        cnt = tr[(et_r >= s) & (et_r < e)]["exit_reason"].value_counts().to_dict()
        print(f"[恒等 S1]出口理由の内訳（入口と出口の両方が恒等の対象）: {cnt}")
    print(f"[検証器の報告] 経路 {rep['経路数']} / 条件 {rep['条件数']} / 触れた列 {rep['触れた列']}")
    print(f"[検証器の報告] legacy 使用 {len(rep['legacy使用'])} 件（恒等レーン）/ 値待ち {rep['値待ち']}")
    ng += 0 if same else 1
    print(f"\n[恒等検収 S1 まとめ] {'✅ 全部一致' if ng == 0 else f'❌ 不一致 {ng} 件'}")
    return ng


# ══ 手数料の分類の食い違い検査（2026-08-02 まこさん OK で「丸ごと比較」から直した）════════════
def maker_taker_sync_check(name: str, src: str, maker: tuple, judge) -> list[str]:
    """戦略と審判で、決済の方式（指値か成行か）の分類が食い違っていないかを見る。

    **何を守るか**＝手数料の計算のずれ。指値は 0.014%、成行は 0.042% で3倍違う。
    戦略は自分でも手数料を引いた金額を売買記録に書き（画面用）、審判は同じ記録を読んで
    計算し直す（公式）。片方が指値、もう片方が成行と思っていると、画面の数字だけが狂う。

    ★比べるのは「その戦略のソースに文字列として出てくる決済理由」だけ。
      直す前は 戦略の指値一覧 と 審判の指値一覧 を丸ごと比べていた。**審判は全戦略ぶんの一覧を
      持つので、他の戦略の理由（例＝E36 の CENTER_LOCK）で必ず差が出て、関係の無い理由で
      番人が落ち続けていた**（2026-08-02 の cbf1fde 以降ずっと ❌ で、自己検査が最後まで走らなかった）。
    ★戦略を引数で受け取る形にした＝E36 と E38 にも同じ検査を1行で足せる（いまは E37 だけ）。
    ★この検査が本物であることは、下の selftest の「番人の番人」が毎回確かめる
      （2026-08-02 に実際に起きた事故＝TREND_CAUGHT_TP の抜け を再現して、落ちることを見る）。
    """
    known = set(judge.MAKER_EXIT_REASONS) | set(judge.TAKER_EXIT_REASONS)
    used = sorted(r for r in known if f'"{r}"' in src)
    if not used:
        return [f"{name}: 決済理由がソースから1つも見つからない（抽出のしかたが壊れている）"]
    mk = set(maker)
    def _w(flag):                                   # 表示用（人が読んで分かる言葉にする）
        return "指値" if flag else "成行"
    bad = [f"{r}（戦略は{_w(r in mk)}／審判は{_w(r in judge.MAKER_EXIT_REASONS)}）"
           for r in used if (r in mk) != (r in judge.MAKER_EXIT_REASONS)]
    return [f"{name} と審判で決済の方式の分類が食い違う: {', '.join(bad)}"] if bad else []


def e36_maker_taker_behavior_check(judge) -> list[str]:
    """E36 と審判で、決済の方式（指値か成行か）の分類が食い違っていないかを見る。

    ★上の maker_taker_sync_check と違って「ソースに書いてある一覧」を読まない。
      **実際に E36 の記録処理を呼んで、出てきた手数料の額から どちらで計算されたかを判定する。**

    なぜこの形にしたか（まこさん OK 2026-08-04・案A）:
      ①E36 は指値の一覧を モジュールの定数でなく 関数の中の式に直接持つ
        （e36_short_oscillation.py 227行 `is_taker = reason not in (...)`）ので、名前で外から読めない。
      ②2026-08-02 の事故（TREND_CAUGHT_TP の写し忘れ）は「書いてあることと 実際の動きがずれた」型。
        だから 実際の動きを見るほうが、同じ型の事故を捕まえられる。
      ③E36 は採用中の柱なので、コードを1バイトも触らずに検査を足せる形を選んだ。

    ★作り物のデータだけで走る＝売買記録CSVを書かない・採点窓を1バーも使わない（L-267）。
    ★審判 score.py は import して一覧を読むだけ＝計算式に触れない（H13）。
    ★手数料の率は eval_engine（E36 が使っているものと同じ実体）から読む＝数字を手で書かない（H4）。
    """
    import e36_short_oscillation as e36          # 局所 import＝通常の実行に読み込みの費用をかけない
    ee36 = e36.ee                                # E36 自身が使っているコスト定数の実体（H4）
    src = inspect.getsource(e36)
    known = set(judge.MAKER_EXIT_REASONS) | set(judge.TAKER_EXIT_REASONS)
    used = sorted(r for r in known if f'"{r}"' in src)
    if not used:
        return ["e36_short_oscillation: 決済理由がソースから1つも見つからない（抽出のしかたが壊れている）"]
    # 作り物の1玉。価格と枚数は実際の桁に合わせる＝小数4桁の丸めで指値と成行の差が消えないように。
    px_in, px_out, sz = 60000.0, 60000.0, 0.024
    ts = pd.date_range("2024-05-01", periods=2, freq="5min").to_numpy()
    pos = {"side": "SHORT", "first_idx": 0, "add_count": 1, "max_fav": px_in, "max_adv": px_in,
           "atr_entry": 1.0, "adx_entry": 20.0, "k_entry": 50.0, "W_entry": 0.01}
    lots = [(0, px_in, sz)]
    fee_maker = round(px_in * sz * ee36.MAKER_FEE + px_out * sz * ee36.MAKER_FEE, 4)
    fee_taker = round(px_in * sz * ee36.MAKER_FEE + px_out * sz * ee36.TAKER_FEE
                      + px_out * sz * ee36.SLIPPAGE, 4)
    if abs(fee_maker - fee_taker) < 1e-9:        # 見分けが付かない作り物＝検査が空振りになるので止める
        return [f"e36 の検査: 作り物のデータで指値 {fee_maker} と成行 {fee_taker} が同額になり判定できない"]
    def _w(flag):                                # 表示用（人が読んで分かる言葉にする）
        return "指値" if flag else "成行"
    bad = []
    for r in used:
        rows: list = []
        e36._record_lots(rows, pos, lots, px_out, r, 1, ts)
        if len(rows) != 1:
            bad.append(f"{r}: 記録が1行にならなかった（{len(rows)} 行）"); continue
        fee = rows[0]["fee_usd"]
        if abs(fee - fee_maker) < 1e-9:
            strat_is_maker = True
        elif abs(fee - fee_taker) < 1e-9:
            strat_is_maker = False
        else:
            bad.append(f"{r}: 出た手数料 {fee} が 指値 {fee_maker} とも 成行 {fee_taker} とも一致しない")
            continue
        judge_is_maker = r in judge.MAKER_EXIT_REASONS
        if strat_is_maker != judge_is_maker:
            bad.append(f"{r}（戦略は{_w(strat_is_maker)}／審判は{_w(judge_is_maker)}）")
    return [f"e36_short_oscillation と審判で決済の方式の分類が食い違う: {', '.join(bad)}"] if bad else []


# ══ 自己検査（番人＝わざと壊したレシピ18種で全部止まる・正しい2種は通る・設計書 §10＋歩4 拡張）══
def _base_ok_recipe() -> dict:
    """検証だけ通す最小の正しいレシピ（V9 風多条件・探索レーン＝legacy なし）。"""
    return {
        "meta": {"strategy": "e38", "logic_id": "T1", "side": "SHORT",
                 "regime": {"name": "range", "entry_col": "range_ok_rg5", "block_col": "rg5_uptrend"}},
        "pre_filter": [],
        "entry": {"connective": {"all": [
            {"role": "trigger", "form": "cross", "value": {"direction": "down"},
             "material": [{"family": "Stoch%K", "param": 14, "tf": "5m"},
                          {"family": "Stoch%D", "param": 14, "tf": "5m"}]},
            {"role": "env", "form": "level", "side": "below", "value": {"const": "RSI_OB"},
             "material": [{"family": "RSI", "param": 14, "tf": "1h"}]},
            {"role": "sufficiency", "form": "level", "side": "above", "value": {"const": "NEUTRAL_0"},
             "material": [{"family": "volume_ratio", "param": 20, "tf": "15m"}]},
            {"role": "location", "form": "level", "side": "above", "value": {"const": "MID_50"},
             "material": [{"geo": "帯内位置%"}]},
            {"if": {"role": "env", "form": "level", "side": "above", "value": {"const": "ADX_TREND"},
                    "material": [{"family": "ADX", "param": 14, "tf": "2h"}]},
             "then": {"role": "sufficiency", "form": "level", "side": "above", "value": {"const": "NEUTRAL_0"},
                      "material": [{"family": "ROC", "param": 12, "tf": "15m"}]}},
        ]}},
        "exits": [
            {"name": "SL", "reason": "SL_FILLED",
             "exec": {"method": "maker", "placement": {"kind": "resting", "fill": "adverse", "pessimistic": True,
                                                       "level": {"kind": "zone_sl", "k": {"const": "FULL_100", "mult": 0.01}}}},
             "size_ratio": 1.0},
            {"name": "TP", "reason": "TP_FILLED",
             "exec": {"method": "maker", "placement": {"kind": "resting", "fill": "profit",
                                                       "level": {"kind": "zone", "target": "mid"}}},
             "size_ratio": 1.0},
        ],
        "position": {"mode": "separate", "max_adds": 2},
    }


def _selftest_4_19() -> list[str]:
    """監査 4-19 の番人6件（要件 R5＝相場／要件 R6＝保有時間の上限）。落ちなかったものを返す。

    番人の考え方＝「直した」と言うために、わざと壊して落ちることを毎回その場で確かめる。
    """
    import copy as _copy
    import tempfile as _tmp
    from tuner_adapters import REQUIRED, load_adapter, RegimeDeclError
    import engine_tuner_gen as _gen
    import tuner_judgement as _tj
    bad: list[str] = []

    # ① 接続ファイルから相場の宣言を消すと、engine_tuner が実行前に止まる
    if "regime" not in REQUIRED:
        bad.append("番人①: 接続ファイルの必須項目に regime が入っていない")
    else:
        _ad = load_adapter("e38")
        _saved = _ad.regime
        try:
            del _ad.regime
            try:
                load_adapter("e38")
                bad.append("番人①: 接続ファイルから regime を消しても止まらない")
            except SystemExit:
                pass
        finally:
            _ad.regime = _saved

    # ② 相場の宣言が辞書でない（＝直す前の文字列の形）と、レシピを読み込まない
    _r = identity_recipe()
    _r2 = _copy.deepcopy(_r)
    _r2["meta"]["regime"] = "range_rg5"
    try:
        validate_recipe(_r2)
        bad.append("番人②: meta.regime が文字列でもレシピが読み込まれる（G5 で止まるはず）")
    except RecipeError:
        pass

    # ③ 決めていない相場の名前を宣言すると、レシピを読み込まない
    _r3 = _copy.deepcopy(_r)
    _r3["meta"]["regime"] = {"name": "bull", "entry_col": "range_ok_rg5", "block_col": None}
    try:
        validate_recipe(_r3)
        bad.append("番人③: 一覧に無い相場の名前でもレシピが読み込まれる（G5 で止まるはず）")
    except RecipeError:
        pass
    try:
        from tuner_adapters import check_regime as _ck
        _ck("e38", "S2", {"name": "bull", "entry_col": "x"})
        bad.append("番人③: 接続ファイル側の検査も一覧に無い名前を通す")
    except RegimeDeclError:
        pass

    # ④ 宣言した列がデータに無いと、走らせない
    _df = _sentinel_df()
    _r4 = _copy.deepcopy(_r)
    _r4["meta"]["regime"]["entry_col"] = "regime_not_exist"
    try:
        run_recipe(_df, _r4)
        bad.append("番人④: データに無い列を宣言しても走ってしまう")
    except RecipeError:
        pass

    # ⑤ 宣言を差し替えると、売買記録が実際に変わる（＝宣言が本当に効いている）
    #    直書きに戻した実装だと、宣言を変えても結果が変わらない＝ここが落ちる。
    _t_base, _ = run_recipe(_df, _r)
    _df2 = _df.copy()
    _df2["regime_never"] = False                       # どのバーでも建てられない相場
    _r5 = _copy.deepcopy(_r)
    _r5["meta"]["regime"] = {"name": "range", "entry_col": "regime_never", "block_col": None}
    _t_never, _ = run_recipe(_df2, _r5)
    if len(_t_base) == 0:
        bad.append("番人⑤: 土台の合成データで玉が1つも建たない（番人が成立していない）")
    elif len(_t_never) != 0:
        bad.append(f"番人⑤: 建てられない相場を宣言しても {len(_t_never)} 玉が建つ（宣言が効いていない）")

    # ⑥ 役割の範囲が決まっていない／台帳に役割が無いと、走らせない
    _lm, _ = _gen.load_limits()
    _lm_empty = dict(_lm)
    _lm_empty["hold_range_by_role"] = {"scalp": {"lo_bars": None, "hi_bars": None}}
    try:
        _gen.resolve_hold_range(_lm_empty, "e38")
        bad.append("番人⑥: 役割の範囲が空でも走ってしまう")
    except _gen.HoldRangeError:
        pass
    _saved_adopted = _tj.ADOPTED
    try:
        with _tmp.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
            fh.write("# 台帳から ROLE_CHECK の行を消した状態（番人⑥）\n")
            _p = pathlib.Path(fh.name)
        _tj.ADOPTED = _p
        try:
            _gen.resolve_hold_range(_lm, "e38")
            bad.append("番人⑥: 台帳に役割が無くても走ってしまう")
        except _gen.HoldRangeError:
            pass
    finally:
        _tj.ADOPTED = _saved_adopted
        try:
            _p.unlink()
        except Exception:                              # noqa: BLE001
            pass

    # ⑦ 古い方の売買ループ（e38_logic_parts.generic_logic_loop）でも宣言が効いている
    #    ＝監査の逐語「共通の売買ループが range_ok_rg5 を前提にしています」を実際に外せたかの確認。
    _ep, _xp, _ml = engine_params_from_recipe(_r)

    def _with_parts_cols(d):
        """古い売買ループが要る列を、番人用の合成データへ足す（値は入口の判定に効かない中立値）。"""
        out = d.copy()
        out["e38_vol_ma20"] = 1.0
        for _pt in parts.HTF_PARTS:
            if f"e38_htf_{_pt}" not in out.columns:
                out[f"e38_htf_{_pt}"] = 0.0
        for _pt in parts.VOL_PARTS:
            if f"e38_vol_{_pt}" not in out.columns:
                out[f"e38_vol_{_pt}"] = 2.0
        return out

    _t_old = parts.generic_logic_loop(_with_parts_cols(_df), "pullback_short", _ep, _xp,
                                      max_lots=_ml, logic_id="番人⑦")
    _t_old_never = parts.generic_logic_loop(_with_parts_cols(_df2), "pullback_short", _ep, _xp,
                                            max_lots=_ml, logic_id="番人⑦",
                                            regime={"name": "range", "entry_col": "regime_never",
                                                    "block_col": None})
    if len(_t_old) == 0:
        bad.append("番人⑦: 古い売買ループの土台で玉が1つも建たない（番人が成立していない）")
    elif len(_t_old_never) != 0:
        bad.append(f"番人⑦: 古い売買ループが宣言を無視して {len(_t_old_never)} 玉を建てる（直書きのままということ）")

    # 追加＝E37 と E38 の宣言が食い違ったら止まる（列の名前は同じ prepare_df が作るため）
    import tuner_adapters.e37 as _e37a
    _sv = dict(_e37a.REGIME)
    try:
        _e37a.REGIME["entry_col"] = "range_ok_OTHER"
        try:
            _e37a.assert_regime_agrees()
            bad.append("番人⑥+: E37 と E38 の宣言が食い違っても止まらない")
        except SystemExit:
            pass
    finally:
        _e37a.REGIME.clear()
        _e37a.REGIME.update(_sv)
    return bad


def _selftest_roundtrip() -> tuple[list[str], int]:
    """名前の組み立ての往復テスト（2026-08-11・段6 の 6-7）。

    ①材料カタログの列名を1つずつ参照表で family と数字に分解する
    ②この表（FAMILY_TEMPLATES）で組み立て直す
    ③元の名前と1文字も違わないことを確かめる
    ④番人の番人＝わざと型を1件 壊すと、この検査が落ちることを確かめる

    ★観察の道具（observe_diag）を import して、実物の列名を数える（名前を手で並べない）。
    """
    import contextlib
    import io
    bad: list[str] = []
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            import observe_diag as _od
            _cfg = _od.load_config()
            names = [nm for nm, _fn, _dr in _od.build_catalog(_cfg)]
    except Exception as e:                                        # noqa: BLE001
        return [f"材料カタログを読めない: {str(e)[:80]}"], 0

    def _mismatch(nms: list[str]) -> list[str]:
        out = []
        for nm in nms:
            ent, prm = iref.find(nm)
            if ent is None:
                out.append(f"参照表に無い列: {nm}")
                continue
            try:
                made = build_name({"family": ent["family"], "param": (list(prm) or None)})
            except SystemExit as e:                               # RecipeError
                out.append(f"{nm}: 組み立てで拒否された（{str(e)[:60]}）")
                continue
            if made != nm:
                out.append(f"{nm}: 組み立て直すと {made}（食い違い）")
        return out

    bad += _mismatch(names)

    # 番人の番人＝型を1件 壊すと落ちるか（この検査が生きていることの確認）
    tgt = "RSI" if "RSI" in FAMILY_TEMPLATES else next(iter(FAMILY_TEMPLATES))
    keep = FAMILY_TEMPLATES[tgt]
    try:
        FAMILY_TEMPLATES[tgt] = keep + "X"
        if not _mismatch([nm for nm in names if iref.find(nm)[0]
                          and iref.find(nm)[0]["family"] == tgt]):
            bad.append("番人の番人: 型を1件 壊しても往復テストが落ちない")
    finally:
        FAMILY_TEMPLATES[tgt] = keep
    return bad, len(names)


def unordered_iteration_scan(src: str) -> list[tuple[int, str]]:
    """「並びの決まらない入れ物（set）を上から順に見ている」所を、ソースから機械で全部 探す。

    何を守るか＝同じ入力なら同じ結果が出ること（再現できること）。
    Python の set は中身の並びが決まっていません。走らせるたびに文字列の置き場所が変わるので、
    set を上から順に見ると、実行ごとに順番が変わります。
    2026-08-16 に生成器で実際に起きました＝案の候補の並びが毎回 変わり、同じ種でも別の案が出て、
    過去の探索をやり直せない状態でした（`session_worklog_20260816.md` の §4）。

    ★手で場所の一覧を書きません（手書きの一覧は書き忘れると穴になる＝next_step §6 の50番）。

    ★何を set と見なすか＝波括弧 `{…}` ／ 集合の内包表記 ／ **`set(...)`・`frozenset(...)` の
      呼び出し**の3つです。`sorted(...)` が出ないのは「Call だから」ではなく、**名前が set・
      frozenset でない Call だから**です（`for x in set(y)` は見つかります）。
    ★見る場所＝①`for`／`async for` が回す相手 ②内包表記が回す相手（`for … in …` の右側）。
    ★見る単位＝**関数1つ＝1つの単位**。それに加えて、**ファイル直下とクラスの本体**を
      「関数の外」としてまとめて1つの単位で見ます（入れ子の関数はそこから外して、別の単位に）。
    ★数え方＝**同じ行に2つ以上あっても1件に丸めます**（行と理由が同じものは1件）。

    ★set 扱いをやめる場合が2つ＝①同じ名前に別の物を代入し直したとき ②同じ名前を for 文か
      内包表記の**ループ変数**として使ったとき（星つき `*s` も含む）。どちらも「入れ直し」です。
      **★やめるのは「その行より後ろ」だけです**（下の1周の走査で、行の順に見ています）。

    ★限界（6つ）
      (a) 関数の外から渡ってきた set（引数・戻り値）は追えません。
      (b) 入れ子の関数で、外側が作った set を内側で回す形は追えません。
      (c) 内包表記のループ変数が set を受け取る形は追えません（代入ではないため）。
      (d) set を作って、その同じ名前をループ変数にも使い、**その後に**その set を回す形は
          追えません（②で set 扱いをやめるため）。engine_tuner の4本には在りません（実測 0件）。
      (e) **包んでから回す形**は追えません＝`for x in list(s)` ／ `for x in (s | t)` ／
          `[*s]`（星つきの展開）。どれも set の並びが結果に出ますが、回す相手が set の形に
          見えないためです（実測でどれも 0件）。
      (f) **ループが繰り返して、次の周で回す形**は追えません＝ループの本体の後ろで set を作り、
          次の周の頭でそれを回す形。行の順に1回 見るだけなので、周をまたぐ関係は見ません。

    ★★この関数は「回している所の形」を見ています。守りたいのは「並びの決まらない値が結果に
      出ないこと」です。**この2つは同じではありません**（前者は後者の一部分）。
      `"".join(s)`・`next(iter(s))`・`s.pop()`・set から作った dict を回す、なども並びが結果に
      出ますが、この関数は見ません（2026-08-26 の読み比べの所見 §6）。

    ★2026-08-26（106番・まこさん承認 29ebcd26…）の直し。**別セッションの Claude Code に
      説明文と実装の読み比べを頼み（まこさん決定）、条件つき GO ＋ 指摘11件を受けて直しました。**
      ①走査を ast.walk から _own_nodes へ＝ファイル全体を見る回で入れ子の関数の中まで潜り、
        別の関数の同名の変数と結び付いていた（生成器 :1352・:1362 の誤報）。
      ②ループ変数として使われた名前の set 扱いをやめる（生成器 :4708 の誤報）。
      ③**3周を1周にして、行と桁の順に見る**＝直す前は「関数を見終わった後の1枚の答え」で
        位置を見ておらず、**見逃しと誤報が両方 出せた**（読み比べの所見 Q1-1・実測）。
        内包表記の中も、`for … in …` を1つずつ「回す相手を見る → 入れる名前をやめる」の順に。
      ④`async for` を、回す相手を見る所でも見るようにした（直す前は片方だけ見ていた）。
      ⑤ループ変数の星つき（`*s`）を開くようにした。
    """
    import ast
    import collections
    tree = ast.parse(src)

    def _is_set_expr(n) -> bool:
        return isinstance(n, (ast.Set, ast.SetComp)) or (
            isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
            and n.func.id in ("set", "frozenset"))

    def _own_nodes(scope) -> list:
        """その scope 直属のノードだけを返す（入れ子の関数の中には入らない）。

        ★入れ子の関数の中身は、その関数自身が scope になった回で見ます＝取りこぼしません。
        ★並べ直しは、これを呼ぶ側が行と桁の順で行います（下の1周の走査）。
        """
        out: list = []
        q = collections.deque(ast.iter_child_nodes(scope))
        while q:
            n = q.popleft()
            out.append(n)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue          # 入れ子の関数は、それ自身が別の scope として見られる
            q.extend(ast.iter_child_nodes(n))
        return out

    def _bound_names(target) -> list:
        """ループが名前に入れる先を集める（`for a, (b, c) in …` の入れ子と `*s` も開く）。"""
        if isinstance(target, ast.Name):
            return [target.id]
        if isinstance(target, ast.Starred):
            return _bound_names(target.value)
        if isinstance(target, (ast.Tuple, ast.List)):
            return [nm for e in target.elts for nm in _bound_names(e)]
        return []

    hits: list[tuple[int, str]] = []
    scopes = [tree] + [n for n in ast.walk(tree)
                       if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    for scope in scopes:
        # ★2026-08-26（106番・読み比べの所見 Q1-1／Q1-2）＝3周を1周にした。
        #   直す前は「代入を全部 集める → ループ変数を全部 消す → 回す所を全部 見る」の3周で、
        #   set の記録が『関数を見終わった後の1枚の答え』になっていた＝回している所が代入より
        #   前か後かを見ておらず、見逃しと誤報が両方 出せた（所見の実測A・B）。
        #   いまは行と桁の順に1回だけ見て、その行までに分かっていることだけで判定する。
        setvars: dict[str, int] = {}
        for n in sorted(_own_nodes(scope),
                        key=lambda x: (getattr(x, "lineno", 0), getattr(x, "col_offset", 0))):

            def _look(it, ln: int) -> None:
                """回す相手を1つ見る（この行までに分かっている set の記録で判定する）。"""
                if _is_set_expr(it):
                    hits.append((ln, "set を直に上から順に見ている"))
                elif isinstance(it, ast.Name) and it.id in setvars:
                    hits.append((ln, f"set の変数 {it.id}"
                                     f"（{setvars[it.id]}行で作成）を上から順に見ている"))

            # ①for／async for＝回す相手を先に見て、そのあとループ変数の set 扱いをやめる
            if isinstance(n, (ast.For, ast.AsyncFor)):
                _look(n.iter, n.lineno)
                for nm in _bound_names(n.target):
                    setvars.pop(nm, None)
            # ②内包表記＝`for … in …` を1つずつ、同じ順で処理する。
            #   ★1つの内包表記の中で入れて回す形が在るため（生成器 :4708 がこれ）。
            for gen in getattr(n, "generators", []) or []:
                _look(gen.iter, n.lineno)
                for nm in _bound_names(gen.target):
                    setvars.pop(nm, None)
            # ③代入＝set を作ったら覚え、別の物を入れ直したらやめる
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                nm = n.targets[0].id
                if _is_set_expr(n.value):
                    setvars[nm] = n.lineno
                elif nm in setvars:
                    del setvars[nm]
    return sorted(set(hits))


def selftest() -> None:
    ng = []
    okr = _base_ok_recipe()
    try:
        rep = validate_recipe(okr)
        for need in ("N_MIN", "K_MAX", "P_MAX"):
            if not any(need in x for x in rep["値待ち"]):
                ng.append(f"値待ちに {need} が出ない（まこさん判断待ちの可視化が消えた）")
    except RecipeError as e:
        ng.append(f"正しいレシピ（V9風多条件）が拒否された: {e}")
    try:
        validate_recipe(identity_recipe())
    except RecipeError as e:
        ng.append(f"正しいレシピ（S2 恒等）が拒否された: {e}")
    try:
        validate_recipe(identity_l1_recipe())
    except RecipeError as e:
        ng.append(f"正しいレシピ（L1 恒等）が拒否された: {e}")
    try:
        validate_recipe(identity_s1_recipe())
    except RecipeError as e:
        ng.append(f"正しいレシピ（S1 恒等・里程標1）が拒否された: {e}")

    import copy

    def broke(name: str, mutate, want_code: str, limits=None, samples=None):
        r = copy.deepcopy(okr)
        mutate(r)
        try:
            validate_recipe(r, limits, samples)
            ng.append(f"番人すり抜け: {name}（{want_code} で止まるはず）")
        except RecipeError as e:
            if want_code not in str(e):
                ng.append(f"番人の理由コード違い: {name}＝{e}（期待 {want_code}）")

    def _set_trig_role(r, role):
        r["entry"]["connective"]["all"][0]["role"] = role
    broke("① 引き金ゼロ", lambda r: _set_trig_role(r, "env"), "G1")
    broke("② 経路内に引き金2本", lambda r: r["entry"]["connective"]["all"].append(
        {"role": "trigger", "form": "cross", "value": {"direction": "down"},
         "material": [{"family": "Stoch%K", "param": 14, "tf": "5m"},
                      {"family": "Stoch%D", "param": 14, "tf": "5m"}]}), "G1")

    def _trig_inside_any(r):
        t = r["entry"]["connective"]["all"].pop(0)
        r["entry"]["connective"]["all"].append({"any": [t, {"role": "env", "form": "level", "side": "above",
                                                            "value": {"const": "NEUTRAL_0"},
                                                            "material": [{"family": "ROC", "param": 12, "tf": "5m"}]}]})
    broke("③ any の内側の引き金", _trig_inside_any, "G1")
    broke("④ 未登録 family", lambda r: r["entry"]["connective"]["all"][1]["material"].__setitem__(
        0, {"family": "未知指標", "param": 9, "tf": "1h"}), "G6")
    broke("⑤ 補正後標本数不足", lambda r: None, "G2",
          limits={"n_min": 100}, samples={"RSI14__1h": 3})
    broke("⑥ 同系統を同役割に2本", lambda r: r["entry"]["connective"]["all"].append(
        {"role": "env", "form": "level", "side": "below", "value": {"const": "RSI_OB"},
         "material": [{"family": "RSI", "param": 7, "tf": "4h"}]}), "G3")
    broke("⑦ SL 系も許容損失枝も無い", lambda r: r["exits"].pop(0), "G4")
    broke("⑧ 深さ超過", lambda r: None, "G5", limits={"depth_max": 1})
    broke("⑨ 生の数字の閾値", lambda r: r["entry"]["connective"]["all"][1].__setitem__(
        "value", {"raw": 65.0}), "G6")
    broke("⑩ レジストリ外の定数", lambda r: r["entry"]["connective"]["all"][1].__setitem__(
        "value", {"const": "ORESAMA_TH"}), "G6")
    broke("⑪ 探索レシピの legacy 値", lambda r: r["entry"]["connective"]["all"][1].__setitem__(
        "value", {"legacy": 65.0}), "G6")
    broke("⑫ streak(N=1)", lambda r: r["entry"]["connective"]["all"].append(
        {"role": "sufficiency", "form": "streak", "value": {"n": 1},
         "inner": {"role": "sufficiency", "form": "level", "side": "above", "value": {"const": "NEUTRAL_0"},
                   "material": [{"family": "ROC", "param": 6, "tf": "5m"}]}}), "G5")
    # 追加の物理: 未知の執行方式・未登録の出口理由・価格水準列を条件の材料に使う
    broke("⑬ iceberg は実行不能＝拒否側", lambda r: r["exits"][1]["exec"].__setitem__("method", "iceberg"), "G6")
    broke("⑭ score 未登録の出口理由", lambda r: r["exits"][1].__setitem__("reason", "MY_EXIT"), "G6")
    broke("⑮ 価格水準列を条件の材料に", lambda r: r["entry"]["connective"]["all"][3]["material"].__setitem__(
        0, {"geo": "res_hi"}), "G6")
    # 歩4 拡張の番人（band 系・入れ子の値）
    broke("⑯ band に lo/hi が無い", lambda r: r["entry"]["connective"]["all"].append(
        {"role": "sufficiency", "form": "band", "material": [{"family": "ATR%", "param": 14, "tf": "1h"}],
         "value": {"lo": {"const": "NEUTRAL_0"}}}), "G5")
    broke("⑰ slope_avg に m が無い", lambda r: r["entry"]["connective"]["all"].append(
        {"role": "sufficiency", "form": "slope_avg", "side": "above",
         "material": [{"family": "ATR%", "param": 14, "tf": "1h"}], "value": {"n": 3}}), "G5")
    broke("⑱ band の lo に未知フィールド（生の数字の混入経路）", lambda r: r["entry"]["connective"]["all"].append(
        {"role": "sufficiency", "form": "band", "material": [{"family": "ATR%", "param": 14, "tf": "1h"}],
         "value": {"lo": {"raw": 1.0}, "hi": {"const": "NEUTRAL_0"}}}), "G6")
    # 歩6-1 拡張の番人（record＝記録スタイル・zone_sl.w＝帯幅の選択・L1 恒等で追加）
    broke("⑲ record は恒等レーン専用", lambda r: r.__setitem__("record", {"w_entry": "zone"}), "G6")

    def _rec_bad(r):
        r["meta"]["lane"] = "legacy"
        r["record"] = {"w_entry": "変な値"}
    broke("⑳ record.w_entry 不正", _rec_bad, "G5")
    broke("㉑ zone_sl.w 不正", lambda r: r["exits"][0]["exec"]["placement"]["level"].__setitem__("w", "変な値"), "G6")
    # 歩6-1 後半の番人（S1 里程標1＝天井入口・位置の出口・縮む TP）
    broke("㉒ ceiling_resting は恒等レーン専用", lambda r: r["entry"].__setitem__("type", "ceiling_resting"), "G6")

    def _ceil_no_split(r):
        r["meta"]["lane"] = "legacy"
        r["entry"] = {"type": "ceiling_resting", "split": {"gap_pct": {"legacy": 0.5}}}
    broke("㉓ ceiling の split 欠落", _ceil_no_split, "G5")
    broke("㉔ position_exits は恒等レーン専用", lambda r: r.__setitem__(
        "position_exits", {"uptrend_cut": {"reason": "TREND_CONT"}}), "G6")

    def _shrink_no_tmax(r):
        r["meta"]["lane"] = "legacy"
        r["exits"][1]["exec"]["placement"]["level"] = {"kind": "shrink", "from": "TP2",
                                                       "floor": {"const": "SCALP_FLOOR"}}
    broke("㉕ shrink の tmax 欠落", _shrink_no_tmax, "G5")

    def _peak_no_arm(r):
        r["meta"]["lane"] = "legacy"
        r["exits"][1]["exec"]["placement"]["level"] = {"kind": "peak_giveback",
                                                       "giveback": {"legacy": 0.5},
                                                       "floor": {"const": "SCALP_FLOOR"}}
    broke("㉖ peak_giveback の arm 欠落", _peak_no_arm, "G5")
    # 歩6-1 里程標9 の番人（v22 アンカー＝swing 水準／捕まった玉の印＝uptrend_cut mark と scope.trend_caught）
    def _swing_no_fb(r):
        r["meta"]["lane"] = "legacy"
        r["exits"][1]["exec"]["placement"]["level"] = {"kind": "swing", "target": "low",
                                                       "m": {"legacy": 24}, "buf": {"const": "V11_SL_BUF"}}
    broke("㉗ swing の fallback 欠落（落ちた時の戻り先が無い）", _swing_no_fb, "G5")

    def _swing_bad_target(r):
        r["meta"]["lane"] = "legacy"
        r["exits"][1]["exec"]["placement"]["level"] = {"kind": "swing", "target": "close",
                                                       "m": {"legacy": 24},
                                                       "fallback": {"kind": "zone", "target": "mid"}}
    broke("㉘ swing.target が low/high でない", _swing_bad_target, "G6")

    def _uc_bad_mode(r):
        r["meta"]["lane"] = "legacy"
        r["position_exits"] = {"uptrend_cut": {"mode": "投げる", "reason": "TREND_CONT"}}
    broke("㉙ uptrend_cut.mode が close/mark でない", _uc_bad_mode, "G6")

    def _uc_mark_bad_state(r):
        r["meta"]["lane"] = "legacy"
        r["position_exits"] = {"uptrend_cut": {"mode": "mark", "state": "変な印"}}
    broke("㉚ mark の state が trend_caught でない", _uc_mark_bad_state, "G6")
    broke("㉛ scope.trend_caught は恒等レーン専用", lambda r: r["exits"][1].__setitem__(
        "scope", {"trend_caught": True}), "G6")

    def _tc_without_mark(r):
        r["meta"]["lane"] = "legacy"
        r["exits"][1]["scope"] = {"trend_caught": True}   # 印を付ける側（mode=mark）が無い＝一度も発火しない枝
    broke("㉜ 印を受ける枝はあるが印を付ける側が無い", _tc_without_mark, "G5")

    # ★2026-08-15（段A の A-5-3）＝分位が範囲の外・書き方違いのレシピを止める（手書きのレシピ対策）。
    def _q_out(r):
        r["entry"]["connective"]["all"][1]["value"] = {"threshold_q": "q95"}   # 範囲は q10〜q90
    broke("㉝ 分位が探せる範囲の外（q95）", _q_out, "G5")

    def _q_bad(r):
        r["entry"]["connective"]["all"][1]["value"] = {"threshold_q": "q12.5"}  # 整数でない
    broke("㉞ 分位の書き方が違う（q12.5）", _q_bad, "G5")

    def _q_in(r):
        # メタ確認＝範囲の中（直す前の9段には無い q37）は通る＝止めすぎていない
        r["entry"]["connective"]["all"][1]["value"] = {"threshold_q": "q37"}
    _r_q_in = copy.deepcopy(okr)
    _q_in(_r_q_in)
    try:
        validate_recipe(_r_q_in)
    except RecipeError as e:
        ng.append(f"範囲の中の分位 q37（直す前の9段には無い）が拒否された: {e}")

    # ★2026-08-15（段A の A-5-4）＝入れ子の「ずらす本数」が範囲の外・整数でないレシピを止める。
    #   直す前は offset を「知っている鍵」として通すだけで、値を1つも見ていなかった。
    def _nest_cond(off) -> dict:
        return {"role": "env", "form": "streak", "value": {"n": 3, "offset": off},
                "inner": {"role": "env", "form": "level", "side": "below",
                          "value": {"const": "RSI_OB"},
                          "material": [{"family": "RSI", "param": 14, "tf": "1h"}]}}
    broke("㉟ ずらす本数が探せる範囲の外（offset=3）",
          lambda r: r["entry"]["connective"]["all"].__setitem__(1, _nest_cond(3)), "G5")
    broke("㊱ ずらす本数が整数でない（offset=0.5）",
          lambda r: r["entry"]["connective"]["all"].__setitem__(1, _nest_cond(0.5)), "G5")
    for _off_ok in (0, 1):                      # メタ確認＝範囲の中は通る（止めすぎていない）
        _r_off = copy.deepcopy(okr)
        _r_off["entry"]["connective"]["all"][1] = _nest_cond(_off_ok)
        try:
            validate_recipe(_r_off)
        except RecipeError as e:
            ng.append(f"範囲の中のずらす本数 offset={_off_ok} が拒否された: {e}")
    # 既知答え（里程標9）＝v22 アンカーの TP1/TP2 が「同じ判定で必ず同時に切り替わる」ことを電卓式で確認。
    # e37_scalp 1531-1541行＝安値×(1+V11_SL_BUF) が建値より下なら TP2＝その値・TP1＝(建値+安値)/2。
    # 下でなければ TP2 も TP1 も元の置き方（TP2＝反対側ゾーン手前／TP1＝(建値+中央)/2）へ同時に戻る。
    _ex9 = [
        {"name": "TP1", "reason": "PARTIAL_TP",
         "exec": {"method": "maker", "placement": {"kind": "resting", "fill": "profit",
                  "level": {"kind": "mix", "from": "entry",
                            "to_level": {"kind": "swing", "target": "low", "m": {"legacy": 24},
                                         "gate_buf": {"const": "V11_SL_BUF"},
                                         "fallback": {"kind": "zone", "target": "mid"}},
                            "frac": {"legacy": 0.5}}}}, "size_ratio": 0.5},
        {"name": "TP2", "reason": "TP_FILLED",
         "exec": {"method": "maker", "placement": {"kind": "resting", "fill": "profit",
                  "level": {"kind": "swing", "target": "low", "m": {"legacy": 24},
                            "buf": {"const": "V11_SL_BUF"},
                            "fallback": {"kind": "zone", "target": "opp",
                                         "buf": {"const": "V11_SL_BUF"}, "fallback": "mid"}}}},
         "size_ratio": 1.0},
    ]
    _geo9 = {"mid": np.array([97.0, 97.0]), "sup_hi": np.array([96.0, 96.0]),
             "sup_lo": np.array([95.0, 95.0]), "res_lo": np.array([99.0, 99.0]),
             "res_hi": np.array([101.0, 101.0]),
             "swing:low:24": np.array([98.0, 101.0])}     # i=0＝安値が建値より下（立つ）／i=1＝上（落ちる）
    _lv0 = _resolve_levels(_ex9, 0, 100.0, "SHORT", _geo9, "legacy")
    if abs(_lv0["TP2"] - 98.0 * (1 + e37.V11_SL_BUF)) > 1e-9 or abs(_lv0["TP1"] - 99.0) > 1e-9:
        ng.append(f"v22 アンカーの既知答え不一致（立つ側）: TP1={_lv0['TP1']} TP2={_lv0['TP2']}"
                  f"（TP1=99.0／TP2={98.0 * (1 + e37.V11_SL_BUF)} のはず）")
    _lv1 = _resolve_levels(_ex9, 1, 100.0, "SHORT", _geo9, "legacy")
    if abs(_lv1["TP2"] - 96.0 * (1 + e37.V11_SL_BUF)) > 1e-9 or abs(_lv1["TP1"] - 98.5) > 1e-9:
        ng.append(f"v22 アンカーの既知答え不一致（落ちる側＝元の置き方へ戻る）: TP1={_lv1['TP1']} "
                  f"TP2={_lv1['TP2']}（TP1=98.5／TP2={96.0 * (1 + e37.V11_SL_BUF)} のはず）")
    # 既知答え（里程標9）＝印が付いていない玉には、印つきの枝が当たらないこと（scope.trend_caught）。
    _b9 = {"name": "TCTP", "reason": "TREND_CAUGHT_TP", "scope": {"trend_caught": True},
           "exec": {"method": "maker", "placement": {"kind": "resting", "fill": "profit",
                    "level": {"kind": "pct", "base": "avg", "k": {"legacy": 0.0008, "side_sign": "profit"}}}},
           "size_ratio": 1.0}
    _df9 = pd.DataFrame({"ts": pd.date_range("2024-05-01", periods=2, freq="5min"),
                         "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0})
    _lotN = {"side": "SHORT", "avg": 100.0, "first_idx": 0, "add_count": 1,
             "max_fav": 100.0, "max_adv": 100.0}
    if _exit_fire_ok(_b9, _lotN, 1, _df9, {}, "legacy", {}):
        ng.append("印の無い玉に印つきの枝が当たった（scope.trend_caught が効いていない）")
    if not _exit_fire_ok(_b9, {**_lotN, "trend_caught": True}, 1, _df9, {}, "legacy", {}):
        ng.append("印の付いた玉に印つきの枝が当たらない（scope.trend_caught が過剰に弾いている）")
    # 既知答え（歩6-1 里程標5）＝ピーク反転ロックの水準（e37_scalp 1211行の電卓式と突き合わせ）
    _lotS = {"avg": 100.0, "pk_prev": 99.0, "max_fav": 99.0}      # SHORT・ピーク含み益 1.0（=1.0%≥arm 0.15%）
    _lvS = {"arm": {"legacy": 0.15}, "giveback": {"legacy": 0.5}, "floor": {"legacy": 0.0008}}
    _gotS = _peak_giveback_level(_lvS, _lotS, "SHORT")             # min(99+0.5×1, 100×(1−0.0008))=min(99.5,99.92)
    if _gotS is None or abs(_gotS - 99.5) > 1e-9:
        ng.append(f"peak_giveback(SHORT) の既知答え不一致: {_gotS}（99.5 のはず）")
    _lotF = {"avg": 100.0, "pk_prev": 99.9, "max_fav": 99.9}       # 含み益 0.1 < arm 0.15% ＝武装しない
    if _peak_giveback_level(_lvS, _lotF, "SHORT") is not None:
        ng.append("peak_giveback が武装前に水準を返した（arm 未達で None のはず）")
    _lotC = {"avg": 100.0, "pk_prev": 90.0, "max_fav": 90.0}       # 大きな含み益＝下限（建値フロア）で頭打ち
    _gotC = _peak_giveback_level(_lvS, _lotC, "SHORT")             # min(90+5, 99.92)=95.0 → 下限は効かない
    if _gotC is None or abs(_gotC - 95.0) > 1e-9:
        ng.append(f"peak_giveback の戻し計算が違う: {_gotC}（95.0 のはず）")
    _lotD = {"avg": 100.0, "pk_prev": 99.8, "max_fav": 99.8}       # 含み益 0.2＝武装する・戻し 0.1 → 99.9
    _gotD = _peak_giveback_level(_lvS, _lotD, "SHORT")             # min(99.9, 99.92)=99.9
    if _gotD is None or abs(_gotD - 99.9) > 1e-9:
        ng.append(f"peak_giveback の下限（建値フロア）が違う: {_gotD}（99.9 のはず）")
    # 歩4 拡張の既知答え（band／band_exclude／slope_avg／分位の解決＝合成列を電卓式と照合）
    a5 = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    df4 = pd.DataFrame({"ts": pd.date_range("2024-05-01", periods=5, freq="5min"),
                        "open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0, "RSI14__1h": a5})
    bandc = {"role": "env", "form": "band", "material": [{"family": "RSI", "param": 14, "tf": "1h"}],
             "value": {"lo": {"threshold_q": "q20"}, "hi": {"threshold_q": "q80"}}}
    qt = {"RSI14__1h": {"q20": 2.0, "q80": 4.0}}
    if list(_eval_cond(bandc, df4, {}, "", qt)) != [False, True, True, True, False]:
        ng.append("band の既知答え不一致（lo=2, hi=4 で [F,T,T,T,F] のはず）")
    if list(_eval_cond({**bandc, "form": "band_exclude"}, df4, {}, "", qt)) != [True, False, False, False, True]:
        ng.append("band_exclude の既知答え不一致（band の否定のはず）")
    try:
        _eval_cond(bandc, df4, {}, "", None)
        ng.append("分位が解決表なしで素通り（fail-closed が死んでいる）")
    except RecipeError:
        pass
    slc = {"role": "env", "form": "slope_avg", "side": "above",
           "material": [{"family": "RSI", "param": 14, "tf": "1h"}], "value": {"n": 1, "m": 2}}
    if list(_eval_cond(slc, df4, {}, "", None)) != [False, False, False, True, True]:
        ng.append("slope_avg の既知答え不一致（MA2 の1本傾き>0 で [F,F,F,T,T] のはず）")
    # 定数レジストリと実体のずれ検査（レジストリの値が実装から黙って離れない）
    ng += iref.const_registry_live_check({"SCALP_FLOOR": e37.SCALP_FLOOR, "V11_SL_BUF": e37.V11_SL_BUF,
                                          "BE_TTL_BARS": parts.BE_TTL_BARS})
    # ★手数料の分類の食い違い検査（2026-08-02 里程標9 で新設 → 同日 まこさん OK で比べ方を直した）。
    #   直した理由＝審判は全戦略ぶんの一覧を持つので、丸ごと比べると他の戦略の理由で必ず差が出る。
    #   いまは「その戦略が使う決済理由だけ」を比べる（詳しくは maker_taker_sync_check の説明）。
    _fee_ng: list[str] = []
    _src37 = inspect.getsource(e37)
    _fee_ng += maker_taker_sync_check("e37_scalp", _src37, tuple(e37._MAKER_EXIT), _score)
    # ★番人の番人＝2026-08-02 に実際に起きた事故をわざと再現して、検査が落ちることを毎回確かめる。
    #   事故の中身＝TREND_CAUGHT_TP が e37 の指値の一覧から抜けていて、戦略だけが成行として
    #   手数料を計算していた（値決め窓18ヶ月で 932玉・$294.42 ぶん実際より悲観的に出ていた）。
    #   これが落ちなければ、比べ方を直したときに検査を無力化したということ＝直ちに止める。
    _broken = tuple(x for x in e37._MAKER_EXIT if x != "TREND_CAUGHT_TP")
    if not maker_taker_sync_check("e37_scalp(わざと壊した)", _src37, _broken, _score):
        _fee_ng.append("番人の番人: TREND_CAUGHT_TP を抜いても手数料の分類の食い違い検査が落ちない"
                       "（＝検査が無力化されている・2026-08-02 の事故を捕まえられない）")
    # ══ E38 の検査（2026-08-04 新設・まこさん決定 2026-08-03「足す」→ 実装 OK 2026-08-04）════
    #   E38 は自分の記録処理を持たず e37._record を借りている（e38_logic_parts 342/345/347/354/
    #   356/359/362/400行の8か所）。だから E38 が使う指値の一覧は E37 のものが正本＝それを渡す。
    _src38 = inspect.getsource(parts)
    _fee_ng += maker_taker_sync_check("e38_logic_parts", _src38, tuple(e37._MAKER_EXIT), _score)
    # 番人＝E38 が e37._record を使い続けているか。E38 が自分の記録処理を持ち始めたら、上で渡した
    #   一覧が嘘になる（別戦略の一覧と比べたまま素通りする）ので、その瞬間に止める。
    #   ★条件を2つにした（2026-08-04）。理由＝「e37._record」だけを文字として探すと、
    #     e37._recordXXX のような別名がそれを含んでしまい、番人が反応しない（メタ確認で実際に素通りした）。
    #     ①呼び出しの丸括弧まで含めて探す ②E38 が自分の記録処理を定義していないこと、の両方を見る。
    if "e37._record(" not in _src38:
        _fee_ng.append("e38_logic_parts が e37._record( を呼んでいない＝手数料の分類の検査に渡す指値の"
                       "一覧が E37 のものではなくなった（E38 自身の一覧を渡す形へ直してから走らせる）")
    if re.search(r"^def _record", _src38, re.M):
        _fee_ng.append("e38_logic_parts が自分の記録処理 _record を定義している＝指値の一覧が E37 の"
                       "ものとは限らない（E38 自身の一覧を検査に渡す形へ直してから走らせる）")
    # 番人の番人＝E38 でも、指値の一覧から1つ抜くと検査が落ちることを毎回確かめる。
    _broken38 = tuple(x for x in e37._MAKER_EXIT if x != "SL_FILLED")
    if not maker_taker_sync_check("e38_logic_parts(わざと壊した)", _src38, _broken38, _score):
        _fee_ng.append("番人の番人: SL_FILLED を抜いても E38 の手数料の分類の検査が落ちない"
                       "（＝検査が無力化されている）")
    # ══ E36 の検査（2026-08-04 新設・案A＝実際に出た手数料の額で判定・E36 のコードは触らない）════
    _fee_ng += e36_maker_taker_behavior_check(_score)
    # 番人の番人＝指値と成行を丸ごと入れ替えた偽の審判を渡すと落ちること。
    #   ★特定の決済理由の名前に頼らない形にした（2026-08-04）。理由＝名前で書くと、その理由の分類が
    #     将来まこさんの承認で正しく変わったときに、番人の番人だけが誤って鳴る。入れ替えなら、
    #     E36 が使う決済理由が1つでも在れば必ず食い違う＝どの名前でも成り立つ。
    #   これで 2026-08-02 の事故の形（片方の一覧に登録が無い＝分類が食い違う）も同時に覆う。
    class _JudgeSwapped:                         # 偽の審判＝この場だけの作り物（score.py は無改造・H13）
        MAKER_EXIT_REASONS = set(_score.TAKER_EXIT_REASONS)
        TAKER_EXIT_REASONS = set(_score.MAKER_EXIT_REASONS)
    if not e36_maker_taker_behavior_check(_JudgeSwapped):
        _fee_ng.append("番人の番人: 審判の指値と成行を丸ごと入れ替えても E36 の手数料の分類の検査が"
                       "落ちない（＝検査が無力化されている・2026-08-02 の事故を捕まえられない）")
    ng += _fee_ng
    print("[番人 手数料の分類] E37（ソースの一覧を比べる）／E38（e37._record を借りている確認つき）／"
          "E36（実際に出た手数料の額で判定・コード無改変） → "
          + ("✅ 食い違いなし・番人の番人3件とも落ちた" if not _fee_ng else "❌ " + " ／ ".join(_fee_ng)))
    # ══ 監査 4-19（要件 R5 相場／R6 保有時間）の番人6件・2026-08-03 新設 ═══════════════════
    #   どれも「わざと壊すと落ちるか」を毎回その場で確かめる。落ちなければ直したことにしない。
    _bad419 = _selftest_4_19()
    ng += _bad419
    print("[番人 監査4-19] ①接続ファイルから相場の宣言を消す ②宣言が文字列（直す前の形） "
          "③一覧に無い相場の名前 ④データに無い列を宣言 ⑤新しい実行器で宣言を差し替えると売買記録が変わるか "
          "⑥役割の範囲が空／台帳に役割が無い ⑦古い売買ループでも宣言が効いているか "
          "＋E37とE38の宣言の食い違い → "
          + ("✅ 全部 落ちた（検査が生きている）" if not _bad419 else "❌ " + " ／ ".join(_bad419)))

    # 系統マップ: FAMILY_TEMPLATES の全 family が割当済み（G3 の前提）
    miss = iref.lineage_coverage(list(FAMILY_TEMPLATES))
    if miss:
        ng.append(f"FAMILY_TEMPLATES の family が系統マップに無い: {miss}")

    # ══ 名前の組み立ての往復テスト（2026-08-11・段6 の 6-7 で新設）══════════════════════
    #   何を守るか＝「材料カタログに列が在るのに engine_tuner が選べない」を二度と作らない。
    #   やり方＝材料カタログの列名を1つずつ family と数字に分解し（参照表 find）、この表で
    #   組み立て直して、元の名前と1文字も違わないことを確かめる。1件でも違えば ❌。
    #   ★番人の番人＝わざと1件の型を壊すと、この検査が落ちることも同時に確かめる。
    _rt_ng, _rt_n = _selftest_roundtrip()
    ng += _rt_ng
    print(f"[番人 名前の組み立て] 材料カタログの全 {_rt_n} 列を family＋数字に分解して組み立て直す"
          "（+ わざと型を1件 壊すと落ちるか） → "
          + ("✅ 全部 一致・壊すと落ちた" if not _rt_ng else "❌ " + " ／ ".join(_rt_ng)))
    # ══ 番人 並びの決まらない入れ物（2026-08-16 新設・A-1a-0 の2番）═══════════════════════
    #   何を守るか＝同じ入力なら同じ結果が出ること。手で場所の一覧を書かず、機械が全部 数える。
    #   ★番人の番人＝わざと set を回すコードを見せたら、ちゃんと見つけるか。
    #   ★2026-08-26（106番・読み比べの所見 Q3-3）＝対象の一覧の手書きをやめた。
    #     直す前は4本の名前をここに手で書いていた＝この検査の説明文が引いている
    #     「手書きの一覧は書き忘れると穴になる」が、テストの側で守られていなかった。
    #     いまは H2 の印（h2_pass.json＝engine_tuner の経路のファイル）から .py を引く。
    #     印が読めないときだけ、元の4本に落ちる（fail-open にせず、その旨を画面に出す）。
    #   ★印に書いてあるパスは、リポジトリの入口からの相対（下の階層＝tuner_adapters/ も入る）。
    #     ファイル名だけで探すと、その3本を落とす（2026-08-26 に実測して気づいた）。
    _uo_here = pathlib.Path(__file__).resolve()
    _uo_root = _uo_here.parents[4]                  # …/cat-bitget（リポジトリの入口）
    _uo_note = "H2 の印から引いた"
    try:
        _uo_mark = json.loads((_uo_here.parents[2] / ".claude" / "state" / "h2_pass.json")
                              .read_text(encoding="utf-8"))
        _uo_files = sorted(str(f) for f in (_uo_mark.get("files") or {}) if str(f).endswith(".py"))
        if not _uo_files:
            raise ValueError("印に .py が1本も無い")
        _uo_paths = [(f, _uo_root / f) for f in _uo_files]
    except Exception as _uo_e:
        _uo_note = f"★印を読めないので手書きの4本に落ちた（{str(_uo_e)[:40]}）"
        _uo_paths = [(f, _uo_here.parent / f) for f in
                     ("engine_tuner_exec.py", "engine_tuner_gen.py",
                      "tuner_judgement.py", "tuner_stats.py")]
    _uo_hits: list[str] = []
    _uo_seen = 0
    for _uf, _up in _uo_paths:
        if not _up.exists():
            _uo_hits.append(f"{_uf}: ファイルが無い（数え上げの対象が消えた）")
            continue
        _uo_seen += 1
        for _ln, _why in unordered_iteration_scan(_up.read_text(encoding="utf-8")):
            _uo_hits.append(f"{pathlib.Path(_uf).name}:{_ln} {_why}")
    if _uo_seen == 0:
        _uo_hits.append("数え上げの対象が0本になった（一覧の引き方が壊れた）")
    if not unordered_iteration_scan("def f():\n    s = {1, 2}\n    for x in s:\n        pass\n"):
        _uo_hits.append("番人の番人: わざと set を回すコードを見せても見つけない（検査が効いていない）")
    #   ★番人の番人2つ目（2026-08-26・106番・まこさん承認 462031cb…）＝見つけすぎないか。
    #     直す前はこの見本で 1件 出た（＝生成器の3行の誤報と同じ形・実装の前に実測）。
    #     別々の関数で同じ名前を使っているだけで、並びが決まらない所は1つも無い。
    #     dict は入れた順を保つ（Python 3.7 以降・実測で確認）。
    _uo_false = ("def a():\n"
                 "    fams = {}\n"
                 "    fams.setdefault('x', []).append(1)\n"
                 "    return [f for f in fams]\n"
                 "\n"
                 "\n"
                 "def b():\n"
                 "    fams = {1, 2}\n"
                 "    return fams\n")
    _uo_fp = unordered_iteration_scan(_uo_false)
    if _uo_fp:
        _uo_hits.append(f"番人の番人: 別の関数の同じ名前を誤って結び付けた（106番の誤報が戻った）: {_uo_fp}")
    #   ★番人の番人3つ目（同上）＝弱めすぎていないか。
    #     同じ関数の中で作った set を回すのは、今までどおり 1件 見つける（行も合う）。
    _uo_true = "def c():\n    got = {1, 2}\n    for x in got:\n        print(x)\n"
    _uo_tp = unordered_iteration_scan(_uo_true)
    if len(_uo_tp) != 1 or _uo_tp[0][0] != 3:
        _uo_hits.append(f"番人の番人: 同じ関数の中の set を回すのを見つけられない（検査が弱まった）: {_uo_tp}")
    #   ★番人の番人4〜9つ目（2026-08-26・読み比べの所見・まこさん承認 29ebcd26…）。
    #     どれも所見が実測で出した見本＝直す前は、この6件のうち5件が期待と逆だった。
    _uo_more = [
        # 位置を見るか（重い指摘 Q1-1）＝回すのが先、入れ直しが後なら、本物として見つける
        ("位置①本物（回した後で入れ直す）", 1,
         "def f():\n    s = {1, 2}\n    for x in s:\n        pass\n    s = sorted(s)\n    return s\n"),
        # 位置②＝入れ直しが先、回すのが後なら、見つけない
        ("位置②誤報（入れ直した後で回す）", 0,
         "def f(q):\n    for i in q:\n        s = {1, 2}\n    s = sorted(q)\n    for y in s:\n        pass\n"),
        # クラスの本体でも、別々の入れ物の同名を結び付けない（Q3-1・106番と同じ形）
        ("クラスの本体（106番と同じ形）", 0,
         "class A:\n    fams = {}\n    z = [f for f in fams]\n\n\nclass B:\n    fams = {1, 2}\n"),
        # async for も見る（Q2-2）
        ("async for", 1,
         "async def f(s):\n    s = {1, 2}\n    async for x in s:\n        pass\n"),
        # ループ変数の星つき（Q1-5）
        ("星つきのループ変数", 0,
         "def f(pairs):\n    s = {1, 2}\n    for a, *s in pairs:\n        pass\n    for x in s:\n        pass\n"),
        # 1つの内包表記の中で入れて回す（生成器 :4708 と同じ形）
        ("内包表記の中で入れて回す", 0,
         "def f(d, got):\n    got = {1, 2}\n"
         "    return [c for bn in d.values() for got in bn.values() for c in got]\n"),
    ]
    for _nm, _want, _sample in _uo_more:
        _got = unordered_iteration_scan(_sample)
        if len(_got) != _want:
            _uo_hits.append(f"番人の番人「{_nm}」: {_want} 件のはずが {len(_got)} 件: {_got}")
    ng += _uo_hits
    print(f"[番人 並びの決まらない入れ物] {_uo_seen} 本のファイルを機械で全部 数える（{_uo_note}）"
          "（+ 番人の番人9つ＝set を回すと見つける・別の関数の同名は結び付けない・同じ関数の中は"
          "見つける・位置を見る2つ・クラスの本体・async for・星つき・内包表記の中で入れて回す） → "
          + ("✅ 0 件・番人の番人9つとも期待どおり" if not _uo_hits else "❌ " + " ／ ".join(_uo_hits)))
    # ══ T-HYST 状態を保つ形（M2-2-5・2026-08-21 まこさん承認 24a453d6…）═══════════════════
    #   何を守るか＝並びの計算で書いた `_hold_state` が、決めごと①〜⑤のとおりに動くこと。
    #   ★確かめ方＝同じ決めごとを1バーずつのループで書いたものと、乱数200通りで突き合わせる。
    #     ループ版はここにだけ在る（速度が要らないため）＝2つが食い違ったら、どちらかが決めごとから外れた。
    #   ★番人の番人＝わざと「保つ最大の本数」を無視した版と比べたら、ちゃんと食い違うか。
    def _hold_loop(on_, off_, n_):
        """決めごと①〜⑤を、1バーずつ書いたもの（照合の相手・実行には使わない）。"""
        out_ = np.zeros(len(on_), bool)
        st, held = False, 0
        for i_ in range(len(on_)):
            if st:
                held += 1
            if off_[i_]:                        # ⑤ 同じバーで両方なら off を優先
                st, held = False, 0
            elif on_[i_]:                       # ①④ on のたびに数え直す
                st, held = True, 0
            if st and held >= int(n_):          # ④ n本 経ったら偽
                st, held = False, 0
            out_[i_] = st                       # ③ どちらも成立しなければ前の値を保つ
        return out_

    _hy_rng = np.random.default_rng(20260821)
    _hy_bad = 0
    for _t in range(200):
        _on = _hy_rng.random(300) < 0.05
        _off = _hy_rng.random(300) < 0.05
        _n = int(_hy_rng.integers(1, 60))
        if not np.array_equal(_hold_loop(_on, _off, _n), _hold_state(_on, _off, _n)):
            _hy_bad += 1
    if _hy_bad:
        ng.append(f"T-HYST: 並びの計算と1バーずつのループが {_hy_bad} 通りで食い違う（決めごと①〜⑤）")
    _hy_on = np.zeros(12, bool)
    _hy_on[1] = True
    _hy_off = np.zeros(12, bool)
    if int(_hold_state(_hy_on, _hy_off, 3).sum()) != 3:
        ng.append("T-HYST: 保つ最大の本数 3 を渡したのに、真になった本数が 3 でない（④が効いていない）")
    if _hold_state(_hy_on, _hy_on, 99).any():
        ng.append("T-HYST: 同じバーで on と off が両方 成立したのに真になった（⑤ off の優先が効いていない）")
    if np.array_equal(_hold_state(_hy_on, _hy_off, 3), _hold_state(_hy_on, _hy_off, 99)):
        ng.append("T-HYST の番人の番人: 保つ最大の本数を変えても結果が同じ＝上限が効いていない")
    print(f"[T-HYST 状態を保つ形] 乱数200通りでループ版と突き合わせ・上限・off の優先・番人の番人 → "
          + ("✅ 全部 pass" if not [x for x in ng if x.startswith('T-HYST')] else "❌ 落ちた"))
    # ══ G7 場面ごとの相場の法則（M2-B0・2026-08-30 に法則番号へ付け替え・通る／捨てるは直す前と同じ）════
    #   通る束2種（range・uptrend）が通り、わざと法則を破った束7通り（C1・C4・C6・R1・R8・R7・S1 を
    #   1件ずつ）が、それぞれの法則番号で止まることを確かめる（直す前の K-1〜K-7 と同じ結果）。
    def _g7_meta(name, tree):
        return {"regime": {"name": name, "entry_col": "g7_ent", "block_col": None,
                           "build": {"entry": {"out_col": "g7_out", "tree": tree}, "block": None}}}

    def _g7_run(name, tree):
        try:
            _check_regime_meta(_g7_meta(name, tree), lane="", legacy_used=[])
            return None
        except SystemExit as e:
            return str(e)

    def _g7_level(fam, param, tf, side, q):
        return {"role": "env", "form": "level", "side": side,
                "material": [{"family": fam, "param": param, "tf": tf}],
                "value": {"threshold_q": q}}

    def _g7_hys(on, off):
        return {"form": "hysteresis", "on": on, "off": off, "value": {"n": 100}}

    _g7_w = _g7_level("BB幅", [20, 2], "1h", "above", "q30")
    _g7_w_off = _g7_level("BB幅", [20, 2], "1h", "below", "q10")
    _g7_struct = {"role": "location", "form": "band",
                  "material": [{"family": "S-Rタッチ数", "param": [144, 0.006], "tf": "15m"}],
                  "value": {"lo": {"threshold_q": "q10"}, "hi": {"threshold_q": "q90"}}}
    _g7_dir = _g7_level("DI差", 14, "1h", "above", "q70")
    _g7_dir_off = _g7_level("DI差", 14, "1h", "below", "q30")
    _g7_dir5m = _g7_level("DI差", 14, "5m", "above", "q70")
    _g7_dir5m_off = _g7_level("DI差", 14, "5m", "below", "q30")
    _g7_adx = _g7_level("ADX", 14, "1h", "above", "q70")
    _g7_adx_off = _g7_level("ADX", 14, "1h", "below", "q30")
    _g7_adx5m = _g7_level("ADX", 14, "5m", "above", "q70")

    # ★M2-B-2b（2026-08-30）＝通る束: range は、レンジの法則10件（判定9＋置き場1）を全部 満たす形に作り直した。
    #   帯＝S-Rタッチ数 15m（R1・R3＝構造・位置 かつ 上位足）／幅がコストを超える＝geo W% above（R7）／
    #   幅が狭い＝BB幅 below（R6・R10＝性質 ボラ量）を streak で包む（R4）／not（ADX above）＝ADX below（R5・R8）／
    #   hysteresis（C6）／系統は 構造・位置 を除いて ボラ1・トレンド1（R2）。
    _g7_geo_w = {"role": "location", "form": "level", "material": [{"geo": "W%"}],
                 "side": "above", "value": {"threshold_q": "q30"}}
    _g7_sq = _g7_level("BB幅", [20, 2], "1h", "below", "q30")
    _g7_streak = {"role": "env", "form": "streak", "value": {"n": 3}, "inner": _g7_sq}
    _g7_struct5m = {"role": "location", "form": "band",
                    "material": [{"family": "S-Rタッチ数", "param": [144, 0.006], "tf": "5m"}],
                    "value": {"lo": {"threshold_q": "q10"}, "hi": {"threshold_q": "q90"}}}
    _g7_atr = _g7_level("ATR%", 14, "1h", "above", "q50")
    _g7_range_ok = {"all": [_g7_hys({"all": [_g7_struct, _g7_geo_w, _g7_streak]}, _g7_w_off), {"not": _g7_adx}]}
    _g7_cases = [
        ("通る束: range", "range", _g7_range_ok, None),
        ("通る束: uptrend", "uptrend", {"all": [_g7_hys(_g7_dir, _g7_dir_off)]}, None),
        ("C1 破り: 強さだけの uptrend", "uptrend", {"all": [_g7_hys(_g7_adx, _g7_adx_off)]}, "C1"),
        ("C4 破り: 5分足だけ", "uptrend", {"all": [_g7_hys(_g7_dir5m, _g7_dir5m_off)]}, "C4"),
        ("C6 破り: hysteresis なし", "downtrend", {"all": [_g7_dir]}, "C6"),
        ("R1 破り: 帯なし", "range",
         {"all": [_g7_hys({"all": [_g7_w]}, _g7_w_off), {"not": _g7_adx}]}, "R1"),
        ("R8 破り: 否定なし", "range",
         {"all": [_g7_hys({"all": [_g7_struct, _g7_w]}, _g7_w_off)]}, "R8"),
        ("R7 破り: 幅なし", "range",
         {"all": [_g7_hys({"all": [_g7_struct, _g7_dir]}, _g7_dir_off), {"not": _g7_adx}]}, "R7"),
        ("S1 破り: スパイクに比の部品なし", "spike", {"all": [_g7_adx5m]}, "S1"),
        # ── M2-B-2b の破り7通り（R2・R3・R4・R5・R6・R7 側逆・R10）＝通る束: range を1か所ずつ壊す ──
        ("R2 破り: ボラ系統が2本（BB幅＋ATR%）", "range",
         {"all": [_g7_hys({"all": [_g7_struct, _g7_geo_w, _g7_streak, _g7_atr]}, _g7_w_off), {"not": _g7_adx}]}, "R2"),
        ("R3 破り: 帯の部品が 5m だけで geo なし", "range",
         {"all": [_g7_hys({"all": [_g7_struct5m, _g7_streak]}, _g7_w_off), {"not": _g7_adx}]}, "R3"),
        ("R4 破り: streak なし", "range",
         {"all": [_g7_hys({"all": [_g7_struct, _g7_geo_w, _g7_sq]}, _g7_w_off), {"not": _g7_adx}]}, "R4"),
        ("R5 破り: not（ADX below）＝強い側", "range",
         {"all": [_g7_hys({"all": [_g7_struct, _g7_geo_w, _g7_streak]}, _g7_w_off), {"not": _g7_adx_off}]}, "R5"),
        ("R6 破り: 幅が above だけ（off 側の below の写しは数えない）", "range",
         {"all": [_g7_hys({"all": [_g7_struct, _g7_geo_w,
                                   {"role": "env", "form": "streak", "value": {"n": 3}, "inner": _g7_w}]}, _g7_w_off),
                  {"not": _g7_adx}]}, "R6"),
        ("R7 破り: 幅が below だけ（コスト超えの above が無い）", "range",
         {"all": [_g7_hys({"all": [_g7_struct, _g7_streak]}, _g7_w_off), {"not": _g7_adx}]}, "R7"),
        ("R10 破り: ボラ量の部品なし", "range",
         {"all": [_g7_hys({"all": [_g7_struct, _g7_geo_w,
                                   {"role": "env", "form": "streak", "value": {"n": 3}, "inner": _g7_adx_off}]},
                          _g7_w_off)]}, "R10"),
    ]
    _g7_ng = []
    for _lbl, _nm, _tr, _want in _g7_cases:
        _msg = _g7_run(_nm, _tr)
        if _want is None:
            if _msg is not None:
                _g7_ng.append(f"G7: {_lbl} が通らない: {str(_msg)[:160]}")
        elif _msg is None or "G7" not in _msg or _want not in _msg:
            _g7_ng.append(f"G7: {_lbl} が {_want} で止まらない（{str(_msg)[:100]}）")
    ng += _g7_ng
    print(f"[G7 場面ごとの相場の法則] 通る束2種・わざと破った束14通り（既存7＝C1・C4・C6・R1・R8・R7・S1 ＋ "
          f"M2-B-2b の7＝R2・R3・R4・R5・R6・R7側逆・R10） → "
          + ("✅ 全部 期待どおり" if not _g7_ng else "❌ " + " ／ ".join(_g7_ng)))
    _cnt = regime_law_counts()
    print(f"[相場の法則の読み込み] 審査に使う {_cnt.get('審査に使う')}件 ／ 置き場あり {_cnt.get('置き場あり')}件 ／ "
          f"持たない {_cnt.get('持たない')}件")
    # ── B0 M2-B0 の壊しテスト（設計書 iter="m2-b0-law-reader-20260830" §4・2026-08-30）──────────────
    #   法則の読み込みが fail-closed か（B0-1〜B0-4）・審査が法則に追従するか（B0-5・B0-6＝差し替え注入。
    #   ファイルは書き替えない＝覚えを一時差し替えて戻す。実ファイルでの1回の実測は検収で別に行う）。
    global _REGIME_LAWS
    _b0_ng: list[str] = []
    try:
        load_regime_laws(path=pathlib.Path("/nonexistent/regime_laws_b0.json"))
        _b0_ng.append("B0-1: 無いファイルで止まらない")
    except SystemExit:
        pass
    try:
        _validate_law("B0", {"掛かる場面": ["range"], "型": "知らない型"})
        _b0_ng.append("B0-2: 知らない型で止まらない")
    except SystemExit:
        pass
    try:
        _validate_law("B0", {"掛かる場面": ["rangee"], "型": "形を持つ", "形": "not"})
        _b0_ng.append("B0-3: 知らない場面名で止まらない")
    except SystemExit:
        pass
    try:
        _validate_law("B0", {"掛かる場面": ["range"], "型": "部品を数える",
                             "数える部品": {"系統": ["無い系統"]}, "本数": 1})
        _b0_ng.append("B0-4: 知らない系統名で止まらない")
    except SystemExit:
        pass
    _b0_keep = load_regime_laws()
    try:
        _b0_inj = json.loads(json.dumps(_b0_keep))
        for _x in _b0_inj:
            if _x["番号"] == "R7":
                _x["判定"]["数える部品"]["family"] = [f for f in _x["判定"]["数える部品"]["family"]
                                                      if f != "BB幅"]
                _x["判定"]["数える部品"]["geo"] = []
        _REGIME_LAWS = _b0_inj
        _b0_msg = _g7_run("range", _g7_range_ok)
        if _b0_msg is None or "R7" not in _b0_msg:
            _b0_ng.append(f"B0-5: R7 の幅の一覧から BB幅 を消したのに、BB幅 だけの束が R7 で"
                          f"止まらない（{str(_b0_msg)[:80]}）＝審査が法則に追従していない")
        _REGIME_LAWS = [x for x in _b0_keep if x["番号"] != "C6"]
        _b0_msg = _g7_run("downtrend", {"all": [_g7_dir]})
        if _b0_msg is not None:
            _b0_ng.append(f"B0-6: C6 を外したのに hysteresis の無い束が通らない（{str(_b0_msg)[:80]}）")
    finally:
        _REGIME_LAWS = _b0_keep
    # ── M2-B-2b の fail-closed 6通り（B0-7〜B0-12）＝知らない形・側・上限・置き場なし・性質・かつ ──
    for _lbl, _j in (
        ("B0-7: 知らない形（within_n）で止まらない", {"掛かる場面": ["range"], "型": "形を持つ", "形": "within_n"}),
        ("B0-8a: 側の値が above/below 以外で止まらない",
         {"掛かる場面": ["range"], "型": "部品を数える", "数える部品": {"family": ["ADX"], "側": {"ADX": "left"}}, "本数": 1}),
        ("B0-8b: family の無い側で止まらない",
         {"掛かる場面": ["range"], "型": "部品を数える", "数える部品": {"系統": ["ボラ"], "側": {"ADX": "below"}}, "本数": 1}),
        ("B0-9: 系統を重ねない の上限 0 で止まらない",
         {"掛かる場面": ["range"], "型": "系統を重ねない", "除く系統": [], "上限": 0}),
        ("B0-11: 知らない性質で止まらない",
         {"掛かる場面": ["range"], "型": "部品を数える", "数える部品": {"性質": "無い性質"}, "本数": 1}),
        ("B0-12: かつ が真偽でなくて止まらない",
         {"掛かる場面": ["range"], "型": "部品を数える", "数える部品": {"かつ": "yes", "系統": ["ボラ"]}, "本数": 1}),
    ):
        try:
            _validate_law("B0", _j)
            _b0_ng.append(_lbl)
        except SystemExit:
            pass
    import tempfile as _tmpf
    with _tmpf.TemporaryDirectory() as _td:
        _pth = pathlib.Path(_td) / "regime_laws_b0.json"
        _pth.write_text(json.dumps({"判定を揃えた場面": ["レンジ"],
                                    "法則": [{"番号": "R99", "場面": "レンジ", "一文": "見本"},
                                             {"番号": "C99", "場面": "共通", "一文": "見本",
                                              "機械が読む判定": {"掛かる場面": ["range"], "型": "形を持つ", "形": "not"}}]},
                                   ensure_ascii=False), encoding="utf-8")
        try:
            load_regime_laws(path=_pth)
            _b0_ng.append("B0-10: 判定を揃えた場面の法則に判定も置き場も無いのに止まらない")
        except SystemExit:
            pass
    ng += _b0_ng
    print("[B0 相場の法則の読み込み] fail-closed 10通り・差し替え注入2通り → "
          + ("✅ 全部 期待どおり" if not _b0_ng else "❌ " + " ／ ".join(_b0_ng)))
    print("=" * 80)
    # ══ 97番＝出口の発火条件が「形」を見る（設計書 v3 やること4・2026-08-25・まこさん承認 9231be44…）═══
    #   何を守るか＝出口の指標の条件が、入口と同じ評価器（_eval_cond）で評価されること（傾き・交差・差・ローソク）。
    #   直す前（60回目・worklog 20260825 §27 の実測）＝材料の値と数字の1点比較だけ＝上がる列でも下がる列でも同じ結果。
    #   ★壊し方の見本は固定（C7 の偽レシピ11通り）。数字は列の作り方だけ（閾値は名前つき定数・分位は見本の解決表）。
    _x_ng: list[str] = []
    _xn = 60
    _xdf = pd.DataFrame({"ts": pd.date_range("2024-05-01", periods=_xn, freq="5min"),
                         "open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0})
    _xdf["close"] = np.where(np.arange(_xn) % 2 == 0, 101.0, 99.0)     # 陽線・陰線が交互（candle_dir 用）
    _xup = np.linspace(50.0, 90.0, _xn)                                 # 上がり続ける列（最後 90）
    _xdn = np.linspace(90.0, 50.0, _xn)                                 # 下がり続ける列（最後 50）
    _xm14 = {"family": "RSI", "param": [14], "tf": "5m"}               # 列名 RSI14__5m（名前は組み立て表が決める）
    _xm7 = {"family": "RSI", "param": [7], "tf": "5m"}                 # 列名 RSI7__5m
    _xlot = {"side": "SHORT", "avg": 100.0, "first_idx": 0, "add_count": 1, "max_fav": 100.0, "max_adv": 100.0}

    def _xdata(col14, col7=None):
        d = _xdf.copy()
        d["RSI14__5m"] = np.asarray(col14, float)
        if col7 is not None:
            d["RSI7__5m"] = np.asarray(col7, float)
        return d

    def _xfire(fire, d, qtable=None, i=None):
        b = {"name": "X", "reason": "BREAKOUT_CUT", "fire": fire}
        fc = _collect_fire_cols({"exits": [b]}, d, {}, "", qtable)
        return _exit_fire_ok(b, dict(_xlot), (_xn - 1) if i is None else int(i), d, {}, "", fc)

    def _xc(form, **kw):
        c = {"role": "env", "form": form}
        c.update(kw)
        return c

    # C1 slope が傾きを見る（side=above：上がる列→成立・下がる列→不成立／below：その逆）
    _xs = _xc("slope", side="above", material=[_xm14], value={"n": 5})
    _xs_b = _xc("slope", side="below", material=[_xm14], value={"n": 5})
    _got1 = (_xfire({"all": [_xs]}, _xdata(_xup)), _xfire({"all": [_xs]}, _xdata(_xdn)),
             _xfire({"all": [_xs_b]}, _xdata(_xup)), _xfire({"all": [_xs_b]}, _xdata(_xdn)))
    if _got1 != (True, False, False, True):
        _x_ng.append(f"C1: slope が傾きを見ていない（above 上/下・below 上/下＝{_got1}・期待 (True, False, False, True)）")
    # C3(i) cross＝交差のバーだけ真・前後は偽・最初のバーは偽
    _xcr = _xc("cross", material=[_xm14, _xm7], value={"direction": "up"})
    _x70 = np.full(_xn, 70.0)
    _xk = int(np.argmax(_xup > 70.0))                                   # 70 を初めて上抜くバー
    _dcr = _xdata(_xup, _x70)
    _got3 = (_xfire({"all": [_xcr]}, _dcr, i=_xk), _xfire({"all": [_xcr]}, _dcr, i=_xk - 1),
             _xfire({"all": [_xcr]}, _dcr, i=_xk + 1), _xfire({"all": [_xcr]}, _dcr, i=0))
    if _got3 != (True, False, False, False):
        _x_ng.append(f"C3: cross が交差のバーだけ真にならない（交差/前/後/最初＝{_got3}）")
    # C4 diff＝2本目の材料が効く（2本目を入れ替えると結果が変わる）
    _xdf2 = _xc("diff", side="above", material=[_xm14, _xm7], value={"th": {"n": 5}})
    _got4 = (_xfire({"all": [_xdf2]}, _xdata(_xup, np.zeros(_xn))), _xfire({"all": [_xdf2]}, _xdata(_xup, np.full(_xn, 1000.0))))
    if _got4 != (True, False):
        _x_ng.append(f"C4: diff の2本目が効いていない（2本目=0／1000＝{_got4}・期待 (True, False)）")
    # C5 candle_dir＝陽線／陰線で逆の結果
    _xcd = _xc("candle_dir", value={"dir": "bull"})
    _xcd_b = _xc("candle_dir", value={"dir": "bear"})
    _dcd = _xdata(_xup)
    _got5 = (_xfire({"all": [_xcd]}, _dcd, i=10), _xfire({"all": [_xcd]}, _dcd, i=11),
             _xfire({"all": [_xcd_b]}, _dcd, i=10), _xfire({"all": [_xcd_b]}, _dcd, i=11))
    if _got5 != (True, False, False, True):
        _x_ng.append(f"C5: candle_dir が陽線／陰線で逆にならない（bull 偶/奇・bear 偶/奇＝{_got5}）")
    # C12 分位が出口で解ける（鍵1つの解決表・鍵が無ければ fail-closed）
    _xq = _xc("level", side="above", material=[_xm14], value={"threshold_q": "q50"})
    _got12 = (_xfire({"all": [_xq]}, _xdata(_xup), qtable={"RSI14__5m": {"q50": 70.0}}),
              _xfire({"all": [_xq]}, _xdata(_xup), qtable={"RSI14__5m": {"q50": 95.0}}))
    if _got12 != (True, False):
        _x_ng.append(f"C12: 出口で分位（q50）が解けていない（q50=70／95＝{_got12}・期待 (True, False)）")
    try:
        _xfire({"all": [_xq]}, _xdata(_xup), qtable=None)
        _x_ng.append("C12: 解決表が無いのに分位の条件が通った（fail-closed が効いていない）")
    except RecipeError:
        pass
    # C13 not が評価される（内側が真なら偽・KeyError が出ない）
    _xlv = _xc("level", side="above", material=[_xm14], value={"n": 5})
    try:
        _got13 = (_xfire({"not": {"all": [_xlv]}}, _xdata(_xup)), _xfire({"all": [_xlv]}, _xdata(_xup)))
        if _got13 != (False, True):
            _x_ng.append(f"C13: not が評価されていない（not/素＝{_got13}・期待 (False, True)）")
    except KeyError as e:
        _x_ng.append(f"C13: not を出口 fire に置くと KeyError（{e}）")
    # C2 入口の評価器との一致＝8組（level・slope・diff × na=fail／na=pass ＝6・cross・candle_dir＝各1）
    _xnan = _xup.copy()
    _xnan[30] = np.nan                                                  # 欠損を1バー入れる
    _pairs2 = []
    for _na in (None, "pass"):
        _v = {"n": 5} if _na is None else {"n": 5, "na": "pass"}
        _pairs2.append(("level", _xc("level", side="above", material=[_xm14], value=_v), _xdata(_xnan)))
        _pairs2.append(("slope", _xc("slope", side="above", material=[_xm14], value=_v), _xdata(_xnan)))
        _vd = {"th": {"n": 5}} if _na is None else {"th": {"n": 5}, "na": "pass"}
        _pairs2.append(("diff", _xc("diff", side="above", material=[_xm14, _xm7], value=_vd), _xdata(_xnan, _x70)))
    _pairs2.append(("cross", _xcr, _xdata(_xnan, _x70)))
    _pairs2.append(("candle_dir", _xcd, _xdata(_xnan)))
    for _nm2, _c2, _d2 in _pairs2:
        _arr = _eval_cond(_c2, _d2, {}, "", None)
        _per = [_xfire({"all": [_c2]}, _d2, i=_i2) for _i2 in range(_xn)]
        if [bool(x) for x in _arr] != _per:
            _bad2 = [j for j in range(_xn) if bool(_arr[j]) != _per[j]]
            _x_ng.append(f"C2: {_nm2} で出口の判定が入口の評価器と食い違うバーが {len(_bad2)} 本（例 {_bad2[:3]}）")
    # C7 検査が締まる＝偽レシピ11通りが指定のコード（G5／G6）と理由の言葉で拒否される
    def _xbroke(name, cond, want_code, want_word):
        r = copy.deepcopy(okr)
        r["exits"][1]["fire"] = {"all": [cond]}
        try:
            validate_recipe(r)
            _x_ng.append(f"C7: {name} が検査を素通り（{want_code}・『{want_word}』で止まるはず）")
        except RecipeError as e:
            if want_code not in str(e) or want_word not in str(e):
                _x_ng.append(f"C7: {name} の止まり方が違う＝{str(e)[:90]}（期待 {want_code}・『{want_word}』）")
    _xpre = {"op": "ts_max", "n": 20}
    _xbroke("① band を出口の fire に", _xc("band", material=[_xm14], value={"lo": {"const": "RSI_OS"}, "hi": {"const": "RSI_OB"}}), "G5", "出口の発火条件で使えない")
    _xbroke("② state×slope", _xc("slope", side="above", material=[{"state": "hold_min"}], value={"n": 5}), "G6", "玉の状態の条件は形 level だけ")
    _xbroke("③ slope の above_strict", _xc("slope", side="above_strict", material=[_xm14], value={"n": 5}), "G5", "strict")
    _xbroke("④ diff の below_strict", _xc("diff", side="below_strict", material=[_xm14, _xm7], value={"th": {"const": "NEUTRAL_0"}}), "G5", "strict")
    _xbroke("⑤ state＋pre", _xc("level", side="above", material=[{"state": "hold_min", "pre": _xpre}], value={"n": 60}), "G6", "前処理")
    _xbroke("⑥ slope（pre_ok=False）＋pre", _xc("slope", side="above", material=[{**_xm14, "pre": _xpre}], value={"n": 5}), "G6", "前処理")
    _xbroke("⑦ value に ref", _xc("level", side="above", material=[_xm14], value={"ref": _xm7}), "G5", "出口")
    _xbroke("⑧ 材料に state と指標の混在", _xc("diff", side="above", material=[_xm14, {"state": "mfe_pct"}], value={"th": {"const": "NEUTRAL_0"}}), "G6", "混ぜられない")
    _xbroke("⑨ 種別の鍵が2つ（geo＋state）", _xc("level", side="above", material=[{"geo": "W%", "state": "hold_min"}], value={"n": 60}), "G6", "種別の鍵が2つ以上")
    _xbroke("⑩ state に threshold_q", _xc("level", side="above", material=[{"state": "hold_min"}], value={"threshold_q": "q50"}), "G6", "分位")
    _xbroke("⑪ candle_dir に材料", _xc("candle_dir", material=[_xm14], value={"dir": "bull"}), "G5", "材料は書けない")
    # 正しい出口の条件5形は検査を通る（過剰に弾いていないこと）
    for _nm_ok, _c_ok in (("level", _xc("level", side="above", material=[_xm14], value={"const": "RSI_OB"})),
                          ("slope", _xs), ("cross", _xcr), ("diff", _xdf2), ("candle_dir", _xcd)):
        r_ok = copy.deepcopy(okr)
        r_ok["exits"][1]["fire"] = {"all": [_c_ok]}
        try:
            validate_recipe(r_ok)
        except RecipeError as e:
            _x_ng.append(f"C7: 正しい出口の条件（{_nm_ok}）が拒否された＝{str(e)[:90]}")
    ng += _x_ng
    print("[番人 97番 出口の発火条件が形を見る] C1 傾き／C3 交差／C4 差の2本目／C5 ローソク／C12 分位／C13 not／"
          "C2 入口の評価器と一致8組／C7 偽レシピ11通り＋正しい5形 → "
          + ("✅ 全部 期待どおり" if not _x_ng else "❌ " + " ／ ".join(_x_ng)))
    print("engine_tuner_exec 自己検査（スキーマ検証器の番人＝壊したレシピ36種で全部止まる・正しい5種は通る・歩4/歩6-1 拡張の既知答え込み）")
    print("=" * 80)
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        raise SystemExit(1)
    print("  ✅ 全部 pass（G1〜G6・legacy 隔離・placement・定数レジストリの実体照合）")


def main() -> int:
    ap = argparse.ArgumentParser(description="歩3 実行器＝レシピ（条件データ）を共通の売買ループで走らせる")
    ap.add_argument("--selftest", action="store_true", help="壊したレシピ25種で全部止まることの機械確認（歩4/歩6-1 拡張の既知答え込み）")
    ap.add_argument("--identity", action="store_true", help="恒等検収（値決め窓・S2 md5 完全一致＋R14）")
    ap.add_argument("--identity-quick", action="store_true", help="恒等検収の短窓デバッグ（値決め窓の頭90日）")
    ap.add_argument("--identity-l1", action="store_true", help="恒等検収 L1（歩6-1＝採用中 L1 の書き写し・run_long_support と md5 完全一致）")
    ap.add_argument("--identity-l1-quick", action="store_true", help="L1 恒等の短窓デバッグ（値決め窓の頭90日）")
    ap.add_argument("--identity-s1", action="store_true", help="恒等検収 S1 里程標1（歩6-1 後半＝天井入口＋v18 基本出口の骨格・run_continuous_v11 と md5 完全一致）")
    ap.add_argument("--identity-s1-quick", action="store_true", help="S1 恒等の短窓デバッグ（値決め窓の頭90日）")
    ap.add_argument("--validate", type=str, default=None, help="レシピ json を検証だけする")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if a.validate:
        rep = validate_recipe(json.loads(pathlib.Path(a.validate).read_text(encoding="utf-8")))
        print(json.dumps(rep, ensure_ascii=False, indent=1))
        return 0
    if a.identity or a.identity_quick:
        return run_identity(quick=a.identity_quick)
    if a.identity_l1 or a.identity_l1_quick:
        return run_identity_l1(quick=a.identity_l1_quick)
    if a.identity_s1 or a.identity_s1_quick:
        return run_identity_s1(quick=a.identity_s1_quick)
    ap.print_help()
    return 0


# ── H2 実行時の守り（2026-08-16 まこさん GO「H2 完全化」の層3・穴④）──────────────────
#    自分のコードに未来参照の典型（shift にマイナスの数字・rolling の center を True）が無いことを、
#    読み込みのたびに ratchet_guards で機械確認する。違反が入ると import の瞬間に止まる＝
#    偽の数字を出す前に落ちる。説明文では誤発火しない（行内コメントを外してから見る）。
import pathlib as _h2_pathlib                            # noqa: E402
import ratchet_guards as _h2_rg                          # noqa: E402
_h2_rg.assert_no_future_ref(_h2_pathlib.Path(__file__).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
