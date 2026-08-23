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
import re
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
# ★cross_val（2026-08-13・段C の C-6・部品①）は実行器の形ではない。実行器では cross の
#   「列1本 ＋ 閾値」の書き方（＝『RSI が 70 を上抜けた』）を指す、生成器の中だけの名前。
#   引き金（縁）だけに置く＝水準を跨いだ瞬間の1バーで成立する形のため。
# ★M2-2-3b（2026-08-21 まこさん承認 e4b86277…）＝下の3つは、手で並べるのをやめて
#   形の性質表（engine_tuner_exec.FORM_SPEC）から作る。直す前は手書きで、形を足すたびに
#   入れ忘れの危険があった（next_step §6 の66番）。
#
# ★★並びの「順番」は直す前のまま残す（大事）。
#   理由＝`_make_cond` が `rng.choice(forms)` で上から選ぶ＝順番が変わると、同じ種でも
#   違う案が出る（＝過去の探索をやり直せない）。2026-08-16 に同じ型の事故が起きている
#   （set を上から順に見ていて、走らせるたびに案が変わった・worklog 20260816 の §4）。
#   ★最初、性質表の順番（FORMS の順）で作ったら、実際に順番が変わっていた。使われ方を
#     読んで気づいたので、順番を保つ形に直した。
#
# ★では何が良くなったか＝**中身（どの形が入るか）は性質表から作る。**
#   順番の一覧と中身がずれたら、読み込みの瞬間に止まる（fail-closed）＝入れ忘れが
#   「黙って通る」から「必ず止まる」に変わった。
_TRIGGER_ORDER = ("cross", "cross_val", "level", "diff", "candle_dir", "slope", "streak",
                  "within_n", "barssince")
_STATE_ORDER = ("level", "band", "band_exclude", "slope", "slope_avg", "diff", "touch",
                "candle_dir", "streak", "within_n", "barssince", "hysteresis")
# ★hysteresis（状態を保つ形）を末尾に足した（M2-2-5・2026-08-21 まこさん承認 24a453d6…）。
#   ★末尾にした理由＝既存の形の並びの順番を1つも動かさないため（順番が変わると同じ種から違う案が出る）。
#   ★引き金の並び（_TRIGGER_ORDER）には足さない＝縁で発火する形ではないため（FORM_SPEC の trigger_ok=False）。


def _ordered_like(order: tuple, members: tuple, name: str) -> tuple:
    """中身は性質表から・順番は order のまま。ずれたら止める（M2-2-3b）。"""
    if set(order) != set(members):
        raise SystemExit(
            f"[{name}] 形の性質表と、並びの順番の一覧がずれています（engine_tuner_gen.py）。\n"
            f"  性質表にだけ在る: {sorted(set(members) - set(order))}\n"
            f"  順番の一覧にだけ在る: {sorted(set(order) - set(members))}\n"
            f"  ★形を足したときは、engine_tuner_exec.FORM_SPEC と、この順番の一覧の両方に足す。\n"
            f"  ★順番は案の中身を左右するので、機械では決められません（どこに入れるかは人が決める）。")
    return tuple(order)


TRIGGER_FORMS = _ordered_like(_TRIGGER_ORDER, ex.forms_where("trigger_ok") + ("cross_val",),
                              "TRIGGER_FORMS")
STATE_FORMS = _ordered_like(_STATE_ORDER, ex.forms_where("state_free"), "STATE_FORMS")
NEEDS_PAIR = ex.forms_pair_in("2", "2or1th")     # ★順番は効かない（in で見るだけ）

