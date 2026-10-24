# 案G 残務処理 完了報告: Phase 4-a 着手前 追加対応 4 項目

| 項目 | 値 |
|---|---|
| 完了日時 | 2026-05-14T10:36 JST |
| 実行者 | CC (Claude Opus 4.7 1M context・本セッション) |
| 関連指示書 | [2026-05-14_plan_g_finalize.md](2026-05-14_plan_g_finalize.md) |
| 関連 commit | e56250c (本指示書) / 30839c1 (案G 実行+完了報告) |
| 結論 | 全タスク 1-4 完了。Phase 4-a 着手指示書発行 準備完了 |

## 結果サマリー

| タスク | 内容 | 結果 |
|---|---|---|
| 1 | phase_compliance §4b.4-b に Exit 約定率 12% 必達ライン追記 | 4 行追記 (L60-64) |
| 2 | K96 SHORT q99 フォールバック spec §4a.5 追加 + 出典 CSV 生成 | §4a.5 新規 (L48) + k96_short_q99_exclusion_scenario.csv 生成 |
| 3 | WORKFLOW.md Phase 6-b 基準 lock 追記 | 新規セクション (L312-321) |
| 4 | Phase 2 完了報告に 8組合せ表 + K96 SHORT q99 記録追記 | 「8 組合せ別 net_quality」+「K96 SHORT q99 構造的問題」セクション追加 (L281-307) |

## タスク 1 詳細: phase_compliance §4b.4-b 拡張 (Exit 約定率 12% 必達ライン)

