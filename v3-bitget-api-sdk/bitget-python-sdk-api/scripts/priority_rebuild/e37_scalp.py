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

★v20（--v20-rg5・acceptance「E37 v20 RG-v5レンジ判定移植＋レンジ期間を漏れなく取る上端入口」承認 2026-07-12・既定 OFF=v19 恒等）:
  v10〜v19 の負けの根＝レンジ判定（range_ok_v11=v17 同一）のトレンド混入を、まこさん視認校正3巡の RG-v5
  （build_regime_gate_rg.py を import 再利用＝コピー禁止・labels_rg-v5 一致 selftest --v20-selftest-rg5）で機構除去し、
  レンジ中の上端ゾーン到達（res_lo・確認なし）で漏れなく建てる。保有中に RG の上げトレンド状態機械が発火したら
  TREND_CONT（登録済み taker）で即クローズ＋新規/add 停止（risk-manager 型・score.py 無変更 H13）。
  Exit/サイズ/add は v18 構成を定数継承（選定0回）。番人メタ確認＝--v20-guard-check。

★v21（--v21-set・acceptance「E37 v21 入口の反転確認（armed DC）＋uptrend畳み分岐（Entry×Exitセット）」承認 2026-07-12・既定 OFF=v20 恒等）:
  v20 の最大出血＝uptrend 発火時の taker 即クローズ（対照=枝OFF が学習窓 +$2,106 良い＝最悪点確定）と、その供給源＝
  確認なしの到達即エントリー（TREND_CONT lot の 61% が保有60分以内・N10 stoch_k が唯一の両窓再現✓）を両側から塞ぐ:
  ① v21_armed_dc_entry＝到達で武装（arm_ttl・range 消滅/uptrend で解除）し stoch(9,3) デッドクロス発生バーで建てる
     （タイミングシフト・RSI9 帯/武装期限/セル別要否は学習窓の層化合意 v21_band_consensus で選定・件数床=incumbent×V21_FREQ_KEEP）。
  ② v21_uptrend_fold＝uptrend 発火時の保有畳みを（発火時セル×含み損深さ）別に分岐＝fold（deadline shrink を期限へ前倒し
     ＝建値側へ縮む maker 逃げ・期限到達で TREND_CONT taker）／キー不在=即 taker（v20 と同じ・切迫側）。
  新 exit_reason なし（TP_FILLED/TREND_CONT 再利用・score.py 無変更 H13）。対照＝--v21-entry-only／--v21-fold-only。
  番人メタ確認＝--v21-guard-check（DC 全 False で入口0／fold 全 taker で v20 恒等 hash／labels 改ざん停止）。

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
import hashlib
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

# ── v14 Exit ポジション状態機械（acceptance 2026-07-07 承認・fixed-value-approved＝学習窓選定の候補メニュー・採点窓スイープでない）──
# 水準は全て進捗率（prog=(建値−価格)/(建値−レンジ中央)＝無次元・レンジ幾何で自動スケール・H6）またはバー数。
# None=その枝を使わない（OFF も選定値）。選定は _select_v14_params（学習窓のみ・枝×玉タイプ別の逐次 greedy・L-267）。
V14_BRANCH_PARAMS = {  # fixed-value-approved
    "dd":    (None, (0.50, 1/3), (0.50, 0.5), (0.75, 1/3), (0.75, 0.5)),  # 枝3 ピーク反転: (p_arm, r=ピークからの割戻し比)
    "be":    (None, 0.25, 0.50),                                           # 枝4 建値撤退: be_arm（進捗がこの水準に達したら建値フロアに buy trigger+limit）
    "stoch": (None, 0.25, 0.50),                                           # 枝5' 指標反転: s_arm（stoch(9,3) GC ∩ 含み益>0 ∩ peak_prog≥s_arm・taker）
    "stall": (None, (4, 0.25, 8), (6, 0.50, 8)),                           # 枝6 失速: (n本経過, 進捗<g, shrink残りT_eff へ前倒し)
    "tmax":  (6, 9, 12),                                                   # 枝7 backstop 長（30/45/60分・60分固定は未検証 a-priori だったため候補に降格）
}
V14_TYPES = ((1, False), (1, True), (2, False), (2, True))   # 玉の4タイプ＝(add数[1本目/追加], tp1_done[半分利確 前/後])

# ── v15 Entry×Exit セット最適化 第1弾＝逆行側分岐の作り直し＋枝水準の場面連動 学習窓選定（acceptance 2026-07-07 承認）──
# 候補は全てレンジ幾何比（W=上下ゾーン間の高さ・進捗率）＝無次元（H6）・fixed-value-approved（学習窓選定の候補格子・採点窓スイープでない L-267）。
# 選定＝場面セル（学習窓 lot の entry 特徴に LightGBM 1本の木を fit した leaf＝データ駆動の場面分割・手置きビンでない）×玉タイプ別に、
# 学習窓を purged 3分割（embargo 1日）した OOF 合意（合計純増 ∩ 2/3 セグメント改善）で採択（_select_v15_params）。
V15_UNIT_DIV = 2                     # add ラダー: UNIT/2=0.012 BTC/lot（合計 4×0.012=0.048 不変＝H1 の取り分を増やさない・H9: ≥0.0001/5USDT）
V15_MAX_LOTS = 4                     # fixed-value-approved 予算幾何 0.048÷0.012（同予算分割・まこさん 2026-07-07「add 増やす」の (a) 形）
V15_LADDER = (None, (0.5, 1.0), (0.4, 0.8, 1.2))   # fixed-value-approved 逆走ラダー段（初回建値からの逆走距離＝W 比・None=再発火 add のみ）
V15_SL_FAR = (0.5, 1.0, 1.5)         # fixed-value-approved 災害SL＝ゾーン上端＋k×W（遠い・浅SL の置換・レンジ幾何比）
V15_RET_ARM = (None, 0.25, 0.5, 1.0)  # fixed-value-approved 戻り決済 arm＝逆走の深さ（W 比）がこの水準に達した玉は建値フロア回帰で BE_EXIT（maker）
V15_TMAX = (12, 24, 48)              # fixed-value-approved backstop 長（1h/2h/4h・上限4h=まこさん指定 2026-07-07）
V15_DOWN = (None, 0.5, 0.25)         # fixed-value-approved 含み損玉の TIME 前倒し係数（V9 TIME_EXIT_DOWN 型・taker）
V15_BREAK_BARS = 12                  # 構造破れの複数TF確認＝ゾーン外終値の 1h 持続（12×5分・KB §5 a-priori・レンジ破れは E32b に譲る）
V15_BREAK_VOL_N = 20                 # 破れ判定の出来高窓（20期間平均・KB §5 a-priori）

# ── v16 Entry×Exit セット最適化 第2弾＝回帰救済×トレンドガード×候補格子の一括 OOF（acceptance 2026-07-07 承認）──
# 候補は全て fixed-value-approved の a-priori 格子（W 比・時間等分・業界標準比率）＝学習窓 OOF 選定の候補メニュー・採点窓スイープでない（L-267）。
# probe（scratchpad 5本）は「どのツマミを格子に載せるか」の方向付けのみ＝probe の数値は焼かない（acceptance ★疑似シミュ由来の固定値ゼロ）。
V16_GUARD = (("disp", 0.5), ("disp", 0.75), ("disp", 1.0), ("disp", 1.5), ("bb",))   # トレンド移行ガード＝変位 k×W_base／BB 幅拡大（コンフルエンス・None=OFF が既定）
V16_COOLDOWN = (6, 12)               # ガード発火後の新規/add veto 本数（30/60分・a-priori）
V16_BE_TIME = (None, 6, 12, 24)      # 時間 arm＝TP1 未達のまま {30,60,120}分 経過で建値フロア指値（BE_EXIT maker・acceptance (3)）
V16_RET_ARM = (None, 0.25, 0.5, 0.75, 1.0)   # 逆走 arm（W 比・V15_RET_ARM に 0.75 を追加＝acceptance (3)）
V16_TMAX_CELL = (12, 24, 36)         # セル×タイプ別 backstop 長候補（global 48 との差分・上限4h=まこさん指定）
V16_DOWN_CELL = (0.5, 0.75)          # セル×タイプ別 含み損 TIME 前倒し係数候補
# v27（fast-mode 2026-07-15・まこさん）: flat_up 型のピーク反転 建値保護（軌跡分析 §12＝flat_up SL負けは含み益+0.4%到達後に反転し −1.16% へ突き抜ける・勝ち玉とは早期区別不能だがピーク後の反転で分岐可）
V27_ARM_PCT  = 0.15   # 武装＝含み益ピークが建値から +0.15% 下に達したら（費用~5×・a-priori・SL負けは+0.40%到達／勝ちの早期dip −0.12% は武装前で無害）
V27_GIVEBACK = 0.5    # ピーク利益の 50% を戻したら MFE_DRAWDOWN_CUT(maker・登録済み)で確定（下限=建値フロア＝損ゼロ以上）
V16_LADDER = (None, (0.25,), (0.25, 0.5), (0.5, 1.0), (0.4, 0.8, 1.2))   # 逆走段 rung（W 比・浅い側 0.25/0.5 を追加＝acceptance (5)）
V16_TP1_F = (0.35, 0.65)             # TP1 位置比率 f×(entry−中央) の候補（0.5=現行・acceptance (6)）
V16_TP2_F = (0.75,)                  # TP2 位置比率の候補（1.0=中央=現行・acceptance (6)）
V16_SIZE0 = (0.5,)                   # セル別 新規初回 lot size 倍率候補（1.0=現行 0.012・0.5=0.006≥H9 最小・acceptance (8)）
V16_BREAK = (("anchor", 12), ("anchor", 24), (None, 24))   # 破れ計数（mode, 持続本数）: anchor=建玉基準（リセット穴の是正）・現行=(None,12)・短縮側は格子に入れない（acceptance (7)）
V16_CLUSTER_GAP = 12                 # クラスタ連結 gap（前 position 最終 exit から 12本=60分以内の新規を同一クラスタ・TTL/T_MAX 幾何の a-priori）
V16_NUM_LEAVES = 6                   # 場面セル木の分割数（候補{4,6}＝min_child_samples ガードでデータが縮退を決める・acceptance (9)）

# ── v17 選定の regime 頑健化（acceptance 2026-07-07 承認 b9a9c702・LEVER＝OOF 合意区間を時間3分割から帯層化へ）──
# 帯境界は precheck P3 の既存区切りの再利用＝成績で選ばない（acceptance ★疑似シミュ由来の固定値ゼロ (a)）。
V17_ATR_BAND_EDGES = (0.15, 0.20, 0.30, 0.40)   # fixed-value-approved entry 時 atr_pct の帯境界（a-priori・acceptance やること2）
V17_LOWVOL_BANDS = 2                 # 低ボラ側の帯数（atr_pct<0.2 の2帯＝層化合意 (ii) の合算対象・a-priori）
V17_BOXW_EXPAND = (1.5, 2.0)         # fixed-value-approved box_W 膨張ガード m×クラスタ初回幅（W 比幾何の格子・学習窓 OOF 選定・acceptance やること5）
V17_GUARD_GLOBAL = V16_GUARD + (("boxw", 1.5), ("boxw", 2.0))   # fixed-value-approved 全セル一律ガード候補（guard_global_v17・採否は層化 OOF・acceptance やること4）

# ── v18 TP2 反対側ゾーン（acceptance 2026-07-11 承認・伸びる玉は伸ばす・1レバー・既定 OFF=v17 恒等）──
# v17_031 の層化 OOF 採択2本（_select_v17_params の実エンジン選定値＝probe 値でない・sidecar v17_031_params.json 記録値）を
# 定数継承し、その上に TP2 置き位置の1レバーだけ載せる（選定 0 回＝学習窓チューニングを増やさない・ARC32 の確定を踏まえる）。
# TP2 の新しい置き位置＝サポートゾーン上端×(1+V11_SL_BUF)＝反対側ゾーンのすぐ手前（レンジ幾何 a-priori・バッファは SL と同一の既存定数）。
V18_FIXED_FROM_V17 = {
    "down_map": {(2, 2, True): 0.75},                   # v17_031 採択1: TIME 含み損前倒し（cell2・add2・TP1済み・V16_DOWN_CELL の候補値）
    "dd": {(4, 2, True): V14_BRANCH_PARAMS["dd"][1]},   # v17_031 採択2: ピーク反転 (0.50, 1/3)（cell4・add2・TP1済み・V14 候補メニューの参照）
}

# ── v21 入口の反転確認（armed DC）＋uptrend 畳み分岐（acceptance 2026-07-12 承認・LEVER＝Entry×Exit セット・既定 OFF=v20 恒等）──
# 候補は全て fixed-value-approved の離散メニュー＝学習窓の場面セル×purged 3分割 OOF＋ATR%帯層化合意が選ぶ（採点窓スイープでない L-267）。
# RSI9 帯＝まこさん指定「だいたい50以上」の近傍格子（どれを使うか・使わないかは学習窓選定）。時間格子＝既存 shrink/TIME の尺度（30/60/120分）。
V21_RSI_LO = (None, 45.0, 50.0, 55.0)   # fixed-value-approved 確認の RSI9 下限（None=RSI 条件なし＝DC のみ）
V21_ARM_TTL = (6, 12, 24)               # fixed-value-approved 到達→武装の有効本数（30/60/120分・range 消滅・uptrend で即解除）
V21_FOLD_M = (6, 12, 24)                # fixed-value-approved uptrend 発火後 maker 逃げの期限（本数・期限到達で TREND_CONT taker）
V21_FOLD_DEEP_W = 0.5                   # 発火時含み損の深い/浅いの境界（W 比の半分＝レンジ幾何 a-priori・畳み分岐キーの次元・スイープしない）
V21_FREQ_KEEP = 2.0 / 3.0               # 選定の件数床＝incumbent（v21 OFF）の学習窓 新規/日 に対する保持率（「エントリー数は極力減らさない」の運用定義）。
                                        # ⚠️初走 v21_035 の是正（2026-07-12）: 旧床は絶対値 4.33（v18 の採点窓実績）を学習窓の門に当てる窓取り違え＝
                                        # incumbent（学習窓 3.88/日）すら通らず全49候補が構造的に不採択。実測＝armed DC のタイミングシフトは
                                        # 学習窓新規 3.88→2.60/日（33%減）が下限＝保持率 2/3 は「DC のみ（RSI 帯なし＝件数最保全）」だけを通し
                                        # RSI 帯つき（≤2.17/日＝44%減超）を落とす水準。採点窓の件数・採否は precheck→score.py が別途判定（H8）。

# ── v22 レンジ中の戻り売り DC 入口×レンジ下限 TP＋ピーク反転畳み・前兆逃げ（acceptance 2026-07-13 承認・Entry×Exit セット・既定 OFF=v21_040 構成恒等）──
# 候補は全て fixed-value-approved の離散メニュー＝学習窓選定 v21_band_consensus（玉集合を動かす候補[入口/TPアンカー]は (iv) 不適用＝L-337）。
V22_FIXED_V21_ENTRY = {"rsi_lo": None, "arm_ttl": 6, "cells_off": ()}   # v21_037/040 採択の入口を定数継承（V18_FIXED_FROM_V17 と同型・選定で再回ししない）
V22_FIXED_V21_FOLD = {(5, False): 12}                                   # v21_037/040 採択の fold 分岐表を定数継承（同上）
# ── v24（acceptance 2026-07-16）: trend_caught 玉のピーク帯 resting maker 利確 ＋ v22 学習の定数化（入口〜出口すべて固定値・学習ゼロ）──
V24_TREND_TP_PCT = 0.08          # trend_caught 玉の resting maker 利確%（a-priori＝手数料床 SCALP_FLOOR ∩ MFE 較正基準[MFE中央値×60-70%] ∩ 学術 Leung&Li[深SL→浅TP]・スイープでない・L-267）
V24_FIXED_V22 = {"v22_anchor": {0: 24}}   # v22_042 採択値の定数継承（cell0/M24・v22 学習窓選定 _select_v22_params をスキップ＝入口〜出口すべて固定値・V22_FIXED_V21_* と同型・他 entry/pf/warn は None＝v22_042 採択どおり）
# ── v25（acceptance 2026-07-16）: レンジ判定 range_ok_rg5 の束ね幅をボラ連動にする（RG-v6・入口/件数/出口は v24 据え置き・1レバー）──
V25_K = 0.5                       # 束ね幅 tol=clamp(K×ATR%_1h,0.15%,0.6%) の倍率（幾何指標 diag＋まこさん視認校正で選定＝採点窓 net 不参照・L-267 非該当・build_regime_gate_rg._adaptive_tol_1h に渡す）
V22_ANCHOR_M = (24, 36, 48)     # fixed-value-approved TP アンカー＝レンジ下限（直近 M 本 low・2〜4h＝スキャル保有整合の幾何 a-priori）
V22_PF_K = (2.0, 3.0)           # fixed-value-approved ピーク畳みの武装＝含み益ピーク ≥ k×往復fee（手数料倍率 a-priori）
V22_PF_R = (0.3, 0.5)           # fixed-value-approved ピークからの戻し率 r（比率 a-priori）
V22_WARN_M = (6, 12, 24)        # fixed-value-approved 前兆中の shrink 前倒し期限（本数・v21 fold と同尺）

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


_MAKER_EXIT = ("TP_FILLED", "SL_FILLED", "TRAIL_EXIT", "EDGE_TP", "BE_EXIT", "PARTIAL_TP", "MFE_DRAWDOWN_CUT")   # score.py MAKER_EXIT_REASONS と完全同期（TRAIL_EXIT は e37 未使用だが将来 emit 時の taker 誤計上を防ぐため同期・2026-07-12／MFE_DRAWDOWN_CUT=v14 トレーリング指値 maker・2026-07-07）


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
        "entry_pos_frac": (round(float(pos["pos_frac"]), 3) if (pos.get("pos_frac") is not None and np.isfinite(pos.get("pos_frac", np.nan))) else None),   # v26 診断: 発火位置（0=下端サポート/1=上端レジスタンス）
        "mid_frac": (round(float(pos["mid_frac"]), 3) if (pos.get("mid_frac") is not None and np.isfinite(pos.get("mid_frac", np.nan))) else None),         # v26 診断: TP2=レンジ中央の帯内位置（entry_pos_frac と比較＝上/下半分の判定）
        "res_zone_pos": (round(float(pos["res_zone_pos"]), 3) if (pos.get("res_zone_pos") is not None and np.isfinite(pos.get("res_zone_pos", np.nan))) else None),   # v26 診断: レジスタンス帯内の発火位置（0=res_lo 下端/1=res_hi 頂点/<0=帯の下/>1=帯の上）
        "ceil_type": pos.get("ceil_type"),   # v26 診断: 入口型（down=下落系[天井=直近高値]／flat_up=平坦上昇系[天井=res_hi]）・net不関与・型別分析の見落とし防止 2026-07-15
        "entry_hour": int(entry_ts.hour), "entry_weekday": int(entry_ts.weekday()),
        "mfe_usd": round((pos["max_fav"] - lp) * lot_size * sdir, 4),
        "mae_usd": round((pos["max_adv"] - lp) * lot_size * sdir, 4),
        "gross_usd": round(gross, 4), "fee_usd": round(entry_fee + exit_fee + slip, 4), "net_usd": round(net, 4),
    }
    if pos.get("evt") is not None:                 # v6 のみ: イベント型（lever-bites 用・v5/OFF では列自体を出さない＝恒等）
        row["event_type"] = pos["evt"]
    trades.append(row)


# ══ ③ 両側スキャル売買エンジン（連続モード・サイドごと単一スロット・ゲート通過候補のみ）══
def _rsi9_v10(df: pd.DataFrame) -> pd.DataFrame:
    """RSI9（5分足スキャル設定・technical_kb §4）。当該足まで＝H2。分析用 rsi(14) とは別列。"""
    delta = df["close"].diff()
    up = delta.clip(lower=0).rolling(9).mean()
    dn = (-delta.clip(upper=0)).rolling(9).mean()
    df["rsi9"] = 100 - 100 / (1 + up / dn.replace(0, np.nan))
    return df


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


def _import_rg5():
    """v20: RG-v5（レンジ・レジーム判定の正本 scripts/dashboard/build_regime_gate_rg.py）を import 再利用。
    コピー禁止＝ロジックの正本は1箇所（まこさん視認校正3巡 2026-07-12 の判定と同一であることは
    labels_rg-v5 一致 selftest（--v20-selftest-rg5）が機械照合する）。"""
    dash = pathlib.Path(__file__).resolve().parents[1] / "dashboard"
    if str(dash) not in sys.path:
        sys.path.insert(0, str(dash))
    import build_regime_gate_rg as rgmod   # noqa: E402  モジュールは定数・関数定義のみ（main は __main__ ガード済み）
    return rgmod


def _rg5_frames(df: pd.DataFrame, adaptive_k=None):
    """v20: RG-v5 の 1h 帯と 5分判定（range/uptrend）を計算して返す（_apply_rg5_to_5m と selftest の共通実体）。
    未来値ゼロ（H2）＝1h/15分は確定バーのみ ffill・状態機械 rg5_uptrend_state は過去 close の逐次更新
    （RG 仕様欄「因果性」と同一・ロジックは build_regime_gate_rg.py を import 再利用＝コピー禁止）。
    adaptive_k=None（既定）＝RG-v5 固定束ね幅（v24 まで恒等）／指定時＝RG-v6 束ね幅ボラ連動（v25・
    tol=clamp(adaptive_k×ATR%_1h,0.15%,0.6%)＝_adaptive_tol_1h）＝平坦は帯が鋭く/高ボラでゾーンが立つ。"""
    rgmod = _import_rg5()
    d5 = df.set_index(pd.DatetimeIndex(df["ts"]))[["open", "high", "low", "close", "volume"]]
    _d1h = rgmod.v17._resample(d5, "1h")
    _tol = rgmod._adaptive_tol_1h(_d1h, adaptive_k) if adaptive_k is not None else None   # v25: RG-v6 適応束ね幅
    z1h = rgmod._zones_1h_rg(_d1h, tol_arr=_tol)
    idx5 = pd.DatetimeIndex(df["ts"])
    okz = z1h["zone_ok"].reindex(idx5, method="ffill").fillna(False).astype(bool).to_numpy()
    res_lo = z1h["res_lo"].reindex(idx5, method="ffill").to_numpy(float)
    res_hi = z1h["res_hi"].reindex(idx5, method="ffill").to_numpy(float)
    sup_lo = z1h["sup_lo"].reindex(idx5, method="ffill").to_numpy(float)
    sup_hi = z1h["sup_hi"].reindex(idx5, method="ffill").to_numpy(float)
    c = df["close"].to_numpy(float)
    brk = (c > res_hi) | (c < sup_lo)
    brk = np.where(np.isfinite(res_hi) & np.isfinite(sup_lo), brk, False)
    up = rgmod._uptrend_state_5m(d5)                   # rg5_uptrend_state＝上げトレンド状態機械（上げ専用・過去のみ）
    rng = okz & ~brk & ~up                             # range_ok_rg5（GATE_IDENT）＝帯あり ∩ 5分帯内 ∩ 非 uptrend
    return z1h, up, rng, res_lo, res_hi, sup_lo, sup_hi


