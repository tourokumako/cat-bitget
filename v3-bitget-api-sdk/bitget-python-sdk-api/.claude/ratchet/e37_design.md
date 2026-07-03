# E37 戦略設計書 v5 — レンジ・スキャル 両側 maker MR ＋「稼げるレンジ」検出器ゲート

作成: 2026-07-03（v2=出来高climax fade は 2026-06-29・v3/v4 を経て本版に置換・過去版は git 履歴）
構成: Peterson hypothesis-driven（制約→ベンチ→目的→仮説 a priori 反証可能→Indicators/Signals/Rules→個別評価→受け入れ）。
進め方: アジャイル（cat_requirements §8.4）。判定は score.py の数字のみ（CC は net 計算に触れない）。

★なぜ v5（分析→設計の連結・enforce_pdca_chain・analysis_block/improvement_plan 2026-07-03）:
- v3＝スキャル頻度は仕組みで達成（15.35件/日）が全セル手数料負け（ledger ARC17）。v4＝入口の質は gross トントンだが 0.47件/日＝役割失格（WORKFLOW 改訂112）。
- まこさん結論（2026-07-03・memory feedback_range_edge_exists_suspect_cc_probe）: **過去データに取れるレンジは確実に在る＝取れない数字が出たら疑うのは CC の probe/設計**。今日の probe 5本は「レンジかどうかを知らずに全場面発火」を測っており、まこさんの「複合的にレジサポを検出してから入る」と別の問いだった。
- まこさんの日別レジームラベルは「値動きがほぼ無い」チェック＝稼げるレンジの教師に不適（まこさん 2026-07-03 明言）＝ **教師は結果ベース（そのイベントでレンジ取りが手数料込みでプラスだったか）を機械生成**。
- 検出器 probe 実測（学習窓 OOF・疑似シミュ）: v1 be 0.99 から v2（忍耐60分＋TP突き抜け0.5σ）で **top10% be 1.36〜1.40・4.1件/日・保有中央20〜30分／top20% be 1.18・8.2件/日**＝E37 初の「手数料超え×スキャル頻度×短保有」同時成立。重要度は POC/VAH/VAL・フィボ・BB・S/R が上位（まこさんの複合手法と一致）・ATR系最下位（H15 クリア）。leak は H12 異常値 STOP で1回検出・除去済（parquet ラベル56列の混入）。

★ベースアップ（2026-07-03 WebSearch3/WebFetch2・種別2=実務家+学術）:
1. メタラベリングの閾値/ハイパラは学習・検証データで確定し OOS は一発評価（Hudson & Thames "Does Meta-Labeling Add to Signal Efficacy?"）。
2. 指値約定は逆選択で期待 約−0.8bp（arxiv 2407.16527）＝be に余裕が要る（ぎりぎり 1.0 の設計をしない）。
3. purged CV＋embargo が leak 防止の標準（AFML）。

---

## §0 位置づけ（§1.2.1 局面3 レンジ・優先度3・ROLE_CHECK e37=scalp）
- E37＝スキャル型＝**件数を上げて小さく多数取る**（役割固定）。E36（デイトレ・1ポジを伸ばす・SHORTのみ）と住み分け＝E37 は短い小波を両側で数十分以内に回す。当面目標＝E36+E37 合算 月 net $600。
- 比較 base＝v3 iter1 地面（頻度達成・net 負）。E37 は全 iter 未採用＝プラスの地面を作るのが本版の仕事。

## §1 制約
- Bitget USDT-FUTURES BTCUSDT・5m・両側（hedge_mode＝LONG/SHORT 各1ポジ・同サイド merge）・MAX_ADDS=1・size 0.024・全建玉合計 cap 0.12（H1）。
- 約定＝eval_engine 固定モデル（H5・改造禁止）: entry 指値 maker close×(1∓0.0001)・TTL3・不約定=不成立／TP=指値 maker／TIME=成行 taker+slip／SL=指値 maker。
- 期間＝periods.py SSOT（H8）: 学習 fit 〜2025-02（検出器の学習は parquet 被覆 2021-04〜2024-12）・採点 2025-06〜2026-02・封印 不参照。
- 特徴量＝Phase 0 leak 検証済み parquet（2725列）から **ラベル56列＋blacklist64列＋close を除外した 2603列**（除外は実行時 assert・H2/H6）。

## §2 ベンチ（地面）
- E37 現況: v3 iter1（15.35件/日・precheck FAIL breakeven −0.59）／v4（0.47件/日・net −$105）＝地面マイナス。
- E36: 月$137.46（採用 base）。合算目標 $600 に対し E37 に月 +$463 級の黒字源が必要。

## §3 目的
検出器ゲート下のレンジ MR スキャルで、**precheck PASS（学習窓 breakeven≥1.0）から 両窓 score.py プラス**の E37 初の黒字地面を作る。件数/日 ≥3（スキャル頻度・v4 の6倍超に上げる）・保有は分単位。

