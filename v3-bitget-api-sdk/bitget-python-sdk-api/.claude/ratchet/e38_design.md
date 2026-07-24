<!-- DESIGN_HASH=2efb0a0eba7edd99 -->
# e38_design.md — E38 優先度スタック 設計書（gen_design.py 機械生成＝手書き禁止）

生成元: e38_logics.json（ロジック定義の正本・sha256=077311789b92473b）＋ e38_requirements.json ＋ 段0 実測（worklog 逐語）。
再生成: python3 scripts/priority_rebuild/gen_design.py --write ／ 改変検出: --verify
⚠️ 本ファイルの手書き編集は禁止。変更は e38_logics.json（値）または gen_design.py（型・まこさん承認）を直して再生成。
⚠️ 設定 json が設計書の中核であり実装データそのもの（e38_requirements.json decisions）＝本書の flags/const は json の逐語ダンプ。

## 1. 要件（逐語・正本 e38_requirements.json）

> ロング・ショート共に、もっとトレード数を増やして、
> ロングとショートそれぞれのEntry/Exitで一番安定して稼げるロジック（指標、閾値、時間軸、パラメータ）を見つけて、
> それをロングとショートそれぞれの優先度１とし、優先度高くエントリーさせるようにする、
> その次を２番目さらに次を３番目、４番目と続くみたいな構成にしたらどうだろう。
> e38に切り替えて、ソースコードもスッキリさせたほうがいいのでは？
> フローはこのあと決めて、固定化して、そのとおりに進められるようにする。
> 設計書も作成したら承認をとる、その設計書と実装データが違わないようにする。

目的: E38＝レンジ・両方向・スキャル。ロング/ショート各サイドの複数ロジックを優先度スタックで並立させ、トレード数を増やしながら安定した net を作る。当面のマイルストーン＝E36+E37/E38 合算 月 net $600（台帳）。

## 2. 確定事項（まこさん決定・逐語）

- E38 新設（E37 の一枚岩 2900 行へは挿し込まない・部品は import 再利用・v59d_164 は採用土台として残す＝E38 が採点窓で超えたら乗り換え）
- 設定駆動＝ロジック定義（入口条件・出口値・優先度・スロット）は設定ファイルが正本・エンジンは設定を解釈する固定部品（設計書と実装の差異を構造的に消す・V9 cat_params_v9.json と同じ思想）
- 安定の物差し＝探索窓で成績良好 ∩ 採点窓4ヶ月全月プラス。ただしロジック個別の確認は探索側期間の分割で行い、採点窓は統合最終形1つの採否だけに使う（採点窓の覗き見禁止）
- 件数/日は成績表の一級列（稼げても件数が出ないロジックは上位にしない）
- 優先度はスロット配分＋発火競合時に若い番号優先で効かせる
- DESIGN_CONTRACT（verify_design_contract.py・実行前機械照合）を E38 設計書に適用する
- 設計書は手書きしない＝骨格をロジック設定 json＋段0 実測から機械生成する（gen_flow/観察器 --plan と同じ思想・CC が自由記述で埋める箇所を最小化）。設定駆動により『設計書を書くと実装データもできる』は生成の向きごと消える＝設定 json が設計書の中核であり実装データそのもの
- フローは本ファイル＋gen_flow.py で固定生成＝CC はフローを手書き・再発明しない
- 段2 の窓構成（まこさん決定 2026-07-24・正本 window_similarity_ranking.md）＝値決め: 探索窓 2024-04〜07 の全期間を目的関数に（構造類似2位・距離1.78）／確認: 2025-12〜2026-02（8位相当・距離2.26・採点窓直前3ヶ月・v59d が採点窓へ移った実績窓）を選んだ値のまま1回走らせ表示のみ＝確認窓の成績で選び直さない／採点: 2026-03〜06 は段5 の統合最終形1つだけ（不変）。注意＝確認窓は S1 現行値 #189 を選んだ窓＝S1 現行値との比較では現行値に地の利がある

## 3. 制約（全段共通・逐語）