def _apply_rg5_to_5m(df: pd.DataFrame, adaptive_k=None) -> pd.DataFrame:
    """v20: RG-v5（帯対拡張＋上げトレンド状態機械・視認校正3巡）で range_ok_rg5（GATE_IDENT）と
    rg5_uptrend を計算し、v11 エンジンの帯列へ供給する（acceptance 2026-07-12・実体は _rg5_frames）。
    adaptive_k 指定時＝RG-v6 束ね幅ボラ連動（v25・acceptance 2026-07-16）＝既定 None は RG-v5 恒等。"""
    _, up, rng, res_lo, res_hi, sup_lo, sup_hi = _rg5_frames(df, adaptive_k)
    df["rg5_uptrend"] = up
    df["range_ok_rg5"] = rng
    df["v11_res_lo"] = res_lo; df["v11_res_hi"] = res_hi
    df["v11_sup_lo"] = sup_lo; df["v11_sup_hi"] = sup_hi
    df["v11_mid"] = (res_lo + sup_hi) / 2.0
    df["range_ok_v11"] = rng                           # v11 エンジン・入口候補はこの列を読む（v20 では RG-v5 が正）
    return df


def v22_uptrend_warning(df: pd.DataFrame) -> pd.DataFrame:
    """v22_uptrend_warning（acceptance 2026-07-13）＝RG-v5 uptrend 状態機械の発火条件の半値水準の前兆フラグ。
    確定した 15分足のみ使用（当該 5分バーを含む形成中の 15分足は使わない）＋過去 close の rolling（shift(1)）＝H2。
    A15半: 直近2本の確定15分足が high/low とも切り上げ ／ D15半: 陽線2連続 ∩ 累積上昇 ≥+0.25%
    ／ C90半: close ≥ 直近90分（過去18本・当該バー除外）の最小 close × (1+0.5%)。いずれかで warning=True。
    用途＝条件情報のみ（shrink 前倒し・ピーク畳みのコンフルエンス）。新規停止は uptrend 発火（現行）だけが担う。"""
    p15 = df["ts"].dt.floor("15min")
    g = df.groupby(p15)
    o15 = g["open"].first(); h15 = g["high"].max(); l15 = g["low"].min(); c15 = g["close"].last()
    a15 = (h15 > h15.shift(1)) & (l15 > l15.shift(1))                                  # A15半（確定バー k vs k-1 の切り上げ）
    d15 = (c15 > o15) & (c15.shift(1) > o15.shift(1)) & (c15 / o15.shift(1) - 1.0 >= 0.0025)   # D15半（陽線2連続∩累積+0.25%）
    w15 = (a15 | d15)
    last_conf = p15 - pd.Timedelta(minutes=15)         # 各5分バーから見た「最後に確定した」15分足（形成中は使わない＝H2）
    w_struct = w15.reindex(last_conf).fillna(False).to_numpy(bool)
    c90min = df["close"].rolling(18).min().shift(1).to_numpy(float)                     # 直近90分の最小 close（当該バー除外）
    w_c90 = df["close"].to_numpy(float) >= c90min * 1.005                               # C90半（+0.5%・NaN 比較は False）
    df["v22_warning"] = w_struct | w_c90
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


def v11_entry_candidates(df: pd.DataFrame, v11_open_entry: bool = False, v12_open_range: bool = False, upper_touch: bool = False) -> np.ndarray:
    """v11 入口候補（KB §3＝到達＋拒否確認・v10 の実証部品を維持）＝
    range_ok_v11 ∩ 上限ゾーン接触（high≥ゾーン下端）∩ 陰転 ∩ RSI9 買われすぎ反転。
    v11_open_entry=True（--v11-open-entry・Step1 Do・acceptance 2026-07-05）＝過熱を必須にする確認（rsi9_prev>70）を
    撤去し、反転確認（陰転∩RSI9下向き）だけで入る＝過熱 fade で負ける方向選別をやめ非過熱の反落も取り件数を戻す
    （probe: 最終入口 stoch_k 高側82%＝過熱に偏る／KB §6.6 過熱fadeは統計的根拠なし・N10 過熱ほど負け）。既定 False=v11 恒等。"""
    h = df["high"].to_numpy(float); c = df["close"].to_numpy(float); o = df["open"].to_numpy(float)
    rsi9 = df["rsi9"].to_numpy(float); rsi9_prev = np.roll(rsi9, 1); rsi9_prev[0] = np.nan
    ok = df["range_ok_v11"].to_numpy(bool)
    # v19_upper_touch: 到達を帯の下端 res_lo から帯の上端 res_hi（本当のレジスタンス）へ＝上端まで上がる逆行を抱えず入る（acceptance 2026-07-12・既定 False=v18 恒等）
    _edge = df["v11_res_hi"].to_numpy(float) if upper_touch else df["v11_res_lo"].to_numpy(float)
    touched = np.isfinite(_edge) & (h >= _edge)
    rev = (c < o) & np.isfinite(rsi9) & np.isfinite(rsi9_prev) & (rsi9 < rsi9_prev)   # 反転確認（陰転∩RSI9下向き・不変）
    rejected = rev if v11_open_entry else (rev & (rsi9_prev > 70.0))                  # open_entry=過熱の必須化を撤去／False=v11 恒等
    if v12_open_range:                                                                # v12=レンジ上部で確認なし（拒否確認 rev を要求しない・acceptance 2026-07-06）
        return ok & touched                                                          # range_ok_v11 ∩ 上限ゾーンのみで SHORT＝薄利多売（方向選別しない・Exit は次段）
    return ok & touched & rejected


def v14_exit_machine(lot, o_i, h_i, c_i, gc_i, params):
    """v14 Exit 状態機械 枝3/4/5'（TP2 の後・v13 shrink の前に判定・acceptance 2026-07-07）。
    トリガ判定は前バーまでの含み益ピーク lot["pk_prev"]（判定バー自身の値動きを使わない＝同一バー楽観の排除＝H2）。
    ⚠️ pk_prev の初期値は fill バーの安値（約定前のバー内値動きを含む近似・バー内順序は不可知）＝
    「fill バー直後は建値＝進捗0」ではない（旧 docstring の記述誤り・2026-07-12 是正・挙動は従来どおり不変）。
    戻り: (exit_reason, exit_px) または None。パラメータは玉のタイプ (add数, tp1_done) 別（V9 の型別条件の E37 版）。
    枝3 MFE_DRAWDOWN_CUT＝ピーク基準トレーリング buy trigger+limit（maker・下限=建値フロア＝損ゼロ以上・⑦）
    枝4 BE_EXIT＝建値フロアに buy trigger+limit（maker・利益消失の事実で損ゼロ級撤退）
    枝5' STOCH_REVERSE_EXIT＝stoch(9,3) GC ∩ 含み益>0 ∩ peak_prog≥s_arm（成行 taker・V9 P23 実績の E37 版）
    レベル系の gap は SL と同規約（max(level, open)＝悲観側）。"""
    den = lot["avg"] - lot["tp2"]
    if den <= 0:
        return None                                    # 防御（tp_ge_sl_check_v11 が原則排除済み）
    pk = lot.get("pk_prev", lot["avg"])                # 前バーまでのピーク価格（SHORT＝低いほど利益・初期値=fill バー安値＝約定前のバー内値動きを含む近似）
    peak_prog = (lot["avg"] - pk) / den
    typ = (min(int(lot["add_count"]), 2), bool(lot["tp1_done"]))
    if "cell" in lot:                                  # v15: 場面セル（LightGBM 木の leaf）×玉タイプでキー（acceptance 2026-07-07）
        typ = (lot["cell"], typ[0], typ[1])
    be_floor = lot["avg"] * (1.0 - SCALP_FLOOR)        # 建値フロア＝手数料床（v13 と同形・損ゼロ以上）
    dd = params["dd"].get(typ)
    if dd is not None and peak_prog >= dd[0]:          # 枝3: armed（進捗ピーク≥p_arm）∩ ピークから r 割戻しレベルへ回帰
        lvl = min(pk + (lot["avg"] - pk) * dd[1], be_floor)
        if h_i >= lvl:
            return ("MFE_DRAWDOWN_CUT", max(lvl, o_i))
    be = params["be"].get(typ)
    if be is not None and peak_prog >= be and h_i >= be_floor:   # 枝4: armed ∩ 建値へ回帰
        return ("BE_EXIT", max(be_floor, o_i))
    st = params["stoch"].get(typ)
    if st is not None and peak_prog >= st and gc_i and c_i < lot["avg"]:   # 枝5': armed ∩ GC ∩ 含み益>0（close 時点）
        return ("STOCH_REVERSE_EXIT", c_i)
    return None


def tp_floor_check_v15(limit: float, tp1_px: float, tp2_px: float) -> bool:
    """v15 の建て条件＝TP1 幅 ≥ 手数料床（⑦）∩ TP2 幅 > 0。
    旧 tp_ge_sl_check_v11 の「TP2幅 ≥ SL幅」は浅SL設計の物理条件＝v15 は SL を災害水準（遠い）へ置換し、
    リスク管理は構造破れ枝＋戻り決済が担う（acceptance 2026-07-07）ため SL 幅条件は課さない。"""
    tp1_w = limit - tp1_px
    tp2_w = limit - tp2_px
    return bool(np.isfinite(tp1_w) and np.isfinite(tp2_w) and tp2_w > 0 and tp1_w >= limit * SCALP_FLOOR)


def range_break_check_v15(c_i: float, ok_i: bool, ztop: float, vol_i: float, vol_sma_i: float,
                          brk_cnt: int, brk_vol: bool, break_bars: int) -> tuple[int, bool, bool]:
    """v15 構造破れ判定（KB §5＝①出来高>20期間平均 ②境界外終値 ③複数TF確認=1h 持続・acceptance 2026-07-07）。
    ゾーン外終値（c>ゾーン上端 ∩ range_ok 消失）が break_bars 本連続 ∩ 期間中に出来高スパイクが1回以上 → 発火。
    戻り: (新カウンタ, 新出来高フラグ, 発火するか)。入力は当該バーの確定値のみ（H2）。"""
    if np.isfinite(ztop) and c_i > ztop and (not ok_i):
        brk_cnt += 1
        if np.isfinite(vol_sma_i) and vol_i > vol_sma_i:
            brk_vol = True
    else:
        brk_cnt = 0
        brk_vol = False
    return brk_cnt, brk_vol, bool(brk_cnt >= break_bars and brk_vol)


def cluster_guard_check_v16(c_i: float, base_px: float, base_w: float, guard, bb_sig_i: bool) -> bool:
    """v16 トレンド移行ガード（acceptance 2026-07-07 (2)）＝クラスタ基準からの上放れを動的サインで検知。
    guard=("disp", k)＝変位 k×W_base（クラスタ初回 entry 基準＝ゾーンごとに切り上がらない・階段急騰を貫通して見る）／
    ("bb",)＝BB 幅拡大コンフルエンス（BBW>rolling288 q90 ∩ 終値>2σ上 ∩ 出来高>20期間平均・_attach_v16_bb で前計算）。
    発火＝保有全 lot を TREND_CONT（taker・score.py 登録済み再利用）で離脱し新規/add をクールダウン。入力は当該バー確定値のみ（H2）。"""
    if guard is None:
        return False
    if guard[0] == "disp":
        return bool(np.isfinite(base_px) and np.isfinite(base_w) and base_w > 0
                    and c_i >= base_px + float(guard[1]) * base_w)
    return bool(bb_sig_i)


def boxw_expand_guard_v17(w_now: float, base_w: float, m: float) -> bool:
    """v17 box_W 膨張ガード（acceptance 2026-07-07 やること5）＝クラスタ初回 entry 時の box_W（px）を基準に、
    現在のゾーン幅が m 倍以上へ膨張＝ゾーン再基準化（階段急騰で box が広がり直す 12/02 実測 0.53 から 4.39 の型）を
    トレンド移行と判定。発火の扱いは既存ガードと同じ（全 lot TREND_CONT taker＋クールダウン・score.py 無変更 H13）。
    入力は当該バーの確定値のみ（H2）。"""
    return bool(np.isfinite(w_now) and np.isfinite(base_w) and base_w > 0 and w_now >= float(m) * base_w)


def guard_fire_v17(c_i: float, base_px: float, base_w: float, guard, bb_sig_i: bool, w_now: float) -> bool:
    """v17 ガード発火判定＝disp/bb は v16 と同一（cluster_guard_check_v16 へ委譲＝恒等）・boxw のみ新分岐。
    v16 経路は boxw ガードを持たない＝挙動不変（OFF 恒等）。"""
    if guard is None:
        return False
    if guard[0] == "boxw":
        return boxw_expand_guard_v17(w_now, base_w, guard[1])
    return cluster_guard_check_v16(c_i, base_px, base_w, guard, bb_sig_i)


def guard_global_v17(p: dict | None):
    """v17 全セル一律ガード（acceptance 2026-07-07 やること4）＝セル別 guard map より優先して適用する global 候補。
    v16 以前の params は本キーを持たない＝None（恒等）。採否（global かセル別か）は層化 OOF（_select_v17_params）が決める。"""
    return (p or {}).get("guard_all")


def be_time_arm_v16(lot, i: int, bt) -> bool:
    """v16 時間 arm（acceptance 2026-07-07 (3)）＝TP1 未達のまま bt 本経過で建値フロア指値（BE_EXIT maker）を arm。"""
    return bool(bt is not None and (not lot["tp1_done"]) and (i - lot["first_idx"]) >= int(bt))


def tmax_scene_v16(lot, tmax_map, default_tmax: int) -> int:
    """v16 TIME の場面連動（acceptance 2026-07-07 (4)）＝backstop 長をセル×タイプ別 map から引く（無ければ global）。"""
    if not tmax_map:
        return int(default_tmax)
    key = (lot.get("cell", 0), min(int(lot["add_count"]), 2), bool(lot["tp1_done"]))
    return int(tmax_map.get(key, default_tmax))


def _attach_v16_bb(df: pd.DataFrame) -> pd.DataFrame:
    """v16 BB 拡大サインの前計算（BBW=(上−下)/中央×100＝LuxAlgo 式・分位/出来高平均は shift(1)＝過去のみ H2）。
    列 v16_bb_sig（bool）を付与。v15 以前の経路はこの列を読まない＝恒等に不干渉。"""
    c = df["close"].astype(float)
    v = df["volume"].astype(float)
    mid20 = c.rolling(20).mean()
    sd20 = c.rolling(20).std()
    upper = mid20 + 2.0 * sd20
    bbw = 4.0 * sd20 / mid20 * 100.0
    q90 = bbw.rolling(288).quantile(0.9).shift(1)
    vs = v.rolling(V15_BREAK_VOL_N).mean().shift(1)
    sig = (bbw > q90) & (c > upper) & (v > vs)
    df = df.copy()
    df["v16_bb_sig"] = sig.fillna(False).to_numpy(bool)
    return df


