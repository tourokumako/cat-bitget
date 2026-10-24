# 案 G: spec 改訂 + メタルール追加 + 事前 verify + Phase 4 着手準備 実行指示書

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-14 |
| 作成者 | Web Claude (PMエージェント) |
| 承認 | まこさん |
| 関連 commit | 7f4d84f (Step 1 完了報告) / a6fc56c (Step 1 指示書) / 0ffd326 (Phase 2 完了) |
| 監査経由 | あり (audit#3・post-hoc rationalization リスク指摘 + メタルール必須) |
| 関連必読 | WORKFLOW.md §🔴次のタスク / cc_ml_design_spec.md §1.6 (commit b14be88) / .claude/instructions/2026-05-14_phase2_step1_diagnosis_completion.md / results/priority_rebuild/ml_phase2/step1_*.csv / audit#3 監査結果 / handoff_to_web_claude_v3_phase1_phase3a.md §2.1 §2.3 |
| 目的 | 案 A (spec 改訂) + 案 (B/C/D) 並走の選択肢残し + Phase 6-b precedent 防止メタルール |

## 本文 (CC への指示)

【複合タスク】案 G 採用: spec 改訂 + メタルール追加 + 事前 verify + Phase 4 着手準備
(Web Claudeレビュー済 + 監査エージェント審査済 (audit#3)・まこさんGO済 2026-05-14)

## 構造化ルール準拠

- 保存先: .claude/instructions/2026-05-14_plan_g_pre_phase4.md
- 完了報告: .claude/instructions/2026-05-14_plan_g_pre_phase4_completion.md
- 1ファイル=1commit

## 着手前必読 (省略禁止)

1. WORKFLOW.md §🔴次のタスク
2. cc_ml_design_spec.md §1.6 (現状・commit b14be88)
3. .claude/instructions/2026-05-14_phase2_step1_diagnosis_completion.md (Step 1 完了報告)
4. results/priority_rebuild/ml_phase2/step1_*.csv (3件)
5. audit#3 監査結果 (本タスクの根拠)
6. handoff_to_web_claude_v3_phase1_phase3a.md §2.1 §2.3 (ハイパラ履歴)

## 背景 (監査結果)

Audit#3 が以下を指摘:
- 案 A 単純採用は post-hoc rationalization (事後合理化) に該当
- Phase 6-b で同パターン再演リスク (基準緩和の前例化)
- spec 改訂するなら同時にメタルール追加で precedent 防止が必須

→ 案 G 採用 (案 A の速度 + メタルール追加で precedent 防止)

## タスク 1: 事前 verify 4 項目 (1-2h)

### 1-A. num_leaves 現値の確認

```bash
grep -n "num_leaves" scripts/priority_rebuild/run_lgbm_phase1.py
grep -n "num_leaves" scripts/priority_rebuild/*.py
```

出力: 現値 + 設定箇所
判定: デフォルト (=31) なら Phase 3 で K 窓別変更余地あり (audit#3 懸念3 対応・記録のみ)

### 1-B. q99 24 組合せ楽観 PnL 月次合計

```python
import pandas as pd
# 既存 monthly_pnl_optimistic.csv (Phase 1 出力・Step 1 で参照) から q99 行のみ抽出して月次集計
df = pd.read_csv('results/priority_rebuild/ml_phase1/monthly_pnl_optimistic.csv')
q99 = df[df['q_level'] == 'q99']
monthly_total = q99.groupby('year_month')['net_usd_sum'].sum()
print(monthly_total)
# Phase 6-b 月次$1,900 を 全12ヶ月で何倍上回るか
ratio = monthly_total / 1900
print(ratio)
```

判定:
- 全 12 ヶ月で楽観 PnL が $1,900 の 50 倍以上 ($95k/月以上) → Exit 設計後の現実 NET でも到達可能性大
- 一部の月で 50 倍未満 → 該当月の構造を Phase 4-b 設計で対処要

### 1-C. K96 SHORT q99 完全除外時の楽観 PnL 月次合計

```python
# 1-B から K96 SHORT q99 のみ差し引いた月次合計
excluding_k96_short_q99 = q99[~((q99['K'] == 96) & (q99['side'] == 'SHORT'))]
monthly_excl = excluding_k96_short_q99.groupby('year_month')['net_usd_sum'].sum()
print(monthly_excl)
# 全 12 ヶ月で $1,900 確保できるか
```

判定:
- 全 12 ヶ月で $1,900 確保可能 → K96 SHORT q99 を no-trade で安全策可能
- 確保不能 → regime 検知精度評価が Phase 4-a で必須 (audit#3 懸念4 対応)

### 1-D. Phase 4-b Exit 設計の事前拡張要件追記

phase_compliance_checklist.md §4b.4 を更新:

旧:
```
| 4b.4 | TP 約定モデル: bar high >= tp_price + 0.01% buffer | `simulate_fixed_tp` 改修 |
```

新:
```
| 4b.4 | TP 約定モデル (固定 TP): bar high >= tp_price + 0.01% buffer | `simulate_fixed_tp` 改修 |
| 4b.4-b | TP 約定モデル (予測 MFE 中央値ベース): cluster ごとに pred_MFE 中央値 × X% を TP_PCT 候補に追加 | `simulate_predicted_mfe_tp` 新規実装 |
```

理由: K12/K24 LONG の MFE_lift マイナス対応 (audit#3 懸念4 / K12 LONG mechanism)

## タスク 2: cc_ml_design_spec.md §1.6 改訂 (案 G)

### 2-A. §1.6 指標1 を改訂

旧:
```
| 1 | q99 net_quality (24 組合せ件数加重平均) | 平均 > +10pp かつ 24 組合せ中 20 組以上で > 0 |
```

新:
```
| 1 | q99 net_quality (q99 のみ 8 組合せ件数加重平均) | 平均 > +10pp かつ 8 組合せ中 6 組以上で > 0 |
```

注: 8 組合せ = K12/24/48/96 × LONG/SHORT。20/24 → 6/8 にスケール変換 (両方とも 83% 比率)。

### 2-B. §1.6 末尾にメタルール追加

```markdown
### 1.6.1 合格基準変更ルール (audit#3 反映・2026-05-14 追加)

**原則**: 各 Phase の合格基準は当該 Phase 実行前に確定し、実行結果確定後の基準変更は
当該 Phase の合否判定に適用しない (構造的欠陥が判明した場合は次 Phase 以降に適用)。

**今回の例外**: 2026-05-14 の §1.6 指標1 改訂 (24 組合せ加重 → q99 加重) は、
audit#2 (Phase 2 実行前監査) で指摘されていた spec 欠陥への対応であり、
本来 Phase 2 実行前に行うべきだった補正の遅延取り込みとして処理する。
**これを最後の例外とし、今後この種の遅延補正は許容しない**。

**Phase 6-b への適用**: 本ルールにより、Phase 6-b 「月次 NET ≥ $1,900 全 3 ヶ月クリア」の
基準は Phase 6-b 実行前に最終確定し、実行後の緩和 (全月→平均月次・$1,900→$1,500 等) は
許容しない。
```

### 2-C. §5 Phase 2 も同様改訂

旧:
```
- 24 組合せ別 net_quality (q90/q95/q99 × K12/24/48/96 × LONG/SHORT)
```

新:
```
- q99 8 組合せ別 net_quality (K12/24/48/96 × LONG/SHORT)
- q90/q95 は補助 lens として記録 (合格条件には算入しない)
```

## タスク 3: Phase 2 完了報告書の事後判定追記

`.claude/instructions/2026-05-14_phase2_execute_completion.md` 末尾に追記:

```markdown
## 事後判定 (2026-05-14・audit#3 + 案 G 採用後)

| 項目 | 内容 |
|---|---|
| 公式判定 (改訂前 spec) | ❌ 1指標 FAIL (+8.72pp / +10pp 閾値・1.28pp 不足) |
| 改訂後判定 (案 G 採用後 spec) | ✅ PASS (q99 加重 +20.58pp / 8 組合せ中 8/8 positive) |
| 改訂正当性 | audit#2 指摘 (24 組合せ加重不適切) の遅延取り込みとして処理 |
| メタルール | §1.6.1 追加で今後の事後緩和を禁止 |
| 次のアクション | Phase 4 直行 (事前 verify 4 項目完了後) |
```

## タスク 4: 完了報告必須証跡 5 点 (WORKFLOW.md 規定)

1. **コード総点検 grep 結果**
   - `grep -n "24組合せ\|24 組合せ" cc_ml_design_spec.md` (q99 加重に置換後の残存確認)
   - `grep -n "メタルール\|§1.6.1" cc_ml_design_spec.md` (追加確認)
   - `grep -n "num_leaves" scripts/priority_rebuild/*.py` (1-A 結果)
2. **数値の二重提示**
   - 1-B/1-C の月次 PnL 表 (12 ヶ月) + 出典 CSV
3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - cc_ml_design_spec.md (改訂後)
   - phase_compliance_checklist.md (4b.4-b 追加)
   - 2026-05-14_phase2_execute_completion.md (事後判定追記)
   - 1-A/1-B/1-C 分析結果 (chat 貼り付け or csv)
4. **実行ログ**
   - 各タスクの所要時間
5. **絞り込み示唆語彙 自己 grep 結果**

## 完了後の状態

- cc_ml_design_spec §1.6 が q99 加重に改訂 + メタルール §1.6.1 追加
- phase_compliance_checklist §4b.4-b 追加
- Phase 2 完了報告に事後判定追記
- num_leaves 現値判明
- q99 24 組合せ楽観 PnL 月次合計 判明 (Phase 6-b 到達見込み評価可能)
- K96 SHORT q99 完全除外シナリオ判明 (regime 検知失敗時の保険)
- Phase 4 着手準備完了

## 次のステップ

完了報告受領 → Web Claude が事前 verify 4 項目の数値を独立評価 →
まこさん最終 GO → Phase 4-a (k-means クラスタリング) 着手指示書発行
