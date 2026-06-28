#!/usr/bin/env python3
"""e37_range_scalp_short.py — E37 レンジ・スキャル ショート戦略 ベース v1（MVP・新戦略）

★このファイルは E37 専用。E36（e36_short_oscillation.py）/ E35 を import しない（兄弟・独立＝切り分け原則）。
  - 共通土台（① 読み込み方 / ⑤ cap検査・funding / ⑥ 出力処理 / ⑦ 取引所・予算の定数）は strat_base から import。
  - 戦略ロジック（② 箱・レンジゲート・入口信号 / ③ スキャル売買エンジン run_continuous）は本ファイルが自前。
  - e35_box は箱特徴の共有ユーティリティ（戦略ファイルではない）。

位置づけ（設計書 e37_design.md）: §1.2.1 局面3 レンジの 2本目の柱＝スキャル型（E36=デイトレ型と住み分け）。
  E36 が「箱の極値で反転→反対端まで往復（EDGE_TP・4h保有）」を取るのに対し、E37 は
  「レンジ内の短期の買われすぎ(dev_z)→平均へ戻ったら浅く速く利確・60分時間切れ」で小波を取る。
  freq-iter2（広い入口×E36 長保有出口）が net 崩壊した正体＝長保有出口（240分 time-exit −$2,921・勝ち玉は約50分で決着）
  を、スキャル出口（浅TP・60分）で回避する（analysis_block.md / improvement_plan.md / acceptance.md）。
  判定は score.py の数字（本スクリプトは eval_engine 定数を import のみ＝審判が独立再計算）。

入口（DESIGN_CONTRACT・§5.2 と一致・_entry_contract/_assemble_signals が成分欠落で自停止＝類型G 物理防止）:
  range_ok   = er_ok ∧ in_box                                   （レンジ有効＝ER<学習分位 ∩ 箱内）
  short_entry= range_ok ∧ macd_ok ∩ ob_dev ∩ short_rev
    er_ok    = ER < 学習窓分位 q_er（Kaufman Efficiency Ratio・低い=往復=レンジ）
    in_box   = 多TFレジサポ箱の内側
    macd_ok  = 1h MACD line ≤ 0（ショート寄り regime・shortset1・符号のみ=価格非依存 H6）
    ob_dev   = dev_z ≥ 学習窓分位 z_entry（短期の買われすぎ＝箱極値を要求しない＝E36 の up_zone と別）
    short_rev= 速い %K(9) が下降転換（k9>k_hi ∩ k9<前k9・受け身指値を置かず確認後 maker 指値=contrarian）

出口（スキャル＝浅く速く・H5 約定）:
  TP_FILLED(maker指値): 短期平均へ戻り＝価格が dev_z=z_exit 水準（sma+z_exit·std）へ。手数料床(COST_FLOOR)を超える時だけ武装。
  TIME_EXIT(成行taker): 初回entryから T_MAX 本(=60分)で未決済なら撤退（スキャル＝短保有・half-life）。
  BOX_BREAK_SL(成行taker): 終値が箱上限 R を上抜け＝レンジ終了＝構造的 SL（固定%でない）。
  ＝**新 exit_reason を作らない**（既存登録名に揃え score.py 改造不要・H13・出戻り防止）。

H 制約（acceptance.md §E）:
  H1 cap … MAX_ADDS=1（size=UNIT 0.024）＝合計≤0.12 自明＋_verify_cap 実測 assert。
  H2 leak … dev_z/ER/stoch/box は当該足まで・1h は確定足のみ(attach_upper_tf)・出口は約定 bar の次以降・未来参照(負shift/中央窓)を grep assert。
  H5 約定 … entry=指値maker / TP=指値maker / time-exit・box-break=成行taker＋slip。
  H6 価格非依存 … dev_z/ER/距離%/W% は無次元・MACD 符号のみ。USD 絶対値の閾値/ラベルなし。
  H8 期間 … 分位は学習窓 fit（periods import・手打ちなし）・採点窓不参照・封印不参照。
  H13 judge … 新 exit_reason を作らない・score.py/eval_engine を触らない（import のみ）。
  H15 ボラ逃げ … ラベル=方向（短期平均へ戻り到達・二値）・dev_z は方向（買われすぎ）＝ボラ大きさ予測でない・ショート単独。
  H16 1変更 … 新戦略のベース v1 を1本（複数レバーを混ぜない）。
"""
from __future__ import annotations
import argparse
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval_engine as ee                       # noqa: E402  確定コスト定数（改造禁止・import のみ）
import e34_range_zscore_taker as e34v1         # noqa: E402  CSV / add_indicators（sma/std/dev_z/atr/adx）
import e34_range_base as e34b                  # noqa: E402  add_analysis_features（stoch 14 等）
import e35_box                                 # noqa: E402  箱特徴の共有ユーティリティ（sup_col/res_col）
import build_labels_pct as bl                  # noqa: E402  resample_ohlcv / attach_upper_tf（1h MACD・leak-safe L-128）
import periods                                 # noqa: E402  検証期間の唯一の正本（SSOT）
import strat_base                              # noqa: E402  ★全戦略共通の土台（① load_5m / ⑤ _verify_cap・_funding_cost / ⑥ _output_and_report / ⑦ 定数）
from strat_base import UNIT, CAP, TTL, ENTRY_OFFSET, COST_FLOOR, load_5m, _verify_cap, _funding_cost  # noqa: E402

