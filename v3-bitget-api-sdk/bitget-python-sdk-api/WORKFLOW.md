# WORKFLOW.md — cat-bitget 改善フロー（2026-04-11 改訂）

---

## 作業手順（必ず順番通りに実行）

```
Step 1.   現状把握       — baseline Replay を実行し result CSV を取得する
Step 2.   集計分析       — exit reason 別・priority 別・LONG/SHORT 別に数値把握する
Step 2.5. 個別分析       — 損失トレードの市場状況・インジケータ値・価格推移を直接確認する
                          （集計統計だけからの提案は禁止）
Step 3.   改善案提示     — Step 2.5 の共通パターンを根拠として仮説を立てる
                          複数案はスコアリングして最優先の1つだけ提案する
                          「この変更で何件が影響を受けるか」を事前に計算して明示する
Step 4.   ユーザー承認   — GO サインが出るまでコード・パラメータを変更しない  ← STOP
Step 5.   最小差分修正   — 1つの仮説に基づく最小変更のみ実施する
Step 6.   Replay実行     — 90日データで実行し、結果を提示する  ← STOP
Step 7.   回帰確認       — 下記評価観点を全項目チェックし「採用しますか？」と確認する  ← STOP
Step 8.   lessons 更新   — 想定外の結果・禁止パターン発見時に lessons.md を更新する
Step 9.   baseline 更新  — 採用時のみ WORKFLOW.md のbaseline数値を更新する
Step 10.  Git コミット   — ユーザーの明示的な OK が出てからコミットする  ← STOP
```

> **STOP のルール**: 各 ← STOP では必ずユーザーに結果を提示し、
> 明示的な承認（"GO" / "OK" / "採用" 等）を得てから次に進む。
> 曖昧な返答・質問への回答は GO ではない。

---

## 改善案スコアリング基準（Step 3 で使用）

複数の改善案があるとき、以下で優先順位をつけて最高スコアの1つだけ提案する。

| 軸 | 高評価 | 低評価 |
|----|--------|--------|
| 損失インパクト | 対象 exit の NET 損失が大きい | 小さい |
| 影響範囲 | 他 exit / priority への波及が少ない | 波及が多い（スロット連鎖） |
| 根拠の強さ | 個別分析で共通パターンを確認済み | 集計だけで推測 |
| 検証可能性 | CSVシミュレーションで事前計算できる | できない |

仮説は `analysis/hypothesis_log.md` に記録し、採用しなかったアイデアも捨てない。

---

## 評価観点（Step 7 で毎回全項目チェック）

| 指標 | 確認内容 |
|------|----------|
| NET/day | 改善前後の比較 |
| TP率 | 全体・Priority別 ≥ 90% を維持しているか |
| トレード件数 | 極端に減っていないか（±20%以内を目安） |
| exit reason 別損益 | TP / MFE_STALE / TIME_EXIT / RSI_REVERSE / SL の内訳 |
| Priority 別損益 | P2/P4/P22/P23 ごとの NET 変化 |
| LONG / SHORT 別損益 | 片側改善が反対側を壊していないか（スロット連鎖に注意） |
| MFE_STALE 件数・損失 | 改善方向か |
| TIME_EXIT 件数・損失 | 改善方向か |

---

## lessons.md 更新ルール（Step 8）

| 状況 | アクション |
|------|-----------|
| バックテストで悪化した | 必ず書く |
| 想定外の結果が出た（改善・悪化問わず） | 書く |
| 禁止すべきパターンを発見した | 書く |
| 改善・悪化なし / 想定通り | 書かなくていい |

---

## $60/day 達成の数学（設計前提）

**上限: 合計ポジションサイズ ≤ 0.12 BTC/trade（組み合わせ自由）**

```
ポジションサイズ別 NET/TP（add=1、手数料後）:
  0.024 BTC → $0.64/TP    0.12 BTC → $3.19/TP ← 上限フル活用

件数別 NET/day 上限（損失ゼロの理想値）:
              9件/day   15件/day   20件/day
0.024 BTC     $5        $9         $12
0.12 BTC      $27       $45        $61 ← $60/day達成ライン

最短ルート: 0.12 BTC × add=1 × 20件/day = $61/day
ただし損失もスケール → 品質改善が先決
```

---

