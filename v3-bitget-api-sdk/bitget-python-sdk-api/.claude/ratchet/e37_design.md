# E37 戦略設計書 v1 — レンジ・スキャル ショート BOT（レンジ内の小波を短く小さく取る・E36 と住み分け）

作成: 2026-06-28 / 構成: Peterson hypothesis-driven（制約→ベンチ→目的→仮説 a priori 反証可能→Indicators/Signals/Rules→個別評価→受け入れ）。
進め方: アジャイル（cat_requirements §8.4）＝ベース v1(MVP) を作る → 連続モード score.py で月次 net の地面 → 改善を1つずつ ratchet。
★ベースアップ済み（2026-06-28 WebSearch 6本＝arxiv 学術／quantstart・quantinsti SSR クオンツ／quantpedia 実戦／TradingView 教育 ＋ WebFetch）: 反映した主要決定＝①平均回帰の入口は z-score（±1.5〜2σ）・利確は平均へ戻り（z→0 付近）＝箱の端まで待たず小さく取る（quantinsti）②取引コストが小 TP の採算下限を作る＝刻みが細かすぎると手数料で消える＝TP は手数料床を超える時だけ置く（arxiv 1411.5062・quantpedia grid primer）③ストップ/deadline を浅く短くするほど最適 TP も浅くなる＝スキャルは「浅 TP・浅 stop・短い時間切れ」をセットで（arxiv 1411.5062/1707.03498）④保有時間は平均回帰の half-life で決まる＝スキャルは短保有（quantinsti）⑤レンジ/オシレーションでのみ機能・トレンドで損＝レンジゲートが生命線（quantpedia grid primer・TradingView）。
★前提分析（analysis_block.md・improvement_plan.md・freq-iter2 データに立脚）: freq-iter2（広い入口×E36 長保有出口）が net 崩壊した正体は**入口の広さでなく長保有出口**＝時間切れ(240分)70件 −$2,921／勝ち玉(EDGE_TP 52分・CENTER_LOCK 48分)は約50分で解決。⇒ 短い時間切れ(60分)＋浅TP なら勝ち玉を保ち負け玉を早く小さく切れる＝E37 設計の直接根拠。

## §0 位置づけ（E36 からの住み分け・なぜ別戦略にするか）
- §1.2.1 全体戦略 局面3（レンジ・横ばい・優先度3）に**2本目の柱**を立てる。E36＝デイトレ型／**E37＝スキャル型（本筋・まこさん 2026-06-28）**。目標＝E36+E37 合算で月 net $600（まこさん 2026-06-28・E36 単体$500 から緩和）。
- **E36 の正体（食い合い回避の起点）**: 箱の**上端ゾーン（上25%）**で %K>70 反転をショート → 箱の**反対端まで**取る（EDGE_TP＝1往復まるごと）→ 最大4時間保有 → 1日 約1.05件。＝レンジを大きく1回取る。
- **E37 の住み分け**: 箱の極値を**待たず**、レンジ内の**短期の買われすぎ（小さい乖離）**を小刻みにショート → **平均へ戻ったら速く小さく利確**（箱の端まで待たない）→ **短い時間切れ**。E36 が取らない小波を拾う＝**別の入口・別の出口**で additive を狙う。
- ⚠️ **食い合い（同方向 SHORT は本番で 1ポジに統合・台帳）は最終配分段の論点**。本 MVP は E37 単独で 0.12 cap・score.py で地面を測る。E36 と additive かは配分段で合算検証（本設計は「E36 と入口/出口が別」を設計原理として担保）。

## §1 制約（Constraints・exchange_spec ★決済方法 / cat_requirements §6.1.1 反映）
- 銘柄/足: Bitget USDT-FUTURES BTCUSDT・5m・isolated・hedge_mode。
- **ショートのみ（§1.2.1 E37＝ショート）**: LONG 入口は持たない。SHORT 1ポジ（add は merge・平均建値）。
- 予算: 任意 t で全建玉 size 合計 ≤ 0.12 BTC（H1）。E37 はスキャル＝浅 add（MVP は単発＝後述）。⚠️ 0.12 は**全採用戦略の共有枠**（P21/P23/E28/E35/E36 と同じ枠を奪い合う）＝本番は合算で検証（単独 CSV の cap はその戦略だけで 0.12）。
- 約定（eval_engine・改造禁止）: entry/add=指値 maker・TTL3・不約定=積まない／TP=指値 maker／SL・時間切れ=成行 taker＋slip。
- データ: 5m OHLCV（Binance spot）＋ 上位足（1h を 5m から leak-safe resample・1h MACD ゲート）＋ funding。板情報なし。
- 期間: periods.py（SSOT）＝学習〜2025-02 で分位 fit／採点 2025-06〜2026-02／封印 2026-03〜05（不参照）。