# §11 の対応（値待ちの可視化に使う・番号は設計書 §11）
LIMIT_LABELS = {
    "n_min": "N_MIN（補正後独立標本数の下限・§11-1）",
    "r_min": "R_MIN（リスクリワード比の下限・§11-2）",
    "role_max": "E_MAX/S_MAX/L_MAX（役割ごとの本数上限・§11-3）",
    "count_range": "条件の合計本数の範囲（§11-4）",
    "k_max": "K_MAX（同系統のレシピ全体での上限・§11-5）",
    # ★2026-08-15（段A の A-5-3）＝分位も「決まった段だけ」から「範囲」に変えた
    "quantile_range": "閾値の段（分位）の範囲（§11-6）",
    "quantile_grid": "分位の格子（§11-6・ほかの道具がまだ読む）",
    "depth_max": "木の深さ上限（§11-7）",
    "p_max": "P_MAX（発火経路数の上限・§11-8）",
    # ★2026-08-15（段A の A-5-2）＝下の9つを「決まった数字だけ」から「範囲」に変えた（鍵の名前も変えた）
    "state_mult_range": "状態列の定数倍数 k の範囲（§11-9）",
    "int_range": "使い方の中の本数の範囲（§11-10）",
    "int_grid": "整数グリッド＝lookback・N（§11-10・ほかの道具がまだ読む）",
    "hold_range_by_role": "保有時間の上限の範囲（役割ごと・5分足の本数・監査 4-19／要件 R6）",
    "hour_range": "時刻の閾値の範囲（§11-10）",
    "frac_range": "段階決済 mix の比率の範囲（§11-10 に準ずる）",
    "exit_mult_range": "SL 幾何 k の倍率の範囲（§11-10 に準ずる）",
    "max_adds_range": "max_adds の範囲（§11-10 に準ずる）",
    "hold_frac_range": "保有の門＝満期に対する割合の範囲（D2 出口の枝）",
    "giveback_range": "含み益のピークから戻す割合の範囲（D2 出口の枝）",
    "loss_cap_range": "1トレードの最大許容損失の範囲（D2 出口の枝）",
    "ladder_steps_range": "部分利確の段数の範囲（D2 出口の枝）",
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

    ★2026-08-11（段6 の 6-7）に、数え方を変えた。理由を残す。
      前は実行器の手書きの型（19件）を正規表現に直して、カタログの列名に当てていた。
      ＝手書きの表に載っていない指標は、カタログに列が在っても候補に載らなかった
      （2026-08-09 実測＝232種類が落ちていた。MACD・BB%b・一目・ローソク足の形 ほか）。
      いまは逆向きに数える＝カタログの列名を1つずつ参照表で family と数字に分解する。
      ＝カタログに在る列は全部 候補に載る（実行器の G6 も同じ参照表から名前を組み立てる）。

    数字の持ち方は3つ＝①数字1つ（RSI14 → 14）②数字の並び（MACD線%(12,26) → (12, 26)）
    ③無し（包み足 → None）。カタログ総列数は網羅度の分母。
    """
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import observe_diag as od
        cfg = cfg or od.load_config()
        names = [name for name, _fn, _d in od.build_catalog(cfg)]
    pool = []
    for nm in names:
        ent, prm = iref.find(nm)
        if ent is None or ent["family"] not in ex.FAMILY_TEMPLATES:
            continue
        p = None if len(prm) == 0 else (prm[0] if len(prm) == 1 else tuple(prm))
        pool.append({"family": ent["family"], "param": p})
    tfs = list(cfg["timeframes"])
    return pool, tfs, len(names) * len(tfs)


# ══ 材料のパラメータの「範囲」（段A の A-4・2026-08-13）════════════════════════════════════
_RANGES: dict | None = None


def material_ranges(cfg: dict | None = None, limits: dict | None = None) -> dict:
    """指標の種類ごとに「パラメータの範囲」を作る（点の一覧でなく、下限と上限の間の全部）。

    ★なぜ要るか＝直す前は、engine_tuner が試せる数字が設定ファイル observe_config.json に
      並んでいる数字だけだった（RSI なら 7・9・14・21 の4つ。RSI12 は何回 引いても出ない）。
      要件の「作ってはいけないもの」2番＝探す値を CC が先に「点の一覧」で限定するもの、に当たる。

    ★範囲の数字を CC は作らない（ここが一番 大事）。
      下限＝いま材料カタログに在る数字の最小。上限＝同じく最大。**新しい数字を1つも足していない。**
      ＝RSI なら 7〜21 の整数が全部 試せる（12 も 13 も 20 も出る）。カタログの4つは全部この中に入る。
      **上限を広げる（例＝RSI を 200 まで）かどうかは、まこさんが決めることです。**
      決まったら、下の「まこさんが決めた範囲」に書けば、そちらが優先されます（CC は書きません）。

    ★まこさんが決めた範囲の置き場所＝recipes/search_limits.json の material_param_ranges。
      形＝{"RSI": [{"kind": "int", "lo": 30, "hi": 50}]}（軸＝名前の {} の数だけ並べる）。
      出どころ＝まこさんの逐語（2026-08-07・engine_tuner_defects.md の D14 ⑥）
      「疑似シミュで出た値の前後あたりで範囲を事前に指定して（例えば３０〜５０の間とか）探す」。
      **いまは空です。**空のあいだは、上のカタログ由来の範囲を使います。

    戻り＝{指標の種類: {"axes": [{"kind": "int"|"float", "lo": x, "hi": y, "dec": 小数の桁数}, ...],
                        "src": "catalog"|"makosan"}}

    ★正直に書く限界＝軸どうしの関係（MACD の 短い方 < 長い方 のような決まり）は、この表に持っていません。
      いまはカタログ由来＝どの軸も1点なので問題は出ません。まこさんが範囲を広げるときに、
      その決まりが要るかを1件ずつ決めます。
    """
    global _RANGES
    default_call = cfg is None and limits is None      # 引数なしの呼び出しだけ 覚えておく（使い回す）
    if _RANGES is not None and default_call:
        return _RANGES
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import observe_diag as od
        cfg = cfg or od.load_config()
        names = [name for name, _fn, _d in od.build_catalog(cfg)]
    seen: dict[str, list[list]] = {}
    for nm in names:
        ent, prm = iref.find(nm)
        if ent is None:
            continue
        fam = ent["family"]
        axes = seen.setdefault(fam, [[] for _ in range(len(prm))])
        if len(axes) != len(prm):                     # 同じ指標で数字の個数が違う＝表の作りが崩れている
            raise SystemExit(f"[範囲エラー] {fam} の数字の個数がカタログの中でそろっていない"
                             f"（{len(axes)} 個 と {len(prm)} 個）")
        for i, v in enumerate(prm):
            axes[i].append(v)
    out: dict[str, dict] = {}
    for fam, axes in seen.items():
        spec = []
        for vals in axes:
            is_int = all(float(v).is_integer() and not isinstance(v, float) for v in vals)
            dec = max((len(str(v).split(".")[1]) if "." in str(v) else 0) for v in vals)
            spec.append({"kind": "int" if is_int else "float",
                         "lo": min(vals), "hi": max(vals), "dec": int(dec)})
        out[fam] = {"axes": spec, "src": "catalog"}
    # ── まこさんが決めた範囲が在れば、そちらを使う（CC は数字を書かない）──
    if limits is None:
        limits, _w = load_limits()
    for fam, axes in (limits.get("material_param_ranges") or {}).items():
        if fam not in out:
            raise SystemExit(f"[範囲エラー] material_param_ranges に、カタログに無い指標の種類: {fam}")
        if len(axes) != len(out[fam]["axes"]):
            raise SystemExit(f"[範囲エラー] {fam} の軸の数が合わない"
                             f"（カタログ {len(out[fam]['axes'])} 個 ／ 設定 {len(axes)} 個）")
        out[fam] = {"axes": [dict(a) for a in axes], "src": "makosan"}
    if default_call:
        _RANGES = out
    return out


def param_in_range(fam: str, param, ranges: dict | None = None) -> tuple[bool, str]:
    """この数字は、その指標の範囲の中か（検証器の番人が呼ぶ）。戻り＝(入っているか, 理由)。"""
    ranges = ranges if ranges is not None else material_ranges()
    spec = ranges.get(fam)
    if spec is None:
        return True, ""                                # カタログに無い指標＝別の関門（G6）が見る
    vals = [] if param is None else (list(param) if isinstance(param, (list, tuple)) else [param])
    if len(vals) != len(spec["axes"]):
        return False, f"{fam} の数字の個数が範囲の表と合わない（{len(vals)} 個 ／ 表は {len(spec['axes'])} 個）"
    for i, (v, ax) in enumerate(zip(vals, spec["axes"])):
        if float(v) < float(ax["lo"]) or float(v) > float(ax["hi"]):
            return False, (f"{fam} の {i + 1} 番目の数字 {v} が範囲の外"
                           f"（{ax['lo']}〜{ax['hi']}・出どころ＝{spec['src']}）")
        if ax["kind"] == "int" and float(v) != int(v):
            return False, f"{fam} の {i + 1} 番目の数字 {v} は整数でない（範囲の表は整数）"
    return True, ""


def draw_param(rng, fam: str, ranges: dict | None = None):
    """その指標のパラメータを1組 引く（範囲の中の、どの数字でもよい）。

    ★点の一覧から選ぶのではありません。下限と上限の間から引きます。
    ★小数の桁数は、カタログに在る数字の桁数に合わせます（CC が桁数を決めない）。
    """
    ranges = ranges if ranges is not None else material_ranges()
    spec = ranges.get(fam)
    if spec is None or not spec["axes"]:
        return None
    vals = []
    for ax in spec["axes"]:
        if ax["kind"] == "int":
            vals.append(int(rng.integers(int(ax["lo"]), int(ax["hi"]) + 1)))
        else:
            v = float(rng.uniform(float(ax["lo"]), float(ax["hi"])))
            vals.append(round(v, int(ax["dec"])) if ax["dec"] else float(round(v)))
    return vals[0] if len(vals) == 1 else tuple(vals)


def int_range_of(limits: dict, n_min: int = 1) -> tuple[int, int]:
    """使い方の中の本数（傾きを何本で見るか・何本 続いたか・何本 以内か）の範囲（段A の A-5・2026-08-13）。

    ★直す前＝`int_grid` の 3・6・12・24 の**4つだけ**。一覧に無い本数（5本・7本・19本）は
      何回 試しても出てこなかった（要件の「作ってはいけないもの」2番に当たる状態）。
    ★直したあと＝下限と上限の間の整数を全部 試せる。
    ★範囲の数字を CC は作っていません＝両端は `int_grid` の最小（3）と最大（24）です。
      まこさんが決めた範囲が `int_range` に在れば、そちらを使います。
    ★n_min＝形によって「2本 以上」しか意味を持たないものが在る（連続・以内・相関の窓）。
      その形では下限を 2 に引き上げます（直す前も `if n >= 2` で同じことをしていた）。
    """
    r = limits.get("int_range")
    if isinstance(r, dict) and r.get("lo") is not None and r.get("hi") is not None:
        lo, hi = int(r["lo"]), int(r["hi"])
    else:
        g = limits.get("int_grid")
        if not g:
            raise SystemExit("[本数の範囲エラー] int_range も int_grid も無い（recipes/search_limits.json）")
        lo, hi = int(min(g)), int(max(g))
    lo = max(lo, int(n_min))
    if hi < lo:
        raise SystemExit(f"[本数の範囲エラー] 上限 {hi} が下限 {lo} より小さい（n_min={n_min}）")
    return lo, hi


def draw_int(rng, limits: dict, n_min: int = 1) -> int:
    """使い方の中の本数を1つ 引く（範囲の中の、どの整数でもよい）。"""
    lo, hi = int_range_of(limits, n_min)
    return int(rng.integers(lo, hi + 1))


# ══ 出口の枝などで使う数字の範囲（段A の A-5-2・2026-08-15）══════════════════════════
#   直す前は、下の9つが「決まった数字だけ」の一覧でした。
#     state_mult_grid ／ exit_mult_grid ／ frac_grid ／ giveback_grid ／ hold_frac_grid ／
#     loss_cap_grid ／ hour_grid ／ max_adds_grid ／ ladder_steps_grid
#   例＝`state_mult_grid` は 1.0・1.5・2.0・3.0 の4つだけ。手数料床の 1.2倍 は何回 試しても
#   出てきません。要件の「作ってはいけないもの」2番（探す値を CC が先に点の一覧で限定する）に
#   当たる状態でした。いまは下限と上限の間から引きます。
#   ★両端の数字を CC は1つも作っていません＝直す前の一覧の 最小 と 最大 です。
def num_range_of(limits: dict, key: str) -> dict:
    """範囲を読む。戻り＝{"lo": 下限, "hi": 上限, "kind": "int" か "float", "dec": 小数の桁数}。

    ★fail-closed＝範囲も、直す前の一覧も無ければ止めます（黙って別の数字を使いません）。
    ★直す前の一覧（`*_grid`）が設定ファイルに残っている間は、その最小と最大を範囲にします
      ＝まこさんが元に戻したくなったときに、設定ファイルだけで戻せます。
    """
    spec = limits.get(key)
    if isinstance(spec, dict) and spec.get("lo") is not None and spec.get("hi") is not None:
        lo, hi = float(spec["lo"]), float(spec["hi"])
        kind = str(spec.get("kind") or ("int" if lo.is_integer() and hi.is_integer() else "float"))
        dec = int(spec.get("dec") or 0)
    else:
        old = key[: -len("_range")] + "_grid" if key.endswith("_range") else key
        g = limits.get(old)
        if not g:
            raise SystemExit(f"[範囲エラー] {key} も {old} も無い（recipes/search_limits.json）")
        lo, hi = float(min(g)), float(max(g))
        kind = "int" if all(float(v).is_integer() for v in g) else "float"
        dec = max((len(str(v).split(".")[1]) if "." in str(v) else 0) for v in g)
    if hi < lo:
        raise SystemExit(f"[範囲エラー] {key} の上限 {hi} が下限 {lo} より小さい（recipes/search_limits.json）")
    return {"lo": lo, "hi": hi, "kind": kind, "dec": int(dec)}


def draw_num(rng, limits: dict, key: str, lo_min=None, hi_max=None):
    """その範囲から数字を1つ 引く（範囲の中の、どの数字でもよい）。

    lo_min・hi_max＝呼ぶ側の事情でさらに狭めるとき（例＝積み増した玉だけに当たる損切りは、
    2回目 以上、かつ その案の積み増し回数 以下）。**設定ファイルの範囲そのものは書き換えません。**
    """
    r = num_range_of(limits, key)
    lo, hi = r["lo"], r["hi"]
    if lo_min is not None:
        lo = max(lo, float(lo_min))
    if hi_max is not None:
        hi = min(hi, float(hi_max))
    if hi < lo:
        raise SystemExit(f"[範囲エラー] {key} を {lo_min}〜{hi_max} で狭めたら範囲が空になった")
    if r["kind"] == "int":
        return int(rng.integers(int(lo), int(hi) + 1))
    v = float(rng.uniform(lo, hi))
    return round(v, r["dec"]) if r["dec"] else float(round(v))


def ladder_min_frac() -> float:
    """部分利確の1回で決済できる、いちばん小さい割合（玉1つに対する割合）。

    ★数字を CC は作っていません＝取引所の最小注文サイズ（`eval_engine.MIN_ORDER_BTC`＝0.0001 BTC・
      出どころは `exchange_spec.md` の audit#19）を、玉1つの量（`engine_tuner_exec.UNIT_LOT`）で割った値です。
    """
    import eval_engine as _ee
    return float(_ee.MIN_ORDER_BTC) / float(ex.UNIT_LOT)


def max_ladder_steps(limits: dict) -> int:
    """どの割合を引いても最小注文サイズを割らない、部分利確の最大の段数。

    ★数字を CC は作っていません。次の3つから機械で出します。
      ①取引所の最小注文サイズ ②玉1つの量 ③各段の割合の上限（`frac_range` の hi）。
    ★実行器は「**いま残っている量** × その段の割合」を決済します（2026-08-15 に実測で確認）。
      ですから、いちばん厳しいのは「毎回 いちばん大きい割合を引いたとき」＝残りがいちばん速く小さくなる場合です。
    ★2026-08-15 の実測＝玉 0.012 BTC・割合の上限 75% のとき **3段**。
    """
    mf = ladder_min_frac()
    keep = 1.0 - float(num_range_of(limits, "frac_range")["hi"]) / 100.0   # 1段ごとに残る割合（最悪の場合）
    n, rest = 0, 1.0
    while keep > 0 and rest * keep >= mf:
        rest *= keep
        n += 1
    return max(1, n)


# ══ 閾値の段（分位）の範囲（段A の A-5-3・2026-08-15）════════════════════════════════
#   直す前は `quantile_grid` の 10・20・30・40・50・60・70・80・90 の **9段だけ**でした。
#   RSI の 65%点・35%点 は、何回 試しても出てきません（要件の「作ってはいけないもの」2番）。
#   ★両端の数字を CC は作っていません＝直す前の一覧の 最小（q10）と 最大（q90）です。
def q_range_of(limits: dict, lo_min=None, hi_max=None) -> tuple[int, int]:
    """分位の範囲（何%点から何%点まで）。戻り＝(下限, 上限) の整数。

    ★まこさんが決めた範囲が `quantile_range` に在れば、それを使います。
      無ければ、直す前の一覧 `quantile_grid` の最小と最大を範囲にします
      （＝設定ファイルだけで元に戻せる。`int_range`／`*_range` と同じ扱い）。
    ★lo_min・hi_max＝呼ぶ側の事情でさらに狭めるとき（例＝DC2 の高分位）。
      **設定ファイルの範囲そのものは書き換えません。**
    """
    r = limits.get("quantile_range")
    if isinstance(r, dict) and r.get("lo") is not None and r.get("hi") is not None:
        lo, hi = int(r["lo"]), int(r["hi"])
    else:
        g = limits.get("quantile_grid")
        if not g:
            raise SystemExit("[分位の範囲エラー] quantile_range も quantile_grid も無い"
                             "（recipes/search_limits.json）")
        nums = [int(str(q).lstrip("q")) for q in g]
        lo, hi = min(nums), max(nums)
    if lo_min is not None:
        lo = max(lo, int(lo_min))
    if hi_max is not None:
        hi = min(hi, int(hi_max))
    if hi < lo:
        raise SystemExit(f"[分位の範囲エラー] 上限 {hi} が下限 {lo} より小さい"
                         f"（recipes/search_limits.json の quantile_range）")
    return lo, hi


def quantile_list(limits: dict) -> list[str]:
    """解決表（分位 → 実値）を作るときに要る分位の全部（範囲の中の整数を全部）。

    ★解決表は「値決め窓の分布から1回だけ固定する」もの（§2.4-①）なので、
      引く前に、範囲の中のどの分位でも引けるように作っておきます。
    """
    lo, hi = q_range_of(limits)
    return [f"q{i}" for i in range(lo, hi + 1)]


def draw_q(rng, limits: dict, lo_min=None, hi_max=None) -> str:
    """分位を1つ 引く（範囲の中の、どの整数でもよい）。戻り＝"q37" の形。"""
    lo, hi = q_range_of(limits, lo_min, hi_max)
    return f"q{int(rng.integers(lo, hi + 1))}"


def q_in_range(limits: dict, q) -> tuple[bool, str]:
    """その分位は範囲の中か（検証器の番人が呼ぶ）。戻り＝(入っているか, 理由)。"""
    s = str(q)
    if not s.startswith("q") or not s[1:].isdigit():
        return False, (f"分位 {q!r} の書き方が違う（q と整数＝例 q37・"
                       "recipes/search_limits.json の quantile_range）")
    lo, hi = q_range_of(limits)
    n = int(s[1:])
    if n < lo or n > hi:
        return False, (f"分位 {s} が探せる範囲の外（q{lo}〜q{hi}・"
                       "recipes/search_limits.json の quantile_range）")
    return True, ""


def num_in_range(limits: dict, key: str, v) -> tuple[bool, str]:
    """その数字は範囲の中か（検証器の番人が呼ぶ）。戻り＝(入っているか, 理由)。"""
    r = num_range_of(limits, key)
    if float(v) < r["lo"] or float(v) > r["hi"]:
        return False, (f"{key} の値 {v} が探せる範囲の外"
                       f"（{r['lo']}〜{r['hi']}・recipes/search_limits.json の {key}）")
    if r["kind"] == "int" and float(v) != int(v):
        return False, f"{key} の値 {v} は整数でない（範囲は整数・recipes/search_limits.json の {key}）"
    return True, ""


def _pool_families(pool: list[dict]) -> list[str]:
    """候補に載っている指標の種類（重複を除く・並びは決定論）。"""
    return sorted({b["family"] for b in pool})


_POOL_LINEAGE_MEMO: dict = {}


def _pool_families_by_lineage(pool: list[dict]) -> dict:
    """候補の指標の種類を、系統（オシレーター・トレンド…）で仕分けした表。

    ★2026-08-13（段A の A-4）に足した。**引く中身は変えていない。空振りを減らすだけ。**
      直す前は 535件の候補から1件 引いて、役割に使えない系統だったら引き直していた
      （実測＝1回 引き当てるのに平均41回 空振り）。いまは役割に使える系統の中から引く
      ＝同じものが同じ割合で出て、空振りだけが無くなる。
    """
    key = id(pool)
    hit = _POOL_LINEAGE_MEMO.get(key)
    if hit is None or hit[0] is not pool:
        by: dict[str, list[str]] = {}
        for b in pool:
            by.setdefault(iref.FAMILY_LINEAGE[b["family"]]["k"], []).append(b["family"])
        _POOL_LINEAGE_MEMO.clear()
        _POOL_LINEAGE_MEMO[key] = (pool, by)
        hit = _POOL_LINEAGE_MEMO[key]
    return hit[1]


def _as_param_list(p) -> list:
    """数字の3通り（1つ／並び／無し）を、並びの形にそろえる。"""
    if p is None:
        return []
    return list(p) if isinstance(p, (list, tuple)) else [p]


def _from_param_list(vals: list):
    """並びの形を、もとの3通りに戻す。"""
    if not vals:
        return None
    return vals[0] if len(vals) == 1 else tuple(vals)


def _range_has_two(fam: str, ranges: dict | None = None) -> bool:
    """その指標の範囲は、違う数字を2つ 持てるか（同じ指標のパラメータ違い2本＝クロスが作れるか）。"""
    ranges = ranges if ranges is not None else material_ranges()
    spec = ranges.get(fam)
    if spec is None or not spec["axes"]:
        return False
    return any(float(ax["hi"]) > float(ax["lo"]) for ax in spec["axes"])


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
    name = ex.build_name(m)
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
        # ★2026-08-16＝lineages を set から「並びの決まったもの」に変えた。
        #   直す前＝set。Python は走らせるたびに文字列の置き場所を変えるので、set を上から
        #   順に見たときの並びが、同じコマンドでも実行のたびに違った（`_make_cond` の
        #   `for k in rr["lineages"]` が候補の並びを作っている）。
        #   ＝同じ種（seed）を渡しても、走らせるたびに違う案が出ていた（再現できない）。
        #   実測 2026-08-16＝案20本を作り、PYTHONHASHSEED を 0・1・2 に変えて比べたら3通りとも別物。
        #   並びを名前順に固定したら3通りとも同じ md5 になった。
        #   ★ほかの使い方（`in` で入っているかを見るだけ）は、並びの決まったものでも同じ結果。
        roles[rname] = {"lineages": tuple(sorted(r["lineages"])),
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


_SCENE_RULES = None


def load_scene_rules() -> list:
    """場面ごとの決まり K-1〜K-7 を完成品（composition_rules.json）から読む（M2-4-2・2026-08-22 まこさん承認）。

    ★照合の実体は engine_tuner_exec の G7（_check_scene_rules）＝満たさない束を拒否する。
      生成の側は M2-5（レンジを組み立てる）で、この一覧を見て決まりを満たす束だけを組む。
      ここは読む口だけ（読めなければ止める＝fail-closed・場所は gen_composition_rules の出力に追従）。
    """
    global _SCENE_RULES
    if _SCENE_RULES is None:
        import gen_composition_rules as gcr
        if not gcr.out_json.exists():
            raise SystemExit("[場面ごとの決まり] composition_rules.json が無い"
                             "（gen_composition_rules.py --write で作る・fail-closed）")
        body = json.loads(gcr.out_json.read_text(encoding="utf-8"))["body"]
        rules = body.get("scene_rules")
        if not rules:
            raise SystemExit("[場面ごとの決まり] composition_rules.json に scene_rules が無い"
                             "（gen_composition_rules.py --write で作り直す・fail-closed）")
        _SCENE_RULES = list(rules)
    return _SCENE_RULES


# ══ 材料の順位を読む（M2-3-4・2026-08-22 まこさん承認・acceptance 086a13df606d…）════════════════
#   正本＝.claude/ratchet/material_ranking.json（observe_diag --rank-regime が値決め窓だけで作った成績表）。
#   使い方＝M2-5（レンジの束を組む）で、役割ごとの材料を「場面を分ける力」の上位 K 列に絞る。
#   ★上位 K は engine_tuner が探す値（まこさん承認済みの基準・worklog 20260822 §2）＝
#     下限1・上限＝その役割の載った全列数（＝絞らない状態も選べる）。数字は設定ファイルに書かない。
#   ★パラメータ違い（ATR%7／14／21 など）は別々の列として順位に並ぶ＝良いパラメータの列が自然に上へ来る。
#   ★成績表に無い列は、順位からは引けない（fail-closed）。

_MATERIAL_RANKING = None
_RANK_PATH = pathlib.Path(__file__).resolve().parent.parent.parent / ".claude" / "ratchet" / "material_ranking.json"


def load_material_ranking() -> dict:
    """材料の成績表を読む。無ければ止まる（fail-closed）。"""
    global _MATERIAL_RANKING
    if _MATERIAL_RANKING is None:
        if not _RANK_PATH.exists():
            raise SystemExit("[材料の順位] material_ranking.json が無い"
                             "（observe_diag.py --rank-regime で作る・fail-closed・M2-3-4）")
        d = json.loads(_RANK_PATH.read_text(encoding="utf-8"))
        if not d.get("順位"):
            raise SystemExit("[材料の順位] 順位が空（--rank-regime で作り直す・fail-closed）")
        _MATERIAL_RANKING = d
    return _MATERIAL_RANKING


def ranked_materials(role: str, label: str | None = None) -> list[tuple[str, float, str, str]]:
    """役割の材料を「場面を分ける力」の降順に並べた1本の一覧（M2-5 の B・2026-08-23 まこさん承認 327e7f80008f…）。

    戻り＝[(列名, 分離力, ラベル, 先読み), ...]。ラベル（強さ・向き・大きさ）× 先読み（24・288）を全部 混ぜて
    |分離力−0.5| の降順に並べる。label を指定したら、そのラベルだけ。
    ★K（上位 K 列の中から乱数で1本）は 2026-08-23 に無くした＝まこさん決定「成績表の1位から順に使う」。
      前の「上位 K」の基準（49回目・2026-08-22）は、この関数で置き換えた。数字（K）を持たない。
    """
    d = load_material_ranking()["順位"]
    if role not in d:
        raise SystemExit(f"[材料の順位] 成績表に役割 {role} が無い（在る役割＝{sorted(d)}・fail-closed）")
    labels = [str(label)] if label is not None else sorted(d[role])
    rows = []
    for lab in labels:
        if lab not in d[role]:
            raise SystemExit(f"[材料の順位] 成績表に {role}/{lab} が無い（fail-closed）")
        for hor in sorted(d[role][lab], key=lambda x: int(x)):
            for col, acc in d[role][lab][hor]:
                rows.append((abs(float(acc) - 0.5), str(col), float(acc), lab, str(hor)))
    if not rows:
        raise SystemExit(f"[材料の順位] {role}/{label} の順位が空（fail-closed）")
    rows.sort(key=lambda r: (-r[0], r[1], r[3], r[4]))       # 強い順・同点は名前順（並びを決定論に）
    return [(c, a, lab, hor) for _s, c, a, lab, hor in rows]


def _role_tfs(tfs, table, role) -> list[str]:
    """役割に使える時間足＝呼び出し側の足 ∩ 表の足 ∩ 対応表の役割の足（D1・表が正本）。"""
    rr = table["roles"][role]
    out = [t for t in tfs if t in table["tfs"] and (rr["tfs"] is None or t in rr["tfs"])]
    if not out:
        raise SampleError(f"役割 {role} に使える時間足が無い")
    return out


_SAMPLE_BAN_MEMO: dict = {}
_SAMPLE_BAN_CONST = None        # (gen_signal_families, 値決め窓の日数, n_min)＝1回だけ読む


def _insufficient_samples(name: str, tf: str) -> bool:
    """禁止3（標本不足）を、その場で計算する（表に無い数字のため・2026-08-13・段A の A-4）。

    ★なぜ要るか＝型の表の禁止3 は「材料カタログの535本 × 時間足」の組でしか作られていない。
      A-4 で範囲から数字を引くようになったので、表に載っていない数字（例＝RSI12）が出る。
      表を引くだけだと、**標本が足りない組をすり抜けて通してしまう**（禁止3 の穴）。
    ★式はここに書き写さない＝表を作っている `gen_signal_families` の関数をそのまま呼ぶ
      （n_eff＝値決め窓の日数 ÷ 値が独立に1つ決まる日数 ＜ n_min なら禁止）。
    """
    key = (name, tf)
    if key in _SAMPLE_BAN_MEMO:
        return _SAMPLE_BAN_MEMO[key]
    import contextlib
    import io
    global _SAMPLE_BAN_CONST
    if _SAMPLE_BAN_CONST is None:                    # 読み込みは1回だけ（毎回 読むと遅い）
        with contextlib.redirect_stdout(io.StringIO()):
            import gen_signal_families as gsf
            _SAMPLE_BAN_CONST = gsf
    out = _SAMPLE_BAN_CONST.insufficient_samples(name, tf)
    _SAMPLE_BAN_MEMO[key] = out
    return out


def _banned_pair(m: dict, table) -> bool:
    """（部品×時間足）が禁止3（標本不足）に当たるか。

    ★2026-08-13（段A の A-4）＝表に載っている組はそのまま拒否し、載っていない組（範囲から引いた
      新しい数字）は、その場で同じ計算をして判定する（表の穴を塞ぐ）。
    """
    if "family" not in m:
        return False
    name = ex.build_name(m)
    if (name, m["tf"]) in table["banned"]:
        return True
    return _insufficient_samples(name, m["tf"])


def _pick_material(rng, pool, tfs, limits, role, seen_rolekind, kind_count, table) -> dict:
    """材料1本＝G3（同系統×同役割は1本・K_MAX）＋型の表（対応表の系統×時間足・禁止3・許可 geo/time）を
    サンプリング時から守る（D1・2026-08-07 まこさん承認の表が正本）。"""
    rr = table["roles"][role]
    tf_pool = _role_tfs(tfs, table, role)
    ranges = material_ranges()
    by_lineage = _pool_families_by_lineage(pool)
    for _ in range(60):
        r = rng.random()
        if role == "location" and rr["geo"] and table["geo_ok"] and r < 0.5:
            m = {"geo": str(rng.choice(table["geo_ok"]))}
        elif role == "env" and "時間帯" in rr["lineages"] and r < 0.10 and limits.get("hour_range"):
            m = {"time": "時刻"}                  # 曜日の閾値格子は未定義＝時刻だけ（格子はまこさん §11-10）。表は両方許可
        else:
            # ★2026-08-13（段A の A-4）＝パラメータは「範囲の中から引く」（点の一覧から選ばない）。
            #   直す前は pool（カタログの列名を分解した (指標, 数字) の一覧）から1件 引いて、
            #   その数字をそのまま使っていた＝設定ファイルに並んだ数字しか出なかった
            #   （RSI なら 7・9・14・21 の4つだけ）。いまは 指標の種類だけを pool から引き、
            #   数字はその指標の範囲から引く（RSI なら 7〜21 の整数どれでも＝RSI12 も出る）。
            #   ★指標の種類の出方（どの指標がどれだけ出るか）は変えていない。候補を役割に使える
            #     系統で先に絞ってから引く＝同じものが同じ割合で出て、空振りだけが無くなる。
            cand_f = [f for k in rr["lineages"] for f in by_lineage.get(k, [])]
            if not cand_f:
                raise SampleError(f"役割 {role} に使える系統の指標が候補に無い")
            fam = str(cand_f[int(rng.integers(len(cand_f)))])
            m = {"family": fam, "param": draw_param(rng, fam, ranges),
                 "tf": str(rng.choice(tf_pool))}
            if _banned_pair(m, table):
                continue                                        # 禁止3（標本不足）＝引き直す
        kind = _lineage_of(m)
        if kind not in rr["lineages"]:
            continue                                            # 対応表＝役割に使えない系統
        if role != "trigger" and (role, kind) in seen_rolekind:
            continue
        _km, _ = ex.cap_of(limits, "k_max")
        if _km is not None and kind_count.get(kind, 0) >= _km:
            continue
        return m
    raise SampleError(f"役割 {role} の材料を60回引いても表と G3 を満たせない")


def _pkey(p):
    """数字の大小を比べるための鍵。数字は「1つ」「並び」「無し」の3通りある（material_pool の説明）。
    無し＜数字1つ・並び。並びは先頭から順に比べる（MACD線%(12,26) と (12,26,9) なら前者が小さい）。"""
    if p is None:
        return (0,)
    if isinstance(p, (tuple, list)):
        return (1,) + tuple(float(x) for x in p)
    return (1, float(p))


def same_fn_family_pairs(families) -> list[tuple[str, str]]:
    """同じライブラリ関数から出た family の組を、対応表から機械で作る（D15・2026-08-11・段C の C-5）。

    ★出どころ＝indicator_reference_diag.INDUSTRY_MAP（materials.md の「計算の出どころ」の欄と同じ）。
      **手で一覧を書かない。**手で1件ずつ登録する形は 2026-08-08 のインシデント #15 と同じ形。
    ★入れる法則＝「同じライブラリ関数から出た2本は組んでよい」。実測（2026-08-11）＝生成器が作らない
      定番のクロス7件（MACD／VWMACD／ストキャスRSI／DI+ × DI−／一目 転換線×基準線／KST／FISHER）と、
      コードに直書きだった例外1件（Stoch%K × %D）の8件すべてが この形。
    """
    byfn: dict[str, set] = {}
    for f in families:
        for fn in (iref.INDUSTRY_MAP.get(f, ((), ""))[0] or ()):
            byfn.setdefault(fn, set()).add(f)
    out = set()
    for fs in byfn.values():
        fl = sorted(fs)
        for i in range(len(fl)):
            for j in range(i + 1, len(fl)):
                out.add((fl[i], fl[j]))
    return sorted(out)


def pair_allowed(a: str, b: str, pa, pb) -> bool:
    """生成器が、この2つの family を『列2本の形』として組めるか。
    ★決まりの実物はここ1か所だけ。gen_materials の定番のクロスの判定も、この関数を呼ぶ
      （決まりを2か所に書き写すと、片方だけ直って腐る）。"""
    if a == b:
        return len({str(x) for x in (pa or ())}) >= 2
    return (min(a, b), max(a, b)) in set(same_fn_family_pairs([a, b]))


def _pair_materials(rng, pool, tfs, role, table, limits=None, form=None) -> list[dict]:
    """列2本の形（cross/diff/touch）＝①同 family の期間違い ②同じライブラリ関数から出た別の family
    ③同じ列の「素」と「前処理を掛けたもの」（＝新高値・新安値）。
    D1＝対応表の系統×時間足・禁止3 を守る。②は D15 の直し（2026-08-11・段C の C-5）。
    ③は部品 ts_max ほか（2026-08-13・段C の C-6）。"""
    rr = table["roles"][role]
    tf_pool = _role_tfs(tfs, table, role)
    ranges = material_ranges()
    fams = {}
    for b in pool:
        if iref.FAMILY_LINEAGE[b["family"]]["k"] in rr["lineages"]:
            fams.setdefault(b["family"], []).append(b["param"])
    # ①同じ指標のパラメータ違い2本 ／ ②同じライブラリ関数から出た別の指標2本
    # ★2026-08-13（段A の A-4）＝「2本を作れるか」は、カタログに数字が2つ以上 在るかではなく、
    #   **範囲が2つ以上の数字を持てるか**で決める（範囲が1点に潰れている指標だけが外れる）。
    cands: list[tuple[str, object]] = [("same", f) for f in fams
                                       if _range_has_two(f, ranges)]
    cands += [("fn", pr) for pr in same_fn_family_pairs(fams)]
    # ③同じ列の「素」と「前処理を掛けたもの」＝『高値が 直前n本の最高値を上抜けた』（新高値）
    #   ★2026-08-13 は「クロスのときだけ」に絞っていた（差・タッチは閾値が要るのに、前処理つきの材料に
    #     分位を使えなかったため）。2026-08-12（18回目） に解決表を前処理に対応させたので、その絞りを外した
    #     ＝差・タッチでも前処理つきの組を作る（段C の 4-2）。
    #   ★使えるのは「元の列と同じ単位のまま」の部品だけ（ts_max・ts_min）。順位・ばらつきは単位が
    #     変わるので、元の列と大小を比べても意味が無い＝水準（level・band）で使う（一覧＝MATERIAL_PRE）。
    if limits is not None and ex.pre_ops(same_unit=True, needs_state=False):
        cands += [("pre", f) for f in fams]
    if not cands:
        raise SampleError(f"役割 {role} で列2本の形を組める family が無い（表の系統の中）")
    for _ in range(30):
        tf = str(rng.choice(tf_pool))
        kind, c = cands[int(rng.integers(len(cands)))]
        if kind == "same":
            # ★2026-08-13（段A の A-4）＝範囲から2つ 引いて、違う数字なら採る。
            #   直す前は「カタログに在る数字の並びから2つ 選ぶ」だった＝RSI7 と RSI21 は組めても、
            #   RSI12 と RSI30 は永久に組めなかった（ゴールデンクロスの2本の期間が4つに縛られていた）。
            #   ★数字は「並び」のこともある（MACD線%(12,26) のような形）＝そのまま組で扱う。
            p1 = draw_param(rng, c, ranges)
            p2 = None
            for _t in range(20):
                cand2 = draw_param(rng, c, ranges)
                if str(cand2) != str(p1):
                    p2 = cand2
                    break
            if p2 is None:
                continue                              # 範囲が狭くて2本 引けない＝別の組み方を引き直す
            a_, b_ = sorted((p1, p2), key=_pkey)      # ★短い方を先に置く（まこさん OK 2026-08-11）
            pair = [{"family": c, "param": a_, "tf": tf},
                    {"family": c, "param": b_, "tf": tf}]
        elif kind == "pre":
            # ★同じ列の「素」と「前処理を掛けたもの」。本数は int_grid から引く＝CC が数字を書かない。
            p0 = draw_param(rng, c, ranges)
            # ★「状態に入って以降」の3つ（since_min・since_max・at_entry）は引かせない
            #   ＝state（基準にする状態の列の名前）が要るが、案を作る段では決められない。
            #   直す前は引いてしまい、出した案が必ず拒否されていた（2026-08-21・M2-2-8 で直した）。
            op = str(rng.choice(ex.pre_ops(same_unit=True, needs_state=False)))
            n_pre = draw_int(rng, limits, n_min=2)
            pair = [{"family": c, "param": p0, "tf": tf},
                    {"family": c, "param": p0, "tf": tf, "pre": {"op": op, "n": n_pre}}]
        else:
            fa, fb = c                                # type: ignore[misc]
            # ★数字は「同じ回の呼び出しから出た2本」を組む＝共通の軸は同じ値にそろえる
            #   （Stoch%K14 と Stoch%D14／MACD線%(12,26) と MACDシグナル線%(12,26,9)）。
            #   そろえた結果が相手の範囲の外に出るときだけ、それぞれ別に引く。
            pa_, pb_ = draw_param(rng, fa, ranges), draw_param(rng, fb, ranges)
            la, lb = _as_param_list(pa_), _as_param_list(pb_)
            k = min(len(la), len(lb))
            if k:
                if len(la) <= len(lb):
                    lb[:k] = la[:k]
                else:
                    la[:k] = lb[:k]
                ca, cb = _from_param_list(la), _from_param_list(lb)
                if param_in_range(fa, ca, ranges)[0] and param_in_range(fb, cb, ranges)[0]:
                    pa_, pb_ = ca, cb
            # ★別の指標どうしは、どちらを先に置くかの決まりが無い＝両方の向きを作る（乱数）。
            #   「短い方を先に置く」は同じ指標のパラメータ違いにだけ効く決まり。
            if rng.random() < 0.5:
                fa, fb, pa_, pb_ = fb, fa, pb_, pa_
            pair = [{"family": fa, "param": pa_, "tf": tf},
                    {"family": fb, "param": pb_, "tf": tf}]
        if not any(_banned_pair(m, table) for m in pair):
            return pair
    raise SampleError(f"役割 {role} の列2本を30回引いても禁止3 を避けられない")


def _q(rng, limits) -> dict:
    # ★2026-08-15（段A の A-5-3）＝分位を範囲から引く（直す前は9段のメニューからだけ）。
    return {"threshold_q": draw_q(rng, limits)}


def _dc1_side(rng, role, mats, side) -> str:
    """DC1（表の向きの決まり・2026-08-07 まこさん承認）＝順張り値の部品を side 付きの形で
    環境認識・十分性に使うとき、SHORT は below だけ・LONG は above だけ。それ以外は乱数。"""
    if role in ("env", "sufficiency") and any(_kubun_of(m) == "順張り値" for m in mats):
        return "below" if side == "SHORT" else "above"
    return str(rng.choice(["above", "below"]))


def _dc2_q(rng, role, m, limits, table, side) -> dict:
    """DC2（表の向きの決まり・2026-08-07 まこさん承認）の閾値の選び方を1か所にまとめたもの。

    レンジ系の引き金のオシレーターは行き過ぎを逆に取る＝SHORT は高分位（q70/q80/q90）・
    LONG は低分位（q10/q20/q30）。それ以外は分位の格子から普通に引く。
    ★2026-08-13（段C の C-6）に、level の中に直に書いてあったものを関数に出した。
      理由＝閾値とのクロス（cross_val）が同じ決まりを使うため。決まりを2か所に書き写さない
      （書き写すと片方だけ直って腐る＝2026-08-11 の C-5 と同じ轍）。中身は1文字も変えていない。
    """
    if role == "trigger" and _lineage_of(m) == "オシレーター":
        grid = table["quantile_grid_hi"] if side == "SHORT" else table["quantile_grid_lo"]
        # ★2026-08-15（段A の A-5-3）＝表の逐語（高分位 q70・q80・q90 ／ 低分位 q10・q20・q30）の
        #   **両端をそのまま範囲の両端にする**＝高分位なら q70〜q90 の整数 全部（q73 も引ける）。
        #   ★CC は数字を作っていません＝両端は表の逐語の 最小 と 最大 です。
        #   ★承認済みの型の表そのものは1バイトも書き換えていません（A-4 と同じやり方＝
        #     「一覧に在るか」の照合を「範囲の中か」の照合に変えただけ）。
        nums = [int(str(q).lstrip("q")) for q in grid]
        lo_all, hi_all = q_range_of(limits)
        lo_q, hi_q = max(lo_all, min(nums)), min(hi_all, max(nums))
        if hi_q < lo_q:
            # まこさんが quantile_range を狭めて、DC2 の帯と重ならなくなったとき。
            # 走行を丸ごと止めず、この案だけ引き直す（SampleError＝直す前と同じ扱い）。
            raise SampleError(f"DC2 の分位の帯（q{min(nums)}〜q{max(nums)}）が"
                              f"探せる範囲（q{lo_all}〜q{hi_all}）と重ならない")
        return {"threshold_q": draw_q(rng, limits, lo_min=lo_q, hi_max=hi_q)}
    return _q(rng, limits)


def _loose_q(rng, limits, q: str, side: str) -> str:
    """出る線（off）の分位＝入る線（on）より緩い側を、分位の範囲の中から引く（法則 C6 の②）。

    above（上に抜けたら入る）なら off は on より小さい分位・below なら大きい分位。
    ★数字を書かない＝範囲は `q_range_of`（recipes/search_limits.json）。緩める余地が無ければ SampleError。
    """
    lo, hi = q_range_of(limits)
    n = int(str(q).lstrip("q"))
    if side == "above":
        if n - 1 < lo:
            raise SampleError("hysteresis: 入る線が分位の下限＝出る線を緩められない（above）")
        return f"q{int(rng.integers(lo, n))}"
    if n + 1 > hi:
        raise SampleError("hysteresis: 入る線が分位の上限＝出る線を緩められない（below）")
    return f"q{int(rng.integers(n + 1, hi + 1))}"


def _make_hysteresis(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side) -> dict:
    """状態を保つ形（hysteresis）を1つ 組む（★72番の直し・M2-5-1・2026-08-23 まこさん承認 2b56024e711f…）。

    直す前＝`STATE_FORMS` に hysteresis が在るのに、ここに分岐が無く、引くたびに
    `SampleError 形 hysteresis の値の組み立てが未定義` で黙って引き直していた＝1本も案に入らなかった。
    ★組み方（法則 C6 の②・U10・C7）＝
      on  … 内側の条件1本（既存の `_make_cond`・入れ子なし・水準の形で分位を持つもの）
      off … 同じ材料・同じ形で、閾値の分位だけを「入る線より緩い側」にずらしたもの（`_loose_q`）
      value.n … 真を保てる最大の本数＝`state_hold_bars_range` から引く（範囲・数字を書かない）
    ★閾値を持たない形（candle_dir・touch・cross・time）は内側に選ばない＝線をずらせないため。
    """
    for _try in range(20):
        inner = _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side,
                           allow_nest=False)
        v = inner.get("value") or {}
        if inner.get("form") == "level" and "threshold_q" in v and inner.get("side") in ("above", "below"):
            off = json.loads(json.dumps(inner))
            off["value"]["threshold_q"] = _loose_q(rng, limits, v["threshold_q"], inner["side"])
            return {"role": role, "form": "hysteresis", "on": inner, "off": off,
                    "value": {"n": int(draw_num(rng, limits, "state_hold_bars_range"))}}
    raise SampleError("hysteresis: 内側に置ける『水準×分位』の条件を20回 引いても作れない")


def _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side, allow_nest=True) -> dict:
    forms = TRIGGER_FORMS if role == "trigger" else STATE_FORMS
    rr = table["roles"][role]
    forms = tuple(f for f in forms if f != "candle_dir" or "ローソク" in rr["lineages"])
    if not allow_nest:
        forms = tuple(f for f in forms if f != "hysteresis")   # 入れ子の内側には置けない（実行器 G5）
    form = str(rng.choice(forms))
    if form == "hysteresis":                    # ★72番の直し（M2-5-1）＝分岐が無くて引き直していた
        return _make_hysteresis(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side)
    if form in ex.NEST_FORMS:
        if not allow_nest:
            form = "level"
        else:
            inner = _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side,
                               allow_nest=False)
            inner.pop("role", None)
            inner["role"] = role
            n = draw_int(rng, limits, n_min=2)
            # ★2026-08-15（段A の A-5-4）＝ずらす本数を、コードに直に書いた 0・1 の2つから
            #   設定ファイルの範囲（`nest_offset_range`）へ出した。両端は直す前の2つの 最小 と 最大。
            out = {"role": role, "form": form, "inner": inner,
                   "value": {"n": n, "offset": int(draw_num(rng, limits, "nest_offset_range"))}}
            if form == "barssince":
                # ★何本前に成立したか（部品 barssince・2026-08-12・段C の C-6）。
                #   ★生成器は above だけを作る。理由＝below（「n本 以内に成立」）は within_n(n+1) と
                #     同じ結果になり、同じ条件を2通りで作ることになる（正規形・CP3 提案7 と同じ考え）。
                #   ★この決まりが潰す条件＝ありません。below で書ける条件は within_n が全部 作ります。
                #   ★検証器（実行器）は above も below も受けます＝人が書いた恒等のレシピを壊さない。
                out["side"] = "above"
            return out
    if form in NEEDS_PAIR:
        mats = _pair_materials(rng, pool, tfs, role, table, limits, form)
        for m in mats:
            kind_count[_lineage_of(m)] = kind_count.get(_lineage_of(m), 0) + 0  # 数えは下で一括
        if form == "cross":
            # DC3（表の向きの決まり）＝cross の direction は side と揃える（up＝LONG・down＝SHORT）
            return {"role": role, "form": "cross", "material": mats,
                    "value": {"direction": "down" if side == "SHORT" else "up"}}
        if form == "diff":
            # ★材料2本の組み方（正本＝engine_tuner_exec.PAIR_OPS・2026-08-12・段C の C-6）を
            #   一様に引く＝CC が「どれを何割で使うか」の数字を書かない。表に1行 足すと自動で増える。
            #   ・向き（side）は既に在る決まり DC1 をそのまま使う＝この部品のために新しい決まりを作らない。
            #   ・閾値は既に在る分位の格子（_q）をそのまま使う。
            #   ・窓の本数は int_grid から引く＝CC が数字を書かない（点の一覧である件は段A で直す）。
            op = str(rng.choice(ex.pair_ops()))
            val = _q(rng, limits) if op == "sub" else {"op": op, "th": _q(rng, limits)}
            if ex.PAIR_OPS[op]["needs_n"]:
                val["n"] = draw_int(rng, limits, n_min=2)
            return {"role": role, "form": "diff", "material": mats,
                    "side": _dc1_side(rng, role, mats, side), "value": val}
        return {"role": role, "form": "touch", "material": mats, "value": {"const": "TOL_SR"}}
    if form == "candle_dir":
        # DC4（表の向きの決まり）＝反転サイン・ローソクは SHORT＝bear だけ・LONG＝bull だけ
        return {"role": role, "form": "candle_dir",
                "value": {"dir": "bear" if side == "SHORT" else "bull"}}
    m = _pick_material(rng, pool, tfs, limits, role, seen_rolekind, kind_count, table)
    if "time" in m:
        return {"role": role, "form": "level", "material": [m],
                "side": str(rng.choice(["above", "below"])),
                "value": {"n": int(draw_num(rng, limits, "hour_range"))}}
    # ★水準の形（level・band・band_exclude）には、単位の変わる前処理を掛けられる（2026-08-12（18回目）・4-2）。
    #   ＝『いまの値が 直近n本の中で上位20%』（ts_rank）／『直近n本のばらつきが大きいとき』（ts_std）。
    #   ・掛けるか掛けないかは「素のまま」を選択肢の1つに入れて一様に引く＝CC が確率の数字を書かない。
    #   ・閾値は下の既に在る決まり（DC1・DC2・分位の格子）がそのまま決める＝新しい決まりを作らない。
    #   ・本数は int_grid から引く＝CC が数字を書かない。
    if form in ex.forms_where("pre_ok"):       # ★手書き → 性質表から（M2-2-3b）
        _pre_opts = [None] + ex.pre_ops(same_unit=False)
        _op = _pre_opts[int(rng.integers(len(_pre_opts)))]
        if _op is not None:
            m = {**m, "pre": {"op": _op,
                              "n": draw_int(rng, limits, n_min=2)}}
    if form == "cross_val":
        # ★閾値とのクロス（部品 cross_val・2026-08-13・段C の C-6）＝『RSI が 70 を上抜けた』。
        #   実行器へ渡す形は cross（列1本 ＋ value.th）＝新しい形の名前を実行器に作らない。
        #   向き＝DC3 をそのまま使う（cross の direction は side と揃える）。
        #   閾値＝DC2 をそのまま使う（レンジ系の引き金のオシレーターは行き過ぎを逆に取る）。
        #   ★どちらも既に在る決まりで、この部品のために新しい決まりを作っていない。
        return {"role": role, "form": "cross", "material": [m],
                "value": {"direction": "down" if side == "SHORT" else "up",
                          "th": _dc2_q(rng, role, m, limits, table, side)}}
    if form == "level":
        if role == "trigger" and _lineage_of(m) == "オシレーター":
            # DC2（表の向きの決まり）＝レンジ系の引き金のオシレーターは行き過ぎを逆に取る
            #   SHORT＝above かつ 高分位（q70/q80/q90）・LONG＝below かつ 低分位（q10/q20/q30）
            return {"role": role, "form": "level", "material": [m],
                    "side": "above" if side == "SHORT" else "below",
                    "value": _dc2_q(rng, role, m, limits, table, side)}
        return {"role": role, "form": "level", "material": [m],
                "side": _dc1_side(rng, role, [m], side), "value": _q(rng, limits)}
    if form in ex.forms_where("band"):        # ★手書き → 性質表から（M2-2-3b）
        # ★2026-08-15（段A の A-5-3）＝帯の下限・上限も範囲から引く（直す前は9段のメニューから2つ）。
        #   ★2つが同じ値にならないようにする＝下限と上限が同じ帯は幅ゼロで意味が無い
        #     （直す前の replace=False と同じ意味を、範囲でやっているだけ）。
        _lo_q, _hi_q = q_range_of(limits)
        if _hi_q - _lo_q < 1:
            raise SampleError(f"帯を作れない（分位の範囲が q{_lo_q}〜q{_hi_q} で2つ選べない）")
        a = int(rng.integers(_lo_q, _hi_q))          # 下限＝上限より小さい所から引く
        b = int(rng.integers(a + 1, _hi_q + 1))      # 上限＝下限より大きい所から引く
        return {"role": role, "form": form, "material": [m],
                "value": {"lo": {"threshold_q": f"q{a}"}, "hi": {"threshold_q": f"q{b}"}}}
    if form == "slope":
        return {"role": role, "form": "slope", "material": [m],
                "side": _dc1_side(rng, role, [m], side),
                "value": {"n": draw_int(rng, limits)}}
    if form == "slope_avg":
        return {"role": role, "form": "slope_avg", "material": [m],
                "side": _dc1_side(rng, role, [m], side),
                "value": {"n": draw_int(rng, limits), "m": draw_int(rng, limits)}}
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
    forms = [f for f in (spec.get("forms") or ["level"]) if f in ex.forms_where("exit_ok")]   # ★手書き → 性質表から（M2-2-3b）
    rev = bool(spec.get("reverse_of_side"))
    form = str(rng.choice(forms))
    # ★系統がローソクだけの枝で、その系統の部品がプールに1本も無いときは、材料の要らない形
    #   （陽線か陰線か）で作る。★2026-08-11（段6 の 6-7）に注記を直した＝前は「ローソクの部品は
    #   実行器の FAMILY_TEMPLATES に無い＝材料として引けない」と書いてあったが、6-7 で名前の
    #   組み立てを参照表から機械で作る形にしたので、包み足・pinbar・body比 なども引けるようになった。
    #   （実際に引けるかは、承認済みの型の表に部品が載っているかで決まる＝6-6 の再承認のあと）
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
            p = ks[int(rng.integers(len(ks)))]       # 数字は並びのこともある（6-7・2026-08-11）
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
                "value": {"n": draw_int(rng, limits)}}
    # ── 水準を見る形（level）──
    # ★実行器は出口の発火条件で分位（threshold_q）を解けない（_exit_fire_ok が解決表を受け取らない・
    #   1073行の _vnum）。だから出口の水準は、名前つき定数レジストリに登録済みの値だけで表す。
    #   使えるのは、その定数が意味を持つ部品（RSI・ストキャス・ADX）に限る。
    #   ほかの部品は水準では見ない＝交差・傾き・ローソクの形で見る（値の要らない形）。
    hi_lo = _EXIT_LEVEL_CONST.get(m["family"])
    if hi_lo is None:
        return {"role": "env", "form": "slope", "material": [m],
                "side": ("above" if side == "SHORT" else "below") if rev else str(rng.choice(["above", "below"])),
                "value": {"n": draw_int(rng, limits)}}
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
    def hold_gate() -> dict:
        """満期に対する割合で保有の門を作る（分・5の倍数に丸める・最低5分）。

        ★2026-08-15（段A の A-5-2）＝割合は 0.25・0.5・0.75 の3つだけでなく、
          0.25〜0.75 の範囲から引く。
        """
        n = int(round(tmax_min * float(draw_num(rng, limits, "hold_frac_range")) / 5.0)) * 5
        return {"n": max(5, n)}

    exits: list[dict] = []

    # ── ① 利確（名前は TP2 で固定＝部分利確と縮む枝がこの名前を参照する）──
    tp_id = str(rng.choice(["TP_ZONE_MID", "TP_ZONE_OPP", "TP_PCT", "TP_SWING"]))
    if tp_id == "TP_ZONE_MID":
        lv = {"kind": "zone", "target": "mid"}
    elif tp_id == "TP_ZONE_OPP":
        lv = {"kind": "zone", "target": "opp", "fallback": "mid",
              "buf": _floor_pct(float(draw_num(rng, limits, "state_mult_range")) / 100.0)}
    elif tp_id == "TP_PCT":
        lv = {"kind": "pct", "base": "entry",
              "k": {"const": "SCALP_FLOOR", "mult": float(draw_num(rng, limits, "state_mult_range"))}}
    else:
        lv = {"kind": "swing", "target": "low" if side == "SHORT" else "high",
              "m": {"n": draw_int(rng, limits)},
              "buf": {"const": "SCALP_FLOOR", "mult": float(draw_num(rng, limits, "state_mult_range"))},
              "fallback": {"kind": "zone", "target": "mid"}}
    exits.append(mk(tp_id, "TP2", placement={"kind": "resting", "fill": "profit", "level": lv}))

    # ── ② 損切り（3種から1つ）／確率で「損切り無し＋資金防衛」（軸 X-d4）──
    no_sl = rng.random() < 0.15
    if not no_sl:
        sl_id = str(rng.choice(["SL_ZONE", "SL_PCT", "SL_SWING"]))
        if sl_id == "SL_ZONE":
            lv = {"kind": "zone_sl", "w": str(rng.choice(["range", "zone", "inner"])),
                  "k": _const100(float(draw_num(rng, limits, "exit_mult_range")) / 100.0)}
        elif sl_id == "SL_PCT":
            lv = {"kind": "pct", "base": "entry",
                  "k": {"const": "SCALP_FLOOR", "mult": float(draw_num(rng, limits, "exit_mult_range")) / 10.0}}
        else:
            lv = {"kind": "swing", "target": "high" if side == "SHORT" else "low",
                  "m": {"n": draw_int(rng, limits)},
                  "buf": {"const": "SCALP_FLOOR", "mult": float(draw_num(rng, limits, "state_mult_range"))},
                  "fallback": {"kind": "zone_sl", "w": "range", "k": _const100(1.0)}}
        exits.append(mk(sl_id, "SL", placement={"kind": "resting", "fill": "adverse",
                                                "pessimistic": True, "level": lv}))

    # ── ③ 資金防衛（1トレードの最大許容損失・損切り無しの案では必ず入れる）──
    if no_sl or rng.random() < 0.30:
        cap = float(draw_num(rng, limits, "loss_cap_range"))
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
                                             "arm": _floor_pct(float(draw_num(rng, limits, "state_mult_range"))),
                                             "giveback": {"n": max(1, int(round(float(draw_num(rng, limits, "giveback_range")) * 100)))},
                                             "floor": {"const": "SCALP_FLOOR"}}}))
    if rng.random() < 0.30:       # 一度 利が乗った後、建値+手数料床で降りる
        exits.append(mk("BEEXIT", "BEEXIT",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "pct", "base": "avg",
                                             "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},
                        fire={"all": [_state_cond("mfe_prev_pct", "above",
                                                  _floor_pct(float(draw_num(rng, limits, "state_mult_range"))))]}))
    if rng.random() < 0.30:       # 時間が経っても利が乗らない玉を、建値フロアで降りる（停滞・失速）
        exits.append(mk("BESTALE", "BESTALE",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "pct", "base": "avg",
                                             "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("mfe_prev_pct", "below",
                                                  _floor_pct(float(draw_num(rng, limits, "state_mult_range"))))]}))
    if rng.random() < 0.30:       # 利確に届かないまま満期が近い玉を、手前の位置で確定する
        frac = float(draw_num(rng, limits, "frac_range")) / 100.0
        exits.append(mk("MFEEXIT", "MFEEXIT",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "mix", "from": "entry", "to": "TP2",
                                             "frac": _const100(frac)}},
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("mfe_prev_pct", "above",
                                                  _floor_pct(float(draw_num(rng, limits, "state_mult_range"))))]}))
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
        # ★2026-08-15（段A の A-5-2）＝直す前は「一覧の中から 2回目以上・その案の回数以下のものを拾い、
        #   1つも無ければ 2 にする」でした（`or [2]` がコードに直に書いた数字＝場所3 の2件目）。
        #   いまは 2回目 から その案の積み増し回数 までの整数から引きます＝直書きの数字が消えました。
        lo = int(draw_num(rng, limits, "max_adds_range", lo_min=2, hi_max=max_adds))
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

    # ── ⑥ 部分利確（段数は範囲から・1回の決済が最小注文サイズを割らない）──
    # ★2026-08-15（まこさん指示「3回以上に分けられるようにする」）＝打ち切りの決まりを直した。
    #   直す前＝各段の割合を「**元の玉の量**に対する割合」として足し、残りより大きい割合が出たら打ち切る。
    #     ＝割合が 25〜75% なので2段でほぼ埋まり、**3段は実際にはほとんど作られなかった**
    #       （実測 2026-08-15＝上限を 5 にしても案200本で3段は0本）。
    #   直したあと＝実行器の実物に合わせた。実行器は「**いま残っている量** × その段の割合」を決済する
    #     ＝合計が玉の量を超えることは構造上 起きない（実測＝3段・各段0.3 で 0.0036／0.00252／0.001764）。
    #     打ち切るのは「決済する分」か「残る分」が **取引所の最小注文サイズ** を割るときだけ（fail-closed）。
    if rng.random() < 0.5:
        steps = int(draw_num(rng, limits, "ladder_steps_range"))
        mf = ladder_min_frac()                    # 玉に対する、最小注文サイズの割合（機械が出す）
        rest = 1.0
        for s in range(steps):
            frac = float(draw_num(rng, limits, "frac_range")) / 100.0
            if rest * frac < mf or rest * (1.0 - frac) < mf:
                break                             # この段を作ると、決済の量か 残りの量が最小注文を割る
            exits.append(mk("TP1_LADDER", f"TP1{'' if s == 0 else s + 1}", size_ratio=frac, once=True,
                            placement={"kind": "resting", "fill": "profit",
                                       "level": {"kind": "mix", "from": "entry", "to": "TP2",
                                                 "frac": _const100(frac * (s + 1) / steps)}}))
            rest *= (1.0 - frac)

    order = rng.permutation(len(exits))          # 並び順もデータ（上から先勝ち・要件 R13）
    return [exits[i] for i in order]


# ══ 場面の判定の束を組む（M2-5-1・2026-08-23 まこさん承認 2b56024e711f…）═══════════════════
#   ★何を作るか＝meta.regime.build（判定の中身＝条件の束）を、案を作るプログラム自身が組む。
#     52回目までは「読む口」（順位・決まり）と「拒否する側」（実行器 G7）だけで、組む側は0か所だった。
#   ★組み方＝決まり1件に部品1つを対応させる（足りない部品が出ない作り・法則の番号は regime_detection_kb §11）。
#     A 帯の幅      … K-6・R7  … geo W% が分位より上（下限の値は探す値）
#     B 構造・位置  … K-4・R1  … location の順位（場面を分ける力）の r_b 位（1位から順・乱数でない）
#     C 非トレンド  … K-5・R8・R5 … env「強さ」の順位の r_c 位 を not で包む（同上）
#     D 上位足      … K-2・R3・C4 … C の時間足は 5m より上からだけ引く
#     E 状態を保つ  … K-3・C6・C7・R4 … hysteresis（on＝A∩B∩C・off＝それぞれを緩い側へずらした any・n は範囲）
#   ★数字を1つも書かない＝閾値は分位の範囲・n は state_hold_bars_range。順位は成績表の実物。
#   ★K（上位 K 列の中から乱数で1本）は 2026-08-23 に無くした（まこさん決定「成績表の1位から順に使う」）。
#     (r_b, r_c, 向き) は `regime_draw_order(order_n)` が決まった並びで割り当てる＝乱数を使わない。
#   ★見本（RG-v5）の列（rg5_zone_ok など）は使わない＝bool_col は組まない（milestones2 §0 の 0.5 の2番）。
#   ★実行器の G7 は最後にもう一度 見る＝生成の側で満たす作り ＋ 拒否の二重。

REGIME_OUT_COL = {"range": "regime_range_built"}


def _material_from_col(col: str) -> dict:
    """成績表の列名（例 ER21__1h）を材料の辞書 {family, param, tf} に戻す（参照表＝indicator_reference_diag）。"""
    if "__" not in col:
        raise SampleError(f"順位の列名に時間足が無い: {col}")
    name, tf = col.rsplit("__", 1)
    ent, prm = iref.find(name)
    if ent is None or ent["family"] not in ex.FAMILY_TEMPLATES:
        raise SampleError(f"順位の列がカタログに無い: {col}")
    p = None if len(prm) == 0 else (prm[0] if len(prm) == 1 else tuple(prm))
    return {"family": ent["family"], "param": p, "tf": tf}


def _ranked_material_at(role, rank_pos: int, tfs, table, label=None, tf_ok=None) -> tuple[dict, dict]:
    """役割の材料を、成績表の rank_pos 位（1始まり）から取る（乱数を使わない・M2-5 の B）。

    型の表（役割×系統・時間足）と禁止3（標本不足）を満たすものだけを数えて rank_pos 位。
    戻り＝(材料, 記録{rank, col, label, horizon})。足りなければ SampleError（＝試行数がその役割の候補を使い切った）。
    """
    rr = table["roles"][role]
    ok_tfs = set(tf_ok if tf_ok is not None else _role_tfs(tfs, table, role))
    n = 0
    for col, acc, lab, hor in ranked_materials(role, label):
        tf = col.rsplit("__", 1)[1] if "__" in col else None
        if tf not in ok_tfs:
            continue
        try:
            m = _material_from_col(col)
        except SampleError:
            continue
        if _lineage_of(m) not in rr["lineages"] or _banned_pair(m, table):
            continue
        n += 1
        if n == int(rank_pos):
            return m, {"rank": int(rank_pos), "col": col, "label": lab, "horizon": hor, "分離力": acc}
    raise SampleError(f"{role}/{label or '全ラベル'} の順位に {rank_pos} 位が無い（使える候補 {n} 本）")


def regime_draw_order(n: int) -> tuple[int, int, str]:
    """案 n 番目（0始まり）に割り当てる (部品B の順位, 部品C の順位, 部品B の向き)＝1位から順・決まった並び。
    並び＝順位の和が小さい順 → 同じ和なら部品B の順位が小さい順 → 向き above・below の順。
    (1,1,above) (1,1,below) (1,2,above) (1,2,below) (2,1,above) (2,1,below) (1,3,…) …
    ★乱数を使わない。どこまで下位を試すかは試行数（search_limits.json・まこさんの値）で決まる。"""
    if n < 0:
        raise SampleError("案の番号が負")
    i = int(n) // 2
    side = ("above", "below")[int(n) % 2]
    s = 2
    while True:
        cnt = s - 1                                   # 和 s の組は (1,s-1) … (s-1,1) の s-1 通り
        if i < cnt:
            return i + 1, s - (i + 1), side
        i -= cnt
        s += 1


def _flip_loose(rng, limits, c: dict) -> dict:
    """水準の条件を「緩い側へずらして反転」した条件＝出る線（off）の部品（法則 C6 の②）。
    above q → below q'（q' < q）／ below q → above q'（q' > q）。"""
    out = json.loads(json.dumps(c))
    out["value"]["threshold_q"] = _loose_q(rng, limits, c["value"]["threshold_q"], c["side"])
    out["side"] = "below" if c["side"] == "above" else "above"
    return out


def sample_regime_build(rng, limits, pool, tfs, table, name="range", order_n: int = 0) -> tuple[dict, dict]:
    """場面の判定の束（meta.regime.build）を1つ 組む。戻り＝(build, 引いた記録)。いまはレンジだけ。

    ★指標と向きは乱数で引かない（2026-08-23 まこさん決定）＝order_n 番目の (部品B の順位, 部品C の順位, 向き) を
      `regime_draw_order` が決め、成績表の その順位の材料を使う。乱数が残るのは閾値の分位と続く長さ n だけ
      （承認済みの「値は範囲で探す」）。
    """
    if name != "range":
        raise SampleError(f"場面 {name} の束の組み方は未定義（レンジ以外は M2-6〜M2-8 で作る）")
    load_scene_rules()                                  # 決まりの正本が読めることを確かめる（fail-closed）
    tfs_all = list(table["tfs"])
    upper = [t for t in tfs_all if tfs_all.index(t) > tfs_all.index("5m")]      # 執行足より上（K-2）
    r_b, r_c, side_b = regime_draw_order(order_n)
    draw: dict = {"order_n": int(order_n)}
    # A 帯の幅（K-6・R7）＝geo W% が分位より上
    cond_a = {"role": "location", "form": "level", "material": [{"geo": "W%"}],
              "side": "above", "value": {"threshold_q": draw_q(rng, limits)}}
    # B 構造・位置（K-4・R1）＝location の成績表の r_b 位（ラベルは混ぜる）・向きは order_n で決まる
    m_b, draw["B"] = _ranked_material_at("location", r_b, tfs, table)
    cond_b = {"role": "location", "form": "level", "material": [m_b],
              "side": side_b, "value": {"threshold_q": draw_q(rng, limits)}}
    # C 非トレンド（K-5・R8・R5）＝env「強さ」の r_c 位・時間足は 5m より上（D・K-2）
    m_c, draw["C"] = _ranked_material_at("env", r_c, tfs, table, label="強さ",
                                         tf_ok=[t for t in _role_tfs(tfs, table, "env") if t in upper])
    strong = {"role": "env", "form": "level", "material": [m_c],
              "side": "above", "value": {"threshold_q": draw_q(rng, limits)}}
    cond_c = {"not": strong}
    # E 状態を保つ（K-3・C6・C7・R4）＝on＝A∩B∩C／off＝それぞれを緩い側へずらした any／n は範囲
    off_c = json.loads(json.dumps(strong))
    off_c["value"]["threshold_q"] = _loose_q(rng, limits, strong["value"]["threshold_q"], "below")
    # ↑ 「強さが上の線を超えたら解除」＝入る線（on の not の閾値）より上の分位＝below の緩め方と同じ向き
    hyst = {"form": "hysteresis",
            "on": {"all": [cond_a, cond_b, cond_c]},
            "off": {"any": [_flip_loose(rng, limits, cond_a), _flip_loose(rng, limits, cond_b), off_c]},
            "value": {"n": int(draw_num(rng, limits, "state_hold_bars_range"))}}
    build = {"entry": {"out_col": REGIME_OUT_COL[name], "tree": {"all": [hyst]}}, "block": None}
    return build, draw


def default_regime() -> dict:
    """既定の相場の宣言＝接続ファイル e38 が設定ファイルから読んだもの（監査 4-19／要件 R5）。

    ★道具の中に列の名前を書かないため、接続ファイルに聞きます。
      列の名前を道具に書いてしまうと、レンジ以外の相場を指定できなくなります（それが 4-19 の指摘でした）。
    """
    from tuner_adapters import e38 as _e38
    return _e38.regime("S2")


def sample_structure(rng, limits, pool, tfs, side="SHORT", regime=None, logic_id="GEN",
                     build_regime: bool = False, regime_order_n: int = 0) -> dict:
    """構造1本＝役割構成・本数・つなぎ方・形・材料・出口の枝・玉の持ち方 をランダムに組む。

    ★D1（2026-08-07 まこさん承認の型の表が正本）＝乱数は表の中だけで振る。
      ①型（シグナル家族）を表の対象（E-a1/4/5/8＝レンジ系）から1つ引く（行が無い型は生成不可）
      ②材料は対応表（役割×系統×時間足）・禁止3・許可 geo/time の中だけ
      ③向きは DC1〜DC4 の決まりで side と噛み合わせる
    """
    table = load_signal_table()
    pool = [b for b in pool
            if ex.build_name(b) in table["parts"]
            and b["family"] in iref.FAMILY_LINEAGE]
    if not pool:
        raise SampleError("表に載っている部品が pool に1つも無い")
    fam_label = str(rng.choice(table["families"]))       # ①型を1つ引く（4型は共通の対応表＝ラベルは記録用）
    # ★条件の合計本数（まこさん決定 2026-08-12・逐語「Aはすべて上限ナシでいいのでは」）
    #   上限の数字を持たない。作れなくなるところまで足して、その中から何本 残すかを一様に引く。
    #   「作れなくなるところ」は、承認済みの型の表（役割 × 使える系統）と G3 から機械が決める＝
    #   CC が数字を書かない。範囲が入っているとき（検収・過去の設定）は、これまでどおりその範囲から引く。
    _cr, _ = ex.cap_of(limits, "count_range")
    n_total = int(rng.integers(_cr[0], _cr[1] + 1)) if _cr is not None else None
    seen_rolekind: set = set()
    kind_count: dict = {}
    conds = []

    def _register(c):
        # ★状態を保つ形（hysteresis）は材料を直接 持たない＝内側（on）の材料を数える（M2-5-1・72番の直し）
        _hy = [c["on"]["material"][0]] if c.get("form") == "hysteresis" and (c.get("on") or {}).get("material") else []
        for m in (c.get("material") or []) + ([c["inner"]["material"][0]] if c.get("inner", {}).get("material") else []) + _hy:
            kind = _lineage_of(m)
            key = (c["role"], kind)
            if c["role"] != "trigger" and key in seen_rolekind:
                raise SampleError("G3 重複")
            seen_rolekind.add(key)
            kind_count[kind] = kind_count.get(kind, 0) + 1
            _km, _ = ex.cap_of(limits, "k_max")
            if _km is not None and kind_count[kind] > _km:
                raise SampleError("K_MAX 超過")

    trig = _make_cond(rng, "trigger", limits, pool, tfs, seen_rolekind, kind_count, table, side)
    _register(trig)
    conds.append(trig)
    _rm, _ = ex.cap_of(limits, "role_max")
    budget = dict(_rm) if _rm is not None else None
    state_roles = sorted(r for r in table["roles"] if r != "trigger")
    while n_total is None or len(conds) < n_total:
        avail = [r for r in state_roles if budget is None or budget.get(r, 0) > 0]
        if not avail:
            break
        # ★1つの役割で作れなくても、案を捨てない。ほかの役割を順に試して、
        #   どの役割でも作れなくなったところで止める（2026-08-12）。
        #   直す前は「その役割で20回 作れなかったら案を丸ごと捨てる」で、100本中19本が捨てられていた。
        made = None
        for role in rng.permutation(avail):
            role = str(role)
            for _try in range(20):
                try:
                    c = _make_cond(rng, role, limits, pool, tfs, seen_rolekind, kind_count, table, side)
                    _register(c)
                    made = (role, c)
                    break
                except SampleError:
                    continue
            if made:
                break
        if made is None:
            break                                         # どの役割でも作れない＝ここが作れる最大
        if budget is not None:
            budget[made[0]] -= 1
        conds.append(made[1])
    if n_total is None and len(conds) > 1:
        # ★上限を持たないとき＝作れた最大までの中から、何本 残すかを一様に引く（引き金は必ず残す）
        conds = conds[:int(rng.integers(1, len(conds) + 1))]
    # ── 発火経路（部品② どれか満たす（OR）＝欠陥 D5・まこさん解禁 2026-08-13）─────────────
    #   1経路＝引き金ちょうど1本 ＋ 状態条件0本以上（G1）。経路どうしは「どれか満たす」でつなぐ。
    #   ★直し方の出どころ＝`engine_tuner_defects.md`「直し方 D5」の逐語
    #     「確率で {"any": [経路1, 経路2]} を作れるようにします。経路ごとに引き金がちょうど1本 要ります（G1）」。
    #   ★経路の数の決め方＝条件の本数とまったく同じ形（2026-08-12 の上限撤廃）。
    #     上限の数字を持たない。**作れた条件の本数**を上限にして、その中から一様に引く。
    #     ＝G3（役割 × 系統は1本まで）の枠が尽きるところが上限で、機械が決める。CC が数字を書かない。
    #     （設定ファイルの p_max も 2026-08-12 に「無制限」になった。ここで数字を作り直さない。）
    #   ★状態条件の配り方＝作った順に1本ずつ、経路へ順番に配る（1本目→経路1・2本目→経路2・…）。
    #     ＝どの経路にも同じだけ配る。CC が「どの条件をどっちの経路に置くか」を選ばない。
    #   ★入れ子（if-then）は1経路のときだけ作る。複数経路のときは経路の木をそのまま平らに置く。
    _dm, _ = ex.cap_of(limits, "depth_max")
    _cr2, _ = ex.cap_of(limits, "count_range")
    max_paths = len(conds)
    if _cr2 is not None:                            # 範囲が在るとき＝増える引き金の分を範囲の中に残す
        max_paths = max(1, min(max_paths, _cr2[1] - len(conds) + 1))
    n_paths = int(rng.integers(1, max_paths + 1)) if max_paths > 1 else 1
    extra_trigs = []
    for _ in range(n_paths - 1):
        t2 = None
        for _try in range(20):
            try:
                cand = _make_cond(rng, "trigger", limits, pool, tfs, seen_rolekind, kind_count,
                                  table, side)
                _register(cand)
                t2 = cand
                break
            except SampleError:
                continue
        if t2 is None:
            break                                   # 引き金を作れなくなったところで止める
        extra_trigs.append(t2)
    if extra_trigs:
        buckets: list[list] = [[t] for t in ([conds[0]] + extra_trigs)]
        for _i, _c in enumerate(conds[1:]):
            buckets[_i % len(buckets)].append(_c)
        tree = {"any": [{"all": b} for b in buckets]}
    else:
        # つなぎ方＝flat all／if-then 入り（深さは limits.depth_max の内側）
        kids: list = list(conds)
        if len(conds) >= 3 and (_dm is None or _dm >= 2) and rng.random() < 0.3:
            a = kids.pop(len(kids) - 1)
            b = kids.pop(len(kids) - 1)
            kids.append({"if": a, "then": b})
        tree = {"all": kids}
    pos_adds = int(draw_num(rng, limits, "max_adds_range"))  # 先に決める＝出口の枝が回数で切り替わるため
    rg = dict(regime if regime is not None else default_regime())
    meta_extra = {}
    if build_regime:
        # ★M2-5-1＝場面の判定の束を、案を作るプログラム自身が組んで meta.regime.build に入れる。
        #   既定 False＝従来どおり（案の中身も乱数の消費も変えない・ここは最後に引く）。
        bd, draw = sample_regime_build(rng, limits, pool, tfs, table, name=str(rg.get("name") or "range"),
                                       order_n=int(regime_order_n))
        rg["build"] = bd
        meta_extra["regime_draw"] = draw             # 引いた記録（ラベル・先読み・K）＝人が追えるように残す
    return {
        "meta": {"strategy": "e38", "logic_id": logic_id, "side": side,
                 "signal_family": fam_label,
                 "regime": rg, **meta_extra},
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
def _qspec(m: dict, lane: str) -> tuple:
    """分位の解決表が1本の材料を読むのに要る指定＝(素の列名, 前処理 or None)。

    ★前処理（pre）も一緒に返す（2026-08-12（18回目）・段C の 4-2）。直す前は列名だけを返していたので、
      解決表は前処理を見ずに素の列の分布から閾値を作っていた＝前処理つきの材料に分位を当てると
      嘘の閾値になるため、実行器が G5 で拒否していた（fail-closed）。ここで前処理を一緒に渡し、
      build_qtable が列を読んだあとに同じ前処理を掛けてから分位を出す形にして、その拒否を外す。
    """
    return (ex._material_name(m, lane)[1], ex._pre_of(m))


def _tree_conds(node, out=None) -> list[dict]:
    """木の中の「本物の条件」を全部 集める（2026-08-21・48回目・M2-2-8 で新設）。

    ★何のために足したか。
      直す前は `ex._walk` だけを使っていた。`ex._walk` は「つなぎ木」を歩く関数で、
      次の2つを歩けない（歩く先として持っていない）。
        ①**判定の中身（meta.regime.build）の木**＝`bool_col`（真偽の列を読む形）が混ざる
        ②**状態を保つ形（hysteresis）の中の on と off**＝つなぎ木の外側にぶら下がる
      その結果、①②の中で分位（threshold_q）を使うと、分位の解決表に鍵が入らず、
      走らせた瞬間に「分位の解決表に無い」で止まった（2026-08-21 に実測）。
    ★`bool_col` は材料を取らないので集めない（分位も要らない）。
    ★入れ子形（streak 等）の内側は、ここでは降りない＝`_cond_keys` が降りる（役割を1か所に）。
    """
    out = [] if out is None else out
    if not isinstance(node, dict):
        return out
    if "bool_col" in node:
        return out
    if "not" in node:
        return _tree_conds(node["not"], out)
    if "all" in node or "any" in node:
        for ch in node.get("all", node.get("any", [])):
            _tree_conds(ch, out)
        return out
    if "if" in node and "then" in node:
        _tree_conds(node["if"], out)
        _tree_conds(node["then"], out)
        return out
    if "form" in node:
        out.append(node)
    return out


def needed_qkeys(recipes: list[dict]) -> dict[str, tuple]:
    """レシピ群が使う分位の鍵 → 材料の指定の組（単材料 or 差の2材料）。

    ★指定1件＝`_qspec` が返す (素の列名, 前処理 or None)。鍵は `ex._mat_key` が作る（前処理を含む
      ＝前処理を掛けると分布が変わるので、素の列とは別の鍵になる）。
    """
    keys: dict[str, tuple] = {}

    def _cond_keys(c, lane):
        v = c.get("value", {})
        mats = c.get("material") or []
        if c["form"] in ex.NEST_FORMS:            # 入れ子形（barssince を足した 2026-08-12・段C の C-6）
            _cond_keys(c["inner"], lane)
            return
        # ★状態を保つ形（hysteresis）＝内側の「入る条件（on）」と「出る条件（off）」を歩く
        #   （2026-08-21・48回目・M2-2-8 で直した）。
        #   直す前＝この形は材料を直接 持たないので `if not mats: return` で素通りしていた。
        #   ＝on と off の中で分位（threshold_q）を使うと、分位の解決表に鍵が入らず、
        #     走らせた瞬間に「分位の解決表に無い」で止まっていた（2026-08-21 に実測）。
        #   ＝M2-2-5 で足した形が、実際には1回も走らない状態だった。
        if c["form"] == "hysteresis":
            for sub in ("on", "off"):
                for cc in _tree_conds(c.get(sub)):
                    _cond_keys(cc, lane)
            return
        if not mats:
            return
        a = ex._mat_key(mats[0], lane)
        sa = _qspec(mats[0], lane)
        if c["form"] == "level" and "threshold_q" in v:
            keys[a] = (sa,)
        # ★連動する閾値（ref）の上下の挟み（clip_lo・clip_hi）を分位で書いたとき（2026-08-21・M2-2-8 で直した）。
        #   挟みは、その条件の材料と同じ鍵で解く（実行器 _vnum_q が同じ qkey を渡す）。
        #   直す前＝この条件は value に threshold_q を持たない（ref を持つ）ので、上の行に当たらず
        #   鍵が1つも入らなかった。＝走らせた瞬間に「分位の解決表に無い」で止まった（2026-08-21 に実測）。
        #   ＝M2-2-5 で足した「1バーごとに動く閾値」が、挟みつきでは1回も使えない状態だった。
        if "ref" in v and any("threshold_q" in v.get(s, {}) for s in ("clip_lo", "clip_hi")):
            keys[a] = (sa,)
        if c["form"] in ex.forms_where("band"):        # ★手書き → 性質表から（M2-2-3b）
            for sub in ("lo", "hi"):
                if "threshold_q" in v.get(sub, {}):
                    keys[a] = (sa,)
        # ★材料2本の組み方（部品 div・corr・2026-08-12・段C の C-6）＝鍵も分布も組み方ごとに違う
        #   （a−b と a÷b と 相関 は別の分布）。鍵の作り方は実行器の _pair_key を呼ぶ＝2か所に書かない。
        if c["form"] == "diff":
            op = ex._pair_op_of(v)
            tv = v.get("th", v)
            if "threshold_q" in tv:
                b = ex._mat_key(mats[1], lane)
                n_win = int(v["n"]) if ex.PAIR_OPS[op]["needs_n"] else None
                keys[ex._pair_key(a, b, op, n_win)] = (sa, _qspec(mats[1], lane), (op, n_win))
        # ★閾値とのクロス（部品 cross_val・2026-08-13・段C の C-6）＝列1本の cross の value.th。
        #   閾値は level とまったく同じ分布（その列そのもの）から解くので、鍵も level と同じ a。
        if c["form"] == "cross" and len(mats) == 1 and "threshold_q" in v.get("th", {}):
            keys[a] = (sa,)

    for r in recipes:
        lane = r["meta"].get("lane", "")
        ex._walk(r["entry"]["connective"])        # ★木の形の検査は今までどおり通す（副作用を残す）
        conds = _tree_conds(r["entry"]["connective"])
        # ★出口の枝の発火条件も歩く（D2・2026-08-07）。直す前は入口と事前の足切りしか見ておらず、
        #   出口に指標を見る条件（例＝レンジが壊れたことを見る枝）を入れると、分位の解決表に鍵が無くて止まった。
        for b in (r.get("exits") or []):
            if b.get("fire"):
                ex._walk(b["fire"])
                conds += _tree_conds(b["fire"])
        # ★判定の中身（meta.regime.build）の木も歩く（2026-08-21・48回目・M2-2-8 で直した）。
        #   直す前＝ここを1行も見ていなかった。
        #   ＝束の中で分位（threshold_q）を使うと、分位の解決表に鍵が入らず、走らせた瞬間に止まった。
        #   ★これは、M2-1-4 の承認材料に書いた逐語
        #     「束の中の値（閾値・パラメータ）が分位の範囲で書かれ、engine_tuner の探索の対象になる」
        #     が、実際には効いていなかったということ（2026-08-21 に実測して分かった）。
        #     M2-1 の見本は `bool_col`（真偽の列を読むだけ）で閾値を1つも使わなかったので表に出なかった。
        bd = ((r.get("meta") or {}).get("regime") or {}).get("build") or {}
        for slot in ("entry", "block"):
            one = bd.get(slot)
            if one and one.get("tree") is not None:
                conds += _tree_conds(one["tree"])
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
    unresolved: list[str] = []
    for key, specs in needed_qkeys(recipes).items():
        def _arr(spec):
            name, pre = spec
            if name in geo:
                a = np.asarray(geo[name], float)
            elif name in df.columns:
                a = df[name].to_numpy(float)
            else:
                # 別名（D4 の直し・2026-08-07）＝実行器 _col_array（686行）と同じ扱いにそろえる。
                # 直す前はここが別名を見ず、別名で持たれている7列のどれかに分位が当たると走行が丸ごと止まった。
                run_col = ex.RUNTIME_ALIAS.get(name)
                if run_col is not None and run_col in df.columns:
                    a = df[run_col].to_numpy(float)
                else:
                    # ★2026-08-13（段A の A-2b）＝実行器と同じく、その場で計算する
                    #   （列を先に全部 作らない・式は observe_diag を呼ぶ＝ここに書き写さない）。
                    a = ex.material_array(df, name)
            # ★前処理（pre）が在れば、実行器とまったく同じ式を掛けてから分位を出す（2026-08-12（18回目）・4-2）。
            #   式は実行器の _apply_pre を呼ぶ＝ここに書き写さない（2か所に同じ式を持つと片方が腐る）。
            # ★df を渡す（2026-08-21・48回目・M2-2-8 で直した）。
            #   「状態に入って以降」の3つ（since_min・since_max・at_entry）は、基準にする状態の列を
            #   データから読む。直す前はここが df を渡しておらず、その3つを材料に使って分位を書くと
            #   「基準にする状態の列がデータにありません」で止まった（2026-08-21 に実測）。
            #   ＝M2-2-5 で足した前処理3つが、分位と一緒には1回も使えない状態だった。
            return ex._apply_pre(a, pre, df) if pre else a
        if len(specs) == 1:
            s = _arr(specs[0])
        else:
            # ★材料2本の組み方（2026-08-12・段C の C-6）＝実行器の _pair_series を呼ぶ。
            #   式をここに書き写さない（書き写すと片方だけ直って黙って腐る＝4-2 の build_qtable と同じ考え）。
            _op, _n = specs[2] if len(specs) > 2 else ("sub", None)
            s = ex._pair_series(_arr(specs[0]), _arr(specs[1]), _op, _n)
        s = s[mask]
        s = s[np.isfinite(s)]
        if not len(s):
            # ★2026-08-13（段A の A-4 で表面化）＝ここで走行を丸ごと止めない。
            #   直す前＝有効標本がゼロの鍵が1つでも在ると、その場で全部の案が死んだ（SystemExit）。
            #   実例＝TD_SEQ_UP（数字を持たない材料）と、その前処理つきの相関。合成データでは
            #   値が動かず、相関が全部 欠損になる。案100本のうち1本が こうなると、残り99本も走らない。
            #   直したあと＝**その鍵だけ解決できないものとして落とす**。この鍵を使う案は、実行器の
            #   G5（解決表に鍵が無い＝fail-closed）で1本ずつ拒否される＝嘘の閾値は作らない。
            unresolved.append(key)
            continue
        table[key] = {q: float(np.quantile(s, int(q.lstrip("q")) / 100.0)) for q in grid}
    if unresolved:
        print(f"[解決表] 有効標本がゼロで解決できない鍵 {len(unresolved)} 件"
              f"（この鍵を使う案は落とす・嘘の閾値は作らない）: {unresolved[:5]}"
              + (" ほか" if len(unresolved) > 5 else ""))
    return table


# ══ 材料の組み立て（observe_diag build_features の再利用＝コピー禁止・H2）═══════════════════
ATTACH_CALLS = 0        # ★A-2b の完了の条件②＝本走でこの処理が1回も呼ばれないこと（数えて 0）


def attach_materials(df: pd.DataFrame, recipes: list[dict]) -> pd.DataFrame:
    """レシピ群が使うカタログ列だけを、走らせる前に組み立てて df に足す。

    ★2026-08-13（段A の A-2b）＝本走からは呼ばなくなった（列はその場で作る＝`ex.material_array`）。
      この関数を残しているのは、古いレシピの読み込みや診断が使えるようにするため。
      呼ばれた回数は `ATTACH_CALLS` に出る（完了の条件②＝本走で 0）。
      いまの呼び出し元は1つだけ＝`engine_tuner_fire_diag.py`（発火の診断）。

    ★2026-08-13（段A の A-3）＝設定ファイル（observe_config.json）に並んでいない数字でも列を作る。
      直す前＝`observe_diag.build_catalog(cfg)`（設定の数字で作った535本）から、名前が一致する物だけを
      拾っていた。＝`RSI12__5m` を要求すると、カタログに `RSI12` が無いので拾えず、
      最後の「組み立てられなかった列」で止まっていた（2026-08-13 に実測して確認）。
      直したあと＝要求された名前を1本ずつ材料の表で分解して（`observe_diag.find_material`）、
      その場で組み立てる（`observe_diag.make_material`）。＝設定ファイルの数字に縛られない。
      ★計算式はここに書き写さない（材料の表が正本）。★組み立て直した名前が要求と1文字でも違えば止める。
    """
    global ATTACH_CALLS
    ATTACH_CALLS += 1
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
        for tf, bases in by_tf.items():
            cfg_tf = dict(cfg)
            cfg_tf["timeframes"] = [tf]
            cat = []
            for base in sorted(bases):
                fam, prm = od.find_material(base)
                if fam is None:
                    raise SystemExit(f"[材料エラー] 材料の表に無い名前: {base}"
                                     f"（observe_diag の MATERIAL_FAMILIES＝計算式の正本）")
                one = od.make_material(fam, *prm)
                if one[0] != base:                       # 組み立て直した名前が要求と違う＝表と実物のずれ
                    raise SystemExit(f"[材料エラー] 名前を組み立て直すと変わる: {base} → {one[0]}"
                                     f"（材料の表 {fam} の名前の型と、分解した数字 {list(prm)} が噛み合っていない）")
                cat.append(one)
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


def run_trial_guarded(df: pd.DataFrame, recipe: dict, qtable: dict, judge, start, end):
    """案1本を走らせる。★その1本が拒否されても、走行を丸ごと止めない（まこさん指示 2026-08-16）。

    戻り値＝(結果, 拒否の理由)。走れたら (結果, None)、拒否されたら (None, 理由の文字列)。

    何を守るか＝探索の走行が、1本の案のせいで丸ごと死なないこと。
    2026-08-16 に実際に起きました＝分位の解決表に鍵の無い案が1本 混ざると、`--selftest` が
    8回中4回 丸ごと止まりました（`session_worklog_20260816.md` の §4）。

    ★握りつぶすのは「レシピの拒否」（RecipeError）だけです。それ以外の例外は、そのまま上へ
    投げます＝本当の不具合を「1本 落としました」で隠さないためです。
    ★落とした件数と理由は、呼ぶ側が必ず画面に出します（黙って消さない）。
    ★落とした案を「net $0 の案」として数に入れません＝嘘の数字を作らないためです。
    """
    try:
        return run_trial(df, recipe, qtable, judge, start, end), None
    except ex.RecipeError as e:
        return None, str(e)


def reject_code(msg: str) -> str:
    """拒否の理由の文字列から、まとめて数えるための短い名前を取り出す。

    実物の形＝`[レシピ拒否 G5] …`（`engine_tuner_exec._fail`）／`[実行器] 分位 q41 の解決表に …`。
    前者は G 番号、後者は `[…]` の中身をそのまま名前にする。どちらでもなければ先頭20文字。"""
    m = re.match(r"\[レシピ拒否 (G\d)\]", msg)
    if m:
        return m.group(1)
    m = re.match(r"\[([^\]]+)\]", msg)
    if m:
        return m.group(1) + ("／解決表に鍵が無い" if "解決表" in msg else "")
    return msg[:20]


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


def _q_range(lo: int, hi: int) -> dict:
    """分位を下限から上限までの整数から選ぶ値（範囲方式・段A の A-5-3・2026-08-15 新設）。

    ★整数で選んで `q37` の形に直します（レシピの中の書き方は直す前と同じ文字列）。
    """
    return {"kind": "q", "lo": int(lo), "hi": int(hi)}


def suggest_slot(trial, name: str, spec: dict):
    """1つの値を Optuna に作らせる。メニュー方式と範囲方式の2つに対応する。

    ★範囲方式を足した理由（監査 4-19／要件 R6・2026-08-03）
      それまで、保有時間の上限はメニュー方式でした。あらかじめ並べた数字からしか選べません。
      たとえば一番稼げる上限が 75分でも、メニューに 75分が無ければ、何回試しても出ません。
      範囲方式では、下限と上限の間の整数を全部試せます。
    """
    if spec.get("kind") == "int":
        return trial.suggest_int(name, spec["lo"], spec["hi"], step=spec.get("step", 1))
    if spec.get("kind") == "q":
        # ★2026-08-15（段A の A-5-3）＝分位も範囲方式にした（直す前は9段のメニュー方式）。
        return f"q{trial.suggest_int(name, spec['lo'], spec['hi'])}"
    return trial.suggest_categorical(name, spec["choices"])


def value_slots(recipe: dict, limits: dict) -> list[tuple[str, dict]]:
    """レシピの中の『動かせる値』を (パス, 値の作り方) で列挙する。構造は動かさない（第2段の定義）。

    値の作り方は2つ。メニュー方式（候補の一覧から選ぶ）と 範囲方式（整数の範囲から選ぶ）。
    """
    slots: list[tuple[str, dict]] = []
    # ★2026-08-15（段A の A-5-3）＝分位の値スロットを メニュー方式 → 範囲方式にした。
    qg = _q_range(*q_range_of(limits))

    def _cond_slots(prefix, c):
        v = c.get("value", {})
        if c["form"] in ex.NEST_FORMS:            # 入れ子形（barssince を足した 2026-08-12・段C の C-6）
            slots.append((f"{prefix}.value.n", _int_range(*int_range_of(limits, n_min=2))))
            # ★2026-08-15（段A の A-5-4）＝ずらす本数も『動かせる値』に出す。
            #   直さないと、生成のときに1回 引いた本数がそのまま固定され、第2段で1度も動かせない
            #   （2026-08-12 に value.th で同じ穴を塞いだのと同じ形）。
            if "offset" in v:
                _or = num_range_of(limits, "nest_offset_range")
                slots.append((f"{prefix}.value.offset", _int_range(int(_or["lo"]), int(_or["hi"]))))
            _cond_slots(f"{prefix}.inner", c["inner"])
            return
        if "threshold_q" in v:
            slots.append((f"{prefix}.value.threshold_q", dict(qg)))
        # ★"th" を足した（2026-08-12・段C の C-6）。★これは やることの表に無い直しです。
        #   直す前は value.th の中の分位が『動かせる値』に出てこなかった＝生成のときに1回 引いた分位が
        #   そのまま固定され、第2段の調整で1度も動かせなかった。当たるのは3か所
        #   ＝閾値とのクロス（cross_val・2026-08-13）／傾きの閾値（slope・slope_avg）／
        #     材料2本の割り算・相関（div・corr・2026-08-12）。
        #   ＝直さないと、いま足す div・corr の閾値が探索の対象にならない（部品を足した意味が消える）。
        for sub in ("lo", "hi", "th"):
            if "threshold_q" in v.get(sub, {}):
                slots.append((f"{prefix}.value.{sub}.threshold_q", dict(qg)))
        if c["form"] in ex.forms_where("slope_n"):     # ★手書き → 性質表から（M2-2-3b）
            slots.append((f"{prefix}.value.n", _int_range(*int_range_of(limits))))
        if c["form"] == "slope_avg":
            slots.append((f"{prefix}.value.m", _int_range(*int_range_of(limits))))
        # ★材料2本の組み方が窓を要るとき（corr）＝窓の本数も動かせる値（2026-08-12・段C の C-6）
        if c["form"] == "diff" and ex.PAIR_OPS[ex._pair_op_of(v)]["needs_n"]:
            slots.append((f"{prefix}.value.n", _int_range(*int_range_of(limits, n_min=2))))

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


def _slot_ref(recipe: dict, path: str):
    """スロットのパスを辿って (その値を持つ入れ物, 鍵) を返す。

    ★読むときも書くときも、この1か所だけを使う（辿り方を2か所に分けて持たない）。
      2026-08-16（段A の A-7）に、前後の値を読む必要が出たので apply_slots から切り出した。
    """
    import re as _re
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
                cur = recipe["entry"]["connective"]
            elif name == "exits":
                cur = recipe["exits"][int(idx)]
            else:
                raise SystemExit(f"[歩4 エラー] スロットのパスの根が不明: {path}")
            i += 1
            continue
        if name == "fire":
            conds, _d = ex._walk(cur["fire"])              # _walk は参照を返す＝直接書ける
            cur = conds[int(idx)]
            i += 1
            continue
        if last:
            return cur, name
        cur = cur[name] if idx is None else cur[name][int(idx)]
        i += 1
    raise SystemExit(f"[歩4 エラー] スロットのパスを辿りきれない: {path}")


def apply_slots(recipe: dict, choices: dict[str, object]) -> dict:
    """スロットのパスに選んだ値を書き込んだレシピの複製を返す（構造は動かさない）。"""
    r = copy.deepcopy(recipe)
    for path, val in choices.items():
        holder, key = _slot_ref(r, path)
        holder[key] = val
    return r


def read_slots(recipe: dict, slots: list[tuple[str, dict]]) -> dict[str, object]:
    """いまレシピに入っている『動かせる値』を読み出す（B8＝選んだ値の前後・段A の A-7）。"""
    out: dict[str, object] = {}
    for path, _spec in slots:
        holder, key = _slot_ref(recipe, path)
        if isinstance(holder, dict) and key in holder:
            out[path] = holder[key]
    return out


# ══ 本体＝2段サンプリング ═══════════════════════════════════════════════════════════════
def run_generation(df: pd.DataFrame, limits: dict, judge, start, end, *,
                   trials1: int, trials2: int, top_k: int, seed: int,
                   run_dir: pathlib.Path, pool, tfs, catalog_total: int,
                   side="SHORT", regime=None,
                   base_trades=None, atr_edges=None, min_per_day=None, net_floor=None,
                   purpose: str, tag: str = "",
                   df_confirm: pd.DataFrame | None = None, confirm_start=None, confirm_end=None,
                   base=None, rules: dict | None = None, rfloor: float | None = None,
                   build_regime: bool = False) -> dict:
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
                                 logic_id=f"GEN{len(structures):04d}", build_regime=build_regime,
                                 regime_order_n=len(structures))      # ★判定の束＝1位から順（乱数でない）
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

    # ── 材料と解決表（探索開始時に1回固定・§5-4）──
    # ★2026-08-13（段A の A-2b）＝ここで列を先に全部 作るのをやめた。
    #   材料は、条件が要求した組だけを その場で計算する（`ex.material_array`・同じ組は使い回す）。
    #   完了の条件②＝本走で `attach_materials` の呼び出し回数が 0 であること（下の行で機械が出す）。
    df2 = df
    print(f"[A-2b] 列を先に全部 作る処理（attach_materials）の呼び出し回数 = {ATTACH_CALLS}"
          f"（0 なら、材料はその場で作っている）")
    geo = _geo_of(df2)
    qtable = build_qtable(df2, geo, structures, quantile_list(limits), start, end)
    (run_dir / "qtable.json").write_text(json.dumps(qtable, ensure_ascii=False, indent=1, sort_keys=True) + "\n",
                                         encoding="utf-8")
    print(f"[分位の解決表] {len(qtable)} 鍵 × {len(quantile_list(limits))} 分位を値決め窓から1回固定"
          f"（rolling しない・保存 {run_dir / 'qtable.json'}）")

    # ── 第1段の実行 ──
    legacy_total = 0
    results1: list[dict] = []
    reused = 0
    run_rejects = Counter()          # ★走らせる段で拒否された案の 理由別の件数（2026-08-16）
    run_reject_msgs: list[str] = []  # ★その中身（画面に出す・黙って消さない）
    for si, r in enumerate(structures):
        key = f"s1/{si}/{recipe_hash(r)}"
        got = jn.get(key)
        if got is not None:
            reused += 1
            results1.append(got)
            continue
        res, why_reject = run_trial_guarded(df2, r, qtable, judge, start, end)
        if res is None:
            # ★1本の案が拒否されても走行を止めない（まこさん指示 2026-08-16・A-1a-0 の1番）。
            #   その1件だけ落として、件数と理由をこの段の終わりに画面へ出す。
            #   ★results1 に入れません＝net $0 の案として数に入れると嘘の数字になるためです。
            run_rejects[reject_code(why_reject)] += 1
            run_reject_msgs.append(f"#{si}: {why_reject}")
            continue
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
    # ★走らせる段で落とした案（2026-08-16・A-1a-0 の1番）＝黙って消さない
    if run_reject_msgs:
        print(f"[走行で落とした案] {len(run_reject_msgs)}/{len(structures)} 本"
              f"（走行は止めません・理由別 {json.dumps(dict(run_rejects), ensure_ascii=False)}）")
        for m in run_reject_msgs[:5]:
            print(f"  {m}")
        if len(run_reject_msgs) > 5:
            print(f"  … ほか {len(run_reject_msgs) - 5} 本（全部は下の記録ファイルに出す）")
        (run_dir / "run_rejects.json").write_text(
            json.dumps({"件数": len(run_reject_msgs), "理由別": dict(run_rejects),
                        "中身": run_reject_msgs}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"  全部の記録＝{run_dir / 'run_rejects.json'}")
    if not results1:
        raise SystemExit(f"[歩4 エラー] 走らせた案が1本も結果を出さなかった"
                         f"（{len(structures)} 本 全部が拒否・理由別 {dict(run_rejects)}）"
                         "＝落として先へ進む形では隠せないので、ここで止めます")
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
    s2_rejects = Counter()           # ★第2段で拒否された案の 理由別の件数（2026-08-16）
    s2_reject_msgs: list[str] = []
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
                res, why_reject = run_trial_guarded(df2, r2, qtable, judge, start, end)
                if res is None:
                    # ★値を詰めた案1本が拒否されても、TPE の走行を止めない（2026-08-16・A-1a-0 の1番）。
                    #   journal には書きません＝net の数字を1つも作らないためです（再実行すれば同じ結果）。
                    s2_rejects[reject_code(why_reject)] += 1
                    s2_reject_msgs.append(f"#{sidx}/試行{trial.number}: {why_reject}")
                    return -1e9
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
        if s2_reject_msgs:                       # ★落とした案は黙って消さない（2026-08-16）
            print(f"  [第2段で落とした案] {len(s2_reject_msgs)}/{len(top) * per} 本"
                  f"（走行は止めません・理由別 {json.dumps(dict(s2_rejects), ensure_ascii=False)}）")
            for m in s2_reject_msgs[:3]:
                print(f"    {m}")
            (run_dir / "run_rejects_stage2.json").write_text(
                json.dumps({"件数": len(s2_reject_msgs), "理由別": dict(s2_rejects),
                            "中身": s2_reject_msgs}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
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
        df2c = df_confirm            # ★A-2b＝列は その場で作る（先に全部 作らない）
        rc_j = run_trial(df2c, best_struct, qtable, judge, confirm_start, confirm_end)   # ★同じ qtable
        print(f"\n[確認窓の1走] 構造 #{best_rec['idx']}（値決め窓で最良）を確認窓で1回だけ走らせた"
              f"＝net ${rc_j['total']:+,.0f} ／ {rc_j['n']}玉 ／ {rc_j['per_day']:.2f}件/日"
              "（★ここで選び直しはしない・分位は値決め窓のものを流用）")
        bands = None
        if base_trades is not None and atr_edges:
            bands = tj.atr_bands(base_trades, rs_j["t"], atr_edges)
        # ★B8＝選んだ値の前後（段A の A-7・2026-08-16 新設）。値を1刻みだけ動かして走らせ、
        #   net が崩れないかを見る。崩れるならその値はまぐれの疑い。
        #   前後の点は値スロットの宣言から機械で作る（CC は数字を作らない）。
        #   ★線（どれだけ落ちてよいか）が設定に無いあいだは1本も走らせない。
        neighbors = None
        if (rules or {}).get("neighbor_drop_max") is not None:
            _slots = value_slots(best_struct, limits)
            _cur = read_slots(best_struct, _slots)
            _pts, _skp = tj.neighbor_points(dict(_slots), _cur, rules)
            print("\n[B8 選んだ値の前後（段A の A-7）＝1刻み動かしても net が崩れないかを見る]")
            for _nm, _why in _skp:
                print(f"  － {_nm}: 作らなかった（{_why}）")
            neighbors = []
            for _p in _pts:
                # ★囲いを使う＝前後の1点が拒否されても走行を丸ごと止めない（まこさん指示 2026-08-16）。
                _r, _why = run_trial_guarded(df2, apply_slots(best_struct, {_p["name"]: _p["value"]}),
                                             qtable, judge, start, end)
                if _r is None:
                    print(f"  {_p['name']}{_p['dir']}: {_p['note']} → 走らせられなかった（{_why}）")
                    continue
                neighbors.append({**_p, "net": float(_r["total"]), "n": int(_r["n"]),
                                  "per_day": float(_r["per_day"])})
                print(f"  {_p['name']}{_p['dir']}: {_p['note']} → net ${_r['total']:+,.0f}"
                      f" / {_r['n']}玉 / {_r['per_day']:.2f}件/日")
            print(f"  ＝前後 {len(neighbors)} 点を走らせた。★この {len(neighbors)} 本は"
                  "累積の試行数に足していない（値を選ぶ走行ではなく、選び終わった値を確かめる走行のため）。"
                  "★前後のほうが net が高くても、最良の構造は選び直さない。")
        verdict = tj.print_judgement(base, rs_j, rc_j, min_per_day, stats, len(kept),
                                     rules=rules, rfloor=rfloor, trials=trials1 + trials2,
                                     stage_bests=None, bands=bands, neighbors=neighbors,
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
    # ★上限5件は 2026-08-12 まこさん決定で「無制限」（逐語「Aはすべて上限ナシでいいのでは」）。
    #   本走の設定ファイルと同じにして、番人が本走と同じ道を通るようにする。
    "role_max": ex.NO_CAP,
    "count_range": ex.NO_CAP, "k_max": ex.NO_CAP,
    "quantile_grid": ["q20", "q50", "q80"], "depth_max": ex.NO_CAP, "p_max": ex.NO_CAP,
    # ★2026-08-15（段A の A-5-2）＝検収専用の値も「決まった数字だけ」から「範囲」に変えた。
    #   ★幅を狭く取っている（検収は毎回 同じ結果が出ることを見るため）。本走は search_limits.json の範囲を使う。
    "state_mult_range": {"lo": 1.0, "hi": 1.0, "kind": "float", "dec": 1}, "int_grid": [3, 6, 12],
    "int_range": {"lo": 3, "hi": 12},
    # 保有時間の上限＝検収専用の範囲（本走は役割から決める＝resolve_hold_range・監査 4-19／要件 R6）
    "hold_bars": (1, 24), "hold_role": "検収専用",
    "hour_range": {"lo": 6, "hi": 18, "kind": "int"},
    "frac_range": {"lo": 50.0, "hi": 50.0, "kind": "float", "dec": 1},
    "exit_mult_range": {"lo": 50.0, "hi": 100.0, "kind": "float", "dec": 1},
    "max_adds_range": {"lo": 1, "hi": 2, "kind": "int"}, "fdr_q": 0.10,
    # 出口の枝（D2・2026-08-07）＝検収専用の値。本走は search_limits.json の範囲を使う。
    "hold_frac_range": {"lo": 0.5, "hi": 0.5, "kind": "float", "dec": 2},
    "giveback_range": {"lo": 0.5, "hi": 0.5, "kind": "float", "dec": 2},
    "loss_cap_range": {"lo": 0.6, "hi": 0.6, "kind": "float", "dec": 1},
    "ladder_steps_range": {"lo": 1, "hi": 2, "kind": "int"},
    # ★2026-08-15（段A の A-5-4）＝入れ子の「ずらす本数」も検収専用の範囲を持つ。
    #   本走は search_limits.json の nest_offset_range を使う（T18 はそちらを読んで確かめる）。
    "nest_offset_range": {"lo": 0, "hi": 1, "kind": "int"},
    # ★状態を保つ形（hysteresis）の続く長さ＝検収専用の範囲（M2-5-1・72番の直しで生成器が hysteresis を
    #   組めるようになったため、検収の limits にも要る。本走は search_limits.json の state_hold_bars_range）。
    "state_hold_bars_range": {"lo": 24, "hi": 288, "kind": "int"},
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

    # ── T1-C5 列2本の形の作り方（D15 の直し・2026-08-11・段C の C-5）───────────────────
    #   ①同じ指標のパラメータ違いの2本は、短い方が必ず先に置かれる（＝ゴールデンクロスの向き）
    #   ②別の指標どうしの2本は「同じライブラリ関数から出た」ものだけ（コードに直書きの例外を持たない）
    #   ③定番のクロス8件（MACD・VWMACD・ストキャスRSI・DI+/DI−・一目・KST・FISHER・ストキャス）が
    #     組める＝pair_allowed が実物の対応表 INDUSTRY_MAP から引いている
    import inspect
    _tbl5 = load_signal_table()
    _p5 = []
    for i in range(100):
        _r5 = np.random.default_rng([55, 1, i])
        for _role5 in _tbl5["roles"]:
            try:
                _p5.append(_pair_materials(_r5, pool, tfs_small, _role5, _tbl5))
            except (SampleError, KeyError):
                continue
    if len(_p5) < 50:
        ng.append(f"T1-C5: 列2本の組を100回×4役割 引いて {len(_p5)} 組しか出ない（引けていない）")
    _rev = [pr for pr in _p5 if pr[0]["family"] == pr[1]["family"]
            and _pkey(pr[0]["param"]) > _pkey(pr[1]["param"])]
    if _rev:
        ng.append(f"T1-C5 番人①: 同じ指標の2本で、長い方が先に置かれた組が {len(_rev)} 件"
                  f"（例 {_rev[0][0]['family']} {_rev[0][0]['param']} → {_rev[0][1]['param']}）"
                  "＝ゴールデンクロスの逆を作っている")
    _bad5 = [pr for pr in _p5 if pr[0]["family"] != pr[1]["family"]
             and not pair_allowed(pr[0]["family"], pr[1]["family"], [0], [0])]
    if _bad5:
        ng.append(f"T1-C5 番人②: 同じライブラリ関数から出ていない2本を組んだ組が {len(_bad5)} 件"
                  f"（例 {_bad5[0][0]['family']} × {_bad5[0][1]['family']}）")
    _src5 = "\n".join(ln.split("#", 1)[0] for ln in inspect.getsource(_pair_materials).splitlines())
    if "Stoch%K" in _src5:                                    # 説明の文（#より右）は外して見る
        ng.append("T1-C5 番人②: _pair_materials に指標の名前が直書きで残っている"
                  "（法則でなく手書きの一覧に戻っている＝インシデント #15 と同じ形）")
    _want5 = [("MACD線%", "MACDシグナル線%"), ("VWMACD線%", "VWMACDシグナル%"),
              ("StochRSI%K", "StochRSI%D"), ("DI+", "DI-"), ("転換線", "基準線"),
              ("KST", "KSTシグナル"), ("FISHER", "FISHERシグナル"), ("Stoch%K", "Stoch%D")]
    _ng5 = [f"{a} × {b}" for a, b in _want5 if not pair_allowed(a, b, [0], [0])]
    if _ng5:
        ng.append(f"T1-C5 番人③: 定番のクロスを組めない（{'／'.join(_ng5)}）")
    if pair_allowed("RSI", "ADX", [7, 21], [7, 21]):
        ng.append("T1-C5 番人③: 関係の無い2本（RSI × ADX）まで組めると言う＝法則が効いていない")

    # ── T1-C6 閾値とのクロス（部品① cross_val・2026-08-13・段C の C-6）──────────────────
    #   ①生成器が実際に「列1本 ＋ 閾値」の cross を作る
    #     （作らなければ、直したのが実行器だけ＝「実行器は受け付けるのに生成器が作らない」D15 と同じ形）
    #   ②作ったものを検証器がそのまま受け付ける（G5・G6 が拒否しない）
    #   ③わざと閾値を外すと検証器が拒否する（＝①②の検査が効いている証拠・メタ確認）
    _cv6 = []
    for i in range(200):
        _r6 = np.random.default_rng([66, 1, i])
        try:
            _c6 = _make_cond(_r6, "trigger", lm, pool, tfs_small, set(), {}, _tbl5,
                             "SHORT" if i % 2 else "LONG")
        except SampleError:
            continue
        if _c6.get("form") == "cross" and len(_c6.get("material") or []) == 1:
            _cv6.append(_c6)
    if not _cv6:
        ng.append("T1-C6 番人①: 生成器が『閾値とのクロス』（列1本＋閾値）を200回 引いて1本も作らない"
                  "＝実行器だけ直って生成器が追随していない（D15 と同じ形）")
    for _c6 in _cv6[:20]:
        if "th" not in (_c6.get("value") or {}):
            ng.append("T1-C6 番人②: 生成した列1本の cross に閾値（value.th）が無い")
            break
        try:
            ex._check_cond(_c6, "", "T1-C6", [])
        except ex.RecipeError as e:
            ng.append(f"T1-C6 番人②: 生成した閾値とのクロスを検証器が拒否する（{str(e)[:60]}）")
            break
    try:
        ex._check_cond({"role": "trigger", "form": "cross", "value": {"direction": "up"},
                        "material": [{"family": "RSI", "param": 14, "tf": "5m"}]},
                       "", "T1-C6 メタ確認", [])
        ng.append("T1-C6 番人③: 閾値の無い列1本の cross が通る＝書き忘れを検証器が捕まえていない")
    except ex.RecipeError:
        pass

    # ── T1-C6b どれか満たす（OR）＝発火経路（部品②・欠陥 D5・まこさん解禁 2026-08-13）────────
    #   ①T1 の100本（＝全部 検証器を通ったもの）に「経路が2本以上」が出る
    #     ＝正本 engine_tuner_defects.md「直し方 D5」の完了の線の逐語
    #       「100構造の内訳の『経路数の分布』に 2 が出ること（いまは {"1": 100}）」
    #   ②経路が2本以上の案は、経路ごとに引き金がちょうど1本（G1）
    #   ③メタ確認＝条件を1本に絞ると、経路も1本になる（経路の数の決め方が効いていることの確認）
    _multi6 = {k: v for k, v in bd["経路数の分布"].items() if int(k) >= 2}
    if not _multi6:
        ng.append("T1-C6b 番人①: 100本の案に『経路が2本以上』が1本も出ない"
                  "＝どれか満たす（OR）を生成器が作っていない（欠陥 D5 のまま）")
    for _r6b in structs:
        _t6 = _r6b["entry"]["connective"]
        if set(_t6) != {"any"}:
            continue
        for _pi, _p6 in enumerate(_t6["any"]):
            _c6b, _ = ex._walk(_p6)
            _n6 = sum(1 for c in _c6b if c.get("role") == "trigger")
            if _n6 != 1:
                ng.append(f"T1-C6b 番人②: 経路{_pi + 1} の引き金が {_n6} 本（経路ごとに1本・G1）")
                break
    # ── T1-C6c 材料の前処理（部品③ ts_max ほか・2026-08-13・段C の C-6）──────────────────
    #   ①生成器が「素の列 × 前処理を掛けた同じ列」の組を作る（＝新高値・新安値が書ける）
    #   ②作った条件を検証器がそのまま受け付ける
    #   ③メタ確認＝前処理の本数を壊すと拒否される／前処理に分位を渡すと拒否される
    _pre6 = []
    for i in range(200):
        _r6c = np.random.default_rng([88, 1, i])
        try:
            _pr = _pair_materials(_r6c, pool, tfs_small, "trigger", _tbl5, lm, "cross")
        except (SampleError, KeyError):
            continue
        if any(m.get("pre") for m in _pr):
            _pre6.append(_pr)
    if not _pre6:
        ng.append("T1-C6c 番人①: 生成器が『素の列 × 前処理を掛けた同じ列』の組を200回 引いて1本も作らない"
                  "（新高値・新安値を書けない＝部品 ts_max が生成器に届いていない）")
    for _pr in _pre6[:20]:
        try:
            ex._check_cond({"role": "trigger", "form": "cross", "material": _pr,
                            "value": {"direction": "up"}}, "", "T1-C6c", [])
        except ex.RecipeError as e:
            ng.append(f"T1-C6c 番人②: 生成した前処理つきの組を検証器が拒否する（{str(e)[:70]}）")
            break
    if _pre6:
        _m_ok = [m for m in _pre6[0] if m.get("pre")][0]
        for _broke, _why in ((({**_m_ok, "pre": {"op": _m_ok["pre"]["op"], "n": 1}}),
                              "前処理の本数を 1 にしても通る"),
                             (({**_m_ok, "pre": {"op": "存在しない部品", "n": 6}}),
                              "一覧に無い前処理の名前でも通る")):
            try:
                ex._check_cond({"role": "trigger", "form": "cross",
                                "material": [_pre6[0][0], _broke],
                                "value": {"direction": "up"}}, "", "T1-C6c メタ確認", [])
                ng.append(f"T1-C6c 番人③: {_why}")
            except ex.RecipeError:
                pass
    # ── T1-C6c 番人③（2026-08-12（18回目）・段C の 4-2 で逆向きに書き換えた）─────────────────────
    #   直す前（2026-08-13）は「前処理つきの材料に分位を渡すと拒否される」を確かめていた
    #   ＝解決表が前処理を見ていなかったので、拒否が正しい状態だった（fail-closed）。
    #   いまは解決表が前処理を掛けてから分位を出すので、次の3つを確かめる。
    #     (a) 前処理つき ＋ 分位の条件を検証器が受け付ける
    #     (b) 解決表に「前処理込みの鍵」が立ち、その値が数値になる
    #     (c) メタ確認＝その値が「素の列の分位」と違う（同じなら解決表が前処理を掛けていない＝嘘の閾値）
    if _pre6:
        try:
            ex._check_cond({"role": "trigger", "form": "level", "side": "above",
                            "material": [_m_ok], "value": {"threshold_q": "q90"}}, "", "T1-C6c", [])
        except ex.RecipeError as e:
            ng.append(f"T1-C6c 番人③(a): 前処理つきの材料に分位を渡すと拒否される（{str(e)[:70]}）")
        _nm6 = ex._material_name(_m_ok, "")[1]
        _k6 = ex._mat_key(_m_ok, "")
        _n6 = 600
        _df6 = pd.DataFrame({
            "ts": pd.date_range("2024-03-01", periods=_n6, freq="5min"),
            "open": 60000.0, "high": 60010.0, "low": 59990.0, "close": 60000.0, "volume": 1.0,
        })
        # 波にする＝直前n本の最大値が いまの値より大きい所が多く出る（素の分位との差が見える）
        _df6[_nm6] = 50.0 + 45.0 * np.sin(np.arange(_n6) / 7.0)
        _rec6 = {
            "meta": {"strategy": "e38", "logic_id": "T1-C6c", "side": "SHORT", "lane": ""},
            "pre_filter": [],
            "entry": {"connective": {"all": [
                {"role": "trigger", "form": "level", "material": [_m_ok],
                 "side": "above", "value": {"threshold_q": "q90"}}]}},
            "exits": [], "position": {"mode": "separate", "max_adds": 1},
        }
        try:
            _qt6 = build_qtable(_df6, {}, [_rec6], ["q10", "q50", "q90"])
        except (SystemExit, ex.RecipeError) as e:
            _qt6 = None
            ng.append(f"T1-C6c 番人③(b): 前処理つきの分位の解決表が作れない（{str(e)[:70]}）")
        if _qt6 is not None:
            if _k6 not in _qt6:
                ng.append(f"T1-C6c 番人③(b): 解決表に前処理込みの鍵 {_k6} が無い（鍵={sorted(_qt6)}）")
            elif not np.isfinite(_qt6[_k6]["q90"]):
                ng.append(f"T1-C6c 番人③(b): 前処理つきの q90 が数値でない（{_qt6[_k6]['q90']}）")
            elif abs(float(_qt6[_k6]["q90"])
                     - float(np.quantile(_df6[_nm6].to_numpy(float), 0.9))) < 1e-9:
                ng.append("T1-C6c 番人③(c) メタ確認: 前処理つきの分位が素の列の分位と一致する"
                          "＝解決表が前処理を掛けていない（嘘の閾値になる）")

    # ── T1-C6d 前処理つきの組は クロス以外（差・タッチ）にも出る（2026-08-12（18回目）・段C の 4-2）──
    #   直す前は _pair_materials が「クロスのときだけ」前処理つきの組を足していた（分位が使えなかったため）。
    _pre6d = 0
    for i in range(200):
        try:
            _pr = _pair_materials(np.random.default_rng([89, 1, i]), pool, tfs_small,
                                  "trigger", _tbl5, lm, "diff")
        except (SampleError, KeyError):
            continue
        if any(m.get("pre") for m in _pr):
            _pre6d += 1
    if _pre6d == 0:
        ng.append("T1-C6d: 差（diff）で『素の列 × 前処理を掛けた同じ列』の組を200回 引いて1本も作らない"
                  "（クロス以外に前処理つきが出ない＝4-2 の絞り外しが効いていない）")

    # ── T1-C6e 水準の前処理（部品 ts_rank・ts_std・2026-08-12（18回目）・段C の 4-2 の本体）──────────
    #   ①案の中に「水準 ＋ 単位の変わる前処理」の条件が実際に出る（＝使える部品になっている）
    #   ②その条件を検証器が受け付ける（分位の閾値つき）
    #   ③メタ確認＝列2本の形に渡すと拒否される（単位が違うものを大小で比べさせない）
    _lv_ops = ex.pre_ops(same_unit=False)
    if not _lv_ops:
        ng.append("T1-C6e: 単位の変わる前処理の部品が1つも登録されていない（ts_rank・ts_std）")
    else:
        _seen_lv: set = set()
        for r in structs:
            _cs, _dd = ex._walk(r["entry"]["connective"])
            for c in list(_cs) + list(r.get("pre_filter", [])):
                for cc in [c] + ([c["inner"]] if c.get("inner") else []):
                    for m in (cc.get("material") or []):
                        p = m.get("pre")
                        if p and p["op"] in _lv_ops:
                            _seen_lv.add((cc["form"], p["op"]))
        if not _seen_lv:
            ng.append(f"T1-C6e 番人①: 案 {len(structs)} 本に「水準 ＋ {_lv_ops}」の条件が1本も出ない"
                      "（部品を登録しただけで、生成器が作れていない＝使えない部品）")
        _m_lv = {"family": "RSI", "param": 14, "tf": "5m", "pre": {"op": _lv_ops[0], "n": 20}}
        try:
            ex._check_cond({"role": "trigger", "form": "level", "side": "above",
                            "material": [_m_lv], "value": {"threshold_q": "q80"}}, "", "T1-C6e", [])
        except ex.RecipeError as e:
            ng.append(f"T1-C6e 番人②: 水準の前処理つきの条件を検証器が拒否する（{str(e)[:70]}）")
        try:
            ex._check_cond({"role": "trigger", "form": "diff", "side": "above",
                            "material": [{"family": "RSI", "param": 14, "tf": "5m"}, _m_lv],
                            "value": {"threshold_q": "q50"}}, "", "T1-C6e メタ確認", [])
            ng.append(f"T1-C6e 番人③: 列2本の形（差）に単位の変わる前処理 {_lv_ops[0]} を渡しても通る"
                      "（単位が違うものを大小で比べている）")
        except ex.RecipeError:
            pass

    # ── T1-C6f 材料2本の組み方（部品 div・corr・2026-08-12・段C の C-6）──────────────────────
    #   ①案の中に「割り算」「相関」の条件が実際に出る（＝表に登録しただけで終わっていない）
    #   ②その条件を検証器が受け付ける（分位の閾値つき）
    #   ③解決表に組み方ごとの鍵が立ち、その値が「引き算の分位」と違う
    #     （同じなら解決表が組み方を掛けていない＝嘘の閾値になる。4-2 の番人③(c) と同じ考え方）
    #   ④メタ確認＝書き忘れ（相関に窓が無い／割り算に閾値が無い）と、表に無い組み方が拒否されること
    _ma6f = {"family": "RSI", "param": 7, "tf": "5m"}
    _mb6f = {"family": "RSI", "param": 21, "tf": "5m"}
    _seen_op6f: set = set()
    for r in structs:
        _cs6f, _dd6f = ex._walk(r["entry"]["connective"])
        for c in list(_cs6f) + list(r.get("pre_filter", [])):
            for cc in [c] + ([c["inner"]] if c.get("inner") else []):
                if cc.get("form") == "diff":
                    _seen_op6f.add(ex._pair_op_of(cc.get("value") or {}))
    for _o6f in ex.pair_ops():
        if _o6f not in _seen_op6f:
            ng.append(f"T1-C6f 番人①: 案 {len(structs)} 本に材料2本の組み方 {_o6f} が1本も出ない"
                      "（部品を登録しただけで、生成器が作れていない＝使えない部品）")
    _val6f = {"sub": {"threshold_q": "q50"},
              "div": {"op": "div", "th": {"threshold_q": "q50"}},
              "corr": {"op": "corr", "n": 20, "th": {"threshold_q": "q50"}}}
    for _o6f, _v6f in _val6f.items():
        try:
            ex._check_cond({"role": "trigger", "form": "diff", "side": "above",
                            "material": [_ma6f, _mb6f], "value": _v6f}, "", "T1-C6f", [])
        except ex.RecipeError as e:
            ng.append(f"T1-C6f 番人②: 組み方 {_o6f} の条件を検証器が拒否する（{str(e)[:70]}）")
    _len6f = 600
    _df6f = pd.DataFrame({
        "ts": pd.date_range("2024-03-01", periods=_len6f, freq="5min"),
        "open": 60000.0, "high": 60010.0, "low": 59990.0, "close": 60000.0, "volume": 1.0,
    })
    _na6f = ex._material_name(_ma6f, "")[1]
    _nb6f = ex._material_name(_mb6f, "")[1]
    # 2本の波の位相をずらす＝引き算・割り算・相関の3つが別々の分布になる（同じなら比べる意味が無い）
    _df6f[_na6f] = 50.0 + 30.0 * np.sin(np.arange(_len6f) / 7.0)
    _df6f[_nb6f] = 50.0 + 30.0 * np.sin(np.arange(_len6f) / 7.0 + 1.1)
    _qv6f: dict = {}
    for _o6f, _v6f in _val6f.items():
        _rec6f = {
            "meta": {"strategy": "e38", "logic_id": "T1-C6f", "side": "SHORT", "lane": ""},
            "pre_filter": [],
            "entry": {"connective": {"all": [
                {"role": "trigger", "form": "diff", "material": [_ma6f, _mb6f],
                 "side": "above", "value": _v6f}]}},
            "exits": [], "position": {"mode": "separate", "max_adds": 1},
        }
        _k6f = ex._pair_key(ex._mat_key(_ma6f, ""), ex._mat_key(_mb6f, ""), _o6f,
                            _v6f.get("n") if ex.PAIR_OPS[_o6f]["needs_n"] else None)
        try:
            _qt6f = build_qtable(_df6f, {}, [_rec6f], ["q10", "q50", "q90"])
        except (SystemExit, ex.RecipeError) as e:
            ng.append(f"T1-C6f 番人③: 組み方 {_o6f} の分位の解決表が作れない（{str(e)[:70]}）")
            continue
        if _k6f not in _qt6f:
            ng.append(f"T1-C6f 番人③: 解決表に組み方 {_o6f} の鍵 {_k6f} が無い（鍵={sorted(_qt6f)}）")
        elif not np.isfinite(_qt6f[_k6f]["q50"]):
            ng.append(f"T1-C6f 番人③: 組み方 {_o6f} の q50 が数値でない（{_qt6f[_k6f]['q50']}）")
        else:
            _qv6f[_o6f] = float(_qt6f[_k6f]["q50"])
    for _o6f in ("div", "corr"):
        if _o6f in _qv6f and "sub" in _qv6f and abs(_qv6f[_o6f] - _qv6f["sub"]) < 1e-9:
            ng.append(f"T1-C6f 番人③ メタ確認: 組み方 {_o6f} の分位が引き算の分位と一致する"
                      "＝解決表が組み方を掛けていない（嘘の閾値になる）")
    for _bad6f, _why6f in (({"op": "corr", "th": {"threshold_q": "q50"}}, "相関に窓（value.n）が無くても通る"),
                           ({"op": "div"}, "割り算に閾値（value.th）が無くても通る"),
                           ({"op": "mul", "th": {"threshold_q": "q50"}}, "表に無い組み方 mul が通る")):
        try:
            ex._check_cond({"role": "trigger", "form": "diff", "side": "above",
                            "material": [_ma6f, _mb6f], "value": _bad6f}, "", "T1-C6f メタ確認", [])
            ng.append(f"T1-C6f 番人④: {_why6f}")
        except ex.RecipeError:
            pass

    # ── T1-C6g 何本前に成立したか（部品 barssince・2026-08-12・段C の C-6）─────────────────────
    #   ①案の中に barssince の条件が実際に出る（＝表に登録しただけで終わっていない）
    #   ②生成器が作るのは above だけ（below は within_n と同じもの＝二重に作らない・正規形）
    #   ③その条件を検証器が受け付ける
    #   ④メタ確認＝side を書き忘れた barssince は拒否されること（数える形なので向きが要る）
    _bs_sides: list = []
    for r in structs:
        _cs6g, _dd6g = ex._walk(r["entry"]["connective"])
        for c in list(_cs6g) + list(r.get("pre_filter", [])):
            if c.get("form") == "barssince":
                _bs_sides.append(c.get("side"))
    if not _bs_sides:
        ng.append(f"T1-C6g 番人①: 案 {len(structs)} 本に『何本前に成立したか』（barssince）が1本も出ない"
                  "（部品を登録しただけで、生成器が作れていない＝使えない部品）")
    if any(s != "above" for s in _bs_sides):
        ng.append(f"T1-C6g 番人②: 生成器が barssince の above 以外を作った（{sorted(set(_bs_sides))}）"
                  "＝within_n と同じ条件を2通りで作っている（正規形）")
    _in6g = {"role": "trigger", "form": "level", "side": "above",
             "material": [_ma6f], "value": {"threshold_q": "q80"}}
    try:
        ex._check_cond({"role": "trigger", "form": "barssince", "side": "above",
                        "inner": _in6g, "material": [], "value": {"n": 6}}, "", "T1-C6g", [])
    except ex.RecipeError as e:
        ng.append(f"T1-C6g 番人③: barssince の条件を検証器が拒否する（{str(e)[:70]}）")
    try:
        ex._check_cond({"role": "trigger", "form": "barssince",
                        "inner": _in6g, "material": [], "value": {"n": 6}}, "", "T1-C6g メタ確認", [])
        ng.append("T1-C6g 番人④: side の無い barssince が通る（数える形なので向きが要る）")
    except ex.RecipeError:
        pass

    _lm6 = dict(lm)
    _lm6["count_range"] = [1, 1]                      # 条件1本＝引き金だけ＝経路を増やす余地が無い
    _s6 = []
    for i in range(30):
        try:
            _s6.append(sample_structure(np.random.default_rng([77, 1, i]), _lm6, pool, tfs_small))
        except (SampleError, ex.RecipeError):
            continue
    if _s6 and any(int(k) >= 2 for k in structure_breakdown(_s6, cat_total)["経路数の分布"]):
        ng.append("T1-C6b メタ確認: 条件を1本に絞っても経路が2本以上 出る"
                  "（経路の数を条件の本数から決める仕組みが効いていない）")

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
    df_m = df                        # ★A-2b＝列は その場で作る（先に全部 作らない）
    s4 = pd.Timestamp(df["ts"].iloc[0]).normalize()
    e4 = s4 + pd.Timedelta(days=10)               # 丸1日×10日＝日次分割（daily_net）の定義と整合させる
    q1 = build_qtable(df_m, geo, structs[:20], quantile_list(lm), s4, e4)
    q2 = build_qtable(df_m, geo, structs[:20], quantile_list(lm), s4, e4)
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
                    name = ex.build_name(m)
                    # ★2026-08-13（段A の A-4）＝照合の単位を「列名そのもの」から
                    #   「指標の種類が表に在るか ＋ 数字が範囲の中か」に変えた（表そのものは変えていない）。
                    #   判定の実物は gen_signal_families._part_allowed 1か所だけ（写しを作らない）。
                    ok13, why13 = gsf13._part_allowed(name, parts13)
                    if not ok13:
                        v.append(why13)
                    elif m["tf"] not in tfs13_all:
                        v.append(f"表に無い時間足 {name}__{m.get('tf')}")
                    if rr["tfs"] is not None and m["tf"] not in rr["tfs"]:
                        v.append(f"{role} に時間足 {m['tf']}（対応表の外）")
                    if (name, m["tf"]) in banned13:
                        v.append(f"禁止3 の組 {name}__{m['tf']}")
            mats = c.get("material") or []
            if (c.get("side") and c["form"] in ex.forms_where("needs_side")   # ★性質表から（M2-2-3b）
                    and role in ("env", "sufficiency")
                    and any(_kubun_of(m) == "順張り値" for m in mats)):
                want = "below" if side_v == "SHORT" else "above"
                if c["side"] != want:
                    v.append(f"DC1 違反（{role}・順張り値・side {c['side']}）")
            if (role == "trigger" and c["form"] == "level" and mats and "family" in mats[0]
                    and iref.FAMILY_LINEAGE[mats[0]["family"]]["k"] == "オシレーター"):
                q13 = str(c.get("value", {}).get("threshold_q", ""))
                # ★2026-08-15（段A の A-5-3）＝照合を「一覧に在るか」から「帯の中か」に変えた。
                #   帯の両端は 表の逐語（高分位 q70〜q90／低分位 q10〜q30）の 最小 と 最大＝
                #   CC は数字を作っていない。承認済みの表そのものは1バイトも変えていない（A-4 と同じ）。
                def _in_band13(q, band):
                    if not (q.startswith("q") and q[1:].isdigit()):
                        return False
                    nb = [int(str(x).lstrip("q")) for x in band]
                    return min(nb) <= int(q[1:]) <= max(nb)
                if side_v == "SHORT" and not (c.get("side") == "above"
                                              and _in_band13(q13, tbl13["quantile_grid_hi"])):
                    v.append(f"DC2 違反（SHORT・side {c.get('side')}・{q13}）")
                if side_v == "LONG" and not (c.get("side") == "below"
                                             and _in_band13(q13, tbl13["quantile_grid_lo"])):
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
                 if k in ("hold_frac_range", "giveback_range", "loss_cap_range", "ladder_steps_range")})
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
    # ★A-2b＝列は その場で作る（先に全部 作らない）
    geo14 = _geo_of(df14)          # 本走と同じ作り方（帯の4隅・中央・帯内位置%・W%）
    fired14: set = set()
    # ★玉の動きで切り替わる枝の名前は、承認済みの表から機械で引く（手で一覧を書かない・2026-08-12）。
    #   直す前は手書きの8件で、そのうち3件（TIMEDOWN／REVIND／MAECUTADDS）が表に存在しない名前だった。
    #   ＝MAECUT_ADDS（表の正しい名前）を、この番人は一度も見ていなかった。
    state_names = {k for k, v in et14["branch_types"].items() if v.get("fire")}
    if not state_names:
        t14.append("表から『玉の動きで切り替わる枝』を1つも引けない（表の読み方が実物とずれている）")
    _miss14 = state_names - {b["name"] for st in sts14 for b in st["exits"]}
    picked14 = None
    for st in sts14:
        if not (state_names & {b["name"] for b in st["exits"]}):
            continue
        st_reasons = {b["reason"] for b in st["exits"] if b["name"] in state_names and b.get("fire")}
        # ★どの枝で決済したかを決済の名前で見分けるので、他の枝も出す名前は除く。
        #   例＝利確の名前（TP_FILLED）は、いつも置く利確の枝も出す＝状態機械の枝の発火とは言えない。
        st_reasons -= {b["reason"] for b in st["exits"]
                       if not (b["name"] in state_names and b.get("fire"))}
        if not st_reasons:
            continue
        # ★発火の証拠は「枝が在ると出て、枝を壊すと消える」名前だけ（2026-08-12・厳しくした）。
        #   直す前は「出た」だけで合格にしていた。実行器は建値待機の中で自分でも BE_EXIT を出す
        #   （engine_tuner_exec.py:1344）ので、「出た」だけでは枝が発火した証拠にならない。
        broke = copy.deepcopy(st)
        for b in broke["exits"]:
            if b["name"] in state_names and b.get("fire"):
                # 発火の条件を「絶対に満たさないもの」に丸ごと置き換える（保有 10^6 分＝約2年）。
                # 条件の中身を1本ずつ弄る形だと、値を持たない形（傾き・交差）が壊れず残る。
                b["fire"] = {"all": [_state_cond("hold_min", "above", {"n": 10 ** 6})]}
        try:
            r14 = ex.run_recipe(df14, st, qtable=build_qtable(df14, geo14, [st], quantile_list(lm14)))
            r14b = ex.run_recipe(df14, broke,
                                 qtable=build_qtable(df14, geo14, [broke], quantile_list(lm14)))
        except BaseException:
            continue
        tr = r14[0] if isinstance(r14, tuple) else r14
        trb = r14b[0] if isinstance(r14b, tuple) else r14b
        if tr is None or not len(tr):
            continue
        got = {t.get("exit_reason") for t in (tr.to_dict("records") if hasattr(tr, "to_dict") else tr)}
        gotb = {t.get("exit_reason") for t in (trb.to_dict("records") if hasattr(trb, "to_dict") else (trb or []))}
        only = (got & st_reasons) - gotb                  # 枝を壊すと消える＝枝が出した証拠
        if only:
            fired14 |= only
            picked14 = st
            break
    if not fired14:
        t14.append("状態機械の枝が『在ると出て、壊すと消える』決済を1つも出さなかった"
                   "（完了の線④＝発火した売買記録が出ること）")
    ng += [f"T14: {x}" for x in t14]

    # ══ T16 部分利確の段数（まこさん決定 2026-08-15「3回以上に分けられるようにする」）══════
    #   ①本走の設定で 3段 が実際に作られる ②どの段も 取引所の最小注文サイズ を割らない
    #   ③割合の上限を上げると、機械が出す最大の段数が減る（メタ確認＝計算が生きている証拠）
    t16: list[str] = []
    lm16 = dict(KENSHU_LIMITS)
    lm16.update({k: v for k, v in json.loads(LIMITS_PATH.read_text(encoding="utf-8")).items()
                 if k in ("ladder_steps_range", "frac_range")})
    mf16 = ladder_min_frac()
    seen16: dict = {}
    for i in range(200):
        rng = np.random.default_rng([16, 8, i])
        try:
            st = sample_structure(rng, lm16, pool, tfs_small, side="SHORT", logic_id="S3")
        except SampleError:
            continue
        lad = [b for b in st["exits"] if str(b["name"]).startswith("TP1")]
        seen16[len(lad)] = seen16.get(len(lad), 0) + 1
        rest = 1.0                                  # 実行器と同じ数え方＝割合は「残っている量」に掛かる
        for b in lad:
            f = float(b["size_ratio"])
            if rest * f < mf16 - 1e-12 or rest * (1.0 - f) < mf16 - 1e-12:
                t16.append(f"最小注文サイズを割る段が出た（案 {i}・枝 {b['name']}・残り {rest:.5f}・割合 {f}）")
                break
            rest *= (1.0 - f)
        if t16:
            break
    if max(seen16, default=0) < 3:
        t16.append(f"3段の部分利確が1本も出ない（段数の分布 {dict(sorted(seen16.items()))}）")
    if max_ladder_steps(lm16) < 3:
        t16.append(f"機械が出す最大の段数が 3 未満（{max_ladder_steps(lm16)}）")
    _wide16 = dict(lm16); _wide16["frac_range"] = {"lo": 25.0, "hi": 90.0, "kind": "float", "dec": 1}
    if not (max_ladder_steps(_wide16) < max_ladder_steps(lm16)):
        t16.append("割合の上限を 90% に上げても最大の段数が減らない（最小注文サイズの計算が効いていない）")
    ng += [f"T16: {x}" for x in t16]

    # ══ T17 閾値の段（分位）の範囲（段A の A-5-3・2026-08-15）═══════════════════════════
    #   ①本走の設定で、直す前の9段（q10・q20…q90）に無い分位が実際に作られる
    #   ②範囲の外の分位（q95・q5）と、書き方が違うもの（q12.5・"50"）は検証器が止める
    #   ③範囲を狭めると、その外の分位が作られなくなる（メタ確認＝範囲が効いている証拠）
    #   ★実物のファイルは1バイトも書き換えません（読み込んだ中身の写しを壊すだけ）。
    t17: list[str] = []
    lm17 = dict(KENSHU_LIMITS)
    lm17["quantile_range"] = json.loads(LIMITS_PATH.read_text(encoding="utf-8"))["quantile_range"]
    lm17.pop("quantile_grid", None)
    old9 = {10, 20, 30, 40, 50, 60, 70, 80, 90}          # 直す前の9段
    seen17: set[int] = set()
    slot17 = {"範囲方式": 0, "メニュー方式": 0}
    for i in range(60):
        rng = np.random.default_rng([17, 5, i])
        try:
            st = sample_structure(rng, lm17, pool, tfs_small, side="SHORT", logic_id="S3")
        except SampleError:
            continue
        for _p, _sp in value_slots(st, lm17):
            slot17["メニュー方式" if _sp.get("kind") == "cat" else "範囲方式"] += 1
        def _walk17(c):
            v = c.get("value") or {}
            for holder in (v, v.get("lo") or {}, v.get("hi") or {}, v.get("th") or {}):
                q = holder.get("threshold_q") if isinstance(holder, dict) else None
                if isinstance(q, str) and q.startswith("q") and q[1:].isdigit():
                    seen17.add(int(q[1:]))
            if c.get("inner"):
                _walk17(c["inner"])
        _cs17, _d17 = ex._walk(st["entry"]["connective"])       # 条件は入口の木の中に在る
        for _c in list(_cs17) + list(st.get("pre_filter", [])):
            _walk17(_c)
    fresh17 = sorted(seen17 - old9)
    if not fresh17:
        t17.append(f"直す前の9段に無い分位が1つも出ない（出た分位 {sorted(seen17)}）")
    lo17, hi17 = q_range_of(lm17)
    for bad in (f"q{hi17 + 5}", f"q{max(lo17 - 5, 0)}", "q12.5", "50"):
        ok17, _why17 = q_in_range(lm17, bad)
        if ok17:
            t17.append(f"範囲の外・書き方違いの分位 {bad} を通した（範囲 q{lo17}〜q{hi17}）")
    narrow17 = dict(lm17)
    narrow17["quantile_range"] = {"lo": 40, "hi": 45, "kind": "int"}
    if q_in_range(narrow17, f"q{hi17}")[0]:
        t17.append("範囲を q40〜q45 に狭めても、その外の分位が通る（範囲が効いていない）")
    ng += [f"T17: {x}" for x in t17]

    # ══ T18 入れ子の「ずらす本数」の範囲（段A の A-5-4・2026-08-15）═════════════════════
    #   ①コードに直に書いた数字が消えた（`materials.md` の ★3 の場所3 が 0件 になる根拠）
    #   ②本走の設定で作られる本数が、全部 範囲の中に入っている
    #   ③その本数が第2段の『動かせる値』に出る（生成のときの1回で固定されない）
    #   ④範囲を 0〜0 に狭めると 1 が出なくなる（メタ確認＝範囲が効いている証拠）
    #   ★実物のファイルは1バイトも書き換えません（読み込んだ中身の写しを壊すだけ）。
    t18: list[str] = []
    # ★探す文字を組み立ててから探す＝この行そのものに反応しないため（自己一致を避ける）。
    _needle18 = "rng." + "choice([0, 1])"
    if _needle18 in pathlib.Path(__file__).read_text(encoding="utf-8"):
        t18.append(f"コードに直に書いた {_needle18} が残っている（設定ファイルへ出していない）")
    lm18 = dict(KENSHU_LIMITS)
    _lim_file18 = json.loads(LIMITS_PATH.read_text(encoding="utf-8"))
    lm18["nest_offset_range"] = _lim_file18["nest_offset_range"]
    lo18, hi18 = int(lm18["nest_offset_range"]["lo"]), int(lm18["nest_offset_range"]["hi"])
    seen18: set[int] = set()
    slot18 = 0

    def _walk18(c):
        v = c.get("value") or {}
        if c.get("form") in ex.NEST_FORMS and "offset" in v:
            seen18.add(int(v["offset"]))
        if c.get("inner"):
            _walk18(c["inner"])
    for i in range(60):
        rng = np.random.default_rng([18, 7, i])
        try:
            st = sample_structure(rng, lm18, pool, tfs_small, side="SHORT", logic_id="S3")
        except SampleError:
            continue
        slot18 += sum(1 for _p, _sp in value_slots(st, lm18) if _p.endswith(".value.offset"))
        _cs18, _d18 = ex._walk(st["entry"]["connective"])
        for _c in list(_cs18) + list(st.get("pre_filter", [])):
            _walk18(_c)
    if not seen18:
        t18.append("案60本で入れ子の条件が1つも作られず、ずらす本数を確かめられなかった")
    if any(x < lo18 or x > hi18 for x in seen18):
        t18.append(f"範囲の外のずらす本数が作られた（出た本数 {sorted(seen18)}・範囲 {lo18}〜{hi18}）")
    if seen18 and slot18 == 0:
        t18.append("ずらす本数が第2段の『動かせる値』に出ない（生成のときの1回で固定される）")
    for bad18 in (hi18 + 2, 0.5):
        if num_in_range(lm18, "nest_offset_range", bad18)[0]:
            t18.append(f"範囲の外・整数でないずらす本数 {bad18} を通した（範囲 {lo18}〜{hi18}）")
    narrow18 = dict(lm18)
    narrow18["nest_offset_range"] = {"lo": 0, "hi": 0, "kind": "int"}
    if num_in_range(narrow18, "nest_offset_range", hi18)[0] and hi18 != 0:
        t18.append(f"範囲を 0〜0 に狭めても {hi18} が通る（範囲が効いていない）")
    ng += [f"T18: {x}" for x in t18]

    # ══ T19 同じ種なら同じ案が出る（2026-08-16 新設）════════════════════════════════════
    #   何を守るか＝engine_tuner の探索が再現できる状態。
    #   直す前は 型の表の「系統の一覧」が set で、Python が走らせるたびに文字列の置き場所を
    #   変えるため、候補の並びが実行ごとに違った＝同じ種でも別の案が出ていた
    #   （実測 2026-08-16＝案20本の md5 が PYTHONHASHSEED 0・1・2 で3通りとも別物）。
    #   ①並びの決まったもの（同じ種→同じ案）になっていること
    #   ②わざと set に戻すと並びが変わりうること（メタ確認＝実物のファイルは書き換えない）
    t19: list[str] = []
    _tbl19 = load_signal_table()
    for _rn, _r in _tbl19["roles"].items():
        if isinstance(_r["lineages"], (set, frozenset)):
            t19.append(f"役割 {_rn} の系統の一覧が set のまま（走らせるたびに並びが変わる）")
    def _plans19(tb) -> str:
        outs = []
        for i in range(12):
            try:
                outs.append(json.dumps(sample_structure(np.random.default_rng([19, 3, i]), lm18, pool,
                                                        tfs_small, side="SHORT", logic_id="S3"),
                                       ensure_ascii=False, sort_keys=True, default=str))
            except SampleError:
                outs.append("SampleError")
        return hashlib.md5("\n".join(outs).encode("utf-8")).hexdigest()[:16]
    _keep19 = {k: v["lineages"] for k, v in _tbl19["roles"].items()}
    _h19a = _plans19(_tbl19)
    if _plans19(_tbl19) != _h19a:
        t19.append("同じ種なのに、続けて2回 作った案が違う（再現できない）")
    try:                                          # メタ確認＝並びを崩すと案が変わりうる
        for _k, _v in _keep19.items():
            _tbl19["roles"][_k]["lineages"] = tuple(reversed(_v))
        if _plans19(_tbl19) == _h19a:
            t19.append("系統の並びを逆にしても案が同じ＝並びが案に効いていない（検査が無意味）")
    finally:
        for _k, _v in _keep19.items():            # 読み込んだ写しを元に戻す
            _tbl19["roles"][_k]["lineages"] = _v
    ng += [f"T19: {x}" for x in t19]

    # ══ T20 案1本が拒否されても走行を止めない（2026-08-16 新設・A-1a-0 の1番）════════════
    #   何を守るか＝探索の走行が、1本の案のせいで丸ごと死なないこと。
    #   直す前は 第1段（run_trial の呼び出し）と第2段が囲われておらず、解決表に鍵の無い案が
    #   1本 混ざると `--selftest` が8回中4回 丸ごと止まりました（worklog 20260816 §4）。
    #   ①本物の拒否（壊したレシピ）で (None, 理由) が返り、例外が外へ出ない
    #   ②走れた案では (結果, None) が返る（＝止めすぎていないことのメタ確認）
    #   ③拒否でない例外（ValueError）は握りつぶさず上へ投げる（＝本当の不具合を隠さない）
    #   ④走行の本体が、第1段と第2段の両方で囲いのある形（run_trial_guarded）を呼んでいる
    t20: list[str] = []
    _t20s, _t20e = pd.Timestamp("2024-03-01"), pd.Timestamp("2024-04-01")
    _r20, _w20 = run_trial_guarded(pd.DataFrame(), {"壊れたレシピ": 1}, {}, judge, _t20s, _t20e)
    if _r20 is not None or not _w20:
        t20.append("壊したレシピを渡しても (None, 理由) が返らない（拒否を捕まえていない）")
    elif reject_code(_w20) == _w20[:20]:
        t20.append(f"拒否の理由から短い名前を取り出せない（理由={_w20[:60]}）")
    _keep20 = globals()["run_trial"]
    try:
        globals()["run_trial"] = lambda *a, **k: {"total": 12.0, "n": 3, "per_day": 0.1,
                                                  "t": pd.DataFrame(), "rep": {}}
        _r20b, _w20b = run_trial_guarded(pd.DataFrame(), {}, {}, judge, _t20s, _t20e)
        if _r20b is None or _w20b is not None:
            t20.append("走れた案なのに落としている（止めすぎ）")

        def _boom20(*a, **k):
            raise ValueError("これは拒否ではない本当の不具合")
        globals()["run_trial"] = _boom20
        try:
            run_trial_guarded(pd.DataFrame(), {}, {}, judge, _t20s, _t20e)
            t20.append("拒否でない例外（ValueError）まで握りつぶした＝本当の不具合を隠す")
        except ValueError:
            pass
    finally:
        globals()["run_trial"] = _keep20
    _src20 = "\n".join(ln.split("#", 1)[0] for ln in inspect.getsource(run_generation).splitlines())
    _bare20 = len(re.findall(r"(?<!_)run_trial\(", _src20))
    _guard20 = len(re.findall(r"run_trial_guarded\(", _src20))
    if _guard20 < 2:
        t20.append(f"走行の本体で囲いのある形を呼んでいるのが {_guard20} か所（第1段・第2段の2か所が要る）")
    if _bare20 > 2:
        t20.append(f"走行の本体に囲いの無い run_trial の呼び出しが {_bare20} か所"
                   "（確認窓の1走の2か所だけのはず）")
    ng += [f"T20: {x}" for x in t20]

    # ══ T21 選んだ値の前後（段A の A-7・2026-08-16 新設・B8 の材料）═══════════════════════
    #   何を守るか＝「選んだ値の1刻み前と1刻み後」を、設定ファイルの宣言から機械で作れること。
    #   ①レシピの中の いまの値を読める（read_slots）＝書く側（apply_slots）と同じ道を通る
    #   ②読んだ値を書き戻すと、そのまま同じ値が読み出せる（往復で崩れない）
    #   ③前後の点が実際に作られ、動かした値だけが変わる（ほかの値は1つも動かない）
    #   ④範囲の外は作らない・メニューは対象外（理由つきで残る）＝tuner_judgement 側の番人 ⑲㉒ と対
    t21: list[str] = []
    import tuner_judgement as _tj21
    _lm21 = dict(KENSHU_LIMITS)
    _lm21["quantile_range"] = json.loads(LIMITS_PATH.read_text(encoding="utf-8"))["quantile_range"]
    _lm21.pop("quantile_grid", None)
    _st21 = None
    for _i in range(60):
        try:
            _st21 = sample_structure(np.random.default_rng([21, 5, _i]), _lm21, pool,
                                     tfs_small, side="SHORT", logic_id="S3")
            break
        except SampleError:
            continue
    if _st21 is None:
        t21.append("検収に使う案を1本も作れなかった")
    else:
        _sl21 = value_slots(_st21, _lm21)
        _cur21 = read_slots(_st21, _sl21)
        if len(_cur21) != len(_sl21):
            t21.append(f"値スロット {len(_sl21)} 件のうち {len(_cur21)} 件しか読めない（read_slots）")
        # ② 往復＝読んだ値をそのまま書き戻しても同じものが読める
        if read_slots(apply_slots(_st21, _cur21), _sl21) != _cur21:
            t21.append("読んだ値を書き戻すと別の値になる（read_slots と apply_slots が食い違う）")
        # ③ 前後の点＝動かした値だけが変わる
        _pt21, _sk21 = _tj21.neighbor_points(dict(_sl21), _cur21, {})
        if not _pt21:
            t21.append(f"前後の点が1つも作れない（スロット {len(_sl21)} 件・理由 {dict(_sk21)}）")
        for _p in _pt21[:5]:
            _after = read_slots(apply_slots(_st21, {_p["name"]: _p["value"]}), _sl21)
            _moved = {k for k in _cur21 if _after.get(k) != _cur21[k]}
            if _moved != {_p["name"]}:
                t21.append(f"{_p['name']}{_p['dir']} を動かしたら、ほかの値まで動いた（{sorted(_moved)}）")
                break
            if _after[_p["name"]] != _p["value"]:
                t21.append(f"{_p['name']}{_p['dir']} の値が書き込まれていない")
                break
        # ④ 範囲の外は作らない（メタ確認＝わざと1点しか無い範囲にすると前後が0点になる）
        _sl21b = [(p, ({**s, "lo": s["hi"]} if s.get("kind") in ("int", "q") else s))
                  for p, s in _sl21]
        _pt21b, _ = _tj21.neighbor_points(dict(_sl21b),
                                          {p: (s["hi"] if s.get("kind") == "int"
                                               else (f"q{s['hi']}" if s.get("kind") == "q"
                                                     else _cur21.get(p)))
                                           for p, s in _sl21b}, {})
        if _pt21b:
            t21.append(f"下限＝上限に狭めたのに前後の点が {len(_pt21b)} 点 作られた（範囲を見ていない）")
    ng += [f"T21: {x}" for x in t21]

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
    print(f"  T16 部分利確の段数（まこさん決定 2026-08-15「3回以上に分けられるようにする」）: "
          f"案200本の段数の分布 {dict(sorted(seen16.items()))}"
          f" ／ 最小注文サイズ（玉の {mf16 * 100:.3f}%）を割る段 0 本"
          f" ／ 機械が出す最大の段数 {max_ladder_steps(lm16)} 段"
          f"（割合の上限を 90% にすると {max_ladder_steps(_wide16)} 段＝メタ確認）")
    print(f"  T17 閾値の段（分位）の範囲（段A の A-5-3）: 案60本で出た分位 {len(seen17)} 種類"
          f"（うち直す前の9段に無いもの {len(fresh17)} 種類・例 {fresh17[:8]}）"
          f" ／ 範囲の外（q{hi17 + 5}・q{max(lo17 - 5, 0)}）と書き方違い（q12.5・50）は4通りとも止めた"
          f" ／ 範囲を q40〜q45 に狭めると q{hi17} が通らなくなる（メタ確認）"
          f" ／ 第2段の値スロット {slot17}")
    print(f"  T18 入れ子のずらす本数の範囲（段A の A-5-4）: コードの直書き 0 件"
          f" ／ 案60本で出た本数 {sorted(seen18)}（範囲 {lo18}〜{hi18}）"
          f" ／ 第2段の値スロットに {slot18} 件 出た"
          f" ／ 範囲の外（{hi18 + 2}）と整数でない（0.5）は2通りとも止めた"
          f" ／ 範囲を 0〜0 に狭めると {hi18} が通らなくなる（メタ確認）")
    print(f"  T19 同じ種なら同じ案が出る（2026-08-16）: 系統の一覧は並びの決まったもの"
          f" ／ 案12本の md5 {_h19a}（続けて2回 とも同じ）"
          f" ／ 並びを逆にすると案が変わる（メタ確認）")
    print(f"  T20 案1本が拒否されても走行を止めない（2026-08-16）: 壊したレシピは"
          f" 理由 {reject_code(_w20)} で落として先へ進む ／ 走れた案は落とさない（止めすぎない）"
          f" ／ 拒否でない例外（ValueError）は握りつぶさず上へ投げる（メタ確認）"
          f" ／ 走行の本体の囲い {_guard20} か所・囲い無し {_bare20} か所（確認窓の1走だけ）")
    print(f"  T21 選んだ値の前後（段A の A-7・B8 の材料）: 値スロット {len(_sl21) if _st21 else 0} 件を"
          f" 読み書きの往復で確認 ／ 前後の点 {len(_pt21) if _st21 else 0} 点"
          f"（動かした値だけが変わる） ／ 下限＝上限に狭めると 0 点になる（メタ確認）"
          f" ／ 作らなかった理由 {len(_sk21) if _st21 else 0} 件は画面に残す")
    # ── T22 分位の解決表が、条件の在る所を全部 歩く（2026-08-21・48回目・M2-2-8 で新設）─────────
    #   ★なぜ足したか。この日、次の2つが数え上げから丸ごと漏れていた（実測で見つけた）。
    #     ①**状態を保つ形（hysteresis）の on と off の中**
    #     ②**判定の中身（meta.regime.build）の木の中**
    #     どちらも「分位で閾値を書くと、解決表に鍵が入らない」＝走らせた瞬間に止まる。
    #     ＝M2-2-5 で足した形が1回も走らず、M2-1-4 の承認材料の逐語
    #       「束の中の値が分位の範囲で書かれ、engine_tuner の探索の対象になる」も効いていなかった。
    #   ★メタ確認＝歩く所を1つ外すと、この番人が落ちること（＝番人が本当に効いている）。
    def _lv22(fam, p, tf, q):
        return {"role": "env", "form": "level", "side": "above", "value": {"threshold_q": q},
                "material": [{"family": fam, "param": p, "tf": tf}]}
    _r22 = {"meta": {"lane": "", "regime": {"name": "range", "entry_col": "x", "build": {
                "entry": {"out_col": "t22_built", "tree": {"all": [
                    _lv22("RSI", 14, "5m", "q30"),
                    {"bool_col": "rg5_uptrend", "want": False},
                    {"not": _lv22("DI差", 14, "1h", "q30")}]}},
                "block": None}}},
            "entry": {"connective": {"all": [
                _lv22("ROC", 6, "5m", "q50"),
                {"form": "hysteresis", "on": _lv22("ADX", 14, "15m", "q70"),
                 "off": _lv22("ADX", 14, "15m", "q40"), "value": {"n": 288}}]}}}
    _k22 = needed_qkeys([_r22])
    _want22 = {"入口のふつうの条件": "ROC6__5m", "状態を保つ形の中": "ADX14__15m",
               "判定の中身の中": "RSI14__5m", "判定の中身の否定の中": "DI差14__1h"}
    _miss22 = [f"{lbl}（{key}）" for lbl, key in _want22.items() if key not in _k22]
    if _miss22:
        ng.append(f"T22: 分位の解決表に鍵が入らない所がある: {_miss22}"
                  "（そこで分位を使うと、走らせた瞬間に『解決表に無い』で止まる）")
    _r22b = json.loads(json.dumps(_r22))          # メタ確認＝判定の中身を消すと鍵が減ること
    _r22b["meta"]["regime"]["build"] = None
    _k22b = needed_qkeys([_r22b])
    if "RSI14__5m" in _k22b or "DI差14__1h" in _k22b:
        ng.append("T22 メタ確認: 判定の中身を消しても鍵が残る＝この番人は中身を見ていない")

    # ── T22b 連動する閾値（ref）の上下の挟みを分位で書いたときの鍵（2026-08-21・M2-2-8）──────────
    #   ★直す前＝この条件は value に threshold_q を持たない（ref を持つ）ので鍵が1つも入らず、
    #     走らせた瞬間に「分位の解決表に無い」で止まった。挟みは条件の材料と同じ鍵で解く。
    _r22c = {"meta": {"lane": ""}, "entry": {"connective": {"all": [{
        "role": "env", "form": "level", "side": "below",
        "value": {"ref": {"family": "ATR%", "param": 14, "tf": "1h"}, "mult": 0.5,
                  "clip_lo": {"threshold_q": "q10"}, "clip_hi": {"threshold_q": "q90"}},
        "material": [{"family": "fractal安値距離%", "param": 2, "tf": "1h"}]}]}}}
    _k22c = needed_qkeys([_r22c])
    if "fractal安値距離%(2)__1h" not in _k22c:
        ng.append("T22b: 連動する閾値の挟み（clip_lo・clip_hi）を分位で書くと鍵が入らない"
                  "（走らせた瞬間に『解決表に無い』で止まる）")
    _r22d = json.loads(json.dumps(_r22c))         # メタ確認＝挟みを外すと鍵が要らなくなる
    for _s in ("clip_lo", "clip_hi"):
        _r22d["entry"]["connective"]["all"][0]["value"].pop(_s)
    if needed_qkeys([_r22d]):
        ng.append("T22b メタ確認: 挟みを外しても鍵が残る＝この番人は挟みを見ていない")

    # ── T22c 分位の解決表が「状態に入って以降」の前処理を解ける（2026-08-21・M2-2-8）──────────
    #   ★直す前＝解決表を作る所が状態の列（df）を渡しておらず、
    #     「基準にする状態の列がデータにありません」で止まった＝M2-2-5 で足した前処理3つが
    #     分位と一緒には1回も使えなかった。
    _n22 = 400
    _idx22 = pd.date_range("2026-03-01", periods=_n22, freq="5min")
    _c22 = 100.0 + np.sin(np.arange(_n22) / 7.0)
    _df22 = pd.DataFrame({"ts": _idx22, "open": _c22, "high": _c22 + 0.2, "low": _c22 - 0.2,
                          "close": _c22, "volume": 1.0})
    _df22["t22_state"] = (np.arange(_n22) % 80) < 40          # 入ったり出たりする状態の列
    _r22e = {"meta": {"lane": ""}, "entry": {"connective": {"all": [{
        "role": "env", "form": "level", "side": "above", "value": {"threshold_q": "q50"},
        "material": [{"family": "RSI", "param": 14, "tf": "5m",
                      "pre": {"op": "since_min", "state": "t22_state"}}]}]}}}
    try:
        _q22 = build_qtable(_df22, {}, [_r22e], quantile_list(lm))
        if not _q22:
            ng.append("T22c: 状態に入って以降の前処理で、分位の解決表が空になった")
    except Exception as _e22:
        ng.append(f"T22c: 状態に入って以降の前処理で、分位の解決表を作れない: {type(_e22).__name__} {_e22}")
        _q22 = {}

    print(f"  T22 分位の解決表が条件の在る所を全部 歩く（2026-08-21・M2-2-8）: 鍵 {len(_k22)} 件"
          f"（入口・状態を保つ形の中・判定の中身の中・否定の中の4か所とも入る）"
          f" ／ 判定の中身を消すと鍵が {len(_k22) - len(_k22b)} 件 減る（メタ確認）")
    print(f"  T22b 連動する閾値の挟み（clip）を分位で書いたときの鍵: {len(_k22c)} 件"
          f" ／ 挟みを外すと 0 件になる（メタ確認）")
    print(f"  T22c 状態に入って以降の前処理で、分位の解決表を作れる: 鍵 {len(_q22)} 件"
          f"（直す前は『基準にする状態の列がデータにありません』で止まった）")

    # ══ T23 材料の順位（M2-3-4・2026-08-22 → ★2026-08-23 K を無くした版・まこさん承認 327e7f80008f…）══════════
    #   ①`ranked_materials` の並びが |分離力−0.5| の降順 ②location の1位＝実物で確かめた S-Rタッチ数(144,0.006)__15m
    #   ③型の表の外（役割に使えない系統・禁止3）は `_ranked_material_at` が飛ばす ④`regime_draw_order` が決まった並び
    global _MATERIAL_RANKING, _RANK_PATH
    try:
        _rk = load_material_ranking()
        _lst23 = ranked_materials("location")
        _dist23 = [abs(a - 0.5) for _c, a, _l, _h in _lst23]
        if _dist23 != sorted(_dist23, reverse=True):
            ng.append("T23①: 並びが分離力の強い順（|分離力−0.5| の降順）になっていない")
        if _lst23[0][0] != "S-Rタッチ数(144,0.006)__15m":
            ng.append(f"T23②: location の1位が実物と違う: {_lst23[0]}（成績表を作り直したなら この見本も直す）")
        _tbl23 = load_signal_table()
        _pool23, _tfs23, _ = material_pool()
        _m1, _d1 = _ranked_material_at("location", 1, _tfs23, _tbl23)
        if ex.build_name(_m1) + "__" + _m1["tf"] != _d1["col"] or _d1["rank"] != 1:
            ng.append(f"T23③: 1位の材料が列名と食い違う: {_m1} / {_d1}")
        _ord = [regime_draw_order(i) for i in range(6)]
        if _ord != [(1, 1, "above"), (1, 1, "below"), (1, 2, "above"), (1, 2, "below"), (2, 1, "above"), (2, 1, "below")]:
            ng.append(f"T23④: 案の並びが決まった順でない: {_ord}")
        _all23 = {f"{p}__{t}" for p in _tbl23["parts"] for t in _tbl23["tfs"]}
        _listed23 = {c for bl in _rk["順位"].values() for bn in bl.values()
                     for got in bn.values() for c, _a in got}
        print(f"  T23 材料の順位: location の並び {len(_lst23)} 本（降順）／ 1位 {_lst23[0][0]}（分離力 {_lst23[0][1]}）"
              f" ／ 案の並び {_ord[:4]}… ／ ★突き合わせ＝型の表の列 {len(_all23)} 本のうち順位に載っているのは"
              f" {len(_all23 & _listed23)} 本（載っていない {len(_all23 - _listed23)} 本＝役割の枠の外と、測れなかった列）")
    except SystemExit as _e23:
        ng.append(f"T23: 順位の読み出しが止まった: {_e23}")
    # ③fail-closed＝成績表が無いと止まる（パスを一時的に無い場所へ差し替えて確かめ、必ず戻す）
    _keep_rank, _keep_path = _MATERIAL_RANKING, _RANK_PATH
    try:
        _MATERIAL_RANKING = None
        _RANK_PATH = _RANK_PATH.with_name("material_ranking__無いはず.json")
        try:
            load_material_ranking()
            ng.append("T23③: 成績表が無いのに止まらない（fail-closed が効いていない）")
        except SystemExit:
            pass
    finally:
        _MATERIAL_RANKING, _RANK_PATH = _keep_rank, _keep_path

    # ══ T24 場面の判定の束を組む（M2-5-1・2026-08-23 まこさん承認 2b56024e711f…）══════════════════
    #   ①72番の直し＝hysteresis を必ず引かせても SampleError にならず、on と off の分位が違う
    #   ②レンジの束 N本 が実行器の検査（G5・G6・G7）を通る本数（M2-5-3 の数え方の土台・数字は決めない）
    #   ③わざと A（K-6）・C（K-5）・hysteresis（K-3）を外した束は G7 で落ちる（番人）
    #   ④材料が順位の上位 K の中から出ている＝K=1 なら1列しか候補に無い ⑤K が範囲の外なら止まる（T23②と同じ口）
    try:
        _tbl24 = load_signal_table()
        _pool24, _tfs24, _ = material_pool()
        _lm24, _w24 = load_limits()
        _lm24 = resolve_hold_range(_lm24, "e38")
        _lim24 = {"n_min": None, "p_max": _lm24.get("p_max"), "count_range": _lm24.get("count_range"),
                  "role_max": _lm24.get("role_max"), "depth_max": _lm24.get("depth_max"),
                  "k_max": _lm24.get("k_max"), "r_min": _lm24.get("r_min")}

        class _R24:                                   # hysteresis を必ず引く rng（①の道具）
            def __init__(self, s): self.r = np.random.default_rng(s)
            def choice(self, a, *k, **kw):
                a = list(a)
                return "hysteresis" if "hysteresis" in a else self.r.choice(a, *k, **kw)
            def __getattr__(self, n): return getattr(self.r, n)
        _c24 = _make_cond(_R24(1), "env", _lm24, _pool24, _tfs24, set(), {}, _tbl24, "SHORT")
        if _c24.get("form") != "hysteresis" or _c24["on"]["value"]["threshold_q"] == _c24["off"]["value"]["threshold_q"]:
            ng.append(f"T24①: hysteresis が組めない・または on と off の分位が同じ: {_c24}")
        _n24, _ok24 = 100, 0
        _rej24: Counter = Counter()
        _r24 = None
        _orders24 = []
        for _i in range(_n24):
            _rng = np.random.default_rng([24, 1, _i])
            try:
                _rr = sample_structure(_rng, _lm24, _pool24, _tfs24, side="SHORT", logic_id=f"T24_{_i}",
                                       build_regime=True, regime_order_n=_i)
                ex.validate_recipe(_rr, limits=_lim24)
                _ok24 += 1
                _r24 = _r24 or _rr
                _dr = _rr["meta"]["regime_draw"]
                _orders24.append((_i, (_dr["B"]["rank"], _dr["C"]["rank"])))
                # ★同じ order_n なら同じ指標（乱数でない）
                _rr2 = sample_structure(np.random.default_rng([99, 1, _i]), _lm24, _pool24, _tfs24, side="SHORT",
                                        logic_id="x", build_regime=True, regime_order_n=_i)
                if _rr2["meta"]["regime_draw"]["B"]["col"] != _dr["B"]["col"] or _rr2["meta"]["regime_draw"]["C"]["col"] != _dr["C"]["col"]:
                    ng.append(f"T24②: 同じ案の番号 {_i} なのに指標が変わった（乱数で引いている）")
            except SampleError as _e:
                _rej24[f"サンプル不能: {str(_e)[:30]}"] += 1
            except ex.RecipeError as _e:
                _rej24[str(_e)[:40]] += 1
        if _ok24 == 0 or _r24 is None:
            ng.append(f"T24②: レンジの束が1本も検査を通らない: {dict(_rej24)}")
        else:
            _hy = _r24["meta"]["regime"]["build"]["entry"]["tree"]["all"][0]
            _on, _off = _hy["on"]["all"], _hy["off"]["any"]
            # ★外すときは on と off の両方から外す（off に同じ部品が残ると G7 はそちらで満たされる）
            for _lbl, _mk in (("A（K-6 帯の幅）", lambda t: {"all": [{"form": "hysteresis", "on": {"all": _on[1:]}, "off": {"any": _off[1:]}, "value": _hy["value"]}]}),
                              ("C（K-5 否定）", lambda t: {"all": [{"form": "hysteresis", "on": {"all": _on[:2]}, "off": {"any": _off[:2]}, "value": _hy["value"]}]}),
                              ("hysteresis（K-3）", lambda t: {"all": _on})):
                _bad = json.loads(json.dumps(_r24))
                _bad["meta"]["regime"]["build"]["entry"]["tree"] = _mk(None)
                try:
                    ex.validate_recipe(_bad, limits=_lim24)
                    ng.append(f"T24③: {_lbl} を外した束が拒否されない")
                except ex.RecipeError as _e:
                    if "G7" not in str(_e)[:12]:
                        ng.append(f"T24③: {_lbl} を外した束が G7 以外で止まった: {str(_e)[:60]}")
            if _r24["meta"]["regime_draw"]["B"]["rank"] != 1 or _r24["meta"]["regime_draw"]["C"]["rank"] != 1:
                ng.append(f"T24④: 0番目の案が (1,1) でない: {_r24['meta']['regime_draw']}")
            _bad24 = [(i, got, regime_draw_order(i)[:2]) for i, got in _orders24 if got != regime_draw_order(i)[:2]]
            if _bad24:
                ng.append(f"T24④: 案の (B,C) の順位が並びどおりでない（番号, 実物, 期待）: {_bad24[:4]}")
        print(f"  T24 場面の判定の束（レンジ）: ①hysteresis on {_c24['on']['value']} → off {_c24['off']['value']}"
              f"（n={_c24['value']['n']}）／ ②{_n24}本 組んで検査（G5・G6・G7）を通った {_ok24}本"
              f"（通らなかった内訳 {dict(_rej24) or 'なし'}）／ ③A・C・hysteresis を外すと G7 で落ちる"
              f" ／ ④0番目は (1,1)・並びどおり・同じ番号なら同じ指標 ／ 引いた記録の例 {(_r24 or {}).get('meta', {}).get('regime_draw')}")
    except SystemExit as _e24:
        ng.append(f"T24: 途中で止まった: {_e24}")

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
                         base=base, rules=rules, rfloor=rfloor, build_regime=bool(a.build_regime))
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
    ap.add_argument("--build-regime", action="store_true",
                    help="★M2-5-1＝全案に場面の判定の束（meta.regime.build）を付ける（既定 off＝従来どおり）")
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


# ── H2 実行時の守り（2026-08-16 まこさん GO「H2 完全化」の層3・穴④）──────────────────
#    自分のコードに未来参照の典型（shift にマイナスの数字・rolling の center を True）が無いことを、
#    読み込みのたびに ratchet_guards で機械確認する。違反が入ると import の瞬間に止まる＝
#    偽の数字を出す前に落ちる。説明文では誤発火しない（行内コメントを外してから見る）。
import pathlib as _h2_pathlib                            # noqa: E402
import ratchet_guards as _h2_rg                          # noqa: E402
_h2_rg.assert_no_future_ref(_h2_pathlib.Path(__file__).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
