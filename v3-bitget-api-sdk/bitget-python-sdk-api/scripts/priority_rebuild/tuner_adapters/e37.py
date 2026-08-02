#!/usr/bin/env python3
"""e37 — E37 の接続ファイル（engine_tuner が読む・要件 R4／R1・まこさん承認 2026-07-27）

値の差し替え方＝e37_scalp のモジュール定数を setattr で書き換えてから run_e37 を呼ぶ。
**この方式を知っているのは本ファイルだけ。探索器は知らない。**
中身は engine_search_e37.py（従来の E37 専用の探索器）から そのまま移した＝挙動を変えない。

⚠️ E37 は S1（ショート）と L1（ロング）が1回の走行で同時に動く一枚岩で、ロジック単位に分かれていない
   （e37_scalp.py 2832行・v11 から v59 までの枝が全部その中にある）。
   だから --logic に渡す単位は「調整するツマミ群」になる。E38 の --logic（入口と出口の組み合わせ）とは
   単位の意味が違う。S1 と L1 を別々に調整するには E37 の実装を分解する作業が要る（要件 R1 の残り）。
"""
from __future__ import annotations

import json
import pathlib

import pandas as pd

import e37_scalp as e37

# ★歩6・監査 4-17（まこさん GO 2026-08-02）＝採用中の S1 と L1 は「レシピ経由」で回す。
#   一枚岩の run_e37 では S1 と L1 が同時に動いてしまい、ロジック単位で調整できない（監査 335-337行）。
#   2026-08-02 に S1 と L1 をレシピ（条件データ）へ書き写し、売買記録が md5 で完全一致することを確かめた。
#   ここはその成果を engine_tuner へつなぐだけ＝売買のルール（e37_scalp.py）は1バイトも変えない。
RECIPE_DIR = pathlib.Path(__file__).resolve().parents[1] / "recipes"
RECIPES = {"S1": "identity_s1_legacy.json", "L1": "identity_l1_legacy.json"}
_PREPARED: dict = {}                                       # 指標つきデータの使い回し（同じ窓は1回だけ作る）

NAME = "e37"
LABEL = "E37 レンジスキャル（採用土台 v59d_164・S1 ショートと L1 ロングが同時に動く一枚岩）"

TYPE_COL = "ceil_type"                                     # 型別に分けて見る列
TYPE_VALUES = ("down", "flat_up")

# 土台の構成（engine_search_e37.BASE_KW と同一＝report_trades_e37_range_scalp_longfu_145_score.txt §0 実行引数）
BASE_KW = dict(
    v11=True, v12_open_range=True, v13_time_maker=True, v18_tp2_far=True, v20_rg5=True,
    v22_set=True, v24_trend_maker_tp=True, v25_adaptive_band=True,
    v26_down_hours=1.0, v26_gap=0.5, v26_max_age_hours=6.0, v26_split_ceiling=True,
    v27_flatup_lock=True, v31_time_be=True, v35_flatup_range=True, v36_flatup_near=True,
    v37_flatup_climb=True, v38_flatup_clamp=True, v40_down_no_age=True,
    v47_mtf_cut=True, v48_stale_wait=True, v50_trend_wait=True, v53_flatup_fast_cut=True,
    v56_rearm_delay=True, v57_long_support=True, v57_long_flat_up_only=True,
)

_SIGS = ["adx7", "di7", "di14", "kijun26"]                 # 急騰の判定に使うシグナルの種類

# 調整できるツマミ群。E37 は一枚岩なので「ロジック」でなく「ツマミ群」の単位で並ぶ。
LOGICS = [
    {"id": "v59", "side": "both", "label": "急騰早切りの値（型別シグナル × 建値からの逆行% × 待ち時間）",
     "searchable": True, "why": ""},
    # ★歩6・監査 4-17＝ロジック単位で回せるようにしたもの（レシピ経由・2026-08-02）
    {"id": "S1", "side": "SHORT", "label": "レンジ上端の逆張りショート（採用土台 v59d_164 の S1・レシピ経由）",
     "searchable": True, "why": ""},
    {"id": "L1", "side": "LONG", "label": "レンジ下端の反発ロング（採用土台 v59d_164 の L1・レシピ経由）",
     "searchable": True, "why": ""},
]


def logics() -> list[dict]:
    return [dict(z) for z in LOGICS]