[.claude/rules/phase_compliance_checklist.md:60-64](../rules/phase_compliance_checklist.md#L60-L64) に追記:

```
**月別 Exit 約定率必達ライン (2026-05-14 Web Claude 評価)**:
- 2025-12 が年最弱月 (楽観 PnL $16,933・8.9 倍)
- Phase 6-b $1,900 死守には Exit 約定率 ≥ **12%** が必達
- TP 約定 + トレーリング + 時間 Exit の合計で 12% を確保すること
- 12% 未達なら Phase 4-b cluster_best_exit 再選定または Exit type 拡張要
```

根拠: 2025-12 楽観 PnL $16,933 / $1,900 = 8.9 倍。Exit 約定率 12% で 0.12 × $16,933 = $2,032 で月次 $1,900 を確保。

## タスク 2 詳細: K96 SHORT q99 フォールバック spec §4a.5 追加

### spec 追記

[.claude/rules/phase_compliance_checklist.md:48](../rules/phase_compliance_checklist.md#L48) Phase 4-a チェックリストに §4a.5 追加:

```
| 4a.5 | **K96 SHORT q99 フォールバック処理** (2026-05-14 案G で追加) |
Phase 4-a クラスタリングで K96 SHORT q99 (1,660件) が独立 cluster に分離されない場合・
または混在 cluster の実 MFE/MAE 比 < 1.0 の場合: 当該 cluster を no-trade で除外 /
フォールバック発動時の年損失見込み: $169,400 (q99 全体の 9.6%)・
全12ヶ月で $1,900 確保継続 (Web Claude 独立評価 2026-05-14) /
出典: results/priority_rebuild/ml_phase2/k96_short_q99_exclusion_scenario.csv |
```

### 出典 CSV 生成

`results/priority_rebuild/ml_phase2/k96_short_q99_exclusion_scenario.csv` (1,385 B / 13 行) を新規生成。

内容 (月次 12 行):

| month | before_usd | after_usd | diff_usd | diff_pct | before_x1900 | after_x1900 |
|---|---:|---:|---:|---:|---:|---:|
| 2025-01 | $246,676 | $156,595 | -$90,081 | -36.52% | 129.8x | 82.4x |
| 2025-02 | $324,261 | $323,130 | -$1,130 | -0.35% | 170.7x | 170.1x |
| 2025-03 | $162,924 | $162,924 | $0 | 0.00% | 85.7x | 85.7x |
| 2025-04 | $93,210 | $76,227 | -$16,983 | -18.22% | 49.1x | 40.1x |
| 2025-05 | $47,691 | $30,491 | -$17,201 | -36.07% | 25.1x | 16.0x |
| 2025-06 | $146,337 | $141,079 | -$5,258 | -3.59% | 77.0x | 74.3x |
| 2025-07 | $222,336 | $220,546 | -$1,790 | -0.81% | 117.0x | 116.1x |
| 2025-08 | $70,131 | $70,131 | $0 | 0.00% | 36.9x | 36.9x |
| 2025-09 | $150,340 | $116,900 | -$33,440 | -22.24% | 79.1x | 61.5x |
| 2025-10 | $73,784 | $73,784 | $0 | 0.00% | 38.8x | 38.8x |
| 2025-11 | $207,209 | $203,693 | -$3,516 | -1.70% | 109.1x | 107.2x |
| 2025-12 | $16,933 | $16,933 | $0 | 0.00% | 8.9x | 8.9x |

**年間累積**: before $1,761,834 / after $1,592,434 / 損失 $169,400 (9.61%)
**全 12 ヶ月 $1,900 確保 (after)**: True (12/12) ✅

## タスク 3 詳細: WORKFLOW.md Phase 6-b 基準 lock 追記

[WORKFLOW.md:312-321](../../WORKFLOW.md#L312-L321) に新規セクション追加:

```markdown
### Phase 6-b 基準 lock (cc_ml_design_spec §1.6.1 メタルール準拠・2026-05-14 案G で追加)

**実行前最終確定**: Phase 6-b 実行前に以下を最終確定し、実行後の緩和は許容しない:
- 月次 NET ≥ $1,900 (固定)
- 全 3 ヶ月クリア必須 (平均・中央値・1ヶ月クリアへの緩和禁止)
- cap 値・Exit 設定・他全パラメータ Phase 6-b 着手指示書発行時点で固定

**基準変更の禁止**: 結果確定後の基準緩和 ($1,900→$1,500・全月→2/3月・等) は
cc_ml_design_spec §1.6.1 メタルール違反。Phase 6-b 不合格時は §6 採否判定通り
「不合格→原因分析→ハイブリッド/設計見直し」または「廃案」のいずれか。
```

## タスク 4 詳細: Phase 2 完了報告 事後判定に追記

[.claude/instructions/2026-05-14_phase2_execute_completion.md:281-307](2026-05-14_phase2_execute_completion.md#L281-L307) 事後判定セクション末尾に 2 ブロック追加。

### 8 組合せ別 net_quality (公式記録) ブロック

| K | side | n_fire | net_quality | 判定 |
|---:|---|---:|---:|---|
| 12 | LONG | 1,660 | +16.06pp | ✅ positive |
| 12 | SHORT | 2,023 | +10.97pp | ✅ positive |
| 24 | LONG | 1,322 | +6.02pp | ✅ positive |
| 24 | SHORT | 1,967 | +28.63pp | ✅ positive |
| 48 | LONG | 3,601 | +33.72pp | ✅ positive |
| 48 | SHORT | 2,323 | +27.71pp | ✅ positive |
| 96 | LONG | 5,133 | +23.37pp | ✅ positive |
| 96 | SHORT | 1,660 | **-8.22pp** | ❌ **negative** |

加重平均 +20.58pp / positive 7/8 → 公式 PASS。

### K96 SHORT q99 構造的問題 (記録) ブロック

- 旧 leak 由来 MFE/MAE 比 = 0.986 / 新 leak-free MFE/MAE 比 = 0.986 → leak と独立な構造的逆行
- 月別分布: 2025-01 (n=700・42.2%) + 2025-09 (n=549・33.1%) = 75.3% 集中
- 2025-09 で MFE/MAE = 0.778 (最悪逆行)
- フォールバック発動時年損失 $169,400 (9.6%)・全12ヶ月で $1,900 確保継続

## 完了報告必須証跡 5 点

### 証跡1. コード総点検 grep 結果

```
$ grep -n "12%\|Exit 約定率" .claude/rules/phase_compliance_checklist.md
60:**月別 Exit 約定率必達ライン (2026-05-14 Web Claude 評価)**:
62:- Phase 6-b $1,900 死守には Exit 約定率 ≥ **12%** が必達
63:- TP 約定 + トレーリング + 時間 Exit の合計で 12% を確保すること
64:- 12% 未達なら Phase 4-b cluster_best_exit 再選定または Exit type 拡張要

$ grep -n "K96 SHORT q99\|フォールバック\|4a.5" .claude/rules/phase_compliance_checklist.md
48:| 4a.5 | **K96 SHORT q99 フォールバック処理** (2026-05-14 案G で追加) | ...

$ grep -n "Phase 6-b 基準 lock\|実行前最終確定" WORKFLOW.md
312:### Phase 6-b 基準 lock (cc_ml_design_spec §1.6.1 メタルール準拠・2026-05-14 案G で追加)
314:**実行前最終確定**: Phase 6-b 実行前に以下を最終確定し、実行後の緩和は許容しない:

$ grep -n "K96 SHORT q99 構造的問題\|8 組合せ別 net_quality" .claude/instructions/2026-05-14_phase2_execute_completion.md
281:### 8 組合せ別 net_quality (公式記録)
298:### K96 SHORT q99 構造的問題 (記録)
```

### 証跡2. 数値の二重提示

- チャットサマリー: 上記タスク 1〜4 各セクション
- 出典: results/priority_rebuild/ml_phase1/monthly_pnl_optimistic.csv (タスク 1/2 数値根拠)・results/priority_rebuild/ml_phase2/net_quality_24combinations.csv (タスク 4)・新規生成 k96_short_q99_exclusion_scenario.csv (タスク 2)

### 証跡3. 成果物ファイル実体

| ファイル | サイズ | 行数 | sha256 (先頭12桁) | 更新時刻 |
|---|---:|---:|---|---|
| .claude/rules/phase_compliance_checklist.md | 8,540 B | 117 | 7e9c8ca68cf2 | 2026-05-14 10:35 |
| WORKFLOW.md | 44,008 B | 613 | d93fc5032375 | 2026-05-14 10:35 |
| .claude/instructions/2026-05-14_phase2_execute_completion.md | 13,738 B | 306 | f3f4dce222b3 | 2026-05-14 10:36 |
| results/priority_rebuild/ml_phase2/k96_short_q99_exclusion_scenario.csv | 1,385 B | 13 | 7f269a931dd7 | 2026-05-14 10:35 |

### 証跡4. 実行ログ

| タスク | 所要 | 内容 |
|---|---|---|
| 1 §4b.4-b 拡張 | 数秒 | Edit |
| 2 §4a.5 追加 + CSV 生成 | 1 分 | Bash python pandas + Edit |
| 3 WORKFLOW.md lock 追記 | 数秒 | Edit |
| 4 Phase 2 完了報告追記 | 数秒 | Edit |
| **総所要** | **約 3-5 分** | |

Python warning: 0 件 (inline `python3 -c` 実行で no warnings)。

### 証跡5. 絞り込み示唆語彙 自己 grep 結果

```
[no matches] 採用候補
[no matches] 効く
[no matches] 効かない
[no matches] 優先
[no matches] 不要
[no matches] 切れる
[no matches] 残せる
[no matches] 除外して良い
[no matches] 使える
[no matches] 意味がある
[no matches] 意味がない
```

指示書 / 報告書 / 改訂 spec / WORKFLOW 追記 / CSV いずれにも絞り込み示唆語彙の使用なし。

## 完了後の状態 (指示書「完了後の状態」確認)

| 項目 | 確認 |
|---|---|
| Phase 4-b TP 設計の Exit 約定率必達ライン (12%) 明文化 | ✅ |
| K96 SHORT q99 フォールバック spec 化 (regime 検知失敗時の保険機構) | ✅ |
| WORKFLOW.md Phase 6-b 基準 lock (メタルール趣旨整合) | ✅ |
| Phase 2 公式記録 (8 組合せ別 + K96 SHORT q99 構造的問題) | ✅ |
| Phase 4-a 着手指示書発行 準備完了 | ✅ |

## 次のステップ

1. Web Claude が本完了報告を独立評価
2. まこさん最終 GO
3. Phase 4-a (k-means クラスタリング) 着手指示書発行
