# Phase 4-a 着手前 追加対応 4 項目 (案 G 残務処理)

| 項目 | 値 |
|---|---|
| 発行日 | 2026-05-14 |
| 作成者 | Web Claude (PMエージェント) |
| 承認 | まこさん |
| 関連 commit | 30839c1 (案G 実行+完了報告) / a265139 (案G 指示書) |
| 監査経由 | あり (Web Claude 独立評価・3 件データ精査結果反映) |
| 関連必読 | WORKFLOW.md §🔴次のタスク / cc_ml_design_spec.md §1.6 / §1.6.1 (改訂版) / .claude/instructions/2026-05-14_plan_g_pre_phase4_completion.md (案 G 完了報告) / 本タスク Web Claude 評価結果 |

## 本文 (CC への指示)

【タスク】Phase 4-a 着手前 追加対応 4 項目
(Web Claude 独立評価結果反映・案 G 残務処理・2026-05-14)

## 構造化ルール準拠
- 保存先: .claude/instructions/2026-05-14_plan_g_finalize.md
- 完了報告: .claude/instructions/2026-05-14_plan_g_finalize_completion.md

## 着手前必読
1. WORKFLOW.md §🔴次のタスク
2. cc_ml_design_spec.md §1.6 / §1.6.1 (改訂版)
3. .claude/instructions/2026-05-14_plan_g_pre_phase4_completion.md (案 G 完了報告)
4. (本タスク Web Claude 評価結果)

## 背景 (Web Claude 評価)

案 G 完了データから 4 つの追加対応が必要:
- 2025-12 が構造的弱月 (8組合せ中 4 完全 0 / 月合計 $16,933 / 8.9 倍)
- Phase 4-b で Exit 約定率 12% 確保が 2025-12 $1,900 死守の必達ライン
- K96 SHORT q99 は leak 独立な構造的問題 (旧/新で MFE/MAE 0.986 同値)
- 7/8 positive の不合格組合せ = K96 SHORT q99 (-8.22pp)

## タスク 1: phase_compliance_checklist §4b.4-b 拡張

§4b.4-b の末尾に Exit 約定率必達ライン明示を追記:

```
**月別 Exit 約定率必達ライン (2026-05-14 Web Claude 評価)**:
- 2025-12 が年最弱月 (楽観 PnL $16,933・8.9 倍)
- Phase 6-b $1,900 死守には Exit 約定率 ≥ **12%** が必達
- TP 約定 + トレーリング + 時間 Exit の合計で 12% を確保すること
- 12% 未達なら Phase 4-b cluster_best_exit 再選定または Exit type 拡張要
```

## タスク 2: K96 SHORT q99 フォールバック spec 化

phase_compliance_checklist §4a (Phase 4-a) または §4b に新規追加:

```
| 4a.5 | K96 SHORT q99 フォールバック処理 |
- Phase 4-a クラスタリングで K96 SHORT q99 (1,660件) が
  独立 cluster に分離されない場合・または混在 cluster の
  実 MFE/MAE 比 < 1.0 の場合: 当該 cluster を no-trade で除外
- フォールバック発動時の年損失見込み: $169k (9.6%)・全12ヶ月で
  $1,900 確保継続 (Web Claude 独立評価 2026-05-14)
- 出典: results/priority_rebuild/ml_phase2/k96_short_q99_exclusion_scenario.csv
```

## タスク 3: WORKFLOW.md に Phase 6-b 基準 lock 追記

WORKFLOW.md の Phase 6-b セクション (現在「月次 NET ≥ $1,900 全月クリア」記載箇所) の直後に追記:

```
### Phase 6-b 基準 lock (cc_ml_design_spec §1.6.1 メタルール準拠)

**実行前最終確定**: Phase 6-b 実行前に以下を最終確定し、実行後の緩和は許容しない:
- 月次 NET ≥ $1,900 (固定)
- 全 3 ヶ月クリア必須 (平均・中央値・1ヶ月クリアへの緩和禁止)
- cap 値・Exit 設定・他全パラメータ Phase 6-b 着手指示書発行時点で固定

**基準変更の禁止**: 結果確定後の基準緩和 ($1,900→$1,500・全月→2/3月・等) は
cc_ml_design_spec §1.6.1 メタルール違反。Phase 6-b 不合格時は §6 採否判定通り
「不合格→原因分析→ハイブリッド/設計見直し」または「廃案」のいずれか。
```

## タスク 4: Phase 2 完了報告 事後判定追記

.claude/instructions/2026-05-14_phase2_execute_completion.md の事後判定セクションに追記:

```
### 8 組合せ別 net_quality (公式記録)

| K | side | net_quality | 判定 |
|---|---|---|---|
| 12 | LONG | (実値) | ✅ positive |
| 12 | SHORT | (実値) | ✅ positive |
| 24 | LONG | (実値) | ✅ positive |
| 24 | SHORT | (実値) | ✅ positive |
| 48 | LONG | (実値) | ✅ positive |
| 48 | SHORT | (実値) | ✅ positive |
| 96 | LONG | (実値) | ✅ positive |
| 96 | SHORT | **-8.22pp** | ❌ **negative** |

### K96 SHORT q99 構造的問題 (記録)
- 旧 leak 由来 MFE/MAE 比 = 0.986
- 新 leak-free MFE/MAE 比 = 0.986 (完全同値)
- → leak と独立な構造的逆行
- 月別分布: 2025-01 (n=700) + 2025-09 (n=549) = 75% 集中
- 2025-09 で MFE/MAE = 0.778 (最悪逆行)
- Phase 4-a/4-b で対処必須 (フォールバック spec は phase_compliance §4a.5 参照)
```

## 完了報告必須証跡 5 点

1. **コード総点検 grep 結果**
   - `grep -n "12%\|Exit 約定率" .claude/rules/phase_compliance_checklist.md`
   - `grep -n "K96 SHORT q99\|フォールバック" .claude/rules/phase_compliance_checklist.md`
   - `grep -n "Phase 6-b 基準 lock\|実行前最終確定" WORKFLOW.md`
   - `grep -n "K96 SHORT q99 構造的問題" .claude/instructions/2026-05-14_phase2_execute_completion.md`

2. **数値の二重提示**
   - 全 4 タスクの追記前後 diff

3. **成果物ファイル実体** (sha256 + 行数 + 更新時刻)
   - phase_compliance_checklist.md
   - WORKFLOW.md
   - 2026-05-14_phase2_execute_completion.md

4. **実行ログ** (各タスク所要)

5. **絞り込み示唆語彙 自己 grep 結果** (no matches 含む)

## 完了後の状態

- Phase 4-b TP 設計の Exit 約定率必達ライン (12%) 明文化
- K96 SHORT q99 フォールバック spec 化 (regime 検知失敗時の保険機構)
- WORKFLOW.md Phase 6-b 基準 lock (メタルール趣旨整合)
- Phase 2 公式記録 (8 組合せ別 + K96 SHORT q99 構造的問題)
- Phase 4-a 着手指示書発行 準備完了
