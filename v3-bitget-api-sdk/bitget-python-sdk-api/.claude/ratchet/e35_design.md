# E35 戦略設計書 v1 — レンジ上下オシレーション BOT（多TFレジサポで箱定義・両方向・高頻度）

作成: 2026-06-14 / 構成: Peterson hypothesis-driven（制約→ベンチ→目的→仮説 a priori 反証可能→Indicators/Signals/Rules→個別評価→受け入れ）。
進め方: アジャイル（cat_requirements §8.4）＝ベース v1(MVP) を作る → 連続モード score.py で月次 net の地面 → 改善を1つずつ ratchet。
★ベースアップ済み: 厳密ソース調査 `research_e35_rangebot.md`（deep-research・86主張・confirmed/refuted/未検証を分類）を反映。研究駆動の主要決定＝①箱検出は単純（C2）・強さは出来高POC/多TF重なり＝touch-count使わない（R1反証）②ゲートは Choppiness+ADX+**Jump Model**（C4/C5）・**Hurst は5m短窓で使わない**（C7/C8）③**受け身指値を置かず反転確認 contrarian**（C9/R6 逆選択）④パラメータ最小 a-priori（D 過剰適合）。

## §0 位置づけ（E34 からの構造転換・なぜ）
- E34（LONG片側・深い押し目1点・add・中心TP）は iteration-3 で「メタラベルで件数を 1.7→0.56件/日 に減らして net 改善」＝**尻すぼみの改悪ルート**と判明（まこさん 2026-06-14）。0.5件/日では月$1,900 の柱に構造的に届かない。
- E34 から引き継ぐ知見: ① dev_z が唯一の両窓再現エッジ（浅いほど勝つ・N10）② レジサポを ML 特徴量に薄く混ぜると過剰適合（両窓不一致・E34 iter3 B）③ 採点窓 2025-06〜12 は steep-down 偏重（bb傾き 87% 急落）＝**真のレンジ局面でしか逆張りは効かない**（レンジ有効性ゲートが生命線）。
- ＝**構造から作り直す**: 多TFレジサポで箱を定義し、レンジの上下を両方向で繰り返し取る（高頻度）。

## §1 制約（Constraints・exchange_spec ★決済方法 / cat_requirements §6.1.1 反映）
- 銘柄/足: Bitget USDT-FUTURES BTCUSDT・5m・isolated・hedge_mode。
- **両方向（E34 と違う核心）**: LONG（箱下限で買い）と SHORT（箱上限で売り）。hedge_mode で LONG/SHORT 各1ポジ（同時最大2）。同サイドは merge・平均建値。
- 予算: 任意 t で**全建玉 size の合計 ≤ 0.12 BTC**（H1・LONG＋SHORT 合算）。
- 約定（eval_engine・改造禁止）: entry/add=指値 maker・TTL3・不約定=積まない／部分TP=指値 maker／SL・撤退=成行 taker＋slip。
- データ: 5m OHLCV（Binance spot）＋ 上位足（1h/4h を 5m から leak-safe resample）＋ funding。板情報なし。
- 期間: 学習 2021-04〜2024-12（分位）／採点 連続モード 2025-06〜2025-12（taker 実被覆内）／封印 2026-03〜05 最終1回。

## §2 ベンチマーク（Benchmark）
- レンジは V9 に Priority が無い空白＝$0 からの純増。器＝全 Priority 合算（SHORT柱 E32b 月$616.55 ＋ レンジ）。
- ベース v1 の地面＝連続モード score.py 月次 net（プラス/マイナス問わず・改善の起点）。
- ⚠️ 旧 E34 新ベース −$65 は別構造＝直接比較しない（E35 は地面から測り直す）。

