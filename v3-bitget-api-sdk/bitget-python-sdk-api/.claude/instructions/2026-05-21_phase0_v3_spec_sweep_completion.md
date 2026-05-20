# Phase 0 v3 spec sweep — 完了報告

完了日: 2026-05-21
担当: CC
指示書: `.claude/instructions/2026-05-21_phase0_v3_spec_sweep.md`
種別: 機械的反映タスク (light 枠)

---

## §0 結論

✅ **完了**。4 ファイル機械反映済 (合計 4 files changed, 24 insertions, 11 deletions)。

修正対象範囲はまこさん 2026-05-21 物理 view 結果で「WORKFLOW.md は対象外 / §2.5・§2.6 ファイル実体不在のため対象外」と確定 → 4 ファイル (cc_ml_design_spec.md / phase_compliance_checklist.md / ml_axis_catalog.md / 2026-05-19_web_claude_self_check_addendum.md) に集約。

---

## §1 修正内容サマリ

| # | ファイル | 行数変更 | 主要修正 |
|---|---|---|---|
| 1 | `cc_ml_design_spec.md` | 9 行置換 | §1.1 リード文 14 ラベル化 + §1.3 / §1.6 #3 / §3 / §3.3 / §5 Phase 1-4 全 hit を 14 化 |
| 2 | `.claude/rules/phase_compliance_checklist.md` | 1 行置換 | L127 Phase 1 セクション見出し「16 label」→「14 ラベル独立」 |
| 3 | `.claude/ml_axis_catalog.md` | 1 行置換 | L576 Funding rate を median +0.0002%/8h baseline + p95 0.01%/8h stress + 方向別適用に更新 |
| 4 | `.claude/instructions/2026-05-19_web_claude_self_check_addendum.md` | 13 行追加 | 冒頭 archive 注記 (v3 更新差分 7 項目を列挙・参照禁止) |

合計: **4 files / 24 insertions / 11 deletions**

---

## §2 grep 証跡 (4 種・全件チェック)

> 期待: 本文側「16 ラベル」「16 LightGBM」「16 モデル」「16 予測値」「16 label」「Funding ... 0.01% 固定」「125x」「maxPositionNum 200」「火/水/木」「メンテ時間帯」が **0 hit**。archive 注記内 / 履歴記述 / 「p95 0.01%/8h stress」(stress 値として残存) のみ hit。

### A. 16 ラベル系 grep

```
--- cc_ml_design_spec.md ---
L23: **14 ラベル独立学習 (対称性活用)**: ... 旧 16 ラベル USD 絶対値版および旧 28 ラベル独立案は archive):
--- phase_compliance_checklist.md ---
(0 hit)
--- ml_axis_catalog.md ---
(0 hit)
--- 2026-05-19_web_claude_self_check_addendum.md ---
(0 hit)
```

判定: cc_ml_design_spec.md L23 の hit は §1.1 リード文の「archive 注記内」(旧 16 / 28 → 新 14 への置換履歴) のため許容。本文側 hit は **0 件** ✅

### B. Funding ... 0.01% 単独 grep (median baseline 化確認)

```
--- cc_ml_design_spec.md ---
L257: | Funding stress | p95 = 0.01%/8h | ストレステスト参考値 ...
L262: - **旧設計**: 0.01%/8h 固定（暫定値）→ 廃止（2026-05-20）
--- phase_compliance_checklist.md ---
L13: ... median (p50) = +0.0002%/8h (baseline) / p95 = 0.01%/8h (stress) ...
L191: ... median (p50) = +0.0002%/8h を baseline ... / p95 = 0.01%/8h を stress test 参考値 ...
--- ml_axis_catalog.md ---
L576: ... **median +0.0002%/8h baseline** ... / p95 0.01%/8h stress ...
--- 2026-05-19_web_claude_self_check_addendum.md ---
L5: - Funding 8h 毎 0.01% → median +0.0002%/8h baseline / p95 0.01%/8h stress (audit#19)
```

