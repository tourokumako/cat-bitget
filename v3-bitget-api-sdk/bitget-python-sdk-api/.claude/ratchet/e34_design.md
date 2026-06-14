# E34 戦略設計書 v2 — レンジ逆張りBOT（行き過ぎ ∩ 投げ売り枯渇・LONG・add＋部分決済）

作成: 2026-06-13 / 版: v2（v1 は per-trade 単発で本番運用を反映せず＝add・部分決済 scale out を欠いた誤り。正しい決済方法で設計し直し）
構成: Peterson hypothesis-driven（制約→ベンチ→目的→仮説a priori反証可能→Indicators/Signals/Rules→個別評価→受け入れ）。
進め方: アジャイル（cat_requirements §8.4・CLAUDE.md）＝**ベース v1(MVP) を作る → 連続モード score.py で月次 net の地面 → 改善を1つずつ ratchet**。1回判定で破棄しない。

---

## §1 制約（Constraints＝Bitget本番再現の枠・exchange_spec ★決済方法 / cat_requirements §6.1.1 を読了して反映）
- 銘柄/足: Bitget USDT-FUTURES BTCUSDT・5m・isolated。
- **ポジションの持ち方（正本＝exchange_spec ★決済方法）**:
  - 同サイドは**1ポジに統合（merge・平均建値 openPriceAvg）**。同サイドの複数同時建玉は不可。
  - add（同サイド買い増し）＝既存ポジに積み増し・**平均建値**。unit 0.024・最大5段で size 0.12。
  - 決済は**全体も部分もできる**＝1ポジに複数 TP で**段階利確（部分決済 scale out・最大20個・size 指定・Reduce-only）**。
- 予算: 任意 t で**全建玉 size の合計 ≤ 0.12 BTC**（H1・1ポジ上限でない）。
- 約定（eval_engine・改造禁止）: entry/add=指値 maker `close×(1−0.0001)`・TTL3・不約定=その回は積まない／部分TP=指値 maker／SL・時間切れ=成行 taker＋slip。
- データ: 5m OHLCV（Binance spot 価格）＋ taker_ls（Binance metrics・asof backward）＋ funding。板情報なし。
- 期間: 学習 2021-04〜2024-12（Phase0 素エッジ）／採点は連続モード新窓 2025-06〜2026-02（封印 2026-03〜05 は最終1回）。

## §2 ベンチマーク（Benchmark）
- レンジは V9 に Priority が無い空白＝$0 からの純増。**ベース v1 の地面＝連続モード score.py の月次 net**（プラス/マイナス問わず＝改善の起点の数字）。
- 器＝全 Priority 合算（§6.2）。本戦略は横ばい月を埋める部品（goal_block §6 届く構成）。

## §3 目的（Objectives）＋受け入れ（a priori）
- 大目標: 月次 NET ≥ $1,900 全月クリア。本戦略の役割＝横ばい月を埋める。
- **ベース v1 の合格＝「動いて地面が出る」こと**（一発で黒字でなくてよい）。地面を出したら改善で超える（ratchet）。
- ⛔ 1回の per-trade/score 判定で「no-edge→破棄」しない（L-278・cat_requirements §8.4 アジャイル節）。素朴版が未黒字なのは出発点・損の出所＝次に直す箇所。

## §4 仮説（Hypothesis・a priori・反証可能）
- 対象: BTC 5m レンジ下限での反発（横ばい相場の往復）。
- 従属変数（予測対象）: 中心へ回帰して部分利確に到達するか＝**方向・二値**（net金額/MFE大きさでない＝H15）。
- 独立変数（入力）: ① 相対的な行き過ぎ（dev_z）② taker 投げ売りの枯渇 ③ 非トレンド（ADX 低）。
- 予想: 固定閾値の素朴MR（E33）は no-edge。相対分位＋投げ売り枯渇で方向が立ち、add で平均建値を下げ・複数TPで往復を刻むと月次 net の地面が出る（E28 が同2道具を下げ相場LONGで per-trade 実証＝+0.29→+1.27/件）。
- 反証/作り込みの起点: 連続モード月次 net がマイナスなら、損の出所（TP刻み・SL・add間隔・行き過ぎの深さ）を次の反復で直す。

## §5 戦略仕様（Specification: Indicators → Signals → Rules）

