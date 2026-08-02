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
import json
import pathlib
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
         "streak", "within_n", "diff", "touch", "candle_dir")
NEST_FORMS = ("streak", "within_n")          # 入れ子形（内側は単純形のみ・1段まで）
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

# ── 材料の名前組み立て（family×param×tf → カタログ名・G6 fail-closed）──
# 単純数値パラメータの family だけ登録（複合パラメータ＝MACD 等は歩4 で拡張＝未登録は生成不可）。
FAMILY_TEMPLATES = {
    "RSI": "RSI{p}", "ROC": "ROC{p}", "ADX": "ADX{p}", "DI差": "DI差{p}",
    "Stoch%K": "Stoch%K{p}", "Stoch%D": "Stoch%D{p}", "MFI": "MFI{p}", "CMF": "CMF{p}",
    "ATR%": "ATR%{p}", "realized_vol": "realized_vol{p}", "Donchian幅": "Donchian幅%{p}",
    "zscore": "zscore{p}", "zscore_return": "zscore_return{p}", "volume_ratio": "volume_ratio{p}",
    "RCI": "RCI{p}", "EMA傾き": "EMA{p}傾き%", "close vs EMA": "close vs EMA{p}%",
    "close vs SMA": "close vs SMA{p}%", "fib位置": "fib位置{p}",
}
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


def _walk(node, depth=0, out=None, depths=None):
    """つなぎ木を歩いて (条件, 深さ) を集める。未知ノードは拒否。"""
    out = [] if out is None else out
    depths = [] if depths is None else depths
    if _is_cond(node):
        out.append(node)
        depths.append(depth)
        return out, depths
    if not isinstance(node, dict):
        _fail("G5", f"つなぎ木に不明なノード: {node!r}")
    if "all" in node or "any" in node:
        for ch in node.get("all", node.get("any", [])):
            _walk(ch, depth + 1, out, depths)
        return out, depths
    if "if" in node and "then" in node:
        _walk(node["if"], depth + 1, out, depths)
        _walk(node["then"], depth + 1, out, depths)
        return out, depths
    _fail("G5", f"つなぎ木のノードが all/any/if-then/条件 のどれでもない: {list(node)}")


def _tree_depth(node, depth=0) -> int:
    if _is_cond(node):
        return depth
    if "all" in node or "any" in node:
        kids = node.get("all", node.get("any", []))
        return max([_tree_depth(ch, depth + 1) for ch in kids] + [depth])
    if "if" in node:
        return max(_tree_depth(node["if"], depth + 1), _tree_depth(node["then"], depth + 1))
    return depth


def _material_name(m: dict, lane: str) -> tuple[str, str]:
    """材料1本を検証して (種別, 解決名) を返す。種別＝col/geo/state/time/legacy_col。"""
    if not isinstance(m, dict):
        _fail("G6", f"材料が dict でない: {m!r}")
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
    fam, prm, tf = m.get("family"), m.get("param"), m.get("tf")
    if not fam or not tf:
        _fail("G6", f"材料の3軸（family×param×tf）が欠けている: {m}")
    tpl = FAMILY_TEMPLATES.get(fam)
    if tpl is None:
        _fail("G6", f"family の名前組み立てが未登録: {fam}（複合パラメータ family は歩4 で拡張＝生成不可）")
    name = tpl.format(p=prm)
    ent, _p = iref.find(name)
    if ent is None:
        _fail("G6", f"カタログに無い材料: {name}（indicator_reference_diag に未登録）")
    if ent["family"] != fam:
        _fail("G6", f"材料の family がカタログと食い違う: {fam} → {name} は {ent['family']}")
    return "col", f"{name}__{tf}"


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
             "lo", "hi", "th", "m"}
    bad = set(v) - known
    if bad:
        _fail("G6", f"{cond_desc}: 値に未知のフィールド {sorted(bad)}（生の数字の閾値の混入経路＝拒否）")
    if "legacy" in v and lane != "legacy":
        _fail("G6", f"{cond_desc}: legacy 値は恒等検収レーン専用（探索は生成できない・§2.4-④）")
    if "legacy" in v:
        legacy_used.append(f"{cond_desc}: legacy={v['legacy']}")
    if "const" in v and v["const"] not in iref.CONST_REGISTRY:
        _fail("G6", f"{cond_desc}: 名前つき定数レジストリに無い定数: {v['const']}")
    if "n" in v and (not isinstance(v["n"], int) or v["n"] < 1):
        _fail("G5", f"{cond_desc}: 整数グリッドの n が不正: {v['n']}")
    if "m" in v and (not isinstance(v["m"], int) or v["m"] < 1):
        _fail("G5", f"{cond_desc}: 整数グリッドの m が不正: {v['m']}")
    for sub in ("lo", "hi", "th"):
        if sub in v:
            _check_value(v[sub], lane, f"{cond_desc}/{sub}", legacy_used)