判定: すべて「p95 0.01%/8h stress (参考値)」または「旧設計廃止」「archive 履歴」の文脈。本文側で「Funding 0.01% 一律固定」と扱っている記述は **0 件** ✅

### C. 125x / maxPositionNum 200 grep

```
--- cc_ml_design_spec.md ---
(0 hit)
--- phase_compliance_checklist.md ---
(0 hit)
--- ml_axis_catalog.md ---
(0 hit)
--- 2026-05-19_web_claude_self_check_addendum.md ---
L7: - 最大レバ 125x → 150x (audit#19)
L8: - maxPositionNum 200 → 150 (audit#19)
```

判定: addendum の hit は冒頭 archive 注記内 (旧→新の置換履歴) のみ。本文側 hit は **0 件** ✅

### D. 火/水/木 / メンテ時間帯 grep

```
--- cc_ml_design_spec.md ---
(0 hit)
--- phase_compliance_checklist.md ---
(0 hit)
--- ml_axis_catalog.md ---
(0 hit)
--- 2026-05-19_web_claude_self_check_addendum.md ---
L4: - メンテ時間帯 火/水/木 05-08 UTC → メンテなし (24/7・exchange_spec.md L37)
L9: - 削除類型 11 種 → 10 種 (旧 #10 メンテ時間帯混入を削除)
L70: 6. メンテ時間帯 火/水/木 05:00-08:00 UTC (発注スキップ実装 + バックテスト → 実運用差異モニタリング)
```

判定: L4 / L9 は冒頭 archive 注記内 (旧→新の置換履歴)。L70 は 2026-05-19 発行当時の追記内容内 (= 凍結対象本文)・冒頭 archive 注記で「本ファイル参照禁止・履歴のみ」と明示済のため許容。本文側 (cc_ml_design_spec.md / phase_compliance_checklist.md / ml_axis_catalog.md) の hit は **0 件** ✅

---

## §3 diff

`git diff --stat` 結果:

```
 .claude/instructions/2026-05-19_web_claude_self_check_addendum.md | 13 +++++++++++++
 .claude/ml_axis_catalog.md                                        |  2 +-
 .claude/rules/phase_compliance_checklist.md                       |  2 +-
 cc_ml_design_spec.md                                              | 18 +++++++++---------
 4 files changed, 24 insertions(+), 11 deletions(-)
```

完全な `git diff` 出力は本セッションのチャットログを参照。

---

## §4 commit log

commit: (次の commit で記録予定・本完了報告書と同じ commit に内包)

メッセージ案:
```
chore: Phase 0 v3 spec sweep - 14 ラベル + exchange_spec.md audit#19 機械反映

handoff v16 §3.2 機械反映タスク (light 枠)。WORKFLOW.md は範囲外 (Phase 1 着手指示書発注時に現フェーズ更新でまとめて反映予定)。

- cc_ml_design_spec.md §1.1/§1.3/§1.6/§3/§5: 16 ラベル → 14 ラベル独立 (対称性活用・LONG×K=7×{MFE,MAE})
- phase_compliance_checklist.md L127: Phase 1 セクション見出しを 14 ラベル独立に
- ml_axis_catalog.md L576: Funding rate を median +0.0002%/8h baseline + p95 stress + 方向別適用 (exchange_spec.md audit#19) に
- 2026-05-19_web_claude_self_check_addendum.md 冒頭: v3 化 archive 注記 (参照禁止・履歴のみ) 追加
```

---

## §5 終了条件

- ✅ 4 ファイル機械反映済
- ✅ grep 4 種で本文側 0 hit 確認
- ✅ 指示書本体 `.claude/instructions/2026-05-21_phase0_v3_spec_sweep.md` 保存済
- ✅ 完了報告書 (本ファイル) 作成済
- ⏭ 次タスク: Web Claude 再確認 → Phase 1 着手指示書 (full 枠) 発注
