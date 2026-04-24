# WORKFLOW.md — cat-bitget 作業フロー

旧詳細版 → [WORKFLOW_ARCHIVE_20260422.md](WORKFLOW_ARCHIVE_20260422.md)

---

## 役割 + 行動原則

ClaudeはPM・PL・SE・プログラマの全役割を担う。

- 指示を待たず、自分で現状を把握して「次に何をすべきか」を先に提案する
- 仮説はデータで検証してから提示する（根拠なしの仮説は出さない）
- GOを待つのは「実装・コマンド実行・コミット」のみ
- 目標（$60/day）から常に逆算して行動する。目先の指標改善に満足しない

---

## Step 0: セッション開始プロトコル（省略禁止）

```
① 目標 $60/day − 現在 $5.97/day = 不足 $54/day
② 現フォーカスレジーム（DOWNTREND）の現状 vs 目標 $60/dt-day
③ [Step 0 D] 目標: $XX/dt-day / 現状: $YY/dt-day / 理論最大: $ZZ/dt-day → 到達可能性: YES/NO
   ※ この1行が出るまで提案・分析を開始しない
③.5 [Step 0 E] 直近タスク期待値合計: $AA/dt-day / 残差: $BB/dt-day
    カバー率 = AA/BB × 100%
    → カバー率 < 50% の場合: 「既存タスクのみでは目標到達不可能。
      新 Priority 設計を直近タスク1として再配置を検討」と明示する
④ 今セッションのタスクを優先順位付きで提示 → STOP
```

レジーム移行条件: 現レジームが目標達成後のみ（DOWNTREND → RANGE → UPTREND）

---

## PMレビュー（オンデマンド）

**起動タイミング**: 「目標に届く気がしない」「方向性が正しいか確信が持てない」「N セッション改善が止まった」と感じたとき。

**起動方法**: ユーザーが「PMレビューして」または `/pm-review` と入力する。

**実行手順**:
1. WORKFLOW.md の現状（Current/Gap/アクティブ Priority 実績）を読む
2. `.claude/pm_review_template.md` のテンプレートに現在値を埋める
3. **Plan タイプのサブエージェント**としてスポーン（コールドスタート・独立評価）
4. 結果を [PM REVIEW] 形式で提示 → ユーザーの判断を待つ

> サブエージェントは実装提案を出さない。方向性判定のみ。

## 監査エージェント（オンデマンド）

**起動タイミング**: 「本当にこの方向で大丈夫か？」「見落としがある気がする」と感じたとき。PM レビュー後に続けて呼ぶことも可。

**起動方法**: ユーザーが「監査して」または `/audit` と入力する。

**実行手順**:
1. WORKFLOW.md の現状と直近の Replay 結果を読む
2. PM レビュー結果が直前にある場合はそれもコンテキストに含める
3. `.claude/auditor_template.md` を読み込み、**統計学・リスク管理・認知バイアス・ソフトウェア工学**の外部基準で評価する（観点は状況に応じて 2〜3 個に絞る）
4. 結果を出力フォーマットで提示 → ユーザーの判断を待つ

> 監査エージェントはコードを書かない・実行しない。外部基準からの指摘のみ。最終判断はまこさん。

---

## 設計思想（絶対不変）

### レジーム切り替え方針（2026-04-21 確定）
- 日足MA70を基準に downtrend / range / uptrend の3レジームに切り替える
- 各レジームに方向性の合う Priority を割り当て、個別に最適化・設計する
- 現状 Priority は「方向性が近いもの」をスタート地点として育てる
- 最終検証: 365d Replay で GO/NO（ここでの再チューニング禁止）

### 実装方針
- 全Priority: 5m足・Priority単位で独立最適化
- ポジションサイズ上限: 0.12 BTC/trade（増加禁止）
- 上限内でのPriority別配分は自由（例: P23=0.06、P3=0.01）
  → 専用パラメータ（P23_POSITION_SIZE_BTC等）を追加して個別設定する
  → エッジの高いPriorityに大きく配分することで$/total-dayを最大化できる