def _check_cond(c: dict, lane: str, where: str, legacy_used: list, in_nest=False):
    """条件1つ＝役割・形・材料・側・値（設計書 §2）の検査。"""
    form = c.get("form")
    if form not in FORMS:
        _fail("G6", f"{where}: 対応表に無い形: {form}")
    if form in NEST_FORMS:
        if in_nest:
            _fail("G5", f"{where}: 入れ子は1段まで（{form} の中に入れ子形）")
        inner = c.get("inner")
        if not _is_cond(inner):
            _fail("G5", f"{where}: {form} の内側の条件が無い")
        if inner.get("form") in NEST_FORMS:
            _fail("G5", f"{where}: {form} の内側は単純形のみ（設計書 §2.2）")
        n = (c.get("value") or {}).get("n")
        if n == 1:
            _fail("G5", f"{where}: {form}(N=1) は素の条件と同値＝生成禁止（正規形・CP3 提案7）")
        _check_value(c.get("value", {}), lane, f"{where}/{form}", legacy_used)
        _check_cond(inner, lane, f"{where}/{form}の内側", legacy_used, in_nest=True)
        return
    if form in ("level", "diff", "slope", "slope_avg") and c.get("side") not in SIDES:
        _fail("G5", f"{where}: 形 {form} に side（{'/'.join(SIDES)}）が無い")
    if form == "cross" and (c.get("value") or {}).get("direction") not in ("up", "down"):
        _fail("G5", f"{where}: cross に向き（up/down）が無い")
    if form in ("band", "band_exclude"):
        vv = c.get("value") or {}
        if "lo" not in vv or "hi" not in vv:
            _fail("G5", f"{where}: 形 {form} は value.lo と value.hi（下限・上限）が要る（§2.2）")
    if form == "slope" and not isinstance((c.get("value") or {}).get("n"), int):
        _fail("G5", f"{where}: 形 slope は value.n（遡る本数＝整数グリッド）が要る（§2.2）")
    if form == "slope_avg":
        vv = c.get("value") or {}
        if not isinstance(vv.get("n"), int) or not isinstance(vv.get("m"), int):
            _fail("G5", f"{where}: 形 slope_avg は value.n（遡る本数）と value.m（平均の本数）が要る（§2.2）")
    mats = c.get("material") or []
    need2 = form in ("cross", "diff", "touch")
    if need2 and len(mats) != 2:
        _fail("G6", f"{where}: 形 {form} は列2本の材料が要る（{len(mats)}本）")
    if form == "candle_dir":
        mats = []                                 # ローソク列＝バーそのもの（材料指定なし）
    elif not need2 and len(mats) != 1:
        _fail("G6", f"{where}: 形 {form} は列1本の材料（{len(mats)}本）")
    for m in mats:
        kind, name = _material_name(m, lane)
        if kind == "geo" and iref.RANGE_GEO_REF[name]["kind"] != "ratio":
            _fail("G6", f"{where}: 価格水準のレンジ幾何列 {name} は条件の材料に使えない"
                        f"（placement の幾何参照専用・H6）")
        if kind == "state" and not where.startswith("exit"):
            _fail("G6", f"{where}: ポジション状態列 {name} は出口 fire の材料専用（入口では建玉が無い）")
    _check_value(c.get("value", {}), lane, where, legacy_used)


