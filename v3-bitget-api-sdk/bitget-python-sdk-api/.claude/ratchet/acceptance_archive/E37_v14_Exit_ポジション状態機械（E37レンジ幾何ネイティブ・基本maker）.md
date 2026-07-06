# acceptance.md — E37 v14: Exit ポジション状態機械（E37 レンジ幾何ネイティブ・基本 maker）（2026-07-06 改2＝計画承認反映）

TARGET: scripts/priority_rebuild/e37_range_scalp.py
TARGET: scripts/priority_rebuild/score.py
（score.py の変更は MFE_DRAWDOWN_CUT の maker 登録1語のみ＋既知答えテスト再pass＝D 審判整合。net 計算式には触れない。）

## LEVER（improvement_plan から逐語引き継ぎ・enforce_pdca_chain 接続②）
E37 の Exit を固定TP+固定SL+固定TIME からポジション状態機械（entry後の状態→発火Exit分岐・V9 _check_exits_replay 型）へ
- 本手＝状態機械一式を1レバーで実装。**V9 は骨格（状態→枝・優先順位つき並行監視・玉の型別条件）の参考のみ＝USD ゲート・Priority別条件は移植しない**。水準は E37 のレンジ幾何（進捗率）で定義（まこさん指示 2026-07-06）。既定 OFF=v13 恒等。

DESIGN_CONTRACT:
```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp.py",
  "self_check_calls": ["range_ok_v11", "short_only_v11", "v14_exit_machine", "V14_BRANCH_PARAMS", "_select_v14_params"]
}
```

## ★戦略照合（enforce_strategy_anchor）
STRATEGY_ANCHOR: e37=range,short_only,scalp
- 局面（range）: 入口は range_ok_v11（1h タッチ実績 S/R ゾーン∩5分ブレイク離脱）不変。GATE_IDENT=range_ok_v11
- 方向（short_only）: LONG 入口の生成経路なし・不変。SIDE_IDENT=short_only_v11
- 頻度（scalp）: 件数/日を上げる（高頻度＝役割）。状態機械は決着を早めスロット解放が早まる＝エントリー機会は増える方向（F の基準に含む）。
- ledger 直近 ARC 逐語引用: ARC order=28 iter=「E37 v13 TIME_EXIT の maker化（deadline shrink）」（採用に至らず・出口の執行コストは締めたが SL 方向ミス −$1905 が全体支配で黒字化せず、が直前の確定）。

## 変更内容（1レバー＝Exit 状態機械一式・入口/ゾーン/add本数/cap は一切不変・執行は基本 maker）
新フラグ --v14-exit-machine（既定 OFF=v13 恒等・--v13-time-maker の上に載る前提を assert）。ON のとき、SHORT の各 lot を毎バー（確定バーのみ・トリガ判定は**前バーまでの含み益ピーク lot["peak_prev"]**＝同一バー楽観の排除）監視し、優先順位つき状態分岐で決済する（関数 v14_exit_machine・候補カタログ V14_BRANCH_PARAMS・学習窓選定 _select_v14_params）。

**E37 ネイティブの尺度＝進捗率** prog = (avg − 価格) ÷ (avg − tp2)（0=建値・1=TP2 到達・無次元＝レンジごとに自動スケール・USD 固定ゲートなし・H6 適合。分母≤0 は防御スキップ）。

| 優先 | entry 後の状態（コンフルエンス検知） | 発火 Exit | 執行 |
|---|---|---|---|
| 1 | レンジ破れ・逆行拡大（ゾーン外） | SL（既存・兼務） | trigger+limit maker（既存・不変） |
| 2 | 下降継続（中央へ） | TP1 半分（PARTIAL_TP）→TP2（既存） | maker（既存・不変） |
| 3 | ピーク反転（peak_prog ≥ p_arm 到達後、ピークから r 割戻し） | MFE_DRAWDOWN_CUT（新規登録）＝ピーク基準のトレーリングレベル（**下限＝建値フロア**）に buy trigger+limit | maker |
| 4 | 利益消失（peak_prog ≥ be_arm 到達後、建値へ回帰） | **BE_EXIT（登録済み maker を再利用）**＝建値フロア entry×(1−SCALP_FLOOR) に buy trigger+limit | maker |
| 5 | 指標反転（保有中 stoch(9,3) ゴールデンクロス ∩ 含み益>0 ∩ peak_prog ≥ s_arm） | STOCH_REVERSE_EXIT（登録済み taker を再利用・V9 P23 実績の E37 版） | taker（成行・OFF 候補つき＝要否は学習窓） |
| 6 | 失速（保有 n 本経過しても peak_prog < g） | deadline shrink の前倒し（既存 shrink の残り時間を T_eff に短縮・reason TP_FILLED のまま） | maker（既存機構の状態依存化） |
| 7 | 時間切れ backstop | TIME_EXIT（既存）・**長さ T_MAX は候補 {6,9,12}バー（30/45/60分）から学習窓選定**（60分固定は未検証 a-priori だったため候補に降格） | taker（最後の砦のみ） |

