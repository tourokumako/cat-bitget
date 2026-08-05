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


def _pick_material(rng, pool, tfs, limits, role, seen_rolekind, kind_count) -> dict:
    """材料1本＝G3（同系統×同役割は1本・K_MAX）をサンプリング時から守る。"""
    for _ in range(30):
        r = rng.random()
        if role == "location" and r < 0.5:
            m = {"geo": str(rng.choice(["帯内位置%", "W%"]))}
        elif role == "env" and r < 0.10 and limits.get("hour_grid"):
            m = {"time": "時刻"}                  # 曜日の閾値格子は未定義＝時刻だけ（格子はまこさん §11-10）
        else:
            base = pool[int(rng.integers(len(pool)))]
            m = {"family": base["family"], "param": base["param"], "tf": str(rng.choice(tfs))}
        kind = _lineage_of(m)
        if role != "trigger" and (role, kind) in seen_rolekind:
            continue
        if limits.get("k_max") is not None and kind_count.get(kind, 0) >= limits["k_max"]:
            continue
        return m
    raise SampleError("材料を30回引いても G3 を満たせない")


def _pair_materials(rng, pool, tfs) -> list[dict]:
    """列2本の形（cross/diff/touch）＝同 family の期間違い、または Stoch%K と %D の対。"""
    fams = {}
    for b in pool:
        fams.setdefault(b["family"], []).append(b["param"])
    tf = str(rng.choice(tfs))
    if rng.random() < 0.4:
        ks = sorted(set(fams.get("Stoch%K", [])) & set(fams.get("Stoch%D", [])))
        if ks:
            p = int(rng.choice(ks))
            return [{"family": "Stoch%K", "param": p, "tf": tf},
                    {"family": "Stoch%D", "param": p, "tf": tf}]
    cands = [f for f, ps in fams.items() if len(set(ps)) >= 2]
    if not cands:
        raise SampleError("列2本の形を組める family が無い")
    f = str(rng.choice(cands))
    p1, p2 = rng.choice(sorted(set(fams[f])), size=2, replace=False)
    return [{"family": f, "param": int(p1), "tf": tf}, {"family": f, "param": int(p2), "tf": tf}]


def _q(rng, limits) -> dict:
    return {"threshold_q": str(rng.choice(limits["quantile_grid"]))}


def _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, allow_nest=True) -> dict:
    forms = TRIGGER_FORMS if role == "trigger" else STATE_FORMS
    form = str(rng.choice(forms))
    if form in ("streak", "within_n"):
        if not allow_nest:
            form = "level"
        else:
            inner = _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, allow_nest=False)
            inner.pop("role", None)
            inner["role"] = role
            n = int(rng.choice([n for n in limits["int_grid"] if n >= 2]))
            return {"role": role, "form": form, "inner": inner,
                    "value": {"n": n, "offset": int(rng.choice([0, 1]))}}
    if form in NEEDS_PAIR:
        mats = _pair_materials(rng, pool, tfs)
        for m in mats:
            kind_count[_lineage_of(m)] = kind_count.get(_lineage_of(m), 0) + 0  # 数えは下で一括
        if form == "cross":
            return {"role": role, "form": "cross", "material": mats,
                    "value": {"direction": str(rng.choice(["up", "down"]))}}
        if form == "diff":
            return {"role": role, "form": "diff", "material": mats,
                    "side": str(rng.choice(["above", "below"])), "value": _q(rng, limits)}
        return {"role": role, "form": "touch", "material": mats, "value": {"const": "TOL_SR"}}
    if form == "candle_dir":
        return {"role": role, "form": "candle_dir", "value": {"dir": str(rng.choice(["bull", "bear"]))}}
    m = _pick_material(rng, pool, tfs, limits, role, seen_rolekind, kind_count)
    if "time" in m:
        return {"role": role, "form": "level", "material": [m],
                "side": str(rng.choice(["above", "below"])),
                "value": {"n": int(rng.choice(limits["hour_grid"]))}}
    if form == "level":
        return {"role": role, "form": "level", "material": [m],
                "side": str(rng.choice(["above", "below"])), "value": _q(rng, limits)}
    if form in ("band", "band_exclude"):
        qs = rng.choice(limits["quantile_grid"], size=2, replace=False)
        lo, hi = sorted(qs, key=lambda s: int(str(s).lstrip("q")))
        return {"role": role, "form": form, "material": [m],
                "value": {"lo": {"threshold_q": str(lo)}, "hi": {"threshold_q": str(hi)}}}
    if form == "slope":
        return {"role": role, "form": "slope", "material": [m],
                "side": str(rng.choice(["above", "below"])),
                "value": {"n": int(rng.choice(limits["int_grid"]))}}
    if form == "slope_avg":
        return {"role": role, "form": "slope_avg", "material": [m],
                "side": str(rng.choice(["above", "below"])),
                "value": {"n": int(rng.choice(limits["int_grid"])), "m": int(rng.choice(limits["int_grid"]))}}
    raise SampleError(f"形 {form} の値の組み立てが未定義")


def _const100(x: float) -> dict:
    """欲しい実値 x を名前つき定数 FULL_100 × mult で表す（生の数字のフィールドを作らない・§2.4-②）。"""
    base = float(iref.CONST_REGISTRY["FULL_100"]["value"])
    return {"const": "FULL_100", "mult": float(x) / base}