## §2 ベンチマーク（Benchmark）
- レンジ・スキャルは現ポートフォリオに**無い**＝$0 からの純増（E36 デイトレとは別の入口/出口＝重複でなく上乗せを狙う）。
- ベース v1 の地面＝連続モード score.py 月次 net（プラス/マイナス問わず・改善の起点）。一発黒字は要求しない（アジャイル）。
- ★直接の比較相手＝**freq-iter2**（広い入口×長保有出口・$79）。E37（広い入口×スキャル出口）が freq-iter2 を超えるか＝§4 仮説の合否。参考＝E36 base scenecap（$1237・住み分け相手）。最終は合算（目標$600）。

## §3 目的（Objectives）＋受け入れ（a priori・★頻度を一級で宣言）
- 大目標: 月次 NET ≥ $1,900 全月クリア。当面＝E36+E37 合算 月$600（E37 の役割＝レンジ局面をスキャルで厚くする）。
- **★頻度宣言（feedback_scalp_daytrade_frequency_floor・E37＝スキャル＝高頻度が役割）**: E37 は E36（1.05件/日）より**明確に高頻度**。期待件数を §6 でロジックから導出し --diagnostic で実測宣言。**件数を増やして net がプラスの地面**が出ることが MVP の眼目（件数を減らして net を作る＝尻すぼみは却下）。
- ベース v1 の合格＝「①宣言した高頻度で動く ②地面が出る ③小 TP が手数料床を超えて採算する」。

## §4 仮説（Hypothesis・a priori・反証可能）
- 対象: BTC 5m の**有効なレンジ内**で起きる**短期の行き過ぎ（小乖離）の戻り**。
- 従属変数: 入った後、短期平均（SMA20）へ戻って小 TP に届くか＝**方向・二値**（net金額/MFE 大きさでない＝H15）。
- 独立変数: ① レンジ有効性（ER 低・非トレンド）② 1h MACD≤0（ショート寄り regime）③ 短期 dev_z の行き過ぎ（+方向＝買われすぎ）④ 短期反転確認（速い %K の下降転換）。
- **予想（核心・freq-iter2 データに立脚）**: **「箱極値を待たない広めの入口」を「浅 TP・短い時間切れのスキャル出口」とセットにすれば、各小波の小勝ちが maker＋slip を超えて net の地面が出る**。freq-iter2（広い入口×E36 長保有出口・$79）が崩壊した正体は、**広い入口でなく長保有出口＝低品質玉が240分 time-exit まで走り −$2,921／平均負け$26-29 に肥大した**（analysis_block ④・C/I/K節）。一方 freq-iter2 の勝ち玉（EDGE_TP 52分・CENTER_LOCK 48分）は**約50分で解決**＝60分時間切れ内に収まる。**E37 は出口がスキャル（浅 TP・60分時間切れ）＝広い入口でも玉が速く解決し、勝ち玉を保ちつつ負け玉の逆行を早く小さく止める**。
- **反証**: 浅 TP・短時間切れにしても (a) 小 TP が maker＋slip を超えず採算しない、または (b) 広い入口の低品質玉が短時間切れ/箱ブレイクで負け越し、小勝ちで取り返せない（＝freq-iter2 と同型＝スキャル出口でも救えない）なら、レンジ・スキャル ショートは no-edge。

### §4.1 正直な赤信号（過去の同型失敗・まこさんと weigh）
- **freq-iter2 が「入口を広げて件数↑」で net 崩壊済**（採点 $79・期待値/玉 大幅低下・analysis_block ①）。E37 は「出口をスキャル化して救う」が唯一の差＝**この差が効くか否かが全て**。効かなければ freq-iter2 の再演になる。
- 緩和（データ根拠あり）: freq-iter2 の損は「長保有 time-exit に集中・勝ち玉は約50分で解決」＝出口時間の短縮が効く余地が**データで見えている**（推測でない）。それでも採否は実エンジン両窓 score.py のみ。効かなければ正直に「レンジ・スキャル ショートは no-edge」と記録（block_premature_giveup＝事前却下しない・数字で出す）。

