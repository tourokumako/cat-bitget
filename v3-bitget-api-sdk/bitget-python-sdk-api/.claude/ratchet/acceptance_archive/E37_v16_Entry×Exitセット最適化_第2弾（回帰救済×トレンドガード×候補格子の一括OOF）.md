# acceptance — E37 v16 Entry×Exit セット最適化 第2弾（回帰救済×トレンドガード×候補格子の一括 OOF）

TARGET: scripts/priority_rebuild/e37_range_scalp.py

## LEVER（improvement_plan 2026-07-07 から逐語引き継ぎ）
<!-- LEVER: v15 の場面セル×玉タイプ×purged OOF 選定枠に、E37 グリッド全ツマミ（TIME backstop 長と前倒し・BE_EXIT arm 帯・ladder rung W比格子・TP1/TP2 位置比率・RANGE_BREAK 持続長・場面セル別 新規 size 配分）を候補格子として統合し、学習窓 OOF 合意で一括選定する -->
- 上記 LEVER に、まこさん指摘（2026-07-07・利益最小週 PNG＝急騰中エントリーとレジーム判定不全）を受けた **クラスタ変位ガード／BB 幅拡大ガード（トレンド移行の動的サイン）** を候補格子として加える（improvement_plan 切り口9・probe 実測済み）。

## 網羅マトリクス参照と Exit 状態機械（enforce_combo_matrix）
- 本提案は**網羅マトリクス（entry_exit_matrix）の E37 グリッド #23（v15）の継続セル**＝「#23 の場面セル×OOF 選定枠に、#19（場面 meta＝size 配分・Eb4）・#20（分離指標 box_W/atr の特徴量化・Ef2）・ladder 幾何（X-i9）・TP1/TP2 位置比率（X-a/X-b）・TIME 場面連動（X-f）・トレンド移行ガード（X-g vol expansion／Eb13 BB 由来のコンフルエンス・Exit×Entry 結合部の新軸=クールダウンは ARC29 (A) 案）を候補ツマミとして統合」を実装する（採点後にグリッドへ #26 として追記）。
- **未試行: あり**（#7〜#21 の単独セル群・#14 需給 taker_ls SHORT 対称性・#11 MTF 整合は次弾候補として残る。出口単独セル #7/#8/#13/#18 は v13/v14 実測で入口/セット軸を含む組を優先する整理済み）。選定は未試行セル全体を見渡した上で、v15 で初めて学習窓 gross がプラス転換した #23 系の作り込み継続が最有力＝まこさん確定方針（俯瞰して Entry/Exit セットで最適化を続ける）と一致。
- **Exit＝ポジション状態機械（基本原則③・v15 の分岐を維持し水準を格子化）**:

| ポジション状態（entry 後） | 発火 Exit（v16） | 水準の候補格子 |
|---|---|---|
| 含み益が TP1/TP2 へ伸びる | PARTIAL_TP／TP_FILLED（maker） | TP1 f{0.35,0.5,0.65}・TP2{中央,0.75×dist} |
| 含み益がピークから反転 | MFE_DRAWDOWN_CUT（トレーリング maker） | v15 選定値を維持（格子は現行） |
| 逆走後に建値へ回帰 | BE_EXIT（建値フロア maker） | 逆走 arm{0.25,0.5,0.75,1.0}×W＋時間 arm{30,60,120}分 |
| 逆走が進む（レンジ内の往復想定） | ladder rung add（maker・ガード非発火中のみ） | rung{0.25,0.5}×W・4段 0.012・cap 0.048 不変 |
| クラスタ基準から明らかに上放れ＝トレンド移行 | **TREND_CONT（taker・登録済み再利用）＋新規/add クールダウン** | 変位 k{0.5,0.75,1.0,1.5}×W_base／BB 拡大（BBW>q90∩終値>2σ∩出来高）／OFF |
| レンジ構造の破れ（出来高∩ゾーン外持続） | RANGE_BREAK_EXIT（taker・全 lot） | 持続{12,24}本・建玉基準カウント |
| 本物の逆行が深い | 災害SL SL_FILLED（maker・遠い） | v15 選定値を維持 |
| 時間切れ（TP1 未達の逆走テール） | deadline shrink → TIME_EXIT backstop | backstop{12,24,36,48}本×down_factor{OFF,0.5,0.75}・上限4h |