### 5.1 Indicators（leak-safe・全 shift(1)/asof backward）
SMA20・std20・dev_z=(close−SMA20)/std20・ATR14・ADX14・taker_ls。

### 5.2 Signals（事前計算）
- S1 行き過ぎ: dev_z ≤ thr_z（学習分位 q0.05・cross-in）
- S2 投げ売り枯渇: taker_ls ≤ thr_taker（学習 q0.25＝成行売り過熱）
- S3 非トレンド: ADX14 ≤ 25
- ENTRY = S1 ∧ S2 ∧ S3（LONG のみ）

### 5.3 Rules（★v2 で正しく＝merge・add・部分決済・cap を反映）
- **入口**: ENTRY 成立 → 次バー maker 指値 LONG・unit 0.024。
- **add（積み増し・平均建値）**: 保有中に ENTRY が再発火 → 既存ポジに unit 0.024 積み増し（merge・平均建値）。**合計 ≤ cap 0.12（最大5段）**。レンジ下限圏で売られすぎが続くと平均建値が下がる（構造はナンピン側＝段数と SL で限定）。
- **出口（部分決済 scale out＝往復を刻む小勝ち）**: 複数 TP で段階利確。
  - ベース v1（MVP）はまず **単一 TP＝平均建値からの中心への戻り（全ロット）** で地面を出す。
  - 改善①（次の反復）で **複数 TP に分割**（例: 平均建値+α で半分・中心で残り）＝レンジの往復を刻む。
- **SL**: ハードSL＝平均建値 − k×ATR14（全ロット・成行・ブレイクダウン回避）。
- **時間切れ**: T_max 本（全ロット・成行）。
- 保有合計が cap 0.12 に達したら add 停止（E32b の cap停止ループと同じ）。

## §6 パラメータ（固定 / データ駆動）
| パラメータ | 値 | 区分 | 根拠 / 固定を外す道筋 |
|---|---|---|---|
| add unit | 0.024 BTC | 固定 | V9 と同じ・H10 |
| MAX_ADDS | 5（cap 0.12） | 固定 | exchange_spec・H1 |
| SMA・std・ADX 期間 | 20 / 20 / 14 | 固定（単一） | 標準・効けば Phase1 で木に学習 |
| ADX 上限 | 25 | 固定（単一） | KB §I RANGING |
| SL = k×ATR14 | k=1.5 | 固定（単一） | スイープしない（hook L-267） |
| TP（ベース v1） | 平均建値→中心 全ロット | 固定（単一） | MVP。改善①で複数TP分割 |
| 時間切れ T_max | 48本(4h) | 固定（単一） | E28 と同・改良で OU 半減期 |
| 方向 | LONG のみ | 固定判断 | BTC 非対称（E33/E28） |
| コスト床 | 0.20% | 固定 | maker往復+slip 未満の TP を除外 |
| thr_z / thr_taker | 学習 q0.05 / q0.25 | データ駆動（生値） | a priori 単一・分位プラトーは要まこさん GO（hook） |

方針: ベース v1 は固定の前提値で**地面**を出す。改善で「複数TP分割／深い極値・情報バー／固定値を木に学習／サイジング」を1つずつ ratchet。

## §7 コンポーネント評価（過剰適合防止）
- 連続モードで「入口のみ／入口+add／入口+add+部分決済」を順に測り、どの要素が地面を動かすかを切り分ける。
- leak: 全 indicator に shift(1)/asof の assert（H2）。

## §8 受け入れ・評価（アジャイル）
- イテレーション0（地面）: ベース v1 を連続モード → precheck（breakeven/cap）→ score.py 月次 net（新窓 2025-06〜2026-02）。これが**地面**。
- イテレーション1+: 改善レバーを1つずつ → 連続モード score.py → 地面を超えた分だけ残す（ratchet）。封印 2026-03〜05 は最終1回。

## §9 H制約照合
- H1 cap: 全建玉合計 ≤ 0.12（時系列・score.assert_hard_constraints が物理ゲート）・add は cap到達で停止。
- H2 leak: 全特徴 shift(1)/asof + assert。
- H6 価格非依存: dev_z・分位・pct・ATR比。
- H8 期間分割: Phase0 学習 ≤ 2024-12 ／ 採点 連続モード新窓。
- H15 ボラ逃げ: §4 ラベル=方向・§5.3 ボラ(ATR)は SL/保有時間のみ・LONG分離。
- H16 1ターン1変更: ベース v1 を1本作る（add・部分決済は本番運用の正しい一式＝複数レバーでなく「正しい器」）／改善は以後1つずつ。