- **パラメータは玉の4タイプ別**（add数[1本目/追加] × tp1_done[半分利確 前/後]）: V14_BRANCH_PARAMS のキー＝（枝×タイプ）。候補（a-priori・無次元・§5 パラメータ）: 枝3 p_arm∈{0.5, 0.75}×r∈{1/3, 1/2}＋OFF ／ 枝4 be_arm∈{0.25, 0.5}＋OFF ／ 枝5' 指標反転 s_arm∈{0.25, 0.5}＋OFF ／ 枝6 (n,g,T_eff)∈{(4,0.25,8),(6,0.5,8)}＋OFF ／ 枝7 T_MAX∈{6,9,12}。**選定は学習窓のみ**（_select_v14_params＝全枝 OFF 基準→枝ごと×タイプごとの逐次 greedy・学習窓 net 最大・同点は OFF 優先・採点窓不参照・L-267）。OFF も選定値。候補メニュー定数は本 acceptance 承認をもって fixed-value-approved（学習窓選定＝採点窓スイープではない）。候補を最小限に絞るのは Lopez de Prado OTR（バックテスト校正の閾値は過剰適合源・arxiv 1408.1159）への防御。
- 手で1点に置く閾値はゼロ。固定は SCALP_FLOOR 0.08%（maker 往復 0.028% を覆う損益分岐の物理）のみ。add 本数（V11_MAX_ADDS=2）は Step 4（規模拡大）の領分＝今回は不変。
- 同一バー競合: SL 最優先（既存・悲観側）。枝3 レベルは min(トレーリング, 建値フロア) にクランプ＝枝3→4 の順が価格到達順と一致。TP2 と枝3 の両ヒットは既存順（TP 先）を維持し件数を診断ログに計上。
- 経路再現の裏取り（正直な執行仮定・疑似シミュ＝焼かない）: 機械（トレーリング＋建値）で学習窓 −$3,471→−$1,013（+$2,458）・採点窓 −$500→−$241（+$259）＝両窓プラス方向。⑨勝ち玉巻き込み＜負け回収。残る負けは含み益が乗らない D 状態（入口の領分）＝この iter では触らない。
- ML 最適化（基本原則②）: 今回は骨格＋学習窓候補選定まで＝素ルール段。**次段でこの機械のパラメータ・分岐発火を ML（メタ分類器・木）に渡すことを明記**。

## 深掘り4点
- **① 真因**: E37 の Exit は固定TP+固定SL+固定TIME のみで、ポジション状態による分岐が無い（網羅マトリクス（entry_exit_matrix）基本原則③）。lot 状態分類で最大の負け状態は B ピーク反転（含み益2×fee 以上が乗ってから消えた・採点窓 191 lot −$1,269・学習窓 2666 lot −$9,697）＝「消える前に確定・利益を守る」枝の欠如。壁A（薄利取り逃し）と壁B（逆行放置）は同じ欠如の両面。
- **② 期待値分解**: 負け側＝平均負け $6.83（N7）を枝3/4 で損ゼロ級〜小勝ちに置き換え・勝ち側＝MFE 捕捉率 0.72 の取り逃しを枝3/5 の確定で回収。必要勝率不足 5.4pt を両側から詰める。
- **③ root か symptom か**: root（Y）。固定点の調整でなく、Exit の構造（状態機械）を E37 の幾何に合わせて入れる。
- **④ ベースアップ**: (a) **トレーリングストップ＋固定利確指値の「併用」が最適という定理**（Leung & Zhang 2017・arxiv 1701.03960）＝枝3（トレーリング）と TP2（固定利確）を並走させる本設計の直接の裏付け (b) 状態依存の entry/exit 閾値は有限状態機械として定式化される標準形（arxiv cond-mat/0012419） (c) 閾値のバックテスト校正は過剰適合源＝候補を絞り理論アンカーで置く（Lopez de Prado OTR 1408.1159・Hudson&Thames O-U 最適閾値＝取引コストが高いほど閾値は広がる） (d) 平均回帰に深い損切りは逆効果・出口領域は stop より上（arxiv 1411.5062）。＋V9 実装 replay_csv.py _check_exits_replay 180-334行を全行読了（骨格＝状態×優先順位×玉の型別条件・カット系 taker は V9 のデイトレ規模ゆえ許容＝E37 スキャルは maker 必須と判断）＋KB range_scalping_kb §4/§6。WebSearch 3本/WebFetch 2本（2026-07-06・学術＋SSR系クオンツの2種別）。