- H1: 予算 0.12 BTC は全採用戦略の共有枠（E38 単独 CSV の cap は単独測定・本番は合算）
- H2: leak なし＝当該バーまでの確定値のみ・決済後の情報をシグナルに使わない
- §8.6: E38 はスキャル＝件数/日 5 が絶対下限・尻すぼみ禁止・本来目標は1時間に約5件
- fast-mode: 采否は採点窓 score.py の審判値のみ・学習窓/precheck/L-320 を持ち込まない
- L-267: 採点窓 net を目的関数にした値選びの禁止（探索の目的関数窓はまこさんが決める）
- L-330: 疑似シミュ・観察の数字はあたり付けのみ＝候補選定は実エンジン探索・采否は採点窓
- L-352: 入口フィルタで負け玉の群だけを消すのは不可能（両半期プラス0行の実測）
- 窓・値の水準・優先度の確定はまこさんのみが決める
- 金額は機械出力の逐語のみ（enforce_no_false_report）

## 4. 検証期間（数値は正本から・本書に手打ちしない）

- 採点窓（采否・段5 のみ）: 2026-03-01 〜 2026-06-30（periods.py 正本・fast-mode §8.5）
- 探索窓（段2 目的関数・まこさん決定 2026-07-24・正本 window_similarity_ranking.md）＝engine_search_e37.py 定数（逐語）:
```python
SEARCH_START = pd.Timestamp("2024-04-01")
SEARCH_END   = pd.Timestamp("2024-08-01")            # 2024-07-31 まで（終端は排他）
```

## 5. 段0 実測（設計の入力・出典 session_worklog_20260723.md §8 逐語＝増やす手段の優先順位: 第1 ロジック追加・第2 スロット構成・第3 ゲート緩和）

```
■ (a) スロット占有（採点窓・5分グリッド）
   ショート保有>0 の時間比率: 26.4%
   ショート満杯（0.024 BTC＝2 lot）の時間比率: 10.24%
   ロング満杯（0.024 BTC）の時間比率: 0.06%
   同時保有 size 分布（BTC）: 中央 0.000 / q90 0.024 / 最大 0.042
■ (b) 機会の在庫
   レンジ∩帯あり: 21242 バー（全 35136 バーの 60.5%・174 バー/日）
   上端 res_hi 到達（S1圏）                62 バー（  0.3% /    0.5 バー/日）
   down近似天井（直近1h高値）到達             2198 バー（ 10.3% /   18.0 バー/日）
   届かない戻り（mid以上・S2在庫）             9902 バー（ 46.6% /   81.2 バー/日）
   下端 sup_hi 到達（L1圏・重複可）          4722 バー（ 22.2% /   38.7 バー/日）
   天井到達 ∩ ショート満杯（機会が来たが建てられない）: 580 バー（4.8 バー/日）
■ (c) 'v56_skip': 1217 / 'v40_age_exempt': 1942 / 'v21_entry_fires': 5699（採点窓+助走の合計）
```
⚠️ この数字は在庫の桁の把握＝設計の固定値に焼かない（L-330・フロー段0 ⛔）。

## 6. global 設定（実装データ・逐語）

```json
{
  "box_tf": "5m",
  "lot_btc": 0.012,
  "entry_ttl_bars": 3,
  "regime": {
    "v20_rg5": true,
    "v25_adaptive_band": true,
    "note": "レンジ判定 RG-v5＋RG-v6 適応束ね幅＝S1/L1 共通の局面ゲート（build_regime_gate_rg.py を import 再利用・視認校正3巡・H2 確定バーのみ）"
  },
  "slots": {
    "short_lots_max": 2,
    "long_lots_max": 2,
    "engine_cap_btc": 0.048,
    "note": "現行 v59d_164 と同一（まこさん OK 2026-07-24・新数値ゼロ）。H1＝予算0.12 は全採用戦略の共有枠＝本エンジン単独の cap は単独測定"
  },
  "priority_rule": "発火競合時は priority の若い番号優先＋優先度別スロット配分。本格調停の実装は段4（値の水準はまこさん）。段1 は S1/L1 が side 別で競合しないため定義のみ",
  "identity_baseline": {
    "csv_stem": "trades_e37_range_scalp_v59d_164",
    "note": "段1 妥当性確認＝S1+L1 既定値の E38 出力がこの採用土台と md5 恒等になること（logic 列は比較時に除外）"
  }
}
```

## 7. ロジック定義（段1 登録分＝S1/L1・値の出典は各節・CC の新数値ゼロ）