def _recipe(logic_id: str) -> dict:
    """そのロジックのレシピ（条件データ）を読む。中身は 2026-08-02 に恒等が取れた書き写し。"""
    return json.loads((RECIPE_DIR / RECIPES[logic_id]).read_text(encoding="utf-8"))


def space(logic_id: str) -> dict:
    """探索する値の宣言。

    ★閾値をシグナルの種類ごとに分けて持つ（th_down_adx7 … th_down_kijun26）。
      kijun26 は%スケールで adx/di の 10〜70 と桁が違うため、1つの範囲では扱えない。
      kijun26 だけ quantile 型＝値決め窓の分布から実行時に決める（CC の手打ち値なし）。
      走らせるときは、選ばれたシグナルに対応する閾値だけを使う（E38 の confirm_htf / th_* と同じ方式）。
    """
    if logic_id not in {"v59"} | set(RECIPES):
        raise SystemExit(f"[エラー] ツマミ群の id が e37 に無い: {logic_id}"
                         f"（在るのは {', '.join(z['id'] for z in LOGICS)}）")
    sp: dict = {}
    for side in ("down", "flat"):
        sp[f"V59_{side.upper()}_SIG"] = {"type": "cat", "choices": list(_SIGS)}
        for s in _SIGS:
            sp[f"th_{side}_{s}"] = ({"type": "quantile", "series": "kij_dev", "q_lo": 0.50, "q_hi": 0.995}
                                    if s == "kijun26" else {"type": "float", "lo": 10.0, "hi": 70.0})
    sp["V59_DOWN_ADV_PCT"] = {"type": "float", "lo": 0.1, "hi": 1.0}
    sp["V59_FLAT_ADV_PCT"] = {"type": "float", "lo": 0.1, "hi": 1.0}
    sp["V59_DOWN_WIN_MIN"] = {"type": "cat", "choices": [0, 120, 180, 240, 360]}
    sp["V59_FLAT_WIN_MIN"] = {"type": "cat", "choices": [60, 120, 240, 360]}
    sp["V59_WAIT_MIN"] = {"type": "cat", "choices": [0, 5, 10, 15, 20, 30, 45, 60]}
    sp["V59_CUT_MODE"] = {"type": "cat", "choices": ["close", "stop"]}
    if logic_id == "v59":
        return sp
    if logic_id == "S1":
        # ★段1（まこさん OK 2026-08-02「最初は v59 の値だけ」）＝レシピで表せる7個だけを開く。
        #   範囲の宣言は上の v59 のものをそのまま使う＝私が新しい数字を作らない（L-267）。
        #   ⛔ 開けない2つと、その理由（矮小化しないために明記する）:
        #     V59_DOWN_SIG／V59_FLAT_SIG（シグナルの種類を4つから選ぶ）
        #       ＝レシピの経路には DI差14 と 基準線乖離26 の2列しか材料が無い。adx7 と di7 の列を
        #         作る処理がまだ無いので、選ばせると材料が無い側で必ず止まる。作れば開く。
        #     V59_CUT_MODE（成行で降りるか、指値を置いて待つか）
        #       ＝枝の執行の形そのものを差し替える変更で、値の差し替えでは書けない。段2 で開く。
        return {k: sp[k] for k in ("th_down_di14", "th_flat_kijun26",
                                   "V59_DOWN_ADV_PCT", "V59_FLAT_ADV_PCT",
                                   "V59_DOWN_WIN_MIN", "V59_FLAT_WIN_MIN", "V59_WAIT_MIN")}
    # L1 は v59 の枝を持たない（急騰早切りはショート側の機構）。段1 で開くのは損切りの幅1つだけ。
    #   宣言は E38 の共通の出口の宣言をそのまま借りる＝ここでも私が新しい数字を作らない。
    from tuner_adapters import e38 as _e38
    return {"sl_zone_k": dict(_e38.config()["search_space"]["common_exit"]["sl_zone_k"])}


