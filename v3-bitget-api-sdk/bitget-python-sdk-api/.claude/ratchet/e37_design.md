# E37 戦略設計書 v2 — レンジ・スキャル ショート BOT（入口をゼロ設計し直し・出来高伸び切り×上位足条件×浅スキャル出口）

作成: 2026-06-29 / 構成: Peterson hypothesis-driven（制約→ベンチ→目的→仮説 a priori 反証可能→Indicators/Signals/Rules→個別評価→受け入れ）。
進め方: アジャイル（cat_requirements §8.4）＝ベース v2(MVP) を作る → 連続モード score.py で月次 net の地面 → 改善を1つずつ ratchet。判定は score.py の数字のみ（CC は net 計算に触れない＝import）。

★なぜ v2＝入口をゼロ設計し直すか（まこさん 2026-06-29 指示「エントリーロジックから設計し直す」）: v1（iter0）の入口は E34/E35（レンジ・デイトレ）の部品流用＝「dev_z 買われすぎ→ショート」の単純逆張りで、稀な深い行き過ぎ（1/日）を遅い %K で取るデイトレ構造だった。スキャルでない。

★ベースアップ（2026-06-29 WebSearch／WebFetch・複数種別）で確定した設計の土台:
1. **BTC で「RSI/z-score 買われすぎ→ショート」の単純逆張りは弱い**（QuantifiedStrategies バックテスト＝RSI 逆張りは BTC で機能せず・順張りは効く）。＝v1 の損の本体（戻らず price が上に走る玉）と一致。**過熱だけで fade してはいけない**。
2. **短期反転の本当のエッジ＝板の需給（order flow・VWAP乖離・流動性回復）**（arxiv 2602.00776）。だが**5m OHLCV では板が見えない**＝直接は使えない。使える代理＝**出来高スパイク（買い climax の伸び切り）・VWAP からの乖離**。
3. **BTC は中期ではトレンド優勢**（QuantPedia 10–50日＝MR より trend-following）。＝**上位足が強い上昇の最中は fade 禁止**（regime 条件付けが生命線）。
4. **平均回帰の出口は平均へ戻りで小さく速く・バリアは固定%でなく ATR/σ スケール・スキャルは短保有**（entry_exit_relationship_kb §7/§9/§18/§19）。

★中心の設計判断（過熱だけで fade しない・出来高の伸び切りで「戻る過熱」だけ取る）: 過熱（dev_z 高い）は「戻る」も「走り続ける」も両方ある。**出来高スパイク＝買い手の最後の押し込み（climax）＝枯れて戻りやすい**を確認できた時だけ fade する。過熱の閾値はむしろ**浅め（頻度を出す）にし、出来高伸び切り＋上位足条件＋反転バーで質を担保**する。＝v1 の「深い過熱・低頻度・質ゲートなし」の逆。

---

## §0 位置づけ（E36 と住み分け・§1.2.1 局面3 レンジ・優先度3）
- E36＝デイトレ型（箱の端まで1往復・最大4h・1.05件/日）。**E37＝スキャル型＝件数を上げて小さく多数取る（本筋）**。目標＝E36+E37 合算 月 net $600（まこさん 2026-06-28・物理強制 ROLE_CHECK=e37 scalp）。
- 住み分け: E36 が取らない**短い小波**を、**出来高伸び切りの反転**で拾い、**平均へ戻りで速く小さく利確・短い時間切れ**で回す。E36 と入口（出来高 climax）・出口（浅TP・短time）が別＝additive を狙う。
- ⚠️ 同方向 SHORT は本番で 1ポジ統合（台帳）＝食い合いは最終配分段で合算検証。本 MVP は E37 単独 0.12 cap で地面を測る。

## §1 制約（Constraints・exchange_spec ★決済方法 / cat_requirements §6.1.1）
- 銘柄/足: Bitget USDT-FUTURES BTCUSDT・5m・isolated・hedge_mode。
- **ショートのみ**: LONG 入口なし。SHORT 1ポジ（MVP は単発＝MAX_ADDS=1）。
- 予算: 任意 t で全建玉 size 合計 ≤ 0.12 BTC（H1・全採用戦略の共有枠）。MVP は単発 0.024。
- 約定（eval_engine・改造禁止）: entry=指値 maker・TTL3・不約定=積まない／TP=指値 maker／SL・時間切れ=成行 taker＋slip。
- データ: 5m OHLCV（Binance spot）＋上位足（5m から leak-safe resample）＋ funding。**板情報なし**＝出来高/VWAP を需給代理に使う。
- 期間: periods.py（SSOT）＝学習〜2025-02 で分位 fit／採点 2025-06〜2026-02／封印 2026-03〜05（不参照）。
- 価格非依存（H6）: 全ゲートは %/比率/σ/出来高比＝無次元。USD 絶対値の閾値/ラベルなし。
- ボラ逃げ禁止（H15）: 方向は「過熱＋伸び切り反転」＝方向シグナル。出来高/ATR は質ゲート・出口幅＝サイズ予測でない。

