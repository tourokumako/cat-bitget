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
