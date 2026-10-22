#!/usr/bin/env python3
"""engine_tuner_gen.py — 売買ルールの案を作るプログラム（第1段＝条件の形を作る → 第2段＝有望な形の数字を TPE で詰める）
★2026-09-13 に書き直した（まこさん指示）。元の文（2026-08-01・commit 863935a）は「第1段＝構造をランダムに作る」「まこさん承認済みの計画」だったが、その承認は後の決定で上書きされた＝乱数で案の形を作ることは 2026-08-08 に「論外」（違反の記録 #14）、乱数そのものは 2026-09-09 に禁止（恒久の決まり67番。乱数はこの commit で入った）。
  ・第1段＝条件の形（役割・本数・つなぎ方・形・材料）を作る。★いまのコードは、入口と出口の条件をまだ乱数で作っている＝この古い計画のまま動いている。外すのは入口＝M3・出口＝M4（まこさんが決めた順番）。場面の判定の束だけは乱数を使わない（成績表の順位から組む・M2-E-2）。
    ★「乱数で作る」を承認済みの根拠として読まない。新しく書き足さない。どの関数が何回 乱数を使うかは、設計書 acceptance.md §2-4 の自動生成の表を見る（数を手で書かない）。
  ・DSR（試した回数が多いほど合格を厳しくする仕組み）の分散・p値・PBO は、第1段の試行だけから作る（CP1 提案4(c)・監査 4-16／4-21）。
  ・第2段＝有望な形の数字を TPE で詰める。結果は統計判定に使わない（値の微調整だけ・CP1 解A）。★恒久の決まり67番は TPE を「試行の成績に基づく＝対象外」と書いているが、TPE の部品（optuna 4.3.0）は最初の10回を乱数で選び、その後も候補を乱数で引く（optuna の samplers/_tpe/sampler.py:281・317・478）。これを乱数の禁止に当てるかは まこさんが決める（2026-09-13 に分かった・まだ決まっていない）。
  ・段の最後に BH 法の偽発見率の検定＝たまたま良く見える案が混ざる割合を抑える（CP1 提案4(e)・監査 4-20）。
  ・値動きの大きさ（ATR%）の帯ごとに、いまの設定より悪くなった案を1本ずつ落とす選別（CP1 の層化・監査 4-22）。
  ・落とした試行の出力は、理由と一緒に残す（黙って消さない・L-330／L-356）。途中で止まった探索は続きから再開できる（R12）＝journal に済んだ試行を記録し再利用する。
  ・閾値の分位 threshold_q の解決表（値決め窓・探索開始時に1回固定・設計書 §5-4）の実装もここ。
  ★BH 法・帯ごとの選別・解決表の関数は乱数を使わない（bh_select・strat_gate・build_qtable の中に乱数の語 0件・2026-09-13 に数えた）。

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
import time                                    # ★2026-09-11（手順6）＝段ごとの記録に掛かった時間を入れる
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
        # ★指標のオン・オフの印（M2-C-2・呼ぶ側 1/5＝案を作る・材料の候補）。
        #   判定は実行器の1つの関数だけ＝ここに条件を書き写さない。
        if not ex.indicator_enabled(ent["family"]):
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
      ＝RSI なら、カタログの数字（5・7・9・14・21）から 5〜21 の整数が全部 試せる（ただし RSI は下の設定の範囲 2〜21 が優先される）。
      **上限を広げる（例＝RSI を 200 まで）かどうかは、まこさんが決めることです。**
      ★2026-10-06（工事 m2c15-param-values-20261006）から、下の設定の範囲に、修正対応表の範囲（まこさんが OK した選び方で
      出たもの）をプログラムが写して書いています。設定の範囲が在る種類は、そちらが優先されます（CC は数字を書いていない）。

    ★設定の範囲の置き場所＝recipes/search_limits.json の material_param_ranges。
      形＝{"RSI": [{"kind": "int", "lo": 30, "hi": 50}]}（軸＝名前の {} の数だけ並べる）。
      出どころ＝まこさんの逐語（2026-08-07・engine_tuner_defects.md の D14 ⑥）
      「疑似シミュで出た値の前後あたりで範囲を事前に指定して（例えば３０〜５０の間とか）探す」。
      設定に無い種類は、上のカタログ由来の範囲を使います。名前に出さない引数の範囲は、ここには書けません（工事2）。

    戻り＝{指標の種類: {"axes": [{"kind": "int"|"float", "lo": x, "hi": y, "dec": 小数の桁数}, ...],
                        "src": "catalog"|"makosan"}}

    ★正直に書く限界＝軸どうしの関係（MACD の 短い方 < 長い方 のような決まり）は、この表に持っていません。
      ★2026-10-06 から設定の範囲を書いたので、軸どうしの範囲が重なる種類が在る（工事 m2c15-param-values-20261006 の
      設計書に一覧）。その決まりが要るかを1件ずつ決めます。
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
        # ★指標のオン・オフの印（M2-C-2・呼ぶ側 2/5＝案を作る・パラメータの範囲）。
        #   使わない指標の範囲は作らない＝範囲の表そのものが小さくなる。
        if not ex.indicator_enabled(fam):
            continue
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
    # ── 設定の範囲（material_param_ranges）が在れば、そちらを使う（CC は数字を書かない）──
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


# ★4つの要素の使い方を強制する印（58回目・2026-08-24・まこさん承認 9d085e391c3e…）
#   まこさんの1行（逐語 2026-08-24）＝
#     「指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを組み合わせ、
#       Entry/Exit やレジーム判定などの条件を作る」
#   守るべき6つのうち、2番（閾値が範囲から）と3番（パラメータが範囲から）を、この印で強制する。
#   ★印は検査のためだけに付ける。検査が終わったら strip_marks() が外すので、
#     実行器にも案のハッシュ値（recipe_hash）にも渡らない＝挙動は変わらない。
#   ★印の持たせ方（2026-08-24・2回 試して決めた）。
#     1回目＝辞書に鍵を足す → 実行器が「値に未知のフィールド」で拒否した
#       （engine_tuner_exec.py:652・自己テスト T1-C6 で発覚）。
#     2回目＝辞書の「種類」で印にする → 案を組み立てる途中で消えた
#       （json.loads(json.dumps(…)) が6か所・{**m, …} が1か所・copy.deepcopy が2か所）。
#     決めた形＝1回目に戻し、案を返す直前に strip_marks() で外す。
#       外したあとは普通の辞書なので、実行器にも案のハッシュ値にも影響しない。
PARAM_SRC = "_param_src"      # 材料に付ける「範囲から引いた」印
Q_SRC = "_q_src"              # 閾値に付ける「範囲から引いた」印


NUM_SRC = "_num_src"          # 出口の枝などの数字に付ける印（引いた瞬間の範囲を写す・59回目）
LIN_SRC = "_lineage_src"      # 出口の指標の条件に付ける「この枝が使える系統」の印（59回目）
_MARK_KEYS = (PARAM_SRC, Q_SRC, NUM_SRC, LIN_SRC)
_TFS_ALL: set | None = None


# ★59回目（2026-08-25・設計書 v2＝監査 cp6 NO-GO の直し）＝印の付け方を根本から変えた。
#   v58 の印は「作った側が無条件に押す印」で、決まった一覧の数字にも「範囲から」と付いていた
#   （監査 Q2 根拠(2)＝出口の材料 1333・1373 行で実際に起きていた）。
#   これから＝材料・閾値・数字は **「引く関数」でしか作れない**（外から数字を渡す口を無くす）。
#   印の中身は「引いた瞬間の範囲（lo・hi）」＝検査は「印が在るか」ではなく
#   「値がその範囲の中か・その範囲が いまの正本と合うか」を見る（assert_provenance）。
#   ★正直に書く限界＝Python では、作者が新しい書き方を1行 足す道は塞げない。
#     だから静的検査（--lint-provenance）で「引く関数の外で材料を作る所」を数えて 0 を確かめる。


def _allowed_tfs() -> set:
    """使える時間足の全部（observe_config.json の timeframes）。1回だけ読む。"""
    global _TFS_ALL
    if _TFS_ALL is None:
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            import observe_diag as _od
            _TFS_ALL = {str(t) for t in _od.load_config()["timeframes"]}
    return _TFS_ALL


def _check_tf(tf, table: dict | None) -> None:
    """4番＝時間足が使えるものか（案を作る瞬間・S2）。"""
    if str(tf) not in _allowed_tfs():
        raise SampleError(f"[4要素ゲート] 使えない時間足 {tf}（使えるのは {sorted(_allowed_tfs())}）")
    if table is not None and str(tf) not in set(table["tfs"]):
        raise SampleError(f"[4要素ゲート] 型の表に無い時間足 {tf}（表の時間足＝{table['tfs']}）")


def _mat_drawn(rng, family: str, tf: str, ranges: dict | None = None, *,
               table: dict | None = None, **kw) -> dict:
    """材料の辞書を作る唯一の入口＝数字は **この関数の中で** 範囲から引く（外から数字を渡せない）。

    印＝引いた瞬間の範囲（軸ごとの lo・hi）と出どころ（catalog／makosan）。
    """
    ranges = ranges if ranges is not None else material_ranges()
    _check_tf(tf, table)
    spec = ranges.get(family)
    if spec is None:
        raise SampleError(f"[4要素ゲート] 範囲の表（カタログ）に無い指標: {family}")
    param = draw_param(rng, family, ranges)
    m = {"family": family, "param": param, "tf": str(tf),
         PARAM_SRC: {"kind": "param", "src": spec["src"],
                     "axes": [{"lo": a["lo"], "hi": a["hi"], "kind": a["kind"]} for a in spec["axes"]]}}
    m.update(kw)
    return m


def _mat_from_col(col: str, family: str, tf: str, ranges: dict | None = None, *,
                  table: dict | None = None, **kw) -> dict:
    """成績表の列の名前から、材料の辞書を作る（★数字を乱数で引かない・2026-09-11・手順9）。

    なぜ要るか（恒久の決まり67番＝乱数は使わない・まこさん指示 2026-09-09
      「乱数は禁止用語にするレベル。絶対に使うな」）
      直す前は `_mat_drawn` が範囲から**乱数で**数字を引いていた（RSI なら 7〜21 のどれか）。
      ★成績表に載っている列は、**その数字で実際に測った結果**なので、その列の数字を
        そのまま使えば、乱数も私（CC）の判断も要らない。

    ★成績表は前のカタログの数字で作られているので、列の数字が範囲の外のことがある（ROC3・ROC6 ほか）。
      この関数は範囲を照らさない。段の候補では _group_usable_col が範囲の外の列を外す（監査 CP63 の修正1・2026-10-07）。
    ★数字を新しく作っていない＝列の名前に書いてある数字を読み取るだけ。
    """
    ranges = ranges if ranges is not None else material_ranges()
    _check_tf(tf, table)
    spec = ranges.get(family)
    if spec is None:
        raise SampleError(f"[4要素ゲート] 範囲の表（カタログ）に無い指標: {family}")
    base = str(col).split("__")[0]                 # ★列の名前＝カタログ名__時間足
    ent, params = iref.find(base)
    if ent is None or params is None:
        raise SampleError(f"成績表の列の名前から数字を取り出せない: {col}（fail-closed）")
    param = params[0] if len(params) == 1 else tuple(params)
    m = {"family": family, "param": param, "tf": str(tf),
         PARAM_SRC: {"kind": "param", "src": spec["src"],
                     "axes": [{"lo": a["lo"], "hi": a["hi"], "kind": a["kind"]} for a in spec["axes"]]}}
    m.update(kw)
    return m


def _group_usable_col(col: str, family: str, tf: str, ranges: dict | None = None,
                      table: dict | None = None) -> bool:
    """**その列の数字で作った材料**が使えるか（禁止3＝標本不足に当たらないか）。2026-09-11・手順9。

    ★なぜ要るか（実測 2026-09-11）＝`_group_usable` は「**範囲のどれか1つの数字**で使えるか」
      を見る。直す前は数字を範囲から乱数で引いていたので、その判定で足りた（使えない数字を
      引いたら引き直していた）。**いまは成績表の列の数字を1つだけ使う**ので、
      「その列の数字で使えるか」を見ないと、順位に残った組で束が組めなくなる。
      **実測＝直す前は100本中80本 組めたものが、この判定を入れる前は 32本 まで落ちた**
      （env の1位 `DI差×1d` の列の数字が禁止3 だった）。
    """
    try:
        m = _mat_from_col(col, family, tf, ranges, table=table)
    except SampleError:
        return False
    # ★2026-10-07（監査 CP63 の修正1・まこさん「全部直す」＝案 A）＝その列の数字が範囲の外なら、段の候補に使わない。
    #   直す前は禁止3（標本不足）だけを見ていた。成績表（material_ranking.json）は前のカタログの数字で作られているので、
    #   範囲の外の列（ROC3・ROC6 ほか）が順位に残り、案を作った後の出どころの検査（assert_provenance の param_in_range）で止まった。
    if not param_in_range(family, m["param"], ranges)[0]:
        return False
    return not _banned_pair(m, table)


def _mat_two_drawn(rng, family: str, tf: str, ranges: dict | None = None, *, table: dict | None = None):
    """同じ指標の数字違い2本（短い方が先）。範囲が狭くて2本 引けなければ None。"""
    m1 = _mat_drawn(rng, family, tf, ranges, table=table)
    for _ in range(20):
        m2 = _mat_drawn(rng, family, tf, ranges, table=table)
        if str(m2["param"]) != str(m1["param"]):
            a_, b_ = sorted((m1, m2), key=lambda m: _pkey(m["param"]))   # ★短い方を先に置く（まこさん OK 2026-08-11）
            return [a_, b_]
    return None


def _mat_pair_drawn(rng, fa: str, fb: str, tf: str, ranges: dict | None = None, *, table: dict | None = None):
    """同じライブラリ関数から出た別の指標2本（共通の軸は同じ値にそろえる＝Stoch%K14 と Stoch%D14）。

    そろえた結果が相手の範囲の外に出るときだけ、それぞれ別に引いた値のまま。
    """
    ranges = ranges if ranges is not None else material_ranges()
    ma, mb = _mat_drawn(rng, fa, tf, ranges, table=table), _mat_drawn(rng, fb, tf, ranges, table=table)
    la, lb = _as_param_list(ma["param"]), _as_param_list(mb["param"])
    k = min(len(la), len(lb))
    if k:
        if len(la) <= len(lb):
            lb[:k] = la[:k]
        else:
            la[:k] = lb[:k]
        ca, cb = _from_param_list(la), _from_param_list(lb)
        if param_in_range(fa, ca, ranges)[0] and param_in_range(fb, cb, ranges)[0]:
            ma["param"], mb["param"] = ca, cb
    return [ma, mb]


def _mat_with_pre(m: dict, pre: dict) -> dict:
    """同じ材料に前処理を掛けたもの（数字は元の材料と同じ＝印もそのまま写す）。

    ★pre の中に印を置かない＝実行器は pre の鍵を厳密に見る（op・n・state 以外は拒否）。
      pre の数字の印は材料の側に「pre.n」の名前で持つ（assert_provenance が点つきの名前を辿る）。
    """
    out = dict(m)
    pre = dict(pre)
    mk = pre.pop(NUM_SRC, None)
    out["pre"] = pre
    if mk:
        merged = dict(out.get(NUM_SRC) or {})
        merged.update({f"pre.{k}": v for k, v in mk.items()})
        out[NUM_SRC] = merged
    return out


def _mat_fixture(family: str, param, tf: str, off_ok: bool = False, **kw) -> dict:
    """★自己テストの見本だけが使う材料（本走のコードからは呼ばない＝--lint-provenance が見張る）。

    印は本物の範囲を写す＝見本の数字が範囲の外なら作れない（見本が嘘の材料にならない）。

    ★off_ok（2026-09-04・設計書 iter="t25-fixture-off-20260904"・まこさん承認）＝
      印（indicator_switch.json）が「使わない」の指標の見本を作る道。印の審査（T33-b）を試すためだけに在る。
      印が「使う」の指標に off_ok=True を渡すと止まる（fail-closed）＝この道で範囲の検査を飛ばすことはできない。
      この fail-closed を機械で守るのは自己テストの T33-f だけ（SPEC は下線で始まる この関数を見ない）。
    """
    if off_ok:
        if ex.indicator_enabled(family):
            raise SampleError(f"[見本] {family} は印が「使う」＝off_ok の見本は作れない")
        m = {"family": family, "param": param, "tf": str(tf)}
        m.update(kw)
        return m
    ranges = material_ranges()
    spec = ranges.get(family)
    if spec is None:
        raise SampleError(f"[見本] 範囲の表に無い指標: {family}")
    ok, why = param_in_range(family, param, ranges)
    if not ok:
        raise SampleError(f"[見本] {why}")
    m = {"family": family, "param": param, "tf": str(tf),
         PARAM_SRC: {"kind": "param", "src": spec["src"], "fixture": True,
                     "axes": [{"lo": a["lo"], "hi": a["hi"], "kind": a["kind"]} for a in spec["axes"]]}}
    m.update(kw)
    return m


def _thr_drawn(rng, limits: dict, lo_min=None, hi_max=None) -> dict:
    """閾値（分位）の辞書を作る唯一の入口＝分位は **この関数の中で** 範囲から引く。印＝その範囲。"""
    lo, hi = q_range_of(limits, lo_min, hi_max)
    return {"threshold_q": draw_q(rng, limits, lo_min, hi_max), Q_SRC: {"kind": "q", "lo": int(lo), "hi": int(hi)}}


def _thr_fixed(limits: dict, lo_min=None, hi_max=None) -> dict:
    """閾値（分位）を1点に決める＝乱数を使わない（2026-09-11・手順9）。

    ★まこさん決定 2026-09-11（逐語）＝「じゃあ、まず１点でつくる」。
    ★どの1点か＝承認済みの範囲（`recipes/search_limits.json` の `quantile_range`）の真ん中。
      **私（CC）は数字を作っていない**＝両端は承認済みで、真ん中はその2つから決まる。
    ★9段（q10〜q90）に戻すときは、設定ファイルの `stage_limits.<段>.quantiles` に書けば足せる
      （設計書 4-9）。コードを変えない。
    ★印（Q_SRC）は `_thr_drawn` と同じものを書く＝範囲が記録に残る。
    """
    lo, hi = q_range_of(limits, lo_min, hi_max)
    return {"threshold_q": f"q{(int(lo) + int(hi)) // 2}",
            Q_SRC: {"kind": "q", "lo": int(lo), "hi": int(hi)}}


def _thr_band_drawn(rng, limits: dict) -> tuple[dict, dict]:
    """帯の下限・上限（下限＜上限）を範囲から引く（2つが同じ値にならない＝幅ゼロの帯を作らない）。"""
    lo, hi = q_range_of(limits)
    if hi - lo < 1:
        raise SampleError(f"帯を作れない（分位の範囲が q{lo}〜q{hi} で2つ選べない）")
    a = int(rng.integers(lo, hi))              # 下限＝上限より小さい所から引く
    b = int(rng.integers(a + 1, hi + 1))       # 上限＝下限より大きい所から引く
    mk = {"kind": "q", "lo": int(lo), "hi": int(hi)}
    return {"threshold_q": f"q{a}", Q_SRC: dict(mk)}, {"threshold_q": f"q{b}", Q_SRC: dict(mk)}


def _thr_fixture(q: str) -> dict:
    """★自己テストの見本だけが使う閾値（印は本物の分位の範囲・範囲の外なら作れない）。"""
    lm, _w = load_limits()
    ok, why = q_in_range(lm, q)
    if not ok:
        raise SampleError(f"[見本] {why}")
    lo, hi = q_range_of(lm)
    return {"threshold_q": str(q), Q_SRC: {"kind": "q", "lo": int(lo), "hi": int(hi), "fixture": True}}


def _nv(rng, limits: dict, key: str, field: str, *, lo_min=None, hi_max=None,
        scale=None, fn=None, as_int: bool = False) -> dict:
    """出口の枝などの数字を1つ 引いて、印つきで返す＝{field: 値, NUM_SRC: {field: 印}}。

    印の種類＝num（値そのもの）／linear（値＝引いた数×scale）／derived（fn で作る＝式は検査しない）。
    ★数字は **この関数の中で** 範囲から引く（外から数字を渡す口が無い）。
    """
    r = num_range_of(limits, key)
    lo = r["lo"] if lo_min is None else max(r["lo"], float(lo_min))
    hi = r["hi"] if hi_max is None else min(r["hi"], float(hi_max))
    raw = draw_num(rng, limits, key, lo_min, hi_max)
    if fn is not None:
        val, kind = fn(raw), "derived"
    elif scale is not None:
        val, kind = raw * float(scale), "linear"
    else:
        val, kind = raw, "num"
    if as_int:
        val = int(val)
    mark = {"kind": kind, "name": key, "lo": lo, "hi": hi, "raw": raw}
    if scale is not None:
        mark["scale"] = float(scale)
    return {field: val, NUM_SRC: {field: mark}}


def _nv_fixed(limits: dict, key: str, field: str, order_n: int, *, as_int: bool = True) -> dict:
    """範囲の中の値を、案の番号から決まった並びで決める＝乱数を使わない（2026-09-11・手順9）。

    ★並び＝範囲の下端から順に、案の番号のぶんだけ進む（端まで来たら下端へ戻る）。
      ＝**同じ案の番号なら、いつでも同じ値**になる（再現できる）。
    ★範囲は承認済み（`recipes/search_limits.json`）。**私（CC）は数字を作っていない。**
    ★印（NUM_SRC）は `_nv` と同じ形で書く＝範囲と、選んだ値が記録に残る。
    """
    r = num_range_of(limits, key)
    lo, hi = int(r["lo"]), int(r["hi"])
    if hi < lo:
        raise SampleError(f"範囲が逆さま: {key} の lo={lo} hi={hi}")
    val = lo + (int(order_n) % (hi - lo + 1))
    mark = {"kind": "num", "name": key, "lo": float(lo), "hi": float(hi), "raw": val}
    return {field: int(val) if as_int else val, NUM_SRC: {field: mark}}


def _loose_q_fixed(limits, q: str, side: str) -> str:
    """出る線（off）の分位＝入る線（on）の**隣の段**に決め打ちする（2026-09-11・手順9）。

    ★直す前は `_loose_q(rng, …)` が「緩い側の範囲の中から乱数で」引いていた。
      いまは隣の段（above なら1つ小さい・below なら1つ大きい）に決める＝乱数を使わない。
    ★緩める余地が無ければ、直す前と同じ理由で止まる（法則 C6 の②）。
    """
    lo, hi = q_range_of(limits)
    n = int(str(q).lstrip("q"))
    if side == "above":
        if n - 1 < lo:
            raise SampleError("hysteresis: 入る線が分位の下限＝出る線を緩められない（above）")
        return f"q{n - 1}"
    if n + 1 > hi:
        raise SampleError("hysteresis: 入る線が分位の上限＝出る線を緩められない（below）")
    return f"q{n + 1}"


def _iv(rng, limits: dict, field: str, n_min: int = 1, *, scale=None) -> dict:
    """使い方の中の本数（傾きを何本で見るか など）を1つ 引いて、印つきで返す。"""
    lo, hi = int_range_of(limits, n_min)
    raw = draw_int(rng, limits, n_min)
    val = raw * int(scale) if scale is not None else raw
    mark = {"kind": "linear" if scale is not None else "int", "name": "__int__", "lo": lo, "hi": hi, "raw": raw}
    if scale is not None:
        mark["scale"] = float(scale)
    return {field: val, NUM_SRC: {field: mark}}


def _iv_from(rng, field: str, lo: int, hi: int, name: str, *, scale=None) -> dict:
    """呼ぶ側が持つ整数の範囲（例＝保有時間の本数 hold_bars）から1つ 引いて、印つきで返す。"""
    raw = int(rng.integers(int(lo), int(hi) + 1))
    val = raw * int(scale) if scale is not None else raw
    mark = {"kind": "linear" if scale is not None else "int", "name": name, "lo": int(lo), "hi": int(hi), "raw": raw}
    if scale is not None:
        mark["scale"] = float(scale)
    return {field: val, NUM_SRC: {field: mark}}


def _nvs(*parts: dict) -> dict:
    """印つきの数字を複数まとめる（NUM_SRC の中身を併合する）。"""
    out: dict = {}
    marks: dict = {}
    for p in parts:
        for k, v in p.items():
            if k == NUM_SRC:
                marks.update(v)
            else:
                out[k] = v
    if marks:
        out[NUM_SRC] = marks
    return out


def _nvd(field: str, val, base_mark: dict) -> dict:
    """引いた数から計算で作った値（丸め・割り算など）＝印は「元の引いた数と範囲」を写し、式は検査しない（derived）。"""
    mk = dict(base_mark)
    mk["kind"] = "derived"
    return {field: val, NUM_SRC: {field: mk}}


def _walk_dicts(obj):
    """案の中の辞書を全部たどる（材料と閾値を見つけるため）。"""
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _walk_dicts(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk_dicts(v)


def _walk_materials(obj):
    """案の中の「material の一覧」に入っている辞書だけをたどる（geo・時刻・玉の状態の材料を見るため）。"""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "material" and isinstance(v, list):
                for m in v:
                    if isinstance(m, dict):
                        yield m
            yield from _walk_materials(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _walk_materials(v)


def _current_num_bounds(limits: dict, name: str) -> tuple[float, float]:
    """印の name に対応する、いまの正本の範囲（lo, hi）。"""
    if name == "__int__":
        lo, hi = int_range_of(limits, 1)
        return float(lo), float(hi)
    if name == "hold_bars":
        lo, hi = hold_bars(limits)
        return float(lo), float(hi)
    r = num_range_of(limits, name)
    return float(r["lo"]), float(r["hi"])


def assert_provenance(obj, limits: dict | None = None, ranges: dict | None = None,
                      table: dict | None = None, where: str = "案") -> None:
    """★値の出どころの検査（59回目）＝印が「在るか」ではなく、
       ①値が印の範囲の中か ②印の範囲が いまの正本（material_ranges／q_range_of／num_range_of）の中か
       ③時間足が使えるものか ④geo・時刻・玉の状態の材料が候補の表に在るか、を見る（fail-closed）。

    ★正直に書く限界＝「範囲の中の決まった値を手で入れる」形は、ここでは止まらない
      （値は範囲の中なので）。それは --lint-provenance（引く関数の外で材料を作る所＝0件）が止める。
    ★limits を渡されないとき＝「印の範囲が いまの正本の中か」（②）は見ない（正本が分からないため）。
      ①③④は見る。本走（run_generation）と --gate-matrix・--verify-provenance は必ず limits を渡す。
    """
    have_limits = limits is not None
    ranges = ranges if ranges is not None else material_ranges()
    qlo, qhi = q_range_of(limits) if have_limits else (None, None)
    tfs_ok = _allowed_tfs() if table is None else (_allowed_tfs() & {str(t) for t in table["tfs"]})

    def bad(msg: str):
        raise SampleError(f"[4要素ゲート] {where}: {msg}")

    for d in _walk_dicts(obj):
        if "family" in d and "tf" in d:
            # ★指標のオン・オフの印（M2-C-2・呼ぶ側 3/5＝案を審査する）。
            #   範囲の表からも消えているので 641行 でも落ちるが、そこだと「カタログに無い」という
            #   別の理由に見える。印で落ちたことが分かるように、先にここで止める。
            if not ex.indicator_enabled(d["family"]):
                bad(f"印が「使わない」の指標 {d['family']}（indicator_switch.json・M2-C-2）")
            src = d.get(PARAM_SRC)
            if not isinstance(src, dict) or src.get("kind") != "param":
                bad(f"範囲から引いた印の無い材料 {d.get('family')}(param={d.get('param')}, tf={d.get('tf')})")
            spec = ranges.get(d["family"])
            if spec is None:
                bad(f"範囲の表（カタログ）に無い指標 {d['family']}")
            axes = src.get("axes") or []
            if len(axes) != len(spec["axes"]):
                bad(f"{d['family']} の印の軸の数 {len(axes)} が正本 {len(spec['axes'])} と合わない")
            for i, (ar, ac) in enumerate(zip(axes, spec["axes"])):
                if float(ar["lo"]) < float(ac["lo"]) or float(ar["hi"]) > float(ac["hi"]):
                    bad(f"{d['family']} の {i + 1} 番目の印の範囲 {ar['lo']}〜{ar['hi']} が"
                        f"正本 {ac['lo']}〜{ac['hi']} の外")
            ok, why = param_in_range(d["family"], d.get("param"), {d["family"]: {"axes": axes, "src": "印"}})
            if not ok:
                bad(why)
            if str(d["tf"]) not in tfs_ok:
                bad(f"使えない時間足 {d['tf']}（使えるのは {sorted(tfs_ok)}）")
        if "threshold_q" in d:
            src = d.get(Q_SRC)
            if not isinstance(src, dict) or src.get("kind") != "q":
                bad(f"範囲から引いた印の無い閾値 {d.get('threshold_q')}")
            lo, hi = int(src["lo"]), int(src["hi"])
            if have_limits and (lo < qlo or hi > qhi):
                bad(f"閾値の印の範囲 q{lo}〜q{hi} が正本 q{qlo}〜q{qhi} の外")
            s = str(d["threshold_q"])
            if not (s.startswith("q") and s[1:].isdigit()) or not (lo <= int(s[1:]) <= hi):
                bad(f"閾値 {s} が印の範囲 q{lo}〜q{hi} の外")
        if isinstance(d.get(NUM_SRC), dict):
            for field, mk in d[NUM_SRC].items():
                cur, found = d, True
                for part in str(field).split("."):              # 点つきの名前（pre.n）は中を辿る
                    if not isinstance(cur, dict) or part not in cur:
                        found = False
                        break
                    cur = cur[part]
                if not found:
                    bad(f"印だけ在って値が無い数字 {field}")
                v = cur
                raw = float(mk["raw"])
                lo, hi = float(mk["lo"]), float(mk["hi"])
                if have_limits:
                    blo, bhi = _current_num_bounds(limits, str(mk["name"]))
                    if lo < blo or hi > bhi:
                        bad(f"{field} の印の範囲 {lo}〜{hi} が正本（{mk['name']}）{blo}〜{bhi} の外")
                if raw < lo or raw > hi:
                    bad(f"{field} の引いた数 {raw} が印の範囲 {lo}〜{hi} の外")
                kind = mk.get("kind")
                if kind in ("num", "int") and abs(float(v) - raw) > 1e-9:
                    bad(f"{field} の値 {v} が引いた数 {raw} と違う（印の後で書き換えられている）")
                if kind == "linear" and abs(float(v) - raw * float(mk["scale"])) > 1e-6:
                    bad(f"{field} の値 {v} が 引いた数 {raw}×{mk['scale']} と違う（印の後で書き換えられている）")
    for m in _walk_materials(obj):
        if "family" in m:
            continue
        # ★2026-09-06（監査 cp24 の §6-1・Critical・設計書 A-4）＝別枠3種は、型の表に加えて
        #   **オン・オフの印も見る**。直す前は型の表としか照らしておらず、まこさんが印から外しても
        #   案が通った（＝「一律で切り替えられる」を満たしていなかった）。
        #   判定は実行器の1つの関数だけを呼ぶ＝同じ判定をここに書き写さない。
        if "geo" in m:
            if table is not None and str(m["geo"]) not in set(table.get("geo_ok") or []):
                bad(f"候補の表に無いかたちの列 {m['geo']}（geo_ok={table.get('geo_ok')}）")
            elif not ex.geo_enabled(str(m["geo"])):
                bad(f"印が「使わない」のレンジ幾何の列 {m['geo']}（indicator_switch.json の geo_on）")
        elif "demand" in m:
            # ★2026-09-05（監査 cp21 の M1②）＝需給の列も、レンジ幾何と同じ形で型の表と照らす。
            #   直す前は、需給だけ型の表（extra_parts の demand）と1度も照らしていなかった。
            if table is not None and str(m["demand"]) not in set(table.get("demand_ok") or []):
                bad(f"候補の表に無い需給の列 {m['demand']}（demand_ok={table.get('demand_ok')}）")
            elif not ex.demand_enabled(str(m["demand"])):
                bad(f"印が「使わない」の需給の列 {m['demand']}（indicator_switch.json の demand_on）")
        elif "time" in m:
            # ★2026-09-06＝「時刻だけ」の決め打ちをやめ、型の表の time_ok と印で見る。
            #   直す前は 時刻 以外を全部 弾いていたので、曜日は表に在っても永久に使えなかった。
            if table is not None and str(m["time"]) not in set(table.get("time_ok") or []):
                bad(f"候補の表に無い時間帯の材料 {m['time']}（time_ok={table.get('time_ok')}）")
            elif not ex.time_enabled(str(m["time"])):
                bad(f"印が「使わない」の時間帯の材料 {m['time']}（indicator_switch.json の time_on）")
        elif "state" in m:
            if str(m["state"]) not in iref.STATE_COLS:
                bad(f"玉の状態の列に無い名前 {m['state']}（使えるのは {iref.STATE_COLS}）")


def assert_roles(obj, table: dict, where: str = "案") -> None:
    """★4つの要素が「役割に基づいて」使われているか（入口の条件・場面の判定）。

    まこさんの依頼（逐語 2026-08-24）＝
      「指標、閾値、パラメータ、時間足の**役割に基づき**、法則に則って４つを組み合わせ、
        Entry/Exit やレジーム判定などの条件を作る」
    型の表（signal_families_approved.txt）の「役割 → 使える系統」に、条件の材料の系統が合っているかを
    1件ずつ見る。1つでも合わなければ、その案は作れない（fail-closed）。
    出口の枝は assert_exit_roles（枝ごとの系統の欄で見る）。
    """
    roles = (table or {}).get("roles") or {}
    if not roles:
        raise SampleError("[4要素ゲート] 型の表に役割の一覧が無い（役割の照合ができない）")
    for d in _walk_dicts(obj):
        role = d.get("role")
        mats = d.get("material")
        if not role or not isinstance(mats, list):
            continue                                  # 条件でない（役割を持たない）＝対象外
        rr = roles.get(role)
        if rr is None:
            raise SampleError(f"[4要素ゲート] {where} に、型の表に無い役割が在る: {role}")
        ok_lineages = tuple(rr.get("lineages") or ())
        for m in mats:
            if not isinstance(m, dict) or "family" not in m:
                continue
            lineage = _lineage_of(m)
            if lineage not in ok_lineages:
                raise SampleError(
                    f"[4要素ゲート] {where} に、役割に合わない指標が在る: "
                    f"役割 {role} に 系統 {lineage} の指標 {m.get('family')}。"
                    f"役割 {role} が使える系統は {ok_lineages}（型の表）")


def assert_exit_roles(exits, where: str = "案の出口") -> list[str]:
    """★出口の指標の条件＝「その枝が使える系統」（出口の表の lineage_any／lineage）に材料の系統が在るか。

    印 LIN_SRC（_exit_indicator_cond が付ける）＝{"branch": 枝, "lineages": [...], "from_table": 表に欄が在ったか}。
    ★2026-08-25（60回目・設計書 v2 の やること5）＝出口の表に系統の欄が入り、まこさんが承認した
      （`exit_families_approved.txt` の指紋 f5d53842ff40ab09…）。だから **from_table=False は止める**。
      直す前は「未判定」として戻り値に載せ、そのまま通していた（表の承認待ちの間だけの形）。
    戻り＝いまは常に空（表に欄が無い枝は、そもそも組み立てられない＝_exit_indicator_cond が止める）。
    """
    notes: list[str] = []
    for d in _walk_dicts(exits or []):
        src = d.get(LIN_SRC)
        if not isinstance(src, dict):
            continue
        mats = d.get("material") or []
        for m in mats:
            if not isinstance(m, dict) or "family" not in m:
                continue
            lineage = _lineage_of(m)
            if not src.get("from_table"):
                raise SampleError(f"[4要素ゲート] {where}: 枝 {src.get('branch')} は、使える系統の欄が"
                                  f"出口の表に無い（印 from_table=False）＝判定の基準が無いので通さない"
                                  f"（設計書 v2 の やること5・2026-08-25）")
            if lineage not in set(src.get("lineages") or []):
                raise SampleError(f"[4要素ゲート] {where}: 枝 {src.get('branch')} に 系統 {lineage} の指標 "
                                  f"{m.get('family')}。枝が使える系統は {sorted(src.get('lineages') or [])}（出口の表）")
    return notes


_GATE_LIMITS: dict | None = None      # 走行中の limits（保有時間の範囲が解決済みのもの）＝run_generation が置く


def _gate_recipe(recipe: dict, where: str = "案", limits: dict | None = None,
                 table: dict | None = None) -> list[str]:
    """案1本に、値の出どころ・役割の検査を全部 掛ける（S2＝案を返す直前／走らせる入口の両方で呼ぶ）。

    戻り＝出口の未判定の一覧（表の承認待ちの枝）。
    limits を渡されないとき＝走行中の limits（_GATE_LIMITS）。それも無ければ設定ファイルを読んで
    保有時間の範囲を e38 の役割で解決したもの（自己テスト・単独の検査のため）。
    """
    if limits is None:
        limits = _GATE_LIMITS                      # 本走なら run_generation が置く。無ければ正本との照合は飛ばす
    table = table if table is not None else load_signal_table()
    assert_provenance(recipe, limits=limits, table=table, where=where)
    assert_roles(recipe.get("entry"), table, where=f"{where} の入口")
    assert_roles((recipe.get("meta") or {}).get("regime"), table, where=f"{where} の場面の判定")
    return assert_exit_roles(recipe.get("exits"), where=f"{where} の出口")


_IDENTITY_HASHES: set | None = None


def _is_identity_recipe(recipe: dict) -> bool:
    """恒等レシピ（recipes/identity_*.json）か＝ファイルの中身のハッシュ値が一致するものだけ。

    ★レーンの名前（legacy）では見ない＝名前を付けるだけで検査を飛ばせる道を作らない（設計書 やること8）。
    """
    global _IDENTITY_HASHES
    if _IDENTITY_HASHES is None:
        hs = set()
        for p in sorted(ex.RECIPE_DIR.glob("identity_*.json")):
            try:
                hs.add(recipe_hash(json.loads(p.read_text(encoding="utf-8"))))
            except Exception:
                continue
        _IDENTITY_HASHES = hs
    try:
        return recipe_hash(recipe) in _IDENTITY_HASHES
    except Exception:
        return False


def _cc(cond, *a, **k):
    """自己テストが検証器（条件1つ）を呼ぶときの包み。印を外してから渡す。"""
    import engine_tuner_exec as _ex
    return getattr(_ex, "_check_cond")(strip_marks(cond), *a, **k)


def validate_drawn(recipe, *a, **k):
    """案を作るプログラムが返した案（印つき）を、実行器の検査 `validate_recipe` に通す **唯一の公開の口**。

    ★69回目（2026-08-27・原因A の直し・承認 d7448952c357c306…）。
      `sample_structure` は印（_num_src ほか・`_MARK_KEYS`）を付けたまま案を返す（C-7＝保存する案に出どころを残す）。
      実行器の検査は印を知らないので、印を外さずに渡すと G5/G6 で拒否される（68回目の実測＝0/96）。
      直す前は、印を外す包みが自己テスト用の `_vr` にしか無く、外から呼ぶ3本（regime_r9_diag／
      build_regime_from_tuner／engine_tuner_fire_diag）が `ex.validate_recipe` を直に呼んで落ちていた。
    ★外のプログラムが案を検査に通すときは、必ずここを通る（番人 T31 が、直に呼ぶ所を構文木で数える）。
    """
    import engine_tuner_exec as _ex
    return _ex.validate_recipe(strip_marks(recipe), *a, **k)


def _vr(recipe, *a, **k):
    """自己テストが検証器（案まるごと）を呼ぶときの包み＝`validate_drawn` を呼ぶだけ（判定を2か所に書かない・89番の型）。"""
    return validate_drawn(recipe, *a, **k)


def _scan_direct_validate_calls(paths) -> list[str]:
    """`sample_structure(` を呼ぶ .py の中で、`validate_recipe(` を印を外さずに直に呼ぶ所を、構文木で数える（番人 T31・69回目）。

    経由していると数えるもの＝1つ目の引数が `strip_marks(...)` か `validate_drawn(...)` の呼び出し。
    ★一覧は手で並べない＝渡された .py を全部 読む（L-563 の型）。構文の木にできないファイルは、飛ばさずに1件として返す。
    戻り＝["ファイル名:行", ...]（0件なら空）。
    """
    import ast
    out: list[str] = []

    def _fn(node):
        f = node.func
        return f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")

    for p in paths:
        p = pathlib.Path(p)
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        except SyntaxError as e:
            out.append(f"{p.name}: 構文の木にできない ({e})")
            continue
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        if not any(_fn(n) == "sample_structure" for n in calls):
            continue
        for n in calls:
            if _fn(n) != "validate_recipe" or not n.args:
                continue
            a0 = n.args[0]
            if isinstance(a0, ast.Call) and _fn(a0) in ("strip_marks", "validate_drawn"):
                continue
            out.append(f"{p.name}:{n.lineno}")
    return out


def strip_marks(obj):
    """印を外す＝実行器に渡す直前・案のハッシュ値を出す瞬間だけで使う（保存する案からは外さない・C-7）。"""
    if isinstance(obj, dict):
        return {k: strip_marks(v) for k, v in obj.items() if k not in _MARK_KEYS}
    if isinstance(obj, list):
        return [strip_marks(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(strip_marks(v) for v in obj)
    return obj


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
    if "demand" in m:
        # ★2026-09-06（監査 cp24 の §6-2・設計書 B）＝需給は系統の1つ（2026-10-22 の R-1 で系統は10になった）
        #   （indicator_reference_diag.LINEAGE_KINDS）。直す前は枝が無く、需給の材料を渡すと
        #   FAMILY_LINEAGE を引きに行って落ちた（＝需給は1度も引かれていなかった証拠でもある）。
        return "需給"
    return iref.FAMILY_LINEAGE[m["family"]]["k"]


def _kubun_of(m: dict) -> str:
    """材料の方向の区分（順張り値／状態量／ボラ量／反転サイン）＝カタログの「方向」の欄から機械で引く。"""
    if "geo" in m:
        return iref.RANGE_GEO_REF[m["geo"]]["houkou"].split("＝")[0]
    if "time" in m:
        return iref.TIME_REF[m["time"]]["houkou"].split("＝")[0]
    if "demand" in m:
        # ★2026-09-06（監査 cp24 の §6-2・設計書 B）＝需給の列も、レンジ幾何・時間帯と同じ形で
        #   定義表から区分を引く。直す前は需給が案に出なかったので、ここに枝が無かった。
        return iref.DEMAND_REF[m["demand"]]["houkou"].split("＝")[0]
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
        # ★2026-09-05（M2-C-4）＝需給の列（別枠・時間足に展開しない）
        "demand_ok": list((t.get("extra_parts") or {}).get("demand", {}).get("parts") or []),
        "roles": roles,
        "families": list(rl["applies_to"]),
        "quantile_grid_hi": ("q70", "q80", "q90"),   # DC2 の高分位（表の DC2 の逐語＝q70・q80・q90）
        "quantile_grid_lo": ("q10", "q20", "q30"),   # DC2 の低分位（同＝q10・q20・q30）
        "quantile_hi": ("q70", "q80", "q90"),        # 出口の確認条件で使う別名（同じ値）
        "quantile_lo": ("q10", "q20", "q30"),
    }
    return _SIGNAL_TABLE


# ★場面ごとの読み込み口（旧 load_scene_rules）は 2026-08-30（M2-B0・まこさん承認
#   iter="m2-b0-law-reader-20260830"）に消した。場面の審査の正本は regime_laws.json の
#   「機械が読む判定」になり、読むのは ex.load_regime_laws（engine_tuner_exec）＝1か所だけ。


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
                # ★指標のオン・オフの印（M2-C-2・呼ぶ側 4/5＝順位の表を作る）。
                #   使わない指標の列は順位から外す＝場面の判定の束が、その材料を1位に引かなくなる。
                #   ★成績表そのものは書き換えない（読むときに外すだけ）＝印を戻せば順位も戻る。
                nm = str(col).rsplit("__", 1)[0] if "__" in str(col) else str(col)
                # ★需給の列（別枠・設計書 iter="demand-in-ranking-20260907" の E・まこさん承認 2026-09-07）
                #   ＝需給の名前は参照表 REFS に無いので indicator_enabled は必ず False を返す。印は demand_on で見る。
                #   既存の判定（下の if）の手前に置いて continue で抜ける＝既存の行は触らない（足すだけ）。
                if nm in iref.DEMAND_REF:
                    if not ex.demand_enabled(nm):
                        continue
                    rows.append((abs(float(acc) - 0.5), str(col), float(acc), lab, str(hor)))
                    continue
                if not ex.indicator_enabled(nm):
                    continue
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
    return _banned_name(ex.build_name(m), m["tf"], table)


def _banned_name(name: str, tf: str, table) -> bool:
    """（列の名前×時間足）が禁止3（標本不足）に当たるか＝`_banned_pair` の中身（69回目に切り出した）。

    ★なぜ切り出したか＝`_group_usable`（原因B の直し）が範囲の数字を全部 走査するときに、材料の辞書
      （family と tf の両方を持つ辞書）を印の外で作らずに済むようにするため（`--lint-provenance` の K1）。
      判定の式は1文字も変えていない（表に載っていれば拒否・載っていなければその場で計算）。
    """
    if (name, tf) in table["banned"]:
        return True
    return _insufficient_samples(name, tf)


def _lineage_candidates(role, rr, table, by_lineage, limits) -> dict:
    """役割ごとに「使える系統 → その系統の中の候補」を作る（承認済みの型の表が正本）。

    戻り＝{系統名: [候補, ...]}。候補は2種類ある。
      ・別枠の部品＝`{"geo": "W%"}` `{"demand": "CVD"}` `{"time": "時刻"}`（時間足を持たない）
      ・指標の種類＝`"RSI"` のような文字列（時間足と数字は引く側が付ける）

    ★2026-09-06（監査 cp24 の §6-1・§6-2・設計書 B）に新設。
      直す前＝別枠を引くかどうかを、CC が書いた割合の数字で決めていた
        （レンジ幾何は `r < 0.5`＝2回に1回・時間帯は `r < 0.10`＝10回に1回）。
        **この2つの数字は出どころの記録が無い**（`git log -S` の実測＝どちらも commit 863935a＝
        まこさんが「論外」とした乱数のくじ引きを作った回に入り、決定の記録が無い）。
        そして**需給は枝そのものが無く、何回 走らせても案に出なかった**（監査の実測）。
      直した後＝表が宣言している「その役割が使える系統」を そのまま候補の単位にする。
        ＝引く先を決めるのが CC の数字ではなく、まこさんが承認した表になる。

    ★別枠3種は、ここでオン・オフの印を見る（監査 §6-1「別枠にオン・オフを効かせる」）。
      印がオフの部品は候補に入らない＝「使わない」と決めたものが案に出ない。
    ★時間帯は「閾値の格子が在るものだけ」を候補にする。実測（2026-09-06）＝
      `時刻` は格子 `hour_range` が在る／`曜日` は格子が無い（まこさん §11-10 の判断待ち）。
      印では両方オンだが、格子が無いものを引くと値を作れない。**格子が決まれば自動で増える。**
    """
    out: dict[str, list] = {}
    for k in rr["lineages"]:
        cand: list = []
        if k == "構造・位置" and rr.get("geo"):
            cand += [{"geo": str(g)} for g in (table.get("geo_ok") or []) if ex.geo_enabled(str(g))]
        if k == "需給":
            cand += [{"demand": str(d)} for d in (table.get("demand_ok") or [])
                     if ex.demand_enabled(str(d))]
        if k == "時間帯":
            cand += [{"time": str(t)} for t in (table.get("time_ok") or [])
                     if ex.time_enabled(str(t)) and limits.get(_TIME_GRID.get(str(t)))]
        cand += [str(f) for f in by_lineage.get(k, [])]     # その系統の指標の種類
        if cand:
            out[k] = cand
    return out


# ★時間帯の列 → その列の閾値の格子の名前（設定ファイル search_limits.json の鍵）。
#   ★手書きの対応はこの1行だけ＝格子の名前は設定ファイル側に在り、CC が数字を作っていない。
#   曜日は格子が未定義（まこさん §11-10 の判断待ち）＝ここに載らない＝候補に入らない。
_TIME_GRID = {"時刻": "hour_range"}


def _pick_material(rng, pool, tfs, limits, role, seen_rolekind, kind_count, table) -> dict:
    """材料1本＝G3（同系統×同役割は1本・K_MAX）＋型の表（対応表の系統×時間足・禁止3・許可 geo/time）を
    サンプリング時から守る（D1・2026-08-07 まこさん承認の表が正本）。

    ★2026-09-06（監査 cp24 の §6-1・§6-2・設計書 B）＝引き方を「系統を引く → その系統の中を引く」
      に変えた。理由と、消した数字2つの出どころは `_lineage_candidates` の説明に書いた。
    """
    rr = table["roles"][role]
    tf_pool = _role_tfs(tfs, table, role)
    ranges = material_ranges()
    by_lineage = _pool_families_by_lineage(pool)
    cands = _lineage_candidates(role, rr, table, by_lineage, limits)
    if not cands:
        raise SampleError(f"役割 {role} に使える系統の候補が1つも無い")
    # ★並びは表が宣言した順（rr["lineages"]）のまま使う。sorted で並べ替えない。
    #   理由＝並べ替えると「表の並びを変えても案が変わらない」＝表の並びが効かなくなる
    #   （番人 T19 が実測で捕まえた・2026-09-06）。表が正本なら、並びも表のものを使う。
    lin_keys = [k for k in rr["lineages"] if k in cands]
    for _ in range(60):
        k0 = str(lin_keys[int(rng.integers(len(lin_keys)))])  # ①系統を引く（表が宣言した系統から一様に）
        bag = cands[k0]
        pick = bag[int(rng.integers(len(bag)))]               # ②その系統の中を引く（一様）
        if isinstance(pick, dict):
            m = dict(pick)                                    # 別枠（レンジ幾何・需給・時間帯）＝時間足なし
        else:
            # ★2026-08-13（段A の A-4）＝パラメータは「範囲の中から引く」（点の一覧から選ばない）。
            #   直す前は pool（カタログの列名を分解した (指標, 数字) の一覧）から1件 引いて、
            #   その数字をそのまま使っていた＝設定ファイルに並んだ数字しか出なかった
            #   （RSI なら 7・9・14・21 の4つだけ）。いまは 指標の種類だけを pool から引き、
            #   数字はその指標の範囲から引く（RSI なら 7〜21 の整数どれでも＝RSI12 も出る）。
            #   ★2026-09-06＝どの指標を引くかは `_lineage_candidates` が系統ごとに用意する。
            #     ここでやるのは「引いた種類に、時間足と数字を付ける」ことだけ。
            m = _mat_drawn(rng, str(pick), str(rng.choice(tf_pool)), ranges, table=table)   # ★数字は引く関数の中で（59回目）
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
    # ★2026-09-11（M2-E-3 の手順1）＝`needs_n=True` を足して、下の引く所と同じ絞りにそろえた。
    #   そろえないと「候補は在る」と言いながら、引く所が1つも引けない形が起きうる。
    if limits is not None and ex.pre_ops(same_unit=True, needs_state=False, needs_n=True):
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
            pair = _mat_two_drawn(rng, c, tf, ranges, table=table)   # ★2本とも引く関数の中で引く（59回目）
            if pair is None:
                continue                              # 範囲が狭くて2本 引けない＝別の組み方を引き直す
        elif kind == "pre":
            # ★同じ列の「素」と「前処理を掛けたもの」。本数は int_grid から引く＝CC が数字を書かない。
            m0 = _mat_drawn(rng, c, tf, ranges, table=table)          # ★数字は引く関数の中で（59回目）
            # ★「状態に入って以降」の3つ（since_min・since_max・at_entry）は引かせない
            #   ＝state（基準にする状態の列の名前）が要るが、案を作る段では決められない。
            #   直す前は引いてしまい、出した案が必ず拒否されていた（2026-08-21・M2-2-8 で直した）。
            # ★2026-09-11（M2-E-3 の手順1）＝`needs_n=True` を足した。
            #   abs（符号を取り去る）は窓を持たないので、下の行が付ける `n` を受け取れない
            #   ＝付けると G5 で「n は書けない」で拒否される。ここは窓を持つ部品だけを引く。
            #   ★abs を実際に付けるのは、場面の判定の束を組む側（段2a の強さの否定）＝別の道。
            op = str(rng.choice(ex.pre_ops(same_unit=True, needs_state=False, needs_n=True)))
            pair = [m0, _mat_with_pre(m0, {"op": op, **_iv(rng, limits, "n", n_min=2)})]
        else:
            fa, fb = c                                # type: ignore[misc]
            # ★数字は「同じ回の呼び出しから出た2本」を組む＝共通の軸は同じ値にそろえる
            #   （Stoch%K14 と Stoch%D14／MACD線%(12,26) と MACDシグナル線%(12,26,9)）。
            #   そろえた結果が相手の範囲の外に出るときだけ、それぞれ別に引く（＝_mat_pair_drawn の中・59回目）。
            pair = _mat_pair_drawn(rng, fa, fb, tf, ranges, table=table)
            # ★別の指標どうしは、どちらを先に置くかの決まりが無い＝両方の向きを作る（乱数）。
            #   「短い方を先に置く」は同じ指標のパラメータ違いにだけ効く決まり。
            if rng.random() < 0.5:
                pair = [pair[1], pair[0]]
        if not any(_banned_pair(m, table) for m in pair):
            return pair
    raise SampleError(f"役割 {role} の列2本を30回引いても禁止3 を避けられない")


def _q(rng, limits) -> dict:
    # ★2026-08-15（段A の A-5-3）＝分位を範囲から引く（直す前は9段のメニューからだけ）。
    return _thr_drawn(rng, limits)


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
        return _thr_drawn(rng, limits, lo_min=lo_q, hi_max=hi_q)
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
                    "value": _nv(rng, limits, "state_hold_bars_range", "n", as_int=True)}
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
            # ★2026-08-15（段A の A-5-4）＝ずらす本数を、コードに直に書いた 0・1 の2つから
            #   設定ファイルの範囲（`nest_offset_range`）へ出した。両端は直す前の2つの 最小 と 最大。
            out = {"role": role, "form": form, "inner": inner,
                   "value": _nvs(_iv(rng, limits, "n", n_min=2),
                                 _nv(rng, limits, "nest_offset_range", "offset", as_int=True))}
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
                val = _nvs(val, _iv(rng, limits, "n", n_min=2))
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
                "value": _nv(rng, limits, "hour_range", "n", as_int=True)}
    # ★水準の形（level・band・band_exclude）には、単位の変わる前処理を掛けられる（2026-08-12（18回目）・4-2）。
    #   ＝『いまの値が 直近n本の中で上位20%』（ts_rank）／『直近n本のばらつきが大きいとき』（ts_std）。
    #   ・掛けるか掛けないかは「素のまま」を選択肢の1つに入れて一様に引く＝CC が確率の数字を書かない。
    #   ・閾値は下の既に在る決まり（DC1・DC2・分位の格子）がそのまま決める＝新しい決まりを作らない。
    #   ・本数は int_grid から引く＝CC が数字を書かない。
    if form in ex.forms_where("pre_ok"):       # ★手書き → 性質表から（M2-2-3b）
        _pre_opts = [None] + ex.pre_ops(same_unit=False, gen_draw=True)   # ★2026-09-27（M2-E-4e）＝乱数の道で引かない部品（ts_pos）を外す
        _op = _pre_opts[int(rng.integers(len(_pre_opts)))]
        if _op is not None:
            m = _mat_with_pre(m, {"op": _op, **_iv(rng, limits, "n", n_min=2)})
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
        _lo_thr, _hi_thr = _thr_band_drawn(rng, limits)      # ★2つとも引く関数の中で（59回目）
        return {"role": role, "form": form, "material": [m],
                "value": {"lo": _lo_thr, "hi": _hi_thr}}
    if form == "slope":
        return {"role": role, "form": "slope", "material": [m],
                "side": _dc1_side(rng, role, [m], side),
                "value": _iv(rng, limits, "n")}
    if form == "slope_avg":
        return {"role": role, "form": "slope_avg", "material": [m],
                "side": _dc1_side(rng, role, [m], side),
                "value": _nvs(_iv(rng, limits, "n"), _iv(rng, limits, "m"))}
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
        # ★59回目＝種類だけを pool から引き、数字は引く関数の中で範囲から引く
        #   （直す前は pool の決まった数字をそのまま使い、「範囲から」の嘘の印が付いていた＝監査 Q2 根拠(2)）。
        m = _mat_drawn(rng, b["family"], str(rng.choice(tf_pool)), table=table)
        if not _banned_pair(m, table):
            return m
    raise SampleError("出口の材料を40回 引いても禁止3 を避けられない")


def _exit_indicator_cond(rng, limits, pool, tfs, table, side, spec, bid: str = "") -> dict:
    """出口の確認条件＝指標を見る形1本。向きの決め方は表の規則から機械で決まる。

    表の規則に reverse_of_side が在る枝＝入口と逆の向きを見る（例＝SHORT の玉は、下げ止まり側で降りる）。
    無い枝＝広がる側・強い側を見る（例＝レンジが壊れたことを見る BREAKOUT）。
    ★59回目＝印 LIN_SRC（この枝が使える系統・表に欄が在ったか）を付ける＝assert_exit_roles が見る。
    ★60回目（2026-08-25・設計書 v2 の やること5）＝**コードに直に書いてあった既定の6系統を消した。**
      使える系統は出口の表（`exit_families.json` の枝の `lineage_any`／`lineage`）だけが決める。
      表に欄が無い枝は、ここで止める（＝組み立てない）。
      直す前＝欄が無い枝は既定の6系統で組み、from_table=False と記して そのまま通していた。
      実測（案300本・2026-08-25）＝REVERSE_IND がその形で、ローソク4回・出来高3回を引いていた
      （包み足の傾きのような、指標の役割と噛み合わない条件が作られていた）。
      表の欄はまこさんが承認する（`exit_families_approved.txt` の指紋 f5d53842ff40ab09…）。
    """
    lineages = set(spec.get("lineage_any") or ([spec["lineage"]] if spec.get("lineage") else []))
    if not lineages:
        raise SampleError(f"[4要素ゲート] 出口の枝 {bid} に、使える系統の欄（lineage_any／lineage）が"
                          f"出口の表に無い＝この枝は組み立てない（設計書 v2 の やること5・2026-08-25）")
    lin = {"branch": str(bid), "lineages": sorted(lineages), "from_table": True}
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
        # ★60回目（2026-08-25）＝印 LIN_SRC を足した。直す前はこの形だけ印が付かず、
        #   assert_exit_roles を素通りしていた（材料を持たない形なので材料の系統は見られないが、
        #   「どの枝の条件か・その枝が使える系統は何か」を記録に残す＝穴を塞ぐ）。
        return {"role": "env", "form": "candle_dir",
                "value": {"dir": ("bull" if side == "SHORT" else "bear") if rev else
                                 ("bear" if side == "SHORT" else "bull")}, LIN_SRC: lin}
    if form == "cross" and "ローソク" not in lineages:
        # 2本の線の交差＝入口の逆向き（DC3 の逆）
        fams = {b["family"] for b in pool if iref.FAMILY_LINEAGE[b["family"]]["k"] in lineages}
        tf_pool = [t for t in tfs if t in table["tfs"]]
        if "Stoch%K" in fams and "Stoch%D" in fams:
            tf = str(rng.choice(tf_pool))
            # ★59回目＝2本の数字は引く関数の中で引く（共通の軸はそろえる）。直す前は pool の決まった数字。
            pair = _mat_pair_drawn(rng, "Stoch%K", "Stoch%D", tf, table=table)
            if not any(_banned_pair(m, table) for m in pair):
                return {"role": "env", "form": "cross", "material": pair,
                        "value": {"direction": ("up" if side == "SHORT" else "down") if rev
                                  else ("down" if side == "SHORT" else "up")}, LIN_SRC: lin}
        form = "level"
    m = _pick_exit_material(rng, pool, tfs, table, lineages)
    if form == "slope":
        return {"role": "env", "form": "slope", "material": [m],
                "side": ("above" if side == "SHORT" else "below") if rev else str(rng.choice(["above", "below"])),
                "value": _iv(rng, limits, "n"), LIN_SRC: lin}
    # ── 水準を見る形（level）──
    # ★実行器は出口の発火条件で分位（threshold_q）を解けない（_exit_fire_ok が解決表を受け取らない・
    #   1073行の _vnum）。だから出口の水準は、名前つき定数レジストリに登録済みの値だけで表す。
    #   使えるのは、その定数が意味を持つ部品（RSI・ストキャス・ADX）に限る。
    #   ほかの部品は水準では見ない＝交差・傾き・ローソクの形で見る（値の要らない形）。
    hi_lo = _EXIT_LEVEL_CONST.get(m["family"])
    if hi_lo is None:
        return {"role": "env", "form": "slope", "material": [m],
                "side": ("above" if side == "SHORT" else "below") if rev else str(rng.choice(["above", "below"])),
                "value": _iv(rng, limits, "n"), LIN_SRC: lin}
    hi, lo = hi_lo
    if rev:                       # 反転を見る＝SHORT の玉は下がり切った側（買われ過ぎの逆）で降りる
        sd, cst = ("below", lo) if side == "SHORT" else ("above", hi)
    else:                         # 壊れたことを見る＝SHORT の玉は上に振れた側
        sd, cst = ("above", hi) if side == "SHORT" else ("below", lo)
    return {"role": "env", "form": "level", "material": [m], "side": sd, "value": {"const": cst}, LIN_SRC: lin}


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

    # ★59回目＝出口の枝の数字は全部「引く関数」（_nv・_iv・_iv_from・_nvd）で作る＝印（範囲）つき。
    #   直す前は draw_num／draw_int の生の数字を辞書に直に書いていた（出どころが案に残らない・監査 注1）。
    _base100 = float(iref.CONST_REGISTRY["FULL_100"]["value"])          # _const100 の分母（名前つき定数）
    _tm = _iv_from(rng, "n", hold_bars(limits)[0], hold_bars(limits)[1], "hold_bars", scale=5)
    tmax_min = int(_tm["n"])

    def hold_gate() -> dict:
        """満期に対する割合で保有の門を作る（分・5の倍数に丸める・最低5分）。

        ★2026-08-15（段A の A-5-2）＝割合は 0.25・0.5・0.75 の3つだけでなく、
          0.25〜0.75 の範囲から引く。
        """
        f = _nv(rng, limits, "hold_frac_range", "frac")
        n = int(round(tmax_min * float(f["frac"]) / 5.0)) * 5
        return _nvd("n", max(5, n), f[NUM_SRC]["frac"])

    def _floor_mult(key: str, scale: float) -> dict:
        """手数料床（SCALP_FLOOR）の倍数を範囲から引いた形（_floor_pct と同じ辞書・印つき）。"""
        return {"const": "SCALP_FLOOR", **_nv(rng, limits, key, "mult", scale=scale)}

    exits: list[dict] = []

    # ── ① 利確（名前は TP2 で固定＝部分利確と縮む枝がこの名前を参照する）──
    tp_id = str(rng.choice(["TP_ZONE_MID", "TP_ZONE_OPP", "TP_PCT", "TP_SWING"]))
    if tp_id == "TP_ZONE_MID":
        lv = {"kind": "zone", "target": "mid"}
    elif tp_id == "TP_ZONE_OPP":
        lv = {"kind": "zone", "target": "opp", "fallback": "mid",
              "buf": _floor_mult("state_mult_range", 1.0)}          # ＝_floor_pct(raw/100)＝mult=raw
    elif tp_id == "TP_PCT":
        lv = {"kind": "pct", "base": "entry",
              "k": _floor_mult("state_mult_range", 1.0)}
    else:
        lv = {"kind": "swing", "target": "low" if side == "SHORT" else "high",
              "m": _iv(rng, limits, "n"),
              "buf": _floor_mult("state_mult_range", 1.0),
              "fallback": {"kind": "zone", "target": "mid"}}
    exits.append(mk(tp_id, "TP2", placement={"kind": "resting", "fill": "profit", "level": lv}))

    # ── ② 損切り（3種から1つ）／確率で「損切り無し＋資金防衛」（軸 X-d4）──
    no_sl = rng.random() < 0.15
    if not no_sl:
        sl_id = str(rng.choice(["SL_ZONE", "SL_PCT", "SL_SWING"]))
        if sl_id == "SL_ZONE":
            lv = {"kind": "zone_sl", "w": str(rng.choice(["range", "zone", "inner"])),
                  "k": {"const": "FULL_100",                       # ＝_const100(raw/100)＝mult=raw/(100×分母)
                        **_nv(rng, limits, "exit_mult_range", "mult", scale=1.0 / (100.0 * _base100))}}
        elif sl_id == "SL_PCT":
            lv = {"kind": "pct", "base": "entry",
                  "k": _floor_mult("exit_mult_range", 0.1)}       # ＝raw/10
        else:
            lv = {"kind": "swing", "target": "high" if side == "SHORT" else "low",
                  "m": _iv(rng, limits, "n"),
                  "buf": _floor_mult("state_mult_range", 1.0),
                  "fallback": {"kind": "zone_sl", "w": "range", "k": _const100(1.0)}}
        exits.append(mk(sl_id, "SL", placement={"kind": "resting", "fill": "adverse",
                                                "pessimistic": True, "level": lv}))

    # ── ③ 資金防衛（1トレードの最大許容損失・損切り無しの案では必ず入れる）──
    if no_sl or rng.random() < 0.30:
        exits.append(mk("FINSTOP", "FINSTOP", placement={"kind": "on_close"}, risk="loss_cap",
                        fire={"all": [_state_cond("unreal_pct", "below",
                                                  _floor_mult("loss_cap_range", -100.0 / 0.08))]}))   # ＝-100×cap/0.08

    # ── ④ 時間切れ（必ず入る）──
    time_br = mk("TIME", "TIME", placement={"kind": "on_close"},
                 fire={"all": [_state_cond("hold_min", "above", dict(_tm))]})
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
        _gb = _nv(rng, limits, "giveback_range", "g")
        exits.append(mk("PEAKLOCK", "PEAKLOCK",
                        placement={"kind": "resting", "fill": "adverse", "pessimistic": True,
                                   "level": {"kind": "peak_giveback",
                                             "arm": _floor_mult("state_mult_range", 100.0),      # ＝_floor_pct(raw)
                                             "giveback": _nvd("n", max(1, int(round(float(_gb["g"]) * 100))),
                                                              _gb[NUM_SRC]["g"]),
                                             "floor": {"const": "SCALP_FLOOR"}}}))
    if rng.random() < 0.30:       # 一度 利が乗った後、建値+手数料床で降りる
        exits.append(mk("BEEXIT", "BEEXIT",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "pct", "base": "avg",
                                             "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},
                        fire={"all": [_state_cond("mfe_prev_pct", "above",
                                                  _floor_mult("state_mult_range", 100.0))]}))
    if rng.random() < 0.30:       # 時間が経っても利が乗らない玉を、建値フロアで降りる（停滞・失速）
        exits.append(mk("BESTALE", "BESTALE",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "pct", "base": "avg",
                                             "k": {"const": "SCALP_FLOOR", "side_sign": "profit"}}},
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("mfe_prev_pct", "below",
                                                  _floor_mult("state_mult_range", 100.0))]}))
    if rng.random() < 0.30:       # 利確に届かないまま満期が近い玉を、手前の位置で確定する
        exits.append(mk("MFEEXIT", "MFEEXIT",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "mix", "from": "entry", "to": "TP2",
                                             "frac": {"const": "FULL_100",                # ＝_const100(raw/100)
                                                      **_nv(rng, limits, "frac_range", "mult",
                                                            scale=1.0 / (100.0 * _base100))}}},
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("mfe_prev_pct", "above",
                                                  _floor_mult("state_mult_range", 100.0))]}))
    if pool and rng.random() < 0.30:    # 指標が反転したら、利益側に指値を置いて確定する
        try:
            c = _exit_indicator_cond(rng, limits, pool, tfs, sig, side, need("REVERSE_IND")["fire"][0],
                                     bid="REVERSE_IND")
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
            c = _exit_indicator_cond(rng, limits, pool, tfs, sig, side, need("BREAKOUT")["fire"][0],
                                     bid="BREAKOUT")
            exits.append(mk("BREAKOUT", "BREAKOUT", placement={"kind": "on_close"}, fire={"all": [c]}))
        except SampleError:
            pass
    if max_adds >= 2 and rng.random() < 0.30:   # 積み増した玉だけに当たる損切り（枝が回数で切り替わる）
        # ★2026-08-15（段A の A-5-2）＝直す前は「一覧の中から 2回目以上・その案の回数以下のものを拾い、
        #   1つも無ければ 2 にする」でした（`or [2]` がコードに直に書いた数字＝場所3 の2件目）。
        #   いまは 2回目 から その案の積み増し回数 までの整数から引きます＝直書きの数字が消えました。
        _lo = _nv(rng, limits, "max_adds_range", "adds_lo", lo_min=2, hi_max=max_adds, as_int=True)
        exits.append(mk("MAECUT_ADDS", "MAECUTADDS", placement={"kind": "on_close"},
                        scope=_nvd("adds", [int(_lo["adds_lo"]), None], _lo[NUM_SRC]["adds_lo"]),
                        fire={"all": [_state_cond("hold_min", "above", hold_gate()),
                                      _state_cond("unreal_pct", "below", {"const": "NEUTRAL_0"})]}))
    if rng.random() < 0.30:       # 残り時間の比で建値側へ縮む指値（時間切れの前に置き直す）
        exits.append(mk("SHRINK", "SHRINK",
                        placement={"kind": "resting", "fill": "profit",
                                   "level": {"kind": "shrink", "from": "TP2",
                                             "tmax": _nvd("n", max(1, tmax_min // 5), _tm[NUM_SRC]["n"]),
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
        steps = int(_nv(rng, limits, "ladder_steps_range", "steps", as_int=True)["steps"])
        mf = ladder_min_frac()                    # 玉に対する、最小注文サイズの割合（機械が出す）
        rest = 1.0
        for s in range(steps):
            _fr = _nv(rng, limits, "frac_range", "frac")
            frac = float(_fr["frac"]) / 100.0
            if rest * frac < mf or rest * (1.0 - frac) < mf:
                break                             # この段を作ると、決済の量か 残りの量が最小注文を割る
            exits.append(mk("TP1_LADDER", f"TP1{'' if s == 0 else s + 1}", once=True,
                            placement={"kind": "resting", "fill": "profit",
                                       "level": {"kind": "mix", "from": "entry", "to": "TP2",
                                                 "frac": {"const": "FULL_100",
                                                          **_nvd("mult", frac * (s + 1) / steps / _base100,
                                                                 _fr[NUM_SRC]["frac"])}}},
                            **_nvd("size_ratio", frac, _fr[NUM_SRC]["frac"])))
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


def _family_tf_from_col(col: str) -> tuple[str, str]:
    """成績表の列名（例 ER21__1h）から「指標の種類」と「時間足」だけを取る（参照表＝indicator_reference_diag）。

    ★59回目（決定 (a')）＝列名の数字（21）は使わない。数字は _mat_drawn が範囲から引く（78番の直し）。
      直す前（_material_from_col）は数字も列名から取っていた＝要件「作ってはいけないもの」2番に当たっていた。
    """
    if "__" not in col:
        raise SampleError(f"順位の列名に時間足が無い: {col}")
    name, tf = col.rsplit("__", 1)
    # ★需給の列（別枠・設計書 demand-in-ranking-20260907 の E）＝参照表 REFS に無いので find は None を返す。
    #   種類＝需給の名前そのもの・時間足＝列名のまま（成績表では 5m の1本だけ）。既存の行は触らない（足すだけ）。
    if name in iref.DEMAND_REF:
        return str(name), str(tf)
    ent, _prm = iref.find(name)
    if ent is None or ent["family"] not in ex.FAMILY_TEMPLATES:
        raise SampleError(f"順位の列がカタログに無い: {col}")
    return str(ent["family"]), str(tf)


_RANKED_GROUPS_MEMO: dict = {}
_GROUP_USABLE_MEMO: dict = {}


def _group_usable(fam: str, tf: str, ranges: dict | None = None, table: dict | None = None) -> bool:
    """その組（種類×時間足）に、範囲の中で禁止3（標本不足）を通る数字が **1つでも在るか**（69回目・原因B の直し・承認 d7448952c357c306…）。

    ★なぜ要るか＝成績表を種類×時間足でまとめた順位（`ranked_groups`）には、範囲のどの数字を引いても
      標本不足で使えない組が混ざる（68回目の実測＝env の順位1・3・4・6・7 が 0/200）。`_ranked_material_at` は
      その組で10回 引いて全部だめなら案を諦めるので、その順位に当たる案は必ず落ちていた。
    ★範囲を **全部 走査** する（乱数で引いて確かめない＝結果が種に依らない・「1位から順」を保つ）。
      整数の軸＝lo〜hi の全部／小数の軸＝dec（カタログの小数の桁数）の刻みで全部＝`draw_param` が丸める桁と同じ
      ＝引ける数字を1つ残らず見る／軸が複数なら直積。判定の式は `_banned_pair` と同じ（表 → `_insufficient_samples`）。
    ★範囲そのもの（`material_ranges`）と引き方（`draw_param`・`_mat_drawn`）には触らない＝探す範囲は変わらない。
    ★走査が 200,000 通りを超えるときは止める（fail-closed）＝刻みは まこさんが決める。
    """
    import itertools
    ranges = ranges if ranges is not None else material_ranges()
    spec = ranges.get(fam)
    if spec is None:
        return False
    key = (str(fam), str(tf), json.dumps(spec["axes"], sort_keys=True, default=str))
    if key in _GROUP_USABLE_MEMO:
        return _GROUP_USABLE_MEMO[key]
    axes_vals: list[list] = []
    for ax in spec["axes"]:
        lo, hi = ax["lo"], ax["hi"]
        if ax["kind"] == "int":
            axes_vals.append(list(range(int(lo), int(hi) + 1)))
        else:
            dec = int(ax.get("dec", 0) or 0)
            if dec:
                step = 10.0 ** (-dec)
                n = int(round((float(hi) - float(lo)) / step))
                axes_vals.append([round(float(lo) + i * step, dec) for i in range(n + 1)])
            else:                                          # draw_param は dec=0 の小数を float(round(v)) にする
                axes_vals.append([float(v) for v in range(int(round(float(lo))), int(round(float(hi))) + 1)])
    total = 1
    for v in axes_vals:
        total *= max(1, len(v))
    if total > 200_000:
        raise SampleError(f"[原因B の走査] {fam} の範囲が広すぎて全走査できない（{total:,} 通り）＝刻みは まこさんが決める")
    usable = False
    for combo in itertools.product(*axes_vals):
        param = combo[0] if len(combo) == 1 else tuple(combo)
        # ★材料の辞書（family＋tf）は作らない＝印を付ける関数の外で材料を作らない決まり（K1）。名前だけを組んで判定する
        if not _banned_name(ex.build_name({"family": str(fam), "param": param}), str(tf), table):
            usable = True
            break
    _GROUP_USABLE_MEMO[key] = usable
    return usable


def ranked_groups(role: str, label: str | None = None) -> list[tuple]:
    """順位を「種類×時間足」ごとにまとめ直した一覧（まこさん決定 (a')・2026-08-25）。

    ★組の成績＝同じ札（label）×見通し（horizon）の表の中で、同じ種類・同じ時間足の列の分離力の **中央値**
      （「いちばん良い列」にしない理由＝列を多く持つ種類が上に来やすい＝類型C と同じ型・3回目の監査の指摘。
        実測 2026-08-25＝最良と中央値で上位10の重なりは役割ごとに平均 5.7〜6.8／10）。
    ★順位の表そのもの（M2-3 で承認）は変えない＝読み方だけ。
    戻り＝[(種類, 時間足, 札, 見通し, 中央値, 列の本数, 代表の列名＝1本目), ...] 強い順（|中央値−0.5| の降順）。
    """
    import statistics as _st
    key = (role, label)
    if key in _RANKED_GROUPS_MEMO:
        return _RANKED_GROUPS_MEMO[key]
    groups: dict = {}
    for col, acc, lab, hor in ranked_materials(role, label):
        try:
            fam, tf = _family_tf_from_col(col)
        except SampleError:
            continue
        groups.setdefault((lab, hor, fam, tf), []).append((col, float(acc)))
    rows = []
    for (lab, hor, fam, tf), items in groups.items():
        med = float(_st.median([a for _c, a in items]))
        rows.append((abs(med - 0.5), fam, tf, lab, hor, med, len(items), items[0][0]))
    rows.sort(key=lambda r: (-r[0], r[1], r[2], r[3], r[4]))      # 強い順・同点は名前順（並びを決定論に）
    out = [(fam, tf, lab, hor, med, n, col) for _s, fam, tf, lab, hor, med, n, col in rows]
    _RANKED_GROUPS_MEMO[key] = out
    return out


def _ranked_material_at(role, rank_pos: int, tfs, table, label=None, tf_ok=None,
                        ranges: dict | None = None) -> tuple[dict, dict]:
    """役割の材料を、成績表（種類×時間足でまとめた順位）の rank_pos 位（1始まり）から取る（M2-5 の B・決定 (a')）。

    種類と時間足は順位から。数字は成績表の列の名前から（★2026-09-11＝乱数を1つも使わない）。
    型の表（役割×系統・時間足）と禁止3（標本不足）を満たすものだけを数えて rank_pos 位。
    戻り＝(材料, 記録{rank, col, family, tf, label, horizon, 分離力, 列の本数})。足りなければ SampleError。
    """
    rr = table["roles"][role]
    ok_tfs = set(tf_ok if tf_ok is not None else _role_tfs(tfs, table, role))
    ranges = ranges if ranges is not None else material_ranges()
    n = 0
    for fam, tf, lab, hor, med, ncol, col in ranked_groups(role, label):
        # ★順位 → 組（種類×時間足）の対応は乱数に依らない（種類・時間足・系統・範囲の表に在るか だけで決める）
        # ★需給の組（設計書 demand-in-ranking-20260907 の E）＝`fam not in ranges` で今までどおり飛ぶ（需給はパラメータの範囲を持たない）
        #   ＝この工事では需給を束に引かない。引く道は M2-E で相場の法則から決める。
        if tf not in ok_tfs or fam not in iref.FAMILY_LINEAGE or fam not in ranges:
            continue
        if iref.FAMILY_LINEAGE[fam]["k"] not in rr["lineages"]:
            continue
        if not _group_usable_col(col, fam, tf, ranges, table):    # ★手順9＝その列の数字で使えるか
            continue
        n += 1
        if n != int(rank_pos):
            continue
        # ★2026-09-11（手順9）＝数字を乱数で引くのをやめ、成績表の列の数字をそのまま使う。
        #   直す前＝`_mat_drawn(rng, …)` で範囲から10回まで引き直していた（恒久の決まり67番に当たる）。
        #   いま＝その列の数字は1つに決まるので、禁止3（標本不足）なら この案は作れない。
        m = _mat_from_col(col, fam, tf, ranges, table=table)
        if _banned_pair(m, table):
            # ★次の組へ飛ばさない＝飛ばすと「1位から順」が崩れる。この案だけ作れない。
            raise SampleError(f"{role} の {rank_pos} 位（{fam}×{tf}）の列の数字が禁止3（標本不足）: {col}")
        if True:
            # ★記録の鍵に family／tf を使わない＝4要素ゲートが「印の無い材料」と取り違えるため（種類・時間足）
            return m, {"rank": int(rank_pos), "col": col, "種類": fam, "時間足": tf, "label": lab,
                       "horizon": hor, "分離力": med, "列の本数": int(ncol)}
    raise SampleError(f"{role}/{label or '全ラベル'} の順位に {rank_pos} 位が無い（使える候補 {n} 本）")


def regime_draw_order(n: int) -> tuple[int, int, int, str]:
    """案 n 番目（0始まり）に割り当てる (帯 B の順位, 強さの否定 C の順位, 3枠目 G の順位, B の向き)。

    並び＝3つの順位の和が小さい順 → 同じ和なら B が小さい順 → C が小さい順 → 向き above・below の順。
    (1,1,1,above) (1,1,1,below) (1,1,2,above) (1,1,2,below) (1,2,1,…) (2,1,1,…) (1,1,3,…) …
    ★乱数を使わない。どこまで下位を試すかは試行数（search_limits.json・まこさんの値）で決まる。

    ★2026-09-11（M2-E-3 の手順10・監査 cp35 の A1-d の3番）＝3枠目 G の順位を足した。
      直す前は戻りが3つ（B・C・向き）で、**3枠目の順位はコードに 1 と直書きされていた**
      （`_material_for_law(rng, "sufficiency", fams_r6, 1, …)`）。
      ＝案の番号を変えても3枠目が1位のまま動かず、探せる束がその分 狭かった。
    ★上限の数字を私が作っていない＝和が小さい順に増やすだけ（和の上限を持たない）。
    """
    if n < 0:
        raise SampleError("案の番号が負")
    i = int(n) // 2
    side = ("above", "below")[int(n) % 2]
    s = 3                                             # 3つとも1位のときの和
    while True:
        # 和 s の組＝B と C を1位から振り、残りを G に回す（3つとも1以上）
        combos = [(b, c, s - b - c) for b in range(1, s - 1) for c in range(1, s - b)]
        if i < len(combos):
            b, c, g = combos[i]
            return b, c, g, side
        i -= len(combos)
        s += 1


def laws_for_scene(name: str) -> dict:
    """その場面に掛かる相場の法則を読み、組む側が使う形にまとめる（M2-E-2・2026-09-10）。

    ★まこさんの指示（逐語 2026-08-24）＝「指標、閾値、パラメータ、時間足の役割に基づき、
      法則に則って４つを組み合わせ、Entry/Exit やレジーム判定などの条件を作る」。
      （逐語 2026-09-09）＝「法則に則って組めって１００回くらい言ってるのに、
      どうしてもそのとおりにやろうとしないよな」。
    ★直す前＝この関数は無く、`sample_regime_build` は法則を1つも読まずに、
      コードに直書きした3つの条件で組んでいた（2303行の逐語「読んだ法則から組むのは M2-E
      ＝ここではまだ使わない」）。だから法則を書き替えても組まれる束が変わらず、
      落とす側（G7）が後から落としていた（実測 2026-09-09＝20回 引き直して通った束は0本）。

    戻り＝{"forms": {形の名前}, "counts": [(法則の番号, 数える部品, 本数)], "no_dup": [(除く系統, 上限)]}
      forms  ＝「形を持つ」の法則が求める形（hysteresis・not・streak）
      counts ＝「部品を数える」の法則（数える条件と、要る本数）
      no_dup ＝「系統を重ねない」の法則（除く系統と、上限）

    ★数字も名前もこの関数に書かない＝全部 `regime_laws.json` から読む。
    """
    out: dict = {"forms": set(), "counts": [], "no_dup": []}
    for law in ex.load_regime_laws():
        j = law["判定"]
        if name not in j.get("掛かる場面", []):
            continue
        typ = j.get("型")
        if typ == "形を持つ":
            out["forms"].add(str(j["形"]))
        elif typ == "系統を重ねない":
            out["no_dup"].append((tuple(j.get("除く系統") or []), int(j["上限"])))
        else:
            out["counts"].append((str(law["番号"]), dict(j["数える部品"]), int(j["本数"])))
    if not out["forms"] and not out["counts"]:
        raise SampleError(f"場面 {name} に掛かる相場の法則が1件も無い（regime_laws.json・fail-closed）")
    return out


def _law_families(laws: dict, no: str) -> tuple:
    """その法則が名指ししている family と、名前ごとの側を取り出す（M2-E-2）。

    戻り＝(family の並び, {family: 側}）。名指ししていなければ (空, 空)。
    ★一覧をこの関数に書かない＝法則ファイルの「数える部品」から取る。
    """
    for num, sel, _n in laws["counts"]:
        if num != no:
            continue
        return tuple(sel.get("family") or []), dict(sel.get("側") or {})
    return (), {}


def _law_geo(laws: dict, no: str) -> tuple:
    """その法則が名指ししている geo と、名前ごとの側を取り出す（M2-E-2）。戻り＝(geo の並び, {geo: 側})。"""
    for num, sel, _n in laws["counts"]:
        if num != no:
            continue
        g = sel.get("geo")
        g = () if g in (None, "any") else tuple(g)
        return g, dict(sel.get("側") or {})
    return (), {}


def _law_lineages(laws: dict, no: str) -> tuple:
    """その法則が名指ししている系統を取り出す（★2026-09-11・監査 cp35 の Critical C-1）。

    戻り＝系統の名前の並び。名指ししていなければ空。
    ★一覧をこの関数に書かない＝法則ファイルの「数える部品」の『系統』から取る。
    ★手本＝`_law_families`（family を読む・同じ作り）。

    ★なぜ要ったか（監査 cp35 の実測）
      直す前、帯の枠だけが法則を読んでいなかった（`_ranked_material_at(rng, "location", …)`＝
      役割の名前をコードに直書き）。監査が法則ファイルの写しを書き替えて試したところ、
      **R1・R3 の系統を「構造・位置」から「ボラ」に変えても、帯の材料が1文字も変わらなかった。**
      法則 R1・R3 が名指ししているのは **family ではなく「系統」**なので、`_law_families` では読めない。
      ＝系統を読む道が1つも無かった。この関数がその道。
    """
    for num, sel, _n in laws["counts"]:
        if num != no:
            continue
        return tuple(sel.get("系統") or [])
    return ()


_STAGE_CANDS_PATH = (HERE.parents[1] / ".claude" / "ratchet" / "m2_stage_candidates.json")
_STAGE_CANDS_MEMO: dict = {}


def stage_candidates(stage: str) -> dict:
    """その段の候補の元を、§2.2 の元データから読む（★手で書かない・2026-09-11）。

    戻り＝{"families": frozenset, "lineages": frozenset, "geo_cols": tuple,
           "pre": dict, "bool_col": str|None}
    段の名前＝"stage1" / "stage2a" / "stage2b" / "stage2c" / "stage3"。

    ★なぜ元データから読むか（まこさん指示 2026-09-11・逐語）
      「手書きで書き換えられないようにプログラムが読める対応付けをすればいいのでは？」
      「この文書の指標の表記が正本通りじゃないのであれば、正本から自動生成する形で修正すべきなのでは？」
    ★直す前＝`gen_stage0_match.py` の中に私（CC）が手で書いた語を読み、成績表に**部分一致**で
      当てていた。**写した一覧なので私が書き換えられる状態で、実際に本数が監査の実測に
      近づくまで絞り方を3回 書き換えた**（618本 → 444本 → 完全一致の形）。
    ★直した後＝元データの指標の名前に**完全一致**。元データに書ける名前は、正本
      （`indicator_reference_diag.FAMILY_LINEAGE`）に実在するものだけ＝
      `gen_regime_kb.py --write stage` が照らして、外れたら止まる（fail-closed）。
    """
    if not _STAGE_CANDS_MEMO:
        if not _STAGE_CANDS_PATH.exists():
            raise SampleError(f"§2.2 の候補の元データが無い: {_STAGE_CANDS_PATH}（fail-closed）")
        # ★展開（語 → 正本の指標の名前）は `gen_regime_kb.expand_stage` の1か所に置く。
        #   この関数・突き合わせの道具・§2.2 の表 の3つが、同じ関数を呼ぶ＝判定を書き写さない。
        _tools = HERE.parents[3] / ".claude" / "tools"
        if str(_tools) not in sys.path:
            sys.path.insert(0, str(_tools))
        try:
            import gen_regime_kb as _grk
            _ex = _grk.expand_stage()
        except SystemExit as e:                    # 正本と合わない＝fail-closed の拒否
            raise SampleError(f"§2.2 の候補の元データが正本と合わない: {e}")
        except Exception as e:                     # noqa: BLE001
            raise SampleError(f"§2.2 の候補の元データを読めない: {e}（fail-closed）")
        for _k, _s in _ex.items():
            _STAGE_CANDS_MEMO[_k] = {
                "families": frozenset(_s.get("families") or ()),
                "lineages": frozenset(_s.get("lineages") or ()),
                "geo_cols": tuple(_s.get("geo_cols") or ()),
                "pre": dict(_s.get("pre") or {}),
                # ★2026-09-27（M2-E-4e）＝窓つきの前処理（指標の名前 → {"op", "months"}）。
                #   固定の線と別に「動く線」の候補を作る（build_stage_candidates）。
                "pre_win": dict(_s.get("pre_win") or {}),
                "bool_col": _s.get("bool_col"),
                # ★2026-09-13（完成の条件 #4・まこさん決定「案1」「一本化する」）＝段の役割と法則の番号も
                #   元データから渡す。コードに法則の番号と役割を書かない（STAGE_SPEC に在った二重持ちを消した）。
                #   番号が法則ファイルに実在するかは `gen_regime_kb.expand_stage` が照らす（fail-closed）。
                "role": _s.get("role"),
                "law": _s.get("law"),
                "law_or": _s.get("law_or"),
                "law_width": _s.get("law_width"),
                # ★2026-09-16（監査 cp36 の M-3）＝時間足の条件を読む法則の番号。
                #   これが無いと `stage_tfs_of`・`stage_lineages_of` が法則を読めない。
                "law_tf": _s.get("law_tf"),
            }
        if not _STAGE_CANDS_MEMO:
            raise SampleError("§2.2 の候補の元データに段が0件（fail-closed）")
    if stage not in _STAGE_CANDS_MEMO:
        raise SampleError(f"§2.2 の候補の元データに {stage} が無い（fail-closed）")
    return _STAGE_CANDS_MEMO[stage]


STAGE_SPEC = {
    # 段ごとの「札・候補の元の引き方」＝設計書 4-4 の手順2〜8 の表。
    #   ★指標の名前をここに書かない＝候補の元は法則ファイル（family／系統）と §2.2（探す語）から読む。
    #   ★2026-09-13（完成の条件 #4・まこさん決定「案1」「一本化する」）＝「役割」と「法則の番号」を
    #     ここから外し、§2.2 の候補の元データ（`stage_candidates(段)` の role・law）から読む形にした。
    #     直す前は同じものを元データと二重に持ち、段3 の役割が食い違っていた（ここ＝None／元データ＝location）。
    # ★2026-10-01（B-6・まこさん決定「それでいいので進めて」）＝段1・段2c は強さ（場面の正解＝実際にレンジだったか）の順に並べる。
    #   直す前は None＝3つの正解を混ぜた順で、段1 の1位は「大きさ・先288本」で上がった
    "stage1":  {"label": "強さ", "pick": "lineage"},
    "stage2a": {"label": "強さ", "pick": "family"},
    "stage2b": {"label": None,   "pick": "bool_col"},
    "stage2c": {"label": "強さ", "pick": "family"},
    "stage3":  {"label": None,   "pick": "number"},
}
# ★符号を取り去る前処理を付ける指標は、ここに書かない（2026-09-11 に元データへ移した）。
#   出どころ＝`m2_stage_candidates.json` の段ごとの `pre` の欄（`stage_candidates(stage)["pre"]`）。
#   なぜ移したか＝指標の名前をコードに直書きすると、§2.2 が変わったとき片方だけ直って腐る
#   （恒久の決まり69番）。まこさん指示 2026-09-10「この件、毎回忘れて、設計に入れないし、
#   やろうとしないから、絶対入れろ」で足した前処理そのものは、1つも外していない。


# ★2026-09-27（M2-E-4e・設計書 m2e4e-r6-moving-line-20260927）＝窓つきの前処理の窓（月）を、実行データの足の本数に直す。
#   なぜ要るか＝前処理は実行データ（5分足）の並びに載った列に掛かる（engine_tuner_exec._col_array）。
#   だから窓の本数は、材料の時間足によらず5分足の本数で数える。
#   ★5 の出どころ＝要件 cat_requirements §4.6 の H7「5m が現行標準」と、実行データ（5分足の正本）。
#   ★1か月＝365.25 ÷ 12 日（暦の平均）。月の数は §2.2 の元データ（m2_stage_candidates.json の pre_win の months）が持ち、
#     その出どころは相場の法則の逐語 six-month。私は月の数を作らない。
_EXEC_BAR_MIN = 5


def pre_win_bars(pw: dict) -> int:
    """窓つきの前処理 {"op", "months"} の窓を、実行データ（5分足）の本数に直す（fail-closed）。"""
    months = pw.get("months")
    if not isinstance(months, int) or isinstance(months, bool) or months < 1:
        raise SampleError(f"窓つきの前処理の月の数が不正: {months!r}（1 以上の整数・fail-closed）")
    return int(round(months * 365.25 / 12 * 1440 / _EXEC_BAR_MIN))


def stage_warm(base_warm):
    """§2.2 の元データに窓つきの前処理（pre_win）が在れば、データの前の余白を「いまの余白＋いちばん長い窓」にする。

    ★2026-09-27（M2-E-4e・まこさん決定「余白の直し方→C」）＝動く線を使う走行（この道具の本走 run_main）だけ余白を延ばす。
      窓の最初の1本の材料にも、いまの余白（指標の助走）が要るので、足し算にする。
      恒等の走行・H2 など、この関数を呼ばない走行の余白は今のまま（engine_tuner.WARM）。
    """
    months = [int(pw["months"]) for k in STAGE_SPEC for pw in stage_candidates(k)["pre_win"].values()]
    if not months:
        return base_warm
    return base_warm + pd.Timedelta(minutes=pre_win_bars({"months": max(months)}) * _EXEC_BAR_MIN)


def _col_in_param_range(col: str, family: str, want: dict | None) -> bool:
    """その列の数字が、設定の欄 `param_range` の中に在るか（M2-E-2 の M-1・2026-09-16 新設）。

    want ＝ {指標の名前: [{"lo":…, "hi":…}, …]}（軸の数だけ並べる）。書いていない指標は絞らない。
    ★数字は列の名前から読む（`_mat_from_col` と同じ `iref.find`）＝CC が数字を作らない。
    ★軸の数が合わなければ止める（黙って通さない）。
    """
    if not want or family not in want:
        return True
    ent, params = iref.find(str(col).split("__")[0])
    if ent is None or params is None:
        raise SampleError(f"成績表の列の名前から数字を取り出せない: {col}（fail-closed）")
    spec = want[family]
    if len(spec) != len(params):
        raise SampleError(f"stage_limits の param_range の軸の数が合わない: {family}"
                          f"（欄 {len(spec)} 軸／列 {len(params)} 軸）")
    for r, v in zip(spec, params):
        if r.get("lo") is not None and float(v) < float(r["lo"]):
            return False
        if r.get("hi") is not None and float(v) > float(r["hi"]):
            return False
    return True


def _check_bundle_counts(laws: dict, build: dict, table) -> list:
    """束ぜんたいで数える法則を、組んだ後に確かめる（M2-E-2 の M-3・2026-09-16 新設）。

    戻り＝満たさなかった法則の説明の並び（空なら全部 満たしている）。

    ★数えるのは実行器の関数（`engine_tuner_exec._law_count`）＝審査（G7）と同じ数え方。
      ここに数え方を書き写さない（恒久の決まり69番・同じ判定を2か所に持たない）。
    ★見るのは「時間足」を数える法則だけ（＝C4）。family・系統・geo を数える法則は、
      枠を選ぶ時点で決まるので、ここでは見ない（二重に落とさない）。
    ★本数も「執行足より上」も、法則ファイルの「数える部品」から読む＝コードに書かない。
    """
    ng = []
    for num, sel, n in laws["counts"]:
        if sel.get("時間足") != "執行足より上":
            continue
        try:
            # ★入れ物の形と集め方は、実行器の審査（`_check_scene_rules`:1432）と同じ1行を使う。
            seen = {"geo": set(), "fams": set(), "tfs": set(), "parts": set(),
                    "not": False, "hysteresis": False, "forms": set(), "on_parts": []}
            ex._scene_scan((build["entry"] or {}).get("tree"), seen)
            got = ex._law_count(sel, seen)
        except Exception as e:                     # noqa: BLE001  数えられない＝止めない（審査が後で見る）
            ng.append(f"{num}: 数えられない（{str(e)[:40]}）")
            continue
        if got < int(n):
            ng.append(f"{num}: 執行足より上の部品が {got} 本（法則は {n} 本 以上）")
    return ng


def _law_tf_upper(laws: dict, no: str) -> bool:
    """その法則が「執行足より上」を数える部品に持つか（M2-E-2 の M-3・2026-09-16）。

    ★一覧をこの関数に書かない＝法則ファイルの「数える部品」の『時間足』から読む。
    ★手本＝`_law_families`（family を読む）・`_law_lineages`（系統を読む）。同じ作り。
    """
    if not no:
        return False
    for num, sel, _n in laws["counts"]:
        if num == no and sel.get("時間足") == "執行足より上":
            return True
    return False


def _law_tf_lineages(laws: dict, no: str) -> tuple:
    """その法則が「かつ」で系統を名指ししていれば、その系統（M2-E-2 の M-3・2026-09-16）。

    ★R3 は「かつ」が真＝1本の部品が 系統・時間足・geo を全部 満たすことを求める。
      だから R3 を時間足の法則に使う段（段1）は、系統の絞りも R3 から受ける。
    ★C4 は「かつ」を持たない＝時間足だけを数える。系統の絞りは掛からない。
    """
    if not no:
        return ()
    for num, sel, _n in laws["counts"]:
        if num == no and sel.get("かつ"):
            return tuple(sel.get("系統") or [])
    return ()


def drop_tfs_of(limits: dict, table) -> list:
    """絞り込みの段で使わない時間足（M2-E-2 の M-1・2026-09-16 新設）。

    ★欄が無い・null＝既定の3本（1分足・3分足・10分足＝まこさん決定 2026-09-10）。
    ★配列＝そのまま使う。**空の配列は「外さない」**（設定ファイルの注記のとおり）。
      直す前＝`limits.get("drop_tfs") or [...]` と書いてあったので、空の配列は
      Python では偽になり、既定の3本へ戻っていた（監査 cp36 の M-1・§6 の183番）。
    ★時間足の表に無い名前が1つでも在れば止める（fail-closed・CC が名前を作らない）。
    """
    v = limits.get("drop_tfs")
    if v is None:
        return ["1m", "3m", "10m"]
    if not isinstance(v, list):
        raise SampleError(f"drop_tfs は配列で書く（いまの形＝{type(v).__name__}）")
    bad = [t for t in v if t not in set(table["tfs"])]
    if bad:
        raise SampleError(f"drop_tfs に時間足の表に無い名前: {bad}（表＝{list(table['tfs'])}）")
    return list(v)


def stage_limits_of(stage: str, limits: dict, table) -> dict:
    """その段の設定の欄（`stage_limits.<段>`）を読んで確かめる（M2-E-2 の M-1・2026-09-16 新設）。

    戻り＝{"tfs": [...]|None, "families": [...]|None, "quantiles": [...]|None,
           "param_range": {...}|None}（書いていない鍵は None＝絞らない）

    ★止めるもの（fail-closed・どれも「CC が数字を作らない」ため）
      ①知らない段の名前 ②知らない鍵 ③時間足の表に無い名前
      ④承認済みの範囲（`quantile_range`）の外の分位 ⑤段2b・段3 に鍵を書いたとき
    ★いまは空＝既定で動く（`search_limits.json` の `stage_limits` は {}）。
      何を書くかは まこさんが決める（設定ファイルの注記の逐語）。
    """
    all_ = limits.get("stage_limits") or {}
    if not isinstance(all_, dict):
        raise SampleError(f"stage_limits は辞書で書く（いまの形＝{type(all_).__name__}）")
    bad_stage = [k for k in all_ if k not in STAGE_SPEC]
    if bad_stage:
        raise SampleError(f"stage_limits に知らない段: {bad_stage}（使えるのは {sorted(STAGE_SPEC)}）")
    # ★書けない段は、どの段を読むときでも止める（設定を書いた時点の誤りなので、
    #   その段を組むときまで気づかないのは遅い）。
    no_write = [k for k in all_ if k in ("stage2b", "stage3") and all_.get(k)]
    if no_write:
        raise SampleError(f"stage_limits には書けない段: {no_write}"
                          "（段2b は真偽の列1本・段3 は本数の並び＝絞る軸が無い）")
    d = all_.get(stage) or {}
    if not d:
        return {"tfs": None, "families": None, "quantiles": None, "param_range": None}
    ok_keys = {"tfs", "families", "quantiles", "param_range"}
    bad_key = [k for k in d if k not in ok_keys]
    if bad_key:
        raise SampleError(f"stage_limits.{stage} に知らない鍵: {bad_key}（使えるのは {sorted(ok_keys)}）")
    tfs_v = d.get("tfs")
    if tfs_v is not None:
        bad = [t for t in tfs_v if t not in set(table["tfs"])]
        if bad:
            raise SampleError(f"stage_limits.{stage}.tfs に時間足の表に無い名前: {bad}")
    q_v = d.get("quantiles")
    if q_v is not None:
        _lo, _hi = q_range_of(limits)              # 承認済みの範囲（`quantile_range`）
        bad = []
        for q in q_v:
            s = str(q)
            if not (s.startswith("q") and s[1:].isdigit() and _lo <= int(s[1:]) <= _hi):
                bad.append(q)
        if bad:
            raise SampleError(f"stage_limits.{stage}.quantiles が承認済みの範囲の外: {bad}"
                              f"（範囲＝q{_lo}〜q{_hi}・形は「q30」）")
    pr_v = d.get("param_range")
    if pr_v is not None:
        # ★カタログ（材料の範囲）より広い範囲は止める＝設定で候補を増やせない（狭めるだけ）。
        #   出どころ＝`search_limits.json` の `_material_param_ranges_note` の逐語
        #   「ここに書いた範囲は 材料カタログの数字を含まなくてよい（狭めるのが目的）」。
        _cat = material_ranges()
        for _fam, _spec in pr_v.items():
            _base = _cat.get(_fam)
            if _base is None:
                raise SampleError(f"stage_limits.{stage}.param_range にカタログに無い指標: {_fam}")
            if len(_spec) != len(_base):
                raise SampleError(f"stage_limits.{stage}.param_range の軸の数が合わない: {_fam}"
                                  f"（欄 {len(_spec)} 軸／カタログ {len(_base)} 軸）")
            for _r, _b in zip(_spec, _base):
                if _r.get("lo") is not None and float(_r["lo"]) < float(_b["lo"]):
                    raise SampleError(f"stage_limits.{stage}.param_range が カタログより広い: "
                                      f"{_fam} の下限 {_r['lo']}（カタログ {_b['lo']}）")
                if _r.get("hi") is not None and float(_r["hi"]) > float(_b["hi"]):
                    raise SampleError(f"stage_limits.{stage}.param_range が カタログより広い: "
                                      f"{_fam} の上限 {_r['hi']}（カタログ {_b['hi']}）")
    return {"tfs": tfs_v, "families": d.get("families"), "quantiles": q_v,
            "param_range": pr_v}


def stage_tfs_of(stage: str, spec_c: dict, laws: dict, table, tfs, limits) -> set:
    """その段で使ってよい時間足（M2-E-2 の M-1・M-3・2026-09-16 新設）。

    順番（設計書 4-3）
      ①役割の時間足 → ②`law_tf` の法則が「執行足より上」を持てばその絞り
      → ③`drop_tfs_of` を引く → ④`stage_limits.<段>.tfs` があれば、その中だけ

    ★②はコードに直書きしない＝段の元データの `law_tf`（段1＝R3・段2a＝C4）が指す法則の
      「数える部品」の『時間足』を読む（監査 cp36 の M-3）。欄が無い段は絞らない。
    ★段2c に `law_tf` を書いていない＝執行足（5分足）も候補に入る。
      出どころ＝§2.2-3 の逐語「段2c（役割 sufficiency＝全時間足）からも 1m・3m・10m を外す」。
    ★1本も残らなければ止める（fail-closed・黙って0本にしない）。
    """
    ok = set(_role_tfs(tfs, table, spec_c["role"]))
    if _law_tf_upper(laws, spec_c.get("law_tf")):
        _all = list(table["tfs"])
        ok &= {t for t in _all if _all.index(t) > _all.index("5m")}
    ok -= set(drop_tfs_of(limits, table))
    want = stage_limits_of(stage, limits, table)["tfs"]
    if want is not None:
        out_of = [t for t in want if t not in ok]
        if out_of:
            raise SampleError(f"stage_limits.{stage}.tfs が、その段で使える時間足の外: {out_of}"
                              f"（使えるのは {sorted(ok)}）")
        ok &= set(want)
    if not ok:
        raise SampleError(f"{stage} で使える時間足が1本も無い（fail-closed）")
    return ok


def stage_lineages_of(stage: str, spec_c: dict, laws: dict) -> tuple:
    """その段で使ってよい系統（M2-E-2 の M-3・2026-09-16 新設）。

    ★`law` の系統（無ければ `law_or`）と、`law_tf` の法則が「かつ」で系統を持てばその系統、
      の**両方に入るもの**だけを返す。
    ★なぜ両方か＝段1 は R1（構造・位置を1本）と R3（構造・位置の部品が上位足に在る）の両方が
      掛かる。片方だけを読むと、もう片方を書き替えても束が変わらない（監査 cp36 の M-3）。
    ★重ならなければ止める（fail-closed・黙って0件にしない）。
    ★`law_tf` が「かつ」を持たない段（段2a＝C4）は、`law` の系統をそのまま返す。
    """
    base = _law_lineages(laws, spec_c["law"])
    if not base and spec_c.get("law_or"):
        base = _law_lineages(laws, spec_c["law_or"])
    extra = _law_tf_lineages(laws, spec_c.get("law_tf"))
    if not extra:
        return tuple(base)
    both = tuple(x for x in base if x in set(extra))
    if base and not both:
        raise SampleError(f"{stage}: 法則が名指しする系統が重ならない"
                          f"（{spec_c['law']}／{spec_c.get('law_or')}＝{sorted(base)} ／ "
                          f"{spec_c.get('law_tf')}＝{sorted(extra)}）")
    return both or tuple(extra)


def build_stage_candidates(stage: str, laws: dict, table, tfs, limits) -> list[dict]:
    """その段の候補を全部 返す（成績表の順・乱数を1か所も使わない）。

    stage ＝ "stage1" | "stage2a" | "stage2b" | "stage2c" | "stage3"
    laws  ＝ laws_for_scene("range") の戻り（法則ファイルから読んだもの）
    戻り  ＝ 候補の一覧（鍵11個・分離力の高い順。★動く線〔鍵 pre_win を足した12個〕は、固定の線を全部 並べた後ろに同じ順で続く・M2-E-4e）

    ★2026-09-13（98回目・監査 cp36 の C-1・C-2）＝実際に束を組む2本目（`sample_regime_build`）は、
      この一覧の順位から候補を取る（`_stage_pick`）。3つの絞り（外す時間足・§2.2 の元データ・
      符号を取り去る前処理）はこの関数にだけ置く＝2本目に写さない。
      直す前は2本目が別の道（法則の系統／family で成績表の順位から引く）で材料を取っていて、
      3つの絞りが実際の束に掛かっていなかった。使われていなかった引数 `fixed` は消した。

    ★2026-09-11（M2-E-3 の手順4・5）＝設計書 4-2 の「候補1件の形」をそのまま返す。
      **各枠が出すのは1本ではない**（まこさん指摘 2026-09-10＝「各段で出力するロジックは１本ではない」）。
    ★候補1件＝材料の組（種類 × 時間足）× 側 × 閾値の分位（設計書 4-2 の「候補の軸」）。
      側は法則が family ごとに持つものを使い、閾値の分位は **1点**（まこさん決定 2026-09-11
      ＝「じゃあ、まず１点でつくる」）。だから本数は材料の組の数そのもの。
    ★この関数は審査（G7）を掛けない＝`law_check` は "—" で返す。審査は束に組んでから掛ける
      （1つの枠だけでは法則を満たせないため）。★落ちた候補も消さない（§2.2 の共通の決まり）。
    """
    spec = STAGE_SPEC.get(stage)
    if spec is None:
        raise SampleError(f"知らない段: {stage}（使えるのは {sorted(STAGE_SPEC)}）")
    # ★§2.2 の候補の元データ（手で書かない）。段の役割と法則の番号も、ここから読む
    #   （2026-09-13・完成の条件 #4・まこさん決定「案1」「一本化する」）。
    spec_c = stage_candidates(stage)
    # ★閾値の分位＝1点（まこさん決定 2026-09-11）。承認済みの範囲の真ん中を使う
    #   ＝私が数字を作らない（両端は `search_limits.json` の `quantile_range`）。
    # ★2026-09-13（98回目・監査 cp36 の C-1）＝値は `_thr_fixed(limits)`（同じ1点＋範囲の印 `_q_src`）。
    #   直す前は印の無い {"threshold_q": q} だった。2本目がこの一覧の cond をそのまま束に使うので、
    #   2本目が今まで持っていた印を失わないように、ここで付ける。
    out: list[dict] = []

    if stage == "stage2b":                         # 向きの否定＝承認済みの借用が1本だけ
        # ★列の名前は §2.2 の元データ（`m2_stage_candidates.json` の `bool_col`）から読む。
        #   出どころ＝まこさん決定 2026-09-01「承認済みの借用」。自前の向きは M2-M。
        _bc = spec_c["bool_col"]
        if not _bc:
            raise SampleError("段2b の真偽の列が §2.2 の元データに無い（fail-closed）")
        out.append({"stage": stage, "rank": 1, "col": _bc, "family": None,
                    "tf": None, "acc": None, "label": None, "horizon": None,
                    "cond": {"not": {"bool_col": _bc, "want": True}},
                    "law_check": "—", "dropped_by": None})
        return out

    if stage == "stage3":                          # 持続＝材料でなく数字の候補（本数）
        # ★本数は承認済みの範囲（`int_range`）の整数を全部 並べる＝乱数を使わない・数字を作らない。
        _n_lo, _n_hi = int_range_of(limits, n_min=2)
        for i, n in enumerate(range(_n_lo, _n_hi + 1), start=1):
            out.append({"stage": stage, "rank": i, "col": None, "family": None, "tf": None,
                        "acc": None, "label": None, "horizon": None,
                        "cond": {"role": spec_c["role"], "form": "streak", "value": {"n": int(n)}},
                        "law_check": "—", "dropped_by": None})
        return out

    role, label = spec_c["role"], spec["label"]
    ranges = material_ranges()
    rr = table["roles"][role]
    # ★2026-09-16（監査 cp36 の M-1・M-3）＝時間足と系統を、法則ファイルと設定の欄から読む。
    #   直す前＝「5m より後ろ」をここに直書きし、法則 C4 を書き替えても束が変わらなかった。
    #   直す前＝`limits.get("drop_tfs") or [...]` で、空の配列が既定の3本に戻っていた。
    #   直した後＝`stage_tfs_of`／`stage_lineages_of`／`drop_tfs_of`／`stage_limits_of` の4つが読む。
    #   ★同じ判定を2か所に書かない＝2本目（`sample_regime_build`）も同じ関数を呼ぶ。
    ok_tfs = stage_tfs_of(stage, spec_c, laws, table, tfs, limits)
    _st_lim = stage_limits_of(stage, limits, table)
    _law = spec_c["law"]                           # ★法則の番号は元データから（コードに書かない・#4）
    fams_law, side_law = _law_families(laws, _law)
    lins_law = stage_lineages_of(stage, spec_c, laws)
    # ★2026-09-27（M2-E-4e）＝「動く線」の候補（窓つきの前処理を付けたもの）。固定の線の候補を全部 並べた後ろに足す
    #   ＝固定の線の順位を1つも変えない（束を組む側は順位で3枠目を取るので、いまの束は変わらない）。
    _moving: list[dict] = []
    _seen_c: set = set()                           # ★2026-10-01（B-5）＝同じ条件の候補を2回 並べない
    rank = 0
    for fam, tf, lab, hor, med, ncol, col in ranked_groups(role, label):
        if fam not in iref.FAMILY_LINEAGE or fam not in ranges:
            continue
        if iref.FAMILY_LINEAGE[fam]["k"] not in rr["lineages"]:
            continue
        if tf not in ok_tfs:
            continue
        # ★2026-09-11（手順9）＝「その列の数字で使えるか」も見る（乱数で引き直さなくなったため）
        if not _group_usable_col(col, fam, tf, ranges, table):
            continue
        if spec["pick"] == "family":               # 段2a・段2c＝法則が名指しした family だけ
            if fams_law and fam not in fams_law:
                continue
        else:                                      # 段1＝法則が名指しした系統だけ
            if lins_law and iref.FAMILY_LINEAGE[fam]["k"] not in lins_law:
                continue
        # ★§2.2 が挙げた候補で絞る＝元データの**指標の名前に完全一致**するもの、または
        #   元データが**系統でまとめて足した分**に属するものだけを通す。
        #   ★2026-09-11（まこさん指示「手書きで書き換えられないようにプログラムが読める
        #     対応付けをすればいいのでは？」）に、部分一致をやめてここに直した。
        #   ★直す前に私がやった誤り（記録として残す）＝本数が監査の実測（354本）に近づくまで
        #     絞り方を3回 書き換えた（①列の名前に部分一致 618本 ②指標の名前に部分一致 444本
        #     ③名前の先頭が合うもの）。**数字を合わせるために絞り方を変えたもので、不正。**
        #     いまの形は、元データの名前と照らすだけ＝本数に合わせて動かせない。
        # ★2026-09-19（設計書 m2c-width-and-stage-candidates-20260918・まこさん承認）＝
        #   §2.2 の元データの名前の一覧で落とす絞りを **消した**。
        #   なぜ＝どの指標を使うかは M2-C の印（indicator_switch.json）が決める。
        #   その印より狭い2つ目の絞りを私（CC）が M2-E-3 で足したせいで、印がオンで法則も許す
        #   指標（構造・位置の系統の多く・MMI・SQZ_ON）が候補に出ていなかった。
        #   まこさんの条件（2026-09-18）＝「印でオンにした指標だけを、候補の母集団として読み込む」。
        #   ★元データ（m2_stage_candidates.json）の語の欄は消さない＝§2.2 の文の写しとして表に残り、
        #     前処理（pre）・役割（role）・法則の番号（law・law_width）・幾何の列・真偽の列は今までどおり読む。
        #   ★候補を決めるのは 印・法則・役割（型の表）・時間足・標本不足・設定の欄 stage_limits だけ。
        # ★2026-09-16（監査 cp36 の M-1）＝設定の欄 `stage_limits.<段>.families` で さらに絞る。
        #   書いていなければ絞らない（いまは空＝既定で動く）。
        if _st_lim["families"] is not None and fam not in set(_st_lim["families"]):
            continue
        # ★2026-09-16（監査 cp36 の M-1）＝設定の欄 `param_range` で、列の数字を絞る。
        if not _col_in_param_range(col, fam, _st_lim["param_range"]):
            continue
        rank += 1
        # ★材料は `_mat_from_col`（成績表の列の名前から作る）＝乱数を1か所も使わない。
        #   ★2026-09-16（監査 cp36 の M-7 の #7）＝説明の文を実物に合わせた。
        #     直す前の文「材料は `_mat_drawn`…数字はその中で範囲から引く」「乱数を外すのは手順9」は、
        #     2026-09-11（手順9）で `_mat_from_col` に替えた後も残っていた古い文。
        #   ★同じ候補の一覧なら、何回 呼んでも同じ材料が出る（列の数字をそのまま読むため）。
        m = _mat_from_col(col, fam, tf, ranges, table=table)
        side = side_law.get(fam, "above" if stage == "stage1" else "below")
        if stage == "stage2a":
            # ★符号を取り去る前処理＝元データの `pre` の欄から引く（指標の名前を直書きしない）
            _op = spec_c["pre"].get(fam)
            if _op:
                m = {**m, "pre": {"op": _op}}
            # 法則が言う側の逆を `not` で包む（入る線は「強いと言えない」）
            strong_side = "above" if side == "below" else "below"
            cond = {"not": {"role": role, "form": "level", "material": [m],
                            "side": strong_side, "value": _thr_fixed(limits)}}
        else:
            cond = {"role": role, "form": "level", "material": [m],
                    "side": side, "value": _thr_fixed(limits)}
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001 の B-5）＝条件の中身が同じ候補は、最初の1本（順位の高い方）だけを残す。
        #   ranked_groups は（正解・先読み・種類・時間足）の組ごとに出すので、同じ種類×時間足の同じ列が最大6回 並んでいた
        #   （段1 は 2,487行のうち中身の違う列 812・worklog 20260928 §15 の 15-8）
        _ck = json.dumps(cond, sort_keys=True, ensure_ascii=False)
        if _ck in _seen_c:
            rank -= 1
            continue
        _seen_c.add(_ck)
        # ★2026-09-16（監査 cp36 の M-1）＝設定の欄 `stage_limits.<段>.quantiles` が在れば、
        #   材料1つにつき、その分位の数だけ候補を作る（分位の順）。
        #   書いていなければ、いままでどおり真ん中の1点だけ（まこさん決定 2026-09-11）。
        _qs = _st_lim["quantiles"]
        for _iq, _q in enumerate(_qs if _qs else [None]):
            _c = cond
            if _q is not None:
                _c = json.loads(json.dumps(cond))          # 1件ずつ別の辞書にする
                _inner = _c["not"] if "not" in _c else _c
                _inner["value"] = {**_inner["value"], "threshold_q": str(_q)}
            # ★2026-10-03（工事 m2f-stage-quantile-rank-20261003・T40②）＝分位ごとの候補に別々の順位を付ける＝材料の順 → 分位の順の通し番号。
            #   直す前は `rank_q = rank if _q is None else rank` で、同じ材料の分位の候補に同じ順位が付いた（9点を書くと T40② が落ちた）。
            if _iq > 0:
                rank += 1
            rank_q = rank
            out.append({"stage": stage, "rank": rank_q, "col": col, "family": fam, "tf": tf,
                        "acc": med, "label": lab, "horizon": hor, "cond": _c,
                        "law_check": "—", "dropped_by": None})
            # ★2026-09-27（M2-E-4e）＝この指標に窓つきの前処理（pre_win）が在れば、同じ閾値の「動く線」の候補も作る。
            #   材料に前処理を付けるだけ＝側と閾値の分位は固定の線と同じ（法則が決める側・まこさん決定の1点）。
            _pw = spec_c["pre_win"].get(fam)
            if _pw:
                _cm = json.loads(json.dumps(_c))
                _inm = _cm["not"] if "not" in _cm else _cm
                _inm["material"] = [{**_inm["material"][0],
                                     "pre": {"op": _pw["op"], "n": pre_win_bars(_pw)}}]
                _moving.append({"stage": stage, "rank": None, "col": col, "family": fam, "tf": tf,
                                "acc": med, "label": lab, "horizon": hor, "cond": _cm,
                                "law_check": "—", "dropped_by": None, "pre_win": dict(_pw)})
    for _mv in _moving:                            # ★動く線は、固定の線の後ろに順位を続けて並べる（M2-E-4e）
        rank += 1
        _mv["rank"] = rank
        out.append(_mv)
    if not out:
        raise SampleError(f"{stage} の候補が0件（法則 {_law} の名指し・§2.2 の語・型の表の絞りの後）")
    return out


def _roles_for_lineage(table, lineage: str) -> list:
    """その系統を使える役割を、承認済みの型の表から引く（★2026-09-19・新設）。

    なぜ要るか＝型の表は「役割 → 系統」の向きしか持たない（`table["roles"][role]["lineages"]` が
      8か所）。帯の幅の指標（BB幅・Donchian幅・HWC幅%）は系統が **ボラ** で、役割 location では
      引けない（型の表の location の系統は「構造・位置」だけ・2026-09-19 に実測）。
      ＝系統から役割を引く道が要る。**役割の名前をコードに書かない**（恒久の決まり69番）。
    戻り＝役割の名前の並び（型の表が宣言した順）。
    """
    return [r for r, v in (table.get("roles") or {}).items()
            if lineage in ((v or {}).get("lineages") or [])]


def build_width_candidates(laws: dict, table, tfs, limits: dict, law_no: str | None = None) -> list:
    """帯の幅の枠（A）の候補の一覧を作る（★2026-09-19・新設・設計書 m2c-width-and-stage-candidates-20260918）。

    ★何をするか＝法則 R7（帯の幅）が名指しした **geo（レンジ幾何の列）と family（指標）の両方**から
      候補を作り、成績表の順位で並べて返す。戻りの鍵は `build_stage_candidates` と同じ
      （束が取る `_stage_pick` が読むため）。

    ★なぜ要るか（まこさん指摘 2026-09-18・逐語）＝「帯の幅を見る指標はBB等、もっといっぱいある」。
      直す前は `sample_regime_build` が `_law_geo` の先頭（W%）を固定で使い、法則に戻した指標3件を
      1本も読まなかった。

    ★並び＝レンジ幾何を先頭、その後ろに指標を成績表の順位（強い順）。乱数は1か所も使わない（恒久67番）。
    ★絞りは既にある関数を呼ぶ＝`ranked_groups`（印がオフの指標は手前で落ちる）・`_group_usable_col`
      （その列の数字で使えるか）・`stage_tfs_of`（法則と設定の欄から時間足）。判定を書き写さない。
    ★役割は `_roles_for_lineage` が型の表から引く（コードに役割の名前を書かない）。
    """
    spec_c = stage_candidates("stage1")
    no = law_no or spec_c["law_width"]
    geo_names, geo_side = _law_geo(laws, no)
    fams_law, side_law = _law_families(laws, no)
    ranges = material_ranges()
    ok_tfs = stage_tfs_of("stage1", spec_c, laws, table, tfs, limits)
    out: list[dict] = []
    rank = 0
    for g in geo_names:                            # ① レンジ幾何の列（役割は段1 と同じ＝型の表が geo を許す役割）
        rank += 1
        out.append({"stage": "width", "rank": rank, "col": None, "family": None, "tf": None,
                    "acc": None, "label": None, "horizon": None,
                    "cond": {"role": spec_c["role"], "form": "level", "material": [{"geo": g}],
                             "side": geo_side.get(g, "above"), "value": _thr_fixed(limits)},
                    "law_check": "—", "dropped_by": None})
    seen_role: dict = {}
    for fam in fams_law:                           # ② 法則が名指しした指標（系統から役割を引く）
        lin = (iref.FAMILY_LINEAGE.get(fam) or {}).get("k")
        if not lin:
            continue
        for role in _roles_for_lineage(table, lin):
            rr = table["roles"][role]
            for f2, tf, lab, hor, med, _n, col in ranked_groups(role, None):
                if f2 != fam or tf not in ok_tfs:
                    continue
                if iref.FAMILY_LINEAGE[f2]["k"] not in rr["lineages"] or f2 not in ranges:
                    continue
                if not _group_usable_col(col, f2, tf, ranges, table):
                    continue
                if (f2, tf) in seen_role:          # 同じ 指標×時間足 は1回だけ（役割が2つに掛かるため）
                    continue
                seen_role[(f2, tf)] = role
                rank += 1
                m = _mat_from_col(col, f2, tf, ranges, table=table)
                out.append({"stage": "width", "rank": rank, "col": col, "family": f2, "tf": tf,
                            "acc": med, "label": lab, "horizon": hor,
                            "cond": {"role": role, "form": "level", "material": [m],
                                     "side": side_law.get(f2, "above"), "value": _thr_fixed(limits)},
                            "law_check": "—", "dropped_by": None})
    if not out:
        raise SampleError(f"帯の幅の候補が0件（法則 {no} が geo も family も名指ししていない・fail-closed）")
    return out


def _material_for_lineage(role, lineages, rank_pos: int, tfs, table, label=None,
                          tf_ok=None, ranges: dict | None = None) -> tuple[dict, dict]:
    """法則が名指しした **系統** の中から、成績表の順位の上から rank_pos 番目を取る（監査 cp35 の C-1）。

    ★`_material_for_law` との違い＝あちらは family（指標の名前）で絞る。こちらは **系統**で絞る。
      法則 R1・R3 は family を名指しせず、系統「構造・位置」だけを名指しするので、この形が要る。
    ★`_ranked_material_at` の中の1行（役割が持つ系統で絞る）を、法則が名指しした系統に替えたもの。
    ★2026-09-16（監査 cp36 の M-7 の #8）＝説明の文を実物に合わせた。
      直す前の文「材料の数字は `_mat_drawn` が範囲から引く」「乱数を外すのは手順9」は、
      2026-09-11（手順9）で `_mat_from_col`（成績表の列の数字をそのまま読む）に替えた後も
      残っていた古い文。**いまは乱数を1か所も使わない。**
    戻り＝(材料, 記録)。足りなければ SampleError。
    """
    rr = table["roles"][role]
    ok_tfs = set(tf_ok if tf_ok is not None else _role_tfs(tfs, table, role))
    ranges = ranges if ranges is not None else material_ranges()
    want = set(lineages or ())
    if not want:
        raise SampleError(f"法則が系統を名指ししていない（役割 {role}・fail-closed）")
    n = 0
    for fam, tf, lab, hor, med, ncol, col in ranked_groups(role, label):
        if fam not in iref.FAMILY_LINEAGE or fam not in ranges:
            continue
        if iref.FAMILY_LINEAGE[fam]["k"] not in want:      # ★法則が名指しした系統だけを数える
            continue
        if iref.FAMILY_LINEAGE[fam]["k"] not in rr["lineages"]:
            continue                                       # ★型の表（役割×系統）も満たす
        if tf not in ok_tfs:
            continue
        # ★2026-09-11（手順9）＝「その列の数字で使えるか」も見る（乱数で引き直さなくなったため）
        if not _group_usable_col(col, fam, tf, ranges, table):
            continue
        n += 1
        if n != int(rank_pos):
            continue
        # ★2026-09-11（手順9）＝数字を乱数で引くのをやめ、成績表の列の数字をそのまま使う。
        m = _mat_from_col(col, fam, tf, ranges, table=table)
        if _banned_pair(m, table):
            raise SampleError(f"{role} の {rank_pos} 位（{fam}×{tf}）の列の数字が"
                              f"禁止3（標本不足）: {col}")
        return m, {"rank": int(rank_pos), "col": col, "種類": fam, "時間足": tf, "label": lab,
                   "horizon": hor, "分離力": med, "列の本数": int(ncol),
                   "法則が名指しした系統": sorted(want)}
    raise SampleError(f"{role}/{label or '全ラベル'} の順位に {rank_pos} 位が無い"
                      f"（使える候補 {n} 本・法則が名指しした系統＝{sorted(want)}）")


def _material_for_law(role, fams, rank_pos: int, tfs, table, label=None, tf_ok=None,
                      ranges: dict | None = None) -> tuple[dict, dict]:
    """法則が名指しした family の中から、成績表の順位の上から rank_pos 番目を取る（M2-E-2）。

    ★`_ranked_material_at` との違い＝あちらは役割の全部から順位を数える。こちらは
      **法則が名指しした family だけ**を数える。だから法則を書き替えると、選ばれる材料が変わる。
    ★私（CC）が名前を選ばない＝名前の一覧は法則ファイルから来る。順位は成績表から来る。
    ★fams が空なら `_ranked_material_at` と同じ（役割の全部から取る）。
    戻り＝(材料, 記録)。足りなければ SampleError。
    """
    rr = table["roles"][role]
    ok_tfs = set(tf_ok if tf_ok is not None else _role_tfs(tfs, table, role))
    ranges = ranges if ranges is not None else material_ranges()
    want = set(fams or ())
    n = 0
    for fam, tf, lab, hor, med, ncol, col in ranked_groups(role, label):
        if want and fam not in want:                     # ★法則が名指しした family だけを数える
            continue
        if tf not in ok_tfs or fam not in iref.FAMILY_LINEAGE or fam not in ranges:
            continue
        if iref.FAMILY_LINEAGE[fam]["k"] not in rr["lineages"]:
            continue
        # ★2026-09-11（手順9）＝「その列の数字で使えるか」も見る（乱数で引き直さなくなったため）
        if not _group_usable_col(col, fam, tf, ranges, table):
            continue
        n += 1
        if n != int(rank_pos):
            continue
        # ★2026-09-11（手順9）＝数字を乱数で引くのをやめ、成績表の列の数字をそのまま使う。
        m = _mat_from_col(col, fam, tf, ranges, table=table)
        if _banned_pair(m, table):
            raise SampleError(f"{role} の {rank_pos} 位（{fam}×{tf}）の列の数字が"
                              f"禁止3（標本不足）: {col}")
        return m, {"rank": int(rank_pos), "col": col, "種類": fam, "時間足": tf, "label": lab,
                   "horizon": hor, "分離力": med, "列の本数": int(ncol),
                   "法則が名指しした family": sorted(want) if want else "（名指し無し＝役割の全部）"}
    raise SampleError(f"{role}/{label or '全ラベル'} の順位に {rank_pos} 位が無い"
                      f"（使える候補 {n} 本・法則が名指しした family＝{sorted(want) if want else '無し'}）")


def _flip_loose(limits, c: dict) -> dict:
    """水準の条件を「緩い側へずらして反転」した条件＝出る線（off）の部品（法則 C6 の②）。
    above q → below q'（q' < q）／ below q → above q'（q' > q）。

    ★2026-09-11（手順9）＝引数から `rng` を落とした。ずらす先は隣の段に決め打ちする
      （`_loose_q_fixed`）＝乱数を使わない（恒久の決まり67番）。
    """
    out = json.loads(json.dumps(c))
    out["value"]["threshold_q"] = _loose_q_fixed(limits, c["value"]["threshold_q"], c["side"])
    out["side"] = "below" if c["side"] == "above" else "above"
    return out


def stage_keep_of(limits: dict, n_cands: int) -> int:
    """設定の欄 `stage_keep_range` を読み、その段で使ってよい候補の本数（keep）を返す。

    ★2026-09-13（98回目・監査 cp36 の C-2）＝直す前は、この欄を読むコードが0か所で、`keep` は 1 の直書きだった。
    ★読むのは上端＝「その段では、成績表の順位が上端以内の候補だけを使ってよい」。上端が null なら候補の本数
      （絞らない）。下端は「1位だけ」になる値。範囲の中を動かす（何本 渡すかを探す）のは M2-F。
    ★数字を作らない＝範囲の外（lo < 1／lo > hi）は SampleError で止める（fail-closed）。
    ★上端が候補の本数を超える段は、候補の本数を使う（2026-10-01・B-1＝直す前は止めていた）。
    ★欄そのものが無ければ既定＝lo 1・hi null（設定ファイル `recipes/search_limits.json` の値と同じ）。
    """
    r = (limits or {}).get("stage_keep_range") or {}
    lo = r.get("lo", 1)
    hi = r.get("hi", None)
    lo = int(lo) if lo is not None else 1
    hi = int(n_cands) if hi is None else int(hi)
    if lo < 1:
        raise SampleError(f"stage_keep_range の下端が 1 未満: lo={lo}（fail-closed）")
    if hi > int(n_cands):
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001 の B-1）＝上端が候補の本数を超える段は、候補の本数の分だけ使う（止めない）。
        #   段2b の候補は1本なので、上端に10を書くと組む側がレンジの判定の束を1本も組めなかった（next_step §6 の224番）
        hi = int(n_cands)
    if lo > hi:
        raise SampleError(f"stage_keep_range が逆さま: lo={lo} > hi={hi}（fail-closed）")
    return hi


def _stage_pick(cands: list, keep: int, rank_pos: int, stage: str,
                extra: dict | None = None) -> tuple[dict, dict]:
    """段の候補の一覧（`build_stage_candidates` の戻り）から、順位 rank_pos（1始まり）の候補を取る。

    ★2026-09-13（98回目・監査 cp36 の C-1・C-2）＝2本目が1本目の一覧の上位を使うための入口。
    戻り＝(cond の深い写し, 記録)。記録の鍵＝rank・col・種類・時間足・label・horizon・分離力・候補の一覧・上位（＋extra）。
    ★順位が keep（その段で使ってよい本数）を超えたら SampleError＝その案は組めない（呼ぶ側は次の案へ進む）。
    ★材料の絞り（外す時間足・§2.2 の元データ・符号を取り去る前処理）は一覧を作る側に在る。
      ここでは写さない＝同じ判定を2か所に書かない（今回の C-1 は、絞りを1本目に足したとき2本目に足し忘れて起きた）。
    """
    r = int(rank_pos)
    if r < 1:
        raise SampleError(f"{stage} の順位が 1 未満: {r}")
    if r > int(keep):
        raise SampleError(f"{stage} の候補の上位 {int(keep)} 本の外（順位 {r}）")
    if r > len(cands):
        raise SampleError(f"{stage} の順位に {r} 位が無い（候補 {len(cands)} 本）")
    c = cands[r - 1]
    rec = {"rank": r, "col": c.get("col"), "種類": c.get("family"), "時間足": c.get("tf"),
           "label": c.get("label"), "horizon": c.get("horizon"), "分離力": c.get("acc"),
           "候補の一覧": stage, "上位": int(keep)}
    if extra:
        rec.update(extra)
    return json.loads(json.dumps(c["cond"])), rec


_STAGE_COUNT_MEMO: dict = {}


def stage_counts(laws: dict, table, tfs, limits) -> list:
    """段ごとの記録を作る（手順6・設計書 4-8 の鍵6つ・2026-09-11 新設）。

    戻り＝[{"stage":…, "n_candidates":…, "n_passed":…, "keep":…, "sec":…, "dropped":…}, …]

    ★`n_passed`（審査を通った本数）と `dropped`（落ちた法則ごとの本数）は **null と空** にする。
      理由＝法則の審査（G7）は**束に対して**掛かるもので、候補1件ごとには掛からない。
      **この工事では測っていない。**測っていないものを 0 と書くと「0本 落ちた」と読めるので、
      正直に null にする。**段ごとに測って落とすのは M2-F**（§2.2 の割り当て表）。
    ★`keep`＝その段で使ってよい候補の本数＝設定の欄 `stage_keep_range` から読む（`stage_keep_of`）。
      ★2026-09-13（98回目・監査 cp36 の C-2）＝直す前は 1 の直書きで、設定の欄を読んでいなかった。
    ★同じ法則・同じ成績表・同じ設定の欄なら本数は変わらないので、法則と欄の指紋で覚える（束1本ごとに
      数え直すと、100本 組む自己テストで5倍 遅くなる）。
    """
    # ★2026-09-16（監査 cp36 の M-1）＝覚える鍵に `drop_tfs` と `stage_limits` を足した。
    #   足さないと、設定の欄を書き替えても古い本数が返る（覚えたものをそのまま出すため）。
    _key = hashlib.sha256(
        json.dumps([laws, (limits or {}).get("stage_keep_range"),
                    (limits or {}).get("drop_tfs"), (limits or {}).get("stage_limits")],
                   sort_keys=True, default=str, ensure_ascii=False).encode("utf-8")
    ).hexdigest()[:16]
    if _key in _STAGE_COUNT_MEMO:
        return copy.deepcopy(_STAGE_COUNT_MEMO[_key])
    out = []
    for sk in ("stage1", "stage2a", "stage2b", "stage2c", "stage3"):
        t0 = time.perf_counter()
        row = {"stage": sk, "n_candidates": None, "n_passed": None,
               "keep": None, "sec": None, "dropped": {}}
        try:
            cands = build_stage_candidates(sk, laws, table, tfs, limits)
        except SampleError as e:
            row["止まった理由"] = str(e)[:120]     # ★黙って0件にしない（理由を残す）
            out.append(row)
            continue
        row["n_candidates"] = len(cands)
        row["keep"] = stage_keep_of(limits, len(cands))
        row["sec"] = round(time.perf_counter() - t0, 3)
        out.append(row)
    _STAGE_COUNT_MEMO[_key] = copy.deepcopy(out)
    return out


def sample_regime_build(limits, pool, tfs, table, name="range", order_n: int = 0,
                        pre_b: dict | None = None) -> tuple[dict, dict]:
    """場面の判定の束（meta.regime.build）を1つ 組む。戻り＝(build, 引いた記録)。いまはレンジだけ。

    ★指標と向きは乱数で引かない（2026-08-23 まこさん決定）＝order_n 番目の (B の順位, C の順位, G の順位, 向き) を
      `regime_draw_order` が決め、段ごとの候補の一覧（`build_stage_candidates`）のその順位の候補を使う。
    ★乱数は0件（2026-09-11 の手順9 で閾値の分位・本数・緩め幅も決まった並びにした・恒久の決まり67番）。
    ★2026-09-13（98回目・監査 cp36 の C-1・C-2）＝B・C・G を1本目の一覧から取る形にした（本文の注記）。

    ★pre_b（2026-09-05・M2-C-4・まこさん承認 iter="m2c4-add-parts-20260905"）＝
      条件B の材料に付ける前処理（例＝{"op": "ts_rank", "n": 20}＝直前の n本の中での順位）。
      **既定は None＝付けない。**＝この直しでは、いまの動きが1バーも変わらない（恒等3本の md5 で確かめる）。
      ★道を通しただけ。実際に付けるかどうかを相場の法則から決めるのは M2-E。
      ★乱数で「付ける／付けない」を選ばない（違反の記録 #14・#24＝くじ引きにしない）。
      ★水準（level）の形にだけ付く＝engine_tuner_exec.py の MATERIAL_PRE の逐語
        「ts_rank は 0〜1・ts_std はばらつきの幅で、元の列とは単位が違う…だから列2本の形には使わず、
         水準（level・band）で閾値と比べる形で使う」。条件B は form="level"。
    """
    if name != "range":
        raise SampleError(f"場面 {name} の束の組み方は未定義（レンジ以外は M2-6〜M2-8 で作る）")
    # ★M2-E-2（2026-09-10）＝相場の法則を **読んで** 組む。直す前は読めることを確かめるだけだった。
    laws = laws_for_scene(name)
    # ★2026-09-13（完成の条件 #4・まこさん決定「案1」「一本化する」）＝枠ごとに使う法則の番号と役割を、
    #   コードに書かず §2.2 の候補の元データから読む（段1＝帯と帯の幅・段2a＝強さの否定・
    #   段2b＝向きの否定・段2c＝3枠目・段3＝持続）。直す前はここに "R7"・"R1"・"R3"・"R5"・"R6"・
    #   "R4"・"R8" と役割の名前を直に書いていた（完成の条件 #4 の文＝組む関数に法則番号の直書きが0件）。
    s1, s2a, s2b, s2c, s3 = (stage_candidates(k) for k in ("stage1", "stage2a", "stage2b", "stage2c", "stage3"))
    draw: dict = {"order_n": int(order_n),
                  "法則から組んだ": {"形": sorted(laws["forms"]),
                                     "数える法則": [n for n, _s, _c in laws["counts"]],
                                     "重ねない法則": len(laws["no_dup"])}}
    # ★2026-09-11（手順10）＝3枠目 G の順位も受け取る（直す前は3つ＝B・C・向きだけ）
    r_b, r_c, r_g, side_b = regime_draw_order(order_n)
    # ★2026-09-13（98回目・監査 cp36 の C-1・C-2）＝B・C・G の材料は、段ごとの候補の一覧（1本目＝
    #   `build_stage_candidates`）の順位から取る（`_stage_pick`）。直す前は2本目が別の道（法則の系統／family で
    #   成績表の順位から引く）で材料を取っていて、1本目に在る3つの絞り（外す時間足・§2.2 の元データ・
    #   符号を取り去る前処理）が実際の束に掛かっていなかった（監査の実測＝200本中 帯の10分足 78本・abs 付き 0本）。
    #   ★時間足の直書き（5分足より後ろ全部）はここから消えた＝上位足と外す時間足の絞りは1本目に在る
    #     （法則 C4 を組む側に読ませるのは監査 cp36 の M-3＝別の工事）。
    #   ★上位を何本まで使うかは設定の欄 `stage_keep_range`（`stage_keep_of`）。
    c1 = build_stage_candidates("stage1", laws, table, tfs, limits)
    c2a = build_stage_candidates("stage2a", laws, table, tfs, limits)
    keep1 = stage_keep_of(limits, len(c1))
    keep2a = stage_keep_of(limits, len(c2a))
    # ── A 帯の幅（R7）＝法則が名指しした geo と family の一覧から、案の番号で決まる順位の1本 ──
    # ★2026-09-19（設計書 m2c-width-and-stage-candidates-20260918・まこさん承認）＝
    #   直す前は `_law_geo` の先頭（W%）を固定で使い、法則 R7 に戻した指標3件（BB幅・Donchian幅・
    #   HWC幅%）を1本も読まなかった（まこさん指摘 2026-09-18「帯の幅を見る指標はBB等、もっといっぱいある」）。
    #   直した後は `build_width_candidates` の一覧（レンジ幾何が先頭・指標は成績表の順位）から取る。
    #   ★順位は案の番号から決まる（`regime_draw_order` の r_b と同じ考え＝乱数を使わない）。
    cw = build_width_candidates(laws, table, tfs, limits)
    cond_a, draw["A"] = _stage_pick(cw, stage_keep_of(limits, len(cw)), r_b, "width",
                                    extra={"法則": s1["law_width"]})
    draw["A"]["側"] = cond_a["side"]
    # ── B 構造・位置（R1・R3）＝location の成績表の r_b 位・向きは order_n で決まる ──
    # ★2026-09-11（M2-E-3 の手順10・監査 cp35 の Critical C-1）＝帯の枠を法則から引く形にした。
    #   直す前＝`_ranked_material_at(rng, "location", r_b, tfs, table)`＝役割の名前をコードに直書き。
    #   監査が法則ファイルの写しを書き替えて試したら、**R1・R3 の系統を変えても帯が1文字も変わらなかった。**
    #   ★法則 R1・R3 が名指ししているのは family ではなく「系統」（構造・位置）。だから
    #     `_law_lineages` で系統を読み、`_material_for_lineage` でその系統の中から順位で引く。
    #   ★`tf_ok=upper`＝法則 R3 の「執行足より上」。直す前は帯に渡しておらず、1分足・3分足も引けた
    #     （監査の A1-d の2番）。
    lins_b = _law_lineages(laws, s1["law"]) or _law_lineages(laws, s1["law_or"])
    if not lins_b:
        raise SampleError(f"{s1['law']}・{s1['law_or']} が系統を名指ししていない（regime_laws.json・fail-closed）")
    # ★2026-09-13（98回目・監査 cp36 の C-1・C-2）＝帯の材料を、段1 の一覧の r_b 位から取る。
    cond_b, draw["B"] = _stage_pick(c1, keep1, r_b, "stage1", extra={"法則が名指しした系統": sorted(lins_b)})
    m_b = cond_b["material"][0]
    if pre_b is not None:                               # ★2026-09-05（M2-C-4）＝前処理の道（既定は通らない）
        m_b = {**m_b, "pre": dict(pre_b)}
        draw["B_pre"] = dict(pre_b)
    # ★向きは案の番号で決まる `side_b` のまま（直す前と同じ＝上側・下側の帯を交互に試す）。
    #   一覧の側（法則が側を決めない帯は above）に揃えると、下側の帯を試せなくなる。
    cond_b = {**cond_b, "material": [m_b], "side": side_b}
    # ── C 非トレンド（R5・R8）＝法則 R5 が名指しした family の中から、成績表の r_c 位 ──
    #    ★直す前＝env の全部から r_c 位を取っていた（法則が名指しした8種を見ていない）。
    fams_r5, side_r5 = _law_families(laws, s2a["law"])
    # ★2026-09-13（98回目・監査 cp36 の C-1・C-2）＝強さの否定を、段2a の一覧の r_c 位から取る。
    #   一覧の候補は、1本目が「法則が言う側の逆を not で包む」形にし、向きを持つ指標には符号を取り去る
    #   前処理（abs）を付けてある（§2.2 の元データの `pre`）。ここでは写さない。
    cond_c, draw["C"] = _stage_pick(c2a, keep2a, r_c, "stage2a",
                                    extra={"法則が名指しした family": sorted(fams_r5) if fams_r5
                                           else "（名指し無し＝役割の全部）"})
    strong = cond_c["not"]
    strong_side = strong["side"]
    want_side = side_r5.get(draw["C"]["種類"], "below")
    draw["C"]["法則の側"] = want_side
    draw["C"]["not で包む側"] = strong_side
    # ── G 低ボラ（R6）＝★M2-E-2 で新しく足した。§2.2 の段2c に当たる ──
    #    ★法則 R6 が名指しした family（BB幅・SQZ_ON・Donchian幅・ATR%・realized_vol・stdev%）から、
    #      成績表の順位の上から1本 取る。側も法則が family ごとに持つ（below／above）。
    #    ★役割は sufficiency（値動きの大きさ）＝型の表の系統「ボラ」がここに入る。
    cond_g = None
    fams_r6, _side_r6 = _law_families(laws, s2c["law"])
    if fams_r6:
        # ★2026-09-11（手順10・監査 cp35 の A1-d の3番）＝順位を 1 の直書きから案の番号へ。
        # ★2026-09-13（98回目・監査 cp36 の C-1・C-2）＝3枠目を、段2c の一覧の r_g 位から取る（側も一覧が法則から付けたもの）。
        c2c = build_stage_candidates("stage2c", laws, table, tfs, limits)
        cond_g, draw["G"] = _stage_pick(c2c, stage_keep_of(limits, len(c2c)), r_g, "stage2c",
                                        extra={"法則が名指しした family": sorted(fams_r6)})
        draw["G"]["法則"] = s2c["law"]
        draw["G"]["側"] = cond_g["side"]
    # ── F 何本 続いたか（R4）＝★M2-E-2 で新しく足した。直す前は無く、20回とも R4 で落ちていた ──
    #    ★M2-E-4d（束1・2026-09-25）＝内側を「成立の全体」にするため、D と G の後ろ（on_core を作った後）で組む。
    cond_f = None
    # ── E 状態を保つ（C6・C7）＝on＝持続 F の1つ（内側＝A∩B∩C∩(D)∩(G)・M2-E-4d）か、法則に R4 が無ければ A∩B∩C∩(D)∩(G)／off＝A・B・C をそれぞれ緩い側へずらした any ──
    off_c = json.loads(json.dumps(strong))
    # ★2026-10-01（B-2）＝not の中身の出る線は、強さが はっきり上がった所（above なら1つ大きい分位）。側は返さない（強さが戻ったら出る）。
    #   直す前は強さの側のまま緩めたので、出る線が入る側の内側（above q(X−1)）で真になった（監査 CP48 の別に見つけたこと）
    off_c["value"]["threshold_q"] = _loose_q_fixed(limits, strong["value"]["threshold_q"],
                                                "below" if strong_side == "above" else "above")
    # ── 段2b 向きの否定（R8・承認済みの借用）＝真偽の列を `not` で包んで1つ入れる（手順8） ──
    #   ★列の名前は §2.2 の元データから読む（`m2_stage_candidates.json` の `bool_col`）。
    #   ★`{"bool_col": …, "want": false}` と書かない＝`not` のノードが消えて、法則 R8 の
    #     「形を持つ＝not」の審査（G7）を通らなくなる（設計書 4-4 の手順5・実測）。
    #   ★自前の向きの判定は M2-M（まこさんが決めた順番を動かさない）。
    cond_d = None
    if "not" in laws["forms"]:
        _bc2b = s2b["bool_col"]
        if _bc2b:
            cond_d = {"not": {"bool_col": _bc2b, "want": True}}
    on_core = ([cond_a, cond_b, cond_c]
               + ([cond_d] if cond_d is not None else [])
               + ([cond_g] if cond_g is not None else []))
    # ★M2-E-4d（束1・2026-09-25）＝持続 F の内側＝成立の全体（A ∩ B ∩ C ∩ (D) ∩ (G)）。入る条件は F の1つ。
    #   直す前＝内側は帯 B の写し1つで、A・C・D・G と横並び（成立が途中で切れたバーも成立と数えた＝
    #   2026-09-20 の実測で真のバーの 9.65%〜18.55%）。§2.2 の段3 の正本＝「成立の連続本数」。
    #   ★「法則に streak が在れば持続を掛ける」の if の行は残す（壊すプログラム b77 がこの行を探す）。
    #   ★n は今までどおり承認済みの範囲（int_range）から案の番号で決まる並び（乱数を使わない・恒久67番）。
    if "streak" in laws["forms"]:
        cond_f = {"role": s3["role"], "form": "streak",
                  "value": _nv_fixed(limits, "int_range", "n", order_n),
                  "inner": {"all": json.loads(json.dumps(on_core))}}
        draw["F"] = {"形": "streak", "法則": s3["law"], "本数": cond_f["value"].get("n"),
                     "内側": "成立の全体（A・B・C・(D)・(G)）", "内側の本数": len(on_core)}
    on_all = [cond_f] if cond_f is not None else on_core
    if "hysteresis" not in laws["forms"]:
        raise SampleError("C6（hysteresis の形）が法則に無い（regime_laws.json・fail-closed）")
    if "not" not in laws["forms"]:
        raise SampleError(f"{s2b['law']}（not の形）が法則に無い（regime_laws.json・fail-closed）")
    hyst = {"form": "hysteresis",
            "on": {"all": on_all},
            "off": {"any": [_flip_loose(limits, cond_a), _flip_loose(limits, cond_b), off_c]},
            "value": _nv_fixed(limits, "state_hold_bars_range", "n", order_n)}
    build = {"entry": {"out_col": REGIME_OUT_COL[name], "tree": {"all": [hyst]}}, "block": None}
    # ★2026-09-16（監査 cp36 の M-3・完成の条件 AUDIT-4）＝束の単位で数える法則を、組んだ後に確かめる。
    #   なぜ組む前に確かめられないか＝C4 は「束の全部の部品のうち、執行足より上が何本 在るか」を
    #   数える法則（実行器の `_law_count` が束ぜんたいを数える）。枠を1つ選ぶ時点では決まらない。
    #   ★直す前＝ここで数えていなかったので、C4 の本数を書き替えても束が変わらず、
    #     後から審査（G7）が落としていた（監査 cp36 の M-3）。
    #   ★本数も「執行足より上」も、コードに書かない＝法則ファイルの「数える部品」から読む。
    _bad_c4 = _check_bundle_counts(laws, build, table)
    if _bad_c4:
        raise SampleError(f"束の単位で数える法則を満たさない: {_bad_c4}")
    if cond_d is not None:
        draw["D"] = {"形": "not", "法則": s2b["law"], "真偽の列": cond_d["not"]["bool_col"]}
    # ★段ごとの記録（手順6・設計書 4-8）＝候補が何本 在ったかを、引いた記録に足す。
    #   いまの鍵（order_n・法則から組んだ・A・B・C・G・F）は1つも消していない。
    draw["stages"] = stage_counts(laws, table, tfs, limits)
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
    _pa = _nv(rng, limits, "max_adds_range", "max_adds", as_int=True)   # 先に決める＝出口の枝が回数で切り替わるため
    pos_adds = int(_pa["max_adds"])
    rg = dict(regime if regime is not None else default_regime())
    meta_extra = {}
    if build_regime:
        # ★M2-5-1＝場面の判定の束を、案を作るプログラム自身が組んで meta.regime.build に入れる。
        #   既定 False＝従来どおり（案の中身も乱数の消費も変えない・ここは最後に引く）。
        bd, draw = sample_regime_build(limits, pool, tfs, table, name=str(rg.get("name") or "range"),
                                       order_n=int(regime_order_n))
        rg["build"] = bd
        meta_extra["regime_draw"] = draw             # 引いた記録（ラベル・先読み・K）＝人が追えるように残す
    recipe = {
        "meta": {"strategy": "e38", "logic_id": logic_id, "side": side,
                 "signal_family": fam_label,
                 "regime": rg, **meta_extra},
        "pre_filter": [],
        "entry": {"connective": tree},
        "exits": _make_exits(rng, limits, pool=pool, tfs=tfs, table=table, side=side,
                             max_adds=int(pos_adds)),
        "position": {"mode": str(rng.choice(["separate", "avg"])),
                     **_pa,
                     **({"add_trigger": {"kind": "resignal"}}
                        if True else {})},
    }
    # ★4要素ゲート（59回目・設計書 v2・まこさん承認 b1290f643e28…）＝S2＝案を返す直前の検査。
    #   まこさんの1行＝「指標、閾値、パラメータ、時間足の役割に基づき、法則に則って４つを
    #   組み合わせ、Entry/Exit やレジーム判定などの条件を作る」。
    #   ①値の出どころ（印の範囲の中か・範囲が正本と合うか・時間足・geo/時刻/状態）＝assert_provenance
    #   ②役割（入口・場面の判定＝型の表／出口＝枝の系統の欄）＝assert_roles・assert_exit_roles
    #   1つでも外れれば SampleError＝その案は作れない（fail-closed）。
    #   ★印は外さずに返す（C-7＝保存する案に出どころを残す）。実行器に渡す直前（run_trial）で外す。
    recipe["meta"]["exit_role_notes"] = _gate_recipe(recipe, where=f"案（logic_id={logic_id}）",
                                                     limits=limits, table=table)
    return recipe


def recipe_hash(recipe: dict) -> str:
    """案のハッシュ値＝印を外した形で計算する（印を付けてもハッシュ値は変わらない・C-7）。"""
    r = strip_marks(recipe)
    if isinstance(r, dict) and isinstance(r.get("meta"), dict):
        r["meta"] = {k: v for k, v in r["meta"].items() if k != "exit_role_notes"}
    return hashlib.sha256(json.dumps(r, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]


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
    used = Counter()                      # ★2026-09-06（監査 cp24 の §6-4）＝材料ごとに何回 使ったか
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
                    used[name] += 1
                elif "geo" in m:
                    touched.add(m["geo"])
                    used[str(m["geo"])] += 1
                # ★2026-09-06（監査 cp24 の §6-4・完成の条件④）＝別枠（需給・時間帯）も数える。
                #   直す前＝ここが指標とレンジ幾何しか集めていなかったので、
                #   「足した部品が案に実際に出てきたか」を数える道が無かった（監査の問いそのもの）。
                elif "demand" in m:
                    touched.add(str(m["demand"]))
                    used[str(m["demand"])] += 1
                elif "time" in m:
                    touched.add(str(m["time"]))
                    used[str(m["time"])] += 1
        modes[r["position"]["mode"]] += 1
        nexits[len(r["exits"])] += 1
    return {"構造数": len(recipes), "条件本数の分布": dict(sorted(counts.items())),
            "形の分布": dict(forms.most_common()), "役割の分布": dict(roles.most_common()),
            "経路数の分布": dict(sorted(paths.items())), "玉の持ち方": dict(modes),
            "出口の枝数": dict(sorted(nexits.items())),
            "触れた列": len(touched),
            # ★2026-09-06（監査 cp24 の §6-4・完成の条件④）＝使った材料の名前と回数を出す。
            #   これが無いと「足した部品が案に実際に出てきたか」を機械で数えられない。
            "使った材料と回数": dict(used.most_common()),
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
      内側が条件の束（判定の束の中の streak・M2-E-4d）のときも、`_cond_keys` がこの関数で束の中の条件を集めてから降りる。
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


def _regime_on_conds(build: dict) -> list:
    """判定の束から「成立の条件の並び」（A・B・C・(D)・(G)）を返す（M2-E-4d・束1・2026-09-25 新設）。

    ★束の形の読み方を、この1か所にまとめる（恒久の決まり69番）。直す前は T24③・T42・gate_matrix・診断が
      それぞれ入る条件を並びの位置で読んでいて、形を変えるたびに全部 直すことになった。
    ・入る条件が持続1つで内側が束（新しい形）＝その内側の並びを返す。
    ・それ以外（直す前の形＝枠が横並び・持続は内側が条件1つ）＝入る条件の並びから持続を除いたものを返す。
    ★hysteresis が無い木（法則に C6 が無いとき）は、木の all の並びを同じ規則で読む。
    ★返す条件は束の中の同じ辞書（写しではない）＝gate_matrix が壊す相手をそのまま書き替えられる。
    """
    tree = ((build.get("entry") or {}).get("tree") or {})
    top = list(tree.get("all") or [])
    hy = top[0] if top and isinstance(top[0], dict) and top[0].get("form") == "hysteresis" else None
    on = list(((hy or {}).get("on") or {}).get("all") or []) if hy is not None else top
    if (len(on) == 1 and isinstance(on[0], dict) and on[0].get("form") == "streak"
            and isinstance(on[0].get("inner"), dict) and not ex._is_cond(on[0]["inner"])):
        return list(on[0]["inner"].get("all") or [])
    return [c for c in on if not (isinstance(c, dict) and c.get("form") == "streak")]


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
            # ★M2-E-4d（束1・2026-09-25）＝内側が条件の束（判定の束の中の streak＝成立の全体）なら、
            #   束の中の条件を `_tree_conds` で集めてから降りる。直す前は内側を条件1つとして降りていた
            #   （束だと form の鍵が無くて落ちる＝分位の解決表に鍵が入らない）。
            if ex._is_cond(c["inner"]):
                _cond_keys(c["inner"], lane)
            else:
                for cc in _tree_conds(c["inner"]):
                    _cond_keys(cc, lane)
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
    """レンジ幾何＝帯の4隅・中央と、そこから作る3列（帯内位置%・W%・下半分位置）。本走と番人で同じ作り方を使う。"""
    geo = {"res_hi": df["v11_res_hi"].to_numpy(float), "res_lo": df["v11_res_lo"].to_numpy(float),
           "sup_hi": df["v11_sup_hi"].to_numpy(float), "sup_lo": df["v11_sup_lo"].to_numpy(float),
           "mid": df["v11_mid"].to_numpy(float)}
    c = df["close"].to_numpy(float)
    span = geo["res_hi"] - geo["mid"]
    with np.errstate(invalid="ignore", divide="ignore"):
        geo["帯内位置%"] = np.where(np.isfinite(span) & (span > 0), (c - geo["mid"]) / span, np.nan)
        geo["W%"] = np.where(np.isfinite(geo["res_hi"]) & np.isfinite(geo["sup_lo"]),
                             (geo["res_hi"] - geo["sup_lo"]) / c * 100.0, np.nan)
        # ★2026-10-09（工事 m2c15-shape-structure-20261009・監査 CP60 の修正65）＝下半分の位置（観察の道具 build_range_geometry と同じ式）
        dn = geo["mid"] - geo["sup_lo"]
        geo["下半分位置"] = np.where(np.isfinite(dn) & (dn > 0), (c - geo["mid"]) / dn, np.nan)
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
        # ★2026-09-11（M2-E-3 の手順2・設計書の完成の条件 条件7）＝分位を1回でまとめて計算する。
        #   直す前＝`np.quantile` を分位の数だけ呼んでいた（格子が81段なら81回）。
        #   `np.quantile` は呼ばれるたびに列を並べ替え直すので、81回 呼ぶと81回 並べ替える。
        #   実測＝1つの鍵につき 0.108秒 → 0.0045秒（24分の1・`gen_s22_fidelity.py --keytime 20`）。
        #   ★値は1つも変わらない＝同じ関数・同じ既定の補間（linear）を、確率の一覧で1回 呼ぶだけ。
        #     それでも念のため、自己テスト T34 が「1段ずつ計算した結果と 1e-12 まで一致するか」を測る。
        _ps = [int(q.lstrip("q")) / 100.0 for q in grid]
        table[key] = {q: float(v) for q, v in zip(grid, np.quantile(s, _ps))}
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
    need_demand: set[str] = set()                # ★2026-09-05（M2-C-4）＝需給の列（別枠）
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
                    # ★2026-09-05（M2-C-4）＝需給の列（別枠）は、時間足の展開をせずに
                    #   observe_diag.load_demand が作った列をそのまま載せる（式を2か所に持たない）。
                    if "demand" in m:
                        _kind, _name = ex._material_name(m, lane)
                        if _name not in df.columns:
                            need_demand.add(_name)
                        continue
                    if "family" in m and "legacy_col" not in m:
                        kind, name = ex._material_name(m, lane)
                        if kind == "col" and name not in df.columns:
                            alias = ex.RUNTIME_ALIAS.get(name)
                            if alias is None or alias not in df.columns:
                                need.add(name)
    if need_demand:
        import contextlib as _cl
        import io as _io
        import observe_diag as _od
        _buf = _io.StringIO()
        with _cl.redirect_stdout(_buf):
            _dem, _cov = _od.load_demand(pd.to_datetime(df["ts"]))
        df = df.copy()
        for _c in sorted(need_demand):
            if _c not in _dem.columns:
                raise SystemExit(f"[材料エラー] 需給の列を作れなかった: {_c}（被覆＝{_cov}）")
            df[_c] = _dem[_c].to_numpy(float)
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


# ══ 減らしたい損失（要件 R8・まこさん確定 2026-07-27・実装 2026-08-26）═══════════════════
#   まこさんの逐語＝「損失最小化というのは、例えばTIMEExitの損失が大きい場合に、その損失額を
#   最小化させるために、指標、閾値、時間足、パラメータ等を調整して損失を最小限にするために
#   調整するという意味」。★何を減らすかは診断の結果で毎回変わるので、コードに焼かず実行時に渡す。
#   ★動かす値は入口も出口も両方（まこさん承認 2026-08-26・逐語「それでOK」）＝目的の値だけを
#     差し替える。探せる範囲（材料・閾値・時間足・パラメータ）には1バイトも触らない。
#   ★式は engine_tuner.py（数字を調整する方）491-495行の写し。net の計算は審判がする（H13）。
def assert_known_exit_reason(name: str | None) -> None:
    """審判が知らない決済の理由なら、走らせる前に止める（fail-closed）。

    ★なぜ要るか＝名前を打ち間違えても、どの玉にも当たらないので損の額が常に 0.0 になり、
      全部の案が同点に見える。走り切ってから気づくのでは遅い。
    一覧の出どころ＝score.py の KNOWN_EXIT_REASONS（手書きの一覧を作らない）。
    """
    if not name:
        return
    import score as _sc
    known = set(_sc.KNOWN_EXIT_REASONS)
    if name not in known:
        raise SystemExit(f"[R8 エラー] 決済した理由 '{name}' を審判が知らない"
                         f"（使えるのは {len(known)} 種）＝{sorted(known)}")


def _focus_net(t, judge, minimize: str | None) -> tuple:
    """指定した決済の理由の玉だけを審判に通した net 合計と、その玉数を返す。

    戻り＝(損の額, 玉数)。マイナスなら損＝大きくするほど損が減る。
    ★この関数は net を1行も計算しない＝judge.score() を呼ぶだけ（H13）。
    """
    if not minimize or t is None or not len(t) or "exit_reason" not in t.columns:
        return 0.0, 0
    sub = t[t["exit_reason"] == minimize].reset_index(drop=True)
    if not len(sub):
        return 0.0, 0
    return float(judge.score(sub)["total"]), len(sub)


def _obj_key(rec: dict, minimize: str | None) -> float:
    """並べ替えと選択に使う値＝指定があれば その決済の理由の損の額、無ければ合計 net。"""
    return float(rec.get("focus", 0.0)) if minimize else float(rec.get("total", 0.0))


# ══ 試行の実行（1本＝実行器で売買 → 審判で net）══════════════════════════════════════════
def run_trial(df: pd.DataFrame, recipe: dict, qtable: dict, judge, start, end,
              minimize: str | None = None) -> dict:
    recipe = strip_marks(recipe)                      # ★実行器に渡す直前で印を外す（C-7）
    if isinstance(recipe, dict) and isinstance(recipe.get("meta"), dict):
        recipe["meta"].pop("exit_role_notes", None)
    trades, rep = ex.run_recipe(df, recipe, qtable=qtable)
    t = pd.DataFrame(trades)
    if len(t):
        et = pd.to_datetime(t["entry_time"])
        t = t[(et >= start) & (et < end)].reset_index(drop=True)
    days = max((end - start).days, 1)
    if not len(t):
        return {"total": 0.0, "n": 0, "per_day": 0.0, "t": t, "rep": rep,
                "focus": 0.0, "focus_n": 0}
    res = judge.score(t)
    focus, focus_n = _focus_net(t, judge, minimize)
    return {"total": float(res["total"]), "n": len(t), "per_day": len(t) / days, "t": t, "rep": rep,
            "focus": focus, "focus_n": focus_n}


def run_trial_guarded(df: pd.DataFrame, recipe: dict, qtable: dict, judge, start, end,
                      minimize: str | None = None):
    """案1本を走らせる。★その1本が拒否されても、走行を丸ごと止めない（まこさん指示 2026-08-16）。

    戻り値＝(結果, 拒否の理由)。走れたら (結果, None)、拒否されたら (None, 理由の文字列)。

    何を守るか＝探索の走行が、1本の案のせいで丸ごと死なないこと。
    2026-08-16 に実際に起きました＝分位の解決表に鍵の無い案が1本 混ざると、`--selftest` が
    8回中4回 丸ごと止まりました（`session_worklog_20260816.md` の §4）。

    ★握りつぶすのは「レシピの拒否」（RecipeError・4要素ゲートの SampleError）だけです。それ以外の例外は、
    そのまま上へ投げます＝本当の不具合を「1本 落としました」で隠さないためです。
    ★落とした件数と理由は、呼ぶ側が必ず画面に出します（黙って消さない）。
    ★落とした案を「net $0 の案」として数に入れません＝嘘の数字を作らないためです。
    ★59回目（設計書 やること8）＝走らせる入口でも4要素ゲート（値の出どころ・役割）を掛ける。
      案を作る関数を通さずに渡された案も、ここで止まる。例外は恒等レシピ（recipes/identity_*.json と
      ハッシュ値が一致するもの）だけ＝レーンの名前では例外にしない。
    """
    try:
        if isinstance(recipe, dict) and recipe and not _is_identity_recipe(recipe):
            _gate_recipe(recipe, where="走らせる入口")
        return run_trial(df, recipe, qtable, judge, start, end, minimize), None
    except (ex.RecipeError, SampleError) as e:
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
# ★59回目＝点の一覧から選ぶ値（メニュー方式・旧 _cat）は消した（設計書 やること3・監査 C-2）。
#   未使用のまま残しておくと1行で点の一覧に戻せる（監査 観点①）。値の作り方は範囲方式だけ。


def _int_range(lo: int, hi: int, step: int = 1, name: str = "__int__") -> dict:
    """下限から上限までの整数から選ぶ値（範囲方式・監査 4-19／要件 R6 で新設）。

    ★60回目（2026-08-25）＝`name`（この範囲の出どころ＝設定ファイルの鍵の名前）を持たせた。
      直す前は apply_slots が印の名前をパスから当てていて、**ずらす本数（offset）の印に
      `__int__`（ふつうの整数の範囲）を書いていた。**正本は `nest_offset_range` なので、
      印の範囲が正本の外と判定され、**第2段（TPE）の試行が全部 4要素ゲートで落ちていた**
      （実測 2026-08-25＝ミニ走行で 6/6 本・理由「offset の印の範囲 0.0〜1.0 が正本（__int__）3.0〜12.0 の外」）。
    """
    return {"kind": "int", "lo": int(lo), "hi": int(hi), "step": int(step), "name": str(name)}


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
    # ★59回目＝メニュー方式（候補の一覧から選ぶ）は無い＝来たら止める（fail-closed・監査 C-2）
    raise SystemExit(f"[歩4 エラー] 値スロット {name} の作り方 {spec.get('kind')!r} は範囲方式でない（点の一覧は使えない）")


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
                slots.append((f"{prefix}.value.offset",
                              _int_range(int(_or["lo"]), int(_or["hi"]), name="nest_offset_range")))
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
                    slots.append((f"exits[{bi}].fire[{ci}].value.n",
                                  _int_range(_lo * 5, _hi * 5, 5, name="hold_bars")))
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


def apply_slots(recipe: dict, choices: dict[str, object], specs: dict | None = None) -> dict:
    """スロットのパスに選んだ値を書き込んだレシピの複製を返す（構造は動かさない）。

    ★59回目（設計書 やること3・監査 B4）＝値を書き込むとき、その値スロットの範囲（specs＝value_slots の
      作り方）を印として一緒に書く。書き込んだ案は run_trial_guarded の入口で assert_provenance を通る
      ＝第2段で詰めた値も「範囲の中か・範囲が正本と合うか」を検査される。
    """
    r = copy.deepcopy(recipe)
    for path, val in choices.items():
        holder, key = _slot_ref(r, path)
        holder[key] = val
        sp = (specs or {}).get(path)
        if not isinstance(sp, dict):
            continue
        if key == "threshold_q" and sp.get("kind") == "q":
            holder[Q_SRC] = {"kind": "q", "lo": int(sp["lo"]), "hi": int(sp["hi"]), "slot": path}
        elif sp.get("kind") == "int":
            # ★60回目（2026-08-25）＝印の名前は、その値スロット自身が持つ出どころ（name）から取る。
            #   直す前はパスから当てていて、ずらす本数（offset）に `__int__` を書いていた
            #   ＝正本（nest_offset_range）と食い違い、第2段の試行が全部 落ちていた（実測 6/6 本）。
            nm = str(sp.get("name") or ("hold_bars" if path.endswith(".value.n")
                                        and path.startswith("exits[") else "__int__"))
            lo, hi = int(sp["lo"]), int(sp["hi"])
            raw = int(val)
            mk = {"kind": "int", "name": nm, "lo": lo, "hi": hi, "raw": raw, "slot": path}
            if nm == "hold_bars":                         # 分＝本数×5（value_slots が 5倍で作る）
                mk = {"kind": "linear", "name": nm, "lo": lo // 5, "hi": hi // 5, "raw": raw / 5.0,
                      "scale": 5.0, "slot": path}
            marks = dict(holder.get(NUM_SRC) or {})
            marks[key] = mk
            holder[NUM_SRC] = marks
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
                   minimize: str | None = None,
                   purpose: str, tag: str = "",
                   df_confirm: pd.DataFrame | None = None, confirm_start=None, confirm_end=None,
                   base=None, rules: dict | None = None, rfloor: float | None = None,
                   build_regime: bool = False) -> dict:
    """第1段＝構造をランダムに撒く（統計の土台）→ BH 法 → 第2段＝有望構造の値を TPE で詰める。"""
    global _GATE_LIMITS
    _GATE_LIMITS = limits                      # ★走らせる入口の4要素ゲートが使う（保有時間の範囲は解決済み）
    meta = {"seed": seed, "trials1": trials1, "trials2": trials2, "top_k": top_k,
            "window": [str(start), str(end)], "side": side,
            "limits_hash": hashlib.sha256(json.dumps(limits, sort_keys=True, default=str).encode()).hexdigest()[:12],
            "tag": tag}
    # ★減らしたい損失（R8）＝指定したときだけ meta に足す。指定なしのときの meta は直す前と同じ
    #   ＝前に作った journal がそのまま再利用できる（恒等を壊さない）。指定の有無や中身が変われば
    #   meta が食い違って Journal が止める＝目的が入れ替わったまま再開する事故を防ぐ（2026-08-26）。
    if minimize:
        meta["minimize"] = minimize
    # ★指標のオン・オフの印（M2-C-2・呼ぶ側 5/5＝走行を再開する）。
    #   印が前回と違う状態で続きから再開すると、前半と後半で使える指標が変わった1本の走行になる＝
    #   試行の母集団が途中で入れ替わり、DSR・PBO の判定が意味を失う。だから meta に入れて食い違いで止める。
    meta["indicator_switch"] = ex.indicator_switch_fingerprint()
    jn = Journal(run_dir / "journal.jsonl", meta)
    print(f"[歩4 生成器] 窓 {start}〜{end} ／ 第1段 {trials1} 本（ランダム＝統計の土台）／ "
          f"第2段 {trials2} 本（TPE＝統計判定に不使用）／ journal {jn.path}")
    # ★何を目標にして探すかを、走り始めに必ず出す（R8・まこさん確定 2026-07-27）
    if minimize:
        print(f"[目的] {minimize} の損失を最小化する"
              f"（審判に {minimize} の玉だけを通した net 合計を最大化＝マイナスを 0 に近づける）")
        if net_floor is None:
            print("[net の歯止め] なし（--net-floor 未指定）。"
                  "⚠️ 損失だけを見ると、ほとんど建てない形が上位に来ます")
        else:
            print(f"[net の歯止め] 値決め窓の合計 net < ${net_floor:,.0f} の試行は捨てる")
    else:
        print("[目的] 合計 net を最大化する"
              "（--minimize を指定すると、特定の決済した理由の損失を減らす形になる）")

    # ── 構造の撒き（決定論＝seed と番号だけから再現できる＝R12 の前提）──
    vlim = {"n_min": None,          # G2 は検査5 の補正後表と接続（本走時・samples 引数）＝ここでは構造検査
            "p_max": limits.get("p_max"), "count_range": limits.get("count_range"),
            "role_max": limits.get("role_max"), "depth_max": limits.get("depth_max"),
            "k_max": limits.get("k_max"), "r_min": limits.get("r_min")}
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
            ex.validate_recipe(strip_marks(r), limits=vlim)     # ★S3＝案1本ずつの検査（印は外して渡す）
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
    bd = structure_breakdown([strip_marks(s) for s in structures], catalog_total)
    print(f"[構造の内訳（機械出力・R3 完了の線⑤）] {json.dumps(bd, ensure_ascii=False)}")
    print(f"[生成拒否の理由別件数] {json.dumps(dict(rejects), ensure_ascii=False)} ／ 重複（正規形で同一） {dup} 本")

    # ── D11＝案そのものを記録に残す ＋ G2＝生成のたびの照合（D1・2026-08-07）──
    #   適合率が100%未満、または表が未承認なら、check_structures が SystemExit(1)＝試行を1本も走らせない。
    #   ★59回目（C-7）＝structures.json は従来どおり印を外した形（型の表との照合はこれを読む）。
    #     印つきの案は structures_marked.json に残す＝走行の後で --verify-provenance が出どころを再判定する。
    spath = run_dir / "structures.json"
    spath.write_text(json.dumps({"structures": [strip_marks(s) for s in structures]},
                                ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    (run_dir / "structures_marked.json").write_text(
        json.dumps({"structures": structures}, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    _notes = sorted({n for s in structures for n in ((s.get("meta") or {}).get("exit_role_notes") or [])})
    print(f"[D11] 案そのもの {len(structures)} 本を {spath} に記録（journal の idx と1対1）"
          f"／印つき＝{run_dir / 'structures_marked.json'}")
    if _notes:
        # ★60回目（2026-08-25）＝ここは本来 0 種（表に系統の欄が無い枝は組み立てない＝S2 で止まる）。
        #   出たときは、印の付かない道が残っているという合図＝見張りとして残す。
        print(f"★[4要素ゲート] 出口の役割の未判定が {len(_notes)} 種 出た（本来 0 種）: {_notes[:6]}")
    import gen_signal_families as gsf
    gsf.check_structures(str(spath))

    # ── 材料と解決表（探索開始時に1回固定・§5-4）──
    # ★2026-08-13（段A の A-2b）＝ここで列を先に全部 作るのをやめた。
    #   材料は、条件が要求した組だけを その場で計算する（`ex.material_array`・同じ組は使い回す）。
    #   完了の条件②＝本走で `attach_materials` の呼び出し回数が 0 であること（下の行で機械が出す）。
    # ★2026-09-06（監査 cp24 の §6-2・設計書 B）＝需給の列（別枠）だけは、その場で作れないので
    #   走らせる前に載せる（元データが別ファイルで、時間足に展開しないため）。
    # ★2026-09-07（next_step §6 の139番・設計書の やること D）＝載せる処理そのものは実行器へ移した。
    #   ここで呼ぶことは残す＝下の分位の解決表（build_qtable）は、候補になりうる需給の列を
    #   全部 見て作るため（案が使う分だけでは足りない）。だから型の表の demand_ok を全部 渡す。
    df2 = ex.attach_demand_columns(df, load_signal_table().get("demand_ok") or [])
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
        res, why_reject = run_trial_guarded(df2, r, qtable, judge, start, end, minimize)
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
        if minimize:                      # ★指定したときだけ足す＝指定なしの記録は直す前と同じ形（恒等）
            rec["focus"] = res["focus"]           # その決済した理由の玉だけの net 合計（R8）
            rec["focus_n"] = res["focus_n"]       # その玉数
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
    # ★R8＝損の額と合計 net の両方を並べて出す（片方だけだと、損を減らすつもりで勝ち玉まで
    #   削った形が上位に来ても気づけない）。指定が無いときは1行も増やさない（恒等）。
    if minimize and kept:
        print(f"  [{minimize} の損失が小さい順・上位3]")
        for r in sorted(kept, key=lambda z: -_obj_key(z, minimize))[:3]:
            print(f"    #{r['idx']}: {minimize} ${r.get('focus', 0.0):+,.0f}"
                  f"（{r.get('focus_n', 0)}玉） / 合計 net ${r['total']:+,.0f}"
                  f" / {r['n']}玉 / {r['per_day']:.2f}件/日")
    # ★名前は審判の一覧に在っても、この戦略の売買記録には1本も出ないことがある（例＝その枝を持たない）。
    #   そのときは損の額が全部 $0 になり、案の優劣が付かない＝黙って進めず警告を出す（R8）。
    if minimize and not any(r.get("focus_n", 0) for r in results1):
        print(f"  ⚠️ [警告] 指定した決済した理由 {minimize} は、どの試行の売買記録にも1本も出ていない"
              "＝損の額が全部 $0 で、案の優劣が付いていません")
    write_kakikudashi(run_dir, [strip_marks(s) for s in structures], results1, kept, seed)   # D1 完了の線①＋監査 G4の材料

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
    top = sorted(top_pool, key=lambda z: -_obj_key(z, minimize))[:top_k]   # ★R8＝指定時は損の額の順
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
                # ★"total" の欄には「目的の値」が入る＝指定が無ければ合計 net、在れば損の額（R8）
                stage2_best.append({"idx": r1["idx"], "total": _obj_key(r1, minimize), "params": {}})
                continue
            def obj(trial, recipe=recipe, slots=slots, sidx=r1["idx"]):
                choices = {p: suggest_slot(trial, p.replace(".", "_"), sp) for p, sp in slots}
                key = f"s2/{sidx}/{trial.number}/" + hashlib.sha256(
                    json.dumps(choices, sort_keys=True, default=str).encode()).hexdigest()[:12]
                got = jn.get(key)
                if got is not None:
                    # ★R8＝再開のときも、指定が在れば損の額を返す。指定の有無が変わると meta が
                    #   食い違って Journal が止まるので、ここで目的が入れ替わることはない
                    return (_obj_key(got, minimize)) if got["ok"] else -1e9
                r2 = apply_slots(recipe, choices, dict(slots))       # ★印つきで書き込む（C-2）
                try:
                    ex.validate_recipe(strip_marks(r2), limits=vlim)   # ★S3 を第2段でも掛け直す（C-2・B4）
                    res, why_reject = run_trial_guarded(df2, r2, qtable, judge, start, end, minimize)
                except ex.RecipeError as _e2:
                    res, why_reject = None, str(_e2)
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
                rec2 = {"stage": 2, "idx": sidx, "trial": trial.number, "total": res["total"],
                        "n": res["n"], "per_day": round(res["per_day"], 4), "ok": ok, "why": why}
                if minimize:              # ★指定時だけ足す＝指定なしの記録は直す前と同じ形（恒等）
                    rec2["focus"] = res["focus"]
                    rec2["focus_n"] = res["focus_n"]
                jn.put(key, rec2)
                return _obj_key(res, minimize) if ok else -1e9
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
        _lab = f"{minimize} の損失" if minimize else "合計 net"      # ★何の値を並べているかを明示（R8）
        for b in stage2_best:
            print(f"  構造 #{b['idx']}（{_lab}）: 第1段 "
                  f"${next(_obj_key(z, minimize) for z in top if z['idx']==b['idx']):+,.0f}"
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
        best_rec = max(kept, key=lambda z: _obj_key(z, minimize))     # ★R8＝指定時は損の額で選ぶ
        best_struct = structures[best_rec["idx"]]
        # 値決め窓でもう1回だけ走らせる＝journal は売買記録を残していないため（1試行ぶんの費用）
        rs_j = run_trial(df2, best_struct, qtable, judge, start, end, minimize)
        df2c = df_confirm            # ★A-2b＝列は その場で作る（先に全部 作らない）
        rc_j = run_trial(df2c, best_struct, qtable, judge, confirm_start, confirm_end, minimize)
        _fx = (f" ／ {minimize} ${rc_j['focus']:+,.0f}（{rc_j['focus_n']}玉）") if minimize else ""
        print(f"\n[確認窓の1走] 構造 #{best_rec['idx']}（値決め窓で最良）を確認窓で1回だけ走らせた"
              f"＝net ${rc_j['total']:+,.0f}{_fx} ／ {rc_j['n']}玉 ／ {rc_j['per_day']:.2f}件/日"
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
                _rn = apply_slots(best_struct, {_p["name"]: _p["value"]}, dict(_slots))   # ★印つき（C-2）
                try:
                    ex.validate_recipe(strip_marks(_rn), limits=vlim)
                    _r, _why = run_trial_guarded(df2, _rn, qtable, judge, start, end)
                except ex.RecipeError as _e3:
                    _r, _why = None, str(_e3)
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
        # ★2026-09-06（監査 cp24 の §6-2・設計書 B）＝需給の列（別枠）。
        #   なぜ要るか＝この直しで、案に需給の条件が入るようになった。合成データにこの列が無いと、
        #   番人が「材料の名前に時間足が無い: L-S比」で落ちる（2026-09-06 に実測）。
        #   ★これは合成の値です（実データではありません）。ほかの合成の列（帯の4隅・stoch_k）と同じ扱い。
        #   ★名前は型の表の extra_parts.demand.parts の3件と同じ（表が正本）。
        "taker_ls": 1.0 + 0.3 * np.sin(np.arange(n) / 11.0),
        "L-S比": 1.0 + 0.2 * np.cos(np.arange(n) / 13.0),
        "CVD": np.cumsum(rng.normal(0, 1.0, n)),
    })


def _selftest_extra_gate() -> list:
    """別枠3種（レンジ幾何・需給・時間帯）の審査が、オン・オフの印を見ているか。

    ★2026-09-07（next_step §6 の149番・設計書 iter="approval-audit-plumbing-20260907"）に
      `_check_extra_gate` から改名した。**中身は1行も変えていない。**
      なぜ＝静的検査（lint_provenance の⑤）は「見本の関数（_thr_fixture ほか）は、
      名前に selftest が入った関数の中でだけ呼んでよい」という決まりを見る。
      直す前の名前には selftest が入っていなかったので、この関数の中の `_thr_fixture("q70")`
      が「自己テストの外で見本を使った」と数えられ、静的検査が 1件 の赤のままだった
      （実測＝`python3 .claude/audits/m2d_lint_check.py` の逐語「見本の関数: 1 件 行=[3815]」）。
      ★検査を緩めていない＝この関数は selftest からしか呼ばれない自己テストの本体なので、
      名前を実体に合わせただけ。

    ★2026-09-07（監査 cp25 の §5-2・Major・設計書 C）に足した。
      直す前＝テストの枝は7つで、**7つとも指標（family）を試していた**。
      2026-09-06 に新しく作った審査の枝3本（assert_provenance の中のレンジ幾何・需給・
      時間帯）を試す枝が **0件** だった＝明日その3枝が消えても、誰も気づかない。
    ★壊すプログラム b33 では代わりにならない（監査 cp25 の §5-2 の実測）＝b33 が測るのは
      候補の側（--count-extra-candidates）だけで、審査の3枝を消しても同じ結果を返す。
    ★形は T33-b・T33-c と同じ＝①オンなら通す ②オフなら止める ③戻せば通る。

    ★なぜ selftest の中から切り出したか（2026-09-07・実測）
      `--selftest` の全体は **6分23秒（383秒）** かかる。承認のときに機械が壊すプログラムを
      走らせる打ち切りは **120秒**（run_breaks.py の TIMEOUT_SEC）。
      2026-09-07 の承認で、実際に b35 が打ち切られた。打ち切りは強制終了なので
      **壊した行を元に戻す処理が走らず、審査の需給の枝が消えたまま残った**
      （記録の逐語＝「時間切れ（120秒）: b35_gate_branch_gone.sh」）。
      だから、この枝だけを数秒で走らせる口 `--selftest-extra-gate` を作り、
      selftest と その口が **この1本の関数を呼ぶ**（同じ判定を2か所に書き写さない）。

    戻り＝ダメだった説明の一覧（空なら3種とも期待どおり）。
    """
    out: list = []
    sw = ex.load_indicator_switch()
    tbl = load_signal_table()
    for kind, key, parts in (
            ("geo", "_geo_set", tbl.get("geo_ok") or []),
            ("demand", "_demand_set", tbl.get("demand_ok") or []),
            ("time", "_time_set", tbl.get("time_ok") or [])):
        if not parts:
            out.append(f"型の表に {kind} の部品が1件も無い（この枝が何も試せない）")
            continue
        part = str(parts[0])
        cand = {"role": "sufficiency", "form": "level", "side": "above",
                "material": [{kind: part}], "value": _thr_fixture("q70")}
        keep = set(sw[key])
        try:
            sw[key] = set(keep) | {part}                      # ①オンなら通す
            try:
                assert_provenance(cand, where="T33-g")
            except SampleError as e1:
                if "印が「使わない」" in str(e1):
                    out.append(f"{kind} の {part} がオンなのに印で止まった")
            sw[key] = set()                                   # ②オフなら止める
            try:
                assert_provenance(cand, where="T33-g")
                out.append(f"{kind} の {part} がオフなのに審査が通した")
            except SampleError as e2:
                if "印が「使わない」" not in str(e2):
                    out.append(f"{kind} が止まったが理由が印ではない: {str(e2)[:60]}")
            sw[key] = set(keep) | {part}                      # ③戻せば通る（片道でない）
            try:
                assert_provenance(cand, where="T33-g")
            except SampleError as e3:
                if "印が「使わない」" in str(e3):
                    out.append(f"{kind} を戻しても印で止まる（片道になっている）")
        finally:
            sw[key] = keep
    return out


def selftest_rank_demand() -> list:
    """T23-demand＝需給の列を、順位を読む側が落とさずに読めるか（設計書 iter="demand-in-ranking-20260907" の F・数秒）。

    ①`ranked_materials("sufficiency")` に需給3列が出る ②`demand_on` から1件 外すと、その列だけ消える ③戻すと出る
    ④`_family_tf_from_col("CVD__5m")` が `("CVD", "5m")` を返す ⑤`ranked_groups("sufficiency")` に需給の組が出て、
      `ranked_groups("location")`・`ranked_groups("env")` には1つも出ない。
    ★成績表は本物を使わず、小さな成績表を一時的に差し込む（本物の順位に依らず、毎回 同じ結果になる）。
    ★口 `--selftest-rank-demand` と `selftest()` の末尾が、この1本を呼ぶ（判定を2か所に書き写さない）。
    ★壊すプログラム b38（`ranked_materials` の需給の枝を消す）が、この口を測る。
    戻り＝ダメだった説明の一覧（空なら全部 期待どおり）。
    """
    global _MATERIAL_RANKING
    out: list = []
    names = sorted(iref.DEMAND_REF)
    dem_cols = [f"{n}__5m" for n in names]
    ind_rows = [["RSI14__5m", 0.61], ["ADX14__1h", 0.42]]
    dem_rows = [[f"{n}__5m", a] for n, a in zip(names, (0.48, 0.53, 0.47))]
    roles = list(load_signal_table()["roles"])
    fake = {"順位": {ro: {la: {hz: (ind_rows + (dem_rows if ro == "sufficiency" else []))
                                for hz in ("24", "288")} for la in ("強さ", "向き", "大きさ")} for ro in roles}}
    keep_rank, keep_memo = _MATERIAL_RANKING, dict(_RANKED_GROUPS_MEMO)
    sw = ex.load_indicator_switch()
    keep_dem = set(sw["_demand_set"])
    try:
        _MATERIAL_RANKING = fake
        _RANKED_GROUPS_MEMO.clear()
        # ① 需給3列が sufficiency の順位に出る
        got = {c for c, _a, _l, _h in ranked_materials("sufficiency")}
        miss = [c for c in dem_cols if c not in got]
        if miss:
            out.append(f"①需給の列が順位に出ない: {miss}")
        # ② demand_on から1件 外すと、その列だけ消える
        off = names[0]
        sw["_demand_set"] = set(keep_dem) - {off}
        got2 = {c for c, _a, _l, _h in ranked_materials("sufficiency")}
        if f"{off}__5m" in got2:
            out.append(f"②demand_on から {off} を外しても順位に残る")
        for n in names[1:]:
            if f"{n}__5m" not in got2:
                out.append(f"②外していない {n} まで順位から消えた")
        # ③ 戻すと出る
        sw["_demand_set"] = set(keep_dem)
        got3 = {c for c, _a, _l, _h in ranked_materials("sufficiency")}
        if f"{off}__5m" not in got3:
            out.append(f"③demand_on に戻しても {off} が順位に出ない（片道になっている）")
        # ④ 列名 → 種類と時間足
        try:
            f4, t4 = _family_tf_from_col(f"{names[0]}__5m")
            if (f4, t4) != (names[0], "5m"):
                out.append(f"④_family_tf_from_col が違う: {(f4, t4)}")
        except SampleError as _e4:
            out.append(f"④_family_tf_from_col が需給で止まる: {_e4}")
        # ⑤ 組の順位＝sufficiency にだけ需給の組が出る
        _RANKED_GROUPS_MEMO.clear()
        # ★set は並びが決まらないので、回す前に sorted で並べる（H2 の番人「並びの決まらない入れ物」）
        g_suf = sorted({g[0] for g in ranked_groups("sufficiency")})
        if not any(f in iref.DEMAND_REF for f in g_suf):
            out.append("⑤ranked_groups('sufficiency') に需給の組が1つも出ない")
        for ro in ("location", "env"):
            g = sorted({g[0] for g in ranked_groups(ro)})
            leak = [f for f in g if f in iref.DEMAND_REF]
            if leak:
                out.append(f"⑤ranked_groups('{ro}') に需給の組が混ざった: {leak}")
    except SystemExit as _e:                              # fail-closed の止まりも ❌ として数える
        out.append(f"T23-demand が途中で止まった: {_e}")
    finally:
        _MATERIAL_RANKING = keep_rank
        _RANKED_GROUPS_MEMO.clear()
        _RANKED_GROUPS_MEMO.update(keep_memo)
        sw["_demand_set"] = set(keep_dem)
    print(f"  T23-demand 需給の列を順位から読む: ①sufficiency に3列 ②印から外すと消える ③戻すと出る "
          f"④列名→(名前, 5m) ⑤location・env の組に混ざらない ／ ダメだった件 {len(out)}")
    return out


def selftest_stages() -> list:
    """T48（2026-10-01・工事 m2f-label-builder-stages-20261001）＝B-1 上端・B-2 出る線の向き・B-5 重なり・B-6 並べる正解。

    ★selftest の T48 と、口 --selftest-stages の両方がこの1本を呼ぶ（判定を2か所に書き写さない）。
      --selftest の全体は約6分半で、承認の前の仮当ての打ち切り（300秒）を超えるため、この口で短く走らせる。
    戻り＝ダメだった件の一覧（空なら全部 通った）。
    """
    t48 = []

    def _find_not48(t):
        if isinstance(t, dict):
            if isinstance(t.get("not"), dict) and t["not"].get("form") == "level":
                return t["not"]
            for _v in t.values():
                _r = _find_not48(_v)
                if _r:
                    return _r
        if isinstance(t, list):
            for _v in t:
                _r = _find_not48(_v)
                if _r:
                    return _r
        return None
    try:
        _lm48, _w48 = load_limits()
        _lm48h = {**_lm48, "stage_keep_range": {"lo": 1, "hi": 10, "kind": "int"}}
        if stage_keep_of(_lm48h, 1) != 1:
            t48.append("B-1: 上端10・候補1本で 1 にならない")
        if STAGE_SPEC["stage1"]["label"] != "強さ" or STAGE_SPEC["stage2c"]["label"] != "強さ":
            t48.append("B-6: 段1・段2c の label が強さでない")
        _laws48 = laws_for_scene("range")
        _tb48 = load_signal_table()
        _pool48, _tfs48, _ = material_pool()
        for _st48 in ("stage1", "stage2a", "stage2c"):
            _cs48 = build_stage_candidates(_st48, _laws48, _tb48, _tfs48, _lm48)
            _ks48 = [json.dumps(_c["cond"], sort_keys=True, ensure_ascii=False) for _c in _cs48]
            if len(_ks48) != len(set(_ks48)):
                t48.append(f"B-5: {_st48} に同じ条件が {len(_ks48) - len(set(_ks48))} 本 重なる")
            if _st48 != "stage2a" and any(_c.get("label") not in ("強さ", None) for _c in _cs48):
                t48.append(f"B-6: {_st48} の候補に強さ以外の正解で並んだ物が在る")
        _bd48, _dr48 = sample_regime_build(_lm48h, _pool48, _tfs48, _tb48)
        _hy48 = _bd48["entry"]["tree"]["all"][0]
        _n48 = _find_not48(_hy48["on"])
        _o48 = _hy48["off"]["any"][2]
        _qi48 = int(str(_n48["value"]["threshold_q"]).lstrip("q"))
        _qo48 = int(str(_o48["value"]["threshold_q"]).lstrip("q"))
        if _o48["side"] != _n48["side"] or not ((_qo48 > _qi48) if _n48["side"] == "above" else (_qo48 < _qi48)):
            t48.append(f"B-2: 段2a の出る線が緩い側でない（入る {_n48['side']} q{_qi48}・出る {_o48['side']} q{_qo48}）")
    except BaseException as _e48:                   # noqa: BLE001
        t48.append(f"途中で止まった: {type(_e48).__name__} {str(_e48)[:120]}")
    return t48


def selftest_stage_q() -> list:
    """T49・T44（2026-10-03・工事 m2f-stage-quantile-rank-20261003）＝段2a の候補の分位ごとの順位と、向きを持つ指標の abs を、成績表の並びに頼らずに試す。

    ★selftest（T48 の後）と、口 --selftest-stage-q の両方がこの1本を呼ぶ（判定を2か所に書き写さない・selftest_stages と同じ作り）。
    T49① 段2a に quantile_grid の分位を全部 書いた設定で、候補の順位が1からの通し番号になり、並びが「材料の順 → 分位の順」になる
    T49② 段2a の系統を、向きを持つ指標（§2.2 の元データの pre の欄）だけに絞った設定で組むと、C に abs が付く
    T44  同じ絞った設定で組んだ束から、分位の解決表の鍵（「abs:列の名前」）が作れる（99回目の不具合・完成の条件 AUDIT-1・前は selftest の中に在った）
    ★なぜ絞った設定で組むか＝いまの設定のまま組むと、段2a の上位10本に向きを持つ指標が来るかは成績表の並び次第（版3 の札で作り直した後は23位から下）で、
      T42・T44 が「測れない」で落ちていた。設定の欄 stage_limits.stage2a.families で絞れば、並びに頼らずに必ず測れる（本物の設定ファイルは書き換えない）。
    戻り＝ダメだった件の一覧（頭に T49①・T49②・T44 を付ける・空なら全部 通った）。
    """
    out: list = []
    try:
        _lm, _ = load_limits()
        _lm = resolve_hold_range(_lm, "e38")
        _laws = laws_for_scene("range")
        _tb = load_signal_table()
        _pool, _tfs, _ = material_pool()
        # ── T49① 分位ごとの候補の順位（設定の quantile_grid を全部 書いた写しで作る）──
        _grid = [str(q) for q in (_lm.get("quantile_grid") or [])]
        if len(_grid) < 2:
            out.append(f"T49①: 設定の quantile_grid が2点未満（{_grid}）＝分位ごとの順位を測れない")
        else:
            _c1 = build_stage_candidates("stage2a", _laws, _tb, _tfs, {**_lm, "stage_limits": {}})
            _cq = build_stage_candidates("stage2a", _laws, _tb, _tfs,
                                         {**_lm, "stage_limits": {"stage2a": {"quantiles": _grid}}})
            if [c["rank"] for c in _cq] != list(range(1, len(_cq) + 1)):
                out.append(f"T49①: 分位を {len(_grid)} 点 書いた段2a の順位が1からの通し番号でない")
            if len(_cq) != len(_c1) * len(_grid):
                out.append(f"T49①: 候補の本数が「1点の本数 × 分位の数」でない（{len(_cq)} ≠ {len(_c1)} × {len(_grid)}）")
            else:
                _bad = None
                for _i, _c in enumerate(_c1):
                    for _k, _g in enumerate(_grid):
                        _x = _cq[_i * len(_grid) + _k]
                        _in = _x["cond"]["not"] if "not" in _x["cond"] else _x["cond"]
                        if _x["col"] != _c["col"] or str(_in["value"].get("threshold_q")) != _g:
                            _bad = (_i * len(_grid) + _k + 1, _x["col"], _in["value"].get("threshold_q"))
                            break
                    if _bad:
                        break
                if _bad:
                    out.append(f"T49①: {_bad[0]} 番目が「材料の順 → 分位の順」でない（{_bad[1]} {_bad[2]}）")
        # ── T49② と T44（段2a の系統を、向きを持つ指標だけに絞った写しで組む）──
        _pre = stage_candidates("stage2a")["pre"]
        _ls = {**_lm, "stage_limits": {"stage2a": {"families": sorted(_pre)}}}
        _n_b, _n_s, _hit = 0, 0, False
        for _i in range(6):
            try:
                _b, _d = sample_regime_build(_ls, _pool, _tfs, _tb, order_n=_i)
            except SampleError:
                continue
            _n_b += 1
            if _d["C"].get("種類") in _pre:
                _n_s += 1
                _on = _regime_on_conds(_b)
                if (_on[2]["not"]["material"][0].get("pre") or {}).get("op") != "abs":
                    out.append(f"T49②: 案{_i} 向きを持つ C（{_d['C'].get('種類')}）に abs が付いていない")
            try:
                _keys = needed_qkeys([{"meta": {"regime": {"build": _b}}, "entry": {"connective": {"all": []}}}])
            except Exception as _e44:                   # noqa: BLE001  KeyError も落ちる（それが99回目の不具合）
                out.append(f"T44: 鍵を作れない: {type(_e44).__name__} {str(_e44)[:80]}")
                break
            if any(str(k).startswith("abs:") for k in _keys):
                _hit = True
        if _n_b == 0:
            out.append("T49②: 系統を絞った設定で、束が1本も組めない＝測れない")
        elif _n_s == 0:
            out.append(f"T49②: 系統を絞った設定で {_n_b} 本 組んでも、向きを持つ C が出ない＝abs を測れない（黙って通さない）")
        if _n_b and not _hit and not any(x.startswith("T44") for x in out):
            out.append("T44: 束を組んでも abs の付いた部品が出なかった＝測れない（嘘の合格を出さない）")
    except BaseException as _e49:                       # noqa: BLE001
        out.append(f"T49: 途中で止まった: {type(_e49).__name__} {str(_e49)[:120]}")
    return out


class _RunStopped(Exception):
    """自己テストの中の本走が、途中で止まった（文＝止まる前に画面へ出た理由の行）。自己テストだけが使う。"""


def _stop_note(text: str) -> str:
    """本走が途中で止まったとき、止まる前に画面へ出た文から、理由の行を短く取り出す（自己テストだけが使う）。"""
    _ls = [x.strip() for x in text.splitlines()]
    _bad = [x for x in _ls if x.startswith("❌")]
    _g2 = [x for x in _ls if x.startswith("[G2] 表に沿っていた構造")]
    _head = _g2[-1] if _g2 else "止まる前の文に [G2] の行が無い"
    return f"{_head} ／ ❌ の行 {len(_bad)} 件" + (f" ／ 1件目＝{_bad[0][:200]}" if _bad else "")


def _selftest_run(fn, *bufs):
    """自己テストの中で本走を呼ぶ口（★2026-10-10・工事 g2-table-range-source-20261010・監査 CP69 の修正1）。

    fn が返した物を、そのまま返す。fn が途中でプログラムごと終わろうとしたら（SystemExit）、止まる前に受け皿（bufs）へ
    出た文から理由の行を取り出し、_RunStopped にして投げる。呼ぶ側は、理由を失敗の一覧に入れて、後ろの検査へ進む。
    直す前＝本走の中の型の表との照らしが SystemExit で終わると、受け皿の文が捨てられ、止まった理由が1行も出ないまま、
    自己テストの全部が終了コード 1 で終わっていた（T6 より後ろの検査が1本も走らない）。
    ★受けるのは SystemExit だけ。ほかの例外は握りつぶさず、そのまま上へ投げる。
    """
    try:
        return fn()
    except SystemExit as _e:
        # ★本走が、止まる理由を SystemExit の中の文として持たせて終わる所（例＝run_generation の「[歩4 エラー] …」）では、
        #   理由は受け皿に出ない。その文も理由に足す（文が無いときは終了コードを足す）。
        _code = _e.code
        _tail = (f" ／ 終わるときの文＝{_code[:200]}" if isinstance(_code, str) and _code
                 else f" ／ 終了コード＝{_code}")
        raise _RunStopped(_stop_note("".join(b.getvalue() for b in bufs)) + _tail) from None


def selftest_stop_note() -> list:
    """本走を呼ぶ口（_selftest_run）の既知答え。戻り＝ダメだった件の一覧（空なら全部 通った）。

    全体の --selftest（T50）と、短い口 --selftest-stop-note が、この同じ本体を呼ぶ（判定を2か所に書き写さない）。
    ★全体の --selftest は、承認の前の仮当ての打ち切り300秒を超える。だから、この枝だけを走らせる口を持つ。
    """
    import io as _io
    out = []
    # ① 途中で止まる本走＝理由の行（[G2] の行・❌ の行の数・1件目）を持った _RunStopped が投げられる
    _b1 = _io.StringIO()

    def _stops():
        _b1.write("[G2] 表に沿っていた構造 見本の行\n❌ 構造#1: 見本の理由\n❌ 構造#2: 見本の理由\n")
        raise SystemExit(1)
    try:
        _selftest_run(_stops, _b1)
        out.append("① 本走が途中で止まったのに、止まったことを知らせない")
    except _RunStopped as _e1:
        _s1 = str(_e1)
        if ("[G2] 表に沿っていた構造 見本の行" not in _s1 or "❌ の行 2 件" not in _s1
                or "1件目＝❌ 構造#1: 見本の理由" not in _s1):
            out.append(f"① 止まった理由の行が欠けている: {_s1}")
    except SystemExit:
        out.append("① 本走が途中で止まると、プログラムごと終わってしまう（理由を知らせていない）")

    # ② 止まらない本走＝fn が返した物が、そのまま返る
    if _selftest_run(lambda: "見本の結果", _io.StringIO()) != "見本の結果":
        out.append("② 止まらない本走の結果が、そのまま返らない")

    # ③ 止まる前の文に [G2] の行も ❌ の行も無い＝そう言う（空の理由にしない）
    def _stops_plain():
        raise SystemExit(1)
    try:
        _selftest_run(_stops_plain, _io.StringIO())
        out.append("③ 本走が途中で止まったのに、止まったことを知らせない")
    except _RunStopped as _e3:
        if "止まる前の文に [G2] の行が無い" not in str(_e3) or "❌ の行 0 件" not in str(_e3):
            out.append(f"③ 止まる前の文に理由の行が無いことを言わない: {_e3}")
    except SystemExit:
        out.append("③ 本走が途中で止まると、プログラムごと終わってしまう（理由を知らせていない）")

    # ④ メタ確認＝SystemExit でない例外は握りつぶさない（そのまま上へ投げる）
    def _raises():
        raise ValueError("見本の例外")
    try:
        _selftest_run(_raises, _io.StringIO())
        out.append("④ SystemExit でない例外（ValueError）が握りつぶされた")
    except _RunStopped:
        out.append("④ SystemExit でない例外（ValueError）が、本走が止まったことにされた")
    except ValueError:
        pass

    # ⑤ 本走が、止まる理由を SystemExit の中の文として持たせて終わる＝その文が理由に入る（受け皿に理由が出ない止まり方）
    def _stops_msg():
        raise SystemExit("[見本エラー] 見本の理由")
    try:
        _selftest_run(_stops_msg, _io.StringIO())
        out.append("⑤ 本走が途中で止まったのに、止まったことを知らせない")
    except _RunStopped as _e5:
        if "終わるときの文＝[見本エラー] 見本の理由" not in str(_e5):
            out.append(f"⑤ SystemExit の中の文が理由に入っていない: {_e5}")
    except SystemExit:
        out.append("⑤ 本走が途中で止まると、プログラムごと終わってしまう（理由を知らせていない）")
    # ⑥ 自己テスト（selftest）の中で本走（run_generation）を呼ぶ所が、全部 口（_selftest_run）を通している
    #   ★行の # より後ろを外してから数える。1か所でも口を通さない呼び方が在れば落ちる。
    import inspect as _insp
    _src50 = "\n".join(ln.split("#", 1)[0] for ln in _insp.getsource(selftest).splitlines())
    _all50 = _src50.count("run_generation(")
    _via50 = _src50.count("_selftest_run(lambda: run_generation(")
    if _all50 == 0 or _all50 != _via50:
        out.append(f"⑥ 自己テストの中で本走を呼ぶ所 {_all50} か所のうち、口を通しているのは {_via50} か所")
    return out


def selftest() -> int:
    """番人＝生成器の機械が正しく効くか（合成データのみ・実データの試行ゼロ・累積試行の記録なし）。

    ★2026-09-11＝「一部の検査だけを走らせる旗」を足すのをやめた（まこさん決定「了解。やめる」）。
      理由＝22件の検査が1つの関数にベタ書きされており、一部を飛ばすには1,000行を超える
        字下げの書き換えが要る。**字下げを1行 間違えると、その検査は黙って走らなくなる。**
        ＝守りを直す作業で守りを壊す危険があるので、やめた。
      壊すプログラムは1本ごとに この自己テストを1回（6分半）走らせる＝10本で約65分 掛かる。
    """
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
            _vr(r, limits={"p_max": lm["p_max"], "count_range": lm["count_range"],
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
            # ★strip_marks を通す（58回目）＝本走と同じ条件にするため。
            #   本走は sample_structure が案を返す直前で印を外すので、実行器に印は届かない。
            #   ここは生成器の中の関数を直に呼ぶテストなので、その一手を自分で入れる。
            _cc(strip_marks(_c6), "", "T1-C6", [])
        except ex.RecipeError as e:
            ng.append(f"T1-C6 番人②: 生成した閾値とのクロスを検証器が拒否する（{str(e)[:60]}）")
            break
    try:
        _cc({"role": "trigger", "form": "cross", "value": {"direction": "up"},
                        "material": [_mat_fixture("RSI", 14, "5m")]},
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
            _cc({"role": "trigger", "form": "cross", "material": _pr,
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
                _cc({"role": "trigger", "form": "cross",
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
            _cc({"role": "trigger", "form": "level", "side": "above",
                            "material": [_m_ok], "value": _thr_fixture("q90")}, "", "T1-C6c", [])
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
                 "side": "above", "value": _thr_fixture("q90")}]}},
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
    _lv_ops = ex.pre_ops(same_unit=False, gen_draw=True)   # ★2026-09-27（M2-E-4e）＝案を作る道が引く部品だけを見る（ts_pos は段2c の動く線だけで使う）
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
        _m_lv = _mat_fixture("RSI", 14, "5m", pre={"op": _lv_ops[0], "n": 20})
        try:
            _cc({"role": "trigger", "form": "level", "side": "above",
                            "material": [_m_lv], "value": _thr_fixture("q80")}, "", "T1-C6e", [])
        except ex.RecipeError as e:
            ng.append(f"T1-C6e 番人②: 水準の前処理つきの条件を検証器が拒否する（{str(e)[:70]}）")
        try:
            _cc({"role": "trigger", "form": "diff", "side": "above",
                            "material": [_mat_fixture("RSI", 14, "5m"), _m_lv],
                            "value": _thr_fixture("q50")}, "", "T1-C6e メタ確認", [])
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
    _ma6f = _mat_fixture("RSI", 7, "5m")
    _mb6f = _mat_fixture("RSI", 21, "5m")
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
    _val6f = {"sub": _thr_fixture("q50"),
              "div": {"op": "div", "th": _thr_fixture("q50")},
              "corr": {"op": "corr", "n": 20, "th": _thr_fixture("q50")}}
    for _o6f, _v6f in _val6f.items():
        try:
            _cc({"role": "trigger", "form": "diff", "side": "above",
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
    for _bad6f, _why6f in (({"op": "corr", "th": _thr_fixture("q50")}, "相関に窓（value.n）が無くても通る"),
                           ({"op": "div"}, "割り算に閾値（value.th）が無くても通る"),
                           ({"op": "mul", "th": _thr_fixture("q50")}, "表に無い組み方 mul が通る")):
        try:
            _cc({"role": "trigger", "form": "diff", "side": "above",
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
             "material": [_ma6f], "value": _thr_fixture("q80")}
    try:
        _cc({"role": "trigger", "form": "barssince", "side": "above",
                        "inner": _in6g, "material": [], "value": {"n": 6}}, "", "T1-C6g", [])
    except ex.RecipeError as e:
        ng.append(f"T1-C6g 番人③: barssince の条件を検証器が拒否する（{str(e)[:70]}）")
    try:
        _cc({"role": "trigger", "form": "barssince",
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
    geo = _geo_of(df)                # 本走と同じ作り方（帯の4隅・中央・帯内位置%・W%・下半分位置）＝手で組むと、印がオンの列が欠ける
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
        _stop6 = None                                # ★ミニ本走が途中で止まったときの理由（止まらなければ None）
        try:
            try:
                with contextlib.redirect_stdout(buf):
                    out1 = _selftest_run(lambda: run_generation(df, **kw), buf)
                with contextlib.redirect_stdout(buf):
                    out2 = _selftest_run(lambda: run_generation(df, **kw), buf)
            except _RunStopped as _e6:
                # ★2026-10-10（監査 CP69 の修正1）＝ミニ本走が途中で止まったら、理由を失敗の一覧に入れて、後ろの検査へ進む。
                #   ★T6 は失敗のまま＝終了コードは 1。本走が止まる原因の直しは、ここには入れていない（やることリストの M2-E-8）。
                _stop6 = str(_e6)
            # T6b（2026-08-05 新設）＝確認の走行では累積が1本も増えない
            if _ts.CUMULATIVE.exists():
                ng.append("T6b: 確認の走行なのに累積ファイルが作られた（数えない約束が守られていない）")
        finally:
            _ts.CUMULATIVE, _ts.CHECK_RUNS = _real_cum, _real_chk
        if _stop6 is not None:
            ng.append(f"T6: ミニ本走が途中で止まった＝{_stop6}（再開と journal の検査は走らせていない）")
        else:
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

    # ── T29 減らしたい損失の実走（要件 R8・2026-08-26 新設・T6 と同じ合成データの小さい本走）──
    #   ★T28 は部品を1つずつ見る検査。T29 は「本走の経路を実際に通したときに、目的が入れ替わり、
    #     損の額と合計 net の両方が画面に出て、再開の記録に指定が残る」ことを見る。
    #   ★メタ確認＝指定が無いときは、画面も記録も直す前のまま（恒等が壊れていないこと）。
    t29: list[str] = []
    _t29_note = ""
    try:
        import contextlib as _c29
        import io as _io29
        with tempfile.TemporaryDirectory() as _td29:
            _rd29 = pathlib.Path(_td29) / "run29"
            _rd29.mkdir(parents=True)
            _rd29b = pathlib.Path(_td29) / "run29b"
            _rd29b.mkdir(parents=True)
            _kw29 = dict(limits=lm, judge=judge, start=s4, end=e4, trials1=10, trials2=6, top_k=2,
                         seed=11, pool=pool, tfs=tfs_small, catalog_total=cat_total,
                         purpose=_ts.PURPOSE_CHECK, tag="selftest29")
            _rc29, _rk29 = _ts.CUMULATIVE, _ts.CHECK_RUNS
            _ts.CUMULATIVE = pathlib.Path(_td29) / "cum.json"
            _ts.CHECK_RUNS = pathlib.Path(_td29) / "chk.json"
            _b29, _b29b = _io29.StringIO(), _io29.StringIO()
            try:
                with _c29.redirect_stdout(_b29):
                    _o29 = _selftest_run(lambda: run_generation(df, run_dir=_rd29, minimize="TIME_EXIT", **_kw29), _b29)
                with _c29.redirect_stdout(_b29b):
                    _o29b = _selftest_run(lambda: run_generation(df, run_dir=_rd29b, **_kw29), _b29b)
            finally:
                _ts.CUMULATIVE, _ts.CHECK_RUNS = _rc29, _rk29
            _s29, _s29b = _b29.getvalue(), _b29b.getvalue()
            # ① 何を目標にするかが画面に出る
            if "[目的] TIME_EXIT の損失を最小化する" not in _s29:
                t29.append("指定しても『何を目標にするか』が画面に出ない")
            # ② 記録の1本1本に損の額が入る
            _miss = [r for r in _o29["results1"] if "focus" not in r]
            if _miss:
                t29.append(f"記録に損の額が入っていない案が {len(_miss)} 本 在る")
            # ③ 損の額と合計 net の両方が並ぶ ／ 1本も出なければ警告
            _n29 = sum(r.get("focus_n", 0) for r in _o29["results1"])
            if _n29:
                if "合計 net $" not in _s29:
                    t29.append("損の額と合計 net の両方が並んだ行が出ていない")
                _t29_note = f"TIME_EXIT が {_n29} 玉 出た＝両方を並べて表示した"
            else:
                if "1本も出ていない" not in _s29:
                    t29.append("指定した理由が1本も出ていないのに警告が出ない")
                _t29_note = "TIME_EXIT が 0玉＝警告の道を通った"
            # ④ 再開の記録に指定が残る（目的の入れ替わりを防ぐ土台）
            _m29 = json.loads((_rd29 / "journal.jsonl").read_text(encoding="utf-8").splitlines()[0])
            if _m29.get("meta", {}).get("minimize") != "TIME_EXIT":
                t29.append("再開の記録に指定が残っていない")
            # ⑤ メタ確認＝指定が無ければ、画面も記録も直す前のまま（恒等）
            if "[目的] 合計 net を最大化する" not in _s29b:
                t29.append("メタ確認: 指定なしで『合計 net を最大化する』が出ない")
            if any("focus" in r for r in _o29b["results1"]):
                t29.append("メタ確認: 指定が無いのに記録へ損の額が入っている（恒等が壊れる）")
            _m29b = json.loads((_rd29b / "journal.jsonl").read_text(encoding="utf-8").splitlines()[0])
            if "minimize" in _m29b.get("meta", {}):
                t29.append("メタ確認: 指定が無いのに再開の記録の欄が増えている（恒等が壊れる）")
    except _RunStopped as _e29s:
        # ★2026-10-10（監査 CP69 の修正1）＝本走が途中で止まったら、理由を失敗の一覧に入れて、後ろの検査へ進む。
        t29.append(f"本走が途中で止まった＝{_e29s}")
    except Exception as _e29:
        t29.append(f"検査が走らない: {type(_e29).__name__} {_e29}")
    ng += [f"T29: {x}" for x in t29]

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
        _vr(r8, limits={"count_range": bad["count_range"], "role_max": bad["role_max"]})
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
        _b10 = _io10.StringIO()
        _stop10 = None                               # ★本走が途中で止まったときの理由（止まらなければ None）
        try:
            try:
                with _ctx10.redirect_stdout(_b10):
                    # ★T6 と同じ種と本数を使う（この合成データで材料が組み立てられることが確認済みの経路）
                    out10 = _selftest_run(lambda: run_generation(
                        df, limits=lm, judge=judge, start=s4, end=e4,
                        trials1=10, trials2=0, top_k=2, seed=11, run_dir=rd10,
                        pool=pool, tfs=tfs_small, catalog_total=cat_total,
                        purpose=_ts10.PURPOSE_CHECK, tag="t10",
                        df_confirm=df, confirm_start=s4, confirm_end=e4,
                        base=None), _b10)
            except _RunStopped as _e10:
                # ★2026-10-10（監査 CP69 の修正1）＝本走が途中で止まったら、理由を失敗の一覧に入れて、後ろの検査へ進む。
                _stop10 = str(_e10)
        finally:
            globals()["build_qtable"] = _real_qt
            _ts10.CUMULATIVE, _ts10.CHECK_RUNS = _rc, _rk
            _tj10.JUDGE_DIR = _jd
        if _stop10 is not None:
            t10.append(f"本走が途中で止まった＝{_stop10}（①②の検査は走らせていない）")
        else:
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
                 "material": [_mat_fixture("ADX", 14, "2h")],
                 "side": "above", "value": _thr_fixture("q50")}]}},
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
    if _stop6 is not None:
        # ★2026-10-10（監査 CP69 の修正1）＝T6 のミニ本走が止まったときは、その結果を使う検査を「走らせていない」と失敗の一覧に入れる。
        t12.append("T6 のミニ本走が途中で止まったので、実走の第1段で 0玉の案が通過していないかの検査は走らせていない")
    else:
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
            st = strip_marks(sample_structure(rng, lm14, pool, tfs_small, side="SHORT", logic_id="S3"))   # 実行器へ直に渡す＝印を外す
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
    geo14 = _geo_of(df14)          # 本走と同じ作り方（帯の4隅・中央・帯内位置%・W%・下半分位置）
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
            st = strip_marks(sample_structure(rng, lm16, pool, tfs_small, side="SHORT", logic_id="S3"))   # 実行器へ直に渡す＝印を外す
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
            st = strip_marks(sample_structure(rng, lm17, pool, tfs_small, side="SHORT", logic_id="S3"))   # 実行器へ直に渡す＝印を外す
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
            st = strip_marks(sample_structure(rng, lm18, pool, tfs_small, side="SHORT", logic_id="S3"))   # 実行器へ直に渡す＝印を外す
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
    if _stop10 is not None:
        # ★2026-10-10（監査 CP69 の修正1）＝T10 の本走が止まったときは、その結果を使うまとめの文を出さない。
        print("  T10 判定表の接続: 本走が途中で止まったので、分位の解決表の回数と結論は出ていない（下の ❌ の行を見る）")
    else:
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
        return {"role": "env", "form": "level", "side": "above", "value": _thr_fixture(q),
                "material": [_mat_fixture(fam, p, tf)]}
    _r22 = {"meta": {"lane": "", "regime": {"name": "range", "entry_col": "x", "build": {
                "entry": {"out_col": "t22_built", "tree": {"all": [
                    _lv22("RSI", 14, "5m", "q30"),
                    {"bool_col": "rg5_uptrend", "want": False},
                    {"not": _lv22("DI差", 14, "1h", "q30")}]}},
                "block": None}}},
            "entry": {"connective": {"all": [
                _lv22("ROC", 12, "5m", "q50"),
                {"form": "hysteresis", "on": _lv22("ADX", 14, "15m", "q70"),
                 "off": _lv22("ADX", 14, "15m", "q40"), "value": {"n": 288}}]}}}
    _k22 = needed_qkeys([_r22])
    _want22 = {"入口のふつうの条件": "ROC12__5m", "状態を保つ形の中": "ADX14__15m",
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
        "value": {"ref": _mat_fixture("ATR%", 14, "1h"), "mult": 0.5,
                  "clip_lo": _thr_fixture("q10"), "clip_hi": _thr_fixture("q90")},
        "material": [_mat_fixture("fractal安値距離%", 2, "1h")]}]}}}
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
        "role": "env", "form": "level", "side": "above", "value": _thr_fixture("q50"),
        "material": [_mat_fixture("RSI", 14, "5m",
                          pre={"op": "since_min", "state": "t22_state"})]}]}}}
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
    #   ①`ranked_materials` の並びが |分離力−0.5| の降順 ②location の1位＝実物で確かめた S-Rタッチ1時間ATR(144,1.0,21)__3m
    #     （★2026-09-26 束2＝成績表を作り直した後の1位・分離力 0.745。直す前＝S-Rタッチ数(144,0.006)__15m・0.743）
    #     （★2026-10-03 工事 m2f-stage-quantile-rank-20261003＝版3 の札で作り直した後の1位・分離力 0.238。直す前＝S-Rタッチ1時間ATR(144,1.5,21)__15m）
    #   ③型の表の外（役割に使えない系統・禁止3）は `_ranked_material_at` が飛ばす ④`regime_draw_order` が決まった並び
    global _MATERIAL_RANKING, _RANK_PATH
    try:
        _rk = load_material_ranking()
        _lst23 = ranked_materials("location")
        _dist23 = [abs(a - 0.5) for _c, a, _l, _h in _lst23]
        if _dist23 != sorted(_dist23, reverse=True):
            ng.append("T23①: 並びが分離力の強い順（|分離力−0.5| の降順）になっていない")
        if _lst23[0][0] != "S-Rタッチ1時間ATR(144,1.0,21)__3m":
            ng.append(f"T23②: location の1位が実物と違う: {_lst23[0]}（成績表を作り直したなら この見本も直す）")
        _tbl23 = load_signal_table()
        _pool23, _tfs23, _ = material_pool()
        _m1, _d1 = _ranked_material_at("location", 1, _tfs23, _tbl23)
        # ★決定 (a')（2026-08-25）＝種類と時間足は順位から・数字は範囲から。列名の数字とは一致しなくてよい。
        _f1, _t1 = _family_tf_from_col(_d1["col"])
        if _m1["family"] != _f1 or _m1["tf"] != _t1 or _d1["rank"] != 1 or _d1["種類"] != _f1:
            ng.append(f"T23③: 1位の材料の種類・時間足が順位の列と食い違う: {_m1} / {_d1}")
        if not param_in_range(_m1["family"], _m1["param"])[0] or PARAM_SRC not in _m1:
            ng.append(f"T23③: 1位の材料の数字が範囲から引かれていない（印なし・または範囲の外）: {_m1}")
        _g23 = ranked_groups("location")
        _dup23 = len(_g23) - len({(g[0], g[1], g[2], g[3]) for g in _g23})
        if _dup23:
            ng.append(f"T23⑤: まとめた順位の中に同じ種類×時間足（同じ札・見通し）が2回 出る: {_dup23} 件")
        # ★2026-09-11（手順10）＝3枠目 G の順位が増えたので、期待する並びも4つ組に直した。
        #   並び＝3つの順位の和が小さい順 → 同じ和なら B が小さい順 → C が小さい順 → above・below。
        _ord = [regime_draw_order(i) for i in range(6)]
        if _ord != [(1, 1, 1, "above"), (1, 1, 1, "below"),
                    (1, 1, 2, "above"), (1, 1, 2, "below"),
                    (1, 2, 1, "above"), (1, 2, 1, "below")]:
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
                _vr(_rr, limits=_lim24)
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
            # ★M2-E-4d（束1・2026-09-25）＝成立の並びは `_regime_on_conds` で読む（形の読み方を1か所に）。
            #   枠を外した束は、持続で包み直す（新しい形＝入る条件は持続1つ・内側が成立の全体）。
            _on, _off = _regime_on_conds(_r24["meta"]["regime"]["build"]), _hy["off"]["any"]
            _on_raw = _hy["on"]["all"]
            _f24 = _on_raw[0] if (len(_on_raw) == 1 and _on_raw[0].get("form") == "streak") else None

            def _wrap24(core):
                return ({"all": [{**_f24, "inner": {"all": list(core)}}]} if _f24 is not None
                        else {"all": list(core)})
            # ★外すときは on と off の両方から外す（off に同じ部品が残ると G7 はそちらで満たされる）
            for _lbl, _mk in (("A（K-6 帯の幅）", lambda t: {"all": [{"form": "hysteresis", "on": _wrap24(_on[1:]), "off": {"any": _off[1:]}, "value": _hy["value"]}]}),
                              ("C（K-5 否定）", lambda t: {"all": [{"form": "hysteresis", "on": _wrap24(_on[:2]), "off": {"any": _off[:2]}, "value": _hy["value"]}]}),
                              ("hysteresis（K-3）", lambda t: _wrap24(_on))):
                _bad = json.loads(json.dumps(_r24))
                _bad["meta"]["regime"]["build"]["entry"]["tree"] = _mk(None)
                try:
                    _vr(_bad, limits=_lim24)
                    ng.append(f"T24③: {_lbl} を外した束が拒否されない")
                except ex.RecipeError as _e:
                    if "G7" not in str(_e)[:12]:
                        ng.append(f"T24③: {_lbl} を外した束が G7 以外で止まった: {str(_e)[:60]}")
            # ★59回目＝最初に通った案が 0番目とは限らない（引いた数字が禁止3 に当たると その案だけ作れない）。
            #   見るのは「最初に通った案の (B,C) が、その案の番号の並びどおりか」。
            _o24 = int(_r24["meta"]["regime_draw"]["order_n"])
            if (_r24["meta"]["regime_draw"]["B"]["rank"], _r24["meta"]["regime_draw"]["C"]["rank"]) != regime_draw_order(_o24)[:2]:
                ng.append(f"T24④: 最初に通った案（{_o24}番目）の (B,C) が並びどおりでない: {_r24['meta']['regime_draw']}")
            _bad24 = [(i, got, regime_draw_order(i)[:2]) for i, got in _orders24 if got != regime_draw_order(i)[:2]]
            if _bad24:
                ng.append(f"T24④: 案の (B,C) の順位が並びどおりでない（番号, 実物, 期待）: {_bad24[:4]}")
        print(f"  T24 場面の判定の束（レンジ）: ①hysteresis on {_c24['on']['value']} → off {_c24['off']['value']}"
              f"（n={_c24['value']['n']}）／ ②{_n24}本 組んで検査（G5・G6・G7）を通った {_ok24}本"
              f"（通らなかった内訳 {dict(_rej24) or 'なし'}）／ ③A・C・hysteresis を外すと G7 で落ちる"
              f" ／ ④0番目は (1,1)・並びどおり・同じ番号なら同じ指標 ／ 引いた記録の例 {(_r24 or {}).get('meta', {}).get('regime_draw')}")
    except SystemExit as _e24:
        ng.append(f"T24: 途中で止まった: {_e24}")

    # ══ T40 段ごとの候補を全部 並べる＝完成の条件 条件12（M2-E-3 の手順4・5・2026-09-11）═══════════
    #   設計書の逐語＝「候補を作る関数が、段ごとに決まった本数の候補を返す（段1 が 354本・段2a が 104本・
    #   段2b が 1本・段2c が 229本。±10% まで許し、外れたら理由を画面に出す）」。
    #   ★本数の出どころ＝監査 cp35 の実測（依頼を出した CC も同じプログラムを走らせ直して一致）。
    #   ★壊すプログラム b86_stage_count.sh が、法則の名指しを外すと本数が桁で変わることを測る。
    try:
        _lm40, _ = load_limits()
        _lm40 = resolve_hold_range(_lm40, "e38")
        _t40 = load_signal_table()
        _p40, _tfs40, _ = material_pool()
        _laws40 = laws_for_scene("range")
        # ★本数は画面に出すだけ（合格の条件にしない・完成の条件 条件12）。
        #   直す前は {"stage1": 354, …}（監査の実測）と ±10% で比べていた＝私（CC）が
        #   その数に近づくまで絞り方を3回 書き換えた（不正）。2026-09-11 に外した。
        _got40 = {}
        for _st40 in ("stage1", "stage2a", "stage2b", "stage2c", "stage3"):
            _c40 = build_stage_candidates(_st40, _laws40, _t40, _tfs40, _lm40)
            _got40[_st40] = len(_c40)
            # ① 鍵は11個・どの段でも同じ並び（読む側が段ごとに形を変えなくて済む）
            _keys40 = {"stage", "rank", "col", "family", "tf", "acc", "label", "horizon",
                       "cond", "law_check", "dropped_by"}
            if set(_c40[0]) != _keys40:
                ng.append(f"T40①: {_st40} の候補1件の鍵が11個でない: {sorted(set(_c40[0]) ^ _keys40)}")
            # ② 順位は1から連番
            if [c["rank"] for c in _c40] != list(range(1, len(_c40) + 1)):
                ng.append(f"T40②: {_st40} の順位が1からの連番でない")
        # ③ 候補の出どころを4つ 測る（完成の条件 条件12・2026-09-11 に本数の判定と入れ替えた）
        #   ★変数名を `_src40` にしない＝⑥ が同じ名前でファイルの中身を読む（2026-09-11 に衝突した）
        _origin40 = {}
        for _st40 in ("stage1", "stage2a", "stage2c"):
            _sc40 = stage_candidates(_st40)
            _c40 = build_stage_candidates(_st40, _laws40, _t40, _tfs40, _lm40)
            _fams40 = [c["family"] for c in _c40]
            # ③-1 ★2026-09-19（設計書 m2c-width-and-stage-candidates-20260918・まこさん承認）＝
            #   「§2.2 の元データの中だけから来ているか」を見るのをやめ、
            #   **印と法則と役割と時間足と標本で許される指標が、全部 候補に出ているか**を見る。
            #   なぜ＝直す前の形は、印より狭い名前の一覧を「正しいもの」として測っていた＝
            #     印がオンで法則も許す指標（MMI・SQZ_ON ほか）が落ちても ✅ になっていた。
            #   ★許される指標は、候補を作るのと同じ関数で作る（判定を2か所に書かない）。
            _rr40 = _t40["roles"][_sc40["role"]]
            _rng40 = material_ranges()
            _tfok40 = stage_tfs_of(_st40, _sc40, _laws40, _t40, _tfs40, _lm40)
            _lawf40, _ = _law_families(_laws40, _sc40["law"])
            _lawl40 = stage_lineages_of(_st40, _sc40, _laws40)
            _want40 = set()
            for _f9, _tf9, _l9, _h9, _m9, _n9, _col9 in ranked_groups(_sc40["role"], None):
                if _f9 not in iref.FAMILY_LINEAGE or _f9 not in _rng40:
                    continue
                if iref.FAMILY_LINEAGE[_f9]["k"] not in _rr40["lineages"] or _tf9 not in _tfok40:
                    continue
                if not _group_usable_col(_col9, _f9, _tf9, _rng40, _t40):
                    continue
                if STAGE_SPEC[_st40]["pick"] == "family":
                    if _lawf40 and _f9 not in _lawf40:
                        continue
                elif _lawl40 and iref.FAMILY_LINEAGE[_f9]["k"] not in _lawl40:
                    continue
                _want40.add(_f9)
            _ng1 = sorted(_want40 - set(_fams40))
            if _ng1:
                ng.append(f"T40③-1: {_st40} で、印と法則と役割と時間足で許される指標が候補に出ていない: {_ng1[:5]}")
            # ③-2 指標が法則の名指し（family か 系統）の中だけから来ているか
            # ★2026-09-13（完成の条件 #4・まこさん決定「一本化する」）＝法則の番号は元データから読む
            #   （直す前は STAGE_SPEC の law と "R3" の文字を読んでいた）。組む側と同じ所を読む。
            _law40 = stage_candidates(_st40)["law"]
            _fl40, _ = _law_families(_laws40, _law40)
            _lor40 = stage_candidates(_st40).get("law_or")
            _ll40 = _law_lineages(_laws40, _law40) or (_law_lineages(_laws40, _lor40) if _lor40 else ())
            if STAGE_SPEC[_st40]["pick"] == "family":
                _ng2 = sorted({f for f in _fams40 if _fl40 and f not in _fl40})
            else:
                _ng2 = sorted({f for f in _fams40
                               if _ll40 and iref.FAMILY_LINEAGE[f]["k"] not in _ll40})
            if _ng2:
                ng.append(f"T40③-2: {_st40} に法則 {_law40} が名指ししていない指標が出た: {_ng2[:5]}")
            # ③-3 時間足が、その段で使ってよいものだけか（外す3本を含まない）
            # ★2026-09-16（監査 cp36 の M-3）＝「執行足より上」を、ここに直書きしない。
            #   段の元データの `law_tf` が指す法則から読む（`stage_tfs_of` と同じ道）。
            #   ＝段2c は `law_tf` を持たないので、執行足（5分足）も使ってよい。
            #   出どころ＝§2.2-3 の逐語「段2c（役割 sufficiency＝全時間足）からも 1m・3m・10m を外す」。
            _tfs_all40 = list(_t40["tfs"])
            _sc40 = stage_candidates(_st40)
            if _law_tf_upper(_laws40, _sc40.get("law_tf")):
                _upper40 = {t for t in _tfs_all40 if _tfs_all40.index(t) > _tfs_all40.index("5m")}
            else:
                _upper40 = set(_tfs_all40)
            _drop40 = set(drop_tfs_of(_lm40, _t40))
            _ng3 = sorted({c["tf"] for c in _c40
                           if c["tf"] not in _upper40 or c["tf"] in _drop40})
            if _ng3:
                ng.append(f"T40③-3: {_st40} に引いてはいけない時間足が出た: {_ng3}")
            # ③-4 元データの指標のうち、1件以上が候補に出ている（0件なら落ちる）
            if not _fams40:
                ng.append(f"T40③-4: {_st40} の候補が0件（§2.2 の元データの指標が1件も引けていない）")
            # ③-6 時間足の絞りを「法則から読む」ことを、段2c で測る（監査 cp36 の M-3・2026-09-16）
            #   ★なぜ段2c か＝段2c は元データに `law_tf` を持たない＝執行足より上に絞らない段。
            #     だから **執行足（5分足）が候補に出る**のが正しい姿（§2.2-3 の逐語
            #     「段2c（役割 sufficiency＝全時間足）からも 1m・3m・10m を外す」＝5m は外さない）。
            #   ★③-3 では測れない＝あちらは「出てはいけない時間足が出た」を見るので、
            #     絞りすぎて 5m が**消えた**ことは捕まらない（壊すプログラム b96 が rc=0 になった実測）。
            if _st40 == "stage2c" and "5m" not in {c["tf"] for c in _c40}:
                ng.append("T40③-6: stage2c の候補に執行足（5m）が無い"
                          "（段2c は law_tf を持たない＝上位足に絞らない段）")
            _origin40[_st40] = {"出た指標": len(set(_fams40)),
                                "元データの指標": len(_sc40["families"]) + len(_sc40["lineages"])}
        # 段2b は候補が1本（真偽の列の借用）＝本数でなく形を見る（⑤で見る）
        if _got40.get("stage2b") != 1:
            ng.append(f"T40③-5: stage2b の候補が {_got40.get('stage2b')} 本（1本であること）")
        # ④ 段2a の向きを持つ3つに、符号を取り去る前処理が付くこと
        _c2a = build_stage_candidates("stage2a", _laws40, _t40, _tfs40, _lm40)
        _pre2a = stage_candidates("stage2a")["pre"]          # ★元データの `pre` から引く
        _signed40 = [c for c in _c2a if c["family"] in _pre2a]
        _nopre40 = [c["col"] for c in _signed40
                    if (c["cond"]["not"]["material"][0].get("pre") or {}).get("op") != "abs"]
        if _signed40 and _nopre40:
            ng.append(f"T40④: 向きを持つ指標に符号を取り去る前処理が付いていない: {_nopre40[:3]}")
        # ⑤ 段2b は `not` で包んだ `bool_col`（`want` は true）
        _c2b = build_stage_candidates("stage2b", _laws40, _t40, _tfs40, _lm40)[0]["cond"]
        if _c2b != {"not": {"bool_col": "rg5_uptrend", "want": True}}:
            ng.append(f"T40⑤: 段2b の形が設計書と違う: {_c2b}")
        # ⑥ 守りが緩んでいないこと＝`build_stage_candidates` を「材料を書いてよい関数」の一覧に足したので、
        #    その関数が材料を手で書いていないことを機械で確かめる（材料は `_mat_drawn` で作る）。
        _src40 = pathlib.Path(__file__).read_text(encoding="utf-8")
        _fn40 = _src40[_src40.index("def build_stage_candidates"):]
        _fn40 = _fn40[:_fn40.index("\ndef ")]
        _code40 = "\n".join(_l.split("#", 1)[0] for _l in _fn40.splitlines())
        # ★2026-09-11（手順9）＝材料を作る入口が2つになった（`_mat_drawn`＝範囲から引く／
        #   `_mat_from_col`＝成績表の列の数字をそのまま使う・乱数を使わない）。どちらかを呼んでいること。
        if not any((_c + "(") in _code40 for _c in ("_mat_drawn", "_mat_from_col")):
            ng.append("T40⑥: 候補を作る関数が、材料を作る入口（_mat_drawn・_mat_from_col）を呼んでいない")
        if '"param"' in _code40:
            ng.append("T40⑥: 候補を作る関数が材料の数字（param）を手で書いている")
        print(f"  T40 段ごとの候補: 本数 {_got40}（★記録だけ・合格の条件にしない）"
              f" ／ ③出どころ {_origin40}"
              f" ／ ①鍵11個・②順位は連番 ／ ④向きを持つ {len(_signed40)} 件に符号を取り去る前処理"
              f" ／ ⑤段2b は not で包んだ bool_col")
    except SystemExit as _e40s:
        ng.append(f"T40: 途中で拒否されて止まった: {str(_e40s)[:120]}")
    except Exception as _e40:
        ng.append(f"T40: 途中で止まった: {type(_e40).__name__} {_e40}")

    # ══ T39 帯の枠が法則 R1・R3 の系統から引かれている＝完成の条件 AUDIT-4b（手順10・2026-09-11）═════
    #   監査 cp35 の Critical C-1＝直す前は、法則の系統を書き替えても帯の材料が1文字も変わらなかった。
    #   ★測り方＝法則ファイルの写しを作り、R1・R3 の系統を別のものに書き替えて、帯が変わるかを見る。
    #     本物の法則ファイルは1文字も書き替えない（実行器が読む一覧を、その場で差し替えて戻す）。
    #   ★壊すプログラム b85_band_ignores_laws.sh が、役割の直書きに戻すとこの検査が落ちることを測る。
    try:
        _lm39, _ = load_limits()
        _lm39 = resolve_hold_range(_lm39, "e38")
        _p39, _t39, _ = material_pool()
        _keep39 = ex.load_regime_laws()

        def _band39(inj=None):
            """束を1本 組んで、帯の枠（B）の材料の名前を返す。inj＝法則の一覧の差し替え。"""
            _save = getattr(ex, "_REGIME_LAWS", None)
            try:
                if inj is not None:
                    ex._REGIME_LAWS = inj
                for _i in range(30):
                    try:
                        _r = sample_structure(np.random.default_rng([39, _i]), _lm39, _p39, _t39,
                                              side="SHORT", logic_id=f"T39_{_i}",
                                              build_regime=True, regime_order_n=0)
                    except SampleError:
                        continue
                    return (_r["meta"]["regime_draw"]["B"] or {}).get("col")
                return None
            finally:
                ex._REGIME_LAWS = _save
        # ① いまの法則で帯が引けること
        _b39 = _band39()
        if not _b39:
            ng.append("T39①: いまの法則で帯の材料が引けない（束が1本も組めない）")
        # ② 引いた記録に「法則が名指しした系統」が入っていること（法則を読んだ証拠）
        _r39 = None
        for _i in range(30):
            try:
                _r39 = sample_structure(np.random.default_rng([39, _i]), _lm39, _p39, _t39,
                                        side="SHORT", logic_id=f"T39b_{_i}",
                                        build_regime=True, regime_order_n=0)
                break
            except SampleError:
                continue
        if _r39 is not None and "法則が名指しした系統" not in (_r39["meta"]["regime_draw"]["B"] or {}):
            ng.append("T39②: 帯の記録に『法則が名指しした系統』が無い＝法則を読んでいない")
        # ③ 法則 R1・R3 の系統を別のものに書き替えると、帯の材料が変わる（または組めなくなる）
        _inj39 = json.loads(json.dumps(_keep39))
        _hit39 = 0
        for _x in _inj39:
            if _x["番号"] in ("R1", "R3") and isinstance(_x.get("判定"), dict):
                _sel = _x["判定"].get("数える部品") or {}
                if "系統" in _sel:
                    _sel["系統"] = ["ボラ"]            # ★構造・位置 → ボラ に書き替える
                    _hit39 += 1
        if _hit39 != 2:
            ng.append(f"T39③: 法則 R1・R3 の系統の欄が 2件 見つからない（{_hit39} 件）＝測れない")
        else:
            _b39b = _band39(_inj39)
            if _b39b == _b39:
                ng.append(f"T39③: R1・R3 の系統を『ボラ』に書き替えても帯が変わらない（{_b39}）"
                          "＝帯が法則を読んでいない（監査 cp35 の Critical C-1）")
        print(f"  T39 帯の枠が法則から引かれている: ①いまの法則で帯＝{_b39}"
              f" ／ ②記録に『法則が名指しした系統』が入っている"
              f" ／ ③系統を『ボラ』に書き替えると帯＝{_b39b if _hit39 == 2 else '—'}（変わる）")
    except SystemExit as _e39s:
        ng.append(f"T39: 途中で拒否されて止まった: {str(_e39s)[:120]}")
    except Exception as _e39:
        ng.append(f"T39: 途中で止まった: {type(_e39).__name__} {_e39}")

    # ══ T41 段ごとの記録（stages）＝完成の条件 条件13（M2-E-3 の手順6・2026-09-11）════════════
    #   監査 cp35 の Critical C-3＝作る順の手順6 に当たる条件が1つも無かった。
    try:
        _lm41, _ = load_limits()
        _lm41 = resolve_hold_range(_lm41, "e38")
        _t41 = load_signal_table()
        _p41, _tfs41, _ = material_pool()
        _laws41 = laws_for_scene("range")
        _st41 = stage_counts(_laws41, _t41, _tfs41, _lm41)
        # ① 鍵6つ（設計書 4-8）が全部 揃っている
        _keys41 = {"stage", "n_candidates", "n_passed", "keep", "sec", "dropped"}
        _bad41 = [r.get("stage") for r in _st41 if not _keys41 <= set(r)]
        if _bad41:
            ng.append(f"T41①: 段ごとの記録に鍵6つが揃っていない: {_bad41}")
        # ② 5段ぶん在る（段1・2a・2b・2c・3）
        if len(_st41) != 5:
            ng.append(f"T41②: 段ごとの記録が5段でない（{len(_st41)}段）")
        # ③ 測っていない欄は null＝0 と書かない（「0本 落ちた」と読めてしまうため）
        _bad41b = [r.get("stage") for r in _st41 if r.get("n_passed") is not None]
        if _bad41b:
            ng.append(f"T41③: 測っていない『審査を通った本数』に数字が入っている: {_bad41b}")
        print(f"  T41 段ごとの記録: {len(_st41)}段・鍵6つ ／ "
              + "・".join(f"{r.get('stage')} {r.get('n_candidates')}本" for r in _st41))
    except SystemExit as _e41s:
        ng.append(f"T41: 途中で拒否されて止まった: {str(_e41s)[:120]}")
    except Exception as _e41:
        ng.append(f"T41: 途中で止まった: {type(_e41).__name__} {_e41}")

    # ══ T24⑤ 法則を1件ずつ書き替えると、実際に組まれる束が変わる＝完成の条件 AUDIT-1（監査 cp36 の C-3・2026-09-13）═══
    #   測り方＝法則ファイルの写し（`ex._REGIME_LAWS` を差し替えて戻す・T39 と同じ口）を、組む側が読む9件について
    #   1件ずつ書き替え、案0〜5 を組み直して土台と比べる（印を外した束のハッシュ値と B・C・G の col）。
    #   期待＝★2026-09-16（監査 cp36 の M-3 を直した後）＝**9件とも変わる**（組めなくなるものを含む）。
    #     直す前は7件（C6・R1・R4・R5・R6・R7・R8）だけが変わり、C4（組む側が読まない）と
    #     R3（R1 が系統を持つ間は読まれない）は変わらなかった＝監査 cp36 §2 の実測。
    #     いまは R3 を `stage_lineages_of` が `law_tf` から読み、C4 は `_check_bundle_counts` が
    #     束を組んだ後に本数を数える。
    #     ★変わるはずの件が変わらなくなったら落ちる＝作りが戻ったことを知らせる。
    #   ★本物の法則ファイルは1文字も触らない。壊すプログラム b93（1本目の法則の絞りを外す）で落ちることを測る。
    try:
        _lm45, _ = load_limits()
        _lm45 = resolve_hold_range(_lm45, "e38")
        _t45 = load_signal_table()
        _p45, _tfs45, _ = material_pool()
        _keep45 = ex.load_regime_laws()
        _N45 = 6

        def _scan45(inj=None):
            """案0〜N-1 の束を組み、番号 → (ハッシュ値, B の col, C の種類, G の種類) を返す。組めない番号は理由の文字。"""
            _save = getattr(ex, "_REGIME_LAWS", None)
            _memo = dict(_STAGE_COUNT_MEMO)
            try:
                if inj is not None:
                    ex._REGIME_LAWS = inj
                out = {}
                for _i in range(_N45):
                    try:
                        _b, _d = sample_regime_build(_lm45, _p45, _tfs45, _t45, order_n=_i)
                        _h = hashlib.sha256(json.dumps(strip_marks(_b), sort_keys=True,
                                                       ensure_ascii=False).encode("utf-8")).hexdigest()[:16]
                        out[_i] = (_h, (_d.get("B") or {}).get("col"), (_d.get("C") or {}).get("種類"),
                                   (_d.get("G") or {}).get("種類"))
                    except SampleError as _e:
                        out[_i] = ("組めない: " + str(_e)[:60],)
                return out
            finally:
                ex._REGIME_LAWS = _save
                _STAGE_COUNT_MEMO.clear()
                _STAGE_COUNT_MEMO.update(_memo)

        _base45 = _scan45()
        _ok45 = [v for v in _base45.values() if len(v) == 4]
        if not _ok45:
            ng.append("T24⑤: 土台の束が1本も組めない＝測れない")
        _c_fam45 = _ok45[0][2] if _ok45 else None      # 土台の C の種類（R5 の書き替えで、これと違う family を選ぶ）
        _g_fam45 = _ok45[0][3] if _ok45 else None

        def _mut45(no, law):
            """法則1件の写しを、その番号なりの形で書き替える（書き替えられたら True）。"""
            j = law.get("判定") if isinstance(law.get("判定"), dict) else None
            if j is None:
                return False
            sel = j.get("数える部品") or {}
            if no == "C4":
                # ★2026-09-16（監査 cp36 の M-3・完成の条件 AUDIT-4）＝C4 は束の単位で数える法則なので、
                #   「本数」を束の部品の数より大きくした写しで、組めなくなることを測る。
                #   直す前＝掛かる場面から range を外していた（組む側が C4 を1つも読んでいなかったので変わらなかった）。
                j["本数"] = 99
            elif no == "C6":                                    # 掛かる場面から range を外す
                j["掛かる場面"] = [s for s in (j.get("掛かる場面") or []) if s != "range"]
            elif no in ("R4", "R8"):                            # range → uptrend（空にすると読み込みが止まる＝監査 §11-3）
                j["掛かる場面"] = ["uptrend" if s == "range" else s for s in (j.get("掛かる場面") or [])]
            elif no in ("R1", "R3"):                            # 系統 → ボラ
                if "系統" not in sel:
                    return False
                sel["系統"] = ["ボラ"]
            elif no in ("R5", "R6"):                            # family を、土台で使われたものと違う1件だけに
                fams = list(sel.get("family") or [])
                _avoid = _c_fam45 if no == "R5" else _g_fam45
                pick = next((f for f in fams if f != _avoid), None)
                if pick is None:
                    return False
                sel["family"] = [pick]
                sel["側"] = {k: v for k, v in (sel.get("側") or {}).items() if k == pick}
            elif no == "R7":                                    # geo → 帯内位置%（側 below）
                sel["geo"] = ["帯内位置%"]
                sel["側"] = {"帯内位置%": "below"}
            else:
                return False
            return True

        # ★2026-09-16（監査 cp36 の M-3・完成の条件 AUDIT-4）＝9件とも変わる。
        #   直す前＝C4 と R3 は「変わらない」が期待だった（C4 は組む側が読まない・
        #   R3 は R1 が系統を持つ間は読まれない＝監査 cp36 §2 の実測）。
        #   直した後＝R3 は `stage_lineages_of` が `law_tf` から読む。
        #   C4 は `_check_bundle_counts` が束を組んだ後に本数を数える。
        _expect45 = {"C4": True, "C6": True, "R1": True, "R3": True, "R4": True,
                     "R5": True, "R6": True, "R7": True, "R8": True}
        _got45 = {}
        for _no in _expect45:
            _inj = json.loads(json.dumps(_keep45))
            _hit = sum(1 for _x in _inj if _x.get("番号") == _no and _mut45(_no, _x))
            if _hit != 1:
                ng.append(f"T24⑤: 法則 {_no} の判定の欄が写しに見つからない（{_hit}件）＝測れない")
                continue
            _got45[_no] = (_scan45(_inj) != _base45)
        _bad45 = [n for n, e in _expect45.items() if n in _got45 and _got45[n] != e]
        if _bad45:
            ng.append("T24⑤: 期待と違う: " + ", ".join(f"{n}={'変わった' if _got45[n] else '変わらない'}" for n in _bad45)
                      + "（期待＝9件とも変わる＝監査 cp36 の M-3 を直した後）")
        print(f"  T24⑤ 法則を1件ずつ書き替える: 変わった {sorted(n for n, v in _got45.items() if v)}"
              f" ／ 変わらない {sorted(n for n, v in _got45.items() if not v)}（期待＝9件とも変わる）")
    except SystemExit as _e45s:
        ng.append(f"T24⑤: 途中で拒否されて止まった: {str(_e45s)[:120]}")
    except Exception as _e45:
        ng.append(f"T24⑤: 途中で止まった: {type(_e45).__name__} {_e45}")

    # ══ T42 実際の束（2本目）が段ごとの候補の一覧の上位から来ている＝完成の条件 AUDIT-2（監査 cp36 の C-1・C-2・2026-09-13）═
    #   ①B・C・G が、その段の一覧の順位の候補と一致（cond が深い写しで等しい・C は not で包んだまま・材料の pre を含む）
    #   ②B・C・G の時間足に、外す3本（drop_tfs）が1本も無い
    #   ③向きを持つ指標（元データの pre の欄）が C に出たとき、材料に abs が付いている
    #     （★2026-10-03＝1件も出ないときの「測れない」は T49② へ移した＝段2a の系統を絞った設定で、成績表の並びに頼らずに必ず測る）
    #   ④記録の keep（上位）が stage_keep_of と一致
    #   ★壊すプログラム b92（2本目に渡す設定の drop_tfs を空にする）で落ちることを測る。
    try:
        _lm42, _ = load_limits()
        _lm42 = resolve_hold_range(_lm42, "e38")
        _t42 = load_signal_table()
        _p42, _tfs42, _ = material_pool()
        _laws42 = laws_for_scene("range")
        _c42 = {k: build_stage_candidates(k, _laws42, _t42, _tfs42, _lm42) for k in ("stage1", "stage2a", "stage2c")}
        _drop42 = set(_lm42.get("drop_tfs") or ["1m", "3m", "10m"])
        _pre42 = stage_candidates("stage2a")["pre"]
        _role_g42 = stage_candidates("stage2c")["role"]
        _n_built42, _n_signed42, _ng42 = 0, 0, []
        for _i in range(200):
            try:
                _b42, _d42 = sample_regime_build(_lm42, _p42, _tfs42, _t42, order_n=_i)
            except SampleError:
                continue
            _n_built42 += 1
            _rb, _rc, _rg, _sb = regime_draw_order(_i)
            _on42 = _regime_on_conds(_b42)       # 並び＝[A, B, C, (D), (G)]＝持続の内側の成立の並び（M2-E-4d・束1）
            # ★比べる相手も json を通す＝2本目の条件は深い写し（json 経由・tuple が list になる）なので、
            #   一覧の生の条件（材料の数字が tuple）と直接 比べると、中身が同じでも違うと出る（2026-09-13 に実測）。
            _jj = lambda o: json.loads(json.dumps(o))                                   # noqa: E731
            _want_b = _jj(_c42["stage1"][_rb - 1]["cond"])
            _want_b["side"] = _sb
            if _on42[1] != _want_b:
                _ng42.append(f"案{_i} B が段1 の一覧の {_rb} 位と違う")
            if _on42[2] != _jj(_c42["stage2a"][_rc - 1]["cond"]):
                _ng42.append(f"案{_i} C が段2a の一覧の {_rc} 位と違う")
            if _d42.get("G"):
                _cg = next((c for c in _on42 if isinstance(c, dict) and c.get("form") == "level"
                            and c.get("role") == _role_g42), None)
                if _cg != _jj(_c42["stage2c"][_rg - 1]["cond"]):
                    _ng42.append(f"案{_i} G が段2c の一覧の {_rg} 位と違う")
            for _k in ("B", "C", "G"):
                if _d42.get(_k) and _d42[_k].get("時間足") in _drop42:
                    _ng42.append(f"案{_i} {_k} に外す時間足 {_d42[_k].get('時間足')} が出た")
            # ★2026-09-14（承認②で b92 が落ちなかった＝設計書のリスク3 が実際に起きた）＝記録の「上位」（その段で
            #   使ってよい本数）が、本物の設定と本物の一覧の本数から出る値と一致するかも見る。2本目が別の設定
            #   （外す時間足を含む）で一覧を作ると本数が変わるので、順位の上位に10分足が上がってこなくても
            #   案0 の時点で必ず食い違う（決定的）。
            for _k, _st in (("B", "stage1"), ("C", "stage2a"), ("G", "stage2c")):
                if _d42.get(_k) and _d42[_k].get("上位") != stage_keep_of(_lm42, len(_c42[_st])):
                    _ng42.append(f"案{_i} {_k} の記録の上位（{_d42[_k].get('上位')}）が、本物の一覧の本数から出る値"
                                 f"（{stage_keep_of(_lm42, len(_c42[_st]))}）と違う＝別の一覧から取っている")
            if _d42["C"].get("種類") in _pre42:
                _n_signed42 += 1
                if (_on42[2]["not"]["material"][0].get("pre") or {}).get("op") != "abs":
                    _ng42.append(f"案{_i} 向きを持つ C（{_d42['C'].get('種類')}）に abs が付いていない")
            for _r in _d42.get("stages", []):
                if _r.get("n_candidates") and _r.get("keep") != stage_keep_of(_lm42, _r["n_candidates"]):
                    _ng42.append(f"案{_i} {_r.get('stage')} の記録の keep が設定と違う")
            if _n_built42 >= 40 and _n_signed42 >= 1:
                break
        if _n_built42 == 0:
            ng.append("T42: 束が1本も組めない＝測れない")
        # ★2026-10-03（工事 m2f-stage-quantile-rank-20261003）＝「向きを持つ C が1件も出ない＝測れない」は T49② へ移した。
        #   いまの設定のまま組むと、段2a の上位10本に向きを持つ指標が来るかは成績表の並び次第（版3 の札で作り直した後は23位から下）。
        #   T49② は段2a の系統を向きを持つ指標だけに絞った設定で組むので、並びに頼らずに abs を必ず測る。
        if _ng42:
            ng.append(f"T42: 2本目が一覧の上位から来ていない（{len(_ng42)}件）: {_ng42[:4]}")
        print(f"  T42 2本目は一覧の上位から: 案 {_n_built42} 本／一覧と合わない・外す時間足・abs 無し・keep の食い違い＝"
              f"{len(_ng42)} 件／向きを持つ C {_n_signed42} 件")
    except SystemExit as _e42s:
        ng.append(f"T42: 途中で拒否されて止まった: {str(_e42s)[:120]}")
    except Exception as _e42:
        ng.append(f"T42: 途中で止まった: {type(_e42).__name__} {_e42}")

    # ══ T35 設定の欄 stage_keep_range が読まれている＝完成の条件 AUDIT-3（監査 cp36 の C-2・2026-09-13）═════════
    #   ①上端 null → keep＝候補の本数 ②上端 1 → 案0 は組めて記録の keep が 1・案2（G が2位）は「上位 1 本の外」で組めない
    #   ③範囲の外（lo 0／lo > hi）は止まる（fail-closed）・上端が候補の本数を超えるときは候補の本数を使う（2026-10-01・B-1）
    #   ★壊すプログラム b91（stage_keep_of が設定を読まずに候補の本数を返す）で落ちることを測る。
    try:
        _lm35, _ = load_limits()
        _lm35 = resolve_hold_range(_lm35, "e38")
        _t35 = load_signal_table()
        _p35, _tfs35, _ = material_pool()
        _laws35 = laws_for_scene("range")
        _n35 = len(build_stage_candidates("stage1", _laws35, _t35, _tfs35, _lm35))
        _lmA = {**_lm35, "stage_keep_range": {"lo": 1, "hi": None, "kind": "int"}}
        if stage_keep_of(_lmA, _n35) != _n35:
            ng.append(f"T35①: 上端 null なのに keep が候補の本数（{_n35}）でない: {stage_keep_of(_lmA, _n35)}")
        _lmB = {**_lm35, "stage_keep_range": {"lo": 1, "hi": 1, "kind": "int"}}
        try:
            _b35, _d35 = sample_regime_build(_lmB, _p35, _tfs35, _t35, order_n=0)
            _k35 = [r.get("keep") for r in _d35.get("stages", []) if r.get("n_candidates")]
            if any(k != 1 for k in _k35):
                ng.append(f"T35②: 上端 1 なのに記録の keep が {_k35}")
        except SampleError as _e35a:
            ng.append(f"T35②: 上端 1 で案0 が組めない: {str(_e35a)[:80]}")
        try:
            sample_regime_build(_lmB, _p35, _tfs35, _t35, order_n=2)
            ng.append("T35②: 上端 1 なのに案2（G が2位）が組めた＝stage_keep_range が読まれていない")
        except SampleError as _e35b:
            if "上位 1 本の外" not in str(_e35b):
                ng.append(f"T35②: 案2 の止まり方が違う: {str(_e35b)[:80]}")
        for _bad35, _why35 in (({"lo": 0, "hi": None}, "lo 0"), ({"lo": 3, "hi": 2}, "lo > hi")):
            try:
                stage_keep_of({**_lm35, "stage_keep_range": _bad35}, _n35)
                ng.append(f"T35③: 範囲の外（{_why35}）で止まらない")
            except SampleError:
                pass
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001 の B-1・監査 cp57）＝上端が候補の本数を超えるときは、止めずに候補の本数を使う
        if stage_keep_of({**_lm35, "stage_keep_range": {"lo": 1, "hi": _n35 + 1}}, _n35) != _n35:
            ng.append(f"T35③: 上端が候補の本数（{_n35}）を超えるのに keep が候補の本数でない（B-1）")
        print(f"  T35 stage_keep_range: ①上端 null → keep {_n35}（候補の本数）／②上端 1 → 案0 の記録の keep は 1・案2 は"
              "『上位 1 本の外』で組めない／③範囲の外 2通りは止まり、上端が候補の本数を超えるときは候補の本数")
    except SystemExit as _e35s:
        ng.append(f"T35: 途中で拒否されて止まった: {str(_e35s)[:120]}")
    except Exception as _e35:
        ng.append(f"T35: 途中で止まった: {type(_e35).__name__} {_e35}")

    # ══ T24⑥ 材料の数字が、成績表の列の名前の数字と一致する（手順9・乱数を使わない）═══════════
    #   完成の条件 AUDIT-5＝材料の数字を乱数で引いていないこと。
    try:
        _lm46, _ = load_limits()
        _lm46 = resolve_hold_range(_lm46, "e38")
        _t46 = load_signal_table()
        _p46, _tfs46, _ = material_pool()
        _laws46 = laws_for_scene("range")
        _c46 = build_stage_candidates("stage1", _laws46, _t46, _tfs46, _lm46)
        _ng46 = []
        for _x46 in _c46[:20]:                      # 先頭20件で確かめる（全件だと遅い）
            _m46 = (_x46["cond"].get("material") or [{}])[0]
            _ent46, _pr46 = iref.find(str(_x46["col"]).split("__")[0])
            _want46 = _pr46[0] if _pr46 is not None and len(_pr46) == 1 else (
                tuple(_pr46) if _pr46 is not None else None)
            if str(_m46.get("param")) != str(_want46):
                _ng46.append(f"{_x46['col']}: 材料 {_m46.get('param')} ／ 列 {_want46}")
        if _ng46:
            ng.append(f"T24⑥: 材料の数字が成績表の列の数字と違う: {_ng46[:3]}")
        # ② 2回 作って同じ（乱数を使っていない＝再現できる）
        _c46b = build_stage_candidates("stage1", _laws46, _t46, _tfs46, _lm46)
        if [c["cond"] for c in _c46] != [c["cond"] for c in _c46b]:
            ng.append("T24⑥②: 同じ段を2回 作って中身が違う（乱数が残っている）")
        print(f"  T24⑥ 材料の数字: 先頭20件とも成績表の列の数字と一致 ／ 2回 作って同じ")
    except SystemExit as _e46s:
        ng.append(f"T24⑥: 途中で拒否されて止まった: {str(_e46s)[:120]}")
    except Exception as _e46:
        ng.append(f"T24⑥: 途中で止まった: {type(_e46).__name__} {_e46}")

    # ══ T37b bool_col に未知の鍵を書くと G5 で止まる＝完成の条件 条件9（監査 cp35 の C-2）════════
    try:
        _ok37 = {"not": {"bool_col": "rg5_uptrend", "want": True}}
        _bad37 = {"not": {"bool_col": "rg5_uptrend", "want": True, "role": "env"}}
        _r37 = []
        for _tag37, _cond37 in (("正しい形", _ok37), ("未知の鍵", _bad37)):
            try:
                ex._check_bool_cond(_cond37["not"], "T37b")   # ★実行器の検査の実物（:1069）
                _r37.append((_tag37, "通った"))
            except SystemExit:
                # ★拒否は SystemExit で飛ぶ（Exception を継承しないので except Exception では
                #   捕まらない）。捕まえ損ねると自己テストが丸ごと止まる（2026-09-11 に実測）。
                _r37.append((_tag37, "止まった（G5 の拒否）"))
            except Exception as _e37i:             # noqa: BLE001
                _r37.append((_tag37, f"止まった（{type(_e37i).__name__}）"))
        if _r37[0][1] != "通った":
            ng.append(f"T37b①: 正しい形が通らない（{_r37[0][1]}）")
        if _r37[1][1] == "通った":
            ng.append("T37b②: `bool_col` に未知の鍵を書いても通った（G5 が効いていない）")
        print(f"  T37b bool_col の未知の鍵: 正しい形＝{_r37[0][1]} ／ 未知の鍵＝{_r37[1][1]}")
    except Exception as _e37:
        ng.append(f"T37b: 途中で止まった: {type(_e37).__name__} {_e37}")

    # ══ T38 解決表を束の本数によらず1回だけ作る＝完成の条件 条件10（M2-E-3 の手順3・2026-09-11）══════
    #   設計書の逐語＝「分位の解決表を、束の本数によらず1回だけ作る（束を3本 渡したとき
    #   `build_qtable` の呼び出し回数が 1）」。
    #   ★実データを読まずに測る＝`regime_r9_diag` の中の `_qtable` を数える関数に差し替えて、
    #     束3本を渡したときの呼び出し回数を見る（合成データ・売買は1件も回さない）。
    #   ★壊すプログラム b84_qtable_per_bundle.sh が、束ごとに作り直す形に戻すとこの検査が落ちることを測る。
    try:
        import regime_r9_diag as _r9
        _src38 = pathlib.Path(_r9.__file__).read_text(encoding="utf-8")
        _m38 = _src38[_src38.index("def measure"):]
        _m38 = _m38[:_m38.index("\ndef ")]
        # ① くり返しの中で解決表を作っていないこと（文字で見る＝戻されたら落ちる）
        #   ★注記（# で始まる行）は外してから見る＝直した経緯をコメントに書くと誤報になる
        #     （2026-09-11 に実測＝私が「直す前＝…[rec]…」と書いた注記を拾って落ちた）。
        _code38 = "\n".join(_l.split("#", 1)[0] for _l in _m38.splitlines())
        if "_qtable(df, geo, [rec]" in _code38:
            ng.append("T38①: 束1本ごとに解決表を作り直す形に戻っている（_qtable(df, geo, [rec], …)）")
        if "qt_all = _qtable(df, geo, recipes" not in _code38:
            ng.append("T38①: 束を全部 渡して1回だけ作る形になっていない（qt_all が無い）")
        # ② 呼び出し回数を実際に数える＝_qtable を数える関数に差し替え、束3本で 1回 であること
        _calls38 = []
        _real38 = _r9._qtable

        def _count38(df, geo, recipes, start, end):
            _calls38.append(len(recipes))
            return {}

        _lm38, _ = load_limits()
        _lm38 = resolve_hold_range(_lm38, "e38")
        _p38, _t38, _ = material_pool()
        _recs38 = []
        for _i38 in range(40):
            if len(_recs38) >= 3:
                break
            try:
                _recs38.append(sample_structure(np.random.default_rng([38, _i38]), _lm38, _p38, _t38,
                                                side="SHORT", logic_id=f"T38_{_i38}",
                                                build_regime=True, regime_order_n=_i38))
            except SampleError:
                continue
        if len(_recs38) < 3:
            ng.append(f"T38②: 束が3本 そろわない（{len(_recs38)}本）＝回数を測れない")
        else:
            # ★合成データは、この中で自分で作らない＝`synth_df`（ほかの自己テストが全部 使うもの）を呼ぶ。
            #   ★2026-09-11 に2回 直した。1回目は 600本 の自作で、正解ラベルを作る所（先読み 288本）に
            #     届かなかった。2回目は 1,200本 に増やしたが、帯の線の列（v11_res_hi ほか）が無くて
            #     `KeyError 'v11_res_hi'` で落ちた（実測）。**`synth_df` はその列を全部 持っている。**
            #   ＝自己テスト用のデータを自分で組み立てると、必要な列を取りこぼす。既に在るものを使う。
            _df38 = synth_df(1200, seed=38)
            _why38 = ""
            try:
                _r9._qtable = _count38
                try:
                    _r9.measure(_df38, _recs38, _df38["ts"].iloc[0], _df38["ts"].iloc[-1],
                                with_trades=False)
                except SystemExit as _e38m:
                    _why38 = f"SystemExit {str(_e38m)[:60]}"
                except Exception as _e38m:
                    _why38 = f"{type(_e38m).__name__} {str(_e38m)[:60]}"
            finally:
                _r9._qtable = _real38
            # ★解決表を作る前に別の所で止まると、回数は 0 になる（2026-09-11 に実測＝正解ラベルを
            #   作る所が合成データで落ちた）。そのときは「測れなかった理由」を出す＝黙って通さない。
            if not _calls38:
                ng.append(f"T38②: 解決表を作る所に届かなかった（回数 0）＝止まった理由: {_why38 or '不明'}")
            elif len(_calls38) != 1:
                ng.append(f"T38②: 束3本で解決表を {len(_calls38)} 回 作った（1回であること）"
                          f"／止まった理由: {_why38 or 'なし'}")
            elif _calls38[0] != 3:
                ng.append(f"T38②: 1回で渡した束が {_calls38[0]} 本（3本 まとめて渡すこと）")
        print(f"  T38 解決表のまとめ作り: ①くり返しの外で1回だけ作る形になっている"
              f" ／ ②束3本で呼び出し {len(_calls38)} 回"
              f"（渡した束 {_calls38[0] if _calls38 else '—'} 本）")
    except SystemExit as _e38s:
        ng.append(f"T38: 途中で拒否されて止まった: {str(_e38s)[:120]}")
    except Exception as _e38:
        ng.append(f"T38: 途中で止まった: {type(_e38).__name__} {_e38}")

    # ══ T34 分位を1回でまとめて計算する＝完成の条件 条件7（M2-E-3 の手順2・2026-09-11）══════════════
    #   設計書の逐語＝「分位を1回でまとめて計算していて、1段ずつ計算した結果と一致する（差 1e-12 まで）」。
    #   なぜ要るか＝束1本を測る時間の99%が、ここの計算に行っていた（実測 2.77秒のうち）。
    #   ★壊すプログラム b80_quantile_one_by_one.sh が、1段ずつ呼ぶ形に戻すとこの検査が落ちることを測る。
    try:
        _lm34, _ = load_limits()
        _grid34 = quantile_list(_lm34)
        if len(_grid34) < 2:
            ng.append(f"T34: 分位の格子が 2段 未満（{len(_grid34)}段）＝まとめ計算を測れない")
        # ① 実物の解決表の作り方（build_qtable の中の1行）と、1段ずつ呼ぶ形を突き合わせる。
        #    ★値の並びは「ばらつきのある合成データ」＝欠損・マイナス・同じ値を混ぜる（端の扱いも測る）。
        _rs34 = np.random.default_rng(34)
        _ng34 = 0
        _worst34 = 0.0
        for _i34 in range(16):                 # 16通りの並びで測る（1通りだと偶然 合うことが在る）
            _s34 = _rs34.normal(0.0, 1.0, 500) * float(_rs34.integers(1, 1000))
            if _i34 % 4 == 1:
                _s34 = np.round(_s34)          # 同じ値が並ぶ形
            if _i34 % 4 == 2:
                _s34 = np.abs(_s34)            # 片側だけの形
            if _i34 % 4 == 3:
                _s34 = np.concatenate([_s34, np.full(50, _s34[0])])   # 端に同じ値が集まる形
            _one = {q: float(np.quantile(_s34, int(q.lstrip("q")) / 100.0)) for q in _grid34}
            _ps34 = [int(q.lstrip("q")) / 100.0 for q in _grid34]
            _all = {q: float(v) for q, v in zip(_grid34, np.quantile(_s34, _ps34))}
            for q in _grid34:
                _d34 = abs(_one[q] - _all[q])
                _worst34 = max(_worst34, _d34)
                if _d34 > 1e-12:
                    _ng34 += 1
        if _ng34:
            ng.append(f"T34①: まとめて計算した分位が、1段ずつ計算した値と違う（{_ng34} 件・最大の差 {_worst34:.3e}）")
        # ② 実物のコードが「まとめて計算する形」になっているか（1段ずつ呼ぶ形に戻されたら落ちる）
        _src34 = pathlib.Path(__file__).read_text(encoding="utf-8")
        _qt34 = _src34[_src34.index("def build_qtable"):]
        _qt34 = _qt34[:_qt34.index("\ndef ")]
        if "np.quantile(s, _ps)" not in _qt34:
            ng.append("T34②: 解決表を作る所が、確率の一覧をまとめて渡す形になっていない")
        if "for q in grid}" in _qt34 and "np.quantile(s, int(" in _qt34:
            ng.append("T34②: 解決表を作る所が、1段ずつ呼ぶ形に戻っている")
        print(f"  T34 分位のまとめ計算: ①合成データ16通り × {len(_grid34)}段 で"
              f" 1段ずつ計算した値と一致（最大の差 {_worst34:.3e}／許す差 1e-12）"
              f" ／ ②実物のコードがまとめて渡す形になっている")
    except SystemExit as _e34s:
        ng.append(f"T34: 途中で拒否されて止まった: {str(_e34s)[:120]}")
    except Exception as _e34:
        ng.append(f"T34: 途中で止まった: {type(_e34).__name__} {_e34}")

    # ══ T36 符号を取り去る前処理（abs）＝完成の条件 AUDIT-2（M2-E-3 の手順1・2026-09-11）═══════════
    #   まこさん指示 2026-09-10（逐語）「この件、毎回忘れて、設計に入れないし、やろうとしないから、絶対入れろ」。
    #   なぜ要るか＝DI差・MACDヒスト%・EMA傾き は符号が相場の向きを表す。そのまま「下位◯%より小さい」と
    #   書くと、大きなマイナス（＝強い下げ）まで「弱い」と数える（DI差 −30 は +2 より小さい）。
    #   ★壊すプログラム b82_abs_missing.sh が、前処理を外すとこの検査が落ちることを測る。
    try:
        if "abs" not in ex.MATERIAL_PRE:
            ng.append("T36①: 前処理の一覧に abs が無い")
        if ex.NO_ARG_OPS != ("abs",):
            ng.append(f"T36①: 窓を持たない部品の一覧が ('abs',) でない: {ex.NO_ARG_OPS}")
        # ② まこさんに出した表の3つの値で、実際に折り返るかを測る（+30・−30・+2 → 30・30・2）
        _a36 = np.array([30.0, -30.0, 2.0, np.nan])
        _g36 = ex._apply_pre(_a36, {"op": "abs"})
        if not np.allclose(_g36[:3], [30.0, 30.0, 2.0]) or not np.isnan(_g36[3]):
            ng.append(f"T36②: マイナスの値が正しく折り返らない: {_g36}")
        # ③ 「下位◯%より小さい」で、強い下げが弱いと数えられないこと（算数をそのまま測る）
        if not (abs(-30.0) > abs(2.0)):
            ng.append("T36③: 絶対値にしても −30 が +2 より小さいままになる")
        # ④ 案を作る側が abs に本数（n）を付けないこと（付けると G5 で拒否される）
        if "abs" in ex.pre_ops(same_unit=True, needs_state=False, needs_n=True):
            ng.append("T36④: 窓を持つ部品だけの絞りに abs が混ざる（n を付けた案を作ってしまう）")
        if "abs" not in ex.pre_ops(same_unit=True, needs_state=False):
            ng.append("T36④: 既定の絞りから abs が落ちている（今までの呼び出しの動きが変わった）")
        # ⑤ n・state を書くと G5 で止まり、書かなければ通ること
        #   ★検査の本体＝`_material_name`（材料の名前を組み立てる途中で pre の形を見る）。
        #   ★材料は `_mat_fixture` で作る＝材料の辞書を手で書かない決まり（K1・--lint-provenance が見張る）。
        #     直す前は `{"family": "DI差", "param": 21, "tf": "1d", …}` を直接 書いて、T25 が2件 拾った。
        #   ★拒否は `SystemExit` で飛ぶ（`_fail` の作り）。`SystemExit` は `Exception` を継承しないので、
        #     `except Exception` だけでは捕まらず、自己テストが丸ごと止まる（2026-09-11 に実測して直した）。
        for _bad36 in ({"op": "abs", "n": 20}, {"op": "abs", "state": "range_ok_build"}):
            try:
                ex._material_name(_mat_fixture("DI差", 21, "1d", pre=_bad36), "")
                ng.append(f"T36⑤: {_bad36} で止まらない（窓を持たない部品に本数・状態は書けない）")
            except SystemExit:
                pass
            except Exception:
                pass
        try:
            ex._material_name(_mat_fixture("DI差", 21, "1d", pre={"op": "abs"}), "")
        except SystemExit as _e36a:
            ng.append(f"T36⑤: 正しい形 {{'op': 'abs'}} が拒否された: {str(_e36a)[:80]}")
        except Exception as _e36b:
            ng.append(f"T36⑤: 正しい形 {{'op': 'abs'}} が通らない: "
                      f"{type(_e36b).__name__} {str(_e36b)[:80]}")
        print(f"  T36 符号を取り去る前処理: ①一覧に在る（窓を持たない部品＝{ex.NO_ARG_OPS}）"
              f" ／ ②+30・−30・+2 → {list(_g36[:3])}（欠損は欠損のまま）"
              f" ／ ④案を作る側の絞りから外れている ／ ⑤n・state を書くと止まる・書かなければ通る")
    except SystemExit as _e36s:
        # ★`SystemExit` は `Exception` を継承しない＝下の except では捕まらない。
        #   これを書かないと、T36 の中の拒否で自己テストが丸ごと止まる（2026-09-11 に実測）。
        ng.append(f"T36: 途中で拒否されて止まった: {str(_e36s)[:120]}")
    except Exception as _e36:
        ng.append(f"T36: 途中で止まった: {type(_e36).__name__} {_e36}")

    # ══ T47 動く線（M2-E-4e・2026-09-27）＝BB幅 が直近6か月の範囲の下の方に在るかを、段2c の候補に足す ══════
    #   ①部品 ts_pos が一覧に在り、入口の案を乱数で作る道の一覧（gen_draw=True）には入らない（恒久67番）
    #   ②既知答え＝直近5本の最小〜最大の中の位置（いまのバーを含める・幅0は値なし）
    #   ③6か月が5分足 52596本。段2c の候補に、BB幅 の固定の線と同じ本数の動く線が在り、
    #     材料は ts_pos・窓 52596本で、固定の線の後ろに並ぶ（固定の線の順位を変えない）
    #   ⑤動く線を使う走行（本走）の余白が「いまの余白＋6か月」（まこさん決定「余白の直し方→C」）
    #   ★壊すプログラム b109（動く線を作らない）・b110（乱数の道に入れる）・b111（いまのバーを外す）・b112（余白を延ばさない）がこの検査を測る。
    try:
        _ng47: list[str] = []
        if "ts_pos" not in ex.MATERIAL_PRE:
            _ng47.append("①前処理の一覧に ts_pos が無い")
        if "ts_pos" in ex.pre_ops(same_unit=False, gen_draw=True):
            _ng47.append("①入口の案を乱数で作る道の一覧に ts_pos が入っている")
        if "ts_pos" not in ex.pre_ops(same_unit=False):
            _ng47.append("①既定の一覧から ts_pos が落ちた")
        _a47 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 3.0, 3.0, 3.0, 3.0, 3.0])
        _g47 = ex._apply_pre(_a47, {"op": "ts_pos", "n": 5})
        _w47 = np.array([np.nan] * 4 + [1.0, 1.0 / 3.0, 0.0, 0.0, 0.0, np.nan])
        if not np.allclose(_g47, _w47, equal_nan=True):
            _ng47.append(f"②既知答えと違う: {list(np.round(_g47, 4))}（期待 {list(np.round(_w47, 4))}）")
        if not np.allclose(ex._apply_pre(_a47[:-1], {"op": "ts_pos", "n": 5}), _g47[:-1], equal_nan=True):
            _ng47.append("②最後の1本を落とすと、その前の値が変わる（未来のバーを見ている）")
        if pre_win_bars({"op": "ts_pos", "months": 6}) != 52596:
            _ng47.append(f"③6か月が5分足 52596本にならない: {pre_win_bars({'op': 'ts_pos', 'months': 6})}")
        _lm47, _ = load_limits()
        _lm47 = resolve_hold_range(_lm47, "e38")
        _c47 = build_stage_candidates("stage2c", laws_for_scene("range"), load_signal_table(),
                                      material_pool()[1], _lm47)
        _mv47 = [c for c in _c47 if c.get("pre_win")]
        _fx47 = [c for c in _c47 if not c.get("pre_win")]
        _bb47 = [c for c in _fx47 if c.get("family") == "BB幅"]
        if not _mv47:
            _ng47.append("③段2c の候補に動く線が1本も無い")
        if len(_mv47) != len(_bb47):
            _ng47.append(f"③動く線 {len(_mv47)} 本が、BB幅 の固定の線 {len(_bb47)} 本と合わない")
        for c in _mv47:
            _in47 = c["cond"]["not"] if "not" in c["cond"] else c["cond"]
            if c.get("family") != "BB幅" or _in47["material"][0].get("pre") != {"op": "ts_pos", "n": 52596}:
                _ng47.append(f"③動く線の材料が違う: {c.get('col')} {_in47['material'][0].get('pre')}")
                break
        if _mv47 and _fx47 and min(i for i, c in enumerate(_c47) if c.get("pre_win")) <= max(i for i, c in enumerate(_c47) if not c.get("pre_win")):
            _ng47.append("③動く線が固定の線の後ろに並んでいない（固定の線の順位が変わる）")
        _wm47 = stage_warm(pd.Timedelta(days=60))
        if _wm47 != pd.Timedelta(days=60) + pd.Timedelta(minutes=52596 * 5):
            _ng47.append(f"⑤動く線を使う走行の余白が 60日＋6か月にならない: {_wm47}")
        _src47 = pathlib.Path(__file__).read_text(encoding="utf-8")
        _rm47 = _src47[_src47.index("\ndef run_main") + 1:]
        _rm47 = _rm47[:_rm47.index("\ndef ")]
        if ("_warm, use_cache=not a.no_cache)" not in _rm47 or "_warm = stage_warm(et.WARM) if a.build_regime else et.WARM" not in _rm47):
            _ng47.append("⑤本走（run_main）が --build-regime のときだけ stage_warm の余白でデータを読む形になっていない")
        ng += [f"T47: {x}" for x in _ng47]
        print(f"  T47 動く線: ①ts_pos は乱数の道の外 ／ ②既知答え ／ ③段2c の動く線 {len(_mv47)} 本"
              f"（BB幅 の固定の線 {len(_bb47)} 本・窓 5分足 52596本・固定の線の後ろ）／ ⑤余白 {_wm47}"
              + ("＝通った" if not _ng47 else "＝落ちた"))
    except SystemExit as _e47s:
        ng.append(f"T47: 途中で拒否されて止まった: {str(_e47s)[:120]}")
    except Exception as _e47:
        ng.append(f"T47: 途中で止まった: {type(_e47).__name__} {_e47}")

    # ══ T25 静的検査（K1〜K3・59回目・設計書 v2）＝引く関数の外で材料・閾値・数字を作っている所が 0件 ══
    try:
        if lint_provenance(verbose=True) != 0:
            ng.append("T25: --lint-provenance が不合格（引く関数の外で材料・印・draw_* を書いている所が在る）")
    except Exception as _e25:
        ng.append(f"T25: 静的検査が走らない: {type(_e25).__name__} {_e25}")

    # ══ T26 18マスを機械が壊す（K4・K5・K7・K8・K14）＝壊し方はプログラムの中の表（gate_matrix）が正本 ══
    try:
        if gate_matrix(verbose=True) != 0:
            ng.append("T26: --gate-matrix が不合格（止まるはずのマスが止まらない・または正しい案が通らない）")
    except Exception as _e26:
        ng.append(f"T26: 18マスの検査が走らない: {type(_e26).__name__} {_e26}")

    # ══ T27 保存した案の出どころを後から数え直す（K9）＝印つきの案 3本 → 違反0 ／ 1本の数字を範囲の外へ → 違反1 ══
    try:
        import tempfile as _tf27
        _lm27, _w27 = load_limits()
        _lm27 = resolve_hold_range(_lm27, "e38")
        _p27, _t27, _ = material_pool()
        _s27 = []
        for _i in range(60):
            if len(_s27) >= 3:
                break
            try:
                _s27.append(sample_structure(np.random.default_rng([27, 1, _i]), _lm27, _p27, _t27, logic_id=f"T27_{_i}"))
            except SampleError:
                continue
        with _tf27.TemporaryDirectory() as _d27:
            _f27 = pathlib.Path(_d27) / "structures_marked.json"
            _f27.write_text(json.dumps({"structures": _s27}, ensure_ascii=False) + "\n", encoding="utf-8")
            _ok27 = verify_provenance(str(_f27))
            _b27 = json.loads(json.dumps(_s27))
            _cs27, _ = ex._walk(_b27[0]["entry"]["connective"])
            _hit27 = False
            for _c in _cs27:
                for _m in (_c.get("material") or []):
                    if isinstance(_m, dict) and "family" in _m:
                        _m["param"] = 999999
                        _hit27 = True
                        break
                if _hit27:
                    break
            _f27.write_text(json.dumps({"structures": _b27}, ensure_ascii=False) + "\n", encoding="utf-8")
            _ng27 = verify_provenance(str(_f27))
        if len(_s27) < 3 or _ok27 != 0:
            ng.append(f"T27: 保存した正しい案 {len(_s27)} 本の再判定が違反0でない（戻り={_ok27}）")
        if _ng27 == 0:
            ng.append("T27 メタ確認: 1本の数字を範囲の外に書き換えた控えが違反0のまま通る（再判定が効いていない）")
    except Exception as _e27:
        ng.append(f"T27: 再判定の検査が走らない: {type(_e27).__name__} {_e27}")

    # ── T28 減らしたい損失（要件 R8・2026-08-26 新設）────────────────────────────────────
    #   ★何を守るか＝「この決済した理由の損を減らして」と指示できること、その損の額が審判の値と
    #     一致すること、名前の打ち間違いと再開の食い違いで止まること、指定が無ければ何も変わらないこと。
    #   ★メタ確認＝絞りを外すと値が変わること（＝本当に絞っている）／正しい名前は止めないこと（止めすぎない）。
    t28: list[str] = []
    try:
        class _J28:                      # 審判の代わり（合成データ・net の欄を足すだけ）
            @staticmethod
            def score(df):
                return {"total": float(df["net"].sum())}

        _t28 = pd.DataFrame({"exit_reason": ["TIME_EXIT", "TP_FILLED", "TIME_EXIT"],
                             "net": [-10.0, 5.0, -3.0]})
        # ① 絞った合計が、審判に通した値と一致する
        _f28, _n28 = _focus_net(_t28, _J28, "TIME_EXIT")
        if not (abs(_f28 - (-13.0)) < 1e-9 and _n28 == 2):
            t28.append(f"絞った損の額が合わない（{_f28} / {_n28}玉・期待 -13.0 / 2玉）")
        # ①メタ確認＝絞らずに全部 足すと別の値になる（＝本当に絞っている）
        if abs(float(_t28["net"].sum()) - _f28) < 1e-9:
            t28.append("メタ確認: 絞っても絞らなくても同じ値＝絞りが効いていない")
        # ② その理由が1本も無ければ 0.0 / 0玉（＝全部の案が同点に見える状態を、呼ぶ側が警告できる）
        if _focus_net(_t28, _J28, "SL_FILLED") != (0.0, 0):
            t28.append("売買記録に無い理由で 0.0/0玉 を返さない")
        # ③ 指定が無ければ 0.0 / 0玉（恒等＝目的は合計 net のまま）
        if _focus_net(_t28, _J28, None) != (0.0, 0):
            t28.append("指定が無いのに損の額を作っている（恒等が壊れる）")
        # ④ 目的の値の切り替え（指定時＝損の額 ／ 指定なし＝合計 net）
        _rec28 = {"total": 5.0, "focus": -13.0}
        if _obj_key(_rec28, "TIME_EXIT") != -13.0:
            t28.append("指定時に目的の値が損の額になっていない")
        if _obj_key(_rec28, None) != 5.0:
            t28.append("指定なしのときに目的の値が合計 net でない（恒等が壊れる）")
        # ⑤ 審判が知らない名前は、走らせる前に止める（fail-closed）
        try:
            assert_known_exit_reason("NO_SUCH_EXIT_REASON")
            t28.append("審判が知らない決済の理由で止まらない")
        except SystemExit:
            pass
        # ⑤メタ確認＝正しい名前と指定なしは止めない（止めすぎない）
        for _ok28 in ("TIME_EXIT", None):
            try:
                assert_known_exit_reason(_ok28)
            except SystemExit:
                t28.append(f"メタ確認: 止めてはいけないもので止まった（{_ok28}）")
        # ⑥ 再開の記録と指定が食い違えば止まる（R12 の meta の食い違い＝目的の入れ替わりを防ぐ）
        with tempfile.TemporaryDirectory() as _d28:
            _jp28 = pathlib.Path(_d28) / "journal.jsonl"
            Journal(_jp28, {"seed": 1})                      # 指定なしで作る
            try:
                Journal(_jp28, {"seed": 1, "minimize": "TIME_EXIT"})   # 指定つきで再開
                t28.append("再開のときに指定の食い違いで止まらない")
            except SystemExit:
                pass
            Journal(_jp28, {"seed": 1})                      # 同じ指定なら通る（止めすぎない）
    except Exception as _e28:
        t28.append(f"検査が走らない: {type(_e28).__name__} {_e28}")
    ng += [f"T28: {x}" for x in t28]
    print("  T28 減らしたい損失（R8）: 絞った損の額が審判の値と一致（絞りを外すと変わる＝メタ確認）／"
          "売買記録に無い理由と指定なしは 0.0/0玉（恒等）／目的の値の切り替え／"
          "審判が知らない名前は止め、正しい名前と指定なしは止めない／再開の指定の食い違いで止まる")
    print(f"  T29 減らしたい損失の実走（R8）: 小さい本走で目的が入れ替わる（{_t29_note}）／"
          "記録の1本1本に損の額が入る／再開の記録に指定が残る／"
          "★メタ確認＝指定なしなら画面も記録も直す前のまま（恒等）")

    # ══ T30〜T32 外から呼ぶ道と、使えない組（69回目・2026-08-27・承認 d7448952c357c306…・原因A・原因B）══════
    #   T30 外の道＝案を作るプログラムが返した案（印つき）を、実行器の検査に直に渡すと止まり、validate_drawn なら通る
    #   T31 呼び出し元の走査＝sample_structure を呼ぶ .py で validate_recipe を直に呼ぶ所が 0件（一覧は機械で集める）
    #       ＋わざと直に呼ぶ写しを走査すると 1件 出る（走査が本物であるメタ確認）
    #   T32 使えない組＝範囲のどの数字でも禁止3 の組は順位に数えない／禁止3 を外すと直す前の1位に戻る（メタ確認）／
    #       種を変えても同じ組（乱数に依らない）
    t3x: list[str] = []
    try:
        _tbl30 = load_signal_table()
        _pool30, _tfs30, _ = material_pool()
        _lm30, _w30 = load_limits()
        _lm30 = resolve_hold_range(_lm30, "e38")
        _lim30 = {"n_min": None, "p_max": _lm30.get("p_max"), "count_range": _lm30.get("count_range"),
                  "role_max": _lm30.get("role_max"), "depth_max": _lm30.get("depth_max"),
                  "k_max": _lm30.get("k_max"), "r_min": _lm30.get("r_min")}
        _rr30 = None
        for _i in range(20):
            try:
                _cand = sample_structure(np.random.default_rng([30, 1, _i]), _lm30, _pool30, _tfs30, side="SHORT",
                                         logic_id=f"T30_{_i}", build_regime=True, regime_order_n=_i)
                validate_drawn(_cand, limits=_lim30)
                _rr30 = _cand
                break
            except (SampleError, ex.RecipeError):
                continue
        if _rr30 is None:
            t3x.append("T30: 場面の判定の束つきの案が、包み（validate_drawn）で1本も通らない（20本 試した）")
        else:
            try:
                # ★わざと印を外さずに直に渡す（getattr 経由＝番人 T31 の走査の対象にしないため）
                getattr(ex, "validate_recipe")(_rr30, limits=_lim30)
                t3x.append("T30-a: 印つきの案を実行器の検査に直に渡しても止まらない（印が外れている？＝C-7 が崩れている）")
            except ex.RecipeError as _e30:
                if "_src" not in str(_e30):
                    t3x.append(f"T30-a: 直に渡すと止まるが、理由が印ではない: {str(_e30)[:80]}")
        # T31
        _scan_dirs = [HERE, HERE.parent / "dashboard"]
        _hits31 = _scan_direct_validate_calls(sorted(p for d in _scan_dirs for p in d.glob("*.py")))
        if _hits31:
            t3x.append("T31-a: 印を外さずに検査を直に呼ぶ所: " + " ／ ".join(_hits31[:6]))
        with tempfile.TemporaryDirectory() as _td:
            _bad31 = pathlib.Path(_td) / "bad_caller.py"
            _bad31.write_text("import engine_tuner_gen as g\nimport engine_tuner_exec as ex\n"
                              "r = g.sample_structure(None, {}, [], [], build_regime=True)\n"
                              "ex.validate_recipe(r, limits={})\n", encoding="utf-8")
            _good31 = pathlib.Path(_td) / "good_caller.py"
            _good31.write_text("import engine_tuner_gen as g\n"
                               "r = g.sample_structure(None, {}, [], [], build_regime=True)\n"
                               "g.validate_drawn(r, limits={})\n", encoding="utf-8")
            if len(_scan_direct_validate_calls([_bad31])) != 1:
                t3x.append("T31-b: わざと直に呼ぶ写しを走査しても 1件 出ない（走査が本物でない）")
            if _scan_direct_validate_calls([_good31]):
                t3x.append("T31-b: 包みで呼ぶ写しが誤って引っかかる")
        # T32
        _tfs_all32 = list(_tbl30["tfs"])
        _upper32 = [t for t in _tfs_all32 if _tfs_all32.index(t) > _tfs_all32.index("5m")]
        _tfok32 = [t for t in _role_tfs(_tfs30, _tbl30, "env") if t in _upper32]
        _ok32 = set(_tfok32)
        _rr32 = _tbl30["roles"]["env"]
        _ranges32 = material_ranges()
        _first32 = None                                   # 直す前の1位（型の表・時間足・系統だけで数えた最初の組）
        for _fam, _tf, _lab, _hor, _med, _ncol, _col in ranked_groups("env", "強さ"):
            if _tf not in _ok32 or _fam not in iref.FAMILY_LINEAGE or _fam not in _ranges32:
                continue
            if iref.FAMILY_LINEAGE[_fam]["k"] not in _rr32["lineages"]:
                continue
            _first32 = (_fam, _tf)
            break
        _m32, _d32 = _ranked_material_at("env", 1, _tfs30, _tbl30, label="強さ", tf_ok=_tfok32)
        if not _group_usable(_d32["種類"], _d32["時間足"], _ranges32, _tbl30):
            t3x.append(f"T32-a: 1位に「範囲のどの数字でも禁止3」の組が残っている: {_d32['種類']}×{_d32['時間足']}")
        if _banned_pair(_m32, _tbl30):
            t3x.append(f"T32-a: 1位から引いた数字が禁止3: {_m32}")
        if str(_d32["種類"]).startswith("stdev"):
            t3x.append(f"T32-a: 1位が直す前と同じ stdev%×1d のまま（68回目の実測＝0/200 の組）: {_d32}")
        if _first32 is not None and _group_usable(_first32[0], _first32[1], _ranges32, _tbl30):
            print(f"  T32 注記: 直す前の1位の組 {_first32} は使える組（成績表を作り直したなら見本を見直す）")
        # (b) メタ確認＝禁止3 を「全部 使える」に差し替えると、直す前の1位に戻る
        _keep_bp = globals()["_banned_name"]
        _keep_memo = dict(_GROUP_USABLE_MEMO)
        try:
            globals()["_banned_name"] = lambda name, tf, table: False
            _GROUP_USABLE_MEMO.clear()
            _m32b, _d32b = _ranked_material_at("env", 1, _tfs30, _tbl30, label="強さ", tf_ok=_tfok32)
            if _first32 is not None and (_d32b["種類"], _d32b["時間足"]) != _first32:
                t3x.append(f"T32-b: 禁止3 を外しても直す前の1位に戻らない: {(_d32b['種類'], _d32b['時間足'])} ≠ {_first32}")
        finally:
            globals()["_banned_name"] = _keep_bp
            _GROUP_USABLE_MEMO.clear()
            _GROUP_USABLE_MEMO.update(_keep_memo)
        # (c) 乱数に依らない
        _m32c, _d32c = _ranked_material_at("env", 1, _tfs30, _tbl30, label="強さ", tf_ok=_tfok32)
        if (_d32c["種類"], _d32c["時間足"]) != (_d32["種類"], _d32["時間足"]):
            t3x.append("T32-c: 種を変えると1位の組が変わる（乱数に依っている）")
        print(f"  T32 実測: env「強さ」の1位＝{_d32['種類']}×{_d32['時間足']}（直す前の1位＝{_first32}）"
              f" ／ 走査した組 {len(_GROUP_USABLE_MEMO)} 件")
    except Exception as _e3x:
        t3x.append(f"T30〜T32: 検査が走らない: {type(_e3x).__name__} {_e3x}")
    ng += t3x
    print("  T30 外の道: 印つきの案を実行器の検査に直に渡すと止まる／包み validate_drawn なら通る")
    print("  T31 呼び出し元の走査: sample_structure を呼ぶ .py で validate_recipe を直に呼ぶ所 0件／わざと直に呼ぶ写しは 1件 出る")
    print("  T32 使えない組: 範囲のどの数字でも禁止3 の組は順位に数えない／禁止3 を外すと直す前の1位に戻る／種を変えても同じ組")

    # ══ T33 指標のオン・オフの印（M2-C-2・設計書 iter="indicator-switch-20260902"）══════════
    #   確かめ方＝設計書 §5 の7つのうち、生成器で試せる5つ（残り2つ＝恒等3本の md5／印を手で
    #   書き換えたら検出、は それぞれ --identity と gen_indicator_switch.py --verify が持つ）。
    t33: list[str] = []
    try:
        _sw = ex.load_indicator_switch()
        _on, _off = list(_sw["on"]), list(_sw["off"])
        if not _off:
            t33.append("T33: 「使わない」が0件＝この検査が何も試せない（印が効いていない）")
        else:
            # (a) 「使わない」の指標は、案を作るときの候補に1件も出ない
            _pool, _tf33, _tot33 = material_pool()
            _leak = sorted({b["family"] for b in _pool} & set(_off))
            if _leak:
                t33.append(f"T33-a: 「使わない」の指標が候補に出た: {_leak[:5]}")
            # (b) 「使わない」の指標を使った案は、審査が捨てる
            _bad33 = {"role": "trigger", "form": "level", "side": "above",
                      "material": [_mat_fixture(_off[0], None, "5m", off_ok=True)],
                      "value": {"threshold_q": 0.7}}
            try:
                assert_provenance(_bad33, where="T33")
                t33.append(f"T33-b: 「使わない」の指標 {_off[0]} を使った案を審査が通した")
            except SampleError as _e33:
                if "印が「使わない」" not in str(_e33):
                    t33.append(f"T33-b: 止まったが理由が印ではない: {str(_e33)[:60]}")
            # (c) 「使う」に戻すと通る＝印を戻せば元に戻る（片道でない）
            _keep33 = set(_sw["_on_set"])
            try:
                _sw["_on_set"].add(_off[0])
                try:
                    assert_provenance(_bad33, where="T33")
                except SampleError as _e33c:
                    if "印が「使わない」" in str(_e33c):
                        t33.append(f"T33-c: 「使う」に戻しても印で止まる（片道になっている）")
            finally:
                _sw["_on_set"] = _keep33
            # (f) 「使う」指標に off_ok=True を渡すと止まる＝off_ok が範囲の検査を飛ばす道にならない
            #     ★恒久のテスト（まこさんの条件 2026-09-04・設計書 iter="t25-fixture-off-20260904"）
            #       ＝この fail-closed を機械で守るのは、ここだけ（SPEC は下線で始まる _mat_fixture を見ない・
            #         must_use は申告）。止まらなければ t33 に入り、ng に加算されて --selftest が ❌ になる。
            try:
                _mat_fixture(_on[0], None, "5m", off_ok=True)
                t33.append(f"T33-f: 「使う」指標 {_on[0]} に off_ok=True を渡しても止まらない（fail-closed が崩れている）")
            except SampleError as _e33f:
                print(f"  T33-f 実測: SampleError: {_e33f}")
                if "off_ok" not in str(_e33f):
                    t33.append(f"T33-f: 止まったが理由が off_ok ではない: {str(_e33f)[:60]}")
            # (d) 順位の表からも「使わない」の指標が外れる
            try:
                _rk = ranked_materials("env")
                _leak_d = sorted({str(c).rsplit("__", 1)[0] for c, _a, _l, _h in _rk} & set(_off))
                if _leak_d:
                    t33.append(f"T33-d: 「使わない」の指標が順位に残った: {_leak_d[:5]}")
            except SystemExit:
                pass                                  # 成績表がまだ無い環境＝この枝は試さない
            # (g) 別枠3種（レンジ幾何・需給・時間帯）の審査も、印を見ているか
            #   ★2026-09-07（監査 cp25 の §5-2・Major・設計書 C）に足した。
            #     直す前＝テストの枝は7つで、**7つとも指標（family）を試していた**。
            #     2026-09-06 に新しく作った審査の枝3本（assert_provenance の中の
            #     レンジ幾何・需給・時間帯）を試す枝が **0件** だった＝明日その3枝が消えても、
            #     誰も気づかない。
            #   ★壊すプログラム b33 では代わりにならない（監査 cp25 の §5-2 の実測）＝
            #     b33 が測るのは候補の側（--count-extra-candidates）だけで、審査の3枝を消しても
            #     同じ結果を返す。だから審査の側を直に呼ぶ枝が要る。
            #   ★形は T33-b・T33-c と同じ＝①オンなら通す ②オフなら止める ③戻せば通る。
            #   ★中身は `_selftest_extra_gate()` の1本に置いた（2026-09-07）＝`--selftest` の全体は
            #     6分23秒 かかり、承認のときの打ち切り（120秒）を超えて壊れたまま残ったため、
            #     この枝だけを数秒で走らせる口 `--selftest-extra-gate` を作った。
            #     selftest と その口が同じ1本を呼ぶ＝同じ判定を2か所に書き写さない。
            t33 += [f"T33-g: {_x33}" for _x33 in _selftest_extra_gate()]
            # (e) 印の指紋が走行の記録の meta に入る＝切り替えたまま再開すると止まる
            #   ★2026-09-06（監査 cp24 の §6-8・Major・設計書 E）＝**わざと食い違わせて試す**形にした。
            #     直す前＝「指紋が空でないこと」しか見ておらず、**本当に止まるかを1度も試していなかった**
            #     （監査の逐語＝「ハッシュ値が空でないことしか見ていない。わざと食い違うハッシュ値で
            #       再開して、本当に止まるかを1度も試していません」）。
            #     直した後＝走行の記録（journal）を一時の場所に作り、印の指紋だけを違う値にした
            #     `meta` でもう一度 開いて、`SystemExit` が出ることを確かめる。
            _fp33 = ex.indicator_switch_fingerprint()
            if not _fp33:
                t33.append("T33-e: 印の指紋が空（走行の再開の食い違いを検出できない）")
            else:
                import tempfile as _tf33
                with _tf33.TemporaryDirectory() as _d33:
                    _p33 = pathlib.Path(_d33) / "journal.jsonl"
                    _meta33 = {"seed": 0, "indicator_switch": _fp33}
                    Journal(_p33, dict(_meta33))                 # 1回目＝記録を作る
                    try:
                        Journal(_p33, {**_meta33, "indicator_switch": _fp33 + "x"})
                        t33.append("T33-e: 印の指紋を変えて再開しても止まらない"
                                   "（前半と後半で使える指標が違う1本の走行になる）")
                    except SystemExit:
                        pass                                     # 期待どおり止まった
                    try:
                        Journal(_p33, dict(_meta33))             # 同じ印なら続けられる（止めすぎない）
                    except SystemExit:
                        t33.append("T33-e: 印が同じなのに再開できない（止めすぎ）")
        print(f"  T33 実測: 使う {len(_on)} 種／使わない {len(_off)} 種"
              f"／候補に出た種類 {len({b['family'] for b in material_pool()[0]})} 種"
              f"／印の指紋 {ex.indicator_switch_fingerprint()}")
    except Exception as _e33x:                        # noqa: BLE001
        t33.append(f"T33: 検査が走らない: {type(_e33x).__name__} {_e33x}")
    ng += t33
    print("  T33 指標のオン・オフの印: (a)候補に出ない (b)審査が捨てる (c)戻せば通る"
          " (d)順位から外れる (e)指紋が記録に入る (f)「使う」指標に off_ok は作れない")
    ng += [f"T23-demand: {_x}" for _x in selftest_rank_demand()]   # 需給の列を順位から読む（設計書 demand-in-ranking-20260907）

    # ══ T43 設定の欄 `stage_limits` が読まれている（監査 cp36 の M-1・設計書の完成の条件 AUDIT-2）═══
    #   測り方＝本物の設定に写しを重ねて、候補の一覧と、組まれた束が変わるかを見る。
    #   ★本物の設定ファイルは1文字も触らない（写しを `load_limits` の戻りに重ねるだけ）。
    t43: list[str] = []
    try:
        _lm43, _ = load_limits()
        _lm43 = resolve_hold_range(_lm43, "e38")
        _t43 = load_signal_table()
        _p43, _tfs43, _ = material_pool()
        _laws43 = laws_for_scene("range")

        def _cands43(over: dict, stage: str = "stage1"):
            return build_stage_candidates(stage, _laws43, _t43, _tfs43, {**_lm43, **over})

        # ① 段1 の時間足を1本に絞ると、候補がその時間足だけになる
        _base43 = _cands43({})
        _one43 = sorted({c["tf"] for c in _base43})[0]
        _c43 = _cands43({"stage_limits": {"stage1": {"tfs": [_one43]}}})
        _got43 = sorted({c["tf"] for c in _c43})
        if _got43 != [_one43]:
            t43.append(f"T43①: 段1 の tfs を {_one43} 1本にしても候補の時間足が {_got43}")
        # ② 知らない鍵・範囲の外の時間足・範囲の外の分位は止まる
        for _bad43, _why43 in (({"stage1": {"bogus": 1}}, "知らない鍵"),
                               ({"stage1": {"tfs": ["9m"]}}, "時間足の表に無い名前"),
                               ({"stage1": {"quantiles": ["q99"]}}, "範囲の外の分位"),
                               ({"bogus_stage": {"tfs": ["1h"]}}, "知らない段"),
                               ({"stage2b": {"tfs": ["1h"]}}, "書けない段")):
            try:
                _cands43({"stage_limits": _bad43})
                t43.append(f"T43②: {_why43} を書いても止まらない: {_bad43}")
            except SampleError:
                pass
        # ③ quantiles を2つ書くと候補が2倍
        _q43 = _cands43({"stage_limits": {"stage1": {"quantiles": ["q30", "q50"]}}})
        if len(_q43) != len(_base43) * 2:
            t43.append(f"T43③: quantiles 2つで候補が {len(_q43)} 本（2倍＝{len(_base43) * 2} 本 のはず）")
        # ④ `drop_tfs` を空の配列にすると 10分足が候補に出る（既定の3本に戻らない）
        _d43 = _cands43({"drop_tfs": []}, "stage2c")
        if "10m" not in {c["tf"] for c in _d43}:
            t43.append("T43④: drop_tfs を空の配列にしても 10分足が候補に出ない（既定へ戻っている）")
        # ⑤ 同じ設定を渡した束の B の時間足が、その設定で作った一覧の中だけから来る
        _b43, _dr43 = sample_regime_build({**_lm43, "stage_limits": {"stage1": {"tfs": [_one43]}}},
                                          _p43, _tfs43, _t43, order_n=0)
        _btf43 = str((_dr43.get("B") or {}).get("col") or "").split("__")[-1]
        if _btf43 != _one43:
            t43.append(f"T43⑤: 段1 を {_one43} 1本にしたのに、束の B の時間足が {_btf43}")
    except (SampleError, SystemExit, KeyError, IndexError) as _e43:
        t43.append(f"T43: 検査が走らない: {type(_e43).__name__} {str(_e43)[:80]}")
    ng += t43
    print("  T43 設定の欄 stage_limits: ①時間足1本で候補もその1本 ②知らない鍵・範囲の外・書けない段は止まる"
          " ③分位2つで候補2倍 ④drop_tfs の空の配列は「外さない」 ⑤束の B もその時間足")

    # ══ T44 は selftest_stage_q へ移した（2026-10-03・工事 m2f-stage-quantile-rank-20261003）＝下の T48 の後で T49 と一緒に呼ぶ ═══

    # ══ T45 帯の幅の枠が、法則が名指しした指標も読む（2026-09-19・設計書 m2c-width-…-20260918）═══
    #   ①帯の幅の候補に、法則 R7 の指標が全部 出る（印がオンのもの）
    #   ②帯の幅に指標を選んだ束が、審査 G7 を通る（法則 R2 でも R6 でも落ちない）
    #   ★①が落ちる＝組む側が法則の family を読まなくなった（壊すプログラム b87 が測る相手）
    #   ★②が落ちる＝法則 R2 の「除く部品」が効かなくなった（b88 が測る相手）
    t45: list[str] = []
    try:
        import engine_tuner_exec as _ex45
        _lm45, _ = load_limits()
        _lm45 = resolve_hold_range(_lm45, "e38")
        _t45 = load_signal_table()
        _p45, _tfs45, _ = material_pool()
        _laws45 = laws_for_scene("range")
        _c45 = build_width_candidates(_laws45, _t45, _tfs45, _lm45)
        _fam45 = {x["family"] for x in _c45 if x["family"]}
        _want45, _ = _law_families(_laws45, stage_candidates("stage1")["law_width"])
        _miss45 = sorted({f for f in (_want45 or ()) if _ex45.indicator_enabled(f)} - _fam45)
        if _miss45:
            t45.append(f"T45: 帯の幅の候補に、法則が名指しし印もオンの指標が出ない: {_miss45[:5]}")
        # ② 指標を選んだ束が審査を通るか＝その順位を指す案の番号を探して1本 組む
        _rk45 = next((x["rank"] for x in _c45 if x["family"]), None)
        if _rk45 is None:
            t45.append("T45: 帯の幅の候補に指標が1本も無い＝②を測れない（嘘の合格を出さない）")
        else:
            _ok45 = False
            for _i45 in range(40):
                if regime_draw_order(_i45)[0] != _rk45:
                    continue
                _b45, _d45 = sample_regime_build(_lm45, _p45, _tfs45, _t45, order_n=_i45)
                _ex45._check_scene_rules({"name": "range", "build": _b45}, "entry")
                _ok45 = True
                break
            if not _ok45:
                t45.append(f"T45: 帯の幅に指標（順位 {_rk45}）を選ぶ案の番号が 40 本の中に無い＝②を測れない")
    except (SystemExit, Exception) as _e45:         # noqa: BLE001  G7 で落ちるのが、直す前の状態（★監査 CP39＝RecipeError は SystemExit の子。受けないと自己テストが ❌ の一覧を出す前に止まり、壊すプログラム b77・b99 の EXPECT_MSG が出ない）
        t45.append(f"T45: 帯の幅の枠が動かない: {type(_e45).__name__} {str(_e45)[:120]}")
    ng += t45
    print("  T45 帯の幅の枠: ①法則が名指しし印もオンの指標が候補に出る ②その指標を選んだ束が審査 G7 を通る")

    # ══ T46 持続の内側が成立の全体（M2-E-4d・束1・2026-09-25）＝完成の条件 #1 ═══════════════════
    #   ①入る条件が持続1つ ②その内側が条件の束 ③内側の本数が引いた記録と一致
    #   ④内側の並びが A・B・C・(D)・(G)（形＝level・level・not・…）で、持続が内側に無い
    #   ★壊すプログラム b99（内側を帯 B の1つに戻す）で落ちることを測る。
    #   ★法則 R4（持続の形）が無いと①で落ちる＝R4 を外す判断は まこさん（そのとき期待を一緒に直す・設計書の塞げないもの）。
    t46: list[str] = []
    try:
        _lm46, _ = load_limits()
        _lm46 = resolve_hold_range(_lm46, "e38")
        _t46 = load_signal_table()
        _p46, _tfs46, _ = material_pool()
        _n46 = 0
        for _i46 in range(40):
            try:
                _b46, _d46 = sample_regime_build(_lm46, _p46, _tfs46, _t46, order_n=_i46)
            except SampleError:
                continue
            _n46 += 1
            _on46 = _b46["entry"]["tree"]["all"][0]["on"]["all"]
            if len(_on46) != 1 or not isinstance(_on46[0], dict) or _on46[0].get("form") != "streak":
                t46.append(f"案{_i46}: 入る条件が持続1つでない（{len(_on46)} 件）")
                continue
            _in46 = _on46[0].get("inner")
            if not isinstance(_in46, dict) or "all" not in _in46:
                t46.append(f"案{_i46}: 持続の内側が条件の束でない（{type(_in46).__name__}）")
                continue
            _core46 = _regime_on_conds(_b46)
            # ★期待の本数は、組む側の引いた記録ではなく、法則と §2.2 の元データから作る（監査 CP39 の A0-a＝D を束と記録の両方から消すと、記録から作る期待では落ちない）
            _laws46 = laws_for_scene("range")
            _want46 = (3 + (1 if ("not" in _laws46["forms"] and stage_candidates("stage2b")["bool_col"]) else 0)
                       + (1 if _law_families(_laws46, stage_candidates("stage2c")["law"])[0] else 0))
            _rec46 = (_d46.get("F") or {}).get("内側の本数")
            if len(_core46) != _want46 or _rec46 != _want46:
                t46.append(f"案{_i46}: 内側の本数 {len(_core46)}・引いた記録の内側の本数 {_rec46} が、法則と元データから作った期待（{_want46}）と違う")
            _forms46 = [("not" if "not" in c else c.get("form")) for c in _core46]
            if _forms46[:3] != ["level", "level", "not"] or any(f == "streak" for f in _forms46):
                t46.append(f"案{_i46}: 内側の並びが A・B・C・(D)・(G) でない: {_forms46}")
            if _n46 >= 5:
                break
        if _n46 == 0:
            t46.append("束が1本も組めない＝測れない")
    except SystemExit as _e46s:
        t46.append(f"途中で拒否されて止まった: {str(_e46s)[:120]}")
    except Exception as _e46:                       # noqa: BLE001
        t46.append(f"途中で止まった: {type(_e46).__name__} {str(_e46)[:120]}")
    ng += [f"T46: {_x}" for _x in t46]
    print("  T46 持続の内側が成立の全体: ①入る条件が持続1つ ②内側が条件の束 ③内側の本数が引いた記録と一致 ④並びが A・B・C・(D)・(G)")
    # ══ T48（2026-10-01・工事 m2f-label-builder-stages-20261001）＝本体は selftest_stages（口 --selftest-stages と同じ1本）══
    t48 = selftest_stages()
    ng += [f"T48: {_x}" for _x in t48]
    print("  T48 段の不具合の直し: B-1 上端が候補の本数を超えても組める ／ B-2 強さの否定の出る線は緩い側 ／ B-5 同じ条件を2回 並べない ／ B-6 段1・段2c は強さで並べる")
    # ══ T44・T49（2026-10-03・工事 m2f-stage-quantile-rank-20261003）＝本体は selftest_stage_q（口 --selftest-stage-q と同じ1本）══
    t49 = selftest_stage_q()
    ng += t49
    print("  T44・T49 段2a: ①分位を書いた設定で順位が通し番号（材料の順 → 分位の順） ②系統を絞った設定で組むと C に abs ／ abs の鍵が作れる")
    # ══ T50（2026-10-10・工事 g2-table-range-source-20261010）＝本体は selftest_stop_note（口 --selftest-stop-note と同じ1本）══
    t50 = selftest_stop_note()
    ng += [f"T50: {_x}" for _x in t50]
    print("  T50 本走を呼ぶ口: ①途中で止まると理由の行つきで知らせる ②止まらなければ結果をそのまま返す ③理由の行が無ければそう言う ④ほかの例外は握りつぶさない")

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

    # ★R8＝減らしたい損失の名前は、走らせる前に審判の一覧と照らす（fail-closed・2026-08-26）。
    #   打ち間違いを走り切ってから気づくのでは遅い（損の額が全部 $0 になり、案の優劣が付かない）。
    assert_known_exit_reason(a.minimize)
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
    # ★2026-09-27（M2-E-4e・まこさん決定「余白の直し方→C」）＝この本走は段2c の動く線（6か月の窓）を使いうるので、
    #   データの前の余白を「いまの余白＋いちばん長い窓」にする（stage_warm）。ほかの走行は engine_tuner.WARM のまま。
    _warm = stage_warm(et.WARM) if a.build_regime else et.WARM
    df, df_c = et.load_windows_cached(ad, [(SEARCH_START, SEARCH_END), (CONFIRM_START, CONFIRM_END)],
                                      _warm, use_cache=not a.no_cache)
    print(f"[データ] 値決め窓 {len(df):,} バー ／ 確認窓 {len(df_c):,} バー（助走込み・余白 {_warm}・{time.time() - t0:.0f}秒）")

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
                         net_floor=a.net_floor, minimize=a.minimize,
                         purpose=a.purpose, tag=a.tag,
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
    # ★減らしたい損失（要件 R8・まこさん確定 2026-07-27）＝診断で見つけた出血源を、形の探索で減らす。
    #   何を減らすかは診断の結果で毎回変わるので、コードに焼かず実行時に渡す（engine_tuner.py と同じ形）。
    ap.add_argument("--minimize", default=None,
                    help="減らしたい損失の、決済した理由（例 TIME_EXIT）。指定するとその損失を最小化する。"
                         "省略すると合計 net を最大化する（従来どおり）。"
                         "審判が知らない名前なら走らせる前に止まる")
    ap.add_argument("--net-floor", type=float, default=None,
                    help="合計 net の下限。値決め窓の合計 net がこれを下回った試行は捨てる（値はまこさん）")
    ap.add_argument("--resume", default=None, metavar="DIR",
                    help="途中で止まった走行の続きから始める（R12）。前の走行の記録の置き場を渡す")
    ap.add_argument("--no-cache", action="store_true", help="指標つきデータの使い回しをやめて毎回作り直す")
    ap.add_argument("--lint-provenance", action="store_true",
                    help="静的検査＝引く関数の外で材料・閾値・数字を作っている所を数える（0件が合格・K1〜K3）")
    ap.add_argument("--gate-matrix", action="store_true",
                    help="18マス（守るべき6つ×入口・場面の判定・出口）を機械が壊して、どの瞬間に止まるかを印字する（K4〜K8・K14）")
    ap.add_argument("--verify-provenance", default=None, metavar="PATH",
                    help="保存した案（structures_marked.json・または走行の置き場）の値の出どころを後から数え直す（K9）")
    ap.add_argument("--count-extra-candidates", action="store_true",
                    help="別枠（レンジ幾何・需給・時間帯）が、いまの印で何件 候補に出るかを数えて印字する"
                         "（監査 cp24 の §6-1 の確かめ方・壊すプログラム b33 が使う・読むだけ）")
    ap.add_argument("--selftest-extra-gate", action="store_true",
                    help="別枠3種（レンジ幾何・需給・時間帯）の審査の枝だけを試す（数秒）"
                         "＝T33-g と同じ本体（_selftest_extra_gate）を呼ぶ。壊すプログラム b35 が使う")
    ap.add_argument("--selftest-rank-demand", action="store_true",
                    help="需給の列を順位から読む枝だけを試す（数秒）＝T23-demand と同じ本体（selftest_rank_demand）を呼ぶ。"
                         "壊すプログラム b38 が使う（設計書 demand-in-ranking-20260907）")
    ap.add_argument("--selftest-stages", action="store_true",
                    help="段の不具合の直し（B-1・B-2・B-5・B-6）だけを試す＝T48 と同じ本体（selftest_stages）を呼ぶ"
                         "（全体の --selftest は約6分半で、承認の前の仮当ての打ち切り300秒を超えるため）")
    ap.add_argument("--selftest-stage-q", action="store_true",
                    help="段2a の分位ごとの順位と、向きを持つ C の abs・abs の鍵だけを試す＝T44・T49 と同じ本体（selftest_stage_q）を呼ぶ"
                         "（全体の --selftest は約6分半で、承認の前の仮当ての打ち切り300秒を超えるため・壊すプログラム b127 が使う）")
    ap.add_argument("--selftest-stop-note", action="store_true",
                    help="自己テストの中で本走を呼ぶ口（_selftest_run）だけを試す＝T50 と同じ本体（selftest_stop_note）を呼ぶ"
                         "（全体の --selftest は、承認の前の仮当ての打ち切り300秒を超えるため・壊すプログラム b159 が使う）")
    a = ap.parse_args()
    if a.selftest_stop_note:
        # ★2026-10-10（工事 g2-table-range-source-20261010）＝T50 だけを短く走らせる口（--selftest-stage-q と同じ作り）
        _ng50 = selftest_stop_note()
        for _x in _ng50:
            print(f"  ❌ T50: {_x}")
        print(f"  {'❌' if _ng50 else '✅'} T50 本走を呼ぶ口（途中で止まった理由を知らせる）／ダメだった件 {len(_ng50)}")
        return 1 if _ng50 else 0
    if a.selftest_stage_q:
        # ★2026-10-03（工事 m2f-stage-quantile-rank-20261003）＝T44・T49 だけを短く走らせる口（--selftest-stages と同じ作り）
        _ng49 = selftest_stage_q()
        for _x in _ng49:
            print(f"  ❌ {_x}")
        print(f"  {'❌' if _ng49 else '✅'} T44・T49 段2a の分位ごとの順位・向きを持つ C の abs と鍵／ダメだった件 {len(_ng49)}")
        return 1 if _ng49 else 0
    if a.selftest_stages:
        # ★2026-10-01（工事 m2f-label-builder-stages-20261001）＝T48 だけを短く走らせる口（--selftest-rank-demand と同じ作り）
        _ng48 = selftest_stages()
        for _x in _ng48:
            print(f"  ❌ T48: {_x}")
        print(f"  {'❌' if _ng48 else '✅'} T48 段の不具合の直し／ダメだった件 {len(_ng48)}")
        return 1 if _ng48 else 0
    if a.selftest_rank_demand:
        # ★2026-09-07（設計書 demand-in-ranking-20260907 の F）＝T23-demand だけを短く走らせる口。
        #   `--selftest` の全体は約6分半で、承認のときの打ち切り（120秒）を超えるため（--selftest-extra-gate と同じ理由）。
        _ngd = selftest_rank_demand()
        for _x in _ngd:
            print(f"  ❌ T23-demand: {_x}")
        print(f"  {'❌' if _ngd else '✅'} T23-demand 需給の列を順位から読む／ダメだった件 {len(_ngd)}")
        return 1 if _ngd else 0
    if a.selftest_extra_gate:
        # ★2026-09-07（監査 cp25 の §5-2・設計書 C）＝T33-g だけを短く走らせる口。
        #   なぜ要るか（実測）＝`--selftest` の全体は 6分23秒 かかり、承認のときに機械が
        #   壊すプログラムを走らせる打ち切り（120秒）を超える。2026-09-07 の承認で実際に
        #   打ち切られ、b35 が壊した行が元に戻らないまま残った。
        #   ★判定の中身は selftest と同じ1本（_selftest_extra_gate）＝2か所に書き写さない。
        _ng33 = _selftest_extra_gate()
        for _x in _ng33:
            print(f"  ❌ T33-g: {_x}")
        print(f"  {'❌' if _ng33 else '✅'} T33-g 別枠3種の審査（レンジ幾何・需給・時間帯）"
              "＝(1)オンなら通す (2)オフなら止める (3)戻せば通る"
              f"／ダメだった件 {len(_ng33)}")
        return 1 if _ng33 else 0
    if a.count_extra_candidates:
        # ★2026-09-06（監査 cp24 の §6-1・設計書 A）＝別枠3種が候補に何件 出るかを数える。
        #   印を空にすると 0 になる＝オン・オフが効いている、を機械で測るための口（b33 が使う）。
        _pool, _tfs, _ = material_pool()
        _tbl = load_signal_table()
        _by = _pool_families_by_lineage(_pool)
        _lm = dict(KENSHU_LIMITS)
        _n = 0
        for _role, _rr in _tbl["roles"].items():
            for _k, _c in _lineage_candidates(_role, _rr, _tbl, _by, _lm).items():
                _n += sum(1 for x in _c if isinstance(x, dict))
        print(_n)
        return 0
    if a.lint_provenance:
        return lint_provenance()
    if a.gate_matrix:
        return gate_matrix()
    if a.verify_provenance:
        return verify_provenance(a.verify_provenance)
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
                ex.validate_recipe(strip_marks(r), limits={"p_max": lm["p_max"], "count_range": lm["count_range"],
                                                           "role_max": lm["role_max"], "depth_max": lm["depth_max"],
                                                           "k_max": lm["k_max"]})
                structs.append(r)
            except (SampleError, ex.RecipeError) as e:
                rejects[str(e)[:24]] += 1
        print(json.dumps(structure_breakdown([strip_marks(s) for s in structs], cat_total), ensure_ascii=False, indent=1))
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


# ══ 4要素ゲートの検査の道具（59回目・設計書 v2 の K1〜K9・K14）══════════════════════════════
_DRAW_CTORS = {"_mat_drawn", "_mat_two_drawn", "_mat_pair_drawn", "_thr_drawn", "_thr_band_drawn",
               "_nv", "_iv", "_iv_from",
               # ★2026-09-11（手順9）＝成績表の列の数字をそのまま使う入口。印（PARAM_SRC）を書く。
               #   **乱数を1つも使わない**（`draw_*` を呼ばない）＝ここに足しても守りは緩まない。
               "_mat_from_col"}                               # draw_* を呼んでよい関数（引く関数）
_MAT_CTORS = {"_mat_drawn", "_mat_fixture", "_mat_from_col",
              # ★2026-09-11（M2-E-3 の手順4）＝`build_stage_candidates` を足した。
              #   なぜ足してよいか＝この関数が書く辞書は **候補の記録**（設計書 4-2 の鍵11個）で、
              #   材料ではない。`family` と `tf` は「どの材料を使ったか」の記録の欄。
              #   **材料そのものは `_mat_drawn`（唯一の入口）で作っている＝手で書いていない。**
              #   ★守りが緩まないことを、自己テスト T40⑥ が機械で確かめる
              #     ＝この関数の中に `_mat_drawn` の呼び出しが在り、`{"family": …, "param": …}` の形を
              #       手で書いていないこと。
              "build_stage_candidates",
              # ★2026-09-19（設計書 m2c-width-and-stage-candidates-20260918・まこさん承認）＝
              #   `build_width_candidates` を足した。理由は `build_stage_candidates` と同じ＝
              #   この関数が書く辞書も **候補の記録**（鍵11個）で、材料そのものではない。
              #   材料は `_mat_from_col`（成績表の列から作る唯一の入口）で作っている。
              #   ★レンジ幾何の候補は `{"geo": …}` で、family も tf も持たない＝この検査に当たらない。
              "build_width_candidates"}                        # family と tf を持つ辞書を書いてよい関数
_MARK_WRITERS = _DRAW_CTORS | {"_mat_fixture", "_thr_fixture", "_nvd", "_nvs", "_mat_with_pre",
                               # ★2026-09-11（手順9）＝乱数を使わない入口（閾値を1点／範囲を順に）
                               "_thr_fixed", "_nv_fixed",
                               "_exit_indicator_cond", "apply_slots", "gate_matrix", "selftest"}   # 印の鍵を書いてよい関数
_FIXTURE_CTORS = {"_mat_fixture", "_thr_fixture"}              # 自己テストの見本だけが呼んでよい関数


def lint_provenance(verbose: bool = True) -> int:
    """静的検査（K1〜K3）＝自分のソースを AST で読み、「引く関数の外」で作っている所を数える。

    数えるもの＝①family と tf の両方の鍵を持つ辞書リテラル（_MAT_CTORS の外）②印の鍵（PARAM_SRC など）を
    書く辞書リテラル・代入（_MARK_WRITERS の外）③draw_* の呼び出し（_DRAW_CTORS の外）
    ④旧 _cat（点の一覧）の定義 ⑤見本の関数（_mat_fixture・_thr_fixture）の呼び出し（selftest の外）。
    合格＝全部 0件。★CC が新しい書き方を1行 足すと、ここの数に出る（設計書 §7 の限界に対する見張り）。
    """
    import ast
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    tree = ast.parse(src)
    mark_names = {"PARAM_SRC", "Q_SRC", "NUM_SRC", "LIN_SRC"}
    draw_names = {"draw_param", "draw_q", "draw_int", "draw_num"}
    bad: dict[str, list[int]] = {"材料の辞書": [], "印の書き込み": [], "draw_*": [], "_cat": [], "見本の関数": []}

    def walk(node, stack):
        for ch in ast.iter_child_nodes(node):
            st = stack
            if isinstance(ch, (ast.FunctionDef, ast.AsyncFunctionDef)):
                st = stack + [ch.name]
                if ch.name == "_cat":
                    bad["_cat"].append(ch.lineno)
            if isinstance(ch, ast.Dict):
                keys = [k.value for k in ch.keys if isinstance(k, ast.Constant)]
                if "family" in keys and "tf" in keys and not (set(st) & _MAT_CTORS):
                    bad["材料の辞書"].append(ch.lineno)
                if any(isinstance(k, ast.Name) and k.id in mark_names for k in ch.keys) and not (set(st) & _MARK_WRITERS):
                    bad["印の書き込み"].append(ch.lineno)
            if isinstance(ch, ast.Assign):
                for t in ch.targets:
                    if (isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Name)
                            and t.slice.id in mark_names and not (set(st) & _MARK_WRITERS)):
                        bad["印の書き込み"].append(ch.lineno)
            if isinstance(ch, ast.Call) and isinstance(ch.func, ast.Name):
                if ch.func.id in draw_names and not (set(st) & _DRAW_CTORS):
                    bad["draw_*"].append(ch.lineno)
                # ★2026-09-07（next_step §6 の149番）＝囲っている関数の名前に selftest が
                #   含まれるかで見る。直す前は「名前がちょうど selftest」のときだけ許していたので、
                #   selftest から呼ばれる自己テストの本体（_selftest_extra_gate など）が
                #   「自己テストの外」と数えられた。★決まりは変えていない＝
                #   「見本の関数は、自己テストの中でだけ呼んでよい」はそのまま。
                if ch.func.id in _FIXTURE_CTORS and not any("selftest" in _s for _s in st):
                    bad["見本の関数"].append(ch.lineno)
            walk(ch, st)

    walk(tree, [])
    total = sum(len(v) for v in bad.values())
    if verbose:
        print("[--lint-provenance] 引く関数の外で作っている所（0件が合格）")
        for k, v in bad.items():
            print(f"  {k}: {len(v)} 件{('  行=' + str(v[:12])) if v else ''}")
        print(f"  合計 {total} 件 → {'合格' if total == 0 else '★不合格'}")
    return 0 if total == 0 else 1


def _stage_of(recipe: dict, lm: dict, table: dict, vlim: dict) -> tuple[str, str]:
    """案1本が、どの瞬間で止まるか＝S2（案を返す直前の4要素ゲート）→ S3（実行器の検査）。通れば「通る」。"""
    try:
        _gate_recipe(recipe, where="壊した案", limits=lm, table=table)
    except SampleError as e:
        return "S2", str(e)[:100]
    try:
        ex.validate_recipe(strip_marks(recipe), limits=vlim)
    except ex.RecipeError as e:
        return "S3", str(e)[:100]
    return "通る", ""


def gate_matrix(verbose: bool = True) -> int:
    """18マス（守るべき6つ × 入口・場面の判定・出口）を、プログラムの中の表のとおりに壊して測る（K4・K5・K7・K8・K14）。

    ★壊し方は CC がその場で選ばない＝下の MUTATIONS が正本（監査 P-3）。各マス＝どの値を・どう壊すか・止まるはずの瞬間。
    ★60回目（2026-08-25・設計書 v2 の やること5）＝出口の5番（役割）の例外を外した。
      直す前＝表に系統の欄が無い枝では「未実装（表の承認待ち）＝通る」と印字して、合格の線の外に置いていた。
      いま＝まこさんが表を承認したので（指紋 f5d53842ff40ab09…）、18マスとも同じに測る。
    """
    pool, tfs, _ct = material_pool()
    table = load_signal_table()
    lm, _w = load_limits()
    lm = resolve_hold_range(lm, "e38")
    vlim = {"n_min": None, "p_max": lm.get("p_max"), "count_range": lm.get("count_range"),
            "role_max": lm.get("role_max"), "depth_max": lm.get("depth_max"),
            "k_max": lm.get("k_max"), "r_min": lm.get("r_min")}
    ranges = material_ranges()
    by_lin = _pool_families_by_lineage([b for b in pool if ex.build_name(b) in table["parts"]
                                        and b["family"] in iref.FAMILY_LINEAGE])

    def conds_of(node):
        cs, _d = ex._walk(node)
        return list(cs)

    def entry_cond(r, pred):
        for c in conds_of(r["entry"]["connective"]):
            for cc in [c] + ([c["inner"]] if c.get("inner") else []) + ([c["on"]] if c.get("on") else []):
                if pred(cc):
                    return cc
        return None

    def regime_cond(r, pred):
        bd = ((r.get("meta") or {}).get("regime") or {}).get("build")
        if not bd:
            return None
        hy = bd["entry"]["tree"]["all"][0]
        # ★M2-E-4d（束1・2026-09-25）＝入る条件の側は、持続の内側の成立の並びを `_regime_on_conds` で読む
        #   （形の読み方を1か所に）。返るのは束の中の同じ辞書なので、わざと壊す相手をそのまま書き替えられる。
        for c in list(_regime_on_conds(bd)) + list(hy["off"]["any"]):
            cc = c.get("not") or c
            if pred(cc):
                return cc
        return None

    def exit_cond(r, pred):
        for b in r["exits"]:
            if not b.get("fire"):
                continue
            for c in conds_of(b["fire"]):
                if pred(c):
                    return c
        return None

    has_fam = lambda c: bool(c.get("material")) and isinstance(c["material"][0], dict) and "family" in c["material"][0]
    has_q = lambda c: "threshold_q" in (c.get("value") or {})

    # ── 土台の案＝場面の判定つき・出口に指標の条件がある案を、種を変えて探す（見つからなければ止める）──
    base = None
    for i in range(400):
        rng = np.random.default_rng([59, 7, i])
        try:
            r = sample_structure(rng, lm, pool, tfs, side="SHORT", logic_id=f"GM{i}",
                                 build_regime=True, regime_order_n=i % 20)
        except SampleError:
            continue
        if _stage_of(r, lm, table, vlim)[0] != "通る":
            continue
        if entry_cond(r, lambda c: has_fam(c) and has_q(c)) is None:
            continue
        if regime_cond(r, has_fam) is None or exit_cond(r, has_fam) is None:
            continue
        base = r
        break
    if base is None:
        print("[--gate-matrix] ★土台の案が作れない（場面の判定つき・出口に指標の条件がある案が400回で0本）")
        return 1

    def fresh():
        return json.loads(json.dumps(base))

    def other_lineage_family(role_lineages):
        for lin, fams in by_lin.items():
            if lin not in set(role_lineages) and fams:
                return fams[0], lin
        return None, None

    # ── 壊し方の表（正本）＝(守るべきこと, 場所) → (壊す関数, 止まるはずの瞬間) ──
    def mut_family(find):
        def f(r):
            c = find(r, has_fam)
            c["material"][0]["family"] = "ZZZ_NOPE"
        return f

    def mut_q(find):
        def f(r):
            c = find(r, lambda c: has_fam(c) and has_q(c)) or find(r, has_q)
            c["value"]["threshold_q"] = "q999"
        return f

    def mut_param(find):
        def f(r):
            c = find(r, has_fam)
            c["material"][0]["param"] = 999999
        return f

    def mut_tf(find):
        def f(r):
            c = find(r, has_fam)
            c["material"][0]["tf"] = "9m"
        return f

    def mut_role_entry(r):
        c = entry_cond(r, lambda c: c.get("role") == "trigger" and has_fam(c))
        fam, lin = other_lineage_family(table["roles"]["trigger"]["lineages"])
        c["material"][0] = _mat_drawn(np.random.default_rng(1), fam, c["material"][0]["tf"], ranges, table=table)

    def mut_role_regime(r):
        c = regime_cond(r, lambda c: c.get("role") == "location" and has_fam(c))
        fam, lin = other_lineage_family(table["roles"]["location"]["lineages"])
        c["material"][0] = _mat_drawn(np.random.default_rng(2), fam, c["material"][0]["tf"], ranges, table=table)

    def mut_role_exit(r):
        c = exit_cond(r, has_fam)
        src = c.get(LIN_SRC) or {}
        # ★60回目（2026-08-25）＝「表に欄が無い枝は測らない」という例外を外した。
        #   まこさんが表を承認したので、出口5番も他の17マスと同じに測る（設計書 v2 の やること5）。
        if not src.get("lineages"):
            raise LookupError("出口の条件に系統の印が無い（印が付かない道が残っている）")
        fam, lin = other_lineage_family(src["lineages"])
        c["material"][0] = _mat_drawn(np.random.default_rng(3), fam, c["material"][0]["tf"], ranges, table=table)

    def mut_exit_num(r):
        for b in r["exits"]:
            for d in _walk_dicts(b):
                mk = d.get(NUM_SRC)
                if isinstance(mk, dict):
                    for field, m in mk.items():
                        if m.get("kind") in ("num", "int", "linear") and field in d:
                            d[field] = float(m["hi"]) * float(m.get("scale", 1.0)) * 10.0 + 1000.0
                            return
        raise LookupError("出口に印つきの数字が無い")

    def mut_form_entry(r):
        entry_cond(r, has_fam)["form"] = "bogus_form"

    def mut_regime_tree(r):
        hy = r["meta"]["regime"]["build"]["entry"]["tree"]["all"][0]
        r["meta"]["regime"]["build"]["entry"]["tree"] = {"all": list(hy["on"]["all"])}      # hysteresis を外す（K-3）

    def mut_exit_reason(r):
        for b in r["exits"]:
            if b.get("fire") and exit_cond({"exits": [b]}, has_fam):
                b["reason"] = "BOGUS_REASON"
                return
        r["exits"][0]["reason"] = "BOGUS_REASON"

    MUTATIONS = {
        (1, "入口"): (mut_family(entry_cond), "S2"), (1, "場面の判定"): (mut_family(regime_cond), "S2"), (1, "出口"): (mut_family(exit_cond), "S2"),
        (2, "入口"): (mut_q(entry_cond), "S2"), (2, "場面の判定"): (mut_q(regime_cond), "S2"), (2, "出口"): (mut_exit_num, "S2"),
        (3, "入口"): (mut_param(entry_cond), "S2"), (3, "場面の判定"): (mut_param(regime_cond), "S2"), (3, "出口"): (mut_param(exit_cond), "S2"),
        (4, "入口"): (mut_tf(entry_cond), "S2"), (4, "場面の判定"): (mut_tf(regime_cond), "S2"), (4, "出口"): (mut_tf(exit_cond), "S2"),
        (5, "入口"): (mut_role_entry, "S2"), (5, "場面の判定"): (mut_role_regime, "S2"), (5, "出口"): (mut_role_exit, "S2"),
        (6, "入口"): (mut_form_entry, "S3"), (6, "場面の判定"): (mut_regime_tree, "S3"), (6, "出口"): (mut_exit_reason, "S3"),
    }
    NAMES = {1: "指標がカタログに在る", 2: "閾値が範囲から", 3: "パラメータが範囲から",
             4: "時間足が使えるものから", 5: "役割に沿う", 6: "つなぎ方が型の表に沿う"}
    rows = []
    ok_all = True
    for (k, place), (fn, want) in MUTATIONS.items():
        r = fresh()
        try:
            fn(r)
        except LookupError as e:
            # ★60回目（2026-08-25）＝出口5番の例外（表の承認待ち＝合格の線の外）を外した。
            #   いまは18マスとも同じ扱い＝壊せなければ不合格。
            got, msg = "未実装", str(e)
            rows.append((k, place, want, got, msg))
            ok_all = False
            continue
        got, msg = _stage_of(r, lm, table, vlim)
        rows.append((k, place, want, got, msg))
        if got != want:
            ok_all = False
    if verbose:
        print(f"[--gate-matrix] 土台の案＝{base['meta']['logic_id']}（入口 {len(conds_of(base['entry']['connective']))} 条件・出口 {len(base['exits'])} 枝）")
        print("  # | 守るべきこと | 場所 | 止まるはず | 止まった | 理由")
        for k, place, want, got, msg in rows:
            mark = "✅" if got == want else ("△" if got == "未実装" else "❌")
            print(f"  {k} | {NAMES[k]} | {place} | {want} | {got} {mark} | {msg[:70]}")
    # ── K5＝正しい案 20本は通る ──
    passed = 0
    tried = 0
    for i in range(400):
        if passed >= 20:
            break
        try:
            r = sample_structure(np.random.default_rng([59, 8, i]), lm, pool, tfs, side="SHORT", logic_id=f"OK{i}")
        except SampleError:
            continue
        tried += 1
        if _stage_of(r, lm, table, vlim)[0] == "通る":
            passed += 1
    # ── K7＝第2段で範囲の外の値を書き込む ──
    slots = value_slots(base, lm)
    k7 = "スロットなし"
    if slots:
        p, sp = slots[0]
        bad_val = f"q999" if sp.get("kind") == "q" else int(sp["hi"]) * 10 + 1000
        r7 = apply_slots(base, {p: bad_val}, dict(slots))
        k7 = _stage_of(r7, lm, table, vlim)[0]
    # ── K14＝案を作る関数を通さずに、範囲の外の値を持つ案を走らせる入口に直に渡す ──
    r14 = fresh()
    mut_param(entry_cond)(r14)
    _res14, _why14 = run_trial_guarded(pd.DataFrame(), r14, {}, None, pd.Timestamp("2024-03-01"), pd.Timestamp("2024-04-01"))
    k14 = "止まる" if (_res14 is None and _why14 and "4要素ゲート" in _why14) else "★通る"
    if verbose:
        print(f"  K5 正しい案: {passed}/{tried} 本 通る（20本 通るまで）")
        print(f"  K7 第2段で範囲の外の値: {k7}（S2 が合格）")
        print(f"  K14 走らせる入口に直に渡す: {k14}")
    ok_all = ok_all and passed >= 20 and k7 == "S2" and k14 == "止まる"
    print(f"  ＝{'合格' if ok_all else '★不合格'}（18マスとも同じに測る＝出口5番の例外は 2026-08-25 に外した）")
    return 0 if ok_all else 1


def verify_provenance(path: str) -> int:
    """保存した案の値の出どころを後から数え直す（K9）。path＝structures_marked.json か、走行の置き場か、journal.jsonl。"""
    p = pathlib.Path(path)
    if p.is_dir():
        p = p / "structures_marked.json"
    elif p.name == "journal.jsonl":
        p = p.with_name("structures_marked.json")
    if not p.exists():
        print(f"[--verify-provenance] 印つきの案の記録が無い: {p}")
        return 2
    d = json.loads(p.read_text(encoding="utf-8"))
    structs = d.get("structures") or []
    table = load_signal_table()
    lm, _w = load_limits()
    lm = resolve_hold_range(lm, "e38")
    bad = []
    for i, r in enumerate(structs):
        try:
            _gate_recipe(r, where=f"保存した案 #{i}", limits=lm, table=table)
        except SampleError as e:
            bad.append((i, str(e)[:120]))
    print(f"[--verify-provenance] {p}: 案 {len(structs)} 本 ／ 違反 {len(bad)} 件")
    for i, m in bad[:10]:
        print(f"  #{i}: {m}")
    return 0 if not bad else 1


# ── H2 実行時の守り（2026-08-16 まこさん GO「H2 完全化」の層3・穴④）──────────────────
#    自分のコードに未来参照の典型（shift にマイナスの数字・rolling の center を True）が無いことを、
#    読み込みのたびに ratchet_guards で機械確認する。違反が入ると import の瞬間に止まる＝
#    偽の数字を出す前に落ちる。説明文では誤発火しない（行内コメントを外してから見る）。
import pathlib as _h2_pathlib                            # noqa: E402
import ratchet_guards as _h2_rg                          # noqa: E402
_h2_rg.assert_no_future_ref(_h2_pathlib.Path(__file__).read_text(encoding="utf-8"))


if __name__ == "__main__":
    raise SystemExit(main())