## §10 実装・再現
- 連続モードの忠実ループ（add・cap停止・merge・部分決済）は既存機構を流用＝`measure_ground_combined_E32b.py`（cap停止 add ループ）＋`measure_p23_ground_scaleout.py`（部分決済 scale out・E0.3）の枠に、入口を E34 レンジ Signals に差し替える。
- 新規 `e34_range_base.py`（連続モード・ベース v1）。出力 `trades_e34_range_base.csv`。
- 再現: `python3 scripts/priority_rebuild/e34_range_base.py` → `precheck.py <csv> --authorize <csv名>` → `score.py <csv> --start 2025-06-01 --end 2026-02-28`。

---

## 付録: v1 からの訂正点（正しい仕様の反映）
1. v1「per-trade 単発・1ポジ・保有中スキップ」→ 誤り。本番は同サイド merge・平均建値・add で cap 0.12 まで積める。
2. v1 は**部分決済（scale out）を欠いていた** → レンジの往復を刻む小勝ちの核心。複数 TP で段階利確を入れる。
3. 判定を per-trade ○× でなく**連続モード score.py の月次 net（地面）**にし、アジャイルで改善（1回判定で破棄しない）。
出典: exchange_spec.md ★決済方法 / cat_requirements §6.1・§6.1.1・§8.4 / Peterson（braverock.com）。

---

## §11 iteration-3 設計 — メタラベル Entry フィルタ ＋ レジサポ特徴量（まこさん GO 2026-06-14・実装前プレゼン GO 済）

### §11.0 6軸ゲート宣言（H15・entry_fix_6axis_gate）
- **軸4 cascade を閉じる**: §18.5 逐語「cascade 構造不在（= ML 単段 entry 判定）」→「前段に固定ロジック段1を足す（高 recall で絞る→ML 段）」。本設計＝前段 dwell（固定ルール・候補生成＝段1）→後段 ML メタラベル（段2）。
- **軸6 Meta 同型を閉じる**: §18.5 逐語「Meta-Labeling 失敗（= primary も secondary も同型）」→「primary≠secondary 異種・secondary は盲点情報入力」。primary=dwell 固定ルール／secondary=LightGBM＝異種。secondary に**盲点情報＝レジサポ**（固定ルールが見ない価格の節目）を入力。
- 軸1 ボラ逃げは不違反（§11.5 H15）。

### §11.1 仮説（a priori・反証可能）
- 玉単位分析（dwell_max2 の N10-N12）＝設計前提が逆: dev_z 最強分離（相関+0.26・浅いほど勝つ・両窓再現✓）。N12 最良象限（dev_z≥中∩ret_5≥中）でも net −$13＝**値動き系だけでは breakeven 止まり**＝構造（レジサポ）という別次元が要る。N11＝方向ミスが主因。
- 仮説: dwell 候補のうち「向きが当たる玉（中心TP 先着）」を ML が選別し、特にレジサポ（強いサポート直上）を入れると、momentum だけの breakeven を超えて陽性に動く。深い乖離でも強サポ直上なら反発／遠ければナイフ。
- 反証: 成分B（+レジサポ）が成分A（既存分離指標のみ）を連続モード net で超えなければ、レジサポは寄与なし（A だけが breakeven 近辺に留まる想定）。

### §11.2 レバー（1ターン1変更＝メタラベル Entry フィルタ・出口/add/cap/候補生成 不変）
- primary（候補生成・**不変**）＝dwell_max2（S1' dev_z≤q0.05 ゾーン滞在 ∩ S2 taker≤q0.25 ∩ S3 ADX≤25・MAX_ADDS=2・cap0.12・出口 TP=中心/SL=1.5ATR/時間切れ4h）。
- secondary（**新規＝レバー本体**）＝LightGBM 二値。候補1件ごとに「中心TP 先着か（方向）」の prob を予測。`entry_sig &= (prob ≥ θ)` で初回も add も同じく gating。
- 源泉検証（§7）: 成分A（既存分離指標のみ）vs 成分B（A＋レジサポ）を同イテレーションで測り、レジサポの寄与を切り分ける（A/B ablation）。

