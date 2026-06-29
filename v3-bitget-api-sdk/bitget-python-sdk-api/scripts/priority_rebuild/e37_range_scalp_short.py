#!/usr/bin/env python3
"""e37_range_scalp_short.py — E37 レンジ・スキャル ショート戦略 v2（入口ゼロ設計・出来高伸び切り×上位足条件×浅スキャル出口）

★このファイルは E37 専用。E36（e36_short_oscillation.py）/ E35 を import しない（兄弟・独立＝切り分け原則）。
  - 共通土台（① 読み込み方 / ⑤ cap検査・funding / ⑥ 出力処理 / ⑦ 取引所・予算の定数）は strat_base から import。
  - 戦略ロジック（② レンジゲート・入口信号 / ③ スキャル売買エンジン run_continuous）は本ファイルが自前。

位置づけ（設計書 e37_design.md v2）: §1.2.1 局面3 レンジの 2本目の柱＝スキャル型（E36=デイトレ型と住み分け）。
  ★v2 で入口をゼロ設計し直し（まこさん 2026-06-29）: v1 は「dev_z 買われすぎ→ショート」の単純逆張り（BTC で弱い・
  base-up＝RSI/z-score 逆張りは BTC で機能せず／短期反転の本体は板の需給＝5m OHLCV では出来高/VWAP が代理／
  BTC は中期トレンド優勢＝強い上昇を fade しない）。v2 は **過熱だけで入らず、出来高スパイク（買い climax の伸び切り）を
  確認できた「戻る過熱」だけ**をショートし、平均へ浅く速く利確・短い時間切れ・ATR スケール SL で回す。
  判定は score.py の数字（本スクリプトは eval_engine 定数を import のみ＝審判が独立再計算）。

入口（DESIGN_CONTRACT・acceptance §C と一致・_entry_contract/_assemble_signals が成分欠落で自停止＝類型G 物理防止）:
  short_entry = er_ok ∩ macd_ok ∩ over ∩ vol_exh ∩ rev
    er_ok    = ER < 学習窓分位 q_er（Kaufman Efficiency Ratio・低い=往復=レンジ regime）
    macd_ok  = 1h MACD line ≤ 0（ショート寄り＝上位足条件・強い上昇を fade しない・符号のみ=価格非依存 H6）
    over     = dev_z ≥ 学習窓分位 q0.75（軽い過熱＝頻度を出す・v1 の上位decile より浅い）
    vol_exh  = vol_z ≥ 1.0（出来高が rolling 平均+1σ＝買い climax の伸び切り＝質の主役・板が無い 5m での需給代理）
    rev      = 反転バー（close<open ∧ close<前close＝下げに転じた確認）

出口（スキャル＝浅く速く・H5 約定・新 exit_reason を作らない＝既存登録名のみ・H13）:
  TP_FILLED(maker指値): 平均(SMA)へ戻り＝小さい戻りで即利確。手数料床 SCALP_FLOOR を超える時だけ武装。
  TIME_EXIT(成行taker): 初回entryから T_MAX 本(=30分)で未決済なら撤退（スキャル＝短保有）。
  SL_FILLED(maker指値): 建値+K_SL×ATR＝ATR スケール SL（固定%でない・V9 placePosTpsl と同じ maker モデル・base-up §18）。

H 制約（acceptance.md §E）:
  H1 cap … MAX_ADDS=1（size=UNIT 0.024）＝合計≤0.12 自明＋_verify_cap 実測 assert。
  H2 leak … dev_z/ER/vol_z/atr/反転バーは当該足まで・1h は確定足のみ(attach_upper_tf)・出口は約定 bar の次以降・未来参照(負shift/中央窓)を grep assert。
  H5 約定 … entry=指値maker / TP=指値maker / SL=指値maker / time-exit=成行taker＋slip。
  H6 価格非依存 … dev_z/ER/vol_z(σ)/atr 倍率/床% は無次元・MACD 符号のみ。USD 絶対値の閾値/ラベルなし。
  H8 期間 … 分位は学習窓 fit（periods import・手打ちなし）・採点窓不参照・封印不参照。
  H13 judge … 新 exit_reason を作らない・score.py/eval_engine を触らない（import のみ）。
  H15 ボラ逃げ … 方向=過熱＋出来高 climax＋反転（方向シグナル）・vol_z/atr は質ゲートと出口幅＝大きさ予測でない・ショート単独。
  H16 1変更 … 新戦略の v2 を1本（入口ゼロ設計＝1コヒーレント構築）。
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
import e34_range_base as e34b                  # noqa: E402  add_analysis_features（stoch 14 等・記録用）
import e35_box                                 # noqa: E402  箱特徴の共有ユーティリティ（box_W_pct 記録用）
import build_labels_pct as bl                  # noqa: E402  resample_ohlcv / attach_upper_tf（1h MACD・leak-safe L-128）
import periods                                 # noqa: E402  検証期間の唯一の正本（SSOT）
import strat_base                              # noqa: E402  ★全戦略共通の土台（① load_5m / ⑤ _verify_cap・_funding_cost / ⑥ _output_and_report / ⑦ 定数）
from strat_base import UNIT, CAP, TTL, ENTRY_OFFSET, load_5m, _verify_cap, _funding_cost  # noqa: E402

# ── 検証期間（periods.py が唯一の正本・SSOT・手打ち禁止）──
TRAIN_END = periods.TRAIN_END              # 学習境界（< TRAIN_END で分位 fit）
SC_START = periods.SCORE_START             # 採点窓 開始（2025-06-01）
SCORE_END = periods.SEAL_START             # 採点スライスの排他終端＝封印開始
SEAL_START = periods.SEAL_START            # 封印開始（不参照）

# ── E37 v2 戦略パラメータ（全て a-priori or 学習窓分位・採点窓でスイープしない L-267）──
PRIORITY = 37
MAX_ADDS = 1                  # スキャル＝単発（1玉を速く回す・cap 0.12 自明）
TFS = e35_box.TFS             # ['5m','1h','4h']
# レンジ有効ゲート（ER＝Kaufman Efficiency Ratio）
ER_N = 20                     # ER 窓
ER_SMOOTH = 5                 # 持続性（過去のみ平滑化＝flicker 抑制）
ER_Q = 0.5                    # レンジ閾値＝学習窓 ER 分位（a-priori）
# 軽い過熱（dev_z=(close−SMA20)/std20・add_indicators 由来）
Z_IN_Q = 0.75                 # 入口＝学習窓 dev_z 分位（上位1/4＝軽い過熱・v1 の 0.90 より浅く頻度を出す）
# 出来高スパイク（買い climax の伸び切り＝板が無い 5m での需給代理・質の主役）
VOL_N = 20                    # 出来高 rolling 窓
VOL_Z_MIN = 1.0               # 出来高 z（平均+1σ）以上＝スパイク（a-priori・出来高σ由来）
# climax→反転の近接窓（過熱＆出来高 climax は「直近 L_LOOK 本以内に起きた」を取る＝同一バー要求の機構ミス回避）
L_LOOK = 3                    # 直近3本=15分（a-priori・base-up の exhaustion→reversal は別バー）
# 出口（スキャル＝浅く速く）
SCALP_FLOOR = 0.0008          # TP 武装の手数料床 0.08%（実 maker 往復0.028%の約3倍・a-priori・E37 ローカル＝strat_base 共有 COST_FLOOR を使わない）
T_MAX = 6                     # 時間切れ＝6本=30分（スキャル・短保有・v1 60分より短い・a-priori）
K_SL = 1.5                    # SL 幅＝建値+K_SL×ATR（ATR スケール・base-up §18・a-priori）


# ══ ② レンジ判定指標（ER）・出来高スパイク・1h MACD（全て当該足まで＝leak-safe H2）══
def add_jump_model(df: pd.DataFrame) -> pd.DataFrame:
    """Kaufman Efficiency Ratio = |C_t − C_{t−N}| / Σ|ΔC|（低い=往復=レンジ / 高い=一方向=トレンド）。
    過去のみの平滑化(ER_SMOOTH)で regime のちらつきを抑える（leak-safe）。"""
    c = df["close"]
    change = (c - c.shift(ER_N)).abs()
    vol = c.diff().abs().rolling(ER_N).sum().replace(0, np.nan)
    df["er"] = (change / vol).rolling(ER_SMOOTH).mean()   # 持続性（過去のみ＝leak-safe）
    return df


def add_vol_z(df: pd.DataFrame) -> pd.DataFrame:
    """出来高 z スコア vol_z = (volume − rolling平均) / rolling標準偏差（窓 VOL_N・当該足まで＝leak-safe）。
    高い vol_z＝出来高スパイク＝買い手の最後の押し込み(climax)＝枯れて戻りやすい（板が無い 5m での需給代理）。
    出来高比＝価格非依存（H6）。当該足の出来高は確定足の値＝leak なし。"""
    v = df["volume"]
    m = v.rolling(VOL_N).mean()
    s = v.rolling(VOL_N).std().replace(0, np.nan)
    df["vol_z"] = (v - m) / s
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
    """入口の合成契約（acceptance §C と同一）。_assemble_signals がこの通りに short_entry を AND 組み立て（成分欠落で自停止）。"""
    return {"short_entry": ["er_ok", "macd_ok", "over", "vol_exh", "rev"]}


def _assemble_signals(components: dict, must_combine: dict) -> dict:
    """must_combine の通りに合成シグナル（short_entry）を AND 組み立てる。
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


