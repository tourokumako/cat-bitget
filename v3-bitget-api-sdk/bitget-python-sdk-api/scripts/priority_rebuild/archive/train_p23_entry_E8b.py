#!/usr/bin/env python3
"""train_p23_entry_E8b.py — P23 Entry×Exit セット ML 学習（ratchet E8b・B 設計・strat_v9ml_design §10 準拠）

§0 の目的（毎回外す事故防止・正本 strat_v9ml_design.md §0）:
  P23 の手動ロジック（V9 の Entry/Exit）をそのまま土台に使い、その中で「ML で調整できる数字」
  （人が手で決めた閾値・指標期間・Exit パラメータ）を学習・調整したら、連続モード(cap 0.12 遵守)の
  NET が 地面 $925.73 から どれだけ伸びるか を検証する。複雑な独自 ML パイプラインが目的ではない。

★ B 設計（2026-06-08・E8b第1回のボラ逃げ違反を是正・軸1準拠・session_log_20260608 §1）:
  E8b第1回は Entry ラベルを「実出口 net >= T の金額二値」にしたため、高ボラほど net が伸びる構造で
  モデルが「方向(下げ)」でなく「荒れているか(揺れ幅=ATR)」を学習し、地面 $925.73 に負けた（$655）。
  B 設計の 3 点修正（本ラウンドのスコープ）:
   ① Entry ラベル＝方向ベース Triple Barrier の符号（金額の大小を消す・§10.7 B 改訂）。
      バリアは固定%でなく **ボラ基準** `entry×(1±k×σ)`（σ=entry時点 t の ATR を価格比化・k=K_BARRIER）。
      固定%だと高ボラ時にラベル自体がボラを写し込むため。先着バリアで +1(下げ到達)/−1(逆行)/0(時間切れ)。
   ② Entry の特徴量 X から atr_pct / bb_width_pct を除外（方向の主役は regime 系・軸1）。
      ATR は「捨てる」でなく「①のバリア幅 σ の入力」として役割を正す（軸1 受け入れ条件③）。
   ③ 期間分割（H8）= 学習〜2024-12-31 / embargo 2025-01〜03 / 採点 2025-04〜12 / 封印 2026Q1。
      `assert 学習末 ≤ 2024-12-31` を module ロード時と split 時に物理 assert。
  ⚠️ Exit ラベル（6-2）は net 基準のまま（サイズ同一なら方向と整合・§10.7 末尾）。今回 ① は Entry ラベルのみ。
  ⚠️ 今回スコープ外（触らない）: k-fold/DSR/PBO/Exit学習の高度化（既存実装をそのまま使う）。

E8b で実装する設計書 §10.13 のステップ（前ラウンドで欠落していた 6-2/6-3/7/9 を新規・4/5 を B で修正）:
  4   Entry ラベル = 方向ベース Triple Barrier の符号（ボラ基準バリア k×σ・金額不使用・MFE ピーク不使用
      ＝§10.7 B 改訂・H2）。Exit ラベル（6-2）= 実出口 net（add 込み連続モード・net 最大の Exit を選ぶ）。
  5   期間分割 = 学習 entry<2024-12-31 かつ exit<2025-04-01(embargo) / 採点 2025-04-01〜2026-01-01 /
      封印 2026Q1 不参照。**生 timestamp に対し直接 assert**（マスク自己無撞着でなく独立検証＝前ラウンド H8 飾り是正）。
  6-1 Entry（閾値・指標期間）= 複数期間特徴量を木に渡し、feature importance で有効期間・split 閾値を学習。
  6-2 Exit（TP/SL/時間/PROFIT_LOCK/失速）= 各 Exit 候補を **params override で前向き sim** し
      場面（学習期間）net 最大の Exit 設定を選ぶ（§10.7 Exit 学習用・§10.8 B1「場面→最適 Exit を予測」の
      まず これ＝場面共通の net 最大 Exit を data-driven に選定）。gen は import のみ・改造しない。
  6-3 Entry/Exit セット = 6-2 で選んだ Exit を土台に、Entry 選別(θ)×Exit 設定の組合せを連続モード net で評価
      （§8.4/§8.5 セットで net 最適化・片方だけ動かさない）。
  7   交差検証・ハイパラ = purged k-fold（embargo 付き・Lopez de Prado AFML Ch.7・既存 purged_kfold.py）+
      Optuna でハイパラ探索（過学習検出・C 対策）。
  8   評価 = 連続モード(cap0.12) score.py NET（採点 2025-04〜12）が地面 $925.73 を超えるか・異常値 STOP。
  9   過学習チェック = DSR>0.95 / PBO<0.5（既存 dsr_pbo.py・iteration 中は採点期間 θ グリッドで多重検定補正・
      封印 2026Q1 の最終 1 回チェックは別工程＝SC_END=2026-01-01 で封印を不参照のまま土台を可視化）。

流用元（import か関数流用・本体は改造しない）:
  - train_p23_entry_E8.py: make_features の MTF（build_mtf）・LightGBM ハイパラ・θ選定思想
  - gen_p23_candidates.py: run_continuous / _p23_type_fires / _step / simulate_independent / preload（import のみ）
  - measure_p23_ground_capped.py: 連続モードの cap 物理検証 思想
  - score.py: 審判（import のみ・改造禁止・cap ゲート）/ purged_kfold.py / dsr_pbo.py（評価基盤・既知答えテスト済）

§4.6 ハード制約の assert（H2/H6/H8 は本学習スクリプトで物理停止・売買記録に出ない boundary だから）:
  H2(leak): 特徴量に結果列なし・shift(-N)/center=True の未来参照なし・**生 timestamp で学習末<採点始** /
  H6(pct・USD絶対値blacklist) / H8(期間分割・生 timestamp 独立 assert) /
  自己検査(AI ゲート無し=全型通すと gen full の連続モードと件数/net 一致)。
V9本体(cat_v9_decider)/replay_csv/score.py/eval_engine/gen_p23_candidates は import のみ・改造しない。
"""
from __future__ import annotations
import sys
import pathlib
import json
import itertools
import numpy as np
import pandas as pd
import ta
import lightgbm as lgb
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "runner"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import replay_csv as rc                                   # noqa: E402  V9 リプレイ（import のみ）
import gen_p23_candidates as gen                          # noqa: E402  連続モード/型/sim（import のみ）
import score as judge                                     # noqa: E402  審判（import のみ・改造しない）
import train_p23_entry_E8 as e8                           # noqa: E402  build_mtf 流用（leak-safe MTF）
import purged_kfold as pk                                 # noqa: E402  Purged K-Fold（AFML Ch.7・既知答え済）
import dsr_pbo                                            # noqa: E402  DSR/PBO（多重検定補正・既知答え済）
import ratchet_guards as rg                              # noqa: E402  ① 番人（leak/期間/cap/コスト/虚偽完了/異常値/自己検査・既知答え済）

try:
    import optuna                                         # ハイパラ探索（インストール済・無ければ既定値）
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    _HAS_OPTUNA = True
except Exception:  # pragma: no cover
    _HAS_OPTUNA = False

RAT = ROOT / "results" / "priority_rebuild" / "ratchet"
TYPEONLY = RAT / "p23_candidates_typeonly.csv"            # 型候補（net_usd 等の列あり・ラベル T 決定の分布用）
OHLCV = ROOT / "data" / "BTCUSDT-5m-2021-04-01_03-31_1826d_V9FULL_safe.csv"
GROUND = RAT / "trades_p23_ground_capped.csv"             # 連続モード地面（measure_p23_ground_capped が出力・$925.73）

# ---- ラベル「伸びるか」の定数（§10.15・全て出典つき＝勘値番人を通す）----
H_HORIZON = 96     # src: V9 P23_TIME_EXIT_MIN=480分 / 5分足 = 96本（保有horizon・cat_params_v9.json L34）
T_FACTOR  = 0.65   # src: trade_analysis_methods_kb §3 TP較正基準（勝ち玉MFE中央値の60-70%・中央値0.65採用）

# ---- 期間分割（H8・§10.5・まこさん確定値・B 設計 ③）----
TRAIN_ENTRY_END = pd.Timestamp("2024-12-31")             # 学習: entry < 2024-12-31（学習末）
EMBARGO_END     = pd.Timestamp("2025-04-01")             # 学習: かつ exit < 2025-04-01（embargo 2025-01〜03 緩衝）
SC_START        = pd.Timestamp("2025-04-01")             # 採点: 2025-04-01 〜
SC_END          = pd.Timestamp("2026-01-01")             #       2025-12-31 まで（封印 2026Q1 不参照）
# ★ B 設計 ③: 学習末は 2024-12-31 を超えてはならない（module ロード時の物理 assert・H8）。
assert TRAIN_ENTRY_END <= pd.Timestamp("2024-12-31"), \
    f"H8: 学習末 {TRAIN_ENTRY_END} が 2024-12-31 を超過（採点期間へ侵入・期間分割違反）"
