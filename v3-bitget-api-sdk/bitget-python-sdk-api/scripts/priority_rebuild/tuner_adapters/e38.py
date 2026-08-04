#!/usr/bin/env python3
"""e38 — E38 の接続ファイル（engine_tuner が読む・要件 R4・まこさん承認 2026-07-27）

値の差し替え方＝共通の売買ループ e38_logic_parts.generic_logic_loop の引数。
**この方式を知っているのは本ファイルだけ。探索器は知らない。**
ロジックの定義と探索範囲の正本＝e38_logics.json（設定駆動・段1 の確定事項）。

中身は engine_tuner.py（旧 engine_search_e38.py）から E38 に依っていた部分をそのまま移した。
挙動は変えない＝同じ種で同じ値が選ばれることを恒等の確認で示す。
"""
from __future__ import annotations

import json
import pathlib

import pandas as pd

import e37_scalp as e37
import e38_logic_parts as parts

NAME = "e38"
LABEL = "E38 優先度スタック（レンジ・両方向・スキャル・設定駆動）"

HERE = pathlib.Path(__file__).resolve().parent.parent      # scripts/priority_rebuild/
CONFIG = HERE / "e38_logics.json"

TYPE_COL = "ceil_type"                                     # 型別に分けて見る列
TYPE_VALUES = ("down", "flat_up")


def config() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def _logic(logic_id: str) -> dict:
    lg = next((z for z in config()["logics"] if z["id"] == logic_id), None)
    if lg is None:
        raise SystemExit(f"[エラー] ロジック id が {CONFIG.name} に無い: {logic_id}")
    return lg


def _is_grid(lg: dict) -> bool:
    """グリッド売買（S5/L5＝parts.grid_loop で動く・要件 R2・2026-08-04）か。"""
    return lg.get("impl", {}).get("entry_point") == "grid_loop"


def logics() -> list[dict]:
    """扱えるロジックの一覧。回せるかの判定も返す（説明書 engine_tuner_manual と同じ条件）。"""
    cfg = config()
    out = []
    for lg in cfg["logics"]:
        ok, why = True, ""
        if lg.get("impl", {}).get("module") != "e38_logic_parts":
            ok, why = False, f"実装が {lg.get('impl', {}).get('module', '未指定')}＝共通の売買ループで動かない"
        elif _is_grid(lg):                                 # グリッド（S5/L5・要件 R2・2026-08-04）
            if lg["entry"]["type"] not in parts.GRID_ENTRY_TYPES:
                ok, why = False, f"入口の型 {lg['entry']['type']} が grid_loop に無い"
            elif cfg["search_space"]["logics"].get(lg["id"]) is None:
                ok, why = False, "探索する値が宣言されていない"
        elif lg["entry"]["type"] not in parts.ENTRY_FNS:
            ok, why = False, f"入口の型 {lg['entry']['type']} が実装されていない"
        elif cfg["search_space"]["logics"].get(lg["id"]) is None:
            ok, why = False, "探索する値が宣言されていない"
        out.append({"id": lg["id"], "side": lg.get("side", ""), "label": lg.get("label", ""),
                    "searchable": ok, "why": why})
    return out


