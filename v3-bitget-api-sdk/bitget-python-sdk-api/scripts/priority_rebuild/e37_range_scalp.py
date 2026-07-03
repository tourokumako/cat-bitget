#!/usr/bin/env python3
"""e37_range_scalp.py — E37 v5 レンジ・スキャル 両側 maker MR ＋「稼げるレンジ」検出器ゲート

★このファイルは E37 専用。E36 / E35 を import しない（兄弟・独立＝切り分け原則）。
  共通土台（① 読み込み方 / ⑤ cap検査・funding / ⑥ 出力処理 / ⑦ 取引所・予算の定数）は strat_base から import。
  戦略ロジック（② イベント＋検出器 / ③ 両側スキャル売買エンジン）は本ファイルが自前。

位置づけ（acceptance.md 承認 2026-07-03・e37_design.md v5・§1.2.1 局面3 レンジ スキャル型）:
  v3＝頻度は達成（15.35件/日）したが「レンジかどうかを知らずに全場面発火」で全セル手数料負け。
  v4＝入口の質は gross トントンだが 0.47件/日＝スキャル役割失格。
  まこさん結論（2026-07-03）＝過去データに取れるレンジは確実に在る・取れないのは CC の検出の作り。
  本 v5＝v3 型イベント（dev_z±1σ∩反転バー・両側）に、結果ベース教師（そのイベントでレンジ取りが
  手数料込みでプラスだったか＝Triple Barrier で機械生成・まこさんラベル不使用）で学習した
  LightGBM 検出器（parquet 2603特徴＝フィボ/出来高プロファイル/ピボット/BB/RSI9/サポレジ/複数TF・
  purged 5fold・学習窓のみ fit）の確率ゲート θ（学習窓 OOF 分位から選定）を掛け、
  「稼げるレンジ」の場面だけ maker で執行するスキャル。判定は score.py の数字のみ。

★v6（--v6・acceptance「E37 v6 イベント母数拡大+θ規則反転」承認 2026-07-03・既定 OFF=v5 恒等）:
  v5 の確定＝手数料超え帯は実在（OOF top10% be1.01）するが、θ選定規則「頻度床内で be 最大」が
  赤字帯（be0.57）を強制＝頻度と手数料超えの両立は θ では解けずイベント母数側で解く（ledger ARC18 問4）。
  ① イベント母数拡大＝一次イベントを5型（EVENT_TYPES・異手法・教科書 a-priori）に拡大し、
     どれが稼げる場面かは検出器（木）に判定させる（event_type one-hot を特徴に追加）。
  ② θ選定規則の反転＝「be≥BE_FLOOR(1.0=損益分岐の定義値) を満たす分位のうちイベント/日最大」
     （_select_theta_be_first・頻度床は選定に使わない・be≥1.0 帯が無ければ執行せず停止）。

H 制約（acceptance.md §E）:
  H1 cap … 両側各1玉（LONG 0.024 + SHORT 0.024 = 最大 0.048 ≤ 0.12）＋_verify_cap 実測 assert。
  H2 leak … 特徴量=Phase 0 leak 検証済 parquet のイベントバー行（因果）。検出器 fit は学習窓のみ
             （TRAIN_END assert）。教師生成は学習窓の中に閉じる（教師=学習窓内の疑似執行結果）。
             未来参照（負 shift/中央窓）を grep assert。
  H5 約定 … entry=指値maker TTL3 / TP=指値maker / SL=指値maker(gap 反映) / time-exit=成行taker+slip。
  H6 価格非依存 … 特徴は pct/比率/σ（USD 絶対値 blacklist 64 列除外 assert）・出口も σ/ATR スケール。
  H8 期間 … periods import（手打ちなし）・fit < TRAIN_END・採点窓/封印 不参照。
  H13 judge … 新 exit_reason なし（TP_FILLED/SL_FILLED/TIME_EXIT のみ）・score.py/eval_engine 無変更。
  H15 ボラ逃げ … 向きスコアなし（両側 MR＝向きを賭けない）・検出器は執行可否のみ・ATR は SL 幅のみ。
  H16 1変更 … 検出器ゲートの導入のみ（--no-gate でゲート OFF＝恒等・lever-bites 分離）。
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eval_engine as ee                       # noqa: E402  確定コスト定数（改造禁止・import のみ）
import e34_range_zscore_taker as e34v1         # noqa: E402  CSV / add_indicators（sma/std/dev_z/atr/adx）
import e34_range_base as e34b                  # noqa: E402  add_analysis_features（rsi/stoch_k 等・記録用）
import e35_box                                 # noqa: E402  箱特徴（box_W 記録用）
import build_labels_pct as bl                  # noqa: E402  resample_ohlcv / attach_upper_tf（v6 EV_PULLBACK の 1h MACD・leak-safe L-128）
import periods                                 # noqa: E402  検証期間の唯一の正本（SSOT）
import strat_base                              # noqa: E402  ★全戦略共通の土台
from strat_base import UNIT, CAP, TTL, ENTRY_OFFSET, load_5m, _verify_cap, _funding_cost  # noqa: E402

# ── 検証期間（periods.py が唯一の正本・SSOT・手打ち禁止）──
TRAIN_END = periods.TRAIN_END              # 学習境界（検出器 fit はこれ未満のみ）
SC_START = periods.SCORE_START             # 採点窓 開始
SCORE_END = periods.SEAL_START             # 採点スライスの排他終端＝封印開始
SEAL_START = periods.SEAL_START            # 封印開始（不参照）

# ── E37 v5 パラメータ（出所は各行に明記・採点窓スイープ禁止 L-267）──
PRIORITY = 37
MAX_ADDS = 1                 # スキャル＝単発（サイドごと単一スロット）
SIG_Z = 1.0                  # イベント: |dev_z| ≥ 1.0σ（σ帯の教科書標準・v3 学習分位 q30/q70≈±0.8σ と同族の a-priori）
K_SL = 2.0                   # SL = entry ∓ K_SL×ATR（教科書 1.5-2×ATR）
TP_OVERSHOOT = 0.5           # TP = SMA ∓ 0.5σ（突き抜け側・教師テンプレ2案{0,0.5σ}を学習窓比較で選定・採点窓不参照）
T_MAX = 12                   # 時間切れ backstop = 12本 = 60分（スキャル役割のバックストップ・保有中央は20-30分想定）
SCALP_FLOOR = 0.0008         # TP 武装の手数料床 0.08%（小 TP の手数料割れ防止・a-priori）
FREQ_FLOOR_EVT_DAY = 5.0     # θ選定の頻度床（学習窓ゲート通過イベント/日・スロット占有の目減り込みで採点窓 件数/日≥3 を狙う）
THETA_QQ = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95)   # θ 候補分位（学習窓 OOF から選定・採点窓不参照）

# ── E37 v6 パラメータ（イベント母数拡大＋θ規則反転・--v6 で ON・既定 OFF=v5 恒等・出所は各行）──
BE_FLOOR = 1.0               # v6 θ選定の be 床＝損益分岐の定義値（be=平均gross÷往復コスト の分岐点・数値探索でない）
SHALLOW_Z = 0.5              # 浅い行き過ぎ／順張り押し目・戻り売りの dev_z（教科書の半σ・a-priori）
BB_K = 2.0                   # EV_BB: BB(20,2σ) バンドタッチ（教科書標準・sma/std は SMA_N=20 と同窓）
BREAK_N = 20                 # EV_BREAK_REV: donchian 窓（教科書標準・当該足除外＝H2）
BREAK_LOOKBACK = 3           # EV_BREAK_REV: ブレイクから3本以内の反転バー
EVENT_TYPES = ("evt_mr", "evt_mr_sh", "evt_bb", "evt_brk", "evt_pull")   # 5型 one-hot（検出器の特徴に渡す＝木が判定）

ROOT = pathlib.Path(__file__).resolve().parents[2]
_PQ_DIR = ROOT / "results" / "priority_rebuild"
PARQUETS = [_PQ_DIR / "labels_mfe_mae_pct_train_2021_2024.parquet",
            _PQ_DIR / "labels_mfe_mae_pct_test_2025.parquet",
            _PQ_DIR / "labels_mfe_mae_pct_test_2026_q1.parquet"]
_BL_FAM = ("sma_20__", "sma_50__", "ichimoku_kijun__", "ichimoku_tenkan__",
           "macd_line__", "macd_signal__", "macd_hist__", "macd_hist_change__")
_LABEL_KW = ("mfe", "mae", "label", "barrier", "fut", "forward", "target")

_LGB_PARAMS = dict(n_estimators=300, num_leaves=63, learning_rate=0.05, subsample=0.8,
                   colsample_bytree=0.5, min_child_samples=100, random_state=42,
                   n_jobs=-1, verbosity=-1)


# ══ ② イベント（一次・高リコール＝dev_z±1σ ∩ 反転バー・両側・向きを賭けない H15）══
def micro_rev_event(df: pd.DataFrame) -> pd.DataFrame:
    """SHORT 候補＝dev_z≥+SIG_Z ∩ 陰転バー ／ LONG 候補＝dev_z≤−SIG_Z ∩ 陽転バー（当該足まで＝H2）。"""
    dev_z = df["dev_z"]
    dn = (df["close"] < df["open"])
    up = (df["close"] > df["open"])
    df["short_cand"] = ((dev_z >= SIG_Z) & dn).fillna(False).to_numpy(bool)
    df["long_cand"] = ((dev_z <= -SIG_Z) & up).fillna(False).to_numpy(bool)
    return df


# ══ ②v6 一次イベント5型（イベント母数拡大・両側・SHORT=陰転/LONG=陽転で相互排他・型は one-hot で検出器へ）══
def _add_htf_macd(df: pd.DataFrame) -> pd.DataFrame:
    """EV_PULLBACK 用: 1h MACD line(EMA12-EMA26) の符号を leak-safe に 5m へ貼る（e36 add_htf_macd と同型・L-128/H2）。
    resample_ohlcv(1h)→EMA(過去のみ)→符号→attach_upper_tf(merge_asof backward＝閉じ足のみ)。符号のみ＝価格非依存(H6)。"""
    px = df[["ts", "open", "high", "low", "close", "volume"]].rename(columns={"ts": "timestamp"}).set_index("timestamp")
    c1h = bl.resample_ohlcv(px, bl.RESAMPLE_RULE["1h"])["close"]
    macd = c1h.ewm(span=12, adjust=False).mean() - c1h.ewm(span=26, adjust=False).mean()
    up = pd.DataFrame({"htf_macd_up": (macd > 0).astype(float)}, index=c1h.index).dropna()
    merged = bl.attach_upper_tf(px[["close"]], up, "1h")
    df["htf_macd_up"] = df["ts"].map(merged["htf_macd_up"]).fillna(0.0).to_numpy() > 0.5
    return df


def _gen_events_v6(df: pd.DataFrame) -> pd.DataFrame:
    """v6 イベント母数拡大＝一次イベント5型（EVENT_TYPES・教科書 a-priori 構造・どれが稼げるかは検出器が判定）:
      EV_MR        : dev_z≥+SIG_Z∩陰転 ／ ≤−SIG_Z∩陽転（v5 同一・逆張り）
      EV_MR_SHALLOW: dev_z≥+SHALLOW_Z∩陰転 ／ ≤−SHALLOW_Z∩陽転（浅い行き過ぎ）
      EV_BB        : BB(20,{BB_K}σ) 上バンドタッチ∩陰転 ／ 下バンドタッチ∩陽転
      EV_BREAK_REV : donchian({BREAK_N}) 高値ブレイク後{BREAK_LOOKBACK}本以内の陰転 ／ 安値ブレイク後の陽転
      EV_PULLBACK  : 1h MACD≤0∩dev_z≥+SHALLOW_Z∩陰転（戻り売り）／ MACD>0∩dev_z≤−SHALLOW_Z∩陽転（押し目）＝順張り
    SHORT 系は全て陰転・LONG 系は全て陽転を要求＝同一バーで両サイドは立たない。全て当該足まで＝H2。"""
    df = _add_htf_macd(df)
    dev_z = df["dev_z"]; c = df["close"]; o = df["open"]; h = df["high"]; l = df["low"]
    sma = df["sma"]; sd = df["std"]
    dn = (c < o); up_ = (c > o)
    up_hi = h.rolling(BREAK_N).max().shift(1)          # 過去 BREAK_N 本の最高値（当該足除外）
    dn_lo = l.rolling(BREAK_N).min().shift(1)
    broke_up = (h > up_hi).astype(float)
    broke_dn = (l < dn_lo).astype(float)
    up_recent = broke_up.rolling(BREAK_LOOKBACK, min_periods=1).max() > 0.5
    dn_recent = broke_dn.rolling(BREAK_LOOKBACK, min_periods=1).max() > 0.5
    macd_up = df["htf_macd_up"]

    pairs = {
        "evt_mr":    ((dev_z >= SIG_Z) & dn,                       (dev_z <= -SIG_Z) & up_),
        "evt_mr_sh": ((dev_z >= SHALLOW_Z) & dn,                   (dev_z <= -SHALLOW_Z) & up_),
        "evt_bb":    ((h >= sma + BB_K * sd) & dn,                 (l <= sma - BB_K * sd) & up_),
        "evt_brk":   (up_recent & dn,                              dn_recent & up_),
        "evt_pull":  ((~macd_up) & (dev_z >= SHALLOW_Z) & dn,      macd_up & (dev_z <= -SHALLOW_Z) & up_),
    }
    s_all = None; l_all = None
    for name in EVENT_TYPES:
        s_m, l_m = pairs[name]
        s_m = s_m.fillna(False); l_m = l_m.fillna(False)
        df[name] = (s_m | l_m).astype(np.float32)
        s_all = s_m if s_all is None else (s_all | s_m)
        l_all = l_m if l_all is None else (l_all | l_m)
    df["short_cand"] = s_all.to_numpy(bool)
    df["long_cand"] = l_all.to_numpy(bool)
    return df


# ══ ② 教師（結果ベース・学習窓のみ＝エンジンと同一執行の Triple Barrier で net>0 を 1・まこさんラベル不使用）══
def _teacher_labels(df: pd.DataFrame, upto_ns: int) -> pd.DataFrame:
    """学習窓（ts < TRAIN_END）のイベントごとに、**エンジンと同一の執行モデル**で疑似執行し net>0 を教師 y=1 にする:
    entry=指値 maker close×(1∓offset)・TTL{TTL}本タッチ約定・**不約定イベントは教師から除外**（エンジンも取引しない＝
    楽観 fill の教師とエンジン実行の不一致＝2026-07-03 v5 初回走の IS/OOS 乖離の主因候補を塞ぐ）。
    出口＝fill バー起点で TP=SMA∓0.5σ maker／SL=K_SL×ATR maker（gap 反映）／T_MAX 打ち切り taker・同バーは SL 優先。
    ⚠️ 教師は学習窓内の未来を使う（=教師生成は学習窓に閉じる・H8）。推論時は特徴のみ＝本番再現可（H2）。"""
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    sma = df["sma"].to_numpy(float); sd = df["std"].to_numpy(float)
    atr = df["atr"].to_numpy(float)
    ts = df["ts"].to_numpy()
    n = len(df)
    rows = []; unfilled = 0
    for i in range(25, n - T_MAX - TTL - 3):
        if ts[i].astype("datetime64[ns]").astype("int64") >= upto_ns:
            break
        side = 0
        if df["short_cand"].iat[i]: side = -1
        elif df["long_cand"].iat[i]: side = 1
        if side == 0 or not (np.isfinite(atr[i]) and np.isfinite(sma[i]) and np.isfinite(sd[i])):
            continue
        # entry＝エンジン同一（指値タッチ・TTL・不約定は除外）
        lim = c[i] * (1 + ENTRY_OFFSET) if side == -1 else c[i] * (1 - ENTRY_OFFSET)
        fill = None
        for j in range(i + 1, i + 1 + TTL):
            if side == -1 and h[j] >= lim: fill = j; break
            if side == 1 and l[j] <= lim: fill = j; break
        if fill is None:
            unfilled += 1
            continue
        ep = lim
        pos = UNIT * ep
        slp = ep + K_SL * atr[fill] if side == -1 else ep - K_SL * atr[fill]
        xp = None; taker = False
        for j in range(fill + 1, fill + 1 + T_MAX):
            tgt = (sma[j] - TP_OVERSHOOT * sd[j]) if side == -1 else (sma[j] + TP_OVERSHOOT * sd[j])
            if side == -1:
                if h[j] >= slp: xp = max(slp, o[j]); break          # SL 優先・gap 反映（保守）
                if np.isfinite(tgt) and tgt <= ep * (1.0 - SCALP_FLOOR) and l[j] <= tgt: xp = tgt; break
            else:
                if l[j] <= slp: xp = min(slp, o[j]); break
                if np.isfinite(tgt) and tgt >= ep * (1.0 + SCALP_FLOOR) and h[j] >= tgt: xp = tgt; break
        if xp is None:
            xp = c[fill + T_MAX]; taker = True
        fee = pos * ee.MAKER_FEE + UNIT * xp * ((ee.TAKER_FEE + ee.SLIPPAGE) if taker else ee.MAKER_FEE)
        gross = (ep - xp) * UNIT if side == -1 else (xp - ep) * UNIT
        rows.append((ts[i], side, gross, fee, gross - fee))
    t = pd.DataFrame(rows, columns=["ts", "side", "gross", "fee", "net"])
    t["y"] = (t["net"] > 0).astype(int)
    print(f"  [教師] エンジン同一執行: 約定 {len(t)} / 不約定除外 {unfilled}（教師とエンジンの fill 一致）")
    return t


# ══ ② 特徴量（Phase 0 leak 検証済み parquet・ラベル/blacklist 除外 assert＝label_exclude_assert）══
def _load_features(want_ns: set) -> tuple[pd.DataFrame, list]:
    """3 parquet をストリームし、イベント時刻の行だけ 2603 特徴を回収する。
    label_exclude_assert: ラベル系 56 列以上・blacklist 64 列以上を必ず除外（漏れ＝停止・leak 事故 2026-07-03 再発防止）。"""
    import pyarrow.parquet as pq
    pf0 = pq.ParquetFile(PARQUETS[0])
    all_cols = pf0.schema_arrow.names
    label_cols = [x for x in all_cols if any(k in x.lower() for k in _LABEL_KW)]
    bl_cols = [x for x in all_cols if x.startswith(_BL_FAM)]
    assert len(label_cols) >= 56 and len(bl_cols) >= 64, \
        f"label_exclude_assert: ラベル/blacklist 検出漏れ疑い（label={len(label_cols)} blacklist={len(bl_cols)}）"
    feat_cols = [x for x in all_cols if x not in set(label_cols + bl_cols + ["close"]) and x != "timestamp"]
    assert "rsi9__5m" in feat_cols, "RSI9 列が特徴に無い（technical_kb §4・acceptance F ⑫）"
    assert any(x.endswith("__1h") for x in feat_cols), "MTF 上位足列が特徴に無い（technical_kb §5・acceptance F ⑫）"
    chunks = []
    for pth in PARQUETS:
        pf = pq.ParquetFile(pth)
        for batch in pf.iter_batches(batch_size=65536, columns=["timestamp"] + feat_cols):
            dfb = batch.to_pandas()
            if "timestamp" not in dfb.columns:
                dfb = dfb.reset_index().rename(columns={dfb.index.name or "index": "timestamp"})
            tsb = pd.DatetimeIndex(dfb["timestamp"])
            if tsb.tz is not None:
                dfb["timestamp"] = tsb.tz_localize(None)
            m = pd.Index(pd.DatetimeIndex(dfb["timestamp"]).asi8).isin(want_ns)
            if m.any():
                sub = dfb.loc[np.asarray(m)]
                sub = pd.concat([sub[["timestamp"]],
                                 sub[feat_cols].astype(np.float32)], axis=1)
                chunks.append(sub)
    feat = pd.concat(chunks, ignore_index=True).drop_duplicates("timestamp")
    return feat, feat_cols


def purged_fold(t: pd.DatetimeIndex, k: int = 5, embargo_days: float = 1.0):
    """時間ブロック k 分割＋embargo（AFML purged CV・leak/系列相関対策）。"""
    edges = pd.date_range(t.min(), t.max() + pd.Timedelta("1ns"), periods=k + 1)
    emb = pd.Timedelta(days=embargo_days)
    for i in range(k):
        lo, hi = edges[i], edges[i + 1]
        te = (t >= lo) & (t < hi)
        tr = (t < lo - emb) | (t >= hi + emb)
        yield np.asarray(tr), np.asarray(te)


def _select_theta_be_first(cand: list) -> dict | None:
    """v6 θ選定規則（反転・acceptance F2）＝be≥BE_FLOOR（損益分岐）を満たす分位のうちイベント/日最大。
    頻度床は選定に使わない（頻度はイベント母数で作る）。満たす帯が無ければ None＝執行せず停止（赤字帯を選ばない）。"""
    feas = [c_ for c_ in cand if np.isfinite(c_["be"]) and c_["be"] >= BE_FLOOR]
    return max(feas, key=lambda c_: c_["events_per_day"]) if feas else None


def _fit_detector(teach: pd.DataFrame, feat: pd.DataFrame, feat_cols: list, days_train: float,
                  v6: bool = False, evt: pd.DataFrame | None = None) -> dict:
    """検出器学習＝purged 5fold OOF → oof_theta（θ）を学習窓分位から選定 → 学習窓全体で再 fit。
    θ選定＝v5: ゲート通過イベント/日 ≥ FREQ_FLOOR_EVT_DAY の範囲で be 最大（採点窓不参照）
           v6: _select_theta_be_first（be≥BE_FLOOR 内で頻度最大・反転）＋旧規則も比較ログ（lever-bites）。
    v6 は event_type one-hot（EVENT_TYPES）を特徴に追加＝どのイベント型が稼げるかを木が判定。"""
    import lightgbm as lgb
    df = teach.merge(feat.rename(columns={"timestamp": "ts"}), on="ts", how="inner").sort_values("ts").reset_index(drop=True)
    miss = len(teach) - len(df)
    print(f"  [検出器] 教師 {len(teach)} 件（特徴結合 {len(df)}・特徴欠落 {miss} 件は学習から除外）/ 勝ちラベル率 {df.y.mean()*100:.1f}%")
    assert int(pd.DatetimeIndex(df.ts).asi8.max()) < int(pd.Timestamp(TRAIN_END).value), \
        "TRAIN_END assert: 教師に学習窓外の行が混入（H8 違反）"
    evt_cols: list = []
    if v6:
        assert evt is not None, "v6 は evt（イベント型 one-hot）必須"
        df = df.merge(evt, on="ts", how="left")
        evt_cols = list(EVENT_TYPES)
        df[evt_cols] = df[evt_cols].fillna(0.0)
    X = df[feat_cols + evt_cols].astype(np.float32).assign(side=df["side"].astype(np.float32))
    y = df["y"].to_numpy()
    tt = pd.DatetimeIndex(df.ts)
    oof = np.full(len(df), np.nan)
    for tr, te in purged_fold(tt):
        mdl = lgb.LGBMClassifier(**_LGB_PARAMS)
        mdl.fit(X[tr], y[tr])
        oof[te] = mdl.predict_proba(X[te])[:, 1]
    ok = np.isfinite(oof)
    # oof_theta 選定（学習窓のみ）
    cand = []
    for qq in THETA_QQ:
        thr = float(np.quantile(oof[ok], qq))
        g = df[ok][oof[ok] >= thr]
        if len(g) == 0:
            continue
        evt_day = len(g) / days_train
        be = float(g.gross.mean() / g.fee.mean()) if g.fee.mean() else float("nan")
        cand.append({"quantile": qq, "theta": round(thr, 4), "events_per_day": round(evt_day, 2),
                     "avg_gross": round(float(g.gross.mean()), 4), "avg_fee": round(float(g.fee.mean()), 4),
                     "be": round(be, 3), "win_rate": round(float((g.net > 0).mean()), 3)})
    feas = [c_ for c_ in cand if c_["events_per_day"] >= FREQ_FLOOR_EVT_DAY]
    pick_old = max(feas, key=lambda c_: c_["be"]) if feas else max(cand, key=lambda c_: c_["events_per_day"])
    if v6:
        pick = _select_theta_be_first(cand)
        print(f"  [検出器 v6] θフロンティア（学習窓 OOF）: {json.dumps(cand, ensure_ascii=False)}")
        print(f"  [検出器 v6] 旧規則（頻度床 {FREQ_FLOOR_EVT_DAY}/日内 be 最大）なら: {json.dumps(pick_old, ensure_ascii=False)}（比較ログ・lever-bites）")
        if pick is None:
            print(f"  [検出器 v6] ⛔ be≥{BE_FLOOR} を満たす分位が存在しない＝執行せず停止（赤字帯を選ばない・acceptance F2）")
            raise SystemExit(1)
        # ⑨巻き込みの明示（acceptance F3）: 選定帯より下に落とす勝ちイベントの絶対数と gross（学習窓 OOF）
        g_all = df[ok]; p_all = oof[ok]
        kept = g_all[p_all >= pick["theta"]]; cut = g_all[p_all < pick["theta"]]
        cut_w = cut[cut.net > 0]
        print(f"  [⑨巻き込み] θ={pick['theta']:.4f} で削るイベント {len(cut)}（うち勝ち {len(cut_w)} 件・gross ${cut_w.gross.sum():.0f}・"
              f"平均gross ${cut_w.gross.mean() if len(cut_w) else 0:.3f}/件）／ 残す {len(kept)}（{pick['events_per_day']}/日）")
    else:
        pick = pick_old
    oof_theta = pick["theta"]
    rule = f"v6: be≥{BE_FLOOR} 内で頻度最大（反転）" if v6 else f"頻度床 {FREQ_FLOOR_EVT_DAY}/日内で be 最大"
    print(f"  [検出器] oof_theta 選定（学習窓 OOF・{rule}）: {json.dumps(pick, ensure_ascii=False)}")
    # 本番モデル＝学習窓全体で再 fit（Hudson&Thames: 閾値/ハイパラは学習側で確定・OOS は一発評価）
    final = lgb.LGBMClassifier(**_LGB_PARAMS)
    final.fit(X, y)
    # H15: 重要度で ATR/vol 家族が非支配か（ボラ逃げ検査）
    fi = pd.Series(final.feature_importances_, index=list(X.columns)).sort_values(ascending=False)
    top10 = list(fi.head(10).index)
    atr_top = [x for x in top10 if "atr" in x.lower() or "realized_vol" in x.lower()]
    print(f"  [検出器] 重要度 top10: {top10}")
    print(f"  [自己検査 H15] top10 中 ATR/vol 系 {len(atr_top)} 列（{atr_top}）: {'✅ 非支配' if len(atr_top) <= 2 else '⚠️ ボラ支配疑い＝報告時に要精査'}")
    oof_map = pd.Series(oof[ok], index=pd.DatetimeIndex(df.ts)[ok])   # 学習窓ゲート用 OOF（in-sample 記憶を使わない）
    return {"model": final, "oof_theta": oof_theta, "theta_log": cand, "picked": pick,
            "feat_cols": feat_cols, "evt_cols": evt_cols, "top10": top10, "oof_map": oof_map,
            "pick_old_rule": pick_old}


def detector_gate(det: dict, feat: pd.DataFrame, df: pd.DataFrame) -> np.ndarray:
    """候補バーごとに p を推論し、oof_theta 以上を True にした配列（len=n）を返す。
    ★学習窓バー＝OOF 確率（そのfoldの学習に使っていない予測）でゲート＝in-sample 記憶の自己採点を塞ぐ
      （2026-07-03 v5 初回走で precheck が breakeven 10.33 の偽 PASS を出した事故の恒久対策）。
    ★TRAIN_END 以降のバー＝学習窓全体で fit した最終モデルで推論（clean OOS）。
    特徴欠落・OOF 欠落（embargo/不約定）バーは不通過＝取引しない（決定的・保守）。"""
    n = len(df)
    ok = np.zeros(n, dtype=bool)
    ts_index = pd.DatetimeIndex(df["ts"])
    is_train = ts_index < pd.Timestamp(TRAIN_END)
    # ── 学習窓: OOF ゲート ──
    oof_map = det["oof_map"]
    cand_any = (df["short_cand"] | df["long_cand"]).to_numpy(bool)
    m_tr = cand_any & np.asarray(is_train)
    if m_tr.any():
        p_tr = oof_map.reindex(ts_index[m_tr]).to_numpy()
        ok[np.where(m_tr)[0]] = np.where(np.isfinite(p_tr), p_tr >= det["oof_theta"], False)
    # ── TRAIN_END 以降: 最終モデル ──
    f = feat.set_index("timestamp")
    present = ts_index.isin(f.index)
    for side_val, col in ((-1.0, "short_cand"), (1.0, "long_cand")):
        m = df[col].to_numpy(bool) & np.asarray(present) & ~np.asarray(is_train)
        if not m.any():
            continue
        ts_m = ts_index[m]
        X = f.loc[ts_m, det["feat_cols"]].astype(np.float32)
        if det.get("evt_cols"):
            ev = df.loc[m, det["evt_cols"]].astype(np.float32)
            ev.index = X.index                      # 同順（両方 df の行順由来）＝index を揃えて結合
            X = pd.concat([X, ev], axis=1)
        X = X.assign(side=np.float32(side_val))
        p = det["model"].predict_proba(X)[:, 1]
        ok[np.where(m)[0]] = p >= det["oof_theta"]
    return ok


# ══ ⑤(戦略別の記録) 売買記録（funding/cap は共通土台・両側）══
_MAKER_EXIT = ("TP_FILLED", "SL_FILLED", "EDGE_TP", "BE_EXIT", "PARTIAL_TP")   # score.py MAKER_EXIT_REASONS と一致


def _record(trades, pos, exit_price, reason, exit_idx, ts_arr):
    """1 ポジ（単発 lot）を記録。TP_FILLED/SL_FILLED=maker（指値）・TIME_EXIT/EOD=taker。"""
    side = pos["side"]; sdir = 1 if side == "LONG" else -1
    exit_ts = pd.Timestamp(ts_arr[exit_idx]); exit_px = float(exit_price)
    is_taker = reason not in _MAKER_EXIT
    pos_id = f"{side}_{int(pos['first_idx'])}"
    lot_idx, lp, lot_size = pos["first_idx"], float(pos["avg"]), float(pos["size"])
    entry_ts = pd.Timestamp(ts_arr[lot_idx])
    gross = (exit_px - lp) * lot_size * sdir
    entry_fee = lp * lot_size * ee.MAKER_FEE
    exit_fee = exit_px * lot_size * (ee.TAKER_FEE if is_taker else ee.MAKER_FEE)
    slip = (exit_px * lot_size * ee.SLIPPAGE) if is_taker else 0.0
    funding = _funding_cost(sdir, entry_ts, exit_ts, lot_size, lp)
    net = gross - entry_fee - exit_fee - slip - funding
    row = {
        "entry_time": entry_ts, "exit_time": exit_ts, "side": side,
        "priority": PRIORITY, "regime": "range", "position_id": pos_id, "add_count": int(pos["add_count"]),
        "size_btc": round(lot_size, 6), "entry_price": round(lp, 2), "exit_price": round(exit_px, 2),
        "exit_reason": reason, "hold_min": int((exit_idx - lot_idx) * 5),
        "atr_14": round(float(pos["atr_entry"]), 2),
        "adx_at_entry": round(float(pos["adx_entry"]), 3) if np.isfinite(pos["adx_entry"]) else None,
        "stoch_k_at_entry": round(float(pos["k_entry"]), 2) if np.isfinite(pos["k_entry"]) else None,
        "box_W_pct_at_entry": round(float(pos["W_entry"]), 5) if np.isfinite(pos["W_entry"]) else None,
        "entry_hour": int(entry_ts.hour), "entry_weekday": int(entry_ts.weekday()),
        "mfe_usd": round((pos["max_fav"] - lp) * lot_size * sdir, 4),
        "mae_usd": round((pos["max_adv"] - lp) * lot_size * sdir, 4),
        "gross_usd": round(gross, 4), "fee_usd": round(entry_fee + exit_fee + slip, 4), "net_usd": round(net, 4),
    }
    if pos.get("evt") is not None:                 # v6 のみ: イベント型（lever-bites 用・v5/OFF では列自体を出さない＝恒等）
        row["event_type"] = pos["evt"]
    trades.append(row)


# ══ ③ 両側スキャル売買エンジン（連続モード・サイドごと単一スロット・ゲート通過候補のみ）══
def run_continuous(df, gate_ok: np.ndarray, box_tf, evt_lbl=None):
    """v5 エンジン。入口＝ゲート通過候補に maker 指値 TTL3（不約定は積まない）。
    出口＝① SL(entry∓K_SL×ATR・指値maker・gap 反映・SL 優先=教師と同順) ② TP(SMA∓0.5σ・maker・SCALP_FLOOR)
          ③ T_MAX=60分 time-exit(taker)。全て約定 bar の次以降＝leak-safe（H2）。"""
    n = len(df)
    ts = df["ts"].to_numpy()
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    sma = df["sma"].to_numpy(float); sd = df["std"].to_numpy(float)
    sup = df[e35_box.sup_col(box_tf)].to_numpy(float); res = df[e35_box.res_col(box_tf)].to_numpy(float)
    Wpct = sup + res
    short_cand = df["short_cand"].to_numpy(bool); long_cand = df["long_cand"].to_numpy(bool)

    trades = []
    slots = {"SHORT": {"pos": None, "pend": None}, "LONG": {"pos": None, "pend": None}}

    def _total_size():
        return sum(s["pos"]["size"] for s in slots.values() if s["pos"] is not None)

    for i in range(n):
        for side, st in slots.items():
            # ── 1. pending fill（指値 maker・TTL・不約定は積まない）──
            pend = st["pend"]
            if pend is not None:
                el = i - pend["placed_idx"]
                filled = False
                if el > TTL:
                    st["pend"] = None
                elif el >= 1:
                    if side == "SHORT" and h[i] >= pend["limit"]: filled = True
                    if side == "LONG" and l[i] <= pend["limit"]: filled = True
                if filled:
                    if st["pos"] is None and np.isfinite(atr[i]) and (_total_size() + UNIT <= CAP + 1e-9):
                        st["pos"] = {"side": side, "avg": pend["limit"], "size": UNIT, "add_count": 1,
                                     "first_idx": i, "last_fill_idx": i,
                                     "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i], "W_entry": Wpct[i],
                                     "max_fav": l[i] if side == "SHORT" else h[i],
                                     "max_adv": h[i] if side == "SHORT" else l[i]}
                        if "evt" in pend:
                            st["pos"]["evt"] = pend["evt"]
                    st["pend"] = None
            # ── 2. MFE/MAE 極値更新（記録用）──
            pos = st["pos"]
            if pos is not None:
                if side == "SHORT":
                    pos["max_fav"] = min(pos["max_fav"], l[i]); pos["max_adv"] = max(pos["max_adv"], h[i])
                else:
                    pos["max_fav"] = max(pos["max_fav"], h[i]); pos["max_adv"] = min(pos["max_adv"], l[i])
            # ── 3. 出口（約定 bar の次以降・SL 優先=教師と同順・保守）──
            if pos is not None and i > pos["last_fill_idx"]:
                avg = pos["avg"]; a = pos["atr_entry"]
                sl = avg + K_SL * a if side == "SHORT" else avg - K_SL * a
                tp = (sma[i] - TP_OVERSHOOT * sd[i]) if side == "SHORT" else (sma[i] + TP_OVERSHOOT * sd[i])
                if side == "SHORT" and np.isfinite(sl) and h[i] >= sl:
                    _record(trades, pos, max(sl, o[i]), "SL_FILLED", i, ts); st["pos"] = None; continue
                if side == "LONG" and np.isfinite(sl) and l[i] <= sl:
                    _record(trades, pos, min(sl, o[i]), "SL_FILLED", i, ts); st["pos"] = None; continue
                if np.isfinite(tp):
                    if side == "SHORT" and tp <= avg * (1.0 - SCALP_FLOOR) and l[i] <= tp:
                        _record(trades, pos, tp, "TP_FILLED", i, ts); st["pos"] = None; continue
                    if side == "LONG" and tp >= avg * (1.0 + SCALP_FLOOR) and h[i] >= tp:
                        _record(trades, pos, tp, "TP_FILLED", i, ts); st["pos"] = None; continue
                if (i - pos["first_idx"]) >= T_MAX:
                    _record(trades, pos, c[i], "TIME_EXIT", i, ts); st["pos"] = None; continue
            # ── 4. 入口（ゲート通過候補のみ・サイドごと単一スロット）──
            if st["pos"] is None and st["pend"] is None:
                cand = short_cand[i] if side == "SHORT" else long_cand[i]
                if cand and gate_ok[i]:
                    lim = c[i] * (1.0 + ENTRY_OFFSET) if side == "SHORT" else c[i] * (1.0 - ENTRY_OFFSET)
                    st["pend"] = {"limit": lim, "placed_idx": i}
                    if evt_lbl is not None:
                        st["pend"]["evt"] = evt_lbl[i]

    for side, st in slots.items():
        if st["pos"] is not None:
            _record(trades, st["pos"], c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    return trades


# ══ ⑥ 出力（共通土台に委譲）＋使用パラメータ（report.py 節0）══
def _param_sections(det: dict | None, gate_on: bool, v6: bool = False) -> dict:
    if v6:
        evt_desc = {
            "イベント（v6・5型＝母数拡大・どれが稼げるかは検出器が判定）": (
                f"EV_MR: dev_z±{SIG_Z}σ∩反転バー（v5 同一）／ EV_MR_SHALLOW: dev_z±{SHALLOW_Z}σ∩反転バー ／ "
                f"EV_BB: BB(20,{BB_K}σ)タッチ∩反転バー ／ EV_BREAK_REV: donchian({BREAK_N})ブレイク後{BREAK_LOOKBACK}本以内の反転バー ／ "
                f"EV_PULLBACK: 1h MACD 方向∩dev_z±{SHALLOW_Z}σ∩反転バー（順張り押し目/戻り売り）。全て教科書 a-priori 構造"),
            "θ選定規則（v6・反転）": f"be≥{BE_FLOOR}（損益分岐の定義値）を満たす学習窓 OOF 分位のうちイベント/日最大（頻度床は選定に使わない・be≥{BE_FLOOR} 帯なしなら執行せず停止）",
        }
    else:
        evt_desc = {
            "イベント": f"SHORT=dev_z≥+{SIG_Z}σ∩陰転 ／ LONG=dev_z≤−{SIG_Z}σ∩陽転（σ帯の教科書標準・a-priori）",
        }
    sec = {
        "検証期間（periods正本・E31）": {
            "学習(fit)": f"〜{TRAIN_END.date()} 未満（検出器の教師生成・fit・θ選定は全て学習窓のみ）",
            "採点(公式net)": f"{SC_START.date()} 〜 {SCORE_END.date()} 未満（特徴は parquet から predict のみ）",
            "封印(不参照)": f"{SEAL_START.date()} 以降",
        },
        "【入口】イベント×検出器ゲート（両側・向きを賭けない H15）": {
            **evt_desc,
            "検出器": "LightGBM（結果ベース教師＝そのイベントでレンジ取りが手数料込みプラスだったか・Triple Barrier 機械生成・まこさんラベル不使用）"
                      + ("＋event_type one-hot 特徴（v6）" if v6 else ""),
            "特徴": "Phase 0 parquet 2603列（フィボ/出来高プロファイル/ピボット/BB/RSI9/サポレジ距離/複数TF整合）＋side（ラベル56+blacklist64+close 除外 assert）",
            "学習": "purged 5fold（embargo 1日）で OOF → 学習窓全体で再fit（Hudson&Thames: 閾値は学習側で確定・OOS 一発評価）",
        },
        "【固定値】サイズ・add（スキャル＝単発・サイドごと単一スロット）": {
            "予算上限": f"全建玉（LONG+SHORT）合計 {CAP} BTC（H1・共有枠）・本戦略の同時最大 {UNIT*2} BTC",
            "size": f"{UNIT} BTC・MAX_ADDS={MAX_ADDS}",
            "指値": f"close×(1∓{ENTRY_OFFSET})・TTL {TTL}本(={TTL*5}分)・不約定は積まない（maker限定）",
        },
        "【出口】スキャル＝幅を取り切る浅TP＋SL backstop（新 exit_reason なし・既存登録のみ）": {
            "TP利確 TP_FILLED(maker指値)": f"SMA ∓ {TP_OVERSHOOT}σ（突き抜け側まで取り切る・教師テンプレ2案を学習窓比較で選定）",
            "TP武装条件": f"建値比 {SCALP_FLOOR*100:.2f}%(SCALP_FLOOR)を超える時だけTPを置く（手数料割れ防止）",
            "SL backstop SL_FILLED(maker指値)": f"entry ∓ {K_SL}×ATR（教科書 1.5-2×・gap 反映・SL 優先＝教師と同順）",
            "時間切れ TIME_EXIT(成行taker)": f"初回entryから {T_MAX}本 = {T_MAX*5}分（スキャル backstop・保有中央は20-30分想定）",
        },
        "【固定値】コスト（eval_engine・確定値・改造禁止）": {
            "maker手数料": f"{ee.MAKER_FEE*100:.3f}%", "taker手数料": f"{ee.TAKER_FEE*100:.3f}%",
            "slippage": f"{ee.SLIPPAGE*100:.3f}%（taker時のみ）", "funding": f"{ee.FUNDING_RATE_8H*100:.4f}% / 8h",
        },
        "【備考】": {
            "ゲート": "ON" if gate_on else "OFF（--no-gate＝恒等確認・全イベント執行）",
            "特徴の出所": "parquet は Bitget 足由来・価格系列は Binance spot（既知の系統差＝特徴は因果情報として使用・net 計算には不関与）",
            "数値の出所": "probe の be/top% は実装に焼いていない＝θ は本実行が学習窓 OOF を作り直して選定（L-267）",
        },
    }
    if det is not None:
        sec["【学習した内容】検出器 θ 選定ログ（学習窓 OOF・採点窓不参照）"] = {
            "選定": json.dumps(det["picked"], ensure_ascii=False),
            "候補": json.dumps(det["theta_log"], ensure_ascii=False),
            "重要度top10": ", ".join(det["top10"]),
        }
    return sec


def run_e37(df, box_tf, tag=None, no_gate=False, v6=False):
    """E37 を回す（v6=False で v5 恒等）。判定は score.py の数字（本関数は net を計算しない＝記録のみ）。"""
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"   # H2 自己 grep
    df = _gen_events_v6(df) if v6 else micro_rev_event(df)
    det = None
    evt_lbl = None
    if v6:
        m = df[list(EVENT_TYPES)].to_numpy(np.float32) > 0.5
        names = np.array(EVENT_TYPES)
        evt_lbl = np.array(["+".join(names[r]) if r.any() else "" for r in m])
        per = {name: int(df[name].sum()) for name in EVENT_TYPES}
        print(f"  [イベント v6] 型別候補バー: {json.dumps(per, ensure_ascii=False)}")
    if no_gate:
        gate_ok = np.ones(len(df), dtype=bool)
        print("  [ゲート] OFF（--no-gate＝恒等確認モード・全イベント執行）")
    else:
        cand_ts = df.loc[df["short_cand"] | df["long_cand"], "ts"]
        print(f"  [イベント] 候補 {len(cand_ts):,} バー（特徴回収に進む）")
        feat, feat_cols = _load_features(set(pd.DatetimeIndex(cand_ts).asi8))
        print(f"  [特徴] {len(feat_cols)} 列 × {len(feat):,} 行 回収（label_exclude_assert 通過）")
        teach = _teacher_labels(df, int(pd.Timestamp(TRAIN_END).value))
        days_train = max((teach.ts.max() - teach.ts.min()) / np.timedelta64(1, "D"), 1.0)
        det = _fit_detector(teach, feat, feat_cols, days_train,
                            v6=v6, evt=(df[["ts"] + list(EVENT_TYPES)] if v6 else None))
        gate_ok = detector_gate(det, feat, df)
        gated = int((gate_ok & (df["short_cand"] | df["long_cand"]).to_numpy(bool)).sum())
        print(f"  [ゲート] oof_theta={det['oof_theta']:.4f} 通過候補 {gated:,} バー")
    trades = run_continuous(df, gate_ok, box_tf, evt_lbl=evt_lbl)
    t = pd.DataFrame(trades)
    if len(t):
        t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
        mx = _verify_cap(trades)                       # 自己検査: cap 実測（H1）
        print(f"  [自己検査 cap] 同時保有 max {mx:.4f} BTC ≤ {CAP}: {'✅' if mx <= CAP + 1e-9 else '⛔cap 超過'}")
        assert mx <= CAP + 1e-9, "cap 0.12 超過（H1 違反）"
        assert (t["size_btc"] >= ee.MIN_ORDER_BTC).all(), "最小注文サイズ違反（H9）"
    _out(t, f"_{box_tf}_{'v6' if v6 else 'v5'}", det, tag=tag, gate_on=not no_gate, v6=v6)


def _out(t: pd.DataFrame, suffix: str, det, tag=None, gate_on=True, v6=False) -> None:
    strat_base._output_and_report(
        t, suffix, stem="e37_range_scalp",
        strategy=("E37 v6 レンジ・スキャル 両側 maker MR＋検出器ゲート（イベント5型＋θ規則反転）" if v6
                  else "E37 v5 レンジ・スキャル 両側 maker MR＋稼げるレンジ検出器ゲート"),
        script="e37_range_scalp.py",
        sections=_param_sections(det, gate_on, v6=v6), tag=tag)


def _load(smoke: int) -> pd.DataFrame:
    df = load_5m(smoke)
    df = e34v1.add_indicators(df)                 # sma/std/dev_z/atr/adx
    df = e34b.add_analysis_features(df)           # rsi/stoch_k（記録用）
    df = e35_box.add_box_features(df, verify_leak=(smoke > 0 and smoke <= 60000))   # box_W 記録用
    df["atr_pct"] = df["atr"] / df["close"] * 100.0
    return df


def _diagnostic(df, v6=False):
    """発火ファネル（採点しない）＝イベント頻度のみ（検出器は本走で学習＝重い処理を diagnostic で回さない）。"""
    df = _gen_events_v6(df) if v6 else micro_rev_event(df)
    n = len(df)
    days = max((df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
    s = int(df["short_cand"].sum()); L = int(df["long_cand"].sum())
    print("=" * 100)
    print(f"[E37 {'v6' if v6 else 'v5'} 発火ファネル診断・採点しない] {n:,}本 / {days:.0f}日")
    if v6:
        for name in EVENT_TYPES:
            k = int(df[name].sum())
            print(f"  {name:<10}: {k:>8,} 本（{k/days:.2f}/日）")
    print(f"  SHORT 候補 : {s:>8,} 本（{s/days:.2f}/日）")
    print(f"  LONG  候補 : {L:>8,} 本（{L/days:.2f}/日）")
    print(f"  合計 {s+L:,} 本（{(s+L)/days:.2f}/日）＝検出器ゲート（θ は本走で学習窓 OOF から選定）で絞る")
    print("=" * 100)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box-tf", choices=e35_box.TFS, default="5m")
    ap.add_argument("--smoke", type=int, default=0, help="先頭 N バーだけで動作確認")
    ap.add_argument("--diagnostic", action="store_true", help="発火ファネル（イベント頻度）だけ出す＝採点しない")
    ap.add_argument("--no-gate", action="store_true", help="検出器ゲート OFF（恒等確認・lever-bites 用）")
    ap.add_argument("--v6", action="store_true", help="v6=イベント母数拡大（5型）＋θ選定規則反転（be≥1.0 内で頻度最大）。既定 OFF=v5 恒等")
    ap.add_argument("--tag", default=None, help="実験タグ。指定で出力名を _<tag>_<NNN> 連番にし旧実験を archive へ退避（実験は必ず付ける）")
    a = ap.parse_args()
    print("=" * 100)
    print(f"[E37 {'v6' if a.v6 else 'v5'}] レンジ・スキャル 両側 maker MR＋検出器ゲート"
          + ("（v6=イベント5型＋θ規則反転）" if a.v6 else "（E36 デイトレと住み分け）"))
    df = _load(a.smoke)
    print(f"  価格 {e34v1.CSV.name}（{len(df):,}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器 maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / unit {UNIT}")
    if a.diagnostic:
        _diagnostic(df, v6=a.v6)
        return
    run_e37(df, a.box_tf, tag=a.tag, no_gate=a.no_gate, v6=a.v6)
    print("=" * 100)


if __name__ == "__main__":
    main()
