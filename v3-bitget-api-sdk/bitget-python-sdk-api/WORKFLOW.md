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

## Priority別ステータス（2026-04-23更新）

| Priority | downtrend/day | range/day | uptrend/day | 状態 |
|---------|--------------|-----------|-------------|------|
| P23-SHORT | **+$18.74/dt-day**（365d OOS・STOCH_REVERSE_EXIT採用） | +$0.60 | -$3.70 | ✅ 確定（STOCH_REVERSE_EXIT MFE=20/HOLD=150） |
| P21-SHORT | **+$5.90/dt-day**（365d OOS） | — | — | ✅ 確定（ATR14_MIN=150・TRAIL_EXIT） |
| P2-LONG | **+$2.11/dt-day**（365d OOS・ATR_MIN=100採用） | — | — | ✅ 確定（P2_ATR14_MIN=100・ATR14_MAX=300） |
| P3-LONG | **-$0.43/dt-day**（365d OOS） | — | — | ⚠️ 微損（SL_FILLED 10件$-317が主因） |
| P4-LONG | — | +$0.69/day | — | 🔲 RANGE着手待ち（DT目標達成後） |
| P24-SHORT | — | — | +$0.88/day | 🔲 UPTREND着手待ち |
| P1-LONG | — | — | -$0.36/day | 🔲 UPTREND割り当て済み・要改善 |
| P22-SHORT | -$0.81 | -$1.12 | +$0.12 | ❌ 全レジーム赤字・保留 |

---

## 現在のベースライン（2026-04-23更新）

### PM基準（$/total-day・Step 0専用）

| レジーム | /total-day | 有効Priority |
|---------|-----------|-------------|
| DOWNTREND | +$9.79（365d実測） | P2/P3/P21/P23 |
| RANGE | -$0.41 | P4 |
| UPTREND | +$0.52 | P1/P24 |
| MIXED | +$0.39 | P4 |
| **合計** | **+$10.29** | ※365d regime_switch=ON |

※90d（Jan-Apr 2026）は好況期バイアスあり。365dを正本とする。

### Priority最適化基準（$/regime-day・Step 2〜9専用）

| Priority | 対象レジーム | $/regime-day | データ |
|---------|------------|-------------|-------|
| P23-SHORT | DOWNTREND | **+$18.74（365d OOS・STOCH_REVERSE_EXIT採用）** | 365d=143dt-day |
| P21-SHORT | DOWNTREND | +$5.90（365d OOS） | 365d=143dt-day |
| P2-LONG | DOWNTREND | **+$2.11（365d OOS・ATR_MIN=100採用）** | 365d=143dt-day |
| P3-LONG | DOWNTREND | -$0.43（365d OOS） | 365d=143dt-day |
| **DT合計** | DOWNTREND | **~$26.35/dt-day** | 目標$60まで-$33.65 |
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

## 次のアクション（2026-04-23 セッション終了時点）

```
【現在フォーカス: DOWNTREND / 合計$60/dt-day目標】
現状: ~$26.35/dt-day / 目標$60 / 残差-$33.65

【P23 最適化 - 完了済み】
✅ STOCH_REVERSE_EXIT 採用確定（2026-04-23）
  - パラメータ: MFE_GATE=20 / MIN_HOLD=150 / UNREAL_MIN=0 / ENABLE=true
  - 365d OOS: $18.74/dt-day・STOCH_REVERSE_EXIT 48件 $+1730（avg $+36/trade）

【P2-LONG 最適化 - 完了済み（2026-04-23）】
✅ P2_ATR14_MIN=100 採用確定（ATR14_MAX=300は前回採用済み）
  - Phase 1 グリッド（ADX_MAX×ATR_MIN 9パターン）: ATR_MIN=100・ADX_MAX=999が最強
  - ADX_MAXフィルター: 効果なし（ADX_MAX=999=制限なしが常に最強）
  - 180d grid: ATR_MIN=100 = +$3.49/day（rank1）
  - 365d OOS: ATR_MIN=100 = +$2.11/dt-day / ベースライン+$1.08から+$1.03改善
  試行済み（REJECTED）: ADX_MIN引き上げ（33/35/37/40・全逆効果）/ RSI_MIN引き上げ / ADX_MAX追加
  Phase 2候補（将来）: add_count制限（仮想sim+$0.56・小さいため後回し）

【直近タスク（優先順位順）】
1. P3-LONG 改善（-$0.45/dt-day・要因: SL_FILLED 10件$-317）
   - SL設定（P3_SL_PCT=0.015）が厳しすぎる可能性
   - ATR avg=327（TIME_EXIT）・ATR_MAX追加が有効か検討
   ※ まずStep 2（結果分析）を実施してから設計する

2. P21 追加改善（P3完了後）
   - $5.95/dt-day（365d OOS）/ TIME_EXIT 30件（avgADX=26.2）残存

3. P2 Phase 2（P3/P21完了後）
   - add_count制限（仮想sim+$0.56）

【確認済み・変更禁止】
- P23: STOCH_REVERSE_EXIT(MFE=20/HOLD=150/UNREAL=0) / TP=0.012/ADX_MAX=50/DF=0.5
  → $18.74/dt-day（365d OOS）確定
- P21: ATR14_MIN=150 / TRAIL_EXIT / TIME_EXIT_MIN=120 → $5.95/dt-day（365d OOS）確定
- P2: ATR14_MIN=100 / ATR14_MAX=300 → +$2.11/dt-day（365d OOS）確定
- replay_csv.py: P23 STOCH_REVERSE_EXIT（3f）実装済み
- replay_csv.py: P21 MFE_STALE_CUT（3e）実装済み
- _REGIME_PRIORITY_SETS: P21→DOWNTREND、P1→UPTREND 追加済み

【PMレビュー知見（2026-04-23）】
- スロット占有制約: 1ポジション保有中は他Priority入れない（シリアル実行）
  → サイズ増加提案前に機会損失計算必須（L-46）
- $60/total-dayは現Priority構造のみでは困難。RANGE/UPTREND改善が将来必要
  → 現フォーカスはDOWNTREND維持

【grid_search.py 現在の設定】
- TARGET: P2 Phase 1完了（ATR_MIN=100採用・次はP3用に変更予定）
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
| P23-SHORT | P23_MFE_STALE_GATE_USD / HOLD_MIN | 4.0 / 30.0 |
| P23-SHORT | P23_SHORT_PROFIT_LOCK_ENABLE | 0 |
| P23-SHORT | P23_STOCH_REVERSE_EXIT_ENABLE | true |
| P23-SHORT | P23_STOCH_EXIT_MFE_GATE | 20.0 |
| P23-SHORT | P23_STOCH_EXIT_MIN_HOLD | 150.0 |
| P23-SHORT | P23_STOCH_EXIT_UNREAL_MIN | 0.0 |
| P21-SHORT | P21_TRAIL_RATIO / TIME_EXIT_MIN | 0.8 / 120 |
| P21-SHORT | P21_SL_PCT | 0.02 |
| P22-SHORT | P22_TIME_EXIT_DOWN_FACTOR | 0.4 |
| P4-LONG | P4_TP_PCT | 0.003 |
| P4-LONG | P4_ATR14_MAX | 130.0 |