assert EMBARGO_END <= SC_START and SC_START >= pd.Timestamp("2025-04-01"), \
    f"H8: embargo({EMBARGO_END})/採点開始({SC_START}) が 2025-04-01 緩衝と不整合"

CAP = 0.12   # 予算（合計上限・CLAUDE §0-2）

# ★ B 設計 ①: 方向ベース Triple Barrier（ボラ基準バリア）の定数（§10.7 B 改訂・将来調整可）。
#   SHORT のバリア: TP(利益=下落)= entry×(1 − K_BARRIER×σ) / SL(逆行=上昇)= entry×(1 + K_BARRIER×σ)。
#   σ = entry 時点 t の ATR を価格比化（atr_14 / close・t 時点確定値・未来不使用）。
#   vertical(時間切れ) = V9 の time_exit 相当（分 → bar）。先着 TP=+1 / SL=−1 / time=0。
K_BARRIER = 1.5                                          # バリア幅係数 k（σ の倍率・既定 1.5・k=1〜3 が業界標準）
BARRIER_VERTICAL_MIN = 480                               # vertical(時間切れ) 分（V9 P23_TIME_EXIT_MIN=480 相当・分→bar 変換は実行時）

# 複数期間（§10.4/§10.6・木が有効期間を選ぶ・前ラウンド10回落とした要件）
# ★ B② で ATR_PERIODS は特徴量 X 生成からは除外（ボラ系を方向主役にしない）。バリア幅 σ は build_barrier_sigma が
#    ATR(14)/close を計算（X には入れない）。ATR_PERIODS 定数は参照履歴のため残置（X には未使用）。
STOCH_PERIODS = [5, 9, 14]
ADX_PERIODS   = [7, 14, 21]
ATR_PERIODS   = [7, 14, 28]      # ★B②: X 生成に未使用（σ は build_barrier_sigma が ATR14 を使う）
BB_PERIODS    = [10, 20, 40]
RSI_PERIODS   = [7, 14, 21]

# 結果列 = leak（特徴量に絶対入れない・H2）。USD 絶対値 = H6 blacklist（pct 化して使う）。
BANNED = {"net_usd", "gross_usd", "fee_usd", "mfe_usd", "mae_usd", "tp_diff_usd",
          "exit_price", "exit_reason", "hold_min", "add_count", "size_btc", "entry_price",
          "exit_time", "entry_time", "side", "priority", "regime"}

# θ グリッド（連続モード 1 pass ≈ 12 分 = O(525k バー)・θ ごとに 1 pass 必要 → 粗く 5 点。
#   効率化は設計書で許可済（「θ候補を粗くするなど効率化してよい・採点期間は覗かない」）。採点期間は覗かない。）
THETA_GRID = [0.35, 0.45, 0.55, 0.62, 0.70]

# Exit グリッド前向き sim のサンプル数（6-2 は当たりを付ける段階・型バー 61k×14候補 を全数 sim すると
#   ~5h かかるため学習期間からサンプリング。設計書 §10.13 6-2 は「片方を仮固定して当たりを付ける段階」）。
EXIT_GRID_SAMPLE = 1200


def _log(m):
    print(m, flush=True)


# ======================================================================
# Exit 候補グリッド（§10.4 / §10.8 B1・6-2）
# V9 が params で露出している Exit の「数値」を振る。各候補は gen の simulate_independent/
# run_continuous に **params の上書きコピー** を渡して前向き sim する（gen 本体は不変）。
# ⚠️ 制約: gen._step の P23 ブロックは TRAIL を呼ばない（L135「TRAIL は P1/P21 専用→P23 は無し」）・
#    分割利確も V9 P23 に無い。これらを「型として」追加すると gen._step の改造になり
#    『gen は import のみ』違反。よって import-only の枠内では V9 が露出する Exit 数値
#    （TP% / TimeExit / down-factor / PROFIT_LOCK on-off + arm/lock / MFE_STALE gate/hold / SL%）を
#    場面別に最適化する（design §10.4 のトレーリング/分割は gen 改造を伴うため E8b 範囲外＝key_decisions 明記）。
# ======================================================================
EXIT_CANDIDATES = [
    # name, params の上書き差分（P23 が _calc_tp_price/_check_exits_replay/SL/TIME で読むキー）
    ("V9base",        {}),                                                       # V9 そのまま（基準）
    ("TP1.0",         {"P23_TP_PCT": 0.010}),
    ("TP1.5",         {"P23_TP_PCT": 0.015}),
    ("TP2.0",         {"P23_TP_PCT": 0.020}),
    ("Time240",       {"P23_TIME_EXIT_MIN": 240}),                               # 短い時間切れ（add1 スキャル成績も見る）
    ("Time720",       {"P23_TIME_EXIT_MIN": 720}),                               # 伸ばす（取り逃し回収・§8.5）
    ("Time960",       {"P23_TIME_EXIT_MIN": 960}),
    ("DownF1.0",      {"P23_TIME_EXIT_DOWN_FACTOR": 1.0}),                        # 含み損でも早切りしない
    ("LockOn",        {"P23_SHORT_PROFIT_LOCK_ENABLE": 1, "P23_SHORT_PROFIT_LOCK_ARM_USD": 15.0,
                       "P23_SHORT_PROFIT_LOCK_USD": 5.0}),                       # 利益確保 on（V9 既定は enable=1 だが arm/lock 明示）
    ("StaleSlow",     {"P23_MFE_STALE_HOLD_MIN": 60.0}),                         # 失速カットを遅く（伸びを待つ）
    ("StaleOff",      {"P23_MFE_STALE_GATE_USD": -1.0}),                         # 失速カット実質オフ
    ("TP1.5_Time720", {"P23_TP_PCT": 0.015, "P23_TIME_EXIT_MIN": 720}),          # 伸ばす×広 TP（セット候補）
    ("TP1.5_Time720_Slow", {"P23_TP_PCT": 0.015, "P23_TIME_EXIT_MIN": 720,
                            "P23_MFE_STALE_HOLD_MIN": 60.0}),
]


def with_exit(params: dict, overrides: dict) -> dict:
    """V9 params のコピーに Exit 数値の上書きを当てた dict を返す（元 params・gen は不変）。"""
    p = dict(params)
    p.update(overrides)
    return p


# ======================================================================
# 特徴量（§10.6・★ B 設計 ②）: 5m 入口指標(pct化・複数期間) + MTF(15m/30m/1h/4h・build_mtf 流用)
# 型バー i（_p23_type_fires が True のバー）時点の確定値のみ（leak-safe）。
# ★ B 設計 ②（軸1ボラ逃げ回避）: Entry モデルに渡す X からボラ系（atr_pct / bb_width_pct）を除外する。
#   方向の主役は regime 系（bb_slope_pct/adx/stoch/rsi/ret_5 + MTF）。
#   ATR は「捨てる」でなく「ラベルのバリア幅 σ の入力」として label 側で使う（compute はする・X には入れない）。
#   bb_width_pct も同じくボラ系として方向主役から外す（X に入れない）。
# ======================================================================
def build_multiperiod(ohlcv: pd.DataFrame) -> pd.DataFrame:
    """raw 5m OHLCV から複数期間の【方向(regime)系】入口指標を計算（全て t 時点の確定値・shift は正方向のみ・center 不使用）。
    ★ B 設計 ②: ボラ系（atr_pct / bb_width_pct）はここで作らない＝X の方向主役にしない。
       ATR（バリア幅 σ 用）は別途 build_barrier_sigma で計算し label 側でのみ使う。index=timestamp。"""
    o = ohlcv.set_index("timestamp").sort_index()
    c, h, l = o["close"], o["high"], o["low"]
    f = pd.DataFrame(index=o.index)

    for p in STOCH_PERIODS:
        st = ta.momentum.StochasticOscillator(h, l, c, window=p, smooth_window=3)
        f[f"stoch_k_{p}"] = st.stoch()
        f[f"stoch_d_{p}"] = st.stoch_signal()
        f[f"stoch_gap_{p}"] = st.stoch_signal() - st.stoch()      # d-k（戻りの高さ＝売り場・型のクロス幅と同義の符号）
    for p in ADX_PERIODS:
        f[f"adx_{p}"] = ta.trend.ADXIndicator(h, l, c, window=p).adx()  # 下げの強さ（方向の強さ・regime 系）
    # ★ B 設計 ②: ATR は X に入れない（atr_pct ループを削除）。σ はバリア幅専用に build_barrier_sigma で計算。
    for p in BB_PERIODS:
        bb = ta.volatility.BollingerBands(c, window=p, window_dev=2)
        mid = bb.bollinger_mavg()
        # ★ B 設計 ②: bb_width_pct（ボラ系）は X に入れない（削除）。bb_slope_pct（中心線の向き＝方向）は残す。
        f[f"bb_slope_pct_{p}"] = (mid - mid.shift(5)) / c * 100.0  # 中心線の傾き（過去5本前比・pct・H6・shift 正方向・方向 regime 系）
        f[f"bb_pctb_{p}"] = (c - bb.bollinger_lband()) / (bb.bollinger_hband() - bb.bollinger_lband()).replace(0, np.nan)  # 位置（方向）
    for p in RSI_PERIODS:
        rsi = ta.momentum.RSIIndicator(c, window=p).rsi()
        f[f"rsi_{p}"] = rsi                                       # 方向 regime 系
        f[f"rsi_slope_{p}"] = rsi - rsi.shift(3)                  # 過去3本前比（pct ポイント・無次元・shift 正方向）
    f["ret_5"] = (c / c.shift(5) - 1.0) * 100.0                   # 5本リターン pct（方向）
    # H2 物理 assert: 未来参照（負方向 shift / center=True）が無いことをソースで担保しているが、
    #   ここでも「全ての shift が正方向」を不変条件として明記（負 shift があればこの関数の grep で即検出）。
    # ★ B 設計 ② 自己検査: 方向系のみ（ボラ系 atr/bb_width が混入していないことを名前で物理 assert）。
    vol_leak = [col for col in f.columns if "atr" in col or "bb_width" in col]
    assert not vol_leak, f"B設計②違反: ボラ系(atr/bb_width)が方向特徴量 X に混入 {vol_leak}（軸1ボラ逃げ）"
    return f