## ★戦略照合（enforce_strategy_anchor）
- アンカー逐語: **e37=range,short_only,scalp**（adopted_strategies.md STRATEGY_ANCHOR・cat_requirements §1.2.1）
- GATE_IDENT=range_ok_v11（1h タッチ実績 S/R ゾーン ∩ 5分ブレイク離脱＝担当局面レンジの入口制約・不変）
- SIDE_IDENT=short_only_v11（LONG 入口の生成経路なし・不変）
- 頻度役割: scalp＝件数/日を上げる（F 合格基準に明記）・勝ち玉保有は分単位・4h は逆走テール backstop 限定（E36 デイトレとの線引き・まこさん 2026-07-07）。
- ledger 直近 ARC の逐語引用（order=30）: 「E37 v15 Entry×Exitセット最適化 第1弾（逆行側分岐の作り直し＋枝×場面セル別 学習窓選定）」＝採用に至らず（precheck FAIL be 0.24・学習窓 平均 gross は E37 初のプラス転換・新最大出血=TIME 4h 満期 −$1,345・ladder は OOF 不採択）。本 v16 はその直接の続き。

## 深掘り4点
- **① 真因**: TP1 未達の逆行側玉の処理が未完成。学習窓の実測（probe 2026-07-07）＝(i) TIME 満期 1,484 fill −$5,192 のうち **69%（−$3,272 分）は満期前に建値フロアへ回帰していた**（初回タッチ中央値10分）のに、現行 BE_EXIT は3セル限定の arm 条件で 332 fill しか拾えていない (ii) **回帰しない玉 463 fill −$1,919 はトレンド移行玉**＝range_ok_v11 が階段状トレンドの踊り場を毎回レンジと認識し（12/02 実測: 入口時 ADX 36〜75 で通過・box_W 4.39% の巨大ゾーン）、移行を検知して離脱・停止する機構が無い (iii) v15 ladder は rung 幾何が届かず 0 発火（probe: 0.25×W の rung なら 55.8% が到達し、到達後 81% は平均建値の建値フロアへ回帰）。
- **② 期待値分解**: 学習窓 be 1.0 の門まで gross/件 あと +$0.08（×19,057 fill ≈ +$1,500 規模）。内訳の狙い所＝BE 回収（母数 −$3,272）・トレンドガード（変位ガード k=0.5〜1.0×W の静的近似 +$330・BB ガード +$258）・TIME 場面短縮（母数 −$1,919）・ladder 平均建値改善・TP1/TP2 位置（f=0.35〜0.65 で期待 gross 近似 0.158〜0.240%/unit の幅）。配分は OOF が決める（固定しない）。
- **③ root か symptom か**: root（逆行側の処理機構と局面移行検知の欠落そのもの。SL 幅の付け替え＝symptom は v10〜v14 で確認済みの型）。
- **④ ベースアップ（証跡）**: WebSearch/WebFetch 2026-07-07＝Leung-Li（arxiv 1411.5062・SL 水準を上げる[遠くする]と最適 TP は浅くなる＝災害SL 化した v15 で TP1 の浅い側格子を試す理論的裏付け）／LuxAlgo scale-out（部分利確25/25/50＋BE 移動＋トレーリングの標準手順）／LuxAlgo squeeze-then-surge・BBW=(上−下)/中央×100（BB 拡大の機械判定）／Hummingbot Grid Strike（limit_price=水準割れで bot ごと停止＝クラスタ一括ガードの対応物）／arxiv 1707.03498（縮む境界の逐次 deadline・v13 から継続）。KB=range_scalping_kb §5（破れ3判定）・§6.5（add＋部分決済=V9 型）。probe 5本（scratchpad・学習窓 read-only）。

## 方針・狙い（前 iter の何を受けて何を狙うか）
- v15（学習窓 gross 初プラス・be 0.24）の壁＝手数料に対し、**「戻る玉は建値以上で早く回収し（BE 拡張・ladder）、戻らないトレンド移行は動的サインで検知して離脱・停止し（変位/BB ガード・TIME 場面連動）、取り幅の形は場面ごとに最適化する（TP1/TP2 格子）」**を、v15 で作った場面セル×玉タイプ×purged OOF 選定基盤にそのまま載せて一括選定する＝TIME 1本の近視眼にしない（まこさん方針 2026-07-07）。