### §11.3 特徴量
- 成分A（既存・全カラム e34_range_base に記録済）: dev_z, ret_5, rsi, stoch_k, rsi_slope, bb_width, atr_pct(=atr/close×100), adx, bb_mid_slope_pct, taker_ls。
- 成分B（A＋レジサポ・**流用 structure_features.compute_c1_features(df, N)**＝L-179 leak 修正済・phase_compliance §5.3 確認済）:
  - support_distance_pct_N（サポートまでの距離%）／ resistance_distance_pct_N（レジまで＝中心TP 伸びしろ%）／ nearest_level_touch_count_N（サポートの強さ＝過去タッチ回数）。
  - ＋ volume_at_support（サポート帯の出来高 ÷ 窓出来高＝出来高プロファイルの節・無次元・新規追加）。
  - 窓 N・タッチ許容バンドは a priori 単一（structure_features 既定＝構造パラメータ・SMA期間と同格・スイープしない）。
- 全て価格非依存（%・回数・出来高比＝H6）。

### §11.4 ラベル・学習・θ
- ラベル＝Triple Barrier の**方向**（候補から単発前向き sim で 中心TP 先着=1／SL・時間先着=0）＝方向ベース（金額/MFE大きさでない＝H15）。exit ロジックは連続モードと同式（armed 中心・SL=1.5ATR・48本）。
- 学習 2021-04〜2024-12（候補のみ）／embargo 2025Q1／採点 連続モード 2025-06〜2025-12（taker 実被覆内）。LONG 単独。
- LightGBM 過学習対策（num_leaves 小・min_child 大・L1/L2・class weight）。lightgbm は python3.13。
- θ＝学習 OOF で1度だけ決める単一 a priori（採点窓でスイープしない＝forbid_fixed_value_tuning hook）。**採用率を N0 で報告**＝degenerate（near-inaction・E21 全通過/E27 採点7件）でないか確認。E8a-2 の「単一スライス θ は分布シフトで外す」を踏まえ OOF で選ぶ。

### §11.5 H 制約照合
- H1 cap: 不変（メタラベルは件数を減らすだけ・cap0.12 物理ゲートそのまま）。
- H2 leak: レジサポ＝pivot 確定遅延（j は j+2 で確定）＋窓 [i-N+1, i]・全特徴 shift(1)/asof・secondary は過去学習→前向き適用・Triple Barrier は LABEL（特徴でない・build_labels と同型）＝コードで assert。
- H6 価格非依存: 全特徴 %/回数/出来高比。
- H8 期間分割: 学習≤2024-12／embargo 2025Q1／採点 2025-06〜12（封印 2026-03〜05 最終1回）。
- H15 ボラ逃げ: ラベル=方向／LONG 単独／ATR は SL・時間のみ／学習後 feature importance でボラ(atr_pct/bb_width)が支配でないことを確認（レジサポ/dev_z 系が主役）。
- H16 1ターン1変更: レバー=メタラベル+レジサポ。候補生成/add/出口/cap 不変。A/B ablation で源泉分解。

### §11.6 受け入れ（ratchet）
- 連続モード score.py 月次 net が新ベース dwell_max2 −$506 を超えた分だけ残す。通過点＝黒字化（残り必要勝率 8.5pt を方向当たりで埋める）。超えなければ現状ベース維持・改善継続（破棄でない・L-278）。
- 成分A→B の差＝レジサポの実力（§7 源泉検証）。

### §11.7 実装（複数CCチェック Workflow・暴走防止＝最大2巡・重い採点は外で1回）
- 新規 `e34_levels.py`（compute_c1_features 流用＋volume_at_support・leak assert）／`train_e34_meta.py`（LightGBM A/B・Triple Barrier 方向ラベル・θ OOF・py3.13）／`e34_range_base.py` 改修（`--meta-model <path> --theta <θ> --meta-set A|B`・lazy import lightgbm・`entry_sig &= prob≥θ`）。
- 再現: `python3.13 train_e34_meta.py --set {A,B}` → `python3.13 e34_range_base.py --entry dwell --max-adds 2 --meta-model <A|B> --theta <θ>` → precheck → score.py（2025-06-01〜2025-12-31）→ report.py --vs dwell_max2 → analyze.py（N0-N12）。
