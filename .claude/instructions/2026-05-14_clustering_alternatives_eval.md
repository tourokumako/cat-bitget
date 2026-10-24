# 【タスク】clustering 廃止後の設計選択肢 評価 (選択肢 4-7・既存データ試算)

(監査#6 審査済・Web Claude レビュー済・まこさん GO 済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_clustering_alternatives_eval.md
- 完了報告: .claude/instructions/2026-05-14_clustering_alternatives_eval_completion.md

## 着手前必読 (省略禁止・L-179/L-180/L-181)

1. WORKFLOW.md §🔴次のタスク
2. phase_compliance_checklist.md §4a / §4b 全項目
3. cc_ml_design_spec.md §3 Exit 設計 / §4b.4-b
4. .claude/instructions/2026-05-14_phase4a_normalize_reselect_completion.md (正規化完了報告)
5. results/priority_rebuild/leak_incident_20260513.md (背景)

## Step 0-1: 必読ファイル引用 (読んだフリ防止)

a. phase_compliance_checklist.md §4b.1〜4b.7 + §4a.5 全文貼り付け
b. 正規化完了報告の cluster_movement_match.csv 全数値引用
c. cc_ml_design_spec.md §4b.4-b 全文貼り付け

各引用が期待値と一致しない/省略 → STOP

## 背景 (監査#6 結果)

監査#6 が以下を確定:

- clustering 廃止の判断自体は statistically 支持される (LONG cluster 反転 1.2%/16.4% は致命的)
- ただし「廃止 → per-entry 直行」は早計
- **重要な非対称性**: SHORT q99 は cluster 安定 (K12 98% / K96 100%)・LONG q99 のみ崩壊
- CC + Web Claude はこの非対称性を見落とし「全廃 (選択肢 1)」で一致していた

→ 選択肢 4-7 を既存データで評価してから設計方針を確定する。

## 評価対象の選択肢 (監査#6 提示)

| 選択肢 | 概要 | clustering との関係 |
|---|---|---|
| 1 (参考) | 全 per-entry prediction-based Exit | clustering 全廃 |
| 4 | (K × side) ごとに 1 Exit = 8 組合せ | clustering なし・per-entry より粗い |
| 5 | (K × side × q-level) ごとに 1 Exit = 24 組合せ | q90/q95/q99 を natural classifier に |
| 6 | ATR バケット (low/mid/high vol) × (K × side) | contemporaneous ATR で同時刻 regime 判定 |
| **7 (監査本命)** | SHORT は k=2 clustering 継続・LONG は per-entry | 非対称設計・データ非対称性に対応 |

## Step 1: 各選択肢の組合せ数とサンプル数 試算

既存データ (predictions_train_normalized.parquet・predictions_test2025_normalized.parquet・
ml_phase4_a_norm の cluster ラベル) を使い、各選択肢で:

### 1-A. 組合せ数の確定

| 選択肢 | 組合せ数の内訳 |
|---|---|
| 4 | K(4) × side(2) = 8 |
| 5 | K(4) × side(2) × q-level(3) = 24 |
| 6 | ATR bucket(3) × K(4) × side(2) = 24 |
| 7 | SHORT: 2 cluster × K(4) = 8 + LONG: K(4) × per-entry = 4 関数 = 計 12 |

### 1-B. 各組合せの train サンプル数

各選択肢の各組合せについて、train (2021-2024) の q99 fire 件数を集計。
**監査#2 基準で判定**:

- ≥ 100 件: 統計的有意
- 30〜99 件: 仮説レベル (⚠️)
- < 30 件: 根拠不足 (❌)

少数組合せ (< 100) がいくつあるかを選択肢別にカウント。

### 1-C. 各組合せの train→test サンプル数変化

選択肢 4/5/6 については、train で定義したグループに test 足が何件入るか。
選択肢 7 については、SHORT 側 cluster の train→test 一致率 (既知: K12 98%/K96 100% だが
q90/q95 含めて再確認)。

## Step 2: 選択肢 7 の SHORT clustering 詳細検証 (監査#6 本命)

選択肢 7 が本命なので SHORT 側 clustering の安定性を厳密確認:

### 2-A. SHORT q90/q95/q99 全ての cluster 一致率

cluster_movement_match.csv は q99 のみ。q90/q95 でも SHORT cluster が安定か確認。

### 2-B. SHORT 側 k=2 cluster の train/test share

SHORT 足だけを対象に k=2 clustering したときの train/test share 乖離。
(現状の k=2 は LONG/SHORT 混在で fit している・SHORT 単独で fit し直すと安定性が変わる可能性)

### 2-C. SHORT 単独 k 再選定

SHORT 足だけで k=2,3,4 を試し、SHORT に最適な k を確認。

## Step 3: LONG per-entry の技術的成立性 verify (監査#6 懸念 3)

選択肢 7 の LONG 側 = per-entry。これが実装可能な spec まで落とせるか:

### 3-A. per-entry Exit パラメータ計算ロジックの定義可否

- TP_PCT(entry) = f(pred_MFE, pred_MAE, ...) の f を具体的に定義できるか
- SL の決め方 (per-entry で SL を使うか・使うならどう決めるか)
- time exit (K 固定か・予測に応じて動的か)
- 予測 MFE が極小の entry での floor 設定

### 3-B. K12 LONG MFE_lift マイナス問題の per-entry での扱い

audit#3 で発見された K12 LONG の MFE_lift マイナス問題が per-entry でどうなるか。
(cluster 平均で隠れていた問題が個別 entry で露出する可能性・監査#6 懸念 3)

## Step 4: 2025-01/09 暴騰局面の影響分析 (監査#6 見落とし A)

LONG cluster 反転 (K12_LONG 1.2% / K96_LONG 16.4%) が
2025-01 / 2025-09 の暴騰局面に集中しているか月別に確認。

- 集中している → regime gate での対処も選択肢になる
- 分散している → 構造的問題・per-entry or 非対称設計が必要

## Step 5: 各選択肢の比較表 + 推奨

| 評価軸 | 選択肢 1 | 選択肢 4 | 選択肢 5 | 選択肢 6 | 選択肢 7 |
|---|---|---|---|---|---|
| 組合せ数 | - | 8 | 24 | 24 | 12 |
| 少数組合せ (<100) 数 | - | XX | XX | XX | XX |
| train/test 安定性 | - | XX | XX | XX | XX |
| SHORT 側の clustering 活用 | なし | なし | なし | なし | あり |
| LONG cluster 反転問題の回避 | ✅ | ✅ | ✅ | ? | ✅ |
| 実装可能な spec まで落とせるか | 懸念 3 | XX | XX | XX | XX |
| Phase 4-b spec 改訂の規模 | 大 | 中 | 中 | 中 | 中 |

CC 推奨を data-driven で 1 つ提示 (CC 主観なし)。

## 監査#6 全項目 対応マッピング (取りこぼし防止)

| 監査項目 | 本タスクでの対応 |
|---|---|
| 懸念 1 (廃止判断は支持) | 前提として受容済 |
| 懸念 2 (中間選択肢未検討) | 本タスク全体 (選択肢 4-7 評価) |
| 懸念 3 (per-entry 技術成立性) | Step 3 |
| 懸念 4 (形式上 vs 実用上 二重判定) | 完了報告で結論一本化 (二重判定しない) |
| 懸念 5 (Web Claude 独立性) | Web Claude 側手順 (下記) |
| 懸念 6 (outlier rate=0 誤読) | Step 2-B で「安全性」と「機能性」を別軸記載 |
| 懸念 7 (§4b spec 改訂未定義) | Step 5 で各選択肢の spec 改訂規模を明示 |
| 見落とし A (暴騰局面集中) | Step 4 |
| 見落とし B (silhouette 用法) | Step 2 で silhouette を主指標にしない |
| 見落とし C (正規化方法の選択肢) | Step 2-B で % 換算以外も検討余地として記載 |
| 見落とし D (k=2 勝因は test 単一化) | Step 5 比較表に注記 |
| 見落とし E (cluster 1 月別分布) | Step 4 と統合 |
| 見落とし F (refit 影響) | Step 3-B |
| 見落とし G (per-entry 運用負荷) | Step 5 比較表に「Phase 7 運用負荷」列追加 |
| 見落とし H (廃止 vs Phase 4-a 廃止の区別) | 完了報告でスコープ境界明示 |
| 見落とし I (Phase 5 影響範囲) | Step 5 で Phase 5-d/5-e への影響記載 |
| 見落とし J (Phase 6-b 到達確率) | 完了報告で「現時点で到達確率は予測困難」と明記 |
| 見落とし K (2025 regime drift 根本原因) | Step 4 と統合・BTC 価格/ボラ要因を記載 |
| 見落とし L (Phase 4-a 完全スキップ) | 選択肢 4-6 が該当・Step 1-5 で評価 |

## 物理証跡

1. 入力ファイル整合性 (正規化版 predictions の sha256)
2. 試算プロセス (各選択肢の組合せ数・サンプル数の集計過程)
3. 出力ファイル証跡 (比較表 CSV の sha256)
4. 第三者再計算検証 (1 選択肢のサンプル数を独立再集計で一致確認)
5. データ sanity (集計対象の行数・null 率)
6. stderr / Python warning 全件
7. 同コマンド bit-exact 再現性確認
8. 監査#6 全項目マッピングの各項目が完了報告で言及されているか

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果** (新規分析スクリプトの絞り込み示唆語彙)
2. **数値の二重提示** (Step 5 比較表 + 出典 CSV)
3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - 選択肢比較表 CSV
   - SHORT clustering 詳細検証結果
   - per-entry 技術成立性レポート
4. **実行ログ** (所要・終了コード・Python warnings 全件)
5. **絞り込み示唆語彙 自己 grep 結果** (no matches 含む)

## 完了後の状態

- 選択肢 1/4/5/6/7 の組合せ数・サンプル数・安定性が比較済
- 選択肢 7 (監査本命) の SHORT clustering 安定性が厳密確認済
- LONG per-entry の技術的成立性が判明
- 2025-01/09 暴騰局面の影響が判明
- 設計方針 (どの選択肢を採用するか) の判断材料が揃う

## 次のステップ

完了報告受領 → Web Claude が独立評価 → まこさん最終 GO で選択肢確定 →
確定選択肢に応じた Phase 4-b 指示書 / §4b spec 改訂

## Web Claude 独立評価の手順 (監査#6 懸念 5 対応・強化版)

監査#6 で「CC 完了報告を見ないだけでは独立性が確保できない・Web Claude が独自再計算すべき」
と指摘された。次の完了報告では:

- Web Claude は CC 完了報告の数値表を読む前に、生 CSV から自分で集計を再実行する
  (例: 各選択肢のサンプル数を Web Claude が独自に数え直す)
- 独自集計と CC 集計を差分照合
- ただし監査#6 が「procedural fix では構造的に解決しない可能性」も指摘しているため、
  重大判断は引き続き監査経路を通すことを前提とする