## §3 目的（Objectives）＋受け入れ（a priori・★頻度を一級で宣言）
- 大目標: 月次 NET ≥ $1,900 全月クリア（本戦略の役割＝横ばい月を埋める非相関の収益源）。
- **★頻度宣言（feedback_scalp_daytrade_frequency_floor）**: E35 はデイトレ〜スキャル頻度。レンジ有効局面で**S↔R の往復を両方向で取る**＝期待件数を §6 でロジックから導出して宣言。**実績件数/日が宣言を下回って net が改善＝尻すぼみ＝却下**（一律の床でなく「実績 vs 設計意図」の照合＝§2.0 #0）。
- ベース v1 の合格＝「①宣言した頻度で動く ②地面が出る」。一発黒字は要求しない（アジャイル・地面を出して反復で超える）。

## §4 仮説（Hypothesis・a priori・反証可能）
- 対象: BTC 5m の**有効なレンジ（安定した箱）**内の往復。
- 従属変数: 入った後、反対側（中心→反対端）へ戻って部分利確に届くか＝**方向・二値**（net金額/MFE大きさでない＝H15）。
- 独立変数: ① 多TFレジサポで定義した箱の端への近さ（下限/上限ゾーン）② レンジ有効性（箱が安定・非トレンド）③ dev_z（行き過ぎ・E34 で唯一両窓再現）。
- 予想: **レンジ有効ゲートで「箱が安定している時だけ」両方向に往復を取れば、件数が構造的に増え（高頻度）、各往復の小勝ちが maker コストを上回り月次 net の地面が出る**。E33（ナイーブ両側MR）/E34（LONG片側）が no-edge だったのは、箱定義＋有効性ゲートが無くトレンドで knife を掴んだから。
- **反証**: レンジ有効ゲートを入れても (a) 往復が maker＋slip を超えない、または (b) ゲートが range と trend を分離できず steep-down でも発火して負ける、なら 5m レンジオシレーションは no-edge。

### §4.1 ★最重要・正直な赤信号（cat-bitget 固有・ベースアップで判明・まこさんと weigh）
- E35 の生命線＝レンジ有効性ゲート＝**実質レジーム判定器**。だが cat-bitget は過去にレジーム判定研究を**精度不足（v14 56%・stage3 33%）で凍結**済（CLAUDE.md「regime 判定研究は凍結」）。＝E35 は「一度できずに凍結した当のもの」に賭ける構造。
- 緩和: 凍結したのは「高精度の1h細粒度分類」。E35 が要るのは「今レンジか」の粗いゲート（Choppiness 等の合議）で、外しても flat＋箱ブレイクSLで損が限定＝凍結用途より要求が低い。さらに regime filter は業界 1.1-1.6×（industry_benchmark §2.4）。**但し regime filter は OOS で lag（遅れ）問題が出やすい（同 §2.4）＝ゲートが遅れて反応する分の損は織り込む**。
- ＝この賭けが妥当かはまこさんと決める（ベースアップ済の判断材料として提示）。

## §5 戦略仕様（Specification: Indicators → Signals → Rules）

### 5.1 Indicators（leak-safe・全 shift(1)/asof backward/上位足は確定足）
- **箱（多TFレジサポ・★研究 C2/R1 反映＝単純で十分・touch-count 使わない）**: 
  - 下限 S = 直近の {1h 実体安値（過去 N1h 本）／出来高プロファイル POC・HVN／クラシックピボット S1·S2} の**多TF合議**（節が重なる帯）。**検出は凝らない**（研究 C2: 高度 DeepSupp 0.554 ≒ 単純 Local Minima 0.507＝作り込み無駄）。
  - 上限 R = 上側（1h 実体高値／POC レジ／R1·R2）。中心 C=(S+R)/2。箱幅 W=(R−S)/C×100。
  - **強さ＝出来高 POC の濃さ＋多TF で同価格が重なるか**（研究 R1: タッチ回数＝強さ は反証＝touch-count を強さ特徴に使わない・E34 iter3 とも整合）。
