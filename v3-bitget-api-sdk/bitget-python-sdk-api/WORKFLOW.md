# WORKFLOW.md — cat-bitget 作業フロー（2026-04-12）

過去実験結果・フェーズ構成・$60/day試算 → [WORKFLOW_ARCHIVE.md](WORKFLOW_ARCHIVE.md)

---

## Claudeの役割定義（最重要）

**ClaudeはPM・PL・SE・プログラマの全役割を担う。**

| 役割 | 担う内容 |
|------|---------|
| PM | 目標（$60/day）に向けた進捗管理・アプローチ見直し判断 |
| PL | 改善サイクルの設計・優先順位決定・リスク評価 |
| SE | コード・ロジック・パラメータの構造把握・仮説立案 |
| プログラマ | 実装・分析・テスト実行 |

**行動原則:**
- 指示を待たず、自分で現状を把握して「次に何をすべきか」を先に提案する
- 「何かおかしい」と感じたら自分で調べて根拠付きで指摘する
- ユーザーが気づく前に問題を発見する
- 仮説はデータで検証してから提示する（検証前の仮説は出さない）
- GOを待つのは「実装・コマンド実行・コミット」のみ。分析・指摘・提案は自律的に行う

---

## セッション開始プロトコル（毎回・例外なく実行）

新しいセッションが始まったら、ユーザーの指示を待たずに以下を実行する:

```
1. WORKFLOW.md を読む → 現在地・次のアクションを把握する
2. 現在地のStepに必要なファイルを読む（コード・CSV・JSONを自律的に判断）
3. 現状を自分でアセスメントして「次にやるべきこと・理由・懸念点」を提案する
```

ユーザーの最初の一言を待ってから動くのではなく、**セッション開始時に自分から状況報告と提案を出す。**

---

## 設計思想（絶対不変）

- タイムフレーム: 1分足
- エントリーシグナル: V9ベース（P2/P4/P22/P23）
- TP幅: Priority単位で設定（P2/P23=スキャル型・現在0.0006で調整中、P4/P22/P24はスイング設計で調整可）
- ポジションサイズ上限: 0.12 BTC/trade
- **各Priorityは独立したミニ戦略として個別に最適化する**

---

## 改善サイクル（1 Priority × 1サイクル）

```
Step 1.  構造把握 & 診断インフラ確認
                          【コード・ロジック把握】
                          cat_v9_decider.py: 対象PriorityのEntry条件・フィルタ・全パラメータの役割
                          replay_csv.py: Exit優先順位・各Exitの発動条件・パラメータ
                          cat_params_v9.json: 現在値の確認

                          【診断インフラ確認（必須）】
                          results CSVの出力項目が以下を満たしているか確認する:
                          □ mfe_usd（最大含み益）
                          □ mae_usd（最大含み損・逆行の深さ）
                          □ stoch_k/d_at_entry（シグナル強度）
                          □ bb_width_at_entry（ボラ幅）
                          □ ret_5（直近モメンタム）
                          □ exit_reason / hold_min / net_usd
                          不足項目があれば先にreplay_csv.pyに追加してReplayを実行する

                          ユーザーに構造サマリーを提示  ← STOP

Step 2.  結果分析        — results/replay_*.csv から対象Priorityの実数を取る
                          exit_reason別: 件数・NET・avg損益
                          損失トレードのentry指標値（ADX・ATR・slope等）
                          ユーザーに結果サマリーを提示  ← STOP

Step 3.  仮説立案        — 構造 × 結果を照合して原因候補を特定し、必ずデータで根拠を確認する
                          ① 損失 vs 成功トレードの指標分布を比較する
                          ② 「差がある」だけでなく「その差が損失を説明できるか」を確認する
                             （価格が逆行したのか・TPに届かなかったのか・どちらが何件か）
                          ③ 候補パラメータを変えた場合の効果を事前推定する
                             （STALE削減件数 vs TP削減件数を計算してNET改善を試算）
                          ④ NET改善が見込める場合のみ仮説として採用する
                          根拠・推定効果なしの仮説は提示しない
                          仮説・根拠・推定効果をセットでユーザーに提示  ← STOP

Step 4.  グリッドサーチ設計
                          仮説に直結するパラメータ × 探索範囲を決める
                          TP_PCT変更時は手数料計算を先に実施（L-40）
                          他Priorityへの影響を確認する
                          採用基準: スキャル型 NET≥$0・TP率≥90%、スイング型 NET≥$0・TP率≥65%
                          grid_search.py更新後、実行コマンドをユーザーに提示  ← STOP

Step 5.  グリッドサーチ結果評価
                          ① 上位パターンの比較表
                          ② 推奨パラメータ（Before / After）
                          ③ 採用基準未達の場合 → 仮説を見直してStep 3へ戻る  ← STOP

Step 6.  実装            — パラメータ変更はStep 5承認後に直接適用
                          コード変更はdiffを提示してGO待ち  ← STOP

Step 7.  最終Replay      — Replayコマンドをユーザーに提示  ← STOP

Step 8.  採用判定        — 全項目チェック後「採用しますか？」← STOP
                          未達の場合 → Step 3へ戻り仮説見直し

Step 9.  baseline更新    — 採用時のみ更新
                          目標達成可能性チェック（毎回出力）:
                            現在X件/day → 目標20件/day
                            現在$Z/day → 目標+$60/day
                            構造的に届かない場合 → アプローチ見直しをユーザーに提案する

Step 10. Gitコミット     — ユーザーの明示OK後のみ  ← STOP
```

> **STOPルール**: 実装・コマンド実行・コミットは必ずユーザーのGO後に行う。
> 分析・指摘・提案は自律的に行う。