def _build_signals(df: pd.DataFrame, drop_vol: bool = False) -> dict:
    """入口成分（er_ok/macd_ok/over/vol_exh/rev）を計算し、契約通りに short_entry を合成。
    分位は学習窓（< TRAIN_END）＝採点窓 覗き見なし（H8）。全て当該足まで＝leak-safe（H2）。
    drop_vol=True で vol_exh を恒真にする＝出来高 ON/OFF 対照（F④・H-d 自己検査用）。"""
    er = df["er"]; dz = df["dev_z"]; vz = df["vol_z"]; macd_up = df["htf_macd_up"]
    op = df["open"]; cl = df["close"]
    fill = lambda s: s.fillna(False)
    tr = df["ts"] < TRAIN_END
    er_thr = er[tr].quantile(ER_Q)              # レンジ閾値＝学習窓 ER 分位（データ駆動・覗き見なし H8）
    z_in = dz[tr].quantile(Z_IN_Q)              # 入口 dev_z 閾値＝学習窓分位（軽い過熱）

    macd_up_bool = macd_up if macd_up.dtype == bool else (macd_up > 0.5)
    # 直近 L_LOOK 本以内の最大（setup＝過熱/climax が「最近 起きた」・rolling max は過去+当該足＝leak-safe）
    dz_recent = dz.rolling(L_LOOK).max()
    vz_recent = vz.rolling(L_LOOK).max()
    vol_exh = pd.Series(True, index=df.index) if drop_vol else fill(vz_recent >= VOL_Z_MIN)
    components = {
        "er_ok": fill(er < er_thr),                                  # レンジ regime
        "macd_ok": fill(~macd_up_bool),                             # 1h MACD≤0（上位足条件）
        "over": fill(dz_recent >= z_in),                            # 直近に軽い過熱（買われすぎ setup）
        "vol_exh": vol_exh,                                          # 直近に出来高スパイク（買い climax の伸び切り setup）
        "rev": fill((cl < op) & (cl < cl.shift(1))),               # 反転バー（下げに転じた trigger・現在バー）
    }
    built = _assemble_signals(components, _entry_contract())        # ★契約通りに合成（成分欠落で自停止）
    return {**components, **built, "er_thr": float(er_thr), "z_in": float(z_in)}


