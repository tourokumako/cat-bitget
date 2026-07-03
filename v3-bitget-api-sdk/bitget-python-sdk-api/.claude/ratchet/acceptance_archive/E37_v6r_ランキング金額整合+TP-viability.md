# acceptance.md — E37 v6 iter2（v6r）＝検出器ランキングの金額整合＋TP-viability 同梱（検出器ゲート両側 maker MR スキャル）

TARGET: scripts/priority_rebuild/e37_range_scalp.py

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["RANK_BE_REGRESSION", "_tp_viable", "_gen_events_v6", "BE_FLOOR", "_select_theta_be_first", "label_exclude_assert", "_verify_cap"]
}
```

## LEVER（improvement_plan から逐語引き継ぎ・まこさん GO 2026-07-03「１はGO・２は同梱する」）
<!-- LEVER: 検出器ランキングの金額整合（教師を per-event の net/fee 回帰にし、θフロンティアを期待値ランキング分位で作る・θ選定規則=be≥1.0 内で頻度最大は不変・イベント5型/OOF測定系/執行出口は不変）＋TP-viability entryゲート同梱（entry時点で TP 目標が SCALP_FLOOR 未満の候補は建てない） -->

## A. これは何か（1行）
v6 で特定した真因（検出器の教師＝勝てるかの二値が金額を見ない）を直す＝**①検出器を「per-event の be（net÷fee・無次元）の回帰」にしてランキングを金額整合に、②entry 時点で TP 目標が手数料床（SCALP_FLOOR）未満の候補は建てない**。イベント5型・θ選定規則（be≥1.0 内で頻度最大・帯なしなら停止）・OOF 測定系・執行/出口は v6 のまま不変。

## B. 深掘り4点
### ① 真因
v6 の学習窓 OOF フロンティアは勝率が上がる（0.648〜0.668）のに avg_gross が約1/3＝**P(net>0) のランキングは be のランキングと別物**（浅い薄利勝ち玉が確率上位を占拠）。母数拡大は機能した（39.4イベント/日）＝直すのはランキングの物差し。＋entry 時点で TP 目標が床未満の玉 6.5/日（be −2.43）が構造的に混入。

### ② 期待値分解
- ランキング上位帯の avg_gross: 二値では q0.95 で $0.153 に希釈 → 回帰（金額整合）で「大きく勝てる場面」を上位に集める＝be≥1.0 帯の再出現を狙う。
- 件数/日: v6 の母数（39.4イベント/日）を維持しつつ、be≥1.0 帯の絶対頻度が床3件/日相当を賄えるかを学習窓 OOF で判定（賄えなければ停止＝赤字帯は選ばない）。
- TP-viability: 毒 6.5/日（教師・エンジン双方から除去）＝教師の学習も綺麗になる。

### ③ root か symptom か
**root**。v6 で「母数だけでは解けない・物差しが金額非整合」を型別/viability probe で特定済み（analysis_block v6 追記・ledger ARC19）。個別イベント型の手動カットはしない（線引きは回帰スコアの分位＝木とフロンティアに委ねる）。

### ④ ベースアップ（2026-07-03 実施・検索3本/種別2/精読2本）
- **分類=向き・回帰=大きさの役割分担は業界整合**: BTC アルゴトレードの ML 比較研究＝「分類器は取引の向き・回帰器は変化の大きさを予測」の二層で扱い、ML 指標（MAE 等）でなく取引指標（PnL%・手数料込み）で統合評価する。https://arxiv.org/html/2407.18334
- **金融 ML の評価はランキング整合**: 期待リターンの意思決定は点予測でなく相対順位（IC/RankIC）で測る＝スコアの絶対値でなく「順序が be と揃うか」が本質＝回帰スコア分位でフロンティアを作る本設計と整合。https://arxiv.org/html/2508.16495（RankRefine 系の整理）
- **メタラベリングの二層構造**（プライマリ=イベント・セカンダリ=取るか）: セカンダリの出力を確率でなく期待値に置き換えるのは「サイズ判断に確率を使う」原型の金額版。https://hudsonthames.org/does-meta-labeling-add-to-signal-efficacy-triple-barrier-method/

## C. 変更の単位（H16）
- **1レバー＝「ランキングの金額整合＋TP-viability 同梱」のセット**（まこさん GO 2026-07-03・viability は既存定数 SCALP_FLOOR の entry 前倒し＝新数値なし）。
- **既定 OFF 恒等**: 新フラグ --v6r。OFF なら v5 と完全同一（v6off で byte 一致確認済みの経路・コード不変）。--v6（二値版）も比較用に不変で残す（lever-bites）。
- 不再演: 楽観 fill 教師・in-sample 自己採点には戻らない（OOF ゲート維持）。頻度床のために赤字帯を選ばない（θ規則不変）。採点窓は覗かない（L-267）。
- **★疑似シミュ由来の固定値ゼロ**:
  - (a) 回帰教師の目標値＝per-event の net/fee（実行シミュの実測比・無次元 H6）＝probe 数値の焼き込みなし。回帰の目的関数は L2（ライブラリ既定・数値探索なし）。
  - (b) TP-viability の閾値＝既存 SCALP_FLOOR（0.08%・v5 から不変の a-priori）を entry 時点に前倒しするだけ＝新しい数値を導入しない。
  - (c) θ は学習窓 OOF の回帰スコア分位から自動選定（BE_FLOOR=1.0＝損益分岐の定義値）・採否は実エンジン両窓 score.py。probe の be/頻度（型別・viability 別）は設計の固定値にしない。

## D. 審判整合・出力
- 新 exit_reason なし・コスト種別不変・judge 不変（H13）・エンジン/出口/サイズは v5 完全同一。
- 出力＝共通書き出し処理・**--tag v6r 連番**・sidecar に回帰フロンティア（分位・be・イベント/日）と θ 選定ログ・⑨巻き込みログ・CSV に event_type 列（v6r のみ）。

## E. §4.6 ハード制約 照合
- **H1** cap 0.048（両側 0.024×2・自己検査＋score.assert_hard_constraints）／**H2** leak（label_exclude_assert・OOF・学習窓のみ fit・grep assert）／**H5** 約定モデル不変／**H6** 価格非依存（net/fee は無次元・イベントは σ/分位）／**H8** periods／**H13** judge 固定／**H15** 向きスコアなし・重要度 top10 で ATR/vol 非支配確認／**H16** 上記 C。

## F. 受け入れ判定
1. **自己検査**: (i) --v6r OFF＝v5 恒等（経路不変・v6off で byte 一致確認済み） (ii) cap (iii) leak grep (iv) label_exclude_assert (v) DESIGN_CONTRACT verify。番人＝わざとラベル列を混ぜて assert が落ちるか。
2. **学習窓**: TP-viability 適用後のイベント型別頻度 → 回帰 OOF スコア分位のフロンティア（realized be・イベント/日）を sidecar 記録 → **θ＝be≥BE_FLOOR(1.0) を満たす分位のうちイベント/日最大**。帯なしなら執行せず停止・結果報告。
3. **⑨巻き込み**: θ で削る勝ちイベントの絶対数と gross を学習窓 OOF でログ。
4. **precheck**: 学習窓 breakeven ≥1.0 PASS が採点の前提。
5. **score.py 両窓**: **件数/日を上げる（scalp 役割・一級基準）＝採点窓 件数/日が v5 の 2.25 を上回りスキャル床 ≥3件/日**・net は E37 地面（v5 −$350）超え・黒字転換を狙う・**⑦手数料を超える TP 幅**（SCALP_FLOOR 0.08%＝maker 往復 0.028% の約3倍・維持）・**⑨短保有（分単位・保有中央 20-30分・60分 time-exit 維持）**・**⑫5分足設定**（RSI9 系特徴・MTF 8TF shift=1＝technical_kb §4.2/§5.3・v5 同一）。
6. **H12 異常値** STOP・degenerate 不採用・lever-bites（--v6[二値] vs --v6r[回帰] のフロンティア比較ログ＋event_type 列）。

## 実装内容（要点）
- RANK_BE_REGRESSION: 検出器を LGBMRegressor（目的=L2・既存 _LGB_PARAMS 同系）にし、教師 y＝per-event の net/fee（エンジン同一執行 Triple Barrier の実測・無次元）。purged 5fold OOF スコア → 分位フロンティア（realized be）→ _select_theta_be_first（不変）→ 学習窓全体で再 fit・OOF ゲート（学習窓バー）＋最終モデル（TRAIN_END 以降）は v5/v6 と同構造。
- _tp_viable: entry 時点（当該バーの close/sma/std のみ＝t 因果）で「指値価格から見た TP 目標距離 ≥ SCALP_FLOOR」を判定し、イベント候補と教師の両方に適用（エンジン同一）。
- イベント5型（_gen_events_v6）・θ規則（_select_theta_be_first・BE_FLOOR）・執行/出口/サイズ＝v6 実装のまま不変。

<!-- ARC order=20 iter="E37 v6r ランキング金額整合+TP-viability" 前提="E37未採用・v6(母数拡大+θ規則反転)が学習窓ゲート停止＝教師の金額非整合を特定した上" 採否="未採点（実装→学習窓OOF→precheck→両窓score.py）" base_csv="trades_e37_range_scalp_v5_008_score.csv" score_csv="" train_csv="" 狙い="v6の真因＝検出器教師(net>0二値)が金額を見ず薄利勝ち玉が上位帯を希釈してbe≥1.0帯が消失（ARC19）を、ランキングの物差しを金額に替えて直す（母数×金額整合ランキングのセットで解く）" 内容="検出器を per-event net/fee（無次元）の回帰（LGBMRegressor）にしθフロンティアを期待値ランキング分位で作る＋entry時点TP-viabilityゲート（TP目標<SCALP_FLOORの候補は建てない・既存定数の前倒し）。イベント5型/θ規則(be≥1.0内で頻度最大)/OOF測定系/執行出口は不変" 方法="自己検査(恒等/cap/leak/label_exclude)→TP-viability後のイベント頻度→回帰OOFフロンティア→θ選定(be≥1.0帯なしなら停止)→precheck be≥1.0→両窓score.py(件数/日>2.25かつ≥3・E37地面超え・短保有維持・H12)" -->