## やること（実装項目）
1. **--v16-exit-set**（既定 OFF＝v15 恒等・OFF 恒等 md5 を v15_029 系で確認）。
2. **cluster_guard_check_v16（トレンド移行ガード）**: クラスタ（前 position 最終 exit から 12本以内の新規を連結）基準価格＝クラスタ初回 entry。候補格子＝(a) 変位ガード k ∈ {0.5, 0.75, 1.0, 1.5}×W_base (b) BB 拡大サイン（BBW>rolling288 q90 ∩ 終値>2σ上 ∩ 出来高>20期間平均・コンフルエンス） (c) OFF。発火＝保有全 lot を成行離脱（**TREND_CONT・登録済み taker を再利用＝score.py 不変**）＋新規/add をクールダウン {6, 12}本 veto。セル×タイプ別 OOF 選定。
3. **be_time_arm_v16（戻り決済の拡張）**: BE_EXIT の arm 候補を (a) 逆走 arm ∈ {0.25, 0.5, 0.75, 1.0}×W (b) **時間 arm＝TP1 未達のまま {30, 60, 120}分 経過で建値フロア maker 指値を置く** (c) OFF、の格子に拡張（現行3セル限定を全セル×タイプの選定対象に）。TP1/TP2 との食い合い（早すぎる BE が勝ち枝を薄める）は OOF の合計純増∩区間合意が判定。
4. **tmax_scene_v16（TIME の場面連動）**: backstop 長 ∈ {12, 24, 36, 48}本 × 含み損側 down_factor ∈ {OFF, 0.5, 0.75} をセル×タイプ別に（上限4h＝まこさん指定を超えない・deadline shrink は同尺維持）。
5. **ladder rung の幾何差し替え**: 逆走段 rung ∈ {0.25, 0.5}×W（maker 指値 TTL3・最大4段 0.012・合計 0.048 不変）・**ガード非発火中のみ**積む（急騰の階段で不利な上値に積まない＝improvement_plan (d)）。
6. **TP1/TP2 位置比率格子**: TP1 f ∈ {0.35, 0.5, 0.65}×（entry−中央）・TP2 ∈ {中央, entry−0.75×(entry−中央)}。tp_floor_check_v15 の物理条件（TP1 幅 ≥ SCALP_FLOOR 0.08%）は全候補に維持。
7. **RANGE_BREAK の計数是正**: 破れカウンタを建玉基準（entry 時ゾーンからの離脱持続）に是正・持続長 ∈ {12, 24}本（短縮側は probe3 実測＝勝ち玉側の差引が負・回帰率35〜55%のため格子に入れない。この判断は probe の方向付けであり、格子 {12,24} の選定自体は学習窓 OOF）。
8. **場面セル別 新規 size 配分**: 初回 lot ∈ {0.006, 0.012}×セル（H9: 最小 0.0001 BTC/5 USDT 充足・cap 0.048 不変＝負けセルに薄く・勝ちセルは現行）。
9. **_select_v16_params**: v15 選定基盤（場面セル LightGBM 1本の木[stoch_k/ATR%/box_W]×玉タイプ×purged 3分割 OOF 合意＝合計純増∩2/3区間改善）の候補表を上記格子に拡張・木の num_leaves ∈ {4, 6}。選定表全行を出力。incumbent＝v15 選定値。
10. **--v16-guard-check（番人メタ確認）**: 枝別極端値（ガード k 極小→TREND_CONT 支配／時間 arm 極小→BE_EXIT 支配／backstop 12本→TIME 支配／rung 極浅→add 支配 等）で exit_reason 分布が枝支配になるか（配線証明・採点しない・--smoke 併用）。
11. sidecar（_param_sections に v16 節）＋ 実行は --tag v16 連番（require_tag_for_experiment）。

## ★疑似シミュ由来の固定値ゼロ
- (a) 全候補格子の値は **a-priori（レンジ幾何の W 比・時間の等分・業界標準比率[scale-out 1/4〜2/3・BBW q90・出来高20期間]）** であり、probe が出した特定数値（69%・+$331・55.8% 等）を閾値・水準として焼き込まない。
- (b) probe（5本・scratchpad）は方向付け（どのツマミを格子に載せるか・載せないか）にのみ使用。probe の数値は選定・採否の根拠にしない。
- (c) 採否は **実エンジン両窓 score.py の数字のみ**（学習窓 OOF 選定 → 対 incumbent 純増 → precheck be≥1.0 → 両窓）。probe は再エントリー動学なしの静的近似（L-330）と明記。

