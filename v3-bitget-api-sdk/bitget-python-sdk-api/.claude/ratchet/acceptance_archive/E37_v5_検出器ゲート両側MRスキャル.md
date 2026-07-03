# acceptance.md — E37 v5 レンジ・スキャル 両側 maker MR ＋「稼げるレンジ」検出器ゲート

TARGET: scripts/priority_rebuild/e37_range_scalp.py

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["micro_rev_event", "detector_gate", "oof_theta", "purged_fold", "label_exclude_assert", "SCALP_FLOOR", "_verify_cap"]
}
```

## A. これは何か（1行）
v3 の頻度エンジン（dev_z±1.0σ∩反転バー・両側 maker・40.8候補/日）に、**結果ベース教師（そのイベントでレンジ取りが手数料込みでプラスだったかを Triple Barrier で機械生成）で学習した LightGBM 検出器（2603特徴・purged CV）の確率ゲート**を掛け、「稼げるレンジ」の場面だけ執行するスキャル。設計正本＝e37_design.md v5。

## LEVER（improvement_plan から逐語引き継ぎ・enforce_pdca_chain 接続②）
<!-- LEVER: v3型イベント（dev_z±1.0σ∩反転バー・両側）に、結果ベース教師（Triple Barrier: TP=SMA∓0.5σ maker／SL=2×ATR maker／60分打ち切りtaker）で学習した LightGBM 検出器（2603特徴・purged CV・学習窓fit）の確率ゲート（θ=学習窓OOF分位から選定・固定閾値の手調整なし）を掛け、通った候補だけ maker で入る（頻度床=スキャル件数を受け入れ基準に含む） -->

## B. 深掘り4点
- **① 真因**: E37 が負け続けた真因は「レンジかどうかを知らずに機械条件で全場面発火」（v3＝全セル手数料負け）または「選別を重ねて頻度を殺す」（v4＝0.47件/日）。まこさんの手動レンジラベルゲートでは両窓エッジ実在（+2.7bps・改訂109）＝欠けていたのは**稼げるレンジの自動認識**。probe 実測で、結果ベース教師の検出器がこれを埋める（OOFゲート top10% で be 1.36〜1.40・4.1件/日・v1 の be 0.99 から教師テンプレ改良で到達）。
- **② 期待値分解**: v3 全体は avg gross −$0.27 vs コスト $0.47。検出器ゲートは**イベントの取捨**で avg gross を動かす: 学習窓 OOF 実測 top10% avg gross $0.38〜0.45（コスト $0.28〜0.32・勝率62〜68%・保有中央20〜30分）。動かすのは「勝てる場面比率」＝勝率と平均勝ち幅の両方（TP=SMA∓0.5σ で幅も v3 比拡大）。
- **③ root か symptom か**: root。入口の「場面選択」そのものを差し替える（θ や SL の微調整＝symptom ではない）。
- **④ ベースアップ**: WebSearch3/WebFetch2（2026-07-03・種別2）: Hudson & Thames メタラベリング（閾値は学習/検証で確定・OOS一発評価）／arxiv 2407.16527（指値の逆選択 −0.8bp＝be 余裕必須）／AFML purged CV+embargo。KB＝technical_kb §4/§5（RSI9・MTF）・trade_analysis_methods_kb §0-§8・analysis_playbook §2・exchange_spec 決済方法・cat_requirements §1.2.1/§6.1。

## C. 変更の単位（H16）
- **1レバー＝検出器ゲートの導入**（イベント定義・出口は v3 系譜の a-priori/教科書値を踏襲＝別レバーにしない。atr サイジングは probe1 で反証済み＝入れない。TREND_CONT は v5 では使わない＝切る系は⑨巻き込み probe 無しに入れない）。
- **既定 OFF で恒等**: --no-gate で検出器 OFF＝全イベント執行（ゲート寄与を lever-bites で分離）。
- **過去失敗の不再演**: ARC16/v4 型「選別で頻度殺し」→ 頻度床（件数/日≥3）を F に物理化。L-308 型「学習窓 AUC を成果と呼ぶ」→ 判定は両窓 score.py のみ。ARC14「入口で向き当て」→ 向きは賭けない（両側 MR・向きスコアなし＝H15）。
- **★疑似シミュ由来の固定値ゼロ**: (a) dev_z ±1.0σ＝σ帯の教科書標準（BB 系・v3 の学習分位 q30/q70≈±0.8σ と同族の a-priori）／SL 2×ATR＝教科書（1.5〜2×）／TIME 60分＝スキャル役割のバックストップ定義／TP=SMA∓0.5σ＝教師テンプレ2案（突き抜け 0σ/0.5σ）を**学習窓で比較して選ぶ**（採点窓不参照・実装時に学習窓で再確認）。(b) probe の θ・be・top% の数値は実装に焼かない＝**θ は実装が学習窓 OOF を作り直して分位から選定**（頻度床 件数/日≥3 内で be 最大・選定ログ sidecar 記録）。(c) 採否は probe でなく**実エンジン両窓 score.py**。
- **★ARC マーカー**:
<!-- ARC order=18 iter="E37 v5 検出器ゲート両側MRスキャル" 前提="E37未採用・v3 iter1地面(頻度達成・net負)の上にゲート追加・教師=結果ベース(まこさんラベル不使用)" 採否="未採点（承認待ち→実装→precheck→両窓score.py）" base_csv="trades_e37_range_scalp_v3_005_score.csv" score_csv="" train_csv="" 狙い="過去データに取れるレンジは確実に在る＝取れないのはCCの検出の作りの問題（まこさん2026-07-03）。レンジかどうかを知らずに発火するv3に『稼げるレンジ』の自動認識を与え、手数料超えの場面だけ執行してE37初の黒字地面を作る" 内容="v3型イベント(dev_z±1.0σ∩反転バー・両側)に結果ベース教師(Triple Barrier: TP=SMA∓0.5σ maker/SL=2×ATR maker/60分taker)で学習したLightGBM検出器(2603特徴・purged 5fold・学習窓fit)の確率ゲートθ(学習窓OOF分位選定)を追加。出口=浅TP maker/ATR-SL maker/60分taker・MAX_ADDS=1・新exit_reasonなし" 方法="学習窓OOFゲートで手数料超えを確認済(probe)→実装後 precheck(学習窓breakeven≥1.0)→両窓score.py・頻度床 件数/日≥3・lever-bites(--no-gate恒等)で寄与分離・重要度でH15確認" -->

## D. 審判整合（出戻り最頻ポイント）
- **新 exit_reason: 出さない**（TP_FILLED/SL_FILLED/TIME_EXIT 既存登録のみ・score.py/eval_engine 変更ゼロ・H13）。
- コスト種別: entry maker／TP maker／SL maker（指値 backstop・v3 と同モデル）／TIME taker+slip＝eval_engine 既存分類と一致。
- 命名: 実験は --tag v5 で連番（require_tag_for_experiment・tagless 禁止）。
- サイドカー: params_sidecar.write_sidecar で使用値＋Entry/Exit ロジック＋**θ選定ログ（OOF 分位・頻度床判定）**を出力（report 節0 表示）。
- 出力: strat_base import（load_5m/_verify_cap/_output_and_report/定数）＝共通書き出し（ratchet_io 自動 archive・上書き防止）。

## E. §4.6 ハード制約 照合
- **H1** cap: 全建玉（LONG+SHORT）合計 ≤0.12・_verify_cap 実測＋score.assert_hard_constraints（非該当なし）。
- **H2** leak なし: 特徴量＝Phase 0 leak 検証済み parquet のイベントバー行のみ（因果）。検出器 fit＝学習窓（2021-04〜2024-12）のみ・TRAIN_END assert・採点窓 parquet は predict のみ。教師ラベルは学習窓内の未来を使う（＝教師生成は学習窓に閉じる・推論時は特徴のみ＝本番再現可）。grep assert（負shift/center=True 不使用）。
- **H5** 約定モデル: eval_engine 固定（entry maker TTL3・TP maker・SL maker・TIME taker+slip）。
- **H6** 価格非依存: 特徴は pct/比率/σ（blacklist 64 除外 assert）・イベント/出口も σ/ATR スケール。
- **H8** 期間: periods.py import（require_period_source）・fit 〜2024-12（<TRAIN_END）・採点 2025-06〜2026-02・封印不参照。
- **H13** judge 固定: score.py/eval_engine に触れない（今回変更ゼロ）。
- **H15** ボラ逃げ禁止: 向きスコアなし（両側 MR）・検出器は執行可否のみ・重要度で ATR/vol 家族非支配を確認（v1/v2 実測 最下位）・実装後も feature importance を report で確認。
- **H16** 1変更: 検出器ゲートのみ（C 節）。
- H9/H10: size 0.024（≥0.0001 BTC・×価格≥5USDT）・固定値扱いしない。H12: 異常値 STOP は score.anomaly＋本セッションで実働（leak 検出実績）。

## F. 受け入れ判定（採点前ゲート・E37 hooks ⑦⑨⑫ 対応）
- **件数/日を上げる（高頻度＝役割・一級）**: 採点窓 **件数/日 ≥3**（v4 0.47件/日 の6倍以上に上げる・E36 1.05 も上回る）。件数がこの床を割ったら**その版は不合格＝検出器の作りを直して次版**（低頻度で net を作る形にしない）。
- **⑨短保有（分単位）**: 保有中央値 ≤30分 目安・最大60分バックストップ（probe 実測 中央20〜30分）。
- **⑦手数料を超える TP 幅（maker 往復）**: precheck P1 で TP側 breakeven >1 を確認（TP=SMA∓0.5σ・SCALP_FLOOR 0.08% で小TP手数料割れ防止・maker往復 0.028%）。
- **⑫5分足設定**: RSI9（rsi9__5m）・MTF 上位足整合列を検出器特徴に含む（technical_kb §4/§5・実装で列存在 assert）。
- **自己検査**: cap・leak grep・ラベル/blacklist 除外 assert（わざとラベル列を混ぜて停止するかメタ確認）・--no-gate 恒等・θ選定ログ。
- **学習窓で純増を先に**（H8）: precheck 全体 breakeven ≥1.0 PASS が採点の前提（FAIL なら採点しない・原因分解して次版）。
- **公式判定＝score.py 両窓**: 採点窓で E37 過去最良（プラス）＋ non-degenerate（件数床と併せて）。学習窓の AUC/net では「効いた」と言わない。
- **較正**: report H 節で検出器確率帯×実 net の単調性を確認（逆較正なら検出器の作りを疑う）。

## 実装やること（順番）
1. e37_range_scalp.py を v5 に書き換え: イベント生成（dev_z±1.0σ∩反転バー・両側）→ 教師生成（Triple Barrier・学習窓）→ 検出器学習（purged 5fold OOF＋全学習窓 re-fit・2603特徴 assert）→ θ 学習窓選定 → 連続執行（単一スロット・maker TTL3・TP/SL/TIME）→ strat_base 出力。
2. py_compile → --diagnostic（候補数/ゲート通過数/日）→ --tag v5 本走 → precheck → PASS なら score.py 両窓 → report --vs v3_005 → analyze。