def space(logic_id: str) -> dict:
    """探索する値の宣言＝出口の共通 ＋ そのロジックの入口。
    ★同名のキーはロジック側が勝つ（例 S2 の tmax_bars＝枠外の長い保有の除外・まこさん決定 2026-07-25）。"""
    cfg = config()
    lg = _logic(logic_id)
    if lg.get("impl", {}).get("module") != "e38_logic_parts" or (
            not _is_grid(lg) and lg["entry"]["type"] not in parts.ENTRY_FNS) or (
            _is_grid(lg) and lg["entry"]["type"] not in parts.GRID_ENTRY_TYPES):
        raise SystemExit(f"[エラー] 回せるのは共通の売買ループか grid_loop のロジックだけ"
                         f"（{logic_id}: {lg.get('impl', {})} / {lg['entry']['type']}）")
    sp = cfg["search_space"]["logics"].get(logic_id)
    if sp is None:
        raise SystemExit(f"[エラー] search_space.logics に {logic_id} が無い（正本 {CONFIG.name}）")
    sp = {k: v for k, v in sp.items() if not k.startswith("_")}   # _note 等の説明の鍵は宣言ではない
    if _is_grid(lg):
        # グリッドの出口は形が違う（要件 R2・2026-08-04）＝共通の出口の宣言から意味のある2つだけを借りる。
        #   sl_zone_k＝災害SL の帯幅係数（既存の宣言 0.5〜2.0 を借用＝新しい数字を作らない）
        #   tmax_bars＝保有の上限（役割から決めた整数の範囲＝hold_space）
        # 残り（tp1_frac / tp2_target / tp_mode / tp_pct_k / be_wait）は入れない＝意味の無い軸を探索しない。
        # grid_n の範囲は search_space.logics が正本＝null の間は engine_tuner が値待ちで止まる（fail-closed）。
        return {"sl_zone_k": cfg["search_space"]["common_exit"]["sl_zone_k"],
                "tmax_bars": hold_space(), **sp}
    out = {**cfg["search_space"]["common_exit"], **sp}
    # ★保有時間の上限を、役割から決めた整数の範囲へ差し替える（監査 4-19／要件 R6・まこさん OK 2026-08-03）。
    #   それまでは設定ファイルのメニュー（1・2・3・6・9・12 本）からしか選べなかった。
    #   メニューに無い本数（例＝5本＝25分）は、何回試しても出なかった。
    #   ロジックが自分で tmax_bars を宣言している場合は、そちらを尊重する（ロジック側が勝つ・従来の決まり）。
    if "tmax_bars" in out and "tmax_bars" not in sp:
        out["tmax_bars"] = hold_space()
    return out


def hold_space() -> dict:
    """保有時間の上限の探索の宣言を、この戦略の役割から作る（単位＝5分足の本数）。

    手順を書きます。
      1 設定ファイル recipes/search_limits.json を読みます。
      2 採用台帳 adopted_strategies.md の ROLE_CHECK の行から、e38 の役割（scalp）を読み取ります。
      3 その役割の範囲（lo_bars と hi_bars）を設定ファイルから読み取ります。
      4 Optuna に渡す宣言の形（type=int）にして返します。
    役割が台帳に無いとき、その役割の範囲が設定ファイルに無いときは、走らせません（fail-closed）。
    """
    import engine_tuner_gen as gen
    lm, _waiting = gen.load_limits()
    lo, hi = gen.hold_bars(gen.resolve_hold_range(lm, NAME))
    return {"type": "int", "lo": lo, "hi": hi, "step": 1}


def stop_rules(logic_id: str) -> dict:
    """終わりの条件の値（まこさん確定・置き場所は設定ファイルの tuner ブロック1箇所）。

    ★engine_tuner は数字を持たない＝実行のたびに手で入れない。戦略が増えたら接続ファイルが返す。
    """
    t = config().get("tuner", {})
    ops = (t.get("ops_min_per_day") or {})
    return {"delta_net": t.get("delta_net"), "n_max": t.get("n_max"),
            "atr_band_edges": t.get("atr_band_edges"),
            "ops_min_per_day": ops.get("value"), "ops_reason": ops.get("reason"),
            "ops_date": ops.get("date")}


def baseline(logic_id: str) -> dict | None:
    """土台＝いま設定ファイルに入っている値（B1・B2 の比較相手・2026-07-27 まこさん OK）。

    探索で選んだ値が「土台より良いか」を見るための相手。設定ファイルの確定値をそのまま返す。
    """
    lg = _logic(logic_id)
    out = {}
    out.update({k: v for k, v in lg["entry"].get("params", {}).items() if v is not None})
    out.update({k: v for k, v in lg["exit"].get("params", {}).items() if v is not None})
    # ★出口の値が設定ファイルに揃っていないロジックは「土台が無い」＝まだ採用値を持たない候補。
    #   無理に既定値を当てて土台のふりをしない（比較相手が偽物になると B1・B2 が意味を失う）。
    need = set(config()["search_space"]["common_exit"])
    return out if need.issubset(out) else None