def _attach_entry_cols(df: pd.DataFrame) -> dict:
    """入口系列（short_entry）を df に付与（TP 目標は平均=SMA＝固定の戻り閾値は使わない）。"""
    sig = _build_signals(df)
    df["short_entry"] = sig["short_entry"].to_numpy()
    return sig


def _load(smoke: int) -> pd.DataFrame:
    """① 5分足の読み込みは共通土台（strat_base.load_5m）。指標付与は E37 v2 が使う指標。"""
    df = load_5m(smoke)
    df = e34v1.add_indicators(df)                 # sma/std/dev_z/atr/adx（taker は呼ばない）
    df = e34b.add_analysis_features(df)           # stoch_k(14) 等（記録用）
    df = e35_box.add_box_features(df, verify_leak=(smoke > 0 and smoke <= 60000))   # box_W_pct 記録用
    df = add_jump_model(df)                       # ER（レンジ判定）
    df = add_vol_z(df)                            # 出来高スパイク（買い climax の伸び切り）
    df = add_htf_macd(df)                         # 1h MACD 符号（上位足条件）
    return df


# ══ ⑤(戦略別の記録) 売買記録（funding/cap は共通土台・E37 が自前で記録）══
def _record(trades, pos, exit_price, reason, exit_idx, ts_arr):
    """1 ポジ（単発 lot）を記録。TP_FILLED/SL_FILLED=maker（指値）・time-exit/EOD=taker（reason で判定・score.py と一致）。
    net = gross − entry_fee − exit_fee − slip − funding（lot fill 起点・score.py と恒等）。"""
    side = pos["side"]; sdir = -1                       # E37 は SHORT 専用
    exit_ts = pd.Timestamp(ts_arr[exit_idx]); exit_px = float(exit_price)
    is_taker = reason not in ("TP_FILLED", "SL_FILLED", "EDGE_TP", "BE_EXIT", "PARTIAL_TP")   # TP/SL=指値maker・他=taker（score.py MAKER_EXIT_REASONS と一致）
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


