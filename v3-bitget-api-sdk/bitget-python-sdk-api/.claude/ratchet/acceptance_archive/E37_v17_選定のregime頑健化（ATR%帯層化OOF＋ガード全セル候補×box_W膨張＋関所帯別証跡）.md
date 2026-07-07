# acceptance — E37 v17 選定の regime 頑健化（ATR% 帯 層化 OOF 合意＋ガード全セル候補×box_W 膨張検知＋関所の帯別証跡）

TARGET: scripts/priority_rebuild/e37_range_scalp.py
TARGET: scripts/priority_rebuild/precheck.py
TARGET: scripts/priority_rebuild/test_precheck_band_known_answers.py
（TARGET 2〜3行目＝承認済み本文「関連1」「やること6」の precheck --target 合格条件拡張と、その既知答えテスト新設を、hook が読む TARGET 形式に再掲しただけ＝スコープ不変。本提案は網羅マトリクス（entry_exit_matrix）#26 の選定枠変更・Exit 状態機械は現行維持・コンフルエンス設計・閾値は ML 最適化＝学習窓 OOF 層化選定＝下の本文のとおり）
（関連1: scripts/priority_rebuild/precheck.py の --target 合格条件拡張＝判定器の変更。本 acceptance の承認がその承認を兼ねる・既知答えテスト再pass＋番人を「やること6」に明記）

## LEVER（improvement_plan 2026-07-07 から逐語引き継ぎ）
<!-- LEVER: _select_v16_params の OOF 合意区間＝時間3分割 → 学習窓内 ATR% 帯の層化分割（低ボラ帯を必ず含む・低ボラ帯でも純増しPARTIAL_TPを毀損しない候補だけ採択） -->
- 実装形の明確化: purged 時間3分割（leak 対策）は**維持**し、OOF 予測の**合意判定**を entry 時 atr_pct の帯スライスで行う＝「時間 fold の合意」から「時間 fold×ATR% 帯の層化合意」へ。低ボラ帯を必ず含み、低ボラ帯でも純増し、PARTIAL_TP を毀損しない候補だけ採択する。

## 網羅マトリクス参照と Exit 状態機械（enforce_combo_matrix）
- 本提案は**網羅マトリクス（entry_exit_matrix）の E37 グリッド #26 の選定基盤の物差し変更**（セルの中身でなく選定枠＝ARC31 の次軸として #26 行に明記済み）＋ガード守備範囲の拡張（#26 の guard 軸を全セル候補へ）＝採点後にグリッドへ #27 として追記する。
- **未試行: あり**（#7〜#21・#14 需給 taker_ls SHORT 対称性・#11 MTF 整合は続弾候補として残る。出口 SL 軸単独セル #7/#8/#13/#18 は v13 実測の整理どおり入口/セット軸を含む組で見る）。選定は未試行セル全体を見渡した上で、v16 実測（probe (a)(b)(c)＝補填合格・セル対応の逆転・ガード発火0）が示す「物差しの上流」を先に直すのが全候補に効く＝最有力。
- **①コンフルエンス**: 単一指標・単一閾値で組まない＝場面セル（stoch_k×ATR%×box_W の木）×玉タイプ×帯層化の複数条件の同時成立で採択を決める（ガードも 変位∩クラスタ基準／BBW>q90∩終値>2σ∩出来高>20avg の AND）。**②ML 最適化**: 全水準は学習窓のみの purged OOF 選定（L-267・固定値の手調整なし）。
- **③Exit＝ポジション状態機械は現行維持**（v15/v16 の分岐一式・水準の候補格子も v16 のまま）。本提案は分岐を足す/引くでなく「どの候補を採択するかの合意規則」と「ガードの適用範囲」を直す:

| ポジション状態（entry 後） | 発火 Exit（現行維持） | v17 で変わる点 |
|---|---|---|
| 含み益が TP1/TP2 へ伸びる | PARTIAL_TP／TP_FILLED（maker） | 採択条件に「PARTIAL_TP 玉数・net 非毀損」を追加（勝ち玉保護） |
| 含み益がピークから反転 | MFE_DRAWDOWN_CUT（maker） | 格子不変・層化合意で再選定 |
| 逆走後に建値へ回帰 | BE_EXIT（建値フロア maker・逆走 arm＋時間 arm） | 格子不変・層化合意で再選定 |
| クラスタ基準から上放れ＝トレンド移行 | TREND_CONT（taker・登録済み再利用）＋クールダウン | **ガード候補を全セル一律にも開放＋box_W 膨張検知を候補に追加** |
| レンジ構造の破れ | RANGE_BREAK_EXIT（taker） | 格子不変 |
| 本物の逆行が深い | 災害SL SL_FILLED（maker） | 格子不変 |
| 時間切れ（TP1 未達テール） | deadline shrink → TIME backstop（tmax/down 場面連動） | 格子不変・層化合意で再選定 |