- **レンジ有効性（regime ゲート・生命線・★研究 C4-C8 反映）**: **Choppiness Index >61.8（横ばい検出の主役）** ∩ ADX14<25 ∩ **Jump Model 系の regime 状態＝range（研究 C4/C5: HMM より jump penalty で持続性↑＝flicker/lag を直接抑える・penalty は CV で選ぶ＝固定値手調整しない）** ∩ 価格が過去 L 本 [S,R] に収まる ∩ W が正常域。⛔ **Hurst は 5m 短窓で使わない**（研究 C7/C8: N≥512 本必要・短窓は誤差±0.3＝regime 判定不可）。
- **行き過ぎ＋反転確認（★研究 C9/R6 反映＝最重要）**: dev_z=(close−SMA20)/std20（E34 で両窓再現エッジ）でゾーン到達を見るが、**受け身の指値を置かない**（研究 C9: maker は fill しやすい指値ほど fill 後リターン負＝負け玉を優先的に掴む逆選択／R6: 受け身両建て MM は BTC perp で −60%・Sharpe −109）。＝**反転を確認してから（反転足/stoch 反転/直近安値切上げ）アクティブに入る contrarian**。

### 5.2 Signals（事前計算）
- RANGE_OK = (Choppiness>61.8) ∧ (ADX≤thr) ∧ (JM regime=range) ∧ (過去 L 本 箱内) ∧ (W∈正常帯)。
- LONG_ENTRY = RANGE_OK ∧ 価格が下限ゾーン到達 ∧ **反転確認**（反転足/stoch 反転/直近安値切上げ）。
- SHORT_ENTRY = RANGE_OK ∧ 価格が上限ゾーン到達 ∧ **反転確認**（鏡像）。

### 5.3 Rules（merge・add・部分決済・箱ブレイク撤退）
- **入口（★研究 C9/R6＝受け身指値を置かない）**: LONG_ENTRY 成立（＝反転確認済）→ その時点で maker 指値を**アクティブに置く**（contrarian）。⛔ 箱の端に受け身で resting させない（逆選択で knife を掴む）。SHORT 鏡像。
- **add**: 保有中に同方向ゾーンで再発火 → merge・平均建値・unit 0.024・**合計 ≤ cap 0.12**。
- **出口（部分決済 scale out＝往復の小勝ち・件数の源泉）**: 複数 TP で段階利確。
  - ベース v1（MVP）はまず **単一 TP＝中心 C へ戻り（全ロット maker）** で地面を出す。改善①で「半分=中心／残り=反対端」分割（往復を刻む）。
- **SL＝箱ブレイク（構造的・固定ATRでない）**: LONG は終値が S を明確に下抜け＝レンジ終了＝撤退。SHORT は R 上抜け。＝「箱が壊れたら仮説死」。
- **時間切れ**: 中心に戻らず T_max 本 経過＝撤退（成行）。
- RANGE_OK が崩れたら新規停止（保有は出口ルールで決済）。

## §6 期待件数の導出（★頻度をロジックから・宣言・feedback_scalp_daytrade_frequency_floor）
- 1つの有効レンジ日: 価格が箱内を往復 → 下限ゾーン到達ごとに LONG・上限ゾーン到達ごとに SHORT・各々中心で利確 → 次の往復で再発火。
- ＝**1往復 ≈ LONG1＋SHORT1**。レンジ日に往復が K 回／レンジ局面が全期間の M%。
- 期待件数/日 ≈ K×2×M。E34（片側・1点・1.7件/日）に対し、両方向＋ゾーン再発火で**桁で増える想定**。
- **宣言と検証**: 実際の K・M は実装前に**学習期間の発火ファネル診断（--diagnostic・採点しない）で実測**し、E35 の頻度目標を数字で宣言。**実績件数/日が宣言を大きく下回る（ゲート/ゾーンが厳しすぎ）なら、それ自体が発見＝却下 or ゾーン再設計**（尻すぼみを最初の診断で止める）。