## §5 戦略仕様（Specification: Indicators → Signals → Rules）

### 5.1 Indicators（leak-safe・全 shift(1)/asof backward/上位足は確定足）
- **箱（E36/E35 と同じ多TFレジサポ＝e35_box 共有ユーティリティを流用）**: 下限 S・上限 R・中心 C・箱幅 W。**E37 は箱の極値ゾーンを入口に使わない**が、箱は「レンジか／箱が壊れたか（SL）」の枠として使う。
- **レンジ有効性（regime ゲート・E36 と同じ）**: ER（Kaufman Efficiency Ratio・低い=往復=レンジ）< 学習分位 q0.5 ∩ in_box（過去 L 本 箱内）。Choppiness/ADX は補助・記録。
- **ショート寄り regime（shortset1 と同じ）**: 1h MACD ≤ 0（leak-safe resample・attach_upper_tf）。
- **短期の行き過ぎ（E37 の入口主役・★E36 の up_zone とは別）**: dev_z=(close−SMA20)/std20（E34/E35 で両窓再現エッジ）。+方向（買われすぎ）が学習分位の z_entry（≈+1.5σ 相当・学習分位 a-priori）以上。
- **短期反転確認（速い・スキャル）**: %K（stoch・E36 の 14 より短い窓 9）が下降転換（k>上限 ∧ k<前k）＝行き過ぎが折り返した瞬間に入る contrarian（受け身指値を置かない・E35 §5.1 C9 逆選択回避）。

### 5.2 Signals（事前計算）
- range_ok = (ER < q_er) ∧ in_box。
- short_bias = (1h MACD ≤ 0)。
- ob_dev = (dev_z ≥ z_entry)  … 短期 買われすぎ（箱極値を要求しない＝E36 の up_zone と別）。
- short_rev = (k9 > k_hi) ∧ (k9 < k9.shift(1))  … 速い反転確認。
- **SHORT_ENTRY = range_ok ∧ short_bias ∧ ob_dev ∧ short_rev**。

### 5.3 Rules（merge・浅 add・スキャル出口）
- **入口**: SHORT_ENTRY 成立（反転確認済）→ その時点で maker 指値をアクティブに置く（contrarian・TTL3・不約定=積まない）。
- **add（浅・スキャル＝E36 の MAX_ADDS=5 と別）**: MVP は **MAX_ADDS=1（単発・size=UNIT 0.024）**＝スキャルは1玉を速く回す。cap 0.12 は自明に満たす。改善で浅 add（2まで）を検討。
- **出口（スキャル＝浅く速く・件数の源泉）**:
  - **TP（maker・主役）**: 短期平均へ戻り＝dev_z ≤ z_exit（≈+0.3〜0.5σ・学習分位 a-priori）で全ロット maker 利確。**手数料床（COST_FLOOR 0.20%）を超える時だけ TP を置く**（arxiv 1411.5062・quantpedia grid primer＝刻みが細かすぎると手数料で消える・E36 と同じ COST_FLOOR 武装）。
  - **時間切れ（taker・短い＝E36 48本/4h と別）**: 初回 entry から **T_max=12本（60分）**で未決済なら成行撤退（スキャル＝短保有・half-life）。
  - **SL＝箱ブレイク（構造・固定ATRでない）**: 終値が箱上限 R を明確に上抜け＝レンジ終了＝成行撤退（E36 と同じ構造 SL の考え）。
- range_ok が崩れたら新規停止（保有は出口ルールで決済）。

## §6 期待件数の導出（★頻度をロジックから・宣言）
- レンジ局面（ER<q0.5＝全期間の約50%）で、短期 dev_z>z_entry の買われすぎ折り返しは E36 の「箱上端のみ」より**ずっと頻繁**（箱内のどこでも起き得る）。
- 浅 TP（dev_z→z_exit）＋短時間切れ（60分）で1玉が速く解決＝**回転が速く再エントリーが早い**＝件数が伸びる。
- 期待件数/日 ≈ E36（1.05件/日）の**数倍**を狙う（スキャル）。**実際の値は --diagnostic（発火ファネル・採点しない）で実測して宣言**。実績が E36 と同水準なら「広げた意味なし＝入口/ゾーン再設計」（量→質の順）。