| id | side | priority | enabled | 内容 | 入口 type | 出口 type |
|---|---|---|---|---|---|---|
| S1 | short | 1 | True | レンジ上端逆張りショート（現行 v59d_164 相当） | ceiling_armed_dc | state_machine_v59d |
| L1 | long | 1 | True | レンジ下端反発ロング（現行 v57 flat_up 限定相当） | support_fresh_touch | long_mvp_symmetric |
| S2 | short | 未確定 | False | 戻り売り（mid 以上への戻り×失速確認） | pullback_short | generic_scalp_exit |
| S3 | short | 未確定 | False | 上抜け失敗 fade（res_hi 上抜け→帯内へ戻り） | fade_short | generic_scalp_exit |
| S4 | short | 未確定 | False | 統計的回帰ショート（dev_z 上側行き過ぎ） | zscore_short | generic_scalp_exit |
| S5 | short | 未確定 | False | グリッド売り（mid〜res_hi 等間隔 resting） | grid_short | grid_exit |
| L2 | long | 未確定 | False | 急落後反発ロング（急落幅×出来高スパイク） | crash_rebound_long | generic_scalp_exit |
| L3 | long | 未確定 | False | 下抜け失敗 fade（sup_lo 下抜け→帯内へ戻り） | fade_long | generic_scalp_exit |
| L4 | long | 未確定 | False | 統計的回帰ロング（dev_z 下側行き過ぎ） | zscore_long | generic_scalp_exit |
| L5 | long | 未確定 | False | グリッド買い（sup_hi〜mid 等間隔 resting） | grid_long | grid_exit |

### S1（priority 1・short・有効）: レンジ上端逆張りショート（現行 v59d_164 相当）

- 出典: report_trades_e37_range_scalp_v59d_164_score.txt §0 実行引数（2026-07-23 まこさん採用）＋ e37_scalp.py V59_* モジュール定数（228〜237行）
- 実装: e37_scalp / run_e37（ショート側＝run_continuous_v11 経路・engine_search_e37.BASE_KW と同一口）
- 入口（type=ceiling_armed_dc）: range_ok_rg5 ∩ 型別天井（down型=直近1h高値［v26 gap0.5%/down-hours1.0/max-age6h/v40 down免除］／flat_up型=res_hi＋実測高値クランプ群 v35/v36/v37/v38＋v56 若レンジ窓禁止）到達で武装 → stoch(9,3) デッドクロス発生バーで maker 指値
- 出口（type=state_machine_v59d）: V9 型ポジション状態機械（entry_exit_matrix 基本原則③）＝枝別の値は engine_flags と const_overrides が正本
- 出口の枝（状態機械・entry_exit_matrix 基本原則③）:
  - PARTIAL_TP: TP1=(建値+アンカー)/2 で半分・v22 低値アンカー M24（maker）
  - TP_FILLED: TP2=サポートゾーン上端×(1+0.05%) 手前・v18＋deadline shrink v13（maker）
  - SL_FILLED: 災害SL=res_hi+1.0×W（遠い・maker）
  - TIME_EXIT: 48本=240分＋v31 建値フロア待機 TTL120分（BE_EXIT maker→未到達 taker）
  - RANGE_BREAK_EXIT: ゾーン外終値1h持続∩出来高（taker）
  - uptrend 畳み: v21 fold＋v24 TREND_CAUGHT_TP 建値+0.08%（maker）
  - v27 ピーク反転建値保護: flat_up 限定 MFE_DRAWDOWN_CUT（maker）
  - v47/v53 切り: flat_up 限定 未搭乗カット（TREND_CONT taker）＋v48/v50 建値フロア待機 TTL6h
  - v59 急騰早切り: 型別シグナル×建値%逆行で stop 切り（const_overrides が正本・段2 探索の主対象）

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{
  "v11": true,
  "v12_open_range": true,
  "v13_time_maker": true,
  "v18_tp2_far": true,
  "v22_set": true,
  "v24_trend_maker_tp": true,
  "v26_split_ceiling": true,
  "v26_gap": 0.5,
  "v26_down_hours": 1.0,
  "v26_max_age_hours": 6.0,
  "v27_flatup_lock": true,
  "v31_time_be": true,
  "v35_flatup_range": true,
  "v36_flatup_near": true,
  "v37_flatup_climb": true,
  "v38_flatup_clamp": true,
  "v40_down_no_age": true,
  "v47_mtf_cut": true,
  "v48_stale_wait": true,
  "v50_trend_wait": true,
  "v53_flatup_fast_cut": true,
  "v56_rearm_delay": true,
  "v59_adx_cut": true
}
```
const_overrides（実装データ＝モジュール定数への注入値・逐語・段2 探索の主対象）:
```json
{
  "V59_WAIT_MIN": 20,
  "V59_FLAT_WIN_MIN": 240,
  "V59_DOWN_ADV_PCT": 0.15588160549621896,
  "V59_FLAT_ADV_PCT": 0.15024814839103248,
  "V59_DOWN_ADX7_TH": 28.102910192963172,
  "V59_FLAT_DID7_TH": 0.283351853801863,
  "V59_DOWN_SIG": "di14",
  "V59_FLAT_SIG": "kijun26",
  "V59_DOWN_WIN_MIN": 0,
  "V59_CUT_MODE": "stop"
}
```

### L1（priority 1・long・有効）: レンジ下端反発ロング（現行 v57 flat_up 限定相当）

- 出典: e37_scalp.py run_long_support（1569行〜・まこさん GO 2026-07-20）＋ v57 4分割由来の flat_up 限定（down型=落ちるナイフ底買いを建てない）
- 実装: e37_scalp / run_e37（ロング側＝run_long_support 経路）
- 入口（type=support_fresh_touch）: range_ok_rg5 ∩ 下端帯 fresh touch（low≤sup_hi ∩ close>sup_lo・帯に入った最初のバー＝1バー1発注）∩ flat_up 型限定 → maker 指値 close×(1−offset)・TTL3
- 出口（type=long_mvp_symmetric）: ショート中核の対称移植 MVP（v22〜v56 型別レバーは未搭載＝段2 でロジック別調整）
- 出口の枝（状態機械・entry_exit_matrix 基本原則③）:
  - PARTIAL_TP: (建値+mid)/2 で半分（maker）
  - TP_FILLED: mid で残り全部（maker）
  - SL_FILLED: 災害SL=sup_lo−1.0×帯幅（maker）
  - TIME_EXIT: 48本=240分（taker）

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{
  "v57_long_support": true,
  "v57_long_flat_up_only": true,
  "v57_long_sl_pct": null,
  "v57_long_vol_gate": null
}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2,
  "tmax_bars": 48,
  "gap_pct": 0.5,
  "sl_zone_k": 1.0
}
```