- 複数Priority並立の目的: リスク分散。詰まったら「新Priority追加」であり「サイズ増加」ではない
- 時間帯フィルターは個別Priority最適化では禁止。統合調整フェーズで実施

---

## 改善サイクル

**Step 1. 構造把握**
cat_v9_decider.py（Entry条件）・replay_csv.py（Exit優先順位）・cat_params_v9.json（現在値）を読む。
CSVにmfe_usd/mae_usd/exit_reason/hold_minが揃っているか確認する。

**Step 2. 結果分析**（グリッドサーチ前・省略禁止）

- **0. ポジション構造**: add_count × exit_reason マトリクスを作る。TIME_EXITが構造的コストか・フィルターで削れるかを1文で言語化してからA/Bへ進む
- **A. なぜ負けているか**: exit_reason別 件数/NET/avgMFE。MFEとMAEから損失の性質（即逆行 or 長期漂流）を特定する

  **TIME_EXIT分類（TIME_EXIT削減に着手する前に必須）**:
  TIME_EXITトレードのMFE分布を確認し、TYPE I / II に分類してから対策を決める。
  - TYPE I（MFEが小さい・概ね<$5）: Entry品質問題 → フィルター強化（ATR/ADX/RSI）
  - TYPE II（MFEが大きいが戻った・概ね>$15）: Exit設計問題 → TRAIL/PROFIT_LOCK改善
  - 分類なしのTIME_EXIT削減は失敗する（L-100: 早期EXIT→逆効果）
  採用条件: 「件数削減」ではなく「TIME_EXIT per-trade 平均損失改善 かつ 全体NET改善」で評価する
- **B. なぜ勝てないか**: TIME_EXIT中のMFE/TP比率・TP_FILLEDのMFE余裕を確認。「勝ちを逃している主因」を1文で言語化する
- **C. 総合判断**: A・Bを並べてどちらを先に解決するか決めてから Step 2.5 へ

> 単位ルール: $/regime-day（= Priority NET ÷ 対象レジーム日数）で集計・提示する。$/total-dayは禁止。

**Step 2.5. シグナル理解の言語化**（グリッドサーチ設計前・省略禁止）

① シグナルが「何を捉えているか」を1文で言語化する
② 期待する価格挙動を時間軸で定義する（理想TP・許容・崩壊のそれぞれ何分で解決するか）
③ 「自然な解決時間」と現在のTP幅・TIME_EXITを比較する。乖離が大きければExit全面見直しを優先する
④ 1日の最大発火スロット数（= 24h ÷ avg_hold）と現状件数/dayを比較し、抑圧要因を特定する
→ ユーザーに提示してGO待ち ← STOP

**Step 3. 仮説立案**
損失 vs 成功トレードの指標分布を比較し「その差が損失を説明できるか」を確認する。
候補パラメータの変更効果（件数増減・NET増減）を事前推定する。根拠なしの仮説は出さない。

**Step 3.5. 仮想シミュレーション**（グリッドサーチ前・省略禁止）

results CSV の per-trade 指標（adx_at_entry / atr_14 / rsi_at_entry 等）を pandas でフィルタして NET を瞬時に推定し、有効な軸・範囲を絞り込んでからグリッドサーチを設計する。

```python
p = df[df['priority']==TARGET].copy()
for threshold in candidates:
    filtered = p[p['adx_at_entry'] >= threshold]
    print(threshold, filtered['net_usd'].sum() / DT_DAYS)
```

- add_count=1 のみの Priority は精度高い。add が複数ある Priority は誤差が出る点に注意。
- 改善が見込めない軸・範囲はグリッドから除外してから実行する。
→ 絞り込み結果を提示してGO待ち ← STOP

**Step 4. グリッドサーチ設計・実行**