## §7 パラメータ（ベース v1＝学習分位の単一 a-priori／ML化は反復）
| パラメータ | ベース v1 | 区分 | ML化の道筋 |
|---|---|---|---|
| 箱の窓・多TF | e35_box 既定（E36 と同じ） | 固定（構造） | 反復で多TF重み学習 |
| ER 窓/平滑/分位 q_er | 20 / 5 / q0.5（学習分位・E36 と同じ） | データ駆動 | 木に |
| 1h MACD ゲート | ≤0（shortset1 と同じ） | 固定（regime） | — |
| dev_z 窓 / z_entry | SMA20·std20 / 学習分位（≈+1.5σ） | データ駆動 | 木に |
| %K 窓 / k_hi | 9 / 70 | データ駆動 | 木に |
| z_exit（TP 戻り） | 学習分位（≈+0.3〜0.5σ） | データ駆動 | 木に |
| T_max 時間切れ | 12本（60分） | 固定（スキャル） | 反復で調整 |
| SL | 箱ブレイク（構造） | 構造 | — |
| add unit / MAX_ADDS / cap | 0.024 / 1 / 0.12 | 固定 | H1/H10 |
方針: ベース v1 は学習分位の単一前提値で地面を出す。⛔ 固定値スイープ禁止（hook L-267）＝採点窓で最良値を選ばない。z_entry/z_exit/q_er は学習窓分位 a-priori（probe で出した特定数値を焼かない＝acceptance ★疑似シミュ由来の固定値ゼロ）。

## §8 コンポーネント評価（源泉検証・過剰適合防止）
- 連続モードで「①箱極値入口（E36 同型）／②短期 dev_z 入口（E37）」、「①長保有出口（4h）／②スキャル出口（60分・浅TP）」を切り分けて測る（--entry / --exit フラグ）＝**「広い入口×スキャル出口」が freq-iter2（広い入口×長保有出口）を超えるか**を直接見る（§4 仮説の検証＝設計の眼目）。
- ⑨巻き込み検証（cat_requirements §8.4・Exit/切る系の作法）＝該当なし（E37 は入口を広げ小さく取る＝勝ち玉を切る機構でない）。⛔ 浅 TP が勝ち玉を刈り過ぎないかは net で見る（L-297 積極部分利確の轍＝採点窓で確認・freq-iter2 の勝ち玉は約50分解決＝60分内に収まる見込み）。

