# acceptance — E37 v21: 入口の反転確認（armed DC）＋uptrend 畳み分岐（Entry×Exit セット・2026-07-12）

TARGET: scripts/priority_rebuild/e37_range_scalp.py

## DESIGN_CONTRACT
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["range_ok_rg5", "short_only_v11", "v21_armed_dc_entry", "v21_uptrend_fold", "rg5_selftest_labels", "_verify_cap"]
}
```

## LEVER（improvement_plan から逐語引き継ぎ）
入口の反転確認（stoch(9,3)デッドクロス∩RSI9水準帯・パラメータは学習窓のOptuna/木で最適化・件数維持が合格基準）と uptrend発火時の畳み方（即takerから新規停止＋建値側へ縮むmaker逃げへの分岐・場面特徴で学習窓OOF選定）のEntry×Exitセット

## 網羅マトリクス（entry_exit_matrix）参照
- 実装セル＝『グリッド: E37』の新セル **#28**＝#27（v20＝RG-v5・確認なし・regime exit 即 taker）の Entry 側へ #9（反転確認 Ee2）＋#20/#25（stoch_k の学習・Ef2）を統合し、Exit 側の X-g regime exit を「即 taker から maker 逃げ分岐」へ拡張。未試行: あり（#7〜#20 ほか・全体からの選定理由は improvement_plan STEP3 重なり判定＝A1 出血に入口と出口の両側から効く）。
- コンフルエンス（基本原則①）: 入口は単一閾値でない＝RG-v5（1h 帯対 ∩ 上げトレンド状態機械 非発火 ∩ 5分帯内）∩ 上端到達（armed）∩ stoch(9,3) デッドクロス ∩ RSI9 水準帯（要否・帯はセル別に学習）∩ TP1幅≥手数料床。
- Exit 状態機械（基本原則③）: 現行分岐（災害SL／TP1 部分／TP2 反対側／deadline shrink／dd ピーク反転／down 含み損前倒し／破れ／TIME backstop）は不変。**「レンジ前提の終了（uptrend 発火）」というポジション状態への発火枝だけを「即 taker 1択」から「場面分岐（maker 逃げ／即 taker）」へ質を是正**する。

## ★戦略照合（enforce_strategy_anchor）
- STRATEGY_ANCHOR 逐語: **e37=range,short_only,scalp**
- GATE_IDENT=range_ok_rg5（入口を担当局面＝レンジの判定で制約する関数・RG-v5・v20 から不変・DESIGN_CONTRACT 登録済み）
- SIDE_IDENT=short_only_v11（SHORT のみ・上限ゾーン到達のみ使用・LONG 入口の生成経路なし・DESIGN_CONTRACT 登録済み）
- 経緯の係留（ledger 直近 ARC 逐語）: 直近 ARC order=35「E37 v20 RG-v5レンジ判定移植＋レンジ期間を漏れなく取る上端入口」＝件数の器は機能（新規 7.58件/日・SL ほぼ消滅・PARTIAL_TP 948件 +$2,901）・最大出血＝uptrend 発火時の taker 即クローズ TREND_CONT 856件 −$3,574（対照＝枝OFF が学習窓 +$2,106 良い＝最悪点確定・L-336）。本 v21 は入口（確認なし）と出口（即 taker）の両側からこの出血を塞ぐ。
- 頻度役割（scalp）: **件数/日を上げる（高頻度＝役割）が一級の合格基準**＝新規件数/日が公式最新 v19_033 の 0.69 と v18_032 参考の 4.33 を上回ること。v20 の 7.58件/日 の器を極力維持する（まこさん 2026-07-12「スキャルなのでエントリー数は極力減らさないように」＝armed 方式は到達即の玉を「同じ到達波の DC バー」へタイミングシフトする設計＝玉の絶滅でなく建て時刻の移動・確認の要否をセル別に学習して効かないセルでは到達即を残す）。

## 深掘り4点
- **① 真因**: (a) 入口＝反転確認なしの到達即エントリー（v12 継承）が上げ進行中の玉を量産＝TREND_CONT 856件の供給源（N10: stoch_k_at_entry が唯一の両窓再現✓分離指標・負け玉中央値 59.6 vs 勝ち玉 50.8／学習窓 TREND_CONT lot の 61% が保有60分以内＝入ってすぐ轢かれ）。(b) 出口＝uptrend 発火の瞬間（上げトリガ確定時点＝局所最悪価格）に taker 成行で全量確定（対照実験: 枝OFF が学習窓 −$1,940 vs 枝あり −$4,046・勝ち玉切りは金額比 1.8% のみ＝巻き込みでなく最悪点確定が問題・L-331 同構造）。
- **② 期待値分解**: 総net＝件数×avg。件数＝7.58件/日 の器を維持（合格基準）。avg 側: (a) 入口確認で負け玉の期待値を圧縮（学習窓の当たり: DC 済み玉のみだと通過玉 net −$4,046 から −$114・TREND_CONT −$10,504 を先回り回避）＝敗率×平均損失の圧縮。(b) 畳み分岐で TREND_CONT の平均損失を圧縮（taker 費+slip $645 の maker 化＋最悪点確定の回避・建値フロア到達 41%[60分・楽観値]）。N7: 必要勝率不足 4.4pt＝平均負けを $3.98 から $3.34 へ縮める側の等価解を両レバーで狙う。
- **③ root か symptom か**: root（Y）。TREND_CONT は「exit_reason の1つ」でなく「入口の質（確認なし）×出口の執行（最悪点 taker）」の合成が根＝v13〜v18 の出口単独チューニング（symptom 側）で直らなかった実測の上で、入口の建て時刻と出口の執行方式という機構そのものを直す。
- **④ ベースアップ（2026-07-12 WebSearch 3本・ソース種別2以上・WebFetch 2本）**: (i) LuxAlgo「How to Combine Stochastic Oscillator with Key Levels」（WebFetch 精読）＝レジスタンス到達＋**%K/%D の明確なクロスオーバーを待ってから**ショート・単なる過熱数値でなくクロス確認・複数条件（価格反応/出来高/MTF）の一致でダマシ回避・SL はレジスタンス上＝**本 v21 の armed 方式（到達で武装しクロスで入る）と災害SL 構成の業界整合**。(ii) arxiv 2412.07461「A theory of passive market impact」（WebFetch 精読）＝passive limit は執行価格が良いが非執行リスクと adverse selection を負う・時間制約下の畳みは speed と impact のトレードオフ＝**「maker 逃げ＋期限 taker backstop」の分岐形が標準**（一律 passive も一律 aggressive も最適でない＝場面分岐の根拠）。(iii) arxiv 2512.12924「Interpretable Hypothesis-Driven Trading: A Rigorous Walk-Forward Validation」＋De Prado purged CV＝**学習窓の walk-forward/purged 検証つき選定が過剰適合防止の標準**＝連続ハイパラ探索（Optuna TPE）より離散メニュー×purged OOF 合意（既存 v17 帯層化基盤）を第一とする実装判断の根拠。＋range_scalping_kb §3（到達→拒否確認→エントリー）・entry_exit_matrix 基本原則①③。
- 出典 URL: https://www.luxalgo.com/blog/how-to-combine-stochastic-oscillator-with-key-levels/ ／ https://arxiv.org/html/2412.07461v1 ／ https://arxiv.org/pdf/2512.12924 ／ https://www.luxalgo.com/blog/how-to-adjust-stochastic-settings-for-scalping-success/

## ★疑似シミュ由来の固定値ゼロ
- (a) 候補メニューの出所: RSI9 帯 {なし, 45, 50, 55}＝まこさん指定「だいたい50以上」の近傍離散メニュー（a-priori・どれを使うかは学習窓選定）／armed 期限 {6, 12, 24}本・fold 期限 {6, 12, 24}本＝既存 shrink/TIME の時間尺度（a-priori）／stoch(9,3)＝KB §4/§5 の 5分足スキャル標準（既存 v14 実装の k9/d9 再利用）。probe の数値（−$114・1.62件/日・41% 等）は**どれも設計の固定値に使っていない**（方向性の確認のみ）。
- (b) メニューからの採択は全て学習窓の場面セル×purged 3分割 OOF＋ATR%帯層化合意（v17 基盤）＝採点窓不参照（L-267）。
- (c) 採否は probe でなく**実エンジン両窓 score.py の数字**で決める。

## やること（実装ステップ・全て --v21-set フラグ内・既定 OFF＝v20 恒等）
1. **フラグ**: --v21-set（既定 OFF＝v20 恒等 md5）・寄与分離用 --v21-entry-only／--v21-fold-only（どちらか片方だけ ON）。
2. **Entry（v21_armed_dc_entry）**: v20 の入口候補（range_ok_rg5 ∩ 上端到達）を「即 pend 発注」から「武装（armed）」に変更＝armed 中（range_ok_rg5 継続が条件・期限はメニュー選定）に stoch(9,3) の %K が %D を下抜けたバー（デッドクロス発生）∩ RSI9 水準帯（セル別メニュー選定・「なし」も候補＝確認が効かないセルは到達即を残す）で従来どおり maker 指値 pend（TTL3・tp_ge_sl／tp_floor・add 機構は不変）。k9/d9 は v14 実装と同式（過去 rolling のみ・H2）。
3. **Exit（v21_uptrend_fold）**: uptrend 発火バーの「pend 取り下げ＋新規/add 停止」は v20 不変。保有 lot の畳みをセル別分岐＝(a) fold＝当該 lot の deadline shrink の残り時間を M 本（メニュー選定）へ前倒し（既存 v13 機構再利用＝建値フロアへ縮む maker 指値・TP_FILLED/BE 級 maker 決済）・M 本経過で残存を TREND_CONT（taker・登録済み）(b) 即 taker＝現 v20 の枝（切迫場面用に温存）。分岐は発火時の場面特徴（含み損深さ・atr_pct・stoch_k・box_W）の場面セル別に学習窓選定。
4. **選定（_select_v21_params）**: 場面セル（LightGBM 1本の木・leaves≤6）×メニュー（entry: 確認要否×RSI9帯×armed期限／fold: M×taker）を purged 3分割 OOF＋ATR%帯層化合意（v17 基盤＝低ボラ帯でも純増∩各帯非悪化∩PARTIAL_TP 非毀損）で選定・選定表全行提示。学習窓のみ・採点窓不参照。
5. **自己検査**: OFF 恒等 md5（--v21-set なし＝v20_034 再現）／rg5_selftest_labels 再pass（RG-v5 一致が崩れていないか）／番人メタ確認 --v21-guard-check＝(a) DC を全バー False に強制すると v21 入口 0（armed が発火しない＝配線支配）(b) fold を全セル taker 指定にすると v20 と出口構成一致（分岐の恒等退行）(c) labels 改ざん検出（既存）／cap 実測 _verify_cap ≤0.048／leak 自己 grep（.shift(- ／center=True 0件・k9/d9/rsi9/armed は過去バーのみの逐次状態）。
6. **本走**: --tag v21 → 学習窓 diagnostic（新規件数/日の残存を最初に実測・合格基準照合）→ 選定 → precheck（be・--target 帯別証跡・ドリフト）→ 両窓 CSV → report/analyze --vs archive/v20_034（--train つき）。**どの判定でも両窓 CSV から report/analyze まで出す（データ捨て禁止・hook 9a4d348）**。

## D. 審判整合（acceptance_checklist D）
- 新 exit_reason: **なし**（TP_FILLED／BE_EXIT／TREND_CONT／TIME_EXIT の登録済み再利用・maker/taker 区分は既存登録どおり）＝score.py／eval_engine 無変更（H13・既知答えテストは変更なしのため再pass 不要だが確認実行）。
- uptrend 起因の畳みの計上: _stats（TREND_CONT_rg5 系）に fold 経由／taker 経由の内訳カウンタを追加（表示のみ・審判不関与）。
- サイドカー: §0 自動生成に v21 節を追加（_param_sections 拡張・PARAM_SECTION_SCHEMA_V11 準拠・--param-schema-selftest 再pass）。
- 出力: 共通書き出し _output_and_report（strat_base 経由・--tag v21 連番・archive 自動）。命名は e37_ 検知で pdca 強制に乗る。

## E. §4.6 ハード制約 照合
- **H1** cap: 本戦略同時最大 0.048 BTC（0.012×4 lot・v15 経路不変）＝_verify_cap＋score.assert_hard_constraints が実測。予算 0.12 は全採用戦略（E32b/E36/E28 等）の共有枠＝本戦略単独の枠ではない（合算は最終配分段で検証）。
- **H2** leak なし: k9/d9/rsi9＝過去 rolling のみ・armed／fold＝当該バー確定値の逐次状態機械・RG-v5＝確定バー ffill（v20 で検証済み・rg5_selftest_labels 再pass）・.shift(-／center=True 0件 grep。
- **H5** 約定モデル: entry maker 指値（close×(1+0.0001)・TTL3・不約定は建てない）／fold maker 指値（建値フロア床）／期限・切迫 taker+slip＝eval_engine 登録どおり。
- **H6** 価格非依存: stoch/RSI は 0-100・幾何は W 比・USD 絶対値の閾値なし。
- **H8** 期間分割: periods.py import（既存）・選定は学習窓のみ・採点窓不参照・封印不参照。
- **H13** judge 固定: score.py／eval_engine／precheck.py 無変更。
- **H15** ボラ逃げ禁止: 方向スコアなし（素ルール）・stoch/RSI は方向の確認ゲート（ボラ非依存）・ATR% は場面セルの分割特徴（サイジング/分岐用）で方向判定に不使用。
- **H16** 1変更・不再演: 変更はセット2箇所だが寄与分離フラグ（--v21-entry-only／--v21-fold-only）で1レバーずつ測れる形（v15/v16 のセット前例）。過去失敗との差分＝v11 の確認（陰転∩RSI9>70 過熱必須＝件数を殺した）と違い過熱を必須にせず要否をセル別学習／v12 の撤去根拠（stoch AUC0.61）は旧レンジ判定前提＝RG-v5 下の N10 両窓再現✓で再検証／v14 の再回転相殺（L-330）は入口の質側を今回直すことで再発条件を消す。

## F. 受け入れ判定（採点前ゲート・PDCA §8.4）
- 自己検査（上記5）を全 pass → 学習窓 diagnostic で**新規件数/日 ≥ 4.33（v18 実績）を最初に確認**（割れたら確認メニューの過しぼり＝選定へ差し戻し・件数を減らして net を作らない）。
- 学習窓で純増（対 v20_train −$4,046）→ precheck（be≥1.0 の門＋--target 帯別証跡＝低ボラ2帯 be・ドリフト）→ 両窓 score.py: **採点窓 net > v8_013（−$18）∩ 新規件数/日 > 4.33 ∩ 非degenerate ∩ PARTIAL_TP 非毀損（+$2,901 の収益源を壊さない・report C/K 節 --vs で確認）**。
- ⑨巻き込み: 入口確認が削った玉の行き先（PARTIAL_TP 減少分）と fold の勝ち玉切りを report L 節／_stats 内訳で確認。
- 割れたら「採用に至らず」と記録（ratchet・地面 v8_013 維持）・どの判定でも両窓 CSV→report/analyze まで完走。

## E37 スキャル基準（enforce_e37_pdca ⑦⑨⑫）
- ⑦ 手数料を超える TP 幅（maker 往復）: TP1 幅 ≥0.08%（maker 往復 0.028% の約2.9倍）不変・fold の maker 決済も建値フロア（損ゼロ級）以上のみ。
- ⑨ 短保有（分単位・保有4h再演防止）: TIME backstop 240分不変・fold は発火から M∈{6,12,24}本（30〜120分）で必ず畳み切る（uptrend 中の無期限保有をしない）。
- ⑫ 5分足設定 RSI9/MTF: 確認は 5分足 RSI9・stoch(9,3)・レンジ判定は 1h帯×15分構造×5分執行の MTF（RG-v5）。

## ARC マーカー（gen_improvement_arc 自動生成の源・数字は書かない）
<!-- ARC order=36 iter="E37 v21 入口の反転確認（armed DC）＋uptrend畳み分岐（Entry×Exitセット）" 前提="base=v20_034（RG-v5の器は機能・precheck FAIL＝採点温存・地面v8_013維持）・まこさん指示2026-07-12＝エントリーはレンジ上端でストキャスのデッドクロス・閾値はMLかオプチューナで最適化・エントリー数は極力減らさない・大量にエントリーさせExit側（ポジション状態機械）で利益最大化" 採否="未（実装→自己検査→学習窓diagnostic件数→OOF選定→precheck→両窓score.py）" base_csv="trades_e37_range_scalp_v20_034_score.csv" score_csv="trades_e37_range_scalp_v21_NNN_score.csv" train_csv="trades_e37_range_scalp_v21_NNN_train.csv" 狙い="v20の最大出血＝uptrend発火時のtaker即クローズ（対照＝枝OFFが学習窓+$2,106良い＝最悪点確定）と、その供給源＝確認なしの到達即エントリー（TREND_CONT lotの61%が保有60分以内・N10 stoch_kが唯一の両窓再現✓）を、入口と出口の両側から機構で塞ぐ" 内容="--v21-set（既定OFF=v20恒等）＝①入口を到達即から『到達で武装しstoch(9,3)デッドクロス発生バーで建てる』へ（RSI9帯・要否・武装期限はセル別メニューを学習窓選定・件数維持が一級基準）②uptrend発火時の保有畳みを『即taker1択』から『deadline shrink前倒しのmaker逃げ（期限で taker）／切迫のみ即taker』のセル別分岐へ（場面特徴で学習窓OOF選定）・寄与分離フラグ2本・score.py無変更H13" 方法="自己検査（OFF恒等md5・rg5_selftest再pass・番人3枝＝DC全False入口0/fold全taker恒等/labels改ざん・cap0.048・leak grep）→学習窓diagnosticで新規件数/日≥4.33を先に確認→場面セル×メニューをpurged3分割OOF＋ATR%帯層化合意で選定（選定表全行）→precheck（be＋--target帯別証跡）→両窓score.py（採点窓net>−$18∩新規件数/日>4.33∩非degenerate∩PARTIAL_TP非毀損）→report/analyze --vs archive/v20_034 --train（データ捨て禁止9a4d348）" -->

## 承認依頼
- 本 acceptance の承認（approve_impl）をお願いします。実装・自己検査・本走・precheck・（PASS 時のみ）両窓 score.py まで進めます。