## ★疑似シミュ由来の固定値ゼロ
- (a) 全パラメータは経路再現 probe の値を**焼かない**＝実エンジンの学習窓選定（候補メニュー＋OFF）。進捗率の定義・建値フロア・SCALP_FLOOR は既存定数と幾何（a-priori・新固定値なし）。
- (b) probe の数値（+$2,458／+$259 等）は方向の裏取りであり、設計の固定値・採否根拠にしない。
- (c) 採否は実エンジン両窓 score.py の数字だけで決める。

## C 変更の単位（H16）
- 変更は 1 レバー＝Exit 状態機械一式（Exit のみ）。入口・レンジ判定・方向・add 本数・サイズ・cap は一切不変。分岐の小出しはしない（Exit は一体で net が決まる・機械は分岐の協調で成立）。
- 既定 OFF=v13 恒等（--v14-exit-machine なしで v13_024 と train/score CSV md5 一致を自己検査・既存行を動かさない/削らない）。
- 過去に採用に至らなかった型の不再演（H16②）: L-309「予測で死ぬ玉を判別して切る」系ではない（全枝が予測モデル不使用＝実現した状態の事実で発火）。新枝は「利益側/損ゼロ級で畳む」が主・単一閾値ピーク反転（第1R で巻き込み超過の形）は入れない（枝3 は armed×レベル×フロア下限の多段）。