### S2（priority 未確定（段3 まこさん）・short・無効）: 戻り売り（mid 以上への戻り×失速確認）

- 出典: 段0 実測＝届かない戻り 81.2 バー/日（worklog 20260723 §8・在庫最大）・E-a4・グリッド E38 #S2（まこさん OK 2026-07-24）
- 実装: e38_logic_parts / generic_logic_loop
- 入口（type=pullback_short）: params が正本（null=段2 探索で決める）: {"pos_min": null, "confirm": null}
- 出口（type=generic_scalp_exit）: params が正本（null=段2 探索で決める）: {"tp1_frac": null, "tp2_target": null, "sl_zone_k": null, "tmax_bars": null, "be_wait": null}

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2
}
```

### S3（priority 未確定（段3 まこさん）・short・無効）: 上抜け失敗 fade（res_hi 上抜け→帯内へ戻り）

- 出典: E-a3 の fade（false breakout）・グリッド E38 #S3（まこさん OK 2026-07-24）
- 実装: e38_logic_parts / generic_logic_loop
- 入口（type=fade_short）: params が正本（null=段2 探索で決める）: {"over_min": null, "confirm_bars": null}
- 出口（type=generic_scalp_exit）: params が正本（null=段2 探索で決める）: {"tp1_frac": null, "tp2_target": null, "sl_zone_k": null, "tmax_bars": null, "be_wait": null}

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2
}
```

### S4（priority 未確定（段3 まこさん）・short・無効）: 統計的回帰ショート（dev_z 上側行き過ぎ）

- 出典: E-a1/E-d2・グリッド E38 #S4。注記＝dev_z=(close−SMA20)/std20 は BB20 と同窓の標準化＝数学的に同値のため指標カテゴリは dev_z に一本化（2026-07-24 まこさん報告済み）
- 実装: e38_logic_parts / generic_logic_loop
- 入口（type=zscore_short）: params が正本（null=段2 探索で決める）: {"z_th": null, "trigger": null}
- 出口（type=generic_scalp_exit）: params が正本（null=段2 探索で決める）: {"tp1_frac": null, "tp2_target": null, "sl_zone_k": null, "tmax_bars": null, "be_wait": null}

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2
}
```

### S5（priority 未確定（段3 まこさん）・short・無効）: グリッド売り（mid〜res_hi 等間隔 resting）

- 出典: E-a5・グリッド E38 #S5
- 実装: e38_logic_parts / grid_loop
- 状態: unimplemented＝グリッド構造（複数 resting・在庫管理）は別部品＝後続の実装単位（まこさん報告済み 2026-07-24）・enabled にすると設定エラーで停止
- 入口（type=grid_short）: params が正本（null=段2 探索で決める）: {}
- 出口（type=grid_exit）: params が正本（null=段2 探索で決める）: {}

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2
}
```