## §2 ベンチマーク（超える地面）
- v1（iter0）＝採点窓 net −$266・手数料負け・0.71件/日・time-exit 87%（z-score 逆張り・流用）。
- E36 デイトレ＝1.05件/日・月$137.46。**E37 はこれを明確に上回る件数（スキャル）＋黒字側**が合格の最低線。
- 最終＝全月 net≥$1,900／当面＝E36+E37 合算 月$600。

## §3 目的（Purpose）
**上位足が強い上昇でない局面で、出来高スパイクを伴う短期の行き過ぎ（買い climax の伸び切り）を SHORT し、平均へ戻りで小さく速く利確、戻らなければ短い時間切れで撤退する高頻度スキャル**を作る。＝「戻る過熱」だけを需給代理（出来高）で選び、トレンドに逆らわない。

## §4 仮説（a priori・反証可能）
- **H-a（入口の質）**: 過熱（dev_z≥k_z）∩出来高スパイク∩反転バー∩上位足が強い上昇でない、で入る SHORT は、過熱単独より「平均へ戻る率」が高い。**反証**＝勝率が tight R:R の必要勝率（§N7・1/(1+R:R)）に届かない／両窓 net<0。
- **H-b（出口＝速く小さく）**: 平均（dev_z≈0＝SMA）への浅 TP は、短い時間切れ（T_MAX 数バー）内に多数が到達する（time-exit 比率が v1 の87%から大きく下がる）。**反証**＝time-exit 比率が下がらない。
- **H-c（頻度＝スキャル）**: 過熱を浅め（k_z を v1 より低く）にし出来高で質を担保することで、件数/日が E36（1.05）を明確に上回る（目安 ≥2〜3/日）。**反証**＝件数が増えない/E36 以下＝スキャル不成立。
- **H-d（出来高が効く）**: 出来高スパイク条件を外すと net/勝率が悪化する（出来高が「戻る過熱」を選別している）。**反証**＝出来高 ON/OFF で差がない＝出来高は無寄与（→別の伸び切り代理へ）。

## §5 Indicators（5m OHLCV から・全て当該足まで＝leak-safe H2）
- **dev_z**＝(close−SMA_w)/std_w（短期の行き過ぎ・σスケール＝ボラ非依存）。w=学習窓で a-priori（短期）。
- **vol_z**＝(volume−vol の rolling 平均)/rolling 標準偏差（出来高スパイク＝買い climax の代理・order flow が無い 5m での需給代理）。
- **rev_bar**＝bearish 反転バー（close<open ∧ close<前 close）＝伸び切りの turn（速いトリガ）。
- **htf_up**＝上位足の強い上昇フラグ（例: 1h/4h を leak-safe resample し、終値が N 本前を上回り続ける＝強い上昇）。**強い上昇なら fade 禁止**。
- **vwap_dev**（任意・第2フィルタ）＝日次 intraday VWAP（Σ price·vol/Σvol・日でリセット）からの上方乖離%＝transient pressure（base-up VWAP-to-mid）。
- **atr**＝出口幅（TP/SL）の σスケール用。
> 値（w・k_z・vol_z 閾値・N・ATR 倍率・T_MAX）は**学習窓分位 or a-priori**で決め、採点窓で最良値を選ぶことはしない（L-267）。probe は当たり付け専用＝採否は実エンジン両窓 score.py。

