#!/usr/bin/env python3
"""e37_range_scalp.py — E37 レンジ・スキャル MVP（両サイド・確認済みエッジ＋S/R幾何のレンジ学習ゲート）

★このファイルは E37 専用。E36 / E35 を import しない（兄弟・独立＝切り分け原則）。
  共通土台（① 読み込み方 / ⑤ cap検査・funding / ⑥ 出力処理 / ⑦ 取引所・予算の定数）は strat_base から import。
  戦略ロジック（② レンジ学習ゲート・入口信号 / ③ 両サイド スキャル売買エンジン）は本ファイルが自前。

位置づけ（acceptance.md・§1.2.1 局面3 レンジ スキャル型・E36 デイトレと住み分け）:
  E37 v2（出来高スパイク fade SHORT）は入口の向きが逆（N11 方向ミス）で手数料負け。本 MVP は入口を
  「両窓で手数料を超えた確認済みレンジ逆張りエッジ（下端/上端＋ダイバ＋高ATR）」＋「S/R幾何のレンジ学習ゲート」に
  差し替える。関門（まこさんのレンジ判定の自動再現）を、硬い1本のルールでなく検証済み S/R幾何を LogisticRegression で
  束ねた連続スコア range_score で解く。判定は score.py の数字（本スクリプトは eval_engine 定数を import のみ＝審判が独立再計算）。
  ⑥ 出力・使用パラメータ サイドカー（write_sidecar）は strat_base._output_and_report 経由（各戦略で手書きしない）。

入口（両サイド・acceptance §やること4）:
  long_sig  = (range_score≥THR) ∩ (dev_z≤Z_LO) ∩ bull_div ∩ (atr_pct≥ATR_HI)
  short_sig = (range_score≥THR) ∩ (dev_z≥Z_HI) ∩ bear_div ∩ (atr_pct≥ATR_HI)
    range_score = e35_box の S/R幾何(box_strength/sup/res_dist)＋donchian幅・往復回数 を LogisticRegression で束ねた
                  「レンジらしさ点数」。教師=regime_ground_truth_daily_human.csv の range・学習窓の行だけで fit（leak-safe）。
    THR   = 学習窓の range 比率に一致させる分位（a-priori base-rate match・sweep しない）。
    Z_LO/Z_HI = 学習窓 dev_z の q25 / q75（a-priori 分位）。ATR_HI = 学習窓 atr_pct の q(2/3)。
    bull_div = 価格12本安値更新 ∩〔taker_ls あり→taker_ls は12本安値を更新せず / taker_ls 無→RSI14 が12本安値を更新せず〕。bear_div は mirror。

出口（スキャル＝浅く速く・H5 約定・新 exit_reason を作らない＝既存登録名のみ・H13）:
  TP_FILLED(maker指値): 平均(SMA)へ戻り＝小さい戻りで即利確。手数料床 SCALP_FLOOR を超える時だけ武装。
  TIME_EXIT(成行taker): 初回entryから T_MAX 本(=30分)で未決済なら撤退（スキャル＝短保有）。
  SL_FILLED(maker指値): 建値±K_SL×ATR＝ATR スケール SL（固定%でない・maker モデル）。

H 制約（acceptance.md §4.6）:
  H1 cap … MAX_ADDS=1（size=UNIT 0.024・単一スロット）＝合計≤0.12 自明＋_verify_cap 実測 assert。
  H2 leak … 特徴は当該足まで（causal）・range_score の fit は学習窓の行のみ・1h/4h は確定足のみ(add_box_features)・出口は約定 bar の次以降・未来参照(負shift/中央窓)を grep assert。
  H5 約定 … entry=指値maker / TP=指値maker / SL=指値maker / time-exit=成行taker＋slip。
  H6 価格非依存 … dev_z/atr_pct/box系/donchian幅=%比率・divergence=符号・TP/SL=ATR比。USD 絶対値の閾値/ラベルなし。
  H8 期間 … 分位・range_score fit は学習窓（periods import・手打ちなし）・採点窓不参照・封印不参照。
  H13 judge … 新 exit_reason を作らない・score.py/eval_engine を触らない（import のみ）。
  H15 ボラ逃げ … 方向=位置(dev_z)＋ダイバ＋range_score（方向シグナル）・atr_pct は高ATR時のみ入口を許すフィルタ＝大きさ予測でない。
  H16 1変更 … E37 の入口を1本 新設（確認済みエッジ＋レンジ学習ゲート）。
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
import e34_range_base as e34b                  # noqa: E402  add_analysis_features（stoch_k 等・記録用）
import e35_box                                 # noqa: E402  箱特徴（フラクタルS/R・box_strength/sup/res_dist・5m/1h/4h）
import periods                                 # noqa: E402  検証期間の唯一の正本（SSOT）
import strat_base                              # noqa: E402  ★全戦略共通の土台
from strat_base import UNIT, CAP, TTL, ENTRY_OFFSET, load_5m, _verify_cap, _funding_cost  # noqa: E402
from periods import TRAIN_END as _P_TRAIN_END  # noqa: E402,F401  SSOT（境界は periods 由来・手打ち禁止 H8）

from sklearn.linear_model import LogisticRegression  # noqa: E402
from sklearn.preprocessing import StandardScaler      # noqa: E402

# ── 検証期間（periods.py が唯一の正本・SSOT・手打ち禁止）──
TRAIN_END = periods.TRAIN_END              # 学習境界（< TRAIN_END で分位 fit・range_score fit）
SC_START = periods.SCORE_START             # 採点窓 開始（2025-06-01）
SCORE_END = periods.SEAL_START             # 採点スライスの排他終端＝封印開始
SEAL_START = periods.SEAL_START            # 封印開始（不参照）

DATA = e34v1.CSV.parent                     # data/ ディレクトリ（絶対パスを手打ちしない）
HUMAN_CSV = DATA / "regime_ground_truth_daily_human.csv"   # まこさん手動 regime ラベル（range_score の教師）
OI_CSV = DATA / "oi_BTCUSDT_5y.csv"                         # taker_ls（ダイバ判定・無い期間は RSI fallback）

# ── E37 MVP 戦略パラメータ（全て a-priori or 学習窓分位・採点窓でスイープしない L-267）──
PRIORITY = 37
MAX_ADDS = 1                  # スキャル＝単発（単一スロット・cap 0.12 自明）
W_GEO = 288                   # レンジ幾何の causal 窓＝過去1日（5m×288・a-priori）
DIV_N = 12                    # ダイバ判定の lookback（12本=60分・a-priori・probe と同じ）
RSI_N = 14                    # RSI（taker_ls 無い期間の fallback・a-priori）
Z_LO_Q, Z_HI_Q = 0.25, 0.75  # 入口 dev_z 分位（下端 q25 / 上端 q75・学習窓 fit）
ATR_HI_Q = 2.0 / 3.0         # 高ATR フィルタ分位（学習窓 fit）
SCALP_FLOOR = 0.0008          # TP 武装の手数料床 0.08%（実 maker 往復0.028%の約3倍・a-priori）
T_MAX = 6                     # 時間切れ＝6本=30分（スキャル短保有・a-priori）
K_SL = 1.5                    # SL 幅＝建値±K_SL×ATR（ATR スケール・a-priori）
# range_score の材料＝検証済み S/R幾何（e35_box）＋causal な幅・往復（束ねて連続スコア＝硬い1本ルールでない）
SCORE_FEATS = ["box_strength__5m", "box_strength__1h", "box_strength__4h",
               "box_sup_dist__1h", "box_res_dist__1h", "box_sup_dist__4h", "box_res_dist__4h",
               "donch_width_pct", "flips"]


# ══ ② 特徴量（全て当該足まで＝leak-safe H2・価格非依存 H6）══
def _merge_taker_ls(df: pd.DataFrame) -> pd.DataFrame:
    """taker_ls（買い/売り比）を 5m へ backward-merge（確定値のみ・当該足まで）。oi データ末以降は NaN（→ RSI fallback）。"""
    oi = pd.read_csv(OI_CSV, parse_dates=["time"])[["time", "taker_ls"]]
    df = pd.merge_asof(df.sort_values("ts"), oi.sort_values("time"),
                       left_on="ts", right_on="time", direction="backward", tolerance=pd.Timedelta("5min"))
    return df.drop(columns=["time"]).reset_index(drop=True)


def _add_geo(df: pd.DataFrame) -> pd.DataFrame:
    """causal なレンジ幾何: donchian幅%（過去W の値幅／close）と往復回数 flips（中心線を跨いだ回数）。全て過去のみ＝leak-safe。"""
    c = df["close"]
    box_hi = df["high"].rolling(W_GEO).max()
    box_lo = df["low"].rolling(W_GEO).min()
    mid = (box_hi + box_lo) / 2.0
    df["donch_width_pct"] = (box_hi - box_lo) / c                       # 値幅（狭い=レンジ寄り）
    df["flips"] = (c > mid).astype(float).diff().abs().rolling(W_GEO).sum()   # 中心線の往復（多い=行き来）
    return df


def _add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    """RSI14（taker_ls 無い期間のダイバ fallback・当該足まで＝leak-safe・0-100 無次元）。"""
    d = df["close"].diff()
    up = d.clip(lower=0).rolling(RSI_N).mean()
    dn = (-d.clip(upper=0)).rolling(RSI_N).mean().replace(0, np.nan)
    df["rsi14"] = 100.0 - 100.0 / (1.0 + up / dn)
    df["atr_pct"] = df["atr"] / df["close"] * 100.0                     # 高ATR フィルタ用（%＝価格非依存 H6）
    return df


def _add_divergence(df: pd.DataFrame) -> pd.DataFrame:
    """強気/弱気ダイバ: 価格が DIV_N 本の安値/高値を更新したのに、需給指標（taker_ls／無ければ RSI14）が更新しない背離。
    taker_ls あり=probe と同式（px_lo ∩ ~tls_lo）。taker_ls 無=RSI で代替（px_lo ∩ ~rsi_lo）。全て当該足まで＝leak-safe。"""
    c = df["close"]
    px_lo = c <= c.rolling(DIV_N).min()
    px_hi = c >= c.rolling(DIV_N).max()
    tls = df["taker_ls"]
    has_tls = tls.notna()
    tls_lo = tls <= tls.rolling(DIV_N).min()
    tls_hi = tls >= tls.rolling(DIV_N).max()
    rsi = df["rsi14"]
    rsi_lo = rsi <= rsi.rolling(DIV_N).min()
    rsi_hi = rsi >= rsi.rolling(DIV_N).max()
    div_lo = has_tls.where(has_tls, other=False) & tls_lo | (~has_tls) & rsi_lo   # 需給が安値更新
    div_hi = has_tls & tls_hi | (~has_tls) & rsi_hi                               # 需給が高値更新
    df["bull_div"] = (px_lo & ~div_lo).fillna(False)      # 価格は安値更新・需給は更新せず＝強気背離
    df["bear_div"] = (px_hi & ~div_hi).fillna(False)      # 価格は高値更新・需給は更新せず＝弱気背離
    return df


def _add_labels(df: pd.DataFrame) -> pd.DataFrame:
    """まこさん手動 regime ラベル（range/uptrend/downtrend）を各5mバーの日付へ貼る（range_score の教師）。"""
    human = pd.read_csv(HUMAN_CSV, parse_dates=["date"])
    rmap = dict(zip(human["date"].dt.normalize(), human["label"]))
    lab = df["ts"].dt.normalize().map(rmap)
    df["reg_label"] = lab
    df["is_range"] = (lab == "range").astype(float)
    return df


# ══ ② レンジ学習ゲート range_score（S/R幾何を LogisticRegression で束ねる・学習窓のみ fit＝leak-safe H2/H8）══
def _fit_range_score(df: pd.DataFrame) -> float:
    """検証済み S/R幾何を1つの「レンジらしさ点数」range_score に束ねる。
    教師=まこさん range ラベル・fit は学習窓の行だけ（採点窓 覗き見なし）・全行に predict。THR=学習窓 range 比率分位（a-priori）。
    return THR。"""
    tr = (df["ts"] < TRAIN_END) & df["reg_label"].notna()
    feat_ok = df[SCORE_FEATS].notna().all(axis=1)
    fit_rows = tr & feat_ok
    Xtr = df.loc[fit_rows, SCORE_FEATS].to_numpy(float)
    ytr = df.loc[fit_rows, "is_range"].to_numpy(int)
    scaler = StandardScaler().fit(Xtr)
    clf = LogisticRegression(max_iter=2000, class_weight="balanced").fit(scaler.transform(Xtr), ytr)
    # 全行に predict（特徴 NaN の行は score=NaN＝入口不可）
    sc = np.full(len(df), np.nan)
    ok = df[SCORE_FEATS].notna().all(axis=1).to_numpy()
    sc[ok] = clf.predict_proba(scaler.transform(df.loc[ok, SCORE_FEATS].to_numpy(float)))[:, 1]
    df["range_score"] = sc
    base_rate = float(ytr.mean())
    THR = float(np.nanquantile(sc[df["ts"].to_numpy() < np.datetime64(TRAIN_END)], 1.0 - base_rate))
    return THR


# ══ ② 入口信号（両サイド・分位は学習窓 fit＝H8・当該足まで＝H2）══
def _build_signals(df: pd.DataFrame) -> dict:
    """long_sig / short_sig を組み立てる。range_score を fit→THR、dev_z/atr_pct 分位を学習窓で fit。
    直接式で AND（range_score/dev_z/atr_pct/*_div を連結）＝設計と一目で照合可能。"""
    THR = _fit_range_score(df)
    tr = df["ts"] < TRAIN_END
    Z_LO = float(df.loc[tr, "dev_z"].quantile(Z_LO_Q))
    Z_HI = float(df.loc[tr, "dev_z"].quantile(Z_HI_Q))
    ATR_HI = float(df.loc[tr, "atr_pct"].quantile(ATR_HI_Q))

    range_score = df["range_score"]
    dev_z = df["dev_z"]
    atr_pct = df["atr_pct"]
    bull_div = df["bull_div"].astype(bool)
    bear_div = df["bear_div"].astype(bool)
    range_ok = (range_score >= THR).fillna(False)

    long_sig = (range_ok & (dev_z <= Z_LO) & bull_div & (atr_pct >= ATR_HI)).fillna(False)
    short_sig = (range_ok & (dev_z >= Z_HI) & bear_div & (atr_pct >= ATR_HI)).fillna(False)
    df["long_sig"] = long_sig.to_numpy(bool)
    df["short_sig"] = short_sig.to_numpy(bool)
    return {"THR": THR, "Z_LO": Z_LO, "Z_HI": Z_HI, "ATR_HI": ATR_HI,
            "range_ok": range_ok, "long_sig": long_sig, "short_sig": short_sig}


def _load(smoke: int) -> pd.DataFrame:
    """① 5分足の読み込みは共通土台（strat_base.load_5m）。指標付与は E37 MVP が使う指標。"""
    df = load_5m(smoke)
    df = e34v1.add_indicators(df)                 # sma/std/dev_z/atr/adx
    df = e34b.add_analysis_features(df)           # stoch_k(14) 等（記録用）
    df = e35_box.add_box_features(df, verify_leak=(smoke > 0 and smoke <= 60000))   # box_strength/sup/res_dist（S/R幾何）
    df = _merge_taker_ls(df)                       # taker_ls（ダイバ・無い期間は RSI fallback）
    df = _add_geo(df)                             # donchian幅・往復回数（レンジ幾何）
    df = _add_rsi(df)                             # RSI14 + atr_pct
    df = _add_divergence(df)                      # bull_div / bear_div
    df = _add_labels(df)                          # is_range（range_score の教師）
    return df


# ══ ⑤(戦略別の記録) 売買記録（funding/cap は共通土台・両サイド）══
_MAKER_EXIT = ("TP_FILLED", "SL_FILLED", "EDGE_TP", "BE_EXIT", "PARTIAL_TP")   # score.py MAKER_EXIT_REASONS と一致


def _record(trades, pos, exit_price, reason, exit_idx, ts_arr):
    """1 ポジ（単発 lot・LONG/SHORT）を記録。TP_FILLED/SL_FILLED=maker（指値）・TIME_EXIT/EOD=taker。
    net = gross − entry_fee − exit_fee − slip − funding（lot fill 起点・score.py と恒等）。"""
    side = pos["side"]; sdir = 1 if side == "LONG" else -1
    exit_ts = pd.Timestamp(ts_arr[exit_idx]); exit_px = float(exit_price)
    is_taker = reason not in _MAKER_EXIT
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


# ══ ③ 両サイド スキャル売買エンジン（連続モード・単一スロット・浅TP=平均/30分time-exit/ATR-SL）══
def run_continuous(df, box_tf):
    """E37 MVP スキャル 両サイド売買エンジン（単発・単一スロット）。
    入口=指値maker（不約定は積まない）／出口=① ATR-SL(maker指値) ② 浅TP=平均(SMA)戻り(maker・手数料床武装) ③ 30分time-exit(taker)。
    全て当該足まで＝leak-safe（H2）。出口は約定 bar の次以降。"""
    n = len(df)
    ts = df["ts"].to_numpy()
    h = df["high"].to_numpy(float); l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    sma = df["sma"].to_numpy(float)
    sup = df[e35_box.sup_col(box_tf)].to_numpy(float); res = df[e35_box.res_col(box_tf)].to_numpy(float)
    Wpct = sup + res
    long_sig = df["long_sig"].to_numpy(bool); short_sig = df["short_sig"].to_numpy(bool)

    trades = []
    pos = None
    pend = None

    for i in range(n):
        # ── 1. pending fill（指値 maker・TTL3・不約定は積まない・単一スロット）──
        if pend is not None:
            el = i - pend["placed_idx"]
            filled = False
            if el > TTL:
                pend = None
            elif el >= 1:
                if pend["side"] == "LONG" and l[i] <= pend["limit"]:
                    filled = True
                elif pend["side"] == "SHORT" and h[i] >= pend["limit"]:
                    filled = True
            if filled:
                if pos is None and np.isfinite(atr[i]) and (UNIT <= CAP + 1e-9):
                    pos = {"side": pend["side"], "avg": pend["limit"], "size": UNIT, "add_count": 1,
                           "first_idx": i, "last_fill_idx": i,
                           "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i], "W_entry": Wpct[i],
                           "max_fav": (h[i] if pend["side"] == "LONG" else l[i]),
                           "max_adv": (l[i] if pend["side"] == "LONG" else h[i])}
                pend = None

        # ── 2. MFE/MAE 極値更新（記録用）──
        if pos is not None:
            if pos["side"] == "LONG":
                pos["max_fav"] = max(pos["max_fav"], h[i]); pos["max_adv"] = min(pos["max_adv"], l[i])
            else:
                pos["max_fav"] = min(pos["max_fav"], l[i]); pos["max_adv"] = max(pos["max_adv"], h[i])

        # ── 3. 出口（約定 bar の次以降＝leak-safe）──
        if pos is not None and i > pos["last_fill_idx"]:
            avg = pos["avg"]; a = pos["atr_entry"]
            if pos["side"] == "LONG":
                sl = avg - K_SL * a                                   # ① ATR-SL（下抜け・指値maker）
                if np.isfinite(sl) and l[i] <= sl:
                    _record(trades, pos, sl, "SL_FILLED", i, ts); pos = None; continue
                tp = sma[i] if np.isfinite(sma[i]) else np.nan        # ② 浅TP=平均戻り（上・手数料床武装）
                if np.isfinite(tp) and tp >= avg * (1.0 + SCALP_FLOOR) and h[i] >= tp:
                    _record(trades, pos, tp, "TP_FILLED", i, ts); pos = None; continue
            else:
                sl = avg + K_SL * a                                   # ① ATR-SL（上抜け・指値maker）
                if np.isfinite(sl) and h[i] >= sl:
                    _record(trades, pos, sl, "SL_FILLED", i, ts); pos = None; continue
                tp = sma[i] if np.isfinite(sma[i]) else np.nan        # ② 浅TP=平均戻り（下・手数料床武装）
                if np.isfinite(tp) and tp <= avg * (1.0 - SCALP_FLOOR) and l[i] <= tp:
                    _record(trades, pos, tp, "TP_FILLED", i, ts); pos = None; continue
            if (i - pos["first_idx"]) >= T_MAX:                       # ③ 時間切れ（30分・成行taker）
                _record(trades, pos, c[i], "TIME_EXIT", i, ts); pos = None; continue

        # ── 4. 入口（単一スロット・pos も pend も無い時のみ新規指値・LONG 優先で衝突は起きない[dev_z 排他]）──
        if pos is None and pend is None:
            if long_sig[i]:
                pend = {"side": "LONG", "limit": c[i] * (1.0 - ENTRY_OFFSET), "placed_idx": i}
            elif short_sig[i]:
                pend = {"side": "SHORT", "limit": c[i] * (1.0 + ENTRY_OFFSET), "placed_idx": i}

    if pos is not None:
        _record(trades, pos, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    return trades


# ══ ⑥ 出力（共通土台 strat_base._output_and_report に委譲）＋使用パラメータ（report.py 節0）══
def _param_sections(ctx: dict) -> dict:
    """E37 MVP の使用パラメータ（report.py 節0 が表示・read専用メタ・net 計算に不関与）。定数参照（手打ちしない）。"""
    return {
        "検証期間（periods正本・E31）": {
            "学習(fit)": f"〜{TRAIN_END.date()} 未満（range_score/dev_z/atr_pct 分位をここで fit）",
            "採点(公式net)": f"{SC_START.date()} 〜 {SCORE_END.date()} 未満（学習に使わない）",
            "封印(不参照)": f"{SEAL_START.date()} 以降",
        },
        "【入口】レンジ学習ゲート（S/R幾何を LogisticRegression で束ねた range_score）": {
            "材料": "box_strength(5m/1h/4h)＋box_sup/res_dist(1h/4h)＋donchian幅%＋往復回数（全て causal・当該足まで）",
            "教師/fit": f"regime_ground_truth_daily_human.csv の range・学習窓の行だけで fit（採点窓不参照・leak-safe）",
            "ゲート": f"range_score ≥ THR（THR=学習窓 range 比率分位・a-priori base-rate match・学習窓 fit={ctx['THR']:.3f}）",
        },
        "【入口】確認済みエッジ（両サイド・下端/上端＋ダイバ＋高ATR）": {
            "下端/上端(dev_z)": f"LONG=dev_z≤学習窓q{int(Z_LO_Q*100)}(={ctx['Z_LO']:+.2f}) / SHORT=dev_z≥q{int(Z_HI_Q*100)}(={ctx['Z_HI']:+.2f})",
            "ダイバ(bull/bear_div)": f"価格が{DIV_N}本安値/高値を更新∩需給(taker_ls／無ければRSI{RSI_N})は更新せず（背離）",
            "高ATRフィルタ": f"atr_pct≥学習窓q{ATR_HI_Q:.2f}(={ctx['ATR_HI']:.3f})＝高ATR時のみ入口（方向スコアの主役でない・H15）",
        },
        "【固定値】サイズ・add（スキャル＝単発・単一スロット）": {
            "予算上限": f"全建玉(LONG+SHORT)合計 {CAP} BTC（H1・全採用戦略の共有枠・1建玉でない）",
            "size": f"{UNIT} BTC・MAX_ADDS={MAX_ADDS}（単発＝1玉を速く回す）",
            "指値": f"LONG=close×(1−{ENTRY_OFFSET})／SHORT=close×(1+{ENTRY_OFFSET})・TTL {TTL}本(={TTL*5}分)・不約定は積まない（maker限定）",
            "方向": "両サイド（レンジ下端でLONG・上端でSHORT）",
        },
        "【出口】スキャル＝浅く速く（新 exit_reason を作らない）": {
            "TP利確 TP_FILLED(maker指値)": "平均(SMA)へ戻り＝小さい戻りで即利確（浅TP）",
            "TP武装条件": f"建値比 {SCALP_FLOOR*100:.2f}%(SCALP_FLOOR)を超える時だけTPを置く（小TPの手数料割れ防止）",
            "時間切れ TIME_EXIT(成行)": f"初回entryから {T_MAX}本 = {T_MAX*5}分で未決済なら撤退（スキャル＝短保有）",
            "SL損切り SL_FILLED(maker指値)": f"建値±{K_SL}×ATR＝ATR スケール SL（固定%でない・maker モデル）",
        },
        "【固定値】コスト（eval_engine・確定値・改造禁止）": {
            "maker手数料": f"{ee.MAKER_FEE*100:.3f}%", "taker手数料": f"{ee.TAKER_FEE*100:.3f}%",
            "slippage": f"{ee.SLIPPAGE*100:.3f}%（taker時のみ）", "funding": f"{ee.FUNDING_RATE_8H*100:.4f}% / 8h",
        },
        "【学習した内容】（学習窓データで決定・採点窓は使わない）": {
            "range_score(LogisticRegression)": f"S/R幾何を束ねた点数・THR={ctx['THR']:.3f}（学習窓 range 比率分位）",
            "dev_z/atr_pct 分位": f"Z_LO={ctx['Z_LO']:+.2f} / Z_HI={ctx['Z_HI']:+.2f} / ATR_HI={ctx['ATR_HI']:.3f}（学習窓 fit・採点窓不参照）",
        },
    }


def _out(t: pd.DataFrame, suffix: str, ctx: dict, tag=None) -> None:
    """E37 の出力（命名/archive/上書き防止/CSV3分割/サイドカー write_sidecar は共通土台に委譲）。"""
    strat_base._output_and_report(
        t, suffix, stem="e37_range_scalp",
        strategy="E37 レンジ・スキャル MVP（両サイド・確認済みエッジ＋S/R幾何のレンジ学習ゲート）",
        script="e37_range_scalp.py",
        sections=_param_sections(ctx), tag=tag)


def run_e37(df, box_tf, tag=None):
    """E37 MVP を回す（連続モード・両サイド・スキャル出口）。判定は score.py の数字（本関数は net を計算しない＝記録のみ）。"""
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"   # H2 自己 grep
    ctx = _build_signals(df)
    trades = run_continuous(df, box_tf)
    t = pd.DataFrame(trades)
    if len(t):
        t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
        mx = _verify_cap(trades)                       # 自己検査: cap 実測（H1・score.assert_hard_constraints と同式）
        print(f"  [自己検査 cap] 同時保有 max {mx:.4f} BTC ≤ {CAP}: {'✅' if mx <= CAP + 1e-9 else '⛔cap 超過'}")
        assert mx <= CAP + 1e-9, "cap 0.12 超過（H1 違反）"
    _out(t, f"_{box_tf}_dev", ctx, tag=tag)


def _diagnostic(df, box_tf):
    """発火ファネル（採点しない・期待件数の宣言）＝各成分が何本に削るか。"""
    ctx = _build_signals(df)
    n = len(df)
    days = max((df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
    def cnt(s): return int(np.asarray(pd.Series(s).fillna(False)).sum())
    range_ok = ctx["range_ok"]
    print("=" * 100)
    print(f"[E37 MVP 発火ファネル診断・採点しない] {n:,}本 / {days:.0f}日 / box={box_tf}")
    print(f"  THR={ctx['THR']:.3f} / Z_LO={ctx['Z_LO']:+.2f} / Z_HI={ctx['Z_HI']:+.2f} / ATR_HI={ctx['ATR_HI']:.3f}")
    print(f"  range_ok(range_score≥THR)   : {cnt(range_ok):>8,} 本（{cnt(range_ok)/n*100:.1f}%）")
    print(f"  → LONG_ENTRY 発火（下端）    : {cnt(ctx['long_sig']):>8,} 本（{cnt(ctx['long_sig'])/days:.2f} 本/日・候補）")
    print(f"  → SHORT_ENTRY 発火（上端）   : {cnt(ctx['short_sig']):>8,} 本（{cnt(ctx['short_sig'])/days:.2f} 本/日・候補）")
    print(f"  → 両サイド計 候補           : {(cnt(ctx['long_sig'])+cnt(ctx['short_sig']))/days:.2f} 本/日（実約定はTTL/単一スロットで減る）")
    print(f"  ※ E36 base=1.05件/日・E37 v2=2.08件/日。件数は本走の score 対象 CSV で確認（degenerate 点検）")
    print("=" * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-tf", choices=e35_box.TFS, default="5m")
    ap.add_argument("--smoke", type=int, default=0, help="先頭 N バーだけで動作確認")
    ap.add_argument("--diagnostic", action="store_true", help="発火ファネル（期待件数）だけ出す＝採点しない")
    ap.add_argument("--tag", default=None, help="実験タグ。指定で出力名を _<tag>_<NNN> 連番にし旧実験を archive へ退避（実験は必ず付ける）")
    a = ap.parse_args()
    print("=" * 100)
    print("[E37 MVP] レンジ・スキャル 両サイド（確認済みエッジ＋S/R幾何のレンジ学習ゲート・E36 デイトレと住み分け）")
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