# ── 検証期間（periods.py が唯一の正本・SSOT・手打ち禁止）──
TRAIN_END = periods.TRAIN_END              # 学習境界（< TRAIN_END で分位 fit）
SC_START = periods.SCORE_START             # 採点窓 開始（2025-06-01）
SCORE_END = periods.SEAL_START             # 採点スライスの排他終端＝封印開始
SEAL_START = periods.SEAL_START            # 封印開始（不参照）

# ── E37 戦略パラメータ（全て a-priori or 学習窓分位・採点窓でスイープしない L-267）──
PRIORITY = 37
MAX_ADDS = 1                  # スキャル＝単発（1玉を速く回す・cap 0.12 自明）
TFS = e35_box.TFS             # ['5m','1h','4h']
# レンジ有効ゲート（ER＝Kaufman Efficiency Ratio・E36 と同じ）
ER_N = 20                     # ER 窓
ER_SMOOTH = 5                 # 持続性（過去のみ平滑化＝flicker 抑制）
ER_Q = 0.5                    # レンジ閾値＝学習窓 ER 分位（a-priori・主役）
# 短期の行き過ぎ（dev_z=(close−SMA20)/std20・add_indicators 由来）
Z_IN_Q = 0.90                 # 入口＝学習窓 dev_z 分位（上位decile=買われすぎ・a-priori≈+1.3σ）
Z_OUT_Q = 0.65                # TP＝学習窓 dev_z 分位（平均近傍へ戻り・a-priori≈+0.4σ）
# 速い反転確認（スキャル＝E36 の %K(14) より短い 9）
K9_N = 9                      # 速い %K の窓
K_HI = 70.0                   # 買われすぎ下限
# 出口
T_MAX = 12                    # 時間切れ＝12本=60分（スキャル・短保有・a-priori）


# ══ ② レンジ判定指標（ER）＝E36 と同じ算式を E37 が自前で持つ（独立・byte 検証可）══
def add_jump_model(df: pd.DataFrame) -> pd.DataFrame:
    """Kaufman Efficiency Ratio = |C_t − C_{t−N}| / Σ|ΔC|（低い=往復=レンジ / 高い=一方向=トレンド）。
    過去のみの平滑化(ER_SMOOTH)で regime のちらつきを抑える（jump penalty 近似・leak-safe）。"""
    c = df["close"]
    change = (c - c.shift(ER_N)).abs()
    vol = c.diff().abs().rolling(ER_N).sum().replace(0, np.nan)
    df["er"] = (change / vol).rolling(ER_SMOOTH).mean()   # 持続性（過去のみ＝leak-safe）
    return df


def add_fast_stoch(df: pd.DataFrame) -> pd.DataFrame:
    """速い %K(9,3)（スキャル＝E36 の 14 より短い反転確認・全て当該足まで＝leak-safe）。
    Stochastic %K = 100×(c−min_low)/(max_high−min_low)・3本平滑。列 k9。"""
    h, l, c = df["high"], df["low"], df["close"]
    ll = l.rolling(K9_N).min(); hh = h.rolling(K9_N).max()
    df["k9"] = (100.0 * (c - ll) / (hh - ll).replace(0, np.nan)).rolling(3).mean()
    return df