- データ期間: 対象PriorityのターゲットREGIMEが密集した期間を選ぶ
  - P23(DOWNTREND): 180d（2025-10〜2026-04）/ P4(RANGE)・P24(UPTREND): 別途特定
- Phase 1（方向確認）: 各軸3点（低・中・高）。効かない軸はPhase 2から除外
- Phase 2（絞り込み）: 有効軸のみ・3〜5点・組み合わせ≤15
- OOS検証: グリッド後に365d Replay（regime_switch=ON）で $/regime-day > ベースラインを確認
- 採用基準: ① 365d $/regime-day > ベースライン ② 全体NET改善 ③ per-trade NET > 手数料
- TP変更時は手数料計算を先に実施（L-40）
→ grid_search.py更新後、実行コマンドをユーザーに提示 ← STOP

**Step 5. 結果評価** → 上位パターン比較表・推奨Before/After。未達ならStep 3へ ← STOP

**Step 6. 実装** → diff提示・GO待ち ← STOP

**Step 7. 最終Replay** → コマンド提示 ← STOP

**Step 8. 採用判定** → 「採用しますか？」。打ち切り前に未試行軸（Entry品質/EXIT設計/add戦略/シグナル条件）がないか確認する ← STOP

**Step 9. baseline更新** → $/regime-day表・$/total-day表を更新。目標との残差を再計算する

**Step 10. Gitコミット** → ユーザーの明示OK後のみ ← STOP

---

## 新規Priority設計フロー（P1/P21等・新規追加時）

1. 必要貢献額を逆算してシグナルの最大期待値が届くか確認する（届かなければ設計変更）
2. シグナルエッジをフィルターなし・タイトなTP/SLで先に検証する（勝率60%未満は却下）
3. Entry特性を言語化してからExitをゼロから設計する（既存流用禁止）
4. 実装 → Replay → 必要貢献額を満たすか判定

---

## Priority別ステータス（2026-04-24更新）

| Priority | downtrend/day | range/day | uptrend/day | 状態 |
|---------|--------------|-----------|-------------|------|
| P23-SHORT | **+$21.32/dt-day**（365d OOS・HIGH_ADX filter採用） | +$0.60 | -$3.70 | ✅ 確定（STOCH_REVERSE_EXIT + HIGH_ADX filter） |
| P21-SHORT | **+$7.36/dt-day**（365d OOS・TIME_EXIT_MIN=180採用） | — | — | ✅ 確定（ATR14_MIN=150・TRAIL_EXIT・TIME_EXIT_MIN=180） |
| P2-LONG | **+$2.11/dt-day**（365d OOS・ATR_MIN=100採用） | — | — | ✅ 確定（改善余地なし：L-112, L-111該当・保留） |
| P3-LONG | **-$0.45/dt-day**（365d OOS） | — | — | ⚠️ 微損（ENABLE_P3_LONG=false 設定済・replay は無視） |
| P4-LONG | — | +$0.69/day | — | 🔲 RANGE着手待ち（DT目標達成後） |
| P24-SHORT | — | — | +$0.88/day | 🔲 UPTREND着手待ち |
| P1-LONG | — | — | -$0.36/day | 🔲 UPTREND割り当て済み・要改善 |
| P22-SHORT | -$0.81 | -$1.12 | +$0.12 | ❌ 全レジーム赤字・保留 |

---

## 現在のベースライン（2026-04-24更新）

### PM基準（$/total-day・Step 0専用）

| レジーム | /total-day | 有効Priority |
|---------|-----------|-------------|
| DOWNTREND | +$11.92（365d実測） | P2/P3/P21/P23 |
| RANGE | -$0.41 | P4 |
| UPTREND | +$0.52 | P1/P24 |
| MIXED | +$0.39 | P4 |
| **合計** | **+$11.37** | ※365d regime_switch=ON |

※90d（Jan-Apr 2026）は好況期バイアスあり。365dを正本とする。