# ── 終わりの条件の値（まこさん確定 2026-07-27・ここが E37 の置き場所＝実行のたびに手で入れない）──
#   ★運用の下限は PDCA で見直してよい。変えたら reason と date を必ず書く（黙って下げない）。
#     役割の下限（台帳 ROLE_FLOOR scalp=5）を下回るのは「調整」でなく「役割を変える決定」。
STOP_RULES = {
    "delta_net": 20.0,          # 値決め窓4ヶ月の net で $20＝月$5 相当。これ以下の伸びは誤差に埋もれる
    "n_max": 500,               # 30分で約690試行が回る実測（1試行2.6秒）。余裕を持たせた数
    "atr_band_edges": list(e37.V17_ATR_BAND_EDGES),   # 実体から取る＝数字を書き写さない（ARC31/ARC32 の層化）
    "ops_min_per_day": None,    # 運用の下限（未設定＝役割の下限 5 で判定する）
    "ops_reason": "未設定",
    "ops_date": None,
}


def stop_rules(logic_id: str) -> dict:
    """終わりの条件の値。E37 は設定ファイルを持たないので本ファイルが置き場所。"""
    return dict(STOP_RULES)


def baseline(logic_id: str) -> dict | None:
    """土台＝採用土台 v59d_164 の値（B1・B2 の比較相手・2026-07-27 まこさん OK）。

    ★空の辞書を返す＝run() が値を1つも上書きしない＝e37_scalp のモジュール定数そのまま。
      それが採用土台の値。ここに数字を書き写さない（書き写すと実体とずれる）。
    """
    return {} if logic_id in ({"v59"} | set(RECIPES)) else None


def coverage(logic_id: str) -> list[str]:
    """この探索が触れる指標の列（＝網羅度の分子・2026-07-27 まこさん OK・監査 提案1）。

    v59 の急騰の判定に使えるシグナルは _SIGS の4種だけ。どれも5分足で、時間足は選べない。
    分母は observe_diag の指標カタログ（96種 × 8足 = 768列）。
    """
    if logic_id != "v59":
        return []
    return [f"{s}_5m" for s in _SIGS]


def exit_keys() -> set:
    """E37 は入口と出口が一枚岩で分かれていない＝全部まとめて run へ渡す。"""
    return set()


def series_bank(win: pd.DataFrame) -> dict:
    """quantile 型の宣言が参照する分布（値決め窓の中だけ）。
    kij_dev＝基準線（26本の高安の中値）からの乖離%＝engine_search_e37._kij_range と同じ式。"""
    kij = (win["high"].rolling(26).max() + win["low"].rolling(26).min()) / 2.0
    dev = ((win["close"] / kij) - 1.0) * 100.0
    return {"kij_dev": dev.dropna()}


def fixed(logic_id: str, space_names) -> tuple[dict, dict]:
    """設定ファイルの確定値。E37 は土台の構成が BASE_KW に固定なので、毎試行に混ぜる値は無い。"""
    return {}, {}


def min_per_day(logic_id: str):
    """件数/日 の下限。E37 はまだ設定していない（値はまこさんが決める）。"""
    return None


def load_windows(windows, warm: pd.Timedelta) -> list[pd.DataFrame]:
    """窓ごとのデータを作る。生データの読み込みは1回だけ。
    ★E37 は指標を run_e37 が内部で作るので、ここでは助走込みのスライスを返すだけ。"""
    lo = min(w[0] for w in windows) - warm
    raw = e37._load(0, start_override=str(lo.date()))
    return [raw[(raw["ts"] >= s - warm) & (raw["ts"] < e)].reset_index(drop=True).copy()
            for (s, e) in windows]


def _prepared(df: pd.DataFrame) -> pd.DataFrame:
    """レシピの共通売買ループが要る指標つきデータ（作り方は E38 の接続ファイルと同じ）。

    同じ窓のデータは1回だけ作って使い回す（毎試行作り直すと1試行の時間が跳ね上がるため）。
    """
    key = (id(df), len(df))
    hit = _PREPARED.get(key)
    if hit is not None:
        return hit
    import e38_logic_parts as parts
    from tuner_adapters import e38 as _e38
    cfg = _e38.config()
    ak = e37.V25_K if cfg["global"].get("regime", {}).get("v25_adaptive_band") else None
    out = parts.prepare_df(df.copy(), adaptive_k=ak)
    if len(_PREPARED) >= 2:                                # 値決め窓と確認窓の2つだけ持てば足りる
        _PREPARED.clear()
    _PREPARED[key] = out
    return out