def add_htf_macd(df: pd.DataFrame) -> pd.DataFrame:
    """1h MACD line(EMA12-EMA26) の符号を leak-safe に 5m へ貼る（>0=上向き=SHORT 不利・shortset1 と同算式）。
    resample_ohlcv(1h)→EMA(過去のみ)→符号→attach_upper_tf(+freq・merge_asof backward=閉じ足のみ・L-128/H2)。
    符号のみ使用＝価格非依存(H6)。列 htf_macd_up（bool・warmup=False=SHORT 許可）。"""
    px = df[["ts", "open", "high", "low", "close", "volume"]].rename(columns={"ts": "timestamp"}).set_index("timestamp")
    c1h = bl.resample_ohlcv(px, bl.RESAMPLE_RULE["1h"])["close"]
    macd = c1h.ewm(span=12, adjust=False).mean() - c1h.ewm(span=26, adjust=False).mean()   # EMA は過去のみ＝leak-safe
    up = pd.DataFrame({"htf_macd_up": (macd > 0).astype(float)}, index=c1h.index).dropna()
    merged = bl.attach_upper_tf(px[["close"]], up, "1h")
    df["htf_macd_up"] = df["ts"].map(merged["htf_macd_up"]).fillna(0.0).to_numpy() > 0.5
    return df


# ══ DESIGN_CONTRACT 自己チェック（設計通りに入口を組み立てる・成分欠落で自停止＝類型G 物理防止）══
def _entry_contract() -> dict:
    """入口の合成契約（must_combine・e37_design.md §12 / §5.2 と同一）。
    _assemble_signals がこの通りに range_ok/short_entry を AND 組み立て（成分欠落で自停止）。"""
    return {"range_ok": ["er_ok", "in_box"],
            "short_entry": ["range_ok", "macd_ok", "ob_dev", "short_rev"]}


def _assemble_signals(components: dict, must_combine: dict) -> dict:
    """must_combine の通りに合成シグナル（range_ok/short_entry）を AND 組み立てる。
    要求成分が components に無ければ即停止＝設計通りに実装しないと動かない（自己チェック・類型G物理防止）。"""
    built, pending = {}, dict(must_combine)
    for _ in range(len(pending) + 1):
        progressed = False
        for sym, parts in list(pending.items()):
            srcs = [components.get(p, built.get(p)) for p in parts]
            if any(s is None for s in srcs):
                continue
            res = srcs[0]
            for s in srcs[1:]:
                res = res & s
            built[sym] = res
            del pending[sym]
            progressed = True
        if not pending:
            return built
        if not progressed:
            missing = {sym: [p for p in parts if p not in components and p not in built]
                       for sym, parts in pending.items()}
            raise RuntimeError(
                "[設計↔実装ゲート・自己チェック] 入口契約が要求する成分が実装に無い → "
                f"{missing}。設計通りに実装してから実行（プログラムが自分で停止）。")
    return built


def _build_signals(df: pd.DataFrame, box_tf: str) -> dict:
    """入口成分（er_ok/in_box/macd_ok/ob_dev/short_rev）を計算し、契約通りに range_ok/short_entry を合成。
    z_entry/z_er は学習窓分位（< TRAIN_END）＝採点窓 覗き見なし（H8）。全て当該足まで＝leak-safe（H2）。"""
    sup = df[e35_box.sup_col(box_tf)]
    res = df[e35_box.res_col(box_tf)]
    er = df["er"]; dz = df["dev_z"]; k9 = df["k9"]; macd_up = df["htf_macd_up"]
    fill = lambda s: s.fillna(False)
    tr = df["ts"] < TRAIN_END
    er_thr = er[tr].quantile(ER_Q)              # レンジ閾値＝学習窓 ER 分位（データ駆動・覗き見なし H8）
    z_in = dz[tr].quantile(Z_IN_Q)              # 入口 dev_z 閾値＝学習窓分位（買われすぎ）

    in_box = sup.notna() & (sup > 0) & res.notna() & (res > 0)
    macd_up_bool = macd_up if macd_up.dtype == bool else (macd_up > 0.5)
    components = {
        "er_ok": fill(er < er_thr),
        "in_box": fill(in_box),
        "macd_ok": fill(~macd_up_bool),                             # 1h MACD≤0（up=False）
        "ob_dev": fill(dz >= z_in),                                 # 短期 買われすぎ（箱極値を要求しない）
        "short_rev": fill((k9 > K_HI) & (k9 < k9.shift(1))),        # 速い %K 下降転換
    }
    built = _assemble_signals(components, _entry_contract())        # ★契約通りに合成（成分欠落で自停止）
    return {**components, **built, "er_thr": float(er_thr), "z_in": float(z_in)}