## §7 パラメータ（ベース v1＝データ駆動単一／ML化は反復）
| パラメータ | ベース v1 | 区分 | ML化の道筋 |
|---|---|---|---|
| 箱の窓 N1h / POC窓 / pivot | 単一固定（多TF代表値） | 固定（構造） | 反復で多TF重み学習 |
| ゾーン幅 X | 箱幅 or ATR からの比率・単一 | データ駆動（生値） | 反復で木に |
| ADX上限 / 中心flat / 箱内L本 / W正常帯 | 学習分位 単一 a priori | データ駆動 | レンジ有効性を木で判定（reg gate ML化） |
| dev_z 行き過ぎ | 学習分位 単一 | データ駆動 | 木に |
| add unit / MAX_ADDS / cap | 0.024 / 2 / 0.12 | 固定 | H1/H10（E34 iter2 で add深さ2 採用済） |
| TP（v1） | 中心C 全ロット | 固定 | 改善①で複数TP分割 |
| SL | 箱ブレイク（構造） | 構造 | — |
方針: ベース v1 は固定の前提値で地面を出す。⛔ 固定値スイープ禁止（hook L-267）＝改善は木に学習させる。

## §8 コンポーネント評価（源泉検証・過剰適合防止）
- 連続モードで「LONG片側のみ／両方向／＋レンジ有効ゲート有無」を順に測り、件数と net への寄与を切り分ける（--side / --gate フラグ）。
- ⚠️ レジサポは E34 で「ML特徴量に薄く混ぜると過剰適合」＝E35 では**箱定義（構造の背骨）として使う**（特徴量の1つでなく入口の母集団を決める）。多TF重みの ML化は地面が出てから（反復）。

## §9 H 制約照合（§4.6）
- H1 cap: 全建玉合計（LONG＋SHORT）≤0.12・add は cap 停止（score.assert_hard_constraints 物理ゲート）。
- H2 leak: 上位足は確定足のみ（resample は bar_start+freq ≤ 現在＝attach_upper_tf 同型）・pivot 確定遅延・全特徴 shift(1)/asof・出口は約定 bar の次以降・assert。
- H6 価格非依存: dev_z・距離%・W%・ATR比・分位（生値）。箱の価格そのものは閾値でなく「現価格との距離%」で使う。
- H7 足: 5m 標準・上位足は特徴のみ（採用は score.py net）。
- H8 期間分割: 分位は学習<2025-01／採点 2025-06〜12／封印不参照。
- H15 ボラ逃げ: ラベル=方向（中心戻り到達・二値）・ボラ(ATR)はゾーン幅/SL/時間のみ・LONG/SHORT 分離（両方向だが各サイド別評価）。
- H16 1ターン1変更: これは**新構造のベース v1 を1本**（E34 と同様「正しい器を1本」）。以後の改善（複数TP/多TF重み ML/ゾーン幅 ML/レンジ有効性 ML）は1つずつ。
- H5 約定: entry/add/TP=指値maker・SL/時間切れ=成行taker＋slip。

## §10 受け入れ・評価（アジャイル）
- イテレーション0（地面）: ベース v1 → **①発火ファネル診断で期待件数を宣言・実測（採点しない）** → 連続モード → precheck → score.py 月次 net（2025-06〜12）。これが地面。
- ★頻度ゲート: 実績件数/日 が宣言（§6）を大きく下回ったら、net 不問で「ゲート/ゾーンが厳しすぎ＝尻すぼみ」と判定し入口を是正（量→質の順）。
- 評価は月別＋「レンジ局面か trend 局面か」別に見る（steep-down 月は flat が正解・レンジ月で net を稼げているか）。SHORT柱と合算で非相関の収益源になるか。
- イテレーション1+: 改善1つずつ → score.py → 地面を超えた分だけ残す（ratchet）。封印は最終1回。