## フェーズ構成

### Phase 1: 品質基盤（現在地）
```
目標: add=1でNET≥+$1/day、TP率≥93%、MFE_STALE≤10件/90d
方法: Step 1〜10 を繰り返して損失を削る
対象損失源:
  P2  MFE_STALE: -$363/90d ← 最優先
  P23 MFE_STALE: -$200/90d ← 次点
  P4  TIME_EXIT:  -$85/90d ← 三番目
```

### Phase 2: 件数最大化
```
目標: 15件/day 以上、TP率≥90%維持
Phase 1 完了後に着手
```

### Phase 3: サイズスケール（〜0.12 BTC上限）
```
最短ルート:
  0.024 BTC 黒字確認 → 0.06 BTC テスト → 0.12 BTC テスト
各ステップで90日Replay + 180日過学習チェック必須
```

### Phase 4: 本番投入
```
Replay黒字 → 少額実弾 → 2週間監視 → スケール
```

---

## 現在地: Phase 1 / Step 2.5（P2 MFE_STALE 残13件 → 次の改善へ）

**確定パラメータ（変更禁止）**

| パラメータ | 値 | 備考 |
|-----------|-----|------|
| LONG_TP_PCT / SHORT_TP_PCT | 0.0006 | 固定 |
| LONG/SHORT_MAX_ADDS | 1 | Phase 1固定 |
| P2_ATR14_MIN | 80.0 | 確定 |
| P23_ATR14_MIN | 80.0 | 確定 |
| P4_ATR14_MAX | 130.0 | 確定 |
| P2_MFE_STALE_GATE_USD | 5.0 | 確定 |
| P23_MFE_STALE_GATE_USD | 4.0 | 確定 |
| P2_TIME_EXIT_MIN | 480 | 固定（短縮は逆効果と確認済み） |
| P2_ADX_EXCL_MAX | 200.0 | 確定（ADX>50のMFE率高い） |

---

## add=1ベースライン（2026-04-12 更新）

| 項目 | 値 |
|------|-----|
| データ | 1m足 90日（2026-01-06〜2026-04-06） |
| 総トレード数 | 747件（8.3件/day） |
| NET | **-$156 / -$1.73/day** |
| TP率 | **94.2%** |
| MFE_STALE_CUT | 25件 / -$477 |
| TIME_EXIT | 9件 / -$89 |
| SL_FILLED | 0件 |

### Priority別
| Priority | 件数/90d | NET | TP率 | 主な損失 |
|---------|---------|-----|------|---------|
| P2-LONG | 355 | -$30 | 96% | MFE_STALE -$277 |
| P4-LONG | 51 | -$56 | 84% | TIME_EXIT -$85 |
| P22-SHORT | 98 | -$17 | 94% | TIME_EXIT -$5 |
| P23-SHORT | 243 | -$54 | 93% | MFE_STALE -$200 |

### 変更履歴
| 変更 | 効果 |
|------|------|
| P2_ADX_EXCL_MAX: 50→200（2026-04-12） | P2 MFE_STALE 20→13件、NET +$0.48/day |

---

## Replay コマンド

```bash
# 90日（Phase 1〜2 メイン検証）
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-1m-binance-2026-04-06_90d.csv

# 180日（Phase 3 過学習チェック用）
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-1m-binance-2026-04-06_180d.csv
```

出力CSV: `results/replay_BTCUSDT-1m-binance-2026-04-06_{90d|180d}.csv`

---

## 過去の確定改善（参考）

| 変更 | 効果 |
|------|------|
| P2_ATR14_MIN: 30→80 | +$6.0/day |
| P23_ATR14_MIN: 30→80 | +$2.2/day |
| P4_ATR14_MAX: なし→130 | +$1.3/day |
| MAX_ADDS: 5→1 | SL消滅・構造安定 |
| P2_ADX_EXCL_MAX: 50→200 | +$0.48/day、P2 MFE_STALE 20→13件 |

---

## V9最終結果（アーカイブ）

| 項目 | 値 |
|------|-----|
| 90日NET | +$20.3/day |
| 180日NET | +$5.3/day（急騰レジームで崩壊） |
| 失敗原因 | addナンピン+広いTPでスイング化。設計上の天井あり |
| 本番投入 | **未実施・達成不可** |