def _attach_entry_cols(df: pd.DataFrame, box_tf: str) -> dict:
    """入口系列（short_entry）を df に付与＋ TP 用 dev_z 戻り閾値 z_out（学習窓分位）を返す。"""
    sig = _build_signals(df, box_tf)
    df["short_entry"] = sig["short_entry"].to_numpy()
    z_out = float(df["dev_z"][df["ts"] < TRAIN_END].quantile(Z_OUT_Q))   # TP 戻り＝学習窓 dev_z 分位（H8）
    return {**sig, "z_out": z_out}


def _load(smoke: int) -> pd.DataFrame:
    """① 5分足の読み込みは共通土台（strat_base.load_5m）。指標付与は E37 が使う指標。"""
    df = load_5m(smoke)
    df = e34v1.add_indicators(df)                 # sma/std/dev_z/atr/adx（taker は呼ばない）
    df = e34b.add_analysis_features(df)           # bb_mid_slope_pct/stoch_k(14) 等（記録用）
    df = e35_box.add_box_features(df, verify_leak=(smoke > 0 and smoke <= 60000))
    df = add_jump_model(df)                       # ER（レンジ判定）
    df = add_fast_stoch(df)                       # 速い %K(9)（反転確認）
    df = add_htf_macd(df)                         # 1h MACD 符号（ショート寄り regime）
    return df


# ══ ⑤(戦略別の記録) 売買記録（funding/cap は共通土台・E37 が自前で記録）══
def _record(trades, pos, exit_price, reason, exit_idx, ts_arr):
    """1 ポジ（単発 lot）を記録。TP=maker・time-exit/box-break/EOD=taker（reason で判定）。
    net = gross − entry_fee − exit_fee − slip − funding（lot fill 起点・score.py と恒等）。"""
    side = pos["side"]; sdir = -1                       # E37 は SHORT 専用
    exit_ts = pd.Timestamp(ts_arr[exit_idx]); exit_px = float(exit_price)
    is_taker = reason not in ("TP_FILLED", "EDGE_TP", "BE_EXIT", "PARTIAL_TP")   # TP_FILLED=maker・他=taker
    pos_id = f"{side}_{int(pos['first_idx'])}"
    atr14 = round(float(pos["atr_entry"]), 2)
    adx_e = round(float(pos["adx_entry"]), 3) if np.isfinite(pos["adx_entry"]) else None
    k_e = round(float(pos["k_entry"]), 2) if np.isfinite(pos["k_entry"]) else None
    w_e = round(float(pos["W_entry"]), 5) if np.isfinite(pos["W_entry"]) else None
    lot_idx, lp, lot_size = pos["first_idx"], float(pos["avg"]), float(pos["size"])
    entry_ts = pd.Timestamp(ts_arr[lot_idx])
    gross = (exit_px - lp) * lot_size * sdir
    entry_fee = lp * lot_size * ee.MAKER_FEE            # entry は指値 maker
    exit_fee = exit_px * lot_size * (ee.TAKER_FEE if is_taker else ee.MAKER_FEE)
    slip = (exit_px * lot_size * ee.SLIPPAGE) if is_taker else 0.0
    funding = _funding_cost(sdir, entry_ts, exit_ts, lot_size, lp)
    net = gross - entry_fee - exit_fee - slip - funding
    trades.append({
        "entry_time": entry_ts, "exit_time": exit_ts, "side": side,
        "priority": PRIORITY, "regime": "range", "position_id": pos_id, "add_count": int(pos["add_count"]),
        "size_btc": round(lot_size, 6), "entry_price": round(lp, 2), "exit_price": round(exit_px, 2),
        "exit_reason": reason, "hold_min": int((exit_idx - lot_idx) * 5),
        "atr_14": atr14, "adx_at_entry": adx_e, "stoch_k_at_entry": k_e, "box_W_pct_at_entry": w_e,
        "entry_hour": int(entry_ts.hour), "entry_weekday": int(entry_ts.weekday()),
        "mfe_usd": round((pos["max_fav"] - lp) * lot_size * sdir, 4),
        "mae_usd": round((pos["max_adv"] - lp) * lot_size * sdir, 4),
        "gross_usd": round(gross, 4), "fee_usd": round(entry_fee + exit_fee + slip, 4), "net_usd": round(net, 4),
    })