def coverage(logic_id: str) -> list[str]:
    """この探索が触れる指標の列（＝網羅度の分子・2026-07-27 まこさん OK・監査 提案1）。

    分母は observe_diag の指標カタログ（96種 × 8足 = 768列）。ここは手で書いた部品の一覧を返す
    ＝入口の確認に使えるのは HTF_PARTS と VOL_PARTS だけで、時間足も部品名に焼き付いている。
    要件 R3 が終わればここがカタログ側に置き換わる。
    """
    sp = space(logic_id)
    used = []
    for k in ("confirm_htf", "confirm_vol"):
        if k in sp:
            used += [c for c in sp[k]["choices"] if c != "none"]
    return used


def exit_keys() -> set:
    """出口側のキー（探索器が試行の値を入口と出口へ振り分けるのに使う）。"""
    return set(config()["search_space"]["common_exit"])


def writeback_map(logic_id: str, values: dict) -> tuple[dict, list[tuple[str, str]]]:
    """試行の値を、設定ファイルの欄の名前へ言い換えます（要件 R9・まこさん OK 2026-08-02・案A）。

    なぜ要るか
      engine_tuner は、確認シグナルの候補それぞれについて、しきい値を1つずつ探します。
      しきい値の名前は th_roc24_2h のように、シグナルの名前が付いています。
      設定ファイルには、選ばれたシグナルのしきい値を入れる欄が1つだけあります。
      欄の名前は confirm_htf_th です。ですから言い換えが要ります。
      この言い換えを知っているのは、この接続ファイルだけです。書き戻しの道具は知りません。

    やること
      1 confirm 系の欄を探します。候補のどれかに th_ の宣言があるものだけが対象です。
      2 その欄で選ばれたシグナルの th_ を、欄の名前に _th を付けた名前へ言い換えます。
      3 選ばれなかった th_ は「使わない」として返します。黙って捨てません。
      4 それ以外の値は、名前を変えずにそのまま返します。

    返すもの
      1つ目は、設定ファイルへ入れる値です。鍵は設定ファイルの欄の名前です。
      2つ目は、使わない値の一覧です。名前と理由の組で返します。
    """
    dec = config()["search_space"]["logics"].get(logic_id) or {}
    conf_cols = [k for k, v in dec.items()
                 if k.startswith("confirm") and isinstance(v, dict) and v.get("type") == "cat"
                 and any(f"th_{ch}" in dec for ch in v.get("choices", []))]

    chosen: dict[str, str] = {}                 # しきい値の名前 → 入れ先の欄の名前
    for c in conf_cols:
        pick = values.get(c)
        if pick and pick != "none" and f"th_{pick}" in dec:
            chosen[f"th_{pick}"] = f"{c}_th"

    out: dict = {}
    unused: list[tuple[str, str]] = []
    for name, v in values.items():
        if not name.startswith("th_"):
            out[name] = v
            continue
        if name in chosen:
            out[chosen[name]] = v
            continue
        sig = name[3:]
        owner = next((c for c in conf_cols if sig in dec[c].get("choices", [])), None)
        why = (f"{owner} で選ばれたのは {values.get(owner)} です。このしきい値は使いません"
               if owner else "対応する確認シグナルが選ばれていません。このしきい値は使いません")
        unused.append((name, why))
    return out, unused