## ★戦略照合（enforce_strategy_anchor）
- アンカー逐語: **e37=range,short_only,scalp**（adopted_strategies.md STRATEGY_ANCHOR・cat_requirements §1.2.1）
- GATE_IDENT=range_ok_v11（1h タッチ実績 S/R ゾーン ∩ 5分ブレイク離脱＝担当局面レンジの入口制約・不変）
- SIDE_IDENT=short_only_v11（LONG 入口の生成経路なし・不変）
- 頻度役割: scalp＝件数/日を上げる（F 合格基準に明記）・勝ち玉保有は分単位・4h は逆走テール backstop 限定。
- ledger 直近 ARC の逐語引用（order=31）: 「E37 v16 Entry×Exitセット最適化 第2弾（回帰救済×トレンドガード×候補格子の一括OOF）」＝採用に至らず（precheck --target FAIL＝学習↔採点ドリフト 28.6pt≥20pt で採点温存・学習窓 net 初プラス +$186・be 1.12＝E37 初の ≥1.0・採点窓参考 CSV −$96）。本 v17 はその選定の物差しを直す直接の続き。

## 深掘り4点
- **① 真因**: 選定の物差し（OOF 合意）が帯の偏りを見ない。probe (a)（玉単位・検算 report 一致）＝学習窓 ATR% 0.2-0.3 帯は 4,067玉 −$338・be 0.32 の恒常赤字（構成 32.1%＝最大）なのに、0.3 以上の帯（be 2.16〜2.36・+$565）の黒字が補填して全体 be 1.12 が門を通過。probe (b)＝学習窓で「良いセル＝通常サイズ」とされた玉が採点窓 0.2-0.3 帯 −$2.01/玉と最悪＝セル別ツマミの対応が窓間で逆転。probe (c)＝ガード（変位/BB）は cell1/cell5 限定採択のため 12/02・2/25 の両トレンド移行日に発火 0（12/02 は box_W が 0.53 から 4.39 へ膨張＝ゾーン再基準化の実測）・別日に 44玉 −$146 のコストのみ発生。
- **② 期待値分解**: 採点窓参考の期待値 −$0.07/玉。プラス転換に等価な動き＝勝率 71.1 から 72.1（+1.0pt）／平均負け $4.42 から $4.19（−$0.23）／平均勝ち $1.71 から $1.80（+$0.09）（analyze N7）。層化合意は「帯別で純増しない採択の混入」をなくす＝主に選定ミス由来の負け側（帯赤字の温存・勝ち玉毀損 −$1,178 の再発）を狙う。ガード守備範囲は災害日クラスタ（12/02・2/25 型・採点窓計約 −$220）を狙う。
- **③ root か symptom か**: root。個々のツマミ（symptom）でなく全ツマミの採択を決める上流（物差し）＝候補を広げるほど悪化した v15 から v16 への実測（全 ATR% 帯で avg/玉 が悪化）の根。
- **④ ベースアップ（証跡・WebSearch/WebFetch 2026-07-07）**:
  - arxiv 2512.12924（walk-forward 厳密枠組み・**regime-aware segmentation＝学習/検証窓をボラ等のレジームで条件付ける拡張**が非定常環境の頑健化として整理され・実証では**高ボラ期に稼ぎ安定期に負ける regime 依存**を報告＝レジーム別に検証・合意する必要の学術裏付け・WebFetch 精読）。
  - SSRN 6324079 WFC（**単一最良パラメータの walk-forward 選定は「偶然の OOS 好成績」で偽の確信を生む**＝パラメータ集合全体で診断すべき・本文 403 のためスニペット引用と明記）。
  - github eslazarev purged-cross-validation paper（purge/embargo が塞ぐ leak 2種と**複数 fold/path 集計が単一 split より頑健**＝現行 purged 3分割 OOF 維持の裏付け・WebFetch 精読）。
  - hudson-and-thames mlfinlab CPCV（複数 backtest path 生成で過剰適合軽減＝選定枠の続弾拡張候補）。arxiv 2601.04490（重尾下の頑健検定・グリッド全点合格の頑健化文脈・スニペット）。
  - KB: trade_analysis_methods_kb §6（Walk-Forward/Purged・DSR/PBO・IS から OOS 劣化 30-70%）／analysis_playbook §2.5 MRP（最悪 regime を robust 下限に＝本提案はその ATR% 帯版）／range_scalping_kb §5（破れ3判定・box_W 膨張検知はそのゾーン構造版）。probe e37_v16_scene_drift_probe（read-only・検算 report 一致）。