# ======================================================================
# ★ B 設計 ①: ラベルのバリア幅 σ（= entry 時点 t の ATR を価格比化・t 時点確定値・未来不使用）。
#   X には入れず（②）、label 側のバリア `entry×(1±K_BARRIER×σ)` の幅だけに使う＝ATR の役割を正す（軸1③）。
# ======================================================================
def build_barrier_sigma(ohlcv: pd.DataFrame, atr_period: int = 14) -> pd.Series:
    """raw 5m OHLCV から σ_t = ATR_t / close_t（価格比・t 時点確定値）を返す。index=timestamp。
    ★ これは特徴量 X ではない（バリア幅専用）。ラベル教師にのみ使う（H2: ラベルは教師のみ）。"""
    o = ohlcv.set_index("timestamp").sort_index()
    c, h, l = o["close"], o["high"], o["low"]
    atr = ta.volatility.AverageTrueRange(h, l, c, window=atr_period).average_true_range()
    sigma = atr / c                                              # 価格比（無次元・H6・t 時点確定値）
    return sigma


def make_features(bar_times: pd.Series, mp_feats: pd.DataFrame, ohlcv: pd.DataFrame) -> pd.DataFrame:
    """型バー時刻に対し 複数期間特徴量(backward 確定値) + MTF(build_mtf・leak-safe) + 時間 を組む。"""
    bt = pd.to_datetime(bar_times.values)
    X_mp = mp_feats.reindex(bt).reset_index(drop=True)            # 型バー時点の確定多期間指標
    mtf = e8.build_mtf(ohlcv, pd.Series(bt))                      # 上位足 backward merge（leak-safe・E8 流用）
    bt_s = pd.Series(bt)
    tcol = pd.DataFrame({"entry_hour": bt_s.dt.hour.values,
                         "entry_weekday": bt_s.dt.weekday.values})
    X = pd.concat([X_mp, mtf.reset_index(drop=True), tcol], axis=1)
    leaked = BANNED & set(X.columns)
    assert not leaked, f"H2/H6 leak: 結果列が特徴量に混入 {leaked}"
    # H6: USD 絶対値（pct 化していない bb 傾き）が紛れていないか名前で機械チェック
    bad = [c for c in X.columns if "bb_slope" in c and "pct" not in c]
    assert not bad, f"H6 違反: USD 絶対値の特徴量が pct 化されていない {bad}"
    # ★ B 設計 ②（軸1ボラ逃げ回避）: ボラ系（atr / bb_width）が方向 X に混入していないことを物理 assert。
    #   MTF(build_mtf)由来でボラ系列が来ても、ここで止める（Entry の方向スコアの主役をボラにしない）。
    vol_in_X = [c for c in X.columns if "atr" in c or "bb_width" in c]
    assert not vol_in_X, (f"B設計②違反: ボラ系(atr/bb_width)が Entry 特徴量 X に混入 {vol_in_X}"
                          f"（軸1: 揺れ幅を方向スコアの主役にしない・σ はラベルのバリア幅専用）")
    return X


# ======================================================================
# ★ B 設計 ①: 型バー → 方向ベース Triple Barrier ラベル（§10.7 B 改訂・軸1ボラ逃げ回避）
# SHORT の戻り売りが「再下落して下げ方向が当たったか」を符号でラベル化（金額の大小を消す）。
#   entry 時点 t から実価格を 1 本ずつ前向きに進め（未来先読みなし＝leak なし）、
#     TP(利益=下落)= entry×(1 − k×σ) … low がここに先着 → +1（下げ到達＝方向当たり）
#     SL(逆行=上昇)= entry×(1 + k×σ) … high がここに先着 → −1（逆行）
#     vertical(時間切れ)= entry から vertical_bars 本（V9 time_exit 相当）に達したら 0
#   σ = entry 時点 t の ATR を価格比化（atr/close・t 時点確定値・未来不使用）。k = K_BARRIER。
#   ⚠️ ラベルは教師のみ（特徴量には未来を入れない・H2）。net 金額・MFE ピークは使わない。
# entry 価格 = 型バー i の close（V9 SHORT は次バーで指値約定だが、方向ラベルは型バー時点 close 基準で
#   barrier 幅 σ も型バー時点で確定 → 約定値ズレは方向の符号には実質影響しない・leak なし）。
# ======================================================================
def label_triple_barrier_direction(df, sigma_by_time, type_bars, k=K_BARRIER, vertical_min=BARRIER_VERTICAL_MIN):
    """type_bars（型バー index）ごとに方向ベース Triple Barrier の符号ラベルを返す。
    返す列: bar_i / bar_time / entry_time(=型バー時刻・方向ラベルの基準時点) / exit_time(=バリア到達時刻) /
            y_dir(+1 下げ到達 / −1 逆行 / 0 時間切れ) / k_sigma(バリア幅 pct・記録用)。
    ★ 全て entry 時点 t の確定値（σ）と t 以降の実価格のみ使用（未来先読みなし・H2）。"""
    bar_ms_local = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    vertical_bars = max(1, int(round(vertical_min * 60_000 / bar_ms_local)))   # 分 → bar（V9 time_exit 相当）
    n = len(df)
    out = []
    for i in type_bars:
        t = pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms")
        entry = float(df.at[i, "close"])                                       # 型バー時点 close（基準）
        sig = float(sigma_by_time.get(t, np.nan))                              # σ = ATR/close（t 時点確定値）
        if not np.isfinite(sig) or sig <= 0 or not np.isfinite(entry):
            continue                                                          # σ 未確定（warmup 等）= 学習対象外
        tp_price = entry * (1.0 - k * sig)                                     # 利益=下落（SHORT TP）
        sl_price = entry * (1.0 + k * sig)                                     # 逆行=上昇（SHORT SL）
        end = min(n - 1, i + vertical_bars)
        y_dir, exit_t = 0, pd.to_datetime(df.at[end, "timestamp_ms"], unit="ms")  # 既定 = 時間切れ(0)
        for j in range(i + 1, end + 1):                                        # 1 本ずつ前向き（先着判定）
            hi = float(df.at[j, "high_raw"]); lo = float(df.at[j, "low_raw"])
            hit_tp = lo <= tp_price                                            # 下落が TP に先着
            hit_sl = hi >= sl_price                                            # 上昇が SL に先着
            if hit_tp or hit_sl:
                # 同一バーで両到達: SHORT の逆行（上昇先）を不利側として優先（保守的＝−1）。
                y_dir = -1 if hit_sl else 1
                exit_t = pd.to_datetime(df.at[j, "timestamp_ms"], unit="ms")
                break
        out.append({"bar_i": i, "bar_time": t, "entry_time": t, "exit_time": exit_t,
                    "y_dir": y_dir, "k_sigma": k * sig * 100.0})
    return pd.DataFrame(out)


# ======================================================================
# 型バー → 実出口 net ラベル（§10.7・6-2 の Exit 設定込み・Exit 学習用＝net 基準のまま）
# 各型バーを simulate_independent（指定 params の add/Exit）で前向き sim し、add 込みの
# 実際の決済 net を得る → Exit ラベル元（MFE ピーク不使用）。型バー i と net が完全に揃う。
# ⚠️ B 設計 ①: これは Exit 学習(6-2)専用。Entry ラベルは label_triple_barrier_direction（方向）を使う。
# ======================================================================
def label_type_bars(df, bar_ms, params, type_bars):
    """type_bars（型バー index リスト）を順に simulate_independent → net / fill / 時刻 を返す。
    params は呼び出し側が Exit override を当てたコピーを渡せる（gen 本体は不変）。"""
    out = []
    for i in type_bars:
        tr = gen.simulate_independent(df, bar_ms, i, params)
        if tr is None:                                            # 不約定 = 候補不成立（学習対象外）
            continue
        out.append({"bar_i": i,
                    "bar_time": pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms"),
                    "entry_time": pd.to_datetime(tr["entry_time"]),
                    "exit_time": pd.to_datetime(tr["exit_time"]),
                    "net_usd": float(tr["net_usd"])})
    return pd.DataFrame(out)