### Priority最適化基準（$/regime-day・Step 2〜9専用）

| Priority | 対象レジーム | $/regime-day | データ |
|---------|------------|-------------|-------|
| P23-SHORT | DOWNTREND | **+$21.32（365d OOS・HIGH_ADX filter採用）** | 365d=143dt-day |
| P21-SHORT | DOWNTREND | **+$7.36（365d OOS・TIME_EXIT_MIN=180採用）** | 365d=143dt-day |
| P2-LONG | DOWNTREND | +$2.11（365d OOS・ATR_MIN=100採用） | 365d=143dt-day |
| P3-LONG | DOWNTREND | -$0.45（365d OOS） | 365d=143dt-day |
| **DT合計** | DOWNTREND | **~$30.43/dt-day** | 目標$60まで-$29.57 |
| P4-LONG | RANGE | 未最適化 | — |
| P24-SHORT | UPTREND | 未最適化 | — |

### _REGIME_PRIORITY_SETS（replay_csv.py・2026-04-22修正）

| Priority | DOWNTREND | RANGE | UPTREND | MIXED |
|---------|-----------|-------|---------|-------|
| P1-LONG | ❌ | ❌ | ✅ | ❌ |
| P2-LONG | ✅ | ❌ | ❌ | ❌ |
| P3-LONG | ✅ | ❌ | ❌ | ❌ |
| P4-LONG | ❌ | ✅ | ❌ | ✅ |
| P21-SHORT | ✅ | ❌ | ❌ | ❌ |
| P23-SHORT | ✅ | ❌ | ❌ | ❌ |
| P24-SHORT | ❌ | ❌ | ✅ | ❌ |

---

## 次のアクション（2026-04-24 継続セッション終了時点）