### L2（priority 未確定（段3 まこさん）・long・無効）: 急落後反発ロング（急落幅×出来高スパイク）

- 出典: E28 型の5分足近似（taker 系列が5分足に無いため 急落幅×出来高スパイク へ置き換え＝まこさん OK 2026-07-24）・E-a1・グリッド E38 #L2
- 実装: e38_logic_parts / generic_logic_loop
- 入口（type=crash_rebound_long）: params が正本（null=段2 探索で決める）: {"k_bars": null, "drop_th": null, "vol_mult": null}
- 出口（type=generic_scalp_exit）: params が正本（null=段2 探索で決める）: {"tp1_frac": null, "tp2_target": null, "sl_zone_k": null, "tmax_bars": null, "be_wait": null}

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2
}
```

### L3（priority 未確定（段3 まこさん）・long・無効）: 下抜け失敗 fade（sup_lo 下抜け→帯内へ戻り）

- 出典: E-a3 の fade・下側対称・グリッド E38 #L3（まこさん OK 2026-07-24）
- 実装: e38_logic_parts / generic_logic_loop
- 入口（type=fade_long）: params が正本（null=段2 探索で決める）: {"over_min": null, "confirm_bars": null}
- 出口（type=generic_scalp_exit）: params が正本（null=段2 探索で決める）: {"tp1_frac": null, "tp2_target": null, "sl_zone_k": null, "tmax_bars": null, "be_wait": null}

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2
}
```

### L4（priority 未確定（段3 まこさん）・long・無効）: 統計的回帰ロング（dev_z 下側行き過ぎ）