# ══ ③ スキャル売買エンジン（連続モード・SHORT 単発・浅TP=平均/30分time-exit/ATR-SL）══
def run_continuous(df, box_tf):
    """E37 v2 スキャル ショート売買エンジン（単発・MAX_ADDS=1）。
    入口=指値maker（不約定は積まない）／出口=① ATR-SL(maker指値) ② 浅TP=平均(SMA)戻り(maker・手数料床武装) ③ 30分time-exit(taker)。
    全て当該足まで＝leak-safe（H2）。出口は約定 bar の次以降。"""
    n = len(df)
    ts = df["ts"].to_numpy()
    h = df["high"].to_numpy(float); l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    sma = df["sma"].to_numpy(float)
    sup = df[e35_box.sup_col(box_tf)].to_numpy(float); res = df[e35_box.res_col(box_tf)].to_numpy(float)
    Wpct = sup + res                                  # 記録用（box 幅）
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
            # ① ATR-SL（建値+K_SL×ATR 上抜け＝指値 maker・V9 placePosTpsl と同モデル・SL_FILLED）
            atr_sl = avg + K_SL * pos["atr_entry"]
            if np.isfinite(atr_sl) and h[i] >= atr_sl:
                _record(trades, pos, atr_sl, "SL_FILLED", i, ts); pos = None
                continue
            # ② 浅TP（平均=SMA へ戻り＝小さい戻りで即利確・指値 maker・手数料床 SCALP_FLOOR を超える時だけ武装）
            tp = sma[i] if np.isfinite(sma[i]) else np.nan
            armed = np.isfinite(tp) and tp <= avg * (1.0 - SCALP_FLOOR)   # SHORT 利＝床を超える時のみ（手数料割れ防止）
            if armed and l[i] <= tp:
                _record(trades, pos, tp, "TP_FILLED", i, ts); pos = None
                continue
            # ③ 時間切れ（30分＝スキャル短保有・成行 taker）
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
def _param_sections(z_in: float, er_thr: float) -> dict:
    """E37 v2 の使用パラメータ（report.py 節0 が表示・read専用メタ・net 計算に不関与）。定数参照（手打ちしない）。"""
    return {
        "検証期間（periods正本・E31）": {
            "学習(fit)": f"〜{TRAIN_END.date()} 未満（ER/dev_z 分位をここで fit）",
            "採点(公式net)": f"{SC_START.date()} 〜 {SCORE_END.date()} 未満（学習に使わない）",
            "封印(不参照)": f"{SEAL_START.date()} 以降",
        },
        "【入口】レンジ regime ＋ 上位足条件": {
            "Efficiency Ratio": f"窓{ER_N}本・平滑{ER_SMOOTH}本・学習期間ERの{int(ER_Q*100)}%ile未満=低効率=レンジ（学習窓 fit={er_thr:.3f}）",
            "上位足条件(macd_ok)": "1h MACD line≤0 のときのみ入口（強い上昇を fade しない・符号のみ=価格非依存 H6）",
        },
        "【入口】軽い過熱＋出来高伸び切り＋反転（v2＝過熱だけで入らない・setup→trigger 分離）": {
            "軽い過熱(over・setup)": f"直近{L_LOOK}本以内に dev_z=(close−SMA20)/std20 ≥ 学習窓 {int(Z_IN_Q*100)}%ile（={z_in:+.2f}・v1 の90%ile より浅く頻度を出す）",
            "出来高スパイク(vol_exh・setup)": f"直近{L_LOOK}本以内に vol_z=(volume−rolling{VOL_N}平均)/std ≥ {VOL_Z_MIN}σ＝買い climax の伸び切り（質の主役・板が無い5mでの需給代理）",
            "反転バー(rev・trigger)": "現在バーが close<open かつ close<前close（下げに転じた確認＝同一バー要求の機構ミス回避・確認後 maker 指値=contrarian）",
        },
        "【固定値】サイズ・add（スキャル＝単発）": {
            "予算上限": f"全建玉(LONG+SHORT)合計 {CAP} BTC（H1・全採用戦略の共有枠・1建玉でない）",
            "size": f"{UNIT} BTC・MAX_ADDS={MAX_ADDS}（単発＝1玉を速く回す・add しない）",
            "指値": f"close×(1+{ENTRY_OFFSET})・TTL {TTL}本(={TTL*5}分)・不約定は積まない（maker限定）",
            "方向": "SHORT 専用（LONG 入口は出さない）",
        },
        "【出口】スキャル＝浅く速く（新 exit_reason を作らない）": {
            "TP利確 TP_FILLED(maker指値)": "平均(SMA)へ戻り＝小さい戻りで即利確（浅TP）",
            "TP武装条件": f"建値−{SCALP_FLOOR*100:.2f}%(SCALP_FLOOR)を超える時だけTPを置く（小TPの手数料割れ防止・実maker往復0.028%の約3倍）",
            "時間切れ TIME_EXIT(成行)": f"初回entryから {T_MAX}本 = {T_MAX*5}分で未決済なら撤退（スキャル＝短保有）",
            "SL損切り SL_FILLED(maker指値)": f"建値+{K_SL}×ATR を上抜けで損切り（ATR スケール＝固定%でない・V9 placePosTpsl と同 maker モデル）",
        },
        "【固定値】コスト（eval_engine・確定値・改造禁止）": {
            "maker手数料": f"{ee.MAKER_FEE*100:.3f}%", "taker手数料": f"{ee.TAKER_FEE*100:.3f}%",
            "slippage": f"{ee.SLIPPAGE*100:.3f}%（taker時のみ）", "funding": f"{ee.FUNDING_RATE_8H*100:.4f}% / 8h",
        },
        "【学習した内容】（学習窓データで決定・採点窓は使わない）": {
            "ER レンジ閾値・dev_z 入口閾値": f"学習窓 %ile で決定（er<{er_thr:.3f} / z_entry={z_in:+.2f}・採点窓不参照）",
        },
    }