## §6 Signals（Entry＝SHORT・confluence で質、過熱は浅めで頻度）
入口 short_entry ＝ 次の AND:
1. **over**: dev_z ≥ k_z（**浅め**＝v1 の上位decile より低い分位・頻度を出す）。
2. **vol_exh**: vol_z ≥ k_v（出来高スパイク＝買い climax・伸び切り）。＝**質の主役**（過熱だけで入らない）。
3. **rev**: rev_bar（bearish 反転バー＝turn 確認）。
4. **htf_ok**: ¬htf_up（上位足が強い上昇でない＝トレンドに逆らわない・base-up #3）。
5. （任意）**vwap_ok**: vwap_dev ≥ d（VWAP 上方乖離＝fair から伸びている）。
- 受け身指値を置かず、確認後に maker 指値（contrarian・不約定は積まない）。

## §7 Rules（Exit＝スキャル＝浅く速く・size）
- **TP（TP_FILLED・maker 指値）**: 平均へ戻り＝価格が dev_z≈z_tp（**SMA 近傍＝小さい戻り**）へ。小TPは手数料床（実コスト基準・実 maker 往復0.028%の数倍 a-priori）を超える時だけ武装（手数料割れ防止・base-up コスト下限）。
- **時間切れ（TIME_EXIT・成行 taker）**: 初回 entry から **T_MAX 数バー（例 6 本=30分・v1 の60分より短い＝スキャル短保有・half-life）**。
- **SL（成行 taker）**: ATR スケール（entry+k_sl×ATR）＝固定%でない（base-up §18・H6）。MVP は ATR-SL を採用（box-break でなく汎用）。
- **size/add**: UNIT 0.024・**MAX_ADDS=1（単発＝速く回す）**。add は v2 が黒字地面を出してから別レバー（§14 逆ピラミッド）。
- **新 exit_reason を作らない**: TP_FILLED / TIME_EXIT / SL_FILLED（既存・score.py 登録済）に揃える（出戻り防止）。

## §8 個別評価（各要素が v1 の患部にどう効くか）
- **vol_exh（新・主役）**: v1 の損の本体＝戻らず走る玉（出来高の伴わない drift の過熱）。出来高スパイクで「買い手が最後に押し込んで枯れた＝戻る」過熱だけ選別＝base-up #1/#2 の OHLCV 実装。
- **htf_ok（強化）**: v1 は1h MACD≤0 だけで強い上昇を fade して負けた。上位足の強い上昇を明示除外＝base-up #3。
- **over を浅く（頻度）＋ vol/rev/htf で質**: v1 の「深い・低頻度・質ゲートなし」を反転。スキャル頻度（H-c）と質（H-a）を両立。
- **浅TP＋短time（出口）**: v1 の time-exit 87% を、平均への小さい戻りを速く取り（H-b）短時間で回す＝turnover で件数も増える。
- **ATR-SL**: 固定%でなくボラスケール（凪で狭く・高ボラで広く）＝base-up §18。

## §9 受け入れ基準（採点前ゲート・F）
- **自己検査**: ①新パラメータ既定 OFF/中立で v1 系と恒等にできるか（または v2 は新規エンジンとして smoke で会計保存＝gross/fee/net が eval_engine と一致）②cap≤0.12 実測 ③leak grep（負shift/中央窓）pass ④出来高 ON/OFF の対照（H-d を smoke で確認）。
- **件数/日（一級・スキャル）**: 採点窓で E36（1.05）を明確に上回る（目安 ≥2〜3/日）。増えなければスキャル不成立＝不採用（ROLE_CHECK e37=scalp）。
- **学習窓で純増を先に**（採点窓 不参照・H8）: precheck breakeven >1（手数料負け解消）＋ time-exit 比率が下がる（H-b）。
- **公式判定は score.py 両窓**: 採点窓で v1（−$266）超え＝黒字側＋件数スキャル＋件数×avg 両立（freq-iter2 型の期待値崩壊でない）を確認するまで「効いた」と言わない。
- **degenerate でない**: 件数が増える（薄めて損を小さく見せるのでない）。

## §10 DESIGN_CONTRACT（acceptance で実装と機械照合）
- impl_file = scripts/priority_rebuild/e37_range_scalp_short.py（v2 で入口/出口を作り直し）。
- 入口契約（must_combine）= short_entry が over ∩ vol_exh ∩ rev ∩ htf_ok を連結（成分欠落で自停止）。
- self_check_calls = 出来高スパイク/上位足/ATR-SL の識別子（実装後 acceptance で確定）。

> ★実装は本設計を acceptance（acceptance_checklist A-F）に落とし、まこさん承認（approve_impl）後。値は学習窓分位/a-priori（probe 値を焼かない）。判定は score.py の数字。