## §11 実装方針（複数CCチェック Workflow・暴走防止）
- 流用: 連続モードの merge/cap停止/部分決済ループ＝e34_range_base.py（両方向に拡張）／上位足 resample＝build_labels_pct.attach_upper_tf 同型／レジサポ＝structure_features（c1 pivot＋c2 classic pivot）＋出来高プロファイル POC（e34_levels の volume_at_support を POC 帯に拡張）。
- 新規 `e35_range_oscillation.py`（連続モード・両方向・箱定義・レンジ有効ゲート）＋ `e35_box.py`（多TFレジサポの箱・leak-safe）。
- 実装は複数CCチェック Workflow（cc_role §1.4.6.3・最大2巡・重い採点は外で1回・進捗監視）。判定は score.py の数字のみ（§8.4 2.9 ①）。
- 再現: `python3 e35_range_oscillation.py --diagnostic`（発火ファネル＝期待件数）→ `python3 e35_range_oscillation.py` → precheck → score.py（2025-06-01〜2025-12-31）→ report.py → analyze.py N0-N12。

出典: exchange_spec.md ★決済方法 / cat_requirements §6.1・§6.1.1・§4.6・§8.4 / E34 ledger（iter1-3・dev_z両窓再現・レジサポ過剰適合・steep-down 偏重）/ feedback_scalp_daytrade_frequency_floor / Peterson（braverock.com）。

## §12 DESIGN_CONTRACT（機械可読・実装と機械照合）

> 目的: CC が設計に時間をかけても実装で核心成分を抜く虚偽（類型G・例: E35 で RANGE_OK の Jump Model を実装から欠落）を物理検出する。
> 2層で守る:
> ① プログラム内の自己チェック＝実装(impl_file)は実行時に下記 must_combine を `_entry_contract()` で読み、`_assemble_signals()` で部品リスト通りに入口を組み立てる。設計が要求する成分（jm_ok 等）を計算していなければ実行時に自停止する（最強・どう起動しても走る）。
> ② 外側の hook＝戦略を python 実行する直前に `verify_design_contract.py` が「①の自己チェック配線（self_check_calls）が外されていないか」を確認し、外されていれば実行をブロックする。
> **まこさんは設計 GO 時に下記 must_combine を §5.2 と突き合わせて見る**（CC が contract を改ざんしたら設計書面で発覚する）。
> 成分名は実装の変数名と一致させる: chop_ok=Choppiness>61.8 / adx_ok=ADX<上限 / jm_ok=Jump Model regime=range（research C4/C5） / in_box=箱内 / w_ok=W正常帯 / low_zone/up_zone=端ゾーン / long_rev/short_rev=反転確認。

```json
{
  "impl_file": "scripts/priority_rebuild/e35_range_oscillation.py",
  "design_ref": "e35_design.md §5.2 Signals",
  "self_check_calls": ["_entry_contract(", "_assemble_signals("],
  "must_combine": {
    "range_ok": ["jm_ok", "in_box", "w_ok"],
    "long_entry": ["range_ok", "low_zone", "long_rev"],
    "short_entry": ["range_ok", "up_zone", "short_rev"]
  }
}
```

ベースアップ（2026-06-14 WebSearch＋KB）:
- regime 判定: Choppiness Index>61.8=レンジ（横ばい検出はADXより向く）／ADX<25／Hurst<0.5=平均回帰（lagging）の合議。「trend-follow はレンジで bleed・MR は強トレンドで壊滅」（tradingview QuantRegime / choppinessindex.com / quantneuraledge Hurst）。
- MR レンジ戦略: グリッド/両方向オシレーション＝レンジの標準・z-score>|2|・中心回帰で利確。落とし穴＝crypto は S/R をオーバーシュート→反転確認必須・コスト/slip/局面別を必ず織込（3commas / luxalgo / backtestme）。
- ML regime: HMM が標準（QuantStart/QuantInsti）。industry_benchmark §2.4＝regime filter 1.1-1.6×・OOS lag。trade_methods_study §1＝regime 最上位・局面別切替（v1 失敗の根）。technical §I.3.3＝regime-conditional 閾値。
- cat-bitget 固有: レジーム判定は v14 56%/stage3 33% で凍結（§4.1 赤信号）。