def run_continuous_v11(df, box_tf, no_add: bool = False, single_tp: bool = False, v11_open_entry: bool = False, v12_open_range: bool = False, v13_time_maker: bool = False, v14_params: dict | None = None, v15_params: dict | None = None, v19_upper_touch: bool = False, v20_uptrend: np.ndarray | None = None):
    """v11 エンジン＝素ルール SHORT 専用（short_only_v11・LONG 入口の生成経路なし＝§1.2.1 ショートのみ）。
    入口: v11_entry_candidates → 指値 maker TTL（不約定は建てない）。TP/SL は発注時点のゾーン幾何で固定・
    tp_ge_sl_check_v11 を通らない候補は建てない。
    出口（lot ごと・SL 優先＝eval_engine と同順）: SL=ゾーン上端×(1+V11_SL_BUF)（maker・gap 反映・全量）
      → TP1=(建値+中央)/2 で半分（PARTIAL_TP・maker）→ TP2=中央で残り（TP_FILLED・maker）
      → TIME=T_MAX 60分 backstop（taker）。
    v13_time_maker=True（--v13-time-maker・Step2・acceptance 2026-07-06）＝TP2 と TIME backstop の間に
    「deadline 型 縮む maker TP」を置く＝残り時間比 r（fill時 r=1＝tp2 通常／deadline で r→0＝建値フロア）で
    TP を建値側へ縮め、到達した玉を成行 taker でなく maker 指値（TP_FILLED）で取り切る（E35 iter8-9 型・arxiv
    1707.03498/1604.04963）。建値フロア＝avg×(1−SCALP_FLOOR)＝手数料床を割る決済は建てない（⑦・損ゼロ以上）。
    縮む TP に当たらなかった玉のみ 60分で成行 TIME_EXIT（taker・backstop）。既定 False=v12 恒等。
    add: 保有中に入口条件の完全再発火で同量 UNIT を追加（最大 V11_MAX_ADDS lot＝レンジの上限ゾーン再テストで
    小刻みに売り増して複数TP で刻む＝KB §6.5 V9型・Bitget 同サイド merge＋複数TP の写像・トレンド型ピラミッド不採用）。
    全て約定 bar の次以降＝leak-safe（H2）。"""
    short_only_v11 = True                              # SIDE_IDENT（LONG 入口の生成経路なし）
    n = len(df)
    ts = df["ts"].to_numpy()
    o = df["open"].to_numpy(float); h = df["high"].to_numpy(float)
    l = df["low"].to_numpy(float); c = df["close"].to_numpy(float)
    atr = df["atr"].to_numpy(float); adx = df["adx"].to_numpy(float); kk = df["stoch_k"].to_numpy(float)
    cand = v11_entry_candidates(df, v11_open_entry=v11_open_entry, v12_open_range=v12_open_range, upper_touch=v19_upper_touch)
    rz_lo = df["v11_res_lo"].to_numpy(float); rz_hi = df["v11_res_hi"].to_numpy(float)
    sz_hi = df["v11_sup_hi"].to_numpy(float); mid = df["v11_mid"].to_numpy(float)
    max_lots = 1 if no_add else V11_MAX_ADDS
    tmax_l = T_MAX                                     # backstop 長（v14 では選定値・OFF では既存 T_MAX と同値＝恒等）
    v15 = v15_params is not None
    unit = UNIT
    vol_arr = vol_sma_prev = ok_arr = cell_fn = None
    tp2_far = False                                    # v18: TP2 反対側ゾーン（v15_params 経由・既定 False=恒等）
    if v15:                                            # v15 Entry×Exit セット（acceptance 2026-07-07・既定 OFF=v14 恒等＝この block ごとスキップ）
        unit = UNIT / V15_UNIT_DIV                     # 0.012 BTC/lot × 最大4段＝合計 0.048 不変（同予算分割・H1/H9）
        max_lots = V15_MAX_LOTS
        tmax_l = int(v15_params.get("tmax", 48))
        _vs = df["volume"].astype(float)
        vol_arr = _vs.to_numpy(float)
        vol_sma_prev = _vs.rolling(V15_BREAK_VOL_N).mean().shift(1).to_numpy(float)   # 過去20本平均（当該バー除外＝H2）
        ok_arr = df["range_ok_v11"].to_numpy(bool)
        cell_fn = v15_params.get("cell_fn") or (lambda k_, a_, w_: 0)
        v15_params["_stats"] = {"ladder_fills": 0, "BE_EXIT_ret": 0, "RANGE_BREAK_EXIT": 0,
                                "MFE_DRAWDOWN_CUT": 0, "down_time": 0}
        tp2_far = bool(v15_params.get("tp2_far"))      # v18: TP2 反対側ゾーン（acceptance 2026-07-11・キー無し=恒等）
        if tp2_far:
            v15_params["_stats"]["tp2_far_applied"] = 0
            v15_params["_stats"]["tp2_far_fallback"] = 0
        v15_machine = {"dd": v15_params.get("dd", {}) or {}, "be": {}, "stoch": {}, "stall": {}}
        brk_bars_req = int(v15_params.get("break_bars", V15_BREAK_BARS))
        rungs = []; rung_next = 0; brk_cnt = 0; brk_vol = False
    v16 = bool(v15 and v15_params.get("v16"))
    if v16:                                            # v16 Entry×Exit セット第2弾（acceptance 2026-07-07・既定 OFF=v15 恒等＝この block ごとスキップ）
        bb_sig = df["v16_bb_sig"].to_numpy(bool) if "v16_bb_sig" in df.columns else np.zeros(n, bool)
        guard_map = v15_params.get("guard", {}) or {}
        guard_all = guard_global_v17(v15_params)       # v17 全セル一律候補（v16 以前はキー無し=None＝恒等・acceptance v17 やること4）
        cooldown = int(v15_params.get("cooldown", V16_COOLDOWN[0]))
        be_time_map = v15_params.get("be_time", {}) or {}
        tmax_map = v15_params.get("tmax_map", {}) or {}
        down_map = v15_params.get("down_map", {}) or {}
        tp1_fmap = v15_params.get("tp1_f", {}) or {}
        tp2_fmap = v15_params.get("tp2_f", {}) or {}
        size0_map = v15_params.get("size0", {}) or {}
        brk_anchor = v15_params.get("break_mode") == "anchor"
        cool_until = -1                                # ガード発火後の新規/add veto（クールダウン）
        clu_base = float("nan"); clu_w = float("nan"); clu_cell = 0   # クラスタ基準（初回 entry・階段急騰を貫通して見る）
        last_exit_i = -10 ** 9
        v15_params["_stats"]["TREND_CONT"] = 0
    v21e = v15_params.get("v21_entry") if v15 else None    # v21 入口の反転確認 armed DC（acceptance 2026-07-12・None=v20 恒等）
    v21f = v15_params.get("v21_fold") if v15 else None     # v21 uptrend 畳み分岐（None=v20 恒等＝即 taker 1択）
    dc21 = rsi9_21 = None
    armed21 = -1                                       # v21_armed_dc_entry: 到達で武装（arm_ttl 本）・DC 発生バーで建てる（-1=非武装）
    if v21e is not None:
        assert v20_uptrend is not None, "v21 は v20（RG-v5）構成の上に載る（acceptance 2026-07-12）"
        _cs21 = pd.Series(c); _ls21 = pd.Series(l); _hs21 = pd.Series(h)
        _ll21 = _ls21.rolling(9).min(); _hh21 = _hs21.rolling(9).max()
        _k21 = (100.0 * (_cs21 - _ll21) / (_hh21 - _ll21).replace(0, np.nan)).rolling(3).mean()
        _d21 = _k21.rolling(3).mean()
        dc21 = ((_k21.shift(1) >= _d21.shift(1)) & (_k21 < _d21)).fillna(False).to_numpy(bool)   # stoch(9,3) デッドクロス発生（v14 と同式・過去 rolling のみ＝H2）
        if bool(v21e.get("_dc_force_off")):            # 番人専用の差し替え口（--v21-guard-check＝DC 全 False で v21 入口 0 の配線証明）
            dc21[:] = False
        rsi9_21 = df["rsi9"].to_numpy(float)
        v15_params["_stats"].setdefault("v21_entry_fires", 0)
    if v21f is not None:
        v15_params["_stats"].setdefault("v21_fold_armed", 0)
        v15_params["_stats"].setdefault("v21_fold_expire", 0)
        v15_params["_stats"].setdefault("v21_fold_taker", 0)
    v22e = v15_params.get("v22_entry") if v15 else None    # v22_range_dc_entry（acceptance 2026-07-13・None=v21 恒等）
    v22a = v15_params.get("v22_anchor") if v15 else None   # v22_low_anchor_tp（cell→M・None/キー無し=現行アンカー恒等）
    v22p = v15_params.get("v22_pf") if v15 else None       # v22_peak_fold（k,r,warn_only・None=恒等）
    v22w = v15_params.get("v22_warn") if v15 else None     # v22_uptrend_warning の shrink 前倒し（M 本・None=恒等）
    v23te = bool(v15_params.get("v23_trend_exit")) if v15 else False   # v23（acceptance 2026-07-15）: uptrend 発火の成行投げを廃止し V9 型状態機械へ
    v24tm = bool(v15_params.get("v24_trend_maker_tp")) if v15 else False   # v24（acceptance 2026-07-16）: trend_caught 玉のピーク帯 resting maker 利確（反転待ち STOCH_REVERSE を置換・全固定値）
    v26g = float(v15_params.get("v26_atr_gate")) if (v15 and v15_params.get("v26_atr_gate") is not None) else None   # v26（fast-mode 2026-07-15）: 入口 atr_pct 固定下限＝低ボラ薄利を建てず TP幅ある高ボラ場面に寄せる（None=恒等・建て時点 atr[i]/c[i]＝H2）
    v26tf = float(v15_params.get("v26_touch_frac")) if (v15 and v15_params.get("v26_touch_frac") is not None) else None   # v26（fast-mode 2026-07-15・まこさん）: 天井で売る＝直近レンジの上端寄り pos>=F でだけ建てる（急落後も直近レンジは価格に追従＝張り付いた古いレジを使わない）
    _hh26 = _ll26 = _rng26f = None
    if v26tf is not None:
        _mbar26 = max(2, int(round(float(v15_params.get("v26_touch_hours", 12.0)) * 12)))   # 直近レンジの窓（時間→5分バー）
        _hh26 = pd.Series(h).rolling(_mbar26, min_periods=2).max().to_numpy(float)           # 直近高値（h[i] は当該バー確定＝H2）
        _ll26 = pd.Series(l).rolling(_mbar26, min_periods=2).min().to_numpy(float)           # 直近安値
        _rng26f = _hh26 - _ll26
        o26 = df["open"].to_numpy(float)                                                     # 陰転（反転）判定用
    v26sp = bool(v15_params.get("v26_split")) if v15 else False                              # v26（fast-mode・まこさん）: 下落系/平坦系でレンジ入口を切り分け＝天井に売り指値を置いて待つ
    v26ue = bool(v15_params.get("v26_uptrend_exit")) if v15 else False                       # v26 B（まこさん 2026-07-15）: uptrend レジーム発火で保有玉を緊急離脱（成行）＝上昇に巻き込まれ時間切れ大損する前に損害頭打ち
    v27fl = bool(v15_params.get("v27_flatup_lock")) if v15 else False                        # v27（fast-mode 2026-07-15・まこさん）: flat_up 型のピーク反転 建値保護（§12・MFE_DRAWDOWN_CUT maker 再利用）
    _rhdn26 = None; _gap26 = 0.0; _v26ceil = np.nan; _ceil_type26 = None   # _ceil_type26=入口型マーカー（診断・net不関与・型別分析の見落とし防止 2026-07-15）
    if v26sp:
        _gap26 = float(v15_params.get("v26_gap", 0.5)) / 100.0                                # 下落系判定＝価格がレジ帯下端より _gap% 以上下（レジが急落前に張り付き）
        _mdn26 = max(2, int(round(float(v15_params.get("v26_down_hours", 6.0)) * 12)))        # 下落系の天井＝直近高値の窓（急落除外の短窓・時間→5分バー）
        _rhdn26 = pd.Series(h).rolling(_mdn26, min_periods=2).max().shift(1).to_numpy(float)  # 直近高値（前バーまで＝H2・当該バーが新高値で約定）
        _maxage26 = float(v15_params.get("v26_max_age_hours", 0.0))                           # A: レンジ判定直後に入る＝range_ok が立ってからの経過がこの時間内のみ建てる（0=制限なし）
        _cbuf26 = float(v15_params.get("v26_ceil_buffer", 0.0)) / 100.0                        # v26 天井バッファ: 売り指値を天井×(1-buffer)へ下げる（上端手前で止まるレンジを拾う・0=恒等・まこさん 2026-07-15）
        if _maxage26 > 0:
            _idxn = np.arange(n); _fi = np.where(~ok_arr, _idxn, -1)                          # range_ok 連続バー数（立ってからの経過・まこさん 2026-07-15）
            _age26 = (_idxn - np.maximum.accumulate(_fi)).astype(float)
        else:
            _age26 = None
    if v23te:                                              # v23: ピーク畳み(trailing=MFE_DRAWDOWN_CUT)は不使用（両窓符号反転で勝ち玉を切る・L-341）
        v22p = None
        v15_params["_stats"].setdefault("v23_trend_caught", 0)
        v15_params["_stats"].setdefault("STOCH_REVERSE_EXIT", 0)
        v15_params["_stats"].setdefault("MFE_STALE_CUT", 0)
    if v24tm:                                              # v24: TREND_CAUGHT_TP（resting maker 利確）のカウンタ
        v15_params["_stats"].setdefault("TREND_CAUGHT_TP", 0)
    V23_RT_FEE = 2.0 * ee.MAKER_FEE                         # 往復 maker fee（含み益ピークが費用を超えたかの目安・a-priori）
    V23_STALE_MIN = 30                                     # V9 §9.2 MFE_STALE の保有分（a-priori・分）
    warn22 = (df["v22_warning"].to_numpy(bool)
              if (v15 and "v22_warning" in df.columns and (v22p is not None or v22w is not None)) else None)
    low22 = {}
    if v22a:
        _ls22 = pd.Series(l)
        for _m in sorted({int(x) for x in v22a.values() if x is not None}):
            low22[_m] = _ls22.rolling(_m).min().shift(1).to_numpy(float)   # レンジ下限＝直近 M 本 low（当該バー除外＝H2）
        v15_params["_stats"].setdefault("v22_anchor_applied", 0)
        v15_params["_stats"].setdefault("v22_anchor_fallback", 0)
    if v22p is not None:
        v15_params["_stats"].setdefault("MFE_DRAWDOWN_CUT_pf", 0)
    if v22e is not None:
        assert dc21 is not None and rsi9_21 is not None, "v22 入口は v21 構成（DC/RSI9 配列）の上に載る（acceptance 2026-07-13）"
        v15_params["_stats"].setdefault("v22_entry_fires", 0)
    k9 = d9 = None
    if v14_params is not None or v23te:                # v14/v23: stoch(9,3)（v14 枝5'／v23 STOCH_REVERSE_EXIT 用・過去 rolling のみ＝leak-safe H2・OFF 経路では計算しない）
        _cs = pd.Series(c); _ls = pd.Series(l); _hs = pd.Series(h)
        _ll9 = _ls.rolling(9).min(); _hh9 = _hs.rolling(9).max()
        k9 = (100.0 * (_cs - _ll9) / (_hh9 - _ll9).replace(0, np.nan)).rolling(3).mean().to_numpy(float)
        d9 = pd.Series(k9).rolling(3).mean().to_numpy(float)
    if v14_params is not None:                         # v14 のみ: tmax／stats 初期化
        tmax_l = int(v14_params.get("tmax", T_MAX))
        v14_params.setdefault("_stats", {})
        v14_params["_stats"] = {"MFE_DRAWDOWN_CUT": 0, "BE_EXIT": 0, "STOCH_REVERSE_EXIT": 0, "stall_early": 0, "tp2_bothhit": 0}
    trades = []
    lots = []                                          # 保有中 lot（同サイド merge＝単一 SHORT ポジの写像・最大 max_lots）
    pend = None
    for i in range(n):
        if pend is not None:
            el = i - pend["placed_idx"]
            if el > TTL:
                pend = None
            elif el >= 1 and h[i] >= pend["limit"]:
                _rng26 = (rz_hi[i] - sz_hi[i]) if (np.isfinite(rz_hi[i]) and np.isfinite(sz_hi[i])) else np.nan   # v26 診断: レンジ帯内の発火位置（0=下端サポート・1=上端レジスタンス）＝下端発火の一次確認
                _lot = {"side": "SHORT", "avg": pend["limit"], "size": unit,
                        "add_count": len(lots) + 1, "first_idx": i, "last_fill_idx": i,
                        "atr_entry": atr[i], "adx_entry": adx[i], "k_entry": kk[i],
                        "W_entry": pend["W_pct"], "max_fav": l[i], "max_adv": h[i],
                        "pos_frac": ((pend["limit"] - sz_hi[i]) / _rng26) if (np.isfinite(_rng26) and _rng26 > 0) else np.nan,
                        "mid_frac": ((mid[i] - sz_hi[i]) / _rng26) if (np.isfinite(_rng26) and _rng26 > 0) else np.nan,
                        "res_zone_pos": (((pend["limit"] - rz_lo[i]) / (rz_hi[i] - rz_lo[i])) if (np.isfinite(rz_lo[i]) and np.isfinite(rz_hi[i]) and rz_hi[i] > rz_lo[i]) else np.nan),
                        "ceil_type": pend.get("ceil_type"),
                        "tp1": pend["tp1"], "tp2": pend["tp2"], "sl": pend["sl"], "tp1_done": False}
                if v15:
                    _lot["zone_top"] = pend["zone_top"]; _lot["w_px"] = pend["w_px"]
                    _lot["cell"] = int(cell_fn(kk[i], atr[i] / max(c[i], 1e-9) * 100.0, pend["W_pct"]))
                    if v16:
                        _lot["size"] = unit * float(pend.get("size_mult", 1.0))   # セル別 新規 size 配分（acceptance (8)・減らす側のみ＝cap 不変）
                    if not lots:                       # position 開始＝逆走ラダーを敷く（初回建値+k×W の resting maker 売り指値）
                        lad = v15_params.get("ladder")
                        rungs = [pend["limit"] + kf * pend["w_px"] for kf in lad] if lad else []
                        rung_next = 0; brk_cnt = 0; brk_vol = False
                        if v16 and (not np.isfinite(clu_base) or (i - last_exit_i) > V16_CLUSTER_GAP):
                            clu_base = pend["limit"]; clu_w = pend["w_px"]; clu_cell = _lot["cell"]   # クラスタ更新（gap 超え＝新クラスタ）
                lots.append(_lot)
                pend = None
        if v20_uptrend is not None and v20_uptrend[i]:   # v20 regime exit（acceptance 2026-07-12）: RG-v5 の上げトレンド発火＝レンジ前提の終了
            pend = None                                    # 未約定の指値は取り下げ＝uptrend 中は新規/add を建てない（risk-manager 型）
            armed21 = -1                                   # v21: uptrend 中は armed DC 入口も封鎖（v21e None 時は無害）
            if v26ue and lots:                             # v26 B（まこさん 2026-07-15）: uptrend 発火で保有玉を緊急離脱（成行 TREND_CONT）＝trend_caught 保持で時間切れ大損する前に頭打ち（v23/v24 の保持より優先）
                for lot in lots:
                    _record(trades, lot, c[i], "TREND_CONT", i, ts)
                    if v15_params is not None:
                        _st = v15_params["_stats"]
                        _st["TREND_CONT_rg5"] = _st.get("TREND_CONT_rg5", 0) + 1
                        _kk = "TREND_CONT_rg5_win$" if trades[-1]["net_usd"] > 0 else "TREND_CONT_rg5_loss$"
                        _st[_kk] = round(_st.get(_kk, 0.0) + trades[-1]["net_usd"], 2)
                lots = []
            elif v23te and lots:                           # v23（acceptance 2026-07-15）: 成行投げ(TREND_CONT 即taker)せず全 lot を trend_caught として保持＝下の Exit 状態機械（STOCH_REVERSE/MFE_STALE/災害SL/TIME）へ委ねる
                for lot in lots:
                    if not lot.get("trend_caught"):
                        lot["trend_caught"] = True
                        v15_params["_stats"]["v23_trend_caught"] += 1
                # lots は keep・新規は pend=None で停止＝この後 Exit ループへフォールスルー（ladder は uptrend 中 ok_arr=False で不発）
            elif lots:
                _keep20 = []
                for lot in lots:
                    if v21f is not None and "fold_dl" in lot:
                        _keep20.append(lot); continue      # v21_uptrend_fold: fold 継続中（発火継続バー）＝期限まで maker 逃げ続行
                    _dec21 = None
                    if v21f is not None and lot.get("w_px"):   # v21 畳み分岐（acceptance 2026-07-12）: 発火時の場面セル×含み損深さで fold/即taker（学習窓選定）
                        _ci21f = int(cell_fn(kk[i], atr[i] / max(c[i], 1e-9) * 100.0, lot["W_entry"])) if cell_fn is not None else 0
                        _deep21 = bool((c[i] - lot["avg"]) >= V21_FOLD_DEEP_W * float(lot["w_px"]))
                        _dec21 = v21f.get((_ci21f, _deep21))
                    if _dec21 is not None:                 # fold＝maker 逃げ（deadline shrink の前倒し・期限到達で TREND_CONT taker）
                        lot["fold_dl"] = i + int(_dec21)
                        v15_params["_stats"]["v21_fold_armed"] += 1
                        _keep20.append(lot)
                        continue
                    _record(trades, lot, c[i], "TREND_CONT", i, ts)   # 即 taker（v21f None=v20 恒等／分岐=切迫側）・登録済み再利用＝score.py 無変更（H13）
                    if v15_params is not None:             # ⑨巻き込みの実測（uptrend クローズの発火先＝勝ち$/負け$内訳・acceptance F）
                        _st20 = v15_params["_stats"]
                        _st20["TREND_CONT_rg5"] = _st20.get("TREND_CONT_rg5", 0) + 1
                        _k20 = "TREND_CONT_rg5_win$" if trades[-1]["net_usd"] > 0 else "TREND_CONT_rg5_loss$"
                        _st20[_k20] = round(_st20.get(_k20, 0.0) + trades[-1]["net_usd"], 2)
                        if v21f is not None:
                            _st20["v21_fold_taker"] += 1
                lots = _keep20
                if not lots and v15:
                    rungs = []; rung_next = 0; brk_cnt = 0; brk_vol = False
                if not lots and v16:
                    last_exit_i = i
            if not lots:
                continue                                   # 保有なし＝現行どおり（v21 fold 玉が残る時だけ下の Exit 判定へ進む＝SL/TP/shrink の maker 逃げが生きる）
        if v15 and lots and rung_next < len(rungs) and len(lots) < max_lots:
            rp = rungs[rung_next]                      # 逆走ラダーの約定（resting maker・1バー1段・レンジ判定が立っている時のみ・置いたバーの次以降）
            if ok_arr[i] and np.isfinite(rz_hi[i]) and np.isfinite(mid[i]) and h[i] >= rp \
               and i > max(x["last_fill_idx"] for x in lots):
                w_px2 = rz_lo[i] - sz_hi[i]
                _cl2 = int(cell_fn(kk[i], atr[i] / max(c[i], 1e-9) * 100.0, w_px2 / max(c[i], 1e-9) * 100.0))
                tp2_px = mid[i]; tp1_px = (rp + tp2_px) / 2.0
                if v16:                                # v16: rung lot にもセル別 TP 位置比率を適用（map 無し=恒等・acceptance (6)）
                    _f2 = tp2_fmap.get(_cl2)
                    if _f2 is not None:
                        tp2_px = rp - _f2 * (rp - mid[i])
                    _f1 = tp1_fmap.get(_cl2)
                    if _f1 is not None:
                        tp1_px = rp - _f1 * (rp - mid[i])
                if tp2_far:                            # v18: rung lot も TP2 は反対側ゾーン手前（TP1 は mid 基準のまま・acceptance 2026-07-11）
                    _t2f = sz_hi[i] * (1.0 + V11_SL_BUF)
                    if np.isfinite(_t2f) and _t2f < mid[i]:
                        tp2_px = _t2f
                        v15_params["_stats"]["tp2_far_applied"] += 1
                    else:
                        v15_params["_stats"]["tp2_far_fallback"] += 1
                if tp_floor_check_v15(rp, tp1_px, tp2_px):
                    lots.append({"side": "SHORT", "avg": rp, "size": unit, "add_count": len(lots) + 1,
                                 "first_idx": i, "last_fill_idx": i, "atr_entry": atr[i], "adx_entry": adx[i],
                                 "k_entry": kk[i], "W_entry": w_px2 / max(c[i], 1e-9) * 100.0,
                                 "max_fav": l[i], "max_adv": h[i], "tp1": tp1_px, "tp2": tp2_px,
                                 "sl": rz_hi[i] + float(v15_params["sl_far"]) * w_px2, "tp1_done": False,
                                 "zone_top": rz_hi[i], "w_px": w_px2, "cell": _cl2})
                    v15_params["_stats"]["ladder_fills"] += 1
                rung_next += 1                         # 幾何条件を満たさない段は撤去（次段へ）
        for lot in lots:
            if v14_params is not None or v15:
                lot["pk_prev"] = lot["max_fav"]        # v14: 前バーまでのピークを退避（当該バー low 反映前＝同一バー楽観の排除・H2）
                lot["adv_prev"] = lot["max_adv"]       # v15: 前バーまでの逆走ピーク（戻り決済の arm 判定用・H2）
            lot["max_fav"] = min(lot["max_fav"], l[i]); lot["max_adv"] = max(lot["max_adv"], h[i])
        if v16 and lots and np.isfinite(clu_base):     # v16 トレンド移行ガード（acceptance (2)・全 lot TREND_CONT taker＋クールダウン）
            _g = guard_all if guard_all is not None else guard_map.get(clu_cell)   # v17: 全セル一律候補が優先（None=v16 恒等）
            if _g is not None and guard_fire_v17(c[i], clu_base, clu_w, _g, bool(bb_sig[i]), rz_lo[i] - sz_hi[i]):
                for lot in lots:
                    _record(trades, lot, c[i], "TREND_CONT", i, ts)
                    v15_params["_stats"]["TREND_CONT"] += 1
                lots = []; pend = None; rungs = []; rung_next = 0; brk_cnt = 0; brk_vol = False
                cool_until = i + cooldown; last_exit_i = i
                continue
        if v15 and lots:                               # v15 構造破れ枝（KB §5・全 lot taker 即畳み→レンジ破れは E32b に譲る）
            _ztop = max(x["zone_top"] for x in lots)
            _okb = False if (v16 and brk_anchor) else bool(ok_arr[i])   # v16 anchor=建玉基準カウント（新ゾーン成立でリセットされる穴の是正・acceptance (7)）
            brk_cnt, brk_vol, _fire = range_break_check_v15(
                c[i], _okb, _ztop, vol_arr[i], vol_sma_prev[i], brk_cnt, brk_vol, brk_bars_req)
            if _fire:
                for lot in lots:
                    _record(trades, lot, c[i], "RANGE_BREAK_EXIT", i, ts)
                    v15_params["_stats"]["RANGE_BREAK_EXIT"] += 1
                lots = []; pend = None; rungs = []; rung_next = 0; brk_cnt = 0; brk_vol = False
                if v16:
                    last_exit_i = i
                continue
        still = []
        for lot in lots:
            if i <= lot["last_fill_idx"]:
                still.append(lot); continue
            if v27fl and lot.get("ceil_type") == "flat_up":   # ①.0 v27: flat_up ピーク反転 建値保護（§12＝含み益+0.4%到達後の反転→SL を建値近傍で止める・SL より内側なので先着）
                _pk27 = lot.get("pk_prev", lot["max_fav"])     # 前バーまでの含み益ピーク＝最安値（H2・同一バー楽観の排除）
                if (lot["avg"] - _pk27) >= lot["avg"] * (V27_ARM_PCT / 100.0):   # 武装＝ピーク含み益 ≥ +ARM%（費用超えの逃げ場が実在）
                    _lvl27 = min(_pk27 + V27_GIVEBACK * (lot["avg"] - _pk27), lot["avg"] * (1.0 - SCALP_FLOOR))   # ピーク利益の GIVEBACK 分戻し（下限=建値フロア＝損ゼロ級）
                    if h[i] >= _lvl27:                         # 価格が戻ってロック水準に到達＝resting buy maker 約定（登録済み MFE_DRAWDOWN_CUT・H13無変更）
                        _record(trades, lot, max(_lvl27, o[i]), "MFE_DRAWDOWN_CUT", i, ts)
                        v15_params["_stats"]["MFE_DRAWDOWN_CUT_pf"] = v15_params["_stats"].get("MFE_DRAWDOWN_CUT_pf", 0) + 1
                        continue
            if h[i] >= lot["sl"]:                      # ① SL 優先（同 bar 両到達は不利側先着＝保守・全量／v15=災害SL 遠水準）
                _record(trades, lot, max(lot["sl"], o[i]), "SL_FILLED", i, ts); continue
            if v23te and lot.get("trend_caught"):      # ①.3 v23/v24: trend_caught 玉の V9 型 Exit 状態機械（SL の次・TP より優先＝反転/失速で先に畳む・固定値 a-priori）
                _pk23 = lot.get("pk_prev", lot["max_fav"])       # 前バーまでの含み益ピーク＝最良（最安）価格（H2・同一バー楽観の排除）
                _in_profit23 = (lot["avg"] - _pk23) >= lot["avg"] * V23_RT_FEE   # 含み益ピークが往復 maker fee を超えた＝逃げ場が実在
                if v24tm:                              # v24（acceptance 2026-07-16）: 反転を待たず建値+L% の resting maker 利確（STOCH_REVERSE 廃止＝速い5分レンジで遅行し取り逃す・MFE_STALE は B型止血で残す）
                    _tp24 = lot["avg"] * (1.0 - V24_TREND_TP_PCT / 100.0)   # SHORT の利確＝建値から L% 下（含み益 L%）・resting maker 指値（建値基準の固定水準＝leak なし H2）
                    if l[i] <= _tp24:                  # 当該バー安値が利確水準に到達＝resting limit maker 約定（PARTIAL_TP/TP_FILLED と同じ maker 決済）
                        _record(trades, lot, _tp24, "TREND_CAUGHT_TP", i, ts)
                        v15_params["_stats"]["TREND_CAUGHT_TP"] += 1
                        continue
                    if (not _in_profit23) and (i - int(lot["first_idx"])) * 5 >= V23_STALE_MIN:   # MFE_STALE_CUT（taker・維持）＝利確に届かず含み益ピークが費用未満の B型を保有30分で小さく切る
                        _record(trades, lot, c[i], "MFE_STALE_CUT", i, ts)
                        v15_params["_stats"]["MFE_STALE_CUT"] += 1
                        continue
                else:                                  # v23（既存・v24 OFF）: 反転待ち STOCH_REVERSE ＋ B型 MFE_STALE（既定 OFF=v23_043 恒等）
                    _gc23 = bool(k9 is not None and i > 0 and np.isfinite(k9[i]) and np.isfinite(d9[i])
                                 and np.isfinite(k9[i - 1]) and np.isfinite(d9[i - 1]) and k9[i - 1] <= d9[i - 1] and k9[i] > d9[i])
                    if _in_profit23 and _gc23:             # STOCH_REVERSE_EXIT（taker・登録済み再利用）＝含み益ありで stoch(9,3) GC＝下げの勢いが尽きた→利確（genuine 反転・トレーリングでない）
                        _record(trades, lot, c[i], "STOCH_REVERSE_EXIT", i, ts)
                        v15_params["_stats"]["STOCH_REVERSE_EXIT"] += 1
                        continue
                    if (not _in_profit23) and (i - int(lot["first_idx"])) * 5 >= V23_STALE_MIN:   # MFE_STALE_CUT（taker・登録済み再利用）＝保有 30分でも益が出ない B型→小さく切る
                        _record(trades, lot, c[i], "MFE_STALE_CUT", i, ts)
                        v15_params["_stats"]["MFE_STALE_CUT"] += 1
                        continue
            if v15:                                    # ①.5 v15 戻り決済枝＝armed（前バーまでの逆走≥ret_arm×W）∩ 建値フロアへ回帰（resting buy limit・maker）
                _key = (lot["cell"], min(int(lot["add_count"]), 2), bool(lot["tp1_done"]))
                _rk = v15_params.get("ret", {}).get(_key)
                _armed = _rk is not None and (lot.get("adv_prev", lot["avg"]) - lot["avg"]) >= _rk * lot["w_px"]
                if v16 and not _armed:                 # v16 時間 arm＝TP1 未達のまま bt 本経過（acceptance (3)・建値フロア指値は同じ）
                    _armed = be_time_arm_v16(lot, i, be_time_map.get(_key))
                if _armed:
                    _bf = lot["avg"] * (1.0 - SCALP_FLOOR)   # 建値フロア＝手数料床（損ゼロ級 maker・⑦・TP1 より建値側＝resting が先に約定）
                    if l[i] <= _bf:
                        _record(trades, lot, _bf, "BE_EXIT", i, ts)
                        v15_params["_stats"]["BE_EXIT_ret"] += 1
                        continue
            if (not single_tp) and (not lot["tp1_done"]) and l[i] <= lot["tp1"]:
                half = dict(lot); half["size"] = lot["size"] / 2.0
                _record(trades, half, lot["tp1"], "PARTIAL_TP", i, ts)   # ② TP1＝半分を部分決済（maker・登録済み）
                lot["size"] = lot["size"] / 2.0
                lot["tp1_done"] = True
            if l[i] <= lot["tp2"]:                     # ③ TP2＝レンジ中央で残り全部（maker）
                if v14_params is not None:             # v14 診断: TP2 と枝3/4/5' の同一バー両ヒット計数（挙動不変・楽観側解決の透明化）
                    _gc = bool(k9 is not None and i > 0 and np.isfinite(k9[i]) and np.isfinite(d9[i])
                               and np.isfinite(k9[i-1]) and np.isfinite(d9[i-1]) and k9[i-1] <= d9[i-1] and k9[i] > d9[i])
                    if v14_exit_machine(lot, o[i], h[i], c[i], _gc, v14_params) is not None:
                        v14_params["_stats"]["tp2_bothhit"] += 1
                _record(trades, lot, lot["tp2"], "TP_FILLED", i, ts); continue
            if v14_params is not None:                 # ③.7 v14 Exit 状態機械 枝3/4/5'（acceptance 2026-07-07・トリガは前バーピーク）
                _gc = bool(i > 0 and np.isfinite(k9[i]) and np.isfinite(d9[i])
                           and np.isfinite(k9[i-1]) and np.isfinite(d9[i-1]) and k9[i-1] <= d9[i-1] and k9[i] > d9[i])
                _r14 = v14_exit_machine(lot, o[i], h[i], c[i], _gc, v14_params)
                if _r14 is not None:
                    v14_params["_stats"][_r14[0]] += 1
                    _record(trades, lot, _r14[1], _r14[0], i, ts); continue
            if v15:                                    # ③.8 v15: dd 枝（ピーク反転確定・場面セル×タイプ別の学習窓選定値・stoch/stall は v15 不使用）
                _r15 = v14_exit_machine(lot, o[i], h[i], c[i], False, v15_machine)
                if _r15 is not None:
                    v15_params["_stats"][_r15[0]] = v15_params["_stats"].get(_r15[0], 0) + 1
                    _record(trades, lot, _r15[1], _r15[0], i, ts); continue
            if v15 and v22p is not None and not lot.get("pf_done") and lot["size"] / 2.0 >= ee.MIN_ORDER_BTC:
                _pk22 = lot.get("pk_prev", lot["avg"])   # v22_peak_fold: 前バーまでの含み益ピーク（H2・acceptance 2026-07-13）
                _mv22 = lot["avg"] - _pk22
                if _mv22 >= float(v22p["k"]) * lot["avg"] * 2.0 * ee.MAKER_FEE \
                   and (not v22p.get("warn_only") or (warn22 is not None and warn22[i])):
                    _lvl22 = min(_pk22 + _mv22 * float(v22p["r"]), lot["avg"] * (1.0 - SCALP_FLOOR))
                    if h[i] >= _lvl22:                 # ピークから r 割戻しレベルへ回帰＝半分だけ maker 畳み（MFE_DRAWDOWN_CUT 再利用・下限=建値フロア・1 lot 1回）
                        _half22 = dict(lot); _half22["size"] = lot["size"] / 2.0
                        _record(trades, _half22, max(_lvl22, o[i]), "MFE_DRAWDOWN_CUT", i, ts)
                        v15_params["_stats"]["MFE_DRAWDOWN_CUT_pf"] += 1
                        lot["size"] = lot["size"] / 2.0
                        lot["pf_done"] = True
            if v13_time_maker:                         # ③.5 deadline shrink（Step2・acceptance 2026-07-06）＝TIME 域の玉を成行taker でなく縮む maker TP で取り切る（E35 iter8-9 型）
                _tm = tmax_scene_v16(lot, tmax_map, tmax_l) if v16 else tmax_l   # v16: shrink の deadline も lot の場面連動 backstop に同尺（map 無し=恒等）
                                                       # v14 枝6: 失速（n本経過しても進捗<g）なら shrink 残り時間を T_eff へ前倒し（式は不変・OFF では tmax_l=T_MAX＝恒等）
                if v14_params is not None:
                    _st = v14_params["stall"][(min(int(lot["add_count"]), 2), bool(lot["tp1_done"]))]
                    if _st is not None and (i - lot["first_idx"]) >= _st[0]:
                        _den = lot["avg"] - lot["tp2"]
                        _ppg = (lot["avg"] - lot.get("pk_prev", lot["avg"])) / _den if _den > 0 else 0.0
                        if _ppg < _st[1]:
                            _tm = min(_tm, int(_st[2]))
                            v14_params["_stats"]["stall_early"] += 1
                if "fold_dl" in lot:                   # v21_uptrend_fold: shrink の deadline を fold 期限へ前倒し（建値側へ速く縮む maker 逃げ・acceptance 2026-07-12）
                    _tm = min(_tm, max(1, int(lot["fold_dl"]) - int(lot["first_idx"])))
                if v22w is not None and warn22 is not None and warn22[i]:   # v22_uptrend_warning: 前兆中は shrink 期限を M 本先へ前倒し（maker 逃げの早駆動・taker 強制なし・acceptance 2026-07-13）
                    _tm = min(_tm, max(1, (i - int(lot["first_idx"])) + int(v22w)))
                r = max(0.0, (_tm - (i - lot["first_idx"])) / _tm)          # 残り時間比（fill時 r=1／deadline で r→0・a-priori 時間機構）
                be_floor = lot["avg"] * (1.0 - SCALP_FLOOR)                 # 建値フロア＝手数料床（損ゼロ maker・手数料床を割る決済は建てない・⑦）
                tp_shrunk = lot["tp2"] + (be_floor - lot["tp2"]) * (1.0 - r)   # r=1で tp2（通常）→ r=0で be_floor（建値側へ縮む・tp2≤tp_shrunk≤be_floor）
                if l[i] <= tp_shrunk:                  # 縮む maker TP に到達＝maker 決済（TP_FILLED＝新 exit_reason なし・score.py 不変）
                    _record(trades, lot, tp_shrunk, "TP_FILLED", i, ts); continue
            if "fold_dl" in lot and i >= int(lot["fold_dl"]):   # v21_uptrend_fold: 期限＝maker 逃げに当たらなかった玉は TREND_CONT で確定（taker・発火起因の計上維持・score.py 無変更）
                v15_params["_stats"]["v21_fold_expire"] += 1
                _record(trades, lot, c[i], "TREND_CONT", i, ts); continue
            _lt = tmax_scene_v16(lot, tmax_map, tmax_l) if v16 else tmax_l   # v16: backstop 長の場面連動（map 無し=global 恒等）
            _t_eff = _lt
            if v15 and c[i] > lot["avg"]:
                _dn = down_map.get((lot["cell"], min(int(lot["add_count"]), 2), bool(lot["tp1_done"]))) if v16 else None
                if _dn is None:
                    _dn = v15_params.get("down")
                if _dn is not None:
                    _t_eff = max(1, int(_lt * float(_dn)))   # v15/v16: 含み損玉の TIME 前倒し（V9 TIME_EXIT_DOWN 型・taker・勝ちは満期まで）
            if (i - lot["first_idx"]) >= _t_eff:       # ④ backstop（taker・lot ごと・縮む maker に当たらなかった玉のみ・OFF=T_MAX 恒等／v14/v15=選定長）
                if v15 and _t_eff < _lt:
                    v15_params["_stats"]["down_time"] += 1
                _record(trades, lot, c[i], "TIME_EXIT", i, ts); continue
            still.append(lot)
        _had16 = bool(v16 and lots)                    # v16: この bar の exit で position が空いたかの判定用（代入前の lots＝exit 前の保有）
        lots = still
        if v16 and _had16 and not lots:
            last_exit_i = i                            # クラスタ連結 gap（V16_CLUSTER_GAP）の起点＝最後に position が空いた bar
        if v15 and not lots and (rungs or brk_cnt):
            rungs = []; rung_next = 0; brk_cnt = 0; brk_vol = False   # position 終了＝ラダー/破れカウンタ撤去
        _fire21 = cand[i]                              # 既定＝到達即（v21e None＝v20 恒等）
        if v21e is not None:                           # v21_armed_dc_entry（acceptance 2026-07-12）: 到達で武装し stoch(9,3) DC 発生バーで建てる（タイミングシフト）
            if not ok_arr[i]:
                armed21 = -1                           # range 消滅＝武装解除（uptrend は上の v20 ブロックで解除済み）
            elif cand[i]:
                armed21 = int(v21e["arm_ttl"])         # 到達（再到達で更新＝同じ波の再武装）
            elif armed21 >= 0:
                armed21 -= 1                           # 期限減算（-1 で非武装）
            _cok21 = True
            if v21e.get("cells_off") and cell_fn is not None and np.isfinite(rz_lo[i]) and np.isfinite(sz_hi[i]):
                _wc21 = (rz_lo[i] - sz_hi[i]) / max(c[i], 1e-9) * 100.0
                _cok21 = int(cell_fn(kk[i], atr[i] / max(c[i], 1e-9) * 100.0, _wc21)) not in v21e["cells_off"]
            if _cok21:                                 # 確認が有効なセル＝武装中 ∩ DC 発生 ∩ RSI9 帯（コンフルエンス AND・セル別要否は学習窓選定＝件数を残す）
                _fire21 = bool(armed21 >= 0 and dc21[i]
                               and (v21e["rsi_lo"] is None or (np.isfinite(rsi9_21[i]) and rsi9_21[i] >= float(v21e["rsi_lo"]))))
        if v22e is not None:                           # v22_range_dc_entry（acceptance 2026-07-13）: レンジ判定中は DC 発生バーで建てる（到達武装なし＝戻り売り・v21 入口を置換）
            _fire21 = bool(ok_arr[i] and dc21[i]
                           and (v22e.get("rsi_lo") is None or (np.isfinite(rsi9_21[i]) and rsi9_21[i] >= float(v22e["rsi_lo"]))))
        if v26g is not None and _fire21:               # v26（fast-mode 2026-07-15）: 入口 atr_pct 固定下限＝低ボラ薄利を建てず TP幅ある高ボラ場面に寄せる（建て時点 atr[i]/c[i]＝H2・両経路一括ゲート）
            _atrp26 = atr[i] / max(c[i], 1e-9) * 100.0
            if not (np.isfinite(_atrp26) and _atrp26 >= v26g):
                _fire21 = False
        if v26tf is not None:                          # v26（fast-mode 2026-07-15・まこさん）: 天井で売る＝直近レンジ上端(pos>=F)∩陰転(反転)で建てる。DC は下落中に出て天井を過ぎるため使わず、上端で赤い足が出た瞬間に売る（range_ok は維持・急落後も直近レンジに追従・H2）
            _pos26 = (c[i] - _ll26[i]) / _rng26f[i] if (np.isfinite(_rng26f[i]) and _rng26f[i] > 0) else np.nan
            _fire21 = bool(ok_arr[i] and np.isfinite(_pos26) and _pos26 >= v26tf and c[i] < o26[i])
        if v26sp:                                      # v26（fast-mode 2026-07-15・まこさん）: レンジを2タイプに切り分けて天井に売り指値を置いて待つ（急落後も直近高値に追従／平坦は res_hi）
            _isdn26 = bool(np.isfinite(rz_lo[i]) and rz_lo[i] > c[i] * (1.0 + _gap26))   # 下落系＝価格がレジ帯下端より _gap 以上下（レジが上に張り付き＝急落後）
            _v26ceil = float(_rhdn26[i] if _isdn26 else rz_hi[i])                        # 下落系=直近高値（急落除外の短窓）／平坦上昇系=システムのレジスタンス res_hi
            _ceil_type26 = "down" if _isdn26 else "flat_up"                              # 入口型マーカー（診断列・net不関与・型別分析を見落とさないため 2026-07-15）
            if _cbuf26 > 0.0 and np.isfinite(_v26ceil):                                  # v26 天井バッファ: 天井×(1-buffer)へ下げる（現値+offset 未満にはしない＝maker 成立・上端手前で止まるレンジを拾う）
                _v26ceil = max(_v26ceil * (1.0 - _cbuf26), c[i] * (1.0 + ENTRY_OFFSET))
            _fire21 = bool(ok_arr[i] and np.isfinite(_v26ceil) and _v26ceil > c[i]       # 天井が現在価格の上＝これから上がって来たら約定（resting maker sell）
                           and (_age26 is None or _age26[i] <= _maxage26 * 12))          # A: レンジ判定直後に入る＝立ってからの経過が _maxage 時間内のみ（序盤ほど上昇転換まで余裕・まこさん 2026-07-15）
        if pend is None and _fire21 and len(lots) < max_lots and not (v16 and i < cool_until):
            lim = (_v26ceil if v26sp else c[i] * (1.0 + ENTRY_OFFSET))   # v26 切り分け: 天井（下落系=直近高値／平坦=res_hi）に売り指値＝価格が上がって来たら約定（resting maker sell）
            tp2_px = mid[i]
            tp1_px = (lim + tp2_px) / 2.0
            if v15:                                    # v15: SL=災害水準（ゾーン上端+k×W・遠い）・建て条件は TP1 手数料床のみ（リスクは構造破れ枝＋戻り決済が担う）
                w_px = rz_lo[i] - sz_hi[i]
                _sm = 1.0
                if v16 and np.isfinite(w_px) and w_px > 0:   # v16: セル別 TP1/TP2 位置比率＋新規 size 配分（map 無し=恒等・acceptance (6)(8)）
                    _ci = int(cell_fn(kk[i], atr[i] / max(c[i], 1e-9) * 100.0, w_px / c[i] * 100.0))
                    _f2 = tp2_fmap.get(_ci)
                    if _f2 is not None:
                        tp2_px = lim - _f2 * (lim - mid[i])
                    _f1 = tp1_fmap.get(_ci)
                    if _f1 is not None:
                        tp1_px = lim - _f1 * (lim - mid[i])   # f×(entry−中央)＝0.5 が現行相当（acceptance (6)）
                    _sm = float(size0_map.get(_ci, 1.0))
                if tp2_far:                            # v18: TP2 を反対側＝サポートゾーン上端のすぐ手前へ（TP1 は mid 基準で計算済み＝不変・acceptance 2026-07-11）
                    _t2f = sz_hi[i] * (1.0 + V11_SL_BUF)
                    if np.isfinite(_t2f) and _t2f < mid[i]:
                        tp2_px = _t2f
                        v15_params["_stats"]["tp2_far_applied"] += 1
                    else:
                        v15_params["_stats"]["tp2_far_fallback"] += 1   # 幾何の防御＝従来どおり中央（恒等側）
                if v22a and np.isfinite(w_px) and w_px > 0:   # v22_low_anchor_tp: TP アンカー＝レンジ下限（cell 別 M・acceptance 2026-07-13）
                    _ci22 = int(cell_fn(kk[i], atr[i] / max(c[i], 1e-9) * 100.0, w_px / c[i] * 100.0))
                    _m22 = v22a.get(_ci22)
                    if _m22 is not None:
                        _lo22 = low22[int(_m22)][i]
                        if np.isfinite(_lo22) and _lo22 * (1.0 + V11_SL_BUF) < lim:
                            tp2_px = _lo22 * (1.0 + V11_SL_BUF)   # TP2＝レンジ下限のすぐ手前（maker）
                            tp1_px = (lim + _lo22) / 2.0          # TP1＝建値と下限の中間で半分（acceptance やること2）
                            v15_params["_stats"]["v22_anchor_applied"] += 1
                        else:
                            v15_params["_stats"]["v22_anchor_fallback"] += 1   # 幾何の防御＝現行アンカーのまま（恒等側・下がり切った直後は床が弾く）
                if not (np.isfinite(w_px) and w_px > 0 and tp_floor_check_v15(lim, tp1_px, tp2_px)):
                    continue
                pend = {"limit": lim, "placed_idx": i, "tp1": tp1_px, "tp2": tp2_px,
                        "sl": rz_hi[i] + float(v15_params["sl_far"]) * w_px,
                        "W_pct": w_px / c[i] * 100.0, "zone_top": rz_hi[i], "w_px": w_px, "size_mult": _sm,
                        "ceil_type": _ceil_type26}
                if v22e is not None:
                    v15_params["_stats"]["v22_entry_fires"] += 1   # v22: DC 発生バーごとの発注（武装概念なし）
                elif v21e is not None:
                    armed21 = -1                       # 発注できた波は武装消費（1波1回・幾何不成立で置けなかった時は武装維持＝次の DC で再試行）
                    v15_params["_stats"]["v21_entry_fires"] += 1
                continue
            sl_px = rz_hi[i] * (1.0 + V11_SL_BUF)
            if not tp_ge_sl_check_v11(lim, tp1_px, tp2_px, sl_px, single_tp=single_tp):
                continue                               # TP幅≥SL幅＋手数料床を満たさない候補は建てない
            pend = {"limit": lim, "placed_idx": i, "tp1": tp1_px, "tp2": tp2_px, "sl": sl_px,
                    "W_pct": (rz_lo[i] - sz_hi[i]) / c[i] * 100.0, "ceil_type": _ceil_type26}
    for lot in lots:
        _record(trades, lot, c[n - 1], "FORCE_CLOSE_EOD", n - 1, ts)
    assert short_only_v11 and all(r["side"] == "SHORT" for r in trades), "short_only_v11 違反（LONG 玉が混入）"
    return trades