def _output_and_report(t: pd.DataFrame, suffix: str, z_in, er_thr, tag=None) -> None:
    """E37 の出力（命名/archive/上書き防止/CSV3分割/サイドカーは共通土台に委譲）。"""
    strat_base._output_and_report(
        t, suffix, stem="e37_range_scalp_short",
        strategy="E37 レンジ・スキャル ショート v2（出来高伸び切り×上位足条件×浅TP/30分time-exit/ATR-SL）",
        script="e37_range_scalp_short.py",
        sections=_param_sections(z_in, er_thr), tag=tag)


def run_e37(df, box_tf, tag=None):
    """E37 v2 を回す（連続モード・SHORT 単発・スキャル出口）。判定は score.py の数字（本関数は net を計算しない＝記録のみ）。"""
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"   # H2 自己 grep
    ctx = _attach_entry_cols(df)
    z_in, er_thr = ctx["z_in"], ctx["er_thr"]
    trades = run_continuous(df, box_tf)
    t = pd.DataFrame(trades)
    if len(t):
        t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
        mx = _verify_cap(trades)                       # 自己検査: cap 実測（H1・score.assert_hard_constraints と同式）
        print(f"  [自己検査 cap] 同時保有 max {mx:.4f} BTC ≤ {CAP}: {'✅' if mx <= CAP + 1e-9 else '⛔cap 超過'}")
        assert mx <= CAP + 1e-9, "cap 0.12 超過（H1 違反）"
    # ★出力名: 実験は必ず --tag で連番（_<tag>_<NNN>）。タグ無しの既定は dev スクラッチ名（"base" 等の採否を pre-declare する語は使わない）。
    _output_and_report(t, f"_{box_tf}_dev", z_in, er_thr, tag=tag)