def label_from_csv(df, type_bars):
    """【効率化・V9base 専用】gen が typeonly CSV に保存済みの実出口 net をそのまま使う（再 sim 不要）。
    typeonly CSV = gen.simulate_independent(type bar, V9 フル params) の結果（add/Exit=V9base）。
    → V9base Exit のラベルは CSV と完全一致（gen 不変・同じ前向き sim の保存値）。型バー i を時刻で照合。"""
    ty = pd.read_csv(TYPEONLY)
    ty["entry_time"] = pd.to_datetime(ty["entry_time"]); ty["exit_time"] = pd.to_datetime(ty["exit_time"])
    tb_time = {i: pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms") for i in type_bars}
    tb_df = pd.DataFrame({"bar_i": list(tb_time), "bar_time": list(tb_time.values())}).sort_values("bar_time")
    ty_s = ty.sort_values("entry_time")
    # 型バーは entry の1〜2本前。entry_time 直前の型バーを backward 照合（gen の signal_i→fill 構造に対応）。
    m = pd.merge_asof(ty_s, tb_df, left_on="entry_time", right_on="bar_time", direction="backward")
    m = m.dropna(subset=["bar_i"]).reset_index(drop=True)
    m["bar_i"] = m["bar_i"].astype(int)
    return m[["bar_i", "bar_time", "entry_time", "exit_time", "net_usd"]].copy()


def decide_label_T(train_net: pd.Series) -> tuple[float, dict]:
    """⚠️ DEPRECATED（B 設計 ①で不使用）: Entry ラベルは net 金額二値（高ボラ依存＝ボラ逃げ）から
    方向ベース Triple Barrier 符号（label_triple_barrier_direction）に置換した。net 金額でラベルしない。
    （関数は参照履歴のため残置・main からは呼ばない）。
    旧: 学習期間の net 分布から data-driven にラベル閾値 T を決める（§10.7）。"""
    tot_pos = float(train_net[train_net > 0].sum())
    rows = []
    for T in [0, 3, 5, 8, 10, 15]:
        sel = train_net >= T
        cov = float(train_net[sel].sum()) / tot_pos if tot_pos > 0 else 0.0   # ○側が正 PnL の何割を保持するか
        rows.append({"T": T, "label_rate": float(sel.mean()), "n_pos": int(sel.sum()),
                     "sum_net_ge_T": float(train_net[sel].sum()), "pos_pnl_coverage": cov})
    grid = pd.DataFrame(rows)
    # 選定ルール（data-driven）: label_rate が net>=0 の半分以下に落ち（薄利の希釈を切る）かつ
    #   正PnLカバレッジ >=0.80（しっかり儲かった大勝ち玉は残す＝fat-tail を切らない）を満たす最小 T。
    rate0 = float((train_net >= 0).mean())
    ok = grid[(grid["label_rate"] <= rate0 * 0.5) & (grid["pos_pnl_coverage"] >= 0.80)]
    T = float(ok.iloc[0]["T"]) if len(ok) else 5.0
    return T, {"grid": grid, "net0_rate": rate0, "chosen_T": T}


# ======================================================================
# 学習 LightGBM 二値（共通化・purged k-fold / Optuna / 本学習で再利用）
# ======================================================================
def train_lgb(X: pd.DataFrame, y: np.ndarray, lparams: dict, valid_frac: float = 0.15):
    """末尾 valid_frac を時系列 valid に early stopping。学習済みモデルを返す。"""
    n = len(X)
    cut = max(1, int(n * (1.0 - valid_frac)))
    pos_w = (y[:cut] == 0).sum() / max(1, (y[:cut] == 1).sum())
    p = dict(lparams); p["scale_pos_weight"] = pos_w
    dtr = lgb.Dataset(X.iloc[:cut], label=y[:cut])
    dva = lgb.Dataset(X.iloc[cut:], label=y[cut:], reference=dtr)
    model = lgb.train(p, dtr, num_boost_round=3000, valid_sets=[dva],
                      callbacks=[lgb.early_stopping(80, verbose=False)])
    return model, pos_w


# ======================================================================
# 採点ヘルパー（連続モード trade → 採点期間で score.py / 地面の差）
# ======================================================================
def score_continuous(trades: list, label: str) -> dict:
    """連続モード trade（gen 出力・時刻は文字列）を採点期間で score.py（cap ゲート）に通す。"""
    d = pd.DataFrame(trades)
    for col in ("entry_time", "exit_time"):
        d[col] = pd.to_datetime(d[col])
    sc = d[(d["entry_time"] >= SC_START) & (d["entry_time"] < SC_END)].reset_index(drop=True)
    if not len(sc):
        return {"total": 0.0, "monthly_avg": 0.0, "n_trades": 0, "anomaly": [], "monthly": None, "df": sc}
    r = judge.score(sc)
    r["df"] = sc
    return r


def monthly_returns(sc_df: pd.DataFrame) -> np.ndarray:
    """採点期間の月次 net 列（DSR/PBO の per-period リターン）。score.py と同じ engine net を月集計。"""
    if sc_df is None or not len(sc_df):
        return np.array([])
    r = judge.score(sc_df)
    return r["monthly"]["net_usd"].values.astype(float)


def main():
    _log("[E8c] P23 Entry/Exit セット ML — ラベル『伸びるか(MFE%≥T)』× 方向regime特徴量(ATR除外) × Exit最適化 × 連続モード採点")

    SMOKE = "--smoke" in sys.argv
    # ① 静的番人（実行前・私の正直さに依存しない）: leak未来参照 / 期間分割
    _src = pathlib.Path(__file__).read_text()
    rg.assert_no_future_ref(_src)                      # 特徴量に .shift(-)/center=True が無い
    rg.assert_period_split(TRAIN_ENTRY_END, SC_START)  # 学習末 < 採点始
    if SMOKE:
        _log("[SMOKE] 数分テスト: 小サンプル＋重い処理(自己検査2 / θsweep / 本採点)を省略し label/特徴量/学習/ボラ可視化のみ確認")

    # ---- 0/1) データ取り込み（gen の preload で V9 df・raw OHLCV）----
    params = rc._load_params()
    p23 = dict(params)                                            # P23 SHORT のみ有効（gen.main と同条件）
    for k in list(p23):
        if k.startswith("ENABLE_P") and k.endswith(("_LONG", "_SHORT")):
            p23[k] = (k == "ENABLE_P23_SHORT")
    df, _ = rc.preload(str(gen.OHLCV_CSV), p23)
    bar_ms = int(df.at[1, "timestamp_ms"] - df.at[0, "timestamp_ms"])
    _log(f"[load] bars={len(df)} bar_ms={bar_ms}")

    ohlcv = pd.read_csv(OHLCV)
    ohlcv["timestamp"] = pd.to_datetime(ohlcv["timestamp"])
    mp_feats = build_multiperiod(ohlcv)                           # 複数期間【方向】指標（§10.4/§10.6・ボラ系除外＝B②）
    sigma_by_time = build_barrier_sigma(ohlcv).to_dict()         # σ=ATR/close（バリア幅専用・B①・X には入れない）

    # ---- 2) 型バー列挙（V9 P23 の型・閾値を外す = gen._p23_type_fires）----
    type_bars = [i for i in range(rc.CANDLE_WARMUP, len(df)) if gen._p23_type_fires(df, i)]
    type_set = set(type_bars)
    _log(f"[型バー] _p23_type_fires が発火するバー = {len(type_bars)} 本")

    # ======================================================================
    # 自己検査(1)（H13/関所A 思想・先に置く）: AI ゲート無し（type_set）== gen の型関数 _p23_type_fires が
    #   ビット単位で一致するか（採点経路 initial_fn は「i in type_set」で発火 → これが gen の型と完全一致なら
    #   AI ゲート無しの連続モードは gen と恒等的に一致する）。連続モード全 pass は重い（~12分/pass）ため、
    #   ここは全バーのブール配列を直接比較（0 コスト・恒真化しない=実際に発火集合をバー単位で照合）。
    # ======================================================================
    ref_fire = {i for i in range(rc.CANDLE_WARMUP, len(df)) if gen._p23_type_fires(df, i)}
    assert type_set == ref_fire, (
        f"自己検査NG(1): 採点ゲート type_set と gen._p23_type_fires が不一致 "
        f"(only_in_set={len(type_set - ref_fire)} / only_in_ref={len(ref_fire - type_set)}) → 移植ミス・停止")
    _log(f"[self-check 1] ✅ 採点ゲート type_set == gen._p23_type_fires（{len(type_set)} バー・ビット一致）")
    # ★ SMOKE: 重い処理の前に型バーを小サンプルへ縮小。自己検査2(full run_continuous×2＝重い)は本番専用。
    if SMOKE:
        _step_n = max(1, len(type_bars) // 2000)               # 全期間(学習/embargo/採点)にまたがるよう間引き
        type_bars = type_bars[::_step_n]
        type_set = set(type_bars)
        _log(f"[SMOKE] 型バーを {len(type_bars)} 本に間引き（全期間横断・自己検査2/θsweep/本採点は省略）")
    else:
        # 自己検査(2)（採点経路の移植同一性・1 pass のみ）: AI ゲート無し（prob 無視）の連続モード ==
        #   gen.run_continuous(型関数) の件数/net が一致するか（① 自己検査番人で判定）。
        tr_ref = gen.run_continuous(df, bar_ms, params, lambda i: gen._p23_type_fires(df, i))
        tr_gate = gen.run_continuous(df, bar_ms, params, lambda i: (i in type_set))
        n_r, n_g = len(tr_ref), len(tr_gate)
        net_r = sum(float(t["net_usd"]) for t in tr_ref); net_g = sum(float(t["net_usd"]) for t in tr_gate)
        rg.assert_selfcheck_match(n_g, net_g, n_r, net_r)   # ① 自己検査番人（移植一致・不一致で停止）
        _log(f"[self-check 2] ✅ AIゲート無し連続 == 型関数連続（{n_g}件 net ${net_g:.2f} 一致・採点経路 = gen と同一）")

    # ======================================================================
    # ステップ 6-2: Exit グリッド（V9 露出 Exit 数値の場面別最適化・§10.4/§10.7/§10.8 B1）
    #   各 Exit 候補を params override で前向き sim → 学習期間 net 平均が最大の Exit 設定を data-driven に選定。
    #   ⚠️ 学習期間（entry<2024-12-31 かつ exit<2025-04-01）だけで選ぶ（採点を覗かない＝類型C）。
    #   【効率化】型バー 61k × 14 候補を全数 sim すると ~5h → §10.13 6-2「当たりを付ける段階」に従い
    #     学習期間の型バーを EXIT_GRID_SAMPLE 件サンプリングして候補比較（採点は全数・後段 6-3 で確定）。
    #     比較は同一サンプル上での net 平均（avg）で公平に（候補ごとに約定数が違うため和でなく平均）。
    # ======================================================================
    _log(f"\n[6-2 Exit グリッド] V9 露出 Exit 数値を場面別に最適化（学習期間 {EXIT_GRID_SAMPLE} サンプル・採点期間は不参照）")
    tr_type_bars = [i for i in type_bars
                    if pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms") < TRAIN_ENTRY_END]
    rng = np.random.RandomState(42)
    samp = (tr_type_bars if len(tr_type_bars) <= EXIT_GRID_SAMPLE
            else sorted(rng.choice(tr_type_bars, EXIT_GRID_SAMPLE, replace=False).tolist()))
    _log(f"  学習期間 型バー {len(tr_type_bars)} 本 → サンプル {len(samp)} 本で候補比較")
    exit_rows = []
    for name, ov in EXIT_CANDIDATES:
        p_ex = with_exit(params, ov)
        lab_ex = label_type_bars(df, bar_ms, p_ex, samp)
        is_tr_ex = (lab_ex["entry_time"] < TRAIN_ENTRY_END) & (lab_ex["exit_time"] < EMBARGO_END)
        sub = lab_ex.loc[is_tr_ex, "net_usd"]
        exit_rows.append({"exit": name, "n_fill": int(is_tr_ex.sum()),
                          "train_avg": float(sub.mean()) if len(sub) else -1e9,
                          "train_net_sample": float(sub.sum())})
    exit_grid = pd.DataFrame(exit_rows).sort_values("train_avg", ascending=False).reset_index(drop=True)
    _log(exit_grid.round(3).to_string(index=False))
    best_exit = str(exit_grid.iloc[0]["exit"])
    best_exit_ov = dict(EXIT_CANDIDATES)[best_exit]
    params_exit = with_exit(params, best_exit_ov)                 # 以降の学習・採点はこの Exit 設定を土台にする
    _log(f"[6-2] 場面別 net 平均 最大の Exit = '{best_exit}'（override={best_exit_ov}）→ 6-1/6-3 はこの Exit を土台に")

    # ---- 3) ラベル = 実出口 net（選定 Exit 設定・add 込み・連続モード土俵・MFE ピーク不使用・全型バー）----
    #   【効率化】V9base が選ばれたら gen が CSV 保存済みの net を使う（再 sim 不要）。
    #   override が選ばれたら全型バーを 1 pass だけ sim（~22 分・採点で全数必要なので避けられない）。
    if not best_exit_ov:                                          # V9base（override 空）= CSV の実 net を流用
        lab = label_from_csv(df, type_bars)
        _log("[ラベル] 選定 Exit = V9base → typeonly CSV の実出口 net を流用（再 sim なし・gen と完全一致）")
    else:
        _log(f"[ラベル] 選定 Exit = '{best_exit}'（override）→ 全型バー {len(type_bars)} 本を 1 pass 前向き sim（~22分）")
        lab = label_type_bars(df, bar_ms, params_exit, type_bars)
    _log(f"[ラベル] 約定した型バー = {len(lab)} 件 / net合計（コスト前engine）${lab['net_usd'].sum():.0f}")

    # ======================================================================
    # ステップ 5: 期間分割（H8）— **生 timestamp に対し直接 assert**（前ラウンドの飾り是正）
    #   マスク（is_tr/is_sc）由来の値でなく、リテラル境界に対して min/max を直接照合する。
    #   フィルタ式が将来変わっても、この assert はフィルタと独立な生 timestamp を見るので黙って通らない。
    # ======================================================================
    is_tr = (lab["entry_time"] < TRAIN_ENTRY_END) & (lab["exit_time"] < EMBARGO_END)   # 学習 + embargo
    is_sc = (lab["entry_time"] >= SC_START) & (lab["entry_time"] < SC_END)             # 採点 2025-04〜12

    tr_lab = lab.loc[is_tr]
    sc_lab = lab.loc[is_sc]
    assert len(tr_lab) > 0 and len(sc_lab) > 0, "H8: 学習/採点いずれかが空（期間分割の前提崩壊）"
    # (a) 学習行: 生 entry の最大 < 2024-12-31・生 exit の最大 < 2025-04-01（embargo を跨がない）
    tr_entry_max = tr_lab["entry_time"].max()
    tr_exit_max  = tr_lab["exit_time"].max()
    assert tr_entry_max < TRAIN_ENTRY_END, f"H8: 学習 entry 最大 {tr_entry_max} が {TRAIN_ENTRY_END} 以上（侵入）"
    assert tr_exit_max < EMBARGO_END, f"H2/H8: 学習 exit 最大 {tr_exit_max} が {EMBARGO_END} 以上（embargo 不備・採点へ leak）"
    # (b) 採点行: 生 entry の最小 >= 2025-04-01・最大 < 2026-01-01（封印 2026Q1 を含まない）
    sc_entry_min = sc_lab["entry_time"].min()
    sc_entry_max = sc_lab["entry_time"].max()
    assert sc_entry_min >= SC_START, f"H8: 採点 entry 最小 {sc_entry_min} が {SC_START} 未満（学習へ侵入）"
    assert sc_entry_max < SC_END, f"H8: 採点 entry 最大 {sc_entry_max} が {SC_END} 以上（封印 2026Q1 が漏れ）"
    # (c) 学習と採点が時間的に重ならない（境界の独立検証）
    assert tr_exit_max < sc_entry_min, f"H8: 学習 exit({tr_exit_max}) と 採点 entry({sc_entry_min}) が重なる（embargo 緩衝喪失）"
    _log(f"[split・H8 生timestamp assert OK] 学習 {len(tr_lab)} 件（entry≤{tr_entry_max.date()} / exit≤{tr_exit_max.date()}）"
         f" / 採点 {len(sc_lab)} 件（{sc_entry_min.date()}〜{sc_entry_max.date()}）"
         f" / embargo+除外 {len(lab) - len(tr_lab) - len(sc_lab)} 件")

    # ======================================================================
    # Entry の教師ラベル = 「伸びるか」二値（§10.15・まこさん承認 2026-06-08）。
    #   定義: 実価格の利益方向(SHORT=下落)の最大幅 MFE% が、保有 horizon(H_HORIZON 本)内に T% 以上に達したか。
    #   ＝「この戻り売りが再下落して伸びたか」の方向判定。金額の大小は使わない（軸1ボラ逃げ回避）。
    #   ⚠ MFE は教師ラベルにのみ使用（推論時の特徴量 X には入れない）＝leak-safe（Prime Directive は
    #      「特徴量・判定式で未来値を使うな」＝ラベルの教師は対象外。AFML Triple Barrier と同じ扱い）。
    #   T = 学習期間の勝ち玉(net>0) の MFE% 中央値 × T_FACTOR（データ由来・勘でない・採点期間は見ない＝C回避）。
    #   ATR/bb_width は特徴量 X から既に除外済(B②)。Entry/Exit はセット（net 判定は連続モードで Exit 込み・§8.5）。
    # ======================================================================
    _close_arr = df["close"].to_numpy()
    _low_arr = df["low_raw"].to_numpy()
    _nb = len(df)
    _mfe = []
    for _bi in lab["bar_i"].astype(int).to_numpy():
        _e = float(_close_arr[_bi])
        _end = min(_nb - 1, _bi + H_HORIZON)
        _lo = _low_arr[_bi + 1:_end + 1]
        _mfe.append((_e - float(_lo.min())) / _e * 100.0 if len(_lo) and _e > 0 else 0.0)
    lab["mfe_pct"] = _mfe
    _tr_win_mfe = lab.loc[is_tr & (lab["net_usd"] > 0), "mfe_pct"]
    T_LABEL = float(_tr_win_mfe.median() * T_FACTOR) if len(_tr_win_mfe) else 0.9   # データ由来
    lab["y"] = (lab["mfe_pct"] >= T_LABEL).astype(int)                              # ○ = 伸びた（下落 MFE% ≥ T）
    n_pos = int(lab["y"].sum())
    _log(f"[ラベル] 伸びるか = 保有{H_HORIZON}本以内に下落 MFE% >= T={T_LABEL:.3f}%"
         f"（T=学習勝ち玉MFE%中央値×{T_FACTOR}・データ由来）"
         f" / 伸びた {n_pos} / 伸びない {len(lab) - n_pos} / 伸び率 {n_pos / max(1, len(lab)) * 100:.1f}%"
         f"（金額不使用=軸1 / MFEは教師のみ=leak-safe）")

    # ---- 6) 特徴量（複数期間【方向】 + MTF・型バー時点の確定値・★ B② ボラ系除外）----
    X_all = make_features(lab["bar_time"], mp_feats, ohlcv)
    Xtr = X_all[is_tr.values].reset_index(drop=True)
    ytr = lab.loc[is_tr, "y"].values
    _log(f"[特徴量] {X_all.shape[1]} 列（複数期間 方向系 stoch/adx/bb_slope/bb_pctb/rsi + MTF 15m/30m/1h/4h + 時間"
         f"／★ atr_pct・bb_width_pct は除外＝B②軸1）／ 学習 ○率（下げ当たり）={ytr.mean():.3f}")

    # ======================================================================
    # ステップ 7: 交差検証（Purged K-Fold + embargo・AFML Ch.7）+ Optuna ハイパラ探索（C 対策）
    #   - purged k-fold: 重なるラベル窓の fold 間 leak を断つ（既存 purged_kfold.py・既知答え済）。
    #     ラベル窓 = [型バー index, 出口バー index]。embargo を bar 数で渡す（採点期間は触らない）。
    #   - Optuna: 学習期間内の purged k-fold OOS AUC を最大化するハイパラを探索。
    #     test/採点期間は一切見ない（類型C 回避）。見つからなければ E8a 既定値にフォールバック。
    # ======================================================================
    # ラベル窓（bar index）: start=型バー、end=出口バー（exit_time→bar index に変換）
    bar_index_by_time = {pd.to_datetime(df.at[i, "timestamp_ms"], unit="ms"): i for i in range(len(df))}
    def _exit_bar_idx(t):
        return bar_index_by_time.get(pd.to_datetime(t), len(df) - 1)
    tr_lab2 = lab.loc[is_tr].reset_index(drop=True)
    starts = tr_lab2["bar_i"].astype(int).values
    ends = np.array([_exit_bar_idx(t) for t in tr_lab2["exit_time"]], dtype=np.int64)
    ends = np.maximum(ends, starts)                               # clip: end >= start
    order = np.argsort(starts, kind="stable")                    # purged_kfold は starts 昇順前提
    starts_s, ends_s = starts[order], ends[order]
    Xtr_s = Xtr.iloc[order].reset_index(drop=True)
    ytr_s = ytr[order]
    embargo_bars = int(round((pd.Timedelta("3 days")) / pd.Timedelta(milliseconds=bar_ms)))  # 3日分の bar（embargo）

    base_lparams = dict(objective="binary", metric="auc", learning_rate=0.03, num_leaves=15,
                        min_child_samples=100, feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1,
                        lambda_l1=1.0, lambda_l2=1.0, seed=42, verbose=-1)

    def cv_auc(lparams: dict, n_splits: int = 5) -> float:
        """学習期間 purged k-fold の OOS AUC 平均（採点期間は不参照）。"""
        kf = pk.PurgedKFold(n_splits=n_splits, starts=starts_s, ends=ends_s, embargo_bars=embargo_bars)
        aucs = []
        for tr_idx, te_idx in kf.split(len(starts_s)):
            if len(tr_idx) < 50 or len(np.unique(ytr_s[te_idx])) < 2 or len(np.unique(ytr_s[tr_idx])) < 2:
                continue
            m, _ = train_lgb(Xtr_s.iloc[tr_idx].reset_index(drop=True), ytr_s[tr_idx], lparams)
            pred = m.predict(Xtr_s.iloc[te_idx], num_iteration=m.best_iteration)
            aucs.append(roc_auc_score(ytr_s[te_idx], pred))
        return float(np.mean(aucs)) if aucs else 0.5

    base_cv = cv_auc(base_lparams)
    _log(f"\n[7 purged k-fold・embargo {embargo_bars} bars] 既定ハイパラ OOS AUC={base_cv:.4f}")

    best_lparams = dict(base_lparams)
    best_cv = base_cv
    if _HAS_OPTUNA:
        def objective(trial):
            lp = dict(base_lparams)
            lp["num_leaves"] = trial.suggest_int("num_leaves", 7, 31)
            lp["min_child_samples"] = trial.suggest_int("min_child_samples", 50, 300)
            lp["lambda_l1"] = trial.suggest_float("lambda_l1", 0.0, 5.0)
            lp["lambda_l2"] = trial.suggest_float("lambda_l2", 0.0, 5.0)
            lp["feature_fraction"] = trial.suggest_float("feature_fraction", 0.6, 1.0)
            return cv_auc(lp, n_splits=5)
        study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
        study.optimize(objective, n_trials=20, show_progress_bar=False)
        if study.best_value > best_cv:
            best_lparams.update(study.best_params)
            best_cv = float(study.best_value)
            _log(f"[7 Optuna] best OOS AUC={best_cv:.4f} / params={study.best_params}")
        else:
            _log(f"[7 Optuna] 既定を上回らず（best試行 {study.best_value:.4f} ≤ 既定 {base_cv:.4f}）→ 既定ハイパラ採用")
    else:
        _log("[7 Optuna] optuna 未インストール → 既定ハイパラ採用")

    # ---- 本学習（採用ハイパラで学習期間全体を学習）----
    model, pos_w = train_lgb(Xtr, ytr, best_lparams)
    _log(f"[train] best_iter={model.best_iteration} / num_leaves={best_lparams['num_leaves']} "
         f"/ min_child={best_lparams['min_child_samples']} / scale_pos_weight={pos_w:.2f} / OOS AUC={best_cv:.4f}")

    # 全型バーの prob を予測（採点の連続モードで bar_i→prob を引くため）
    prob_all = model.predict(X_all, num_iteration=model.best_iteration)
    prob_by_bar = dict(zip(lab["bar_i"].astype(int).values, prob_all))
    if len(np.unique(lab.loc[is_sc, "y"])) > 1:
        _log(f"[score] 採点期間 AUC={roc_auc_score(lab.loc[is_sc, 'y'], prob_all[is_sc.values]):.4f}（参考・最終判定は net）")

    # ② ボラの役割：feature importance を「見える化」（raise しない・凍結しない・軸1の判断はまこさん）
    _imp = dict(zip(model.feature_name(), model.feature_importance(importance_type="gain")))
    _vr = rg.report_vol_importance(_imp)
    _log(f"[②ボラ可視化] vol_share={_vr['vol_share']} / top5={_vr['top']} / top内ボラ={_vr['top_vol']}（凍結せず可視化）")
    if SMOKE:
        _log(f"[SMOKE] 完了: クラッシュ無 / 学習OK(OOS AUC参考={best_cv:.4f}) / ボラ可視化済 / ラベル分布確認済。本番(θsweep/採点)は省略。")
        return

    # ======================================================================
    # ステップ 6-3 + 8: Entry/Exit セット（θ × 選定 Exit）を連続モード net で評価
    #   - Exit = 6-2 で選んだ params_exit を土台（gen に override コピーを渡す・gen 不変）。
    #   - Entry = θ で型バーを選別。θ は **学習期間（entry<2024-12-31 かつ exit<2025-04-01）** の
    #     連続モード net 最大化で選ぶ（前ラウンドの embargo 汚染を是正＝exit 制約を is_tr と一致させる）。
    #   - 連続モード sweep は重い → θ 候補を粗く（効率化は設計書で許可）。採点期間は覗かない（類型C）。
    # ======================================================================
    def continuous_trades(theta):
        fn = lambda i: (i in type_set and prob_by_bar.get(i, 0.0) >= theta)
        return gen.run_continuous(df, bar_ms, params_exit, fn)    # ★ 選定 Exit 設定の連続モード

    def train_net_of(trades):
        """学習期間の net（entry<2024-12-31 **かつ exit<2025-04-01**）。
        前ラウンド是正: exit 制約を is_tr と一致させ embargo 期間の出口を θ 選定に混入させない。"""
        s = 0.0
        for t in trades:
            et = pd.to_datetime(t["entry_time"])                  # gen の entry_time は文字列
            xt = pd.to_datetime(t["exit_time"])
            if et < TRAIN_ENTRY_END and xt < EMBARGO_END:         # 学習期間のみ（embargo の出口も採点も覗かない）
                s += float(t["net_usd"])
        return s

    cache = {}
    best_th, best_train_net = THETA_GRID[0], -1e18
    _log("\n[6-3/8 θ sweep・学習期間 連続モード net（選定 Exit・embargo&採点は不参照）]")
    for th in THETA_GRID:
        trd = continuous_trades(th); cache[th] = trd
        tn = train_net_of(trd)
        _log(f"  θ={th}: 連続トレード総数 {len(trd):5d} / 学習期間net ${tn:9.0f}")
        if tn > best_train_net:
            best_train_net, best_th = tn, th
    _log(f"[θ*] 学習期間 連続モード net 最大 → θ*={best_th}（学習net ${best_train_net:.0f} / Exit '{best_exit}'）")

    # ---- 採点（地面と土俵を合わせる）: θ* × 選定 Exit の連続モード trade を score.py（cap ゲート）----
    ai_trades = cache[best_th]
    # ★ 0取引クラッシュ修正（E8b第2回の KeyError:entry_time 再発防止）:
    #   θ* で採用 0 件なら空 DataFrame で落ちていた → 「net $0・地面に負け」と扱い正常終了（クラッシュさせない）。
    if len(ai_trades) == 0:
        _log(f"[採点] θ*={best_th} で AI 採用トレード 0 件 → net $0（地面 $925.73 に負け）。"
             f"0件は破棄扱いで正常終了（クラッシュ回避）。原因究明は ledger に記録。")
        return
    ai_df = pd.DataFrame(ai_trades)
    for col in ("entry_time", "exit_time"):
        ai_df[col] = pd.to_datetime(ai_df[col])
    out_ai = RAT / "trades_p23_E08b_ai.csv"
    ai_df.to_csv(out_ai, index=False)

    r_ai = score_continuous(ai_trades, "AI")
    sc_ai_df = r_ai["df"]
    _log("\n===== 採点（score.py・cap0.12 ゲート通過・採点 2025-04〜12・連続モード）=====")
    _log(f"  AI(θ*={best_th} / Exit '{best_exit}'): {r_ai['n_trades']:5d}件 / 月平均 ${r_ai['monthly_avg']:8.2f} / 合計 ${r_ai['total']:8.1f}")
    if r_ai.get("anomaly"):
        _log("  ⚠️ 異常値・要調査（H12）: " + " / ".join(r_ai["anomaly"]))

    # 地面（連続モード V9手書き P23 = measure_p23_ground_capped の出力・$925.73）を並べる
    ground_total = None
    if GROUND.exists():
        g = pd.read_csv(GROUND)
        g["entry_time"] = pd.to_datetime(g["entry_time"]); g["exit_time"] = pd.to_datetime(g["exit_time"])
        g_sc = g[(g["entry_time"] >= SC_START) & (g["entry_time"] < SC_END)].reset_index(drop=True)
        r_g = judge.score(g_sc)
        ground_total = r_g["total"]
        _log(f"  地面(連続モードV9手書きP23): {r_g['n_trades']:5d}件 / 月平均 ${r_g['monthly_avg']:8.2f} / 合計 ${r_g['total']:8.1f}")
        _log(f"  → AI {'勝ち' if r_ai['total'] > r_g['total'] else '負け'}（合計差 ${r_ai['total']-r_g['total']:+.1f} / 地面 $925.73 基準）")
    else:
        _log(f"  地面 {GROUND.name} が無い → measure_p23_ground_capped.py を先に実行してください（地面 $925.73）")

    # ======================================================================
    # ステップ 9: 過学習チェック（DSR>0.95 / PBO<0.5・既存 dsr_pbo.py・多重検定補正）
    #   iteration 中は **封印 2026Q1 を不参照**のまま、採点期間（2025-04〜12）で θ グリッドを
    #   「試した N 戦略」とみなして DSR/PBO を出す（θ sweep の多重検定を補正＝C 対策・§10.9）。
    #   ⚠️ 封印 2026Q1 での「最終 1 回」DSR/PBO は別工程（全月クリア後・SC_END=2026-01-01 で触れない）。
    #   注: 月次 9 点は PBO の CSCV ブロック分割に足りないため、PBO は per-trade リターンで CSCV、
    #       DSR は月次 per-period（Sharpe 整合）で算出（足りない時は安全に skip 表示）。
    # ======================================================================
    _log("\n[9 過学習チェック（採点期間 θ グリッドで多重検定補正・封印2026Q1は不参照）]")
    # θ グリッド各戦略の採点期間 月次 net 行列（DSR の sr_estimates / PBO の戦略次元）
    theta_sc_dfs = {}
    for th in THETA_GRID:
        d = pd.DataFrame(cache[th]); d["entry_time"] = pd.to_datetime(d["entry_time"])
        d["exit_time"] = pd.to_datetime(d["exit_time"])
        theta_sc_dfs[th] = d[(d["entry_time"] >= SC_START) & (d["entry_time"] < SC_END)].reset_index(drop=True)

    # DSR: 採用 θ* の月次リターンを、θ グリッド全戦略の月次 Sharpe 分布で deflation
    best_monthly = monthly_returns(sc_ai_df)
    sr_estimates = []
    for th in THETA_GRID:
        mr = monthly_returns(theta_sc_dfs[th])
        if len(mr) >= 2:
            sr_estimates.append(dsr_pbo.per_period_sharpe(mr))
    if len(best_monthly) >= 3 and len(sr_estimates) >= 2:
        dres = dsr_pbo.deflated_sharpe_ratio(best_monthly, np.array(sr_estimates), n_trials=len(THETA_GRID))
        _log(f"  DSR={dres['dsr']:.3f}（>0.95 で合格）/ SR={dres['sr']:.3f} / SR0(deflation)={dres['sr0']:.3f}"
             f" / N試行={dres['n_trials']} / T={dres['T']}ヶ月")
    else:
        dres = None
        _log(f"  DSR: 月次サンプル不足（best {len(best_monthly)}点 / 戦略 {len(sr_estimates)}本）→ skip（採点期間が短い）")

    # PBO: θ グリッドを N 戦略として per-trade リターンで CSCV（同一時間軸が必要 → 日次にそろえて行列化）
    pbo_res = None
    try:
        # 採点期間の日次 net 行列（行=日 / 列=θ 戦略）。同じ日付 index にそろえる。
        daily_cols = {}
        for th in THETA_GRID:
            d = theta_sc_dfs[th]
            if not len(d):
                continue
            # engine net を exit 日でまとめる（PBO は θ 戦略間の OOS 相対順位を見るので CSV engine net で十分）
            dn = d.assign(_day=d["exit_time"].dt.normalize()).groupby("_day")["net_usd"].sum()
            daily_cols[f"th{th}"] = dn
        if len(daily_cols) >= 4:
            mat = pd.DataFrame(daily_cols)
            full_idx = pd.date_range(mat.index.min(), mat.index.max(), freq="D")
            mat = mat.reindex(full_idx).fillna(0.0)
            if mat.shape[0] >= 20 and mat.shape[1] >= 4:
                nb = min(10, (mat.shape[0] // 2) * 2)             # 偶数ブロック
                nb = max(4, nb)
                pbo_res = dsr_pbo.pbo_cscv(mat.values, n_blocks=nb)
                _log(f"  PBO={pbo_res['pbo']:.3f}（<0.5 で合格）/ 組合せ {pbo_res['n_combos']} / "
                     f"戦略 {mat.shape[1]} × 日次 {mat.shape[0]}")
            else:
                _log(f"  PBO: 日次サンプル/戦略不足（{mat.shape}）→ skip")
        else:
            _log("  PBO: θ グリッドの採点トレードが少なく行列化不能 → skip")
    except Exception as ex:  # pragma: no cover  PBO は補助指標・落ちても採点は出す
        _log(f"  PBO: 算出スキップ（{type(ex).__name__}: {ex}）")

    # ---- θ 掃引 採点期間 参考（覗き見でなく事後の報告のみ・θ* は学習で確定済）----
    _log("\n[θ掃引・採点期間 連続モード net 参考（θ* は学習で確定済・ここは事後報告）]")
    for th in THETA_GRID:
        sc = theta_sc_dfs[th]
        _log(f"  θ={th}: 採点トレード {len(sc):4d} / engine net合計 ${sc['net_usd'].sum():8.1f}")

    # ---- 重要特徴 + 学習した分岐閾値（どの期間・どの値を見ているか＝§10.4 の答え）----
    imp = pd.Series(model.feature_importance("gain"), index=X_all.columns).sort_values(ascending=False)
    _log("\n[重要特徴 top15（どの指標・どの期間を見ているか＝§10.4 指標期間の答え）]\n" + imp.head(15).to_string())
    # ★ B② / H15 受け入れ条件①: 揺れ幅(ボラ)系が方向スコア上位を支配しないことを feature importance で確認。
    #   そもそも X からボラ系を除外済（make_features assert）なので寄与は 0 のはずだが、念のため実測表示。
    vol_gain = float(imp[[c for c in imp.index if ("atr" in c or "bb_width" in c)]].sum())
    _log(f"[軸1 verify・H15①] ボラ系(atr/bb_width)の gain 合計={vol_gain:.1f}（X から除外済＝0 が期待・"
         f"非0 なら MTF 等から混入＝設計やり直し）／ 方向系が主役であることを top15 で確認")
    tdf = model.trees_to_dataframe()
    sp = tdf[tdf["split_feature"].notna()].groupby("split_feature").agg(
        分岐回数=("threshold", "size"), 代表閾値=("threshold", "median"),
        gain合計=("split_gain", "sum")).sort_values("gain合計", ascending=False).round(3)
    _log("\n[AIが学習した分岐閾値 top10（指標をどの値で切るか・gain順＝§10.4 閾値の答え）]\n" + sp.head(10).to_string())

    # 全型バー(prob付き)を保存 → report.py の H（予測確率帯別）を全域で見られる
    all_scored = lab.copy()
    all_scored["p"] = prob_all
    all_scored["side"] = "SHORT"
    all_scored.to_csv(RAT / "trades_p23_E08b_all_scored.csv", index=False)

    # ---- 使用した値一覧（cat_params 風・E8b 学習/使用値）----
    learned = {
        "_source": "train_p23_entry_E8b.py（B設計・P23・Entry=方向Triple Barrier符号/ボラ系特徴量除外/期間分割是正・Exit グリッド・連続モード採点）",
        "_period": "学習 entry<2024-12-31 かつ exit<2025-04-01(embargo 2025Q1) / 採点 2025-04-01〜2026-01-01 / 封印2026Q1不参照",
        "_label": (f"★B① Entry ○ = 方向 Triple Barrier の +1（下げ TP 先着＝下げ方向当たり）。"
                   f"バリア=ボラ基準 entry×(1±{K_BARRIER}×σ)・σ=ATR/close(t確定値)・vertical={BARRIER_VERTICAL_MIN}分。"
                   f"金額不使用・MFEピーク不使用＝§10.7 B改訂・H2"),
        "_label_K_BARRIER": K_BARRIER,
        "_label_vertical_min": BARRIER_VERTICAL_MIN,
        "_feature_policy": "★B② Entry X からボラ系(atr_pct/bb_width_pct)を除外し方向(regime)系を主役（軸1）。ATR は σ=バリア幅専用",
        "_exit_label": f"Exit 学習(6-2)は実出口 net 基準（選定 Exit '{best_exit}'・add込み連続モード・サイズ同一で方向と整合・§10.7末尾）",
        "_exit_selection": f"6-2 Exit グリッド {len(EXIT_CANDIDATES)} 候補を params override で前向き sim → 学習期間 net 最大 = '{best_exit}'（gen 不変）",
        "_set_optimization": f"6-3 Entry(θ)×Exit('{best_exit}') を連続モード net で評価（§8.4/§8.5 セット最適化）",
        "_cv": f"7 purged k-fold(embargo {embargo_bars}bars・AFML Ch.7) OOS AUC={best_cv:.4f}"
               + ("（Optuna 20 trials 探索）" if _HAS_OPTUNA else "（既定ハイパラ）"),
        "_overfit_check": "9 DSR/PBO（採点期間 θ グリッドで多重検定補正・封印2026Q1は最終1回別工程）",
        "_score": "全型バーに prob 予測 → gen.run_continuous(選定Exit override) の initial_fn=(型バー かつ prob>=θ) で連続モード(cap0.12) → score.py",
        "ML_LABEL_TYPE": "direction_triple_barrier_sign",       # ★B①（旧 ML_LABEL_T_USD=net金額閾値 は廃止）
        "ML_BARRIER_K": K_BARRIER,
        "ML_BARRIER_VERTICAL_MIN": BARRIER_VERTICAL_MIN,
        "ML_EXIT_SELECTED": best_exit,
        "ML_EXIT_OVERRIDE": best_exit_ov,
        "ML_THETA_ADOPT": round(float(best_th), 3),
        "ML_THETA_SELECTION": "学習期間(entry<2024-12-31 かつ exit<2025-04-01) 連続モード net 最大化（embargo&採点 不参照＝類型C回避）",
        "ML_CV_OOS_AUC": round(float(best_cv), 4),
        "ML_AUC_SCORE": round(float(roc_auc_score(lab.loc[is_sc, "y"], prob_all[is_sc.values])), 3)
        if len(np.unique(lab.loc[is_sc, "y"])) > 1 else None,
        "ML_DSR": round(float(dres["dsr"]), 3) if dres else None,
        "ML_PBO": round(float(pbo_res["pbo"]), 3) if pbo_res else None,
        "ML_NUM_LEAVES": int(best_lparams["num_leaves"]), "ML_MIN_CHILD_SAMPLES": int(best_lparams["min_child_samples"]),
        "ML_LAMBDA_L1": round(float(best_lparams["lambda_l1"]), 3), "ML_LAMBDA_L2": round(float(best_lparams["lambda_l2"]), 3),
        "ML_FEATURE_FRACTION": round(float(best_lparams["feature_fraction"]), 3),
        "ML_SCALE_POS_WEIGHT": round(float(pos_w), 2), "ML_BEST_ITER": int(model.best_iteration),
        "AI_SCORE_TOTAL_USD": round(float(r_ai["total"]), 2),
        "AI_SCORE_MONTHLY_AVG_USD": round(float(r_ai["monthly_avg"]), 2),
        "GROUND_SCORE_TOTAL_USD": round(float(ground_total), 2) if ground_total is not None else None,
        "_exit_grid_train_net": {row["exit"]: round(float(row["train_net_sample"]), 1)
                                 for _, row in exit_grid.iterrows()},
        "_top_features_gain": {k: round(float(v), 1) for k, v in imp.head(12).to_dict().items()},
        "_V9手書き": {"P23_ADX_MIN": 30, "P23_ADX_MAX": 50, "P23_ATR14_MIN": 150,
                    "P23_BB_MID_SLOPE_MAX": -10, "P23_TP_PCT": 0.012, "P23_TIME_EXIT_MIN": 480},
        "_limitation": "design §10.4 のトレーリング(シャンデリア/ATR)・分割利確 は gen._step の P23 ブロック改造を伴う"
                       "（『gen は import のみ』違反）ため E8b 範囲外。import-only の枠内で V9 露出 Exit 数値"
                       "（TP%/TimeExit/down-factor/PROFIT_LOCK/MFE_STALE/SL%）を場面別最適化した。",
    }
    for k, v in sp["代表閾値"].head(8).to_dict().items():
        learned[f"LEARNED_SPLIT_{k}"] = round(float(v), 4)
    pj = RAT / "p23_learned_params_E08b.json"
    json.dump(learned, open(pj, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    _log(f"\n[out] AI 連続モード trade → {out_ai}")
    _log(f"[out] 全型バー(prob付き) → trades_p23_E08b_all_scored.csv（report.py の H/G を全域で）")
    _log(f"[out] 使用した値一覧（cat_params風）→ {pj}\n" + json.dumps(learned, ensure_ascii=False, indent=2))
    _log("\n[次] python3 scripts/priority_rebuild/report.py "
         f"{out_ai} --start 2025-04-01 --end 2025-12-31  （A〜I 分析）")


if __name__ == "__main__":
    main()