def _v18_guard_check(df, box_tf) -> None:
    """v18 番人メタ確認（acceptance F-1・§2.9③）＝TP2 反対側の配線が生きている証明＋わざと壊すと恒等へ退行する既知答え。
    ①通常バッファ: tp2_far ON で applied が支配（>0）∩ ON≠OFF（trades hash が変わる）
    ②わざと壊す: バッファを極端（5%＝幅要件 0.4% を大幅超過→置き位置≥中央）にすると全玉フォールバック＝OFF と恒等 hash。
    診断専用（出力ファイルなし・採点しない）。--smoke と併用する。"""
    global V11_SL_BUF
    df = _rsi9_v10(df)
    z1h = _zones_v11_1h(df)
    df = _apply_v11_to_5m(df, z1h)
    df = _attach_v16_bb(df)
    base = {"ladder": None, "sl_far": 1.0, "tmax": 48, "down": None, "ret": {}, "dd": {}, "cell_fn": None,
            "v16": True, "v17": True, "guard": {}, "guard_all": None, "cooldown": 6, "be_time": {}, "tmax_map": {},
            "down_map": {}, "tp1_f": {}, "tp2_f": {}, "size0": {}, "break_mode": None, "break_bars": V15_BREAK_BARS}

    def _run(tp2_far: bool, buf: float | None = None):
        global V11_SL_BUF
        old = V11_SL_BUF
        if buf is not None:
            V11_SL_BUF = buf
        try:
            pp = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base.items()}
            if tp2_far:
                pp["tp2_far"] = True
            tr = run_continuous_v11(df, box_tf, v12_open_range=True, v13_time_maker=True, v15_params=pp)
        finally:
            V11_SL_BUF = old
        s = json.dumps([[str(r["entry_time"]), r["exit_reason"], round(float(r["net_usd"]), 6)] for r in tr])
        return tr, pp.get("_stats", {}), hashlib.sha256(s.encode()).hexdigest()[:12]

    print("=" * 100)
    print("[v18 番人メタ確認] TP2 反対側の配線証明（採点しない）")
    tr0, _, h0 = _run(False)
    tr1, st1, h1 = _run(True)
    tw0 = [float(r["net_usd"]) for r in tr0 if r["exit_reason"] == "TP_FILLED"]
    tw1 = [float(r["net_usd"]) for r in tr1 if r["exit_reason"] == "TP_FILLED"]
    print(f"  OFF: {len(tr0)} fill / hash {h0} / TP_FILLED {len(tw0)}玉 平均net ${(sum(tw0)/len(tw0)) if tw0 else float('nan'):.2f}")
    print(f"  ON : {len(tr1)} fill / hash {h1} / TP_FILLED {len(tw1)}玉 平均net ${(sum(tw1)/len(tw1)) if tw1 else float('nan'):.2f}"
          f" / applied={st1.get('tp2_far_applied')} fallback={st1.get('tp2_far_fallback')}")
    assert st1.get("tp2_far_applied", 0) > 0 and h1 != h0, "T1: tp2_far ON で applied=0 or OFF と同一＝配線が死んでいる"
    print("  T1 ✅ 配線: applied>0 ∩ ON≠OFF")
    _, st2, h2 = _run(True, buf=0.5)
    print(f"  壊し（buf=50%）: hash {h2} / applied={st2.get('tp2_far_applied')} fallback={st2.get('tp2_far_fallback')}")
    assert st2.get("tp2_far_applied", 0) == 0 and h2 == h0, "T2: 極端バッファで恒等へ退行しない＝幾何防御（フォールバック）が死んでいる"
    print("  T2 ✅ わざと壊すと全玉フォールバック＝OFF と恒等（幾何防御が生きている）")
    print("=" * 100)


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