def _diagnostic(df, box_tf):
    """発火ファネル（採点しない・期待件数の宣言）＋出来高 ON/OFF 対照（F④・H-d）。"""
    sig = _build_signals(df)
    sig_novol = _build_signals(df, drop_vol=True)        # 出来高条件を外した版（対照）
    n = len(df)
    days = max((df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
    def cnt(s): return int(np.asarray(s.fillna(False)).sum())
    print("=" * 100)
    print(f"[E37 v2 発火ファネル診断・採点しない] {n:,}本 / {days:.0f}日 / box={box_tf} / ER閾値={sig['er_thr']:.3f} / dev_z入口閾値={sig['z_in']:+.2f}")
    print(f"  er_ok(ER<分位レンジ)   : {cnt(sig['er_ok']):>8,} 本")
    print(f"  macd_ok(1h MACD≤0)     : {cnt(sig['macd_ok']):>8,} 本")
    print(f"  over(dev_z≥分位・軽過熱): {cnt(sig['over']):>8,} 本")
    print(f"  vol_exh(出来高≥{VOL_Z_MIN}σ)   : {cnt(sig['vol_exh']):>8,} 本")
    print(f"  rev(反転バー)          : {cnt(sig['rev']):>8,} 本")
    print(f"  → SHORT_ENTRY 発火     : {cnt(sig['short_entry']):>8,} 本（{cnt(sig['short_entry'])/days:.2f} 本/日・候補数＝実約定はTTL/単発で減る）")
    print(f"  〔対照〕出来高条件 OFF  : {cnt(sig_novol['short_entry']):>8,} 本（{cnt(sig_novol['short_entry'])/days:.2f} 本/日）＝vol_exh が削る量（H-d・出来高が質を選別）")
    print(f"  ※ E36 base は 1.05 件/日（デイトレ）。E37=スキャルは数倍を狙う（実際の件数は本走の score 対象 CSV で確認）")
    print("=" * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-tf", choices=TFS, default="5m")
    ap.add_argument("--smoke", type=int, default=0, help="先頭 N バーだけで動作確認")
    ap.add_argument("--diagnostic", action="store_true", help="発火ファネル（期待件数）＋出来高 ON/OFF 対照だけ出す＝採点しない")
    ap.add_argument("--tag", default=None, help="実験タグ。指定で出力名を _<tag>_<NNN> 連番にし旧実験を archive へ退避（実験は必ず付ける）。未指定=dev スクラッチ名 _<box_tf>_dev（採否を pre-declare する語=base 等は使わない）")
    a = ap.parse_args()
    print("=" * 100)
    print("[E37 v2] レンジ・スキャル ショート（出来高伸び切り×上位足条件×浅TP/30分time-exit/ATR-SL・E36 デイトレと住み分け）")
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