def _apply_s1(recipe: dict, p: dict) -> None:
    """S1 の値をレシピへ入れる（段1＝v59 の枝の値だけ・space() が開いた7個と1対1）。"""
    bx = {b["name"]: b for b in recipe["exits"]}
    dn, fl = bx["V59DOWN"], bx["V59FLAT"]
    if "th_down_di14" in p:                                # down 型のしきい値（DI差14）
        dn["fire"]["all"][0]["value"] = {"legacy": float(p["th_down_di14"])}
    if "th_flat_kijun26" in p:                             # flat_up 型のしきい値（基準線乖離26%）
        fl["fire"]["all"][0]["value"] = {"legacy": float(p["th_flat_kijun26"])}
    if "V59_DOWN_ADV_PCT" in p:                            # 建値からの逆行%（%→比率）
        dn["exec"]["placement"]["level"]["k"] = {"legacy": float(p["V59_DOWN_ADV_PCT"]) / 100.0}
    if "V59_FLAT_ADV_PCT" in p:
        fl["exec"]["placement"]["level"]["k"] = {"legacy": float(p["V59_FLAT_ADV_PCT"]) / 100.0}
    wait = p.get("V59_WAIT_MIN")
    for b, win_key in ((dn, "V59_DOWN_WIN_MIN"), (fl, "V59_FLAT_WIN_MIN")):
        sc = b["scope"]["hold_min"]                        # [待ち時間の下限, 効く窓の上限]（分）
        if wait is not None:
            sc[0] = int(wait)
        if win_key in p:
            sc[1] = None if int(p[win_key]) == 0 else int(p[win_key])   # 0＝窓なし（e37 と同じ意味）


def _apply_l1(recipe: dict, p: dict) -> None:
    """L1 の値をレシピへ入れる（段1＝損切りの帯幅の倍率だけ）。"""
    bx = {b["name"]: b for b in recipe["exits"]}
    if "sl_zone_k" in p:
        bx["SL"]["exec"]["placement"]["level"]["k"] = {"legacy": float(p["sl_zone_k"])}


def _run_recipe_logic(df: pd.DataFrame, logic_id: str, p: dict) -> pd.DataFrame:
    """レシピ経由で1試行を走らせる（歩6・監査 4-17）。値を1つも渡さなければ採用土台そのもの。"""
    import engine_tuner_exec as ex
    recipe = _recipe(logic_id)
    (_apply_s1 if logic_id == "S1" else _apply_l1)(recipe, p)
    dfx = ex.attach_recipe_columns(_prepared(df), recipe)
    trades, _rep = ex.run_recipe(dfx, recipe)
    return pd.DataFrame(trades)


def run(df: pd.DataFrame, logic_id: str, entry_params: dict, exit_params: dict) -> pd.DataFrame:
    """値を1組受け取って売買記録を返す（1試行の中身）。

    S1 と L1 はレシピ経由（歩6・監査 4-17）。v59 は従来どおり一枚岩の run_e37 を呼ぶ。
    一枚岩の側は、モジュール定数を書き換えて run_e37 を呼び、**必ず元へ戻す**
    （戻さないと次の試行が汚れる）。選ばれたシグナルに対応する閾値だけを、エンジンが見る定数へ入れる。
    """
    p = {**entry_params, **exit_params}
    if logic_id in RECIPES:
        return _run_recipe_logic(df, logic_id, p)
    ov = {k: v for k, v in p.items() if k.startswith("V59_")}
    if not ov:                                     # ★値を1つも渡さない＝土台（採用 v59d_164 の定数のまま）
        return e37.run_e37(df.copy(), "5m", tag=None, v59_adx_cut=True, return_trades=True, **BASE_KW)
    ds, fs = p["V59_DOWN_SIG"], p["V59_FLAT_SIG"]
    for s, key, dst in ((ds, f"th_down_{ds}", "V59_DOWN_ADX7_TH"), (fs, f"th_flat_{fs}", "V59_FLAT_DID7_TH")):
        if key not in p:
            raise SystemExit(f"[設定エラー] シグナル {s} に対応する閾値 {key} が無い")
        ov[dst] = float(p[key])
    saved = {k: getattr(e37, k) for k in ov}
    for k, v in ov.items():
        setattr(e37, k, v)
    try:
        t = e37.run_e37(df.copy(), "5m", tag=None, v59_adx_cut=True, return_trades=True, **BASE_KW)
    finally:
        for k, v in saved.items():
            setattr(e37, k, v)
    return t