```
【現在フォーカス: DOWNTREND / 合計$60/dt-day目標】
現状: ~$30.43/dt-day / 目標$60 / 残差-$29.57
前セッション改善: +$4.08/dt-day（$26.35→$30.43, +15.5%）
本セッション(継続): ±$0（全提案 REJECT・ロールバック済）

【前セッション 2026-04-24 採用済み】
✅ P21_TIME_EXIT_MIN=180（実効90min）→ P21 $5.95→$7.36/dt-day
✅ P23 HIGH_ADX フィルター → P23 $18.74→$21.32/dt-day

【本セッションの REJECTED 提案（2026-04-24 継続）】
❌ P23 MAX_ADDS 削減（5→3or4）
  - 仮想シミュ: add=4,5 は NET最大貢献源（+$1,860 / 全体61%）
  - 削減は $-1.19〜-$4.14/dt-day。WORKFLOW直近タスク1は却下

❌ P23 A1_STALL 事前エントリーフィルタ
  - A1_STALL 51件-$433 の分離可能性を探索
  - 最良 bb_mid_slope>-20 で +$1.07/dt-day（A1_TP 4件巻き添え）
  - 改善幅が小さくサンプル過少（統計有意性弱）

❌ P23 MFE_STALE_CUT チューニング（B2案）
  - 現行 GATE=$4/HOLD=30 は A1_STALL 51件を完璧に捕捉済み
  - HOLD短縮（20min）の理論上限 +$0.5〜+$1.7/dt-day
  - 優先度低く実行せず

❌ P23 TRAIL_EXIT 追加（L-113 記録）
  - 仮想シミュ予測 +$14.62/dt-day → 実測 -$20.14/dt-day（P23 $21.32→$1.18）
  - TP_FILLED 47件→1件・STOCH_REVERSE_EXIT 41件消滅・avgHold 100→9.5分
  - 原因: デフォルト GATE_PCT=0.05（≈MFE$1で即活性化）が P23 長ホールド型に壊滅的不整合
  - ロールバック済（replay_csv.py の priority list を (1,21) に復元）

❌ P23 MFE_DRAWDOWN_CUT（L-114 記録・PMレビュー後の第2ラウンド）
  - パラメータ: MIN_USD=30 / RATIO=0.3（TP奪取リスクを設計で回避したつもり）
  - 実測 -$10.29/dt-day（P23 $21.32→$11.03）
  - TP_FILLED 47件→40件（-7件）・STOCH_REVERSE_EXIT 41件→26件（-15件）
  - MFE_DRAWDOWN_CUT 33件は NET -$219（avg -$6.6・期待値負）
  - ロールバック済（cat_params_v9.json から 2行削除）

【ratchet型 Exit 全面禁止（L-114 確定）】
  P23 に PROFIT_LOCK / TRAIL_EXIT / MFE_DRAWDOWN_CUT を追加する提案は
  原則禁止。P23 は TP到達までに volatile-path をたどる性質で、ratchet型は
  TP経路の中間 pullback を誤認して発火しTP奪取する。3連敗で構造確定。

【本セッションの保留アイデア（次セッション以降）】
- A1_STALL の per-trade 損失 -$8.48 自体は MFE_STALE_HOLD_MIN 短縮で
  $0.5〜$1.7/dt-day 削れる可能性（非ratchet型・安全）

【直近タスク（優先順位順・非ratchet型のみ）】
1. STOCH_REVERSE_EXIT MFE_GATE 単軸スイープ
   - 現行 P23_STOCH_EXIT_MFE_GATE=20 の周辺 [10, 15, 25, 30]
   - L-109 は MIN_HOLD 軸のみ最適化・MFE_GATE は未探索
   - 期待 +$0.5〜+$2/dt-day（データ不足・実測で判定）

2. P23_STOCH_K_MAX ゲート（Entry強化）
   - decider L474 に実装済みだが params=999.0 で実質無効
   - まず CSV で TP vs TIME_EXIT の stoch_k_at_entry 分布を確認
   - 分布に差があればスイープ

3. P23_TIME_EXIT_DOWN_FACTOR スイープ
   - 現行 SHORT_TIME_EXIT_DOWN_FACTOR=0.5 を継承（実効240min）
   - P22 は 0.4 採用実績あり・P23 独自値は未探索
   - 期待 +$0.3/dt-day（上限 +$1.5）・L-100 通り短縮悪化リスクあり

4. P21 TP_PCT / BB_RATIO 最適化（別Priority・未試行軸）
   - 現行 TP_BB_RATIO=1.0 / TP_MIN_PCT=0.0003
   - 期待 +$1〜$3/dt-day

5. 新 DOWNTREND Priority 設計（ゼロベース）
   - 既存Priority内では $60/dt-day 到達厳しい可能性
   - 新シグナル発見フェーズから
   - ratchet型以外の Exit 設計を前提にする

6. P4-LONG RANGE 改善（DT目標達成後）

【確認済み・変更禁止】
- P23: HIGH_ADX_THRESH=40 / HIGH_ADX_ATR_MIN=200 / STOCH_REVERSE_EXIT(MFE=20/HOLD=150/UNREAL=0)
  → $21.32/dt-day（365d OOS）確定
- P21: ATR14_MIN=150 / TRAIL_EXIT / TIME_EXIT_MIN=180 → $7.36/dt-day（365d OOS）確定
- P2: ATR14_MIN=100 / ATR14_MAX=300 → +$2.11/dt-day（365d OOS）確定
- replay_csv.py: P23 STOCH_REVERSE_EXIT（3f）実装済み
- replay_csv.py: P21 MFE_STALE_CUT（3e）実装済み
- replay_csv.py: TRAIL_EXIT 対象 priority は (1, 21) 維持（P23追加は回帰確認済）
- _REGIME_PRIORITY_SETS: P21→DOWNTREND、P1→UPTREND 追加済み

【PMレビュー知見（2026-04-23）】
- スロット占有制約: 1ポジション保有中は他Priority入れない（シリアル実行）
  → サイズ増加提案前に機会損失計算必須（L-46）
- $60/total-dayは現Priority構造のみでは困難。RANGE/UPTREND改善が将来必要
  → 現フォーカスはDOWNTREND維持（feedback_downtrend_focus）

【本セッションの教訓】
- L-111: PROFIT_LOCK/TRAIL系は TP_FILLED 奪取リスクを必ず事前確認
- L-112: final_mfe は途中時点 MFE の推定に使えない（MFE=単調増加型）
- L-113: TRAIL_EXIT の trail_net ≈ ratio × final_mfe - fee 仮想シミュは ratchet型の動的挙動を
  捉えず大外しする。GATE_PCT は Priority 固有の TP_PCT・avgHold に合わせて設計必須
- L-114: P23 は ratchet型 Exit 全般と構造的不整合。P23 の TP経路は volatile-path で
  中間pullback が正常経路。PROFIT_LOCK/TRAIL/MFE_DRAWDOWN_CUT は全て誤認発火で TP奪取。
  P23 の Exit 改善は非ratchet型（STOCH_REVERSE/MFE_STALE/TIME_EXIT/Entry強化）に限定

【grid_search.py 現在の設定】
- TARGET: P23 TIME_EXIT_MIN グリッド（完了・480維持確定）
- 次: P21 TP_PCT / BB_RATIO グリッド、もしくは P23 TRAIL_EXIT 再設計用
```