## 方針・狙い（前 iter の何を受けて何を狙うか）
- v16（学習窓 net 初プラス・ドリフト関所 FAIL＝採点温存）の壁＝**持続性**に対し、「学習窓で選んだ候補が採点窓で消える」機構そのもの（帯の補填・セル対応の逆転・ガードの守備範囲）を選定の物差し側で塞ぐ。**学習窓 net の見かけ（+$186）は下がることを許容**し、「どの帯でも成立する採択」だけ残す＝L-320 型（4回目）の再発を選定段で止める。関所（precheck --target）には「帯別頑健の機械証跡」の門を追加し、入口分布のドリフトが大きくても証跡があれば採点を authorize する（証跡が無ければ現行どおり停止＝弱体化ではない）。

## やること（実装項目）
1. **--v17-exit-set**（既定 OFF）: ON で v16 候補格子＋下記 4/5 の追加候補を **v17_band_consensus** の層化合意で一括選定。OFF 恒等＝--v16-exit-set 経路・v15 経路の出力が本変更前後で md5 一致（2系統）。
2. **V17_ATR_BAND_EDGES = [0.15, 0.2, 0.3, 0.4]**（entry 時 atr_pct の帯境界・precheck P3 の既存区切りと同一＝a-priori・成績で選ばない）。帯割当は entry 時点の atr_pct のみ使用（t 時点取得可能・H2）。
3. **v17_band_consensus（_select_v17_params）**: purged 時間3分割 OOF は不変。候補の採択条件を「(i) OOF 合計純増 ∩ (ii) 低ボラ2帯（atr_pct 0.2 未満）の合算で純増 ∩ (iii) 各帯で incumbent 比 非悪化 ∩ (iv) **partial_tp_protect_v17**＝PARTIAL_TP の玉数・net が incumbent 比 非悪化」に変更。incumbent＝v15 選定値（現行 OFF 挙動）。選定表は全行出力（帯別内訳つき）。
4. **guard_global_v17**: トレンド移行ガード（変位 k∈{0.5,0.75,1.0,1.5}×W_base／BB 拡大）を「全セル一律適用」の候補としても格子に追加（セル別候補は維持・どちらを採るかは 3 の層化合意が決める）。
5. **boxw_expand_guard_v17**: クラスタ初回 entry 時の box_W を基準に、現在 box_W ≥ m×基準（m∈{1.5, 2.0}・W 比の幾何 a-priori 格子）でトレンド移行と判定し全 lot TREND_CONT 離脱＋クールダウン（probe (c) の膨張実測 0.53 から 4.39 を捕まえる機構・TREND_CONT 再利用＝score.py 無変更 H13）。
6. **precheck.py --target の合格条件拡張（判定器の変更）**: ドリフト最大 ≥20pt の場合でも、「train CSV の帯別 be（玉単位）で、採点候補側の構成最大帯を含む低ボラ2帯の合算 be ≥ 1.0」を precheck 自身が計算・表示し、満たす時のみ **WARN-PASS（採点 authorize・証跡を出力）**。満たさなければ現行どおり停止。**既知答えテストに帯別 be の既知答えを追加して再pass＋番人（わざと低ボラ帯赤字の train を渡して停止することを確認）**。採点候補側は現行どおり特徴分布のみ参照（PnL 列 drop 済み・L-267 維持）。
7. 自己検査一式: OFF 恒等 md5（2系統）・py_compile・DESIGN_CONTRACT 照合・**番人メタ確認（層化合意にわざと「低ボラ帯赤字の候補」を混ぜて不採択になるか／partial_tp_protect をわざと外して採択が変わるか）**・cap 実測 0.048・leak 自己 grep（.shift(- / center=True 追加 0 件）。

## ★疑似シミュ由来の固定値ゼロ
- (a) 帯境界 [0.15/0.2/0.3/0.4]＝precheck P3 の既存 a-priori 区切りの再利用（成績で選定していない）。ガード k 格子＝v16 と同一。m∈{1.5,2.0}＝W 比幾何の a-priori 格子。すべて採択は学習窓 OOF（層化合意）が決める。
- (b) probe の数値（+$110／be1.56／64〜68% 等）を設計の固定値・採否根拠に焼かない（あたり付けのみ）。
- (c) 採否は実エンジン両窓 score.py の数字で決める。

## D. 審判整合
- 新 exit_reason なし（TREND_CONT／BE_EXIT 等 登録済み再利用）＝ **score.py・eval_engine 無変更（H13）**。
- precheck.py の変更は「やること6」のとおり判定器の変更＝本 acceptance のまこさん承認を変更承認とし、既知答えテスト再pass＋番人を必須（弱体化しない＝証跡なしの FAIL は維持）。
- 出力は共通書き出し（_output_and_report／ratchet_io・--tag v17 連番）・params_sidecar に v17 選定結果（帯別合意・ガード採択）を記録。

## E. ハード制約照合（§4.6）
- **H1**: 本戦略の同時最大 0.048 BTC（cap 0.12 共有枠内）・_verify_cap＋score.assert_hard_constraints 実測。
- **H2**: 帯割当・ガード判定は entry/当該バーまでの値のみ（atr_pct・box_W・BBW・出来高）＝t 時点取得可能。選定は学習窓のみ。.shift(-)/center=True 追加なし。
- **H5**: 約定モデル不変（maker 指値 TTL3・TIME/TREND=taker+slip）。
- **H6**: % / W比 / 無次元のみ（USD 絶対値の閾値なし）。
- **H8**: periods.py 正本・学習窓のみで fit/選定・採点窓の PnL 不参照（precheck --target も特徴分布のみ）。
- **H9**: size 格子 0.006/0.012（≥0.0001 BTC・≥5 USDT）。
- **H13**: score.py/eval_engine 無変更。precheck 変更は既知答え再pass（上記 D）。
- **H15**: atr_pct は方向スコアでなく「選定の層化軸」＝ボラで方向を当てない（入口の方向条件は不変）。
- **H16**: 1変更＝「選定の物差し（層化合意）」。ガード全セル候補化・box_W 膨張は、その物差しが守備範囲を選び直せるようにする同一選定枠内の候補追加（v16「候補格子の一括 OOF」を1レバーと扱った前例に整合）。過去に採用に至らなかった手の再演でないこと＝層化合意は初・ガードは適用範囲の拡張・box_W 膨張は新機構（v15 ladder 型の再演ではない）。

## スキャル一級基準（enforce_e37_pdca ⑦⑨⑫）
- **⑦ 手数料を超える TP 幅（maker 往復）**: TP1 幅 ≥0.08% 床（maker 往復 0.028% の約2.9倍）を全候補で維持。層化合意 (ii) は「低ボラ帯でも幅が手数料を超えて残る」ことの選定段での保証。
- **⑨ 短保有（分単位・保有4h 再演防止）**: 勝ち玉は分単位（PARTIAL 54分・MFE_DD 28分）を維持。4h は逆走テールの backstop 限定（デイトレ化しない）。
- **⑫ 5分足設定 RSI9/MTF**: 1h ゾーン構築×5分執行の MTF 構造・RSI9 系拒否確認（v11 経路）は不変。

## F. 受け入れ判定（採点前ゲート → 両窓）
1. 自己検査（やること7）全✅（1つでも落ちたら実装に戻る）。
2. 学習窓: _select_v17_params の層化合意で選定（選定表全行・帯別内訳）。**対 incumbent（v15 選定値）で OOF 合計純増 ∩ 各帯非悪化 ∩ PARTIAL_TP 非毀損**。合意を満たす候補が 0 なら「全候補が層化の門を通らず」と記録して停止（採点温存・それ自体が発見）。
3. precheck: train be ≥1.0 ∩ --target（帯別証跡の新判定）。FAIL なら採点温存で停止し記録。
4. 両窓 score.py（公式）: **採点窓 net > 地面 v8_013（−$18）∩ 新規件数/日 5.39 以上（下回れば採用に至らず）∩ 非degenerate ∩ PARTIAL_TP の玉数・単価を大きく損なわない ∩ 勝ち玉保有 分単位維持**。持続性の門を通過したら、続弾で入口側レバー（#14 需給・#11 MTF）により件数/日をさらに上げる（役割＝高頻度）。
5. ガード採択時は report C/F2 で TREND_CONT 発火玉の勝ち玉巻き込み額を確認（⑨巻き込み・fat-tail 保護）。
6. 割れたら「採用に至らず」と記録（ratchet・地面 v8_013 維持）し、続弾候補（攻め＝需給 taker_ls／構造＝ladder 幾何）へ作り込みを続ける。

## ARC マーカー（gen_improvement_arc 用・採点後に score_csv/train_csv の実 stem を記入）
<!-- ARC order=32 iter="E37 v17 選定のregime頑健化（ATR%帯層化OOF＋ガード全セル候補×box_W膨張＋関所帯別証跡）" 前提="E37未採用・v16=precheck --target FAIL（ドリフト28.6pt・学習窓net初プラス+$186/be1.12・採点温存・地面v8_013維持）" 採否="採用に至らず（層化の門 不通過＋precheck FAIL 3点[全体be0.13/追加玉be−0.46/ドリフト27.4pt＋帯別証跡なし 低ボラ2帯be0.04]＝採点温存・472候補中採択2本＝骨格−$1,894→−$1,730・採点窓参考CSV 1,285玉4.72件/日net+$7[0近傍・件数−12%は役割上マイナス面]＝ほぼ素の骨格構成がv16フル調整−$96に+$103勝る＝学習窓チューニングが採点窓を傷めていた実測・v16の+$186は帯補填の見かけと確定・初走はCSV出力前停止のデータ捨て設計＝まこさん指摘でhook恒久禁止[9a4d348]して再走・地面v8_013維持）" base_csv="trades_e37_range_scalp_v16_030_score.csv" score_csv="trades_e37_range_scalp_v17_031_score.csv" train_csv="trades_e37_range_scalp_v17_031_train.csv" 狙い="v16の壁＝持続性（学習窓選定が採点窓ドリフトで消えるL-320型4回目）に対し、選定の物差しを帯層化合意（低ボラ帯でも純増・PARTIAL_TP非毀損・各帯非悪化）へ替え、ガードの守備範囲（全セル候補・box_W膨張検知）を物差しが選び直せるようにし、関所に帯別頑健の機械証跡の門を追加して、学習窓の前進を採点窓へ運ぶ" 内容="--v17-exit-set（既定OFF=v16恒等）＝①V17_ATR_BAND_EDGES[0.15/0.2/0.3/0.4]（a-priori）②v17_band_consensus（purged時間3分割OOF×帯層化の採択条件4点）③partial_tp_protect_v17④guard_global_v17（変位/BBの全セル一律候補）⑤boxw_expand_guard_v17（m∈{1.5,2.0}×クラスタ初回box_W・TREND_CONT再利用）⑥precheck --target帯別証跡（判定器変更・既知答え＋番人）・score.py無変更H13・入口/ゾーン/勝ち枝は不変" 方法="自己検査（OFF恒等md5 2系統・py_compile・DESIGN_CONTRACT・番人メタ確認[帯赤字候補の混入で不採択/保護解除で採択変化/precheck番人]・cap0.048・leak grep）→_select_v17_paramsで学習窓のみ層化OOF選定（選定表全行・対incumbent純増∩各帯非悪化∩PARTIAL_TP非毀損）→precheck train be≥1.0＋--target帯別証跡→両窓score.py（採点窓net>−$18∩新規件数/日5.39以上∩非degenerate∩PARTIAL_TP温存）" -->

## DESIGN_CONTRACT
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": [
    "v17_exit_set",
    "_select_v17_params",
    "v17_band_consensus",
    "V17_ATR_BAND_EDGES",
    "partial_tp_protect_v17",
    "guard_global_v17",
    "boxw_expand_guard_v17",
    "range_ok_v11",
    "short_only_v11"
  ]
}
```