def series_bank(win: pd.DataFrame) -> dict:
    """quantile 型の宣言が参照する分布（値決め窓の中だけ＝確認窓・採点窓は見ない）。"""
    r12 = win["close"].pct_change(12)
    out = {
        "dev_z_abs": win["dev_z"].abs().dropna(),
        "ret12_abs_down": (-r12[r12 < 0]).dropna(),
    }
    for c in win.columns:                       # 確認2軸の部品列（prepare_df が付ける）
        if c.startswith("e38_htf_") or c.startswith("e38_vol_"):
            out[c] = win[c].dropna()
    return out


def fixed(logic_id: str, space_names) -> tuple[dict, dict]:
    """設定ファイルの確定値（探索対象でないもの）。毎試行に混ぜる。

    ★2026-07-25 に見つけた配線漏れの対策＝試行の値だけを部品に渡すと、設定ファイルの
      固定値（例 S2 の ceil_filter=flat_up）が探索中に無視される。探索対象のキーは試行値が勝つ。
    """
    lg = _logic(logic_id)
    ep = {k: v for k, v in lg["entry"].get("params", {}).items() if v is not None and k not in space_names}
    xp = {k: v for k, v in lg["exit"].get("params", {}).items() if v is not None and k not in space_names}
    return ep, xp


def min_per_day(logic_id: str):
    """件数/日 の下限（値の確定はまこさん・null ならゲートなし）。"""
    v = _logic(logic_id).get("params", {}).get("search_min_per_day")
    return None if v is None else float(v)


def regime(logic_id: str) -> dict:
    """このロジックが担当する相場を宣言する（監査 4-19／要件 R5・2026-08-03 新設）。

    どこから読むか
      設定ファイル e38_logics.json の global.regime に書いてある3つを、そのまま返します。
      name は相場の名前です。entry_col は「このバーだけ玉を建ててよい」を表す列の名前です。
      block_col は「このバーでは新規の発注を止める」を表す列の名前です。

    なぜここに置くか
      それまで実行器 engine_tuner_exec.py のコードに、列の名前が直接書いてありました。
      だから engine_tuner はレンジ以外の相場を指定できませんでした。
      戦略の側が宣言する形にすると、戦略ごとに違う相場を指定できます（要件 R5 の完了の線）。

    ⚠️ 値はいまと同じです。ですから売買の結果は1行も変わりません。
    """
    rg = config()["global"].get("regime") or {}
    return {"name": rg.get("name"), "entry_col": rg.get("entry_col"), "block_col": rg.get("block_col")}


def load_windows(windows, warm: pd.Timedelta) -> list[pd.DataFrame]:
    """窓ごとの指標つきデータを作る。生データの読み込みは1回だけ（重いため）。"""
    lo = min(w[0] for w in windows) - warm
    raw = e37._load(0, start_override=str(lo.date()))
    cfg = config()
    adaptive_k = e37.V25_K if cfg["global"].get("regime", {}).get("v25_adaptive_band") else None
    out = []
    for (s, e) in windows:
        d = raw[(raw["ts"] >= s - warm) & (raw["ts"] < e)].reset_index(drop=True).copy()
        out.append(parts.prepare_df(d, adaptive_k=adaptive_k))
    return out


def run(df: pd.DataFrame, logic_id: str, entry_params: dict, exit_params: dict) -> pd.DataFrame:
    """値を1組受け取って売買記録を返す（1試行の中身・CSV は書かない）。"""
    lg = _logic(logic_id)
    if _is_grid(lg):                                       # グリッド（S5/L5・要件 R2・2026-08-04）
        tr = parts.grid_loop(df, lg["entry"]["type"], entry_params, exit_params,
                             max_lots=int(lg.get("params", {}).get("max_lots", 2)),
                             logic_id=logic_id, regime=regime(logic_id))
        return pd.DataFrame(tr)
    tr = parts.generic_logic_loop(df, lg["entry"]["type"], entry_params, exit_params,
                                  max_lots=int(lg.get("params", {}).get("max_lots", 2)),
                                  logic_id=logic_id,
                                  regime=regime(logic_id))   # 監査 4-19＝相場は宣言から渡す
    return pd.DataFrame(tr)