---

## Replayコマンド

```bash
# 180d グリッドサーチ用
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/grid_search.py data/BTCUSDT-5m-2025-10-03_04-01_combined_180d.csv

# 90d Replay（regime_switch=ON・全Priority）
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-5m-2026-01-01_04-01_combined_90d.csv --regime

# 365d OOS検証
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-5m-2025-04-01_03-31_365d.csv --regime
```

---

## 確定パラメータ（2026-04-22時点）

| Priority | パラメータ | 値 |
|---------|-----------|-----|
| P2-LONG | P2_TP_PCT | 0.004 |
| P2-LONG | P2_ATR14_MIN / ATR14_MAX | **100.0（採用確定）** / **300.0（採用確定）** |
| P2-LONG | P2_MFE_STALE_GATE_USD / HOLD_MIN | 5.0 / 90.0 |
| P23-SHORT | P23_TP_PCT | 0.012 |
| P23-SHORT | P23_TIME_EXIT_MIN | 480（実効240min via DOWN_FACTOR=0.5） |
| P23-SHORT | P23_ADX_MIN/MAX | 30.0 / 50.0 |
| P23-SHORT | P23_ATR14_MIN | 150.0 |
| P23-SHORT | **P23_HIGH_ADX_THRESH / P23_HIGH_ADX_ATR_MIN** | **40.0 / 200.0（2026-04-24採用）** |
| P23-SHORT | P23_MFE_STALE_GATE_USD / HOLD_MIN | 4.0 / 30.0 |
| P23-SHORT | P23_SHORT_PROFIT_LOCK_ENABLE | 0 |
| P23-SHORT | P23_STOCH_REVERSE_EXIT_ENABLE | true |
| P23-SHORT | P23_STOCH_EXIT_MFE_GATE | 20.0 |
| P23-SHORT | P23_STOCH_EXIT_MIN_HOLD | 150.0 |
| P23-SHORT | P23_STOCH_EXIT_UNREAL_MIN | 0.0 |
| P21-SHORT | P21_TRAIL_RATIO / **P21_TIME_EXIT_MIN** | 0.8 / **180（2026-04-24採用・実効90min）** |
| P21-SHORT | P21_SL_PCT | 0.02 |
| P22-SHORT | P22_TIME_EXIT_DOWN_FACTOR | 0.4 |
| P4-LONG | P4_TP_PCT | 0.003 |
| P4-LONG | P4_ATR14_MAX | 130.0 |