## §4 仮説（a priori・反証可能）
「dev_z±1.0σ∩反転バーの MR イベントのうち、複合状況（出来高プロファイル・フィボ・BB・サポレジ距離・RSI9・複数TF整合 等 2603特徴）が『稼げるレンジ』を示すものに限れば、SMA∓0.5σ への戻り幅は maker 往復コストを超える」。
反証条件: 検出器ゲート下で学習窓 precheck FAIL、または採点窓 score.py net がゲート無し（v3型）を下回る。FAIL の場合は路線でなく**この版の作り**（教師幅/特徴/モデル/θ）を原因分解して v6 へ（feedback_range_edge_exists_suspect_cc_probe）。

## §5 Indicators / Signals / Rules
1. **イベント（一次・高リコール＝メタラベリングの一次モデル）**: dev_z=(close−SMA20)/std20 が +1.0σ 以上 ∩ 陰転バー で SHORT 候補／−1.0σ 以下 ∩ 陽転バー で LONG 候補（v3 の頻度エンジン系譜・学習窓実測 40.8候補/日）。
2. **検出器（二次・結果ベース教師）**: LightGBM binary。
   - 教師（機械生成・学習窓のみ）: 各イベントを Triple Barrier で疑似執行（TP=SMA∓0.5σ 先着 maker／SL=entry∓2×ATR14 maker／12本=60分打ち切り taker・同バー両ヒットは SL 優先=保守）で net>0 を 1 にラベル。
   - 特徴: parquet 2603列（フィボ175・POC/VAH/VAL 500超・ピボット・BB104・RSI97[rsi9__5m 含む]・サポレジ距離・複数TF 整合列）＋side。線引きは全て木に学習させる（固定閾値の手調整なし・L-267）。
   - 学習: purged 5fold（時間ブロック・embargo 1日）で OOF を作る。**本番モデル＝学習窓全体で再 fit**。
   - **θ（ゲート閾値）＝学習窓 OOF の分位から選定**（頻度床＝学習窓換算 件数/日≥3 を満たす範囲で be 最大の分位・採点窓不参照）。θ選定ログを sidecar に記録。
3. **執行**: 通過候補に maker 指値・TTL3・単一スロット（サイドごと1玉・MAX_ADDS=1）。
4. **出口**: TP=SMA∓0.5σ（maker・SCALP_FLOOR 0.08% 手数料割れ防止）／SL=entry∓2×ATR14（maker）／TIME=12本60分（taker）。**新 exit_reason なし**（TP_FILLED/SL_FILLED/TIME_EXIT 既存登録のみ＝score.py 変更なし・H13）。
5. **出力**: strat_base 経由 _output_and_report・--tag v5 連番・params_sidecar（使用値＋Entry/Exit ロジック＋θ選定ログ）。

## §6 個別評価（自己検査・わざと壊すメタ確認込み）
- cap 自己検査（時系列合計 ≤0.12）・最小注文（0.024≥0.0001・×価格≥5USDT）。
- leak: 特徴量はイベントバー時点の parquet 行のみ・grep assert（負shift / center=True 不使用）・**ラベル/blacklist 除外 assert（56/64 未満で停止）**・TRAIN_END assert（fit データが境界を跨いだら停止）。
- 恒等: --no-gate＝検出器 OFF で全イベント執行（ゲート寄与を lever-bites で分離）。
- 較正: 採点窓の検出器確率帯×実 net を report H 節で確認（逆較正チェック・KB §5）。

## §7 受け入れ基準（F・詳細は acceptance.md）
① **件数/日 ≥3（v4 0.47 の6倍以上に上げる＝スキャル役割・一級）** ② 保有中央値 分単位（目安 ≤30分・バックストップ60分） ③ TP 幅は maker 往復手数料超え（precheck P1 の TP側 breakeven>1） ④ precheck 全体 PASS（学習窓 breakeven≥1.0） ⑤ 両窓 score.py で E37 過去最良（プラス地面）・non-degenerate ⑥ H15: 検出器重要度で ATR/vol 家族が非支配（v1/v2 実測 最下位クリア） ⑦ 5分足スキャル設定: RSI9・MTF 整合を検出器特徴に含む（rsi9__5m・上位足列・technical_kb §4/§5）。

## §8 リスク・限界（隠さない）
- probe は楽観側（タッチ=約定・キュー無視）＋指値の逆選択 −0.8bp（arxiv 2407.16527）＝実エンジンで be は目減りする。be 1.18〜1.82 の余裕は薄い＝ θ は頻度床内で be 高め側を学習窓選定。
- N4 ドリフト（採点窓は低ATR寄り +24pt）＝学習窓の高確信帯が採点窓で痩せる可能性＝両窓 score.py が最終判定（L-308・学習窓の数字で「効いた」と言わない）。
- 検出器はオフライン特徴（parquet）前提＝バックテスト用。本番稼働時は特徴量の増分計算が必要（Phase 7 で別途・E 系戦略共通の既知課題）。
- 採点窓の特徴は labels_mfe_mae_pct_test_2025 / test_2026_q1 parquet から読む（評価のみ・fit 不使用）。

## §10 DESIGN_CONTRACT（acceptance で実装と機械照合）
- impl_file = scripts/priority_rebuild/e37_range_scalp.py（v5 で作り直し）。
- self_check_calls = ["micro_rev_event", "detector_gate", "oof_theta", "purged_fold", "label_exclude_assert", "SCALP_FLOOR", "_verify_cap"]。
