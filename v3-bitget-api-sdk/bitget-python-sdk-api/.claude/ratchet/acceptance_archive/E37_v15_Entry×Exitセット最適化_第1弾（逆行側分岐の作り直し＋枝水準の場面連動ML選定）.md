# acceptance.md — E37 v15: Entry×Exit セット最適化 第1弾＝逆行側分岐の作り直し＋枝水準の場面連動 ML 選定（2026-07-07）

TARGET: scripts/priority_rebuild/e37_range_scalp.py
TARGET: scripts/priority_rebuild/score.py
（score.py の変更は RANGE_BREAK_EXIT の taker 登録1語のみ＋既知答えテスト再pass＝D 審判整合。net 計算式には触れない・H13。）

## LEVER（improvement_plan から逐語引き継ぎ・enforce_pdca_chain 接続②）
Exit状態機械の枝パラメータ（玉タイプ×場面別の発火水準）を学習窓MLで最適化
- 本手＝v14 で選定が OFF に収束した原因（候補が手置き2〜3点・場面非連動）を直す: ①負けの本体だった逆行側の分岐（浅SL 即切り）を「add ラダー＋戻り決済＋構造破れ判定＋4時間 backstop」に作り替え ②全枝の発火水準を場面特徴×玉タイプの学習窓 ML（purged CV・OOF・木＝コンフルエンス）で選定。既定 OFF＝v14 恒等。
- まこさん決定（2026-07-07）: 抱え上限4時間 GO／add を増やす（同予算分割から）／E37=スキャル・E36=デイトレの線引きを設計の第一制約に。

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["range_ok_v11", "short_only_v11", "v15_exit_set", "V15_LADDER", "range_break_check_v15", "_fit_v15_branch_policy", "_select_v15_params"]
}
```

## ★戦略照合（enforce_strategy_anchor）
STRATEGY_ANCHOR: e37=range,short_only,scalp
- 局面（range）: 入口の range_ok_v11（1h タッチ実績 S/R ゾーン ∩ 5分ブレイク離脱）は不変。GATE_IDENT=range_ok_v11。破れ判定枝は「レンジでなくなったら畳んで E32b に譲る」＝§1.2.1「E32b を邪魔しない」を強化する側。
- 方向（short_only）: LONG 入口の生成経路なし・不変。SIDE_IDENT=short_only_v11。本手は出口と玉の構成の話＝方向の賭けを追加しない。
- 頻度（scalp）: **件数/日を上げる（高頻度＝役割）**。add ラダー（0.012×4）＋部分決済で position 内の約定数を増やす＝決済 fills/日 3.40 から上げるのを F の合格基準に含む。勝ち玉の保有は分単位を維持（下記⑨）。
- ledger 直近 ARC 逐語引用: ARC order=29 iter=「E37 v14 Exit ポジション状態機械（E37レンジ幾何ネイティブ・基本maker）」（採用に至らず＝学習窓の逐次選定がほぼ全枝 不使用を採択・発火15回・寄与+$7・採点窓 CSV は v13 と同一、が直前の確定）。

## 変更内容（1レバー＝逆行側分岐の作り直し＋枝水準の場面連動 ML 選定・入口/ゾーン/勝ち枝は不変）
新フラグ --v15-exit-set（既定 OFF＝v14 恒等 md5）。ON のとき:

**(1) add ラダー（同予算分割・グリッドの精神を Bitget 仕様で）**
- UNIT_V15=0.012 BTC・最大4段（**position 合計 0.048 BTC 不変＝現行 0.024×2 と同額・H1 の E37 取り分を増やさない**・0.012 は最小注文 0.0001 BTC/5 USDT を満たす・H9）。
- トリガ＝現行の入口条件 完全再発火（上限ゾーン再テスト）に加え、**逆走進捗の段**（負の進捗率＝レンジ幾何・無次元・H6）に maker 指値（TTL 3本・同一 side の pending 中は追加発注しない＝exchange_spec 指値仕様準拠）。段の位置・使用可否は学習窓選定（後述(5)）。
- 平均建値（merge・openPriceAvg）が寄る＝TP1/TP2/戻り決済の発火点が近づく＝戻りの決済を早く・多くする（exchange_spec ★ポジションの持ち方 (1)(2) 準拠）。

**(2) 戻り決済枝（今回の最大回収源）**
- 逆走後、価格が平均建値〜手数料床帯（avg×(1−0.08%) 級）へ回帰したら maker 決済＝**BE_EXIT（登録済み・maker）を「含み損からの建値回帰」でも発火する形に拡張**。全量/半量の別・発火帯の水準は場面×玉タイプの学習対象。
- 根拠データ: SL で切られた玉のうち建値回帰は 60分以内 63%・4時間以内 78%（回帰の中央値10分・両窓同率）＝現行の浅SLはレンジの往復を最悪点で確定していた。

**(3) SL 構成の作り直し（即切りから「構造で畳む」へ）**
- 現行の浅SL（ゾーン外0.05%）を置換: (a) **構造破れ枝 RANGE_BREAK_EXIT**（新 exit_reason・taker 成行）＝出来高が20期間平均超 ∩ 5分終値がゾーン外 ∩ 上位足（1h）終値もゾーン外、の3条件 AND（range_scalping_kb §5 の a-priori・関数 range_break_check_v15）で即畳み。(b) **災害SL（SL_FILLED 維持・遠い水準）**＝ゾーン上端からの距離候補（レンジ幾何比の a-priori 入れ子）から学習窓選定。
- 4時間戻らない玉（2割・保有時最大逆行の上位1割は4%超）はここで塞ぐ。

**(4) 時間の枝（4時間 backstop・まこさん指定）**
- T_MAX を 48本＝4時間へ（60分から変更・まこさん GO 2026-07-07）。**含み損玉は down_factor で前倒し taker**（V9 TIME_EXIT_DOWN 型・係数は学習窓選定）・v13 deadline shrink（縮む maker TP）は 4時間尺に再スケールして維持＝満期成行を減らし maker で取り切る。
- 勝ち枝（TP1 部分利確・TP2・PARTIAL_TP・MFE_DRAWDOWN_CUT）は温存（採点窓 +$2,048 の源泉・⑨巻き込み対象＝F で温存確認）。

**(5) 枝水準の場面連動 ML 選定（v14 の浅さを直す本体）**
- 特徴: stoch_k(9,3)・RSI9・ATR%・box_W_pct・進捗率・経過分・玉タイプ（add 有無×TP1 済み）・1h ゾーン文脈（MTF＝上位足）。
- 方法: 学習窓のみで LightGBM（purged K-fold＋embargo・OOF 選定）に枝の発火水準/使用可否を学習させる（単一閾値の手置きメニューにしない＝コンフルエンス・複数特徴の AND を木に学ばせる・L-267）。教師は per-lot の実出口ベース（エンジン同一執行・MFE ピークを教師にしない）。
- 目的関数: lot net（負けの回収 − 勝ち玉の犠牲）＋制約（決済 fills/日 ≥ 3.40・勝ち玉保有中央値 分単位）。選定表は全行ログ提示。

**入口 meta-labeling ゲートは本レバーに含めない**＝次のイテレーションで独立に検証する（1ターン1変更・H16）。

## E37 スキャル物理条件（⑦⑨⑫）
- ⑦ 手数料の壁: TP1 幅 ≥0.08%（maker 往復 0.028% の約2.9倍）を維持。戻り決済も手数料床を割らない水準に限定（損ゼロ級 maker）。taker 出口（TIME_EXIT）は shrink/戻り決済で縮減方向＝手数料を超える幅だけ取る。
- ⑨ スキャル定義＝短保有: **勝ち玉の保有は分単位を維持**（現行 TP1 中央29分・全体中央37分級）。4時間は逆走テールの backstop 限定＝「1ポジを伸ばして大きく取る」設計にしない（それは E36=デイトレの領分・ROLE_CHECK 線引き）。保有の分布（勝ち玉中央値・全体）を F で監視。
- ⑫ 5分足スキャル設定: RSI9・stoch(9,3)・MTF＝1h ゾーン（上位足確認）＝v11 計器を維持。

## 深掘り4点
- **① 真因**: (i) v14 の枝水準候補が手置き2〜3点で場面非連動＝学習窓選定が不使用に収束（発火15回・+$7） (ii) 浅SL がレンジの往復を最悪点で確定（SL損の74%＝−$1,425 が4時間以内に建値回帰する玉・両窓） (iii) 出血が TP1 未達玉に全額集中（採点窓 −$2,546 vs TP1済み −$44）＝序盤の含み益確定と逆走の抱え方に分岐が無い。
- **② 期待値分解**: 必要勝率不足 5.4pt＝平均負け $6.83 から $5.50 への縮小が等価解。対象＝SL戻り玉 −$1,425（採点窓）＋B ピーク反転の取り逃し $1,104。勝ち側（平均勝ち $5.68）は温存し、add ラダーで黒字帯（MFE 5-15 +$847）の厚みを足す。
- **③ root か symptom か**: root=Y。損の名前（SL/TIME）でなく「Exit の構成ロジック＝状態分岐と水準最適化の不在」に当てる。損玉の症状別パッチ（SL 幅だけ動かす等）ではない。
- **④ ベースアップ**: range_scalping_kb §4/§5/§6.5（SL=構造基準・破れ3判定・add＋部分決済＝グリッドの精神）・entry_exit_matrix 基本原則①②③＋V9 分岐表・Hudson & Thames meta-labeling/Triple Barrier（教師は実出口・primary は雑でよい）・arxiv 2604.02035/2105.08877（exit=optimal stopping・強化学習は今回採らず教師ありで枝別に）・QuantifiedStrategies position sizing in mean reversion（ラダーの線形分割）・WebSearch/WebFetch 2026-07-07 実施。

## ★疑似シミュ由来の固定値ゼロ
- (a) 4段=予算幾何（0.048÷0.012）・段の位置=学習窓選定。4時間=まこさん指定。破れ判定の3条件=KB §5 の a-priori（数値は20期間平均等の既存定数）。災害SL・down_factor・戻り決済帯=レンジ幾何の a-priori 入れ子候補から学習窓選定。
- (b) probe の数値（戻り74%・63%・回帰10分・逆走深さ分位 等）は**設計の固定値に焼かない**＝分析の構造根拠のみ。経路 probe は lot 独立＝再エントリー/スロット動学なし（L-330）＝採否根拠にしない。
- (c) 採否は実エンジン両窓 score.py の数字だけで決める。

## C 変更の単位（H16）
- 1レバー＝「逆行側分岐の作り直し＋枝水準の場面連動 ML 選定」一式（v14 と同じ「一式で1レバー」の型・まこさん承認済みの方向）。入口 meta ゲートは次のイテレーション。
- 既定 OFF=v14 恒等（トグル1つ・恒等 md5 で自己検査）。
- 過去に採用に至らなかった型との差分: 切る系（L-309・予測で切る）と逆方向＝切りを減らして戻りで出る。STRUCT_SL（無条件の深い構造ストップ追加）とは「破れ判定 AND 3条件＋戻り決済とセット」の点で別物。E36 hold-mom-exit（判別器で早期手仕舞い）とも逆（抱える側）。

## D 審判整合（acceptance_checklist）
- 新 exit_reason: **RANGE_BREAK_EXIT（taker 成行）を score.py TAKER_EXIT_REASONS に登録＋既知答えテスト再pass**（H13・登録1語のみ・net 計算式不変）。
- 再利用（登録済み）: BE_EXIT（maker）・SL_FILLED（maker）・TIME_EXIT（taker）・PARTIAL_TP/TP_FILLED（maker）・MFE_DRAWDOWN_CUT（maker）。
- 出力: 共通書き出し _output_and_report（ratchet_io）・--tag v15 連番・params_sidecar に v15 の実使用値（ラダー段・選定水準・T_MAX・破れ判定）を記録。
- 命名: 実験は e37_range_scalp.py --tag v15（pdca 検知に乗る）。

## E §4.6 ハード制約 照合
- H1: position 合計 0.048 不変（0.012×4）・全戦略共有 0.12 の取り分を増やさない。score.assert_hard_constraints が時系列で実測。
- H2: 特徴は t 時点まで（トリガ判定は前バーまでのピーク＝v14 と同じ H2 設計）・shift(-)/center=True を書く場合は H2OK 因果宣言（require_leak_annotation）・学習は学習窓のみ・fit 境界 assert。
- H5: 約定モデル準拠＝ラダー/戻り決済/TP は指値 maker・破れ/TIME down_factor は成行 taker+slip。
- H6: 水準は進捗率・%・レンジ幾何比（USD 絶対値なし）。
- H8: periods.py 正本（学習 fit・採点評価のみ・封印不参照）。
- H9: 0.012 BTC ≥ 最小 0.0001・約5 USDT 超 ✓。
- H13: judge 不変（登録1語＋既知答え再pass のみ）。
- H15: 方向スコアに揺れ幅を使わない（本手は方向を予測しない）。ATR% は Exit 水準/場面特徴への使用（軸1の許容用途＝TP/SL・フィルタ側）＝学習後 feature importance で揺れ幅の支配がないことを確認して提示。
- H16: 1変更（上記 C）・過去に採用に至らなかった型の再演でないこと確認済み（上記 C）。

## F 受け入れ判定（採点前ゲート・すべて実エンジン）
1. 自己検査: --v15-exit-set OFF 恒等 md5（v14_026 と一致・3本）／py_compile／DESIGN_CONTRACT 7識別子／cap 0.048 assert／leak grep／既知答えテスト再pass（RANGE_BREAK_EXIT 登録後 15/15）。
2. 番人メタ確認（わざと壊して落ちるか）: 枝別極端値で各枝が発火支配になるか・破れ判定を常時 true にして RANGE_BREAK_EXIT が全数出るか・ラダー段0で v14 相当に戻るか。
3. 学習窓: _fit_v15_branch_policy の OOF 選定→選定表全行提示→**学習窓 net 純増**を確認（純増なしなら停止・採点温存）。
4. precheck（breakeven ≥1.0 ゲート）→ 両窓 score.py:
   - 採点窓 net > 地面 v8_013（−$18）
   - **決済 fills/日 > 3.40（件数/日を上げる＝scalp 役割・add 約定＋部分決済で position 内から増やす）**
   - PARTIAL_TP +$1,413／TP_FILLED +$635 を大きく減らさない（⑨巻き込み・勝ち枝温存）
   - 勝ち玉の保有中央値が分単位（40分級以内）・非degenerate
   - RANGE_BREAK_EXIT の発火数と最大逆行の分布を提示（テール監視）
5. 割れたら「採用に至らず（地面 ratchet 維持）＋次の作り込み案」を記録。

<!-- ARC order=30 iter="E37 v15 Entry×Exitセット最適化 第1弾（逆行側分岐の作り直し＋枝水準の場面連動ML選定）" 前提="E37未採用・v14=学習窓選定がほぼ全枝不使用に収束（候補手置き2〜3点・場面非連動）・path probe両窓でSL損の74%が4時間以内に建値回帰と実測・まこさん決定=抱え上限4時間GO/add増（同予算分割）/E37=スキャル・E36=デイトレの線引き維持" 採否="未（実装→学習窓ML選定→precheck→両窓score.py）" base_csv="trades_e37_range_scalp_v14_026_score.csv" score_csv="" train_csv="" 狙い="v14で機械がOFFに収束した原因＝枝候補の浅さ（手置き・場面非連動）と、負けの本体＝逆行側（浅SLがレンジの往復を最悪点で確定・TP1未達玉に出血集中）を、add ラダー（同予算0.012×4）＋戻り決済（建値〜手数料床maker）＋構造破れ判定（KB§5）＋4時間backstop（down_factor）＋枝水準の場面×玉タイプ別 学習窓ML選定（purged CV・OOF・コンフルエンス）で一式として直し、スキャル役割（件数/日を上げる・勝ち玉保有は分単位）を保ったままE37の地面を黒字側へ動かす" 内容="--v15-exit-set（既定OFF=v14恒等md5）＝①add ラダー UNIT 0.012×最大4段（合計0.048不変・上限ゾーン再テスト∪逆走進捗の段・maker指値TTL3）②戻り決済枝（BE_EXIT拡張=含み損からの建値回帰でmaker決済・帯は学習）③浅SLを構造破れ枝RANGE_BREAK_EXIT（新taker登録・出来高∩ゾーン外終値∩1h確認のAND）＋遠い災害SL（学習窓選定）に置換④T_MAX 4時間・down_factor・shrink再スケール⑤枝水準を場面特徴（stoch_k/RSI9/ATR%/box_W/進捗率/経過分/玉タイプ/1h文脈）のLightGBM（学習窓のみ・purged CV・OOF）で選定・入口/ゾーン/勝ち枝/capは不変" 方法="自己検査（OFF恒等md5・DESIGN_CONTRACT 7識別子・番人メタ確認・cap・leak grep・既知答え再pass）→学習窓OOF選定（選定表全行）→学習窓純増→precheck→両窓score.py（採点窓net>−$18∩決済fills/日>3.40∩PARTIAL_TP/TP温存∩勝ち玉保有分単位∩非degenerate・テール=RANGE_BREAK_EXIT発火と最大逆行提示）・割れたら採用に至らずと記録（ratchet）" -->