- 出典: E-a1/E-d2・S4 の対称・グリッド E38 #L4（まこさん OK 2026-07-24）
- 実装: e38_logic_parts / generic_logic_loop
- 入口（type=zscore_long）: params が正本（null=段2 探索で決める）: {"z_th": null, "trigger": null}
- 出口（type=generic_scalp_exit）: params が正本（null=段2 探索で決める）: {"tp1_frac": null, "tp2_target": null, "sl_zone_k": null, "tmax_bars": null, "be_wait": null}

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2
}
```

### L5（priority 未確定（段3 まこさん）・long・無効）: グリッド買い（sup_hi〜mid 等間隔 resting）

- 出典: E-a5・段0 (b) 下端到達 38.7 バー/日・グリッド E38 #L5
- 実装: e38_logic_parts / grid_loop
- 状態: unimplemented＝S5 と同じ後続の実装単位・enabled にすると設定エラーで停止
- 入口（type=grid_long）: params が正本（null=段2 探索で決める）: {}
- 出口（type=grid_exit）: params が正本（null=段2 探索で決める）: {}

engine_flags（実装データ＝run_e37 への注入値・逐語）:
```json
{}
```
params（実装データ＝関数引数への注入値・逐語）:
```json
{
  "max_lots": 2
}
```

## 7b. 探索範囲の宣言（段2・engine_search_e38 が読む・実装データ＝json 逐語）

```json
{
  "note": "engine_search_e38 が読む探索範囲の宣言（type=float/cat/quantile）。quantile は探索窓の分布分位から実行時に上下限を決める＝CC の手打ち値なし（kijun26 前例）。float の比率系は幾何 a-priori の広め固定幅（engine_search_e37 の 0.1〜1.0 と同型＝L-267 の禁止は採点窓 net 目的関数の選定）。値決め＝探索窓のみ・確認窓は表示のみ・採点窓不使用（まこさん決定 2026-07-24・正本 window_similarity_ranking.md）",
  "common_exit": {
    "tp1_frac": {
      "type": "float",
      "lo": 0.2,
      "hi": 0.8
    },
    "tp2_target": {
      "type": "cat",
      "choices": [
        "mid",
        "opp"
      ]
    },
    "sl_zone_k": {
      "type": "float",
      "lo": 0.5,
      "hi": 2.0
    },
    "tmax_bars": {
      "type": "cat",
      "choices": [
        24,
        48,
        96
      ]
    },
    "be_wait": {
      "type": "cat",
      "choices": [
        0,
        1
      ]
    }
  },
  "logics": {
    "S2": {
      "pos_min": {
        "type": "float",
        "lo": 0.0,
        "hi": 0.9
      },
      "confirm": {
        "type": "cat",
        "choices": [
          "stoch_dc",
          "rsi9_down",
          "bear_bar",
          "none"
        ]
      }
    },
    "S3": {
      "over_min": {
        "type": "float",
        "lo": 0.0,
        "hi": 0.5
      },
      "confirm_bars": {
        "type": "cat",
        "choices": [
          0,
          1
        ]
      }
    },
    "S4": {
      "z_th": {
        "type": "quantile",
        "series": "dev_z_abs",
        "q_lo": 0.7,
        "q_hi": 0.995
      },
      "trigger": {
        "type": "cat",
        "choices": [
          "imm",
          "rev"
        ]
      }
    },
    "L2": {
      "k_bars": {
        "type": "cat",
        "choices": [
          6,
          12,
          24
        ]
      },
      "drop_th": {
        "type": "quantile",
        "series": "ret12_abs_down",
        "q_lo": 0.9,
        "q_hi": 0.995
      },
      "vol_mult": {
        "type": "float",
        "lo": 1.0,
        "hi": 4.0
      }
    },
    "L3": {
      "over_min": {
        "type": "float",
        "lo": 0.0,
        "hi": 0.5
      },
      "confirm_bars": {
        "type": "cat",
        "choices": [
          0,
          1
        ]
      }
    },
    "L4": {
      "z_th": {
        "type": "quantile",
        "series": "dev_z_abs",
        "q_lo": 0.7,
        "q_hi": 0.995
      },
      "trigger": {
        "type": "cat",
        "choices": [
          "imm",
          "rev"
        ]
      }
    }
  }
}
```

## 8. 段1 の作業・完了条件・禁止（フロー正本 e38_flow.md 逐語＝再発明しない）

### 段1 器＝E38 設定駆動エンジンと候補ロジック定義 — ✅ 完了（根拠: /Users/tachiharamasako/Documents/GitHub/cat-bitget/.claude/state/session_worklog_20260724.md）
- 目的: 設定ファイルが正本のエンジンを新設し、設計書と実装の差異を構造的に消す。
- 作業: e38 エンジン新設（strat_base・レンジ計器等を import 再利用・E37 一枚岩に挿し込まない）。ロジック定義（入口条件・出口値・優先度・スロット）は設定ファイル（json）に置き、エンジンは設定を解釈する固定部品にする。最初の登録＝S1（現行 v59d 相当ショート）とL1（現行 v57 相当ロング）。売買記録に logic 列（診断・net 不関与）。設計書は手書きしない＝骨格を設定 json＋段0 実測から機械生成（gen_design スクリプト・CC の自由記述を最小化）し、DESIGN_CONTRACT を含めて、まこさんの承認を得る。
- 道具: e38_*.py（新規）・logic config json・acceptance/設計書・verify_design_contract.py。
- 完了条件: 設計書がまこさん承認済み。E38 が S1/L1 構成で走り、py_compile・番人（わざと壊して落ちる）・妥当性確認（件数/型別が v59d と桁が合う）を通過。
- ⛔ 禁止: 採点窓を覗く。設定ファイルの外にロジック固有値をハードコードする。

## 9. 段1 妥当性確認の番人（設計）

- 恒等番人: S1+L1 を json 既定値のまま走らせた E38 出力が、採用土台 trades_e37_range_scalp_v59d_164 と md5 完全一致（logic 列は比較時に除外・md5 は数字を見ない＝採点窓の覗き見でない）。
- 破壊番人: json をわざと壊す（必須キー欠落）と実行前に停止する。enabled=false でそのロジックの玉が消える。
- py_compile ＋ require_design_contract_before_run（下の DESIGN_CONTRACT を実行前に機械照合）。

## 10. DESIGN_CONTRACT（verify_design_contract.py 実行前機械照合・e38_requirements.json decisions）

```json
{
  "impl_file": "scripts/priority_rebuild/e38_priority_stack.py",
  "self_check_calls": [
    "load_logic_config",
    "e38_logics.json",
    "run_e37",
    "const_overrides",
    "_output_and_report",
    "priority"
  ]
}
```

承認: まこさんの承認をもって段1 の設計確定（承認前にエンジン実装へ進まない）。