def _make_exits(rng, limits) -> list[dict]:
    """出口の枝＝SL 必須（G4）＋TP（zone mid）＋確率で TP1（mix）＋TIME。並び順もランダム＝順番はデータ。

    exit_mult_grid・frac_grid は％表記（50.0＝0.5）＝格子の値はまこさん（§11-10 に準ずる）。
    """
    exits = [
        {"name": "SL", "reason": "SL_FILLED",
         "exec": {"method": "maker", "placement": {"kind": "resting", "fill": "adverse", "pessimistic": True,
                                                   "level": {"kind": "zone_sl",
                                                             "k": _const100(float(rng.choice(limits["exit_mult_grid"])) / 100.0)}}},
         "size_ratio": 1.0},
        {"name": "TP2", "reason": "TP_FILLED",
         "exec": {"method": "maker", "placement": {"kind": "resting", "fill": "profit",
                                                   "level": {"kind": "zone", "target": "mid"}}},
         "size_ratio": 1.0},
        {"name": "TIME", "reason": "TIME_EXIT",
         "fire": {"all": [{"role": "env", "form": "level", "side": "above",
                           "material": [{"state": "hold_min"}],
                           # 監査 4-19／要件 R6＝メニューから選ぶのをやめ、役割から決めた整数の範囲から引く。
                           # 単位は分。5分足なので必ず5の倍数になる（本数 × 5）。
                           "value": {"n": int(rng.integers(hold_bars(limits)[0],
                                                           hold_bars(limits)[1] + 1)) * 5}}]},
         "exec": {"method": "taker", "placement": {"kind": "on_close"}},
         "size_ratio": 1.0},
    ]
    if rng.random() < 0.5:
        frac = float(rng.choice(limits["frac_grid"])) / 100.0
        exits.append({"name": "TP1", "reason": "PARTIAL_TP", "once": True,
                      "exec": {"method": "maker",
                               "placement": {"kind": "resting", "fill": "profit",
                                             "level": {"kind": "mix", "from": "entry", "to": "TP2",
                                                       "frac": _const100(frac)}}},
                      "size_ratio": frac})
    if rng.random() < 0.3:
        exits[2]["exec"]["be_wait"] = {"level": {"kind": "pct", "base": "avg",
                                                 "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}},
                                       "ttl": {"const": "BE_TTL_BARS"}}
    order = rng.permutation(len(exits))
    return [exits[i] for i in order]


def default_regime() -> dict:
    """既定の相場の宣言＝接続ファイル e38 が設定ファイルから読んだもの（監査 4-19／要件 R5）。

    ★道具の中に列の名前を書かないため、接続ファイルに聞きます。
      列の名前を道具に書いてしまうと、レンジ以外の相場を指定できなくなります（それが 4-19 の指摘でした）。
    """
    from tuner_adapters import e38 as _e38
    return _e38.regime("S2")


def sample_structure(rng, limits, pool, tfs, side="SHORT", regime=None, logic_id="GEN") -> dict:
    """構造1本＝役割構成・本数・つなぎ方・形・材料・出口の枝・玉の持ち方 をランダムに組む。"""
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

    trig = _make_cond(rng, "trigger", limits, pool, tfs, seen_rolekind, kind_count)
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
                c = _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count)
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
    return {
        "meta": {"strategy": "e38", "logic_id": logic_id, "side": side,
                 "regime": dict(regime if regime is not None else default_regime())},
        "pre_filter": [],
        "entry": {"connective": tree},
        "exits": _make_exits(rng, limits),
        "position": {"mode": str(rng.choice(["separate", "avg"])),
                     "max_adds": int(rng.choice(limits["max_adds_grid"])),
                     **({"add_trigger": {"kind": "resignal"}}
                        if True else {})},
    }


def recipe_hash(recipe: dict) -> str:
    return hashlib.sha256(json.dumps(recipe, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


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
        for c in conds + list(r.get("pre_filter", [])):
            _cond_keys(c, lane)
    return keys


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

    # ── 材料の組み立てと解決表（探索開始時に1回固定・§5-4）──
    df2 = attach_materials(df, structures)
    geo = {"res_hi": df2["v11_res_hi"].to_numpy(float), "res_lo": df2["v11_res_lo"].to_numpy(float),
           "sup_hi": df2["v11_sup_hi"].to_numpy(float), "sup_lo": df2["v11_sup_lo"].to_numpy(float),
           "mid": df2["v11_mid"].to_numpy(float)}
    c = df2["close"].to_numpy(float)
    span = geo["res_hi"] - geo["mid"]
    with np.errstate(invalid="ignore", divide="ignore"):
        geo["帯内位置%"] = np.where(np.isfinite(span) & (span > 0), (c - geo["mid"]) / span, np.nan)
        geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),
                             (geo["res_hi"] - geo["sup_lo"]) / c * 100.0, np.nan)
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
        ok, why = True, ""
        if min_per_day is not None and res["per_day"] < min_per_day:
            ok, why = False, f"件数の下限 {min_per_day} に対して {res['per_day']:.2f}件/日"
        elif net_floor is not None and res["total"] < net_floor:
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
                ok, why = True, ""
                if min_per_day is not None and res["per_day"] < min_per_day:
                    ok, why = False, "件数の下限"
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