def rg5_selftest_labels(df: pd.DataFrame, lab_path: pathlib.Path | None = None) -> None:
    """v20 自己検査（acceptance F・--v20-selftest-rg5）: 戦略内の RG-v5 判定（1h帯・zone_ok・uptrend・5分 range）が
    ダッシュボード生成物（labels_rg-v5.csv／predictions_rg-v5_5m/<月>.json）と全期間一致するか機械照合。
    一致＝まこさんが⑪タブで視認校正した判定と同一のレンジ判定・トレンド除外で戦略が動く証明（v11 selftest と同方式）。
    lab_path は番人メタ確認（--v20-guard-check＝改ざん検出）専用の差し替え口＝通常は正本固定。"""
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    proto = repo_root / "dashboard" / "regime_prototype"
    lab_path = lab_path or (proto / "labels_rg-v5.csv")
    assert lab_path.exists(), f"labels_rg-v5.csv がありません: {lab_path}"
    z1h, up, rng, res_lo, res_hi, sup_lo, sup_hi = _rg5_frames(df)
    # ── ① 1h 層＝帯（zone_ok・4価格）と uptrend_1h の照合 ──
    lab = pd.read_csv(lab_path, parse_dates=["datetime_utc"]).set_index("datetime_utc").sort_index()
    j = z1h.join(lab, how="inner", rsuffix="_lab")
    assert len(j) > 0, "labels_rg-v5.csv と 1h index が重ならない（入力 CSV が違う疑い）"
    zk_mis = int((j["zone_ok"].astype(int) != j["zone_ok_lab"].astype(int)).sum())
    px_mis = 0
    for col in ("res_lo", "res_hi", "sup_lo", "sup_hi"):
        a = j[col].round(1); b = j[f"{col}_lab"]
        both = a.notna() & b.notna()
        px_mis += int(((a[both] - b[both]).abs() > 0.1).sum())
        px_mis += int((a.isna() != b.isna()).sum())
    up_s = pd.Series(up, index=pd.DatetimeIndex(df["ts"]))
    up1h = (up_s.resample("1h", label="right", closed="right").mean() >= 0.5).astype(int)
    ju = pd.DataFrame({"mine": up1h}).join(lab[["uptrend_1h"]], how="inner").dropna()
    up_mis = int((ju["mine"] != ju["uptrend_1h"].astype(int)).sum())
    print(f"  [selftest rg5 ①1h] {len(j):,}本 / zone_ok 不一致 {zk_mis} / 帯価格 不一致 {px_mis} / uptrend_1h 不一致 {up_mis}（labels_rg-v5.csv 照合）")
    assert zk_mis == 0 and px_mis == 0 and up_mis == 0, "RG-v5 の 1h 判定が labels_rg-v5.csv と不一致＝移植ミス（視認校正した判定と別物）"
    # ── ② 5分 最終判定（range/uptrend ラベル）＝ダッシュボード表示の実物 JSON と照合 ──
    pred_dir = proto / "predictions_rg-v5_5m"
    mine = pd.Series(np.where(up, "uptrend", np.where(rng, "range", "")), index=pd.DatetimeIndex(df["ts"]))
    n5 = 0; mis5 = 0
    for p in sorted(pred_dir.glob("*.json")):
        rows = json.loads(p.read_text(encoding="utf-8"))["rows"]
        d = pd.DataFrame(rows, columns=["ts_ms", "close", "label", "x"])
        d.index = pd.to_datetime(d["ts_ms"], unit="ms")
        both = d.index.intersection(mine.index)
        if len(both) == 0:
            continue
        n5 += len(both)
        mis5 += int((mine.loc[both].to_numpy() != d.loc[both, "label"].to_numpy()).sum())
    if n5 == 0:
        print("  [selftest rg5 ②5分] 照合対象なし（--smoke が predictions の期間 2024-06 以降に届いていない）＝①のみで判定")
    else:
        print(f"  [selftest rg5 ②5分] {n5:,}本 / ラベル不一致 {mis5}（predictions_rg-v5_5m 照合）")
        assert mis5 == 0, "RG-v5 の 5分最終判定が predictions_rg-v5_5m と不一致＝移植ミス"
    print("  [selftest rg5] ✅ 全期間一致＝視認校正済み RG-v5 と同一のレンジ判定・トレンド除外で戦略が動く")


def _v20_guard_check(df: pd.DataFrame) -> None:
    """v20 番人メタ確認（--v20-guard-check・採点しない・--smoke 併用推奨）＝わざと壊して落ちるか（§2.9③）:
    (a) 配線支配＝uptrend を全期間 True に強制すると新規が1件も建たない（入口 veto の配線証明）
    (b) 境界クローズ＝後半だけ True にすると保有が境界バーで TREND_CONT で畳まれ以後 entry ゼロ
    (c) 改ざん検出＝labels_rg-v5.csv の zone_ok を反転した改ざんコピーで selftest ①が停止する"""
    df = _rsi9_v10(df)
    df = _apply_rg5_to_5m(df)
    n = len(df)
    # (a) 全期間 uptrend 強制 → 新規ゼロ
    tr_a = run_continuous_v11(df, "5m", v12_open_range=True, v13_time_maker=True,
                              v20_uptrend=np.ones(n, bool))
    ok_a = len(tr_a) == 0
    print(f"  [番人a 全期間uptrend強制] trades={len(tr_a)}（期待0）: {'✅ 入口 veto が配線支配' if ok_a else '⛔ 配線不全'}")
    # (b) 保有中に uptrend 強制 → 建玉が TREND_CONT で即畳まれ・以後 entry ゼロ
    #     境界＝通常走行の最初の建玉の fill バー直後（保有が確実に在る瞬間に発火させる＝配線証明）
    tr_n = run_continuous_v11(df, "5m", v12_open_range=True, v13_time_maker=True)
    assert len(tr_n) > 0, "番人b: 通常走行で建玉ゼロ（--smoke を増やして再実行）"
    first_fill = pd.Timestamp(pd.DataFrame(tr_n)["entry_time"].min())
    k = int(np.searchsorted(df["ts"].to_numpy(), np.datetime64(first_fill))) + 1
    up_b = np.zeros(n, bool); up_b[k:] = True
    tr_b = run_continuous_v11(df, "5m", v12_open_range=True, v13_time_maker=True, v20_uptrend=up_b)
    tb = pd.DataFrame(tr_b)
    bnd_ts = pd.Timestamp(df["ts"].iloc[k])
    n_tc = int((tb["exit_reason"] == "TREND_CONT").sum()) if len(tb) else 0
    # 境界バー当日（uptrend が立った最初のバー）の約定は因果的に正当＝バー内では uptrend 未知（close で確定）→
    # 直後の uptrend 枝が即クローズする（悲観側＝手数料を払う）。禁止すべきは「境界より厳密に後」の新規。
    late_entry = int((pd.to_datetime(tb["entry_time"]) > bnd_ts).sum()) if len(tb) else 0
    ok_b = n_tc > 0 and late_entry == 0
    print(f"  [番人b 保有中uptrend強制] TREND_CONT={n_tc}（期待>0） / 境界より後の新規={late_entry}（期待0）: {'✅ 即クローズ＋新規停止が配線支配' if ok_b else '⛔ 配線不全'}")
    # (c) labels 改ざん → selftest が停止
    repo_root = pathlib.Path(__file__).resolve().parents[2]
    src_lab = repo_root / "dashboard" / "regime_prototype" / "labels_rg-v5.csv"
    tam = pd.read_csv(src_lab)
    tam["zone_ok"] = 1 - tam["zone_ok"].astype(int)     # 全行反転＝確実に不一致
    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
        tam.to_csv(f.name, index=False)
        tam_path = pathlib.Path(f.name)
    try:
        rg5_selftest_labels(df, lab_path=tam_path)
        ok_c = False
    except AssertionError:
        ok_c = True
    finally:
        tam_path.unlink(missing_ok=True)
    print(f"  [番人c labels改ざん] selftest 停止: {'✅ 改ざんを検出して停止' if ok_c else '⛔ 素通り＝検査不全'}")
    assert ok_a and ok_b and ok_c, "v20 番人メタ確認 不合格（配線/検査の不全）"
    print("  [v20 番人] ✅ 3/3 pass（入口 veto 支配・即クローズ支配・改ざん検出）")


# ── §0「使用パラメータ」の必須項目スキーマ（今後 CC が項目を削れない物理強制・まこさん指示「強制」2026-07-12）──
#   実行時 assert が §0（v11）に下記ブロック・キーが揃っているか検証し、欠けたら SystemExit＝戦略が走らない＝
#   出力が出ない＝項目の削除や手書き固定文字列への差し替えを物理的に塞ぐ。既知答えテスト test_param_sections_schema.py と対。
PARAM_SECTION_SCHEMA_V11 = {
    "blocks": ["検証期間", "【入口】", "【固定値】サイズ", "【出口】", "【学習方法", "【固定値】コスト"],
    "keys": {"【入口】": ["レンジ判定", "エントリー", "方向"],
             "【出口】": ["TP1", "TP2", "SL", "時間切れ"],
             "【学習方法": ["ML/検出器", "選定 vs 固定"]},
}


def _assert_param_schema_v11(sec: dict) -> None:
    """§0（v11）が必須ブロック・必須キーを全部含むか検証。欠けたら SystemExit（項目削除/手書き化を物理的に禁止）。"""
    keys = list(sec.keys())
    for blk in PARAM_SECTION_SCHEMA_V11["blocks"]:
        m = [k for k in keys if str(k).startswith(blk)]
        if not m:
            raise SystemExit(f"[§0 スキーマ強制] 必須ブロック欠落: {blk}（report §0 の項目は削れない・まこさん 2026-07-12）")
        for sk in PARAM_SECTION_SCHEMA_V11["keys"].get(blk, []):
            if not any(str(k).startswith(sk) for k in sec[m[0]]):
                raise SystemExit(f"[§0 スキーマ強制] {blk} の必須キー欠落: {sk}（項目は削れない・まこさん 2026-07-12）")


def _used_flags_section(parser, args) -> dict:
    """report §0 用: 実際に渡された全フラグ＋argparse help（＝ロジック説明）＋実値を自動列挙する。
    ★狙い（まこさん 2026-07-15「強制せずとも今後も修正した内容を正確に Report へ自動生成」）＝
      argparse を単一の出所にすることで、今後どのフラグ（入口/出口ロジック）を足しても report に
      自動で漏れなく載る。手書き _param_sections が v25/v26 を取りこぼしドリフトした根本対策で、
      フラグは argparse に定義しないと使えない＝report を argparse から作れば構造的に正確なまま（強制hook不要）。"""
    import sys
    passed = {t.split("=", 1)[0] for t in sys.argv[1:] if t.startswith("--")}   # 実際に渡された option 名
    used = {}
    for act in parser._actions:
        if not act.option_strings:                                             # 位置引数/helpはスキップ
            continue
        if set(act.option_strings) & passed:                                   # このフラグは今回の実行で使われた
            val = getattr(args, act.dest, None)
            used[f"{act.option_strings[-1]} = {val}"] = " ".join((act.help or "").split())
    title = ("【使用フラグ全量（argparse 由来・自動生成＝今後どのフラグ[入口/出口ロジック]を足しても"
             "漏れず載る・強制hook不要で正確・手書きドリフト対策・まこさん 2026-07-15）】")
    return {title: (used or {"（既定フラグのみ）": "明示フラグなし"})}


def _param_schema_selftest() -> None:
    """§0 自動生成の既知答えテスト＋番人（--param-schema-selftest）。導出の正しさ＋項目削除の物理禁止を検証。"""
    _s = {"sl_far": 1.0, "tmax": 48, "down": None, "ret": {}, "dd": {(4, 2, True): (0.5, 1 / 3)}, "cell_fn": (lambda k, a, w: 0),
          "v16": True, "v17": True, "guard": {}, "guard_all": None, "cooldown": 6, "be_time": {}, "tmax_map": {},
          "down_map": {(2, 2, True): 0.75}, "tp1_f": {}, "tp2_f": {}, "size0": {}, "break_mode": None, "break_bars": 12,
          "tp2_far": True, "ladder": None, "_stats": {"tp2_far_applied": 13434, "tp2_far_fallback": 0, "RANGE_BREAK_EXIT": 537}}
    sec = _param_sections(None, True, v11=True, v13_time_maker=True, v12_open_range=True, v15_sel=_s)
    _assert_param_schema_v11(sec)
    e = sec[[k for k in sec if k.startswith("【入口】")][0]]
    x = sec[[k for k in sec if k.startswith("【出口】")][0]]
    assert "到達だけ" in e["エントリー"], f"入口が v12_open_range を反映せず: {e['エントリー']}"
    sl = x[[k for k in x if k.startswith("SL")][0]]
    assert ("災害SL" in sl) and ("1.0" in sl), f"SL が sl_far を反映せず（手書き浅SL疑い）: {sl}"
    assert not any("ラダー" in str(k) for k in x), "使っていない add ラダーが表示されている（不使用の枝は出さない）"
    assert any("ピーク反転" in str(k) for k in x), "使っている dd 枝が表示されていない"
    sec_up = _param_sections(None, True, v11=True, v13_time_maker=True, v12_open_range=True, v19_upper_touch=True, v15_sel=_s)
    assert "res_hi" in sec_up[[k for k in sec_up if k.startswith("【入口】")][0]]["エントリー"], "v19 upper_touch を反映せず"
    sec20 = _param_sections(None, True, v11=True, v13_time_maker=True, v12_open_range=True, v15_sel=_s, v20_rg5=True)
    _e20 = sec20[[k for k in sec20 if k.startswith("【入口】")][0]]
    _rgk = [k for k in _e20 if str(k).startswith("レンジ判定 range_ok_rg5")]
    assert _rgk and any("RG-v5" in str(_e20[k]) for k in _rgk), "v20 rg5 のレンジ判定表示を反映せず"
    # v21 拡張: RG-v5 詳細＝実定数からの自動生成（帯対・5分判定・状態機械の発火/解除・接続）を平坦キーで1行ずつ（まこさん 2026-07-12）
    for _need_rg in ("帯対", "発火", "解除", "5分 range"):
        assert any(_need_rg in str(k) for k in _rgk), f"RG-v5 のレンジレジーム判定 詳細（{_need_rg}）が §0 に出ていない（まこさん 2026-07-12）"
    _x20 = sec20[[k for k in sec20 if k.startswith("【出口】")][0]]
    assert any("uptrend 即クローズ" in str(k) for k in _x20), "v20 の uptrend 即クローズ枝が §0 に出ていない"
    # v21: 学習した実験（_learning_spec あり）は学習対象/方法/合格判定/選定結果が自動で載る（まこさん 2026-07-12）
    _s21 = dict(_s); _s21["_learning_spec"] = {
        "targets": [{"name": "test", "menu": ["a", "b"], "selected": "a", "note": "n"}],
        "method": {"m": "x"}, "gate": [{"cond": "(t)", "thr": "y"}],
        "result": {"n_tried": 2, "incumbent_net": -1.0, "final_net": -0.5, "incumbent_freq": 1.0, "freq_floor": 0.7,
                   "selected": {"v21_entry": None, "v21_fold": None},
                   "rows": [{"候補": "e:t", "net$": -1, "新規/日": 1.0, "採否": "採択"}]}}
    _l21 = _param_sections(None, True, v11=True, v13_time_maker=True, v12_open_range=True, v15_sel=_s21, v20_rg5=True)
    _lb = _l21[[k for k in _l21 if k.startswith("【学習方法")][0]]
    for _need in ("★学習対象", "★学習方法", "★合格判定条件", "★選定結果"):
        assert any(str(k).startswith(_need) for k in _lb), f"学習の自動ドキュメント（{_need}）が §0 に出ていない（まこさん 2026-07-12）"
    xb = _param_sections(None, True, v11=True)
    xb = xb[[k for k in xb if k.startswith("【出口】")][0]]
    assert "浅い" in xb[[k for k in xb if k.startswith("SL")][0]], "v15 なしで浅SLにならず"
    # 番人: 必須ブロック/キーを削ると SystemExit
    try:
        _assert_param_schema_v11({k: v for k, v in sec.items() if not k.startswith("【学習方法")})
        raise AssertionError("学習ブロック欠落を検出せず＝強制不全")
    except SystemExit:
        pass
    try:
        _b = dict(sec); _xk = [k for k in _b if k.startswith("【出口】")][0]
        _b[_xk] = {k: v for k, v in _b[_xk].items() if not str(k).startswith("SL")}
        _assert_param_schema_v11(_b)
        raise AssertionError("出口 SL キー欠落を検出せず＝強制不全")
    except SystemExit:
        pass
    print("✅ §0 スキーマ selftest 全 pass（自動生成＝実値導出／項目削除・手書き化で SystemExit＝物理強制）")
    print("\n── 自動生成 §0 の実例（v18 構成＝--v12-open-range ∩ sl_far=1.0 ∩ tp2_far・すべて実値から導出）──")
    for blk, body in sec.items():
        if any(t in blk for t in ("入口", "サイズ", "出口", "学習")):
            print(f"■ {blk}")
            for k, v in body.items():
                print(f"    {k}: {v}")


def _rg5_gate_desc() -> dict:
    """§0 レンジ判定 range_ok_rg5 の詳細（まこさん 2026-07-12「レンジレジーム判定ロジックも詳細に記述」）＝
    正本 build_regime_gate_rg.py（RG-v5）のモジュール定数を実行時に import して埋める＝手書きドリフトしない
    （実際に走る判定と同じ定数・labels 一致 selftest と対）。"""
    rg = _import_rg5()
    z = rg.v17                                         # 帯の定数の正本（視認校正済み・RG が import 再利用）
    return {
        "正本・照合": ("build_regime_gate_rg.py（RG-v5）を import 再利用（コピー禁止）・labels_rg-v5.csv／predictions_rg-v5_5m と"
                   "全期間一致を --v20-selftest-rg5 で機械照合・視認校正3巡（まこさん 2026-07-12 OK）・全て確定バーのみ＝未来値ゼロ（H2）〔視認校正〕"),
        "①1h S/R 帯対（レンジの認識）": (
            f"1時間足の確定 fractal スイング（j+2 確定＝当該足までで確定）を過去{z.ZONE_LOOKBACK}h（{z.ZONE_LOOKBACK//24}日）窓・"
            f"価格帯{z.ZONE_TOL*100:.1f}%で束ね、タッチ数≥{z.ZONE_TOUCH}のクラスタ帯を価格に近い順に上下で対にし、"
            f"帯間の幅≥{z.ZONE_MIN_W*100:.1f}%を満たす最初の対（上=レジスタンス帯 res_lo/res_hi・下=サポート帯 sup_lo/sup_hi）を採用"
            "＝帯対拡張（最近接対が幅不足でも次の対を試す・RG-v3・12月/1月の不検出解消）"),
        "②5分 range 判定（執行ゲート）": (
            "①の帯対あり ∩ 5分 close が帯内（close>res_hi または close<sup_lo でブレイク＝離脱） ∩ ③uptrend 非発火 ＝ range"
            "（range の時だけ入口候補を生成・帯価格を v11_res_lo/hi・v11_sup_hi・mid へ供給）"),
        "③uptrend 状態機械・発火（いずれか1つ・上げ専用・過去 close の逐次更新）": (
            f"A15: 15分足{rg.TREND_ST15_K}本連続の高値切り上げ∩安値切り上げ（上げ構造） ／ "
            f"D15: 15分足{rg.TREND_MOM15_K}本連続の陽線 ∩ 累積上昇≥{rg.TREND_MOM15_AMP*100:.1f}% ／ "
            f"C90: 直近90分（前回解除以降に限定＝影再発火の根絶）の最小 close から+{rg.TREND_T90*100:.1f}% ／ "
            f"T6: 直近6h（同）の最小 close から+{rg.TREND_T6*100:.1f}%（遅い上げの受け皿）"),
        "③uptrend 状態機械・継続再発火": (
            f"解除後{rg.TREND_CONT_W}本（{rg.TREND_CONT_W*5//60}時間）以内に close>前回高値×(1+{rg.TREND_CONT_M*100:.1f}%)"
            "＝上げ継続と確定し再発火（発火時安値は前回の脚から引き継ぐ＝緩やかな上げの断片化防止）"),
        "③uptrend 状態機械・解除（いずれか1つ）": (
            f"半値戻し: close≤最高値−{rg.TREND_RETR:.0%}×(最高値−発火時安値) ／ "
            f"停滞: 高値更新なし{rg.TREND_STALL}本（{rg.TREND_STALL*5//60}時間） ／ "
            f"15分構造破断: close<直近{rg.TREND_STRUCT_REL}本の確定15分足安値の最小（上げ構造の終了を速く検出）"),
        "④エンジンへの接続": ("range=入口候補の生成を許可 ／ uptrend 発火中=新規・add 停止（pend 取り下げ）＋保有 lot は"
                        "『uptrend 畳み分岐』（出口ブロック参照）＝レンジ前提の終了を機構で守る（risk-manager 型）"),
    }