def validate_recipe(recipe: dict, limits: dict | None = None, samples: dict | None = None) -> dict:
    """スキーマ検証器＝G1〜G6。壊れたレシピは RecipeError（読み込み拒否）。
    limits＝まこさん判断の値（n_min/k_max/depth_max/p_max/r_min/role_max/count_range）。
    未確定（None）は『値待ち』として報告し、構造の検査だけ行う（§11＝値はまこさんが決める）。
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
    p_max = lm.get("p_max")
    if p_max is None:
        rep["値待ち"].append("P_MAX（経路数の上限・§11-8）")
    elif len(paths) > p_max:
        _fail("G1", f"発火経路が {len(paths)} 本 > P_MAX={p_max}")
    all_conds = []
    for pi, path in enumerate(paths):
        conds, depths = _walk(path)
        all_conds += conds
        if et == "ceiling_resting":
            if conds:
                _fail("G5", "ceiling_resting の entry は条件の木を持たない（発火は天井の幾何＝engine 側・歩6-1）")
            continue
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
    cr = lm.get("count_range")
    if cr is None:
        rep["値待ち"].append("条件の合計本数の範囲（§11-4）")
    elif not (cr[0] <= len(all_conds) <= cr[1]):
        _fail("G5", f"条件の合計本数 {len(all_conds)} が範囲 {cr} の外")
    role_max = lm.get("role_max")
    if role_max is None:
        rep["値待ち"].append("E_MAX/S_MAX/L_MAX（役割ごとの本数上限・§11-3）")
    else:
        from collections import Counter
        rc = Counter(c["role"] for c in all_conds)
        for r, mx in role_max.items():
            if rc.get(r, 0) > mx:
                _fail("G5", f"役割 {r} が {rc[r]} 本 > 上限 {mx}")
    dmax = lm.get("depth_max")
    depth = _tree_depth(tree)
    if dmax is None:
        rep["値待ち"].append("木の深さ上限（§11-7）")
    elif depth > dmax:
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
        fams = {_material_family(m) for m in (c.get("material") or [])}
        kinds = {iref.FAMILY_LINEAGE[f]["k"] for f in fams if f in iref.FAMILY_LINEAGE}
        for kind in kinds:
            key = (c.get("role"), kind)
            if key in seen_role_kind and c.get("role") != "trigger":
                _fail("G3", f"同一系統 {kind} を同一役割 {c.get('role')} に2本（1本まで）")
            seen_role_kind.add(key)
            kind_count[kind] += 1
    k_max = lm.get("k_max")
    if k_max is None:
        rep["値待ち"].append("K_MAX（同系統のレシピ全体での上限・§11-5）")
    else:
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


def _vnum_q(v: dict, qkey: str, qtable: dict | None) -> float:
    """値の解決（分位対応・歩4）。threshold_q は解決表（値決め窓の分布から探索開始時に1回固定・§2.4-①・
    §5-4）でしか実値にならない＝表に無ければ止まる（fail-closed・rolling 解決の混入経路を持たない）。"""
    if "threshold_q" in v:
        q = v["threshold_q"]
        if qtable is None or qkey not in qtable or q not in qtable[qkey]:
            raise RecipeError(f"[実行器] 分位 {q} の解決表に {qkey} が無い"
                              f"（解決表＝探索開始時に1回固定・§5-4・生成器が作って渡す）")
        return float(qtable[qkey][q]) * float(v.get("mult", 1.0))
    return _vnum(v)


def _col_array(df: pd.DataFrame, m: dict, geo: dict, lane: str) -> np.ndarray:
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
        if run_col is None or run_col not in df.columns:
            raise RecipeError(f"[実行器] 材料列 {name} が実行データに無い"
                              f"（生成器の材料組み立て（build_features 接続）でも別名でも見つからない）")
        return df[run_col].to_numpy(float)
    raise RecipeError(f"[実行器] 入口の材料に使えない種別: {kind}（{name}）")


def _mat_key(m: dict, lane: str) -> str:
    """分位の解決表の鍵＝材料の解決名（列名）。"""
    return _material_name(m, lane)[1]


def _eval_cond(c: dict, df: pd.DataFrame, geo: dict, lane: str, qtable: dict | None = None) -> np.ndarray:
    """条件1つ → 各バーの真偽（状態評価）。na=fail が既定（欠損は不成立）。"""
    form = c["form"]
    v = c.get("value", {})
    na_pass = (v.get("na") == "pass")
    if form in NEST_FORMS:
        inner = _eval_cond(c["inner"], df, geo, lane, qtable)
        n = int(v["n"])
        off = int(v.get("offset", 0))
        s = pd.Series(inner.astype(float))
        if form == "streak":
            out = (s.rolling(n).sum() >= n).to_numpy()
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
    mats = c.get("material") or []
    a = _col_array(df, mats[0], geo, lane)
    akey = _mat_key(mats[0], lane)
    if form == "level":
        th = _vnum_q(v, akey, qtable)
        ok = _side_cmp(a, th, c.get("side"))
        res = np.where(np.isfinite(a), ok, na_pass)
        return res.astype(bool)
    if form in ("band", "band_exclude"):
        lo = _vnum_q(v["lo"], akey, qtable)
        hi = _vnum_q(v["hi"], akey, qtable)
        if lo > hi:
            lo, hi = hi, lo                       # 分位の取り違えで帯が裏返っても空帯にしない（正規化）
        inside = (a >= lo) & (a <= hi)
        ok = inside if form == "band" else ~inside
        return np.where(np.isfinite(a), ok, na_pass).astype(bool)
    if form == "slope":
        n = int(v["n"])
        d = a - np.roll(a, n)
        d[:n] = np.nan
        th = _vnum_q(v["th"], f"Δ{n}:{akey}", qtable) if "th" in v else 0.0
        ok = (d >= th) if c.get("side") == "above" else (d <= th)
        return np.where(np.isfinite(d), ok, na_pass).astype(bool)
    if form == "slope_avg":
        n, m_ = int(v["n"]), int(v["m"])
        ma = pd.Series(a).rolling(m_).mean().to_numpy()
        d = ma - np.roll(ma, n)
        d[:n + m_] = np.nan
        th = _vnum_q(v["th"], f"Δ{n}:MA{m_}:{akey}", qtable) if "th" in v else 0.0
        ok = (d >= th) if c.get("side") == "above" else (d <= th)
        return np.where(np.isfinite(d), ok, na_pass).astype(bool)
    b = _col_array(df, mats[1], geo, lane) if len(mats) > 1 else None
    if form == "cross":
        pa, pb = np.roll(a, 1), np.roll(b, 1)
        pa[0] = pb[0] = np.nan
        fin = np.isfinite(a) & np.isfinite(b)
        if v.get("direction") == "down":
            out = fin & (pa >= pb) & (a < b)
        else:
            out = fin & (pa <= pb) & (a > b)
        return out.astype(bool)
    if form == "diff":
        d = a - b
        th = _vnum_q(v, f"{akey}−{_mat_key(mats[1], lane)}", qtable)
        ok = (d >= th) if c.get("side") == "above" else (d <= th)
        return np.where(np.isfinite(d), ok, na_pass).astype(bool)
    if form == "touch":
        tol = _vnum(v)                            # 許容幅＝名前つき定数（§2.2・分位は使わない）
        d = np.abs(a - b)
        return np.where(np.isfinite(d), d <= tol * np.abs(b), na_pass).astype(bool)
    raise RecipeError(f"[実行器] 形 {form} の実行が未実装")


def _entry_fire(recipe: dict, df: pd.DataFrame, geo: dict, qtable: dict | None = None) -> np.ndarray:
    """エントリー発火＝経路の木が当バーで真 ∧ その経路の引き金が当バーで縁（設計書 §2.1・確定意味論）。"""
    lane = recipe["meta"].get("lane", "")
    tree = recipe["entry"]["connective"]
    paths = tree["any"] if (isinstance(tree, dict) and set(tree) == {"any"}) else [tree]
    pre = np.ones(len(df), bool)
    for c in recipe.get("pre_filter", []):
        pre &= _eval_cond(c, df, geo, lane, qtable)
    fire = np.zeros(len(df), bool)

    def _eval_tree(node) -> np.ndarray:
        if _is_cond(node):
            return _eval_cond(node, df, geo, lane, qtable)
        if "all" in node:
            out = np.ones(len(df), bool)
            for ch in node["all"]:
                out &= _eval_tree(ch)
            return out
        if "any" in node:
            out = np.zeros(len(df), bool)
            for ch in node["any"]:
                out |= _eval_tree(ch)
            return out
        cond_if = _eval_tree(node["if"])          # if-then＝if が真のときだけ then を要求
        cond_th = _eval_tree(node["then"])
        return ~cond_if | cond_th

    for path in paths:
        conds, _d = _walk(path)
        trig = next(c for c in conds if c.get("role") == "trigger")
        t_true = _eval_cond(trig, df, geo, lane, qtable)
        edge = t_true & ~np.roll(t_true, 1)       # 縁＝前バー不成立→今バー成立（cross は形が縁を内包）
        edge[0] = False
        fire |= _eval_tree(path) & edge & pre
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
    ok = df["range_ok_rg5"].to_numpy(bool)
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


def _collect_fire_cols(recipe: dict, df: pd.DataFrame, geo: dict, lane: str) -> dict:
    """出口 fire が使う材料列を、ループの前に1回だけ解決して配列にする（歩6-1 里程標7）。
    ★毎バー解決すると列の作り直しが走って遅い＝ここで1回だけ作る。値そのものは変えない。"""
    out: dict[str, np.ndarray] = {}
    for b in recipe.get("exits") or []:
        fire = b.get("fire")
        if fire is None:
            continue
        conds, _d = _walk(fire)
        for c in conds:
            for m in (c.get("material") or []):
                if "state" in m:
                    continue                      # ポジション状態列は毎バー計算（配列にできない）
                key = _material_name(m, lane)[1]
                if key not in out:
                    out[key] = _col_array(df, m, geo, lane)
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
            m = (node.get("material") or [{}])[0]
            nm = m.get("state")
            if nm is not None:
                val = state[nm]
            else:                                  # 指標の列（歩6-1 里程標7 で拡張・先に配列にしてある）
                key = _material_name(m, lane)[1]
                if fire_cols is None or key not in fire_cols:
                    raise RecipeError(f"[実行器] 出口 fire の材料列が解決されていない: {key}")
                val = float(fire_cols[key][i])
                if not np.isfinite(val):           # 欠損は不成立（入口の条件と同じ既定・na=pass で反転）
                    return bool((node.get("value") or {}).get("na") == "pass")
            th = _vnum(node.get("value", {}))
            return bool(_side_cmp(val, th, node.get("side")))
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
    ok = df["range_ok_rg5"].to_numpy(bool)
    up = df["rg5_uptrend"].to_numpy(bool)
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
    fire_cols = _collect_fire_cols(recipe, df, geo, lane)   # 出口 fire の指標列（ループ前に1回だけ解決）
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


def _ordering_sentinel() -> bool:
    """番人＝枝順（exits の並び）が結果を変えることを、競合バーを必ず含む合成データで機械確認する。
    実データの窓では TIME と SL が同じバーで競合するとは限らない（短窓で実測＝競合ゼロだと差が出ない）
    ため、番人は運任せにしない＝バー17で『保有30分の TIME 発火』と『SL 触り』を同時に起こす。
    [TIME,SL] の順＝建値フロア待機へ → 後で BE_EXIT ／ [SL,TIME] の順＝その場で SL_FILLED ＝ md5 が変わる。"""
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
    df = pd.DataFrame({"ts": idx, "open": o, "high": h, "low": l, "close": c, "volume": 1.0,
                       "atr": 1.0, "adx": 20.0, "stoch_k": k, "e38_stoch_d": d,
                       "rsi9": 50.0, "dev_z": 0.0,
                       "range_ok_rg5": True, "rg5_uptrend": False,
                       "v11_res_hi": 110.0, "v11_res_lo": 109.0, "v11_sup_hi": 91.0,
                       "v11_sup_lo": 90.0, "v11_mid": 100.0,
                       "e38_htf_roc24_2h": 0.0, "e38_vol_volr20_15m": 2.0})
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
        out = _l1_attach_legacy_cols(out, float(source_logic(recipe)["params"]["gap_pct"]))
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


def _l1_attach_legacy_cols(dfp: pd.DataFrame, gap_pct: float) -> pd.DataFrame:
    """L1 恒等用の legacy 材料列（run_long_support 1594-1595 / 1636 行と同式・当該バーのみ＝H2）。"""
    ok = dfp["range_ok_rg5"].to_numpy(bool)
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


# ══ 自己検査（番人＝わざと壊したレシピ18種で全部止まる・正しい2種は通る・設計書 §10＋歩4 拡張）══
def _base_ok_recipe() -> dict:
    """検証だけ通す最小の正しいレシピ（V9 風多条件・探索レーン＝legacy なし）。"""
    return {
        "meta": {"strategy": "e38", "logic_id": "T1", "side": "SHORT", "regime": "range_rg5"},
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
    # ★戦略と審判の maker/taker の一覧が一致しているか（2026-08-02 里程標9 で新設・まこさん指示「修正する」）。
    #   e37_scalp の _MAKER_EXIT は「score.py MAKER_EXIT_REASONS と完全同期」と自分で宣言している。
    #   ところが TREND_CAUGHT_TP が score.py にだけ在り、e37 に無い状態が 2026-07-16 から続いていた
    #   （売買記録CSVの net_usd/fee_usd だけが成行として計算され実際より悲観的に出ていた）。
    #   宣言は機械で守られていなかった＝ここで一致を検査する。ずれたら止まる。
    _only_e37 = sorted(set(e37._MAKER_EXIT) - set(_score.MAKER_EXIT_REASONS))
    _only_judge = sorted(set(_score.MAKER_EXIT_REASONS) - set(e37._MAKER_EXIT))
    if _only_e37 or _only_judge:
        ng.append(f"戦略と審判の maker 一覧がずれている: e37 だけに在る {_only_e37} / "
                  f"score.py だけに在る {_only_judge}（e37_scalp の宣言は『score.py と完全同期』）")
    # 系統マップ: FAMILY_TEMPLATES の全 family が割当済み（G3 の前提）
    miss = iref.lineage_coverage(list(FAMILY_TEMPLATES))
    if miss:
        ng.append(f"FAMILY_TEMPLATES の family が系統マップに無い: {miss}")
    print("=" * 80)
    print("engine_tuner_exec 自己検査（スキーマ検証器の番人＝壊したレシピ32種で全部止まる・正しい4種は通る・歩4/歩6-1 拡張の既知答え込み）")
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


if __name__ == "__main__":
    raise SystemExit(main())
