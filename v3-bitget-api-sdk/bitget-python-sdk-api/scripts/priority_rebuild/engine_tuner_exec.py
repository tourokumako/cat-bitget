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
EXEC_METHODS = ("maker", "taker", "post_only", "stop")          # 歩3 で実行できる方式
EXEC_REGISTERED_ONLY = ("iceberg", "twap", "vwap")              # 登録済みだが実行不能＝拒否側（CP3 Q1）
# 出口理由は score.py の maker/taker 登録と一致していること（H13・acceptance_checklist D）
REASONS_MAKER = set(e37._MAKER_EXIT)
REASONS_TAKER = {"TIME_EXIT", "FORCE_CLOSE_EOD", "RANGE_BREAK_EXIT", "TREND_CONT"}

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
    if form in ("level", "diff", "slope", "slope_avg") and c.get("side") not in ("above", "below"):
        _fail("G5", f"{where}: 形 {form} に side（above/below）が無い")
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
        if uc is not None and uc.get("reason") not in REASONS_TAKER:
            _fail("G6", f"uptrend_cut.reason が taker 登録に無い: {uc.get('reason')}（H13）")
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
    elif kind == "shrink":
        # v13 deadline shrink（歩6-1・S1 の書き写し）＝from 枝の水準から建値フロアへ残り時間比で縮む maker TP。
        if lv.get("from") is None:
            _fail("G6", f"{where}: shrink.from（縮み始めの枝名・例 TP2）が無い")
        for key in ("tmax", "floor"):
            if key not in lv:
                _fail("G5", f"{where}: shrink.{key} が無い（tmax＝縮み切るまでの本数／floor＝建値フロアの床）")
            _check_value(lv[key], lane, f"{where}/{key}", legacy_used)
    else:
        _fail("G6", f"{where}: level.kind が zone/zone_sl/mix/pct/shrink でない: {kind}")


# ══ ② 実行器（共通の売買ループ・設計書 §1〜§7 の意味論）══════════════════════════════
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
        ok = (a >= th) if c.get("side") == "above" else (a <= th)
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


def _resolve_levels(exits: list, i: int, lim: float, side: str, geo: dict, lane: str) -> dict:
    """resting 枝の価格水準をシグナルバー i で解決（設計書 §6・エントリー時に指値を置く）。"""
    sgn = -1.0 if side == "SHORT" else 1.0        # profit 側の符号（SHORT は下が利益）
    lv_out: dict[str, float] = {}
    mixes = []
    for b in exits:
        pl = (b.get("exec") or {}).get("placement") or {}
        if pl.get("kind") != "resting":
            continue
        lv = pl["level"]
        if lv["kind"] == "shrink":
            continue                              # 縮む TP＝毎バーの水準（歩6-1）＝ここでは解決しない（ループ側で計算）
        if lv["kind"] == "zone":
            if lv["target"] == "mid":
                px = geo["mid"][i]
            else:                                 # opp＝反対側ゾーン手前×バッファ（v18 と同じ幾何）
                buf = _vnum(lv.get("buf", {"const": "V11_SL_BUF"}))
                px = geo["sup_hi"][i] * (1 + buf) if side == "SHORT" else geo["res_lo"][i] * (1 - buf)
                if lv.get("fallback") == "mid":   # v18 幾何防御＝非有限/中央超えは中央へ（e37_scalp 1524-1530行と同式）
                    _mid = geo["mid"][i]
                    if not (np.isfinite(px) and (px < _mid if side == "SHORT" else px > _mid)):
                        px = _mid
        elif lv["kind"] == "zone_sl":
            k = _vnum(lv["k"])
            if lv.get("w", "range") == "zone":    # 同じ側の帯幅（L1＝sup_hi−sup_lo・run_long_support 1634行と同式）
                w = max((geo["res_hi"][i] - geo["res_lo"][i]) if side == "SHORT"
                        else (geo["sup_hi"][i] - geo["sup_lo"][i]), 1e-9)
            elif lv.get("w") == "inner":          # 帯の内側の隙間（S1＝res_lo−sup_hi・e37_scalp 1513/1549行と同式・下駄なし）
                w = geo["res_lo"][i] - geo["sup_hi"][i]
            else:                                 # range＝レンジ全幅（S2 恒等と同じ既定）
                w = max(geo["res_hi"][i] - geo["sup_lo"][i], 1e-9)   # 実装と同じ下駄（幅0の防御・S2 恒等）
            px = geo["res_hi"][i] + k * w if side == "SHORT" else geo["sup_lo"][i] - k * w
        elif lv["kind"] == "pct":
            base = lim                            # entry 基準（avg 基準は arm 時に解決＝be_wait）
            kv = _vnum(lv["k"])
            if lv["k"].get("side_sign") == "profit":
                kv = abs(kv) * sgn
            px = base * (1 + kv)
        elif lv["kind"] == "mix":
            mixes.append((b["name"], lv))
            continue
        else:
            raise RecipeError(f"[実行器] level.kind 未実装: {lv['kind']}")
        lv_out[b["name"]] = float(px)
    for name, lv in mixes:                        # mix は他の枝の水準に依存＝後で解決
        if isinstance(lv.get("to_level"), dict):  # to_level＝枝でなく水準そのもの（S1 の TP1＝mid 基準・歩6-1）
            tl = lv["to_level"]
            if tl.get("kind") == "zone" and tl.get("target") == "mid":
                to = float(geo["mid"][i])
            else:
                raise RecipeError(f"[実行器] mix.to_level は zone/mid のみ: {tl}")
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