def _render_learning_block(spec: dict) -> dict:
    """★学習の自動ドキュメント化（まこさん 2026-07-12「実装した学習内容・学習方法・合格判定の条件を Report §0 に
    詳細に自動生成」）＝選定関数が返す構造化 _learning_spec を §0 の【学習方法・学習内容】サブ項目へ描画する
    戦略非依存の共通レンダラ。今後の選定（v22+）も同じ形の spec を v15p['_learning_spec'] に入れれば自動で載る。
    spec = {targets:[{name,menu,selected?,note}], method:{...}, gate:[{cond,thr}], result:{...}}"""
    out = {}
    res = spec.get("result", {})
    sel = res.get("selected", {})
    # ① 学習対象（何を学習したか＝候補メニュー→選定値）※report 表示は2階層まで＝プレフィックス付き平坦キー
    for t in spec.get("targets", []):
        menu = " / ".join(str(x) for x in t.get("menu", []))
        selected = t.get("selected", "（本走で確定）")
        line = f"候補メニュー{{{menu}}} → 学習窓選定＝{selected}"
        if t.get("note"):
            line += f"（{t['note']}）"
        out[f"★学習対象: {t['name']}"] = line
    # ② 学習方法（どう学習したか）
    for k, v in spec.get("method", {}).items():
        out[f"★学習方法: {k}"] = v
    # ③ 合格判定条件（採択ゲートと閾値＝どれを満たせば採用か）
    for g in spec.get("gate", []):
        out[f"★合格判定条件 {g['cond']}"] = g["thr"]
    # ④ 選定結果（試行数・incumbent→最終・採択値・全候補行を §0 に丸ごと＝学習内容の証跡）
    if res:
        out["★選定結果: 試行数"] = f"{res.get('n_tried', '?')} 候補（学習窓のみ・採点窓不参照）"
        out["★選定結果: incumbent→最終 net"] = (f"${res.get('incumbent_net', 0):,.0f}（新規 {res.get('incumbent_freq', 0)}/日・"
                                            f"件数床 {res.get('freq_floor', 0)}/日）→ ${res.get('final_net', 0):,.0f}")
        out["★選定結果: 採択値"] = f"入口={sel.get('v21_entry')} / 出口fold={sel.get('v21_fold')}"
        for i, rw in enumerate(res.get("rows", []), 1):   # 全候補を1行ずつ（net/新規per日/採否 or 不採択理由）＝手書き不能・実測から自動
            out[f"★選定結果: 候補{i:02d} {rw['候補']}"] = f"学習窓 net ${rw['net$']:,.0f} / 新規 {rw['新規/日']}/日 / {rw['採否']}"
    return out


def _v22_entry_desc(e22: dict, stats: dict) -> str:
    """§0 エントリー行（v22_range_dc_entry・実値から生成・acceptance 2026-07-13）。"""
    _rsi = "なし（DC のみ）" if e22.get("rsi_lo") is None else f"≥{e22['rsi_lo']:g}"
    return (f"v22_range_dc_entry＝range_ok_rg5 が立つバーで 5分 stoch(9,3) デッドクロス発生バーに SHORT 指値"
            f"（到達武装なし＝レンジ内の戻り売り・RSI9 下限={_rsi}・発火{stats.get('v22_entry_fires', 0)}"
            f"【カウンタ集計窓＝直近6ヶ月(採点窓)+助走の合計（非ML固定版）】・手数料床/R:R チェックが薄い場面と下がり切った直後を自動拒否）〔学習窓選定〕")


def _v21_entry_desc(e21, edge: str, conf: str, stats: dict) -> str:
    """§0 エントリー行（v21_armed_dc_entry の実値表示・acceptance 2026-07-12・None=v20 表示）。
    ★学習対象パラメータ（RSI9 帯・武装期限）は「候補メニュー→選定値」の形で明示する（まこさん 2026-07-12
    「RSI の学習内容が Report に書いてない」＝学習させた閾値の選定過程を §0 に残す・選定表全行は
    <stem>_v21_selection.txt に保存＝gate_diag と対）。"""
    if not e21:
        return f"上限ゾーンの{edge} に high 到達 ∩ 拒否確認={conf}"
    _rsi_menu = "/".join("なし" if x is None else str(x) for x in V21_RSI_LO)
    rsi_sel = "なし（RSI 条件なし）" if e21.get("rsi_lo") is None else f"≥{e21['rsi_lo']}"
    _ttl_menu = "/".join(str(x) for x in V21_ARM_TTL)
    off_txt = f"・確認offセル={sorted(e21['cells_off'])}（このセルは到達即＝確認なし）" if e21.get("cells_off") else ""
    return (f"上限ゾーンの{edge} に high 到達で武装（武装期限 arm_ttl={e21['arm_ttl']}本・"
            f"range 消滅/uptrend で解除）→ stoch(9,3) デッドクロス発生バーで建てる（v21_armed_dc_entry）"
            f"∩ RSI9 買われすぎ下限={rsi_sel}"
            f"{off_txt}・発火{stats.get('v21_entry_fires', 0)}〔定数継承（v21_037/040 採択値・v24 で固定・非ML・学習窓選定なし）〕")