## D 審判整合
- **新 exit_reason の新規登録: MFE_DRAWDOWN_CUT の1語のみ**（score.py 44行 MAKER_EXIT_REASONS へ追加＋**test_eval_engine_known_answers.py 再pass**＝H13 正規手順・net 計算式不変）。
- **BE_EXIT＝登録済み maker を再利用**（追加変更なし）。**STOCH_REVERSE_EXIT＝登録済み taker を再利用**（V9 と同義・追加変更なし）。**PROFIT_LOCK は使わない**（V9 の成行 taker 定義と同名衝突＝archive の V9 系 CSV 再採点の正しさを守る）。
- e37 側の maker ミラー _MAKER_EXIT（score.py と一致コメント付き）にも MFE_DRAWDOWN_CUT／BE_EXIT を追加（選定が taker コストで歪むのを防ぐ）。
- 本番再現性（H2）: 全枝の発火判定は確定バーの値のみ・トリガ判定は前バーまでのピーク（.shift(- / center=True 不使用）。トレーリング/建値フロアは placePosTpsl（trigger+limit）で事前設置可能＝offline=online 同形。stoch 枝は指標確定後の成行＝本番同形。
- 出力: 共通書き出し（_output_and_report・--tag v14 連番）・params_sidecar に各枝×タイプの選定値・ON/OFF・発火 lot 数・同一バー両ヒット計数を記録。
- strat_base import・periods.py 由来の期間＝現行のまま。

## E §4.6 ハード制約照合
- H1 cap: 合計 0.048 BTC（V11_MAX_ADDS=2）不変・score.assert_hard_constraints 実測 → 適合
- H2 leak: 確定バーのみ・前バーピークでトリガ（同一バー楽観なし）→ 適合
- H3/H4/H5: net 判定・コスト定数・約定モデルは eval_engine 不変 → 適合
- H6 価格非依存: 全水準が進捗率・比率・バー数＝無次元 → 適合
- H7 5m 足不変 → 適合／ H8 periods.py 由来不変 → 適合／ H9 最小注文（半 lot 0.012 BTC ≥0.0001）→ 適合
- H10 サイズ配分不変 → 非該当／ H11 判定は score.py → 適合／ H12 異常値 STOP は score 側強制 → 適合
- H13 judge: MFE_DRAWDOWN_CUT 登録のみ＋既知答えテスト再pass（正規手順）→ 適合
- H14 発注フラグ: バックテストのみ → 非該当
- H15 ボラ逃げ: Entry 不変 → 非該当（Exit のみ）
- H16: 上記 C → 適合

## スキャル一級基準（enforce_e37_pdca）
- ⑦ 手数料を超える TP 幅: TP1 幅 ≥ SCALP_FLOOR 0.08% 不変。枝3/4 の決済レベルは建値フロア以上・枝5 は含み益>0 側＝実質建値を割る確定はしない。
- ⑨ 短保有（分単位）: 状態機械は決着を早める方向・backstop は 30〜60分候補（保有4h 型を繰り返さない）。
- ⑫ 5分足設定: RSI9・1h ゾーン MTF（v11 計器）不変・枝5 は 5分足 stoch(9,3)。
- 件数/日: 入口不変＋スロット早期解放＝件数/日を上げる方向（F の基準に含む）。

## F 受け入れ判定（実装前固定・後出ししない）
1. **自己検査**: (a) --v14-exit-machine OFF で v13_024 と train/score CSV md5 一致 (b) py_compile (c) DESIGN_CONTRACT 識別子 PASS (d) 番人メタ確認＝枝別極端値（p_arm=0／g=9e9 等）で exit_reason 分布が枝支配になることを確認 (e) cap 0.048 実測（既存 assert） (f) score.py 既知答えテスト再pass (g) 同一バー両ヒット計数をログ。
2. **学習窓（採点窓不参照）**: _select_v14_params＝枝×タイプ別の逐次 greedy（約25〜37回・実行回数と選定表を提示）。機械全体で学習窓純増（v13 の学習窓超え）でなければ停止（採点温存・扱いはまこさん判断）。
3. precheck（学習窓 breakeven・--vs v13_024_train）→ FAIL でも審判の門として記録。
4. **両窓 score.py（公式・全部満たして採用）**:
   - 採点窓 net > 地面 v8_013（−$18）
   - **件数/日 ≥ 3.46（件数/日を上げる方向を確認・degenerate でない）**
   - 勝ち枝を壊さない＝PARTIAL_TP・TP_FILLED の net 合計が v13（+$1,413／+$635）から大きく減らない（新枝は reason 別に分離計上＝report C 節で⑨を実測）
   - fat-tail 保全＝report I 節 MFE≥5 帯の net が減らない
   - 割れたら「採用に至らず（地面 v8_013 は ratchet で維持）＋次の作り込み案」を記録。

<!-- ARC order=29 iter="E37 v14 Exit ポジション状態機械（E37レンジ幾何ネイティブ・基本maker）" 前提="E37未採用・v13 precheck FAIL be−0.52・lot状態分類でBピーク反転が最大の負け状態と確定・経路再現4R（正直な執行仮定で機械=学習窓+$2458/採点窓+$259の両窓プラス方向・単一閾値は巻き込み超過）・分岐1本への矮小化と60分固定をまこさんが差し戻し一式実装＋時間候補化を指示の上" 採否="未（実装→学習窓 枝×タイプ別選定→precheck→両窓score.py）" base_csv="trades_e37_range_scalp_v13_024_score.csv" score_csv="" train_csv="" 狙い="Exitを固定TP+固定SL+固定TIMEからポジション状態機械へ一式で作り替え＝V9は骨格のみ参考・水準はE37レンジ幾何（進捗率=entry→中央距離比・無次元）・基本maker＝利益最大化（ピーク割戻し確定・指標反転確定）と損失最小化（建値撤退・失速前倒し・backstop長の選定）を玉の4タイプ（add×TP1済み）別の学習窓選定で同時に成立させ、壁A（−$1420）壁B（−$1905）を機械として塞ぐ" 内容="--v14-exit-machine（既定OFF=v13恒等md5）＝優先順位つき7分岐（ゾーン外SL/TP1・TP2/MFE_DRAWDOWN_CUT[トレーリングmaker・フロア下限]/BE_EXIT[建値フロアmaker]/STOCH_REVERSE_EXIT[stoch GC∩含み益>0∩進捗閾・taker]/shrink失速前倒し/TIME backstop長{30,45,60分}選定）・水準は進捗率・パラメータは玉4タイプ×枝でV14_BRANCH_PARAMS＋OFFから学習窓逐次選定・新規登録はMFE_DRAWDOWN_CUT 1語（maker）＋既知答えテスト再pass・BE_EXIT/STOCH_REVERSE_EXITは登録済み再利用・入口/add本数/cap不変" 方法="自己検査（OFF恒等md5・py_compile・DESIGN_CONTRACT・番人メタ確認[枝別極端値]・cap・既知答えテスト再pass・両ヒット計数）→_select_v14_paramsで学習窓のみ枝×タイプ逐次選定（選定表提示）→機械全体で学習窓純増→precheck --vs→両窓score.py（採点窓net>−$18∩件数/日≥3.46∩PARTIAL_TP/TP_FILLED・MFE≥5帯を大きく減らさない・新枝はreason別分離計上）" -->
