# acceptance — E37 v22「レンジ中の戻り売り DC 入口×レンジ下限 TP＋ピーク反転畳み・前兆逃げ（Entry×Exit セット）」2026-07-13

TARGET: scripts/priority_rebuild/e37_range_scalp.py

## DESIGN_CONTRACT
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": [
    "v22_range_dc_entry",
    "v22_low_anchor_tp",
    "v22_peak_fold",
    "v22_uptrend_warning",
    "range_ok_rg5",
    "short_only_v11",
    "tp_floor_check_v15",
    "v21_band_consensus"
  ]
}
```

## 網羅マトリクス参照
- **網羅マトリクス（entry_exit_matrix）の「グリッド: E37」#29 のセルを実装する**（2026-07-13 追加行＝本セット）。
- 未試行: あり（#7〜#20 系ほか＝マトリクス末尾の宣言どおり・潰し切るまで閉じない）。#29 は未試行セル全体を見渡した選定（2026-07-13 分析＝W別密度3.3倍偏り・ATR%≥0.3のみ両窓黒字・TREND_CONT 玉の67%に逃げ場・7/18 実例窓 0件、とまこさん指示「8回エントリーしてレンジ下限でTP＋Exit 側同時」）。

## ★戦略照合（enforce_strategy_anchor）
- アンカー逐語: STRATEGY_ANCHOR: e37=range,short_only,scalp
- 局面: GATE_IDENT=range_ok_rg5（RG-v5 の range 判定が立つバーのみ入口候補を生成・uptrend 発火で新規停止は不変）＝range 担当に整合。
- 方向: SIDE_IDENT=short_only_v11（LONG 入口の生成経路なし・上限側の戻り反転 DC のみ）＝short_only に整合。
- 頻度: DC 入口は到達型より発火機会が多く**件数/日を上げる**（実例 2025-07-18 窓で現行 0件 が DC 候補8件・受け入れ基準 F に件数/日 3.53 超を明記）＝scalp（件数一級）に整合。
- 経緯の係留（ledger 直近 ARC 逐語）: ledger ARC36「E37 v21 入口の反転確認（armed DC）＋uptrend畳み分岐（Entry×Exitセット）」の確定＝入口確認は TREND_CONT 出血 +$1,980 圧縮・PARTIAL_TP −$1,724 巻き込みで採点窓正味 +$224・DC は「発生」だけで「水準」を見ない（負け玉 stoch_k 62.4 vs 勝ち 48.2）＝本 v22 はその入口を到達依存から解き、TP アンカーと出口畳みをセットで動かす次段。

## LEVER（improvement_plan から逐語引き継ぎ）
入口の武装を上端到達からレンジ判定中の5分stoch(9,3)DC発生（戻り売りの反転確認）へ一般化し、TPアンカーをレンジ下限（直近M本押し安値・Mと場面別採否は学習窓層化合意で選定）に置き、出口はピーク反転畳みの常設（uptrend前兆コンフルエンス）と前兆fold前倒しをセットで入れる（v22 Entry×Exitセット）

## Exit 状態機械（ポジション状態と発火枝の分岐表・v22 での変更点）
| ポジションの状態（entry 後の動き） | 発火する Exit | v22 での扱い |
|---|---|---|
| 含み益が乗って TP1/TP2 到達 | PARTIAL_TP / TP_FILLED（maker） | **アンカーをレンジ下限（直近 M 本押し安値）へ**＝v22_low_anchor_tp |
| 含み益がピークから反転 | MFE_DRAWDOWN_CUT（maker 半畳み） | **常設候補化（k×fee 武装・r 割戻し・前兆コンフルエンス形もメニュー）**＝v22_peak_fold |
| uptrend 前兆（発火の1段手前） | deadline shrink 前倒し（maker 逃げ） | **新設**＝v22_uptrend_warning |
| uptrend 発火 | v21_uptrend_fold（fold=maker 逃げ／即 taker） | 現行維持（v21 継承） |
| 含み損からの建値回帰 | BE_EXIT（maker） | 現行維持 |
| レンジ破れ（出来高∩帯外持続） | RANGE_BREAK_EXIT（taker） | 現行維持 |
| 深い逆行 | 災害 SL（res_hi＋1.0W・maker） | 現行維持（浅 SL は足さない＝L-331） |
| 時間切れ | deadline shrink→TIME_EXIT（240分 backstop） | 現行維持 |

## 深掘り4点
- **① 真因**: (入口) 到達型武装の幾何＝上端ゾーンに近い狭レンジほど常時武装・広レンジは価格が上端に届かず不発（W別エントリー密度 51.3 vs 15.6件/100h・3.3倍偏り・2025-07-18 実例窓 0件）。(出口) TREND_CONT 玉の 67%（学習窓 70%）は発火前に往復手数料超えの含み益ピークを持つのに畳む枝が実質不活性（MFE_DRAWDOWN_CUT 発火33回＝1セル継承定数のみ）＝発火時 taker の最悪点で確定。
- **② 期待値分解**: 平均勝ち $3.43 / 平均負け $3.91・必要勝率 53.3% vs 実際 46.6%（不足 6.6pt）。動かすのは (a) 平均勝ち＝レンジ下限 TP は現行 TP1（中間）より深いアンカー・7/18 実測 幅 0.18〜0.38%（手数料床の 2〜5倍） (b) 平均負け＝ピーク畳みで TREND_CONT の実損 −$1,123（採点窓・両窓再現）を含み益側で先取り (c) 件数＝DC 入口で広レンジの機会を回収（増える方向）。
- **③ root か symptom か**: root。入口の幾何（どの場面で発火できるか）と出口の状態分岐（ピークで畳めるか）は構造そのもの。位置の固定値いじり（v19 の一律 res_hi）は symptom 対応で件数 −84% になった実測があり、本設計は場面セル×学習窓選定に線引きを委ねる。
- **④ ベースアップ**: WebSearch 5本＋WebFetch 2本（2026-07-13・luxalgo/quantifiedstrategies/babypips/fxopen＋arxiv＋quantpedia＝実戦・学術・クオンツの3種別）＝(i) レンジスキャルの TP は「反対側のサポートレベル」が論理的出口（luxalgo Scalping Basics S/R・How to Combine Stochastic with Key Levels） (ii) ストキャス売りクロス（K が D を下抜く）はレンジ相場で信頼性が上がり、キーレベルとの一致が必須＝単独では使わない（luxalgo Stochastic in Trending vs Ranging） (iii) 平均回帰の出口は scale-out＋利益が乗ってからのトレーリング/ピーク確定が標準で、trailing stop と指値売りの併用に最適性の理論結果がある（luxalgo Mean Reversion Playbook・quantifiedstrategies Exit Strategies・arxiv 1701.03960 Optimal Trading with a Trailing Stop・arxiv 1411.5062 Optimal Mean Reversion Trading with Stop-Loss） (iv) pullback（戻り）トリガの平均回帰はレンジ市場の標準形（quantpedia pullback strategy discovery）。range_scalping_kb §3/§4（ゾーン到達＋確認・TP=レンジ反対側/中央・幅>往復コスト）と整合。

## やること（実装項目・--v22-set・既定 OFF＝v21_040 構成と恒等）
1. **v22_range_dc_entry（入口）**: range_ok_rg5 が立つバーで、5分 stoch(9,3) の K が D を下抜いた発生バーに SHORT 指値（close×(1+0.0001)・TTL3・maker）。到達武装（v21_armed_dc_entry）は入口メニューの対決候補として残す＝学習窓選定が {v22 range-DC / v21 armed DC} を場面セル別に選ぶ。RSI9 水準（なし/45/50/55）のメニューも継続。
2. **v22_low_anchor_tp（TP アンカー）**: TP の基準を「レンジ下限＝直近 M 本 low の最小値（当該バー除外の shift(1)・過去のみ）」へ。TP1=(建値+下限)/2 で半分（PARTIAL_TP）・TP2=下限×(1+V11_SL_BUF) で残り（TP_FILLED）。M は候補メニュー {24/36/48}本（2〜4時間・幾何 a-priori）から場面セル別に学習窓選定。現行アンカー（帯中央/サポート帯上端）も対決候補としてメニューに残す。tp_floor_check_v15（TP1幅≥0.08%）と R:R 物理条件は全候補に適用＝薄い場面・下がり切った直後は建てない。
3. **v22_peak_fold（出口・ピーク反転畳みの常設）**: 全セル×玉タイプを対象に「含み益 ≥ k×往復fee 到達で武装（k∈{2,3}）・ピークから r 割戻し（r∈{0.3,0.5}）で半分 maker 畳み」を候補化（決済は登録済み MFE_DRAWDOWN_CUT maker を再利用）。発火条件は (a) 常設 (b) v22_uptrend_warning とのコンフルエンス限定 の2形をメニューに置き学習窓選定（単一閾値で組まない＝基本原則①）。
4. **v22_uptrend_warning（前兆・条件情報）**: RG-v5 uptrend 状態機械の発火条件の半値水準（15分足2本連続切り上げ／陽線2連続∩累積+0.25%／90分安値+0.5%＝幾何 a-priori・全て確定バーのみ）で warning フラグを立てる。warning 中は deadline shrink の期限を前倒し（v21 fold と同じ maker 逃げ機構の早駆動）・新規 pend は据え置き（新規停止は発火時のみ＝現行不変）。
5. 選定は v21_band_consensus を再利用（層化合意・時間3fold・ATR%帯）。**条件分け＝玉集合を動かす候補（入口メニュー・TP アンカー）には (iv) PARTIAL 平均非悪化を適用しない・件数床は incumbent×2/3 の相対値／玉集合を動かさない候補（v22_peak_fold・warning 前倒し）には (iv) を適用**（L-337）。不採択理由はログ表示。
6. §0 自動生成（_param_sections）に v22 の全メニュー・選定値・warning 定義を実値から追記（スキーマ selftest 断言込み）。
7. 番人（メタ確認）: (a) DC 全 False 差し替えで v22 入口 0 件（配線証明） (b) M 極端値（M=1）で下限が建値に張り付き床チェックが全拒否（物理条件の実効） (c) v22_peak_fold の r 極端値（r=0.01）で発火が支配（枝の実効） (d) OFF 恒等 md5（--v22-set 無し＝v21_040 構成と完全一致）。
8. 走行は --tag v22（連番）・_output_and_report（strat_base 経由）・両窓 CSV→report --vs archive/v21_040 --train→analyze を必ず出す（どの判定でも・9a4d348）。

## ★疑似シミュ由来の固定値ゼロ
- (a) M{24/36/48}・k{2,3}・r{0.3,0.5}・前兆の半値水準は幾何 a-priori（保有時間整合・fee 倍率・発火条件の半分）＝probe の特定数値を焼いていない。
- (b) 7/18 概算（+$42・6/6 到達）は妥当性のあたり付けのみ＝設計の固定値・採否根拠に使わない。
- (c) 採否は実エンジンの学習窓選定（層化合意）＋precheck＋両窓 score.py の数字で決める。

## D. 審判整合（acceptance_checklist）
- 新しい exit_reason: **なし**。PARTIAL_TP / TP_FILLED / SL_FILLED / TIME_EXIT / TREND_CONT / MFE_DRAWDOWN_CUT / BE_EXIT / RANGE_BREAK_EXIT の登録済みを再利用＝score.py / precheck.py 無変更（H13・既知答えテストは現状 pass のまま）。
- コスト種別: 入口 maker（指値 TTL3）・TP1/TP2/畳み maker・TIME/TREND_CONT taker＝現行分類のまま変更なし。
- 命名: --tag v22 連番（require_tag_for_experiment 準拠）・probe を作る場合は *_probe.py 命名。
- サイドカー: _output_and_report（strat_base 経由・ratchet_io）で <stem>_params.json 自動出力（§0 に v22 実値）。
- 共通土台: strat_base import（load_5m・_verify_cap・_funding_cost・_output_and_report）＝現行のまま。

## E. §4.6 ハード制約 照合
- H1 cap: 合計 0.12・本戦略同時最大 0.048（2 lot）不変＝_verify_cap＋score.assert_hard_constraints 実測。
- H2 leak: DC=過去 rolling のみ／レンジ下限=shift(1) 済み rolling min／warning=確定 15分足のみ。.shift(- や center=True は使わない（使う行が出る場合は H2OK 因果性宣言必須＝現設計では該当なし）。
- H5 約定モデル: entry 指値 maker TTL3・TP/SL 指値 maker・TIME/能動 taker+slip＝eval_engine 準拠・変更なし。
- H6 価格非依存: M は本数・k は fee 倍率・r は比率・前兆は %＝USD 絶対値なし。
- H8 期間: periods.py import（TRAIN_END/SC_START/SCORE_END/SEAL_START）＝学習窓のみで選定・採点窓/封印は不参照。
- H9 最小注文: 半 lot 0.012 BTC ≥ 0.0001・5 USDT 以上＝現行のまま。
- H13 judge 固定: score.py / eval_engine / precheck.py 無変更。
- H15 ボラ逃げ: 入口の方向スコアに揺れ幅を使わない（DC＝方向の反転確認・ATR% は場面セルの特徴のみ）＝非該当構造を維持。
- H16 1変更: Entry×Exit の1セット（v21 と同型の承認単位）。過去の轍の回避＝v19 の一律位置固定は場面セル選定で・L-334 の守り枝相殺型は前兆コンフルエンスで・L-337 の選定の門は条件分けで・L-331 の浅SLは足さない（災害SL 維持）。

## F. 受け入れ判定（採点前ゲート）
- 自己検査: OFF 恒等 md5（v21_040 一致）／py_compile／DESIGN_CONTRACT 8識別子／番人4枝（やること7）／cap 実測／leak 自己 grep／§0 スキーマ selftest。
- 学習窓: v21_band_consensus（条件分け込み）で選定＝選定表全行ログ・対 incumbent（v21_040 構成）純増が門。
- precheck: 学習窓 be・--target 帯別証跡（FAIL なら採点温存・それでも両窓 CSV→report/analyze は必ず出す＝データ捨て禁止）。
- 両窓 score.py: 採点窓 net が v21_040 参考 −$465 を上回る ∩ **新規件数/日 > 3.53（v21 比で件数/日を上げる＝scalp 役割の一級基準）** ∩ 非 degenerate ∩ PARTIAL_TP の器の非毀損（report C/K 節で確認）。
- ⑨ 巻き込み: v22_peak_fold が勝ち玉に当たる量（採点窓 母集団 +$419・学習窓 +$1,457 が上限リスク）を report K 節（平均勝ち）と選定 (iv) で確認・毀損が回収を超えるなら不採択のまま走らせ結果を記録。
- スキャル一級基準: ⑦ TP1 幅 ≥ 0.08%（maker 往復の約2.9倍）維持／⑨ 短保有＝TP1 分単位・TIME backstop 240分以内維持／⑫ 5分足設定＝stoch(9,3)・RSI9・MTF は RG-v5（1h/15m/5m）。

<!-- ARC order=37 iter="E37 v22 レンジ中の戻り売りDC入口×レンジ下限TP＋ピーク反転畳み・前兆逃げ（Entry×Exitセット）" 前提="base=v21_040構成（RG-v5+armed DC+fold・precheck FAIL採点温存・地面v8_013維持）・まこさん指示2026-07-13＝7/18型のレジサポ幅があるレンジで8回エントリーしレンジ下限でTP＋Exit側ピーク畳み同時" 採否="未（実装前）" base_csv="trades_e37_range_scalp_v21_040" score_csv="" train_csv="" 狙い="到達型武装の幾何（狭レンジ乱発・広レンジ不発＝W別密度3.3倍偏り）とTREND_CONT玉の含み益取り逃し（67%に逃げ場・−$1,123両窓再現）を、入口と出口の両側からセットで直す" 内容="入口=range_ok_rg5中の5分stoch(9,3)DC発生バーで建てる（到達武装はメニュー対決）・TPアンカー=レンジ下限（直近M本押し安値・M{24/36/48}メニュー）・出口=ピーク反転畳み常設（k×fee武装・r割戻し・maker半畳み）＋uptrend前兆warningでshrink前倒し" 方法="学習窓のみv21_band_consensus層化合意（玉集合可動候補は(iv)不適用・件数床incumbent相対＝L-337）→OFF恒等md5→番人4枝→precheck→両窓score.py（件数/日>3.53∩net>−$465∩PARTIAL_TP非毀損）→report/analyze --vs v21_040" -->