def _param_sections(det: dict | None, gate_on: bool, v6: bool = False, v6r: bool = False, v7: bool = False, v8: bool = False, v9: bool = False, v10: bool = False, v11: bool = False, v11_no_add: bool = False, v11_single_tp: bool = False, v13_time_maker: bool = False, v14_sel: dict | None = None, v15_sel: dict | None = None, v11_open_entry: bool = False, v12_open_range: bool = False, v19_upper_touch: bool = False, v20_rg5: bool = False) -> dict:
    if v11:
        # ── §0 は実行時フラグ・v15p 実値から自動導出（手書き固定文字列を廃す・ズレ根絶・2026-07-12）──
        s15 = v15_sel or {}
        _prov = s15.get("prov") or {}                  # 値ごとの出所タグ（v18 定数継承構成が設定・無ければ従来表示＝恒等・2026-07-12）
        _edge = "帯の上端 res_hi（本当のレジスタンス）" if v19_upper_touch else "帯の下端 res_lo"
        _conf = ("なし＝到達だけ（--v12-open-range で拒否確認を外す）" if v12_open_range
                 else ("陰転 ∩ RSI9 下向き反転（過熱の必須化なし・--v11-open-entry）" if v11_open_entry
                       else "陰転 ∩ RSI9>70 からの下向き反転（到達＋拒否確認）"))
        _sl_eff = (f"ゾーン上端 res_hi ＋ {s15['sl_far']}×W＝深い災害SL（遠い・v15 経路が有効な時の実効SL）〔{_prov.get('sl_far', '学習窓選定/定数継承')}〕"
                   if "sl_far" in s15 else f"res_hi×(1+{V11_SL_BUF*100:.2f}%)＝ゾーンのすぐ外（浅い）〔固定値〕")
        # 出口の状態機械：実際に有効（値が非空）な枝だけを実値で出す（使っていない枝は表示しない・まこさん 2026-07-12）
        _stats = s15.get("_stats", {})
        _fire = lambda k: (f"・発火{_stats[k]}" if _stats.get(k) else "")
        _tp2 = (f"サポートゾーン上端×(1+{V11_SL_BUF*100:.2f}%)＝反対側ゾーンのすぐ手前で残り全部〔幾何a-priori・v18〕"
                + (f"・発火{_stats['tp2_far_applied']}（発注試行ベース＝約定数ではない）" if _stats.get("tp2_far_applied") else "")
                if s15.get("tp2_far") else "レンジ中央（(上限ゾーン下端+下限ゾーン上端)/2）で残り全部〔幾何a-priori〕")
        _mech = {}   # 有効な枝だけ（値が非空のもの）を実値で
        if s15.get("dd"):
            _mech["ピーク反転 dd MFE_DRAWDOWN_CUT(maker)"] = f"(p_arm,r)×(セル,add,tp1)={s15['dd']}{_fire('MFE_DRAWDOWN_CUT')}〔{_prov.get('dd', '学習窓選定/定数継承')}〕"
        if s15.get("down_map"):
            _mech["含み損 TIME 前倒し down_map(taker)"] = f"(セル,add,tp1)→短縮率={s15['down_map']}{_fire('down_time')}〔{_prov.get('down_map', '学習窓選定/定数継承')}〕"
        elif s15.get("down") is not None:              # グローバル down フォールバック（実エンジン 1920-1925 と同経路・表示欠落の是正 2026-07-12）
            _mech["含み損 TIME 前倒し down(taker・全lot一律)"] = f"短縮率={s15['down']}{_fire('down_time')}〔{_prov.get('down', '学習窓選定')}〕"
        if s15.get("break_bars"):
            _mech["レンジ破れ RANGE_BREAK_EXIT(taker)"] = f"ゾーン外終値{s15['break_bars']}本(1h)持続 ∩ 出来高>{V15_BREAK_VOL_N}期間平均{_fire('RANGE_BREAK_EXIT')}〔KB§5〕"
        if s15.get("ret") or s15.get("be_time"):
            _mech["戻り決済 BE_EXIT(maker)"] = f"逆走arm={s15.get('ret')}／時間arm={s15.get('be_time')}{_fire('BE_EXIT_ret')}〔学習窓選定〕"
        if s15.get("ladder"):
            _mech["add ラダー(maker指値)"] = f"逆走段(W比)={s15['ladder']}{_fire('ladder_fills')}〔学習窓選定〕"
        if s15.get("guard") or s15.get("guard_all"):
            _mech["トレンドガード TREND_CONT(taker)"] = f"セル別={s15.get('guard')}／全セル={s15.get('guard_all')}{_fire('TREND_CONT')}〔学習窓選定〕"
        if s15.get("tp1_f") or s15.get("tp2_f"):
            _mech["TP 位置比率"] = f"tp1_f={s15.get('tp1_f')}／tp2_f={s15.get('tp2_f')}〔学習窓選定〕"
        if s15.get("size0"):
            _mech["新規 size 配分 size0"] = f"={s15['size0']}〔学習窓選定〕"
        if v20_rg5:                                    # v20 regime exit（acceptance 2026-07-12）＝実フラグから自動生成
            _f21 = s15.get("v21_fold")
            if _f21:                                   # v21_uptrend_fold（acceptance 2026-07-12）: 即 taker 1択から場面分岐へ
                _mech["uptrend 畳み分岐 v21_uptrend_fold(maker逃げ/taker)"] = (
                    f"RG-v5 上げトレンド発火＝新規/add 停止＋保有 lot を(発火時セル,含み損≥{V21_FOLD_DEEP_W}W)別に分岐："
                    f"fold=(deadline shrink を期限へ前倒し＝建値側へ縮む maker 逃げ・期限到達で TREND_CONT taker)／キー不在=即 taker。"
                    f"分岐表={_f21}"
                    + f"・fold_armed {_stats.get('v21_fold_armed', 0)}／期限taker {_stats.get('v21_fold_expire', 0)}／即taker {_stats.get('v21_fold_taker', 0)}"
                    + (f"・即taker側 内訳 勝ち玉 ${_stats.get('TREND_CONT_rg5_win$', 0)} / 負け玉 ${_stats.get('TREND_CONT_rg5_loss$', 0)}（⑨巻き込みの実測）"
                       if _stats.get("TREND_CONT_rg5") else "")
                    + "【カウンタ集計窓＝直近6ヶ月(採点窓)+助走60日の合計（非ML固定版は採点窓+助走のみ replay・学習/embargo/封印は走らせない）＝エンジン1走の合計・このCSVの窓だけの数字ではない・採点窓分は本レポート C節/K節の TREND_CONT を見る】〔定数継承（v21_040/v22_042 採択・v24 固定・非ML・学習窓選定なし）〕")
            else:
                _mech["uptrend 即クローズ TREND_CONT(taker)"] = (
                    f"RG-v5 上げトレンド状態機械の発火で全 lot 即クローズ＋新規/add 停止（レンジ前提の終了・risk-manager 型）"
                    f"{_fire('TREND_CONT_rg5')}"
                    + (f"・内訳 勝ち玉 ${_stats.get('TREND_CONT_rg5_win$', 0)} / 負け玉 ${_stats.get('TREND_CONT_rg5_loss$', 0)}（⑨巻き込みの実測）"
                       if _stats.get("TREND_CONT_rg5") else "")
                    + "【カウンタ集計窓＝直近6ヶ月(採点窓)+助走60日の合計（非ML固定版は採点窓+助走のみ replay・学習/embargo/封印は走らせない）＝エンジン1走の合計・このCSVの窓だけの数字ではない・採点窓分は本レポート C節/K節の TREND_CONT を見る】〔視認校正〕")
        if s15.get("v22_anchor"):                      # v22_low_anchor_tp（acceptance 2026-07-13）: TP アンカー＝レンジ下限（セル別 M）
            _mech["TP アンカー v22_low_anchor_tp(レンジ下限)"] = (
                f"セル別 M={s15['v22_anchor']}＝TP1=(建値+直近M本low)/2 で半分・TP2=直近M本low×(1+{V11_SL_BUF*100:.2f}%)（キー無しセルは現行アンカー）"
                f"・適用{_stats.get('v22_anchor_applied', 0)}／幾何防御フォールバック{_stats.get('v22_anchor_fallback', 0)}"
                "【カウンタ集計窓＝直近6ヶ月(採点窓)+助走の合計（非ML固定版）】〔定数継承（v22_042 採択・v24 固定・非ML・学習窓選定なし）〕")
        if s15.get("v22_pf"):                          # v22_peak_fold（acceptance 2026-07-13）: ピーク反転の半分 maker 畳み
            _p22 = s15["v22_pf"]
            _mech["ピーク反転畳み v22_peak_fold MFE_DRAWDOWN_CUT(maker半畳み)"] = (
                f"含み益ピーク≥{_p22['k']:g}×往復fee で武装・ピークから {_p22['r']:g} 割戻しで半分 maker 畳み（1 lot 1回・下限=建値フロア）"
                f"・形={'前兆限定（v22_uptrend_warning 中のみ）' if _p22.get('warn_only') else '常設'}"
                f"・発火{_stats.get('MFE_DRAWDOWN_CUT_pf', 0)}【カウンタ集計窓＝直近6ヶ月(採点窓)+助走の合計（非ML固定版）】〔定数継承（v22_042 採択・v24 固定・非ML・学習窓選定なし）〕")
        if s15.get("v22_warn") is not None:            # v22_uptrend_warning の shrink 前倒し（acceptance 2026-07-13）
            _mech["前兆 shrink 前倒し v22_warn(maker逃げの早駆動)"] = (
                f"v22_uptrend_warning（RG-v5 発火条件の半値水準＝A15半/D15半/C90半・確定15分足+過去close のみ）中は "
                f"deadline shrink の期限を {s15['v22_warn']} 本先へ前倒し（maker のみ・taker 強制なし・新規停止は発火時のみ）〔学習窓選定〕")
        _sec_v11 = {
            "検証期間（periods正本・E31）": {
                "学習(fit)": f"〜{TRAIN_END.date()} 未満（v11 は fit なし＝素ルール・分位選定なし）",
                "採点(公式net)": f"{SC_START.date()} 〜 {SCORE_END.date()} 未満",
                "封印(不参照)": f"{SEAL_START.date()} 以降",
            },
            "【入口】視認校正レンジ計器×到達・確認（SHORT のみ・実フラグから自動生成）": {
                # ★RG-v5 の判定ロジック全詳細（帯対・5分判定・uptrend 状態機械の発火/解除・実定数から自動生成）＝まこさん 2026-07-12
                #   report 表示は2階層まで＝「レンジ判定 range_ok_rg5・<項目>」の平坦キーで1行ずつ展開（学習ブロックと同形）
                **({f"レンジ判定 range_ok_rg5・{k}": v for k, v in _rg5_gate_desc().items()} if v20_rg5 else
                   {"レンジ判定 range_ok_v11": (
                       f"1時間足の確定 fractal スイングを過去{V11_ZONE_LOOKBACK}h(7日)窓・価格帯{V11_ZONE_TOL*100:.1f}%で束ね、"
                       f"スイング数≥{V11_ZONE_TOUCH}のS/Rゾーンが close の上下に揃い幅≥{V11_ZONE_MIN_W*100:.1f}%＝レンジ局面。"
                       "5分足で close がゾーン外（ブレイク）なら離脱＝新規候補を生成しない"
                       "（まこさん視認校正済み v17 計器と同一ロジック・labels_v17.csv 一致を selftest で機械照合・トレンド排除はゾーンが立つか否かが担う）〔視認校正〕")}),
                "エントリー": (_v22_entry_desc(s15["v22_entry"], _stats) if s15.get("v22_entry")
                            else _v21_entry_desc(s15.get("v21_entry"), _edge, _conf, _stats)),
                "方向 short_only_v11": "SHORT のみ（LONG 入口の生成経路なし・上限ゾーンのみ使用）",
            },
            "【固定値】サイズ（スキャル＝add で積み・複数TPで刻む）": {
                "予算上限": f"全建玉合計 {CAP} BTC（H1・共有枠）・本戦略の同時最大 {UNIT * V11_MAX_ADDS} BTC（{V11_MAX_ADDS} lot）",
                "size": f"{UNIT} BTC/lot・V11_MAX_ADDS={V11_MAX_ADDS}（保有中の入口条件 完全再発火で同量 add＝上限ゾーン再テストの統合・トレンド型ピラミッド不採用）",
                "指値": f"close×(1+{ENTRY_OFFSET})・TTL {TTL}本(={TTL*5}分)・不約定は建てない（maker限定）",
                "対照フラグ": f"--v11-no-add（1 lot）/ --v11-single-tp（TP2 のみ＝v10 出口）＝diagnostic 寄与分離用（no_add={v11_no_add}・single_tp={v11_single_tp}）",
            },
            "【出口】レンジ幾何・状態機械（実際に有効な枝だけ・実値から自動生成）": {
                "TP1 部分利確 PARTIAL_TP(maker指値)": f"(建値+レンジ中央)/2 で lot の半分（{UNIT/2} BTC）・TP1幅 ≥{SCALP_FLOOR*100:.2f}%（手数料床＝maker往復0.028%の約2.9倍）〔幾何a-priori〕",
                "TP2 利確 TP_FILLED(maker指値)": _tp2,
                "SL SL_FILLED(maker指値)": _sl_eff,
                "R:R の物理条件 tp_ge_sl_check_v11": "TP2幅 ≥ SL幅 ∩ TP1幅 ≥ 手数料床 でなければ建てない（逆R:R の禁止＝KB §1）",
                "時間切れ TIME_EXIT(成行taker)": f"lot の初回entryから {s15.get('tmax', T_MAX)}本 = {s15.get('tmax', T_MAX)*5}分（短保有＝分単位・lot ごと）〔{_prov.get('tmax', '学習窓選定/継承') if 'tmax' in s15 else '固定値'}〕",
                **({"deadline shrink v13 TP_FILLED(maker指値)": (
                    f"TP2 と TIME backstop の間に縮む maker TP を置く＝残り時間比 r=(T_MAX−経過本)/T_MAX（fill時 r=1＝tp2 通常／deadline で r→0）で "
                    f"tp_shrunk=tp2+(建値フロア−tp2)×(1−r)・建値フロア=avg×(1−{SCALP_FLOOR*100:.2f}%)（損ゼロ maker・手数料床を割らない）。"
                    "到達玉は maker(TP_FILLED)・未到達玉のみ 60分 成行 TIME_EXIT(taker)。E35 iter8-9 型・acceptance 2026-07-06")}
                  if v13_time_maker else {}),
                **({"★v14 Exit 状態機械（枝×玉4タイプ別の学習窓選定値・acceptance 2026-07-07）": {
                    "尺度": "進捗率 prog=(建値−価格)/(建値−レンジ中央)＝無次元（レンジ幾何で自動スケール・H6）・トリガ判定は前バーまでのピーク（H2）",
                    "枝3 MFE_DRAWDOWN_CUT(maker trigger+limit)": f"(p_arm, r)×タイプ = {v14_sel['dd']}（None=不使用・レベル下限=建値フロア）",
                    "枝4 BE_EXIT(maker trigger+limit)": f"be_arm×タイプ = {v14_sel['be']}（armed 後 建値フロアで損ゼロ級撤退）",
                    "枝5' STOCH_REVERSE_EXIT(taker成行)": f"s_arm×タイプ = {v14_sel['stoch']}（stoch(9,3) GC ∩ 含み益>0）",
                    "枝6 失速shrink前倒し": f"(n,g,T_eff)×タイプ = {v14_sel['stall']}",
                    "枝7 TIME backstop 長": f"{v14_sel['tmax']}本={v14_sel['tmax']*5}分（候補{{6,9,12}}から学習窓選定）",
                    "発火数(全期間)": f"{v14_sel.get('_stats')}",
                }} if v14_sel is not None else {}),
                **_mech,
            },
            "【学習方法・学習内容】": {
                "ML/検出器": "不使用（素ルール＝v5〜v10 の検出器経路は不変・v11 は fit なし＝分位選定なし）",
                "場面セル": ("固定 cell_fn（常に cell0＝全場面共通・非ML・学習木なし・将来 ML を足す時はここに渡す差し込み口）〔固定値〕" if s15.get("cell_fixed") else (f"LightGBM 1本の木（entry 特徴 stoch_k/ATR%/box_W → net・num_leaves≤{V16_NUM_LEAVES}）の leaf でセル分割〔学習窓のみ・L-267〕" if s15.get("cell_fn") else "なし（場面セル未使用）")),
                "選定 vs 固定": ("学習窓選定なし＝全固定値（非ML・場面別セルなし・TP2/anchor/TIME 等すべて a-priori 定数）〔固定値〕" if s15.get("cell_fixed")
                                else ("選定0回＝v17_031 採択2本を V18_FIXED_FROM_V17 で定数継承（学習窓で回さない・全 a-priori/継承）〔定数継承〕" if (s15.get("tp2_far") and not s15.get("_learning_spec"))
                                else ("学習窓 OOF 選定（本走で候補メニューから選定＝下記【学習内容/方法/合格判定】に詳細）〔学習窓選定〕" if s15.get("_learning_spec")
                                      else ("学習窓 OOF 選定（purged 3分割 合意）で枝水準を選定〔学習窓選定〕" if s15.get("cell_fn") else "学習なし（全固定 a-priori）〔固定値〕")))),
                # ★実際に学習した時（_learning_spec あり）は学習内容/方法/合格判定条件を自動描画（まこさん 2026-07-12・戦略非依存）
                **(_render_learning_block(s15["_learning_spec"]) if s15.get("_learning_spec") else {}),
                "出所タグ凡例": "〔固定値〕既存定数 /〔学習窓選定〕学習窓 OOF /〔幾何a-priori〕レンジ幾何 /〔視認校正〕まこさん校正 /〔定数継承〕過去採択の継承",
                "⚠️発火カウンタの集計窓": "本§0の発火N・カウンタ・勝ち玉/負け玉$はすべて直近6ヶ月(採点窓)+助走60日の合計（非ML固定版は採点窓+助走のみ replay・学習/embargo/封印は走らせない）＝エンジン1走の合計。このCSVの窓（train/score）だけの数字ではない。窓別の損益は本レポート C節/K節（採点窓CSVなら採点窓のみ）が正",
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
        _assert_param_schema_v11(_sec_v11)   # §0 の必須項目を物理強制（欠けたら SystemExit＝走らない）
        return _sec_v11
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


def run_e37(df, box_tf, tag=None, no_gate=False, v6=False, v6r=False, v7=False, v8=False, v9=False, v10=False, v11=False, v11_no_add=False, v11_single_tp=False, v11_open_entry=False, v12_open_range=False, v13_time_maker=False, v14_machine=False, v15_exit_set=False, v16_exit_set=False, v17_exit_set=False, v18_tp2_far=False, v19_upper_touch=False, v20_rg5=False, v21_set=False, v21_entry_only=False, v21_fold_only=False, v22_set=False, v23_trend_exit=False, v24_trend_maker_tp=False, v25_adaptive_band=False, v26_atr_gate=None, v26_touch_frac=None, v26_touch_hours=12.0, v26_split_ceiling=False, v26_gap=0.5, v26_down_hours=6.0, v26_max_age_hours=0.0, v26_ceil_buffer=0.0, v26_uptrend_exit=False, v27_flatup_lock=False, used_flags_section=None):
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
        if v20_rg5:                                    # v20: 入口ゲートを RG-v5 に差し替え（acceptance 2026-07-12 承認・LEVER）
            assert v12_open_range and v13_time_maker and v18_tp2_far and not v19_upper_touch, \
                "v20 は v18 構成（--v12-open-range --v13-time-maker --v18-tp2-far）の入口ゲート差し替え＝--v19-upper-touch と併用しない（acceptance 2026-07-12）"
            if v25_adaptive_band:                       # v25: レンジ判定の束ね幅をボラ連動に（RG-v6・acceptance 2026-07-16・LEVER）
                assert v24_trend_maker_tp, "v25 は v24 構成の上に載る（--v24-trend-maker-tp 必須・acceptance 2026-07-16）"
            _ak = V25_K if v25_adaptive_band else None   # v25 時のみ RG-v6 適応束ね幅・None=RG-v5 恒等
            df = _apply_rg5_to_5m(df, adaptive_k=_ak)
            _upn = int(df["rg5_uptrend"].sum())
            okn = int(df["range_ok_v11"].sum())
            cn = int(v11_entry_candidates(df, v11_open_entry=v11_open_entry, v12_open_range=v12_open_range, upper_touch=v19_upper_touch).sum())
            print(f"  [range_ok_rg5] {'RG-v6 適応束ね幅' if v25_adaptive_band else 'RG-v5 レンジ判定'} 通過 {okn:,}/{len(df):,} バー（{okn/len(df)*100:.1f}%）"
                  f"／uptrend {_upn:,}（{_upn/len(df)*100:.1f}%）＝帯対拡張 ∩ 5分帯内 ∩ 非uptrend"
                  f"{f'・束ね幅 tol=clamp({V25_K}×ATR%_1h,0.15%,0.6%)' if v25_adaptive_band else '（labels_rg-v5 一致は --v20-selftest-rg5）'}")
        else:
            z1h = _zones_v11_1h(df)
            df = _apply_v11_to_5m(df, z1h)
            okn = int(df["range_ok_v11"].sum())
            cn = int(v11_entry_candidates(df, v11_open_entry=v11_open_entry, v12_open_range=v12_open_range, upper_touch=v19_upper_touch).sum())
            print(f"  [range_ok_v11] レンジ判定 通過 {okn:,}/{len(df):,} バー（{okn/len(df)*100:.1f}%）"
                  f"＝1h S/Rゾーン（スイング≥{V11_ZONE_TOUCH}・幅≥{V11_ZONE_MIN_W*100:.1f}%）∩ 5分ブレイクなし")
        _in_label = "到達のみ（確認なし v12）" if v12_open_range else "到達＋拒否確認"
        print(f"  [入口候補 v11] {_in_label} {cn:,} バー（no_add={v11_no_add}・single_tp={v11_single_tp}・open_entry={v11_open_entry}・open_range={v12_open_range}）")
        v14p = None
        v15p = None
        if v18_tp2_far:                                # v18 TP2 反対側ゾーン（acceptance 2026-07-11 承認・1レバー・選定0回）
            assert v13_time_maker, "v18 は v13（deadline shrink）の上に載る（--v13-time-maker 必須・acceptance 2026-07-11）"
            assert not (v14_machine or v15_exit_set or v16_exit_set or v17_exit_set), "v18 は v17_031 構成を定数継承＝--v14/--v15/--v16/--v17 と併用しない（acceptance 2026-07-11）"
            df = _attach_v16_bb(df)                    # v16 基盤の列（ガードは空だが経路は v16 有効＝v17_031 と同一）
            # 非ML固定版（2026-07-16 まこさん・出口は固定値）: 場面分類の学習木(cell_fn)を廃止＝固定 cell_fn（常に0・1セル）。
            # 学習窓での fit（dtr18/base_tr18/_fit_v15_branch_policy）を全廃＝古い5年データを使わず直近6ヶ月だけで動く・非ML。
            # ★差し込み口(cell_fn)は残す＝将来 ML を足す時はここに学習した木を渡すだけ（py 作り変え不要・まこさん確認済）。
            base18 = {"ladder": None, "sl_far": 1.0, "tmax": 48, "down": None, "ret": {}, "dd": {}, "cell_fn": None,
                      "v16": True, "v17": True, "guard": {}, "guard_all": None, "cooldown": V16_COOLDOWN[0], "be_time": {},
                      "tmax_map": {}, "down_map": {}, "tp1_f": {}, "tp2_f": {}, "size0": {},
                      "break_mode": None, "break_bars": V15_BREAK_BARS}
            cell_fn18 = (lambda k_, a_, w_: 0); ncell18 = 1   # 固定 cell_fn＝全場面 cell0（差し込み口は維持・将来 ML 差替可）
            v15p = {k: (dict(v) if isinstance(v, dict) else v) for k, v in base18.items()}
            # 非ML固定＝固定 cell_fn(常に0)＝場面別セルなし。旧 V18_FIXED_FROM_V17（cell2/4 の dd/down_map）は cell_fn=0 で
            # cell2/4 が発生せず一度も発火しない死に枝＝空にする（挙動不変＝md5 で確認・§0 の死に枝表示を消して実態に一致させる）。
            v15p.update({"cell_fn": cell_fn18, "cell_fixed": True, "dd": {}, "down_map": {}, "tp2_far": True})
            v15p["prov"] = {"sl_far": "骨格a-priori（固定・非ML）", "tmax": "骨格a-priori（固定・非ML）"}   # §0 出所タグの実出所（表示のみ）
            print("  [v18 非ML固定] 場面分類の学習木を廃止＝固定 cell_fn(常に0・場面別セルなし)。出口は全場面共通の固定値（dd/down_map の場面別枝なし・TP2 反対側ゾーン＋v22 anchor は固定値・この上で固定値調整）")
            print(f"  [v18 レバー] TP2＝サポートゾーン上端×(1+{V11_SL_BUF}) ＝反対側ゾーンのすぐ手前（従来=レンジ中央・TP1/守り枝/入口 不変・幾何防御=非有限/中央超えは中央へフォールバック）")
        if v22_set:                                    # v22 Entry×Exit セット（acceptance 2026-07-13 承認・既定 OFF=v21_040 構成恒等）
            assert v20_rg5 and v18_tp2_far and v15p is not None, "v22 は v20/v21 構成の上に載る（--v20-rg5 --v18-tp2-far 必須・acceptance 2026-07-13）"
            assert not (v21_set or v21_entry_only or v21_fold_only), "v22 は v21 採択値を定数継承（V22_FIXED_V21_*）＝--v21-set と併用しない"
            v15p["v21_entry"] = dict(V22_FIXED_V21_ENTRY)   # v21_037/040 採択の定数継承（選定0回・V18_FIXED_FROM_V17 と同型）
            v15p["v21_fold"] = dict(V22_FIXED_V21_FOLD)
            df = v22_uptrend_warning(df)               # 前兆フラグ（確定15分足＋過去close のみ＝H2）
            if v24_trend_maker_tp:                      # v24（acceptance 2026-07-16）: v22 学習窓選定を定数化＝_select_v22_params を走らせず v22_042 採択値を継承（入口〜出口すべて固定値・学習ゼロ・まこさん指摘）
                for _k24, _v24 in V24_FIXED_V22.items():
                    v15p[_k24] = (dict(_v24) if isinstance(_v24, dict) else _v24)
                print(f"  [v24] v22 学習窓選定を定数化＝V24_FIXED_V22 継承（{V24_FIXED_V22}・cell0/M24・入口〜出口すべて固定値・学習ゼロ・_select_v22_params スキップ）")
        if v23_trend_exit or v24_trend_maker_tp:       # v23（acceptance 2026-07-15）/v24（2026-07-16）: TREND_CONT を V9 型 Exit 状態機械へ（uptrend 発火の成行投げを廃止・入口/TP は v22 据え置き・固定値・学習窓選定なし）
            assert v22_set and v15p is not None, "v23/v24 は v22 構成の上に載る（--v22-set 必須・acceptance 2026-07-15/16）"
            v15p["v23_trend_exit"] = True              # trend_caught 保持（v24 は v23 の上に載る＝uptrend 発火で保有玉を trend_caught へ）
            if v24_trend_maker_tp:                      # v24: 反転待ち STOCH_REVERSE を建値+L% の resting maker 利確に置換
                v15p["v24_trend_maker_tp"] = True
                print(f"  [v24] trend_caught 玉に建値+{V24_TREND_TP_PCT}% の resting maker 利確（TREND_CAUGHT_TP・maker）＝反転待ち STOCH_REVERSE を置換・MFE_STALE(B型止血)/災害SL/TIME 維持・稼ぐ玉不変・全固定値（既定 OFF=v23_043 恒等）")
            else:
                print("  [v23] TREND_CONT を V9 型状態機械へ＝uptrend 発火で保有 SHORT を成行投げせず、STOCH_REVERSE_EXIT(taker・stoch GC∩含み益)/MFE_STALE_CUT(taker・保有30分∩益なし)/災害SL・TIME(現行) に委ねる（MFE_DRAWDOWN_CUT・v21_fold・v22_peak_fold は不使用・既定 OFF=v22_042 恒等）")
        if v27_flatup_lock and v15p is not None:            # v27（fast-mode 2026-07-15・まこさん）: flat_up ピーク反転 建値保護を v15p に注入（§12・両窓 score.py で采否）
            v15p["v27_flatup_lock"] = True
            print(f"  [v27] flat_up 型のピーク反転 建値保護＝含み益ピークが+{V27_ARM_PCT}%到達で武装→ピーク利益の{V27_GIVEBACK*100:.0f}%戻しで MFE_DRAWDOWN_CUT(maker・下限=建値フロア)＝flat_up SL負け(含み益+0.4%→反転→−1.16%突き抜け)を建値近傍で止める（下落系は不変・1レバー・H2・H13無変更・両窓 score.py で采否）")
        if v26_atr_gate is not None and v15p is not None:   # v26（fast-mode 2026-07-15）: 入口 atr_pct 固定下限を v15p に注入（run_continuous_v11 が発火時にゲート・両窓 score.py で采否）
            v15p["v26_atr_gate"] = float(v26_atr_gate)
            print(f"  [v26] 入口 atr_pct 固定下限ゲート＝atr_pct >= {float(v26_atr_gate):.3f}% でのみ建てる（低ボラ薄利を止め TP幅ある高ボラ場面に寄せる・固定値・H2・両窓 score.py で采否）")
        if v26_touch_frac is not None and v15p is not None:   # v26（fast-mode 2026-07-15・まこさん）: 天井で売る＝直近レンジ上端寄りフィルタを v15p に注入
            v15p["v26_touch_frac"] = float(v26_touch_frac); v15p["v26_touch_hours"] = float(v26_touch_hours)
            print(f"  [v26] 天井で売る＝直近{float(v26_touch_hours):.0f}hレンジの上端寄り pos>={float(v26_touch_frac):.2f} でだけ建てる（急落後も直近レンジに追従＝張り付いた古いレジを使わない・下端エントリー禁止・H2・両窓 score.py で采否）")
        if v26_split_ceiling and v15p is not None:            # v26（fast-mode 2026-07-15・まこさん）: レンジ2タイプ切り分け＋天井に売り指値を v15p に注入
            v15p["v26_split"] = True; v15p["v26_gap"] = float(v26_gap); v15p["v26_down_hours"] = float(v26_down_hours)
            v15p["v26_max_age_hours"] = float(v26_max_age_hours); v15p["v26_ceil_buffer"] = float(v26_ceil_buffer)
            print(f"  [v26] レンジ切り分け＝下落系(価格がレジ帯下端より{float(v26_gap):.1f}%以上下→天井=直近{float(v26_down_hours):.0f}h高値)／平坦上昇系(→天井=res_hi) に売り指値を置いて待つ（下がる足で仕掛けない・H2・両窓 score.py で采否）"
                  + (f" ＋A: レンジ判定直後{float(v26_max_age_hours):.1f}h以内のみ建てる（上昇転換巻き込み回避）" if v26_max_age_hours > 0 else "")
                  + (f" ＋天井バッファ {float(v26_ceil_buffer):.2f}%＝売り指値を天井×(1-{float(v26_ceil_buffer):.2f}%)へ下げ上端手前で止まるレンジを拾う（現値未満にはしない）" if v26_ceil_buffer > 0 else ""))
        if v26_uptrend_exit and v15p is not None:             # v26 B（まこさん 2026-07-15）: uptrend 発火で緊急離脱
            v15p["v26_uptrend_exit"] = True
            print(f"  [v26] B: uptrend レジーム発火で保有玉を緊急離脱（成行 TREND_CONT）＝時間切れ大損の前に頭打ち（v23/v24 の trend_caught 保持より優先・両窓 score.py で采否）")
        trades = run_continuous_v11(df, box_tf, no_add=v11_no_add, single_tp=v11_single_tp, v11_open_entry=v11_open_entry, v12_open_range=v12_open_range, v13_time_maker=v13_time_maker, v14_params=v14p, v15_params=v15p, v19_upper_touch=v19_upper_touch,
                                    v20_uptrend=(df["rg5_uptrend"].to_numpy(bool) if v20_rg5 else None))
        if v14p is not None:
            print(f"  [v14 発火（全期間・full CSV 基準）] {v14p.get('_stats')}")
        if v15p is not None:
            print(f"  [v15 発火（全期間・full CSV 基準）] {v15p.get('_stats')}")
        t = pd.DataFrame(trades)
        if len(t):
            t["entry_time"] = pd.to_datetime(t["entry_time"]); t["exit_time"] = pd.to_datetime(t["exit_time"])
            mx = _verify_cap(trades)
            print(f"  [自己検査 cap] 同時保有 max {mx:.4f} BTC ≤ {CAP}: {'✅' if mx <= CAP + 1e-9 else '⛔cap 超過'}")
            assert mx <= CAP + 1e-9, "cap 0.12 超過（H1 違反）"
            assert (t["size_btc"] >= ee.MIN_ORDER_BTC).all(), "最小注文サイズ違反（H9・PARTIAL_TP 半 lot 含む）"
        sfx = "_v11" + ("na" if v11_no_add else "") + ("st" if v11_single_tp else "") + ("oe" if v11_open_entry else "") + ("or" if v12_open_range else "") + ("tm" if v13_time_maker else "") + ("xm" if v14_machine else "") + ("xs" if v15_exit_set else "") + ("x6" if v16_exit_set else "") + ("x7" if v17_exit_set else "") + ("x8" if v18_tp2_far else "") + ("x9" if v19_upper_touch else "") + ("r5" if v20_rg5 else "") + ("s21" if v21_set else "") + ("s21e" if v21_entry_only else "") + ("s21f" if v21_fold_only else "") + ("s22" if v22_set else "")
        _out(t, f"_{box_tf}{sfx}", None, tag=tag, gate_on=True, v11=True, v11_no_add=v11_no_add, v11_single_tp=v11_single_tp, v13_time_maker=v13_time_maker, v14_sel=v14p, v15_sel=v15p, v11_open_entry=v11_open_entry, v12_open_range=v12_open_range, v19_upper_touch=v19_upper_touch, v20_rg5=v20_rg5, used_flags_section=used_flags_section)
        return


def _out(t: pd.DataFrame, suffix: str, det, tag=None, gate_on=True, v6=False, v6r=False, v7=False, v8=False, v9=False, v10=False, v11=False, v11_no_add=False, v11_single_tp=False, v13_time_maker=False, v14_sel=None, v15_sel=None, v11_open_entry=False, v12_open_range=False, v19_upper_touch=False, v20_rg5=False, used_flags_section=None) -> None:
    strat_base._output_and_report(
        t, suffix, stem="e37_range_scalp",
        strategy=("E37 v21 入口の反転確認（armed DC）＋uptrend 畳み分岐（Entry×Exit セット・v20 RG-v5 の上・v18 Exit 継承）" if ((v15_sel or {}).get("v21_entry") is not None or (v15_sel or {}).get("v21_fold") is not None)
                  else "E37 v20 RG-v5 レンジ判定移植＋レンジ期間を漏れなく取る上端入口（uptrend 即クローズ・v18 Exit 継承）" if v20_rg5
                  else "E37 v17 選定の regime 頑健化（ATR%帯 層化OOF合意＋勝ち玉保護＋ガード全セル候補×box_W膨張）" if (v15_sel or {}).get("v17")
                  else "E37 v16 Entry×Exit セット最適化 第2弾（回帰救済×トレンドガード×候補格子の一括OOF・場面セル×玉タイプ×purged OOF 選定）" if (v15_sel or {}).get("v16")
                  else "E37 v15 Entry×Exit セット最適化 第1弾（逆行側分岐＝ラダー/戻り決済/構造破れ/4h backstop＋枝×場面セル別 学習窓選定）" if v15_sel is not None
                  else "E37 v14 Exit ポジション状態機械（レンジ幾何ネイティブ・玉4タイプ別 学習窓選定・基本 maker）" if v14_sel is not None
                  else "E37 v11 視認校正レンジ計器の組み込み（1h S/Rゾーン×5分ブレイク離脱×複数TP+add・SHORT のみ）" if v11
                  else "E37 v10 ゾーン方式レンジスキャル SHORT（§1.2.1 準拠 MVP・タッチ実績ゾーン×拒否確認・ML 不使用）" if v10
                  else "E37 v9 レンジ・スキャル 両側 maker MR＋型×side Entry/Exit セット共同選定（フェーズ1）" if v9
                  else "E37 v8 レンジ・スキャル 両側 maker MR＋型×side 検出器（選定計器の是正＝母数一致・side別be・型相互排他）" if v8
                  else "E37 v7 レンジ・スキャル 両側 maker MR＋型別検出器（帯の合併＋TP-viability）" if v7
                  else "E37 v6r レンジ・スキャル 両側 maker MR＋検出器ゲート（金額整合回帰＋TP-viability）" if v6r
                  else "E37 v6 レンジ・スキャル 両側 maker MR＋検出器ゲート（イベント5型＋θ規則反転）" if v6
                  else "E37 v5 レンジ・スキャル 両側 maker MR＋稼げるレンジ検出器ゲート"),
        script="e37_scalp.py",
        sections={**_param_sections(det, gate_on, v6=v6, v6r=v6r, v7=v7, v8=v8, v9=v9, v10=v10, v11=v11, v11_no_add=v11_no_add, v11_single_tp=v11_single_tp, v13_time_maker=v13_time_maker, v14_sel=v14_sel, v15_sel=v15_sel, v11_open_entry=v11_open_entry, v12_open_range=v12_open_range, v19_upper_touch=v19_upper_touch, v20_rg5=v20_rg5),
                  **(used_flags_section or {})},   # ＋argparse 由来の使用フラグ全量（自動生成＝入口/出口ロジックの実フラグを漏れなく載せる・強制hook不要で正確・まこさん 2026-07-15）
        tag=tag)


def _load(smoke: int) -> pd.DataFrame:
    df = load_5m(smoke)
    if smoke == 0:                                # 非ML固定ルール＝本走は直近6ヶ月(採点窓)＋助走60日だけ処理（5年 replay 廃止・periods.py で切る・手打ちなし）
        _warm = SC_START - pd.Timedelta(days=60)  # 助走60日（RG-v5 168h=7日・各指標 rolling を満たす a-priori）＝この前は不要（学習窓を作らない）
        df = df[df["ts"] >= _warm].reset_index(drop=True)
    df = e34v1.add_indicators(df)                 # sma/std/dev_z/atr/adx
    df = e34b.add_analysis_features(df)           # rsi/stoch_k（記録用）
    df = e35_box.add_box_features(df, verify_leak=(smoke > 0 and smoke <= 60000))   # box_W 記録用
    df["atr_pct"] = df["atr"] / df["close"] * 100.0
    return df


def _diagnostic(df, v6=False, v6r=False, v7=False, v8=False, v10=False, v11=False, v11_open_entry=False, v12_open_range=False, v19_upper_touch=False, v20_rg5=False, v25_adaptive_band=False):
    """発火ファネル（採点しない）＝イベント頻度のみ（検出器は本走で学習＝重い処理を diagnostic で回さない）。"""
    if v11:
        df = _rsi9_v10(df)
        if v20_rg5:                                    # v20: RG-v5 ゲート（acceptance 2026-07-12）
            df = _apply_rg5_to_5m(df, adaptive_k=(V25_K if v25_adaptive_band else None))   # v25: RG-v6 適応束ね幅
        else:
            z1h = _zones_v11_1h(df)
            df = _apply_v11_to_5m(df, z1h)
        n = len(df)
        days = max((df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds() / 86400.0, 1.0)
        ok = df["range_ok_v11"].to_numpy(bool)
        cand = v11_entry_candidates(df, v11_open_entry=v11_open_entry, v12_open_range=v12_open_range, upper_touch=v19_upper_touch)
        adx = df["adx"].to_numpy(float)
        print("=" * 100)
        print(f"[E37 {'v20(RG-v5)' if v20_rg5 else 'v11'} 発火ファネル診断・採点しない] {n:,}本 / {days:.0f}日")
        if v20_rg5:
            _up = df["rg5_uptrend"].to_numpy(bool)
            print(f"  range_ok_rg5 通過率  : {ok.mean()*100:.1f}%（帯対拡張 ∩ 5分帯内 ∩ 非uptrend）／uptrend {_up.mean()*100:.1f}%（新規停止＋保有即クローズ）")
        else:
            print(f"  range_ok_v11 通過率  : {ok.mean()*100:.1f}%（1h S/Rゾーン スイング≥{V11_ZONE_TOUCH}・幅≥{V11_ZONE_MIN_W*100:.1f}% ∩ 5分ブレイクなし・v10 実績 53.1% と比較）")
        _lbl = ("到達のみ（確認なし v12）" if v12_open_range
                else ("到達＋拒否確認（過熱必須なし）" if v11_open_entry else "到達＋拒否確認"))
        if v19_upper_touch:
            _lbl += "・上端 res_hi 到達"                # 実フラグから分岐（run_e37 と同一の表示規則・誤ラベル是正 2026-07-12）
        print(f"  入口候補（{_lbl}）: {int(cand.sum()):,} 本（{cand.sum()/days:.2f}/日）")
        if cand.sum():
            adx_c = adx[cand]
            fin = np.isfinite(adx_c)
            print(f"  入口候補の ADX40+ 混入 : {(adx_c[fin] >= 40).mean()*100:.1f}%（v10 実績 38.5% と比較＝トレンド排除の実効）")
            w = (df.loc[cand, "v11_res_lo"] - df.loc[cand, "v11_sup_hi"]) / df.loc[cand, "close"] * 100
            print(f"  （参考）候補バーのゾーン幅: median {np.nanmedian(w):.3f}%（TP1/TP2 2段の手数料床 2×{SCALP_FLOOR*100:.2f}% と比較）")
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
    ap.add_argument("--v11-open-entry", action="store_true", help="v11 Step1 Do: 入口の過熱を必須にする確認（rsi9_prev>70）を撤去＝反転確認だけで入る（過熱fadeで負ける方向選別をやめ件数を戻す・acceptance 2026-07-05・既定OFF=v11恒等）")
    ap.add_argument("--v12-open-range", action="store_true", help="v12: 入口の拒否確認（陰転∩RSI9下向き）を外し range_ok_v11∩上限ゾーンのみで SHORT＝レンジ上部で確認なしに件数を出す（方向選別しない・Exit は次段・acceptance 2026-07-06・既定OFF=v11oe恒等）")
    ap.add_argument("--v13-time-maker", action="store_true", help="v13 Step2: TP2 と TIME backstop の間に deadline 型 縮む maker TP を置く＝TIME 域の玉を成行taker でなく残り時間比 r で建値側へ縮む maker指値(TP_FILLED)で取り切る（建値フロア=avg×(1-SCALP_FLOOR)・E35 iter8-9 型・acceptance 2026-07-06・既定OFF=v12恒等）")
    ap.add_argument("--v14-exit-machine", action="store_true", help="v14: Exit ポジション状態機械（枝3 MFE_DRAWDOWN_CUT トレーリングmaker／枝4 BE_EXIT 建値フロアmaker／枝5' STOCH_REVERSE_EXIT taker／枝6 失速shrink前倒し／枝7 backstop長{30,45,60分}選定・水準=進捗率・玉4タイプ別に学習窓のみで逐次選定・--v13-time-maker 必須・acceptance 2026-07-07・既定OFF=v13恒等）")
    ap.add_argument("--v14-guard-check", action="store_true", help="v14 番人メタ確認: 枝別極端値で exit_reason 分布が枝支配になるか（配線証明・採点しない・--smoke 併用）")
    ap.add_argument("--v15-exit-set", action="store_true", help="v15: Entry×Exit セット最適化 第1弾＝逆行側分岐の作り直し（add ラダー同予算0.012×4／戻り決済 BE_EXIT／構造破れ RANGE_BREAK_EXIT＋災害SL／4h backstop+down_factor）＋枝水準の場面セル（LightGBM 木）×玉タイプ別 学習窓選定（purged 3分割 OOF 合意・--v13-time-maker 必須・--v14-exit-machine と併用不可・acceptance 2026-07-07・既定OFF=v14恒等）")
    ap.add_argument("--v15-guard-check", action="store_true", help="v15 番人メタ確認: 枝別極端値（ラダー/戻り決済/災害SL/破れ/down/dd）で exit_reason 分布が枝支配になるか（配線証明・採点しない・--smoke 併用）")
    ap.add_argument("--v16-exit-set", action="store_true", help="v16: Entry×Exit セット最適化 第2弾＝回帰救済×トレンドガード×候補格子の一括 OOF（トレンド移行ガード[変位k×W/BB拡大→TREND_CONT再利用]／BE arm帯+時間arm／TIME場面連動／ladder rung 0.25-0.5×W／TP1/TP2位置比率／破れ建玉基準カウント／セル別新規size配分・場面セル木 leaves≤6×玉タイプ×purged 3分割 OOF 合意・--v13-time-maker 必須・--v14/--v15 と併用不可・acceptance 2026-07-07・既定OFF=v15恒等）")
    ap.add_argument("--v16-guard-check", action="store_true", help="v16 番人メタ確認: 枝別極端値（ガードdisp/bb・時間arm・tmax_map・rung・tp1_f・size0・破れanchor）で exit_reason 分布が枝支配になるか（配線証明・採点しない・--smoke 併用）")
    ap.add_argument("--v17-exit-set", action="store_true", help="v17: 選定の regime 頑健化＝OOF 合意区間を時間3分割から学習窓内 ATR%帯の層化分割へ（低ボラ2帯でも純増∩各帯非悪化∩PARTIAL_TP 非毀損の候補だけ採択＝v17_band_consensus）＋ガード全セル一律候補（guard_global_v17）＋box_W 膨張検知（boxw_expand_guard_v17・TREND_CONT 再利用）・--v13-time-maker 必須・--v14/--v15/--v16 と併用不可・acceptance 2026-07-07 承認 b9a9c702・既定OFF=v16恒等")
    ap.add_argument("--v17-guard-check", action="store_true", help="v17 番人メタ確認: 層化合意の既知答え（帯赤字混入=不採択/低ボラ非改善=不採択/PARTIAL毀損=不採択）＋boxw 膨張境界＋guard_all 配線支配（採点しない・--smoke 併用）")
    ap.add_argument("--v18-tp2-far", action="store_true", help="v18: TP2 をレンジ中央から反対側＝サポートゾーン上端×(1+V11_SL_BUF) のすぐ手前へ伸ばす（伸びる玉は伸ばす・TP1/守り枝/入口 不変・v17_031 採択2本を V18_FIXED_FROM_V17 で定数継承＝選定0回・--v13-time-maker 必須・--v14〜--v17 と併用不可・acceptance 2026-07-11 承認・既定OFF=v17恒等）")
    ap.add_argument("--v18-guard-check", action="store_true", help="v18 番人メタ確認: TP2 反対側の配線証明（極端バッファで全玉フォールバック＝恒等へ退行するか／通常バッファで applied が支配か・採点しない・--smoke 併用）")
    ap.add_argument("--v19-upper-touch", action="store_true", help="v19: 入口の到達を帯の下端(res_lo)から帯の上端(res_hi=本当のレジスタンス)へ＝上端まで上がる逆行を抱えず入る（R:R構造改善・跳ね返り確認や出口/サイズ/決済は不変・v18の上に載る・acceptance 2026-07-12 承認・既定OFF=v18恒等）")
    ap.add_argument("--v20-rg5", action="store_true", help="v20: 入口ゲートを RG-v5（視認校正3巡・帯対拡張＋上げトレンド状態機械・build_regime_gate_rg.py を import 再利用）に差し替え＝レンジ中の上端ゾーン到達で漏れなく建て、uptrend 発火で新規停止＋保有 TREND_CONT 即クローズ。v18 構成の上（--v12-open-range --v13-time-maker --v18-tp2-far 必須・--v19-upper-touch 併用不可・acceptance 2026-07-12 承認・既定OFF=v19恒等）")
    ap.add_argument("--v20-selftest-rg5", action="store_true", help="v20 自己検査: 戦略内 RG-v5 判定（1h帯・zone_ok・uptrend・5分ラベル）が labels_rg-v5.csv／predictions_rg-v5_5m と全期間一致するか機械照合して終了")
    ap.add_argument("--v20-guard-check", action="store_true", help="v20 番人メタ確認: uptrend 強制で入口 veto/即クローズが配線支配になるか＋labels 改ざんで selftest が停止するか（採点しない・--smoke 併用推奨）")
    ap.add_argument("--v21-set", action="store_true", help="v21: 入口の反転確認（到達で武装し stoch(9,3) デッドクロス発生バーで建てる・RSI9帯/武装期限/セル別要否は学習窓の層化合意で選定・件数床 4.33/日）＋uptrend 発火時の畳み分岐（即taker 1択から fold=deadline shrink 前倒しの maker 逃げ[期限で TREND_CONT taker]／切迫のみ即taker をセル×深さ別に学習窓選定）の Entry×Exit セット。v20 構成の上（--v20-rg5 --v18-tp2-far 必須・acceptance 2026-07-12 承認・既定OFF=v20恒等）")
    ap.add_argument("--v21-entry-only", action="store_true", help="v21 対照: 入口確認（armed DC）だけ選定・畳み分岐は v20 のまま＝寄与分離用")
    ap.add_argument("--v21-fold-only", action="store_true", help="v21 対照: 畳み分岐（fold/taker）だけ選定・入口は v20 のまま（到達即）＝寄与分離用")
    ap.add_argument("--v21-guard-check", action="store_true", help="v21 番人メタ確認: DC 全 False 強制で入口 0（配線支配）／fold 全 taker で v20 恒等 hash／labels 改ざんで selftest 停止（採点しない・--smoke 併用推奨）")
    ap.add_argument("--v22-set", action="store_true", help="v22: レンジ中の戻り売り DC 入口（range_ok_rg5 ∩ stoch(9,3) デッドクロス発生バー・到達武装との対決を学習窓選定）×TP アンカー=レンジ下限（直近 M 本押し安値・セル別 M 選定）＋ピーク反転畳み常設（k×fee 武装・r 割戻し・半分 maker）＋uptrend 前兆 warning で shrink 前倒し、の Entry×Exit セット。v21 採択値は定数継承（--v20-rg5 --v18-tp2-far 必須・--v21-set と併用不可・acceptance 2026-07-13 承認・既定 OFF=v21_040 構成恒等）")
    ap.add_argument("--v22-guard-check", action="store_true", help="v22 番人メタ確認: DC 全 False で v22 入口 0／anchor M=1 で床が全拒否／pf r 極端値で MFE_DRAWDOWN_CUT 支配／OFF 恒等（採点しない・--smoke 併用推奨）")
    ap.add_argument("--v23-trend-exit", action="store_true", help="v23: TREND_CONT の V9 型 Exit 状態機械化＝uptrend 発火で保有 SHORT を成行投げ（TREND_CONT 即taker）せず trend_caught として保持し、STOCH_REVERSE_EXIT(taker・stoch(9,3) GC∩含み益ピーク≥往復fee)／MFE_STALE_CUT(taker・保有30分∩含み益ピーク<往復fee)／災害SL・TIME(現行)の優先順位つき状態機械へ委ねる。MFE_DRAWDOWN_CUT(trailing)・v21_fold・v22_peak_fold は v23 中は不使用。固定値は V9 実証 a-priori・学習窓選定なし・入口 armed DC/TP 据え置き（--v22-set 必須・acceptance 2026-07-15 承認・既定 OFF=v22_042 構成恒等）")
    ap.add_argument("--v23-guard-check", action="store_true", help="v23 番人メタ確認: OFF 恒等 md5(v22_042 一致)／uptrend 全True で TREND_CONT 即taker 0＝新設枝へ／stoch GC 全False で STOCH_REVERSE 0／MFE_STALE gate 極大で全 trend_caught 即 stall cut（採点しない・--smoke 併用推奨）")
    ap.add_argument("--v24-trend-maker-tp", action="store_true", help="v24: trend_caught 玉（uptrend 発火で畳む玉）に建値+0.08%（V24_TREND_TP_PCT）の resting maker 利確（TREND_CAUGHT_TP・maker）を優先枝で置き、反転待ち STOCH_REVERSE_EXIT を置換（速い5分レンジで遅行し取り逃すため）。MFE_STALE_CUT(B型止血)・災害SL・TIME は維持・稼ぐ玉は不変。v22 学習窓選定も V24_FIXED_V22 で定数化＝入口〜出口すべて固定値（学習ゼロ）。L=0.08% は a-priori（手数料床∩MFE較正∩両窓crude∩学術Leung&Li）・学習窓選定なし（--v22-set 必須・acceptance 2026-07-16 承認・既定 OFF=v23_043 恒等）")
    ap.add_argument("--v25-adaptive-band", action="store_true", help="v25: レンジ判定 range_ok_rg5 の束ね幅をボラ連動にする（RG-v6・tol=clamp(0.5×ATR%_1h[V25_K],0.15%,0.6%)・build_regime_gate_rg._adaptive_tol_1h）＝平坦は帯が鋭く res_lo が真の抵抗に近づく[下弦是正]／高ボラはスイングが束なってゾーンが立つ[高ボラレンジを拾う・頻度維持]。入口の到達/armed DC・件数・出口は v24 据え置き（1レバー・K は幾何指標 diag＋まこさん視認校正で選定＝採点窓 net 不参照・L-267 非該当）。--v24-trend-maker-tp 必須・acceptance 2026-07-16 承認・既定 OFF=v24_044 恒等")
    ap.add_argument("--v26-atr-gate", type=float, default=None, help="v26（fast-mode 2026-07-15）: 入口に atr_pct 固定下限ゲートを課す＝atr_pct(=atr14/close×100) >= 指定値 の場面でだけ建てる。低ボラ薄利（v25 採点窓 atr<0.15 で入口70%・全帯 net マイナス）を止め、TP幅が実在する高ボラ場面（atr≥0.3 が唯一 net プラス）に寄せる。建て時点 atr[i]/c[i]＝H2。固定値・学習窓選定なし・両窓 score.py で采否（採点窓を覗いて閾値を選ばない＝L-320）。--v24-trend-maker-tp 必須・既定 None=v25 恒等")
    ap.add_argument("--v26-touch-frac", type=float, default=None, help="v26（fast-mode 2026-07-15・まこさん）: 天井で売る＝直近レンジ（--v26-touch-hours 窓の高安）の上端寄り pos=(close-直近安値)/(直近高値-直近安値) >= F でだけ建てる。急落後も直近レンジは価格に追従＝張り付いた古いレジスタンスを使わず、下端エントリー（ショートなのに安い所で売る）を止める。H2（直近高安は当該バー確定値）。既定 None=v22 恒等")
    ap.add_argument("--v26-touch-hours", type=float, default=12.0, help="v26: 直近レンジ窓の長さ（時間・既定12h＝144本）。--v26-touch-frac と併用")
    ap.add_argument("--v26-split-ceiling", action="store_true", help="v26（fast-mode 2026-07-15・まこさん）: レンジを2タイプに切り分けて天井に売り指値を置いて待つ。下落系レンジ（価格がレジ帯下端より --v26-gap%% 以上下＝急落後でレジが上に張り付き）は天井＝直近高値（--v26-down-hours の短窓＝急落除外）／平坦・上昇系レンジは天井＝システムのレジスタンス res_hi。価格が天井まで上がってきたら約定（resting maker sell）＝下がる足で仕掛けて約定しない問題を回避。既定 OFF=v22 恒等")
    ap.add_argument("--v26-gap", type=float, default=0.5, help="v26 切り分け: 下落系判定のしきい値%%（価格がレジ帯下端より何%%下なら下落系＝レジ張り付き・既定0.5）")
    ap.add_argument("--v26-down-hours", type=float, default=6.0, help="v26 切り分け: 下落系の天井=直近高値の窓（時間・急落を除くため短め・既定6h）")
    ap.add_argument("--v27-flatup-lock", action="store_true", help="v27（fast-mode 2026-07-15・まこさん）: flat_up 型（天井=res_hi でショート）の玉に「ピーク反転 建値保護」を足す。軌跡分析（§12）＝flat_up の SL 負けは建てた直後は勝ち玉とそっくり（含み益+0.4%まで乗る）だが、その後40分かけて反転し −1.16% まで突き抜けて SL になるピーク反転型。含み益ピークが建値+0.15%(V27_ARM_PCT)に達したら武装し、ピーク利益の50%(V27_GIVEBACK)を戻したら登録済み MFE_DRAWDOWN_CUT(maker・下限=建値フロア=損ゼロ級)で確定＝深いSLの前に建値近傍で止める。下落系は不変（1レバー）。新 exit_reason なし=score.py 無変更(H13)。既定 OFF=v26 恒等・両窓 score.py で采否")
    ap.add_argument("--v26-max-age-hours", type=float, default=0.0, help="v26（A・まこさん 2026-07-15）: レンジ判定直後に入る＝range_ok が立ってからの経過がこの時間内のバーだけ建てる（序盤ほど上昇転換まで余裕＝勝てる／時間が経ってからの入口は上昇レジームに巻き込まれ損）。0=制限なし（恒等）")
    ap.add_argument("--v26-ceil-buffer", type=float, default=0.0, help="v26（まこさん 2026-07-15「指定レンジも入れるように調整しろ」）: 天井の売り指値を 天井×(1-buffer%%) へ下げる。価格が上端手前で止まって約定しないレンジ（W1=遠いres_hi/W2=直近高値に僅か届かず）を拾う。現値+offset 未満には下げない（maker 成立）。既定 0=v26 恒等・采否は両窓 score.py")
    ap.add_argument("--v26-uptrend-exit", action="store_true", help="v26（B・まこさん 2026-07-15）: uptrend レジーム発火で保有玉を緊急離脱（成行 TREND_CONT）＝trend_caught 保持で時間切れ大損する前に損害頭打ち（v23/v24 の保持より優先・既定 OFF=保持のまま恒等）")
    ap.add_argument("--v11-selftest-zones", action="store_true", help="v11 自己検査: _zones_v11_1h が labels_v17.csv（視認校正済み計器）と全期間一致するか機械照合して終了")
    ap.add_argument("--param-schema-selftest", action="store_true", help="§0 使用パラメータ 自動生成の既知答えテスト＋番人（導出の正しさ＋項目削除の物理禁止）を実行して終了・採点しない・データ不要")
    ap.add_argument("--tag", default=None, help="実験タグ。指定で出力名を _<tag>_<NNN> 連番にし旧実験を archive へ退避（実験は必ず付ける）")
    a = ap.parse_args()
    if a.param_schema_selftest:              # §0 自動生成の既知答えテスト＋番人（データ不要・採点しない）
        _param_schema_selftest()
        return
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
    if a.v20_selftest_rg5:
        rg5_selftest_labels(df)
        return
    if a.v20_guard_check:
        _v20_guard_check(df)
        return
    if a.v18_guard_check:
        _v18_guard_check(df, a.box_tf)
        return
    if a.diagnostic:
        _diagnostic(df, v6=a.v6, v6r=a.v6r, v7=a.v7, v8=(a.v8 or a.v9), v10=a.v10, v11=a.v11, v11_open_entry=a.v11_open_entry, v12_open_range=a.v12_open_range, v19_upper_touch=a.v19_upper_touch, v20_rg5=a.v20_rg5, v25_adaptive_band=a.v25_adaptive_band)
        return
    run_e37(df, a.box_tf, tag=a.tag, no_gate=a.no_gate, v6=a.v6, v6r=a.v6r, v7=a.v7, v8=a.v8, v9=a.v9, v10=a.v10,
            v11=a.v11, v11_no_add=a.v11_no_add, v11_single_tp=a.v11_single_tp, v11_open_entry=a.v11_open_entry, v12_open_range=a.v12_open_range, v13_time_maker=a.v13_time_maker, v14_machine=a.v14_exit_machine, v15_exit_set=a.v15_exit_set, v16_exit_set=a.v16_exit_set, v17_exit_set=a.v17_exit_set, v18_tp2_far=a.v18_tp2_far, v19_upper_touch=a.v19_upper_touch, v20_rg5=a.v20_rg5,
            v21_set=a.v21_set, v21_entry_only=a.v21_entry_only, v21_fold_only=a.v21_fold_only, v22_set=a.v22_set,
            v23_trend_exit=a.v23_trend_exit, v24_trend_maker_tp=a.v24_trend_maker_tp, v25_adaptive_band=a.v25_adaptive_band,
            v26_atr_gate=a.v26_atr_gate, v26_touch_frac=a.v26_touch_frac, v26_touch_hours=a.v26_touch_hours,
            v26_split_ceiling=a.v26_split_ceiling, v26_gap=a.v26_gap, v26_down_hours=a.v26_down_hours,
            v26_max_age_hours=a.v26_max_age_hours, v26_ceil_buffer=a.v26_ceil_buffer, v26_uptrend_exit=a.v26_uptrend_exit,
            v27_flatup_lock=a.v27_flatup_lock,
            used_flags_section=_used_flags_section(ap, a))   # report §0 に実際に使った全フラグ＋help を自動列挙（強制hook不要で正確・まこさん 2026-07-15）
    print("=" * 100)


if __name__ == "__main__":
    main()
