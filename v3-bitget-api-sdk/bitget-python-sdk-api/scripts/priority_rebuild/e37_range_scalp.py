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

★v7（--v7・acceptance「E37 v7 型別検出器（帯の合併）」承認 2026-07-04・既定 OFF=v5 恒等）:
  v6r の確定＝混合母数そのものが型内ランキングを半減させる（二値 vs 回帰の対照で「教師の金額非整合」
  仮説を棄却＝be0.498→0.508 不変。同頻度対照＝v5 単独母数 be1.01@3.7/日 vs 混合 be0.51・ledger ARC20）。
  ① 型別検出器＝fit と θ 選定の単位をイベント型（EVENT_TYPES 5型）に分ける（_fit_detector_per_type）。
     教師はエンジン同一執行（union で1回生成）を型マスクでサブセット化＝執行モデルは型非依存なので
     型ごとの独立生成と同値（v5 の evt_mr 単独母数 fit の再現構造・教師は二値=v5 と同一の物差し）。
  ② 型別 θ＝型ごとに be≥BE_FLOOR を満たす学習窓 OOF 分位のうちイベント/日最大（_select_theta_per_type）。
     帯なしの型は不使用（be ゲートの自然排除・新閾値なし）。全型で帯なしなら SystemExit＝停止ガード維持。
  ③ 帯の合併＝be≥1.0 に届いた型のいずれかで自型 θ を超えたバーを執行（OR・_detector_gate_v7）。
  ④ TP-viability（v6r 承認済み部品）は同梱を継続。執行エンジン・出口・サイズは v5 不変。

★v8（--v8・acceptance「E37 v8 選定計器の是正」承認 2026-07-04・既定 OFF=v7 恒等・フェーズ0＝計器是正・新レバーなし）:
  実装総点検（2026-07-04）で特定した「選定計器の歪み」3点の是正＝θ・帯を選ぶ物差しを実行実態に一致させる:
  ① 型の相互排他化（_gen_events_v8_exclusive）＝5型の入れ子（evt_mr⊂evt_mr_sh 等）を特異度順で1バー1型に割当
     （型別教師の重複と「帯の合併で最も緩い帯が支配」を根絶・union は不変＝候補集合を変えない）。
  ② 執行後フロンティア（_frontier_exec_consistent）＝θ選定の件数/日・be を、実行同一規則（サイドごと単一スロット・
     pending 占有・TTL タッチ約定・不約定は建てない）を適用した執行後の系列で測る（v7 までの独立カウント＝
     学習1.82イベント/日が実行0.41件/日に消える過大見積りの是正・根拠 arxiv 2407.16527=100%fill 仮定は利益850%過大）。
  ③ 型×side 別の θ・be≥1.0 判定（_select_theta_per_type_side）＝side プールが片側赤字（採点窓 B節 LONG−$3 vs
     SHORT−$53）を覆い隠すのを止める。帯なしの型×side は執行しない・全型×side 帯なしなら SystemExit（停止ガード）。
  検出器 fit（型別・side は特徴列）・特徴・執行・出口・サイズは v7 不変＝新レバーなし・新数値なし。

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
import structure_features as sf                # noqa: E402  fractal ピボット（j+2 確定・leak-safe・v10 ゾーン構築＝e35_box が regime パスを通す）
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

# ── v10 ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP・acceptance 2026-07-04・全て a-priori/既存定数＝スイープしない）──
V10_LOOKBACK = 288           # ゾーン構築の窓 = 288本 = 24h（a-priori の丸い値）
V10_ZONE_TOL = 0.0010        # ピボット束ね幅 0.10%（a-priori の丸い値）
V10_TOUCH_MIN = 3            # 機能実績＝タッチ3回以上（range_scalping_kb §2 の検証標準）
V10_SL_BUF = 0.0005          # SL = ゾーン上端×(1+0.05%)（ゾーンのすぐ外＝KB §4・a-priori）
V10_MIN_RANGE_W = 2 * SCALP_FLOOR   # レンジ最低幅（幾何由来: TP幅≥SL幅と手数料床の両立に必要な最小幅）

# ── v11 視認校正レンジ計器の組み込み（acceptance 2026-07-05・ゾーン4値=まこさん視認校正済み v17 計器と同一・スイープしない）──
V11_ZONE_LOOKBACK = 168      # 1h ゾーン構築の窓（168h=7日・build_range_gate_dashboard.py v17 と同一）
V11_ZONE_TOL = 0.003         # ゾーン束ね幅 0.3%（v17 と同一）
V11_ZONE_TOUCH = 2           # 機能実績＝束ねたスイング数≥2（v17 と同一）
V11_ZONE_MIN_W = 0.004       # 上下ゾーン間の最低幅 0.4%（v17 と同一）
V11_MAX_ADDS = 2             # 同時最大 lot 数（2×UNIT=0.048 BTC ≤ CAP 0.12・H1・V9 MAX_ADDS=5 の縮小版）
V11_SL_BUF = V10_SL_BUF      # SL = ゾーン上端×(1+0.05%)（v10 と同一・ゾーンのすぐ外）
FREQ_FLOOR_EVT_DAY = 5.0     # θ選定の頻度床（学習窓ゲート通過イベント/日・スロット占有の目減り込みで採点窓 件数/日≥3 を狙う）
THETA_QQ = (0.50, 0.60, 0.70, 0.80, 0.90, 0.95)   # θ 候補分位（学習窓 OOF から選定・採点窓不参照）

# ── E37 v6 パラメータ（イベント母数拡大＋θ規則反転・--v6 で ON・既定 OFF=v5 恒等・出所は各行）──
BE_FLOOR = 1.0               # v6 θ選定の be 床＝損益分岐の定義値（be=平均gross÷往復コスト の分岐点・数値探索でない）
SHALLOW_Z = 0.5              # 浅い行き過ぎ／順張り押し目・戻り売りの dev_z（教科書の半σ・a-priori）
BB_K = 2.0                   # EV_BB: BB(20,2σ) バンドタッチ（教科書標準・sma/std は SMA_N=20 と同窓）
BREAK_N = 20                 # EV_BREAK_REV: donchian 窓（教科書標準・当該足除外＝H2）
BREAK_LOOKBACK = 3           # EV_BREAK_REV: ブレイクから3本以内の反転バー
EVENT_TYPES = ("evt_mr", "evt_mr_sh", "evt_bb", "evt_brk", "evt_pull")   # 5型 one-hot（検出器の特徴に渡す＝木が判定）

# ── E37 v6r（iter2＝ランキングの金額整合＋TP-viability・--v6r で ON・既定 OFF=v5 恒等・acceptance 2026-07-03）──
# RANK_BE_REGRESSION: 検出器の教師を「net>0 の二値」から「per-event の be＝net/fee（無次元 H6）」の回帰へ。
#   v6 の確定＝二値教師は金額を見ず薄利勝ち玉が確率上位を占拠し be≥1.0 帯が消失（ledger ARC19）。
#   回帰（大きさ予測）と分類（向き）の役割分担は業界整合（arxiv 2407.18334）。目的関数=L2（ライブラリ既定・数値探索なし）。
RANK_BE_REGRESSION = "net_over_fee_l2"   # 教師目標の宣言（DESIGN_CONTRACT トークン・値は識別子であり閾値でない）

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


# ══ ②v6r TP-viability entry ゲート（毒の機械除去・教師とエンジンの両方＝同一執行・acceptance 2026-07-03）══
def _tp_viable(df: pd.DataFrame) -> pd.DataFrame:
    """entry 時点（当該バーの close/sma/std のみ＝t 因果 H2）で、指値価格から見た TP 目標（SMA∓TP_OVERSHOOT×σ）の
    距離が SCALP_FLOOR（既存定数・新数値なし）未満＝届いても手数料負けが確定している候補は建てない。
    probe 実測: 該当 6.5イベント/日・be −2.43（毒）。viable_s/viable_l 列を付けるだけ（適用は呼び出し側）。"""
    c = df["close"]; sma = df["sma"]; sd = df["std"]
    lim_s = c * (1 + ENTRY_OFFSET)               # SHORT 指値
    lim_l = c * (1 - ENTRY_OFFSET)               # LONG 指値
    tgt_s = sma - TP_OVERSHOOT * sd              # SHORT TP 目標
    tgt_l = sma + TP_OVERSHOOT * sd              # LONG TP 目標
    df["viable_s"] = (tgt_s <= lim_s * (1.0 - SCALP_FLOOR)).fillna(False)
    df["viable_l"] = (tgt_l >= lim_l * (1.0 + SCALP_FLOOR)).fillna(False)
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
        xp = None; taker = False; exit_j = None
        for j in range(fill + 1, fill + 1 + T_MAX):
            tgt = (sma[j] - TP_OVERSHOOT * sd[j]) if side == -1 else (sma[j] + TP_OVERSHOOT * sd[j])
            if side == -1:
                if h[j] >= slp: xp = max(slp, o[j]); exit_j = j; break          # SL 優先・gap 反映（保守）
                if np.isfinite(tgt) and tgt <= ep * (1.0 - SCALP_FLOOR) and l[j] <= tgt: xp = tgt; exit_j = j; break
            else:
                if l[j] <= slp: xp = min(slp, o[j]); exit_j = j; break
                if np.isfinite(tgt) and tgt >= ep * (1.0 + SCALP_FLOOR) and h[j] >= tgt: xp = tgt; exit_j = j; break
        if xp is None:
            xp = c[fill + T_MAX]; taker = True; exit_j = fill + T_MAX
        fee = pos * ee.MAKER_FEE + UNIT * xp * ((ee.TAKER_FEE + ee.SLIPPAGE) if taker else ee.MAKER_FEE)
        gross = (ep - xp) * UNIT if side == -1 else (xp - ep) * UNIT
        rows.append((ts[i], side, gross, fee, gross - fee, i, fill, exit_j))
    t = pd.DataFrame(rows, columns=["ts", "side", "gross", "fee", "net", "entry_i", "fill_i", "exit_i"])
    # entry_i/fill_i/exit_i は v8 の執行後フロンティア（スロット整合）専用の付加列＝v5〜v7 は不使用（挙動不変）
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


def _select_theta_per_type(cand: list) -> dict | None:
    """v7 型別 θ選定（acceptance 2026-07-04）＝be≥BE_FLOOR（損益分岐の定義値）を満たす学習窓 OOF 分位のうち
    イベント/日最大（v6 の反転規則を型別に適用）。満たす帯が無い型は None＝その型は不使用
    （帯なし型を捨てるのは be ゲートの自然排除＝新しい固定閾値を足さない）。"""
    feas = [c_ for c_ in cand if np.isfinite(c_["be"]) and c_["be"] >= BE_FLOOR]
    return max(feas, key=lambda c_: c_["events_per_day"]) if feas else None


def _fit_detector_per_type(teach: pd.DataFrame, feat: pd.DataFrame, feat_cols: list,
                           days_train: float, df: pd.DataFrame) -> dict:
    """v7＝検出器を型別に独立 fit し型別 θ を選定（帯なし型は不使用・全型帯なしなら SystemExit＝停止ガード）。
    混合母数が型内ランキングを半減させる（ledger ARC20）への直接対策。
    教師＝エンジン同一執行（_teacher_labels・union で1回生成）を型マスク（そのバーにその型が立つ）で
    サブセット化＝執行モデルは型非依存なので型ごとの独立生成と同値（v5 の単独母数 fit の再現構造）。
    教師の物差し＝二値 net>0（v5 の be1.01 実証と同一・v6r 対照で回帰と同値と確認済み）。
    型ごとの教師量・正例率・フロンティア・選定 θ を全部ログ（lever-bites）。"""
    import lightgbm as lgb
    t_ns = pd.Index(pd.DatetimeIndex(teach.ts).asi8)
    dets = {}
    frontier_log = {}
    for name in EVENT_TYPES:
        evt_ns = set(pd.DatetimeIndex(df.loc[df[name] > 0.5, "ts"]).asi8)
        sub = teach[t_ns.isin(evt_ns)]
        if len(sub) == 0:
            print(f"  [v7 {name}] 教師 0 件＝型不使用")
            frontier_log[name] = {"teacher": 0, "picked": None}
            continue
        d = (sub.merge(feat.rename(columns={"timestamp": "ts"}), on="ts", how="inner")
                .sort_values("ts").reset_index(drop=True))
        print(f"  [v7 {name}] 教師 {len(sub)} 件（特徴結合 {len(d)}）/ 勝ちラベル率 {d.y.mean()*100:.1f}%")
        assert int(pd.DatetimeIndex(d.ts).asi8.max()) < int(pd.Timestamp(TRAIN_END).value), \
            "TRAIN_END assert: 教師に学習窓外の行が混入（H8 違反）"
        X = d[feat_cols].astype(np.float32).assign(side=d["side"].astype(np.float32))
        y = d["y"].to_numpy()
        tt = pd.DatetimeIndex(d.ts)
        oof = np.full(len(d), np.nan)
        try:
            for tr, te in purged_fold(tt):
                if tr.sum() == 0 or te.sum() == 0:
                    continue
                mdl = lgb.LGBMClassifier(**_LGB_PARAMS)
                mdl.fit(X[tr], y[tr])
                oof[te] = mdl.predict_proba(X[te])[:, 1]
        except Exception as e:   # 教師が薄く fit 不能な型は不使用（数値閾値でなく実行可能性）
            print(f"  [v7 {name}] fit 不能（{e}）＝型不使用")
            frontier_log[name] = {"teacher": int(len(sub)), "picked": None}
            continue
        ok = np.isfinite(oof)
        if not ok.any():
            print(f"  [v7 {name}] OOF 0 件＝型不使用")
            frontier_log[name] = {"teacher": int(len(sub)), "picked": None}
            continue
        cand = []
        for qq in THETA_QQ:
            thr = float(np.quantile(oof[ok], qq))
            g = d[ok][oof[ok] >= thr]
            if len(g) == 0:
                continue
            cand.append({"quantile": qq, "theta": round(thr, 4),
                         "events_per_day": round(len(g) / days_train, 2),
                         "avg_gross": round(float(g.gross.mean()), 4),
                         "avg_fee": round(float(g.fee.mean()), 4),
                         "be": round(float(g.gross.mean() / g.fee.mean()), 3) if g.fee.mean() else float("nan"),
                         "win_rate": round(float((g.net > 0).mean()), 3)})
        pick = _select_theta_per_type(cand)
        print(f"  [v7 {name}] θフロンティア（学習窓 OOF）: {json.dumps(cand, ensure_ascii=False)}")
        frontier_log[name] = {"teacher": int(len(sub)), "win_label_rate": round(float(d.y.mean()), 3),
                              "frontier": cand, "picked": pick}
        if pick is None:
            print(f"  [v7 {name}] be≥{BE_FLOOR} 帯なし＝型不使用")
            continue
        # 参考ログ: この型の θ で帯の下に落とす勝ちイベント（学習窓 OOF・入口選別＝保有玉は切らない）
        g_all = d[ok]; p_all = oof[ok]
        cut_w = g_all[(p_all < pick["theta"]) & (g_all.net > 0)]
        print(f"  [v7 {name}] 選定 θ={pick['theta']:.4f}（{pick['events_per_day']}/日・be {pick['be']}）"
              f"／帯の下に落とす勝ちイベント {len(cut_w)} 件 gross ${cut_w.gross.sum():.0f}")
        final = lgb.LGBMClassifier(**_LGB_PARAMS)
        final.fit(X, y)
        fi = pd.Series(final.feature_importances_, index=list(X.columns)).sort_values(ascending=False)
        top10 = list(fi.head(10).index)
        atr_top = [x for x in top10 if "atr" in x.lower() or "realized_vol" in x.lower()]
        print(f"  [v7 {name}] 重要度 top10: {top10}")
        print(f"  [v7 {name} 自己検査 H15] top10 中 ATR/vol 系 {len(atr_top)} 列（{atr_top}）: "
              f"{'✅ 非支配' if len(atr_top) <= 2 else '⚠️ ボラ支配疑い＝報告時に要精査'}")
        dets[name] = {"model": final, "oof_theta": pick["theta"], "picked": pick,
                      "feat_cols": feat_cols, "top10": top10,
                      "oof_map": pd.Series(oof[ok], index=pd.DatetimeIndex(d.ts)[ok])}
    used = list(dets.keys())
    print(f"  [v7 帯の合併] be≥{BE_FLOOR} 帯が立った型: {used if used else 'なし'}"
          + (f"（合算 {sum(v['picked']['events_per_day'] for v in dets.values()):.2f} イベント/日・学習窓 OOF）" if dets else ""))
    if not dets:
        print(f"  [v7] ⛔ 全型で be≥{BE_FLOOR} 帯なし＝執行せず停止（赤字帯を選ばない・停止ガード・採点温存）")
        raise SystemExit(1)
    return {"dets": dets, "frontier_log": frontier_log}