def _exit_fire_ok(b: dict, lot: dict, i: int, df: pd.DataFrame, geo: dict, lane: str) -> bool:
    """出口 fire（材料＝ポジション状態列・on_close 評価）。scope（adds・hold_min）もここで見る。"""
    sc = b.get("scope")
    hold_min = (i - lot["first_idx"]) * 5
    if sc:
        lo, hi = sc.get("adds", [1, 10**9])
        if not (lo <= lot["add_count"] <= hi):
            return False
        if "hold_min" in sc:
            lo2, hi2 = sc["hold_min"]
            if not (lo2 <= hold_min <= (10**9 if hi2 is None else hi2)):
                return False
    fire = b.get("fire")
    if fire is None:
        return True
    state = {"hold_min": hold_min, "add_count": lot["add_count"],
             "peak_age_bars": i - lot.get("peak_idx", lot["first_idx"])}
    sgn = -1.0 if lot["side"] == "SHORT" else 1.0
    avg = lot["avg"]
    state["mfe_pct"] = (lot["max_fav"] - avg) / avg * 100.0 * sgn
    state["mae_pct"] = (lot["max_adv"] - avg) / avg * 100.0 * sgn
    c = float(df["close"].iloc[i])
    state["unreal_pct"] = (c - avg) / avg * 100.0 * sgn
    state["dist_be_pct"] = abs(c - avg) / avg * 100.0

    def _ev(node) -> bool:
        if _is_cond(node):
            m = (node.get("material") or [{}])[0]
            nm = m.get("state")
            if nm is None:
                raise RecipeError("[実行器] 出口 fire の材料はポジション状態列（歩4 でカタログ列に拡張）")
            val = state[nm]
            th = _vnum(node.get("value", {}))
            return val >= th if node.get("side") == "above" else val <= th
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
    pex = recipe.get("position_exits") or {}
    uc = pex.get("uptrend_cut")
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
            if uc is not None:                     # 歩6-1: uptrend 畳み＝保有全 lot を成行で確定（e37_scalp 1096-1145行の v20 経路）
                for lot in lots:                   # mfe/mae は更新前＝e37 と同じ（1096行は 1177行の更新より前）
                    e37._record(trades, lot, c[i], uc["reason"], i, ts)
                lots = []
                brk_cnt, brk_vol = 0, False
                continue                           # e37 1144-1145行＝uptrend バーは以降の処理へ進まない
        if pre_mfe:                                # e37_scalp 1177-1181行＝mfe/mae は枝の前に全 lot 一括更新
            for lot in lots:
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
                if side == "LONG":
                    lot["max_fav"] = max(lot["max_fav"], h[i])
                    lot["max_adv"] = min(lot["max_adv"], l[i])
                else:
                    lot["max_fav"] = min(lot["max_fav"], l[i])
                    lot["max_adv"] = max(lot["max_adv"], h[i])
            closed = False
            if lot["be_dl"] >= 0:                  # 建値フロア待機（v31 型＝SL→BE→期限の順・§8 行11）
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
                    if _hit and _exit_fire_ok(b, lot, i, df, geo, lane):
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
                    if not (hit and _exit_fire_ok(b, lot, i, df, geo, lane)):
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
                if not _exit_fire_ok(b, lot, i, df, geo, lane):
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
    dfl = _l1_attach_legacy_cols(dfp, gp)
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
            "sl_far": _vnum(bx["SL"]["exec"]["placement"]["level"]["k"]),
            "tmax": tmax_sh, "break_bars": int(_vnum(rbx["bars"])), "vol_n": int(_vnum(rbx["vol_n"])),
            "max_lots": int(recipe["position"]["max_adds"])}


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
    for nm, want, got in checks:
        okc = (want == got)
        print(f"[恒等検収 S1] 値の照合 {nm}: 正本={want} / レシピ側={got} → {'✅' if okc else '❌'}")
        ng += 0 if okc else 1
    (dfp,) = tuner.load_windows_cached(ad, [(s, e)], tuner.WARM, use_cache=not quick)
    # 里程標3 の材料列＝run_e37 2393-2394行／2436行と同じ関数を呼ぶ（式のドリフト防止＝出典を e37 に固定）。
    # 両側（現行 run_continuous_v11 とレシピ実行器）に同じ df を渡す＝材料の食い違いを物理的に作らない。
    if _cl.get("flat_up_top") == "range_high" or _cl.get("climb_guard"):
        dfp = dfp.copy()
        if _cl.get("flat_up_top") == "range_high":
            dfp["v35_range_top"] = e37._v35_range_top(dfp)      # v35＝今のレンジ開始以降の実測高値×(1−tol)
        if _cl.get("climb_guard"):
            dfp = e37.v22_uptrend_warning(dfp)                  # v37＝uptrend 前兆フラグ（確定15分足のみ＝H2）
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
    print(f"[恒等検収 S1] 載せたレバー: {' / '.join(_lv)}（レシピが正本＝現行側の引数はレシピから機械導出）")
    box_tf = ad.config()["global"]["box_tf"]
    up_arr = dfp["rg5_uptrend"].to_numpy(bool)
    t_ref = e37.run_continuous_v11(dfp, box_tf, v12_open_range=True, v13_time_maker=True,
                                   v20_uptrend=up_arr, short_lots=prm["max_lots"], v15_params=v15p)
    for r in t_ref:
        r["logic"] = recipe["meta"]["logic_id"]
    h_ref, n_ref = _md5_trades(t_ref, s, e)
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
    # 系統マップ: FAMILY_TEMPLATES の全 family が割当済み（G3 の前提）
    miss = iref.lineage_coverage(list(FAMILY_TEMPLATES))
    if miss:
        ng.append(f"FAMILY_TEMPLATES の family が系統マップに無い: {miss}")
    print("=" * 80)
    print("engine_tuner_exec 自己検査（スキーマ検証器の番人＝壊したレシピ25種で全部止まる・正しい4種は通る・歩4/歩6-1 拡張の既知答え込み）")
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