## §9 H 制約照合（§4.6）
- H1 cap: 全建玉合計 ≤0.12（MVP は MAX_ADDS=1＝size 0.024 で自明）・_verify_cap 実測 assert ＋ score.assert_hard_constraints。
- H2 leak: 上位足 1h は確定足のみ（attach_upper_tf 同型）・dev_z/ER/stoch は当該足まで（shift 安全）・出口は約定 bar の次以降・grep assert（shift(-/center=True）。
- H5 約定: entry/add/TP=指値 maker・時間切れ/箱ブレイク SL=成行 taker＋slip。
- H6 価格非依存: dev_z（無次元）・z 分位・ER（無次元）・距離%・W%。USD 絶対値の閾値/ラベルなし。
- H8 期間分割: 分位は学習<2025-03 で fit／採点 2025-06〜2026-02／封印不参照（periods import・手打ちなし）。
- H13 judge: **新 exit_reason を出すなら score.py の maker/taker 登録＋既知答えテスト再pass**（②別承認）。MVP の exit_reason は既存（TP_FILLED=maker / TIME_EXIT=taker / SL=taker 相当）に揃え、新規追加を避ける（出戻り防止・acceptance D）。本ファイルは judge を触らない。
- H15 ボラ逃げ: ラベル=方向（短期平均へ戻り到達・二値）・ボラ(ATR/std)はゾーン/SL/時間のみ・ショート単独評価。dev_z は方向（買われすぎ）であってボラ大きさ予測でない。
- H16 1ターン1変更: これは**新戦略 E37 のベース v1 を1本**（新しい器を1本＝E34/E35 と同じ扱い）。以後の改善（浅 add・z 分位 ML・複数 TP 刻み・dev_z 窓 ML）は1つずつ。

## §10 受け入れ・評価（アジャイル）
- イテレーション0（地面）: ベース v1 → **①発火ファネル診断 --diagnostic で期待件数を宣言・実測（採点しない）** → 連続モード → precheck → score.py 月次 net（2025-06〜2026-02）。これが E37 の地面。
- ★頻度ゲート: 実績件数/日 が E36 と同水準（広げた意味なし）or 宣言を大きく下回るなら、net 不問で入口/ゾーン是正（量→質）。
- ★採算ゲート: 小 TP が maker＋slip を超えているか（gross/fee 分解・report.py J）＝スキャルの生命線。
- 評価は月別＋「レンジ局面か trend 局面か」別。**freq-iter2 比較**（広い入口×長保有 $79）に対し E37（広い入口×スキャル出口）が地面で上回るか＝§4 仮説の合否。
- イテレーション1+: 改善1つずつ → score.py → 地面を超えた分だけ残す（ratchet）。封印は最終1回。最終は E36 と合算で月$600 へ（配分段で食い合い検証）。

## §11 実装方針（小局所＝新規1ファイル・cc_role §1.4.6.3）
- 流用（import）: strat_base（① load_5m / ⑤ _verify_cap・_funding_cost / ⑥ _output_and_report / ⑦ 定数 UNIT/CAP/TTL/ENTRY_OFFSET/COST_FLOOR）／ e35_box（箱）／ build_labels_pct（1h MACD resample・leak-safe）／ e34_range_zscore_taker・e34_range_base（add_indicators・stoch・dev_z）。
- **⛔ e36_short_oscillation は import しない**（E35/E36 切り分けと同じ独立原則＝E37 も兄弟・独立）。箱/ER ゲートの組み立てヘルパは E37 が自前で持つ（E36 が E35 から複製したのと同じ流儀）。
- 新規 `e37_range_scalp_short.py`（連続モード・ショート専用・短期 dev_z 入口・スキャル出口）。出力は strat_base の共通書き出し（--tag 連番・archive・上書き防止を自動踏襲）。サイドカー（使用パラメータ・Entry/Exit ロジック）必須。
- 既定 OFF で恒等の起点が無い（新戦略＝ゼロから）ので、自己検査＝①cap 実測 ②leak grep ③発火件数の妥当性 ④恒等でなく「会計保存（lot 合計＝net）」。
- 判定は score.py の数字のみ（§8.4 2.9 ①・CC は net 計算に触れない＝import のみ）。
- 再現: `python3 e37_range_scalp_short.py --diagnostic`（発火ファネル＝期待件数）→ `python3 e37_range_scalp_short.py` → precheck → score.py（2025-06-01〜2026-02-28）→ report.py → analyze.py --vs（E36 base）--train。

出典: exchange_spec.md ★決済方法 / cat_requirements §1.2.1・§6.1・§6.1.1・§4.6・§8.4 / E36 ledger（freq-iter1/freq-iter2/scene-cap）/ analysis_block.md・improvement_plan.md（freq-iter2 前提分析）/ E35 design / feedback_scalp_daytrade_frequency_floor / WebSearch+WebFetch（arxiv 1411.5062・arxiv 1707.03498・quantinsti mean reversion building blocks・quantpedia grid primer・TradingView range scalping・2026-06-28）/ Peterson（braverock.com）。

## §12 DESIGN_CONTRACT（機械可読・実装と機械照合）

> 目的: 設計に時間をかけても実装で核心成分を抜く虚偽（類型G）を物理検出。実装(impl_file)は実行時に下記 must_combine を `_entry_contract()` で読み `_assemble_signals()` で部品リスト通り組み立て、成分（er_ok/ob_dev 等）を計算していなければ自停止する。hook `verify_design_contract.py` が self_check_calls の配線を確認。
> **まこさんは設計 GO 時に下記 must_combine を §5.2 と突き合わせる**。
> 成分名（実装の変数名と一致）: er_ok=ER<q_er / in_box=箱内 / macd_ok=1h MACD≤0 / ob_dev=dev_z≥z_entry（短期買われすぎ・E36 の up_zone と別） / short_rev=速い%K 下降転換。

```json
{
  "impl_file": "v3-bitget-api-sdk/bitget-python-sdk-api/scripts/priority_rebuild/e37_range_scalp_short.py",
  "design_ref": "e37_design.md §5.2 Signals",
  "self_check_calls": ["_entry_contract(", "_assemble_signals("],
  "must_combine": {
    "range_ok": ["er_ok", "in_box"],
    "short_entry": ["range_ok", "macd_ok", "ob_dev", "short_rev"]
  }
}
```