---

## Priority別ステータス（毎サイクル更新）

| Priority | 型 | 現在フェーズ | 未解決問題 | ゴール |
|---------|-----|------------|---------|-------|
| P2-LONG | スキャル | Step 3（stoch_kフィルタ検討中） | MFE_STALE 5件/-$195、TIME_EXIT 1件/-$45 | NET≥$100/90d, TP率≥97% |
| P23-SHORT | スキャル | ✅完了 | MFE_STALE 3件/-$62（残存） | NET≥$0 ✅($+24.56), TP率≥90% ✅(98%) |
| P22-SHORT | 中スイング | Step 1待ち | RSI_REVERSE 5件/-$74 | NET≥$0, TP率≥65% |
| P4-LONG | スイング | 保留 | TIME_EXIT 12件/-$165 | NET≥$0✅, TP率≥65%✅ |
| P24-SHORT | 中スイング候補 | 未着手 | 不明 | 有効化後: NET≥$0, TP率≥90% |

---

## 現在地: P2 Step 3（stoch_k フィルタ仮説）

**このセッションで確定した変更（2026-04-13）:**

| 変更内容 | Before | After |
|---------|--------|-------|
| P23_ATR14_MIN | 80.0 | **115.0** |
| P23_MFE_STALE_HOLD_MIN | （新規追加） | **90.0** |
| P2_MFE_STALE_GATE_USD | 5.0 | **0.5** |
| P2_MFE_STALE_HOLD_MIN | （新規追加） | **90.0** |
| replay_csv.py | 診断フィールド追加 | mfe_usd/mae_usd/tp_diff_usd/stoch_k_d/bb_width |
| replay_csv.py | サマリー3セクション追加 | MFE_STALE詳細/Priority別指標比較/Priority別時間帯 |

**P2 残課題（次セッション）:**
- MFE_STALE 5件（全件 avgMFE=$0.00、avgMAE=-$46.48）
- TP vs STALE で stoch_k 差 **-23.62**（TP=64.77 vs STALE=41.15）← 強い指標差
- ret_5 差 **-0.15**（TP=+0.02% vs STALE=-0.14%）
- 仮説: `P2_STOCH_K_MIN` パラメータ追加（現在未存在）でSTALE 3-4件除外可能性

**次のアクション:**
1. cat_v9_decider.py の P2 Entry条件を確認（P2_STOCH_K_MIN が追加可能か）
2. stoch_k < 45 の TP取引件数を確認（除外コスト計算）
3. グリッドサーチ設計・実行

---

## Priority別 確定パラメータ（2026-04-13時点）

| Priority | パラメータ | 値 | 備考 |
|---------|-----------|-----|------|
| P2-LONG | P2_POSITION_SIZE_BTC | 0.06 | ✅採用 |
| P2-LONG | P2_TP_PCT | 0.0006 | 調整中 |
| P2-LONG | MAX_ADDS_BY_PRIORITY.2 | 1 | 採用済み |
| P2-LONG | P2_ATR14_MIN | 80.0 | 採用済み |
| P2-LONG | P2_ATR14_MAX | 120.0 | 採用済み |
| P2-LONG | P2_MFE_STALE_GATE_USD | **0.5** | ✅2026-04-13更新 |
| P2-LONG | P2_MFE_STALE_HOLD_MIN | **90.0** | ✅2026-04-13追加 |
| P2-LONG | P2_TIME_EXIT_MIN | 480 | 採用済み |
| P2-LONG | P2_ADX_EXCL_MAX | 200.0 | 採用済み |
| P23-SHORT | SHORT_POSITION_SIZE_BTC | 0.024 | 未スケール |
| P23-SHORT | P23_TP_PCT | 0.0006 | 調整中 |
| P23-SHORT | P23_ATR14_MIN | **115.0** | ✅2026-04-13更新 |
| P23-SHORT | P23_MFE_STALE_GATE_USD | 4.0 | 採用済み |
| P23-SHORT | P23_MFE_STALE_HOLD_MIN | **90.0** | ✅2026-04-13追加 |
| P4-LONG | P4_TP_PCT | 0.003 | ✅採用 |
| P4-LONG | P4_TIME_EXIT_DOWN_FACTOR | 1.0 | ✅採用 |
| P4-LONG | LONG_POSITION_SIZE_BTC | 0.024 | 未スケール |
| P4-LONG | P4_ATR14_MAX | 130.0 | 採用済み |

---

## 現在のベースライン（2026-04-13）

| Priority | 件数/90d | NET | TP率 | 主な損失 |
|---------|---------|-----|------|---------|
| P2-LONG | 188 | **+$89** | **97%** | MFE_STALE 5件/-$195、TIME_EXIT 1件/-$45 |
| P4-LONG | 46 | +$20 | 74% | TIME_EXIT 12件/-$165 |
| P22-SHORT | 98 | -$17 | 94% | RSI_REVERSE 5件/-$74 |
| P23-SHORT | 122 | **+$25** | **98%** | MFE_STALE 3件/-$62 |
| **全体** | **454件（5.0件/day）** | **+$116.27/+$1.3/day** | | |

---

## Replayコマンド

```bash
# 90日（メイン検証）
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-1m-binance-2026-04-06_90d.csv

# 180日（過学習チェック用）
echo "=====🚀 RUN START $(date) =====" && \
cd /Users/tachiharamasako/Documents/GitHub/cat-bitget/v3-bitget-api-sdk/bitget-python-sdk-api && \
python3 runner/replay_csv.py data/BTCUSDT-1m-binance-2026-04-06_180d.csv
```