def _detector_gate_v7(bundle: dict, feat: pd.DataFrame, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """v7 帯の合併（OR）＝各バーで「be≥1.0 帯が立った型」のうち、そのバーに立っている型のいずれかが
    自型の θ を超えたら通過。学習窓バー＝型別 OOF（in-sample 自己採点を塞ぐ・v5 恒久対策と同一）／
    TRAIN_END 以降＝型別最終モデルで推論（clean OOS）。戻り値＝(gate_ok, 通過型ラベル via)。"""
    n = len(df)
    ok = np.zeros(n, dtype=bool)
    via = np.array([""] * n, dtype=object)
    ts_index = pd.DatetimeIndex(df["ts"])
    is_train = np.asarray(ts_index < pd.Timestamp(TRAIN_END))
    f = feat.set_index("timestamp")
    present = np.asarray(ts_index.isin(f.index))
    cand_any = (df["short_cand"] | df["long_cand"]).to_numpy(bool)
    for name, det in bundle["dets"].items():
        m_evt = (df[name].to_numpy(np.float32) > 0.5) & cand_any
        # ── 学習窓: 型別 OOF ゲート ──
        m_tr = m_evt & is_train
        if m_tr.any():
            p_tr = det["oof_map"].reindex(ts_index[m_tr]).to_numpy()
            hit = np.where(np.isfinite(p_tr), p_tr >= det["oof_theta"], False)
            for j in np.where(m_tr)[0][hit]:
                ok[j] = True
                via[j] = f"{via[j]}+{name}" if via[j] else name
        # ── TRAIN_END 以降: 型別最終モデル（side ごと・特徴欠落バーは不通過＝保守）──
        for side_val, col in ((-1.0, "short_cand"), (1.0, "long_cand")):
            m = m_evt & df[col].to_numpy(bool) & present & ~is_train
            if not m.any():
                continue
            X = f.loc[ts_index[m], det["feat_cols"]].astype(np.float32).assign(side=np.float32(side_val))
            p = det["model"].predict_proba(X)[:, 1]
            for j in np.where(m)[0][p >= det["oof_theta"]]:
                ok[j] = True
                via[j] = f"{via[j]}+{name}" if via[j] else name
    return ok, via


# ══ ②v8 選定計器の是正（acceptance 2026-07-04・フェーズ0＝母数一致＋side別be＋型相互排他・新レバーなし）══
def _gen_events_v8_exclusive(df: pd.DataFrame) -> pd.DataFrame:
    """v8①: 5型の入れ子を相互排他化＝同一バーは特異度順（条件が多い型を優先・a-priori・新数値なし）で1型に割当。
    v7 実装総点検（2026-07-04）＝型が入れ子（evt_mr⊂evt_mr_sh 等）だと型別教師が重複し、帯の合併では
    最も緩い帯が通過を支配する。union（short_cand/long_cand）は不変＝執行候補集合は変えない（割当の一意化のみ）。"""
    pri = ("evt_pull", "evt_brk", "evt_bb", "evt_mr", "evt_mr_sh")   # 特異度順（MACD条件付き→ブレイク後→バンド→深→浅）
    assert set(pri) == set(EVENT_TYPES), "v8 優先順と EVENT_TYPES の不一致"
    taken = np.zeros(len(df), dtype=bool)
    before = {n_: int(df[n_].sum()) for n_ in EVENT_TYPES}
    for name in pri:
        m = df[name].to_numpy(np.float32) > 0.5
        keep = m & ~taken
        df[name] = keep.astype(np.float32)
        taken |= keep
    tot = np.zeros(len(df), dtype=int)
    for n_ in EVENT_TYPES:
        tot += (df[n_].to_numpy(np.float32) > 0.5).astype(int)
    assert int((tot > 1).sum()) == 0, "v8 相互排他 assert: 型マスクに重複が残存"
    after = {n_: int(df[n_].sum()) for n_ in EVENT_TYPES}
    print(f"  [v8 相互排他] 型割当 before={json.dumps(before)} → after={json.dumps(after)}（ペア重複0 assert PASS）")
    return df


def _frontier_exec_consistent(sub: pd.DataFrame, oof: np.ndarray, days_train: float) -> list:
    """v8②: θ 候補ごとに、実行同一規則（サイドごと単一スロット＝busy 中はスキップ・教師は TTL タッチ約定済み
    ＝不約定は建てない を反映済み）を学習窓イベント列へ逐次適用した「執行後の件数/日・be」でフロンティアを作る。
    v7 まで＝全候補を同時執行可能とみなす独立カウント（学習1.82イベント/日→実行0.41件/日の過大見積りの正体）。
    近似の限界＝スロット競合は同一 型×side 内のみ（型横断の競合は本走の乖離ログで観測＝acceptance F⑤）。"""
    order = np.argsort(sub["entry_i"].to_numpy())
    e_i = sub["entry_i"].to_numpy()[order]
    x_i = sub["exit_i"].to_numpy()[order]
    gross = sub["gross"].to_numpy(float)[order]
    fee = sub["fee"].to_numpy(float)[order]
    net = sub["net"].to_numpy(float)[order]
    p = oof[order]
    cand = []
    for qq in THETA_QQ:
        thr = float(np.quantile(oof, qq))
        busy_until = -1
        g_s = 0.0; f_s = 0.0; w = 0
        n_exec = 0
        for k in range(len(e_i)):
            if p[k] < thr or e_i[k] <= busy_until:
                continue
            busy_until = int(x_i[k])
            g_s += gross[k]; f_s += fee[k]; n_exec += 1
            if net[k] > 0:
                w += 1
        if n_exec == 0:
            continue
        cand.append({"quantile": qq, "theta": round(thr, 4),
                     "events_per_day": round(n_exec / days_train, 2),   # ＝執行後の件数/日（スロット整合）
                     "avg_gross": round(g_s / n_exec, 4), "avg_fee": round(f_s / n_exec, 4),
                     "be": round((g_s / n_exec) / (f_s / n_exec), 3) if f_s else float("nan"),
                     "win_rate": round(w / n_exec, 3), "n_exec": int(n_exec)})
    return cand


def _select_theta_per_type_side(cand: list) -> dict | None:
    """v8③: 型×side 別の θ 選定＝be≥BE_FLOOR（損益分岐の定義値）を満たす候補のうち執行後件数/日 最大。
    規則は v7 と同一＝変えたのは母数（型×side の執行後系列）だけ＝新閾値なし。無ければ None＝その型×side は執行しない
    （side プールが片側赤字を覆い隠すのを止める＝採点窓 B節 LONG−$3 vs SHORT−$53 の非対称を計器に見せる）。"""
    feas = [c_ for c_ in cand if np.isfinite(c_["be"]) and c_["be"] >= BE_FLOOR]
    return max(feas, key=lambda c_: c_["events_per_day"]) if feas else None


def _fit_detector_per_type_v8(teach: pd.DataFrame, feat: pd.DataFrame, feat_cols: list,
                              days_train: float, df: pd.DataFrame) -> dict:
    """v8＝型別 fit（v7 同一・side は特徴列）＋ 選定だけを（執行後フロンティア × 型×side 別）に是正。
    fit の side 分割はフェーズ1（Entry/Exit セット共同選定）で扱う＝本フェーズは物差しの是正のみ（acceptance やること3）。"""
    import lightgbm as lgb
    t_ns = pd.Index(pd.DatetimeIndex(teach.ts).asi8)
    dets = {}
    frontier_log = {}
    for name in EVENT_TYPES:
        evt_ns = set(pd.DatetimeIndex(df.loc[df[name] > 0.5, "ts"]).asi8)
        sub = teach[t_ns.isin(evt_ns)]
        if len(sub) == 0:
            print(f"  [v8 {name}] 教師 0 件＝型不使用")
            frontier_log[name] = {"teacher": 0}
            continue
        d = (sub.merge(feat.rename(columns={"timestamp": "ts"}), on="ts", how="inner")
                .sort_values("ts").reset_index(drop=True))
        print(f"  [v8 {name}] 教師 {len(sub)} 件（特徴結合 {len(d)}）/ 勝ちラベル率 {d.y.mean()*100:.1f}%")
        assert int(pd.DatetimeIndex(d.ts).asi8.max()) < int(pd.Timestamp(TRAIN_END).value), \
            "TRAIN_END assert: 教師に学習窓外の行が混入（H8 違反）"
        X = d[feat_cols].astype(np.float32).assign(side=d["side"].astype(np.float32))
        y = d["y"].to_numpy()
        tt = pd.DatetimeIndex(d.ts)
        oof = np.full(len(d), np.nan)
        try:
            for tr, te in purged_fold(tt):
                if tr.sum() == 0 or te.sum() == 0:
                    continue
                mdl = lgb.LGBMClassifier(**_LGB_PARAMS)
                mdl.fit(X[tr], y[tr])
                oof[te] = mdl.predict_proba(X[te])[:, 1]
        except Exception as e:   # 教師が薄く fit 不能な型は不使用（数値閾値でなく実行可能性）
            print(f"  [v8 {name}] fit 不能（{e}）＝型不使用")
            frontier_log[name] = {"teacher": int(len(sub))}
            continue
        ok = np.isfinite(oof)
        if not ok.any():
            print(f"  [v8 {name}] OOF 0 件＝型不使用")
            frontier_log[name] = {"teacher": int(len(sub))}
            continue
        theta_side = {}
        picked_side = {}
        log_side = {}
        for sv, s_lbl in ((-1, "SHORT"), (1, "LONG")):
            m_s = ok & (d["side"].to_numpy() == sv)
            if int(m_s.sum()) == 0:
                theta_side[sv] = None; picked_side[sv] = None
                log_side[s_lbl] = {"n": 0, "picked": None}
                continue
            cand = _frontier_exec_consistent(d[m_s], oof[m_s], days_train)
            pick = _select_theta_per_type_side(cand)
            print(f"  [v8 {name} {s_lbl}] 執行後フロンティア（学習窓 OOF・スロット整合）: {json.dumps(cand, ensure_ascii=False)}")
            log_side[s_lbl] = {"n": int(m_s.sum()), "frontier": cand, "picked": pick}
            theta_side[sv] = pick["theta"] if pick else None
            picked_side[sv] = pick
            if pick is None:
                print(f"  [v8 {name} {s_lbl}] be≥{BE_FLOOR} 帯なし＝この型×side は執行しない")
            else:
                print(f"  [v8 {name} {s_lbl}] 選定 θ={pick['theta']:.4f}（執行後 {pick['events_per_day']}/日・be {pick['be']}）")
        frontier_log[name] = {"teacher": int(len(sub)), "win_label_rate": round(float(d.y.mean()), 3), **log_side}
        if theta_side.get(-1) is None and theta_side.get(1) is None:
            continue
        final = lgb.LGBMClassifier(**_LGB_PARAMS)
        final.fit(X, y)
        fi = pd.Series(final.feature_importances_, index=list(X.columns)).sort_values(ascending=False)
        top10 = list(fi.head(10).index)
        atr_top = [x for x in top10 if "atr" in x.lower() or "realized_vol" in x.lower()]
        print(f"  [v8 {name}] 重要度 top10: {top10}")
        print(f"  [v8 {name} 自己検査 H15] top10 中 ATR/vol 系 {len(atr_top)} 列（{atr_top}）: "
              f"{'✅ 非支配' if len(atr_top) <= 2 else '⚠️ ボラ支配疑い＝報告時に要精査'}")
        dets[name] = {"model": final, "theta_side": theta_side, "picked_side": picked_side,
                      "feat_cols": feat_cols, "top10": top10,
                      "oof_map": pd.Series(oof[ok], index=pd.DatetimeIndex(d.ts)[ok])}
    used = [f"{n_}:" + ("S" if v_["theta_side"].get(-1) is not None else "") + ("L" if v_["theta_side"].get(1) is not None else "")
            for n_, v_ in dets.items()]
    print(f"  [v8 帯の合併] be≥{BE_FLOOR} 帯が立った型×side: {used if used else 'なし'}")
    if not dets:
        print(f"  [v8] ⛔ 全型×side で be≥{BE_FLOOR} 帯なし＝執行せず停止（赤字帯を選ばない・停止ガード・採点温存）")
        raise SystemExit(1)
    return {"dets": dets, "frontier_log": frontier_log}


def _detector_gate_v8(bundle: dict, feat: pd.DataFrame, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """v8 帯の合併＝型×side 別 θ（帯なしの型×side は不通過）。学習窓=型別 OOF／TRAIN_END 以降=型別最終モデル
    （v7 と同一の測定系＝in-sample 自己採点を塞ぐ）。相互排他なので1バーは高々1型。"""
    n = len(df)
    ok = np.zeros(n, dtype=bool)
    via = np.array([""] * n, dtype=object)
    ts_index = pd.DatetimeIndex(df["ts"])
    is_train = np.asarray(ts_index < pd.Timestamp(TRAIN_END))
    f = feat.set_index("timestamp")
    present = np.asarray(ts_index.isin(f.index))
    for name, det in bundle["dets"].items():
        m_evt = df[name].to_numpy(np.float32) > 0.5
        for sv, col in ((-1, "short_cand"), (1, "long_cand")):
            th = det["theta_side"].get(sv)
            if th is None:
                continue
            m_side = m_evt & df[col].to_numpy(bool)
            m_tr = m_side & is_train
            if m_tr.any():
                p_tr = det["oof_map"].reindex(ts_index[m_tr]).to_numpy()
                hit = np.where(np.isfinite(p_tr), p_tr >= th, False)
                for j in np.where(m_tr)[0][hit]:
                    ok[j] = True
                    via[j] = name
            m_os = m_side & present & ~is_train
            if m_os.any():
                X = f.loc[ts_index[m_os], det["feat_cols"]].astype(np.float32).assign(side=np.float32(sv))
                p = det["model"].predict_proba(X)[:, 1]
                for j in np.where(m_os)[0][p >= th]:
                    ok[j] = True
                    via[j] = name
    return ok, via


# ══ ②v9 型×side Entry/Exit セット共同選定（acceptance 2026-07-04 フェーズ1・まこさん承認・既定 OFF=v8 恒等）══
def _exit_templates_v9() -> dict:
    """出口テンプレ4案（a-priori・SL=2×ATR は全案共通＝probe 較正済みのため動かさない・acceptance やること1）。
    anchor: move=毎バー SMA∓kσ（現行＝選定が現行を選べるよう候補に残す）／fill=約定バーの SMA∓kσ で固定
    （OU 系平均回帰の最適水準は建値側で確定する固定境界＝arxiv 1602.05858・移動目標はTP逃げの経路＝総点検欠陥5）。
    tp_k: 0.5σ（現行）/1.0σ（教科書の1σ）。t_max: 12本=60分（現行）/6本=30分（既存定数の半分・短保有側）。"""
    return {
        "Xa": {"anchor": "move", "tp_k": TP_OVERSHOOT, "t_max": T_MAX},
        "Xb": {"anchor": "fill", "tp_k": TP_OVERSHOOT, "t_max": T_MAX},
        "Xc": {"anchor": "fill", "tp_k": 1.0, "t_max": T_MAX},
        "Xd": {"anchor": "fill", "tp_k": 1.0, "t_max": T_MAX // 2},
    }


def _entry_variants_v9(df: pd.DataFrame) -> dict:
    """入口バリアント（入れ子4段・a-priori・acceptance やること2）。
    E0=現行／E1=実体過半の反転バー（0.5=過半の定義値・単一足陰陽の強化＝総点検欠陥1）／
    E2=E1∩上位足整合（SHORT=1h MACD≤0・LONG=MACD>0・符号のみ＝E36 shortset1 採用済み機構＝総点検欠陥3の入口版）／
    E3=E2∩クールダウン（同 side の SL 決済から T_MAX 本は新規建てしない＝総点検欠陥7・マスクでなく逐次パス/エンジンで適用）。"""
    rng = (df["high"] - df["low"]).to_numpy(float)
    body = (df["close"] - df["open"]).abs().to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        body_maj = np.where(rng > 0, body / rng > 0.5, False)
    htf_up = df["htf_macd_up"].to_numpy(bool)
    return {
        "E0": {"s": None, "l": None, "cooldown": False},
        "E1": {"s": body_maj, "l": body_maj, "cooldown": False},
        "E2": {"s": body_maj & ~htf_up, "l": body_maj & htf_up, "cooldown": False},
        "E3": {"s": body_maj & ~htf_up, "l": body_maj & htf_up, "cooldown": True},
    }


def _tp_viable_k(df: pd.DataFrame, tp_k: float) -> tuple[np.ndarray, np.ndarray]:
    """TP-viability のテンプレ幅版（_tp_viable と同式・tp_k 引数化）。entry 時点の close/sma/std のみ＝t 因果（H2）。"""
    c = df["close"]; sma = df["sma"]; sd = df["std"]
    lim_s = c * (1 + ENTRY_OFFSET); lim_l = c * (1 - ENTRY_OFFSET)
    tgt_s = sma - tp_k * sd; tgt_l = sma + tp_k * sd
    vs = (tgt_s <= lim_s * (1.0 - SCALP_FLOOR)).fillna(False).to_numpy(bool)
    vl = (tgt_l >= lim_l * (1.0 + SCALP_FLOOR)).fillna(False).to_numpy(bool)
    return vs, vl


def _teacher_labels_v9(df: pd.DataFrame, upto_ns: int, cand_s: np.ndarray, cand_l: np.ndarray,
                       anchor: str, tp_k: float, t_max: int) -> pd.DataFrame:
    """テンプレ別教師（エンジン同一執行・_teacher_labels のテンプレ引数版＝v5〜v8 経路は不変）。
    is_sl 列＝E3 クールダウンの逐次パス用。TP 武装は SCALP_FLOOR（手数料を超える幅のみ・全テンプレ共通）。"""
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    sma = df["sma"].to_numpy(float); sd = df["std"].to_numpy(float)
    atr = df["atr"].to_numpy(float)
    ts = df["ts"].to_numpy()
    n = len(df)
    rows = []; unfilled = 0
    for i in range(25, n - t_max - TTL - 3):
        if ts[i].astype("datetime64[ns]").astype("int64") >= upto_ns:
            break
        side = 0
        if cand_s[i]: side = -1
        elif cand_l[i]: side = 1
        if side == 0 or not (np.isfinite(atr[i]) and np.isfinite(sma[i]) and np.isfinite(sd[i])):
            continue
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
        tgt_fix = None
        if anchor == "fill" and np.isfinite(sma[fill]) and np.isfinite(sd[fill]):
            tgt_fix = (sma[fill] - tp_k * sd[fill]) if side == -1 else (sma[fill] + tp_k * sd[fill])
        xp = None; taker = False; exit_j = None; is_sl = False
        for j in range(fill + 1, fill + 1 + t_max):
            tgt = tgt_fix if anchor == "fill" else ((sma[j] - tp_k * sd[j]) if side == -1 else (sma[j] + tp_k * sd[j]))
            if side == -1:
                if h[j] >= slp: xp = max(slp, o[j]); exit_j = j; is_sl = True; break
                if tgt is not None and np.isfinite(tgt) and tgt <= ep * (1.0 - SCALP_FLOOR) and l[j] <= tgt: xp = tgt; exit_j = j; break
            else:
                if l[j] <= slp: xp = min(slp, o[j]); exit_j = j; is_sl = True; break
                if tgt is not None and np.isfinite(tgt) and tgt >= ep * (1.0 + SCALP_FLOOR) and h[j] >= tgt: xp = tgt; exit_j = j; break
        if xp is None:
            xp = c[fill + t_max]; taker = True; exit_j = fill + t_max
        fee = pos * ee.MAKER_FEE + UNIT * xp * ((ee.TAKER_FEE + ee.SLIPPAGE) if taker else ee.MAKER_FEE)
        gross = (ep - xp) * UNIT if side == -1 else (xp - ep) * UNIT
        rows.append((ts[i], side, gross, fee, gross - fee, i, fill, exit_j, is_sl))
    t = pd.DataFrame(rows, columns=["ts", "side", "gross", "fee", "net", "entry_i", "fill_i", "exit_i", "is_sl"])
    t["y"] = (t["net"] > 0).astype(int)
    print(f"  [教師 v9 {anchor}/tp{tp_k}σ/T{t_max}] 約定 {len(t)} / 不約定 {unfilled}（エンジン同一執行）")
    return t


def _frontier_exec_v9(sub: pd.DataFrame, oof: np.ndarray, days_train: float, cooldown_bars=None) -> list:
    """v9 組フロンティア＝_frontier_exec_consistent と同一規則（単一スロット・執行後系列）＋
    E3 のクールダウン（同 side の SL 決済から cooldown_bars は建てない）を逐次パスに追加。"""
    order = np.argsort(sub["entry_i"].to_numpy())
    e_i = sub["entry_i"].to_numpy()[order]
    x_i = sub["exit_i"].to_numpy()[order]
    is_sl = sub["is_sl"].to_numpy(bool)[order]
    gross = sub["gross"].to_numpy(float)[order]
    fee = sub["fee"].to_numpy(float)[order]
    net = sub["net"].to_numpy(float)[order]
    p = oof[order]
    cand = []
    for qq in THETA_QQ:
        thr = float(np.quantile(oof, qq))
        busy_until = -1; cool_until = -1
        g_s = 0.0; f_s = 0.0; w = 0; n_exec = 0
        for k in range(len(e_i)):
            if p[k] < thr or e_i[k] <= busy_until or e_i[k] <= cool_until:
                continue
            busy_until = int(x_i[k])
            if cooldown_bars is not None and is_sl[k]:
                cool_until = int(x_i[k]) + int(cooldown_bars)
            g_s += gross[k]; f_s += fee[k]; n_exec += 1
            if net[k] > 0:
                w += 1
        if n_exec == 0:
            continue
        cand.append({"quantile": qq, "theta": round(thr, 4),
                     "events_per_day": round(n_exec / days_train, 2),
                     "avg_gross": round(g_s / n_exec, 4), "avg_fee": round(f_s / n_exec, 4),
                     "be": round((g_s / n_exec) / (f_s / n_exec), 3) if f_s else float("nan"),
                     "win_rate": round(w / n_exec, 3), "n_exec": int(n_exec)})
    return cand


def _select_combo_per_type_side(df: pd.DataFrame, feat: pd.DataFrame, feat_cols: list, days_train: float) -> dict:
    """v9 本体＝型×出口テンプレごとに教師再生成＋型別 fit（20 fit）→ 型×side ごとに
    （入口バリアント×出口テンプレ×θ）の執行後フロンティアから be≥BE_FLOOR 内で執行後件数/日最大の組を選定。
    入口バリアントは母数のサブセット＝fit 再利用でフロンティアだけ引き直す（acceptance やること3・4）。"""
    import lightgbm as lgb
    templates = _exit_templates_v9()
    variants = _entry_variants_v9(df)
    short_cand = df["short_cand"].to_numpy(bool); long_cand = df["long_cand"].to_numpy(bool)
    upto = int(pd.Timestamp(TRAIN_END).value)
    fits = {}          # (type, tpl) -> {d, oof, model}
    combo = {}         # (type, sv) -> pick dict or None
    sel_log = {}
    for tpl_name, tpl in templates.items():
        vs, vl = _tp_viable_k(df, tpl["tp_k"])
        cand_s = short_cand & vs
        cand_l = long_cand & vl
        teach = _teacher_labels_v9(df, upto, cand_s, cand_l, tpl["anchor"], tpl["tp_k"], tpl["t_max"])
        t_ns = pd.Index(pd.DatetimeIndex(teach.ts).asi8)
        for name in EVENT_TYPES:
            evt_ns = set(pd.DatetimeIndex(df.loc[df[name] > 0.5, "ts"]).asi8)
            sub = teach[t_ns.isin(evt_ns)]
            if len(sub) < 50:                      # fit 実行可能性（数値閾値でなく学習の成立性・±で帯判定はしない）
                continue
            d = (sub.merge(feat.rename(columns={"timestamp": "ts"}), on="ts", how="inner")
                    .sort_values("ts").reset_index(drop=True))
            if len(d) < 50:
                continue
            assert int(pd.DatetimeIndex(d.ts).asi8.max()) < upto, "TRAIN_END assert（H8）"
            X = d[feat_cols].astype(np.float32).assign(side=d["side"].astype(np.float32))
            y = d["y"].to_numpy()
            oof = np.full(len(d), np.nan)
            try:
                for tr, te in purged_fold(pd.DatetimeIndex(d.ts)):
                    if tr.sum() == 0 or te.sum() == 0:
                        continue
                    mdl = lgb.LGBMClassifier(**_LGB_PARAMS)
                    mdl.fit(X[tr], y[tr])
                    oof[te] = mdl.predict_proba(X[te])[:, 1]
            except Exception as e:
                print(f"  [v9 {name}×{tpl_name}] fit 不能（{e}）")
                continue
            if not np.isfinite(oof).any():
                continue
            final = lgb.LGBMClassifier(**_LGB_PARAMS)
            final.fit(X, y)
            fits[(name, tpl_name)] = {"d": d, "oof": oof, "model": final}
            print(f"  [v9 fit] {name}×{tpl_name}: 教師 {len(d)} 件 / 勝ちラベル率 {d.y.mean()*100:.1f}%")
    for name in EVENT_TYPES:
        for sv, s_lbl in ((-1, "SHORT"), (1, "LONG")):
            best = None
            for tpl_name in templates:
                fx = fits.get((name, tpl_name))
                if fx is None:
                    continue
                d = fx["d"]; oof = fx["oof"]
                ok = np.isfinite(oof) & (d["side"].to_numpy() == sv)
                if not ok.any():
                    continue
                e_idx = d["entry_i"].to_numpy()
                for var_name, var in variants.items():
                    vmask = var["s"] if sv == -1 else var["l"]
                    m = ok if vmask is None else (ok & vmask[e_idx])
                    if int(m.sum()) < 30:
                        continue
                    cool = T_MAX if var["cooldown"] else None
                    for c_ in _frontier_exec_v9(d[m], oof[m], days_train, cooldown_bars=cool):
                        if not (np.isfinite(c_["be"]) and c_["be"] >= BE_FLOOR):
                            continue
                        c_ = {**c_, "tpl": tpl_name, "variant": var_name}
                        if best is None or c_["events_per_day"] > best["events_per_day"]:
                            best = c_
            combo[(name, sv)] = best
            sel_log[f"{name}_{s_lbl}"] = best
            if best:
                print(f"  [v9 選定 {name} {s_lbl}] {best['tpl']}×{best['variant']} θ={best['theta']:.4f}"
                      f"（執行後 {best['events_per_day']}/日・be {best['be']}・勝率 {best['win_rate']}）")
            else:
                print(f"  [v9 選定 {name} {s_lbl}] be≥{BE_FLOOR} の組なし＝執行しない")
    used = [k for k, v in sel_log.items() if v]
    print(f"  [v9 帯の合併] 組が立った型×side: {used if used else 'なし'}")
    if not used:
        print(f"  [v9] ⛔ 全型×side で be≥{BE_FLOOR} の組なし＝執行せず停止（採点温存・停止ガード）")
        raise SystemExit(1)
    return {"fits": fits, "combo": combo, "sel_log": sel_log, "templates": templates, "variants": variants}


def _detector_gate_v9(bundle: dict, feat: pd.DataFrame, df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """v9 ゲート＝型×side の選定組（テンプレ・バリアント・θ）でバーを通す。学習窓=OOF／以降=最終モデル（v8 同一測定系）。
    バリアントの静的条件（実体過半・上位足整合）とテンプレ別 TP-viability はここで反映・クールダウンはエンジンで適用。"""
    n = len(df)
    ok = np.zeros(n, dtype=bool)
    via = np.array([""] * n, dtype=object)
    ts_index = pd.DatetimeIndex(df["ts"])
    is_train = np.asarray(ts_index < pd.Timestamp(TRAIN_END))
    f = feat.set_index("timestamp")
    present = np.asarray(ts_index.isin(f.index))
    variants = bundle["variants"]; templates = bundle["templates"]
    for (name, sv), pick in bundle["combo"].items():
        if pick is None:
            continue
        fx = bundle["fits"][(name, pick["tpl"])]
        tpl = templates[pick["tpl"]]
        vs, vl = _tp_viable_k(df, tpl["tp_k"])
        col = "short_cand" if sv == -1 else "long_cand"
        m_side = (df[name].to_numpy(np.float32) > 0.5) & df[col].to_numpy(bool) & (vs if sv == -1 else vl)
        var = variants[pick["variant"]]
        vmask = var["s"] if sv == -1 else var["l"]
        if vmask is not None:
            m_side = m_side & vmask
        oof_map = pd.Series(fx["oof"], index=pd.DatetimeIndex(fx["d"].ts))
        m_tr = m_side & is_train
        if m_tr.any():
            p_tr = oof_map.reindex(ts_index[m_tr]).to_numpy()
            hit = np.where(np.isfinite(p_tr), p_tr >= pick["theta"], False)
            for j in np.where(m_tr)[0][hit]:
                ok[j] = True; via[j] = name
        m_os = m_side & present & ~is_train
        if m_os.any():
            X = f.loc[ts_index[m_os], feat.columns.drop("timestamp")].astype(np.float32).assign(side=np.float32(sv))
            p = fx["model"].predict_proba(X)[:, 1]
            for j in np.where(m_os)[0][p >= pick["theta"]]:
                ok[j] = True; via[j] = name
    return ok, via


def run_continuous_v9(df, gate_ok: np.ndarray, box_tf, bundle: dict, evt_lbl=None):
    """v9 エンジン＝run_continuous のテンプレ適用版（v5〜v8 経路の run_continuous は不変）。
    ポジションごとに自分の型×side の選定組（TP anchor/幅・TIME 本数・クールダウン）を適用（acceptance やること5）。"""
    n = len(df)
    ts = df["ts"].to_numpy()
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    sma = df["sma"].to_numpy(float); sd = df["std"].to_numpy(float)
    sup = df[e35_box.sup_col(box_tf)].to_numpy(float); res = df[e35_box.res_col(box_tf)].to_numpy(float)
    Wpct = sup + res
    short_cand = df["short_cand"].to_numpy(bool); long_cand = df["long_cand"].to_numpy(bool)
    combo = bundle["combo"]; templates = bundle["templates"]; variants = bundle["variants"]
    evt_names = {name: (df[name].to_numpy(np.float32) > 0.5) for name in EVENT_TYPES}

    trades = []
    slots = {"SHORT": {"pos": None, "pend": None, "cool_until": -1}, "LONG": {"pos": None, "pend": None, "cool_until": -1}}

    def _total_size():
        return sum(s["pos"]["size"] for s in slots.values() if s["pos"] is not None)

    def _bar_type(i):
        for name in EVENT_TYPES:
            if evt_names[name][i]:
                return name
        return None

    for i in range(n):
        for side, st in slots.items():
            sv = -1 if side == "SHORT" else 1
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
                        tpl = pend["tpl"]
                        tp_fix = None
                        if tpl["anchor"] == "fill" and np.isfinite(sma[i]) and np.isfinite(sd[i]):
                            tp_fix = (sma[i] - tpl["tp_k"] * sd[i]) if side == "SHORT" else (sma[i] + tpl["tp_k"] * sd[i])
                        st["pos"] = {"side": side, "avg": pend["limit"], "size": UNIT, "add_count": 1,
                                     "first_idx": i, "last_fill_idx": i,
                                     "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i], "W_entry": Wpct[i],
                                     "max_fav": l[i] if side == "SHORT" else h[i],
                                     "max_adv": h[i] if side == "SHORT" else l[i],
                                     "tpl": tpl, "cooldown": pend["cooldown"], "tp_fix": tp_fix,
                                     "evt": pend.get("evt")}
                    st["pend"] = None
            pos = st["pos"]
            if pos is not None:
                if side == "SHORT":
                    pos["max_fav"] = min(pos["max_fav"], l[i]); pos["max_adv"] = max(pos["max_adv"], h[i])
                else:
                    pos["max_fav"] = max(pos["max_fav"], h[i]); pos["max_adv"] = min(pos["max_adv"], l[i])
            if pos is not None and i > pos["last_fill_idx"]:
                avg = pos["avg"]; a = pos["atr_entry"]; tpl = pos["tpl"]
                sl = avg + K_SL * a if side == "SHORT" else avg - K_SL * a
                if tpl["anchor"] == "fill":
                    tp = pos["tp_fix"]
                else:
                    tp = (sma[i] - tpl["tp_k"] * sd[i]) if side == "SHORT" else (sma[i] + tpl["tp_k"] * sd[i])
                if side == "SHORT" and np.isfinite(sl) and h[i] >= sl:
                    _record(trades, pos, max(sl, o[i]), "SL_FILLED", i, ts); st["pos"] = None
                    if pos["cooldown"]:
                        st["cool_until"] = i + T_MAX
                    continue
                if side == "LONG" and np.isfinite(sl) and l[i] <= sl:
                    _record(trades, pos, min(sl, o[i]), "SL_FILLED", i, ts); st["pos"] = None
                    if pos["cooldown"]:
                        st["cool_until"] = i + T_MAX
                    continue
                if tp is not None and np.isfinite(tp):
                    if side == "SHORT" and tp <= avg * (1.0 - SCALP_FLOOR) and l[i] <= tp:
                        _record(trades, pos, tp, "TP_FILLED", i, ts); st["pos"] = None; continue
                    if side == "LONG" and tp >= avg * (1.0 + SCALP_FLOOR) and h[i] >= tp:
                        _record(trades, pos, tp, "TP_FILLED", i, ts); st["pos"] = None; continue
                if (i - pos["first_idx"]) >= tpl["t_max"]:
                    _record(trades, pos, c[i], "TIME_EXIT", i, ts); st["pos"] = None; continue
            if st["pos"] is None and st["pend"] is None:
                cand = short_cand[i] if side == "SHORT" else long_cand[i]
                if cand and gate_ok[i]:
                    name = _bar_type(i)
                    pick = combo.get((name, sv)) if name else None
                    if pick is None:
                        continue
                    if variants[pick["variant"]]["cooldown"] and i <= st["cool_until"]:
                        continue
                    lim = c[i] * (1.0 + ENTRY_OFFSET) if side == "SHORT" else c[i] * (1.0 - ENTRY_OFFSET)
                    st["pend"] = {"limit": lim, "placed_idx": i, "tpl": templates[pick["tpl"]],
                                  "cooldown": variants[pick["variant"]]["cooldown"]}
                    if evt_lbl is not None:
                        st["pend"]["evt"] = evt_lbl[i]

    for side, st in slots.items():
        if st["pos"] is not None:
            _record(trades, st["pos"], c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    return trades


def _fit_detector(teach: pd.DataFrame, feat: pd.DataFrame, feat_cols: list, days_train: float,
                  v6: bool = False, evt: pd.DataFrame | None = None, rank_be: bool = False) -> dict:
    """検出器学習＝purged 5fold OOF → oof_theta（θ）を学習窓分位から選定 → 学習窓全体で再 fit。
    θ選定＝v5: ゲート通過イベント/日 ≥ FREQ_FLOOR_EVT_DAY の範囲で be 最大（採点窓不参照）
           v6/v6r: _select_theta_be_first（be≥BE_FLOOR 内で頻度最大・反転）＋旧規則も比較ログ（lever-bites）。
    v6 は event_type one-hot（EVENT_TYPES）を特徴に追加＝どのイベント型が稼げるかを木が判定。
    rank_be（v6r・RANK_BE_REGRESSION）＝教師を per-event の be（net/fee・無次元）の回帰にし、
    ランキングを金額整合へ（二値 P(net>0) は金額を見ず薄利勝ち玉が上位帯を希釈＝ledger ARC19 の是正）。"""
    import lightgbm as lgb
    df = teach.merge(feat.rename(columns={"timestamp": "ts"}), on="ts", how="inner").sort_values("ts").reset_index(drop=True)
    miss = len(teach) - len(df)
    print(f"  [検出器] 教師 {len(teach)} 件（特徴結合 {len(df)}・特徴欠落 {miss} 件は学習から除外）/ 勝ちラベル率 {df.y.mean()*100:.1f}%"
          + (f" / 教師目標={RANK_BE_REGRESSION}（per-event net/fee 回帰）" if rank_be else ""))
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
    y_reg = (df["net"] / df["fee"]).to_numpy() if rank_be else None   # per-event be（無次元 H6・実測比）
    tt = pd.DatetimeIndex(df.ts)
    oof = np.full(len(df), np.nan)
    for tr, te in purged_fold(tt):
        if rank_be:
            mdl = lgb.LGBMRegressor(**_LGB_PARAMS)
            mdl.fit(X[tr], y_reg[tr])
            oof[te] = mdl.predict(X[te])
        else:
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
    if rank_be:
        final = lgb.LGBMRegressor(**_LGB_PARAMS)
        final.fit(X, y_reg)
    else:
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
            "pick_old_rule": pick_old, "rank_be": rank_be}


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
        if det.get("rank_be"):
            p = det["model"].predict(X)          # v6r: 回帰スコア（期待 be）
        else:
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
# ══ ③v10 ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP・acceptance 2026-07-04・ML 不使用・素ルール）══
def _rsi9_v10(df: pd.DataFrame) -> pd.DataFrame:
    """RSI9（5分足スキャル設定・technical_kb §4）。当該足まで＝H2。分析用 rsi(14) とは別列。"""
    delta = df["close"].diff()
    up = delta.clip(lower=0).rolling(9).mean()
    dn = (-delta.clip(upper=0)).rolling(9).mean()
    df["rsi9"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    return df


def _zones_v10(df: pd.DataFrame) -> pd.DataFrame:
    """タッチ実績のあるゾーン（range_scalping_kb §2）＝過去 V10_LOOKBACK 本の確定ピボット
    （structure_features の fractal j+2 確定＝当該足までで確定・H2）を価格帯 V10_ZONE_TOL で束ね、
    タッチ回数（束ねたピボット数＋帯への接触バー数）が V10_TOUCH_MIN 以上の帯だけを
    「機能しているレジスタンス／サポートゾーン」とする。破れ（最終ピボットより後に
    出来高>20期間平均 ∩ 終値が帯の外）で無効化＝KB §5「破れたら黙る」。
    付与列: v10_res_lo/hi・v10_sup_lo/hi・v10_mid・range_ok_v10（GATE_IDENT＝局面の物理 AND）。"""
    is_res, is_sup, piv_h, piv_l = sf._detect_fractals(df)
    n = len(df)
    h = df["high"].to_numpy(float); l = df["low"].to_numpy(float)
    c = df["close"].to_numpy(float); v = df["volume"].to_numpy(float)
    vma = pd.Series(v).rolling(20).mean().to_numpy(float)
    is_res = np.asarray(is_res, bool); is_sup = np.asarray(is_sup, bool)
    piv_h = np.asarray(piv_h, float); piv_l = np.asarray(piv_l, float)
    res_idx = np.flatnonzero(is_res); res_px = piv_h[res_idx]
    sup_idx = np.flatnonzero(is_sup); sup_px = piv_l[sup_idx]
    z_res_lo = np.full(n, np.nan); z_res_hi = np.full(n, np.nan)
    z_sup_lo = np.full(n, np.nan); z_sup_hi = np.full(n, np.nan)
    ok = np.zeros(n, bool)

    def _best_zone(px_arr, idx_arr, i, lo_w, price, above):
        """窓内の確定ピボットを価格で束ね、price の上（above=True）/下で最も近い有効ゾーンを返す。
        有効＝タッチ（ピボット数＋帯接触バー数）≥ V10_TOUCH_MIN かつ 破れなし。無ければ None。"""
        j0 = int(np.searchsorted(idx_arr, lo_w)); j1 = int(np.searchsorted(idx_arr, i + 1))
        if j1 <= j0:
            return None
        px = px_arr[j0:j1]; pidx = idx_arr[j0:j1]
        sel = (px > price) if above else (px < price)
        if not sel.any():
            return None
        px = px[sel]; pidx = pidx[sel]
        order = np.argsort(px)
        px = px[order]; pidx = pidx[order]
        clusters = []
        s = 0
        for k in range(1, len(px) + 1):
            if k == len(px) or px[k] - px[k - 1] > px[k - 1] * V10_ZONE_TOL:
                clusters.append((px[s:k], pidx[s:k]))
                s = k
        clusters.sort(key=lambda cl: abs(float(np.mean(cl[0])) - price))   # price に近いゾーンから評価
        hw = h[lo_w:i + 1]; lw = l[lo_w:i + 1]; cw = c[lo_w:i + 1]
        vw = v[lo_w:i + 1]; vmw = vma[lo_w:i + 1]
        for cpx, cidx in clusters:
            zlo = float(cpx.min()) * (1 - V10_ZONE_TOL / 2)
            zhi = float(cpx.max()) * (1 + V10_ZONE_TOL / 2)
            touch_bars = int(np.count_nonzero((hw >= zlo) & (lw <= zhi)))
            if len(cpx) + touch_bars < V10_TOUCH_MIN:
                continue
            last_piv = int(cidx.max()) - lo_w
            cw_a = cw[last_piv + 1:]; vw_a = vw[last_piv + 1:]; vmw_a = vmw[last_piv + 1:]
            broke = ((cw_a > zhi) if above else (cw_a < zlo)) & (vw_a > vmw_a)
            if broke.any():
                continue                                   # 破れ済み＝無効（KB §5＝E32b に道を譲る）
            return zlo, zhi
        return None

    start = max(V10_LOOKBACK, 21)
    for i in range(start, n):
        lo_w = i - V10_LOOKBACK + 1
        rz = _best_zone(res_px, res_idx, i, lo_w, c[i], above=True)
        if rz is None:
            continue
        sz = _best_zone(sup_px, sup_idx, i, lo_w, c[i], above=False)
        if sz is None:
            continue
        if (rz[0] - sz[1]) / c[i] < V10_MIN_RANGE_W:
            continue                                       # 幅が往復可能な最低幅未満＝レンジと呼ばない
        z_res_lo[i], z_res_hi[i] = rz
        z_sup_lo[i], z_sup_hi[i] = sz
        ok[i] = True
    df["v10_res_lo"] = z_res_lo; df["v10_res_hi"] = z_res_hi
    df["v10_sup_lo"] = z_sup_lo; df["v10_sup_hi"] = z_sup_hi
    df["v10_mid"] = (z_res_lo + z_sup_hi) / 2.0
    df["range_ok_v10"] = ok
    return df


def tp_ge_sl_check_v10(limit: float, tp_px: float, sl_px: float) -> bool:
    """TP 幅 ≥ SL 幅 かつ TP 幅 ≥ SCALP_FLOOR（KB §1/§4＝勝ち側を大きく・手数料超え・逆 R:R の物理禁止）。"""
    tp_w = limit - tp_px
    sl_w = sl_px - limit
    return bool(np.isfinite(tp_w) and np.isfinite(sl_w) and sl_w > 0
                and tp_w >= sl_w and tp_w >= limit * SCALP_FLOOR)


def v10_entry_candidates(df: pd.DataFrame) -> np.ndarray:
    """v10 入口候補（KB §3＝到達＋拒否確認）＝range_ok_v10 ∩ 上限ゾーン接触 ∩ 陰転 ∩ RSI9 買われすぎ反転。
    エンジンと diagnostic が同一条件を使う（条件の二重実装を避ける）。"""
    h = df["high"].to_numpy(float); c = df["close"].to_numpy(float); o = df["open"].to_numpy(float)
    rsi9 = df["rsi9"].to_numpy(float); rsi9_prev = np.roll(rsi9, 1); rsi9_prev[0] = np.nan
    ok = df["range_ok_v10"].to_numpy(bool)
    rz_lo = df["v10_res_lo"].to_numpy(float)
    touched = np.isfinite(rz_lo) & (h >= rz_lo)
    rejected = (c < o) & np.isfinite(rsi9) & np.isfinite(rsi9_prev) & (rsi9_prev > 70.0) & (rsi9 < rsi9_prev)
    return ok & touched & rejected


def run_continuous_v10(df, box_tf):
    """v10 エンジン＝素ルール SHORT 専用（short_only_v10・LONG スロットを持たない＝§1.2.1 ショートのみ）。
    入口: v10_entry_candidates → 指値 maker TTL（不約定は建てない）。TP/SL は発注時点のゾーン幾何で固定・
    tp_ge_sl_check_v10 を通らない候補は建てない。
    出口: SL=ゾーン上端×(1+V10_SL_BUF)（指値 maker・gap 反映・SL 優先）→ TP=レンジ中央（maker）→ TIME=T_MAX（taker）。
    全て約定 bar の次以降＝leak-safe（H2）。"""
    short_only_v10 = True                                  # SIDE_IDENT（LONG 入口の生成経路なし）
    n = len(df)
    ts = df["ts"].to_numpy()
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    cand = v10_entry_candidates(df)
    rz_lo = df["v10_res_lo"].to_numpy(float); rz_hi = df["v10_res_hi"].to_numpy(float)
    sz_hi = df["v10_sup_hi"].to_numpy(float); mid = df["v10_mid"].to_numpy(float)
    trades = []
    pos = None; pend = None
    for i in range(n):
        if pend is not None:
            el = i - pend["placed_idx"]
            filled = False
            if el > TTL:
                pend = None
            elif el >= 1 and h[i] >= pend["limit"]:
                filled = True
            if filled:
                if pos is None:
                    pos = {"side": "SHORT", "avg": pend["limit"], "size": UNIT, "add_count": 1,
                           "first_idx": i, "last_fill_idx": i,
                           "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i],
                           "W_entry": pend["W_pct"],
                           "max_fav": l[i], "max_adv": h[i],
                           "tp": pend["tp"], "sl": pend["sl"]}
                pend = None
        if pos is not None:
            pos["max_fav"] = min(pos["max_fav"], l[i]); pos["max_adv"] = max(pos["max_adv"], h[i])
        if pos is not None and i > pos["last_fill_idx"]:
            if h[i] >= pos["sl"]:
                _record(trades, pos, max(pos["sl"], o[i]), "SL_FILLED", i, ts); pos = None; continue
            if l[i] <= pos["tp"]:
                _record(trades, pos, pos["tp"], "TP_FILLED", i, ts); pos = None; continue
            if (i - pos["first_idx"]) >= T_MAX:
                _record(trades, pos, c[i], "TIME_EXIT", i, ts); pos = None; continue
        if pos is None and pend is None and cand[i]:
            lim = c[i] * (1.0 + ENTRY_OFFSET)
            tp_px = mid[i]
            sl_px = rz_hi[i] * (1.0 + V10_SL_BUF)
            if not tp_ge_sl_check_v10(lim, tp_px, sl_px):
                continue                                   # TP幅≥SL幅＋手数料床を満たさない候補は建てない
            pend = {"limit": lim, "placed_idx": i, "tp": tp_px, "sl": sl_px,
                    "W_pct": (rz_lo[i] - sz_hi[i]) / c[i] * 100.0}
    if pos is not None:
        _record(trades, pos, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    assert short_only_v10 and all(r["side"] == "SHORT" for r in trades), "short_only_v10 違反（LONG 玉が混入）"
    return trades


# ══ ③v11 視認校正レンジ計器の組み込み（1hゾーン×複数TP+add・acceptance 2026-07-05・ML 不使用・素ルール）══
def _zones_v11_1h(df: pd.DataFrame) -> pd.DataFrame:
    """v17 計器（scripts/dashboard/build_range_gate_dashboard.py の _zones_1h）と同一ロジック・同一パラメータ。
    1時間足（label=right/closed=right＝バー確定時刻）の確定 fractal スイング（j+2 確定＝H2 leak-safe）を
    価格帯 V11_ZONE_TOL で束ね、スイング数≥V11_ZONE_TOUCH のゾーンが close の上下に揃い
    幅≥V11_ZONE_MIN_W ならレンジ局面。出力は labels_v17.csv と全期間一致（--v11-selftest-zones で機械照合）。
    ★トレンド排除は「ゾーンが立つか否か」が担う（トレンド中はスイングが同価格帯に集まらず立たない）。"""
    d5 = df.set_index(pd.DatetimeIndex(df["ts"]))
    z = pd.DataFrame({
        "open": d5["open"].resample("1h", label="right", closed="right").first(),
        "high": d5["high"].resample("1h", label="right", closed="right").max(),
        "low": d5["low"].resample("1h", label="right", closed="right").min(),
        "close": d5["close"].resample("1h", label="right", closed="right").last(),
        "volume": d5["volume"].resample("1h", label="right", closed="right").sum(),
    }).dropna(subset=["close"])
    is_res, is_sup, piv_h, piv_l = sf._detect_fractals(z)
    n = len(z)
    c = z["close"].to_numpy(float)
    is_res = np.asarray(is_res, bool); is_sup = np.asarray(is_sup, bool)
    piv_h = np.asarray(piv_h, float); piv_l = np.asarray(piv_l, float)
    res_idx = np.flatnonzero(is_res); res_px = piv_h[res_idx]
    sup_idx = np.flatnonzero(is_sup); sup_px = piv_l[sup_idx]
    r_lo = np.full(n, np.nan); r_hi = np.full(n, np.nan)
    s_lo = np.full(n, np.nan); s_hi = np.full(n, np.nan)
    ok = np.zeros(n, bool)

    def best_zone(px_arr, idx_arr, i, lo_w, price, above):
        j0 = int(np.searchsorted(idx_arr, lo_w)); j1 = int(np.searchsorted(idx_arr, i + 1))
        if j1 <= j0:
            return None
        px = px_arr[j0:j1]
        sel = (px > price) if above else (px < price)
        if not sel.any():
            return None
        px = np.sort(px[sel])
        clusters = []; s = 0
        for k in range(1, len(px) + 1):
            if k == len(px) or px[k] - px[k - 1] > px[k - 1] * V11_ZONE_TOL:
                clusters.append(px[s:k]); s = k
        clusters.sort(key=lambda cl: abs(float(np.mean(cl)) - price))   # price に近いゾーンから
        for cpx in clusters:
            if len(cpx) >= V11_ZONE_TOUCH:
                return float(cpx.min()) * (1 - V11_ZONE_TOL / 2), float(cpx.max()) * (1 + V11_ZONE_TOL / 2)
        return None

    start = max(V11_ZONE_LOOKBACK, 25)
    for i in range(start, n):
        lo_w = i - V11_ZONE_LOOKBACK + 1
        rz = best_zone(res_px, res_idx, i, lo_w, c[i], True)
        if rz is None:
            continue
        sz = best_zone(sup_px, sup_idx, i, lo_w, c[i], False)
        if sz is None:
            continue
        if (rz[0] - sz[1]) / c[i] < V11_ZONE_MIN_W:
            continue
        r_lo[i], r_hi[i] = rz; s_lo[i], s_hi[i] = sz; ok[i] = True
    z["res_lo"] = r_lo; z["res_hi"] = r_hi; z["sup_lo"] = s_lo; z["sup_hi"] = s_hi
    z["range_ok"] = ok
    return z


def _apply_v11_to_5m(df: pd.DataFrame, z1h: pd.DataFrame) -> pd.DataFrame:
    """1h ゾーン局面を 5m へ ffill（過去方向＝H2）し、5分足の即離脱ガード（ゾーンブレイク）を重ねる。
    range_ok_v11（GATE_IDENT）＝1h レンジ局面 ∩ 5分 close がゾーン内（ブレイクで新規候補を生成しない）。"""
    idx5 = pd.DatetimeIndex(df["ts"])
    ok1h = z1h["range_ok"].reindex(idx5, method="ffill").fillna(False).to_numpy(bool)
    res_lo = z1h["res_lo"].reindex(idx5, method="ffill").to_numpy(float)
    res_hi = z1h["res_hi"].reindex(idx5, method="ffill").to_numpy(float)
    sup_lo = z1h["sup_lo"].reindex(idx5, method="ffill").to_numpy(float)
    sup_hi = z1h["sup_hi"].reindex(idx5, method="ffill").to_numpy(float)
    c = df["close"].to_numpy(float)
    brk = (c > res_hi) | (c < sup_lo)                  # 5分足でゾーン外れ（ブレイク＝離脱・v17 計器と同一）
    brk = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), brk, False)
    df["v11_res_lo"] = res_lo; df["v11_res_hi"] = res_hi
    df["v11_sup_lo"] = sup_lo; df["v11_sup_hi"] = sup_hi
    df["v11_mid"] = (res_lo + sup_hi) / 2.0
    df["range_ok_v11"] = ok1h & ~brk
    return df


def tp_ge_sl_check_v11(limit: float, tp1_px: float, tp2_px: float, sl_px: float, single_tp: bool = False) -> bool:
    """R:R の物理条件（KB §1/§4＝勝ち側を大きく・手数料超え・逆 R:R の禁止）:
    TP2 幅 ≥ SL 幅 ∩（複数TP: TP1 幅 ≥ SCALP_FLOOR ／ 単一TP 対照: TP2 幅 ≥ SCALP_FLOOR）。"""
    tp1_w = limit - tp1_px
    tp2_w = limit - tp2_px
    sl_w = sl_px - limit
    if not (np.isfinite(tp1_w) and np.isfinite(tp2_w) and np.isfinite(sl_w) and sl_w > 0):
        return False
    if tp2_w < sl_w:
        return False
    floor_w = (tp2_w if single_tp else tp1_w)
    return bool(floor_w >= limit * SCALP_FLOOR)


def v11_entry_candidates(df: pd.DataFrame) -> np.ndarray:
    """v11 入口候補（KB §3＝到達＋拒否確認・v10 の実証部品を維持）＝
    range_ok_v11 ∩ 上限ゾーン接触（high≥ゾーン下端）∩ 陰転 ∩ RSI9 買われすぎ反転。"""
    h = df["high"].to_numpy(float); c = df["close"].to_numpy(float); o = df["open"].to_numpy(float)
    rsi9 = df["rsi9"].to_numpy(float); rsi9_prev = np.roll(rsi9, 1); rsi9_prev[0] = np.nan
    ok = df["range_ok_v11"].to_numpy(bool)
    rz_lo = df["v11_res_lo"].to_numpy(float)
    touched = np.isfinite(rz_lo) & (h >= rz_lo)
    rejected = (c < o) & np.isfinite(rsi9) & np.isfinite(rsi9_prev) & (rsi9_prev > 70.0) & (rsi9 < rsi9_prev)
    return ok & touched & rejected


def run_continuous_v11(df, box_tf, no_add: bool = False, single_tp: bool = False):
    """v11 エンジン＝素ルール SHORT 専用（short_only_v11・LONG 入口の生成経路なし＝§1.2.1 ショートのみ）。
    入口: v11_entry_candidates → 指値 maker TTL（不約定は建てない）。TP/SL は発注時点のゾーン幾何で固定・
    tp_ge_sl_check_v11 を通らない候補は建てない。
    出口（lot ごと・SL 優先＝eval_engine と同順）: SL=ゾーン上端×(1+V11_SL_BUF)（maker・gap 反映・全量）
      → TP1=(建値+中央)/2 で半分（PARTIAL_TP・maker）→ TP2=中央で残り（TP_FILLED・maker）
      → TIME=T_MAX 60分 backstop（taker）。
    add: 保有中に入口条件の完全再発火で同量 UNIT を追加（最大 V11_MAX_ADDS lot＝レンジの上限ゾーン再テストで
    小刻みに売り増して複数TP で刻む＝KB §6.5 V9型・Bitget 同サイド merge＋複数TP の写像・トレンド型ピラミッド不採用）。
    全て約定 bar の次以降＝leak-safe（H2）。"""
    short_only_v11 = True                              # SIDE_IDENT（LONG 入口の生成経路なし）
    n = len(df)
    ts = df["ts"].to_numpy()
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    cand = v11_entry_candidates(df)
    rz_lo = df["v11_res_lo"].to_numpy(float); rz_hi = df["v11_res_hi"].to_numpy(float)
    sz_hi = df["v11_sup_hi"].to_numpy(float); mid = df["v11_mid"].to_numpy(float)
    max_lots = 1 if no_add else V11_MAX_ADDS
    trades = []
    lots = []                                          # 保有中 lot（同サイド merge＝単一 SHORT ポジの写像・最大 max_lots）
    pend = None
    for i in range(n):
        if pend is not None:
            el = i - pend["placed_idx"]
            if el > TTL:
                pend = None
            elif el >= 1 and h[i] >= pend["limit"]:
                lots.append({"side": "SHORT", "avg": pend["limit"], "size": UNIT,
                             "add_count": len(lots) + 1, "first_idx": i, "last_fill_idx": i,
                             "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i],
                             "W_entry": pend["W_pct"], "max_fav": l[i], "max_adv": h[i],
                             "tp1": pend["tp1"], "tp2": pend["tp2"], "sl": pend["sl"], "tp1_done": False})
                pend = None
        for lot in lots:
            lot["max_fav"] = min(lot["max_fav"], l[i]); lot["max_adv"] = max(lot["max_adv"], h[i])
        still = []
        for lot in lots:
            if i <= lot["last_fill_idx"]:
                still.append(lot); continue
            if h[i] >= lot["sl"]:                      # ① SL 優先（同 bar 両到達は不利側先着＝保守・全量）
                _record(trades, lot, max(lot["sl"], o[i]), "SL_FILLED", i, ts); continue
            if (not single_tp) and (not lot["tp1_done"]) and l[i] <= lot["tp1"]:
                half = dict(lot); half["size"] = lot["size"] / 2.0
                _record(trades, half, lot["tp1"], "PARTIAL_TP", i, ts)   # ② TP1＝半分を部分決済（maker・登録済み）
                lot["size"] = lot["size"] / 2.0
                lot["tp1_done"] = True
            if l[i] <= lot["tp2"]:                     # ③ TP2＝レンジ中央で残り全部（maker）
                _record(trades, lot, lot["tp2"], "TP_FILLED", i, ts); continue
            if (i - lot["first_idx"]) >= T_MAX:        # ④ 60分 backstop（taker・lot ごと）
                _record(trades, lot, c[i], "TIME_EXIT", i, ts); continue
            still.append(lot)
        lots = still
        if pend is None and cand[i] and len(lots) < max_lots:
            lim = c[i] * (1.0 + ENTRY_OFFSET)
            tp2_px = mid[i]
            tp1_px = (lim + tp2_px) / 2.0
            sl_px = rz_hi[i] * (1.0 + V11_SL_BUF)
            if not tp_ge_sl_check_v11(lim, tp1_px, tp2_px, sl_px, single_tp=single_tp):
                continue                               # TP幅≥SL幅＋手数料床を満たさない候補は建てない
            pend = {"limit": lim, "placed_idx": i, "tp1": tp1_px, "tp2": tp2_px, "sl": sl_px,
                    "W_pct": (rz_lo[i] - sz_hi[i]) / c[i] * 100.0}
    for lot in lots:
        _record(trades, lot, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    assert short_only_v11 and all(r["side"] == "SHORT" for r in trades), "short_only_v11 違反（LONG 玉が混入）"
    return trades


def _selftest_zones_v11(df: pd.DataFrame) -> None:
    """自己検査（acceptance F-1）: _zones_v11_1h の出力が視認校正済み計器の labels_v17.csv と全期間一致するか機械照合。
    一致＝まこさんがダッシュボードで校正した判定と同一のレンジ判定で戦略が動く証明。"""
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    lab_path = repo_root / "dashboard" / "regime_prototype" / "labels_v17.csv"
    assert lab_path.exists(), f"labels_v17.csv がありません: {lab_path}"
    z = _zones_v11_1h(df)
    lab = pd.read_csv(lab_path, parse_dates=["datetime_utc"]).set_index("datetime_utc").sort_index()
    j = z.join(lab, how="inner", rsuffix="_lab")
    assert len(j) > 0, "labels_v17.csv と 1h index が重ならない（入力 CSV が違う疑い）"
    ok_mis = int((j["range_ok"].astype(int) != j["range_ok_lab"].astype(int)).sum())
    px_mis = 0
    for col in ("res_lo", "res_hi", "sup_lo", "sup_hi"):
        a = j[col].round(1); b = j[f"{col}_lab"]
        both = a.notna() & b.notna()
        px_mis += int(((a[both] - b[both]).abs() > 0.1).sum())   # labels は round(1) 保存＝0.1 丸めで照合
        px_mis += int((a.isna() != b.isna()).sum())
    print(f"  [selftest zones v11] 1h {len(j):,}本 / range_ok 不一致 {ok_mis} / ゾーン価格 不一致 {px_mis}（labels_v17.csv 照合）")
    assert ok_mis == 0 and px_mis == 0, "v11 ゾーンが labels_v17.csv と不一致＝移植ミス（視認校正した判定と別物）"
    print("  [selftest zones v11] ✅ 全期間一致＝視認校正済み計器と同一のレンジ判定")


def _param_sections(det: dict | None, gate_on: bool, v6: bool = False, v6r: bool = False, v7: bool = False, v8: bool = False, v9: bool = False, v10: bool = False, v11: bool = False, v11_no_add: bool = False, v11_single_tp: bool = False) -> dict:
    if v11:
        return {
            "検証期間（periods正本・E31）": {
                "学習(fit)": f"〜{TRAIN_END.date()} 未満（v11 は fit なし＝素ルール・分位選定なし）",
                "採点(公式net)": f"{SC_START.date()} 〜 {SCORE_END.date()} 未満",
                "封印(不参照)": f"{SEAL_START.date()} 以降",
            },
            "【入口】視認校正レンジ計器×拒否確認（SHORT のみ・§1.2.1・acceptance 2026-07-05）": {
                "レンジ判定 range_ok_v11": (
                    f"1時間足の確定 fractal スイングを過去{V11_ZONE_LOOKBACK}h(7日)窓・価格帯{V11_ZONE_TOL*100:.1f}%で束ね、"
                    f"スイング数≥{V11_ZONE_TOUCH}のS/Rゾーンが close の上下に揃い幅≥{V11_ZONE_MIN_W*100:.1f}%＝レンジ局面。"
                    "5分足で close がゾーン外（ブレイク）なら離脱＝新規候補を生成しない"
                    "（まこさん視認校正済み v17 計器と同一ロジック・labels_v17.csv 一致を selftest で機械照合・トレンド排除はゾーンが立つか否かが担う）"),
                "エントリー": "上限ゾーン接触（high≥ゾーン下端）∩ 陰転バー ∩ RSI9>70 からの下向き反転（到達＋拒否確認・v10 と同一）",
                "方向 short_only_v11": "SHORT のみ（LONG 入口の生成経路なし・上限ゾーンのみ使用）",
            },
            "【固定値】サイズ（スキャル＝add で積み・複数TPで刻む）": {
                "予算上限": f"全建玉合計 {CAP} BTC（H1・共有枠）・本戦略の同時最大 {UNIT * V11_MAX_ADDS} BTC（{V11_MAX_ADDS} lot）",
                "size": f"{UNIT} BTC/lot・V11_MAX_ADDS={V11_MAX_ADDS}（保有中の入口条件 完全再発火で同量 add＝上限ゾーン再テストの統合・トレンド型ピラミッド不採用）",
                "指値": f"close×(1+{ENTRY_OFFSET})・TTL {TTL}本(={TTL*5}分)・不約定は建てない（maker限定）",
                "対照フラグ": f"--v11-no-add（1 lot）/ --v11-single-tp（TP2 のみ＝v10 出口）＝diagnostic 寄与分離用（no_add={v11_no_add}・single_tp={v11_single_tp}）",
            },
            "【出口】レンジ幾何・複数TP 2段（新 exit_reason なし・既存登録のみ）": {
                "TP1 部分利確 PARTIAL_TP(maker指値)": f"(建値+レンジ中央)/2 で lot の半分（{UNIT/2} BTC）・TP1幅 ≥{SCALP_FLOOR*100:.2f}%（手数料床＝maker往復0.028%の約2.9倍）",
                "TP2 利確 TP_FILLED(maker指値)": "レンジ中央（(上限ゾーン下端+下限ゾーン上端)/2）で残り全部",
                "SL SL_FILLED(maker指値)": f"上限ゾーン上端×(1+{V11_SL_BUF*100:.2f}%)＝ゾーンのすぐ外（浅い・gap 反映・SL 優先・全 lot 共通の構造基準）",
                "R:R の物理条件 tp_ge_sl_check_v11": "TP2幅 ≥ SL幅 ∩ TP1幅 ≥ 手数料床 でなければ建てない（逆R:R の禁止＝KB §1）",
                "時間切れ TIME_EXIT(成行taker)": f"lot の初回entryから {T_MAX}本 = {T_MAX*5}分（短保有＝分単位・lot ごと）",
            },
            "【固定値】コスト（eval_engine・確定値・改造禁止）": {
                "maker手数料": f"{ee.MAKER_FEE*100:.3f}%", "taker手数料": f"{ee.TAKER_FEE*100:.3f}%",
                "slippage": f"{ee.SLIPPAGE*100:.3f}%（taker時のみ）", "funding": f"{ee.FUNDING_RATE_8H*100:.4f}% / 8h",
            },
            "【備考】": {
                "ML/検出器": "不使用（素ルール＝v5〜v10 の既存経路は不変・--v11 OFF で v10 恒等）",
                "数値の出所": "ゾーン4値=視認校正（まこさん 2026-07-05 概ね良い・v17 計器と同一）/ SLバッファ=v10 と同一 / V11_MAX_ADDS=cap幾何とV9前例 / SCALP_FLOOR・TTL・T_MAX・UNIT=既存定数（スイープなし・L-267）",
            },
        }
    if v10:
        return {
            "検証期間（periods正本・E31）": {
                "学習(fit)": f"〜{TRAIN_END.date()} 未満（v10 は fit なし＝素ルール・分位選定なし）",
                "採点(公式net)": f"{SC_START.date()} 〜 {SCORE_END.date()} 未満",
                "封印(不参照)": f"{SEAL_START.date()} 以降",
            },
            "【入口】ゾーン方式レンジ判定×拒否確認（SHORT のみ・§1.2.1・range_scalping_kb §2/§3）": {
                "レンジ判定 range_ok_v10": (
                    f"過去{V10_LOOKBACK}本(24h)の確定ピボット（fractal j+2）を価格帯 {V10_ZONE_TOL*100:.2f}% で束ね、"
                    f"タッチ回数（ピボット数＋帯接触バー数）≥{V10_TOUCH_MIN} のゾーンが上下に揃い、"
                    f"ゾーン間幅 ≥{V10_MIN_RANGE_W*100:.2f}% の時だけ入口を開く（統計量でなく機能実績のあるレベル）"),
                "ゾーン破れの無効化": "最終ピボットより後に 出来高>20期間平均 ∩ 終値がゾーン外 → 無効（レンジ破れ＝黙る・E32b に道を譲る）",
                "エントリー": "上限ゾーン接触（high≥ゾーン下端）∩ 陰転バー ∩ RSI9>70 からの下向き反転（到達＋拒否確認・確認なしでは入らない）",
                "方向 short_only_v10": "SHORT のみ（LONG 入口の生成経路なし・上限ゾーンのみ使用）",
            },
            "【固定値】サイズ（スキャル＝単発・単一スロット）": {
                "予算上限": f"全建玉合計 {CAP} BTC（H1・共有枠）・本戦略の同時最大 {UNIT} BTC（SHORT 単一スロット）",
                "size": f"{UNIT} BTC・MAX_ADDS=1（単発）",
                "指値": f"close×(1+{ENTRY_OFFSET})・TTL {TTL}本(={TTL*5}分)・不約定は建てない（maker限定）",
            },
            "【出口】レンジ幾何（新 exit_reason なし・既存登録のみ）": {
                "TP利確 TP_FILLED(maker指値)": f"レンジ中央（(上限ゾーン下端+下限ゾーン上端)/2）・TP幅 ≥{SCALP_FLOOR*100:.2f}%（手数料床）",
                "SL SL_FILLED(maker指値)": f"上限ゾーン上端×(1+{V10_SL_BUF*100:.2f}%)＝ゾーンのすぐ外（浅い・gap 反映・SL 優先）",
                "R:R の物理条件 tp_ge_sl_check_v10": "TP幅 ≥ SL幅 でなければ建てない（逆R:R の禁止＝KB §1）",
                "時間切れ TIME_EXIT(成行taker)": f"初回entryから {T_MAX}本 = {T_MAX*5}分（短保有＝分単位）",
            },
            "【固定値】コスト（eval_engine・確定値・改造禁止）": {
                "maker手数料": f"{ee.MAKER_FEE*100:.3f}%", "taker手数料": f"{ee.TAKER_FEE*100:.3f}%",
                "slippage": f"{ee.SLIPPAGE*100:.3f}%（taker時のみ）", "funding": f"{ee.FUNDING_RATE_8H*100:.4f}% / 8h",
            },
            "【備考】": {
                "ML/検出器": "不使用（素ルール MVP＝v5〜v9 の検出器経路は不変・--v10 OFF で恒等）",
                "数値の出所": "タッチ≥3=range_scalping_kb §2 / 窓24h・束ね0.10%・SLバッファ0.05%=a-priori / SCALP_FLOOR・TTL・T_MAX・UNIT=既存定数（スイープなし・L-267）",
            },
        }
    if v9:
        evt_desc = {
            "イベント（v9・5型 相互排他＝v8 同一）": "特異度順（pull→brk→bb→mr→mr_sh）で1バー1型（入れ子解消・union 不変）",
            "組の共同選定（v9・型×side・acceptance フェーズ1）": (
                "入口バリアント（E0=現行／E1=実体過半の反転バー[0.5=過半の定義値]／E2=E1∩上位足整合[SHORT=1h MACD≤0・LONG=MACD>0]／"
                "E3=E2∩クールダウン[同sideのSL決済からT_MAX本]）×出口テンプレ（Xa=TP移動0.5σ・T12／Xb=fill固定0.5σ・T12／"
                "Xc=fill固定1.0σ・T12／Xd=fill固定1.0σ・T6）×θ分位 の組を、v8計器（実行同一規則の執行後フロンティア・学習窓OOF）で"
                f"型×sideごとに be≥{BE_FLOOR} 内 執行後件数/日最大で選定・組なしの型×sideは執行しない・全組なしなら停止"),
            "TP-viability（テンプレ幅対応）": f"entry 時点で TP 目標が指値から {SCALP_FLOOR*100:.2f}% 未満の候補は建てない（選定テンプレの tp_k で判定）",
        }
    elif v8:
        evt_desc = {
            "イベント（v8・5型 相互排他）": (
                f"v6 5型（EV_MR/EV_MR_SHALLOW/EV_BB/EV_BREAK_REV/EV_PULLBACK・教科書 a-priori）を"
                "特異度順（pull→brk→bb→mr→mr_sh）で1バー1型に割当＝入れ子解消（union 不変・教師母数を互いに素に）"),
            "検出器（v8・型別 fit）": "v7 同一（型ごとに LightGBM 独立 fit・教師=エンジン同一執行 Triple Barrier 二値・side は特徴列）",
            "θ選定規則（v8・型×side・執行後フロンティア）": (
                f"型×side ごとに be≥{BE_FLOOR}（損益分岐の定義値）を満たす候補のうち『実行同一規則（サイドごと単一スロット・"
                f"pending 占有・TTL タッチ約定）適用後の件数/日』最大・帯なしの型×side は執行しない・全帯なしなら執行せず停止"),
            "TP-viability entry ゲート（v8 同梱）": (
                f"entry 時点で TP 目標（SMA∓{TP_OVERSHOOT}σ）が指値価格から {SCALP_FLOOR*100:.2f}%（SCALP_FLOOR・既存定数）未満の候補は建てない"
                "（届いても手数料負け確定の毒を機械除去・教師とエンジンの両方＝同一執行・v6r 承認済み部品）"),
        }
    elif v7:
        evt_desc = {
            "イベント（v7・5型＝v6 同一・母数）": (
                f"EV_MR: dev_z±{SIG_Z}σ∩反転バー ／ EV_MR_SHALLOW: dev_z±{SHALLOW_Z}σ∩反転バー ／ "
                f"EV_BB: BB(20,{BB_K}σ)タッチ∩反転バー ／ EV_BREAK_REV: donchian({BREAK_N})ブレイク後{BREAK_LOOKBACK}本以内の反転バー ／ "
                f"EV_PULLBACK: 1h MACD 方向∩dev_z±{SHALLOW_Z}σ∩反転バー（順張り押し目/戻り売り）。全て教科書 a-priori"),
            "検出器（v7・型別 fit）": ("イベント型ごとに LightGBM を独立 fit（教師=その型のイベントのみ・エンジン同一執行 Triple Barrier 二値）"
                                  "＝混合母数が型内ランキングを半減させる（ledger ARC20）への直接対策"),
            "θ選定規則（v7・型別）": (f"型ごとに be≥{BE_FLOOR}（損益分岐の定義値）を満たす学習窓 OOF 分位のうちイベント/日最大・"
                                 f"帯なしの型は不使用・届いた型の帯を合併（OR）して執行・全型帯なしなら執行せず停止"),
            "TP-viability entry ゲート（v7 同梱）": (
                f"entry 時点で TP 目標（SMA∓{TP_OVERSHOOT}σ）が指値価格から {SCALP_FLOOR*100:.2f}%（SCALP_FLOOR・既存定数）未満の候補は建てない"
                "（届いても手数料負け確定の毒を機械除去・教師とエンジンの両方＝同一執行・v6r 承認済み部品）"),
        }
    elif v6:
        evt_desc = {
            "イベント（v6・5型＝母数拡大・どれが稼げるかは検出器が判定）": (
                f"EV_MR: dev_z±{SIG_Z}σ∩反転バー（v5 同一）／ EV_MR_SHALLOW: dev_z±{SHALLOW_Z}σ∩反転バー ／ "
                f"EV_BB: BB(20,{BB_K}σ)タッチ∩反転バー ／ EV_BREAK_REV: donchian({BREAK_N})ブレイク後{BREAK_LOOKBACK}本以内の反転バー ／ "
                f"EV_PULLBACK: 1h MACD 方向∩dev_z±{SHALLOW_Z}σ∩反転バー（順張り押し目/戻り売り）。全て教科書 a-priori 構造"),
            "θ選定規則（v6・反転）": f"be≥{BE_FLOOR}（損益分岐の定義値）を満たす学習窓 OOF 分位のうちイベント/日最大（頻度床は選定に使わない・be≥{BE_FLOOR} 帯なしなら執行せず停止）",
        }
        if v6r:
            evt_desc["検出器の教師（v6r・金額整合）"] = (
                f"per-event の be＝net/fee（無次元・エンジン同一執行の実測比）の回帰（{RANK_BE_REGRESSION}・L2）"
                "＝二値 P(net>0) が金額を見ず薄利勝ち玉を上位帯に集めた v6 の是正（分類=向き/回帰=大きさ＝arxiv 2407.18334）")
            evt_desc["TP-viability entry ゲート（v6r）"] = (
                f"entry 時点で TP 目標（SMA∓{TP_OVERSHOOT}σ）が指値価格から {SCALP_FLOOR*100:.2f}%（SCALP_FLOOR・既存定数）未満の候補は建てない"
                "（届いても手数料負け確定の毒を機械除去・教師とエンジンの両方＝同一執行）")
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
                      + ("＝型別に独立 fit（v7・one-hot 不使用）" if v7 else ("＋event_type one-hot 特徴（v6）" if v6 else "")),
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
        if v9:
            sec["【学習した内容】型×side 組選定ログ（v9・学習窓 OOF・執行後フロンティア・組なし=null）"] = {
                k: json.dumps(v, ensure_ascii=False) for k, v in det["sel_log"].items()
            }
        elif v8:
            sec["【学習した内容】型×side 検出器 θ 選定ログ（v8・学習窓 OOF・執行後フロンティア・採点窓不参照・帯なし=picked null）"] = {
                name: json.dumps(log, ensure_ascii=False) for name, log in det["frontier_log"].items()
            }
            sec["【学習した内容】型別 重要度top10（v8・使用型のみ）"] = {
                name: ", ".join(d_["top10"]) for name, d_ in det["dets"].items()
            }
        elif v7:
            sec["【学習した内容】型別検出器 θ 選定ログ（v7・学習窓 OOF・採点窓不参照・帯なし型=picked null）"] = {
                name: json.dumps(log, ensure_ascii=False) for name, log in det["frontier_log"].items()
            }
            sec["【学習した内容】型別 重要度top10（v7・使用型のみ）"] = {
                name: ", ".join(d_["top10"]) for name, d_ in det["dets"].items()
            }
        else:
            sec["【学習した内容】検出器 θ 選定ログ（学習窓 OOF・採点窓不参照）"] = {
                "選定": json.dumps(det["picked"], ensure_ascii=False),
                "候補": json.dumps(det["theta_log"], ensure_ascii=False),
                "重要度top10": ", ".join(det["top10"]),
            }
    return sec


def run_e37(df, box_tf, tag=None, no_gate=False, v6=False, v6r=False, v7=False, v8=False, v9=False, v10=False, v11=False, v11_no_add=False, v11_single_tp=False):
    """E37 を回す（v6/v6r/v7/v8/v9/v10/v11=False で v5 恒等）。判定は score.py の数字（本関数は net を計算しない＝記録のみ）。
    v6r＝v6 のイベント5型に ①TP-viability entry ゲート ②検出器の金額整合回帰（RANK_BE_REGRESSION）を重ねる（acceptance 2026-07-03）。
    v7＝イベント5型＋TP-viability の上で、検出器の fit と θ 選定を型別に分け be≥1.0 帯の合併で執行（acceptance 2026-07-04）。
    v8＝v7 の上で選定計器を是正（型相互排他＋執行後フロンティア＋型×side 別 θ/be・acceptance 2026-07-04 フェーズ0）。
    v9＝v8 計器の上で型×side の Entry/Exit セット共同選定（入口バリアント×出口テンプレの組・acceptance 2026-07-04 フェーズ1）。
    v10＝素ルール MVP（§1.2.1 準拠・ゾーン方式レンジ判定×拒否確認 SHORT・ML 不使用・acceptance 2026-07-04）。
    v11＝視認校正レンジ計器の組み込み（1h S/Rゾーン×5分ブレイク離脱×複数TP+add・acceptance 2026-07-05）。"""
    src = pathlib.Path(__file__).read_text(encoding="utf-8")
    _p1 = "shift(" + "-"; _p2 = "center" + "=True"
    assert _p1 not in src and _p2 not in src, "leak 疑い（未来参照 shift/center）"   # H2 自己 grep
    assert not (v9 and no_gate), "v9 は組選定＝ゲートそのもの（--no-gate 併用不可）"
    if v11:
        assert not (v6 or v6r or v7 or v8 or v9 or v10 or no_gate), "v11 は素ルール（他バージョンフラグと併用不可）"
        df = _rsi9_v10(df)
        z1h = _zones_v11_1h(df)
        df = _apply_v11_to_5m(df, z1h)
        okn = int(df["range_ok_v11"].sum())
        cn = int(v11_entry_candidates(df).sum())
        print(f"  [range_ok_v11] レンジ判定 通過 {okn:,}/{len(df):,} バー（{okn/len(df)*100:.1f}%）"
              f"＝1h S/Rゾーン（スイング≥{V11_ZONE_TOUCH}・幅≥{V11_ZONE_MIN_W*100:.1f}%）∩ 5分ブレイクなし")
        print(f"  [入口候補 v11] 到達＋拒否確認 {cn:,} バー（no_add={v11_no_add}・single_tp={v11_single_tp}）")
        trades = run_continuous_v11(df, box_tf, no_add=v11_no_add, single_tp=v11_single_tp)
        t = pd.DataFrame(trades)
        if len(t):
            t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
            mx = _verify_cap(trades)
            print(f"  [自己検査 cap] 同時保有 max {mx:.4f} BTC ≤ {CAP}: {'✅' if mx <= CAP + 1e-9 else '⛔cap 超過'}")
            assert mx <= CAP + 1e-9, "cap 0.12 超過（H1 違反）"
            assert (t["size_btc"] >= ee.MIN_ORDER_BTC).all(), "最小注文サイズ違反（H9・PARTIAL_TP 半 lot 含む）"
        sfx = "_v11" + ("na" if v11_no_add else "") + ("st" if v11_single_tp else "")
        _out(t, f"_{box_tf}{sfx}", None, tag=tag, gate_on=True, v11=True, v11_no_add=v11_no_add, v11_single_tp=v11_single_tp)
        return
    if v10:
        assert not (v6 or v6r or v7 or v8 or v9 or no_gate), "v10 は素ルール MVP（他バージョンフラグと併用不可）"
        df = _rsi9_v10(df)
        df = _zones_v10(df)
        okn = int(df["range_ok_v10"].sum())
        cn = int(v10_entry_candidates(df).sum())
        print(f"  [range_ok_v10] レンジ判定 通過 {okn:,}/{len(df):,} バー（{okn/len(df)*100:.1f}%）"
              f"＝タッチ≥{V10_TOUCH_MIN} ゾーン上下＋幅≥{V10_MIN_RANGE_W*100:.2f}%")
        print(f"  [入口候補 v10] 到達＋拒否確認 {cn:,} バー")
        trades = run_continuous_v10(df, box_tf)
        t = pd.DataFrame(trades)
        if len(t):
            t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
            mx = _verify_cap(trades)
            print(f"  [自己検査 cap] 同時保有 max {mx:.4f} BTC ≤ {CAP}: {'✅' if mx <= CAP + 1e-9 else '⛔cap 超過'}")
            assert mx <= CAP + 1e-9, "cap 0.12 超過（H1 違反）"
            assert (t["size_btc"] >= ee.MIN_ORDER_BTC).all(), "最小注文サイズ違反（H9）"
        _out(t, f"_{box_tf}_v10", None, tag=tag, gate_on=True, v10=True)
        return
    v6 = v6 or v6r or v7 or v8 or v9
    df = _gen_events_v6(df) if v6 else micro_rev_event(df)
    if v8 or v9:
        df = _gen_events_v8_exclusive(df)          # v8①: 型の相互排他化（union 不変・教師母数を互いに素に）
    det = None
    evt_lbl = None
    if v6r or v7 or v8:
        df = _tp_viable(df)
        before = int(df["short_cand"].sum() + df["long_cand"].sum())
        df["short_cand"] = (df["short_cand"] & df["viable_s"].to_numpy(bool))
        df["long_cand"] = (df["long_cand"] & df["viable_l"].to_numpy(bool))
        after = int(df["short_cand"].sum() + df["long_cand"].sum())
        print(f"  [TP-viability] entry 時点で TP 目標<SCALP_FLOOR の候補を除外: {before:,} → {after:,} バー（−{before-after:,}）")
    if v6:
        m = df[list(EVENT_TYPES)].to_numpy(np.float32) > 0.5
        names = np.array(EVENT_TYPES)
        evt_lbl = np.array(["+".join(names[r]) if r.any() else "" for r in m])
        per = {name: int(df[name].sum()) for name in EVENT_TYPES}
        print(f"  [イベント {'v7' if v7 else 'v6'}] 型別候補バー: {json.dumps(per, ensure_ascii=False)}")
    if no_gate:
        gate_ok = np.ones(len(df), dtype=bool)
        print("  [ゲート] OFF（--no-gate＝恒等確認モード・全イベント執行）")
    else:
        cand_ts = df.loc[df["short_cand"] | df["long_cand"], "ts"]
        print(f"  [イベント] 候補 {len(cand_ts):,} バー（特徴回収に進む）")
        feat, feat_cols = _load_features(set(pd.DatetimeIndex(cand_ts).asi8))
        print(f"  [特徴] {len(feat_cols)} 列 × {len(feat):,} 行 回収（label_exclude_assert 通過）")
        if v9:
            days_train = max((pd.Timestamp(TRAIN_END) - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
            det = _select_combo_per_type_side(df, feat, feat_cols, days_train)   # 全型×side 組なしなら SystemExit
            gate_ok, via = _detector_gate_v9(det, feat, df)
            evt_lbl = via
            gated = int((gate_ok & (df["short_cand"] | df["long_cand"]).to_numpy(bool)).sum())
            print(f"  [ゲート v9] 型×side 選定組の合併 通過候補 {gated:,} バー")
            trades = run_continuous_v9(df, gate_ok, box_tf, det, evt_lbl=evt_lbl)
            t = pd.DataFrame(trades)
            if len(t):
                t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
                mx = _verify_cap(trades)
                print(f"  [自己検査 cap] 同時保有 max {mx:.4f} BTC ≤ {CAP}: {'✅' if mx <= CAP + 1e-9 else '⛔cap 超過'}")
                assert mx <= CAP + 1e-9, "cap 0.12 超過（H1 違反）"
                assert (t["size_btc"] >= ee.MIN_ORDER_BTC).all(), "最小注文サイズ違反（H9）"
                tr_n = int((t["entry_time"] < pd.Timestamp(TRAIN_END)).sum())
                days_tr = max((min(pd.Timestamp(TRAIN_END), df["ts"].iloc[-1]) - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
                sel = sum(p_["events_per_day"] for p_ in det["sel_log"].values() if p_)
                act = tr_n / days_tr
                dev = (act / sel - 1.0) * 100.0 if sel else float("nan")
                print(f"  [自己検査⑤ 計器整合] 選定時の執行後見積り {sel:.2f}件/日 vs 本走 学習窓 {act:.2f}件/日（乖離 {dev:+.0f}%）")
            _out(t, f"_{box_tf}_v9", det, tag=tag, gate_on=True, v6=True, v9=True)
            return
        teach = _teacher_labels(df, int(pd.Timestamp(TRAIN_END).value))
        days_train = max((teach.ts.max() - teach.ts.min()) / np.timedelta64(1, "D"), 1.0)
        if v8:
            det = _fit_detector_per_type_v8(teach, feat, feat_cols, days_train, df)   # 全型×side 帯なしなら SystemExit
            gate_ok, via = _detector_gate_v8(det, feat, df)
            evt_lbl = via                              # 記録＝通過させた型（lever-bites）
            gated = int((gate_ok & (df["short_cand"] | df["long_cand"]).to_numpy(bool)).sum())
            print(f"  [ゲート v8] 型×side 帯の合併 通過候補 {gated:,} バー")
        elif v7:
            det = _fit_detector_per_type(teach, feat, feat_cols, days_train, df)   # 全型帯なしなら SystemExit
            gate_ok, via = _detector_gate_v7(det, feat, df)
            evt_lbl = via                              # 記録＝通過させた型（lever-bites）
            gated = int((gate_ok & (df["short_cand"] | df["long_cand"]).to_numpy(bool)).sum())
            print(f"  [ゲート v7] 型別 θ 帯の合併 通過候補 {gated:,} バー")
        else:
            det = _fit_detector(teach, feat, feat_cols, days_train,
                                v6=v6, evt=(df[["ts"] + list(EVENT_TYPES)] if v6 else None), rank_be=v6r)
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
    if v8 and det is not None and len(t):
        # 自己検査⑤（acceptance F）: 選定時の執行後見積り vs 本走の学習窓 実件数/日（計器の是正確認・観測値として記録）
        tr_n = int((t["entry_time"] < pd.Timestamp(TRAIN_END)).sum())
        days_tr = max((min(pd.Timestamp(TRAIN_END), df["ts"].iloc[-1]) - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
        sel = sum(p_["events_per_day"] for d_ in det["dets"].values() for p_ in d_["picked_side"].values() if p_)
        act = tr_n / days_tr
        dev = (act / sel - 1.0) * 100.0 if sel else float("nan")
        print(f"  [自己検査⑤ 計器整合] 選定時の執行後見積り {sel:.2f}件/日（型×side 合算・型横断競合なし近似） "
              f"vs 本走 学習窓 {act:.2f}件/日（乖離 {dev:+.0f}%・±30%目安は観測値）")
    ver = "v8" if v8 else ("v7" if v7 else ("v6r" if v6r else ("v6" if v6 else "v5")))
    _out(t, f"_{box_tf}_{ver}", det, tag=tag, gate_on=not no_gate, v6=v6, v6r=v6r, v7=v7, v8=v8)


def _out(t: pd.DataFrame, suffix: str, det, tag=None, gate_on=True, v6=False, v6r=False, v7=False, v8=False, v9=False, v10=False, v11=False, v11_no_add=False, v11_single_tp=False) -> None:
    strat_base._output_and_report(
        t, suffix, stem="e37_range_scalp",
        strategy=("E37 v11 視認校正レンジ計器の組み込み（1h S/Rゾーン×5分ブレイク離脱×複数TP+add・SHORT のみ）" if v11
                  else "E37 v10 ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP・タッチ実績ゾーン×拒否確認・ML 不使用）" if v10
                  else "E37 v9 レンジ・スキャル 両側 maker MR＋型×side Entry/Exit セット共同選定（フェーズ1）" if v9
                  else "E37 v8 レンジ・スキャル 両側 maker MR＋型×side 検出器（選定計器の是正＝母数一致・side別be・型相互排他）" if v8
                  else "E37 v7 レンジ・スキャル 両側 maker MR＋型別検出器（帯の合併＋TP-viability）" if v7
                  else "E37 v6r レンジ・スキャル 両側 maker MR＋検出器ゲート（金額整合回帰＋TP-viability）" if v6r
                  else "E37 v6 レンジ・スキャル 両側 maker MR＋検出器ゲート（イベント5型＋θ規則反転）" if v6
                  else "E37 v5 レンジ・スキャル 両側 maker MR＋稼げるレンジ検出器ゲート"),
        script="e37_range_scalp.py",
        sections=_param_sections(det, gate_on, v6=v6, v6r=v6r, v7=v7, v8=v8, v9=v9, v10=v10, v11=v11, v11_no_add=v11_no_add, v11_single_tp=v11_single_tp), tag=tag)


def _load(smoke: int) -> pd.DataFrame:
    df = load_5m(smoke)
    df = e34v1.add_indicators(df)                 # sma/std/dev_z/atr/adx
    df = e34b.add_analysis_features(df)           # rsi/stoch_k（記録用）
    df = e35_box.add_box_features(df, verify_leak=(smoke > 0 and smoke <= 60000))   # box_W 記録用
    df["atr_pct"] = df["atr"] / df["close"] * 100.0
    return df


def _diagnostic(df, v6=False, v6r=False, v7=False, v8=False, v10=False, v11=False):
    """発火ファネル（採点しない）＝イベント頻度のみ（検出器は本走で学習＝重い処理を diagnostic で回さない）。"""
    if v11:
        df = _rsi9_v10(df)
        z1h = _zones_v11_1h(df)
        df = _apply_v11_to_5m(df, z1h)
        n = len(df)
        days = max((df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
        ok = df["range_ok_v11"].to_numpy(bool)
        cand = v11_entry_candidates(df)
        adx = df["adx"].to_numpy(float)
        print("=" * 100)
        print(f"[E37 v11 発火ファネル診断・採点しない] {n:,}本 / {days:.0f}日")
        print(f"  range_ok_v11 通過率  : {ok.mean()*100:.1f}%（1h S/Rゾーン スイング≥{V11_ZONE_TOUCH}・幅≥{V11_ZONE_MIN_W*100:.1f}% ∩ 5分ブレイクなし・v10 実績 53.1% と比較）")
        print(f"  入口候補（到達＋拒否確認）: {int(cand.sum()):,} 本（{cand.sum()/days:.2f}/日）")
        if cand.sum():
            adx_c = adx[cand]
            fin = np.isfinite(adx_c)
            print(f"  入口候補の ADX40+ 混入 : {(adx_c[fin] >= 40).mean()*100:.1f}%（v10 実績 38.5% と比較＝トレンド排除の実効）")
            w = (df.loc[cand, "v11_res_lo"] - df.loc[cand, "v11_sup_hi"]) / df.loc[cand, "close"] * 100
            print(f"  （参考）候補バーのゾーン幅: median {np.nanmedian(w):.3f}%（TP1/TP2 2段の手数料床 2×{SCALP_FLOOR*100:.2f}% と比較）")
        print("=" * 100)
        return
    if v10:
        df = _rsi9_v10(df)
        df = _zones_v10(df)
        n = len(df)
        days = max((df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
        ok = df["range_ok_v10"].to_numpy(bool)
        cand = v10_entry_candidates(df)
        adx = df["adx"].to_numpy(float)
        print("=" * 100)
        print(f"[E37 v10 発火ファネル診断・採点しない] {n:,}本 / {days:.0f}日")
        print(f"  range_ok_v10 通過率   : {ok.mean()*100:.1f}%（タッチ≥{V10_TOUCH_MIN} ゾーン上下＋幅≥{V10_MIN_RANGE_W*100:.2f}%）")
        print(f"  入口候補（到達＋拒否確認）: {int(cand.sum()):,} 本（{cand.sum()/days:.2f}/日）")
        if cand.sum():
            adx_c = adx[cand]
            fin = np.isfinite(adx_c)
            print(f"  入口候補の ADX40+ 混入 : {(adx_c[fin] >= 40).mean()*100:.1f}%（v9 実績 48.5% と比較＝レンジ判定の実効）")
            print(f"  （参考）候補バーのゾーン幅: median {np.nanmedian((df.loc[cand,'v10_res_lo']-df.loc[cand,'v10_sup_hi'])/df.loc[cand,'close']*100):.3f}%")
        print("=" * 100)
        return
    v6 = v6 or v6r or v7 or v8
    df = _gen_events_v6(df) if v6 else micro_rev_event(df)
    if v8:
        df = _gen_events_v8_exclusive(df)
    if v6r or v7 or v8:
        df = _tp_viable(df)
        before = int(df["short_cand"].sum() + df["long_cand"].sum())
        df["short_cand"] = (df["short_cand"] & df["viable_s"].to_numpy(bool))
        df["long_cand"] = (df["long_cand"] & df["viable_l"].to_numpy(bool))
        print(f"  [TP-viability] 候補 {before:,} → {int(df.short_cand.sum()+df.long_cand.sum()):,} バー")
    n = len(df)
    days = max((df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
    s = int(df["short_cand"].sum()); L = int(df["long_cand"].sum())
    print("=" * 100)
    print(f"[E37 {'v8' if v8 else 'v7' if v7 else 'v6r' if v6r else 'v6' if v6 else 'v5'} 発火ファネル診断・採点しない] {n:,}本 / {days:.0f}日")
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
    ap.add_argument("--v6r", action="store_true", help="v6r=v6＋検出器の金額整合回帰（net/fee）＋TP-viability entry ゲート（acceptance 2026-07-03）")
    ap.add_argument("--v7", action="store_true", help="v7=型別検出器（型ごとに独立 fit・型別 θ=be≥1.0 内で頻度最大・帯の合併）＋TP-viability（acceptance 2026-07-04）")
    ap.add_argument("--v8", action="store_true", help="v8=選定計器の是正（型相互排他＋執行後フロンティア＋型×side 別 θ/be・acceptance 2026-07-04 フェーズ0・既定 OFF=v7 恒等）")
    ap.add_argument("--v9", action="store_true", help="v9=型×side の Entry/Exit セット共同選定（入口バリアント×出口テンプレの組・acceptance 2026-07-04 フェーズ1・既定 OFF=v8 恒等）")
    ap.add_argument("--v10", action="store_true", help="v10=ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP・タッチ実績ゾーン×拒否確認・ML 不使用・acceptance 2026-07-04・既定 OFF=既存経路 恒等）")
    ap.add_argument("--v11", action="store_true", help="v11=視認校正レンジ計器の組み込み（1h S/Rゾーン×5分ブレイク離脱×複数TP+add・acceptance 2026-07-05・既定 OFF=v10 恒等）")
    ap.add_argument("--v11-no-add", action="store_true", help="v11 対照: add なし（1 lot）＝寄与分離用（diagnostic/学習窓）")
    ap.add_argument("--v11-single-tp", action="store_true", help="v11 対照: TP2 のみ（v10 出口）＝寄与分離用（diagnostic/学習窓）")
    ap.add_argument("--v11-selftest-zones", action="store_true", help="v11 自己検査: _zones_v11_1h が labels_v17.csv（視認校正済み計器）と全期間一致するか機械照合して終了")
    ap.add_argument("--tag", default=None, help="実験タグ。指定で出力名を _<tag>_<NNN> 連番にし旧実験を archive へ退避（実験は必ず付ける）")
    a = ap.parse_args()
    ver = "v11" if a.v11 else ("v10" if a.v10 else ("v9" if a.v9 else ("v8" if a.v8 else ("v7" if a.v7 else ("v6r" if a.v6r else ("v6" if a.v6 else "v5"))))))
    print("=" * 100)
    print(f"[E37 {ver}] " + ("視認校正レンジ計器の組み込み（1h S/Rゾーン×5分ブレイク離脱×複数TP+add・SHORT のみ）" if a.v11
          else "ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP・タッチ実績ゾーン×拒否確認・ML 不使用）" if a.v10
          else "レンジ・スキャル 両側 maker MR＋検出器ゲート"
          + ("（v9=型×side Entry/Exit セット共同選定・フェーズ1）" if a.v9
             else "（v8=選定計器の是正＝母数一致・side別be・型相互排他）" if a.v8
             else "（v7=型別検出器・帯の合併＋TP-viability）" if a.v7
             else "（v6r=金額整合回帰＋TP-viability）" if a.v6r else "（v6=イベント5型＋θ規則反転）" if a.v6 else "（E36 デイトレと住み分け）")))
    df = _load(a.smoke)
    print(f"  価格 {e34v1.CSV.name}（{len(df):,}本・{df.ts.iloc[0].date()}〜{df.ts.iloc[-1].date()}）")
    print(f"  計器 maker {ee.MAKER_FEE} / taker {ee.TAKER_FEE} / slip {ee.SLIPPAGE} / funding {ee.FUNDING_RATE_8H}/8h / unit {UNIT}")
    if a.v11_selftest_zones:
        _selftest_zones_v11(df)
        return
    if a.diagnostic:
        _diagnostic(df, v6=a.v6, v6r=a.v6r, v7=a.v7, v8=(a.v8 or a.v9), v10=a.v10, v11=a.v11)
        return
    run_e37(df, a.box_tf, tag=a.tag, no_gate=a.no_gate, v6=a.v6, v6r=a.v6r, v7=a.v7, v8=a.v8, v9=a.v9, v10=a.v10,
            v11=a.v11, v11_no_add=a.v11_no_add, v11_single_tp=a.v11_single_tp)
    print("=" * 100)


if __name__ == "__main__":
    main()