# ══ ③ スキャル売買エンジン（連続モード・SHORT 単発・浅TP/60分時間切れ/箱ブレイクSL）══
def run_continuous(df, box_tf, z_out):
    """E37 スキャル ショート売買エンジン（単発・MAX_ADDS=1）。
    入口=指値maker（不約定は積まない）／出口=① 箱ブレイクSL(taker) ② 浅TP=dev_z→z_out 戻り(maker・手数料床武装) ③ 60分time-exit(taker)。
    z_out=TP 用 dev_z 戻り閾値（学習窓分位・採点窓不参照 H8）。全て当該足まで＝leak-safe（H2）。"""
    n = len(df)
    ts = df["ts"].to_numpy()
    h = df["high"].to_numpy(float); l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    sma = df["sma"].to_numpy(float); std = df["std"].to_numpy(float)
    sup = df[e35_box.sup_col(box_tf)].to_numpy(float); res = df[e35_box.res_col(box_tf)].to_numpy(float)
    R = c * (1.0 + res / 100.0)                      # 箱上限（box-break SL 用）
    Wpct = sup + res
    short_sig = df["short_entry"].to_numpy(bool)

    trades = []
    pos = None
    pend = None

    for i in range(n):
        # ── 1. pending fill（SHORT 指値 maker・TTL3・不約定は積まない）──
        if pend is not None:
            el = i - pend["placed_idx"]
            if el > TTL:
                pend = None
            elif el >= 1 and h[i] >= pend["limit"]:
                if pos is None and np.isfinite(atr[i]) and (UNIT <= CAP + 1e-9):   # 単発＝pos 無い時のみ・H1 自明
                    pos = {"side": "SHORT", "avg": pend["limit"], "size": UNIT, "add_count": 1,
                           "first_idx": i, "last_fill_idx": i,
                           "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i], "W_entry": Wpct[i],
                           "max_fav": l[i], "max_adv": h[i]}
                pend = None

        # ── 2. MFE/MAE 極値更新（記録用・SHORT＝順行は下・逆行は上）──
        if pos is not None:
            pos["max_fav"] = min(pos["max_fav"], l[i])
            pos["max_adv"] = max(pos["max_adv"], h[i])

        # ── 3. 出口（約定 bar の次以降＝leak-safe）──
        if pos is not None and i > pos["last_fill_idx"]:
            avg = pos["avg"]
            # ① 箱ブレイク＝構造的 SL（終値が箱上限 R を上抜け・成行 taker）
            if np.isfinite(R[i]) and c[i] > R[i]:
                _record(trades, pos, c[i], "BOX_BREAK_SL", i, ts); pos = None
                continue
            # ② 浅TP（短期平均へ戻り＝dev_z=z_out 水準 sma+z_out·std・指値 maker・手数料床を超える時だけ武装）
            tp = sma[i] + z_out * std[i] if (np.isfinite(sma[i]) and np.isfinite(std[i])) else np.nan
            armed = np.isfinite(tp) and tp <= avg * (1.0 - COST_FLOOR)   # SHORT 利＝床を超える時のみ（手数料割れ防止）
            if armed and l[i] <= tp:
                _record(trades, pos, tp, "TP_FILLED", i, ts); pos = None
                continue
            # ③ 時間切れ（60分＝スキャル短保有・成行 taker）
            if (i - pos["first_idx"]) >= T_MAX:
                _record(trades, pos, c[i], "TIME_EXIT", i, ts); pos = None
                continue

        # ── 4. 入口（SHORT 単発・pos も pend も無い時のみ新規指値）──
        if short_sig[i] and pos is None and pend is None:
            pend = {"limit": c[i] * (1.0 + ENTRY_OFFSET), "placed_idx": i}

    # ── 期間末 強制クローズ ──
    if pos is not None:
        _record(trades, pos, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    return trades


# ══ ⑥ 出力（共通土台 strat_base._output_and_report に委譲）＋使用パラメータ（report.py 節0）══
def _param_sections(z_in: float, z_out: float, er_thr: float) -> dict:
    """E37 の使用パラメータ（report.py 節0 が表示・read専用メタ・net 計算に不関与）。定数参照（手打ちしない）。"""
    return {
        "検証期間（periods正本・E31）": {
            "学習(fit)": f"〜{TRAIN_END.date()} 未満（ER/dev_z 分位をここで fit）",
            "採点(公式net)": f"{SC_START.date()} 〜 {SCORE_END.date()} 未満（学習に使わない）",
            "封印(不参照)": f"{SEAL_START.date()} 以降",
        },
        "【固定値】レンジ判定ゲート（a-priori・スイープしない）": {
            "Efficiency Ratio": f"窓{ER_N}本・平滑{ER_SMOOTH}本・学習期間ERの{int(ER_Q*100)}%ile未満=低効率=レンジ（主役）",
            "箱(多TFレジサポ)": f"{list(TFS)} で 上限R＝box-break SL の枠・in_box＝レンジ内（touch-count 使わない）",
            "SHORT 入口ゲート(shortset1)": "1h MACD line≤0 のときのみ入口（符号のみ=価格非依存 H6）",
        },
        "【固定値】入口＝短期の行き過ぎ＋速い反転（E36 の箱極値 up_zone とは別・スキャルの広い入口）": {
            "短期の買われすぎ": f"dev_z=(close−SMA20)/std20 ≥ 学習窓 {int(Z_IN_Q*100)}%ile（={z_in:+.2f}・買われすぎ・箱極値を要求しない）",
            "速い反転確認": f"%K({K9_N},3) > {K_HI} かつ 下降転換（k9<前k9・受け身指値を置かず確認後 maker 指値=contrarian）",
            "ER 閾値（学習窓 fit 実値）": f"er < {er_thr:.3f}",
        },
        "【固定値】サイズ・add（スキャル＝単発）": {
            "予算上限": f"全建玉(LONG+SHORT)合計 {CAP} BTC（H1・全採用戦略の共有枠・1建玉でない）",
            "size": f"{UNIT} BTC・MAX_ADDS={MAX_ADDS}（単発＝1玉を速く回す・add しない）",
            "指値": f"close×(1+{ENTRY_OFFSET})・TTL {TTL}本(={TTL*5}分)・不約定は積まない（maker限定）",
            "方向": "SHORT 専用（LONG 入口は出さない）",
        },
        "【固定値】Exit（スキャル＝浅く速く・新 exit_reason を作らない）": {
            "TP利確 TP_FILLED(maker指値)": f"短期平均へ戻り＝価格が dev_z={int(Z_OUT_Q*100)}%ile 水準(sma+{z_out:+.2f}·std)へ（浅TP）",
            "TP武装条件": f"建値−{COST_FLOOR*100:.2f}%(COST_FLOOR)を超える時だけTPを置く（小TPの手数料割れ防止）",
            "時間切れ TIME_EXIT(成行)": f"初回entryから {T_MAX}本 = {T_MAX*5}分で未決済なら撤退（スキャル＝短保有）",
            "SL損切り BOX_BREAK_SL(成行)": "箱が壊れたら撤退（終値が上限R上抜け）＝固定%でなく構造的",
        },
        "【固定値】コスト（eval_engine・確定値・改造禁止）": {
            "maker手数料": f"{ee.MAKER_FEE*100:.3f}%", "taker手数料": f"{ee.TAKER_FEE*100:.3f}%",
            "slippage": f"{ee.SLIPPAGE*100:.3f}%（taker時のみ）", "funding": f"{ee.FUNDING_RATE_8H*100:.4f}% / 8h",
        },
        "【学習した内容】（学習窓データで決定・採点窓は使わない）": {
            "ER レンジ閾値・dev_z 入口/戻り閾値": f"学習窓 %ile で決定（er<{er_thr:.3f} / z_entry={z_in:+.2f} / z_exit={z_out:+.2f}・採点窓不参照）",
        },
    }


def _output_and_report(t: pd.DataFrame, suffix: str, z_in, z_out, er_thr, tag=None) -> None:
    """E37 の出力（命名/archive/上書き防止/CSV3分割/サイドカーは共通土台に委譲）。"""
    strat_base._output_and_report(
        t, suffix, stem="e37_range_scalp_short",
        strategy="E37 レンジ・スキャル ショート（短期dev_z入口×浅TP・60分time-exit）",
        script="e37_range_scalp_short.py",
        sections=_param_sections(z_in, z_out, er_thr), tag=tag)


def run_e37(df, box_tf, tag=None):
    """E37 ベース v1 を回す（連続モード・SHORT 単発・スキャル出口）。判定は score.py の数字（本関数は net を計算しない＝記録のみ）。"""
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"   # H2 自己 grep
    ctx = _attach_entry_cols(df, box_tf)
    z_in, z_out, er_thr = ctx["z_in"], ctx["z_out"], ctx["er_thr"]
    trades = run_continuous(df, box_tf, z_out)
    t = pd.DataFrame(trades)
    if len(t):
        t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
        mx = _verify_cap(trades)                       # 自己検査: cap 実測（H1・score.assert_hard_constraints と同式）
        print(f"  [自己検査 cap] 同時保有 max {mx:.4f} BTC ≤ {CAP}: {'✅' if mx <= CAP + 1e-9 else '⛔cap 超過'}")
        assert mx <= CAP + 1e-9, "cap 0.12 超過（H1 違反）"
    # ★出力名: 実験は必ず --tag で連番（_<tag>_<NNN>）。タグ無しの既定は dev スクラッチ名（"base" 等の採否を pre-declare する語は使わない＝採用は結果を見てから決める・まこさん 2026-06-29）。
    _output_and_report(t, f"_{box_tf}_dev", z_in, z_out, er_thr, tag=tag)


def _diagnostic(df, box_tf):
    """発火ファネル（採点しない・期待件数の宣言）＝各ゲートが何バーに削ったか・E37 の高頻度狙いと照合。"""
    sig = _build_signals(df, box_tf)
    n = len(df)
    days = max((df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
    def cnt(s): return int(np.asarray(s.fillna(False)).sum())
    print("=" * 100)
    print(f"[E37 発火ファネル診断・採点しない] {n:,}本 / {days:.0f}日 / box={box_tf} / ER閾値={sig['er_thr']:.3f} / dev_z入口閾値={sig['z_in']:+.2f}")
    print(f"  er_ok(ER<分位)         : {cnt(sig['er_ok']):>8,} 本")
    print(f"  in_box(箱内)           : {cnt(sig['in_box']):>8,} 本")
    print(f"  range_ok(er_ok∩in_box) : {cnt(sig['range_ok']):>8,} 本")
    print(f"  macd_ok(1h MACD≤0)     : {cnt(sig['macd_ok']):>8,} 本")
    print(f"  ob_dev(dev_z≥分位)     : {cnt(sig['ob_dev']):>8,} 本")
    print(f"  short_rev(速い%K反転)  : {cnt(sig['short_rev']):>8,} 本")
    print(f"  → SHORT_ENTRY 発火     : {cnt(sig['short_entry']):>8,} 本（{cnt(sig['short_entry'])/days:.2f} 本/日・候補数＝実約定はTTL/単発で減る）")
    print(f"  ※ E36 base は 1.05 件/日（デイトレ）。E37=スキャルは数倍を狙う（実際の件数は本走の score 対象 CSV で確認）")
    print("=" * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-tf", choices=TFS, default="5m")
    ap.add_argument("--smoke", type=int, default=0, help="先頭 N バーだけで動作確認")
    ap.add_argument("--diagnostic", action="store_true", help="発火ファネル（期待件数）だけ出す＝採点しない")
    ap.add_argument("--tag", default=None, help="実験タグ。指定で出力名を _<tag>_<NNN> 連番にし旧実験を archive へ退避（実験は必ず付ける）。未指定=dev スクラッチ名 _<box_tf>_dev（採否を pre-declare する語=base 等は使わない）")
    a = ap.parse_args()
    print("=" * 100)
    print("[E37] レンジ・スキャル ショート ベース v1（短期dev_z入口×浅TP・60分time-exit／E36 デイトレと住み分け）")
    df = _load(a.smoke)
    print(f"  価格 {e34v1.CSV.name}（{len(df):,}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器 maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / unit {UNIT}")
    if a.diagnostic:
        _diagnostic(df, a.box_tf)
        return
    run_e37(df, a.box_tf, tag=a.tag)
    print("=" * 100)


if __name__ == "__main__":
    main()
