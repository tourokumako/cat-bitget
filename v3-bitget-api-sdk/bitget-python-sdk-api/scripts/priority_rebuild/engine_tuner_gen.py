#!/usr/bin/env python3
"""engine_tuner_gen.py — 歩4 生成器（2段サンプリング＝構造をランダムに撒く→有望構造の値を TPE で詰める）

fix_map 歩4 の定義（まこさん承認済みの計画）:
  ・第1段＝構造（役割構成・本数・つなぎ方・形・材料）をランダムに撒く＝DSR の分散推定の土台を兼ねる
    （CP1 提案4(c)・監査 4-16／4-21 の実装＝分散・p値・PBO は第1段のサンプルだけから作る）。
  ・第2段＝有望構造の値を TPE で詰める。第2段の結果は統計判定に使わない（値の微調整だけ・CP1 解A）。
  ・段の最後に BH 法の偽発見率の検定（CP1 提案4(e)・監査 4-20）。
  ・CP1 の層化の門（候補1本1本を ATR% 帯の非悪化で弾く選別の門・監査 4-22）もこの段構成に入れる。
  ・落とした試行の機械出力は現行の形を踏襲（黙って消さない・L-330／L-356）。
  ・途中で止まった探索を続きから再開できる仕組み（R12）＝journal に済んだ試行を記録し再利用する。
  ・分位 threshold_q の解決表（値決め窓・探索開始時に1回固定・設計書 §5-4）の実装もここ。

守る制約:
  H2＝材料は当該バーまでの確定値のみ（材料の組み立ては observe_diag build_features を再利用＝コピー禁止）。
  H8＝窓は periods.py（本走時）。H13＝net は score.py（judge）だけが出す＝本ファイルは net を計算しない。
  L-267＝採点窓は使わない。値の水準（設計書 §11）は recipes/search_limits.json＝全部まこさん待ち（null）。
  null の間は本走を始められない（fail-closed）。selftest だけが「検収専用」の値を使う（採否・本走に不使用）。

採点はしない・売買記録CSVは書かない・score.py の採点窓は呼ばない。
自己検査: python3 engine_tuner_gen.py --selftest（合成データのみ・実データの試行ゼロ）
構造だけの試し撒き: python3 engine_tuner_gen.py --dry-run N（データ不要・内訳の機械出力だけ）
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import pathlib
import sys
import tempfile
from collections import Counter

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import engine_tuner_exec as ex               # noqa: E402  歩3 実行器（検証器・共通売買ループ）
import indicator_reference_diag as iref      # noqa: E402  材料・系統・定数レジストリの正本

HERE = pathlib.Path(__file__).resolve().parent
LIMITS_PATH = HERE / "recipes" / "search_limits.json"
RUNS_DIR = HERE.parents[2] / "results" / "priority_rebuild" / "tuner_gen"

# 生成器が組み立てに使う形（実行器 FORMS の全11種＝歩4 で band 系の実行も実装済み）
TRIGGER_FORMS = ("cross", "level", "diff", "candle_dir", "slope", "streak", "within_n")
STATE_FORMS = ("level", "band", "band_exclude", "slope", "slope_avg", "diff", "touch",
               "candle_dir", "streak", "within_n")
NEEDS_PAIR = ("cross", "diff", "touch")

# §11 の対応（値待ちの可視化に使う・番号は設計書 §11）
LIMIT_LABELS = {
    "n_min": "N_MIN（補正後独立標本数の下限・§11-1）",
    "r_min": "R_MIN（リスクリワード比の下限・§11-2）",
    "role_max": "E_MAX/S_MAX/L_MAX（役割ごとの本数上限・§11-3）",
    "count_range": "条件の合計本数の範囲（§11-4）",
    "k_max": "K_MAX（同系統のレシピ全体での上限・§11-5）",
    "quantile_grid": "分位の格子（§11-6）",
    "depth_max": "木の深さ上限（§11-7）",
    "p_max": "P_MAX（発火経路数の上限・§11-8）",
    "state_mult_grid": "状態列の定数倍数 k の格子（§11-9）",
    "int_grid": "整数グリッド＝lookback・N（§11-10）",
    "hold_range_by_role": "保有時間の上限の範囲（役割ごと・5分足の本数・監査 4-19／要件 R6）",
    "hour_grid": "整数グリッド＝時刻の閾値（§11-10）",
    "frac_grid": "段階決済 mix の比率の格子（§11-10 に準ずる）",
    "exit_mult_grid": "SL 幾何 k の倍率の格子（§11-10 に準ずる）",
    "max_adds_grid": "max_adds の格子（§11-10 に準ずる）",
    "fdr_q": "BH 法の偽発見率の水準 q（歩4 新設・まこさんが決める）",
}


def load_limits(path: pathlib.Path | None = None) -> tuple[dict, list[str]]:
    """limits を読み、値待ち（null）の一覧を返す。値待ちが1つでもあれば本走は始められない。"""
    p = path or LIMITS_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    lm = {k: v for k, v in raw.items() if not k.startswith("_")}
    waiting = [LIMIT_LABELS.get(k, k) for k, v in lm.items() if v is None]
    return lm, waiting


class HoldRangeError(SystemExit):
    """保有時間の上限の範囲が決まっていない＝走らせない（fail-closed）。"""


def resolve_hold_range(limits: dict, strategy: str) -> dict:
    """戦略の役割から、保有時間の上限の範囲を決めて limits に入れて返す（監査 4-19／要件 R6）。

    なぜ役割から決めるか
      保有時間の上限は、その戦略の役割で変わります。
      scalp は短く小刻みに売買します。daytrade は1つの玉を長く伸ばします。
      それまでは、どの戦略でも同じ候補（30分・60分・120分・240分の4つ）を使っていました。

    どうやって役割を知るか
      tuner_judgement.role_of が、台帳ファイル adopted_strategies.md を開きます。
      そのファイルの ROLE_CHECK という行の中から、戦略の名前を探します。
      その右側に書いてある文字（scalp か daytrade）を読み取ります。

    範囲の単位
      5分足の本数です。1本＝5分です。12本＝60分です。120本＝600分です。
      設定ファイル recipes/search_limits.json の hold_range_by_role に書いてあります。

    止める場合（fail-closed）
      ①役割が台帳に書かれていないとき ②その役割の範囲が設定ファイルに無いか空のとき。
      黙って別の役割の範囲を使うことはしません。
    """
    import tuner_judgement as tj
    role = tj.role_of(strategy)
    if not role:
        raise HoldRangeError(
            f"[保有時間の範囲エラー] 戦略 {strategy} の役割が採用台帳に書かれていません。"
            f"\n  台帳＝{tj.ADOPTED}\n  その中の ROLE_CHECK の行に「{strategy}=scalp」のように足してください。")
    table = limits.get("hold_range_by_role") or {}
    rng_decl = table.get(role)
    if not rng_decl or rng_decl.get("lo_bars") is None or rng_decl.get("hi_bars") is None:
        raise HoldRangeError(
            f"[保有時間の範囲エラー] 役割 {role} の保有時間の上限の範囲が決まっていません。"
            f"\n  設定ファイル＝{LIMITS_PATH}\n  その中の hold_range_by_role.{role} に lo_bars と hi_bars を書いてください"
            f"（単位＝5分足の本数・値はまこさんが決める）。")
    lo, hi = int(rng_decl["lo_bars"]), int(rng_decl["hi_bars"])
    if lo < 1 or hi < lo:
        raise HoldRangeError(
            f"[保有時間の範囲エラー] 役割 {role} の範囲が不正です: lo_bars={lo} / hi_bars={hi}"
            f"（1本以上で、上限が下限以上であること）")
    out = dict(limits)
    out["hold_bars"] = (lo, hi)
    out["hold_role"] = role
    return out


def hold_bars(limits: dict) -> tuple[int, int]:
    """解決済みの保有時間の上限の範囲（5分足の本数）を読み出す。未解決なら止める。"""
    hb = limits.get("hold_bars")
    if not hb:
        raise HoldRangeError(
            "[保有時間の範囲エラー] 保有時間の上限の範囲が解決されていません。"
            "\n  先に resolve_hold_range(limits, 戦略の名前) を呼んでください（役割から範囲を決める処理）。")
    return int(hb[0]), int(hb[1])


# ══ 材料の候補プール ═══════════════════════════════════════════════════════════════════
def material_pool(cfg: dict | None = None) -> tuple[list[dict], list[str], int]:
    """カタログから (family, param) の候補と時間足を機械で数える。戻り＝(プール, 足, カタログ総列数)。

    候補に載るのは実行器 FAMILY_TEMPLATES で名前を組み立てられる family だけ（複合パラメータ family は
    歩4 時点でも生成不可＝G6 と同じ線）。カタログ総列数は網羅度の分母。
    """
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import observe_diag as od
        cfg = cfg or od.load_config()
        names = [name for name, _fn, _d in od.build_catalog(cfg)]
    import re
    pool = []
    for fam, tpl in ex.FAMILY_TEMPLATES.items():
        pat = re.compile("^" + re.escape(tpl).replace(re.escape("{p}"), r"(\d+)") + "$")
        for nm in names:
            m = pat.match(nm)
            if m:
                pool.append({"family": fam, "param": int(m.group(1))})
    tfs = list(cfg["timeframes"])
    return pool, tfs, len(names) * len(tfs)


# ══ 構造のランダムサンプリング（第1段）═══════════════════════════════════════════════════
class SampleError(Exception):
    """この乱数の引きでは条件を組めなかった（引き直す・黙って弱い構造に逃げない）。"""


def _lineage_of(m: dict) -> str:
    if "geo" in m:
        return "構造・位置"
    if "time" in m:
        return "時間帯"
    return iref.FAMILY_LINEAGE[m["family"]]["k"]


def _kubun_of(m: dict) -> str:
    """材料の方向の区分（順張り値／状態量／ボラ量／反転サイン）＝カタログの「方向」の欄から機械で引く。"""
    if "geo" in m:
        return iref.RANGE_GEO_REF[m["geo"]]["houkou"].split("＝")[0]
    if "time" in m:
        return iref.TIME_REF[m["time"]]["houkou"].split("＝")[0]
    name = ex.FAMILY_TEMPLATES[m["family"]].format(p=m.get("param"))
    ref, _ = iref.find(name)
    return ref["houkou"].split("＝")[0] if ref else "？"


# ══ 型の表（signal_families）＝D1 の閉じ込めの正本（2026-08-07 まこさん承認・指紋つき）════════
_SIGNAL_TABLE: dict | None = None


def load_signal_table() -> dict:
    """承認済みの型の表を読み、閉じ込めに使う形へ直す。未承認・指紋不一致なら止まる（fail-closed）。"""
    global _SIGNAL_TABLE
    if _SIGNAL_TABLE is not None:
        return _SIGNAL_TABLE
    import gen_signal_families as gsf
    ok, msg = gsf._table_status()
    if not ok:
        raise SystemExit(f"[型の表] {msg}＝構造を生成できない（fail-closed・D1）")
    t = json.loads(gsf.OUT_JSON.read_text(encoding="utf-8"))
    rl = t["role_lineage"]
    roles = {}
    for rname, r in rl["roles"].items():
        roles[rname] = {"lineages": set(r["lineages"]),
                        "tfs": None if r["tfs"] == "all" else set(r["tfs"]),   # None＝表の全足
                        "geo": bool(r.get("geo"))}
    _SIGNAL_TABLE = {
        "parts": set(t["parts"]),
        "tfs": list(t["timeframes"]),
        "banned": {(p["part"], p["tf"]) for p in t["bans"]["insufficient_samples"]["pairs"]},
        "geo_ok": list((t.get("extra_parts") or {}).get("geo", {}).get("parts") or []),
        "time_ok": list((t.get("extra_parts") or {}).get("time", {}).get("parts") or []),
        "roles": roles,
        "families": list(rl["applies_to"]),
        "quantile_grid_hi": ("q70", "q80", "q90"),   # DC2 の高分位（表の DC2 の逐語＝q70・q80・q90）
        "quantile_grid_lo": ("q10", "q20", "q30"),   # DC2 の低分位（同＝q10・q20・q30）
        "quantile_hi": ("q70", "q80", "q90"),        # 出口の確認条件で使う別名（同じ値）
        "quantile_lo": ("q10", "q20", "q30"),
    }
    return _SIGNAL_TABLE


def _role_tfs(tfs, table, role) -> list[str]:
    """役割に使える時間足＝呼び出し側の足 ∩ 表の足 ∩ 対応表の役割の足（D1・表が正本）。"""
    rr = table["roles"][role]
    out = [t for t in tfs if t in table["tfs"] and (rr["tfs"] is None or t in rr["tfs"])]
    if not out:
        raise SampleError(f"役割 {role} に使える時間足が無い")
    return out


def _banned_pair(m: dict, table) -> bool:
    """（部品×時間足）が禁止3（標本不足）に当たるか。"""
    if "family" not in m:
        return False
    name = ex.FAMILY_TEMPLATES[m["family"]].format(p=m["param"])
    return (name, m["tf"]) in table["banned"]


def _pick_material(rng, pool, tfs, limits, role, seen_rolekind, kind_count, table) -> dict:
    """材料1本＝G3（同系統×同役割は1本・K_MAX）＋型の表（対応表の系統×時間足・禁止3・許可 geo/time）を
    サンプリング時から守る（D1・2026-08-07 まこさん承認の表が正本）。"""
    rr = table["roles"][role]
    tf_pool = _role_tfs(tfs, table, role)
    for _ in range(60):
        r = rng.random()
        if role == "location" and rr["geo"] and table["geo_ok"] and r < 0.5:
            m = {"geo": str(rng.choice(table["geo_ok"]))}
        elif role == "env" and "時間帯" in rr["lineages"] and r < 0.10 and limits.get("hour_grid"):
            m = {"time": "時刻"}                  # 曜日の閾値格子は未定義＝時刻だけ（格子はまこさん §11-10）。表は両方許可
        else:
            base = pool[int(rng.integers(len(pool)))]
            m = {"family": base["family"], "param": base["param"], "tf": str(rng.choice(tf_pool))}
            if _banned_pair(m, table):
                continue                                        # 禁止3（標本不足）＝引き直す
        kind = _lineage_of(m)
        if kind not in rr["lineages"]:
            continue                                            # 対応表＝役割に使えない系統
        if role != "trigger" and (role, kind) in seen_rolekind:
            continue
        if limits.get("k_max") is not None and kind_count.get(kind, 0) >= limits["k_max"]:
            continue
        return m
    raise SampleError(f"役割 {role} の材料を60回引いても表と G3 を満たせない")


def _pair_materials(rng, pool, tfs, role, table) -> list[dict]:
    """列2本の形（cross/diff/touch）＝同 family の期間違い、または Stoch%K と %D の対。
    D1＝対応表の系統×時間足・禁止3 を守る。"""
    rr = table["roles"][role]
    tf_pool = _role_tfs(tfs, table, role)
    fams = {}
    for b in pool:
        if iref.FAMILY_LINEAGE[b["family"]]["k"] in rr["lineages"]:
            fams.setdefault(b["family"], []).append(b["param"])
    for _ in range(30):
        tf = str(rng.choice(tf_pool))
        if rng.random() < 0.4:
            ks = sorted(set(fams.get("Stoch%K", [])) & set(fams.get("Stoch%D", [])))
            if ks:
                p = int(rng.choice(ks))
                pair = [{"family": "Stoch%K", "param": p, "tf": tf},
                        {"family": "Stoch%D", "param": p, "tf": tf}]
                if not any(_banned_pair(m, table) for m in pair):
                    return pair
        cands = [f for f, ps in fams.items() if len(set(ps)) >= 2]
        if not cands:
            raise SampleError(f"役割 {role} で列2本の形を組める family が無い（表の系統の中）")
        f = str(rng.choice(cands))
        p1, p2 = rng.choice(sorted(set(fams[f])), size=2, replace=False)
        pair = [{"family": f, "param": int(p1), "tf": tf}, {"family": f, "param": int(p2), "tf": tf}]
        if not any(_banned_pair(m, table) for m in pair):
            return pair
    raise SampleError(f"役割 {role} の列2本を30回引いても禁止3 を避けられない")


def _q(rng, limits) -> dict:
    return {"threshold_q": str(rng.choice(limits["quantile_grid"]))}


def _dc1_side(rng, role, mats, side) -> str:
    """DC1（表の向きの決まり・2026-08-07 まこさん承認）＝順張り値の部品を side 付きの形で
    環境認識・十分性に使うとき、SHORT は below だけ・LONG は above だけ。それ以外は乱数。"""
    if role in ("env", "sufficiency") and any(_kubun_of(m) == "順張り値" for m in mats):
        return "below" if side == "SHORT" else "above"
    return str(rng.choice(["above", "below"]))


def _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side, allow_nest=True) -> dict:
    forms = TRIGGER_FORMS if role == "trigger" else STATE_FORMS
    rr = table["roles"][role]
    forms = tuple(f for f in forms if f != "candle_dir" or "ローソク" in rr["lineages"])
    form = str(rng.choice(forms))
    if form in ("streak", "within_n"):
        if not allow_nest:
            form = "level"
        else:
            inner = _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side,
                               allow_nest=False)
            inner.pop("role", None)
            inner["role"] = role
            n = int(rng.choice([n for n in limits["int_grid"] if n >= 2]))
            return {"role": role, "form": form, "inner": inner,
                    "value": {"n": n, "offset": int(rng.choice([0, 1]))}}
    if form in NEEDS_PAIR:
        mats = _pair_materials(rng, pool, tfs, role, table)
        for m in mats:
            kind_count[_lineage_of(m)] = kind_count.get(_lineage_of(m), 0) + 0  # 数えは下で一括
        if form == "cross":
            # DC3（表の向きの決まり）＝cross の direction は side と揃える（up＝LONG・down＝SHORT）
            return {"role": role, "form": "cross", "material": mats,
                    "value": {"direction": "down" if side == "SHORT" else "up"}}
        if form == "diff":
            return {"role": role, "form": "diff", "material": mats,
                    "side": _dc1_side(rng, role, mats, side), "value": _q(rng, limits)}
        return {"role": role, "form": "touch", "material": mats, "value": {"const": "TOL_SR"}}
    if form == "candle_dir":
        # DC4（表の向きの決まり）＝反転サイン・ローソクは SHORT＝bear だけ・LONG＝bull だけ
        return {"role": role, "form": "candle_dir",
                "value": {"dir": "bear" if side == "SHORT" else "bull"}}
    m = _pick_material(rng, pool, tfs, limits, role, seen_rolekind, kind_count, table)
    if "time" in m:
        return {"role": role, "form": "level", "material": [m],
                "side": str(rng.choice(["above", "below"])),
                "value": {"n": int(rng.choice(limits["hour_grid"]))}}
    if form == "level":
        if role == "trigger" and _lineage_of(m) == "オシレーター":
            # DC2（表の向きの決まり）＝レンジ系の引き金のオシレーターは行き過ぎを逆に取る
            #   SHORT＝above かつ 高分位（q70/q80/q90）・LONG＝below かつ 低分位（q10/q20/q30）
            grid = table["quantile_grid_hi"] if side == "SHORT" else table["quantile_grid_lo"]
            qs = [q for q in limits["quantile_grid"] if q in grid]
            if not qs:
                raise SampleError("DC2 の分位が格子に無い")
            return {"role": role, "form": "level", "material": [m],
                    "side": "above" if side == "SHORT" else "below",
                    "value": {"threshold_q": str(rng.choice(qs))}}
        return {"role": role, "form": "level", "material": [m],
                "side": _dc1_side(rng, role, [m], side), "value": _q(rng, limits)}
    if form in ("band", "band_exclude"):
        qs = rng.choice(limits["quantile_grid"], size=2, replace=False)
        lo, hi = sorted(qs, key=lambda s: int(str(s).lstrip("q")))
        return {"role": role, "form": form, "material": [m],
                "value": {"lo": {"threshold_q": str(lo)}, "hi": {"threshold_q": str(hi)}}}
    if form == "slope":
        return {"role": role, "form": "slope", "material": [m],
                "side": _dc1_side(rng, role, [m], side),
                "value": {"n": int(rng.choice(limits["int_grid"]))}}
    if form == "slope_avg":
        return {"role": role, "form": "slope_avg", "material": [m],
                "side": _dc1_side(rng, role, [m], side),
                "value": {"n": int(rng.choice(limits["int_grid"])), "m": int(rng.choice(limits["int_grid"]))}}
    raise SampleError(f"形 {form} の値の組み立てが未定義")


def _const100(x: float) -> dict:
    """欲しい実値 x を名前つき定数 FULL_100 × mult で表す（生の数字のフィールドを作らない・§2.4-②）。"""
    base = float(iref.CONST_REGISTRY["FULL_100"]["value"])
    return {"const": "FULL_100", "mult": float(x) / base}


# ══ 出口の表（exit_families）＝D2 の枝の組み立ての正本（2026-08-07 まこさん承認・指紋つき）════
_EXIT_TABLE: dict | None = None


def load_exit_table() -> dict:
    """承認済みの出口の表を読む。未承認・指紋不一致なら止まる（fail-closed・D2）。

    表は gen_exit_families.py が軸カタログ entry_exit_matrix.md の X-a〜X-k から全自動生成する。
    ここで読むのは「どの枝の型を作ってよいか」の一覧＝表に無い枝は組み立てない。
    """
    global _EXIT_TABLE
    if _EXIT_TABLE is not None:
        return _EXIT_TABLE
    import gen_exit_families as gef
    ok, msg = gef.table_status()
    if not ok:
        raise SystemExit(f"[出口の表] {msg}＝出口の枝を生成できない（fail-closed・D2）")
    _EXIT_TABLE = json.loads(gef.OUT_JSON.read_text(encoding="utf-8"))
    return _EXIT_TABLE


def _floor_pct(k: float) -> dict:
    """手数料床（SCALP_FLOOR＝比率 0.0008）の k 倍を、％の値として表す。

    玉の状態の列（mfe_prev_pct・unreal_pct）は％の単位で持たれている（実行器 1051行）。
    SCALP_FLOOR は比率なので、100 を掛けて％にそろえる。生の数字のフィールドは作らない（§2.4）。
    """
    return {"const": "SCALP_FLOOR", "mult": 100.0 * float(k)}


# 出口の水準の条件に使える名前つき定数（部品 → 上側・下側）。定数レジストリ iref.CONST_REGISTRY が正本＝
# ここは対応づけだけ。実行器が出口の発火条件で分位を解けないため、水準は定数でしか表せない（上の注記）。
_EXIT_LEVEL_CONST = {
    "RSI": ("RSI_OB", "RSI_OS"),
    "Stoch%K": ("STOCH_OB", "STOCH_OS"),
    "Stoch%D": ("STOCH_OB", "STOCH_OS"),
    "ADX": ("ADX_TREND", "ADX_TREND"),
}


def _state_cond(state: str, side: str, value: dict) -> dict:
    """出口の発火条件1本＝玉の状態の列を見る形。役割は env で固定（実行器は出口の fire で役割を見ない）。"""
    return {"role": "env", "form": "level", "side": side, "material": [{"state": state}], "value": value}


def _pick_exit_material(rng, pool, tfs, table, lineages: set) -> dict:
    """出口の確認条件の材料＝入口の型の表の部品から、決められた系統の中で1本 引く。

    禁止3（標本不足の部品×時間足）は入口と同じように避ける。表の外は引かない（D1 と同じ閉じ込め）。
    """
    cand = [b for b in pool if iref.FAMILY_LINEAGE[b["family"]]["k"] in lineages]
    if not cand:
        raise SampleError(f"出口の材料に使える部品が無い（系統 {sorted(lineages)}）")
    tf_pool = [t for t in tfs if t in table["tfs"]]
    for _ in range(40):
        b = cand[int(rng.integers(len(cand)))]
        m = {"family": b["family"], "param": b["param"], "tf": str(rng.choice(tf_pool))}
        if not _banned_pair(m, table):
            return m
    raise SampleError("出口の材料を40回 引いても禁止3 を避けられない")


def _exit_indicator_cond(rng, limits, pool, tfs, table, side, spec) -> dict:
    """出口の確認条件＝指標を見る形1本。向きの決め方は表の規則から機械で決まる。

    表の規則に reverse_of_side が在る枝＝入口と逆の向きを見る（例＝SHORT の玉は、下げ止まり側で降りる）。
    無い枝＝広がる側・強い側を見る（例＝レンジが壊れたことを見る BREAKOUT）。
    """
    lineages = set(spec.get("lineage_any") or ([spec["lineage"]] if spec.get("lineage") else
                                               ["オシレーター", "トレンド", "ボラ", "ローソク", "出来高", "構造・位置"]))
    forms = [f for f in (spec.get("forms") or ["level"]) if f in ("level", "cross", "slope", "diff", "candle_dir")]
    rev = bool(spec.get("reverse_of_side"))
    form = str(rng.choice(forms))
    # ★ローソクの部品は「値のある列」ではない（実行器の FAMILY_TEMPLATES に無い＝材料として引けない）。
    #   だから系統がローソクだけの枝は、材料の要らない形（陽線か陰線か）で作る。
    if "ローソク" in lineages and not any(iref.FAMILY_LINEAGE[b["family"]]["k"] in lineages for b in pool):
        form = "candle_dir"
    if form == "candle_dir":
        # 出口のローソク＝入口の逆（SHORT の玉は陽線の形で降りる・DC4 の逆）
        return {"role": "env", "form": "candle_dir",
                "value": {"dir": ("bull" if side == "SHORT" else "bear") if rev else
                                 ("bear" if side == "SHORT" else "bull")}}
    if form == "cross" and "ローソク" not in lineages:
        # 2本の線の交差＝入口の逆向き（DC3 の逆）
        fams = {}
        for b in pool:
            if iref.FAMILY_LINEAGE[b["family"]]["k"] in lineages:
                fams.setdefault(b["family"], []).append(b["param"])
        ks = sorted(set(fams.get("Stoch%K", [])) & set(fams.get("Stoch%D", [])))
        tf_pool = [t for t in tfs if t in table["tfs"]]
        if ks:
            p = int(rng.choice(ks))
            tf = str(rng.choice(tf_pool))
            pair = [{"family": "Stoch%K", "param": p, "tf": tf}, {"family": "Stoch%D", "param": p, "tf": tf}]
            if not any(_banned_pair(m, table) for m in pair):
                return {"role": "env", "form": "cross", "material": pair,
                        "value": {"direction": ("up" if side == "SHORT" else "down") if rev
                                  else ("down" if side == "SHORT" else "up")}}
        form = "level"
    m = _pick_exit_material(rng, pool, tfs, table, lineages)
    if form == "slope":
        return {"role": "env", "form": "slope", "material": [m],
                "side": ("above" if side == "SHORT" else "below") if rev else str(rng.choice(["above", "below"])),
                "value": {"n": int(rng.choice(limits["int_grid"]))}}
    # ── 水準を見る形（level）──
    # ★実行器は出口の発火条件で分位（threshold_q）を解けない（_exit_fire_ok が解決表を受け取らない・
    #   1073行の _vnum）。だから出口の水準は、名前つき定数レジストリに登録済みの値だけで表す。
    #   使えるのは、その定数が意味を持つ部品（RSI・ストキャス・ADX）に限る。
    #   ほかの部品は水準では見ない＝交差・傾き・ローソクの形で見る（値の要らない形）。
    hi_lo = _EXIT_LEVEL_CONST.get(m["family"])
    if hi_lo is None:
        return {"role": "env", "form": "slope", "material": [m],
                "side": ("above" if side == "SHORT" else "below") if rev else str(rng.choice(["above", "below"])),
                "value": {"n": int(rng.choice(limits["int_grid"]))}}
    hi, lo = hi_lo
    if rev:                       # 反転を見る＝SHORT の玉は下がり切った側（買われ過ぎの逆）で降りる
        sd, cst = ("below", lo) if side == "SHORT" else ("above", hi)
    else:                         # 壊れたことを見る＝SHORT の玉は上に振れた側
        sd, cst = ("above", hi) if side == "SHORT" else ("below", lo)
    return {"role": "env", "form": "level", "material": [m], "side": sd, "value": {"const": cst}}


def _make_exits(rng, limits, pool=None, tfs=None, table=None, side="SHORT", max_adds=1) -> list[dict]:
    """出口の枝＝承認済みの出口の表（exit_families）の枝の型から組み立てる（D2・2026-08-07）。

    ★2026-08-07 まで＝作れる枝は4つ（損切り・利確・時間切れ・確率で部分利確）だけで、中身も固定だった。
      玉がどう動いたかで枝が切り替わる形（状態機械）を1つも作れなかった＝欠陥 D2。
    ★これから＝表に載っている枝の型20種から組み立てる。どの枝を入れるか・並び順は乱数（要件 R13＝
      枝の有無と順番が探索の対象）。枝の中身（決済の名前・置き場所・発火の条件の形）は表が決める＝
      乱数で条件をつなぐ形にはならない。

    必ず入る枝＝利確1本（名前 TP2）・時間切れ（TIME）・損切り（SL）または資金防衛（FINSTOP）。
    実行器の G4＝損切り系の枝か、1トレード最大許容損失の枝（risk=loss_cap）のどちらかが要る。
    """
    et = load_exit_table()
    bt = et["branch_types"]
    sig = table or load_signal_table()
    pool = pool if pool is not None else []
    tfs = tfs if tfs is not None else sig["tfs"]

    def need(bid: str) -> dict:
        if bid not in bt:
            raise SampleError(f"出口の表に枝の型 {bid} が無い＝組み立てられない（表が正本）")
        return bt[bid]

    def mk(bid: str, name: str, **kw) -> dict:
        """表の枝の型から、実行器が読む形の枝を1本 作る。決済の名前と執行は表のとおり。"""
        b = need(bid)
        method = "maker" if b["exec_method"].startswith("maker") else "taker"
        out = {"name": name, "reason": b["reason"], "size_ratio": kw.pop("size_ratio", 1.0),
               "exec": {"method": method, "placement": kw.pop("placement")}}
        for k, v in kw.items():
            if v is not None:
                out[k] = v
        return out

    tmax_min = int(rng.integers(hold_bars(limits)[0], hold_bars(limits)[1] + 1)) * 5
    hf = limits["hold_frac_grid"]

    def hold_gate() -> dict:
        """満期に対する割合で保有の門を作る（分・5の倍数に丸める・最低5分）。"""
        n = int(round(tmax_min * float(rng.choice(hf)) / 5.0)) * 5
        return {"n": max(5, n)}

    exits: list[dict] = []

    # ── ① 利確（名前は TP2 で固定＝部分利確と縮む枝がこの名前を参照する）──
    tp_id = str(rng.choice(["TP_ZONE_MID", "TP_ZONE_OPP", "TP_PCT", "TP_SWING"]))
    if tp_id == "TP_ZONE_MID":
        lv = {"kind": "zone", "target": "mid"}
    elif tp_id == "TP_ZONE_OPP":
        lv = {"kind": "zone", "target": "opp", "fallback": "mid",
              "buf": _floor_pct(float(rng.choice(limits["state_mult_grid"])) / 100.0)}
    elif tp_id == "TP_PCT":
        lv = {"kind": "pct", "base": "entry",
              "k": {"const": "SCALP_FLOOR", "mult": float(rng.choice(limits["state_mult_grid"]))}}
    else:
        lv = {"kind": "swing", "target": "low" if side == "SHORT" else "high",
              "m": {"n": int(rng.choice(limits["int_grid"]))},
              "buf": {"const": "SCALP_FLOOR", "mult": float(rng.choice(limits["state_mult_grid"]))},
              "fallback": {"kind": "zone", "target": "mid"}}
    exits.append(mk(tp_id, "TP2", placement={"kind": "resting", "fill": "profit", "level": lv}))

    # ── ② 損切り（3種から1つ）／確率で「損切り無し＋資金防衛」（軸 X-d4）──
    no_sl = rng.random() < 0.15
    if not no_sl:
        sl_id = str(rng.choice(["SL_ZONE", "SL_PCT", "SL_SWING"]))
        if sl_id == "SL_ZONE":
            lv = {"kind": "zone_sl", "w": str(rng.choice(["range", "zone", "inner"])),
                  "k": _const100(float(rng.choice(limits["exit_mult_grid"])) / 100.0)}
        elif sl_id == "SL_PCT":
            lv = {"kind": "pct", "base": "entry",
                  "k": {"const": "SCALP_FLOOR", "mult": float(rng.choice(limits["exit_mult_grid"])) / 10.0}}
        else:
            lv = {"kind": "swing", "target": "high" if side == "SHORT" else "low",
                  "m": {"n": int(rng.choice(limits["int_grid"]))},
                  "buf": {"const": "SCALP_FLOOR", "mult": float(rng.choice(limits["state_mult_grid"]))},
                  "fallback": {"kind": "zone_sl", "w": "range", "k": _const100(1.0)}}
        exits.append(mk(sl_id, "SL", placement={"kind": "resting", "fill": "adverse",
                                                "pessimistic": True, "level": lv}))

    # ── ③ 資金防衛（1トレードの最大許容損失・損切り無しの案では必ず入れる）──
    if no_sl or rng.random() < 0.30:
        cap = float(rng.choice(limits["loss_cap_grid"]))
        exits.append(mk("FINSTOP", "FINSTOP", placement={"kind": "on_close"}, risk="loss_cap",
                        fire={"all": [_state_cond("unreal_pct", "below",
                                                  {"const": "SCALP_FLOOR", "mult": -100.0 * cap / 0.08})]}))

    # ── ④ 時間切れ（必ず入る）──
    time_br = mk("TIME", "TIME", placement={"kind": "on_close"},
                 fire={"all": [_state_cond("hold_min", "above", {"n": tmax_min})]})
    if rng.random() < 0.3:
        time_br["exec"]["be_wait"] = {"level": {"kind": "pct", "base": "avg",
                                                "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}},
                                      "ttl": {"const": "BE_TTL_BARS"}}
    exits.append(time_br)

    # ── ⑤ 玉の動きで切り替わる枝（ここが D2 の本体）──
    if rng.random() < 0.40:       # 含み損の玉だけ満期を前倒しする（V9 の down_factor）
        exits.append(mk("TIME_DOWN", "TIMEDOWN", placement={"kind": "on_close"},
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("unreal_pct", "below", {"const": "NEUTRAL_0"})]}))
    if rng.random() < 0.40:       # 含み益のピークから戻したら、利益を残す位置に指値
        exits.append(mk("PEAKLOCK", "PEAKLOCK",
                        placement={"kind": "resting", "fill": "adverse", "pessimistic": True,
                                   "level": {"kind": "peak_giveback",
                                             "arm": _floor_pct(float(rng.choice(limits["state_mult_grid"]))),
                                             "giveback": {"n": max(1, int(round(float(rng.choice(limits["giveback_grid"])) * 100)))},
                                             "floor": {"const": "SCALP_FLOOR"}}}))
    if rng.random() < 0.30:       # 一度 利が乗った後、建値+手数料床で降りる
        exits.append(mk("BEEXIT", "BEEXIT",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "pct", "base": "avg",
                                             "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},
                        fire={"all": [_state_cond("mfe_prev_pct", "above",
                                                  _floor_pct(float(rng.choice(limits["state_mult_grid"]))))]}))
    if rng.random() < 0.30:       # 時間が経っても利が乗らない玉を、建値フロアで降りる（停滞・失速）
        exits.append(mk("BESTALE", "BESTALE",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "pct", "base": "avg",
                                             "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("mfe_prev_pct", "below",
                                                  _floor_pct(float(rng.choice(limits["state_mult_grid"]))))]}))
    if rng.random() < 0.30:       # 利確に届かないまま満期が近い玉を、手前の位置で確定する
        frac = float(rng.choice(limits["frac_grid"])) / 100.0
        exits.append(mk("MFEEXIT", "MFEEXIT",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "mix", "from": "entry", "to": "TP2",
                                             "frac": _const100(frac)}},
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("mfe_prev_pct", "above",
                                                  _floor_pct(float(rng.choice(limits["state_mult_grid"]))))]}))
    if pool and rng.random() < 0.30:    # 指標が反転したら、利益側に指値を置いて確定する
        try:
            c = _exit_indicator_cond(rng, limits, pool, tfs, sig, side, need("REVERSE_IND")["fire"][0])
            exits.append(mk("REVERSE_IND", "REVIND",
                            placement={"kind": "resting", "fill": "profit",
                                       "level": {"kind": "pct", "base": "avg",
                                                 "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},
                            fire={"all": [c, _state_cond("unreal_pct", "above", {"const": "NEUTRAL_0"})]}))
        except SampleError:
            pass
    # ★ローソクの形の反転（軸 X-g11）は組まない＝実行器が出口の発火条件で「材料の無い形」を
    #   評価できないことを実物で確認したため（2026-08-07・exit_families.md の X-g11 に理由を記録）。
    if pool and rng.random() < 0.30:    # レンジが壊れたら成行で降りる（前提崩れ）
        try:
            c = _exit_indicator_cond(rng, limits, pool, tfs, sig, side, need("BREAKOUT")["fire"][0])
            exits.append(mk("BREAKOUT", "BREAKOUT", placement={"kind": "on_close"}, fire={"all": [c]}))
        except SampleError:
            pass
    if max_adds >= 2 and rng.random() < 0.30:   # 積み増した玉だけに当たる損切り（枝が回数で切り替わる）
        lo = int(rng.choice([a for a in limits["max_adds_grid"] if 2 <= a <= max_adds] or [2]))
        exits.append(mk("MAECUT_ADDS", "MAECUTADDS", placement={"kind": "on_close"},
                        scope={"adds": [lo, None]},
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("unreal_pct", "below", {"const": "NEUTRAL_0"})]}))
    if rng.random() < 0.30:       # 残り時間の比で建値側へ縮む指値（時間切れの前に置き直す）
        exits.append(mk("SHRINK", "SHRINK",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "shrink", "from": "TP2",
                                             "tmax": {"n": max(1, tmax_min // 5)},
                                             "floor": {"const": "SCALP_FLOOR"}}}))

    # ── ⑥ 部分利確（段数は格子から・各段の量の合計が玉を超えない）──
    if rng.random() < 0.5:
        steps = int(rng.choice(limits["ladder_steps_grid"]))
        rest = 1.0
        for s in range(steps):
            frac = float(rng.choice(limits["frac_grid"])) / 100.0
            if frac >= rest:
                break
            exits.append(mk("TP1_LADDER", f"TP1{'' if s == 0 else s + 1}", size_ratio=frac, once=True,
                            placement={"kind": "resting", "fill": "profit",
                                       "level": {"kind": "mix", "from": "entry", "to": "TP2",
                                                 "frac": _const100(frac * (s + 1) / steps)}}))
            rest -= frac

    order = rng.permutation(len(exits))          # 並び順もデータ（上から先勝ち・要件 R13）
    return [exits[i] for i in order]


def default_regime() -> dict:
    """既定の相場の宣言＝接続ファイル e38 が設定ファイルから読んだもの（監査 4-19／要件 R5）。

    ★道具の中に列の名前を書かないため、接続ファイルに聞きます。
      列の名前を道具に書いてしまうと、レンジ以外の相場を指定できなくなります（それが 4-19 の指摘でした）。
    """
    from tuner_adapters import e38 as _e38
    return _e38.regime("S2")


def sample_structure(rng, limits, pool, tfs, side="SHORT", regime=None, logic_id="GEN") -> dict:
    """構造1本＝役割構成・本数・つなぎ方・形・材料・出口の枝・玉の持ち方 をランダムに組む。

    ★D1（2026-08-07 まこさん承認の型の表が正本）＝乱数は表の中だけで振る。
      ①型（シグナル家族）を表の対象（E-a1/4/5/8＝レンジ系）から1つ引く（行が無い型は生成不可）
      ②材料は対応表（役割×系統×時間足）・禁止3・許可 geo/time の中だけ
      ③向きは DC1〜DC4 の決まりで side と噛み合わせる
    """
    table = load_signal_table()
    pool = [b for b in pool
            if ex.FAMILY_TEMPLATES[b["family"]].format(p=b["param"]) in table["parts"]
            and b["family"] in iref.FAMILY_LINEAGE]
    if not pool:
        raise SampleError("表に載っている部品が pool に1つも無い")
    fam_label = str(rng.choice(table["families"]))       # ①型を1つ引く（4型は共通の対応表＝ラベルは記録用）
    lo, hi = limits["count_range"]
    n_total = int(rng.integers(lo, hi + 1))
    seen_rolekind: set = set()
    kind_count: dict = {}
    conds = []

    def _register(c):
        for m in (c.get("material") or []) + ([c["inner"]["material"][0]] if c.get("inner", {}).get("material") else []):
            kind = _lineage_of(m)
            key = (c["role"], kind)
            if c["role"] != "trigger" and key in seen_rolekind:
                raise SampleError("G3 重複")
            seen_rolekind.add(key)
            kind_count[kind] = kind_count.get(kind, 0) + 1
            if limits.get("k_max") is not None and kind_count[kind] > limits["k_max"]:
                raise SampleError("K_MAX 超過")

    trig = _make_cond(rng, "trigger", limits, pool, tfs, seen_rolekind, kind_count, table, side)
    _register(trig)
    conds.append(trig)
    budget = dict(limits["role_max"])
    for _ in range(n_total - 1):
        avail = [r for r, b in budget.items() if b > 0]
        if not avail:
            break
        role = str(rng.choice(sorted(avail)))
        for _try in range(20):
            try:
                c = _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side)
                _register(c)
                break
            except SampleError:
                continue
        else:
            raise SampleError(f"役割 {role} の条件を組めない")
        budget[role] -= 1
        conds.append(c)
    # つなぎ方＝flat all／if-then 入り（深さは limits.depth_max の内側）
    kids: list = list(conds)
    if len(conds) >= 3 and limits["depth_max"] >= 2 and rng.random() < 0.3:
        a = kids.pop(len(kids) - 1)
        b = kids.pop(len(kids) - 1)
        kids.append({"if": a, "then": b})
    tree = {"all": kids}
    pos_adds = int(rng.choice(limits["max_adds_grid"]))    # 先に決める＝出口の枝が回数で切り替わるため
    return {
        "meta": {"strategy": "e38", "logic_id": logic_id, "side": side,
                 "signal_family": fam_label,
                 "regime": dict(regime if regime is not None else default_regime())},
        "pre_filter": [],
        "entry": {"connective": tree},
        "exits": _make_exits(rng, limits, pool=pool, tfs=tfs, table=table, side=side,
                             max_adds=int(pos_adds)),
        "position": {"mode": str(rng.choice(["separate", "avg"])),
                     "max_adds": pos_adds,
                     **({"add_trigger": {"kind": "resignal"}}
                        if True else {})},
    }


def recipe_hash(recipe: dict) -> str:
    return hashlib.sha256(json.dumps(recipe, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


def write_kakikudashi(run_dir, structures: list[dict], results1: list[dict], kept: list[dict], seed) -> None:
    """人が読む書き下し＝最良1本＋機械が無作為に選んだ3本（D1 完了の線①・監査 G4 の材料・L-400 の4番）。
    画面と run_dir/kakikudashi.txt の両方に出す。条件の日本語化は fire_diag.cond_label（既存）を使う。"""
    import engine_tuner_fire_diag as fd
    lines: list[str] = []

    def _one(idx: int, title: str) -> None:
        st = structures[idx]
        lane = str(st.get("meta", {}).get("lane", ""))
        conds, _d = ex._walk(st["entry"]["connective"])
        rec = next((r for r in results1 if r["idx"] == idx), None)
        lines.append(f"■ {title} 構造#{idx}（型 {st['meta'].get('signal_family', '?')} ／ side {st['meta'].get('side')}）")
        if rec is not None:
            gate = "" if rec["ok"] else f" ／ 門で不合格（{rec['why']}）"
            lines.append(f"  値決め窓: net ${rec['total']:+,.0f} ／ {rec['n']}玉 ／ {rec['per_day']:.2f}件/日{gate}")
        for c in conds:
            lines.append(f"  ・{fd.cond_label(c, lane)}")
        exs = "、".join(f"{b['name']}({b['reason']})" for b in st.get("exits", []))
        pos = st.get("position", {})
        lines.append(f"  出口の枝: {exs} ／ 玉の持ち方: {pos.get('mode')}・積み増し上限 {pos.get('max_adds')}")
        lines.append("")

    if kept:
        best = max(kept, key=lambda z: z["total"])
        _one(int(best["idx"]), "最良（値決め窓）")
    else:
        lines.append("■ 最良: 通った構造が0本＝書けない（偽装の書き下しを出さない）")
        lines.append("")
    rng = np.random.default_rng([int(seed), 9999])
    picks = sorted(int(i) for i in rng.choice(len(structures), size=min(3, len(structures)), replace=False))
    for i in picks:
        _one(i, "無作為")
    text = "\n".join(lines)
    (pathlib.Path(run_dir) / "kakikudashi.txt").write_text(text, encoding="utf-8")
    print("\n[書き下し（最良1本＋機械が無作為に選んだ3本・kakikudashi.txt にも保存）]")
    print(text)


# ══ 構造の内訳（機械出力・R3 完了の線⑤）══════════════════════════════════════════════════
def structure_breakdown(recipes: list[dict], catalog_total: int) -> dict:
    forms, roles, counts, modes, nexits = Counter(), Counter(), Counter(), Counter(), Counter()
    touched: set = set()
    paths = Counter()
    for r in recipes:
        conds, _d = ex._walk(r["entry"]["connective"])
        counts[len(conds)] += 1
        tree = r["entry"]["connective"]
        paths[len(tree["any"]) if set(tree) == {"any"} else 1] += 1
        for c in conds:
            forms[c["form"]] += 1
            roles[c["role"]] += 1
            for m in (c.get("material") or []):
                if "family" in m:
                    kind, name = ex._material_name(m, r["meta"].get("lane", ""))
                    touched.add(name)
                elif "geo" in m:
                    touched.add(m["geo"])
        modes[r["position"]["mode"]] += 1
        nexits[len(r["exits"])] += 1
    return {"構造数": len(recipes), "条件本数の分布": dict(sorted(counts.items())),
            "形の分布": dict(forms.most_common()), "役割の分布": dict(roles.most_common()),
            "経路数の分布": dict(sorted(paths.items())), "玉の持ち方": dict(modes),
            "出口の枝数": dict(sorted(nexits.items())),
            "触れた列": len(touched),
            "網羅度%": round(len(touched) / catalog_total * 100.0, 2) if catalog_total else None}


# ══ 分位の解決表（値決め窓・探索開始時に1回固定・設計書 §5-4）═══════════════════════════════
def needed_qkeys(recipes: list[dict]) -> dict[str, tuple]:
    """レシピ群が使う分位の鍵 → 列の組（単列 or 差の2列）。"""
    keys: dict[str, tuple] = {}

    def _cond_keys(c, lane):
        v = c.get("value", {})
        mats = c.get("material") or []
        if c["form"] in ("streak", "within_n"):
            _cond_keys(c["inner"], lane)
            return
        if not mats:
            return
        a = ex._mat_key(mats[0], lane)
        if c["form"] == "level" and "threshold_q" in v:
            keys[a] = (a,)
        if c["form"] in ("band", "band_exclude"):
            for sub in ("lo", "hi"):
                if "threshold_q" in v.get(sub, {}):
                    keys[a] = (a,)
        if c["form"] == "diff" and "threshold_q" in v:
            b = ex._mat_key(mats[1], lane)
            keys[f"{a}−{b}"] = (a, b)

    for r in recipes:
        lane = r["meta"].get("lane", "")
        conds, _d = ex._walk(r["entry"]["connective"])
        # ★出口の枝の発火条件も歩く（D2・2026-08-07）。直す前は入口と事前の足切りしか見ておらず、
        #   出口に指標を見る条件（例＝レンジが壊れたことを見る枝）を入れると、分位の解決表に鍵が無くて止まった。
        for b in (r.get("exits") or []):
            if b.get("fire"):
                ec, _ed = ex._walk(b["fire"])
                conds += ec
        for c in conds + list(r.get("pre_filter", [])):
            _cond_keys(c, lane)
    return keys


def _geo_of(df: pd.DataFrame) -> dict:
    """レンジ幾何＝帯の4隅・中央と、そこから作る2列（帯内位置%・W%）。本走と番人で同じ作り方を使う。"""
    geo = {"res_hi": df["v11_res_hi"].to_numpy(float), "res_lo": df["v11_res_lo"].to_numpy(float),
           "sup_hi": df["v11_sup_hi"].to_numpy(float), "sup_lo": df["v11_sup_lo"].to_numpy(float),
           "mid": df["v11_mid"].to_numpy(float)}
    c = df["close"].to_numpy(float)
    span = geo["res_hi"] - geo["mid"]
    with np.errstate(invalid="ignore", divide="ignore"):
        geo["帯内位置%"] = np.where(np.isfinite(span) & (span > 0), (c - geo["mid"]) / span, np.nan)
        geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),
                             (geo["res_hi"] - geo["sup_lo"]) / c * 100.0, np.nan)
    return geo


def build_qtable(df: pd.DataFrame, geo: dict, recipes: list[dict], grid: list[str],
                 start=None, end=None) -> dict:
    """解決表＝値決め窓の分布から分位→実値を1回だけ固定（rolling しない・§2.4-①）。"""
    mask = np.ones(len(df), bool)
    if start is not None:
        ts = pd.to_datetime(df["ts"])
        mask = (ts >= start) & (ts < end)
    table: dict[str, dict] = {}
    for key, cols in needed_qkeys(recipes).items():
        def _arr(name):
            if name in geo:
                return np.asarray(geo[name], float)
            if name in df.columns:
                return df[name].to_numpy(float)
            # 別名（D4 の直し・2026-08-07）＝実行器 _col_array（686行）と同じ扱いにそろえる。
            # 直す前はここが別名を見ず、別名で持たれている7列のどれかに分位が当たると走行が丸ごと止まった。
            run_col = ex.RUNTIME_ALIAS.get(name)
            if run_col is not None and run_col in df.columns:
                return df[run_col].to_numpy(float)
            raise SystemExit(f"[解決表エラー] 列 {name} が実行データに無い（材料の組み立て漏れ）")
        s = _arr(cols[0]) if len(cols) == 1 else _arr(cols[0]) - _arr(cols[1])
        s = s[mask]
        s = s[np.isfinite(s)]
        if not len(s):
            raise SystemExit(f"[解決表エラー] {key} の有効標本がゼロ（窓とデータを確認）")
        table[key] = {q: float(np.quantile(s, int(q.lstrip("q")) / 100.0)) for q in grid}
    return table


# ══ 材料の組み立て（observe_diag build_features の再利用＝コピー禁止・H2）═══════════════════
def attach_materials(df: pd.DataFrame, recipes: list[dict]) -> pd.DataFrame:
    """レシピ群が使うカタログ列だけを組み立てて df に足す（全列は作らない＝時間とメモリの節約）。"""
    need: set[str] = set()
    for r in recipes:
        lane = r["meta"].get("lane", "")
        conds, _d = ex._walk(r["entry"]["connective"])
        # ★出口の枝の発火条件の材料も組み立てる（D2・2026-08-07）。needed_qkeys と同じ理由。
        for b in (r.get("exits") or []):
            if b.get("fire"):
                ec, _ed = ex._walk(b["fire"])
                conds += ec
        for c in conds + list(r.get("pre_filter", [])):
            stack = [c] + ([c["inner"]] if c.get("inner") else [])
            for cc in stack:
                for m in (cc.get("material") or []):
                    if "family" in m and "legacy_col" not in m:
                        kind, name = ex._material_name(m, lane)
                        if kind == "col" and name not in df.columns:
                            alias = ex.RUNTIME_ALIAS.get(name)
                            if alias is None or alias not in df.columns:
                                need.add(name)
    if not need:
        return df
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import observe_diag as od
        cfg = od.load_config()
    by_tf: dict[str, set] = {}
    for full in need:
        base, tf = full.rsplit("__", 1)
        by_tf.setdefault(tf, set()).add(base)
    bars = df.set_index(pd.to_datetime(df["ts"]))[["open", "high", "low", "close", "volume"]]
    out = df.copy()
    with contextlib.redirect_stdout(buf):
        cat_all = od.build_catalog(cfg)
        for tf, bases in by_tf.items():
            cfg_tf = dict(cfg)
            cfg_tf["timeframes"] = [tf]
            cat = [t for t in cat_all if t[0] in bases]
            feats, _meta = od.build_features(bars, cfg_tf, catalog=cat)
            for col in feats.columns:
                if col in need:
                    out[col] = feats[col].to_numpy(float)
    missing = [c for c in need if c not in out.columns]
    if missing:
        raise SystemExit(f"[材料エラー] 組み立てられなかった列: {missing}（黙って落とさない）")
    return out


# ══ BH 法（偽発見率の制御・CP1 提案4(e)・監査 4-20）══════════════════════════════════════
def pvalue_daily(x: np.ndarray) -> float:
    """日ごとの net の平均が 0 を超えるかの片側検定（正規近似）。統計判定は第1段のサンプル専用。"""
    x = np.asarray(x, float)
    T = len(x)
    if T < 2:
        return 1.0
    sd = float(x.std(ddof=1))
    if sd == 0:
        return 0.0 if float(x.mean()) > 0 else 1.0
    t = float(x.mean()) / (sd / math.sqrt(T))
    return 1.0 - 0.5 * (1.0 + math.erf(t / math.sqrt(2.0)))


def bh_select(pvals: list[float], q: float) -> list[bool]:
    """Benjamini–Hochberg＝小さい順に p_(i) ≤ q·i/m の最大 i まで採択。"""
    m = len(pvals)
    if m == 0:
        return []
    order = np.argsort(pvals)
    k = -1
    for rank, j in enumerate(order, start=1):
        if pvals[j] <= q * rank / m:
            k = rank
    sel = [False] * m
    if k > 0:
        for rank, j in enumerate(order, start=1):
            if rank <= k:
                sel[j] = True
    return sel


# ══ 層化の門（CP1・候補1本1本を ATR% 帯の非悪化で弾く・監査 4-22）═══════════════════════════
def strat_gate(base_t: pd.DataFrame | None, cand_t: pd.DataFrame, edges, judge) -> tuple[bool | None, str]:
    """土台がある時だけ判定（無ければ判定不能＝None・偽装の✅を出さない）。net は judge（審判）で出す。"""
    if base_t is None or edges is None:
        return None, "判定不能（土台なし or 帯の値がまこさん待ち）"
    def band_of(t):
        return t["atr_14"].astype(float) / t["entry_price"].astype(float) * 100.0
    lo = [-float("inf")] + list(edges)
    hi = list(edges) + [float("inf")]
    ngs = []
    for a, b in zip(lo, hi):
        vals = []
        for t in (base_t, cand_t):
            if t is None or not len(t):
                vals.append(0.0)
                continue
            m = (band_of(t) >= a) & (band_of(t) < b)
            sub = t[m].reset_index(drop=True)
            vals.append(float(judge.score(sub)["total"]) if len(sub) else 0.0)
        if vals[1] < vals[0]:
            ngs.append(f"{a:g}〜{b:g}")
    return (len(ngs) == 0), ("全帯で非悪化" if not ngs else f"悪化した帯 {', '.join(ngs)}")


# ══ journal（途中再開 R12）════════════════════════════════════════════════════════════════
class Journal:
    """済んだ試行の記録＝続きから再開する土台。meta が食い違う journal は使わない（fail-closed）。"""

    def __init__(self, path: pathlib.Path, meta: dict):
        self.path = path
        self.done: dict[str, dict] = {}
        self.meta = meta
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            if lines:
                head = json.loads(lines[0])
                if head.get("meta") != meta:
                    raise SystemExit("[R12 エラー] journal の meta（seed・窓・limits）が今回と食い違う"
                                     "＝別条件の続きには使えない（新しい run-id で走らせること）")
                for ln in lines[1:]:
                    rec = json.loads(ln)
                    self.done[rec["key"]] = rec
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps({"meta": meta}, ensure_ascii=False, sort_keys=True) + "\n",
                            encoding="utf-8")

    def get(self, key: str) -> dict | None:
        return self.done.get(key)

    def put(self, key: str, rec: dict) -> None:
        rec = {"key": key, **rec}
        self.done[key] = rec
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")


# ══ 試行の実行（1本＝実行器で売買 → 審判で net）══════════════════════════════════════════
def run_trial(df: pd.DataFrame, recipe: dict, qtable: dict, judge, start, end) -> dict:
    trades, rep = ex.run_recipe(df, recipe, qtable=qtable)
    t = pd.DataFrame(trades)
    if len(t):
        et = pd.to_datetime(t["entry_time"])
        t = t[(et >= start) & (et < end)].reset_index(drop=True)
    days = max((end - start).days, 1)
    if not len(t):
        return {"total": 0.0, "n": 0, "per_day": 0.0, "t": t, "rep": rep}
    res = judge.score(t)
    return {"total": float(res["total"]), "n": len(t), "per_day": len(t) / days, "t": t, "rep": rep}


def zero_trade_gate(res: dict) -> tuple[bool, str]:
    """売買ゼロ（0玉）の案は、件数/日 の下限（min_per_day）が空欄でも候補に残さない（D3 の一部・0c）。

    2026-08-07 まこさん OK＝「件数が 0件/日 の案を候補に残さない」は CC の判断でよい。
    下限の値そのもの（例＝5件/日）はまこさんが決める＝ここでは判定しない（0玉だけを捨てる）。
    背景＝売買ゼロの net は $0 で、負けた案（net マイナス）に勝つため「最良」に居座る（defects.md D3）。"""
    if res["n"] == 0:
        return False, "売買ゼロ（0玉）＝候補に残さない（D3・net $0 が負けた案に勝つのを防ぐ）"
    return True, ""


def per_day_gate(res: dict, min_per_day) -> tuple[bool, str]:
    """件数/日 の関門（D3 の残り・D6・まこさん OK 2026-08-07「OK」）。

    門は2つあります。第1段と第2段で同じ1本の処理として持ちます
    （書き分けると、片方だけ直して片方が古いまま残ります）。
      ① 売買ゼロ（0玉）の門＝下限が空欄でも捨てる（zero_trade_gate・0c・2026-08-07）
      ② 件数/日 の下限＝下限が入っているとき、それを下回る案を捨てる

    下限の値の正本＝e38_logics.json の logics[].params.search_min_per_day（11本とも 5.0）。
    5.0 の出どころ＝cat_requirements §8.6 の逐語「絶対下限＝件数/日 5」＋
    採用台帳 adopted_strategies.md の ROLE_FLOOR: scalp=5 と ROLE_CHECK: e38=scalp。
    ★下限が空欄（None）のときは ① だけが働きます。2026-08-07 まで、11本のうち9本がこの形でした
    （残り2本は CC が置いた 2.0 で、絶対下限 5.0 を下回るため走らせられませんでした）。
    """
    ok, why = zero_trade_gate(res)
    if ok and min_per_day is not None and res["per_day"] < min_per_day:
        return False, f"件数の下限 {min_per_day} に対して {res['per_day']:.2f}件/日"
    return ok, why


# ══ 第2段（TPE）用＝値スロットの列挙と適用 ═══════════════════════════════════════════════
def _cat(choices) -> dict:
    """候補の一覧から選ぶ値（メニュー方式）。"""
    return {"kind": "cat", "choices": list(choices)}


def _int_range(lo: int, hi: int, step: int = 1) -> dict:
    """下限から上限までの整数から選ぶ値（範囲方式・監査 4-19／要件 R6 で新設）。"""
    return {"kind": "int", "lo": int(lo), "hi": int(hi), "step": int(step)}


def suggest_slot(trial, name: str, spec: dict):
    """1つの値を Optuna に作らせる。メニュー方式と範囲方式の2つに対応する。

    ★範囲方式を足した理由（監査 4-19／要件 R6・2026-08-03）
      それまで、保有時間の上限はメニュー方式でした。あらかじめ並べた数字からしか選べません。
      たとえば一番稼げる上限が 75分でも、メニューに 75分が無ければ、何回試しても出ません。
      範囲方式では、下限と上限の間の整数を全部試せます。
    """
    if spec.get("kind") == "int":
        return trial.suggest_int(name, spec["lo"], spec["hi"], step=spec.get("step", 1))
    return trial.suggest_categorical(name, spec["choices"])


def value_slots(recipe: dict, limits: dict) -> list[tuple[str, dict]]:
    """レシピの中の『動かせる値』を (パス, 値の作り方) で列挙する。構造は動かさない（第2段の定義）。

    値の作り方は2つ。メニュー方式（候補の一覧から選ぶ）と 範囲方式（整数の範囲から選ぶ）。
    """
    slots: list[tuple[str, dict]] = []
    qg = limits["quantile_grid"]

    def _cond_slots(prefix, c):
        v = c.get("value", {})
        if c["form"] in ("streak", "within_n"):
            slots.append((f"{prefix}.value.n", _cat([n for n in limits["int_grid"] if n >= 2])))
            _cond_slots(f"{prefix}.inner", c["inner"])
            return
        if "threshold_q" in v:
            slots.append((f"{prefix}.value.threshold_q", _cat(qg)))
        for sub in ("lo", "hi"):
            if "threshold_q" in v.get(sub, {}):
                slots.append((f"{prefix}.value.{sub}.threshold_q", _cat(qg)))
        if c["form"] in ("slope", "slope_avg"):
            slots.append((f"{prefix}.value.n", _cat(limits["int_grid"])))
        if c["form"] == "slope_avg":
            slots.append((f"{prefix}.value.m", _cat(limits["int_grid"])))

    tree = recipe["entry"]["connective"]

    def _walk_tree(prefix, node):
        if ex._is_cond(node):
            _cond_slots(prefix, node)
            return
        if "all" in node or "any" in node:
            k = "all" if "all" in node else "any"
            for i, ch in enumerate(node[k]):
                _walk_tree(f"{prefix}.{k}[{i}]", ch)
            return
        _walk_tree(f"{prefix}.if", node["if"])
        _walk_tree(f"{prefix}.then", node["then"])

    _walk_tree("entry", tree)
    for bi, b in enumerate(recipe["exits"]):
        if b.get("fire"):
            conds, _d = ex._walk(b["fire"])
            for ci, c in enumerate(conds):
                mats = c.get("material") or []
                if mats and "state" in mats[0] and mats[0]["state"] == "hold_min":
                    # 監査 4-19／要件 R6＝保有時間の上限は範囲方式（単位は分・5分足なので刻みは5）
                    _lo, _hi = hold_bars(limits)
                    slots.append((f"exits[{bi}].fire[{ci}].value.n", _int_range(_lo * 5, _hi * 5, 5)))
    return slots


def apply_slots(recipe: dict, choices: dict[str, object]) -> dict:
    """スロットのパスに選んだ値を書き込んだレシピの複製を返す（構造は動かさない）。"""
    import re as _re
    r = copy.deepcopy(recipe)
    for path, val in choices.items():
        toks = path.split(".")
        cur: object = None
        i = 0
        while i < len(toks):
            tk = toks[i]
            m = _re.match(r"^([^\[\]]+)(?:\[(\d+)\])?$", tk)
            name, idx = m.group(1), m.group(2)
            last = (i == len(toks) - 1)
            if i == 0:
                if name == "entry":
                    cur = r["entry"]["connective"]
                elif name == "exits":
                    cur = r["exits"][int(idx)]
                else:
                    raise SystemExit(f"[歩4 エラー] スロットのパスの根が不明: {path}")
                i += 1
                continue
            if name == "fire":
                conds, _d = ex._walk(cur["fire"])          # _walk は参照を返す＝直接書ける
                cur = conds[int(idx)]
                i += 1
                continue
            if last:
                cur[name] = val
                break
            cur = cur[name] if idx is None else cur[name][int(idx)]
            i += 1
    return r


# ══ 本体＝2段サンプリング ═══════════════════════════════════════════════════════════════
def run_generation(df: pd.DataFrame, limits: dict, judge, start, end, *,
                   trials1: int, trials2: int, top_k: int, seed: int,
                   run_dir: pathlib.Path, pool, tfs, catalog_total: int,
                   side="SHORT", regime=None,
                   base_trades=None, atr_edges=None, min_per_day=None, net_floor=None,
                   purpose: str, tag: str = "",
                   df_confirm: pd.DataFrame | None = None, confirm_start=None, confirm_end=None,
                   base=None, rules: dict | None = None, rfloor: float | None = None) -> dict:
    """第1段＝構造をランダムに撒く（統計の土台）→ BH 法 → 第2段＝有望構造の値を TPE で詰める。"""
    meta = {"seed": seed, "trials1": trials1, "trials2": trials2, "top_k": top_k,
            "window": [str(start), str(end)], "side": side,
            "limits_hash": hashlib.sha256(json.dumps(limits, sort_keys=True, default=str).encode()).hexdigest()[:12],
            "tag": tag}
    jn = Journal(run_dir / "journal.jsonl", meta)
    print(f"[歩4 生成器] 窓 {start}〜{end} ／ 第1段 {trials1} 本（ランダム＝統計の土台）／ "
          f"第2段 {trials2} 本（TPE＝統計判定に不使用）／ journal {jn.path}")

    # ── 構造の撒き（決定論＝seed と番号だけから再現できる＝R12 の前提）──
    structures: list[dict] = []
    rejects = Counter()
    seen_hash: set = set()
    dup = 0
    i = 0
    draws = 0
    while len(structures) < trials1 and draws < trials1 * 50:
        draws += 1
        rng = np.random.default_rng([seed, 1, i])
        i += 1
        try:
            r = sample_structure(rng, limits, pool, tfs, side=side, regime=regime,
                                 logic_id=f"GEN{len(structures):04d}")
        except SampleError as e:
            rejects[f"サンプル不能: {e}"] += 1
            continue
        try:
            ex.validate_recipe(r, limits={
                "n_min": None,          # G2 は検査5 の補正後表と接続（本走時・samples 引数）＝ここでは構造検査
                "p_max": limits.get("p_max"), "count_range": limits.get("count_range"),
                "role_max": limits.get("role_max"), "depth_max": limits.get("depth_max"),
                "k_max": limits.get("k_max"), "r_min": limits.get("r_min")})
        except ex.RecipeError as e:
            code = str(e)[7:9] if "G" in str(e)[:12] else "G?"
            rejects[code] += 1
            continue
        h = recipe_hash(r)
        if h in seen_hash:
            dup += 1
            continue
        seen_hash.add(h)
        structures.append(r)
    if len(structures) < trials1:
        raise SystemExit(f"[歩4 エラー] 構造が {trials1} 本そろわない（{len(structures)} 本・拒否 {dict(rejects)}）")
    bd = structure_breakdown(structures, catalog_total)
    print(f"[構造の内訳（機械出力・R3 完了の線⑤）] {json.dumps(bd, ensure_ascii=False)}")
    print(f"[生成拒否の理由別件数] {json.dumps(dict(rejects), ensure_ascii=False)} ／ 重複（正規形で同一） {dup} 本")

    # ── D11＝案そのものを記録に残す ＋ G2＝生成のたびの照合（D1・2026-08-07）──
    #   適合率が100%未満、または表が未承認なら、check_structures が SystemExit(1)＝試行を1本も走らせない。
    spath = run_dir / "structures.json"
    spath.write_text(json.dumps({"structures": structures}, ensure_ascii=False, sort_keys=True) + "\n",
                     encoding="utf-8")
    print(f"[D11] 案そのもの {len(structures)} 本を {spath} に記録（journal の idx と1対1）")
    import gen_signal_families as gsf
    gsf.check_structures(str(spath))

    # ── 材料の組み立てと解決表（探索開始時に1回固定・§5-4）──
    df2 = attach_materials(df, structures)
    geo = _geo_of(df2)
    qtable = build_qtable(df2, geo, structures, limits["quantile_grid"], start, end)
    (run_dir / "qtable.json").write_text(json.dumps(qtable, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                         encoding="utf-8")
    print(f"[分位の解決表] {len(qtable)} 鍵 × {len(limits['quantile_grid'])} 分位を値決め窓から1回固定"
          f"（rolling しない・保存 {run_dir / 'qtable.json'}）")

    # ── 第1段の実行 ──
    legacy_total = 0
    results1: list[dict] = []
    reused = 0
    for si, r in enumerate(structures):
        key = f"s1/{si}/{recipe_hash(r)}"
        got = jn.get(key)
        if got is not None:
            reused += 1
            results1.append(got)
            continue
        res = run_trial(df2, r, qtable, judge, start, end)
        legacy_total += len(res["rep"]["legacy使用"])
        ok, why = per_day_gate(res, min_per_day)   # 0玉の門（0c）＋件数/日 の下限（D6）を1本で
        if ok and net_floor is not None and res["total"] < net_floor:
            ok, why = False, f"net の下限 ${net_floor:,.0f} に対して ${res['total']:+,.0f}"
        gate_ok, gate_why = strat_gate(base_trades, res["t"], atr_edges, judge)
        if ok and gate_ok is False:
            ok, why = False, f"層化の門: {gate_why}"
        daily = None
        # ★2026-08-05 改訂（まこさん OK・fix_map 決定-確認走行を数えない）＝ok の条件を外した。
        #   直す前は「ゲートを通った試行」だけ日ごとの net を作っていたので、捨てた試行が
        #   DSR の統計に入れられなかった。ゲートは 売買を回して審判の net を出した "後で" 捨てる門
        #   ＝捨てた試行も「比べた」。DSR は選ばれなかった試行の情報を使う設計（Bailey & LdP 2014）。
        if len(res["t"]):
            import tuner_stats
            s = tuner_stats.daily_net(res["t"], judge, start, end)
            tuner_stats.check_daily_sum(s, res["total"])
            daily = [round(float(x), 4) for x in s.to_numpy()]
        rec = {"stage": 1, "idx": si, "total": res["total"], "n": res["n"],
               "per_day": round(res["per_day"], 4), "ok": ok, "why": why,
               "gate": gate_why if gate_ok is not None else "判定不能（土台なし or 帯の値がまこさん待ち）",
               "daily": daily}
        jn.put(key, rec)
        results1.append(rec)
    if reused:
        print(f"[R12 再開] 済み {reused} 本を journal から再利用・今回実行 {trials1 - reused} 本")
    if legacy_total:
        raise SystemExit(f"[歩4 エラー] 探索レシピに legacy が {legacy_total} 件（恒等レーン専用＝混入は不正）")
    print("[legacy 使用] 0 件（探索レシピに legacy なし＝番人）")

    kept = [r for r in results1 if r["ok"]]
    dropped = [r for r in results1 if not r["ok"]]
    print(f"[第1段] 通過 {len(kept)} 本 ／ ゲートで捨てた試行 {len(dropped)}/{len(results1)} 本（黙って消さない）")
    for r in sorted(dropped, key=lambda z: -z["total"])[:3]:
        print(f"  #{r['idx']}: net ${r['total']:+,.0f} / {r['n']}玉 / {r['per_day']:.2f}件/日 ← {r['why']}")
    write_kakikudashi(run_dir, structures, results1, kept, seed)   # D1 完了の線①＋監査 G4 の材料

    # ── BH 法（第1段のサンプルだけ・CP1 提案4(e)）──
    #   BH は「どの候補を採択するか」の門なので、対象は通過した試行のまま（2026-08-05 も不変）。
    stat_kept = [r for r in kept if r.get("daily")]
    # ★DSR/PBO は「何通り比べたか」を数えるので、捨てた試行も入れる（2026-08-05 新設）。
    stat_all = [r for r in results1 if r.get("daily")]
    pvals = [pvalue_daily(np.array(r["daily"])) for r in stat_kept]
    fdr_q = limits.get("fdr_q")
    survivors_idx = [r["idx"] for r in stat_kept]
    if pvals:
        if fdr_q is None:
            print(f"[BH 法] q が値待ち（まこさんが決める）＝採択の印は出さない。p 値の分布だけ機械出力:"
                  f" 最小 {min(pvals):.4f} ／ 中央 {float(np.median(pvals)):.4f} ／ {len(pvals)} 本")
        else:
            sel = bh_select(pvals, float(fdr_q))
            survivors_idx = [r["idx"] for r, s in zip(stat_kept, sel) if s]
            print(f"[BH 法] q={fdr_q}: {len(pvals)} 本中 {sum(sel)} 本を採択（偽発見率の制御・第1段のみ）")
    else:
        print("[BH 法] 統計対象ゼロ（通過した試行に売買が無い）")

    # ── DSR/PBO＝第1段のサンプルだけから（CP1 解A・4-16／4-21 の実装）──
    stats = None
    if len(stat_all) >= 2 and stat_kept:
        import tuner_stats
        is_search = (purpose == tuner_stats.PURPOSE_SEARCH)
        daily = {r["idx"]: pd.Series(np.array(r["daily"]),
                                     index=pd.date_range(start.normalize(), periods=len(r["daily"]), freq="D"))
                 for r in stat_all}                       # ★試した全部（捨てた分も含む）
        kept_ids = {r["idx"] for r in stat_kept}          # 選定の対象は通過した試行だけ
        best_id = max(kept_ids, key=lambda k: float(daily[k].sum()))
        key = f"gen/{tag or 'run'}@{pd.Timestamp(start).date()}_{pd.Timestamp(end).date()}"
        past = tuner_stats.load_cumulative(key) if is_search else 0
        stats = tuner_stats.evaluate(daily, best_id, past)
        d = stats["dsr"]
        print(f"[統計＝第1段ランダムのみ] 分散・p値・PBO の入力はランダム段 {stats['n_raw']} 本"
              f"（うち通過 {len(stat_kept)} 本・捨てた {stats['n_raw'] - len(stat_kept)} 本も"
              "『比べた』ので数に入れる＝2026-08-05）"
              "（TPE の試行は入れない＝CP1 解A・『独立に撒く段は未実装』の警告をここで解消）")
        # ★ばらつき（分散）を測った単位（2026-08-06）＝黙って切り替えないための表示。
        if stats["v_unit"] == "cluster":
            print(f"  ばらつきは まとめた {stats['n_var']} グループの成績から測った（標準 ONC の形）")
        else:
            print(f"  ⚠️ ばらつきは まとめる前の {stats['n_var']} 本の成績から測った"
                  "＝グループが2つ未満で、グループごとだと分散が 0 になり罰が消えるため戻した")
        if not is_search:
            print("  ⚠️ 確認の走行（purpose=check）＝合格の印は出さない・値の選択には使わない")
        elif stats["pbo"]:
            print(f"  DSR {d['dsr']:.3f} ／ PBO {stats['pbo']['pbo']:.3f}")
        else:
            print(f"  DSR {d['dsr']:.3f} ／ PBO 測れない（候補不足）")
        # ★走行の目的で行き先が変わる（2026-08-05）。足すのは「まとめた後の数」＝判定に使う数と同じ。
        where, tot = tuner_stats.record_run(key, stats["n_eff"],
                                            pd.Timestamp.now().strftime("%Y-%m-%d"), purpose, note=tag)
        if is_search:
            print(f"  この窓での累積の試行数を {tot} 本に更新した"
                  f"（足したのは まとめた後の {stats['n_eff']} 本＝判定に使った数と同じ）")
        else:
            print(f"  累積（合格の線に効く数）は1本も増やしていない＝確認の帳簿に {tot} 件目として残した")
    else:
        print("[統計＝第1段ランダムのみ] 売買のあった試行が2本未満、または通過ゼロ＝判定できない")

    # ── 第2段＝有望構造の値を TPE で詰める（統計判定に不使用）──
    top_pool = [r for r in kept if r["idx"] in survivors_idx] or kept
    top = sorted(top_pool, key=lambda z: -z["total"])[:top_k]
    stage2_best: list[dict] = []
    if trials2 > 0 and top:
        import optuna
        optuna.logging.set_verbosity(optuna.logging.WARNING)
        per = max(trials2 // len(top), 1)
        for rank, r1 in enumerate(top):
            recipe = structures[r1["idx"]]
            slots = value_slots(recipe, limits)
            if not slots:
                stage2_best.append({"idx": r1["idx"], "total": r1["total"], "params": {}})
                continue
            def obj(trial, recipe=recipe, slots=slots, sidx=r1["idx"]):
                choices = {p: suggest_slot(trial, p.replace(".", "_"), sp) for p, sp in slots}
                key = f"s2/{sidx}/{trial.number}/" + hashlib.sha256(
                    json.dumps(choices, sort_keys=True, default=str).encode()).hexdigest()[:12]
                got = jn.get(key)
                if got is not None:
                    return got["total"] if got["ok"] else -1e9
                r2 = apply_slots(recipe, choices)
                res = run_trial(df2, r2, qtable, judge, start, end)
                ok, why = per_day_gate(res, min_per_day)   # 第1段と同じ1本の門（0玉＋件数/日 の下限）
                gate_ok, _gw = strat_gate(base_trades, res["t"], atr_edges, judge)
                if ok and gate_ok is False:
                    ok, why = False, "層化の門"
                jn.put(key, {"stage": 2, "idx": sidx, "trial": trial.number, "total": res["total"],
                             "n": res["n"], "per_day": round(res["per_day"], 4), "ok": ok, "why": why})
                return res["total"] if ok else -1e9
            st = optuna.create_study(direction="maximize",
                                     sampler=optuna.samplers.TPESampler(seed=int(seed * 1000 + rank)))
            st.optimize(obj, n_trials=per, show_progress_bar=False)
            stage2_best.append({"idx": r1["idx"], "total": float(st.best_value),
                                "params": dict(st.best_trial.params)})
        print(f"[第2段 TPE] 有望 {len(top)} 構造 × 各 {per} 本＝値の微調整（★統計判定に不使用＝CP1 解A）")
        for b in stage2_best:
            print(f"  構造 #{b['idx']}: 第1段 ${next(z['total'] for z in top if z['idx']==b['idx']):+,.0f}"
                  f" → 第2段 best ${b['total']:+,.0f}")
    # ══ tuner_judgement（判定表）＝A と B の合否を1枚で出す（2026-08-05 新設・まこさん OK「OK」）══
    #   直す前は、この器が判定表を1行も出していなかった。出すには確認窓の成績が要る（B2 が要求する）が、
    #   この器は値決め窓しか走らせていなかった。ここで確認窓の1走を足してつなぐ。
    #   ★確認窓では分位（閾値の基準の値）を作り直さない＝値決め窓で1回固定した qtable をそのまま使う。
    #     作り直すと「確認窓を見て閾値を選び直した」ことになり、窓の決まり（periods.py）に反する。
    #   ★tuner_judgement の中身は変えない＝古い器と新しい器が同じ表を使う（変えると古い器の合否まで動く）。
    verdict = None
    if df_confirm is not None and kept:
        import tuner_judgement as tj
        best_rec = max(kept, key=lambda z: z["total"])
        best_struct = structures[best_rec["idx"]]
        # 値決め窓でもう1回だけ走らせる＝journal は売買記録を残していないため（1試行ぶんの費用）
        rs_j = run_trial(df2, best_struct, qtable, judge, start, end)
        df2c = attach_materials(df_confirm, [best_struct])
        rc_j = run_trial(df2c, best_struct, qtable, judge, confirm_start, confirm_end)   # ★同じ qtable
        print(f"\n[確認窓の1走] 構造 #{best_rec['idx']}（値決め窓で最良）を確認窓で1回だけ走らせた"
              f"＝net ${rc_j['total']:+,.0f} ／ {rc_j['n']}玉 ／ {rc_j['per_day']:.2f}件/日"
              "（★ここで選び直しはしない・分位は値決め窓のものを流用）")
        bands = None
        if base_trades is not None and atr_edges:
            bands = tj.atr_bands(base_trades, rs_j["t"], atr_edges)
        verdict = tj.print_judgement(base, rs_j, rc_j, min_per_day, stats, len(kept),
                                     rules=rules, rfloor=rfloor, trials=trials1 + trials2,
                                     stage_bests=None, bands=bands,
                                     save_tag=f"gen_{tag or 'run'}",
                                     save_note=f"新しい器（engine_tuner_gen）／構造 #{best_rec['idx']}"
                                               f"／第1段 {trials1} 本・第2段 {trials2} 本／目的 {purpose}")
    elif df_confirm is not None:
        print("\n[判定表] 通った構造が0本＝比べる相手がいないので出さない（偽装の✅を出さない）")

    print("\n⚠️ ここは探索側の数字＝採否の数字ではない。統合最終形1つだけを採点窓 score.py にかけ、採否はまこさんが判断する。")
    return {"breakdown": bd, "rejects": dict(rejects), "kept": len(kept), "dropped": len(dropped),
            "pvals": pvals, "stats": stats, "stage2": stage2_best, "qtable_keys": len(qtable),
            "reused": reused, "results1": results1, "verdict": verdict}


# ══ 検収専用（selftest／--dry-run）＝採否・本走に使わない ═══════════════════════════════════
KENSHU_LIMITS = {
    # ★検収専用（§11 の値はまこさんが決める＝この値は生成器の機械の検収にだけ使い、本走・採否に使わない）
    "n_min": None, "r_min": None,
    "role_max": {"env": 2, "sufficiency": 2, "location": 1},
    "count_range": [3, 6], "k_max": 3,
    "quantile_grid": ["q20", "q50", "q80"], "depth_max": 3, "p_max": 2,
    "state_mult_grid": [1.0], "int_grid": [3, 6, 12],
    # 保有時間の上限＝検収専用の範囲（本走は役割から決める＝resolve_hold_range・監査 4-19／要件 R6）
    "hold_bars": (1, 24), "hold_role": "検収専用",
    "hour_grid": [6, 12, 18], "frac_grid": [50.0], "exit_mult_grid": [50.0, 100.0],
    "max_adds_grid": [1, 2], "fdr_q": 0.10,
    # 出口の枝（D2・2026-08-07）＝検収専用の値。本走は search_limits.json の格子を使う。
    "hold_frac_grid": [0.5], "giveback_grid": [0.5], "loss_cap_grid": [0.6], "ladder_steps_grid": [1, 2],
}


def synth_df(n: int = 3000, seed: int = 7) -> pd.DataFrame:
    """検収用の合成5分足＝レンジ相場もどき（実データを使わない＝累積試行を汚さない・L-373 と同じ思想）。"""
    rng = np.random.default_rng(seed)
    ts = pd.date_range("2024-05-01", periods=n, freq="5min")
    S = 1000.0                                    # 価格帯を実勢（10万ドル級）に＝最小注文額 H9 を満たす
    mid = (100.0 + np.cumsum(rng.normal(0, 0.02, n))) * S
    osc = 3.0 * S * np.sin(np.arange(n) / 40.0)
    c = mid + osc + rng.normal(0, 0.05 * S, n)
    o = np.roll(c, 1)
    o[0] = c[0]
    h = np.maximum(o, c) + rng.uniform(0.0, 0.2 * S, n)
    l = np.minimum(o, c) - rng.uniform(0.0, 0.2 * S, n)
    v = rng.uniform(0.5, 2.0, n)
    atr = (np.full(n, 1.0) + (np.arange(n) % 3) * 0.7) * S    # 帯が3つに割れる（層化の門の検収用）
    k = 50.0 + 45.0 * np.sin(np.arange(n) / 7.0)
    d = pd.Series(k).rolling(3).mean().fillna(50.0).to_numpy()
    return pd.DataFrame({
        "ts": ts, "open": o, "high": h, "low": l, "close": c, "volume": v,
        "atr": atr, "adx": 20.0, "stoch_k": k, "e38_stoch_d": d, "rsi9": 50.0, "dev_z": 0.0,
        "range_ok_rg5": True, "rg5_uptrend": False,
        "v11_res_hi": mid + 3.2 * S, "v11_res_lo": mid + 2.8 * S, "v11_sup_hi": mid - 2.8 * S,
        "v11_sup_lo": mid - 3.2 * S, "v11_mid": mid,
        "e38_htf_roc24_2h": 0.0, "e38_vol_volr20_15m": 2.0,
    })


def selftest() -> int:
    """番人＝生成器の機械が正しく効くか（合成データのみ・実データの試行ゼロ・累積試行の記録なし）。"""
    import tempfile
    import score as judge
    ng: list[str] = []
    lm = dict(KENSHU_LIMITS)
    pool, tfs, cat_total = material_pool()
    tfs_small = ["5m", "15m"]

    # T1 構造100本＝全部が検証器を通り、内訳が出て、legacy がゼロ
    structs = []
    for i in range(100):
        rng = np.random.default_rng([11, 1, i])
        try:
            r = sample_structure(rng, lm, pool, tfs_small)
            ex.validate_recipe(r, limits={"p_max": lm["p_max"], "count_range": lm["count_range"],
                                          "role_max": lm["role_max"], "depth_max": lm["depth_max"],
                                          "k_max": lm["k_max"]})
            structs.append(r)
        except (SampleError, ex.RecipeError):
            continue
    if len(structs) < 80:
        ng.append(f"T1: 100回の撒きで検証を通った構造が {len(structs)} 本（80 本未満＝生成が弱すぎる）")
    bd = structure_breakdown(structs, cat_total)
    if bd["触れた列"] < 10 or len(bd["形の分布"]) < 5:
        ng.append(f"T1: 内訳が痩せている（触れた列 {bd['触れた列']}・形 {len(bd['形の分布'])}種）")
    lane_bad = [r for r in structs if r["meta"].get("lane")]
    if lane_bad:
        ng.append("T1: 探索構造に lane が付いている（legacy 混入経路）")

    # T2 BH 法の既知答え（q=0.05・p=[0.001,0.01,0.02,0.04,0.2,0.9] → 3 本採択）
    sel = bh_select([0.001, 0.01, 0.02, 0.04, 0.2, 0.9], 0.05)
    if sum(sel) != 3 or sel != [True, True, True, False, False, False]:
        ng.append(f"T2: BH の既知答え不一致（3本のはずが {sum(sel)} 本・{sel}）")
    if bh_select([], 0.05) != []:
        ng.append("T2: 空リストで空が返らない")

    # T3 p 値＝プラスに寄った列は小さく・ゼロ列は 0.5 付近
    rngp = np.random.default_rng(3)
    p_pos = pvalue_daily(rngp.normal(1.0, 1.0, 200))
    p_zero = pvalue_daily(rngp.normal(0.0, 1.0, 200))
    if not (p_pos < 0.01):
        ng.append(f"T3: プラスの列の p が小さくない（{p_pos:.3f}）")
    if not (0.05 < p_zero < 0.95):
        ng.append(f"T3: ゼロの列の p が偏っている（{p_zero:.3f}）")

    # T4 解決表＝同じ入力から2回作って完全一致（探索開始時に1回固定の決定論）
    df = synth_df()
    geo = {"帯内位置%": ((df["close"] - df["v11_mid"]) / (df["v11_res_hi"] - df["v11_mid"])).to_numpy(float),
           "W%": ((df["v11_res_hi"] - df["v11_sup_lo"]) / df["close"] * 100.0).to_numpy(float)}
    df_m = attach_materials(df, structs[:20])
    s4 = pd.Timestamp(df["ts"].iloc[0]).normalize()
    e4 = s4 + pd.Timedelta(days=10)               # 丸1日×10日＝日次分割（daily_net）の定義と整合させる
    q1 = build_qtable(df_m, geo, structs[:20], lm["quantile_grid"], s4, e4)
    q2 = build_qtable(df_m, geo, structs[:20], lm["quantile_grid"], s4, e4)
    if json.dumps(q1, sort_keys=True) != json.dumps(q2, sort_keys=True):
        ng.append("T4: 解決表が決定論でない")
    if not q1:
        ng.append("T4: 解決表が空（分位を使う構造が無いのは不自然）")

    # T5 層化の門＝門の判定だけをスタブ審判で単体検査（帯分け＝atr_14/entry_price・net はスタブの合計）
    class _StubJudge:
        def score(self, t):
            return {"total": float(t["fake_net"].sum())}
    base_t = pd.DataFrame({"atr_14": [1.0, 1.0, 2.0, 2.0, 3.0, 3.0],
                           "entry_price": [100.0] * 6,
                           "fake_net": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0]})
    same_t = base_t.copy()
    worse_t = base_t.copy()
    worse_t.loc[worse_t["atr_14"] == 2.0, "fake_net"] = -1.0   # 真ん中の帯だけ悪化
    edges5 = [1.5, 2.5]
    okg, _w = strat_gate(base_t, same_t, edges5, _StubJudge())
    okb, w2 = strat_gate(base_t, worse_t, edges5, _StubJudge())
    if okg is not True:
        ng.append(f"T5: 同一候補が門を通らない（{_w}）")
    if okb is not False or "1.5〜2.5" not in w2:
        ng.append(f"T5: 悪化した候補が門で弾かれない（{okb}・{w2}）")
    okn, wn = strat_gate(None, same_t, edges5, _StubJudge())
    if okn is not None or "判定不能" not in wn:
        ng.append("T5: 土台なしで判定不能にならない（偽装の✅経路）")

    # T6 ミニ本走（合成データ・第1段10本＋第2段6本）→ R12 再開＝journal から再利用して同一結果
    #   ★2026-08-05 追加: 走行の目的（purpose）を渡す。ここは検収なので check＝累積に数えない。
    #     本物の記録ファイル2本には触らせない（一時の場所へ差し替える＝この検査そのものが
    #     試した回数を1本も増やさない・帳簿も汚さない）。
    import tuner_stats as _ts
    with tempfile.TemporaryDirectory() as td:
        run_dir = pathlib.Path(td) / "run1"
        run_dir.mkdir(parents=True)
        _real_cum, _real_chk = _ts.CUMULATIVE, _ts.CHECK_RUNS
        _ts.CUMULATIVE = pathlib.Path(td) / "cum.json"
        _ts.CHECK_RUNS = pathlib.Path(td) / "chk.json"
        kw = dict(limits=lm, judge=judge, start=s4, end=e4, trials1=10, trials2=6, top_k=2,
                  seed=11, run_dir=run_dir, pool=pool, tfs=tfs_small, catalog_total=cat_total,
                  purpose=_ts.PURPOSE_CHECK, tag="selftest")
        import contextlib
        import io
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                out1 = run_generation(df, **kw)
            with contextlib.redirect_stdout(buf):
                out2 = run_generation(df, **kw)
            # T6b（2026-08-05 新設）＝確認の走行では累積が1本も増えない
            if _ts.CUMULATIVE.exists():
                ng.append("T6b: 確認の走行なのに累積ファイルが作られた（数えない約束が守られていない）")
        finally:
            _ts.CUMULATIVE, _ts.CHECK_RUNS = _real_cum, _real_chk
        if out2["reused"] != 10:
            ng.append(f"T6: 再開で第1段 10 本が再利用されない（{out2['reused']} 本）")
        a = [(r["idx"], r["total"], r["ok"]) for r in out1["results1"]]
        b = [(r["idx"], r["total"], r["ok"]) for r in out2["results1"]]
        if a != b:
            ng.append("T6: 再開の結果が初走と一致しない（R12 が壊れている）")
        # meta が違う journal は拒否（fail-closed）
        try:
            Journal(run_dir / "journal.jsonl", {"seed": 999})
            ng.append("T6: meta 食い違いの journal が拒否されない")
        except SystemExit:
            pass

    # T7 値待ち＝limits に null が在れば「まこさん待ち」として検出できる（fail-closed の仕組みの検査）
    #
    # ★2026-08-03 に直しました。直す前の T7 は「search_limits.json に null が在ること」を検査していました。
    #   しかし 2026-08-02 の commit a9368fe で R_MIN が 0.25 に決まり、null がゼロになりました。
    #   その時点から T7 は ❌ を出し続けていました。誰も生成器の自己検査を走らせ直さなかったので、
    #   気づかれませんでした（監査 4-19 の作業中 2026-08-03 に発見）。
    #   検査したいのは「ファイルにいま null が在ること」ではなく「null を検出できること」です。
    #   だから、わざと null を1つ入れた設定ファイルを作って、検出されるかを見る形へ直しました。
    _lm_real, waiting = load_limits()
    with tempfile.TemporaryDirectory() as _td:
        _p = pathlib.Path(_td) / "search_limits_null.json"
        _inj = json.loads(LIMITS_PATH.read_text(encoding="utf-8"))
        _inj["r_min"] = None                      # わざと1つ空にする
        _p.write_text(json.dumps(_inj, ensure_ascii=False), encoding="utf-8")
        _lm2, _w2 = load_limits(_p)
        if not _w2:
            ng.append("T7: 値が空（null）でも『まこさん待ち』として検出されない（fail-closed が死んでいる）")
    if waiting:
        ng.append(f"T7: いまの search_limits.json に値待ちが残っている＝本走は始められない: {waiting}")

    # T8 サンプル不能が黙って通らない（役割の予算ゼロで count_range を満たせない）
    bad = dict(lm)
    bad["role_max"] = {"env": 0, "sufficiency": 0, "location": 0}
    bad["count_range"] = [4, 4]
    rng8 = np.random.default_rng(8)
    r8 = sample_structure(rng8, bad, pool, tfs_small)
    try:
        ex.validate_recipe(r8, limits={"count_range": bad["count_range"], "role_max": bad["role_max"]})
        ng.append("T8: 本数を満たせない構造が検証を素通り（G5 で止まるはず）")
    except ex.RecipeError:
        pass

    # T10 tuner_judgement（判定表）の接続（2026-08-05 新設）＝3つ
    #   ① 確認窓で分位（閾値の基準の値）を作り直さない＝値決め窓で1回固定したものを流用する
    #   ② 土台が無いときに「これ以上出ない」と言わない（偽装の✅を出さない）
    #   ③ 確認窓が採点窓に掛かるときは走らせない（③は T9 の窓の検査と同じ関門）
    import contextlib as _ctx10
    import io as _io10

    import tuner_judgement as _tj10
    import tuner_stats as _ts10
    t10 = []
    _real_qt = globals()["build_qtable"]
    _calls = {"n": 0}

    def _counting_qtable(*args, **kw):
        _calls["n"] += 1
        return _real_qt(*args, **kw)
    with tempfile.TemporaryDirectory() as td10:
        rd10 = pathlib.Path(td10) / "run"
        rd10.mkdir(parents=True)
        _rc, _rk = _ts10.CUMULATIVE, _ts10.CHECK_RUNS
        _jd = _tj10.JUDGE_DIR
        _ts10.CUMULATIVE = pathlib.Path(td10) / "cum.json"
        _ts10.CHECK_RUNS = pathlib.Path(td10) / "chk.json"
        _tj10.JUDGE_DIR = pathlib.Path(td10) / "judgement"
        globals()["build_qtable"] = _counting_qtable
        try:
            with _ctx10.redirect_stdout(_io10.StringIO()):
                # ★T6 と同じ種と本数を使う（この合成データで材料が組み立てられることが確認済みの経路）
                out10 = run_generation(df, limits=lm, judge=judge, start=s4, end=e4,
                                       trials1=10, trials2=0, top_k=2, seed=11, run_dir=rd10,
                                       pool=pool, tfs=tfs_small, catalog_total=cat_total,
                                       purpose=_ts10.PURPOSE_CHECK, tag="t10",
                                       df_confirm=df, confirm_start=s4, confirm_end=e4,
                                       base=None)
        finally:
            globals()["build_qtable"] = _real_qt
            _ts10.CUMULATIVE, _ts10.CHECK_RUNS = _rc, _rk
            _tj10.JUDGE_DIR = _jd
        if _calls["n"] != 1:
            t10.append(f"① 分位の解決表を {_calls['n']} 回 作った（確認窓では作り直さない＝1回のはず）")
        if out10.get("kept") and out10.get("verdict") is None:
            t10.append("② 通った構造が在るのに判定表を出していない")
        if out10.get("verdict") == _tj10.PASS:
            t10.append("② 土台が無いのに『これ以上出ない』と出た（偽装の✅）")
    ng += [f"T10: {x}" for x in t10]

    # T9 本走の関門（2026-08-05 新設）＝3つの止まり方。1つでも素通りしたら本走を作った意味がない
    import inspect

    import tuner_stats as _ts9
    from periods import SCORE_END, SCORE_START, SEARCH_END, SEARCH_START
    t9 = []
    for bad_p in (None, "", "SEARCH", "確認"):           # ① 目的の宣言（既定に倒れない）
        try:
            pre_run_gate("e38", bad_p, SEARCH_START, SEARCH_END, None, {}, None)
            t9.append(f"目的 {bad_p!r} で止まらない")
        except SystemExit:
            pass
    try:                                                  # ② 採点窓に掛かる窓（H8・L-267）
        pre_run_gate("e38", _ts9.PURPOSE_CHECK, SCORE_START, SCORE_END, None, {}, None)
        t9.append("採点窓に掛かる窓で止まらない")
    except SystemExit:
        pass
    try:                                                  # ②b 確認窓が採点窓に掛かる（2026-08-05 追加）
        pre_run_gate("e38", _ts9.PURPOSE_CHECK, SEARCH_START, SEARCH_END, None, {}, None,
                     confirm_end=SCORE_END)
        t9.append("確認窓が採点窓に掛かっても止まらない")
    except SystemExit:
        pass
    try:                                                  # ③ 役割の下限割れ（監査 4-14）
        pre_run_gate("e38", _ts9.PURPOSE_CHECK, SEARCH_START, SEARCH_END,
                     1.0, {"ops_min_per_day": 1.0}, 5.0)
        t9.append("役割の下限 5 を下回る線 1 で止まらない")
    except (SystemExit, Exception) as e:                  # noqa: BLE001  RoleFloorError も含めて止まればよい
        if "役割の下限" not in str(e):
            t9.append(f"③ の止まり方が役割の下限でない: {str(e)[:60]}")
    try:                                                  # 正しい組み合わせは通る（過剰に止めない）
        pre_run_gate("e38", _ts9.PURPOSE_CHECK, SEARCH_START, SEARCH_END, None, {}, None)
    except Exception as e:                                # noqa: BLE001
        t9.append(f"正しい組み合わせなのに止まる: {str(e)[:60]}")
    # T9b 本走の入口が、その関門を実際に呼んでいるか（丸括弧まで見る＝L-394 の型）
    if "pre_run_gate(" not in inspect.getsource(run_main):
        t9.append("T9b: run_main が pre_run_gate( を呼んでいない（関門が配線されていない）")
    ng += [f"T9: {x}" for x in t9]

    # T11 別名の列でも分位の解決表が作れるか（D4 の直し・2026-08-07 新設）
    #   直す前は build_qtable が別名を見なかった。カタログ名の列が無く別名だけ在ると、
    #   その列に分位が当たった瞬間に本走が丸ごと止まった（2026-08-06 実測＝Stoch%D14__2h で停止）。
    #   ここでは カタログ名の列を わざと作らず、別名の列だけを置いて、解決表が作れることを見る。
    t11 = []
    alias_name = "ADX14__2h"                      # RUNTIME_ALIAS の7列のうちの1つ
    alias_col = ex.RUNTIME_ALIAS.get(alias_name)
    if alias_col is None:
        t11.append(f"前提が崩れている: {alias_name} が RUNTIME_ALIAS に無い")
    else:
        n11 = 600
        df11 = pd.DataFrame({
            "ts": pd.date_range("2024-03-01", periods=n11, freq="5min"),
            "open": 60000.0, "high": 60010.0, "low": 59990.0, "close": 60000.0, "volume": 1.0,
        })
        df11[alias_col] = np.linspace(10.0, 40.0, n11)      # ★別名の列だけを置く
        if alias_name in df11.columns:
            t11.append("前提が崩れている: カタログ名の列を作ってしまっている")
        rec11 = {
            "meta": {"strategy": "e38", "logic_id": "T11", "side": "SHORT", "lane": ""},
            "pre_filter": [],
            "entry": {"connective": {"all": [
                {"role": "trigger", "form": "level",
                 "material": [{"family": "ADX", "param": 14, "tf": "2h"}],
                 "side": "above", "value": {"threshold_q": "q50"}}]}},
            "exits": [], "position": {"mode": "separate", "max_adds": 1},
        }
        try:
            qt11 = build_qtable(df11, {}, [rec11], ["q10", "q50", "q90"],
                                start=pd.Timestamp("2024-03-01"), end=pd.Timestamp("2024-03-03"))
            if alias_name not in qt11:
                t11.append(f"解決表に {alias_name} の鍵が無い")
            elif not np.isfinite(qt11[alias_name]["q50"]):
                t11.append(f"{alias_name} の q50 が数値でない")
        except SystemExit as e:
            t11.append(f"別名の列で止まった（D4 が直っていない）: {str(e)[:80]}")
    ng += [f"T11: {x}" for x in t11]

    # T12 売買ゼロ（0玉）の案が候補に残らない（D3 の一部・0c・2026-08-07 まこさん OK）
    #   直す前は min_per_day が空欄だと門が無く、0玉（net $0）の案が「通過」し、
    #   負けた案（net マイナス）より net が大きいので「最良」に選ばれた（2026-08-05 実測＝#0 が選ばれた）。
    t12 = []
    ok0, why0 = zero_trade_gate({"n": 0, "per_day": 0.0, "total": 0.0})
    if ok0 is not False or "売買ゼロ" not in why0:
        t12.append("0玉の案が門を素通り（min_per_day が空欄でも捨てるはず）")
    ok1, _w1 = zero_trade_gate({"n": 3, "per_day": 0.01, "total": -5.0})
    if ok1 is not True:
        t12.append("売買が在る案（負けでも）が0玉の門で捨てられた（下限の値の判定はまこさん待ち＝ここではしない）")
    z_bad = [r for r in out1["results1"] if r["n"] == 0 and r["ok"]]
    if z_bad:
        t12.append(f"実走（T6 のミニ本走）の第1段で 0玉の案が {len(z_bad)} 本 通過している")
    ng += [f"T12: {x}" for x in t12]

    # T15 件数/日 の下限が実際に案を捨てる（D3 の残り・D6・まこさん OK 2026-08-07「OK」）
    #   直す前は 11本のうち9本が空欄で門が無く、残り2本（S2・L1i）は CC が置いた 2.0 で
    #   役割の絶対下限 5.0 を下回るため走らせられなかった（2026-08-07 実測）。
    #   ここで見るのは4つ＝①下回る案を捨てる ②届く案は負けでも通す
    #   ③★メタ確認＝下限を空欄に戻すと同じ案が通る（＝止めているのが確かに下限であること）
    #   ④実物の設定ファイルの11本が、全部 役割の絶対下限以上であること。
    t15 = []
    ng15, why15 = per_day_gate({"n": 600, "per_day": 4.99, "total": 999.0}, 5.0)
    if ng15 is not False or "件数の下限" not in why15:
        t15.append("下限 5.0 に対して 4.99件/日 の案が通った（捨てるはず）")
    ok15, _w15 = per_day_gate({"n": 700, "per_day": 5.00, "total": -50.0}, 5.0)
    if ok15 is not True:
        t15.append("下限 5.0 に対して 5.00件/日 の案が捨てられた（負けでも通すはず）")
    okn15, _wn15 = per_day_gate({"n": 600, "per_day": 4.99, "total": 999.0}, None)   # ③ メタ確認
    if okn15 is not True:
        t15.append("下限を空欄にしても 4.99件/日 の案が捨てられた＝止めているのは下限ではない")
    okz15, whyz15 = per_day_gate({"n": 0, "per_day": 0.0, "total": 0.0}, None)
    if okz15 is not False or "売買ゼロ" not in whyz15:
        t15.append("0玉の門が per_day_gate を通っていない（0c が第2段で外れる）")
    import engine_tuner as et15
    import tuner_judgement as tj15
    ad15 = et15.load_adapter("e38")
    _role15, rf15 = tj15.role_floor("e38")
    for lg15 in ad15.config()["logics"]:
        v15 = ad15.min_per_day(lg15["id"])
        if v15 is None:
            t15.append(f"{lg15['id']} の件数/日 の下限が空欄（11本とも値が要る＝D6）")
        elif rf15 is not None and v15 < rf15:
            t15.append(f"{lg15['id']} の下限 {v15:g} が役割の絶対下限 {rf15:g} を下回る")
    ng += [f"T15: {x}" for x in t15]

    # T13 D1＝生成が型の表の中に閉じている（対応表の役割×系統×時間足・禁止3・DC1〜DC4・G2 適合率100%）
    #   本物の格子（search_limits.json）・本物の部品・本物の承認済みの表で、SHORT と LONG の両方を撒いて照合する。
    t13 = []
    import gen_signal_families as gsf13
    tbl13 = load_signal_table()
    lm13, _w13 = load_limits()
    lm13 = dict(lm13)
    lm13.update(resolve_hold_range(lm13, "e38"))
    parts13 = set(tbl13["parts"])
    tfs13_all = set(tbl13["tfs"])
    banned13 = tbl13["banned"]
    sts13: list[dict] = []
    for side13 in ("SHORT", "LONG"):
        i13 = 0
        got = 0
        while got < 30 and i13 < 300:
            rng13 = np.random.default_rng([13, 1 if side13 == "SHORT" else 2, i13])
            i13 += 1
            try:
                sts13.append(sample_structure(rng13, lm13, pool, tfs, side=side13, logic_id="T13"))
                got += 1
            except SampleError:
                continue
    if len(sts13) < 60:
        t13.append(f"本物の格子で 60本 撒けない（{len(sts13)} 本）")

    def _t13_viol(st: dict) -> list[str]:
        v: list[str] = []
        side_v = st["meta"]["side"]
        conds: list = []
        gsf13._walk_conds(st["entry"]["connective"], conds)
        for c in conds:
            role = c.get("role")
            rr = tbl13["roles"].get(role)
            if rr is None:
                v.append(f"知らない役割 {role}")
                continue
            for m in (c.get("material") or []):
                kind = _lineage_of(m)
                if kind not in rr["lineages"]:
                    v.append(f"{role} に系統 {kind}（対応表の外）")
                if "family" in m:
                    name = ex.FAMILY_TEMPLATES[m["family"]].format(p=m["param"])
                    if name not in parts13 or m["tf"] not in tfs13_all:
                        v.append(f"表に無い部品/時間足 {name}__{m.get('tf')}")
                    if rr["tfs"] is not None and m["tf"] not in rr["tfs"]:
                        v.append(f"{role} に時間足 {m['tf']}（対応表の外）")
                    if (name, m["tf"]) in banned13:
                        v.append(f"禁止3 の組 {name}__{m['tf']}")
            mats = c.get("material") or []
            if (c.get("side") and c["form"] in ("level", "diff", "slope", "slope_avg")
                    and role in ("env", "sufficiency")
                    and any(_kubun_of(m) == "順張り値" for m in mats)):
                want = "below" if side_v == "SHORT" else "above"
                if c["side"] != want:
                    v.append(f"DC1 違反（{role}・順張り値・side {c['side']}）")
            if (role == "trigger" and c["form"] == "level" and mats and "family" in mats[0]
                    and iref.FAMILY_LINEAGE[mats[0]["family"]]["k"] == "オシレーター"):
                q13 = str(c.get("value", {}).get("threshold_q", ""))
                if side_v == "SHORT" and not (c.get("side") == "above" and q13 in tbl13["quantile_grid_hi"]):
                    v.append(f"DC2 違反（SHORT・side {c.get('side')}・{q13}）")
                if side_v == "LONG" and not (c.get("side") == "below" and q13 in tbl13["quantile_grid_lo"]):
                    v.append(f"DC2 違反（LONG・side {c.get('side')}・{q13}）")
            if c["form"] == "cross":
                want = "down" if side_v == "SHORT" else "up"
                if c.get("value", {}).get("direction") != want:
                    v.append(f"DC3 違反（{side_v}・{c.get('value', {}).get('direction')}）")
            if c["form"] == "candle_dir":
                want = "bear" if side_v == "SHORT" else "bull"
                if c.get("value", {}).get("dir") != want:
                    v.append(f"DC4 違反（{side_v}・{c.get('value', {}).get('dir')}）")
        return v

    viol13 = [f"#{i}: {'; '.join(vv)}" for i, st in enumerate(sts13) if (vv := _t13_viol(st))]
    if viol13:
        t13.append(f"対応表・向きの決まりの違反 {len(viol13)} 本（例＝{viol13[0]}）")
    n_ok13 = 0
    for st in sts13:
        ng13, _c13, _o13 = gsf13._judge_structure(st, parts13, tfs13_all, banned13,
                                                  set(tbl13["geo_ok"]), set(tbl13["time_ok"]))
        if not ng13:
            n_ok13 += 1
    if sts13 and n_ok13 != len(sts13):
        t13.append(f"G2 適合率が100%でない（{n_ok13}/{len(sts13)}）")
    fam13 = {st["meta"].get("signal_family") for st in sts13}
    if sts13 and not fam13 <= set(tbl13["families"]):
        t13.append(f"型のラベルが表の対象の外（{sorted(fam13)}）")
    ng += [f"T13: {x}" for x in t13]

    # ══ T14 出口の状態機械（D2・2026-08-07）＝完了の線①②④の番人 ═══════════════════════
    #   ①枝の種類が4種類より増える ②積み増しの回数で枝が切り替わる構造が組める
    #   ④枝が実際に発火した売買記録が出る・わざと条件を外すと発火しない（メタ確認つき）
    t14: list[str] = []
    import gen_exit_families as gef14
    ok14, msg14 = gef14.table_status()
    if not ok14:
        t14.append(f"出口の表が無効（{msg14}）")
    et14 = load_exit_table()
    lm14 = dict(KENSHU_LIMITS)
    lm14.update({k: v for k, v in json.loads(LIMITS_PATH.read_text(encoding="utf-8")).items()
                 if k in ("hold_frac_grid", "giveback_grid", "loss_cap_grid", "ladder_steps_grid")})
    sts14, reasons14, names14 = [], set(), set()
    for i in range(80):
        rng = np.random.default_rng([14, 8, i])
        try:
            st = sample_structure(rng, lm14, pool, tfs_small, side="SHORT", logic_id="S3")
        except SampleError:
            continue
        sts14.append(st)
        for b in st["exits"]:
            reasons14.add(b["reason"])
            names14.add(b["name"])
    # ①枝の種類（決済の名前の種類）が4種類より増えたか
    if len(reasons14) <= 4:
        t14.append(f"出口の決済の名前が {len(reasons14)} 種類しか出ない（4種類より増えること＝完了の線①）")
    # ②積み増しの回数で切り替わる枝が組めたか（scope.adds を持つ枝が在るか）
    if not any(b.get("scope", {}).get("adds") for st in sts14 for b in st["exits"]):
        t14.append("積み増しの回数で切り替わる枝が1本も出ない（完了の線②）")
    # ★表に無い決済の名前・置き場所を作っていないか（表が正本）
    allow14 = {b["reason"] for b in et14["branch_types"].values()}
    if not reasons14 <= allow14:
        t14.append(f"表に無い決済の名前を作った: {sorted(reasons14 - allow14)}")
    # ★成行（taker）の枝が、能動クローズの決済の名前だけか（H5・完了の線⑥）
    import score as _sc14
    for st in sts14:
        for b in st["exits"]:
            is_taker = b["exec"]["method"] == "taker"
            if is_taker != (b["reason"] in _sc14.TAKER_EXIT_REASONS):
                t14.append(f"執行と決済の名前が食い違う枝: {b['name']}（{b['reason']}・{b['exec']['method']}）")
                break
        if t14 and t14[-1].startswith("執行と"):
            break
    # ④実際に発火するか＝合成データで走らせて、状態機械の枝の決済が売買記録に出るか
    df14 = synth_df(1500, seed=14)
    # ★材料の列を組み立ててから走らせる（本走と同じ経路＝attach_materials）。
    #   これを抜くと「列が実行データに無い」で走行が落ちる＝番人が枝の発火を見られない。
    df14 = attach_materials(df14, sts14)
    geo14 = _geo_of(df14)          # 本走と同じ作り方（帯の4隅・中央・帯内位置%・W%）
    fired14: set = set()
    # 玉の動きで切り替わる枝＝発火の条件（fire）を持つものだけを見る（常に置く枝は対象外）
    state_names = {"TIMEDOWN", "BEEXIT", "BESTALE", "MFEEXIT", "REVIND", "BREAKOUT",
                   "MAECUTADDS", "FINSTOP"}
    picked14 = None
    for st in sts14:
        if not (state_names & {b["name"] for b in st["exits"]}):
            continue
        try:
            r14 = ex.run_recipe(df14, st, qtable=build_qtable(df14, geo14, [st], lm14["quantile_grid"]))
        except BaseException:
            continue
        tr = r14[0] if isinstance(r14, tuple) else r14
        if tr is None or not len(tr):
            continue
        got = {t.get("exit_reason") for t in (tr.to_dict("records") if hasattr(tr, "to_dict") else tr)}
        # ★どの枝で決済したかを決済の名前で見分けるので、他の枝も出す名前は除く。
        #   例＝利確の名前（TP_FILLED）は、いつも置く利確の枝も出す＝状態機械の枝の発火とは言えない。
        st_reasons = {b["reason"] for b in st["exits"] if b["name"] in state_names and b.get("fire")}
        st_reasons -= {b["reason"] for b in st["exits"]
                       if not (b["name"] in state_names and b.get("fire"))}
        if got & st_reasons:
            fired14 |= got & st_reasons
            picked14 = st
            break
    if not fired14:
        t14.append("状態機械の枝が1本も発火しなかった（完了の線④＝発火した売買記録が出ること）")
    elif picked14 is not None:
        # メタ確認＝わざと条件を外すと発火しなくなるか（枝の発火の門を届かない値にする）
        broke = copy.deepcopy(picked14)
        for b in broke["exits"]:
            if b["name"] in state_names and b.get("fire"):
                # 発火の条件を「絶対に満たさないもの」に丸ごと置き換える（保有 10^6 分＝約2年）。
                # 条件の中身を1本ずつ弄る形だと、値を持たない形（傾き・交差）が壊れず残る。
                b["fire"] = {"all": [_state_cond("hold_min", "above", {"n": 10 ** 6})]}
        try:
            r14b = ex.run_recipe(df14, broke,
                                 qtable=build_qtable(df14, geo14, [broke], lm14["quantile_grid"]))
            trb = r14b[0] if isinstance(r14b, tuple) else r14b
            gotb = {t.get("exit_reason") for t in (trb.to_dict("records") if hasattr(trb, "to_dict") else (trb or []))}
            if fired14 & gotb:
                t14.append(f"条件を届かない値にしても枝が発火した（門が飾り）: {sorted(fired14 & gotb)}")
        except BaseException as e:
            t14.append(f"メタ確認の走行が落ちた: {str(e)[:60]}")
    ng += [f"T14: {x}" for x in t14]

    print("=" * 80)
    print("engine_tuner_gen 自己検査（合成データのみ・実データの試行ゼロ・累積試行の記録なし）")
    print("=" * 80)
    print(f"  T1 構造の撒き: {len(structs)}/100 本が検証を通過 ／ 内訳 {json.dumps(bd, ensure_ascii=False)[:200]}…")
    print(f"  T2 BH 既知答え ✅ ／ T3 p値 (+){p_pos:.4f} (0){p_zero:.3f} ／ T4 解決表 {len(q1)} 鍵・決定論")
    print(f"  T5 層化の門 ／ T6 R12 再開 ／ T7 値待ち {len(waiting)} 件 ／ T8 生成不能の拒否")
    print("  T9 本走の関門: 目的の未宣言4通り・採点窓・確認窓の越境・役割の下限割れ で停止／"
          "正しい組み合わせは通過／T9b 入口が関門を呼んでいる")
    print(f"  T10 判定表の接続: 分位の解決表は {_calls['n']} 回だけ作った（確認窓では作り直さない）／"
          f"土台なしの結論 {out10.get('verdict')}（『これ以上出ない』ではない）")
    print(f"  T11 別名の列: カタログ名の列が無く別名（{ex.RUNTIME_ALIAS.get('ADX14__2h')}）だけでも"
          " 分位の解決表が作れる（D4）")
    print("  T12 0玉の門: 売買ゼロの案は min_per_day が空欄でも候補に残らない（D3 の一部・0c）／"
          "売買が在る案（負けでも）は0玉の門では捨てない")
    print(f"  T15 件数/日 の下限（D3 の残り・D6）: 下限 {ad15.min_per_day('S3'):g} で 4.99件/日 は捨て・"
          f"5.00件/日 は負けでも通す ／ 下限を空欄に戻すと同じ案が通る（メタ確認）／"
          f" 設定ファイルの11本とも 役割の絶対下限 {rf15:g} 以上")
    print(f"  T13 型の表の閉じ込め（D1）: 本物の格子で {len(sts13)} 本（SHORT/LONG）＝対応表・禁止3・DC1〜DC4 の"
          f"違反 {len(viol13)} 本 ／ G2 適合率 {n_ok13}/{len(sts13)} ／ 型のラベル {sorted(fam13)}")
    print(f"  T14 出口の状態機械（D2）: {len(sts14)} 本＝決済の名前 {len(reasons14)} 種類"
          f"（表の中だけ・4種類より増える）／枝の名前 {len(names14)} 種類 ／"
          f" 積み増しの回数で切り替わる枝あり ／ 実際に発火した枝 {sorted(fired14) or 'なし'}"
          f" ／ 条件を届かない値にすると発火しない（メタ確認）")
    if ng:
        for x in ng:
            print(f"  ❌ {x}")
        return 1
    print("  ✅ 全部 pass")
    return 0


# ══ 本走（2026-08-05 新設・next_step §6.5 の13番）══════════════════════════════════
#   直す前は、この器に本走の入口が無かった。コマンドは --selftest と --dry-run の2つだけで、
#   本体の関数 run_generation は在るのに外から呼べなかった（1213行が「本走の実装は測定2 と同時」と
#   出して終わっていた＝測定2 は 2026-08-04 に「やらない」で確定したので、その一文は嘘になっていた）。
#   ここで作るのは入口だけ。判定の1枚表（A1・A2・B1〜B7）の接続は次の一手に分ける（1ターン1変更）。

GEN_RUNS = HERE.parents[2] / "results" / "priority_rebuild" / "ratchet" / "gen_runs"


def pre_run_gate(strategy: str, purpose: str | None, start, end,
                 min_per_day, rules: dict | None, rfloor, confirm_end=None) -> None:
    """本走の前の関門3つ。1つでも欠けたら走らせない（fail-closed）。

    ① 走行の目的が宣言されているか（既定に黙って倒れない・2026-08-05 の決まり）
    ② 使う窓が採点窓に掛かっていないか（H8・L-267＝采否の窓を探索に使わない）
       ★確認窓も同じ検査に掛ける（2026-08-05 の判定表の接続で追加）
    ③ 役割から来る件数/日 の絶対下限を下回っていないか（監査 4-14・cat_requirements §8.6）
    """
    import tuner_judgement as tj
    import tuner_stats as ts
    from periods import SCORE_START
    if purpose not in ts.PURPOSES:
        raise SystemExit(f"[走行の目的エラー] --purpose は {ts.PURPOSES} のどれか。渡された値: {purpose!r}\n"
                         "  search＝値を選ぶ（試した回数に数える）／check＝道具の動作確認（数えない）。\n"
                         "  既定は持ちません＝書き忘れをここで止めます。")
    for nm, w in (("値決め窓", end), ("確認窓", confirm_end)):
        if w is not None and pd.Timestamp(w) > SCORE_START:
            raise SystemExit(f"[窓エラー] {nm} の終わり {pd.Timestamp(w).date()} が "
                             f"採点窓の始まり {SCORE_START.date()} を越えています。\n"
                             "  採点窓は采否を決める窓です。探索にも確認にも1バーも使いません（H8・L-267）。")
    tj.assert_role_floor(strategy, min_per_day, rules, rfloor)


def run_main(a) -> int:
    """本走の入口。窓は periods.py、宣言は接続ファイルと採用台帳から機械で読む（道具に数字を焼かない）。"""
    import time

    import engine_tuner as et                  # データの読み込みと接続ファイルの解決を使い回す（二重に書かない）
    import score as judge                      # 審判＝import のみ・無変更（H13）
    import tuner_judgement as tj
    import tuner_stats as ts
    from periods import CONFIRM_END, CONFIRM_START, SEARCH_END, SEARCH_START

    ad = et.load_adapter(a.strategy)           # ★戦略の中身を知るのは接続ファイルだけ（要件 R4）
    known = {z["id"]: z for z in ad.logics()}
    if a.logic not in known:
        raise SystemExit(f"[エラー] ロジック id が {ad.NAME} に無い: {a.logic}（在るのは {', '.join(known)}）")
    side = (known[a.logic].get("side") or "SHORT").upper()
    regime = ad.regime(a.logic)
    rules = getattr(ad, "stop_rules", lambda _l: {})(a.logic)
    mpd = ad.min_per_day(a.logic)
    role, rfloor = tj.role_floor(a.strategy)

    pre_run_gate(a.strategy, a.purpose, SEARCH_START, SEARCH_END, mpd, rules, rfloor,
                 confirm_end=CONFIRM_END)

    lm, waiting = load_limits()
    if waiting:
        print("[歩4 本走] 走らせられない＝search_limits.json の値がまこさん待ち:")
        for w in waiting:
            print(f"  ・{w}")
        return 2
    # ★保有時間の上限の範囲は、戦略の役割から決める（監査 4-19／要件 R6・2026-08-03）。
    #   これを呼ばずに撒くと「範囲が解決されていません」で止まる（fail-closed＝黙って既定に倒れない）。
    lm = resolve_hold_range(lm, a.strategy)
    _lo, _hi = hold_bars(lm)
    print(f"[保有時間の上限の範囲] {_lo}〜{_hi} 本（1本＝5分＝{_lo * 5}〜{_hi * 5} 分）"
          f"＝役割 {lm['hold_role']} から決めた（設定 recipes/search_limits.json の hold_range_by_role が正本）")

    print(f"[戦略] {ad.NAME}: {ad.LABEL} ／ 宣言を借りるロジック {a.logic}: {known[a.logic].get('label', '')}")
    if a.purpose == ts.PURPOSE_SEARCH:
        print("[この走行の目的] search＝値を選ぶ。試した回数に数える"
              "（この窓で今後行う探索すべての合格の線が、その分だけ厳しくなる）")
    else:
        print("[この走行の目的] check＝道具が動くかを見る。試した回数に数えない（帳簿には残す）")
    print(f"[窓] 値決め {SEARCH_START.date()}〜{SEARCH_END.date()}（排他）／"
          f"確認 {CONFIRM_START.date()}〜{CONFIRM_END.date()}（排他・1回走らせて表示するだけ・選び直さない）"
          "＝periods.py が正本・採点窓は1バーも使わない")
    print(f"[側] {side} ／ [局面] {regime.get('name')}（入口の列 {regime.get('entry_col')}／止める列 {regime.get('block_col')}）")
    print(f"[役割] {a.strategy} = {role} ／ 役割から来る件数/日 の絶対下限 {rfloor}"
          f" ／ この回の探索で使う件数の下限 {mpd}")
    print(f"[終わりの条件の値] δ ${rules.get('delta_net')} ／ N_max {rules.get('n_max')} ／ "
          f"ATR%帯 {rules.get('atr_band_edges')}")
    if rules.get("n_max") and (a.trials1 + a.trials2) > rules["n_max"]:
        print(f"⚠️ 今回の試行 {a.trials1 + a.trials2:,} が宣言した上限 {rules['n_max']:,} を超えている"
              "＝合格の線を後出しで薄める形。上限を変えるなら設定ファイルを直してから回すこと。")

    t0 = time.time()
    df, df_c = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END), (CONFIRM_START, CONFIRM_END)],
                                      et.WARM, use_cache=not a.no_cache)
    print(f"[データ] 値決め窓 {len(df):,} バー ／ 確認窓 {len(df_c):,} バー（助走込み・{time.time() - t0:.0f}秒）")

    # ★土台＝いまの採用値を両窓で1回ずつ走らせた結果（B1・B2・B4 の比較相手）。
    #   無ければ判定表は「判定不能」と出るだけ（偽装の✅を出さない）。
    base = et._run_baseline(ad, df, df_c, a.logic, ad.exit_keys(), None)
    base_trades = base["search"]["t"] if base else None
    if base:
        print(f"[土台] {a.logic} の現行値＝値決め窓 net ${base['search']['total']:+,.0f}／{base['search']['n']:,}玉"
              f" ／ 確認窓 net ${base['confirm']['total']:+,.0f}／{base['confirm']['n']:,}玉")
    else:
        print("[土台] このロジックは採用値を持たない＝B1・B2・B4 は判定不能と出る（合格の印は出さない）")

    if a.resume:                                # R12＝途中で止まった走行の続きから
        run_dir = pathlib.Path(a.resume)
        if not run_dir.exists():
            raise SystemExit(f"[再開エラー] 記録の置き場が無い: {run_dir}")
        print(f"[再開] {run_dir} の記録を使う（同じ構造は走らせ直さない）")
    else:
        run_dir = GEN_RUNS / f"{a.tag or 'run'}_{time.strftime('%Y%m%d_%H%M%S')}"
        run_dir.mkdir(parents=True, exist_ok=True)
        print(f"[記録の置き場] {run_dir}（途中で止まってもここから続きを始められる＝R12）")

    pool, tfs, cat_total = material_pool()
    out = run_generation(df, limits=lm, judge=judge, start=SEARCH_START, end=SEARCH_END,
                         trials1=a.trials1, trials2=a.trials2, top_k=a.top_k, seed=a.seed,
                         run_dir=run_dir, pool=pool, tfs=tfs, catalog_total=cat_total,
                         side=side, regime=regime, base_trades=base_trades,
                         atr_edges=rules.get("atr_band_edges"), min_per_day=mpd,
                         net_floor=a.net_floor, purpose=a.purpose, tag=a.tag,
                         df_confirm=df_c, confirm_start=CONFIRM_START, confirm_end=CONFIRM_END,
                         base=base, rules=rules, rfloor=rfloor)
    print(f"\n[本走まとめ] 通った {out['kept']} 本 ／ 捨てた {out['dropped']} 本 ／ 再利用 {out['reused']} 本"
          f" ／ 結論 {out.get('verdict') or '（判定表を出していない）'} ／ 記録 {run_dir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="歩4 生成器＝構造をランダムに撒き（第1段）、有望構造の値を TPE で詰める（第2段）")
    ap.add_argument("--selftest", action="store_true", help="番人（合成データのみ・実データの試行ゼロ）")
    ap.add_argument("--dry-run", type=int, default=None, metavar="N",
                    help="構造を N 本撒いて内訳だけ機械出力（売買しない・データ不要・検収専用 limits）")
    # ── 本走（2026-08-05 新設・next_step §6.5 の13番・まこさん OK「OK」）────────────
    ap.add_argument("--run", action="store_true",
                    help="本走＝実データで構造を撒いて売買を回す（--purpose 必須・値決め窓のみ）")
    ap.add_argument("--strategy", default="e38", help="宣言の出どころの戦略（接続ファイル tuner_adapters/<名前>.py）")
    ap.add_argument("--logic", default="S2",
                    help="宣言を借りるロジック id。側・局面・件数の下限・ATR%%帯・δ・N_max・土台をここから機械で読む")
    ap.add_argument("--trials1", type=int, default=30, help="第1段＝ランダムに撒く本数（統計の土台）")
    ap.add_argument("--trials2", type=int, default=0, help="第2段＝TPE で値を詰める本数（統計判定に不使用）")
    ap.add_argument("--top-k", type=int, default=3, help="第2段へ送る有望構造の本数")
    ap.add_argument("--seed", type=int, default=1, help="撒き方の種（同じ種なら同じ構造が出る＝再現できる）")
    ap.add_argument("--purpose", default=None,
                    help="この走行の目的。search＝値を選ぶ（試した回数に数える）／check＝道具の動作確認"
                         "（数えない・帳簿に残る）。書き忘れは止める＝既定に黙って倒れない")
    ap.add_argument("--tag", default="", help="この走行の名前（記録の置き場と、確認の走行の帳簿の理由の欄に入る）")
    ap.add_argument("--net-floor", type=float, default=None,
                    help="合計 net の下限。値決め窓の合計 net がこれを下回った試行は捨てる（値はまこさん）")
    ap.add_argument("--resume", default=None, metavar="DIR",
                    help="途中で止まった走行の続きから始める（R12）。前の走行の記録の置き場を渡す")
    ap.add_argument("--no-cache", action="store_true", help="指標つきデータの使い回しをやめて毎回作り直す")
    a = ap.parse_args()
    if a.run:
        return run_main(a)
    if a.selftest:
        return selftest()
    if a.dry_run:
        pool, tfs, cat_total = material_pool()
        lm = dict(KENSHU_LIMITS)
        print("⚠️ 検収専用 limits（§11 の値はまこさん待ち＝この内訳は機械の検収であって探索ではない）")
        structs = []
        rejects = Counter()
        for i in range(a.dry_run * 5):
            if len(structs) >= a.dry_run:
                break
            rng = np.random.default_rng([1, 1, i])
            try:
                r = sample_structure(rng, lm, pool, tfs)
                ex.validate_recipe(r, limits={"p_max": lm["p_max"], "count_range": lm["count_range"],
                                              "role_max": lm["role_max"], "depth_max": lm["depth_max"],
                                              "k_max": lm["k_max"]})
                structs.append(r)
            except (SampleError, ex.RecipeError) as e:
                rejects[str(e)[:24]] += 1
        print(json.dumps(structure_breakdown(structs, cat_total), ensure_ascii=False, indent=1))
        print(f"[生成拒否] {json.dumps(dict(rejects), ensure_ascii=False)}")
        return 0
    lm, waiting = load_limits()
    if waiting:
        print("[歩4] 本走はまだ始められない＝search_limits.json の値がまこさん待ち:")
        for w in waiting:
            print(f"  ・{w}")
        print("→ 値が入り次第、windows（periods.py）と接続ファイルで本走する（採点窓は使わない）。")
        return 2
    # ★2026-08-05 に書き換えた。直す前はここに「本走の窓・接続・累積記録の実装は測定2 と同時
    #   （まこさんの実施判断待ち）」と出していたが、測定2 は 2026-08-04 に「やらない」で確定した
    #   ＝この一文はもう嘘だった。本走は --run で走る。
    print("[歩4] limits はそろっている。本走は --run で走らせる。例:")
    print("  python3 engine_tuner_gen.py --run --purpose check --trials1 3 --tag 動作確認")
    print("  （--purpose は必須。search＝値を選ぶ＝試した回数に数える／check＝動作確認＝数えない）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