## D. 審判整合
- **新 exit_reason なし**: ガード離脱は登録済み TREND_CONT（taker）を再利用（score.py L48 で 2026-07-02 登録済み・意味＝トレンド化した継続玉の成行カット＝本ガードと同義）。BE_EXIT／MFE_DRAWDOWN_CUT／PARTIAL_TP／TP_FILLED（maker）・TIME_EXIT／RANGE_BREAK_EXIT（taker）も登録済み再利用。**score.py／eval_engine は触らない（H13・judge 不変を diff で確認）**。
- コスト種別: ガード/TIME/破れ＝成行 taker+slip・TP/BE/dd/rung＝指値 maker（H5 の約定モデルどおり）。
- 出力は共通の書き出し処理（_output_and_report/ratchet_io）・sidecar params_sidecar を更新。

## E. §4.6 ハード制約照合
- **H1**: 同時最大 4 lot×0.012＝0.048 BTC 不変（size 格子は減らす側のみ・_verify_cap＋score.assert_hard_constraints 実測）。
- **H2**: 全判定は確定バーの値のみ（BBW/出来高 SMA は shift(1)・ガード/arm/rung は当該バー確定値→次バー執行・shift(- と center=True の自己 grep 継続・OOF は purged 3分割）。
- **H5**: entry 指値 maker TTL3・TP/BE/dd/rung=maker・TIME/ガード/破れ=taker+slip（eval_engine 定数）。
- **H6**: 全水準は W 比・%・本数の無次元（USD 絶対値なし）。
- **H8**: periods.py import（TRAIN_END 前で fit/選定・採点窓不参照・封印不参照）。
- **H13**: judge 不変（score.py/eval_engine に変更なし）。
- **H15**: 非該当寄り＝方向スコアは作らない（方向は入口で当てない前提を維持）。atr_pct は場面セルの特徴と size 配分に使用＝「ボラ系はサイジング/フィルタへ役割を移す」の整合側。
- **H16**: 1変更＝「v16 候補格子の統合＋OOF 一括選定」1枠（v15 と同型の1レバー粒度）。過去の型の不再演＝予測で切る枝は入れない（L-309）・採点窓で選ばない（L-267）・probe 値を焼かない（上記）・出口単独に閉じない（L-330＝入口 veto/size/ladder を同枠に含む）。

## スキャル一級基準（enforce_e37_pdca ⑦⑨⑫）
- **⑦ 手数料を超える TP 幅**: TP1 幅 ≥ SCALP_FLOOR 0.08%（maker 往復 0.028% の約2.9倍）を全候補で物理維持（tp_floor_check_v15）。
- **⑨ 短保有（分単位）**: 勝ち玉の保有は分単位を維持（v15 実績 TP1 平均73分）。4h は TP1 未達の逆走テール backstop 限定（保有4時間のデイトレ化はしない・tmax 格子は短縮方向のみ）。
- **⑫ 5分足設定**: RSI9（入口）・1h ゾーン×5分執行（MTF）を不変で維持。

## F. 受け入れ判定（採点前ゲート→公式判定）
1. 自己検査: --v16-exit-set OFF 恒等（md5 が v15_029 の CSV と一致・2系統）・py_compile・DESIGN_CONTRACT 照合・--v16-guard-check 番人（枝別極端値で発火支配＝わざと壊して落ちるかのメタ確認）・cap 0.048 実測・leak 自己 grep。
2. _select_v16_params: 学習窓のみで OOF 選定（選定表全行提示）→ **対 incumbent（v15 選定値）で学習窓 純増**が無ければ停止（採点温存・扱いはまこさん判断）。
3. precheck: 学習窓 be ≥ 1.0（FAIL なら採点温存・採用に至らずと記録し ratchet 維持）。
4. 両窓 score.py: **採点窓 net > 地面 v8_013（−$18）∩ 新規件数/日が v15 の 4.96 から増える（件数/日を上げる＝scalp 役割の合格基準・ladder 約定と size 配分は増側・ガード veto で減った分を上回ること）∩ 非degenerate ∩ PARTIAL_TP の黒字本体を壊さない ∩ 勝ち玉保有 分単位維持**。割れたら採用に至らずと記録（地面 ratchet 維持・次の作り込み案へ）。
5. 報告: 勝率 >70% が出たら H12 切り分け（小利 maker 構造か leak か）をしてから。N5 bootstrap が 0 を跨ぐ限り「黒字」と言わない。

## DESIGN_CONTRACT
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": [
    "range_ok_v11",
    "short_only_v11",
    "--v16-exit-set",
    "cluster_guard_check_v16",
    "be_time_arm_v16",
    "tmax_scene_v16",
    "_select_v16_params",
    "--v16-guard-check"
  ]
}
```

## ARC マーカー
<!-- ARC order=31 iter="E37 v16 Entry×Exitセット最適化 第2弾（回帰救済×トレンドガード×候補格子の一括OOF）" 前提="E37未採用・v15=precheck FAIL be0.24（学習窓平均gross初プラス転換・新最大出血=TIME 4h満期・ladder 0発火）・まこさん指摘=急騰中エントリーとレジーム判定不全（12/02 実測: ADX36〜75でrange_ok通過・階段型売り直し13玉）・probe5本（TIME玉69%が満期前建値回帰[中央値10分]/変位ガードk0.5〜1.0×W静的+$330/BB拡大+$258/破れ短縮は勝ち玉側差引負/rung0.25W到達56%・BE回帰81%）" 採否="未（実装→学習窓OOF→precheck→両窓score.py）" base_csv="trades_e37_range_scalp_v15_029_score.csv" score_csv="" train_csv="" 狙い="v15の壁＝手数料（gross/件あと+$0.08）に対し、戻る玉は建値以上で早く回収（BE arm帯+時間arm・ladder rung W比）・戻らないトレンド移行は動的サイン（クラスタ変位k×W/BB幅拡大）で検知して離脱と新規停止（TREND_CONT再利用・クールダウン）・TIMEは場面連動で短縮・TP1/TP2位置と新規sizeを場面別に、v15の場面セル×玉タイプ×purged OOF選定基盤へ候補格子として一括統合し、スキャル役割（件数/日を上げる・勝ち玉分単位・4hはbackstop限定）を保ったまま学習窓be≥1.0の門を通す" 内容="--v16-exit-set（既定OFF=v15恒等md5）＝①cluster_guard_check_v16（クラスタ変位k∈{0.5,0.75,1.0,1.5}×W_base／BB拡大[BBW>q90∩終値>2σ∩出来高>20avg]／OFF・発火で全lot TREND_CONT taker＋新規/addクールダウン{6,12}本）②be_time_arm_v16（逆走arm{0.25,0.5,0.75,1.0}×W＋時間arm{30,60,120}分＋OFF）③tmax_scene_v16（backstop{12,24,36,48}本×down_factor{OFF,0.5,0.75}）④ladder rung{0.25,0.5}×W（ガード非発火中のみ・4段0.012・cap0.048不変）⑤TP1 f{0.35,0.5,0.65}×TP2{中央,0.75×dist}（床0.08%維持）⑥RANGE_BREAK建玉基準カウント・持続{12,24}本⑦新規size{0.006,0.012}×セル⑧_select_v16_params（場面セル木[stoch_k/ATR%/box_W]num_leaves{4,6}×玉タイプ×purged 3分割OOF合意）・新exit_reasonなし（TREND_CONT再利用＝score.py不変H13）・入口/ゾーン/勝ち枝は不変" 方法="自己検査（OFF恒等md5=v15_029一致・py_compile・DESIGN_CONTRACT 8識別子・--v16-guard-check番人[枝別極端値で発火支配]・cap実測・leak自己grep）→_select_v16_paramsで学習窓のみOOF選定（選定表全行・対incumbent v15選定値で純増なければ停止）→precheck be≥1.0（FAILなら採点温存）→両窓score.py（採点窓net>−$18∩新規件数/日>4.96∩非degenerate∩PARTIAL_TP温存∩勝ち玉分単位）・probe値は焼かない（a-priori W比/時間等分/業界比率格子）" -->
